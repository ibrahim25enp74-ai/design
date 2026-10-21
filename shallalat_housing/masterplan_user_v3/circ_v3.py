"""Circulation of variant 3: centre lines of each kind of route, and walking distances from homes to services.

Kinds:
- main: the entry road from the main gate to the roundabout and the civic street;
- loop: the two residential loops (north and south) with the tower stretch between them;
- drop: the two drop-off lanes into the towers' plaza;
- service: the service street from the service gate (utilities, police, civil defence);
- emergency: service street + the bollarded link across the east garden that closes the two loops into a ring;
- ped: the car-free park path from the gate square to the east garden, the green links and cross walks.
"""
import networkx as nx
import numpy as np
from shapely.geometry import LineString, Point, box
from shapely.ops import nearest_points

from layout_v3 import (EAST_GARDEN, EMERG_U, ENTRY, FRAMES, HOU, HOUSE, HOUSES, LAYBY, LINKS, PARK_ALL, PLAZA_ALL,
                       RB_C, ROAD, SERV, SGATE_U, SPINE, SROAD, TOWERS, TWR, VIL, VILLA, VILLAS, WALKS, north_v, t_of,
                       _tc, _vc)


def pt(side, t, s):
    o, d, n = FRAMES[side]
    return tuple(o + t * d + s * n)


def fline(side, pts):
    return LineString([pt(side, t, s) for t, s in pts])


ROUTES = {k: [] for k in ("main", "loop", "drop", "service", "emergency", "ped")}

# main: gate -> roundabout -> south loop; civic street west; school lay-by
ROUTES["main"].append(LineString([(RB_C[0], north_v(RB_C[0])), (RB_C[0], RB_C[1] + 20)]))
ROUTES["main"].append(LineString([(RB_C[0], RB_C[1] - 20), (RB_C[0], VILLA[1] + ROAD / 2)]))
ROUTES["main"].append(LineString([(RB_C[0] - 20, sum(SPINE) / 2), (2.0, sum(SPINE) / 2)]))
ROUTES["main"].append(LineString([(LAYBY[0] + 3.5, LAYBY[1] + 4), (LAYBY[0] + 3.5, LAYBY[3] - 4)]))
ROUTES["main"].append(Point(RB_C).buffer(15.0).exterior)

# residential loops, per side
vd, hd = VILLA[1], HOUSE[1]
for side in ("N", "S"):
    tv0, tv1 = t_of(side, VIL[0]), t_of(side, VIL[1])
    th0, th1 = t_of(side, HOU[0]), t_of(side, HOU[1])
    so_v, si_v = vd + ROAD / 2, 3 * vd + 1.5 * ROAD
    so_h, si_h = hd + ROAD / 2, 3 * hd + 1.5 * ROAD
    # outer street, villas -> towers -> houses
    ROUTES["loop"].append(fline(side, [(tv0 - 6, so_v), (tv1, so_v), (tv1, so_h), (th1 - 5, so_h)]))
    # park-side street of the villas and its two ends
    ROUTES["loop"].append(fline(side, [(tv0 - 6, si_v), (tv1 - 5, si_v), (tv1 - 5, so_v)]))
    # park-side street of the houses, joined to the outer street at both ends
    ROUTES["loop"].append(fline(side, [(th0 + 5, so_h), (th0 + 5, si_h), (th1 - 5, si_h), (th1 - 5, so_h)]))

# drop-offs to the plaza from both loops
ROUTES["drop"].append(LineString([(_tc, hd + ROAD / 2), (_tc, PLAZA_ALL.bounds[1] + 8)]))
ROUTES["drop"].append(LineString([(_tc, PLAZA_ALL.bounds[3] - 8), (_tc, north_v(_tc) - hd - ROAD / 2)]))

# service: gate -> service street -> civic street
ROUTES["service"].append(LineString([(SGATE_U, 0.0), (SGATE_U, sum(SPINE) / 2)]))

# emergency ring: east link across the garden between the two outer loop streets
_s_end = pt("S", t_of("S", HOU[1]) - 5, hd + ROAD / 2)
_n_end = pt("N", t_of("N", HOU[1]) - 5, hd + ROAD / 2)
ROUTES["emergency"].append(LineString([_s_end, (EMERG_U, _s_end[1]), (EMERG_U, _n_end[1] - (EMERG_U - _n_end[0]) * 0.176), _n_end]))

# pedestrians: the park path along the middle of the park, zigzagging between the towers
_spine = []
for u in np.arange(ENTRY[1] + 20, EAST_GARDEN.bounds[2] - 15, 6.0):
    if PLAZA_ALL.bounds[0] - 2 <= u <= PLAZA_ALL.bounds[2] + 2:
        continue
    seg = PARK_ALL.intersection(box(u - 0.1, -10, u + 0.1, 400))
    if seg.is_empty:
        continue
    _spine.append((u, (seg.bounds[1] + seg.bounds[3]) / 2))
