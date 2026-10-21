"""Variant 3 of Ibrahim's proposal: the linear park.

Same program and presentation as Ibrahim's developed proposal, different idea:
- a continuous linear park runs the full length of the site, down its middle, instead of a central road;
- each side (north and south) has its own loop road: an outer street and a park-side street joined at
  both ends, serving a row of plots against the boundary wall and a double row between the two streets;
- the three towers stand in the middle of the park, where the park widens into the towers' plaza;
- all services are grouped in a civic quarter at the main gate, at the wide west end;
- the park ends in a large garden at the narrow east tip.

Geometry is in the local frame used by the other proposals: u along the south edge Q1->Q4,
v towards the north edge.
"""
import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

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


# --- band frames: t along an edge, s inwards from it --------------------------------------------------
_dn = np.subtract(NE, NW) / np.linalg.norm(np.subtract(NE, NW))
FRAMES = {
    "S": (np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, 1.0])),
    "N": (np.array(NW), _dn, np.array([_dn[1], -_dn[0]])),
}


def fbox(side, t0, t1, s0, s1):
    o, d, n = FRAMES[side]
    return Polygon([tuple(o + t * d + s * n) for t, s in ((t0, s0), (t1, s0), (t1, s1), (t0, s1))])


def t_of(side, u):
    """t on an edge for a given u (measured on the edge itself)."""
    o, d, _ = FRAMES[side]
    return (u - o[0]) / d[0]


# --- plot types -----------------------------------------------------------------------------------------
VILLA = (16.0, 25.0)        # frontage x depth = 400 m2
HOUSE = (12.0, 20.0)        # 240 m2
ROAD = 10.0                 # loop streets
N_VILLAS, N_HOUSES = 80, 88

# sections along the site (u on each edge): villas, the towers' stretch, houses
HUB_E = 150.0               # civic quarter west of this
ENTRY = (HUB_E, HUB_E + 14.0)          # entry road from the main gate
TWR_LEN = 130.0


def lots_row(side, t0, t1, s0, s1, w, avoid=None):
    out = []
    t = t0
    while t + w <= t1 + 1e-6:
        p = fbox(side, t, t + w, s0, s1)
        if p.within(SITE.buffer(0.01)) and (avoid is None or not p.intersects(avoid)):
            out.append(p)
        t += w
    return out


def loop_band(side, u0, u1, plot, reserve):
    """Row A against the wall, outer street, double row B+C, park-side street; the two streets meet at both
    ends of the band (the loop). A green link crosses the double row in the middle."""
    w, d = plot
    t0, t1 = t_of(side, u0), t_of(side, u1)
    tm = (t0 + t1) / 2
    lk = fbox(side, tm - 4.0, tm + 4.0, d + ROAD, 3 * d + ROAD)
    a = lots_row(side, t0, t1, 0, d, w)
    bc = lots_row(side, t0 + ROAD, t1 - ROAD, d + ROAD, 2 * d + ROAD, w, lk) + \
        lots_row(side, t0 + ROAD, t1 - ROAD, 2 * d + ROAD, 3 * d + ROAD, w, lk)
    reserve.append(fbox(side, t0, t1, 0, 3 * d + 2 * ROAD))
    return a + bc, lk


def single_band(side, u0, u1, plot, reserve):
    """Beside the towers: one row against the wall and the street (both loops pass the plaza here)."""
    w, d = plot
    t0, t1 = t_of(side, u0), t_of(side, u1)
    reserve.append(fbox(side, t0, t1, 0, d + ROAD))
    return lots_row(side, t0, t1, 0, d, w)


def build(vil_end, hou_end):
    vil, hou, res, links = [], [], [], []
    for side in ("N", "S"):
        v, lk = loop_band(side, ENTRY[1], vil_end, VILLA, res)
        vil += v
        links.append(lk)
        hou += single_band(side, vil_end, vil_end + TWR_LEN, HOUSE, res)
        h, lk = loop_band(side, vil_end + TWR_LEN, hou_end, HOUSE, res)
        hou += h
        links.append(lk)
    return vil, hou, res, links


