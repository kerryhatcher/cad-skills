# B7/B8 proposal, revision 8: consolidated `pcb-fab-package` interface (claude-skill-dev)

Date: 2026-11-14. Status: consolidated paper for review. It replaces revisions 4 to 7 (`b7-b8-proposal-claude-r4.md`, `b7-b8-proposal-claude-r5.md`, `b7-b8-proposal-claude-r6.md`, `b7-b8-proposal-claude-r7.md`) and the addendum (`b7-b8-r4-addendum-claude.md`). Those files stay as history. Revision 7 is kept unchanged. No B7 implementation before explicit reviewer agreement. B6 is accepted and stays unchanged (`b6-acceptance-root.md`).

Measured basis: `b7-prereq-trials-claude.md`, `b7-mask-boundary-trials-claude.md` and the frozen evidence in `b7-trial-evidence-r8/` (manifest `b7-prereq-evidence-r8.sha256`). Reviews consolidated: `b7-b8-design-pi.md` (section 16), `b7-b8-design-codex.md` (revision 7), and the earlier reviewer sections.

## 1. Scope and standalone files

`skills/pcb-fab-package/` is independent of `skills/pcb-design/`. It has no runtime reference outside its own directory. B6 keeps circular drills only.

| Path | Origin |
|---|---|
| `scripts/fab.py` | new CLI (section 3) |
| `scripts/export_inspect.py` | owned derivative. The B6 export checks are extracted from `skills/pcb-design/scripts/pcb.py` (functions `check_export_outputs`, `excellon`, `export_subset`, `placement_filter`) and adapted. It is not a byte copy of a separate file. |
| `scripts/inspect_slots.py` | new (section 5) |
| `scripts/inspect_mask.py` | new (section 6). It contains the exact `RoundRect` analyzer and the refusal rules. |
| `scripts/board_inventory.py` | byte copy of the B6 worker `skills/pcb-design/scripts/board_inventory.py` |
| `scripts/board_inventory_slots.py` | owned derivative of the worker. Slot and oval drills are reported with minor and major dimensions and their pad attribute, instead of being refused. B6 keeps its worker. |
| `scripts/validate.py`, `scripts/project_io.py` | byte copies of `contracts/validate.py` and `contracts/project_io.py`, verified by the package test |
| `contracts/schemas/*.json`, `contracts/registry.json`, `contracts/README.md` | byte copies of `contracts/` |
| `runtime/Containerfile`, `runtime/BUILD.md` | byte copies of the B6 runtime recipe |
| `supplier/profiles/*.yaml` | five profile records (section 4) |
| `supplier/pages/*`, `supplier/rules/*.kicad_dru.in` | byte copies of the retained pages; rule templates |
| `SKILL.md`, `references/*.md` | new |

## 2. Contract changes (narrow, authorized under review)

1. `contracts/validate.py`: `fab.supplier_rules` is added to `BARE_CHECKS`. `PCBA_CHECKS` inherits it. `INPUT_ROLES` gains `supplier_rules` and `supplier_settings`. `CHECK_INPUT_ROLES["fab.supplier_rules"] = ("board", "supplier_profile", "export_settings", "supplier_rules", "supplier_settings", "toolchain")`.
2. `contracts/schemas/manifest.schema.json`: the inputs role enum gains `supplier_rules` and `supplier_settings`. The outputs enum does not change.
3. Evidence schema: no change. Manual geometry results use the existing `evidence` and `report` roles (section 14).
4. Test builders: `tests/pcb_support.py` and the expectations in `tests/test_pcb_tools.py` gain the check. A test shows that a package without `fab.supplier_rules` is unqualified, not a pass.
5. Every bundled copy is updated and tested. `skills/pcb-design/scripts/validate.py` and `skills/pcb-design/contracts/*` change with `contracts/`. The B6 replacement manifest is named for acceptance before the copy lands.

## 3. CLI and exit codes (one table for every command)

Exit codes, for every command in this interface:

| Exit | Meaning |
|---|---|
| 0 | success: valid, passed, qualified, or recorded |
| 1 | invalid record or extension, unknown key, path escape, violation, failed check, unqualified package, stale or missing evidence, changed reviewed bytes, or an unmet mandatory condition |
| 2 | invalid arguments (for example a missing flag), missing prerequisite, unsupported operation or construct, runtime or image mismatch, existing destination |
| 3 | tool failure (KiCad, the worker or the container failed or produced no output) |

