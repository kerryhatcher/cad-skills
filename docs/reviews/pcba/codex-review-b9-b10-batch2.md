# Review of B9 and B10 batch 2

Date: 2026-11-15 UTC. Reviewer: codex-pcba-dev. Branch: `work/pcba`.

## Frozen boundary

I checked all 36 hashes in `docs/reviews/pcba/b9-b10-batch2-claude.md`. All hashes match. The author reports 62 focused tests passed. I did not run tests. The release-owned snippet route remains separate.

The provenance record states that the sample retrieval time and reuse terms are not known. It does not claim a page fetch. This matches the source evidence in this batch.

## Findings

1. **Blocker: old or partial supplier files can remain in the output directory.** `build_sierra` omits the BOM file when the policy is missing or unknown, then writes the other files into the existing output directory. It does not remove an old BOM or refuse an existing output set. A second run can therefore report `bom: not_produced` while an old BOM remains. A write failure after one file also leaves a partial set. Use a new staging directory and publish the complete set only after all writes succeed, or refuse an existing output directory.

2. **Blocker: the supplier profile is not a captured input.** `build_sierra` reads `board.yaml` again after the neutral build and reads `supplier-profile.yaml` outside `Snapshots`. The final freshness loop checks only the neutral input list. That list does not include the supplier profile. A profile change after its hash check can therefore go undetected. Capture the board and profile once, bind the profile under the existing `supplier_profile` role, derive policy from captured bytes, and include it in final freshness.

3. **Blocker: the skill guide contradicts the new command.** `skills/pcba-design/SKILL.md` says the skill does not convert supplier formats and documents only the neutral command. The frozen code adds the `sierra` command and writes supplier-format files. Update the guide with the command, outputs, and unqualified status behavior.

The alternate selection corrections pass code review. The selection type checks run before lookup. The schema and loader refuse alternates on mechanical entries. The approval key binds the reference, variant, and alternate. The sampled output keeps supplier conventions unconfirmed and the qualification status unqualified.

## Changed file hashes

| File | Before this batch | Frozen batch 2 |
|---|---|---|
| `skills/pcba-design/scripts/pcba.py` | `f77ce802567606504fd0101acdac276ec6ee5fb9052a26113a0da08a4f52b8cc` | `a8f1e0d832444a1820141ec3dafbd5a6fde65fd50cad47c9898ce8dbd82678ab` |
| `skills/pcba-design/SKILL.md` | `371f99d5ae246b43ad6f2f764bb898a2148be29d8d62896c942af5736585fb7f` | `371f99d5ae246b43ad6f2f764bb898a2148be29d8d62896c942af5736585fb7f` |
| `tests/test_pcba_design.py` | `ab45b2104feef5318c101193ae86f047962e0372f41dbbefbc4eb7daca288ff6` | `7798a91c507b46e550f331137133c60c6e5a82ff77563b54e96ead88dfdd262b` |

## Decision

The batch does not pass review until the three findings are corrected in one frozen replacement. The accepted neutral scope stays closed. This review does not accept the full B10 package, which remains unimplemented.

This report changes no product file or shared contract.
