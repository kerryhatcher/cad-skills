# Source text hash freeze (pi)

Date: 2026-11-26 UTC. Released by the lead decision of 2026-11-26 (issue #9, "Controller decisions on the open questions"). This freeze replaces `source-retrieval-alias-freeze-claude.md` for `skills/pcb-fab-package/scripts/fetch_sources.py` (hash `35e21d37dc82e8367a167411b887843f426e0a2f5d1b4708cfe4f5dfad63ab01`). That earlier freeze stays as history.

## Changed files

| Path | SHA-256 |
|---|---|
| `skills/pcb-fab-package/scripts/fetch_sources.py` | `01e6ae945cb67ae0daa38bfc8ab43466ae8c68c03458d341fc6a7ee6f5d8708e` |
| `skills/pcb-fab-package/scripts/recheck_sources.py` | `6ef5ddbb36350b3cac8cdd252a1efd38584b6c2f8ff1fe2909c17a30ad6a3712` |
| `tests/test_source_retrieval.py` | `86b3005d3963b06cac94a5af1f64073789a2aeabf097752afb028aa306c6b68c` |
| `tests/test_recheck_sources.py` | `e2c90b1d7f40e885b2052744975fcaf456135229ea00a05307090aa4f66387d4` |
| `tests/fab_fixture.py` | `58162631b319c76d45b465548eb1c36adf7617c2e2d1d15d7ab1cab85354c69a` |

Manifest: `docs/reviews/source-text-hash-files.sha256`.

No supplier profile, `sources.yaml` entry or source byte changed.

## Behavior

A manifest entry can have the optional key `text_sha256`, the SHA-256 of the visible page text. Validation rules:

1. The value must be 64 lowercase hexadecimal characters (a null value is refused).
2. An entry with `text_sha256` must have the magic token `markup` and a non-null `sha256`.

The visible text rule: replace each tag with one space. Replace each `script`, `style` and `noscript` element, and each comment, with one space. The text in `title` and `head` stays. Decode HTML entities. Collapse each run of whitespace to one space. Remove the whitespace at the two ends. Decode the page bytes as strict UTF-8; if the decode fails, the entry has no text hash.

Outcome rules (`fetch_sources.py`):

- Bytes match, no `text_sha256`: status `match`, write, exit 0. Text status `null`.
- Bytes match, text hash matches: status `match`, text status `match`, write, exit 0.
- Bytes match, text hash differs or the text is not UTF-8: status `match`, text status `changed`, write (the byte hash is the binding evidence), exit 1. The re-check gives the status `text-mismatch`.
- Bytes differ, text hash matches: status `layout`, text status `match`, no write, exit 0.
- Bytes differ, no or a non-matching text hash: status `changed`, exit 1, no write.
- A magic mismatch on a `layout` row gives exit 1 and no write. Exit precedence 2, then 3, then 1, then 0 did not change.
- `fetch_sources.py` reports `observed_text_sha256` for each fetched `markup` entry, also when the entry has no `text_sha256`.

`recheck_sources.py` adds the `Text` column, the `layout` and `text-mismatch` statuses, the `recorded_text_sha256`, `observed_text_sha256` and `text_status` keys, and the layout and text-mismatch action texts. The report `schema_version` stays 1. There is no automatic write for a `layout` result; a person re-binds the byte hash at the next source review.

`tests/fab_fixture.py` removes `text_sha256` from each entry it copies, because the fixture bytes are project-authored.

## Tests

- Tests 57 to 70 in `tests/test_source_retrieval.py` and tests 28 to 35 in `tests/test_recheck_sources.py` are new. Tests 60, 61 and 62 prove the new key checks. Tests 35 and 70 prove the new report keys. Only test 71 is a guard test, and it also passes on the base scripts (commit `e3bdbca`).
- Test counts before (base `2823b6c`): `test_source_retrieval.py` 56/56, `test_recheck_sources.py` 28/28, `test_release_packaging.py` 37/37.
- Test counts after: `test_source_retrieval.py` 71/71, `test_recheck_sources.py` 36/36, `test_release_packaging.py` 37/37, `test_snippets.py` 52/52 blocks, `test_skill_packages.py` 8/8, `test_print_tools.py` 6/6, `test_pcb_tools.py` 60/60, `test_project_io.py` 11/11, `test_release_harness.py` 65/65, `test_release_isolation.py` 29/29, `test_artifact_expectations.py` 35/35, `test_pcb_fab_standalone.py` exit 0, `test_pcb_fab_jlcpcb.py` 19/19, `test_pcb_fab_pcbway.py` 24/24.
- Known expected failure: `test_artifact_fixtures.py` 15/16. `test_a2_source_manifest_matches_the_repository_sources` fails for `fetch_sources.py` because the retained A2 evidence names the old hashes. Per the lead decision of 2026-11-26, the retained A2 files are not edited. The integrator re-accepts the hash lines after the merge.

## Review request

Examine `fetch_sources.py` and `recheck_sources.py` at the hashes above, the new tests, and the visible text rule. Confirm the replacement of the alias freeze for `fetch_sources.py`.
