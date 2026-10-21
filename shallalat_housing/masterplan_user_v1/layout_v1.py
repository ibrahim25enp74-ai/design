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

# --- clusters' positions: the green fingers between them ----------------------------------------------
# Rev 1: fingers 10 m wide (pitch 58); every finger lines up with a pocket garden in the villa row and a
# zebra crossing on the ring, so each villa group walks straight through a finger to the central park.
CL_PITCH = 58.0
CL_W_START, CL_E_START = 150.0, 532.0
_u_mid = [CL_W_START + CL_PITCH / 2 + CL_PITCH * k for k in range(4)]
_u_east = [CL_E_START + CL_PITCH / 2 + CL_PITCH * k for k in range(3)]
FINGER_U_S = [CL_W_START + CL_PITCH * k for k in range(5)] + [CL_E_START + CL_PITCH * k for k in range(4)]
FINGER_U_N = [CL_W_START + CL_PITCH * k for k in range(5)]
FINGER_T_N = [FN.t_of((u, north_v(u))) for u in FINGER_U_N]

# --- villas: one row outside the ring, groups with pocket gardens between ------------------------------
VW, GROUP, POCKET = 16.0, 6, 10.0
VILLA_TARGET = 80
NO_VILLA = unary_union([AXIS_N.buffer(4), SG_ROAD.buffer(4), box(SGATE_U - 6, -5, 900, 60)])


def villa_row(frame, t0, t1, pockets):
    """Villas along an edge; a pocket garden at every finger and after at most GROUP + 1 villas."""
    out, t, k = [], t0, 0
    while t + VW <= t1:
        r = frame.rect(t, t + VW, 0.0, BELT)
        hit = [c for c in pockets if t < c + POCKET / 2 and t + VW > c - POCKET / 2]
        if hit:
            t, k = hit[0] + POCKET / 2, 0
            continue
        if r.difference(OUTER_BELT).area < 0.5 and not r.intersects(NO_VILLA):
            out.append(r)
            k += 1
            t += VW
            nxt = [c for c in pockets if c > t]
            if k >= GROUP and not (nxt and nxt[0] - POCKET / 2 - t < VW * 1.5):
                t, k = t + POCKET, 0
        else:
            t, k = t + 1.0, 0
    return out


_north = villa_row(FN, 30.0, FN.length - 20.0, FINGER_T_N)
_south = villa_row(FS, 30.0, FS.length, FINGER_U_S)
VILLAS = (_north + _south)[:VILLA_TARGET]
POCKET_T = {"N": FINGER_T_N, "S": FINGER_U_S}

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


CL_SOUTH_T = _u_mid + _u_east
CL_NORTH_T = [FN.t_of((u, north_v(u))) for u in _u_mid]
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
PLAZA_ZONE = INNER.intersection(box(530.0, IN0 + CL_DEPTH + 6.0, 676.0, 400))
PLAZA = clean(PLAZA_ZONE).difference(unary_union(TOWERS))

# --- services ---------------------------------------------------------------------------------------
SERV, OPEN = {}, {}
_strip = INNER.difference(INNER.buffer(-3.5, join_style="mitre"))


def layby(zone, length=40.0):
    """Rev 1: a 3.5 m drop-off bay along the ring in front of a school / kindergarten."""
    c = zone.centroid
    bay = clean(_strip.intersection(zone).intersection(box(c.x - length / 2, -10, c.x + length / 2, 400)))
    return bay, clean(zone.difference(bay.buffer(0.01)))


