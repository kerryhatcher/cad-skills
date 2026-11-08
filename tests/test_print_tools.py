# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Regression tests for the structural-analysis, print-prep and prusaslicer tools.

  uv run tests/test_print_tools.py            # all
  uv run tests/test_print_tools.py fea        # only tests whose name contains 'fea'

Each tool runs through `uv run` exactly as an agent would. The PrusaSlicer
profile tests use the installed bundle if found, else download
PrusaResearch.ini from GitHub. The real slice test is skipped when
PrusaSlicer is not installed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEA = ROOT / "skills/structural-analysis/scripts/fea.py"
PREP = ROOT / "skills/print-prep/scripts/printability.py"
SLICE = ROOT / "skills/prusaslicer/scripts/slice.py"
BUNDLE_URL = "https://raw.githubusercontent.com/prusa3d/PrusaSlicer/version_2.9.7/resources/profiles/PrusaResearch.ini"

BEAM = textwrap.dedent("""
    import cadquery as cq
    length = 100.0
    w = 10.0
    h = 10.0
    result = cq.Workplane("XY").box(length, w, h, centered=(False, True, False))
    show_object(result)
""")


def run(*args, ok=(0,)):
    r = subprocess.run(["uv", "run", "-q", *map(str, args)], capture_output=True, text=True)
    if r.returncode not in ok:
        raise AssertionError(f"{args} -> exit {r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r


def close(a, b, rel):
    assert abs(a - b) <= rel * abs(b), f"{a} not within {rel:.0%} of {b}"


def test_fea_cantilever(tmp: Path):
    """PLA cantilever 100x10x10, 10 N tip load: delta = 1.739 mm, root stress 6.0 MPa."""
    (tmp / "beam.py").write_text(BEAM)
    r = run(FEA, tmp / "beam.py", "--material", "prusament-pla", "--fix", "<X", "--force", ">X=0,0,-10",
            "--json", "--png", tmp / "beam.png", "--vtu", tmp / "beam.vtu")
    d = json.loads(r.stdout)
    close(d["max_displacement_mm"], 10 * 100**3 / (3 * 2300 * 10**4 / 12), 0.02)
    close(d["von_mises_max_MPa"], 6.0, 0.05)
    close(d["von_mises_design_MPa"], 5.85, 0.06)
    assert d["equilibrium_error"] < 1e-3
    assert d["safety_factor_inplane"] > 8 and d["passes"]
    assert (tmp / "beam.png").stat().st_size > 10_000 and (tmp / "beam.vtu").exists()


def test_fea_layer_check(tmp: Path):
    """Same beam printed standing up (layers across the bending stress) must be governed by layers."""
    (tmp / "beam.py").write_text(BEAM)
    r = run(FEA, tmp / "beam.py", "--material", "pla", "--fix", "<X", "--force", ">X=0,0,-10",
            "--build-dir", "x", "--sf-target", "5", "--json", ok=(3,))
    d = json.loads(r.stdout)
    assert d["safety_factor_interlayer"] < d["safety_factor_inplane"]
    close(d["layer_normal_tension_design_MPa"], 5.85, 0.08)
    assert not d["passes"]


def test_fea_list_faces_and_set(tmp: Path):
    (tmp / "beam.py").write_text(BEAM)
    r = run(FEA, tmp / "beam.py", "--list-faces", "--set", "length=50")
    assert "x[0.00,50.00]" in r.stdout and r.stdout.count("face:") == 6


def test_printability(tmp: Path):
    (tmp / "beam.py").write_text(BEAM)
    r = run(PREP, tmp / "beam.py", "--load-axis", "x", "--json", "-o", tmp / "beam.3mf", "--png", tmp / "o.png")
    d = json.loads(r.stdout)
    assert d["health"]["watertight"] and d["health"]["bodies"] == 1
    assert d["best"]["fits_bed"] and d["best"]["load_across_layers"] == 0
    assert d["best"]["height"] == 10.0  # lying flat beats standing up
    assert (tmp / "beam.3mf").exists() and (tmp / "o.png").exists()
    big = tmp / "big.py"
    big.write_text(BEAM.replace("length = 100.0", "length = 400.0"))
    r = run(PREP, big, "--json", ok=(3,))
    assert any("does not fit" in p for p in json.loads(r.stdout)["problems"])


def bundle_args(tmp: Path) -> list[str]:
    r = subprocess.run(["uv", "run", "-q", str(SLICE), "find", "--json"], capture_output=True, text=True)
    try:
        if json.loads(r.stdout).get("bundle"):
            return []
    except json.JSONDecodeError:
        pass
    dest = tmp / "PrusaResearch.ini"
    if not dest.exists():
        urllib.request.urlretrieve(BUNDLE_URL, dest)
    return ["--bundle", str(dest)]


def test_slice_profiles(tmp: Path):
    b = bundle_args(tmp)
    d = json.loads(run(SLICE, *b, "profiles", "--printer", "MK4", "--print", "0.20mm STRUCTURAL", "--json").stdout)
    assert d["printer"] == "Original Prusa MK4 Input Shaper 0.4 nozzle" and d["printer_model"] == "MK4IS"
    assert "0.20mm STRUCTURAL @MK4IS 0.4" in d["prints"]
    for f in ("Prusament PLA @PGIS", "Prusament PETG @PGIS", "Jessie PLA @PG", "Jessie PETG @PG"):
        assert f in d["filaments"], f
    assert not any("MK4S" in f or "@MINI" in f for f in d["filaments"])
    d = json.loads(run(SLICE, *b, "profiles", "--printer", "MK4S", "--json").stdout)
    assert d["printer"] == "Original Prusa MK4S HF0.4 nozzle" and d["printer_model"] == "MK4S"
    assert "Jessie PETG @MK4S HF0.4" in d["filaments"]
    ini = tmp / "c.ini"
    run(SLICE, *b, "config", "--printer", "MK4", "--filament", "Jessie PETG", "--perimeters", "5", "-o", ini)
    cfg = dict(l.split(" = ", 1) for l in ini.read_text().splitlines() if " = " in l)
    assert cfg["printer_model"] == "MK4IS" and cfg["perimeters"] == "5"
    assert cfg["filament_type"] == "PETG" and cfg["temperature"] == "245"
    assert cfg["bed_shape"] == "0x0,250x0,250x210,0x210" and cfg["gcode_flavor"] == "marlin2"


def test_slice_real(tmp: Path):
    r = subprocess.run(["uv", "run", "-q", str(SLICE), "find", "--json"], capture_output=True, text=True)
    if r.returncode != 0:
        print("  (skipped: PrusaSlicer not installed)")
        return
    (tmp / "beam.py").write_text(BEAM)
    run(PREP, tmp / "beam.py", "-o", tmp / "beam.stl", ok=(0, 3))
    d = json.loads(run(SLICE, "slice", tmp / "beam.stl", "--printer", "MK4", "--filament", "Prusament PETG",
                       "--perimeters", "4", "--json", "-o", tmp / "beam.bgcode").stdout)
    s = d["summary"]
    assert not d["verification_problems"]
    assert s["printer_model"] == "MK4IS" and s["perimeters"] == "4" and s["temperature"] == "250"
    assert float(s["filament_used_g"]) > 5
    info = json.loads(run(SLICE, "info", tmp / "beam.bgcode", "--json").stdout)
    assert info["printer_model"] == "MK4IS"


def main(argv):
    key = argv[0] if argv else ""
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and key in n]
    failed = 0
    with tempfile.TemporaryDirectory() as td:
        for name, fn in tests:
            tmp = Path(td) / name
            tmp.mkdir()
            try:
                fn(tmp)
                print(f"ok   {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
