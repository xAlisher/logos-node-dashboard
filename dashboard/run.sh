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
NODE_CONFIG="${NODE_CONFIG:-$RUNBOOK_ROOT/configs/live/node.yaml}"
WALLET_PUBLIC_KEY="${WALLET_PUBLIC_KEY:-}"

if [[ -z "$WALLET_PUBLIC_KEY" && -f "$NODE_CONFIG" ]]; then
  WALLET_PUBLIC_KEY="$(awk '/funding_pk:/ { print $2; exit }' "$NODE_CONFIG" | tr -d '"')"
fi

cd "$RUNBOOK_ROOT"
exec python3 dashboard/server.py \
  --host "$HOST" \
  --port "$PORT" \
  --node-api "$NODE_API" \
  --log-dir "$NODE_LOG_DIR" \
  --zone-board-dir "$ZONE_BOARD_DIR" \
  --zone-board-tmux-session "$ZONE_BOARD_TMUX_SESSION" \
  --local-zone-channel "$ZONE_CHANNEL" \
  --wallet-public-key "$WALLET_PUBLIC_KEY" \
  --live-channel-cache "$DASHBOARD_LIVE_CHANNEL_CACHE"
