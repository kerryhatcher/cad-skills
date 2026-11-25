# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure a captured-profile file link in an isolated directory."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

root = Path('/mnt/storage/projects/cad-skills')
spec = importlib.util.spec_from_file_location('fixture', root / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
base = Path(tempfile.mkdtemp(prefix='b7-leaf-root-'))
project = base / 'project'
scratch = project / 'out/fab/supplier/captured'
scratch.mkdir(parents=True)
target = base / 'outside-profile.yaml'
link = scratch / 'profile.yaml'
link.symlink_to(target)
result = {'workflow_sha256': hashlib.sha256(Path(fixture.workflow.__file__).read_bytes()).hexdigest(),
          'target_absent_before': not target.exists(), 'temporary_directory': str(base)}
try:
    fixture.workflow.profile_from_bytes(project, fixture.PROFILE.read_bytes(), scratch)
    result['returned'] = True
except Exception as exc:
    result['exception'] = str(exc)
    result['code'] = getattr(exc, 'code', None)
result['outside_file_created'] = target.exists()
result['link_preserved'] = link.is_symlink()
result['outside_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
print(json.dumps(result, indent=2))
