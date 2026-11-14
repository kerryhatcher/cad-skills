---
name: structural-analysis
description: Use this skill to find if a part is sufficiently strong or stiff for its function, especially an FDM 3D-printed part. Topics are finite element analysis (FEA, FEM), stress, deflection, safety factor and load capacity. Questions are "will it break" and "how thick must it be". Other topics are the dimensions of a bracket, mount, hook, clip or lever, and layer adhesion. The last topics are the strength in a print orientation and the selection of PLA, PETG, ASA or PC. The skill operates on CadQuery scripts and STEP files with open-source tools (gmsh and scikit-fem) that run through uv.
license: MIT
metadata:
  author: Kerry Hatcher
  version: "1.0.0"
---

# Structural analysis for 3D-printed parts

## Overview

This skill finds if a part is applicable for its function before you print it. A linear static FEA (`scripts/fea.py`: gmsh mesh → scikit-fem P2 tetrahedra) calculates the deflection and the stress. The tool compares these values with data for **printed** material. It also examines the primary cause of FDM part failure: tension and shear **across the layers**.

**Primary rule: an FEA result is only as accurate as its loads, supports and material data. Also, FDM parts are not isotropic.** Always do these steps:

1. Calculate the result by hand, and compare.
2. Examine the image of the boundary conditions.
3. Examine the mesh convergence.
4. Examine the stress normal to the layers, for the actual print orientation.
5. Use a safety factor that agrees with the uncertainty.

## Language: Simplified Technical English

Write in ASD-STE100 Simplified Technical English (STE) when you use or change this skill. This rule applies to documentation, code comments, docstrings, CLI help text, error messages, commit messages and all messages to the user.

- Use approved STE words with one meaning each. You can use technical nouns and technical verbs.
- Use the active voice. Use the imperative for instructions. Use the simple present, simple past or simple future tense.
- Write one topic in each sentence. Use a maximum of 20 words in a procedure step, and 25 words in a description.
- Do not use phrasal verbs, idioms, semicolons, or noun clusters of more than three words.
- Write a WARNING or CAUTION as a command before the step. Then give the risk.
- Do not change code, commands, file names, configuration keys or quoted output. Copy them without changes.

`AGENTS.md` at the root of the cad-skills repository gives all the rules and examples.

## Environment

All tools run with `uv` (Python 3.10 to 3.13). `uv` downloads the dependencies when necessary:

```bash
uv run <skill-dir>/scripts/fea.py --list-materials
```

`<skill-dir>` is the directory that contains this SKILL.md. The first run downloads gmsh, scikit-fem and CadQuery (approximately 1 minute).

The gmsh wheel loads system GL and X libraries, also with no screen. If it shows the error `libGLU.so.1: cannot open shared object file`, install these libraries:

- Debian and Ubuntu: `sudo apt install libglu1-mesa libxcursor1 libxft2 libxinerama1`
- Fedora: `sudo dnf install mesa-libGLU libXcursor libXft libXinerama`

## Procedure

1. **Write the load case** before you use the solver:
   - The magnitude and the direction of each force (N). Change masses to forces: `F = m·g` (1 kg ≈ 9.81 N).
   - Multiply by a dynamic factor for drops, sudden movements and hands. Use ×2 if a person pulls on the part. Use ×3 or more for an impact.
   - The location of the supports (bolted face, clamped area, hole). The location where the load goes into the part (hole, face, edge).
   - The time that the load stays: short, **sustained** (creep) or **cyclic** (fatigue).
   - The temperature (in a car, in sunlight, near motors).
2. **First, calculate by hand** (`references/hand-calcs.md`). Examples: beam or cantilever, bearing, pull-out force of bolts and inserts. The FEA and the hand result can be different by more than approximately 30%. Then think that the model has an error. Find the error, or show that the model is correct.
3. **Learn the print orientation.** Run `printability.py` from the `print-prep` skill, or select the orientation. The tool shows `--build-dir` in model coordinates. The layers stack along this direction.
4. **Show the list of faces,** to select the supports and the loads:
   ```bash
   uv run <skill-dir>/scripts/fea.py part.py --list-faces
   ```
