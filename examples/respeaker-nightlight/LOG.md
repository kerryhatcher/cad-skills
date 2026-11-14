# Build log: reSpeaker night light

This log records the sources, the research, the plan, the decisions and the actions for this model. It uses ASD-STE100 Simplified Technical English. New entries go at the end of each section.

## 1. Request

Make a round night light for a desk. The 16 LEDs of an Adafruit NeoPixel Ring must shine up from inside the ring of a reSpeaker Flex XVF3800 Circular-4 mic array. The mic array core board ("motherboard") must be inside the enclosure. The USB-C port must be open to supply power.

The user prints on a Prusa MK4 with Prusament and Jessie (Printed Solid) filaments.

## 2. Sources

| # | Source | Data used |
|---|---|---|
| S1 | Adafruit product 2854: https://www.adafruit.com/product/2854 | NeoPixel Ring 16 x 5050 RGBW, warm white (~3000 K). Outer diameter 44.5 mm, inner diameter 31.75 mm, thickness 3.25 mm, 4.2 g, 5 V DC |
| S2 | Seeed product page: https://www.seeedstudio.com/reSpeaker-Flex-XVF3800-Circular-4-p-6737.html | Product name, SKU 100005504, split design, I2S/USB modes. No dimensions on the page |
| S3 | Seeed wiki, reSpeaker Flex: https://wiki.seeedstudio.com/respeaker_flex_introduction/ | Core board + mic array board. 24-pin, 0.5 mm pitch FPC with latch, 20 cm cable. Core board 4 x M3, circular board 3 x M3. 44 mm mic spacing. Links to the STEP and DXF files |
| S4 | `refs/reSpeaker_xvf3800_flex_circular_260210.step` (Seeed) | Mic ring geometry (see section 3) |
| S5 | `refs/reSpeaker_xvf3800_flex_Separate.step` (Seeed) | Core board geometry (see section 3) |
| S6 | `refs/reSpeaker_xvf3800_flex_circular_2d.dxf`, rendered to `refs/mic_ring_drawing.png` | FPC connector position on the mic ring (not in the STEP model) |
| S7 | `refs/reSpeaker_xvf3800_flex_Separate_2d.dxf`, rendered to `refs/core_board_drawing.png` | FPC connector, 2 x 10 header, screw terminal and XIAO positions on the core board (not all in the STEP model) |
| S8 | RobotShop and ThinkRobotics listings (web search) | "73 mm" circular array diameter. This agrees with S4 (72.5 mm) |
| S9 | The Pi Hut listing (web search) | 102 x 102 x 10 mm: this is the case version, not the bare board. Not used |
| S10 | USB Type-C specification (plug overmold limit 12.35 x 6.5 mm) | Size of the USB-C tunnel |
| S11 | Infineon IM69D130 microphone (part name in S4) | Bottom-port MEMS microphone: sound enters through a hole in the PCB |

Download the Seeed files again with `./fetch_refs.sh`.

## 3. Research results

### 3.1 Mic ring (S4, S6)

- Annulus: outer diameter 72.5 mm, inner diameter 52.5 mm, PCB 1.51 mm. All components are on one side. The highest component is 1.4 mm.
- 3 x M3 holes (3.3 mm) on radius 31.25 mm at 180°, +60° and -60° (Seeed coordinates).
- 4 x IM69D130 microphones at (±22, ±22) mm. Each has a 1.0 mm sound hole through the PCB. The microphones are bottom-port, so sound must reach the flat side of the PCB (the side without components).
- The 24-pin FPC connector is on the component side, near the inner edge, at +X (approximately X 28 to 34 mm, Y ±7.8 mm). The STEP model does not include it. I found it in the DXF drawing.

### 3.2 Core board (S5, S7)

