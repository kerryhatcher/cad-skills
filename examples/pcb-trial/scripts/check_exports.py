# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Compare the exports of the final board with the expected values (T10). Host script, no KiCad.

  uv run scripts/check_exports.py EXPORT_DIR BOARD.kicad_pcb [--json]

The expected values come from the constants of `scripts/layout.py` (`PLACE`, `VIAS`) and from the
contract settings. The script never reads an expected value from an exported file.
It checks: the saved plot settings of the board, the set of Gerber files, the single file-function comment of each Gerber
against the fixed nine-layer mapping and the copper order of the board, the absence of active attribute commands in all nine
Gerbers, the drill files (plated and non-plated, hole diameters and positions), and the placement rows (reference, position,
rotation, side, and exactly one row for each of the seven references).

The effective plot settings come from the saved board, because `--board-plot-params` takes them and they override `--no-x2`.
The contract says x2 false. The file-function line is then a comment (`G04 #@! TF.FileFunction,...`). The check is a bounded
header comparison. It is not a general Gerber parser.

KiCad writes the Y coordinate of a placement row and of a drill hole as the negative of the board Y value.
The expectation applies this rule to the layout constants. The rule is a measured convention of KiCad 10.0.5.

Exit status: 0 all checks pass, 1 a check fails, 2 incorrect input.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout  # noqa: E402

PREFIX = "trial"
GERBERS = ["B_Cu", "B_Mask", "B_Paste", "B_Silkscreen", "Edge_Cuts", "F_Cu", "F_Mask", "F_Paste", "F_Silkscreen"]
PLOT_SETTINGS = {"drillshape": "0", "usegerberattributes": "no", "usegerberadvancedattributes": "no"}
# Fixed mapping of the nine layers to the file function (X2 file function text, without the copper position).
FUNCTION = {"B_Mask": "Soldermask,Bot", "B_Paste": "Paste,Bot", "B_Silkscreen": "Legend,Bot", "Edge_Cuts": "Profile,NP",
            "F_Mask": "Soldermask,Top", "F_Paste": "Paste,Top", "F_Silkscreen": "Legend,Top"}
ACTIVE_ATTRIBUTE = re.compile(r"^%T[FAOD]")
FUNCTION_COMMENT = re.compile(r"^G04 #@! TF\.FileFunction,(.*)\*$")
PIN_PITCH = 2.54  # pitch of the header J1 (footprint PinHeader_1x02_P2.54mm_Vertical)
MOUNTING_DRILL = 3.2  # footprint MountingHole_3.2mm_M3
J1_DRILL = 1.0
FOOTPRINT_ROTATION = {ref: rot for ref, (_x, _y, rot) in layout.PLACE.items()}


def expected_rows():
    return {ref: (x, -y, float(rot)) for ref, (x, y, rot) in layout.PLACE.items()}


def expected_holes():
    plated = {layout.VIA_DRILL: sorted((x, -y) for _pad, (x, y) in layout.VIAS)}
    jx, jy, _ = layout.PLACE["J1"]
    plated[J1_DRILL] = sorted([(jx, -jy), (jx, -(jy + PIN_PITCH))])
    nonplated = {MOUNTING_DRILL: sorted((layout.PLACE[r][0], -layout.PLACE[r][1]) for r in ("MH1", "MH2"))}
    return plated, nonplated


def parse_drill(text: str) -> dict:
    """Return {diameter: sorted positions} for an Excellon file with 3:3 format and suppressed leading zeros."""
    tools, holes, current = {}, {}, None
    for line in text.splitlines():
        m = re.fullmatch(r"T(\d+)C([\d.]+)", line.strip())
        if m:
            tools[m.group(1)] = float(m.group(2))
            continue
        m = re.fullmatch(r"T(\d+)", line.strip())
        if m:
            current = tools[m.group(1)]
            continue
        m = re.fullmatch(r"X(-?\d+)Y(-?\d+)", line.strip())
        if m and current is not None:
            holes.setdefault(current, []).append((int(m.group(1)) / 1000, int(m.group(2)) / 1000))
    return {d: sorted(p) for d, p in holes.items()}


