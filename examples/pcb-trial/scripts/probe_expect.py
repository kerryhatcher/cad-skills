# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Expected differences for the limit probes, from the baseline snapshot. Written BEFORE the run.

  uv run scripts/probe_expect.py BASELINE.snap.json OUTDIR

readd-d1: the board has no D1 and the update uses the original schematic. D1 must come back with its library ID, its value
and its pad nets (the data of the baseline D1). Nothing else may change. The new UUID and the position are not predicted.
remove-d1-delete-off: the symbol D1 is removed from the schematic and the option "delete footprints with no components in netlist" is OFF.
Hypothesis (written before the run): the footprint D1 stays on the board and nothing changes (empty list). The parity check then reports D1
as an extra footprint. The deletion-ON result is in the frozen evidence (`remove-d1.json`).
sheet-move: no expectation is stated. The probe measures what the update does when the path of a symbol changes.
"""

import json
import sys
from pathlib import Path

snap = json.loads(Path(sys.argv[1]).read_text())
d1 = next(f for f in snap["footprints"].values() if f["reference"] == "D1")
expected = [{"op": "added", "class": "footprint", "ident": "D1", "lib_id": d1["lib_id"], "value": d1["value"],
             "pad_nets": {n: p["net"] for n, p in d1["pads"].items()}}]
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
(out / "remove-d1-delete-off.json").write_text(json.dumps({"differences": []}, indent=2) + "\n")
(out / "readd-d1.json").write_text(json.dumps({"differences": expected}, indent=2) + "\n")
