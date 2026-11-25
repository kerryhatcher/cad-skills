# Source retrieval implementation freeze review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the frozen retrieval implementation
`docs/reviews/source-retrieval-implementation-freeze-claude.md`,
SHA-256 `386106caae33fc9347d6e6cbafe07392aa50763992d6d41f9067d5c4a89448c8`.
I examined the same hashes as the codex review. I changed no product file. I ran no broad
suite. I ran the frozen offline test file.

## Hash boundary

The freeze record hash matches the request. All ten entries in
`docs/reviews/source-retrieval-implementation-files.sha256` pass. `sha256sum -c` exit 0.

| File | SHA-256 |
|---|---|
| `skills/pcb-fab-package/scripts/fetch_sources.py` | `33397ab92b085d28d95b873e78011b9e7d03746105f5a9ee801023fcfd7e0dc3` |
| `tests/test_source_retrieval.py` | `58e33eb71bd0ce6d0faa213a42f7bfe9258e1f3efb95114c6a51254dd590c285` |
| `skills/pcb-fab-package/SKILL.md` | `bb3f5ab2db4cd791ffe6055945c35e2f0c61445958ca9e0016a4d0aa57c5c0bc` |
| the five profile files | as recorded |

Logs: `test_source_retrieval-run2.log` ends with `48/48 passed`.
`test_skill_packages-retrieval.log` ends with `8/8 passed`.

I ran `uv run --quiet tests/test_source_retrieval.py`. Result: `48/48 passed`, exit 0. The
test file is offline and uses an injected fetch function. The redirect and 404 cases use a
server on `127.0.0.1`.

## Code review

The implementation meets the released corrections:

- **Explicit link check.** `refuse_links` calls `os.path.islink` on every component of the
  relative path, for both the destination and the profile binding, before any read or write.
  It raises `Refused`, which maps to exit 2.
- **Profile confinement.** `check_binding` resolves the profile path and requires
  `resolved.is_relative_to(resolved supplier/profiles)`. A profile that resolves into
  `supplier/pages` is refused. Tests 47 and 48 cover this.
- **Read after the checks.** The profile is read only after `refuse_links` and the
  resolved-path check. Tests 45, 47 and 48 assert the target bytes are unchanged and no fetch
  occurred.
- **Manifest meaning.** `profile_binding` names a profile under `supplier/profiles`. `path`
  is the only destination. The bound page must be under `supplier/pages/` and end in `.html`.
- **Page key and hash.** The `path` stem must be a key of the profile
  `extensions.evidence_pages`. A non-null manifest `sha256` must equal the profile value.
- **Magic tokens.** `markup`, `%PDF`, `PK\u0003\u0004`, `OLE2` and `null`. The fourth token is
  the literal string with a backslash. The code compares it and checks the bytes
  `PK\x03\x04`. `pdf`, `xlsx` and `none` are refused.
- **Exit precedence.** Validation 2, then a fetch or write failure 3, then candidate, changed
  or magic mismatch 1, then 0.
- **Post-replace outcome.** `PostReplaceError` gives `write-error-after-replace`, the new
  bytes stay, and no rollback is claimed. Test 33 covers it.
- **No side effects.** The command never edits the manifest or a profile. The pre-replace
  failure keeps the old bytes and leaves no temporary file.

The allocation of the open normalization dependency to release is correct. The release
manifest still holds full repository-relative profile paths. The command refuses it with exit
2 until release normalizes the five values. The freeze record states this dependency.

## Minor findings

- The `%PDF` and `PK\u0003\u0004` tokens have no dedicated positive test. Add one for each.
  The `PK\u0003\u0004` test should pin the YAML storage form.
- The `stem not in evidence_pages` branch in `check_binding` has no dedicated test. Test 39
  covers a hash difference, not a missing page key. Add a missing-key test.
- The destination path has no in-root link test. Tests 7 and 8 use outside targets. The code
  refuses any link, so add an in-root destination link test to pin it.
- `refuse_links` starts at the root and checks the components below it. It does not check the
  manifest parent itself. A symlinked manifest parent is followed. This is the user-chosen
  root, so it is a small risk. State whether the root is trusted, or add a root check.

## Supersession

The freeze record says the `SKILL.md` entry in the documentation freeze 2 is superseded by
this record. The current `SKILL.md` hash is `bb3f5ab2…`, which differs from the freeze 2 value
`f1d6fb86…`. The retrieval command row and the file entry are present. I accept the
supersession.

## Verdict

The retrieval implementation freeze is accepted. The code meets the released link and
confinement corrections. The 48 offline tests pass. The four minor findings above do not
block the freeze. The normalization of the release manifest is a separate release dependency.

No product edit. No broad suite.