# shortest villa and house stretches that hold the program
VIL_END = next(e for e in np.arange(380.0, 520.0, 1.0) if len(build(e, e + 300)[0]) >= N_VILLAS)
HOU_END = next(e for e in np.arange(VIL_END + TWR_LEN + 60, 860.0, 1.0) if len(build(VIL_END, e)[1]) >= N_HOUSES)
VILLAS, HOUSES, RESERVE, LINKS = build(VIL_END, HOU_END)
VIL = (ENTRY[1], VIL_END)
TWR = (VIL_END, VIL_END + TWR_LEN)
HOU = (TWR[1], HOU_END)
VILLAS = sorted(VILLAS, key=lambda p: (p.centroid.y < 150, round(p.centroid.x / 4), -p.centroid.y))
HOUSES = sorted(HOUSES, key=lambda p: (p.centroid.y < 120, round(p.centroid.x / 4), -p.centroid.y))

# --- civic quarter at the main gate ------------------------------------------------------------------
RB_C = (sum(ENTRY) / 2, 145.0)
RB_R, RB_ISL = 20.0, 10.0
ROUNDABOUT_ISLAND = Point(RB_C).buffer(RB_ISL)
SPINE = (139.0, 151.0)                 # civic street west from the roundabout
SROAD = (72.0, 82.0)                   # service street from the service gate up to the civic street

WEST = SITE.intersection(box(-100, -10, ENTRY[0], 400))
N_BLOCK = WEST.intersection(box(-100, SPINE[1], ENTRY[0], 400))
SW_BLOCK = WEST.intersection(box(-100, -10, SROAD[0], SPINE[0]))
SE_BLOCK = WEST.intersection(box(SROAD[1], -10, ENTRY[0], SPINE[0]))
# rev 1: a school drop-off lay-by along the entry road, so parents stop off the through lane
LAYBY = (ENTRY[0] - 7.0, 20.0, ENTRY[0], SPINE[0] - 6.0)
SE_BLOCK = SE_BLOCK.difference(box(*LAYBY))


def clean(g):
    g = g.buffer(-0.02, join_style="mitre").buffer(0.02, join_style="mitre")
    ps = polys(g)
    return max(ps, key=lambda p: p.area) if ps else g


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


SERV, OPEN = {}, {}
HUB_MID = 75.0
NE_BLOCK = N_BLOCK.intersection(box(HUB_MID, -10, 1e3, 400))
NW_BLOCK = N_BLOCK.intersection(box(-100, -10, HUB_MID, 400))
# north-east, at the gate: health centre on the civic street by the roundabout with a civic garden,
# the mall facing the entry road with its parking, a gate square between them
# (rev 1: mosque, kindergarten and primary school moved to the park beside the towers, the heart of the plan)
low, up = cut(NE_BLOCK, 3000, "v", "min")
SERV["HEALTH"], OPEN["G_CIVIC"] = cut(low, 1000, "u", "max")
OPEN["PARK_MALL"], r = cut(up, 1600, "u", "max")
SERV["MALL"], OPEN["G_PLAZA"] = cut(r, 3000, "u", "max")
# north-west: the club was dropped from the programme (rev 1); the whole block is the west garden
OPEN["G_WEST"] = clean(NW_BLOCK)
# south-east: primary school on the civic street, secondary school on the south side, a garden between
# (rev 1: the primary school moved to the park beside the towers)
SERV["SECONDARY"], OPEN["G_SCHOOL"] = cut(SE_BLOCK, 5000, "v", "min")
# south-west, by the service gate: utilities, police and civil defence in a row along the service street,
# a buffer garden behind them
row, OPEN["G_UTIL"] = cut(SW_BLOCK, 3500, "u", "max")
for k, a in (("WATER", 1000), ("POWER", 1000), ("WASTE", 300), ("CIVIL_DEF", 600)):
    SERV[k], row = cut(row, a, "v", "min")
SERV["POLICE"] = row
UTILITIES = ("WATER", "POWER", "WASTE")

# --- the linear park and the towers in it ------------------------------------------------------------
BANDS = unary_union(RESERVE)
PARK_ALL = SITE.intersection(box(ENTRY[1], -10, 1e4, 400)).difference(BANDS)
PARK_ALL = max(polys(PARK_ALL.difference(Point(RB_C).buffer(RB_R + 3.0))), key=lambda p: p.area)

TOWER_SIDE = 31.5
_tc = (TWR[0] + TWR[1]) / 2
_vc = (north_v(_tc) - (HOUSE[1] + ROAD)) / 2 + (HOUSE[1] + ROAD) / 2
TOWERS = [box(x - TOWER_SIDE / 2, _vc - TOWER_SIDE / 2, x + TOWER_SIDE / 2, _vc + TOWER_SIDE / 2)
          for x in (_tc - 44.0, _tc, _tc + 44.0)]
