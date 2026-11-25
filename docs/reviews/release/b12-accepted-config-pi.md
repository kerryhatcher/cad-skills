# B12 accepted configuration from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: record of the lead decisions of 2026-11-15 01:51 UTC for the B12 matrix, the
harness directory, the ceilings, the provider accounting, and the licensing items. This
report gives the accepted values. It does not approve a paid run. Reviewers remain
reports-only.

## 1. Accepted layout and counts

| Item | Accepted value |
|---|---|
| Harness directory | `tests/eval/` |
| Notice file | `docs/release-licensing.md` |
| Matrix design | 210 scheduled runs |
| Local installation checks | 24, no provider call |
| Automatic retries | None |

Run count: routing 162, explicit invocation 27, artifact 9, baseline 9, compaction 3.
Total 210.

Install checks: copy 9, symlink 6, user scope 9. Total 24. These are local. A paid
selection run is not part of the 24.

No provider batch starts until the integrated skill artifacts pass their reviews.

## 2. Accepted ceilings

| Group | Runs | Turns each | Time each | Reported tokens each |
|---|---|---|---|---|
| Routing | 162 | 10 | 300 s | 30000 |
| Explicit invocation | 27 | 10 | 300 s | 30000 |
| Artifact | 9 | 30 | 1200 s | 250000 |
| Baseline | 9 | 30 | 1200 s | 250000 |
| Compaction | 3 | 30 | 1200 s | 250000 |
| Batch | 210 | Not applicable | Not applicable | 12000000 |

The sum of the per-run token ceilings is 10,920,000:

| Group | Product |
|---|---|
| Routing | 162 × 30000 = 4860000 |
| Explicit invocation | 27 × 30000 = 810000 |
| Artifact | 9 × 250000 = 2250000 |
| Baseline | 9 × 250000 = 2250000 |
| Compaction | 3 × 250000 = 750000 |
| Total | 10920000 |

The batch ceiling of 12000000 leaves 1080000 tokens of headroom. The values agree.

## 3. Provider accounting and enforcement limits

State these limits in the harness and in each release report.

1. A token count is the value that the host reports for the run. It is not an
   independent measurement. It is not a meter.
2. Not every host reports tokens. If a host does not report a count, record
   `tokens: unavailable` and enforce the turn and time limits only.
3. The harness examines the budget after each response. It decides before the next
   request. It cannot stop a request that is in flight.
4. The run ceiling of 210 is a hard count of scheduled runs.
5. There is no automatic retry. A manual retry is a new scheduled run. It must fit the
   210-run ceiling and the batch token ceiling.
6. Stop before another request when the remaining budget is insufficient for that
   request class. Record the stop reason.
7. Stop the batch when the reported tokens reach the batch ceiling. Record the stop
   reason. Keep every failed attempt.

## 4. Ceiling tests without provider calls

The static suite injects fake usage records and fake turn and time records. It checks:

- C-1: A run that passes the turn limit stops with `stop_reason: turn_limit`.
- C-2: A run that passes the time limit stops with `stop_reason: time_limit`.
- C-3: A run that passes the reported token limit stops with
  `stop_reason: token_limit`.
- C-4: A run with `tokens: unavailable` stops on the turn or time limit only. It does
  not fail on a missing token count.
- C-5: The harness stops the batch before the next request when the remaining batch
  budget is insufficient.
- C-6: The batch stops at the 210-run ceiling.
- C-7: A mock usage record carries the label `mock` and never enters the release table.

These tests call no provider.

## 5. Licensing decisions recorded

| ID | Decision |
|---|---|
| O1 | Full supplier copies have unconfirmed permission. Do not claim that a copyright line alone decides all use rights. See the packaging boundary report. |
| O2 | No built-image publication in this feature. The image section stays a reference section. |
| O3 | Cite the KiCad design exception for embedded design data. Do not extend it to a redistributed library collection. |
| O4 | Use the license from the exact pinned KiBot version. Retain the metadata conflict. |
| O5 | B11 uses project-authored labeled proxies. |
| O6 | The provenance inventory records hashes, source URLs, retrieval dates, and applicable license evidence. |

### O4 measured detail

| Item | Value |
|---|---|
| Pinned KiBot version in the image | 1.9.1 |
| Source tag | `v1.9.1`, commit `3b79f610136aebc1b9c539e316d9e16af5e37732` |
| Upstream license | GNU Affero General Public License v3.0 |
| `LICENSE` SHA-256 | `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0` |
| Installed metadata | `GPL-3.0` and `GPLv3+` |

The metadata conflict stays in the notice. The pinned tag text is authoritative.

### O6 measured detail

| File | SHA-256 | Source | Retrieval | License evidence |
|---|---|---|---|---|
| `tests/fixtures/pcb-fab-package/drawing-example.png` | `c5a4395fda642b7d031e5dcf30d81043070bb9878b1556dcb867cd5ea954b425` | Not recorded | Open | Open |
| `examples/respeaker-nightlight/refs/core_board_drawing.png` | `e5f14bf1c6ef1b134130eba2670622010ef719d31f0200288b909ada53ef0921` | Not recorded | Open | Open |
| `examples/respeaker-nightlight/refs/mic_ring_drawing.png` | `3e616f736bf68553b1a2e40d8d9ca07cce1364e4c771e143281a73ad9821d9f3` | Not recorded | Open | Open |

## 6. Limits

This report records decisions. It runs no paid call and no CAD tool. Claude owns product
changes. Reviewers write reports only.
