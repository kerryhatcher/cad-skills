# B11 residual run log

Image: `localhost/cad-skills-pcb:b6`, ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`, KiCad CLI 10.0.5. No pull. The run uses captured bytes and the pinned image ID.

Fresh fixture from `make_fixture.py`. The corrected positive flow runs through the thin dispatch with the positional fixture path:

| Step | Command | Exit |
|---|---|---|
| export | `uv run scripts/pcb.py mechanical export DIR` | 0 |
| fit | `uv run scripts/pcb.py mechanical fit DIR` | 0 (geometry pass, fit pass, no missing or inconsistent results) |
| release | `uv run scripts/pcb.py mechanical release DIR` | 0 (release_id b11-mech-fit-a-r1, first_mismatch null) |

Output and record hashes (SHA-256):

```
afc6650d6a0ad52e436cad5eec3bf3ed6d6912ab7a75c5c0bc4e8c25e179f1f1  board-NPTH.drl  (506 bytes, role drill_npth)
cfcb4324935d39ac95b1fc6d2d42583e53c9d1ba333c26091c656c4f7c02a0d1  board-PTH.drl  (423 bytes, role drill_pth)
5109a50209eaebb4e28a82881c3be75c5ffd90f135685c111e7f9d6b1cc2c6a2  board.step  (14721 bytes, role step_board)
7f78d95024454e3e64793cc114c04e4c97c867e04bff04c0592230df1f066fcd  outline.dxf  (7266 bytes, role dxf_outline)
8d9ed46a10ce952a871f8c311617356838bdbea134b04b25e375fcbdd7db811b  fit-assembly.step  (role step_fit)
d789c235197b7488cda12e264a12634ed5708b9f0e58b5df16f2f19ecda5a0f4  report.json  (role report)
f7e28927d75b393e23aee665d071f0920db2813e6c4ae45b3aa285a5b1e2b4c1  mech-release/1 record_sha256
```

Focused residual tests (`tests/test_mechanical.py`, 55 tests pass) cover: interface side and depth mismatches naming the connector and field; source drift refused before the first publication write, with nothing published; a changed release_id naming `release_id` as the first mismatch through the explicit mismatch order; a changed board naming `board.kicad_pcb`; a changed fit assembly and a changed bound output refused before release; and the `--image` forwarding through the dispatch.

The earlier repair evidence in `docs/reviews/mechanical/b11-repair-evidence` stays historical. This residual evidence is the corrected run for the residual batch.
