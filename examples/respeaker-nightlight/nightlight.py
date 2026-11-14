# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery>=2.5"]
# ///
"""Round desk night light for a reSpeaker Flex XVF3800 Circular-4 and a NeoPixel Ring 16.

Units: millimetres. Origin: the centre of the base bottom face. +Z is up.
The USB-C port of the core board points to -Y.

Parts (print each part separately):
  base   - opaque cup. It holds the core board and has the USB-C tunnel.
  plate  - white disc. It holds the NeoPixel ring and the mic ring posts.
  lid    - top ring (open center by default). It clamps the mic ring and has the mic sound holes.

Stack from the bottom up:
  floor -> core board on standoffs -> plate on 3 columns -> NeoPixel ring on the plate
  -> mic ring (component side down) on 3 posts -> lid.

Hardware:
  4 x M3 x 6 self-tapping screw (core board to base standoffs)
  3 x M3 x 12 screw (from below, through the column web and plate into the lid bosses)

Set `part` to "base", "plate", "lid" or "assembly".
Set `with_boards = True` to add the reference boards (STEP files from Seeed) to the assembly.
"""

import math
from pathlib import Path

import cadquery as cq

# ----------------------------------------------------------------- parameters
part = "assembly"
with_boards = False
section = False  # True cuts the assembly at X = 0 (through the USB-C tunnel)
refs_dir = "refs"  # folder with the Seeed STEP files (see fetch_refs.sh)

# Enclosure
outer_d = 100.0
wall = 2.5
floor_t = 2.0
fit = 0.3  # radial clearance for the plate and the lid skirt in the base

# Core board (reSpeaker Flex XVF3800 core board, from the Seeed STEP and DXF)
core_l = 70.5  # X
core_w = 52.2  # Y
core_t = 1.51
core_hole_dx = 62.5
core_hole_dy = 44.2
core_usb_dx = -1.31  # USB-C centre minus board centre, along X
core_usb_protrusion = 1.33  # USB-C face beyond the board edge
core_usb_z = 2.78  # USB-C centre above the board bottom face
core_part_h = 10.6  # tallest component above the board bottom face (pin headers)
core_shift = 3.0  # move the board toward the USB-C wall
standoff_h = 5.0  # clears through-hole pins (2.8 mm) under the board
standoff_d = 6.5
self_tap_d = 2.5  # pilot hole for an M3 self-tapping screw

# USB-C cable access. The USB-C specification limits the plug overmold to 12.35 x 6.5 mm.
usb_open_w = 13.0
usb_open_h = 7.5
usb_open_r = 2.0
tunnel_wall = 1.6

# Columns (plate support and lid screws)
column_r = 44.0  # radius of the column centres (the columns join the wall)
column_d = 9.5  # 1.5 mm wall around the 6.5 mm counterbore
column_angles = (60.0, 180.0, 300.0)
column_web = 3.0  # material between the counterbore and the plate
screw_clear_d = 3.4
screw_head_d = 6.5

# Plate
plate_t = 2.0
plate_gap = 1.0  # clearance above the tallest core component

# NeoPixel Ring 16 (Adafruit 2854)
ring_od = 44.5
ring_id = 31.75
ring_h = 3.25
seat_clear = 0.25  # radial clearance in the centring ring
seat_wall = 1.2
seat_h = 2.0
led_gap = 8.0  # LED top surface to the lid underside (more gap = softer light)
wire_slot_r = (16.5, 21.5)
wire_slot_angle = 30.0  # total arc of the NeoPixel wire slot, centred on +X

# Mic ring (reSpeaker Flex XVF3800 Circular-4 array board)
mic_od = 72.5
mic_id = 52.5
mic_t = 1.51
mic_hole_r = 31.25
mic_rotation = 90.0  # turns the FPC connector from +X to +Y (toward the core FPC connector)
mic_port_r = 22.0 * math.sqrt(2.0)
mic_port_angles = (45.0, 135.0, 225.0, 315.0)
mic_part_h = 1.4  # components below the board when it is upside down
post_d = 7.0
pin_d = 3.0  # M3 holes are 3.3 mm
pin_h = 1.2  # less than the board thickness, so the lid sits flat
fpc_slot_w = 18.0
fpc_slot_r = (24.2, 40.0)

