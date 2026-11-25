# Matrix revision 4 review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: check of `docs/reviews/b12-matrix-revision4-claude.md` and `tests/eval/matrix.yaml`
against the lead values of 2026-11-15 01:51 UTC. This report gives the result. It writes
no product file. It does not commit.

## Freeze and tests

| Item | Result |
|---|---|
| Freeze list | `docs/reviews/b12-matrix-freeze-claude.sha256`, 11 entries |
| `sha256sum -c` | 11 of 11 OK, exit 0 |
| `uv run tests/test_release_harness.py` | 41 of 41 passed, exit 0 |
| `uv run tests/test_release_packaging.py` | 22 of 22 passed, exit 0 |

## Token figures

I derived every number independently from `tests/eval/matrix.yaml` through
`tests/eval/common.py`.

| Item | Lead value | Matrix value | Result |
|---|---|---|---|
| Routing | 162 | 162 | Match |
| Explicit invocation | 27 | 27 | Match |
| Artifact, skill arm | 9 | 9 | Match |
| Artifact, baseline | 9 | 9 | Match |
| Compaction | 3 | 3 | Match |
| Scheduled total | 210 | 210 | Match |
| Install checks | 24 | 24 | Match |
| Routing and explicit limits | 10 turns, 300 s, 30000 tokens | Same | Match |
| Artifact, baseline, compaction limits | 30 turns, 1200 s, 250000 tokens | Same | Match |
| Worst case | 189 × 30000 + 21 × 250000 | 10920000 | Match |
| Batch cap | 12000000 | 12000000 | Match |
| Margin | 1080000 | 1080000 | Match |
| Automatic retries | 0 | 0 | Match |

The conflict in revision 3 is gone. The batch cap is 12000000 tokens. The per-run caps
match the lead values.

The accounting limits are stated honestly: host-reported tokens, charge at the ceiling
when the count is missing, reserve before a run, stop before the next request, and no
cutoff of a started request.

## Codex blockers

| Blocker | Result |
|---|---|
| One-skill install cannot test routing | Answered. Routing installs all three. A test covers it |
| R2 boundaries | Answered. One frozen prompt for each skill in section 4 and `routing_r2_prompts` |
| `selected_path` shape | Answered. `selected_paths` and `expected_paths` are lists. Empty means no selection |
| User-scope paths | Answered. Per-host temporary home. A test covers discovery and the unchanged real home |
| Ignored-run limit | Answered. Every plan entry carries the isolation limit |
| Token caps conflict | Answered. Section 7 and the matrix match the lead |
| One-run option | Answered. Withdrawn. The three-repeat matrix stands |
| Install count | Answered. 24 local checks. Zero paid calls |
| Blocked artifact cells | Answered. A1 and A3 held out. 12 runs |

## Findings

### M-1 `executable_now` is not validated by a test

`tests/eval/matrix.yaml` holds `held_out` and `held_out_summary.executable_now: 198`. No
test reads those keys. A later edit can change the held-out set and leave the summary
stale.

Correction: add a static test that asserts
`scheduled_runs - sum(held_out runs) == executable_now`, and that each held-out cell is
absent from the paid plan.

Severity: low. The figures are correct now.

### M-2 The run record omits `expected_paths`

Section 8 lists `discovered_paths` and `selected_paths`. It does not list
`expected_paths`. `tests/eval/score.py` reads `expected_paths`.

Correction: add `expected_paths` to the run record list in section 8.

Severity: low.

### M-3 The executable count is conditional

Section 3 says executable paid runs are now 198. The lead states that provider execution
waits for the accepted integrated skill artifacts. Routing needs all three skills
installed. Thus the routing and explicit cells for `pcba-design` also wait for its
acceptance.

Correction: state that 198 is the count after all three skills are accepted, minus the
two blocked artifact cells. Do not imply that 198 runs can start before acceptance.

Severity: low. The status line at the top already states the condition.

### M-4 The image has two repository digests

The image ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`
matches the local `localhost/cad-skills-pcb:b6` image. That image has two repository
digests:

- `sha256:e1b50b506fd1eb2b3d84e6c52affa01b0847417fa23e960b8042be93518ff8c3`
- `sha256:f0e90890954589c72f1fde8dd0ee14b83dd865c2c3f2bdfa5eaf4f117f77274e`

Section 10 and the matrix name only the second one. It is valid. The record is
incomplete.

Correction: record the image ID with both repository digests, or state that the tag
resolves to the ID and give the full digest list. Keep `--pull=never` and no pull.

Severity: low. The image ID, the strongest identity, matches.

## Confirmed correct

- The counts and the token ceilings match the lead values.
- Held-out A1 and A3 leave paid execution. 210 − 12 = 198.
- Install checks use no provider call. Zero paid install calls.
- Symlink is limited to Codex and Pi.
- Claude Code discovery paths are proposals until measured. The record is honest.
- The mock-only suite refuses a live provider and keeps mock results out of the release
  table.

## M-1 to M-4 verification

The author applied M-1 to M-4 before this report was final.

| ID | Verification |
|---|---|
| M-1 | `test_mock_held_out_runs_leave_198_executable` reads `held_out` and `held_out_summary`. It asserts 12 held-out runs and `executable_now == 198`. It passes |
| M-2 | Section 8 now lists `expected_paths` |
| M-3 | Section 3 states that 198 is conditional on all three skills accepted. `matrix.yaml` adds `conditional_on` |
| M-4 | Section 10 and `matrix.yaml` list both RepoDigests and bind the tag to the image ID. `test_mock_image_repo_digests_are_both_listed` passes |

The rewritten freeze `docs/reviews/b12-matrix-freeze-claude.sha256` has 11 entries. All
11 match. The harness suite is now 43 of 43 passed. Packaging stays 22 of 22.

## Verdict

Accept with M-1 to M-4. The token figures match the lead values. The blockers from
Codex's matrix review are answered. M-1 to M-4 are applied and verified. None blocks the
interface.

## Limits

This review ran the local test suites. It made no provider call and no CAD call. It
changed no product file.
