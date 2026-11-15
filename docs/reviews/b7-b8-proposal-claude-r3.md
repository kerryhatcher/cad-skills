# B7/B8 proposal, revision 3: independent skill `pcb-fab-package` (claude-skill-dev)

Date: 2026-11-14. Status: paper proposal for review. No implementation before B6 acceptance and design agreement. B6 revision 3 stays frozen. Revisions 1 and 2 stay unchanged. Revision 2 placed fabrication inside `pcb-design`; this revision replaces that scope.

Sources read for this revision: the five stored OSH Park pages in `/tmp/cad-skills-supplier-evidence/` (bytes and headers), `contracts/validate.py`, `contracts/schemas/supplier-profile.schema.json` and `manifest.schema.json`, and the research files `b7-rule-research-*.md`, `b7-b8-preparation-*.md`. Worked example: `b7-b8-two-layer-profile-example.yaml` (validated with `contracts/validate.py`, status pass, content hash `632546c36b3a0647210a1de813cac340ee8a265527ef8ef5b761a292bde773eb`).

## 1. Scope and bundled files

`skills/pcb-fab-package/` operates alone. It has no file dependency on `skills/pcb-design/`. It reads a project folder with the same record layout (`board.yaml`, `kicad/board.kicad_pcb`, and so on). That layout is a documented record format, not a file import.

| Path | Kind | Source |
|---|---|---|
| `SKILL.md`, `references/*.md` | skill docs | new |
| `scripts/fab.py` | dedicated CLI (section 2) | new |
| `scripts/validate.py`, `scripts/project_io.py` | accepted helpers, copies | `contracts/` (byte copies) |
| `contracts/schemas/*`, `contracts/README.md` | copy set | `contracts/` (byte copies, README with `${PROJECT}` and `${PACKAGE}` placeholders) |
| `runtime/Containerfile`, `runtime/BUILD.md` | fixed recipe, copy | identical to the B6 recipe bytes |
| `supplier/profiles/*.yaml` | five profile records | section 3 |
| `supplier/evidence/*.html`, `*.headers` | the five stored pages and headers, byte copies | `/tmp/cad-skills-supplier-evidence/` |
| `templates/rc-fab-project/` | optional fixture project | derived from B6 template bytes |
| `tests/test_pcb_fab_package.py` (repo) | acceptance tests | section 7 |

Cross-copy changes outside the new skill (narrow, requested as authorized):

1. `contracts/validate.py`: add `fab.supplier_rules` to `BARE_CHECKS` (so `PCBA_CHECKS` inherits it); add roles `supplier_rules` and `supplier_settings` to `INPUT_ROLES`; add `CHECK_INPUT_ROLES["fab.supplier_rules"] = ("board", "supplier_profile", "export_settings", "supplier_rules", "supplier_settings")`.
2. `contracts/schemas/manifest.schema.json`: add `supplier_rules` and `supplier_settings` to the manifest role enum.
3. `contracts/README.md`: document the check and both roles (placeholders kept).
4. Copies of (1)–(3) in every skill that carries them: `skills/pcb-fab-package/` (new) and `skills/pcb-design/contracts/` and `skills/pcb-design/scripts/validate.py`. The B6 copy test requires equality, so the B6 copy changes. This is the one B6 file-set change; it is named here for the reviewers.
5. B234 builders: `tests/pcb_support.py` (`build_package`, `build_project`) and the expectations in `tests/test_pcb_tools.py` gain the new check and roles.

## 2. CLI: `scripts/fab.py`

All inputs are project-relative. Every write goes under `out/` of the project and holds the project lock. Exit status: 0 success, 1 violation, stale or unqualified, 2 invalid input, unsupported selector or runtime mismatch, 3 tool failure. Precedence 3, 2, 1, 0.

