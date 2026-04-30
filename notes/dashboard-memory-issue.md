## Dashboard memory issue

Date logged: 2026-04-30

### Summary

The local dashboard is functionally healthy, but `dashboard.service` is using too much memory.

Observed on this machine:

- `dashboard.service` RSS: ~7.1G
- `dashboard.service` peak: ~14.5G
- node log directory size: `46G`
- node log file count: `69`
- live channel cache size: `68K`

### Likely root cause

The dashboard server indexes the full node log history into process-wide caches.

Relevant code in `dashboard/server.py`:

- `parse_log_metadata()` reads full log files with `read_text(...).splitlines()`
- `_refresh_log_metadata()` walks every file in `state/live-v0.1.2/logs`
- class-level caches keep aggregated metadata in memory:
  - `log_file_cache`
  - `block_metadata_cache`
  - `channel_metadata_cache`

This is likely driven by `logos-live` message reconciliation and enrichment, but the current approach scales with total historical logs instead of recent/live activity.

### What is not the problem

- `state/zone-board-v0.2.2/dashboard-live-channels.json` is only `68K`
- live TUI persistence appears bounded and not materially contributing to memory growth

### Proposed fix after the demo

Keep the same functionality for recent/live messages, but bound the log index:

1. Parse logs line-by-line instead of loading whole files into memory.
2. Only index a bounded recent window:
   - last `N` log files, or
   - last `X` hours.
3. Keep only the newest few matches per `(channel, text)` in `channel_metadata_cache`.
4. Keep `block_metadata_cache` bounded to recent blocks/messages relevant to live reconciliation.
5. Optionally add a setting for log-index window size.

### Expected tradeoff

- recent/live message matching and finality enrichment should keep working
- very old messages may lose enriched metadata if they fall outside the bounded log window

That tradeoff is acceptable for the dashboard use case and should reduce memory pressure substantially.

### Compatibility note: logos-node-visualizer

Checked against:

- `/home/alisher/logos-node-visualizer/publish.py`
- `/home/alisher/logos-node-visualizer/server.py`

Important:

- the visualizer reads raw node logs directly from `state/live-v0.1.2/logs`
- the visualizer also reads `state/zone-board-v0.2.2/dashboard-live-channels.json`
- it does **not** appear to depend on the runbook dashboard's internal Python log caches

Safe optimization boundary:

- optimize only `dashboard/server.py` in-memory log indexing behavior
- keep the raw log directory path and file availability unchanged
- keep `dashboard-live-channels.json` format unchanged

Risky change to avoid before review:

- aggressive log retention / deletion / compaction

Reason:

`logos-node-visualizer` currently uses the raw logs for its own telemetry window, so deleting or shrinking log availability could affect it even if the dashboard itself keeps working.
