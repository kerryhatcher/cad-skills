# OSH Park setup documentation freeze (claude-skill-dev)

Date: 2026-11-15 UTC. Separate from the publication freezes. Documentation only. No profile, export-contract or code change.

## Scope

- Installed reference `skills/pcb-fab-package/references/oshpark-kicad-setup.md`. Direct links to all three official pages. Margin direction for minimum and maximum limits. Optional tenting. Native Embed Fonts guidance with native KiCad 10 status unconfirmed. The statement that OSH Park uses the selected service stackup. A visual font and output review, which replaces the invented per-text font record. The 0 mask-web recommendation is separated from the measured 4 mil physical web. Each table row says whether the repository checks it.
- Link in `skills/pcb-fab-package/SKILL.md` (Files section).
- Coverage report `docs/reviews/oshpark-kicad-coverage-claude.md` (corrected).
- Draft `docs/reviews/proposals/oshpark-kicad-setup.md` marked superseded.
- Manifest draft `docs/reviews/proposals/sources.yaml` (target `skills/pcb-fab-package/sources.yaml`). Hashes are `null`.

## Check

- `uv run tests/test_skill_packages.py`: 8 of 8, exit 0. Log `docs/reviews/b7-workflow-evidence/test_skill_packages-docs.log`.

## Not claimed

- Native KiCad 10 acceptance is unconfirmed, not rejected.
- Mirror, alternate drill mode and decimal zero format are unmeasured.
- Copper-to-hole, hole-to-hole, via and connection values are recommendations for the two-layer profile, not checked.
- Source page bytes are not retrieved. Hashes are unset.

## SHA-256

```
f755a28d19b797c954e2d8f8156cdc981cd6501a3e3831f031b7411b9aad557e  skills/pcb-fab-package/references/oshpark-kicad-setup.md
8e6c162f5bff1b9a5093900259e018e8f59635205c1f2874f216f93dab762488  skills/pcb-fab-package/SKILL.md
6a9fbb93c7338ea120c73c31ce33f23d921a0c7255d798d4ca604cfdcf9bdb8f  docs/reviews/oshpark-kicad-coverage-claude.md
adaa07984e3db2e7fb883e13be7ebf93d468e8ac4827f04995a3294b0bd553d0  docs/reviews/proposals/oshpark-kicad-setup.md
2c26684c6975c043ae56ad2ff046deb87904dd8feb2bb07fff410d0d5da6353f  docs/reviews/proposals/sources.yaml
0b86b756e912fbb29f1b70f54fc1fcd76602632b60769eebc9ea7a0980102bfc  docs/reviews/b7-workflow-evidence/test_skill_packages-docs.log
```
