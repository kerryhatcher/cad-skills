---
name: print-prep
description: Use this skill to prepare a part for FDM 3D printing (by default on a Prusa MK4 or MK4S). It examines STL, 3MF, STEP or CadQuery models for printability. It finds mesh problems (watertight, manifold) and makes sure that the part is not too large for the build volume. It helps you select the print orientation for strength, supports and surface quality. It also gives rules for overhangs, bridges, thin walls, clearances, tolerances, holes and heat-set inserts. Other rules are for warping, large parts in sections, and PLA, PETG, ASA or PC. Use it after modeling and before slicing.
license: MIT
metadata:
  author: Kerry Hatcher
  version: "1.0.0"
---

# Prepare a part for printing (FDM, Prusa MK4)

## Overview

This skill is the step between a finished CAD model and the slicer. `scripts/printability.py` does these tasks:

- It examines the mesh and makes sure that the part is not too large for the build volume.
- It compares the orientations by support volume, height, bed contact area, tip-over risk and **load across the layers**.
- It measures the wall thickness with ray casting.
- It writes the turned mesh, which you can then slice.

**Primary rule: the orientation is a design decision. The slicer does not make this decision for you.** The orientation sets the weak axis (across the layers). It also sets where the supports damage the surface, and which faces are accurate. Select the orientation from the function of the part. Then calculate the strength with the `structural-analysis` skill, with the same build direction.

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

```bash
uv run <skill-dir>/scripts/printability.py part.stl
```

`<skill-dir>` is the directory that contains this SKILL.md. The tool accepts STL, 3MF, OBJ, PLY, STEP, or a CadQuery `.py` file. With a `.py` file, `--set name=value` changes the parameters.

## Procedure

1. **Learn the function of the part:**
   - The loads and their directions.
   - The mating parts.
   - The faces that must look good.
   - The environment (heat, UV, outdoor use).
   - The filament (default: Prusament or Jessie PLA or PETG). Refer to "Material selection" below.
2. **Run the check.** If the part has a load, give the direction of the primary tension or bending load:
   ```bash
   uv run <skill-dir>/scripts/printability.py part.py --load-axis x \
       --png out/orient.png -o out/part.3mf
   ```
   Read the PNG and the table. In the PNG, green shows bed contact and red shows overhangs that must have support.
3. **Repair the problems that the tool shows** (exit status 3):
   - If the mesh is not watertight, export it again from CAD. A STEP-to-STL export from CadQuery is always closed.
   - If the part is too large, divide it into sections. Also make sure that the units are correct (inches?).
   - If a wall is too thin, make it thicker. Use a minimum of 2 line widths (0.9 mm with a 0.4 mm nozzle).
4. **Select the orientation** with the list of orientation rules below. The table is a start point, not the last answer. `--orientation "rx=90,rz=30"` calculates and exports a rotation that you specify.
5. **Apply the FDM design rules** to the CAD model (refer to `references/dfam.md`):
   - Chamfer the edges on the bed (elephant foot).
   - Use a teardrop or a bridge shape for horizontal holes.
   - Use 45° chamfers, not fillets, on edges that point down.
   - Add clearances and the holes for inserts.

   Then run the check again.
6. **Calculate the strength.** Give the `build_dir_model` value from the report to `structural-analysis` (`fea.py --build-dir ...`).
7. **Export the turned model** (`-o part.3mf`, at the center, on z=0). Then use the `prusaslicer` skill.

## Orientation rules, most important first (for functional parts)

1. **Strength.** The primary tensile or bending stress must go **along** the layers. It must not pull the layers apart. Put hooks, brackets, levers and snap-fit arms flat or on their side. Then the bending plane is in XY. The `load-x-layers` column shows: 0 = load in the layer plane (good), 1 = load straight across the layers (bad).
2. **Precision of important features.** Make holes and bores vertical (axis = Z) if they must be circular. Put flat mating faces on the bed or up.
3. **Bed adhesion and a stable part.** Put the largest flat face down. A tall and narrow part (tip ratio more than 3) must have a 5 mm brim, or a different orientation.
4. **Supports.** Make the supported area on functional faces and on faces that you can see as small as possible. A face on supports becomes rough.
5. **Time.** A lower part prints faster, because the number of layers has the largest effect.

If rule 1 and rule 4 do not agree, **strength is more important**. Supports have a small cost, but a part with separated layers is not serviceable.

## How to read the report

