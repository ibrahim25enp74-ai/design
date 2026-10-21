"""Master plan, proposal E rev 2 "Shallalat garden" (حديقة الشلالات) for plot 157 / district 53 Baybokht.

Redrawn from the client's concept render: the two towers stand at the wide NW end around a drop-off
plaza and fountain, a long central garden with cascades and a lake runs down the middle, detached
villas line the south side and attached houses the north side, a service centre (mosque, schools,
health, police, civil defence, market) fills the middle of the plot, and a second villa / house
quarter with its own park sits at the narrow SE end.

Changes from the render, at the client's request: no parking outside the NW end and no water channel
at the SE end. The plot does not front a street at either short end, so every entrance comes from the
two long-side roads (and the public cross road): a 24 m boulevard and a 16 m street cross the plot
between the long-side roads and carry the gates. The watercourse on the cadastral scan is ignored.

Geometry is laid out in a local frame (u along the south edge Q1->Q4, v across, towards the north
edge) and written to the DXF in UTM 38S, on the same net boundary as SHALLALAT_SITE_PLAN.dxf.

Rev 2 applies the client's revised program: 80 villas 400 m2, 88 houses 240 m2 (12 x 20), three towers
of 20 floors (240 flats) on a plaza over a 360-car basement, services at their new sizes (no club),
and all leftover land to gardens.
"""
import math
import os

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "NotoSansArabic-Regular.ttf")

# --- site (same numbers as site/make_site_dxf.py) ----------------------------------------------------
P = [(338954.0, 4035462.0), (339032.0, 4035771.0), (339836.0, 4035336.0), (339747.0, 4035198.0)]
Q = [(338955.19, 4035466.71), (339030.78, 4035766.16), (339833.37, 4035331.92), (339749.71, 4035202.20)]
PIX = np.array([(259.3, 156), (468.3, 119.3), (395, 731.7), (290, 712.3)])
AFF = np.linalg.lstsq(np.c_[PIX, np.ones(4)], np.array(P), rcond=None)[0]

O = np.array(Q[0])
U = np.subtract(Q[3], Q[0]) / np.linalg.norm(np.subtract(Q[3], Q[0]))
V = np.array([-U[1], U[0]])
ROT = math.degrees(math.atan2(U[1], U[0]))


def loc(p):
    d = np.subtract(p, O)
    return float(d @ U), float(d @ V)


def utm(p):
    return tuple(O + p[0] * U + p[1] * V)


def scan(x, y):
    return loc(tuple(np.array([x, y, 1.0]) @ AFF))


SITE = Polygon([loc(q) for q in Q])
SITE_RAW = Polygon([loc(p) for p in P])
NW, NE = loc(Q[1]), loc(Q[2])
SE = loc(Q[3])

# north-edge frame: t along Q2->Q3, d measured inwards from the north edge
DN = np.subtract(NE, NW) / math.dist(NW, NE)
NI = np.array([DN[1], -DN[0]])  # inward normal (points south, into the plot)


def npt(t, d):
    return tuple(np.add(NW, DN * t + NI * d))


def nstrip(t0, t1, d0, d1):
    return Polygon([npt(t0, d0), npt(t1, d0), npt(t1, d1), npt(t0, d1)])


def t_of(u):
    """t on the north edge of the point whose u is given (north edge parametrised by t)."""
    return (u - NW[0]) / DN[0]


def north_v(u):
    return NW[1] + (u - NW[0]) * (NE[1] - NW[1]) / (NE[0] - NW[0])


def band(a, b, half, ext=0.0):
    ln = LineString([a, b])
    if ext:
        d = np.subtract(b, a) / ln.length
        ln = LineString([tuple(np.subtract(a, d * ext)), tuple(np.add(b, d * ext))])
    return ln.buffer(half, cap_style="flat")


def across(u0, u1):
    """Full-width slice of the plot between two chainages (perpendicular to the south edge)."""
    return SITE.intersection(box(u0, -50, u1, 500))


# --- public cross road (from the cadastral scan) -----------------------------------------------------
CROSS_A, CROSS_B = scan(267, 251), scan(455, 214)
CROSS = band(CROSS_A, CROSS_B, 5.0, ext=40).intersection(SITE_RAW)
CROSS_IN = CROSS.intersection(SITE)
cross_dir = np.subtract(CROSS_B, CROSS_A) / math.dist(CROSS_A, CROSS_B)
cross_n = np.array([cross_dir[1], -cross_dir[0]])
if cross_n[0] < 0:
    cross_n = -cross_n  # points ESE, away from the NW end


def past_cross(off):
    a = np.add(CROSS_A, cross_n * off)
    big = 3000
    pts = [a - cross_dir * big, a + cross_dir * big, a + cross_dir * big + cross_n * big, a - cross_dir * big + cross_n * big]
    return Polygon([tuple(p) for p in pts])


def cross_strip(o0, o1):
    return SITE.intersection(past_cross(o0)).difference(past_cross(o1))


# --- program (rev 2) ----------------------------------------------------------------------------------
N_VILLAS, N_HOUSES = 80, 88
N_TOWERS, FLOORS, FLATS_PER_FLOOR = 3, 20, 4
N_APTS = N_TOWERS * FLOORS * FLATS_PER_FLOOR
BASEMENT_CARS = 360
SV_AREAS = {"MALL": 3000, "MOSQUE": 2000, "HEALTH": 1000, "POLICE": 600, "CIVIL_DEF": 600,
            "KG": 1500, "PRIMARY": 3000}
SEC_SCHOOL_M2 = 5000
UTIL_AREAS = {"WATER": 1000, "POWER": 1000, "WASTE": 300}

# --- chainages of the main bands --------------------------------------------------------------------
BLV_U = (438.0, 462.0)    # 24 m boulevard from the main gate on the north road, closed at the south wall


def solve(f, target, lo, hi, n=60):
    """x in [lo, hi] with f(x) = target, f increasing."""
    for _ in range(n):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < target else (lo, mid)
    return (lo + hi) / 2


# service parcels between the boulevard and the 16 m street; the street sits right after them
_SV_BAND = across(BLV_U[1], 900.0).buffer(-3, join_style="mitre")
SV_ST = 12.0
SV_V1 = (66.0, 66.0 + SV_ST)      # service street along u, south
SV_V2 = (146.0, 146.0 + SV_ST)    # service street along u, north
U0 = BLV_U[1] + 4
_COLS = {  # column -> v range, parcels in order from the boulevard
    "S": ((0.0, SV_V1[0] - 3), ["PRIMARY", "KG"]),
    "C": ((SV_V1[1] + 3, SV_V2[0] - 3), ["MOSQUE", "HEALTH"]),
    "N": ((SV_V2[1] + 3, 400.0), ["MALL", "POLICE", "CIVIL_DEF"]),
}
SV = {}
_col_end = []
for (v0, v1), keys in _COLS.values():
    u = U0
    for k in keys:
        f = lambda x, u=u: _SV_BAND.intersection(box(u, v0, x, v1)).area
        x = solve(f, SV_AREAS[k], u, u + 300)
        SV[k] = _SV_BAND.intersection(box(u, v0, x, v1))
        u = x + 6
    _col_end.append(u)
