# B9/B10 proposal inputs

Date: 2026-11-14 UTC. This note identifies the remaining interface choices for the author's proposal.
It does not authorize B9 implementation before the reviewers agree.

Use plan section 8, both preparation reports, and `b9-source-addendum-root.md` as the starting point.
The inch drill probe in `b9-drill-probe-root.md` establishes one available export command.
It does not establish supplier acceptance or complete coordinate agreement.

## Necessary proposal details

1. Make `pcba-design` independent. Give it its own scripts, runtime files, templates, schemas, and supplier evidence.
2. State the complete command sequence from a source project to neutral assembly data and a Sierra candidate package.
3. Name each copied helper and each owned derivative. Do not call another installed skill.
4. State how references select part records. The current part schema contains no reference field.
5. Use `variants.yaml` as the sole owner of population state. Do not add a second population list.
6. State how `hand_installed` affects supplier quantities, placement, drawings, and test instructions.
7. State which excluded mechanical references can omit part records.
8. Bind all selected part files, the variant, the source board, the board record, and the supplier convention.
9. Derive BOM quantities, supplier placement, and DNP drawings from the same selected neutral data.
10. Group identical parts only when manufacturer, MPN, population state, and applicable assembly instructions agree.
11. Aggregate stock demand across all populated references that use the same part. Keep board quantity separate from per-board quantity.
12. Keep substitution explicit. An alternate part must receive the same electrical, footprint, polarity, process, and evidence checks.
13. Give an exact stock policy field and date comparison. Do not invent a universal age limit.
14. Use `draft`, `unqualified`, and `qualified` as the existing manifest states.
15. Keep unresolved service, placement, process, and plane conditions visible. They block qualification, not the neutral-data implementation.
16. State the required assembly drawing content, including side, reference, polarity, DNP state, and the selected variant.
17. Supply executable electrical test instructions and expected limits. A test plan does not establish a measured physical pass.
18. Bind firmware and programming instructions only when applicable. Do not invent firmware for the example.
19. Test the supplier's Gerber drawing separately from local PDF documentation.
20. Keep the agreed exit meanings and safe publication rules. Preserve source bytes and prior packages.

One possible reference-to-part map is a named board extension whose values are confined paths under `components/`.
That record already has a manifest input role. The author can propose this form or a smaller equivalent.
The proposal must resolve the mapping before implementation. File-name guesses and MPN guesses cannot establish the join.

The example must include two variants, an excluded mechanical item, a DNP part, and a part with an offset footprint origin.
Independent asymmetric fixtures must cover both sides and 0, 90, 180, and 270 degrees.
Supplier example rows do not supply those expected coordinates.

Keep service-specific facts separate from generic workflow guidance. The Turnkey PRO FAQ directly supplies the candidate fabrication settings.
The PDF placement sample is its linked candidate format. The placement transform still lacks complete source evidence.
No supplier contact, upload, payment, or physical test is part of the current authorization.
