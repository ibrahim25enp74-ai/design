"""Geometry of master plan proposal B "The Green Heart", revision 2 (client program of 2026-10-21 evening) (plot 157 / district 53 Baybokht).

Built in a local frame and transformed to UTM 38S on output:
  s = metres along the south long side, from Q1 (west end) towards Q4 (east end)
  t = metres square to it, from the south side towards the north side
"""
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

Q_UTM = [(338955.19, 4035466.71), (339030.78, 4035766.16), (339833.37, 4035331.92), (339749.71, 4035202.20)]
O = np.array(Q_UTM[0])
U = np.subtract(Q_UTM[3], Q_UTM[0]) / np.linalg.norm(np.subtract(Q_UTM[3], Q_UTM[0]))
N = np.array([-U[1], U[0]])


def to_utm(s, t):
    p = O + s * U + t * N
    return float(p[0]), float(p[1])


def to_local(x, y):
    d = np.subtract((x, y), O)
    return float(d @ U), float(d @ N)


SITE = Polygon([to_local(*q) for q in Q_UTM])
BIG = 1000


def t_north(s):
    (s1, t1), (s2, t2) = SITE.exterior.coords[1], SITE.exterior.coords[2]
    return t1 + (s - s1) * (t2 - t1) / (s2 - s1)


def clip(g):
    return g.intersection(SITE)


# --- context traced from the scan (approximate, see site plan) ----------------------------------------
CROSS_ROAD = LineString([(143.8, -1.4), (115.3, 285.7)])
WATERCOURSE = LineString([(659.0, -131.0), (669.1, -70.8), (678.2, -6.0), (683.8, 69.6), (676.0, 130.8),
                          (683.2, 191.2), (722.1, 271.1), (755.0, 349.8)])
TREES = [(29.2, 70.1), (28.1, 138.5), (53.2, 197.9), (66.5, 52.9), (69.6, 118.1), (92.0, 180.6), (74.6, 234.7)]

# --- the heart: oval park, 16 m ring road, gate boulevard, tower plaza ----------------------------------
PARK_C = (450.0, 100.0)
PARK_A, PARK_B = 115.0, 45.0
RING_W = 16.0
PARK = affinity.scale(Point(PARK_C).buffer(1.0, resolution=96), PARK_A, PARK_B)
RING_OUT = PARK.buffer(RING_W, resolution=48)
RING = RING_OUT.difference(PARK)
GATE_S = PARK_C[0]
BOULEVARD = clip(box(GATE_S - 12, PARK_C[1], GATE_S + 12, BIG)).difference(PARK)
BOULEVARD_MEDIAN = clip(box(GATE_S - 3, PARK_C[1] + PARK_B + RING_W, GATE_S + 3, BIG))

# three towers 31.5 x 31.5 m (4 flats a floor, G+19), 33 m apart, 12 m off the fence; the gate passes between 2 and 3
TOWER = 31.5
N_TOWERS = 3
_tw_s0 = [GATE_S - 24 - TOWER - 33 - TOWER, GATE_S - 24 - TOWER, GATE_S + 24]
TOWERS = []
for s0 in _tw_s0:
    top = t_north(s0 + TOWER) - 12
    TOWERS.append(box(s0, top - TOWER, s0 + TOWER, top))

# --- road network ---------------------------------------------------------------------------------------
W_LOCAL = 14.0
AVENUE_HALF = 10.0  # old cross road taken into the plan as a 20 m tree-lined avenue (needs approval)
AVENUE = clip(CROSS_ROAD.buffer(AVENUE_HALF, cap_style=2))
WEST_LOOP = clip(Polygon([(-40, -5), (-40, 320), (-22.87 + W_LOCAL, 308.0 + 1), (W_LOCAL + 0.4, -5)]))
WEST_COLL_S = (300.0, 316.0)
WEST_COLL = clip(box(WEST_COLL_S[0], -5, WEST_COLL_S[1], BIG))
WEST_LINK = box(WEST_COLL_S[1] - 1, PARK_C[1] - 7, PARK_C[0] - PARK_A - RING_W + 4, PARK_C[1] + 7)
EAST_ST_S = (690.0, 704.0)  # N-S street of the east villa quarter
EAST_ST = clip(box(EAST_ST_S[0], -5, EAST_ST_S[1], BIG))
EAST_LOOP_S = 754.0
EAST_SPINE = clip(box(PARK_C[0] + PARK_A + RING_W - 4, PARK_C[1] - 7, EAST_LOOP_S + 1, PARK_C[1] + 7))
EAST_LOOP = clip(box(EAST_LOOP_S, -5, EAST_LOOP_S + W_LOCAL, BIG))
UTIL_S = EAST_LOOP_S + W_LOCAL + 25

