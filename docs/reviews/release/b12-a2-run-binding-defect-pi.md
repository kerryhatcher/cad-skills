# A2 run-binding defect from Pi

Date: 2026-11-15 UTC.
Author: pi-release-dev (Pi pane `w1P:pF`), reviewer.

Scope: check of the root concern on the artifact connection freeze. This report writes no
product file. It does not commit and it does not edit a frozen file. It made no provider
call.

## 1. Result

The current A2 expectation set accepts a minimal run root whose supplier result is only
`{"exit": 1}`. `all_pass` is True.

Probe: the frozen A2 expectations ran with the frozen fixture root and a temporary run root
that held only `out/fab/supplier/supplier-result.json` = `{"exit": 1}`.

| Expectation | Pass | Source of the evidence |
|---|---|---|
| `A2-status-overall` | True | Fixture `status.json` |
| `A2-status-package` | True | Fixture `status.json` |
| `A2-status-review` | True | Fixture `status.json` |
| `A2-status-fail` | True | Fixture `status.json` |
| `A2-status-pending` | True | Fixture `status.json` |
| `A2-supplier-exit` | True | Run `supplier-result.json` |
| `A2-package-absent` | True | Run root |

`all_pass`: True.

## 2. Cause

Five of the seven A2 expectations use `base: fixture` and read the immutable fixture
`status.json`. Only `A2-supplier-exit` and `A2-package-absent` read the run root. Thus the
run output does not prove the order failure or the pending condition. The fixture carries
that evidence, and the fixture does not change with the run.

## 3. Correction

1. Add a checker kind that finds a row in a produced JSON array by a key value, then compares
   one field. Proposed name `row_equals`. Fields: `path`, `json_path` (the array), `match_key`,
   `match_value`, `field`, `value`. A missing row fails.
2. Change the A2 run-facing expectations to read the produced
   `out/fab/supplier/supplier-result.json` rows under `base: run`:
   - The row with `condition == service.order_multiple` has `status == fail` and
     `mandatory == true`.
   - The row with `condition == silk_line_min_short_text` has `status == pending`.
   - The supplier exit is 1.
   - No package exists.
3. Keep the static fixture description separate. The fixture `status.json` checks
   (`overall == incomplete`, the command states, the counts) move to a fixture-level group or
   stay in `tests/test_artifact_fixtures.py`. They do not enter the run `all_pass`.
4. Add a negative test: the minimal run `{"exit": 1}` fails the row expectations.
5. Keep the real A2 run passing the new expectations.

## 4. Acceptance

| ID | Criterion |
|---|---|
| R-1 | The minimal run `{"exit": 1}` fails `all_pass` |
| R-2 | The frozen A2 run passes the new run-facing expectations |
| R-3 | The order failure is proven from the produced row, not the fixture |
| R-4 | The pending condition is proven from the produced row, not the fixture |
| R-5 | The static fixture description is checked separately and does not enter the run `all_pass` |
| R-6 | A changed mandatory flag or status in a produced row fails |
| R-7 | No provider call and no network call |
| R-8 | No frozen fixture byte changes |
| R-9 | A duplicate matching row is refused. The row selector matches exactly one row |
| R-10 | A matched row that lacks the compared field fails, even when the expected value is null |
| R-11 | A missing array, a non-list array, a non-object row, or a value with a different JSON type is refused |
| R-12 | The mandatory failure set and the pending set compare the produced rows with the exact named sets. Examine the mandatory flag for each named condition. Do not infer it from the condition name |

The lead adopted R-1 to R-8 in `docs/reviews/release/b12-a2-run-binding-correction-root.md`
and added R-9 to R-12 as explicit coverage. The order condition is the only mandatory
failure. The short-text silk condition is the only mandatory pending condition.

## 5. Scope note

This is a new correction to the artifact connection freeze. It changes `check_artifacts.py`,
`matrix.yaml`, and `test_artifact_expectations.py`. Those files are in the connection freeze,
so a new freeze supersedes them. A1 is not affected. Provider authorization stays zero.

## Limits

This report ran one local probe with a temporary run root. It made no provider call. It
changed no product file and edited no frozen file.
