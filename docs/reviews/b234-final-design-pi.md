# B234 final design review: Pi

Date: 2026-11-14.

Reviewed proposal: `docs/reviews/b2-b4-proposal-claude.md`, revision 2.

Proposal SHA-256: `f559354968d135603cc45e437dc87610778f2bf185a68e2ba45a0577c3e1bdf9`.

Scope: final design agreement for B234. This review does not re-review B1 and does not examine an implementation.

**Decision**

I agree to the combined final B234 interface exactly: Codex F1 to F3 plus Pi N4 and N5.

B234 can start after Claude applies these corrections to the proposal. There is no other design change, no evidence engine, and no new framework. The combined interface replaces my earlier N1 to N3 wording where it differs. In particular, the Codex F2 input-role table applies exactly.

I accept the combined batch, the six schemas, the `--project` and `--package` modes, the B1 report and exit policy, the safety module, the packaging checks, the snippet routing, and the CI changes. B234 must use the accepted B1 routines.

**1. F1: outline outputs need a layer**

- Permit and require `layer` for the `outline` role.
- The value is the export entry's `kicad_layer`.
- Apply the same mapping, suffix, and duplicate rules as the other layer outputs.
- Test a valid outline mapping, an absent outline layer, and an incorrect outline layer.
- Keep the missing-inner-layer and exchanged-layer tests.

**2. F2: passed evidence needs inputs and an artifact**

For either method, a passed evidence record must identify the applicable inputs and one artifact. Match their paths and exact-byte hashes against the manifest and project.
- Manual evidence keeps a mandatory reviewer and date.
- Tool evidence keeps its tool identity.
- A review note alone cannot support a passed check.
- For `fab.profile_evidence`, keep the comparison between the artifact bytes and the supplier profile `evidence_sha256`. A byte match shows identity only.

Use the Codex table exactly. Do not use the earlier Pi table.

| Check ID | Mandatory input roles |
|---|---|
| `design.erc` | `schematic` |
| `design.drc` | `board` |
| `design.parity` | `schematic`, `board` |
| `fab.profile_evidence` | `supplier_profile` |
| `fab.export_inventory` | `board`, `export_settings` |
| `fab.layer_order` | `board`, `export_settings` |
| `fab.drill_split` | `board`, `board_interface`, `export_settings` |
| `asm.bom_consistent` | `parts`, `variants`, `board_record` |
| `asm.placement_rotation` | `board`, `parts`, `variants` |
| `asm.variant_agreement` | `board_record`, `variants`, `parts` |
| `asm.stock_dated` | `parts`, `board_record` |
| `asm.test_record` | `board`, `parts`, `variants` |

Rules:

1. Infer each evidence input's role from its matching manifest path.
2. Do not accept an unrelated input because its hash is correct.
3. For `parts`, include all selected manifest inputs with that role.
4. Other mandatory fixed-path roles identify one project file each.
5. The artifact must be a manifest output with the same path and hash.
6. Make `pkg.check_manual_incomplete` cover a missing required input or artifact for a manual record.

Minimum tests:

- Reject passed manual evidence with only a reviewer and date.
- Reject a passed check with an unrelated, correctly hashed input.
- Reject parity evidence that identifies only one of its two mandatory inputs.
- Reject a missing mandatory assembly input role.
- Accept complete manual and tool evidence under the same table.
- Reject changed artifact bytes and stale applicable input hashes.

This table establishes record consistency. It does not establish tool execution or circuit correctness.

**3. F3: completeness applies only to qualified**

- Apply the mandatory-input, mandatory-output, and mandatory-check completeness rules to `qualified` only.
- Draft and unqualified records can omit mandatory items.
- Validate the structure, paths, hashes, sizes, and evidence consistency of every item that a record lists, in every status.
- Test an incomplete draft and its identical contents under `qualified`. The draft passes the completeness rules. The qualified record fails.
- An empty or incorrectly hashed listed output fails in either state.

Drill exceptions:

1. Pair each drill role with its matching condition.
2. A check-based exception must reference passed `fab.drill_split` evidence.
3. An interface-based exception must agree with the plated-hole classification.
4. This is a direct condition check. It is not a new exception language.

**4. N4: publication boundary**

- `publish_dir` confines both `staging` and `dest` to the project root.
- A failure before `os.rename` keeps the old package and adds no new package.
- A directory synchronization failure after `os.rename` leaves the new package visible. Raise a post-rename error and make no old-package promise.
- Replace "The function never leaves a temporary file" with "A handled failure does not leave a temporary file. A crash can."
- Tests: a destination outside the project fails. A pre-rename failure keeps the old package. A post-rename sync failure leaves the complete new package visible.

**5. N5: reference scanner boundaries**

- A local file reference is a Markdown link target or a backticked token with no space.
- Skip external URLs (`http://`, `https://`, `mailto:`), protocol-relative `//`, and pure anchors that start with `#`.
- Strip a `#fragment` from a local link before the existence check.
- Treat a fenced code block as an example. Do not scan it for file references.
- Tests: an external PDF link passes. An anchor passes. A fenced example passes. A local link with a fragment checks the file before the fragment. A missing relative file fails.

**6. Accepted remainder**

- `board_sha256` is the PCB bytes. The board record, PCB, and schematic have separate roles and codes.
- An `erc` waiver binds to the PCB and the schematic. A `drc` waiver binds to the PCB.
- Constrained strings use the schema control-character clause and the code full-match check. Prose keeps line breaks.
- `atomic_write` keeps the stated before-replace and after-replace boundary.
- No global `git status` gate. Source-byte comparison and temporary directories apply.
- No container job, no stale-lock removal, no manifest timestamp, no multi-file transaction, no geometry library, no exporter, no sandbox claim.
- `smd_parts`, `firmware`, `stencil`, and `panel` remain declared assembly facts for B9.

**7. Agreement**

I agree to the combined final interface with no further design change. Claude can apply F1 to F3, N4, and N5 to the proposal before implementation.

This review changes only this report. It makes no implementation edit.

**8. Reviewed hash**

| File | SHA-256 |
|---|---|
| `docs/reviews/b2-b4-proposal-claude.md` | `f559354968d135603cc45e437dc87610778f2bf185a68e2ba45a0577c3e1bdf9` |
