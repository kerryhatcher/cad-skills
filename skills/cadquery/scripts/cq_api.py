#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery"]
# ///
"""Show the CadQuery API of the *installed* version (signatures and docstrings).

Use this tool. Do not guess parameter names. The CadQuery API changes between
releases, and the online documentation is for the development version.

  uv run scripts/cq_api.py Workplane              # list of methods with one-line summaries
  uv run scripts/cq_api.py Workplane.hole         # full signature and docstring
  uv run scripts/cq_api.py Sketch.slot Assembly.constrain
  uv run scripts/cq_api.py func                   # cadquery.func free functions
  uv run scripts/cq_api.py func.sweep
  uv run scripts/cq_api.py --search fillet        # find names that contain 'fillet'
  uv run scripts/cq_api.py --version
"""

from __future__ import annotations

import inspect
import re
import sys

import cadquery as cq
import cadquery.func as func

NAMESPACES = {
    "cq": cq,
    "func": func,
    "selectors": cq.selectors,
    "exporters": cq.exporters,
    "importers": cq.importers,
}
CLASSES = ["Workplane", "Sketch", "Assembly", "Shape", "Solid", "Face", "Wire", "Edge",
           "Vertex", "Compound", "Shell", "Vector", "Plane", "Location", "Color", "Matrix",
           "BoundBox"]


def resolve(path: str):
    parts = path.split(".")
    head = parts[0]
    if head in NAMESPACES:
        obj = NAMESPACES[head]
    elif hasattr(cq, head):
        obj = getattr(cq, head)
    elif hasattr(func, head):
        obj = getattr(func, head)
    else:
        raise AttributeError(f"unknown name {head!r}")
    for p in parts[1:]:
        # First look in the class __dict__ (MRO). Then multimethod objects stay
        # complete and do not become one bound function.
        raw = None
        if inspect.isclass(obj):
            for klass in obj.__mro__:
                if p in klass.__dict__:
                    raw = klass.__dict__[p]
                    break
        obj = raw if isinstance(raw, dict) else getattr(obj, p)
    return obj


def tidy(text: str) -> str:
    """Make long type annotations shorter, so that the signatures are easy to read."""
    text = re.sub(r"\bcadquery\.(occ_impl\.)?(\w+\.)*(?=[A-Z])", "", text)
    text = re.sub(r"\bOCP\.(\w+\.)*(?=[A-Z])", "", text)
    text = text.replace("Union[int, float]", "Real").replace("~T", "T")
    return text


def summary(obj) -> str:
    doc = inspect.getdoc(obj) or ""
    return doc.strip().splitlines()[0] if doc.strip() else ""


def sig(obj) -> str:
    # Multimethod callables have many signatures.
    if isinstance(obj, dict) and obj:  # Multimethod: one entry for each overload.
        lines = []
        for f in obj.values():
            try:
                lines.append(f"  {tidy(str(inspect.signature(f)))}")
            except (TypeError, ValueError):
                pass
        if lines:
            return "Overloads (give the arguments by position, because keywords stop the dispatch):\n" + \
                "\n".join(lines)
    try:
        return f"  {tidy(str(inspect.signature(obj)))}"
    except (TypeError, ValueError):
        return "  (signature unavailable)"


def members(obj):
    out = []
    for name in sorted(dir(obj)):
        if name.startswith("_"):
            continue
        try:
            m = getattr(obj, name)
        except Exception:
            continue
        if callable(m):
            out.append((name, m))
    return out


def show(path: str):
    obj = resolve(path)
    if inspect.isclass(obj) or inspect.ismodule(obj):
        print(f"# {path}  ({summary(obj)})")
        for name, m in members(obj):
            print(f"  {name:<24} {summary(m)[:100]}")
    else:
        print(f"# {path}")
        print(sig(obj))
        print()
        print(tidy(inspect.getdoc(obj) or "(no docstring)"))
    print()


def search(term: str):
    term = term.lower()
    seen = set()
    for label, ns in [("cq", cq), ("func", func)] + [(c, getattr(cq, c)) for c in CLASSES]:
        for name, m in members(ns):
            if term in name.lower():
                key = f"{label}.{name}"
                if key not in seen:
                    seen.add(key)
                    print(f"{key:<36} {summary(m)[:90]}")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    if argv[0] == "--version":
        print(cq.__version__)
        return
    if argv[0] == "--search":
        for t in argv[1:]:
            search(t)
        return
    for a in argv:
        try:
            show(a)
        except AttributeError as e:
            print(f"{a}: {e}. Try --search.")


if __name__ == "__main__":
    main(sys.argv[1:])
