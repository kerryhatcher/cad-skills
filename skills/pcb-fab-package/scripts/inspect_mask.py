# /// script
# requires-python = ">=3.10"
# dependencies = ["gerbonara==1.6.3"]
# ///
"""Measure the solder-mask webs of an exported mask Gerber with the exact distance method.

Usage: uv run scripts/inspect_mask.py --gerber FILE.gbr (--limit-mil N | --limit-mm N) --report OUT.json

Exit status: 0 every web passes, 1 a web fails or is uncertain, 2 an unsupported construct or a resource limit,
3 a tool failure.

Supported subset (measured in `b7-mask-boundary-trials-claude.md`):
- dark flashes of circle apertures without a hole, rectangle apertures without a hole, and the `RoundRect` macro;
- every macro definition in the file, found anywhere in the text, must equal the measured `RoundRect` definition
  (`macro_defs.py`). Any other macro, or a `%AM` form that does not match, is refused with exit 2;
- a `RoundRect` flash must have an axis-aligned rectangle of four corners, traversed as a cycle, with a radius
  that is positive and finite. The radius has no limit relative to the core side. Any other parameter geometry is refused with exit 2.
- regions, strokes, clear polarity and other apertures are refused with exit 2;
- two flashes whose cores overlap in their interior form an overlapping cluster and are refused with exit 2;
- two flashes that touch (gap exactly 0 without interior overlap) are `merged_opening` and are not a web failure.

The exact distance is max(0, d_core - r1 - r2). A circle core is its centre. A rectangle core is its box.
A `RoundRect` core is the box through its four corner centres, and r is its corner radius. The error bound
0.000003 mm is derived from the 6-decimal Gerber coordinates (not measured). A web passes only when it is at
least the limit plus the bound, fails when it is below the limit minus the bound, and is uncertain otherwise.

One byte snapshot: the file is read once. Its SHA-256 is computed from those bytes, and the parser and the
geometry use the same bytes. The report holds that hash. The caller compares it with the published file.

Resource limits: at most 10000 flashes, 5 MB of input, 2000000 candidate pairs, and an elapsed-time budget of
2 seconds across reading, parsing and pair inspection. The report stores counts, the minimum web, and at most
100 pairs that are not a pass.
"""
import hashlib
import json
import math
import pathlib
import re
import sys
import time

from gerbonara import GerberFile
from gerbonara.apertures import ApertureMacroInstance, CircleAperture, RectangleAperture

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from macro_defs import ROUNDRECT_MACRO  # noqa: E402

MAX_FLASHES = 10000
MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_PAIR_CHECKS = 2000000
MAX_SECONDS = 2.0
CHECK_EVERY = 1000
MAX_LISTED_PAIRS = 100
ERROR_BOUND_MM = 0.000003
MIL_MM = 0.0254
EXIT_PASS, EXIT_VIOLATION, EXIT_UNSUPPORTED, EXIT_TOOL = 0, 1, 2, 3
MACRO_RE = re.compile(r"%AM([^*%]+)\*(.*?)%", re.S)
# The measured definition without the leading `%AM` and the closing `%`.
EXPECTED_MACRO = ROUNDRECT_MACRO.strip()[3:-1]


class Unsupported(Exception):
    pass


def check_macros(text):
    """Accept only the measured RoundRect definition. Search the whole text, not only line starts."""
    for match in re.finditer(r"%AM", text):
        if match.start() == 0 or text[match.start() - 1] != "\n":
            raise Unsupported("a macro definition does not start a line")
    blocks = MACRO_RE.findall(text)
    if text.count("%AM") != len(blocks):
        raise Unsupported("a macro definition is not in the measured form")
    if len(blocks) > 1:
        raise Unsupported("more than one macro definition")
    for name, body in blocks:
        if name != "RoundRect":
            raise Unsupported(f"unsupported macro {name}")
        if name + "*" + body != EXPECTED_MACRO:
            raise Unsupported("the RoundRect macro definition differs from the measured definition")
    return len(blocks)


