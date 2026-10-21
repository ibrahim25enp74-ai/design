"""Master plan proposal C - "the green valley" (الوادي الأخضر), plot 157 / district 53 Baybokht.

Geometry is built in a local frame aligned with the plot's south edge (u along Q1->Q4, v towards
the north edge, metres) and transformed to UTM 38S when written. Every feature is kept as
(layer, shapely geometry, label) so the DXF writer and the preview draw the same thing.

Concept: a continuous park runs down the length of the plot from the cross road to the
east end (the "valley"). The watercourse on the cadastral map is ignored, as the client asked. Cars stay on a collector loop near the plot edges and reach the
houses by short cul-de-sacs (Radburn); every house backs onto green - a green court, a green
finger, the park, or the perimeter belt with the jogging track - and green fingers with rain
channels drain into the park stream and a rain pond at its east end (Village Homes). Only the entry street
crosses the park, at the plaza with the waterfalls.
"""
import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

# --- frame -----------------------------------------------------------------------------------------
Q = {  # net plot corners (= announced area 199,175 m2), UTM 38S
    "Q1": (338955.19, 4035466.71),
    "Q2": (339030.78, 4035766.16),
    "Q3": (339833.37, 4035331.92),
    "Q4": (339749.71, 4035202.20),
}
O = np.array(Q["Q1"])
U = (np.array(Q["Q4"]) - O) / np.linalg.norm(np.array(Q["Q4"]) - O)
V = np.array([-U[1], U[0]])
ROT_DEG = math.degrees(math.atan2(U[1], U[0]))  # direction of the local u axis in the world


def to_local(p):
    d = np.array(p) - O
    return float(d @ U), float(d @ V)


def to_utm(u, v):
    p = O + U * u + V * v
    return float(p[0]), float(p[1])


QL = {k: to_local(p) for k, p in Q.items()}
SITE = Polygon([QL["Q1"], QL["Q2"], QL["Q3"], QL["Q4"]])


def v_north(u):
    (u2, v2), (u3, v3) = QL["Q2"], QL["Q3"]
    return v2 + (v3 - v2) * (u - u2) / (u3 - u2)


def u_east(v):
    (u4, v4), (u3, v3) = QL["Q4"], QL["Q3"]
    return u4 + (u3 - u4) * (v - v4) / (v3 - v4)


# cross road (public, kept) - centreline traced from the cadastral scan
XR_A, XR_B = to_local((339090.5, 4035416.6)), to_local((339155.5, 4035704.2))
XR_W = 12.0


def u_cross(v):
    return XR_A[0] + (XR_B[0] - XR_A[0]) * (v - XR_A[1]) / (XR_B[1] - XR_A[1])


# existing trees (scan trace), local coords
TREES = [to_local(p) for p in [
    (339005.0, 4035524.0), (339025.6, 4035589.3), (339068.2, 4035637.7), (339035.0, 4035495.9),
    (339058.6, 4035556.7), (339099.5, 4035609.0), (339100.1, 4035665.9)]]

# --- dimensions (m) ----------------------------------------------------------------------------------
BELT = 8.0  # green belt inside the fence, carries the perimeter jogging track
OUTER = 25.0  # outer row of villas between the belt and the loop (gardens onto the belt)
LEG = 12.0  # collector loop right of way
LANE = 7.0  # cul-de-sac (shared surface); 7 + 2 x front setback >= 12 m between facing houses
COURT = 6.0  # green court between the back gardens of two clusters
FINGER = 20.0  # green finger with rain channel
ENDGAP = 6.0  # turning head where a cul-de-sac meets the park
EAST0 = 712.0  # east service zone (school, club, utilities) starts here
EAST_GREEN = 10.0  # green strip with the jogging track between the houses and the east zone
VILLA = dict(f=16.0, d=25.0, front=4.0, side=2.0, bw=12.0, bd=10.0)  # 400 m2, 120 m2 footprint = 30 %
HOUSE = dict(f=10.0, d=20.0, front=2.5, side=0.0, bw=10.0, bd=12.0)  # 200 m2, 120 m2 footprint = 60 %

