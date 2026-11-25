# OSH Park KiCad setup coverage: gap report and proposed files

Date: 2026-11-15 UTC.
Author: `claude-release-dev` (Claude, assigned model Haiku 5.5).
Status: report only. No product file is changed. The frozen set (`b12-adapter-isolation-freeze-claude.sha256`) stays as it is. Source-manifest additions wait for the frozen review, as the lead directed.

Source request: `docs/reviews/oshpark-kicad-setup-root.md` (original worktree).

## 1. Measured current coverage

Searches over `skills/pcb-fab-package` and `docs/pcb-pcba-plan.md`:

| Topic (lead item) | Current coverage | Gap |
|---|---|---|
| 1. Board Setup, physical layers, constraints, net classes | Net classes appear only in the plan | No procedure in the skill |
| 2. Supplier limits separate from setup recommendations and margins | Supplier limits exist in `supplier/profiles/*.yaml` with source URL and hash | No written separation of limit and recommendation |
| 3. Mask expansion, minimum web, tenting, assembler paste | Tenting appears only in the page copies; web appears in the mask checker and profiles; paste appears in the export schema | No mask-expansion or paste guidance for the user |
| 4. Fill and save zones before export | Refill appears only in the plan | No user instruction |
| 5. Embedded fonts for native, local rendering for Gerbers | `fab.py` mentions fonts | No instruction |
| 6. Copper, mask, silk, Edge.Cuts layers for the service | Edge.Cuts and layer checks exist in `semantics.py` and `workflow.py` | Per-service layer list is not in the skill docs |
| 7. Disable plot-on-all-layers; examine effective layer functions | `workflow.py` mentions plot | No user instruction |
| 8. Documented drill settings mapped to the measured KiCad 10 command | `export_inspect.py` and `workflow.py` mention KiCad 10 | The mapping to OSH Park drill settings is not written |
| 9. X2 difference | X2 appears in the validator, the schema and the exporter | No written explanation of the difference |
| 10. Source links with measured version and dates | The service pages are in `sources.yaml` and the profiles. The three KiCad pages are not | Missing three sources |
| Microvia | No mention | Do not infer support (lead) |

## 2. Gaps by file

1. **Sources.** The three KiCad pages are not in any manifest. They need entries with URL, retrieval date and hash. The hashes need a retrieval, which waits for the frozen review.
2. **Procedure.** No skill reference covers items 1 to 9. The procedure belongs in one project-authored reference.
3. **Binding.** The profiles bind to the service pages only. The KiCad pages are setup guidance, not supplier limits. They do not need a profile binding. This keeps the source-review binding as the authority.

## 3. Proposed files (exact paths)

| Path | Kind | Content | Status |
|---|---|---|---|
| `skills/pcb-fab-package/references/oshpark-kicad-setup.md` | Project-authored reference | Items 1 to 9. Each step cites its source URL and the measured KiCad version. No page text is copied | Proposed, not written |
| `skills/pcb-fab-package/sources.yaml` | Manifest addition | Three entries for `design-tools/kicad`, `kicad-design-rules` and `generating-kicad-gerbers`. Fields: URL, retrieved date, sha256, content type, distribution decision | Proposed. Hashes pending retrieval after the frozen review |
| `tests/eval/distribution.yaml` | Distribution addition | None. The KiCad pages are excluded from distribution as full copies, like the service pages | Proposed, not written |
| `tests/test_release_packaging.py` | Test addition | Each new manifest entry passes D-1 to D-8. The reference contains no supplier bytes (D-7) | Proposed, not written |

Setup guidance is a project-authored reference. Full page copies stay as local evidence outside distribution, as the lead directed.

## 4. Constraints the proposal keeps

- The accepted export contract is unchanged. The X2 difference is explained, not changed.
- Native KiCad 10 support is not inferred from local export success. The OSH Park main page lists KiCad 9.x for native processing. The tested Gerber route stays the route.
- No microvia support is inferred.
- Setup values are reconciled with the selected service limit before any profile change. A setup value does not prove an exported web dimension.
- Source-review and profile bindings remain the authority for changed bytes. A new source hash needs a new recorded review.

## 5. Next steps

1. Codex and Pi examine this report.
2. The lead releases the frozen set. Only then are the manifest entries and the reference written.
3. The hashes come from a measured retrieval recorded in the source review.

No provider call and no supplier contact were made for this report.

## 6. Pi review corrections (recorded, not applied)

Pi's review is `docs/reviews/release/b12-oshpark-setup-gap-review-pi.md`. Its five corrections are recorded here. None is applied, because the lead has not released the frozen set and retrieval needs supplier contact, which the lead has prohibited.

- R-1: name the storage path of the three page copies. If they go under `skills/pcb-fab-package/supplier/pages/`, the existing D-1 and exclusion rules cover them. Otherwise they need repository manifest entries. Proposal: store under `supplier/pages/`, so the existing rules apply.
- R-2: use the full D-2 field set for each new entry, including `license_state` and `magic`.
- R-3: the KiCad 9.x claim comes from the plan and the root request, not from the stored pages. Record that source.
- R-4: confirm both new URLs at retrieval time, not from this report.
- R-5: no copied page text in the reference or the manifest.

Conflict: Pi asks for retrieval with a recorded source review. Retrieval requires contacting `docs.oshpark.com`. The lead has prohibited supplier contact in this scope, so retrieval waits for a lead decision.
