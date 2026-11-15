---
name: pcb-fab-package
description: Check a bare printed circuit board against a supplier profile and build a fabrication package. Use for supplier profile validation, design checks, supplier conditions, slot and solder-mask measurements, the source review of supplier pages, the fabrication drawing sheet, and the package gate. Not for PCB layout, assembly, or ordering.
---

# PCB fabrication package

This skill checks a bare printed circuit board against a supplier profile and writes a fabrication package. It runs alone. It uses no file from another skill at run time. Its copies of the B1 contract, the B6 inventory worker and the stored supplier pages are byte copies.

## Commands

Run every command through `uv run`. Give explicit paths. Each command returns the exit code in the table.

| Command | Purpose | Exit 0 | Exit 1 | Exit 2 | Exit 3 |
|---|---|---|---|---|---|
| `fab.py profile --profile FILE` | validate a profile and its page bindings | valid | invalid record or binding | arguments | not used |
| `fab.py judge --kind K --measured V --threshold T --unit U` | judge one value | pass or finding | fail | arguments | not used |
| `fab.py design --project P --profile FILE [--out DIR]` | ERC, DRC with parity, exports, inventory, drawing sheet | all checks pass | a check fails | unsupported board, missing input, wrong tool identity | KiCad failure |
| `fab.py supplier --project P --profile FILE [--design-dir DIR] [--out DIR] [--manual FILE]` | supplier conditions on a staged copy | every mandatory condition passes | a condition fails, is pending, or the source changed | unsupported mask construct or resource limit | tool failure |
| `fab.py review-source --project P --profile FILE --release ID --observations FILE --reviewer NAME --out FILE` | source review | decision unchanged or harmless | decision material or invalid record | arguments or existing destination | not used |
| `fab.py review-gate --project P --profile FILE --review FILE --expect-sha256 H --release ID` | re-check a review record | intact | any problem | not used | not used |
| `fab.py package --project P --profile FILE --release ID --review FILE --review-sha256 H --dest DIR` | build and publish the package | qualified | unqualified (reasons in the manifest) | existing destination or missing prerequisite | tool failure |
| `fab.py inspect-slots --board-inventory FILE --pth FILE --npth FILE --report FILE` | slot comparison | every slot matches | mismatch | unsupported record | missing input |
| `fab.py inspect-mask --gerber FILE --limit-mil N --report FILE` | mask web measurement | every web passes | fail or uncertain | unsupported construct or limit | tool failure |
| `fab.py drawing-facts` and `fab.py drawing` | fabrication drawing sheet | written | not used | arguments | not used |

## Flow

1. Validate the profile with `profile`.
2. Run `design`. It writes `out/fab/design/`, including the inventory and the drawing sheet.
3. Run `supplier`. It writes `out/fab/supplier/`. Mandatory manual conditions need a manual record (`--manual`) that names the artifact and the current board and silk-layer hashes.
4. Run `review-source`. It writes the review record and the observation copy. Keep the printed review hash.
5. Run `package` with the review hash. The package is built in a staging directory and published only at the end.

## Limits and rules

- Every write stays under `out/fab/` of the project. A symbolic link or an escape is refused.
- Each KiCad command runs in the pinned image with no network. The image identity must match `toolchain.lock.json`. The KiCad version must match the lock.
- A source file that changes during a run is refused. A stale design or supplier result is refused at package time.
- The mask worker has a two-second caller timeout. A timeout returns exit 2 and writes no report. Each run needs a fresh report path. The worker also has a two-second budget of its own, checked at its checkpoints. The caller timeout includes process start and stop time.
- Boundary rules: a `maximum` limit passes at and below the threshold. A `minimum` limit passes at and above it. A `recommendation` never fails. A value inside the error bound of a threshold is `uncertain`, and an uncertain value never passes.
- Measured subset of the drill reader: `METRIC,TZ`, `FMAT,2`, whole micrometre coordinates, three-decimal tool widths, one definition per tool, the `G85` slot record, and a terminal `M30`. Other forms are refused.
- Measured subset of the mask inspector: dark circle and rectangle flashes without a hole, and the measured `RoundRect` macro. Regions, strokes, clear polarity, other macros, holes and overlapping flashes are refused with exit 2.
- The mask error bound (0.000003 mm) is derived from the Gerber coordinate format. It is not measured.
- The fabrication drawing is a generated sheet. The layer PDF from KiCad proves only the export.

## Not implemented

- Process-capability facts are recorded in the profile. They are not supplier rows.
- A manual geometry route for region-producing masks is not implemented. Such a mask stops the supplier step with exit 2.

## Files

- `scripts/fab.py`: command line.
- `scripts/workflow.py`: design, supplier and package.
- `scripts/review.py`: source review and gate.
- `scripts/semantics.py`: export file functions and drill multisets.
- `scripts/inspect_slots.py`, `scripts/export_inspect.py`: slot comparison and drill reader.
- `scripts/inspect_mask.py`, `scripts/macro_defs.py`: mask measurement and the measured macro text.
- `scripts/board_inventory_slots.py`: container worker that reports slots, holes and the outline.
- `scripts/board_inventory.py`, `scripts/validate.py`, `scripts/project_io.py`: byte copies.
- `contracts/`, `runtime/`, `supplier/`: byte copies and the five profile records.
