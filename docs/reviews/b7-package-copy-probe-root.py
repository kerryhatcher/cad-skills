# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure package-copy binding on a temporary test project. Do not change product files."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fab_fixture", ROOT / "tests/test_pcb_fab_workflow.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
workflow = fixture.workflow
tmp = Path(tempfile.mkdtemp(prefix="b7-copy-root-"))
project = fixture.fresh_project(tmp, "project")
profile_path = fixture.PROFILE
profile = json.loads(profile_path.read_bytes())
design = fixture.run_fab("design", "--project", str(project), "--profile", str(profile_path))
if design.returncode:
    raise RuntimeError((design.returncode, design.stderr))
design_dir = project / "out/fab/design"
supplier_dir = project / "out/fab/supplier"
review_path = project / "out/fab/source-review/REVIEW.json"
observations = fixture.observations(project, profile)
review_record = fixture.review.build_review(observations, profile, profile_path.read_bytes(), "trial-1", project)
review_path.write_text(json.dumps(review_record, sort_keys=True, indent=2) + "\n")
(review_path.parent / "observations.json").write_bytes(observations)
artifact = project / "out/fab/manual/silk-check.txt"
artifact.parent.mkdir(parents=True)
artifact.write_text("Synthetic evidence for the root package-copy regression.\n")
manual = project / "out/fab/manual-record.json"
manual.write_text(json.dumps({
    "schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1,
    "condition": "silk_line_min_short_text", "result": "pass",
    "procedure": "Synthetic test fixture. No production qualification claim.",
    "artifact_path": "out/fab/manual/silk-check.txt", "artifact_sha256": fixture.sha(artifact.read_bytes()),
    "inputs": {"board_sha256": fixture.sha((project / "kicad/board.kicad_pcb").read_bytes()),
               "silk_gerber_sha256": fixture.sha((design_dir / "export/board-F_Silkscreen.gbr").read_bytes())},
    "reviewer": "Root test fixture", "statement": "Synthetic evidence for this regression only."
}) + "\n")
supplier = fixture.run_fab("supplier", "--project", str(project), "--profile", str(profile_path), "--manual", str(manual))
if supplier.returncode:
    raise RuntimeError((supplier.returncode, supplier.stdout, supplier.stderr))
review_hash = fixture.sha(review_path.read_bytes())
baseline_code, baseline_manifest = workflow.package(project, profile_path, "trial-1", review_path,
    project / "out/fab/packages/baseline", design_dir, supplier_dir, review_hash)
original_copy = workflow.shutil.copy2
target = design_dir / "export/board-F_Cu.gbr"
original_bytes = target.read_bytes()
injected_bytes = b"deliberately invalid Gerber for the root regression\n"
injection_count = 0


def changed_copy(source, destination, *args, **kwargs):
    global injection_count
    if Path(source) != target:
        return original_copy(source, destination, *args, **kwargs)
    injection_count += 1
    target.write_bytes(injected_bytes)
    try:
        return original_copy(source, destination, *args, **kwargs)
    finally:
        target.write_bytes(original_bytes)


workflow.shutil.copy2 = changed_copy
destination = project / "out/fab/packages/changed-copy"
try:
    code, manifest = workflow.package(project, profile_path, "trial-1", review_path,
        destination, design_dir, supplier_dir, review_hash)
finally:
    workflow.shutil.copy2 = original_copy
published = destination / "gerber/board-F_Cu.gbr"
result = {
    "workflow_sha256": fixture.sha(Path(workflow.__file__).read_bytes()),
    "temporary_project": str(project), "baseline_exit": baseline_code,
    "baseline_status": baseline_manifest["status"], "injection_count": injection_count,
    "changed_copy_exit": code, "changed_copy_status": manifest["status"],
    "reasons": manifest["reasons"], "source_restored": target.read_bytes() == original_bytes,
    "published_injected_bytes": published.is_file() and published.read_bytes() == injected_bytes,
    "source_sha256": hashlib.sha256(original_bytes).hexdigest(),
    "published_sha256": fixture.sha(published.read_bytes()) if published.is_file() else None,
}
(tmp / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
