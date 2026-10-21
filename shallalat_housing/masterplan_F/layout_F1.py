"""Layout of master plan proposal F, revision 1 (new program, no club), "towers in the heart" (الأبراج في القلب) for plot 157 / district 53 Baybokht.

Rev 1 program (client, 2026-10-21): 80 villas 400 m2, 88 houses 240 m2, 3 towers x 20 floors = 240 flats on a
plaza over a basement car park (360 cars); health 1000, police 600, civil defence 600, primary 3000, secondary
5000, water 1000, power 1000, mall 3000, kindergarten 1500, mosque 2000, waste 300; no club; leftover land is green.

Driver: the towers stand in the middle of the site inside a central park ringed by a 14 m loop road,
with the main gate on the north road on the towers' axis. The community services (mosque, souq, club,
kindergarten) fill the four corners around the ring. From the ring a tree-lined spine runs west to the
cross road and east to the utilities. Off the spine, every group of houses wraps a U-shaped lane around
its own green court, so each house fronts a garden. The western part beyond the cross road is the
public front (schools, police, civil defence, health). The watercourse is ignored at the client's request.

Geometry is in the local frame of make_masterplan_D.py: u along the south edge Q1->Q4, v towards
the north edge, written to the DXF in UTM 38S on the net 199,175 m2 boundary.
"""
import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

# --- site --------------------------------------------------------------------------------------------
P = [(338954.0, 4035462.0), (339032.0, 4035771.0), (339836.0, 4035336.0), (339747.0, 4035198.0)]
Q = [(338955.19, 4035466.71), (339030.78, 4035766.16), (339833.37, 4035331.92), (339749.71, 4035202.20)]
PIX = np.array([(259.3, 156), (468.3, 119.3), (395, 731.7), (290, 712.3)])
AFF = np.linalg.lstsq(np.c_[PIX, np.ones(4)], np.array(P), rcond=None)[0]
O = np.array(Q[0])
U = np.subtract(Q[3], Q[0]) / np.linalg.norm(np.subtract(Q[3], Q[0]))
V = np.array([-U[1], U[0]])


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


def north_v(u):
    return NW[1] + (u - NW[0]) * (NE[1] - NW[1]) / (NE[0] - NW[0])


def band(a, b, half, ext=0.0):
    ln = LineString([a, b])
    if ext:
        d = np.subtract(b, a) / ln.length
        ln = LineString([tuple(np.subtract(a, d * ext)), tuple(np.add(b, d * ext))])
    return ln.buffer(half, cap_style="flat")


def polys(g):
    if g is None or g.is_empty:
        return []
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 0.5]


def ellipse(c, a, b):
    return affinity.scale(Point(c).buffer(1.0, quad_segs=32), a, b)


# --- context: cross road (public), trees ---------------------------------------------------------------
CROSS_A, CROSS_B = scan(267, 251), scan(455, 214)
CROSS = band(CROSS_A, CROSS_B, 5.0, ext=40).intersection(SITE_RAW)
CROSS_IN = SITE.intersection(CROSS)
TREES = [scan(x, y) for x, y in [(310, 170), (355, 165), (395, 178), (300, 196), (343, 194), (385, 205), (420, 190)]]
cross_dir = np.subtract(CROSS_B, CROSS_A) / math.dist(CROSS_A, CROSS_B)
cross_n = np.array([cross_dir[1], -cross_dir[0]])
if cross_n[0] < 0:
    cross_n = -cross_n


def east_of_cross(off):
    a = np.add(CROSS_A, cross_n * off)
    big = 3000
    pts = [a - cross_dir * big, a + cross_dir * big, a + cross_dir * big + cross_n * big, a - cross_dir * big + cross_n * big]
    return Polygon([tuple(p) for p in pts])


def u_cross(v):
    """u of the cross road centre line at v."""
    t = (v - CROSS_A[1]) / (CROSS_B[1] - CROSS_A[1])
    return CROSS_A[0] + t * (CROSS_B[0] - CROSS_A[0])


WEST = SITE.difference(east_of_cross(5.0))
REST = SITE.intersection(east_of_cross(5.0))
BELT = 4.0                                   # planted belt inside the compound wall
R_IN = REST.buffer(-BELT, join_style="mitre")

