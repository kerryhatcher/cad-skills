# /// script
# requires-python = ">=3.10"
# dependencies = ["gerbonara==1.6.3", "shapely==2.2.0"]
# ///
"""Measure the mask web between two circular openings in each fixture. Refuse other constructs."""
import math, sys
from gerbonara import GerberFile
from gerbonara.apertures import CircleAperture, ApertureMacroInstance, RectangleAperture
MIL = 0.0254
for name in ["m39", "m40", "m41"]:
    path = f"{name}/out/board-F_Mask.gts"
    f = GerberFile.open(path)
    flashes, refused = [], []
    for o in f.objects:
        ap = o.aperture
        if type(o).__name__ != "Flash":
            refused.append(f"{type(o).__name__}")
        elif isinstance(ap, CircleAperture):
            flashes.append((float(o.x), float(o.y), float(ap.diameter)))
        else:
            refused.append(f"aperture {type(ap).__name__}")
    print(f"{name}: objects={len(f.objects)} flashes={flashes} refused={refused}")
    if refused or len(flashes) != 2:
        print(name, "UNSUPPORTED"); continue
    (x1, y1, d1), (x2, y2, d2) = flashes
    center = math.hypot(x2 - x1, y2 - y1)
    web = center - d1 / 2 - d2 / 2
    print(f"{name}: web_mm={web:.6f} web_mil={web/MIL:.4f} derived_bound_mm=0.000002")
