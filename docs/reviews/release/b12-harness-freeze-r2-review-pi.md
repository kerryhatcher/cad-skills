# Harness freeze r2 review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-harness-freeze-claude-r2.sha256` for B-1, B-2, B-3,
M-A and M-B, and the retained packaging acceptance. This report writes no product file.
It does not commit. It made no provider call.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-harness-freeze-claude-r2.sha256` has SHA-256
`09e77fa0f2d280f23918f1fd02b8afd5fd557e90b6b147932a1cb2a5897c32a6`. It matches the
author message.

| Item | Before | After |
|---|---|---|
| Entries | 33 | 33 |
| `sha256sum -c` | 33 of 33 OK | 33 of 33 OK |
| Freeze file hash | `09e77fa0...` | `09e77fa0...` |

The r2 freeze does not overwrite the first freeze. The first freeze stays as history.

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_release_harness.py` | 64 of 64 passed, exit 0 |
| `uv run tests/test_release_packaging.py` | 25 of 25 passed, exit 0 |
| `uv run tests/test_skill_packages.py` | 8 of 8 passed, exit 0 |
| `uv run tests/test_project_io.py` | 11 of 11 passed, exit 0 |

No provider call was made.

## 3. Correction checks

### B-1 Actual R2 task and expected path attachment

`plan_runs` calls `_attach_expectations` for every run. I ran a focused local check on the
planned runs:

| Check | Result |
|---|---|
| R2 runs | 27 (3 skills × 3 hosts × 3 repeats) |
| `pcb-design` R2 | expects `pcb-fab-package`, task text attached |
| `pcb-fab-package` R2 | expects `pcba-design`, task text attached |
| `pcba-design` R2 | expects `pcb-design`, task text attached |
| Runs with `expected_paths` | 210 of 210 |
| Expected owners in the prompt text | None |

`test_mock_planned_runs_carry_their_expected_paths` passes.

### B-2 Unavailable host discovery and selection

The run record now carries four explicit fields:

| Field | Value |
|---|---|
| `host_discovery_status` | `unavailable` |
| `host_discovered_paths` | `null` |
| `host_selection_status` | `unavailable` |
| `host_selected_paths` | `null` |

`score_run` treats a null host selection as not measured. A local scan never fills a host
field. The tests `test_mock_host_discovery_and_selection_are_unavailable` and
`test_mock_null_host_selection_is_not_measured` pass.

### B-3 Evidence and status separation

| State | `measured` | Result |
|---|---|---|
| `held` | False | Not in the measured table |
| `mock` | False | Not in the measured table |
| Missing evidence | False | Not treated as live |
| Explicit `live` | True | In the measured table |

`summarize` returns two outputs: the measured live table and an `execution_summary` for
every status. Measured live failures stay in the table. The tests
`test_mock_held_record_is_not_measured`, `test_mock_unauthorized_record_is_not_measured`,
`test_mock_unexecuted_record_is_not_measured`, `test_mock_missing_evidence_is_not_treated_as_live`
and `test_mock_mock_record_is_not_measured` pass.

### M-A Complete freeze input set

`test_mock_freeze_lists_every_harness_input` now requires `.gitignore`,
`.github/workflows/test.yml`, `skills/pcb-fab-package/sources.yaml`, and
`docs/reviews/b12-matrix-revision5-claude.md` in addition to the modules, matrix files,
tests and fixtures. It passes.

### M-B Authorized subset count

`readiness_counts` computes `authorized` as the number of runs with `state == "fixture-ready"`
and `authorized` true. The focused check gives `scheduled: 210`, `fixture_ready: 0`,
`authorized: 0`.

## 4. Pending integration item

`docs/reviews/b12-matrix-revision5-claude.md` section 9 records the pending
`pcba-design` snippet routing entry. It is not applied.

- `tests/snippet_envs.json` is unchanged.
- The exact routing-set test in `tests/test_skill_packages.py` still passes (8 of 8).
- The entry belongs to the integration tree when the `pcba-design` skill is present.

The pending entry is recorded without weakening the test.

## 5. Retained packaging acceptance

Packaging P-6 and P-7 remain accepted at the unchanged hashes.

| File | SHA-256 |
|---|---|
| `tests/eval/packaging.py` | `bc5e7e40971d5df02967bc9987ba9879c0d0abfe105db41970c414fe161b3db7` |
| `tests/eval/distribution.yaml` | `0bc2b200a7997c0951eb53fba439874b6f9b158c8027f23f73e865467d519c72` |

The packaging suite passes 25 of 25. Packaging acceptance stays separate from harness
acceptance.

## 6. Key file hashes

| File | SHA-256 |
|---|---|
| `tests/eval/matrix.yaml` | `fc07ba25f862026a50b946f4dcbbaf8871b6eafa37f26fa22457b72cba54fbab` |
| `tests/eval/run_case.py` | `bbd0ee6202c983e13566c13e370b13b912fdc7ba8ac76d927f41d4c1575f45c9` |
| `tests/eval/score.py` | `c80b80f73f3ae0cc3607c4d6ac58b0ab25296d7637e9151638b8facb68945c41` |
| `tests/eval/check_artifacts.py` | `76031aeeecf8bdf832358f57e0446001c4b6acbff2300e87e8453f3177eadad1` |
| `tests/test_release_harness.py` | `02305cde8681c483dcb66bfc088f074447c043e9923d4ad98114bcdab5108db6` |
| `tests/test_release_packaging.py` | `c19d4a7609e73c180013f5e4cae059fbf2fdb3cdcd270a99d9b3e80da7594c37` |

## 7. Open limits

- The filesystem restriction and the sentinel read test are not implemented. The limit is
  recorded in the matrix, the run records, and the sentinel test.
- No live provider adapter exists.
- The setup-fetch path is not implemented.
- The integrated skill artifacts are not accepted.
- Provider authorization is zero.

## 8. Verdict

B-1, B-2, B-3, M-A and M-B are implemented and verified. The complete freeze has 33
entries and all match. The focused local tests pass. Packaging acceptance is retained
separately.

I recommend the lead accept the harness freeze at these hashes. I do not approve a final
release. Provider dispatch remains unauthorized.

I made no edit during this review.

## Limits

This review ran focused local checks. It made no provider call and no CAD call. It changed
no product file.
