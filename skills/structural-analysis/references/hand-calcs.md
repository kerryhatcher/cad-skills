# Hand Calculations (sanity checks before and after FEA)

Units: mm, N, MPa (N/mm²), N·mm. If FEA and a hand calculation disagree by more than ~30%, suspect the model (loads, supports, units) first.

## Section properties

| Section | Area A | I (bending about horizontal axis) | c (extreme fibre) | Torsion J (approx.) |
|---|---|---|---|---|
| Rectangle b wide × h tall | b·h | b·h³/12 | h/2 | β·b·h³ with b ≥ h, β ≈ 0.141 (square) → 0.333 (thin) |
| Solid round Ø d | π d²/4 | π d⁴/64 | d/2 | π d⁴/32 |
| Tube D/d | π(D²−d²)/4 | π(D⁴−d⁴)/64 | D/2 | π(D⁴−d⁴)/32 |
| I/box/rib sections | sum of parts | parallel axis: Σ(Iᵢ + Aᵢ·yᵢ²) | | |

Bending stress `σ = M·c / I`. Shear stress (rectangle, max) `τ = 1.5·V/A`.

**Height wins**: doubling h → 8× stiffer, 4× stronger. Ribs beat thicker walls.

## Beams

| Case | Max moment M | Max deflection δ |
|---|---|---|
| Cantilever, end load F, length L | F·L (at the wall) | F·L³ / (3·E·I) |
| Cantilever, uniform load w [N/mm] | w·L²/2 | w·L⁴ / (8·E·I) |
| Simply supported, centre load F | F·L/4 | F·L³ / (48·E·I) |
| Simply supported, uniform w | w·L²/8 | 5·w·L⁴ / (384·E·I) |
| Fixed–fixed, centre load F | F·L/8 | F·L³ / (192·E·I) |

Worked check (matches `fea.py` within 1%): PLA cantilever 100 × 10 × 10, F = 10 N: I = 833 mm⁴, σ = 10·100·5/833 = 6.0 MPa, δ = 10·100³/(3·2300·833) = 1.74 mm.

## Torsion

Shaft Ø d under torque T: `τ = 16·T/(π·d³)`, twist `θ = T·L/(G·J)` with `G = E / (2(1+ν))`. FDM shafts twist-fail along layers. Print shafts lying down when torque matters.

## Buckling (slender columns in compression)

Euler: `F_cr = π²·E·I / (K·L)²`. K = 2 (one end free), 1 (pinned–pinned), 0.7 (fixed–pinned), 0.5 (fixed–fixed). Use SF ≥ 3 on buckling. Thin printed walls in compression also buckle locally.

## Plates (flat panel, edges supported)

Uniform pressure p on a rectangle, long side a, short side b, thickness t (Roark):
- Simply supported: `σ_max ≈ β·p·b²/t²`, `δ ≈ α·p·b⁴/(E·t³)`. a/b = 1: β ≈ 0.287, α ≈ 0.044. a/b = 2: β ≈ 0.610, α ≈ 0.111. a/b → ∞: β ≈ 0.75, α ≈ 0.142.
- Clamped edges: deflection ~⅓ of simply supported (square: α ≈ 0.0138), but peak stress moves to mid-edge and stays similar (square: β ≈ 0.308).

## Holes, pins, bolts, inserts

| Check | Formula / guideline |
|---|---|
| Bearing on a hole (pin Ø d, wall t, load F) | `σ_b = F / (d·t)`. Keep ≤ 0.5 × yield for FDM |
| Tear-out (edge distance e from hole centre) | `τ = F / (2·e·t)`. Keep e ≥ 2·d |
| Net-section tension (plate width w) | `σ = F / ((w − d)·t)` × Kt ≈ 2.2–3 at the hole edge |
| M3 heat-set insert pull-out (brass, PLA/PETG) | ~400–800 N typical. Design to ≤ 150 N per insert |
| Screw into printed plastic (self-tapping, M3) | ~150–300 N pull-out. Design ≤ 50–80 N. Boss OD ≥ 2.2·d |
| Bolt clamp crushing printed part | Washers. Limit torque (M3 ≈ 0.5 N·m, M4 ≈ 1 N·m in plastic) |

## Stress concentration factors (Kt, multiply nominal stress)

| Feature | Kt |
|---|---|
| Small circular hole in a wide plate (tension) | 3.0 |
| Shoulder fillet r/h = 0.05 / 0.1 / 0.2 | ~2.5 / ~1.9 / ~1.5 |
| Sharp inside corner (r → 0) | unbounded. **Fillet it** (r ≥ 1 mm, better ≥ wall/2) |
| Notch from a layer line / seam | ~1.2–1.5 (built into the SF targets) |

## Snap-fit cantilever (rectangular arm, root fixed)

Deflection y needed to engage, arm length L, thickness t at the root:
- Strain at the root: `ε = 1.5·y·t / L²` (constant section).
- Allowable strain, momentary single use: PLA ≈ 1.5–2%, PETG ≈ 3%, PC Blend ≈ 3–4%. Repeated use: half that.
- Deflection force: `P = E·b·t²·ε / (6·L)` (b = arm width).
- Print snap arms so they **bend within a layer** (arm lying in the XY plane), never bending across layers.
- Taper the arm (t at tip = t/2) to cut root strain by ~40%.

## Weight → force

`F[N] = m[kg] × 9.81`. Dynamic or handled loads ×2. Dropped or impact ×3–5. A person leaning ~ 300–500 N, pulling a handle ~ 200 N.
