# Implementation sequence for the B7/B8 acceptance gaps (claude-skill-dev)

Date: 2026-11-15 UTC. Author: claude-skill-dev (model claude-haiku-5-5). Status: plan for lead review. No product file was changed for this plan.

Source: `current-state-inventory-claude.md` (section 1 gaps, section 3 row mapping), and the r8 proposal `b7-b8-proposal-claude-r8.md`, rows 3 to 45.

## 1. Constraints

- Do not edit the frozen retrieval files `skills/pcb-fab-package/scripts/fetch_sources.py` and `tests/test_source_retrieval.py` (freeze `35e21d37…`, `1d61a5a2…`) while Codex finishes.
- Keep accepted publication behavior closed. This covers the final gate, `publish_dir`, `project_io` and the staged output checks in `workflow.py`.
- Keep accepted geometry behavior closed. Frozen files are `fab.py` (the `run_mask_worker` guard), `inspect_mask.py`, `macro_defs.py`, `export_inspect.py`, `inspect_slots.py`, `board_inventory_slots.py` and `tests/test_pcb_fab_package.py`.
- New tests go in new files. Proposed name: `tests/test_pcb_fab_acceptance.py`.
- Do not repair the historical trial scripts.
- Do not add a design phase.

## 2. Classes used below

- **A. Absent product behavior.** The product has no code path for the row. A test alone cannot close it.
- **B. Test gap.** The product path exists. Only a named test is missing.
- **C. Decision or conflict.** The row and the product disagree, or the row needs a choice first.

Each class was checked by reading the code. Code references are given. A class B item still needs its test to run before it counts as covered.

## 3. Classification of the gaps

| Row | Class | Finding (code reference) |
|---|---|---|
| 3 | B | Maximum kind and unit-on-text refusals are not tested. Schema kinds exist. Confirm by a refusal test. |
| 6 | B | `min_space` and `min_annular_ring` are generated KiCad rules (`workflow.py` `RULE_CONSTRAINT`, `REPORT_KEYS`). Board fixtures missing. |
| 7a, 7b | B | `board_max_width` and `board_max_height` are checked (`workflow.py`). Board runs missing. |
| 8 | B | Slot width is compared through the export. Only 19.9 mil is tested. |
| 13 | B | `inspect_mask.py` refuses clear polarity (line 115) and strokes (line 18). Fixtures missing. |
| 13c | B | `inspect_mask.py` refuses any macro other than the measured `RoundRect` (lines 14 to 15). Different macro name test missing. |
| 14 | B | Region output is refused (`inspect_mask.py`). The 4 mil setting fixture is missing. |
| 16 | B | `fab.supplier_rules` is a required check (`validate.py` lines 491, 503). No test removes it by name. |
| 22 | B | Package validation requires `schematic_pdf` and `fabrication_drawing` roles (`validate.py` lines 1030 to 1034). No test removes them. |
| 23 | B | Row 23 requires internal copper, so it needs a four-layer or six-layer fixture. The four-layer and six-layer profiles generate `plated_drill_to_internal_copper` (`hole_clearance`). The two-layer profile has no internal copper and is not a closure for this row. All five profiles exist. The four-layer fixture is missing. Root confirmed this reading. |
| 24 | B | Same rule as row 23. Boundary fixtures at 9.9, 10 and 10.1 mil on a four-layer or six-layer board are missing. |
| 25 | B | `edge_keepout` is a generated KiCad rule (`copper_edge_clearance`). Boundary fixtures at 14.9, 15 and 15.1 mil are missing. |
| 26 | C | `silk_line_min_short_text` is a manual evidence condition (profile `division.manual_evidence`). No automatic silk measurement exists. The row expects an automatic fail or pass at 2.9, 3 and 3.1 mil. Decision needed: measure, or test the manual route. |
| 28 | A | No profile limit and no code for outline concave corner radii or cutout corner radii. `min_corner` and `corner_radius` do not appear in any profile or script. Needs a new profile limit (contract change) and an outline measurement. |
| 29 | A (via-in-pad), B (blind and buried), C (exit class) | Row 29 expects a supplier failure with exit 1 (`fail (exit 1)`). Preserve the accepted distinction: exit 1 is a supplier failure, and exit 2 is an unsupported measurement. The B6 worker refuses a via whose span is not through the board with exit 2 (`REFUSED_VIA`, `board_inventory.py` line 73). The derivative `board_inventory_slots.py` (line 102) also refuses it. Row 29 needs the exit 1 supplier failure. The current path gives exit 2. Decision needed. Via-in-pad has no check in any script. Adding it changes a frozen geometry file. |
| 31 | B | No `drill_max` key exists. The row expects no maximum. Test that a 250 mil or larger drill is not refused by a maximum. |
| 32 | B | `service.order_multiple` is a mandatory geometric row (`workflow.py` lines 626 to 628). Quantities 1, 2 and 4 are not tested. |
| 36 | B | `review_gate` compares the profile hash and the live page hash (`fab.py` lines 231 to 236). The stored page hash path is not tested separately. |
| 41 | B | Row 41 expects the B6 worker to refuse an oval or obround drill with exit 2, and the owned B7 derivative to report it. The B6 worker does refuse `slot or oval drill` with exit 2 (`board_inventory.py` line 59). The derivative reports it as a slot with endpoints (`board_inventory_slots.py` lines 88 to 89). Both match row 41. The derivative must keep reporting supported slots. Test both behaviors. Earlier class C was wrong. |
| 44 | A | Package validation checks only that a `fabrication_drawing` role exists. It does not check that the PDF came from the drawing facts. A layer PDF in that role is not refused. A provenance or content check is absent. |
| 45 | B | Row 45 permits the accepted S-expression parser or pcbnew, and forbids a regex object parser. `drawing_facts` takes the inventory from `board_inventory_slots.py` (pcbnew) (`fab.py` line 268). Test that the facts equal the inventory and that no regex object parser is used. |
| Standalone | B | No repository-root paths were found in the skill scripts. Schemas and the validator are byte copies in the skill. The workflow needs the container image `localhost/cad-skills-pcb:b6` (`workflow.py` line 36). The image is outside the skill and must be a documented prerequisite. Standalone test missing. |

