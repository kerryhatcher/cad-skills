# B5 acceptance record

Date: 2026-11-14.

The lead accepts B5 with the limits below. Both reviewers accepted the corrected technical results. This record identifies the current revision and closes the final-record actions in the Pi review.

The accepted board is `examples/pcb-trial/results/final_r2/trial.kicad_pcb`. Its SHA-256 is `56f794242345dd3950d5bd066bea6f2a1d1740c5adfc7152651667210297bd94`.

The complete manifest is [b5-correction-files-v2.sha256](b5-correction-files-v2.sha256), with 1,154 entries. Its SHA-256 is `00297fd7caf708b3f8deaa58202c1cf6ca1bfebfba3c826244f12ff85cb8c188`.

The supplement manifest is [b5-supplement-files-v2.sha256](b5-supplement-files-v2.sha256), with 325 entries. Its SHA-256 is `e54bc0949d687e999649e9d1de0ba0a4ccf9f98e4b88013b67a3beccb58045a8`. The complete manifest includes these entries.

Current results are in [the correction record](b5-correction-claude.md). Acceptance reports are [Codex](b5-correction-review-codex.md) and [Pi](b5-correction-review-pi.md). Earlier trial records and outputs remain historical evidence.

The native route passed six supported identity edits and their repeat runs. The replace-off run is a separate option experiment. It is not a seventh supported edit. Saved-board tests also show preservation of an arc, a via, and a zone.

The corrected board passes ERC, DRC, and schematic parity. Its neutral exports contain no drill marks or active X2 attributes. Layer-function checks and placement checks pass. KiBot agrees with the corrected exports. The RC assertion uses the same target for both circuits. It passes for the nominal circuit and fails for the incorrect capacitor.

The validator accepts the package as a bare-board draft. It has no supplier evidence or physical test result.

These limits remain:

- Results apply to the tested fixture, image, machine, and KiCad 10.0.5.
- SKiDL schematic generation fails the no-edit gate because connectivity changes.
- Netlist import remains experimental. It lacks the complete edit tests.
- The IPC API remains untested. The `pcbnew` updater has a measured negative result.
- GUI zone refill remains untested.
- The STEP export does not establish complete component-model coverage.
- The hierarchy and remove-and-readd probes show identity and placement limits.

B6 can proceed to interface agreement. Implementation follows agreement from both reviewers.
