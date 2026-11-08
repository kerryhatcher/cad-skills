---
name: print-prep
description: Use when getting a part ready to 3D print (FDM, Prusa MK4/MK4S by default) — checking an STL/3MF/STEP/CadQuery model is printable, mesh repair (watertight/manifold), fitting the build volume, choosing print orientation for strength vs supports vs surface finish, overhangs, bridges, thin walls, clearances/tolerances, holes, heat-set inserts, warping, splitting large parts, and picking PLA/PETG/ASA/PC. Use before slicing and after modelling.
license: MIT
metadata:
  author: Kerry Hatcher
  version: "1.0.0"
---

# Print Preparation (FDM, Prusa MK4)

## Overview

Bridges a finished CAD model and the slicer. `scripts/printability.py` checks mesh health and build-volume fit. It ranks orientations by support volume, height, bed contact, tip-over risk and **load-across-layers**, measures wall thickness by ray casting, and writes the re-oriented mesh to slice.

**Core principle: orientation is a design decision, not a slicer afterthought.** It fixes the weak axis (layers), where supports scar the surface, and which faces come out accurate. Decide it from the part's job, then confirm strength with the `structural-analysis` skill using the same build direction.

## Environment

```bash
uv run <skill-dir>/scripts/printability.py part.stl
```

`<skill-dir>` = directory containing this SKILL.md. Accepts STL/3MF/OBJ/PLY, STEP, or a CadQuery `.py` (`--set name=value` overrides parameters).

## Workflow

1. **Know the job**: loads and their directions, mating parts, which faces are cosmetic, environment (heat/UV/outdoor), filament (default Prusament or Jessie PLA/PETG; see material choice below).
2. **Run the check**, giving the main tension or bending direction if the part is loaded:
   ```bash
   uv run <skill-dir>/scripts/printability.py part.py --load-axis x \
       --png out/orient.png -o out/part.3mf
   ```
   Read the PNG (green = bed contact, red = overhang needing support) and the table.
3. **Fix problems it reports** (exit code 3): non-watertight mesh means re-export from CAD (STEP → STL from CadQuery is always closed). Not fitting means split it or check units (inches?). Thin walls mean thicken to ≥ 2 line widths (0.9 mm on a 0.4 nozzle).
4. **Choose the orientation** using the priority list below. The ranked table is a starting point, not the answer. `--orientation "rx=90,rz=30"` evaluates and exports any specific rotation.
5. **Design-for-FDM pass** on the CAD (see `references/dfam.md`): chamfer bed edges (elephant foot), teardrop or bridge horizontal holes, 45° chamfers instead of downward fillets, clearances, insert holes. Re-run.
6. **Strength check**: pass the printed `build_dir_model` to `structural-analysis` → `fea.py --build-dir ...`.
7. **Export** the oriented model (`-o part.3mf`, centred, on z=0) and hand it to the `prusaslicer` skill.

## Orientation priority (for functional parts)

1. **Strength**: the main tensile or bending stress runs **along** layers, never pulling them apart. Hooks, brackets, levers and snap-fit arms lie flat or on their side so the bending plane is in XY. `load-x-layers` in the table: 0 = load in-plane (good), 1 = straight across layers (bad).
2. **Accuracy of critical features**: holes and bores that need to be round are vertical (axis = Z). Flat mating faces go on the bed or upward.
3. **Bed adhesion and stability**: large flat face down. Tall and narrow (tip ratio > 3) needs a brim (5 mm) or reorienting.
4. **Supports**: minimise supported area on functional/cosmetic faces. Supports under a face leave it rough.
5. **Time**: lower height prints faster (layer count dominates).

When 1 and 4 conflict, **strength wins**: supports are cheap, a delaminated part is not.

## Reading the report

| Column | Meaning |
|---|---|
| `height` | Z extent in that orientation, roughly proportional to print time |
| `bed mm2` | Area touching the bed. < 50 mm² = adhesion risk (brim, or re-orient) |
| `overh mm2` | Down-facing area steeper than `--overhang` (default 50° from vertical = PrusaSlicer's 40° support threshold) |
| `support mm3` | Estimated support volume (overhang area × drop to bed or part below) |
| `tip` | Height / smallest footprint side. > 3 is wobbly |
| `load-x-layers` | Only with `--load-axis`: how much the load pulls across layers (0–1) |
| `build dir (model)` | Layer stacking direction in original model coords. Pass to `fea.py --build-dir` |
| wall thickness | Min and 5th percentile local thickness. Walls < 0.9 mm get < 2 perimeters |

## MK4 / MK4S quick facts

| Item | Value |
|---|---|
| Build volume | 250 × 210 × 220 mm (use ≤ 245 × 205 for brim/skirt margin) |
| Nozzle | 0.4 mm standard (MK4: brass. MK4S: 0.4 high-flow CHT). 0.25–0.8 available |
| Line width / min wall | 0.45 mm / 0.9 mm (2 perimeters). Structural ≥ 1.8 mm (4 perimeters) |
| Layer height | 0.05–0.30 mm. 0.20 mm default, 0.15 mm for detail/strength |
| Bed | Smooth or satin/textured PEI sheets, 120 °C max. No enclosure stock (ASA/PC: enclosure or draft shield) |
| Hotend max | 290 °C |

## Material choice (Prusament / Jessie)

| Need | Use |
|---|---|
| Indoor, stiff, easy, room temperature | PLA (Prusament PLA, Jessie PLA) |
| Tough, snap-fits, warm (≤ 60 °C), outdoor-ish | PETG (Prusament PETG, Jessie PETG) |
| Outdoor/UV, ≤ 85 °C | Prusament ASA (brim, enclosure helps) |
| Strongest, hot (≤ 100 °C) | Prusament PC Blend (enclosure, brim, glue stick on smooth PEI) |

PETG sticks too well to smooth PEI. Use the textured sheet or a release agent (glue stick or Windex film).

## Common mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Hook/bracket printed upright (load across layers) | Snaps along a layer line at a fraction of its strength | Lay it on its side. Check `load-x-layers` |
| Horizontal hole with round top | Drooping or support inside the hole | Teardrop or flat-top hole, or rotate so the axis is Z |
| Fillet on bottom edges | Overhang that sags, plus elephant foot | 45° chamfer (0.5–1 mm) on bed edges |
| Mating parts at nominal size | Won't fit | 0.2–0.3 mm/side sliding, 0.1 press (test coupon) |
| Model in inches or metres | Tiny or huge part | Check bbox in mm before slicing |
| Thin text/features < 0.45 mm | Vanish | ≥ 0.6 mm stroke, ≥ 0.4 mm depth |
| Large flat ASA/PC part with no brim | Warps or lifts | Brim 5–8 mm, mouse ears, enclosure, rounded corners |
| STL from a mesh-only source | Non-manifold, slicer guesses | Export from CAD, or repair and re-check |

## Reference files

| File | When |
|---|---|
| `references/dfam.md` | Design-for-FDM rules: overhangs, bridges, holes, clearances, inserts, threads, text, warping, splitting, multi-part joints |

## Bundled tools

- `scripts/printability.py`: health, fit (`--printer MK4|MK4S|COREONE|MINI|XL`), orientation ranking (`--load-axis`, `--overhang`, `--weights`, `--stable N`, `--orientation`), wall thickness (`--min-wall`, `--nozzle`), `-o` oriented STL/3MF, `--png`, `--json`. Exit 0 ok, 3 problems found.