def copper_order(board_text: str) -> dict[str, str]:
    """The expected file function of each copper layer, from the `layers` block of the saved board."""
    block = re.search(r"\(layers\s(.*?)\n\t\)", board_text, re.S)
    names = re.findall(r'\(\d+ "([^"]+\.Cu)" signal', block.group(1)) if block else []
    # Stack order of KiCad: F.Cu is the top layer, In1.Cu to InN.Cu follow by number, B.Cu is the bottom layer.
    rank = lambda n: (0, 0) if n == "F.Cu" else (2, 0) if n == "B.Cu" else (1, int(re.sub(r"\D", "", n) or 0))  # noqa: E731
    names = sorted(names, key=rank)
    out = {}
    for i, name in enumerate(names, 1):
        position = "Top" if i == 1 else "Bot" if i == len(names) else "Inr"
        out[name.replace(".", "_")] = f"Copper,L{i},{position}"
    return out


def plot_settings(board_text: str) -> dict[str, list[str]]:
    return {key: re.findall(rf"\({key} ([^)]*)\)", board_text) for key in PLOT_SETTINGS}


def check(export: Path, board: Path) -> list[dict]:
    results = []
    board_text = board.read_text()

    def add(name, ok, detail=""):
        results.append({"check": name, "status": "pass" if ok else "fail", "detail": detail})

    saved = plot_settings(board_text)
    add("board.plot_settings", all(saved[k] == [v] for k, v in PLOT_SETTINGS.items()), f"saved {saved}, expected {PLOT_SETTINGS}")
    found = sorted(p.name for p in export.glob("*.gbr"))
    wanted = sorted(f"{PREFIX}-{n}.gbr" for n in GERBERS)
    add("gerber.layer_set", found == wanted, f"found {found}")
    functions = {**FUNCTION, **copper_order(board_text)}
    wanted_functions = {f"{PREFIX}-{n}.gbr": functions.get(n) for n in GERBERS}
    bad_attr, bad_function = [], []
    for name, want in wanted_functions.items():
        path = export / name
        if not path.is_file():
            bad_attr.append(f"{name}: missing")
            bad_function.append(f"{name}: missing")
            continue
        lines = path.read_text().splitlines()
        active = [line for line in lines if ACTIVE_ATTRIBUTE.match(line)]
        if active:
            bad_attr.append(f"{name}: {len(active)} active attribute commands")
        declared = [m.group(1) for m in map(FUNCTION_COMMENT.match, lines) if m]
        if declared != [want]:
            bad_function.append(f"{name}: declared {declared}, expected {[want]}")
    add("gerber.no_active_attributes", not bad_attr, "; ".join(bad_attr))
    add("gerber.layer_function", not bad_function and None not in wanted_functions.values(), "; ".join(bad_function))
    plated, nonplated = expected_holes()
    for name, expect in (("PTH", plated), ("NPTH", nonplated)):
        path = export / f"{PREFIX}-{name}.drl"
        got = parse_drill(path.read_text()) if path.is_file() else None
        add(f"drill.{name.lower()}", got == expect, f"expected {expect}, got {got}")
    pos = export / f"{PREFIX}-pos.csv"
    listed = []
    if pos.is_file():
        for row in csv.DictReader(pos.open()):
            listed.append((row["Ref"], float(row["PosX"]), float(row["PosY"]), float(row["Rot"]), row["Side"]))
    refs = [r[0] for r in listed]
    rows = {r[0]: r[1:] for r in listed}
    expect = expected_rows()
    # A repeated reference fails before any comparison, in either row order. The row count is exact.
    ok = (len(listed) == len(expect) and len(set(refs)) == len(refs) and set(rows) == set(expect)
          and all(rows[r][:3] == expect[r] and rows[r][3] == "top" for r in expect))
    add("placement.rows", ok, f"expected {expect}, got {listed}")
    return results


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    if len(args) != 2 or not Path(args[0]).is_dir() or not Path(args[1]).is_file():
        print(json.dumps({"error": "check_exports: give the export directory and the saved board"}))
        return 2
    results = check(Path(args[0]), Path(args[1]))
    print(json.dumps(results, indent=2) if as_json else "\n".join(f"{r['status']:4} {r['check']}" for r in results))
    return 0 if all(r["status"] == "pass" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
