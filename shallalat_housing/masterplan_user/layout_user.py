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
# north-west block, beside the main gate: mall, then the mosque, parking on the roundabout side
SERV["MALL"], r = cut(RED["WN"], 3000, "v", "max")
SERV["MOSQUE"], r = cut(r, 2000, "u", "min")
OPEN["PARK_MALL"] = r
# north-east block, beside the main gate: police + civil defence, health centre, garden
SERV["POLICE_CD"], r = cut(RED["EN"], 600, "v", "max")
SERV["HEALTH"], r = cut(r, 1000, "v", "max")
OPEN["G_HEALTH"] = r
# south-west block: secondary school (intermediate + preparatory merged)
SERV["SECONDARY"], r = cut(RED["WS"], 5000, "v", "min")
OPEN["G_SEC"] = r
# south-east block: primary school, kindergarten
SERV["PRIMARY"], r = cut(RED["ES"], 3000, "v", "min")
SERV["KG"], r = cut(r, 1500, "v", "min")
OPEN["G_KG"] = r
# west zone: utilities on the south road by the service gate, the club, the rest is the big park
UT, r = cut(PINK, 2300, "v", "min")
SERV["WATER"], ut = cut(UT, 1000, "u", "min")
SERV["POWER"], SERV["WASTE"] = cut(ut, 1000, "u", "min")
SERV["CLUB"], r = cut(r, 5000, "v", "min")
BIG_PARK = r

UTILITIES = ("WATER", "POWER", "WASTE")

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


GREEN = STRIPS + [BIG_PARK, OPEN["G_HEALTH"], OPEN["G_SEC"], OPEN["G_KG"], ROUNDABOUT_ISLAND]
LANDUSE = [
    (f"Villas 400 m2 ({len(VILLAS)}) - فلل 400 م2", total(VILLAS)),
    (f"Houses 240 m2 ({len(HOUSES)}) - دور 240 م2", total(HOUSES)),
    (f"Towers ({len(TOWERS)}) + plaza - الأبراج والبلازا", total(TOWERS) + PLAZA.area),
    ("Community services - الخدمات", total(SERV[k] for k in SERV if k not in UTILITIES)),
    ("Utilities - المرافق الفنية", total(SERV[k] for k in UTILITIES)),
    ("Gardens + green strips - الحدائق والأشرطة الخضراء", total(GREEN)),
    ("Parking (mall + mosque) - موقف السوق والجامع", OPEN["PARK_MALL"].area),
    ("Roads - الشوارع", ROADS.area),
]
