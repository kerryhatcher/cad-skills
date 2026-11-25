# Final local repair review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-final-local-repair-freeze-claude.sha256` against the
release `docs/reviews/release/b12-final-local-repair-release-root.md` and the narrow
agreements. This report writes no product file. It does not commit. It made no provider
call.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-final-local-repair-freeze-claude.sha256` has SHA-256
`efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b`. It matches the
author message.

| Item | Before | After |
|---|---|---|
| Entries | 41 | 41 |
| `sha256sum -c` | 41 of 41 OK | 41 of 41 OK |
| Freeze file hash | `efbf8f61...` | `efbf8f61...` |

Four files changed from the previous freeze. The earlier 41-entry freeze stays as history.

| File | SHA-256 |
|---|---|
| `tests/eval/run_case.py` | `67777dc7e5cb420ff5c1c7ff63b6bafcbd16319d5ae02da998694ad0c77f0466` |
| `tests/eval/adapters.py` | `899247193a06e8c522ed6a0d34f50ceb774d1c1336d0e126369a570949f46b8a` |
| `tests/test_release_isolation.py` | `c1e37106b63a71cea7a86081228f8f0be308e277fbebdb3ddda49856fb045a90` |
| `tests/test_release_harness.py` | `d057b83d6d84740c75b66eb6725ce4f7ccf4f15f17e0a4cd68ca688ffc46e7fe` |

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_release_harness.py` | 65 of 65 passed, exit 0 |
| `uv run tests/test_release_isolation.py` | 29 of 29 passed, exit 0 |
| `uv run tests/test_release_packaging.py` | 25 of 25 passed, exit 0 |
| `uv run tests/test_skill_packages.py` | 8 of 8 passed, exit 0 |
| `uv run tests/test_project_io.py` | 11 of 11 passed, exit 0 |

## 3. Correction check

### B-1 Baseline policy at planning and dispatch

`run_case.plan_runs` reads `baseline_policy` for each baseline run and sets
`state = "refused-by-policy"` with a reason. `run_case.execute` reads the state before the
ledger reserve and records `refused-by-policy` with `evidence: "not-executed"` and zero
reported tokens.

`test_mock_codex_baseline_refused_with_every_gate_open` opens every other gate. The Codex
baseline is refused at planning and at dispatch. It does not reach the adapter stub and it
consumes no budget. The Claude and Pi baselines stay eligible.

### B-2 Pi baseline skill paths

`adapters.command_for` raises a `ValueError` for a Pi baseline with a nonempty
`skill_paths`. Skill mode attaches `--skill` once for each declared path. Baseline mode
carries `--no-skills` and no `--skill`.

`test_adapter_pi_baseline_rejects_a_nonempty_skill_path_list` and
`test_adapter_pi_skill_mode_attaches_only_the_declared_skill` pass.

### B-3 Live tick sampling

`adapters.run_stub_observed` runs the stub in a background thread. It samples the tick file
every 0.2 s while the thread is alive. After the join it records the immediate post-return
count, sleeps the declared 1.5 s, and records the later count.

`test_adapter_child_ticks_are_observed_live_then_stop` asserts at least two live increases,
a positive immediate count, an immediate count equal to the later count, one attempt, no
retry, exit 124, the stop reason, and the 1.5 s observation interval.

### Count-order sentence

`docs/reviews/b12-final-local-correction-claude.md` corrects the sentence. It states that
the earlier test took its first count after the return and slept before the second count,
and that the earlier wording was incorrect. The replacement samples while the stub runs.

## 4. Minor finding

### m1 The count-order correction document is not in the freeze

`docs/reviews/b12-final-local-correction-claude.md` is a report. It is not a harness input,
so the freeze does not include it. The freeze holds the modules, the tests and the fixtures.

Correction: none required. If the lead wants the correction sentence in the frozen record,
add the document to the freeze.

## 5. Unchanged scope

- The filesystem boundary result stays accepted at its measured scope: bwrap 0.13.1,
  sentinel hidden inside, readable outside, run root readable.
- The network result stays accepted: only `lo` inside, the local listener unreachable
  inside and reachable outside, no external endpoint.
- Packaging P-6 and P-7 stay accepted separately at their unchanged hashes.
- The authenticated host route is not established. Credential and configuration
  preservation is unmeasured for that route.
- Provider authorization is zero.

## 6. Verdict

B-1, B-2 and B-3 are implemented and verified. The count-order sentence is corrected. The
freeze has 41 entries and all match. The local suites pass.

I recommend the lead accept the final local repair at freeze
`efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b`. Provider dispatch
stays unauthorized.

I made no edit during this review.

## Limits

This review ran focused local checks. It made no provider call and no CAD call. It changed
no product file. It does not approve a release.
