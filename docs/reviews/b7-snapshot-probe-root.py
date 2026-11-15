# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure the source-copy and hash order on temporary files. Do not run KiCad."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/pcb-fab-package/scripts"))
import workflow

project = Path(tempfile.mkdtemp(prefix="b7-snapshot-root-"))
(project / "kicad").mkdir()
for relative in workflow.SOURCE_FILES:
    (project / relative).write_bytes(b"original bytes\n")
board = project / "kicad/board.kicad_pcb"
stage = project / "out/fab/design/work"
original_copy = workflow.shutil.copy2


def copy_then_change(source, destination, *args, **kwargs):
    result = original_copy(source, destination, *args, **kwargs)
    if Path(source) == board:
        board.write_bytes(b"changed source bytes\n")
    return result


workflow.shutil.copy2 = copy_then_change
try:
    recorded = workflow.stage_project(project, stage)
finally:
    workflow.shutil.copy2 = original_copy

after = workflow.source_hashes(project)
staged_hash = hashlib.sha256((stage / "kicad/board.kicad_pcb").read_bytes()).hexdigest()
result = {
    "workflow_sha256": hashlib.sha256(Path(workflow.__file__).read_bytes()).hexdigest(),
    "temporary_project": str(project),
    "recorded_board_sha256": recorded["kicad/board.kicad_pcb"],
    "staged_board_sha256": staged_hash,
    "before_equals_after": recorded == after,
    "recorded_hash_matches_staged_bytes": recorded["kicad/board.kicad_pcb"] == staged_hash,
    "scope": "stage_project only; no KiCad run or package qualification claim",
}
output = project / "probe.json"
output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
