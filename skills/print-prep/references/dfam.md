# FDM design rules (Prusa MK4, 0.4 mm nozzle)

The values are for a 0.4 mm nozzle, 0.45 mm line width, 0.2 mm layers, a calibrated printer, and Prusament or Jessie PLA or PETG. Put each value in the CAD parameter block. For important fits, print a test coupon.

## Overhangs and bridges

| Feature | Rule |
|---|---|
| Overhang with no support | 45° from vertical or less gives a clean surface. 55° or less is satisfactory on the MK4 (PrusaSlicer adds supports from 50°) |
| Bottom edges | Use a 45° chamfer, not a fillet. The bottom part of a fillet is an overhang of approximately 90° |
| Bridges | 10 mm to 20 mm or less give a clean bridge. Up to approximately 50 mm, the bridge sags. Make a bridge between two solid anchors |
| Horizontal holes, 10 mm or less | Usually satisfactory with no support. The top sags a little: ream the hole, or make the Ø 1.05 times larger |
| Horizontal holes, more than 10 mm | Use a teardrop profile (45° roof) or a flat-top profile (bridge) |
| Ceilings above cavities | Make them bridges (rectangular) or 45° roofs |
| Bosses or shelves that overhang | Add 45° gussets below them. Do not use support |

## Walls, floors and small features

| Feature | Minimum | Structural |
|---|---|---|
| Vertical wall | 0.9 mm (2 lines) | 1.8 mm or more (4 lines). Make the wall thickness a multiple of 0.45 mm |
| Floor and roof | 0.6 mm (3 layers) | 1.0 mm or more (5 layers) |
| Pin or vertical post Ø | 2 mm | 4 mm or more. Fillet the bottom of the post |
| Embossed or engraved text | Stroke 0.6 mm or more, depth or height 0.4 mm or more | Text on top faces looks best |
| Gap between parts (print-in-place) | 0.4 mm | 0.5 mm for a release that always occurs |

## Fits and tolerances (on each side, on a calibrated MK4)

| Fit | Clearance on each side |
|---|---|
| Press fit | 0.0 mm to 0.1 mm (coupon test) |
| Tight fit, location | 0.1 mm to 0.15 mm |
| Sliding or turning fit | 0.2 mm to 0.3 mm |
| Loose fit, print-in-place | 0.4 mm to 0.5 mm |
| Vertical holes | The printed hole is approximately 0.1 mm to 0.15 mm too small. Increase the modeled Ø by this value. By default, the hole compensation of the slicer is off |
| Horizontal holes | The holes become a little elliptical in Z. Ream important holes, or make them vertical |

The first layers become wider (elephant foot). The Prusa profiles compensate 0.2 mm (`elefant_foot_compensation`). But also chamfer the bed edges of mating faces by 0.4 mm to 0.5 mm.

## Fasteners

| Method | Hole | Notes |
|---|---|---|
| Heat-set insert M3 (short) | Ø 4.0 mm to 4.2 mm, depth = insert length + 0.5 mm | Wall around the insert: 1.6 mm or more (4 perimeters or more). This is the strongest method for assemblies that you open many times |
| Heat-set insert M4 / M5 | Ø 5.6 / 6.4 mm | Refer to the data from the supplier |
| Self-tapping screw into plastic, M3 | Ø 2.5 mm to 2.7 mm pilot hole | Boss outer diameter 7 mm or more. 10 assemblies or less |
| Captive nut M3 | Hex 5.5 mm AF + 0.2 mm to 0.3 mm clearance, slot from the side | Make a bridge above the nut, or pause the print and put the nut in |
| Through bolt M3 | Ø 3.4 mm clearance | Counterbore Ø 6.5 mm |
| Printed threads | Only M8 or larger, coarse pitch, 0.2 mm clearance | For structural parts, inserts are better |

If the bolt axis is Z, the clamp force of the bolt pushes **across the layers**. Use washers and a low torque.

## Features for strength

- Fillet inner corners that hold a load (1 mm or more, or half of the wall thickness or more). This decreases the stress concentration by 2 to 3 times.
- Use ribs, not thick walls. Rib thickness: approximately 0.6 to 1 × wall. Rib height: 3 × wall or less. Fillet the bottom of the rib.
- Add perimeters before you add infill. 4 to 6 perimeters give most of the strength of a solid part.
- Do not make thin sections that the slicer prints as gap fill (between 0.45 mm and 0.9 mm). Make them 0.9 mm, or 1.35 mm or more.
- Put the layer lines **parallel** to the bending stress. If a part must hold loads in all directions, use a tougher material (PETG or PC) or change the design.

## Warping and adhesion

| Material | Risk | Procedure to prevent it |
|---|---|---|
| PLA | Low | Clean sheet. Brim for tall or thin parts |
| PETG | Low to medium | Textured sheet or release agent (PETG bonds too strongly to smooth PEI) |
| ASA | High | Brim 5 mm to 8 mm, enclosure or draft shield, rounded corners, no air flow |
| PC Blend | High | Brim, enclosure, glue stick on smooth PEI, 110 °C bed |

Large flat parts: round the corners (R 5 mm or more). Add "mouse ears" (discs with Ø 10 mm to 15 mm and 0.2 mm to 0.4 mm thickness) at the corners.

## Large parts in sections

- The bed limit is 250 × 210 × 220 mm. A diagonal position gives a little more length in XY.
- Divide the part along faces with low stress. Connect the sections with alignment pins (Ø 5 mm, 0.15 mm clearance), dovetails, bolts and inserts, or adhesive (PETG, ASA, PC: solvent or CA). The Cut tool of PrusaSlicer (GUI) adds connectors automatically.
- Each section must have its own orientation for its loads.

## Surface quality

- Top faces are the cleanest. Faces on supports are rough. Vertical walls show layer lines.
- Shallow slopes (less than 20° from horizontal) show steps. Use thinner layers (0.10 mm to 0.15 mm) or variable layer height (GUI).
- The seam position (aligned or rear) sets the position of the vertical seam line. Put it at an inner corner or at the rear.

## Checklist before you slice

- [ ] The units are mm, the bbox agrees with the design, and the part is not larger than 250 × 210 × 220
- [ ] The mesh is watertight, with one body (or many bodies, if you want them)
- [ ] You selected the orientation for strength first, and you gave `build_dir` to the FEA
- [ ] Chamfers on the bed face, no fillets that point down, holes that are correct for their orientation
- [ ] Walls are multiples of 0.45 mm and 0.9 mm or more (structural: 1.8 mm or more)
- [ ] Clearances on all mating features, holes for inserts at the correct dimension
- [ ] You selected the material for temperature, UV and creep, and you exported a `.3mf` file
