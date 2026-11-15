import sys, pcbnew
b=pcbnew.LoadBoard('/work/board.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference()=='MH2': fp.SetOrientationDegrees(45)
pcbnew.SaveBoard('/work/board_rot45.kicad_pcb', b)
print('rotated')
