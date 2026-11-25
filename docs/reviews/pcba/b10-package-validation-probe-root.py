# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Compare package publication with the full copied validator."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import yaml

root = Path(__file__).resolve().parents[3]
project = Path(tempfile.mkdtemp(prefix="b10-validation-root-")) / "project"
shutil.copytree(root / "tests/fixtures/pcba-design/project", project)
board_path = project / "board.yaml"
board = yaml.safe_load(board_path.read_text())
board["restrictions"] = []
board_path.write_text(yaml.safe_dump(board, sort_keys=False))
package = project / "out/pcba/packages/root-probe"
commands = [
    ["uv", "run", str(root / "skills/pcba-design/scripts/pcba.py"), "package",
     "--project", str(project), "--board", "board.kicad_pcb", "--variant", "base",
     "--as-of", "2026-11-15", "--package-id", "root-probe"],
    ["uv", "run", str(root / "skills/pcba-design/contracts/validate.py"),
     "--project", str(project), "--package", str(package), "--json"],
]
results = []
for command in commands:
    proc = subprocess.run(command, capture_output=True, text=True)
    try:
        output = json.loads(proc.stdout)
    except ValueError:
        output = proc.stdout
    results.append({"command": command, "exit": proc.returncode,
                    "stdout": output, "stderr": proc.stderr})
print(json.dumps({"project": str(project), "results": results}, indent=2))
