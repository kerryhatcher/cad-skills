# B11 Batch 1 review: Pi

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Scope: the frozen contract-layer batch announced by Claude. No CadQuery. No product file changed.

Basis: interface revision 8, SHA-256 `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`.

**Decision: Batch 1 passes review. F1 was required before Batch 2 and is resolved in Batch 1a. The five minor items are resolved in Batch 1a. The hashes match, the tests pass, and the generated fixture agrees with the accepted interface.**

## 1. Hashes confirmed

| File | SHA-256 |
|---|---|
| `skills/pcb-design/scripts/mechanical.py` | `3764e651aee1540fd763d573a363c498f5e67f6e4039e1eec7d37ebb356bc9cc` |
| `skills/pcb-design/templates/mech-fit-a/make_fixture.py` | `ff1d3fec802e3969500faefdeed3d304aac0c458f4c0df44fe14dae1f12bb905` |
| `skills/pcb-design/templates/mech-fit-a/fixture-source.json` | `ea61b95da21e4ff343defb1f0df541e2792ab282a424f61de6c528491e7dd296` |
| `skills/pcb-design/templates/mech-fit-a/component-evidence.json` | `233a8225bd0e2ecb3b69fe9be0df43737be909dbf520fb93c11db835eeef9cdd` |
| `skills/pcb-design/templates/mech-fit-a/export-settings.json` | `a41be7d3fefb2a3e6e5ae5b4287c7772fe234a8d2c392fdfb11b2a1508a3dafe` |
| `tests/test_mechanical.py` | `2993432b5e782fd48b0afe51912540afb27fec905818154bc28e7884ad2cc9d2` |

All six match the announcement.

## 2. Independent results

| Check | Command | Result |
|---|---|---|
| Contract tests | `uv run tests/test_mechanical.py` | 40 pass, exit 0 |
| Fixture generation | `uv run skills/pcb-design/templates/mech-fit-a/make_fixture.py --out /tmp/mechfix1` | board SHA-256 `f79ab47b9ff202a6f2cecae7f3a4a0628908bfa650cc4888abd0f0503503d10f` |
| Determinism | generate again into `/tmp/mechfix2` and compare | identical trees |
| Contract validator | `uv run contracts/validate.py --schemas contracts/schemas board.yaml mechanical/board-interface.json` | pass, exit 0 |
| Contract CLI | `uv run skills/pcb-design/scripts/mechanical.py check --fixture /tmp/mechfix1` | exit 0, evidence `conservative_envelope_only` |
| KiCad read | `kicad-cli pcb export step --drill-origin --board-only --no-extra-pad-thickness` in `localhost/cad-skills-pcb:b6` | STEP created |

The generated board agrees with the accepted interface:

| Item | Measured |
|---|---|
| Outline in the contract frame | X `-3.7..56.3`, Y `-17.8..18.2` |
| Substrate solid Z | `0..1.51` |
| Cylinder faces | radius `1.6`, `1.5`, `1.25` for H1, H3, H2 |
| H1 contract point | `(6.3, -11.8)` |
| H2 contract point | `(48.8, 14.7)` |
| H3 contract point | `(14.3, 12.2)` |

The frame logic matches the accepted Q7 rule. Local `(2.0, 0.5)` at 30° gives `(1.982, 0.567)` and the angle `15.96°`. Local `(1, 0)` at 30° gives `(3.464, 2.0)` and the angle `30°`.

The `mechanical.py` contract rules are correct for the accepted interface: strict transform keys and types, boolean scale refusal, unsupported-axis refusal, the stackup sum, the finished-envelope surfaces, the `pad_frame` rule for `B.Cu`, the connector six-field rule, the owner conflict, the closed release role list, the stale order, and the accepted canonical-hash helper.

## 3. Findings

### F1. The `B1` placement is missing (required before Batch 2)

The accepted interface section 4 records the bottom-side part `B1` at center `(130.0, 120.0)`, rotation `90°`, side `bottom`. No Batch 1 record holds the placement. `component-evidence.json` holds the `B1` envelope `(8.0, 4.0, 2.8)` and `pad_frame` `placed-file`, but no position or rotation. The generated board has no `B1`.

C06, C07, C08 and C09 need the `B1` position and rotation. T8 and T13 also need it. Add the placement before Batch 2:

- Add `placement_kicad_mm` and `rotation_deg` to the `B1` evidence record, or
- Add a `parts` list to `fixture-source.json` with the placement of each part.

State also where the test-only `CN2` placement comes from.

### F2. `release_outputs_ok` checks only the role

The accepted interface section 8 says each output names a role, a path and an exact SHA-256. `release_outputs_ok` examines the role only. Add a check that `path` is a nonempty string and `sha256` is 64 lowercase hex characters. If the release builder in Batch 2 does this, state that in the module docstring.

### F3. `source_sha256` is null

Each `component-evidence.json` record gives `source_sha256: null`. The accepted interface section 5 lists `source_sha256`. State the rule for a proxy: null is allowed, or use the `fixture-source.json` hash. Do not leave the meaning open.

### F4. Error code naming

`evidence_status` raises the code `transform.type` for a non-numeric `height_mm`. Use an evidence-specific code, for example `evidence.height`. The status 2 is correct.

### F5. `__pycache__` in the frozen template

`skills/pcb-design/templates/mech-fit-a/__pycache__/make_fixture.cpython-313.pyc` exists. `.gitignore` line 2 ignores `__pycache__/`, so it will not be committed. Remove it to keep the frozen batch clean.

