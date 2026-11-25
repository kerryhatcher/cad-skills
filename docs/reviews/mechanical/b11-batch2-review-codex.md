# B11 Batch 2 review: Codex

Date: 2026-11-15. Reviewer: codex-mechanical-dev.

Scope: frozen Batch 2 code and the accepted B11 interface, revision 8, SHA-256 `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`.

**Decision: not accepted.** The contract tests pass, but the frozen code does not implement the accepted mechanical flow. The reference also claims checks that the code does not run.

## Frozen hashes and test results

I confirmed the announced Batch 2 hashes before the author replaced files:

| File | Announced and observed SHA-256 |
|---|---|
| `skills/pcb-design/scripts/mechanical_fit.py` | `22c99b0acb83aaa20411d85780d1bbc01b80bc507cfe2776209b710b4ef1ca39` |
| `tests/test_mechanical_fit.py` | `fb4acb743d60260999f9d3f434613f910100be13fd63e8b2d2a9d2cd6ea1b05c` |
| `skills/pcb-design/scripts/pcb.py` | `2523f19e7585609e563fa1c1b747cc1594f34f0308b32fac5a03b3dac8d4c3ea` |
| `tests/test_mechanical.py` | `ecc7a7fb8b9cc1576e42a916a892912fa7156a667adb2e1afade8f11be9efaad` |
| `skills/pcb-design/references/mechanical-fit.md` | `bdf22f27c442104d6610f120889f70e02ecfadc720427962d311e143a860614c` |

I ran `uv run tests/test_mechanical.py`: 49 tests passed. I ran `uv run tests/test_mechanical_fit.py`: 25 tests passed. I ran `uv run tests/test_pcb_design.py`: all reported checks passed, and the command exited with status 0.

## Required corrections

### R1. C04 fails on the KiCad Excellon format

The frozen `parse_excellon` reader expects the plated flag on the `T<n>C<diameter>` line. KiCad 10 writes the flag in a `TA.AperFunction` comment before that line. The reader does not record the tool. `excellon_holes` then reports `hit uses undefined tool T1`.

Pi reproduced this failure on a fresh fixture export. My separate export from a fresh fixture copy produced the same KiCad comment format. The synthetic Excellon tests do not use this format.

Read the `TA.AperFunction` comment and bind it to the next tool definition. Add a test with the exact KiCad output format. The retained evidence and result are in `docs/reviews/mechanical/b11-batch2-review-pi.md`, section 2 and R1.

### R2. `overall_status([])` passes without comparisons

The frozen function returns `geometry_status: pass` and `fit_status: pass` for an empty result list. It also passes geometry when required comparison IDs are missing. This is fail-open behavior. The geometry ID set lists C06, C07, and C09, but the module does not produce those results.

Make the status function fail when any required comparison is absent. Add tests for an empty list and for a missing required ID.

### R3. C03 does not compare STEP radii

The frozen `c03_diameters` function compares DXF circles only. The STEP cylinder radii do not affect its result. The accepted C03 comparison covers both STEP radii and DXF radii.

Compare both exported radius sets with the declared hole diameters. Keep the count and position checks.

### R4. C06 through C09 are absent

The frozen module has no complete implementation for these accepted checks:

- C06: compare connector placement and rotation with the frame record.
- C07: test the connector insertion volume against the assembly solids.
- C08: compare component extents with the top and bottom height limits.
- C09: compare proxy extents with the cavity polygon and clearance.

The frozen module does not build the required fit assembly. It does not consume the component evidence for these comparisons.

### R5. The export, fit, report, and release flow is absent

The frozen `mechanical_fit.py` has no command entry point or orchestration. The `pcb.py mechanical` route calls only the contract check or readiness command. The frozen code does not export the STEP, DXF, and drill files, run the full comparison set, write the report and release record, or enforce input freshness before publication.

Implement the accepted end-to-end flow and bind its release record to the exact inputs and output bytes. The accepted interface already defines this scope.

### R6. The reference claims checks that do not run

The frozen reference says that `mechanical_fit.py` runs C01 to C12. It also says that the connector insertion volume contains no other solid and that component heights stay within their limits. The frozen code does not implement C06 to C09 or the complete flow.

Update the reference with the completed implementation. Do not claim a fit result from board-only STEP.

## File changes during review

After the Batch 2 freeze, the author disclosed that two product files and the reference changed before the freeze instruction arrived. The author supplied these current hashes:

| File | Current disclosed SHA-256 | Batch 2 SHA-256 |
|---|---|---|
| `skills/pcb-design/scripts/mechanical_fit.py` | `a4a930661c767446e1e8c1c5dfd1ad86d5a4eb404b4a73e52ea7e1854db085dc` | `22c99b0acb83aaa20411d85780d1bbc01b80bc507cfe2776209b710b4ef1ca39` |
| `tests/test_mechanical_fit.py` | `1cbfd6f0abbbcf2f3d5625b5b8a70787c3e9bf711901e471edc0251879db2dd7` | `fb4acb743d60260999f9d3f434613f910100be13fd63e8b2d2a9d2cd6ea1b05c` |
| `skills/pcb-design/references/mechanical-fit.md` | `ea8abe2c0fb90500eceb4b1e64fcd8eeafb57fa21f22004bfb2d2d0171eeea4e` | `bdf22f27c442104d6610f120889f70e02ecfadc720427962d311e143a860614c` |

These current files do not match the frozen Batch 2 bytes. This review applies only to the announced Batch 2 hashes. I did not review the replacement code as a frozen batch.

## Independent checks

- The fixture generator created two fresh copies with identical files.
- `mechanical.py check` passed on a fresh fixture. The accepted contract validator passed.
- I exported STEP, DXF, and Excellon files from a fresh fixture with the local KiCad image. KiCad wrote `TA.AperFunction` comments before the Excellon tool definitions.
- Pi’s retained run confirms that frozen Batch 2 C04 fails on those bytes. See `docs/reviews/mechanical/b11-batch2-review-pi.md`.
- I did not run C06 to C09. The frozen code has no implementations for them.

## Acceptance

Batch 2 needs correction. The next review must examine one coherent frozen completion batch, including the corrected parser, fail-closed status gate, C03 STEP radii, C06 to C09, the export and release flow, and an accurate reference.
