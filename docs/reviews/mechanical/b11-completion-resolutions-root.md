# B11 completion resolutions

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The current implementation remains frozen until the lead releases the combined correction.
The Codex completion review is still pending.

## Drill outputs

Use `--excellon-separate-th` with the accepted origin and millimeter settings.
For the staged board basename `board`, use `board-PTH.drl` and `board-NPTH.drl`.
Measure these names in the local image and record them in the export settings.
Bind them to `drill_pth` and `drill_npth`, respectively.
Do not give a mixed drill file either role.
Refuse unsupported drill classes with a named finding.

## Cavity and connector body

The cavity polygon is the board outline offset outward by `clearance_mm`.
Include the chamfer. Keep the fixed 0.01 mm tolerance.
Test proxy containment against this cavity.
A point on the board edge lies in the outward cavity.
There is no mating-edge exemption.

The declared connector body extends inward from its mating face.
Inward is opposite the transformed insertion vector.
The fixture has zero body overhang beyond that face.
Declare this placement and `body_length_mm: 4.0` in the project-authored proxy evidence.
Keep `body_length_mm` separate from `insertion_depth_mm`.
This test proxy makes no datasheet or detailed component-fit claim.

## Existing integrity requirements

Consume captured bytes or private copies of those bytes.
Do not follow a freshness test with another live read for the calculation.
Run the measured image ID, not a mutable tag.
Keep the accepted explicit release fields, byte counts and mismatch order.
Confine paths from records before any read or write.
Recompute comparison completeness and status before release.
Complete the final freshness and output-integrity gate before publication.
Use thin local dispatch for `pcb.py mechanical export`, `fit` and `release`.

The current positive evidence remains historical.
Run the corrected positive and negative cases before the next complete freeze.