# Lid
lid_t = 2.0
diffuser_t = 1.2  # thinner centre window over the LEDs
diffuser_d = 51.0  # inside the mic ring hole (52.5)
lid_center_open = True  # True: a hole replaces the thin window (the LEDs show directly)
skirt_h = 3.0
skirt_t = 1.6
lid_chamfer = 0.8
boss_d = 7.0
boss_pilot_depth = 9.0
sound_hole_d = 1.6

# Feet (stick-on bumpers)
foot_d = 10.5
foot_depth = 1.0
foot_r = 36.0
foot_angles = (0.0, 120.0, 240.0)

# ------------------------------------------------------------- derived values
ri = outer_d / 2 - wall
core_x = -core_usb_dx  # board centre X, so that the USB-C is at X = 0
core_y = -core_shift
core_z = floor_t + standoff_h  # board bottom face
core_top = core_z + core_part_h
plate_z = core_top + plate_gap  # plate bottom face
plate_top = plate_z + plate_t
led_top = plate_top + ring_h
lid_z = led_top + led_gap  # lid underside = mic board top (flat side)
mic_bottom = lid_z - mic_t
post_h = mic_bottom - plate_top
base_h = lid_z
usb_face_y = core_y - core_w / 2 - core_usb_protrusion
usb_z = core_z + core_usb_z
tunnel_y = usb_face_y - 0.3  # inner end of the tunnel, 0.3 mm from the USB-C face

core_holes = [
    (core_x + sx * core_hole_dx / 2, core_y + sy * core_hole_dy / 2)
    for sx in (-1, 1)
    for sy in (-1, 1)
]

assert post_h > mic_part_h + 1.0, "the posts are too short for the mic board components"
assert lid_z - skirt_h > plate_top, "the lid skirt hits the plate"
assert math.hypot(core_x + core_l / 2, core_y - core_w / 2) < ri - 0.5, "the core board does not fit"
assert ring_od / 2 + seat_clear + seat_wall < mic_id / 2, "the NeoPixel seat does not fit in the mic ring hole"
assert pin_h < mic_t, "the pins must not touch the lid"


def polar(r: float, a_deg: float) -> tuple[float, float]:
    a = math.radians(a_deg)
    return (r * math.cos(a), r * math.sin(a))


def disc(d: float, h: float, z: float = 0.0, xy=(0.0, 0.0)) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z).center(*xy).circle(d / 2).extrude(h)


# --------------------------------------------------------------------- parts
def make_base() -> cq.Workplane:
    body = disc(outer_d, base_h).cut(disc(2 * ri, base_h, floor_t))

    # Standoffs for the core board.
    for xy in core_holes:
        body = body.union(disc(standoff_d, standoff_h + 0.5, floor_t - 0.5, xy))

    # Columns: they hold the plate. A counterbore from below gives access to the lid screws.
    for a in column_angles:
        xy = polar(column_r, a)
        body = body.union(disc(column_d, plate_z - floor_t + 0.5, floor_t - 0.5, xy))
    # Cut the column parts that go outside the wall.
    body = body.intersect(disc(outer_d, base_h))

    # USB-C tunnel block, from the floor to above the opening (no overhang).
    tunnel_top = usb_z + usb_open_h / 2 + tunnel_wall
    block_w = usb_open_w + 2 * tunnel_wall
    block = (
        cq.Workplane("XY")
        .box(block_w, ri - abs(tunnel_y) + 1.0, tunnel_top - floor_t + 0.5, centered=(True, False, False))
        .translate((0, -ri - 1.0, floor_t - 0.5))
    )
    body = body.union(block)

    # Holes.
    for xy in core_holes:
        body = body.cut(disc(self_tap_d, standoff_h, core_z - standoff_h + 1.0, xy))
    for a in column_angles:
        xy = polar(column_r, a)
        cb_top = plate_z - column_web
        body = body.cut(disc(screw_head_d, cb_top + 1.0, -1.0, xy))
        body = body.cut(disc(screw_clear_d, base_h, -1.0, xy))
    usb_cut = (
        cq.Workplane("XZ")
        .workplane(offset=-tunnel_y)  # the XZ normal is -Y, so this plane is at Y = tunnel_y
        .center(0, usb_z)
        .rect(usb_open_w, usb_open_h)
        .extrude(outer_d)  # toward -Y, through the wall
        .edges("|Y")
        .fillet(usb_open_r)
    )
    body = body.cut(usb_cut)
    for a in foot_angles:
        body = body.cut(disc(foot_d, foot_depth + 0.01, -0.01, polar(foot_r, a)))

    # Chamfer the bed edge to compensate for the elephant foot.
    body = body.faces("<Z").edges(cq.selectors.RadiusNthSelector(-1)).chamfer(0.6)
    return body


