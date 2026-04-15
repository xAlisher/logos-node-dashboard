#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import urllib.error
import urllib.request
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock


ROOT = Path(__file__).resolve().parent
RUNBOOK_ROOT = ROOT.parent
DEFAULT_NODE_API = "http://127.0.0.1:8080"
DEFAULT_LOG_DIR = RUNBOOK_ROOT / "state/live-v0.1.2/logs"
DEFAULT_ZONE_BOARD_DIR = RUNBOOK_ROOT / "state/zone-board-v0.2.2"
DEFAULT_LIVE_CHANNEL_CACHE_NAME = "dashboard-live-channels.json"
DEFAULT_ZONE_BOARD_TMUX_SESSION = "zone-board"
DEFAULT_LOCAL_ZONE_CHANNEL = "local"
ZONE_TOPIC_PREFIX = b"logos:yolo:"
MAX_PUBLISH_BYTES = 500
MAX_SUBSCRIBE_CHANNEL_BYTES = 64
MAX_LIVE_MESSAGES_PER_CHANNEL = 200
TUI_MESSAGE_RE = re.compile(r"^\s*(\d{2}:\d{2}:\d{2})\s+(.+?)\s*$")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
SLOT_RE = re.compile(r"slot: Slot\((\d+)\)")
CHANNEL_INSCRIBE_RE = re.compile(
    r"ChannelInscribe\(InscriptionOp \{ channel_id: ChannelId\(\[([^\]]+)\]\), "
    r"inscription: \[([^\]]*)\].*?signer: PublicKey\(([0-9a-f]+)\).*?"
    r"Received proposal with ID: HeaderId\(([0-9a-f]+)\)"
)


def latest_log_file(log_dir: Path) -> Path | None:
    if not log_dir.exists():
        return None
    files = [path for path in log_dir.iterdir() if path.is_file()]
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def tail_lines(path: Path, line_count: int) -> list[str]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return list(deque(handle, maxlen=line_count))


def decode_zone_channel(topic_hex: str) -> str:
    try:
        raw = bytes.fromhex(topic_hex).rstrip(b"\x00")
    except ValueError:
        return topic_hex

    if raw.startswith(ZONE_TOPIC_PREFIX):
        raw = raw[len(ZONE_TOPIC_PREFIX) :]

    return raw.decode("utf-8", errors="replace") or topic_hex


def short_channel_label(topic_hex: str) -> str:
    decoded = decode_zone_channel(topic_hex)
    if decoded != topic_hex and "\ufffd" not in decoded and all(ord(char) >= 32 for char in decoded):
        return decoded
    if len(topic_hex) == 64:
        return f"{topic_hex[:13]}..."
    return topic_hex


def channel_topic_bytes(channel: str) -> bytes:
    return (ZONE_TOPIC_PREFIX + channel.encode("utf-8"))[:32].ljust(32, b"\x00")


def parse_decimal_bytes(raw: str) -> bytes | None:
    try:
        values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    except ValueError:
        return None
    if any(value < 0 or value > 255 for value in values):
        return None
    return bytes(values)