ST2_U = (math.ceil(max(_col_end)) + 4.0, math.ceil(max(_col_end)) + 20.0)   # 16 m internal street

TOWER_ZONE = SITE.difference(past_cross(-5.0))           # NW end, before the cross road
CENTRAL = SITE.intersection(past_cross(5.0)).intersection(box(-100, -50, BLV_U[0], 500))
SERVICES = across(BLV_U[1], ST2_U[0])
SE_Q = across(ST2_U[1], 2000)
BOULEVARD = across(*BLV_U).intersection(box(-100, 20.0, 2000, 500))
STREET2 = across(*ST2_U).intersection(box(-100, 20.0, 2000, 500)).difference(nstrip(-50, 1200, -50, 16.0))

ROAD = 12.0
VD, VF = 25.0, 16.0       # villa plot depth x frontage = 400 m2
HD, HF = 20.0, 12.0       # house plot depth x frontage = 240 m2

# --- central quarter: villas on the south side, attached houses on the north side ------------------
# south side, from the wall: villa row | road S1 | villa double row | road S2 (garden edge)
S1 = (VD, VD + ROAD)
S2 = (S1[1] + 2 * VD, S1[1] + 2 * VD + ROAD)
# north side, from the wall: house row | road N1 | house double row | road N2 (garden edge)
N1 = (HD, HD + ROAD)
N2 = (N1[1] + 2 * HD, N1[1] + 2 * HD + ROAD)
TOP_RD = cross_strip(9.0, 9.0 + ROAD)                    # internal road along the cross road
TOP_BELT = cross_strip(5.0, 9.0)
MID_U = 300.0                                             # cross lanes through the double rows


def s_road(v0, v1, u0, u1):
    return box(u0, v0, u1, v1)


C_ROADS = [
    TOP_RD,
    s_road(*S1, 0, BLV_U[0]), s_road(*S2, 0, BLV_U[0]),
    nstrip(-50, 1200, *N1), nstrip(-50, 1200, *N2),
    box(MID_U - ROAD / 2, S1[1] - 1, MID_U + ROAD / 2, S2[0] + 1),
    nstrip(t_of(MID_U) - ROAD / 2, t_of(MID_U) + ROAD / 2, N1[1] - 1, N2[0] + 1),
]
C_ROADS = unary_union(C_ROADS).intersection(CENTRAL)
C_FREE = CENTRAL.intersection(past_cross(9.0 + ROAD)).difference(C_ROADS.buffer(0.01))

# garden between S2 and N2
GARDEN = CENTRAL.intersection(past_cross(9.0 + ROAD)).intersection(box(-100, S2[1], BLV_U[0], 500)).difference(
    nstrip(-50, 1200, -50, N2[1]))
GARDEN = max(getattr(GARDEN, "geoms", [GARDEN]), key=lambda g: g.area)


def rows_south(region, rows, u0, u1, kind):
    depth, w = (VD, VF) if kind == "V" else (HD, HF)
    out = []
    for v0 in rows:
        u = u0
        while u + w <= u1:
            p = box(u, v0, u + w, v0 + depth)
            if region.contains(p.buffer(-0.05)):
                out.append(p)
                u += w
            else:
                u += 1.0
    return out


def rows_north(region, rows, t0, t1, kind):
    depth, w = (VD, VF) if kind == "V" else (HD, HF)
    out = []
    for d0 in rows:
        t = t0
        while t + w <= t1:
            p = nstrip(t, t + w, d0, d0 + depth)
            if region.contains(p.buffer(-0.05)):
                out.append(p)
                t += w
            else:
                t += 1.0
    return out


REG_S = C_FREE.intersection(box(-100, 0, 2000, S2[0]))
REG_N = C_FREE.difference(nstrip(-50, 1200, N2[1], 600))
_CV = rows_south(REG_S, [0.0, S1[1], S1[1] + VD], 0, BLV_U[0], "V")
_CH = rows_north(REG_N, [0.0, N1[1], N1[1] + HD], 0, t_of(BLV_U[0]) + 5, "H")

# --- SE quarter: villa rows on the south side, house rows on the north side, park between ------------
SE_S = (VD, VD + ROAD)
SE_N = (HD, HD + ROAD)
SE_TIP = SE_Q.buffer(-3, join_style="mitre")
# loop road across the quarter; the utilities fill the narrow tip beyond it
SE_END_U = solve(lambda x: -SE_TIP.intersection(box(x + ROAD + 3, -50, 2000, 500)).area,
                 -(sum(UTIL_AREAS.values()) + 900), ST2_U[1] + 50, 870)
SE_LOOP = box(SE_END_U, 0, SE_END_U + ROAD, 500)
SE_ROADS = unary_union([box(ST2_U[1] - 1, SE_S[0], SE_END_U + ROAD, SE_S[1]),
                        nstrip(t_of(ST2_U[1]) - 3, t_of(SE_END_U + ROAD) + 3, *SE_N), SE_LOOP]).intersection(SE_Q)
_se_core = SE_Q.intersection(box(-100, -50, SE_END_U, 500))
SE_FREE = _se_core.difference(SE_ROADS.buffer(0.01))
_SV_ = rows_south(SE_FREE.intersection(box(-100, 0, 2000, SE_S[1] + VD)), [0.0, SE_S[1]], ST2_U[1], SE_END_U, "V")
_SH = rows_north(SE_FREE.difference(nstrip(-50, 1200, SE_N[1] + HD, 600)), [0.0, SE_N[1]],
                 t_of(ST2_U[1]) - 2, t_of(SE_END_U) + 2, "H")
