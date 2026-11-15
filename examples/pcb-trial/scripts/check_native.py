# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check the native fixture against explicit expectations (host or container, no KiCad import).

  uv run scripts/check_native.py --dir native --netlist native/out/trial.net.xml --expected expected

Checks (the constants are written by hand and do not come from the files under test):
  * exactly 7 raw symbol instances, with the expected references, values and footprints.
    A duplicate reference or an instance with missing mandatory data is a problem.
  * the pin points MEASURED from the embedded symbol definitions and the instance positions equal
    the expected pin points. A rotation or a mirror of an instance is not supported by this fixture
    and is a problem. The sidecar `pin_points.json` is diagnostic output and proves nothing.
  * the complete pin-to-net map of the exported netlist equals expected/netlist.json. A repeated pin
    is a problem. KiCad adds one leading slash to a local label. The checker removes at most one.

A malformed input gives a problem report (exit 1), not a traceback. This is a small reader for this
fixture. It is not a general KiCad parser.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sexp  # noqa: E402

EXPECTED_PARTS = {
    "J1": ("Connector_Generic:Conn_01x02", "Power", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"),
    "R1": ("Device:R", "1k", "Resistor_SMD:R_0603_1608Metric"),
    "D1": ("Device:LED", "Green", "LED_SMD:LED_0603_1608Metric"),
    "R2": ("Device:R", "10k", "Resistor_SMD:R_0603_1608Metric"),
    "C1": ("Device:C", "100n", "Capacitor_SMD:C_0603_1608Metric"),
    "MH1": ("Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3"),
    "MH2": ("Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3"),
}
MANDATORY_PROPERTIES = ("Reference", "Value", "Footprint")


def as_number(value, what):
    """Return a float. A nested list or a text that is not a number gives a ValueError with a clear message."""
    if isinstance(value, list):
        raise ValueError(f"{what} is not a number")
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{what} is not a number ({value!r})")


def read_instances(tree, problems):
    """Return the list of raw instances. Each is a dict. Nothing is merged by reference."""
    out = []
    for index, sym in enumerate(sexp.children(tree, "symbol")):
        # A direct child `symbol` of the schematic is an instance. The library definitions are inside `lib_symbols`.
        lib_id = sexp.child(sym, "lib_id")
        if lib_id is None or len(lib_id) < 2 or isinstance(lib_id[1], list) or not str(lib_id[1]).strip():
            problems.append(f"symbol {index} misses mandatory data: lib_id")
            continue
        props = {}
        for p in sexp.children(sym, "property"):
            if len(p) >= 3:
                if isinstance(p[1], list) or isinstance(p[2], list):
                    raise ValueError(f"symbol {index} has a property name or value that is not text")
                props[p[1]] = p[2]
        at = sexp.child(sym, "at")
        missing = [k for k in MANDATORY_PROPERTIES if k not in props or not str(props[k]).strip()]
        if at is None or len(at) < 3:
            missing.append("at")
        if missing:
            problems.append(f"instance {index} ({props.get('Reference', '?')}) misses mandatory data: {', '.join(missing)}")
            continue
        out.append({"ref": props["Reference"], "lib_id": str(lib_id[1]), "value": props["Value"], "footprint": props["Footprint"],
                    "x": as_number(at[1], f"the x position of {props['Reference']}"), "y": as_number(at[2], f"the y position of {props['Reference']}"),
                    "rotation": as_number(at[3], f"the rotation of {props['Reference']}") if len(at) > 3 else 0.0,
                    "mirror": sexp.child(sym, "mirror") is not None})
    return out


def embedded_pins(tree, problems):
    """Return {lib_id: {pin number: (x, y)}} measured from the embedded `lib_symbols` text."""
    out = {}
    section = sexp.child(tree, "lib_symbols")
    for symbol in sexp.children(section or [], "symbol"):
        pins = {}

        def walk(node):
            for item in node:
                if isinstance(item, list) and item:
                    if item[0] == "pin":
                        at, number = sexp.child(item, "at"), sexp.child(item, "number")
                        if at is None or number is None:
                            problems.append(f"a pin of {symbol[1]} has no position or number")
                            continue
                        if str(number[1]) in pins:
                            problems.append(f"{symbol[1]} has the pin {number[1]} two times")
                        pins[str(number[1])] = (as_number(at[1], f"a pin x of {symbol[1]}"), as_number(at[2], f"a pin y of {symbol[1]}"))
                    else:
                        walk(item)

        walk(symbol[2:])
        out[str(symbol[1])] = pins
    return out


def read_netlist(path, problems):
    found = {}
    root = ET.parse(path).getroot()
    for net in root.iter("net"):
        name = net.get("name") or ""
        name = name[1:] if name.startswith("/") else name  # at most one slash
        for node in net.iter("node"):
            key = f"{node.get('ref')}.{node.get('pin')}"
            if key in found:
                problems.append(f"the pin {key} is in the netlist two times ({found[key]!r} and {name!r})")
            found[key] = name
    return found


def run(directory, netlist, expected, project="trial"):
    problems = []
    expected_dir = Path(expected)
    try:
        tree = sexp.parse((Path(directory) / f"{project}.kicad_sch").read_text())
        instances = read_instances(tree, problems)
        measured = embedded_pins(tree, problems)
    except (OSError, ValueError, IndexError, KeyError, TypeError) as err:
        return {"instances": 0, "problems": [f"the schematic cannot be read: {type(err).__name__}: {err}"]}
    refs = [i["ref"] for i in instances]
    for ref in sorted({r for r in refs if refs.count(r) > 1}):
        problems.append(f"the reference {ref} occurs {refs.count(ref)} times")
    if len(instances) != 7:
        problems.append(f"{len(instances)} raw symbol instances, expected 7")
    by_ref = {i["ref"]: i for i in instances}
    for ref in sorted(set(EXPECTED_PARTS) - set(by_ref)):
        problems.append(f"the expected reference {ref} is absent")
    for ref in sorted(set(by_ref) - set(EXPECTED_PARTS)):
        problems.append(f"the reference {ref} is not expected")
    expected_pins = {k: v for k, v in json.loads((expected_dir / "pins.json").read_text()).items() if not k.startswith("_")}
    pins_compared = 0
    for ref, (lib_id, value, footprint) in EXPECTED_PARTS.items():
        inst = by_ref.get(ref)
        if inst is None:
            continue  # reported as absent
        if (inst["lib_id"], inst["value"], inst["footprint"]) != (lib_id, value, footprint):
            problems.append(f"{ref}: {(inst['lib_id'], inst['value'], inst['footprint'])} differs from {(lib_id, value, footprint)}")
        if inst["rotation"] != 0.0 or inst["mirror"]:
            problems.append(f"{ref}: a rotation or a mirror is not supported by this fixture (rotation {inst['rotation']}, mirror {inst['mirror']})")
            continue
        want = {n: (round(inst["x"] + x, 4), round(inst["y"] - y, 4)) for n, (x, y) in expected_pins[lib_id].items()}
        got = {n: (round(inst["x"] + x, 4), round(inst["y"] - y, 4)) for n, (x, y) in measured.get(lib_id, {}).items()}
        if got != want:
            problems.append(f"{ref}: the embedded pin points {got} differ from the expected {want}")
        pins_compared += len(want)
    try:
        found = read_netlist(netlist, problems)
    except (OSError, ET.ParseError) as err:
        problems.append(f"the netlist cannot be read: {type(err).__name__}: {err}")
        found = None
    want_nets = {k: v for k, v in json.loads((expected_dir / "netlist.json").read_text()).items() if not k.startswith("_")}
    if found is not None and found != want_nets:
        problems.append(f"pin-to-net map differs: only exported {sorted(set(found.items()) - set(want_nets.items()))}, "
                        f"only expected {sorted(set(want_nets.items()) - set(found.items()))}")
    return {"instances": len(instances), "pins_compared": pins_compared, "nets_compared": len(want_nets), "problems": problems}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--project", default="trial")
    args = parser.parse_args(argv)
    result = run(args.dir, args.netlist, args.expected, args.project)
    print(json.dumps(result, indent=2))
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
