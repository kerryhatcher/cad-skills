# Release task handoff from Pi

Date: 2026-11-15 UTC.
Author: pi-release-dev (Pi pane `w1P:pF`), reviewer.

Reason: context use is approximately 68 percent of the 1,048,576-token window
(712,631 reported total tokens at the last turn). This handoff is compact.

## 1. Worktrees and commits

| Item | Value |
|---|---|
| Release worktree | `/mnt/storage/projects/cad-skills-worktrees/release` |
| Release branch | `work/release`, base `75d99da` |
| Integration worktree | `/mnt/storage/projects/cad-skills-worktrees/integration` |
| Integration branch | `work/integration`, A3 commit `a6816ce` |
| My reports | `docs/reviews/release/` in the release worktree |

## 2. Accepted freezes

| Freeze | SHA-256 |
|---|---|
| Harness `b12-a2-run-binding-freeze-claude.sha256` | `4d250e0a163bdd514b4051fc3e909752c0ae7dcade5f8ddf10ba4b652e170c40` |
| BOM OLE2 `b12-bom-ole2-freeze-r3-claude.sha256` | `ff67bca674b75a01ff66428c6465677cdc07733d8e57cb9ce099f5483112520c` |
| Source-path normalization r2 `b12-source-path-normalization-freeze-r2-claude.sha256` | `407e030d809852f9a5a3d4b1d1a98d977431cb4d008464e0b1c8b38bfceaeb32` |
| A1/A2 fixtures `artifact-a1-a2-freeze-r2-claude.sha256` | `7b01b363285f96e36ece6be1f74517f62622c9fd13dd29f3b1d21b546752bc26` |
| Distribution integration r2 `b12-distribution-integration-freeze-r2-root.sha256` | `2c92bbe9d79279b65818fd3d91473283525904c230fa48bf7e78dbfef9d8b392` |
| A3 connection `b12-a3-connection-freeze-root.sha256` | `7ae60dedf3ca70de0fcb79b4fef9f96a58bf764905fbc9d5d314ea51b116290a` |

Packaging P-6 and P-7 are accepted separately at their unchanged hashes.

## 3. Open state

- Provider authorization is zero. No paid run occurred.
- A3 stays held. Its fixture is unqualified: ten pass, DRC and stock fail, supplier rules
  unconfirmed, physical tests not measured.
- A2 stays deliberately incomplete. Do not change A2 now.
- The next task follows the B7 completion freeze. Its new process facts and `via` declaration
  need a separate A2 refresh.
- The pending `pcba-design` snippet routing entry belongs to integration.

## 4. Key implementation facts

- Harness roots: `fixture` and `run`. A3 uses local copies at
  `tests/eval/fixtures/artifacts/A3`.
- Checker kinds: `exists`, `absent`, `sha256`, `json_equals`, `json_path_equals`,
  `row_equals`, `row_set_equals`, `length_equals`, `row_binding`, `sha256_binding`,
  `record_binding`. Values compare with JSON types.
- `_is_supplier_path` is scoped to `skills/<name>/supplier/` and
  `docs/reviews/sierra-source-evidence/`.
- The candidate set includes tracked plus untracked nonignored files.
- The A3 fixture has 59 copies bound by `source-copy-hashes.json` to PCBA manifest
  `d419688f2e4b5b30a35209985f619c2fc46ae2d58c2a1d949feb9ab24079ca64`.

## 5. Host limits

- The bwrap boundary is host-specific. A host without working bwrap fails the isolation
  suite. Use a checkout path with no symlinked ancestor.
- A symlinked manifest-directory ancestor reports D-9 for every binding.

## 6. Next steps for a fresh session

1. Read the B7 completion freeze and its process facts.
2. Prepare the separate A2 refresh scope and acceptance, including the `via` declaration.
3. Do not change A2 until the lead releases that refresh.
4. Keep provider authorization zero and A3 held.
5. Use `uv` for all Python. Reviewers write reports only.

## Limits

This handoff reads accepted records and the session usage. It made no provider call. It
changed no product file.
