"""The trial circuit in SKiDL for the U3 netlist-import edit tests. It writes a netlist only.

  KICAD10_SYMBOL_DIR=/usr/share/kicad/symbols KICAD10_FOOTPRINT_DIR=/usr/share/kicad/footprints \
      uv run --no-project --no-config --offline --python /opt/trial-venv/bin/python python skidl/circuit_u3.py OP OUTDIR

OP: none | reorder | value-r2 | add-c2 | remove-d1 | footprint-r1 | rename-c1 | line-shift

The circuit has the 7 parts of the native fixture (with the two mounting holes). Each part has a tag.
SKiDL makes the tstamp of a part from its hierarchy and its tag, not from its reference.
Each OP is the SKiDL form of the native edit with the same name in `scripts/edit_native.py`:

  none          no change
  reorder       the parts are made in the reverse order
  value-r2      the value of R2 changes from 10k to 22k
  add-c2        a new part C2 (100n, tag C2) between N_RC and GND
  remove-d1     the part D1 is not made. N_LED then has only R1 pin 2.
  footprint-r1  the footprint of R1 changes from 0603 to 0805
  rename-c1     the reference of C1 changes to C9. The tag stays C1.
  line-shift    no circuit change. The parts are made on a different source line. SKiDL writes the source
                line of each part into the netlist field "SKiDL Line". This edit measures the effect of that field.

The script does not call generate_schematic(). The schematic route (U2) is not part of this test.
"""

import os
import sys

from skidl import KICAD10, Net, Part, generate_netlist, set_default_tool

OPS = ("none", "reorder", "value-r2", "add-c2", "remove-d1", "footprint-r1", "rename-c1", "line-shift")
op, out = sys.argv[1], sys.argv[2]
if op not in OPS:
    sys.exit(f"circuit_u3: unknown OP {op!r}. Use one of: {', '.join(OPS)}.")
os.makedirs(out, exist_ok=True)
set_default_tool(KICAD10)

R0603, R0805 = "Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_0805_2012Metric"
# (tag, library, symbol, reference, value, footprint). The tag is the identity. It never changes.
PARTS = [
    ("J1", "Connector_Generic", "Conn_01x02", "J1", "Power", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"),
    ("R1", "Device", "R", "R1", "1k", R0805 if op == "footprint-r1" else R0603),
    ("D1", "Device", "LED", "D1", "Green", "LED_SMD:LED_0603_1608Metric"),
    ("R2", "Device", "R", "R2", "22k" if op == "value-r2" else "10k", R0603),
    ("C1", "Device", "C", "C9" if op == "rename-c1" else "C1", "100n", "Capacitor_SMD:C_0603_1608Metric"),
    ("MH1", "Mechanical", "MountingHole", "MH1", "M3", "MountingHole:MountingHole_3.2mm_M3"),
    ("MH2", "Mechanical", "MountingHole", "MH2", "M3", "MountingHole:MountingHole_3.2mm_M3"),
]
if op == "add-c2":
    PARTS.append(("C2", "Device", "C", "C2", "100n", "Capacitor_SMD:C_0603_1608Metric"))
if op == "remove-d1":
    PARTS = [p for p in PARTS if p[0] != "D1"]
if op == "reorder":
    PARTS.reverse()

if op != "line-shift":
    parts = {tag: Part(lib, sym, ref=ref, value=value, tag=tag, footprint=fp) for tag, lib, sym, ref, value, fp in PARTS}
else:
    # The same parts, made on a different source line.
    parts = {tag: Part(lib, sym, ref=ref, value=value, tag=tag, footprint=fp) for tag, lib, sym, ref, value, fp in PARTS}
vin, gnd, n_led, n_rc = Net("VIN"), Net("GND"), Net("N_LED"), Net("N_RC")
vin += parts["J1"][1], parts["R1"][1], parts["R2"][1]
gnd += parts["J1"][2], parts["C1"][2]
n_rc += parts["R2"][2], parts["C1"][1]
n_led += parts["R1"][2]
if "D1" in parts:
    gnd += parts["D1"][1]
    n_led += parts["D1"][2]
if "C2" in parts:
    n_rc += parts["C2"][1]
    gnd += parts["C2"][2]
generate_netlist(file_=os.path.join(out, "trial.net"))
