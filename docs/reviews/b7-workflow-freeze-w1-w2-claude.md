# B7 workflow freeze record after W1 and W2 (claude-skill-dev)

Date: 2026-11-14 UTC. Freezes workflow.py and tests/test_pcb_fab_workflow.py for the combined review. No further checkpoint correction is made until the focused reports and the combined direction arrive.

Command: `uv run tests/test_pcb_fab_workflow.py`. Exit: 0 (background task). Result: 72 of 72 passed. Log: `docs/reviews/b7-workflow-evidence/workflow-run-w2.log`.

## Limits in the frozen code

- Container runs use the measured image identity (lock digest match), not the mutable tag. KiCad version measured: 10.0.5, compared with the lock.
- Each consumed input is read once; staging and digests come from the same bytes (W1). Absent optional inputs are recorded as `absent`.
- Supplier counts and severities use the explicit constraint-to-report mapping (W2): min_drill includes `hole_size` and `drill_out_of_range`; edge_keepout includes `edge_clearance` and `copper_edge_clearance`.
- Stage directories without the marker are refused, not removed.
- Writes stay under out/fab; a destination outside it is refused (exit 2). Results use `project_io.atomic_write`.
- Mask worker: 2-second caller timeout; 2-second in-process checkpoint budget; 2,000,000 candidate-pair cap; 10,000 flashes; 5 MB input; at most 100 listed pairs.

## SHA-256

```text
ca33910a5921c00a7ed8b57d35a7c79c1ff9a7ac053a94eaa7d7e9b2cc803f04  skills/pcb-fab-package/scripts/workflow.py
7cc2f7d80b0c3bad067962ae708aa24dd215cccf4ddeca67e9376c2fc37c83b1  tests/test_pcb_fab_workflow.py
```

## Not claimed

- Locks and atomic records are not complete across all shared records.
- The full consumed snapshot and the raw report, binding and publication sequence are under review.
- Final freshness at package time is under review.
- Supplier condition completeness, the manual region-mask route, and the standalone test are not complete.
