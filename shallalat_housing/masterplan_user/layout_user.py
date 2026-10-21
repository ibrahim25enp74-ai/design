"""Layout of Ibrahim's own master plan proposal for plot 157 / district 53 Baybokht, developed.

The architect's sketch (DXF, colour hatches) is kept as drawn: villa rows (400 m2), house rows (240 m2),
green strips, three towers on a plaza, the central spine with its roundabout and the perimeter road.
user_geom.json holds his hatches moved back onto the site coordinates (UTM 38S; his drawing was only
rotated and moved, the fit is exact). Development: the two service zones get the service areas he set,
plus the missing items, and what is left over becomes gardens.

Geometry is in the local frame used by the other proposals: u along the south edge Q1->Q4,
v towards the north edge.
"""
import json
import math
import os

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely import affinity
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))

# --- site --------------------------------------------------------------------------------------------
P = [(338954.0, 4035462.0), (339032.0, 4035771.0), (339836.0, 4035336.0), (339747.0, 4035198.0)]
Q = [(338955.19, 4035466.71), (339030.78, 4035766.16), (339833.37, 4035331.92), (339749.71, 4035202.20)]
O = np.array(Q[0])
U = np.subtract(Q[3], Q[0]) / np.linalg.norm(np.subtract(Q[3], Q[0]))
V = np.array([-U[1], U[0]])


def loc(p):
    d = np.subtract(p, O)
    return float(d @ U), float(d @ V)


def utm(p):
    return tuple(O + p[0] * U + p[1] * V)


def polys(g):
    if g is None or g.is_empty:
        return []
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 0.5]


SITE = Polygon([loc(q) for q in Q])
SITE_RAW = Polygon([loc(p) for p in P])
NW, NE = loc(Q[1]), loc(Q[2])


def north_v(u):
    return NW[1] + (u - NW[0]) * (NE[1] - NW[1]) / (NE[0] - NW[0])


# --- the architect's sketch --------------------------------------------------------------------------
_raw = json.load(open(os.path.join(HERE, "user_geom.json")))
SK = {k: [Polygon([loc(q) for q in r]).buffer(0) for r in v] for k, v in _raw.items() if not k.startswith("_")}

VILLAS = sorted(SK["yellow"], key=lambda p: (round(p.centroid.x / 20), -p.centroid.y))
HOUSES = sorted(SK["orange"], key=lambda p: (round(p.centroid.x / 20), -p.centroid.y))
STRIPS = SK["green"]
TOWERS = sorted(SK["tower"], key=lambda p: -p.centroid.y)
PLAZA = max(SK["plaza"], key=lambda p: p.area).difference(unary_union(TOWERS))
PINK = SK["pink"][0]
RED = {}
for p in SK["red"]:
    c = p.centroid
    RED[("W" if c.x < 452 else "E") + ("N" if c.y > 112 else "S")] = p

# --- revision 1 (architect's mark-up): wider green strips, lighter service blocks -------------------
# Each green strip grows from 15 m to 40 m. The villa rows west of a strip move west into the west
# zone; the house rows west of the house strip move west into the eastern service blocks.
STRIP_GROW = 25.0
EAST_SERV_EDGE = 506.0


def _mv(p, dx):
    return affinity.translate(p, dx, 0)


def _widen(p, dx0):
    """Strip moved by dx0, then widened westwards by STRIP_GROW."""
    return unary_union([_mv(p, dx0), _mv(p, dx0 - STRIP_GROW)]).convex_hull


_villa_dx = lambda x: -2 * STRIP_GROW if x < 190 else (-STRIP_GROW if x < 280 else 0.0)  # noqa: E731
VILLAS = sorted([_mv(p, _villa_dx(p.centroid.x)) for p in VILLAS], key=lambda p: (round(p.centroid.x / 20), -p.centroid.y))
HOUSES = sorted([_mv(p, -STRIP_GROW if p.centroid.x < 640 else 0.0) for p in HOUSES],
                key=lambda p: (round(p.centroid.x / 20), -p.centroid.y))
_strips = []
for p in STRIPS:
    x = p.centroid.x
    if x < 250:
        _strips.append(_widen(p, -STRIP_GROW))
    elif x < 300:
        _strips.append(_widen(p, 0.0))
    elif p.area > 600:                                   # the two halves of the house strip
        _strips.append(_widen(p, 0.0))
    else:                                                # island of the small roundabout, stays centred
        _strips.append(_mv(p, -STRIP_GROW / 2))
