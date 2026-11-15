"""The trial circuit in SKiDL (same references, values and footprints as the native fixture).

  KICAD10_SYMBOL_DIR=/usr/share/kicad/symbols uv run --no-project --no-config --offline \
      --python /opt/trial-venv/bin/python python skidl/circuit.py OUTDIR

Each part has a tag. It writes OUTDIR/trial.net (netlist) and OUTDIR/trial.kicad_sch (schematic).
"""

import os
import sys

from skidl import KICAD10, Net, Part, generate_netlist, generate_schematic, set_default_tool

out = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else "noholes"  # "full": all 7 parts, netlist only. "noholes": no mounting holes, netlist and schematic.
os.makedirs(out, exist_ok=True)
set_default_tool(KICAD10)
vin, gnd, n_led, n_rc = Net("VIN"), Net("GND"), Net("N_LED"), Net("N_RC")
j1 = Part("Connector_Generic", "Conn_01x02", ref="J1", value="Power", tag="J1",
          footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
r1 = Part("Device", "R", ref="R1", value="1k", tag="R1", footprint="Resistor_SMD:R_0603_1608Metric")
d1 = Part("Device", "LED", ref="D1", value="Green", tag="D1", footprint="LED_SMD:LED_0603_1608Metric")
r2 = Part("Device", "R", ref="R2", value="10k", tag="R2", footprint="Resistor_SMD:R_0603_1608Metric")
c1 = Part("Device", "C", ref="C1", value="100n", tag="C1", footprint="Capacitor_SMD:C_0603_1608Metric")
for ref in ("MH1", "MH2") if mode == "full" else ():
    Part("Mechanical", "MountingHole", ref=ref, value="M3", tag=ref, footprint="MountingHole:MountingHole_3.2mm_M3")
vin += j1[1], r1[1], r2[1]
gnd += j1[2], d1[1], c1[2]
n_led += r1[2], d1[2]
n_rc += r2[2], c1[1]
generate_netlist(file_=os.path.join(out, "trial.net"))
if mode != "full":  # The first schematic run (step T4_skidl_125) failed in the SKiDL placer.
    generate_schematic(filepath=out, top_name="trial")