Summary: class A has 3 items (28, 44, and the via-in-pad part of 29). Class C has 2 items (26, and the exit class of row 29). Class B has the rest, including rows 23, 24 and 41, which root resolved in favor of tests.

## 4. Sequence

The groups follow the lead's order. Each step ends with a focused run and a retained log. Steps in one group may run in parallel only when they touch different files.

### Group 1. Profile validation

No board is needed.

- **P1 (B).** Add tests in `tests/test_pcb_fab_acceptance.py`: profile refused for maximum kind, and for unit on text. Rows 3.
- **P2 (A, contract).** Add the corner limits (rows 28) only after the lead assigns the contract change to `contracts/schemas/supplier-profile.schema.json` and its copies. This step cannot start before that assignment.
- **P3 (C).** Decide the silk route for row 26: automatic measurement, or manual evidence with boundary tests. Then write the tests for the chosen route.
- **P4 (B).** Test that no `drill_max` key is accepted as a maximum. Row 31 uses this as its negative test.

### Group 2. Board measurements

Each step needs a fixture board and a KiCad run in the container image. Rows 23 and 24 use a four-layer or six-layer fixture. All five profiles exist.

- **M1 (B).** Space and annular ring fixtures at the limit, below it and above it. Row 6.
- **M2 (B).** Width and height maxima through a board run. Rows 7a and 7b.
- **M3 (B).** Slot width at 20.0 and 20.1 mil through the export comparison. Row 8.
- **M4 (B).** Edge keepout at 14.9, 15 and 15.1 mil through a board run. Row 25.
- **M5 (B).** Plated drill to internal copper, same net at 0 mil (row 23), and to unconnected copper at 9.9, 10 and 10.1 mil (row 24). Use a four-layer or six-layer fixture.
- **M6 (B).** Gerber fixtures for clear polarity, stroke and a different macro name. Rows 13 and 13c. These are refusal tests, with exit 2.
- **M7 (B).** 4 mil mask-web setting with a 3.9 mil nominal fixture (row 14). Expect automatic inspection to refuse with exit 2 and manual evidence only.
- **M8 (B).** Blind and buried via refusal through the existing span check (row 29, present part). Test the exit that the decision in section 5 selects.
- **M9 (A).** Via-in-pad check (row 29, absent part). Adding it changes `board_inventory_slots.py`, which is frozen. Lead must choose a new module or authorize a change.
- **M10 (B).** Oval or obround drill (row 41). Test that the B6 worker refuses it with exit 2, and that the B7 derivative reports it while still reporting supported slots.
- **M11 (A).** Outline corner radius measurement (row 28). Needs a new measurement module. Starts after P2.

### Group 3. Package evidence

- **E1 (B).** Package with `fab.supplier_rules` removed by name is refused. Row 16.
- **E2 (B).** Package with the schematic or the drawing removed is refused. Row 22.
- **E3 (A).** A layer PDF in the `fabrication_drawing` role must be refused. Needs a provenance or content check that the lead assigns. Publication code is accepted, so the check goes in a new verifier called before publication, not in the final gate.
- **E4 (B).** Drawing facts equal the board inventory. Row 45.
- **E5 (B).** Stored page hash changed through the separate review path. Row 36.
- **E6 (B).** Quantities 1, 2, 3 and 4 through the supplier path (row 32). Quantities 1 and 2 fail, 3 passes, 4 fails. Needs a design run.

### Group 4. Standalone installation

- **S1 (B).** Copy the skill directory to a path outside the repository. Run its own tests from that copy. The copy must not read any repository file. Use the image `localhost/cad-skills-pcb:b6` by its identity, and record that the image was not pulled.
- **S2 (B).** Record the image prerequisite in `SKILL.md`. Check the command table against the code. This is the stale-prose item from the checkpoint.

## 5. Open questions for the lead

1. Answered by root: rows 23 and 24 need a four-layer or six-layer fixture. Row 41 is covered by the B6 worker refusal and the B7 derivative report.
2. Row 26: automatic silk measurement, or manual evidence only?
3. Row 29 exit class: blind and buried vias are refused with exit 2 today. Row 29 expects a supplier failure with exit 1. Preserve the distinction between a supplier failure (exit 1) and an unsupported measurement (exit 2). Which exit does the row require for each via case?
4. Row 44: which check proves the drawing came from the drawing facts? Options are a provenance hash binding or a content check on the PDF.
5. Corner radii (row 28): contract change to the supplier profile schema, and a new outline measurement module.
6. Via-in-pad (row 29): new module, or an authorized change to the frozen `board_inventory_slots.py`.

Release handoff (checked in this pass): the normalized `sources.yaml` at `/mnt/storage/projects/cad-skills-worktrees/release/skills/pcb-fab-package/sources.yaml` has SHA-256 `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`. Its five `profile_binding` values match the five existing profile files. It is not installed here. Install waits for Codex's acceptance. Release notes that a linked ancestor directory makes each skill binding report D-9. Use a checkout with no linked ancestors.

## 6. What this plan does not do

- It does not repair the historical trial scripts, the inferred command table, or the accepted trial records.
- It does not touch the retrieval freeze.
- It does not change publication or geometry behavior.
- It does not rerun any accepted check.
