#!/usr/bin/env python3
"""Read the holes, the placement and the copper layers of a saved board with the installed pcbnew.

Worker for the container runtime. It runs with `/usr/bin/python3` and never writes the board.

  python3 /worker/board_inventory.py BOARD.kicad_pcb

Every structured record goes to standard output as one JSON object. That includes the
inventory, an error record and a refusal record. pcbnew diagnostics go to standard error.
The worker keeps KiCad's transformed coordinates in millimeters. It lists each object,
so that the caller can compare multisets. It refuses geometry that the measured export
subset does not cover. A refusal record names each refused object, and the worker exits
with status 2.

Exit status: 0 inventory written, 2 unsupported geometry or incorrect input, 3 pcbnew failure.
"""

import json
import sys

REFUSED_VIA = "via that is not through the board"


def refuse(objects, status=2):
    print(json.dumps({"unsupported": objects}, sort_keys=True))
    return status


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"error": "board_inventory: give the board path"}))
        return 2
    try:
        import pcbnew
    except ImportError as err:
        print(json.dumps({"error": f"pcbnew is not importable: {err}"}))
        return 3
    try:
        board = pcbnew.LoadBoard(argv[1])
    except Exception as err:  # pcbnew raises several exception types.
        print(json.dumps({"error": f"pcbnew cannot load the board: {err}"}))
        return 3
    mm = pcbnew.ToMM
    copper = [board.GetLayerName(layer) for layer in board.GetEnabledLayers().CuStack()]
    attrs = {pcbnew.PAD_ATTRIB_PTH: "pth", pcbnew.PAD_ATTRIB_NPTH: "npth",
             pcbnew.PAD_ATTRIB_SMD: "smd", pcbnew.PAD_ATTRIB_CONN: "conn"}
    footprints, holes, unsupported = [], [], []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        pos = fp.GetPosition()
        footprints.append({"ref": fp.GetReference(), "x": round(mm(pos.x), 6), "y": round(mm(pos.y), 6),
                           "rot": round(fp.GetOrientationDegrees(), 6), "side": "bottom" if fp.IsFlipped() else "top"})
        for pad in fp.Pads():
            drill = pad.GetDrillSize()
            if drill.x <= 0:
                continue
            attr = attrs.get(pad.GetAttribute(), str(pad.GetAttribute()))
            name = f"pad {fp.GetReference()}.{pad.GetNumber()}"
            if drill.x != drill.y or pad.GetDrillShape() != pcbnew.PAD_DRILL_SHAPE_CIRCLE:
                unsupported.append({"object": name, "reason": "slot or oval drill"})
                continue
            if attr not in ("pth", "npth"):
                unsupported.append({"object": name, "reason": f"unsupported drilled pad type {attr}"})
                continue
            q = pad.GetPosition()
            holes.append({"kind": "pad", "object": name, "attr": attr, "x": round(mm(q.x), 6), "y": round(mm(q.y), 6),
                          "diameter": round(mm(drill.x), 6)})
    for track in board.GetTracks():
        if track.Type() != pcbnew.PCB_VIA_T:
            continue
        name = f"via {track.m_Uuid.AsString()}"
        top, bottom = board.GetLayerName(track.TopLayer()), board.GetLayerName(track.BottomLayer())
        if {top, bottom} != {copper[0], copper[-1]}:
            unsupported.append({"object": name, "reason": REFUSED_VIA})
            continue
        q = track.GetPosition()
        holes.append({"kind": "via", "object": name, "attr": "pth", "x": round(mm(q.x), 6), "y": round(mm(q.y), 6),
                      "diameter": round(mm(track.GetDrillValue()), 6)})
    if unsupported:
        return refuse(unsupported)
    print(json.dumps({"kicad": pcbnew.GetBuildVersion(), "copper_layers": copper, "footprints": footprints,
                      "holes": holes}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
