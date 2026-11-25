# Harness freeze boundary from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: record the freeze boundary only. No new probes. No product edit. No commit. No
provider call.

## Boundary

Three files changed after the freeze `docs/reviews/b12-harness-freeze-claude.sha256`
(SHA-256 `21168df2ef2d1d4902883adae8a27896c401f79728d7f9e096ea20aeb82f6d62`) was
published. Root measured the same three files. Claude was stopped.

| File | Frozen SHA-256 | Current SHA-256 | State |
|---|---|---|---|
| `tests/eval/run_case.py` | `59eeb7505cdbbee3b253b0fc11277fbb9c161bf79321e7f8a1d0d43ec2c4950d` | `bbd0ee6202c983e13566c13e370b13b912fdc7ba8ac76d927f41d4c1575f45c9` | Changed |
| `tests/eval/score.py` | `a1f1d160d887c634b3b986c0454dfcbfb1f11392c85de6cf7a6e8e586a6a556c` | `c80b80f73f3ae0cc3607c4d6ac58b0ab25296d7637e9151638b8facb68945c41` | Changed |
| `tests/test_release_harness.py` | `9c1293ac5a70d0651a906cb414e3137caa970c991a0e4322744b09a8a1c64692` | `ff759c0980e3c5871527bda7271b9463390c7f7cafc2430190f5aaf879516617` | Changed |

The other 30 entries of the freeze still match. The packaging files are unchanged:

- `tests/eval/packaging.py` matches.
- `tests/eval/distribution.yaml` matches.
- `tests/test_release_packaging.py` matches.
- `skills/pcb-fab-package/sources.yaml` matches.

Thus the freeze no longer matches the working tree. The working tree is a new, unreviewed
revision.

## Effect on the completed review

`docs/reviews/release/b12-harness-freeze-review-pi.md` is valid for the frozen hashes
only. Its results apply to these bytes:

| Item | Frozen value |
|---|---|
| Freeze file | `21168df2...` |
| Entries | 33 of 33 |
| Harness tests | 53 of 53 |
| Packaging tests | 25 of 25 |
| Skill packages | 8 of 8 |
| Project I/O | 11 of 11 |

The blocked items B-1, B-2, B-3, M-A and M-B in
`docs/reviews/release/b12-narrow-correction-pi.md` refer to the frozen bytes. The current
working-tree changes are not reviewed.

No new probe ran for this record. The changed files were not executed.

## Next

1. Wait for Codex to report.
2. Release one complete correction for B-1, B-2, B-3, M-A and M-B.
3. Freeze the complete input set again.
4. Codex and Pi review the new freeze.
5. Keep authorization at zero.

## Limits

This record compares hashes only. It does not examine the changed behavior. It does not
approve the changed files.
