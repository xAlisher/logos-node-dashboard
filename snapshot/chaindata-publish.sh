#!/usr/bin/env bash
# Publish a chaindata fast-sync tarball to the GitHub 'chaindata' release (ui#13).
# CHAIN DATA ONLY — tars the node's RocksDB state/db, never the sibling keystore/config.
# Hard security gate: aborts if the tarball contains any key/keystore/secret. Prunes to
# the newest KEEP snapshots. Writes chaindata-latest.json to gh-pages for the public page.
#
# Requires on the host: gh (authed, contents:write) + the repo's push deploy key (gh-pages).
# Usage: chaindata-publish.sh [DB_DIR] [NODE_URL] [KEEP]
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$DIR/.." && pwd)"
DB_DIR="${1:-$HOME/logos-v2/standalone-021/state/db}"
NODE="${2:-http://127.0.0.1:8080}"
KEEP="${3:-3}"
GHREPO="xAlisher/logos-node-dashboard"
WORK=/tmp/chaindata-pub

H=$(curl -sS -m8 "$NODE/cryptarchia/info" 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["cryptarchia_info"]["height"])' 2>/dev/null || echo "")
[ -z "$H" ] && { echo "node unreachable — skip"; exit 0; }
[ -d "$DB_DIR" ] || { echo "DB dir missing: $DB_DIR"; exit 1; }

rm -rf "$WORK"; mkdir -p "$WORK"
TAR="$WORK/chaindata-h$H.tar.zst"
BASE_DIR="$(dirname "$(dirname "$DB_DIR")")"          # parent-of-parent: tar 'state/db' relative
( cd "$BASE_DIR" && sync && tar -I 'zstd -6' -cf "$TAR" state/db )

# ── HARD SECURITY GATE ──
BAD=$(tar tf "$TAR" | grep -ivE '^state/(db/?)?([0-9A-Za-z._-]+)?$' || true)
[ -n "$BAD" ] && { echo "ABORT: unexpected entries in tarball:"; echo "$BAD"; exit 1; }
mkdir -p "$WORK/scan"; tar -I zstd -xf "$TAR" -C "$WORK/scan"
if grep -rilE 'BEGIN.*PRIVATE|keystore|mnemonic|funding_pk|secret_key|"sk"' "$WORK/scan" >/dev/null 2>&1; then
  echo "ABORT: secret material found in chaindata — NOT publishing"; exit 1; fi
rm -rf "$WORK/scan"

SZ=$(stat -c%s "$TAR"); SHA=$(sha256sum "$TAR" | cut -d' ' -f1)
NOW=$(date -u +%FT%TZ)
gh release upload chaindata "$TAR" --repo "$GHREPO" --clobber
URL="https://github.com/$GHREPO/releases/download/chaindata/chaindata-h$H.tar.zst"

# chaindata-latest.json -> gh-pages (deploy key)
git -C "$REPO" fetch -q origin
git -C "$REPO" worktree prune; rm -rf /tmp/cd-ghp
git -C "$REPO" worktree add -q /tmp/cd-ghp gh-pages
python3 - "$H" "$NOW" "$SZ" "$SHA" "$URL" > /tmp/cd-ghp/chaindata-latest.json <<'PY'
import json,sys
h,now,sz,sha,url=sys.argv[1:6]
print(json.dumps({"height":int(h),"updated_utc":now,"size_bytes":int(sz),
                  "sha256":sha,"url":url,"restore":"extract into <node>/state/ then start the node"},indent=2))
PY
git -C /tmp/cd-ghp add chaindata-latest.json
git -C /tmp/cd-ghp commit -q -m "chaindata: h$H $NOW" || true
git -C /tmp/cd-ghp push -q origin gh-pages
git -C "$REPO" worktree remove --force /tmp/cd-ghp 2>/dev/null || true

# ── prune: keep newest KEEP by height ──
mapfile -t OLD < <(gh release view chaindata --repo "$GHREPO" --json assets \
  --jq '.assets[].name' | grep -E '^chaindata-h[0-9]+\.tar\.zst$' \
  | sort -t h -k2 -n | head -n -"$KEEP")
for a in "${OLD[@]:-}"; do [ -n "$a" ] && gh release delete-asset chaindata "$a" --repo "$GHREPO" --yes && echo "pruned $a"; done
echo "published chaindata-h$H.tar.zst ($((SZ/1024/1024))MB) + chaindata-latest.json; kept newest $KEEP"
