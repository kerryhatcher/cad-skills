# Design guidelines for parts that you can manufacture

These are general rules to change a CadQuery model into a part that a machine can make. If the user does not tell you the manufacturing method, get it from the user. As an alternative, use FDM 3D printing for hobby parts and prototypes, and tell the user. Put the selected values in the parameter block, not in the code of the chain.

## General rules (all methods)

- Make the model in **millimeters**, at nominal dimensions. Put the fit clearances in named parameters (`clearance = 0.3`).
- Each pair of mating parts must have an explicit clearance or interference value. Run `inspect_model.py --interference` on the assembly.
- Standard hardware: make holes at the clearance dimension, not at the thread dimension.

| Screw | Clearance hole (normal) | Tap drill | Counterbore Ø / depth (SHCS) | Countersink Ø (90°) | Hole for heat-set insert |
|---|---|---|---|---|---|
| M2 | 2.4 | 1.6 | 4.4 / 2.1 | 4.4 | 3.2 |
| M2.5 | 2.9 | 2.05 | 5.5 / 2.6 | 5.5 | 3.6 |
| M3 | 3.4 | 2.5 | 6.5 / 3.2 | 6.5 | 4.0–4.2 |
| M4 | 4.5 | 3.3 | 8.0 / 4.3 | 8.6 | 5.6 |
| M5 | 5.5 | 4.2 | 10.0 / 5.3 | 10.4 | 6.4 |
| M6 | 6.6 | 5.0 | 11.0 / 6.4 | 12.4 | 8.0 |

(The dimensions of heat-set inserts are different for each supplier. Make the dimension a parameter.)

## FDM 3D printing

If you will print the part, use the related skills:

- **`print-prep`**: orientation, printability, FDM design rules.
- **`structural-analysis`**: FEA and layer adhesion.
- **`prusaslicer`**: slice for a Prusa MK4 or MK4S.

| Feature | Rule |
|---|---|
| Wall thickness | 2 × nozzle width or more (0.8 mm for a 0.4 mm nozzle). Typical: 1.2 mm to 2.0 mm. Structural: 2.4 mm or more |
| Floor and roof | 4 to 5 layers or more (approximately 1.0 mm with 0.2 mm layers) |
| Clearance, sliding fit | 0.2 mm to 0.3 mm on each side |
| Clearance, loose fit or print-in-place | 0.4 mm to 0.5 mm on each side |
| Press fit | 0 mm to 0.1 mm (print a test coupon) |
| Holes | Make them approximately 0.1 mm to 0.2 mm smaller. Vertical holes are more accurate than horizontal holes |
| Overhangs | 45° from vertical or less with no support. Chamfer the bottom edges (45°). Do not fillet them |
| Bridges | Keep them shorter than 10 mm to 20 mm |
| Minimum feature | 0.8 mm or more. Text: stroke of 0.6 mm or more, emboss or engrave depth of 0.4 mm or more |
| Bosses for self-tapping screws | Outer diameter approximately 2.2 to 2.5 × screw Ø. Pilot hole approximately 0.8 × screw Ø. Fillet the bottom of the boss |
| Bed face | Make one large flat face that sits on the build plate (frequently `<Z`) |
| Export | `.3mf` or `.stl` with `tolerance=0.01–0.05` |

Large prints must not have sharp inner corners (they increase the stress). Add small fillets (0.5 mm to 1 mm) on inner corners that hold a load.

## CNC milling

| Feature | Rule |
|---|---|
| Inner vertical corners | Radius equal to or more than the tool radius (1/3 of the pocket depth or more is better). A mill cannot make a sharp inner corner. Fillet the `edges("|Z")` of pockets |
| Pocket depth | 3 to 4 × tool diameter or less |
| Walls | 0.8 mm or more for metal, 1.5 mm or more for plastic |
| Holes | Standard drill dimensions. Depth: 4 to 6 × Ø or less. If it is important, blind holes get a 118° drill point |
| Fixtures | Make flat, parallel reference faces. Use as few setups as possible (put the features on as few sides as possible) |
| External edges | Use a chamfer (0.3 mm to 0.5 mm), not a fillet, if the edge is not visible. A chamfer costs less |
| Threads | Make the tap-drill hole in the model. Specify the thread on the drawing |

## Laser and waterjet (2D)

- Make the part as a `Sketch` or a planar face. Export the outline at z=0 to `.dxf` (`faces("<Z")`).
- Kerf: approximately 0.1 mm to 0.2 mm (laser), 0.8 mm to 1.0 mm (waterjet). For tight fits, offset the outlines by kerf/2.
- Slots and tabs: slot width = material thickness + fit allowance. Make the material thickness a parameter (the thickness of sheets changes by ±10%).
- Minimum hole Ø: approximately the material thickness. Minimum web: approximately the material thickness.

## Sheet metal (approximate method in CadQuery)

CadQuery cannot unfold sheet metal. Make bends as profiles with a constant thickness (L or U extrusions). The inner radius must be equal to or more than the thickness. Keep holes at a distance of 2× thickness or more from bends. For flat patterns, calculate the bend allowance: `BA = angle_rad × (R + K × T)` with K ≈ 0.33 to 0.45.

## Injection molding (only if the user tells you)

Use walls with a constant thickness (1.5 mm to 3 mm). Use a draft of 1° to 2° on faces that are parallel to the pull direction (`extrude(..., taper=1)` or `func.draft`). Make ribs 60% of the wall thickness or less. Use large radii. Do not use undercuts, unless the mold design has a function for them.
