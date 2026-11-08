# FEA method

## What `fea.py` does

1. It builds the CadQuery script (CQGI, thus `--set name=value` operates) or imports a STEP or BREP file. The model must be exactly one solid.
2. It meshes the solid with gmsh (OpenCASCADE kernel, Delaunay 3D, refinement at curves). It finds the CadQuery face for each gmsh surface from the centroid and the area. Thus face selectors operate on the mesh.
3. It solves linear elasticity with scikit-fem on **quadratic (P2) tetrahedra**. P2 elements do not have the shear locking of linear tetrahedra in bending. It uses a direct sparse solver up to approximately 150k DOFs. For larger models, it uses CG with an AMG preconditioner.
4. It calculates the von Mises stress, the stress normal to the layers `σ_nn = n·σ·n` (n = `--build-dir`) and the interlayer shear `|σ·n − σ_nn·n|`. It projects these values to the nodes. It shows the maximum values **away from** the support faces and load faces (at more than one element size). The list also shows the raw peaks.
5. It examines the equilibrium (reactions = −applied loads). It gives SF = min(in-plane, interlayer tension, interlayer shear).

The stiffness calculation uses isotropic linear elasticity. The **strength check** includes the anisotropy. For FDM, anisotropy has the largest effect on strength. The stiffness changes only approximately 5% to 15% with direction. But the strength across the layers is approximately ⅓.

Validation with beam theory: the cantilever deflection agrees to 0.1%, and the root bending stress agrees to 1% to 2%.

## Boundary conditions: the largest cause of errors

| Actual condition | Model | Notes |
|---|---|---|
| Bolted to a rigid wall | Fix the cylinders of the bolt holes. Use `@` to fix only the normal direction on the contact face | A fully fixed face makes the model too stiff |
| Clamped in a vise | Fix the two clamped faces | |
| On a table | `@z` on the bottom face, and one very small lateral constraint | The model cannot show lift-off (no contact) |
| Hook or pin through a hole | `--force` on the cylinder of the hole | The force is constant on the full cylinder. This is approximately conservative on the far side |
| Hand that pushes on a face | `--pressure` or `--force` on a sub-face | If the load area is small, divide the face in CadQuery |
| Symmetric part and load | Half model, `@` normal on the cut plane, half of the load | |
| Bonded or press-fit | Fix the bonded faces | |

`fea.py` cannot calculate contact, friction, bolt preload or large deflection (geometric nonlinearity). If these effects are important, refer to "Other open-source tools".

**Divide a face for a local load:** in CadQuery, cut a rectangle 0.01 mm deep into the face (or use `split`). Then the load area is a different face. Select it with `near:x,y,z`.

## Mesh convergence

- Default element size: min(shortest bbox side / 4, longest bbox side / 20). Refinement at curves: 12 elements for each 2π.
- `--convergence` solves at 2×, 1.41× and 1× the element size. The result converges if the design stress and the deflection change by less than 5%.
- The deflection converges quickly. The stress converges more slowly. At sharp re-entrant corners, the stress does not converge (singularity). This shows an actual stress concentration: add a fillet and run the analysis again.
- Keep the model below approximately 150k DOFs for a fast direct solution (a few seconds to approximately 40 s). Thin, large parts give many elements. For these parts, set `--size` explicitly. With P2 elements, a size of wall thickness / 2 or more gives good results.

## How to read the stresses

- **von Mises compared with yield**: ductile failure in the layer plane (PETG, PC). PLA is more brittle, and the SF targets include this.
- **Maximum principal stress**: tension that opens cracks. The VTU file has it as `max_principal`.
- **Layer normal stress (+)**: it causes delamination. For most FDM parts with a bad orientation, it is the governing check.
- **Peaks at the edges of supports or loads** come from ideal BCs, and the design value does not include them. But if the actual support has sharp edges, the actual part also has high stress there.
- **Deflection more than 5% of the part dimension**: linear theory is not accurate. Use the results only to compare designs, and make the design stiffer.

## Skin-only analysis (sparse infill)

For parts that you will print with low infill, do a second analysis on a hollow copy. In CadQuery: `part.shell(-skin)` with `skin = perimeters × 0.45`. For a closed shell with no faces removed, use `cq.Workplane().add(part.val().shell([], -skin))`, or make the inner cavity explicitly. This model is conservative, because it ignores the infill. The actual part is between the skin-only model and the solid model.

## How to see the results

`--vtu out/result.vtu`: open the file in **ParaView** (`flatpak install flathub org.paraview.ParaView`). Point data: `displacement`, `von_mises`, `layer_normal`, `layer_shear`, `max_principal`. Use *Warp By Vector* on the displacement, and *Clip* to see the inner areas.

## Other open-source tools (when to use them)

| Tool | Use it for |
|---|---|
| **CalculiX** (`ccx`, GPL) with **gmsh** | Contact, plasticity, large deflection, **orthotropic** materials (`*ELASTIC, TYPE=ENGINEERING CONSTANTS`), modal analysis and buckling. Industry uses it frequently. For scripts, use **PyCCX** or **pycalculix**. Debian and Ubuntu: `apt install calculix-ccx`. Other systems: conda-forge `calculix` |
| **FreeCAD FEM workbench** (uses CalculiX) | GUI setup of contact, bolts and orthotropic materials. It imports STEP files from CadQuery |
| **Code_Aster / salome_meca** | Complex nonlinear analysis, fatigue, composites |
| **Elmer FEM** | Multiphysics (thermal and structural) |
| **scikit-fem** directly | Custom physics in Python (`fea.py` uses scikit-fem) |

Use a more advanced tool in these conditions:

- The part uses contact or friction (clips, interference fits).
- The deflection is large (living hinges, flexures).
- The load is an impact.
- A failure can cause injury.

For FDM, also think about a test print. A test print with 2× the design load is frequently the validation with the lowest cost.

## Report template

```
Part and revision:          Material and filament brand:    Print orientation (build dir):
Load case: forces (N), location, time (short, sustained or cyclic), temperature
Supports:
Mesh: element size, nodes, converged (Δ%)?
Results: max deflection __ mm. von Mises __ MPa (SF __). Layer tension __ MPa (SF __). Layer shear __ MPa (SF __)
Governing mode, and SF compared with the target:
Assumptions and limits: (linear, no contact, solid or infill, estimated material data …)
Recommendation: (pass, change X, or test print)
```
