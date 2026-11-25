# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "openpyxl==3.1.5", "pyyaml==6.0.3", "xlrd==2.0.1"]
# ///
"""Measure a staged output change after package validation in a temporary project."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("pcba_tests", ROOT / "tests/test_pcba_design.py")
test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test)
tmp = Path(tempfile.mkdtemp(prefix="b10-after-validation-root-"))
project = test.package_project(tmp)
changed = {}

def alter():
    staging = project / "out/pcba/.package-staging"
    manifest = json.loads((staging / "manifest.json").read_text())
    entry = next(row for row in manifest["outputs"] if row["role"] == "copper")
    path = staging / entry["path"]
    changed.update(path=entry["path"], bound_sha256=entry["sha256"])
    path.write_bytes(b"ROOT AFTER-VALIDATION PROBE\n")

result = {"project": str(project)}
try:
    test.in_process_package(project, {"after_validate": alter})
    result["returned"] = "success"
except Exception as error:
    result.update(returned="exception", error_type=type(error).__name__, message=str(error))
dest = project / "out/pcba/packages/pkg-hook"
result.update(changed)
result["published"] = dest.is_dir()
if changed and (dest / changed["path"]).is_file():
    result["published_sha256"] = hashlib.sha256((dest / changed["path"]).read_bytes()).hexdigest()
print(json.dumps(result, indent=2))
