#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery", "jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Geometry for the B11 mechanical fit (completion repair). Reads DXF and Excellon bytes with
the standard library and STEP with CadQuery. Builds the labeled proxy assembly. Runs every
comparison against independent expectations from the source record.

Every function takes bytes or private files written from captured bytes. No function reopens
a live project path.

Results are dictionaries with `id`, `ref` (or None), `status`, `measured_error_mm`,
`tolerance_mm`, `reason`. Completeness and status are recomputed by `recompute_status`.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

TOL_GEOMETRY = 0.01
TOL_ANGLE = 0.1
TOL_VOLUME = 1e-6
GEOMETRY_IDS = ("C01", "C02", "C02d", "C03", "C04", "C05", "C06", "C07", "C09", "C12", "closed_hole_set")
FIT_IDS = ("C08", "C10", "C11")
PER_REF_IDS = ("C06", "C07", "C08", "C09")
DRILL_FILES = {"board-PTH.drl": ("drill_pth", True), "board-NPTH.drl": ("drill_npth", False)}


class UnsupportedDrill(ValueError):
    """A drill object the reader cannot measure. The message names the object."""


# --------------------------------------------------------------------------- DXF

def parse_dxf(data: bytes) -> dict:
    """LINE and CIRCLE entities. Any other entity type refuses with its name."""
    raw = [line.strip() for line in data.decode("utf-8").splitlines()]
    pairs = [(raw[i], raw[i + 1]) for i in range(0, len(raw) - 1, 2)]
    lines, circles, cur, types = [], [], None, []
    in_entities = False
    section_next = False

    def close(entity):
        if entity is None:
            return
        g = entity["g"]
        if entity["type"] == "LINE":
            lines.append(((float(g["10"]), float(g["20"])), (float(g["11"]), float(g["21"]))))
        elif entity["type"] == "CIRCLE":
            circles.append((float(g["10"]), float(g["20"]), float(g["40"])))

    for code, value in pairs:
        if code == "0":
            close(cur)
            cur = None
            if value == "SECTION":
                section_next = True
                continue
            if value == "ENDSEC":
                in_entities = False
                continue
            if value == "EOF":
                break
            if in_entities:
                if value in ("LINE", "CIRCLE"):
                    cur = {"type": value, "g": {}}
                else:
                    types.append(value)
            continue
        if section_next and code == "2":
            in_entities = value == "ENTITIES"
            section_next = False
            continue
        if cur is not None and code in ("10", "20", "11", "21", "40"):
            cur["g"][code] = value
    close(cur)
    if types:
        raise UnsupportedDrill(f"DXF entity {types[0]} is not supported; slots and arcs are refused")
    return {"lines": lines, "circles": circles}


def outline_vertices(dxf: dict) -> list[tuple[float, float]]:
    """Unique line endpoints. Order is not kept (Codex item 14)."""
    seen = []
    for a, b in dxf["lines"]:
        for p in (a, b):
            if not any(abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6 for q in seen):
                seen.append(p)
    return seen


# --------------------------------------------------------------------------- Excellon

_TA = re.compile(r"^; #@! TA\.AperFunction,(Plated|NonPlated)")
_TOOL = re.compile(r"^T(\d+)C([0-9.]+)$")
_SELECT = re.compile(r"^T(\d+)$")
_HIT = re.compile(r"^X(-?[0-9.]+)Y(-?[0-9.]+)$")
_KNOWN = re.compile(r"^(M48|M30|METRIC,TZ|METRIC|FMAT,2|G90|G05|%|;.*)$")


