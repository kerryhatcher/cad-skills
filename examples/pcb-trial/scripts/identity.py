# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Identity reader for KiCad `.kicad_pcb` text. It does not import `pcbnew`.

  uv run scripts/identity.py snapshot BOARD.kicad_pcb -o before.json
  uv run scripts/identity.py compare before.json after.json --expect expected/EDIT.json [--json]

A snapshot holds, for each object class, the fields that decide identity:
  footprint  UUID, reference, value, library ID, schematic path, layer, position, rotation, other properties,
             and each pad (number, UUID, position, rotation, net name)
  segment / arc / via  UUID, net name, geometry, layer
  zone       UUID, net name, layers, name, polygon definition (the filled polygons are volatile and ignored)
  graphic    UUID and normalized text of each `gr_*` item
The reader lists the top-level forms that it handles and the forms that it ignores on purpose.
A form in neither list stops the reader with exit 3 (`identity.unparsed_class`). The reader never reports
identity as kept for a class that it does not read.

`compare` has no blanket exception. `--expect` lists the exact differences that the edit may cause. The
comparison fails if an observed difference is not listed, and it fails if a listed difference does not occur.
A difference is (op, class, ident, field, before, after). The ident of a footprint is its reference, and of
a routing object its UUID. A footprint that is only in one snapshot is `added` or `removed`.

An added footprint lists its reference, library ID, value and pad nets. The reader stops with exit 2 when two
objects of one class have the same UUID, when a handled object has no UUID, and when the expectation lists
the same difference two times.

Exit status: 0 the differences equal the expected ones, 1 they differ, 2 incorrect arguments or input,
3 an unparsed top-level form.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sexp  # noqa: E402

HANDLED = {"footprint", "segment", "arc", "via", "zone"}
GRAPHIC_PREFIX = "gr_"
# Forms that carry no identity of a board object, or whose bytes change without a design change.
IGNORED = {"version", "generator", "generator_version", "general", "paper", "title_block", "layers", "setup", "net",
           "embedded_fonts", "embedded_files", "group", "generated", "property", "image", "target", "dimension", "teardrops"}


class Unparsed(Exception):
    pass


class InputProblem(ValueError):
    """The input board or the expectation is not usable. The command exits with status 2."""


def put(table: dict, key, value, cls: str) -> None:
    """Add an object to its table. A missing or repeated UUID stops the reader, so no object can hide."""
    if key is None:
        raise InputProblem(f"identity.missing_uuid: a {cls} has no UUID")
    if key in table:
        raise InputProblem(f"identity.duplicate_uuid: the {cls} UUID {key} occurs two times")
    table[key] = value


def num(x):
    f = float(x)
    return int(f) if f == int(f) else round(f, 6)


def scalar(node, name, default=None):
    item = sexp.child(node, name)
    return str(item[1]) if item is not None and len(item) > 1 else default


def pos(node, name="at"):
    item = sexp.child(node, name)
    if item is None:
        return None
    vals = [num(v) for v in item[1:]]
    return vals + [0] * (3 - len(vals)) if name == "at" else vals


def dump(node) -> str:
    if isinstance(node, list):
        return "(" + " ".join(dump(n) for n in node) + ")"
    return json.dumps(str(node)) if isinstance(node, sexp.Quoted) else str(node)


def footprint(node):
    props, pads = {}, {}
    for prop in sexp.children(node, "property"):
        if len(prop) >= 3:
            props[str(prop[1])] = str(prop[2])
    for pad in sexp.children(node, "pad"):
        number = str(pad[1])
        if number in pads:
            number = f"{number}#{len(pads)}"
        pads[number] = {"uuid": scalar(pad, "uuid"), "at": pos(pad), "net": scalar(pad, "net")}
    ref = props.pop("Reference", None)
    value = props.pop("Value", None)
    return {"reference": ref, "value": value, "lib_id": str(node[1]), "path": scalar(node, "path"), "layer": scalar(node, "layer"),
            "at": pos(node), "properties": props, "pads": pads}


def snapshot_text(text: str) -> dict:
    tree = sexp.parse(text)
    if not tree or tree[0] != "kicad_pcb":
        raise Unparsed("the file is not a kicad_pcb")
    snap = {"footprints": {}, "segments": {}, "arcs": {}, "vias": {}, "zones": {}, "graphics": {}, "forms_seen": []}
    for node in tree[1:]:
        if not isinstance(node, list) or not node:
            continue
        name = str(node[0])
        snap["forms_seen"].append(name)
        if name == "footprint":
            put(snap["footprints"], scalar(node, "uuid"), footprint(node), "footprint")
        elif name in ("segment", "arc"):
            geometry = {k: pos(node, k) for k in ("start", "mid", "end") if sexp.child(node, k) is not None}
            put(snap[name + "s"], scalar(node, "uuid"), {"net": scalar(node, "net"), "layer": scalar(node, "layer"), "width": scalar(node, "width"), **geometry}, name)
        elif name == "via":
            put(snap["vias"], scalar(node, "uuid"), {"net": scalar(node, "net"), "at": pos(node), "size": scalar(node, "size"), "drill": scalar(node, "drill"),
                                                   "layers": dump(sexp.child(node, "layers"))}, "via")
        elif name == "zone":
            keep = [c for c in node if not (isinstance(c, list) and c and c[0] in ("filled_polygon", "fill_segments", "filled_areas_thickness"))]
            polygon = sexp.child(node, "polygon")
            put(snap["zones"], scalar(node, "uuid"), {"net": scalar(node, "net"), "layers": dump(sexp.child(node, "layers") or sexp.child(node, "layer")),
                                                    "name": scalar(node, "name"), "polygon": dump(polygon) if polygon else None, "definition": dump(keep)}, "zone")
        elif name.startswith(GRAPHIC_PREFIX):
            put(snap["graphics"], scalar(node, "uuid") or dump(node), {"class": name, "text": dump([c for c in node if not (isinstance(c, list) and c and c[0] == "uuid")])}, "graphic")
        elif name in IGNORED:
            continue
        else:
            raise Unparsed(f"identity.unparsed_class: the top-level form {name!r} is neither handled nor ignored on purpose")
    snap["forms_seen"] = sorted(set(snap["forms_seen"]))
    return snap


