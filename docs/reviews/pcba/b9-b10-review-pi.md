# B9/B10 interface review: Pi

Date: 2026-11-15 UTC. Author: pi-pcba-dev (w1P:pD), reviewer for B9/B10.
Subject: `docs/reviews/b9-b10-interface-claude.md`, revision with lead decisions folded in.
Status: review only. No product file is changed. No commit, push, or merge is made.

I read `AGENTS.md`, `docs/reviews/parallel-workstreams-root.md`, plan section 8, the three B9 source
records, the Codex preparation report, the Pi preparation report, the Codex interface review, and the
updated Claude interface. I measured the KiCad placement export in the accepted local image. I verified
the interface claims against the shared contracts.

## 1. Decision

The interface is sound. Accept it with the corrections in section 4. The corrections are small and
concrete. None changes the lead decisions. Two corrections prevent a wrong supplier claim. The other
corrections prevent an ambiguity in the neutral data.

The lead decisions are applied correctly:

- The map is `components/parts-map.yaml`, schema `cad-skills/part-map` 1.0, skill-owned.
- The map and each part file are `parts` inputs.
- `variants.yaml` is the sole population owner.
- A populated `hand_installed` reference counts in the neutral BOM and test coverage. It stays out of
  automatic placement. Its supplier BOM treatment follows `hand_installed_bom`.
- An unknown supplier policy blocks qualification. It does not block neutral output.
- Coordinate conventions stay unconfirmed until authoritative evidence exists.

## 2. Measured KiCad placement transform

I ran `kicad-cli pcb export pos` in the accepted image `localhost/cad-skills-pcb:b6`
(`--pull=never`, no network). I used a copy of the RC trial board with an LED moved to `B.Cu`. I varied
the rotation and the side. The results are stable and repeatable.

| Board value | Export value | Side |
|---|---|---|
| X = 125 | 125.000000 | top |
| Y = 106 | -106.000000 | top |
| X = 125 | 125.000000 | bottom |
| Y = 106 | -106.000000 | bottom |
| rotation 0 | 0.000000 | bottom |
| rotation 45 | 45.000000 | bottom |
| rotation 90 | 90.000000 | bottom |
| rotation 135 | 135.000000 | bottom |
| rotation 180 | 180.000000 | bottom |
| rotation 270 | -90.000000 | bottom |
| rotation 315 | -45.000000 | bottom |
| rotation 270 | -90.000000 | top |

The measured transform is:

- `X_export = X_board`.
- `Y_export = -Y_board`.
- `Rotation_export = ((Rotation_board + 180) mod 360) - 180`.
- The side does not change the transform. A bottom-side part is not mirrored in X, Y, or rotation.
- The drill-file origin option does not change the top-side values. I measured `--use-drill-file-origin`
  and the plain export on the same board. The values agree.

This transform is a property of the KiCad exporter. It is not a Sierra convention. It does not resolve
the Sierra origin, axes, side view, rotation direction, or zero orientation. It does tell the fixture
author what to expect from the exporter.

## 3. Verified contract facts

I checked these claims against the repository:

| Claim | Result |
|---|---|
| `parts` is an input role | Yes. `INPUT_ROLES` includes `parts`. |
| `parts` is a manifest input role | Yes. The manifest schema input role enum includes `parts`. |
| The five `asm.*` check IDs exist | Yes. `PCBA_CHECKS` lists `asm.bom_consistent`, `asm.placement_rotation`, `asm.variant_agreement`, `asm.stock_dated`, `asm.test_record`. |
| The `asm.*` checks accept `parts` | Yes. `CHECK_INPUT_ROLES` lists `parts` for four of the five checks. `asm.placement_rotation` lists `board`, `parts`, `variants`. |
| `variants.schema.json` has `hand_installed` | Yes. It has `reference` and `reason`, both required. |
| `board.schema.json` has `extensions` | Yes. `extensions` is an object. The `pcba.stock` extension is allowed. |
| `manifest.schema.json` allows `unqualified` | Yes. The status enum is `draft`, `qualified`, `unqualified`. |
| `supplier-profile.schema.json` has `extensions` | Yes. `additionalProperties` is `false`. |
| The shared validator enforces variant semantics | No. `_rules_variants` checks duplicate IDs only. |
| The shared validator parses `parts` records | No. `_load_project` reads only the roles in `PROJECT_RECORDS`. `parts` is not one of them. |

## 4. Corrections

### C1. State where `hand_installed_bom` lives in the supplier profile

Section 9.1 says the field is "set in the Sierra profile". The supplier profile schema has
`additionalProperties: false` and an `extensions` object. A top-level `hand_installed_bom` key fails
schema validation. Put the field in `extensions`, for example
`extensions.pcba.hand_installed_bom`. Alternatively, ask the lead for a schema change. The interface
must say which form applies. Section 9.1 must not imply a top-level key.

### C2. State who validates the map schema

Section 4 says the map is "strict: unknown keys fail". The shared validator does not parse `parts`
records. It reads each `parts` input as bytes and hashes the bytes. Therefore the copied validator
cannot reject an unknown key in the map. The skill's `neutral` and `check` steps must validate the map
against `cad-skills/part-map` 1.0. The interface must say this. Otherwise a reader expects the copied
validator to enforce the map rules. It does not.

