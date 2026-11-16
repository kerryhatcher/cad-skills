# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Find footprint changes that `identity.py` does not read (U3 supplement).

  uv run scripts/u3_unread_audit.py BEFORE.kicad_pcb AFTER.kicad_pcb

`identity.py` reads the footprint fields reference, value, library ID, path, layer, position, properties and pads.
It does not read the other child forms of a footprint, for example `attr` (smd, through_hole, dnp,
exclude_from_bom, exclude_from_pos_files), `fp_line` and `fp_text`. This audit compares each child form of
each footprint that is in both boards (the same footprint UUID). It ignores the `uuid` form of a child form,
because KiCad can make new child UUIDs. It reports each child form kind that changed.

Exit status: 0 no unread change, 1 one or more unread changes, 2 incorrect input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identity  # noqa: E402
import sexp  # noqa: E402

READ = {"property", "pad", "path", "layer", "at", "uuid"}


def strip_uuid(node):
    if isinstance(node, list):
        return [strip_uuid(n) for n in node if not (isinstance(n, list) and n and n[0] == "uuid")]
    return node


def children(fp) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for child in fp[2:]:
        if isinstance(child, list) and child and str(child[0]) not in READ:
            out.setdefault(str(child[0]), []).append(identity.dump(strip_uuid(child)))
    return {k: sorted(v) for k, v in out.items()}


def footprints(text: str) -> dict[str, tuple[str, dict]]:
    out = {}
    for node in sexp.parse(text)[1:]:
        if isinstance(node, list) and node and node[0] == "footprint":
            uid = identity.scalar(node, "uuid")
            ref = next((str(p[2]) for p in sexp.children(node, "property") if str(p[1]) == "Reference"), None)
            out[uid] = (ref, children(node))
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("before")
    parser.add_argument("after")
    args = parser.parse_args(argv)
    try:
        old, new = footprints(Path(args.before).read_text()), footprints(Path(args.after).read_text())
    except (OSError, ValueError, IndexError) as err:
        print(json.dumps({"error": f"u3_unread_audit: cannot read a board ({type(err).__name__}: {err}). Give two KiCad boards."}))
        return 2
    found = []
    for uid in sorted(set(old) & set(new)):
        (ref, a), (_, b) = old[uid], new[uid]
        for kind in sorted(set(a) | set(b)):
            if a.get(kind) != b.get(kind):
                entry = {"ref": ref, "form": kind}
                if kind == "attr":
                    entry["before"], entry["after"] = a.get(kind), b.get(kind)
                found.append(entry)
    print(json.dumps({"footprints_compared": len(set(old) & set(new)), "unread_changes": found}, indent=2))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
