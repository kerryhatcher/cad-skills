# FEA Method Notes

## What `fea.py` does

1. Builds the CadQuery script (CQGI, so `--set name=value` works) or imports STEP/BREP. It must be exactly one solid.
2. Meshes with gmsh (OpenCASCADE kernel, Delaunay 3D, curvature refinement), matching gmsh surfaces back to CadQuery faces by centroid and area, so face selectors work on the mesh.
3. Solves linear elasticity with scikit-fem on **quadratic (P2) tetrahedra**, which avoid the shear locking of linear tets in bending. Direct sparse solve up to ~150k DOFs, then AMG-preconditioned CG.
4. Computes von Mises, stress normal to the layers `σ_nn = n·σ·n` (n = `--build-dir`) and interlayer shear `|σ·n − σ_nn·n|`. Projects them to nodes and reports maxima **away from** support and load faces (more than one element size). Raw peaks are still listed.
5. Checks equilibrium (reactions = −applied) and returns SF = min(in-plane, interlayer tension, interlayer shear).

Isotropic linear elasticity is used for stiffness. Anisotropy is handled in the **strength check**, which is where FDM anisotropy matters most (stiffness differs only ~5–15% by direction, while strength across layers is ~⅓).

Validated against beam theory: cantilever deflection within 0.1%, root bending stress within 1–2%.

## Boundary conditions: the biggest source of error

| Real situation | Model it as | Notes |
|---|---|---|
| Bolted to a rigid wall | Fix the bolt hole cylinders, plus `@` normal-only on the contact face | Full fixing of the whole face over-stiffens |
| Clamped in a vise | Fix both clamped faces | |
| Resting on a table | `@z` on the bottom face plus one tiny lateral constraint | Can't model lift-off (no contact) |
| Hook/pin through a hole | `--force` on the hole cylinder | Uniform over the full cylinder, conservative-ish on the far side |
| Hand pressing on a face | `--pressure` or `--force` on a sub-face | Split the face in CadQuery if the load area is small |
| Symmetric part and load | Half model, `@` normal on the cut plane, half the load | |
| Glued/press-fit | Fix the bonded faces | |

`fea.py` has no contact, friction, bolt preload, or large-deflection (geometric nonlinear) capability. If they matter, see "Other tools".

**Splitting a face for a local load**: in CadQuery, cut a 0.01 mm deep rectangle onto the face (or use `split`) so the load patch is its own face, then select it with `near:x,y,z`.

## Mesh convergence

- Default element size: min(smallest bbox side / 4, largest / 20). Curvature refinement 12 elements per 2π.
- `--convergence` solves at 2×, 1.41× and 1× size. Converged = < 5% change in design stress and deflection.
- Deflection converges fast. Stress converges slower, except at sharp re-entrant corners, where it never converges (singularity). That signals a real stress concentration: add a fillet and re-run.
- Keep runs under ~150k DOFs for fast direct solves (a few seconds to ~40 s). Thin, large parts produce many elements, so set `--size` explicitly (≥ wall thickness / 2 still gives good P2 results).

## Interpreting stresses

- **von Mises vs. yield**: ductile in-plane failure (PETG, PC). PLA is more brittle, so the SF targets assume that.
- **Max principal**: tension that opens cracks. It's in the VTU as `max_principal`.
- **Layer normal (+)**: delamination driver. It's the governing check for most poorly oriented FDM parts.
- **Peaks at support or load edges** are artefacts of idealised BCs. The design value excludes them, but if the real support has sharp edges, the real part is stressed there too.
- **Deflection > 5% of size**: linear theory is no longer accurate. Results are qualitative, so stiffen the design.

## Skin-only analysis (sparse infill)

For parts that will be printed with low infill, run a second analysis on a hollowed copy. In CadQuery: `part.shell(-skin)` with `skin = perimeters × 0.45` (closed shell, no faces removed: `cq.Workplane().add(part.val().shell([], -skin))`, or model the interior cavity explicitly). This is conservative because it ignores infill. The truth lies between skin-only and solid.

## Viewing results

`--vtu out/result.vtu` → open in **ParaView** (`flatpak install flathub org.paraview.ParaView`). Point data: `displacement`, `von_mises`, `layer_normal`, `layer_shear`, `max_principal`. Use *Warp By Vector* on displacement and *Clip* to look inside.

## Other open-source tools (when to escalate)

| Tool | Use it for |
|---|---|
| **CalculiX** (`ccx`, GPL) with **gmsh** | Contact, plasticity, large deflection, **orthotropic** materials (`*ELASTIC, TYPE=ENGINEERING CONSTANTS`), modal/buckling. Industry-proven. Use **PyCCX/pycalculix** for scripting. Debian/Ubuntu: `apt install calculix-ccx`; anywhere: conda-forge `calculix` |
| **FreeCAD FEM workbench** (uses CalculiX) | GUI setup of contact, bolts and orthotropic materials. Imports STEP from CadQuery |
| **Code_Aster / salome_meca** | Heavy nonlinear, fatigue, composites |
| **Elmer FEM** | Multiphysics (thermal + structural) |
| **scikit-fem** directly | Custom physics in Python (what `fea.py` is built on) |

Escalate when: the part relies on contact or friction (clips, interference fits), deflects a lot (living hinges, flexures), the load is impact, or a failure would be dangerous. For FDM, also consider printing and testing. A test print loaded to 2× design load is often the cheapest validation.

## Reporting template

```
Part / revision:            Material + filament brand:      Print orientation (build dir):
Load case: forces (N), where, duration (momentary/sustained/cyclic), temperature
Supports:
Mesh: size, nodes, converged? (Δ%)
Results: max deflection __ mm; von Mises __ MPa (SF __); layer tension __ MPa (SF __); layer shear __ MPa (SF __)
Governing mode + SF vs target:
Assumptions / limitations: (linear, no contact, solid vs infill, estimated material data …)
Recommendation: (pass / change X / test print)
```
