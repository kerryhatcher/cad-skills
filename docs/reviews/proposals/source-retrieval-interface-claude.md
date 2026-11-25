# Source retrieval interface (compatibility revision, not installed)

Date: 2026-11-15 UTC. Author: claude-skill-dev. Reviewers: codex-skill-dev, pi-skill-dev.
Basis: `docs/reviews/source-retrieval-compatibility-root.md`. Supersedes the revision 6 meaning of `profile_binding` and the magic tokens `pdf`, `xlsx` and `none`.

Scope: the smallest interface that retrieves the source pages named in the release-format manifest. It does not accept changed bytes, revise a profile, or add a license gate. It has no repository path in the code. Every path comes from the manifest location and the arguments.

## Manifest and roots

- Format: the release-worktree format, `schema: cad-skills/sources`, `schema_version: 1`. Fields: `id`, `path`, `url`, `retrieved`, `sha256`, `content_type`, `magic`, `license_state`, `distribution_decision`, `profile_binding`. Any other key is refused with exit 2.
- The manifest root is the parent directory of the manifest file. The command takes `--manifest FILE` and derives the root from it.
- `path` is the only destination. It is a relative path under the root. The destination is `DIR/<path>`. The `supplier/` prefix is kept.
- `profile_binding` identifies a profile. It never names a destination. Its value is `null`, or a relative path `supplier/profiles/<name>.yaml` under the root. The profile is never written. The release manifest currently holds full root-relative values (`skills/pcb-fab-package/supplier/profiles/...`). Normalizing them to `supplier/profiles/<name>.yaml` is a text change that release must coordinate.
- When `profile_binding` is not `null`:
  - `path` must start with `supplier/pages/`;
  - `path` must end in `.html`. The five bound pages in the release manifest all end in `.html`. Another suffix is refused with exit 2;
  - the file name stem of `path` must be a key of the profile `extensions.evidence_pages`;
  - the profile path is confined with `project_io.confine` under `supplier/profiles` before it is read. A link on any component, or an escape from the root, is refused with exit 2 before any fetch and before any read of the profile. The resolved absolute profile path must also stay under the resolved `supplier/profiles` directory. A path that resolves into another directory, including `supplier/pages`, is refused with exit 2 before any read or fetch;
  - the profile is read only for this check. If the manifest `sha256` is not `null` and differs from that key's `sha256` in the profile, the run stops with exit 2 before any fetch.
- `license_state` and `content_type` are informational. Neither is read for any decision. `content_type` is recorded, not checked.
- `url` must use `https`. Redirects are not followed.
- `retrieved` must be a real calendar date, checked with `datetime.date.fromisoformat`.

## Magic tokens

The allowed values are the release tokens and `null`. Each token has an exact byte rule:

| Token | Byte rule |
|---|---|
| `markup` | after optional leading whitespace, the first byte is `<` |
| `%PDF` | the first four bytes are `%PDF` |
| `PK\u0003\u0004` | the first four bytes are `0x50 0x4B 0x03 0x04` |
| `OLE2` | the first eight bytes are `0xD0 0xCF 0x11 0xE0 0xA1 0xB1 0x1A 0xE1` |
| `null` | no magic test |

Any other value, including `pdf`, `xlsx` and `none`, is refused with exit 2.

## Distribution decisions

- `exclude-full-copy`: the entry is fetched, checked and written to `DIR/<path>`. It is excluded from distribution.
- `exclude-local-evidence`: the entry is not fetched. The command does not read, fetch or verify its bytes. Its bytes are evidence captured once, kept in the review tree.

## Command

```
uv run scripts/fetch_sources.py --manifest FILE [--dest DIR] [--entry ID ...] [--check-only]
```

- `--dest` defaults to the manifest root. A write requires the resolved `--dest` to equal the resolved manifest root. Any other destination is refused with exit 2 when a write is requested.
- `--check-only` fetches and hashes entries and writes nothing. A differing `--dest` is ignored. The command reads nothing from it, and the exit follows the outcomes.

## Strict handling

- The manifest is parsed with `validate.parse_record`, which parses the mapping only. The schema, field and type checks in the next section are applied to the parsed mapping before any fetch.
- Each `DIR/<path>` is confined with `project_io.confine` against the root. A link on any component is refused before any write.
- Each write uses `project_io.atomic_write`.

## Manifest schema validation (before any fetch, exit 2)

- The top level has exactly the keys `schema`, `schema_version`, `sources`. `schema` equals `cad-skills/sources`. `schema_version` equals the integer `1`.
- `sources` is a non-empty list. Each entry is a mapping.
- Required keys for each entry: `id`, `path`, `url`, `retrieved`, `sha256`, `content_type`, `magic`, `license_state`, `distribution_decision`, `profile_binding`. `profile_binding` may be `null`.
- No other key is allowed.
- Types: `id`, `path`, `url`, `retrieved`, `content_type`, `magic`, `license_state`, `distribution_decision` are strings, except `magic` which is one of the allowed tokens or `null`. `sha256` is 64 lowercase hexadecimal characters, or `null`. `profile_binding` is a string or `null`.
- `retrieved` is a real calendar date in the form `YYYY-MM-DD`.
- The check runs over all entries first. The first defect stops the run with exit 2, and nothing is fetched or written.

