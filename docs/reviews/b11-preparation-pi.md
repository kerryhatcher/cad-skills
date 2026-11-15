# B11 mechanical preparation review: Pi

Date: 2026-11-14.

**Decision: the plan and the accepted board-interface schema are sufficient for B11. Six choices are necessary. The trial STEP lacks component 3D models. B11 can supply licensed models or labeled proxies. The component-height constraints stay explicit.**

## 1. Source check

| Source | Fact used |
|---|---|
| Plan section 9 | Export STEP for the board and components. Export DXF for the outline and holes. Also export `board-interface.json`. Use an asymmetric trial board with an offset origin, unequal holes and a bottom-side component. Import into CadQuery. Measure holes, thickness, connector orientation and enclosure clearance. Detect mirror and axis errors. Record the owner of each dimension. Keep generated files in `out/`. Regenerate in CI before the fit test. Use one release ID and compare interface hashes before publication. |
| `contracts/schemas/board-interface.schema.json` | Required: `units` (mm), `origin_mm`, `thickness_mm`, `geometry_tolerance_mm`, `outline`, `cutouts`, `holes`, `connector_frames`, `height_limits` (top and bottom), `enclosure_clearance_mm`, `dimension_owners`, `board_revision`, `board_sha256`. Optional `extensions`. No axis-direction field and no per-component height field. |
| Trial STEP (`results/final_r2/export/trial.step`) | Two products, `trial 1` and `trial_PCB`, and one solid. No component models. A general B11 fixture can add licensed models or labeled proxies. |
| Trial interface | Board outline is `100..140 x 100..125` in KiCad coordinates. Interface outline is `0..40 x 0..25`. Holes: MH1 `(3,22)`, MH2 `(37,3)`. The board holes are `(103,103)` and `(137,122)`. The interface flips Y (`125 - y`) and translates X by `100`. No connector frames. No bottom-side component. |

## 2. Necessary choices

| ID | Choice | Recommended answer |
|---|---|---|
| B11-1 | Transform | State the KiCad +Y-down to mechanical +Y-up conversion and the board anchor. The trial maps board `(100,125)` to interface `(0,0)`, but `origin_mm` is `0,0`. The plan's text says `origin_mm` is a board point. Resolve this: record the board anchor and the axis directions in `extensions`, or correct the trial interface. Add the explicit source-to-contract transform for the new B11 fixture. Do not rewrite the accepted B5 history. Test mirror and axis errors. |
| B11-2 | Asymmetric fixture | The trial has an offset origin and unequal holes. It has no bottom-side component and no connector frame. The new B11 fixture includes a bottom-side part and a connector frame. The trial STEP is board-only. |
| B11-3 | STEP/DXF identity | Bind each file to `board_revision`, `board_sha256` and the interface hash. Use one release ID. Regenerate in CI. Do not require byte-identical STEP regeneration unless a measurement shows it. Use geometry and tolerance agreement. Retain the exact hash of each produced file. Compare interface hashes before publishing both artifact sets. |
| B11-4 | Component-height evidence | `height_limits` are constraints, not evidence of actual part height. Keep measured or datasheet heights and any owned proxy geometry in separate records, each with explicit limits. A proxy can test a conservative envelope. It cannot prove detailed component clearance. Mark an unevidenced limit `unconfirmed`. |
| B11-5 | Collision checks | Do not forbid STEP component geometry in general. The trial STEP lacks component models. B11 can supply licensed models or labeled proxies. When no model exists, use the height constraints or a labeled proxy envelope. A proxy checks a conservative envelope only. It does not prove detailed component clearance. Check connector insertion space and orientation. State the tolerance. |
| B11-6 | Stale-release failures | A board, interface, component-revision or supplier-profile change makes the release stale. Refuse publication and name the first mismatch. A board change triggers the fit test. |

## 3. Test expectations

- Transform: a mirrored or Y-flipped board fails. The measured board passes.
- Fixture: the new fixture includes a bottom-side part and a connector frame. A missing one fails.
- Identity: a changed board or interface hash fails. Geometry and tolerance agreement passes. The exact hash of each produced file is retained. A byte-identical claim needs a measurement.
- Height: an unevidenced limit is `unconfirmed`. A datasheet or measured height over a limit fails. A proxy envelope passes a conservative check only.
- Collision: a part over the top limit, or inside the connector insertion space, fails. A part within clearance passes. A proxy does not prove detailed clearance.
- Stale: each change refuses publication with the named reason.

No implementation, container run or broad research was done. I will review the B6 checkpoint first when it arrives.
