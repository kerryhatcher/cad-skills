# B7/B8 proposal, revision 6: consolidated `pcb-fab-package` interface (claude-skill-dev)

Date: 2026-11-14. Status: consolidated paper for review. It replaces revisions 4 and 5 (`b7-b8-proposal-claude-r4.md`, `b7-b8-proposal-claude-r5.md`) and the addendum (`b7-b8-r4-addendum-claude.md`). Those files stay as history and are not reused for implementation. No B7 implementation before explicit reviewer agreement. B6 is accepted and stays unchanged (`b6-acceptance-root.md`).

Measured basis: `b7-prereq-trials-claude.md`. Reviews consolidated: `b7-b8-design-codex.md`, `b7-b8-design-pi.md` (section 11), `b7-b8-design-root.md`, `b7-b8-r5-review-root.md`, the Codex and Pi r5 sections, `b7-mask-research-root.md`.

## 1. Scope and standalone files

`skills/pcb-fab-package/` is independent of `skills/pcb-design/`. It has no runtime reference outside its own directory. B6 keeps circular drills only.

| Path | Origin |
|---|---|
| `scripts/fab.py` | new CLI (section 3) |
| `scripts/export_inspect.py` | owned derivative. The B6 export checks are extracted from `skills/pcb-design/scripts/pcb.py` (functions `check_export_outputs`, `excellon`, `export_subset`, `placement_filter`) and adapted. It is not a byte copy of a separate file. |
| `scripts/inspect_slots.py` | new (section 5) |
| `scripts/inspect_mask.py` | new (section 6) |
| `scripts/board_inventory.py` | byte copy of the B6 worker `skills/pcb-design/scripts/board_inventory.py` |
| `scripts/board_inventory_slots.py` | owned derivative of the worker. Slot and oval drills are reported with minor and major dimensions instead of being refused. B6 keeps its worker. |
| `scripts/validate.py`, `scripts/project_io.py` | byte copies of `contracts/validate.py` and `contracts/project_io.py`, verified by the package test |
| `contracts/schemas/*.json`, `contracts/registry.json`, `contracts/README.md` | byte copies of `contracts/` |
| `runtime/Containerfile`, `runtime/BUILD.md` | byte copies of the B6 runtime recipe |
| `supplier/profiles/*.yaml` | five profile records (section 4) |
| `supplier/pages/*`, `supplier/rules/*.kicad_dru.in` | byte copies of the retained pages; rule templates |
| `SKILL.md`, `references/*.md` | new |

## 2. Contract changes (narrow, authorized under review)

1. `contracts/validate.py`: `fab.supplier_rules` is added to `BARE_CHECKS`. `PCBA_CHECKS` inherits it. `INPUT_ROLES` gains `supplier_rules` and `supplier_settings`. `CHECK_INPUT_ROLES["fab.supplier_rules"] = ("board", "supplier_profile", "export_settings", "supplier_rules", "supplier_settings", "toolchain")`.
2. `contracts/schemas/manifest.schema.json`: the inputs role enum gains `supplier_rules` and `supplier_settings`. The outputs enum does not change.
3. Evidence schema: no change.
4. Test builders: `tests/pcb_support.py` and the expectations in `tests/test_pcb_tools.py` gain the check. A test shows that a package without `fab.supplier_rules` is unqualified, not a pass.
5. Every bundled copy is updated and tested. `skills/pcb-design/scripts/validate.py` and `skills/pcb-design/contracts/*` change with `contracts/`. The B6 replacement manifest is named for acceptance before the copy lands.

## 3. CLI and exit codes (one table for every command)

Exit codes, for every command in this interface:

| Exit | Meaning |
|---|---|
| 0 | success: valid, passed, qualified, or recorded |
| 1 | invalid record or extension, violation, failed check, unqualified package, stale or missing evidence, or an unmet mandatory condition |
| 2 | invalid arguments, missing prerequisite, unsupported operation or construct, runtime or image mismatch, existing destination |
| 3 | tool failure (KiCad, the worker or the container failed or produced no output) |

Precedence: 3, 2, 1, 0.

