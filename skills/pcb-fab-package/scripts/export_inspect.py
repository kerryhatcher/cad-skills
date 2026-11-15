"""Read the KiCad Excellon drill files of the export. This reader covers the measured subset only.

Derived from the B6 export checks in `skills/pcb-design/scripts/pcb.py` (function `excellon`). It keeps the
round-hole form and adds the `G85` slot record. It is not a general Excellon parser.

The accepted subset (measured with KiCad 10.0.5, `b7-prereq-trials-claude.md` section 3):
- header: `METRIC,TZ`, `FMAT,2`, and the comment `FORMAT={3:3/ absolute / metric / suppress leading zeros}`;
- coordinates: integer micrometres, `X<int>Y<int>`, with an optional `G85X<int>Y<int>` slot end;
- tool definitions: `T<n>C<d>.<ddd>` before the `%` line, exactly three decimals, each tool number once;
- commands: `G90`, `G05`, `M48`, `%`, and selection `T<n>` of a defined tool;
- the file ends with the terminal `M30`. A missing `M30` and any record after it are refused.

Anything else raises `UnsupportedRecord`. The caller refuses the file with exit 2. A tool width is never
rounded to a passing value. A width without exactly three decimals is refused.
"""
import re

NM_PER_UM = 1000
HEADER_COMMENT = "; FORMAT={3:3/ absolute / metric / suppress leading zeros}"
SLOT_RE = re.compile(r"^X(-?\d+)Y(-?\d+)G85X(-?\d+)Y(-?\d+)$")
HOLE_RE = re.compile(r"^X(-?\d+)Y(-?\d+)$")
TOOL_DEF_RE = re.compile(r"^T(\d+)C(\d+)\.(\d{3})$")
TOOL_SEL_RE = re.compile(r"^T(\d+)$")
PLAIN_COMMANDS = {"M48", "%", "G90", "G05", "M30"}


class UnsupportedRecord(Exception):
    """A drill record or header state outside the measured subset. The caller refuses the file."""


def _nm(text):
    return int(text) * NM_PER_UM


def parse(text):
    """Return the slot and hole records in file order. Each record has `kind` (`hole` or `slot`),
    `width_nm` (the tool width of the record), and `points_nm` (one point for a hole, two for a slot)."""
    tools, records = {}, []
    header_seen = set()
    body = False  # True after the `%` line, which ends the header
    ended = False  # True after the terminal M30
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";"):
            if line == HEADER_COMMENT or line.startswith(("; DRILL file", "; #@!")):
                continue
            raise UnsupportedRecord(f"unsupported header comment: {line}")
        if not body:
            if line in ("METRIC,TZ", "FMAT,2"):
                if line in header_seen:
                    raise UnsupportedRecord(f"duplicate header line: {line}")
                header_seen.add(line)
                continue
            if line.startswith("INCH") or line == "M72" or line.startswith("METRIC"):
                raise UnsupportedRecord(f"unsupported units or format declaration: {line}")
            m = TOOL_DEF_RE.match(line)
            if m:
                if m.group(1) in tools:
                    raise UnsupportedRecord(f"duplicate tool definition T{m.group(1)}")
                tools[m.group(1)] = int(m.group(2)) * 1000 * NM_PER_UM + int(m.group(3)) * NM_PER_UM
                continue
            if line == "M48":
                continue
            if line == "%":
                if header_seen != {"METRIC,TZ", "FMAT,2"}:
                    raise UnsupportedRecord("the header must declare METRIC,TZ and FMAT,2 before the body")
                body = True
                continue
            raise UnsupportedRecord(f"unsupported header line: {line}")
        if ended:
            raise UnsupportedRecord(f"a record follows the terminal M30: {line}")
        if line == "M30":
            ended = True
            continue
        if line in PLAIN_COMMANDS:
            continue
        if line.startswith(("INCH", "METRIC")) or line == "M72":
            raise UnsupportedRecord(f"unsupported units declaration in the body: {line}")
        m = TOOL_SEL_RE.match(line)
        if m:
            if m.group(1) not in tools:
                raise UnsupportedRecord(f"tool T{m.group(1)} is not defined")
            current = tools[m.group(1)]
            continue
        if current is None:
            raise UnsupportedRecord(f"coordinate before a tool selection: {line}")
        m = SLOT_RE.match(line)
        if m:
            records.append({"kind": "slot", "width_nm": current,
                            "points_nm": [(_nm(m.group(1)), _nm(m.group(2))), (_nm(m.group(3)), _nm(m.group(4)))]})
            continue
        m = HOLE_RE.match(line)
        if m:
            records.append({"kind": "hole", "width_nm": current, "points_nm": [(_nm(m.group(1)), _nm(m.group(2)))]})
            continue
        raise UnsupportedRecord(f"unsupported drill record: {line}")
    if not body:
        raise UnsupportedRecord("the drill file has no body (no % line)")
    if not ended:
        raise UnsupportedRecord("the drill file has no terminal M30")
    return records
