# B11 residual batch review: Pi

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Scope: the frozen residual batch `docs/reviews/mechanical/b11-residual-batch.sha256` (21 files) and `b11-residual-evidence/RUN-LOG.md`. Files stay frozen. I did not edit a product file.

Basis: interface revision 8, SHA-256 `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`, the residual correction release, and my repair review.

**Decision: the batch resolves N1 and R-A, R-B, R-C. I give explicit agreement. One minor RUN-LOG wording note follows.**

## 1. Manifest and suites

The manifest SHA-256 is `2f264b6790010a58e5771fbb62ee2542c725528ac05bc344baa002fd31a82204`. All 21 entries match.

| Suite | Result |
|---|---|
| `uv run tests/test_mechanical.py` | 55 pass, exit 0 |
| `uv run tests/test_mechanical_fit.py` | 43 pass, exit 0 |
| `uv run tests/test_skill_packages.py` | 8 pass, exit 0 |
| `uv run tests/test_project_io.py` | 11 pass, exit 0 |

`skills/pcb-design/scripts/mechanical_fit.py` keeps the hash `a5a6ef320390ee7cca0ea84ffcb7c94a5102e4df84a0bd0574883f9eb4c0802c`. It is byte-identical to the repair batch. The geometry, the hole sets and the cavity rules are unchanged.

## 2. Independent positive flow

Fresh fixture, public dispatch, positional path:

```text
uv run scripts/pcb.py mechanical export DIR   exit 0
uv run scripts/pcb.py mechanical fit DIR      exit 0
uv run scripts/pcb.py mechanical release DIR  exit 0
```

## 3. Independent focused probes

| Correction | Probe | Measured refusal |
|---|---|---|
| R1 and N1 connector agreement | Set the interface `side` to `bottom`; source and evidence stay `top` | `connector.mismatch: CN1: side differs: interface 'bottom', source 'top', evidence 'top'.`, exit 1 |
| R1 and N1 connector agreement | Set the interface `insertion_depth_mm` to `8.0`; source and evidence stay `4.0` | `connector.mismatch`, names `insertion_depth_mm`, exit 1 |
| R-A export drift | Change the live board during the export (test `test_export_source_drift_refused_before_publication`) | `stale.input`, names `board.kicad_pcb`, and nothing is published |
| R-B release gate | Append to `fit-assembly.step` before release | `stale.fit_assembly: The fit assembly changed after the fit.`, exit 1, no release record |
| R-B release gate | Change a bound output before release | `export.altered`, exit 1, no release record |
| R-C mismatch order | Change `release_id` only | `release.mismatch: First mismatch: release_id (expected b11-mech-fit-a-r1, measured b11-other).`, exit 1 |
| R-C mismatch order | Change the board only | `release.mismatch: First mismatch: board_sha256 (expected 37105cf5..., measured c0eefeba...).`, exit 1 |

The `release_id` and board refusals use the explicit order and name the field. The generic `stale.input` check no longer preempts them.

## 4. Code confirmations

- `check_connector_agreement` compares the interface, source and evidence `side` and `insertion_depth_mm` for each connector frame. It raises `connector.mismatch` with the connector and the field.
- `run_export` compares the captured inputs before the first publication write. A change refuses with `stale.input` and publishes nothing.
- `run_release` calls `release_first_mismatch` before `first_stale`. The accepted order runs first.
- The final release gate covers every bound output and its byte count, including the report and the fit assembly.
- `cmd_mechanical` passes a positional fixture path and forwards the optional `--image` to `export` only. The reference documents this.

## 5. Minor note

The RUN-LOG says a changed `release_id` is refused "naming `mechanical/fixture-source.json` through the explicit mismatch order". The measured refusal names `release_id`. The test `test_release_id_change_names_fixture_source_first` has the same misleading name. The behavior is correct. Correct the two descriptions to say that the refusal names `release_id`.

## 6. Limits

- I examined the frozen files and ran the probes above on copies in `/tmp`. I did not change a product file.
- The manifest, the suites, the positive flow and the refusals are measured.
- The review covers the announced manifest only. The set stays frozen until the lead releases it.
