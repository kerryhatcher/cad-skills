---
name: pcba-design
description: Build the supplier-neutral assembly data of a KiCad project. Map each board reference to a part record, apply the variant population states, group the BOM rows, and evaluate stock against an explicit policy. This skill is independent. It copies its own helpers and contract files.
---

# pcba-design

## Status

The skill covers the neutral step (the part map, the variant rules, the neutral rows, the BOM groups and the stock evaluation) and the Sierra draft command.

The skill writes the neutral data, the Sierra draft set, and the package. It does not qualify a package. Every package is `unqualified` in this batch. Qualification needs open supplier conventions to be confirmed first.

## Command

Run the neutral step from the repository root:

```bash
uv run skills/pcba-design/scripts/pcba.py neutral --project PROJECT --board BOARD.kicad_pcb --variant ID --as-of YYYY-MM-DD
```

- `--project` is the project directory. Every input path is relative to it.
- `--board` is the KiCad board file, relative to the project.
- `--variant` is the variant to build. It must equal the `variant` value in `board.yaml`.
- `--as-of` is the comparison date for stock. The tool never reads the clock.
- `--out` is optional. The default is the neutral JSON file in the `out/pcba` directory.

The command exits with 0 when it writes the data. It exits with 1 for a failure and 2 for incorrect arguments.

A failure has one of two outcomes. A refusal before the write has status `refused`, and nothing is written. A failure after the write has status `failure` with `output_replaced` true. In that case the new output bytes are in place, but a synchronization step failed. Review the output before use. The tool does not roll it back.

## Inputs

| File | Role | Rule |
|---|---|---|
| `board.yaml` | board record | Validated with the copied validator. Set `extensions.pcba.stock.max_age_days`. |
| `board.kicad_pcb` | board | Source of the positions and the source rotations. The numeric fields are derived finite numbers for calculations. Only `source_tokens` keeps the exact source text. |
| `variants.yaml` | variants | The only owner of population states. |
| the parts map file in the `components` directory | parts map | Skill-owned schema `cad-skills/part-map` 1.0. Strict. |
| the part files named by the map | parts | Part records named by the map. Validated with the copied validator. |

## Population states

Each reference in a variant has one state:

- `populate`: placed by the supplier. It needs a part map entry with a part file.
- `dnp`: do not install. It needs a part map entry with a part file.
- `exclude_from_assembly`: absent from the assembly. It needs an explicit map entry. A mechanical item uses `mechanical: true` and no part file.

A `hand_installed` reference must be `populate`. It counts in the neutral BOM and stays out of automatic placement.

## Sierra draft command

Run the Sierra step from the repository root:

```bash
uv run skills/pcba-design/scripts/pcba.py sierra --project PROJECT --board BOARD.kicad_pcb --variant ID --as-of YYYY-MM-DD --out-dir NEW_DIRECTORY
```

- `--out-dir` names a new directory inside the project. An existing directory is refused with `output.exists`. A file is refused with `output.path_invalid`.
- The command captures the board record, the variants, the part map, the parts and the supplier profile once, under the project lock. It derives every value from those captured bytes.
- The supplier profile must match the hash in the board record. Otherwise the command refuses with `supplier.profile_mismatch`.
- A nonempty board restriction refuses with `supplier.restriction_review`. The restriction text is kept in the finding. This is a conservative limit: the tool does not infer export-control status from the text, and an empty restriction list leaves the export applicability `unconfirmed`.
- The command stages the complete set in a temporary directory inside the project. It checks the inputs again, then publishes the directory once. A failure before publication leaves no destination.

Outputs:

- the Sierra BOM workbook, with the header row copied from the retained sample. It is produced only when the supplier profile sets `hand_installed_bom` to `include_in_bom` or `exclude_from_bom`. A missing or unknown value leaves the BOM out and records `not_produced` in the status file.
- the placement draft in mil, with `T` or `B` for the side. Its origin, axes, side view, rotation direction, zero orientation and midpoint mapping are `unconfirmed`.
- a test record. Every limit and every hand-installed step is `not measured`. The record never states a physical pass.
- a status record. It names the service `turnkey_pro`, with the fabrication and assembly locations `unconfirmed`. Its qualification is always `unqualified`.

The Vendor columns of the BOM stay blank. The neutral data does not yet carry supplier part numbers.

## Package command

Run the package step from the repository root:

```bash
uv run skills/pcba-design/scripts/pcba.py package --project PROJECT --board kicad/board.kicad_pcb --variant ID --as-of YYYY-MM-DD --package-id ID
```

- `--board` must name the file `board.kicad_pcb` in the `kicad` directory. The package needs the standard layout that the next section lists.
- `--package-id` names a new package. It matches the release id pattern. An existing package is refused with `package.exists`. Earlier packages are never changed.
- The command takes the project lock. It captures each input once, and it derives every output from the captured bytes.

### Standard layout

The package reads these project files. The paths match the copied validator. Each row names a directory and a file in that directory.

| Directory | File | Role |
|---|---|---|
| project root | `board.yaml` | board record |
| `kicad` | `board.kicad_pcb` | board |
| `kicad` | `board.kicad_sch` | schematic |
| project root | `variants.yaml` | variants |
| `components` | part map and part files | parts |
| `manufacturing` | `supplier.yaml` | supplier profile |
| `manufacturing` | `export.yaml` | export settings |
| `manufacturing` | `supplier-rules.yaml` | supplier rules (skill-owned record) |
| `manufacturing` | `supplier-settings.yaml` | supplier settings (skill-owned record) |
| `evidence` in `manufacturing` | `turnkey-pro-service.txt` | retained supplier evidence (optional) |
| `mechanical` | `board-interface.json` | board interface |
| project root | `toolchain.lock.json` | toolchain lock |

