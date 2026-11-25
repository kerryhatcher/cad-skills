# B9/B10 batch 2 correction review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b9-b10-batch2-correction-claude.md`, the frozen batch 2
correction. Reviewed against the combined scope and the batch 2 release root. I changed
no product file.

## 1. Result

I accept the correction. The three findings are resolved. No blocker.

- `uv run tests/test_pcba_design.py`: 66 passed, 0 failed, exit 0.
- All 36 listed file hashes match.
- `sha256sum -c skills/pcba-design/COPY_SHA256.txt`: 15 of 15 copies OK.
- `uv run tests/test_skill_packages.py`: 7 of 8. The failure is only the release-owned
  snippet route.

## 2. Before and after hashes

The correction changed four files. The other 32 files are unchanged.

| Path | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `371f99d5ae246b43ad6f2f764bb898a2148be29d8d62896c942af5736585fb7f` | `f410fa82a6dddca12e7b2cf76b2969b78c982275e105bebc3adf813b6458fddc` |
| `skills/pcba-design/scripts/pcba.py` | `a8f1e0d832444a1820141ec3dafbd5a6fde65fd50cad47c9898ce8dbd82678ab` | `435528f5760d797362866a62a6e31fdada6fe58f760bc40252042141f7d561ad` |
| `skills/pcba-design/scripts/sierra.py` | `13fc4636733498ef568a22d9acb4a881b6aa147a11dd51f4c78604ac46630887` | `f4d8ef1a3b5e832ec0743501cce55947fb019d5ced77576537dcaaa276f0d379` |
| `tests/test_pcba_design.py` | `7798a91c507b46e550f331137133c60c6e5a82ff77563b54e96ead88dfdd262b` | `2602a6dd184c696df2d76f7e7479b05807a94f15c723a90e7743347927edbcb3` |

No shared contract file changed. The sample provenance and the retained `.xls` are
unchanged.

## 3. Resolved findings

- C1: the check order is output validity, then profile presence and hash, then
  restrictions, then policy. Probes confirm that an output directory that is a file gives
  `output.path_invalid`, and a changed profile gives `supplier.profile_mismatch` before the
  restriction check. The two negative tests keep the shared fixture. The positive,
  determinism, policy and stale-destination tests use the owned empty-restriction copy.
- G1: the status record now has `service` with `service` `turnkey_pro`, the supplier id,
  and both locations `unconfirmed`, and `export_applicability` `unconfirmed`. The
  unreachable `restriction_review` status value is dropped.
- G2: a nonempty restriction refuses with `supplier.restriction_review`, and the message
  keeps the original text. An empty list leaves export applicability `unconfirmed`. The
  tool does not infer export-control status. This is conservative and correct.

## 4. Verified

- Capture: the neutral inputs and the supplier profile go through one `Snapshots` object
  under the lock. The profile uses role `supplier_profile` and its hash equals
  `board.supplier.profile_sha256`. The policy comes from the captured profile bytes.
- Final freshness: `Snapshots.check_unchanged` rehashes every captured input, the profile
  included, before the publish. A tampered profile refuses before publication.
- Staging: the complete set is staged inside the project and published once with
  `project_io.publish_dir`. An existing destination refuses with `output.exists` and the
  earlier BOM is untouched. A partial write publishes nothing and the staging directory is
  removed. A leftover staging directory refuses with `output.staging_exists`.
- The positive Sierra run writes the BOM, the XY draft, the test record and the status.
- The `SKILL.md` describes the `sierra` command, its outputs and the `unqualified` status.
- Vendor columns stay blank. The provenance stays honest. Release owns fresh retrieval.

## 5. Non-blocking note

The `SKILL.md` Status section still says the skill "covers the neutral step only". The next
sentence documents the `sierra` command and its draft set. Update the first sentence to
include the Sierra draft step.

## 6. Limits

The publication batch with the full manifest, the fabrication Gerber drawing, the drill
files, the board image and the assembly drawing remain later work. The snippet route stays
an integration task.
