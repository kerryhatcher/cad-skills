# Source retrieval proposal review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the retrieval interface, twelve tests, and exit rules. It does not approve implementation.

## Findings

### Blocker: the stated manifest format does not match the current manifest

The proposal says it uses the existing skill-level manifest format. It lists `schema`, `schema_version`, and fields such as `path`, `profile_binding`, and `distribution_decision`.

The current draft at `docs/reviews/proposals/sources.yaml` uses `schema_id: cad-skills/supplier-sources`, `schema_version: "1.0"`, and a `sources` list. Its entries do not have `path`, `profile_binding`, `distribution_decision`, or `magic`.

Define the accepted manifest format and its schema before implementation. Add an offline test that parses the current manifest shape or update the manifest proposal and identify the new schema. The generic `validate.parse_record` function only parses a mapping. It does not enforce required fields, field types, or unknown-field rules.

### Blocker: exit rules conflict for mixed outcomes

The rules assign exit 1 to any partial result. They assign exit 3 when a fetch fails and no refusal applies. A run with one successful write and one fetch failure meets both rules. A run with one changed page and one fetch failure also meets both rules.

Define one precedence order. For example: exit 2 for refusal or invalid input, exit 1 for any non-match outcome, exit 3 only when fetch failure is the only non-match outcome, and exit 0 only when every selected entry matches. Add mixed-result tests for these cases.

The exit 0 rule also says “every write request succeeded,” but candidate and skipped entries do not write. State exact results for `--check-only`, skipped entries, and an empty selection. Test these cases. A skipped entry must never contribute to an all-match result.

### Gap: the twelve tests do not prove write failure safety

Test 6 covers a symbolic link at the target. It does not test a failure before atomic replace with an existing regular file. Add a test that injects a pre-replace failure and confirms that the old bytes remain and that no temporary file remains.

Test 10 covers a changed entry after one write. Add mixed partial cases for fetch failure and path refusal. Confirm the per-entry list, overall result, written paths, and exit code in each case.

## Confirmed design points

The proposal keeps the full manifest path under `DIR`, requires the write destination to equal the manifest root, confines paths, uses atomic writes, treats null hashes as candidates, and never treats skipped entries as matches. It does not write changed bytes or update the manifest. These rules support the intended limits when the manifest schema and exit precedence are explicit.

## Review result

Resolve the manifest schema and mixed-outcome exit rules before implementation. Add the focused tests above. No code or tests were changed or run for this review.
