# B12 narrow correction authorization from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: reviewer record of the lead authorization
`docs/reviews/release/b12-narrow-authorization-root.md`. This report writes no product
file. It does not commit. It made no provider call.

## Agreement

I read the lead authorization. I agree with the seven correction items and the scope.

| Item | Correction |
|---|---|
| 1 | Attach the task and the expected paths to each planned run. Keep expected owners outside the prompts |
| 2 | Record unavailable host discovery and selection explicitly. A local scan is only a file inventory |
| 3 | Separate execution status from measured provider evidence. Missing evidence must not mean live evidence |
| 4 | Exclude held, unauthorized, unexecuted and mock records from the measured release table |
| 5 | Retain their execution records. Keep measured live failures in the measured table |
| 6 | Test the complete freeze input set and count the authorized subset correctly |
| 7 | Run the focused local tests and freeze the complete input set again |

## Correction baseline

The correction starts from these candidate bytes.

| File | SHA-256 |
|---|---|
| `tests/eval/run_case.py` | `bbd0ee6202c983e13566c13e370b13b912fdc7ba8ac76d927f41d4c1575f45c9` |
| `tests/eval/score.py` | `c80b80f73f3ae0cc3607c4d6ac58b0ab25296d7637e9151638b8facb68945c41` |
| `tests/test_release_harness.py` | `ff759c0980e3c5871527bda7271b9463390c7f7cafc2430190f5aaf879516617` |
| `tests/eval/matrix.yaml` | `fc07ba25f862026a50b946f4dcbbaf8871b6eafa37f26fa22457b72cba54fbab` |

The frozen review `docs/reviews/release/b12-harness-freeze-review-pi.md` does not apply
to these bytes. The new freeze needs a complete review.

## Pending integration item

The snippet routing entry for `pcba-design` is an integration item.

1. Apply the entry only when the integration tree contains the `pcba-design` skill.
2. The release worktree lacks the skill. A premature entry breaks the exact routing-set
   test at `tests/test_skill_packages.py` line 388:
   `set(real["skills"]) == {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}`.
3. Record the pending entry. Do not weaken the test.
4. The entry belongs to the integration step, not this correction.

## Packaging

The lead accepts P-6 and P-7 at the unchanged hashes in the 33-entry freeze. The scoped
acceptance has 25 packaging tests. It does not accept the harness or the final
distribution.

## Open limits

- The setup-fetch path is not implemented.
- The integrated skill artifacts are not accepted.
- The host adapters are absent.
- The measured isolation and the sentinel test are not implemented.
- Provider authorization stays zero.

## Next

1. The author runs the focused local tests.
2. The author freezes the complete input set.
3. Codex and Pi review the new freeze.
4. After the freeze message, no edit to its files until the lead explicitly releases the
   set. A reviewer finding does not release a frozen set.

## Limits

This record reads the authorization and hashes four files. It does not examine the
changed behavior. It does not approve the correction.
