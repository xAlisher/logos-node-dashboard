#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RUNBOOK_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8090}"
NODE_API="${NODE_API:-http://127.0.0.1:8080}"
NODE_LOG_DIR="${NODE_LOG_DIR:-$RUNBOOK_ROOT/state/live-v0.1.2/logs}"
ZONE_BOARD_DIR="${ZONE_BOARD_DIR:-$RUNBOOK_ROOT/state/zone-board-v0.2.2}"
ZONE_BOARD_TMUX_SESSION="${ZONE_BOARD_TMUX_SESSION:-zone-board}"
ZONE_CHANNEL="${ZONE_CHANNEL:-local}"
DASHBOARD_LIVE_CHANNEL_CACHE="${DASHBOARD_LIVE_CHANNEL_CACHE:-$ZONE_BOARD_DIR/dashboard-live-channels.json}"

cd "$RUNBOOK_ROOT"
exec python3 dashboard/server.py \
  --host "$HOST" \
  --port "$PORT" \
  --node-api "$NODE_API" \
  --log-dir "$NODE_LOG_DIR" \
  --zone-board-dir "$ZONE_BOARD_DIR" \
  --zone-board-tmux-session "$ZONE_BOARD_TMUX_SESSION" \
  --local-zone-channel "$ZONE_CHANNEL" \
  --live-channel-cache "$DASHBOARD_LIVE_CHANNEL_CACHE"
