# Current-state inventory review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: `docs/reviews/current-state-inventory-claude.md` against the
accepted r8 rows, the current product tests and the retained logs. I changed no product file.
I reran no accepted suite and reopened no accepted geometry or publication decision.
I coordinated with codex after its alias review.

## Hash and evidence boundary

- The inventory cites `test_pcb_fab_package-residual.log` (101/101),
  `workflow-run-residual.log` (132/132) and the retrieval alias log (56/56).
- The current test files are `tests/test_pcb_fab_package.py` and
  `tests/test_pcb_fab_workflow.py`.
- Codex has recorded its alias verdict in
  `docs/reviews/source-retrieval-alias-freeze-review-codex.md` (accepted). The inventory
  section 2 status is stale.

## Incorrect classifications

1. **Row 14 is covered, not partial.** The `mask` helper defaults to `limit="4"`. The tests
   `mask("m39")`, `mask("m40")`, `mask("m41")` and `mask("m39merge")` use the 4 mil limit,
   with 3.9/4.0/4.1 webs and the region output. Row 14 is C. Remove it from the gap list.
2. **Row 6 wording is too broad.** `min_space` is tested for pass in
   `supplier rows give pass for every KiCad rule`. `min_annular_ring` is not in that check
   line. The gap is: `min_space` boundary tests, and `min_annular_ring` positive and boundary
   tests.
3. **Row 3 is narrower.** The maximum-kind refusal uses the same `check_profile` branch as
   the tested minimum-kind refusal: `if limit["kind"] in ("minimum", "maximum")`. The genuine
   untested branch is `unit on text`. A maximum-kind test is optional.
4. **Row 41 is wrong for B7.** Accepted r8 says the B6 worker refuses an oval drilled pad with
   exit 2, and the B7 derivative reports it as a slot. The B7 case is a positive test that
   `board_inventory_slots.py` reports the oval or obround pad as a slot with minor and major
   dimensions and the pad attribute. It is not a B7 refusal. The inventory asks for the wrong
   behavior.
5. **Row 45 wording.** Accepted r8 permits the S-expression parser or pcbnew. The worker
   `board_inventory_slots.py` imports pcbnew. So the source is permitted. The remaining item is
   a test that the drawing facts come from pcbnew or the S-expression parser, not a regex
   extractor. The inventory's `facts match the inventory` test is acceptable because the
   inventory is pcbnew-sourced.
6. **Row 29 is a supplier failure with exit 1.** The B7 supplier must implement the
   via-construction check (blind, buried, filled-and-plated via-in-pad) and return exit 1 on
   failure. The B6 worker refusal is exit 2 (unsupported measurement), a different path. The
   inventory conflates the two.
7. **Rows 23 and 24 are genuine gaps.** Both need internal-copper fixtures on the existing
   four- or six-layer profiles. Do not substitute a two-layer not-applicable decision.

## Later evidence that closes or narrows a case

- Row 15a: covered by `test_row_15a`.
- Row 14: covered by the mask tests.
- Row 6: `min_space` positive coverage exists.
- Row 45: the pcbnew worker already supplies the permitted source.

## Compact corrected gap list

Genuine remaining acceptance cases, in r8 order:

1. Row 3: unit-on-text profile refusal. Optional: a maximum-kind refusal.
2. Row 6: `min_space` boundary tests; `min_annular_ring` positive and boundary tests.
3. Rows 7a/7b: board width and height limit runs.
4. Row 8: slot 20.0 and 20.1 mil through an export comparison.
5. Row 13: mask clear polarity and stroke.
6. Row 13c: a different macro name.
7. Row 16: a package with `fab.supplier_rules` removed by name.
8. Row 22: a missing schematic PDF or drawing.
9. Row 23: four/six-layer internal copper, same net at 0 mil, passes through `hole_clearance`.
10. Row 24: four/six-layer unconnected internal copper at 9.9/10/10.1 mil gives fail, pass,
    pass.
11. Row 25: edge keepout at 14.9/15/15.1 mil (judge and board).
12. Row 26: short-text silk at 2.9/3/3.1 mil (judge and board).
13. Row 28: outline and cutout corner radii.
14. Row 29: implement the supplier via-construction check. Blind, buried and filled-and-plated
    via-in-pad give exit 1. Keep the B6 worker exit 2 separate.
15. Row 31: the 250 mil drill process note (a 250 mil drill passes and no maximum applies).
16. Row 32: order quantities 1, 2, 3 and 4.
17. Row 36: a changed stored page file hash through a separate path.
18. Row 41: the B7 derivative reports an oval or obround drilled pad as a slot. The B6 refusal
    (exit 2) is the B6 side.
19. Row 44: a layer PDF in the drawing slot.
20. Row 45: a test that the drawing facts come from pcbnew or the S-expression parser, not a
    regex extractor.
21. Standalone installation outside the repository. The lead closes this after the alias and
    normalization reviews.

Corrected count: C 27, J 5, P 8, G 11. Row 14 moves from P to C. Rows 41 and 45 stay gaps but
with the corrected expected behavior and source rule. Rows 23 and 24 stay gaps.

## Coordination

Codex accepted the alias freeze and repeated the inventory's gap list. I sent codex the row 14
correction and the root corrections for rows 41, 45, 29 and 23/24. The compact list above is
the corrected shared list.

## Verdict

The inventory is a sound base. Apply the corrections above. No product edit. No suite rerun.