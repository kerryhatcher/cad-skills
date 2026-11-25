# Review of the frozen B9 neutral batch

Date: 2026-11-15 UTC.

Reviewed the 30 file rows in `docs/reviews/pcba/b9-neutral-batch-claude.md`. Root measured all 30 listed hashes as matching. The author reports 20 focused tests passed. I did not rerun tests. Sierra conversion and B10 publication remain outside this review.

## Findings

### Blockers

1. **The part path can leave `components/`.** `check_part_path` rejects `..` in the path text. `capture` then confines only to the project root. A symlink in `components/` can point to `../outside.yaml` and pass. The author reproduced this result. Resolve the `components` root and target. Require the target to stay under that root. Reuse one captured byte snapshot for each resolved file. Record canonical paths relative to the project. Add a symlink escape test.

2. **The output path can replace an input.** The command accepts `--out board.yaml`. `atomic_write` replaces that input. The author reproduced this result. Resolve the output and all inputs before the write. Refuse any output that aliases an input. Add tests for the board record, board file, map, and part files.

3. **The lock starts too late.** `build` reads all inputs before it enters `project_lock`. It also omits a final freshness check before the write. A cooperating process can change the project during capture or processing. Hold the lock before capture. Recheck captured input hashes before the atomic write. Add a test for a changed input before write.

4. **The board values lose precision.** `read_board` converts the board-file tokens to `float` at lines 122 to 124. This can change exact coordinates and rotation values. Preserve exact board-file values in neutral data. Use separate numeric values only for calculations. Add a high-precision fixture. Keep `kicad-cli pcb export pos` results as comparison evidence only.

5. **Neutral rows omit required fields.** `build` omits `board_quantity`, `datum`, `midpoint_mapping`, and `selected_alternate`. The accepted interface requires these fields. Emit the exact datum `kicad_footprint_origin`, `midpoint_mapping: unconfirmed`, the per-row board quantity, and an empty alternate value while alternates remain unsupported. The code sets excluded rows to `per_board_quantity: 0`, but the interface says one for each row. State zero for excluded rows in the interface and the skill guide.

6. **Hand-install instructions are lost.** The code reads each hand-install reason into `hand`, but it does not copy that reason into the neutral row. The BOM key omits the instruction. Preserve the reason in the row. Group BOM rows by manufacturer, MPN, state, installation method, and instruction. Set the instruction to empty for automatic rows. Add a fixture with two instructions for the same part.

### Additional blocker

7. **Stock selection can use an arbitrary part record.** The code groups stock demand by manufacturer and MPN. It then selects the first part record with that identity. Separate files can hold different stock data for the same manufacturer and MPN. Reject conflicting stock records or define one explicit stock source before the comparison. Add a fixture with two part paths for one manufacturer and MPN.

## Batch record issue

`docs/reviews/pcba/b9-neutral-batch-claude.md` calls `test_snippet_routing` a pre-existing failure. That claim does not follow from the two committed test files alone. The new skill lacks the shared `snippet_envs.json` routing entry. Release owns that shared edit. Record this as an integration failure, not a baseline pass. Do not change shared files in this batch.

## Known limit

Alternates remain incomplete, as the frozen record states. This batch does not establish alternate-part support. No supplier output, manifest, supplier qualification, or physical test appears in this batch.

## Decision

Do not accept this batch until findings 1 to 6 pass focused negative tests. Resolve finding 7 before any stock claim for duplicate part identities. Keep the frozen files unchanged during this review.

This report changes no product file or shared contract.

## Lead resolutions

Date: 2026-11-15 UTC.

I agree with both selected resolutions:

- Keep the raw board-file x, y, and angle tokens in `source_tokens`. Keep numeric fields as derived finite numbers. Use the tokens for exact comparisons. Test high precision, a default zero angle, and non-finite refusal.
- Refuse a stock claim when records for one manufacturer and MPN have conflicting stock or lifecycle values. Do not select the first record. Aggregate demand once per populated reference. Do not add stock quantities from repeated records.

I also agree with the lead's related row rules. Use `assembly_instruction` for the hand-install reason. Use an empty value for automatic rows. Record resolved part paths relative to the project in both rows and inputs.

Codex agrees to these resolutions. This agreement does not accept the frozen batch. The reported defects still require correction and focused tests.
