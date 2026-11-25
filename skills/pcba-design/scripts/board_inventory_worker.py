"""Measure all drilled pads and vias with pcbnew.

The package runs this owned worker in the locked KiCad image:

    python3 /work/board_inventory_worker.py /work/board.kicad_pcb

The worker prints one JSON object. `holes` lists the supported holes in millimeters.
`refused` lists the unsupported drilled objects. The package stops on each refusal.
"""

import json
import sys

import pcbnew

NM_PER_MM = 1000000.0


def measure(path: str) -> dict:
    board = pcbnew.LoadBoard(path)
    holes = []
    refused = []
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        for pad in footprint.Pads():
            drill = pad.GetDrillSize()
            if drill.x == 0 and drill.y == 0:
                continue
            name = f"{reference}.{pad.GetNumber()}"
            if drill.x <= 0 or drill.y <= 0:
                refused.append({"object": name, "reason": "The drill diameter is not positive."})
                continue
            if pad.GetDrillShape() != pcbnew.PAD_DRILL_SHAPE_CIRCLE or drill.x != drill.y:
                refused.append({"object": name, "reason": "The drill is not a round hole."})
                continue
            attribute = pad.GetAttribute()
            if attribute == pcbnew.PAD_ATTRIB_PTH:
                plated = True
            elif attribute == pcbnew.PAD_ATTRIB_NPTH:
                plated = False
            else:
                refused.append({"object": name, "reason": "The pad type with a drill is not supported."})
                continue
            position = pad.GetPosition()
            holes.append({"object": name, "kind": "pad", "x_mm": position.x / NM_PER_MM,
                          "y_mm": position.y / NM_PER_MM, "diameter_mm": drill.x / NM_PER_MM,
                          "plated": plated})
    for track in board.GetTracks():
        if track.GetClass() != "PCB_VIA":
            continue
        position = track.GetPosition()
        name = f"via@{position.x / NM_PER_MM:.4f},{position.y / NM_PER_MM:.4f}"
        if track.GetViaType() != pcbnew.VIATYPE_THROUGH:
            refused.append({"object": name, "reason": "Only through vias are supported."})
            continue
        if track.GetDrillValue() <= 0:
            refused.append({"object": name, "reason": "The drill diameter is not positive."})
            continue
        holes.append({"object": name, "kind": "via", "x_mm": position.x / NM_PER_MM,
                      "y_mm": position.y / NM_PER_MM, "diameter_mm": track.GetDrillValue() / NM_PER_MM,
                      "plated": True})
    holes.sort(key=lambda hole: hole["object"])
    refused.sort(key=lambda item: item["object"])
    return {"holes": holes, "refused": refused}


if __name__ == "__main__":
    print(json.dumps(measure(sys.argv[1]), indent=2, sort_keys=True))
