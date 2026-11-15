# B7 geometry checkpoint (claude-skill-dev)

Date: 2026-11-14 UTC. Modules and tests for the geometry subset, frozen before the remaining fab.py work.

Command: `uv run tests/test_pcb_fab_package.py` (exit 0, 80 of 80 passed).

## SHA-256

```text
ade74723a60442ced804686e8784526c283f619064cccf17f842116cad0af328 skills/pcb-fab-package/scripts/inspect_mask.py
c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d skills/pcb-fab-package/scripts/macro_defs.py
4b1b87dcbb00d69eba86b7192683466e851443dde59a6b78f5cf823bd8ce1f20 skills/pcb-fab-package/scripts/export_inspect.py
9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc skills/pcb-fab-package/scripts/inspect_slots.py
ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838 skills/pcb-fab-package/scripts/board_inventory_slots.py
182ca9e52faa55cc557e67f57462192b7d36ce2d22e8ec35c1ab44584ae72341 tests/test_pcb_fab_package.py
```

Covered: rectangle and mixed interior overlap refused; edge contact is merged_opening; exact RoundRect macro text checked; unknown macro and other apertures refused; pair checks bounded at 2000000 and stored pairs bounded at 100; slot tolerance 501 and 502 nm; Excellon subset (INCH, M72, missing declarations, duplicate tool, tool width precision) refused.
