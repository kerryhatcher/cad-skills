#!/usr/bin/env python3
"""Measure via spans in the saved board with pcbnew. Do not change the board."""

import hashlib
import json
import sys
from pathlib import Path


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"error": "Give one board path."}))
        return 2
    try:
        import pcbnew
        path = Path(argv[1])
        raw = path.read_bytes()
        board = pcbnew.LoadBoard(str(path))
        copper = list(board.GetEnabledLayers().CuStack())
        if len(copper) < 2:
            raise ValueError("The board has fewer than two copper layers.")
        outer = {copper[0], copper[-1]}
        vias = []
        for item in board.GetTracks():
            if item.Type() != pcbnew.PCB_VIA_T:
                continue
            ends = {item.TopLayer(), item.BottomLayer()}
            if not ends.issubset(set(copper)) or len(ends) != 2:
                raise ValueError("A via has an invalid copper span.")
            kind = "through" if ends == outer else "blind" if ends & outer else "buried"
            vias.append({"uuid": item.m_Uuid.AsString(), "construction": kind,
                         "top": board.GetLayerName(item.TopLayer()),
                         "bottom": board.GetLayerName(item.BottomLayer())})
        print(json.dumps({"board_sha256": hashlib.sha256(raw).hexdigest(),
                          "copper_layers": [board.GetLayerName(x) for x in copper],
                          "vias": sorted(vias, key=lambda x: x["uuid"])}, sort_keys=True))
        return 0
    except ValueError as err:
        print(json.dumps({"error": str(err)}))
        return 2
    except Exception as err:
        print(json.dumps({"error": f"The via measurement failed: {err}"}))
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