| Command | Inputs | Writes (under `out/fab/` only) | Exits |
|---|---|---|---|
| `fab.py profile --profile FILE` | profile record, its pages | none; prints findings | 0 valid; 1 invalid record, extension or division; 2 missing page or arguments |
| `fab.py design --project P` | board, schematic, `.kicad_pro`, `.kicad_dru`, export contract, lock | `reports/design/*` (ERC, DRC with parity, export set), each with binding and result | 0 pass; 1 check failure; 2 unsupported construct or prerequisite; 3 tool failure |
| `fab.py supplier --project P --profile FILE` | design inputs and the profile | staged copy (disposable) and `supplier/` with the effective `board.kicad_dru`, the effective `board.kicad_pro`, `supplier-settings.json`, the raw DRC report, the slot and mask inspections, `supplier-result.json`, binding and result | 0 pass; 1 invalid profile, unmet condition, violation, or source changed during the run; 2 unsupported selector or construct, missing prerequisite, runtime mismatch; 3 KiCad failure |
| `fab.py inspect-slots --project P --profile FILE` | board, drill outputs, profile | `reports/slots.json` | 0 pass; 1 mismatch; 2 unsupported; 3 tool failure |
| `fab.py inspect-mask --project P --profile FILE` | mask Gerbers, profile | `reports/mask.json` | 0 pass; 1 violation or uncertain result; 2 unsupported construct; 3 tool failure |
| `fab.py review-source --project P --profile FILE --release ID --observations FILE --reviewer NAME` | release ID, profile, stored pages, observation JSON | `source-review/REVIEW.json` | 0 recorded with decision `unchanged` or `harmless`; 1 decision `material` or a missing observation; 2 invalid arguments or unknown key |
| `fab.py package --project P --profile FILE --release ID --dest out/fab/packages/NAME` | results of `design`, `supplier`, the source review | new package directory, published with `project_io.publish_dir` | 0 qualified; 1 unqualified (reason in the manifest); 2 existing destination or missing input; 3 tool failure |

Path policy: every file is written under `out/fab/` of the project. Packages are published only with `project_io.publish_dir`.

## 4. Profiles: limit kinds and boundaries

Kinds and scopes follow the accepted schema: `kind` is `minimum`, `maximum`, `recommendation` or `unconfirmed`. `scope` is `fabrication`, `assembly` or `margin`. `value_kind` is `number` or `text`. A text value has no unit. A number has a unit.

Boundary rules (these are the only ones):
- A `maximum` limit passes at and below the threshold and fails above it.
- A `minimum` limit fails below the threshold and passes at and above it.
- A `recommendation` never fails the package. It is reported as a finding.

Limits in `limits` (numeric design limits and actionable recommendations): trace width, spacing, annular ring, drill (minimum), slot minor dimension (minimum, 20 mil), edge keepout (minimum, 15 mil), outline and cutout concave corner radii (minimum), board width and height (minimum 6.35 mm, maximum 406.4 mm and 558.8 mm), mask web (minimum 4 mil, geometric), short-text silkscreen (minimum 3 mil), recommended silkscreen (recommendation 5 mil), overlapping-drill clearance (recommendation 5 mil), plated-drill-to-internal-copper (minimum 10 mil, four and six layers).

Extensions (service facts and process capability, validated by `fab.py profile` with named fields; the schema `extensions` is an untyped object). Published process capability is not a design margin. It is recorded as manual evidence with its published value and unit:
- `service.layers` (requirement), `service.copper`, `service.substrate`, `service.finished_thickness_nominal_mm`, `service.via_construction_prohibited` (requirement list), `service.order_multiple` (requirement).
- `process.mask_alignment_max_mil`, `process.drill_size_tolerance_max_mil`, `process.drill_size_tolerance_typical_mil`, `process.drill_position_tolerance_max_mil`, `process.drill_position_tolerance_typical` (text). These are published process capability values. They are not CAD-measured and not design margins.
- `notes.max_drill`: a tolerance note, not a limit.

Source values: from the stored pages only (`b7-b8-two-layer-profile-example.yaml` is the worked example, a subset of the table).

Single-layer profile: its limits are the two-layer limits. Its `evidence` binds two pages: the single-layer page (the process statement that the service is a two-layer process with identical specifications) and the two-layer page (the value source).

Slot width: the supplier phrase is "Minimum Slot Size 20mil (drill slot only)". The profile records `min_slot_size` = 20 mil with `interpretation: minor dimension of a drilled slot`. No slot length minimum exists in the source.

## 5. Slot export inspection