# towers diagonal-staggered so every flat looks along the park
TOWERS = [box(t.bounds[0], t.bounds[1] + dv, t.bounds[2], t.bounds[3] + dv) for t, dv in zip(TOWERS, (14, -14, 14))]
PLAZA_ALL = box(_tc - 78.0, _vc - 42.0, _tc + 78.0, _vc + 42.0).intersection(PARK_ALL)
PLAZA = PLAZA_ALL.difference(unary_union(TOWERS))

# rev 1: kindergarten, primary school and mosque in the park round the towers' plaza, each on a loop street
# and a drop-off lane, so the daily walks of every home are short and stay inside the park
_south = PARK_ALL.intersection(box(_tc - 70.0, -10, _tc - 9.0, PLAZA_ALL.bounds[1]))
SERV["KG"], _ = cut(_south, 1500, "u", "max")
_north = PARK_ALL.intersection(box(_tc - 150.0, PLAZA_ALL.bounds[3] - 6.0, _tc - 9.0, 400))
SERV["PRIMARY"], _ = cut(_north, 3000, "u", "max")
_south_e = PARK_ALL.intersection(box(_tc + 9.0, -10, _tc + 78.0, PLAZA_ALL.bounds[1]))
SERV["MOSQUE"], _ = cut(_south_e, 2000, "u", "min")
PARK_ALL = PARK_ALL.difference(SERV["KG"]).difference(SERV["MOSQUE"]).difference(SERV["PRIMARY"])
PLAZA_ALL = PLAZA_ALL.difference(SERV["PRIMARY"])
PLAZA = PLAZA_ALL.difference(unary_union(TOWERS))

# drop-off lanes from both loops into the plaza ends (the only park crossings for cars)
DROP = [box(_tc - 5.0, -10, _tc + 5.0, PLAZA_ALL.bounds[1] + 1.0).intersection(PARK_ALL),
        box(_tc - 5.0, PLAZA_ALL.bounds[3] - 1.0, _tc + 5.0, 400).intersection(PARK_ALL)]
DROP = [d.difference(PLAZA_ALL) for d in DROP]
PARK = PARK_ALL.difference(PLAZA_ALL).difference(unary_union(DROP))
# cut the park into garden rooms with paved cross walks every ~110 m, the east tip is one big garden
EAST_GARDEN_U = HOU[1]
WALKS = []
for u in ((ENTRY[1] + VIL_END) / 2 + 40.0, (TWR[1] + HOU_END) / 2 + 40.0):
    WALKS.append(box(u - 3.0, -10, u + 3.0, 400).intersection(PARK))
GARDEN_ROOMS = polys(PARK.difference(unary_union(WALKS)))
GARDEN_ROOMS = [g for g in GARDEN_ROOMS if g.area > 300]
EAST_GARDEN = max(GARDEN_ROOMS, key=lambda g: g.centroid.x)
WALKS = [w for w in WALKS if not w.is_empty]
# rev 1: emergency link (grass-crete, bollards) across the east garden joins the two loops into one ring
EMERG_U = HOU_END + 12.0
EMERG = box(EMERG_U - 2.5, -10, EMERG_U + 2.5, 400).intersection(EAST_GARDEN)

ROADS = SITE.difference(unary_union(VILLAS + HOUSES + list(SERV.values()) + list(OPEN.values())
                                    + [PARK_ALL, ROUNDABOUT_ISLAND] + LINKS))
ROADS = ROADS.union(unary_union(DROP))
# the leftover corner pieces of the band reserves are road too; tidy slivers
ROADS = ROADS.buffer(-0.05, join_style="mitre").buffer(0.05, join_style="mitre")

# --- landscape of the plaza (same scheme as the developed proposal) --------------------------------
APRONS = unary_union([t.buffer(4.0, join_style="mitre") for t in TOWERS]).intersection(PLAZA.buffer(-1.0))
_px0, _py0, _px1, _py1 = PLAZA_ALL.bounds
PROMENADE = box(_px0, _vc - 5.0, _px1, _vc + 5.0).intersection(PLAZA)
PROMENADE = unary_union([PROMENADE, box(_tc - 5.0, _py0, _tc + 5.0, _py1).intersection(PLAZA)])
CHANNEL = unary_union([box(_px0 + 6.0, _vc - 1.2, _tc - 22.0 - 4, _vc + 1.2),
                       box(_tc + 22.0 + 4, _vc - 1.2, _px1 - 6.0, _vc + 1.2)]).intersection(PLAZA.buffer(-5.0))
