# Review of the B9/B10 interface by Codex

Date: 2026-11-15 UTC.

Reviewed file: `docs/reviews/b9-b10-interface-claude.md`.

Decision: the lead's map and hand-install decisions appear in this revision. The interface is not ready for acceptance. Correct the findings below before product work.

## Required corrections

1. Keep population state separate from installation method. Section 6 lists `hand_installed` as a `variant_state`. This conflicts with the rule that `variants.yaml` owns only `populate`, `dnp`, and `exclude_from_assembly`. Store `variant_state: populate` and a separate `installation_method: hand_installed` value.
2. Exclude hand-installed references from automatic placement. Section 6 says placement uses all populated rows. Filter rows where `installation_method` is not `hand_installed`. Keep the explicit service policy for supplier BOM output.
3. Define the neutral record for mechanical exclusions. Section 6 says one row exists for each board reference, but excluded mechanical references can lack part records. State whether an exclusion row has no part fields. Keep the explicit exclusion list in `components/parts-map.yaml` and reject all implicit exclusions.
4. Keep a geometry-derived midpoint estimate unconfirmed. Section 6 and R6 permit an anchor-to-midpoint offset derived from footprint geometry. Geometry alone does not establish the supplier's requested midpoint. Store such an estimate as an assumption with `unconfirmed` status. Do not use it to qualify placement.
5. Preserve the source rotation value when normalizing `360` to `0`. Record both the source value and the normalized neutral angle. Do not treat normalization as evidence for Sierra's rotation convention.

## Review notes

- The map path, schema ID and version, strict key handling, `parts` input role, and per-part hash binding match the lead's decision.
- The hand-installed policy correctly blocks qualification when the service value is missing or unknown. Neutral output can still proceed.
- The separate Turnkey PRO FAQ settings and the retained XY PDF candidate remain distinct from Web PCB XYRS evidence.
- Section 9.1 correctly identifies that the BOM workbook must match retained sample evidence. The source workbook remains in `/tmp`, so copy it into retained evidence with its hash before implementation. The local file exists at review time.
- The listed acceptance cases cover the lead's hand-install and map rules. Add a case that confirms a geometry-derived midpoint estimate remains unconfirmed and cannot qualify.
- The sample states mil, but the supplier convention remains unconfirmed. Distinguish the sample's stated unit from supplier confirmation of its coordinate convention.

## Acceptance recommendation

Accept the interface after the five required corrections and the added midpoint acceptance case. Keep all placement conventions unconfirmed until authoritative evidence binds them. Independent fixtures test implementation behavior only.

This review changes no product file and no shared contract. I sent these findings to Claude and the lead.
