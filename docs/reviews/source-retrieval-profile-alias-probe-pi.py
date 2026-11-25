# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure a destination that aliases an input profile read by another entry."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

import yaml

root = Path('/mnt/storage/projects/cad-skills')
spec = importlib.util.spec_from_file_location(
    "retrieval_probe", root / "skills/pcb-fab-package/scripts/fetch_sources.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix="retrieval-profile-alias-") as folder:
    base = Path(folder)
    (base / "supplier" / "pages").mkdir(parents=True)
    (base / "supplier" / "profiles").mkdir(parents=True)
    page = b"<!doctype html>\n<title>page</title>\n"
    profile = {"id": "fixture", "extensions": {"evidence_pages": {"two-layer": {"sha256": hashlib.sha256(page).hexdigest()}}}}
    profile_path = base / "supplier" / "profiles" / "fixture.yaml"
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False))
    before = profile_path.read_bytes()
    replacement = b"replacement profile bytes\n"
    record = {
        "schema": "cad-skills/sources", "schema_version": 1,
        "sources": [
            {"id": "alias", "path": "supplier/profiles/fixture.yaml", "url": "https://example.test/alias",
             "retrieved": "2026-11-15", "sha256": hashlib.sha256(replacement).hexdigest(),
             "content_type": "text/plain", "magic": None, "license_state": "fixture",
             "distribution_decision": "exclude-full-copy", "profile_binding": None},
            {"id": "bound", "path": "supplier/pages/two-layer.html", "url": "https://example.test/bound",
             "retrieved": "2026-11-15", "sha256": hashlib.sha256(page).hexdigest(),
             "content_type": "text/html", "magic": "markup", "license_state": "fixture",
             "distribution_decision": "exclude-full-copy",
             "profile_binding": "supplier/profiles/fixture.yaml"},
        ],
    }
    manifest = base / "sources.yaml"
    manifest.write_text(json.dumps(record))
    responses = {"https://example.test/alias": replacement, "https://example.test/bound": page}
    code, report = module.main(["--manifest", str(manifest)], fetch=lambda url: responses[url])
    print(json.dumps({
        "exit": code,
        "profile_changed": profile_path.read_bytes() != before,
        "profile_replaced": profile_path.read_bytes() == replacement,
        "rows": [{"id": r["id"], "written": r["written"], "hash_status": r["hash_status"]} for r in report.get("entries", [])],
    }, indent=2))