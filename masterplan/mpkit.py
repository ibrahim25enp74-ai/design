"""Master-plan authoring helpers on top of kit.Plan.

Design is done in the north-edge frame (s along the 912 m north edge, d inward), so every street
is parallel or perpendicular to the main public road. Curved park geometry is drawn with
Chaikin-smoothed polylines.
"""
import math

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

import kit

N, S = kit.NORTH, kit.SOUTH


def ds(s):
    """Depth of the plot (north edge to south edge) at north-frame s."""
    ln = LineString([N.pt(s, -10), N.pt(s, 400)]).intersection(kit.SITE)
    if ln.is_empty:
        return 0.0
    return max(N.sd(c)[1] for c in ln.coords)


def NR(s0, s1, d0, d1):
    return N.rect(s0, s1, d0, d1)


def SR(s0, s1, d0, d1):
    return S.rect(s0, s1, d0, d1)


def npt(s, d):
    return N.pt(s, d)


def nline(pts):
    return LineString([N.pt(s, d) for s, d in pts])


def npoly(pts):
    return Polygon([N.pt(s, d) for s, d in pts])


def chaikin(pts, n=3, closed=False):
    pts = list(pts)
    for _ in range(n):
        out = [] if closed else [pts[0]]
        rng = range(len(pts)) if closed else range(len(pts) - 1)
        for i in rng:
            a, b = pts[i], pts[(i + 1) % len(pts)]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        if not closed:
            out.append(pts[-1])
        pts = out
    return pts


def ncurve(pts, n=3):
    return LineString(chaikin([N.pt(s, d) for s, d in pts], n))


def nblob(pts, n=3):
    return Polygon(chaikin([N.pt(s, d) for s, d in pts], n, closed=True))


def s_on_south(s_n, d_from_south):
    """South-frame s for the point that is d off the south edge, on the north normal at s_n."""
    far = LineString([N.pt(s_n, -50), N.pt(s_n, 450)])
    p = far.intersection(S.line(d_from_south, -300, 1200))
    return S.sd((p.x, p.y))[0]


class MPlan(kit.Plan):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.plazas = []       # dict(poly, kind)  kind: plaza / court / forecourt
        self.waters = []       # polygons
        self.buildings = []    # dict(poly, kind, label)  service / gatehouse / tower podium
        self.parking = []      # dict(poly, angle)  stall lines drawn along angle
        self.keys = []         # numbered labels: dict(n, pt, text)
        self.cul_heads = []    # turning circles (points)
        self.paths_wide = []   # promenades (lines), width 5 m

    def rows(self, edge, seq, s0, s1, d_start=0.0, street_cls="local"):
        """Like strip_rows but bounded by frame s (not local x); streets get the given class."""
        e = kit.EDGES[edge]
        d = d_start
        out = []
        for item in seq:
            if item.startswith("buf") or item.startswith("G"):
                d += float(item.split(":")[1])
            elif item[0] in ("S", "C", "L"):
                cls = {"S": street_cls, "C": "collector", "L": "lane"}[item[0]]
                w = kit.ROAD_W[cls]
                self.road_line(LineString([e.pt(s0, d + w / 2), e.pt(s1, d + w / 2)]), cls)
                d += w
            else:
                t, f = item[0], item[1]
                out.append((edge, d, t, f))
                d += kit.LOT[t][1]
        return out, d

    def key(self, n, pt, text):
        self.keys.append({"n": n, "pt": pt, "text": text})

    def gate_at(self, s, d, kind, label):
        x, y = N.pt(s, d)
        self.gate(x, y, kind)
        self.gates[-1]["label"] = label
