# Migrating logos-node + dashboard to an always-on server

Guide for moving a running logos-blockchain-node, zone-board, and the node dashboard from a dev machine to a dedicated server with minimal downtime.

---

## Overview

The migration uses a non-destructive approach: prep and test on the new server while the old node keeps running, then execute a ~3 min hot-swap.

**Do NOT run both nodes simultaneously with real keys** — double-signing risk on testnet.

---

## Phase 0 — Install dependencies on new server (zero downtime)

```bash
# On new server
sudo apt install -y tmux
pip3 install httpx --break-system-packages

# Log directory (adjust path to your storage)
sudo mkdir -p /your/log/dir && sudo chown $USER:$USER /your/log/dir
```

---

## Phase 1 — Check for port conflicts

The node's HTTP API defaults to `0.0.0.0:8080`. Check if anything else uses that port:

```bash
ss -tlnp | grep 8080
```

If 8080 is taken, choose a free port (e.g. 8085) and update everywhere:

- `configs/live/node.yaml` → `listen_address: 0.0.0.0:<PORT>`
- `run-zone-board.sh` → `NODE_URL` default
- Any sequencer config that references the node URL

---

## Phase 2 — Mirror files to new server (zero downtime)

```bash
# From old machine
rsync -av ~/logos-blockchain-runbook/ newserver:~/logos-blockchain-runbook/

# Update log path in node.yaml on new server only
ssh newserver "sed -i 's|directory: ./state/live-v0.1.2/logs|directory: /your/log/dir|' \
  ~/logos-blockchain-runbook/configs/live/node.yaml"
```

Fix any hardcoded home directory paths in scripts:
```bash
ssh newserver "sed -i 's|/home/olduser/|/home/newuser/|g' \
  ~/logos-blockchain-runbook/run-zone-board.sh"
```

---

## Phase 3 — Dry-run test (zero downtime, throwaway key)

Start a shadow node on a different port with a dummy key — no conflict with the running node:

```bash
ssh newserver 'cp ~/logos-blockchain-runbook/configs/live/node.yaml \
  ~/logos-blockchain-runbook/configs/live/node-test.yaml'
ssh newserver "sed -i 's|0.0.0.0:<PORT>|0.0.0.0:<PORT+1>|' \
  ~/logos-blockchain-runbook/configs/live/node-test.yaml"
ssh newserver "sed -i 's|node_key: <your_key>|node_key: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa|' \
  ~/logos-blockchain-runbook/configs/live/node-test.yaml"
ssh newserver 'cd ~/logos-blockchain-runbook && nohup artifacts/node/logos-blockchain-node \
  configs/live/node-test.yaml >> /your/log/dir/node-test.log 2>&1 &'

# Verify after ~15s
sleep 15 && ssh newserver 'curl -s http://127.0.0.1:<PORT+1>/cryptarchia/info'
```

Kill test processes when done:
```bash
ssh newserver 'kill $(pgrep -f node-test.yaml) 2>/dev/null; \
  rm ~/logos-blockchain-runbook/configs/live/node-test.yaml'
```

---

## Phase 4 — Hot-swap (~3 min downtime)

