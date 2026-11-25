# B10 handoff (Claude, claude-pcba-dev, w1P:p7)

Date: 2026-11-15 UTC. Saved at 67% context on lead request. Model: claude-haiku-5-5. Branch: work/pcba. Worktree: /mnt/storage/projects/cad-skills-worktrees/pcba.

## Frozen boundary (do not change)

- Last frozen record: docs/reviews/pcba/b9-b10-overlap-correction-claude.md (36 file rows). Accepted by Codex and Pi (overlap correction review).
- Release for the remaining B10 work: docs/reviews/pcba/b9-sierra-acceptance-b10-release-root.md. Governing note: docs/reviews/pcba/b9-b10-remaining-execution-claude.md, sha256 22afe3344d32c1306060446fc5622bc9bd586c15811e0b96accd3ce6c3607610.
- Release rules: one coherent completion batch; freeze all consumed files and outputs before review; no next-batch edits during review; no shared schema change; no physical test result; supplier unknowns stay qualification limits; no commit, merge or push.

## Uncommitted work since the freeze (not yet frozen)

- skills/pcba-design/scripts/export.py: runs localhost/cad-skills-pcb:b6 with --pull=never and --network none on a temporary copy. Verified: gerbers, drill (PTH/NPTH), pdf, svg, drc. Returns {version, files}. KiCad version 10.0.5.
- skills/pcba-design/scripts/checks_design.py: drc (pass only with zero violations and zero unconnected), erc_pending, parity_pending.
- skills/pcba-design/scripts/checks_fab.py: profile_evidence_pending, export_inventory, layer_order, drill_split, supplier_rules_unconfirmed.
- skills/pcba-design/scripts/checks_asm.py: bom_consistent, placement_rotation, variant_agreement, stock_dated, test_record.
- skills/pcba-design/scripts/report.py: CHECK_INPUT_ROLES (copied from interface section 14), evidence_record, manifest_record, sha256.
- Changed earlier in this session, also uncommitted: pcba.py build_sierra (shared Snapshots, staging, overlap and staging-link checks), sierra.py (service record), SKILL.md, tests.

## Verified facts

- Gerber FileFunction lines: F.Cu Copper,L1,Top; B.Cu Copper,L2,Bot; F.Mask Soldermask,Top; B.Mask Soldermask,Bot; F.SilkS Legend,Top; B.SilkS Legend,Bot; F.Paste Paste,Top; B.Paste Paste,Bot; Edge.Cuts Profile,NP; F.Fab AssemblyDrawing,Top.
- Drill: PTH file has "TF.FileFunction,Plated,1,2,PTH"; NPTH has "TF.FileFunction,NonPlated,1,2,NPTH"; both carry "FORMAT={2:4/ absolute / inch / suppress trailing zeros}".
- kicad-cli pcb drc exits 0 with violations. Count is in the JSON keys violations and unconnected_items. The fixture board gives 13 violations, so design.drc is fail on the fixture.
- Exports write board-job.gbrjob, which is not packaged (reported in export-inventory).
- Evidence rules (copied validator): a pass needs inputs and artifact; a tool method pass needs a tool object. Manifest needs release_id, kind, board_revision, board_sha256, variant, supplier, inputs, outputs, applicability, drill_applicability, checks, status, reasons, tool_versions.

## Remaining steps

1. package.py: build_package(pcba_module, project, board_rel, variant, as_of, package_id).
   - Refuse invalid package id (pattern ^[a-z0-9][a-z0-9._-]*$), an existing destination (package.exists), a staging link or directory.
   - One Snapshots object: board.yaml, board file, variants, parts map, parts, approvals, supplier-profile.yaml (hash checked against board supplier.profile_sha256). Refuse nonempty restrictions (supplier.restriction_review) like the Sierra path.
   - Build neutral result with build(..., None, snapshots=snap). Build Sierra files like build_sierra (BOM only when policy known, placement, test record, status).
   - export.run_exports(board bytes). Map files: gerber/* by layer to fab/gerber/<name> with roles copper, mask, silk, paste, outline, fabrication_drawing (F.Fab to fab/fabrication-drawing.gbr); drill to drill/plated.drl and drill/nonplated.drl (drill_plated, drill_nonplated); assembly.pdf to drawings/assembly.pdf (assembly_drawing); board.svg to image/board.svg (image); drc.json to reports/drc.json (report).
   - Checks: design.drc (tool), design.erc and design.parity pending, fab.profile_evidence pending, fab.export_inventory, fab.layer_order, fab.drill_split, fab.supplier_rules unconfirmed, asm.* five checks.
   - Evidence records to evidence/<check-id>.json (role evidence). Each record validated with the copied validator.
   - Manifest to manifest.json at the package root, validated with the copied validator. Status unqualified. Reasons for every non-pass check and for the open supplier conditions.
   - Final gate: snap.check_unchanged(); write all files into out/pcba/.package-staging; verify the staged tree against the expected {path: sha256} set (refuse extra, missing, hash mismatch, links); then project_io.publish_dir to out/pcba/packages/<id>. PostRenameError maps to ReplacedThenFailed.
2. pcba.py: add subcommand `package` with --package-id, dispatched under the project lock.
3. Tests in tests/test_pcba_design.py: package written with the expected files; manifest and evidence validate; 13 checks present with one evidence file each; design.drc fail on fixture; erc/parity/profile pending; supplier_rules unconfirmed; status unqualified; no physical pass; refusal for an existing package id; staged gate refusing an extra file (in-process); partial failure publishes nothing; prior package untouched.
4. Run focused suite, package checks, copies check. Write the freeze record for the B10 batch, verify every hash, notify lead, Codex and Pi. Do not edit the frozen files after the freeze.
