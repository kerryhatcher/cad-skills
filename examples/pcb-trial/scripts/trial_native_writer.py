"""Write the original native KiCad fixture of the trial (schematic, PCB, project, library tables).

Generator name: cad_skills_trial_native. It uses no SKiDL and no file from a person.
It uses only the installed KiCad symbol libraries and the KiCad text format.

  uv run --no-project --no-config --offline --python /usr/bin/python3 python scripts/trial_native_writer.py --out native

The schematic and the PCB are two formats with two version numbers. The generator learns
both from the installed KiCad: it writes a stub, runs `kicad-cli sch upgrade --force` and
`kicad-cli pcb upgrade --force`, and reads the `(version ...)` that KiCad writes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sexp  # noqa: E402

GENERATOR = "cad_skills_trial_native"
NAMESPACE = uuid.UUID("6f1c2a9e-0b7d-4c55-9a3e-2f7f6c1d9b11")
SYMBOL_DIR = Path("/usr/share/kicad/symbols")
FOOTPRINT_DIR = Path("/usr/share/kicad/footprints")
ROOT_UUID = str(uuid.uuid5(NAMESPACE, "root-sheet"))

# reference, library symbol, value, footprint, position on the sheet (mm), pin -> net
PARTS = [
    ("J1", "Connector_Generic:Conn_01x02", "Power", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", (50.8, 50.8),
     {"1": "VIN", "2": "GND"}),
    ("R1", "Device:R", "1k", "Resistor_SMD:R_0603_1608Metric", (101.6, 50.8), {"1": "VIN", "2": "N_LED"}),
    ("D1", "Device:LED", "Green", "LED_SMD:LED_0603_1608Metric", (152.4, 50.8), {"1": "GND", "2": "N_LED"}),
    ("R2", "Device:R", "10k", "Resistor_SMD:R_0603_1608Metric", (101.6, 101.6), {"1": "VIN", "2": "N_RC"}),
    ("C1", "Device:C", "100n", "Capacitor_SMD:C_0603_1608Metric", (152.4, 101.6), {"1": "N_RC", "2": "GND"}),
    ("MH1", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", (50.8, 152.4), {}),
    ("MH2", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", (88.9, 152.4), {}),
]
BOARD_ORIGIN = (100.0, 100.0)  # offset origin of the 40 mm by 25 mm board
BOARD_SIZE = (40.0, 25.0)

PCB_LAYERS = """(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)"""


def uid(*parts) -> str:
    return str(uuid.uuid5(NAMESPACE, "/".join(map(str, parts))))


def learn_versions() -> dict:
    """Ask the installed KiCad which format versions it writes."""
    with tempfile.TemporaryDirectory() as tmp:
        sch, pcb = Path(tmp) / "stub.kicad_sch", Path(tmp) / "stub.kicad_pcb"
        sch.write_text(f'(kicad_sch (version 20250114) (generator "{GENERATOR}") (uuid "{ROOT_UUID}") (paper "A4") (lib_symbols))\n')
        pcb.write_text(f'(kicad_pcb (version 20240108) (generator "{GENERATOR}") (general (thickness 1.6)) (paper "A4") (layers (0 "F.Cu" signal) (2 "B.Cu" signal)))\n')
        out = {}
        for kind, path in (("sch", sch), ("pcb", pcb)):
            result = subprocess.run(["kicad-cli", kind, "upgrade", "--force", str(path)], capture_output=True, text=True)
            if result.returncode != 0:
                raise SystemExit(f"kicad-cli {kind} upgrade failed: {result.stdout}{result.stderr}")
            out[kind] = int(re.search(r"\(version (\d+)\)", path.read_text()).group(1))
    return out


def pin_points(symbol_text: str) -> dict:
    """Return {pin number: (x, y)} in library coordinates, read from the symbol text."""
    tree = sexp.parse(symbol_text)
    points = {}

    def walk(node):
        for item in node:
            if isinstance(item, list) and item:
                if item[0] == "pin":
                    at = sexp.child(item, "at")
                    number = sexp.child(item, "number")
                    points[str(number[1])] = (float(at[1]), float(at[2]))
                else:
                    walk(item)

    walk(tree)
    return points


def load_symbols():
    """Return {lib_id: (definition text for lib_symbols, pin points)}."""
    cache, out = {}, {}
    for _, lib_id, *_ in PARTS:
        if lib_id in out:
            continue
        lib, name = lib_id.split(":")
        if lib not in cache:
            cache[lib] = (SYMBOL_DIR / f"{lib}.kicad_sym").read_text()
        text = sexp.find_symbol_text(cache[lib], name)
        renamed = text.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
        out[lib_id] = (renamed, pin_points(text))
    return out


def fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def build_schematic(version: int, symbols: dict, project: str) -> tuple[str, dict]:
    lines = [f'(kicad_sch\n\t(version {version})\n\t(generator "{GENERATOR}")\n\t(generator_version "1.0")\n\t(uuid "{ROOT_UUID}")\n\t(paper "A4")\n\t(lib_symbols']
    for lib_id in symbols:
        body = "\n".join("\t\t" + line for line in symbols[lib_id][0].splitlines())
        lines.append(body.rstrip())
    lines.append("\t)")
    placed = {}
    labels = []
    for ref, lib_id, value, footprint, (px, py), nets in PARTS:
        pts = symbols[lib_id][1]
        pin_lines = "".join(f'\n\t\t(pin "{n}"\n\t\t\t(uuid "{uid(ref, "pin", n)}")\n\t\t)' for n in sorted(pts))
        props = [("Reference", ref, False), ("Value", value, False), ("Footprint", footprint, True), ("Datasheet", "~", True), ("Description", "", True)]
        prop_text = "".join(
            f'\n\t\t(property "{k}" "{v}"\n\t\t\t(at {fmt(px + 2.54)} {fmt(py - 2.54 + 2.54 * i)} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)'
            + ("\n\t\t\t\t(hide yes)" if hide else "") + "\n\t\t\t)\n\t\t)"
            for i, (k, v, hide) in enumerate(props))
        lines.append(
            f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {fmt(px)} {fmt(py)} 0)\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
            f'\t\t(uuid "{uid(ref)}"){prop_text}{pin_lines}\n\t\t(instances\n\t\t\t(project "{project}"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        for number, net in nets.items():
            x, y = pts[number]
            sx, sy = px + x, py - y  # the sheet has the y axis down
            placed[f"{ref}.{number}"] = (round(sx, 4), round(sy, 4))
            labels.append(
                f'\t(label "{net}"\n\t\t(at {fmt(sx)} {fmt(sy)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{uid(ref, "label", number)}")\n\t)')
    lines.extend(labels)
    lines.append(f'\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)')
    return "\n".join(lines) + "\n", placed


def build_pcb(version: int) -> str:
    x0, y0 = BOARD_ORIGIN
    x1, y1 = x0 + BOARD_SIZE[0], y0 + BOARD_SIZE[1]
    return (
        f'(kicad_pcb\n\t(version {version})\n\t(generator "{GENERATOR}")\n\t(generator_version "1.0")\n\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)\n\t(paper "A4")\n'
        f'\t{PCB_LAYERS}\n\t(setup\n\t\t(pad_to_mask_clearance 0)\n\t)\n\t(net 0 "")\n'
        f'\t(gr_rect\n\t\t(start {fmt(x0)} {fmt(y0)})\n\t\t(end {fmt(x1)} {fmt(y1)})\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n\t\t(fill no)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uid("outline")}")\n\t)\n)\n')


def build_fp_table() -> str:
    libs = sorted({p[3].split(":")[0] for p in PARTS})
    rows = "".join(
        f'\n\t(lib (name "{lib}")(type "KiCad")(uri "{FOOTPRINT_DIR}/{lib}.pretty")(options "")(descr ""))' for lib in libs)
    return f"(fp_lib_table\n\t(version 7){rows}\n)\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="the output directory")
    parser.add_argument("--project", default="trial")
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    versions = learn_versions()
    schematic, pins = build_schematic(versions["sch"], load_symbols(), args.project)
    (out / f"{args.project}.kicad_sch").write_text(schematic)
    (out / f"{args.project}.kicad_pcb").write_text(build_pcb(versions["pcb"]))
    (out / f"{args.project}.kicad_pro").write_text(json.dumps({"meta": {"filename": f"{args.project}.kicad_pro", "version": 3}}, indent=2) + "\n")
    (out / "fp-lib-table").write_text(build_fp_table())
    (out / "format_versions.json").write_text(json.dumps({"generator": GENERATOR, "schematic_version": versions["sch"], "pcb_version": versions["pcb"],
                                                           "evidence": "kicad-cli sch upgrade --force and pcb upgrade --force on a stub, KiCad 10.0.5"}, indent=2) + "\n")
    (out / "pin_points.json").write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schematic_version": versions["sch"], "pcb_version": versions["pcb"], "pins": len(pins)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
