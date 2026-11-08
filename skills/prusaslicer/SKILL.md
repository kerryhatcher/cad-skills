---
name: prusaslicer
description: Use when slicing a model into G-code for a Prusa printer (MK4, MK4S, MK3.9, CORE One, MINI) with PrusaSlicer — choosing print/filament profiles, layer height, perimeters, infill, supports, brim, temperatures, Prusament or Jessie filament settings, binary .bgcode, print time/filament estimates, running the PrusaSlicer command line (CLI) headless, inspecting an existing .gcode/.bgcode, or sending a job to the printer via PrusaLink.
license: MIT
metadata:
  author: Kerry Hatcher
  version: "1.0.0"
  prusaslicer-version: "2.9"
---

# Slicing with PrusaSlicer (Prusa MK4 / MK4S)

## Overview

`scripts/slice.py` drives the PrusaSlicer CLI with **Prusa's official system profiles** and verifies the result. It resolves the profile bundle (`PrusaResearch.ini`, following `inherits` chains and compatibility conditions) into one flat config and slices with `--load`. It then reads the G-code back (ASCII or binary `.bgcode`) to confirm printer model, nozzle, temperatures and every override really landed. It reports time, filament and slicer warnings.

**Core principle: never trust that the CLI used the profile you named.** `prusa-slicer --printer-profile "Original Prusa MK4 ..."` silently falls back to a generic RepRap printer (200 °C PLA, no MK4 start G-code) unless the GUI previously "installed" those presets. The MK4 then refuses the file or prints it wrong. Always slice through `slice.py`, or check `printer_model` and the temperatures in the output.

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

