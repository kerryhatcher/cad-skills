---
name: structural-analysis
description: Use when checking whether a part (especially an FDM 3D-printed part) is strong or stiff enough for its job — finite element analysis (FEA/FEM), stress, deflection, safety factor, load capacity, "will it break", "how thick does it need to be", bracket/mount/hook/clip/lever sizing, layer adhesion or print-orientation strength, or choosing between PLA/PETG/ASA/PC. Works on CadQuery scripts and STEP files with open-source tools (gmsh + scikit-fem) run through uv.
license: MIT
metadata:
  author: Kerry Hatcher
  version: "1.0.0"
---

# Structural Analysis for 3D-Printed Parts

## Overview

Answers "is this part suitable for the job?" before it is printed. A linear-static FEA (`scripts/fea.py`: gmsh mesh → scikit-fem P2 tetrahedra) gives deflection and stress. It then checks them against **printed** material data, including what kills FDM parts: tension and shear **across the layers**.

**Core principle: an FEA number is only as good as its loads, supports and material data, and FDM parts are not isotropic.** Always (1) sanity-check with a hand calculation, (2) look at the boundary-condition picture, (3) check mesh convergence, (4) check layer-normal stress for the real print orientation, and (5) apply a safety factor suited to the uncertainty.

## Language: Simplified Technical English

Write in ASD-STE100 Simplified Technical English (STE) when you use or change this skill. This applies to documentation, code comments, docstrings, CLI help text, error messages, commit messages and all messages to the user.

- Use approved STE words with one meaning each. Technical names and technical verbs are permitted.
- Use the active voice. Use the imperative for instructions. Use simple present, simple past or simple future.
- Write one topic in each sentence. Maximum 20 words in a procedure step, 25 words in a description.
- Do not use phrasal verbs, idioms, or noun clusters of more than three words.
- Write a warning or caution as a command before the step, then give the reason.
- Do not change code, commands, file names, setting keys or quoted output. Copy them exactly.

The full rules and examples are in `AGENTS.md` at the root of the cad-skills repository.

## Environment

Everything runs with `uv` (Python 3.10–3.13, deps fetched on demand):

```bash
uv run <skill-dir>/scripts/fea.py --list-materials
```

`<skill-dir>` = the directory containing this SKILL.md. The first run downloads gmsh, scikit-fem and CadQuery (~1 min). The gmsh wheel loads system GL/X libraries even headless; if it fails with `libGLU.so.1: cannot open shared object file`, install them (Debian/Ubuntu: `sudo apt install libglu1-mesa libxcursor1 libxft2 libxinerama1`; Fedora: `sudo dnf install mesa-libGLU libXcursor libXft libXinerama`).

## Workflow

1. **Define the load case**, in writing, before touching the solver:
   - Magnitude and direction of every force (N). Convert masses: `F = m·g` (1 kg ≈ 9.81 N). Multiply by a dynamic factor for drops/jerks/hands (×2 for "someone pulls on it", ×3+ for impact).
   - Where it is held (bolted face, clamped region, hole) and where the load enters (hole, face, edge).
   - Duration: momentary, **sustained** (creep), or **cyclic** (fatigue). Temperature (car interior, sunlight, near motors).
2. **Hand-calculate first** (`references/hand-calcs.md`): beam/cantilever, bearing, bolt and insert pull-out. FEA that disagrees with a hand calc by more than about 30% means a modelling error until proven otherwise.
3. **Know the print orientation.** Run the `print-prep` skill's `printability.py` (or decide manually). It prints `--build-dir` in model coordinates. Layers stack along this direction.
4. **List faces** to pick supports and loads:
   ```bash
   uv run <skill-dir>/scripts/fea.py part.py --list-faces
   ```
5. **Run the analysis**:
   ```bash
   uv run <skill-dir>/scripts/fea.py part.py --material prusament-petg \
       --fix "face:7" --fix "<X@x" --force "face:5=0,0,-100" \
       --build-dir y --sf-target 3 --png out/fea.png --vtu out/fea.vtu
   ```
   Then **Read the PNG**. Panel 1 must show blue (fixed) and red (loaded) exactly where you intended. Panels 2–3 show von Mises on the exaggerated deformed shape. Panel 4 shows stress normal to layers (red = layers being pulled apart).
6. **Converge**: re-run with `--convergence` (3 mesh sizes). Accept when deflection and design stress change by less than 5%. Design stress that keeps climbing means a sharp internal corner, so add a fillet.
7. **Judge** with the governing safety factor (minimum of in-plane, interlayer tension, interlayer shear) against the targets below. Exit code 3 means it is below `--sf-target`.
8. **Iterate the design, cheapest fix first**: reorient the print → fillet the hot spot → thicken or add ribs → stronger material → more perimeters or infill. Re-run after each change, using `--set name=value` to sweep CadQuery parameters.
9. **Report** load case, material, orientation, results, SF, and every assumption. For anything safety-relevant, recommend a physical test print loaded to 2× the design load.

## Supports and loads (selector syntax)

| Spec | Meaning |
|---|---|
| `--fix "<X"` | Face(s) chosen by a CadQuery selector, fully fixed |
| `--fix "face:7"` / `"face:3,4"` | Faces by index from `--list-faces` |
| `--fix "<Z@z"` | Fixed only in Z (roller, symmetry plane, part resting on a table) |
| `--fix "box:x0,y0,z0,x1,y1,z1"` / `"near:x,y,z"` | Faces inside a box / nearest a point |
| `--force "SEL=fx,fy,fz"` | **Total** force in N, spread uniformly over the selected faces |
| `--pressure "SEL=p"` | MPa, positive pushes into the surface |

