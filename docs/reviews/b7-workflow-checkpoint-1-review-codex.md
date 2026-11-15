# B7 workflow checkpoint 1 review

Date: 2026-11-14 UTC

## Reviewed boundary

At the start of this review, the files matched checkpoint 1:

| File | Checkpoint hash |
|---|---|
| `skills/pcb-fab-package/scripts/workflow.py` | `517e266c6f012191ad65b3cf95b1267dd995d5161ed23794792e331f36267fb3` |
| `skills/pcb-fab-package/scripts/fab.py` | `d410a64ac7c3e5477c8a4ae6c1258aff3b7f3324fca145cbb0966cb55821c255` |
| `tests/test_pcb_fab_workflow.py` | `93d8625f46ba0fab90312a833d431a5dfe9a3e63019c7964de8fae330d73232a` |

While I reviewed the checkpoint, `workflow.py` changed to `efe3f47659a121e617b483ea9d77eb57e9c599370b1f3ac55264528ee4830441`. The workflow test changed to `8ff06d569a103f0da310379e66f3fc4ec8ecbdbaf152144a36342d59e7d99216`. `fab.py` stayed unchanged. I did not review those later bytes. My findings below apply to checkpoint hash `517e...`. The later W1 correction record and active W2 edit remain outside this review.

## Findings

**W1: the snapshot does not bind the staged bytes.** I agree with `b7-workflow-checkpoint-1-root.md`. The checkpoint copies each source file, then hashes the live source. It later takes another live snapshot. The retained controlled probe shows `before_equals_after: true` while the recorded hash differs from the staged bytes. A later package can therefore treat a result as current when the design used different bytes.

The checkpoint also leaves its `extra` snapshot path unused. The selected profile and optional manual record do not enter the recorded snapshot. Operations read the profile, export settings, source rules and manual evidence from live paths. The run must capture each consumed input once, use those captured bytes for parsing and staging, then compare the live inputs with that capture before publication.

**Project lock and atomic records are missing.** The checkpoint calls `PIO.publish_dir`, but it does not call `PIO.project_lock` or `PIO.atomic_write`. `write_result` writes result JSON with `Path.write_text`. The package manifest also uses direct writes. A concurrent project command can change shared inputs or outputs during a run. A process interruption can leave a partial record. Hold the project lock across each operation. Use the local atomic-write helper for shared records.

**The result and binding pair is missing.** The design result has a `content_sha256` field. That field does not replace the binding file and result file pair required by r8. The raw ERC, DRC and export results lack the required per-result binding and result sequence. The supplier result binds the design result, but it has no separate binding file. Add the accepted bindings and write each result last through the atomic helper.

**W2: the checkpoint maps constraints to the wrong KiCad report names.** The supplier loop uses `RULE_CONSTRAINT` values to count DRC report types. KiCad 10.0.5 reports `hole_size` as `drill_out_of_range` and `edge_clearance` as `copper_edge_clearance`. The current loop can miss these findings. The [`KiCad 10.0.5 DRC source`](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.5/pcbnew/drc/drc_item.cpp) confirms these report and severity keys.

The checkpoint also writes `supplier_{key}` into `rule_severities`. A generated rule name is not a DRC severity key. Keep rule constraints separate from report and severity keys. Use `track_width`, `clearance`, `annular_width`, `drill_out_of_range`, `hole_clearance`, and `copper_edge_clearance` for the measured KiCad 10.0.5 types. Update row 15a to set the measured violation key to `ignore`, then confirm that the staged project sets that key to `error` and the violation still fails. Add focused drill and copper-edge findings with their measured report types.

## Checks that match this scope

The measured image identity check, unmarked-stage refusal, outside-destination refusal, and `publish_dir` call match the stated checkpoint. The 15a test checks source-byte preservation and exclusion removal. Its severity assertion does not establish the accepted KiCad severity behavior until W2 receives the correction above. I did not rerun the 65-test suite. The retained 65-of-65 log hash is `1f43022423500c11b52575651832c290997f2d40b49cb43a47b4c273eaa7b69e`.

## Verdict

I do not accept checkpoint 1. W1, W2, the missing project lock, non-atomic result writes, and missing binding/result files block this scope. This review makes no qualification claim. Supplier evidence completeness and the later W1/W2 edits remain outside this checkpoint review.
