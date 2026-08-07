#!/usr/bin/env python3
"""Sanitized public chain snapshot for the node-dashboard GitHub Pages (ui#13).

Safety by construction: the output is built from an EXPLICIT ALLOWLIST of chain-state
fields only. It never copies whole objects, so wallet address/balance/notes, peer IDs,
and listen_addresses (LAN / docker / Tailscale IPs) cannot leak — they are simply never
read into the output. Pulls the RAW node endpoints (not the ops dashboard's /api/status,
which carries the wallet). Run on the node host via cron; push chain.json to gh-pages.

Usage: chain-snapshot.py [NODE_URL=http://127.0.0.1:8080] [OUT=chain.json]
"""
import json, sys, urllib.request, datetime

NODE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080").rstrip("/")
OUT  = sys.argv[2] if len(sys.argv) > 2 else "chain.json"

# genesis_time_unix_ms -> human chain label (no secrets; just identifies the network)
GENESIS_LABEL = {
    1785920400000: {"network": "testnet", "version": "0.2.1"},
    1782808200000: {"network": "testnet", "version": "0.2.0 (pre-fork, retired)"},
}

def get(path):
    try:
        with urllib.request.urlopen(NODE + path, timeout=8) as r:
            return json.load(r)
    except Exception:
        return {}

ci = (get("/cryptarchia/info") or {}).get("cryptarchia_info", {}) or {}
ti = get("/time/info") or {}
ni = get("/network/info") or {}          # contains IPs + peer_id — we take ONLY counts

genesis = ti.get("genesis_time_unix_ms")
label   = GENESIS_LABEL.get(genesis, {"network": None, "version": None})
now     = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ── ALLOWLIST — the ONLY fields that ever leave this process ──
snapshot = {
    "network":        label["network"],
    "node_version":   label["version"],
    "state":          ci.get("state"),          # Online / Bootstrapping
    "height":         ci.get("height"),
    "slot":           ci.get("slot"),
    "tip":            ci.get("tip"),            # public block hash
    "lib":            ci.get("lib"),            # public block hash
    "lib_slot":       ci.get("lib_slot"),
    "genesis_unix_ms": genesis,
    "epoch":          ti.get("current_epoch"),
    "current_slot":   ti.get("current_slot"),
    "n_peers":        ni.get("n_peers"),         # COUNT only — never the peer list/IPs
    "n_connections":  ni.get("n_connections"),
    "updated_utc":    now,
    "reachable":      bool(ci) and bool(ti),
}
json.dump(snapshot, open(OUT, "w"), indent=2)
print(json.dumps(snapshot, indent=2))