def parse_excellon(data: bytes, expect_plated: bool | None = None) -> dict:
    """Tools with the plated flag from the AperFunction comment, and round hits in mm.

    Refuses with the object named: a routed or slot record (G85, G00, G01, G02, G03), a hit
    with more than one coordinate pair, an undefined tool, a tool without a plating comment,
    and any unknown line. When `expect_plated` is given, every tool must match it.
    """
    tools, hits, pending, current = {}, [], None, None
    for number, raw in enumerate(data.decode("utf-8").splitlines(), start=1):
        s = raw.strip()
        if not s:
            continue
        m = _TA.match(s)
        if m:
            pending = m.group(1) == "Plated"
            continue
        m = _TOOL.match(s)
        if m:
            if pending is None:
                raise UnsupportedDrill(f"tool T{m.group(1)} (line {number}) has no plating comment")
            tools[m.group(1)] = {"diameter_mm": float(m.group(2)), "plated": pending}
            pending = None
            continue
        m = _SELECT.match(s)
        if m:
            current = m.group(1)
            continue
        m = _HIT.match(s)
        if m:
            if current is None:
                raise UnsupportedDrill(f"hit at line {number} has no tool selected")
            hits.append((current, float(m.group(1)), float(m.group(2))))
            continue
        if re.search(r"G8[0-9]|G0[0-3]", s) or len(re.findall(r"[XY]-?[0-9.]+", s)) > 2:
            coords = re.findall(r"X(-?[0-9.]+)Y(-?[0-9.]+)", s)
            where = f"at {coords[0]}" if coords else f"at line {number}"
            raise UnsupportedDrill(f"routed or slot drill object {where} (line {number}) is not supported")
        if not _KNOWN.match(s):
            raise UnsupportedDrill(f"unknown Excellon record at line {number}: {s[:40]}")
    if expect_plated is not None:
        for tid, info in tools.items():
            if info["plated"] is not expect_plated:
                raise UnsupportedDrill(f"tool T{tid} plating does not match this file")
    for tool, _, _ in hits:
        if tool not in tools:
            raise UnsupportedDrill(f"hit uses undefined tool T{tool}")
    return {"tools": tools, "hits": hits}


def excellon_holes(exc: dict) -> list[dict]:
    out = []
    for tool, x, y in exc["hits"]:
        info = exc["tools"][tool]
        out.append({"x": x, "y": y, "diameter_mm": info["diameter_mm"], "plated": info["plated"]})
    return out


# --------------------------------------------------------------------------- STEP (CadQuery)

def read_step(path: Path) -> dict:
    """Solids (validity, volume, bounding box), shapes, cylinder axes and planar faces."""
    import cadquery as cq  # noqa: PLC0415
    from OCP.BRepAdaptor import BRepAdaptor_Surface  # noqa: PLC0415
    from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane  # noqa: PLC0415

    shape = cq.importers.importStep(str(path)).val()
    solids, shapes = [], []
    for s in shape.Solids():
        bb = s.BoundingBox()
        solids.append({"valid": s.isValid(), "volume": s.Volume(),
                       "bbox": (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)})
        shapes.append(s)
    cylinders, planes = [], []
    for face in shape.Faces():
        surf = BRepAdaptor_Surface(face.wrapped)
        if surf.GetType() == GeomAbs_Plane:
            n = face.normalAt()
            c = face.Center()
            planes.append({"normal": (n.x, n.y, n.z), "centre": (c.x, c.y, c.z)})
            continue
        if surf.GetType() != GeomAbs_Cylinder:
            continue
        cyl = surf.Cylinder()
        loc = cyl.Axis().Location()
        d = cyl.Axis().Direction()
        cylinders.append({"x": loc.X(), "y": loc.Y(), "z": loc.Z(), "radius_mm": cyl.Radius(),
                          "axis": (d.X(), d.Y(), d.Z())})
    return {"solids": solids, "shapes": shapes, "cylinders": cylinders, "planes": planes}


def substrate_solid(step: dict, outline_bbox: tuple[float, float, float, float]) -> dict:
    """The one valid substrate solid whose X and Y range lies in the outline (C05)."""
    x0, y0, x1, y1 = outline_bbox
    inside = []
    for s in step["solids"]:
        bx0, by0, _, bx1, by1, _ = s["bbox"]
        if bx0 >= x0 - TOL_GEOMETRY and bx1 <= x1 + TOL_GEOMETRY and by0 >= y0 - TOL_GEOMETRY \
                and by1 <= y1 + TOL_GEOMETRY:
            inside.append(s)
    if len(inside) != 1 or not inside[0]["valid"]:
        raise ValueError(f"expected one valid substrate solid in the outline, found {len(inside)}")
    return inside[0]


def make_box(size, centre_xy, z0: float, rotation_deg: float):
    import cadquery as cq  # noqa: PLC0415
    sx, sy, sz = size
    box = cq.Solid.makeBox(sx, sy, sz, pnt=cq.Vector(-sx / 2, -sy / 2, z0))
    box = box.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), rotation_deg)
    return box.translate(cq.Vector(centre_xy[0], centre_xy[1], 0))


