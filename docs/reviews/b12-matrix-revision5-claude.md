# B12 harness and matrix (revision 5)

Date: 2026-11-15 UTC.
Author: `claude-release-dev` (Claude, assigned model Haiku 5.5).
Base commit: `75d99da`. Branch: `work/release`.
Status: implementation for review. Zero provider calls. Authorization is zero. The paid gate stays closed.

This revision implements the agreed corrections: the root review R1 to R5, Codex C-1 to C-5, Pi's combined correction C-1 to C-5 with P-6 and P-7, and the lead's acceptance of 2026-11-15 02:12 UTC. It supersedes revision 4 (`b12-matrix-revision4-claude.md`) for the harness design. The counts and token limits of revision 4 do not change.

## 1. Three separate counts (C-2)

| Count | Meaning | Value now |
|---|---|---|
| Scheduled | The accepted design: 162 routing, 27 explicit, 9 artifact, 9 baseline, 3 compaction | 210 |
| Fixture-ready | A run whose skill is accepted and whose artifact fixture is frozen, or whose routing is ready | 0 |
| Authorized | A fixture-ready run that the lead allows for provider dispatch | 0 |

A run is refused before any provider dispatch when it is held (not fixture-ready) or not authorized. The refusal is a record. It does not stop the plan. A held run never reserves ledger budget. The check `check_plan` compares the executable set with the fixture-ready set and the authorization flag.

## 2. Enforcement (C-1, R1)

- `plan_runs` marks each run with `state` (`fixture-ready` or `held`), `hold_reason` and the lead's `authorized` flag.
- `execute` records a held run as `held`, an unauthorized run as `not-authorized`, and refuses both before the ledger reserve.
- `held_stub` is a tripwire. It raises `HeldCellReachedProvider` if a held run reaches it. It makes no external call. The test `test_mock_held_cells_never_reach_the_provider` runs the full 210-run plan through it.
- `live_provider` refuses every call. No adapter exists.

## 3. Test-only open matrix

The tests that check budget ceilings need dispatchable cells. They use `open_matrix(paid=True)`, a deep copy of the matrix with every readiness flag set in memory. No repository file changes. This proves only that the gate opens when all three inputs agree. It is not a dispatch approval.

## 4. R2 cross-skill prompts (C-3, R2)

| Target label | Task | Expected owner (kept outside the prompt) |
|---|---|---|
| `pcb-design` | Prepare a bare-board supplier package from this KiCad project. | `pcb-fab-package` |
| `pcb-fab-package` | Prepare assembly data for one variant of this KiCad project. | `pcba-design` |
| `pcba-design` | Change an electrical value in the schematic and board of this KiCad project. | `pcb-design` |

A test checks that each expected owner differs from its target and does not appear in its task text.

## 5. Artifact cells (C-4, R4)

- A1 (`pcb-design`) uses the accepted native edit fixture, `skills/pcb-design/examples/rc-edit`. The lead confirms that fixture. A1 has no B7/B8 runtime dependency.
- A2 (`pcb-fab-package`) needs a complete valid KiCad input project. None is selected yet.
- A3 (`pcba-design`) needs the PCBA implementation.
- Freshness uses hashes. The checker kind `sha256_binding` compares the output manifest's recorded source hash with the source file's current hash. Timestamps are not used for pass or fail.

## 6. Evidence fields (C-3, root R3)

| Field | Source | Status |
|---|---|---|
| `installed_path` | Our install step | Recorded |
| `scanned_paths`, `filesystem_selected_path` | Local filesystem inventory | Recorded. Not host evidence |
| `host_discovered_paths` | The host, measured | Not measured. Unavailable |
| `host_selected_paths` | The host output, from the trace | Not measured. Unavailable. Scored only from host output |
| `expected_paths` | The R2 and R1 expectation | Recorded |

A local scan never scores as selection. The routing score S1 is `None` (not measured) without host output.

## 7. Isolation (open)

The current harness has no filesystem restriction. The repository, credentials and sibling skills stay readable to a host with shell access. The final standalone isolation test requires a filesystem restriction measured with a repository sentinel that the evaluated process cannot read, without widening permissions. That execution adapter is not implemented. The limit is recorded in `isolation_prototype_limit` and in every run record. Until the sentinel test passes, the limit stays open and authorization stays at zero.

## 8. Freeze

The freeze `docs/reviews/b12-harness-freeze-claude.sha256` holds every harness module (`tests/eval/*.py`), the matrix and distribution files (`tests/eval/*.yaml`), both test suites, the packaging manifest, the fixture files, and this revision. The test `test_mock_freeze_lists_every_harness_input` checks that the freeze holds all of them.

## 9. Pending integration items

- `tests/snippet_envs.json`: add `pcba-design` mapped to `pcb`. Pending. Apply it only when the integration tree contains the `pcba-design` skill. A premature entry breaks the exact routing-set test in the release worktree. The release worktree does not contain that skill yet.

## 10. Open items

- The sentinel and filesystem restriction test (section 7).
- Measured host discovery and selection, once an adapter exists.
- The A2 complete input project and the A1 fixture confirmation.
- Lead authorization. The count of authorized runs stays zero.
