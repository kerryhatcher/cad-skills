# Follow-up review of the B9/B10 interface

Date: 2026-11-15 UTC.

Reviewed file: `docs/reviews/b9-b10-interface-claude.md`.

Decision: the five corrections from my first review now appear. The interface still has two conflicts between its rules and acceptance cases.

## Required corrections

1. AC-10 says unresolved Sierra origin and rotation produce `Draft only`. Section 10 says validated output with an open qualification condition has status `unqualified`. State both stages: the generated XY file remains a draft, then package validation sets manifest status to `unqualified`.
2. AC-02 says an excluded mechanical reference is absent everywhere. Section 6 requires a neutral exclusion row. State that the reference appears only in neutral data and does not appear in supplier outputs.

## Resolved findings

- Population state now uses only the three states from `variants.yaml`. `installation_method` records `hand_installed` separately.
- Populated hand-installed references count in the neutral per-board BOM and test coverage. They appear on the drawing and in hand-install instructions. They do not enter automatic placement.
- The neutral dataset now defines a part-free row for an explicit mechanical exclusion.
- A geometry-derived midpoint estimate remains unconfirmed and cannot qualify placement.
- Neutral data retains the source rotation and its normalized angle.
- The sample's stated mil unit stays separate from supplier convention confirmation.

## Review notes

Close R1 and R2 as decisions in section 12. The current text still presents them as open questions, although the interface defines their outcomes. Name the copied validator and other copied helpers in the interface before implementation, as the proposal inputs require.

## Acceptance recommendation

Accept the interface after the two required corrections. The review point and helper-name notes can close with the next revision. Coordinate conventions remain unconfirmed until authoritative evidence establishes them. Fixtures establish implementation behavior only.

This review changes no product file and no shared contract.
