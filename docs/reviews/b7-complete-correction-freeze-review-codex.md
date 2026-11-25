# B7 complete correction review (codex-skill-dev)

Date: 2026-11-15 UTC. Scope: the seven B7 corrections in the frozen `pcb-fab-package` workflow.
I changed no product file. I ran no broad accepted suite.

## Freeze and hash boundary

The freeze record hash is `0ff3976651f25171fd7bbdcad8a9a2314fe62690785027aa63fdfbb2fdb46772`.
All 17 entries in `docs/reviews/b7-workflow-evidence/c4c6c7-freeze.sha256` passed before and after my probe.
The command `sha256sum -c docs/reviews/b7-workflow-evidence/c4c6c7-freeze.sha256` returned exit 0.
The source hashes match the freeze record:

| File | SHA-256 |
|---|---|
| `skills/pcb-fab-package/scripts/workflow.py` | `65f88be99b9fb758fc095e9086f954688eb1b240b5f192d69d9660bceb075f0b` |
| `skills/pcb-fab-package/scripts/fab.py` | `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be` |
| `tests/test_pcb_fab_workflow.py` | `0686624ec3c0072279f747053dff649f8293cbcb02dfacb54e14c02d4d920932` |

## Findings

### C1: file links and direct write paths block acceptance

Root measured a link at `captured/profile.yaml`. The profile call returned without refusal and wrote outside the project.
The outside file hash was `2aedaa0c8076b18005345bf0f56f97396121e1faae915152d5bfcf10a942ad87`.
The directory-link regression remains valid, but it does not check a link at the file path.

The direct-write inventory follows. A directory check does not confine a child file path.
The write locations below need complete path confinement and the existing atomic write helper.

| Operation | Direct write paths |
|---|---|
| `_design` | `captured/profile.yaml`, `logs/*.stderr`, `inventory.json`, `erc.json`, `drc.json`, `export/*`, `drawing-facts.json`, `fabrication-drawing.pdf` |
| `_supplier` | `captured/profile.yaml`, `supplier-drc.stderr`, `slots.json`, `mask.json`, `mask-bottom.json`, `supplier.kicad_dru`, `supplier.kicad_pro`, `supplier-drc.json`, `manual-artifact.txt`, `manual-evidence.json` |
| `_package` | `supplier/captured/profile.yaml`, staged `gerber/*`, `docs/*`, `reports/*`, `evidence/*`, and `manifest.json` |
| Helper reports | `inspect_slots.py` writes the report path directly. The mask worker writes its report directly after a freshness guard. |
| Other `fab.py` commands | `drawing-facts` and `drawing` write their `--out` path directly. These commands sit outside the design, supplier, and package write set. |

`review-source` uses `PIO.atomic_write` for both records. Its project lock covers the reads and writes.
The complete C1 probe results and path inventory appear in `b7-complete-correction-freeze-review-pi.md`.

### C2: capture each consumed result and design input once

The package reads `supplier-result.json` to decide qualification. Later, `out_item` reads that file again for the package copy.
The result file does not appear in the supplier binding.

Pi changed the result between those reads. The package returned exit 0 with status `qualified` and no reasons.
The published `reports/supplier-result.json` held the injected field.
Its hash was `b1889ec18892c620aa76683354d9b01185ad76c17d04ad57c91e125ec4bf5ae9`.
The package therefore used one byte set for its decision and published another.

The package also reads `design-result.json`, `observations.json`, and `REVIEW.json` more than once.
Pi measured a changed `design-result.json` as draft because the supplier result caught the mismatch.
The other two changed inputs also have checks, but the package still copies bytes from a second read.
Capture each consumed file once. Use the captured bytes for decisions and copies. Retain the same hash.

The supplier reads `inventory.json`, PTH and NPTH drill exports, and top and bottom mask Gerbers from live paths.
It does not compare those bytes with the design binding before it uses them.
Compare each captured design output hash with the design binding before supplier checks.
Use those captured bytes for slot and mask checks.
At package time, compare each supplier measurement hash with the matching staged Gerber hash.
This prevents a transient design output change from supplying a measurement for different published bytes.
Pi did not reproduce this transient supplier-input case.

### C5: the final gate does not bind staged package bytes

I ran `uv run docs/reviews/b7-workflow-evidence/b7-c5-staged-output-probe-codex.py`.
The command returned exit 0. The package returned exit 0 with status `qualified` and no reasons.
The probe changed `gerber/board-F_Cu.gbr` after the second validator call and before the final gate.
The published file held the injected bytes.
Its hash was `a146a538dde04b616d6d2727cc7f292bc60f403e9ea26ab8bc571fd7470b656c`.
The manifest hash was `84aab678577a12141a0c17ab90620f00a5a3b30d6b44ee79444c3b00761324d7`.
The temporary project was `/tmp/b7-c5-codex-9vnv5uml`.

The final gate compares source inputs, bound source outputs, and the original manual record.
It does not compare staged package outputs with the hashes that the validator checked.
Hash the staged manifest and each staged output immediately before `PIO.publish_dir`.
Refuse publication if any hash differs.

### C3, C6, and C7

The manual record check passes the focused byte-change probe. A changed original record returns exit 1 and draft status.
The final gate compares the original record, the retained copy, and its referenced artifact.

The source-review lock passes the focused held-lock probe. The command returns exit 2 and keeps prior records.
The interrupted binding probe also passes. The old result cannot pass against the new binding.

## Verdict and limits

C1, C2, and C5 block acceptance. C3, C6, and C7 pass their focused probes.
The accepted geometry and report-key results remain outside this review.
Pi's report records the focused commands, outputs, and file hashes for the other probes.

The C5 probe used an in-process hook and a temporary project. It changed staged bytes after validation.
The C1 root probe used a symbolic link to a temporary outside file.
The supplier design-input case remains an inspection finding. I did not measure it.
The probes do not prove a race with another process. I ran no broad suite.
