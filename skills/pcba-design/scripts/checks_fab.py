"""Fabrication checks for the pcba-design package. Each function returns one result dict.

The checks read the captured bytes and the captured records. They never read a live project path.
A supplier convention that is not confirmed returns `unconfirmed`, and the reason names the open
convention. A check with no input returns `pending`.
"""

from __future__ import annotations

import hashlib
import json
import re

from checks_design import _result

TOOL = {"name": "pcba-design", "version": "1.0"}
MM_PER_INCH = 25.4
# KiCad writes the Excellon Y axis with the opposite sign to the board Y axis. Measured on the
# standard fixture: the via at Y 30 mm is written as Y-011811 (inch, 2.4 format).
EXCELLON_Y_SIGN = -1
# The Gerber function that each export role must carry in its file content (X2 FileFunction).
ROLE_FUNCTION = {
    "copper_top": "Copper,L1,Top", "copper_bottom": "Copper,L2,Bot",
    "mask_top": "Soldermask,Top", "mask_bottom": "Soldermask,Bot",
    "silk_top": "Legend,Top", "silk_bottom": "Legend,Bot",
    "paste_top": "Paste,Top", "paste_bottom": "Paste,Bot",
    "outline": "Profile,NP", "fabrication": "AssemblyDrawing,Top",
}
DRILL_PLATING = {"plated": True, "nonplated": False}
EXCELLON_FIXED = ("M48", "%", "G90", "G05", "M30", "FMAT,2", "INCH,LZ")
EXCELLON_TOOL = re.compile(r"^T(\d+)C([-+]?[0-9.]+)$")
EXCELLON_HIT = re.compile(r"^X([-+]?[0-9.]+)Y([-+]?[0-9.]+)$")
EXCELLON_SELECT = re.compile(r"^T(\d+)$")


def _json_bytes(data) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def profile_evidence(evidence, expected_sha256: str) -> dict:
    """fab.profile_evidence: pass when the retained evidence bytes hash to the profile `evidence_sha256`.

    No retained evidence gives pending, because the input is absent. Changed bytes give fail.
    """
    if evidence is None:
        return _result("fab.profile_evidence", "pending", "tool", TOOL, None,
                       [{"code": "fab.evidence_absent", "text": "No retained supplier evidence is captured."}],
                       "not run")
    digest = hashlib.sha256(evidence).hexdigest()
    artifact = {"path": "reports/supplier-evidence.txt", "bytes": evidence}
    if digest != expected_sha256:
        return _result("fab.profile_evidence", "fail", "tool", TOOL, artifact,
                       [{"code": "fab.evidence_changed", "text": "The evidence bytes differ from the profile hash."}],
                       "hash mismatch")
    return _result("fab.profile_evidence", "pass", "tool", TOOL, artifact, [],
                   "evidence hash matches the profile")


def export_inventory(actual: dict, expected: dict) -> dict:
    """fab.export_inventory: compare the written file names with the names that the settings expect.

    `expected` maps each expected file name to its role. `actual` maps each written file name to its bytes.
    Missing files and extra files are counted separately. Empty files are counted as a third problem.
    """
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    empty = sorted(name for name, data in actual.items() if name in expected and not data)
    reasons = [{"code": "fab.file_missing", "text": f"Expected file {name} is not written."} for name in missing]
    reasons += [{"code": "fab.file_extra", "text": f"File {name} is not in the export settings."} for name in extra]
    reasons += [{"code": "fab.file_empty", "text": f"Expected file {name} has 0 bytes."} for name in empty]
    body = _json_bytes({"expected": sorted(expected), "missing": missing, "extra": extra, "empty": empty})
    status = "fail" if reasons else "pass"
    return _result("fab.export_inventory", status, "tool", TOOL,
                   {"path": "reports/export-inventory.json", "bytes": body}, reasons,
                   f"expected={len(expected)} missing={len(missing)} extra={len(extra)}")


