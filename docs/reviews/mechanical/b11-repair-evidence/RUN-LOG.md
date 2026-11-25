# B11 repair run log

Image: `localhost/cad-skills-pcb:b6`, ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`, KiCad CLI 10.0.5. No pull. Podman runs with `--pull=never --network none`. The run uses the captured bytes and the pinned image ID.

Fresh fixture from `make_fixture.py`. Commands (fixture directory DIR):

| Step | Command | Exit |
|---|---|---|
| export | `uv run scripts/mechanical.py export --project DIR --image localhost/cad-skills-pcb:b6` | 0 (kicad step, dxf, drill: 0, 0, 0) |
| fit | `uv run scripts/mechanical.py fit --project DIR` | 0 (geometry pass, fit pass, no missing or duplicate results) |
| release | `uv run scripts/mechanical.py release --project DIR` | 0 (release_id b11-mech-fit-a-r1) |

The same three actions run through `uv run scripts/pcb.py mechanical export|fit|release --project DIR` as thin dispatch.

Output and record hashes (SHA-256):

```
f13692d44d66cec28c5b14d9e043525261d68ccf00f68b1f8b6d0004ab3b6249  board-NPTH.drl  (506 bytes, role drill_npth)
2d9c5b3f05c114b9e5e3fd29ce49175674ec64a592f61694ea16db6f8c3dede4  board-PTH.drl  (423 bytes, role drill_pth)
036d8ceb22b371e59c913a5da2a48057488cca6951ff198bf604cd383f32ca46  board.step  (14721 bytes, role step_board)
7f78d95024454e3e64793cc114c04e4c97c867e04bff04c0592230df1f066fcd  outline.dxf  (7266 bytes, role dxf_outline)
6ea4c43ef9874168c6afce5fec40e0480b924e8050a50625ce8a4135ad933145  fit-assembly.step  (role step_fit)
569c9ed7ffa902a0947e1616d1366931cfd4165c0943f85ed1643426c9a77b99  mech-release/1 record_sha256
```

Drill outputs: `board-PTH.drl` (role drill_pth) and `board-NPTH.drl` (role drill_npth), measured with `--excellon-separate-th` in the local image.

## Focused negatives (through the real export)

| Case | Export exit | Fit exit | Release exit |
|---|---|---|---|
| neg_altered_step_output | 0 | 1 | 2 |
| neg_b1_height_5 | 0 | 1 | 1 |
| neg_blocker_U9 | 1 | - | - |
| neg_empty_report_release | 0 | 0 | 1 |
| neg_excluded_no_reason | 2 | - | - |
| neg_export_record_path_escape | 0 | 1 | 2 |
| neg_extra_hole | 0 | 1 | 1 |
| neg_h1_plated | 0 | 1 | 1 |
| neg_mirror_cn1_rot180 | 0 | 1 | 1 |
| neg_missing_b1 | 1 | - | - |
| neg_no_body_length | 1 | - | - |
| neg_slot_oval | 0 | 2 | 2 |
| neg_stale_board_after_export | 0 | 1 | 2 |
| neg_unconfirmed_b1 | 0 | 1 | 1 |
| neg_wrong_image | 2 | - | - |

Notes:
- `neg_slot_oval`: the oval NPTH is written in the DXF as an arc, so the DXF reader refuses it by name (`drill.unsupported`, exit 2).
- `neg_missing_b1` and `neg_excluded_no_reason`: refused before export, by name.
- `neg_blocker_source_U9`: a blocker declared in the source and placed in the CN1 insertion box fails C07 with `intersects: U9` and C09 for U9 outside the cavity.
- `neg_empty_report_release`: a report with no results is refused by the recomputed status, and nothing is published.
- `neg_export_record_path_escape`: an absolute path in the export record is refused before any read.

## Historical evidence

The earlier run in `docs/reviews/mechanical/b11-e2e-evidence` stays historical. It used the frozen Batch 2 candidate. It is not evidence for this batch.
