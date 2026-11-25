# OSH Park setup documentation freeze review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the documentation replacement freeze
`docs/reviews/oshpark-setup-documentation-freeze-claude.md`,
SHA-256 `5c93bcc2dfcf3ecffd79bdc0f02458b0c8eb493e389c0c33da066ae89f0e51e7`.
I reviewed the same frozen bytes as the codex review. I changed no product file.
I ran no broad suite. The retrieval compatibility revision is separate.

## Hash boundary

The freeze record hash matches the request. All seven entries in
`docs/reviews/oshpark-setup-documentation-files.sha256` pass. The command `sha256sum -c`
returned exit 0.

| File | SHA-256 |
|---|---|
| `skills/pcb-fab-package/references/oshpark-kicad-setup.md` | `91bf7ac5ecf5946dd57c1f0e72a11f3958589c69545821becbf006b118b094af` |
| `docs/reviews/oshpark-kicad-coverage-claude.md` | `f17de71173e683f7d5eaf9a45d47b7fbac0a3cb7c8de6264a498ddb30c31a3f2` |
| `skills/pcb-fab-package/SKILL.md` | `f1d6fb86537a24725ed5d0ad512731762d88d8d96971c03664ba9158a6806845` |
| `docs/reviews/proposals/oshpark-kicad-setup-corrected-claude.md` | `140a4382614f127dacdf33affe271a221637f3d4041985b3d499ded580214760` |
| `docs/reviews/proposals/sources.yaml` | `d179915dfe91152adb19d33ced9ffd339e1a57849d68486a0b59985e13ff8dcb` |
| `docs/reviews/proposals/oshpark-kicad-setup.md` | `adaa07984e3db2e7fb883e13be7ebf93d468e8ac4827f04995a3294b0bd553d0` |
| `docs/reviews/b7-workflow-evidence/test_skill_packages-doc-correction.log` | `0b86b756e912fbb29f1b70f54fc1fcd76602632b60769eebc9ea7a0980102bfc` |

The log ends with `8/8 passed`, exit 0.

## Confirmed corrections

Root's classification correction and the earlier review findings are addressed:

- **Constraints stay constraints.** The reference defines `Supplier setup constraint, not
  enforced` as a kind. The four constraints (copper to hole clearance, hole to hole
  clearance, minimum via diameter, minimum connection width) use that kind, with
  `Enforcement is manual or unimplemented`. They are not labeled as recommendations.
- **Generic safety claims are removed.** The `Limit direction` section states the allowed
  side of a minimum and a maximum only. It does not say that a larger or a smaller value is
  safer.
- **Silkscreen difference is stated.** The setup page names 5 mil. The two-layer profile
  names 3 mil for short text. The reference says the setup guidance uses 5 mil and that the
  3 mil profile record does not prove compliance with the 5 mil guidance. The coverage report
  has a `Source difference (silkscreen)` section.
- **Per-font record rule is removed.** Coverage item 10 now says to state a visual font and
  output review and not to record a font family per text item. The reference uses the visual
  review step.
- **`SKILL.md` is corrected.** It says `Every write of design, supplier, review-source and
  package stays under out/fab/`. It gives the standalone drawing commands their own
  output-root rule and says they refuse a link at `--out`. The drawing exit row names a link
  at `--out`.
- Profile and export contract are unchanged.

## Review result

The installed reference is clear, correct and free of semicolons. It separates checked
values, supplier setup constraints, true recommendations, project margins and manual steps.
It states which values the repository checks.

Minor point: the coverage report `docs/reviews/oshpark-kicad-coverage-claude.md` still uses
semicolons in items 6, 7 and 18. That file is a review artifact, not the installed reference.
If the project wants the whole documentation set in STE, remove those semicolons in a later
pass. This does not block the freeze.

## Verdict

The documentation replacement freeze is accepted. The corrections match the root
classification rule and the earlier reviews. Code and supplier profiles are unchanged. The
retrieval compatibility revision at `4dd920c6…` is a separate review.

No product edit. No broad suite.