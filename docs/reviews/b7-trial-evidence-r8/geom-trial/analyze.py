import sys, math, itertools
from gerbonara import GerberFile
from gerbonara.apertures import CircleAperture, RectangleAperture, ApertureMacroInstance
from shapely.geometry import box, Point
from shapely import affinity
import shapely
f = GerberFile.open(sys.argv[1])
shapes = []
for o in f.objects:
    ap = o.aperture
    if isinstance(ap, ApertureMacroInstance) and ap.macro.name == 'RoundRect':
        p = ap.parameters
        r, xs = p[0], p[1:9]
        cx = [xs[0], xs[2], xs[4], xs[6]]; cy = [xs[1], xs[3], xs[5], xs[7]]
        core = (min(cx), min(cy), max(cx), max(cy))
        shapes.append(('roundrect', float(o.x), float(o.y), core, float(r)))
    elif isinstance(ap, CircleAperture):
        shapes.append(('circle', float(o.x), float(o.y), None, float(ap.diameter) / 2))
    elif isinstance(ap, RectangleAperture):
        shapes.append(('rect', float(o.x), float(o.y), (-float(ap.w)/2, -float(ap.h)/2, float(ap.w)/2, float(ap.h)/2), 0.0))
    else:
        raise SystemExit('unsupported aperture ' + repr(ap))
def core_box(s):
    kind, x, y, core, r = s
    if kind == 'circle': return (x, y, x, y)  # a circle core is its centre; its radius enters once
    if kind == 'rect': return (x + core[0], y + core[1], x + core[2], y + core[3])
    return (x + core[0], y + core[1], x + core[2], y + core[3])
def exact_distance(a, b):
    A, B = core_box(a), core_box(b)
    dx = max(B[0] - A[2], A[0] - B[2], 0.0)
    dy = max(B[1] - A[3], A[1] - B[3], 0.0)
    d_core = math.hypot(dx, dy)
    ra = a[4]; rb = b[4]
    return d_core - ra - rb   # negative means overlap; exact for Minkowski sums with a disk
def approx_distance(a, b, q):
    def poly(s):
        kind, x, y, core, r = s
        if kind == 'circle': return Point(x, y).buffer(r, quad_segs=q)
        bx = core_box(s)
        return box(*bx).buffer(r, quad_segs=q) if r > 0 else box(*bx)
    return poly(a).distance(poly(b))
print('flashes:', len(shapes))
res = []
for i, j in itertools.combinations(range(len(shapes)), 2):
    e = exact_distance(shapes[i], shapes[j])
    res.append((e, i, j))
res.sort()
for e, i, j in res[:8]:
    print(f"pair {i}-{j} exact_gap_mm={e:.6f} exact_gap_mil={e/0.0254:.4f} approx_q16_mm={approx_distance(shapes[i], shapes[j], 16):.6f}")