S_LEG = (BELT + OUTER, BELT + OUTER + LEG)  # v range of the south leg
GATE_U = 458.0  # main gate / entry street axis (~450 m from the west end of the north edge)
BLVD = 24.0
NU0 = 196.0  # the outer north row starts here; west of it a tree screen faces the towers
PLAZA = (424.0, 492.0)  # u range of the plaza
LINK = (480.0, 492.0)  # the one street that crosses the park (plaza -> south leg)


def n_leg(u):
    vn = v_north(u)
    return vn - BELT - OUTER - LEG, vn - BELT - OUTER


def w_leg(v):
    a = u_cross(v) + XR_W / 2 + 4  # cross road + planted verge
    return a, a + LEG


CORE_E = EAST0 - EAST_GREEN  # east limit of the housing core


# park: ~40 m wide down the middle of the core, opening to ~58 m at the plaza and widening at the ends
PLAZA_V = (88.0, 146.0)


def _mid(u):
    return (S_LEG[1] + n_leg(u)[0]) / 2


def _half(u):
    return float(np.interp(u, [150, 190, 300], [27, 20, 20]))


def p_s(u):
    if PLAZA[0] - 2 <= u <= PLAZA[1] + 2:
        return PLAZA_V[0]
    return _mid(u) - _half(u)


def p_n(u):
    if PLAZA[0] - 2 <= u <= PLAZA[1] + 2:
        return PLAZA_V[1]
    return _mid(u) + _half(u)


# cul-de-sac sequences per band: V villa cluster, H house cluster, C green court, F green finger,
# a number = gap in metres
SEQ = {
    "NW": ["V", "C", "V", "F", "V", "C", "H"],
    "SW": ["H", "C", "H", "F", "H", "C"],
    "SE": [2, "H", "C", "H", "F", "H", "C"],
    "NE": [4, "H", "C", "H", "C", "H"],
}
BANDS = {}
F = []  # (layer, geom, label)
COUNT = {"villa": 0, "house": 0}
AREAS = {}  # program item -> (drawn m2, program m2)


def add(layer, geom, label=None):
    F.append((layer, geom, label))
    return geom


def rect(u0, v0, u1, v1):
    return box(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1))


def along_north(u0, u1, off0, off1):
    """Quad between u0..u1 whose long edges run parallel to the north boundary (offsets from the leg)."""
    def p(u, off):
        return (u, n_leg(u)[1] + off)
    return Polygon([p(u0, off0), p(u1, off0), p(u1, off1), p(u0, off1)])


# --- housing -----------------------------------------------------------------------------------------
def plot(kind, geom, bldg):
    COUNT[kind] += 1
    lab = ("V" if kind == "villa" else "H") + str(COUNT[kind])
    add("MP-PLOT-VILLA" if kind == "villa" else "MP-PLOT-HOUSE", geom, lab)
    add("MP-BLDG-VILLA" if kind == "villa" else "MP-BLDG-HOUSE", bldg)


