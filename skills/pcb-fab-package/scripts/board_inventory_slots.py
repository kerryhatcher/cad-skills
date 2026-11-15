#!/usr/bin/env python3
"""Read the holes, the slots, the outline and the copper layers of a saved board with the installed pcbnew.

Owned derivative of the B6 worker `board_inventory.py`. The difference is the slot handling: an oblong
drill is reported as a slot with its endpoints, its minor and major dimensions, and its pad attribute. The
B6 worker refuses such a drill. The outline dimensions exclude the Edge.Cuts stroke width.

  python3 /worker/board_inventory_slots.py BOARD.kicad_pcb

Every structured record goes to standard output as one JSON object. pcbnew diagnostics go to standard error.
The worker never writes the board. Coordinates are millimetres, rounded to 6 decimals (1 nanometre).

Exit status: 0 inventory written, 2 unsupported geometry or incorrect input, 3 pcbnew failure.
"""

import json
import math
import sys

REFUSED_VIA = "via that is not through the board"
ROUND_DIGITS = 6


def refuse(objects, status=2):
    print(json.dumps({"unsupported": objects}, sort_keys=True))
    return status


def _mm(pcbnew, value):
    return round(pcbnew.ToMM(value), ROUND_DIGITS)


def _slot_endpoints(pcbnew, pad, drill):
    """The centre of each end arc, in millimetres. The major axis follows the pad orientation."""
    center = pad.GetPosition()
    angle = math.radians(pad.GetOrientationDegrees())
    major_nm = max(drill.x, drill.y)
    minor_nm = min(drill.x, drill.y)
    if drill.x < drill.y:
        angle += math.pi / 2  # the drill height is the major axis
    half = (major_nm - minor_nm) / 2.0
    cx, cy = pcbnew.ToMM(center.x), pcbnew.ToMM(center.y)
    # KiCad angles turn counterclockwise on the y-down board plane, so the y step is negated.
    dx, dy = half * math.cos(angle) / 1e6, -half * math.sin(angle) / 1e6
    p1 = [round(cx - dx, ROUND_DIGITS), round(cy - dy, ROUND_DIGITS)]
    p2 = [round(cx + dx, ROUND_DIGITS), round(cy + dy, ROUND_DIGITS)]
    return p1, p2, pcbnew.ToMM(minor_nm), pcbnew.ToMM(major_nm)


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"error": "board_inventory_slots: give the board path"}))
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
    oblong = getattr(pcbnew, "PAD_DRILL_SHAPE_OBLONG", None)
    footprints, holes, slots, unsupported = [], [], [], []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        pos = fp.GetPosition()
        footprints.append({"ref": fp.GetReference(), "x": round(mm(pos.x), ROUND_DIGITS),
                           "y": round(mm(pos.y), ROUND_DIGITS), "rot": round(fp.GetOrientationDegrees(), ROUND_DIGITS),
                           "side": "bottom" if fp.IsFlipped() else "top"})
        for pad in fp.Pads():
            drill = pad.GetDrillSize()
            if drill.x <= 0:
                continue
            attr = attrs.get(pad.GetAttribute(), str(pad.GetAttribute()))
            name = f"pad {fp.GetReference()}.{pad.GetNumber()}"
            if attr not in ("pth", "npth"):
                unsupported.append({"object": name, "reason": f"unsupported drilled pad type {attr}"})
                continue
            if drill.x != drill.y or pad.GetDrillShape() != pcbnew.PAD_DRILL_SHAPE_CIRCLE:
                if oblong is not None and pad.GetDrillShape() not in (pcbnew.PAD_DRILL_SHAPE_CIRCLE, oblong):
                    unsupported.append({"object": name, "reason": "unsupported drill shape"})
                    continue
                p1, p2, minor, major = _slot_endpoints(pcbnew, pad, drill)
                slots.append({"kind": "slot", "object": name, "attr": attr, "endpoints_mm": [p1, p2],
                              "minor_mm": round(minor, ROUND_DIGITS), "major_mm": round(major, ROUND_DIGITS),
                              "rot_deg": round(pad.GetOrientationDegrees(), ROUND_DIGITS)})
                continue
            q = pad.GetPosition()
            holes.append({"kind": "pad", "object": name, "attr": attr, "x": round(mm(q.x), ROUND_DIGITS),
                          "y": round(mm(q.y), ROUND_DIGITS), "diameter": round(mm(drill.x), ROUND_DIGITS)})
    for track in board.GetTracks():
        if track.Type() != pcbnew.PCB_VIA_T:
            continue
        name = f"via {track.m_Uuid.AsString()}"
        top, bottom = board.GetLayerName(track.TopLayer()), board.GetLayerName(track.BottomLayer())
        if {top, bottom} != {copper[0], copper[-1]}:
            unsupported.append({"object": name, "reason": REFUSED_VIA})
            continue
        q = track.GetPosition()
        holes.append({"kind": "via", "object": name, "attr": "pth", "x": round(mm(q.x), ROUND_DIGITS),
                      "y": round(mm(q.y), ROUND_DIGITS), "diameter": round(mm(track.GetDrillValue()), ROUND_DIGITS)})
    if unsupported:
        return refuse(unsupported)
    # Measure the edge centerlines. Stroke width does not change the physical board dimensions.
    drawings = list(board.GetDrawings())
    for footprint in board.GetFootprints():
        drawings.extend(footprint.GraphicalItems())
    for drawing in drawings:
        if drawing.GetLayer() == pcbnew.Edge_Cuts and isinstance(drawing, pcbnew.PCB_SHAPE):
            drawing.SetWidth(0)
    box = board.GetBoardEdgesBoundingBox()
    outline = {"x": round(mm(box.GetX()), ROUND_DIGITS), "y": round(mm(box.GetY()), ROUND_DIGITS),
               "width": round(mm(box.GetWidth()), ROUND_DIGITS), "height": round(mm(box.GetHeight()), ROUND_DIGITS)}
    print(json.dumps({"kicad": pcbnew.GetBuildVersion(), "copper_layers": copper, "outline": outline,
                      "footprints": footprints, "holes": holes, "slots": slots}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
