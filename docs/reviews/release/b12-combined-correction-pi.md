# B12 combined correction from Pi

Date: 2026-11-15 UTC. Revised to align the numbering with Codex C-1 to C-5 and to make
the filesystem-boundary detail explicit.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: reconcile the root review `docs/reviews/release/b12-revision4-review-root.md`
(R1 to R5), the Codex revision 4 review `docs/reviews/release/b12-revision4-review-codex.md`
(C-1 to C-5), the Codex packaging review P-6 and P-7, and the Pi findings into one
correction list. This report writes no product file. It does not commit. It makes no
provider call.

## 1. Agreement

The root corrections and the Codex corrections are correct. I reproduced each cause.

| Root | Codex | Finding | My check |
|---|---|---|---|
| R1 | C-1 | Held cells are not consumed by `plan_runs` or `execute` | Correct. `plan_runs` expands all 210 cells. `execute` dispatches every entry. `check_plan` asserts a 210 plan |
| R2 | C-2 | The R2 prompts repeat the direct task of the owner | Correct. Each R2 prompt names its own skill as the owner |
| R3 | C-3 | A local path scan is not host discovery | Correct. `isolate.discover` scans assumed directories. It calls no host. The returned path is the installed path |
| R4 | C-4 | A1 depends on B7/B8. A timestamp is not freshness evidence | Correct. A1 is held out for the B7/B8 dependency. The A2 drill check uses time |
| R5 | C-5 | The freeze omits `common.py`, `check_artifacts.py`, and other inputs | Correct. The 11-entry freeze omits both modules |
| — | P-6 | `magic: null` disables the format check for any content type | Correct. `_magic_ok(None, ...)` returns `True` |
| — | P-7 | A full copy at an unrelated path can enter distribution | Correct. `check_distribution` compares paths and patterns. It does not hash a distributed file against the excluded full-copy hashes |

Codex C-3 is the explicit version. My first list omitted the filesystem boundary. The
correction below keeps it.

## 2. One harness correction (C-1 to C-5)

### C-1 Enforce held cells before provider dispatch

1. Keep all 210 scheduled rows.
2. Mark each row as `scheduled`, `fixture-ready`, `held`, or `authorized`.
3. `execute` refuses a `held` or `unauthorized` row before the provider call. The refusal
   is a record with a stop reason. It is not an exception that stops the batch.
4. A stub provider fails if a held or unauthorized row reaches it. The stub makes no
   external call.
5. `check_plan` compares the fixture-ready set with the matrix. Keep the 210 scheduled
   total and the token limits.

State the counts separately:

| Count | Meaning | Current value |
|---|---|---|
| Scheduled | The accepted 210-cell design | 210 |
| Fixture-ready | Cells whose prompt, fixture and expectation are frozen and independently checked | Recompute after C-4. Proposal: pcb-fab-package A2 (6 runs) after its fixture review |
| Authorized | Cells the lead authorizes for provider dispatch | 0. No live adapter. No accepted integrated artifacts |

Do not present a fixture-ready count as an executable count.

### C-2 Correct the three R2 boundaries

Use a different owner for each R2 target cell.

| Target label | Task | Expected owner |
|---|---|---|
| `pcb-design` | Prepare a bare-board supplier package | `pcb-fab-package` |
| `pcb-fab-package` | Prepare assembly data for a variant | `pcba-design` |
| `pcba-design` | Change an electrical value in the schematic and board | `pcb-design` |

Keep the expected owner outside the prompt. Store it in the expectation data. The agent
must not see the expected owner in the task text.

### C-3 Separate path inventory from host discovery and skill selection

1. Use separate record fields for:
   - installed paths,
   - filesystem inventory,
   - host-reported discovery,
   - agent-selected paths,
   - expected paths.
2. Mark host discovery `unavailable` when the host cannot report it.
3. Do not score a local filesystem scan as host discovery or skill selection.
4. Keep `selected_paths` and `expected_paths` as lists. An empty list means no selection.
5. The current root lets host tools read the repository and sibling skills. Keep this
   prototype limit explicit.
6. For the final isolation test, add a filesystem restriction. Do not change trust,
   credentials, or host permissions.
7. Prove the boundary with a known repository sentinel. Record that the evaluated process
   cannot read it. An unsuccessful read is the necessary evidence.
8. Keep this limit open until that test passes.

### C-4 Correct artifact dependencies and freshness

1. A1 uses the accepted native edit fixture, plus the reviewed B11 coverage when it is
   integrated. A1 does not depend on the B7/B8 runtime.
2. A2 uses a complete valid input project. Keep A2 held until its fixture review passes.
3. A3 stays held until the PCBA package is accepted.
4. Every agent run still waits for the integrated skill artifact review and the lead
   authorization.
5. Replace the timestamp freshness rule. Use source and output hashes, bindings, and
   independent semantic expectations. Keep a timestamp as a supplemental observation.
6. Recompute the fixture-ready set after A1 is redefined.

### C-5 Complete the run record and the freeze

The run record items are applied. I verified `expected_paths` in section 8 and both
repository digests. The remaining item is the freeze.

The next freeze includes:

- Every module in `tests/eval/`, including `common.py` and `check_artifacts.py`.
- `matrix.yaml`.
- `tests/test_release_harness.py` and `tests/test_release_packaging.py`.
- Project-authored prompts and fixtures.
- The relevant skill hashes.
- Every other file that affects an evaluation.

Do not claim a full harness review from a partial freeze.

Add local tests for the held-cell dispatch, the readiness counts, the cross-skill R2
expectations, and the filesystem boundary. These tests make no provider call.

## 3. Separate packaging correction (P-6, P-7)

Packaging acceptance stays separate from the harness correction.

1. P-6: reject `magic: null` for `text/html`, `application/pdf`, and the XLSX content
   type. Keep `null` for header text only. Add a fixture test for each supported type.
2. P-7: hash every candidate distribution file against the excluded full-copy hashes.
   Fail when the bytes match. Add a project-authored regression fixture with a known
   source hash at an unrelated path. Do not block a project-authored PDF or HTML file by
   type alone.

## 4. Applied corrections confirmed

- My M-1 to M-4: held-out test, `expected_paths`, the conditional statement, both
  repository digests. Verified.
- My P-1 to P-5 and the Codex packaging agreement. Verified.
- Freeze 11 of 11. Harness 43 of 43. Packaging 22 of 22.

These confirmations do not close C-1 to C-5 or P-6 and P-7.

## 5. Recommendation

1. The author implements C-1 to C-5 in one change, and P-6 and P-7 in the packaging
   track.
2. The author freezes the complete input set from C-5.
3. Codex and Pi review the corrected freeze against this list.
4. The lead accepts the schedule, the fixture readiness, and the authorization
   separately.
5. No provider call starts until the lead authorizes it.

## Limits

This report read stable files and reproduced the root and Codex causes. It made no
provider call and no CAD call. It changed no product file.
