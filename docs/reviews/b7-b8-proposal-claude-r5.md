# B7/B8 proposal, revision 5: consolidated `pcb-fab-package` (claude-skill-dev)

Date: 2026-11-14. Status: paper for review. Consolidates revision 4 (`b7-b8-proposal-claude-r4.md`), its addendum (`b7-b8-r4-addendum-claude.md`), the slot export inspection requirement, and the mask geometry note (`b7-mask-research-root.md`). No implementation starts before explicit reviewer agreement to this interface. B6 stays frozen under `b6-replacement-files.sha256`.

Revisions 3 and 4 are unchanged. The corrections from the design reviews are in section 9.

## 1. Scope

`skills/pcb-fab-package/` is independent of `skills/pcb-design/`. It owns the supplier-specific checks, the slot inspection and the mask inspection, and the package. It has no runtime file reference outside its own directory. B6 keeps its measured subset: circular drills only, no slot support.

## 2. Files (standalone)

| Path | Origin |
|---|---|
| `scripts/fab.py` | new CLI (section 3) |
| `scripts/inspect_slots.py` | new: Excellon slot records and pcbnew slot geometry (section 5) |
| `scripts/inspect_mask.py` | new: exported mask geometry (section 6) |
| `scripts/export_inspect.py` | byte copy of the B6 export checks used by `design` |
| `scripts/board_inventory.py` | the B6 worker, byte copy, plus the owned slot-capable derivative `board_inventory_slots.py` (B6 worker unchanged) |
| `scripts/validate.py`, `scripts/project_io.py`, `contracts/schemas/*.json`, `contracts/registry.json`, `contracts/README.md` | byte copies of `contracts/` |
| `runtime/Containerfile`, `runtime/BUILD.md` | byte copy of the B6 recipe |
| `supplier/profiles/*.yaml` | five profiles (r4 section 4) |
| `supplier/pages/*`, `supplier/rules/*.kicad_dru.in` | byte copies of the retained pages; rule templates |
| `SKILL.md`, `references/*.md` | new |

## 3. CLI (unchanged from r4, with the additions)

`fab.py profile`, `design`, `supplier`, `review-source`, `package` keep the r4 commands, inputs, outputs and exits. Two additional inspections are run by `supplier`:

| Inspection | Command | Output | Exit |
|---|---|---|---|
| Slot export | `fab.py inspect-slots --project P` | `out/fab/reports/slots.json` (per slot: endpoints, orientation, width, source object, export records) | 0 pass; 1 mismatch; 2 invalid; 3 tool failure |
| Mask geometry | `fab.py inspect-mask --project P --profile FILE` | `out/fab/reports/mask.json` (openings, webs, merged openings, tolerance, raster parameters) | 0 pass; 1 violation; 2 invalid; 3 tool failure |

Path policy as r4: every write under `out/fab/`; packages published by `project_io.publish_dir`.

## 4. Slot export inspection

B6 refuses slots, and its Excellon parser reads only `T`, `X` and `Y` records. A slot needs its own inspection.

Method:
1. From the saved board (`pcbnew`, in the container), list each drilled slot: centre, length, width, rotation, and its two endpoints in board coordinates. Use the same Y convention as B6 (the exported Y is the negative of board Y).
2. From the exported drill file, parse the `G85` slot records (`X..Y..G85X..Y..`) and the tool diameter of the slot's `T` record.
3. Compare, for each slot: the set of exported endpoint pairs against the board endpoints (within 0.5 mil, the drill decimals), the tool width against the minor dimension, and the orientation angle derived from the endpoints against the board rotation.
4. Any slot in the board without a matching record, or any exported record without a board slot, is a mismatch (exit 1).

Minimum slot condition (`min_slot_size`, 20 mil): applied to the minor dimension of each drilled slot. This is the declared interpretation (r4 section 4.1). The width and length split is not stated by the supplier page.

Acceptance rows: slot minor width 19.9, 20 and 20.1 mil (fails, passes, passes); endpoint and orientation match for a slot at 0, 45 and 90 degrees; a slot record with an endpoint 1 mil off is a mismatch; a board slot with no export record is a mismatch.

Fixture: a slot-capable derivative of the template board (one oval drill, the derivative is owned by this skill and recorded by its own hash). The B6 slot fixture (`tests/fixtures/pcb-design/slot.kicad_pcb`) tests only the B6 refusal.

## 5. Mask geometry inspection

The saved mask-web setting is a parameter. It does not establish the exported geometry. KiCad merges openings closer than the web setting during export (lead research note), and pad-level expansion overrides can change the openings. The inspection therefore measures the exported mask.

