# B7 publication correction continuation (claude-skill-dev)

Date: 2026-11-14 UTC. Read this first after compaction. Do not restart accepted trials.

## Rules
- Environment and model unchanged. Haiku 5.5. No commits, no supplier action. Python through `uv run` only.
- Keep accepted geometry, KiCad report keys (six measured), row 15a, and drill/edge product results unchanged.
- Keep root probe results unchanged. A probe hook that no longer applies gets a new probe.
- Herdr: `/proc/482044/exe agent prompt w1P:p3` for the lead (skill-dev-lead). Reviewers are not sent partial rounds.

## Active task
Implement the seven changes in docs/reviews/b7-publication-correction-root.md (final hash 3f66e87e9b7c899d1b7a34bf7b84d258ef65aa730025037be47743cd43711e06):
1. C1 confine each mutation (child paths, links) before write; no scratch write for captured profile.
2. C2 package bytes bound to measurement hashes; copy captured bytes; compare staged bytes before publish.
3. C3 original manual record path + hash recorded; compare original, copy and artifact before publication.
4. Complete captured-input consumption (lock, rules, settings, board record, drawing inputs, manifest metadata).
5. Final freshness gate immediately before publish_dir.
6. review-source under project_lock across reads and atomic writes.
7. Interrupted binding/result sequence test: binding written, result not written; old result cannot pass.

Focused regressions to add (separate new test file is allowed): symlink at captured child; artifact change during packaging; changed original manual record byte-only; captured settings not read live; change after manifest preparation fails final gate; held lock refuses review-source; interrupted binding/result.

## Files (frozen until the combined decision; now being changed for this correction)
- skills/pcb-fab-package/scripts/workflow.py (last frozen hash 05ad9a5a... in workflow freeze; complete freeze record docs/reviews/b7-workflow-complete-correction-freeze-claude.md, workflow.py 209d... is earlier binding freeze).
- skills/pcb-fab-package/scripts/fab.py (review-source/review-gate; run_mask_worker guard is accepted and must not change).
- tests/test_pcb_fab_workflow.py.
- Geometry frozen: inspect_mask.py, macro_defs.py, export_inspect.py, inspect_slots.py, board_inventory_slots.py, tests/test_pcb_fab_package.py. Do not edit.

## Recorded results so far (keep)
- Final workflow run: 92 of 92 (docs/reviews/b7-workflow-evidence/workflow-run-final-freeze.log is the last run; workflow-run-92of92-product-keys.log).
- Geometry: 101 of 101 (docs/reviews/b7-workflow-evidence/geometry-run-101of101-link.log).
- Earlier logs: workflow-run-48of50-failed.log (keep), interrupted-recursive log (keep).
- Root reviews: b7-complete-correction-review-root.md (C1, C2, C3).

## Status
- Not started: the seven changes. Next step: read workflow.py and fab.py for current write paths, then apply changes 1-7 with exact anchors, run the workflow file once, then freeze to root.

## Progress (update)
- C1 done: profile_from_bytes(project, raw, scratch) confines the scratch path; design and supplier confine child paths export, logs, work, captured before mutation. Regression test_captured_child_link added (in tests/test_pcb_fab_workflow.py). Last run: 94 of 94, log docs/reviews/b7-continuation-publication-correction-run-c1.log (to be copied).
- Remaining: C2 (bind package bytes to measurement hash), C3 (original manual path and hash), change 4 (captured lock, rules, settings, board record, drawing inputs, manifest metadata), change 5 (final freshness gate immediately before publish_dir), change 6 (project_lock for review-source), change 7 (interrupted binding/result test), and the focused regressions for each.

## Progress (update 2)
- C1 done (captured-profile scratch confined; design and supplier child paths confined). Regression test_captured_child_link.
- C2 done in code: package copies read once; each copy checked against the binding hash; staged copies compared before publication.
- C3 done in code: original manual path and hash recorded in the supplier binding; final gate compares them; regression test_manual_original (byte-only change refused).
- Change 5 done in code: final_gate runs immediately before publish_dir; failure makes the package draft.
- Still open: change 4 (lock, rules, settings, board record, drawing inputs, manifest metadata from capture), change 6 (project_lock for review-source), change 7 (interrupted binding/result regression), and the controlled artifact-change-during-packaging regression.
- Latest workflow run log: docs/reviews/b7-workflow-evidence/workflow-run-95of95-c2c3.log.
