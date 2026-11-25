# B9/B10 remaining execution review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b9-b10-remaining-execution-claude.md`. The accepted neutral
design stays closed. This review lists missing concrete interfaces only. It proposes no
redesign and no research.

## 1. Result

The note is a sound plan. Section 7, 9 and 14 coverage is mostly complete. Six concrete
interfaces are missing. An implementer must invent them without the list below.

## 2. Missing concrete interfaces

1. Alternate selection trigger (interface section 7). The note sets `selected_alternate`
   but never states what selects the alternate. It can be a board record field, a variant
   field, a CLI option, or an explicit map selector. Without this decision,
   `selected_alternate` is always empty.
2. Alternate map shape (interface section 7). State the exact shape of the `alternates`
   key. State whether it is a top-level list, a per-reference list, or an object, and each
   value type. The note says only that a schema change is necessary.
3. Alternate identity in the row and the BOM (interface section 7). State whether a
   selected alternate replaces the row `manufacturer`, `mpn`, `part_path` and
   `part_sha256`, or adds `selected_alternate` next to the primary values. State whether the
   BOM group key uses the alternate. The demand rule in the note needs this to prevent
   double counting.
4. Sierra `hand_installed_bom` policy (interface section 9.1). The note omits the supplier
   profile field `extensions.pcba.hand_installed_bom` with `include_in_bom` or
   `exclude_from_bom`, the missing or unknown policy that blocks qualification, and the BOM
   row treatment. Add it to the Sierra artifacts.
5. Manifest roles and package paths (interface sections 9 and 10). The note lists the
   artifacts and says the manifest binds them by hash, but it does not name the manifest
   role or the package-relative path for each artifact. The interface names only
   `fabrication_drawing`, `report` and `image`. Define the role and path for the BOM
   workbook, the XY draft, the drill files, the assembly drawing, the test record and the
   neutral dataset.
6. Staged publication and final freshness ownership (interface section 14). The note lists
   the owned modules but not the module that stages the package, validates the staged set,
   publishes with `publish_dir`, and rehashes every input for final freshness. The
   interface gives a six-step rule. Name the module and the call order.

## 3. Smaller concrete gaps

- Evidence file naming and location (interface section 10). `report.py` writes one evidence
  file for each check. The name pattern and the package directory are not stated.
- Check artifact binding (interface section 10). State the artifact for each check. The
  `asm.placement_rotation` artifact is the neutral placement dataset.

## 4. Confirmed complete

- The alternate evidence checks name the compared part fields.
- The owned module list matches interface section 14.
- The inherited gate names the eight bare checks and the five assembly checks.
- The artifact list matches interface section 9, and it keeps each placement convention
  `unconfirmed`.
- The exit states are `draft`, `unqualified` and `qualified`, with no success claim.
- `export_rotation_deg` stays in the separate comparison evidence. It does not enter the
  neutral rows. The accepted neutral design stays closed.

## 5. Limits

This review covers concrete interfaces only. It does not review the implementation, the
Sierra format details, or the B10 qualification logic. The shared snippet route stays an
integration item.
