# B6 worker checkpoint review: Pi

Date: 2026-11-14.

**Decision: the two frozen workers are accepted at the worker-only scope. No blocking worker defect. The caller `pcb.py` must enforce the option-state, process-exit and board-change checks. Six caller-side items remain.**

## 1. Reviewed bytes

| File | SHA-256 before and after |
|---|---|
| `skills/pcb-design/scripts/board_inventory.py` | `b990a150796f988e5f88e785e2ca6aa001862b9c89c6173897e658ef8ea71fa8` |
| `skills/pcb-design/scripts/gui_update.py` | `7e953fead679f3e63929eab2d74368806335a1a545ca397b563eae328ddaa18c` |

The hashes did not change. Image: `localhost/cad-skills-pcb:b6`, ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`. The 19-pass log is `suite-full.txt` in the named scratchpad. I read it; I did not rerun the suite.

## 2. `board_inventory.py`

The worker reads with `pcbnew`. It uses `GetPosition`, `GetOrientationDegrees`, `IsFlipped`, `GetDrillSize`, `GetPosition` and `GetDrillValue`, and `GetEnabledLayers().CuStack()`. It keeps KiCad's transformed coordinates and appends each object to a list, so multiplicity is preserved. It refuses a slot or oval drill, a drilled pad that is not plated or non-plated, and a via that is not through the board. It names each refused object and exits 2.

**Focused probe.** I ran the frozen worker in the image on `results/final_r2/trial.kicad_pcb`, with `uv run --no-project --no-config --offline --python /usr/bin/python3`. The board hash before and after was `56f794242345dd3950d5bd066bea6f2a1d1740c5adfc7152651667210297bd94`, unchanged. The output equals `examples/pcb-trial/results/b6-probe/plain.json` for the copper layers, the KiCad version, the footprints, the pad holes and the via holes. Standard error held only the known `pcbnew` assertion messages.

**Limits and defects.**

1. The docstring says diagnostics go to standard error, but the error and refusal JSON go to standard output. The caller must use the exit code. Recommend either move the error JSON to standard error or correct the docstring.
2. The worker lists all footprints. It does not apply the placement filter. The B6 design said one filter function serves the export and the inventory. The caller must filter.
3. The worker does not refuse a copper layer that the export settings do not name. The caller checks this.
4. The slot and blind-via refusal is static-reviewed only. No slot or blind fixture was probed.
5. The `refuse(objects, status=2)` parameter is unused. Minor.
6. It does not report the outline or cutouts. This is outside its scope.

## 3. `gui_update.py`

The worker runs on a staged copy, takes the project basename as an argument, measures the three option states from the screen, saves dialog and save screenshots, records the before and after board hashes, the `pcb_changed` value, and the KiCad exit state and code. It never reports a pass. The caller judges with the identity reader and the parity check.

The 19-pass log includes the GUI integration, the identity mismatch, the missing expectation and the manual refusal tests. Thus the caller enforces those cases.

**Limits and defects.**

1. The worker records `options_measured.after` but does not fail when `after` differs from the request. The caller must compare and fail.
2. The worker records `kicad_exit` but does not fail on an abnormal or forced stop. The value `"stopped by the script after 15 s"` is not a pass. The caller must reject it.
3. The worker does not fail when `pcb_changed` is false. The caller must check it when the edit expects a change.
4. The worker assumes the root config path `/root/.config/kicad/10.0` and the exact 1600x1000 screen. `pcb.py` must preflight the image, the KiCad version and the screen.
5. An uncaught `xdotool`, `import` or window error exits nonzero with a traceback, not a JSON failure. The caller must treat a nonzero exit as a failure.
6. The default `--replace on` matches the dialog default. The caller selects the option for the edit.

## 4. Caller-side items

These are not worker defects. Confirm them when `pcb.py` is reviewed:

1. Compare `options_measured` with `options_requested`. A mismatch is a failure.
2. Reject `kicad_exit.state != "exited"` or `kicad_exit.code != 0`.
3. Reject `pcb_changed == false` when the edit expects a change.
4. Apply the placement filter in one function used by the export and the inventory.
5. Add a focused caller test with a stubbed summary for the option mismatch, the forced stop and `pcb_changed` false.
6. Add an inventory refusal fixture with a slot or a blind via.

## 5. Limits of this worker-only review

- `pcb.py` is not reviewed. Its enforcement of the six items is out of scope.
- I ran one focused inventory probe. I ran no GUI probe. The 19-pass suite already ran the real GUI.
- I did not pull an image and did not run a broad suite.
- I accept the 19-pass log as reported and did not rerun it.
- The worker-only review cannot confirm the caller's failure paths, the GUI option mismatch, the forced-stop policy or the placement filter.

## 6. Verdict

The two frozen workers are accepted at the worker-only scope. No blocking worker defect. The six caller-side items in section 4 must be confirmed in the `pcb.py` and runtime-test review. The stdout/stderr docstring mismatch and the unused `status` parameter are small corrections.

No implementation was done.

## 7. Caller correction agreement (r3)

Date: 2026-11-14.

I reviewed the live `skills/pcb-design/scripts/pcb.py`, SHA-256 `c57de5b825ae03bb32f9132d3ebf2a1e088338f0216c3534286b9738c5f87621`. I agree with the caller corrections and the two live findings.

1. **Option and process enforcement, plus focused negative tests.** `cmd_update_gui` already enforces `kicad_exit == {"state": "exited", "code": 0}` and `options_measured[name]["after"] == (want == "on")`. Agree. The negative tests remain.
2. **`pcb_changed == false` fails only when the expected edit changes bytes.** An empty `expect["differences"]` (no-edit update) stays valid. Agree. The identity comparison already gives a `missing` difference when an expected change is absent. Keep the explicit check for a clear `update.no_change` message.
3. **One shared placement filter.** `cmd_export` builds `expect_rows` from all `inv["footprints"]`. Define one filter function used by the export and the inventory. Agree.
4. **Unsupported-drill fixture.** Add a slot or blind-via fixture and assert `export.unsupported_geometry`. Agree.
5. **Inventory docstring correction only.** The error and refusal JSON go to standard output. Correct the docstring. Agree.
6. **`normalized_equal` in the update path.** Line 842 blocks every geometry-changing update after the identity and parity checks pass. Keep `normalized_equal` in `cmd_interface` (line 1220) for the interface rebinding. Remove it from `cmd_update_gui`. The identity comparison, the parity check and the option check already enforce the expected update. Allow an expected intermediate board that still needs routing. Agree.
7. **`gui_preflight` image identity.** The preflight checks KiCad 10.0.5 and the tools, but not the exact image ID. Add the resolved image ID comparison with the measured GUI image ID `sha256:b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`. A revised lock must not certify a rebuilt image. Agree.

These corrections restore r3. The interface rebind keeps the whole-board geometry proof. The update path publishes an expected intermediate board. No implementation edit was made.
