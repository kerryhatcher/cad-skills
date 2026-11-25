# Set up a KiCad board for the OSH Park Gerber route (corrected proposal)

Proposed replacement for `skills/pcb-fab-package/references/oshpark-kicad-setup.md`. The installed file stays frozen until both documentation reviews finish. This text corrects the root review: supplier minimums are not recommendations, and the repository does not enforce every supplier constraint.

This reference is project-authored. It summarizes three official OSH Park pages, read on 2026-11-15 UTC. It does not copy their text.

Official sources:

- Main page: https://docs.oshpark.com/design-tools/kicad/
- Design rules: https://docs.oshpark.com/design-tools/kicad/kicad-design-rules/
- Gerbers: https://docs.oshpark.com/design-tools/kicad/generating-kicad-gerbers/

## Toolchain status

- The repository tests the Gerber route with KiCad 10.0.5 and the pinned image.
- The OSH Park main page describes native board processing with KiCad 9.x.
- Native KiCad 10 acceptance is unconfirmed. It is not proven rejected. Do not treat a local KiCad 10 export as proof of native acceptance.

## Five kinds of statement

Each row in this reference has exactly one kind:

- **Checked**: the repository checks the value against the selected profile, with the code named in the table.
- **Supplier setup constraint, not enforced**: a supplier value from the OSH Park design-rule page. The repository does not enforce it. Enforcement is manual or unimplemented. This is not a recommendation.
- **True recommendation**: a value that the OSH Park page recommends, or a finding that the repository reports without failing the package.
- **Project margin**: a project value that you choose. It must stay on the allowed side of a supplier limit (see below).
- **Manual step**: a step that the repository does not read or check.

## Limit direction

- A supplier **minimum** is the lowest allowed value. Set the project value at or above it.
- A supplier **maximum** is the highest allowed value. Set the project value at or below it.
- A recommendation does not change the direction of a limit. It never fails the package.

## Board setup

1. Open File > Board Setup.
2. Set the copper layers to 2, 4 or 6. The service checks this value against the profile (checked).
3. Enter values with units, for example `0.1524mm` or `6 mil`.
4. OSH Park uses the stackup of the selected service. It ignores stackup values that you upload (manual: enter stackup values only for your own impedance work).

## Mask setup

- **Mask expansion.** The page recommends 2 mil (0.0508 mm) (true recommendation).
- **Mask web setting.** The page shows a solder mask expansion web width of 0 as its setup value (true recommendation). This is not the physical web that the service measures.
- **Measured physical web.** The repository measures the exported mask flashes. The two-layer profile requires at least 4 mil between mask openings (checked, by the mask inspector). The setup value 0 does not prove the measured web. Check the measured web.
- **Tenting.** Tenting is optional. The page says tenting is typically recommended (true recommendation). A tented via is covered and cannot be soldered. An untented via stays exposed (manual).
- **Solder paste.** The assembler or the stencil supplier owns paste settings. The repository exports the paste layers when the contract lists them. It does not check paste (manual).

## Constraint values, two-layer service

