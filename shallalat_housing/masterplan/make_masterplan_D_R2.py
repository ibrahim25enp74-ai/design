"""Master plan, proposal D "secure clusters" - REVISION 2 (client program of 21 Oct 2026:
80 villas 400 m2, 88 houses 240 m2, 3 towers x 20 floors on a plaza with basement parking, service
areas as set by the client, everything left over is green; two gates only, both on the long sides).

Proposal D (التجمعات الآمنة) for plot 157 / district 53 Baybokht.

Driver: privacy and security. The cross road stays public; the western part is a public front
(police, civil defence, schools, Friday mosque, open orchard park). One main gate on the north road
at about chainage 300 m with an inspection forecourt leads to a single distributor street. Off the
distributor, gated cul-de-sac clusters (each lane <= 120 m) end in a green court. The service centre
sits midway along the distributor, inside the main gate but outside the clusters. The two towers
stand in a separate eastern zone with their own entrance. The watercourse on the cadastral scan is
ignored at the client's request.

Geometry is laid out in a local frame (u along the south edge Q1->Q4, v across, towards the north
edge) and written to the DXF in UTM 38S, on the same net boundary as SHALLALAT_SITE_PLAN.dxf.
"""
import math
import os
import sys

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))

# --- site (same numbers as site/make_site_dxf.py) ----------------------------------------------------
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
    """v of the north edge at chainage u."""
    return NW[1] + (u - NW[0]) * (NE[1] - NW[1]) / (NE[0] - NW[0])


def band(a, b, half, ext=0.0):
    ln = LineString([a, b])
    if ext:
        d = np.subtract(b, a) / ln.length
        ln = LineString([tuple(np.subtract(a, d * ext)), tuple(np.add(b, d * ext))])
    return ln.buffer(half, cap_style="flat")



# --- context ------------------------------------------------------------------------------------------
CROSS_A, CROSS_B = scan(267, 251), scan(455, 214)
CROSS = band(CROSS_A, CROSS_B, 5.0, ext=40).intersection(SITE_RAW)
# the watercourse on the cadastral scan is ignored at the client's request: the land is continuous
TOWER_ZONE_M2 = 20000.0  # 3 towers on a plaza (basement parking) inside their own garden
TREES = [scan(x, y) for x, y in [(310, 170), (355, 165), (395, 178), (300, 196), (343, 194), (385, 205), (420, 190)]]

cross_dir = np.subtract(CROSS_B, CROSS_A) / math.dist(CROSS_A, CROSS_B)
cross_n = np.array([cross_dir[1], -cross_dir[0]])
if cross_n[0] < 0:
    cross_n = -cross_n  # points east


def east_of_cross(off):
    a = np.add(CROSS_A, cross_n * off)
    big = 3000
    pts = [a - cross_dir * big, a + cross_dir * big, a + cross_dir * big + cross_n * big, a - cross_dir * big + cross_n * big]
    return Polygon([tuple(p) for p in pts])


WEST = SITE.difference(east_of_cross(5.0))             # public front
CROSS_IN = SITE.intersection(CROSS)
REST = SITE.intersection(east_of_cross(5.0))
_lo, _hi = 500.0, 870.0
for _ in range(60):  # straight split across the plot so the eastern tower zone gets its program area
    U_SPLIT = (_lo + _hi) / 2
    _lo, _hi = (U_SPLIT, _hi) if REST.intersection(box(U_SPLIT, -50, 2000, 500)).area > TOWER_ZONE_M2 else (_lo, U_SPLIT)
GATED = REST.intersection(box(-2000, -50, U_SPLIT, 500))
ISLAND = REST.intersection(box(U_SPLIT, -50, 2000, 500))

BELT = 4.0  # planted belt inside the compound wall
G_IN = GATED.buffer(-BELT, join_style="mitre")

# --- distributor street ---------------------------------------------------------------------------
SP_W = 18.0          # 2 x 6.5 m carriageway + 2.5 m tree-lined walks
U_W, U_E = 176.0, U_SPLIT - 4.0 - 26.0
SA, SB = (U_W, north_v(U_W) / 2), (U_E, north_v(U_E) / 2)
S_DIR = np.subtract(SB, SA) / math.dist(SA, SB)
S_N = np.array([-S_DIR[1], S_DIR[0]])
S_LEN = math.dist(SA, SB)
TURN_R = 14.0


def sp(t, n):
    """Point at station t along the distributor, offset n to its north."""
    return tuple(np.add(SA, S_DIR * t + S_N * n))


def strip_poly(t0, t1, n0, n1):
    return Polygon([sp(t0, n0), sp(t1, n0), sp(t1, n1), sp(t0, n1)])


SPINE = unary_union([band(SA, SB, SP_W / 2), Point(SA).buffer(TURN_R), Point(SB).buffer(TURN_R)])

# --- main gate: north road, ~300 m from the NW corner, inspection forecourt outside the gate line ---
T_GATE = 100.0
GATE_U = sp(T_GATE, 0)[0]
BLV_W = 24.0
FORE_D, FORE_W = 42.0, 64.0
GATE_V = north_v(GATE_U) - FORE_D
BOULEVARD = band(sp(T_GATE, 0), (GATE_U, north_v(GATE_U) + 2), BLV_W / 2).intersection(GATED)
ROUNDABOUT = Point(sp(T_GATE, 0)).buffer(19)
RB_ISLAND = Point(sp(T_GATE, 0)).buffer(9)
FORECOURT = Polygon([(GATE_U - FORE_W / 2, north_v(GATE_U - FORE_W / 2) + 1), (GATE_U + FORE_W / 2, north_v(GATE_U + FORE_W / 2) + 1),
                     (GATE_U + FORE_W / 2, GATE_V), (GATE_U - FORE_W / 2, GATE_V)]).intersection(GATED)
