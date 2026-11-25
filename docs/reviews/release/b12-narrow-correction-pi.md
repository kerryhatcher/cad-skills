# B12 combined narrow correction from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: one narrow correction list for the harness. It combines Pi B-1 and B-2, the root
held-run scoring defect B-3, and the two minor items M-A and M-B. This report writes no
product file. It does not commit. It made no provider call.

The full evidence is in `docs/reviews/release/b12-harness-freeze-review-pi.md` and
`docs/reviews/release/b12-held-score-review-root.md`.

## Fingerprint

| Item | Value |
|---|---|
| Freeze file | `docs/reviews/b12-harness-freeze-claude.sha256` |
| Freeze file SHA-256 | `21168df2ef2d1d4902883adae8a27896c401f79728d7f9e096ea20aeb82f6d62` |
| Entries | 33, all match before and after |
| Harness tests | 53 of 53 |
| Packaging tests | 25 of 25 |
| Skill packages | 8 of 8 |
| Project I/O | 11 of 11 |

Keep the frozen files until Codex completes its report.

## B-1 Attach `expected_paths` and the R2 owner to the plan

The scheduled runs never set `expected_paths`. Only `score.py` reads it. The `r2_tasks`
expected owner is checked in the matrix but never attached to an R2 run.

1. In `plan_runs`, set `expected_paths` for each run:
   - R1, R4, R5, R6: the target skill.
   - R3: an empty list.
   - R2: the `expected_owner` from `r2_tasks` for the target skill.
   - Explicit, artifact, compaction: the skill under test.
   - Baseline: an empty list.
2. Carry the R2 task text in the plan, so the prompt matches the expectation.
3. Add a test that each plan entry carries `expected_paths`, and that S1 uses it.

## B-2 Mark host discovery and selection as unavailable

The install record holds `installed_path`, `filesystem_selected_path`, and `scanned_paths`.
It omits the host fields. A test asserts their absence.

1. Add explicit fields: `host_discovery_status: "unavailable"` and
   `host_selection_status: "unavailable"`, or `host_discovered_paths: null` with the
   status.
2. Keep `score_run` treating a missing or null host selection as `None` (not measured).
3. Keep the rule that a local scan never fills a host field.

## B-3 Missing evidence must not imply live evidence

The root probe measured two incorrect passes. A held record reached `summarize`, its
absent `evidence` field defaulted to `live`, and S4 and S5 counted passes.

1. `execute` sets `evidence: "not-executed"` on each `held`, `not-authorized`, and
   `not-executed` record.
2. The dispatched path sets `evidence: "live"`. The mock path sets `evidence: "mock"`.
3. `score_run` does not default a missing evidence value to live. Return the value as it
   is, or `"unavailable"` when absent.
4. `summarize` puts only `evidence == "live"` records in the measured release table. It
   puts `mock` and `not-executed` records in a separate execution summary.
5. Preserve every measured live failure. Do not exclude a failure to improve the result.
6. Add a test for each state: held, unauthorized, not-executed, missing evidence, mock,
   and an explicit measured live record. Assert that only the live record enters the
   measured table, and that a live failure stays.

## M-A Complete the freeze test required set

Add `.github/workflows/test.yml`, `.gitignore`, `skills/pcb-fab-package/sources.yaml`,
and the revision document to the `required` set in
`test_mock_freeze_lists_every_harness_input`. All four are in the current freeze.

## M-B Count the authorized subset

`readiness_counts` returns `fixture_ready if all(run["authorized"] for run in plan) else 0`.
A future per-cell authorization would zero the count. Compute `authorized` as the number of
runs with `state == "fixture-ready"` and `authorized` true. `check_plan` already builds that
subset.

## Order

1. Codex completes its report.
2. The author implements B-1, B-2, B-3, M-A and M-B in one change.
3. The author freezes the complete input set again.
4. Codex and Pi review the corrected freeze.
5. The lead accepts. Authorization stays zero.

## Limits

This list reads frozen files and the root probe. It made no provider call and no CAD call.
It changed no product file.
