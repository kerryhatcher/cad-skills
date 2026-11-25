# B11 bound export trial: Pi

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Basis: the lead decision record `b11-decisions-root.md`, items 5 and 7. The lead authorized the frame and hole-export trials. This trial gives the measured exporter frame and the DXF hole method for the consolidated interface.

No product file changed. All trial files are under `/tmp/b11-trial`.

## 1. Environment and inputs

| Item | Value |
|---|---|
| Image | `localhost/cad-skills-pcb:b6` |
| Image ID | `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f` |
| KiCad CLI | 10.0.5 |
| Accepted board | `examples/pcb-trial/results/final_r2/trial.kicad_pcb`, SHA-256 `56f794242345dd3950d5bd066bea6f2a1d1740c5adfc7152651667210297bd94` |
| Board thickness | 1.6 mm |
| Edge.Cuts | `(100, 100)` to `(140, 125)` |
| MH1 | `(103, 103)`, 3.2 mm, not plated |
| MH2 | `(137, 122)`, 3.2 mm, not plated |
| Auxiliary origin | absent from the setup block, so the drill/place origin is `(0, 0)` |
| Template cross-check | `skills/pcb-design/templates/rc-bare-board/kicad/board.kicad_pcb`, 1.6 mm |

The accepted board was copied to `/tmp/b11-trial/in`. The source board was not changed.

## 2. Commands

```text
kicad-cli pcb export step --drill-origin --board-only -o board.step trial.kicad_pcb
kicad-cli pcb export step --drill-origin --board-only --no-extra-pad-thickness -o b_nopad.step trial.kicad_pcb
kicad-cli pcb export step --drill-origin --board-only --include-soldermask -o d_mask.step trial.kicad_pcb
kicad-cli pcb export step --drill-origin --no-components -o c_nocomp.step trial.kicad_pcb
kicad-cli pcb export dxf --use-drill-origin --output-units mm -l Edge.Cuts --mode-single -o outline.dxf trial.kicad_pcb
kicad-cli pcb export dxf --use-drill-origin --output-units mm -l Edge.Cuts --drill-shape-opt 0 --mode-single -o outline_opt0.dxf trial.kicad_pcb
kicad-cli pcb export dxf --use-drill-origin --output-units mm -l Edge.Cuts,F.Cu,B.Cu --mode-single -o copper.dxf trial.kicad_pcb
kicad-cli pcb export drill --drill-origin plot --excellon-units mm -o drill/ trial.kicad_pcb
```

## 3. Measured results

### 3.1 Export frame

The three formats use the same axis map: X unchanged and Y negated.

| Format | Measured |
|---|---|
| STEP | board body X `100..140`, Y `-125..-100` |
| DXF | `LINE (100,-100) -> (140,-100) -> (140,-125) -> ...` |
| Excellon | T3 NPTH at `X103.0Y-103.0` and `X137.0Y-122.0` |

So `X_step = X_kicad` and `Y_step = -Y_kicad`. This matches the lead formula `y_target = origin_mm.y + anchor.y - y_source`.

The STEP also holds global points `(0, 0, 0)` and `(0, 0, 1.51)`. They are not board geometry. A measurement must select the board body by its X and Y range. The global bounding box is `X 0..140` and `Y -125..0` and would give a wrong result.

The anchor must equal the drill/place origin. The accepted board has the default origin `(0, 0)`. The fixture must set the origin to the anchor.

### 3.2 DXF holes

`-l Edge.Cuts` with the default `--drill-shape-opt 2` produced four circles on the Edge.Cuts layer:

| Center (DXF) | Radius | Hole |
|---|---|---|
| `(137, -122)` | 1.6 | MH2, 3.2 mm NPTH |
| `(103, -103)` | 1.6 | MH1, 3.2 mm NPTH |
| `(105, -112.5)` | 0.5 | connector PTH, 1.0 mm |
| `(105, -115.04)` | 0.5 | connector PTH, 1.0 mm |

The switch controls the result:

| `--drill-shape-opt` | Circle count |
|---|---|
| 0 | 0 |
| 1 | 4 |
| 2 (default) | 4 |