GATE_LINE = LineString([(GATE_U - FORE_W / 2, GATE_V), (GATE_U + FORE_W / 2, GATE_V)])
INSPECT = [box(GATE_U + o - 2.5, GATE_V + 6, GATE_U + o + 2.5, GATE_V + 26) for o in (-9, 0, 9)]   # lane islands / canopies
GUARD = box(GATE_U - FORE_W / 2 + 2, GATE_V + 2, GATE_U - FORE_W / 2 + 14, GATE_V + 12)
VISITOR_P = box(GATE_U + 16, GATE_V + 4, GATE_U + FORE_W / 2 - 2, north_v(GATE_U + FORE_W / 2) - 4)

# --- service centre: midway on the distributor, inside the gate, outside the clusters ----------------
SC_N_T = (T_GATE + BLV_W / 2 + 4, T_GATE + 100.0)
SC_S_T = (88.0, 118.0)
SC_N = strip_poly(*SC_N_T, SP_W / 2, 400).intersection(G_IN).difference(FORECOURT.buffer(4))
SC_S = strip_poly(*SC_S_T, -400, -SP_W / 2).intersection(G_IN)
_split = SP_W / 2 + 36
SC_ITEMS = {
    "MALL": SC_N.intersection(strip_poly(*SC_N_T, 0, _split)),
    "ADMIN": SC_N.intersection(strip_poly(SC_N_T[0], SC_N_T[0] + 12, _split + 4, _split + 40)),
    "KG": SC_S.intersection(strip_poly(*SC_S_T, -SP_W / 2 - 58, -SP_W / 2 - 4)),
}
SC_PLAZA = SC_S.intersection(strip_poly(*SC_S_T, -SP_W / 2 - 4, 0))

# --- clusters -------------------------------------------------------------------------------------
LANE = 8.0          # shared-surface cul-de-sac; facing houses >= 13 m apart with setbacks
FRONT = 4.0         # planted strip + cluster wall along the distributor
MAX_LANE = 120.0
COURT_MIN = float(os.environ.get("COURT", 600))  # m2 of green court at the closed end, at least   # m2 of green court at the closed end, at least
TYPES = {"V": (16.0, 25.0), "H": (12.0, 20.0)}  # frontage x depth -> 400 / 240 m2


def make_cluster(t0, side, kind, region, W=None):
    w, d = TYPES[kind]
    W = W or 2 * d + LANE
    sg = 1 if side == "N" else -1
    n_in = SP_W / 2 + FRONT
    strip = strip_poly(t0, t0 + W, sg * (SP_W / 2), sg * 400).intersection(region)
    sb = strip.buffer(0.01)
    rows = [(t0, t0 + d), (t0 + W - d, t0 + W)]
    lane_t = (t0 + d, t0 + W - d)
    rp = []
    for r0, r1 in rows:
        ps = []
        for k in range(30):
            a, b = n_in + k * w, n_in + (k + 1) * w
            if b - SP_W / 2 > MAX_LANE - 10:
                break
            p = strip_poly(r0, r1, sg * a, sg * b)
            if not sb.contains(p):
                break
            ps.append((p, (r0, r1, a, b, sg, "hi" if r1 <= lane_t[0] + 0.01 else "lo")))
        rp.append(ps)
    while True:
        end = n_in + max(len(r) for r in rp) * w
        lane = strip_poly(*lane_t, sg * (SP_W / 2), sg * end).intersection(strip)
        head = Point(sp((lane_t[0] + lane_t[1]) / 2, sg * (end + 7))).buffer(7).intersection(strip)
        plots = [p for p, _ in rp[0] + rp[1]]
        specs = [q for _, q in rp[0] + rp[1]]
        front = strip.intersection(strip_poly(t0, t0 + W, sg * (SP_W / 2), sg * n_in)).difference(lane)
        court = strip.difference(unary_union(plots + [lane, front]).buffer(0.01))
        court = unary_union([g for g in getattr(court, "geoms", [court]) if g.area > 30]) if not court.is_empty else court
        if court.area >= COURT_MIN or not plots:
            break
        longest = max(rp, key=len)
        longest.pop()
    return dict(kind=kind, side=side, t0=t0, W=W, plots=plots, specs=specs, lane=lane, head=head, court=court, front=front,
                strip=strip, lane_len=end + 14 - SP_W / 2,
                gate=(sp(lane_t[0], sg * (n_in - 0.5)), sp(lane_t[1], sg * (n_in - 0.5))),
                kiosk=strip_poly(lane_t[1] + 0.5, lane_t[1] + 3.5, sg * (n_in + 0.5), sg * (n_in + 3.5)))


CL_N = G_IN.difference(SC_N.buffer(0.5)).difference(BOULEVARD.buffer(4)).difference(FORECOURT.buffer(6)).difference(ROUNDABOUT.buffer(2))
CL_S = G_IN.difference(SC_S.buffer(0.5))


# villas on the deep west wing and at the east end, houses near the centre; every plot beyond the
# program is given back to the cluster courts (see trim below)
PLAN_N, PLAN_S = os.environ.get("PLAN", "VVVHHV,HHVVVH").split(",")
TARGET = {"V": 80, "H": 88}


def pack(side, t_start, kinds):
    out, t = [], t_start
    reg = CL_N if side == "N" else CL_S
    for k in kinds:
        c = make_cluster(t, side, k, reg)
        out.append(c)
        t += c["W"]
    return out


# villas on the deep west wing and at the east end, attached houses near the centre
CLUSTERS = (pack("N", -34.0, "VH") + pack("N", SC_N_T[1] + 2, PLAN_N)
            + pack("S", -22.0, "VH") + pack("S", SC_S_T[1] + 2, PLAN_S))
CLUSTERS = [c for c in CLUSTERS if c["plots"]]


