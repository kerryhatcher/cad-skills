# B7 geometry final checkpoint review (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: `b7-geometry-final-checkpoint-claude.md`
(SHA-256 `5cc534630c858221af4802f6e55e9a626c89d8d8a6187b460b97b6fde9516f73`) and the two final
decisions in `b7-geometry-final-decisions-root.md`.

This report gives the review result only. It does not change the frozen files. Full B7/B8 workflow
acceptance stays separate.

## Hash check

The six measured hashes match the final checkpoint before and after this review. The last measurement follows.

```text
5676a31124670f3f307e06e7c3d2e385881622e2769b4f263e4e5023e6c243db skills/pcb-fab-package/scripts/inspect_mask.py
c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d skills/pcb-fab-package/scripts/macro_defs.py
5be010bffda38af71ad1fba753d460bb65534d1d6c887999d8a1049d60ce759b skills/pcb-fab-package/scripts/export_inspect.py
9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc skills/pcb-fab-package/scripts/inspect_slots.py
ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838 skills/pcb-fab-package/scripts/board_inventory_slots.py
26b765635fd666577fa34dbf4a5ee0d8ad546b7188e82a385c66c791922954d2 tests/test_pcb_fab_package.py
```

The earlier checkpoints stay unchanged. The replacement checkpoint and the first checkpoint have the same
hashes as before.

## Declared command

I ran the declared command one time. It returned exit 0 and 98 of 98 passed.

## Decision 1 verification

- Radius above half the core side: a core gap of 1.7 mm minus two 0.5 mm radii gives a web of
  `0.7000000000000002` mm. The run returns exit 1 with the 30 mil limit. The core-distance formula holds.
- Overlap refusal: the same shape with a 0.4016 mm core gap returns exit 2 and
  `unsupported "overlapping cluster: objects 0 and 1 overlap by 0.598400 mm"`.
- A wide gap returns exit 0 and `pass`. No upper radius bound stays.
- The helper budget still refuses a zero budget with "the elapsed-time limit of 0.0 seconds was exceeded
  during reading".

## Decision 2 verification

- A stalled worker through `fab.py inspect-mask` returns exit 2, mentions the caller timeout, leaves no
  report, and stops in 2.109 s of wall time.
- An existing report path returns exit 2 with "the report path exists; give a fresh report path". No stale
  success survives.
- A fresh report path with a passing web returns exit 0 and writes the report.

## Concrete corrections

1. Stale documentation in `inspect_mask.py`. The module docstring says "with a radius inside the measured
   range" (lines 16 and 17). The final decision removes that limit. The code is correct. The docstring must
   say that the radius is positive and finite, with no core-side limit.
2. Record binding for decision 2. The caller timeout lives in `skills/pcb-fab-package/scripts/fab.py`
   (`run_mask_worker`, SHA-256 `d6d13ab732190b7be0a029fb1f3ce27c81506fd8f94c83e1989cffe2cbc2adeb`). The
   workflow uses it (`skills/pcb-fab-package/scripts/workflow.py`, SHA-256
   `bca595484e0298362d5173a5b94ae37360855a3ade8b3e114188c68c412adbb1`). Neither file is in the checkpoint
   SHA-256 block. The record cannot bind the decision 2 claim without them. Add both files or their hashes to
   the replacement record.
3. `workflow.py` changed at 2026-11-14 11:46:38 UTC, after the checkpoint was written. It is a changing file
   and it is outside this frozen geometry scope. The full workflow review stays separate.

## Verdict

The two final decisions are implemented and independently verified. The earlier six corrections stay. I
accept the geometry checkpoint as the corrected basis after the stale docstring is fixed and the record adds
the caller-timeout files. Full B7/B8 workflow acceptance stays pending.
