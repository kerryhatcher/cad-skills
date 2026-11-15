# B7 workflow complete correction freeze (claude-skill-dev)

Date: 2026-11-14 UTC. Complete four-part correction for root, per b7-workflow-correction-decisions-root.md. The partial record b7-workflow-binding-freeze-claude.md and its claim of complete correction stay as history and are superseded by this record.

## Measured

- `uv run tests/test_pcb_fab_workflow.py`: final run in docs/reviews/b7-workflow-evidence/workflow-run-final-freeze.log (exit 0). Earlier full run with the product key fixtures: 92 of 92, docs/reviews/b7-workflow-evidence/workflow-run-92of92-product-keys.log.
- Decision 4 product results: a via drilled 0.2 mm (below the 10 mil minimum) reports drill_out_of_range on its UUID; a track 0.1 mm inside the outline reports copper_edge_clearance on its UUID; the min_drill and edge_keepout rows fail.
- Row 15a: the source design DRC omits the ignored finding and marks the excluded finding excluded; the staged DRC shows each active.

## Decisions

1. Captured inputs: profile, export settings, manual record and manual artifact are read once; staging and digests use the same capture.
2. Locks and atomic writes: project_lock around design, supplier and package; review-source writes through atomic_write after confinement; binding files written atomically.
3. Binding sequence: each result carries the hash of its binding file; package compares bound outputs and the manual artifact with current bytes.
4. Measured report keys only: track_width, clearance, annular_width, drill_out_of_range, hole_clearance, copper_edge_clearance.

## Limits

- Mask worker: 2-second caller timeout; 2-second in-process budget; 2,000,000 pair cap; 10,000 flashes; 5 MB input; 100 listed pairs.
- Container runs use the measured image identity from the lock; KiCad version measured as 10.0.5.

## Not claimed

- Boundary coverage of the drill and edge limits beyond the two deliberate cases.
- Supplier condition completeness for process-capability rows; the manual region-mask route; standalone acceptance.

## SHA-256

```text
05ad9a5ab565d1eb0ef18d6d9a8b0e4575e869c9d9f7cb344de33811e82435d4  skills/pcb-fab-package/scripts/workflow.py
84a09ec61fb3b453ff74e0a748b8974b17ac5739929697423e1c76bc615da3ca  skills/pcb-fab-package/scripts/fab.py
bf80316793ee9e4090112688e17714a80ce97ab427ebfe60040fe8863ea1b1e1  tests/test_pcb_fab_workflow.py
```
