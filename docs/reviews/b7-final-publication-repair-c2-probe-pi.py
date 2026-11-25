# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Independent C2 probes: captured design inputs before the supplier measurement."""
import hashlib
import importlib.util
import json
import pathlib
import tempfile

ROOT = pathlib.Path('/mnt/storage/projects/cad-skills')
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
workflow = fixture.workflow
fab = fixture.fab

RESULTS = {}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-c2-'))
RESULTS['temporary_directory'] = str(tmp)

# Probe 1: a design output that differs from the binding is refused before any measurement.
proj = fixture.fresh_project(tmp, 'mismatch')
fixture.run_fab('design', '--project', str(proj), '--profile', str(fixture.PROFILE))
drill = proj / 'out/fab/design/export/board-PTH.drl'
drill.write_bytes(b'changed before the supplier measurement\n')
p = fixture.run_fab('supplier', '--project', str(proj), '--profile', str(fixture.PROFILE))
RESULTS['mismatch_before_measurement'] = {
    'exit': p.returncode,
    'message_has_binding_reason': 'differs from the accepted design binding' in (p.stdout + p.stderr),
    'stderr_tail': (p.stderr or '')[-240:]}

# Probe 2: a transient change to the source mask Gerber during the worker does not change the measured bytes.
proj2 = fixture.fresh_project(tmp, 'transient')
fixture.run_fab('design', '--project', str(proj2), '--profile', str(fixture.PROFILE))
gerber = proj2 / 'out/fab/design/export/board-F_Mask.gbr'
captured = gerber.read_bytes()
original_worker = fab.run_mask_worker


def worker_with_transient(gerber_arg, limit, report):
    gerber.write_bytes(b'transient bytes, not the design output\n')
    try:
        return original_worker(gerber_arg, limit, report)
    finally:
        gerber.write_bytes(captured)


fab.run_mask_worker = worker_with_transient
try:
    code, result = workflow.supplier(proj2, fixture.PROFILE, proj2 / 'out/fab/supplier',
                                     proj2 / 'out/fab/design')
finally:
    fab.run_mask_worker = original_worker
mask = json.loads((proj2 / 'out/fab/supplier/mask.json').read_text())
RESULTS['transient_during_measurement'] = {
    'supplier_exit': code,
    'captured_sha256': hashlib.sha256(captured).hexdigest(),
    'mask_gerber_sha256': mask['gerber_sha256'],
    'result_measure_input_sha256': result['measure_inputs']['export/board-F_Mask.gbr'],
    'bind_is_captured': mask['gerber_sha256'] == result['measure_inputs']['export/board-F_Mask.gbr'] == hashlib.sha256(captured).hexdigest()}

RESULTS['workflow_sha256_after'] = sha(workflow.__file__)
print(json.dumps(RESULTS, indent=2, sort_keys=True))