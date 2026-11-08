# PrusaSlicer CLI: internal operation and troubleshooting

## Raw CLI (the command that `slice.py` runs)

```bash
prusa-slicer --load config.ini --export-gcode --output out/part.bgcode --center 125,105 --loglevel 2 part.stl
```

| Option | Meaning |
|---|---|
| `--load FILE` | Configuration ini file. You can use it many times, and the last file has priority. `slice.py` writes one flat file |
| `--key=value` (for example, `--fill-density=40%`) | Settings with the highest priority |
| `--export-gcode` / `-g`, `--export-3mf`, `--export-stl` | Actions |
| `--output` / `-o` | Output path. Use the extension `.bgcode` with `binary_gcode=1` |
| `--center X,Y`, `--rotate`, `--rotate-x/-y`, `--scale`, `--duplicate N`, `--merge`, `--split`, `--cut Z` | Transformations |
| `--info` | Shows the dimensions, the volume and the manifold status of the model |
| `--help-fff` | Shows all print, filament and printer keys with their defaults |
| `--printer-profile/--print-profile/--material-profile` | These options operate only for presets that are **installed** in the datadir (refer to the risk below) |
| `--query-printer-models`, `--query-print-filament-profiles` | JSON lists (these options also operate only with an installed datadir) |
| `--datadir DIR` | Use a different configuration folder |

Priority: command-line keys > `--load` files > values in a 3MF file.

### Risk: the CLI uses a default printer and shows no error

With a new datadir, or a datadir that the GUI did not set up, `--printer-profile "Original Prusa MK4 Input Shaper 0.4 nozzle"` cannot find the preset. Then the CLI uses `- default FFF -` (bed 200×200, `gcode_flavor=reprap`, 200 °C PLA, no `M862.3` model check). **The exit status is still 0.** The CLI possibly applies only the print profile. Always examine the output:

```bash
grep -E "^; (printer_model|printer_settings_id|temperature|bed_temperature) =" out.gcode
uv run slice.py info out.bgcode --keys printer_model printer_settings_id temperature
```

The "installed" status is in `PrusaSlicer.ini` (`[vendor:PrusaResearch] model_MK4IS = 0.4` and other lines, and a `[filaments]` section). The GUI wizard writes this file. `slice.py` prevents this problem, because it reads the bundle itself.

## Format of the profile bundle (`PrusaResearch.ini`)

- Sections: `[vendor]` (`config_version`), `[printer_model:MK4IS]` (variants, default materials), `[printer:NAME]`, `[print:NAME]`, `[filament:NAME]`.
- Names in `*asterisks*` are abstract parents. `inherits = A; B` applies A, then B, then the keys of the section.
- Compatibility: `compatible_printers_condition` (prints and filaments compared with the printer) and `compatible_prints_condition` (filaments compared with the print). The expression language: `printer_notes=~/.*MK4IS.*/ and nozzle_diameter[0]==0.4 and ! nozzle_high_flow[0]`. `=~` is a full regex match.
- Locations:
  - Installed copy: `…/share/PrusaSlicer/profiles/PrusaResearch.ini` (flatpak: `/app/share/PrusaSlicer/profiles/`).
  - Copy that the GUI updates: `~/.config/PrusaSlicer/vendor/` (flatpak `~/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/vendor/`, macOS `~/Library/Application Support/PrusaSlicer/vendor/`, Windows `%APPDATA%\PrusaSlicer\vendor\`).
  - `slice.py` uses the bundle with the highest `config_version`.
- Source on GitHub: github.com/prusa3d/PrusaSlicer-settings-prusa-fff.

## Flatpak (Linux)

- Run: `flatpak run --command=prusa-slicer com.prusa3d.PrusaSlicer ...` (`slice.py` uses this command).
- The sandbox sees only the paths that you permit. `slice.py` automatically adds `--filesystem=<dir>` for each input and output directory. If you run the command yourself, add `--filesystem=$PWD` (or the paths that are necessary).
- The CLI operates with no screen.

## Binary G-code (`.bgcode`)

The Prusa libbgcode format has these parts:

- The `GCDE` magic number.
- Blocks for the metadata of the file, printer, print and slicer (INI text, frequently deflate-compressed).
- Thumbnails (PNG or QOI).
- The G-code (MeatPack or heatshrink).

`slice.py info` decodes the metadata blocks. To get full ASCII G-code, slice again with `--ascii`. As an alternative, open the file in the PrusaSlicer G-code viewer (`prusa-slicer --gcodeviewer file.bgcode`). libbgcode (github.com/prusa3d/libbgcode) has a converter. MK4 firmware 5.1 and more recent versions read `.bgcode`. For older firmware, use `--ascii`.

## Checks in the start G-code of the MK4

| Line | Check |
|---|---|
| `M862.3 P "MK4IS"` / `"MK4S"` | Printer model. If the profile is for an MK4 and the printer is an MK4S (or the opposite), the printer shows a warning |
| `M862.1 P0.4 A0 F0/1` | Nozzle diameter, abrasive nozzle, high-flow nozzle |
| `M862.5 P2`, `M862.6 P"Input shaper"` | G-code level and firmware features |
| `M115 U6.x` | Minimum firmware version |

## Troubleshooting

| Message or symptom | Cause | Repair |
|---|---|---|
| `All objects are outside of the print volume.` | The 3MF puts the part off the bed, or the part is too large | `--center 125,105`. Make sure that the dimensions are 250×210×220 or less |
| `Detected print stability issues: Floating bridge anchors, Loose extrusions, Long bridging extrusions` | Islands or overhangs with no support | `--supports organic`, turn the part, add chamfers |
| `Configuration wasn't found. Check your 'datadir' value.` | Options with profile names and an empty datadir | Use `slice.py` |
| `query-print-filament-profiles error: Printer profile '…' wasn't found among installed printers` | The same cause | The same repair |
| G-code with a length of 0, or empty G-code | The model is empty after slicing (incorrect units, very small model) | Measure the bbox in mm |
| Warnings about unknown keys | The key is from a newer or older PrusaSlicer | Use `--help-fff` for your version |
| Exit status 0, but the G-code is for an incorrect printer | The CLI used a default printer and showed no error | The check in `slice.py` finds this problem |