def build_fit_assembly(board_step: Path, proxies: list[dict], out_path: Path) -> None:
    """Board body plus one labeled proxy per record. Names: BOARD and PROXY <ref>."""
    import cadquery as cq  # noqa: PLC0415
    board = cq.importers.importStep(str(board_step)).val()
    assembly = cq.Assembly(name="PROXY FIT ASSEMBLY")
    assembly.add(cq.Workplane().add(board), name="BOARD")
    for p in proxies:
        box = make_box(p["size"], p["centre_xy"], p["z0"], p["rotation_deg"])
        assembly.add(cq.Workplane().add(box), name=f"PROXY {p['ref']}")
    assembly.save(str(out_path))


def intersection_volume(a, b) -> float:
    common = a.intersect(b)
    return common.Volume() if common is not None else 0.0


def solid_bbox(shape) -> tuple[float, float, float, float, float, float]:
    bb = shape.BoundingBox()
    return (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)


# --------------------------------------------------------------------------- geometry helpers

def signed_area(poly) -> float:
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def outward_cavity(outline, clearance: float) -> list[tuple[float, float]]:
    """The outline offset outward by `clearance`, chamfer included (lead resolution). Convex
    outlines only. Each edge moves along its outward normal. Neighbouring offset lines meet at
    a mitred corner. A non-convex outline refuses."""
    pts = list(outline)
    if signed_area(pts) < 0:
        pts = pts[::-1]
    n = len(pts)
    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        nx, ny = dy / length, -dx / length  # outward normal for counter-clockwise order
        lines.append(((a[0] + nx * clearance, a[1] + ny * clearance), (dx, dy)))
    for i in range(n):
        cross = lines[i][1][0] * lines[(i + 1) % n][1][1] - lines[i][1][1] * lines[(i + 1) % n][1][0]
        if cross < -1e-9:
            raise ValueError("the outline is not convex; the outward cavity is not defined")
    cavity = []
    for i in range(n):
        p1, d1 = lines[i - 1]
        p2, d2 = lines[i]
        cross = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(cross) < 1e-12:
            cavity.append(p2)
            continue
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / cross
        cavity.append((p1[0] + t * d1[0], p1[1] + t * d1[1]))
    return cavity


def point_in_polygon(p, poly) -> bool:
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def segment_distance(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    t = 0.0 if denom == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / denom))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def distance_to_boundary(p, poly) -> float:
    n = len(poly)
    return min(segment_distance(p, poly[i], poly[(i + 1) % n]) for i in range(n))


def inside_or_on(p, poly, tol: float = TOL_GEOMETRY) -> bool:
    """A corner is inside when it is inside the polygon or on its boundary within the tolerance."""
    return point_in_polygon(p, poly) or distance_to_boundary(p, poly) <= tol


def match_points(expected, measured, tol: float) -> dict:
    """Each expected point matches one measured point. Counts must agree. No order, no alignment."""
    if len(expected) != len(measured):
        return {"ok": False, "max_error_mm": None, "reason": f"count {len(measured)} differs from {len(expected)}"}
    used = [False] * len(measured)
    worst = 0.0
    for ex, ey in expected:
        best, best_j = None, None
        for j, (mx, my) in enumerate(measured):
            if used[j]:
                continue
            d = math.hypot(mx - ex, my - ey)
            if best is None or d < best:
                best, best_j = d, j
        if best is None or best > tol:
            return {"ok": False, "max_error_mm": best, "reason": f"no measured point within {tol} of ({ex}, {ey})"}
        used[best_j] = True
        worst = max(worst, best)
    return {"ok": True, "max_error_mm": worst, "reason": ""}


def result(cid, status, ref=None, error=None, tol=None, reason=""):
    return {"id": cid, "ref": ref, "status": status, "measured_error_mm": error, "tolerance_mm": tol,
            "reason": reason}


def from_match(cid, match, tol, ref=None):
    return result(cid, "pass" if match["ok"] else "fail", ref, match.get("max_error_mm"), tol, match.get("reason", ""))


# --------------------------------------------------------------------------- comparisons

def c01_outline(expected_outline, dxf: dict) -> dict:
    return from_match("C01", match_points(expected_outline, outline_vertices(dxf), TOL_GEOMETRY), TOL_GEOMETRY)