# --- the heart: ring road, central park, towers -------------------------------------------------------
HC = (430.0, 114.0)                           # centre of the ring = the towers' axis
RING_A, RING_B, RING_W = 88.0, 78.0, 14.0     # centre-line semi axes, carriageway + kerbs
ARC_D, ARC_F, ARC_VERGE = 20.0, 12.0, 2.0      # houses round the ring: depth, mean frontage, front verge
RING_OUT = ellipse(HC, RING_A + RING_W / 2, RING_B + RING_W / 2)
RING_INN = ellipse(HC, RING_A - RING_W / 2, RING_B - RING_W / 2)
RING = RING_OUT.difference(RING_INN)
PARK = RING_INN.buffer(-2.0)                  # central park «حديقة الشلالات» inside the ring

TW = 28.3                                     # 800 m2 floor plate, 4 corner flats per floor
T_CENTRES = [(HC[0] - 62, HC[1] - 5), (HC[0], HC[1] + 30), (HC[0] + 62, HC[1] - 5)]   # an arc facing the gate
TOWERS = [box(x - TW / 2, y - TW / 2, x + TW / 2, y + TW / 2) for x, y in T_CENTRES]
TOWER_GAP = min(TOWERS[i].distance(TOWERS[j]) for i in range(3) for j in range(i + 1, 3))
PODIUM = unary_union(TOWERS).convex_hull.buffer(4, join_style="mitre")   # plaza over the basement car park
PARK_CARS = 360
BASEMENT_LEVELS = math.ceil(PARK_CARS * 30.0 / PODIUM.area)               # ~30 m2 gross per car
T_PLAZA = PODIUM
T_DROP = band((HC[0], HC[1] + RING_B - RING_W / 2), (HC[0], 172.0), 4.0).union(
    Point((HC[0], 172.0 - 4)).buffer(9)).intersection(RING_INN)
LAKE = ellipse((HC[0], HC[1] - 47), 40, 13)    # lake fed by cascades «الشلالات»
CASCADE = box(HC[0] - 12, HC[1] - 33, HC[0] + 12, HC[1] - 26)
PATHS = [LineString([(HC[0] - 78, HC[1] - 28), (HC[0] - 44, HC[1] - 32), (HC[0] - 30, HC[1] - 46)]),
         LineString([(HC[0] + 78, HC[1] - 28), (HC[0] + 44, HC[1] - 32), (HC[0] + 30, HC[1] - 46)]),
         LineString([(HC[0], HC[1] - 74), (HC[0], HC[1] - 60)])]

# gates (kept to the minimum at the client's request): one main gate on the north road on the towers'
# axis; one service / emergency gate at the east tip for the utilities. No gate to the cross road or the south road.
GATE_W, GATE_D = 30.0, 18.0
GV = north_v(HC[0])
FORECOURT = box(HC[0] - GATE_W / 2, GV - BELT - GATE_D, HC[0] + GATE_W / 2, GV + 2).intersection(SITE)
BLVD = box(HC[0] - 12, HC[1] + RING_B, HC[0] + 12, GV - BELT - GATE_D + 0.5)
GATE_LINE = LineString([(HC[0] - GATE_W / 2, GV - BELT - GATE_D + 6), (HC[0] + GATE_W / 2, GV - BELT - GATE_D + 6)])
GUARD = box(HC[0] + 4, GV - BELT - GATE_D + 8, HC[0] + 12, GV - BELT - 3)
GUARD_ISL = box(HC[0] - 2, GV - BELT - GATE_D + 8, HC[0] + 2, GV - BELT - 3)

# --- spine ---------------------------------------------------------------------------------------------
SP_W = 16.0       # 10 m carriageway + 2 x 3 m tree-lined walks
SPINES = {
    "W": ((u_cross(136.0) + 16.0, 136.0), (HC[0] - RING_A, HC[1])),
    "E": ((HC[0] + RING_A, HC[1]), (812.0, 80.0)),
}


class Frame:
    def __init__(self, a, b):
        self.a = np.array(a, float)
        self.d = (np.subtract(b, a)) / math.dist(a, b)
        self.n = np.array([-self.d[1], self.d[0]])   # +n = north side
        self.L = math.dist(a, b)

    def p(self, t, n):
        return tuple(self.a + self.d * t + self.n * n)

    def rect(self, t0, t1, n0, n1):
        return Polygon([self.p(t0, n0), self.p(t1, n0), self.p(t1, n1), self.p(t0, n1)])

    def tn(self, q):
        r = np.subtract(q, self.a)
        return float(r @ self.d), float(r @ self.n)


FR = {k: Frame(*v) for k, v in SPINES.items()}
SPINE = unary_union([band(*v, SP_W / 2) for v in SPINES.values()])
E_END = Point(SPINES["E"][1]).buffer(13)         # turning circle at the east end
W_END = Point(FR["W"].p(20, 0)).buffer(13)      # turning circle at the west end, wall towards the cross road

