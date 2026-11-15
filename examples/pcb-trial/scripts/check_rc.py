# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fixed RC assertion for the trial circuit (T12). Host script. ngspice runs in the trial container.

  uv run scripts/check_rc.py make POS.csv OUT.cir      write the circuit from the values of R2 and C1 in the placement file
  uv run scripts/check_rc.py assert RC.log             compare the measured voltage with the fixed expected value

The expected value is fixed in this file: the time constant is 1.000 ms (10 kohm and 100 nF), and the voltage at one
time constant for a 3.3 V step is 3.3 * (1 - exp(-1)) = 2.086 V. The tolerance is 1 percent.
The expected value does not come from the circuit values. A wrong capacitor value in the design therefore fails.

Exit status: 0 the value is inside the tolerance, 1 it is outside, 2 incorrect input.
"""

from __future__ import annotations

import csv
import math
import re
import sys
from pathlib import Path

EXPECTED_VOLT = 2.086
TOLERANCE = 0.01
STEP_VOLT = 3.3
TAU_SECOND = 1.0e-3
assert abs(STEP_VOLT * (1 - math.exp(-1)) - EXPECTED_VOLT) < 5e-4
SCALE = {"": 1.0, "k": 1e3, "meg": 1e6, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12}


def value_of(text: str) -> float:
    m = re.fullmatch(r"([\d.]+)\s*([a-zA-Z]*)", text.strip())
    if not m or m.group(2).lower() not in SCALE:
        raise ValueError(f"the value {text!r} is not a number with a unit prefix")
    return float(m.group(1)) * SCALE[m.group(2).lower()]


def circuit(resistance: float, capacitance: float) -> str:
    return (f"RC step response of the trial circuit\nV1 in 0 PULSE(0 {STEP_VOLT} 0 1n 1n 1 2)\nR2 in out {resistance:g}\nC1 out 0 {capacitance:g}\n"
            f".tran 1u 5m\n.control\nrun\nmeas tran vtau FIND v(out) AT={TAU_SECOND:g}\nprint vtau\n.endc\n.end\n")


def make(pos: Path, out: Path) -> None:
    rows = {r["Ref"]: r["Val"] for r in csv.DictReader(pos.open())}
    out.write_text(circuit(value_of(rows["R2"]), value_of(rows["C1"])))


def measured(log: str) -> float:
    m = re.search(r"vtau\s*=\s*([-+\d.eE]+)", log)
    if not m:
        raise ValueError("the log has no value vtau")
    return float(m.group(1))


def judge(volt: float) -> tuple[bool, str]:
    error = abs(volt - EXPECTED_VOLT) / EXPECTED_VOLT
    return error <= TOLERANCE, f"measured {volt:.4f} V, expected {EXPECTED_VOLT} V, error {error * 100:.3f} percent, tolerance {TOLERANCE * 100:.0f} percent"


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if len(args) == 3 and args[0] == "make":
            make(Path(args[1]), Path(args[2]))
            return 0
        if len(args) == 2 and args[0] == "assert":
            ok, text = judge(measured(Path(args[1]).read_text()))
            print(("pass " if ok else "fail ") + text)
            return 0 if ok else 1
    except (OSError, ValueError, KeyError) as err:
        print(f"check_rc: {err}")
        return 2
    print("check_rc: use 'make POS.csv OUT.cir' or 'assert RC.log'")
    return 2


if __name__ == "__main__":
    sys.exit(main())
