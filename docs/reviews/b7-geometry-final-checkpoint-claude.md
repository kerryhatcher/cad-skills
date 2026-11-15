# B7 geometry final replacement checkpoint (claude-skill-dev)

Date: 2026-11-14 UTC. Applies the final decisions in b7-geometry-final-decisions-root.md after both reviewers agreed. The earlier checkpoints stay unchanged as history.

Command: `uv run tests/test_pcb_fab_package.py` (exit 0, 98 of 98 passed).

## Final decisions applied

1. The radius no longer has a limit relative to the core side. Radii must be positive and finite; coordinates must be finite. A radius above half the core side follows the core-distance formula (regression: 1.7 mm core gap minus two 0.5 mm radii gives 0.7 mm). Overlap refusals stay.
2. The helper budget (2 seconds, checkpoints in inspect_mask.py) is separate from the caller timeout. Every public mask worker call (fab.py inspect-mask and both workflow mask calls) runs with a 2-second caller timeout in its own process group. A timeout returns exit 2 with a resource-limit finding and writes no report. Each run needs a fresh report path; an existing report is refused. Regression: a stalled worker through the public caller.
The caller timeout includes uv process start and stop overhead. No exact real-time scheduling is claimed.

## SHA-256

```text
5676a31124670f3f307e06e7c3d2e385881622e2769b4f263e4e5023e6c243db  skills/pcb-fab-package/scripts/inspect_mask.py
c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d  skills/pcb-fab-package/scripts/macro_defs.py
5be010bffda38af71ad1fba753d460bb65534d1d6c887999d8a1049d60ce759b  skills/pcb-fab-package/scripts/export_inspect.py
9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc  skills/pcb-fab-package/scripts/inspect_slots.py
ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838  skills/pcb-fab-package/scripts/board_inventory_slots.py
26b765635fd666577fa34dbf4a5ee0d8ad546b7188e82a385c66c791922954d2  tests/test_pcb_fab_package.py
```
