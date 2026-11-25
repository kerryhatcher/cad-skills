# Codex review: B10 completion correction

Date: 2026-11-15 UTC. Reviewer: codex-pcba-dev. Branch: `work/pcba`.

All 99 SHA-256 entries in `b10-completion-correction-claude.md` match disk. I reviewed the batch against the correction root and interface section 14. I did not run tests. The author reports 97 focused tests passed and a retained full-validator exit code of 0.

## Review result

The batch corrects the six earlier findings. The full validator, required input capture, toolchain lock, export inventory, executable checks, and variant drawing now operate. The package remains `unqualified`, and the test record makes no physical pass claim.

These defects remain in the frozen bytes.

1. **Staged outputs can change after validation.** `package.py` runs `_verify_staged` before `build_report`. It then runs the `after_validate` hook and checks only captured inputs. The root probe changed `fab/gerber/board-B_Cu.gbl` after validation. The package returned success and published the changed bytes. The manifest binds `61e7a8c0522e5dc3fb4e990a1ec058e9c28ca37fbc359a6325bb902a84ac2494`. The published file has hash `8cb13e4a7c1b84ee39f5253e9bdde1f84c8eea6efeb4d63514abcb5f8bc0a535`. Recheck the manifest and all staged files, counts, and links after validation, immediately before rename. Run the input freshness check at that point too.

2. **The drill check does not establish a complete board inventory.** `package.py` gives `interface["holes"]` to `drill_split`. The board interface schema accepts an empty `holes` list. The copied validator checks the interface hash, revision, dimensions, and hole locations. It does not compare the hole list with drilled pads and vias in the captured board. Thus the check can pass against an incomplete interface list. It proves agreement with that list, not equivalence with all board holes. Derive the inventory from the captured board, or prove that the interface lists every drilled pad and via.

3. **The Sierra command uses the old profile path and hash rule.** The lead defines `board.supplier.profile_sha256` as the canonical profile content hash. `package.py` follows that rule. `build_sierra` still reads `supplier-profile.yaml` and compares the hash of its full file bytes with that field. The standard layout stores the profile at `manufacturing/supplier.yaml`. The Sierra command therefore refuses with `supplier.profile_missing` on that layout. If the old path exists, a canonical profile hash differs from its full file hash. The Sierra path and interface section 2a need the same path and hash rule.

4. **The BOM check rejects a valid exclusion policy and misses manufacturer changes.** `sierra.bom_table` omits hand-installed rows when the policy is `exclude_from_bom`. `checks_asm.bom_consistent` still expects every neutral group, so it reports a mismatch for valid output under that policy. The check also omits the manufacturer column from its comparison. A wrong manufacturer can pass when the MPN, references, quantity, and DNI value match.

5. **The test-record check does not compare the selected variant or hand-install instructions.** `checks_asm.test_record` checks item IDs, statuses, and electrical limit values. It does not check `record["variant"]`. It does not compare each hand-install instruction with the selected variant record. An incorrect variant or instruction can pass `asm.test_record`.

The lead confirmed the first two defects with the root probe and the frozen source. The profile path and hash issue also appears in the author record and the standard fixture. The remaining findings follow from the check inputs and comparisons in the frozen code.

This report changes no product file or shared contract. The accepted neutral and Sierra scopes stay closed, except for the required Sierra compatibility correction.
