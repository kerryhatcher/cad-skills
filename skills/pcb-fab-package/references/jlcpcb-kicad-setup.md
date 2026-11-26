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
- The page bytes change at each fetch. Thus `fetch_sources.py` reports the entry as `changed`. It cannot restore the stored copy. A follow-up step must make a normalized page hash.
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
| Minimum plated slot | 0.5 mm | 0.35 mm | Manual evidence only |
| Soldermask bridge | 0.13 mm | 0.13 mm | Black and white. Green and other colors use 0.10 mm |
| Silkscreen line | 0.15 mm | 0.15 mm | Manual evidence only |
| Silkscreen text height | 1.0 mm | 1.0 mm | Manual evidence only |
| Pad to silkscreen | 0.15 mm | 0.15 mm | Manual evidence only |
| Via hole to via hole | 0.2 mm | 0.2 mm | Manual evidence only |
| Pad hole to pad hole | 0.45 mm | 0.45 mm | Manual evidence only |

Limit direction:

- A minimum is the lowest value. Set the project value at or above it.
- A maximum is the highest value. Set the project value at or below it.
- A recommendation does not change the direction of a limit. It never fails a package.

Notes on the table:

- The workflow has one minimum slot value for all slots. The profile uses 1.0 mm, the value for a non-plated slot. A plated slot of 0.5 mm or 0.35 mm fails this value. The profile keeps the plated value as manual evidence.
- Where the page gives more than one value for a setting, the profile uses the safer value.

## Conditions that no command examines

The workflow reads no board thickness, no mask color and no copper weight. The profiles record the values that the page states as text limits in `manual_evidence`. No workflow row enforces them. For these conditions, the stop of the JLCPCB profiles (see above) is the control.

Do not describe a JLCPCB package from this repository as ready for production. A follow-up must add these facts to the board record first.

- **Thickness.** The page gives a minimum board dimension for thicknesses of 0.6 mm or more. The page gives manual review for a thickness below 0.6 mm. The maximum board size is 599 x 497 mm below 0.8 mm. The page gives 670 x 600 mm for two-layer and 663 x 593 mm for four-layer FR4 at 0.8 mm or more. The profile uses the lower maximum board dimension for all thicknesses.
- **Mask color.** The profile uses the bridge value for black and white. Other colors can use a smaller bridge. The profile value is larger than needed for those colors.
- **Copper weight.** The profiles apply to 1 oz finished outer copper only. The page gives larger values for trace, space, annular ring and bridge at 2 oz and heavier copper. These values are out of scope. The inner copper of the four-layer profile is 0.5 oz by default.

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
- The lead opens follow-up work for these facts, for the mask units, for the drawing facts and for the review of project settings.
