# Materials for structural analysis of FDM parts

All strength values are for **printed specimens**, not injection-molded plastic. These values are lower, and they change with the direction.

## Property table (`fea.py --material` uses it)

| Key | E [MPa] | ν | Yield, along strands [MPa] | Interlayer (Z) [MPa] | HDT 0.45 MPa [°C] | ρ [g/cm³] | Source |
|---|---|---|---|---|---|---|---|
| `prusament-pla` | 2300 | 0.35 | 51 | 17 | 55 | 1.24 | Prusament PLA TDS |
| `prusament-pla-blend` | 2300 | 0.35 | 51 | 17 | 55 | 1.24 | the same TDS (PLA and PLA Blend) |
| `prusament-petg` | 1500 | 0.38 | 47 | 18 | 68 | 1.27 | Prusament PETG TDS v1.1 |
| `prusament-asa` | 1600 | 0.35 | 42 | 11 | 93 | 1.07 | Prusament ASA TDS v1.1 |
| `prusament-pc-blend` | 1900 | 0.37 | 63 | 21 | 113 | 1.22 | Prusament PC Blend TDS v1.1 |
| `jessie-pla` | 2200 | 0.35 | 45 | 14 | ~55 | 1.24 | **estimate** |
| `jessie-petg` | 1500 | 0.38 | 42 | 14 | ~68 | 1.27 | **estimate** |
| `generic-pla/petg/abs/asa/pc` | – | – | – | – | – | – | conservative values for a brand that you do not know |

Prusament test conditions (from the TDS sheets):

- ISO 527-1 tensile bars, 0.20 mm layers, 100% rectilinear infill, no top or bottom shells.
- "Horizontal" bars are flat on the bed. The Prusa "vertical xz" bars stand on their long edge. In both bars, the strands go along the bar. Thus **neither bar measures Z**.
- Prusa gives the Z value as a different value, "Interlayer Adhesion" (a Prusa test method).
- The table uses the lower value of horizontal and vertical for yield. It uses the interlayer value for Z.
- To find the sheets: `prusament.com` → each material → Technical data sheet.

Ratio to remember: **interlayer strength ≈ 25% to 40% of the in-plane strength**. ASA has the lowest ratio (approximately 26%). PC Blend has the highest ratio (approximately 33%).

### Jessie (Printed Solid)

Printed Solid publishes **no technical data sheet** for Jessie PLA or PETG (examined in November 2026). Other websites give approximately 50 MPa tensile strength for Jessie PETG, 6% elongation and 1.24 to 1.27 g/cm³, with no orientation data. Users think that Jessie is a PLA and PETG of good quality. Thus the estimates are approximately 10% below Prusament in-plane, and approximately 20% below for interlayer strength. **If the part is important, do a coupon test (below) before you use the Jessie values. Then give your results with `--yield` and `--z-strength`.** PrusaSlicer has `Jessie PLA` and `Jessie PETG` print profiles for the MK4 and MK4S.

## Effective strength of an actual print

The table is for 100% solid material. Actual parts are different:

| Factor | Effect | Action |
|---|---|---|
| Sparse infill (15% default) | Infill adds little strength. Perimeters and skins hold the bending load | For the load path: 4 perimeters or more, 40% gyroid or cubic infill or more, or calculate a skin-only model |
| Number of perimeters | The largest single effect on bending and torsion strength | 4 to 6 perimeters for structural parts (`perimeters=5`) |
| Layer height | Thinner layers give a little better adhesion. 0.2 mm is satisfactory | Use 0.15 mm to 0.20 mm for strength, not 0.28 mm or more |
| Nozzle temperature | Higher temperature gives better interlayer bonds (top of the range) | Add 5 °C to 10 °C for structural parts. Use less cooling for PETG and ASA |
| Cooling fan | More fan gives weaker layers (PLA is not sensitive, but PETG, ASA and PC are sensitive) | The profiles set a low fan speed for PETG, ASA and PC |
| Moisture (PETG, PC) | Wet filament gives bubbles and weak layers | Dry the filament before structural prints (PETG 65 °C 4 h, PC 90 °C 4 h) |
| Seams, holes, starts | Local weak areas | The safety-factor targets include a factor of approximately 1.2 for these areas |

### Conservative skin-only model

For a part with sparse infill, make a model of the skin only. Use walls of `perimeters × 0.45 mm`. Use floors of `top/bottom_solid_min_thickness` (0.7 mm and 0.5 mm in the Prusa profiles). In CadQuery:

```python
# notest
skin = solid_part.faces(">Z").shell(-(perimeters * 0.45))  # open top (or shell a copy and remove no faces)
```

If the skin-only model passes, the actual part (skin and infill) also passes. If only the solid model passes, print the load path solid.

## Temperature, creep, fatigue and environment

| Topic | General rule |
|---|---|
| Service temperature | Keep the temperature 15 °C to 20 °C or more below the HDT. The strength decreases as the temperature increases to the HDT |
| Creep (sustained load) | At 20 °C, PLA creeps a measurable quantity above approximately 10 MPa. PETG is better, ASA and PC are the best. Design for a sustained stress of 25% of yield or less (SF 4 or more) |
| Fatigue | The FDM endurance limit is approximately 20% to 30% of the static strength at 10⁶ cycles. It is lower across the layers. Do not put cyclic tension across the layers |
| Impact and toughness | PLA is brittle (Charpy approximately 13 kJ/m²). PETG and PC Blend do not break in a test with no notch |
| UV and outdoor use | PLA and PETG become weak and yellow. ASA is stable in UV. PC Blend is satisfactory |
| Chemicals, fuel, oil | PETG and PC are resistant. PLA is not resistant |

| Material | Select it for |
|---|---|
| PLA / PLA Blend | Indoor use, stiff parts, room temperature, loads for a short time. It is the easiest to print |
| PETG | Tougher, warmer conditions (60 °C or less), snap-fits, some outdoor use, medium creep |
| ASA | Outdoor use and UV, 85 °C or less. It has the weakest layers: select the orientation carefully, use a brim, and use an enclosure if possible |
| PC Blend | Highest strength and toughness, 100 °C or less. It must have an enclosure, a brim, a 275 °C nozzle and a 110 °C bed |

## Coupon test for your filament (do this test for Jessie)

This test has a low cost, and it is sufficiently accurate to calibrate `--yield` and `--z-strength`:

1. Make a model of a 10 × 10 × 100 mm bar. Print two sets with your print profile:
   - **XY bars** flat on the bed (the strands go along the bar). These bars give the in-plane strength.
   - **Z bars** vertical (bar axis = Z). These bars give the interlayer strength.
2. Do a three-point bend test on each bar. Put the bar on two supports, `L = 80 mm` apart. Apply a load at the center until the bar breaks. For the load, hang a bucket and add water, or use a luggage scale. Record `F` [N].
3. Calculate the flexural stress at the break: `σ = 3·F·L / (2·b·h²)` with `b = h = 10`. Thus `σ = 0.12·F` MPa.
4. For plastics, the bend strength is approximately 1.3 to 1.5 times more than the tensile strength. Use `σ/1.4` for `--yield` (XY bars) and `--z-strength` (Z bars). Test 3 bars or more, and use the **lowest** value.
