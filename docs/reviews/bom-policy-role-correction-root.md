# BOM policy input role

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The independent BOM comparison consumes `supplier_profile.extensions.pcba.hand_installed_bom`.
Its evidence must bind that input. The lead added `supplier_profile` to `CHECK_INPUT_ROLES["asm.bom_consistent"]`.
No schema changed. No bare-board check changed.

The new validator SHA-256 is `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41`.
The source and byte copies in the main and PCBA worktrees match. The PCBA copy manifest has the new hash.
The shared regression removes the profile from BOM evidence and expects `pkg.check_input_role_missing`.

Validation:

- `uv run tests/test_pcb_tools.py`: 59 of 59 passed, exit 0.
- `uv run tests/test_skill_packages.py copy`: 2 of 2 passed, exit 0.

The PCBA author must update `report.py` and the interface table in the combined correction.
The final integration must use these same source and copy bytes.
Historical worktrees and accepted freeze records retain their old hashes until an explicit integration update.
