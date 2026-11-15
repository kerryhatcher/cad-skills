# B5 correction review: Pi

Date: 2026-11-14.

**Decision: the correction is accepted. B5 can complete with its explicit limits. I found no technical blocker.**

Two final-record actions remain. They are documentation steps, not technical defects. The final record must present the corrected revision and the corrected U1 status. It must also name the correction manifest and the supplement manifest.

I reviewed E1 to E6 and Pi-1 and Pi-2. I ran no GUI repeat, no unrelated suite and no implementation edit. I changed only this report.

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Correction record | `docs/reviews/b5-correction-claude.md` |
| Correction manifest | `docs/reviews/b5-correction-files-v2.sha256`, 1154 entries |
| Correction manifest hash | `00297fd7caf708b3f8deaa58202c1cf6ca1bfebfba3c826244f12ff85cb8c188` |
| Check result | 1154 of 1154 entries `OK` |
| Corrected board | `results/final_r2/trial.kicad_pcb`, SHA-256 `56f794242345dd3950d5bd066bea6f2a1d1740c5adfc7152651667210297bd94` |
| Image | `d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2` |

The correction manifest is complete. It contains every path of `b5-files.sha256` (707) and every path of `b5-supplement-files-v2.sha256` (325). It also contains every file under `examples/pcb-trial/`, except `out/` and `__pycache__`.

Exactly 5 main entries changed:

- `scripts/check_exports.py`
- `scripts/build_draft_package.py`
- `scripts/export_final.sh`
- `scripts/layout.py`
- `tests/test_trial_exports.py`

All 325 supplement hashes are unchanged. The main `b5-files.sha256` now has 5 stale hashes by design. The final record must use the correction manifest, not the old main manifest alone.

The v2 manifest replaces the v1 correction manifest. The one-line difference is the correction record:

- v1: `b5-correction-claude.md` = `9d941c560054d263a97968aca65718839cd885ce5ca201b9f6887f88886ed9fb`
- v2: `b5-correction-claude.md` = `4a345c13c3e5be10f8f810ecffc4ad92715c1d532e032bf50a393bc91acea5ca`

No implementation file changed between v1 and v2. I use v2 as the final B5 acceptance boundary.

## 2. E1 to E6

| Item | Result |
|---|---|
| E1 | `fab.layer_order` now uses the passed `gerber.layer_function` result beside `gerber.layer_set`. The file-function comment of each Gerber is compared with the fixed nine-layer mapping and the board copper order. No job-file-only check. |
| E2 | A repeated placement reference fails before comparison. The row count must be exactly 7. |
| E3 | The diagnostics stay in the frozen supplement. This correction does not change them. |
| E4 | The `export_final.sh` comment is corrected. The replace-off classification stays in `results/supplement/classification.json`. |
| E5 | `drillshape 0` is set and checked. The copper and mask files have no drill marks. |
| E6 | `usegerberattributes no` and `usegerberadvancedattributes no` are set and checked. The file function is a `G04 #@!` comment. No schema change. |

### Measured checks

`uv run scripts/check_exports.py results/final_r2/export results/final_r2/trial.kicad_pcb` gives 7 of 7 pass:

```text
pass board.plot_settings
pass gerber.layer_set
pass gerber.no_active_attributes
pass gerber.layer_function
pass drill.pth
pass drill.npth
pass placement.rows
```

The same command on the first revision (`results/final`) fails exactly the 3 intended checks: `board.plot_settings`, `gerber.no_active_attributes` and `gerber.layer_function`.

I reproduced the original defects against the corrected export in temporary copies:

- Exchange the bytes of `trial-F_Cu.gbr` and `trial-B_Cu.gbr`. `gerber.layer_function` fails. The names stay correct.
- Insert an extra conflicting `C1` placement row before the correct row. `placement.rows` fails.
- Insert the same row after the correct row. `placement.rows` fails.
- Add an active `%TF`, `%TA`, `%TO` or `%TD` command to a Gerber. `gerber.no_active_attributes` fails.
- Remove, duplicate or corrupt the file-function comment. `gerber.layer_function` fails.
- Change each saved plot setting. `board.plot_settings` fails.

The test file covers these cases, plus the identical duplicate, the missing row and the 4-layer copper order. It passes 16 of 16.

### Effective settings and file functions

The corrected board holds these saved settings:

```text
(drillshape 0)
(usegerberattributes no)
(usegerberadvancedattributes no)
```

No exported Gerber has an active `%TF`, `%TA`, `%TO` or `%TD` command. Each of the 9 Gerbers has exactly one comment:

```text
F.Cu        Copper,L1,Top
B.Cu        Copper,L2,Bot
F.Mask      Soldermask,Top
B.Mask      Soldermask,Bot
F.Paste     Paste,Top
B.Paste     Paste,Bot
F.Silkscreen Legend,Top
B.Silkscreen Legend,Bot
Edge.Cuts   Profile,NP
```

The `drawing` setting `usegerberextensions no` stays. The names are `.gbr`, not Protel extensions.

## 3. Regenerated exact-byte evidence

