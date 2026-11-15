# GUI update and the manual route

## Manual route (default)

`uv run scripts/pcb.py update --project PROJECT --adapter manual` does three things:

1. It preserves the current board in `${PROJECT}/out/history/boards/`.
2. It writes the handoff file `${PROJECT}/out/handoff/manual.json` with the input hashes and the pending step.
3. It exits 2 with `update.manual_required`. The dependent steps stop.

The user or the agent then saves the board in KiCad. Next, run `drc` (for parity) and examine the interface. A board saved by KiCad has no automatic rebinding proof. Record the review with `interface --record-review`.

## GUI adapter

`uv run scripts/pcb.py update --project PROJECT --adapter gui --expect FILE [--replace on|off] [--delete on|off] [--relink on|off]`

Write `FILE` before the update. `FILE` names a path inside the project, for example `${PROJECT}/expect/r2-value.json`. An absolute path, or a path that leaves the project, fails with `path.escape`. `FILE` has the identity format (`{"differences": [...]}`) and lists each change that the schematic update may cause. Each entry holds raw `before` and `after` values.

The adapter runs in the runtime image on a staged copy of the project. It does this in order:

1. Preflight. The image ID must be one of the measured IDs in `GUI_IMAGE_IDS`. KiCad must be 10.0.5. Xvfb, xdotool, ImageMagick `import` and `kicad` must exist. Otherwise the command exits 2 with `update.adapter_unavailable`.
2. It starts KiCad in Xvfb at 1600x1000, opens the update dialog, sets the three options, updates the PCB, saves the board and closes KiCad.
3. It validates the driver summary. An absent or malformed summary exits 3 with `update.summary_malformed`. The KiCad exit must be `exited` with code 0 (a forced stop or other exit exits 3 with `update.kicad_exit`). A measured option state that differs from the request exits 3 with `update.option_mismatch`. The adapter keeps the screenshots and the driver logs under `out/reports/update-trace/`.
4. It compares the saved board with `FILE` by the identity reader. A difference that `FILE` does not list exits 1 with `update.identity_mismatch`. The adapter publishes nothing.
5. It runs DRC with schematic parity. Any parity finding exits 1 with `update.parity`. The adapter records other DRC diagnostics, and the state is `not_ready`.
6. It preserves the prior board, writes the saved board, and records the change with its expectation. The whole-board geometry comparison is not a publication gate, because a valid expected edit can leave an intermediate board that needs routing. The interface does not rebind here. Run `interface --apply --expect out/reports/update.expect.json` to rebind it. That conservative comparison then decides. A changed interface can stay not ready.

Limits: one dialog layout (KiCad 10.0.5, screen 1600x1000, no window manager). The driver reads the option states from screen pixels. A zone refill is not part of a GUI update.