def cluster(kind, u0, band):
    """Two rows of plots on a cul-de-sac running from the loop leg towards the park.

    band "S": lane starts at the south leg and runs north; "N": starts at the north leg and runs south.
    Returns the u where the cluster ends.
    """
    t = VILLA if kind == "villa" else HOUSE
    u1 = u0 + 2 * t["d"] + LANE
    us = np.linspace(u0, u1, 12)
    if band == "S":
        start, sgn = S_LEG[1], 1
        stop = min(p_s(u) for u in us) - ENDGAP
    else:
        start, sgn = min(n_leg(u)[0] for u in us), -1
        stop = max(p_n(u) for u in us) + ENDGAP
    n = int(abs(stop - start) // t["f"])
    lane_end = start + sgn * n * t["f"]
    head_end = lane_end + sgn * ENDGAP
    lu0, lu1 = u0 + t["d"], u0 + t["d"] + LANE
    add("MP-ROAD-LOCAL", unary_union([rect(lu0, start, lu1, lane_end),
                                      rect(lu0 - 6, lane_end, lu1 + 6, head_end)]))
    add("MP-ROAD-CL", LineString([((lu0 + lu1) / 2, start), ((lu0 + lu1) / 2, head_end)]))
    if band == "N":  # sliver between the sloping leg and the first plots: entrance garden
        sl = Polygon([(u0, start), (u0, n_leg(u0)[0]), (u1, n_leg(u1)[0]), (u1, start)])
        if sl.area > 1:
            add("MP-GREEN-COURT", sl)
    for side in (0, 1):
        pu0 = u0 if side == 0 else lu1
        pu1 = pu0 + t["d"]
        fu0 = pu1 - t["front"] if side == 0 else pu0 + t["front"]
        fu1 = fu0 - t["bd"] if side == 0 else fu0 + t["bd"]
        for i in range(n):
            a = start + sgn * i * t["f"]
            b = a + sgn * t["f"]
            lo = min(a, b)
            bv0, bv1 = (lo + t["side"], lo + t["side"] + t["bw"]) if kind == "villa" else (lo, lo + t["f"])
            plot(kind, rect(pu0, a, pu1, b), rect(fu0, bv0, fu1, bv1))
    return u1


def court(u0, band, w=COURT):
    """Green court (or finger with rain channel) between clusters, from the leg to the park."""
    c = u0 + w / 2
    if band == "S":
        poly = Polygon([(u0, S_LEG[1]), (u0 + w, S_LEG[1]), (u0 + w, p_s(u0 + w)), (u0, p_s(u0))])
        a, b = S_LEG[1], p_s(c)
    else:
        poly = Polygon([(u0, n_leg(u0)[0]), (u0 + w, n_leg(u0 + w)[0]), (u0 + w, p_n(u0 + w)), (u0, p_n(u0))])
        a, b = n_leg(c)[0], p_n(c)
    if w >= FINGER:
        add("MP-GREEN-FINGER", poly)
        add("MP-WATER-CHANNEL", LineString([(c, a), (c, b)]))
        add("MP-PATH", rect(c + 3, a, c + 5.5, b))
    else:
        add("MP-GREEN-COURT", poly)
        add("MP-PATH", rect(c - 1.0, a, c + 1.0, b))
    return u0 + w


def run(seq, u0, band):
    u = u0
    for item in seq:
        if item == "V":
            u = cluster("villa", u, band)
        elif item == "H":
            u = cluster("house", u, band)
        elif item == "C":
            u = court(u, band)
        elif item == "F":
            u = court(u, band, FINGER)
        else:
            u += item
    return u


def outer_row(u0, u1, band, kind="villa"):
    """Plots fronting the loop leg, rear gardens onto the perimeter green belt."""
    t = VILLA if kind == "villa" else HOUSE
    n = int((u1 - u0) // t["f"])
    for i in range(n):
        a, b = u0 + i * t["f"], u0 + (i + 1) * t["f"]
        s0, s1 = (a + t["side"], a + t["side"] + t["bw"]) if kind == "villa" else (a, b)
        if band == "S":
            plot(kind, rect(a, BELT, b, S_LEG[0]),
                 rect(s0, S_LEG[0] - t["front"], s1, S_LEG[0] - t["front"] - t["bd"]))
        else:
            plot(kind, along_north(a, b, 0, OUTER), along_north(s0, s1, t["front"], t["front"] + t["bd"]))
    return u0 + n * t["f"]


# --- services ----------------------------------------------------------------------------------------
def service(layer, geom, name, program=None, bldg=None):
    add(layer, geom, name)
    AREAS[name] = (geom.area, program)
    if bldg is not None:
        add("MP-BLDG-SERVICE", bldg)
    return geom


def build():
    F.clear()
    COUNT.update(villa=0, house=0)
    AREAS.clear()
    vn = v_north

    # ---- plot, cross road ----
    add("MP-BOUNDARY", SITE)
    xr = SITE.intersection(Polygon([(u_cross(-50) - 6, -50), (u_cross(-50) + 6, -50),
                                    (u_cross(400) + 6, 400), (u_cross(400) - 6, 400)]))
    add("MP-ROAD-PUBLIC", xr, "شارع عرضي عام 12 م (يبقى)")
    add("MP-ROAD-CL", LineString([(u_cross(0), 0), (u_cross(vn(120)), vn(120))]))
    AREAS["الشارع العرضي العام"] = (xr.area, None)

    # ================= WEST PART: towers + public services ======================================
    def xw(v):  # west edge of the cross road
        return u_cross(v) - XR_W / 2
    west = SITE.intersection(Polygon([(-60, -10), (xw(-10), -10), (xw(400), 400), (-60, 400)]))
    s_top = 45.0  # public services face the south road
    service("MP-SERVICE-PUBLIC", rect(3, 0, 35, s_top), "مركز شرطة", 1200, rect(8, 8, 30, 26))
    service("MP-SERVICE-PUBLIC", rect(38, 0, 76, s_top), "دفاع مدني", 1500, rect(43, 6, 71, 30))
    service("MP-SERVICE-PUBLIC", rect(79, 0, 117, s_top), "مركز صحي", 1500, rect(84, 10, 112, 30))
    add("MP-PARKING", west.intersection(rect(120, 0, 200, s_top)), "مواقف")
    add("MP-PATH", west.intersection(rect(-60, s_top, 200, s_top + 4)))
    grove = west.intersection(rect(-60, s_top + 4, 200, 108))
    service("MP-PARK", grove, "حديقة البستان")
    # secondary schools face the cross road, yards onto the grove
    sch0, sch1 = 112.0, 202.0
    add("MP-PATH", west.intersection(rect(-60, 108, 200, sch0)))
    service("MP-SERVICE-EDU", west.intersection(rect(-60, sch0, 57, sch1)), "مدرسة متوسطة", 4800,
            rect(8, sch1 - 40, 50, sch1 - 12))
    service("MP-SERVICE-EDU", west.intersection(rect(60, sch0, 200, sch1)), "مدرسة إعدادية", 4100,
            rect(66, sch1 - 40, 104, sch1 - 12))
    add("MP-PATH", west.intersection(rect(-60, sch1, 200, sch1 + 6)))
    # towers in the north-west corner: shadow falls on the north road, no house to overlook
    tz = west.intersection(rect(-60, sch1 + 6, 200, 400))
    service("MP-TOWER-ZONE", tz, "منطقة البرجين", 25300)
    t1 = rect(-4, 250, 26, 278)
    t2 = rect(64, 238, 94, 266)
    for i, t in enumerate((t1, t2), 1):
        add("MP-TOWER", t, f"برج {i} - 20 طابق")
        add("MP-TOWER-PODIUM", t.buffer(6, join_style=2))
    add("MP-PARKING", west.intersection(rect(-60, sch1 + 14, xw(230) - 16, sch1 + 30)), "مواقف + سرداب")
    add("MP-ROAD-LOCAL", west.intersection(rect(xw(230) - 16, sch1 + 8, xw(230) + 1, 236)))
    add("MP-ROAD-LOCAL", west.intersection(rect(-60, sch1 + 8, xw(230), sch1 + 14)))

    # ================= CORE: loop, park, housing ================================================
    tail = SITE.difference(box(-100, -10, EAST0, 400))
    t0 = EAST0 + 2
    s_end = t0 + 6  # the south leg runs on into the east zone
    s_leg = rect(w_leg(S_LEG[0])[0], S_LEG[0], s_end, S_LEG[1])
    n_end = CORE_E - 18
    nw = w_leg(n_leg(140)[1])[0]
    n_leg_poly = Polygon([(nw, n_leg(nw)[0]), (n_end, n_leg(n_end)[0]), (n_end, n_leg(n_end)[1]), (nw, n_leg(nw)[1])])
    w_leg_poly = Polygon([(w_leg(S_LEG[0])[0], S_LEG[0]), (w_leg(S_LEG[0])[1], S_LEG[0]),
                          (w_leg(260)[1], 260), (w_leg(260)[0], 260)]).intersection(
        Polygon([(0, S_LEG[0]), (900, S_LEG[0]), (900, n_leg(900)[1]), (0, n_leg(0)[1])]))
    loop = unary_union([s_leg, n_leg_poly, w_leg_poly, Point(n_end, (n_leg(n_end)[0] + n_leg(n_end)[1]) / 2).buffer(13)])
    add("MP-ROAD-LOOP", loop, "الحلقة التجميعية 12 م")
    sc = (S_LEG[0] + S_LEG[1]) / 2
    add("MP-ROAD-CL", LineString([(w_leg(sc)[0] + 6, sc), (s_end, sc)]))
    add("MP-ROAD-CL", LineString([(nw + 6, n_leg(nw + 6)[0] + 6), (n_end, n_leg(n_end)[0] + 6)]))
    add("MP-ROAD-CL", LineString([(w_leg(sc)[0] + 6, sc), (w_leg(n_leg(140)[0])[0] + 6, n_leg(140)[0] + 6)]))
    add("MP-GATE", LineString([(w_leg(sc)[0], S_LEG[0]), (w_leg(sc)[0], S_LEG[1])]), "بوابة ثانوية")

    # perimeter green belt with the jogging track
    ub0 = w_leg(0)[0]
    belt_s = rect(ub0, 0, CORE_E, BELT)
    belt_n = Polygon([(nw, vn(nw) - BELT), (n_end + 30, vn(n_end + 30) - BELT),
                      (n_end + 30, vn(n_end + 30)), (nw, vn(nw))])
    add("MP-GREEN-BELT", belt_s.union(belt_n), "حزام أخضر ومسار جري")
    add("MP-JOG", LineString([(ub0, BELT / 2), (CORE_E + EAST_GREEN / 2, BELT / 2)]))
    add("MP-JOG", LineString([(nw, vn(nw) - BELT / 2), (n_end + 30, vn(n_end + 30) - BELT / 2)]))

    # outer villa rows (front on the loop, gardens on the belt)
    outer_row(w_leg(BELT)[1] + 2, CORE_E - 2, "S")
    g0, g1 = GATE_U - BLVD / 2, GATE_U + BLVD / 2
    nu0 = NU0  # first ~45 m behind the cross road stays a tree screen facing the towers
    outer_row(nu0, g0 - 14, "N")
    outer_row(g1 + 14, n_end - 14, "N")
    add("MP-GREEN", along_north(nw + LEG, nu0, 0, OUTER), "ستارة أشجار")

    # main gate + entry boulevard down to the plaza
    blvd = Polygon([(g0, vn(g0)), (g1, vn(g1)), (g1, p_n(g1)), (g0, p_n(g0))])
    add("MP-ROAD-ENTRY", blvd, "شارع الدخول 24 م")
    add("MP-WATER-CHANNEL", LineString([(GATE_U, vn(GATE_U) - 14), (GATE_U, p_n(GATE_U))]))
    add("MP-SERVICE-PUBLIC", along_north(g0 - 14, g0, 0, OUTER), "إدارة وأمن")
    add("MP-SERVICE-PUBLIC", along_north(g1, g1 + 14, 0, OUTER), "حرس البوابة")
    AREAS["إدارة وأمن البوابات"] = (2 * 14 * OUTER, 1500)
    add("MP-GATE", LineString([(g0, vn(g0) - 1), (g1, vn(g1) - 1)]), "البوابة الرئيسية")

    # plaza with waterfalls: the only place a car crosses the park
    plaza = Polygon([(PLAZA[0], p_s(PLAZA[0] + 2)), (PLAZA[1], p_s(PLAZA[1] - 2)),
                     (PLAZA[1], p_n(PLAZA[1] - 2)), (PLAZA[0], p_n(PLAZA[0] + 2))])
    add("MP-PLAZA", plaza, "ساحة الشلالات")
    add("MP-WATER", Point(GATE_U, 118).buffer(14), "شلالات")
    add("MP-WATER", rect(GATE_U - 22, 92, GATE_U + 22, 98), "قناة")
    add("MP-ROAD-ENTRY", unary_union([rect(g0, p_n(GATE_U) - 6, LINK[1], p_n(GATE_U)),
                                      rect(LINK[0], p_s(LINK[0]) - 1, LINK[1], p_n(GATE_U))]))
    add("MP-ROAD-ENTRY", rect(LINK[0], S_LEG[1], LINK[1], p_s(LINK[0])))

    # civic heart: souq flanks the boulevard, the mosque ends the entry vista, kindergarten on the park
    def nband(u0, u1):
        return Polygon([(u0, n_leg(u0)[0]), (u1, n_leg(u1)[0]), (u1, p_n(u1)), (u0, p_n(u0))])
    souq_w, souq_e = nband(390, g0), nband(g1, g1 + 44)
    service("MP-SERVICE-COMM", souq_w.union(souq_e), "سوق ومقاهٍ ومطاعم", 3500)
    add("MP-BLDG-SERVICE", souq_w.buffer(-5, join_style=2))
    add("MP-BLDG-SERVICE", souq_e.buffer(-5, join_style=2))
    msq = rect(GATE_U - 18, S_LEG[1], GATE_U + 18, PLAZA_V[0])
    service("MP-SERVICE-MOSQUE", msq, "جامع", 1500, rect(GATE_U - 13, PLAZA_V[0] - 32, GATE_U + 13, PLAZA_V[0] - 6))
    add("MP-SERVICE-MOSQUE", Point(GATE_U + 10, PLAZA_V[0] - 3).buffer(2.5))
    kg = Polygon([(354, S_LEG[1]), (GATE_U - 20, S_LEG[1]), (GATE_U - 20, p_s(GATE_U - 20)), (PLAZA[0] - 2, p_s(PLAZA[0] - 2)),
                  (PLAZA[0] - 2.01, p_s(PLAZA[0] - 2.01)), (354, p_s(354))])
    service("MP-SERVICE-EDU", kg, "روضة", 3600, rect(362, S_LEG[1] + 8, 400, S_LEG[1] + 30))
    club_u1 = g1 + 44

    # ---- housing on cul-de-sacs ----
    nu = max(w_leg(v)[1] for v in (p_n(150), n_leg(150)[0])) + 3
    su = w_leg(p_s(170))[1] + 3
    for key, u0, band in (("NW", nu, "N"), ("SW", su, "S"), ("SE", LINK[1], "S"), ("NE", club_u1, "N")):
        c0 = dict(COUNT)
        run(SEQ[key], u0, band)
        BANDS[key] = {k: COUNT[k] - c0[k] for k in COUNT}

    # ================= EAST ZONE ===================================================================
    eg = SITE.intersection(rect(CORE_E, 0, EAST0, 400)).difference(s_leg)
    add("MP-GREEN", eg, "ممر أخضر")
    add("MP-JOG", LineString([(CORE_E + EAST_GREEN / 2, BELT / 2), (CORE_E + EAST_GREEN / 2, vn(CORE_E) - BELT / 2)]))
    # utilities in the low south-east corner, own service gate on the south road
    service("MP-SERVICE-UTIL", tail.intersection(rect(t0 + 8, 0, t0 + 56, 56)), "تحلية ومعالجة مياه", 2500,
            rect(t0 + 14, 12, t0 + 50, 42))
    service("MP-SERVICE-UTIL", tail.intersection(rect(t0 + 58, 0, t0 + 102, 56)), "محطة كهرباء 33/11", 2500,
            rect(t0 + 66, 12, t0 + 94, 42))
    service("MP-SERVICE-UTIL", tail.intersection(rect(t0 + 104, 0, 900, 56)), "مجاري وخزن أمطار", 1500)
    add("MP-GATE", LineString([(t0 + 50, 0.5), (t0 + 62, 0.5)]), "بوابة خدمة")
    # primary school and the social club at the east end of the park
    sch = tail.intersection(rect(0, 64, 900, 120))
    service("MP-SERVICE-EDU", sch, "مدرسة ابتدائية", 7700, rect(t0 + 30, 88, t0 + 96, 114))
    add("MP-ROAD-LOCAL", tail.intersection(rect(t0 - 4, 56, 900, 64)))
    add("MP-ROAD-LOCAL", tail.intersection(rect(t0 - 4, S_LEG[0], t0 + 6, 124)))
    club = tail.intersection(rect(t0 + 4, 120, 900, 400))
    service("MP-SERVICE-COMM", club, "النادي الاجتماعي", 4000, rect(t0 + 50, 128, t0 + 100, 150))
    add("MP-WATER", rect(t0 + 30, 152, t0 + 60, 164), "مسبح")
    add("MP-PARK", tail.difference(rect(0, 0, 900, 400)), "")

    # ---- the park = everything left inside the core ----
    core = Polygon([(w_leg(S_LEG[1])[1], S_LEG[1]), (CORE_E, S_LEG[1]), (CORE_E, n_leg(CORE_E)[0]),
                    (w_leg(n_leg(140)[0])[1], n_leg(w_leg(200)[1])[0])]).intersection(SITE)
    taken = unary_union([g for lay, g, _ in F if not isinstance(g, LineString)
                         and lay not in ("MP-BOUNDARY", "MP-WATER", "MP-PLAZA") and g.area > 0])
    park = core.difference(taken).buffer(-0.01).buffer(0.01)
    park = unary_union([g for g in getattr(park, "geoms", [park]) if g.area > 400])
    add("MP-PARK", park, "الحديقة المتصلة")
    # stream along the park, cascading at the plaza, ending in a rain pond
    pond_c = (CORE_E - 34, (p_s(CORE_E - 34) + p_n(CORE_E - 34)) / 2)
    add("MP-WATER", Polygon([(pond_c[0] + 24 * math.cos(a), pond_c[1] + 13 * math.sin(a) + 3 * math.sin(3 * a))
                              for a in np.linspace(0, 2 * math.pi, 40)]), "بحيرة تجميع الأمطار")
    us = np.arange(170, pond_c[0] - 20, 8)
    add("MP-WATER-CHANNEL", LineString([(u, (p_s(u) + p_n(u)) / 2 + 4 * math.sin(u / 30)) for u in us]))
    for edge in (p_s, p_n):
        sgn = 6 if edge is p_s else -6
        for seg in ((172, PLAZA[0] - 4), (PLAZA[1] + 4, pond_c[0] - 30)):
            add("MP-PATH-PARK", LineString([(u, edge(u) + sgn) for u in np.arange(seg[0], seg[1], 6)]))
    for t in TREES:
        add("MP-TREES-EXIST", Point(t).buffer(4), "شجرة قائمة")
    return F


if __name__ == "__main__":
    build()
    print(COUNT)
    for k, (a, p) in AREAS.items():
        print(f"{k:35s} {a:9.0f} {p}")
