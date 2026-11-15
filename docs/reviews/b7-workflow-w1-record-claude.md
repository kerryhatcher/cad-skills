# B7 workflow W1 correction record (claude-skill-dev)

Date: 2026-11-14 UTC. Responds to b7-workflow-checkpoint-1-root.md (W1).

## Change

- Each consumed input is read once (`captured`). Staging writes those captured bytes. The recorded digests are computed from the same bytes.
- The profile is in the snapshot. The manual record is in the supplier snapshot. The package compares the same keys.
- Result files are written through `project_io.atomic_write`.
- The post-run comparison still reads the live files, and it is compared with the captured snapshot. It is not substituted for it.

## Measured

- `uv run tests/test_pcb_fab_workflow.py`: 68 of 68 passed, exit 0. Log: `docs/reviews/b7-workflow-evidence/workflow-run-68of68-w1.log`.
- The new W1 regression changes the source on disk after the capture. The staged bytes and the recorded hash match the captured bytes, and the live bytes are not substituted.
- The root probe `b7-snapshot-probe-root.py` hooks `shutil.copy2`, which the corrected staging no longer calls. Its printed JSON is a fixed value. It does not measure the corrected code, and the W1 regression above replaces it.

## Not claimed

- Raw report, binding and result publication sequence in full, supplier condition completeness, and the manual region-mask route. These remain open.

```text
efe3f47659a121e617b483ea9d77eb57e9c599370b1f3ac55264528ee4830441  skills/pcb-fab-package/scripts/workflow.py
8ff06d569a103f0da310379e66f3fc4ec8ecbdbaf152144a36342d59e7d99216  tests/test_pcb_fab_workflow.py
```