def flat(value):
    return json.dumps(value, sort_keys=True)


def differences(before: dict, after: dict) -> list[dict]:
    """The observed differences, sorted. Each is a dict with op, class, ident, field, before, after."""
    out = []

    def add(op, cls, ident, field=None, b=None, a=None, **extra):
        out.append({"op": op, "class": cls, "ident": ident, "field": field, "before": flat(b) if field else None, "after": flat(a) if field else None, **extra})

    old, new = before["footprints"], after["footprints"]
    for uid in sorted(set(old) | set(new)):
        if uid in old and uid in new:
            for field in ("reference", "value", "lib_id", "path", "layer", "at", "properties"):
                if old[uid][field] != new[uid][field]:
                    add("changed", "footprint", old[uid]["reference"], field, old[uid][field], new[uid][field])
            for number in sorted(set(old[uid]["pads"]) | set(new[uid]["pads"])):
                po, pn = old[uid]["pads"].get(number), new[uid]["pads"].get(number)
                if po is None or pn is None:
                    add("changed", "pad", f"{old[uid]['reference']}.{number}", "present", po is not None, pn is not None)
                    continue
                for field in ("uuid", "at", "net"):
                    if po[field] != pn[field]:
                        add("changed", "pad", f"{old[uid]['reference']}.{number}", field, po[field], pn[field])
        elif uid in old:
            add("removed", "footprint", old[uid]["reference"], uuid=uid)
        else:
            nets = {n: p["net"] for n, p in new[uid]["pads"].items()}
            add("added", "footprint", new[uid]["reference"], lib_id=new[uid]["lib_id"], value=new[uid]["value"], pad_nets=nets)
    for cls, key in (("segment", "segments"), ("arc", "arcs"), ("via", "vias"), ("zone", "zones"), ("graphic", "graphics")):
        o, n = before[key], after[key]
        for uid in sorted(set(o) | set(n)):
            if uid in o and uid in n:
                for field in sorted(set(o[uid]) | set(n[uid])):
                    if o[uid].get(field) != n[uid].get(field):
                        add("changed", cls, uid, field, o[uid].get(field), n[uid].get(field))
            elif uid in o:
                add("removed", cls, uid, net=o[uid].get("net"))
            else:
                add("added", cls, uid, net=n[uid].get("net"))
    return out


def key_of(d: dict) -> str:
    return json.dumps({k: d[k] for k in sorted(d) if d[k] is not None}, sort_keys=True)


def compare(before: dict, after: dict, expected: list[dict]) -> dict:
    observed = differences(before, after)
    exp = []
    for e in expected:
        entry = dict(e)
        if entry.get("field"):
            entry["before"], entry["after"] = flat(entry.get("before")), flat(entry.get("after"))
        exp.append(json.loads(key_of(entry)))
    obs = [json.loads(key_of(d)) for d in observed]
    keys = [key_of(e) for e in exp]
    repeated = sorted({k for k in keys if keys.count(k) > 1})
    if repeated:
        raise InputProblem(f"identity.duplicate_expectation: the expectation lists a difference two times: {repeated[0]}")
    unexpected = [d for d in obs if d not in exp]
    missing = [e for e in exp if e not in obs]
    return {"observed": len(obs), "expected": len(exp), "unexpected": unexpected, "missing": missing, "status": "equal" if not unexpected and not missing else "different"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("board")
    snap.add_argument("-o", "--output")
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("before")
    cmp_.add_argument("after")
    cmp_.add_argument("--expect", required=True)
    cmp_.add_argument("--json", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as err:
        return 2 if err.code else 0
    try:
        if args.command == "snapshot":
            data = snapshot_text(Path(args.board).read_text())
            text = json.dumps(data, indent=2, sort_keys=True) + "\n"
            if args.output:
                Path(args.output).write_text(text)
            else:
                print(text, end="")
            return 0
        before, after = json.loads(Path(args.before).read_text()), json.loads(Path(args.after).read_text())
        expected = json.loads(Path(args.expect).read_text())["differences"]
        result = compare(before, after, expected)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "equal" else 1
    except Unparsed as err:
        print(json.dumps({"error": str(err)}))
        return 3
    except (OSError, ValueError, IndexError, KeyError) as err:
        print(json.dumps({"error": f"{type(err).__name__}: {err}"}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
