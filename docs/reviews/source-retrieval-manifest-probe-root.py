# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure whether a source entry can replace its own manifest."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "retrieval_probe", root / "skills/pcb-fab-package/scripts/fetch_sources.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix="retrieval-manifest-probe-") as folder:
    manifest = Path(folder) / "sources.yaml"
    response = b"replacement bytes\n"
    record = {
        "schema": "cad-skills/sources", "schema_version": 1,
        "sources": [{
            "id": "source", "path": "sources.yaml",
            "url": "https://example.test/source", "retrieved": "2026-11-15",
            "sha256": hashlib.sha256(response).hexdigest(),
            "content_type": "text/plain", "magic": None,
            "license_state": "The fixture makes no permission claim.",
            "distribution_decision": "exclude-full-copy", "profile_binding": None,
        }],
    }
    manifest.write_text(json.dumps(record))
    before = manifest.read_bytes()
    code, report = module.main(["--manifest", str(manifest)], fetch=lambda url: response)
    print(json.dumps({
        "exit": code, "manifest_changed": manifest.read_bytes() != before,
        "response_replaced_manifest": manifest.read_bytes() == response, "report": report,
    }, indent=2))