def c02_step_holes(expected_holes, step_cylinders) -> dict:
    unique = []
    for c in step_cylinders:
        p = (c["x"], c["y"])
        if not any(math.hypot(p[0] - q[0], p[1] - q[1]) < 1e-3 for q in unique):
            unique.append(p)
    return from_match("C02", match_points([(h["x"], h["y"]) for h in expected_holes], unique, TOL_GEOMETRY),
                      TOL_GEOMETRY)


def c02d_dxf_holes(expected_holes, dxf: dict) -> dict:
    measured = [(x, y) for x, y, _ in dxf["circles"]]
    return from_match("C02d", match_points([(h["x"], h["y"]) for h in expected_holes], measured, TOL_GEOMETRY),
                      TOL_GEOMETRY)


def c03_diameters(expected_holes, dxf: dict, step_cylinders) -> dict:
    """Each hole: exactly one DXF circle and at least one STEP cylinder at its centre. Both radii count."""
    worst = 0.0
    for h in expected_holes:
        circles = [r for x, y, r in dxf["circles"] if math.hypot(x - h["x"], y - h["y"]) <= TOL_GEOMETRY]
        if len(circles) != 1:
            return result("C03", "fail", h["id"], None, TOL_GEOMETRY, f"{len(circles)} DXF circles at the centre")
        radii = [c["radius_mm"] for c in step_cylinders if math.hypot(c["x"] - h["x"], c["y"] - h["y"]) <= TOL_GEOMETRY]
        if not radii:
            return result("C03", "fail", h["id"], None, TOL_GEOMETRY, "no STEP cylinder at the centre")
        err = max([abs(2 * circles[0] - h["diameter_mm"])] + [abs(2 * r - h["diameter_mm"]) for r in radii])
        worst = max(worst, err)
        if err > TOL_GEOMETRY:
            return result("C03", "fail", h["id"], err, TOL_GEOMETRY, "diameter differs")
    return result("C03", "pass", None, worst, TOL_GEOMETRY)


def c04_plated(expected_holes, pth: dict, npth: dict) -> dict:
    """Each separate file holds exactly its plating class: PTH file = plated holes, NPTH = non-plated."""
    for label, exc, want in (("PTH", pth, True), ("NPTH", npth, False)):
        exp = [h for h in expected_holes if h["plated"] is want]
        measured = excellon_holes(exc)
        if len(measured) != len(exp):
            return result("C04", "fail", None, None, 0.0, f"{label} file has {len(measured)} hits, expected {len(exp)}")
        for h in exp:
            if sum(1 for m in measured if math.hypot(m["x"] - h["x"], m["y"] - h["y"]) <= TOL_GEOMETRY) != 1:
                return result("C04", "fail", h["id"], None, 0.0, f"{label} file lacks {h['id']}")
    return result("C04", "pass", None, 0.0, 0.0)


def c05_substrate(solid: dict, core_mm: float) -> dict:
    z0, z1 = solid["bbox"][2], solid["bbox"][5]
    err = max(abs(z0 - 0.0), abs(z1 - core_mm))
    ok = err <= TOL_GEOMETRY
    return result("C05", "pass" if ok else "fail", None, err, TOL_GEOMETRY,
                  "" if ok else f"substrate z {z0}..{z1}, core {core_mm}")


def c12_origin(aux_origin, anchor) -> dict:
    err = math.hypot(aux_origin[0] - anchor[0], aux_origin[1] - anchor[1])
    return result("C12", "pass" if err <= TOL_GEOMETRY else "fail", None, err, TOL_GEOMETRY,
                  "" if err <= TOL_GEOMETRY else "origin differs from the anchor")


def closed_set(name: str, measured, expected) -> dict:
    """The measured centres equal the complete expected set. Missing and extra holes both fail."""
    for p in measured:
        if not any(math.hypot(p[0] - e[0], p[1] - e[1]) <= TOL_GEOMETRY for e in expected):
            return result("closed_hole_set", "fail", name, None, TOL_GEOMETRY, f"{name} hole at {p} is not listed")
    for e in expected:
        if not any(math.hypot(p[0] - e[0], p[1] - e[1]) <= TOL_GEOMETRY for p in measured):
            return result("closed_hole_set", "fail", name, None, TOL_GEOMETRY, f"{name} lacks the hole at {e}")
    return result("closed_hole_set", "pass", name, None, TOL_GEOMETRY)


