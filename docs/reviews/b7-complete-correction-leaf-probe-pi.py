# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Focused unit probes for the B7 complete correction. Read-only for product files."""
import hashlib
import importlib.util
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path('/mnt/storage/projects/cad-skills')
spec = importlib.util.spec_from_file_location('fixture', ROOT / 'tests/test_pcb_fab_workflow.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
workflow = fixture.workflow
sys.path.insert(0, str(ROOT / 'skills/pcb-fab-package/scripts'))
import inspect_slots  # noqa: E402

RESULTS = {}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# A. The root file-link defect: a link at captured/profile.yaml.
base = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-filelink-'))
proj = base / 'project'
scratch = proj / 'out/fab/supplier/captured'
scratch.mkdir(parents=True)
target = base / 'outside-profile.yaml'
link = scratch / 'profile.yaml'
link.symlink_to(target)
res = {'temporary_directory': str(base), 'target_absent_before': not target.exists(),
       'workflow_sha256': sha(workflow.__file__)}
try:
    workflow.profile_from_bytes(proj, fixture.PROFILE.read_bytes(), scratch)
    res['returned'] = True
except Exception as exc:  # noqa: BLE001
    res['returned'] = False
    res['exception'] = type(exc).__name__
    res['code'] = getattr(exc, 'code', None)
res['outside_file_created'] = target.exists()
res['link_preserved'] = link.is_symlink()
res['outside_sha256'] = sha(target) if target.exists() else None
RESULTS['leaf_link_profile'] = res

# B. check_manual: direct writes to manual-artifact.txt and manual-evidence.json.
base = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-manualwrites-'))
proj = base / 'project'
out = proj / 'out/fab/supplier'
out.mkdir(parents=True)
board = b'board bytes\n'
silk = b'silk bytes\n'
design = proj / 'out/fab/design'
(design / 'export').mkdir(parents=True)
(design / 'export/board-F_Silkscreen.gbr').write_bytes(silk)
art = b'artifact bytes\n'
rec = {"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1,
       "condition": "silk_line_min_short_text", "result": "pass", "procedure": "p",
       "artifact_path": "out/fab/manual/silk-check.txt",
       "artifact_sha256": hashlib.sha256(art).hexdigest(),
       "inputs": {"board_sha256": hashlib.sha256(board).hexdigest(),
                  "silk_gerber_sha256": hashlib.sha256(silk).hexdigest()},
       "reviewer": "r", "statement": "s"}
raw = (json.dumps(rec, indent=2, sort_keys=True) + "\n").encode()
target1 = base / 'outside-artifact.txt'
target2 = base / 'outside-evidence.json'
(out / 'manual-artifact.txt').symlink_to(target1)
(out / 'manual-evidence.json').symlink_to(target2)
res = {'temporary_directory': str(base),
       'targets_absent_before': not target1.exists() and not target2.exists()}
try:
    info, status, interp = workflow.check_manual(
        proj / 'out/fab/manual-record.json', raw, art, board, design, 'silk_line_min_short_text', out)
    res['returned'] = True
    res['status'] = status
except Exception as exc:  # noqa: BLE001
    res['returned'] = False
    res['exception'] = type(exc).__name__
    res['code'] = getattr(exc, 'code', None)
res['outside_artifact_created'] = target1.exists()
res['outside_evidence_created'] = target2.exists()
res['outside_artifact_sha256'] = sha(target1) if target1.exists() else None
res['outside_evidence_sha256'] = sha(target2) if target2.exists() else None
RESULTS['leaf_link_manual'] = res

# C. inspect_slots main: a link at the report path.
base = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-slots-'))
invp = base / 'inventory.json'
invp.write_text(json.dumps({'slots': []}))
drill = "M48\nMETRIC,TZ\nFMAT,2\n%\nG90\nG05\nM30\n"
pth = base / 'board-PTH.drl'
pth.write_text(drill)
npth = base / 'board-NPTH.drl'
npth.write_text(drill)
target = base / 'outside-slots.json'
report = base / 'slots.json'
report.symlink_to(target)
res = {'temporary_directory': str(base), 'target_absent_before': not target.exists()}
code = inspect_slots.main(['--board-inventory', str(invp), '--pth', str(pth),
                           '--npth', str(npth), '--report', str(report)])
res['exit'] = code
res['outside_created'] = target.exists()
res['outside_sha256'] = sha(target) if target.exists() else None
RESULTS['leaf_link_slots'] = res

# D. run_mask_worker freshness guard on an existing link at the report path.
base = pathlib.Path(tempfile.mkdtemp(prefix='b7-pi-mask-'))
target = base / 'outside-mask.json'
report = base / 'mask.json'
report.symlink_to(target)
code = workflow.fab.run_mask_worker(str(ROOT / 'skills/pcb-fab-package/supplier/pages/two-layer.html'),
                                    '6', str(report))
RESULTS['mask_report_guard'] = {'temporary_directory': str(base),
                                'target_absent_before': not target.exists(),
                                'exit': code, 'outside_created': target.exists()}

print(json.dumps(RESULTS, indent=2, sort_keys=True))
print('workflow_sha256_after=' + sha(workflow.__file__))
print('fab_sha256_after=' + sha(ROOT / 'skills/pcb-fab-package/scripts/fab.py'))