# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Confirm the accepted C3/C6/C7 and directory-link cases under the frozen code. Read-only."""
import hashlib
import importlib.util
import json
import pathlib
import tempfile

ROOT = pathlib.Path('/mnt/storage/projects/cad-skills')
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-accepted-'))
before = sha(ROOT / 'skills/pcb-fab-package/scripts/workflow.py')
fixture.test_captured_child_link(tmp)
fixture.test_manual_original(tmp / 'c3')
fixture.test_review_lock(tmp / 'lock')
fixture.test_interrupted_binding(tmp / 'c7')
after = sha(ROOT / 'skills/pcb-fab-package/scripts/workflow.py')
out = {'temporary_directory': str(tmp),
       'checks': [{'name': n, 'ok': ok} for n, ok in fixture.RESULTS],
       'all_ok': all(ok for _, ok in fixture.RESULTS),
       'workflow_sha256_before': before, 'workflow_sha256_after': after}
print(json.dumps(out, indent=2, sort_keys=True))