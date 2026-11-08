# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery"]
# ///
"""Run each ```python code block in the Markdown files of the skills.

  uv run tests/test_snippets.py               # all skills
  uv run tests/test_snippets.py -k recipes    # only files with 'recipes' in their path
  uv run tests/test_snippets.py -v            # show each block

Rules:
  * Each block runs in a new namespace in a temporary directory.
  * The test does not run a block that has `# notest` in its first line (parts of code, CLI only).
  * If the block sets `result`, it must be a valid shape, workplane or assembly
    with one solid or face or more. Exception: the block has the mark `# noresult`.
  * `show_object` and `debug` are functions that do nothing.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import time
import traceback
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r"^```python[^\n]*\n(.*?)^```", re.S | re.M)


def check_result(res) -> str | None:
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


def main(argv):
    verbose = "-v" in argv
    key = argv[argv.index("-k") + 1] if "-k" in argv else ""
    files = sorted(p for p in (ROOT / "skills").rglob("*.md") if key in str(p))
    failures = 0
    total = skipped = 0
    for md in files:
        text = md.read_text()
        for m in BLOCK.finditer(text):
            code = m.group(1)
            line = text[: m.start()].count("\n") + 1
            label = f"{md.relative_to(ROOT)}:{line}"
            first = code.splitlines()[0] if code.strip() else ""
            if "# notest" in first:
                skipped += 1
                continue
            total += 1
            ns = {"__name__": "__snippet__", "show_object": lambda *a, **k: None,
                  "debug": lambda *a, **k: None}
            cwd = os.getcwd()
            t0 = time.time()
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                try:
                    exec(compile(code, label, "exec"), ns)
                    err = None if "# noresult" in first else (
                        check_result(ns["result"]) if "result" in ns else None)
                except Exception:
                    err = traceback.format_exc(limit=3)
                finally:
                    os.chdir(cwd)
            dt = time.time() - t0
            if err:
                failures += 1
                print(f"FAIL {label}\n{err}")
            elif verbose:
                print(f"ok   {label} ({dt:.1f}s)")
    print(f"\n{total - failures}/{total} blocks passed, {skipped} skipped")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
