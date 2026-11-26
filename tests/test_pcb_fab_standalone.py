# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Run an installed skill while a filesystem boundary hides the repository."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import test_pcb_fab_acceptance as base

RUNNER = r'''
import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
skill = root / "installed/pcb-fab-package"
project = root / "project"
scripts = skill / "scripts"
sys.path.insert(0, str(scripts))
import fetch_sources
import review
import workflow

assert not Path("/mnt/storage/projects/cad-skills/AGENTS.md").exists()
assert Path("/mnt/storage/projects").is_dir()
profile_path = skill / "supplier/profiles/oshpark-two-layer.yaml"
profile = json.loads(profile_path.read_text())

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

commands = []
def run(label, args, expected=0):
    command = ["uv", "run", "--offline", "--quiet", str(scripts / "fab.py"), *args]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    (root / f"{label}.stdout").write_text(result.stdout)
    (root / f"{label}.stderr").write_text(result.stderr)
    commands.append({"label": label, "command": command, "exit": result.returncode,
                     "stdout_sha256": sha(result.stdout.encode()), "stderr_sha256": sha(result.stderr.encode())})
    assert result.returncode == expected, (label, result.returncode, result.stdout[-600:], result.stderr[-600:])

manifest = fetch_sources.load_manifest(skill / "sources.yaml")
source_map = {entry["url"]: root / "retrieval-input" / Path(entry["path"]).name
              for entry in manifest["sources"] if entry["distribution_decision"] == "exclude-full-copy"}
fetches = []
def offline_fetch(url):
    fetches.append(url)
    return source_map[url].read_bytes()

code, retrieval = fetch_sources.main(["--manifest", str(skill / "sources.yaml"), "--dest", str(skill)], fetch=offline_fetch)
assert code == 0 and len(fetches) == 6 and sum(row["written"] for row in retrieval["entries"]) == 6
(root / "retrieval.json").write_text(json.dumps(retrieval, indent=2) + "\n")
assert not list((skill / "supplier/pages").glob("*.headers"))
run("profile", ["profile", "--profile", str(profile_path)])
run("judge", ["judge", "--kind", "minimum", "--measured", "6", "--threshold", "6", "--unit", "mil"])
common = ["--project", str(project), "--profile", str(profile_path)]
run("design", ["design", *common])
board = project / "kicad/board.kicad_pcb"
silk = project / "out/fab/design/export/board-F_Silkscreen.gbr"
artifact = project / "out/fab/manual/artifact.txt"
artifact.parent.mkdir(parents=True)
artifact.write_text("Owned test evidence. No physical result is measured.\n")
manual = project / "out/fab/manual.json"
manual.write_text(json.dumps({"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1,
    "condition": "silk_line_min_short_text", "result": "pass", "procedure": "Use the owned fixture expectation.",
    "artifact_path": artifact.relative_to(project).as_posix(), "artifact_sha256": sha(artifact.read_bytes()),
    "inputs": {"board_sha256": sha(board.read_bytes()), "silk_gerber_sha256": sha(silk.read_bytes())},
    "reviewer": "Owned fixture reviewer", "statement": "This is test evidence."}, indent=2) + "\n")
run("supplier", ["supplier", *common, "--manual", str(manual)])
stored = skill / "supplier/pages/two-layer.html"
live = project / "out/fab/source-review/live/two-layer.html"
live.parent.mkdir(parents=True)
live.write_bytes(stored.read_bytes())
obs = {"schema_id": review.OBS_SCHEMA, "schema_version": 1, "release_id": "standalone-1",
       "profile_sha256": profile["content_sha256"], "pages": [{"page_id": "two-layer",
       "source_url": profile["extensions"]["evidence_pages"]["two-layer"]["source_url"],
       "stored_path": "supplier/pages/two-layer.html", "stored_sha256": sha(stored.read_bytes()),
       "live_path": live.relative_to(project).as_posix(), "live_sha256": sha(live.read_bytes()),
       "retrieved": "2026-11-14"}], "observations": [
       {"key": key, "observed_value": value, "observed_unit": unit, "observed_condition": "Owned offline observation.",
        "source_url": url, "reviewer_reading": "This is an offline fixture observation."}
       for key, (value, unit, url) in review.fact_items(profile).items()],
       "reviewer": "Owned fixture reviewer", "statement": "This trial makes no current supplier review claim."}
observations = project / "offline-observations.json"
observations.write_text(json.dumps(obs, indent=2) + "\n")
review_path = project / "out/fab/source-review/REVIEW.json"
run("review-source", ["review-source", *common, "--release", "standalone-1", "--observations", str(observations),
    "--reviewer", "Owned fixture reviewer", "--out", str(review_path)])
review_hash = sha(review_path.read_bytes())
run("review-gate", ["review-gate", *common, "--release", "standalone-1", "--review", str(review_path), "--expect-sha256", review_hash])
destination = project / "out/fab/packages/standalone-1"
run("package", ["package", *common, "--release", "standalone-1", "--review", str(review_path),
    "--review-sha256", review_hash, "--dest", str(destination)])
package = json.loads((destination / "manifest.json").read_text())
assert package["status"] == "qualified"
code, report = workflow.VAL.build_report([str(destination / "manifest.json")], workflow.SCHEMAS, project, destination)
assert code == 0, report
for name in ("fab", "workflow", "review", "validate", "project_io", "fetch_sources"):
    module = sys.modules[name]
    assert Path(module.__file__).resolve().is_relative_to(skill.resolve()), (name, module.__file__)
(root / "result.json").write_text(json.dumps({"commands": commands, "validator": report,
    "runtime": workflow.runtime_identity((project / "toolchain.lock.json").read_bytes()),
    "package_status": package["status"], "output_count": len(package["outputs"]),
    "scope": "Offline owned fixture. No physical result or current supplier review is measured.",
    "repository_hidden": True, "retrieval": "Five project-authored fixture pages through an offline transport."}, indent=2) + "\n")
print(json.dumps({"commands": len(commands), "validator_exit": code, "repository_hidden": True, "package_status": package["status"]}))
'''


def main():
    root = Path(tempfile.mkdtemp(prefix="fab-standalone-root-"))
    skill = root / "installed/pcb-fab-package"
    shutil.copytree(base.SKILL, skill, ignore=shutil.ignore_patterns("__pycache__", "pages"))
    (skill / "supplier/pages").mkdir()
    evidence = root / "retrieval-input"
    evidence.mkdir()
    for page in (base.SKILL / "supplier/pages").glob("*.html"):
        shutil.copy2(page, evidence / page.name)
    base.fresh_project(root, "project")
    runner = root / "trial.py"
    header = Path(__file__).read_text().split('"""', 1)[0]
    runner.write_text(header + RUNNER.lstrip())
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["CONTAINER_HOST"] = "unix:///run/user/1000/podman/podman.sock"
    command = ["bwrap", "--bind", "/", "/", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/mnt/storage/projects", "--chdir", str(root), "--",
               "uv", "run", "--offline", str(runner)]
    result = subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True)
    (root / "boundary.stdout").write_text(result.stdout)
    (root / "boundary.stderr").write_text(result.stderr)
    (root / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    print(json.dumps({"root": str(root), "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