# the program is fixed: keep the plots nearest the gate / services, the rest becomes garden
VILLAS = (_CV + _SV_)[:N_VILLAS]
HOUSES = (_CH + _SH)[:N_HOUSES]
C_VILLAS = [p for p in VILLAS if p.centroid.x < BLV_U[0]]
SE_VILLAS = [p for p in VILLAS if p.centroid.x > BLV_U[0]]
C_HOUSES = [p for p in HOUSES if p.centroid.x < BLV_U[0]]
SE_HOUSES = [p for p in HOUSES if p.centroid.x > BLV_U[0]]
SE_PARK = _se_core.intersection(box(-100, SE_S[1] + VD, 2000, 500)).difference(nstrip(-50, 1200, -50, SE_N[1] + HD))
SE_PARK = max(getattr(SE_PARK, "geoms", [SE_PARK]), key=lambda g: g.area)
UTIL = SE_Q.intersection(box(SE_END_U + ROAD, -50, 2000, 500))
CAP = dict(villas=len(_CV + _SV_), houses=len(_CH + _SH))

# --- tower zone (NW end): three towers on a plaza over the basement, secondary school -----------------
def cross_pt(v, off):
    """Point at offset `off` from the cross-road axis (negative = NW side) whose v is given."""
    base = np.add(CROSS_A, cross_n * off)
    s_ = (v - base[1]) / cross_dir[1]
    return tuple(np.add(base, cross_dir * s_))


TZ_IN = TOWER_ZONE.buffer(-3, join_style="mitre")
T_ACCESS = TOWER_ZONE.intersection(past_cross(-19.0)).difference(past_cross(-7.0)).intersection(box(-100, -1, 500, 262))
_acc_in = TZ_IN.difference(past_cross(-22.0))
SEC_TOP = solve(lambda x: _acc_in.intersection(box(-100, 0, 500, x)).area, SEC_SCHOOL_M2, 10, 150)
SEC_SCHOOL = _acc_in.intersection(box(-100, 0, 500, SEC_TOP))
SEC_PITCH = box(10, 8, 60, 34)
PLAZA = _acc_in.intersection(box(-100, SEC_TOP + 10, 500, 500)).difference(nstrip(-50, 1200, -50, 12.0))
PLAZA = PLAZA.buffer(-1, join_style="mitre")
_pb = PLAZA.bounds
T_MID_V = (SEC_TOP + 10 + north_v(60) - 12) / 2
TW = 31.5  # 992 m2 floor plate, 4 flats per floor
T_CEN = [(40.0, T_MID_V - 66.0), (66.0, T_MID_V), (40.0, T_MID_V + 66.0)]
TOWERS = [box(c[0] - TW / 2, c[1] - TW / 2, c[0] + TW / 2, c[1] + TW / 2) for c in T_CEN]
TOWER_GAP = min(a.distance(b) for i, a in enumerate(TOWERS) for b in TOWERS[i + 1:])
BASEMENT = box(14, T_MID_V - 85, 92, T_MID_V + 85).intersection(PLAZA)
_rp = cross_pt(T_MID_V - 90, -22.0)
T_RAMP = box(_rp[0] - 30, T_MID_V - 96, _rp[0] - 2, T_MID_V - 89)
T_DROP = PLAZA.intersection(past_cross(-29.0)).intersection(box(-100, T_MID_V - 45, 500, T_MID_V + 45))
T_ROADS = unary_union([T_ACCESS, T_DROP])
T_FOUNTAINS = [box(c[0] - 9, c[1] - 9, c[0] + 9, c[1] + 9) for c in ((40.0, T_MID_V - 33), (40.0, T_MID_V + 33))]
T_CHANNEL = box(14, T_MID_V - 3, 48, T_MID_V + 3)
T_PLAZA_GREEN = TZ_IN.difference(unary_union([SEC_SCHOOL, PLAZA, T_ACCESS]).buffer(2))
T_PLAZA_GREEN = unary_union([g for g in getattr(T_PLAZA_GREEN, "geoms", [T_PLAZA_GREEN]) if g.area > 100])

# --- central garden: cascades, lake, paths, amphitheatre ----------------------------------------------
def garden_axis(n=40):
    gb = GARDEN.bounds
    pts = []
    for i in range(n + 1):
        u = gb[0] + 8 + (gb[2] - gb[0] - 26) * i / n
        cut = GARDEN.intersection(LineString([(u, -50), (u, 500)]))
        if cut.is_empty:
            continue
        lo, hi = cut.bounds[1], cut.bounds[3]
        mid = (lo + hi) / 2 + 0.28 * (hi - lo) * math.sin(i / n * 3.2 * math.pi)
        pts.append((u, mid, hi - lo))
    return pts


AX = garden_axis()
_lake_parts = []
for i, (u, v, w) in enumerate(AX):
    r = max(4.0, min(w * 0.22, 15.0)) * (0.75 + 0.35 * abs(math.sin(i * 0.9)))
    _lake_parts.append(Point(u, v).buffer(r))
WATER = unary_union(_lake_parts).buffer(3).buffer(-3).intersection(GARDEN.buffer(-10))
CASCADES = [box(AX[k][0] - 3, AX[k][1] - 9, AX[k][0] + 3, AX[k][1] + 9) for k in (6, 14, 22, 30)]
PATH = LineString([(u, v + (w * 0.33 if i % 2 else -w * 0.33)) for i, (u, v, w) in enumerate(AX[::4])]).buffer(1.6)
PATH = PATH.union(LineString([(u, v) for u, v, _ in AX]).parallel_offset(0, "left").buffer(0) if False else PATH)
PATHS = PATH.intersection(GARDEN.buffer(-2)).difference(WATER.buffer(1))
BRIDGES = [band((AX[k][0], AX[k][1] - 22), (AX[k][0], AX[k][1] + 22), 1.8).intersection(GARDEN.buffer(-2))
           for k in (10, 26, 36)]
_amp_c = (AX[18][0], AX[18][1])
AMPHI = Point(_amp_c).buffer(16).difference(Point(_amp_c).buffer(6)).intersection(box(_amp_c[0] - 20, _amp_c[1], _amp_c[0] + 20, _amp_c[1] + 20))
AMPHI = AMPHI.difference(WATER.buffer(2))
CAFE = box(GARDEN.bounds[2] - 30, AX[-1][1] - 9, GARDEN.bounds[2] - 16, AX[-1][1] + 9).intersection(GARDEN.buffer(-3))

# --- service centre (parcels sized above), leftover land between them is garden ------------------------
SV_IN = SERVICES.buffer(-3, join_style="mitre")
SV_ROADS = unary_union([box(BLV_U[1] - 1, SV_V1[0], ST2_U[0] + 1, SV_V1[1]),
                        box(BLV_U[1] - 1, SV_V2[0], ST2_U[0] + 1, SV_V2[1])]).intersection(SERVICES)
SV_GREEN = SV_IN.difference(unary_union(list(SV.values()) + [SV_ROADS]).buffer(3))
MOSQUE_FP = Point(SV["MOSQUE"].centroid).buffer(15, quad_segs=2)  # indicative square prayer hall
SPORT = SEC_PITCH                                                  # school pitch

