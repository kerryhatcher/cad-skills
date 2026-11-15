# B7/B8 proposal, revision 4: `pcb-fab-package` (claude-skill-dev)

Date: 2026-11-14. Status: paper proposal for review. Authorized by both design reviews and `b7-b8-design-root.md`. No implementation starts until both reviewers agree to this concrete interface. B6 stays frozen under the replacement manifest `b6-correction-files.sha256` (B6 acceptance is pending the native probe correction in progress).

Revision 3 (`b7-b8-proposal-claude-r3.md`) is kept unchanged. Its corrections are listed in section 10.

Sources: `b7-b8-design-codex.md`, `b7-b8-design-pi.md` (including section 11), `b7-b8-design-root.md`, the five stored OSH Park pages in `/tmp/cad-skills-supplier-evidence/`, `contracts/validate.py`, `contracts/schemas/*.json`.

## 1. Scope and standalone files

`skills/pcb-fab-package/` is an independent skill. It has its own copies of everything it runs. It never calls `skills/pcb-design/` and never uses a repository path at runtime.

| Path | Content | Origin |
|---|---|---|
| `scripts/fab.py` | CLI (section 3) | new |
| `scripts/export_inspect.py` | Gerber, drill and placement inspection used by `design` | copy of the B6 export-check logic, bytes listed in the manifest |
| `scripts/board_inventory.py` | `pcbnew` worker run in the container | byte copy of the B6 worker |
| `scripts/validate.py`, `scripts/project_io.py` | accepted helpers | byte copies of `contracts/` |
| `contracts/schemas/*.json`, `contracts/registry.json`, `contracts/README.md` | copy set | byte copies of `contracts/` |
| `runtime/Containerfile`, `runtime/BUILD.md` | fixed recipe | byte copy of the B6 recipe |
| `supplier/profiles/*.yaml` | five profile records (section 4) | new |
| `supplier/pages/*.html`, `*.headers` | the five retrieved pages and headers | byte copies of `/tmp/cad-skills-supplier-evidence/` |
| `supplier/rules/*.kicad_dru.in` | rule templates per profile (section 5) | new |
| `SKILL.md`, `references/*.md` | docs | new |

Test-builder copies in the repository (narrow, authorized under review): `contracts/validate.py`, `contracts/schemas/manifest.schema.json`, `contracts/README.md`, the B234 builders in `tests/pcb_support.py`, the expectations in `tests/test_pcb_tools.py`. Every bundled copy (`skills/pcb-design/scripts/validate.py`, `skills/pcb-design/contracts/*`, `skills/pcb-fab-package/...`) is updated and tested. The B6 replacement manifest changes with these copies, and it is named for acceptance before B7 lands.

## 2. Contract changes (narrow)

1. `contracts/validate.py`: `fab.supplier_rules` is added to `BARE_CHECKS`. `PCBA_CHECKS` inherits it. The inputs roles `supplier_rules` and `supplier_settings` are added to `INPUT_ROLES`. `CHECK_INPUT_ROLES["fab.supplier_rules"]` is `("board", "supplier_profile", "export_settings", "supplier_rules", "supplier_settings", "toolchain")`.
2. `contracts/schemas/manifest.schema.json`: the inputs role enum gains `supplier_rules` and `supplier_settings`. The outputs enum does not change.
3. Evidence schema: no change. Its `check_id` is free text. The validator enforces the input roles.
4. Tests: an old qualified manifest that lacks `fab.supplier_rules` must become `unqualified` (a test, not a silent pass). Historical manifests are kept as files and their checks are not rewritten.

## 3. CLI `fab.py`

Every write goes under `out/fab/`. Inputs are project-relative. Exit status: 0 success; 1 invalid record, violation, unqualified or stale evidence; 2 missing prerequisite, unsupported operation, invalid arguments, or runtime mismatch; 3 tool failure. Precedence 3, 2, 1, 0.