Modelling real supports (details in `references/fea-method.md`):
- **Bolted through a hole**: fix the hole's cylinder face, plus `@` normal-only on the clamped face (`"<X@x"`). Fixing a whole face fully is stiffer than reality and gives stress spikes at its edge, which the design value ignores.
- **Load through a pin or bolt**: put `--force` on the hole cylinder. It is uniform over the full cylinder, not bearing on one side, so expect local error near the hole.
- **Symmetry**: model half and use `@` on the cut plane in its normal direction (load halved).
- The model must not be free to slide or spin. If the solver says under-constrained, add a constraint.

## Reading results

| Output | Meaning |
|---|---|
| `deflection max` | Stiffness check. Typically keep < 1% of span for brackets, or whatever the function needs |
| `von Mises design` | Max away from support/load faces (Saint-Venant). Compared with in-plane yield |
| `von Mises max` | Raw peak incl. idealised-support artefacts. Informational |
| `tension across layers` | Stress pulling layers apart along `--build-dir`, compared with interlayer adhesion (≈ ⅓ of in-plane strength) |
| `interlayer shear` | Shear sliding layers, compared with 0.6 × interlayer strength (estimate) |
| `safety factor` | min of the three. Governing failure mode named in NOTES |
| `equilibrium error` | Reactions vs. applied. Should be ~0%, otherwise loads didn't land |

### Safety-factor targets for FDM parts

| Situation | Target SF (on printed-specimen strength) |
|---|---|
| Static, known load, prototype or non-critical, Prusament data | 2 |
| Typical functional part, Jessie/generic data or uncertain load | 3 |
| Sustained load (shelf bracket, hanger), any PLA under constant load | 4 (and check creep, `references/materials.md`) |
| Cyclic/fatigue (> 10³ cycles), snap-fits used repeatedly | 4–5, or design to strain < 1–2% |
| Anything that can hurt someone if it fails | Don't rely on FDM alone. Test physically and add redundancy |

## FDM essentials the solver can't see

- **The solver models a solid part.** A 15%-infill print is mostly perimeters and skins. For load-bearing parts, either print the load path effectively solid (≥ 4–6 perimeters, ≥ 40% infill; walls up to ~2×perimeters×0.45 mm are solid anyway), **or** analyse a conservative "skin-only" model: CadQuery `shell(-perimeters*0.45)` of the region. See `references/fea-method.md`.
- **Layer adhesion is the weak axis.** Prusament interlayer strength is 11–21 MPa against 40–63 MPa along the strands. Orient so bending and tension run *along* layers, not across them.
- **Holes, notches and sharp inside corners** concentrate stress 2–3×. Fillet them (≥ 1 mm) and don't rely on values at sharp corners.
- **Temperature**: PLA softens at ~55 °C (HDT). Hot car, sun or a motor means use PETG, ASA or PC Blend.
- **Creep**: PLA under sustained load sags over weeks even at room temperature. Size sustained loads to ≤ 25% of yield.
- **Material data**: Prusament values come from Prusa TDS sheets. **Jessie (Printed Solid) publishes no TDS**, so `jessie-pla`/`jessie-petg` are conservative estimates. Coupon-test them and override with `--yield` and `--z-strength` (`references/materials.md` shows how).

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Fixed and loaded on the same face, or wrong face index | BC panel shows wrong colours; tiny deflection | `--list-faces`, look at panel 1 |
| Forgot `--build-dir` (default z = as modelled) | Interlayer SF for the wrong orientation | Use printability's `build_dir_model` |
| Load per face instead of total | Load × N faces | Force is the TOTAL over all selected faces |
| Units: kg instead of N, Pa instead of MPa | Off by ×10 or ×10⁶ | mm, N, MPa throughout |
| Trusting a sharp-corner peak | Stress grows with every refinement | Fillet it, or judge away from it |
| Deflection > 5% of size | NOTE: large deflection | Linear theory invalid. Stiffen the part, treat results as qualitative |
| Analysing an STL | Error | FEA needs exact geometry: CadQuery `.py` or STEP |
| SF 2 on a PLA part under constant load | Sags or cracks in weeks | Creep: SF ≥ 4 or PETG/ASA/PC |

## Reference files

| File | When |
|---|---|
| `references/materials.md` | Property table + sources, Jessie estimates, coupon tests, infill/perimeter effects, creep, temperature, fatigue |
| `references/hand-calcs.md` | Beam, plate, torsion, buckling, bolt/insert, snap-fit, stress concentration formulas |
| `references/fea-method.md` | BC modelling, mesh convergence, singularities, skin-only models, validating, other OSS tools (CalculiX, FreeCAD FEM, Code_Aster, ParaView) |

## Bundled tools

- `scripts/fea.py` takes a CadQuery `.py` (with `--set` parameter overrides), STEP or BREP. Options: `--list-faces`, `--list-materials`, `--material` (+ `--E --nu --yield --z-strength` overrides), `--fix/--force/--pressure`, `--build-dir`, `--size`, `--convergence`, `--sf-target`, `--png`, `--vtu`, `--json`. Exit 0 = passes, 3 = below target.
