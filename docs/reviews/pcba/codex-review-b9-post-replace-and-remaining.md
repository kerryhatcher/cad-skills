# Review of the B9 post-replace correction and remaining note

Date: 2026-11-15 UTC. Reviewer: codex-pcba-dev. Branch: `work/pcba`.

## B9 post-replace correction

I checked all 30 hashes in `docs/reviews/pcba/b9-post-replace-correction-claude.md`. All hashes match. The author reports 41 focused tests passed. I did not run tests.

| File | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `a7315a7b6c3dd7a504268cfb18b57edc3a2a8ec11f1e1dbd22f77337d01e759d` | `3fb2f9de791c938879f9cf82abada1e85a2e64dc49c70de2b72a15e2728d5146` |
| `skills/pcba-design/scripts/pcba.py` | `8cda4a6b473a8f98b095f78b23d749cf07061364ebb688aa9618440b4a6ee5b7` | `30ae7d359c1c3977c31519238d6c03020c81223b87d7443e44322a58f131e3a3` |
| `tests/test_pcba_design.py` | `2adf25817a32ab75acfbaa30de2f4969bbb32a64f0eae1ac433a8334633a5010` | `e21e06d81bc15ee755164fd0d164a070acca3648f60257aa360ec527947a5cb6` |

The code catches `PostReplaceError` before `OSError`. It returns status `failure`, exit 1, `output_replaced: true`, and finding `output.replaced_then_failed`. The message states that new bytes are in place and synchronization failed. The controlled test confirms these fields and confirms that the output contains the new data. The normal `OSError` path still returns status `refused`.

The B9 neutral correction passes this scoped review. The shared snippet route remains a separate release integration item. This review does not accept alternate support, Sierra conversion, or B10 publication.

## Remaining execution note

The note at `docs/reviews/pcba/b9-b10-remaining-execution-claude.md` keeps alternates and B10 work outside the accepted neutral scope. Two interface items remain incomplete before those later tasks start:

1. **Alternates:** The note says an alternate can be named in the part map or an `alternates` list. It does not define which record owns that list, its strict schema, or how the selected alternate binds to a reference and declared variant. Define those fields before alternate implementation. Do not infer alternates by part name.
2. **B10 gate reference:** The note says checks use their listed mandatory input roles, but it does not list those roles or the independent checks. Point to the role and test table in section 14 of `docs/reviews/b9-b10-interface-claude.md`, or copy that table into the execution note. The table must remain the gate for all eight bare-board checks and all five assembly checks.

The source interface already defines the hand-installed supplier policy as `supplier_profile.extensions.pcba.hand_installed_bom`, with `include_in_bom` or `exclude_from_bom`. The execution note should point to that rule for the BOM export. A missing or unknown policy blocks qualification, while neutral output remains available.

These items do not block the accepted neutral batch. They block later alternate or B10 implementation until the lead releases that work.

This report changes no product file or shared contract.