VILLA_STREETS_T = [32.0, 96.0, 160.0, 224.0]  # villa blocks 25+25 deep, spacing 64
HOUSE_STREETS_T = [31.0, 93.0, 155.0]  # house blocks 24+24 deep (10 x 24 = 240 m2 lots), spacing 62
HOUSE_W, HOUSE_D = 10.0, 24.0


def avenue_edge(side, t):
    """s of the avenue edge (side -1 west, +1 east) at height t."""
    (s0, t0), (s1, t1) = CROSS_ROAD.coords
    s = s0 + (t - t0) * (s1 - s0) / (t1 - t0)
    return s + side * AVENUE_HALF / 0.995


villa_streets = [clip(box(0, tc - W_LOCAL / 2, avenue_edge(-1, tc) + 3, tc + W_LOCAL / 2)) for tc in VILLA_STREETS_T]
house_streets = [clip(box(avenue_edge(1, tc) - 3, tc - W_LOCAL / 2, WEST_COLL_S[0] + 1, tc + W_LOCAL / 2))
                 for tc in HOUSE_STREETS_T]

ROADS = {
    "RING": RING,
    "BOULEVARD": BOULEVARD,
    "AVENUE": AVENUE,
    "COLLECTOR": unary_union([WEST_COLL, WEST_LINK, EAST_SPINE]),
    "LOCAL": unary_union(villa_streets + house_streets + [WEST_LOOP, EAST_ST, EAST_LOOP]),
}
ALL_ROADS = unary_union(list(ROADS.values()))

ORCHARD = box(38, 103, 98, 153)
def pack(tc, side, s0, s1, width, depth, zone, w=W_LOCAL):
    """Greedy row of lots along the street at tc, on its north (+1) or south (-1) side."""
    t_front = tc + side * w / 2
    t_back = t_front + side * depth
    z = zone.buffer(0.05)
    out, s = [], s0
    while s + width <= s1:
        lot = box(s, min(t_front, t_back), s + width, max(t_front, t_back))
        if z.contains(lot):
            out.append(lot)
            s += width
        else:
            s += 0.5
    return out


def pack_t(s_front, side, t0, t1, width, depth, zone):
    """Greedy row of lots fronting a N-S street edge at s_front, extending west (-1) or east (+1)."""
    s_back = s_front + side * depth
    z = zone.buffer(0.05)
    out, t = [], t0
    while t + width <= t1:
        lot = box(min(s_front, s_back), t, max(s_front, s_back), t + width)
        if z.contains(lot):
            out.append(lot)
            t += width
        else:
            t += 0.5
    return out


BUILDABLE = SITE.difference(ALL_ROADS.buffer(0.01))
west_of_avenue = Polygon([(-50, -50), (avenue_edge(-1, -50), -50), (avenue_edge(-1, 400), 400), (-50, 400)])
east_of_avenue = Polygon([(avenue_edge(1, -50), -50), (WEST_COLL_S[0], -50), (WEST_COLL_S[0], 400), (avenue_edge(1, 400), 400)])

N_VILLAS, N_HOUSES = 80, 88
VILLA_ZONE_W = BUILDABLE.intersection(west_of_avenue).difference(ORCHARD)
HOUSE_ZONE = BUILDABLE.intersection(east_of_avenue)

villas, houses = [], []
for tc in VILLA_STREETS_T:
    for side in (1, -1):
        villas += pack(tc, side, 0, 200, 16, 25, VILLA_ZONE_W)
# east villa quarter: columns on the east street and the east loop, filled until the program is met
for s_front, side in ((EAST_ST_S[0], -1), (EAST_ST_S[1], 1), (EAST_LOOP_S, -1), (EAST_LOOP_S + W_LOCAL, 1)):
    col = pack_t(s_front, side, 0, 300, 16, 25, BUILDABLE)
    villas += col[: max(0, N_VILLAS - len(villas))]
# houses: rows from the south, the rest of the quarter becomes pocket gardens
rows = []
for tc in HOUSE_STREETS_T:
    for side in (-1, 1):
        rows.append(pack(tc, side, 100, WEST_COLL_S[0], HOUSE_W, HOUSE_D, HOUSE_ZONE))
for row in rows:
    take = max(0, N_HOUSES - len(houses))
    houses += sorted(row, key=lambda g: -g.bounds[0])[:take]

# --- services (client program, m2) -------------------------------------------------------------------------
HEART_FREE = SITE.difference(RING_OUT.buffer(3)).difference(BOULEVARD.buffer(3)).difference(ALL_ROADS.buffer(3))


def parcel(s0, s1, t0=-5, t1=BIG, base=HEART_FREE):
    return base.intersection(box(s0, t0, s1, t1))


