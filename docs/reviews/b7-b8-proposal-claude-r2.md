# B7/B8 proposal, revision 2 (claude-skill-dev)

Date: 2026-11-14. Status: paper proposal for review. No implementation starts before B6 acceptance and B7/B8 design agreement. B6 revision 3 stays frozen (`b6-final-files.sha256`). Revision 1 (`b7-b8-proposal-claude.md`) is kept unchanged.

Sources: `/tmp/cad-skills-supplier-evidence/` (five OSH Park pages and headers; SHA-256 values in `b7-b8-preparation-pi.md`), `b7-rule-research-*.md`, `b7-b8-preparation-*.md`, `contracts/validate.py`, `contracts/schemas/`.

## 1. Files and copies

| Path | Kind | Change |
|---|---|---|
| `contracts/validate.py` | source contract | Add `fab.supplier_rules` to `BARE_CHECKS` (so `PCBA_CHECKS` inherits it); add `supplier_rules` and `supplier_settings` to `INPUT_ROLES`; add `CHECK_INPUT_ROLES["fab.supplier_rules"]`. |
| `contracts/schemas/manifest.schema.json` | source contract | Add `supplier_rules` and `supplier_settings` to the manifest `role` enum. |
| `contracts/README.md` | source contract | Document the check and the two roles. Keep placeholders (`${PROJECT}`, `${PACKAGE}`). |
| `skills/pcb-design/contracts/*` | skill copy | Byte copy of the three source files above. Test: byte comparison (test added in B6). |
| `skills/pcb-design/supplier/profiles/*.yaml` | skill data | Five profile records (section 3). |
| `skills/pcb-design/supplier/evidence/*.html`, `*.headers` | skill data | The five retrieved pages and headers, byte copies, so the skill runs alone. |
| `skills/pcb-design/scripts/pcb.py` | skill code | New subcommands `supplier`, `review-source`, `package` (section 2). |
| `skills/pcb-design/references/supplier-rules.md` | skill doc | Rules, profile use, exit codes. |
| `tests/test_pcb_design.py`, `tests/test_pcb_tools.py` | repo tests | Acceptance matrix (section 6). `test_pcb_tools.py` must be updated because the B234 package builders lack the new check. |

No new framework. The validator, the schemas and the project lock stay as they are, except for the additions above.

## 2. Commands

All commands use the B6 runtime and lock rules. Inputs are project-relative. Outputs go under `out/`.

| Command | Inputs | Outputs | Exit |
|---|---|---|---|
| `pcb.py supplier --project P --profile PROFILE.yaml` | board, profile, `manufacturing/export.yaml`, lock | `out/supplier/rules/supplier.kicad_dru` (generated rules), `out/supplier/rules/supplier-settings.json` (staged severity mapping), `out/reports/supplier-drc-SHA256.json` (raw KiCad DRC), `out/reports/supplier.binding.json`, `out/reports/supplier.result.json` | 0 pass; 1 violation or source changed; 2 invalid profile, unsupported selector, runtime mismatch; 3 tool failure |
| `pcb.py review-source --project P --profile PROFILE.yaml --live FILE --reviewer NAME --decision unchanged\|harmless\|material` | profile, live page bytes, stored evidence | `manufacturing/supplier-review.json` (skill record) | 0 recorded; 1 decision `material` unresolved; 2 invalid input |
| `pcb.py package --project P --profile PROFILE.yaml --dest out/packages/NAME` | all B6 results, supplier result, source review | a new package directory with `manifest.json`, evidence files, output files | 0 qualified; 1 unqualified (reason in manifest); 2 invalid input or existing destination; 3 tool failure |

`supplier` never refills zones and never writes the source PCB, the source rule file or the source severity settings. It runs on a staged copy, and it checks the source bytes again before publication (the B6 stage-snapshot rule).

## 3. Five-profile limit mapping

Each profile file uses the accepted `supplier-profile` schema. `evidence_sha256` is the SHA-256 of the stored HTML page. `content_sha256` is the canonical hash of the record (`validate.py canonical_hash`). `retrieved` is `2026-11-14`. Units: `mil` for trace, space, annular, drill, edge and mask values; `mm` for thickness and board size; `oz` and text for copper weight.

