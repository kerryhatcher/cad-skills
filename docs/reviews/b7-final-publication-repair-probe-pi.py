# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Independent focused probes for the C1/C2/C5 repair. Read-only for product files."""
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
review = fixture.review

RESULTS = {}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def run_step(step, proj):
    return fixture.run_fab(step, '--project', str(proj), '--profile', str(fixture.PROFILE))


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-final-'))
RESULTS['temporary_directory'] = str(tmp)
RESULTS['workflow_sha256_before'] = sha(workflow.__file__)
RESULTS['test_sha256_before'] = sha(ROOT / 'tests/test_pcb_fab_workflow.py')

base, review_path, rsha = fixture.prepared(tmp, 'base')
RESULTS['base_prepared'] = True

# --- C1: links at complete destinations ---
c1 = {}
cases = [
    ('profile-file', 'design', 'out/fab/design/captured/profile.yaml', True),
    ('dangling-profile-file', 'design', 'out/fab/design/captured/profile.yaml', False),
    ('design-output', 'design', 'out/fab/design/inventory.json', True),
    ('design-log', 'design', 'out/fab/design/logs/erc.stderr', True),
    ('supplier-output', 'supplier', 'out/fab/supplier/supplier.kicad_dru', True),
    ('worker-report', 'supplier', 'out/fab/supplier/mask.json', True),
]
for label, step, rel, target_exists in cases:
    proj = tmp / ('c1-' + label)
    shutil.copytree(base, proj, symlinks=True)
    outside = tmp / ('outside-' + label + '.txt')
    if target_exists:
        outside.write_bytes(b'outside before the run\n')
    link = proj / rel
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.exists():
        link.unlink()
    os.symlink(outside, link)
    p = run_step(step, proj)
    unchanged = outside.read_bytes() == b'outside before the run\n' if target_exists else not outside.exists()
    c1[label] = {'exit': p.returncode, 'link_preserved': link.is_symlink(), 'outside_unchanged': unchanged}
RESULTS['c1_leaf_links'] = c1

# C1 package destinations: final and staging links.
c1pkg = {}
for label, which in (('final', 'final'), ('staging', 'staging')):
    proj = tmp / ('c1pkg-' + label)
    shutil.copytree(base, proj, symlinks=True)
    dest = proj / 'out/fab/packages' / 'x'
    (dest.parent).mkdir(parents=True, exist_ok=True)
    outside = tmp / ('outside-pkg-' + label)
    outside.mkdir()
    target = dest if which == 'final' else dest.parent / '.staging-x'
    os.symlink(outside, target)
    try:
        code, _ = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path,
                                   dest, proj / 'out/fab/design', proj / 'out/fab/supplier', rsha)
        c1pkg[label] = {'exit': code, 'link_preserved': target.is_symlink(), 'outside_empty': not any(outside.iterdir())}
    except workflow.Stop as err:
        c1pkg[label] = {'exit': err.code, 'link_preserved': target.is_symlink(), 'outside_empty': not any(outside.iterdir())}
RESULTS['c1_package_links'] = c1pkg

# --- C2: a change to a result file after the package read must not be published ---
def result_change(label, rel):
    proj = tmp / label
    shutil.copytree(base, proj, symlinks=True)
    dest = proj / 'out/fab/packages' / label
    target = proj / rel
    original = target.read_bytes()
    original_gate = review.gate

    def gate_then_change(*args, **kwargs):
        res = original_gate(*args, **kwargs)
        body = json.loads(target.read_text())
        body['injected_probe'] = 'changed after the read'
        target.write_text(json.dumps(body, indent=2, sort_keys=True) + '\n')
        return res

    review.gate = gate_then_change
    try:
        code, manifest = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path, dest,
                                          proj / 'out/fab/design', proj / 'out/fab/supplier', rsha)
    finally:
        review.gate = original_gate
    published = dest / ('reports/' + pathlib.Path(rel).name)
    published_body = json.loads(published.read_text()) if published.is_file() else {}
    entry = next((o for o in manifest['outputs'] if o['path'] == 'reports/' + pathlib.Path(rel).name), None)
    return {'exit': code, 'status': manifest['status'],
            'published_has_injection': published_body.get('injected_probe') == 'changed after the read',
            'published_matches_original': published.is_file() and sha(published) == hashlib.sha256(original).hexdigest(),
            'manifest_output_sha256': entry['sha256'] if entry else None,
            'original_sha256': hashlib.sha256(original).hexdigest(),
            'reasons': [r['text'] for r in manifest['reasons']]}


RESULTS['c2_supplier_result_change'] = result_change('c2-supplier', 'out/fab/supplier/supplier-result.json')
RESULTS['c2_design_result_change'] = result_change('c2-design', 'out/fab/design/design-result.json')

# --- C5: changes to the staged package after validation ---
def staged_case(label, mutate):
    proj = tmp / ('c5-' + label)
    shutil.copytree(base, proj, symlinks=True)
    dest = proj / 'out/fab/packages' / label
    staging = dest.parent / ('.staging-' + dest.name)
    original_build = workflow.VAL.build_report
    state = {'done': False}

    def build_then_mutate(*args, **kwargs):
        res = original_build(*args, **kwargs)
        if not state['done']:
            state['done'] = True
            if staging.is_dir():
                mutate(staging)
        return res

    workflow.VAL.build_report = build_then_mutate
    code, message = 0, ''
    try:
        code, _ = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path, dest,
                                   proj / 'out/fab/design', proj / 'out/fab/supplier', rsha)
    except workflow.Stop as err:
        code, message = err.code, str(err)
    except Exception as err:  # noqa: BLE001
        code, message = type(err).__name__, str(err)
    finally:
        workflow.VAL.build_report = original_build
    return {'exit': code, 'published': dest.exists(), 'staging_kept': staging.is_dir(), 'message': message[:220]}


RESULTS['c5_staged_gerber'] = staged_case('gerber', lambda s: (s / 'gerber/board-F_Cu.gbr').write_bytes(b'changed\n'))
RESULTS['c5_staged_manifest'] = staged_case('manifest', lambda s: (s / 'manifest.json').write_bytes((s / 'manifest.json').read_bytes() + b'\n'))
RESULTS['c5_unexpected_file'] = staged_case('unexpected', lambda s: (s / 'extra.txt').write_bytes(b'extra\n'))
RESULTS['c5_missing_output'] = staged_case('missing', lambda s: (s / 'gerber/board-F_Cu.gbr').unlink())

# --- Baseline: the unchanged project qualifies and publishes the captured bytes ---
proj = tmp / 'baseline'
shutil.copytree(base, proj, symlinks=True)
dest = proj / 'out/fab/packages' / 'baseline'
code, manifest = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path, dest,
                                  proj / 'out/fab/design', proj / 'out/fab/supplier', rsha)
RESULTS['baseline'] = {'exit': code, 'published': dest.exists(), 'status': manifest['status'],
                       'reasons': [r['text'] for r in manifest['reasons']]}

RESULTS['workflow_sha256_after'] = sha(workflow.__file__)
RESULTS['test_sha256_after'] = sha(ROOT / 'tests/test_pcb_fab_workflow.py')
RESULTS['fab_sha256_after'] = sha(ROOT / 'skills/pcb-fab-package/scripts/fab.py')
print(json.dumps(RESULTS, indent=2, sort_keys=True))