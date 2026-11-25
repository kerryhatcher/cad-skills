# B10 correction handoff (Claude, claude-pcba-dev, w1P:p7)

Date: 2026-11-15 UTC. Saved at about 72 percent context, on lead request, before implementation.
Model: claude-haiku-5-5 (keep). Branch: work/pcba (keep). Worktree: /mnt/storage/projects/cad-skills-worktrees/pcba.
Status: stop before implementation. Do not edit frozen files. Do not change models.

## Frozen batch to be superseded (do not edit)

- Record: docs/reviews/pcba/b10-completion-claude.md, sha256 7a0a4a2720984552fc3fe86033061d97de3360caab02a9bc050dffe60e7105f0. It lists 42 file rows; all hashes matched at freeze.
- Its behaviour summary contains a false claim: "the other checks pass" while asm.stock_dated fails (LED stock 10 below demand 20). Correction item 7 fixes this.
- Earlier records are kept: docs/reviews/pcba/b9-b10-overlap-correction-claude.md, b9-b10-batch2-correction-claude.md, b9-b10-alternates-batch-claude.md, b9-b10-batch2-claude.md, b9-neutral-correction-claude.md, b9-post-replace-correction-claude.md, b9-final-neutral-repair-claude.md.

## Review and scope paths

- Scope root: docs/reviews/pcba/b10-completion-scope-root.md (six points).
- Pi review: docs/reviews/pcba/b10-completion-review-pi.md (confirms the six points; D1 to D6 detail).
- Codex review: docs/reviews/pcba/codex-review-b10-completion.md (the Codex handoff is docs/reviews/pcba/codex-handoff-b10-review.md).
- Combined correction root: docs/reviews/pcba/b10-completion-correction-root.md (eight items).
- Root probe: docs/reviews/pcba/b10-package-validation-probe-root.py and docs/reviews/pcba/b10-package-validation-probe-root.json. The package step exits 0, then the full copied validator exits 2 with missing inputs, missing evidence roles and path mismatches.

## Combined correction (eight items to implement in one batch)

1. Capture all necessary project records using the accepted paths and profile-hash rules. Validate the project and the complete staged package, not only record structure. Missing prerequisites must not yield a package that fails its listed-evidence checks.
2. Implement ERC, parity and profile-evidence checks for supplied inputs. Use pending only for an absent or explicitly unmeasured input.
3. Derive expected exports from captured export settings. Compare missing and extra files independently. Compare drill coordinates, multiplicity and plating with a captured board inventory. Header text alone is not enough.
4. Capture the toolchain and settings. Resolve the local image identity, compare it with the lock, and run that identity. Never pull an image. The current code hard-codes the mutable tag localhost/cad-skills-pcb:b6.
5. Validate all staged bytes and counts. Repeat input freshness immediately before publication, after the staged validation. Add controlled source drift during staged writes, and final staged-output alteration tests.
6. Compare assembly evidence with captured parts, variants and board limits. Refuse missing test steps (an empty item list must not pass). Generate the selected variant's assembly drawing with DNP marks. Keep physical measurements unmeasured and supplier conventions unconfirmed.
7. Correct the record's stock claim (LED stock fails on the fixture).
8. Retain a complete standard-layout fixture and a full validator result for the generated package. Include the listed independent negative cases from section 14. Preserve prior packages on failure.

Constraints: owned code and copied local helpers only; no runtime import of another skill; no shared schema change; accepted neutral and Sierra behaviour stays closed except necessary call-site compatibility.

## Code facts for the next session

- Skill files: skills/pcba-design/scripts/ (pcba.py, package.py, export.py, checks_design.py, checks_fab.py, checks_asm.py, report.py, sierra.py, project_io.py, sexp.py). Contracts: skills/pcba-design/contracts/ (validate.py, schemas, part-map schemas, alternate-approval schema).
- package.py: build_package(pcba, project, board_rel, variant, as_of, package_id). The staged gate is _verify_staged. The snapshot check runs before the staged writes (item 5 moves it).
- export.py: run_exports(board_bytes) runs IMAGE = localhost/cad-skills-pcb:b6 with --pull=never and --network none on a temporary copy.
- KiCad version 10.0.5. kicad-cli pcb drc exits 0 even with violations; read violations and unconnected_items from the JSON.
- Evidence rules: a pass needs inputs and artifact, and a tool method needs a tool object. Manifest: layer only on layered roles (copper, mask, silk, paste, outline).
- Fixture: tests/fixtures/pcba-design/project. Sierra and package tests use sierra_project (empty restrictions). The shared fixture has a nonempty restriction, kept for neutral and negative tests.
- Test runner: uv run tests/test_pcba_design.py (77 pass at freeze). Package checks: uv run tests/test_skill_packages.py (7 of 8; test_snippet_routing is release-owned).

## Next step

Wait for the lead's release of the combined correction. Then implement the eight items as one batch, run the focused tests, and freeze one complete replacement batch for both reviewers. Keep all earlier records.
