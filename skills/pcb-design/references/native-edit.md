# Native schematic edits

Edit `${PROJECT}/kicad/board.kicad_sch` as text. Keep the file a valid KiCad 10 schematic.

## Measured edit kinds

| Kind | Supported | Rule |
|---|---|---|
| Value | Yes | Change the `Value` property of the symbol. Keep the UUID. |
| Add part | Yes | A new symbol gets a new UUID. Its `instances` path uses the same root as the other symbols. |
| Remove part | Yes | Remove the whole symbol and its wires. Record the removed UUID in the expected-difference file. |
| Footprint | Yes | Change the `Footprint` property only. Do not change the footprint UUID by removing the part and adding it again. |
| Reorder | Yes | Change the order of the symbols in the file. The UUIDs stay. |
| No edit | Yes | Used as the control case. |

The replace-off run is an option experiment. It is not a supported edit kind.

## Rules

- Keep the symbol UUID and the `instances` path of each existing symbol.
- Never move a symbol to another sheet. The move loses the identity and adds a duplicate.
- Never remove and re-add a part to change it. The new footprint has a new UUID and a default position.
- Write the expected-difference file before the edit. Use the `identity.py` format: `{"differences": [{"op", "class", "ident", "field", "before", "after"}]}`. Write raw values for `before` and `after`.
- After the edit, run `uv run --no-project --no-config python scripts/identity.py snapshot` on the board before and after the board edit, then `compare --expect`.
- A changed or removed track needs a UUID entry in the expected-difference file.
- Run `erc` after each schematic edit.

## Example

See `examples/rc-edit/`. It changes the value of R2 from 10k to 20k. The file `expected-difference.json` lists the one expected change.
