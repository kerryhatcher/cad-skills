# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Deterministic text edits of the native schematic for the gate edits and limit probes.

  uv run scripts/edit_native.py OP --in native/trial.kicad_sch --out NEW.kicad_sch

OP: value-r2 | reorder | add-c2 | remove-d1 | footprint-r1 | rename-c1 | none
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from pathlib import Path

NS = uuid.UUID("6f1c2a9e-0b7d-4c55-9a3e-2f7f6c1d9b11")


def span(text, start):
    """The end of the parenthesized form that starts at `start` (quote-aware)."""
    depth, i = 0, text.index("(", start)
    while True:
        c = text[i]
        if c == '"':
            i += 1
            while text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1


def block(text, ref):
    at = text.index(f'(property "Reference" "{ref}"')
    start = text.rindex("\n\t(symbol\n", 0, at) + 1
    return start, span(text, start)


def label_block(text, net, ref, number):
    marker = f'(uuid "{uuid.uuid5(NS, f"{ref}/label/{number}")}")'
    at = text.index(marker)
    start = text.rindex("\n\t(label ", 0, at) + 1
    return start, span(text, start)


def apply(op: str, text: str) -> str:
    if op == "none":
        return text
    if op == "value-r2":
        a, b = block(text, "R2")
        return text[:a] + text[a:b].replace('(property "Value" "10k"', '(property "Value" "22k"', 1) + text[b:]
    if op == "footprint-r1":
        a, b = block(text, "R1")
        return text[:a] + text[a:b].replace("Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_0805_2012Metric", 1) + text[b:]
    if op == "rename-c1":
        a, b = block(text, "C1")
        new = text[a:b].replace('(property "Reference" "C1"', '(property "Reference" "C9"', 1).replace('(reference "C1")', '(reference "C9")', 1)
        return text[:a] + new + text[b:]
    if op == "reorder":
        a, b = block(text, "R2")
        r2 = text[a:b]
        text = text[:a] + text[b:]
        j, _ = block(text, "J1")
        return text[:j] + r2.lstrip("\n") + "\n" + text[j:]
    if op == "remove-d1":
        a, b = block(text, "D1")
        text = text[:a] + text[b:].lstrip("\n")
        for number in ("1", "2"):
            la, lb = label_block(text, "", "D1", number)
            text = text[:la] + text[lb:].lstrip("\n")
        return text
    if op == "add-c2":
        a, b = block(text, "C1")
        c2 = text[a:b]
        c2 = c2.replace('(property "Reference" "C1"', '(property "Reference" "C2"', 1).replace('(reference "C1")', '(reference "C2")', 1)
        c2 = c2.replace("(at 152.4 101.6 0)", "(at 152.4 127 0)", 1)
        c2 = re.sub(r'\(uuid "[0-9a-f-]+"\)', lambda m, it=iter(range(1000)): f'(uuid "{uuid.uuid5(NS, "C2/" + str(next(it)))}")', c2)
        labels = "".join(
            f'\t(label "{net}"\n\t\t(at 152.4 {y} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{uuid.uuid5(NS, f"C2/label/{n}")}")\n\t)\n'
            for n, net, y in (("1", "N_RC", 123.19), ("2", "GND", 130.81)))
        return text[:b] + "\n" + c2.lstrip("\n") + "\n" + labels + text[b:]
    raise SystemExit(f"unknown operation {op}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("op")
    parser.add_argument("--in", dest="inp", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    Path(args.out).write_text(apply(args.op, Path(args.inp).read_text()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
