# Design Guidelines for Manufacturable Models

Rules of thumb for turning a CadQuery model into a part that can actually be made. When the user doesn't say how the part will be made, ask — or assume FDM 3D printing for hobby/prototype requests and say so. Put the chosen values in the parameter block, never inline.

## General (any process)

- Model in **millimetres**, at nominal size; put fit clearances in named parameters (`clearance = 0.3`).
- Every mating pair needs an explicit clearance or interference value. Run `inspect_model.py --interference` on the assembly.
- Standard hardware: design holes to clearance size, not thread size.

| Screw | Clearance hole (normal) | Tap drill | Counterbore Ø / depth (SHCS) | Countersink Ø (90°) | Heat-set insert hole |
|---|---|---|---|---|---|
| M2 | 2.4 | 1.6 | 4.4 / 2.1 | 4.4 | 3.2 |
| M2.5 | 2.9 | 2.05 | 5.5 / 2.6 | 5.5 | 3.6 |
| M3 | 3.4 | 2.5 | 6.5 / 3.2 | 6.5 | 4.0–4.2 |
| M4 | 4.5 | 3.3 | 8.0 / 4.3 | 8.6 | 5.6 |
| M5 | 5.5 | 4.2 | 10.0 / 5.3 | 10.4 | 6.4 |
| M6 | 6.6 | 5.0 | 11.0 / 6.4 | 12.4 | 8.0 |

(Heat-set insert sizes vary by vendor — make it a parameter.)

## FDM 3D printing

For a part that will be printed, continue with the companion skills: **`print-prep`** (orientation, printability, DfAM details), **`structural-analysis`** (FEA + layer-adhesion strength check) and **`prusaslicer`** (slice for Prusa MK4/MK4S).

| Feature | Guideline |
|---|---|
| Wall thickness | ≥ 2 × nozzle width (0.8 mm for 0.4 nozzle); 1.2–2.0 mm typical; structural ≥ 2.4 mm |
| Floor/roof | ≥ 4–5 layers (≈ 1.0 mm at 0.2 mm layers) |
| Clearance, sliding fit | 0.2–0.3 mm per side |
| Clearance, loose / print-in-place | 0.4–0.5 mm per side |
| Press fit | 0–0.1 mm (test-print a coupon) |
| Holes | print ~0.1–0.2 mm undersize; vertical holes better than horizontal |
| Overhangs | ≤ 45° from vertical without support; chamfer (45°) bottom edges instead of filleting them |
| Bridges | keep < 10–20 mm |
| Min feature | ≥ 0.8 mm; text ≥ 0.6 mm stroke, ≥ 0.4 mm emboss/engrave depth |
| Bosses for self-tapping screws | OD ≈ 2.2–2.5 × screw Ø, pilot ≈ 0.8 × screw Ø, fillet the base |
| Bed face | design one large flat face to sit on the build plate (often `<Z`) |
| Export | `.3mf` or `.stl` with `tolerance=0.01–0.05` |

Model large prints to avoid sharp internal corners (stress risers): small fillets (0.5–1 mm) on load-bearing inside corners.

## CNC milling

| Feature | Guideline |
|---|---|
| Internal vertical corners | radius ≥ tool radius (≥ 1/3 pocket depth is comfortable); you cannot mill a sharp inside corner — fillet `edges("|Z")` of pockets |
| Pocket depth | ≤ 3–4 × tool diameter |
| Walls | ≥ 0.8 mm metal, ≥ 1.5 mm plastic |
| Holes | standard drill sizes; depth ≤ 4–6 × Ø; blind holes get a 118° drill point if it matters |
| Fixturing | design flat, parallel reference faces; minimise setups (features on as few sides as possible) |
| External edges | chamfer (0.3–0.5 mm) instead of fillet unless cosmetic — cheaper |
| Threads | model the tap-drill hole, specify the thread on the drawing |

## Laser / waterjet (2D)

- Design as a `Sketch` or a planar face; export `.dxf` of the outline at z=0 (`faces("<Z")`).
- Kerf ≈ 0.1–0.2 mm (laser), 0.8–1.0 mm (waterjet): offset outlines by kerf/2 for tight fits.
- Slots/tabs: slot width = material thickness + fit allowance; material thickness is a parameter (real sheets vary ±10%).
- Minimum hole Ø ≈ material thickness; minimum web ≈ material thickness.

## Sheet metal (approximation in CadQuery)

CadQuery has no sheet-metal unfolding. Model bends as constant-thickness profiles (L/U extrusions) with inside radius ≥ thickness; keep holes ≥ 2× thickness from bends. For flat patterns compute bend allowance manually: `BA = angle_rad × (R + K × T)` with K ≈ 0.33–0.45.

## Injection moulding (if asked)

Uniform walls (1.5–3 mm), draft 1–2° on faces parallel to pull (`extrude(..., taper=1)` or `func.draft`), ribs ≤ 60% of wall, generous radii, no undercuts unless planned.
