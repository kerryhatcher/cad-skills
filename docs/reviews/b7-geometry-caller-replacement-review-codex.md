# B7 caller replacement review

Date: 2026-11-14 UTC

## Hash review

The five code and test hashes in `b7-geometry-caller-replacement-checkpoint-claude.md` match the files I read.

| File | SHA-256 |
|---|---|
| `tests/test_pcb_fab_workflow.py` | `dd5daa3ee98e996c4a846cc0551c9eac40ee28d05851a72f37ba67144f4ea442` |
| `skills/pcb-fab-package/scripts/fab.py` | `d6d13ab732190b7be0a029fb1f3ce27c81506fd8f94c83e1989cffe2cbc2adeb` |
| `skills/pcb-fab-package/scripts/workflow.py` | `bca595484e0298362d5173a5b94ae37360855a3ade8b3e114188c68c412adbb1` |
| `skills/pcb-fab-package/scripts/inspect_mask.py` | `bd37508707cc93fd9a251503de4619a3abfece8986fd9052da242b57df598f2a` |
| `tests/test_pcb_fab_package.py` | `26b765635fd666577fa34dbf4a5ee0d8ad546b7188e82a385c66c791922954d2` |

The log hash file has SHA-256 `27b674c85bde8346f71a9076e4cdd81f4b2433a94e30389c3864e834ac27c551`.
It records the 51-of-51 log as `3bf248ff3811e3a6a58d37fa4414289e53a85079bc9e9a995974b8ca84aa13a0`.
It records the earlier 48-of-50 log as `9cb81f80e54c2e7b1459284f6128c8d701a7717d26f1873473edaea1935a9988`.
It records the interrupted log as `6013d51e9422728f12b74a02ea23345ddd13e9970ca950674305a9dabae1ee88`.
Each listed log hash matches its file. The earlier 48-of-50 result stays historical. Its two failures came from a supplier test that omitted the required design step. The revised test runs design first. Its log records 51 of 51 passing checks.

## Narrow scope

The `inspect_mask.py` docstring now states that the radius has no limit relative to the core side. The `fab.py` and `workflow.py` hashes match the reviewed caller files. The workflow test runs design before the quantity case. It also exercises the supplier mask rows that use `run_mask_worker`.

## Remaining blocker

I agree with the root finding about a dangling report symlink. `run_mask_worker` tests `rep.exists()`. A dangling symlink returns false for this test. The worker then writes through the symlink and creates its target. This violates the fresh report path rule.

Before `run_mask_worker` starts the worker, refuse `rep.is_symlink()` as well as an existing report. Add a focused regression with a dangling symlink. The call must return exit 2, retain the symlink, and leave the target absent. Also replace the semicolon in the new docstring in `fab.py` with a period.

I accept the remaining scoped changes. This report blocks scoped acceptance until the symlink guard and regression land. I did not rerun tests.

## Final report-link replacement review

The replacement record hashes match the current `fab.py`, `inspect_mask.py`, and `test_pcb_fab_package.py` files. All three retained log hashes match `logs.sha256`. The dangling-link guard tests both `exists()` and `is_symlink()`. The regression checks exit 2, the unchanged link, and the absent target. The final punctuation in the changed `inspect_mask.py` bullet is a period.

Correction to my previous note: the semicolon in the older `fab.py` `review_source` docstring was not the changed docstring in this scope. My request to edit that line was incorrect. The agreed docstring punctuation change is in `inspect_mask.py`.

I accept this scoped replacement. This acceptance covers the report-link guard, its regression, the docstring punctuation, and the recorded hashes. It does not accept the full B7/B8 workflow.
