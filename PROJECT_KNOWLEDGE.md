# Logos Blockchain Runbook

Date: 2026-04-13
Workspace: `/home/alisher/logos-blockchain-runbook`
Repository: `https://github.com/logos-blockchain/logos-blockchain`
Release page: `https://github.com/logos-blockchain/logos-blockchain/releases`

## Update 2026-04-14

- The active testnet target changed from `0.1.2rc2` testing to the released `0.1.2` tag on April 13, 2026.
- The local binary originally in `artifacts/node/logos-blockchain-node` turned out to be older than expected:
  - `logos-blockchain-node 0.1.1`
  - `commit: 5633e3b (tag 0.1.1rc2)`
- The local canonical node path was updated to the verified `0.1.2` binary:
  - `logos-blockchain-node 0.1.2`
  - `commit: 05f84a5 (tag 0.1.2)`
- The previous binary was preserved as:
  - `artifacts/node/logos-blockchain-node-0.1.1rc2`
- The `0.1.2` release notes include explicit bootstrap peers, so the required peer config is publicly available via the release notes even though the devnet node-data endpoints return `401 Unauthorized`.
- A fresh live config was generated with the release-note peers:
  - `configs/live/node.yaml`
  - state path: `./state/live-v0.1.2`
- The older generated live config was preserved as:
  - `configs/live/node-pre-0.1.2.yaml`
- Dry-run validation of the new live config succeeded with:
  - `Configs are valid! ✅`

Bootstrap peers from release `0.1.2`:

```text
/ip4/65.109.51.37/udp/3000/quic-v1/p2p/12D3KooWFrouXfmrR4nsLMtE7wu15DoMJ6VtoUtHinREZCvbWHar
/ip4/65.109.51.37/udp/3001/quic-v1/p2p/12D3KooWJRGau8M1rjT7R5e4YYsgdFhsMX35nRDtMwCDjxQkXAHz
/ip4/65.109.51.37/udp/3002/quic-v1/p2p/12D3KooWQXJavMDTRscjauFSgVAB1VLB6Rzpy2uY5SU9Tk7927tb
/ip4/65.109.51.37/udp/3003/quic-v1/p2p/12D3KooWSQc7CcGtvWDPF1yCbBthFnQjprfCVHmfmNDUrSmqQsU1
```

Implication:

- For `0.1.2`, the deployment remains the built-in `devnet`, and the missing practical join input was the bootstrap peers.
- The public devnet node-data endpoints are still protected with basic auth, but joining the network no longer appears blocked on that because the release notes publish the peer list directly.

## Start Command For v0.1.2 Testnet

Run from `/home/alisher/logos-blockchain-runbook`.

Multi-line:

```bash
env LOGOS_BLOCKCHAIN_CIRCUITS=/home/alisher/logos-blockchain-runbook/artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64 \
/home/alisher/logos-blockchain-runbook/artifacts/node/logos-blockchain-node \
/home/alisher/logos-blockchain-runbook/configs/live/node.yaml
```

One-line:

```bash
cd /home/alisher/logos-blockchain-runbook && env LOGOS_BLOCKCHAIN_CIRCUITS=/home/alisher/logos-blockchain-runbook/artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64 /home/alisher/logos-blockchain-runbook/artifacts/node/logos-blockchain-node /home/alisher/logos-blockchain-runbook/configs/live/node.yaml
```

Important:

- Do not put a space after the trailing `\` in the multi-line command.
- This config uses `./state/live-v0.1.2`, so it is isolated from the earlier standalone run.
- Current live config writes logs to `./state/live-v0.1.2/logs`.
- Verify sync progress with:

```bash
curl -w "\n" http://localhost:8080/cryptarchia/info
```

## Disk Usage Checks

Check total `v0.1.2` state size:

```bash
du -sh /home/alisher/logos-blockchain-runbook/state/live-v0.1.2
```

Check the RocksDB directory specifically:

```bash
du -sh /home/alisher/logos-blockchain-runbook/state/live-v0.1.2/db
```

Check logs specifically:

```bash
du -sh /home/alisher/logos-blockchain-runbook/state/live-v0.1.2/logs
```

List the newest log files:

```bash
ls -t /home/alisher/logos-blockchain-runbook/state/live-v0.1.2/logs | head
```

## Restart And Log Commands

Restart the `v0.1.2` node:

```bash
cd /home/alisher/logos-blockchain-runbook

