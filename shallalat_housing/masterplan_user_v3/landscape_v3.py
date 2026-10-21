"""Landscape of the linear park and gardens in the style of the architect's reference image (contemporary, angular).

Every garden gets: a 2.6 m coloured jogging track that runs the length of the garden in straight runs
with sharp bends; the ground on either side is cut by angled joints into faceted lawn mounds (with
contour lines), paved plazas (striped paving with square tree pits), gravel and buffer planting beds,
and one timber deck with a curved bench. Palms mark the bends of the track; shade trees line the edges.
"""
import math

import numpy as np
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from layout_v3 import GARDEN_ROOMS, GARDENS, LAWN, PAVING, PLAZA_TREES, polys

TRACK_W = 2.6
JOINT = 0.9


def _rot(p, ang, origin):
    from shapely import affinity
    return affinity.rotate(p, ang, origin=origin, use_radians=False)


def _stripes(poly, gap=1.4, ang=0.0):
    """Lines of the striped paving pattern."""
    c = poly.centroid
    x0, y0, x1, y1 = poly.buffer(30).bounds
    out = []
    for y in np.arange(y0, y1, gap):
        ln = _rot(LineString([(x0, y), (x1, y)]), ang, c).intersection(poly)
        out += [g for g in getattr(ln, "geoms", [ln]) if g.geom_type == "LineString" and g.length > 0.5]
    return out


