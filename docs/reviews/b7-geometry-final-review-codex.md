# B7 geometry final checkpoint review

Date: 2026-11-14 UTC

## Hash measurements

All six files in `b7-geometry-final-checkpoint-claude.md` matched its hashes before and after this review.

| File | SHA-256 before and after |
|---|---|
| `skills/pcb-fab-package/scripts/inspect_mask.py` | `5676a31124670f3f307e06e7c3d2e385881622e2769b4f263e4e5023e6c243db` |
| `skills/pcb-fab-package/scripts/macro_defs.py` | `c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d` |
| `skills/pcb-fab-package/scripts/export_inspect.py` | `5be010bffda38af71ad1fba753d460bb65534d1d6c887999d8a1049d60ce759b` |
| `skills/pcb-fab-package/scripts/inspect_slots.py` | `9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc` |
| `skills/pcb-fab-package/scripts/board_inventory_slots.py` | `ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838` |
| `tests/test_pcb_fab_package.py` | `26b765635fd666577fa34dbf4a5ee0d8ad546b7188e82a385c66c791922954d2` |

The caller files are outside that six-file list. `fab.py` stayed at `d6d13ab732190b7be0a029fb1f3ce27c81506fd8f94c83e1989cffe2cbc2adeb`. `workflow.py` changed during this review from `2d5b58ca5af768ec50087a024cac8633a59c968fb941e9a78d6625832563bb13` to `bca595484e0298362d5173a5b94ae37360855a3ade8b3e114188c68c412adbb1`.

## Focused results

I ran the focused final-decision test through `uv`. All five checks passed. The test measured a 0.7 mm web for a radius above half the core side, retained overlap refusal, stopped a stalled worker through the public `fab inspect-mask` command, refused an existing report path, and wrote a pass result to a fresh path.

I called `fab.run_mask_worker` directly. It returned integer `0` and wrote a report. During my first read, the top-mask path in `workflow.py` accessed `rc_mask.returncode`. That access raises `AttributeError` for the returned integer. The file hash changed during this review. The current code compares `rc_mask` directly with the integer exit values, so the observed mismatch no longer exists in the current file.

The worker uses a cooperative two-second budget. The caller starts a new process group and sets a two-second timeout for each public mask run. On timeout, the caller stops the process group, removes any report, and returns exit 2. The test confirms this path through `fab inspect-mask`. The workflow calls the same helper for both mask files. I did not run a complete workflow or the 98-test suite.

## Verdict

The geometry replacement passes the focused review for the two final decisions and the listed geometry corrections. The measured caller timeout test passes, and the radius limit now follows the accepted core-distance formula. I cannot attest that `workflow.py` stayed frozen because its hash changed during review, and the checkpoint does not list that file. Add the final `workflow.py` hash to the next frozen record and retain a workflow-call regression. Full B7/B8 acceptance remains separate.