| Command | Inputs | Outputs | Exit |
|---|---|---|---|
| `fab.py profile --profile FILE` | profile record, bundled page bytes | prints the findings; no write | 0 valid; 1 invalid record or division; 2 missing page or arguments |
| `fab.py supplier --project P --profile FILE` | board, schematic, `.kicad_pro`, rule files, `manufacturing/export.yaml`, `toolchain.lock.json`, profile | `out/fab/supplier/rules/supplier.kicad_dru`, `out/fab/supplier/rules/supplier-settings.json`, `out/fab/reports/supplier-drc-SHA256.json` (raw), `out/fab/reports/supplier.binding.json`, `out/fab/reports/supplier.result.json` (written last) | 0 pass; 1 unwaived supplier finding or source changed during run; 2 invalid profile, unsupported selector, lock mismatch; 3 KiCad failure |
| `fab.py review-source --project P --profile FILE --live FILE --reviewer NAME --decision unchanged\|harmless\|material --checked KEY...` | profile, live page bytes, stored page | `fab/supplier-review.json` (skill record, section 5) | 0 recorded (decision unchanged or harmless); 1 decision material; 2 invalid input or unknown key |
| `fab.py design --project P` | board, schematic, export settings, lock | ERC, DRC with parity and the export set (B6 commands subset, measured by B6), raw reports and bindings under `out/fab/reports/` | 0 pass; 1 violation; 2 invalid; 3 tool failure |
| `fab.py package --project P --profile FILE --dest out/fab/packages/NAME` | the results of `supplier`, `design`, the review record | a new package directory with `manifest.json`, the evidence files, the output files and the stored page | 0 qualified; 1 unqualified (reason in manifest); 2 invalid input or existing destination; 3 tool failure |

Rules shared by all commands:

- `supplier` never refills zones and never writes the source PCB, the source `.kicad_dru` or the source `.kicad_pro`. It works on a staged copy and compares the source hashes before publication.
- Supplier rules are placed after the project rules in the staged `supplier.kicad_dru`. KiCad examines later custom rules first, so the mandatory rules are not shadowed by a weaker earlier rule.
- The staged `.kicad_pro` sets every supplier rule severity to `error` and clears the source exclusion list for the supplier run. The source files keep their settings.
- The raw DRC report is the evidence artifact of `fab.supplier_rules`. Its bytes are named by their SHA-256.

## 3. Five profiles: verified values and key names

Every value below was read from the stored page named in the source column. The stored page is the evidence (`evidence_sha256`). Nothing comes from the earlier boundary table alone.

Key naming carries the metadata that the schema has no field for:
- `nominal_*` (kind `recommendation`, scope `fabrication`): the page's nominal statement, for example "Board Thickness 63mil (1.6mm) nominal".
- `*_max`, `*_typical`, `*_tolerance` (scope `margin`): process capability values from the page, for example "Drill Size tolerance Max: +/- 2.5mil".
- `min_*`, `max_*` (kind `minimum`/`maximum`, scope `fabrication`): design limits.
- `kind: unconfirmed` is reserved for a value the page does not state. The five pages state every value below, so no value uses it.

