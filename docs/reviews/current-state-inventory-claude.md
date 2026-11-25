# Current-state inventory and r8 row mapping (claude-skill-dev)

Date: 2026-11-15 UTC. Author: claude-skill-dev (model claude-haiku-5-5). Status: draft for lead review.

This report corrects `completion-inventory-claude.md`. It makes no code change and reruns no accepted check. It repairs no historical trial prototype. No provider call was made. No commit was made.

Evidence used is the retained logs in `b7-workflow-evidence/`:

- `test_pcb_fab_package-residual.log`: 101 of 101 passed.
- `workflow-run-residual.log`: 132 of 132 passed, exit 0.
- Retrieval: `source-retrieval-alias-evidence/retrieval-alias-run3.log` (in `docs/reviews/`), 56 of 56 passed, exit 0.

A row is covered only when a named log line exercises it. "Judge" means a function-level test of the limit or decision. It is not a board-level test.

## 1. Exact remaining product acceptance gaps

These gaps block full B7/B8 acceptance. They are listed first, by row.

| Row | Gap | Test needed |
|---|---|---|
| 6 | Space and annular ring are not tested. Trace and drill are only partly tested. | Board fixtures for space and annular ring, at the limit and beyond it. |
| 7a, 7b | Width and height maxima are judge-only. No board run. | Board fixtures at 406.3/406.4/406.5 mm width and 558.7/558.8/558.9 mm height. |
| 8 | Slot width at 20.0 and 20.1 mil is not compared through an export. Only 19.9 is. | Export comparison at 20.0 and 20.1 mil. |
| 3 | Maximum and unit-on-text refusals are not tested. Only the minimum-kind refusal is. | Profile refusals for maximum kind and unit on text. |
| 13 | Clear polarity and stroke are not tested. | Gerber fixtures with clear polarity and stroke, each refused or measured as the rule states. |
| 13c | A different macro name is not tested. Only a changed RoundRect definition is. | Gerber fixture with another macro name, refused with exit 2. |
| 14 | The 4 mil minimum-web setting is not tested in the current suite. The region refusal is. | Fixture with the 4 mil setting and region output. |
| 16 | No test removes `fab.supplier_rules` from a package and checks the refusal. | Package test with the rule row removed by name. |
| 22 | No refusal test for a missing schematic PDF or drawing. | Package test with the schematic and drawing removed. |
| 23 | Plated drill to internal copper, same net. Not tested. Applies only to profiles with internal copper. | Four-layer or six-layer profile test, or a written not-applicable decision for the two-layer profile. |
| 24 | Plated drill to unconnected copper at 9.9, 10, and 10.1 mil. Not tested. | Board fixtures at the three values. |
| 25 | Edge keepout at 14.9, 15, and 15.1 mil. Only the fail case is tested. | Judge and board tests at the three values. |
| 26 | Short-text silk at 2.9, 3, and 3.1 mil. Not tested. | Judge and board tests at the three values. |
| 28 | Outline and cutout corner radii. Not tested. | Board fixture with a corner radius, measured and refused where required. |
| 29 | Via construction refusal. Not tested in the B7 suite. The B6 worker refuses blind vias, but B7 has no test of that path. | Fixture with a blind or buried via, refused with exit 2. |
| 31 | Drill above 250 mil must not be a maximum. Not tested. | Process-note test: a 250 mil drill passes, and a larger drill is not refused by a maximum. |
| 32 | Order quantities 1, 2, and 4 are not tested. Only quantity 5 is refused. | Workflow tests for quantities 1, 2, 3, and 4. |
| 41 | Oval drilled pad in the worker. Not tested. | Worker fixture with an oval drilled pad, refused with exit 2. |
| 44 | Layer PDF used as the drawing. No refusal test. | Package test with a layer PDF in the drawing slot, refused. |
| 45 | No test that drawing facts come from the worker inventory and not from a text parser. | Test that the drawing facts file matches the inventory. |
| 36 | Stored page hash change through a separate path. Only the live page and profile tests exist. | Package test with a changed stored page hash. |
| Standalone | Standalone installation is not tested. The skill directory has byte copies. No run-time reference to another skill was tested. | Install the skill outside the repository and run its suite. Lead will close this after the alias and normalization reviews. |

The gap list is complete for the r8 rows. A row not named here is covered by a current test (section 3).

## 2. Retrieval compatibility: current status

This section corrects the earlier inventory.

