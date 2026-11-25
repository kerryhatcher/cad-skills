# B10 integrity replacement

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The Claude author reached the provider usage limit. The lead completed this correction.
The assigned models and reviewer roles stay unchanged.

This replacement implements `b10-final-integrity-correction-root.md` and the shared BOM role correction.
It supersedes the 99-file completion correction for the files in the new manifest.
The previous records stay as history. The lead did not commit or push these changes.

## Final publication gate

The package runs the full copied validator before the final comparison.
The final comparison covers the manifest bytes, output paths, hashes, byte counts, file count and links.
The package compares the captured input hashes at this boundary too.
No staged file changes after the final comparison.
The CLI does not expose `_hooks`. The regression tests use this private argument.

The controlled cases change copper, the manifest, an extra file, a missing file, a symbolic link and a hard link after validation.
Each case refuses publication and preserves the earlier package.
The source-drift test remains in the suite.

## Drill reference

The owned `board_inventory_worker.py` runs with pcbnew in the locked local image.
It reads the captured board bytes and measures all drilled pads and through vias.
The inventory retains global coordinates, diameter, plating and multiplicity.
An unsupported drilled object gives a named refusal before publication.

The drill comparison uses this measured inventory. It does not substitute the interface hole list for the board inventory.
The report binds the board bytes, worker bytes and image identity.
Tests cover an empty interface, a rotated footprint, a missing pad hole, a missing via hole and a duplicate drill record.
An oval drill gives the named refusal `drill.unsupported`.

## Sierra compatibility

Both commands read `manufacturing/supplier.yaml`.
They compare the profile `content_sha256` with `board.supplier.profile_sha256`.
The input bindings retain the full file hash separately.
The Sierra status record now includes these bindings.
The owned fixture uses the standard supplier path. It no longer contains `supplier-profile.yaml`.
The tests retain profile mismatch and final freshness refusals.

## Assembly evidence

The independent BOM comparison applies the captured `hand_installed_bom` policy.
It compares manufacturer, MPN, references, quantity and DNI.
The exclusion policy does not remove a hand-installed part from neutral data or test instructions.

The shared validator, its PCBA copy, `report.py` and interface section 14 name `supplier_profile` for `asm.bom_consistent`.
The validator hash is `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41`.
The shared negative test refuses evidence without this role. No schema changed.

The test-record comparison examines the selected variant and the captured hand-install instruction.
It refuses duplicate IDs before it builds the item dictionary.
Tests cover a different variant, changed instruction, missing instruction and duplicate ID.
The existing board-limit and physical-result comparisons remain.

## Results and limits

The retained standard package passes the full validator with exit 0 and no finding.
The package remains `unqualified`. Ten checks pass.
`design.drc` and `asm.stock_dated` fail on the fixture. `fab.supplier_rules` remains `unconfirmed`.
All physical test items remain `not measured`.

The focused run and copy comparison are in `b10-final-integrity-evidence/`.
The final freeze manifest binds these logs and all consumed skill and fixture files.
The prior package bytes remain in the local historical archive `b10-prior-retained-package.tar`.

The release team still owns the `pcba-design` entry in `tests/snippet_envs.json`.
The known exact-set failure remains until integration adds the skill and its entry together.
No provider evaluation ran. Supplier conventions remain unconfirmed.
KiCad export timestamps can differ between runs. Each package binds its own output bytes.

## Frozen replacement

The final focused run passes 105 of 105 tests with exit 0.
The copy comparison passes 15 of 15 files.
The manifest is `b10-final-integrity-replacement-root.sha256`.
Both reviewers must use these frozen bytes. The lead stops product edits during review.