Measured basis: the exported non-plated drill file has one `G85` record per slot (`X..Y..G85X..Y..`), with the tool record `T..C<width>` for the minor dimension. Coordinates are 3:3 mm, with 0.001 mm increments.

Method:
1. From the saved board (`board_inventory_slots.py`, container), list each slot with its endpoints (centres of the end arcs), its minor dimension and its plated class (PTH or NPTH by the file it belongs to).
2. From the exported drill file for each class, parse each `G85` record into an unordered endpoint pair, and read the minor dimension from the `T` record of that slot.
3. Compare the board and export as multisets, per plated class: each board slot is matched once, and each exported record is matched once. Endpoint pairs are compared as unordered pairs.
4. Tolerance: 0.001 mm per coordinate (one coordinate increment; the rounding error is at most 0.0005 mm). Two endpoints of the same pair match when each coordinate differs by no more than 0.001 mm.
5. Orientation: the angle from the endpoints is compared with the board rotation. For a near-circular slot (major minus minor below 0.001 mm) the orientation is not compared, and the record is reported as `near_circular`.
6. A board slot with no export record, an export record with no board slot, a difference in multiplicity, or a plated class mismatch is a mismatch (exit 1).

Acceptance: minor width 19.9, 20 and 20.1 mil (fails, passes, passes); endpoint pairs in reversed order match; a 0.002 mm endpoint difference is a mismatch; a duplicate slot needs two export records; a slot in the wrong plated file is a mismatch; a 45-degree slot matches the measured rotated record.

## 6. Mask geometry inspection

The saved mask-web setting is a parameter. It does not establish the exported geometry. The mask is measured from the exported Gerber.

Automatic subset (selected from the template mask, measured in `b7-prereq-trials-claude.md`):
- Flashes (`D03`) of circle (`C`) and rectangle (`R`) apertures, and of the `RoundRect` macro, with dark polarity only.
- Anything else is `unsupported` with the object named (exit 2): regions (`G36`/`G37`), strokes (`D01`), other macros, clear polarity (`%LP C`), other aperture types.

Method: exact distance between two flashed shapes, from the macro parameters, with no polygon conversion. Circles and rectangles have closed-form distances. A `RoundRect` flash is the core rectangle (its corner centres) Minkowski-summed with a disk of radius `$1`. Its outline, its four corner circles and its four edge vectors together describe that shape exactly. The distance between two such flashes is max(0, d_core - r1 - r2), where d_core is the distance between the core rectangles and a circle's core is its centre.

Error bound (combined, per decision): Gerber coordinates have six decimals in millimetres, so each coordinate is exact to 0.000001 mm. A distance uses at most two coordinate roundings and one floating-point operation. The bound is 0.000002 mm plus 0.000001 mm of floating-point margin, so 0.000003 mm in total. This figure is derived from the coordinate format, not measured. This bound applies to the exact method only. A polygon conversion would add its own chord error, and that is not used.

Resource bounds (inspection): flashes are checked only against neighbours whose core boxes lie within the limit plus twice the largest radius. Limits: at most 10000 flashes per layer, at most 5 MB of Gerber input, at most 2 seconds of run time, and memory linear in the flash count. Exceeding any limit gives exit 2 with the reason. No raster is used.

Decision rule (no tolerance band becomes a pass; a result at the limit is never a pass):
- A web is `pass` only when its exact minimum distance is at least the limit plus the error bound. A distance exactly at the limit is `uncertain`, not a pass.
- A web is `fail` when the distance is below the limit by more than the error bound.
- A web within the error bound of the limit is `uncertain`. An uncertain web is never a pass and blocks qualification.

Merged openings: two flashes with no mask between them after export form one opening. This is reported as `merged_opening` with the object pair. It is not a web failure and not a manufacturing failure.

Manual geometry evidence: an operator-supplied geometric observation is allowed only with a hashed artifact and a stated procedure, as manual evidence. It is never an automatic pass.

Not measured yet: the exact-distance code on a fixture (the 3.9, 4.0 and 4.1 mil rows). This is the first step after the release.

## 7. Supplier rules and effective staged files