env LOGOS_BLOCKCHAIN_CIRCUITS=/home/alisher/logos-blockchain-runbook/artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64 \
/home/alisher/logos-blockchain-runbook/artifacts/node/logos-blockchain-node \
/home/alisher/logos-blockchain-runbook/configs/live/node.yaml
```

Run it detached from your shell and keep stdout/stderr:

```bash
cd /home/alisher/logos-blockchain-runbook
nohup env LOGOS_BLOCKCHAIN_CIRCUITS=/home/alisher/logos-blockchain-runbook/artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64 /home/alisher/logos-blockchain-runbook/artifacts/node/logos-blockchain-node /home/alisher/logos-blockchain-runbook/configs/live/node.yaml > /home/alisher/logos-blockchain-runbook/state/live-v0.1.2/node-stdout.log 2>&1 &
disown
```

Check the detached stdout log:

```bash
tail -n 100 /home/alisher/logos-blockchain-runbook/state/live-v0.1.2/node-stdout.log
```

Check live API state:

```bash
curl -w "\n" http://127.0.0.1:8080/cryptarchia/info
```

List newest log files:

```bash
ls -t /home/alisher/logos-blockchain-runbook/state/live-v0.1.2/logs | head
```

Show the newest log file:

```bash
latest=$(ls -t /home/alisher/logos-blockchain-runbook/state/live-v0.1.2/logs | head -n 1)
sed -n '1,200p' "/home/alisher/logos-blockchain-runbook/state/live-v0.1.2/logs/$latest"
```

Show the last 100 lines from the newest log file:

```bash
latest=$(ls -t /home/alisher/logos-blockchain-runbook/state/live-v0.1.2/logs | head -n 1)
tail -n 100 "/home/alisher/logos-blockchain-runbook/state/live-v0.1.2/logs/$latest"
```

## Local Dashboard

Files:

- `dashboard/server.py`
- `dashboard/index.html`

Start the dashboard server:

```bash
cd /home/alisher/logos-blockchain-runbook
python3 dashboard/server.py --host 127.0.0.1 --port 8090
```

Or use the helper script:

```bash
cd /home/alisher/logos-blockchain-runbook
./dashboard/run.sh
```

Open in browser:

```text
http://127.0.0.1:8090
```

What it shows:

- current node status from `/cryptarchia/info`
- mode, height, slot, LIB slot, tip, LIB
- tail of the newest file log from `state/live-v0.1.2/logs`

API endpoints exposed by the dashboard:

```text
http://127.0.0.1:8090/api/status
http://127.0.0.1:8090/api/logs
```

## User Systemd Service

Files:

- `run-node.sh`
- `logos-node.service`

Installed user unit:

- `~/.config/systemd/user/logos-node.service`

Current service name:

```text
logos-node.service
```

Check status:

```bash
systemctl --user status --no-pager logos-node.service
```

Start:

```bash
systemctl --user start logos-node.service
```

Stop:

```bash
systemctl --user stop logos-node.service
```

Restart:

```bash
systemctl --user restart logos-node.service
```

Follow journal logs:

```bash
journalctl --user -u logos-node.service -f
```

Check all major local footprints together:

```bash
du -sh \
  /home/alisher/logos-blockchain-runbook/artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64 \
  /home/alisher/logos-blockchain-runbook/artifacts/node \
  /home/alisher/logos-blockchain-runbook/state/live-v0.1.2