def roundrect_geometry(params):
    """Return ((x0, y0, x1, y1), radius) for the measured parameter form, or raise Unsupported."""
    if len(params) != 10:
        raise Unsupported("the RoundRect macro needs one radius, four corners and a rotation")
    if float(params[9]) != 0.0:
        raise Unsupported("a rotated RoundRect is not measured")
    radius = float(params[0])
    pts = [(float(params[1 + 2 * i]), float(params[2 + 2 * i])) for i in range(4)]
    xs = sorted({p[0] for p in pts})
    ys = sorted({p[1] for p in pts})
    if len(xs) != 2 or len(ys) != 2:
        raise Unsupported("the RoundRect corners are not an axis-aligned rectangle")
    if set(pts) != {(xs[0], ys[0]), (xs[0], ys[1]), (xs[1], ys[0]), (xs[1], ys[1])} or len(set(pts)) != 4:
        raise Unsupported("the RoundRect corners are not the four corners of one rectangle")
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        if (a[0] == b[0]) == (a[1] == b[1]):
            raise Unsupported("the RoundRect corners are not in a cycle around the rectangle")
    w, h = xs[1] - xs[0], ys[1] - ys[0]
    if w <= 0 or h <= 0 or not (math.isfinite(radius) and radius > 0):
        raise Unsupported("the RoundRect size or radius is not valid")
    if not all(math.isfinite(v) for v in (xs[0], xs[1], ys[0], ys[1])):
        raise Unsupported("the RoundRect coordinates are not finite")
    return (xs[0], ys[0], xs[1], ys[1]), radius


def shape_of(obj, index):
    """Return (x, y, core, radius) for a dark flash, or raise Unsupported."""
    kind = type(obj).__name__
    if kind != "Flash":
        raise Unsupported(f"object {index} is a {kind}; only flashes are supported")
    if not obj.polarity_dark:
        raise Unsupported(f"object {index} has clear polarity")
    ap = obj.aperture
    x, y = float(obj.x), float(obj.y)
    if isinstance(ap, (CircleAperture, RectangleAperture)) and getattr(ap, "hole_dia", None):
        raise Unsupported(f"object {index} uses an aperture with a hole, which is not measured")
    if isinstance(ap, CircleAperture):
        return x, y, (0.0, 0.0, 0.0, 0.0), float(ap.diameter) / 2
    if isinstance(ap, RectangleAperture):
        w, h = float(ap.w), float(ap.h)
        return x, y, (-w / 2, -h / 2, w / 2, h / 2), 0.0
    if isinstance(ap, ApertureMacroInstance) and ap.macro.name == "RoundRect":
        box, radius = roundrect_geometry(ap.parameters)
        return x, y, (box[0], box[1], box[2], box[3]), radius
    name = getattr(getattr(ap, "macro", None), "name", type(ap).__name__)
    raise Unsupported(f"object {index} uses the unsupported aperture {name}")


def core_box(shape):
    x, y, core, _ = shape
    return x + core[0], y + core[1], x + core[2], y + core[3]


def signed_gap(a, b):
    """The exact signed gap in millimetres. Negative means overlap.

    Cores whose interiors intersect give a negative gap. Interior overlap is tested first, so two zero-radius
    rectangles that overlap are not read as contact. Cores that touch only on an edge give a gap of zero."""
    ax0, ay0, ax1, ay1 = core_box(a)
    bx0, by0, bx1, by1 = core_box(b)
    ox = min(ax1, bx1) - max(ax0, bx0)
    oy = min(ay1, by1) - max(ay0, by0)
    if ox > 0 and oy > 0:
        return -min(ox, oy) - a[3] - b[3]
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return math.hypot(dx, dy) - a[3] - b[3]


def decide(web, limit):
    if web >= limit + ERROR_BOUND_MM:
        return "pass"
    if web < limit - ERROR_BOUND_MM:
        return "fail"
    return "uncertain"


