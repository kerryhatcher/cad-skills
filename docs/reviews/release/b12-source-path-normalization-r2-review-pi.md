# Source-path normalization r2 review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-source-path-normalization-freeze-r2-claude.sha256`. This
report writes no product file. It does not commit. It made no provider call.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-source-path-normalization-freeze-r2-claude.sha256` has
SHA-256 `407e030d809852f9a5a3d4b1d1a98d977431cb4d008464e0b1c8b38bfceaeb32`. It matches the
author message.

| Item | Before | After |
|---|---|---|
| Entries | 4 | 4 |
| `sha256sum -c` | 4 of 4 OK | 4 of 4 OK |
| Freeze file hash | `407e030d...` | `407e030d...` |

Supersedes `eaa19fa9...`. The manifest is unchanged at
`fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`. The A1 and A2 freeze r2
still matches 155 of 155.

## 2. Test reproduced

`uv run tests/test_release_packaging.py` gives 32 of 32 passed, exit 0.

## 3. N-4 addressed

`confined_profile` now:

1. Refuses an absolute binding, a `..` part, or an empty binding.
2. Checks every prefix of the absolute manifest directory path for a symbolic link.
3. Builds the candidate under the manifest directory.
4. Checks every prefix of the candidate path for a symbolic link.
5. Refuses a candidate whose resolved path is not under the resolved manifest directory.
6. Reads no file before it returns a path.

D-9 is preserved and its text is updated. The new tests
`test_fixture_symlinked_manifest_directory_is_refused` and
`test_repository_manifest_relative_bindings_resolve_under_their_directory` pass. The first
covers a symlinked manifest directory and a linked parent. The second confirms the five
bindings resolve under the manifest directory and exist.

The STE corrections are applied: the D-9 module text, the D-9 test docstring, and the record.

## 4. Host limit

A host whose manifest directory has a symlinked ancestor reports D-9 for every binding.
`_has_link_component` checks the full absolute path from `/`. Examples: `/tmp` on macOS is a
link to `/private/tmp`, and some checkouts use a linked ancestor.

This is a documented limit. The lead recorded it.

Recommendation: in CI and in the fabrication handoff, use a checkout path with no symlinked
ancestor. If a portable rule is necessary later, check only the components below a trusted
root or compare resolved paths without refusing an ancestor link. No change is necessary for
this batch.

## 5. Low observations

### o2 The new test name mentions the repository manifest

`test_repository_manifest_relative_bindings_resolve_under_their_directory` loads the skill
manifest `skills/pcb-fab-package/sources.yaml`. The repository manifest
`tests/eval/distribution.yaml` has no `profile_binding`, so a repository-level binding is
still unexercised. The name is slightly broad. No change is necessary.

## 6. Verdict

N-4 passes. The checker refuses a symlink in the manifest directory path and in the binding
path, and it compares the resolved candidate with the resolved manifest directory before a
read. D-9 is preserved. The manifest and the A1/A2 files are unchanged. Packaging passes 32
of 32.

I recommend acceptance. After acceptance, the normalized manifest and its SHA-256
`fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f` can go to the
fabrication team. Provider authorization stays zero.

I made no edit during this review.

## Limits

This review ran the focused packaging suite and read the frozen bytes. It made no provider
call and no CAD call. It changed no product file.
