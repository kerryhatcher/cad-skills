# rc-bare-board

A bare RC board project for `pcb-design`. Copy the directory before you change it.

- `kicad/`: the KiCad 10 board, schematic and project (saved by KiCad 10.0.5, zone filled, measured clean in ERC and DRC).
- `board.yaml`, `variants.yaml`, `components/part.yaml`: design records.
- `manufacturing/`: supplier record with its note, export contract (neutral subset), empty waiver list.
- `toolchain.lock.json`: the runtime image and its ID.
- `mechanical/board-interface.json` and `mechanical/interface-review.json`: the outline and the initial self-review (a template acknowledgment, not an independent review).
- `simulations/`: the RC circuit (R2 = 10 kohm, C1 = 100 nF) and `assertions.json` (2.086 V at 1 ms, tolerance 1 percent).
- `docs/layout-notes.md`: placeholder notes.

The supplier note and the part record are examples. Replace them before a real order.