- 70.5 x 52.2 mm, PCB 1.51 mm. 4 x M3 holes on a 62.5 x 44.2 mm rectangle, 4 mm from the edges.
- USB-C (GCT USB4105) on a long edge. Its face is 1.33 mm beyond the board edge. Its centre is 2.78 mm above the board bottom face, and 1.31 mm to the left of the board centre.
- On the same edge: PH2.0 4-pin connector, and a 3.5 mm audio jack that extends 2.0 mm beyond the edge.
- FPC connector on the opposite long edge, near the centre. Not in the STEP model.
- Tallest components: pin headers, 10.55 mm above the board bottom face. Through-hole pins extend 2.8 mm below the board.
- The XIAO ESP32S3 is surface-mounted on the board (flat). Its USB-C extends approximately 1.7 mm beyond the short edge. In the "without XIAO" version, this area is empty.

### 3.3 Fit of the two rings

The NeoPixel ring (outer diameter 44.5 mm) fits inside the hole of the mic ring (52.5 mm). The radial gap is 4 mm on each side. Thus the LEDs can shine up through the centre of the mic ring.

## 4. Plan

1. Measure the boards from the Seeed STEP and DXF files. (Done, section 3.)
2. Write a parametric CadQuery model with three printed parts: base, plate and lid. (Done, A6 to A9.)
3. Do an interference check of the printed parts against the real board models. (Done, A15, A16.)
4. Examine each part with `print-prep` (orientation, supports, wall thickness). (Done, A12 to A14.)
5. Do an FEA of the lid for a hand press on the diffuser, with `structural-analysis`. (Done, A17, A18.)
6. Slice each part for the MK4 with `prusaslicer`. (Done, A19.)

## 5. Design decisions

| # | Decision | Reason |
|---|---|---|
| D1 | Install the mic ring upside down (components down) | The microphones are bottom-port. The flat side must face the lid sound holes |
| D2 | Put the NeoPixel ring on a plate 8 mm below the lid | Distance between the LEDs and the diffuser gives softer light and fewer bright points |
| D3 | Put a white plate between the core board and the LEDs | It reflects light up and hides the electronics. It also holds the NeoPixel ring and the mic ring posts, above all core board components |
| D4 | Turn the mic ring 90° so that its FPC connector points to +Y | The core board FPC connector is on the +Y edge. The cable then goes straight down through a slot in the plate |
| D5 | Move the core board 3 mm toward the USB-C wall | This makes the USB-C tunnel shorter. A larger move puts the board corners into the wall |
| D6 | USB-C tunnel 13.0 x 7.5 mm, about 17 mm long | It accepts all plug overmolds that obey the USB-C specification (S10). The tunnel block goes down to the floor, so it needs no support |
| D7 | 3 columns at 60°, 180° and 300°, radius 44 mm (joined to the wall) | These positions are clear of the core board, the USB-C tunnel and the audio jack |
| D8 | Lid screws from below (M3 x 12) into lid bosses | No screw heads show on the top. The screw clamps column, plate and lid together |
| D9 | Print the lid top face down, with a flat top | No supports. The best surface is on the visible face |
| D10 | Diffuser window 1.2 mm thick, rest of the lid 2.0 mm. Replaced by A23: the center is open | More light through the centre. The 2.0 mm area clamps the mic ring |
| D11 | 1.6 mm sound holes in the lid over the 4 mic ports | A 1.0 mm hole does not print well with a 0.4 mm nozzle |
| D12 | Arc slot in the plate at +X for the NeoPixel wires | The XIAO (a possible LED controller) is below this area |

## 6. Actions

