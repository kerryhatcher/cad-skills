# B11 Batch 2 review: Pi

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Scope: the frozen geometry batch announced by Claude. No product file changed.

Basis: interface revision 8, SHA-256 `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`, and the lead Batch 2 note of 2026-11-15.

**Decision: not accepted. The implemented comparisons pass on real exports, but the batch does not match the accepted interface. Two hard defects and four scope gaps follow.**

## 1. Hashes confirmed

| File | SHA-256 |
|---|---|
| `skills/pcb-design/scripts/mechanical_fit.py` | `22c99b0acb83aaa20411d85780d1bbc01b80bc507cfe2776209b710b4ef1ca39` |
| `tests/test_mechanical_fit.py` | `fb4acb743d60260999f9d3f434613f910100be13fd63e8b2d2a9d2cd6ea1b05c` |
| `skills/pcb-design/scripts/pcb.py` | `2523f19e7585609e563fa1c1b747cc1594f34f0308b32fac5a03b3dac8d4c3ea` |
| `tests/test_mechanical.py` | `ecc7a7fb8b9cc1576e42a916a892912fa7156a667adb2e1afade8f11be9efaad` |
| `skills/pcb-design/references/mechanical-fit.md` | `bdf22f27c442104d6610f120889f70e02ecfadc720427962d311e143a860614c` |

All five match the announcement.

## 2. Independent results on real exports

I generated a fresh fixture copy and exported real KiCad output with the recorded switches in `localhost/cad-skills-pcb:b6`:

```text
uv run templates/mech-fit-a/make_fixture.py --out /tmp/mf2
kicad-cli pcb export step --drill-origin --board-only --no-extra-pad-thickness --min-distance 0.01mm -o board.step board.kicad_pcb
kicad-cli pcb export dxf --use-drill-origin --output-units mm --mode-single --layers Edge.Cuts --drill-shape-opt 2 -o outline.dxf board.kicad_pcb
kicad-cli pcb export drill --drill-origin plot --excellon-units mm -o drill/ board.kicad_pcb
```

I then drove the implemented comparisons with the real files:

| Comparison | Status | Error |
|---|---|---|
| C01 outline | pass | `1.8e-15` mm |
| C02 STEP hole centers | pass | `0.0` mm |
| C02d DXF circles | pass | `1.8e-15` mm |
| C03 DXF diameters | pass | `2.0e-06` mm |
| C04 plated flags | **fail** | `hit uses undefined tool T1` |
| C05 substrate | pass | `0.0` mm |
| C12 origin | pass | `0.0` mm |
| closed hole set | pass | — |

`overall_status` on that set gives `geometry_status fail`, `fit_status pass`. The only failure is C04.

Test suites:

| Suite | Result |
|---|---|
| `uv run tests/test_mechanical.py` | 49 pass, exit 0 |
| `uv run tests/test_mechanical_fit.py` | 25 pass, exit 0 |
| `uv run tests/test_pcb_design.py` | exit 0 |

## 3. Required corrections

### R1. The Excellon parser cannot read a real KiCad drill file

`parse_excellon` matches tool lines of the shape `T<n>C<diameter> Plated|NonPlated`. KiCad 10.0.5 writes the plating in a comment line before the tool line:

```text
; #@! TA.AperFunction,Plated,PTH,ComponentDrill
T1C3.000
; #@! TA.AperFunction,NonPlated,NPTH,ComponentDrill
T2C2.500
```

The parser returns `tools {}`, so `excellon_holes` raises `hit uses undefined tool T1`. C04 fails on every real file. The 25 tests use a synthetic tool line that KiCad does not write, so they do not cover the real format.

Correction:

- Read the `TA.AperFunction` comment that precedes each `T<n>C<d>` line, and take the plated flag from it.
- Add a test with the exact KiCad comment format.
- Keep the `--excellon-separate-th` output in mind. With that switch, the plated and nonplated tools are in two files and the `FileFunction` header differs.

### R2. `overall_status` fails open

`overall_status([])` returns `{"geometry_status": "pass", "fit_status": "pass"}`. A caller that omits a comparison gets a pass. `C06`, `C07` and `C09` are in the geometry id set, but no function produces them, so the geometry status does not reflect them.

Correction: the check must include every comparison id in the accepted list. A missing id is a failure. Add a test for the empty list and for a list with one id absent.

### R3. C03 does not compare the STEP radii

The accepted interface C03 covers the STEP cylinder radius and the DXF circle radius. `c03_diameters` uses the DXF circles only. The STEP radii are read and unused. In the real run the STEP radii are `1.25, 1.5, 1.6` and the DXF radii are the same. Compare both, and keep the DXF count check.

### R4. C06, C07, C08 and C09 are absent

