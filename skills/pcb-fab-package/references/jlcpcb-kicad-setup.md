# KiCad board setup for the JLCPCB route

This reference is project-authored. It describes the JLCPCB capability page for rigid PCBs. The project read the page on 2026-11-26 UTC. This reference does not copy the page text.

Source page: https://jlcpcb.com/capabilities/pcb-capabilities

## Status of the JLCPCB profiles

- The JLCPCB profiles contain only values. The workflow does not run for them.
- Three commands work for a JLCPCB profile:
  - `profile` examines the profile record.
  - `judge` compares one measured value with one limit.
  - `review-source` records a reading of the page by a reviewer.
- Five commands end with exit 2 for a JLCPCB profile: `design`, `drawing-facts`, `supplier`, `review-gate` and `package`.
- Each stop names the profile and the command. The stop happens before the command reads a project or starts a container.
- The standalone KiCad rule files are for a person. The person runs the KiCad design rule check (DRC) manually. The workflow does not read these files. The workflow makes the same rule text from the profile.
- The stored copy of the source page is local evidence only. It is not in the repository.
- The page bytes change at each fetch. Thus `fetch_sources.py` reports the entry as `changed`. It cannot restore the stored copy. The entry has no `text_sha256`. The entry gets a `text_sha256` at the next binding of the page. Then a layout change gives only the status `layout`.
- The page gives no order multiple. The profiles record `service.order_multiple` as not stated, with no value.
- The page gives no cutter diameter for the outline or the cutouts.
- The page names more than one laminate supplier and seven thicknesses. It gives no one substrate and no one finished thickness for the service. The profiles contain none of these facts. The `notes.not_stated` list names them.

## Limit values

Each value is in millimeters. No workflow row of a JLCPCB profile examines these values. Use the `judge` command to compare one measured value with one limit. Each limit is only a value.

| Setting | Two-layer profile | Four-layer profile | Note |
|---|---|---|---|
| Minimum trace width | 0.10 mm | 0.09 mm | For 1 oz outer copper |
| Minimum trace spacing | 0.10 mm | 0.09 mm | For 1 oz outer copper |
| Minimum annular ring | 0.18 mm | 0.15 mm | Absolute minimum. Recommended: 0.25 mm (two-layer) and 0.20 mm (four-layer) |
| Minimum drill | 0.15 mm | 0.15 mm | The 0.1 mm drill is possible only for a thickness of 1 mm or less, with ENIG or OSP |
| Copper to routed edge | 0.2 mm | 0.2 mm | |
| Inner copper to plated hole | not used | 0.2 mm | Four-layer only |
| Minimum board edge | 3 mm | 3 mm | For a thickness of 0.6 mm or more |
| Maximum board width | 599 mm | 599 mm | The thinner FR4 value. It is lower than the thick FR4 value |
| Maximum board height | 497 mm | 497 mm | The thinner FR4 value |
| Minimum slot | 1.0 mm | 1.0 mm | One value for all slots (see below) |
| Minimum plated slot | 0.5 mm | 0.35 mm | Geometric test in `division.geometric_tests` |
| Soldermask bridge | 0.13 mm | 0.13 mm | Black and white. Green and other colors use 0.10 mm |
| Silkscreen line | 0.15 mm | 0.15 mm | Manual evidence with `board_sha256` and `silk_gerber_sha256` |
| Silkscreen text height | 1.0 mm | 1.0 mm | Manual evidence with `board_sha256` and `silk_gerber_sha256` |
| Pad to silkscreen | 0.15 mm | 0.15 mm | Manual evidence with `board_sha256` and `silk_gerber_sha256` |
| Via hole to via hole | 0.2 mm | 0.2 mm | Geometric test in `division.geometric_tests` |
| Pad hole to pad hole | 0.45 mm | 0.45 mm | Geometric test in `division.geometric_tests` |

Limit direction:

- A minimum is the lowest value. Set the project value at or above it.
- A maximum is the highest value. Set the project value at or below it.
- A recommendation does not change the direction of a limit. It never fails a package.

Notes on the table:

- The workflow has one minimum slot value for all slots (`1.0 mm`) and a plated slot minimum (`0.5 mm` or `0.35 mm`) in `division.geometric_tests`.
- Where the page gives more than one value for a setting, the profile uses the safer value.

## Structured options and manual conditions

The JLCPCB profiles include `fabrication_options` for copper weight, board thickness and mask color. The workflow compares these options with `board.yaml` and `${PROJECT}/manufacturing/supplier.yaml`. The stop of the JLCPCB profiles stays active until phase 5.

- **Thickness.** `mechanical.thickness_mm` in `board.yaml` must match `fabrication_options.board_thickness.allowed_mm` (`0.4` to `2.0 mm`). A board thinner than `0.6 mm` keeps the status `pending` for manual review. `drawing_facts` reads `mechanical.thickness_mm` and `extensions.fabrication.substrate` from `board.yaml`.
- **Mask color.** `extensions.fabrication.mask_color` in `board.yaml` must name an allowed color (`green`, `red`, `yellow`, `blue`, `purple`, `black` or `white`). Missing or `unconfirmed` values keep the row `pending`. The workflow checks `mask_web_min` against `bridge_min_by_color`.
- **Copper weight.** `extensions.fabrication.copper_outer_oz` must be `1`. The four-layer profile also checks `extensions.fabrication.copper_inner_oz` against `0.5`. Missing or `unconfirmed` values keep the row `pending`. The profiles keep the text limits as recommendation notes.
- **Manual minimums.** `silk_line_min_short_text`, `silk_text_min_height`, `pad_to_silk_min` and `pth_hole_to_internal_copper` (four-layer) use `manual-evidence` JSON records passed through `--manual`.

## Vias

- The profiles refuse blind vias, buried vias and the via-in-pad process with epoxy or copper paste. The page names these as advanced options or as other processes.
- Through vias are the standard service. A declared `standard_through` process passes for through spans only.
- The via list is a project setting. It is data for later work.

## Board setup

1. Select the profile for the copper layer count: two layers or four layers.
2. Use 1 oz outer copper. The profiles do not apply to heavier copper.
3. Enter the values with units, for example `0.1 mm`. Use the table above.
4. For a black or white mask, use the 0.13 mm bridge. For another mask color, the bridge can be 0.10 mm. The profile value is 0.13 mm for every color. That value is larger than needed for the other colors.
5. Keep the board within 599 mm by 497 mm. This is the lower maximum for all thicknesses.

## What this part does not claim

- The repository does not approve a JLCPCB package. The stop above prevents it.
- One-layer and six-layer services are out of scope.
- Copper heavier than 1 oz is out of scope.
- Cutter diameters, a substrate and a finished thickness are not in the profiles.
- The lead opens follow-up work for these facts, for the drawing facts and for the review of project settings.