## Hash rule

One HTTP GET per entry, a generic client name, a 30 second timeout, and no credentials. The SHA-256 of the response bytes is compared with the manifest `sha256`. A non-2xx response, a redirect, a network error or a timeout is a fetch failure.

## Validation before any fetch (exit 2)

All of the following are checked before the first fetch. A failure stops the run. Nothing is fetched or written.

- An unknown `--entry ID`.
- An empty manifest.
- A duplicate `id`, or a duplicate resolved destination. Two entries are duplicates when their `DIR/<path>` resolve to the same absolute path.
- An absolute `path`, a `path` with a `..` segment, or a `path` that resolves outside the root.
- A link on any component of `DIR/<path>`.
- A `profile_binding` that is not `null`, not under `supplier/profiles/`, or contains `..`.
- A non-null `profile_binding` whose `path` does not start with `supplier/pages/`, does not end in `.html`, whose stem is not a key of the profile `evidence_pages`, or whose manifest `sha256` differs from the profile value.
- A `profile_binding` path that fails confinement (a link on any component, or an escape from the root), or whose resolved absolute path is not under the resolved `supplier/profiles` directory. The profile is not read in that case.
- A `url` scheme other than `https`.
- A `--dest` whose resolved path differs from the resolved manifest root when a write is requested.
- An unknown `magic` token, or an unknown `distribution_decision`.
- A schema, field or type defect from the schema section.

## Entry outcomes (after validation)

Each fetched entry has two statuses, and the command reports both:

- hash status: `match`, `candidate` (the manifest `sha256` is `null`), or `changed`;
- magic status: `ok`, `mismatch`, or `not-tested` (the manifest `magic` is `null`).

The magic check runs on every fetched entry, including candidate and changed entries. An entry writes only when the hash status is `match` and the magic status is `ok` or `not-tested`.

| Outcome | Condition | Written | Exit contribution |
|---|---|---|---|
| match | hash status `match`, magic status `ok` or `not-tested` | yes, if a write was requested | 0 |
| skipped | `exclude-local-evidence` | no | 0. Not fetched and not verified. Never reported as match |
| candidate | hash status `candidate` | no | 1 |
| changed | hash status `changed` | no | 1 |
| magic mismatch | magic status `mismatch` | no | 1 |
| fetch failure | network error, timeout, redirect, or non-2xx | no | 3 |
| write failure before replace | `atomic_write` raises before the replace | no; the old bytes stay | 3 |
| write failure after replace | the replace is done and a later durability step fails | yes, new bytes in place; reported as write error | 3. No rollback is claimed |

The exit contribution of a fetched entry is 1 when the hash status is `candidate` or `changed`, or when the magic status is `mismatch`. A magic status of `ok` or `not-tested` contributes nothing. The command reports both statuses for every fetched entry, whatever the exit.

## Overall exit precedence

The overall exit is the first rule that applies:

1. Validation failed: 2.
2. Any entry had a fetch failure or a write failure, before or after the replace: 3.
3. Any entry had a candidate, changed, or magic mismatch: 1.
4. Otherwise: 0.

A run with one fetch failure and one changed entry exits 3. A skipped entry never changes the exit.

## Overall result

The overall result is one of these states. This is the only place where they are defined:

- all match: every fetched entry matched, and nothing was skipped in error;
- partial: some entries were written and at least one was not;
- none written: no entry was written;
- no entry fetched: every selected entry was skipped (exit 0);
- write error: a post-replace failure. The result names the entries that changed on disk.

`--check-only` has the same overall result as a write run, with the write removed. No file is written. A match is a match. A candidate or a changed entry gives exit 1.

The result lists each entry with its two statuses and its outcome. Skipped entries are listed by id, marked "not fetched, not verified".

## Unset hashes

Entries with `sha256: null` are review candidates. The command prints their hashes for source review. It writes nothing for them. They become accepted entries only after a recorded source review fills the manifest `sha256` field. The command never fills that field.

## What the command never does

- It never edits `sources.yaml`, a profile, or any file that a changed outcome would replace.
- It never accepts changed bytes. A changed page needs a recorded source review, a new profile binding written by hand, and a new `retrieved` date.
- It does not decide reuse rights, and it does not add a license gate.

## Offline tests

The test file is `tests/test_source_retrieval.py`. The fetch function is injected. The fixture bytes are project-authored. There is no network call.

