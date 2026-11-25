# B7 complete correction freeze (claude-skill-dev)

Date: 2026-11-15 UTC. Freeze for root only. Scope: fabrication (pcb-fab-package). The original worktree is `/mnt/storage/projects/cad-skills` on `main`, with uncommitted changes. No commit was made. Geometry files were not edited.

## Changes

1. C1 (confinement): the captured-profile scratch path is confined before any write. The design, supplier and package commands confine every child path. Test: `test_captured_child_link`.
2. C2 (package bytes): each consumed artifact is read once. The copy uses those bytes. The copy hash is compared with the measured hash. Test: `test_copy_change`.
3. C3 (manual record): the original path and hash are recorded. The final gate compares the original, the retained copy and the artifact. Test: `test_manual_original`.
4. Captured inputs: the lock, rules, settings, board record, drawing inputs, board hash and manifest inputs come from the capture. The capture now also holds `variants.yaml` and `mechanical/board-interface.json`. The manual artifact is read as a captured input. The unused `tool_version` reader is removed. Test: `test_captured_settings`.
5. Final freshness gate: runs immediately before `publish_dir`. It compares source inputs, supplier inputs, bindings and the original manual record. Test: `test_final_gate`.
6. Source review lock: `review-source` runs under `project_lock` across its reads and writes. A held lock returns exit 2 and writes nothing. Test: `test_review_lock`.
7. Interrupted binding and result: the run stops after the new binding and before the new result. The old result does not pass against the new binding. Test: `test_interrupted_binding`.

## Commands and results

- `uv run tests/test_pcb_fab_workflow.py`: 112 of 112, exit 0. Log `docs/reviews/b7-workflow-evidence/workflow-run-final-c4c6c7.log`. A run before this edit gave 95 of 95 (`workflow-run-pre-c4c6c7.log`).
- `uv run tests/test_pcb_tools.py`: 59 of 59, exit 0.
- `uv run tests/test_pcb_fab_package.py`: 101 of 101, exit 0.
- `uv run tests/test_project_io.py`: 11 of 11, exit 0.
- `uv run tests/test_skill_packages.py`: 8 of 8, exit 0.

## Limits

- The controlled copy change runs in-process: a hook changes the Gerber after the review gate and before the copies. It does not prove a race with another process.
- The interrupted run uses an exception after the binding write. It does not kill the process.
- `review.gate` still reads the live review pages. The B1 validator still reads the live project for cross-checks. Both are freshness-style reads and were not moved into the capture.
- Not claimed: supplier condition completeness for process-capability rows, the manual region-mask route, and standalone acceptance. These follow this correction.

## SHA-256

See `docs/reviews/b7-workflow-evidence/c4c6c7-freeze.sha256`. Source hashes:

```text
65f88be99b9fb758fc095e9086f954688eb1b240b5f192d69d9660bceb075f0b  skills/pcb-fab-package/scripts/workflow.py
f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be  skills/pcb-fab-package/scripts/fab.py
0686624ec3c0072279f747053dff649f8293cbcb02dfacb54e14c02d4d920932  tests/test_pcb_fab_workflow.py
```
