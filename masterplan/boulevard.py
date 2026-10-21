"""Concept A (the boulevard), drawn on site_v2.dxf coordinates (plot rotated: wide end up).

Structure, as in the approved board: towers among the grove above the public cross road, a
tree-lined boulevard with planted median down the plot's centreline, roundabouts on it, a circular
fountain plaza at mid-length with the mosque and civic buildings around it, villas (400 m2) in the
upper and middle blocks, townhouses (200 m2) in the lower blocks. The watercourse is cancelled.
"""
import math

import ezdxf
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

Q1 = (339878.5, 4035811.5)   # top-left
Q2 = (340186.5, 4035834.4)   # top-right
Q3 = (340028.0, 4034935.7)   # bottom-right
Q4 = (339878.5, 4034974.1)   # bottom-left
OX, OY = Q4
SITE_W = Polygon([Q1, Q2, Q3, Q4])
SITE = affinity.translate(SITE_W, -OX, -OY)          # local: x right, v up, origin at Q4
XR0, XR1 = (Q3[0] - OX, Q3[1] - OY), (Q2[0] - OX, Q2[1] - OY)
CROSS = LineString([(339873.6 - OX, 4035667.4 - OY), (340167.1 - OX, 4035696.5 - OY)])
TREES = [(339948.6, 4035782.3), (340017.0, 4035783.4), (340076.4, 4035758.4), (339931.4, 4035745.0),
         (339996.5, 4035741.9), (340059.1, 4035719.5), (340113.2, 4035736.9)]
TREES = [(x - OX, y - OY) for x, y in TREES]

LOT = {"V": (16.0, 25.0), "D": (10.0, 20.0)}
FOOT = {"V": (10.0, 12.0, 4.0), "D": (10.0, 12.0, 2.5)}
W = {"blvd": 24.0, "avenue": 24.0, "collector": 16.0, "local": 12.0, "public": 10.0}


def xr(v):
    """x of the right edge at height v."""
    t = (v - XR0[1]) / (XR1[1] - XR0[1])
    return XR0[0] + t * (XR1[0] - XR0[0])


def xc(v):
    return xr(v) / 2


def v_cross(x):
    (a, b), (c, d) = CROSS.coords
    return b + (x - a) * (d - b) / (c - a)


class Frame:
    """u along an edge, n inward."""

    def __init__(self, o, u, n):
        self.o, self.u, self.n = o, u, n

    def pt(self, s, d):
        return (self.o[0] + s * self.u[0] + d * self.n[0], self.o[1] + s * self.u[1] + d * self.n[1])

    def rect(self, s0, s1, d0, d1):
        return Polygon([self.pt(s0, d0), self.pt(s1, d0), self.pt(s1, d1), self.pt(s0, d1)])

    def sd(self, p):
        x, y = p[0] - self.o[0], p[1] - self.o[1]
        return (x * self.u[0] + y * self.u[1], x * self.n[0] + y * self.n[1])


_L = math.dist(XR0, XR1)
_ru = ((XR1[0] - XR0[0]) / _L, (XR1[1] - XR0[1]) / _L)
FR = {"L": Frame((0, 0), (0, 1), (1, 0)), "R": Frame(XR0, _ru, (-_ru[1], _ru[0]))}
if FR["R"].sd((0, 0))[1] < 0:
    FR["R"] = Frame(XR0, _ru, (_ru[1], -_ru[0]))


