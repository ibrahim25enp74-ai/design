"""Circulation and relationships of variant 2 («الأحياء المتجاورة»).

Road hierarchy, the continuous green walk through the parks, the pedestrian links to the services,
the service and emergency routes, the school drop-offs, and the walking distances between every
residential zone and the services it uses.
"""
import math

import numpy as np
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from layout_v2 import (CIVIC_GARDEN, CROSS, EAST_PARK, EAST_START, FORECOURT, GATE_U, LANES, OPEN, PARKS,
                       PLAZA_ALL, PROMENADES, QPLOTS, Q_RANGE, ROAD_W, SERV, SGATE_U, SOUTH_ROAD_END,
                       TOWER_END, TOWER_PARK_N, TOWER_PARK_S, TOWERS, npt, north_v)

ROAD_C = ROAD_W / 2


def north_road_v(u):
    """v of the north road centre line at u."""
    ln = LineString([npt(-200, ROAD_C), npt(1200, ROAD_C)])
    return ln.intersection(LineString([(u, -1e3), (u, 1e3)])).y


# --- vehicles ---------------------------------------------------------------------------------------
# collectors: the two 14 m roads on the long sides; local: the 12 m cross streets; access: the 10 m lanes
COLLECTORS = [
    LineString([(CROSS[0][0] + 6, north_road_v(CROSS[0][0] + 6)), (CROSS[-1][1] - 6, north_road_v(CROSS[-1][1] - 6))]),
    LineString([(CROSS[0][0] + 6, ROAD_C), (SOUTH_ROAD_END, ROAD_C)]),
]
LOCALS = [LineString([((a + b) / 2, ROAD_C), ((a + b) / 2, north_road_v((a + b) / 2))]) for a, b in CROSS]
ACCESS = LANES
GATE_IN = LineString([(GATE_U, north_v(GATE_U) + 12), (GATE_U, north_road_v(GATE_U))])
SGATE_IN = LineString([(SGATE_U, -12), (SGATE_U, ROAD_C)])

# service vehicles: in by the service gate, along the south road to the utilities and the
# secondary school's yard; deliveries to the mall straight from the main gate (the mall is on the north road)
_mall = SERV["MALL"]
SERVICE = [
    LineString([(SGATE_U, -12), (SGATE_U, ROAD_C), (SOUTH_ROAD_END, ROAD_C)]),
    LineString([(GATE_U, north_v(GATE_U) + 12), (GATE_U, north_road_v(GATE_U)), (_mall.centroid.x, north_road_v(_mall.centroid.x))]),
]
# emergency: civil defence and police open onto the north road; the ring of the two collectors and the outer
# cross streets reaches every plot within one street
EMERGENCY = LineString([(CROSS[0][0] + 6, ROAD_C), (CROSS[0][0] + 6, north_road_v(CROSS[0][0] + 6)),
                        (CROSS[-1][1] - 6, north_road_v(CROSS[-1][1] - 6)), (CROSS[-1][1] - 6, ROAD_C),
                        (CROSS[0][0] + 6, ROAD_C)])
CD_OUT = LineString([(SERV["CIVIL_DEF"].centroid.x, SERV["CIVIL_DEF"].centroid.y),
                     (SERV["CIVIL_DEF"].centroid.x, north_road_v(SERV["CIVIL_DEF"].centroid.x))])

# --- school drop-offs: 3.5 m lay-bys in the road, so cars stop off the carriageway -------------------
_kg, _pr = SERV["KG"], SERV["PRIMARY"]
_sec = SERV["SECONDARY"]
DROPOFFS = [
    box(_pr.bounds[0] + 4, ROAD_W - 3.5, _kg.bounds[2] - 4, ROAD_W),
    box(TOWER_END, ROAD_W, TOWER_END + 3.5, ROAD_W + 20),
    box(CROSS[-1][1] - 3.5, _sec.bounds[1] + 6, CROSS[-1][1], _sec.bounds[3] - 12),
]

# --- the green walk: one continuous pedestrian route through all the parks ----------------------------
_mq = SERV["MOSQUE"]
_walk_v = _mq.bounds[3] + (CIVIC_GARDEN.bounds[3] - _mq.bounds[3]) / 2        # north of the mosque
GREENS = [PLAZA_ALL, PARKS["V1"], PARKS["V2"], CIVIC_GARDEN, PARKS["H1"], PARKS["H2"], OPEN["G_SEC"]]


def _vrange(g, u):
    s = g.intersection(LineString([(u, -1e3), (u, 1e3)]))
    return (s.bounds[1], s.bounds[3]) if not s.is_empty else None


def _crossing_v(g1, g2, a, b):
    r1, r2 = _vrange(g1, a - 0.3), _vrange(g2, b + 0.3)
    lo, hi = max(r1[0], r2[0]), min(r1[1], r2[1])
    return (lo + hi) / 2 if hi > lo + 6 else (r1[0] + r1[1] + r2[0] + r2[1]) / 4