def trim(c, n):
    """Rebuild cluster c with n plots fewer: drop the far plots of the longer row, the court grows."""
    keep = {"lo": [], "hi": []}
    for p, q in zip(c["plots"], c["specs"]):
        keep[q[5]].append((p, q))
    for _ in range(n):
        max(keep.values(), key=len).pop()
    pairs = keep["hi"] + keep["lo"]
    sg = 1 if c["side"] == "N" else -1
    w, d = TYPES[c["kind"]]
    n_in = SP_W / 2 + FRONT
    t0, W = c["t0"], c["W"]
    lane_t = (t0 + d, t0 + W - d)
    end = n_in + max(len(keep["hi"]), len(keep["lo"])) * w
    c["plots"] = [p for p, _ in pairs]
    c["specs"] = [q for _, q in pairs]
    c["lane"] = strip_poly(*lane_t, sg * (SP_W / 2), sg * end).intersection(c["strip"])
    c["head"] = Point(sp((lane_t[0] + lane_t[1]) / 2, sg * (end + 7))).buffer(7).intersection(c["strip"])
    court = c["strip"].difference(unary_union(c["plots"] + [c["lane"], c["front"]]).buffer(0.01))
    c["court"] = unary_union([g for g in getattr(court, "geoms", [court]) if g.area > 30])
    c["lane_len"] = end + 14 - SP_W / 2


for kind, target in TARGET.items():
    cs = [c for c in CLUSTERS if c["kind"] == kind]
    extra = sum(len(c["plots"]) for c in cs) - target
    if extra < 0 and os.environ.get("PLAN"):
        print("SHORT", kind, extra); sys.exit()
    assert extra >= 0, f"{kind}: {extra}"
    while extra > 0:  # take one plot at a time from the fullest cluster
        c = max(cs, key=lambda c: len(c["plots"]))
        trim(c, 1)
        extra -= 1
CLUSTERS.sort(key=lambda c: (c["side"] == "S", c["t0"]))
for i, c in enumerate(CLUSTERS):
    c["name"] = f"C{i + 1}"
VILLAS = [p for c in CLUSTERS if c["kind"] == "V" for p in c["plots"]]
HOUSES = [p for c in CLUSTERS if c["kind"] == "H" for p in c["plots"]]


# leftovers inside the compound become shared gardens / play grounds
_used = unary_union([c["strip"] for c in CLUSTERS] + [SPINE, ROUNDABOUT, BOULEVARD, FORECOURT, SC_PLAZA] + list(SC_ITEMS.values()))
GARDENS = [g for g in getattr(G_IN.difference(_used.buffer(0.5)), "geoms", []) if g.area > 150]

# --- three towers on a plaza (basement parking) in the eastern zone, own gate on the south road -----
TW = 28.3  # 800 m2 floor plate, 4 corner flats
_tc = ((U_SPLIT + 28, 122), (U_SPLIT + 28, 50), (U_SPLIT + 92, 88))
TOWERS = [box(c[0] - TW / 2, c[1] - TW / 2, c[0] + TW / 2, c[1] + TW / 2) for c in _tc]
TOWER_GAP = min(a.distance(b) for k, a in enumerate(TOWERS) for b in TOWERS[k + 1:])
TOWER_FENCE = min(t.distance(ISLAND.exterior) for t in TOWERS)
T_ENTRY_U = U_SPLIT + 68.0
T_DROP = Point((T_ENTRY_U, 34)).buffer(11)
T_ROAD = unary_union([band((T_ENTRY_U, -2), (T_ENTRY_U, 34), 4.0), T_DROP]).intersection(ISLAND)
T_GATE_LINE = LineString([(T_ENTRY_U - 8, 6), (T_ENTRY_U + 8, 6)])
T_PLAZA = unary_union([t.buffer(9, join_style="mitre") for t in TOWERS]).convex_hull.intersection(ISLAND.buffer(-6)).difference(T_ROAD)
T_BASEMENT = unary_union([t.buffer(9, join_style="mitre") for t in TOWERS]).convex_hull.intersection(ISLAND.buffer(-8))
T_RAMP = box(T_ENTRY_U + 6, 6, T_ENTRY_U + 12, 30)
T_POOL = box(U_SPLIT + 62, 112, U_SPLIT + 90, 126)
BRIDGE = band(sp(S_LEN, 0), (U_SPLIT + 14, sp(S_LEN, 0)[1]), 1.8).difference(Point(SB).buffer(TURN_R))
PED_GATE = LineString([(U_SPLIT, sp(S_LEN, 0)[1] - 3), (U_SPLIT, sp(S_LEN, 0)[1] + 3)])
N_PARK = 360  # basement spaces, 1.5 per flat

# --- public front (west of the cross road) --------------------------------------------------------
W_IN = WEST.buffer(-3, join_style="mitre")
PUB = {
    "PRIMARY": box(-1, 4, 55, 58),
    "SEC_SCHOOL": box(64, 4, 140, 69),
    "HEALTH": box(98, 98, 140, 125),
    "MOSQUE": box(88, 134, 140, 184),
    "POLICE": box(22, 272, 48, 320),
    "CIVIL_DEF": box(52, 268, 78, 320),
}
UTIL_ITEMS = {
    "POWER": box(-30, 234, 16, 268),
    "WATER": box(-30, 194, 18, 228),
    "WASTE": box(-30, 176, 14, 189),
}
PUB = {k: v.intersection(W_IN) for k, v in PUB.items()}
UTIL_ITEMS = {k: v.intersection(W_IN) for k, v in UTIL_ITEMS.items()}
PUB_PARK = {
    "P_MOSQUE": box(96, 188, 140, 226).intersection(W_IN),
}
ORCHARD = W_IN.difference(unary_union(list(PUB.values()) + list(PUB_PARK.values()) + list(UTIL_ITEMS.values())).buffer(3))
ORCHARD = max(getattr(ORCHARD, "geoms", [ORCHARD]), key=lambda g: g.area)


def A(g):
    return 0.0 if g is None else g.area


# --- indicative footprints -------------------------------------------------------------------------
def footprint(spec, kind):
    r0, r1, a, b, sg, front = spec
    if kind == "V":   # 120 m2 ground floor (30 %), 4 m front setback, 3 m side yards
        sb, dep, side = 4.0, 12.0, 3.0
    else:             # 144 m2 (60 %), 2.5 m front setback, attached on both sides
        sb, dep, side = 2.5, 12.0, 0.0
    t_a, t_b = (r1 - sb - dep, r1 - sb) if front == "hi" else (r0 + sb, r0 + sb + dep)
    return strip_poly(t_a, t_b, sg * (a + side) if sg > 0 else sg * (b - side), sg * (b - side) if sg > 0 else sg * (a + side))


