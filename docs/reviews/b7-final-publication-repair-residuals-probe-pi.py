# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Independent checks of the three codex residual findings on the frozen C1/C2/C5 repair."""
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import tempfile

ROOT = pathlib.Path('/mnt/storage/projects/cad-skills')
BASE = pathlib.Path('/tmp/b7-pi-final-086rfp18/base')
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
workflow = fixture.workflow
fab = fixture.fab

RESULTS = {}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-codex-'))
RESULTS['temporary_directory'] = str(tmp)
RESULTS['workflow_sha256'] = sha(workflow.__file__)
RESULTS['fab_sha256'] = sha(ROOT / 'skills/pcb-fab-package/scripts/fab.py')

# Finding 2: a mandatory row changed to fail, with exit 0 and the binding unchanged.
proj = tmp / 'supplier-row'
shutil.copytree(BASE, proj, symlinks=True)
review_path = proj / 'out/fab/source-review/REVIEW.json'
rsha = sha(review_path)
sr_path = proj / 'out/fab/supplier/supplier-result.json'
before_sha = sha(sr_path)
sr = json.loads(sr_path.read_text())
changed_row = None
for row in sr['rows']:
    if row['mandatory']:
        row['status'] = 'fail'
        changed_row = row['condition']
        break
sr_path.write_text(json.dumps(sr, indent=2, sort_keys=True) + '\n')
dest = proj / 'out/fab/packages/supplier-row'
try:
    code, manifest = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path, dest,
                                      proj / 'out/fab/design', proj / 'out/fab/supplier', rsha)
    stop = None
except workflow.Stop as err:
    code, manifest, stop = err.code, {}, str(err)
RESULTS['finding2_supplier_row'] = {
    'changed_row': changed_row,
    'result_sha_before': before_sha, 'result_sha_after': sha(sr_path),
    'exit': code, 'status': manifest.get('status'), 'published': dest.exists(),
    'reasons': [r['text'] for r in manifest.get('reasons', [])], 'stop': stop}

# Finding 3: a coordinated change to the source output and the binding after the manifest validation.
proj3 = tmp / 'binding-drift'
shutil.copytree(BASE, proj3, symlinks=True)
review3 = proj3 / 'out/fab/source-review/REVIEW.json'
rsha3 = sha(review3)
gerber = proj3 / 'out/fab/design/export/board-F_Cu.gbr'
binding_path = proj3 / 'out/fab/design/design-binding.json'
captured_gerber = gerber.read_bytes()
captured_binding_sha = sha(binding_path)
changed_bytes = b'changed source copper after the manifest\n'
original_build = workflow.VAL.build_report
state = {'done': False}


def build_then_drift(*args, **kwargs):
    res = original_build(*args, **kwargs)
    if not state['done']:
        state['done'] = True
        binding = json.loads(binding_path.read_text())
        gerber.write_bytes(changed_bytes)
        binding['outputs']['export/board-F_Cu.gbr'] = hashlib.sha256(changed_bytes).hexdigest()
        binding_path.write_text(json.dumps(binding, indent=2, sort_keys=True) + '\n')
    return res


workflow.VAL.build_report = build_then_drift
dest3 = proj3 / 'out/fab/packages/binding-drift'
try:
    code3, manifest3 = workflow.package(proj3, fixture.PROFILE, 'trial-1', review3, dest3,
                                        proj3 / 'out/fab/design', proj3 / 'out/fab/supplier', rsha3)
    stop3 = None
except workflow.Stop as err:
    code3, manifest3, stop3 = err.code, {}, str(err)
finally:
    workflow.VAL.build_report = original_build
published = dest3 / 'gerber/board-F_Cu.gbr'
RESULTS['finding3_binding_drift'] = {
    'exit': code3, 'status': manifest3.get('status'), 'published': dest3.exists(), 'stop': stop3,
    'reasons': [r['text'] for r in manifest3.get('reasons', [])],
    'captured_binding_sha256': captured_binding_sha, 'current_binding_sha256': sha(binding_path),
    'binding_drifted': captured_binding_sha != sha(binding_path),
    'captured_gerber_sha256': hashlib.sha256(captured_gerber).hexdigest(),
    'changed_source_sha256': hashlib.sha256(changed_bytes).hexdigest(),
    'published_gerber_sha256': sha(published) if published.is_file() else None}

# Finding 1: the two standalone drawing commands follow a link at --out.
proj1 = tmp / 'drawing'
shutil.copytree(BASE, proj1, symlinks=True)
facts = proj1 / 'out/fab/design/drawing-facts.json'
outside1 = tmp / 'outside-drawing.pdf'
outside1.write_bytes(b'outside before\n')
link1 = tmp / 'drawing-out.pdf'
link1.symlink_to(outside1)
before1 = sha(outside1)
code1 = fab.main(['drawing', '--facts', str(facts), '--out', str(link1)])
RESULTS['finding1_drawing'] = {'exit': code1, 'link_preserved': link1.is_symlink(),
                               'outside_changed': sha(outside1) != before1,
                               'outside_sha256': sha(outside1)}
outside2 = tmp / 'outside-facts.json'
outside2.write_bytes(b'outside before\n')
link2 = tmp / 'facts-out.json'
link2.symlink_to(outside2)
before2 = sha(outside2)
code2 = fab.main(['drawing-facts', '--inventory', str(proj1 / 'out/fab/design/inventory.json'),
                  '--profile', str(fixture.PROFILE), '--board', str(proj1 / 'kicad/board.kicad_pcb'),
                  '--release', 'x', '--out', str(link2)])
RESULTS['finding1_drawing_facts'] = {'exit': code2, 'link_preserved': link2.is_symlink(),
                                     'outside_changed': sha(outside2) != before2,
                                     'outside_sha256': sha(outside2)}

RESULTS['workflow_sha256_after'] = sha(workflow.__file__)
print(json.dumps(RESULTS, indent=2, sort_keys=True))