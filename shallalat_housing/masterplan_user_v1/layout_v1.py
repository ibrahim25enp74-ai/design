"""Variant 1 of Ibrahim's proposal - "the green ring" (الحلقة الخضراء).

Same program and drawing style as Ibrahim's developed proposal, different idea:
one ring road runs round the whole plot 25 m inside the boundary.
 - Outside the ring: the 80 villas (400 m2) in one row, backs to the boundary wall, fronts on the ring,
   in groups of six with pocket gardens between them.
 - Inside the ring: the 88 houses (240 m2) in eleven short cul-de-sac clusters of eight that end on the
   green; between the clusters green fingers lead from the ring to a central park that runs west-east.
 - West end: education + sports campus (secondary school, club). Centre: civic core on the main-gate axis
   with a roundabout (mall, mosque, health, primary, kindergarten). East: the three towers on a plaza,
   then the Shallalat garden (lake + cascades) at the east tip. Utilities, police and civil defence by
   the service gate on the south road.
No street at the short ends, no local street opens to the outer roads: one main gate (north road) and one
service / emergency gate (south road).

Local frame as in the other proposals: u along the south edge Q1->Q4, v towards the north edge.
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
SW_, NW, NE, SE = [loc(q) for q in Q]


def north_v(u):
    return NW[1] + (u - NW[0]) * (NE[1] - NW[1]) / (NE[0] - NW[0])


class Frame:
    """Edge frame: t along a boundary edge, n inwards from it."""

    def __init__(self, a, b):
        self.a = np.array(a)
        self.t = (np.array(b) - self.a) / np.linalg.norm(np.subtract(b, a))
        n = np.array([-self.t[1], self.t[0]])
        c = np.array(SITE.centroid.coords[0])
        self.n = n if (c - self.a) @ n > 0 else -n
        self.length = float(np.linalg.norm(np.subtract(b, a)))

    def p(self, t, n):
        q = self.a + t * self.t + n * self.n
        return float(q[0]), float(q[1])

    def rect(self, t0, t1, n0, n1):
        return Polygon([self.p(t0, n0), self.p(t1, n0), self.p(t1, n1), self.p(t0, n1)])

    def t_of(self, q):
        return float((np.array(q) - self.a) @ self.t)


FS = Frame(SW_, SE)          # south edge (long side, outer road)
FN = Frame(NW, NE)           # north edge (long side, outer road)
FW = Frame(SW_, NW)          # west short end (no street)


def clean(g):
    g = g.buffer(-0.02, join_style="mitre").buffer(0.02, join_style="mitre")
    ps = polys(g)
    return max(ps, key=lambda p: p.area) if ps else g


def cut(poly, area, axis="v", side="min"):
    """Cut a piece of `area` m2 off `poly` with a line across `axis`, from its min / max side."""
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


# --- the ring --------------------------------------------------------------------------------------
BELT = 25.0            # villa row: plot depth, back to the boundary
RING_W = 14.0          # 8 m carriageway + 3 m walks
RING_R = 30.0          # corner radius
R_OUT = SITE.buffer(-BELT - RING_R, join_style="mitre").buffer(RING_R)
INNER = R_OUT.buffer(-RING_W)
RING = R_OUT.difference(INNER)
OUTER_BELT = SITE.difference(R_OUT)
IN0 = BELT + RING_W    # depth of the inner edge of the ring from a long side


def north_in(u):
    """v of the inner edge of the ring's north side at u."""
    return north_v(u) - IN0 / math.cos(math.atan2(NE[1] - NW[1], NE[0] - NW[0]))


# --- gates and the main axis -------------------------------------------------------------------------
GATE_U = 450.0
SGATE_U = 698.0
RB_C = (GATE_U, (IN0 + north_in(GATE_U)) / 2)
RB_R, RB_ISL = 20.0, 10.0
AXIS_N = box(GATE_U - 10, RB_C[1], GATE_U + 10, 400).intersection(SITE)            # 20 m boulevard
MEDIAN = box(GATE_U - 2, RB_C[1] + RB_R + 6, GATE_U + 2, north_v(GATE_U) - 6)
AXIS_S = box(GATE_U - 6, IN0 - 1, GATE_U + 6, RB_C[1])                              # 12 m street
ROUNDABOUT = Point(RB_C).buffer(RB_R)
RB_ISLAND = Point(RB_C).buffer(RB_ISL)
SG_ROAD = box(SGATE_U - 6, -1, SGATE_U + 6, BELT + 1).intersection(SITE)
GATE = LineString([(GATE_U - 10, north_v(GATE_U - 10) - 0.3), (GATE_U + 10, north_v(GATE_U + 10) - 0.3)])
SGATE = LineString([(SGATE_U - 6, 0.3), (SGATE_U + 6, 0.3)])

