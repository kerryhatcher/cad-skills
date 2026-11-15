# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Compare the KiBot output with the kicad-cli exports of the final board (T11). Host script.

  uv run scripts/compare_kibot.py EXPORT_DIR KIBOT_DIR

It lists each difference. It compares the layer set, the drill split (hole diameters and positions), the placement
header and rows, and the Gerber bytes without the lines that hold a date or the generator version.
Agreement with KiBot is not proof of a correct export. T10 compares with the expected values.
Exit status: 0 no difference, 1 differences, 2 incorrect input.
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_exports as CE  # noqa: E402

VOLATILE = re.compile(r"CreationDate|GenerationSoftware|Created by|DRILL file|date|ProjectId|SameCoordinates")


def stable(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines() if not VOLATILE.search(line)]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or not all(Path(a).is_dir() for a in args):
        print("compare_kibot: give the kicad-cli export directory and the KiBot output directory")
        return 2
    exp, kib = Path(args[0]), Path(args[1])
    diffs = []
    cli_layers = sorted(p.name for p in exp.glob("*.gbr"))
    kibot_layers = sorted(p.name for p in (kib / "gerbers").glob("*.gbr"))
    if cli_layers != kibot_layers:
        diffs.append({"item": "gerber layer set", "kicad_cli": cli_layers, "kibot": kibot_layers})
    for name in cli_layers:
        if (kib / "gerbers" / name).is_file() and stable(exp / name) != stable(kib / "gerbers" / name):
            a_lines, b_lines = stable(exp / name), stable(kib / "gerbers" / name)
            diffs.append({"item": f"gerber content {name}", "lines_only_in_kicad_cli": len([x for x in a_lines if x not in b_lines]),
                          "lines_only_in_kibot": len([x for x in b_lines if x not in a_lines])})
    for kind, kname in (("PTH", "trial-PTH_drill.drl"), ("NPTH", "trial-NPTH_drill.drl")):
        a, b = CE.parse_drill((exp / f"trial-{kind}.drl").read_text()), CE.parse_drill((kib / "drill" / kname).read_text())
        if a != b:
            diffs.append({"item": f"drill {kind}", "kicad_cli": a, "kibot": b})
        elif stable(exp / f"trial-{kind}.drl") != stable(kib / "drill" / kname):
            diffs.append({"item": f"drill {kind} text (same holes)", "note": "header or tool text differs"})
    a = list(csv.reader((exp / "trial-pos.csv").open()))
    b = list(csv.reader((kib / "pos/trial-both_pos.csv").open()))
    if a[0] != b[0]:
        diffs.append({"item": "placement header", "kicad_cli": a[0], "kibot": b[0]})
    key = lambda rows, col: {r[0]: r for r in rows[1:]}  # noqa: E731
    ra, rb = key(a, 0), key(b, 0)
    if set(ra) != set(rb):
        diffs.append({"item": "placement references", "kicad_cli": sorted(ra), "kibot": sorted(rb)})
    def number(row):  # the two tools write 6 and 4 decimals. Compare the values as numbers.
        return [float(c) if re.fullmatch(r"-?[\d.]+", c) else c for c in row]

    for ref in sorted(set(ra) & set(rb)):
        if number(ra[ref]) != number(rb[ref]):
            diffs.append({"item": f"placement row {ref}", "kicad_cli": ra[ref], "kibot": rb[ref]})
    print(json.dumps(diffs, indent=2))
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