1. A match writes the file at `DIR/<path>` and exits 0.
2. `--check-only` with a match writes nothing and exits 0.
3. A changed hash writes nothing, reports changed, exits 1, and leaves the manifest and profile bytes unchanged.
4. A candidate hash reports candidate, writes nothing, and exits 1.
5. A fetch failure exits 3 and writes nothing.
6. A magic mismatch exits 1 and writes nothing.
7. A link at the destination file is refused with exit 2, and the target keeps its bytes.
8. A link at a parent directory of `DIR/<path>` is refused with exit 2, and nothing is written outside the root.
9. A `path` that is absolute, or has a `..` segment, is refused with exit 2 before any fetch.
10. A duplicate resolved destination under two entries is refused with exit 2 before any fetch.
11. An unknown `--entry ID` is refused with exit 2 before any fetch.
12. An empty manifest is refused with exit 2 before any fetch.
13. A `profile_binding` outside `supplier/profiles/`, or containing `..`, is refused with exit 2.
14. A `--dest` that differs from the manifest root is refused with exit 2 for a write.
15. An `exclude-local-evidence` entry is reported as skipped, exits 0 when the other entries match, and is never reported as match.
16. A mixed run with one fetch failure and one changed entry exits 3 and reports both outcomes.
17. A multi-entry run with one changed entry reports partial, names the written entries, and exits 1.
18. A duplicate `id`, or a magic token `pdf`, `xlsx` or `none`, exits 2 before any fetch.
19. A match with a changed `license_state` still writes the file and exits 0.
20. An `exclude-full-copy` entry that matches is written to `DIR/<path>` and exits 0.
21. An `exclude-full-copy` entry with a candidate hash is not written and exits 1.
22. A valid `profile_binding` (`supplier/profiles/oshpark-two-layer.yaml`) with `path` `supplier/pages/two-layer.html` matches, is written to `DIR/<path>`, and exits 0. The profile file bytes are unchanged.
23. `--check-only` with a candidate writes nothing and exits 1.
24. An `http` URL is refused with exit 2 before any fetch.
25. A 3xx response is a fetch failure (exit 3) and nothing is written.
26. A wrong `schema` or `schema_version` exits 2 before any fetch.
27. A missing required key, or an unknown key, exits 2 before any fetch.
28. An invalid type (for example a `sha256` that is not 64 hexadecimal characters, or a `retrieved` that is not a real date) exits 2 before any fetch.
29. A pre-replace write failure keeps the old destination bytes, leaves no temporary file, and exits 3.
30. A match on one entry and a fetch failure on another writes the matched entry, reports both outcomes, and exits 3 (partial).
31. A run where every entry is skipped exits 0 and reports "no entry fetched".
32. A non-2xx response (404 or 500) is a fetch failure, exits 3, and writes nothing.
33. A post-replace durability failure is reported as write error with exit 3. The new bytes stay in place, and the result states that no rollback was done.
34. An entry with `magic: null` is written when the hash matches, with magic status `not-tested`.
35. `--check-only` with a `--dest` that differs from the manifest root reads nothing from that destination, writes nothing, and exits by the outcomes.
36. A `retrieved` value such as `2026-02-30` exits 2.
37. A `profile_binding` that contains `..` is refused with exit 2.
38. A non-null `profile_binding` whose `path` is not under `supplier/pages/` exits 2 before any fetch.
39. A non-null `profile_binding` whose manifest `sha256` differs from the profile `evidence_pages` value exits 2 before any fetch.
40. An entry with a changed hash and an invalid magic reports both statuses (changed and mismatch), writes nothing, and exits 1.
41. An entry with a candidate hash and an invalid magic reports both statuses (candidate and mismatch), writes nothing, and exits 1.
42. A magic token `OLE2` matches an OLE compound-file header and is written with magic status `ok`.
43. A `profile_binding` whose profile path is not `supplier/profiles/<name>.yaml` exits 2.
44. The five release-manifest entries that name a profile (single-layer, two-layer, two-layer-hhdc, four-layer, six-layer) pass the validation tests offline, after the path normalization that release coordinates. Each one resolves its page key in the profile `evidence_pages`.
45. A `profile_binding` whose profile path is a symbolic link to a file outside the root is refused with exit 2 before any fetch. The outside file is neither read nor written, and the test checks that its bytes are unchanged.
46. A non-null `profile_binding` whose `path` ends in a suffix other than `.html` (for example `supplier/pages/two-layer.pdf`) is refused with exit 2 before any fetch.
47. A `profile_binding` whose profile path is a link (or sits under a directory link) that resolves into `supplier/pages` is refused with exit 2 before any read of the profile and before any fetch. The page file keeps its bytes, and the test checks that the profile was not read.

## Ownership

- Fabrication: `scripts/fetch_sources.py` and `tests/test_source_retrieval.py`.
- Release: the normalization of the five `profile_binding` values, and the provenance and distribution checks.
- Lead: the decision to record a hash after a source review.
