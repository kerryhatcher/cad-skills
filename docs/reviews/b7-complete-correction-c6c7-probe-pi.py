# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Focused C6 and C7 runs of the frozen test functions. Read-only for product files."""
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


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-c6c7-'))
before = {'workflow': sha(fixture.workflow.__file__),
          'fab': sha(ROOT / 'skills/pcb-fab-package/scripts/fab.py'),
          'test': sha(ROOT / 'tests/test_pcb_fab_workflow.py')}
fixture.test_review_lock(tmp / 'lock')
fixture.test_interrupted_binding(tmp / 'interrupt')
after = {'workflow': sha(fixture.workflow.__file__),
         'fab': sha(ROOT / 'skills/pcb-fab-package/scripts/fab.py'),
         'test': sha(ROOT / 'tests/test_pcb_fab_workflow.py')}
out = {'temporary_directory': str(tmp), 'checks': [{'name': n, 'ok': ok} for n, ok in fixture.RESULTS],
       'hashes_before': before, 'hashes_after': after, 'hashes_equal': before == after}
print(json.dumps(out, indent=2, sort_keys=True))