import pcbnew,json
p="/work/board.kicad_pcb"
b=pcbnew.LoadBoard(p)
pad=next(p for f in b.GetFootprints() for p in f.Pads())
zone=next(iter(b.Zones()))
zone.SetNetCode(pad.GetNetCode())
zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(p,b)
poly=zone.GetFilledPolysList(pcbnew.In1_Cu)
print(json.dumps({"pad_net":pad.GetNetname(),"zone_net":zone.GetNetname(),"filled_contains_pad_center":poly.Contains(pad.GetPosition()),"pad_connection":int(zone.GetPadConnection()),"outline_count":poly.OutlineCount()}))
