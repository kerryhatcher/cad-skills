# PCBA interface review: Codex

Date: 2026-11-15 UTC.

Scope: initial interface review for B9 and B10. I read `AGENTS.md`, `docs/reviews/parallel-workstreams-root.md`, plan section 8, both preparation reports, and all three source records. No product files changed. No stable product change existed at review time.

## Decision

The evidence supports neutral assembly data and a draft Sierra candidate package. The evidence does not support Sierra placement qualification. Keep unknown supplier conventions visible and block qualification until evidence binds them.

## Interface recommendations

1. Keep `pcba-design` independent. Copy required helpers into its own scripts and own all runtime files, templates, schemas, and source evidence. Do not import another skill at runtime.
2. Resolve each board reference through an explicit board extension that names a confined path under `components/`. Reject duplicate paths, missing references, and ambiguous joins. Do not infer a join from a file name or MPN.
3. Keep `variants.yaml` as the sole owner of population state. Generate one neutral row per reference before supplier formatting. Include the selected part path and hash, reference, variant, state, manufacturer, MPN, footprint, side, coordinates, datum, rotation, and assembly instructions where known.
4. Keep board quantity separate from per-board quantity. Sum stock demand across populated references that use the same part. Group BOM rows only when manufacturer, MPN, state, and assembly instructions match.
5. Define `hand_installed` behavior. Exclude those references from supplier BOM and placement rows. Retain them on the assembly drawing and in applicable test instructions. If the selected state is DNP, do not treat the part as hand-installed.
6. Permit an omitted part record only for a reference with `exclude_from_assembly` state and a mechanical footprint. Reject an omitted record for a populated or DNP reference.
7. Bind the source board, board record, selected part files, variant, stock policy, supplier profile, and placement convention by path and hash. A change to any bound input makes derived outputs stale.
8. Derive the BOM, placement rows, DNP marks, and test references from the same selected neutral rows. Require one row per placement reference and reject duplicates.
9. Preserve the Sierra BOM headers exactly, including the sample spelling `Manfacturer (optional)`. Split populated and DNP references when the sample row note applies DNI to the whole row.
10. Record an alternate part explicitly. Apply the same electrical, footprint, polarity, process, and evidence checks to that part.
11. Define stock policy with an explicit field such as `maximum_age_days`, or an explicit no-age-limit policy. Record the comparison date. Do not set a universal age limit.
12. Use only `draft`, `unqualified`, and `qualified` as manifest states. Keep unresolved service, placement, plane, and process conditions as findings. These findings block qualification, not neutral-data generation.
13. The assembly drawing must show side, reference, polarity, DNP state, and selected variant. Keep local PDF documentation separate from the supplier-requested Gerber fabrication drawing.
14. Include executable electrical test steps and expected limits. A written test plan does not establish a measured physical pass. Bind firmware and programming instructions only when applicable.
15. Keep the Sierra Turnkey PRO placement PDF separate from the Web PCB XYRS workbook. Preserve each sample's own columns and side terms. Do not use sample rows as expected coordinates.

## Coordinate evidence and acceptance cases

The retained PDF names the component midpoint and uses mil with `T` and `B`. It does not define origin, axes, side view, rotation direction, or zero orientation. The workbook does not define units or a complete transform. Its duplicate reference and disagreeing sheets make its example rows unsuitable as expected results.

Keep units, board datum, axes, side view, rotation direction, zero orientation, and any footprint-origin-to-midpoint mapping `unconfirmed` until service-specific evidence resolves them. Do not infer a supplier transform from a synthetic round trip. Independent fixtures test code behavior only.

Acceptance cases:

- Use two variants with populated, DNP, excluded mechanical, and hand-installed references. Confirm each output follows the selected variant.
- Use an offset footprint origin and an asymmetric board datum. Confirm neutral coordinates retain both values without an unsupported midpoint assumption.
- Test asymmetric polarized parts on top and bottom at 0, 90, 180, and 270 degrees. Compare results with independently recorded expected coordinates.
- Confirm the Sierra format fixture preserves exact source headers and the DNI row note.
- Confirm duplicate placement references fail. Confirm missing references, MPNs, or part records fail where state does not permit omission.
- Confirm unresolved placement or plane conditions keep the manifest unqualified. Confirm source or profile hash changes invalidate derived package evidence.
- Confirm one board image enters the candidate package. Record that Sierra performs panelization.
- Confirm the Turnkey PRO Gerber fabrication drawing and local PDF documents use separate output roles.

## Source limits

The Turnkey PRO FAQ supports the candidate fabrication settings and requests a Gerber fabrication drawing. Its negative-plane guidance remains unresolved for the current exporter. The retained placement PDF is a sample, not proof of a complete transform. The preparation records do not establish a universal DNP drawing format or stock age limit.

## Communication

I sent these interface recommendations to `claude-skill-dev` in pane `w1P:p7` and `skill-dev-lead` in pane `w1P:p3`. This report records recommendations only. It does not accept an implementation or change a shared contract.
