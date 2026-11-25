# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Focused C1 probe: a leaf link in the design output and log paths. Read-only for product files."""
import hashlib
import importlib.util
import json
import pathlib
import tempfile

ROOT = pathlib.Path('/mnt/storage/projects/cad-skills')
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)

RESULTS = {}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-c1design-'))
RESULTS['temporary_directory'] = str(tmp)
RESULTS['workflow_sha256_before'] = sha(fixture.workflow.__file__)

proj = fixture.fresh_project(tmp, 'c1design')
design = proj / 'out/fab/design'
(design / 'logs').mkdir(parents=True)
target_inventory = tmp / 'outside-inventory.json'
target_log = tmp / 'outside-erc.stderr'
(design / 'inventory.json').symlink_to(target_inventory)
(design / 'logs' / 'erc.stderr').symlink_to(target_log)
RESULTS['targets_absent_before'] = not target_inventory.exists() and not target_log.exists()

p = fixture.run_fab('design', '--project', str(proj), '--profile', str(fixture.PROFILE))
RESULTS['design_exit'] = p.returncode
RESULTS['outside_inventory_created'] = target_inventory.exists()
RESULTS['outside_log_created'] = target_log.exists()
RESULTS['outside_inventory_sha256'] = sha(target_inventory) if target_inventory.exists() else None
RESULTS['outside_log_sha256'] = sha(target_log) if target_log.exists() else None
RESULTS['inventory_link_preserved'] = (design / 'inventory.json').is_symlink()
RESULTS['log_link_preserved'] = (design / 'logs' / 'erc.stderr').is_symlink()
RESULTS['stdout_tail'] = (p.stdout or '')[-300:]
RESULTS['stderr_tail'] = (p.stderr or '')[-300:]
RESULTS['workflow_sha256_after'] = sha(fixture.workflow.__file__)

print(json.dumps(RESULTS, indent=2, sort_keys=True))