# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Negative and nominal tests for examples/pcb-trial/scripts/check_native.py.

  uv run tests/test_trial_checker.py

The host tests need no KiCad. They use the generated native fixture and a netlist XML that the test
builds from the expected map. Two tests use a fresh KiCad netlist export from the trial container.
They show `unavailable` (and do not count as passed) if podman or the image is absent.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / "examples/pcb-trial"
CHECKER = TRIAL / "scripts/check_native.py"
sys.path.insert(0, str(TRIAL / "scripts"))
import check_native as CN  # noqa: E402

IMAGE_TAG = "localhost/cad-skills-trial:b5"
UNAVAILABLE = []


def expected_map():
    return {k: v for k, v in json.loads((TRIAL / "expected/netlist.json").read_text()).items() if not k.startswith("_")}


def make_xml(path: Path, pins=None, prefix="/", extra=()):
    """A minimal KiCad-like netlist XML. `extra` adds (net, ref, pin) memberships."""
    pins = expected_map() if pins is None else pins
    nets = {}
    for pin, net in pins.items():
        nets.setdefault(net, []).append(pin)
    for net, ref, pin in extra:
        nets.setdefault(net, []).append(f"{ref}.{pin}")
    rows = "".join(
        f'<net code="{i}" name="{prefix}{net}">' + "".join(f'<node ref="{p.split(".")[0]}" pin="{p.split(".")[1]}"/>' for p in members) + "</net>"
        for i, (net, members) in enumerate(sorted(nets.items()), 1))
    path.write_text(f'<?xml version="1.0"?><export version="E"><nets>{rows}</nets></export>')
    return path


def native_copy(tmp: Path) -> Path:
    target = tmp / "native"
    shutil.copytree(TRIAL / "native", target)
    return target


def check(directory: Path, netlist: Path):
    return CN.run(directory, netlist, TRIAL / "expected")


def sch_text(directory: Path) -> str:
    return (directory / "trial.kicad_sch").read_text()


def write_sch(directory: Path, text: str):
    (directory / "trial.kicad_sch").write_text(text)


def instance_block(text: str, ref: str) -> tuple[int, int]:
    """Start and end of the instance block of `ref` (top-level symbol with a lib_id)."""
    marker = f'(property "Reference" "{ref}"'
    at = text.index(marker)
    start = text.rindex("\n\t(symbol\n", 0, at) + 1
    depth, i = 0, start
    while True:
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1


def has(result, text):
    return any(text in p for p in result["problems"])


def test_nominal(tmp: Path):
    directory = native_copy(tmp)
    result = check(directory, make_xml(tmp / "n.xml"))
    assert result == {"instances": 7, "pins_compared": 10, "nets_compared": 10, "problems": []}, result


def test_duplicate_reference_counts_raw_instances(tmp: Path):
    directory = native_copy(tmp)
    text = sch_text(directory)
    a, b = instance_block(text, "MH1")
    block = text[a:b]
    copy = re.sub(r'\(uuid "[0-9a-f-]+"\)', '(uuid "99999999-9999-5999-8999-999999999999")', block, count=1)
    write_sch(directory, text[:b] + "\n" + copy + text[b:])
    result = check(directory, make_xml(tmp / "n.xml"))
    assert result["instances"] == 8 and has(result, "8 raw symbol instances") and has(result, "MH1 occurs 2 times"), result


