# A1 and A2 replacement freeze r2 review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/artifact-a1-a2-freeze-r2-claude.sha256`. This review is
separate from the BOM text batch and the harness. It writes no product file. It does not
commit. It made no provider call.

## 1. Freeze and hashes

The freeze file `docs/reviews/artifact-a1-a2-freeze-r2-claude.sha256` has SHA-256
`7b01b363285f96e36ece6be1f74517f62622c9fd13dd29f3b1d21b546752bc26`. It matches the author
message.

| Item | Before | After |
|---|---|---|
| Entries | 155 | 155 |
| `sha256sum -c` | 155 of 155 OK | 155 of 155 OK |
| Freeze file hash | `7b01b363...` | `7b01b363...` |

Supersedes `87ea9b62...`.

## 2. Test reproduced

`uv run tests/test_artifact_fixtures.py` gives 16 of 16 passed, exit 0. No container, KiCad
process or simulator runs.

## 3. F-1 addressed

The focused test now holds five checks on the retained records.

| Test | Check |
|---|---|
| `test_a1_erc_and_drc_records_pass` | Each of `erc` and `drc` names its operation, status `pass`, exit 0, and no findings or waivers |
| `test_a1_update_record_is_ready_with_equal_identity` | The update record names its operation, state `ready`, status `pass`, identity `equal`, exit 0, and all options off |
| `test_a1_raw_outputs_match_their_bindings` | Each raw output file exists, its bytes match `raw_sha256`, its name carries the hash, and the tool exit is 0 |
| `test_a1_result_records_name_their_binding_files` | Each result record names its binding file by hash |
| `test_a1_closure_hashes_match_the_frozen_bytes` | Each closure entry names a file of the after tree with that hash, including the edited board |

These checks read frozen bytes only. They need no KiCad process. F-1 is closed.

## 4. F-2 addressed

`tests/eval/fixtures/artifacts/A1/README.md` now states that `after/README.md` is the
template README, unchanged, and still states R2 = 10 kohm and 2.086 V. It also states the
values for R2 = 20 kohm, 1.298 V, and names the procedure. F-2 is closed.

## 5. A2

A2 is unchanged and deliberately incomplete. The status is `incomplete`. The mandatory
failure is `service.order_multiple`. The pending condition is `silk_line_min_short_text`.
`package` and `review-source` are not run. The focused test still passes.

## 6. Low observation

### o1 `check --for ready` has no separate retained record

The A1 parent README lists `check --for ready` as step 8 and says it exits 0. That command
prints and exits. It writes no record. The focused test checks the inputs: `erc` pass, `drc`
pass, `sim` pass, the interface pass, and the update state ready. The exit is derivable from
those facts. No change is necessary. Retain an explicit record only if a later release
report needs the command exit as direct evidence.

## 7. Verdict

F-1 and F-2 are addressed. The freeze has 155 entries and all match. The focused test passes
16 of 16. A1 is ready within this scope. A2 is correctly incomplete.

I recommend acceptance of the A1 and A2 fixture freeze at
`7b01b363285f96e36ece6be1f74517f62622c9fd13dd29f3b1d21b546752bc26`. A full artifact run
still needs the harness adapter and the integrated skill acceptance. Provider
authorization stays zero.

I made no edit during this review.

## Limits

This review ran the focused fixture test and read the frozen bytes. It made no provider call
and no CAD call. It changed no product file.