So an Edge.Cuts DXF does carry the through holes when the switch is not 0. The plan's "DXF for the outline and holes" is possible in one DXF. The team must record the switch. A separate DXF role or the drill file is also correct.

### 3.3 STEP holes

The board-only STEP holds four cylindrical faces: two with radius 1.6 and two with radius 0.5. The accepted interface lists only the two 3.2 mm mounting holes. The two 1.0 mm connector holes are extra. A comparison of the STEP hole set with the interface hole set must reconcile the two sets, or the fixture interface must list all through holes.

### 3.4 STEP Z datum and extent

| Export | Z values | Z span |
|---|---|---|
| `--board-only` (substrate) | `0.0`, `1.51` | 1.51 |
| `--board-only` (all points) | `-0.046`, `0.0`, `1.51` | 1.556 |
| `--board-only --no-extra-pad-thickness` | `-0.036`, `0.0`, `1.51` | 1.546 |
| `--board-only --include-soldermask` | `-0.050`, `0.0`, `1.51`, `1.560` | 1.610 |
| Template `--board-only` | `0.0`, `1.51` | 1.51 |
| Template `--board-only --include-pads` | `-0.046`, `-0.04`, `0.0`, `1.51`, `1.55` | 1.596 |

The declared thickness is 1.6 mm. The board-only substrate is 1.51 mm on both boards. The difference is 0.09 mm. That is nine times the 0.01 mm tolerance.

Root imported `board.step` and `b_nopad.step` with CadQuery (probe `b11-body-probe-root.py`, exit 0). Each file holds one valid solid with Z `0..1.51`. The `1.556` value in the table comes from text control points outside that solid. The imported substrate solid is 1.51 mm. C05 must use the imported solid, not the text points.

Therefore C05 must not compare the raw STEP Z span with `thickness_mm`. The interface must define one method:

- Measure the substrate face to face and state the expected 1.51 mm, or
- Include the pads with the explicit switches and measure about 1.60 mm, or
- Measure a calibration value from the fixture and bind that value.

State the Z datum. The padded export gives `1.55` for the top and `-0.046` for the bottom on the template.

### 3.5 Excellon holes

`--drill-origin plot --excellon-units mm` gave:

```text
T1C0.300   Plated,PTH,ViaDrill
T2C1.000   Plated,PTH,ComponentDrill
T3C3.200   NonPlated,NPTH,ComponentDrill
X103.0Y-103.0   X137.0Y-122.0   (T3)
X105.0Y-112.5   X105.0Y-115.04  (T2)
X127.5Y-106.0   X127.5Y-118.0   (T1)
```

The plated flag is in the `AperFunction` comment for each aperture. C04 can read it. The coordinates use the same Y negation.

## 4. Consequences for the consolidated interface

1. State the frame as X unchanged and Y negated, relative to the drill/place origin. Select the board body and exclude the STEP global points.
2. Redefine C05. Do not use the raw Z span against `thickness_mm`. Use the measured substrate method and state the expected value. Record the switch set.
3. Reconcile the C02 and C03 hole set with the interface hole set. The exports hold more through holes than the accepted interface.
4. State `--drill-shape-opt` (2) in the export settings. Use a dedicated DXF role or the drill file for the holes. Do not select `0`.
5. Read the C04 plated flag from the Excellon aperture comment.
6. Set the fixture auxiliary origin to the anchor. The accepted board uses `(0, 0)`.
7. Report the measured frame in the trial report. Freeze it before the acceptance tests, per lead item 5.

## 5. Limits

- I examined the STEP as text. A CadQuery import can examine the face and cylinder values.
- The accepted board and the template are not the B11 fixture `mech-fit-a`.
- The trial shows the exporter behavior. It does not accept an implementation.
- No container image was pulled. The local image was used.

## 6. Reproduction

```bash
podman run --rm --security-opt label=disable -v /tmp/b11-trial:/work -w /work \
  localhost/cad-skills-pcb:b6 bash -c 'kicad-cli pcb export step --drill-origin --board-only -o board.step in/trial.kicad_pcb'
```
