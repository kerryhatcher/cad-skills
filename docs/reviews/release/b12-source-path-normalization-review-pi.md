# Source-path normalization review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-source-path-normalization-freeze-claude.sha256` against
the release `docs/reviews/release/b12-bom-acceptance-normalization-root.md`. This report
writes no product file. It does not commit. It made no provider call.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-source-path-normalization-freeze-claude.sha256` has
SHA-256 `eaa19fa93d228c3a3378a9ac016bf8f89d018de9c4e482e02d36afd8829f4a50`. It matches the
author message and the lead message.

| Item | Before | After |
|---|---|---|
| Entries | 4 | 4 |
| `sha256sum -c` | 4 of 4 OK | 4 of 4 OK |
| Freeze file hash | `eaa19fa9...` | `eaa19fa9...` |

The normalized manifest `skills/pcb-fab-package/sources.yaml` has SHA-256
`fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`. It matches the author
message.

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_release_packaging.py` | 30 of 30 passed, exit 0 |
| `uv run tests/test_release_packaging.py real` | 9 of 9 passed, exit 0 |
| `sha256sum -c docs/reviews/artifact-a1-a2-freeze-r2-claude.sha256` | 155 of 155 OK |

No A1 or A2 file changed.

## 3. Criterion check

| ID | Criterion | Result |
|---|---|---|
| N-1 | Five bindings are `supplier/profiles/<name>.yaml`. Headers stay `null` | Pass |
| N-2 | The checker resolves `manifest_dir / binding` through `confined_profile` | Pass |
| N-3 | A repository-manifest binding resolves relative to `ROOT` | Pass by construction. No repository binding exists to exercise it. See o2 |
| N-4 | The resolved path is confined before a read. An escape or a symbolic link is refused | Pass. `confined_profile` refuses an absolute path, `..`, an empty path, and a symbolic-link component. It returns None, and the checker reports D-9 before the read |
| N-5 | Hashes, dates, page paths, and profile contents are unchanged | Pass. The non-binding fields match the earlier records. The real manifest test passes |
| N-6 | An offline test with a skill manifest outside the repository resolves its relative profile | Pass. `test_fixture_skill_outside_repo_resolves_its_relative_binding` |
| N-7 | A profile-link refusal test | Pass. `test_fixture_profile_link_and_escape_are_refused` covers a symlink and a `..` path |
| N-8 | The existing packaging results hold | Pass. 30 of 30 and the real subset 9 of 9 |
| N-9 | A1 and A2 are untouched. Separate freeze | Pass. The A1/A2 freeze r2 still matches 155 of 155 |

The new D-9 code names the refusal. The D-5 code still covers a missing or mismatched
profile.

## 4. Low observations

### o1 The manifest directory is not checked for a symbolic link

`confined_profile` checks each component of the binding. It does not check the manifest
directory itself. The manifest directory comes from the code, not the manifest, so it is
trusted input. A hostile manifest directory is out of scope. No change is necessary.

### o2 The repository manifest has no profile binding

The repository manifest `tests/eval/distribution.yaml` has no `profile_binding` field.
Thus the resolver treats `manifest_dir = ROOT` correctly by construction, but no test
exercises a repository-level binding. Consider a fixture if a later batch adds one. Low.

### o3 The confinement does not resolve the path

`confined_profile` uses `is_symlink()` on each component. It does not call `resolve()`. A
change between the check and the read is possible, but the checker reads immediately after.
The current form is acceptable for a local check. Low.

## 5. Verdict

N-1 to N-9 pass. The bindings are normalized. The resolver is relative to the manifest
directory. The confinement refuses an escape and a symbolic link before any read. The
hashes, dates, paths and profile contents are unchanged. A1 and A2 are untouched.

I recommend acceptance. After acceptance, the normalized manifest and its SHA-256
`fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f` can go to the
fabrication team.

Provider authorization stays zero.

I made no edit during this review.

## Limits

This review ran the focused packaging suite and read the frozen bytes. It made no provider
call and no CAD call. It changed no product file.