The accepted interface and the reference list these items:

| ID | Missing item |
|---|---|
| C06 | Connector proxy placement against the frame record and the rotation rule |
| C07 | The insertion box, its membership set, its self-exclusion and the boolean volume |
| C08 | Proxy and body Z extents against the top and bottom height limits |
| C09 | Proxy extents against the cavity polygon, offset by the clearance |

There is no proxy solid, no `PROXY` label, no `fit-assembly.step`, no insertion box, no finished-board envelope use, and no cavity offset. `component-evidence.json` holds the placement and envelope, but no function consumes them.

### R5. The export, fit, report and release flow is absent

The accepted interface section 6 and section 8 define the end-to-end flow. `mechanical_fit.py` has no command entry point. `mechanical.py` has the helpers `release_outputs_ok`, `release_first_mismatch`, `release_record_hash` and `file_sha256`, but nothing builds `out/mechanical/board.step`, `outline.dxf`, `drill/`, `fit-assembly.step`, `mechanical-report.json`, or `out/release/mech-release.json`. There is no input capture, no freshness gate, and no publication refusal.

`pcb.py mechanical` routes only `mechanical.py check` and `mechanical.py readiness`. The reference documents only those two commands, so an agent cannot run the geometry comparisons.

Correction: add the fit and release entry point, the orchestration of the recorded switches, the report, the release record, the input capture and the freshness gate. Add one command that runs the full fit on a fixture copy.

### R6. The reference claims more than the code

`references/mechanical-fit.md` says that `mechanical_fit.py` performs "comparisons C01 to C12", that "a connector insertion volume contains no other solid", and that "component heights stay within their limits, measured from the finished-board mounting surfaces". The code does none of the three. Correct the reference to the implemented scope, or implement the scope. The reference must not describe a check that does not run.

## 4. Positive confirmations

- C01, C02, C02d, C03 (DXF), C05 and C12 pass on real exports within the fixed tolerance.
- `match_points` matches without vertex order and without alignment. A mirrored or incomplete outline fails.
- `substrate_solid` selects the one valid solid in the outline and refuses two solids. It uses the imported solid, not the text control points. This follows the lead addendum.
- The closed-hole-set check refuses an unlisted hole and permits an excluded hole.
- `settings_switches_ok` refuses inch DXF units, `--drill-shape-opt` other than 2, a missing STEP switch and a banned STEP switch.
- The two route tests and the `pcb.py mechanical` dispatch work.
- The frame rule matches the accepted Q7 rule.

## 5. Minor

- `parse_dxf` reads group-code lines in fixed pairs. It works on the KiCad DXF. A comment section with an odd line count would shift the pairs. The real file has an even count. Keep it, or state the assumption.
- `settings_switches_ok` reads `switches` only. It does not check the `excluded_switches` list. The current record is correct.
- The tests build synthetic DXF and Excellon text. Add one test with real KiCad bytes for each reader.

## 6. Limits

- I examined the frozen files and ran the commands above on a fresh fixture copy. I did not change a product file.
- I did not test C06 to C11 because they do not exist.
- The review covers the announced hashes only.

## 7. Next

After R1 to R6, I will re-review the frozen files and repeat the end-to-end run. The C04 real-format test and the fail-closed `overall_status` test are necessary before acceptance.

## 8. Boundary after the freeze

The review above applies to the announced Batch 2 hashes in section 1. After the freeze instruction, Claude disclosed that `mechanical_fit.py`, `tests/test_mechanical_fit.py` and the reference were overwritten by an R1 and R2 candidate:

| File | Announced hash (reviewed) | Current candidate hash (not reviewed) |
|---|---|---|
| `skills/pcb-design/scripts/mechanical_fit.py` | `22c99b0acb83aaa20411d85780d1bbc01b80bc507cfe2776209b710b4ef1ca39` | `a4a930661c767446e1e8c1c5dfd1ad86d5a4eb404b4a73e52ea7e1854db085dc` |
| `tests/test_mechanical_fit.py` | `fb4acb743d60260999f9d3f434613f910100be13fd63e8b2d2a9d2cd6ea1b05c` | `1cbfd6f0abbbcf2f3d5625b5b8a70787c3e9bf711901e471edc0251879db2dd7` |
| `skills/pcb-design/references/mechanical-fit.md` | `bdf22f27c442104d6610f120889f70e02ecfadc720427962d311e143a860614c` | `ea8abe2c0fb90500eceb4b1e64fcd8eeafb57fa21f22004bfb2d2d0171eeea4e` |

The candidate hashes are outside the reviewed scope. Per the lead instruction, I did not review them here. The Batch 2 decision stands for the announced hashes. The lead will combine the Codex findings and release a coherent completion batch, and I will review that batch.
