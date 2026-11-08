#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["trimesh>=4", "rtree", "scipy", "numpy", "matplotlib", "networkx", "lxml", "cadquery"]
# ///
"""FDM printability check and print-orientation search (Prusa MK4 defaults).

Input: STL / 3MF / OBJ / PLY mesh, STEP, or a CadQuery .py script.

Checks
  * mesh health: watertight, consistent winding, positive volume, bodies,
    degenerate faces -- the things that make a slicer guess
  * build-volume fit (MK4/MK4S: 250 x 210 x 220 mm)
  * per orientation: height, bed-contact area, overhang area beyond the
    threshold, estimated support volume, tip-over ratio, and (with
    --load-axis) how much the main load pulls across the layers
  * thin walls / small features via inward ray casting (local thickness)

Outputs a ranked orientation table, optionally the re-oriented mesh
(-o part_oriented.stl / .3mf, placed on z=0) and a PNG overhang map.
The chosen orientation's build direction *in the original model
coordinates* is printed so it can be passed to fea.py --build-dir.

Examples
  uv run printability.py part.stl
  uv run printability.py bracket.py --load-axis x --png out/orient.png -o out/bracket.3mf
  uv run printability.py part.step --overhang 50 --nozzle 0.6 --json
  uv run printability.py part.stl --orientation "rx=90" -o out/part_rx90.stl

Exit status: 0 ok, 3 = problems found (non-manifold, does not fit, thin walls), 1/2 = error.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

BEDS = {
    "MK4": (250.0, 210.0, 220.0), "MK4S": (250.0, 210.0, 220.0), "MK3.9": (250.0, 210.0, 220.0),
    "COREONE": (250.0, 220.0, 270.0), "MINI": (180.0, 180.0, 180.0), "XL": (360.0, 360.0, 360.0),
}


# --------------------------------------------------------------------------- #
def load_mesh(path: Path, params: dict, tol: float) -> trimesh.Trimesh:
    suf = path.suffix.lower()
    if suf in (".stl", ".obj", ".ply", ".off", ".glb", ".3mf"):
        m = trimesh.load(str(path), force="mesh")
        return m
    import cadquery as cq
    if suf in (".step", ".stp"):
        shape = cq.importers.importStep(str(path)).val()
    elif suf == ".py":
        from cadquery import cqgi
        res = cqgi.parse(path.read_text()).build(build_parameters=params) if params else \
            cqgi.parse(path.read_text()).build()
        if not res.success:
            sys.exit(f"model script failed: {res.exception}")
        objs = [r.shape for r in res.results]
        if not objs:
            ns = {"__name__": "__prep__", "show_object": lambda *a, **k: None, "debug": lambda *a, **k: None}
            exec(compile(path.read_text(), str(path), "exec"), ns)
            objs = [ns[n] for n in ("result", "part", "model") if n in ns][:1]
        if not objs:
            sys.exit("script produced nothing (show_object(...) or `result`)")
        obj = objs[0]
        if isinstance(obj, cq.Assembly):
            obj = obj.toCompound()
        if isinstance(obj, cq.Workplane):
            obj = cq.Compound.makeCompound([v for v in obj.vals() if isinstance(v, cq.Shape)])
        shape = obj
    else:
        sys.exit(f"unsupported input {path}")
    tmp = Path(tempfile.mkdtemp()) / "m.stl"
    cq.exporters.export(shape, str(tmp), tolerance=tol, angularTolerance=0.1)
    return trimesh.load(str(tmp), force="mesh")


def parse_set(values):
    out = {}
    for item in values or []:
        k, _, v = item.partition("=")
        try:
            out[k.strip()] = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            out[k.strip()] = v
    return out


# --------------------------------------------------------------------------- #
def mesh_health(m: trimesh.Trimesh) -> dict:
    bodies = m.split(only_watertight=False)
    degenerate = int((m.area_faces < 1e-10).sum())
    return dict(
        faces=len(m.faces), watertight=bool(m.is_watertight), winding_consistent=bool(m.is_winding_consistent),
        volume_mm3=round(float(m.volume), 2) if m.is_watertight else None,
        area_mm2=round(float(m.area), 2), bodies=len(bodies), degenerate_faces=degenerate,
        volume_positive=bool(m.is_watertight and m.volume > 0),
    )


def rot_from_spec(spec: str) -> np.ndarray:
    """'rx=90,ry=0,rz=45' -> 4x4 (applied x, then y, then z)."""
    T = np.eye(4)
    for part in spec.split(","):
        if not part.strip():
            continue
        k, _, v = part.partition("=")
        axis = {"rx": [1, 0, 0], "ry": [0, 1, 0], "rz": [0, 0, 1]}[k.strip().lower()]
        T = trimesh.transformations.rotation_matrix(math.radians(float(v)), axis) @ T
    return T


def axis_candidates() -> list[tuple[str, np.ndarray]]:
    c = [("as modelled", np.eye(4))]
    for name, spec in (("rx=180", "rx=180"), ("rx=90", "rx=90"), ("rx=-90", "rx=-90"),
                       ("ry=90", "ry=90"), ("ry=-90", "ry=-90")):
        c.append((name, rot_from_spec(spec)))
    return c


def evaluate(m: trimesh.Trimesh, T: np.ndarray, overhang_deg: float, load_axis, bed_tol=0.05,
             ray_support=True) -> dict:
    mm = m.copy()
    mm.apply_transform(T)
    mm.apply_translation([0, 0, -mm.bounds[0, 2]])
    n = mm.face_normals
    a = mm.area_faces
    c = mm.triangles_center
    ext = mm.extents
    on_bed = (n[:, 2] < -0.999) & (c[:, 2] < bed_tol)
    bed_area = float(a[on_bed].sum())
    # overhang angle measured from vertical (0 = wall, 90 = flat ceiling)
    down = n[:, 2] < 0
    ang = np.degrees(np.arcsin(np.clip(-n[:, 2], 0, 1)))
    over = down & (ang > overhang_deg) & ~on_bed
    over_area = float(a[over].sum())
    proj = a * np.clip(-n[:, 2], 0, 1)
    support_vol = 0.0
    if over.any():
        if ray_support:
            origins = c[over] - np.array([0, 0, 1e-3])
            dirs = np.tile([0, 0, -1.0], (len(origins), 1))
            locs, idx_ray, _ = mm.ray.intersects_location(origins, dirs, multiple_hits=False)
            drop = c[over][:, 2].copy()  # default: down to the bed
            if len(idx_ray):
                drop[idx_ray] = origins[idx_ray, 2] - locs[:, 2]
            support_vol = float((proj[over] * drop).sum())
        else:
            support_vol = float((proj[over] * c[over][:, 2]).sum())
    flat_ceiling = float(a[down & (ang > 85) & ~on_bed].sum())
    # tip-over / adhesion: height vs. smallest footprint dimension
    footprint = min(ext[0], ext[1])
    tip_ratio = float(ext[2] / max(footprint, 1e-6))
    load_across = None
    if load_axis is not None:
        v = T[:3, :3] @ load_axis
        load_across = float(abs(v[2]) / np.linalg.norm(v))  # 1 = load pulls straight across layers
    # build direction expressed in the ORIGINAL model coordinates
    bdir = np.linalg.inv(T[:3, :3]) @ np.array([0, 0, 1.0])
    return dict(height=round(float(ext[2]), 2), extents=np.round(ext, 2).tolist(),
                bed_contact_mm2=round(bed_area, 1), overhang_mm2=round(over_area, 1),
                flat_ceiling_mm2=round(flat_ceiling, 1), support_volume_mm3=round(support_vol, 1),
                tip_ratio=round(tip_ratio, 2), load_across_layers=None if load_across is None else round(load_across, 3),
                build_dir_model=np.round(bdir, 4).tolist(), _mesh=mm, _over=over, _bed=on_bed)


def score(r: dict, vol: float, weights: dict) -> float:
    ref = max(vol, 1.0)
    s = weights["support"] * r["support_volume_mm3"] / ref
    s += weights["height"] * r["height"] / 100.0
    s += weights["bed"] * (1.0 if r["bed_contact_mm2"] < 50 else 0.0) + weights["bed"] * 0.3 * (r["bed_contact_mm2"] < 200)
    s += weights["tip"] * max(r["tip_ratio"] - 3.0, 0) / 3.0
    if r["load_across_layers"] is not None:
        s += weights["strength"] * r["load_across_layers"]
    return round(s, 3)


def thickness_check(m: trimesh.Trimesh, min_wall: float, samples: int = 4000, seed: int = 0) -> dict:
    """Local wall thickness by casting rays inward from sampled surface points."""
    rng = np.random.default_rng(seed)
    pts, fidx = trimesh.sample.sample_surface(m, samples, seed=seed) if "seed" in \
        trimesh.sample.sample_surface.__code__.co_varnames else trimesh.sample.sample_surface(m, samples)
    normals = m.face_normals[fidx]
    origins = pts - normals * 1e-3
    locs, ridx, _ = m.ray.intersects_location(origins, -normals, multiple_hits=False)
    th = np.full(len(pts), np.inf)
    if len(ridx):
        th[ridx] = np.linalg.norm(locs - origins[ridx], axis=1)
    finite = np.isfinite(th)
    thin = finite & (th < min_wall)
    out = dict(samples=int(finite.sum()), min_wall_mm=min_wall,
               min_thickness_mm=round(float(th[finite].min()), 3) if finite.any() else None,
               p5_thickness_mm=round(float(np.percentile(th[finite], 5)), 3) if finite.any() else None,
               thin_fraction=round(float(thin.sum() / max(finite.sum(), 1)), 4))
    if thin.any():
        out["thin_example_points"] = np.round(pts[thin][:5], 2).tolist()
    return out


def render(results: list[dict], path: Path, top: int = 3):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    sel = results[:top]
    fig = plt.figure(figsize=(5 * len(sel), 5))
    for k, r in enumerate(sel):
        mm = r["_mesh"]
        # subdivide long sliver triangles so matplotlib's painter sort works
        v, f, idx = trimesh.remesh.subdivide_to_size(mm.vertices, mm.faces, max_edge=mm.scale / 25,
                                                     max_iter=12, return_index=True)
        mm = trimesh.Trimesh(v, f, process=False)
        ax = fig.add_subplot(1, len(sel), k + 1, projection="3d")
        col = np.tile([0.78, 0.78, 0.78, 1.0], (len(mm.faces), 1))
        light = 0.55 + 0.45 * np.clip(mm.face_normals @ np.array([0.3, -0.5, 0.8]), 0, 1)
        col[:, :3] *= light[:, None]
        col[r["_over"][idx]] = (0.9, 0.15, 0.1, 1)
        col[r["_bed"][idx]] = (0.1, 0.65, 0.2, 1)
        ax.add_collection3d(Poly3DCollection(mm.triangles, facecolors=col, edgecolors="none"))
        lo, hi = mm.bounds
        cc, rr = (lo + hi) / 2, (hi - lo).max() / 2
        ax.set_xlim(cc[0] - rr, cc[0] + rr); ax.set_ylim(cc[1] - rr, cc[1] + rr); ax.set_zlim(0, 2 * rr)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=20, azim=-60)
        ax.set_title(f"#{k + 1} {r['name']}  score {r['score']}\nsupport {r['support_volume_mm3']:.0f} mm3, "
                     f"h {r['height']} mm, bed {r['bed_contact_mm2']:.0f} mm2", fontsize=9)
    fig.suptitle("green = on bed, red = overhang needing support", fontsize=10)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=90)
    plt.close(fig)


# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    ap.add_argument("--printer", default="MK4", choices=sorted(BEDS))
    ap.add_argument("--nozzle", type=float, default=0.4)
    ap.add_argument("--overhang", type=float, default=50.0,
                    help="max unsupported overhang, deg from vertical (50 = PrusaSlicer support_material_threshold 40)")
    ap.add_argument("--min-wall", type=float, help="flag walls thinner than this (default 2 x line width)")
    ap.add_argument("--load-axis", help="main load/tension direction in model coords (x, y, z or vector); "
                                        "orientations that pull layers apart are penalised")
    ap.add_argument("--orientation", help="evaluate only this rotation, e.g. 'rx=90,rz=45'")
    ap.add_argument("--stable", type=int, default=6, help="also try N most stable resting poses")
    ap.add_argument("--weights", default="support=1,height=0.2,bed=1,tip=0.5,strength=2")
    ap.add_argument("--tolerance", type=float, default=0.02, help="tessellation tolerance for STEP/.py")
    ap.add_argument("--no-thickness", action="store_true")
    ap.add_argument("-o", "--output", help="write best (or --orientation) mesh: .stl or .3mf")
    ap.add_argument("--png")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    m = load_mesh(Path(args.model), parse_set(args.set), args.tolerance)
    health = mesh_health(m)
    problems = []
    if not health["watertight"]:
        problems.append("mesh is not watertight (holes/non-manifold edges): slicer will guess. Re-export "
                        "from CAD, or repair (trimesh: fill_holes / PrusaSlicer: Fix by Windows repair)")
    if not health["winding_consistent"]:
        problems.append("inconsistent face winding (flipped normals)")
    if health["bodies"] > 1:
        problems.append(f"{health['bodies']} separate bodies: intended? (print-in-place / multi-part plate)")
    if health["degenerate_faces"]:
        problems.append(f"{health['degenerate_faces']} degenerate (zero-area) faces")
    if not health["watertight"]:
        m.fill_holes()
        trimesh.repair.fix_normals(m)

    w = {k: float(v) for k, v in (p.split("=") for p in args.weights.split(","))}
    load_axis = None
    if args.load_axis:
        named = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}
        load_axis = np.array(named.get(args.load_axis.lower().lstrip("+-"),
                                       [float(v) for v in args.load_axis.split(",")] if "," in args.load_axis else None),
                             dtype=float)
    cands = [("custom " + args.orientation, rot_from_spec(args.orientation))] if args.orientation else axis_candidates()
    if not args.orientation and args.stable and m.is_watertight:
        try:
            poses, probs = m.compute_stable_poses(n_samples=1, threshold=0.0)
            for i, (T, p) in enumerate(zip(poses[: args.stable], probs[: args.stable])):
                cands.append((f"stable#{i + 1} (p={p:.2f})", T))
        except Exception:
            pass
    vol = float(abs(m.volume)) if m.is_watertight else float(m.convex_hull.volume)
    bx, by, bz = BEDS[args.printer]
    results, seen = [], set()
    for name, T in cands:
        r = evaluate(m, T, args.overhang, load_axis)
        key = (tuple(np.round(r["build_dir_model"], 2)), r["height"])
        if key in seen:
            continue
        seen.add(key)
        r["name"] = name
        r["rotation_matrix"] = np.round(T[:3, :3], 5).tolist()
        e = sorted(r["extents"][:2])
        r["fits_bed"] = bool(r["height"] <= bz and ((e[1] <= max(bx, by) and e[0] <= min(bx, by))))
        r["score"] = score(r, vol, w) + (100 if not r["fits_bed"] else 0)
        results.append(r)
    results.sort(key=lambda r: r["score"])
    best = results[0]
    if not best["fits_bed"]:
        problems.append(f"does not fit the {args.printer} build volume {bx}x{by}x{bz} in any tried "
                        f"orientation: split the part (PrusaSlicer cut tool / model a joint)")

    th = None
    if not args.no_thickness and m.is_watertight:
        min_wall = args.min_wall or round(2 * args.nozzle * 1.125, 2)
        th = thickness_check(m, min_wall)
        if th["min_thickness_mm"] is not None and th["min_thickness_mm"] < args.nozzle:
            problems.append(f"features thinner than the nozzle ({th['min_thickness_mm']} mm < {args.nozzle}) "
                            "will not print at all")
        elif th["thin_fraction"] > 0.01:
            problems.append(f"{th['thin_fraction']:.1%} of the surface has walls < {min_wall} mm "
                            "(fewer than 2 perimeters: weak, may become gap fill)")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        mm = best["_mesh"].copy()
        lo, hi = mm.bounds
        mm.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
        mm.export(str(out))
    if args.png:
        render(results, Path(args.png))

    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]
    report = dict(model=args.model, printer=args.printer, build_volume=[bx, by, bz], health=health,
                  overhang_threshold_deg=args.overhang, orientations=clean, best=clean[0],
                  thickness=th, problems=problems, output=args.output, png=args.png)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        h = health
        print(f"mesh: {h['faces']} faces, watertight={h['watertight']}, winding_ok={h['winding_consistent']}, "
              f"bodies={h['bodies']}, volume={h['volume_mm3']} mm3")
        print(f"\norientations (overhang > {args.overhang:g} deg from vertical needs support; lower score = better)")
        hdr = f"{'#':>2} {'orientation':22s} {'score':>6} {'height':>7} {'bed mm2':>8} {'overh mm2':>9} " \
              f"{'support mm3':>11} {'tip':>5} {'load-x-layers':>13} {'fits':>5}  build dir (model)"
        print(hdr)
        for i, r in enumerate(clean):
            la = "-" if r["load_across_layers"] is None else f"{r['load_across_layers']:.2f}"
            print(f"{i + 1:>2} {r['name'][:22]:22s} {r['score']:6.2f} {r['height']:7.1f} {r['bed_contact_mm2']:8.0f} "
                  f"{r['overhang_mm2']:9.0f} {r['support_volume_mm3']:11.0f} {r['tip_ratio']:5.1f} {la:>13} "
                  f"{str(r['fits_bed']):>5}  {r['build_dir_model']}")
        b = clean[0]
        print(f"\nbest: {b['name']}  -> fea.py --build-dir {','.join(str(round(v, 4)) for v in b['build_dir_model'])}")
        if th:
            print(f"wall thickness: min {th['min_thickness_mm']} mm, 5th pct {th['p5_thickness_mm']} mm, "
                  f"{th['thin_fraction']:.1%} of samples < {th['min_wall_mm']} mm")
        for p in problems:
            print(f"PROBLEM: {p}")
        if args.output:
            print(f"oriented mesh -> {args.output} (centred, on z=0)")
        if args.png:
            print(f"png -> {args.png}")
    return 3 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
