"""B6 design probe (not an implementation): read hole and placement geometry with the installed pcbnew bindings.
Run: uv run --no-project --no-config --offline --python /usr/bin/python3 python scripts/b6_probe_inventory.py BOARD OUT.json [--mutate]
--mutate rotates J1 by 90 degrees and flips C1 to the bottom side in memory, saves a copy next to OUT.json, and inventories the copy."""
import json, sys
import pcbnew

mm = pcbnew.ToMM
board_path, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(board_path)
if "--mutate" in sys.argv or "--mutate-tht" in sys.argv:
    for fp in board.GetFootprints():
        if fp.GetReference() == "J1":
            fp.SetOrientationDegrees(90)
            if "--mutate-tht" in sys.argv:
                fp.Flip(fp.GetPosition(), False)
        if fp.GetReference() == "C1":
            fp.Flip(fp.GetPosition(), False)
    board_path = out.replace(".json", ".kicad_pcb")
    pcbnew.SaveBoard(board_path, board)
    board = pcbnew.LoadBoard(board_path)
inv = {"board": board_path, "kicad": pcbnew.GetBuildVersion(), "copper_layers": [board.GetLayerName(l) for l in board.GetEnabledLayers().CuStack()],
       "footprints": [], "holes": []}
attr = {pcbnew.PAD_ATTRIB_PTH: "pth", pcbnew.PAD_ATTRIB_NPTH: "npth", pcbnew.PAD_ATTRIB_SMD: "smd", pcbnew.PAD_ATTRIB_CONN: "conn"}
for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
    p = fp.GetPosition()
    inv["footprints"].append({"ref": fp.GetReference(), "x": round(mm(p.x), 6), "y": round(mm(p.y), 6), "rot": round(fp.GetOrientationDegrees(), 6), "side": "bottom" if fp.IsFlipped() else "top"})
    for pad in fp.Pads():
        d = pad.GetDrillSize()
        if d.x > 0:
            q = pad.GetPosition()
            inv["holes"].append({"kind": "pad", "ref": fp.GetReference(), "pad": pad.GetNumber(), "attr": attr.get(pad.GetAttribute(), str(pad.GetAttribute())),
                                 "x": round(mm(q.x), 6), "y": round(mm(q.y), 6), "dx": round(mm(d.x), 6), "dy": round(mm(d.y), 6), "slot": d.x != d.y})
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        q = t.GetPosition()
        inv["holes"].append({"kind": "via", "x": round(mm(q.x), 6), "y": round(mm(q.y), 6), "dx": round(mm(t.GetDrillValue()), 6), "dy": round(mm(t.GetDrillValue()), 6), "slot": False,
                             "attr": "pth", "span": [board.GetLayerName(t.TopLayer()), board.GetLayerName(t.BottomLayer())]})
json.dump(inv, open(out, "w"), indent=1)
print(len(inv["footprints"]), "footprints", len(inv["holes"]), "holes", inv["copper_layers"])
