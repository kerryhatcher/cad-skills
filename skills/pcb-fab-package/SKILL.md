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
| `fetch_sources.py --manifest FILE [--dest DIR] [--entry ID ...] [--check-only]` | retrieve the source pages named by the manifest. Writes only when the hash matches and the magic check passes | each fetched entry matches, or each entry is skipped | a candidate, changed or magic mismatch | manifest, argument, link or binding defect | fetch or write failure |
| `make_rules.py [--profiles DIR] [--out DIR] [--check]` | make or compare the rule files | files agree, or written | a file is different or missing, or a rule file has no profile | incorrect profile, argument or symbolic link | file or schema error |
| `fab.py drawing-facts` and `fab.py drawing` | fabrication drawing sheet | written | not used | arguments, or a link at `--out` | not used |
| `recheck_sources.py --manifest FILE [--entry ID ...] [--format F] [--allow-ci]` | release re-check of the live pages. Writes no file and changes no profile | each fetched page has its recorded hash | a candidate, changed or magic mismatch | arguments, manifest or watch problem, or CI | fetch failure |

## Source setup

Public source excludes the full supplier pages and response headers.
The profiles retain the source URLs and expected hashes.
Before the first profile command, retrieve the pages with the skill's manifest:

```sh
uv run scripts/fetch_sources.py --manifest sources.yaml
```

Run this command from the skill directory. The command contacts the source URLs.
It writes only bytes that match the recorded hash and format.
If the source changes, record a new source review before you change a profile.
The local tests use project-authored fixtures. They do not retrieve supplier pages.

## Release re-check

Before a release, compare the live supplier pages with the manifest:

```sh
uv run scripts/recheck_sources.py --manifest sources.yaml
```

The command runs `fetch_sources.py` in check-only mode. The command writes no file and does not change a profile.
The command prints a report with the status of each page and the watch items.
If a page changed, record a new source review before you change a profile.
The command is a release step. It does not run when the shell sets the `CI` variable.
The repository release checklist gives the full procedure.

## Flow

1. Validate the profile with `profile`.
2. Run `design`. It writes `out/fab/design/`, including the inventory and the drawing sheet.
3. Run `supplier`. It writes `out/fab/supplier/`. Mandatory manual conditions need a manual record (`--manual`) that names the artifact and the current board and silk-layer hashes.
4. Run `review-source`. It writes the review record and the observation copy. Keep the printed review hash.
5. Run `package` with the review hash. The package is built in a staging directory and published only at the end.

## Rule files for KiCad DRC

The skill supplies one KiCad rule file for each supplier profile. The files are in `supplier/rules/`.
The file name is the profile id, for example `supplier/rules/oshpark-two-layer.kicad_dru`.
Use a rule file to run KiCad DRC without the workflow.
Copy the file next to the board as `<project-name>.kicad_dru`, with the project name of the board. Then run DRC in KiCad.
If the board has a rule file, put only the rule lines into that file.

The workflow does not read these files. The `supplier` command makes its rules from the profile when it runs.
`scripts/make_rules.py` makes the files with the same function. Thus the two rule texts are equal.
The files contain only the limits that KiCad checks (`division.kicad_dru` of the profile).
For the other supplier conditions, use the `supplier` command.

After you make a change to a profile, run the generator from the skill directory:

```sh
uv run scripts/make_rules.py
uv run scripts/make_rules.py --check
```

## Limits and rules

