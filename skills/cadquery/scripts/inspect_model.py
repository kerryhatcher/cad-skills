#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery"]
# ///
"""Build a CadQuery model script, show data about it, export it, and render previews.

The tool runs the model script through the CQGI layer of CadQuery:
  * It collects the ``show_object(obj, name=...)`` calls (the preferred method).
  * If the script shows nothing, the tool uses a top-level ``result`` variable
    (or ``assy``, ``part``, ``model``).
  * It does NOT run the code under ``if __name__ == "__main__":``.
  * You can change top-level constant assignments (``width = 40``) with --set.

Examples (run them from all directories. uv installs cadquery when necessary):

  uv run scripts/inspect_model.py model.py
  uv run scripts/inspect_model.py model.py --set width=60 --set holes=6
  uv run scripts/inspect_model.py model.py -o out/part.step -o out/part.stl
  uv run scripts/inspect_model.py model.py --png out/preview.png --views
  uv run scripts/inspect_model.py model.py --interference --json

The exit status is not 0 if the script fails, makes no shape, or makes a shape
that is not valid (the BRep check fails). Thus you can also use the tool as a CI check.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import sys
import traceback
from pathlib import Path

import cadquery as cq
from cadquery import cqgi

FALLBACK_NAMES = ("result", "assy", "assembly", "part", "model")


# --------------------------------------------------------------------------- #
# Building
# --------------------------------------------------------------------------- #
def parse_set(values: list[str]) -> dict:
    params = {}
    for item in values:
        if "=" not in item:
            sys.exit(f"--set must have the form name=value. The tool received {item!r}")
        k, v = item.split("=", 1)
        try:
            params[k.strip()] = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            params[k.strip()] = v  # use the value as a string
    return params


def build(path: Path, params: dict):
    src = path.read_text()
    model = cqgi.parse(src)
    unknown = set(params) - set(model.metadata.parameters)
    if unknown:
        known = ", ".join(sorted(model.metadata.parameters)) or "(none)"
        sys.exit(
            f"Unknown parameter(s) {sorted(unknown)}. "
            f"You can change these top-level constants: {known}"
        )

    # Relative paths in the script (for example importDXF("x.dxf")) must point to the
    # directory of the script. The script can then also import modules from that directory.
    old_cwd = os.getcwd()
    os.chdir(path.parent.resolve())
    sys.path.insert(0, str(path.parent.resolve()))
    try:
        res = model.build(build_parameters=params)
    finally:
        os.chdir(old_cwd)

    if not res.success:
        print(f"BUILD FAILED: {type(res.exception).__name__}: {res.exception}")
        if res.exception is not None and res.exception.__traceback__ is not None:
            traceback.print_exception(
                type(res.exception), res.exception, res.exception.__traceback__
            )
        sys.exit(2)

    objs = [(r.options.get("name") or f"object{i}", r.shape) for i, r in enumerate(res.results)]
    if not objs:
        env = getattr(res, "env", None) or {}
        for n in FALLBACK_NAMES:
            if n in env:
                objs = [(n, env[n])]
                break
    if not objs:
        # Some CQGI versions do not give the namespace. Run the script again without CQGI.
        ns: dict = {"__name__": "__cqgi__", "show_object": lambda *a, **k: None,
                    "debug": lambda *a, **k: None, "cq": cq}
        ns.update(params)
        os.chdir(path.parent.resolve())
        try:
            exec(compile(src, str(path), "exec"), ns)
        finally:
            os.chdir(old_cwd)
        for n in FALLBACK_NAMES:
            if n in ns:
                objs = [(n, ns[n])]
                break
    if not objs:
        sys.exit(
            "The script made no shape. Call show_object(obj), or set a "
            f"top-level variable with one of these names: {FALLBACK_NAMES}."
        )
    return objs, model.metadata.parameters


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def to_shape(obj):
    """Give a cq.Shape (a Compound for workplanes with many objects), or None."""
    if isinstance(obj, cq.Shape):
        return obj
    if isinstance(obj, cq.Workplane):
        shapes = [o for o in obj.vals() if isinstance(o, cq.Shape)]
        if not shapes:
            return None
        return shapes[0] if len(shapes) == 1 else cq.Compound.makeCompound(shapes)
    if isinstance(obj, cq.Sketch):
        faces = obj._faces
        return faces if faces is not None and not faces.isNull() else None
    if isinstance(obj, cq.Assembly):
        return obj.toCompound()
    return None


def r(x, nd=4):
    return round(x, nd) if isinstance(x, float) else x


def shape_report(shape: cq.Shape) -> dict:
    bb = shape.BoundingBox()
    rep = {
        "type": type(shape).__name__,
        "valid": shape.isValid(),
        "counts": {
            "solids": len(shape.Solids()),
            "shells": len(shape.Shells()),
            "faces": len(shape.Faces()),
            "edges": len(shape.Edges()),
            "vertices": len(shape.Vertices()),
        },
        "bbox": {
            "min": [r(bb.xmin), r(bb.ymin), r(bb.zmin)],
            "max": [r(bb.xmax), r(bb.ymax), r(bb.zmax)],
            "size": [r(bb.xlen), r(bb.ylen), r(bb.zlen)],
        },
    }
    solids = shape.Solids()
    if solids:
        vol = sum(s.Volume() for s in solids)
        rep["volume"] = r(vol)
        rep["area"] = r(shape.Area())
        try:
            c = cq.Shape.centerOfMass(shape)
            rep["center_of_mass"] = [r(c.x), r(c.y), r(c.z)]
        except Exception:
            pass
        if any(s.Volume() < 0 for s in solids):
            rep["warning"] = "negative solid volume (the orientation is inverted)"
    elif shape.Faces():
        rep["area"] = r(shape.Area())
    return rep


def assembly_report(assy: cq.Assembly, check_interference: bool) -> dict:
    parts = []
    shapes = []
    for name, sub in assy.traverse():
        if sub.obj is None:
            continue
        shp = to_shape(sub.obj)
        if shp is None:
            continue
        # global location = product of the locations from the root to this item
        loc = cq.Location()
        node = sub
        chain = []
        while node is not None:
            chain.append(node.loc)
            node = node.parent
        for l in reversed(chain):
            loc = loc * l
        placed = shp.moved(loc)
        shapes.append((name, placed))
        rep = shape_report(placed)
        rep["name"] = name
        t, rot = loc.toTuple()
        rep["location"] = {"translation": [r(v) for v in t], "rotation_deg": [r(v) for v in rot]}
        parts.append(rep)

    out = {"type": "Assembly", "name": assy.name, "parts": parts,
           "valid": all(p["valid"] for p in parts)}

    if check_interference:
        clashes = []
        for i in range(len(shapes)):
            for j in range(i + 1, len(shapes)):
                (na, a), (nb, b) = shapes[i], shapes[j]
                if not a.Solids() or not b.Solids():
                    continue
                if not _bbox_overlap(a.BoundingBox(), b.BoundingBox()):
                    continue
                try:
                    # Parts that touch give faces with a thickness of 0, but their Volume()
                    # is not 0. Thus count only the solids in the common part.
                    v = sum(abs(s.Volume()) for s in a.intersect(b).Solids())
                except Exception as e:  # a boolean failure also gives useful data
                    clashes.append({"a": na, "b": nb, "error": str(e)})
                    continue
                if v > 1e-6:
                    clashes.append({"a": na, "b": nb, "volume": r(v)})
        out["interference"] = clashes
    return out


def _bbox_overlap(a, b, tol=1e-9):
    return not (a.xmax < b.xmin - tol or b.xmax < a.xmin - tol or
                a.ymax < b.ymin - tol or b.ymax < a.ymin - tol or
                a.zmax < b.zmin - tol or b.zmax < a.zmin - tol)


def report(objs, check_interference: bool) -> list[dict]:
    reps = []
    for name, obj in objs:
        if isinstance(obj, cq.Assembly):
            rep = assembly_report(obj, check_interference)
        else:
            shp = to_shape(obj)
            if shp is None:
                rep = {"type": type(obj).__name__, "valid": False,
                       "error": "no shape on the stack (is an extrude() or a different 3D operation missing?)"}
            else:
                rep = shape_report(shp)
                if isinstance(obj, cq.Workplane) and len(obj.vals()) > 1:
                    rep["note"] = (f"workplane stack holds {len(obj.vals())} objects; "
                                   "reported as a compound")
        rep["name"] = name
        reps.append(rep)
    return reps


def print_human(reps, params, overrides):
    if params:
        print("Parameters (script defaults):",
              ", ".join(f"{k}={v.default_value!r}" for k, v in params.items()))
    if overrides:
        print("Overrides:", ", ".join(f"{k}={v!r}" for k, v in overrides.items()))
    for rep in reps:
        print(f"\n== {rep['name']} ({rep['type']}) valid={rep['valid']}")
        if rep["type"] == "Assembly":
            for p in rep["parts"]:
                print(f"  - {p['name']}: {p['type']} valid={p['valid']} "
                      f"size={p['bbox']['size']} vol={p.get('volume')} "
                      f"at={p['location']['translation']} rot={p['location']['rotation_deg']}")
            if "interference" in rep:
                if rep["interference"]:
                    print("  INTERFERENCE:")
                    for c in rep["interference"]:
                        print(f"    {c['a']} x {c['b']}: {c.get('volume', c.get('error'))}")
                else:
                    print("  interference: none")
            continue
        if "error" in rep:
            print("  ERROR:", rep["error"])
            continue
        for k in ("counts", "bbox", "volume", "area", "center_of_mass", "warning", "note"):
            if k in rep:
                print(f"  {k}: {rep[k]}")


# --------------------------------------------------------------------------- #
# Export & render
# --------------------------------------------------------------------------- #
def export(objs, outputs: list[str], tolerance: float, ang_tol: float):
    for out in outputs:
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        multi = len(objs) > 1
        for name, obj in objs:
            target = p.with_name(f"{p.stem}_{name}{p.suffix}") if multi else p
            ext = p.suffix.lower()
            if isinstance(obj, cq.Sketch):
                obj.export(str(target))
            elif ext in ASSY_EXT or isinstance(obj, cq.Assembly) and ext in (".step", ".stp"):
                # formats only for assemblies (or STEP of an assembly: keeps the names and colors)
                assy = obj if isinstance(obj, cq.Assembly) else \
                    cq.Assembly().add(to_shape(obj), name=name)
                assy.export(str(target), ASSY_EXT.get(ext) or "STEP",
                            tolerance=tolerance, angularTolerance=ang_tol)
            else:
                shp = obj.toCompound() if isinstance(obj, cq.Assembly) else obj
                cq.exporters.export(shp, str(target), SHAPE_EXT.get(ext),
                                    tolerance=tolerance, angularTolerance=ang_tol)
            print(f"exported {target}")


# extensions that cq.exporters.export cannot identify
SHAPE_EXT = {".stp": "STEP", ".json": "TJS", ".wrl": "VRML", ".bin": "BIN"}
# formats that only Assembly.export can write
ASSY_EXT = {".gltf": "GLTF", ".glb": "GLTF", ".xml": "XML", ".xbf": "XBF", ".vtkjs": "VTKJS"}


VIEWS = {
    # name: (direction from the target to the camera, view-up vector)
    "iso": ((1, -1, 1), (0, 0, 1)),
    "front": ((0, -1, 0), (0, 0, 1)),
    "back": ((0, 1, 0), (0, 0, 1)),
    "right": ((1, 0, 0), (0, 0, 1)),
    "left": ((-1, 0, 0), (0, 0, 1)),
    "top": ((0, 0, 1), (0, 1, 0)),
    "bottom": ((0, 0, -1), (0, -1, 0)),
}


DEFAULT_COLOR = (0.85, 0.65, 0.13, 1.0)  # goldenrod. Assemblies keep their colors


def _render_one(assy: cq.Assembly, target: Path, view: str, size: int):
    """Render one view off-screen with VTK. The camera shows the full model."""
    from cadquery.occ_impl.assembly import toVTKAssy
    from vtkmodules.vtkRenderingCore import (vtkRenderer, vtkRenderWindow,
                                             vtkWindowToImageFilter, vtkMapper)
    from vtkmodules.vtkIOImage import vtkPNGWriter
    import vtkmodules.vtkRenderingOpenGL2  # noqa: F401  (this import registers the GL backend)
    import vtkmodules.vtkInteractionStyle  # noqa: F401

    ren = vtkRenderer()
    for act in toVTKAssy(assy, color=DEFAULT_COLOR, edgecolor=(0, 0, 0, 1),
                         edges=True, linewidth=1.5, tolerance=1e-3):
        ren.AddActor(act)
    ren.SetBackground(1, 1, 1)
    from vtkmodules.vtkRenderingCore import vtkLightKit
    vtkLightKit().AddLightsToRenderer(ren)
    vtkMapper.SetResolveCoincidentTopologyToPolygonOffset()

    win = vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(size, size)

    d, up = VIEWS[view]
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(0, 0, 0)
    cam.SetPosition(*d)
    cam.SetViewUp(*up)
    cam.SetParallelProjection(view != "iso")
    ren.ResetCamera()  # keeps the view direction and shows all of the model
    cam.Zoom(0.95)
    ren.ResetCameraClippingRange()
    win.Render()

    w2i = vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.SetInputBufferTypeToRGB()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    writer = vtkPNGWriter()
    writer.SetFileName(str(target))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    win.Finalize()


def render(objs, png: str, views: list[str], size: int):
    assy = cq.Assembly()
    shapes = []
    for i, (name, obj) in enumerate(objs):
        if isinstance(obj, cq.Assembly):
            assy.add(obj, name=f"{name}_{i}")
            shapes.append(obj.toCompound())
        else:
            s = to_shape(obj)
            if s is not None:
                assy.add(s, name=f"{name}_{i}")
                shapes.append(s)
    if not shapes:
        print("nothing to render")
        return
    p = Path(png)
    p.parent.mkdir(parents=True, exist_ok=True)
    for v in views:
        target = p if len(views) == 1 else p.with_name(f"{p.stem}_{v}{p.suffix}")
        try:
            _render_one(assy, target, v, size)
            print(f"rendered {target}")
        except Exception as e:
            print(f"render failed for view {v}: {e}")
            _svg_fallback(shapes, target.with_suffix(".svg"), VIEWS[v][0])


def _svg_fallback(shapes, target: Path, d):
    comp = cq.Compound.makeCompound(shapes)
    cq.exporters.export(comp, str(target), opt={"projectionDir": d, "showHidden": False,
                                                "width": 600, "height": 600})
    print(f"wrote SVG fallback {target} (no display? Use: xvfb-run -a uv run ...)")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path, help="CadQuery model script (.py)")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE",
                    help="change a top-level constant (you can use this option many times)")
    ap.add_argument("-o", "--output", action="append", default=[],
                    help="export path (you can use this option many times). The extension sets the format: step stp stl 3mf "
                         "amf svg dxf vrml wrl vtp json(threejs) brep glb gltf xml xbf")
    ap.add_argument("--tolerance", type=float, default=0.01,
                    help="linear tolerance of the mesh for STL, 3MF and glTF (default 0.01)")
    ap.add_argument("--angular-tolerance", type=float, default=0.1)
    ap.add_argument("--png", help="render a PNG preview (if there is no display, use xvfb-run -a)")
    ap.add_argument("--views", action="store_true",
                    help="with --png, render the iso, front, top and right views as different files")
    ap.add_argument("--view", action="append", choices=sorted(VIEWS),
                    help="the view or views to render with --png")
    ap.add_argument("--size", type=int, default=800, help="PNG size in px")
    ap.add_argument("--interference", action="store_true",
                    help="for assemblies, show the volumes where parts overlap")
    ap.add_argument("--json", action="store_true", help="report in JSON format")
    args = ap.parse_args()

    if not args.script.exists():
        sys.exit(f"the file does not exist: {args.script}")

    overrides = parse_set(args.set)
    objs, params = build(args.script, overrides)
    reps = report(objs, args.interference)

    if args.json:
        print(json.dumps({"parameters": {k: v.default_value for k, v in params.items()},
                          "overrides": overrides, "objects": reps}, indent=2, default=str))
    else:
        print_human(reps, params, overrides)

    if args.output:
        export(objs, args.output, args.tolerance, args.angular_tolerance)

    sys.stdout.flush()
    if args.png:
        views = args.view or (["iso", "front", "top", "right"] if args.views else ["iso"])
        render(objs, args.png, views, args.size)

    ok = all(rep.get("valid") for rep in reps) and not any(
        rep.get("interference") for rep in reps)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
