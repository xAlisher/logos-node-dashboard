# Public chain snapshot (ui#13)

A **sanitized, read-only** "where is the chain" feed for the community, published to GitHub Pages.

## Safety model — allowlist, not blocklist
`chain-snapshot.py` builds its output from an **explicit allowlist** of chain-state fields, pulled from
the node's raw endpoints. It never copies whole objects, so it **cannot** leak:
- wallet address / balance / notes,
- `peer_id` / `connected_peers`,
- `listen_addresses` (LAN `192.168.x`, docker `172.x`, **Tailscale `100.x`**).

Only these are ever published: `network, node_version, state, height, slot, tip, lib, lib_slot,
genesis_unix_ms, epoch, current_slot, n_peers, n_connections, updated_utc, reachable`.

`security-test.py` is a **hard gate** run before every publish (also suitable for CI): it fails if any
IPv4, forbidden key/substring, or known-sensitive literal appears in the output. `deploy.sh` aborts the
publish if the test fails.

## Publish (push model — no inbound exposure)
Never expose the ops dashboard (`:8090`) to the internet. Instead push a static snapshot:

```bash
# one-time: create the gh-pages branch + enable Pages
git checkout --orphan gh-pages && git rm -rf . && git commit --allow-empty -m init && git push origin gh-pages
gh api -X POST repos/xAlisher/logos-node-dashboard/pages -f 'source[branch]=gh-pages' -f 'source[path]=/'

# recurring (cron on a node host):
*/5 * * * * bash ~/logos-node-dashboard/snapshot/deploy.sh http://127.0.0.1:8080
```

Served at `https://<pages>/chain.html` (+ `chain.json`).
