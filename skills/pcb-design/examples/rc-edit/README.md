# rc-edit

One meaningful edit of the RC template: R2 changes from 10 kohm to 20 kohm. The RC time constant changes from 1 ms to 2 ms.

- `before/`: the template board and schematic, and the interface file.
- `after/`: the same files after the edit. Only the value of R2 changes.
- `expected-difference.json`: the one difference that the edit may cause (identity format, raw values).

Check the edit:

```bash
uv run scripts/identity.py snapshot before/kicad/board.kicad_pcb -o before.json
uv run scripts/identity.py snapshot after/kicad/board.kicad_pcb -o after.json
uv run scripts/identity.py compare before.json after.json --expect expected-difference.json
```

The comparison exits 0 only when the observed differences equal the expected ones.
