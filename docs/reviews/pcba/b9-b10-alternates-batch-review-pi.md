# B9/B10 alternates batch review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b9-b10-alternates-batch-claude.md`, batch 1 of the remaining
implementation. Reviewed against `docs/reviews/pcba/b9-b10-remaining-execution-claude.md`
at SHA-256 `22afe3344d32c1306060446fc5622bc9bd586c15811e0b96accd3ce6c3607610`.

Scope: alternate selection, the approval binding, and alternate identity in rows and BOM.
I changed no product file.

## 1. Result

I accept batch 1 in this scope, with one concrete conflict.

- `uv run tests/test_pcba_design.py`: 50 passed, 0 failed, exit 0.
- All 32 listed file hashes match.
- `sha256sum -c skills/pcba-design/COPY_SHA256.txt`: 15 of 15 copies OK.
- `uv run tests/test_skill_packages.py`: 7 of 8. The failure is only the release-owned
  snippet route.

## 2. Before and after hashes

The batch changed or added five files. The other 27 files are unchanged.

| Path | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `3fb2f9de791c938879f9cf82abada1e85a2e64dc49c70de2b72a15e2728d5146` | `371f99d5ae246b43ad6f2f764bb898a2148be29d8d62896c942af5736585fb7f` |
| `skills/pcba-design/contracts/alternate-approval.schema.json` | absent | `dc598d5666f4a2f6c7a9d62d9d09579310500e5d5dfc534b66f4eb518540a66f` |
| `skills/pcba-design/contracts/part-map-1.1.schema.json` | absent | `c61bf95ecdca13d245e90cc6d89e17af3b523aa3630816403c43b46469a9e8ad` |
| `skills/pcba-design/scripts/pcba.py` | `30ae7d359c1c3977c31519238d6c03020c81223b87d7443e44322a58f131e3a3` | `22360ed4344c41cbae008aa15d46788e4dd86307b5c0e4f31223745cdc3e5b55` |
| `tests/test_pcba_design.py` | `e21e06d81bc15ee755164fd0d164a070acca3648f60257aa360ec527947a5cb6` | `ab45b2104feef5318c101193ae86f047962e0372f41dbbefbc4eb7daca288ff6` |

No shared contract file changed. The interface file is unchanged.

## 3. Conflict

C1. A mechanical entry can hold `alternates`. The accepted note, section 6 item 2, says
"A mechanical entry holds no `alternates`." The 1.1 schema lists `alternates` as a property
of every reference entry and does not forbid it with `mechanical`. The loader does not
check it either.

Probe:

```bash
# Set schema_version 1.1. Add to the MH1 entry:
#   mechanical: true
#   alternates:
#     - name: alt-m
#       part: components/resistor-alt.yaml
uv run skills/pcba-design/scripts/pcba.py neutral --project /tmp/a2 --board board.kicad_pcb \
    --variant base --as-of 2026-11-15
```

Result: exit 0, status written. The unused alternate is bound as a `parts` input.

Fix: forbid `alternates` when `mechanical` is present, in the 1.1 schema or in the loader
with one named refusal. Add one focused test.

## 4. Verified

- Selection: the board record `extensions.pcba.selected_alternates` names the alternate per
  reference. An unknown reference, an unknown name, and a mechanical reference refuse
  (`alternate.unknown`). A reference excluded in the selected variant refuses
  (`alternate.reference_excluded`).
- Map: version 1.1 accepts `alternates`. Version 1.0 refuses them (`map.schema`). A repeated
  alternate name in one entry refuses (`map.alternate_duplicate`).
- Approval: `components/alternate-approvals.yaml` is a skill-owned record bound as a
  `parts` input. The key is reference, variant and alternate name. A duplicate key refuses
  (`alternate.approval_conflict`). An approval for no declared reference or variant refuses
  (`alternate.approval_unused`). A missing approval refuses (`alternate.unapproved`).
- Bytes: a changed alternate part, and a wrong hash in the approval, refuse
  (`alternate.approval_stale`). The approval is checked before the field checks.
- Fields: footprint, polarity, pin map, package, ratings and temperature range each refuse
  on a mismatch.
- Identity: the row takes the alternate manufacturer, MPN, part path and part hash, and
  names the alternate in `selected_alternate`. Unselected rows keep an empty name.
- Demand: each populated reference counts once under the part actually used. The probe split
  the resistor demand into 5 for the alternate and 15 for the primary.
- The accepted neutral design stays closed except for the declared alternate extension.

## 5. Non-blocking observation

The loader binds every listed alternate as a `parts` input and includes every listed
alternate in the stock-conflict check, selected or not. This is why the C1 case binds an
unused file. Decide later whether only selected alternates should be bound and checked.

## 6. Limits

Placement, supplier artifacts and package publication are later batches. The snippet route
stays an integration task.

## 7. Boundary

This review is valid only for the 32 SHA-256 values in the batch 1 record. A hash record
does not keep the old file bytes. The working tree now holds uncommitted batch 2 edits, so
those bytes are outside this review. C1 and the batch 2 scope go into one coherent batch 2
supersession after Codex completes. No separate micro-freeze.
