"""Design checks for the pcba-design package. Each check returns one result dict.

A result holds these keys:
- id: the check ID.
- status: pass, fail, pending or unconfirmed.
- method: tool or manual.
- tool: the tool name and version, or None.
- artifact: a dict with `path` and `bytes`, or None.
- reasons: a list of code and text.
- observed: a short summary.
The checks read captured bytes only. A check that has no input returns pending. It never returns
pass without a measured artifact.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import sexp

def _result(check_id, status, method, tool, artifact, reasons, observed):
    return {"id": check_id, "status": status, "method": method, "tool": tool,
            "artifact": artifact, "reasons": reasons, "observed": observed}


def _tool(version: str) -> dict:
    return {"name": "kicad-cli", "version": version}


def drc(drc_bytes: bytes, kicad_version: str) -> dict:
    """design.drc: pass only when the DRC report has no violations and no unconnected items.

    Warnings count as violations. The report of KiCad exits 0 even when it reports violations, so
    the counts come from the JSON.
    """
    report = json.loads(drc_bytes.decode("utf-8"))
    violations = len(report.get("violations", []))
    unconnected = len(report.get("unconnected_items", []))
    reasons = []
    if violations:
        reasons.append({"code": "drc.violations", "text": f"The DRC reports {violations} violations."})
    if unconnected:
        reasons.append({"code": "drc.unconnected", "text": f"The DRC reports {unconnected} unconnected items."})
    status = "fail" if reasons else "pass"
    return _result("design.drc", status, "tool", _tool(kicad_version),
                   {"path": "reports/drc.json", "bytes": drc_bytes}, reasons,
                   f"violations={violations} unconnected={unconnected}")


def erc(erc_bytes, kicad_version: str) -> dict:
    """design.erc: pass only when the ERC report lists no violation of any severity.

    With no schematic bytes the check is pending, because no input exists to examine.
    """
    if erc_bytes is None:
        return _result("design.erc", "pending", "tool", None, None,
                       [{"code": "design.schematic_absent", "text": "No schematic input is captured."}],
                       "not run")
    report = json.loads(erc_bytes.decode("utf-8"))
    count = sum(len(sheet.get("violations", [])) for sheet in report.get("sheets", []))
    reasons = [{"code": "design.erc_violations", "text": f"The ERC reports {count} violations."}] if count else []
    return _result("design.erc", "fail" if count else "pass", "tool", _tool(kicad_version),
                   {"path": "reports/erc.json", "bytes": erc_bytes}, reasons, f"violations={count}")


def schematic_pads(netlist_bytes: bytes) -> dict:
    """Return {(reference, pin): net} from a KiCad XML netlist. Pins without a net are absent."""
    root = ET.fromstring(netlist_bytes)
    pairs = {}
    for net in root.iter("net"):
        name = net.get("name")
        for node in net.iter("node"):
            key = (node.get("ref"), node.get("pin"))
            if key in pairs:
                raise ValueError(f"The netlist lists pin {key} two times.")
            pairs[key] = name
    return pairs


def board_pads(board_bytes: bytes) -> dict:
    """Return {(reference, pad number): net} from the footprints of a KiCad board. Pads without a net are absent."""
    tree = sexp.parse(board_bytes.decode("utf-8"))
    pairs = {}

    def walk(node):
        if not isinstance(node, list) or not node:
            return
        if node[0] == "footprint":
            ref = None
            for item in node:
                if isinstance(item, list) and item and item[0] == "property" and item[1] == "Reference":
                    ref = str(item[2])
            for item in node:
                if isinstance(item, list) and item and item[0] == "pad":
                    for part in item:
                        if isinstance(part, list) and part and part[0] == "net" and len(part) >= 3:
                            pairs[(ref, str(item[1]))] = str(part[2])
        for item in node:
            walk(item)

    walk(tree)
    return pairs


def parity(netlist_bytes, board_bytes: bytes, kicad_version: str) -> dict:
    """design.parity: pass only when each schematic pin and each board pad carry the same net name.

    Pads without a net and pins without a net are not compared. Each difference is one reason.
    """
    if netlist_bytes is None:
        return _result("design.parity", "pending", "tool", None, None,
                       [{"code": "design.schematic_absent", "text": "No schematic input is captured."}],
                       "not run")
    try:
        sch = schematic_pads(netlist_bytes)
    except (ET.ParseError, ValueError) as err:
        return _result("design.parity", "fail", "tool", _tool(kicad_version), None,
                       [{"code": "design.netlist_unreadable", "text": f"The netlist is not readable: {err}"}],
                       "netlist unreadable")
    brd = board_pads(board_bytes)
    reasons, lines = [], []
    for key in sorted(set(sch) | set(brd), key=lambda k: (str(k[0]), str(k[1]))):
        if sch.get(key) != brd.get(key):
            text = f"{key[0]} pad {key[1]}: schematic net {sch.get(key)!r}, board net {brd.get(key)!r}."
            reasons.append({"code": "design.parity_mismatch", "text": text})
            lines.append(text)
    artifact = {"path": "reports/parity.json", "bytes": (json.dumps(
        {"schematic_pins": len(sch), "board_pads": len(brd), "mismatches": lines}, indent=2, sort_keys=True)
        + "\n").encode("utf-8")}
    return _result("design.parity", "fail" if reasons else "pass", "tool", _tool(kicad_version), artifact,
                   reasons, f"pins={len(sch)} pads={len(brd)} mismatches={len(reasons)}")
