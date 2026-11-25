# Packaging review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: check of D-1 to D-8 against `tests/eval/packaging.py`, `tests/eval/distribution.yaml`,
and `skills/pcb-fab-package/sources.yaml`. This report gives the result. It writes no
product file. It does not commit.

## Freeze

The freeze list is
`/tmp/claude-1000/-mnt-storage-projects-cad-skills-worktrees-release/eaf2167c-7fd4-482f-935e-4f1b42b4cdd7/scratchpad/packaging-freeze.sha256`.

| Result | Value |
|---|---|
| Entries | 11 |
| `sha256sum -c` | 11 of 11 OK, exit 0 |

I reproduced the test result:

| Command | Result |
|---|---|
| `uv run tests/test_release_packaging.py` | 20 of 20 passed, exit 0 |

## Finding check

| ID | Requirement | Result |
|---|---|---|
| D-1 | Each stored supplier source has a manifest entry | Pass for the 16 stored sources. Scope gap P-2 |
| D-2 | Required fields, URL or `url_state` | Pass |
| D-3 | No full supplier copy in the distributed set | Pass |
| D-4 | No local evidence in the distributed set | Pass. All 8 `.headers` files are excluded |
| D-5 | A changed hash needs a recorded review and a profile binding | Pass. The profile `evidence_sha256` is the binding authority |
| D-6 | Only allowlisted supplier files ship | Pass |
| D-7 | Fixtures hold no supplier bytes | Pass |
| D-8 | File magic agrees with the recorded format | Pass for the 6 repository entries. Gap P-1 for the 10 skill entries |

The 16 stored sources are 10 OSH Park page files and 6 Sierra evidence files. The count is
correct.

## Findings

### P-1 D-8 is not exercised for the 10 skill page entries

The repository `tests/eval/distribution.yaml` records a `magic` value for each of its 6
entries. The skill `skills/pcb-fab-package/sources.yaml` records no `magic` field for any
of its 10 entries.

`_magic_ok(None, ...)` returns `True`. Thus D-8 skips every skill page. A recorded format
for the 10 pages is not checked.

Correction: add `magic` to each skill entry. Use `markup` for the five HTML pages and
`null` for the five header files. Alternatively, derive the expected format from
`content_type` and require a recorded `magic`. Add a fixture test where a skill entry
omits `magic` and the check reports the gap.

Severity: medium. The SHA-256 still binds the bytes, so a substituted page with the same
hash is not possible. D-8 is defense in depth. The correction gives the check its stated
coverage.

### P-2 D-1 coverage is limited to `supplier/pages/**`

`supplier_sources` globs `skills/*/supplier/pages/**/*` and
`docs/reviews/sierra-source-evidence/*`. A stored supplier source elsewhere under
`skills/*/supplier/` is not covered.

I demonstrated this on a temporary tree:

| Path | Detected by D-1 |
|---|---|
| `skills/demo/supplier/pages/page.html` | Yes |
| `skills/demo/supplier/other/page.html` | No |

Correction: glob `skills/*/supplier/**/*` and remove the allowlisted paths, or state the
narrow scope in the module docstring and add a fixture test for the current scope. Add a
fixture test for a supplier file outside `pages/`.

Severity: medium for coverage. The current tree stores the pages under `pages/`, so the
present result is correct. The rule is weaker than the interface text.

### P-3 The Sierra source URL is marked unrecorded

The repository manifest writes `url_state: "not recorded in the repository (provenance
open, O6)"` for `xy.pdf`, `xyrs.xlsx`, and their headers. The source pages are named in
`docs/reviews/b9-source-addendum-root.md`.

Correction: record the source page URL for each item. If the exact file URL is unknown,
name the linking page and its retrieval date. This satisfies the O6 source URL field.

Severity: low. The notice records the open state honestly.

### P-4 The freeze list is not retained

The freeze list is in a `/tmp` scratchpad. It can be removed.

Correction: copy the freeze list into the review area, or list the 11 hashes in the
review report. A release record needs the tested bytes.

Severity: low. The hashes are in this report and in the author record.

### P-5 Minor wording

The D-8 message says the magic does not match the "recorded content type". The check
compares the bytes with the `magic` field. Correction: say "recorded magic".

## Confirmed correct

- The manifest does not approve anything. The profile content and evidence hashes and the
  source-review record bind the data.
- `license_state` is informational. `distribution_decision` is separate.
- No acknowledgment gate exists. The text check passes.
- Zero fetch scripts is reported as provisional. The test does not fail on it.
- The distribution is built from tracked files. The checks read bytes and hashes.
- Project-authored fixtures cover each defect. No fixture holds supplier bytes.
- The D-3/D-4 regression check fires when the exclusions are absent.

## Verdict

Accept with corrections P-1 to P-5. P-1 and P-2 are the substantive corrections. P-3 and
P-4 are record corrections. P-5 is a wording change. The 20 tests pass. The check reads
no provider and contacts no supplier.

## Limits

This review ran the local test suite. It made no provider call and no CAD call. It changed
no product file. It does not approve a release. The final release cannot pass without the
setup fetch path.
