# B11 repair batch review: Pi

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Scope: the frozen repair batch `docs/reviews/mechanical/b11-repair-batch.sha256` (28 files) and `b11-repair-evidence/RUN-LOG.md`. Files stay frozen. I did not edit a product file.

Basis: interface revision 8, SHA-256 `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`, the completion direction, the repair release, and my completion review.

**Decision: the repair batch resolves P1 to P5 and I1 to I7 and the explicit cases. One new finding (N1) and two minor notes remain.**

## 1. Manifest and suites

The manifest SHA-256 is `f618d854b1b44f2a16af7baa9625380b3e1d5761d8737730802b49844373dfdb`. All 28 entries match.

| Suite | Result |
|---|---|
| `uv run tests/test_mechanical.py` | 46 pass, exit 0 |
| `uv run tests/test_mechanical_fit.py` | 43 pass, exit 0 |
| `uv run tests/test_skill_packages.py` | 8 pass, exit 0 |
| `uv run tests/test_project_io.py` | 11 pass, exit 0 |

## 2. Independent positive flow

Fresh fixture. Public dispatch, positional path:

```text
uv run scripts/pcb.py mechanical export DIR   exit 0
uv run scripts/pcb.py mechanical fit DIR      exit 0
uv run scripts/pcb.py mechanical release DIR  exit 0
```

The fit status is `{"geometry_status": "pass", "fit_status": "pass", "missing": [], "duplicates": [], "inconsistent": [], "problems": [], "failing": []}`. The export holds `board-PTH.drl` and `board-NPTH.drl`. The release record holds the explicit fields: `board_sha256`, `interface_sha256`, `component_evidence_sha256`, `fixture_source_sha256`, `export_settings_sha256`, `electrical_inputs`, `electrical_release_id`, `toolchain_image_id`, `fixture_id`, `first_mismatch`, and the output byte counts under `size`.

The positive report identifies each result by comparison ID and reference:

```text
C12 -, C01 -, C02d -, C05 -, C02 -, C03 -, C04 -,
closed_hole_set STEP, closed_hole_set DXF, closed_hole_set PTH, closed_hole_set NPTH,
C06 CN1, C07 CN1, C08 CN1, C09 CN1, C08 B1, C09 B1, C10 -, C11 -
```

## 3. Independent focused probes

| Correction | Probe | Result |
|---|---|---|
| P1 slot and oval | Add an oval NPTH pad and export | `drill.unsupported: DXF entity ARC is not supported; slots and arcs are refused`, fit exit 2 |
| P2 path escape | Add `/etc/hostname` to the export record | `export.outputs: The export record must name exactly the four export files.`, fit exit 1. `read_project` confines each record path. |
| P3 excluded reason | Add an excluded hole with no reason | `excluded.fields: Each excluded hole needs exactly: id, x, y, diameter_mm, plated, reason.`, exit 2 |
| Missing B1 | Remove the `B1` evidence record | `component.missing: No evidence record for: B1.`, exit 1 |
| Empty report | Set `results` to `[]` and release | Refused by the recomputed status with `problems: ["empty result set"]`, exit 1 |

The repair evidence lists the same cases, and adds extra hole, H1 plated, B1 height, blocker U9, mirrored CN1, unconfirmed, missing body length, wrong image, stale board and altered STEP.

## 4. Code confirmations

- `capture` keeps the bytes. `files_of` returns them, and `evaluate` receives the captured bytes for the board, interface, source, evidence, DXF, STEP, PTH and NPTH. No calculation reopens a live file (I1, I3).
- `_run_kicad` receives `image_id`, the measured image ID (I2).
- `read_project` and `_stage_dir` use `project_io.confine` (P2, I6).
- `run_fit` and `run_release` make a final freshness and output-integrity read before publication (I7).
- `run_release` recomputes the status with `recompute_status` and compares the recorded status with the recomputed status (I4).
- The release record uses the explicit fields, the byte counts under `size`, and the accepted mismatch order through `release_first_mismatch` (I5, I6).
- `validate_excluded` needs the id, position, positive diameter, plated flag and nonblank reason (P3).
- `check_required_components` refuses a missing reference and an extra reference (missing B1).
- `outward_cavity` offsets the convex outline outward by `clearance_mm`, chamfer included. `c09_cavity` tests every proxy corner inside the cavity or on its boundary. There is no mating-edge exemption (P5).
- `proxy_plan` places the connector body inward from its mating face, opposite the transformed insertion vector, with `body_length_mm` and zero overhang. The position and angle come from the source record through the transform (P5).
- The complete hole set is compared per output: STEP, DXF, PTH and NPTH.
- `pcb.py mechanical export|fit|release DIR` is a thin dispatch to the local module.

