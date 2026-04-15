# Logos Blockchain Runbook

Local runbook and dashboard helpers for running a Logos Blockchain testnet node.
<img width="1418" height="1200" alt="image" src="https://github.com/user-attachments/assets/93103a20-cf5f-4fdb-a372-264ab4f5888c" />

## Dashboard

The reusable dashboard lives in [`dashboard/`](dashboard/README.md).

Start it from this directory:

```bash
ZONE_CHANNEL=your-channel ./dashboard/run.sh
```

Open:

```text
http://127.0.0.1:8090/
```

## Publish Safety

This repository should contain scripts, configs, and docs only. Do not commit local runtime state, keys, databases, logs, or downloaded release artifacts.

Important private/local paths:

- `state/`
- `artifacts/`
- `dashboard/dashboard.log`
- `*.key`

See [`dashboard/README.md`](dashboard/README.md) for dashboard-specific setup.
