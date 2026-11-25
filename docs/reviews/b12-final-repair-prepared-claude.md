# B12 final narrow repair (prepared, not applied)

Date: 2026-11-15 UTC.
Author: `claude-release-dev` (Claude, assigned model Haiku 5.5).
Status: prepared plan only. No product file is changed. The frozen set `docs/reviews/b12-adapter-correction-freeze-claude.sha256` (41 entries, SHA-256 `316f392c…bbf`) stays as it is. Pi's agreement is pending.

Source: the lead's request of 02:57 UTC, and the Codex correction report.

## R-1 Enforce baseline policy at planning and at dispatch

Current state: `baseline_policy` exists in `tests/eval/adapters.py`, but nothing calls it from the planner or the dispatcher. The Codex baseline is refused by the policy function alone.

Change:

- `tests/eval/run_case.py`, `plan_runs`: for each baseline run, call `baseline_policy(run["host"])`. When the status is `refused-for-measured-evaluation`, set `state` to `refused-by-policy` and `hold_reason` to the policy reason. Do this whatever the fixture and authorization flags say.
- `tests/eval/run_case.py`, `execute`: before the fixture and authorization checks, refuse any run whose state is `refused-by-policy`. Record `status: refused-by-policy`, `evidence: not-executed`, and no provider call. The check runs even when every gate is open.
- `readiness_counts`: a `refused-by-policy` run is never counted as fixture-ready or authorized.

Test: with every gate open (the test-only `open_matrix(paid=True)`), the Codex baseline runs are refused and the provider stub is never called. The Claude and Pi baseline runs stay eligible.

## R-2 Pi baseline rejects skill paths

Current state: `command_for("pi", mode="none", skill_paths=[...])` appends `--skill` for each path. The baseline argv must not carry a skill.

Change:

- `tests/eval/adapters.py`, `command_for`, Pi branch: when `mode == "none"` and `skill_paths` is non-empty, raise `ValueError("the Pi baseline rejects skill paths")`. When `mode == "none"`, append `--no-skills` only, and never `--skill`.
- Skill mode is unchanged: `--skill` is attached only in skill mode.

Test: the baseline argv contains no `--skill` token, and a baseline call with `skill_paths` raises.

## R-3 Observe tick growth while the child runs, then immediate and later counts

Current state: the tick test reads the tick file only after the adapter returns. The live growth while the child runs is not observed. The Codex report's sentence that the first count is taken after the sleep is incorrect. The count is taken after the return, and no sample is taken during the run.

Change:

- `tests/eval/adapters.py`: add `run_stub_observed(run_root, stub_args, timeout_seconds, probe, sample_seconds)`. It starts `run_stub` in a thread. While the thread runs, the main thread samples the tick-file line count every `sample_seconds` (0.2 s), and records each sample with a monotonic time.
- After the thread returns:
  - `immediate_count`: the count read at once after return.
  - `later_count`: the count read after a 1.5 s observation interval.
- Assertions:
  - The live samples show growth while the child runs: at least two samples with a count larger than the previous one, all before the stop.
  - `immediate_count == later_count`, so the tick file stopped growing after termination.
  - The record keeps every sample, the sample interval, the observation interval, and the stop reason (exit 124).
- No claim is made from an empty or unchanged file alone. A count of zero before the stop fails the test.

Test: `test_adapter_child_ticks_are_observed_live_then_stop` replaces the current tick test. The old test stays in place only as a record of the earlier measurement.

## R-4 Frozen files

No frozen file changes until the lead releases the set. After the repair passes the focused tests, the complete replacement freeze is generated. The 41-entry freeze stays as the reviewed record.

## Files this repair touches

| File | Change |
|---|---|
| `tests/eval/run_case.py` | R-1 planning and dispatch refusal, readiness counts |
| `tests/eval/adapters.py` | R-1 policy use, R-2 Pi baseline, R-3 observed runner |
| `tests/test_release_isolation.py` | R-2 and R-3 tests |
| `tests/test_release_harness.py` | R-1 test with open gates |
| `docs/reviews/b12-adapter-correction-freeze-claude.sha256` | Frozen; superseded only after release |

## Not in this repair

- Live dispatch. Provider authorization stays zero.
- The authenticated host route, which is unmeasured.
- The OSH Park reference and manifest entries.
- The `pcba-design` snippet entry, which belongs to integration.
