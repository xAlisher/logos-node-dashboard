# Logos Blockchain Runbook

Local runbook and dashboard helpers for running a Logos Blockchain testnet node.

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
