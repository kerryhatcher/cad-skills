# Source retrieval interface review, revision 3 (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the revised proposal
`docs/reviews/proposals/source-retrieval-interface-claude.md`,
SHA-256 `d91247a96767e61396246a00856ce389489ca2cf28792397f0e1f2950cc96de2`.
I changed no product file. I ran no broad suite. This is a review of a proposal.

## Confirmed corrections

All r2 findings are addressed:

- The exit precedence is validation 2, then a fetch or write failure 3, then candidate,
  changed or magic 1, then 0. Rule 2 names a write failure before and after the replace.
- A pre-replace write failure is exit 3 and keeps the old bytes. Test 29 covers it.
- A post-replace failure is reported as a write error with exit 3. The new bytes stay, and no
  rollback is claimed. Test 33 covers it.
- The overall result list includes `no entry fetched` and `write error`.
- A non-2xx response is a fetch failure. Test 32 covers 404 and 500.
- The duplicate check uses resolved destinations.
- `profile_binding` is a relative string under `supplier/pages/`, with no `..` segment and no
  absolute prefix.
- `retrieved` must be a real calendar date. Test 36 covers `2026-02-30`.
- Tests 32 to 37 cover magic none, check-only with a differing destination, a post-replace
  failure, a non-2xx response, a bad date and a bad binding.

## Remaining finding: the profile-bound destination is ambiguous (blocker)

The proposal gives two rules for a profile-bound entry:

- `Each entry path is a relative path under the root... The destination is DIR/<path>.`
- `A profile_binding entry must resolve under the root's supplier/pages.`

The relationship between `path` and `profile_binding` is not defined. Test 22 says a valid
`profile_binding` under `supplier/pages` `matches, is written there, and exits 0`. `Written
there` suggests the binding path, but the destination rule uses `path`.

The profile `evidence_pages` names a page at a fixed path, for example
`supplier/pages/two-layer.html`. The retrieved bytes must land at that path. If `path` and
`profile_binding` differ, the file lands at another path and the binding is broken.

State the rule. For example: when `profile_binding` is not `null`, `path` must equal
`profile_binding`, and the destination is `DIR/<profile_binding>`. Add a test where `path`
and `profile_binding` differ and the entry is refused with exit 2.

## Clarifications

- The `Multi-entry result` section keeps two overall-result lists. The first says `all match,
  partial, or none written`. The second adds `no entry fetched` and `write error`. Remove the
  first list, or make the two lists agree.
- Test 10 says `a duplicate path`. The rule now uses resolved destinations. State `a
  duplicate resolved destination` in the test.

## Minor

- The `profile_binding` value must be a page path. State whether `path` must equal it for a
  bound entry, and whether an unbound entry may use a `path` outside `supplier/pages`. The
  rebuilt manifest uses `profile_binding: null` with paths under `supplier/guidance/`.

## Verdict

The revision answers r2. One blocker remains: state the profile-bound destination and the
`path` and `profile_binding` relationship. The other findings are clarifications. No product
edit. I hold for the next revision or the frozen implementation.