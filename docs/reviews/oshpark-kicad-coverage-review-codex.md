# OSH Park KiCad setup coverage review (codex-skill-dev)

Date: 2026-11-15 UTC. Scope: Claude's coverage report and proposed setup text.
I changed no product file. I ran no test suite and did no new source research.

## Findings

### The report misses existing four- and six-layer profiles

The report says that no four- or six-layer profile exists.
Both profile files exist under `skills/pcb-fab-package/supplier/profiles/`.
The four-layer profile sets `service.layers` to 4.
The six-layer profile sets `service.layers` to 6.
The report must show these profiles as existing records.
It must not plan to add duplicate profiles.
It can state which service values the setup text presents and which checks the workflow applies.

### The report misses B6 zone-refill support

The B6 command supports `drc --refill-zones` and saves the refilled board.
The B6 tests include `test_refill_matches_accepted_board_and_rebinds_interface`.
The OSH Park setup text correctly tells the reader to fill zones and save before export.
The report must not say that KiCad 10 zone refill still needs measurement.
The fabrication workflow still exports the saved board and does not refill it.
State both facts. Do not imply that the fabrication workflow invokes B6.

### The layer list does not prove that Plot On All Layers is off

The setup text tells the reader not to select Plot On All Layers.
The coverage report marks this item as covered because the export command passes `--layers`.
The explicit command list does not inspect the board setting `plot_on_all_layers_selection`.
Keep the user instruction, but mark the setting as a manual step or an unmeasured check.
Do not state that the explicit list proves the saved setting is off.

### The source manifest path is incorrect

The proposed manifest path is `skills/pcb-fab-package/supplier/sources.yaml`.
The lead's final path is `skills/pcb-fab-package/sources.yaml`.
Use the final path in the coverage report and in the later retrieval plan.
Keep the hashes unset until the retrieval step records the page bytes.

## Other coverage points

The setup text maps Board Setup, copper count, design rules, the layer list, mask expansion, mask web, tenting, zones, fonts, and drill settings.
The text does not name net classes or state how named classes relate to the supplier limits.
It says paste is optional, but the requested text must state that the assembler owns paste settings.
It must separate supplier limits, OSH Park recommendations, and project margins.

The drill text names absolute origin, millimeter units, separate PTH and NPTH files, and no Y mirror.
The accepted KiCad 10 command sets the first three items.
The command does not set Y mirroring, alternate mode, or decimal zero format.
Keep those settings marked as unmeasured until retained evidence supports a statement.

The proposal keeps X2 disabled and records the difference from OSH Park's recommendation.
I found no measured compatibility reason to change the accepted export contract.
Keep the current contract.

## Hashes before and after review

The files below have the same hashes after review.
I changed no file in this table.

| File | Before review | After review |
|---|---|---|
| `docs/reviews/oshpark-kicad-coverage-claude.md` | `2c08806ed7c04219a06c08faf95fc5e48c87194a5c14fa7813e77588209b611c` | `2c08806ed7c04219a06c08faf95fc5e48c87194a5c14fa7813e77588209b611c` |
| `docs/reviews/proposals/oshpark-kicad-setup.md` | `1aa604d7954a3e2bb8ca3e1764e9a2dcdc04944b814ef846680420b1ef03b28a` | `1aa604d7954a3e2bb8ca3e1764e9a2dcdc04944b814ef846680420b1ef03b28a` |
| `docs/reviews/proposals/supplier-sources.yaml` | `dff59b737b5017259f17aed5d71267d24a3ac4d09c455c22041d880aad89ce98` | `dff59b737b5017259f17aed5d71267d24a3ac4d09c455c22041d880aad89ce98` |
| `skills/pcb-fab-package/supplier/profiles/oshpark-four-layer.yaml` | `3eaddc56d0a81d957c14c997555efaba951507092f7c504c9cf4f25f679e15f5` | `3eaddc56d0a81d957c14c997555efaba951507092f7c504c9cf4f25f679e15f5` |
| `skills/pcb-fab-package/supplier/profiles/oshpark-six-layer.yaml` | `382f67e2c3f2a79545fc6d70855c4ae52489319351dc7bd2e0f686bb776fb3f9` | `382f67e2c3f2a79545fc6d70855c4ae52489319351dc7bd2e0f686bb776fb3f9` |
| `skills/pcb-design/scripts/pcb.py` | `0928be463f6503b41d5c7ba02c076556c0ac750630da63ac8c86866cf664cabe` | `0928be463f6503b41d5c7ba02c076556c0ac750630da63ac8c86866cf664cabe` |
| `tests/test_pcb_design.py` | `242176ead31847772750c58b224933178e2e1bc265ca8245909912de87aebe6c` | `242176ead31847772750c58b224933178e2e1bc265ca8245909912de87aebe6c` |

## Verdict

Revise the coverage report before it guides setup work.
Correct the four named facts above.
Keep the accepted export contract.
Do not add or change a supplier profile without a measured source reason and both reviews.