STRIPS = _strips
PINK = PINK.intersection(box(-1e3, -1e3, PINK.bounds[2] - 2 * STRIP_GROW, 1e3))
for k in ("EN", "ES"):
    RED[k] = RED[k].intersection(box(-1e3, -1e3, EAST_SERV_EDGE, 1e3))

# main roundabout on the spine between the four service blocks
RB_C = (453.5, 112.5)
RB_R, RB_ISL = 24.0, 12.0
ROUNDABOUT_ISLAND = Point(RB_C).buffer(RB_ISL)

BUILT = unary_union(VILLAS + HOUSES + STRIPS + TOWERS + [PLAZA, PINK] + list(RED.values()))
ROADS = SITE.difference(BUILT).difference(ROUNDABOUT_ISLAND)

# --- splitting a zone into parcels of a set area -----------------------------------------------------


def cut(poly, area, axis="v", side="min"):
    """Cut a piece of `area` m2 off `poly` with a line across `axis`, starting from its min / max side."""
    x0, y0, x1, y1 = poly.bounds
    lo, hi = (y0, y1) if axis == "v" else (x0, x1)

    def piece(c):
        if axis == "v":
            b = box(x0 - 1, y0 - 1, x1 + 1, c) if side == "min" else box(x0 - 1, c, x1 + 1, y1 + 1)
        else:
            b = box(x0 - 1, y0 - 1, c, y1 + 1) if side == "min" else box(c, y0 - 1, x1 + 1, y1 + 1)
        return poly.intersection(b)

    a, b = lo, hi
    for _ in range(60):
        m = (a + b) / 2
        grow = piece(m).area < area
        if (side == "min") == grow:
            a = m
        else:
            b = m
    p = clean(piece((a + b) / 2))
    return p, clean(poly.difference(p))


def clean(g):
    """Drop the slivers a boolean leaves along a shared edge."""
    g = g.buffer(-0.02, join_style="mitre").buffer(0.02, join_style="mitre")
    ps = polys(g)
    return max(ps, key=lambda p: p.area) if ps else g


# --- services: the areas the architect set, plus the missing items ------------------------------------
SERV = {}       # key -> polygon
OPEN = {}       # leftover green / parking inside the service zones
# Revision 1: the four blocks round the roundabout keep only the daily services, each in a garden;
# the secondary school and police + civil defence move to the west zone by the service gate.
# north-west block, beside the main gate: mall + its parking, garden on the roundabout side
SERV["MALL"], r = cut(RED["WN"], 3000, "v", "max")
OPEN["PARK_MALL"], r = cut(r, 1200, "u", "min")
OPEN["G_MALL"] = r
# north-east block, beside the main gate: health centre, garden
SERV["HEALTH"], r = cut(RED["EN"], 1000, "v", "max")
OPEN["G_HEALTH"] = r
# south-west block: kindergarten on the quiet south side, mosque, garden on the roundabout side
SERV["KG"], r = cut(RED["WS"], 1500, "v", "min")
SERV["MOSQUE"], r = cut(r, 2000, "v", "min")
OPEN["G_KG"] = r
# south-east block: primary school, garden
SERV["PRIMARY"], r = cut(RED["ES"], 3000, "v", "min")
OPEN["G_PRIM"] = r
# west zone: utilities, police and civil defence (600 m2 each) on the south road by the service gate, then the
# secondary school beside the club's sports fields, the rest is the park
UT, r = cut(PINK, 2000, "v", "min")
SERV["WATER"], SERV["POWER"] = cut(UT, 1000, "u", "min")
UT, r = cut(r, 1500, "v", "min")
SERV["WASTE"], ut = cut(UT, 300, "u", "min")
SERV["POLICE"], SERV["CIVIL_DEF"] = cut(ut, 600, "u", "min")
SERV["CLUB"], r = cut(r, 5000, "v", "min")
SERV["SECONDARY"], r = cut(r, 5000, "v", "min")
BIG_PARK = r

UTILITIES = ("WATER", "POWER", "WASTE")

