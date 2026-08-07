#!/usr/bin/env bash
# Generate → SECURITY-GATE → publish the sanitized chain snapshot to gh-pages (ui#13).
# Push model: a node host runs this on a timer; nothing inbound is exposed.
# The security test is a HARD gate — if it fails, NOTHING is published.
# Race-safe: rebases onto the latest gh-pages and retries (the chaindata job also pushes there).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$DIR/.." && pwd)"
NODE="${1:-http://127.0.0.1:8080}"
WORK=/tmp/chain-snapshot-pub

python3 "$DIR/chain-snapshot.py" "$NODE" /tmp/chain.json >/dev/null
python3 "$DIR/security-test.py" /tmp/chain.json \
  || { echo "ABORT: security test failed — NOT publishing"; exit 1; }

git -C "$REPO" show-ref -q refs/remotes/origin/gh-pages || git -C "$REPO" fetch -q origin gh-pages \
  || { echo "gh-pages branch missing — create it first (see snapshot/README.md)"; exit 1; }

ok=0
for attempt in 1 2 3 4 5; do
  git -C "$REPO" fetch -q origin gh-pages
  rm -rf "$WORK"; git -C "$REPO" worktree prune
  git -C "$REPO" worktree add -q --detach "$WORK" origin/gh-pages
  cp /tmp/chain.json "$WORK/chain.json"
  cp "$DIR/chain.html" "$WORK/chain.html"
  echo "snapshot.logos.live" > "$WORK/CNAME"     # keep the custom domain across deploys
  git -C "$WORK" add chain.json chain.html CNAME
  if ! git -C "$WORK" commit -q -m "snapshot: chain state $(date -u +%FT%TZ)"; then
    git -C "$REPO" worktree remove --force "$WORK"; ok=1; echo "  (no change)"; break; fi
  if git -C "$WORK" push -q origin HEAD:gh-pages 2>/dev/null; then
    git -C "$REPO" worktree remove --force "$WORK"; ok=1; echo "published chain.json + chain.html to gh-pages"; break; fi
  git -C "$REPO" worktree remove --force "$WORK" 2>/dev/null || true
  sleep 3
done
[ "$ok" = 1 ] || { echo "publish failed after retries (gh-pages contention)"; exit 1; }