```

## Goal

Run a Logos blockchain node locally from the public GitHub release and record what worked and what failed.

## Release Pinned

- Latest release checked on 2026-04-13: `0.1.2rc2`
- Release name: `Logos Blockchain Node 0.1.2rc2`
- Published at: `2026-04-10T13:40:49Z`
- Release type: prerelease
- Local architecture: `x86_64`

Artifacts downloaded into `artifacts/`:

- `logos-blockchain-node-linux-x86_64-0.1.2rc2.tar.gz`
- `logos-blockchain-circuits-v0.4.2-linux-x86_64.tar.gz`

Extracted artifacts:

- Binary: `artifacts/node/logos-blockchain-node`
- Circuits root: `artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64`

## Repo + Configs

The release itself did not include standalone config files as downloadable assets. The standalone configs were pulled from the repository and checked against tag `0.1.2rc2`:

- `nodes/node/standalone-deployment-config.yaml`
- `nodes/node/standalone-node-config.yaml`

These tagged configs matched the cloned repo copies used for the run.

## Commands Used

Inspect CLI:

```bash
/home/alisher/logos-blockchain-runbook/artifacts/node/logos-blockchain-node --help
```

Validate configs:

```bash
LOGOS_BLOCKCHAIN_CIRCUITS=/home/alisher/logos-blockchain-runbook/artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64 \
/home/alisher/logos-blockchain-runbook/artifacts/node/logos-blockchain-node \
  --deployment /home/alisher/logos-blockchain-runbook/repo/logos-blockchain/nodes/node/standalone-deployment-config.yaml \
  /home/alisher/logos-blockchain-runbook/repo/logos-blockchain/nodes/node/standalone-node-config.yaml \
  --check-config
```

Run standalone node:

```bash
env LOGOS_BLOCKCHAIN_CIRCUITS=/home/alisher/logos-blockchain-runbook/artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64 \
/home/alisher/logos-blockchain-runbook/artifacts/node/logos-blockchain-node \
  --log-level INFO \
  --deployment /home/alisher/logos-blockchain-runbook/repo/logos-blockchain/nodes/node/standalone-deployment-config.yaml \
  /home/alisher/logos-blockchain-runbook/repo/logos-blockchain/nodes/node/standalone-node-config.yaml
