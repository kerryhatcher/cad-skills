# B7 workflow continuation record (claude-skill-dev)

Date: 2026-11-14 UTC. Read this first after compaction. Do not restart accepted trials.

## Rules
- Environment and model unchanged. Haiku 5.5. No commits, no supplier action, no product code beyond the agreed interface.
- Python through uv, script files only. Herdr messages use the UTC date-time prefix from date -u, and the compatible CLI /proc/482044/exe at pane w1P:p3 for the lead. Reviewer panes: w1P:p5 (codex-skill-dev), w1P:p6 (pi-skill-dev).
- Frozen geometry: fab.py run_mask_worker guard, inspect_mask.py, macro_defs.py, export_inspect.py, inspect_slots.py, board_inventory_slots.py, tests/test_pcb_fab_package.py. Accepted; do not edit.
- Freezes go to root first. Do not request piecemeal reviews while changing files.
- Keep all earlier records; failed logs are evidence.

## Active correction (b7-workflow-correction-decisions-root.md, agreed by both reviewers)
Four parts: (1) capture and consume the same bytes, (2) project_lock and atomic_write with confined writes, (3) raw report / binding / result sequence, (4) measured KiCad report keys.

Implemented so far in skills/pcb-fab-package/scripts/workflow.py:
- Lock wrappers: design, supplier, package call _design, _supplier, _package inside PIO.project_lock; LockHeld and LockMalformed become exit 2.
- Binding files: design-binding.json and supplier-binding.json are written with atomic_write before their results; results carry binding_sha256.
- Package checks: every bound output compared with current bytes; a missing or mismatched binding refused; manual artifact compared with its recorded hash.
- Captured bytes: captured() reads each consumed input once; stage_project and digests use the same bytes; profile and manual are in the snapshot.
- Report keys: REPORT_KEYS mapping (W2), tested.
- Stage marker and runtime pin: from the earlier pipeline work, tested.

Not yet complete (be explicit):
- Export settings and profile are still parsed from live files in some paths (export_layers reads the project file); full parse from captured bytes is not done.
- review-source and review-gate in fab.py write with write_text, not atomic_write (fab.py is a frozen-adjacent caller; decide with root).
- Locks cover the three public operations; no test yet for a crash mid-publication.

## Test and run state
- Workflow test: tests/test_pcb_fab_workflow.py. Last full run: 72 of 72 (log docs/reviews/b7-workflow-evidence/workflow-run-w2.log), before the binding correction.
- Binding correction run in progress when this record was written: log /tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/corr-run.log (ID be3qt8sj6). Its focused cases: test_binding_and_lock (raw report, tampered binding, changed manual artifact, held lock, nested output link).
- Scratch project for manual runs: /tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/proj (design, supplier, package all exit 0 after the binding edit; package status qualified).

## Frozen records to keep
- b7-workflow-freeze-w1-w2-claude.md (W1/W2 freeze, sha 87807d0f...)
- b7-workflow-w1-record-claude.md, b7-workflow-w1-addendum-claude.md (corrects the fixed-value wording)
- b7-workflow-checkpoint-1-claude.md
- b7-r8-acceptance-mapping-claude.md (not yet updated for these results)
- b7-workflow-evidence/ logs: workflow-run-48of50-failed.log, workflow-run-51of51.log, workflow-run-59of59-rules.log, workflow-run-65of65-15a.log, workflow-run-68of68-w1.log, workflow-run-w2.log, workflow-run-interrupted-recursive.log

## Remaining supplier and evidence work (after this correction freeze)
- Supplier condition completeness: process-capability rows (mask alignment, drill tolerances, position tolerance) are recorded in the profile but not supplier rows.
- Manual route for region-producing masks: not implemented; stops with exit 2.
- Rows 22-45 of the acceptance mapping still not run (see b7-r8-acceptance-mapping-claude.md).
- Standalone acceptance: test the installed skill outside the repository with its own files.
- Skill document and mapping update with exact commands, exits, and artifacts.

## Freeze handoff
Root only. Send the complete correction freeze to root after the affected checks pass. Include exact file hashes of workflow.py and tests/test_pcb_fab_workflow.py, the run log path, and the limits. Do not send reviewer checkpoints in parallel.
