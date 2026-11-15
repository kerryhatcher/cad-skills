# B7 geometry replacement checkpoint (claude-skill-dev)

Date: 2026-11-14 UTC. Replaces the frozen geometry checkpoint for the corrections in b7-geometry-corrections-root.md. The old checkpoint (b7-geometry-checkpoint-claude.md) stays unchanged as history.

Command: `uv run tests/test_pcb_fab_package.py` (exit 0, 93 of 93 passed).

## Corrections

- G1: every %AM must start a line; the macro body must equal the measured RoundRect text (inline and leading-space forms refused).
- G2: one byte snapshot; the report hash is computed from the bytes that were measured; the file is read once.
- G3: an elapsed-time budget of 2 seconds across reading, parsing and pair inspection, with checkpoints; the pair cap stays as an additional bound.
- Aperture holes refused (circle and rectangle).
- RoundRect: ten parameters, rotation zero, axis-aligned rectangle with a consistent corner cycle, radius within half the smaller side.
- Excellon: terminal M30 required; any record after it refused.

## SHA-256

```text
7d0e6592dcd504e662a4944107367f948b7833caa205d64e73d4706e479f1192  skills/pcb-fab-package/scripts/inspect_mask.py
c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d  skills/pcb-fab-package/scripts/macro_defs.py
5be010bffda38af71ad1fba753d460bb65534d1d6c887999d8a1049d60ce759b  skills/pcb-fab-package/scripts/export_inspect.py
9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc  skills/pcb-fab-package/scripts/inspect_slots.py
ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838  skills/pcb-fab-package/scripts/board_inventory_slots.py
070440293e9520dd75999a8acd4daebdf87947b1e547330f49cb7d04c6c3a5bb  tests/test_pcb_fab_package.py
```
