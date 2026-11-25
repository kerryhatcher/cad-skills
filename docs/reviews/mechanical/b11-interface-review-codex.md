# B11 interface review: Codex

Date: 2026-11-15.

## Decision

The B11 scope is sufficient for implementation after the lead accepts the interface below. Keep B11 inside `pcb-design`. Do not change shared contracts without lead assignment. The B5 board-only STEP does not prove component fit.

## Interface recommendations

1. Keep the existing `board-interface.json` schema unchanged for this batch. Use its `extensions` object for the fixture's coordinate declaration and source-to-contract transform. Record source axes, target axes, translation, rotation, and board anchor. State the transform as a matrix or an unambiguous ordered transform. Do not infer the anchor from `origin_mm`.
2. Make a new asymmetric fixture. Give it a nonzero board origin, unequal hole offsets, a connector frame, and a bottom-side part. Record the bottom-side orientation and side in the fixture data.
3. Include a connector insertion volume in the enclosure model. Define its frame, extent, and clearance owner. Measure connector orientation and free insertion space after the transform.
4. Keep component evidence separate from constraints. Record each component revision, evidence type, measured or datasheet height, and source hash. Mark a proxy as a conservative envelope. Mark unsupported height evidence `unconfirmed`.
5. Keep expected geometry as dimensions with units and tolerances. Compare transformed outline, holes, board thickness, connector frame, insertion volume, and component envelopes. Report measured error for each comparison. Reject any error over its declared tolerance.
6. Bind the board revision and PCB hash, interface hash, component revisions, enclosure source hash, export settings, release ID, and each produced STEP/DXF hash in one release record. Keep exact output hashes for identity. Use geometric tolerance checks for regenerated STEP and DXF files.
7. Stop release publication on the first stale input. Name the input and expected and measured hashes. A board, interface, component, or enclosure change must run the geometry checks again.

## Acceptance cases

- The asymmetric fixture passes its declared transform and all geometry tolerances.
- A mirrored transform, reversed Y axis, incorrect anchor, or untransformed fixture fails a named comparison.
- A fixture without the bottom-side part, connector frame, or insertion volume fails.
- A connector with reversed orientation or an obstructed insertion volume fails.
- A part over a confirmed height limit fails. An unevidenced limit remains `unconfirmed`.
- A conservative proxy can pass its envelope check. The result does not claim detailed component fit.
- A geometry difference within tolerance passes even when an export hash changes. The exact new hash remains in the release record.
- A board, interface, component revision, enclosure source, or release ID mismatch blocks publication with the first mismatch named.
- A trial that uses only the B5 board STEP reports board geometry only. It does not report component clearance.

## Scope and limits

Use the local KiCad image for export trials. Do not pull a new image. Do not edit `pcb.py` or copied contracts until the lead assigns that work. Keep all B5 files and records unchanged. This review covers the frozen preparation report and plan only. It does not accept an implementation.
