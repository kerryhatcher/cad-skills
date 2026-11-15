"""T6: exit code of a SKiDL `ERC()` run for a good and a defective trial circuit.

  KICAD10_SYMBOL_DIR=/usr/share/kicad/symbols uv run --no-project --no-config --offline \
      --python /opt/trial-venv/bin/python python skidl/erc_probe.py OUTDIR good|bad

Mode `good` wires all pins as in `circuit.py`. Mode `bad` leaves R1 pin 2 and D1 pin 2 unconnected and ties
the pin 1 of D1 to a net with only one pin. The script calls `ERC()`. SKiDL logs the number of errors and warnings
It does not change the exit code. The test measures the exit code of the process. (Runs `T6_good_175` and `T6_bad_176` are invalid: the first version of the script read a count attribute that does not exist.)
"""

import os
import sys

from skidl import ERC, KICAD10, Net, Part, set_default_tool

out, mode = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
os.chdir(out)
set_default_tool(KICAD10)
vin, gnd, n_led, n_rc = Net("VIN"), Net("GND"), Net("N_LED"), Net("N_RC")
j1 = Part("Connector_Generic", "Conn_01x02", ref="J1", value="Power", tag="J1", footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
r1 = Part("Device", "R", ref="R1", value="1k", tag="R1", footprint="Resistor_SMD:R_0603_1608Metric")
d1 = Part("Device", "LED", ref="D1", value="Green", tag="D1", footprint="LED_SMD:LED_0603_1608Metric")
r2 = Part("Device", "R", ref="R2", value="10k", tag="R2", footprint="Resistor_SMD:R_0603_1608Metric")
c1 = Part("Device", "C", ref="C1", value="100n", tag="C1", footprint="Capacitor_SMD:C_0603_1608Metric")
vin += j1[1], r1[1], r2[1]
gnd += j1[2], d1[1], c1[2]
n_rc += r2[2], c1[1]
if mode == "good":
    n_led += r1[2], d1[2]
ERC()
