# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Independent focused probes for the residual publication repair. Read-only for product files."""
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import tempfile

ROOT = pathlib.Path('/mnt/storage/projects/cad-skills')
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
workflow = fixture.workflow
fab = fixture.fab
VAL = fixture.VAL

RESULTS = {}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def content_hash(record):
    body = {k: v for k, v in record.items() if k != 'content_sha256'}
    return VAL.canonical_hash(body)


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-residual-final-'))
RESULTS['temporary_directory'] = str(tmp)
RESULTS['workflow_sha256_before'] = sha(workflow.__file__)
RESULTS['fab_sha256_before'] = sha(ROOT / 'skills/pcb-fab-package/scripts/fab.py')

base, review_path, rsha = fixture.prepared(tmp, 'base')
RESULTS['base_prepared'] = True


def run_package(label, mutate_result=None):
    proj = tmp / label
    shutil.copytree(base, proj, symlinks=True)
    if mutate_result is not None:
        path = proj / 'out/fab/supplier/supplier-result.json'
        rec = json.loads(path.read_text())
        mutate_result(rec)
        path.write_text(json.dumps(rec, indent=2, sort_keys=True) + '\n')
    dest = proj / 'out/fab/packages' / label
    staging = dest.parent / ('.staging-' + dest.name)
    try:
        code, manifest = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path,
                                          dest, proj / 'out/fab/design', proj / 'out/fab/supplier', rsha)
        return {'exit': code, 'status': manifest['status'], 'published': dest.exists(),
                'staging_kept': staging.is_dir(), 'stop': None,
                'reasons': [r['text'] for r in manifest['reasons']]}
    except workflow.Stop as err:
        return {'exit': err.code, 'status': None, 'published': dest.exists(),
                'staging_kept': staging.is_dir(), 'stop': str(err), 'reasons': []}


RESULTS['baseline'] = run_package('baseline')
RESULTS['changed_row_old_hash'] = run_package(
    'row-old-hash', lambda r: next(row for row in r['rows'] if row['mandatory']).update(status='fail'))


def new_hash_bad_exit(r):
    next(row for row in r['rows'] if row['mandatory']).update(status='fail')
    r['content_sha256'] = content_hash(r)


RESULTS['changed_row_bad_exit'] = run_package('row-bad-exit', new_hash_bad_exit)


def drop_row(r):
    r['rows'] = [row for row in r['rows'] if row['condition'] != 'service.order_multiple']
    r['content_sha256'] = content_hash(r)


RESULTS['missing_mandatory_row'] = run_package('row-missing', drop_row)


def consistent_fail(r):
    next(row for row in r['rows'] if row['mandatory']).update(status='fail')
    r['exit'] = workflow.rows_exit(r['rows'])
    r['content_sha256'] = content_hash(r)


RESULTS['consistent_failing_row'] = run_package('row-consistent-fail', consistent_fail)


def empty_rows(r):
    r['rows'] = []
    r['content_sha256'] = content_hash(r)


RESULTS['empty_rows'] = run_package('row-empty', empty_rows)

# Binding drift: a real byte change after manifest validation.
proj = tmp / 'binding-drift'
shutil.copytree(base, proj, symlinks=True)
review3 = proj / 'out/fab/source-review/REVIEW.json'
rsha3 = sha(review3)
binding_path = proj / 'out/fab/design/design-binding.json'
original_build = workflow.VAL.build_report
state = {'done': False}


def build_then_drift(*args, **kwargs):
    res = original_build(*args, **kwargs)
    if not state['done']:
        state['done'] = True
        binding_path.write_bytes(binding_path.read_bytes() + b'\n')
    return res


workflow.VAL.build_report = build_then_drift
dest3 = proj / 'out/fab/packages/binding-drift'
staging3 = dest3.parent / ('.staging-' + dest3.name)
try:
    code3, _manifest3 = workflow.package(proj, fixture.PROFILE, 'trial-1', review3, dest3,
                                         proj / 'out/fab/design', proj / 'out/fab/supplier', rsha3)
    RESULTS['binding_drift'] = {'exit': code3, 'published': dest3.exists(), 'stop': None}
except workflow.Stop as err:
    RESULTS['binding_drift'] = {'exit': err.code, 'published': dest3.exists(),
                                'staging_kept': staging3.is_dir(), 'stop': str(err)}
finally:
    workflow.VAL.build_report = original_build

# Drawing links.
facts = base / 'out/fab/design/drawing-facts.json'
draw = {}
for label, dangling in (('dangling', True), ('existing', False)):
    target = tmp / ('outside-draw-' + label + '.pdf')
    if not dangling:
        target.write_bytes(b'outside before\n')
    link = tmp / ('draw-' + label + '.pdf')
    link.symlink_to(target)
    before = target.read_bytes() if target.exists() else None
    code = fab.main(['drawing', '--facts', str(facts), '--out', str(link)])
    unchanged = (target.read_bytes() == before) if target.exists() else not target.exists()
    draw['drawing_' + label] = {'exit': code, 'link_preserved': link.is_symlink(), 'target_unchanged': unchanged}
for label, dangling in (('dangling', True), ('existing', False)):
    target = tmp / ('outside-facts-' + label + '.json')
    if not dangling:
        target.write_bytes(b'outside before\n')
    link = tmp / ('facts-' + label + '.json')
    link.symlink_to(target)
    before = target.read_bytes() if target.exists() else None
    code = fab.main(['drawing-facts', '--inventory', str(base / 'out/fab/design/inventory.json'),
                     '--profile', str(fixture.PROFILE), '--board', str(base / 'kicad/board.kicad_pcb'),
                     '--release', 'x', '--out', str(link)])
    unchanged = (target.read_bytes() == before) if target.exists() else not target.exists()
    draw['drawing_facts_' + label] = {'exit': code, 'link_preserved': link.is_symlink(), 'target_unchanged': unchanged}
plain = tmp / 'plain-facts.json'
plain_code = fab.main(['drawing-facts', '--inventory', str(base / 'out/fab/design/inventory.json'),
                       '--profile', str(fixture.PROFILE), '--board', str(base / 'kicad/board.kicad_pcb'),
                       '--release', 'x', '--out', str(plain)])
draw['ordinary_output'] = {'exit': plain_code, 'written': plain.is_file()}
RESULTS['drawing'] = draw

RESULTS['workflow_sha256_after'] = sha(workflow.__file__)
RESULTS['fab_sha256_after'] = sha(ROOT / 'skills/pcb-fab-package/scripts/fab.py')
print(json.dumps(RESULTS, indent=2, sort_keys=True))