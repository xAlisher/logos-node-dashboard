## Proposal panel spec

Date logged: 2026-04-30

### Goal

Add a lightweight `Block Proposals` panel to the local dashboard so it is obvious that the node is actively participating in leader selection and proposing blocks.

The panel should be demo-friendly and should not require full historical log indexing.

### Motivation

The dashboard already shows:

- node mode, height, tip, slot, LIB
- recent logs
- zone activity

What is missing is a clear summary of local proposal activity.

Recent node logs already contain useful proposal data, including:

- proposal timestamp
- slot
- parent block ID
- proposed block ID
- transaction count
- mempool removals count
- confirmation that our own proposed block was applied locally
- confirmation that it was published to the network

### Scope

Add a new dashboard panel:

- `Block Proposals`

It should only use a bounded recent log window, for example:

- newest log file, or
- last `N` log files, or
- last `X` hours

Do not rely on full log history.

### Proposed UI

#### Top stats

- `Proposals Today`
- `Last Proposal`
- `Last Slot`
- `Last Block`

Optional:

- `Time Since Last Proposal`
- `Non-empty Proposals Today`
- `0-tx Proposals Today`

#### Recent proposals table

Columns:

- `Time`
- `Slot`
- `Block ID`
- `Tx`
- `Removed`
- `Status`

Example status values:

- `proposed`
- `applied`
- `broadcast`
- `applied+broadcast`

### Data source

Use recent node log lines only.

Relevant log patterns already observed:

- `proposed block with id HeaderId(...) containing N transactions (M removed)`
- `Successfully applied our own proposed block`
- `Publishing it to the blend network`

These can be grouped by proposed block ID.

### Parsing model

For each proposal event, extract:

- `timestamp`
- `slot`
- `parent_block_id`
- `block_id`
- `tx_count`
- `removed_count`

Then enrich with follow-up lines:

- `applied_locally: true|false`
- `published_to_network: true|false`

Derived status:

- `proposed`
- `applied`
- `broadcast`
- `applied+broadcast`

### Performance constraints

This panel must not worsen the known dashboard memory issue.

Requirements:

1. Parse logs line-by-line.
2. Only inspect a bounded recent window.
3. Keep proposal entries bounded in memory.
4. Avoid indexing full historical proposal data.

### Suggested implementation

Backend:

- add a small parser for proposal lines in `dashboard/server.py`
- expose a new endpoint such as `/api/proposals`
- return:
  - summary stats
  - recent proposal list

Frontend:

- add a `Block Proposals` card/panel to `dashboard/index.html`
- refresh on the same interval as status/log panels

### Example payload

```json
{
  "ok": true,
  "summary": {
    "proposals_today": 73,
    "non_empty_today": 41,
    "zero_tx_today": 32,
    "last_proposal_at": "2026-04-30T11:08:12Z",
    "last_slot": 1453701,
    "last_block_id": "abcd1234..."
  },
  "recent": [
    {
      "timestamp": "2026-04-29T14:41:14Z",
      "slot": 1380103,
      "parent_block_id": "e080a6e7...",
      "block_id": "1865fc5c...",
      "tx_count": 2,
      "removed_count": 3487,
      "applied_locally": true,
      "published_to_network": true,
      "status": "applied+broadcast"
    }
  ]
}
```

### Nice-to-have later

- proposals per hour sparkline
- link between proposal events and chain inclusion if cheaply derivable
- filter for empty vs non-empty proposals
- “first proposal after funding” marker

### Non-goals for now

- full historical proposal analytics
- deep explorer-style block browsing
- expensive chain-wide reconciliation
