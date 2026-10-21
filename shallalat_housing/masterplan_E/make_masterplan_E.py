"""Master plan, proposal E "Shallalat garden" (حديقة الشلالات) for plot 157 / district 53 Baybokht.

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


# --- chainages of the main bands --------------------------------------------------------------------
BLV_U = (438.0, 462.0)    # 24 m boulevard from the main gate on the north road, closed at the south wall
ST2_U = (640.0, 656.0)    # 16 m internal street between services and the SE quarter, closed at both walls
TOWER_ZONE = SITE.difference(past_cross(-5.0))           # NW end, before the cross road
CENTRAL = SITE.intersection(past_cross(5.0)).intersection(box(-100, -50, BLV_U[0], 500))
SERVICES = across(BLV_U[1], ST2_U[0])
SE_Q = across(ST2_U[1], 2000)
BOULEVARD = across(*BLV_U).intersection(box(-100, 20.0, 2000, 500))
STREET2 = across(*ST2_U).intersection(box(-100, 20.0, 2000, 500)).difference(nstrip(-50, 1200, -50, 16.0))

ROAD = 12.0
VD, VF = 25.0, 16.0       # villa plot depth x frontage = 400 m2
HD, HF = 20.0, 10.0       # house plot depth x frontage = 200 m2

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
C_VILLAS = rows_south(REG_S, [0.0, S1[1], S1[1] + VD], 0, BLV_U[0], "V")
C_HOUSES = rows_north(REG_N, [0.0, N1[1], N1[1] + HD], 0, t_of(BLV_U[0]) + 5, "H")

# --- SE quarter: villa rows on the south side, house rows on the north side, park between ------------
SE_S = (VD, VD + ROAD)
SE_N = (HD, HD + ROAD)
SE_END_U = 790.0          # loop road across the quarter; utilities beyond it at the narrow tip
SE_LOOP = box(SE_END_U, 0, SE_END_U + ROAD, 500)
SE_ROADS = unary_union([box(ST2_U[1] - 1, SE_S[0], SE_END_U + ROAD, SE_S[1]),
                        nstrip(t_of(ST2_U[1]) - 3, t_of(SE_END_U + ROAD) + 3, *SE_N), SE_LOOP]).intersection(SE_Q)
_se_core = SE_Q.intersection(box(-100, -50, SE_END_U, 500))
SE_FREE = _se_core.difference(SE_ROADS.buffer(0.01))
SE_VILLAS = rows_south(SE_FREE.intersection(box(-100, 0, 2000, SE_S[1] + VD)), [0.0, SE_S[1]], ST2_U[1], SE_END_U, "V")
SE_HOUSES = rows_north(SE_FREE.difference(nstrip(-50, 1200, SE_N[1] + HD, 600)), [0.0, SE_N[1]],
                       t_of(ST2_U[1]) - 2, t_of(SE_END_U) + 2, "H")
SE_PARK = _se_core.intersection(box(-100, SE_S[1] + VD, 2000, 500)).difference(nstrip(-50, 1200, -50, SE_N[1] + HD))
SE_PARK = max(getattr(SE_PARK, "geoms", [SE_PARK]), key=lambda g: g.area)
UTIL = SE_Q.intersection(box(SE_END_U + ROAD, -50, 2000, 500))

VILLAS = C_VILLAS + SE_VILLAS
HOUSES = C_HOUSES + SE_HOUSES

# --- tower zone (NW end) -----------------------------------------------------------------------------
T_GATE_U_ = 80.0  # tower access road from the south road
TW = 28.3  # 800 m2 floor plate, 4 flats per floor
T_CEN = [(62.0, 88.0), (62.0, 212.0)]
TOWERS = [box(c[0] - TW / 2, c[1] - TW / 2, c[0] + TW / 2, c[1] + TW / 2) for c in T_CEN]
TOWER_GAP = TOWERS[0].distance(TOWERS[1])
T_PLAZA_C = (62.0, 150.0)
T_LOOP = Point(T_PLAZA_C).buffer(34).difference(Point(T_PLAZA_C).buffer(26))       # drop-off ring
T_PLAZA = Point(T_PLAZA_C).buffer(26)
T_FOUNTAIN = Point(T_PLAZA_C).buffer(11)
T_POOL = box(102, 136, 124, 164)  # reflecting pool on the plaza axis, towards the cross road
T_PARK = [box(8, 8, 46, 62), box(8, 238, 46, 292).intersection(SITE.buffer(-6)),
          box(92, 8, 128, 62), box(92, 238, 116, 280).intersection(SITE.buffer(-6))]
T_RING = unary_union([band((4, 4), (4, 300), 3.5), band((4, 70), (130, 70), 3.5), band((4, 230), (110, 230), 3.5),
                      band((50, 70), (50, 230), 3.5)]).intersection(TOWER_ZONE.buffer(-2))
T_ROADS = unary_union([T_LOOP, T_RING, band((T_GATE_U_, 0.0), (T_GATE_U_, 70.0), 5.0).intersection(TOWER_ZONE)])
T_SPORT = box(16, 120, 30, 180)          # tennis / multi-court along the NW wall
T_PLAY = Point((100, 100)).buffer(9)

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

# --- service centre between the boulevard and the 16 m street ---------------------------------------
SV_IN = SERVICES.buffer(-3, join_style="mitre")
SV_ST = 12.0
SV_V1 = (66.0, 66.0 + SV_ST)      # service street along u, south
SV_V2 = (146.0, 146.0 + SV_ST)    # service street along u, north
SV_ROADS = unary_union([box(BLV_U[1] - 1, *SV_V1, ST2_U[0] + 1, ), box(BLV_U[1] - 1, SV_V2[0], ST2_U[0] + 1, SV_V2[1])])
SV_ROADS = unary_union([box(BLV_U[1] - 1, SV_V1[0], ST2_U[0] + 1, SV_V1[1]), box(BLV_U[1] - 1, SV_V2[0], ST2_U[0] + 1, SV_V2[1]),
                        box(548, SV_V1[1] - 1, 560, SV_V2[0] + 1)]).intersection(SERVICES)
U0, U1 = BLV_U[1] + 4, ST2_U[0] - 4
SV = {
    "PRIMARY": box(U0, 0, 544, SV_V1[0] - 3),
    "INT_SCHOOL": box(564, 0, U1, SV_V1[0] - 3),
    "MOSQUE": box(U0, SV_V1[1] + 3, 544, SV_V2[0] - 3),
    "HEALTH": box(564, SV_V1[1] + 3, 600, SV_V2[0] - 3),
    "MARKET": box(604, SV_V1[1] + 3, U1, SV_V2[0] - 3),
    "POLICE": box(U0, SV_V2[1] + 3, 510, 400),
    "CIVIL_DEF": box(514, SV_V2[1] + 3, 560, 400),
    "YOUTH": box(564, SV_V2[1] + 3, 600, 400),
    "ADMIN": box(604, SV_V2[1] + 3, U1, 400),
}
SV = {k: g.intersection(SV_IN) for k, g in SV.items()}
MOSQUE_FP = Point(SV["MOSQUE"].centroid).buffer(15, quad_segs=2)  # indicative square prayer hall
SPORT = box(U0 + 6, 6, U0 + 40, 26)                                # school pitch

_ub = UTIL.buffer(-3, join_style="mitre")
_ubb = _ub.bounds
UTIL_ITEMS = {
    "SUBSTATION": _ub.intersection(box(_ubb[0], -50, _ubb[2], 52)),
    "DESAL": _ub.intersection(box(_ubb[0], 56, _ubb[2], 102)),
    "SEWAGE": _ub.intersection(box(_ubb[0], 106, _ubb[2], 500)),
}

# --- gates -------------------------------------------------------------------------------------------
# only two entrances, both from the long-side roads (the short ends do not front a street)
MG_T = t_of((BLV_U[0] + BLV_U[1]) / 2) + 6
MAIN_GATE = LineString([npt(MG_T - 16, 14.0), npt(MG_T + 16, 14.0)])          # main gate on the north road
MAIN_GUARD = nstrip(MG_T + 13, MG_T + 19, 4.0, 12.0)
T_GATE_U = 80.0
T_ACCESS = band((T_GATE_U, 0.0), (T_GATE_U, 70.0), 5.0).intersection(TOWER_ZONE)
T_GATE = LineString([(T_GATE_U - 7, 8.0), (T_GATE_U + 7, 8.0)])                  # tower gate on the south road
T_GUARD = box(T_GATE_U + 7, 2.0, T_GATE_U + 13, 10.0)
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
_tz_free = TOWER_ZONE.buffer(-4).difference(unary_union(TOWERS + T_PARK + [T_ROADS, T_PLAZA, T_POOL, T_SPORT, T_PLAY]).buffer(3))
TREES += scatter(_tz_free, 120)
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


N_APTS = 2 * 19 * 4
LANDUSE = [
    ("Villa plots 400 m2 - قطع الفلل", len(VILLAS) * 400.0),
    ("House plots 200 m2 - قطع الدور", len(HOUSES) * 200.0),
    ("Tower zone - منطقة البرجين", TOWER_ZONE.area),
    ("Services - الخدمات العامة", A(SV.values())),
    ("Utilities - المرافق الفنية", UTIL.area),
    ("Shallalat central garden - حديقة الشلالات", GARDEN.area),
    ("SE quarter park - حديقة الحي الجنوبي", SE_PARK.area),
    ("Public cross road - الشارع العرضي العام", CROSS_IN.area),
    ("Boulevard + internal roads - الشارع الرئيسي والشوارع الداخلية",
     unary_union([BOULEVARD, STREET2, C_ROADS, SE_ROADS, SV_ROADS]).area),
    ("Belts, verges, small gardens - أحزمة خضراء", 0.0),
]
LANDUSE[-1] = (LANDUSE[-1][0], SITE.area - sum(a for _, a in LANDUSE))
GREEN_M2 = GARDEN.area + SE_PARK.area + LANDUSE[-1][1]
POP = len(VILLAS) * 6 + len(HOUSES) * 6 + 2 * 19 * (2 * 4 + 2 * 6)

NAMES = {
    "PRIMARY": ("PRIMARY SCHOOL", "مدرسة ابتدائية"), "INT_SCHOOL": ("INTERMEDIATE + SECONDARY", "مدرسة متوسطة وإعدادية"),
    "MOSQUE": ("FRIDAY MOSQUE + PLAZA", "جامع وساحة"), "HEALTH": ("HEALTH CENTRE", "مركز صحي"),
    "MARKET": ("MARKET + RESTAURANTS", "سوق ومطاعم ومقاهي"), "POLICE": ("POLICE", "مركز شرطة"),
    "CIVIL_DEF": ("CIVIL DEFENCE", "دفاع مدني"), "YOUTH": ("SOCIAL + YOUTH CENTRE", "مركز اجتماعي وشبابي"),
    "ADMIN": ("ADMIN + SECURITY", "إدارة المجمع والأمن"),
    "SUBSTATION": ("33/11 kV SUBSTATION", "محطة كهرباء"), "DESAL": ("WATER TREATMENT + TANK", "محطة تحلية وخزان"),
    "SEWAGE": ("SEWAGE + WASTE", "معالجة مجاري ونفايات"),
    "GARDEN": ("SHALLALAT CENTRAL GARDEN", "حديقة الشلالات المركزية"),
    "SE_PARK": ("NEIGHBOURHOOD PARK", "حديقة الحي"),
    "BLV": ("MAIN BOULEVARD 24 m", "الشارع الرئيسي 24 م"),
    "ST2": ("INTERNAL STREET 16 m", "شارع داخلي 16 م"),
    "MGATE": ("MAIN GATE", "البوابة الرئيسية"),
    "CROSS": ("CROSS ROAD (PUBLIC)", "الشارع العرضي"),
    "TOWERS": ("TOWER ZONE", "منطقة البرجين"),
    "TGATE": ("SECONDARY GATE (TOWERS)", "بوابة ثانوية للبرجين"),
    "VILLAS": ("DETACHED VILLAS", "فلل منفصلة"), "HOUSES": ("ATTACHED HOUSES", "دور متصلة"),
    "AMPHI": ("AMPHITHEATRE", "مسرح مكشوف"), "CAFE": ("GARDEN CAFE", "مقهى الحديقة"),
}
LABELS = {
    "GARDEN": (AX[len(AX) // 2 - 6][0], AX[len(AX) // 2 - 6][1] + 30),
    "SE_PARK": tuple(SE_PARK.representative_point().coords[0]),
    "BLV": ((BLV_U[0] + BLV_U[1]) / 2, 110.0),
    "ST2": ((ST2_U[0] + ST2_U[1]) / 2, 110.0),
    "CROSS": tuple(np.add(CROSS_A, cross_dir * 60)),
    "TOWERS": (120.0, 210.0),
    "TGATE": (T_GATE_U + 2, 22.0),
    "MGATE": tuple(npt(MG_T, 26.0)),
    "VILLAS": (230.0, 12.5),
    "HOUSES": tuple(npt(t_of(230), 10)),
}


def table_rows():
    units = len(VILLAS) + len(HOUSES) + N_APTS
    return [
        "PROPOSAL E - SHALLALAT GARDEN - المقترح هـ: حديقة الشلالات",
        "Plot 157 / District 53 Baybokht - NIC 5/2026 - UTM 38S",
        "",
        f"UNITS: {len(VILLAS)} villas 400 m2 + {len(HOUSES)} houses 200 m2 + {N_APTS} flats = {units}",
        f"Population approx. {POP:,}  -  green {GREEN_M2:,.0f} m2 = {GREEN_M2 / POP:.1f} m2/person",
        f"Towers: 2 x (G+19), 800 m2 plate, clear gap {TOWER_GAP:.0f} m (min 33 m)",
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
    for g in T_PARK:
        hatch(g, "MP_HATCH_ROAD", "park_lot")
    hatch(T_PLAZA.difference(T_FOUNTAIN), "MP_HATCH_ROAD", "plaza")
    for g in (T_FOUNTAIN, T_POOL, WATER):
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
    for g in T_PARK:
        outline(g, "MP_PARKING")
    outline(T_PLAZA, "MP_PATHS")
    for g in [T_FOUNTAIN, T_POOL, WATER] + CASCADES:
        outline(g, "MP_WATER")
    for g in [PATHS, AMPHI, CAFE, T_SPORT, T_PLAY, SPORT] + BRIDGES:
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

    for k, g in {**SV, **UTIL_ITEMS}.items():
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
    for t, nm in zip(TOWERS, ("TOWER A", "TOWER B")):
        text(nm, (t.centroid.x, t.centroid.y + 3), 3.5)
        text("G+19, 76 flats", (t.centroid.x, t.centroid.y - 3), 2.2)

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
    for g in T_PARK:
        f(g, "park_lot", ec="#777", z=2)
    f(T_PLAZA, "plaza", ec="#7a5a3a", z=3)
    f(T_FOUNTAIN, "water", ec="#2a6f9a", z=4)
    f(T_POOL, "water", ec="#2a6f9a", z=3)
    f(T_SPORT, "sport", ec="#633", z=3)
    f(T_PLAY, "plaza", ec="#7a5a3a", z=3)
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

    for k, g in {**SV, **UTIL_ITEMS}.items():
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
    for tw, nm in zip(TOWERS, ("A", "B")):
        t(f"TOWER {nm}\nG+19", tw.centroid.coords[0], 7, color="white", w="bold", z=11)

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
    fig.text(0.97, 0.965, ar("مجمع الشلالات السكني - المقترح هـ: حديقة الشلالات"), ha="right", fontsize=30, fontweight="bold")
    fig.text(0.97, 0.948, "MASTER PLAN - PROPOSAL E: SHALLALAT GARDEN", ha="right", fontsize=17)
    fig.text(0.97, 0.935, ar("القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026 - مساحة 199,175 م²"), ha="right", fontsize=14)
    units = len(VILLAS) + len(HOUSES) + N_APTS
    summ = [
        ar(f"{units} وحدة سكنية لنحو {POP:,} ساكن"),
        ar(f"{len(VILLAS)} فيلا منفصلة 400 م² + {len(HOUSES)} دار متصلة 200 م² + {N_APTS} شقة في برجين"),
        ar(f"المساحات الخضراء {GREEN_M2:,.0f} م² = {GREEN_M2 / POP:.1f} م²/ساكن"),
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
        ("villa", "Villa plot 400 m² (16 x 25)", "قطعة فيلا منفصلة"), ("house", "Attached house 200 m² (10 x 20)", "قطعة دار متصلة"),
        ("tower", "Tower G+19", "برج سكني"), ("sv", "Public services", "خدمات عامة"), ("util", "Utilities", "مرافق فنية"),
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
    write_dxf(os.path.join(out, "SHALLALAT_MASTERPLAN_E.dxf"))
    write_preview(os.path.join(out, "SHALLALAT_MASTERPLAN_E_preview.png"), os.path.join(out, "SHALLALAT_MASTERPLAN_E_preview.pdf"))
    for r in table_rows():
        print(r)
    for n, a in LANDUSE:
        print(f"{n:<48s}{a:>9,.0f}  {a / SITE.area * 100:5.1f}")
    print("garden", GARDEN.area, "services", A(SV.values()), "C villas", len(C_VILLAS), "C houses", len(C_HOUSES),
          "SE villas", len(SE_VILLAS), "SE houses", len(SE_HOUSES))
