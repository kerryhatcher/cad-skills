# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Exercise bound manual silk evidence with three measured board fixtures."""
import json
import tempfile
from pathlib import Path
import test_pcb_fab_workflow as base


def main():
    fixtures = base.ROOT / "tests/fixtures/pcb-fab-package/silk"
    with tempfile.TemporaryDirectory(prefix="fab-silk-") as directory:
        for value, width, expected in [("2.9", 73660, "fail"), ("3.0", 76200, "pass"), ("3.1", 78740, "pass")]:
            project = base.fresh_project(Path(directory), value)
            board = project / "kicad/board.kicad_pcb"
            board.write_bytes((fixtures / f"silk-{value}mil.kicad_pcb").read_bytes())
            runtime = base.workflow.runtime_identity((project / "toolchain.lock.json").read_bytes())
            code, stdout, stderr = base.workflow.podman(project, ["python3", "/worker/measure.py", "/work/kicad/board.kicad_pcb"], worker=fixtures)
            measured = json.loads(stdout)
            base.check(f"The {value} mil fixture has the independent stroke dimension.",
                       code == 0 and len(measured["labels"]) == 1 and measured["labels"][0]["stroke_nm"] == width
                       and measured["labels"][0]["layer"] == "F.Silkscreen", measured)
            design = project / "out/fab/design"
            base.workflow.design(project, base.PROFILE, design)
            artifact = project / "out/fab/manual/silk-measurement.json"
            artifact.parent.mkdir(parents=True)
            evidence = {"measurement": measured, "runtime": runtime, "expected_stroke_nm": width,
                        "manual_fixture_result": expected,
                        "scope": "Owned short-text fixture. No automatic product silk inspection or physical manufacturing claim."}
            artifact.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
            record = {"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1,
                      "condition": "silk_line_min_short_text", "result": expected,
                      "procedure": "Compare the measured B7 label thickness with the independently specified 3 mil threshold.",
                      "artifact_path": "out/fab/manual/silk-measurement.json", "artifact_sha256": base.sha(artifact.read_bytes()),
                      "inputs": {"board_sha256": base.sha(board.read_bytes()),
                                 "silk_gerber_sha256": base.sha((design / "export/board-F_Silkscreen.gbr").read_bytes())},
                      "reviewer": "Owned fixture expectation", "statement": "The fixture measurement establishes the expected manual result only."}
            manual = project / "out/fab/manual-record.json"
            manual.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
            code, result = base.workflow.supplier(project, base.PROFILE, project / "out/fab/supplier", design, manual)
            row = next(row for row in result["rows"] if row["condition"] == "silk_line_min_short_text")
            base.check(f"The bound manual result for {value} mil reaches the supplier row.",
                       row["status"] == expected and code == (1 if expected == "fail" else 0), result)
            retained = project / "out/fab/supplier/manual-artifact.txt"
            base.check(f"The supplier retains the measured artifact for {value} mil.", retained.read_bytes() == artifact.read_bytes())
            print(json.dumps({"fixture": value, "measurement": measured, "result": row,
                              "artifact_sha256": record["artifact_sha256"], "inputs": record["inputs"]}, sort_keys=True))
    passed = sum(ok for _, ok in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
