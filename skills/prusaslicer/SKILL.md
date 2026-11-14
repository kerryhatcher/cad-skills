---
name: prusaslicer
description: Use this skill to slice a model into G-code for a Prusa printer (MK4, MK4S, MK3.9, CORE One, MINI) with PrusaSlicer. Topics are print and filament profiles, layer height, perimeters, infill, supports, brim and temperatures. Other topics are Prusament and Jessie filament settings, binary .bgcode, and estimates of print time and filament. Use it to run the PrusaSlicer command line (CLI) with no GUI, or to examine a .gcode or .bgcode file. Also use it to send a print to the printer through PrusaLink.
license: MIT
metadata:
  author: Kerry Hatcher
  version: "1.0.0"
  prusaslicer-version: "2.9"
---

# Slicing with PrusaSlicer (Prusa MK4 and MK4S)

## Overview

`scripts/slice.py` runs the PrusaSlicer CLI with **the Prusa system profiles**, and makes sure that the result is correct. It does these steps:

1. It reads the profile bundle (`PrusaResearch.ini`). It uses the `inherits` chains and the compatibility conditions.
2. It writes one flat configuration file and slices with `--load`.
3. It reads the G-code (ASCII or binary `.bgcode`). It makes sure that the printer model, the nozzle, the temperatures and all your settings are in the G-code.
4. It shows the print time, the filament and the slicer warnings.

**Primary rule: do not think that the CLI used the profile that you specified.** `prusa-slicer --printer-profile "Original Prusa MK4 ..."` operates correctly only if the GUI installed these presets before. If not, the CLI uses a generic RepRap printer (200 °C PLA, no MK4 start G-code). It shows no error. Then the MK4 does not accept the file, or it prints the part incorrectly. Always slice with `slice.py`, or examine `printer_model` and the temperatures in the output.

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

- PrusaSlicer 2.8 or a more recent version (tested with 2.9.7).
  - Linux: `flatpak install flathub com.prusa3d.PrusaSlicer`. Prusa does not supply Linux AppImages.
  - macOS and Windows: use the installer from prusa3d.com.
  - As an alternative, set `PRUSA_SLICER=/path/to/prusa-slicer`.
- The script uses only the Python standard library: `uv run <skill-dir>/scripts/slice.py ...` (`<skill-dir>` is the directory of this SKILL.md).
- `slice.py find` shows the slicer and the profile bundle that it found. It uses the most recent bundle. The GUI updates its copy of the bundle, and this copy is usually more recent than the installed copy.

## Procedure

1. **Input:** use a turned and examined model from the `print-prep` skill (`.3mf` or `.stl`). STEP and OBJ files are also possible. The slicer does not turn the part. If necessary, use `--rotate`, `--rotate-x` or `--rotate-y`.
2. **Select the presets.** The presets must be compatible with the printer:
   ```bash
   uv run <skill-dir>/scripts/slice.py profiles --printer MK4 --print "0.20mm STRUCTURAL" --filter jessie
   ```
3. **Slice the part,** with the strength settings from the analysis:
   ```bash
   uv run <skill-dir>/scripts/slice.py slice part.3mf --printer MK4 \
       --filament "Jessie PETG" --print "0.20mm STRUCTURAL" \
       --perimeters 4 --infill 40% --set fill_pattern=gyroid -o out/part.bgcode
   ```
4. **Read the report:**
   - The report must show `verification: OK`. If not, the exit status is not 0.
   - Examine `estimated_time` and `filament_used_g`.
   - `SLICER:` lines can show problems, for example *"Detected print stability issues: Floating bridge anchors, Long bridging extrusions…"*. Then add supports (`--supports organic`), turn the part, or change the geometry. Then slice again.
5. **Give the results to the user:**
   - The path of the `.bgcode` file (for a USB drive, or for PrusaLink, below).
   - The `.ini` file next to it. This file gives the same slice again.

Do not start a print or send a file to a printer before the user tells you to do it.

## Printer, print and filament presets

| Alias (`--printer`) | Preset | Notes |
|---|---|---|
| `MK4` (default), `MK4IS` | Original Prusa MK4 Input Shaper 0.4 nozzle | Standard MK4 with firmware 6 or more recent (input shaping is standard) |
| `MK4 0.6`, `MK4 HF0.6` | …Input Shaper 0.6 / HF0.6 nozzle | Other nozzles |
| `MK4S` | Original Prusa MK4S HF0.4 nozzle | The MK4S comes with the 0.4 mm high-flow nozzle |
| `MK4S 0.4` | Original Prusa MK4S 0.4 nozzle | MK4S with a standard nozzle |
| full name | each entry from `profiles` | for example, `"Original Prusa MK4 Input Shaper 0.25 nozzle"` |

**Use the correct printer.** The G-code starts with `M862.3 P "MK4IS"` or `"MK4S"` and a nozzle check (`M862.1 … F1` for high-flow). If the printer model or the nozzle is different, the printer shows a warning or stops.

Print presets for the MK4 with a 0.4 mm nozzle: `0.10mm FAST DETAIL`, `0.15mm SPEED|STRUCTURAL`, `0.20mm SPEED|STRUCTURAL`. The MK4S adds 0.25 mm and 0.28 mm presets for the HF nozzle. **STRUCTURAL** uses lower perimeter speeds: 80/45 mm/s, not 170 mm/s. These speeds give better layer bonds and better precision. Use it for functional parts. Use SPEED for prototypes and for parts that must only look good. The default of this skill is `0.20mm STRUCTURAL`.

