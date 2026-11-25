# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure whether output paths can replace protected inputs."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills/pcb-fab-package/scripts/fetch_sources.py"
SPEC = importlib.util.spec_from_file_location("fetch_sources_probe", SOURCE)
FETCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FETCH)
BODY = b"project-authored response bytes\n"


def run_case(label, destination, protected_path):
    with tempfile.TemporaryDirectory(prefix=f"source-alias-{label}-") as folder:
        root = Path(folder)
        protected = root / protected_path
        protected.parent.mkdir(parents=True, exist_ok=True)
        before = b"protected input bytes\n"
        protected.write_bytes(before)
        manifest = root / "sources.yaml"
        record = {
            "schema": "cad-skills/sources",
            "schema_version": 1,
            "sources": [{
                "id": label,
                "path": destination,
                "url": "https://example.test/source",
                "retrieved": "2026-11-15",
                "sha256": hashlib.sha256(BODY).hexdigest(),
                "content_type": "text/plain",
                "magic": None,
                "license_state": "Fixture only.",
                "distribution_decision": "exclude-full-copy",
                "profile_binding": None,
            }],
        }
        manifest.write_text(json.dumps(record), encoding="utf-8")
        original_manifest = manifest.read_bytes()
        calls = []

        def fetch(url):
            calls.append(url)
            return BODY

        code, report = FETCH.main(["--manifest", str(manifest)], fetch=fetch)
        return {
            "case": label,
            "exit": code,
            "fetch_calls": len(calls),
            "manifest_changed": manifest.read_bytes() != original_manifest,
            "protected_changed": protected.read_bytes() != before,
            "protected_replaced": protected.read_bytes() == BODY,
            "report": report,
        }


print(json.dumps([
    run_case("manifest", "./sources.yaml", "sources.yaml"),
    run_case("profile", "supplier/profiles/./fixture.yaml", "supplier/profiles/fixture.yaml"),
], indent=2, sort_keys=True))
