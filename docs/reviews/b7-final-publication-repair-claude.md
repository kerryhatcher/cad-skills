# B7 final publication repair freeze (claude-skill-dev)

Date: 2026-11-15 UTC. Frozen checkpoint for root, under `b7-final-publication-repair-root.md`. The earlier freeze `b7-complete-correction-freeze-claude.md` stays as history. Original worktree `/mnt/storage/projects/cad-skills` on `main`, uncommitted. No commit made. Geometry files unchanged.

## Changes

- **C1 (complete destination writes).** Every output file of design, supplier and package goes through `write_out`. It confines the complete destination, then calls `PIO.atomic_write`. The destinations of each command are refused before any mutation (`design_destinations`, `supplier_destinations`, package final and staging). Worker reports (slots, top and bottom masks) are written to a private execution directory `out/fab/supplier/measure`, then published through `write_out`. The worker geometry code is unchanged. The profile scratch file uses `write_out`.
- **C2 (one byte set).** `Reader` reads each package input once. Decisions and copies use the same bytes. The design result is checked for its own content hash and for its binding. The supplier checks each consumed design output (inventory, drills, both masks, silkscreen) against the design binding before any measurement. The measurements read the private copies only. Their hashes are recorded as `measure_inputs` and bound in the supplier binding.
- **C5 (validated bytes at publication).** The manifest is validated once. If validation finds a defect, the manifest is rewritten and validated again. The final gate then compares the staged manifest with the validated bytes, and each staged output with its recorded hash and size. It also rejects links, missing outputs and unexpected files. A gate failure raises `pkg.final_gate`, keeps the staging directory, and does not rename it. Nothing is published, and no rollback is claimed.

## Tests (new or changed)

- C1: `test_link_destinations` covers a profile file, a dangling profile file, a design output, a design log, a supplier output and a worker report. Each case expects exit 2, the link kept, and the outside target unchanged. `test_captured_child_link` (directory link) is kept.
- C2: `test_result_change` (changed design result refused, supplier result kept). `test_transient_input` (a Gerber changed during the mask measurement; the measured hash is the captured hash).
- C5: `test_staged_gerber` and `test_staged_manifest` (changes after validation refused, nothing published). `test_final_gate` and `test_copy_change` expect exit 1 and no published package.
- C7 and the others: `test_interrupted_binding`, `test_captured_settings`, `test_review_lock`, `test_manual_original` and the stale-source test are updated to the new rule. They keep their accepted behavior.

## Commands and results

- `uv run tests/test_pcb_fab_workflow.py` (before the stale-source test update): 123 of 124, one expectation updated. Log `docs/reviews/b7-workflow-evidence/workflow-run-c1-c2-c5.log`.
- `uv run tests/test_pcb_fab_workflow.py` (final): 124 of 124, exit 0. Log `docs/reviews/b7-workflow-evidence/workflow-run-c1-c2-c5-final.log`.
- No broad suite was run in this checkpoint.

## Limits

- The controlled copy change, the staged-byte changes and the transient input are in-process hooks. They do not prove a race with another process.
- The interrupted run uses an exception, not a killed process.
- `review.gate` and the B1 validator still read live project files. These are freshness-style reads, not captured.
- The `drawing-facts` and `drawing` CLI commands in `fab.py` write directly. They are outside design, supplier and package and are not changed here.
- Not claimed: supplier condition completeness, manual region-mask support, setup retrieval, standalone release.

## SHA-256

```text
ac38b636a748816a530f89f7a951296da4fd140304a66ee74e5b09261f7a48a7  skills/pcb-fab-package/scripts/workflow.py
f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be  skills/pcb-fab-package/scripts/fab.py
58b8a45f20e73907b5ca538950189e157f190676f4e67688883732d770276338  tests/test_pcb_fab_workflow.py
fe9d234629587afefac82aed3a25e9c2c1305b786d67c0dabedc43b9ac38f059  docs/reviews/b7-workflow-evidence/workflow-run-c1-c2-c5-final.log
a59b899b055610df555eb8f0002061be0e1a0ed62b0795d696c7fa1451e7a920  docs/reviews/b7-workflow-evidence/workflow-run-c1-c2-c5.log
```
