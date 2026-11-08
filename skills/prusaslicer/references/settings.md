# PrusaSlicer settings (FFF)

You can set all keys with `slice.py slice ... --set key=value`. The defaults below are from the Prusa MK4 Input Shaper 0.4 profile and the `0.20mm STRUCTURAL` profile (bundle 2.4.x). For the correct list for your version, use `prusa-slicer --help-fff`.

## How the slicer makes a print

1. The slicer **slices** the mesh into layers (`layer_height`, `first_layer_height`).
2. In each layer, it makes the **perimeters** (outer walls, `perimeters` loops, Arachne variable width). Then it makes the **top and bottom solid infill** (skins). Then it makes the **sparse infill** in the part.
3. It adds **supports** below overhangs that are steeper than the threshold. **Bridges** go between anchors.
4. It sets the speeds, accelerations, fan and temperatures of the **toolpaths**. Then it writes the **G-code** with the start and end code of the printer. Binary packing (`.bgcode`) adds thumbnails and metadata.

## Layers and walls

| Key | Default | Notes |
|---|---|---|
| `layer_height` | 0.2 | 0.05 to 0.30 (0.4 mm nozzle). Thinner layers give better Z bonds and smaller features, but the print is slower |
| `first_layer_height` | 0.2 | A thicker first layer is less sensitive to bed errors |
| `perimeters` | 2 | **The largest effect on strength.** Use 4 to 6 for structural parts |
| `perimeter_generator` | arachne | Walls with variable width. `classic` gives lines with a constant width |
| `extrusion_width`, `perimeter_extrusion_width`, `external_perimeter_extrusion_width` | 0.45 | Wider lines (0.5 to 0.6) bond better and are a little stronger |
| `external_perimeters_first` | 0 | 1 gives better dimensional accuracy, but worse overhangs |
| `extra_perimeters_on_overhangs` | 0 | 1 helps steep overhangs with no supports |
| `ensure_vertical_shell_thickness` | profile default | Adds solid infill, so that sloped walls keep their full thickness |
| `seam_position` | aligned | `rear`, `nearest`, `random`. Put the seams away from visible faces and faces with high stress |
| `top_solid_layers` / `bottom_solid_layers` | 5 / 4 | Also `top_solid_min_thickness` 0.7 and `bottom_solid_min_thickness` 0.5 |

## Infill

| Key | Default | Notes |
|---|---|---|
| `fill_density` | 15% | Use the `%` sign. Use 25% to 60% for functional parts |
| `fill_pattern` | grid | `gyroid` (isotropic, tough), `cubic`/`adaptivecubic` (fast, 3D), `rectilinear`, `honeycomb`, `lightning` (only to hold the top layers, no strength) |
| `infill_every_layers` | 1 | Thicker sparse infill. Keep 1 for strength |
| `solid_infill_below_area` | 0 | The slicer prints areas smaller than this value (mm²) as solid. A value of 5 to 20 makes small posts stronger |
| `infill_anchor`, `infill_anchor_max` | 2, 12 mm | The length of the infill anchors along the perimeters |
| `top_fill_pattern` / `bottom_fill_pattern` | monotoniclines / monotonic | Monotonic gives better top surfaces |
| `fill_angle` | 45 | For 2D parts, align it with the load |

## Supports

| Key | Notes |
|---|---|
| `support_material` + `support_material_auto` | Both 1: automatic supports. `support_material=1, auto=0`: only support enforcers (the 3MF must have painted areas) |
| `support_material_style` | `organic` (tree, minimum contact), `grid`, `snug` |
| `support_material_threshold` | 40 (MK4): support for surfaces at less than 40° from horizontal (more than 50° from vertical) |
| `support_material_buildplate_only` | 1: no supports on the model |
| `support_material_contact_distance` | 0.2 mm gap: easier removal, but a rougher bottom surface. Use 0 for soluble supports |
| `support_material_interface_layers` | Layers with more density below the part, for a better surface |
| `raft_layers` | Almost never necessary on the MK4 |

You cannot paint supports with the CLI. For painted supports or modifiers, prepare a 3MF in the GUI. Then slice that 3MF (the 3MF keeps the painted areas).

## Adhesion

| Key | Notes |
|---|---|
| `brim_width` | Default 0. Use 3 mm to 8 mm for ASA, PC or tall parts |
| `brim_type` | `outer_only`, `inner_only`, `outer_and_inner`, `no_brim` |
| `brim_separation` | 0.1 mm makes the removal easier |
| `elefant_foot_compensation` | 0.2. Makes the first layer smaller, to compensate for the squeezed first layer |
| `skirts` | 0. The MK4 profiles use the purge line |

## Speed (it changes the strength, not only the time)

| Key | STRUCTURAL / SPEED |
|---|---|
| `perimeter_speed` | 80 / 170 mm/s |
| `external_perimeter_speed` | 45 / 170 |
| `infill_speed` | 120 / 200 |
| `filament_max_volumetric_speed` (`max_volumetric_speed` = 0, no limit) | Maximum flow for each filament: Prusament PLA 15, PETG 12, PLA Blend 7.5 mm³/s on the standard 0.4 mm nozzle. Higher values for the HF nozzle |

Slower outer walls give a better surface and better bonds. Use STRUCTURAL for strength.

## Filament (temperature and cooling)

| Key | Notes |
|---|---|
| `temperature`, `first_layer_temperature` | Higher temperature gives better layer bonds, but more strings. Stay in the range of the filament |
| `bed_temperature`, `first_layer_bed_temperature` | |
| `min_fan_speed`, `max_fan_speed`, `fan_always_on`, `disable_fan_first_layers` | Less fan gives stronger layers (PETG, ASA, PC). PLA must have the fan for overhangs |
| `bridge_fan_speed` | Bridges and overhangs |
| `filament_retract_length`, `filament_retract_speed` | Strings |
| `filament_shrinkage_compensation_xy/z` | ASA and PC shrink approximately 0.5% to 0.7%. Set it for accurate fits |
| `filament_density`, `filament_cost` | The slicer uses these values for the grams and the cost in the estimate |

## Output

| Key | Notes |
|---|---|
| `binary_gcode` | 1 on MK4 profiles → `.bgcode` (smaller, with thumbnails, faster transfer). The MK4 must have firmware 5.1 or more recent. `--ascii` sets 0 |
| `thumbnails` | 16x16/QOI, 313x173/QOI, 480x240/QOI, 380x285/PNG |
| `output_filename_format` | The slicer ignores it when you use `-o` |
| `gcode_flavor` | `marlin2` on the MK4. Do not change it |

## Examples

| Part | Settings |
|---|---|
| Structural bracket or mount (PETG) | `--print "0.20mm STRUCTURAL" --perimeters 5 --infill 40% --set fill_pattern=gyroid --set top_solid_layers=6 --set bottom_solid_layers=5` |
| Stiff fixture for indoor use (PLA) | `--perimeters 4 --infill 30% --set fill_pattern=cubic` |
| Small part with a high load (gear, pin) | `--print "0.15mm STRUCTURAL" --perimeters 6 --infill 100%` |
| Outdoor use (ASA) | `--filament "Prusament ASA" --perimeters 4 --infill 30% --brim 5` (use an enclosure) |
| Hot environment (PC Blend) | `--filament "Prusament PC Blend" --perimeters 5 --infill 40% --brim 6` |
| Fast prototype | `--print "0.20mm SPEED"` with the defaults |
| Small features | `--print "0.10mm FAST DETAIL"` |