5. **Run the analysis:**
   ```bash
   uv run <skill-dir>/scripts/fea.py part.py --material prusament-petg \
       --fix "face:7" --fix "<X@x" --force "face:5=0,0,-100" \
       --build-dir y --sf-target 3 --png out/fea.png --vtu out/fea.vtu
   ```
   Then **read the PNG**:
   - Panel 1 must show blue (fixed) and red (loaded) at the correct faces.
   - Panels 2 and 3 show the von Mises stress on the deformed shape. The tool magnifies the deformation.
   - Panel 4 shows the stress normal to the layers. Red shows where the load pulls the layers apart.
6. **Examine the convergence.** Run the tool again with `--convergence` (3 mesh dimensions). The result is satisfactory when the deflection and the design stress change by less than 5%. If the design stress continues to increase, a sharp inner corner is the cause. Add a fillet.
7. **Compare the governing safety factor with the targets below.** The governing safety factor is the minimum of three values. These values are in-plane, interlayer tension and interlayer shear. Exit status 3 shows that it is less than `--sf-target`.
8. **Change the design. Start with the change that has the minimum cost:**
   1. Turn the part to a different print orientation.
   2. Add a fillet at the area of high stress.
   3. Make the part thicker, or add ribs.
   4. Use a stronger material.
   5. Add perimeters or infill.

   Run the analysis again after each change. Use `--set name=value` to change CadQuery parameters.
9. **Write a report.** Give the load case, the material, the orientation, the results, the safety factor and all assumptions. If the part has a safety function, tell the user to print a test part. Then apply 2× the design load to the test part.

## Supports and loads (selector syntax)

| Option | Meaning |
|---|---|
| `--fix "<X"` | The faces that a CadQuery selector selects. The tool holds these faces in all directions |
| `--fix "face:7"` / `"face:3,4"` | Faces by their number from `--list-faces` |
| `--fix "<Z@z"` | Fixed only in Z (roller, symmetry plane, part on a table) |
| `--fix "box:x0,y0,z0,x1,y1,z1"` / `"near:x,y,z"` | Faces in a box / the face nearest to a point |
| `--force "SEL=fx,fy,fz"` | **Total** force in N. The tool divides it equally on the selected faces |
| `--pressure "SEL=p"` | Pressure in MPa. A positive value pushes into the surface |

How to make a model of actual supports (refer to `references/fea-method.md` for more data):

- **Bolt through a hole:** hold the cylindrical face of the hole. On the clamped face, use `@` to hold only the normal direction (`"<X@x"`). A fully fixed face is stiffer than the actual part. It gives high stress values at its edge, and the design value ignores these values.
- **Load through a pin or bolt:** put `--force` on the cylindrical face of the hole. The tool divides the force equally on the full cylinder. An actual pin pushes on one side only. Thus the stress values near the hole are not accurate.
- **Symmetry:** make a model of one half of the part. Use `@` on the cut plane, in its normal direction. Use half of the load.
- The model must not be free to move or turn. If the solver shows that the model is under-constrained, add a constraint.

## How to read the results

| Output | Meaning |
|---|---|
| `deflection max` | Stiffness check. For brackets, usually keep it less than 1% of the span, or use the value that the function makes necessary |
| `von Mises design` | The maximum stress away from the support faces and load faces (Saint-Venant). The tool compares it with the in-plane yield strength |
| `von Mises max` | The highest stress, which includes the effects of ideal supports. For information only |
| `tension across layers` | The stress that pulls the layers apart along `--build-dir`. The tool compares it with the interlayer adhesion (approximately ⅓ of the in-plane strength) |
| `interlayer shear` | The shear stress that makes the layers move along each other. The tool compares it with 0.6 × interlayer strength (an estimate) |
| `safety factor` | The minimum of the three safety factors. The NOTES line gives the governing failure mode |
| `equilibrium error` | Reactions compared with the applied loads. It must be approximately 0%. If not, the loads are not on the correct faces |

### Safety-factor targets for FDM parts