LAYBYS = []
_civ_free = INNER.difference(ROUNDABOUT.buffer(3)).difference(AXIS_N.buffer(3)).difference(AXIS_S.buffer(3))
_civ_free = _civ_free.difference(CLUSTERS.buffer(5.0)).difference(PLAZA_ZONE.buffer(4.0))
# civic core round the roundabout: daily services, each in its garden
_nw = clean(_civ_free.intersection(box(370, RB_C[1], GATE_U, 400)))
SERV["MALL"], r = cut(_nw, 3000, "v", "max")
OPEN["PARK_MALL"], r = cut(r, 1200, "u", "min")
OPEN["G_MALL"] = r
_ne = clean(_civ_free.intersection(box(GATE_U, RB_C[1], 540, 400)))
SERV["MOSQUE"], r = cut(_ne, 2000, "v", "max")
OPEN["G_MOSQUE"] = r                          # mosque forecourt garden on the roundabout
_sw = clean(_civ_free.intersection(box(370, -10, GATE_U, RB_C[1])))
bay, _sw = layby(_sw, 50.0)
LAYBYS.append(bay)
SERV["PRIMARY"], r = cut(_sw, 3000, "v", "min")
OPEN["G_PRIM"] = r
_se = clean(_civ_free.intersection(box(GATE_U, -10, 540, RB_C[1])))
SERV["HEALTH"], _ = cut(clean(_se.intersection(box(-1e3, -10, 1e3, IN0 + 36))), 1000, "u", "max")
OPEN["G_HEALTH"] = clean(_se.difference(SERV["HEALTH"].buffer(0.01)))
# west end: secondary school + west park; Rev 1: kindergarten split in two (750 + 750) so that every
# home is within about 300 m of one: west KG on the ring by the west clusters ...
_west = clean(INNER.intersection(box(-100, -10, 150.0 - 6.0, 400)).difference(CLUSTERS.buffer(6.0)))
_kgw = clean(_west.intersection(box(100, -10, 150, IN0 + 34)))
bay, _kgw = layby(_kgw, 22.0)
LAYBYS.append(bay)
SERV["KG_W"], _ = cut(_kgw, 750, "u", "max")
_west = clean(_west.difference(SERV["KG_W"].buffer(4.0)).difference(bay.buffer(0.5)))
_c = _west.centroid
bay = clean(_strip.intersection(_west).intersection(box(_c.x - 25, 150, _c.x + 25, 400)))
LAYBYS.append(bay)
_west = clean(_west.difference(bay.buffer(0.01)))
SERV["SECONDARY"], r = cut(_west, 5000, "v", "max")
# Rev 2 (architect): the club is dropped from the programme; its land joins the sports park
WEST_PARK = r
# ... and east KG at the end of the towers' plaza, for the towers' families and the east clusters
_kge = clean(INNER.intersection(box(676.0, IN0 + CL_DEPTH + 6.0, 708.0, 400)))
SERV["KG_E"], _ = cut(_kge, 750, "v", "max")
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
ROADS = ROADS.difference(unary_union(LAYBYS))
ROADS = ROADS.difference(RB_ISLAND).difference(MEDIAN)

# --- green: everything left inside and outside the ring ------------------------------------------------
_taken = unary_union(VILLAS + HOUSES + TOWERS + [PLAZA, ROADS, RB_ISLAND, MEDIAN, CLUSTERS] + list(SERV.values())
                     + list(OPEN.values()) + [WEST_PARK, UT_GREEN] + LAYBYS)
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


def walk_max(keys):
    """Longest straight walk from any home (villa, house, tower) to the nearest of these services."""
    homes = [p.centroid for p in VILLAS + HOUSES + TOWERS]
    return max(min(h.distance(SERV[k]) for k in keys) for h in homes)
LANDUSE = [
    (f"Villas 400 m2 ({len(VILLAS)}) - فلل 400 م2", total(VILLAS)),
    (f"Houses 240 m2 ({len(HOUSES)}) - دور 240 م2", total(HOUSES)),
    (f"Towers ({len(TOWERS)}) + plaza - الأبراج والبلازا", total(TOWERS) + PLAZA.area),
    ("Community services - الخدمات", total(SERV[k] for k in SERV if k not in UTILITIES)),
    ("Utilities - المرافق الفنية", total(SERV[k] for k in UTILITIES)),
    ("Parks, gardens, green fingers - الحدائق والأصابع الخضراء", total(GREEN)),
    ("Parking: mall + school drop-off bays - مواقف المول وأماكن إنزال الطلاب", OPEN["PARK_MALL"].area + total(LAYBYS)),
    ("Roads - الشوارع", ROADS.area),
]

