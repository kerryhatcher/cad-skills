# Review of alternate batch 1

Date: 2026-11-15 UTC. Reviewer: codex-pcba-dev. Branch: `work/pcba`.

## Frozen review boundary

I checked the 32 hashes in `docs/reviews/pcba/b9-b10-alternates-batch-claude.md`. All matched during my initial review. The author reports 50 focused tests passed. I did not run tests.

The lead later reported product edits during this review. I stopped code review at that point. These files no longer match the frozen batch record:

| File | Frozen hash | Current hash |
|---|---|---|
| `skills/pcba-design/contracts/part-map-1.1.schema.json` | `c61bf95ecdca13d245e90cc6d89e17af3b523aa3630816403c43b46469a9e8ad` | `890a36acfb696c0823b370a33661ea9d7476578433513bf79c5b0007060217ce` |
| `skills/pcba-design/scripts/pcba.py` | `22360ed4344c41cbae008aa15d46788e4dd86307b5c0e4f31223745cdc3e5b55` | `f77ce802567606504fd0101acdac276ec6ee5fb9052a26113a0da08a4f52b8cc` |
| `tests/fixtures/pcba-design/project/board.yaml` | `95901a4b284357c2b6507f7eb4d7dcb39a84228587cb6d759c71743cf7a9257a` | `3137bf4b40e21360c15ad36776f20f9dfda570649197f38a3901ca531019ab4f` |

The current tree also has unlisted file `skills/pcba-design/scripts/sierra.py`, hash `13fc4636733498ef568a22d9acb4a881b6aa147a11dd51f4c78604ac46630887`. I did not review it.

## Finding on the frozen bytes

**Blocker: malformed alternate selections can raise an uncaught exception.** The frozen code checks that `selected_alternates` is a mapping. It does not check that each alternate name is a string. A YAML value such as `R1: [alt-r]` reaches tuple membership in `alt_of` and raises `TypeError` because the list is not hashable. The command then exits with a traceback instead of one named refusal. Validate each key and value before lookup, then add a focused negative case.

The finding applies only to the frozen `pcba.py` hash above. The current code differs, and I did not examine it. Root accepted the mechanical-entry correction for the next batch. I did not record it as a blocker.

## Decision

The frozen batch does not pass review because of the malformed-selection case. The changed files need one coherent frozen supersession before review. This report does not reopen the accepted neutral scope or review placement, supplier artifacts, or package publication.

This report changes no product file or shared contract.