| Step | Action | Result |
|---|---|---|
| A1 | Fetched S1, S2 and S3 | S2 has no dimensions. S3 links the STEP and DXF files |
| A2 | Downloaded the STEP and DXF files (S4 to S7) | 4 files in `refs/` |
| A3 | Measured the mic ring STEP (part names, bounding boxes, PCB holes) | Section 3.1. The FPC connector is not in the model |
| A4 | Measured the core board STEP | Section 3.2. The FPC connector, 2 x 10 header and screw terminal are not in the model |
| A5 | Rendered both DXF drawings to PNG and examined them | Found both FPC connectors and the XIAO position |
| A6 | Wrote `nightlight.py` (parameters, base, plate, lid, assembly with reference boards) | Built with `inspect_model.py` |
| A7 | Built each part with `inspect_model.py --set part=...` | Base and lid valid. Plate not valid |
| A8 | Found the cause: `slot2D` with a width (18 mm) larger than its length (15.8 mm) | Changed the FPC slot to a rectangle with 2 mm corner fillets. Plate valid |
| A9 | Examined the renders (`out/*.png`) | The columns were 1 mm from the wall (radius 42.5 + 4.0 < 47.5). Moved them to radius 44.0, so they join the wall |
| A10 | Wrote `check_fit.py`: overlap of each printed part with each board solid, plus keep-out boxes for parts not in the STEP files | First run is slow (the core board model has 1546 solids) |
| A11 | Changed `check_fit.py` to intersect only the board solids whose bounding box touches the part | Run time 52 s (before: more than 10 min, stopped) |
| A12 | Ran `printability.py` on each part | Plate and lid: no overhangs, walls >= 1.2 mm. Base: 3.3 % of walls < 0.9 mm |
| A13 | Found the cause: 6.5 mm counterbore in an 8 mm column (0.75 mm wall) | Column diameter 9.5 mm. Base minimum wall now 1.0 mm (at the bed edge chamfer), 0 % < 0.9 mm |
| A14 | Examined the base overhang map | The red areas are bridges: foot recesses (10.5 mm), USB-C tunnel roof (13 mm), counterbore roofs (6.5 mm). No support necessary |
| A15 | Ran `check_fit.py` | 1 clash: lid x mic board, 0.657 mm3 |
| A16 | Found the cause: 16 copper test pads, 1.1 x 1.1 x 0.04 mm, on the flat side of the mic board | 0.04 mm is less than the print tolerance. Changed `check_fit.py` to ignore solids thinner than 0.1 mm and report them. Result: PASS |
| A17 | FEA of the lid: 30 N finger press on the diffuser window, Prusament PETG, build direction -Z | Safety factor 10.4 (target 2). Maximum deflection 0.40 mm |
| A18 | Hand calculation of the same case: clamped circular plate, radius 25.5 mm, 1.2 mm, E = 1.5 GPa | Stress 4.97 MPa (FEA 4.54 MPa). Deflection 0.39 mm (FEA 0.40 mm). The FEA agrees |
| A19 | Sliced the three oriented 3MF files for the MK4 (0.20mm STRUCTURAL, 3 perimeters) | All 3: verification OK, no slicer warnings. See section 7 |
| A20 | Added the `section` parameter and rendered the assembly with both boards, cut at X = 0 | `out/section_*.png`. The stack is correct |
| A21 | Tried to make one project 3MF with `prusa-slicer --merge --export-3mf` | PrusaSlicer 2.9.7 stopped with a segmentation fault (exit 139). One object with no `--merge` exported correctly |
| A22 | Wrote `make_3mf.py`: 3 meshes, a bed position for each part, and the MK4 configuration in `Metadata/Slic3r_PE.config` | `out/nightlight_plate.3mf`. A slice of it: verification OK, no warnings, 3 h 34 min, 84.8 g. With no other configuration, PrusaSlicer reads MK4IS, Jessie PETG, 3 perimeters, 20% infill from the file |
| A23 | User request: open the center of the lid. Added `lid_center_open = True`. The 51 mm window is now a through hole (`False` gives the 1.2 mm window again) | Lid valid, volume 2472 mm³ less. The hole (51 mm) is smaller than the mic ring hole (52.5 mm), so the lid still clamps the mic ring. No overhangs, minimum wall 1.21 mm. New lid slice: 43 min 43 s, 16.3 g. New plate 3MF: 3 h 31 min, 81.9 g, no warnings |
| A24 | User request: change the material to PLA. All three parts now use Jessie PLA (`Jessie PLA @PG`: 220 °C nozzle, 60 °C bed). New config, plate 3MF and G-code files | Base 2 h 8 min 47.6 g, plate 39 min 16.5 g, lid 42 min 16.0 g. Plate 3MF: 3 h 27 min, 80.0 g. All: verification OK, no warnings. The 3MF carries `Jessie PLA @PG` |

## 7. Results

### 7.1 Dimensions and clearances (from `check_fit.py`)

