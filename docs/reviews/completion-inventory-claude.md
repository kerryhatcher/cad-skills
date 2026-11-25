# Completion inventory and B7/B8 trial command table (claude-skill-dev)

Date: 2026-11-15 UTC. Author: claude-skill-dev (model claude-haiku-5-5). Status: draft for lead review.

This report makes no code change. It does not change any frozen file. No provider call was made. No commit was made.

## 1. Restored context

- Checkpoint: `claude-handoff-checkpoint.md` (read in full).
- Accepted: B1 to B6, B7 publication (`b7-publication-acceptance-root.md`), setup freeze 2.
- The lead corrected the checkpoint. The B7 residual publication repair (`b7-residual-publication-repair-claude.md`, hash `08ec5765fa96e35988a2d08cb70b60a72687aa28bc551bb2a6f64b228ac93b06`) is accepted by both reviewers and by root. Do not repeat that review.
- The hashes of the four records listed in the checkpoint match the files on disk.

## 2. New blocker (measured, open)

The lead reports that a source entry with `path: sources.yaml` replaces the manifest with the fetched bytes and exits 0.

- Probe: `source-retrieval-manifest-probe-root.py`. Result: `source-retrieval-manifest-probe-root.json` (exit 0, `manifest_changed: true`, `response_replaced_manifest: true`).
- The accepted rule forbids manifest and profile mutation.
- Plan from the lead: reject protected input and output aliases before fetch.
- Status: no edit made. Frozen retrieval code stays unchanged until Codex completes its review.

## 3. Completion inventory

| # | Item | State | Evidence | Next action |
|---|---|---|---|---|
| 0 | Source retrieval manifest alias (section 2) | Open, measured | probe `.py` and `.json` | Codex review. Then the lead correction. Then rerun the retrieval tests. |
| 1 | Retrieval compatibility review of proposal revision `faa31c20` | Open. Codex accepted `63bb2d36` only. Pi has not reviewed the compatibility revision. | `source-retrieval-interface-claude.md` hash `faa31c20ff804c066600333f3d813db3203bda759048a56d9267056d5627d10e` | Codex and Pi review `faa31c20`. |
| 2 | Normalized source manifest | Exists in the release worktree. Not installed. The lead has not confirmed the hash. | Release hash `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f` (not verified by this session). Codex review pending. | Do not install before Codex acceptance. |
| 3 | Source retrieval tests | Passed on the frozen code: 48 of 48, exit 0. Re-run needed after item 0 and after item 2 is confirmed. | `b7-workflow-evidence/test_source_retrieval-run2.log` | Re-run after the correction and the manifest check. |
| 4 | Setup documentation | Freeze 2 accepted by both reviewers and root. Remaining items are measurements only: drill mirror, alternate mode, decimal zero format, zone-fill precondition, slot effect. | `oshpark-setup-documentation-freeze-2-claude.md` hash `9caa827162cdaeaddf2039cb8864cc1223af1771e723f32bf8e6780fd35ee268` | Measure the five items, or state them as limits. |
| 5 | Both reviewers' implementation review of the B7 residual freeze | Closed. Accepted by both reviewers and root (lead correction, section 1). | `b7-publication-acceptance-root.md`, `b7-residual-publication-release-root.md` | None. |
| 6 | B7/B8 trial command table with explicit paths | Draft in this report (section 5). | This file | Lead review. |
| 7 | Stale command-status prose in `SKILL.md` | Open | Checkpoint item 6 | Check each command status against the code in the final documentation pass. |
| 8 | Release provenance and distribution tests | Open. Release-owned. | `/mnt/storage/projects/cad-skills-worktrees/release` | Release team. |
| 9 | Standalone release acceptance | Not started | Checkpoint item 8 | After items 0 to 8. |
| 10 | B7/B8 full acceptance | Open. The publication record does not claim release readiness. Acceptance mapping has open rows (section 4). | `b7-r8-acceptance-mapping-claude.md`, `b7-workflow-completion-root.md` | Work the NOT RUN rows through product tests. |
| 11 | B9 to B12 | Pending. PCBA, mechanical and release worktrees exist. | `parallel-workstreams-root.md` | Per the lead plan. |

## 4. B7/B8 acceptance mapping status

Source: `b7-r8-acceptance-mapping-claude.md`. It was written on 2026-11-14, before the residual publication repair. Rows may have changed. Rerun the mapping before a claim.

- Rows marked NOT RUN (13): 15a, 16, 22, 23, 24, 25, 26, 28, 29, 31, 41, 44, 45.
- Rows marked partial (5): 6, 8, 13, 13c, 36. Rows 7a and 7b are judge-only and not run through a board.
- Row 16 (package without `fab.supplier_rules`) may now be covered by the residual row-completeness tests. Confirm with a test before changing its status.

A row marked NOT RUN is not a pass.