_ub = UTIL.buffer(-3, join_style="mitre")
UTIL_ITEMS = {}
_v = _ub.bounds[1]
for k in ("POWER", "WATER", "WASTE"):
    f = lambda x, v=_v: _ub.intersection(box(-100, v, 2000, x)).area
    x = solve(f, UTIL_AREAS[k], _v, 400)
    UTIL_ITEMS[k] = _ub.intersection(box(-100, _v, 2000, x))
    _v = x + 4
UTIL_GREEN = _ub.difference(unary_union(list(UTIL_ITEMS.values())).buffer(2))

# --- gates -------------------------------------------------------------------------------------------
# only two entrances, both from the long-side roads (the short ends do not front a street)
MG_T = t_of((BLV_U[0] + BLV_U[1]) / 2) + 6
MAIN_GATE = LineString([npt(MG_T - 16, 14.0), npt(MG_T + 16, 14.0)])          # main gate on the north road
MAIN_GUARD = nstrip(MG_T + 13, MG_T + 19, 4.0, 12.0)
T_GATE = LineString([cross_pt(8.0, -19.0), cross_pt(8.0, -7.0)])                # tower gate on the south road
T_GATE_U = T_GATE.centroid.x
_gp = cross_pt(4.0, -25.0)
T_GUARD = box(_gp[0] - 3, 2.0, _gp[0] + 3, 10.0)
GATES = {"MAIN": MAIN_GATE, "TOWER": T_GATE}
GUARDS = [MAIN_GUARD, T_GUARD]
ENTRIES = {
    "E_MAIN": (MAIN_GATE.centroid.x, north_v(MAIN_GATE.centroid.x) + 18),
    "E_TOWER": (T_GATE_U, -18.0),
}

# --- trees -----------------------------------------------------------------------------------------
rng = np.random.default_rng(7)


def scatter(region, n, keep_off=None, r=3.5):
    out = []
    b = region.bounds
    tries = 0
    while len(out) < n and tries < n * 60:
        tries += 1
        p = Point(rng.uniform(b[0], b[2]), rng.uniform(b[1], b[3]))
        if not region.buffer(-r).contains(p):
            continue
        if keep_off is not None and keep_off.buffer(r + 1).contains(p):
            continue
        if any(p.distance(q) < 2.4 * r for q in out):
            continue
        out.append(p)
    return out


_garden_keep = unary_union([WATER, PATHS, AMPHI, CAFE] + BRIDGES + CASCADES)
TREES = scatter(GARDEN, 230, _garden_keep) + scatter(SE_PARK, 45)
TREES += scatter(T_PLAZA_GREEN, 60) + scatter(SV_GREEN, 40) + scatter(UTIL_GREEN, 6)
PALMS = scatter(PLAZA, 70, unary_union(TOWERS + T_FOUNTAINS + [T_CHANNEL, T_DROP]), r=3.0)
STREET_TREES = []
for g in (BOULEVARD, STREET2):
    b = g.bounds
    for u in (b[0] + 4, b[2] - 4):
        for v in np.arange(6, 320, 14):
            p = Point(u, v)
            if g.buffer(-1).contains(p):
                STREET_TREES.append(p)
TREES += STREET_TREES

# --- land use --------------------------------------------------------------------------------------
def A(gs):
    return sum(g.area for g in gs)


LANDUSE = [
    ("Villa plots 400 m2 - قطع الفلل", len(VILLAS) * 400.0),
    ("House plots 240 m2 - قطع الدور", len(HOUSES) * 240.0),
    ("Towers + plaza - الأبراج والساحة", PLAZA.area),
    ("Services - الخدمات العامة", A(SV.values()) + SEC_SCHOOL.area),
    ("Utilities - المرافق الفنية", A(UTIL_ITEMS.values())),
    ("Shallalat central garden - حديقة الشلالات", GARDEN.area),
    ("Other gardens + parks - حدائق ومتنزهات أخرى", SE_PARK.area),
    ("Public cross road - الشارع العرضي العام", CROSS_IN.area),
    ("Streets + access roads - الشوارع والمداخل",
     unary_union([BOULEVARD, STREET2, C_ROADS, SE_ROADS, SV_ROADS, T_ROADS]).area),
]
LANDUSE[6] = (LANDUSE[6][0], SITE.area - sum(a for i, (_, a) in enumerate(LANDUSE) if i != 6))
GREEN_M2 = GARDEN.area + LANDUSE[6][1]
ROADS_M2 = LANDUSE[7][1] + LANDUSE[8][1]
POP = len(VILLAS) * 6 + len(HOUSES) * 6 + N_TOWERS * FLOORS * (2 * 4 + 2 * 6)

