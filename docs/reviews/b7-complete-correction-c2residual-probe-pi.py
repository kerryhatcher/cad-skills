# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Focused C2 residual probe: an unbound result file changes after the package loads it."""
import hashlib
import importlib.util
import json
import pathlib
import shutil
import tempfile

ROOT = pathlib.Path('/mnt/storage/projects/cad-skills')
BASE = pathlib.Path('/tmp/b7-pi-workflow-b4czyk7h/base')
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
workflow = fixture.workflow
review = fixture.review

RESULTS = {}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


tmp = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-c2res-'))
RESULTS['temporary_directory'] = str(tmp)


def run(label, target_rel, add):
    proj = tmp / label
    shutil.copytree(BASE, proj, symlinks=True)
    review_path = proj / 'out/fab/source-review/REVIEW.json'
    rsha = sha(review_path)
    target = proj / target_rel
    original_gate = review.gate

    def gate_then_change(*args, **kwargs):
        result = original_gate(*args, **kwargs)
        body = json.loads(target.read_text())
        body.update(add)
        target.write_text(json.dumps(body, indent=2, sort_keys=True) + '\n')
        return result

    review.gate = gate_then_change
    try:
        dest = proj / 'out/fab/packages' / label
        code, manifest = workflow.package(proj, fixture.PROFILE, 'trial-1', review_path, dest,
                                          proj / 'out/fab/design', proj / 'out/fab/supplier', rsha)
    finally:
        review.gate = original_gate
    published = dest / ('reports/' + target_rel.split('/')[-1])
    out = {'exit': code, 'status': manifest['status'],
           'reasons': [r['text'] for r in manifest['reasons']],
           'published_report_has_injection': published.is_file() and add['injected_probe'] == json.loads(published.read_text()).get('injected_probe'),
           'published_sha256': sha(published) if published.is_file() else None}
    return out


RESULTS['change_supplier_result'] = run('supplier-result', 'out/fab/supplier/supplier-result.json',
                                        {'injected_probe': 'changed after the package loaded it'})
RESULTS['change_design_result'] = run('design-result', 'out/fab/design/design-result.json',
                                      {'injected_probe': 'changed after the package loaded it'})
RESULTS['workflow_sha256_after'] = sha(workflow.__file__)
print(json.dumps(RESULTS, indent=2, sort_keys=True))