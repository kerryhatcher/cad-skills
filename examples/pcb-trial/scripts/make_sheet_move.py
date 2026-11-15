# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Limit probe: move the symbol R2 of the native schematic into a hierarchical sub-sheet. Host script.

  uv run scripts/make_sheet_move.py IN.kicad_sch OUTDIR

It writes OUTDIR/trial.kicad_sch (root) and OUTDIR/sub.kicad_sch. The symbol keeps its UUID, its reference and its value.
The path of the symbol changes from `/ROOT/SYMBOL` to `/ROOT/SHEET/SYMBOL`. The nets VIN and N_RC reach R2 through
two sheet pins and two hierarchical labels. This is a separate trial script. It does not change `edit_native.py`.
Exit status: 0 done, 2 incorrect input.
"""

import re
import sys
import uuid
from pathlib import Path

NS = uuid.UUID("6f1c2a9e-0b7d-4c55-9a3e-2f7f6c1d9b11")
FONT = "\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n"


def block_end(text: str, start: int) -> int:
    depth, i = 0, start
    while True:
        depth += 1 if text[i] == "(" else -1 if text[i] == ")" else 0
        i += 1
        if depth == 0:
            return i


def cut(text: str, pattern: str) -> tuple[str, str]:
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"the pattern {pattern!r} is not in the schematic")
    end = block_end(text, m.start() + 2)
    return text[: m.start()] + text[end:], text[m.start() + 1 : end]


def u(name: str) -> str:
    return str(uuid.uuid5(NS, "sheet-move/" + name))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or not Path(args[0]).is_file():
        print("make_sheet_move: give the input schematic and the output directory")
        return 2
    text = Path(args[0]).read_text()
    root_uuid = re.search(r'\n\t\(uuid "([^"]+)"', text).group(1)
    sheet_uuid = u("sheet")
    text, symbol = cut(text, r'\n\t\(symbol\n\t\t\(lib_id "Device:R"\)\n\t\t\(at 101\.6 101\.6 0\)')
    text, _ = cut(text, r'\n\t\(label "VIN"\n\t\t\(at 101\.6 97\.79 0\)')
    text, _ = cut(text, r'\n\t\(label "N_RC"\n\t\t\(at 101\.6 105\.41 0\)')
    old = f'(path "/{root_uuid}"'
    assert old in symbol
    symbol = symbol.replace(old, f'(path "/{root_uuid}/{sheet_uuid}"')
    lib = re.search(r"\n\t\(lib_symbols.*?\n\t\)\n", text, re.S).group(0)
    labels = "".join(
        f'\t(hierarchical_label "{n}"\n\t\t(shape passive)\n\t\t(at 101.6 {y} 90)\n\t\t(effects\n{FONT}\t\t\t(justify left)\n\t\t)\n\t\t(uuid "{u("hl" + n)}")\n\t)\n'
        for n, y in (("VIN", 97.79), ("N_RC", 105.41)))
    sub = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "cad_skills_trial_native")\n\t(generator_version "1.0")\n\t(uuid "{sheet_uuid}")\n\t(paper "A4")'
           f'{lib}{chr(9)}{symbol}\n{labels}\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n')
    pins = "".join(f'\t\t(pin "{n}" passive\n\t\t\t(at 95 {y} 180)\n\t\t\t(uuid "{u("pin" + n)}")\n\t\t\t(effects\n{FONT}\t\t\t\t(justify left)\n\t\t\t)\n\t\t)\n'
                   for n, y in (("VIN", 100), ("N_RC", 110)))
    root_labels = "".join(f'\t(label "{n}"\n\t\t(at 95 {y} 180)\n\t\t(effects\n{FONT}\t\t\t(justify right bottom)\n\t\t)\n\t\t(uuid "{u("rl" + n)}")\n\t)\n'
                          for n, y in (("VIN", 100), ("N_RC", 110)))
    sheet = (f'\t(sheet\n\t\t(at 95 95)\n\t\t(size 20 20)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
             f'\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill\n\t\t\t(color 0 0 0 0)\n\t\t)\n\t\t(uuid "{sheet_uuid}")\n'
             f'\t\t(property "Sheetname" "sub"\n\t\t\t(at 95 94 0)\n\t\t\t(effects\n{FONT}\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n'
             f'\t\t(property "Sheetfile" "sub.kicad_sch"\n\t\t\t(at 95 115.5 0)\n\t\t\t(effects\n{FONT}\t\t\t\t(justify left top)\n\t\t\t)\n\t\t)\n{pins}'
             f'\t\t(instances\n\t\t\t(project "trial"\n\t\t\t\t(path "/{root_uuid}"\n\t\t\t\t\t(page "2")\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    marker = "\t(sheet_instances"
    text = text.replace(marker, root_labels + sheet + marker, 1)
    out = Path(args[1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "trial.kicad_sch").write_text(text)
    (out / "sub.kicad_sch").write_text(sub)
    return 0


if __name__ == "__main__":
    sys.exit(main())
