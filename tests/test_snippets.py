# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery"]
# ///
"""Execute every ```python code block in the skills' Markdown files.

  uv run tests/test_snippets.py               # all skills
  uv run tests/test_snippets.py -k recipes    # only files whose path contains 'recipes'
  uv run tests/test_snippets.py -v            # list every block

Rules:
  * Each block runs in a fresh namespace inside a temp directory.
  * A block whose first line contains `# notest` is skipped (fragments, CLI-only).
  * If the block defines `result`, it must be a valid shape/workplane/assembly
    with at least one solid or face, unless the block is marked `# noresult`.
  * `show_object` and `debug` are provided as no-ops.
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