# --- circulation (Rev 1) -------------------------------------------------------------------------------
# Vehicles: the ring (two-way, 8 m) and the gate axis carry all traffic; the cul-de-sacs serve 8 houses
# each; tower cars turn off the ring straight into two basement ramps between the towers; service
# trucks use the south gate and the ring's south-east arc only, where there are no homes.
# Pedestrians: a 6 m promenade (the green spine) runs west-east through the parks; every green finger
# lines up with a villa pocket garden and a raised zebra crossing on the ring; the ring's walks are
# lined with trees on both sides - a 1.9 km shaded loop (the "green ring").
RING_CL = R_OUT.buffer(-RING_W / 2).exterior
_nv = north_v(GATE_U)
AXIS_CL = LineString([(GATE_U, _nv), (GATE_U, IN0 - RING_W / 2)])
LANE_CL = [LineString([fr.p(tc, IN0 - RING_W / 2), fr.p(tc, IN0 + PER_SIDE * HW + HEAD / 2)])
           for fr, ts in ((FS, CL_SOUTH_T), (FN, CL_NORTH_T)) for tc in ts]
CROSSINGS = [FS.rect(u - 2.0, u + 2.0, BELT, IN0) for u in FINGER_U_S] + \
            [FN.rect(t - 2.0, t + 2.0, BELT, IN0) for t in FINGER_T_N]
SPINE_V = 101.0
CROSSINGS.append(box(GATE_U - 6, SPINE_V - 2, GATE_U + 6, SPINE_V + 2))
SPINE = LineString([(30, 140), (144, 140), (172, 128), (205, 108), (290, 106), (345, 108), (370, SPINE_V),
                    (528, SPINE_V), (548, 107), (676, 107), (712, 98), (735, 64), (770, 52), (805, 70), (812, 95),
                    (790, 116), (750, 118), (712, 98)])
FINGER_WALKS = [LineString([FS.p(u, BELT / 2), FS.p(u, IN0 + CL_DEPTH + 3)]) for u in FINGER_U_S] + \
               [LineString([FN.p(t, BELT / 2), FN.p(t, IN0 + CL_DEPTH + 3)]) for t in FINGER_T_N]
_walkable = unary_union(PARKS + FINGERS + POCKETS + [PLAZA] + CROSSINGS).buffer(0.3)
SPINE_PATH = unary_union([SPINE.buffer(3.0)] + [w.buffer(1.5) for w in FINGER_WALKS]).intersection(_walkable)
SPINE_PATH = SPINE_PATH.difference(unary_union(WATER).buffer(1.0)).difference(unary_union(TOWERS).buffer(1.0))
# ring-road trees, both sides, every 10 m
_no_tree = unary_union(LANES + CROSSINGS + LAYBYS + [AXIS_N, AXIS_S, SG_ROAD, ROUNDABOUT]).buffer(4.0)
RING_TREES = []
for edge in (R_OUT.buffer(-1.6).exterior, INNER.buffer(1.6).exterior):
    for d in np.arange(0, edge.length, 10.0):
        q = edge.interpolate(d)
        if not _no_tree.contains(q):
            RING_TREES.append((q.x, q.y))
# basement ramps between the towers, straight off the ring
RAMPS = []
for a_, b_ in zip(TOWERS, TOWERS[1:]):
    tm = (FN.t_of(a_.centroid.coords[0]) + FN.t_of(b_.centroid.coords[0])) / 2
    RAMPS.append(FN.rect(tm - 3.5, tm + 3.5, IN0, IN0 + 12.0))
GATEHOUSE = box(GATE_U - 1.5, _nv - 15, GATE_U + 1.5, _nv - 8)
# routes for the circulation diagram
_tg = FN.t_of((GATE_U, _nv))
_ring_n = lambda t0, t1: [FN.p(t, BELT + RING_W / 2) for t in np.linspace(t0, t1, 12)]  # noqa: E731
_ramp_t = [FN.t_of(r.centroid.coords[0]) for r in RAMPS]
TOWER_ROUTE = LineString([(GATE_U, _nv)] + _ring_n(_tg, _ramp_t[-1]) + [RAMPS[-1].centroid.coords[0]])
MALL_ROUTE = LineString([(GATE_U, _nv)] + _ring_n(_tg, FN.t_of(SERV["MALL"].centroid.coords[0]))
                        + [SERV["MALL"].centroid.coords[0]])
SERVICE_ROUTE = LineString([(SGATE_U, 0), (SGATE_U, BELT + RING_W / 2), (812, BELT + RING_W / 2),
                            SERV["WASTE"].centroid.coords[0]])

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
