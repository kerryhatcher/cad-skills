# OSH Park KiCad coverage review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: `docs/reviews/oshpark-kicad-coverage-claude.md` and
`docs/reviews/oshpark-kicad-setup-root.md`. I changed no product file. I ran no broad suite.
I hold the implementation review until the replacement freeze.

## Corrections

### 4-layer and 6-layer profiles exist

The coverage report says the 4- and 6-layer tables have no profile (item 3) and
`no profile exists`. That is incorrect. The repository has all five service profiles.

Measured with `fab.check_profile` on 2026-11-15:

| Profile | Limits | Layers | Extra division key |
|---|---|---|---|
| `oshpark-single-layer` | 13 | 2 | none |
| `oshpark-two-layer` | 13 | 2 | none |
| `oshpark-two-layer-hhdc` | 13 | 2 | none |
| `oshpark-four-layer` | 14 | 4 | `plated_drill_to_internal_copper` |
| `oshpark-six-layer` | 14 | 6 | `plated_drill_to_internal_copper` |

Each profile keeps its own evidence page. The four-layer profile binds `four-layer`. The
six-layer profile binds `six-layer`.

The coverage action for item 3 stays: examine the two-layer values line by line. A new
profile is not necessary. A profile change still needs a service specification and both
reviews. The four-layer and six-layer profiles already carry the internal-copper clearance
rule.

### KiCad refill is measured in B6

The coverage report says `Measure whether kicad-cli 10 can fill zones before a plan is made`
(item 8) and lists zone fill as a gap that needs a measurement. That is incorrect.

- B6, the `pcb-design` skill, supports refill. `skills/pcb-design/scripts/pcb.py` has
  `drc --refill-zones`. The command saves the board after a whole-board comparison.
- The focused test `test_refill_matches_accepted_board_and_rebinds_interface` in
  `tests/test_pcb_design.py` covers it. The B6 final record lists the refill result.
- The `pcb-fab-package` skill has no own refill operation. A search of its Python files for
  `refill` returns no match. The supplier works on a staged copy and does not refill. That
  behavior is correct and accepted.

The remaining fabrication item is the precondition text only: fill and save the board zones
before the design export. Do not add a new refill measurement for fabrication.

### Source manifest path

The coverage report recommends `supplier/sources.yaml` and cites the packaging proposal. Root
states that the source manifest remains `skills/pcb-fab-package/sources.yaml` under the final
accepted packaging interface. I agree with root. Use `skills/pcb-fab-package/sources.yaml`.
The file is not present yet. It is the planned path.

## Agreement with the rest

- Item 9: keep the KiCad 10 Gerber route. Do not infer native KiCad 10 support from a local
  Gerber export. I agree.
- Item 13: keep the neutral export with no X2 attributes. Record the difference from the
  OSH Park recommendation. A change needs a compatibility reason and both reviews. I agree.
- Items 4, 15 and 17: measure the mask expansion, the drill alternate mode and the drill zero
  format. Do not change the export contract on a page statement alone. I agree.
- Item 11: record the `F.Silkscreen` naming difference, the KiCad 10 name. I agree.
- The proposed setup reference `skills/pcb-fab-package/references/oshpark-kicad-setup.md` and
  the manifest `skills/pcb-fab-package/sources.yaml` are the correct targets.

## Release note

I read `docs/reviews/b7-residual-publication-release-root.md`. The three corrections are in
the scope of my residual agreement. I hold the implementation review until the replacement
freeze.

## Measured command

The profile check script is retained as `oshpark-kicad-coverage-probe-pi.py` in this
directory. Command `uv run --quiet /tmp/b7-pi-profile-check.py`, exit 0.

## Verdict

The coverage map is a useful base. Correct the two false claims above and the manifest path.
Then the setup work can start as project-authored reference text. No product edit.