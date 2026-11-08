# PrusaSlicer Settings Reference (FFF)

Set any key with `slice.py slice ... --set key=value`. Defaults below are from the Prusa MK4 Input Shaper 0.4 / `0.20mm STRUCTURAL` profile (bundle 2.4.x). The authoritative list for your version is `prusa-slicer --help-fff`.

## How the slicer builds a print

1. **Slice** the mesh into layers (`layer_height`, `first_layer_height`).
2. Per layer, **perimeters** (outer walls, `perimeters` loops, Arachne variable width), then **top/bottom solid infill** (skins), then **sparse infill** inside.
3. **Supports** under overhangs steeper than the threshold. **Bridges** span between anchors.
4. **Toolpaths** get speeds, accelerations, fan and temperatures. Then **G-code** with the printer's start/end code, and binary packing (`.bgcode`) with thumbnails and metadata.

## Layers and walls

| Key | Default | Notes |
|---|---|---|
| `layer_height` | 0.2 | 0.05–0.30 (0.4 nozzle). Thinner = better Z bonding and detail, slower |
| `first_layer_height` | 0.2 | Thicker first layer is more forgiving |
| `perimeters` | 2 | **Main strength lever.** 4–6 for structural parts |
| `perimeter_generator` | arachne | Variable-width walls. `classic` gives uniform lines |
| `extrusion_width`, `perimeter_extrusion_width`, `external_perimeter_extrusion_width` | 0.45 | Wider lines (0.5–0.6) bond better and are slightly stronger |
| `external_perimeters_first` | 0 | 1 improves dimensional accuracy, worse overhangs |
| `extra_perimeters_on_overhangs` | 0 | 1 helps steep overhangs without supports |
| `ensure_vertical_shell_thickness` | profile default | Adds solid infill so sloped walls keep full thickness |
| `seam_position` | aligned | `rear`, `nearest`, `random`. Put seams away from cosmetic and stress faces |
| `top_solid_layers` / `bottom_solid_layers` | 5 / 4 | Plus `top_solid_min_thickness` 0.7, `bottom_solid_min_thickness` 0.5 |

## Infill

| Key | Default | Notes |
|---|---|---|
| `fill_density` | 15% | Use the `%` sign. 25–60% for functional parts |
| `fill_pattern` | grid | `gyroid` (isotropic, tough), `cubic`/`adaptivecubic` (fast, 3D), `rectilinear`, `honeycomb`, `lightning` (top support only, no strength) |
| `infill_every_layers` | 1 | Thicker sparse infill. Leave 1 for strength |
| `solid_infill_below_area` | 0 | Regions smaller than this (mm²) printed solid. 5–20 strengthens small posts |
| `infill_anchor`, `infill_anchor_max` | 2, 12 mm | How far infill lines are anchored along perimeters |
| `top_fill_pattern` / `bottom_fill_pattern` | monotoniclines / monotonic | Monotonic gives nicer tops |
| `fill_angle` | 45 | Align with load for 2D parts |

## Supports

| Key | Notes |
|---|---|
| `support_material` + `support_material_auto` | Both 1 = automatic supports. `support_material=1, auto=0` = enforcers only (needs painted 3MF) |
| `support_material_style` | `organic` (tree, minimal contact), `grid`, `snug` |
| `support_material_threshold` | 40 (MK4) = support surfaces sloped less than 40° from horizontal (more than 50° from vertical) |
| `support_material_buildplate_only` | 1 = never on the model |
| `support_material_contact_distance` | 0.2 mm gap: easier removal, rougher underside. 0 for soluble |
| `support_material_interface_layers` | Denser layers under the part for a better surface |
| `raft_layers` | Rarely needed on MK4 |

Supports can't be painted from the CLI. For painted supports or modifiers, prepare a 3MF in the GUI and slice that 3MF (painting is stored in it).

## Adhesion

| Key | Notes |
|---|---|
| `brim_width` | 0 default. 3–8 mm for ASA/PC/tall parts |
| `brim_type` | `outer_only`, `inner_only`, `outer_and_inner`, `no_brim` |
| `brim_separation` | 0.1 mm makes removal easier |
| `elefant_foot_compensation` | 0.2. Shrinks the first layer to counter squish |
| `skirts` | 0. MK4 profiles use the purge line instead |

## Speed (affects strength, not just time)

| Key | STRUCTURAL / SPEED |
|---|---|
| `perimeter_speed` | 80 / 170 mm/s |
| `external_perimeter_speed` | 45 / 170 |
| `infill_speed` | 120 / 200 |
| `filament_max_volumetric_speed` (`max_volumetric_speed` = 0, unlimited) | Flow cap per filament: Prusament PLA 15, PETG 12, PLA Blend 7.5 mm³/s on the standard 0.4 nozzle. HF nozzle higher |

Slower outer walls give better surface and bonding. STRUCTURAL is the strength choice.

## Filament (temperature/cooling)

| Key | Notes |
|---|---|
| `temperature`, `first_layer_temperature` | Hotter = better layer bonding, more stringing. Stay in the filament range |
| `bed_temperature`, `first_layer_bed_temperature` | |
| `min_fan_speed`, `max_fan_speed`, `fan_always_on`, `disable_fan_first_layers` | Less fan = stronger layers (PETG/ASA/PC). PLA needs fan for overhangs |
| `bridge_fan_speed` | Bridges/overhangs |
| `filament_retract_length`, `filament_retract_speed` | Stringing |
| `filament_shrinkage_compensation_xy/z` | ASA/PC shrink ~0.5–0.7%. Set for precise fits |
| `filament_density`, `filament_cost` | Used for grams/cost in the estimate |

## Output

| Key | Notes |
|---|---|
| `binary_gcode` | 1 on MK4 profiles → `.bgcode` (smaller, thumbnails, faster transfer). Needs MK4 firmware ≥ 5.1. `--ascii` sets 0 |
| `thumbnails` | 16x16/QOI, 313x173/QOI, 480x240/QOI, 380x285/PNG |
| `output_filename_format` | Ignored when `-o` is given |
| `gcode_flavor` | `marlin2` on MK4. Never change it |

## Recipes

| Part | Settings |
|---|---|
| Structural bracket / mount (PETG) | `--print "0.20mm STRUCTURAL" --perimeters 5 --infill 40% --set fill_pattern=gyroid --set top_solid_layers=6 --set bottom_solid_layers=5` |
| Stiff indoor fixture (PLA) | `--perimeters 4 --infill 30% --set fill_pattern=cubic` |
| Small highly loaded part (gear, pin) | `--print "0.15mm STRUCTURAL" --perimeters 6 --infill 100%` |
| Outdoor (ASA) | `--filament "Prusament ASA" --perimeters 4 --infill 30% --brim 5` (enclosure recommended) |
| Hot environment (PC Blend) | `--filament "Prusament PC Blend" --perimeters 5 --infill 40% --brim 6` |
| Quick prototype | `--print "0.20mm SPEED"` defaults |
| Fine detail | `--print "0.10mm FAST DETAIL"` |