```bash
# 1. Final sync while old node still running
rsync -av ~/logos-blockchain-runbook/state/live-v0.1.2/db/ \
  newserver:~/logos-blockchain-runbook/state/live-v0.1.2/db/
rsync -av ~/logos-blockchain-runbook/state/zone-board-v0.2.2/ \
  newserver:~/logos-blockchain-runbook/state/zone-board-v0.2.2/

# 2. Stop old node (check for systemd service first)
systemctl --user stop logos-node 2>/dev/null && systemctl --user disable logos-node 2>/dev/null
# Also kill any stray processes
kill $(pgrep -f "dashboard/server.py") 2>/dev/null
tmux kill-session -t zone-board 2>/dev/null
kill $(pgrep -f zone-board) 2>/dev/null
sleep 3
kill $(pgrep -f logos-blockchain-node) 2>/dev/null
sleep 5

# 3. Final delta
rsync -av ~/logos-blockchain-runbook/state/live-v0.1.2/db/ \
  newserver:~/logos-blockchain-runbook/state/live-v0.1.2/db/

# 4. Start on new server
ssh newserver 'cd ~/logos-blockchain-runbook && nohup artifacts/node/logos-blockchain-node \
  configs/live/node.yaml >> /your/log/dir/node.log 2>&1 &'
sleep 15
ssh newserver 'curl -s http://127.0.0.1:<PORT>/cryptarchia/info'

ssh newserver 'cd ~/logos-blockchain-runbook && nohup bash run-zone-board.sh \
  >> /your/log/dir/zone-board.log 2>&1 &'

ssh newserver 'cd ~/logos-blockchain-runbook && nohup python3 dashboard/server.py \
  --host 0.0.0.0 --port 8090 \
  --node-api http://127.0.0.1:<PORT> \
  --log-dir /your/log/dir \
  --zone-board-dir ~/logos-blockchain-runbook/state/zone-board-v0.2.2 \
  --zone-board-tmux-session zone-board \
  --local-zone-channel <your_channel> \
  --wallet-public-key <your_pubkey> \
  --live-channel-cache ~/logos-blockchain-runbook/state/zone-board-v0.2.2/dashboard-live-channels.json \
  >> /your/log/dir/dashboard.log 2>&1 &'
```

---

## Verify

```bash
# Node syncing
ssh newserver 'curl -s http://127.0.0.1:<PORT>/cryptarchia/info'

# Wallet balance (may take a few seconds after startup)
ssh newserver 'curl -s http://127.0.0.1:<PORT>/wallet/<pubkey>/balance'

# zone-board running
ssh newserver 'tmux ls'

# Dashboard
# Visit http://<server-ip>:8090
```

---

## Known issues

**Node panics on first block proposal — circuits directory missing**

Symptom: node syncs and connects to peers normally, then crashes when it first wins a slot:
```
panic: "Could not find logos-blockchain-circuits directory.
  1. Set LOGOS_BLOCKCHAIN_CIRCUITS env var, or
  2. Place circuits at /home/<user>/.logos-blockchain-circuits"
```

Cause: the ZK circuits are needed to produce leadership proofs. The node expects them at `~/.logos-blockchain-circuits`. The original machine had this set up; the new machine does not. The crash only happens the first time the node wins a slot lottery — which may be hours after migration, making it easy to miss.

Fix — run this on the new machine immediately after migration:
```bash
ln -s ~/logos-blockchain-runbook/artifacts/circuits ~/.logos-blockchain-circuits
```

---

**Wallet service fails on restart after mid-run kill**

Symptom: `/wallet/.../balance` returns 408 or hangs. Node logs show:
```
ERROR: Failed to apply backfill block to wallet
  err=Requested wallet state for unknown block
ERROR: ServiceStatuses: Wallet: ServiceStatus::Starting
```

Cause: wallet service internal state out of sync when node is killed while processing blocks.

Fix: restart the node once more. On the second clean start it initialises correctly.

---

**Old machine has a systemd service restarting the node**

`kill` alone is not enough if `logos-node.service` is enabled. Always:
```bash
systemctl --user stop logos-node
systemctl --user disable logos-node
```

---

**Proposals panel empty on new server**

Normal — proposals are parsed from local node log files. The old machine's logs were not migrated. The panel fills in as the node runs and proposes blocks.

---

## Rollback

Old node processes are stopped but not deleted. To roll back:
```bash
cd ~/logos-blockchain-runbook
systemctl --user enable logos-node && systemctl --user start logos-node
# or manually:
nohup artifacts/node/logos-blockchain-node configs/live/node.yaml >> /tmp/node.log 2>&1 &
bash run-zone-board.sh &
```
