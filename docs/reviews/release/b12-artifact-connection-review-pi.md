# Artifact connection freeze review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-artifact-connection-freeze-claude.sha256` against the
scope `docs/reviews/release/b12-artifact-connection-scope-pi.md`. This report writes no
product file. It does not commit. It made no provider call.

Update: the root A2 run-binding concern is confirmed in
`docs/reviews/release/b12-a2-run-binding-defect-pi.md`. The current A2 `all_pass` accepts a
minimal run. The acceptance recommendation in this report is superseded. The A2 run-facing
expectations must read the produced rows. See that report for the correction.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-artifact-connection-freeze-claude.sha256` has SHA-256
`09c052d84cddc4c941992641bbba32158292edf37dfcf5cc8c24adc5cd649559`. It matches the author
message and the lead message.

| Item | Before | After |
|---|---|---|
| Entries | 198 | 198 |
| `sha256sum -c` | 198 of 198 OK | 198 of 198 OK |
| Freeze file hash | `09c052d8...` | `09c052d8...` |

The A1 and A2 fixture entries are byte-identical to `artifact-a1-a2-freeze-r2-claude.sha256`.
`comm` on the fixture lines reports no difference. The frozen fixture bytes are unchanged.

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_artifact_expectations.py` | 11 of 11 passed, exit 0 |
| `uv run tests/test_artifact_fixtures.py` | 16 of 16 passed, exit 0 |
| `uv run tests/test_release_harness.py` | 65 of 65 passed, exit 0 |
| `uv run tests/test_release_packaging.py` | 32 of 32 passed, exit 0 |
| `uv run tests/test_release_isolation.py` | 29 of 29 passed, exit 0 |

No provider call and no network call.

## 3. Scope check

| ID | Item | Result |
|---|---|---|
| S-1 | A1 25 and A2 7 expectations under `artifact_checks` | Present. `fixture_root` and `run_root` name the roots. `base` selects a root per item |
| S-2 | `absent`, `json_path_equals`, `record_binding`; `json_equals` requires the key | Present. `sha256`, `json_equals`, `json_path_equals`, `sha256_binding`, `record_binding`, `exists`, `absent` |
| S-3 | `tests/test_artifact_expectations.py` runs the matrix expectations against the frozen roots | Present. 11 tests |
| S-4 | A2 stays incomplete | Present. `overall == incomplete`, `package == not run`, `review-source == not run`, `supplier.exit == 1`, the one fail, the one pending, and an absent package |
| S-5 | No fixture, model, trust or credential change | Present |
| S-6 | A new freeze for the changed matrix, checker and test | Present |

### Explicit roots

`check_one` selects `fixture` or `run` from the `base` field. A `sha256_binding` item can
use a separate `reference_base`. The A1 prior-board item uses `base: run` with
`reference_base: fixture`. A1 sim items use `base: run`.

### Array indices

`json_path_equals` accepts a list of string keys and integer indices. `_lookup` rejects a
boolean index, a non-integer index, and an out-of-range index. `test_array_index_out_of_range_fails`
covers an out-of-range index and a string key used on an array.

### Missing keys

`_lookup` returns not-found for a missing key. `json_equals` and `json_path_equals` fail on
the missing key, even when the expected value is null.
`test_missing_key_fails_even_when_expected_is_null` covers it.

### Confined paths

`resolve_under` refuses an absolute path, a `..` part, an empty path, a symbolic-link
component, and a candidate outside its root. A refused path fails every kind.
`test_linked_artifact_path_is_refused` and `test_escaping_artifact_path_is_refused` cover it.

### Dangling-link absence

`absent` passes only when nothing exists and no link exists. A dangling link fails.
`test_dangling_link_fails_the_absent_expectation` and `test_absent_passes_when_nothing_exists`
cover both cases.

### Record-bound raw hashes

`record_binding` reads `raw_file` and `raw_sha256`, validates the 64-hex value, resolves the
raw path under its root, and compares the bytes.
`test_record_binding_fails_when_the_raw_file_changes` covers a changed raw file.

### A2 incomplete

`test_a2_expectations_pass_and_record_the_incomplete_state` requires the overall, package
and supplier checks. `test_complete_a2_claim_fails` changes the status to `complete` and adds
a package. The status and absence expectations fail. A2 cannot pass as a complete package.

## 4. Freeze pointer

`tests/test_release_harness.py` now points `FREEZE` at
`docs/reviews/b12-artifact-connection-freeze-claude.sha256`. The freeze holds every consumed
harness input:

- All `tests/eval/*.py` modules, `matrix.yaml`, and `distribution.yaml`.
- The five release test files.
- The CLI help fixtures, the stub, and the 154 artifact fixture files.
- `.github/workflows/test.yml`, `.gitignore`, and the skill source manifest.

The harness freeze completeness test passes on this pointer.

## 5. Concrete defects

None block acceptance.

### o1 The manifest-directory ancestor link limit applies here too

`resolve_under` calls `_has_link` on the root. A repository under a symlinked ancestor
reports a refusal for every expectation. This is the same class of limit the lead recorded
for the source-path normalization. Use a checkout path with no symlinked ancestor in CI.

### o2 The artifact connection freeze does not include the notice

`docs/release-licensing.md` was in the earlier harness freeze. It is not a harness input, so
its absence is correct. The notice lives in its own batch.

## 6. Verdict

S-1 to S-6 are implemented. The expectations run through the checker. The roots, array
indices, missing keys, confined paths, dangling-link absence and record-bound raw hashes are
covered by positive and negative tests. A2 stays deliberately incomplete. The frozen fixture
bytes are unchanged. The freeze pointer holds every consumed harness input.

I recommend acceptance at freeze
`09c052d84cddc4c941992641bbba32158292edf37dfcf5cc8c24adc5cd649559`. Provider
authorization stays zero.

I made no edit during this review.

## Limits

This review ran focused local tests. It made no provider call and no CAD call. It changed no
product file.