| Item | Current state | Evidence |
|---|---|---|
| Compatibility decision | Accepted by the lead. It sets the release manifest format. | `source-retrieval-compatibility-root.md` |
| Proposal revision `b2cdf367` | Codex v2 found a blocker: the profile confinement boundary was not explicit. | `source-retrieval-compatibility-review-codex-v2.md` |
| Proposal revision `faa31c20` | Pi held on the link rule (no explicit symlink mechanism). The defect was resolved in the implementation freeze. | `source-retrieval-implementation-review-pi.md` |
| Codex verdict on `faa31c20` | None is recorded. Codex's implementation review confirms the link corrections, and its blocker (manifest and profile alias) was closed by the alias freeze. | `source-retrieval-implementation-review-codex.md`, `source-retrieval-input-alias-probe-codex.json` |
| Implementation freeze `386106ca…` | Accepted by Pi (48 of 48). Superseded for the alias defect. | `source-retrieval-implementation-freeze-review-pi.md` |
| Alias freeze `35e21d37…` (fetch_sources.py) and `1d61a5a2…` (tests) | Accepted by Pi (56 of 56). Codex verdict not yet recorded. Two minor points from Pi: test 50 is caught by the `..` shape check, and a directory destination fails later with exit 3. | `source-retrieval-alias-freeze-review-pi.md`, `source-retrieval-alias-freeze-claude.md` |
| Manifest normalization | Pi accepted the normalized manifest. Codex review pending. The hash `fd415dc5…` is not verified in this session. Not installed. | Lead message, `source-retrieval-alias-release-root.md` |
| Standalone retrieval tests | Not yet run outside the repository. | Section 1 |

Corrected status: the compatibility decision is accepted. The implementation and alias freezes are accepted by Pi. Codex has not recorded a verdict on the alias freeze or on revision `faa31c20`. The normalization is pending Codex.

## 3. r8 acceptance rows mapped to current tests

Key: **C** covered by a current named check. **J** judge-level only. **P** partial. **G** gap (section 1).

| Row | Status | Current evidence (log line or test) |
|---|---|---|
| 1 | C | `five profiles validate` (package) |
| 2 | C | `profile refused: unknown division key`, `profile refused: duplicate division key` (package) |
| 3 | P | `profile refused: text value with minimum kind` (package). Maximum and unit not tested. |
| 4 | J | `max width 406.3/406.4/406.5`, `max height 558.7/558.8/558.9` (package, judge) |
| 5 | J | `min board edge 6.34/6.35/6.36 mm`, `min slot 19.9/20/20.1 mil` (package, judge) |
| 6 | P | `generated rule uses the exact trace minimum 0.1524 mm` (workflow). Space and annular ring: G. |
| 7a, 7b | J | Width and height judge lines above. Board run: G. |
| 8 | P | `min slot 19.9/20/20.1 mil` (judge); `minor width 19.9 mil (0.5054 mm) against 20 mil export is a mismatch` (package). 20.0 and 20.1 through export: G. |
| 9 | C | `slot exact match passes`, `0.000501 mm ... passes (boundary)`, `0.000502 mm ... is a mismatch`, `slot endpoints in reversed order match`, `duplicate export record ... mismatch`, `duplicate board slot needs two export records`, `class swap ... mismatch`, `missing export record is a mismatch` (package) |
| 10 | C | `mask 3.9 mil fixture fails (exit 1)`, `mask 4.0 mil fixture is uncertain (exit 1)`, `mask 4.1 mil fixture passes (exit 0)` (package) |
| 11 | C | `mask at the limit is uncertain`, `mask 4.0 mil fixture is uncertain` (package) |
| 12 | C | `rectangles touching on an edge are merged_opening, not a web (exit 0)` (package) |
| 13 | P | `region output refused for automatic inspection (exit 2)`, `a RoundRect macro with a changed primitive is refused (exit 2)`. Clear polarity and stroke: G. |
| 13a | C | `unknown macro or obround aperture refused (exit 2)` (package) |
| 13b | C | `two 2 mm rectangles overlapping by 1 mm are refused (exit 2)`, `coincident rectangles are refused (exit 2)`, `circle inside a rectangle is refused (exit 2)` (package) |
| 13c | P | `G1: a changed RoundRect definition is refused (exit 2)`, `G1: a macro inline on the units line is refused (exit 2)` (package). Different macro name: G. |
| 14 | P | `region output refused for automatic inspection (exit 2)`. 4 mil setting: G. |
| 14a | C | `round-rect fixture: exact RoundRect web 4.0000 mil`, `round-rect fixture at the limit is uncertain` (package) |
| 15 | C | Covered by the 15a staged-project tests below. |
| 15a | C | `15a ignore: the staged DRC bytes show the target track_width finding active`, `15a exclusion: the staged project clears any exclusion`, `15a exclusion: the source files keep their bytes` (workflow) |
| 16 | P | `rows: a missing mandatory row is refused and does not qualify a package (exit 1)` (workflow). Removal of `fab.supplier_rules` by name: G. |
| 17 | C | `gate rejects a missing review (omission)`, `gate rejects another release` (workflow) |
| 18 | C | `a missing observation gives material`, `a value of the wrong number gives material` (workflow) |
| 19 | C | `a changed live page with equal facts gives harmless`, `review harmless (changed page, equal observations)` (package) |
| 20 | C | `the validator detects a changed output after qualification` (workflow) |
| 21 | C | `profile refused: single-layer with one page bound` (package) |
| 22 | G | No refusal test. |
| 23 | G | No test. |
| 24 | G | No test. |
| 25 | G | Judge and board tests at 14.9/15/15.1 mil are absent. `copper_edge_clearance` path only. |
| 26 | G | No test. |
| 27 | C | `recommendation never fails` (package) |
| 28 | G | No test. |
| 29 | G | No test. |
| 30 | J | `min board edge 6.34/6.35/6.36 mm` (package, judge) |
| 31 | G | No test. |
| 32 | P | `the supplier result stops on a quantity of 5 (exit 1 or 2, not a pass)` (workflow). Quantities 1, 2, 3, 4: G. |
| 33 | C | `gate rejects a missing review (omission)` (workflow) |
| 34 | C | `gate rejects changed review bytes` (workflow) |
| 35 | C | `gate rejects altered observations` (workflow) |
| 36 | P | `gate rejects another profile`, `gate rejects changed profile file bytes`, `wrong stored hash is refused` (workflow). Stored page hash through a separate path: G. |
| 37 | C | `gate rejects a live page that differs from the reviewed hash` (workflow) |
| 38 | C | `class swap: PTH board slot exported only as NPTH is a mismatch` (package) |
| 39 | C | `duplicate board slot needs two export records` (package) |
| 40 | C | `missing export record is a mismatch` (package) |
| 41 | G | No test. |
| 42 | C | `rectangles touching on an edge are merged_opening`, `two 2 mm rectangles overlapping by 1 mm are refused` (package) |
| 43 | C | `drawing shows release identity` ... `drawing renders to PNG` (package, 14 drawing checks) |
| 44 | G | No refusal test. |
| 45 | G | No test. |

