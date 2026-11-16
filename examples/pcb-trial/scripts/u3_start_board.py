# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Make the start board of the U3 netlist-import edit tests from the native baseline board. Text edit only.

  uv run scripts/u3_start_board.py --board results/native/baseline.kicad_pcb \
      --extra expected/fixtures/vz_saved_by_kicad.kicad_pcb --netlist NET -o OUTPUT.kicad_pcb

The native baseline has the 7 footprints, their positions and 6 track segments. The script:
  * replaces the schematic path of each footprint with "/" and the SKiDL tstamp of the same reference in NET,
  * removes the "/" prefix from each net name, because the SKiDL netlist names the nets without it,
  * adds the via, the arc and the zone of the `--extra` board (KiCad-saved forms) with the same rename.

The result is an input. It is not a gate baseline. The gate baseline is the board that KiCad saves after a first
netlist import with no edit (see `docs/reviews/u3-netlist-edits-claude.md`).
The script stops with exit 2 if a reference has no tstamp in NET, or if a footprint has no path.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROUTING = re.compile(r"^\t\((via|arc|zone)\n.*?^\t\)\n", re.S | re.M)


def tstamps(netlist: str) -> dict[str, str]:
    """Reference to tstamp, from the `comp` forms of a KiCad netlist."""
    pairs = re.findall(r'\(comp\s+\(ref "([^"]+)"\).*?\n      \(tstamps "([^"]+)"\)\)', netlist, re.S)
    return dict(pairs)


def convert(board: str, stamps: dict[str, str]) -> str:
    out, pos, seen = [], 0, set()
    for m in re.finditer(r'^\t\(footprint ".*?^\t\)\n', board, re.S | re.M):
        block = m.group(0)
        ref = re.search(r'\(property "Reference" "([^"]+)"', block).group(1)
        if ref not in stamps:
            raise SystemExit(f"u3_start_board: the netlist has no tstamp for {ref}. Use the netlist of the 'none' edit.")
        new, count = re.subn(r'\n\t\t\(path "[^"]*"\)', f'\n\t\t(path "/{stamps[ref]}")', block, count=1)
        if count != 1:
            raise SystemExit(f"u3_start_board: the footprint {ref} has no path form.")
        seen.add(ref)
        out.append(board[pos:m.start()] + new)
        pos = m.end()
    out.append(board[pos:])
    missing = set(stamps) - seen
    if missing:
        raise SystemExit(f"u3_start_board: the board has no footprint for {sorted(missing)}.")
    return "".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--board", required=True)
    parser.add_argument("--extra", required=True)
    parser.add_argument("--netlist", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args(argv)
    try:
        text = convert(Path(args.board).read_text(), tstamps(Path(args.netlist).read_text()))
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    extra = "".join(m.group(0) for m in ROUTING.finditer(Path(args.extra).read_text()))
    body = text.rstrip()
    text = body[:-1] + extra + ")\n"
    text = re.sub(r'\(net "/([^"]*)"\)', r'(net "\1")', text)
    Path(args.output).write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
