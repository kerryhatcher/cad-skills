# OSH Park setup documentation correction freeze (claude-skill-dev)

Date: 2026-11-15 UTC. Frozen together for both documentation reviewers, under `oshpark-setup-correction-release-root.md`. Earlier record `b7-doc-setup-freeze-claude.md` stays as history. Code and supplier profiles unchanged.

## Changes

1. Supplier setup constraints are labeled as constraints, with manual or absent enforcement stated separately. Recommendations are kept apart.
2. Generic "larger or smaller is safer" statements are removed. Only the minimum or maximum relation is stated.
3. The silkscreen source difference is stated: the setup page names 5 mil, and the two-layer profile names 3 mil for short text.
4. The setup guidance uses 5 mil. The 3 mil profile test is not claimed to prove compliance with that guidance.
5. The profile and the export contract are unchanged. The difference is a limit of automated coverage.
6. The per-font record rule is removed from the coverage report. Fonts are a visual review step.
7. `SKILL.md` no longer claims that every write stays under `out/fab/`. The standalone drawing commands have their own output-root rule. The drawing exit row names a link at `--out`.

The reference is installed at `skills/pcb-fab-package/references/oshpark-kicad-setup.md`. The proposal copy is kept as history.

## Check

- `uv run tests/test_skill_packages.py`: 8 of 8, exit 0. Log `docs/reviews/b7-workflow-evidence/test_skill_packages-doc-correction.log`.
- STE review by the reviewers. Not run by the author with a linter in this record.

## Not claimed

- Native KiCad 10 acceptance is unconfirmed.
- The four supplier setup constraints are not enforced by the code.
- The retrieval interface is not implemented. Its proposal hash is recorded below for the compatibility review.

## SHA-256

```
91bf7ac5ecf5946dd57c1f0e72a11f3958589c69545821becbf006b118b094af  skills/pcb-fab-package/references/oshpark-kicad-setup.md
f17de71173e683f7d5eaf9a45d47b7fbac0a3cb7c8de6264a498ddb30c31a3f2  docs/reviews/oshpark-kicad-coverage-claude.md
f1d6fb86537a24725ed5d0ad512731762d88d8d96971c03664ba9158a6806845  skills/pcb-fab-package/SKILL.md
140a4382614f127dacdf33affe271a221637f3d4041985b3d499ded580214760  docs/reviews/proposals/oshpark-kicad-setup-corrected-claude.md
d179915dfe91152adb19d33ced9ffd339e1a57849d68486a0b59985e13ff8dcb  docs/reviews/proposals/sources.yaml
adaa07984e3db2e7fb883e13be7ebf93d468e8ac4827f04995a3294b0bd553d0  docs/reviews/proposals/oshpark-kicad-setup.md
0b86b756e912fbb29f1b70f54fc1fcd76602632b60769eebc9ea7a0980102bfc  docs/reviews/b7-workflow-evidence/test_skill_packages-doc-correction.log
```

Retrieval proposal (compatibility revision): `4dd920c6aac29d9c94b03fff2797c1de07e90b72756e79cbb32569d0293549e5`.
