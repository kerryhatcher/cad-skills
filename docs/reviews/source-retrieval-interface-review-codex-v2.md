# Source retrieval proposal review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the revised interface and its nineteen tests. It does not approve implementation.

Proposal hash: `183f1139c04b28b93681c2966aecfc52730f5d02fdfde618b60cbbf51b7b56a0`.

## Findings

### Blocker: the named parser does not validate the manifest schema

The proposal says `validate.parse_record` rejects missing fields, unknown fields, and malformed values. In this worktree, that function parses YAML or JSON and returns a mapping. It does not validate a manifest schema or field types.

Use a schema validator after parsing. Add tests for the wrong schema name, wrong schema version, missing fields, unknown fields, and invalid field types. Test each failure before any fetch. Keep the existing duplicate-id and unknown-magic tests.

The proposal names the release worktree format, which differs from the draft manifest in this worktree. Record the exact schema path or schema identifier that the implementation validates. Do not rely on generic parsing as schema validation.

### Gap: skipped entries and result labels remain unclear

A skipped entry exits 0 and never counts as a match. A run with one match and one skipped entry writes some entries but not all. The multi-entry rule therefore calls the run `partial`, while the exit rule calls it successful. The text also says that `partial` does not claim the set is complete, though the skip follows the manifest policy.

Define whether the overall result describes fetchable entries or all selected entries. Report skipped entries separately. Add assertions for the overall result with a skipped entry and with `--check-only`.

### Gap: atomic-write failure lacks a test

The proposal states that a failure before replace keeps the old bytes. No test injects this failure. Add a test with an existing regular destination file. Cause a failure before replace, then confirm that the old bytes remain and no temporary file remains.

### Gap: the fetch-failure test does not cover a partial write

Test 16 pins exit 3 when one entry fails to fetch and another has changed bytes. It does not test a run that writes a matching entry, then gets a fetch failure. Add this case. Confirm exit 3, the partial result, and the written and unwritten entry lists.

## Exit rules and tests reviewed

The revised precedence is clear for validation failures, fetch failures, changed bytes, candidates, and magic mismatches. Test 16 pins fetch-failure precedence over a changed result. The proposal also adds pre-fetch checks for duplicate paths, unsafe paths, unknown entry IDs, and empty manifests.

The nineteen tests cover the main outcomes and path refusal cases. Add the focused cases above before implementation. No code or tests were changed or run for this review.
