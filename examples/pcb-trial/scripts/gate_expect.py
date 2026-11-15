# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Write the expected-difference files for the gate edits and limit probes, from the baseline snapshot.

  uv run scripts/gate_expect.py out/g/baseline.snap.json out/g/expected

The expectations are stated BEFORE the experiment runs. They are hypotheses that the run tests.
The script reads the baseline snapshot and the edit definitions only. It never reads an after-board.
A file name holds the edit and, when the option state changes the result, the option state:
`footprint-r1.json` (replace footprints on) and `footprint-r1-replace-off.json` (replace footprints off).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    snap = json.loads(Path(argv[0]).read_text())
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    fp = {f["reference"]: f for f in snap["footprints"].values()}
    exp = {
        "none": [],
        "reorder": [],
        "value-r2": [{"op": "changed", "class": "footprint", "ident": "R2", "field": "value", "before": "10k", "after": "22k"}],
        # The edit copies C1 as C2. The expected value of C2 is the baseline value of C1.
        "add-c2": [{"op": "added", "class": "footprint", "ident": "C2", "lib_id": "Capacitor_SMD:C_0603_1608Metric", "value": fp["C1"]["value"], "pad_nets": {"1": "/N_RC", "2": "/GND"}}],
        "remove-d1": [{"op": "removed", "class": "footprint", "ident": "D1", "uuid": next(u for u, f in snap["footprints"].items() if f["reference"] == "D1")}],
        "footprint-r1": [{"op": "changed", "class": "footprint", "ident": "R1", "field": "lib_id", "before": "Resistor_SMD:R_0603_1608Metric", "after": "Resistor_SMD:R_0805_2012Metric"}] + [
            {"op": "changed", "class": "pad", "ident": f"R1.{n}", "field": "at", "before": fp["R1"]["pads"][n]["at"], "after": [x, 0, 0]}
            for n, x in (("1", -0.9125), ("2", 0.9125))],
        # Replace footprints off: the update must not change the library ID. The edit changes no other board object.
        "footprint-r1-replace-off": [],
        "rename-c1": [{"op": "changed", "class": "footprint", "ident": "C1", "field": "reference", "before": "C1", "after": "C9"}],
    }
    for name, diffs in exp.items():
        (out / f"{name}.json").write_text(json.dumps({"differences": diffs}, indent=2) + "\n")
    print(sorted(exp))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
