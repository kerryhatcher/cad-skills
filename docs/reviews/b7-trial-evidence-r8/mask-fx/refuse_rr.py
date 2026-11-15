# /// script
# requires-python = ">=3.10"
# dependencies = ["gerbonara==1.6.3"]
# ///
"""Refuse the macro fixture: report each aperture the measurement does not support."""
from gerbonara import GerberFile
f = GerberFile.open("rr/out/board-F_Mask.gts")
for o in f.objects:
    print(type(o).__name__, type(o.aperture).__name__, getattr(getattr(o.aperture, "macro", None), "name", None))