_w = [p for p in _spine if p[0] < PLAZA_ALL.bounds[0]]
_e = [p for p in _spine if p[0] > PLAZA_ALL.bounds[2]]
tb = [t.bounds for t in TOWERS]
_zig = [(PLAZA_ALL.bounds[0] + 2, _vc - 8), ((tb[0][2] + tb[1][0]) / 2, _vc - 8), ((tb[0][2] + tb[1][0]) / 2, _vc + 8),
        ((tb[1][2] + tb[2][0]) / 2, _vc + 8), ((tb[1][2] + tb[2][0]) / 2, _vc - 8), (PLAZA_ALL.bounds[2] - 2, _vc - 8)]
ROUTES["ped"].append(LineString([(RB_C[0] + 22, RB_C[1])] + _w + _zig + _e))
# civic quarter: sidewalk paths from the roundabout to the gate square and the schools
ROUTES["ped"].append(LineString([(RB_C[0] - 16, RB_C[1] + 9), (RB_C[0] - 16, SPINE[1] + 40)]))
for lk in LINKS:
    c = lk.centroid
    a, b = lk.exterior.coords[0], lk.exterior.coords[2]
    ROUTES["ped"].append(LineString([nearest_points(lk.exterior, Point(c.x, -1e3 if c.y < 150 else 1e3))[0], c]))
for g in WALKS:
    ROUTES["ped"].append(LineString([(g.centroid.x, g.bounds[1]), (g.centroid.x, g.bounds[3])]))
# kindergarten, mosque and primary school open onto the drop-off lanes; from the drop-offs a path runs between towers A and B
# to the park path
_gx = (tb[0][2] + tb[1][0]) / 2
for k in ("KG", "MOSQUE", "PRIMARY"):
    cc = SERV[k].centroid
    ROUTES["ped"].append(LineString([(cc.x, cc.y), (_tc, cc.y)]))
for y0, y1 in ((PLAZA_ALL.bounds[1] + 8, _vc - 8), (PLAZA_ALL.bounds[3] - 8, _vc + 8)):
    ROUTES["ped"].append(LineString([(_tc, y0), (_gx, y0), (_gx, y1)]))

# --- walking distances: shortest path on the street + path network -----------------------------------
G = nx.Graph()


def _add(ln):
    cs = list(ln.coords)
    for a, b in zip(cs, cs[1:]):
        # split long pieces so crossings snap
        n = max(1, int(Point(a).distance(Point(b)) // 6))
        pts = [tuple(np.round(np.add(a, np.subtract(b, a) * i / n), 1)) for i in range(n + 1)]
        for p, q in zip(pts, pts[1:]):
            G.add_edge(p, q, w=Point(p).distance(Point(q)))


for k in ROUTES:
    if k == "emergency":
        continue
    for ln in ROUTES[k]:
        _add(ln)
_nodes = np.array(list(G.nodes))
# join nodes that are close to each other (crossings, ends meeting a street)
from scipy.spatial import cKDTree  # noqa: E402
for i, j in cKDTree(_nodes).query_pairs(7.0):
    a, b = tuple(_nodes[i]), tuple(_nodes[j])
    G.add_edge(a, b, w=float(np.hypot(*np.subtract(a, b))))
_tree = cKDTree(_nodes)


def _near(p):
    d, i = _tree.query(p)
    return tuple(_nodes[i]), d


def walk(a, b):
    na, da = _near(a)
    nb, db = _near(b)
    return da + db + nx.shortest_path_length(G, na, nb, weight="w")


GROUPS = {
    "Villas north - فلل الشمال": [p for p in VILLAS if p.centroid.y > 150],
    "Villas south - فلل الجنوب": [p for p in VILLAS if p.centroid.y < 150],
    "Houses west of towers - الدور قرب الأبراج": [p for p in HOUSES if p.centroid.x < HOU[0] + 1],
    "Houses east - الدور الشرقية": [p for p in HOUSES if p.centroid.x > HOU[0] + 1],
    "Towers - الأبراج": TOWERS,
}
DEST = ["KG", "MOSQUE", "PRIMARY", "SECONDARY", "MALL", "HEALTH"]


def distances():
    out = {}
    for g, ps in GROUPS.items():
        out[g] = {k: max(walk(p.centroid.coords[0], SERV[k].centroid.coords[0]) for p in ps) for k in DEST}
        out[g]["PARK"] = max(p.centroid.distance(PARK_ALL) for p in ps)
    return out

