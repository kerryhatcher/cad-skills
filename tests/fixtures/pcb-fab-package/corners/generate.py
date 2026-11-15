# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Make owned corner fixtures from explicit dimensions in millimeters."""
import math
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HEADER = '''(kicad_pcb (version 20260101) (generator "pcbnew") (generator_version "10.0.5")
 (general (thickness 1.6)) (paper "A4")
 (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
 (setup (pad_to_mask_clearance 0))
'''


def xy(p):
    return f"{p[0]:.9f} {p[1]:.9f}"


def shape(kind, fields, index):
    ident = uuid.uuid5(uuid.NAMESPACE_URL, f"cad-skills-corner-{index}")
    return f' ({kind} {fields} (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{ident}"))\n'


def line(a, b, index):
    return shape("gr_line", f"(start {xy(a)}) (end {xy(b)})", index)


def arc(center, radius, start, stop, index):
    def p(angle):
        return (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))
    return shape("gr_arc", f"(start {xy(p(start))}) (mid {xy(p((start + stop) / 2))}) (end {xy(p(stop))})", index)


def main():
    for value in ("0.033", "0.034", "0.035"):
        r = float(value) * 25.4
        points = [(0, 0), (20, 0), (20, 10), (10 + r, 10)]
        text = "".join(line(a, b, i) for i, (a, b) in enumerate(zip(points, points[1:])))
        text += arc((10 + r, 10 + r), r, -math.pi / 2, -math.pi, 10)
        points = [(10, 10 + r), (10, 20), (0, 20), (0, 0)]
        text += "".join(line(a, b, 20 + i) for i, (a, b) in enumerate(zip(points, points[1:])))
        (ROOT / f"outline-{value}in.kicad_pcb").write_text(HEADER + text + ")\n")
    rectangle = shape("gr_rect", "(start 0 0) (end 20 20) (fill none)", 100)
    for value in ("0.019", "0.020", "0.021"):
        r = float(value) * 25.4
        centers = [(12-r,8+r),(12-r,12-r),(8+r,12-r),(8+r,8+r)]
        angles = [(-math.pi/2,0),(0,math.pi/2),(math.pi/2,math.pi),(math.pi,3*math.pi/2)]
        points = [((8+r,8),(12-r,8)),((12,8+r),(12,12-r)),((12-r,12),(8+r,12)),((8,12-r),(8,8+r))]
        text = rectangle
        for i, (center, (a,b), (start,end)) in enumerate(zip(centers,angles,points)):
            text += line(start,end,200+i)
            text += arc(center,r,a,b,300+i)
        (ROOT / f"cutout-{value}in.kicad_pcb").write_text(HEADER + text + ")\n")
    (ROOT / "convex-square.kicad_pcb").write_text(HEADER + rectangle + ")\n")
    (ROOT / "open-outline.kicad_pcb").write_text(HEADER + line((0,0),(20,0),400) + ")\n")
    polygon = shape("gr_poly", "(pts (xy 0 0) (xy 20 0) (xy 20 20) (xy 0 20)) (fill none)",500)
    (ROOT / "unsupported-polygon.kicad_pcb").write_text(HEADER + polygon + ")\n")


if __name__ == "__main__":
    main()