def design(poly, seed):
    rng = np.random.default_rng(seed)
    out = {k: [] for k in ("track", "paving", "stripes", "lawn", "contour", "gravel", "shrub", "deck", "bench",
                           "pits")}
    out["trees"], out["palms"] = [], []
    x0, y0, x1, y1 = poly.bounds
    along_v = (y1 - y0) >= (x1 - x0)
    L = (y1 - y0) if along_v else (x1 - x0)
    W = (x1 - x0) if along_v else (y1 - y0)

    def P(s, t):            # s along the garden 0..1, t across 0..1
        return (x0 + t * W, y0 + s * L) if along_v else (x0 + s * L, y0 + t * W)

    # the track: straight runs with sharp bends, switching sides like the reference
    sides = [0.24, 0.24, 0.72, 0.72, 0.30, 0.30, 0.70] if seed % 2 else [0.72, 0.72, 0.28, 0.28, 0.68, 0.68, 0.30]
    stops = np.linspace(-0.05, 1.05, len(sides))
    stops[1:-1] += rng.uniform(-0.04, 0.04, len(stops) - 2)
    line = LineString([P(s, t) for s, t in zip(stops, sides)])
    if W < 14:
        line = LineString([P(-0.05, 0.5), P(1.05, 0.5)])
    track = line.buffer(TRACK_W / 2, join_style="mitre", mitre_limit=4).intersection(poly)
    out["track"] = polys(track)
    for q in list(line.coords)[1:-1]:
        if poly.buffer(-2.5).contains(Point(q)):
            off = 4.5 if q[0 if along_v else 1] < (x0 + x1 if along_v else y0 + y1) / 2 else -4.5
            qq = (q[0] + off, q[1]) if along_v else (q[0], q[1] + off)
            if poly.buffer(-2.0).contains(Point(qq)):
                out["palms"].append((qq[0], qq[1], 2.6))
    # facets: angled joints across the garden
    rest = poly.difference(line.buffer(TRACK_W / 2 + JOINT, join_style="mitre", mitre_limit=4))
    n_cut = max(2, int(L / 22))
    cuts = []
    for i in range(n_cut):
        s = (i + 0.6 + rng.uniform(-0.2, 0.2)) / (n_cut + 0.2)
        d = rng.uniform(0.10, 0.22) * (1 if i % 2 else -1)
        cuts.append(LineString([P(s - d, -0.2), P(s + d, 1.2)]))
    pieces = []
    for part in polys(rest):
        g = part.difference(unary_union([c.buffer(JOINT / 2) for c in cuts]))
        pieces += [p for p in polys(g) if p.area > 6]
    pieces.sort(key=lambda p: (p.centroid.y if along_v else p.centroid.x))
    # classify: end pieces paved (entries), smallest planted, one middle piece a timber deck, rest lawns
    big = sorted(pieces, key=lambda p: -p.area)
    n_lawn = max(1, int(len(pieces) * 0.42))
    lawns = set(id(p) for p in big[:n_lawn])
    ends = {id(pieces[0]), id(pieces[-1])} if len(pieces) > 3 else set()
    deck_done = False
    for i, p in enumerate(pieces):
        if id(p) in ends:
            kind = "paving"
        elif p.area < 45:
            kind = "shrub"
        elif id(p) in lawns:
            kind = "lawn"
        elif not deck_done and 0.3 < i / max(1, len(pieces) - 1) < 0.8 and p.area > 60:
            kind, deck_done = "deck", True
        elif i % 3 == 0:
            kind = "gravel"
        else:
            kind = "paving"
        if kind == "lawn":
            out["lawn"].append(p)
            for k in (1.3, 2.8, 4.4):
                c = p.buffer(-k, join_style="mitre")
                if not c.is_empty and c.area > 8:
                    out["contour"] += [q.exterior for q in polys(c)]
            buf = p.buffer(-1.0, join_style="mitre")
            if not buf.is_empty and p.area > 120:
                # a shrub border on the long edge of each mound (the "buffer planting")
                out["shrub"] += polys(p.difference(p.buffer(-0.6, join_style="mitre")).intersection(
                    box(x0, y0, (x0 + x1) / 2, y1) if along_v else box(x0, y0, x1, (y0 + y1) / 2)))
        elif kind == "paving":
            out["paving"].append(p)
            out["stripes"] += _stripes(p, 1.3, 0 if along_v else 90)
            for u in np.arange(p.bounds[0] + 3, p.bounds[2] - 2, 6.0):
                for v in np.arange(p.bounds[1] + 3, p.bounds[3] - 2, 6.0):
                    sq = box(u - 0.7, v - 0.7, u + 0.7, v + 0.7)
                    if p.buffer(-1.2).contains(sq):
                        out["pits"].append(sq)
                        out["trees"].append((u, v, 2.2))
        elif kind == "deck":
            out["deck"].append(p)
            out["stripes"] += _stripes(p, 0.6, 90 if along_v else 0)
            c = p.centroid
            r = min(4.0, math.sqrt(p.area) / 3)
            arc = LineString([(c.x + r * math.cos(a), c.y + r * math.sin(a)) for a in np.linspace(0.3, 2.8, 20)])
            out["bench"].append(arc.buffer(0.35, cap_style="round").intersection(p))
        elif kind == "gravel":
            out["gravel"].append(p)
        else:
            out["shrub"].append(p)
    # shade trees along both long edges
    for edge in [p.exterior for p in polys(poly.buffer(-2.2, join_style="mitre"))]:
        busy = unary_union(out["track"] + out["deck"]).buffer(2.0)
        for d in np.arange(0, edge.length, 11.0):
            q = edge.interpolate(d)
            if not busy.contains(q) and all(math.dist((q.x, q.y), t[:2]) > 5 for t in out["trees"] + out["palms"]):
                out["trees"].append((q.x, q.y, rng.uniform(2.2, 3.0)))
    return out


LANDSCAPE = [design(g, i) for i, g in enumerate(GARDEN_ROOMS + GARDENS) if g.area > 300]

# the towers' plaza: the paving becomes striped stone, every lawn a faceted mound, palms on the promenade
PLAZA_LS = {k: [] for k in ("track", "paving", "stripes", "lawn", "contour", "gravel", "shrub", "deck", "bench",
                            "pits")}
PLAZA_LS["trees"], PLAZA_LS["palms"] = [(x, y, 2.2) for x, y in PLAZA_TREES], []
PLAZA_LS["paving"] = polys(PAVING)
PLAZA_LS["stripes"] = _stripes(PAVING, 1.2, 0)
for i, g in enumerate(polys(LAWN)):
    if g.area < 15:
        PLAZA_LS["shrub"].append(g)
        continue
    x0, y0, x1, y1 = g.bounds
    cuts = [LineString([(x0 - 5, v - 6), (x1 + 5, v + 6)]) for v in np.arange(y0 + 14, y1, 16)]
    for p in polys(g.difference(unary_union([c.buffer(0.45) for c in cuts]))):
        PLAZA_LS["lawn"].append(p)
        for k in (1.0, 2.2):
            c = p.buffer(-k, join_style="mitre")
            PLAZA_LS["contour"] += [q.exterior for q in polys(c) if q.area > 4]