Also, the shared `registry.json` has no `cad-skills/part-map` entry. The skill must load the map schema
directly, or add a skill-owned registry entry. Section 2 lists the copied schema set. Add the map schema
to that set and to the copy record.

### C3. Remove the `source_rotation_deg` ambiguity

Section 6 says `source_rotation_deg` is "the rotation as read from KiCad, unchanged". KiCad has two
values: the board file value and the pos export value. For a bottom-side part at 270 degrees they
differ. The board value is 270. The pos export value is -90. State which one the field holds. My
recommendation: `source_rotation_deg` is the board file value. Add `export_rotation_deg` for the pos
export value when the neutral step reads the pos file. If the neutral step reads only the board file,
state that. The neutral row must not mix the two.

### C4. State the measured transform in section 3, step 0

Section 3, step 0 says "Record the exact origin and rotation in an evidence file". It does not say what
the fixture author must expect. Add the measured transform from section 2 of this review. Then the
fixture expectations are written by hand from a known transform. The interface already says the fixture
expectations are not computed by the adapter under test. The transform statement makes that practical.

### C5. Name the rotation normalization in the neutral row

Section 6 says `rotation_deg` is "normalized to [0, 360)". A bottom-side part at 270 in the board file
gives -90 in the pos export. The neutral row must keep 270 after normalization. A source value of 360
becomes 0. State the rule explicitly:

- `rotation_deg = ((source_rotation_deg mod 360) + 360) mod 360`.
- A source value of 360 gives 0.
- A source value of -90 gives 270.

This makes AC-07 and AC-14 consistent. It also makes the supplier XY draft conversion unambiguous.

### C6. Separate the skill checks from the copied validator checks

Section 10 says the five `asm.*` check IDs "exist in `contracts/validate.py`". That is true. Section 5
says the neutral step stops on a missing or duplicate reference, a missing MPN, a footprint mismatch,
and a quantity disagreement. The copied validator does not enforce those variant rules. The skill's
`neutral` step must. State this in section 5 and section 10. Do not let a reader think the copied
validator enforces the join rules.

### C7. Keep the geometry midpoint estimate out of the supplier XY values

Section 6 and R6 accept `midpoint_estimate_mm` as a draft assumption. I agree. Add one limit. The
estimate must never become the Sierra XY value that the package presents as the supplier's requested
midpoint. The Sierra XY draft must carry the KiCad footprint position with `midpoint_mapping:
unconfirmed`. The estimate can appear in a separate draft field or a separate draft output. If the
estimate enters the supplier XY column, the draft looks like a supplier-confirmed midpoint. That is the
wrong claim. This is a small wording change. It prevents a false supplier claim.

### C8. State the `hand_installed` neutral row fields

Section 6 lists `variant_state` and `installation_method`. For a populated `hand_installed` reference,
the interface must state the neutral row values exactly:

- `variant_state`: `populate`.
- `installation_method`: `hand_installed`.
- `per_board_quantity`: 1.
- The row is in the neutral BOM group and the test reference list.
- The row is absent from the automatic placement rows.

The interface already implies this in section 5. Section 6 must state it, because the BOM derivation
reads the neutral rows. A `hand_installed` row must not be grouped as a DNP row.

## 5. Answers to the open review points

- R3: I cannot confirm the BOM headers or the DNI value from repository evidence. The sample file
  `/tmp/cad-skills-sierra-bom.xls` is not in the repository. The retained `xy.pdf` and `xyrs.xlsx` are
  placement and workbook evidence, not the BOM sample. The proposal is correct: retain the sample and
  bind the header fixture to the retained copy before implementation. Do not write header strings from
  memory. The interface already names the two known header strings. Bind them to a retained file.
- R4: Yes. A draft XY file with `unconfirmed` conventions is an acceptable output. It must not qualify.
  The manifest status stays `unqualified` until the conventions are confirmed. I agree with the
  interface.
- R5: Yes. Tests in `tests/test_pcba_design.py` and fixtures in `tests/fixtures/pcba-design/` are the
  right locations. Shared-file changes stay with the lead. I agree with the interface.
- R6: Yes, with correction C7. A geometry-derived estimate is acceptable as a draft assumption. It must
  never enter the supplier XY column as the supplier midpoint. It must be per footprint. It must never
  be a global offset.

## 6. Open items

- The Sierra BOM sample is not retained. Retain it and bind the header fixture before implementation.
- The Sierra placement origin, axes, side view, rotation direction, zero orientation, and units stay
  unconfirmed. My measurement covers the KiCad exporter only. It does not resolve the Sierra
  convention. No supplier contact is allowed to resolve it.
- The plane interpretation stays unconfirmed. The FAQ asks "Should plane layers be supplied in
  negative format?" and gives pros and cons. It does not give a mandatory answer. The interface is
  correct to keep the condition open.
- The MacroFab and Ninja profiles stay provisional. In-house evidence is absent.

## 7. Communication

I sent these corrections to `claude-pcba-dev` in pane `w1P:p7` and to `skill-dev-lead` in pane
`w1P:p3`. This report records recommendations only. It does not accept an implementation and does not
change a shared contract.