def fit(s0, target, t0=-5, t1=BIG, base=HEART_FREE, back=False):
    """Parcel starting at s0 (or ending at s0 when back) whose area is `target`."""
    lo, hi = 0.0, 400.0
    for _ in range(60):
        mid = (lo + hi) / 2
        g = parcel(s0 - mid, s0, t0, t1, base) if back else parcel(s0, s0 + mid, t0, t1, base)
        lo, hi = (mid, hi) if g.area < target else (lo, mid)
    return g


SOUTH = (-5, PARK_C[1])
NORTH = (PARK_C[1], BIG)
GAP = 3.0
mosque_half = 0
lo, hi = 5.0, 60.0
for _ in range(50):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if parcel(GATE_S - mid, GATE_S + mid, *SOUTH).area < 2000 else (lo, mid)
MOSQUE = parcel(GATE_S - mid, GATE_S + mid, *SOUTH)
m0, m1 = GATE_S - mid, GATE_S + mid

health = fit(m0 - GAP, 1000, -5, 36, back=True)
civil = fit(health.bounds[0] - GAP, 600, -5, 30, back=True)
police = fit(civil.bounds[0] - GAP, 600, -5, 30, back=True)
mall = fit(m1 + GAP, 3000, *SOUTH)
kinder = fit(mall.bounds[2] + GAP, 1500, *SOUTH)
primary = fit(kinder.bounds[2] + GAP, 3000, *SOUTH)
PLAZA_END = TOWERS[2].bounds[2] + 14
secondary = fit(PLAZA_END + GAP, 5000, *NORTH)  # the club was dropped by the client; its land is green
TIP = BUILDABLE.intersection(box(UTIL_S, -5, BIG, BIG))
power = fit(UTIL_S + 3, 1000, -5, 36, TIP)  # fronts the south public road
water = fit(UTIL_S + 3, 1000, 39, 75, TIP)
waste = fit(power.bounds[2] + GAP, 300, -5, 26, TIP)

SERVICES = {
    "MOSQUE - جامع": MOSQUE,
    "HEALTH CENTRE - مركز صحي": health,
    "CIVIL DEFENCE - دفاع مدني": civil,
    "POLICE - مركز شرطة": police,
    "MALL - مول": mall,
    "KINDERGARTEN - روضة": kinder,
    "PRIMARY SCHOOL - مدرسة ابتدائية": primary,
    "SECONDARY SCHOOL - ثانوية (متوسطة وإعدادية)": secondary,
    "POWER STATION - محطة كهرباء": power,
    "WATER STATION - محطة ماء": water,
    "WASTE POINT - نقطة نفايات": waste,
}
PROGRAM = {"MOSQUE": 2000, "HEALTH": 1000, "CIVIL": 600, "POLICE": 600, "MALL": 3000, "KINDERGARTEN": 1500,
           "PRIMARY": 3000, "SECONDARY": 5000, "POWER": 1000, "WATER": 1000, "WASTE": 300}
TOWER_ZONE = parcel(WEST_COLL_S[1], PLAZA_END, *NORTH)  # tower plaza over the basement car park
SPORTS = Polygon()

# --- open space ----------------------------------------------------------------------------------------------
GATEHOUSE = box(GATE_S - 3, t_north(GATE_S) - 14, GATE_S + 3, t_north(GATE_S) - 4)
LOTS = unary_union(villas + houses)
USED = unary_union([LOTS, ALL_ROADS, PARK, ORCHARD, unary_union(list(SERVICES.values())), TOWER_ZONE])
BUFFERS = SITE.difference(USED)  # every leftover piece is landscaped: pocket gardens, east park, verges, belts
# indicative footprints: villa 12 x 10 m (30 %) with 4 m front setback, house 10 x 12 m (60 %) with 2.5 m
def footprint(lot, kind, front):
    (s0, t0, s1, t1) = lot.bounds
    if kind == "V":
        w, d, sb = 12.0, 10.0, 4.0
    else:
        w, d, sb = 10.0, 14.0, 3.0
    if front in ("N", "S"):
        sc = (s0 + s1) / 2
        tf = t1 - sb if front == "N" else t0 + sb
        return box(sc - w / 2, min(tf, tf - d if front == "N" else tf + d), sc + w / 2, max(tf, tf - d if front == "N" else tf + d))
    tc = (t0 + t1) / 2
    sf = s1 - sb if front == "E" else s0 + sb
    return box(min(sf, sf - d if front == "E" else sf + d), tc - w / 2, max(sf, sf - d if front == "E" else sf + d), tc + w / 2)


def lot_front(lot):
    """Side of the lot that touches a road."""
    s0, t0, s1, t1 = lot.bounds
    probes = {"N": ((s0 + s1) / 2, t1 + 1), "S": ((s0 + s1) / 2, t0 - 1), "W": (s0 - 1, (t0 + t1) / 2), "E": (s1 + 1, (t0 + t1) / 2)}
    for k, p in probes.items():
        if ALL_ROADS.contains(Point(p)):
            return k
    return "S"