# --- utilities at the east tip -------------------------------------------------------------------------
UTIL_U = 822.0
UTIL = R_IN.intersection(box(UTIL_U, -100, 2000, 500))
U_GATE = LineString([(UTIL_U + 6, 0.5), (UTIL_U + 18, 0.5)])   # service / emergency gate on the south road

# --- houses round the ring: one row of 240 m2 plots fronting the ring road and the park ---------------
HEART_X = RING_OUT.buffer(ARC_VERGE + ARC_D + 3.0)       # kept clear of the court blocks
_arc_free = R_IN.difference(SPINE.buffer(3)).difference(BLVD.buffer(3)).difference(FORECOURT.buffer(3))


def _ell(a, b, th):
    return (HC[0] + a * math.cos(th), HC[1] + b * math.sin(th))


def _arc_plots():
    a0, b0 = RING_A + RING_W / 2 + ARC_VERGE, RING_B + RING_W / 2 + ARC_VERGE
    am, bm = a0 + ARC_D / 2, b0 + ARC_D / 2
    ths = np.linspace(0, 2 * math.pi, 4001)
    pts = np.array([_ell(am, bm, t) for t in ths])
    cum = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    out, specs, s0 = [], [], 0.0
    while s0 + ARC_F <= cum[-1]:
        t1, t2 = np.interp([s0, s0 + ARC_F], cum, ths)
        tt = np.linspace(t1, t2, 6)
        g = Polygon([_ell(a0, b0, t) for t in tt] + [_ell(a0 + ARC_D, b0 + ARC_D, t) for t in tt[::-1]])
        if _arc_free.buffer(0.01).contains(g):
            out.append(g); specs.append((t1, t2))
            s0 += ARC_F
        else:
            s0 += 1.0
    return out, specs


ARC, ARC_SPECS = _arc_plots()


def arc_footprint(t1, t2):   # 120 m2 class footprint: 2.5 m front setback, 12 m deep, attached
    a0, b0 = RING_A + RING_W / 2 + ARC_VERGE + 2.5, RING_B + RING_W / 2 + ARC_VERGE + 2.5
    tt = np.linspace(t1, t2, 6)
    return Polygon([_ell(a0, b0, t) for t in tt] + [_ell(a0 + 12, b0 + 12, t) for t in tt[::-1]])


# --- housing: U-lanes wrapped around green courts ----------------------------------------------------
LANE = 7.0        # shared-surface lane, one way round the court
VERGE = 3.0       # planted strip between the spine and the first plots
TYPES = {"V": (16.0, 25.0), "H": (12.0, 20.0)}     # frontage x depth -> 400 / 240 m2
MIN_GREEN = 16.0


def fits(g, region):
    return region.buffer(0.01).contains(g)


