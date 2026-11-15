# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Compare the drilled slots of the saved board with the slot records of the export.

Usage: uv run scripts/inspect_slots.py --board-inventory INV.json --pth PTH.drl --npth NPTH.drl --report OUT.json

Exit status: 0 every slot matches, 1 a mismatch, 2 an unsupported record, 3 a missing or unreadable input.

Method:
- The expected plated class comes from the board attribute of each slot: `pth` is the plated file,
  `npth` is the non-plated file. The export file class is never used to choose the expected class.
- Each board slot matches one export record of the same class. Endpoint pairs are unordered.
- A coordinate matches when it differs by no more than 501 nanometres (0.000501 mm). The export grid is
  1 micrometre, and the rounding error is at most 500 nanometres. One nanometre is added for floating-point margin.
- The minor width of the board slot matches the `T` tool width of the export record under the same tolerance.
- A slot whose major and minor dimensions differ by less than 1 micrometre is `near_circular`.
  Its orientation is not reported. Its endpoint match still applies.
- Multiplicity is kept. Each board slot consumes one export record. A missing or extra record is a mismatch.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import export_inspect  # noqa: E402

TOL_NM = 501
NEAR_CIRCULAR_NM = 1000
EXIT_OK, EXIT_MISMATCH, EXIT_UNSUPPORTED, EXIT_TOOL = 0, 1, 2, 3
CLASS_OF_ATTR = {"pth": "pth", "npth": "npth"}


def nm(value_mm):
    return round(float(value_mm) * 1_000_000)


def board_slots(inventory):
    """Return the board slots as dicts with integer nanometres. Refuse any attribute other than pth or npth."""
    out = []
    for slot in inventory.get("slots", []):
        attr = slot.get("attr")
        if attr not in CLASS_OF_ATTR:
            raise export_inspect.UnsupportedRecord(f"unsupported slot attribute {attr!r} at {slot.get('object')}")
        (x1, y1), (x2, y2) = slot["endpoints_mm"]
        # The Excellon Y axis is the negative of the board Y axis (the B6 check convention).
        out.append({"object": slot["object"], "class": CLASS_OF_ATTR[attr],
                    "points_nm": [(nm(x1), -nm(y1)), (nm(x2), -nm(y2))],
                    "minor_nm": nm(slot["minor_mm"]), "major_nm": nm(slot["major_mm"])})
    return out


def _close(a, b):
    return abs(a[0] - b[0]) <= TOL_NM and abs(a[1] - b[1]) <= TOL_NM


def _same_endpoints(p, q):
    return (_close(p[0], q[0]) and _close(p[1], q[1])) or (_close(p[0], q[1]) and _close(p[1], q[0]))


def compare_class(board, export_records):
    """Match the board slots of one class with the export slot records of the same class."""
    unmatched_export = [r for r in export_records if r["kind"] == "slot"]
    result = {"matched": [], "missing_in_export": [], "extra_in_export": [], "near_circular": []}
    for slot in board:
        found = None
        for i, rec in enumerate(unmatched_export):
            if abs(rec["width_nm"] - slot["minor_nm"]) > TOL_NM:
                continue
            if _same_endpoints(slot["points_nm"], rec["points_nm"]):
                found = i
                break
        if found is None:
            result["missing_in_export"].append(slot["object"])
            continue
        rec = unmatched_export.pop(found)
        result["matched"].append(slot["object"])
        if slot["major_nm"] - slot["minor_nm"] < NEAR_CIRCULAR_NM:
            result["near_circular"].append(slot["object"])
    result["extra_in_export"] = [f"slot at {r['points_nm']} width {r['width_nm']} nm" for r in unmatched_export]
    return result


def inspect(inventory, pth_text, npth_text):
    """Return (exit status, report dict)."""
    report = {"tolerance_nm": TOL_NM, "classes": {}}
    try:
        slots = board_slots(inventory)
        records = {"pth": export_inspect.parse(pth_text), "npth": export_inspect.parse(npth_text)}
    except export_inspect.UnsupportedRecord as err:
        report["error"] = str(err)
        return EXIT_UNSUPPORTED, report
    status = EXIT_OK
    for cls in ("pth", "npth"):
        part = compare_class([s for s in slots if s["class"] == cls], records[cls])
        bad = part["missing_in_export"] or part["extra_in_export"]
        part["status"] = "mismatch" if bad else "pass"
        report["classes"][cls] = part
        if bad:
            status = EXIT_MISMATCH
    return status, report


def main(argv):
    args = {}
    for key in ("--board-inventory", "--pth", "--npth", "--report"):
        if key not in argv or argv.index(key) + 1 >= len(argv):
            print(f"inspect_slots: missing argument {key}", file=sys.stderr)
            return 2
        args[key] = argv[argv.index(key) + 1]
    try:
        inventory = json.loads(pathlib.Path(args["--board-inventory"]).read_text())
        pth_text = pathlib.Path(args["--pth"]).read_text()
        npth_text = pathlib.Path(args["--npth"]).read_text()
    except (OSError, ValueError) as err:
        print(f"inspect_slots: cannot read an input: {err}", file=sys.stderr)
        return 3
    status, report = inspect(inventory, pth_text, npth_text)
    pathlib.Path(args["--report"]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"exit": status, "tolerance_nm": TOL_NM}))
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
