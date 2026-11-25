# Smallest repair for the Codex publication findings (proposal, not implemented)

Date: 2026-11-15 UTC. Basis: `docs/reviews/b7-final-publication-repair-review-codex.md`. No product file changed.

## 1. Standalone drawing leaves (C1)

Problem: `fab.py` `drawing-facts` and `drawing` write `--out` with `write_text` and `write_bytes`. A link at `--out` writes the outside file. The Codex probe changed a linked outside file.

Smallest repair:

- Add one helper in `fab.py`. Refuse a link at `--out`. Then call `PIO.atomic_write(out.parent, out, data)`.
- Use both branches. No new argument is needed.

Focused test: a link at `--out` for `drawing` and for `drawing-facts` exits 2. The outside target keeps its bytes.

## 2. Supplier result integrity and row consistency (C2)

Problem: the supplier result has no content hash. The package trusts its `exit` field. A changed mandatory row with an unchanged binding gave `qualified`.

Smallest repair:

- In `_supplier_measure`, add `content_sha256`, computed as `VAL.canonical_hash` of the result without that key. This follows the design result.
- In `_package`, call the same check that the design result uses (`check_result_content`). A mismatch is refused with `Stop`, not published as a draft.
- In `_package`, recompute the exit from the mandatory rows (all `pass` means 0, else 1). If the recomputed exit differs from `exit`, add a draft reason. The package is not qualified.

Focused tests:

- A changed mandatory row, with the content hash kept, is refused (exit 1, nothing published).
- A changed mandatory row, with the content hash recomputed, gives a draft with the row-consistency reason (exit 1, not qualified).

## 3. Final gate binding bytes (C5)

Problem: the final gate reads the binding JSON live and does not compare its bytes with the bytes captured at the start of the package.

Smallest repair:

- `_package` already holds `design_binding_raw` and `supplier_binding_raw` from `Reader`. Pass them to `final_gate`.
- In `final_gate`, compare the current binding bytes with those captured bytes, and with the `binding_sha256` in each result. Any difference is a problem. Nothing is published.

Focused test: change the design binding bytes after validation (in the same hook style as the staged tests). Expect exit 1, a `Stop` that names the binding, and no published package.

## Order and scope

- Items 1 to 3 are independent in code but share `workflow.py` (2 and 3) and `fab.py` (1).
- Run only `tests/test_pcb_fab_workflow.py` after the change. Freeze once.
- No new framework. Each repair uses `write_out`, `PIO.atomic_write`, `Reader`, `check_result_content` and `final_gate`, which already exist.
