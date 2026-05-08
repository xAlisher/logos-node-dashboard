# DEBUG → INFO Log Level Migration

## Context

Node is configured at `tracing.level: DEBUG` in `configs/live/node.yaml`.
At ~3 GB/hr this saturates the 295 GB `/data` partition in ~3 days.
Switching to INFO would reduce volume substantially, but a small number of
dashboard and visualizer features parse raw log lines and may break.

**Decision: keep DEBUG before the demo. Run this checklist after.**

---

## Pre-migration snapshot

Run before switching to capture a baseline to compare against:

```bash
# 1. Note current telemetry numbers
curl -s http://localhost:8080/network/info | jq .

# 2. Capture current visualizer telemetry
python3 ~/logos-node-visualizer/publish.py 2>&1 | grep -E "Telemetry|Zone|Gap"

# 3. Note unique peer count in last 24h
python3 -c "
import json
data = json.loads(open('~/logos-node-visualizer/pages/network.json').read())
t = data.get('telemetry', {})
print('tracked_peers:', t.get('summary', {}).get('tracked_peers'))
print('active_peak:', t.get('summary', {}).get('active_peak'))
"
```

---

## The switch

```yaml
# configs/live/node.yaml
tracing:
  level: INFO   # was: DEBUG
```

Then restart the node (or reload if hot-reload is supported).
Wait at least **2 full hours** before evaluating — one hour for logs to
accumulate, one for publish.py to run at least twice.

---

## Verification checklist

### 1. logos-node-visualizer peer telemetry

| Check | Expected at INFO | How to verify |
|-------|-----------------|---------------|
| Tracked peers count | ≥50 (was ~63; may drop ~5-8) | `network.json` → `telemetry.summary.tracked_peers` |
| Active peers/hr chart | Still populated | logos.live → Telemetry tab |
| Peer uptime rows | Still present | `telemetry.peer_uptime` array non-empty |

If tracked peers drops below 30 → peer visibility is broken at INFO,
revert or add a per-module DEBUG override for `logos_blockchain_chain_network_service`.

**Why the risk:** ~25 unique peers appear only in DEBUG lines:
`"Requested orphan parents from peer: 12D3Koo…"`

---

### 2. Dashboard — Block Proposals panel

Log lines at risk (currently DEBUG):
- `proposed block with id ...`
- `Successfully applied our own proposed block...`

| Check | Pass condition |
|-------|---------------|
| Proposals panel shows recent entries | At least one entry in last 2 hours |
| Block ID populated | Not empty / not "unknown" |
| Timestamp populated | Not epoch 0 |

If empty → these are DEBUG-only lines. Options:
- Add targeted override: `logos_blockchain_cryptarchia=DEBUG` in node.yaml
- Or rebuild the panel from the `/cryptarchia/headers` API instead of logs

---

### 3. Dashboard — Zone message finality

Log lines at risk:
- `Received proposal with ID ...` (used to attach block/timestamp/finality context)

| Check | Pass condition |
|-------|---------------|
| Zone messages show finality status | Not all stuck at "pending" |
| Block ID attached to finalized messages | Present in zone-board cache |

---

### 4. Disk usage

```bash
df -h /data
# After 24h at INFO: expect ~500 MB–1.5 GB/hr vs ~3 GB/hr at DEBUG
# If still >2 GB/hr → the gossipsub ERROR/WARN spam is the real driver, not DEBUG
```

Note: 6.4M ERROR + 6.1M WARN lines/hr are emitted regardless of level
(`gossipsub: failed to broadcast: Duplicate`). If disk usage doesn't drop
significantly, the upstream gossipsub duplicate-message bug is the root cause
and needs a node fix, not a log-level change.

---

### 5. Revert condition

Revert to DEBUG if **any** of:
- Tracked peers < 30
- Proposals panel empty for 2+ hours during active block production
- Zone finality metadata missing for messages that should be finalized

```yaml
# revert
tracing:
  level: DEBUG
```

---

## Longer-term fix (regardless of INFO outcome)

The real log flood is upstream gossipsub spam:
- `ERROR logos_blockchain_network_service::backends::libp2p::swarm::gossipsub: failed to broadcast message to topic: …/mempool/1.0.0 Duplicate` — ~63,000/hr
- `WARN libp2p_gossipsub::behaviour: Not publishing a message that has already been published` — ~57,000/hr

These fire at INFO too. The right fix is either:
- A node release that de-duplicates mempool gossip before logging
- Or a per-module log filter to suppress these specific modules at WARN/ERROR