| Column | Meaning |
|---|---|
| `height` | Z dimension in that orientation. The print time increases approximately with the height |
| `bed mm2` | The area that touches the bed. Less than 50 mm² gives a risk of bad adhesion (add a brim, or turn the part) |
| `overh mm2` | The area that points down at an angle steeper than `--overhang`. The default (50° from vertical) agrees with the 40° support threshold of PrusaSlicer |
| `support mm3` | Estimated support volume (overhang area × distance down to the bed or to the part) |
| `tip` | Height divided by the shortest side of the footprint. More than 3 is not stable |
| `load-x-layers` | Only with `--load-axis`: the fraction of the load that pulls across the layers (0 to 1) |
| `build dir (model)` | The direction of the layer stack in the initial model coordinates. Give this value to `fea.py --build-dir` |
| wall thickness | Minimum and 5th percentile of the local thickness. A wall less than 0.9 mm thick gets less than 2 perimeters |

## MK4 and MK4S data

| Item | Value |
|---|---|
| Build volume | 250 × 210 × 220 mm (use a maximum of 245 × 205 mm, to keep space for a brim or skirt) |
| Nozzle | 0.4 mm standard (MK4: brass. MK4S: 0.4 mm high-flow CHT). Nozzles from 0.25 mm to 0.8 mm are available |
| Line width and minimum wall | 0.45 mm and 0.9 mm (2 perimeters). For structural parts, 1.8 mm or more (4 perimeters) |
| Layer height | 0.05 mm to 0.30 mm. The default is 0.20 mm. Use 0.15 mm for small features or strength |
| Bed | Smooth, satin or textured PEI sheets, 120 °C maximum. The printer has no enclosure (for ASA and PC, use an enclosure or a draft shield) |
| Maximum hotend temperature | 290 °C |

## Material selection (Prusament and Jessie)

| Condition | Material |
|---|---|
| Indoor, stiff, easy to print, room temperature | PLA (Prusament PLA, Jessie PLA) |
| Tough, snap-fits, warm (maximum 60 °C), some outdoor use | PETG (Prusament PETG, Jessie PETG) |
| Outdoor and UV, maximum 85 °C | Prusament ASA (a brim and an enclosure help) |
| Highest strength, hot (maximum 100 °C) | Prusament PC Blend (enclosure, brim, glue stick on smooth PEI) |

PETG bonds too strongly to smooth PEI. Use the textured sheet or a release agent (glue stick or a layer of Windex).

## Frequent errors

| Error | Result | Repair |
|---|---|---|
| Hook or bracket printed upright (load across the layers) | It breaks along a layer line at a small fraction of its strength | Put it on its side. Examine `load-x-layers` |
| Horizontal hole with a circular top | The top of the hole sags, or the hole has support material in it | Use a teardrop or flat-top hole. As an alternative, turn the part until the axis is Z |
| Fillet on the bottom edges | The overhang sags, and the elephant foot is larger | Use a 45° chamfer (0.5 mm to 1 mm) on the edges on the bed |
| Mating parts at nominal dimension | The parts do not go together | Use 0.2 mm to 0.3 mm on each side for a sliding fit, 0.1 mm for a press fit (print a test coupon) |
| Model in inches or meters | The part is very small or very large | Measure the bbox in mm before you slice |
| Thin text or features (less than 0.45 mm) | The features are not in the print | Use a minimum stroke of 0.6 mm and a minimum depth of 0.4 mm |
| Large flat ASA or PC part with no brim | The part warps or comes off the bed | Use a 5 mm to 8 mm brim, mouse ears, an enclosure and rounded corners |
| STL from a source that has only a mesh | The mesh is not manifold, and the slicer must guess | Export from CAD, or repair the mesh and examine it again |

## Reference files

| File | Contents |
|---|---|
| `references/dfam.md` | FDM design rules: overhangs, bridges, holes, clearances, inserts, threads, text, warping, parts in sections, joints between parts |

## Tools in this skill

- `scripts/printability.py`:
  - Mesh health and fit (`--printer MK4|MK4S|COREONE|MINI|XL`).
  - It compares the orientations (`--load-axis`, `--overhang`, `--weights`, `--stable N`, `--orientation`).
  - Wall thickness (`--min-wall`, `--nozzle`).
  - Output: turned STL or 3MF (`-o`), `--png`, `--json`.
  - Exit status 0: no problems. Exit status 3: the tool found problems.