DROPOFF = unary_union([Point((_tc, _py0)).buffer(14.0), Point((_tc, _py1)).buffer(14.0)]).intersection(PLAZA)
FOUNTAIN = Point((_tc - 22.0, _vc - 22.0)).buffer(3.6)
FOUNTAIN2 = Point((_tc + 22.0, _vc + 22.0)).buffer(3.6)
FOUNTAIN = unary_union([FOUNTAIN, FOUNTAIN2])
FOUNTAIN_COURT = unary_union([f.buffer(5.5) for f in polys(FOUNTAIN)]).intersection(PLAZA)
FOUNTAIN_RING = FOUNTAIN_COURT.difference(FOUNTAIN.buffer(1.0))
PAVING = unary_union([APRONS, PROMENADE, DROPOFF, FOUNTAIN_COURT]).intersection(PLAZA)
PLAY = box(_px1 - 30.0, _py1 - 26.0, _px1 - 6.0, _py1 - 8.0).intersection(PLAZA).difference(PAVING.buffer(1.0))
PLAY = max(polys(PLAY), key=lambda p: p.area) if polys(PLAY) else PLAY
LAWN = PLAZA.buffer(-1.0).difference(PAVING.buffer(0.8)).difference(PLAY.buffer(1.0))
PLAZA_TREES = []
_ring = PLAZA_ALL.buffer(-3.5).exterior
for d in np.arange(0, _ring.length, 9.0):
    q = _ring.interpolate(d)
    if not PAVING.buffer(1.5).contains(q):
        PLAZA_TREES.append((q.x, q.y))
PALMS = []
for u in np.arange(_px0 + 8.0, _px1 - 6.0, 6.0):
    for dv in (-3.6, 3.6):
        q = Point(u, _vc + dv)
        if PLAZA.buffer(-1.5).contains(q) and not unary_union(TOWERS).buffer(5.0).contains(q):
            PALMS.append((q.x, q.y))
JETS = [Point(u, _vc).buffer(0.5) for g in polys(CHANNEL) for u in np.arange(g.bounds[0] + 3.0, g.bounds[2] - 2.0, 4.0)]
PLANTERS = [box(f.centroid.x + dx - 1.2, f.centroid.y - 1.2, f.centroid.x + dx + 1.2, f.centroid.y + 1.2)
            for f in polys(FOUNTAIN) for dx in (-8.0, 8.0)]
DROP_ISLAND = unary_union([Point((_tc, _py0 + 4.0)).buffer(4.0), Point((_tc, _py1 - 4.0)).buffer(4.0)]).intersection(PLAZA)
PLAY_KIT = [Point(PLAY.centroid.x + dx, PLAY.centroid.y + dy).buffer(1.2) for dx, dy in ((-5, 1.5), (0, -2), (5, 1.5))] \
    if not PLAY.is_empty else []

# --- gates: only two, both on the long-side roads ----------------------------------------------------
GATE_U = RB_C[0]
GATE = LineString([(GATE_U - 9, north_v(GATE_U - 9) - 0.3), (GATE_U + 9, north_v(GATE_U + 9) - 0.3)])
SGATE_U = sum(SROAD) / 2
SGATE = LineString([(SGATE_U - 6, 0.3), (SGATE_U + 6, 0.3)])

# --- numbers ------------------------------------------------------------------------------------------
FLOORS, FLATS_PER_FLOOR = 20, 4
N_APTS = len(TOWERS) * FLOORS * FLATS_PER_FLOOR
PARK_NEED = math.ceil(N_APTS * 1.5)


def total(gs):
    return sum(g.area for g in gs)


GARDENS = [OPEN[k] for k in OPEN if k.startswith("G_")]
GREEN_LINKS = LINKS
GREEN = GARDEN_ROOMS + WALKS + GARDENS + GREEN_LINKS + [ROUNDABOUT_ISLAND]
LANDUSE = [
    (f"Villas 400 m2 ({len(VILLAS)}) - فلل 400 م2", total(VILLAS)),
    (f"Houses 240 m2 ({len(HOUSES)}) - دور 240 م2", total(HOUSES)),
    (f"Towers ({len(TOWERS)}) + plaza - الأبراج والبلازا", PLAZA_ALL.area),
    ("Community services - الخدمات", total(SERV[k] for k in SERV if k not in UTILITIES)),
    ("Utilities - المرافق الفنية", total(SERV[k] for k in UTILITIES)),
    ("Linear park + gardens - الحديقة الطولية والحدائق", total(GREEN)),
    ("Parking (mall) - موقف المول", OPEN["PARK_MALL"].area),
    ("Roads - الشوارع", ROADS.area),
]
