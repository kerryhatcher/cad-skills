# B12 source-path normalization: compatibility record

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Type: compatibility change record. Authority: `b12-bom-acceptance-normalization-root.md` (lead, 2026-11-15 03:32 UTC) and the N-4 release (lead, 2026-11-15 03:40 UTC).

## Change

1. The five `profile_binding` values in `skills/pcb-fab-package/sources.yaml` read `supplier/profiles/<name>.yaml`. The name of each profile does not change.
2. `tests/eval/packaging.py` resolves each binding under its manifest directory. The checker does not use the repository root for a skill binding.
3. The function `confined_profile` refuses a binding that is absolute, that contains `..`, or that passes through a symbolic link. It also refuses a manifest directory whose full path contains a symbolic link. It compares the resolved candidate with the resolved manifest directory. It reads no file for a refused binding. It reports the code D-9.
4. The repository manifest paths keep their meaning. The repository root is their manifest directory.

## N-4 (second pass)

Review N-4 (`b12-source-path-normalization-review-codex.md`) found two gaps in the first version. It did not inspect the manifest directory path for symbolic links. It did not compare the resolved candidate with the resolved manifest directory. The second pass closes both gaps. It also adds two tests: one for a symbolic link in the manifest directory path, and one for the five repository bindings. It rewrites the new text in active voice.

## Preserved

- Every source hash, retrieval date and page path in `sources.yaml` is unchanged. Only the five binding strings changed in the first pass.
- Every profile file is unchanged. The profile content hash binding is unchanged.
- No A1 or A2 file changed.

## Tests

- `test_fixture_profile_binding_must_agree`: the binding is relative to the skill directory. A profile with a different evidence hash reports D-5.
- `test_fixture_skill_outside_repo_resolves_its_relative_binding`: a skill manifest outside the repository resolves its relative profile. The checker root holds no profile. No finding is reported.
- `test_fixture_profile_link_and_escape_are_refused`: a symbolic link binding reports D-9. A binding with `..` reports D-9.
- `test_fixture_symlinked_manifest_directory_is_refused`: a symbolic link to the manifest directory reports D-9. A manifest directory under a linked parent reports D-9.
- `test_repository_manifest_relative_bindings_resolve_under_their_directory`: the five repository bindings resolve under the skill directory and exist.

Results: `tests/test_release_packaging.py` passes 32 of 32.

## Limits

- A host whose ancestor directories are symbolic links reports D-9 for each skill binding. This repository has no such ancestor.
- No fetch script exists. The retrieval script has no path to align yet.
- The change adds no supplier byte to the repository.
