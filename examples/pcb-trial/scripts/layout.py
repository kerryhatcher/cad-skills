# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Intermediate baseline layout for the identity experiments (phase A). Text edit of a saved .kicad_pcb.

  uv run scripts/layout.py INPUT.kicad_pcb -o OUTPUT.kicad_pcb [--final]

It sets unequal positions and rotations (0 and 180 degrees only) for the 7 footprints inside the
40 mm by 25 mm outline at (100,100) to (140,125), and it adds straight track segments with fixed UUIDs.
The result is labeled intermediate experiment data: it is not routed completely. The final reference
board (phase B) needs a separate, complete routing.

With `--final` the script adds the routing of the GND net: one via and one short track for each SMD GND pad
(`D1.1` and `C1.2`), the field and pad angles of the rotated footprint (D1), the saved plot settings of the export (see `PLOT_SETTINGS`), and a GND zone on `B.Cu` that covers the board interior. The through-hole pad `J1.2` touches
the zone. KiCad refills the zone later (`kicad-cli pcb drc --refill-zones --save-board`). The expected values of
the exports come from the constants in this file (`PLACE`, `VIAS`, `ZONE`), not from the exported files.
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identity  # noqa: E402

NS = uuid.UUID("6f1c2a9e-0b7d-4c55-9a3e-2f7f6c1d9b11")
PLACE = {"J1": (105.0, 112.5, 0), "R1": (115.0, 106.0, 0), "D1": (125.0, 106.0, 180), "R2": (115.0, 118.0, 0), "C1": (125.0, 118.0, 0),
         "MH1": (103.0, 103.0, 0), "MH2": (137.0, 122.0, 0)}
# (net, [points]) straight polylines between pad points. A pad point is ("REF", "pad") or (x, y).
TRACKS = [("/N_LED", [("R1", "2"), ("D1", "2")]), ("/VIN", [("J1", "1"), (105.0, 106.0), ("R1", "1")]),
          ("/VIN", [("R2", "1"), (115.0 - 0.825, 112.0), (105.0, 112.0)]), ("/N_RC", [("R2", "2"), ("C1", "1")])]


# GND vias, one for each SMD GND pad: (pad, via point). The track runs from the pad to the via.
VIAS = [(("D1", "1"), (127.5, 106.0)), (("C1", "2"), (127.5, 118.0))]
VIA_SIZE, VIA_DRILL = 0.6, 0.3
ZONE = [(101.0, 101.0), (139.0, 101.0), (139.0, 124.0), (101.0, 124.0)]


# Saved plot settings for the manufacturing Gerbers. `kicad-cli pcb export gerbers --board-plot-params` takes them from the board.
# They override the CLI flag --no-x2. The contract says x2: false and no drill marks (the Excellon files define the holes).
# The first final revision (`results/final`) did not set them: it had drillshape 1 and both attribute settings yes.
PLOT_SETTINGS = {"drillshape": "0", "usegerberattributes": "no", "usegerberadvancedattributes": "no"}


def set_plot_settings(text: str) -> str:
    """Set the saved plot settings. A setting that is absent from the board is an error: no silent skip."""
    for key, value in PLOT_SETTINGS.items():
        text, count = re.subn(rf"\({key} [^)]*\)", f"({key} {value})", text)
        if count != 1:
            raise ValueError(f"layout: the board has {count} entries of the plot setting {key}. One entry is necessary.")
    return text


