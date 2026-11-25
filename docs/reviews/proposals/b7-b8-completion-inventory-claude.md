# B7/B8 completion inventory (claude-skill-dev)

Date: 2026-11-15 UTC. Checked against `docs/reviews/b7-b8-design-acceptance-root.md` and `docs/reviews/b7-publication-acceptance-root.md`. Status is from the repository and the retained logs, not from memory.

| # | Accepted item | Evidence in repository | Status |
|---|---|---|---|
| 1 | Independent `pcb-fab-package` skill | `skills/pcb-fab-package/` with its own scripts, contracts copy, supplier copy | Implemented |
| 2 | Shared-contract additions and skill copies | `contracts/schemas/manifest.schema.json` and the skill copy are identical (one file checked in this inventory; the others are not re-hashed here) | Implemented, spot-checked |
| 3 | Slot tolerance 0.000501 mm pass and 0.000502 mm refusal | `tests/test_pcb_fab_package.py` (names 0.000501 and 0.000502) | Tested; passed in the retained package run (101 of 101) |
| 4 | Mask macro refusal, overlap refusal, measured `RoundRect` | `tests/test_pcb_fab_package.py` (RoundRect, unknown macro, overlap) | Tested; passed in the retained run |
| 5 | Manual geometry evidence with artifact and current input hashes | `workflow.py` `check_manual` and `staged_problems`; workflow tests `test_design_supplier_package`, `test_manual_original`, `test_binding_and_lock` | Tested; passed in the retained workflow run (132 of 132) |
| 6 | Fabrication drawing content and rendered example | `tests/test_pcb_fab_package.py` (drawing, render) | Tested; passed in the retained run |
| 7 | Publication correction (complete paths, captured bytes, supplier result, final gate) | Freezes `b7-final-publication-repair-claude.md` and `b7-residual-publication-repair-claude.md`; acceptance `b7-publication-acceptance-root.md` | Accepted by the lead |
| 8 | Complete executable trial commands with explicit paths | Each freeze lists the suite commands. A single trial command table for B7/B8 is not in one record | Open |
| 9 | Implementation acceptance by both reviewers | Not yet requested for the residual freeze | Open |
| 10 | Source retrieval interface | `docs/reviews/proposals/source-retrieval-interface-claude.md` (proposal) | Proposed, not implemented |
| 11 | Setup documentation review and corrections | Installed reference frozen in `b7-doc-setup-freeze-claude.md`; corrected text in `oshpark-kicad-setup-corrected-claude.md` | Corrections proposed; reviews pending |
| 12 | Stale command-status prose in `pcb-fab-package/SKILL.md` | Final documentation pass | Open, after the doc reviews |
| 13 | Release provenance and distribution tests | Owned by release (`tests/test_release_packaging.py`) | Release-owned |

## Open items before B7/B8 completion

1. Item 8: write the single executable trial command table with explicit paths.
2. Item 9: request both reviewers for the residual implementation freeze.
3. Item 10: implement the retrieval interface after the frozen review.
4. Item 11: finish both documentation reviews, then install the corrected reference.
5. Item 12: correct the stale SKILL.md command prose in the final documentation pass.

## Limits

This inventory does not run any suite. Tested items are supported by the retained logs listed in the freezes. Standalone release acceptance is not part of this inventory.
