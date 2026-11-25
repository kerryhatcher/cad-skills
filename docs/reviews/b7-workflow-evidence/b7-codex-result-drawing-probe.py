# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure a changed supplier result and a drawing link."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "tests"))
import test_pcb_fab_workflow as fixture

temporary = Path(tempfile.mkdtemp(prefix="b7-codex-result-drawing-"))
project, review_path, review_hash = fixture.prepared(temporary, "supplier")
supplier_dir = project / "out/fab/supplier"
result_path = supplier_dir / "supplier-result.json"
binding_path = supplier_dir / "supplier-binding.json"
result = json.loads(result_path.read_bytes())
original_result_hash = hashlib.sha256(result_path.read_bytes()).hexdigest()
row = next(item for item in result["rows"] if item["mandatory"])
row["status"] = "fail"
result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
result_hash = hashlib.sha256(result_path.read_bytes()).hexdigest()
binding_hash = hashlib.sha256(binding_path.read_bytes()).hexdigest()
destination = project / "out/fab/packages/result-tamper"
code, manifest = fixture.package_in_process(project, review_path, review_hash, destination)
published_result = destination / "reports/supplier-result.json"

facts = {
    "release_id": "probe",
    "unit": "mm",
    "overall_width_mm": 10,
    "overall_height_mm": 10,
    "holes": {"count": 0, "diameters_mm": []},
    "copper_layers": ["F.Cu", "B.Cu"],
    "stackup": "2-layer",
    "profile": {"profile": "probe", "source_page": "stored page", "min_trace_mil": 5,
                "min_space_mil": 5, "min_drill_mil": 5, "mask_web_min_mil": 5,
                "substrate": "FR-4", "finished_thickness_mm": 1.6, "copper": "1 oz"},
    "board_sha256": "0" * 64,
    "profile_sha256": "1" * 64,
}
facts_path = temporary / "facts.json"
facts_path.write_text(json.dumps(facts))
outside = temporary / "outside.pdf"
outside_before = b"outside before the command\n"
outside.write_bytes(outside_before)
outside_before_hash = hashlib.sha256(outside_before).hexdigest()
link = temporary / "drawing.pdf"
link.symlink_to(outside)
drawing_exit = fixture.fab.main(["drawing", "--facts", str(facts_path), "--out", str(link)])
print(json.dumps({
    "package_exit": code,
    "package_status": manifest["status"],
    "tampered_row_status": row["status"],
    "supplier_binding_unchanged": hashlib.sha256(binding_path.read_bytes()).hexdigest() == binding_hash,
    "supplier_result_before_hash": original_result_hash,
    "published_result_hash": hashlib.sha256(published_result.read_bytes()).hexdigest(),
    "manifest_result_hash": next(item["sha256"] for item in manifest["outputs"]
                                  if item["path"] == "reports/supplier-result.json"),
    "drawing_exit": drawing_exit,
    "drawing_link_preserved": link.is_symlink(),
    "outside_pdf_changed": outside.read_bytes().startswith(b"%PDF-1.4"),
    "outside_pdf_before_sha256": outside_before_hash,
    "outside_pdf_sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
    "supplier_result_sha256": result_hash,
}, sort_keys=True))