Positive and gate checks outside the r8 rows:

- Positive package gate: `package with every condition passing is qualified (exit 0)`, `qualified manifest has no reasons` (workflow). Covered.
- Caller timeout (decision 2): `a stalled mask worker is stopped by the caller timeout (exit 2)`, `an existing report path is refused: no stale success (exit 2)` (package). Covered.
- Workflow mask path regression: `the supplier mask path writes both mask rows (regression for the returncode defect)` (workflow). Covered.
- Confinement and lock: `confinement: a nested output link is refused`, `lock: a held project lock stops the design (exit 2)` (workflow). Covered.

Count: 51 items (rows 1 to 45, plus the sub-rows 7a, 7b, 13a, 13b, 13c, 14a and 15a). Covered C: 26 items (1, 2, 9, 10, 11, 12, 13a, 13b, 14a, 15, 15a, 17, 18, 19, 20, 21, 27, 33, 34, 35, 37, 38, 39, 40, 42, 43). Judge J: 5 items (4, 5, 7a, 7b, 30). Partial P: 9 items (3, 6, 8, 13, 13c, 14, 16, 32, 36). Gap G: 11 items (22, 23, 24, 25, 26, 28, 29, 31, 41, 44, 45). Section 1 names the sub-cases that each partial or gap item still needs.

## 4. Historical trial command table: inferred

The trial command table in `completion-inventory-claude.md` (section 5) is **inferred**. It came from `b7-r8-command-record.md` and `run-exit-codes.log`. Its working directories are partly inferred, and the bind mount for the container is not recorded. The historical `mask-fx/make.py` writes to a scratchpad path from another session. Keep this table labeled inferred. Do not present it as a retained invocation log. The current product evidence for B7 is the suite logs in section 3, not the trial table.

## 5. What remains before full B7/B8 acceptance

1. Codex verdict on the alias freeze, and the normalization review. Then the retrieval status is closed.
2. Standalone installation test, outside the repository (lead will close after step 1).
3. The gaps in section 1, in the order the lead assigns.
4. Rerun the affected suites after new tests are added. Retain their logs with exit codes.

No accepted check is rerun in this report.