def fmt(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def pad_point(snap, ref, pad):
    fp = next(f for f in snap["footprints"].values() if f["reference"] == ref)
    x, y, rot = PLACE[ref]
    ox, oy = fp["pads"][pad]["at"][:2]
    if rot == 180:
        ox, oy = -ox, -oy
    return round(x + ox, 4), round(y + oy, 4)


def footprint_blocks(text):
    for m in re.finditer(r"\n\t\(footprint \"", text):
        start = m.start() + 1
        depth, i = 0, start
        while True:
            if text[i] == '"':
                i += 1
                while text[i] != '"':
                    i += 2 if text[i] == "\\" else 1
            elif text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    yield start, i + 1
                    break
            i += 1


def rotate_children(block: str, rot: float) -> str:
    """KiCad stores the angle of each field and pad as an absolute angle. Add the footprint rotation to them."""
    head, sep, rest = block.partition("\n\t\t(at ")
    first, sep2, tail = rest.partition("\n")

    def bump(m):
        angle = (float(m.group(3) or 0) + rot) % 360
        return f"(at {m.group(1)} {m.group(2)}" + (f" {fmt(angle)}" if angle else "") + ")"

    return head + sep + first + sep2 + re.sub(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", bump, tail)


def build(text: str, final: bool = False) -> str:
    snap = identity.snapshot_text(text)
    edits = []
    for start, end in footprint_blocks(text):
        block = text[start:end]
        ref = re.search(r'\(property "Reference" "([^"]+)"', block).group(1)
        x, y, rot = PLACE[ref]
        at = f"(at {fmt(x)} {fmt(y)}" + (f" {rot}" if rot else "") + ")"
        new = re.sub(r"\n\t\t\(at [^)]*\)", "\n\t\t" + at, block, count=1)
        if final and rot:
            new = rotate_children(new, rot)
        edits.append((start, end, new))
    for start, end, new in reversed(edits):
        text = text[:start] + new + text[end:]
    segs = []
    n = 0
    for net, pts in TRACKS:
        pts = [pad_point(snap, *p) if isinstance(p[0], str) else p for p in pts]
        for a, b in zip(pts, pts[1:]):
            n += 1
            segs.append(f'\t(segment\n\t\t(start {fmt(a[0])} {fmt(a[1])})\n\t\t(end {fmt(b[0])} {fmt(b[1])})\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uuid.uuid5(NS, f"segment/{n}")}")\n\t)\n')
    body = text.rstrip()
    assert body.endswith(")")
    return body[:-1].rstrip() + "\n" + "".join(segs) + ")\n"


def add_final(text: str) -> str:
    """Add the GND vias, the short GND tracks and the B.Cu GND zone to a laid out board."""
    snap = identity.snapshot_text(text)
    items = []
    for n, (pad, via) in enumerate(VIAS, 1):
        a = pad_point(snap, *pad)
        items.append(f'\t(segment\n\t\t(start {fmt(a[0])} {fmt(a[1])})\n\t\t(end {fmt(via[0])} {fmt(via[1])})\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net "/GND")\n\t\t(uuid "{uuid.uuid5(NS, f"gnd-segment/{n}")}")\n\t)\n')
        items.append(f'\t(via\n\t\t(at {fmt(via[0])} {fmt(via[1])})\n\t\t(size {VIA_SIZE})\n\t\t(drill {VIA_DRILL})\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "/GND")\n\t\t(uuid "{uuid.uuid5(NS, f"gnd-via/{n}")}")\n\t)\n')
    pts = "".join(f"\t\t\t\t(xy {fmt(x)} {fmt(y)})\n" for x, y in ZONE)
    items.append(f'\t(zone\n\t\t(net "/GND")\n\t\t(layer "B.Cu")\n\t\t(uuid "{uuid.uuid5(NS, "gnd-zone")}")\n\t\t(name "GND_pour")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads\n\t\t\t(clearance 0.3)\n\t\t)\n\t\t(min_thickness 0.25)\n\t\t(filled_areas_thickness no)\n\t\t(fill yes\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n{pts}\t\t\t)\n\t\t)\n\t)\n')
    body = text.rstrip()
    return set_plot_settings(body[:-1].rstrip() + "\n" + "".join(items) + ")\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--final", action="store_true", help="add the GND vias, tracks and the B.Cu GND zone")
    args = parser.parse_args(argv)
    text = build(Path(args.input).read_text(), args.final)
    Path(args.output).write_text(add_final(text) if args.final else text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