| Key (scope) | Single-layer | Two-layer | Two-layer HHDC | Four-layer | Six-layer | Page statement |
|---|---|---|---|---|---|---|
| `min_trace` (fab) | 6 mil | 6 mil | 6 mil | 5 mil | 5 mil | "Trace Width" in Copper Specifications |
| `min_space` (fab) | 6 mil | 6 mil | 6 mil | 5 mil | 5 mil | "Trace Spacing" |
| `min_annular_ring` (fab) | 5 mil | 5 mil | 5 mil | 4 mil | 4 mil | "Minimum Annular Ring" |
| `min_drill` (fab) | 10 mil | 10 mil | 10 mil | 10 mil | 8 mil | "Minimum Drill Size" |
| `min_slot_size` (fab) | 20 mil | 20 mil | 20 mil | 20 mil | 20 mil | "Minimum Slot Size 20mil (drill slot only)" |
| `plated_drill_to_internal_copper` (fab) | n/a | n/a | n/a | 10 mil | 10 mil | "Plated Drill to Internal Layer Copper Clearance" |
| `edge_keepout` (fab) | 15 mil | 15 mil | 15 mil | 15 mil | 15 mil | "Board Edge Keepout 15mil from nominal board edge" |
| `mask_web_min` (fab) | 4 mil | 4 mil | 4 mil | 4 mil | 4 mil | "Minimum soldermask web 4 mil" |
| `mask_alignment_max` (margin) | 3 mil | 3 mil | 3 mil | 3 mil | 3 mil | "Maximum soldermask alignment 3mil" |
| `silk_line_min_short_text` (fab) | 3 mil | 3 mil | 3 mil | 3 mil | 3 mil | "3 mil (short lines, text, graphics)" |
| `silk_line_recommended` (fab, recommendation) | 5 mil | 5 mil | 5 mil | 5 mil | 5 mil | "5 mil (recommended minimum)" |
| `drill_size_tolerance_max` (margin) | 2.5 mil | 2.5 mil | 2.5 mil | 2.5 mil | 2.5 mil | "Drill Size tolerance Max: +/- 2.5mil" |
| `drill_size_tolerance_typical` (margin) | 1.0 mil | 1.0 mil | 1.0 mil | 1.0 mil | 1.0 mil | "Typical: +/- 1.0mil" |
| `drill_position_tolerance_max` (margin) | 2 mil | 2 mil | 2 mil | 2 mil | 2 mil | "Drill Positional Tolerance Max: 2mil" |
| `drill_position_tolerance_typical` (margin, text) | less than 1 mil | same | same | same | same | "Typical: <1mil" |
| `overlapping_drill_clearance` (fab, recommendation) | 5 mil | 5 mil | 5 mil | 5 mil | 5 mil | "5 mil clearance is recommended between holes" |
| `max_drill` (fab, text) | no maximum | no maximum | no maximum | no maximum | no maximum | "Maximum Drill Size None; above 250mil larger milling tolerances" |
| `board_min_edge` (fab, mm) | 6.35 | 6.35 | 6.35 | 6.35 | 6.35 | "Minimum board size 0.25in (6.35mm)" |
| `board_max_width` / `board_max_height` (fab, mm) | 406.4 / 558.8 | same | same | same | same | "Maximum board size 16in (406.4mm) by 22in (558.8mm)" |
| `nominal_board_thickness` (fab, mm) | 1.6 | 1.6 | 0.8 | 1.6 | 1.6 | "Board Thickness 63mil (1.6mm) nominal"; HHDC "32mil (0.8mm) nominal" |
| `substrate` (text) | two-layer | 175Tg FR4 (Kingboard KB6167F) | 180 Tg FR4 Ventec VT-47, core "4x 7628 Ventec VT-47", "28 mil (0.711mm) core" | 190Tg FR408-HR | published stackup | Material Specs |
| `copper_weight` (text) | 1 oz | 1 oz | 2 oz | 1 oz outer, 1/2 oz inner | 1 oz outer, 1/2 oz inner | Copper Weight |
| `via_construction` (text) | blind, buried, filled+plated via-in-pad: No; tenting yes | same | same | same | same | "Blind Via No", "Via Tenting Yes (filled hole and flat surface not guaranteed)" |
| `order_multiple` (text) | multiples of three | same | same | same | same | "in multiples of three" |

The worked example (`b7-b8-two-layer-profile-example.yaml`) is a subset of this table: the two-layer design keys without the substrate and per-layer copper entries. It validates as the schema requires.

Single-layer: the stored page says "we support single layer designs on our 2 layer fabrication service. The cost, stackup, specs, and turn time are identical to that of the 2 layer service." Its limits are therefore the two-layer limits, with the single-layer page as evidence. The page has no specification table of its own.

## 4. Division and the tool's check

The schema accepts division entries as free strings. `fab.py profile` therefore enforces:
- every division entry is a key of `limits`;
- every key of `limits` appears in exactly one division list;
- each `minimum` or `maximum` limit is `value_kind: number` with a unit (the validator already requires this);
- a `text` value has no unit (the schema forbids it).

The validator does not check these links. They are a tool rule, stated here so that the reviewers can see it.

Division (two-layer example): `kicad_dru` = trace, space, annular, drill, mask web; `project_settings` = copper layers, copper weight, nominal thickness, substrate; `geometric_tests` = slot, edge keepout, board size, max drill; `manual_evidence` = margin values, silkscreen, overlapping drills, via construction, order multiple. Process capability is manual evidence with its published value. No CAD measurement is claimed.

Rule artifacts:
- `supplier.kicad_dru`: project rules (copied from the source) followed by the generated supplier rules. Later rules are examined first, so the supplier rules win.
- `supplier-settings.json`: the staged severity mapping, `error` for each supplier rule.

