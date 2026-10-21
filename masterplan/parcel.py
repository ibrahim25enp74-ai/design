"""Parcellation engine: street network first, blocks are what is left, blocks get a use, and
residential blocks are subdivided into 400 / 200 m2 plots.

All authoring is in the north-edge frame (s along the north road, d inward), the way the plan is
drawn on the sheet. Geometry is shapely in the local frame of plot157.py.
"""
import math

from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

import kit
import plot157 as P

N, S = kit.NORTH, kit.SOUTH
SITE = kit.SITE

LOT = {"V": (16.0, 25.0), "D": (10.0, 20.0)}
FOOT = {"V": (10.0, 12.0, 4.0), "D": (10.0, 12.0, 2.5)}


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


def sd_bounds(poly, e=N):
    g = poly if isinstance(poly, Polygon) else poly.convex_hull
    cs = [e.sd(c) for c in g.exterior.coords]
    ss, dd = [c[0] for c in cs], [c[1] for c in cs]
    return min(ss), max(ss), min(dd), max(dd)


def parts(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [x for x in getattr(g, "geoms", []) if isinstance(x, Polygon)]


ROAD = {   # class: (width, label)
    "blvd": (30.0, "بوليفارد 30 م"),
    "avenue": (24.0, "شارع دخول 24 م"),
    "collector": (16.0, "تجميعي 16 م"),
    "local": (12.0, "محلي 12 م"),
    "lane": (8.0, "زقاق 8 م"),
    "public": (10.0, "شارع عام"),
    "finger": (8.0, "ممر أخضر 8 م"),
}
MEDIAN = {"blvd": 8.0, "avenue": 6.0}


class Scheme:
    def __init__(self, key, name, name_ar):
        self.key, self.name, self.name_ar = key, name, name_ar
        self.roads = []          # dict(line, cls)
        self.rings = []          # roundabouts: dict(c, r) r = outer radius of carriageway
        self.belt = 7.0
        self.uses = []           # dict(pt, use, label, spec)   assigned by a point inside the block
        self.paths = []          # pedestrian lines
        self.gates = []          # dict(pt, kind, label, n)
        self.towers = []         # footprints
        self.extra_parcels = []  # explicit parcels carved from blocks: dict(poly, use, label)
        self.waters = []
        self.notes = {}
        self.zones_inset = []    # dict(poly, label, color) for the communities inset

    # ------------------------------------------------ authoring
    def road(self, pts, cls):
        self.roads.append({"line": nline(pts), "cls": cls})

    def road_geom(self, line, cls):
        self.roads.append({"line": line, "cls": cls})

    def ring(self, s, d, r=22.0):
        self.rings.append({"c": Point(N.pt(s, d)), "r": r})

    def use(self, s, d, use, label="", **spec):
        self.uses.append({"pt": Point(N.pt(s, d)), "use": use, "label": label, "spec": spec})

    def zone(self, poly, use, label="", **spec):
        """Blocks whose representative point falls inside poly get this use."""
        self.uses.append({"zone": poly, "use": use, "label": label, "spec": spec})

    def carve(self, poly, use, label=""):
        self.extra_parcels.append({"poly": poly, "use": use, "label": label})

    def gate(self, s, d, kind, label, n):
        self.gates.append({"pt": Point(N.pt(s, d)), "kind": kind, "label": label, "n": n})

    def tower(self, s, d, w=40.0, h=20.0):
        self.towers.append(N.rect(s - w / 2, s + w / 2, d - h / 2, d + h / 2))

    # ------------------------------------------------ build
    def build(self):
        polys, medians = [], []
        for r in self.roads:
            w = ROAD[r["cls"]][0]
            polys.append(r["line"].buffer(w / 2, cap_style="flat", join_style="round"))
            if r["cls"] in MEDIAN:
                medians.append(r["line"].buffer(MEDIAN[r["cls"]] / 2, cap_style="flat"))
        for g in self.rings:
            polys.append(g["c"].buffer(g["r"]))
        roads = unary_union(polys)
        # smooth kerb returns at junctions
        roads = roads.buffer(6, join_style="round").buffer(-6, join_style="round")
        self.road_area = roads.intersection(SITE)
        islands = [g["c"].buffer(g["r"] - 10) for g in self.rings]
        self.medians = unary_union(medians + islands).intersection(self.road_area)
        inner = SITE.buffer(-self.belt, join_style="mitre")
        self.belt_area = SITE.difference(inner).difference(self.road_area)
        free = inner.difference(self.road_area)
        # carved parcels first
        carved = unary_union([p["poly"] for p in self.extra_parcels]) if self.extra_parcels else Polygon()
        blocks = []
        for b in parts(free.difference(carved)):
            if b.area < 30:
                continue
            rb = b.buffer(-7, join_style="round").buffer(7, join_style="round")
            for q in parts(rb):
                if q.area > 30:
                    blocks.append(q)
        self.blocks = []
        for b in blocks:
            rp = b.representative_point()
            u = next((x for x in self.uses if ("pt" in x and b.contains(x["pt"])) or
                      ("zone" in x and x["zone"].contains(rp))), None)
            self.blocks.append({"poly": b, "use": u["use"] if u else "green", "label": u["label"] if u else "",
                                "spec": u["spec"] if u else {}})
        for p in self.extra_parcels:
            self.blocks.append({"poly": p["poly"].intersection(inner).difference(self.road_area), "use": p["use"],
                                "label": p["label"], "spec": {}})
        self.subdivide()
        return self

    # ------------------------------------------------ subdivision
    def subdivide(self):
        """Rows per block: spec rows=[(frame, side, type)], side 'near' fronts the street at the block's
        smallest depth in that frame, 'far' the street at its largest depth."""
        self.lots = []
        for b in self.blocks:
            rows = b["spec"].get("rows")
            if not rows:
                continue
            poly = b["poly"]
            zone = poly.buffer(0.05)
            for frame, side, t in rows:
                e = kit.EDGES[frame]
                s0, s1, d0, d1 = sd_bounds(poly, e)
                w, L = LOT[t]
                dstart = d0 if side == "near" else d1 - L
                best = []
                for k in range(10):
                    st = s0 + k * w / 10
                    run, s = [], st
                    while s + w <= s1 + 1e-6:
                        if zone.contains(e.rect(s, s + w, dstart, dstart + L)):
                            run.append(s)
                        s += w
                    if len(run) > len(best):
                        best = run
                for s in best:
                    lot = e.rect(s, s + w, dstart, dstart + L)
                    hw, hd, sb = FOOT[t]
                    sy = (w - hw) / 2
                    if side == "near":
                        fp = e.rect(s + sy, s + sy + hw, dstart + sb, dstart + sb + hd)
                        front, normal = e.pt(s + w / 2, dstart), (-e.n[0], -e.n[1])
                    else:
                        fp = e.rect(s + sy, s + sy + hw, dstart + L - sb - hd, dstart + L - sb)
                        front, normal = e.pt(s + w / 2, dstart + L), e.n
                    self.lots.append({"poly": lot, "fp": fp, "type": t, "front": Point(front), "normal": normal,
                                      "block": b})
                zone = zone.difference(unary_union([l["poly"] for l in self.lots if l["block"] is b]))
                zone = zone.buffer(0.05)
        lots_u = unary_union([l["poly"] for l in self.lots]) if self.lots else Polygon()
        jeera, park = [], []
        for b in self.blocks:
            if not b["spec"].get("rows"):
                continue
            rest = b["poly"].difference(lots_u)
            (park if b["spec"].get("residual") == "park" else jeera).append(rest)
        self.jeera = unary_union(jeera) if jeera else Polygon()
        self.valley = unary_union(park) if park else Polygon()

    # ------------------------------------------------ figures
    def units(self):
        v = sum(1 for l in self.lots if l["type"] == "V")
        d = sum(1 for l in self.lots if l["type"] == "D")
        apts = 76 * len(self.towers)
        pop = 6 * (v + d) + 38 * 4 * len(self.towers) + 38 * 6 * len(self.towers)
        return {"V": v, "D": d, "apts": apts, "total": v + d + apts, "pop": pop}

    def area_by_use(self):
        out = {}
        for b in self.blocks:
            if b["spec"].get("rows"):
                continue
            out[b["use"]] = out.get(b["use"], 0.0) + b["poly"].area
        out["lots_V"] = sum(l["poly"].area for l in self.lots if l["type"] == "V")
        out["lots_D"] = sum(l["poly"].area for l in self.lots if l["type"] == "D")
        out["jeera"] = self.jeera.area
        out["valley"] = self.valley.area
        out["roads"] = self.road_area.area
        out["belt"] = self.belt_area.area
        return out
