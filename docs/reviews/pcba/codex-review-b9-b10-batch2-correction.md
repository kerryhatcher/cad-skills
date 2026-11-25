# Review of the B9 and B10 batch 2 correction

Date: 2026-11-15 UTC. Reviewer: codex-pcba-dev. Branch: `work/pcba`.

## Frozen boundary

I checked all 36 hashes in `docs/reviews/pcba/b9-b10-batch2-correction-claude.md`. All hashes match. The author reports 66 focused tests passed. I did not run tests. The release-owned snippet route remains separate.

The correction captures the supplier profile through the shared `Snapshots` object and rechecks all captured inputs before publication. It stages the output set and publishes it once. It also refuses nonempty restrictions with their source text and leaves neutral tests on the original fixture.

## Finding

**Blocker: an output path can overlap the fixed staging path and raise an uncaught `ValueError`.** The command accepts a new output directory inside the project. It does not reject `out/pcba/.sierra-staging` or an ancestor such as `out/pcba`. The command then writes into the fixed staging directory and calls `project_io.publish_dir`. That helper raises `ValueError` when the source and destination overlap. The command does not catch that error, so it prints a traceback and leaves the staging directory. Reject any destination that equals, contains, or sits inside the staging path before capture. Add a focused negative test.

## Before and after hashes

| File | Before this correction | Frozen correction |
|---|---|---|
| `skills/pcba-design/scripts/pcba.py` | `a8f1e0d832444a1820141ec3dafbd5a6fde65fd50cad47c9898ce8dbd82678ab` | `435528f5760d797362866a62a6e31fdada6fe58f760bc40252042141f7d561ad` |
| `skills/pcba-design/scripts/sierra.py` | `13fc4636733498ef568a22d9acb4a881b6aa147a11dd51f4c78604ac46630887` | `f4d8ef1a3b5e832ec0743501cce55947fb019d5ced77576537dcaaa276f0d379` |
| `skills/pcba-design/SKILL.md` | `371f99d5ae246b43ad6f2f764bb898a2148be29d8d62896c942af5736585fb7f` | `f410fa82a6dddca12e7b2cf76b2969b78c982275e105bebc3adf813b6458fddc` |
| `tests/test_pcba_design.py` | `7798a91c507b46e550f331137133c60c6e5a82ff77563b54e96ead88dfdd262b` | `2602a6dd184c696df2d76f7e7479b05807a94f15c723a90e7743347927edbcb3` |

## Decision

The correction does not pass review until the staging overlap path returns one controlled refusal and leaves no staging output. The accepted neutral scope stays closed. The full B10 package remains unimplemented and outside this review.

This report changes no product file or shared contract.