| Limit key (scope fabrication unless noted) | kind | Single | Two-layer | Two-layer HHDC | Four-layer | Six-layer |
|---|---|---|---|---|---|---|
| `min_trace` | minimum | 6 mil | 6 mil | 6 mil | 5 mil | 5 mil |
| `min_space` | minimum | 6 mil | 6 mil | 6 mil | 5 mil | 5 mil |
| `min_annular_ring` | minimum | 5 mil | 5 mil | 5 mil | 4 mil | 4 mil |
| `min_drill` | minimum | 10 mil | 10 mil | 10 mil | 10 mil | 8 mil |
| `internal_clearance_plated_drill` | minimum (selector `hole_clearance`, `inner`) | n/a | n/a | n/a | 10 mil | 10 mil |
| `finished_thickness` | text/number | 63 mil (1.6 mm) | 1.6 mm | 0.8 mm nominal | 1.6 mm | 1.6 mm |
| `substrate_core` | text (not finished thickness) | two-layer | 175Tg FR4 | 4x 7628 VT-47, 28 mil core | published stackup | published stackup |
| `copper_weight` | text, unit `oz` | 1 oz | 1 oz | 2 oz | 1 oz outer, 0.5 oz inner | 1 oz outer, 0.5 oz inner |
| `edge_keepout` (geometric) | minimum | 15 mil | 15 mil | 15 mil | 15 mil | 15 mil |
| `mask_web` | minimum | 4 mil | 4 mil | 4 mil | 4 mil | 4 mil |
| `silkscreen_hard_minimum` (short lines, text) | minimum | 3 mil | 3 mil | 3 mil | 3 mil | 3 mil |
| `silkscreen_recommended` | recommendation | 5 mil | 5 mil | 5 mil | 5 mil | 5 mil |
| `overlapping_drill_clearance` | recommendation | 5 mil | 5 mil | 5 mil | 5 mil | 5 mil |
| `max_drill` | recommendation, text | none (larger tolerance above 250 mil) | same | same | same | same |
| `board_min` / `board_max` (geometric, mm) | minimum / maximum | 6.35 x 6.35 / 406.4 x 558.8 | same | same | same | same |
| `slot` (geometric) | minimum, **unconfirmed split** | 20 mil | 20 mil | 20 mil | 20 mil | 20 mil |
| `order_quantity` (manual) | text | multiples of three | same | same | same | same |

Notes that the profile must carry:

- The single-layer profile is a two-layer process. Its file set is the two-layer file set.
- The slot value 20 mil is taken from the preparation boundary table. The width and length limits are not separated in the source text. The profile marks them `unconfirmed` until the source is re-read at review, and the slot tests stay open for that reason.
- The four-layer HTML contains hidden historical stackup comments (January and June 2026). They are not recorded as limits.
- Blind, buried and filled-and-plated via-in-pad are not supported by the supplier. The profile records this as manual evidence (`via_construction`, text) and the geometric test refuses such vias. This is a supplier rule. It is not a claim that the four- or six-layer geometry is impossible.
- Process capability (mask alignment, plating, finished tolerance, drill size and position tolerance) is manual evidence, with its published value and unit. No CAD measurement is claimed.

Division of the limits (accepted schema `division` block):

| Division | Content |
|---|---|
| `kicad_dru` | trace, space, annular, drill, `internal_clearance_plated_drill` with `hole_clearance` on `inner` layers, mask web |
| `project_settings` | layer count, stackup, net classes |
| `geometric_tests` | edge keepout, board size, slot width and length, outline and cutout concave corners |
| `manual_evidence` | finish, colour, process capability values, via construction, order quantity |

## 4. Rule artifacts and selectors

- `supplier.kicad_dru`: the generated rule file, with mandatory rules ordered last so that no later weaker rule shadows them (research record).
- `supplier-settings.json`: the staged severity mapping. Each mandatory check uses `error`. No `ignore`. Source exclusions are reported and ignored for the supplier result.
- Selectors: `hole_clearance` for the plated-drill clearance (different-net copper only), `physical_hole_clearance` not used where a same-net connection must pass, `inner` for internal copper, `hole_size` with separate minor and major dimensions for slots.
- Both artifacts are inputs of the `fab.supplier_rules` evidence record (role `supplier_rules` and `supplier_settings`), so their bytes are bound by hash.

## 5. Package, evidence and qualification

Evidence records: the existing `cad-skills/evidence` schema. No new record type.