def make_plate() -> cq.Workplane:
    plate_d = 2 * (ri - fit)
    plate = disc(plate_d, plate_t, plate_z)

    # NeoPixel centring ring.
    seat_id = ring_od + 2 * seat_clear
    plate = plate.union(
        disc(seat_id + 2 * seat_wall, seat_h + 0.5, plate_top - 0.5).cut(disc(seat_id, seat_h + 1, plate_top - 0.6))
    )

    # Mic ring posts with locating pins.
    for k in range(3):
        a = mic_rotation + 180.0 + 120.0 * k
        xy = polar(mic_hole_r, a)
        plate = plate.union(disc(post_d, post_h + 0.5, plate_top - 0.5, xy))
        pin = disc(pin_d, pin_h, mic_bottom, xy).faces(">Z").edges().chamfer(0.3)
        plate = plate.union(pin)

    # Screw holes at the columns.
    for a in column_angles:
        plate = plate.cut(disc(screw_clear_d, plate_t + 2, plate_z - 1, polar(column_r, a)))

    # FPC slot toward the core board FPC connector.
    r0, r1 = fpc_slot_r
    slot = (
        cq.Workplane("XY")
        .workplane(offset=plate_z - 1)
        .center(0, (r0 + r1) / 2)
        .rect(fpc_slot_w, r1 - r0)
        .extrude(plate_t + 2)
        .edges("|Z")
        .fillet(2.0)
    )
    plate = plate.cut(slot)

    # Arc slot for the NeoPixel wires (5V, GND, DIN). Put the ring pads over this slot.
    a0, a1 = -wire_slot_angle / 2, wire_slot_angle / 2
    ro, rin = wire_slot_r[1], wire_slot_r[0]
    pts_out = [polar(ro, a0 + (a1 - a0) * i / 8) for i in range(9)]
    pts_in = [polar(rin, a1 - (a1 - a0) * i / 8) for i in range(9)]
    wire_slot = cq.Workplane("XY").workplane(offset=plate_z - 1).polyline(pts_out + pts_in).close().extrude(plate_t + 2)
    plate = plate.cut(wire_slot)
    return plate


def make_lid() -> cq.Workplane:
    lid = disc(outer_d, lid_t, lid_z).faces(">Z").edges().chamfer(lid_chamfer)

    # Skirt that locates the lid in the base.
    skirt_od = 2 * (ri - fit)
    lid = lid.union(disc(skirt_od, skirt_h + 0.5, lid_z - skirt_h).cut(disc(skirt_od - 2 * skirt_t, skirt_h + 2, lid_z - skirt_h - 1)))

    # Screw bosses that press on the plate.
    boss_h = lid_z - plate_top
    for a in column_angles:
        xy = polar(column_r, a)
        lid = lid.union(disc(boss_d, boss_h + 0.5, plate_top, xy))
    lid = lid.intersect(disc(outer_d, lid_t + boss_h + 1, plate_top - 0.1))
    for a in column_angles:
        lid = lid.cut(disc(self_tap_d, boss_pilot_depth, plate_top - 0.01, polar(column_r, a)))

    if lid_center_open:
        # Open center: remove all material in the window area.
        lid = lid.cut(disc(diffuser_d, lid_t + 2, lid_z - 1))
    else:
        # Thinner diffuser window over the LEDs (recess in the underside).
        lid = lid.cut(disc(diffuser_d, lid_t - diffuser_t, lid_z - 0.01))

    # Sound holes over the bottom-port microphones.
    for a in mic_port_angles:
        lid = lid.cut(disc(sound_hole_d, lid_t + 2, lid_z - 1, polar(mic_port_r, a)))
    return lid