| Setting | Value | Kind | Enforcement in the repository |
|---|---|---|---|
| Minimum clearance | 6 mil (0.1524 mm) minimum | Checked | `min_space` in the generated KiCad rule |
| Minimum track width | 6 mil (0.1524 mm) minimum | Checked | `min_trace` in the generated KiCad rule |
| Minimum annular ring | 5 mil (0.127 mm) minimum | Checked | `min_annular_ring` in the generated KiCad rule |
| Minimum drill (through hole) | 10 mil (0.254 mm) minimum | Checked | `min_drill` in the generated KiCad rule |
| Edge keepout | 15 mil minimum | Checked | `edge_keepout` in the generated KiCad rule |
| Board minimum edge | 0.25 in minimum | Checked | outline check |
| Board maximum width | 16 in maximum | Checked | outline check |
| Board maximum height | 22 in maximum | Checked | outline check |
| Minimum slot size | 20 mil minimum | Checked | slot check |
| Measured mask web | 4 mil minimum | Checked | mask inspector |
| Copper count | 2, 4 or 6 | Checked | `service.layers` |
| Order quantity | a multiple of the profile value | Checked | `service.order_multiple` |
| Copper to hole clearance | 5 mil (0.127 mm) | Supplier setup constraint, not enforced. Enforcement is manual or unimplemented | none. The two-layer profile does not list this rule |
| Hole to hole clearance | 5 mil (0.127 mm) | Supplier setup constraint, not enforced. Enforcement is manual or unimplemented | none |
| Minimum via diameter | 20 mil (0.508 mm) | Supplier setup constraint, not enforced. Enforcement is manual or unimplemented | none |
| Minimum connection width | 6 mil (0.1524 mm) | Supplier setup constraint, not enforced. Enforcement is manual or unimplemented | none |
| Silkscreen text thickness | 5 mil (0.127 mm) setup guidance | Supplier setup constraint. The setup page names 5 mil. The service profile names 3 mil for short text. Use 5 mil for the setup guidance | manual evidence only (`silk_line_min_short_text`). The 3 mil profile record does not prove compliance with the 5 mil guidance |
| Silkscreen recommended line | 5 mil | True recommendation | reported as a finding, never a failure |
| Overlapping drill clearance | 5 mil | True recommendation | reported as a finding, never a failure |

The four-layer and six-layer values are in their profiles. Check those profile values, not this table. The code does not enforce the four supplier setup constraints in the table. Each one needs a manual check or a future implementation before a package relies on it.

## Net classes (project)

1. The supplier check adds generated minimum rules to the staged copy of the project.
2. Keep every named net class on the allowed side of the supplier minimum.
3. A tighter named class is a project margin. It is not a supplier requirement.
4. Whether a looser named class can relax the generated rules is not measured. Do not depend on that behavior.

## Zones (precondition)

1. Fill the zones. Press `b`, or select Edit > Fill All Zones.
2. Save the board before the export. The export reads the saved state. OSH Park does not refill an uploaded board.
3. The `pcb-design` skill has a refill command: `drc --refill-zones`. It refills the zones and saves the board.
4. The `pcb-fab-package` workflow has no refill step. It exports the saved board.

## Fonts

- **Native upload.** The OSH Park main page says to open Board Setup > Board Data > Embedded Files and enable Embed Fonts for KiCad 9.x. Native KiCad 10 acceptance is unconfirmed.
- **Gerber route (the tested route).** Gerbers are drawn on your computer. A font that is not installed is replaced by a fallback font. The shape and spacing can change.
- **Visual font and output review (manual).** Open the exported layer PDF and the silkscreen Gerber render. Compare each text item with the intended font, size and position. Record the review result in your project notes. The repository does not check fonts.

## Layers and export

1. Export the layers in the contract: F.Cu, B.Cu, F.Mask, B.Mask, F.Silkscreen, B.Silkscreen, Edge.Cuts. Add the inner copper layers for four and six layers. Paste is optional.
2. The repository passes an explicit layer list. This does not prove that the saved Plot On All Layers setting is off. Check that the option is unchecked in the Plot dialog (manual).
3. The repository export is neutral. It does not set the X2 attributes that OSH Park recommends. This difference is accepted. The export contract does not change.
4. The layer name `F.Silkscreen` is the KiCad 10 name. OSH Park uses the older name `F.SilkScreen` in its text.

## Drill files

| Setting | Repository | Kind |
|---|---|---|
| Absolute drill origin | yes, `--drill-origin absolute` | Checked by the command |
| Millimeter units | yes, `-u mm` | Checked by the command |
| Separate PTH and NPTH files | yes, `--excellon-separate-th` | Checked by the command |
| Mirror Y axis off | the command does not set it | Unmeasured |
| Alternate drill mode on | the command does not set it | Unmeasured |
| Decimal zero format | the command uses leading-zero suppression | Unmeasured |

Do not assume the unmeasured settings. Measure them on a trial board before you state them.

## Summary of what is not claimed

- Native KiCad 10 acceptance is not claimed. It is unconfirmed.
- Microvia support is not claimed.
- The four supplier setup constraints in the table are not enforced by the repository.
- Tenting, paste, Plot On All Layers and font choices are manual steps.
