# B7 complete correction review

Date: 2026-11-14 UTC

## Hashes and scope

All three frozen source and test files matched the freeze record before and after review.

| File | SHA-256 |
|---|---|
| `skills/pcb-fab-package/scripts/workflow.py` | `05ad9a5ab565d1eb0ef18d6d9a8b0e4575e869c9d9f7cb344de33811e82435d4` |
| `skills/pcb-fab-package/scripts/fab.py` | `84a09ec61fb3b453ff74e0a748b8974b17ac5739929697423e1c76bc615da3ca` |
| `tests/test_pcb_fab_workflow.py` | `bf80316793ee9e4090112688e17714a80ce97ab427ebfe60040fe8863ea1b1e1` |

The retained final log hash is `5a82c8bca456d1d8ad28bbcc0eae51ac729f5b9fc4168586e76d28036d22cf7d`. The log records 92 passing checks and exit 0. I did not run that suite.

## Accepted parts

The design, supplier and package functions hold `project_lock`. The result and binding files use `atomic_write`. Each result contains the hash of its binding. The package rejects a missing or changed binding. The six KiCad report keys and the row 15a product cases match the agreed decision.

The binding structure records hashes for generated outputs. However, the package does not bind the bytes that it copies into the final package. This gap blocks publication.

## Blockers

**C1: a profile scratch write can escape confinement.** `_package` calls `profile_from_bytes` before it confines the destination. That helper writes `supplier_dir/captured/profile.yaml`. A link at `captured` can direct the write outside the project. The design and supplier paths also check the top-level output but do not confine the nested `captured` path. Confine the full write path before mutation, or parse captured profile bytes without a scratch file. The root probe records the outside write.

**C2: the package can publish bytes that do not match the binding.** I ran `uv run docs/reviews/b7-package-copy-probe-root.py`. It used a temporary project and changed the source Gerber during `copy2`, then restored the source. The package returned exit 0 with status `qualified`, no reasons, and the injected Gerber bytes. The source hash returned to its prior value. The package recorded the injected bytes with a new hash.

`out_item` hashes the copied target and adds that current hash to the manifest. Later freshness checks examine the restored source and the measured source output. They do not compare the package copy with the accepted binding hash. Compare each copied artifact with its binding hash. Run the accepted semantic checks on the bytes in the package, or prove that the copied bytes equal the measured bytes before publication.

**C3: the package does not check the original manual record.** The supplier result retains the manual record in `supplier_dir/manual-evidence.json`. The package compares its `manual` snapshot key with that copy. It does not retain and compare the original manual record path and hash. The root probe appended a newline to the original record after supplier measurement. The package still returned exit 0 and status `qualified`. Record the original path and measured hash, then compare that file and the retained copy before publication.

**The operations do not consume all captured bytes.** `runtime_identity` reads `toolchain.lock.json` from the live project. `_supplier` reads source rules and project settings from live paths. It reads the order quantity with `VAL.load_record(project / "board.yaml")`. `_design` reads the board and supplier record again for the drawing facts. `_package` reads `board.yaml` again for manifest fields. These reads can differ from the captured snapshot. Pass the captured bytes to each consumer. The test that calls `stage_project` does not cover these live reads.

`captured` includes the manual record but not its referenced artifact. `check_manual` reads the artifact later. Bind the captured artifact bytes and use them for the copy and result.

**The final freshness gate runs too early.** `_package` compares source snapshots and binding outputs before it builds the evidence and manifest. It then writes the manifest and publishes without a final comparison. Compare captured inputs, raw reports, bindings, and copied outputs again immediately before `publish_dir`.

**The review-source command does not take the project lock.** It writes `REVIEW.json` and `observations.json` atomically, but it does not use `project_lock`. It can change review evidence while a locked package run reads and copies those files. Use the same project lock for this project write.

**The interruption case lacks a focused regression.** The package rejects a tampered binding. The test does not interrupt a write after a new binding and before its result. Add that case and confirm that the old result cannot pass against the new binding.

## Verdict

I do not accept the complete correction freeze for publication. C1, C2, C3, live input reads, the early freshness gate, and the unlocked review write remain blockers. The C2 root probe also reproduced a false qualified package. Supplier completeness and standalone acceptance remain outside this review. I did not change implementation files or run unrelated suites.