for c in CLUSTERS:
    c["fps"] = [footprint(q, c["kind"]) for q in c["specs"]]

# --- land use -------------------------------------------------------------------------------------
def total(gs):
    return sum(g.area for g in gs)


ROADS = unary_union([SPINE, ROUNDABOUT, BOULEVARD, FORECOURT, T_ROAD, BRIDGE] + [c["lane"].union(c["head"]) for c in CLUSTERS]
                    + list(PUB_PARK.values())).difference(RB_ISLAND).intersection(SITE)
ROADS_ALL = ROADS.area + CROSS_IN.intersection(SITE).area
LANDUSE = [
    ("Villa plots 400 m2 - قطع الفلل", len(VILLAS) * 400.0),
    ("House plots 240 m2 - قطع الدور", len(HOUSES) * 240.0),
    ("Towers + plaza (basement parking) - الأبراج والبلازا", T_PLAZA.area + total(TOWERS) - total([t.intersection(T_PLAZA) for t in TOWERS])),
    ("Public front services - خدمات الواجهة العامة", total(PUB.values())),
    ("Service centre - المركز الخدمي", total(SC_ITEMS.values()) + SC_PLAZA.area),
    ("Utilities - المرافق الفنية", total(UTIL_ITEMS.values())),
    ("Roads, lanes, gates, parking - الطرق والمواقف", ROADS_ALL),
    ("Green: parks, courts, belts - المساحات الخضراء", 0.0),
]
LANDUSE[-1] = (LANDUSE[-1][0], SITE.area - sum(a for _, a in LANDUSE))
GREEN_PCT = LANDUSE[-1][1] / SITE.area * 100
ROADS_PCT = ROADS_ALL / SITE.area * 100



# --- DXF ------------------------------------------------------------------------------------------
LAYERS = {
    "MP_BOUNDARY": (1, 50), "MP_BOUNDARY_COORDS": (6, 18), "MP_FENCE": (8, 35), "MP_GATES": (1, 50),
    "MP_ROADS": (8, 25), "MP_ROAD_CL": (8, 13), "MP_LANES": (8, 18), "MP_PARKING": (9, 13),
    "MP_PLOT_VILLA": (30, 18), "MP_PLOT_HOUSE": (40, 18), "MP_FOOTPRINT": (7, 25), "MP_TOWERS": (1, 50),
    "MP_SERVICES": (200, 25), "MP_SERVICE_CENTRE": (210, 25), "MP_UTILITIES": (8, 25),
    "MP_GREEN_COURT": (3, 13), "MP_GREEN_PARK": (94, 13), "MP_TREES": (3, 13),
    "MP_CONTEXT": (8, 13), "MP_TEXT": (7, 18), "MP_TEXT_PLOTNO": (8, 9), "MP_TABLE": (7, 18), "MP_NORTH": (7, 25),
    "MP_HATCH_RES": (31, 0), "MP_HATCH_SERV": (211, 0), "MP_HATCH_GREEN": (93, 0), "MP_HATCH_ROAD": (252, 0),
    "MP_HATCH_WATER": (151, 0), "MP_HATCH_TOWER": (11, 0),
}
FILL = {  # true colours for the hatches (also used by the preview)
    "villa": (244, 214, 160), "house": (238, 170, 120), "tower": (196, 96, 86), "pub": (190, 160, 220),
    "sc": (214, 176, 230), "util": (170, 170, 170), "court": (168, 214, 140), "park": (120, 186, 110),
    "garden": (196, 226, 172), "road": (205, 205, 205), "lane": (225, 225, 225), "water": (150, 200, 240),
    "fore": (215, 215, 215), "park_lot": (232, 232, 232),
}


def polys(g):
    if g is None or g.is_empty:
        return []
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 0.5]