Precedence: 3, 2, 1, 0. An invalid record is always exit 1. A path that leaves its root is an invalid record, so it is exit 1.

| Command | Inputs | Writes (under `out/fab/` only) | Exits |
|---|---|---|---|
| `fab.py profile --profile FILE` | profile record, its pages | none; prints findings | 0 valid; 1 invalid record, extension or division; 2 missing page or arguments |
| `fab.py design --project P` | board, schematic, `.kicad_pro`, `.kicad_dru`, export contract, lock | `reports/design/*` (ERC, DRC with parity, export set), each with binding and result | 0 pass; 1 check failure; 2 unsupported construct or prerequisite; 3 tool failure |
| `fab.py supplier --project P --profile FILE` | design inputs and the profile | staged copy (disposable) and `supplier/` with the effective `board.kicad_dru`, the effective `board.kicad_pro`, `supplier-settings.json`, the raw DRC report, the slot and mask inspections, `supplier-result.json`, binding and result | 0 pass; 1 invalid profile, unmet condition, violation, or source changed during the run; 2 unsupported selector or construct, missing prerequisite, runtime mismatch; 3 KiCad failure |
| `fab.py inspect-slots --project P --profile FILE` | board, drill outputs, profile | `reports/slots.json` | 0 pass; 1 mismatch; 2 unsupported; 3 tool failure |
| `fab.py inspect-mask --project P --profile FILE` | mask Gerbers, profile | `reports/mask.json` | 0 pass; 1 violation or uncertain result; 2 unsupported construct; 3 tool failure |
| `fab.py review-source --project P --profile FILE --release ID --observations FILE --reviewer NAME` | release ID, profile, stored pages, observation JSON | `source-review/REVIEW.json` | 0 recorded with decision `unchanged` or `harmless`; 1 decision `material`, a missing observation, an unknown key or a path escape; 2 invalid arguments (missing flag or unknown option) |
| `fab.py package --project P --profile FILE --release ID --dest out/fab/packages/NAME` | results of `design`, `supplier`, the source review | new package directory, published with `project_io.publish_dir` | 0 qualified; 1 unqualified (reason in the manifest); 2 existing destination or missing input; 3 tool failure |

Path policy: every file is written under `out/fab/` of the project. Packages are published only with `project_io.publish_dir`.

## 4. Profiles: limit kinds, scopes and source values

Kinds and scopes follow the accepted schema: `kind` is `minimum`, `maximum`, `recommendation` or `unconfirmed`. `scope` is `fabrication`, `assembly` or `margin`. `value_kind` is `number` or `text`. A text value has no unit. A number has a unit.

Boundary rules (these are the only ones):
- A `maximum` limit passes at and below the threshold and fails above it.
- A `minimum` limit fails below the threshold and passes at and above it.
- A `recommendation` never fails the package. It is reported as a finding.
- A limit with a measured error bound (section 6) is `uncertain` inside the bound. It is never a pass at the threshold.

### 4.1 Design limits (`limits`)

Source values are the stored page values. The metric label is a display value, computed as 25.4 µm per mil and rounded for display only. It is not a design value. The profile stores the source value in its source unit.