### F6. Generated KiCad board version

`make_fixture.py` writes `(version 20241229)`. The accepted board writes `(version 20260206)`. KiCad 10.0.5 reads and exports the file. Confirm the intended version and keep it consistent with the image.

## 4. Notes, not findings

- The fixture source and the interface use the same `dimension_owners`, so C11 passes. The electrical declaration is the interface copy. This follows the accepted O1 rule.
- `board.yaml` holds no `dimension_owners` field. It passes `validate.py`. This follows O1.
- The generated `board-interface.json` passes `validate.py`. The existing interface operation is a Batch 2 integration check (T35).
- The `CN1` frame is frame-only, and the fixture has exactly three through holes. This follows O3.

## 5. Limits

- I examined the frozen files and ran the commands above. I did not change a product file.
- I did not test the geometry comparisons C01 to C12. They are Batch 2.
- The tests need CadQuery for Batch 2. This batch does not.
- The review covers the announced hashes only.

## 6. Next

After F1 is added, I will review Batch 2 (`mechanical_fit.py`, `references/mechanical-fit.md`, `tests/test_mechanical_fit.py`, and the narrow `pcb.py` dispatch) against the same interface and this review.

## 7. Batch 1a update (F1 to F6 resolved)

| File | Batch 1a SHA-256 |
|---|---|
| `skills/pcb-design/scripts/mechanical.py` | `7896cf6db0240c1b28334914e21c63e22cb47e81a5418c599d31f6a9f47db38a` |
| `skills/pcb-design/templates/mech-fit-a/make_fixture.py` | `869a05ca5da28dabf665ed4bcb80261acbb61fd79d3212fe8bdd66cd123a8a35` |
| `skills/pcb-design/templates/mech-fit-a/fixture-source.json` | `e440ee6442424fe4750bbd871c0198e9677ca8c0786581ecc17b38566710a2cf` |
| `skills/pcb-design/templates/mech-fit-a/component-evidence.json` | `fe60cc688e4565be6933a3b135c8372d590f72aacc57cdc024e8d6493d03f35d` |
| `skills/pcb-design/templates/mech-fit-a/export-settings.json` | `a41be7d3fefb2a3e6e5ae5b4287c7772fe234a8d2c392fdfb11b2a1508a3dafe` |
| `tests/test_mechanical.py` | `b3b9a11707e97ec3ddc4a950ff993e988aab055212044cba7a9a026e25269dcf` |

All six match the announcement. The corrections:

- F1 resolved. `B1` and `CN1` carry `kicad_center_mm` and `rotation_deg`. `fixture-source.json` holds a `parts` list with `B1` at `(130.0, 120.0)`, rotation `90`, side `bottom`, and `test_variants.CN2` at `(150.0, 128.0)`, rotation `30`, side `bottom`, with `test_only` true and `release_allowed` false. `check_placement` requires the centre and the rotation. `check_fixture` refuses a variant that does not declare the test-only flags.
- F2 resolved. `release_outputs_ok` checks a nonempty `path` and a 64-character lowercase `sha256`.
- F3 resolved. `check_evidence_source` allows a null `source_sha256` only for `proxy` and `unconfirmed`. `measured` and `datasheet` need a 64-hex source.
- F4 resolved. `_height` raises the code `evidence.height` for a non-numeric value.
- F5 resolved. The `__pycache__` directory is gone.
- F6 resolved. The generated board writes `(version 20260206)`.

Independent results:

| Check | Result |
|---|---|
| `uv run tests/test_mechanical.py` | 47 pass, exit 0 |
| `uv run tests/test_mechanical_fit.py` | 25 pass, exit 0 |
| Generation determinism | identical trees, board SHA-256 `37105cf50e2bb0c997f7b9f6a02affef2f101a6b0684a4024d5a78541f8e20ba` |
| `contracts/validate.py` on `board.yaml` and the interface | pass, exit 0 |
| `mechanical.py check --fixture` | exit 0 |
| Generated board version | `20260206` |

**Decision: Batch 1a passes. F1 is closed. I give explicit agreement to Batch 1a.**

The 25 geometry tests belong to Batch 2. I ran them to confirm the suite. I will review Batch 2 separately when Claude freezes it.

## 8. Post-Batch-1a disclosure

Claude disclosed that two route tests were added to `tests/test_mechanical.py` after the Batch 1a freeze, and the narrow mechanical subcommand was added to `pcb.py`. The Batch 1a acceptance in section 7 applies to the frozen hashes only.

| File | Batch 1a accepted hash | Current hash |
|---|---|---|
| `tests/test_mechanical.py` | `b3b9a11707e97ec3ddc4a950ff993e988aab055212044cba7a9a026e25269dcf` | `ecc7a7fb8b9cc1576e42a916a892912fa7156a667adb2e1afade8f11be9efaad` |
| `skills/pcb-design/scripts/pcb.py` | not in Batch 1a | `2523f19e7585609e563fa1c1b747cc1594f34f0308b32fac5a03b3dac8d4c3ea` |

Current state, measured:

- `uv run tests/test_mechanical.py` runs 49 tests, exit 0.
- `pcb.py` has a `mechanical` subcommand and `cmd_mechanical`, which imports the skill-local `mechanical` module.

Both files belong to Batch 2. I did not review them here. I will review them in Batch 2 with `mechanical_fit.py`, its tests, and the reference.
