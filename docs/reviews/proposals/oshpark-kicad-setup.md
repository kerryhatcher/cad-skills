> Superseded: the installed reference is `skills/pcb-fab-package/references/oshpark-kicad-setup.md`. This draft is kept as history.

# Set up a board for the OSH Park Gerber route (project-authored draft)

Sources: `skills/pcb-fab-package/sources.yaml`. Read on 2026-11-15 UTC. Local toolchain: KiCad 10.0.5 with the Gerber route.

Four kinds of statement appear below. Each heading says which kind it is:

- **Supplier limit**: checked by the repository against the selected profile.
- **Recommendation**: from the OSH Park setup pages. Not checked by the repository.
- **Project margin**: a value that you choose. It must be at least the supplier limit.
- **Manual step**: the repository does not read or check this step.

CAUTION: Do not upload a native KiCad 10 board in place of the tested route. OSH Park documents native processing with KiCad 9.x. Native KiCad 10 acceptance is unconfirmed.

## 1. Board setup (recommendation)

1. Open File > Board Setup.
2. Set the copper layers to 2, 4 or 6. The service checks this value against the profile.
3. Set mask expansion to 2 mil (0.0508 mm). OSH Park does not recommend a larger value.
4. Set the solder mask web to 0.

## 2. Supplier limits, two-layer profile (supplier limit)

| Rule | Limit |
|---|---|
| Minimum clearance | 6 mil (0.1524 mm) |
| Minimum track width | 6 mil (0.1524 mm) |
| Minimum annular ring | 5 mil (0.127 mm) |
| Minimum through hole | 10 mil (0.254 mm) |
| Copper to hole clearance | 5 mil (0.127 mm) |
| Hole to hole clearance | 5 mil (0.127 mm) |
| Minimum silkscreen text thickness | 5 mil (0.127 mm) |

Four-layer and six-layer profiles exist. Their values are in their profile files. Check the values in the profile, not in this text.

## 3. Net classes (project margin)

1. Keep the Default net class at the supplier limit or above.
2. The supplier check adds generated minimum rules to the staged project. Whether a looser named class can relax them is unmeasured. Keep every named class at or above the supplier limit.
3. A named net class with a tighter value is a project margin. It is not a supplier requirement.

## 4. Zones (precondition)

1. Fill the zones (press `b`, or Edit > Fill All Zones).
2. Save the board before the export. The export reads the saved state. OSH Park does not refill an uploaded board.
3. The repository has a refill command in `pcb-design`: `drc --refill-zones`, which saves the board. The fabrication workflow has no refill step.

## 5. Solder paste (manual step)

Paste settings belong to the assembler or the stencil supplier. The repository exports the paste layers when the contract lists them. It performs no paste check.

## 6. Fonts (manual step)

Gerbers are rendered on your computer. A missing font is replaced by a fallback font. Record the font family of each silkscreen text item in the manual silk check.

## 7. Layers and export

1. Export the layers in the contract: F.Cu, B.Cu, F.Mask, B.Mask, F.Silkscreen, B.Silkscreen, Edge.Cuts. Add the inner copper layers for four and six layers. Paste is optional.
2. The repository passes an explicit layer list. This does not prove that the saved Plot On All Layers setting is off. Check that the option is unchecked in the Plot dialog (manual step).
3. The export is neutral. It does not set the X2 attributes that OSH Park recommends. This difference is accepted.

## 8. Drill files

1. Use an absolute drill origin (checked by the repository).
2. Use millimeter units (checked by the repository).
3. Write PTH and NPTH to separate files (checked by the repository).
4. Do not mirror the Y axis. The repository does not read this setting; it is unmeasured.
5. The alternate drill mode and the decimal zero format are unmeasured. Do not assume either setting.
