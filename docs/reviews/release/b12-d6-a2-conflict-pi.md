# D-6 A2 path conflict from Pi

Date: 2026-11-15 UTC.
Author: pi-release-dev (Pi pane `w1P:pF`), reviewer.

Scope: one concrete conflict with the planned D-6 integration correction. This report
writes no product file and does not edit the release worktree. It made no provider call.

## Confirmed

- The A2 fixture holds 17 files under
  `tests/eval/fixtures/artifacts/A2/project/out/fab/supplier/`.
- `_is_supplier_path` matches any `/supplier/` substring:
  `return "/supplier/" in f"/{rel}" or rel.startswith("docs/reviews/sierra-source-evidence/")`.
- Thus each of the 17 project-authored fixture outputs is treated as a supplier path. The
  D-6 finding follows from the path rule, not from a byte match.

## Concrete conflict

The per-file allowlist approach conflates two categories.

The `tests/eval/distribution.yaml` allowlist names supplier evidence that a distribution may
carry. The A2 `out/fab/supplier/` files are project-authored harness fixture outputs. Adding
them to the supplier allowlist labels fixture outputs as distributable supplier data and
requires one exact entry for each of the 17 files. A later A2 output change needs allowlist
churn again.

The narrow fix is to scope the path rule, not to expand the allowlist:

- Restrict `_is_supplier_path` to the supplier evidence roots: a path under
  `skills/*/supplier/` or under `docs/reviews/sierra-source-evidence/`.
- Or exclude `tests/eval/fixtures/**` from the distribution candidate set.

With either change, the 17 A2 files are not supplier paths and need no allowlist entries.
The full-copy byte-hash exclusions stay active.

If the lead keeps the allowlist approach, the exact 17 paths must come from the A2 freeze
manifest to avoid omission, and each entry must be labeled as a fixture path, not a supplier
source. The `_is_supplier_path` rule remains a substring match on `/supplier/`.

The second change (include untracked nonignored files in the candidate set) is correct. It
will expose the same false positive for any future fixture that uses a `supplier/` directory,
so it strengthens the case for the rule fix.

## Agreed resolution

Codex agrees with the finding and the resolution.

1. Scope `_is_supplier_path` to `skills/*/supplier/` and
   `docs/reviews/sierra-source-evidence/`.
2. Do not add the 17 A2 fixture outputs to the supplier evidence allowlist.
3. Keep the tracked-plus-untracked candidate inventory.
4. Keep the full-copy byte-hash exclusions.
5. Add a regression: the A2 path
   `tests/eval/fixtures/artifacts/A2/project/out/fab/supplier/supplier-result.json` is not a
   supplier path, and a real supplier file under `skills/pcb-fab-package/supplier/pages/`
   still receives D-6 when it is not allowlisted.

Both reviewers also confirm the A3 local-copy path correction:
`tests/eval/fixtures/artifacts/A3` with the `standard-project` and `retained/pkg-standard`
subtrees.

## Limits

This report read the A2 fixture tree and the checker rule. It made no provider call and
changed no file.
