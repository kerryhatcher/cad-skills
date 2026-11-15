---
name: pcb-design
description: Edit a KiCad 10 board project with native schematic edits, check it with ERC, DRC, simulation and export checks, and prepare a neutral manufacturing export. Use for RC and small bare-board designs. Not for SKiDL circuits.
---

# pcb-design

This skill guides an agent through a KiCad board design. The agent designs and edits the circuit.
The script `scripts/pcb.py` checks the project and runs the tools. The script never designs a circuit.

## Scope

| Route | Status |
|---|---|
| Native schematic (`${PROJECT}/kicad/board.kicad_sch`) with six measured edit kinds: value, add part, remove part, footprint, reorder, no edit | Supported. See `references/native-edit.md`. |
| SKiDL generated schematic | Refused. `source.skidl_unsupported`, exit 2. |
| Netlist import, IPC API, pcbnew updater | Not used. `pcbnew` only reads the board. |
| GUI update adapter (`update --adapter gui`) | Supported only for the measured image IDs (KiCad 10.0.5, one measured dialog layout). The controller refuses another image ID. See `references/gui-update.md`. |

Open limits: one measured fixture, one machine, KiCad 10.0.5 only, no supplier qualification, no zone refill inside a GUI update.

## Procedure

1. Read `references/design-workflow.md`. It lists the decisions and the check that closes each one.
2. Run `uv run scripts/pcb.py env --project PROJECT`. Stop if the report does not show the lock image.
3. Edit the schematic as described in `references/native-edit.md`. Write the expected-difference file before the edit.
4. Run `uv run scripts/pcb.py erc --project PROJECT`. Repair each unwaived violation.
5. Update the board from the schematic with `uv run scripts/pcb.py update --project PROJECT --adapter gui --expect FILE`. `FILE` is the identity expectation that you wrote before the edit (see `references/gui-update.md`). Use the manual route for any other board edit, and follow `references/placement-routing.md`.
6. Run `uv run scripts/pcb.py drc --project PROJECT` (add `--refill-zones` to refill the zones and save the board).
7. Run `uv run scripts/pcb.py sim --project PROJECT` when `${PROJECT}/simulations/` exists.
8. After a board change that the wrapper made, run `uv run scripts/pcb.py interface --project PROJECT --apply --expect EXPECT`. `EXPECT` is the expectation of that operation: `${PROJECT}/out/reports/update.expect.json` (GUI update), `${PROJECT}/out/reports/settings.expect.json` (settings) or `${PROJECT}/out/reports/refill.expect.json` (refill). Otherwise record a review with `interface --record-review`.
9. Run `uv run scripts/pcb.py export --project PROJECT` after clean ERC and DRC results.
10. Run `uv run scripts/pcb.py check --project PROJECT --for ready`. Report the exit code and the state. Run `check --for export` after an export to compare the published files with their bound hashes. A refused run keeps its logs under `${PROJECT}/out/history/failures/`. A residual staging directory is a finding (`staging.residual`, exit 1).

Run every command from the skill directory, or give the absolute path to `scripts/pcb.py`.

## Rules for the agent

- Never edit a hash by hand, for example `board_sha256` in `${PROJECT}/mechanical/board-interface.json` or a waiver hash. A hand edit gives an `interface.review_stale` or `interface.geometry_stale` finding (exit 1). Run the command that owns the hash instead.
- Before you edit `${PROJECT}/kicad/board.kicad_pcb` by hand, run `uv run scripts/pcb.py update --project ${PROJECT} --adapter manual`. It preserves the prior board. It exits 2 by design. Then edit the board. Without the preserved board, the interface rebinding fails.

- Keep the symbol UUID and the `instances` path of each existing symbol. Never remove and re-add a part to change it.
- Change a footprint only through its `Footprint` property.
- Never move a symbol to another sheet. The identity is lost.
- A board change makes every ERC waiver stale. No operation renews a waiver. The user must renew the waivers.
- A GUI save by the user has no prior copy. The rebinding of the interface is then refused. Use the review record.
- Do not claim that a board is ready when `check --for ready` exits 1.
- Do not claim an identity-kept change when the identity comparison shows an unexpected difference.

## Records

The validators are separate:

- `scripts/validate.py --schemas contracts/schemas --project PROJECT` checks the registry records of the project: `board.yaml`, `variants.yaml`, `${PROJECT}/manufacturing/supplier.yaml`, `${PROJECT}/manufacturing/export.yaml`, `${PROJECT}/manufacturing/waivers.yaml`, `toolchain.lock.json` and `${PROJECT}/mechanical/board-interface.json`. It also checks the relations between them and the hashes of the board and the schematic. It does not check `${PROJECT}/mechanical/interface-review.json` or `${PROJECT}/components/*.yaml`.
- `pcb.py check` runs `validate.py` on each part record in `${PROJECT}/components/*.yaml`, one file at a time. Its readiness check reads `${PROJECT}/mechanical/interface-review.json` (a skill record outside the registry, see `references/design-workflow.md`).
- The schemas are in `contracts/schemas/`.

## Waivers

A waiver lists the exact KiCad item UUIDs of one finding. The set of UUIDs must equal the set of the finding. A label shows the item in the report only. A UUID that occurs two times in the project cannot be waived. A waiver for another board or revision is stale and fails the check.

## Exit codes

See `references/exit-codes.md`. The precedence is 3, then 2, then 1, then 0.

## Runtime

See `references/runtime.md`. The option `--runtime auto|container|native` selects the route. The default `auto` follows `toolchain.lock.json`, and nothing falls back silently. A conflicting explicit runtime exits 2. The native route runs the same tools without podman, and it checks each operation's own tools and the lock versions. The tests run the native route inside the runtime image only. `native` exits 2 on this host with `runtime.native_unavailable`, because KiCad and pcbnew are not installed outside the image. The lock names the image and its ID. A different ID fails the command.

## Files

- `scripts/pcb.py`: the commands.
- `scripts/board_inventory.py`: the pcbnew worker that reads holes and placement in the container.
- `scripts/validate.py`, `scripts/project_io.py`, `scripts/identity.py`, `scripts/sexp.py`: accepted helpers. They are copies and do not change.
- `contracts/`: the record schemas and the copy of their README.
- `runtime/`: the build recipe with pinned versions.
- `templates/rc-bare-board/`: a bare RC board project.
- `examples/rc-edit/`: one value edit with its before files, after files and expected difference.
