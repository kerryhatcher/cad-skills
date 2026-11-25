# B12 revision 4 review from codex-release-dev

Date: 2026-11-15 UTC.

Scope: revision 4, the machine-readable matrix, and the harness freeze. This report combines the root review, the Pi review, and the Codex findings. Packaging findings stay in `packaging-review-codex.md`.

## Freeze and count review

I ran `sha256sum -c` on `docs/reviews/b12-matrix-freeze-claude.sha256`. All 11 entries match. The freeze omits `tests/eval/common.py` and `tests/eval/check_artifacts.py`. It does not cover all harness inputs.

The scheduled arithmetic matches the lead's values:

| Item | Count |
|---|---:|
| Scheduled runs | 210 |
| Held artifact and baseline runs for A1 and A3 | 12 |
| Candidate runs after these two holdouts | 198 |
| Authorized provider runs now | 0 |
| Local installation checks | 24 |

The 198 candidate runs are not executable now. A2 still awaits fixture review. The integrated skill artifacts do not have final acceptance. The host adapter is absent. R2 prompts also need correction. Record the schedule, fixture readiness, and provider authorization as separate values. Do not describe 198 as the current executable count.

The run limits and token arithmetic match the lead's decision:

| Group | Runs | Tokens per run | Maximum reported tokens |
|---|---:|---:|---:|
| Routing and explicit invocation | 189 | 30,000 | 5,670,000 |
| Artifact, baseline, and compaction | 21 | 250,000 | 5,250,000 |
| Scheduled total | 210 | — | 10,920,000 |
| Batch limit | — | — | 12,000,000 |

Keep the current host-reported token limit text. It states the post-request enforcement limit. No provider call can test this ledger.

## Required harness corrections

### C-1: Enforce held cells before provider dispatch

`plan_runs` includes all 210 scheduled rows. `execute` sends every row to its provider function. Neither function reads the held-out statuses. Thus, A1 and A3 can reach the provider when a provider function exists.

Keep all 210 rows in the schedule. Mark each row as scheduled, fixture-ready, held, or authorized. Make the dispatch step refuse a held or unauthorized row before it calls the provider. Keep an attempt record with the stop reason.

Add a local test with a provider stub that fails if a held or unauthorized row reaches it. The stub must not make a network call. Test the 210 scheduled count, the 12 held cells, and each readiness count.

### C-2: Correct the three R2 boundaries

The current R2 prompts repeat each target skill's direct task. They do not test neighboring skill selection. Use these cross-skill prompts:

| Target label | Task | Expected owner |
|---|---|---|
| `pcb-design` | Prepare a bare-board supplier package | `pcb-fab-package` |
| `pcb-fab-package` | Prepare assembly data for a variant | `pcba-design` |
| `pcba-design` | Change an electrical value in the schematic and board | `pcb-design` |

Keep the expected owner outside each prompt. Store it in the expectation data. The agent must not see the expected owner in the task text.

### C-3: Separate path inventory from host discovery and skill selection

`isolate.discover` scans assumed directories. It does not call a host. Its installed path does not prove host discovery or agent selection.

Use separate record fields for installed paths, filesystem inventory, host-reported discovery, agent-selected paths, and expected paths. Mark host discovery unavailable when the host cannot report it. Do not score a local filesystem scan as host discovery or skill selection.

The current root still lets host tools read the repository and sibling skills. For the final isolation test, add a filesystem restriction. Do not change trust, credentials, or host permissions. Use a known repository sentinel and record that the evaluated process cannot read it. Keep this limitation open until that test passes.

### C-4: Correct artifact dependencies and freshness evidence

- A1 must use the accepted native edit fixture. It must not depend on the B7/B8 runtime. Include reviewed B11 coverage when the integrated `pcb-design` skill includes it.
- A2 must use a complete valid project input. Keep A2 held until its fixture review passes.
- A3 stays held until the PCBA package is accepted.
- All agent runs still wait for integrated skill artifact review and lead authorization.

The timestamp comparison does not prove that manufacturing outputs match the source. Use source and output hashes, bindings, and independent semantic expectations. Keep timestamps as supplemental observations only.

### C-5: Complete the run record and freeze

Add `expected_paths` to the revision 4 run record. The scorer reads this field, but section 8 omits it.

Record both repository digests for the local KiCad image. Keep the image ID and `--pull=never` evidence.

Freeze all harness modules, including `common.py` and `check_artifacts.py`. Also freeze the matrix, both test files, project-authored prompts and fixtures, relevant skill hashes, and all other files that affect an evaluation. Do not claim a full harness review from a partial freeze.

Add local tests for held-cell dispatch, readiness counts, cross-skill R2 expectations, and the filesystem boundary. These tests make no provider call.

## Findings from the separate packaging review

The packaging review still records P-6 and P-7. A null magic value can skip format checking for non-header data. A copy of supplier bytes outside known paths can enter the distribution. Keep these findings in `packaging-review-codex.md`. Do not mix packaging acceptance with matrix acceptance.

## Result

The schedule, counts, token limits, and isolation mode design match the lead's decisions. The current revision does not resolve C-1 to C-5. Correct the dispatch gate, R2 prompts, discovery evidence, artifact checks, run record, and freeze before the final review.

Pi reports 43 of 43 harness tests and 22 of 22 packaging tests. I did not run these tests. I made no provider calls and no product edits.
