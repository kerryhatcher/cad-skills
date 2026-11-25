# OSH Park KiCad setup coverage (claude-skill-dev), corrected

Date: 2026-11-15 UTC. Review only. No frozen code changed.
Sources read on 2026-11-15 (WebFetch): the main page, the design-rules page and the Gerbers page under `https://docs.oshpark.com/design-tools/kicad/`.
Corrections follow `oshpark-kicad-coverage-review-codex.md` and `oshpark-kicad-coverage-review-pi.md`.

Status key: **C** = covered and tested in the repository. **P** = partly covered. **M** = manual step, not checked by the repository. **U** = unmeasured, no statement. **A** = accepted difference, documented, not changed.

## Facts the repository already has

- Five service profiles exist: single-layer, two-layer, two-layer-hhdc, four-layer and six-layer. The four-layer and six-layer profiles exist (service.layers 4 and 6). They carry the internal-copper clearance rule. No new profile is planned.
- `pcb-design` B6 supports `drc --refill-zones`. It refills the zones and saves the board. The focused test `test_refill_matches_accepted_board_and_rebinds_interface` covers it.
- The `pcb-fab-package` workflow has no fill operation. It exports the saved board and stages a copy. It does not invoke B6.

## Coverage map

| # | OSH Park item | Repository state | Status | Action |
|---|---|---|---|---|
| 1 | Board Setup: copper layers 2, 4 or 6 | Five profiles, each with its service.layers | C | none |
| 2 | Stackup values are ignored by the service | Not recorded | P | state in the setup text |
| 3 | Constraint values, two layers (6 mil clearance and track, 5 mil annular ring, 10 mil drill) | Two-layer profile limits. Four- and six-layer profiles exist | P | check the two-layer values line by line. Show the four- and six-layer values as profile-backed, not as a new profile |
| 4 | Mask expansion 2 mil, web 0 | Mask web limit only. Expansion is not recorded | P | set expansion in the setup text. Measure only the exported web through the existing mask check |
| 5 | Tent vias (optional) | Not set by the export | M | state as a manual choice |
| 6 | Solder paste | Paste layers are exported. The assembler owns paste settings | M | state that the assembler owns paste; the repository performs no paste check |
| 7 | Net classes (OSH Park default is the minimum values) | The supplier rules are generated minimum rules (`supplier_rules_text`). Named classes are project settings | P | state that every named class must stay at or above the supplier limit; whether a looser class can relax the generated rules is unmeasured |
| 8 | Fill zones and save before export. Uploads are not refilled | The fabrication workflow exports the saved board and has no fill step. B6 has `drc --refill-zones` | P | state the precondition. Point to the B6 command. Make no new refill measurement |
| 9 | Native KiCad 9.x processing and embedded fonts | The tested route is the Gerber route with KiCad 10.0.5 | A | keep the Gerber route. Native KiCad 10 acceptance is unconfirmed, not proven rejected |
| 10 | Font substitution for Gerbers | No font statement | M | state the visual font and output review as a manual step. Do not record a font family per text item |
| 11 | Layer list: F.SilkScreen (OSH Park) and F.Silkscreen (KiCad 10 name) | Contract uses the KiCad 10 names | C | note the naming difference |
| 12 | Plot On All Layers off | The export passes an explicit `--layers` list. This does not read the saved `plot_on_all_layers_selection` setting | M | keep the user instruction. Mark as a manual check. Do not state that the explicit list proves the saved setting is off |
| 13 | X2 recommended | Contract `x2: false` (neutral export) | A | keep. Record the difference. A change needs a compatibility reason and both reviews |
| 14 | Drill: Mirror Y off | Not set by the command. The default is not measured here | U | measure the default before a statement |
| 15 | Drill: alternate drill mode on | Not set by the command | U | measure the KiCad 10 option and its effect on slots |
| 16 | Drill: absolute origin | `--drill-origin absolute` | C | none |
| 17 | Drill: decimal zero format preferred | The command uses `suppressleading` | U | measure the decimal option. Do not change the contract on a page statement |
| 18 | Drill units; separate PTH and NPTH | `-u mm` and `--excellon-separate-th` | C | none |
| 19 | Drill options that prevent slot detection | Slot inspection reads the separate drill files | P | test once with the chosen options |
| 20 | KiCad 7 drill-handling note | Not applicable to the Gerber route | A | record only |
| 21 | Source links and dates | Not in the repository | M | add the manifest entries below |

## Release state of the setup files

1. The project-authored setup reference is installed at `skills/pcb-fab-package/references/oshpark-kicad-setup.md`. It is linked from `skills/pcb-fab-package/SKILL.md`. The corrected text is in the documentation freeze `docs/reviews/oshpark-setup-documentation-freeze-2-claude.md`.
2. The earlier draft `docs/reviews/proposals/oshpark-kicad-setup.md` is superseded. The corrected proposal `docs/reviews/proposals/oshpark-kicad-setup-corrected-claude.md` is kept as history of the installed text.
3. The three source entries are a proposal at `docs/reviews/proposals/sources.yaml`. Their target is `skills/pcb-fab-package/sources.yaml` (skill root). They are not installed. Their hashes are `null` until a source retrieval is recorded in a source review. A candidate hash is not an accepted entry.

## Source difference (silkscreen)

The setup page names 5 mil for silkscreen text thickness. The existing two-layer profile names 3 mil for short text (`silk_line_min_short_text`), checked only by manual evidence. The setup guidance uses 5 mil. The 3 mil profile test does not prove compliance with the 5 mil guidance. This difference is a limit of automated coverage. The profile and the export contract are unchanged.

## Recommendation

Keep the export contract. The setup text is installed and states the distinctions that the reviews asked for: supplier limits, supplier setup constraints that are not enforced, true recommendations, project margins, and manual steps. The open items are measurements, not documentation: the drill items (14, 15, 17) and the slot effect (19). Do not add profiles. Do not change the export contract without a measured reason and both reviews.

## Limits

These pages were summarized from one fetch on 2026-11-15. Page text can change. The repository does not store page bytes. The coverage is not a service approval.
