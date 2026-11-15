# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Make an isolated skill with project-authored source bytes for local tests.

The repository profiles and manifests retain their source hashes. Only temporary copies change.
The fixture pages test hash bindings. They contain no supplier text and support no supplier claim.
"""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import yaml

_TEMPORARY = tempfile.TemporaryDirectory(prefix="fab-fixture-")
_SKILL = None


def fixture_skill(source: Path) -> Path:
    """Return a temporary skill with measured fixture hashes and explicit fixture source URLs."""
    global _SKILL
    if _SKILL is not None:
        return _SKILL
    skill = Path(_TEMPORARY.name) / "pcb-fab-package"
    shutil.copytree(source, skill, ignore=shutil.ignore_patterns("pages", "__pycache__"))
    pages = skill / "supplier/pages"
    pages.mkdir()
    manifest = yaml.safe_load((skill / "sources.yaml").read_text())
    replacements = {}
    entries = []
    for entry in manifest["sources"]:
        if entry["distribution_decision"] != "exclude-full-copy":
            continue
        name = Path(entry["path"]).stem
        data = f"<html><body>Project-authored test page: {name}. No supplier evidence.</body></html>\n".encode()
        (skill / entry["path"]).write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        replacements[entry["sha256"]] = digest
        replacements[entry["url"]] = f"https://example.invalid/fixture/{name}/"
        entry = dict(entry, sha256=digest, url=replacements[entry["url"]],
                     license_state="Project-authored fixture. No supplier evidence.")
        entries.append(entry)
    manifest["sources"] = entries
    (skill / "sources.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return replacements.get(value, value) if isinstance(value, str) else value

    for path in (skill / "supplier/profiles").glob("*.yaml"):
        profile = replace(json.loads(path.read_text()))
        profile["extensions"]["test_fixture"] = "Project-authored bytes. No supplier evidence."
        body = {key: value for key, value in profile.items() if key != "content_sha256"}
        data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        profile["content_sha256"] = hashlib.sha256(data).hexdigest()
        path.write_text(json.dumps(profile, indent=2) + "\n")
    _SKILL = skill
    return skill
