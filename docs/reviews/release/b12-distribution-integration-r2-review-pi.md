# Distribution integration r2 review from Pi

Date: 2026-11-15 UTC.
Author: pi-release-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of the narrow classifier and candidate-set correction in the integration
worktree. This report writes no product file and does not edit the integration worktree. It
made no provider call.

## 1. Freeze and hashes

The freeze file
`docs/reviews/b12-distribution-integration-freeze-r2-root.sha256` in the integration
worktree has SHA-256
`2c92bbe9d79279b65818fd3d91473283525904c230fa48bf7e78dbfef9d8b392`. It matches the lead
message.

| Item | Before | After |
|---|---|---|
| Entries | 200 | 200 |
| `sha256sum -c` | 200 of 200 OK | 200 of 200 OK |
| Freeze file hash | `2c92bbe9...` | `2c92bbe9...` |

Key file hashes:

| File | SHA-256 |
|---|---|
| `tests/eval/packaging.py` | `e4761a18418478549050ef8d68327fd2fa8c62dbc4a255b9fbd985747b5edb99` |
| `tests/test_release_packaging.py` | `e23f828a058e48b4d132bd80b27037ac333a651efe8b4a7362cd5bf4716b0081` |
| `tests/test_release_harness.py` | `16d149bb55111032e2b0fa2a79ab531149b6a313d8accb6a963fd5c2af86d145` |
| `tests/eval/distribution.yaml` | `fe76d4b112d239f0f926cc18d03bf2bf57b2b974cf93db57af40244be49e6582` |
| `skills/pcb-fab-package/sources.yaml` | `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f` |

The `distribution.yaml` and `sources.yaml` hashes match the accepted release values. The
fixture and manifest entries are byte-identical to the release connection freeze. `comm`
reports no difference. No fixture byte or distribution manifest changed.

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_release_packaging.py` | 34 of 34 passed, exit 0 |
| `uv run tests/test_release_harness.py` | 65 of 65 passed, exit 0 |

No provider call and no network call.

## 3. Narrow difference

### Classifier

Old: `return "/supplier/" in f"/{rel}" or rel.startswith("docs/reviews/sierra-source-evidence/")`.
That substring matched project output directories.

New:

```python
parts = Path(rel).parts
skill_source = len(parts) >= 4 and parts[0] == "skills" and parts[2] == "supplier"
return skill_source or rel.startswith("docs/reviews/sierra-source-evidence/")
```

A path is a skill supplier source only when it sits under `skills/<name>/supplier/`. The
Sierra evidence root is unchanged.

Classifier probe:

| Path | Result | Expected |
|---|---|---|
| `skills/pcb-fab-package/supplier/pages/page.html` | True | True |
| `skills/pcb-fab-package/supplier/profiles/oshpark-two-layer.yaml` | True | True |
| `tests/eval/fixtures/artifacts/A2/project/out/fab/supplier/supplier-result.json` | False | False |
| `docs/reviews/sierra-source-evidence/xy.pdf` | True | True |
| `skills/pcb-design/scripts/pcb.py` | False | False |
| `skills/a/b/supplier/x` | False | False |

### Candidate set

`tracked_files` now reads tracked files and untracked nonignored files:

```text
git ls-files --cached --others --exclude-standard -z
```

It deduplicates and sorts. An untracked supplier file enters the check before a commit.

### New tests

| Test | Check |
|---|---|
| `test_untracked_supplier_file_enters_distribution_check` | An untracked `skills/demo/supplier/unlisted.txt` is in the candidate set and gives D-6 |
| `test_project_supplier_outputs_are_not_supplier_source_paths` | The exact A2 fixture path is not a supplier path. The unlisted skill supplier page gives the sole D-6 |

The second test names the exact A2 path
`tests/eval/fixtures/artifacts/A2/project/out/fab/supplier/supplier-result.json` and the real
source `skills/pcb-fab-package/supplier/pages/unlisted.html`.

### Freeze pointer

`tests/test_release_harness.py` points `FREEZE` at the integration freeze.

## 4. Agreement with the reviewer position

The correction matches the combined reviewer position in
`docs/reviews/release/b12-d6-a2-conflict-pi.md`:

1. Scope the classifier to the two documented roots. Done.
2. Do not add the 17 A2 fixture outputs to the supplier allowlist. Done.
3. Keep the tracked-plus-untracked candidate inventory. Done.
4. Keep the full-copy byte-hash exclusions. Unchanged.
5. Add the regression naming the A2 path and a real supplier file. Done.

## 5. Verdict

The narrow classifier and candidate-set correction is correct. The freeze has 200 entries
and all match. Packaging passes 34 of 34 and the harness 65 of 65. No fixture byte or
distribution manifest changed. The first integration proposal stays as history.

I accept the correction. A3 implementation can follow this review. Provider authorization
stays zero.

I made no edit in the integration worktree.

## Limits

This review ran focused local tests and one classifier probe. It made no provider call and
no CAD call. It changed no product file and did not edit the integration worktree.
