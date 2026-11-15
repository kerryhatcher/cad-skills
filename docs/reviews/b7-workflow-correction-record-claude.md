# B7 workflow correction record (claude-skill-dev)

Date: 2026-11-14 UTC. Records the work on `b7-workflow-correction-decisions-root.md` after the partial freeze in
`b7-workflow-binding-freeze-claude.md`. The partial freeze and its claim of complete correction are kept as history.
This record corrects that claim: the four-part correction is not complete until the checks below pass.

## Deviation (recorded once)

Host `python3` was used for empty probes and some text edits in earlier commands of this batch (for example a
`python3 -c ""` no-op and a JSON read). AGENTS.md requires `uv run` for all host Python. From this point all Python
runs through `uv run`.

## Changes in this step

- Decision 4: `REPORT_KEYS` holds only the six measured report keys: `track_width`, `clearance`, `annular_width`,
  `drill_out_of_range`, `hole_clearance`, `copper_edge_clearance`. The unmeasured aliases `hole_size` and
  `edge_clearance` are removed. Constraint names are used only in the generated rule file. The `supplier_<key>`
  severities are removed. The unused `RULE_OF_TYPE` map is removed.
- Decision 4 test: `test_row_15a` uses the measured `track_width` key and the segment midpoint of the first track.
  It runs an ignore-severity case and an exclusion case as separate supplier runs. Both must still fail the trace row.
- Decision 1: the profile, the export settings, the manual record and the manual artifact are read once into a capture.
  The profile and export settings are parsed from captured bytes. The staging and the digests use the same capture.
  The package copies the manual artifact from the supplier copy, not from the live project.

## Not yet established

- Decision 4 asks for product results for the drill and copper-edge mappings. No fixture has produced
  `drill_out_of_range` or `copper_edge_clearance` in a KiCad run yet.
- The live project supplier record is compared with the captured profile (`manufacturing/supplier.yaml`).
- `review-source` and `review-gate` in `fab.py` still write with `write_text`, not `atomic_write`.

## Measured in this step

- `uv run tests/test_pcb_fab_workflow.py`: 82 of 82 passed, exit 0. Log: `docs/reviews/b7-workflow-evidence/workflow-run-82of82-decisions.log`.
- Covers the row 15a ignore-severity and exclusion cases with the measured `track_width` key, the W2 report keys, and the binding and lock cases.
- Not measured: the drill (`drill_out_of_range`) and copper-edge (`copper_edge_clearance`) product results. This stays open for decision 4.
05ad9a5ab565d1eb0ef18d6d9a8b0e4575e869c9d9f7cb344de33811e82435d4  skills/pcb-fab-package/scripts/workflow.py
bf7337b18dd3f047fe2269bb04635b16c87cd26f25e2bf843a695d51ec2c9adc  tests/test_pcb_fab_workflow.py

## Row 15a source-first premise (measured)

- `uv run tests/test_pcb_fab_workflow.py`: 86 of 86 passed, exit 0. Log: `docs/reviews/b7-workflow-evidence/workflow-run-86of86-15a-premise.log`.
- Ignore case: the source design DRC bytes omit the target `track_width` finding. The staged DRC bytes show it active.
- Exclusion case: the source design DRC bytes mark the target finding `excluded: true`. The staged DRC bytes show it active.
- The target is matched by segment UUID in the KiCad report items, not by a dictionary value.