NAMES = {
    "PRIMARY": ("PRIMARY SCHOOL", "مدرسة ابتدائية"), "INT_SCHOOL": ("INTERMEDIATE + SECONDARY", "مدرسة متوسطة وإعدادية"),
    "MOSQUE": ("MOSQUE", "جامع"), "HEALTH": ("HEALTH CENTRE", "مركز صحي"),
    "MARKET": ("MARKET + RESTAURANTS", "سوق ومطاعم ومقاهي"), "POLICE": ("POLICE", "مركز شرطة"),
    "CIVIL_DEF": ("CIVIL DEFENCE", "دفاع مدني"), "YOUTH": ("SOCIAL + YOUTH CENTRE", "مركز اجتماعي وشبابي"),
    "ADMIN": ("ADMIN + SECURITY", "إدارة المجمع والأمن"),
    "POWER": ("POWER STATION", "محطة كهرباء"), "WATER": ("WATER STATION", "محطة ماء"),
    "WASTE": ("WASTE", "نفايات"), "MALL": ("MALL", "مول"), "KG": ("KINDERGARTEN", "روضة"),
    "SEC_SCHOOL": ("SECONDARY SCHOOL", "مدرسة ثانوية (متوسطة وإعدادية)"),
    "GARDEN": ("SHALLALAT CENTRAL GARDEN", "حديقة الشلالات المركزية"),
    "SE_PARK": ("NEIGHBOURHOOD PARK", "حديقة الحي"),
    "BLV": ("MAIN BOULEVARD 24 m", "الشارع الرئيسي 24 م"),
    "ST2": ("INTERNAL STREET 16 m", "شارع داخلي 16 م"),
    "MGATE": ("MAIN GATE", "البوابة الرئيسية"),
    "CROSS": ("CROSS ROAD (PUBLIC)", "الشارع العرضي"),
    "TOWERS": ("3 TOWERS + PLAZA, BASEMENT 360 CARS", "الأبراج الثلاثة والساحة - سرداب 360 سيارة"),
    "TGATE": ("SECONDARY GATE", "البوابة الثانوية"),
    "VILLAS": ("DETACHED VILLAS", "فلل منفصلة"), "HOUSES": ("ATTACHED HOUSES", "دور متصلة"),
    "AMPHI": ("AMPHITHEATRE", "مسرح مكشوف"), "CAFE": ("GARDEN CAFE", "مقهى الحديقة"),
}
LABELS = {
    "GARDEN": (AX[len(AX) // 2 - 6][0], AX[len(AX) // 2 - 6][1] + 30),
    "SE_PARK": tuple(SE_PARK.representative_point().coords[0]),
    "BLV": ((BLV_U[0] + BLV_U[1]) / 2, 110.0),
    "ST2": ((ST2_U[0] + ST2_U[1]) / 2, 110.0),
    "CROSS": tuple(np.add(CROSS_A, cross_dir * 60)),
    "TOWERS": (95.0, T_MID_V + 60),
    "TGATE": (T_GATE_U - 30, 16.0),
    "MGATE": tuple(npt(MG_T, 26.0)),
    "VILLAS": (230.0, 12.5),
    "HOUSES": tuple(npt(t_of(230), 10)),
}


def table_rows():
    units = len(VILLAS) + len(HOUSES) + N_APTS
    return [
        "PROPOSAL E rev 2 - SHALLALAT GARDEN - المقترح هـ (تعديل 2): حديقة الشلالات",
        "Plot 157 / District 53 Baybokht - NIC 5/2026 - UTM 38S",
        "",
        f"UNITS: {len(VILLAS)} villas 400 m2 + {len(HOUSES)} houses 240 m2 + {N_APTS} flats = {units}",
        f"Population approx. {POP:,}  -  green {GREEN_M2:,.0f} m2 ({GREEN_M2 / SITE.area * 100:.1f} %), roads {ROADS_M2 / SITE.area * 100:.1f} %",
        f"Towers: {N_TOWERS} x 20 floors, 992 m2 plate, clear gap {TOWER_GAP:.1f} m (min 33 m), basement {BASEMENT_CARS} cars",
        "Two entrances only, both from the long-side roads: main gate (north road), tower gate (south road)",
    ]


# --- DXF ------------------------------------------------------------------------------------------
LAYERS = {
    "MP_BOUNDARY": (1, 50), "MP_BOUNDARY_COORDS": (6, 18), "MP_FENCE": (8, 35), "MP_GATES": (1, 50),
    "MP_ROADS": (8, 25), "MP_ROAD_CL": (8, 13), "MP_PARKING": (9, 13),
    "MP_PLOT_VILLA": (30, 18), "MP_PLOT_HOUSE": (40, 18), "MP_FOOTPRINT": (7, 25), "MP_TOWERS": (1, 50),
    "MP_SERVICES": (200, 25), "MP_UTILITIES": (8, 25), "MP_GARDEN": (3, 18), "MP_WATER": (5, 25),
    "MP_PATHS": (33, 13), "MP_TREES": (3, 13), "MP_CONTEXT": (8, 13), "MP_TEXT": (7, 18),
    "MP_TEXT_PLOTNO": (8, 9), "MP_TABLE": (7, 18), "MP_NORTH": (7, 25),
    "MP_HATCH_RES": (31, 0), "MP_HATCH_SERV": (211, 0), "MP_HATCH_GREEN": (93, 0), "MP_HATCH_ROAD": (252, 0),
    "MP_HATCH_WATER": (151, 0), "MP_HATCH_TOWER": (11, 0),
}
FILL = {
    "villa": (246, 226, 150), "house": (240, 200, 120), "tower": (150, 150, 205), "sv": (238, 190, 196),
    "util": (180, 180, 180), "garden": (150, 200, 120), "park": (120, 182, 100), "verge": (196, 224, 170),
    "road": (200, 200, 200), "lane": (222, 222, 222), "water": (110, 190, 225), "plaza": (236, 222, 200),
    "park_lot": (232, 232, 232), "sport": (200, 110, 90), "path": (232, 214, 180),
}


def polys(g):
    if g is None or g.is_empty:
        return []
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 0.5]


def footprint(p, kind):
    """Indicative building footprint: villas 4 m front setback and 3 m side yards, houses attached."""
    c = p.minimum_rotated_rectangle
    return p.buffer(-3.0 if kind == "V" else -2.0, join_style="mitre")


def write_dxf(path):
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 6
    doc.styles.add("AR", font="arial.ttf")
    for n, (c, lw) in LAYERS.items():
        doc.layers.add(n, color=c, lineweight=lw if lw else -3)
    msp = doc.modelspace()

    def outline(g, layer):
        for p in polys(g):
            msp.add_lwpolyline([utm(q) for q in p.exterior.coords[:-1]], close=True, dxfattribs={"layer": layer})
            for hole in p.interiors:
                msp.add_lwpolyline([utm(q) for q in hole.coords[:-1]], close=True, dxfattribs={"layer": layer})

    def hatch(g, layer, key):
        for p in polys(g):
            h = msp.add_hatch(dxfattribs={"layer": layer})
            h.rgb = FILL[key]
            h.paths.add_polyline_path([utm(q) for q in p.exterior.coords[:-1]], is_closed=True)
            for hole in p.interiors:
                h.paths.add_polyline_path([utm(q) for q in hole.coords[:-1]], is_closed=True)

    def line(ls, layer):
        msp.add_lwpolyline([utm(q) for q in ls.coords], dxfattribs={"layer": layer})

    def text(s, at, h=3.0, layer="MP_TEXT", rot=0.0):
        t = msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "AR"})
        t.set_placement(utm(at), align=TextEntityAlignment.MIDDLE_CENTER)

    hatch(SITE, "MP_HATCH_GREEN", "verge")
    hatch(GARDEN, "MP_HATCH_GREEN", "garden")
    hatch(SE_PARK, "MP_HATCH_GREEN", "park")
    hatch(unary_union([BOULEVARD, STREET2, CROSS_IN, C_ROADS, SE_ROADS, SV_ROADS, T_ROADS]), "MP_HATCH_ROAD", "road")
    hatch(PLAZA.difference(T_DROP), "MP_HATCH_ROAD", "plaza")
    for g in (T_PLAZA_GREEN, SV_GREEN, UTIL_GREEN):
        hatch(g, "MP_HATCH_GREEN", "garden")
    hatch(SEC_SCHOOL, "MP_HATCH_SERV", "sv")
    for g in T_FOUNTAINS + [T_CHANNEL, WATER]:
        hatch(g, "MP_HATCH_WATER", "water")
    hatch(PATHS, "MP_HATCH_ROAD", "path")
    for p in VILLAS:
        hatch(p, "MP_HATCH_RES", "villa")
    for p in HOUSES:
        hatch(p, "MP_HATCH_RES", "house")
    for g in SV.values():
        hatch(g, "MP_HATCH_SERV", "sv")
    for g in UTIL_ITEMS.values():
        hatch(g, "MP_HATCH_SERV", "util")
    for t in TOWERS:
        hatch(t, "MP_HATCH_TOWER", "tower")

    outline(SITE, "MP_BOUNDARY")
    outline(SITE_RAW, "MP_BOUNDARY_COORDS")
    for g in (TOWER_ZONE, CENTRAL, SE_Q, UTIL):
        outline(g, "MP_FENCE")
    for g in (BOULEVARD, STREET2, CROSS_IN, C_ROADS, SE_ROADS, SV_ROADS, T_ROADS):
        outline(g, "MP_ROADS")
    outline(PLAZA, "MP_PATHS")
    outline(BASEMENT, "MP_PARKING")
    outline(T_RAMP, "MP_PARKING")
    outline(SEC_SCHOOL, "MP_SERVICES")
    for g in T_FOUNTAINS + [T_CHANNEL, WATER] + CASCADES:
        outline(g, "MP_WATER")
    for g in [PATHS, AMPHI, CAFE, SPORT] + BRIDGES:
        outline(g, "MP_PATHS")
    outline(GARDEN, "MP_GARDEN")
    outline(SE_PARK, "MP_GARDEN")
    for i, p in enumerate(VILLAS):
        outline(p, "MP_PLOT_VILLA")
        outline(footprint(p, "V"), "MP_FOOTPRINT")
        text(f"V{i + 1:03d}", tuple(p.centroid.coords[0]), 1.6, "MP_TEXT_PLOTNO")
    for i, p in enumerate(HOUSES):
        outline(p, "MP_PLOT_HOUSE")
        outline(footprint(p, "H"), "MP_FOOTPRINT")
        text(f"H{i + 1:03d}", tuple(p.centroid.coords[0]), 1.4, "MP_TEXT_PLOTNO")
    for g in SV.values():
        outline(g, "MP_SERVICES")
    outline(MOSQUE_FP, "MP_FOOTPRINT")
    for g in UTIL_ITEMS.values():
        outline(g, "MP_UTILITIES")
    for t in TOWERS:
        outline(t, "MP_TOWERS")
    for g in GATES.values():
        line(g, "MP_GATES")
    for g in GUARDS:
        outline(g, "MP_GATES")
    for t in TREES:
        msp.add_circle(utm((t.x, t.y)), 3.0, dxfattribs={"layer": "MP_TREES"})
    # long-side roads outside the plot (approx., 12 m) and entry arrows
    for a, b in ((P[3], P[0]), (P[1], P[2])):
        la, lb = loc(a), loc(b)
        dv = np.subtract(lb, la) / math.dist(la, lb)
        for d in (0.0, 12.0):
            nn = np.array([-dv[1], dv[0]]) * d
            msp.add_line(utm(tuple(np.add(la, nn - dv * 40))), utm(tuple(np.add(lb, nn + dv * 40))), dxfattribs={"layer": "MP_CONTEXT"})
    for k, at in ENTRIES.items():
        text("ENTRY - مدخل", at, 4.5, "MP_GATES")

    for k, g in {**SV, **UTIL_ITEMS, "SEC_SCHOOL": SEC_SCHOOL}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        text(n1, (q.x, q.y + 2.5), 3)
        text(f"{n2}  {g.area:,.0f} m2", (q.x, q.y - 2.5), 2.2)
    for k, at in LABELS.items():
        n1, n2 = NAMES[k]
        text(n1, (at[0], at[1] + 2.8), 3.6)
        text(n2, (at[0], at[1] - 2.8), 2.8)
    if not AMPHI.is_empty:
        text("AMPHITHEATRE - مسرح مكشوف", tuple(AMPHI.centroid.coords[0]), 2)
    for t, nm in zip(TOWERS, ("TOWER A", "TOWER B", "TOWER C")):
        text(nm, (t.centroid.x, t.centroid.y + 3), 3.5)
        text("20 floors, 80 flats", (t.centroid.x, t.centroid.y - 3), 2.2)
    q = BASEMENT.representative_point()
    text(f"BASEMENT PARKING {BASEMENT_CARS} CARS - سرداب", (q.x, q.y - 40), 2.5)

    na = (-60, 330)
    gn = np.array([U[1], V[1]])
    tip = tuple(np.add(na, gn * 30))
    msp.add_lwpolyline([utm(tuple(np.add(na, np.array([-gn[1], gn[0]]) * 8 - gn * 10))), utm(tip),
                        utm(tuple(np.add(na, np.array([gn[1], -gn[0]]) * 8 - gn * 10)))], close=True, dxfattribs={"layer": "MP_NORTH"})
    text("N", tuple(np.add(na, gn * 40)), 10, "MP_NORTH")
    tx, ty = 338560.0, 4035840.0
    rows = table_rows() + ["", "LAND USE - استعمالات الأرض              m2        %"]
    rows += [f"{n:<48s}{a:>9,.0f}  {a / SITE.area * 100:5.1f}" for n, a in LANDUSE]
    rows.append(f"{'TOTAL':<48s}{SITE.area:>9,.0f}  100.0")
    for i, row in enumerate(rows):
        msp.add_text(row, height=5 if i == 0 else 3.6, dxfattribs={"layer": "MP_TABLE", "style": "AR"}).set_placement(
            (tx, ty - i * 6.5), align=TextEntityAlignment.TOP_LEFT)
    doc.saveas(path)


