#!/usr/bin/env bash
# Generate → SECURITY-GATE → publish the sanitized chain snapshot to gh-pages (ui#13).
# Push model: a node host runs this on a timer; nothing inbound is exposed.
# The security test is a HARD gate — if it fails, NOTHING is published.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$DIR/.." && pwd)"
NODE="${1:-http://127.0.0.1:8080}"
WORK=/tmp/chain-snapshot-pub

python3 "$DIR/chain-snapshot.py" "$NODE" /tmp/chain.json >/dev/null
python3 "$DIR/security-test.py" /tmp/chain.json \
  || { echo "ABORT: security test failed — NOT publishing"; exit 1; }

git -C "$REPO" fetch -q origin
git -C "$REPO" show-ref -q refs/remotes/origin/gh-pages \
  || { echo "gh-pages branch missing — create it first (see snapshot/README.md)"; exit 1; }
rm -rf "$WORK"
git -C "$REPO" worktree prune
git -C "$REPO" worktree add -q "$WORK" gh-pages
cp /tmp/chain.json "$WORK/chain.json"
cp "$DIR/chain.html" "$WORK/chain.html"
git -C "$WORK" add chain.json chain.html
git -C "$WORK" commit -q -m "snapshot: chain state $(date -u +%FT%TZ)" || echo "  (no change)"
git -C "$WORK" push -q origin gh-pages
git -C "$REPO" worktree remove --force "$WORK" 2>/dev/null || true
echo "published chain.json + chain.html to gh-pages"
