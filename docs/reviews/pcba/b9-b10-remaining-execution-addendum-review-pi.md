# B9/B10 remaining execution addendum review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: section 6 of `docs/reviews/pcba/b9-b10-remaining-execution-claude.md`. The
accepted neutral design stays closed. This review lists concrete conflicts and missing
interfaces only.

## 1. Result

Section 6 fixes the six interfaces and the two smaller gaps from my earlier review. One
internal conflict and four smaller concrete gaps remain.

## 2. Conflict

C1. The value of `selected_alternate`. Section 1, line 10, says the field holds the
resolved project-relative path of the alternate part file. Section 6, item 3, says the
field holds the alternate name. Decide one value and correct the other sentence. The name
is stable when a part path changes. The path is what the row already uses for
`part_path`. Do not keep both.

## 3. Missing concrete interfaces

G1. Package destination and prior packages. Item 6, step 7, publishes to
`out/pcba/package/`. `project_io.publish_dir` refuses an existing destination
(`project_io.py` lines 228 and 229). Interface section 14 says "Preserve prior packages."
Define the destination for a second package, for example a revision or token in the path,
or a move of the prior package. Also define the finding and status when the destination
exists.

G2. The post-rename failure. Item 6 names the status and `output_replaced` true, but not
the finding code. The post-replace case named its finding `output.replaced_then_failed`.
Name the post-rename finding in the same way. Also state whether `output_replaced` means
"the output path is in place" for a new package. The word "replaced" fits a file
replacement, not a new package.

G3. The evidence path convention. Item 5 says the role `evidence` has path
`evidence/<check-id>.json`. Item 8 binds `evidence/supplier-profile-evidence.bin`. State
whether the profile copy is the only non-JSON evidence artifact and give its rule.

G4. The owned code list. Interface section 14 names `export.py`, `report.py`,
`checks_*.py` and `project_io.py`. Section 6 adds `package.py`. Add `package.py` to the
interface owned-code list, or state that it is a new module. This is bookkeeping, not a
shared schema change.

## 4. Confirmed correct

- Every output role in item 5 is in the manifest output role enum. No shared schema
  expansion is necessary.
- The alternates map shape, the selection trigger, the row identity, the
  `hand_installed_bom` policy, the per-check artifact table and the staged publication
  order are concrete.
- The neutral design stays closed. `export_rotation_deg` stays in the separate comparison
  evidence.

## 5. Limits

This review covers concrete interfaces only. It does not review the implementation or the
Sierra format details.