# --- preview (vertical, like the concept render: NW end at the top) --------------------------------
def write_preview(png, pdf):
    import arabic_reshaper
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import Polygon as MPoly

    font_manager.fontManager.addfont(FONT)
    plt.rcParams["font.family"] = ["DejaVu Sans", "Noto Sans Arabic"]

    def ar(s):
        return arabic_reshaper.reshape(s)  # matplotlib 3.11 orders RTL runs itself

    def X(p):  # local (u, v) -> sheet (x, y): v to the right, u downwards
        return (p[1], -p[0])

    fig = plt.figure(figsize=(23.4, 33.1))  # A1 portrait
    ax = fig.add_axes([0.03, 0.03, 0.56, 0.93])
    rgb = {k: tuple(c / 255 for c in v) for k, v in FILL.items()}

    def f(g, key, ec="#555", lw=0.3, z=1):
        for p in polys(g):
            ax.add_patch(MPoly([X(q) for q in p.exterior.coords], closed=True, fc=rgb[key] if key else "none", ec=ec, lw=lw, zorder=z))
            for hole in p.interiors:
                ax.add_patch(MPoly([X(q) for q in hole.coords], closed=True, fc=rgb["verge"], ec=ec, lw=lw, zorder=z))

    def t(s, at, size=6, ar_s=None, w="normal", color="#222", z=10, box_=False):
        x, y = X(at)
        txt = s if ar_s is None else f"{ar(ar_s)}\n{s}"
        kw = dict(boxstyle="round,pad=0.3", fc="white", ec="#333", lw=0.6, alpha=0.9) if box_ else None
        ax.text(x, y, txt, fontsize=size, ha="center", va="center", fontweight=w, color=color, zorder=z,
                linespacing=1.15, bbox=kw)

    f(SITE, "verge", ec="none")
    f(GARDEN, "garden", ec="#5a8a40", lw=0.5)
    f(SE_PARK, "park", ec="#5a8a40", lw=0.5)
    f(PATHS, "path", ec="none", z=2)
    f(WATER, "water", ec="#2a6f9a", lw=0.6, z=3)
    for g in CASCADES:
        f(g, "plaza", ec="#2a6f9a", lw=0.5, z=4)
    for g in BRIDGES:
        f(g, "plaza", ec="#7a5a3a", lw=0.5, z=4)
    f(AMPHI, "plaza", ec="#7a5a3a", lw=0.5, z=4)
    f(CAFE, "sv", ec="#7a3a4a", lw=0.5, z=4)
    f(unary_union([BOULEVARD, STREET2, CROSS_IN]), "road", ec="#666", lw=0.6, z=2)
    f(unary_union([C_ROADS, SE_ROADS, SV_ROADS, T_ROADS]), "lane", ec="#777", lw=0.4, z=2)
    for g in (T_PLAZA_GREEN, SV_GREEN, UTIL_GREEN):
        f(g, "garden", ec="none", z=1)
    f(PLAZA.difference(T_DROP), "plaza", ec="#7a5a3a", z=3)
    for g in T_FOUNTAINS + [T_CHANNEL]:
        f(g, "water", ec="#2a6f9a", z=4)
    f(SEC_SCHOOL, "sv", ec="#8a4a5a", lw=0.5, z=3)
    for x_, y_ in [X(q) for q in BASEMENT.exterior.coords]:
        pass
    ax.plot(*zip(*[X(q) for q in BASEMENT.exterior.coords]), color="#555", lw=0.9, ls="--", zorder=4)
    f(T_RAMP, "lane", ec="#555", z=4)
    for pm in PALMS:
        ax.add_patch(plt.Circle(X((pm.x, pm.y)), 2.2, fc="#5f9a3f", ec="#2f5a1f", lw=0.3, zorder=5))
    for p in VILLAS:
        f(p, "villa", ec="#8a6a30", lw=0.3, z=3)
        f(footprint(p, "V"), None, ec="#555", lw=0.25, z=3)
    for p in HOUSES:
        f(p, "house", ec="#8a5a20", lw=0.3, z=3)
    for k, g in SV.items():
        f(g, "sv", ec="#8a4a5a", lw=0.5, z=3)
    f(MOSQUE_FP, "plaza", ec="#555", lw=0.6, z=4)
    f(SPORT, "sport", ec="#633", z=4)
    for g in UTIL_ITEMS.values():
        f(g, "util", ec="#444", lw=0.5, z=3)
    for tw in TOWERS:
        f(tw, "tower", ec="#33336a", lw=0.9, z=5)
    for g in (TOWER_ZONE, CENTRAL, SE_Q, UTIL):
        f(g, None, ec="#333", lw=0.8, z=6)
    f(SITE, None, ec="#d00", lw=2.0, z=7)
    for g in GATES.values():
        ax.plot(*zip(*[X(q) for q in g.coords]), color="#d00", lw=3.5, zorder=8)
    for g in GUARDS:
        f(g, "util", ec="#333", lw=0.6, z=8)
    for tr in TREES:
        ax.add_patch(plt.Circle(X((tr.x, tr.y)), 3.0, fc="#3d7a2d", ec="#1f4f1f", lw=0.3, alpha=0.85, zorder=6))
    # long-side roads outside the plot
    for a, b in ((P[3], P[0]), (P[1], P[2])):
        la, lb = loc(a), loc(b)
        dv = np.subtract(lb, la) / math.dist(la, lb)
        nn = np.array([-dv[1], dv[0]])
        pts = [np.add(la, -dv * 30), np.add(lb, dv * 30), np.add(lb, dv * 30 + nn * 14), np.add(la, -dv * 30 + nn * 14)]
        ax.add_patch(MPoly([X(tuple(p)) for p in pts], closed=True, fc=rgb["road"], ec="#666", lw=0.5, zorder=0))
    for k, at in ENTRIES.items():
        side = -1 if at[1] < 0 else 1
        x, y = X(at)
        ax.annotate("", xy=(x - side * 10, y), xytext=(x + side * 22, y),
                    arrowprops=dict(arrowstyle="-|>", color="k", lw=2.2, mutation_scale=22), zorder=9)
        ax.text(x + side * 46, y, f"{ar('مدخل')}\nENTRY", fontsize=8, ha="center", va="center", fontweight="bold", zorder=9)

    for k, g in {**SV, **UTIL_ITEMS, "SEC_SCHOOL": SEC_SCHOOL}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        t(f"{n1}\n{g.area:,.0f} m²", (q.x, q.y), 6.5, ar_s=n2)
    for k, at in LABELS.items():
        n1, n2 = NAMES[k]
        t(n1, at, 8.5, ar_s=n2, w="bold", box_=k in ("GARDEN", "TOWERS", "VILLAS", "HOUSES", "SE_PARK"))
    for k, g in (("AMPHI", AMPHI), ("CAFE", CAFE)):
        if g.is_empty:
            continue
        n1, n2 = NAMES[k]
        t(n1, tuple(g.centroid.coords[0]), 5.5, ar_s=n2)
    for tw, nm in zip(TOWERS, ("A", "B", "C")):
        t(f"TOWER {nm}\n20 F", tw.centroid.coords[0], 7, color="white", w="bold", z=11)

    gn = np.array([U[1], V[1]])
    na = np.array(X((-2.0, 330.0)))
    g2 = np.array([gn[1], -gn[0]])          # grid north on the sheet
    s2 = np.array([-g2[1], g2[0]])
    ax.add_patch(MPoly([tuple(na - g2 * 12 + s2 * 9), tuple(na + g2 * 30), tuple(na - g2 * 12 - s2 * 9)], closed=True, fc="k", zorder=12))
    ax.text(*(na + g2 * 44), "N", fontsize=16, ha="center", va="center", fontweight="bold")
    for i in range(5):
        ax.add_patch(plt.Rectangle((230 + i * 20, -905), 20, 5, fc="k" if i % 2 == 0 else "w", ec="k", lw=0.6))
        ax.text(230 + i * 20, -912, f"{i * 20}", fontsize=8, ha="center")
    ax.text(335, -912, "100 m", fontsize=8, ha="left")
    ax.set_xlim(-70, 360)
    ax.set_ylim(-925, 25)
    ax.set_aspect("equal")
    ax.axis("off")

    # side panel
    fig.text(0.97, 0.965, ar("مجمع الشلالات السكني - المقترح هـ (تعديل 2): حديقة الشلالات"), ha="right", fontsize=30, fontweight="bold")
    fig.text(0.97, 0.948, "MASTER PLAN - PROPOSAL E rev 2: SHALLALAT GARDEN", ha="right", fontsize=17)
    fig.text(0.97, 0.935, ar("القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026 - مساحة 199,175 م²"), ha="right", fontsize=14)
    units = len(VILLAS) + len(HOUSES) + N_APTS
    summ = [
        ar(f"{units} وحدة سكنية لنحو {POP:,} ساكن"),
        ar(f"{len(VILLAS)} فيلا 400 م² + {len(HOUSES)} داراً 240 م² + {N_APTS} شقة في 3 أبراج (20 طابقاً)"),
        ar(f"الخضرة {GREEN_M2:,.0f} م² ({GREEN_M2 / SITE.area * 100:.1f}%) والشوارع {ROADS_M2 / SITE.area * 100:.1f}%"),
        ar(f"سرداب تحت ساحة الأبراج لـ {BASEMENT_CARS} سيارة، بدون نادٍ"),
        ar("مدخلان فقط من الشارعين الجانبيين: البوابة الرئيسية وبوابة ثانوية للبرجين"),
        ar("حذف المواقف الخارجية العليا والمجرى المائي السفلي"),
    ]
    for i, s in enumerate(summ):
        fig.text(0.97, 0.912 - i * 0.016, s, ha="right", fontsize=13)
    tx = fig.add_axes([0.62, 0.40, 0.35, 0.40])
    tx.axis("off")
    y0 = 1.0
    tx.text(1.0, y0, ar("توزيع استعمالات الأرض"), fontsize=15, fontweight="bold", va="top", ha="right")
    tx.text(0.0, y0, "LAND USE", fontsize=12, fontweight="bold", va="top")
    for i, (n, a) in enumerate(LANDUSE + [("TOTAL - المجموع", SITE.area)]):
        en, arb = n.split(" - ")
        y = y0 - 0.065 * (i + 1)
        tx.text(1.0, y, ar(arb), fontsize=12, va="top", ha="right", fontweight="bold" if en == "TOTAL" else "normal")
        tx.text(0.0, y - 0.025, en, fontsize=9, va="top", color="#555")
        tx.text(0.38, y, f"{a:,.0f}", fontsize=12, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(0.50, y, f"{a / SITE.area * 100:.1f}%", fontsize=12, va="top", ha="right", family="DejaVu Sans Mono")
    key = [
        ("villa", "Villa plot 400 m² (16 x 25)", "قطعة فيلا منفصلة"), ("house", "Attached house 240 m² (12 x 20)", "قطعة دار متصلة"),
        ("tower", "Tower, 20 floors", "برج سكني"), ("sv", "Public services", "خدمات عامة"), ("util", "Utilities", "مرافق فنية"),
        ("garden", "Central garden", "حديقة الشلالات"), ("park", "Neighbourhood park", "حديقة الحي"),
        ("water", "Cascades, lake, fountain", "شلالات وبحيرة ونافورة"), ("road", "Main boulevard, cross road", "الشارع الرئيسي والشارع العرضي"),
        ("lane", "Internal roads 12 m", "شوارع داخلية 12 م"), ("park_lot", "Parking", "مواقف"),
    ]
    lg = fig.add_axes([0.62, 0.12, 0.35, 0.25])
    lg.axis("off")
    for i, (k, en, a) in enumerate(key):
        y = 1 - i * 0.085
        lg.add_patch(plt.Rectangle((0.88, y - 0.05), 0.12, 0.055, fc=rgb[k], ec="#555", transform=lg.transAxes))
        lg.text(0.85, y - 0.022, ar(a), fontsize=12, ha="right", va="center", transform=lg.transAxes)
        lg.text(0.0, y - 0.022, en, fontsize=10, ha="left", va="center", color="#444", transform=lg.transAxes)
    lg.plot([0.88, 1.0], [1 - len(key) * 0.085 - 0.02] * 2, color="#d00", lw=3, transform=lg.transAxes)
    lg.text(0.85, 1 - len(key) * 0.085 - 0.02, ar("بوابة مراقبة"), fontsize=12, ha="right", va="center", transform=lg.transAxes)
    lg.text(0.0, 1 - len(key) * 0.085 - 0.02, "Controlled gate", fontsize=10, ha="left", va="center", color="#444", transform=lg.transAxes)
    fig.text(0.97, 0.06, ar("الحدود: القطعة الصافية حسب الإعلان 199,175 م² (UTM 38S). المخطط استرشادي لمرحلة الفكرة."),
             ha="right", fontsize=11, color="#555")
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)
    plt.close(fig)


if __name__ == "__main__":
    out = os.environ.get("OUT_DIR", HERE)
    write_dxf(os.path.join(out, "SHALLALAT_MASTERPLAN_E_REV2.dxf"))
    write_preview(os.path.join(out, "SHALLALAT_MASTERPLAN_E_REV2_preview.png"), os.path.join(out, "SHALLALAT_MASTERPLAN_E_REV2_preview.pdf"))
    for r in table_rows():
        print(r)
    for n, a in LANDUSE:
        print(f"{n:<48s}{a:>9,.0f}  {a / SITE.area * 100:5.1f}")
    print("capacity", CAP, "ST2", ST2_U, "SE_END", round(SE_END_U), "gap", round(TOWER_GAP, 1))
    print({k: round(g.area) for k, g in {**SV, **UTIL_ITEMS, "SEC": SEC_SCHOOL}.items()})