def layer_order(gerbers: dict, layers: list) -> dict:
    """fab.layer_order: find each settings layer by the FileFunction line in the file content.

    `layers` lists (role, kicad_layer) pairs from the export settings. The file name is not used.
    A layer needs exactly one file with its function. The result holds `layer_files`, which maps
    each KiCad layer to the file name that carries its function.
    """
    problems, layer_files = [], {}
    for role, kicad_layer in layers:
        function = ROLE_FUNCTION.get(role)
        if function is None:
            problems.append(f"{kicad_layer} has no supported role {role}")
            continue
        wanted = f"%TF.FileFunction,{function}*%"
        found = sorted(name for name, data in gerbers.items() if wanted in data.decode("utf-8", errors="replace"))
        if len(found) != 1:
            problems.append(f"{kicad_layer} needs one file with FileFunction {function}; found {len(found)}")
            continue
        layer_files[kicad_layer] = found[0]
    reasons = [{"code": "fab.layer_function", "text": text} for text in problems]
    body = _json_bytes({"layers": [kicad for _, kicad in layers], "problems": problems, "files": layer_files})
    status = "fail" if problems else "pass"
    result = _result("fab.layer_order", status, "tool", TOOL,
                     {"path": "reports/layer-order.json", "bytes": body}, reasons,
                     f"layers={len(layers)} problems={len(problems)}")
    result["layer_files"] = layer_files
    return result


def _coordinate(token: str, decimals: int) -> float:
    """Return an inch value. A token with a decimal point is exact.

    Otherwise the point is implied after `decimals` digits, in a field of 2 integer digits plus
    `decimals` digits. KiCad suppresses the trailing zeros of the field. The reader adds them back,
    so `01` with 4 decimals is 1.0000 inch.
    """
    if "." in token:
        return float(token)
    sign = -1 if token.startswith("-") else 1
    digits = token.lstrip("+-")
    width = 2 + decimals
    if len(digits) > width:
        raise ValueError(f"The coordinate {token!r} is wider than the format.")
    return sign * int(digits.ljust(width, "0")) / (10 ** decimals)


def parse_excellon(raw: bytes, decimals: int) -> dict:
    """Read one inch Excellon file. Return {"problems": [...], "tools": {...}, "hits": [(x_mm, y_mm, tool)]}.

    The header must state inch units, format 2 and leading zeros, which is trailing-zero suppression.
    A line that the reader does not know is a problem. Coordinates and diameters are in inches here
    and in millimeters in the result.
    """
    text = raw.decode("utf-8", errors="replace")
    problems, tools, hits = [], {}, []
    tool = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";") or line in EXCELLON_FIXED:
            continue
        select = EXCELLON_SELECT.match(line)
        if select:
            tool = int(select.group(1))
            continue
        tool_def = EXCELLON_TOOL.match(line)
        if tool_def:
            tools[int(tool_def.group(1))] = float(tool_def.group(2)) * MM_PER_INCH
            continue
        hit = EXCELLON_HIT.match(line)
        if hit and tool is not None:
            try:
                x_in = _coordinate(hit.group(1), decimals)
                y_in = _coordinate(hit.group(2), decimals)
            except ValueError as err:
                problems.append(str(err))
                continue
            hits.append((x_in * MM_PER_INCH, EXCELLON_Y_SIGN * y_in * MM_PER_INCH, tool))
            continue
        problems.append(f"The line {line!r} is not recognized.")
    if "INCH,LZ" not in text or "FMAT,2" not in text:
        problems.append("The header does not state inch units, format 2 and trailing-zero suppression.")
    return {"problems": problems, "tools": tools, "hits": hits}


