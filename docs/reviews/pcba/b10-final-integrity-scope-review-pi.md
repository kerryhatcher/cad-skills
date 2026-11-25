# B10 final integrity scope review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b10-final-integrity-correction-root.md` and Codex's completed
review. This is a scope review before the correction. No product file changed.

## 1. Result

The combined correction covers my D1 to D3, the root findings, and Codex's BOM and
test-record findings. One concrete conflict with the accepted interface remains.

## 2. Concrete conflict

The BOM policy role is not bound.

Interface section 14, `contracts/validate.py` `CHECK_INPUT_ROLES`, and
`skills/pcba-design/scripts/report.py` list the `asm.bom_consistent` mandatory roles as
`parts`, `variants` and `board_record`.

The correction releases this: "Give the BOM checker the captured supplier policy. Under
`exclude_from_bom`, omit hand-installed references from its expected supplier rows."

The supplier policy is `supplier_profile.extensions.pcba.hand_installed_bom`. No listed
role carries it. If the check reads the captured supplier profile, the evidence record must
bind that profile, and the role must be mandatory. As written, the check would read an
unbound input, and a package could omit the profile from the evidence and still pass the
mandatory-role check.

Fix: add `supplier_profile` to `asm.bom_consistent` in the interface section 14 table, the
shared `CHECK_INPUT_ROLES` and the skill's `report.py` table. This is a shared table change,
not a schema change. Alternatively, name one bound artifact that carries the policy, and
state that the check reads it. Do not read the live project.

## 3. No other conflict

- D1 and D2 match the accepted interface. D1 adds the final comparison after validation;
  D2 replaces the interface-only inventory with the captured board inventory. The
  `fab.drill_split` role `board_interface` can stay for the separate interface comparison.
- D3 changes the Sierra profile path and hash rule. The lead authorizes the section 2a and
  documentation update.
- The test-record check keeps the roles `board`, `parts` and `variants`. The variant and
  hand-install instruction come from `variants`. The duplicate item ID refusal adds no
  interface.
- The manufacturer comparison uses `parts`. The role is present.

## 4. Hold

I hold for the coherent replacement and will review the same stable bytes as Codex.