- Basename: the staged project is named `board`. KiCad reads custom rules from `board.kicad_dru`, next to `board.kicad_pro`. Measured: a file with another basename gives no violations; a file named `board.kicad_dru` gives violations (trial rule cases A and B).
- Severity: `board.design_settings.rule_severities.<rule>` in `board.kicad_pro`. Measured: `ignore` removes the violations (case C). The supplier severity is `error`.
- Exclusions: the staged `board.kicad_pro` clears `drc_exclusions`. The exclusion entry format is not measured, so the clearing is format-agnostic. The source file keeps its exclusions.
- The package records the hash of the effective staged `board.kicad_dru` and `board.kicad_pro`.
- Generated rules are placed after the source rules. KiCad examines later rules first.
- Source PCB, source `.kicad_dru` and source `.kicad_pro` are hashed before and after the run. A change is exit 1.

## 8. Source review and supplier result

Source review (`REVIEW.json`), bound to the release ID, the profile hash, and each stored and live page hash. The tool computes byte equality. Observations are structured JSON, one per profile key: `key`, `observed_value`, `observed_unit`, `observed_condition`, `source_url`, `reviewer_reading`. Decisions: `unchanged` (all pages byte-equal, observations still required), `harmless` (changed bytes, every observation complete and equal), `material` (any observation missing or different). The tool does not parse HTML and claims no machine proof of changed-page meaning. Changed-page meaning stays manual evidence.

Supplier result (`supplier-result.json`): one row per applicable condition, with `condition`, `method` (`kicad_dru`, `geometric_test`, `slot_inspection`, `mask_inspection`, `manual_evidence`), `status` (`pass`, `fail`, `uncertain`, `unsupported`, `pending`), `evidence` (hash) and `interpretation`. A mandatory condition with status other than `pass` or `fail` blocks qualification. `uncertain`, `unsupported` and `pending` block qualification.

## 9. Qualification