# --- landscape of the towers' plaza (zone 6) ----------------------------------------------------------
# The spine reaches the plaza between the houses; a drop-off loop there, a promenade with a water channel
# through the gap between towers A and B, a fountain court between B and C, 4 m paved aprons round the
# towers, lawns with a winding walk and a playground on the east side, trees round the edge.
APRONS = unary_union([t.buffer(4.0, join_style="mitre") for t in TOWERS]).intersection(PLAZA.buffer(-1.0))
_gap_ab = (TOWERS[0].bounds[1] + TOWERS[1].bounds[3]) / 2
_gap_bc = (TOWERS[1].bounds[1] + TOWERS[2].bounds[3]) / 2
_px0, _py0, _px1, _py1 = PLAZA.bounds
PROMENADE = box(_px0, _gap_ab - 5.0, _px1, _gap_ab + 5.0).intersection(PLAZA)
CHANNEL = box(_px0 + 18.0, _gap_ab - 1.2, _px1 - 18.0, _gap_ab + 1.2).intersection(PLAZA.buffer(-6.0))
DROPOFF = Point((_px0, _gap_ab)).buffer(16.0).intersection(PLAZA)
FOUNTAIN_COURT = box(_px0 + 6.0, _gap_bc - 4.0, TOWERS[1].bounds[2], _gap_bc + 4.0).intersection(PLAZA)
FOUNTAIN = Point(((TOWERS[1].bounds[0] + TOWERS[1].bounds[2]) / 2, _gap_bc)).buffer(3.0)
_tx = max(t.bounds[2] for t in TOWERS) + 4.0
_east = PLAZA.difference(box(-1e3, -1e3, _tx, 1e3))


def _east_edge(v):
    seg = PLAZA.intersection(box(-1e3, v - 0.25, 1e3, v + 0.25))
    return seg.bounds[2] if not seg.is_empty else _tx


_vs = [v for v in np.arange(_py0 + 4.0, _py1 - 4.0, 2.0) if _east_edge(v) - _tx > 9.0]
WALK = LineString([((_tx + _east_edge(v)) / 2 + 2.0 * math.sin(v / 9.0), v) for v in _vs if v < _py1 - 34.0]
                  + [(_tx + 2.0, _gap_ab + 4.0)][:0])
WALK_AREA = WALK.buffer(1.5)
_top = _east.intersection(box(-1e3, _py1 - 30.0, 1e3, _py1))
PLAY = _top.buffer(-3.0, join_style="mitre")
PLAY = max(polys(PLAY), key=lambda p: p.area) if polys(PLAY) else PLAY
PAVING = unary_union([APRONS, PROMENADE, DROPOFF, FOUNTAIN_COURT, WALK_AREA]).intersection(PLAZA)
LAWN = PLAZA.buffer(-1.0).difference(PAVING.buffer(0.8)).difference(PLAY.buffer(1.0))
PLAZA_TREES = []
_ring = PLAZA.buffer(-3.5).exterior
for d in np.arange(0, _ring.length, 9.0):
    q = _ring.interpolate(d)
    if not PAVING.buffer(1.5).contains(q):
        PLAZA_TREES.append((q.x, q.y))
for d in np.arange(6.0, WALK.length, 12.0):
    q = WALK.interpolate(d)
    PLAZA_TREES.append((q.x + 4.0, q.y))

# --- gates: only two, both on the long-side roads ----------------------------------------------------
GATE_U = RB_C[0]                           # main gate on the north road, on the roundabout street
GATE = LineString([(GATE_U - 9, north_v(GATE_U - 9) - 0.3), (GATE_U + 9, north_v(GATE_U + 9) - 0.3)])
SGATE_U = float(np.mean([SERV["POWER"].bounds[0], SERV["POWER"].bounds[2]]))
SGATE = LineString([(SGATE_U - 6, 0.3), (SGATE_U + 6, 0.3)])   # service / emergency gate on the south road

# --- numbers ------------------------------------------------------------------------------------------
FLOORS, FLATS_PER_FLOOR = 20, 4
N_APTS = len(TOWERS) * FLOORS * FLATS_PER_FLOOR
PARK_NEED = math.ceil(N_APTS * 1.5)


def total(gs):
    return sum(g.area for g in gs)


GARDENS = [OPEN[k] for k in OPEN if k.startswith("G_")]
GREEN = STRIPS + [BIG_PARK, ROUNDABOUT_ISLAND] + GARDENS
LANDUSE = [
    (f"Villas 400 m2 ({len(VILLAS)}) - فلل 400 م2", total(VILLAS)),
    (f"Houses 240 m2 ({len(HOUSES)}) - دور 240 م2", total(HOUSES)),
    (f"Towers ({len(TOWERS)}) + plaza - الأبراج والبلازا", total(TOWERS) + PLAZA.area),
    ("Community services - الخدمات", total(SERV[k] for k in SERV if k not in UTILITIES)),
    ("Utilities - المرافق الفنية", total(SERV[k] for k in UTILITIES)),
    ("Gardens + green strips - الحدائق والأشرطة الخضراء", total(GREEN)),
    ("Parking (mall) - موقف المول", OPEN["PARK_MALL"].area),
    ("Roads - الشوارع", ROADS.area),
]
