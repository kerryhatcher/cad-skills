# Materials for FDM Structural Analysis

All strengths are for **printed specimens**, not injection-moulded plastic. They are lower and direction-dependent.

## Property table (used by `fea.py --material`)

| Key | E [MPa] | ν | Yield, along strands [MPa] | Interlayer (Z) [MPa] | HDT 0.45 MPa [°C] | ρ [g/cm³] | Source |
|---|---|---|---|---|---|---|---|
| `prusament-pla` | 2300 | 0.35 | 51 | 17 | 55 | 1.24 | Prusament PLA TDS |
| `prusament-pla-blend` | 2300 | 0.35 | 51 | 17 | 55 | 1.24 | same sheet (PLA/PLA Blend) |
| `prusament-petg` | 1500 | 0.38 | 47 | 18 | 68 | 1.27 | Prusament PETG TDS v1.1 |
| `prusament-asa` | 1600 | 0.35 | 42 | 11 | 93 | 1.07 | Prusament ASA TDS v1.1 |
| `prusament-pc-blend` | 1900 | 0.37 | 63 | 21 | 113 | 1.22 | Prusament PC Blend TDS v1.1 |
| `jessie-pla` | 2200 | 0.35 | 45 | 14 | ~55 | 1.24 | **estimate** |
| `jessie-petg` | 1500 | 0.38 | 42 | 14 | ~68 | 1.27 | **estimate** |
| `generic-pla/petg/abs/asa/pc` | – | – | – | – | – | – | conservative unknown-brand values |

Prusament test conditions (from the sheets): ISO 527-1 tensile bars, 0.20 mm layers, 100% rectilinear infill, no top/bottom shells. "Horizontal" means flat on the bed. Prusa's "vertical xz" means standing on its long edge: strands still run along the bar, so **neither is Z**. Prusa reports Z separately as "Interlayer Adhesion" (in-house method). The table uses the lower of horizontal/vertical for yield and the interlayer value for Z. Sheets: `prusament.com` → each material → Technical data sheet.

Ratio to remember: **interlayer ≈ 25–40% of in-plane strength** (ASA worst at ~26%, PC Blend best at ~33%).

### Jessie (Printed Solid)

Printed Solid publishes **no technical data sheet** for Jessie PLA or PETG (checked Nov 2026). Third-party aggregators list Jessie PETG at ~50 MPa tensile, 6% elongation, 1.24–1.27 g/cm³, no orientation data. Jessie is generally regarded as a good-quality PLA/PETG, so the estimates sit ~10% below Prusament in-plane and ~20% below on interlayer. **Before trusting Jessie numbers on a part that matters, coupon-test (below) and pass your results with `--yield` / `--z-strength`.** PrusaSlicer ships `Jessie PLA` and `Jessie PETG` print profiles for the MK4/MK4S.

## Effective strength of a real print

The table assumes 100% solid material. Real parts differ:

| Factor | Effect | What to do |
|---|---|---|
| Sparse infill (15% default) | Infill adds little strength. Perimeters and skins carry bending | Load path: ≥ 4 perimeters, ≥ 40% gyroid/cubic, or analyse skin-only |
| Perimeter count | Strongest single lever for bending/torsion strength | 4–6 perimeters for structural parts (`perimeters=5`) |
| Layer height | Thinner layers: slightly better adhesion. 0.2 mm is fine | Use 0.15–0.20 mm for strength, not 0.28+ |
| Nozzle/extrusion temperature | Hotter = better interlayer bonding (top of range) | +5–10 °C for structural parts, less cooling for PETG/ASA |
| Cooling fan | More fan = weaker layers (PLA tolerates it, PETG/ASA/PC don't) | Profiles already set low fan for PETG/ASA/PC |
| Moisture (PETG, PC) | Wet filament: bubbles, weak layers | Dry before structural prints (PETG 65 °C 4 h, PC 90 °C 4 h) |
| Seams, holes, starts | Local weak spots | Rough SF of 1.2 already assumed in targets |

### Skin-only conservative model

For a part printed with sparse infill, model just the skin: `perimeters × 0.45 mm` walls and `top/bottom_solid_min_thickness` floors (0.7/0.5 mm in Prusa profiles). In CadQuery:

```python
# notest
skin = solid_part.faces(">Z").shell(-(perimeters * 0.45))  # open top; or shell a copy with no faces removed
```

If the skin-only model passes, the real part (skin + infill) passes. If only the solid model passes, print the load path solid.

## Temperature, creep, fatigue, environment

| Topic | Rule of thumb |
|---|---|
| Service temperature | Keep ≥ 15–20 °C below HDT. Strength falls steadily as you approach it |
| Creep (sustained load) | PLA creeps noticeably at 20 °C above ~10 MPa. PETG is better, ASA/PC best. Design sustained stress ≤ 25% of yield (SF ≥ 4) |
| Fatigue | FDM endurance is roughly 20–30% of static strength at 10⁶ cycles, worse across layers. Avoid cyclic tension across layers |
| Impact / toughness | PLA is brittle (Charpy ~13 kJ/m²). PETG and PC Blend don't break unnotched |
| UV / outdoors | PLA, PETG degrade/yellow. ASA is UV-stable. PC Blend is OK |
| Chemicals/fuel/oil | PETG and PC fairly resistant, PLA poor |

| Material | Pick it when |
|---|---|
| PLA / PLA Blend | Indoor, stiff, room temperature, short-term loads, easiest to print |
| PETG | Tougher, warmer (≤ 60 °C), snap-fits, outdoor-ish, moderate creep |
| ASA | Outdoor/UV, ≤ 85 °C. Weakest layers: orient carefully, brim, ideally enclosed |
| PC Blend | Strongest/toughest, ≤ 100 °C. Needs enclosure, brim, 275 °C nozzle, 110 °C bed |

## Coupon testing your filament (do this for Jessie)

Cheap and good enough to calibrate `--yield` and `--z-strength`:

1. Model a 10 × 10 × 100 mm bar. Print two sets with your real profile:
   - **XY bars** flat on the bed (strands along the bar) → in-plane strength.
   - **Z bars** standing vertical (bar axis = Z) → interlayer strength.
2. Three-point bend each on supports `L = 80 mm` apart, loading the centre (hang a bucket and add water, or use a luggage scale) until it breaks. Record `F` [N].
3. Flexural stress at break: `σ = 3·F·L / (2·b·h²)` with `b = h = 10` → `σ = 0.12·F` MPa.
4. Bend strength overestimates tensile strength ~1.3–1.5× for plastics. Use `σ/1.4` for `--yield` (XY bars) and `--z-strength` (Z bars). Take the **lowest** of ≥ 3 bars.