# --- villas: one row outside the ring, groups of six, pocket gardens between ------------------------
VW, GROUP, POCKET = 16.0, 6, 10.0
VILLA_TARGET = 80
NO_VILLA = unary_union([AXIS_N.buffer(4), SG_ROAD.buffer(4), box(SGATE_U - 6, -5, 900, 60)])


def villa_row(frame, t0, t1):
    out, t, k = [], t0, 0
    while t + VW <= t1:
        r = frame.rect(t, t + VW, 0.0, BELT)
        if r.difference(OUTER_BELT).area < 0.5 and not r.intersects(NO_VILLA):
            out.append(r)
            k += 1
            t += VW
            if k % GROUP == 0:
                t += POCKET
        else:
            t += 1.0
            k = 0 if k % GROUP == 0 else k
    return out


_north = villa_row(FN, 30.0, FN.length - 20.0)
_south = villa_row(FS, 30.0, FS.length)
VILLAS = (_north + _south)[:VILLA_TARGET]

# --- houses: eleven cul-de-sac clusters of eight inside the ring --------------------------------------
HW, HD, PER_SIDE, LANE = 12.0, 20.0, 4, 8.0
HEAD = 10.0
CL_DEPTH = PER_SIDE * HW + HEAD           # 58 m from the ring


def cluster(frame, tc):
    plots, lane = [], frame.rect(tc - LANE / 2, tc + LANE / 2, IN0 - 1.0, IN0 + PER_SIDE * HW)
    head = frame.rect(tc - 12.0, tc + 12.0, IN0 + PER_SIDE * HW, IN0 + CL_DEPTH)
    for s in (-1, 1):
        a, b = (tc + LANE / 2, tc + LANE / 2 + HD) if s > 0 else (tc - LANE / 2 - HD, tc - LANE / 2)
        for k in range(PER_SIDE):
            plots.append(frame.rect(a, b, IN0 + k * HW, IN0 + (k + 1) * HW))
    return plots, lane, head


CL_PITCH = 55.0
CL_SOUTH_T = [150.0 + CL_PITCH / 2 + CL_PITCH * k for k in range(4)] + [535.0 + CL_PITCH / 2 + CL_PITCH * k for k in range(3)]
CL_NORTH_T = [FN.t_of((u, north_v(u))) for u in [150.0 + CL_PITCH / 2 + CL_PITCH * k for k in range(4)]]
HOUSES, LANES, HEADS = [], [], []
for fr, ts in ((FS, CL_SOUTH_T), (FN, CL_NORTH_T)):
    for tc in ts:
        p, ln, hd = cluster(fr, tc)
        HOUSES += p
        LANES.append(ln)
        HEADS.append(hd)
HOUSES.sort(key=lambda p: (round(p.centroid.x / 30), -p.centroid.y))
CLUSTERS = unary_union(HOUSES + LANES + HEADS)

# --- towers on a plaza (basement car park), north of the eastern clusters ----------------------------
TW_SIDE = 31.5
TOWERS = []
for u in (566.0, 614.0, 662.0):
    tc = FN.t_of((u, north_v(u)))
    TOWERS.append(FN.rect(tc - TW_SIDE / 2, tc + TW_SIDE / 2, IN0 + 7.0, IN0 + 7.0 + TW_SIDE))
PLAZA_ZONE = INNER.intersection(box(530.0, IN0 + CL_DEPTH + 6.0, 708.0, 400))
PLAZA = clean(PLAZA_ZONE).difference(unary_union(TOWERS))

