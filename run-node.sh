#!/usr/bin/env bash
# Portable logos-node launcher. Drop in ~/logos-blockchain-runbook/run-node.sh
# (the systemd unit's ExecStart points here). Auto-detects paths from its own
# location — no hardcoded /home/<user> and no hardcoded circuits version.
#
# Includes the dirty-shutdown self-heal guard (see
# ../skills/logos-node-auto-rollback-guard.md). After a power loss the chain can
# be left with an orphan tip whose parent never flushed to storage; the node then
# panics on recovery and systemd crash-loops it. The guard detects that exact
# panic before each start and rolls tip <- lib (last irreversible block), so the
# node self-heals in one restart cycle. It is idempotent and conservative — once
# tip == lib it never fires again, and it bails (leaving it for a human) on an
# unparseable snapshot or unexpected pending block removals.
set -euo pipefail

RUNBOOK="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$RUNBOOK"

# --- dirty-shutdown self-heal guard ------------------------------------------
# Recovery snapshot path is auto-detected so this works whether your config's
# base_folder is `state/` (this kit) or `state/live-vX.Y.Z/` (older layouts).
RECOVERY="$(ls -t "$RUNBOOK"/state*/recovery/consensus/chain_service.json 2>/dev/null | head -1 || true)"

# True if the previous launch died on the orphan-tip recovery panic. Checks the
# journal FIRST (this kit's node.yaml logs to stdout -> journald) and falls back
# to file-only logs (configs with tracing.logger.stdout/stderr = false).
recovery_panic_detected() {
  local sig="Could not retrieve block parent.*during recovery"
  journalctl --user -u logos-node -n 50 --no-pager 2>/dev/null | grep -qa "$sig" && return 0
  local logdir latest
  logdir="$(ls -d "$RUNBOOK"/state*/logs 2>/dev/null | head -1 || true)"
  [ -n "$logdir" ] || return 1
  latest="$(ls -t "$logdir" 2>/dev/null | head -1 || true)"
  [ -n "$latest" ] || return 1
  tail -n 60 "$logdir/$latest" 2>/dev/null | grep -qa "$sig"
}

guard_recovery() {
  [ -n "$RECOVERY" ] && [ -f "$RECOVERY" ] || return 0
  recovery_panic_detected || return 0
  echo "[run-node] recovery panic detected — evaluating auto-rollback"   # -> journald
  python3 - "$RECOVERY" <<'PY'
import json, os, shutil, sys
p = sys.argv[1]
try:
    d = json.load(open(p))
except Exception as e:
    print(f"[run-node] cannot parse recovery snapshot ({e}); leaving for manual fix"); sys.exit(0)
if d.get("tip") == d.get("lib"):
    print("[run-node] tip already == lib; nothing to do"); sys.exit(0)
if d.get("storage_blocks_to_remove") != []:
    print("[run-node] unexpected storage_blocks_to_remove; leaving for manual fix"); sys.exit(0)
shutil.copy2(p, p + ".bak.autorollback")
d["tip"] = d["lib"]
json.dump(d, open(p + ".tmp", "w"))
os.replace(p + ".tmp", p)
print("[run-node] auto-rollback applied: tip <- lib")
PY
}
guard_recovery

# --- circuits + launch -------------------------------------------------------
# find the circuits dir; fail loudly if missing (don't start the node blind to its circuits).
# NOTE: assigning separately, not `export VAR=$(...)`, so a failed glob still trips `set -e`.
CIRC_DIR="$(ls -d "$RUNBOOK"/artifacts/circuits/logos-blockchain-circuits-* 2>/dev/null | head -1)"
[ -n "$CIRC_DIR" ] && [ -d "$CIRC_DIR" ] || {
  echo "[run-node] circuits not found in $RUNBOOK/artifacts/circuits — run scripts/fetch-artifacts.sh" >&2
  exit 1
}
export LOGOS_BLOCKCHAIN_CIRCUITS="$CIRC_DIR"
exec "$RUNBOOK/artifacts/node/logos-blockchain-node" "$RUNBOOK/configs/live/node.yaml"