def inspect(path, limit_mm, max_seconds=MAX_SECONDS):
    """Measure the file. Return (status, body). The body holds the SHA-256 of the bytes that were measured."""
    start = time.monotonic()

    def budget(stage):
        if time.monotonic() - start > max_seconds:
            raise Unsupported(f"the elapsed-time limit of {max_seconds} seconds was exceeded during {stage}")

    raw = pathlib.Path(path).read_bytes()
    snapshot = hashlib.sha256(raw).hexdigest()
    if len(raw) > MAX_INPUT_BYTES:
        raise Unsupported(f"the Gerber input is larger than {MAX_INPUT_BYTES} bytes")
    budget("reading")
    text = raw.decode("ascii", errors="strict")
    check_macros(text)
    gerber = GerberFile.from_string(text)
    budget("parsing")
    shapes = [shape_of(obj, i) for i, obj in enumerate(gerber.objects)]
    budget("geometry")
    if len(shapes) > MAX_FLASHES:
        raise Unsupported(f"more than {MAX_FLASHES} flashes")
    if not shapes:
        return EXIT_PASS, {"gerber_sha256": snapshot, "flashes": 0, "counts": {}, "minimum_web_mm": None,
                           "result": "pass", "listed_pairs": []}
    extent = [max(abs(s[2][0]), abs(s[2][1]), abs(s[2][2]), abs(s[2][3])) + s[3] for s in shapes]
    window = limit_mm + 2 * max(extent) + 2 * ERROR_BOUND_MM
    order = sorted(range(len(shapes)), key=lambda i: shapes[i][0])
    counts = {"pass": 0, "fail": 0, "uncertain": 0, "merged_opening": 0}
    listed, minimum, checks = [], None, 0
    for pos, i in enumerate(order):
        for j in order[pos + 1:]:
            if shapes[j][0] - shapes[i][0] > window:
                break
            checks += 1
            if checks > MAX_PAIR_CHECKS:
                raise Unsupported(f"more than {MAX_PAIR_CHECKS} candidate pairs")
            if checks % CHECK_EVERY == 0:
                budget("pair inspection")
            gap = signed_gap(shapes[i], shapes[j])
            if gap < 0:
                raise Unsupported(f"overlapping cluster: objects {i} and {j} overlap by {-gap:.6f} mm")
            if gap == 0:
                counts["merged_opening"] += 1
                continue
            decision = decide(gap, limit_mm)
            counts[decision] += 1
            if minimum is None or gap < minimum[0]:
                minimum = (gap, i, j)
            if decision != "pass" and len(listed) < MAX_LISTED_PAIRS:
                listed.append({"objects": [i, j], "web_mm": gap, "decision": decision})
    budget("result")
    if minimum is None:
        return EXIT_PASS, {"gerber_sha256": snapshot, "flashes": len(shapes), "pair_checks": checks,
                           "counts": counts, "minimum_web_mm": None, "result": "pass", "listed_pairs": listed}
    worst = "fail" if counts["fail"] else ("uncertain" if counts["uncertain"] else "pass")
    status = EXIT_PASS if worst == "pass" else EXIT_VIOLATION
    return status, {"gerber_sha256": snapshot, "flashes": len(shapes), "pair_checks": checks, "counts": counts,
                    "minimum_web_mm": minimum[0], "minimum_pair": [minimum[1], minimum[2]],
                    "result": worst, "listed_pairs": listed}


def main(argv):
    def arg(key):
        return argv[argv.index(key) + 1] if key in argv and argv.index(key) + 1 < len(argv) else None
    gerber, report = arg("--gerber"), arg("--report")
    limit_mil_text, limit_mm_text = arg("--limit-mil"), arg("--limit-mm")
    if not gerber or not report or (limit_mil_text is None) == (limit_mm_text is None):
        print("inspect_mask: give --gerber, --report and one of --limit-mil or --limit-mm", file=sys.stderr)
        return 2
    flag, text = ("--limit-mil", limit_mil_text) if limit_mil_text is not None else ("--limit-mm", limit_mm_text)
    try:
        value = float(text)
    except ValueError:
        value = math.nan
    if not math.isfinite(value) or value <= 0:
        print(f"inspect_mask: {flag} must be a finite number greater than 0", file=sys.stderr)
        return 2
    limit_mil, limit_mm = (value, value * MIL_MM) if flag == "--limit-mil" else (None, value)
    try:
        status, body = inspect(gerber, limit_mm)
    except Unsupported as err:
        status, body = EXIT_UNSUPPORTED, {"unsupported": str(err)}
    except OSError as err:
        print(f"inspect_mask: cannot read the Gerber: {err}", file=sys.stderr)
        return EXIT_TOOL
    except Exception as err:  # a parser failure on malformed input is a tool failure.
        print(f"inspect_mask: the parser failed: {err}", file=sys.stderr)
        return EXIT_TOOL
    body.update({"limit_mil": limit_mil, "limit_mm": limit_mm, "error_bound_mm": ERROR_BOUND_MM,
                 "error_bound_basis": "derived from 6-decimal Gerber coordinates, not measured",
                 "time_limit_seconds": MAX_SECONDS, "exit": status})
    pathlib.Path(report).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"exit": status, "result": body.get("result", body.get("unsupported"))}))
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
