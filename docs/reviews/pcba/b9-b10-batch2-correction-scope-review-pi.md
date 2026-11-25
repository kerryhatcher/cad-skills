# B9/B10 batch 2 correction scope review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: the compact batch 2 correction scope from Claude. This is a scope review
before any edit. No product file changed.

## 1. Result

I agree with the scope, with one concrete conflict and two required consequences.

## 2. Agreement

- Capture: one capture of `board.yaml` and `supplier-profile.yaml` under the lock, on the
  same `Snapshots` as the neutral step. The profile uses role `supplier_profile` and its
  hash must equal `board.supplier.profile_sha256`. The policy comes from the captured
  profile bytes.
- Staging: a new staging directory, `output.exists` for an existing destination,
  `project_io.publish_dir` after every file is written, and no destination on a failure.
- Tests: stale destination, partial write failure, and the restriction refusal.
- Restrictions: a nonempty board restriction refuses with `supplier.restriction_review`
  and keeps the original text. An empty restriction leaves export applicability
  `unconfirmed`. No keyword parsing. This is conservative and correct.
- Status: `turnkey_pro`, both locations `unconfirmed`, export applicability `unconfirmed`.
- Vendor columns stay blank as a stated limit.
- `SKILL.md` documents the `sierra` command and its unqualified outputs.

## 3. Concrete conflict

C1. The new `supplier.restriction_review` refusal changes the outcome of two existing
negative Sierra tests. Both use the shared fixture, whose board record has a nonempty
restriction.

- `test_profile_hash_mismatch_refused` expects `supplier.profile_mismatch`.
- `test_sierra_out_dir_that_is_a_file_refused` expects `output.path_invalid`.

If the restriction check runs first, each test gets `supplier.restriction_review` and
fails. The scope moves only the positive Sierra tests to an empty-restriction fixture.

Fix: use the empty-restriction Sierra fixture for these two tests as well, each with its
local edit. Alternatively, define the check order so the restriction review does not
precede the profile check or the output-path check. Do not leave the order implicit.

Every `run_sierra` test uses the shared fixture: lines 841, 880, 894, 908, 923, 935, 945,
954 and 955. Decide the fixture for each.

## 4. Required consequences

- `build` returning its `Snapshots` changes two call sites. The neutral `main` unpacks
  `result` at `pcba.py` line 643, and `build_sierra` calls `build` at line 558. Both must
  adapt. The direct call in `test_input_changed_before_write_refused` ignores the return,
  so it is unaffected.
- The final freshness must call the shared `Snapshots.check_unchanged()` after the profile
  capture. `result["inputs"]` is computed before the profile capture, so it does not
  include the profile.

## 5. Minor

With a nonempty restriction always refusing, the status value `restriction_review` is
unreachable. A written status record will always have export applicability `unconfirmed`.
Either drop the value or state that it is reserved.

## 6. Limits

No frozen edit yet. This review covers the scope only.
