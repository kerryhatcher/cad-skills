# B10 completion correction: frozen batch (Claude)

Date: 2026-11-15 UTC. Author: claude-pcba-dev (w1P:p7). Branch `work/pcba`. Model `claude-haiku-5-5`. Worktree `/mnt/storage/projects/cad-skills-worktrees/pcba`.

Governing records:

- `docs/reviews/pcba/b10-completion-correction-root.md`: the released combined correction, with eight items.
- `docs/reviews/pcba/b10-completion-scope-root.md`: the six scope points.
- `docs/reviews/pcba/b10-completion-review-pi.md` and `docs/reviews/pcba/codex-review-b10-completion.md`: the two reviews.
- Section 14 of `docs/reviews/b9-b10-interface-claude.md`: the accepted inherited gate.

This record supersedes `docs/reviews/pcba/b10-completion-claude.md` for the bytes listed below. The earlier record stays unchanged. No commit has been made. No push has been made. No provider call has been made.

## Result

All eight items are implemented in one batch. The focused suite passes 97 of 97 tests. The package step writes a complete package for the standard-layout fixture. The copied validator passes that package with exit 0 and no finding. The package status is `unqualified`.

The 13 checks of the package have these statuses on the standard fixture:

| Status | Checks |
|---|---|
| `pass` (10) | `design.erc`, `design.parity`, `fab.profile_evidence`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split`, `asm.bom_consistent`, `asm.placement_rotation`, `asm.variant_agreement`, `asm.test_record` |
| `fail` (2) | `design.drc`, `asm.stock_dated` |
| `unconfirmed` (1) | `fab.supplier_rules` |

No physical result is claimed. The test record states `not measured` for each step.

## Behaviour by item

### 1. Records and validation

- The package captures each mandatory record once, at the fixed paths of the copied validator. The paths are listed in `skills/pcba-design/SKILL.md`.
- A missing mandatory record refuses the package with `package.input_missing`. No package is written, so no package can fail its own listed-evidence checks.
- The package runs the copied validator on the project and on the staged package before publication. A validator finding refuses the package.
- The manifest binds the board supplier block exactly as the board record states it.

### 2. ERC, parity and profile evidence

- `design.erc` runs `kicad-cli sch erc` in the locked image. It counts the violations of every severity. Zero violations pass.
- `design.parity` compares the KiCad XML netlist of the schematic with the net of each board pad. Each difference is one reason.
- `fab.profile_evidence` compares the hash of the retained supplier evidence with `evidence_sha256` of the profile. Pending appears only when no evidence file is captured.

### 3. Exports and drill

- `fab.export_inventory` derives the expected file names from the captured export settings. It reports missing files and extra files as separate reasons.
- `fab.layer_order` finds each layer by its FileFunction line in the file content. The file name is not used.
- `fab.drill_split` reads each inch Excellon file. It compares each hole with the board interface inventory in position, diameter, plating and count. KiCad writes the Excellon Y axis with the opposite sign to the board Y axis. The check uses this sign, which was measured on the fixture. The reader also restores the trailing zeros that KiCad suppresses.

### 4. Toolchain and settings

- The lock names the image and its identity. The identity is `sha256:` followed by the local image ID.
- The package reads the local image ID with `podman image inspect`. It never pulls an image. A different ID refuses with `toolchain.image_mismatch`.
- The package reads the KiCad version of the locked image. A different version refuses with `toolchain.version_mismatch`.
- Each KiCad run uses the identity, with `--pull=never` and no network. The export arguments come from the captured export settings.

### 5. Staged validation and freshness

The order of the final steps is:

1. Write the staged files.
2. Check the staged bytes and the file count.
3. Run the copied validator on the project and on the staged package.
4. Check the inputs again.
5. Publish the staged directory once.

Tests cover three cases. Drift during the staged writes refuses through the validator, and no package is published. Drift before publication refuses with `input.changed`. A changed staged file refuses with `package.hash_mismatch`.

### 6. Assembly evidence

- `asm.test_record` compares the record steps with the board limits and the hand-installed references of the selected variant. An empty step list fails.
- The assembly drawing is an SVG file. The skill generates it from the neutral rows and the captured board outline. It marks each `dnp` reference with a cross and the text `DNP`. It marks each hand-installed reference with the text `HAND`.
- Physical measurements stay `not measured`. Supplier conventions stay `unconfirmed`.

### 7. Stock claim

The earlier record `docs/reviews/pcba/b10-completion-claude.md` states that the other checks pass. That statement is false for the fixture. The check `asm.stock_dated` fails. The LED part `EX-LED-0603-G` has stock 10. The base variant needs 20, which is 4 LEDs for 5 boards. Its stock date is 75 days old, and the policy allows 30 days. This record replaces the earlier statement. Two checks fail on the standard fixture: `design.drc` and `asm.stock_dated`.

### 8. Fixture, retained result and negative cases

- The standard-layout fixture is in `tests/fixtures/pcba-design/standard-project`. It holds a board, a schematic, the manufacturing records, the board interface and the toolchain lock.
- The retained package is in `tests/fixtures/pcba-design/retained/pkg-standard`. Its full validator result is in `tests/fixtures/pcba-design/retained/validator-result.json`. The validator exits 0 with no finding.
- A test refuses a qualified manifest with open checks, and the validator names `pkg.false_qualification`.
- Independent negative cases:
  - `design.erc`: a seeded unconnected label fails.
  - `design.drc`: a seeded overlap of two pads on different nets fails.
  - `design.parity`: a seeded pad on another net fails.
  - `fab.profile_evidence`: a changed byte fails, and absent evidence is pending.
  - `fab.export_inventory`: missing and extra files fail.
  - `fab.layer_order`: a renamed file with the right content passes, and wrong content fails.
  - `fab.drill_split`: suppressed trailing zeros, negative coordinates, a duplicate hole and a plating difference are tested.
  - `fab.supplier_rules`: an open plane interpretation or placement convention never passes.
  - `asm.test_record`: an empty step list fails, and a missing hand-install step fails.
- A refused package leaves earlier packages unchanged. The test `test_existing_package_id_refused_and_kept` checks this case.

## Decisions for the lead

1. **Profile hash rule.** The copied validator requires `board.supplier.profile_sha256` to equal the profile `content_sha256`. Interface section 2a and the Sierra path bind the file bytes. The package follows the validator, and it binds the file bytes as a manifest input. The Sierra path is unchanged. The lead must choose one rule, and then update section 2a and the Sierra path together.
2. **Routing entry.** The file `tests/snippet_envs.json` has no `pcba-design` entry. `tests/test_snippets.py` reports `snippet.unrouted`, and `tests/test_skill_packages.py` reports `test_snippet_routing`. The routing table is release-owned, so this batch does not change it. The same gap existed before this batch.
3. **Routing of the fixture.** The fixture board is placed but not routed. The DRC reports 15 violations and 16 unconnected items. Some violations are warnings about footprint copies. The check fails, which is the true state of the fixture.
4. **Reproducibility.** KiCad writes creation dates into the Gerber, drill and job files. Two runs give different bytes. Each package records the bytes of its own run through hashes. The record does not claim byte equality between runs.
5. **Pending and refusal.** Item 2 allows pending only for an absent input. A missing mandatory record refuses the package instead, which follows item 1. Pending appears only for the retained supplier evidence.
6. **Drawing.** The assembly drawing is now an SVG file that the skill generates. The KiCad PDF is no longer in the package.
7. **Excellon sign.** The sign of the Excellon Y axis is measured on the standard fixture. The measured transform in interface section 3 covers only the pos export. The lead must confirm that the drill rule belongs in section 14.

## Commands and exit codes

| Command | Exit | Result |
|---|---:|---|
| `uv run tests/test_pcba_design.py` | 0 | 97 passed, 0 failed |
| `uv run skills/pcba-design/scripts/pcba.py package --project COPY --board kicad/board.kicad_pcb --variant base --as-of 2026-11-15 --package-id pkg-standard` | 0 | written; validation exit 0 |
| `uv run skills/pcba-design/scripts/pcba.py check --project tests/fixtures/pcba-design/standard-project --package tests/fixtures/pcba-design/retained/pkg-standard` | 0 | no finding |
| `uv run tests/test_skill_packages.py` | 1 | 7 of 8 passed. Failure: `test_snippet_routing` (release-owned routing entry) |
| `uv run tests/test_snippets.py` | 1 | `pcba-design` has no routing entry (release-owned) |
| `uv run tests/test_project_io.py` | 0 | 11 of 11 passed |
| `uv run tests/test_pcb_tools.py` | 0 | 59 of 59 passed |
| `uv run tests/test_print_tools.py` | 0 | 6 of 6 passed |

The copies check of the skill package test passes. The copied validator, `sexp.py`, `project_io.py` and `COPY_SHA256.txt` are unchanged.

## Pending compatibility correction

Status: pending. Not edited during review. For one combined release after both reviews.

- The field `board.supplier.profile_sha256` follows the copied validator's canonical content hash (`content_sha256`). The package follows this meaning.
- The input bindings still record the full file hash of the profile in the manifest inputs. These are different fields with different meanings.
- The Sierra command still binds the file hash in `board.supplier.profile_sha256`. It must follow the same board-field meaning as the package. Change it in the combined release, with its tests.
- Missing mandatory project records refuse, as implemented. A truthful `unqualified` package is permitted after full structural validation.

## Open finding: staged bytes after validation

Status: open. Reported by the lead from the root probe `docs/reviews/pcba/b10-after-validation-probe-root.py` and `docs/reviews/pcba/b10-after-validation-probe-root.json`. Product files are not changed while both combined reviews are open.

- The probe changes the staged file `fab/gerber/board-B_Cu.gbl` in the `after_validate` hook. The package returns success and publishes. The bound hash is `61e7a8c0522e5dc3fb4e990a1ec058e9c28ca37fbc359a6325bb902a84ac2494`. The published hash is `8cb13e4a7c1b84ee39f5253e9bdde1f84c8eea6efeb4d63514abcb5f8bc0a535`.
- Cause, confirmed in `skills/pcba-design/scripts/package.py`: the staged byte gate `_verify_staged` runs before the validator. After the validator, the code runs only `snap.check_unchanged()` for captured inputs, then `publish_dir`. No staged check runs between validation and publication.
- Required later correction: compare the validated manifest bytes and all staged outputs, counts and links after validation and immediately before rename. Keep the input freshness check at the same point.

## Open findings from the Pi review

Source: `docs/reviews/pcba/b10-completion-correction-review-pi.md`, dated 2026-11-15 04:21 UTC. Status: open. Product files stay unchanged while both combined reviews are open.

- **D1, staged bytes after validation.** Confirmed. See the open finding above. The fix compares the validated manifest bytes and every staged output path, hash, size, count and link immediately before `publish_dir`, with input freshness. The after-stage and after-validate hooks become test-only.
- **D2, interface completeness.** Confirmed. `checks_fab.drill_split` receives the interface holes from `mechanical/board-interface.json`. No code measures the board pads and vias against the interface. The check therefore shows drill-versus-interface agreement, not drill-versus-board equivalence. The later correction must add a board inventory check from the captured board bytes.
- **D3, Sierra profile field.** Confirmed in `skills/pcba-design/scripts/pcba.py`. The Sierra path reads `supplier-profile.yaml`. It compares the full file hash with `board.supplier.profile_sha256`. That field now means the content hash, so the Sierra path refuses with `supplier.profile_mismatch`. At the standard layout it refuses with `supplier.profile_missing`. Section 2a and the Sierra path must change together, in the combined release.

## Limits

- No physical board is built or tested. No supplier is contacted. The supplier conventions stay unconfirmed.
- The fixture is an example. Its supplier text is fixture data, and it is not a supplier statement.
- The drill and ERC checks depend on the image `localhost/cad-skills-pcb:b6` with identity `sha256:b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`.

## Files and SHA-256

This record is not hashed by itself. Each row is one consumed or changed file of the batch. The 42 files under `retained` are the package and its validator result. The bytecode caches are excluded.

| Path | SHA-256 |
|---|---|
| `skills/pcba-design/contracts/alternate-approval.schema.json` | `dc598d5666f4a2f6c7a9d62d9d09579310500e5d5dfc534b66f4eb518540a66f` |
| `skills/pcba-design/contracts/part-map-1.1.schema.json` | `890a36acfb696c0823b370a33661ea9d7476578433513bf79c5b0007060217ce` |
| `skills/pcba-design/contracts/part-map.schema.json` | `d3c5a6335faf0206461b38c6e9da52c574a9bee354eb63acde3a924fd5a20ed2` |
| `skills/pcba-design/contracts/README.md` | `7c3454f4715cb77925e8471d2f2308dc408af30238e0abd8cc7d61db5a874915` |
| `skills/pcba-design/contracts/schemas/board-interface.schema.json` | `8fd8b0e4d15d8ceb29de85245f3f5e3f378b56ed30ac08f9f78cb0cb5a547b9f` |
| `skills/pcba-design/contracts/schemas/board.schema.json` | `9d0b1702bfed18d50485f6ccd59d2da9eeb14c13e4a3246ccb04cb559178ad97` |
| `skills/pcba-design/contracts/schemas/evidence.schema.json` | `eb631648f9862ff31c927cb639df9b6ffd441f4862d96b068966fcf8ec19001b` |
| `skills/pcba-design/contracts/schemas/export-settings.schema.json` | `911043d2779333071517be168015ca6cbcb4a3a531220e3fcf8ce89a5f413116` |
| `skills/pcba-design/contracts/schemas/manifest.schema.json` | `096c7aa85eab334d8e5e48d0a7b35e9d66b15c9468c3916185064895a58df790` |
| `skills/pcba-design/contracts/schemas/part.schema.json` | `50e36d4941fe4db3533c0a69f93da3a1c812d5143f569ccc729947daf060e908` |
| `skills/pcba-design/contracts/schemas/registry.json` | `5ae88c4127e7a51829c89db6a321cfc5adc0b7d9718c9b5a358f75a83285e5fd` |
| `skills/pcba-design/contracts/schemas/supplier-profile.schema.json` | `29489d3a14d5fd7403ff016200375669ffdd78aae42c24ace821fbf34e9c98ea` |
| `skills/pcba-design/contracts/schemas/toolchain-lock.schema.json` | `3911e6fb457798dbd5d621d41be470e93bcf9ab3387980ec6bf4472cc5a73e0c` |
| `skills/pcba-design/contracts/schemas/variants.schema.json` | `23fd221c65924bd777f94131a0b1153f1423e06fa4a88f6435d1fb5264106ae7` |
| `skills/pcba-design/contracts/schemas/waivers.schema.json` | `2e3764fb32fda0766ad489d968d637ad7e0f31e7173e7902367278f906e5d928` |
| `skills/pcba-design/contracts/validate.py` | `102e252c211bab973adc4e5ae97c051ad4b35dfb59e53916d8b8099144731d9e` |
| `skills/pcba-design/COPY_SHA256.txt` | `0ea6a004fb9577587e2364e3f2d365df8d2387cbfd4a4232b048c0b058881c6c` |
| `skills/pcba-design/scripts/checks_asm.py` | `826dabdda919f6261a9bb45830b8c7ecd37a46ae4c1efc53845036964ea39a10` |
| `skills/pcba-design/scripts/checks_design.py` | `b5a6de7c684d8973cd1063020dc18d36dd7f8cfc6cb04162d920036a348bf2b3` |
| `skills/pcba-design/scripts/checks_fab.py` | `57246c9db87707080e977932af771752eea6719911cfc2b31a09803fa973cbf0` |
| `skills/pcba-design/scripts/drawing.py` | `91db2cfa72211958d4a1f98e03f337abaada724491c8a6b2e7420f1b37a11c7d` |
| `skills/pcba-design/scripts/export.py` | `bcb32c16e336693a50d3203e4c49f22f54e6681bfdf75491134101430aae5504` |
| `skills/pcba-design/scripts/package.py` | `c3d768f97babdeba952a619ba8935fd77ef5766bfe510ac80e9286cd46f53a97` |
| `skills/pcba-design/scripts/pcba.py` | `a0a5290b0e3132e32e377a4d67eb6f1587a8b326ddd1a59546915dafcab2fc8f` |
| `skills/pcba-design/scripts/project_io.py` | `f4f2fb06ddb14805da9ea80d06bb4ab8e30c17102529746a7015bf15ed6de9e3` |
| `skills/pcba-design/scripts/report.py` | `6b38efc4cce801df1b26586cc52de6ace133b7d6a9dfc4903da7fad366948543` |
| `skills/pcba-design/scripts/sexp.py` | `2dfc36f2bc4141c870de2eb4edb2bc83fd692dedf7c31241aa084f3927e8669a` |
| `skills/pcba-design/scripts/sierra.py` | `f4d8ef1a3b5e832ec0743501cce55947fb019d5ced77576537dcaaa276f0d379` |
| `skills/pcba-design/SKILL.md` | `49f9019712efb0da8632bfbdd85a10b2ccf30965fccf376ae52e1a8136f07cb2` |
| `tests/fixtures/pcba-design/project/board.kicad_pcb` | `efa69ee5fb853347ccb336b5049d67d9676602ce07cd9db4cd4bb114b8e81198` |
| `tests/fixtures/pcba-design/project/board.yaml` | `3137bf4b40e21360c15ad36776f20f9dfda570649197f38a3901ca531019ab4f` |
| `tests/fixtures/pcba-design/project/components/cap-100n.yaml` | `6d92bae75baf73304a9e5ed0d5dca93ab58ccc2e64fb9a8c7925fc4040ff593e` |
| `tests/fixtures/pcba-design/project/components/header-2.yaml` | `2546128f2893a074f06cb31978f58f3897d41c8c43ca5d4c3d10722b610ed2e9` |
| `tests/fixtures/pcba-design/project/components/led-green.yaml` | `449962943f98cd6a3db980d3274e92a93a60000510bcde89c0f997f7414c7faa` |
| `tests/fixtures/pcba-design/project/components/parts-map.yaml` | `0d26cc93458dd2d743f24d12901e8e92da04d36175e551c82b60066404144e08` |
| `tests/fixtures/pcba-design/project/components/resistor-10k.yaml` | `11bef0c36e83db32be23df9e0db5b8465d8e18c4b490ab70c8e6d4c1c7f308d5` |
| `tests/fixtures/pcba-design/project/components/testpoint.yaml` | `3c09b1bace014af514a78adc5a6d869403b1bda04b7410930670c35e29f3a81a` |
| `tests/fixtures/pcba-design/project/supplier-profile.yaml` | `29e33a4103eaa6d19c563a6cea52e1b0b25937480edff3a6d127e3428a2deaa4` |
| `tests/fixtures/pcba-design/project/variants.yaml` | `6ce057427c1d130cb5ef00fcd913a36cbb23927ff38274cea95517653759ad36` |
| `tests/fixtures/pcba-design/retained/pkg-standard/bom/sierra-bom.xlsx` | `ad434f8c0ad1937e49e91131461d8734fd187030e075ac9f91a6d00c71727239` |
| `tests/fixtures/pcba-design/retained/pkg-standard/drawings/assembly.svg` | `c2cd2d347512916be3cc072615a5aa29e621e9d4a753a4fd713bbe14456cb19b` |
| `tests/fixtures/pcba-design/retained/pkg-standard/drill/nonplated.drl` | `7797ad07c2831b82766b3805de9c1b01efd51f043236608c8f87ebd69d2e7050` |
| `tests/fixtures/pcba-design/retained/pkg-standard/drill/plated.drl` | `898bf514aadb0ffdade2c1cac55b19fda8878561691c5463de6ba84519e63709` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/asm.bom_consistent.json` | `552d5c0b882ed9ee91879b044eddf5758a17f7332cdd5ca49350d51616cd6e64` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/asm.placement_rotation.json` | `5587b213390486be552a3198cbc8572cf2a38c7b88020a3361b9d07e32b79cc5` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/asm.stock_dated.json` | `fa61a3e676d8689e27145b642e7c37b33a97d55d044ab2e80bb6d80b466770c8` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/asm.test_record.json` | `4a90d8ebfc0402eaa645ce8aade5b5c66bb949d8be3cb736c49832ef8b3f42be` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/asm.variant_agreement.json` | `934b7168eb39628989c78bd3cb6760c46dbe4d6e3a345a5d73bdd2979d880ac5` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/design.drc.json` | `3c138fcd0647cdf7c1a0e0724fedc265e2494d3ca4583fe91b4b675d3e2562e9` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/design.erc.json` | `c5bb35fbe92ec19715d82d63f967b9911679e2e387af8e0cf66f382eeb8ca447` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/design.parity.json` | `69420dde3559c78ece0623aeba3b4344156a0bb2182570c8a874b7c0da2cdea8` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/fab.drill_split.json` | `4aca972049ca0fc14e0c027e4751a2f7d1be59d7c86673b5f52cdbd4b9cf6ad7` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/fab.export_inventory.json` | `1d304384caca6b5f30770266d81810d3fc49b0b2d7b3d03e0dcd75b9de4b9ed0` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/fab.layer_order.json` | `054bdb3dd0a1b9c74a5028d241e27587a3979ba417439f07adca058030f57da4` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/fab.profile_evidence.json` | `4d7e03105faeeb64e4573d38df30e89005d748c37e03eebcef8ed533ec128c22` |
| `tests/fixtures/pcba-design/retained/pkg-standard/evidence/fab.supplier_rules.json` | `8abdb8db381e79250cc80def7a1ce1ca4147cb3adc9f7b28814e7df8cfa809e0` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/fabrication-drawing.gbr` | `df5125af0aae24e2915859dc1fe0af4eeff0928cebf422cadbd89684f0e73723` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-B_Cu.gbl` | `6b9a5015add3c4de9ee57abb428306d4dbcc180e1e841fcf2409527f148e2ff2` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-B_Mask.gbs` | `6ba96103bb782be2506ee597a78bf22e50bf27a24cfabd189bb4e6f9e4c5e5ae` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-B_Paste.gbp` | `35691f54363aff7da9149b5b4c0ea28929792c4ebfabcfd20d8f7b551617827b` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-B_Silkscreen.gbo` | `009dbef5787689ed35f5e19cfa01a423da85146dbeb811300f21e9e71153bff2` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-Edge_Cuts.gm1` | `584b1ad65a4553e0e4d7dd18e1fa75d3a13315c187460ac21ea2eb10f9daa34d` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-F_Cu.gtl` | `b3ad244bdaf1851bf8c0c7b1cce8e0e8208879d74aa60c83aae4718ae2b1d43c` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-F_Mask.gts` | `b509e5448910b5020bee9e5f47b062ab82cc7af5c1301e92ebea4b01a8814f06` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-F_Paste.gtp` | `d8bda31b53bec1cfce7ba343f8561bf325912a4582f00c22c391f6b406fae010` |
| `tests/fixtures/pcba-design/retained/pkg-standard/fab/gerber/board-F_Silkscreen.gto` | `195aab06c03f0f0c3c42217da7d2fae97af4d43ac35e9b5cdfbe2a2a9aeec27c` |
| `tests/fixtures/pcba-design/retained/pkg-standard/image/board.svg` | `43fc42dd54a9b71261caaa7106b834aecdfad423a4bf8fef772c6388cc7ae69b` |
| `tests/fixtures/pcba-design/retained/pkg-standard/manifest.json` | `9d51c742a0b5364e3c43281c880e081356d5001b07f175f376b45af26742293b` |
| `tests/fixtures/pcba-design/retained/pkg-standard/placement/sierra-xy-draft.csv` | `85f73ef4872f9a480af0bdacd390db28e0f688c83544b322ffaee72f195ac7df` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/assembly-neutral.json` | `8b3438271d9b14401b119104aaee59b1652dd7ee2b8dbeca8de05ee25dec25fd` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/drc.json` | `67731a9c037f4d2b902addb3a822755265fdde2a900a10573af69494e1e9daa1` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/drill-split.json` | `6fcd1975f6ed147830035a9bbfe0dd0a21e5cf0189436f81891834f70e7a3618` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/erc.json` | `646c7fb5d4135a8282430c8b5ea226938c8929909a653459f776236389c9d465` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/export-inventory.json` | `ee32d519bf1ccfdb89d71fc5cdf570fd3c6f149a98b2ca056271e38e704cde19` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/layer-order.json` | `aaca6d424d78584cfffdb8b46281b6b914a71535b80a1f0f48d1095174a9b50a` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/parity.json` | `00a6e97509472ca0daff8360b3474402110f1709f5497346af2fd60a3f70c551` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/sierra-status.json` | `ff8c47857ba09e9c096fceb13ad134c76620819cc9581fe628274a2ec00b097d` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/supplier-evidence.txt` | `9b228dbf457fcdf80a5a517c2305556ff48fa6d60837729f274022e264f87c9e` |
| `tests/fixtures/pcba-design/retained/pkg-standard/reports/supplier-rules.json` | `c1aae82cdfca7def31114b9f6175f626d3da3b8f09f89f6a68980129269b93d5` |
| `tests/fixtures/pcba-design/retained/pkg-standard/test/test-record.json` | `1460d140cd1af036a369b6e524f93694eb1114108813fe0cd1b22008edabd35d` |
| `tests/fixtures/pcba-design/retained/validator-result.json` | `218395b20d712bdea4cfbc13cb2d80e368545cbac80867312ae62173c488dd66` |
| `tests/fixtures/pcba-design/standard-project/board.yaml` | `da6773bf8fc75debc19fe0471aa8305fb411b77dd236c2359bdff6710019874a` |
| `tests/fixtures/pcba-design/standard-project/components/cap-100n.yaml` | `6d92bae75baf73304a9e5ed0d5dca93ab58ccc2e64fb9a8c7925fc4040ff593e` |
| `tests/fixtures/pcba-design/standard-project/components/header-2.yaml` | `2546128f2893a074f06cb31978f58f3897d41c8c43ca5d4c3d10722b610ed2e9` |
| `tests/fixtures/pcba-design/standard-project/components/led-green.yaml` | `449962943f98cd6a3db980d3274e92a93a60000510bcde89c0f997f7414c7faa` |
| `tests/fixtures/pcba-design/standard-project/components/parts-map.yaml` | `0d26cc93458dd2d743f24d12901e8e92da04d36175e551c82b60066404144e08` |
| `tests/fixtures/pcba-design/standard-project/components/resistor-10k.yaml` | `11bef0c36e83db32be23df9e0db5b8465d8e18c4b490ab70c8e6d4c1c7f308d5` |
| `tests/fixtures/pcba-design/standard-project/components/testpoint.yaml` | `3c09b1bace014af514a78adc5a6d869403b1bda04b7410930670c35e29f3a81a` |
| `tests/fixtures/pcba-design/standard-project/kicad/board.kicad_pcb` | `3bda15fa26f711a5647dc6cdd2f074786095e272062bd4737a3773664240f14e` |
| `tests/fixtures/pcba-design/standard-project/kicad/board.kicad_sch` | `ff883a203f2b07864fe8c0e5a4e26d37afdd8a93a84ab1db1657c3f7c9f539ae` |
| `tests/fixtures/pcba-design/standard-project/manufacturing/evidence/turnkey-pro-service.txt` | `9b228dbf457fcdf80a5a517c2305556ff48fa6d60837729f274022e264f87c9e` |
| `tests/fixtures/pcba-design/standard-project/manufacturing/export.yaml` | `c56e136a6d3e5f1f7e8ec33bef66e589acfaaf580a4a0673a7143554a684830c` |
| `tests/fixtures/pcba-design/standard-project/manufacturing/supplier-rules.yaml` | `c62f0c61cd00ab35671eb1e33e4ce9fa1385d876f1b362144b1e4330601ebffb` |
| `tests/fixtures/pcba-design/standard-project/manufacturing/supplier-settings.yaml` | `6e23cd77a375696ff288c8a8f10ce31b2f637ce51b364616bfc142957a5bf835` |
| `tests/fixtures/pcba-design/standard-project/manufacturing/supplier.yaml` | `1c036fc4df5fc0562e419d3a844877f69f319b338dba6179aadaef82220e9813` |
| `tests/fixtures/pcba-design/standard-project/mechanical/board-interface.json` | `7095e4855a477d44c6605c7525e8ab39f409d0d30dcc9cfefed19634689323dd` |
| `tests/fixtures/pcba-design/standard-project/toolchain.lock.json` | `5eed9dc6fcda5792ca54845a49dcee9464b5ffc99958e69d9fc713af8a8d541d` |
| `tests/fixtures/pcba-design/standard-project/variants.yaml` | `6ce057427c1d130cb5ef00fcd913a36cbb23927ff38274cea95517653759ad36` |
| `tests/test_pcba_design.py` | `44dc570447d01f2d006ede1db83b3873a6bee4dc6ce21a4b8b900c76ce69ed8f` |
