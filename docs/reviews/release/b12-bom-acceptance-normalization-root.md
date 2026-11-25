# BOM acceptance and source-path normalization

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers accept the BOM correction and its final text.
The lead accepts freeze r3 at `ff67bca674b75a01ff66428c6465677cdc07733d8e57cb9ce099f5483112520c`.
The historical proposal stays unchanged. Provider authorization remains zero.

Release the following separate compatibility change:

1. Normalize the five `profile_binding` values in the skill source manifest to `supplier/profiles/<name>.yaml`.
2. Resolve each binding relative to its manifest directory in the packaging checker.
3. Keep repository-manifest paths relative to that manifest directory, which is the repository root.
4. Confine the resolved profile path before a read. Refuse an escape or a symbolic link.
5. Preserve all source hashes, dates, page paths and profile contents.
6. Add an offline test with a skill manifest outside the repository. Its relative profile must resolve without the repository path.
7. Add a profile-link refusal test. Retain the existing packaging results.

This change gives the retrieval script and the distribution checker the same path meaning.
Do not change the A1/A2 frozen files. Freeze the compatibility files separately for both reviewers.
After acceptance, send the normalized manifest and its hash to the fabrication team.