| Check | Status rule | Input roles | Artifact |
|---|---|---|---|
| `fab.supplier_rules` (new, mandatory) | pass only if the supplier run passed on the current source bytes and the staged files | `board`, `supplier_profile`, `export_settings`, `supplier_rules`, `supplier_settings` | the raw supplier DRC report (role `report`) |
| `design.drc` (unchanged) | normal project DRC | `board` | its own report |
| `fab.profile_evidence` (unchanged) | the stored page hash equals `evidence_sha256` | `supplier_profile` | the stored page (role `evidence`) |

The package holds: the staged rule and settings files as manifest inputs, the raw supplier DRC report as the evidence artifact, and the stored page. Each check's evidence lists its inputs by hash, as the validator requires.

## 6. Live-source review and qualification gate

Live-source review input: `manufacturing/supplier-review.json` (skill record outside the registry, validated by `pcb.py`):

| Field | Content |
|---|---|
| `record`, `version` | `pcb-design/supplier-review`, `1` |
| `profile_sha256` | canonical hash of the profile |
| `evidence_sha256` | the stored page hash |
| `live_sha256` | SHA-256 of the page bytes fetched for the review |
| `retrieved` | date of the live fetch |
| `decision` | `unchanged`, `harmless` (after reading the limits), or `material` |
| `checked_limits` | list of limit keys re-read against the live page |
| `reviewer`, `statement` | non-empty strings |

Qualification gate. A manifest is `qualified` only if all of these hold:

1. `validate.py --package` reports no finding.
2. Every required check passes with valid evidence, including `fab.supplier_rules`. A missing or failed supplier check leaves the package `unqualified`.
3. `fab.profile_evidence` matches the stored page.
4. If `live_sha256` differs from `evidence_sha256`, the review record exists, its decision is `harmless` or resolved, and `checked_limits` covers each material limit.
5. No check is reported as pass without evidence. Unsupported checks stay `pending` or `unconfirmed` with a reason.

Decision on the mandatory check. Make `fab.supplier_rules` mandatory in `BARE_CHECKS`. Reason: otherwise a manifest can be qualified without any supplier inspection, which is the failure this proposal must prevent. Cost: a contract change to the validator, its copy and the B234 test packages (`tests/pcb_support.py` builders, `test_pcb_tools.py`). The reviewers must accept this cost before implementation. The alternative, an optional check, cannot prevent omission and is not proposed.

## 7. Acceptance matrix

| # | Case | Expected |
|---|---|---|
| 1 | Two-layer trace, space, annular, drill, edge, mask web at below / at / above values from the boundary table | below fails, at and above pass (per limit) |
| 2 | Four- and six-layer trace, space, annular, drill, internal clearance at the same values | as above |
| 3 | Plated drill to internal copper, same net, 0 mil | passes (`hole_clearance`) |
| 4 | Unconnected internal copper, 9.9 mil | fails |
| 5 | Unconnected internal copper, 10 mil and 10.1 mil | pass |
| 6 | Slot width and length, separately, 19.9 / 20 / 20.1 mil | per the unconfirmed split; both tests stay open until the source is re-read |
| 7 | Drill above 250 mil | passes; no maximum failure |
| 8 | Blind, buried and filled-and-plated via-in-pad | fail |
| 9 | Weaker matching rule after a mandatory rule | supplier result still fails the below-limit geometry |
| 10 | Project severity `ignore`, applicable source exclusion | supplier result does not pass; source settings unchanged |
| 11 | Order quantity 1, 2, 3, 4 | 1, 2, 4 flagged or fail; 3 passes; no silent increase |
| 12 | Source PCB, source rule file, source severity: hashes before and after `supplier` | equal |
| 13 | Package without `fab.supplier_rules` | unqualified |
| 14 | Live page changed, decision `material`, no resolution | unqualified |
| 15 | Live page changed, decision `harmless`, limits re-read | qualified (other gates pass) |
| 16 | Four-layer export with the published `.GTL/.G2L/.G3L/.GBL` names and X2-off bytes | layer content checks pass; no X2 path is added |

Rows 1–8 and 16 need a fixed-image run with KiCad custom rules. A paper statement alone is not support.

## 8. Limits and open decisions

- Paper proposal. No KiCad custom rule was run here.
- Open for reviewers: (a) the mandatory-check decision in section 6; (b) the slot split, which needs a re-read of the live source; (c) whether the supplier rule file is shipped as a fixed template or generated per profile. The proposal assumes generated per profile.
- Qualification does not prove that the supplier accepts a board. It proves that the recorded checks passed on the recorded bytes.
