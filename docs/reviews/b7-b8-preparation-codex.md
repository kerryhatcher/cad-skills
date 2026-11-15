# B7/B8 paper review preparation

Date: 2026-11-14 UTC. Scope: plan sections 7 and 8, supplier evidence notes, accepted supplier profile schema, and `contracts/validate.py`. This is a paper review. It does not approve a design or package.

## Decisions for implementation

| Topic | Decision |
|---|---|
| Five OSH Park profiles | Use one profile for single-layer, two-layer, two-layer HHDC, four-layer, and six-layer service. Keep each service URL and evidence hash distinct. Record the 2026-11-14 retrieval date and content hash. |
| Profile limits | Use the accepted `supplier-profile` schema. Record limit kind, scope, value kind, value, unit, source URL, and retrieval date. Keep substrate data separate from finished thickness. Mark recommendations and unconfirmed claims with their schema kinds. |
| Units and values | Keep each source nominal value and its source unit. Do not force all numeric values to mil. Copper weight, temperature, and counts keep their own units. For length conversion, use exactly 0.0254 mm per mil. Store rounded metric labels separately from exact source values. |
| Evidence freshness | Treat stored hashes as identity for retrieved bytes, not proof of current terms or order acceptance. A source-byte change triggers review. Block qualification only while a material change remains unresolved or lacks evidence. Harmless HTML changes do not block qualification after review. Recompute evidence and content hashes after a source update. |
| Rule boundaries | Put measurable fabrication rules in `kicad_dru`, stackup and net-class choices in project settings, outline and slot geometry in geometric tests, and non-measurable terms in manual evidence. Do not encode lead times as design rules. Do not treat the 250 mil drill threshold as a maximum drill size. |
| Process capability | Treat mask alignment, plating, and finished tolerances as process capability data. A CAD board cannot supply measured fabricated values for these properties. Tests validate the recorded policy and evidence. They do not claim physical measurement. |
| Internal clearance | Keep the three published mitigation methods as alternatives. Do not make annular rings on every unconnected layer a universal supplier rule. Test connected and unconnected copper against the stated clearance. |
| Copper filenames | Prefer the published copper filename pattern (`GTL`, `G2L` ... `GBL`) with neutral X2-off bytes. Check layer content independently. Do not add an untested X2 export path only to get names. |
| Package qualification | Use the existing manifest and package validator. A qualified package must include all applicable output roles and passing evidence. Do not report unsupported checks as pass. Keep unresolved conditions unqualified with a reason. |
| Output roles | For a bare board, require each copper, mask, silkscreen, and outline layer from export settings, plus schematic PDF, fabrication drawing, and each drill role or a supported applicability record. For PCBA, also require paste layers when applicable, BOM, placement, assembly drawing, and test record. Add firmware, stencil, and panel only when declared applicable. |
| Unsupported conditions | Refuse qualification when a requested rule or evidence cannot be measured or confirmed. Preserve the draft outputs and state the reason. Do not infer support from schema validity or a successful export command. |

## Focused test expectations

- For each profile, test values below, at, and above each numeric rule boundary. Include mask web, edge clearance, board dimensions, slots, and drill thresholds where applicable. Keep non-length units unchanged. Test exact length conversion separately from rounded metric labels.
- For four-layer and six-layer profiles, test the 10 mil plated-drill clearance with connected and unconnected internal copper. Test the published mitigation alternatives without promoting one to a universal rule. Confirm positive plane output and compare rendered copper with the board. Preserve clear-polarity primitives that form holes.
- Check the published copper filename pattern while the bytes remain neutral X2-off. Independently inspect layer contents. Do not qualify an X2-only route without a separate export test.
- Test blind vias, buried vias, and unsupported filled-and-plated via-in-pad constructions as refusals. Test other via-in-pad geometry separately. Do not treat soldermask tenting as a filled, flat pad.
- Test the single-layer process distinction, the 250 mil tolerance threshold, the absence of a maximum drill claim, and the distinction between nominal substrate core and finished thickness.
- Change source bytes after profile creation. Confirm that the change triggers review. Confirm that an unresolved material change or missing evidence blocks package qualification. Confirm harmless HTML churn can pass after review and hash refresh.
- Remove each required output role in turn. Confirm a missing required output blocks qualification. Confirm an omitted optional role passes only when its applicability record has a valid reason and evidence.
- Mark a check unsupported, absent, or without evidence. Confirm that the manifest cannot claim qualified status. A valid schema and successful export alone must not pass a supplier check.
- Test package evidence against exact input and output hashes. Change an input, evidence artifact, or output after manifest creation. Confirm the validator reports a mismatch.

The accepted schema records source and retrieval data per limit. The current validator checks the profile content hash and basic completeness. Package validation checks manifest hashes, evidence hashes, required roles, and required checks. Implementation must preserve these checks and add focused behavior only where the chosen profiles need it.
