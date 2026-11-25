#!/usr/bin/env python3
"""Measure circular corner radii and classify closed Edge.Cuts contours with pcbnew."""
import hashlib
import json
import math
import sys
from pathlib import Path


class Unsupported(ValueError):
    pass


def point(value):
    return (int(value.x), int(value.y))


def delta(a, b):
    return (b[0] - a[0], b[1] - a[1])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def reverse(edge):
    result = dict(edge)
    result["start"], result["end"] = edge["end"], edge["start"]
    result["points"] = list(reversed(edge["points"]))
    result["tin"] = tuple(-x for x in edge["tout"])
    result["tout"] = tuple(-x for x in edge["tin"])
    result["sweep"] = -edge["sweep"]
    return result


def line(a, b, name):
    if a == b:
        raise Unsupported(f"Edge.Cuts {name} has zero length.")
    return {"start": a, "end": b, "points": [a, b], "tin": delta(a, b), "tout": delta(a, b),
            "sweep": 0, "radius_nm": None, "uuid": name}


def arc(shape, name):
    a, b, mid, center = point(shape.GetStart()), point(shape.GetEnd()), point(shape.GetArcMid()), point(shape.GetCenter())
    start = math.atan2(a[1] - center[1], a[0] - center[0])
    stop = math.atan2(b[1] - center[1], b[0] - center[0])
    middle = math.atan2(mid[1] - center[1], mid[0] - center[0])
    sweep = (stop - start) % math.tau
    if (middle - start) % math.tau > sweep:
        sweep -= math.tau
    if abs(abs(sweep) - math.pi / 2) > 0.00001:
        raise Unsupported(f"Edge.Cuts arc {name} is not a quarter circle.")
    radius = int(shape.GetRadius())
    if radius <= 1000:
        raise Unsupported(f"Edge.Cuts arc {name} has a radius at or below one micrometer.")
    # The polygon classifies topology only. Its circular chord error is at most one micrometer.
    step = 2 * math.acos(1 - 1000 / radius)
    count = max(2, math.ceil(abs(sweep) / step))
    if count > 4096:
        raise Unsupported(f"Edge.Cuts arc {name} exceeds the topology point limit.")
    points = [(center[0] + radius * math.cos(start + sweep * i / count),
               center[1] + radius * math.sin(start + sweep * i / count)) for i in range(count + 1)]
    points[0], points[-1] = a, b
    sign = 1 if sweep > 0 else -1
    def tangent(p):
        return (-(p[1] - center[1]) * sign, (p[0] - center[0]) * sign)
    return {"start": a, "end": b, "points": points, "tin": tangent(a), "tout": tangent(b),
            "sweep": sweep, "radius_nm": radius, "uuid": name}