| Key | Kind (scope) | Single-layer | Two-layer | Two-layer HHDC | Four-layer | Six-layer | Source statement |
|---|---|---|---|---|---|---|---|
| `min_trace` | minimum (fab) | 6 mil (0.152 mm) | 6 mil (0.152 mm) | 6 mil (0.152 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | "Trace Width" |
| `min_space` | minimum (fab) | 6 mil (0.152 mm) | 6 mil (0.152 mm) | 6 mil (0.152 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | "Trace Spacing" |
| `min_annular_ring` | minimum (fab) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | 4 mil (0.102 mm) | 4 mil (0.102 mm) | "Minimum Annular Ring" |
| `min_drill` | minimum (fab) | 10 mil (0.254 mm) | 10 mil (0.254 mm) | 10 mil (0.254 mm) | 10 mil (0.254 mm) | 8 mil (0.203 mm) | "Minimum Drill Size" |
| `min_slot_size` | minimum (fab), minor dimension of a drilled slot | 20 mil (0.508 mm) | 20 mil (0.508 mm) | 20 mil (0.508 mm) | 20 mil (0.508 mm) | 20 mil (0.508 mm) | "Minimum Slot Size 20mil (drill slot only)" |
| `plated_drill_to_internal_copper` | minimum (fab), four and six layers only | not applicable | not applicable | not applicable | 10 mil (0.254 mm) | 10 mil (0.254 mm) | "Plated Drill to Internal Layer Copper Clearance" |
| `edge_keepout` | minimum (fab) | 15 mil (0.381 mm) | 15 mil (0.381 mm) | 15 mil (0.381 mm) | 15 mil (0.381 mm) | 15 mil (0.381 mm) | "Board Edge Keepout 15mil from nominal board edge" |
| `mask_web_min` | minimum (fab), geometric (section 6) | 4 mil (0.102 mm) | 4 mil (0.102 mm) | 4 mil (0.102 mm) | 4 mil (0.102 mm) | 4 mil (0.102 mm) | "Minimum soldermask web 4 mil" |
| `silk_line_min_short_text` | minimum (fab) | 3 mil (0.076 mm) | 3 mil (0.076 mm) | 3 mil (0.076 mm) | 3 mil (0.076 mm) | 3 mil (0.076 mm) | "3 mil (short lines, text, graphics)" |
| `silk_line_recommended` | recommendation (fab) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | "5 mil (recommended minimum)" |
| `overlapping_drill_clearance` | recommendation (fab) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | 5 mil (0.127 mm) | "5 mil clearance is recommended between holes" |
| `board_min_edge` | minimum (fab) | 6.35 mm | 6.35 mm | 6.35 mm | 6.35 mm | 6.35 mm | "Minimum board size 0.25in (6.35mm)" |
| `board_max_width` | maximum (fab) | 406.4 mm | 406.4 mm | 406.4 mm | 406.4 mm | 406.4 mm | "Maximum board size 16in (406.4mm) by 22in (558.8mm)" |
| `board_max_height` | maximum (fab) | 558.8 mm | 558.8 mm | 558.8 mm | 558.8 mm | 558.8 mm | same source line |

Board width and height are separate maxima. Each axis is tested at its own below, at and above values (section 10).

### 4.2 Extensions (`extensions`)

Extensions are service facts and process capability, validated by `fab.py profile` with named fields. The schema `extensions` is an untyped object. Published process capability is not a design margin. It is recorded as manual evidence with its published value and unit.

| Field | Kind | Single | Two | Two HHDC | Four | Six | Source statement |
|---|---|---|---|---|---|---|---|
| `service.layers` | requirement | single | two | two | four | six | Stackup |
| `service.copper` | text | 1 oz | 1 oz | 2 oz | 1 oz outer, 1/2 oz inner | 1 oz outer, 1/2 oz inner | Copper Weight |
| `service.substrate` | text | two-layer | 175Tg FR4 (Kingboard KB6167F) | 180 Tg FR4 Ventec VT-47, "4x 7628 Ventec VT-47", "28 mil (0.711mm) core" | 190Tg FR408-HR | published stackup | Material Specs |
| `service.finished_thickness_nominal_mm` | number, mm | 1.6 | 1.6 | 0.8 | 1.6 | 1.6 | "Board Thickness 63mil (1.6mm) nominal"; HHDC "32mil (0.8mm) nominal" |
| `service.via_construction_prohibited` | requirement list | blind, buried, filled and plated via-in-pad | same | same | same | same | "Blind Via No"; "Via Tenting Yes (filled hole and flat surface not guaranteed)" |
| `service.order_multiple` | requirement, text | multiples of three | same | same | same | same | "in multiples of three" |
| `process.mask_alignment_max_mil` | margin, process | 3 mil | 3 mil | 3 mil | 3 mil | 3 mil | "Maximum soldermask alignment 3mil" |
| `process.drill_size_tolerance_max_mil` | margin, process | 2.5 mil | 2.5 mil | 2.5 mil | 2.5 mil | 2.5 mil | "Drill Size tolerance Max: +/- 2.5mil" |
| `process.drill_size_tolerance_typical_mil` | margin, process | 1.0 mil | 1.0 mil | 1.0 mil | 1.0 mil | 1.0 mil | "Typical: +/- 1.0mil" |
| `process.drill_position_tolerance_max_mil` | margin, process | 2 mil | 2 mil | 2 mil | 2 mil | 2 mil | "Drill Positional Tolerance Max: 2mil" |
| `process.drill_position_tolerance_typical` | margin, process, text | less than 1 mil | same | same | same | same | "Typical: <1mil" |
| `notes.max_drill` | note, text | no maximum | same | same | same | same | "Maximum Drill Size None; above 250mil larger milling tolerances". A note only. No maximum limit exists. |

The single-layer profile uses the two-layer limits. Its `evidence` binds two pages: the single-layer page (the process statement that the service is a two-layer process with identical specifications) and the two-layer page (the value source). The two-layer example file `b7-b8-two-layer-profile-example.yaml` is schema-valid but semantically superseded by this table. It is kept as history.

Slot width: the profile records `min_slot_size` = 20 mil with `interpretation: minor dimension of a drilled slot`. No slot length minimum exists in the source.

## 5. Slot export inspection

Measured basis: the exported non-plated drill file has one `G85` record per slot (`X..Y..G85X..Y..`), with the tool record `T..C<width>` for the minor dimension. Coordinates are 3:3 mm, with 0.001 mm increments (`prereq` trials, section 3).

Method:
1. From the saved board (`board_inventory_slots.py`, container), list each slot with its endpoints (centres of the end arcs), its minor dimension, and its expected plated class. The expected class comes from the board attribute: a pad with type `thru_hole` is PTH, a pad with type `np_thru_hole` is NPTH, and a via is PTH. The class is never read from the export file.
2. From the exported drill file for each class, parse each `G85` record into an unordered endpoint pair, and read the minor dimension from the `T` record of that slot.
3. Compare the board and export as multisets, per plated class: each board slot is matched once, and each exported record is matched once. Endpoint pairs are compared as unordered pairs.
4. Tolerance: the board value is exact in nanometres. The export rounds each coordinate to 0.001 mm, so the rounding error is at most 0.0005 mm per coordinate (derived from the measured increment). Two endpoints of the same pair match when each coordinate differs by no more than 0.0005 mm plus 0.000001 mm of floating-point margin.
5. Orientation: the angle from the endpoints is compared with the board rotation. For a near-circular slot (major minus minor below 0.001 mm) the orientation is not compared, and the record is reported as `near_circular`.
6. A board slot with no export record, an export record with no board slot, a difference in multiplicity, a plated class mismatch (the slot is in the wrong file), or a duplicate is a mismatch (exit 1).

Acceptance: minor width 19.9, 20 and 20.1 mil (fail, pass, pass); endpoint pairs in reversed order match; an endpoint difference of 0.0004 mm matches, and 0.002 mm is a mismatch (both derived bounds, not measured); a duplicate slot needs two export records; a slot in the wrong plated file is a mismatch; a board PTH slot exported only in the NPTH file is a mismatch (class swap); a 45-degree slot matches the measured rotated record.

## 6. Mask geometry inspection

The saved mask-web setting is a parameter. It does not establish the exported geometry. The mask is measured from the exported Gerber.

### 6.1 Measured basis

Measured in `b7-mask-boundary-trials-claude.md`, with exit codes and full hashes:
- Circle pads at 3.9, 4.0 and 4.1 mil webs export as two separate circle flashes. Measured webs: 3.9000, 4.0000 and 4.1000 mil, within 1 nm of the nominal gap.
- Round-rect pads export as `RoundRect` macro flashes. The exact analyzer on the real round-rect fixture (`geom-trial/analyze.py`) gives 4.0000 mil. This is a nominal success, separate from the circle-only measurement script, which refuses macros.
- An oval pad exports as an obround aperture (not a macro). The analyzer refuses it. Exit 2.
- Two overlapping pads (centres 0.5 mm apart, diameter 0.6 mm) give an exact gap of -0.1 mm. The current analyzer prints this value and does not refuse it. The implementation must refuse it (`overlapping_cluster`, exit 2). This is a required test, not a passed behavior.
- A 4 mil minimum web setting on the 3.9 mil fixture did not merge the openings. KiCad wrote two 25-point polygon regions, shrank each opening from radius 0.300 mm to 0.297433 mm, and the web rose to 4.1 mil. The exported geometry decides the result.

### 6.2 Automatic subset

- Flashes (`D03`) of circle (`C`) and rectangle (`R`) apertures, and of the `RoundRect` macro, with dark polarity only.
- Anything else is `unsupported` with the object named (exit 2): regions (`G36`/`G37`), strokes (`D01`), other macros, clear polarity (`%LP C`), other aperture types. The 4 mil minimum web setting output (regions) is in this group. It is not covered by the automatic method.
- Explicit manual evidence is the only route for a region-producing result (section 14). The circle algorithm does not cover it.

### 6.3 Exact method

Exact distance between two flashed shapes, from the parameters, with no polygon conversion. A circle's core is its centre. A rectangle's core is its box. A `RoundRect` flash is its core rectangle (the box through its corner centres) Minkowski-summed with a disk of radius `r`. The distance between two flashes is max(0, d_core - r1 - r2), where d_core is the distance between the core boxes.

### 6.4 Error bound and decision

Error bound (derived, not measured): Gerber coordinates have six decimals in millimetres, so each coordinate is exact to 0.000001 mm. A distance uses at most two coordinate roundings and one floating-point operation. The bound is 0.000002 mm plus 0.000001 mm of floating-point margin, so 0.000003 mm in total. This bound applies to the exact method only.

Decision rule (no tolerance band becomes a pass; a result at the limit is never a pass):
- A web is `pass` only when its exact minimum distance is at least the limit plus the error bound.
- A web is `fail` when the distance is below the limit by more than the error bound.
- A web within the error bound of the limit is `uncertain`. An uncertain web is never a pass and blocks qualification.

Measured results with this rule (limit 4.0 mil):

| Fixture | Measured web | Result |
|---|---|---|
| 3.9 mil circles | 3.9000 mil | fail |
| 4.0 mil circles | 4.0000 mil | uncertain (at the limit) |
| 4.1 mil circles | 4.1000 mil | pass |
| Round-rect pads, 4.0 mil nominal | 4.0000 mil | uncertain (at the limit) |

### 6.5 Refusals and merged openings

- Two flashes with no mask between them after export form one opening. This is reported as `merged_opening` with the object pair. It is not a web failure and not a manufacturing failure.
- Overlapping flashes (negative exact gap) form an overlapping cluster. Exit 2 with `overlapping_cluster`. No web value is reported for the cluster.
- Narrow mask channels inside a merged opening are not measured. The automatic method refuses a merged region (regions are unsupported).

### 6.6 Resource bounds

Flashes are checked only against neighbours whose core boxes lie within the limit plus twice the largest radius. Limits: at most 10000 flashes per layer, at most 5 MB of Gerber input, at most 2 seconds of run time, and memory linear in the flash count. Exceeding any limit gives exit 2 with the reason. No raster is used.

## 7. Supplier rules, staging and effective files

### 7.1 Measured rule facts

- Basename: the staged project is named `board`. KiCad reads custom rules from `board.kicad_dru`, next to `board.kicad_pro`. A file with another basename gives no violations (trial rule cases A and B).
- Severity: `board.design_settings.rule_severities.<rule>` in `board.kicad_pro`. `ignore` removes the violations (case C). The supplier severity is `error`.
- Exclusion format (KiCad 10.0.5, measured): `board.design_settings.drc_exclusions = [["track_width|<x_nm>|<y_nm>|<mainUUID>|<auxUUID>", "<comment>"]]`. The marker is the straight track midpoint in nanometres, taken from the segment with the S-expression parser. The auxiliary UUID is the nil UUID. Exactly the targeted violation is excluded. Earlier candidate forms with the comment inside the string were invalid and are kept as evidence.

### 7.2 Staged exclusion restoration (measured)

Command: `uv run stage_proof.py <excl directory>`, with the B6 image through `podman run --rm --pull=never --network none`, `kicad-cli pcb drc --severity-all --format json`. Full hashes are in `b7-mask-boundary-trials-claude.md` and the manifest.

| Copy | Exclusion entry | track_width active | track_width excluded | Rule file hash |
|---|---|---|---|---|
| source | kept | 7 | 1 | `c3e649bd…6904` (unchanged) |
| staged | cleared by the mandatory supplier check | 8 | 0 | `c3e649bd…6904` (unchanged) |

Result: the source keeps its entry. The staged copy clears it and reports all eight active violations. The supplier rule still applies in both copies. Mandatory supplier checks clear source exclusions in staging. A source exclusion never hides a supplier violation in the supplier result.

### 7.3 Staging rules

- Generated rules are placed after the source rules. KiCad examines later rules first.
- The package records the hash of the effective staged `board.kicad_dru` and `board.kicad_pro`.
- Source PCB, source `.kicad_dru` and source `.kicad_pro` are hashed before and after the run. A change is exit 1.

### 7.4 Referenced output hashes

- The supplier role table is mandatory: `fab.supplier_rules` requires `supplier_rules` and `supplier_settings`.
- The inputs `supplier_rules` and `supplier_settings` must be the effective staged files. Their hashes must match the effective `board.kicad_dru` and `board.kicad_pro` hashes recorded in section 7.3.
- `validate.py` checks the manifest input paths and hashes.
- `fab.py` checks the referenced output hash. A reference that does not match the manifest output is exit 1.

## 8. Source review and supplier result

### 8.1 Source review record

Source review (`REVIEW.json`), bound to the release ID, the profile hash, and each stored and live page hash. The tool computes byte equality. Observations are structured JSON, one per profile key: `key`, `observed_value`, `observed_unit`, `observed_condition`, `source_url`, `reviewer_reading`. Decisions: `unchanged` (all pages byte-equal, observations still required), `harmless` (changed bytes, every observation complete and equal), `material` (any observation missing or different). The tool does not parse HTML and claims no machine proof of changed-page meaning. Changed-page meaning stays manual evidence.

### 8.2 Omission and tamper gate (Codex revision 7, item 3)

The source-review record is mandatory package evidence. The package gate rejects:
- a missing `REVIEW.json`;
- changed `REVIEW.json` bytes (the package stores its hash);
- altered observations (the record stores a hash of the observation list, and the hash must match);
- changed release ID, profile hash or stored page hash;
- a live page whose current hash differs from the reviewed `live_sha256`.

Each rejection is exit 1 and makes the package unqualified. Acceptance rows 33 to 37 test each case.

### 8.3 Supplier result

`supplier-result.json`: one row per applicable condition, with `condition`, `method` (`kicad_dru`, `geometric_test`, `slot_inspection`, `mask_inspection`, `manual_evidence`), `status` (`pass`, `fail`, `uncertain`, `unsupported`, `pending`), `evidence` (full hash) and `interpretation`. A mandatory condition with status other than `pass` or `fail` blocks qualification. `uncertain`, `unsupported` and `pending` block qualification.

## 9. Qualification

A package is `qualified` only when all hold:
1. `validate.py --package` reports no finding.
2. Each required check passes with valid evidence: `design.erc`, `design.drc`, `design.parity`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split`, `fab.profile_evidence`, and `fab.supplier_rules`.
3. Every mandatory condition of the supplier result has status `pass` or `fail`, and no `fail` is present.
4. A source review exists for the release ID and profile, passes section 8.2, and its decision is `unchanged` or `harmless`.
5. Every required output role is present with passing evidence. The schematic PDF and the fabrication drawing are required outputs for a bare board.
6. The `fabrication_drawing` output is not qualified by its role or by a non-empty PDF alone. The raw layer PDF from `kicad-cli pcb export pdf` proves only the export. The drawing must be a generated sheet or a supplied drawing with current hashes, and its content must contain: board and release identity, units, overall dimensions, holes, the selected stackup and the supplier process facts (for example trace, space, drill, mask web and substrate values from the profile). The package stores the board, profile and drawing hashes. The implementation test inspects the expected content and renders the example drawing. No general PDF parser is used.

Required outputs (bare board): `copper`, `mask`, `silk`, `paste` when enabled, `outline`, `drill_plated`, `drill_nonplated`, `schematic_pdf`, `fabrication_drawing`, `report`, `evidence`.

Measured PDF commands (`b7-prereq-trials-claude.md`, section 4): `kicad-cli sch export pdf` with the schematic (exit 0). `kicad-cli pcb export pdf --layers F.Fab,B.Fab,Edge.Cuts` (exit 0). Reviewer decision (`b7-pdf-review-root.md`, Codex and Pi): the layer PDF is a layer view with no dimensions, release or stackup. It proves export only. The fabrication drawing content in section 9 item 6 is the required output content.

## 10. Acceptance matrix

Status column: `measured` (a fixture in the frozen evidence), `derived` (computed from measured units), or `to implement` (a required test for the later implementation).

| # | Case | Expected | Status |
|---|---|---|---|
| 1 | `fab.py profile` on the five profiles | exit 0 | to implement |
| 2 | A division key naming no limit, or used twice | exit 1 | to implement |
| 3 | A `minimum` or `maximum` limit with `value_kind: text`, or a text value with a unit | exit 1 | to implement |
| 4 | Maximum limit at below, at and above the threshold | pass, pass, fail | to implement |
| 5 | Minimum limit at below, at and above the threshold | fail, pass, pass | to implement |
| 6 | Trace, space, annular ring, drill at below / at / above (minimum) | fail, pass, pass | to implement |
| 7a | Board width at 406.3 / 406.4 / 406.5 mm (maximum, width axis) | pass, pass, fail | to implement |
| 7b | Board height at 558.7 / 558.8 / 558.9 mm (maximum, height axis) | pass, pass, fail | to implement |
| 8 | Slot minor width 19.9 / 20 / 20.1 mil | fail, pass, pass | to implement |
| 9 | Slot endpoints in reversed order; 0.0004 mm and 0.002 mm endpoint differences; duplicate slot; plated-class mismatch | pass; pass; pass; mismatch; needs two records; mismatch | to implement (tolerance derived) |
| 10 | Narrow exported web 3.9 / 4.0 / 4.1 mil (circle pads) | fail, uncertain (blocks qualification), pass | measured |
| 11 | Web within the error bound of 4 mil | uncertain; blocks qualification | derived |
| 12 | Two pads fused by export (merged opening) | `merged_opening`; no web failure | to implement |
| 13 | Clear polarity, a region, a stroke, another macro | unsupported (exit 2) | to implement |
| 13a | Oval pad (obround aperture) | unsupported (exit 2) | measured (refusal in the analyzer) |
| 13b | Overlapping pads (exact gap -0.1 mm) | `overlapping_cluster` (exit 2) | measured as a gap; refusal to implement |
| 13c | Unknown macro name | unsupported (exit 2) | to implement |
| 14 | Mask-web setting 4 mil with a 3.9 mil nominal fixture: export is two regions | automatic inspection unsupported (exit 2); manual evidence only | measured |
| 14a | `RoundRect` pads at 4.0 mil nominal | exact measured 4.0000 mil; uncertain at the limit | measured |
| 15 | Source exclusion `track_width` entry; staged copy | source: 7 active, 1 excluded; staged: 8 active; rule hash unchanged | measured |
| 15a | `board.kicad_dru` with a below-limit rule, project `ignore` severity, source exclusion | the staged rule fails the geometry; the source keeps its files | to implement (staged copy measured) |
| 16 | Package without `fab.supplier_rules`, and an old qualified manifest without it | unqualified | to implement |
| 17 | Source review absent, or for another release | unqualified | to implement |
| 18 | Changed page with a missing observation, or a material one | unqualified | to implement |
| 19 | Changed page, every observation complete and equal | `harmless`; qualified if the other gates pass | to implement |
| 20 | Published output changed after qualification | package check fails | to implement |
| 21 | Single-layer profile with one of its two pages bound | exit 1 | to implement |
| 22 | Schematic PDF or fabrication drawing missing | unqualified (exit 1) | to implement |
| 23 | Plated drill to internal copper, same net at 0 mil (connected plane) | pass (`hole_clearance`, same-net exception) | to implement |
| 24 | Plated drill to unconnected internal copper at 9.9 / 10 / 10.1 mil | fail, pass, pass | to implement |
| 25 | Edge keepout at 14.9 / 15 / 15.1 mil (minimum) | fail, pass, pass | to implement |
| 26 | Short-text silkscreen at 2.9 / 3 / 3.1 mil (minimum) | fail, pass, pass | to implement |
| 27 | Recommended silkscreen 5 mil and overlapping-drill clearance 5 mil | recommendation: reported, never a failure | to implement |
| 28 | Outline concave corner radius at 0.033 / 0.034 / 0.035 in (minimum) and cutout corner at 0.019 / 0.020 / 0.021 in | fail, pass, pass | to implement |
| 29 | Via construction: blind, buried, filled-and-plated via-in-pad | fail (exit 1) | to implement |
| 30 | Board minimum edge at 6.34 / 6.35 / 6.36 mm (minimum) | fail, pass, pass | to implement |
| 31 | Drill above 250 mil (maximum drill: none) | pass; no maximum failure; the 250 mil note is a note, not a limit | to implement |
| 32 | Order quantity 1, 2, 3, 4 | 1 and 2 fail, 3 passes, 4 fails or is flagged; no silent increase | to implement |
| 33 | `REVIEW.json` missing | unqualified (exit 1) | to implement |
| 34 | `REVIEW.json` bytes changed after packaging | unqualified (exit 1) | to implement |
| 35 | An observation altered after the review | unqualified (exit 1) | to implement |
| 36 | Release ID, profile hash or stored page hash changed | unqualified (exit 1) | to implement |
| 37 | Live page differs from the reviewed `live_sha256` | unqualified (exit 1) | to implement |
| 38 | Slot: PTH board slot exported only in the NPTH file (class swap) | mismatch (exit 1) | to implement |
| 39 | Slot: duplicate board slot with one export record | mismatch (exit 1) | to implement |
| 40 | Slot: board slot with no export record | mismatch (exit 1) | to implement |
| 41 | Oval or obround drilled pad in the B6 worker | unsupported (exit 2); the derivative reports it | to implement |
| 42 | Mask: `merged_opening` and `overlapping_cluster` cases | merged: reported, not a failure; overlap: exit 2 | to implement |
| 43 | Fabrication drawing: content test (release, units, overall size, holes, stackup, process facts, board/profile/drawing hashes) | pass; a missing item fails | to implement |
| 44 | Fabrication drawing: layer PDF used as the drawing | unqualified (exit 1) | to implement |
| 45 | Drawing facts taken from the board by the accepted S-expression parser or pcbnew (no regex object parser) | required; a regex-based extractor is refused in review | to implement |

Rows 4 to 9, 12, 16 to 32 and 33 to 45 need a fixed-image run before any package claim. This paper supports no package claim.

## 11. Open decisions

1. The observation JSON layout, which the reviewers accept as the input form.
2. The overlapping-cluster and merged-opening refusal text, which the reviewers accept.
3. The fabrication drawing generator on the fixed image (section 9 item 6). The content rule is decided. A generator prototype is optional and is not evidence.

Decided by measurement since revision 7: the exclusion entry format (section 7.1), the staged clearing behavior (section 7.2), the rule basename and severity, the slot record format, the PDF commands, and the exact RoundRect method on a fixture (section 6). Decided by review: the fabrication drawing content (section 9 item 6).

Trial tools: fixture and proof scripts that find board objects use the accepted S-expression parser (`skills/pcb-design/scripts/sexp.py`), not a regex. Fixture generation writes a board header by text copy. KiCad produces the exported files, and those files are measured.

## 12. Limits

Consolidated paper only. No B7 implementation, no product code, no commit and no package. The measured facts come from temporary fixtures in the existing B6 image through `podman` and from the pinned `gerbonara` 1.6.3 and `shapely` 2.2.0 installed through `uv`. B6 remains accepted and unchanged. The derived bounds (section 6.4 and section 5 item 4) are not measured.

## 13. Source review inputs (replaces the `--live` argument)

The `review-source` command takes one observation file, `--observations FILE`, and no `--live`. The live page bytes are retained inside the project and named by the observation file. Each page entry is required:

| Field | Rule |
|---|---|
| `page_id` | a key of the profile (`two-layer`, `four-layer`, and so on) |
| `source_url` | the exact URL of the profile for that page |
| `stored_path` | a path under `supplier/pages/`, confined to the skill directory |
| `stored_sha256` | the full SHA-256 of the stored bytes; must equal the file |
| `live_path` | a path under `out/fab/source-review/live/`, confined to the project; the file must exist |
| `live_sha256` | the full SHA-256 of the live bytes; the tool recomputes it and must match |
| `retrieved` | the date of the live fetch (`YYYY-MM-DD`) |

Every path is confined: no symbolic link, no `..`, and no absolute path. A path outside its root is an invalid record, so it is exit 1.

Observation record (`pcb-fab-package/source-observations`, version 1): `release_id`, `profile_sha256` (the canonical hash), `pages` (the list above), `observations` (one entry per profile key, with `key`, `observed_value`, `observed_unit`, `observed_condition`, `source_url` and `reviewer_reading`), `reviewer`, and `statement`. An unknown key in this record is an invalid record (exit 1).

The tool writes `source-review/REVIEW.json` with `release_id`, `profile_sha256`, the page hashes (stored and live), `bytes_equal` for each page (computed), the observation hash, the observations, and the decision. The decision is `unchanged` only when every page is byte-equal, `harmless` when a page changed and every observation is complete and equal, and `material` otherwise (exit 1).

## 14. Manual geometry evidence

A manual geometry result is a report artifact `pcb-fab-package/manual-geometry` (version 1). It is written as the `report` role, and it records the hash of the mask Gerber it covers inside the report. It is not an input role. Its `inputs` use the existing roles `board` and `export_settings`. Fields: `condition`, `procedure` (a short text), `mask_gerber_sha256` (the full hash of the mask Gerber, which must equal the actual manifest output hash), `artifact_path` (under `out/fab/manual/`), `artifact_sha256` (full hash), `reviewer`, `result` (`pass`, `fail`, or `uncertain`), and `statement`. It is listed as an `evidence` record of method `manual` in the existing evidence contract. `fab.py` validates the referenced Gerber hash against the manifest output hash before qualification. A region-producing mask (section 6.1) is eligible only through this route. It is never an automatic pass.
