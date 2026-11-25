# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure a staged package change after validation."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "tests"))
import test_pcb_fab_workflow as fixture

temporary = Path(tempfile.mkdtemp(prefix="b7-c5-codex-"))
project, review_path, review_hash = fixture.prepared(temporary, "project")
destination = project / "out/fab/packages/codex-c5"
original_build_report = fixture.VAL.build_report
call_count = {"value": 0}
injected = b"changed staged bytes after final validation\n"


def build_then_change(*args, **kwargs):
    result = original_build_report(*args, **kwargs)
    call_count["value"] += 1
    if call_count["value"] == 2:
        manifest_path = Path(args[0][0])
        target = manifest_path.parent / "gerber/board-F_Cu.gbr"
        target.write_bytes(injected)
    return result


fixture.VAL.build_report = build_then_change
try:
    code, manifest = fixture.package_in_process(project, review_path, review_hash, destination)
finally:
    fixture.VAL.build_report = original_build_report

published = destination / "gerber/board-F_Cu.gbr"
expected = next(row["sha256"] for row in manifest["outputs"]
                if row["path"] == "gerber/board-F_Cu.gbr")
actual = hashlib.sha256(published.read_bytes()).hexdigest()
print(json.dumps({
    "temporary_directory": str(temporary),
    "exit": code,
    "status": manifest["status"],
    "validator_calls": call_count["value"],
    "manifest_sha256": expected,
    "published_sha256": actual,
    "published_injected_bytes": published.read_bytes() == injected,
    "reason_codes": [row["code"] for row in manifest["reasons"]],
}, sort_keys=True))
