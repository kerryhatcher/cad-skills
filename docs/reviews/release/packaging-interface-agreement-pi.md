# Packaging interface combined agreement

Date: 2026-11-15 UTC.
Authors: codex-release-dev (Codex) and pi-release-dev (Pi), reviewers.

Scope: combined agreement for the bounded supplier packaging interface. This report
confirms that both reviewers agree. Claude can implement it. The reviewers write reports
only and change no product file.

## Agreement

Both reviewers agree to the bounded packaging interface. The final findings are D-1 to
D-8 in `docs/reviews/release/supplier-page-packaging-boundary-pi.md`.

Codex recorded the same boundary in `docs/reviews/release/b12-matrix-review-codex.md`.
Codex also agreed in a direct message and will correct its report so that the source
manifest does not duplicate approval records.

## Bounded interface

| Item | Value |
|---|---|
| Check path | `tests/test_release_packaging.py` |
| Provider call | None |
| Fixtures | Project-authored page fixtures |
| Manifest scopes | Skill-level `sources.yaml`, plus a repository-level manifest for the Sierra evidence |
| Distribution control | Explicit provenance manifest plus a distribution allowlist |
| Regression exclusions | `skills/*/supplier/pages/**` and the known Sierra evidence, including the `.headers` files |
| License state | Informational only. Separate from the distribution decision |
| Acknowledgment gate | Rejected |
| Approval authority | The existing supplier-profile content and evidence hashes and the source-review record |
| Changed bytes | A new recorded review and a profile binding. No automatic acceptance |
| Fetch script | Zero scripts is valid for a provisional test. A final standalone release cannot pass without the setup path |
| File magic | Identifies format, not license or ownership. A project-authored PDF or HTML fixture is not forbidden by type alone |

## Finding list

| ID | Check |
|---|---|
| D-1 | Each supplier source has a manifest entry in the correct scope |
| D-2 | Each entry has URL, retrieval date, SHA-256, content type, `license_state`, and `distribution_decision`. No acknowledgment field |
| D-3 | A distributed file is on the allowlist. No full supplier copy and no local evidence file, including `.headers` |
| D-4 | The local evidence is in the review tree and absent from distribution |
| D-5 | A changed hash has a recorded review and a profile binding |
| D-6 | Only the manifest and the fetch script ship for supplier sources. Zero fetch scripts is valid provisionally |
| D-7 | Fixtures are project-authored |
| D-8 | Type detection reads the extension and the file magic. The recorded hash decides a change |

## Reviewer corrections accepted

| ID | Source | Correction |
|---|---|---|
| Isolation | Codex | Routing mode installs all three accepted skills. Single-skill mode supports artifact and explicit invocation. The baseline root holds none |
| Approval | Codex | The source manifest does not duplicate the approval record |
| Selected paths | Codex | Store selected skill names and paths as lists. Keep discovered paths separate |
| Blocked cells | Codex | A1 waits for B7/B8. A3 waits for the accepted PCBA package |

## Next step

Claude implements `tests/test_release_packaging.py` with project-authored fixtures and no
provider call. Both reviewers examine the code and the fixture results. No commit before
both reviews and lead acceptance.

## Limits

This agreement uses no provider call and no CAD tool. It changes no product file.
