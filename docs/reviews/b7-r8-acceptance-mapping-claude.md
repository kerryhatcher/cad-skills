# B7/B8 r8 acceptance mapping (claude-skill-dev)

Date: 2026-11-14 UTC. Maps the r8 acceptance rows (with the r8 errata) to tests or retained records.
Test counts are from this session: geometry `tests/test_pcb_fab_package.py` 98/98; workflow
`tests/test_pcb_fab_workflow.py` 51/51. A count does not map a row by itself; each row names its test.
"Not run" means no product test or retained record establishes that row. It is not a pass.

| Row | Case | Evidence |
|---|---|---|
| 1 | profile validation, five profiles | test: five profiles validate; record run: profile-* exit 0 |
| 2 | unknown or duplicate division key | test: profile refused (unknown, duplicate) |
| 3 | text limit with minimum/maximum, unit on text | test: profile refused (text minimum) |
| 4 | maximum limit at below/at/above | test: boundaries (judge), width and height |
| 5 | minimum limit at below/at/above | test: boundaries (judge), board edge and slot |
| 6 | trace, space, annular ring, drill | partial: judge only; not run through a board |
| 7a/7b | board width and height maxima | test: boundaries (judge); not run through a board |
| 8 | slot minor 19.9/20/20.1 mil | partial: judge only; slot width comparison not run at these values |
| 9 | slot endpoints, reversed, 0.000501/0.000502 mm, duplicate, class swap, missing | tests: slot exact, boundary 501/502, reversed, duplicate board and export, class swap, missing |
| 10 | mask web 3.9/4.0/4.1 | test: mask fixtures; record: mask-m39/m40/m41 exits 1/1/0 |
| 11 | web within bound is uncertain | test: mask 4.0 uncertain; judge uncertain |
| 12 | merged opening | test: rectangle edge contact is merged_opening |
| 13 | clear polarity, region, stroke, other macro | partial: region and changed macro tested; clear polarity and stroke not run |
| 13a | oval aperture refused | test: unknown macro or obround refused; record: mask-oval exit 2 |
| 13b | overlapping flashes refused | test: overlapping cluster refused; interior rectangle overlap refused |
| 13c | unknown macro name | partial: changed RoundRect definition refused; a different macro name not run |
| 14 | 4 mil minimum-web setting, region output | record: mask-m39merge exit 2; test: region refused |
| 14a | RoundRect at 4.0 mil nominal | test: round-rect fixture 4.0000 mil uncertain |
| 15 | staged exclusion restoration | retained record: stage-proof (source 7 active and 1 excluded, staged 8 active); not a product test |
| 15a | project ignore severity and source exclusion, staged rule fails | NOT RUN as a product test. The staged copy was measured in the trial record only. |
| 16 | package without fab.supplier_rules | NOT RUN. The validator requires the check; no test removes it. |
| 17 | source review absent or another release | test: gate omission, gate another release |
| 18 | changed page with missing or material observation | test: material (missing observation, different value) |
| 19 | changed page, complete and equal | test: harmless |
| 20 | output changed after qualification | test: validator detects a changed output |
| 21 | single-layer with one page bound | test: profile refused (one page) |
| 22 | schematic PDF or drawing missing | NOT RUN |
| 23 | plated drill to internal copper, same net | NOT RUN (two-layer profile has no such limit) |
| 24 | plated drill to unconnected copper 9.9/10/10.1 mil | NOT RUN |
| 25 | edge keepout 14.9/15/15.1 mil | NOT RUN through a board (judge only) |
| 26 | short-text silk 2.9/3/3.1 mil | NOT RUN through a board (judge only) |
| 27 | recommendations never fail | test: recommendation never fails; supplier rows give finding |
| 28 | outline and cutout corner radii | NOT RUN |
| 29 | via construction refused | NOT RUN |
| 30 | board minimum edge 6.34/6.35/6.36 mm | test: boundaries (judge); supplier row in workflow run |
| 31 | drill above 250 mil, no maximum | NOT RUN |
| 32 | order quantity 1, 2, 3, 4 | test: workflow quantity 5 fails the order-multiple row (negative test) |
| 33 | REVIEW.json missing | test: gate omission |
| 34 | REVIEW.json bytes changed | test: gate changed bytes; workflow changed review record refused |
| 35 | observation altered | test: gate altered observations |
| 36 | release, profile or stored page hash changed | partial: release and profile tested; stored page hash change not run |
| 37 | live page differs from reviewed hash | test: gate live page changed |
| 38 | PTH slot exported only as NPTH | test: class swap |
| 39 | duplicate board slot | test: duplicate board slot needs two export records |
| 40 | board slot with no export record | test: missing export record |
| 41 | oval drilled pad in the worker | NOT RUN |
| 42 | merged and overlapping mask cases | test: edge contact; overlap refusal |
| 43 | drawing content and render | test: drawing shows content; renders to PNG |
| 44 | layer PDF used as the drawing | NOT RUN as a refusal test |
| 45 | drawing facts without a regex object parser | NOT RUN as a test; the facts come from the worker inventory |

## Additional items the lead asked for

- Positive package gate: test: package with every condition passing is qualified (exit 0); record: package-qualified exit 0.
- Supplier conditions: the workflow run gives rows for KiCad rules, outline, slots, both masks, layer count and order multiple, and the manual silk condition. Process-capability rows are not supplier rows.
- Standalone use: not run as a dedicated test. The skill directory has byte copies only; no run-time reference to another skill was tested.
- Caller timeout (decision 2): test: stalled worker through `fab.py inspect-mask` gives exit 2; fresh report path refused when it exists.
- Workflow mask path regression: test: supplier writes both mask rows.