def write_dxf(path):
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 6
    doc.styles.add("AR", font="arial.ttf")
    for n, (c, lw) in LAYERS.items():
        doc.layers.add(n, color=c, lineweight=lw if lw else -3)
    msp = doc.modelspace()

    def outline(g, layer, closed=True):
        for p in polys(g):
            msp.add_lwpolyline([utm(q) for q in p.exterior.coords[:-1]], close=True, dxfattribs={"layer": layer})

    def hatch(g, layer, rgb):
        for p in polys(g):
            h = msp.add_hatch(dxfattribs={"layer": layer})
            h.rgb = rgb
            h.paths.add_polyline_path([utm(q) for q in p.exterior.coords[:-1]], is_closed=True)
            for hole in p.interiors:
                h.paths.add_polyline_path([utm(q) for q in hole.coords[:-1]], is_closed=True)

    def line(ls, layer):
        msp.add_lwpolyline([utm(q) for q in ls.coords], dxfattribs={"layer": layer})

    def text(s, at, h=3.0, rot=0.0, layer="MP_TEXT"):
        t = msp.add_text(s, height=h, rotation=rot + ROT, dxfattribs={"layer": layer, "style": "AR"})
        t.set_placement(utm(at), align=TextEntityAlignment.MIDDLE_CENTER)

    # hatches first so outlines draw on top
    hatch(ORCHARD, "MP_HATCH_GREEN", FILL["park"])
    for g in GARDENS:
        hatch(g, "MP_HATCH_GREEN", FILL["garden"])
    hatch(G_IN.symmetric_difference(GATED).intersection(GATED), "MP_HATCH_GREEN", FILL["garden"])
    hatch(ISLAND, "MP_HATCH_GREEN", FILL["garden"])
    for c in CLUSTERS:
        hatch(c["court"], "MP_HATCH_GREEN", FILL["court"])
        hatch(c["front"], "MP_HATCH_GREEN", FILL["garden"])
        hatch(c["lane"].union(c["head"]), "MP_HATCH_ROAD", FILL["lane"])
        for p in c["plots"]:
            hatch(p, "MP_HATCH_RES", FILL["villa" if c["kind"] == "V" else "house"])
    hatch(unary_union([SPINE, ROUNDABOUT, BOULEVARD]).difference(RB_ISLAND), "MP_HATCH_ROAD", FILL["road"])
    hatch(RB_ISLAND, "MP_HATCH_GREEN", FILL["park"])
    hatch(FORECOURT.difference(BOULEVARD), "MP_HATCH_ROAD", FILL["fore"])
    hatch(CROSS_IN, "MP_HATCH_ROAD", FILL["road"])
    for g in PUB.values():
        hatch(g, "MP_HATCH_SERV", FILL["pub"])
    for g in PUB_PARK.values():
        hatch(g, "MP_HATCH_ROAD", FILL["park_lot"])
    for g in SC_ITEMS.values():
        hatch(g, "MP_HATCH_SERV", FILL["sc"])
    for g in UTIL_ITEMS.values():
        hatch(g, "MP_HATCH_SERV", FILL["util"])
    hatch(T_ROAD, "MP_HATCH_ROAD", FILL["road"])
    hatch(T_PLAZA, "MP_HATCH_ROAD", FILL["fore"])
    hatch(T_POOL, "MP_HATCH_WATER", FILL["water"])
    for t in TOWERS:
        hatch(t, "MP_HATCH_TOWER", FILL["tower"])

    # boundary + walls
    outline(SITE, "MP_BOUNDARY")
    outline(SITE_RAW, "MP_BOUNDARY_COORDS")
    outline(GATED, "MP_FENCE")
    outline(ISLAND, "MP_FENCE")
    for c in CLUSTERS:
        outline(c["strip"], "MP_FENCE")
    # roads
    outline(unary_union([SPINE, ROUNDABOUT, BOULEVARD]), "MP_ROADS")
    outline(RB_ISLAND, "MP_ROADS")
    line(LineString([SA, SB]), "MP_ROAD_CL")
    outline(FORECOURT, "MP_ROADS")
    outline(CROSS_IN, "MP_ROADS")
    for g in INSPECT:
        outline(g, "MP_GATES")
    outline(GUARD, "MP_GATES")
    outline(VISITOR_P, "MP_PARKING")
    line(GATE_LINE, "MP_GATES")
    line(T_GATE_LINE, "MP_GATES")
    outline(T_ROAD, "MP_ROADS")
    outline(T_PLAZA, "MP_ROADS")
    msp.add_lwpolyline([utm(q) for q in T_BASEMENT.exterior.coords[:-1]], close=True,
                       dxfattribs={"layer": "MP_PARKING", "linetype": "DASHED"})
    outline(T_RAMP, "MP_PARKING")
    outline(BRIDGE, "MP_ROADS")
    line(PED_GATE, "MP_GATES")
    # clusters
    for c in CLUSTERS:
        outline(c["lane"].union(c["head"]), "MP_LANES")
        outline(c["court"], "MP_GREEN_COURT")
        line(LineString(c["gate"]), "MP_GATES")
        outline(c["kiosk"], "MP_GATES")
        lay = "MP_PLOT_VILLA" if c["kind"] == "V" else "MP_PLOT_HOUSE"
        for p in c["plots"]:
            outline(p, lay)
        for f in c["fps"]:
            outline(f, "MP_FOOTPRINT")
    for g in PUB.values():
        outline(g, "MP_SERVICES")
    for g in PUB_PARK.values():
        outline(g, "MP_PARKING")
    for g in SC_ITEMS.values():
        outline(g, "MP_SERVICE_CENTRE")
    for g in UTIL_ITEMS.values():
        outline(g, "MP_UTILITIES")
    for t in TOWERS:
        outline(t, "MP_TOWERS")
    outline(T_POOL, "MP_GREEN_PARK")
    outline(ORCHARD, "MP_GREEN_PARK")
    for g in GARDENS:
        outline(g, "MP_GREEN_PARK")
    for t in TREES:
        msp.add_circle(utm(t), 4, dxfattribs={"layer": "MP_TREES"})
    # outer roads (approx., from the cadastral scan)
    for a, b in ((P[3], P[0]), (P[1], P[2])):
        la, lb = loc(a), loc(b)
        for d in (0.0, 12.0):
            dv = np.subtract(lb, la) / math.dist(la, lb)
            nn = np.array([-dv[1], dv[0]]) * d
            msp.add_line(utm(tuple(np.add(la, nn - dv * 40))), utm(tuple(np.add(lb, nn + dv * 40))), dxfattribs={"layer": "MP_CONTEXT"})

    # labels
    for c in CLUSTERS:
        kind = f"{len(c['plots'])} villas 400 m2 - فلل" if c["kind"] == "V" else f"{len(c['plots'])} houses 200 m2 - دور"
        cc = c["court"].representative_point()
        text(f"{c['name']}", (cc.x, cc.y + 3), 5)
        text(kind, (cc.x, cc.y - 3), 2.2)
        for j, p in enumerate(c["plots"]):
            q = p.centroid
            text(f"{c['name']}-{j + 1:02d}", (q.x, q.y), 1.2, layer="MP_TEXT_PLOTNO")
    for k, g in {**PUB, **SC_ITEMS, **UTIL_ITEMS}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        text(n1, (q.x, q.y + 2.5), 3)
        text(f"{n2}  {g.area:,.0f} m2", (q.x, q.y - 2.5), 2.2)
    for k, at in LABELS.items():
        n1, n2 = NAMES[k]
        text(n1, (at[0], at[1] + 2.8), 3.4)
        text(n2, (at[0], at[1] - 2.8), 2.6)
    text(f"PLAZA - BASEMENT PARKING {N_PARK} CARS", (T_ENTRY_U + 10, 70), 2.6)
    for t, nm in zip(TOWERS, ("TOWER A", "TOWER B", "TOWER C")):
        text(nm, (t.centroid.x, t.centroid.y + 3), 3.5)
        text("G+19, 76 flats", (t.centroid.x, t.centroid.y - 3), 2.2)

    # north arrow + table
    na = (-120, 260)
    gn = np.array([U[1], V[1]])   # grid north in the local frame
    tip = tuple(np.add(na, gn * 30))
    msp.add_lwpolyline([utm(tuple(np.add(na, np.array([-gn[1], gn[0]]) * 8 - gn * 10))), utm(tip),
                        utm(tuple(np.add(na, np.array([gn[1], -gn[0]]) * 8 - gn * 10)))], close=True, dxfattribs={"layer": "MP_NORTH"})
    text("N", tuple(np.add(na, gn * 40)), 10, layer="MP_NORTH")
    tx, ty = 338560.0, 4035840.0  # west of the site, unrotated
    for i, row in enumerate(table_rows()):
        msp.add_text(row, height=5 if i == 0 else 3.6, dxfattribs={"layer": "MP_TABLE", "style": "AR"}).set_placement(
            (tx, ty - i * 6.5), align=TextEntityAlignment.TOP_LEFT)
    doc.saveas(path)


