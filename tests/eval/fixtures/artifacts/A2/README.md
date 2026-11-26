# A2: fabrication package input with incomplete status

This fixture holds a project-authored copy of the RC bare board and the selected OSH Park two-layer profile.

- `project/` copies the accepted template. Only `board.yaml` and `manufacturing/supplier.yaml` differ among its input files.
- `board.yaml` selects the current profile and declares `standard_through` through `extensions.fabrication.via_process`.
- `profile/oshpark-two-layer.yaml` and the project supplier file hold identical profile bytes.
- `sources.sha256` records each source hash and its repository path.
- `status.json` records the command results. The `out/fab/` directory holds the measured outputs.

The local Python process validates the profile and returns exit 0. The design command returns exit 0.
The KiCad operations use the accepted local image with no pull and no network.

The supplier command returns exit 1. Sixteen of eighteen mandatory conditions pass.
The order quantity stays at 5. The condition `service.order_multiple` fails because the profile specifies a multiple of 3.
The condition `silk_line_min_short_text` stays pending because the fixture has no bound manual evidence.
The three new conditions for via construction and tool compatibility pass.
The two corner conditions share `corner-report.json`. The via condition uses `via-report.json`.
The matrix binds these produced files to their recorded hashes.

The commands `review-source` and `package` did not run. The fixture does not claim a qualified package.
The two recommendations do not change the mandatory result.
The tests make no supplier contact or provider call. The fixture uses no network at test time.

The fixture ran again on 2026-11-26 after the OSH Park source rebind (issue #10). The profile copy has the new page hash and the new content hash. The exits and the condition results did not change. The note `docs/reviews/oshpark-source-rebind-claude.md` records the run.