def parts(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [x for x in getattr(g, "geoms", []) if isinstance(x, Polygon)]


def edge_line(side, d, v0, v1):
    """Line parallel to the left/right edge, d metres inside, between heights v0 and v1."""
    if side == "L":
        return LineString([(d, v0), (d, v1)])
    f = FR["R"]
    s0 = f.sd((xr(v0), v0))[0]
    s1 = f.sd((xr(v1), v1))[0]
    return LineString([f.pt(s0, d), f.pt(s1, d)])


def hline(v, x0=-20, x1=340):
    return LineString([(x0, v), (x1, v)])


class Plan:
    def __init__(self):
        self.roads, self.rings, self.carves, self.zones, self.gates, self.towers = [], [], [], [], [], []
        self.belt = 3.0

    def road(self, line, cls):
        self.roads.append((line, cls))

    def ring(self, x, v, r):
        self.rings.append((Point(x, v), r))

    def carve(self, poly, use, label):
        self.carves.append({"poly": poly, "use": use, "label": label})

    def zone(self, poly, use, label="", rows=None):
        self.zones.append({"poly": poly, "use": use, "label": label, "rows": rows or []})

    def build(self):
        polys, med = [], []
        for ln, cls in self.roads:
            polys.append(ln.buffer(W[cls] / 2, cap_style="flat", join_style="round"))
            if cls in ("blvd", "avenue"):
                med.append(ln.buffer((8 if cls == "blvd" else 5) / 2, cap_style="flat"))
        for c, r in self.rings:
            polys.append(c.buffer(r))
        roads = unary_union(polys).buffer(6).buffer(-6)
        self.road_area = roads.intersection(SITE)
        self.medians = unary_union(med + [c.buffer(r - 9) for c, r in self.rings]).intersection(self.road_area)
        inner = SITE.buffer(-self.belt, join_style="mitre")
        self.belt_area = SITE.difference(inner).difference(self.road_area)
        free = inner.difference(self.road_area)
        cv = unary_union([c["poly"] for c in self.carves])
        self.blocks = []
        for b in parts(free.difference(cv)):
            for q in parts(b.buffer(-6).buffer(6)):
                if q.area < 40:
                    continue
                rp = q.representative_point()
                z = next((z for z in self.zones if z["poly"].contains(rp)), None)
                self.blocks.append({"poly": q, "use": z["use"] if z else "green", "label": z["label"] if z else "",
                                    "rows": z["rows"] if z else []})
        for c in self.carves:
            self.blocks.append({"poly": c["poly"].intersection(inner).difference(self.road_area), "use": c["use"],
                                "label": c["label"], "rows": []})
        self.subdivide()
        return self

    def subdivide(self):
        self.lots = []
        for b in self.blocks:
            zone = b["poly"].buffer(0.8)
            mine = []
            for fr, side, t in b["rows"]:
                f = FR[fr]
                cs = [f.sd(c) for c in b["poly"].exterior.coords]
                s0, s1 = min(c[0] for c in cs), max(c[0] for c in cs)
                w, L = LOT[t]
                ds = side                      # explicit row start (depth off the edge)
                best = []
                for k in range(10):
                    run, s = [], s0 + k * w / 10
                    while s + w <= s1 + 1e-6:
                        if zone.contains(f.rect(s, s + w, ds, ds + L)):
                            run.append(s)
                        s += w
                    if len(run) > len(best):
                        best = run
                for s in best:
                    hw, hd, sb = FOOT[t]
                    sy = (w - hw) / 2
                    if ds > 30:            # inner rows front the street on the edge side
                        fp = f.rect(s + sy, s + sy + hw, ds + sb, ds + sb + hd)
                    else:
                        fp = f.rect(s + sy, s + sy + hw, ds + L - sb - hd, ds + L - sb)
                    lot = {"poly": f.rect(s, s + w, ds, ds + L), "fp": fp, "type": t}
                    self.lots.append(lot)
                    mine.append(lot["poly"])
                if mine:
                    zone = b["poly"].buffer(0.8).difference(unary_union(mine).buffer(-0.05))
        lots_u = unary_union([l["poly"] for l in self.lots])
        self.jeera = unary_union([b["poly"] for b in self.blocks if b["rows"]]).difference(lots_u)


def build():
    p = Plan()
    VC = 380.0                       # civic fountain plaza
    VH = 620.0                       # head roundabout
    VB = 70.0                        # bottom roundabout
    rings = [VH, 505.0, 255.0, 160.0, VB]

    # -------------------------------------------------- network
    p.road(LineString([(xc(v), v) for v in range(int(VB), int(VH) + 1, 10)]), "blvd")
    for v in rings:
        p.ring(xc(v), v, 18)
    p.ring(xc(VC), VC, 46)
    p.road(edge_line("L", 32.5, 20, v_cross(32.5) - 8), "local")
    p.road(edge_line("R", 32.5, 25, v_cross(xr(600) - 32.5) - 8), "local")
    for v in (VH, 505.0, 445.0, 315.0, 255.0, 160.0, VB):
        p.road(hline(v, 26, xr(v) - 26), "local")
    # main gate avenue from the right (main) road into the head roundabout
    p.road(LineString([(xr(VH) + 8, VH), (xc(VH) + 18, VH)]), "avenue")
    p.road(CROSS, "public")
    gates = [("البوابة الرئيسية", (xr(VH), VH), 1), ("بوابة الخدمة", (0, 40), 3)]

    # -------------------------------------------------- above the public cross road: towers in the grove
    top = Polygon([(-5, v_cross(-5) + 9), (320, v_cross(320) + 9), (320, 900), (-5, 900)]).intersection(SITE)
    tz = top.intersection(box(70, 0, 250, 900))
    p.carve(tz, "towers", "منطقة البرجين")
    p.towers = [box(95, 770, 135, 790), box(170, 772, 210, 792)]
    p.carve(top.intersection(box(-5, 0, 70, 900)).intersection(box(0, 770, 70, 900)), "sports", "ملعب")
    p.carve(top.intersection(box(-5, 0, 70, 770)), "community", "شرطة ودفاع مدني")
    p.carve(top.intersection(box(250, 0, 330, 775)), "edu", "مدرسة إعدادية")
    p.carve(top.intersection(box(250, 775, 330, 900)), "utility", "محطة كهرباء")
    gates.append(("مدخل البرجين", (160, v_cross(160)), 2))

    # -------------------------------------------------- civic plaza at mid-length
    vc_lo, vc_hi = 315.0, 445.0
    p.carve(Polygon([(xc(v) + 15, v) for v in (vc_lo + 6, vc_hi - 6)] +
                    [(xr(v) - 38.5, v) for v in (vc_hi - 6, vc_lo + 6)]).difference(Point(xc(VC), VC).buffer(52)),
            "religious", "الجامع وساحته")
    p.carve(Polygon([(38.5, vc_lo + 6), (38.5, VC - 2), (xc(VC) - 12, VC - 2), (xc(vc_lo) - 12, vc_lo + 6)])
            .difference(Point(xc(VC), VC).buffer(52)), "health", "مركز صحي وإدارة")
    p.carve(Polygon([(38.5, VC + 2), (38.5, vc_hi - 6), (xc(vc_hi) - 12, vc_hi - 6), (xc(VC) - 12, VC + 2)])
            .difference(Point(xc(VC), VC).buffer(52)), "commercial", "السوق والمطاعم")
    # schools and kindergartens on inner blocks next to the boulevard
    p.carve(Polygon([(38.5, 451), (38.5, 499), (xc(499) - 15, 499), (xc(451) - 15, 451)]), "edu",
            "مدرسة ابتدائية")
    p.carve(Polygon([(xc(451) + 15, 451), (xc(499) + 15, 499), (xr(499) - 38.5, 499), (xr(451) - 38.5, 451)]), "edu",
            "مدرسة متوسطة")
    p.carve(Polygon([(38.5, 261), (38.5, 309), (xc(309) - 15, 309), (xc(261) - 15, 261)]), "edu", "روضة 1 وملاعب")
    p.carve(Polygon([(xc(261) + 15, 261), (xc(309) + 15, 309), (xr(309) - 38.5, 309), (xr(261) - 38.5, 261)]),
            "community", "النادي الاجتماعي")
    p.carve(Polygon([(38.5, 121), (38.5, 154), (xc(154) - 15, 154), (xc(121) - 15, 121)]), "edu", "روضة 2")
    # pocket parks with ponds beside the boulevard
    for v0, v1 in ((511.0, 554.0),):
        p.carve(Polygon([(xc(v0) - 15, v0), (xc(v1) - 15, v1), (xc(v1) - 55, v1), (xc(v0) - 55, v0)]),
                "park", "حديقة")
        p.carve(Polygon([(xc(v0) + 15, v0), (xc(v1) + 15, v1), (xc(v1) + 55, v1), (xc(v0) + 55, v0)]),
                "park", "حديقة")
    # utilities at the low southern tip, on the service gate
    p.carve(SITE.intersection(box(-5, -60, 340, 34)).difference(box(-5, -60, 38.5, 46)), "utility",
            "محطة معالجة ماء ومجاري")

    # -------------------------------------------------- housing rows
    left = box(-5, 0, 400, 2000)
    for (v0, v1), t in (((315.0, 900.0), "V"), ((-60.0, 315.0), "D")):
        band = box(-5, v0, 400, v1)
        L = LOT[t][1]
        p.zone(box(-5, -60, 26.5, 2000).intersection(band), "res", rows=[("L", 6.5, "D")])
        p.zone(Polygon([(xr(v) - 26.5, v) for v in (-60, 900)] + [(400, 900), (400, -60)]).intersection(band),
               "res", rows=[("R", 6.5, "D")])
        inner_l = Polygon([(38.5, -60), (38.5, 900)] + [(xc(v), v) for v in (900, -60)]).intersection(band)
        p.zone(inner_l, "res", rows=[("L", 38.5, t), ("L", 38.5 + L, t)])
        inner_r = Polygon([(xc(v), v) for v in (-60, 900)] + [(xr(v) - 38.5, v) for v in (900, -60)]).intersection(band)
        p.zone(inner_r, "res", rows=[("R", 38.5, t), ("R", 38.5 + L, t)])
    p.zones.insert(0, {"poly": top, "use": "park", "label": "حديقة البستان", "rows": []})
    p.gates = gates
    p.VC = VC
    return p.build()