Selectors:
- `hole_clearance` for the plated-drill clearance to internal copper (other-net copper only; same-net connections pass).
- `inner` layer selector for internal copper.
- `physical_hole_clearance` is not used where a same-net connection must pass.

## 5. Live-source review and the qualification gate

The live review record is required on every release, including when the live bytes equal the stored bytes. Stored bytes alone do not satisfy review.

`fab/supplier-review.json` (record `pcb-fab-package/source-review`, version `1`):

| Field | Content |
|---|---|
| `profile_sha256` | canonical hash of the profile |
| `evidence_sha256` | the stored page hash |
| `live_sha256` | SHA-256 of the page bytes fetched for this review |
| `retrieved` | date of the live fetch |
| `decision` | `unchanged` (live equals stored), `harmless` (changed; every checked limit re-read and equal), `material` (changed or a checked limit differs) |
| `checked_limits` | the keys re-read on the live page (non-empty) |
| `reviewer`, `statement` | non-empty strings |

Qualification gate (`fab.py package`). A package is `qualified` only if all hold:
1. `validate.py --package` reports no finding.
2. Every required check passes with valid evidence, including `fab.supplier_rules` and the `design.*` and `fab.*` checks.
3. `fab.profile_evidence` matches the stored page hash.
4. A current source-review record exists whose `live_sha256` is the current live bytes, and whose decision is `unchanged` or `harmless`.
5. No check is reported as pass without evidence. An unsupported check stays `pending` with a reason.

## 6. Open decisions for the reviewers

1. Mandatory check: `fab.supplier_rules` in `BARE_CHECKS`. Without it a package can qualify without supplier inspection. The cost is the validator change and the B234 builder update (section 1).
2. Slot condition. The official page says only "Minimum Slot Size 20mil (drill slot only)". It does not state a width or length condition. The proposal therefore does not invent one. Decision: the supplier rule applies `hole_size` minimum 20 mil to the minor dimension of drilled slots, which is an interpretation, and it is recorded as a decision, not a page fact. The reviewers may choose another reading.
3. Blind, buried and filled-and-plated via-in-pad are not supported by the supplier. They are refused by the supplier rule. The geometry itself can exist on a four- or six-layer board (correction note `b6-record-correction-claude.md`).
4. Single-layer profile: the two-layer limits with the single-layer page as evidence (page statement).

## 7. Acceptance matrix

| # | Case | Expected |
|---|---|---|
| 1 | `fab.py profile` on the two-layer example | pass |
| 2 | `fab.py profile` with a division key that names no limit | fail (exit 1) |
| 3 | A limit with `kind: minimum` and `value_kind: text` | fail (exit 1) |
| 4 | Two-layer trace, space, annular, drill at below / at / above values | below fails; at and above pass |
| 5 | Four- and six-layer internal clearance: same-net 0 mil passes; unconnected 9.9 mil fails, 10 mil passes | as stated |
| 6 | Slot minor dimension 19.9 / 20 / 20.1 mil | per decision 2 |
| 7 | Drill above 250 mil | passes; no maximum failure |
| 8 | Weaker matching project rule and project `ignore` severity and a source exclusion | supplier result still fails the below-limit geometry; source files unchanged |
| 9 | Source PCB, source `.kicad_dru`, source `.kicad_pro` hashes before and after `supplier` | equal |
| 10 | Package without `fab.supplier_rules` | unqualified |
| 11 | Source review absent, live bytes equal stored bytes | unqualified (review is required) |
| 12 | Source review `unchanged`, live equal | qualified (other gates pass) |
| 13 | Source review `material` | unqualified |
| 14 | Source review `harmless` with all checked limits re-read | qualified |
| 15 | Four-layer export with the published `.GTL/.G2L/.G3L/.GBL` names | layer content checks pass; no X2 path added |

Rows 4–8 and 15 need a fixed-image KiCad run. This paper does not run them.

## 8. Limits

- Paper proposal. No KiCad custom rule, no container run and no validator change has been made.
- The `kicad-cli` commands for the schematic PDF and the fabrication drawing are not measured. They are listed as required outputs and must be measured before package support.
- Qualification proves that the recorded checks passed on the recorded bytes. It does not prove that the supplier accepts the board.
