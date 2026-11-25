# B7 direct write inventory (claude-skill-dev)

Date: 2026-11-15 UTC. Review only. No product file was changed. Source: `workflow.py` at hash 65f88be9..., `fab.py` at f63e4d58..., `inspect_mask.py`, `inspect_slots.py`.

Status key: **A** = uses `PIO.atomic_write` (confined, refuses a symbolic-link target). **L** = direct write with no check on the leaf. **D** = directory creation or removal with no leaf check. **S** = staged or container output (inside `out/work`).

## design (`_design`)

| Line | Write | Status |
|---|---|---|
| 117-119 | `captured/profile.yaml` (`write_bytes`, scratch dir confined) | **L** (root defect) |
| 117 | `captured/` (`mkdir`) | D |
| 138-144 | `work/` rmtree and rewrite of KiCad inputs, marker | S |
| 227-231 | `export/` rmtree, `export/`, `work/export/`, `logs/` (`mkdir`) | D |
| 236-259 | `logs/erc.stderr`, `logs/drc.stderr`, `logs/export-*.stderr`, `logs/inventory.stderr` (`write_text`) | **L** |
| 265 | `out/inventory.json` (`write_text`) | **L** |
| 267 | `out/erc.json`, `out/drc.json` (`copy2` from stage) | **L** |
| 269 | `out/export/*` (`copy2` from stage) | **L** |
| 281 | `out/drawing-facts.json` (`write_text`) | **L** |
| 282 | `out/fabrication-drawing.pdf` (`write_bytes`) | **L** |
| 301 | `out/design-binding.json` | A |
| 307 | `out/design-result.json` (`write_result` → A) | A |

## supplier (`_supplier`)

| Line | Write | Status |
|---|---|---|
| 345 | `captured/profile.yaml` | **L** (same as design) |
| 347-351 | `work/` stage, `kicad/board.kicad_dru`, `kicad/board.kicad_pro` | S |
| 354 | `out/supplier-drc.stderr` (`write_text`) | **L** |
| 387-389 | `out/slots.json` (written by `inspect_slots.main`, line 120 `write_text`) | **L** |
| 398-402 | `out/mask.json`: `unlink`, then worker writes (`inspect_mask.py` line 248) | **L** (worker) |
| 417-419 | `out/mask-bottom.json`: `unlink`, then worker writes | **L** (worker) |
| 457 | `out/supplier.kicad_dru` (`write_text`) | **L** |
| 458 | `out/supplier.kicad_pro` (`write_text`) | **L** |
| 459 | `out/supplier-drc.json` (`write_text`) | **L** |
| 472 | `out/supplier-binding.json` | A |
| 476 | `out/supplier-result.json` (`write_result`) | A |
| 517-518 | `out/manual-artifact.txt` (`write_bytes`) | **L** |
| 527-528 | `out/manual-evidence.json` (`write_bytes`) | **L** |
| 517, 527 | `out/` (`mkdir`) | D |

## package (`_package`)

| Line | Write | Status |
|---|---|---|
| 548 | `supplier/captured/profile.yaml` (through `profile_from_bytes`) | **L** |
| 597-600 | `dest/`, `dest/evidence/`, `dest/reports/` (`mkdir`), `dest` is `.staging-<name>` | D |
| 621-622 | every staged output: `target.write_bytes` into `dest/` (copies of gerbers, drills, PDFs, reports, observations, manual files, REVIEW) | S (staging) |
| 726 | `dest/manifest.json` (`write_text`) | S |
| 729, 735, 743 | `dest/manifest.json` rewrites (`write_text`), three times | S |
| 745 | `PIO.publish_dir(project, dest, final)` (`os.rename`) | A (directory rename) |
| 796 | `dest/reports/<check>.txt` (`write_text`) | S |
| 805 | `dest/evidence/<check>.json` (`write_text`) | S |

## Gap for C5 (staged bytes)

After `out_item` writes each staged file (line 622) and the manifest is built, nothing hashes the files in `dest/` against the manifest `outputs` entries. The final gate (line 715) compares only the bindings in `out/fab/design` and `out/fab/supplier` and the original manual record. A change to `dest/` between line 622 and line 745 is not caught. The final gate must hash each staged `dest/<path>` against its manifest `sha256` immediately before `publish_dir`.

## Summary for the repair

- Leaf writes (**L**): about 20 call sites across design, supplier and package. Each one can be routed through one confined helper that calls `PIO.atomic_write`. `copy2` calls need the same helper, with the bytes read once from the stage.
- Directory creation (**D**): add a confinement check on each directory before its files are written.
- Staged bytes (**S** and the C5 gap): the final gate hashes `dest/` against the manifest.
- Worker writes (`inspect_mask.py`, `inspect_slots.py`): the parent passes a path. The parent must confine it before the worker runs, and the report must be written through `atomic_write` by the parent after the worker returns.