- PrusaSlicer ≥ 2.8 (tested 2.9.7). Linux: `flatpak install flathub com.prusa3d.PrusaSlicer` (Prusa no longer ships Linux AppImages). macOS/Windows: installer from prusa3d.com. Or set `PRUSA_SLICER=/path/to/prusa-slicer`.
- The script is pure Python stdlib: `uv run <skill-dir>/scripts/slice.py ...` (`<skill-dir>` = folder of this SKILL.md).
- `slice.py find` shows which slicer and profile bundle it found (it prefers the newest bundle: the GUI's auto-updated copy over the installed one).

## Workflow

1. **Input**: an oriented, checked model from the `print-prep` skill (`.3mf` or `.stl`; STEP and OBJ also work). The slicer does not re-orient. Rotate with `--rotate/--rotate-x/--rotate-y` if needed.
2. **Pick presets** (they must be compatible with the printer):
   ```bash
   uv run <skill-dir>/scripts/slice.py profiles --printer MK4 --print "0.20mm STRUCTURAL" --filter jessie
   ```
3. **Slice**, with strength settings from the analysis:
   ```bash
   uv run <skill-dir>/scripts/slice.py slice part.3mf --printer MK4 \
       --filament "Jessie PETG" --print "0.20mm STRUCTURAL" \
       --perimeters 4 --infill 40% --set fill_pattern=gyroid -o out/part.bgcode
   ```
4. **Read the report**: `verification: OK` is required (exit ≠ 0 otherwise). Check `estimated_time` and `filament_used_g`. `SLICER:` lines such as *"Detected print stability issues: Floating bridge anchors, Long bridging extrusions…"* mean add supports (`--supports organic`), re-orient, or fix the geometry, then re-slice.
5. **Deliver**: give the user the `.bgcode` path (USB stick, or PrusaLink upload, below) and the `.ini` written beside it, which reproduces the slice exactly.

Never start a print or upload to a printer without the user's explicit go-ahead.

## Printer, print and filament presets

| Alias (`--printer`) | Preset | Notes |
|---|---|---|
| `MK4` (default), `MK4IS` | Original Prusa MK4 Input Shaper 0.4 nozzle | Stock MK4 on firmware ≥ 6 (input shaper is standard) |
| `MK4 0.6`, `MK4 HF0.6` | …Input Shaper 0.6 / HF0.6 nozzle | Other nozzles |
| `MK4S` | Original Prusa MK4S HF0.4 nozzle | MK4S ships with the 0.4 high-flow nozzle |
| `MK4S 0.4` | Original Prusa MK4S 0.4 nozzle | MK4S with a standard nozzle |
| full name | any `profiles` entry | e.g. `"Original Prusa MK4 Input Shaper 0.25 nozzle"` |

**Get the printer right.** The G-code starts with `M862.3 P "MK4IS"` / `"MK4S"` and a nozzle check (`M862.1 … F1` for high-flow). The printer warns or stops on a mismatch.

Print presets for MK4 0.4: `0.10mm FAST DETAIL`, `0.15mm SPEED|STRUCTURAL`, `0.20mm SPEED|STRUCTURAL` (MK4S adds 0.25/0.28 on HF). **STRUCTURAL** = slower perimeters (80/45 mm/s vs 170) for better layer bonding and accuracy. Use it for functional parts. SPEED is for prototypes and looks. The default here is `0.20mm STRUCTURAL`.

Filament presets (MK4: `@PGIS`/`@PG`/`@MK4`; MK4S: `@MK4S HF0.4`): the prefix is enough: `"Prusament PLA"`, `"Prusament PLA Blend"`, `"Prusament PETG"`, `"Prusament ASA"`, `"Prusament PC Blend"`, `"Jessie PLA"`, `"Jessie PETG"`.

| Filament (MK4 0.4) | Nozzle 1st/other °C | Bed 1st/other °C | Fan % | Max flow mm³/s |
|---|---|---|---|---|
| Prusament PLA | 230 / 225 | 60 / 60 | 100 | 15 |
| Prusament PLA Blend | 230 / 225 | 60 / 60 | 100 | 7.5 |
| Jessie PLA | 230 / 220 | 60 / 60 | 100 | 12 |
| Prusament PETG | 250 / 250 | 85 / 90 | 30–60 | 12 |
| Jessie PETG | 245 / 245 | 85 / 90 | 30–50 | 12 |
| Prusament ASA | 260 / 260 | 105 / 110 | 20 | 15 |
| Prusament PC Blend | 275 / 275 | 110 / 115 | 20 (off by default) | 12 |

## Settings for strength (functional parts)

| Goal | Flag / `--set` | Typical |
|---|---|---|
| Stronger walls (biggest lever) | `--perimeters N` | 4–6 (default 2) |
| Stronger/stiffer core | `--infill 40%` + `--set fill_pattern=gyroid` (or `cubic`) | 25–60%. 100% only for small, highly loaded parts |
| Thicker skins | `--set top_solid_layers=7 --set bottom_solid_layers=5` | defaults 5/4 |
| Better layer adhesion | `--set temperature=<+5..10> --set first_layer_temperature=...` | stay within the filament range |
| Less cooling (PETG/ASA) | `--set max_fan_speed=30 --set min_fan_speed=15` | |
| Supports | `--supports organic` / `grid` / `snug` / `buildplate` / `none` | organic for curved overhangs |
| Bed adhesion / warping | `--brim 5` | ASA, PC, tall/narrow parts |
| Finer layers | `--print "0.15mm STRUCTURAL"` | better Z strength and detail, ~30% slower |
| Plain-text G-code | `--ascii` | for reading/diffing. MK4 prefers `.bgcode` |

Any key from `prusa-slicer --help-fff` works with `--set key=value`. Full list with explanations: `references/settings.md`.

## Inspecting G-code

```bash
uv run <skill-dir>/scripts/slice.py info out/part.bgcode            # summary
uv run <skill-dir>/scripts/slice.py info out/part.bgcode --keys perimeters fill_density printer_model
```

Reads the metadata and embedded config of `.bgcode` (binary, deflate blocks) and `.gcode`.

## Sending to the printer (PrusaLink), only when asked

```bash
curl -fsS -X PUT -H "X-Api-Key: $PRUSALINK_KEY" -H "Overwrite: ?0" -H "Print-After-Upload: ?0" \
     --data-binary @out/part.bgcode "http://$PRINTER_IP/api/v1/files/usb/part.bgcode"   # 201 = ok, 409 = exists
```

The API key is in the printer menu: Settings → Network → PrusaLink. `Print-After-Upload: ?1` starts the print, so **confirm with the user first** and make sure the bed is clear. Prusa Connect (cloud) is an alternative via the web UI.

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Raw CLI with `--printer-profile` names | `printer_settings_id = - default FFF -`, 200 °C, MK4 rejects/mis-prints | Use `slice.py` (verifies) |
| MK4S file on an MK4 (or HF vs standard nozzle) | Printer model/nozzle warning at start | Correct `--printer` alias |
| 3MF from another tool lands off the bed | "All objects are outside of the print volume" | `slice.py` centres single objects by default. `--center X,Y` to place |
| Expecting the slicer to orient | Supports everywhere / weak part | Orient in `print-prep` first |
| Ignoring "stability issues" messages | Spaghetti, detached islands | Supports, re-orient, or change geometry |
| `fill_density=40` without `%` | Interpreted oddly | `--infill 40` (adds `%`) or `--set fill_density=40%` |
| PETG on smooth PEI without release agent | Sheet damage | Textured sheet or glue stick |
| Old profile bundle | Missing new filaments/printers | Open the GUI once (updates `vendor/`), or `--bundle path` |

## Reference files

| File | When |
|---|---|
| `references/settings.md` | Key print/filament/printer config keys, what they do, strength vs speed vs quality trade-offs |
| `references/cli.md` | Raw CLI usage, flatpak sandbox paths, profile bundle internals, binary G-code, troubleshooting |

## Bundled tools

`scripts/slice.py`: `find`, `profiles [--printer --print --filter --json]`, `config -o x.ini`, `slice inputs… [--printer --print --filament --set k=v --perimeters --infill --supports --brim --layer-height --ascii --rotate* --scale --duplicate --merge --center --json]`, `info file`. Exit 0 = sliced and verified. 1 = slicing failed or mismatch. 2 = PrusaSlicer not installed.
