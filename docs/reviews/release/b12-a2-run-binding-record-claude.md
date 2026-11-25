# B12 A2 run binding: correction record

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Authority: `b12-a2-run-binding-correction-root.md` (lead, 2026-11-15 03:54 UTC), with Pi's R-1 to R-12 and Codex's review `b12-artifact-connection-review-codex.md`.

## Defect

The connection freeze (`b12-artifact-connection-freeze-claude.sha256`, 198 entries) accepted a minimal run `{"exit": 1}`. Five A2 expectations read the immutable fixture `status.json`. The run did not prove the order failure or the pending condition.

## Changes

1. `tests/eval/check_artifacts.py`:
   - `row_equals` finds exactly one produced row by a named selector and compares one field. It refuses a missing array, a non-list array, a non-object row, no match, a duplicate match and a missing field.
   - `row_set_equals` compares the exact multiset of a field over the rows selected by `where`.
   - All comparisons use JSON types. A boolean never equals a string or a number.
   - `json_equals` and `json_path_equals` use the same typed comparison.
2. `tests/eval/matrix.yaml`, A2:
   - `expectations` (run group, `base: run`): the order and silk rows, the order and silk mandatory flags, the exact mandatory failure set, the exact mandatory pending set, the supplier exit 1, and the absent package.
   - `fixture_expectations` (fixture group, `base: fixture`): the static description of `status.json`. It is kept out of the run outcome.
3. `tests/test_artifact_expectations.py`: 23 focused tests. Negative cases use temporary copies. They cover the minimal run, a missing row, a duplicate row, a wrong status, a changed mandatory flag, a string flag, an unexpected mandatory failure, a missing field under a null expectation, a non-list array and a non-object row.
4. `tests/test_release_harness.py`: `FREEZE` points to `docs/reviews/b12-a2-run-binding-freeze-claude.sha256`. The connection freeze stays as history.

## Unchanged

- Every A1 expectation and the A1 fixture.
- Every A2 fixture byte. The A2 fixture hashes match freeze r2 (`7b01b363`).
- The accepted path and link refusals.

## Results

- `tests/test_artifact_expectations.py`: 23 of 23.
- The minimal run `{"exit": 1}` fails the six row expectations.
- The frozen A2 run passes its run group. The frozen fixture description passes its fixture group.

## Limits

- No provider call. Provider authorization stays zero.
- `json_equals` and `json_path_equals` now compare JSON types. A `1` no longer matches `true`, and a `"1"` no longer matches `1`.
