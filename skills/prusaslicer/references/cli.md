# PrusaSlicer CLI Internals and Troubleshooting

## Raw CLI (what `slice.py` runs)

```bash
prusa-slicer --load config.ini --export-gcode --output out/part.bgcode --center 125,105 --loglevel 2 part.stl
```

| Option | Meaning |
|---|---|
| `--load FILE` | Config ini (repeatable, later wins). `slice.py` writes one flat file |
| `--key=value` (e.g. `--fill-density=40%`) | Highest-priority overrides |
| `--export-gcode` / `-g`, `--export-3mf`, `--export-stl` | Actions |
| `--output` / `-o` | Output path. Extension `.bgcode` with `binary_gcode=1` |
| `--center X,Y`, `--rotate`, `--rotate-x/-y`, `--scale`, `--duplicate N`, `--merge`, `--split`, `--cut Z` | Transforms |
| `--info` | Prints model size/volume/manifold status |
| `--help-fff` | Every print/filament/printer key with defaults |
| `--printer-profile/--print-profile/--material-profile` | Only work for presets **installed** in the datadir (see trap below) |
| `--query-printer-models`, `--query-print-filament-profiles` | JSON listings (also need an installed datadir) |
| `--datadir DIR` | Use a different config folder |

Priority: command-line keys > `--load` files > values stored in a 3MF.

### The silent-fallback trap

With a fresh or non-GUI datadir, `--printer-profile "Original Prusa MK4 Input Shaper 0.4 nozzle"` cannot find the preset. It falls back to `- default FFF -` (bed 200×200, `gcode_flavor=reprap`, 200 °C PLA, no `M862.3` model check) **and still exits 0**. Only the print profile may be applied. Always verify:

```bash
grep -E "^; (printer_model|printer_settings_id|temperature|bed_temperature) =" out.gcode
uv run slice.py info out.bgcode --keys printer_model printer_settings_id temperature
```

The "installed" state lives in `PrusaSlicer.ini` (`[vendor:PrusaResearch] model_MK4IS = 0.4; ...` plus a `[filaments]` section), which the GUI wizard writes. `slice.py` avoids all this by resolving the bundle itself.

## Profile bundle format (`PrusaResearch.ini`)

- Sections: `[vendor]` (`config_version`), `[printer_model:MK4IS]` (variants, default materials), `[printer:NAME]`, `[print:NAME]`, `[filament:NAME]`.
- Names in `*asterisks*` are abstract parents. `inherits = A; B` applies A then B, then the section's own keys.
- Compatibility: `compatible_printers_condition` (prints/filaments vs printer), `compatible_prints_condition` (filaments vs print). The expression language: `printer_notes=~/.*MK4IS.*/ and nozzle_diameter[0]==0.4 and ! nozzle_high_flow[0]`. `=~` is a full regex match.
- Locations: installed `…/share/PrusaSlicer/profiles/PrusaResearch.ini` (flatpak: `/app/share/PrusaSlicer/profiles/`), plus the GUI's updated copy `~/.config/PrusaSlicer/vendor/` (flatpak `~/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/vendor/`, macOS `~/Library/Application Support/PrusaSlicer/vendor/`, Windows `%APPDATA%\PrusaSlicer\vendor\`). `slice.py` picks the highest `config_version`.
- Upstream source: github.com/prusa3d/PrusaSlicer-settings-prusa-fff.

## Flatpak notes (Linux)

- Run: `flatpak run --command=prusa-slicer com.prusa3d.PrusaSlicer ...` (this is what `slice.py` uses).
- The sandbox only sees allowed paths. `slice.py` adds `--filesystem=<dir>` for every input/output directory automatically. When running by hand, add `--filesystem=$PWD` (or the paths you need).
- Headless works: CLI slicing needs no display.

## Binary G-code (`.bgcode`)

Prusa's libbgcode format: `GCDE` magic, blocks for file/printer/print/slicer metadata (INI text, often deflate-compressed), thumbnails (PNG/QOI), and G-code (MeatPack/heatshrink). `slice.py info` decodes the metadata blocks. Full conversion to ASCII: re-slice with `--ascii`, or open it in the PrusaSlicer G-code viewer (`prusa-slicer --gcodeviewer file.bgcode`); libbgcode (github.com/prusa3d/libbgcode) has a converter. MK4 firmware ≥ 5.1 reads `.bgcode`. Older firmware needs `--ascii`.

## Start G-code checks the MK4 performs

| Line | Check |
|---|---|
| `M862.3 P "MK4IS"` / `"MK4S"` | Printer model. MK4 vs MK4S profile mismatch warns |
| `M862.1 P0.4 A0 F0/1` | Nozzle diameter, abrasive, high-flow |
| `M862.5 P2`, `M862.6 P"Input shaper"` | G-code level / firmware features |
| `M115 U6.x` | Minimum firmware version |

## Troubleshooting

| Message / symptom | Cause | Fix |
|---|---|---|
| `All objects are outside of the print volume.` | 3MF placed off the bed, or too big | `--center 125,105`. Check size ≤ 250×210×220 |
| `Detected print stability issues: Floating bridge anchors, Loose extrusions, Long bridging extrusions` | Unsupported islands/overhangs | `--supports organic`, re-orient, add chamfers |
| `Configuration wasn't found. Check your 'datadir' value.` | Profile-name options with empty datadir | Use `slice.py` |
| `query-print-filament-profiles error: Printer profile '…' wasn't found among installed printers` | Same | Same |
| Zero-length or empty G-code | Model empty after slicing (wrong units, tiny) | Check bbox in mm |
| Unknown key warnings | Key from a newer/older PrusaSlicer | `--help-fff` for your version |
| Exit 0 but wrong printer in G-code | Silent fallback | Verification in `slice.py` catches it |