def c06_connector(ref: str, frame: dict, insertion_angle_deg: float, planes, proxy_bbox) -> dict:
    """The mating face (normal along the insertion angle) sits at the interface frame position,
    and the frame rotation equals the insertion angle, within 0.01 mm and 0.1 degrees."""
    ang = math.radians(insertion_angle_deg)
    u = (math.cos(ang), math.sin(ang))
    candidates = []
    for pl in planes:
        if not _inside_bbox(pl["centre"], proxy_bbox, TOL_GEOMETRY):
            continue
        nx, ny, _ = pl["normal"]
        if math.hypot(nx, ny) < 1e-9:
            continue
        if (nx * u[0] + ny * u[1]) / math.hypot(nx, ny) >= math.cos(math.radians(TOL_ANGLE)):
            candidates.append(pl)
    if not candidates:
        return result("C06", "fail", ref, None, TOL_GEOMETRY, "no mating face along the insertion direction")
    mating = max(candidates, key=lambda pl: pl["centre"][0] * u[0] + pl["centre"][1] * u[1])
    err = math.hypot(mating["centre"][0] - frame["x"], mating["centre"][1] - frame["y"])
    ang_err = abs((frame["rotation_deg"] - insertion_angle_deg + 180) % 360 - 180)
    ok = err <= TOL_GEOMETRY and ang_err <= TOL_ANGLE
    res = result("C06", "pass" if ok else "fail", ref, err, TOL_GEOMETRY,
                 "" if ok else "position or rotation differs")
    res["angle_error_deg"] = ang_err
    return res


def _inside_bbox(p, bbox, tol):
    return (bbox[0] - tol <= p[0] <= bbox[3] + tol and bbox[1] - tol <= p[1] <= bbox[4] + tol
            and bbox[2] - tol <= p[2] <= bbox[5] + tol)


def c07_insertion(ref: str, box, others) -> dict:
    """No other solid shares volume with the insertion box. The connector's own proxy is excluded
    from `others` by the caller. Each intersecting solid is named."""
    offenders = [name for name, solid in others if intersection_volume(box, solid) > TOL_VOLUME]
    return result("C07", "fail" if offenders else "pass", ref, None, TOL_VOLUME,
                  ("intersects: " + ", ".join(offenders)) if offenders else "")


def c08_vertical(ref: str, side: str, bbox, top_surface_z: float, bottom_surface_z: float,
                 top_mm: float, bottom_mm: float) -> dict:
    if side == "top":
        over = bbox[5] - (top_surface_z + top_mm)
        name = "top_mm"
    else:
        over = (bottom_surface_z - bbox[2]) - bottom_mm
        name = "bottom_mm"
    ok = over <= TOL_GEOMETRY
    return result("C08", "pass" if ok else "fail", ref, over, TOL_GEOMETRY, "" if ok else f"over {name} by {round(over, 4)}")


def c09_cavity(ref: str, bbox, cavity) -> dict:
    """Every corner of the proxy lies inside the outward cavity or on its boundary (tolerance 0.01)."""
    x0, y0, _, x1, y1, _ = bbox
    bad = [c for c in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)] if not inside_or_on(c, cavity)]
    return result("C09", "fail" if bad else "pass", ref, None, TOL_GEOMETRY,
                  ("outside the cavity at " + ", ".join(str(c) for c in bad)) if bad else "")


def settings_switches_ok(settings: dict) -> list[str]:
    problems = []
    dxf = settings.get("dxf_outline", {}).get("switches", [])
    if "--output-units" not in dxf or dxf[dxf.index("--output-units") + 1] != "mm":
        problems.append("DXF output units must be mm")
    if "--drill-shape-opt" not in dxf or dxf[dxf.index("--drill-shape-opt") + 1] != "2":
        problems.append("DXF drill-shape-opt must be 2")
    step = settings.get("step_board", {}).get("switches", [])
    for needed in ("--board-only", "--no-extra-pad-thickness", "--drill-origin"):
        if needed not in step:
            problems.append(f"STEP switch {needed} is missing")
    for banned in ("--include-soldermask", "--include-pads", "--include-silkscreen"):
        if banned in step:
            problems.append(f"STEP switch {banned} must be off")
    drill = settings.get("drill", {}).get("switches", [])
    if "--excellon-separate-th" not in drill:
        problems.append("the drill export must use --excellon-separate-th")
    return problems


# --------------------------------------------------------------------------- completeness