# ------------------------------------------------------- reference components
def make_neopixel() -> cq.Workplane:
    pcb = disc(ring_od, 1.6, plate_top).cut(disc(ring_id, 3, plate_top - 0.5))
    r_led = (ring_od + ring_id) / 4
    for k in range(16):
        x, y = polar(r_led, 360.0 / 16 * k)
        led = cq.Workplane("XY").box(5.0, 5.0, ring_h - 1.6, centered=(True, True, False)).rotate(
            (0, 0, 0), (0, 0, 1), 360.0 / 16 * k
        )
        pcb = pcb.union(led.translate((x, y, plate_top + 1.6)))
    return pcb


def load_board(name: str) -> cq.Shape | None:
    p = Path(__file__).resolve().parent / refs_dir / name if "__file__" in globals() else Path(refs_dir) / name
    if not p.exists():
        return None
    return cq.importers.importStep(str(p)).val()


def place_core(shape: cq.Shape) -> cq.Shape:
    # Seat the STEP model: board centre (80.25, -68.61) in Seeed coordinates.
    return shape.translate(cq.Vector(core_x - 80.25, core_y + 68.61, core_z))


def place_mic(shape: cq.Shape) -> cq.Shape:
    # Turn the board upside down (rotate 180 degrees about X), turn it about Z, then lift it.
    s = shape.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180)
    s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), mic_rotation)
    return s.translate(cq.Vector(0, 0, lid_z))


def cut_section(shape) -> cq.Shape | None:
    """Keep the half of the shape at X <= 0 (section through the USB-C tunnel).

    For a board compound, the function cuts only the solids that cross X = 0. This is
    much faster than one boolean operation on 1500 solids.
    """
    if isinstance(shape, cq.Workplane):
        shape = shape.val()
    half = cq.Solid.makeBox(200, 200, 200, cq.Vector(-200, -100, -50))
    keep = []
    for s in shape.Solids():
        bb = s.BoundingBox()
        if bb.xmax <= 0:
            keep.append(s)
        elif bb.xmin < 0:
            keep.extend(s.intersect(half).Solids())
    return cq.Compound.makeCompound(keep) if keep else None


def make_assembly() -> cq.Assembly:
    assy = cq.Assembly(name="nightlight")
    items = [
        (make_base(), "base", cq.Color(0.15, 0.15, 0.17)),
        (make_plate(), "plate", cq.Color(0.95, 0.95, 0.95)),
        (make_neopixel(), "neopixel", cq.Color(0.2, 0.2, 0.2)),
        (make_lid(), "lid", cq.Color(0.85, 0.9, 1.0, 0.45)),
    ]
    if with_boards:
        core = load_board("reSpeaker_xvf3800_flex_Separate.step")
        mic = load_board("reSpeaker_xvf3800_flex_circular_260210.step")
        if core is not None:
            items.append((place_core(core), "core_board", cq.Color(0.1, 0.4, 0.15)))
        if mic is not None:
            items.append((place_mic(mic), "mic_board", cq.Color(0.1, 0.3, 0.6)))
    for obj, name, color in items:
        if section:
            obj = cut_section(obj)
            if obj is None:
                continue
        assy.add(obj, name=name, color=color)
    return assy


builders = {"base": make_base, "plate": make_plate, "lid": make_lid}
if part in builders:
    show_object(builders[part](), name=part)
else:
    show_object(make_assembly(), name="nightlight")
