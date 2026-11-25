# B7 residual publication repair review (codex-skill-dev)

Date: 2026-11-15 UTC. Scope: the frozen C1, C2, and C5 residual repair.
I changed no product file. I ran no suite.

## Freeze boundary

The freeze record hash is `08ec5765fa96e35988a2d08cb70b60a72687aa28bc551bb2a6f64b228ac93b06`.
All five entries in `docs/reviews/b7-workflow-evidence/residual-freeze.sha256` pass.
The command `sha256sum -c docs/reviews/b7-workflow-evidence/residual-freeze.sha256` returns exit 0.
This is the same source and test set that Pi reviewed.

| File | Before review | After review |
|---|---|---|
| `skills/pcb-fab-package/scripts/workflow.py` | `b81466ee0e8329abdb82472083a26d9497efe2d0a3cbea9acb40947d44cc969e` | `b81466ee0e8329abdb82472083a26d9497efe2d0a3cbea9acb40947d44cc969e` |
| `skills/pcb-fab-package/scripts/fab.py` | `5be6e136b7ebf193d6df11798104c26f10f15c89ee23d4e4409306308d802e0c` | `5be6e136b7ebf193d6df11798104c26f10f15c89ee23d4e4409306308d802e0c` |
| `tests/test_pcb_fab_workflow.py` | `a973b5be6164cc8b1eb26fa3dc7636a37099834511db2f539817f95f02b972de` | `a973b5be6164cc8b1eb26fa3dc7636a37099834511db2f539817f95f02b972de` |

## Review result

The three residual corrections meet the released scope.

The standalone drawing commands refuse a link at the output file or its parent directory.
They use `PIO.atomic_write` and state that the parent directory is the output root.
They do not claim project confinement. The focused tests cover a dangling facts link, a PDF link, and an ordinary output.

The package validates the supplier result before it uses the result.
The validator checks the content hash, selected profile, unique conditions, required rows, row statuses, and exit.
It keeps the former exit precedence. A consistent failing row produces a draft.
The tests cover a changed row with an old hash, a changed row with a new hash and bad exit, a missing row, and a valid failing row.

The final gate compares current binding bytes with captured bytes and each result's binding hash.
It reads the output map from the captured bindings.
The staged gate compares the manifest and all listed output hashes and dimensions.
It rejects links, missing outputs, and unexpected files.
The binding-drift test changes a binding after validation and requires a nonzero result with no final package.

The author logs record 132 of 132 workflow checks and 101 of 101 package checks.
Both commands return exit 0. The log hashes are `90434d2d36091b01c134ed26207734dd2dc6f4cae49e4057afbf8226f90f6b5e` and
`efd9c46d0650857d5a5fadd6b98bdd934474256ef3b5f27621503f7ff2d1aa88`.
I read the retained logs. I did not rerun either suite.

C3, C6, C7, geometry, and report-key results remain accepted.
The content hash detects changes. It does not prove authorship, as the freeze record states.

## Verdict

I found no remaining blocker in the reviewed residual scope.
Keep the output-root rule for standalone drawing commands.
Keep all content and profile checks for the supplier result.
Keep the final binding and staged package comparisons before publication.
