# Design for FDM (Prusa MK4, 0.4 mm nozzle)

Values assume 0.4 mm nozzle, 0.45 mm line width, 0.2 mm layers, a calibrated printer and Prusament/Jessie PLA or PETG. Put every value in the CAD parameter block, and print a test coupon for critical fits.

## Overhangs and bridges

| Feature | Rule |
|---|---|
| Unsupported overhang | ≤ 45° from vertical is clean, ≤ 55° acceptable on MK4 (PrusaSlicer supports from 50°) |
| Bottom edges | 45° chamfer, never a fillet (a fillet's lower part is a ~90° overhang) |
| Bridges | ≤ 10–20 mm clean, up to ~50 mm with sag. Bridge between two solid anchors |
| Horizontal holes ≤ 10 mm | Usually fine unsupported. Slight droop at top: ream or ×1.05 Ø |
| Horizontal holes > 10 mm | Teardrop (45° roof) or flat-top (bridge) profile |
| Ceilings over cavities | Make them bridges (rectangular) or 45° roofs |
| Overhanging bosses/shelves | Add 45° gussets underneath instead of support |

## Walls, floors, small features

| Feature | Minimum | Structural |
|---|---|---|
| Vertical wall | 0.9 mm (2 lines) | ≥ 1.8 mm (4 lines). Design in multiples of 0.45 mm |
| Floor/roof | 0.6 mm (3 layers) | ≥ 1.0 mm (5 layers) |
| Pin / standing post Ø | 2 mm | ≥ 4 mm, fillet the base |
| Embossed/engraved text | stroke ≥ 0.6 mm, depth/height ≥ 0.4 mm | Text on top faces looks best |
| Gap between parts (print-in-place) | 0.4 mm | 0.5 mm for reliable release |

## Fits and tolerances (per side, on a tuned MK4)

| Fit | Clearance per side |
|---|---|
| Press fit | 0.0–0.1 mm (coupon test) |
| Snug / location | 0.1–0.15 mm |
| Sliding / rotating | 0.2–0.3 mm |
| Loose / print-in-place | 0.4–0.5 mm |
| Vertical holes | Print ~0.1–0.15 mm undersize in Ø. Slicer hole compensation is off by default |
| Horizontal holes | Ellipse slightly in Z. Ream critical holes or orient vertically |

The first layers spread (elephant foot). Prusa profiles compensate 0.2 mm (`elefant_foot_compensation`). Still chamfer bed edges of mating faces 0.4–0.5 mm.

## Fasteners

| Method | Hole | Notes |
|---|---|---|
| Heat-set insert M3 (short) | Ø 4.0–4.2 mm, depth = insert length + 0.5 mm | Wall around ≥ 1.6 mm (≥ 4 perimeters). Strongest repeat-assembly option |
| Heat-set insert M4 / M5 | Ø 5.6 / 6.4 mm | Per vendor spec |
| Self-tapping into plastic M3 | Ø 2.5–2.7 mm pilot | Boss OD ≥ 7 mm. ≤ 10 re-assemblies |
| Captive nut M3 | Hex 5.5 mm AF + 0.2–0.3 clearance, slot from the side | Bridge over it, or pause-and-insert |
| Through bolt M3 | Ø 3.4 mm clearance | Counterbore 6.5 mm Ø |
| Printed threads | Only ≥ M8, coarse pitch, 0.2 mm clearance | Prefer inserts for anything structural |

Bolt clamping pushes **across layers** if the bolt axis is Z. Use washers and modest torque.

## Strength features

- Fillet load-bearing inside corners (≥ 1 mm, better ≥ half the wall) to cut stress concentration 2–3×.
- Ribs over thick walls: rib thickness ≈ 0.6–1 × wall, height ≤ 3 × wall, fillet the root.
- Increase perimeters before infill: 4–6 perimeters gives most of the strength of solid.
- Avoid thin sections that would print as gap fill (between 0.45 and 0.9 mm). Make them 0.9 or ≥ 1.35.
- Put layer lines **parallel** to bending stress. A part that must carry load in all directions needs a tougher material (PETG/PC) or a design change.

## Warping and adhesion

| Material | Tendency | Countermeasures |
|---|---|---|
| PLA | Low | Clean sheet. Brim for tall/thin parts |
| PETG | Low–medium | Textured sheet or release agent (sticks too hard to smooth PEI) |
| ASA | High | Brim 5–8 mm, enclosure/draft shield, rounded corners, no drafts |
| PC Blend | High | Brim, enclosure, glue stick on smooth PEI, 110 °C bed |

Large flat parts: round the corners (R ≥ 5 mm), add "mouse ears" (Ø 10–15 mm, 0.2–0.4 mm discs) at corners.

## Large parts and splitting

- Bed limit 250 × 210 × 220 mm. Diagonal placement gains a little in XY.
- Split along low-stress faces. Join with alignment pins (Ø 5 mm, 0.15 mm clearance), dovetails, bolts and inserts, or glue (PETG/ASA/PC: solvent or CA). PrusaSlicer's Cut tool (GUI) adds connectors automatically.
- Each piece must still be oriented for its own loads.

## Surface finish

- Top faces are cleanest. Faces against support are rough. Vertical walls show layer lines.
- Shallow slopes (< 20° from horizontal) show stair-stepping. Use smaller layers (0.10–0.15 mm) or variable layer height (GUI).
- The seam position (aligned/rear) controls the vertical zipper line. Put it at an inside or back corner.

## Pre-slice checklist

- [ ] Units mm, bbox matches intent, fits 250 × 210 × 220
- [ ] Watertight, single body (or intentionally several)
- [ ] Orientation chosen for strength first; `build_dir` passed to FEA
- [ ] Bed-face chamfers, no downward fillets, holes OK for their orientation
- [ ] Walls in multiples of 0.45 mm, ≥ 0.9 mm (structural ≥ 1.8 mm)
- [ ] Clearances on every mating feature; inserts sized
- [ ] Material picked for temperature/UV/creep; exported `.3mf`
