# Hand calculations (checks before and after the FEA)

Units: mm, N, MPa (N/mm²), N·mm. If the FEA and a hand calculation are different by more than approximately 30%, first examine the model (loads, supports, units).

## Section properties

| Section | Area A | I (bending about the horizontal axis) | c (outermost fiber) | Torsion J (approximate) |
|---|---|---|---|---|
| Rectangle, b wide × h tall | b·h | b·h³/12 | h/2 | β·b·h³ with b ≥ h, β ≈ 0.141 (square) to 0.333 (thin) |
| Solid circular section Ø d | π d²/4 | π d⁴/64 | d/2 | π d⁴/32 |
| Tube D/d | π(D²−d²)/4 | π(D⁴−d⁴)/64 | D/2 | π(D⁴−d⁴)/32 |
| I sections, box sections, ribs | sum of the parts | parallel axis: Σ(Iᵢ + Aᵢ·yᵢ²) | | |

Bending stress: `σ = M·c / I`. Maximum shear stress (rectangle): `τ = 1.5·V/A`.

**Height has the largest effect.** If you make h two times larger, the part becomes 8× stiffer and 4× stronger. Ribs are better than thicker walls.

## Beams

| Load condition | Maximum moment M | Maximum deflection δ |
|---|---|---|
| Cantilever, load F at the end, length L | F·L (at the wall) | F·L³ / (3·E·I) |
| Cantilever, distributed load w [N/mm] | w·L²/2 | w·L⁴ / (8·E·I) |
| Simply supported, load F at the center | F·L/4 | F·L³ / (48·E·I) |
| Simply supported, distributed load w | w·L²/8 | 5·w·L⁴ / (384·E·I) |
| Fixed at the two ends, load F at the center | F·L/8 | F·L³ / (192·E·I) |

Example (agrees with `fea.py` to 1%): PLA cantilever 100 × 10 × 10, F = 10 N: I = 833 mm⁴, σ = 10·100·5/833 = 6.0 MPa, δ = 10·100³/(3·2300·833) = 1.74 mm.

## Torsion

Shaft Ø d with torque T: `τ = 16·T/(π·d³)`. Twist: `θ = T·L/(G·J)` with `G = E / (2(1+ν))`. FDM shafts break along the layers in torsion. If the torque is important, print shafts horizontal.

## Buckling (thin columns in compression)

Euler: `F_cr = π²·E·I / (K·L)²`. K = 2 (one end free), 1 (pinned at the two ends), 0.7 (fixed and pinned), 0.5 (fixed at the two ends). Use SF 3 or more for buckling. Thin printed walls in compression can also buckle locally.

## Plates (flat panel, supported edges)

Constant pressure p on a rectangle, long side a, short side b, thickness t (Roark):
- Simply supported: `σ_max ≈ β·p·b²/t²`, `δ ≈ α·p·b⁴/(E·t³)`. a/b = 1: β ≈ 0.287, α ≈ 0.044. a/b = 2: β ≈ 0.610, α ≈ 0.111. a/b → ∞: β ≈ 0.75, α ≈ 0.142.
- Clamped edges: the deflection is approximately ⅓ of the simply supported value (square: α ≈ 0.0138). The peak stress moves to the middle of the edge, and its value stays approximately the same (square: β ≈ 0.308).

## Holes, pins, bolts and inserts

| Check | Formula or rule |
|---|---|
| Bearing on a hole (pin Ø d, wall t, load F) | `σ_b = F / (d·t)`. For FDM, keep it at 0.5 × yield or less |
| Tear-out (edge distance e from the center of the hole) | `τ = F / (2·e·t)`. Keep e at 2·d or more |
| Tension in the net section (plate width w) | `σ = F / ((w − d)·t)` × Kt ≈ 2.2 to 3 at the edge of the hole |
| Pull-out of an M3 heat-set insert (brass, PLA or PETG) | Typically approximately 400 N to 800 N. Design for 150 N or less on each insert |
| Self-tapping screw M3 into printed plastic | Pull-out approximately 150 N to 300 N. Design for 50 N to 80 N or less. Boss outer diameter 2.2·d or more |
| The clamp force of the bolt crushes the printed part | Use washers. Limit the torque (M3 ≈ 0.5 N·m, M4 ≈ 1 N·m in plastic) |

## Stress concentration factors (Kt, multiply the nominal stress by Kt)

| Feature | Kt |
|---|---|
| Small circular hole in a wide plate (tension) | 3.0 |
| Shoulder fillet r/h = 0.05 / 0.1 / 0.2 | approximately 2.5 / 1.9 / 1.5 |
| Sharp inner corner (r → 0) | No limit. **Add a fillet** (r 1 mm or more, better wall/2 or more) |
| Notch from a layer line or seam | approximately 1.2 to 1.5 (the SF targets include this factor) |

## Snap-fit cantilever (rectangular arm, fixed root)

y is the deflection that is necessary to engage. L is the arm length. t is the thickness at the root.
- Strain at the root: `ε = 1.5·y·t / L²` (constant section).
- Permitted strain, one short use: PLA ≈ 1.5% to 2%, PETG ≈ 3%, PC Blend ≈ 3% to 4%. Many uses: half of these values.
- Force for the deflection: `P = E·b·t²·ε / (6·L)` (b = arm width).
- Print snap arms so that they **bend in a layer** (the arm is flat in the XY plane). The arm must not bend across the layers.
- Make the arm thinner at the tip (t at the tip = t/2). This decreases the root strain by approximately 40%.

## Mass to force

`F[N] = m[kg] × 9.81`. For dynamic loads, or loads from hands, multiply by 2. For drops or impact, multiply by 3 to 5. A person who leans on a part: approximately 300 N to 500 N. A person who pulls a handle: approximately 200 N.
