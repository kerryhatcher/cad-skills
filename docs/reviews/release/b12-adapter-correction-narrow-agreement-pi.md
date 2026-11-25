# Adapter correction narrow agreement from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: narrow agreement with the three blockers in
`docs/reviews/release/b12-adapter-correction-review-codex.md`. This report writes no
product file. It does not commit. It made no provider call.

## B-1 Baseline policy must enforce at planning or dispatch

I agree. `adapters.baseline_policy("codex")` returns
`refused-for-measured-evaluation`, but `run_case.plan_runs` and `run_case.execute` do not
read it. The mock open-matrix test dispatches all 210 entries.

Smallest correction:

1. `plan_runs` or `execute` reads `baseline_policy` for a baseline run.
2. A Codex baseline whose host skill set is unmeasured is refused before the adapter call.
   The refusal is a record with a reason.
3. A test opens every other gate and proves the Codex baseline cannot reach the adapter.

## B-2 The Pi baseline must not attach profiled skills

I agree. `adapters.command_for("pi", mode="none", skill_paths=[...])` adds `--no-skills`
and each `--skill` argument.

Smallest correction:

1. Attach `--skill` only in skill mode.
2. Reject or ignore `skill_paths` in baseline mode.
3. Add a test with a nonempty `skill_paths` value.

## B-3 Add live sampling while the child runs

I agree with the live sampling. One sentence in the Codex report is inaccurate, and the
lead noted it.

Current test order in `test_adapter_child_ticks_before_timeout_and_stops_after`:

1. `run = A.run_stub(...)` returns.
2. `before = len(ticks_file.read_text().splitlines())` is the first post-return count.
   It is taken before `time.sleep(1.5)`.
3. `time.sleep(1.5)`.
4. `after = len(...)` is the later count.

Thus the first post-return count is before the sleep. The Codex sentence "It also waits
1.5 seconds before its first post-timeout count" is incorrect. The real missing evidence
is live sampling while the child runs.

Smallest correction:

1. Run the stub in a background thread.
2. While the thread is alive, poll the tick file. Record at least two live samples. Assert
   the count increases. This proves ticks while the child runs.
3. After the thread joins, take the immediate post-return count.
4. Sleep the observation interval. Take the later count.
5. Assert the immediate count is at least the last live sample, and the immediate count
   equals the later count. This proves the writer stops.
6. Record the interval and the stop reason. Keep one attempt and no retry.

## Agreement

I agree with B-1, B-2 and B-3 and the smallest corrections above. No broad repeat is
needed. The measured boundary, the network isolation and the packaging acceptance are
unchanged. Provider authorization stays zero.

## Limits

This report compares the Codex blockers with the frozen bytes. It made no provider call
and no network call. It changed no product file.