- Every write of `design`, `supplier`, `review-source` and `package` stays under `out/fab/` of the project. A symbolic link or an escape is refused.
- The standalone `drawing-facts` and `drawing` commands have no project argument. Their output root is the parent directory of `--out`. They refuse a link at `--out`, including a dangling link. They claim no project confinement.
- Each KiCad command runs in the pinned image with no network. The image identity must match `toolchain.lock.json`. The KiCad version must match the lock.
- A source file that changes during a run is refused. A stale design or supplier result is refused at package time.
- The mask worker has a two-second caller timeout. A timeout returns exit 2 and writes no report. Each run needs a fresh report path. The worker also has a two-second budget of its own, checked at its checkpoints. The caller timeout includes process start and stop time.
- Boundary rules: a `maximum` limit passes at and below the threshold. A `minimum` limit passes at and above it. A `recommendation` never fails. A value inside the error bound of a threshold is `uncertain`, and an uncertain value never passes.
- Measured subset of the drill reader: `METRIC,TZ`, `FMAT,2`, whole micrometre coordinates, three-decimal tool widths, one definition per tool, the `G85` slot record, and a terminal `M30`. Other forms are refused.
- Measured subset of the mask inspector: dark circle and rectangle flashes without a hole, and the measured `RoundRect` macro. Regions, strokes, clear polarity, other macros, holes and overlapping flashes are refused with exit 2.
- The mask error bound (0.000003 mm) is derived from the Gerber coordinate format. It is not measured.
- The fabrication drawing is a generated sheet. The layer PDF from KiCad proves only the export.
- The board dimensions use the Edge.Cuts centerlines. The inventory excludes the drawing stroke width and includes footprint graphics.

## Via construction

The supplier command measures via spans from the captured board in the locked image.
It compares them with `service.via_construction_prohibited` in the profile.
A prohibited blind or buried span gives exit 1 before the design inventory prerequisite.
The result names the failed precondition. It is not a complete supplier result and cannot qualify a package.

Declare the requested process in `board.yaml`:

```yaml
extensions:
  fabrication:
    via_process: standard_through
```

The other supported values are `filled_plated_via_in_pad` and `unconfirmed`.
The declaration describes the requested process. It does not prove physical construction.
A prohibited declaration fails with exit 1. A missing or unconfirmed declaration with measured vias remains pending.
An unknown value gives exit 2. A board with no vias records the measured zero count.
The B6 inventory worker remains unchanged.

## Corner tool compatibility

The profile records published cutter diameters under `process.outline_cutter_diameter` and `process.cutout_cutter_diameter`.
Each fact retains its inch value, source URL and source hash.
The supplier command derives the circular tool radius as half that diameter.
It compares this radius with measured concave outline corners and cutout corners.
The result is derived tool compatibility. It is not a quoted supplier minimum or a general manufacturing guarantee.
Convex outer corners do not use this comparison.

The worker supports closed contours made from segments, rectangles, circles and quarter-circle arcs.
It refuses other shapes, open or branching contours, nested cutouts and intersecting contours.
The topology polygon has a circular chord bound of one micrometer.
Separate contours must have more than 0.01 mm between their topology boundaries.
The radius comparison uses the pcbnew integer nanometer radius, not the topology polygon.

## Not implemented

- Process-capability facts other than the declared comparisons remain informational.
- A manual geometry route for region-producing masks is not implemented. Such a mask stops the supplier step with exit 2.

## Files

- `references/oshpark-kicad-setup.md`: project-authored KiCad setup for the OSH Park Gerber route. It separates checked values, recommendations, margins and manual steps.
- `scripts/fetch_sources.py`: source retrieval for the manifest. It checks every entry before the first fetch, confines the profile and destination paths, and never writes a profile or a changed source.
- `scripts/recheck_sources.py`: release re-check. It runs `fetch_sources.py` in check-only mode and prints a report.
- `scripts/make_rules.py`: generator for `supplier/rules/*.kicad_dru`. The generator uses the rule function of `workflow.py`.
- `scripts/fab.py`: command line.
- `scripts/workflow.py`: design, supplier and package.
- `scripts/review.py`: source review and gate.
- `scripts/semantics.py`: export file functions and drill multisets.
- `scripts/inspect_slots.py`, `scripts/export_inspect.py`: slot comparison and drill reader.
- `scripts/inspect_mask.py`, `scripts/macro_defs.py`: mask measurement and the measured macro text.
- `scripts/board_inventory_slots.py`: container worker that reports slots, holes and the outline.
- `scripts/via_inventory.py`: container worker that measures via spans without a board change.
- `scripts/corner_inventory.py`: container worker that measures supported corner geometry.
- `scripts/board_inventory.py`, `scripts/validate.py`, `scripts/project_io.py`: byte copies.
- `contracts/`, `runtime/`, `supplier/`: byte copies, the five profile records and the five generated rule files.
