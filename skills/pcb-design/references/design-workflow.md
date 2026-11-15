# Design workflow

Each decision names the record that stores its value and the check that closes it.

| # | Decision | Recorded in | Closed by |
|---|---|---|---|
| 1 | Requirements and board statement | `board.yaml` (`restrictions`, `electrical_limits`) | `check` (record validation) |
| 2 | Circuit topology and values | `${PROJECT}/kicad/board.kicad_sch` | `erc` (no unwaived violation) |
| 3 | Datasheet and pin-to-pad map | `${PROJECT}/components/part.yaml` (`pin_map`, `datasheet_url`) | `check` (part record validation) |
| 4 | Power budget | `board.yaml` `electrical_limits` and a hand calculation | Reviewer note in `${PROJECT}/docs/` |
| 5 | Simulated response | `${PROJECT}/simulations/*.cir` and `${PROJECT}/simulations/assertions.json` | `sim` (each assertion within tolerance) |
| 6 | Footprints and placement | `${PROJECT}/kicad/board.kicad_pcb` | `drc` (with schematic parity) |
| 7 | Routing and copper | `${PROJECT}/kicad/board.kicad_pcb` | `drc` (no unwaived violation) |
| 8 | Zone fill | `${PROJECT}/kicad/board.kicad_pcb` | `drc --refill-zones` (the command saves the board) |
| 9 | Decoupling and return path | `${PROJECT}/docs/layout-notes.md` | Reviewer note |
| 10 | Interface geometry | `${PROJECT}/mechanical/board-interface.json` | `interface --apply` or `interface --record-review` |
| 11 | Waivers | `${PROJECT}/manufacturing/waivers.yaml` | `erc` and `drc` (exact UUID match) |
| 12 | Supplier limits | `${PROJECT}/manufacturing/supplier.yaml` | `check` (record validation) |
| 13 | Export contract | `${PROJECT}/manufacturing/export.yaml` | `export` (seven checks) |
| 14 | Plot settings | Saved board (`pcbplotparams`) | `settings` |
| 15 | Toolchain | `toolchain.lock.json` | `env` (image ID equals the lock) |
| 16 | Release revision | `board.yaml` `release_revision` | `check` (waiver and interface revision match) |
| 17 | Ready state | `${PROJECT}/out/reports/*.result.json` | `check --for ready` |

Do the decisions in this order. Each change to the board stales the results that depend on it.