def current_lib_slot(node_api: str) -> int | None:
    try:
        with urllib.request.urlopen(f"{node_api}/cryptarchia/info", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None

    try:
        return int(payload.get("lib_slot"))
    except (TypeError, ValueError):
        return None


def find_channel_inscriptions(log_dir: Path, channel: str) -> dict[str, dict]:
    if not log_dir.exists():
        return {}

    topic = channel_topic_bytes(channel)
    found: dict[str, dict] = {}
    for log_file in sorted((path for path in log_dir.iterdir() if path.is_file()), key=lambda path: path.name):
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for line in lines:
            if "ChannelInscribe" not in line or "Received proposal with ID" not in line:
                continue
            clean = ANSI_RE.sub("", line)
            match = CHANNEL_INSCRIBE_RE.search(clean)
            if not match:
                continue
            channel_bytes = parse_decimal_bytes(match.group(1))
            inscription = parse_decimal_bytes(match.group(2))
            slot_match = SLOT_RE.search(clean)
            if channel_bytes != topic or inscription is None or slot_match is None:
                continue
            text = inscription.decode("utf-8", errors="replace")
            found[text] = {
                "text": text,
                "slot": int(slot_match.group(1)),
                "signer": match.group(3),
                "block_id": match.group(4),
                "source": "node-log",
            }

    return found


def parse_zone_board_tui(capture: str) -> dict:
    channel = None
    messages = []

    for line in capture.splitlines():
        if "┌" in line and "─" in line:
            matches = re.findall(r"┌\s*(.*?)\s*─", line)
            names = [name.strip() for name in matches if name.strip() and name.strip() != "Channels"]
            if names:
                channel = names[-1]
                if channel.startswith("[you] "):
                    channel = channel[6:]

        if "││" not in line:
            continue

        content = line.split("││", 1)[1].rsplit("│", 1)[0]
        match = TUI_MESSAGE_RE.match(content)
        if not match:
            continue

        messages.append(
            {
                "text": match.group(2),
                "timestamp": match.group(1),
                "pending": False,
                "failed": False,
                "block_id": None,
                "source": "live-tui",
            }
        )

    return {
        "channel": channel,
        "messages": messages,
    }


def message_key(message: dict) -> tuple[str, str]:
    return (str(message.get("timestamp") or ""), str(message.get("text") or ""))


def normalize_live_channels(payload: object) -> dict[str, list[dict]]:
    if not isinstance(payload, dict):
        return {}

    channels = payload.get("channels", payload)
    if not isinstance(channels, dict):
        return {}

    normalized: dict[str, list[dict]] = {}
    for channel, messages in channels.items():
        if not isinstance(channel, str) or not isinstance(messages, list):
            continue

        clean_messages = [message for message in messages if isinstance(message, dict)]
        normalized[channel] = clean_messages[-MAX_LIVE_MESSAGES_PER_CHANNEL:]
    return normalized


def load_live_channels(path: Path) -> dict[str, list[dict]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return normalize_live_channels(payload)


def save_live_channels(path: Path, channels: dict[str, list[dict]]) -> None:
    payload = {
        "channels": channels,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


class DashboardHandler(BaseHTTPRequestHandler):
    node_api = DEFAULT_NODE_API
    log_dir = DEFAULT_LOG_DIR
    zone_board_dir = DEFAULT_ZONE_BOARD_DIR
    zone_board_tmux_session = DEFAULT_ZONE_BOARD_TMUX_SESSION
    local_zone_channel = DEFAULT_LOCAL_ZONE_CHANNEL
    live_channel_cache: Path | None = None
    live_channels: dict[str, list[dict]] = {}
    live_channels_lock = Lock()

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._serve_file(ROOT / "index.html")
            return

        if self.path == "/api/status":
            self._serve_status()
            return

        if self.path == "/api/logs":
            self._serve_logs()
            return

        if self.path == "/api/zone-messages":
            self._serve_zone_messages()
            return

        if self.path == "/api/zone-live":
            self._serve_zone_live()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        if self.path == "/api/zone-publish":
            self._serve_zone_publish()
            return

        if self.path == "/api/zone-subscribe":
            self._serve_zone_subscribe()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, fmt: str, *args) -> None:
        return

    def _serve_file(self, path: Path) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        body = path.read_bytes()
        content_type, _ = mimetypes.guess_type(str(path))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc

        if length <= 0:
            return {}
        if length > 4096:
            raise ValueError("Request body is too large")

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be JSON") from exc

        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object")
        return payload

    def _serve_status(self) -> None:
        url = f"{self.node_api}/cryptarchia/info"
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": f"Node API unavailable: {exc}",
                    "url": url,
                },
                status=HTTPStatus.BAD_GATEWAY,
            )
            return

        payload["ok"] = True
        payload["url"] = url
        self._send_json(payload)

    def _serve_logs(self) -> None:
        latest = latest_log_file(self.log_dir)
        if latest is None:
            self._send_json(
                {
                    "ok": False,
                    "error": "No log file found",
                    "log_dir": str(self.log_dir),
                    "lines": [],
                },
                status=HTTPStatus.NOT_FOUND,
            )
            return

        lines = [line.rstrip("\n") for line in tail_lines(latest, 80)]
        self._send_json(
            {
                "ok": True,
                "log_dir": str(self.log_dir),
                "latest_file": latest.name,
                "lines": lines,
            }
        )

    def _serve_zone_messages(self) -> None:
        cache_dir = self.zone_board_dir / "cache"
        if not cache_dir.exists():
            self._send_json(
                {
                    "ok": False,
                    "error": "Zone-board cache directory not found",
                    "zone_board_dir": str(self.zone_board_dir),
                    "channels": [],
                },
                status=HTTPStatus.NOT_FOUND,
            )
            return

        channels = []
        seen_topics = set()
        for cache_file in sorted(cache_dir.glob("*.json")):
            topic_hex = cache_file.stem
            seen_topics.add(topic_hex)
            try:
                messages = json.loads(cache_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                channels.append(
                    {
                        "channel": decode_zone_channel(topic_hex),
                        "topic": topic_hex,
                        "ok": False,
                        "error": str(exc),
                        "messages": [],
                    }
                )
                continue

            channels.append(
                {
                    "channel": decode_zone_channel(topic_hex),
                    "topic": topic_hex,
                    "ok": True,
                    "messages": messages if isinstance(messages, list) else [],
                }
            )

        subscriptions_file = self.zone_board_dir / "subscriptions.json"
        if subscriptions_file.exists():
            try:
                subscriptions = json.loads(subscriptions_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                subscriptions = []

            for topic_hex in subscriptions:
                if not isinstance(topic_hex, str) or topic_hex in seen_topics:
                    continue
                seen_topics.add(topic_hex)
                channels.append(
                    {
                        "channel": short_channel_label(topic_hex),
                        "topic": topic_hex,
                        "ok": True,
                        "messages": [],
                    }
                )

        if not any(channel.get("channel") == self.local_zone_channel for channel in channels):
            channels.insert(
                0,
                {
                    "channel": self.local_zone_channel,
                    "topic": f"local:{self.local_zone_channel}",
                    "ok": True,
                    "messages": [],
                },
            )

        self._send_json(
            {
                "ok": True,
                "zone_board_dir": str(self.zone_board_dir),
                "channels": channels,
            }
        )

    def _serve_zone_live(self) -> None:
        session = self.zone_board_tmux_session
        try:
            capture = subprocess.run(
                ["tmux", "capture-pane", "-pt", session, "-S", "-80"],
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": f"Could not read zone-board tmux session '{session}': {exc}",
                    "session": session,
                },
                status=HTTPStatus.BAD_GATEWAY,
            )
            return

        parsed = parse_zone_board_tui(capture)
        inscriptions = find_channel_inscriptions(self.log_dir, parsed["channel"] or self.local_zone_channel)
        lib_slot = current_lib_slot(self.node_api)
        for message in parsed["messages"]:
            inscription = inscriptions.get(message["text"])
            if not inscription:
                continue
            message.update(inscription)
            if lib_slot is not None and inscription["slot"] <= lib_slot:
                message["status"] = "finalized"
                message["finalized"] = True
            else:
                message["status"] = "confirmed"
                message["finalized"] = False

        channel = parsed["channel"] or self.local_zone_channel
        with self.live_channels_lock:
            stored = self.live_channels.setdefault(channel, [])
            seen = {message_key(message) for message in stored}
            changed = False
            for message in parsed["messages"]:
                key = message_key(message)
                if key not in seen:
                    stored.append(message)
                    seen.add(key)
                    changed = True
                else:
                    for index, existing in enumerate(stored):
                        if message_key(existing) == key:
                            updated = {**existing, **message}
                            if updated != existing:
                                stored[index] = updated
                                changed = True
                            break
            if len(stored) > MAX_LIVE_MESSAGES_PER_CHANNEL:
                del stored[:-MAX_LIVE_MESSAGES_PER_CHANNEL]
                changed = True
            if changed and self.live_channel_cache is not None:
                save_live_channels(self.live_channel_cache, self.live_channels)
            live_channels = [
                {
                    "channel": channel_name,
                    "topic": f"live:{channel_name}",
                    "ok": True,
                    "messages": messages,
                }
                for channel_name, messages in sorted(self.live_channels.items())
            ]

        self._send_json(
            {
                "ok": True,
                "session": session,
                "channel": channel,
                "messages": parsed["messages"],
                "channels": live_channels,
            }
        )

    def _serve_zone_publish(self) -> None:
        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        message = str(payload.get("message", "")).strip()
        message = " ".join(message.splitlines())
        if not message:
            self._send_json({"ok": False, "error": "Message is empty"}, status=HTTPStatus.BAD_REQUEST)
            return
        if len(message.encode("utf-8")) > MAX_PUBLISH_BYTES:
            self._send_json(
                {
                    "ok": False,
                    "error": f"Message is too large; max {MAX_PUBLISH_BYTES} UTF-8 bytes",
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        session = self.zone_board_tmux_session
        try:
            subprocess.run(["tmux", "send-keys", "-t", session, "Enter"], check=True, timeout=2)
            subprocess.run(["tmux", "send-keys", "-t", session, "-l", message], check=True, timeout=2)
            subprocess.run(["tmux", "send-keys", "-t", session, "Enter"], check=True, timeout=2)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": f"Could not publish through zone-board tmux session '{session}': {exc}",
                },
                status=HTTPStatus.BAD_GATEWAY,
            )
            return

        self._send_json(
            {
                "ok": True,
                "message": message,
                "session": session,
                "channel": "your channel",
            }
        )

    def _serve_zone_subscribe(self) -> None:
        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        channel = str(payload.get("channel", "")).strip()
        if not channel:
            self._send_json({"ok": False, "error": "Channel is empty"}, status=HTTPStatus.BAD_REQUEST)
            return
        if any(char.isspace() for char in channel):
            self._send_json(
                {"ok": False, "error": "Channel must not contain whitespace"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        if len(channel.encode("utf-8")) > MAX_SUBSCRIBE_CHANNEL_BYTES:
            self._send_json(
                {
                    "ok": False,
                    "error": f"Channel is too large; max {MAX_SUBSCRIBE_CHANNEL_BYTES} UTF-8 bytes",
                },
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        session = self.zone_board_tmux_session
        command = f"/sub {channel}"
        try:
            subprocess.run(["tmux", "send-keys", "-t", session, "-l", command], check=True, timeout=2)
            subprocess.run(["tmux", "send-keys", "-t", session, "Enter"], check=True, timeout=2)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": f"Could not subscribe through zone-board tmux session '{session}': {exc}",
                },
                status=HTTPStatus.BAD_GATEWAY,
            )
            return

        self._send_json(
            {
                "ok": True,
                "channel": channel,
                "session": session,
            }
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Local dashboard for Logos node status")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--node-api", default=os.environ.get("NODE_API", DEFAULT_NODE_API))
    parser.add_argument(
        "--log-dir",
        default=os.environ.get("NODE_LOG_DIR", str(DEFAULT_LOG_DIR)),
    )
    parser.add_argument(
        "--zone-board-dir",
        default=os.environ.get("ZONE_BOARD_DIR", str(DEFAULT_ZONE_BOARD_DIR)),
    )
    parser.add_argument(
        "--zone-board-tmux-session",
        default=os.environ.get("ZONE_BOARD_TMUX_SESSION", DEFAULT_ZONE_BOARD_TMUX_SESSION),
    )
    parser.add_argument(
        "--local-zone-channel",
        default=os.environ.get("ZONE_CHANNEL", DEFAULT_LOCAL_ZONE_CHANNEL),
        help="Fallback local channel name when zone-board has not rendered one yet.",
    )
    parser.add_argument(
        "--live-channel-cache",
        default=os.environ.get("DASHBOARD_LIVE_CHANNEL_CACHE"),
        help="JSON file used to persist dashboard live channel messages across restarts.",
    )
    args = parser.parse_args()

    DashboardHandler.node_api = args.node_api.rstrip("/")
    DashboardHandler.log_dir = Path(args.log_dir)
    DashboardHandler.zone_board_dir = Path(args.zone_board_dir)
    DashboardHandler.zone_board_tmux_session = args.zone_board_tmux_session
    DashboardHandler.local_zone_channel = args.local_zone_channel
    DashboardHandler.live_channel_cache = (
        Path(args.live_channel_cache)
        if args.live_channel_cache
        else DashboardHandler.zone_board_dir / DEFAULT_LIVE_CHANNEL_CACHE_NAME
    )
    DashboardHandler.live_channels = load_live_channels(DashboardHandler.live_channel_cache)

    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Dashboard listening on http://{args.host}:{args.port}")
    print(f"Node API: {DashboardHandler.node_api}")
    print(f"Log dir: {DashboardHandler.log_dir}")
    print(f"Zone-board dir: {DashboardHandler.zone_board_dir}")
    print(f"Zone-board tmux session: {DashboardHandler.zone_board_tmux_session}")
    print(f"Local zone channel: {DashboardHandler.local_zone_channel}")
    print(f"Live channel cache: {DashboardHandler.live_channel_cache}")
    server.serve_forever()


if __name__ == "__main__":
    main()
