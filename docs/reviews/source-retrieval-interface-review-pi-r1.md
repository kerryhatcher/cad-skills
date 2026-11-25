# Source retrieval interface review, revision 1 (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the revised proposal
`docs/reviews/proposals/source-retrieval-interface-claude.md`
(SHA-256 `183f1139c04b28b93681c2966aecfc52730f5d02fdfde618b60cbbf51b7b56a0`) and the rebuilt
manifest `docs/reviews/proposals/sources.yaml`
(SHA-256 `d179915dfe91152adb19d33ced9ffd339e1a57849d68486a0b59985e13ff8dcb`).
I changed no product file. I ran no broad suite. This is a review of a proposal.

## Confirmed corrections

All findings from `source-retrieval-interface-review-pi.md` are addressed:

- Exit precedence is `2`, then `3`, then `1`, then `0`. Test 16 pins the mixed case.
- A skipped entry contributes `0` and never changes the exit. Test 15 covers it.
- The outcome table uses the label `magic mismatch` with exit contribution `1`.
- Validation runs before any fetch and covers an unknown `--entry ID`, an empty manifest,
  a duplicate `id` or `path`, an absolute or `..` path, an outside-root path, a link, a
  binding outside `supplier/pages`, a wrong `--dest`, an unknown `magic`, an unknown
  `distribution_decision` and an unknown field.
- `magic` values are `markup`, `pdf`, `xlsx` and `none`. Others are exit 2.
- `--check-only` follows the outcomes and writes nothing. Test 2 covers a match.
- The schema is `cad-skills/sources` version 1. The old `title` and `review_status` fields
  are refused.
- The manifest is rebuilt in that format. Nineteen tests cover the listed gaps.

## Remaining finding: the `exclude-full-copy` outcome is not defined

The allowed `distribution_decision` values are `exclude-full-copy` and
`exclude-local-evidence`. The outcome table only defines `skipped` for
`exclude-local-evidence`. The `exclude-full-copy` outcome is absent.

The rebuilt manifest uses `distribution_decision: exclude-full-copy` for all three entries.
So the behavior for the real manifest is ambiguous.

State the outcome. For example: `exclude-full-copy` follows the normal hash rule (fetch,
compare, write when the hash matches), and it only tells the release bundle to keep the full
copy out of the distribution. Add a test for it.

Also clarify this sentence: `Entries with distribution_decision: exclude-local-evidence are
not fetched. Their bytes are captured once as evidence.` The command does not fetch them, so
the command does not capture their bytes. Name the separate step that captures them.

## Minor findings

- `profile_binding` is listed as a field. State whether it is optional and whether `null` is
  allowed. The rebuilt manifest uses `null`. Add a test for a valid binding that resolves
  under `supplier/pages` and writes the page.
- `magic: xlsx` says `a zip header`. State the exact prefix, for example `PK\x03\x04`.
- State the `url` scheme rule. A `file://` or other scheme should be refused.
- State whether the HTTP client follows redirects.
- `content_type` is a field but no decision reads it. State that it is informational.
- `--dest` equality should use resolved paths, because a link to the root is otherwise
  unclear.
- Add a test for `--check-only` with a candidate entry. It must write nothing and exit 1.
- Add a test for a differing `--dest` with `--check-only`. The proposal allows it and the
  path is unused.

## Verdict

The revision answers the previous review. One blocker remains: define the
`exclude-full-copy` outcome and test it, because the rebuilt manifest uses that value. The
minor findings improve the interface but do not block it. No product edit. I hold for the
next revision or the frozen implementation.