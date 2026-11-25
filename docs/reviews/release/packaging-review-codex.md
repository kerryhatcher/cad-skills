# Packaging review from codex-release-dev

Date: 2026-11-15 UTC.

Scope: review of the second packaging freeze, the packaging checker, both manifests, and the new packaging tests. This report does not approve a public release.

## Freeze and test evidence

The freeze file is [b12-packaging-freeze-claude.sha256](../b12-packaging-freeze-claude.sha256). I ran `sha256sum -c` on this file. All 13 entries matched.

Claude reported 22 of 22 packaging tests and 37 of 37 harness tests. Pi reports that both results reproduced. I did not run these tests.

The first freeze list did not match `tests/eval/isolate.py`. The second freeze includes the changed hash. The second freeze passes.

## Review findings

### P-1 to P-5: corrected

- The skill source manifest has a `magic` key for each entry. Five HTML pages use `markup`. Five header files use `null`.
- Coverage now scans `skills/*/supplier/**` and the Sierra evidence tree. It skips allowlisted support files. A test covers a supplier file outside `pages/`.
- The Sierra manifest names source URLs and states when the retained bytes do not match a verified download. It does not contact the supplier.
- The freeze list now stays in the repository.
- The D-8 message names the recorded magic value.

### P-6: `null` can disable the format check

The current data uses `null` only for header files. The checker accepts `magic: null` for any content type because `_magic_ok(None, ...)` returns `True`. The test text says null applies to header text, but the checker does not enforce this limit.

**Correction:** Reject `magic: null` for HTML, PDF, and XLSX content types. Add a fixture test for each supported type. Keep null for header text only.

### P-7: a copy outside known paths can enter the distribution

The distribution check uses source paths, exclusions, and supplier path rules. It does not hash every distributed file against the known full-copy hashes. A copy of a supplier page at another path, such as `examples/reference.html`, can pass the current checks.

**Correction:** Compare hashes of all candidate distribution files with the hashes for excluded full copies. Add a project-authored regression fixture that puts a known source hash at an unrelated path. Fail distribution when the bytes match. Do not block a project-authored PDF or HTML file by file type alone.

## Agreement with the bounded interface

The second freeze follows the accepted interface for the source manifest, distribution allowlist, and known path exclusions. The manifest records source data. Existing profile hashes and the source-review record remain the binding authority. The manifest does not add a second approval record.

The notices keep license state informational for local retrieval. The allowlist controls distribution. The checker uses project-authored fixtures. Zero fetch scripts remain acceptable for this provisional packaging test. A final standalone release still needs the explicit setup fetch path.

The source entries for `xy.pdf` and `xyrs.xlsx` use URLs from `b9-source-addendum-root.md`. The manifest states that the retained bytes are not verified against those URLs. This record preserves the known limit.

## Result

The second freeze is valid. The earlier P-1 to P-5 corrections are present. Add P-6 and P-7 before the final packaging gate. Do not run provider evaluations for these checks.

This review made no product edits. It made no provider calls and contacted no supplier. It did not run the test suites.