## 5. New finding

### N1. The interface connector `side` and `insertion_depth_mm` are not validated

The interface `connector_frames` item holds `side` and `insertion_depth_mm`. C06 compares the interface `x`, `y` and `rotation_deg` with the source-built proxy. C07 builds its insertion box from the evidence `insertion_depth_mm`. Neither comparison reads the interface `side` or the interface `insertion_depth_mm`.

Probe: set the interface `connector_frames[0].insertion_depth_mm` from `4.0` to `8.0`, re-export so the input is fresh, then fit. The fit exits 0 and C06 and C07 both pass. The wrong interface depth is accepted.

Correction: compare the interface `side` and `insertion_depth_mm` with the source or the evidence, or build the C07 insertion box from the interface depth. Add one negative case for a wrong interface depth and one for a wrong interface side.

## 6. Minor notes

- The `b11-repair-evidence/RUN-LOG.md` documents `pcb.py mechanical export|fit|release --project DIR`. The dispatch uses a positional path, so that command fails with `unrecognized arguments: --project`. The reference documents the correct positional form. Correct the RUN-LOG line.
- The `pcb.py mechanical export` route does not forward `--image`. It uses the module default `localhost/cad-skills-pcb:b6`, which equals the fixture pinned image. A fixture with another pinned image can only be exported through `scripts/mechanical.py export --image`. State this limit or forward the flag.

## 7. Residual integrity defects (root probe, reproduced)

The lead measured two residual integrity defects in `b11-freshness-review-root.md`. I reproduced the probe `b11-freshness-probe-root.py` (exit 0). Both controlled changes return success with different recorded and current hashes.

### R-A. `run_export` has no final source comparison

The probe appends a newline to `board.kicad_pcb` after the drill command returns. Measured:

- Recorded board hash `37105cf50e2bb0c997f7b9f6a02affef2f101a6b0684a4024d5a78541f8e20ba`.
- Current board hash `c0eefebadbd03641de8fa20f251b1733441b6729759001e4249ce260244d7c2d`.
- `run_export` returned success and wrote `export.json`.

Narrow correction: before the first export write, compare every consumed input with its captured hash. Reuse the `first_stale(inputs_record(cap), capture(project))` pattern that `run_fit` and `run_release` already use.

### R-B. `run_release` omits the report and the fit assembly from its final loop

The release binds the report and the fit assembly, but its final output loop reads only `report["outputs"]`. The probe appends a newline to `fit-assembly.step` and `report.json` during the release's second capture call. Measured:

| Output | Recorded hash | Current hash |
|---|---|---|
| `out/mechanical/fit-assembly.step` | `6a099c08be702f5580e4c7ada8b1227b0459dd84830b3084d049c4a7db474f0a` | `67a2e479e3ac59a561fcc6b8545834581f85a9c8c7924e8511f7dc60932826ad` |
| `out/mechanical/report.json` | `dc93a8319130536e39c8d1e8fa86db74d1923baeabab553200ae8d971c8cf768` | `cd1fdca13078d769dceea16f47832e8bedc7a51ee98bf1a0e07b837d9cc8787f` |

`run_release` returned success and wrote `mech-release.json`.

Narrow correction: compare all bound output bytes and byte counts before the release write, including the report and the fit assembly. Keep the captured bytes as the source for the decision.

### R-C (Codex R4). The release applies the generic stale order before the accepted mismatch order

Codex found that `run_release` runs `first_stale` before `release_first_mismatch`. I reproduced it:

| Change | Refusal | Accepted order would name |
|---|---|---|
| `release_id` only | `stale.input: mechanical/fixture-source.json changed after the fit` | `release_id` |
| board only | `stale.input: board.kicad_pcb changed after the fit` | `board_sha256` |

Revision 8 section 8 order starts with `electrical_release_id`, then `release_id`, then the hashes. The generic file check preempts it.

Narrow correction: apply the explicit expected fields in the accepted order first. Then run the generic stale check. Name the field with its expected and measured values.

### Agreement

I agree with the narrow corrections R-A, R-B and R-C (Codex R4). No broad repeat is necessary. Keep the finding N1 (the interface connector `side` and `insertion_depth_mm` cross-check). The batch resolves P1 to P5 and I1 to I7. R-A, R-B, R-C and N1 are the remaining corrections.

## 8. Limits

- I examined the frozen files and ran the probes above on copies in `/tmp`. I did not change a product file.
- The manifest, the suites and the positive flow are measured.
- The repair evidence is consistent with my probes.
- The review covers the announced manifest only. The set stays frozen until the lead releases it.