Method:
1. Export the mask layers (`F.Mask`, `B.Mask`) with the B6 export commands (`kicad-cli pcb export gerbers` with the contract settings).
2. Parse the exported mask Gerber: flashes (`D03`) with their apertures, and regions (`G36`/`G37`). Rasterize the openings onto a grid of 0.25 mil cells.
3. Compute the material between openings: a distance transform over the grid. A narrow remaining web is a band of mask material between two openings, measured as its minimum width.
4. Separate two cases. A narrow web (two openings with mask material of width below the limit between them) is a web failure. A merged opening (two pads that the exporter fused into one opening, so no web exists) is a distinct condition, reported as `merged_opening` with its object pair. A removed pre-export gap is not reported as a manufacturing failure. The gap is a design input, not a manufacturing fact.
5. Record any separate assembly concern (for example solder bridging risk) as its own condition with method `manual_evidence`. It is not inferred from the mask geometry.

Tolerance: the raster cell (0.25 mil) plus one cell for the boundary. The minimum web of 4 mil is tested at 3.9, 4.0 and 4.1 mil.

Fixtures (below, at, above): narrow web at 3.9, 4.0 and 4.1 mil between two pads (exported geometry); merged opening where two pads with 2 mil pre-export gap are fused into one opening (reported as `merged_opening`, not as a web failure); a pad expansion override that changes the opening (exported geometry used, not the setting).

Parameter-only checks are not sufficient for the geometric claim. The setting may appear in the record as evidence of the parameter only.

## 6. Supplier result and qualification

Unchanged from r4 sections 6.1 to 6.3, with two additions: the slot minor-width condition is a `geometric_test` row fed by `inspect-slots`, and the mask-web condition is a `geometric_test` row fed by `inspect-mask`. A `merged_opening` finding is not a failure row. It is reported with its own row (`mask_merged_opening`, status `pass` when none exists, `fail` only when a supplier rule requires separate openings).

## 7. Exact roles and mandatory evidence

Required inputs of `fab.supplier_rules` (bound by hash in its evidence record): `board`, `supplier_profile`, `export_settings`, `supplier_rules`, `supplier_settings`, `toolchain`, and the effective staged `board.kicad_dru` and `board.kicad_pro`.

Required outputs of a bare-board package: copper, mask, silk, paste when enabled, outline, `drill_plated`, `drill_nonplated`, `report` (raw supplier DRC, slot and mask inspections, supplier result), `evidence`. The schematic PDF and the fabrication drawing remain unsupported until measured; a package that needs them is unqualified (exit 1).

The source review (`REVIEW.json`, r4 section 6.2) is mandatory qualification evidence. It is bound to the release ID, the profile and each page. A missing review or a missing observation blocks qualification. Changed-page meaning stays manual evidence. No HTML parser.

## 8. Acceptance matrix (additions to r4 section 9)

| # | Case | Expected |
|---|---|---|
| 21 | Slot minor width 19.9 / 20 / 20.1 mil | fails / passes / passes |
| 22 | Slot endpoints and orientation at 0, 45, 90 degrees matching | pass |
| 23 | Slot endpoint 1 mil off in the export | mismatch (exit 1) |
| 24 | Board slot with no export record, or export record with no board slot | mismatch (exit 1) |
| 25 | Narrow exported web 3.9 / 4.0 / 4.1 mil between two pads | 3.9 fails; 4.0 and 4.1 pass |
| 26 | Two pads with 2 mil pre-export gap, fused by export | `merged_opening` reported; no web failure; no manufacturing failure |
| 27 | Pad expansion override changes the opening | exported geometry decides, not the setting |
| 28 | Mask-web setting saved as 4 mil with exported web 3.9 mil | fails (the export decides) |
| 29 | Separate assembly concern | reported as manual evidence, not inferred from mask geometry |

Rows 4–8, 19, 21–28 need a fixed-image run with KiCad export and the owned derivative. This paper alone supports nothing.

## 9. Corrections incorporated from the reviews

- Staged files are the basename `board` and the effective `.kicad_pro`/`.kicad_dru` bytes (r4 section 5).
- Nominal and process metadata in `extensions` with named fields; requirements are requirements (r4 section 4).
- Complete coverage through the supplier result, not the raw DRC report (r4 section 6.1).
- Source review bound to release, profile and pages; observations are complete structured values; no HTML parser (r4 section 6.2).
- Path policy and exits (r4 section 3).
- Standalone files, including the export inspection and the worker (section 2).
- Slot export inspection and mask geometry inspection are added (sections 4 and 5).

## 10. Open decisions

1. KiCad `.kicad_pro` field names for rule severities and the solder-mask web setting: fixture proof before implementation.
2. Raster method and tolerance for mask geometry (section 5): reviewers to agree the 0.25 mil cell.
3. Schematic PDF and fabrication drawing: measure in a temporary copy of the existing image, or keep unsupported.
4. Slot endpoint tolerance (0.5 mil) and the orientation tolerance (degrees): to be agreed.

## 11. Limits

Paper only. No KiCad export, no inspection code and no container run was performed for r5. The derivative inspection and the mask inspection are not implemented. B6 stays frozen and makes no slot or mask-geometry claim.
