# B12 revision 4 root review

Date: 2026-11-15 UTC.
All 11 entries in `b12-matrix-freeze-claude.sha256` match.
The counts and token arithmetic agree with the lead decisions.
The following corrections are necessary before implementation acceptance.

## R1. Held cells are not enforced

`plan_runs` expands all 210 cells. `execute` sends all entries to an injected provider.
Neither function uses `held_out` or an accepted-artifact gate.
Thus the stated 198 count is metadata only. No live adapter exists, so zero provider runs are executable now.
Separate scheduled, fixture-ready, and authorized counts.
Enforce held cells before provider dispatch. Add a stub that fails if a held cell reaches it.
The stub must make no external call.

## R2. Neighbor prompts repeat direct tasks

The R2 entries name each target skill as the owner of its own normal task.
They repeat R1 and do not test the boundary with another skill.
Use a different owner for each R2 target cell. For example:

| Target label | Task | Expected owner |
|---|---|---|
| pcb-design | Prepare a bare-board supplier package | pcb-fab-package |
| pcb-fab-package | Prepare assembly data for a variant | pcba-design |
| pcba-design | Change an electrical value in the schematic and board | pcb-design |

Keep the expected owner outside the agent prompt. Do not put the answer in the task text.

## R3. Local path scans are not host discovery

`isolate.discover` scans assumed directories. It does not call any host.
The returned `selected_path` is the installed path, not evidence that an agent selected a skill.
Label these results as filesystem inventory. Keep observed host discovery and observed selection separate and unavailable until measured.
The static tests cannot establish host discovery behavior.

The current root does not prevent tools from reading the repository or sibling skills.
Keep this prototype limit explicit. It does not satisfy the planned standalone isolation test.
Implement and measure a filesystem restriction for the final test. Do not widen host permissions.
An unsuccessful read of a known repository sentinel is necessary evidence for that boundary.

## R4. Artifact dependencies and freshness

A1 tests `pcb-design`. It must not depend on another skill's B7/B8 runtime.
Use the accepted native edit fixture, plus the reviewed B11 coverage when integrated.
A2 depends on the fabrication skill and a complete valid input project.
A3 depends on the PCBA implementation. All live evaluations still wait for accepted integrated artifacts.

The timestamp checker is not evidence that manufacturing files match source bytes.
For release acceptance, use hashes, bindings, and independent semantic expectations.
Keep timestamps only as supplemental observations.

## R5. Freeze the complete harness input set

The freeze omits `tests/eval/common.py` and `tests/eval/check_artifacts.py`.
Both affect the tested behavior. Include all harness modules, matrix files, and applicable test fixtures in the next freeze.
Do not claim a full harness review from hashes of only some modules.

These corrections do not change the accepted 210-run schedule or the token limits.
The bounded packaging review remains separate.