The corrected board hash is `56f794242345dd3950d5bd066bea6f2a1d1740c5adfc7152651667210297bd94`.

I re-ran DRC with schematic parity and ERC on a temporary copy of the saved board, offline, in the existing image:

- DRC exit 0: 0 violations, 0 unconnected items, 0 parity findings.
- ERC exit 0: 0 violations.
- The board hash did not change.

The stored reports agree. The first revision stays as history.

The design identity did not change. The `identity.py` comparison of the first and corrected boards is `equal` with 0 differences. A text diff of the two boards with the three plot-setting lines removed has 0 lines. Thus the correction changes the export settings only.

The 6 export commands exit 0. The RC assertion gives 2.0860 V pass and 1.2054 V fail for 220 nF.

## 4. T11 agreement

The new `trial.kibot.v3.yaml` sets `use_gerber_x2_attributes: false` and `use_gerber_net_attributes: false`. The old `trial.kibot.yaml` stays as history.

`uv run scripts/compare_kibot.py results/final_r2/export results/final_r2/t11/kibot_out` gives `[]` and exit 0. The comparison covers the 9 Gerber names, the stable Gerber lines, the drill split (holes, diameters, positions), the placement header and the placement rows as numbers. Thus KiBot agrees with the corrected kicad-cli export at the neutral X2 and drill-mark state.

## 5. Draft package

`contracts/validate.py --project .../final_r2/draft_parent/project --package .../final_r2/draft_parent/package` gives exit 0 and no findings.

| Item | Result |
|---|---|
| Manifest status | `draft` |
| Reason | `fab.profile_evidence_pending` |
| Checks | `design.erc`, `design.drc`, `design.parity`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split` pass. `fab.profile_evidence` is `pending`. |
| `fab.layer_order` evidence | `gerber.layer_function` and `gerber.layer_set`, both pass |
| Package PCB hash | `56f794242345dd3950d5bd066bea6f2a1d1740c5adfc7152651667210297bd94`, equal to the board |
| `qualified` claim | Exit 1 with `pkg.false_qualification` |

No supplier evidence is invented.

## 6. Pi-1 and Pi-2

**Pi-1.** The 3 files in `results/correction/pi1/` reproduce exactly with the frozen `identity.py` and the retained snapshots. Each has `value` in its added-footprint records. The status and the difference counts match the historical files. The historical files stay unchanged and still have no `value`. The snapshots are the same.

**Pi-2.** The host commands have `.cmd` and `.out` files: `T13r2_build_196` (exit 0), `T13r2_validate_197` (exit 0) and `T13r2_negative_198` (exit 1, expected). The negative report contains `pkg.false_qualification`. The commands and the exit codes are available from the retained output.

## 7. U1 status and final-record actions

The v2 correction record gives the correct U1 status: 6 supported gate edits plus the replace-off option experiment with 2 parity findings. The report-only U1 correction is now frozen in v2.

The main trial record `docs/reviews/b5-trial-claude.md` still says `Native gate edits (7)` and `All 7 give equal`. It also points to `results/final/` and `results/final/draft/`, the first revision. Those statements now describe history.

Two documentation actions are necessary before the final record:

1. Mark the trial report `docs/reviews/b5-trial-claude.md` and the first revision as history, or add a pointer to the correction record. Present `results/final_r2/` and `results/final_r2/draft_parent/` with the corrected U1 status. The U1 count is already correct in the v2 correction record.
2. Name the correction manifest `docs/reviews/b5-correction-files-v2.sha256` (1154 entries) and the supplement manifest `docs/reviews/b5-supplement-files-v2.sha256` (325 entries) as the complete evidence sets. Do not present `b5-files.sha256` alone as current.

These are report actions. They change no measured result.

## 8. Explicit limits

B5 can complete with these limits, which the records state:

- U3 is experimental. The no-edit, sentinel and delete tests ran. Other U3 edits are untested.
- U5 is untested. `kipy` is absent and the offline container has no API socket.
- U6 is a measured negative. The `pcbnew` module has no update function.
- Zone refill inside a GUI update is untested. The preservation test shows that the update keeps the zone.
- One machine, one image and one KiCad version. Other machines and versions are untested.
- The STEP file has no 3D models for C1, J1 and D1.
- The package is a bare-board `draft` with a neutral placeholder supplier profile. It has no supplier evidence.
- The supplement keeps its 3 small record observations: no supplement `steps.txt` lines, no pre-run expectation for the sheet-move probe, and the U2 parity cause is not examined.

## 9. Verdict

The correction is accepted against the v2 manifest `docs/reviews/b5-correction-files-v2.sha256` (1154 entries, `00297fd7...c8c188`). E1 to E6 and Pi-1 and Pi-2 are correct and reproducible. The corrected board and its reports are clean for the exact bytes. The exports and the T11 comparison agree. The draft package validates and stays `draft`. The manifest is complete.

B5 can complete with its explicit limits after the two final-record documentation actions in section 7. No technical blocker remains. The accepted setup, identity and supplement observations stay closed.
