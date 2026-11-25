# Mechanical fit

This reference describes the mechanical fit flow for the fixture `mech-fit-a`. It states only what the commands implement. The measured end-to-end evidence is kept with the batch review record in the repository, not in this skill.

## Commands

Run from `skills/pcb-design`. Each command takes the fixture directory as `--project`.

```bash
uv run templates/mech-fit-a/make_fixture.py --out DIR      # generate the fixture
uv run scripts/mechanical.py check --fixture DIR           # contract rules only
uv run scripts/mechanical.py export --project DIR          # STEP, DXF and separate drill files
uv run scripts/mechanical.py fit --project DIR             # comparisons C01 to C12
uv run scripts/mechanical.py release --project DIR         # publish mech-release/1
uv run scripts/pcb.py mechanical {check|readiness|fit|release} DIR            # thin dispatch
uv run scripts/pcb.py mechanical export DIR [--image REF]                     # thin dispatch, optional image
```

`pcb.py mechanical` only dispatches to `mechanical.py` through `uv run`, so the CadQuery header of the module applies. The fixture path is positional. `--image` is optional and applies to `export` only.

Exit status: 0 pass, 1 failed comparison, incomplete or inconsistent report, stale input, altered output, lock or path refusal, 2 invocation, unsupported frame, transform, settings, drill class or image, 3 tool or integrity failure after publication started.

## Flow

1. `export` reads each captured input once as bytes. Before the first publication write it compares every consumed input with its captured hash, and a source change publishes nothing. It checks the contract on those bytes. It pins the local image ID from `export-settings.json` and refuses a different ID. It runs the three KiCad exports in a private staging folder, and checks each staged file before it is published with an atomic write. It writes an export record beside the outputs, with the input hashes, the exit codes, the image ID and each output's role, path, SHA-256 and byte count.
2. `fit` reads the captured inputs once. It runs the contract check. It confines and validates the export record: exactly four outputs, fixed relative paths, accepted roles. It refuses a changed input (`stale.input`) or a changed output (`export.altered`). It runs every comparison on the bytes. It recomputes completeness and status. Before it writes, it checks the live inputs and outputs again. It writes a report and the fit assembly beside the export.
3. `release` reads the report. It recomputes the status from the results and refuses a report that is not a complete pass. It compares the recorded expected values with the live values in the accepted order and names the first mismatch, before any generic stale check. It checks every bound output's bytes and byte count, including the report and the fit assembly, requires all six roles, and runs a final freshness and integrity check. It writes the `mech-release/1` record with the explicit fields, the output byte counts and a canonical record hash.

Every write holds the project lock. Every record path is confined to the project before access.

## Comparisons

Expected values come from the source record through the accepted transform. They never come from the files under test. Each result carries its ID and, where it applies, its reference.

| ID | Measures | Reference |
|---|---|---|
| C01 | DXF outline vertices, order-independent | none |
| C02 | STEP cylinder axes against the complete declared hole set | none |
| C02d | DXF hole circle centres against the complete declared hole set | none |
| C03 | Diameter from each DXF circle and each STEP cylinder against the complete set | none |
| C04 | PTH file holds the plated holes, NPTH file holds the non-plated holes | none |
| C05 | Imported substrate solid against `core_mm` and datum `z = 0` | none |
| C06 | Connector mating face centre and angle against the interface frame | each connector |
| C07 | Insertion box against every other solid, boolean volume with zero tolerance; the own proxy is excluded | each connector |
| C08 | Proxy heights from the finished-board mounting surfaces against `top_mm` and `bottom_mm` | each part and connector |
| C09 | Proxy corners inside or on the outward cavity | each part and connector |
| C10 | Evidence statuses; `unconfirmed` gives `unconfirmed` | none |
| C11 | Owner declarations; a conflict names the dimension | none |
| C12 | Auxiliary origin from the board file against the anchor | none |
| closed set | Measured centres equal the complete set, for STEP, DXF, PTH and NPTH | output name |

The complete declared hole set is the interface `holes` plus the validated `excluded_through_holes`. Each excluded hole needs an id, a finite position, a positive diameter, a plated flag and a nonblank reason. Any other form refuses by name.

Tolerances are fixed: 0.01 mm for geometry, 0.1° for angles, 1e-6 mm³ for the insertion box volume.

A required result that is missing, duplicated, inconsistent with its tolerance, or has an unknown status makes the report fail. An empty result set fails. A missing required reference is named.

## Cavity and connector body

The cavity is the board outline offset outward by `clearance_mm`, with the chamfer included. The outline must be convex. A corner is inside when it lies inside that polygon or on its boundary, within 0.01 mm. There is no mating-edge exemption.

A connector body is declared separately. Its `body_length_mm` is project-authored for this test proxy, and it is not derived from `insertion_depth_mm`. The body lies inward from its mating face, opposite the transformed insertion vector, with zero overhang. This proxy makes no datasheet claim and no detailed component-fit claim.

## Drill files

`--excellon-separate-th` writes `board-PTH.drl` (role `drill_pth`) and `board-NPTH.drl` (role `drill_npth`). Each file must hold only its plating class. A tool whose plating does not match its file refuses.

Refused by name: a slot or oval (routed `G85` records, and an arc in the DXF), any other unknown Excellon record, a hit with no tool, and a tool without a plating comment.

## Stackup

`thickness_mm` is the total stack. The substrate is `core_mm`. C05 compares the imported substrate solid with `core_mm`. Global STEP points are not used. The layer sum is checked against `thickness_mm` (C05s) on every contract check.

## Frame and transform

- `x_target = origin.x + x − anchor.x`, `y_target = origin.y + anchor.y − y`. Scale 1.
- The anchor is `aux_axis_origin` in the board file, and it must equal `source_origin_mm`.
- Target vector: `target = R(θ) · F · local`, with `F = diag(1, −1)` and `R(θ) = [[cos θ, −sin θ], [sin θ, cos θ]]`. Combined: `[[cos θ, sin θ], [sin θ, −cos θ]]`. The target angle is the angle of that vector. It equals `θ` only for a local vector along local +x.

## Connector agreement

The connector side and insertion depth must agree across the interface frame, the source record and the evidence. A mismatch refuses by name, with the connector and the field.

## Contract refusals (every command)

- The `extensions.transform` block is missing or altered: exit 2.
- A `B.Cu` footprint has no `pad_frame`, or a frame other than `placed-file`: refused.
- A source part or connector frame has no evidence record: refused by reference.
- A test-only variant may not release.
- The export settings lack a required switch, including `--excellon-separate-th`: exit 2.

## What the check does not prove

- A proxy proves a conservative envelope only. It does not prove detailed component fit.
- A board-only STEP proves board geometry only.
- A footprint stored with `pad_frame` `placed-file` is accepted as declared. The file has no edit history, so an editor flip is not detected.
