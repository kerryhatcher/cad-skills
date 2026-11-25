# B7 setup documentation freeze review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the setup documentation freeze
`docs/reviews/b7-doc-setup-freeze-claude.md`. I changed no product file. I ran no broad suite.
I keep the root constraint-versus-enforcement correction in this combined report.

## Hash boundary

Freeze record: `docs/reviews/b7-doc-setup-freeze-claude.md`,
SHA-256 `a3fed526c4b05a40baf2ac3a3ddd1e0ae4bdd03b807eb502a0e8f4db19e93cb8`.
The record matches the request.

All six frozen file hashes match the record:

| File | SHA-256 |
|---|---|
| `skills/pcb-fab-package/references/oshpark-kicad-setup.md` | `f755a28d19b797c954e2d8f8156cdc981cd6501a3e3831f031b7411b9aad557e` |
| `skills/pcb-fab-package/SKILL.md` | `8e6c162f5bff1b9a5093900259e018e8f59635205c1f2874f216f93dab762488` |
| `docs/reviews/oshpark-kicad-coverage-claude.md` | `6a9fbb93c7338ea120c73c31ce33f23d921a0c7255d798d4ca604cfdcf9bdb8f` |
| `docs/reviews/proposals/oshpark-kicad-setup.md` | `adaa07984e3db2e7fb883e13be7ebf93d468e8ac4827f04995a3294b0bd553d0` |
| `docs/reviews/proposals/sources.yaml` | `2c26684c6975c043ae56ad2ff046deb87904dd8feb2bb07fff410d0d5da6353f` |
| `docs/reviews/b7-workflow-evidence/test_skill_packages-docs.log` | `0b86b756e912fbb29f1b70f54fc1fcd76602632b60769eebc9ea7a0980102bfc` |

The log ends with `8/8 passed`, exit 0.

## Root classification correction (blocker)

Root states: a supplier minimum stays a constraint even when the repository does not enforce it
in code. Label the enforcement, not the requirement. Use `checked in code`, `manual evidence`
or `not implemented in code`. Do not downgrade a supplier minimum to a recommendation.

The frozen reference does not follow this rule. The `Four kinds of statement` section defines:

- `Recommendation`: the OSH Park page recommends the value. The repository does not check it.
- `Manual`: a step that the repository does not read or check.

The constraint table then labels these rows `Recommendation` only because the repository does
not check them:

| Row | Value | Current kind |
|---|---|---|
| Copper to hole clearance | 5 mil | `Recommendation` |
| Hole to hole clearance | 5 mil | `Recommendation` |
| Minimum via diameter | 20 mil | `Recommendation` |
| Minimum connection width | 6 mil | `Recommendation` |
| Silkscreen text thickness | 5 mil | `Recommendation` |

The freeze record repeats the error in `Not claimed`: `Copper-to-hole, hole-to-hole, via and
connection values are recommendations for the two-layer profile, not checked.`

These items are supplier minimums. The coverage map calls item 3 `Constraint values`. The
superseded draft lists copper-to-hole and hole-to-hole under `Supplier limits`. They stay
constraints. The table must say the source kind is a constraint and the enforcement is
`not implemented in code` or `manual evidence`. The section heading and the `Four kinds`
definitions must separate the source kind from the enforcement.

The silkscreen row needs the same treatment. The profile records a 3 mil minimum
(`silk_line_min_short_text`, manual evidence) and a 5 mil recommendation
(`silk_line_recommended`). If the OSH Park page states 5 mil as a minimum, keep that value a
constraint and state the profile difference. Do not label it a recommendation.

The same correction applies to `docs/reviews/oshpark-kicad-coverage-claude.md` (items 3, 7
and the `Recommendation` paragraph) and to the `SKILL.md` Files line, which says the
reference `separates checked values, recommendations, margins and manual steps`.

## Generic larger or smaller claims (blocker)

Root states: remove generic larger/smaller-is-safer claims. The frozen reference keeps them:

- `A minimum limit passes at and above the limit. Choose a project margin at or above it. A larger value is safer.`
- `A maximum limit passes at and below the limit. Choose a project margin at or below it. A smaller value is safer.`

Keep the pass direction. Remove the two generic safety sentences. Remove any other generic
safety claim, for example a claim that a larger value is always better.

The mask expansion sentence (`It does not recommend a larger value`) is attributed to the
page. Keep it only if the page states it, and keep the source link.

## Other findings

- **Invented font-record rule remains in the coverage doc.** The reference correctly replaces
  the per-text font record with a visual font review. The coverage doc item 10 still says
  `record the silk font family in the manual silk check`. Remove it there too.
- **Semicolons.** The reference uses a semicolon in the drill table
  (`the command does not set it; the default is not measured`). The coverage doc uses
  semicolons in items 6, 7, 10 and 18. STE rule 8.1 forbids semicolons.
- **Redundant row.** The table has both `Minimum drill` and `Minimum through hole` for the
  10 mil value. Merge them or mark the second as a duplicate.

## Confirmed final corrections

These corrections are present and correct:

- Direct links to all three official pages.
- Minimum and maximum margin direction.
- Optional tenting with the covered and exposed note.
- The native `Embed Fonts` note with the unconfirmed native KiCad 10 status.
- The selected service as the stackup authority.
- The 0 mask-web setup value separated from the measured 4 mil physical web.
- The visual font review replaced the invented per-text font record in the reference.
- The table says which values the repository checks.
- The proposal is marked superseded.
- The manifest target is `skills/pcb-fab-package/sources.yaml`.

## Verdict

The documentation freeze is not accepted yet. Two corrections block it:

1. Keep every supplier minimum a constraint. Label the enforcement, not the requirement.
2. Remove the generic larger/smaller-is-safer claims.

Also remove the font-record sentence from the coverage doc and the semicolons. No profile
change and no export-contract change are necessary. I hold for the corrected freeze.