def test_missing_expected_reference_has_no_traceback(tmp: Path):
    directory = native_copy(tmp)
    text = sch_text(directory)
    a, b = instance_block(text, "R2")
    write_sch(directory, text[:a] + text[b:])
    result = check(directory, make_xml(tmp / "n.xml"))
    assert has(result, "the expected reference R2 is absent") and has(result, "6 raw symbol instances"), result
    r = subprocess.run(["uv", "run", "-q", str(CHECKER), "--dir", str(directory), "--netlist", str(tmp / "n.xml"), "--expected", str(TRIAL / "expected")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "Traceback" not in r.stderr, r.stderr


def test_missing_mandatory_instance_data(tmp: Path):
    directory = native_copy(tmp)
    text = sch_text(directory)
    a, b = instance_block(text, "R1")
    block = re.sub(r'\n\t\t\(property "Footprint".*?\n\t\t\)', "", text[a:b], count=1, flags=re.S)
    assert block != text[a:b]
    write_sch(directory, text[:a] + block + text[b:])
    result = check(directory, make_xml(tmp / "n.xml"))
    assert has(result, "misses mandatory data: Footprint") and has(result, "6 raw symbol instances"), result
    write_sch(directory, text.replace('(at 152.4 101.6 0)', ""))  # an instance with no position
    result = check(directory, make_xml(tmp / "n.xml"))
    assert has(result, "misses mandatory data: at"), result


def test_duplicate_pin_membership(tmp: Path):
    directory = native_copy(tmp)
    result = check(directory, make_xml(tmp / "a.xml", extra=[("GND", "R1", "1")]))
    assert has(result, "the pin R1.1 is in the netlist two times"), result
    result = check(directory, make_xml(tmp / "b.xml", extra=[("VIN", "R1", "1")]))
    assert has(result, "the pin R1.1 is in the netlist two times"), "the same net twice is also a duplicate"
    # The later membership must not hide the earlier one.
    assert not any(p.startswith("pin-to-net map differs") and "only exported" not in p for p in result["problems"])


def test_double_leading_slash_is_not_normalized(tmp: Path):
    directory = native_copy(tmp)
    result = check(directory, make_xml(tmp / "n.xml", prefix="//"))
    assert has(result, "pin-to-net map differs"), result
    assert check(directory, make_xml(tmp / "ok.xml", prefix="/"))["problems"] == []
    assert check(directory, make_xml(tmp / "ok2.xml", prefix=""))["problems"] == [], "a name with no slash is allowed"


def changed_definition(directory: Path):
    """Move pin 1 of the embedded Device:R definition by 2.54 mm and the matching labels of R1 and R2."""
    text = sch_text(directory)
    start = text.index('(symbol "Device:R"')
    end = text.index('(symbol "Device:LED"') if text.index('(symbol "Device:LED"') > start else len(text)
    block = text[start:end]
    assert "(at 0 3.81 270)" in block
    text = text[:start] + block.replace("(at 0 3.81 270)", "(at 0 6.35 270)", 1) + text[end:]
    text = text.replace('(at 101.6 46.99 0)', '(at 101.6 44.45 0)', 1).replace('(at 101.6 97.79 0)', '(at 101.6 95.25 0)', 1)
    write_sch(directory, text)


def test_changed_embedded_pin_definition(tmp: Path):
    directory = native_copy(tmp)
    changed_definition(directory)
    sidecar = (directory / "pin_points.json").read_text()  # the generated sidecar stays as it was
    result = check(directory, make_xml(tmp / "n.xml"))
    assert has(result, "the embedded pin points") and sidecar == (directory / "pin_points.json").read_text(), result
    (directory / "pin_points.json").write_text("{}")  # the sidecar proves nothing, with or without it
    assert has(check(directory, make_xml(tmp / "n.xml")), "the embedded pin points")


def test_changed_instance_orientation(tmp: Path):
    directory = native_copy(tmp)
    text = sch_text(directory)
    write_sch(directory, text.replace("(at 152.4 101.6 0)", "(at 152.4 101.6 90)", 1))
    result = check(directory, make_xml(tmp / "n.xml"))
    assert has(result, "C1: a rotation or a mirror is not supported"), result
    a, b = instance_block(text, "R1")
    block = text[a:b].replace("\n\t\t(unit 1)", "\n\t\t(mirror x)\n\t\t(unit 1)", 1)
    write_sch(directory, text[:a] + block + text[b:])
    assert has(check(directory, make_xml(tmp / "m.xml")), "R1: a rotation or a mirror is not supported")


def test_sidecar_does_not_decide(tmp: Path):
    directory = native_copy(tmp)
    (directory / "pin_points.json").write_text('{"R1.1": [0, 0]}')
    assert check(directory, make_xml(tmp / "n.xml"))["problems"] == [], "a wrong sidecar does not change the result of a good schematic"


def test_malformed_inputs_give_a_report(tmp: Path):
    directory = native_copy(tmp)
    good = make_xml(tmp / "n.xml")
    text = sch_text(directory)
    for label, broken in (("unterminated string", text + '\n(label "x'), ("extra parenthesis", text + "\n)"), ("empty", "")):
        write_sch(directory, broken)
        result = check(directory, good)
        assert result["problems"] and (label == "empty" or has(result, "cannot be read")), (label, result)
    write_sch(directory, text)
    (tmp / "bad.xml").write_text("<export><nets>")
    assert has(check(directory, tmp / "bad.xml"), "the netlist cannot be read")
    assert has(check(directory, tmp / "absent.xml"), "the netlist cannot be read")
    r = subprocess.run(["uv", "run", "-q", str(CHECKER), "--dir", str(directory), "--netlist", str(tmp / "bad.xml"), "--expected", str(TRIAL / "expected")],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "Traceback" not in r.stderr, r.stderr


def cli(directory: Path, netlist: Path):
    r = subprocess.run(["uv", "run", "-q", str(CHECKER), "--dir", str(directory), "--netlist", str(netlist), "--expected", str(TRIAL / "expected")],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def test_malformed_extra_symbol_with_seven_valid_instances(tmp: Path):
    directory = native_copy(tmp)
    good = make_xml(tmp / "n.xml")
    text = sch_text(directory)
    for label, extra in (("no lib_id", "(symbol (at 1 1 0))"), ("nested lib_id", "(symbol (lib_id (x)) (at 1 1 0))"), ("blank lib_id", '(symbol (lib_id " ") (at 1 1 0))')):
        write_sch(directory, text.replace("\n\t(sheet_instances", "\n\t" + extra + "\n\t(sheet_instances", 1))
        assert extra in sch_text(directory), label
        rc, out, err = cli(directory, good)
        report = json.loads(out)
        assert rc == 1 and "Traceback" not in err and report["instances"] == 7, (label, rc, out, err)
        assert any("misses mandatory data: lib_id" in p for p in report["problems"]), (label, report)


def test_nested_at_value_gives_a_report(tmp: Path):
    directory = native_copy(tmp)
    text = sch_text(directory)
    assert "(at 101.6 50.8 0)" in text
    write_sch(directory, text.replace("(at 101.6 50.8 0)", "(at (x) 50.8 0)", 1))
    rc, out, err = cli(directory, tmp / "missing.xml")
    assert rc == 1 and "Traceback" not in err and "Traceback" not in out, (rc, out, err)
    assert "is not a number" in out, out
    write_sch(directory, text.replace("(at 101.6 50.8 0)", "(at abc 50.8 0)", 1))
    rc, out, err = cli(directory, make_xml(tmp / "n.xml"))
    assert rc == 1 and "Traceback" not in err and "is not a number" in out, (rc, out, err)


def test_non_scalar_property_gives_a_report(tmp: Path):
    directory = native_copy(tmp)
    text = sch_text(directory)
    assert '(property "Value" "1k"' in text
    write_sch(directory, text.replace('(property "Value" "1k"', '(property (v) "1k"', 1))
    rc, out, err = cli(directory, make_xml(tmp / "n.xml"))
    assert rc == 1 and "Traceback" not in err and "not text" in out, (rc, out, err)
    write_sch(directory, text.replace('(property "Value" "1k"', '(property "Value" (v)', 1))
    rc, out, err = cli(directory, make_xml(tmp / "n.xml"))
    assert rc == 1 and "Traceback" not in err and "not text" in out, (rc, out, err)


def container_ready():
    r = subprocess.run(["podman", "image", "inspect", "--format", "{{.Id}}", IMAGE_TAG], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout.strip().removeprefix("sha256:")


def fresh_export(image: str, directory: Path) -> Path:
    out = directory / "out"
    out.mkdir(exist_ok=True)
    r = subprocess.run(["podman", "run", "--rm", "--pull=never", "--network", "none", "-v", f"{directory}:/work:Z", image,
                        "kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", "/work/out/trial.net.xml", "/work/trial.kicad_sch"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return out / "trial.net.xml"


def test_fresh_export_changed_definition(tmp: Path):
    image = container_ready()
    if image is None:
        UNAVAILABLE.append("test_fresh_export_changed_definition")
        print("  unavailable: podman or the trial image is absent")
        return
    directory = native_copy(tmp)
    assert check(directory, fresh_export(image, directory))["problems"] == [], "the nominal fixture passes with a fresh export"
    changed_definition(directory)
    result = check(directory, fresh_export(image, directory))
    assert has(result, "the embedded pin points") and not has(result, "pin-to-net map differs"), result  # the connectivity is unchanged


def test_fresh_export_renamed_label(tmp: Path):
    image = container_ready()
    if image is None:
        UNAVAILABLE.append("test_fresh_export_renamed_label")
        print("  unavailable: podman or the trial image is absent")
        return
    directory = native_copy(tmp)
    write_sch(directory, sch_text(directory).replace('(label "VIN"', '(label "/VIN"'))
    export = fresh_export(image, directory)
    assert "//VIN" in export.read_text(), "KiCad adds a slash to a label that already has one"
    assert has(check(directory, export), "pin-to-net map differs")


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
                print(f"{'unav' if name in UNAVAILABLE else 'ok  '} {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {type(e).__name__}: {e}")
    passed = len(tests) - failed - len(UNAVAILABLE)
    print(f"\n{passed}/{len(tests)} passed, {len(UNAVAILABLE)} unavailable")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