| Command | Inputs | Writes (all under `out/fab/`) | Exit |
|---|---|---|---|
| `fab.py profile --profile FILE` | profile record, its bundled pages | none (prints findings) | 0 valid; 1 invalid record, extension or division; 2 missing page or arguments |
| `fab.py design --project P` | board, schematic, `.kicad_pro`, `.kicad_dru`, export contract, lock | `reports/design/erc.json`, `drc.json`, `export/` (checked by `export_inspect.py`), each with a binding and a result | 0 pass; 1 violation or check failure; 2 invalid or unsupported; 3 tool failure |
| `fab.py supplier --project P --profile FILE` | design inputs plus the profile | `staging` copy (disposable), `packages-input/supplier/` (`board.kicad_dru`, `board.kicad_pro` effective bytes, `supplier-settings.json`, raw DRC report, `supplier-result.json`, binding, result) | 0 pass; 1 unwaived supplier violation, changed source, or unmet condition; 2 invalid profile or unsupported selector; 3 KiCad failure |
| `fab.py review-source --project P --profile FILE --release ID --live FILE --reviewer NAME --observations FILE` | release ID, profile, stored pages, live bytes, observation file | `source-review/REVIEW.json` (record, section 6) | 0 recorded; 1 material difference or missing observation; 2 invalid input |
| `fab.py package --project P --profile FILE --release ID --dest out/fab/packages/NAME` | results of `design`, `supplier`, the source review | a new package directory, published with `project_io.publish_dir` (atomic, refuses an existing destination) | 0 qualified; 1 unqualified (reason in the manifest); 2 invalid input or existing destination; 3 tool failure |

Path policy: every file the tools write is under `out/fab/` of the project. The package is the only directory published outside the staging area, and it is published with the accepted helper. The review record is written under `out/fab/source-review/` and copied into the package.

## 4. Five profiles

Each profile validates against the accepted `supplier-profile` schema. Numeric design limits and true recommendations go in `limits`. Service facts and process capability go in `extensions`, under explicit field names checked by `fab.py profile`:

| `extensions` field | Meaning | Example (two-layer) |
|---|---|---|
| `service.layers` | required layer count (requirement) | 2 |
| `service.copper` | copper weight per layer, source unit `oz` | "1 oz" |
| `service.substrate` | substrate material text, not finished thickness | "175Tg FR4 Kingboard KB6167F" |
| `service.finished_thickness_nominal_mm` | nominal finished thickness | 1.6 |
| `service.via_construction_prohibited` | list of prohibited constructions (requirement) | ["blind", "buried", "filled_and_plated_via_in_pad"] |
| `service.order_multiple` | required order quantity multiple (requirement) | 3 |
| `process.mask_alignment_max_mil` | process capability, margin | 3 |
| `process.drill_size_tolerance_max_mil`, `process.drill_size_tolerance_typical_mil` | process capability | 2.5, 1.0 |
| `process.drill_position_tolerance_max_mil` | process capability | 2 |
| `notes.max_drill` | tolerance note, not a limit | "No maximum drill size; drills above 250 mil use larger milling tolerances" |

Each extension field names its evidence: the page URL and the stored page hash, or the statement of an inherited page (see section 7).

Limits in `limits` (numeric, with `kind` `minimum`, `maximum` or `recommendation` and `scope` `fabrication` or `margin`): trace, space, annular ring, drill, slot minimum (20 mil, with the interpretation in section 4.1), edge keepout 15 mil, outline and cutout concave corners, board minimum and maximum dimensions (6.35 mm; 406.4 mm and 558.8 mm), mask web 4 mil, short-text silkscreen 3 mil, recommended silkscreen 5 mil, overlapping-drill clearance 5 mil recommendation, plated-drill-to-internal-copper 10 mil (four and six layers).

Division entries name limit keys or extension keys, and `fab.py profile` checks that each key is used exactly once.

### 4.1 Slot-width interpretation

The page says "Minimum Slot Size 20mil (0.508mm) (drill slot only)". It states no length limit. The profile records one limit, `min_slot_size` = 20 mil, with the note `interpretation: minor dimension of a drilled slot`. The test names that inference. No slot length minimum is recorded.

### 4.2 Units

Each limit keeps its source nominal value and unit, and a separate rounded metric label. Board dimensions keep the source 0.25 in, 16 in and 22 in, with the rounded metric values beside them. Conversions use 0.0254 mm per mil.

### 4.3 Five profile contents

| Profile | Source of values | Notes |
|---|---|---|
| `single-layer` | two-layer page (value source), single-layer page (process statement) | The page says the service is a two-layer process, with identical cost, stackup, specs and turn time. Both pages are bound (section 7). |
| `two-layer` | two-layer page | 1 oz copper, 63 mil nominal, 175Tg FR4 |
| `two-layer-hhdc` | HHDC page | 2 oz copper, 32 mil (0.8 mm) nominal, 4x 7628 Ventec VT-47 core with a 28 mil (0.711 mm) core on the page |
| `four-layer` | four-layer page | 1 oz outer, 1/2 oz inner; plated-drill-to-internal clearance 10 mil |
| `six-layer` | six-layer page | minimum drill 8 mil; otherwise as four layers |

