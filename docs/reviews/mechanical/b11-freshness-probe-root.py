# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery", "jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Probe mechanical freshness on a temporary fixture. Preserve all product files."""
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "skills/pcb-design/scripts"))
import mechanical as M

spec = importlib.util.spec_from_file_location("fixture", ROOT / "skills/pcb-design/templates/mech-fit-a/make_fixture.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
result = {}
with tempfile.TemporaryDirectory(prefix="b11-root-freshness-") as folder:
    project = Path(folder)
    with contextlib.redirect_stdout(io.StringIO()):
        fixture.main(["--out", str(project)])
    board = project / "board.kicad_pcb"
    original_board = board.read_bytes()
    original_run = M._run_kicad
    def changed_source(stage, image_id, args):
        value = original_run(stage, image_id, args)
        if args[:3] == ["pcb", "export", "drill"]:
            board.write_bytes(original_board + b"\n")
        return value
    M._run_kicad = changed_source
    export = M.run_export(project, "localhost/cad-skills-pcb:b6")
    M._run_kicad = original_run
    result["export"] = {
        "returned": True,
        "record_exists": (project / M.EXPORT_DIR / "export.json").is_file(),
        "recorded_board_sha256": export["inputs"]["board.kicad_pcb"]["sha256"],
        "current_board_sha256": hashlib.sha256(board.read_bytes()).hexdigest(),
    }
    board.write_bytes(original_board)
    fit = M.run_fit(project)
    result["fit_status"] = fit["status"]
    original_capture = M.capture
    calls = 0
    def changed_outputs(path):
        global calls
        data = original_capture(path)
        calls += 1
        if calls == 2:
            for rel in (M.REPORT, M.FIT_ASSEMBLY):
                target = project / rel
                target.write_bytes(target.read_bytes() + b"\n")
        return data
    M.capture = changed_outputs
    release = M.run_release(project)
    M.capture = original_capture
    result["release"] = {
        "returned": True,
        "record_exists": (project / M.RELEASE).is_file(),
        "capture_calls": calls,
        "outputs": [
            {"path": item["path"], "recorded_sha256": item["sha256"],
             "current_sha256": hashlib.sha256((project / item["path"]).read_bytes()).hexdigest()}
            for item in release["outputs"] if item["role"] in ("report", "step_fit")
        ],
    }
print(json.dumps(result, indent=2, sort_keys=True))