| Item | Value |
|---|---|
| Overall size | Diameter 100 mm, height 33.85 mm |
| Tallest core component (STEP) to the plate bottom | 17.55 mm to 18.60 mm (1.05 mm gap) |
| LED top to the lid underside | 8.0 mm |
| USB-C face to the tunnel end | 0.3 mm. The tunnel goes from Y = -30.73 mm to the outer wall at Y = -50 mm |
| Interference with both boards and all keep-out volumes | None (16 contacts with 0.04 mm test pads ignored) |

### 7.2 FEA (lid)

`out/fea_lid.png`, `out/fea_lid.json`. Load: 30 N on the diffuser window. Supports: 3 bosses, mic ring contact face, rim on the base wall. Safety factor 10.35 (in-plane), 33.5 (across layers). The highest stress is at the edge of the 1.2 mm window.

### 7.3 Print files (Prusa MK4, 0.4 mm nozzle, 0.20mm STRUCTURAL, 3 perimeters)

| Part | Orientation | Filament | Infill | Time | Filament | File |
|---|---|---|---|---|---|---|
| Base | As modelled (floor down) | Jessie PLA (opaque color) | 20 % | 2 h 8 min | 47.6 g | `out/base.bgcode` |
| Plate | As modelled | Jessie PLA, white | 20 % | 39 min | 16.5 g | `out/plate.bgcode` |
| Lid | Upside down (top face on the bed), open center (A23) | Jessie PLA | 20 % | 42 min | 16.0 g | `out/lid.bgcode` |

Total: approximately 3 h 30 min and 80 g (A24, Jessie PLA). Each `.bgcode` has an `.ini` beside it that gives the same slice again.

### 7.4 Hardware

| Qty | Item | Use |
|---|---|---|
| 4 | M3 x 6 self-tapping screw (for plastic) | Core board to the base standoffs (2.5 mm pilot holes) |
| 3 | M3 x 12 machine or self-tapping screw | From below, through the column web and the plate, into the lid bosses (2.5 mm pilot holes) |
| 3 | Adhesive bumper, diameter 10 mm, max. 1 mm recess | Feet |
| 3 | Wires (5 V, GND, DIN), approx. 60 mm | NeoPixel ring to its controller |

### 7.5 Assembly procedure

1. Solder 3 wires to the 5V, GND and DIN pads on the back of the NeoPixel ring.
2. Install the core board on the 4 standoffs with the USB-C port in the tunnel. Attach it with 4 M3 x 6 screws.
3. Connect the FPC cable to the core board connector (+Y edge). Fold the extra cable flat in the space between the board edge and the wall.
4. Put the plate on the 3 columns. Push the FPC cable up through the large slot.
5. Put the wires of the NeoPixel ring through the arc slot. Put the ring in the centring ring, LEDs up.
6. Connect the FPC cable to the mic ring. Put the mic ring on the 3 posts, components down, so that the pins go into the M3 holes.
7. Put the lid on the base. Align the bosses with the columns.
8. Turn the assembly over. Install 3 M3 x 12 screws through the counterbores in the bottom.

CAUTION: Do not tighten the lid screws too much. The bosses are plastic, and the threads can strip.

## 8. Open items

- The NeoPixel ring needs a data signal. The XVF3800 core board does not drive it directly. Possible controller: the XIAO ESP32S3 (data pin and 5 V). The user must wire and program it.
- PLA becomes soft at approximately 55 °C. Keep the LED brightness low, so that the parts near the LEDs stay cool.
- Power: 16 RGBW LEDs at full white can take approximately 1 A. Limit the brightness in software for a night light. This keeps the USB current and the heat low.
- The XIAO USB-C port (if installed) is not accessible with the lid on. To program the XIAO, remove the lid and the plate. A second tunnel at +X is possible if necessary.
- The fit of the 3.0 mm pins in the 3.3 mm mic ring holes and the USB-C tunnel position are from the drawings. Print the base and the plate first and do a test fit before you print the lid.
- Acoustic seal: the lid presses on the flat side of the mic ring. For a better seal, add a thin foam ring around each sound hole.
