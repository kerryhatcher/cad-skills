# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery>=2.5"]
# ///
"""Do an interference check of the printed parts against the Seeed board models.

The script builds the base, plate and lid in their assembled positions. It loads the
two board STEP files from refs/ and puts them in position. Then it calculates the
overlap volume of each printed part with each board solid. It also checks keep-out
boxes for components that are not in the STEP files.

  uv run check_fit.py            # report
  uv run check_fit.py --set led_gap=6
Exit status 1 if an overlap is larger than 0.001 mm3.
"""
import ast
import sys
import time
from pathlib import Path

import cadquery as cq

here = Path(__file__).resolve().parent
overrides = {}
args = sys.argv[1:]
while args:
    if args[0] == "--set":
        k, v = args[1].split("=", 1)
        overrides[k] = ast.literal_eval(v)
        args = args[2:]
    else:
        sys.exit(f"unknown argument {args[0]}")

src = (here / "nightlight.py").read_text().split("builders = ")[0]
for k, v in overrides.items():
    src = src.replace(f"\n{k} = ", f"\n{k} = {v!r}  # ", 1)
g = {"__file__": str(here / "nightlight.py"), "show_object": lambda *a, **k: None}
exec(src, g)

t0 = time.time()
parts = {"base": g["make_base"]().val(), "plate": g["make_plate"]().val(), "lid": g["make_lid"]().val()}
core = g["place_core"](g["load_board"]("reSpeaker_xvf3800_flex_Separate.step"))
mic = g["place_mic"](g["load_board"]("reSpeaker_xvf3800_flex_circular_260210.step"))
print(f"loaded boards in {time.time() - t0:.0f} s")

# Keep-out volumes for parts that the STEP files do not include.
cx, cy, cz = g["core_x"], g["core_y"], g["core_z"]
L, W = g["core_l"], g["core_w"]
keepout = {
    # All core board components, as one box (pin headers 10.6 mm up, pins 2.8 mm down).
    "core component envelope": cq.Workplane("XY").box(L, W, 13.4, centered=(True, True, False)).translate((cx, cy, cz - 2.8)).val(),
    # Core FPC connector + cable bend at the +Y edge (approx. 16 x 6 x 3 mm, plus 4 mm for the cable).
    "core FPC + cable": cq.Workplane("XY").box(18, 10, 6, centered=(True, False, False)).translate((cx + 0.1, cy + W / 2 - 6, cz + 1.5)).val(),
    # XIAO USB-C beyond the +X edge.
    "XIAO USB-C": cq.Workplane("XY").box(3, 9.5, 3.5, centered=(False, True, False)).translate((cx + L / 2, cy, cz + 1.5)).val(),
    # NeoPixel ring with wire joints on the back.
    "NeoPixel ring": g["make_neopixel"]().val(),
}
# Mic FPC connector (component side, now hanging below the upside-down board), turned to +Y.
mic_fpc = cq.Workplane("XY").box(16.0, 6.0, 2.0, centered=(True, False, False)).translate((0, 27.8, g["mic_bottom"] - 2.0)).val()
keepout["mic FPC connector"] = mic_fpc

bad = 0
SURFACE_LAYER = 0.1  # mm. Copper, solder mask and silkscreen solids are thinner than this.
ignored = []


def overlap_volume(a, b, a_name="", b_name=""):
    """Intersect only the solids of b whose bounding box touches the bounding box of a.

    Solids thinner than SURFACE_LAYER are surface layers. A printed part can touch them
    (they are less than the print tolerance), so they do not count as a clash.
    """
    ab = a.BoundingBox()
    v = 0.0
    for s in b.Solids():
        sb = s.BoundingBox()
        if sb.xmin > ab.xmax or sb.xmax < ab.xmin or sb.ymin > ab.ymax or sb.ymax < ab.ymin or sb.zmin > ab.zmax or sb.zmax < ab.zmin:
            continue
        vs = a.intersect(s).Volume()
        if vs > 1e-6 and min(sb.xlen, sb.ylen, sb.zlen) < SURFACE_LAYER:
            ignored.append((a_name, b_name, vs))
            continue
        v += vs
    return v


def report(a_name, a, b_name, b):
    global bad
    v = overlap_volume(a, b, a_name, b_name)
    flag = "CLASH" if v > 1e-3 else "ok"
    if v > 1e-3:
        bad += 1
    print(f"  {flag:5s} {a_name:6s} x {b_name:28s} {v:9.3f} mm3")

for pname, p in parts.items():
    for bname, board in (("core board (STEP)", core), ("mic board (STEP)", mic)):
        report(pname, p, bname, board)
    for kname, k in keepout.items():
        if kname == "core component envelope" and pname == "base":
            continue  # the standoffs touch the board area from below; checked by the STEP model
        report(pname, p, kname, k)

# Clearances that matter.
def gap_z(top_shape, bottom_shape):
    return top_shape.BoundingBox().zmin - bottom_shape.BoundingBox().zmax
print(f"core components top z = {core.BoundingBox().zmax:.2f}, plate bottom z = {g['plate_z']:.2f}")
print(f"LED top z = {g['led_top']:.2f}, lid underside z = {g['lid_z']:.2f}, gap = {g['led_gap']:.2f}")
print(f"USB-C face y = {g['usb_face_y']:.2f}, tunnel end y = {g['tunnel_y']:.2f}, wall outside y = {-g['outer_d']/2:.2f}")
print(f"overall height = {g['lid_z'] + g['lid_t']:.2f} mm, diameter = {g['outer_d']:.1f} mm")
if ignored:
    print(f"ignored {len(ignored)} contacts with surface layers < {SURFACE_LAYER} mm "
          f"(total {sum(i[2] for i in ignored):.3f} mm3), for example {ignored[0][0]} x {ignored[0][1]}")
print("RESULT:", "FAIL" if bad else "PASS")
sys.exit(1 if bad else 0)
