#!/usr/bin/env python3
"""Measure the owned B7 label. This worker is test evidence, not a product silk inspector."""
import hashlib
import json
import sys
from pathlib import Path
import pcbnew

path = Path(sys.argv[1])
raw = path.read_bytes()
board = pcbnew.LoadBoard(str(path))
rows = []
for item in board.GetDrawings():
    if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() == "B7":
        rows.append({"text": item.GetText(), "layer": board.GetLayerName(item.GetLayer()),
                     "stroke_nm": item.GetTextThickness(), "uuid": item.m_Uuid.AsString()})
print(json.dumps({"board_sha256": hashlib.sha256(raw).hexdigest(), "labels": rows}, sort_keys=True))
