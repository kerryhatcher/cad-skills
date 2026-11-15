# /// script
# requires-python = ">=3.10"
# dependencies = ["gerbonara==1.6.3"]
# ///
"""Print the x and y extent of each region of the 4 mil minimum web fixture."""
from gerbonara import GerberFile
f = GerberFile.open("m39merge/out/board-F_Mask.gts")
for o in f.objects:
    xs = [float(p[0]) for p in o.outline]
    ys = [float(p[1]) for p in o.outline]
    print(f"region x=[{min(xs):.6f},{max(xs):.6f}] y=[{min(ys):.6f},{max(ys):.6f}] n={len(xs)}")
