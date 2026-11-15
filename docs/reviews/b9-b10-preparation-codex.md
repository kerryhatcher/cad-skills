# B9/B10 paper review preparation

Date: 2026-11-14 UTC. Scope: plan section 8 and the existing PCBA research and review records. This is a paper review. It does not qualify a supplier or package.

## Necessary interface choices

| Topic | Choice or boundary |
|---|---|
| Neutral assembly data | Generate one supplier-neutral dataset before supplier files. Include references, quantity, MPN, manufacturer, footprint, selected variant, and DNP state. Keep supplier-specific columns in the adapter. |
| Variant source | `variants.yaml` owns population state. Select one stable variant for each package. Derive BOM quantities, placement rows, and DNP drawings from that selection. Do not repeat DNP state in part records. |
| BOM joins | Join by exact reference to component records and the selected variant. Stop on duplicate or missing references, missing MPN, or quantity disagreement. For Sierra, split populated and unpopulated references into separate rows because DNI applies to the whole row. |
| Placement joins | Join each populated reference to the board footprint and selected variant. Preserve X, Y, units, origin, rotation, and side in neutral data. Do not assume the KiCad footprint origin equals Sierra's requested midpoint. Keep datum interpretation unconfirmed, or bind an explicit per-footprint mapping to evidence. Do not apply one global rotation offset. |
| Sierra adapter | Preserve the measured sample BOM header strings, including `Size / Footprint  (optional)`, `Part description/ specs (optional, but recommended)`, and `Manfacturer (optional)`. Keep source headers exactly in the format fixture. Use the source row note to interpret DNI. The XY sample identifies designator, footprint, midpoint X/Y, side, and rotation. Its origin and rotation convention remain unresolved. Do not qualify until applicable evidence resolves them. Sierra performs panelization. |
| Stock evidence | Record lifecycle status, available quantity, source, and retrieval date. Treat stock as a dated observation, not a reservation. Compare available quantity with assembly quantity under an explicit project or supplier policy. Do not invent a universal stale interval. Unknown lifecycle or stock stays explicit and blocks the related qualified claim. |
| Supplier filenames | Reject unsupported supplier conventions. Do not reject compatible Gerber filenames only because another supplier also uses them. Validate file role and layer content independently from filename compatibility. |
| Manifest completeness | Use existing manifest roles for `parts`, `variants`, `board_record`, `bom`, `placement`, `assembly_drawing`, `test_record`, plus applicable firmware, stencil, panel, and fabrication outputs. Bind each input and output by path and hash. Require the PCBA checks already listed by the validator. |
| Supplier conditions | Keep Sierra as the first candidate, but do not infer order-specific in-house work or unresolved file conventions. Keep MacroFab and Ninja provisional under the in-house condition. Do not apply JLCPCB columns or rotations to Sierra. |

## Concrete tests

- Use two variants. Confirm the selected variant drives BOM quantity, placement inclusion, and DNP drawings from the same population records.
- Include `populate`, `dnp`, and `exclude_from_assembly` references. Confirm DNP references do not appear as populated placement rows. Confirm their BOM rows have the correct supplier-level DNP state and do not mix populated and DNP references.
- Add a missing reference, duplicate reference, missing MPN, footprint mismatch, and conflicting quantity. Confirm package generation stops for each case.
- Change the selected variant after output generation. Confirm manifest inputs become stale and qualification fails until all derived outputs and evidence refresh.
- Change a part record or board reference after manifest creation. Confirm BOM or placement evidence hash checks detect the change.
- Record a stock quantity below assembly quantity, a stale retrieval date, and unknown lifecycle data. Confirm each blocks the relevant qualified stock claim. Do not treat stock evidence as a reservation.
- Test top and bottom asymmetric polarized parts at 0, 90, 180, and 270 degrees. Compare neutral placement data with the board. Do not set a universal rotation correction.
- Use an offset-origin board fixture. Confirm placement output preserves the board datum and does not treat the KiCad footprint origin as the requested midpoint without evidence or an explicit mapping.
- Use an exact-header Sierra BOM fixture. Confirm the optional header strings remain unchanged and DNI follows the sample row note, not guessed column labels.
- Keep Sierra origin or rotation unknown in a fixture. Confirm the Sierra adapter cannot claim qualification while the convention remains unresolved. A synthetic round-trip test can check implementation after the convention has evidence, but cannot establish the supplier convention.
- Remove each required PCBA output role or required check in turn. Confirm the manifest validator rejects qualified status. Test optional output roles only with explicit applicability.
- Check that the final package has fabrication outputs, assembly files, drawings, test record, DNP and variant records, reports, and one manifest whose hashes match all released files.

The plan and prior reviews do not establish Sierra's placement origin or rotation convention, or that its requested midpoint equals the KiCad footprint origin. They also do not establish a universal DNP drawing format or stock freshness interval. Keep these open until source evidence or an explicit project policy resolves them.

## Sierra source addendum decision

I agree with `b9-source-addendum-root.md`. The retained XY PDF and XYRS workbook are separate samples. The PDF names designator, footprint, midpoint X/Y, side (`T`/`B`), and rotation. Its coordinates use mil, but it does not define origin or complete rotation behavior. The workbook uses designator, X, Y, layer (`Top`/`Bottom`), and rotation. It does not state coordinate units, origin, or bottom-side rotation behavior. Its example data includes duplicate references and conflicting populated sheets, so those rows are not expected results.

Name the selected sample and service in the adapter record. Keep each sample's exact columns and side terms in its own fixture. Do not combine their formats or transfer Web PCB-only instructions to Turnkey PRO. Keep midpoint-to-footprint datum, axes, units, and rotation conventions unconfirmed until service-specific evidence binds a convention and any per-footprint mapping. Reject duplicate placement references. Test with independent asymmetric fixtures. Supplier submission remains out of scope; these open conventions block qualification, not neutral dataset implementation.

### Turnkey PRO source clarification

The Turnkey PRO FAQ also states inch RS-274X, absolute inch drill coordinates, trailing-zero suppression, and 2.4 format. This direct service evidence appears under its order-file question. The FAQ also requests a fabrication drawing in Gerber format and retains negative-plane guidance. The source review records these findings in `b9-source-addendum-root.md`, with the page snapshot at `sierra-source-evidence/turnkey-faq.html`. Keep the Gerber drawing role distinct from local PDF documentation. The negative-plane guidance needs review against the current exporter. The placement datum, units, axes, and rotation convention remain unresolved.