Filament presets (MK4: `@PGIS`, `@PG` or `@MK4`. MK4S: `@MK4S HF0.4`): the first part of the name is sufficient. Examples: `"Prusament PLA"`, `"Prusament PLA Blend"`, `"Prusament PETG"`, `"Prusament ASA"`, `"Prusament PC Blend"`, `"Jessie PLA"`, `"Jessie PETG"`.

| Filament (MK4, 0.4 mm) | Nozzle, first layer / other layers (°C) | Bed, first layer / other layers (°C) | Fan (%) | Maximum flow (mm³/s) |
|---|---|---|---|---|
| Prusament PLA | 230 / 225 | 60 / 60 | 100 | 15 |
| Prusament PLA Blend | 230 / 225 | 60 / 60 | 100 | 7.5 |
| Jessie PLA | 230 / 220 | 60 / 60 | 100 | 12 |
| Prusament PETG | 250 / 250 | 85 / 90 | 30 to 60 | 12 |
| Jessie PETG | 245 / 245 | 85 / 90 | 30 to 50 | 12 |
| Prusament ASA | 260 / 260 | 105 / 110 | 20 | 15 |
| Prusament PC Blend | 275 / 275 | 110 / 115 | 20 (off by default) | 12 |

## Settings for strength (functional parts)

| Goal | Option or `--set` | Typical value |
|---|---|---|
| Stronger walls (largest effect) | `--perimeters N` | 4 to 6 (default 2) |
| Stronger and stiffer core | `--infill 40%` and `--set fill_pattern=gyroid` (or `cubic`) | 25% to 60%. Use 100% only for small parts with very high loads |
| Thicker skins | `--set top_solid_layers=7 --set bottom_solid_layers=5` | defaults 5 and 4 |
| Better layer adhesion | `--set temperature=<+5..10> --set first_layer_temperature=...` | Stay in the temperature range of the filament |
| Less cooling (PETG, ASA) | `--set max_fan_speed=30 --set min_fan_speed=15` | |
| Supports | `--supports organic` / `grid` / `snug` / `buildplate` / `none` | `organic` for curved overhangs |
| Bed adhesion, warping | `--brim 5` | ASA, PC, tall or narrow parts |
| Thinner layers | `--print "0.15mm STRUCTURAL"` | Better Z strength and smaller features, approximately 30% slower |
| G-code as text | `--ascii` | To read or compare G-code. The MK4 uses `.bgcode` by default |

All keys from `prusa-slicer --help-fff` operate with `--set key=value`. For the full list with explanations, refer to `references/settings.md`.

## How to examine G-code

```bash
uv run <skill-dir>/scripts/slice.py info out/part.bgcode            # summary
uv run <skill-dir>/scripts/slice.py info out/part.bgcode --keys perimeters fill_density printer_model
```

The command reads the metadata and the embedded configuration of `.bgcode` files (binary, deflate blocks) and `.gcode` files.

## Send a file to the printer (PrusaLink), only when the user tells you

```bash
curl -fsS -X PUT -H "X-Api-Key: $PRUSALINK_KEY" -H "Overwrite: ?0" -H "Print-After-Upload: ?0" \
     --data-binary @out/part.bgcode "http://$PRINTER_IP/api/v1/files/usb/part.bgcode"   # 201 = ok, 409 = exists
```

The API key is in the printer menu: Settings → Network → PrusaLink.

WARNING: Do not use `Print-After-Upload: ?1` before the user agrees and the bed is clear. This header starts the print immediately. The moving printer can cause injury, and the nozzle can hit loose parts.

Prusa Connect (cloud) is an alternative, through the web interface.

## Frequent errors

| Error | Symptom | Repair |
|---|---|---|
| Raw CLI with `--printer-profile` names | `printer_settings_id = - default FFF -`, 200 °C. The MK4 does not accept the file, or prints it incorrectly | Use `slice.py` (it examines the output) |
| MK4S file on an MK4 (or HF nozzle and standard nozzle) | Warning about the printer model or the nozzle at the start | Use the correct `--printer` alias |
| 3MF from a different tool is off the bed | "All objects are outside of the print volume" | `slice.py` puts a single object at the bed center by default. Use `--center X,Y` for a different position |
| You think that the slicer turns the part | Supports in all areas, or a weak part | Turn the part in `print-prep` first |
| You ignore "stability issues" messages | Spaghetti, loose islands | Add supports, turn the part, or change the geometry |
| `fill_density=40` without `%` | The slicer can read the value incorrectly | `--infill 40` (adds `%`) or `--set fill_density=40%` |
| PETG on smooth PEI with no release agent | Damage to the sheet | Use a textured sheet or glue stick |
| Profile bundle that is not current | New filaments or printers are missing | Open the GUI one time (it updates `vendor/`), or use `--bundle path` |

## Reference files

| File | Contents |
|---|---|
| `references/settings.md` | Important configuration keys for print, filament and printer, their function, and the balance of strength, speed and quality |
| `references/cli.md` | Raw CLI, flatpak sandbox paths, the structure of the profile bundle, binary G-code, troubleshooting |

## Tools in this skill

`scripts/slice.py` has these subcommands:

- `find`
- `profiles [--printer --print --filter --json]`
- `config -o x.ini`
- `slice inputs… [--printer --print --filament --set k=v --perimeters --infill --supports --brim --layer-height --ascii --rotate* --scale --duplicate --merge --center --json]`
- `info file`

Exit status 0: sliced, and the output is correct. Exit status 1: the slice did not complete, or the output is not correct. Exit status 2: PrusaSlicer is not installed.