WALK_PTS, CROSSINGS = [], []
_g1 = PROMENADES[0].centroid.y
for i, (a, b) in enumerate(CROSS):
    g1, g2 = GREENS[i], GREENS[i + 1]
    vc = _g1 if i == 0 else _crossing_v(g1, g2, a, b)
    if g1 is CIVIC_GARDEN:
        WALK_PTS += [(_mq.bounds[2] + 3, _walk_v), (a - 6, vc)]
    elif i > 0:
        c = g1.centroid
        WALK_PTS.append((c.x, c.y))
    if g2 is CIVIC_GARDEN:
        WALK_PTS += [(a - 6, vc), (b + 6, vc), (_mq.bounds[0] - 3, _walk_v)]
    else:
        WALK_PTS += [(a - 6, vc), (b + 6, vc)]
    CROSSINGS.append(box(a, vc - 3, b, vc + 3))
WALK_PTS = [(TOWERS[1].bounds[2] + 4, _g1)] + WALK_PTS
_eg = OPEN["G_SEC"].centroid
WALK_PTS += [(_eg.x, _eg.y), (EAST_PARK.centroid.x, EAST_PARK.centroid.y)]
GREEN_WALK = LineString(WALK_PTS)

# links from the green walk to the services and the other parks
_fc = FORECOURT.centroid
_gs = OPEN["G_SCHOOL"]
PED_LINKS = [
    LineString([(_fc.x, _walk_v), (_fc.x, _fc.y), (GATE_U, north_road_v(GATE_U))]),            # gate, forecourt
    LineString([(_mq.bounds[0] - 3, _walk_v), (_mq.bounds[0] - 3, _mq.bounds[1] - 3),
                (_gs.centroid.x, _mq.bounds[1] - 3), (_gs.centroid.x, _gs.bounds[1] + 2)]),     # KG + primary
    LineString([(_mq.bounds[2] + 3, _walk_v), (_mq.bounds[2] + 3, _mq.centroid.y)]),           # mosque door
    LineString([(_eg.x, _eg.y), (_eg.x, _sec.bounds[1])]),                                      # secondary
    LineString([(PLAZA_ALL.centroid.x, PLAZA_ALL.bounds[3] - 4), (TOWER_PARK_N.centroid.x, TOWER_PARK_N.centroid.y)]),
    LineString([(PLAZA_ALL.centroid.x, PLAZA_ALL.bounds[1] + 4), (TOWER_PARK_S.centroid.x, TOWER_PARK_S.centroid.y)]),
]

# --- relationships: walking distance from the farthest home of each zone to each service ---------------
# measured along the streets / green walk as the Manhattan distance in the local frame, which is what
# a walk on this grid comes to
TARGETS = {
    "Kindergarten - الروضة": unary_union([SERV["KG"], SERV["KG_W"]]),
    "Primary school - الابتدائية": SERV["PRIMARY"],
    "Mosque - الجامع": SERV["MOSQUE"],
    "Mall + health - المول والصحي": unary_union([SERV["MALL"], SERV["HEALTH"]]),
    "Secondary school - الثانوية": SERV["SECONDARY"],
}
ZONES = {
    "Towers - الأبراج": list(TOWERS),
    "Quarter 1 - الحي 1": QPLOTS["V1"], "Quarter 2 - الحي 2": QPLOTS["V2"],
    "Quarter 3 - الحي 3": QPLOTS["H1"], "Quarter 4 - الحي 4": QPLOTS["H2"],
}
OWN_PARK = {"Towers - الأبراج": unary_union([TOWER_PARK_N, TOWER_PARK_S]), "Quarter 1 - الحي 1": PARKS["V1"],
            "Quarter 2 - الحي 2": PARKS["V2"], "Quarter 3 - الحي 3": PARKS["H1"], "Quarter 4 - الحي 4": PARKS["H2"]}


def _walk(p, g):
    q = g.exterior.interpolate(g.exterior.project(p)) if g.geom_type == "Polygon" else \
        min((x.exterior.interpolate(x.exterior.project(p)) for x in g.geoms), key=lambda z: z.distance(p))
    return abs(p.x - q.x) + abs(p.y - q.y)


DIST = {}
for z, plots in ZONES.items():
    row = {}
    for t, g in list(TARGETS.items()) + [("Own park - حديقة الحي", OWN_PARK[z])]:
        row[t] = max(_walk(p.centroid, g) for p in plots)
    DIST[z] = row

if __name__ == "__main__":
    print("crossings", len(CROSSINGS), "green walk", round(GREEN_WALK.length))
    for z, r in DIST.items():
        print(z, {k.split(" - ")[0]: round(v) for k, v in r.items()})
