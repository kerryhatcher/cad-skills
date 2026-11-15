# B7 prerequisite trials (claude-skill-dev)

Date: 2026-11-14. Scope: bounded measurements on temporary copies with the existing image `localhost/cad-skills-pcb:b6` (ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`). No image pull. The accepted B6 files were not changed. No B7 product code was written. This record does not establish package qualification.

Temporary root (absolute): `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/prereq/` (rule cases), `.../prereq/slot/`, `.../mask/`.

Deviation: during these trials three short reads used a bare `python3` command. AGENTS.md requires `uv`. The later commands use `uv` only.

## 1. Active rule file and severity (KiCad 10.0.5, `kicad-cli pcb drc --format json`)

| Case | Setup | Exit | `track_width` violations |
|---|---|---|---|
| A | `board.kicad_dru` next to `board.kicad_pcb` (basename `board`), rule `(constraint track_width (min 1mm))` | 0 | 8 |
| B | same rule in `supplier.kicad_dru` (other basename) | 0 | 0 |
| C | as A, plus `board.design_settings.rule_severities.track_width = "ignore"` in `board.kicad_pro` | 0 | 0 |
| D | baseline, no rule file | 0 | 0 |

Measured: KiCad loads the custom rule file only when its basename matches the project basename. A severity override in the project file is read from `board.design_settings.rule_severities`. A severity of `ignore` removes the violations.

Not measured: the exclusion format (`drc_exclusions` is a list in the project file; its entry format is not measured). The staged project therefore clears the list, and the package records the effective staged file hash. A source exclusion is never removed from the source.

Outputs (sha256, first 16 characters): A `6409c4bb6ce34007`, B `9545c247ddca466d`, C `352acee78ba12077`, D `4978e72c0f68059d`.

## 2. Slot export records (`kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-zeros-format suppressleading -u mm --excellon-separate-th`)

Fixture: the B6 slot fixture (oval drill 3.2 x 2.0 mm on the non-plated mounting hole), and a copy rotated by 45 degrees with `pcbnew` (`rot.py`, container exit 0).

| Case | Record in `board-NPTH.drl` | Tool record |
|---|---|---|
| Unrotated | `X136400Y-122000G85X137600Y-122000` | `T1C2.000` |
| Rotated 45 degrees | `X136576Y-122424G85X137424Y-121576` | `T1C2.000` |

Measured: a slot is one line with two coordinate pairs joined by `G85`. Coordinates use 3:3 mm, so the increment is 0.001 mm. The endpoints are the centres of the end arcs. The tool width equals the minor dimension. The 45-degree endpoints are the centre plus and minus 0.6 mm times (cos 45, sin 45), within the coordinate rounding.

Outputs: unrotated NPTH `5cd79d14e34afa77`, rotated NPTH `8f288109d3444f56`, unrotated PTH `96f72a6a406baaee`.

Consequence for the slot tolerance: the exported coordinate precision is 0.001 mm (rounding error at most 0.0005 mm per coordinate). The comparison tolerance is therefore 0.001 mm. The earlier 0.5 mil tolerance is withdrawn. The comparison uses unordered endpoint pairs, keeps multiplicity, and keeps the plated class (PTH or NPTH file).

## 3. Mask Gerber constructs (template, `kicad-cli pcb export gerbers --layers F.Mask,B.Mask --no-x2 --precision 6`)

`board-F_Mask.gbr` (sha256 `8591b3e55894e380`): six `%AD` apertures (C and R, plus a `RoundRect` macro), one `%AM` macro, one `%LP` polarity command, twelve `D03` flashes, no `G36` regions, no `D01` strokes.

Renderer available in the image: Ghostscript (`/usr/bin/gs`) and `pdftoppm`. No Gerber renderer (`gerbv` and `pcb2gcode` are absent).

## 4. PDF commands

| Command | Exit | Output sha256 (first 16) |
|---|---|---|
| `kicad-cli sch export pdf --output /work/out/schematic.pdf /work/board.kicad_sch` | 0 | `095673fb7edf0320` |
| `kicad-cli pcb export pdf --output /work/out/fab.pdf --layers F.Fab,B.Fab,Edge.Cuts /work/board.kicad_pcb` | 0 | `ac32d98867f665bf` |
| `kicad-cli sch export pdf` with the PCB file as input (probe of the wrong input) | 3 | not produced |

Measured: the schematic PDF needs the schematic file. The fabrication PDF command accepts the layer list and exits 0. Its output is produced on the fixture only. A package may use these commands only after they are part of the fixed image and listed fixtures.

## 5. Mask geometry decision (bounded, 20-minute budget)

Selected automatic subset for the mask web: flashes of `C` (circle) and `R` (rectangle) apertures and of the `RoundRect` macro that the retained mask uses, with dark polarity only, and no regions, no strokes, no other macros and no clear polarity.

Method: exact vector distance between two shapes. For circles and rectangles the distance is the closed form. For `RoundRect` the distance is measured on the macro's exact outline. The coordinate error is the Gerber precision: six decimals in millimetres, so 0.000001 mm per coordinate. This error is far smaller than the 0.1 mil resolution the mask limit needs. A raster is not used, so no fixed cell size is needed.

Decision rule: a web is a pass when its exact minimum distance is at least the limit plus the coordinate error bound. A web below the limit fails. A web within the bound of the limit is `uncertain`, and an uncertain result never passes.

Not automatic, reported as `unsupported` with the object: regions (`G36`/`G37`), strokes (`D01`), other macros, clear polarity (`%LP C`), and any other aperture type. Manual geometry evidence is allowed only with a hashed artifact and a stated procedure.

Not yet measured: the exact distance code on a fixture. It is the next step after the release. The 3.9, 4.0 and 4.1 mil fixtures must establish this.

## 6. Status

- Measured: rule file basename and severity; slot record format and precision; PDF commands; Gerber construct inventory of the template mask.
- Not measured: exclusion format; the exact mask distance code; the slot-capable derivative; any Gerber construct beyond the template's.
- Unsupported claims: none are claimed beyond the measured subset above.

## 7. Geometry trial (Gerbonara 1.6.3, Shapely 2.2.0, temporary venv)

Setup (network used only here): `uv venv --python 3.13 <venv>` and `uv pip install --python <venv>/bin/python gerbonara shapely` in the scratchpad `geom-trial/`. Installed: gerbonara 1.6.3, numpy 2.5.4, shapely 2.2.0.

Input (retained nominal export, B6 command, unchanged): `board-F_Mask.gbr`, sha256 `8591b3e55894e380f18025c3f76bce024b29bfbd8a5457b07ead2cf67db8ea52`.

Command: `uv run --no-project --python <venv>/bin/python analyze.py <mask.gbr>` (script sha256 `571ff1fbd5bd53a8930d4e50784a69fd14eaf188a97a59f587f7b1d29ba2dc66`; output `analysis.txt` sha256 `04542dd5e091389651fa5a6d42f29fce7d843f39bcecf5b24eae44c3dc33ef62`; exit 0).

Findings:
- The 12 flashes are C (circle), R (rectangle) and RoundRect macro instances. The RoundRect macro is four corner circles of diameter 2*$1, four edge vector lines of width 2*$1, and a core outline. Its geometry is the core rectangle Minkowski-summed with a disk of radius $1.
- Exact distance between two such shapes: max(0, d_core - r1 - r2). d_core is the distance between the core boxes (a circle's core is its centre). This is exact; it adds no curve error.
- Shapely polygon approximation (quad_segs 16) agrees within 0.0011 mm for the 7.1 mm pair (3-7). That approximation error is separate from the Gerber coordinate precision (1e-6 mm). Polygon approximation is therefore not the exact method.
- The nominal export has no web below 0.65 mm (25.6 mil). The 3.9 / 4.0 / 4.1 mil rows need a constructed fixture; they are not measured here.
- Exact method selected for the RoundRect subset. Overlaps: a pair with exact gap <= 0 is a `merged_opening` candidate; a cluster of three or more overlapping flashes, or any region, is refused as unsupported (no general union analysis).

Not measured: fixtures at 3.9 / 4.0 / 4.1 mil; overlap clusters; any Gerbonara behaviour on regions or strokes beyond the template.

## 8. Source-exclusion format trial (KiCad 10.0.5, measured negative)

Candidate format (primary report, not measured on our version): `drc_exclusions` entries of the form `[serialized rule|x|y|uuid1|uuid2, comment]`, with `excluded: true` when measured with `--severity-all`.

Setup: temporary project `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/excl` (copy of rule case A: `board.kicad_dru` with a 1 mm minimum track width, which gives 8 `track_width` violations). The exclusion is written to `board.design_settings.drc_exclusions` in `board.kicad_pro` (the same section where the severity override was accepted).

Violation used (from `base.json`): `track_width`, one item, UUID `9024f436-90ab-541e-847d-e2efb7de6a0d`, position x 115.825 y 118.0 mm.

Commands (each with `--severity-all --format json`, run in `podman run --rm --pull=never --network none --security-opt label=disable -v /tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/excl:/work -w /work localhost/cad-skills-pcb:b6 kicad-cli pcb drc ...`):
- `probe.py` (baseline) sha256 `abf45b4c757434624668ae006929ef2cf196cd6816bd30e85e5cca7c5da2ee8c`: exit 0, 8 track_width violations, no excluded flags.
- `probe2.py` sha256 `ff8ae58583de221309e9156eb1a03243b1efcca6d9e38f451831a9a4b5337a68`: variants A (rule|x|y|uuid|), B (rule|x|y|uuid), C (x|y|uuid|). Each exit 0, 8 violations, 0 excluded.
- `probe3.py` sha256 `2acd64b9046825274e60f9e6832de47cce4b43fe6390347387d9352f41e6b468`: variants D (uuid repeated), E (coordinates in nanometres), F (description as rule name). Each exit 0, 8 violations, 0 excluded.

Result: none of the six forms produced `excluded: true`. CLI exit 0 does not establish that no violation exists: the violations remained in the report. The `drc_exclusions` format on KiCad 10.0.5 is therefore NOT established. No exclusion claim is made. The B7 package must not rely on exclusion behaviour until a GUI-created exclusion or a verified format is measured.

Outputs (full hashes in `b7-prereq-evidence.sha256` when regenerated): `base.json`, `base-probe2`, `A/B/C` and `D/E/F` reports in `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/excl`.

## 9. Source-derived exclusion hypothesis (KiCad 10.0.5 sources, measured negative)

Sources read (raw files in scratchpad, sha256 in brackets): `pcbnew/pcb_marker.cpp` [4f6a2ff43642495c5acc88674306afe8338bfc1c9b13a441ae93da089f5f61cd], `pcbnew/drc/drc_test_provider_track_width.cpp` [63ccb7f0826f006dc7472230b7661bb6d75c857e5b2315003eddcdbb62980b10]. Source facts: the default serialization is `settingsKey|x|y|mainUUID|auxUUID` in internal integer units (nm); the track-width marker uses the straight track midpoint `(start+end)/2`, and an arc uses its start.

Test: `probe4.py` [085476adde9ab4811d54227e88a343dbc54855f4974a8258160073601aea6e90]. Segment with the violation UUID `9024f436-90ab-541e-847d-e2efb7de6a0d` in `board.kicad_pcb`: start (115.825, 118.0) mm, end (124.225, 118.0) mm, midpoint (120025000, 118000000) nm. Nil auxiliary UUID `00000000-0000-0000-0000-000000000000`.

Variants (exit 0 each, 8 track_width violations, 0 excluded):
- G: `track_width|120025000|118000000|9024f436-90ab-541e-847d-e2efb7de6a0d|00000000-0000-0000-0000-000000000000, excl-probe`
- H: `min_track_probe|120025000|118000000|9024f436-90ab-541e-847d-e2efb7de6a0d|00000000-0000-0000-0000-000000000000, excl-probe`

Result: the source-derived hypothesis is not confirmed on the image. The six earlier forms also failed. The settings key for track width on this build is not established, and no exclusion claim is made.

## 10. Corrected exclusion trial: CONFIRMED on KiCad 10.0.5 (supersedes sections 8 and 9)

Earlier candidate forms in sections 8 and 9 were INVALID for this test: the comment was appended inside the serialized string, and the target segment was found by a regex that could cross segment blocks. Their results are kept as recorded but do not represent the correct format.

Corrected method: the target segment is found with the accepted S-expression parser (`skills/pcb-design/scripts/sexp.py`, byte copy of the B6 helper). Its midpoint in integer nanometres is (120025000, 118000000). The serialized value is the five pipe fields `settingsKey|x_nm|y_nm|mainUUID|auxUUID`, and the comment is a separate array element.

Command (per variant, container `localhost/cad-skills-pcb:b6`, `--pull=never --network none`, mount `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/excl:/work`): `kicad-cli pcb drc --severity-all --format json -o /work/<name>.json /work/board.kicad_pcb`. Script: `probe5.py` (sha256 36c13fc48022b64a9fa1621f3df60e8e17166f8130a4609102072d4eada1244a).

| Variant | drc_exclusions value | Exit | track_width | excluded true | Output sha256 |
|---|---|---|---|---|---|
| I | `[["track_width|120025000|118000000|9024f436-90ab-541e-847d-e2efb7de6a0d|00000000-0000-0000-0000-000000000000", "excl-probe"]]` | 0 | 8 | 1 | c4d59514e49c545d5464a0dcf4de5c002a4468d99c49ab15c4643d3b5d0a0656 |
| K | `[["track_width|120025000|118000000|9024f436-90ab-541e-847d-e2efb7de6a0d|00000000-0000-0000-0000-000000000000"]]` | 0 | 8 | 1 | 4cae868e4b2e8ddf81396dd5eb34b06b899fa29c1b9b8eb12c6800f5e171831a |
| J (wrong key) | `[["min_track_probe|120025000|118000000|9024f436-90ab-541e-847d-e2efb7de6a0d|00000000-0000-0000-0000-000000000000", "excl-probe"]]` | 0 | 8 | 0 | 0d4511d7c9ff2387b99560941abd7d25f7e826ccc2c7ddc15807ee8464751315 |

Result: the exclusion format is CONFIRMED on KiCad 10.0.5. Exactly the violation with UUID 9024f436-90ab-541e-847d-e2efb7de6a0d (x 115.825, y 118.0) is excluded. The other seven track_width violations stay active. The settings key for track width is `track_width`. A wrong settings key does not exclude. The check script `check5.py` has sha256 3732d86b7da958f536d20d3316c4668d6a8a3dfcb849d73d161dd0c1c595f278.

Consequence for B7: the staged project may clear or keep a source exclusion as a recorded decision. The source file keeps its entries. A supplier violation not matched by an exclusion stays active, and this is measured for the one case above. The override test in r8 must use this exact format.

## 11. Mask boundary, RoundRect, refusal and staged exclusion results (2026-11-14)

- Mask boundary fixtures (3.9, 4.0, 4.1 mil), the 4 mil minimum-web setting, the round-rect macro, the oval refusal and the overlap refusal: `b7-mask-boundary-trials-claude.md`. Measured webs: 3.9000, 4.0000 and 4.1000 mil. The 4 mil setting produced regions, not a merge.
- Staged exclusion restoration: source 7 active and 1 excluded `track_width`; staged copy 8 active. The rule file hash is unchanged. Scripts use the S-expression parser for the segment (`stage-proof/stage_proof.py`).
- Evidence copy and frozen manifest: `b7-trial-evidence-r8/` and `b7-prereq-evidence-r8.sha256`. Full commands and exits: `b7-r8-command-record.md`.
- Section 5 (RoundRect distance and bound) is superseded by `b7-b8-proposal-claude-r8.md` section 6, which uses the exact Minkowski method with the derived bound 0.000003 mm.
- The 78-entry manifest `b7-prereq-evidence.sha256` stays as history.