A missing mandatory record refuses the package with `package.input_missing`. A waiver file refuses the package with `package.waivers_unsupported`, because this batch does not apply waivers.

### Toolchain identity

The lock names the local image (`container.image`) and its identity (`container.digest`). The identity is `sha256:` followed by the local image ID. The command reads the local image ID with `podman image inspect`. It never pulls an image.

- A different identity refuses with `toolchain.image_mismatch`.
- A different KiCad version refuses with `toolchain.version_mismatch`.
- The tools run the locked identity, with no network.

### Checks

The package runs 13 checks. Each check has one evidence file.

- `design.erc`: the ERC report has no violation. Each severity counts.
- `design.drc`: the DRC report has no violation and no unconnected item. Warnings count as violations.
- `design.parity`: each schematic pin and each board pad has the same net name.
- `fab.profile_evidence`: the retained evidence bytes match `evidence_sha256` of the profile. Absent evidence gives `pending`.
- `fab.export_inventory`: the written files match the export settings. Missing files and extra files are reported separately.
- `fab.layer_order`: each layer is found by its FileFunction line in the file content. The file name is not used.
- `fab.drill_split`: each drill hole matches the measured board inventory in position, diameter, plating and count. The worker measures all drilled pads and vias.
- `fab.supplier_rules`: the export settings match the supplier rules. An open plane interpretation or an open placement convention gives `unconfirmed`. This check never passes while a convention is open.
- `asm.bom_consistent`, `asm.placement_rotation`, `asm.variant_agreement`, `asm.stock_dated`: the assembly data agrees with the captured parts, variants and board.
- `asm.test_record`: the record identifies the selected variant. It lists each board limit and hand-install instruction. An empty list or duplicate step fails.

Each check states `pass`, `fail`, `pending` or `unconfirmed`. No check is forced to pass.

The Excellon Y axis has the opposite sign to the board Y axis. KiCad writes it that way. The drill check uses this sign.

The drill comparison supports absolute origin, inch units, trailing-zero suppression, four decimal places and separate plated/nonplated files.
The package refuses other settings with `export.drill_setting_unsupported` before it runs an export.

### Validation and publication

The package stages each output in a temporary directory inside the package. Then it runs these steps, in order:

1. It checks the staged bytes and the file count.
2. It runs the copied validator on the project and on the staged package.
3. It compares the inputs with their captured hashes.
4. It compares the manifest and all staged outputs with the validated bytes, byte counts and file count. It refuses links.
5. It publishes the staged directory once.

A change to an input before publication refuses with `input.changed`. A failure before publication leaves no package.

To run the validator on a package:

```bash
uv run skills/pcba-design/scripts/pcba.py check --project PROJECT --package PACKAGE_DIRECTORY
```

The command prints one JSON report. Its exit status is 0 when the validator finds no problem.

### Known limits

- KiCad writes creation times into the Gerber, drill and job files. Two runs give different bytes for these files. Each package records the bytes of its own run through hashes.
- The copied validator binds `board.supplier.profile_sha256` to the profile `content_sha256`. The package and Sierra commands follow this rule. Both commands read `manufacturing/supplier.yaml`. Input bindings retain the full file hash.
- The assembly drawing is an SVG file that the skill generates. It marks the `dnp` and `hand_installed` references of the selected variant. It does not show the KiCad layers.

## Alternates

An alternate is a second part file that the part map lists for one reference. The board record selects it, under the pcba extension `selected_alternates`. The selection takes effect only after an approval exists. The approval file is in the components directory. It binds the reference, the variant, the alternate name, both part hashes and the application evidence. Matching datasheet fields and equal ratings do not approve a substitution. A changed part, a missing approval or a duplicate approval refuses the run.

## Stock policy

Set `extensions.pcba.stock.max_age_days` in `board.yaml`:

- a positive integer, or
- the text `no_age_limit`.

A missing policy refuses the run. The tool never sets a default age limit.

Stock status uses the existing evidence values:

- `pass`: enough stock, a date within the policy, and an active lifecycle.
- `fail`: stock below the demand, a stale date, or an obsolete part.
- `unconfirmed`: unknown stock or an unknown or NRND lifecycle.

## Files

- `scripts/pcba.py`: the neutral step, the Sierra step, the package step and the check command.
- `scripts/package.py`: the package build. It runs the staged validation and the publication.
- `scripts/export.py`: the locked KiCad runs. Each run uses a private copy of the captured bytes.
- `scripts/board_inventory_worker.py`: all drilled pad and via measurements in the locked image. The worker refuses unsupported holes.
- `scripts/checks_design.py`, `scripts/checks_fab.py`, `scripts/checks_asm.py`: the check rules.
- `scripts/drawing.py`: the SVG assembly drawing of the selected variant.
- `scripts/report.py`: the evidence and manifest records.
- `scripts/project_io.py`, `scripts/sexp.py`: copied from `pcb-design`. Listed in `COPY_SHA256.txt`.
- `contracts/`: copied validator, registry, and record schemas. The part map schema is skill-owned.
- `COPY_SHA256.txt`: source hashes of every copied file.

## Tests

```bash
uv run tests/test_pcba_design.py
```

The neutral and Sierra tests copy the fixture project in the `tests/fixtures/pcba-design/project` directory to a temporary directory. The package tests copy the standard-layout fixture in the `standard-project` directory of the same fixture set. Each test edits the copy and checks one rule.

The `retained` directory of the same fixture set holds one package run, in the `pkg-standard` directory, and its full validator result, in the file `validator-result.json`.