def required_keys(src: dict) -> list[tuple[str, str | None]]:
    """Every comparison that must produce a result, keyed by ID and reference (R4, R8)."""
    refs = [p["ref"] for p in src.get("parts", [])] + [f["id"] for f in src["connector_frames"]]
    keys = [(c, None) for c in GEOMETRY_IDS if c not in PER_REF_IDS + ("closed_hole_set",)]
    keys += [("closed_hole_set", name) for name in ("STEP", "DXF", "PTH", "NPTH")]
    keys += [("C10", None), ("C11", None)]
    for ref in refs:
        keys.append(("C08", ref))
        keys.append(("C09", ref))
    for f in src["connector_frames"]:
        keys.append(("C06", f["id"]))
        keys.append(("C07", f["id"]))
    return keys


def recompute_status(results: list[dict], keys: list[tuple[str, str | None]]) -> dict:
    """Recompute completeness and status from the results (R8). Refuses empty results, duplicate
    keys, missing keys, unknown status values, and a pass whose error exceeds its tolerance."""
    problems = []
    if not results:
        return {"geometry_status": "fail", "fit_status": "fail", "missing": [f"{k}" for k in keys],
                "duplicates": [], "inconsistent": [], "problems": ["empty result set"]}
    seen = {}
    for r in results:
        key = (r["id"], r.get("ref"))
        if key in seen:
            problems.append(f"duplicate result {key}")
        seen[key] = r
        if r["status"] not in ("pass", "fail", "unconfirmed"):
            problems.append(f"status {r['status']!r} for {key} is not allowed")
        err, tol = r.get("measured_error_mm"), r.get("tolerance_mm")
        if r["status"] == "pass" and err is not None and tol is not None and err > tol + 1e-12:
            problems.append(f"{key} passes with error {err} above tolerance {tol}")
    missing = [f"{k[0]}:{k[1]}" if k[1] else k[0] for k in keys if k not in seen]
    geom_keys = [k for k in keys if k[0] in GEOMETRY_IDS]
    geom = all(seen.get(k, {}).get("status") == "pass" for k in geom_keys)
    fit_items = [seen[k] for k in keys if k[0] in FIT_IDS and k in seen]
    if missing or problems:
        return {"geometry_status": "fail", "fit_status": "fail", "missing": missing,
                "duplicates": [p for p in problems if p.startswith("duplicate")],
                "inconsistent": [p for p in problems if not p.startswith("duplicate")], "problems": problems}
    if any(r["status"] == "fail" for r in fit_items):
        fit = "fail"
    elif any(r["status"] == "unconfirmed" for r in fit_items):
        fit = "unconfirmed"
    else:
        fit = "pass"
    failing = [f"{k[0]}:{k[1]}" if k[1] else k[0] for k in keys if seen[k]["status"] == "fail"]
    return {"geometry_status": "pass" if geom else "fail", "fit_status": fit, "missing": [],
            "duplicates": [], "inconsistent": [], "problems": [], "failing": failing}


# --------------------------------------------------------------------------- proxy plan

