# Source retrieval interface review, revision 2 (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the revised proposal
`docs/reviews/proposals/source-retrieval-interface-claude.md`
(SHA-256 `fb9b478a1a817d20c99b5f4383a9119c8fff5f4f9d3df529b8fc23177ebf7b97`) and the manifest
`docs/reviews/proposals/sources.yaml`
(SHA-256 `d179915dfe91152adb19d33ced9ffd339e1a57849d68486a0b59985e13ff8dcb`).
I changed no product file. I ran no broad suite. This is a review of a proposal.

## Confirmed corrections

All r1 findings are addressed:

- `exclude-full-copy` is fetched and written to `DIR/<path>`. Tests 20 and 21 cover the
  match and the candidate.
- `exclude-local-evidence` is not fetched or verified. Tests 15 and 31 cover it.
- `profile_binding` is optional, and `null` is allowed. Test 22 covers a valid binding.
- The `xlsx` prefix is `PK\x03\x04`.
- Only `https` is allowed. Test 24 covers `http`.
- Redirects are fetch failures. Test 25 covers a 3xx response.
- `content_type` is informational.
- `--dest` equality uses resolved paths.
- `--check-only` with a candidate is covered by test 23.

The manifest schema, the field types and the validation order are clear. The test count is
now 31.

## Remaining findings

### Exit precedence does not include a write failure (blocker)

Test 29 expects exit 3 for a pre-replace failure in the atomic write. The overall exit
precedence only names a fetch failure for rule 3. A write failure is not a fetch failure.

Add a tool or write failure to the precedence list. For example: 2 validation, 3 fetch or
write failure, 1 candidate, changed or magic mismatch, 0 otherwise. State the post-replace
case too. `PIO.atomic_write` can raise `PostReplaceError` after the new bytes are in place.
Say whether that is exit 3 and whether the result reports the replaced file.

### The overall result states are inconsistent (clarification)

The `Multi-entry result` section says the overall result is one of `all match`, `partial` or
`none written`. The skipped section adds `no entry fetched` for a run where every entry is
skipped. Reconcile the list. For example, add `no entry fetched` as a fourth state.

### Non-2xx responses are not stated (clarification)

The proposal says a 3xx response is a fetch failure. State that any non-2xx response is a
fetch failure, including 4xx and 5xx. A 404 is an HTTP response, not a network error, and the
outcome table says `network error or timeout`.

### Duplicate `path` comparison (clarification)

`confine` resolves the path. Two raw paths such as `supplier/pages/x.html` and
`supplier/pages/./x.html` resolve to one destination. State that the duplicate check uses
the resolved path, not the raw string. Otherwise the second entry can overwrite the first.

### `profile_binding` value format (clarification)

The proposal says a value must resolve under the root `supplier/pages`. It does not define
the value. Is it a path under the root, a page id, or a path under `supplier/pages`? State the
format. Test 22 uses one valid form.

### Minor

- Add a test for `magic: none` with a match. The outcome is defined but not tested.
- State whether `retrieved` must be a real calendar date, not only the `YYYY-MM-DD` shape.
- Add a test for a differing `--dest` with `--check-only`. The proposal allows it and the
  path is unused.

## Verdict

The revision is close. One blocker remains: the exit precedence must include a write failure,
because test 29 expects exit 3 for it. The other findings are clarifications. No product edit.
I hold for the next revision or the frozen implementation.