def drill_split(drills: dict, decimals: int, holes: list, plated_name: str, nonplated_name: str) -> dict:
    """fab.drill_split: compare the holes of the drill files with the captured board inventory.

    `holes` comes from all drilled pads and vias in the captured board. Each hole has x, y, diameter_mm and plated. Each inventory
    hole needs one file hole with the same position, diameter and plating. Each file hole needs one
    inventory hole. Duplicate holes count once for each copy. The tolerance is half of one count
    of the coordinate format.
    """
    tol = 0.5 * MM_PER_INCH / (10 ** decimals) + 1e-9
    reasons, file_holes = [], []
    for name, plated in ((plated_name, True), (nonplated_name, False)):
        raw = drills.get(name)
        if raw is None:
            reasons.append({"code": "fab.drill_file_absent", "text": f"The drill file {name} is not written."})
            continue
        parsed = parse_excellon(raw, decimals)
        for problem in parsed["problems"]:
            reasons.append({"code": "fab.drill_format", "text": f"{name}: {problem}"})
        for x, y, tool in parsed["hits"]:
            if tool not in parsed["tools"]:
                reasons.append({"code": "fab.drill_format", "text": f"{name}: tool {tool} has no diameter."})
                continue
            file_holes.append({"file": name, "x": x, "y": y, "d": parsed["tools"][tool], "plated": plated})
    unmatched = list(file_holes)
    rows = []
    for hole in holes:
        match = None
        for item in unmatched:
            if (abs(item["x"] - hole["x"]) <= tol and abs(item["y"] - hole["y"]) <= tol
                    and abs(item["d"] - hole["diameter_mm"]) <= tol and item["plated"] == hole["plated"]):
                match = item
                break
        if match is None:
            reasons.append({"code": "fab.drill_missing",
                            "text": f"Hole {hole['id']} at ({hole['x']}, {hole['y']}) is not in the drill files."})
        else:
            unmatched.remove(match)
        rows.append({"hole": hole["id"], "matched": match is not None})
    for item in unmatched:
        reasons.append({"code": "fab.drill_extra",
                        "text": f"{item['file']} has a hole at ({item['x']:.4f}, {item['y']:.4f}) with no inventory hole."})
    body = _json_bytes({"inventory": rows, "file_holes": len(file_holes), "unmatched": len(unmatched)})
    status = "fail" if reasons else "pass"
    return _result("fab.drill_split", status, "tool", TOOL,
                   {"path": "reports/drill-split.json", "bytes": body}, reasons,
                   f"inventory={len(holes)} file_holes={len(file_holes)} problems={len(reasons)}")


def supplier_rules(rules: dict, settings: dict, export: dict) -> dict:
    """fab.supplier_rules: compare the export settings with the supplier rules. Open conventions stay unconfirmed.

    The rules record holds the required Gerber and drill settings. The settings record holds the
    placement conventions, each with a `status`. Only `confirmed` counts as confirmed. The check
    never returns pass while the plane interpretation or a placement convention is not confirmed.
    """
    mismatches = []
    pairs = [
        ("gerber.format", rules["gerber"]["format"], export["format"]),
        ("drill.format", rules["drill"]["format"], export["drill"]["format"]),
        ("drill.units", rules["drill"]["units"], export["extensions"]["pcba"]["drill_units"]),
        ("drill.origin", rules["drill"]["origin"], export["origin"]),
        ("drill.zero_suppression", rules["drill"]["zero_suppression"], export["drill"]["zero_suppression"]),
        ("drill.decimal_places", rules["drill"]["decimal_places"], export["drill"]["decimal_places"]),
        ("drill.separate_files", rules["drill"]["separate_files"], export["drill"]["separate_files"]),
    ]
    for name, required, actual in pairs:
        if required != actual:
            mismatches.append(name)
    reasons = [{"code": "fab.rule_mismatch", "text": f"The export setting {name} differs from the supplier rule."}
               for name in mismatches]
    open_items = []
    if rules["plane_interpretation"]["status"] != "confirmed":
        open_items.append("plane_interpretation")
        reasons.append({"code": "fab.plane_unconfirmed", "text": "The plane interpretation is unconfirmed."})
    for field, entry in sorted(settings["placement"].items()):
        if entry["status"] != "confirmed":
            open_items.append(field)
    if any(item != "plane_interpretation" for item in open_items):
        names = ", ".join(item for item in open_items if item != "plane_interpretation")
        reasons.append({"code": "fab.xy_unconfirmed",
                        "text": f"The placement conventions are unconfirmed: {names}."})
    body = _json_bytes({"mismatches": mismatches, "open": open_items})
    if mismatches:
        status = "fail"
    elif open_items:
        status = "unconfirmed"
    else:
        status = "pass"
    return _result("fab.supplier_rules", status, "tool", TOOL,
                   {"path": "reports/supplier-rules.json", "bytes": body}, reasons,
                   f"mismatches={len(mismatches)} open={len(open_items)}")
