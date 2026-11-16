# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Compare the pad nets of a board with a KiCad netlist (the U3 replacement of the schematic parity check).

  uv run scripts/u3_netcheck.py BOARD.kicad_pcb NETLIST.net [--json]

The netlist route has no reliable schematic, thus `kicad-cli pcb drc --schematic-parity` cannot run.
This check reads the components and the nets of the netlist and the footprints of the board (identity reader).
It reports:
  missing_footprint  a netlist component with no footprint of that reference on the board
  extra_footprint    a board footprint with a reference that is not in the netlist
  path_mismatch      a footprint whose path is not "/" and the tstamp of the component
  pad_net            a pad whose net is not the net of that pin in the netlist. A pin in no net must have no net.
  unknown_pin        a netlist pin with no pad of that number on the footprint

Exit status: 0 no finding, 1 one or more findings, 2 incorrect input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identity  # noqa: E402


def read_netlist(text: str):
    comps = dict(re.findall(r'\(comp\s+\(ref "([^"]+)"\).*?\n      \(tstamps "([^"]+)"\)\)', text, re.S))
    pins = {}
    nets = text[text.index("(nets"):] if "(nets" in text else ""
    for block in re.split(r"\n    \(net\n", nets)[1:]:
        name = re.search(r'\(name "([^"]*)"\)', block).group(1)
        for ref, pin in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', block):
            pins[(ref, pin)] = name
    return comps, pins


def check(board: dict, comps: dict, pins: dict) -> list[dict]:
    found = []
    by_ref = {f["reference"]: f for f in board["footprints"].values()}
    for ref in sorted(set(comps) - set(by_ref)):
        found.append({"kind": "missing_footprint", "ref": ref})
    for ref in sorted(set(by_ref) - set(comps)):
        found.append({"kind": "extra_footprint", "ref": ref, "path": by_ref[ref]["path"]})
    for ref in sorted(set(comps) & set(by_ref)):
        f = by_ref[ref]
        if f["path"] != f"/{comps[ref]}":
            found.append({"kind": "path_mismatch", "ref": ref, "board": f["path"], "netlist": f"/{comps[ref]}"})
        for number, pad in sorted(f["pads"].items()):
            if number == "":
                continue
            want = pins.get((ref, number))
            if pad["net"] != want:
                found.append({"kind": "pad_net", "pad": f"{ref}.{number}", "board": pad["net"], "netlist": want})
    for ref, pin in sorted(pins):
        if ref in by_ref and pin not in by_ref[ref]["pads"]:
            found.append({"kind": "unknown_pin", "pad": f"{ref}.{pin}"})
    return found


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("board")
    parser.add_argument("netlist")
    args = parser.parse_args(argv)
    try:
        board = identity.snapshot_text(Path(args.board).read_text())
        comps, pins = read_netlist(Path(args.netlist).read_text())
    except (OSError, ValueError, AttributeError, identity.Unparsed) as err:
        print(json.dumps({"error": f"u3_netcheck: cannot read the input ({type(err).__name__}: {err}). Give a KiCad board and a KiCad netlist."}))
        return 2
    if not comps:
        print(json.dumps({"error": "u3_netcheck: the netlist has no components. Give a KiCad netlist."}))
        return 2
    found = check(board, comps, pins)
    print(json.dumps({"components": len(comps), "pins": len(pins), "findings": found, "status": "pass" if not found else "fail"}, indent=2))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
