# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure owned corner fixtures and compare them with the derived tool radii."""
import copy
import json
import tempfile
from decimal import Decimal
from pathlib import Path
import test_pcb_fab_workflow as base


M_PASS = {"corners": [{"location": "outline", "radius_nm": 863600}, {"location": "cutout", "radius_nm": 508000}]}
M_FAIL = {"corners": [{"location": "outline", "radius_nm": 863599}, {"location": "cutout", "radius_nm": 507999}]}


def unit_checks():
    """The cutter facts accept mm, mil and in with the same exact radius. A bad fact gives exit 2."""
    w = base.workflow
    profile = base.fab.check_profile(base.PROFILE)

    def with_facts(outline_value, cutout_value, unit):
        changed = copy.deepcopy(profile)
        for key, value in (("process.outline_cutter_diameter", outline_value),
                           ("process.cutout_cutter_diameter", cutout_value)):
            changed["extensions"][key]["value"] = value
            changed["extensions"][key]["unit"] = unit
        return changed

    def rows(profile, measured):
        try:
            return w.corner_conditions(profile, measured)
        except w.Stop as err:
            return err.code

    rows_in = {name: rows(with_facts("0.068", "0.040", "in"), measured)
               for name, measured in (("pass", M_PASS), ("fail", M_FAIL))}
    for name, expected in (("pass", "pass"), ("fail", "fail")):
        base.check(f"The cutter facts in in give {expected} for each corner with the exact radius.",
                   all(row["status"] == expected for row in rows_in[name])
                   and [row["tool_radius_nm"] for row in rows_in[name]] == [863600, 508000], rows_in[name])
    def strip(result):
        return [{key: value for key, value in row.items() if key != "process_fact"} for row in result]

    stripped = {name: strip(result) for name, result in rows_in.items()}
    for value in (("1.7272", "1.016", "mm"), ("68", "40", "mil")):
        for name, measured in (("pass", M_PASS), ("fail", M_FAIL)):
            got = rows(with_facts(*value), measured)
            ok = strip(got) == stripped[name]
            base.check(f"The cutter facts in {value[2]} give the same rows as the facts in in ({name}).", ok, got)
    for label, changed in (("the unit cm", with_facts("0.068", "0.040", "cm")),
                           ("a radius below one nanometer", with_facts("0.0000001", "1.016", "mm"))):
        code = rows(changed, M_PASS)
        base.check(f"{label} refuses with exit 2.", code == 2, code)
    missing = copy.deepcopy(profile)
    del missing["extensions"]["process.outline_cutter_diameter"]
    code = rows(missing, M_PASS)
    base.check("A profile without the outline cutter fact refuses with exit 2.", code == 2, code)
    listed = with_facts("0.068", "0.040", ["in"])
    code = rows(listed, M_PASS)
    base.check("A cutter unit that is a list refuses with exit 2, not TypeError.", code == 2, code)


def main():
    unit_checks()
    w = base.workflow
    fixtures = base.ROOT / "tests/fixtures/pcb-fab-package/corners"
    with tempfile.TemporaryDirectory(prefix="fab-corners-") as directory:
        project = base.fresh_project(Path(directory), "project")
        consumed = w.captured(project, {"profile": base.PROFILE})
        runtime = w.runtime_identity(consumed["toolchain.lock.json"])
        profile = base.fab.check_profile(base.PROFILE)
        for location, values, count in [("outline", ["0.033", "0.034", "0.035"], 1),
                                        ("cutout", ["0.019", "0.020", "0.021"], 4)]:
            for value, expected in zip(values, ["fail", "pass", "pass"]):
                name = f"{location}-{value}in"
                consumed["kicad/board.kicad_pcb"] = (fixtures / f"{name}.kicad_pcb").read_bytes()
                out = project / "out/fab" / name
                out.mkdir(parents=True)
                rows = w.measure_corners(consumed, out, w.Outputs(project, out), runtime, profile)
                row = next(row for row in rows if row["condition"] == f"process.{location}_tool_compatibility")
                expected_nm = int(Decimal(value) * 25400000)
                radii = [item["radius_nm"] for item in row["measured_corners"]]
                base.check(f"The {location} fixture at {value} in gives {expected} with the independent radius.",
                           row["status"] == expected and radii == [expected_nm] * count, row)
                report = json.loads((out / "corner-report.json").read_text())
                base.check(f"The {name} report binds the captured board bytes.",
                           report["measurement"]["board_sha256"] == base.sha(consumed["kicad/board.kicad_pcb"]))
                print(json.dumps({"fixture": name, "radii_nm": radii, "status": row["status"],
                                  "board_sha256": report["measurement"]["board_sha256"], "runtime": runtime}, sort_keys=True))
        for name in ("convex-square", "open-outline", "unsupported-polygon"):
            consumed["kicad/board.kicad_pcb"] = (fixtures / f"{name}.kicad_pcb").read_bytes()
            out = project / "out/fab" / name
            out.mkdir(parents=True)
            try:
                rows = w.measure_corners(consumed, out, w.Outputs(project, out), runtime, profile)
                code = 0
            except w.Stop as err:
                code = err.code
                print(str(err))
            if name == "convex-square":
                base.check("The square outer contour has no concave corner condition.",
                           code == 0 and all(row["status"] == "pass" and not row["measured_corners"] for row in rows))
            else:
                base.check(f"The {name} fixture refuses with exit 2.", code == 2)
        changed = copy.deepcopy(profile)
        changed["extensions"]["process.outline_cutter_diameter"]["source_sha256"] = "0" * 64
        try:
            w.corner_conditions(changed, {"corners": []})
            refused = False
        except w.Stop as err:
            refused = err.code == 2
        base.check("A cutter fact with an incorrect source hash refuses.", refused)
    passed = sum(ok for _, ok in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
