# A3 connection freeze review from Pi

Date: 2026-11-15 UTC.
Author: pi-release-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of the A3 connection implementation and freeze in the integration worktree.
This report writes no product file and does not edit the integration worktree. It ran Python
through `uv` only. It made no provider call and no package run.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-a3-connection-freeze-root.sha256` in the integration
worktree has SHA-256
`7ae60dedf3ca70de0fcb79b4fef9f96a58bf764905fbc9d5d314ea51b116290a`. It matches the lead
message.

| Item | Before | After |
|---|---|---|
| Entries | 261 | 261 |
| `sha256sum -c` | 261 of 261 OK | 261 of 261 OK |
| Freeze file hash | `7ae60ded...` | `7ae60ded...` |

Key file hashes:

| File | SHA-256 |
|---|---|
| `tests/eval/check_artifacts.py` | `cce4810dac35bb80fa9204188088530e41e980cca5495f81c9c229ce7acf9040` |
| `tests/eval/matrix.yaml` | `f45b261120ea4820dfef3c9f14db41609504299bf40b9d6e4616540460e42fe1` |
| `tests/test_artifact_expectations.py` | `2c044da8dedf4a1411894f5f1e8a64fb137acb1ef0de91e375228bd1289f26d1` |
| `tests/test_release_harness.py` | `cdf07c88cc6d65fe5bde01510566484b178d5879e1b8ae97f3e378144e7c5ba1` |
| `tests/eval/fixtures/artifacts/A3/source-copy-hashes.json` | `3a0425b16c7a3ac1396f5938911112b025e9f452bb65c6431b85d6590a3901a9` |

The freeze holds 60 A3 fixture entries: 59 copies and the copy hash map. The harness `FREEZE`
pointer names this freeze. The A1 and A2 entries are byte-identical to the accepted release
freeze. `comm` reports no difference.

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_artifact_expectations.py` | 30 of 30 passed, exit 0 |
| `uv run tests/test_artifact_fixtures.py` | 16 of 16 passed, exit 0 |
| `uv run tests/test_release_harness.py` | 65 of 65 passed, exit 0 |
| `uv run tests/test_release_packaging.py` | 34 of 34 passed, exit 0 |

No package run, no container and no provider call.

## 3. Source-copy hash map

`tests/eval/fixtures/artifacts/A3/source-copy-hashes.json` records
`source_manifest_sha256` `d419688f2e4b5b30a35209985f619c2fc46ae2d58c2a1d949feb9ab24079ca64`
and 59 file entries with `source`, `path` and `sha256`.

I checked every entry with a read-only `uv` probe:

| Check | Result |
|---|---|
| Entry count | 59 |
| Local path exists and hash matches the map | Pass |
| Local hash matches the accepted PCBA source bytes | Pass |
| Local path repeats | None |
| `source_manifest_sha256` | Matches the accepted PCBA manifest |

The local tests need no external worktree.

## 4. A3 matrix expectations

The A3 block uses `fixture_root: tests/eval/fixtures/artifacts/A3` and
`run_root: tests/eval/fixtures/artifacts/A3/retained/pkg-standard`.

| Group | Count | Base |
|---|---|---|
| Run expectations | 19 | `run` |
| Fixture expectation | 1 | `fixture` |

The run expectations produce the accepted unqualified result:

- `manifest.json` status `unqualified`.
- The exact pass, fail and unconfirmed check id sets.
- Check count 13.
- DRC evidence status `fail`.
- DRC report `violations` length 15 and `unconnected_items` length 16.
- Stock evidence status `fail` and the `EX-LED-0603-G` stock row.
- Supplier rules `unconfirmed`.
- Sierra `qualification` `unqualified` and `export_applicability` `unconfirmed`.
- `physical_test_passed` false, the two `not measured` items and the item count 2.
- The board binding to the fixture project board.
- The output binding over 41 unique output paths, hashes and byte counts.
- The output count 41.

The two additions beyond the proposal are `A3-physical-test-count` and the `size_key`
byte-count check in the output binding.

## 5. New checker kinds

| Kind | Behavior |
|---|---|
| `length_equals` | The array at `json_path` has the integer length `value`. A non-integer or negative expectation raises. A missing or non-list array fails |
| `row_binding` | Each row names a unique file through `path_key` and a 64-hex hash through `hash_key`. An optional `size_key` names the byte count. A missing array or row object, a missing or invalid path or hash, an escape, a link, a duplicate path, an absent file, a hash mismatch or a byte-count mismatch fails |

The `row_binding` duplicate check uses the resolved path. Two relative paths that resolve to
one file are caught.

## 6. Focused mutations

| Test | Check |
|---|---|
| `test_a3_frozen_package_and_copy_hashes` | The 59 copies match the map. The run and fixture expectations pass |
| `test_a3_minimal_manifest_does_not_pass` | A status-only manifest fails the output binding |
| `test_a3_semantic_changes_fail_after_new_output_hashes` | A changed DRC violation count or `physical_test_passed` fails the semantic expectation after the manifest output hash and size are refreshed. The output binding does not fail, so the semantic expectation detects the defect independently |
| `test_a3_wrong_check_sets_fail` | A changed check id fails the exact set |
| `test_a3_output_bindings_refuse_mutations` | Bytes, missing, link, duplicate, escape, size, bad-hash and missing-key mutations all fail the output binding |
| `test_length_equals_refuses_missing_and_non_list_values` | `{}`, an empty string, an object and null all fail |
| `test_a3_board_binding_uses_the_fixture_board` | A changed fixture board fails its binding |

The refreshed-hash test is the important case. A correct output hash cannot conceal an
incorrect DRC count or a false physical pass.

## 7. Verdict

The A3 connection is correct. The freeze has 261 entries and all match. The focused
expectations pass 30 of 30, the fixtures 16 of 16, the harness 65 of 65 and the packaging 34
of 34. The source-copy map binds every copy to the accepted PCBA bytes. The 19 run
expectations read the produced package bytes, including the item count, the DRC counts and
the output byte counts. The semantic mutation tests detect a defect after a refreshed output
hash. No A1 or A2 byte changed. A3 remains held. Provider authorization stays zero.

I accept the A3 connection freeze at
`7ae60dedf3ca70de0fcb79b4fef9f96a58bf764905fbc9d5d314ea51b116290a`.

I made no product edit and did not edit the integration worktree.

## Limits

This review ran focused local tests and read-only `uv` probes. It made no provider call, no
package run and no CAD call. It changed no product file.