def measure(board, pcbnew):
    from shapely.geometry import Polygon
    edges = []
    circles = []
    drawings = list(board.GetDrawings())
    for footprint in board.GetFootprints():
        drawings.extend(footprint.GraphicalItems())
    for shape in drawings:
        if shape.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if not isinstance(shape, pcbnew.PCB_SHAPE):
            raise Unsupported("Edge.Cuts contains an object other than a geometric shape.")
        kind, name = shape.GetShape(), shape.m_Uuid.AsString()
        if kind == pcbnew.SHAPE_T_SEGMENT:
            edges.append(line(point(shape.GetStart()), point(shape.GetEnd()), name))
        elif kind == pcbnew.SHAPE_T_ARC:
            edges.append(arc(shape, name))
        elif kind == pcbnew.SHAPE_T_RECT:
            a, c = point(shape.GetStart()), point(shape.GetEnd())
            points = [a, (c[0], a[1]), c, (a[0], c[1])]
            edges.extend(line(points[i], points[(i + 1) % 4], name) for i in range(4))
        elif kind == pcbnew.SHAPE_T_CIRCLE:
            center, radius = point(shape.GetCenter()), int(shape.GetRadius())
            if radius <= 1000:
                raise Unsupported(f"Edge.Cuts circle {name} has a radius at or below one micrometer.")
            count = max(16, math.ceil(math.tau / (2 * math.acos(1 - 1000 / radius))))
            if count > 4096:
                raise Unsupported(f"Edge.Cuts circle {name} exceeds the topology point limit.")
            points = [(center[0] + radius * math.cos(math.tau * i / count),
                       center[1] + radius * math.sin(math.tau * i / count)) for i in range(count)]
            circles.append({"edges": [], "polygon": Polygon(points), "circle": (name, radius)})
        else:
            raise Unsupported(f"Edge.Cuts shape {name} has unsupported type {shape.GetShapeStr()}.")
    adjacency = {}
    for index, edge in enumerate(edges):
        for p in (edge["start"], edge["end"]):
            adjacency.setdefault(p, []).append(index)
    if any(len(indices) != 2 for indices in adjacency.values()):
        raise Unsupported("Edge.Cuts has an open, branching or overlapping endpoint.")
    loops = circles
    unused = set(range(len(edges)))
    while unused:
        first = min(unused)
        current = edges[first]
        unused.remove(first)
        sequence = [current]
        start = current["start"]
        while current["end"] != start:
            choices = [i for i in adjacency[current["end"]] if i in unused]
            if len(choices) != 1:
                raise Unsupported("Edge.Cuts does not form separate closed contours.")
            index = choices[0]
            following = edges[index]
            if following["start"] != current["end"]:
                following = reverse(following)
            unused.remove(index)
            sequence.append(following)
            current = following
        points = [p for edge in sequence for p in edge["points"][:-1]]
        loops.append({"edges": sequence, "polygon": Polygon(points), "circle": None})
    if not loops or any(not item["polygon"].is_valid or item["polygon"].area <= 0 for item in loops):
        raise Unsupported("Edge.Cuts has no valid simple closed outline.")
    outer = max(loops, key=lambda item: item["polygon"].area)
    for item in loops:
        if item is not outer and not outer["polygon"].contains(item["polygon"]):
            raise Unsupported("Edge.Cuts has multiple outer contours or intersecting contours.")
    for i, first in enumerate(loops):
        for second in loops[i + 1:]:
            if first["polygon"].boundary.distance(second["polygon"].boundary) <= 10000:
                raise Unsupported("Edge.Cuts contours are within the topology separation bound of 0.01 mm.")
            if first is not outer and second is not outer and first["polygon"].intersects(second["polygon"]):
                raise Unsupported("Edge.Cuts contains intersecting or nested cutouts.")
    corners = []
    for item in loops:
        cutout = item is not outer
        location = "cutout" if cutout else "outline"
        if item["circle"]:
            if cutout:
                name, radius = item["circle"]
                corners.append({"location": location, "uuid": name, "radius_nm": radius, "kind": "circle"})
            continue
        sequence = item["edges"]
        winding = 1 if item["polygon"].exterior.is_ccw else -1
        material_sign = winding if cutout else -winding
        for i, edge in enumerate(sequence):
            if edge["sweep"] * material_sign > 0:
                corners.append({"location": location, "uuid": edge["uuid"], "radius_nm": edge["radius_nm"], "kind": "arc"})
            following = sequence[(i + 1) % len(sequence)]
            a, b = edge["tout"], following["tin"]
            turn = math.atan2(cross(a, b), a[0] * b[0] + a[1] * b[1])
            if abs(turn) > math.pi - 0.00001:
                raise Unsupported("Edge.Cuts reverses direction at an endpoint.")
            if turn * material_sign > 0.00001:
                corners.append({"location": location, "uuid": edge["uuid"], "radius_nm": 0, "kind": "sharp"})
    return {"corners": corners, "contours": len(loops), "topology_chord_bound_nm": 1000,
            "topology_separation_bound_nm": 10000, "radius_source": "pcbnew GetRadius in integer nanometers"}


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"error": "Give one board path."}))
        return 2
    try:
        import pcbnew
        path = Path(argv[1])
        data = path.read_bytes()
        result = measure(pcbnew.LoadBoard(str(path)), pcbnew)
        result["board_sha256"] = hashlib.sha256(data).hexdigest()
        print(json.dumps(result, sort_keys=True))
        return 0
    except Unsupported as err:
        print(json.dumps({"unsupported": str(err)}))
        return 2
    except Exception as err:
        print(json.dumps({"error": f"The corner measurement failed: {err}"}))
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