The four-layer page's hidden historical stackup comments are not recorded. The rendered values only are recorded.

## 5. Supplier rules and staged effective files

KiCad reads custom rules from the file named after the project basename, next to the `.kicad_pro` file. The staged copy therefore uses the basename `board`:

- Effective rules file: `board.kicad_dru` in the staged `kicad/` directory. It is the source rules, if any, followed by the generated supplier rules. KiCad examines later rules first, so the mandatory rules are not shadowed.
- Effective project file: `board.kicad_pro` in the staged `kicad/` directory. The severity of each supplier rule is set to `error` in the rule-severity block of the project file. The field name is to be proved by a fixture before implementation. The source exclusion list is cleared in the staged copy only.
- Board setup settings that KiCad does not read as custom rules (for example the solder-mask web) are not written as rules. They are checked by a geometric test that reads the saved board setup, and the test result is an entry in the supplier result (section 6).
- The source PCB, source `.kicad_dru` and source `.kicad_pro` are hashed before the run and after the run. A change fails the run (exit 1).
- The package records the hash of the effective staged `board.kicad_dru` and the effective staged `board.kicad_pro`, and the generated rule template hash.

Selectors: `hole_clearance` with `inner` for plated-drill clearance to internal copper (different-net copper only). `physical_hole_clearance` is not used where a same-net connection must pass. Slot minor dimension uses `hole_size`. Overlapping drills, outline and cutout concave corners are geometric tests.

Required proof before implementation agreement: a fixture board named `board` with a below-limit geometry (trace 5.9 mil in the two-layer profile) shows that the generated rule fails it, and that a weaker later source rule, project `ignore` severity and a source exclusion do not hide it.

## 6. Supplier result, source review and qualification

### 6.1 Supplier result (`supplier-result.json`)

One compact record lists every applicable condition of the profile:

| Field | Content |
|---|---|
| `condition` | the limit or extension key |
| `method` | `kicad_dru`, `geometric_test`, `setup_read`, `manual_evidence` |
| `status` | `pass`, `fail`, `pending`, `not_applicable` |
| `evidence` | the hash of the raw report or the observation record that supports the status |
| `interpretation` | text, for the slot rule and similar inferences |

The raw DRC report is an artifact of the result. It does not stand for the conditions it does not test. A mandatory condition without a `pass` or `fail` result fails qualification. Conditions covered by this result: trace, space, annular ring, drill, slot minor width, edge keepout, outline and cutout concave corners, board dimensions, mask web, short-text silkscreen, plated-drill-to-internal clearance, stackup (layer count and copper), via construction, and order quantity. Process capability and finish are manual evidence.

### 6.2 Source review (`REVIEW.json`)

Written by `review-source`. Bound to the release ID, the profile hash, and each stored page hash and each live page hash.

| Field | Content |
|---|---|
| `record`, `version` | `pcb-fab-package/source-review`, `1` |
| `release_id` | the release ID given on the command line |
| `profile_sha256` | canonical profile hash |
| `pages` | for each page of the profile: `stored_sha256`, `live_sha256`, `bytes_equal` (computed by the tool) |
| `observations` | for each checked limit or extension key: `key`, `observed_value`, `observed_unit`, `observed_condition`, `source_url`, `reviewer_reading` |
| `decision` | `unchanged` (every page byte-equal), `harmless` (bytes changed; the reviewer read every material key and found equality), `material` |
| `reviewer`, `statement` | non-empty strings; the statement acknowledges that the meaning of changed pages is manual evidence |

Rules: with unchanged bytes the tool computes equality, and the observations are still required for every key of the profile (this is the acknowledgment that the meaning is unchanged). For changed bytes the observations must cover every checked key. The tool compares each observation with the profile value, unit and condition. A missing observation or a material difference gives `decision: material` and blocks qualification. The tool does not parse HTML and claims no machine proof of changed-page meaning.

### 6.3 Qualification gate (`package`)

A package is `qualified` only if all hold:

