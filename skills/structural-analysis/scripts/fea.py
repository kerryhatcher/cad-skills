#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["cadquery", "gmsh", "scikit-fem>=10", "meshio", "matplotlib", "pyamg"]
# ///
"""Linear static FEA of a solid part, with strength checks for FDM parts.

Sequence: CadQuery script, STEP or BREP -> gmsh tetrahedral mesh -> scikit-fem
(quadratic P2 tetrahedra, linear elasticity) -> displacement, von Mises stress,
stress normal to the print layers -> safety factors, PNG, VTU (ParaView).

Face selection (for --fix, --force, --pressure). SEL is one of these:
  >Z  <X  %CYLINDER  ">Z and %PLANE"   a CadQuery face selector string
  face:3  or  face:3,7,8               face numbers from --list-faces
  box:x0,y0,z0,x1,y1,z1               faces with a bounding box in this box
  near:x,y,z                           the one face nearest to a point
Add @xyz components to --fix to hold only these directions (roller, symmetry):
  --fix "<Z@z"   (fixed only in Z)

Examples
  uv run fea.py bracket.py --list-faces
  uv run fea.py bracket.py --material prusament-petg --fix "<X" \\
      --force ">X=0,0,-50" --build-dir z --png out/fea.png
  uv run fea.py hook.step --material jessie-pla --fix "face:4" \\
      --pressure "face:9=0.5" --sf-target 3 --json
  uv run fea.py beam.py --fix "<X" --force ">X=0,0,-10" --convergence

Units: mm, N, MPa (N/mm^2). A force is the TOTAL force in newtons. The tool divides it
equally on the selected faces. The pressure is in MPa. A positive pressure pushes into the surface.

Exit status: 0 = the analysis is complete and the safety factors are >= --sf-target.
3 = the analysis is complete, but a safety factor is below the target.
1 or 2 = error (bad input, model not constrained, mesh failure).
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

# Properties of printed specimens (100 % infill, 0.2 mm layers). E and yield are
# in-plane values (along the extrusion). "z" is the interlayer tensile strength
# (across the layers). Prusament values: Prusa Polymers TDS (ISO 527-1, Prusa method).
# Jessie (Printed Solid) does not publish a TDS. Thus its values are conservative estimates.
MATERIALS = {
    "prusament-pla":      dict(E=2300, nu=0.35, yield_xy=51, z=17, hdt=55, rho=1.24, source="Prusament PLA TDS"),
    "prusament-pla-blend": dict(E=2300, nu=0.35, yield_xy=51, z=17, hdt=55, rho=1.24, source="Prusament PLA TDS (PLA/PLA Blend)"),
    "prusament-petg":     dict(E=1500, nu=0.38, yield_xy=47, z=18, hdt=68, rho=1.27, source="Prusament PETG TDS"),
    "prusament-asa":      dict(E=1600, nu=0.35, yield_xy=42, z=11, hdt=93, rho=1.07, source="Prusament ASA TDS"),
    "prusament-pc-blend": dict(E=1900, nu=0.37, yield_xy=63, z=21, hdt=113, rho=1.22, source="Prusament PC Blend TDS"),
    "jessie-pla":         dict(E=2200, nu=0.35, yield_xy=45, z=14, hdt=55, rho=1.24, source="ESTIMATE - no Printed Solid TDS. Do a coupon test before you use it"),
    "jessie-petg":        dict(E=1500, nu=0.38, yield_xy=42, z=14, hdt=68, rho=1.27, source="ESTIMATE - no Printed Solid TDS. Do a coupon test before you use it"),
    "generic-pla":        dict(E=2200, nu=0.35, yield_xy=40, z=12, hdt=52, rho=1.24, source="conservative generic"),
    "generic-petg":       dict(E=1400, nu=0.38, yield_xy=38, z=12, hdt=65, rho=1.27, source="conservative generic"),
    "generic-abs":        dict(E=1800, nu=0.35, yield_xy=33, z=10, hdt=85, rho=1.04, source="conservative generic"),
    "generic-asa":        dict(E=1600, nu=0.35, yield_xy=35, z=9,  hdt=90, rho=1.07, source="conservative generic"),
    "generic-pc":         dict(E=1900, nu=0.37, yield_xy=55, z=18, hdt=110, rho=1.20, source="conservative generic"),
}
ALIASES = {"pla": "prusament-pla", "petg": "prusament-petg", "asa": "prusament-asa",
           "pc": "prusament-pc-blend", "pc-blend": "prusament-pc-blend", "abs": "generic-abs"}
FALLBACK_NAMES = ("result", "part", "model", "assy", "assembly")


# --------------------------------------------------------------------------- #
# Load the geometry
# --------------------------------------------------------------------------- #
def parse_set(values):
    out = {}
    for item in values or []:
        k, _, v = item.partition("=")
        try:
            out[k.strip()] = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            out[k.strip()] = v
    return out


def load_shape(path: Path, params: dict):
    import cadquery as cq
    suf = path.suffix.lower()
    if suf in (".step", ".stp"):
        return cq.importers.importStep(str(path)).val()
    if suf == ".brep":
        return cq.Shape.importBrep(str(path))
    if suf in (".stl", ".3mf", ".obj"):
        sys.exit("FEA must have exact solid geometry. Give the CadQuery .py file or a STEP file, not a mesh.")
    if suf != ".py":
        sys.exit(f"this input type is not supported: {path}")
    from cadquery import cqgi
    model = cqgi.parse(path.read_text())
    res = model.build(build_parameters=params) if params else model.build()
    if not res.success:
        raise SystemExit(f"the model script failed: {res.exception}")
    objs = [r.shape for r in res.results]
    if not objs:
        ns = {"__name__": "__fea__", "show_object": lambda *a, **k: None, "debug": lambda *a, **k: None}
        cwd = os.getcwd()
        os.chdir(path.parent)
        try:
            exec(compile(path.read_text(), str(path), "exec"), ns)
        finally:
            os.chdir(cwd)
        objs = [ns[n] for n in FALLBACK_NAMES if n in ns][:1]
    if not objs:
        sys.exit("the script made no shape: call show_object(part) or set `result`")
    obj = objs[0]
    if isinstance(obj, cq.Assembly):
        obj = obj.toCompound()
    if isinstance(obj, cq.Workplane):
        vals = [v for v in obj.vals() if isinstance(v, cq.Shape)]
        obj = vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    solids = obj.Solids()
    if len(solids) != 1:
        if len(solids) == 0:
            sys.exit("the model has no solid")
        print(f"warning: {len(solids)} solids. The tool fuses them (parts that touch become one body)", file=sys.stderr)
        fused = solids[0]
        for s in solids[1:]:
            fused = fused.fuse(s)
        obj = fused.clean()
        solids = obj.Solids()
        if len(solids) != 1:
            sys.exit("the model has many solids that are not connected. Analyze each solid separately")
    return solids[0]


def face_info(shape):
    out = []
    for i, f in enumerate(shape.Faces()):
        c = f.Center()
        bb = f.BoundingBox()
        try:
            n = f.normalAt()
            n = (round(n.x, 3), round(n.y, 3), round(n.z, 3))
        except Exception:
            n = None
        out.append(dict(index=i, type=f.geomType(), area=f.Area(), center=(c.x, c.y, c.z),
                        normal=n, bbox=(bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)))
    return out


def select_faces(shape, sel: str) -> list[int]:
    """Give the face numbers (in shape.Faces()) for a selector string."""
    import cadquery as cq
    faces = shape.Faces()
    sel = sel.strip()
    if sel.startswith("face:"):
        idx = [int(x) for x in sel[5:].split(",") if x.strip()]
        bad = [i for i in idx if i < 0 or i >= len(faces)]
        if bad:
            sys.exit(f"this face number is not in the model: {bad} (the model has {len(faces)} faces)")
        return idx
    if sel.startswith("box:"):
        x0, y0, z0, x1, y1, z1 = (float(v) for v in sel[4:].split(","))
        eps = 1e-6
        hits = [i for i, f in enumerate(faces) if (lambda b: b.xmin >= x0 - eps and b.ymin >= y0 - eps and
                b.zmin >= z0 - eps and b.xmax <= x1 + eps and b.ymax <= y1 + eps and b.zmax <= z1 + eps)(f.BoundingBox())]
    elif sel.startswith("near:"):
        p = cq.Vector(*(float(v) for v in sel[5:].split(",")))
        v = cq.Vertex.makeVertex(p.x, p.y, p.z)
        hits = [min(range(len(faces)), key=lambda i: faces[i].distance(v))]
    else:
        chosen = cq.Workplane().add(shape).faces(sel).vals()
        hashes = {c.hashCode() for c in chosen}
        hits = [i for i, f in enumerate(faces) if f.hashCode() in hashes or any(f.isSame(c) for c in chosen)]
    if not hits:
        sys.exit(f"selector {sel!r} found no faces. Use --list-faces to see the face numbers")
    return hits


# --------------------------------------------------------------------------- #
# Make the mesh
# --------------------------------------------------------------------------- #
def mesh_shape(shape, size: float, curv: int, quiet=True):
    """Make a tetrahedral mesh with gmsh. Gives points (N,3), tets (M,4), {face_index: tris (K,3)}."""
    import gmsh
    tmp = Path(tempfile.mkdtemp()) / "part.brep"
    shape.exportBrep(str(tmp))
    gmsh.initialize(interruptible=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0 if quiet else 1)
        gmsh.model.add("part")
        gmsh.model.occ.importShapes(str(tmp))
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.option.setNumber("Mesh.MeshSizeMin", size / 6)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", curv)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.Optimize", 1)
        gmsh.model.mesh.generate(3)

        # Find the CadQuery face for each gmsh surface from the centroid and the area.
        cq_faces = shape.Faces()
        cq_c = np.array([[f.Center().x, f.Center().y, f.Center().z] for f in cq_faces])
        cq_a = np.array([f.Area() for f in cq_faces])
        scale = max(np.ptp(cq_c, axis=0).max(), 1.0)
        surf_to_face = {}
        for dim, tag in gmsh.model.getEntities(2):
            c = np.array(gmsh.model.occ.getCenterOfMass(dim, tag))
            a = gmsh.model.occ.getMass(dim, tag)
            score = np.linalg.norm(cq_c - c, axis=1) / scale + np.abs(cq_a - a) / np.maximum(cq_a, 1e-9)
            surf_to_face[tag] = int(np.argmin(score))

        ntags, coords, _ = gmsh.model.mesh.getNodes()
        pts = coords.reshape(-1, 3)
        idx = np.full(int(ntags.max()) + 1, -1, dtype=np.int64)
        idx[ntags.astype(np.int64)] = np.arange(len(ntags))
        tets = []
        for dim, tag in gmsh.model.getEntities(3):
            types, _, nodes = gmsh.model.mesh.getElements(dim, tag)
            for t, n in zip(types, nodes):
                if t == 4:  # 4-node tetrahedron
                    tets.append(idx[n.astype(np.int64)].reshape(-1, 4))
        tris = {}
        for dim, tag in gmsh.model.getEntities(2):
            types, _, nodes = gmsh.model.mesh.getElements(dim, tag)
            for t, n in zip(types, nodes):
                if t == 2:
                    f = surf_to_face[tag]
                    tris.setdefault(f, []).append(idx[n.astype(np.int64)].reshape(-1, 3))
        tris = {k: np.vstack(v) for k, v in tris.items()}
    finally:
        gmsh.finalize()
    if not tets:
        raise SystemExit("gmsh made no tetrahedra (is the solid closed and valid?)")
    tets = np.vstack(tets)
    used = np.unique(tets)
    remap = np.full(len(pts), -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    return pts[used], remap[tets], {k: remap[v] for k, v in tris.items()}


# --------------------------------------------------------------------------- #
# Solve
# --------------------------------------------------------------------------- #
def parse_vec(s: str) -> np.ndarray:
    v = np.array([float(x) for x in s.split(",")])
    if v.shape != (3,):
        raise SystemExit(f"the value must be fx,fy,fz. The tool received {s!r}")
    return v


def build_dir(s: str) -> np.ndarray:
    named = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
    s = s.strip().lower()
    if s.lstrip("+-") in named:
        v = np.array(named[s.lstrip("+-")], float)
        return -v if s.startswith("-") else v
    v = parse_vec(s)
    return v / np.linalg.norm(v)


def solve(pts, tets, tris, bcs, mat, bdir, size):
    from skfem import (Basis, ElementTetP1, ElementTetP2, ElementVector, FacetBasis,
                       Functional, LinearForm, MeshTet, asm, condense, solve as sksolve)
    from skfem.helpers import dot
    from skfem.models.elasticity import lame_parameters, linear_elasticity

    m = MeshTet(pts.T.copy(), tets.T.copy())
    # facet table: sorted node triple -> facet number
    fac = np.sort(m.facets, axis=0).T
    bfac = m.boundary_facets()
    lut = {tuple(fac[i]): i for i in bfac}

    def facets_for(face_ids):
        out = []
        for f in face_ids:
            for tri in tris.get(f, ()):
                k = tuple(sorted(tri))
                if k in lut:
                    out.append(lut[k])
        return np.unique(np.array(out, dtype=np.int64))

    e = ElementVector(ElementTetP2())
    ib = Basis(m, e, intorder=2)  # exact integration for P2 stiffness
    lam, mu = lame_parameters(mat["E"], mat["nu"])
    K = asm(linear_elasticity(lam, mu), ib)
    f = np.zeros(K.shape[0])

    @Functional
    def unit(w):
        return 1.0 + 0.0 * w.x[0]

    applied = np.zeros(3)
    marks = {"fixed": [], "loaded": []}
    for kind, faces, val in bcs:
        fids = facets_for(faces)
        if len(fids) == 0:
            raise SystemExit(f"no mesh facets on faces {faces} (the tool did not find the mesh faces)")
        fb = FacetBasis(m, e, facets=fids, intorder=4)
        area = asm(unit, FacetBasis(m, ElementTetP1(), facets=fids))
        if kind == "force":
            t = val / area

            @LinearForm
            def trac(v, w, t=t):
                return t[0] * v[0] + t[1] * v[1] + t[2] * v[2]

            f += asm(trac, fb)
            applied += val
            marks["loaded"].append(fids)
        elif kind == "pressure":
            p = float(val)

            @LinearForm
            def pres(v, w, p=p):
                return -p * dot(w.n, v)

            f += asm(pres, fb)
            applied += np.array([asm(Functional(lambda w, i=i, p=p: -p * w.n[i]),
                                     FacetBasis(m, ElementTetP1(), facets=fids)) for i in range(3)])
            marks["loaded"].append(fids)
    D = []
    for kind, faces, comps in bcs:
        if kind != "fix":
            continue
        fids = facets_for(faces)
        dofs = ib.get_dofs(facets=fids)
        names = [f"u^{'xyz'.index(c) + 1}" for c in comps]
        D.append(dofs.all(names) if len(names) < 3 else dofs.all())
        marks["fixed"].append(fids)
    if not D:
        raise SystemExit("no --fix option: the part is not constrained")
    D = np.unique(np.concatenate(D))

    ndof = K.shape[0]
    t0 = time.time()
    if ndof - len(D) > 150_000:
        import pyamg
        from scipy.sparse.linalg import cg
        A, b, x0, I = condense(K, f, D=D)
        # rigid-body modes as near-null space: AMG must have them for elasticity
        X = ib.doflocs
        B = np.zeros((ndof, 6))
        comp = [ib.get_dofs().all(f"u^{c + 1}") for c in range(3)]
        for c in range(3):
            B[comp[c], c] = 1.0
        x_, y_, z_ = X
        B[comp[0], 3], B[comp[1], 3] = -y_[comp[0]], x_[comp[1]]
        B[comp[1], 4], B[comp[2], 4] = -z_[comp[1]], y_[comp[2]]
        B[comp[2], 5], B[comp[0], 5] = -x_[comp[2]], z_[comp[0]]
        ml = pyamg.smoothed_aggregation_solver(A.tocsr(), B=B[I], symmetry="symmetric")
        xi, info = cg(A, b, M=ml.aspreconditioner(), rtol=1e-8, maxiter=3000)
        if info != 0:
            raise SystemExit("the iterative solver did not converge (is the model under-constrained?)")
        u = np.zeros(ndof)
        u[I] = xi
    else:
        u = sksolve(*condense(K, f, D=D))
    t_solve = time.time() - t0
    if not np.all(np.isfinite(u)):
        raise SystemExit("the solution is not finite: the model is under-constrained (add --fix, examine the selectors)")

    reaction = (K @ u - f)[D]  # force from the supports on the part
    rx = np.zeros(3)
    for c in range(3):
        sel = np.isin(D, ib.get_dofs().all(f"u^{c + 1}"))
        rx[c] = reaction[sel].sum()

    # stresses at quadrature points
    uh = ib.interpolate(u)
    G = uh.grad  # (3,3,nel,nqp)
    eps = 0.5 * (G + np.transpose(G, (1, 0, 2, 3)))
    tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
    sig = 2 * mu * eps
    for i in range(3):
        sig[i, i] += lam * tr
    s = sig
    vm = np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2)
                 + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[2, 0] ** 2))
    n = bdir
    sn = np.einsum("i,ijkl,j->kl", n, s, n)                # normal stress across layers
    tvec = np.einsum("ijkl,j->ikl", s, n)
    tau = np.sqrt(np.maximum((tvec ** 2).sum(0) - sn ** 2, 0))  # interlayer shear
    # principal stresses (maximum principal) at each quadrature point
    S = np.transpose(s, (2, 3, 0, 1))
    pmax = np.linalg.eigvalsh(S)[..., -1]

    vol = ib.dx  # (nel,nqp) quadrature weights * |J|
    disp = u[ib.nodal_dofs].T  # (Nnodes,3) at P1 vertices
    p1 = Basis(m, ElementTetP1(), intorder=2)
    nodal = {k: p1.project(v) for k, v in
             (("von_mises", vm), ("layer_normal", sn), ("layer_shear", tau), ("max_principal", pmax))}
    # Elements at more than one element size from all fixed or loaded faces. The stresses
    # at ideal supports and loads are not correct (Saint-Venant). Thus the design
    # values below ignore them. The report also gives the raw peaks.
    from scipy.spatial import cKDTree
    bc_nodes = np.unique(np.concatenate([m.facets[:, f].ravel() for f in marks["fixed"] + marks["loaded"]]))
    dist, _ = cKDTree(m.p[:, bc_nodes].T).query(m.p.T)
    far = dist > size
    if far.sum() < 0.2 * len(far):  # the part is very small relative to the mesh: use all elements
        far[:] = True
    return dict(mesh=m, u=disp, ndof=ndof, nfixed=len(D), t_solve=t_solve, applied=applied,
                reaction=rx, vm=nodal["von_mises"], sn=nodal["layer_normal"], tau=nodal["layer_shear"],
                pmax=nodal["max_principal"],
                vol=vol.sum(1), nodal=nodal, marks=marks, far=far)


def design_max(vals, far):
    """Maximum value of the elements that are away from the boundary-condition faces."""
    return float(vals[far].max())


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def render_png(res, path: Path, bdir, title=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    m = res["mesh"]
    p = m.p.T
    bf = m.boundary_facets()
    tri = m.facets[:, bf].T
    u = res["u"]
    span = np.ptp(p, axis=0).max()
    umax = np.linalg.norm(u, axis=1).max()
    scale = 0.08 * span / umax if umax > 0 else 0
    pd = p + scale * u
    fixed = np.concatenate(res["marks"]["fixed"]) if res["marks"]["fixed"] else np.array([], int)
    loaded = np.concatenate(res["marks"]["loaded"]) if res["marks"]["loaded"] else np.array([], int)

    panels = [("Boundary conditions (blue fixed, red loaded)", None, p),
              (f"von Mises [MPa] (deformed x{scale:.3g})", res["nodal"]["von_mises"], pd),
              ("von Mises, opposite view", res["nodal"]["von_mises"], pd),
              ("Stress normal to layers [MPa] (+ = peeling)", res["nodal"]["layer_normal"], pd)]
    fig = plt.figure(figsize=(14, 11))
    for k, (ttl, field, P) in enumerate(panels):
        ax = fig.add_subplot(2, 2, k + 1, projection="3d")
        polys = P[tri]
        if field is None:
            col = np.full((len(bf), 4), (0.8, 0.8, 0.8, 1.0))
            col[np.isin(bf, fixed)] = (0.15, 0.35, 0.95, 1)
            col[np.isin(bf, loaded)] = (0.95, 0.2, 0.15, 1)
            pc = Poly3DCollection(polys, facecolors=col, edgecolors=(0, 0, 0, 0.08), linewidths=0.2)
        else:
            fv = field[tri].mean(1)
            if k == 3:
                lim = max(abs(fv).max(), 1e-9)
                cmap, vmin, vmax = "coolwarm", -lim, lim
            else:
                cmap, vmin, vmax = "turbo", 0, max(np.percentile(fv, 99.5), 1e-9)
            pc = Poly3DCollection(polys, cmap=cmap, edgecolors="none")
            pc.set_array(fv)
            pc.set_clim(vmin, vmax)
            fig.colorbar(pc, ax=ax, shrink=0.6, pad=0.08)
        ax.add_collection3d(pc)
        lo, hi = P.min(0), P.max(0)
        c, r = (lo + hi) / 2, (hi - lo).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=25, azim=-60 if k != 2 else 120)
        ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
        ax.set_title(ttl, fontsize=10)
    fig.suptitle(title + f"   build dir = {np.round(bdir, 3).tolist()}", fontsize=11)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=90)
    plt.close(fig)


def write_vtu(res, path: Path):
    import meshio
    m = res["mesh"]
    pdata = {"displacement": res["u"], **{k: v for k, v in res["nodal"].items()}}
    path.parent.mkdir(parents=True, exist_ok=True)
    meshio.write(str(path), meshio.Mesh(m.p.T, [("tetra", m.t.T)], point_data=pdata))


# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", help="CadQuery .py, .step or .brep file")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE", help="change a script parameter")
    ap.add_argument("--list-faces", action="store_true", help="show the face numbers, centers and normals, then stop")
    ap.add_argument("--list-materials", action="store_true")
    ap.add_argument("--material", default="prusament-pla")
    ap.add_argument("--E", type=float, help="use this Young's modulus [MPa]")
    ap.add_argument("--nu", type=float, help="use this Poisson's ratio")
    ap.add_argument("--yield", dest="yield_", type=float, help="use this in-plane yield strength [MPa]")
    ap.add_argument("--z-strength", type=float, help="use this interlayer tensile strength [MPa]")
    ap.add_argument("--fix", action="append", default=[], metavar="SEL[@xyz]")
    ap.add_argument("--force", action="append", default=[], metavar="SEL=fx,fy,fz", help="total force [N]")
    ap.add_argument("--pressure", action="append", default=[], metavar="SEL=p", help="pressure [MPa]")
    ap.add_argument("--build-dir", default="z", help="direction of the print layer stack in model coordinates: z, -y, x, or vector")
    ap.add_argument("--size", type=float, help="maximum element size [mm] (default: shortest bbox side / 4, with a limit)")
    ap.add_argument("--curvature", type=int, default=12, help="elements for each 2*pi of curvature (0 = off)")
    ap.add_argument("--sf-target", type=float, default=2.0, help="necessary safety factor (default 2)")
    ap.add_argument("--convergence", action="store_true", help="solve with 3 mesh sizes and compare the results")
    ap.add_argument("--png", help="write a PNG with 4 panels (BCs, von Mises x2, stress normal to the layers)")
    ap.add_argument("--vtu", help="write results for ParaView")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.list_materials:
        for k, v in MATERIALS.items():
            print(f"{k:20s} E={v['E']:5.0f} nu={v['nu']} yield_xy={v['yield_xy']:3.0f} "
                  f"z={v['z']:3.0f} HDT={v['hdt']}C  [{v['source']}]")
        return 0

    shape = load_shape(Path(args.model), parse_set(args.set))
    if not shape.isValid():
        print("warning: the solid fails the BRep validity check. The mesh can fail", file=sys.stderr)
    if args.list_faces:
        bb = shape.BoundingBox()
        print(f"bbox x[{bb.xmin:.2f},{bb.xmax:.2f}] y[{bb.ymin:.2f},{bb.ymax:.2f}] z[{bb.zmin:.2f},{bb.zmax:.2f}]  "
              f"volume {shape.Volume():.1f} mm3")
        for fi in face_info(shape):
            c = ", ".join(f"{v:.2f}" for v in fi["center"])
            print(f"face:{fi['index']:<4d} {fi['type']:10s} area={fi['area']:9.2f}  centre=({c})  normal={fi['normal']}")
        return 0

    key = ALIASES.get(args.material.lower(), args.material.lower())
    if key not in MATERIALS:
        sys.exit(f"unknown material {args.material!r}. Use --list-materials")
    mat = dict(MATERIALS[key])
    for k, v in (("E", args.E), ("nu", args.nu), ("yield_xy", args.yield_), ("z", args.z_strength)):
        if v is not None:
            mat[k] = v
            mat["source"] += f"; {k} overridden"

    bcs = []
    for s in args.fix:
        sel, _, comps = s.partition("@")
        comps = comps.lower() or "xyz"
        bcs.append(("fix", select_faces(shape, sel), comps))
    for s in args.force:
        sel, _, vec = s.rpartition("=")
        bcs.append(("force", select_faces(shape, sel), parse_vec(vec)))
    for s in args.pressure:
        sel, _, p = s.rpartition("=")
        bcs.append(("pressure", select_faces(shape, sel), float(p)))
    if not any(b[0] == "fix" for b in bcs):
        sys.exit("give one --fix option or more")
    if not any(b[0] in ("force", "pressure") for b in bcs):
        sys.exit("give one --force or --pressure option or more")
    fixed_faces = {f for b in bcs if b[0] == "fix" for f in b[1]}
    loaded_faces = {f for b in bcs if b[0] != "fix" for f in b[1]}
    if fixed_faces & loaded_faces:
        print(f"warning: faces {sorted(fixed_faces & loaded_faces)} are fixed and loaded at the same time", file=sys.stderr)

    bdir = build_dir(args.build_dir)
    bb = shape.BoundingBox()
    dims = sorted([bb.xlen, bb.ylen, bb.zlen])
    size = args.size or max(min(dims[0] / 4, dims[2] / 20), 0.3)

    sizes = [size * 2, size * 1.41, size] if args.convergence else [size]
    runs = []
    for sz in sizes:
        t0 = time.time()
        pts, tets, tris = mesh_shape(shape, sz, args.curvature)
        res = solve(pts, tets, tris, bcs, mat, bdir, sz)
        vm_r = design_max(res["vm"], res["far"])
        runs.append(dict(size=round(sz, 3), nodes=len(pts), tets=len(tets), dofs=res["ndof"],
                         max_disp=float(np.linalg.norm(res["u"], axis=1).max()),
                         vm_max=float(res["vm"].max()), vm_design=vm_r,
                         seconds=round(time.time() - t0, 1)))
    r = runs[-1]
    umag = np.linalg.norm(res["u"], axis=1)
    imax = int(np.argmax(umag))
    m = res["mesh"]
    vm_max, vm_rob = float(res["vm"].max()), design_max(res["vm"], res["far"])
    sn_max = float(max(res["sn"].max(), 0.0))
    sn_rob = max(design_max(res["sn"], res["far"]), 0.0)
    tau_rob = design_max(res["tau"], res["far"])
    ielem = int(np.argmax(np.where(res["far"], res["vm"], -np.inf)))
    loc = m.p[:, ielem]
    isn = int(np.argmax(np.where(res["far"], res["sn"], -np.inf)))
    loc_sn = m.p[:, isn]
    sf_xy = mat["yield_xy"] / vm_rob if vm_rob > 0 else math.inf
    sf_z = mat["z"] / sn_rob if sn_rob > 0 else math.inf
    sf_shear = (0.6 * mat["z"]) / tau_rob if tau_rob > 0 else math.inf  # interlayer shear strength ~ 0.6 x interlayer tensile strength (estimate)
    sf = min(sf_xy, sf_z, sf_shear)
    applied, reaction = res["applied"], res["reaction"]
    eq_err = float(np.linalg.norm(applied + reaction) / max(np.linalg.norm(applied), 1e-12))
    span = float(max(bb.xlen, bb.ylen, bb.zlen))

    notes = []
    if vm_max > 1.5 * vm_rob:
        notes.append("the raw peak von Mises (at a fixed or loaded face) is >1.5x the design value. The ideal support "
                     "causes this peak. If the actual support or load is that concentrated, make a more accurate model of it.")
    if args.convergence and len(runs) >= 2 and runs[-1]["vm_design"] > 1.15 * runs[-2]["vm_design"]:
        notes.append("the design stress continues to increase with a finer mesh: a sharp re-entrant corner (singularity). "
                     "Add a fillet there. The value at a sharp corner has no meaning.")
    if eq_err > 0.02:
        notes.append(f"equilibrium error {eq_err:.1%}: examine the loads and the mesh")
    if r["max_disp"] > 0.05 * span:
        notes.append("displacement > 5% of the part dimension: the linear analysis is not accurate (large deflection). "
                     "Use the results only to compare designs, and make the design stiffer")
    if "ESTIMATE" in mat["source"]:
        notes.append(f"{key}: no data sheet from the manufacturer. The strengths are estimates. Print and test coupons")
    if min(sf_z, sf_shear) < sf_xy:
        notes.append("layer adhesion governs: turn the part so that the load does not pull the layers apart, "
                     "or add perimeters, or increase the temperature")
    if args.convergence and len(runs) >= 2:
        d = abs(runs[-1]["vm_design"] - runs[-2]["vm_design"]) / max(runs[-1]["vm_design"], 1e-12)
        notes.append(f"mesh convergence: the design von Mises stress changed {d:.1%} with the last refinement "
                     + ("(converged)" if d < 0.05 else "(NOT converged: make the mesh finer with --size)"))

    report = dict(
        model=str(args.model), material=key, material_props=mat,
        build_dir=np.round(bdir, 4).tolist(),
        mesh=dict(size=r["size"], nodes=r["nodes"], tets=r["tets"], dofs=r["dofs"], element="P2 tetra"),
        applied_force_N=np.round(applied, 4).tolist(), reaction_N=np.round(reaction, 4).tolist(),
        equilibrium_error=round(eq_err, 5),
        max_displacement_mm=round(float(umag[imax]), 5),
        max_displacement_at=np.round(m.p[:, imax], 2).tolist(),
        von_mises_max_MPa=round(vm_max, 3), von_mises_design_MPa=round(vm_rob, 3),
        von_mises_max_at=np.round(loc, 2).tolist(),
        layer_normal_tension_max_MPa=round(sn_max, 3), layer_normal_tension_design_MPa=round(sn_rob, 3),
        layer_normal_max_at=np.round(loc_sn, 2).tolist(),
        layer_shear_design_MPa=round(tau_rob, 3),
        safety_factor_inplane=round(sf_xy, 2), safety_factor_interlayer=round(sf_z, 2),
        safety_factor_interlayer_shear=round(sf_shear, 2),
        safety_factor=round(sf, 2), sf_target=args.sf_target, passes=bool(sf >= args.sf_target),
        notes=notes, convergence=runs if args.convergence else None,
        solve_seconds=round(res["t_solve"], 2),
    )
    if args.png:
        render_png(res, Path(args.png), bdir, title=f"{Path(args.model).name} | {key} | SF={sf:.2f}")
        report["png"] = args.png
    if args.vtu:
        write_vtu(res, Path(args.vtu))
        report["vtu"] = args.vtu

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"model      {args.model}   material {key} ({mat['source']})")
        print(f"mesh       {r['nodes']} nodes, {r['tets']} P2 tets, {r['dofs']} dofs, size {r['size']} mm, "
              f"solve {res['t_solve']:.1f}s")
        print(f"loads      applied {np.round(applied, 3).tolist()} N, reaction {np.round(reaction, 3).tolist()} N "
              f"(equilibrium error {eq_err:.2%})")
        print(f"deflection max {umag[imax]:.4f} mm at {np.round(m.p[:, imax], 2).tolist()}")
        print(f"von Mises  max {vm_max:.2f} MPa at {np.round(loc, 2).tolist()}, design {vm_rob:.2f} MPa "
              f"vs yield {mat['yield_xy']} -> SF {sf_xy:.2f}")
        print(f"layers     build dir {np.round(bdir, 3).tolist()}: tension across layers {sn_rob:.2f} MPa "
              f"(peak {sn_max:.2f} at {np.round(loc_sn, 2).tolist()}) vs interlayer {mat['z']} -> SF {sf_z:.2f}; "
              f"interlayer shear {tau_rob:.2f} MPa -> SF {sf_shear:.2f}")
        verdict = "PASS" if sf >= args.sf_target else "FAIL"
        print(f"RESULT     governing safety factor {sf:.2f} (target {args.sf_target}) -> {verdict}")
        if args.convergence:
            print("convergence:")
            for c in runs:
                print(f"  size {c['size']:7.3f}  nodes {c['nodes']:7d}  disp {c['max_disp']:.4f}  "
                      f"vmDesign {c['vm_design']:.3f}  vmMax {c['vm_max']:.3f}  ({c['seconds']}s)")
        for n in notes:
            print(f"NOTE: {n}")
        if args.png:
            print(f"png -> {args.png}")
        if args.vtu:
            print(f"vtu -> {args.vtu}")
    return 0 if sf >= args.sf_target else 3


if __name__ == "__main__":
    sys.exit(main())