# --- services ---------------------------------------------------------------------------------------
SERV, OPEN = {}, {}
_civ_free = INNER.difference(ROUNDABOUT.buffer(3)).difference(AXIS_N.buffer(3)).difference(AXIS_S.buffer(3))
# civic core round the roundabout: daily services, each in its garden
_nw = clean(_civ_free.intersection(box(370, RB_C[1], GATE_U, 400)))
SERV["MALL"], r = cut(_nw, 3000, "v", "max")
OPEN["PARK_MALL"], r = cut(r, 1200, "u", "min")
OPEN["G_MALL"] = r
_ne = clean(_civ_free.intersection(box(GATE_U, RB_C[1], 530, 400)))
SERV["MOSQUE"], r = cut(_ne, 2000, "v", "max")
SERV["HEALTH"], r = cut(r, 1000, "u", "max")
OPEN["G_MOSQUE"] = r
_sw = clean(_civ_free.intersection(box(370, -10, GATE_U, RB_C[1])))
SERV["PRIMARY"], r = cut(_sw, 3000, "v", "min")
OPEN["G_PRIM"] = r
_se = clean(_civ_free.intersection(box(GATE_U, -10, 530, RB_C[1])))
SERV["KG"], r = cut(_se, 1500, "v", "min")
OPEN["G_KG"] = r
# west end: education + sports campus
_west = clean(INNER.intersection(box(-100, -10, 150.0 - 6.0, 400)))
SERV["SECONDARY"], r = cut(_west, 5000, "v", "max")
SERV["CLUB"], r = cut(r, 5000, "v", "min")
WEST_PARK = r
# utilities + police + civil defence in the villa row east of the service gate
_ut = clean(OUTER_BELT.intersection(box(SGATE_U + 6, -10, 900, 120)).intersection(box(-1e3, -10, 1e3, 70)))
SERV["POLICE"], r = cut(_ut, 600, "u", "min")
SERV["CIVIL_DEF"], r = cut(r, 600, "u", "min")
SERV["WATER"], r = cut(r, 1000, "u", "min")
SERV["POWER"], r = cut(r, 1000, "u", "min")
SERV["WASTE"], r = cut(r, 300, "u", "min")
UT_GREEN = r
UTILITIES = ("WATER", "POWER", "WASTE")

# --- roads -------------------------------------------------------------------------------------------
ROADS = unary_union([RING, AXIS_N, AXIS_S, ROUNDABOUT, SG_ROAD] + LANES + HEADS).intersection(SITE)
ROADS = ROADS.difference(RB_ISLAND).difference(MEDIAN)

# --- green: everything left inside and outside the ring ------------------------------------------------
_taken = unary_union(VILLAS + HOUSES + TOWERS + [PLAZA, ROADS, RB_ISLAND, MEDIAN, CLUSTERS] + list(SERV.values())
                     + list(OPEN.values()) + [WEST_PARK, UT_GREEN])
_inner_left = INNER.difference(_taken)
# the Shallalat garden at the east tip, with a lake and cascades
EAST_GARDEN = clean(_inner_left.intersection(box(708.0, -10, 900, 400)))
_inner_left = _inner_left.difference(EAST_GARDEN)
# green fingers: the bands of the clusters
_band = unary_union([FS.rect(-50, 900, IN0 - 1, IN0 + CL_DEPTH), FN.rect(-50, 1000, IN0 - 1, IN0 + CL_DEPTH)])
FINGERS = [p for p in polys(_inner_left.intersection(_band)) if p.area > 60]
_core = _inner_left.difference(_band)
CENTRAL_PARK = max(polys(_core.intersection(box(140, -10, 372, 400))), key=lambda p: p.area)
LINKS = [p for p in polys(_core.difference(CENTRAL_PARK)) if p.area > 60]
POCKETS = [p for p in polys(OUTER_BELT.difference(_taken)) if p.area > 30]

LAKE_C = (CENTRAL_PARK.centroid.x, CENTRAL_PARK.centroid.y)
_lake = Point(LAKE_C).buffer(1.0)
from shapely import affinity  # noqa: E402
LAKE = affinity.scale(_lake, 34.0, 13.0).intersection(CENTRAL_PARK.buffer(-12))
_ec = EAST_GARDEN.centroid
SH_LAKE = affinity.scale(Point(_ec.x + 6, _ec.y).buffer(1.0), 22.0, 15.0).intersection(EAST_GARDEN.buffer(-10))
CASCADES = [box(_ec.x - 30 - 5 * i, _ec.y - 4 - 1.5 * i, _ec.x - 26 - 5 * i, _ec.y + 4 + 1.5 * i).intersection(
    EAST_GARDEN.buffer(-6)) for i in range(4)]