def proxy_plan(iface: dict, evidence: dict, src: dict, transform: dict) -> list[dict]:
    """Proxy solids for every required reference. Expectations come from the source record through
    the accepted transform. Each connector has a declared body_length_mm, set inward from its mating
    face, opposite the transformed insertion vector, with zero overhang (lead resolution).
    """
    import mechanical as M  # noqa: PLC0415
    surfaces = M.check_stackup(src)
    frames = {f["id"]: f for f in iface.get("connector_frames", [])}
    sframes = {f["id"]: f for f in src["connector_frames"]}
    parts = {p["ref"]: p for p in src.get("parts", [])}
    records = {c["ref"]: c for c in evidence.get("components", [])}
    plan = []
    for ref in list(parts) + list(sframes):
        if ref not in records:
            raise ValueError(f"the evidence has no record for {ref}")
    for ref, sf in sframes.items():
        rec = records[ref]
        loc = rec["insertion_vector_local"]
        vec = M.target_vector((loc["x"], loc["y"]), sf["rotation_deg"])
        angle = M.target_angle_deg(vec)
        norm = math.hypot(vec[0], vec[1])
        u = (vec[0] / norm, vec[1] / norm)
        mate = M.to_target((sf["x"], sf["y"]), transform)
        body = rec["body_length_mm"]
        centre = (mate[0] - u[0] * body / 2, mate[1] - u[1] * body / 2)
        side = sf["side"]
        env = rec["connector_envelope"]
        z0 = surfaces["top_surface_z"] if side == "top" else surfaces["bottom_surface_z"] - env["height_mm"]
        plan.append({"ref": ref, "side": side, "kind": "connector", "centre_xy": centre,
                     "size": (body, env["width_mm"], env["height_mm"]), "z0": z0, "rotation_deg": angle,
                     "insertion_angle_deg": angle, "u": u, "mate": mate, "frame": frames[ref],
                     "insertion_depth_mm": rec["insertion_depth_mm"], "width_mm": env["width_mm"],
                     "height_mm": env["height_mm"]})
    for ref, p in parts.items():
        rec = records[ref]
        if rec["kicad_center_mm"] != p["kicad_center_mm"] or rec["rotation_deg"] != p["rotation_deg"]:
            raise ValueError(f"{ref}: the evidence placement differs from the source record")
        centre = M.to_target((p["kicad_center_mm"]["x"], p["kicad_center_mm"]["y"]), transform)
        size = (rec["envelope_mm"]["x"], rec["envelope_mm"]["y"], rec["envelope_mm"]["z"])
        z0 = surfaces["top_surface_z"] if p["side"] == "top" else surfaces["bottom_surface_z"] - size[2]
        plan.append({"ref": ref, "side": p["side"], "kind": "part", "centre_xy": centre, "size": size,
                     "z0": z0, "rotation_deg": (-p["rotation_deg"]) % 360.0})
    return plan


def proxy_bbox_for(read: dict, expected_box, count_offset: int = 1):
    """Index of the measured solid that matches an expected box (nearest bounding box)."""
    eb = solid_bbox(expected_box)
    best = None
    for i in range(count_offset, len(read["solids"])):
        bb = read["solids"][i]["bbox"]
        d = sum(abs(a - b) for a, b in zip(bb, eb))
        if best is None or d < best[0]:
            best = (d, i)
    return best


