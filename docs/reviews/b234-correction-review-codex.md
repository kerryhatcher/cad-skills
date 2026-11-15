# B234 correction review: Codex

Date: 2026-11-14.

**Decision: one R1 blocker remains**

I accept the R2–R6 and A1 repairs. R1 remains incomplete for two paths that resolve to the same file. No other correction is necessary from this review.

Manifest: `docs/reviews/b234-correction-files.sha256`.

Reviewed manifest SHA-256: `846f5496b67938311d5c200b7bc4f70086c3d260eab209ccce918015e97e0bfb`.

All 36 manifest entries passed before and after review.

**Remaining R1 defect: cache keys do not identify resolved files**

Location: `contracts/validate.py`, `_Ctx.read`.

The cache key is `(resolved root, relative path)`. Two relative paths through an in-project symbolic link therefore get separate reads and separate snapshots of one file. This does not meet the agreed one-read rule for resolved files.

I reproduced a false qualified result with temporary fixtures:

1. Build a project whose board interface has no holes.
2. Make `components/part.yaml` a symbolic link to `mechanical/board-interface.json` within the project.
3. Build the package with the existing helper.
4. Omit the plated drill output with an interface-based `no_plated_holes` exception.
5. Prepare changed interface bytes that contain a plated hole.
6. Set the `parts` input and its evidence references to the changed-byte hash.
7. Keep the board-interface input and its evidence references at the original hash.
8. Change the interface bytes immediately after the first underlying read.

The validator read the same file through both paths:

```text
mechanical/board-interface.json
components/part.yaml
```

It returned exit 0 with no findings. The drill exception used the original hole list. The second path supplied a different snapshot of the same file.

The probe uses the accepted free-path input role and confined symbolic links. It does not modify a symbolic link during validation. It tests byte consistency, not future part-reference coverage.

Share successful snapshots by resolved file identity after the root-confinement test. Alternatively, reject duplicate file aliases explicitly. Do not reuse a cached success before the current path passes its own root-confinement test.

Add one regression with two confined names for one file and a controlled byte change. The run must not qualify inconsistent snapshots. Preserve the existing outside-link rejection and ordinary one-path cache test.

**Accepted repairs**

| Repair | Review result |
|---|---|
| R2 | Listed inputs and artifacts now receive comparisons for all evidence statuses. Mandatory-role checks remain specific to passed evidence. |
| R3 | Qualified SKiDL packages require a source input. Its path and exact-byte hash receive the generic input checks. Native and draft cases retain their behavior. |
| R4 | Publication refuses an existing lexical destination, including a dangling link, before path resolution. |
| R5 | Worker process failure takes priority over response text. Exit-code and signal regressions pass. |
| R6 | Both legacy documentation repairs are present. The baseline is gone. New missing references fail the package tests. |
| A1 | List, string, and integer frontmatter give `skill.frontmatter_invalid` without a crash. Ordinary mapping checks remain. |

The original one-path R1 case now fails as expected. All project/package read calls use `_Ctx.read`. The remaining issue is its cache identity.

**Commands and independent evidence**

| Command | Result |
|---|---|
| `uv run tests/test_pcb_tools.py` | 57/57 passed, exit 0 |
| `uv run tests/test_project_io.py` | 11/11 passed, exit 0 |
| `uv run tests/test_skill_packages.py` | 8/8 passed, exit 0 |
| `uv run /tmp/cad-skills-b234-evidence-probe.py` | Exit 1 with two `pkg.check_evidence_mismatch` findings |

Independent probes also confirmed dangling-link refusal, `snippet.worker_failed` for worker exit 7, and frontmatter findings for list/string/integer inputs. The same-file alias probe above gave exit 0.

I did not repeat the mechanical suites or reopen the accepted design. The correction record reports the successful full snippet run and dry run. The contract suite retains the B1 fixed-byte hash tests.

**Frozen identity after review**

`sha256sum -c docs/reviews/b234-correction-files.sha256` passed again for all 36 entries. The manifest hash remained `846f5496b67938311d5c200b7bc4f70086c3d260eab209ccce918015e97e0bfb`.

Correct the cache identity and supply the focused regression results and replacement hashes. I changed only this report. I request no commit.
