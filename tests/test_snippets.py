# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery"]
# ///
"""Run each ```python code block in the Markdown files of the skills.

  uv run tests/test_snippets.py               # all skills
  uv run tests/test_snippets.py -k recipes    # only files with 'recipes' in their path
  uv run tests/test_snippets.py -v            # show each block
  uv run tests/test_snippets.py --list-envs   # show the routing table
  uv run tests/test_snippets.py --dry-run     # show the environment of each block, run nothing

Rules:
  * `tests/snippet_envs.json` maps each skill directory to an environment.
    A skill with no entry fails (`snippet.unrouted`).
  * An environment with `command: null` runs the block in this process.
    An environment with a command list runs the block in a subprocess.
    The test sends {"label", "code"} on standard input and reads {"status", "stdout", "stderr"}.
    The worker must exit with code 0. A nonzero exit or a signal fails the block (`snippet.worker_failed`).
  * An environment with `available: false` fails each block (`snippet.env_unavailable`).
  * Each block runs in a new namespace in a temporary directory.
  * The test does not run a block that has `# notest: <reason>` in its first line.
    A `# notest` mark with no reason fails (`snippet.notest_reason`).
  * If the block sets `result`, it must be a valid shape, workplane or assembly
    with one solid or face or more. Exception: the block has the mark `# noresult`.
  * `show_object` and `debug` are functions that do nothing.
  * The test compares the bytes of the skill source files before and after the blocks of the skill.
    A change fails (`snippet.source_changed`).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENVS_PATH = Path(__file__).resolve().parent / "snippet_envs.json"
BLOCK = re.compile(r"^```python[^\n]*\n(.*?)^```", re.S | re.M)


def check_result(res) -> str | None:
    import cadquery as cq  # Imported here, so that routing tests do not need CadQuery.

    if isinstance(res, cq.Assembly):
        shp = res.toCompound()
    elif isinstance(res, cq.Workplane):
        vals = [v for v in res.vals() if isinstance(v, cq.Shape)]
        if not vals:
            return "result Workplane holds no shapes"
        shp = cq.Compound.makeCompound(vals)
    elif isinstance(res, cq.Sketch):
        return None
    elif isinstance(res, cq.Shape):
        shp = res
    else:
        return None
    if not shp.isValid():
        return "result is not a valid shape"
    if not shp.Solids() and not shp.Faces() and not shp.Edges():
        return "result is empty"
    return None


def load_table(path: Path = ENVS_PATH) -> dict:
    return json.loads(path.read_text())


def source_digest(skill_dir: Path) -> str:
    """One hash for the bytes and the relative names of all files of a skill."""
    digest = hashlib.sha256()
    for path in sorted(p for p in skill_dir.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(skill_dir)).encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def run_in_process(code: str, label: str, first: str) -> str | None:
    ns = {"__name__": "__snippet__", "show_object": lambda *a, **k: None, "debug": lambda *a, **k: None}
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            exec(compile(code, label, "exec"), ns)
            return None if "# noresult" in first else (check_result(ns["result"]) if "result" in ns else None)
        except Exception:
            return traceback.format_exc(limit=3)
        finally:
            os.chdir(cwd)


def run_in_worker(command: list, code: str, label: str, timeout: float) -> tuple[str | None, str | None]:
    """Return (error text, failure code). Both are None if the block passes."""
    with tempfile.TemporaryDirectory() as tmp:
        try:
            r = subprocess.run(command, input=json.dumps({"label": label, "code": code}), capture_output=True,
                               text=True, cwd=tmp, timeout=timeout)
        except subprocess.TimeoutExpired:
            return f"The worker did not finish in {timeout} s.", "snippet.timeout"
        except OSError as err:
            return f"The worker did not start: {err}", "snippet.env_unavailable"
    if r.returncode != 0:
        message = f"Signal {-r.returncode} stopped the worker." if r.returncode < 0 else f"The worker exited with code {r.returncode}."
        return f"{message} {r.stderr[-500:]}".strip(), "snippet.worker_failed"
    try:
        answer = json.loads(r.stdout)
        status = answer["status"]
    except (ValueError, KeyError, TypeError):
        return f"The worker output is not valid JSON ({r.stdout[:80]!r}).", "snippet.worker_output"
    if status != "ok":
        return str(answer.get("stderr") or answer.get("stdout") or status)[-2000:], "snippet.block_failed"
    return None, None


def run_suite(skills_root: Path, table: dict, key: str = "", verbose: bool = False, dry_run: bool = False,
              timeout: float = 120.0, out=print) -> dict:
    """Run or list the blocks. Return {"failures": [...], "counts": {...}, "skipped": [...]}."""
    failures, skipped, counts = [], [], {}

    def fail(code, label, message):
        failures.append({"code": code, "label": label, "message": message})
        out(f"FAIL {label} [{code}]\n{message}")

    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        files = sorted(p for p in skill_dir.rglob("*.md") if key in str(p))
        env_name = table["skills"].get(skill_dir.name)
        if env_name is None:
            fail("snippet.unrouted", skill_dir.name, "The skill directory has no entry in the routing table.")
            continue
        env = table["envs"].get(env_name)
        if env is None:
            fail("snippet.env_missing", skill_dir.name, f"The environment {env_name!r} is not in the routing table.")
            continue
        before = None if dry_run else source_digest(skill_dir)
        for md in files:
            text = md.read_text()
            for m in BLOCK.finditer(text):
                code = m.group(1)
                line = text[: m.start()].count("\n") + 1
                label = f"{md.relative_to(skills_root.parent)}:{line}"
                first = code.splitlines()[0] if code.strip() else ""
                if "# notest" in first:
                    reason = first.split("# notest", 1)[1].lstrip(": ").strip()
                    if not reason:
                        fail("snippet.notest_reason", label, "The `# notest` mark needs a reason: `# notest: <reason>`.")
                    else:
                        skipped.append({"label": label, "reason": reason})
                        if verbose or dry_run:
                            out(f"skip {label} ({reason})")
                    continue
                counts[env_name] = counts.get(env_name, 0) + 1
                if env.get("available", True) is False:
                    fail("snippet.env_unavailable", label, f"The environment {env_name!r} is not available.")
                    continue
                if dry_run:
                    out(f"run  {label} [{env_name}]")
                    continue
                t0 = time.time()
                if env.get("command"):
                    err, code_name = run_in_worker(env["command"], code, label, timeout)
                else:
                    err, code_name = run_in_process(code, label, first), "snippet.block_failed"
                if err:
                    fail(code_name or "snippet.block_failed", label, err)
                elif verbose:
                    out(f"ok   {label} [{env_name}] ({time.time() - t0:.1f}s)")
        if not dry_run and source_digest(skill_dir) != before:
            fail("snippet.source_changed", skill_dir.name, "A block changed a source file of the skill.")
    return {"failures": failures, "counts": counts, "skipped": skipped}


def main(argv):
    verbose = "-v" in argv
    key = argv[argv.index("-k") + 1] if "-k" in argv else ""
    table = load_table()
    if "--list-envs" in argv:
        for name, env in table["envs"].items():
            kind = "unavailable" if env.get("available", True) is False else ("worker" if env.get("command") else "this process")
            print(f"{name}: {kind}")
        for skill, env in table["skills"].items():
            print(f"  {skill} -> {env}")
        return 0
    dry = "--dry-run" in argv
    result = run_suite(ROOT / "skills", table, key, verbose, dry)
    failures, counts, skipped = result["failures"], result["counts"], result["skipped"]
    total = sum(counts.values())
    label = "blocks listed" if dry else "blocks passed"
    ok = total - sum(1 for f in failures if f["code"] != "snippet.unrouted" and f["code"] != "snippet.env_missing"
                     and f["code"] != "snippet.notest_reason" and f["code"] != "snippet.source_changed")
    print(f"\n{ok}/{total} {label}, {len(skipped)} skipped")
    for name, number in sorted(counts.items()):
        print(f"  environment {name}: {number} blocks")
    for item in skipped:
        print(f"  skipped {item['label']}: {item['reason']}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