WATER = [LAKE, SH_LAKE] + CASCADES

# --- plaza landscape (towers) ---------------------------------------------------------------------------
APRONS = unary_union([t.buffer(4.0, join_style="mitre") for t in TOWERS]).intersection(PLAZA.buffer(-0.5))
_gaps = []
for a, b in zip(TOWERS, TOWERS[1:]):
    ca, cb = np.array(a.centroid.coords[0]), np.array(b.centroid.coords[0])
    m = (ca + cb) / 2
    _gaps.append(Point(m).buffer(6.0))
FOUNTAINS = [Point(g.centroid).buffer(3.4) for g in _gaps]
FOUNTAIN_COURTS = [g.intersection(PLAZA) for g in _gaps]
_px0, _py0, _px1, _py1 = PLAZA.bounds
PROMENADE = PLAZA.intersection(box(_px0, _py0, _px1, _py0 + 7.0))
DROPOFF = PLAZA.intersection(Point((_px0 + 6, (_py0 + _py1) / 2 + 10)).buffer(14.0))
PAVING = unary_union([APRONS, PROMENADE, DROPOFF] + FOUNTAIN_COURTS).intersection(PLAZA)
LAWN = PLAZA.buffer(-1.0).difference(PAVING.buffer(0.8))
PLAZA_TREES = []
for _pp in polys(PLAZA_ZONE.buffer(-3.5)):
    _ring = _pp.exterior
    for d in np.arange(0, _ring.length, 9.0):
        q = _ring.interpolate(d)
        if not PAVING.buffer(1.5).contains(q) and not unary_union(TOWERS).buffer(5).contains(q):
            PLAZA_TREES.append((q.x, q.y))
PALMS = [(u, _py0 + 3.5) for u in np.arange(_px0 + 8, _px1 - 6, 7.0) if PLAZA.buffer(-1).contains(Point(u, _py0 + 3.5))]

# --- numbers ------------------------------------------------------------------------------------------
FLOORS, FLATS_PER_FLOOR = 20, 4
N_APTS = len(TOWERS) * FLOORS * FLATS_PER_FLOOR
PARK_NEED = math.ceil(N_APTS * 1.5)


def total(gs):
    return sum(g.area for g in gs)


GARDENS = [OPEN[k] for k in OPEN if k.startswith("G_")]
PARKS = [CENTRAL_PARK, WEST_PARK, EAST_GARDEN] + LINKS + GARDENS
GREEN = PARKS + FINGERS + POCKETS + [UT_GREEN, RB_ISLAND, MEDIAN]
LANDUSE = [
    (f"Villas 400 m2 ({len(VILLAS)}) - فلل 400 م2", total(VILLAS)),
    (f"Houses 240 m2 ({len(HOUSES)}) - دور 240 م2", total(HOUSES)),
    (f"Towers ({len(TOWERS)}) + plaza - الأبراج والبلازا", total(TOWERS) + PLAZA.area),
    ("Community services - الخدمات", total(SERV[k] for k in SERV if k not in UTILITIES)),
    ("Utilities - المرافق الفنية", total(SERV[k] for k in UTILITIES)),
    ("Parks, gardens, green fingers - الحدائق والأصابع الخضراء", total(GREEN)),
    ("Parking (mall) - موقف المول", OPEN["PARK_MALL"].area),
    ("Roads - الشوارع", ROADS.area),
]

if __name__ == "__main__":
    print("villas", len(VILLAS), "north", len(_north), "south", len(_south), "houses", len(HOUSES))
    print("site", round(SITE.area))
    s = 0
    for n, a in LANDUSE:
        s += a
        print(f"{n:<60s}{a:>10,.0f} {a / SITE.area * 100:5.1f}")
    print("sum", round(s))
    for k, g in SERV.items():
        print(k, round(g.area), g.geom_type)
    print("inner overlap check", round(unary_union(HOUSES).difference(INNER).area, 1),
          round(unary_union(VILLAS).intersection(R_OUT).area, 1), round(unary_union(TOWERS).difference(PLAZA_ZONE).area, 1))