ROT = math.degrees(math.atan2(U[1], U[0]))

NAMES = {
    "PRIMARY": ("PRIMARY SCHOOL", "مدرسة ابتدائية"), "POWER": ("POWER STATION", "محطة كهرباء"),
    "WATER": ("WATER STATION", "محطة ماء"), "WASTE": ("WASTE", "نفايات"),
    "SEC_SCHOOL": ("SECONDARY SCHOOL (INT. + PREP.)", "ثانوية (متوسطة وإعدادية)"),
    "HEALTH": ("HEALTH CENTRE", "مركز صحي"), "MOSQUE": ("FRIDAY MOSQUE", "جامع"),
    "POLICE": ("POLICE", "مركز شرطة"), "CIVIL_DEF": ("CIVIL DEFENCE", "دفاع مدني"),
    "MALL": ("MALL", "مول"), "CLUB": ("SOCIAL CLUB + SPORTS", "النادي والملاعب"),
    "ADMIN": ("ADMIN + SECURITY", "إدارة وأمن"), "KG": ("KINDERGARTEN + NURSERY", "روضة وحضانة"),
    "PLAZA": ("CENTRE PLAZA", "ساحة المركز"),
    "GATE": ("GATE 1 - MAIN + INSPECTION", "البوابة 1 الرئيسية وساحة التفتيش"),
    "SPINE": ("DISTRIBUTOR STREET 18 m", "الشارع الموزع"),
    "ORCHARD_IN": ("ORCHARD GARDEN", "حديقة البستان"),
    "PARK": ("OPEN PUBLIC PARK", "حديقة عامة مفتوحة"),
    "TOWERS": ("TOWER ZONE - SECOND GATE", "منطقة الأبراج - البوابة الثانية"),
    "CROSS": ("CROSS ROAD - STAYS PUBLIC", "الشارع العرضي يبقى عاما"),
    "PUBLIC": ("PUBLIC FRONT", "الواجهة العامة"),
    "BRIDGE": ("CONTROLLED PEDESTRIAN GATE", "بوابة مشاة مراقبة"),
    "TGATE": ("GATE 2 - TOWERS (SOUTH ROAD)", "البوابة 2 - الأبراج"),
    "P_MOSQUE": ("PARKING", "موقف"),
}
_gardens_w = [g for g in GARDENS if g.centroid.x < 300]
_orch_in = max(_gardens_w, key=lambda g: g.area) if _gardens_w else None
LABELS = {
    "GATE": (GATE_U, GATE_V + 34),
    "SPINE": sp(S_LEN * 0.72, 0),
    "PARK": tuple(ORCHARD.representative_point().coords[0]),
    "BRIDGE": (U_SPLIT + 4, sp(S_LEN, 0)[1] + 14),
    "TOWERS": (U_SPLIT + 80, 150),
    "PLAZA": tuple(SC_PLAZA.representative_point().coords[0]),
    "CROSS": tuple(np.add(CROSS_A, cross_dir * 60)),
    "PUBLIC": (40, 316),
    "TGATE": (T_ENTRY_U + 30, 12),
    "P_MOSQUE": tuple(PUB_PARK["P_MOSQUE"].centroid.coords[0]),
}
if _orch_in is not None:
    LABELS["ORCHARD_IN"] = tuple(_orch_in.representative_point().coords[0])

N_APTS = 3 * 20 * 4


def table_rows():
    units = len(VILLAS) + len(HOUSES) + N_APTS
    rows = [
        "PROPOSAL D rev.2 - SECURE CLUSTERS - المقترح د م2: التجمعات الآمنة",
        "Plot 157 / District 53 Baybokht - NIC 5/2026 - UTM 38S",
        "",
        f"UNITS: {len(VILLAS)} villas 400 m2 + {len(HOUSES)} houses 240 m2 + {N_APTS} flats = {units}",
        f"Green {GREEN_PCT:.1f} %   Roads + parking {ROADS_PCT:.1f} %   Two gates only, both on the long sides",
        f"Clusters: {len(CLUSTERS)} gated cul-de-sacs, longest lane {max(c['lane_len'] for c in CLUSTERS):.0f} m (limit 120 m)",
        f"Main gate on the north road at {math.dist(NW, (GATE_U, north_v(GATE_U))):.0f} m from Q2, inspection forecourt {FORE_W:.0f} x {FORE_D:.0f} m",
        f"Towers: 3 x 20 floors x 4 flats, 800 m2 plate, gap {TOWER_GAP:.1f} m (min 33), basement {N_PARK} cars",
        "",
        "LAND USE - استعمالات الأرض              m2        %",
    ]
    for n, a in LANDUSE:
        rows.append(f"{n:<46s}{a:>9,.0f}  {a / SITE.area * 100:5.1f}")
    rows.append(f"{'TOTAL':<46s}{SITE.area:>9,.0f}  100.0")
    return rows


