# Source retrieval compatibility decision

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The retrieval proposal must use the release manifest format. The existing manifest is
`/mnt/storage/projects/cad-skills-worktrees/release/skills/pcb-fab-package/sources.yaml`.

1. `path` names the destination under the manifest directory. It is the only write destination.
2. `profile_binding` identifies a profile. It does not name a page destination. Do not change its meaning to a page path.
3. Normalize the five profile paths to `supplier/profiles/<name>.yaml` in the integrated manifest. Coordinate this text change with release.
4. A bound page path stays under `supplier/pages/`. Its profile path stays under `supplier/profiles/`.
5. Confine both paths. Read the profile only when necessary to examine its declared page path and hash. Never write the profile.
6. Use the existing magic tokens: `markup`, `%PDF`, `PK\u0003\u0004`, and null. The release addition is `OLE2`.
7. Null means no magic test. Do not substitute the strings `pdf`, `xlsx`, or `none` in this schema version.
8. `exclude-full-copy` permits local retrieval. It excludes the bytes from distribution. `exclude-local-evidence` skips retrieval.
9. Apply the agreed exit precedence: validation 2, fetch or write failure 3, changed or candidate or magic mismatch 1, then 0.
10. Keep the explicit post-replace outcome. New bytes can remain after a synchronization failure.

Use the five existing profile entries in an offline compatibility test. Use project-authored response bytes in network tests.
Examine the profile page-path representation before implementation. Resolve any concrete mismatch once with both reviewers.
Do not add a new approval record or change a supplier profile.
