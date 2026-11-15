"""Semantic export checks for pcb-fab-package. An owned derivative of the accepted B6 export checks.

Checks in this module:
- the file function of each Gerber layer is exactly the function that the layer and the copper order require;
- each Gerber declares its file function exactly once;
- each drill file holds the complete multiset of its holes: position (to the export grid), tool diameter and
  plating class, compared with the saved board inventory. Equal counts alone do not pass.

Coordinates use integer nanometres. The Excellon Y axis is the negative of the board Y axis (B6 convention).
Positions match when each coordinate differs by at most 500 nm. This is half of the 1 micrometre export grid.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import export_inspect  # noqa: E402

GRID_TOL_NM = 500
FUNCTION_RE = re.compile(r"^G04 #@! TF\.FileFunction,([^*]+)\*$", re.M)
X2_RE = re.compile(r"^%T[FAOD]", re.M)
NON_COPPER = {
    "F.Mask": "Soldermask,Top", "B.Mask": "Soldermask,Bot", "F.Silkscreen": "Legend,Top",
    "B.Silkscreen": "Legend,Bot", "F.Paste": "Paste,Top", "B.Paste": "Paste,Bot", "Edge.Cuts": "Profile,NP",
}


def expected_function(kicad_layer, copper_order):
    """The exact FileFunction text of a layer. `copper_order` lists the copper layers, top first."""
    if kicad_layer in NON_COPPER:
        return NON_COPPER[kicad_layer]
    if kicad_layer not in copper_order:
        raise ValueError(f"layer {kicad_layer} is not a copper layer of the board")
    index = copper_order.index(kicad_layer)
    count = len(copper_order)
    if index == 0:
        side = "Top"
    elif index == count - 1:
        side = "Bot"
    else:
        side = "Inr"
    return f"Copper,L{index + 1},{side}"


def function_problems(contract, export_dir, copper_order):
    """Return a list of problems with the file functions of the exported Gerbers."""
    problems = []
    for layer in contract["layers"]:
        name = "board" + layer["suffix"]
        path = export_dir / name
        if not path.is_file():
            problems.append(f"{name} is missing")
            continue
        text = path.read_text(errors="replace")
        if X2_RE.search(text):
            problems.append(f"{name} has active X2 attributes; the contract requires X2 off")
        found = FUNCTION_RE.findall(text)
        want = expected_function(layer["kicad_layer"], copper_order)
        if len(found) != 1:
            problems.append(f"{name} declares its function {len(found)} times")
        elif found[0] != want:
            problems.append(f"{name} declares {found[0]!r}, expected {want!r}")
    return problems


def expected_holes(inventory):
    """Return (plated, nonplated) lists of (x_nm, y_nm, width_nm) from the saved inventory. Vias are plated."""
    plated, nonplated = [], []
    for hole in inventory.get("holes", []):
        point = (round(hole["x"] * 1e6), -round(hole["y"] * 1e6), round(hole["diameter"] * 1e6))
        (plated if hole["attr"] == "pth" else nonplated).append(point)
    return plated, nonplated


def _match(expected, actual):
    """Greedy multiset match with the grid tolerance. Return the unmatched expected and actual points."""
    remaining = list(actual)
    unmatched = []
    for e in expected:
        for i, a in enumerate(remaining):
            if all(abs(e[k] - a[k]) <= GRID_TOL_NM for k in range(3)):
                remaining.pop(i)
                break
        else:
            unmatched.append(e)
    return unmatched, remaining


def drill_problems(inventory, export_dir, suffix_plated="-PTH.drl", suffix_nonplated="-NPTH.drl"):
    """Compare each drill file with the saved board holes. Return a list of problems."""
    problems = []
    plated, nonplated = expected_holes(inventory)
    for label, suffix, expected in (("plated", suffix_plated, plated), ("nonplated", suffix_nonplated, nonplated)):
        path = export_dir / ("board" + suffix)
        if not path.is_file():
            problems.append(f"{label} drill file is missing")
            continue
        try:
            records = export_inspect.parse(path.read_text())
        except export_inspect.UnsupportedRecord as err:
            problems.append(f"{label} drill file is unsupported: {err}")
            continue
        actual = []
        for rec in records:
            if rec["kind"] != "hole":
                continue
            (x, y) = rec["points_nm"][0]
            actual.append((x, y, rec["width_nm"]))
        missing, extra = _match(expected, actual)
        if missing:
            problems.append(f"{label}: {len(missing)} board holes are not in the file, first {missing[0]}")
        if extra:
            problems.append(f"{label}: {len(extra)} file holes are not on the board, first {extra[0]}")
    return problems