def write_preview(png, pdf):
    import arabic_reshaper
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from bidi.algorithm import get_display
    from matplotlib.patches import Polygon as MPoly

    def ar(s):
        # matplotlib >= 3.9 shapes and orders RTL text itself (libraqm); older builds need help
        if NATIVE_RTL:
            return s
        return get_display(arabic_reshaper.reshape(s))

    plt.rcParams["font.family"] = "DejaVu Sans"
    NATIVE_RTL = tuple(int(x) for x in matplotlib.__version__.split(".")[:2]) >= (3, 9)
    fig = plt.figure(figsize=(33.1, 23.4))  # A1
    ax = fig.add_axes([0.02, 0.30, 0.96, 0.64])
    rgb = {k: tuple(c / 255 for c in v) for k, v in FILL.items()}

    def f(g, key, ec="#555", lw=0.3, z=1):
        for p in polys(g):
            ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=rgb[key] if key else "none", ec=ec, lw=lw, zorder=z))

    def t(s, at, size=6, ar_s=None, w="normal", color="#222", z=10):
        ax.text(at[0], at[1], s if ar_s is None else f"{ar(ar_s)}\n{s}", fontsize=size, ha="center", va="center",
                fontweight=w, color=color, zorder=z, linespacing=1.1)

    f(SITE, "garden", ec="none")
    f(ORCHARD, "park", ec="none")
    for g in GARDENS:
        f(g, "garden", ec="none")
    f(ISLAND, "garden", ec="none")
    f(CROSS_IN, "road", ec="#777")
    for c in CLUSTERS:
        f(c["court"], "court", ec="none")
        f(c["lane"].union(c["head"]), "lane", ec="#888", lw=0.3)
        for p in c["plots"]:
            f(p, "villa" if c["kind"] == "V" else "house", ec="#8a6a40", lw=0.25)
        for fp in c["fps"]:
            f(fp, None, ec="#444", lw=0.35)
        f(c["strip"], None, ec="#666", lw=0.7, z=3)
        ax.plot(*zip(*c["gate"]), color="#d00", lw=1.6, zorder=4)
        cc = c["court"].representative_point()
        t(c["name"], (cc.x, cc.y), 7, w="bold", color="#2b5a1e")
    f(unary_union([SPINE, ROUNDABOUT, BOULEVARD]), "road", ec="#666", lw=0.5)
    f(RB_ISLAND, "park", ec="#666")
    f(FORECOURT.difference(BOULEVARD.buffer(0.1)), "fore", ec="#666")
    for g in INSPECT + [GUARD]:
        f(g, "util", ec="#333")
    f(VISITOR_P, "park_lot", ec="#777")
    ax.plot(*zip(*GATE_LINE.coords), color="#d00", lw=2.5, zorder=5)
    ax.plot(*zip(*T_GATE_LINE.coords), color="#d00", lw=2.5, zorder=5)
    f(SC_PLAZA, "fore", ec="#777")
    for k, g in PUB.items():
        f(g, "pub", ec="#6a4a8a", lw=0.5)
    for g in PUB_PARK.values():
        f(g, "park_lot", ec="#777")
    for g in SC_ITEMS.values():
        f(g, "sc", ec="#6a4a8a", lw=0.5)
    for g in UTIL_ITEMS.values():
        f(g, "util", ec="#444", lw=0.5)
    f(T_ROAD, "road", ec="#666")
    f(T_PLAZA, "fore", ec="#777")
    ax.plot(*T_BASEMENT.exterior.xy, color="#555", lw=0.8, ls="--", zorder=4)
    t(f"PLAZA - BASEMENT {N_PARK} CARS", (T_ENTRY_U + 12, 72), 6.5, ar_s="بلازا وسرداب مواقف")
    f(T_POOL, "water", ec="#468")
    f(BRIDGE, "road", ec="#444")
    ax.plot(*PED_GATE.xy, color="#d00", lw=2.5, zorder=5)
    for tw in TOWERS:
        f(tw, "tower", ec="#5a1e1e", lw=0.8, z=5)
    f(SITE, None, ec="#c00", lw=1.6, z=6)
    f(GATED, None, ec="#333", lw=1.0, z=6)
    f(ISLAND, None, ec="#333", lw=1.0, z=6)
    for tr in TREES:
        ax.add_patch(plt.Circle(tr, 4, fc="#3d8a3d", ec="#1f4f1f", lw=0.4, zorder=7))

    for k, g in {**PUB, **SC_ITEMS, **UTIL_ITEMS}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        t(f"{n1}\n{g.area:,.0f} m²", (q.x, q.y), 6.5, ar_s=n2)
    for k, at in LABELS.items():
        n1, n2 = NAMES[k]
        t(n1, at, 7.5, ar_s=n2, w="bold")
    for tw, nm in zip(TOWERS, ("A", "B", "C")):
        t(f"TOWER {nm}\n20 F", tw.centroid.coords[0], 6.5, color="white", w="bold", z=11)

    # north arrow + scale
    na = np.array([-45.0, 296.0])
    gn = np.array([U[1], V[1]])
    side_v = np.array([-gn[1], gn[0]])
    ax.add_patch(MPoly([tuple(na - gn * 12 + side_v * 9), tuple(na + gn * 30), tuple(na - gn * 12 - side_v * 9)], closed=True, fc="k", zorder=12))
    t("N", tuple(na + gn * 44), 14, w="bold")
    for i in range(5):
        ax.add_patch(plt.Rectangle((560 + i * 20, 300), 20, 4, fc="k" if i % 2 == 0 else "w", ec="k", lw=0.6))
        t(f"{i * 20}", (560 + i * 20, 296), 7)
    t("100 m", (660, 296), 7)
    ax.set_xlim(-80, 900)
    ax.set_ylim(-20, 360)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.5, 0.965, ar("المخطط العام - المقترح د (م2): التجمعات الآمنة") + "   |   MASTER PLAN - PROPOSAL D rev.2: SECURE CLUSTERS",
             ha="center", fontsize=26, fontweight="bold")
    fig.text(0.5, 0.945, ar("مجمع الشلالات السكني - القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026"),
             ha="center", fontsize=15)
    rows = table_rows()
    tx = fig.add_axes([0.03, 0.02, 0.45, 0.26])
    tx.axis("off")
    head = [r for r in rows[:8] if r]
    head[0] = "PROPOSAL D rev.2 - SECURE CLUSTERS"
    tx.text(0, 1, "\n".join(head), family="DejaVu Sans Mono", fontsize=10.5, va="top", linespacing=1.5)
    y0 = 0.60
    tx.text(0, y0, "LAND USE", fontsize=10.5, fontweight="bold", va="top")
    tx.text(0.62, y0, "m²", fontsize=10.5, fontweight="bold", va="top", ha="right")
    tx.text(0.72, y0, "%", fontsize=10.5, fontweight="bold", va="top", ha="right")
    tx.text(1.0, y0, ar("استعمالات الأرض"), fontsize=10.5, fontweight="bold", va="top", ha="right")
    for i, (n, a) in enumerate(LANDUSE + [("TOTAL - المجموع", SITE.area)]):
        en, arb = n.split(" - ")
        y = y0 - 0.05 * (i + 1)
        tx.text(0, y, en, fontsize=10, va="top")
        tx.text(0.62, y, f"{a:,.0f}", fontsize=10, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(0.72, y, f"{a / SITE.area * 100:.1f}", fontsize=10, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(1.0, y, ar(arb), fontsize=10, va="top", ha="right")
    key = [
        ("villa", "Villa plot 400 m² (16 x 25)", "قطعة فيلا"), ("house", "Attached house 240 m² (12 x 20)", "دار متصلة"),
        ("tower", "Tower, 20 floors", "برج"), ("pub", "Public front services", "خدمات الواجهة العامة"),
        ("sc", "Service centre (inside the gate)", "المركز الخدمي داخل البوابة"), ("util", "Utilities", "مرافق فنية"),
        ("court", "Cluster green court", "فناء أخضر للتجمع"), ("park", "Park / orchard", "حديقة / بستان"),
        ("garden", "Gardens, belts", "حدائق وأحزمة خضراء"), ("water", "Pool", "مسبح"),
        ("road", "Streets", "شوارع"), ("lane", "Cluster cul-de-sac (8 m shared surface)", "زقاق مغلق"),
    ]
    lg = fig.add_axes([0.50, 0.02, 0.22, 0.26])
    lg.axis("off")
    for i, (k, en, a) in enumerate(key):
        y = 1 - i * 0.075
        lg.add_patch(plt.Rectangle((0, y - 0.05), 0.08, 0.05, fc=rgb[k], ec="#555", transform=lg.transAxes))
        lg.text(0.11, y - 0.025, f"{en}  -  {ar(a)}", fontsize=10.5, va="center", transform=lg.transAxes)
    lg.plot([0, 0.08], [1 - len(key) * 0.075 - 0.025] * 2, color="#d00", lw=2.5, transform=lg.transAxes)
    lg.text(0.11, 1 - len(key) * 0.075 - 0.025, "Gate / cluster gate  -  " + ar("بوابة"), fontsize=10.5, va="center", transform=lg.transAxes)
    nt = fig.add_axes([0.74, 0.02, 0.24, 0.26])
    nt.axis("off")
    notes = [
        "الفكرة: الخصوصية والأمن",
        "الشارع العرضي يبقى عاما، وغربه واجهة عامة: شرطة، دفاع مدني، جامع، مدرستان،",
        "مركز صحي، محطتا الماء والكهرباء والنفايات، وحديقة مفتوحة حول الأشجار.",
        "بوابتان فقط على الضلعين الطويلين: الرئيسية شمالا مع ساحة تفتيش، والثانية جنوبا للأبراج.",
        "شارع موزع واحد بلا حركة عابرة، وتنتهي طرفاه بدوارين.",
        "كل تجمع زقاق مغلق 120 م أو أقل، ببوابة وكشك حراسة،",
        "وينتهي بفناء أخضر. ظهور القطع متلاصقة فتصبح أسوار التجمعات.",
        "المركز الخدمي في منتصف الموزع: مول، روضة، إدارة، وحديقة مكان النادي الملغى.",
        "ثلاثة أبراج على بلازا فوق سرداب مواقف، وبوابة مشاة مراقبة إلى الموزع.",
        "المدارس خارج البوابة حتى لا تدخل حركة الطلبة إلى التجمعات.",
        "",
        "Layers MP_*: plots, footprints, gates, hatches are separate.",
        "Outer roads, cross road, trees: approx. from the",
        "cadastral scan, to be confirmed by survey.",
    ]
    for i, n in enumerate(notes):
        nt.text(1, 1 - i * 0.07, ar(n) if any("\u0600" <= ch <= "\u06ff" for ch in n) else n, fontsize=11,
                ha="right", va="top", transform=nt.transAxes)
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)


if __name__ == "__main__" and "--check" not in sys.argv:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    base = os.path.join(out_dir, "SHALLALAT_MASTERPLAN_D_R2")
    write_dxf(base + ".dxf")
    write_preview(base + "_preview.png", base + "_preview.pdf")
    print("\n".join(table_rows()))

if __name__ == "__main__" and "--check" in sys.argv:
    print(f"site {SITE.area:,.0f}  west {WEST.area:,.0f}  cross {CROSS_IN.area:,.0f}  gated {GATED.area:,.0f}"
          f"  split u={U_SPLIT:.1f}  tower zone {ISLAND.area:,.0f}")
    print(f"villas {len(VILLAS)}  houses {len(HOUSES)}  tower gap {TOWER_GAP:.1f}  tower-fence {TOWER_FENCE:.1f}  green {GREEN_PCT:.1f}%  roads {ROADS_PCT:.1f}%")
    for c in CLUSTERS:
        print(c["side"], c["kind"], f"t0={c['t0']:.0f}", len(c["plots"]), f"lane {c['lane_len']:.0f} court {c['court'].area:.0f}")
    for k, v in {**PUB, **SC_ITEMS, **UTIL_ITEMS}.items():
        print(f"{k:12s} {v.area:8,.0f}")
    print("orchard", f"{ORCHARD.area:,.0f}", "gardens", f"{sum(g.area for g in GARDENS):,.0f}",
          "gate chainage on N edge", f"{math.dist(NW, (GATE_U, north_v(GATE_U))):.0f}")
