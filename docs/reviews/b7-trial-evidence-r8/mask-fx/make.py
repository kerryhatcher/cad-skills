"""Write three two-pad boards whose mask web is 3.9, 4.0 and 4.1 mil (exact nm positions)."""
import pathlib, re, sys
S = pathlib.Path("/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad")
src = (S / "mask" / "board.kicad_pcb").read_text()
header = src[: src.index("\t(footprint ")]
PAD = 0.6  # pad diameter in mm
MIL = 0.0254
cases = {"m39": 3.9, "m40": 4.0, "m41": 4.1}
for name, mil in cases.items():
    gap = round(mil * MIL, 6)  # 1 nm grid in KiCad
    x2 = round(PAD + gap, 6)
    fps = []
    for i, x in enumerate([0.0, x2]):
        fps.append(f'''\t(footprint "Test:Pad"
\t\t(layer "F.Cu")
\t\t(uuid "00000000-0000-0000-0000-00000000000{i+1}")
\t\t(at {x} 0)
\t\t(property "Reference" "P{i+1}" (at 0 0 0) (layer "F.SilkS") (hide yes) (uuid "00000000-0000-0000-0000-00000000010{i+1}") (effects (font (size 1 1) (thickness 0.15))))
\t\t(pad "1" smd circle (at 0 0) (size {PAD} {PAD}) (layers "F.Cu" "F.Mask") (uuid "00000000-0000-0000-0000-00000000020{i+1}"))
\t)
''')
    text = header + "".join(fps) + ")\n"
    d = S / "mask-fx" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "board.kicad_pcb").write_text(text)
    (d / "board.kicad_pro").write_text("{}\n")
    print(name, "gap_mm", gap, "x2_mm", x2)
