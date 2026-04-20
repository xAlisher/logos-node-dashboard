#!/usr/bin/env bash
set -euo pipefail

cd /home/alisher/logos-blockchain-runbook

SESSION="${ZONE_BOARD_TMUX_SESSION:-zone-board}"
NODE_URL="${NODE_API:-http://127.0.0.1:8080}"
DATA_DIR="${ZONE_BOARD_DIR:-/home/alisher/logos-blockchain-runbook/state/zone-board-v0.2.2}"
CHANNEL="${ZONE_CHANNEL:-alisher}"

cleanup() {
  tmux kill-session -t "$SESSION" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -ds "$SESSION" \
  "cd /home/alisher/logos-blockchain-runbook && exec artifacts/zone-sdk-test-v0.2.2/zone-board --node-url $NODE_URL --data-dir $DATA_DIR --channel $CHANNEL"

while tmux has-session -t "$SESSION" 2>/dev/null; do
  sleep 2
done

exit 1
