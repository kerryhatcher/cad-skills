# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Focused workflow probes for C2 and C3. Read-only for product files."""
import hashlib
import importlib.util
import json
import pathlib
import shutil
import tempfile

ROOT = pathlib.Path('/mnt/storage/projects/cad-skills')
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
workflow = fixture.workflow
review = fixture.review

RESULTS = {}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-workflow-'))
RESULTS['temporary_directory'] = str(tmp)
RESULTS['workflow_sha256_before'] = sha(workflow.__file__)

# One prepared project: design and supplier runs, manual evidence, source review.
proj, review_path, rsha = fixture.prepared(tmp, 'base')
supplier_dir = proj / 'out/fab/supplier'
design_dir = proj / 'out/fab/design'
RESULTS['supplier_exit_row'] = json.loads((supplier_dir / 'supplier-result.json').read_text())['exit']
RESULTS['design_binding'] = json.loads((design_dir / 'design-binding.json').read_text())['outputs']

# Positive: the published bytes equal the measured binding bytes.
dest = proj / 'out/fab/packages' / 'baseline'
code, manifest = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path, dest, design_dir, supplier_dir, rsha)
measured = json.loads((design_dir / 'design-binding.json').read_text())['outputs']['export/board-F_Cu.gbr']
published = sha(dest / 'gerber/board-F_Cu.gbr')
entry = next(o for o in manifest['outputs'] if o['path'] == 'gerber/board-F_Cu.gbr')
RESULTS['baseline'] = {'exit': code, 'status': manifest['status'], 'reasons': [r['text'] for r in manifest['reasons']],
                       'measured_binding_sha256': measured, 'published_sha256': published,
                       'manifest_output_sha256': entry['sha256'],
                       'published_equals_measured': published == measured == entry['sha256']}

# C2: a controlled change to a different bound artifact (the PTH drill) before the copy.
drill = design_dir / 'export/board-PTH.drl'
injected_drill = b'injected drill bytes, not measured\n'
original_gate = review.gate


def gate_then_inject(*args, **kwargs):
    result = original_gate(*args, **kwargs)
    drill.write_bytes(injected_drill)
    return result


review.gate = gate_then_inject
try:
    dest2 = proj / 'out/fab/packages' / 'copy-drill'
    code2, manifest2 = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path, dest2, design_dir, supplier_dir, rsha)
finally:
    review.gate = original_gate
    drill.write_bytes(drill.read_bytes())  # restore is not necessary, but the file is temporary anyway
reasons2 = [r['text'] for r in manifest2['reasons']]
entry2 = next(o for o in manifest2['outputs'] if o['path'] == 'gerber/board-PTH.drl')
RESULTS['c2_copy_change'] = {
    'exit': code2, 'status': manifest2['status'],
    'reason_named': any('gerber/board-PTH.drl changed after its measurement' in r for r in reasons2),
    'published_equals_injected': sha(dest2 / 'gerber/board-PTH.drl') == hashlib.sha256(injected_drill).hexdigest(),
    'manifest_output_sha256': entry2['sha256'], 'reasons': reasons2}

# Restore the measured drill bytes from the binding source before the next package run.
# The original bytes are still available in the clean staging copy.
clean_drill = dest / 'gerber/board-PTH.drl'
drill.write_bytes(clean_drill.read_bytes())
RESULTS['c2_restored_drill_sha256'] = sha(drill)
RESULTS['c2_binding_drill_sha256'] = json.loads((design_dir / 'design-binding.json').read_text())['outputs']['export/board-PTH.drl']

# C3: a byte-only change to the original manual record after measurement.
manual = proj / 'out/fab/manual-record.json'
original_manual_sha = sha(manual)
manual.write_bytes(manual.read_bytes() + b' ')
dest3 = proj / 'out/fab/packages' / 'manual-change'
code3, manifest3 = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path, dest3, design_dir, supplier_dir, rsha)
reasons3 = [r['text'] for r in manifest3['reasons']]
RESULTS['c3_manual_change'] = {
    'original_sha256_before': original_manual_sha, 'original_sha256_after': sha(manual),
    'exit': code3, 'status': manifest3['status'],
    'reason_named': any('original manual record changed before publication' in r for r in reasons3),
    'reasons': reasons3}

manual.write_bytes(manual.read_bytes()[:-1])
RESULTS['c3_restored_manual_sha256'] = sha(manual)

RESULTS['workflow_sha256_after'] = sha(workflow.__file__)
RESULTS['fab_sha256_after'] = sha(ROOT / 'skills/pcb-fab-package/scripts/fab.py')

print(json.dumps(RESULTS, indent=2, sort_keys=True))