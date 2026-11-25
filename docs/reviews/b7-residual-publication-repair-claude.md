# B7 residual publication repair freeze (claude-skill-dev)

Date: 2026-11-15 UTC. Frozen replacement for both reviewers, under `b7-residual-publication-release-root.md`. Original worktree `/mnt/storage/projects/cad-skills`, uncommitted. No commit. Geometry unchanged. Earlier freezes stay as history.

## Changes

1. **Drawing output.** `fab.py` `drawing-facts` and `drawing` write through `write_standalone`. It refuses a symbolic link at `--out` (including a dangling link) and a link at its directory before any write. It then calls `PIO.atomic_write`. These commands have no project argument, so the output root is the parent directory of `--out`. No project confinement is claimed.
2. **Supplier result.** `_supplier_measure` adds `content_sha256`. `validate_supplier_result` runs in the package before the result is consumed. It checks the content hash, the profile id and hash, the row set (no missing, no extra, no repeated mandatory condition), each row status, the non-mandatory rows, and the exit. The exit is recomputed by `rows_exit`, which keeps the existing precedence. A mismatch raises `Stop`, so nothing is published. The design result is checked the same way (`check_result_content`).
3. **Final binding comparison.** The package passes the captured binding bytes to `final_gate`. The gate compares the current bytes with those bytes and with each result's `binding_sha256`. It then checks the output map of the captured binding. Drift keeps the staging directory and publishes nothing.

## Tests

- `test_supplier_rows`: a changed row with the old hash is refused. A changed row with a new hash and an inconsistent exit is refused. A missing mandatory row is refused. A consistent failing row is a draft, not a refusal.
- `test_binding_drift`: a binding changed after validation is refused. Nothing is published.
- `test_drawing_links`: a dangling link at `drawing-facts --out` and a link at `drawing --out` are refused with exit 2. The targets are unchanged. An ordinary output still writes.

## Commands and results

- `uv run tests/test_pcb_fab_workflow.py`: 132 of 132, exit 0. Log `docs/reviews/b7-workflow-evidence/workflow-run-residual.log`.
- `uv run tests/test_pcb_fab_package.py`: 101 of 101, exit 0. Log `docs/reviews/b7-workflow-evidence/test_pcb_fab_package-residual.log`. Run because `fab.py` drawing branches changed.
- No broad suite was run.

## Limits

- The content hash detects changes. It is not a signature and does not prove authorship.
- The controlled changes are in-process hooks, or edits between subprocess runs. They do not prove a race with another process.
- Standalone drawing commands state their output-root rule. They do not confine to a project.
- `review.gate` and the validator still read some live files, as recorded in the earlier freeze.

## SHA-256

```
b81466ee0e8329abdb82472083a26d9497efe2d0a3cbea9acb40947d44cc969e  skills/pcb-fab-package/scripts/workflow.py
5be6e136b7ebf193d6df11798104c26f10f15c89ee23d4e4409306308d802e0c  skills/pcb-fab-package/scripts/fab.py
a973b5be6164cc8b1eb26fa3dc7636a37099834511db2f539817f95f02b972de  tests/test_pcb_fab_workflow.py
90434d2d36091b01c134ed26207734dd2dc6f4cae49e4057afbf8226f90f6b5e  docs/reviews/b7-workflow-evidence/workflow-run-residual.log
efd9c46d0650857d5a5fadd6b98bdd934474256ef3b5f27621503f7ff2d1aa88  docs/reviews/b7-workflow-evidence/test_pcb_fab_package-residual.log
```
