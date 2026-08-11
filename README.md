# Logos Blockchain Runbook

> This is a personal, experimental hobby project. It is not an official Logos product. Not audited.


Local runbook and dashboard helpers for running a Logos Blockchain testnet node.
<img width="1593" height="1308" alt="image" src="https://github.com/user-attachments/assets/ebe1790d-ff05-41b8-8bd4-8df83d759911" />


## Dashboard

The reusable dashboard lives in [`dashboard/`](dashboard/README.md).

Current dashboard highlights (v0.1.3):

- compatible with **testnet v0.2 / v0.2.1** — reads node liveness from `cryptarchia_info.state` (0.2.1 moved it off the top-level `mode`), with a fallback for older 0.2.0 nodes
- node state, chain progress, wallet balance, and peer count
- block proposal panel — reads proposals from journald when no file logs exist
- self-heals a dirty-shutdown crash loop; a slow/timing-out node can't wedge the dashboard
- zone-board messages, live TUI sync, and local inscribing controls

Start it from this directory:

```bash
ZONE_CHANNEL=your-channel ./dashboard/run.sh
```

Open:

```text
http://127.0.0.1:8090/
```

## User Services

User `systemd` service files are included for both processes:

- `logos-node.service`
- `dashboard.service`
- `zone-board.service`

Install them under `~/.config/systemd/user/`, then run:

```bash
systemctl --user daemon-reload
systemctl --user enable --now logos-node.service dashboard.service zone-board.service
```

Both services are configured with automatic restart on failure.

## Publish Safety

This repository should contain scripts, configs, and docs only. Do not commit local runtime state, keys, databases, logs, or downloaded release artifacts.

Important private/local paths:

- `state/`
- `artifacts/`
- `dashboard/dashboard.log`
- `*.key`

See [`dashboard/README.md`](dashboard/README.md) for dashboard-specific setup.