def evaluate(files: dict, work: Path, fit_out: Path) -> dict:
    """Every comparison on captured bytes. `files` keys: board_kicad, interface, source, evidence,
    dxf, step, pth, npth. Writes the proxy assembly to `fit_out`. Work files are private copies in `work`.
    """
    import json  # noqa: PLC0415
    import mechanical as M  # noqa: PLC0415

    iface = json.loads(files["interface"].decode("utf-8"))
    src = json.loads(files["source"].decode("utf-8"))
    evidence = json.loads(files["evidence"].decode("utf-8"))
    transform = M.load_transform(iface)
    outline = [M.to_target((x, y), transform) for x, y in src["outline_kicad_mm"]]
    holes_src = []
    for h in src["holes"]:
        x, y = M.to_target((h["x"], h["y"]), transform)
        holes_src.append({"id": h["id"], "x": x, "y": y, "diameter_mm": h["diameter_mm"], "plated": h["plated"]})
    excluded = []
    for e in M.validate_excluded(iface):
        excluded.append({"id": e["id"], "x": e["x"], "y": e["y"], "diameter_mm": e["diameter_mm"], "plated": e["plated"]})
    complete = holes_src + excluded
    surfaces = M.check_stackup(src)
    cavity = outward_cavity(outline, src["enclosure"]["clearance_mm"])
    results: list[dict] = []

    m_aux = re.search(r"aux_axis_origin ([-0-9.]+) ([-0-9.]+)", files["board_kicad"].decode("utf-8"))
    if m_aux is None:
        results.append(result("C12", "fail", None, None, TOL_GEOMETRY, "the board has no aux_axis_origin"))
    else:
        results.append(c12_origin((float(m_aux.group(1)), float(m_aux.group(2))), transform["anchor"]))

    dxf = parse_dxf(files["dxf"])
    pth = parse_excellon(files["pth"], expect_plated=True)
    npth = parse_excellon(files["npth"], expect_plated=False)
    work.mkdir(parents=True, exist_ok=True)
    step_copy = work / "board.step"
    step_copy.write_bytes(files["step"])
    step = read_step(step_copy)

    results.append(c01_outline(outline, dxf))
    results.append(c02d_dxf_holes(complete, dxf))
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    solid = substrate_solid(step, (min(xs), min(ys), max(xs), max(ys)))
    results.append(c05_substrate(solid, src["stackup"]["core_mm"]))
    results.append(c02_step_holes(complete, step["cylinders"]))
    results.append(c03_diameters(complete, dxf, step["cylinders"]))
    results.append(c04_plated(complete, pth, npth))
    step_centres = []
    for c in step["cylinders"]:
        p = (round(c["x"], 3), round(c["y"], 3))
        if p not in step_centres:
            step_centres.append(p)
    expected_centres = [(h["x"], h["y"]) for h in complete]
    results.append(closed_set("STEP", step_centres, expected_centres))
    results.append(closed_set("DXF", [(x, y) for x, y, _ in dxf["circles"]], expected_centres))
    results.append(closed_set("PTH", [(x, y) for _, x, y in pth["hits"]],
                              [(h["x"], h["y"]) for h in complete if h["plated"]]))
    results.append(closed_set("NPTH", [(x, y) for _, x, y in npth["hits"]],
                              [(h["x"], h["y"]) for h in complete if not h["plated"]]))
    # Results from the closed-set helper carry no hole ID; the status above is the whole check.

    plan = proxy_plan(iface, evidence, src, transform)
    records_solids = []
    for p in plan:
        exp = make_box(p["size"], p["centre_xy"], p["z0"], p["rotation_deg"])
        records_solids.append((p, exp))
    build_fit_assembly(step_copy, [{k: p[k] for k in ("ref", "centre_xy", "size", "z0", "rotation_deg")} for p in plan],
                       fit_out)
    read = read_step(fit_out)
    shapes = read["shapes"]
    placed = []
    if len(read["solids"]) != 1 + len(plan):
        results.append(result("C08", "fail", None, None, TOL_GEOMETRY,
                              f"the fit assembly holds {len(read['solids']) - 1} proxies, expected {len(plan)}"))
        bboxes = None
    else:
        bboxes = []
        for p, exp in records_solids:
            d, i = proxy_bbox_for(read, exp)
            if d > 0.02:
                results.append(result("C08", "fail", p["ref"], d, TOL_GEOMETRY, "the measured proxy differs from its placement"))
            placed.append({"plan": p, "index": i, "bbox": read["solids"][i]["bbox"]})
    if bboxes is None or len(placed) != len(plan):
        for p in plan:
            for cid in ("C09", "C08") if p["kind"] == "part" else ("C06", "C07", "C08", "C09"):
                if not any(r["id"] == cid and r.get("ref") == p["ref"] for r in results):
                    results.append(result(cid, "fail", p["ref"], None, TOL_GEOMETRY, "the proxy assembly is incomplete"))
    else:
        for item in placed:
            p = item["plan"]
            if p["kind"] == "connector":
                results.append(c06_connector(p["ref"], p["frame"], p["insertion_angle_deg"], read["planes"], item["bbox"]))
                box_centre = (p["mate"][0] + p["u"][0] * p["insertion_depth_mm"] / 2,
                              p["mate"][1] + p["u"][1] * p["insertion_depth_mm"] / 2)
                z0 = surfaces["top_surface_z"] if p["side"] == "top" else surfaces["bottom_surface_z"] - p["height_mm"]
                box = make_box((p["insertion_depth_mm"], p["width_mm"], p["height_mm"]), box_centre, z0,
                               p["insertion_angle_deg"])
                others = [("BOARD", shapes[0])]
                others += [(o["plan"]["ref"], shapes[o["index"]]) for o in placed if o is not item]
                results.append(c07_insertion(p["ref"], box, others))
            results.append(c08_vertical(p["ref"], p["side"], item["bbox"], surfaces["top_surface_z"],
                                        surfaces["bottom_surface_z"], iface["height_limits"]["top_mm"],
                                        iface["height_limits"]["bottom_mm"]))
            results.append(c09_cavity(p["ref"], item["bbox"], cavity))

    statuses = [M.evidence_status(rec) for rec in evidence.get("components", [])]
    if "unconfirmed" in statuses:
        results.append(result("C10", "unconfirmed", None, None, None, "an evidence item is unconfirmed"))
    else:
        results.append(result("C10", "pass", None, None, None, ""))
    conflicts = M.owner_conflicts(iface["dimension_owners"], src["dimension_owners"])
    results.append(result("C11", "fail" if conflicts else "pass", None, None, None, ", ".join(conflicts)))
    return {"results": results, "keys": required_keys(src), "cavity": cavity}