```

Verify API:

```bash
curl -sf http://127.0.0.1:8080/cryptarchia/info
```

## Wins

- The GitHub repo exists and is public.
- The latest visible release was resolved successfully from GitHub API.
- The Linux `x86_64` binary downloaded and executed without linker errors.
- The circuits bundle downloaded and worked with `LOGOS_BLOCKCHAIN_CIRCUITS`.
- `--check-config` passed with `Configs are valid!`.
- The node booted in standalone mode.
- The node served HTTP on `127.0.0.1:8080`.
- API verification succeeded with:

```json
{"lib":"e2b9e243037357c4cef7be3d3d5d793eda2183f3c4de097ab6e886355459b2d3","lib_slot":0,"tip":"e2b9e243037357c4cef7be3d3d5d793eda2183f3c4de097ab6e886355459b2d3","slot":0,"height":0,"mode":"Online"}
```

- During runtime the node opened port `8080`.
- Runtime state and logs were created under:
  - `state/db/`
  - `state/logs/logos-blockchain.log.2026-04-13-13`

## Fails / Rough Edges

- The release assets do not include the example standalone config files. They had to be pulled from the repository tag.
- The standalone config is not a network-joined config. There are no peers configured, so the node logs:
  - `Failed to trigger bootstrap: No known peers.`
  - `Skipping IBD as no peers are configured`
- The verified standalone node stayed at `slot: 0`, `height: 0`, `mode: "Online"`. It booted successfully, but it did not advance as a connected network node.
- The tagged standalone node config defaults to `DEBUG` logging. With the included `chain_start_time` set to `2026-02-17 07:47:56.891858 +00:00:00`, running it on 2026-04-13 produces extremely noisy repeated stake-adjustment logs and `skipped epochs` warnings.
- A short timed run with default log level generated huge output volume. Using `--log-level INFO` is much more usable for manual verification.
- Devnet join was not attempted. The release notes say devnet config generation requires credentials and network-specific details:
  - deployment config
  - bootnode addresses
  - cfgsync credentials for hosted devnet access

## Retro — 2026-06-21 (power-cut recovery, self-heal guard, proposals visibility)

### Wins
- [project] Power-cut **orphan-tip crash loop** recovered with the `tip = lib` rollback (node back Online, no resync). The fix is now **durable**: a portable + dual-source (journald *and* file) self-heal guard committed into `run-node.sh` (here and in logos-node-starter), verified by a controlled restart (guard no-ops on a healthy start; tip preserved).
- [project] Root-caused the recurring **journald-vs-file-log gap** — this kit logs to journald, so file-log assumptions silently break features. It had hidden BOTH the self-heal guard AND the dashboard Block Proposals panel on optiplex.
- [project] **Block Proposals panel fixed** — `/api/proposals` now falls back to journald (`--grep`/`--since`, bounded scan) when file logs yield nothing; verified live (15 proposals, `source: journal`). Confirmed the node is a healthy proposing validator (~1.5% stake; 15/17 proposed blocks landed in-chain).
- [process] Unbiased multi-reviewer comparison vs 0xSarnavo's dashboard (2 independent Claude tiers), claims hand-verified against the upstream repo before publishing the epic issue (#6).

### Fails
- [process] Asserted "node never proposed" **twice** before reading `chain_leader_service` logs (which showed 18 proposals). Wrong action: concluded a *negative* from a grep pattern (`proposing`/`created proposal`) that didn't match the real phrase (`proposed block with id`). Root cause: didn't validate the search pattern against actual log samples before claiming absence. Caught only by continuing to dig.
- [project] The auto-rollback guard shipped for Sneg (file-log trigger) **silently never fired** on optiplex (journald) — the box ran with non-functional self-heal until a real power cut. Root cause: the recipe assumed file-only logs; a log-consumer must read where the node actually logs.
- [project] **Two diverged `run-node.sh`** launchers (starter/scripts vs dashboard root; the deployed one hardcoded `/home/alisher`, broken for user `dar`). Root cause: launcher edited per-box instead of kept portable. Reconciled — both now portable (`BASH_SOURCE`) + guarded.
- [process] Repeated SSH heredoc/quoting failures (parens in `echo`, `$0` vs positional args, `FETCH_HEAD` vs `origin/<branch>`) cost several round-trips. Fix: use `ssh host 'bash -l' <<'EOF'` for any non-trivial remote script; never inline parens in a double-quoted `ssh "..."`.
- [project] The proposal parser first used line-count windowing (`-n 5000`) which returned nothing — the node is so verbose that sparse proposal lines scroll out of any sane window. Fixed with server-side `--grep` + `--since`. Root cause: assumed sparse events sit in a small recent line window.

## Evidence Summary

- Binary health: confirmed via `--help`
- Config health: confirmed via `--check-config`
- Runtime health: confirmed via successful service startup logs and live HTTP response
- Shutdown state: process was stopped after verification and port `8080` was released

## Folder Layout

```text
/home/alisher/logos-blockchain-runbook
├── artifacts/
├── configs/
├── logs/
├── notes/
├── repo/
├── state/
└── PROJECT_KNOWLEDGE.md
```

## Recommended Next Steps

- If the goal is only local validation, keep using standalone mode and `--log-level INFO`.
- If the goal is joining a real network, fetch or generate the network-specific deployment config and bootnodes instead of the standalone config.
- If repeated epoch catch-up logs are a problem, adjust the standalone deployment time settings for a fresh local test or use a config designed for current wall-clock time.