## 5. Trial command table (B7/B8 revision 8)

Paths are absolute. `EVID` means `/mnt/storage/projects/cad-skills/docs/reviews/b7-trial-evidence-r8`.

Limits of this table:

- The source record (`b7-r8-command-record.md`) is abbreviated. This table adds paths from the scripts and from `run-exit-codes.log`.
- No command was run again in this pass. Exits are the recorded values.
- Some working directories are inferred from relative paths in the scripts. They are marked as such.
- `mask-fx/make.py` writes to a hard-coded scratchpad path from a previous session. Its output is not reproducible from this repository until that path is replaced.

### 5.1 Mask fixtures (container, exports)

| Step | Command | Working directory | Recorded exit |
|---|---|---|---|
| F1 | `uv run "$EVID/mask-fx/make.py"` | `$EVID/mask-fx` (inferred) | 0 |
| F2 | `podman run --rm --pull=never --network none --security-opt label=disable -v <fixture-dir>:/work localhost/cad-skills-pcb:b6 kicad-cli pcb export gerbers --output /work/out/ --layers F.Cu,F.Mask /work/board.kicad_pcb` | Not recorded | m39, m40, m41, rr, m39merge, oval, overlap: 0 each |

Note for F2: the bind mount (`-v`) is not in the record. The `<fixture-dir>` placeholder is one of `$EVID/mask-fx/{m39,m40,m41,rr,m39merge,oval,overlap}`. The `m39merge` case adds `solder_mask_min_width 0.1016`.

### 5.2 Measurement and refusal (host, read-only)

| Step | Command | Working directory | Recorded exit |
|---|---|---|---|
| M1 | `uv run "$EVID/mask-fx/measure.py"` | `$EVID/mask-fx` (inferred) | 0 |
| M2 | `uv run "$EVID/mask-fx/refuse_rr.py"` (reads `rr/out/board-F_Mask.gts`) | `$EVID/mask-fx` (from code) | 0 |
| M3 | `uv run "$EVID/mask-fx/merge_check.py"` | `$EVID/mask-fx` (inferred) | 0 |
| M4 | `uv run "$EVID/mask-fx/merge_extent.py"` (reads `m39merge/out/board-F_Mask.gts`) | `$EVID/mask-fx` (from code) | 0 |

### 5.3 Exact RoundRect and refusal analyzer

Command pattern: `uv run --with gerbonara==1.6.3 --with shapely==2.2.0 "$EVID/geom-trial/analyze.py" <gerber>`

| Step | Gerber argument | Recorded exit | Result |
|---|---|---|---|
| A1 | `$EVID/mask-fx/rr/out/board-F_Mask.gts` | 0 | Nominal gap 4.0000 mil |
| A2 | `$EVID/mask-fx/oval/out/board-F_Mask.gts` | 1 | Obround refused |
| A3 | `$EVID/mask-fx/overlap/out/board-F_Mask.gts` | 0 | Negative gap printed. Not refused here. The refusal is a required implementation test. |

### 5.4 Staged exclusion restoration

| Step | Command | Recorded exit | Result |
|---|---|---|---|
| S1 | `uv run "$EVID/stage-proof/stage_proof.py" "$EVID/excl"` | 0 | Source: 7 active, 1 excluded `track_width`. Staged: 8 active. |

Note: the script comment says the argument is a scratchpad `excl/` directory. This run used the evidence copy.

### 5.5 Dependency lock

| Step | Command | Recorded exit | Note |
|---|---|---|---|
| D1 | `uv pip freeze` in the scratch venv `geom-trial/venv` | 0 | Output `geom-trial/pinned-lock-geom-trial.txt`. The exact invocation is not retained. |

### 5.6 Product test suites (repository)

| Step | Command | Retained result |
|---|---|---|
| T1 | `uv run tests/test_pcb_fab_package.py` | 101 of 101 passed (`b7-workflow-evidence/test_pcb_fab_package-residual.log`) |
| T2 | `uv run tests/test_pcb_fab_workflow.py` | 132 of 132 passed, exit 0 (`b7-workflow-evidence/workflow-run-residual.log`) |
| T3 | `uv run tests/test_source_retrieval.py` | 48 of 48 passed (`b7-workflow-evidence/test_source_retrieval-run2.log`). Re-run after item 0. |

The T1 and T2 command lines follow the convention in `AGENTS.md`. The log headers do not record them.

## 6. Open risks

1. The retrieval alias blocker (section 2). It is measured and not yet corrected.
2. `mask-fx/make.py` depends on a hard-coded scratchpad path. Replace it before the trial is claimed as reproducible.
3. Bind mounts and working directories are missing from the record. Recover them, or state the exits as recorded values only.
4. The acceptance mapping predates the residual publication repair. Rerun it.
5. Item 2 (normalized manifest hash) is not verified by this session.
