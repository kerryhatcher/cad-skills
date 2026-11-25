# A2 run-binding replacement freeze review from Pi

Date: 2026-11-15 UTC.
Author: pi-release-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-a2-run-binding-freeze-claude.sha256` against R-1 to R-12
and the Codex F-1 finding. This report writes no product file. It does not commit. It made
no provider call.

## 1. Freeze and hashes

| Item | Before | After |
|---|---|---|
| Freeze file `b12-a2-run-binding-freeze-claude.sha256` | `4d250e0a163bdd514b4051fc3e909752c0ae7dcade5f8ddf10ba4b652e170c40` | Same |
| Entries | 199 | 199 |
| `sha256sum -c` | 199 of 199 OK | 199 of 199 OK |

Supersedes the connection freeze `09c052d8...`.

Key file hashes:

| File | SHA-256 |
|---|---|
| `tests/eval/check_artifacts.py` | `a815593112b48520443372d3377e2c1cfda3b18bb0aea65f6dabdd69d740c5f1` |
| `tests/eval/matrix.yaml` | `cb70bba9d738294cae42c942807320b1bf78ea5738e51104c89feb50f1ff0528` |
| `tests/test_artifact_expectations.py` | `c3b98fd9a4fb10b1ff67d6539b86dd4064da91cd2cff40edfab7ab1371124d81` |
| `tests/test_release_harness.py` | `55b247956ae1bbc05d29ee403ee2084b4b30c47478cc7018dd222f06846ac5d8` |

The A1 and A2 fixture entries are byte-identical to `artifact-a1-a2-freeze-r2-claude.sha256`.
`comm` reports no difference. The fixture bytes are unchanged.

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_artifact_expectations.py` | 23 of 23 passed, exit 0 |
| `uv run tests/test_artifact_fixtures.py` | 16 of 16 passed, exit 0 |
| `uv run tests/test_release_harness.py` | 65 of 65 passed, exit 0 |

No provider call and no network call.

## 3. Criterion check

| ID | Criterion | Result |
|---|---|---|
| R-1 | The minimal run `{"exit": 1}` fails | Pass. `test_minimal_run_fails_the_row_expectations` |
| R-2 | The frozen A2 run passes | Pass |
| R-3 | The order failure comes from the produced row | Pass. `A2-row-order-status` reads the run row |
| R-4 | The pending condition comes from the produced row | Pass. `A2-row-silk-status` reads the run row |
| R-5 | The fixture description is separate | Pass. `fixture_expectations`; the run set has no fixture base |
| R-6 | A changed mandatory flag or status fails | Pass. `test_wrong_order_status_fails`, `test_wrong_silk_mandatory_flag_fails` |
| R-7 | No provider or network call | Pass |
| R-8 | No frozen fixture byte changes | Pass |
| R-9 | A duplicate match is refused | Pass. `row_equals` refuses more than one match. `test_duplicate_order_row_is_refused` |
| R-10 | A missing compared field fails even for null | Pass. `test_missing_compared_field_fails_even_for_null` |
| R-11 | A missing or non-list array, a non-object row, or a wrong JSON type is refused | Pass. `_array_at` and `same_json`. `test_non_list_array_and_non_object_row_are_refused`, `test_string_flag_is_not_a_boolean` |
| R-12 | The exact named failure and pending sets, with the mandatory flag examined per condition | Pass. `A2-set-mandatory-fail` and `A2-set-mandatory-pending` |
| F-1 | The run expectations read the produced rows, not the fixture status | Pass |

## 4. Detail

- `check_artifacts.py` adds `row_equals` and `row_set_equals`. Both use `_array_at`, which
  refuses a missing array path and a non-list array. Both refuse a non-object row.
- `row_equals` refuses no match, a duplicate match, and a missing compared field.
- `row_set_equals` selects rows by a `where` mapping and compares the field multiset with
  `same_json`.
- `same_json` compares JSON types. A boolean never equals a number or a string. Lists and
  objects compare recursively. A null is distinct from a missing key.
- `json_equals` and `json_path_equals` now compare with `same_json`.
- Matrix A2 has 8 run expectations under `base: run` on
  `out/fab/supplier/supplier-result.json`, and 5 fixture expectations under
  `fixture_expectations`.
- The two mandatory conditions are `service.order_multiple` and
  `silk_line_min_short_text`. Each has a status check and a mandatory-flag check. The two
  set checks name the exact condition lists.
- `test_fixture_description_does_not_enter_the_run_outcome` asserts that the run ids and the
  fixture ids are disjoint and that every run expectation uses `base: run`.

## 5. Harness pointer

`tests/test_release_harness.py` points `FREEZE` at
`docs/reviews/b12-a2-run-binding-freeze-claude.sha256`. The freeze holds every consumed
harness input: all `tests/eval/*.py` modules, `matrix.yaml`, `distribution.yaml`, the five
release test files, the CLI help fixtures, the stub, and the 154 artifact fixture files. The
harness freeze completeness test passes on this pointer.

## 6. Concrete defects

None block acceptance.

### o1 The root symlink-ancestor limit applies

`resolve_under` calls `_has_link` on the root. A repository under a symlinked ancestor
reports a refusal for every expectation. This is the same host limit already recorded for
the source-path normalization. Use a checkout path with no symlinked ancestor in CI.

## 7. Verdict

R-1 to R-12 and F-1 are implemented and verified. The run expectations read the produced
rows. The exact named sets and the mandatory flags are checked. The typed comparison,
missing-field, duplicate-match and malformed-array refusals are covered. The fixture
description is separate. A1 and the fixture bytes are unchanged. The harness pointer covers
all consumed files.

I recommend acceptance at freeze
`4d250e0a163bdd514b4051fc3e909752c0ae7dcade5f8ddf10ba4b652e170c40`. Provider
authorization stays zero.

I made no edit during this review.

## Limits

This review ran focused local tests. It made no provider call and no CAD call. It changed no
product file.