def make_block(fr, t0, side, kind, region, G):
    """One court block: two rows of plots facing a U lane, the green court between them and, where the
    land is deep enough, a back row of plots behind the far lane. Each plot is checked against the land."""
    f, d = TYPES[kind]
    B = 2 * d + 2 * LANE + G
    n0 = SP_W / 2 + VERGE
    s = 1 if side == "N" else -1

    def R(ta, tb, na, nb):
        return fr.rect(ta, tb, s * na, s * nb)

    if not fits(R(t0 + d, t0 + B - d, n0, n0 + 2 * f), region):
        return None
    lo, hi = n0, 300.0
    for _ in range(40):          # depth of the lanes + court core
        m = (lo + hi) / 2
        lo, hi = (m, hi) if fits(R(t0 + d, t0 + B - d, n0, m), region) else (lo, m)
    n_core = lo

    def option(back):
        n_lane = n_core - LANE - (d if back else 0)
        if n_lane - n0 < MIN_GREEN:
            return None
        side_end = n_lane + LANE
        row_end = n_lane if back else side_end   # with a back row the far lane runs the full block width
        plots, specs = [], []
        for ta, tb, fr_ in ((t0, t0 + d, "t+"), (t0 + B - d, t0 + B, "t-")):
            i = 0
            while n0 + (i + 1) * f <= row_end + 0.01:
                na, nb = n0 + i * f, n0 + (i + 1) * f
                g = R(ta, tb, na, nb)
                if not fits(g, region):
                    break
                plots.append(g); specs.append((ta, tb, na, nb, fr_))
                i += 1
        if back:
            kb = int(B // f)
            off = (B - kb * f) / 2
            for i in range(kb):
                ta = t0 + off + i * f
                g = R(ta, ta + f, side_end, side_end + d)
                if fits(g, region):
                    plots.append(g); specs.append((ta, ta + f, side_end, side_end + d, "n-"))
        lane = unary_union([R(t0 + d, t0 + d + LANE, n0 - VERGE - 0.5, side_end),
                            R(t0 + B - d - LANE, t0 + B - d, n0 - VERGE - 0.5, side_end),
                            R(t0 if back else t0 + d, t0 + B if back else t0 + B - d, n_lane, side_end)])
        court = R(t0 + d + LANE, t0 + B - d - LANE, n0, n_lane)
        strip = unary_union([R(t0 + d, t0 + B - d, n0 - VERGE, side_end), lane] + plots)
        return dict(kind=kind, side=side, t0=t0, B=B, G=G, plots=plots, specs=specs, lane=lane, court=court,
                    strip=strip, n0=n0, n_max=side_end + (d if back else 0), s=s, fr=fr, back=back)

    opts = [o for o in (option(False), option(True)) if o]
    if not opts:
        return None
    return max(opts, key=lambda o: len(o["plots"]) * (400 if kind == "V" else 200))


def region_for(key):
    r = R_IN.difference(HEART_X).difference(BLVD.buffer(3)).difference(FORECOURT.buffer(3)) \
        .difference(UTIL.buffer(6)).difference(SPINE.buffer(0.2))
    return r


def pack(key, side, seq, G, fill=None):
    """Blocks one after the other along the spine; each block slides up to 30 m to find its best spot
    (most plot area per metre of spine used). Then the rest of the wing is filled with `fill` blocks."""
    fr = FR[key]
    region = region_for(key)
    out, t = [], 0.0
    kinds = list(seq)
    while t < fr.L:
        kind = kinds.pop(0) if kinds else fill
        if kind is None:
            break
        best = None
        for dt in range(0, 31):
            b = make_block(fr, t + dt, side, kind, region, G[kind])
            if b:
                score = len(b["plots"]) * TYPES[kind][0] * TYPES[kind][1] / (dt + b["B"])
                if best is None or score > best[0]:
                    best = (score, b, dt)
        if best is None:
            t += 10.0
            if not kinds and t > fr.L:
                break
            continue
        out.append(best[1])
        t += best[2] + best[1]["B"]
    return out


# west wing and the south side of the east wing: villas; north side of the east wing + the ring: houses
G = {"V": 18.0, "H": 18.0}
PLAN = {
    ("W", "N"): ("", "V"),
    ("W", "S"): ("", "V"),
    ("E", "N"): ("", "H"),
    ("E", "S"): ("", "V"),
}
N_VILLAS, N_HOUSES = 80, 88
BLOCKS = []
for (key, side), (seq, fill) in PLAN.items():
    BLOCKS += pack(key, side, seq, G, fill)


def trim(kind, n_keep):
    """Drop surplus plots (the far end of the longest rows first); the land joins the court gardens."""
    extra = sum(len(b["plots"]) for b in BLOCKS if b["kind"] == kind) - n_keep
    while extra > 0:
        b = max((b for b in BLOCKS if b["kind"] == kind), key=lambda b: len(b["plots"]))
        i = max(range(len(b["specs"])), key=lambda i: (b["specs"][i][4] == "n-", b["specs"][i][3]))
        b["plots"].pop(i); b["specs"].pop(i)
        extra -= 1


trim("V", N_VILLAS)
_h_blocks = sum(len(b["plots"]) for b in BLOCKS if b["kind"] == "H")
_n_arc = max(0, N_HOUSES - _h_blocks)
if _n_arc < len(ARC):   # keep the ring houses nearest the gate axis, the rest become garden
    order = sorted(range(len(ARC)), key=lambda i: abs(ARC[i].centroid.x - HC[0]))[:_n_arc]
    order.sort()
    ARC = [ARC[i] for i in order]
    ARC_SPECS = [ARC_SPECS[i] for i in order]
trim("H", N_HOUSES - len(ARC))
for i, b in enumerate(BLOCKS):
    b["name"] = f"{'V' if b['kind'] == 'V' else 'H'}{i + 1:02d}"

VILLAS = [p for b in BLOCKS if b["kind"] == "V" for p in b["plots"]]
HOUSES = [p for b in BLOCKS if b["kind"] == "H" for p in b["plots"]] + ARC
N_APTS = 3 * 20 * 4

# --- public front west of the cross road (same zoning as proposal D) ------------------------------------
W_IN = WEST.buffer(-3, join_style="mitre")
PUB = {   # exact program areas, laid out west of the cross road (public, reached from the outer roads)
    "PRIMARY": box(2, 3, 62, 53),               # 3,000
    "SECONDARY": box(2, 58, 72, 58 + 5000 / 70),  # 5,000 intermediate + preparatory
    "MALL": box(2, 135, 62, 185),               # 3,000
    "HEALTH": box(80, 128, 120, 153),           # 1,000
    "MOSQUE": box(68, 160, 115, 160 + 2000 / 47),  # 2,000
    "KG": box(2, 192, 52, 222),                 # 1,500
    "POWER": box(68, 210, 108, 235),            # 1,000 (33/11 kV)
    "POLICE": box(0, 268, 24, 293),             # 600
    "CIVIL_DEF": box(30, 262, 54, 287),         # 600
}
MALL_PARK = box(2, 3, 62, 3).union(box(78, 3, 122, 120)).intersection(W_IN)   # mall / school / mosque car park
MALL_PARK = box(78, 3, 120, 60).intersection(W_IN)
PUB = {k: v.intersection(W_IN) for k, v in PUB.items()}
ORCHARD = W_IN.difference(unary_union(list(PUB.values()) + [MALL_PARK]).buffer(3))
ORCHARD = max(polys(ORCHARD), key=lambda g: g.area)

UTIL_ITEMS = {}
_ub = UTIL.bounds
UTIL_ITEMS["WATER"] = box(UTIL_U + 6, 46, UTIL_U + 6 + 40, 71).intersection(UTIL)
UTIL_ITEMS["WASTE"] = box(UTIL_U + 30, 10, UTIL_U + 50, 25).intersection(UTIL)
SERV = {}

# leftovers inside the compound: shared gardens and pocket parks
_used = unary_union([b["strip"] for b in BLOCKS] + [SPINE, E_END, W_END, RING_OUT, BLVD, FORECOURT, UTIL] + ARC)
GARDENS = [g for g in polys(R_IN.difference(_used.buffer(0.3))) if g.area > 120]


def total(gs):
    return sum(g.area for g in gs)


ROADS = unary_union([SPINE, E_END, W_END, RING, BLVD, FORECOURT]).intersection(REST)
LANES = unary_union([b["lane"] for b in BLOCKS])
COURTS = [b["court"] for b in BLOCKS]
LANDUSE = [
    ("Villa plots 400 m2 - قطع الفلل", len(VILLAS) * 400.0),
    ("House plots 240 m2 - قطع الدور", total(HOUSES)),
    ("Tower plaza over basement - ساحة الأبراج فوق السرداب", PODIUM.area),
    ("Public services - الخدمات العامة", total(PUB.values())),
    ("Utilities (water, waste) - المرافق (ماء، نفايات)", total(UTIL_ITEMS.values())),
    ("Ring, spine, gates, parking - الحلقة والمحور والبوابات والمواقف", ROADS.area + MALL_PARK.area),
    ("Court lanes - أزقة البلوكات", LANES.area),
    ("Cross road (public) - الشارع العرضي", CROSS_IN.area),
    ("Green: park, courts, gardens, belts - المساحات الخضراء", 0.0),
]
LANDUSE[-1] = (LANDUSE[-1][0], SITE.area - sum(a for _, a in LANDUSE))
GREEN_M2 = LANDUSE[-1][1]
ROADS_M2 = ROADS.area + MALL_PARK.area + LANES.area + CROSS_IN.area

if __name__ == "__main__":
    print(f"site {SITE.area:,.0f}  west {WEST.area:,.0f}  park {RING_INN.area:,.0f}  util {UTIL.area:,.0f}  arc {len(ARC)}"
          f"  podium {PODIUM.area:,.0f} x{BASEMENT_LEVELS}")
    for b in BLOCKS:
        print(b["name"], b["kind"], b["side"], f"t0={b['t0']:.0f} B={b['B']:.0f} depth={b['n_max'] - b['n0']:.0f} back={b['back']}",
              len(b["plots"]), f"court {b['court'].area:.0f}")
    print("villas", len(VILLAS), "houses", len(HOUSES), "units", len(VILLAS) + len(HOUSES) + N_APTS)
    for k, v in {**PUB, **UTIL_ITEMS}.items():
        print(f"{k:12s} {v.area:8,.0f}")
    for n, a in LANDUSE:
        print(f"{n:55s} {a:9,.0f} {a / SITE.area * 100:5.1f}")
    print("tower gap", TOWER_GAP, "green %", GREEN_M2 / SITE.area * 100, "roads %", ROADS_M2 / SITE.area * 100)
