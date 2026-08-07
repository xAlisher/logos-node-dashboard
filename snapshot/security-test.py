#!/usr/bin/env python3
"""Security test for chain-snapshot output (ui#13). Fails (exit 1) if the sanitized
snapshot contains ANYTHING sensitive. Run in CI before every publish.

Checks:
 1. keys are a subset of the allowlist (structural guarantee)
 2. no dotted-IPv4 anywhere (LAN 192.168.x / docker 172.x / Tailscale 100.x)
 3. no forbidden key/substrings (wallet, balance, notes, address, peer_id, listen, url, funding_pk, keystore, connected_peers)
 4. known-sensitive literals absent (the Sneg wallet address + tailnet IP seen in /api/status & /network/info)
"""
import json, re, sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "chain.json"

ALLOWLIST = {
    "network", "node_version", "state", "height", "slot", "tip", "lib", "lib_slot",
    "genesis_unix_ms", "epoch", "current_slot", "n_peers", "n_connections",
    "updated_utc", "reachable",
}
FORBIDDEN_SUBSTR = [
    "wallet", "balance", "notes", "address", "peer_id", "listen", "connected_peers",
    "discovered_peers", "funding_pk", "keystore", "private", "127.0.0.1", "192.168.",
    "172.1", "100.10", "/ip4/", "http://", "https://",
]
KNOWN_SECRETS = [
    "face706210ecf700ba975f64d2ccaeaaba290d2f58424e3f702e7058b83ea823",  # Sneg wallet addr
    "100.108.127.3",                                                     # Tailscale IP
]
IPV4 = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

raw = open(PATH).read()
data = json.loads(raw)
fails = []

extra = set(data.keys()) - ALLOWLIST
if extra:
    fails.append(f"non-allowlisted keys present: {sorted(extra)}")

for ip in IPV4.findall(raw):
    fails.append(f"IPv4 address leaked: {ip}")

low = raw.lower()
for s in FORBIDDEN_SUBSTR:
    if s in low:
        fails.append(f"forbidden substring present: {s!r}")

for sec in KNOWN_SECRETS:
    if sec in raw:
        fails.append(f"known sensitive literal present: {sec[:16]}…")

if fails:
    print("SECURITY TEST: FAIL")
    for f in fails:
        print("  ✗", f)
    sys.exit(1)
print("SECURITY TEST: PASS — only allowlisted chain-state fields; no IPs, wallet, keys, or peer IDs.")
print("  keys:", sorted(data.keys()))
sys.exit(0)