| Condition | Target SF (on the strength of printed specimens) |
|---|---|
| Static load that you know, prototype or part that is not important, Prusament data | 2 |
| Typical functional part, Jessie or generic data, or a load that you do not know accurately | 3 |
| Sustained load (shelf bracket, hanger), all PLA parts with a constant load | 4 (also examine creep, `references/materials.md`) |
| Cyclic load or fatigue (more than 10³ cycles), snap-fits that you use many times | 4 to 5, or design for a strain of less than 1% to 2% |
| A part that can cause injury if it breaks | Do not use FDM parts alone for this function. Do a physical test and add a second load path |

## FDM data that the solver does not see

- **The solver uses a model of a solid part.** A print with 15% infill is mostly perimeters and skins. For parts that hold a load, select one of these two methods:
  - Print the load path almost solid (4 to 6 perimeters or more, 40% infill or more). Walls up to approximately 2 × perimeters × 0.45 mm are solid in all conditions.
  - Calculate a conservative "skin-only" model: CadQuery `shell(-perimeters*0.45)` of the area. Refer to `references/fea-method.md`.
- **Layer adhesion is the weak axis.** The interlayer strength of Prusament is 11 MPa to 21 MPa. Along the strands, the strength is 40 MPa to 63 MPa. Turn the part until bending and tension go *along* the layers, not across them.
- **Holes, notches and sharp inner corners** increase the stress by 2× to 3×. Add fillets (1 mm or more). Do not use the stress values at sharp corners.
- **Temperature:** PLA becomes soft at approximately 55 °C (HDT). For a hot car, sunlight or a motor, use PETG, ASA or PC Blend.
- **Creep:** PLA with a sustained load sags during some weeks, also at room temperature. Keep sustained loads at 25% of yield or less.
- **Material data:** the Prusament values are from the Prusa TDS sheets. **Jessie (Printed Solid) does not publish TDS data.** Thus the values of `jessie-pla` and `jessie-petg` are conservative estimates. Do a coupon test, and then use `--yield` and `--z-strength` with your values (`references/materials.md` shows how).

## Frequent errors

| Error | Symptom | Repair |
|---|---|---|
| Held and loaded on the same face, or an incorrect face number | The BC panel shows incorrect colors. The deflection is very small | Use `--list-faces`. Examine panel 1 |
| No `--build-dir` (the default z is the direction of the model) | The interlayer SF is for an incorrect orientation | Use `build_dir_model` from the printability tool |
| Load for each face, not the total load | The load is N times too large (N = number of faces) | The force is the TOTAL on all selected faces |
| Units: kg, not N. Pa, not MPa | The result is incorrect by ×10 or ×10⁶ | Use mm, N and MPa in all values |
| You use the peak at a sharp corner | The stress increases each time that you make the mesh finer | Add a fillet, or use the values away from the corner |
| Deflection more than 5% of the part dimension | NOTE: large deflection | Linear theory is not applicable. Make the part stiffer. Use the results only to compare designs |
| Analysis of an STL file | Error | FEA must have accurate geometry: a CadQuery `.py` file or STEP |
| SF 2 on a PLA part with a constant load | The part sags or cracks after some weeks | Creep: use SF 4 or more, or PETG, ASA or PC |

## Reference files

| File | Contents |
|---|---|
| `references/materials.md` | Property table and sources, Jessie estimates, coupon tests, effects of infill and perimeters, creep, temperature, fatigue |
| `references/hand-calcs.md` | Formulas for beams, plates, torsion, buckling, bolts and inserts, snap-fits, stress concentration |
| `references/fea-method.md` | Boundary conditions, mesh convergence, singularities, skin-only models, validation, other open-source tools (CalculiX, FreeCAD FEM, Code_Aster, ParaView) |

## Tools in this skill

- `scripts/fea.py` accepts a CadQuery `.py` file (with `--set` to change parameters), a STEP file or a BREP file. Options:
  - `--list-faces`, `--list-materials`
  - `--material` (with `--E --nu --yield --z-strength` to change the values)
  - `--fix`, `--force`, `--pressure`, `--build-dir`
  - `--size`, `--convergence`, `--sf-target`
  - `--png`, `--vtu`, `--json`
  - Exit status 0: the part passes. Exit status 3: the safety factor is less than the target.