A package is `qualified` only when all hold:
1. `validate.py --package` reports no finding.
2. Each required check passes with valid evidence: `design.erc`, `design.drc`, `design.parity`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split`, `fab.profile_evidence`, and `fab.supplier_rules`.
3. Every mandatory condition of the supplier result has status `pass` or `fail`, and no `fail` is present.
4. A source review exists for the release ID and profile, its pages match the packaged page hashes, and its decision is `unchanged` or `harmless`.
5. Every required output role is present with passing evidence. The schematic PDF and the fabrication drawing are required outputs for a bare board, so a package that needs them is unqualified until their commands are part of the fixed image and listed fixtures.

Required outputs (bare board): `copper`, `mask`, `silk`, `paste` when enabled, `outline`, `drill_plated`, `drill_nonplated`, `schematic_pdf`, `fabrication_drawing`, `report`, `evidence`.

Measured PDF commands (`b7-prereq-trials-claude.md` section 4): `kicad-cli sch export pdf` with the schematic (exit 0). `kicad-cli pcb export pdf --layers F.Fab,B.Fab,Edge.Cuts` (exit 0). The fabrication drawing is measured only on a fixture, so it stays unqualified until the fixed image and a fixture establish it.

## 10. Acceptance matrix

| # | Case | Expected |
|---|---|---|
| 1 | `fab.py profile` on the five profiles | exit 0 |
| 2 | A division key naming no limit, or used twice | exit 1 |
| 3 | A `minimum` or `maximum` limit with `value_kind: text`, or a text value with a unit | exit 1 |
| 4 | Maximum limit at below, at and above the threshold | pass, pass, fail |
| 5 | Minimum limit at below, at and above the threshold | fail, pass, pass |
| 6 | Trace, space, annular ring, drill at below / at / above (minimum) | fail, pass, pass |
| 7a | Board width at 406.3 / 406.4 / 406.5 mm (maximum, width axis) | pass, pass, fail |
| 7b | Board height at 558.7 / 558.8 / 558.9 mm (maximum, height axis) | pass, pass, fail |
| 8 | Slot minor width 19.9 / 20 / 20.1 mil | fail, pass, pass |
| 9 | Slot endpoints in reversed order; 0.002 mm endpoint difference; duplicate slot; plated-class mismatch | pass; mismatch; needs two records; mismatch |
| 10 | Narrow exported web 3.9 / 4.0 / 4.1 mil | fail, uncertain (blocks qualification), pass (after the exact-distance measurement and fixtures) |
| 11 | Web within the error bound of 4 mil | uncertain; blocks qualification |
| 12 | Two pads fused by export | `merged_opening`; no web failure |
| 13 | Clear polarity, a region, a stroke, another macro | unsupported (exit 2) |
| 14 | Mask-web setting 4 mil with an exported web of 3.9 mil | the exported geometry decides: fail |
| 15 | `board.kicad_dru` with a below-limit rule, project `ignore` severity, source exclusion | the staged rule fails the geometry; the source keeps its files |
| 16 | Package without `fab.supplier_rules`, and an old qualified manifest without it | unqualified |
| 17 | Source review absent, or for another release | unqualified |
| 18 | Changed page with a missing observation, or a material one | unqualified |
| 19 | Changed page, every observation complete and equal | `harmless`; qualified if the other gates pass |
| 20 | Published output changed after qualification | package check fails |
| 21 | Single-layer profile with one of its two pages bound | exit 1 |
| 22 | Schematic PDF or fabrication drawing missing | unqualified (exit 1) |
| 23 | Plated drill to internal copper, same net at 0 mil (connected plane) | pass (`hole_clearance`, same-net exception) |
| 24 | Plated drill to unconnected internal copper at 9.9 / 10 / 10.1 mil | fail, pass, pass |
| 25 | Edge keepout at 14.9 / 15 / 15.1 mil (minimum) | fail, pass, pass |
| 26 | Short-text silkscreen at 2.9 / 3 / 3.1 mil (minimum) | fail, pass, pass |
| 27 | Recommended silkscreen 5 mil and overlapping-drill clearance 5 mil | recommendation: reported, never a failure |
| 28 | Outline concave corner radius at 0.033 / 0.034 / 0.035 in (minimum) and cutout corner at 0.019 / 0.020 / 0.021 in | fail, pass, pass |
| 29 | Via construction: blind, buried, filled-and-plated via-in-pad | fail (exit 1) |
| 30 | Board minimum edge at 6.34 / 6.35 / 6.36 mm (minimum) | fail, pass, pass |
| 31 | Drill above 250 mil (maximum drill: none) | pass; no maximum failure; the 250 mil note is a recommendation |
| 32 | Order quantity 1, 2, 3, 4 | 1 and 2 fail, 3 passes, 4 fails or is flagged; no silent increase |

Rows 4–10, 14–15, 22 and 23–32 need a fixed-image run. This paper alone supports nothing.

Source-exclusion behaviour (staged `drc_exclusions` override): not measured. The format of a KiCad 10 `drc_exclusions` entry has not been established by a fixture, so no row claims that the staged clearing hides nothing. The fixture (a real source exclusion that would hide a supplier violation, then the staged clearing) is a prerequisite before any exclusion claim.

## 11. Open decisions

1. The exact-distance code and its fixtures (rows 10–11).
2. The exclusion entry format (before any exclusion-specific claim).
3. The fabrication drawing command on the fixed image.
4. The observation JSON file layout, which the reviewers accept as the input form.

## 12. Limits

Consolidated paper only. No B7 implementation, no KiCad run of the inspections, no container run of the new code, and no package. B6 remains accepted and unchanged.

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

Every path is confined: no symbolic link, no `..`, and no absolute path. A path outside its root is exit 2.

Observation record (`pcb-fab-package/source-observations`, version 1): `release_id`, `profile_sha256` (the canonical hash), `pages` (the list above), `observations` (one entry per profile key, with `key`, `observed_value`, `observed_unit`, `observed_condition`, `source_url` and `reviewer_reading`), `reviewer`, and `statement`.

The tool writes `source-review/REVIEW.json` with `release_id`, `profile_sha256`, the page hashes (stored and live), `bytes_equal` for each page (computed), the observations, and the decision. The decision is `unchanged` only when every page is byte-equal, `harmless` when a page changed and every observation is complete and equal, and `material` otherwise (exit 1).

## 14. Manual geometry evidence

A manual geometry result is a record `pcb-fab-package/manual-geometry` (version 1) with: `condition`, `procedure` (a short text), `input_sha256` (the full hash of the mask Gerber it covers), `artifact_path` (under `out/fab/manual/`), `artifact_sha256` (full hash), `reviewer`, `result` (`pass`, `fail`, or `uncertain`), and `statement`. It is listed as an `evidence` record of method `manual` in the existing evidence contract, with its `inputs` listing the mask Gerber by hash. It is never an automatic pass. It needs no new registry and no general framework.
