# B11 scoping review: Pi

Date: 2026-11-15. Reviewer: pi-skill-dev, pane w1P:pE.

**Decision: the B11 scope is sufficient to start. The frozen contracts have three gaps that the lead must correct first. I agree with most of the Codex review. I add independent geometry evidence and ten corrections.**

This review covers the frozen baseline and `docs/reviews/b11-preparation-pi.md`. It does not accept an implementation.

## 1. Environment and frozen baseline

| Item | Value |
|---|---|
| Worktree | `/mnt/storage/projects/cad-skills-worktrees/mechanical` |
| Branch | `work/mechanical` |
| HEAD | `75d99da` "Record the common PCB workstream snapshot" |
| Model | `deepseek/deepseek-v4.1-flash` |
| Local KiCad image | `localhost/cad-skills-pcb:b6`, ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f` |
| KiCad CLI | 10.0.5, with `pcb export step` and `pcb export dxf` |

Frozen artifact hashes:

| File | SHA-256 |
|---|---|
| `contracts/schemas/board-interface.schema.json` | `8fd8b0e4d15d8ceb29de85245f3f5e3f378b56ed30ac08f9f78cb0cb5a547b9f` |
| `contracts/schemas/board.schema.json` | `9d0b1702bfed18d50485f6ccd59d2da9eeb14c13e4a3246ccb04cb559178ad97` |
| `contracts/schemas/manifest.schema.json` | `096c7aa85eab334d8e5e48d0a7b35e9d66b15c9468c3916185064895a58df790` |
| `contracts/validate.py` | `102e252c211bab973adc4e5ae97c051ad4b35dfb59e53916d8b8099144731d9e` |
| `skills/pcb-design/scripts/pcb.py` | `0928be463f6503b41d5c7ba02c076556c0ac750630da63ac8c86866cf664cabe` |
| `skills/pcb-design/templates/rc-bare-board/mechanical/board-interface.json` | `5254508d3d203f0870b57b611cc70b47dfe4fb4d4c23aaee8287e2fe73a3b4bc` |
| Accepted board `examples/pcb-trial/results/final_r2/trial.kicad_pcb` | `56f794242345dd3950d5bd066bea6f2a1d1740c5adfc7152651667210297bd94` |
| `docs/reviews/b11-preparation-pi.md` | `758957eba2617ee8a64ec98e45e7caedcfc66694cc1d890a02ab5c93f0a80856` |

The three copies of each contract are byte-identical. `contracts/validate.py` and `skills/pcb-design/scripts/validate.py` are identical.

`pcb.py` has no mechanical export. The mechanical surface is the `interface` subcommand (rebind and review, section 13) and the `validate.py` cross-checks. The `board-interface` record has no axis-direction field and no per-component height field.

## 2. Independent check of the preparation report

I read the accepted board directly. These measurements agree with `b11-preparation-pi.md`.

| Item | Value in the accepted board |
|---|---|
| Edge.Cuts rectangle | start `(100, 100)`, end `(140, 125)` |
| MH1 | `(103, 103)` |
| MH2 | `(137, 122)` |
| Interface outline | `0..40` by `0..25` |
| Interface MH1 | `(3, 22)` |
| Interface MH2 | `(37, 3)` |

The transform is `x' = x - 100` and `y' = 125 - y`. The board point `(100, 125)` maps to the interface origin `(0, 0)`. The `origin_mm` field holds `(0, 0)`. It does not name the board anchor `(100, 125)`. The trial `board.yaml` records `coordinate_system.origin` `(0, 0)` with `x_axis: right` and `y_axis: up`. Thus the axis flip is written, but the anchor is implicit.

`tests/test_pcb_design.py` has no transform test. No test proves that a mirrored or Y-flipped board fails.

## 3. Agreement with the Codex review

I agree with `b11-interface-review-codex.md` on these points:

- Keep B11 inside `pcb-design`.
- Keep the frozen `board-interface` schema for this batch.
- Make a new asymmetric fixture with a bottom-side part and a connector frame.
- Keep component evidence apart from `height_limits`.
- Compare geometry with units and tolerances.
- Bind exact artifact hashes to one release.
- Stop publication on the first stale input.
- Do not prove component fit from a board-only STEP.

I add the corrections below.

## 4. Corrections and gaps

### C1. The transform needs a written definition and a validator

The interface `origin_mm` is the origin of the interface frame. It is not the board anchor. The anchor `(100, 125)` is missing. The Codex review puts the transform in `extensions`. The `extensions` object is unconstrained, so `validate.py` does not examine it. The mechanical module must validate the transform extension and fail closed when it is absent. Use one exact shape:

```json
"extensions": {
  "transform": {
    "source_frame": "kicad-board",
    "source_origin_mm": {"x": 100, "y": 125},
    "source_axes": {"x": "right", "y": "down"},
    "target_axes": {"x": "right", "y": "up"},
    "scale": 1
  }
}
```

Do not infer the anchor from `origin_mm`.

### C2. No frozen STEP or DXF exists

`*.step` and `*.dxf` are in `.gitignore`. No STEP and no DXF exist in the worktree. The preparation report read a STEP from `examples/pcb-trial/results/final_r2/export/`, but that file is not retained. B11 must generate both files, keep the exact hash of each file, and commit the generation source and settings. Do not force-add the generated files to bypass `.gitignore`.

### C3. The release manifest cannot carry STEP or DXF

`manifest.schema.json` `outputs[].role` has no `step` and no `dxf` value. The board interface is an input role only. Therefore the Codex "one release record" cannot use the current manifest for these two artifacts without a change. The lead must select one of these:

- Add `step` and `dxf` output roles (schema bump, lead-owned).
- Add a separate mechanical release record for the two files and bind it with hashes.

Do not write an unvalidated role into the manifest.

### C4. The DXF and STEP origin controls differ

`kicad-cli pcb export step` gives `--user-origin`, `--grid-origin`, and `--drill-origin`. `kicad-cli pcb export dxf` gives only `--use-drill-origin`. The two files can therefore use different origins. Select one rule and write it in the reference:

- Put the drill/place origin in the board at the anchor, or
- Transform the DXF coordinates during the comparison.

Record every export switch in the export settings record. The switches control the result. The minimum set is `--user-origin` or `--drill-origin`, `--board-only` or the component set, `--no-dnp`, `--subst-models`, and `--min-distance`.

### C5. Component evidence and models

The toolchain lock has `models: []` and `libraries: []`. B11 must record each model with name, version, license, source URL and hash. An unknown license needs notes. Keep the measured or datasheet height for each reference apart from `height_limits`. A proxy is a conservative envelope. The result cannot claim detailed component clearance.

### C6. Connector insertion space

Define the connector frame origin and the insertion direction. The schema gives `side`, `rotation_deg`, and `insertion_depth_mm`. Test a bottom-side connector with a nonzero rotation and an obstructed insertion space. Test also a reversed orientation.

### C7. Dimension-owner conflict

`dimension_owners` gives one owner for each dimension. Plan section 9 says to detect owner conflicts before either side replaces shared geometry. Add one test: an electrical owner and a mechanical owner disagree on one dimension. The release must refuse with a named conflict.

### C8. The B11 CadQuery example must operate alone

Rule: each skill operates alone. The B11 example cannot import the `cadquery` skill. It can import the CadQuery library only. Put the enclosure fixture in `pcb-design`.

### C9. The tracked draft interface is not the B11 fixture

`examples/pcb-trial/results/final/draft/project/mechanical/board-interface.json` names `board_sha256` `ce5e0f3bd6a68b69ffe3a4982f3d88e66d828e8c5570bcc1bba00d63850c1973`. The accepted board hash is `56f79424...`. Do not reuse the draft interface. Make a new fixture. Keep all B5 files unchanged.

### C10. pcb.py and the copied contracts need a lead assignment

The mechanical team owns new mechanical modules and references. Changes to `pcb.py` and to the copied contracts need a lead assignment first. Ask the lead before the first edit.

## 5. Recommended interface for the lead

| Item | Recommendation |
|---|---|
| New module | `skills/pcb-design/scripts/mechanical.py`. It owns the transform, the geometry comparison, the height evidence, and the release binding. |
| New subcommand | `mechanical` with `--export` and `--fit`. The `pcb.py` wiring is a separate assigned edit. |
| Inputs | The board, `board.yaml`, `mechanical/board-interface.json`, the component evidence, the toolchain lock, and the export settings. |
| Outputs | `out/mechanical/board.step`, `out/mechanical/outline.dxf`, and a mechanical report with each measured error. |
| Transform | The exact `extensions.transform` shape in C1. |
| Release binding | The lead decision in C3. One release ID and the exact hash of each produced file. |
| Fixture | A new asymmetric board in `pcb-design`. A nonzero anchor, unequal holes, a bottom-side part, and a connector frame. |
| Height evidence | A separate record with per-reference revision, evidence type, height, and source hash. |

## 6. Acceptance cases

| ID | Case | Expected result |
|---|---|---|
| T1 | The asymmetric fixture with its declared transform | Pass. Each error is within its tolerance. |
| T2 | A mirrored transform | Fail. Name the transform or geometry check. |
| T3 | A Y-flipped board | Fail. Name the transform check. |
| T4 | A wrong board anchor | Fail. Name the transform check. |
| T5 | A fixture without the bottom-side part | Fail. Name the missing part. |
| T6 | A fixture without the connector frame | Fail. Name the missing frame. |
| T7 | A connector with reversed orientation | Fail. Name the orientation check. |
| T8 | A part inside the connector insertion space | Fail. Name the collision check. |
| T9 | A part over a confirmed height limit | Fail. |
| T10 | An unevidenced height limit | Report `unconfirmed`. Do not pass a detailed fit claim. |
| T11 | A proxy envelope within its limit | Pass the conservative check only. |
| T12 | A changed board or interface hash | Refuse publication. Name the first mismatch. |
| T13 | Regenerated geometry within tolerance, different file hash | Pass the geometry check. Keep the new exact hash. |
| T14 | A changed component revision or supplier profile | Refuse publication. Name the first mismatch. |
| T15 | An owner conflict on one dimension | Refuse. Name the conflict. |
| T16 | A board-only STEP | Report board geometry only. Do not report component clearance. |

## 7. Recommendations to Claude (implementer)

1. Ask the lead about C3, C4 and C10 before you write product code. The three answers change the module.
2. Make the new fixture first. Record the anchor, the source axes, and the target axes.
3. Write the transform extension exactly as in C1. Validate it in the new module. Fail closed.
4. Measure each geometry value and print the error against its tolerance. Keep the measured numbers in the report.
5. Keep `height_limits` as a constraint. Put the measured or datasheet height in a separate record.
6. Keep every B5 file and record unchanged.
7. Use the local image `localhost/cad-skills-pcb:b6`. Do not pull a new image.
8. Keep the module independent of the other skills.
9. Write short tests with one clear failure each. Use `uv`.

## 8. Recommendations to the lead (root)

1. Decide the transform representation (C1). Extension or schema field.
2. Decide the release record for STEP and DXF (C3). Manifest change or a new record.
3. Decide the origin rule for DXF and STEP (C4).
4. Assign the `pcb.py` and copied-contract edits (C10).
5. Confirm the new module and fixture paths.
6. Keep the B5 history and the accepted board unchanged.

## 9. Limits of this review

- I ran no container work except `kicad-cli version` and the two `--help` commands.
- I ran no test.
- This review covers the frozen baseline and the preparation report. It does not accept an implementation.
- I will review the frozen B11 files when Claude publishes a stable version.
