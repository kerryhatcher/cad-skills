# /// script
# requires-python = ">=3.10"
# dependencies = ["gerbonara==1.6.3"]
# ///
"""Report each mask object of the 3.9 mil fixture with and without the 4 mil minimum web setting."""
from gerbonara import GerberFile
for path in ["m39/out/board-F_Mask.gts", "m39merge/out/board-F_Mask.gts"]:
    f = GerberFile.open(path)
    print(path)
    for o in f.objects:
        kind = type(o).__name__
        ap = getattr(o, "aperture", None)
        print(f"  {kind} aperture={type(ap).__name__ if ap is not None else None}")
        if kind == "Region":
            pts = [(round(float(p[0]), 6), round(float(p[1]), 6)) for p in o.outline] if hasattr(o, "outline") else None
            print(f"    region_points={len(pts) if pts else 'n/a'}")
    print(f"  objects={len(f.objects)}")
