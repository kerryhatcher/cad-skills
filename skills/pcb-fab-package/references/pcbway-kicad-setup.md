# KiCad board setup for the PCBWay route

This reference is project-authored. It describes the PCBWay capability page for standard PCBs. The project read the page on 2026-11-26 UTC. This reference does not copy the page text.

Source page: https://www.pcbway.com/capabilities.html

## Status of the PCBWay profiles

- The PCBWay profiles have data only. The workflow does not run for them.
- Three commands work for a PCBWay profile:
  - `profile` checks the profile record.
  - `judge` compares one measured value with one limit.
  - `review-source` records a reading of the page by a reviewer.
- Five commands end with exit 2 for a PCBWay profile: `design`, `drawing-facts`, `supplier`, `review-gate` and `package`.
- Each stop names the profile and the command. The stop happens before the command reads a project or starts a container.
- The standalone KiCad rule files are for a person. The person runs the KiCad design rule check (DRC) manually. The workflow does not read these files. The workflow makes the same rule text from the profile.
- The copy of the source page is local evidence only. It is not in the repository.
- The page gives no order multiple and no minimum order quantity. The profiles record `service.order_multiple` as not stated, with no value.
- The page gives no cutter diameter for the outline or the cutouts.

## Source rule

The profiles fail closed. For each item, the profile uses the stricter value:

1. If the normal process of the advanced table gives a stricter value, the profile uses it.
2. Otherwise, the profile uses the value of the standard table.
3. If the standard table gives no value, the profile uses the normal process of the advanced table.

The profile notes give the standard-table values for each item that changed.

## Limit values

Each row gives its unit. Some values are in mil.

| Setting | Two-layer profile | Four-layer profile | Note |
|---|---|---|---|
| Minimum trace width | 5 mil | 5 mil | Advanced table, normal process, 35 um outer copper. Standard table: 4 mil |
| Minimum trace spacing | 6 mil | 6 mil | Advanced table, normal process, 35 um outer copper. Inner layers may use 5 mil |
| Minimum annular ring | 0.15 mm | 0.15 mm | Standard table, 6 mil |
| Minimum drill | 0.15 mm | 0.15 mm | Standard table. A hole smaller than 0.2 mm or larger than 6 mm has an extra charge |
| Copper to board edge, CNC milling | 0.25 mm | 0.25 mm | Advanced table, normal process |
| Inner hole to inner copper | not used | 7 mil | Four-layer only. Advanced table, normal process |
| Minimum board edge | 20 mm | 20 mm | Advanced table, normal process. Standard table: 3 x 3 mm |
| Minimum board thickness | 0.3 mm | 0.6 mm | Advanced table, normal process. Manual evidence only |
| Maximum board width | 508 mm | 508 mm | Advanced table, normal process |
| Maximum board height | 610 mm | 600 mm | Advanced table, normal process. The four-layer profile limits each side to 600 mm |
| Minimum slot | 0.8 mm | 0.8 mm | Non-plated slot. Advanced table, normal process |
| Minimum plated slot | 0.5 mm | 0.5 mm | Manual evidence only |
| Soldermask bridge | 4.5 mil | 4.5 mil | The stricter value. Green oil uses 4 mil |
| Silkscreen line | 0.15 mm | 0.15 mm | Manual evidence only |
| Silkscreen text height | 0.8 mm | 0.8 mm | Manual evidence only |
| Pad hole to pad hole | 16 mil | 16 mil | Manual evidence only |
| Via hole to via hole | 11 mil | 11 mil | Manual evidence only. For vias up to 0.45 mm |
| Plated half hole diameter | 0.4 mm | 0.4 mm | Manual evidence only |

Limit direction:

- A minimum is the lowest value. Set the project value at or above it.
- A maximum is the highest value. Set the project value at or below it.
- A recommendation does not change the direction of a limit. It never fails a package.

Notes on the table:

- The workflow has one minimum slot value for all slots. The profile uses 0.8 mm, the value for a non-plated slot. A plated slot of 0.5 mm or more fails this value. The profile keeps the plated value as manual evidence.
- The four-layer profile limits each side to 600 mm. A side larger than 600 mm needs an inner hole to copper spacing of 15 mil or more.
- The four-layer profile uses 5 mil and 6 mil for all layers. Inner layers may use 4 mil and 5 mil. The profile is stricter there.

## Conditions that no command examines

No workflow row reads the board thickness, the mask color or the copper weight. The profiles record the values of the page as text limits in `manual_evidence`. The stop of the PCBWay profiles is the control for these conditions.

- **Copper weight.** The profiles apply to 1 oz outer copper. The standard table gives 1 oz to 8 oz for the outer layers. The four-layer profile records the inner copper weights of the standard table. The page gives no default inner copper weight.
- **Board thickness.** The standard table gives 0.2 mm to 3.2 mm, in 13 options. The profile uses 0.3 mm or 0.6 mm as the minimum, as the table above shows. The normal process gives a maximum board thickness for each drill size. For a 0.20 mm hole, the maximum board thickness is 1.6 mm. The profile does not check the board thickness.
- **Mask color.** The standard table gives ten options, including none. The page gives no extra charge for green, red, yellow and blue. The bridge depends on the oil color. Green oil uses 4 mil when the spacing between ICs is 8 mil. Variegated or black oil uses 4.5 mil or more. The profile uses 4.5 mil for every color.

## Standard-table values replaced

The profiles replace these standard-table values with the stricter advanced values. The profile notes keep the standard values as notes.

- Maximum board size: 600 x 1200 mm (two-layer) and 560 x 1150 mm (four-layer).
- Minimum board size: 3 x 3 mm.
- Trace and space: 4 mil and 4 mil.

The profiles replace the 0.2 mm minimum board thickness of the standard table with 0.3 mm (two-layer) and 0.6 mm (four-layer).

## Vias

- The profiles do not let blind vias, buried vias or via-in-pad pass. The advanced table gives blind and buried vias only as HDI types. Keeping out via-in-pad is a project choice for the standard service.
- Through vias are the standard service. A declared `standard_through` process passes for through spans only.
- The via list is a project setting. It is data for future work.

## Pages that the profiles do not use

PCBWay has other pages. The profiles use only the capabilities page. These pages give other values:

- The tolerance page gives a drill range of 0.2 mm to 6.3 mm. It gives a board thickness of 0.4 mm to 2.4 mm and a maximum board size of 500 x 1100 mm.
- The milling page gives a minimum mill tool diameter of 0.8 mm and a standard mill tool diameter of 2.0 mm. The `supplier` command does not use this page, because it stops for PCBWay profiles.
- The soldermask page gives the IC pad spacing for a mask bridge. This is a different quantity. The profiles do not use it.

## What this part does not claim

- The repository does not approve a PCBWay package. The stop above prevents it.
- One-layer, six-layer and advanced services are out of scope.
- Copper heavier than 1 oz is out of scope.
- Cutter diameters, a substrate and a finished thickness are not in the profiles.
- The lead opens follow-up work for these facts, for the board record conditions and for the review of project settings.
