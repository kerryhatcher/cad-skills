# Harness freeze review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: complete review of `docs/reviews/b12-harness-freeze-claude.sha256` and the agreed
harness C-1 to C-5. Packaging P-6 and P-7 are checked separately and do not decide the
harness acceptance. This report gives concrete blockers once. It writes no product file.
It does not commit. It made no provider call.

## 1. Freeze, hashes before and after

The freeze file `docs/reviews/b12-harness-freeze-claude.sha256` has SHA-256
`21168df2ef2d1d4902883adae8a27896c401f79728d7f9e096ea20aeb82f6d62`.

| Item | Before | After |
|---|---|---|
| Entries in the freeze | 33 | 33 |
| `sha256sum -c` | 33 of 33 OK | 33 of 33 OK |
| Freeze file hash | `21168df2...` | `21168df2...` |

No reviewed file changed during the review.

Key file hashes, unchanged before and after:

| File | SHA-256 |
|---|---|
| `tests/eval/matrix.yaml` | `fc07ba25f862026a50b946f4dcbbaf8871b6eafa37f26fa22457b72cba54fbab` |
| `tests/eval/run_case.py` | `59eeb7505cdbbee3b253b0fc11277fbb9c161bf79321e7f8a1d0d43ec2c4950d` |
| `tests/eval/isolate.py` | `1a86f73b41ae7d6f454d7be0c53b263b28d092a8ee9cc9125758cc71fc18710e` |
| `tests/eval/score.py` | `a1f1d160d887c634b3b986c0454dfcbfb1f11392c85de6cf7a6e8e586a6a556c` |
| `tests/eval/check_artifacts.py` | `76031aeeecf8bdf832358f57e0446001c4b6acbff2300e87e8453f3177eadad1` |
| `tests/eval/packaging.py` | `bc5e7e40971d5df02967bc9987ba9879c0d0abfe105db41970c414fe161b3db7` |
| `tests/test_release_harness.py` | `9c1293ac5a70d0651a906cb414e3137caa970c991a0e4322744b09a8a1c64692` |
| `tests/test_release_packaging.py` | `c19d4a7609e73c180013f5e4cae059fbf2fdb3cdcd270a99d9b3e80da7594c37` |

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_release_harness.py` | 53 of 53 passed, exit 0 |
| `uv run tests/test_release_packaging.py` | 25 of 25 passed, exit 0 |
| `uv run tests/test_skill_packages.py` | 8 of 8 passed, exit 0 |
| `uv run tests/test_project_io.py` | 11 of 11 passed, exit 0 |

No provider call was made.

## 3. Correction status

| ID | Correction | Result |
|---|---|---|
| C-1 | Enforce held cells before dispatch | Pass. `plan_runs` sets `state`, `hold_reason`, `authorized`. `execute` refuses a held or unauthorized run before the ledger reserve. `held_stub` is a tripwire. Five tests cover it |
| C-2 | Correct the three R2 boundaries | Partial. The matrix has the three cross-skill tasks. The plan does not attach the expected owner to the R2 runs. See B-1 |
| C-3 | Separate inventory from host discovery and selection | Partial. Inventory fields exist (`installed_path`, `filesystem_selected_path`, `scanned_paths`). Host fields are omitted, not marked unavailable. See B-2 |
| C-4 | Artifact dependencies and freshness | Pass. A1 uses the native edit fixture. `sha256_binding` replaces timestamps. Tests cover a stale binding and a matching binding |
| C-5 | Complete the run record and freeze | Freeze pass. Run record incomplete. See B-1 and B-2 |
| P-6 | Reject magic null for HTML, PDF and XLSX | Pass. `MAGIC_REQUIRED_TYPES` and a test for each type |
| P-7 | Hash distributed files against full-copy hashes | Pass. `check_distribution` hashes each file when a root is given. Tests cover a full copy at an unrelated path and a project-authored PDF |

## 4. Blockers

### B-1 The scheduled runs do not carry `expected_paths` or the R2 expected owner

`tests/eval/run_case.py` never sets `expected_paths`. `_entry` and `_one_run` omit it. A
search of `tests/eval/` finds `expected_paths` only in `score.py`.

Consequences:

1. `score.score_run` reads `run.get("expected_paths", [])`. A run record without the field
   has an empty expected list. A correct routing selection then scores S1 as a fail.
2. The `r2_tasks` expected owner is checked in the matrix tests only. The plan uses
   `case="R2"` and does not look up the expected owner. Thus the R2 boundary is not
   testable in a run.
3. Revision 5 section 6 says `expected_paths` is "Recorded". It is not.

Correction:

- In `plan_runs`, set `expected_paths` for each run.
  - R1, R4, R5, R6: the target skill.
  - R3: an empty list.
  - R2: the `expected_owner` from `r2_tasks` for the target skill.
  - Explicit, artifact, compaction: the skill under test.
  - Baseline: an empty list or the baseline expectation.
- Carry the R2 task text in the plan so the prompt matches the expectation.
- Add a test that each plan entry carries `expected_paths`, and that S1 uses it.

### B-2 Host discovery and selection are omitted, not marked unavailable

The `install` record holds `installed_path`, `filesystem_selected_path`, and `scanned_paths`.
It does not hold `host_discovered_paths` or `host_selected_paths`. The test
`test_mock_install_record_separates_inventory_from_host_selection` asserts that the host
fields are absent.

Revision 5 section 6 lists host discovery and host selection as fields with the status
"Not measured. Unavailable". The lead C-3 requires separate record fields and an explicit
unavailable marker.

Correction:

- Add `host_discovery_status: "unavailable"` and `host_selection_status: "unavailable"`
  to the record, or add `host_discovered_paths: null` with a status field.
- Keep `score.score_run` treating a missing or null host selection as `None` (not
  measured), not as a fail.
- Keep the rule that a local scan never fills a host field.

### B-3 Missing evidence defaults to live in the measured table

The lead measured this with a local probe. I reproduced the cause in `score.py`.

1. `score_run` returns `"evidence": run.get("evidence", "live")`. A record without an
   `evidence` field becomes live.
2. `summarize` excludes only `evidence == "mock"`. A `held`, `not-authorized`, or
   `not-executed` record has no `evidence` field. It defaults to live and enters the
   measured table.
3. S4 and S5 then count a pass, because such a record has no claims and no external
   event. The lead measured two incorrect passes.

Correction:

- `execute` sets `evidence: "not-executed"` on each `held`, `not-authorized`, and
  `not-executed` record.
- The dispatched path sets `evidence: "live"` and the mock path sets `evidence: "mock"`.
- `score_run` does not default a missing evidence value to live. It returns the value as
  it is, or `"unavailable"` when the field is absent.
- `summarize` puts only `evidence == "live"` records in the measured release table. It
  puts `mock` and `not-executed` records in a separate execution summary.
- Preserve every measured live failure. Do not exclude a failure to improve the result.
- Add a test for each state: held, unauthorized, not-executed, missing evidence, mock, and
  an explicit measured live record. Assert that only the live record enters the measured
  table, and that a live failure stays.

This concerns the accepted separation between local tests and measured provider results.
It is a blocker for the measured table.

## 5. Minor corrections

### M-A The freeze completeness test has gaps

`test_mock_freeze_lists_every_harness_input` requires `tests/eval/*.py`, `tests/eval/*.yaml`,
both test files, and the fixture files. It does not require `.github/workflows/test.yml`,
`.gitignore`, `skills/pcb-fab-package/sources.yaml`, or the revision document. All four are
in the current freeze, but a later freeze can drop one without a test failure.

Correction: add those four paths to the `required` set, or state the freeze scope.

### M-B The authorized count is all-or-nothing

`readiness_counts` returns `fixture_ready if all(run["authorized"] for run in plan) else 0`.
A future per-cell authorization would zero the count instead of counting the authorized
subset. The current global flag makes this correct.

Correction: compute `authorized` as the count of runs with `state == "fixture-ready"` and
`authorized` true. `check_plan` already builds that subset.

## 6. Open limits, recorded

- The filesystem restriction and the sentinel read test are not implemented. The limit is
  in `matrix.yaml` `isolation_prototype_limit`, in `run_case.ISOLATION_LIMIT`, and in
  `test_mock_sentinel_boundary_stays_incomplete`. The test states that it does not prove
  isolation. This matches the lead decision. The limit stays open.
- No live provider adapter exists. `live_provider` refuses every call.
- Authorization is zero. The matrix sets `paid_batch_authorized: false`.
- The repository, credentials and sibling skills stay readable to a host with shell
  access. The prototype does not isolate them.

## 7. Verdict

The harness is close. C-1, C-4, C-5 (freeze), P-6 and P-7 pass. C-2 and C-3 are partial.
B-1, B-2 and B-3 block harness acceptance. M-A and M-B are minor.

The combined narrow correction is `docs/reviews/release/b12-narrow-correction-pi.md`.

Packaging acceptance stays separate. I confirm P-6 and P-7 are implemented and the
packaging suite passes. The packaging gate still needs the complete input set and the
setup fetch path.

## Limits

This review ran focused local regressions. It made no provider call and no CAD call. It
changed no product file. It does not approve a release.
