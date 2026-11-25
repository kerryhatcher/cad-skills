# OSH Park setup documentation freeze 2 (claude-skill-dev)

Date: 2026-11-15 UTC. Supersedes the freeze `oshpark-setup-documentation-freeze-claude.md`, which stays as history. Covers the documentation set only. Code and supplier profiles unchanged.

## Change from freeze 1

The coverage report `docs/reviews/oshpark-kicad-coverage-claude.md` now states the release state. The setup reference is installed and linked from `SKILL.md`. The earlier draft is superseded. The corrected proposal is history of the installed text. The three source entries are a proposal, not installed, with `sha256: null` candidates. The recommendation no longer asks for a future documentation batch. The open items are measurements only.

## Check

- `uv run tests/test_skill_packages.py`: 8 of 8, exit 0. Log `docs/reviews/b7-workflow-evidence/test_skill_packages-doc-correction.log`. The check ran before the coverage report edit. It does not check the report text, and no test covers that release state.
- The reviewers examine the hashes below.

## Not claimed

- Native KiCad 10 acceptance is unconfirmed.
- The four supplier setup constraints are not enforced by the code.
- The retrieval interface is not implemented. Its proposal hash is recorded separately.

## SHA-256

```
91bf7ac5ecf5946dd57c1f0e72a11f3958589c69545821becbf006b118b094af  skills/pcb-fab-package/references/oshpark-kicad-setup.md
64cffedc7976452f72f87c5985e02166920a40cd41c65c9b3e71b458e8ef0fb4  docs/reviews/oshpark-kicad-coverage-claude.md
f1d6fb86537a24725ed5d0ad512731762d88d8d96971c03664ba9158a6806845  skills/pcb-fab-package/SKILL.md
140a4382614f127dacdf33affe271a221637f3d4041985b3d499ded580214760  docs/reviews/proposals/oshpark-kicad-setup-corrected-claude.md
d179915dfe91152adb19d33ced9ffd339e1a57849d68486a0b59985e13ff8dcb  docs/reviews/proposals/sources.yaml
adaa07984e3db2e7fb883e13be7ebf93d468e8ac4827f04995a3294b0bd553d0  docs/reviews/proposals/oshpark-kicad-setup.md
0b86b756e912fbb29f1b70f54fc1fcd76602632b60769eebc9ea7a0980102bfc  docs/reviews/b7-workflow-evidence/test_skill_packages-doc-correction.log
```

Retrieval proposal (separate freeze, not part of this set): `b2cdf367d932425f9d7914e20385034401b25bf335bdfa7cafe29a3c138796b8`.
