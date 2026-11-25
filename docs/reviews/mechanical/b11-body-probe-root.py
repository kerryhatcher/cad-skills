# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["cadquery"]
# ///
"""Measure imported STEP solids without text-point assumptions."""
import json
from pathlib import Path
import cadquery as cq

for path in [Path('/tmp/b11-trial/out/board.step'), Path('/tmp/b11-trial/out/b_nopad.step')]:
    solids = cq.importers.importStep(str(path)).solids().vals()
    rows = []
    for solid in solids:
        box = solid.BoundingBox()
        rows.append({'valid': solid.isValid(), 'volume': solid.Volume(),
                     'x': [box.xmin, box.xmax], 'y': [box.ymin, box.ymax],
                     'z': [box.zmin, box.zmax], 'thickness': box.zlen})
    print(json.dumps({'file': str(path), 'solids': rows}))