1. `validate.py --package` reports no finding.
2. Each required check passes with valid evidence: `design.erc`, `design.drc`, `design.parity`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split`, `fab.profile_evidence`, and the new mandatory `fab.supplier_rules`.
3. The supplier result has a `pass` or `fail` result for every mandatory condition, and no `fail`.
4. The source review exists for this release ID and profile, its pages match the packaged page hashes, and its decision is `unchanged` or `harmless`.
5. Every enabled output role of the bare board is present with a passing evidence record. A `pending` check never qualifies.

## 7. Single-layer provenance

The `single-layer` profile binds two evidence records: the single-layer page (its statement that the service is a two-layer process with identical specifications) and the two-layer page (the value source). Both page hashes appear in `extensions.evidence`. A change to either page requires a new source review.

## 8. Output roles, measured prerequisites and unsupported items

Required output roles for a bare board: `copper`, `mask`, `silk`, `paste` (when enabled), `outline`, `drill_plated`, `drill_nonplated`, `schematic_pdf`, `fabrication_drawing`, `report`, `evidence`.

Measured prerequisites (B6): ERC, DRC with parity, Gerber, Excellon and placement exports, STEP.

Unmeasured: the schematic PDF and the fabrication drawing. They are classified as unsupported until the commands are measured in the fixed image. A package that needs them is unqualified (exit 1), with the reason in the manifest. The implementation measures them first.

## 9. Acceptance matrix

| # | Case | Expected |
|---|---|---|
| 1 | `fab.py profile` on each of the five profiles | pass |
| 2 | A division key that names no limit or extension, or a key used twice | exit 1 |
| 3 | A `minimum` or `maximum` limit with `value_kind: text`, or a text value with a unit | exit 1 |
| 4 | Staged `board` project with a weaker later source rule, project `ignore` severity and a source exclusion, and a below-limit trace (5.9 mil) | `supplier` fails; source PCB, `.kicad_pro` and `.kicad_dru` bytes unchanged |
| 5 | Each numeric limit at below, at and above its threshold: trace, space, annular, drill (9.9, 10, 10.1 mil), slot minor width (19.9, 20, 20.1 mil, the declared inference), edge keepout (14.9, 15, 15.1 mil), mask web (3.9, 4, 4.1 mil), short-text silkscreen (2.9, 3 mil), board minimum (6.34, 6.35, 6.36 mm), board maximum | below fails; at and above pass |
| 6 | Four- and six-layer internal copper: same-net connected pad at 0 mil passes; unconnected internal copper at 9.9 mil fails and at 10 mil passes | as stated |
| 7 | Drill above 250 mil | passes; no maximum failure |
| 8 | Outline and cutout concave corners at the stated radii, below and above | as the geometric test defines |
| 9 | Via construction: blind, buried and filled-and-plated via-in-pad | fail |
| 10 | Order quantity 1, 2, 3, 4 | 1, 2, 4 fail or are flagged; 3 passes; no silent increase |
| 11 | Package without `fab.supplier_rules`, and an old qualified manifest without it | unqualified, not a pass |
| 12 | Supplier result missing a mandatory condition | unqualified |
| 13 | Source review absent, or for another release ID | unqualified |
| 14 | Changed page with an observation missing, or a material observation | unqualified |
| 15 | Changed page, every observation complete and equal, decision `harmless` | qualified (other gates pass) |
| 16 | Changed profile, stored page or live page each on its own | the review or the evidence hash mismatches; unqualified until refreshed |
| 17 | Published output changed after qualification | the package check fails |
| 18 | Single-layer profile with only one of its two pages bound | exit 1 |
| 19 | Four-layer export with the published `.GTL/.G2L/.G3L/.GBL` names | layer content checks pass; no X2 path added |
| 20 | Validate the two-layer profile through the copied validator from outside the repository; compare every bundled copy with its source | pass; bytes equal |

Rows 4–8, 19 need a fixed-image KiCad run. Paper alone does not support them.

## 10. Revision 3 corrections, incorporated

- Staged rule and project filenames are named (section 5). Proof required (section 5).
- Nominal and process metadata moved to `extensions`, with named fields (section 4). Requirements (layers, via prohibition, order multiple) are requirements, not recommendations.
- Complete boundary coverage (acceptance rows 5–10).
- Source review bound to release, profile and each page; observations per key; no HTML parser (section 6.2).
- Supplier result covers every applicable condition; the raw DRC report is only an artifact (section 6.1).
- Path policy and exit meanings defined (section 3).
- Standalone files listed (section 1).
- Units keep the source nominal and the metric label (section 4.2).

## 11. Open decisions for the reviewers

1. KiCad field names in `.kicad_pro` for rule severities and the solder-mask web setting: to be proved by fixtures before implementation.
2. The schematic PDF and the fabrication drawing: measure, or keep the package unqualified until they are measured.
3. Whether `observations` is a JSON file supplied by the reviewer or typed through the CLI. The proposal assumes a JSON file with the fields in 6.2.

## 12. Limits

Paper proposal. No KiCad rule, container run, schema change or copy was made by this revision. The B6 replacement manifest must be accepted before any copy change lands.
