# BOM source-path normalization plan from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review plan for `docs/reviews/release/b12-bom-acceptance-normalization-root.md`. This
report writes no product file. It does not commit. It made no provider call.

## 1. Current state

| Item | Value |
|---|---|
| `profile_binding` values | `skills/pcb-fab-package/supplier/profiles/<name>.yaml` (repository-relative) |
| Checker resolution | `profile = root / binding` (repository root) |
| Five bound entries | single-layer, two-layer, two-layer-hhdc, four-layer, six-layer |
| Five header entries | `profile_binding: null` |

The current values work only because the repository root is the base. A skill manifest used
outside the repository would not resolve.

## 2. Acceptance criteria for the compatibility freeze

| ID | Criterion |
|---|---|
| N-1 | The five `profile_binding` values are `supplier/profiles/<name>.yaml` (manifest-relative). The header entries stay `null` |
| N-2 | The checker resolves each binding as `manifest_dir / binding` |
| N-3 | A repository-manifest binding resolves relative to `ROOT`, because that manifest directory is the repository root |
| N-4 | The resolved profile path is confined to the manifest directory before a read. An escape or a symbolic link is a finding |
| N-5 | All source hashes, dates, page paths, and profile contents are unchanged |
| N-6 | An offline test uses a skill manifest outside the repository. Its relative profile resolves without the repository path |
| N-7 | A profile-link refusal test. A symbolic link is refused |
| N-8 | The existing packaging results hold. The focused packaging suite still passes |
| N-9 | A1 and A2 are untouched. The compatibility files freeze separately |

## 3. Checks I will run

1. Verify the freeze file hash and every entry before and after.
2. Reproduce `uv run tests/test_release_packaging.py`.
3. Confirm the normalized manifest values and the unchanged hashes.
4. Confirm the resolution, the confinement, and the symlink refusal.
5. Confirm the offline outside-repository test and the link refusal test.
6. Confirm no A1 or A2 file changed.

## 4. Notes for the author

- The confinement base is the manifest directory. A repository-manifest binding that
  resolves outside the repository is also a finding.
- Refuse a symbolic link in the resolved path, not only the final component. Use a real
  path comparison against the confinement root.
- Keep the D-5 code for a missing or mismatched profile. Add a distinct code if a new
  refusal reason is necessary.
- Preserve the existing `profile_binding: null` entries.

## 5. Limits

This plan reads the current manifest and checker. It made no provider call. It changed no
product file.
