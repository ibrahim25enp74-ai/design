"""Variant 2 of Ibrahim's proposal: «الأحياء المتجاورة» (adjacent neighbourhood quarters).

Same programme, presentation and colours as Ibrahim's developed proposal, different idea:
- the three towers stand on their plaza at the WEST (wide) end, between two tower parks;
- four residential quarters follow each other along the site, separated by cross streets: two villa
  quarters, then the civic spine, then two house quarters;
- every quarter has its own pocket park in its middle; the plot rows run along the long sides
  (the south rows parallel to the south road, the north rows parallel to the north road), so the
  taper of the site is taken by the parks and not by the plots;
- the daily services form a civic spine across the full width of the site, opposite the main gate;
- the secondary school and the utilities sit at the east end, by the service gate; the rest is the east park.

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
NW, NE = np.array(loc(Q[1])), np.array(loc(Q[2]))
EN = (NE - NW) / np.linalg.norm(NE - NW)          # along the north edge, west -> east
NN = np.array([EN[1], -EN[0]])                     # from the north edge into the site


def north_v(u):
    return NW[1] + (u - NW[0]) * (NE[1] - NW[1]) / (NE[0] - NW[0])


def npt(s, w):
    """Point s along the north edge from NW, w into the site."""
    return tuple(NW + s * EN + w * NN)


def nband(w0, w1):
    """Band parallel to the north edge, w0..w1 into the site."""
    return Polygon([npt(-200, w0), npt(1200, w0), npt(1200, w1), npt(-200, w1)])


def sband(v0, v1):
    return box(-200, v0, 1200, v1)


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


# --- dimensions ---------------------------------------------------------------------------------------
ROAD_W = 14.0        # roads along the two long sides
CROSS_W = 12.0       # cross streets between the quarters
LANE_W = 10.0        # quarter lanes
VILLA = (16.0, 25.0)  # frontage x depth = 400 m2
HOUSE = (12.0, 20.0)  # 240 m2
N_VILLAS, N_HOUSES = 80, 88

# along u, west -> east: tower zone | cross | V1 | cross | V2 | cross | civic spine | cross | H1 | cross | H2 |
# cross | east zone
TOWER_END = 70.0
QUARTERS = [  # name, width, kind, rows per half
    ("V1", 118.0, "villa", 3),
    ("V2", 118.0, "villa", 3),
    ("SPINE", 100.0, None, 0),
    ("H1", 122.0, "house", 3),
    ("H2", 100.0, "house", 2),
]
x = TOWER_END
CROSS = []
Q_RANGE = {}
for name, w, kind, rows in QUARTERS:
    CROSS.append((x, x + CROSS_W))
    x += CROSS_W
    Q_RANGE[name] = (x, x + w)
    x += w
CROSS.append((x, x + CROSS_W))
EAST_START = x + CROSS_W
SOUTH_ROAD_END = 762.0          # the south road goes on past the cross street to the utilities

INNER = SITE.intersection(sband(ROAD_W, 1e3)).intersection(nband(ROAD_W, 1e3))   # inside the two long roads

# --- the quarters ---------------------------------------------------------------------------------------
VILLAS, HOUSES = [], []
PARKS = {}           # quarter -> pocket park
BITS = []            # row ends left over -> small corner gardens
QPLOTS = {}


def south_rows(a, b, w, d, rows):
    """Rows along the south road: road | r1 | r2 (back to back) | lane | r3 (backs onto the park)."""
    out, bands, v = [], [], ROAD_W
    seq = ["row", "row", "lane", "row"][: (4 if rows == 3 else 3)]
    for s in seq:
        h = LANE_W if s == "lane" else d
        if s == "row":
            n = int((b - a) // w)
            u0 = a + ((b - a) - n * w) / 2
            row = [box(u0 + i * w, v, u0 + (i + 1) * w, v + d) for i in range(n)]
            out.append(row)
            bands.append(box(a, v, b, v + d))
        else:
            LANES.append(LineString([(a, v + h / 2), (b, v + h / 2)]))
        v += h
    return out, bands, v


def north_rows(a, b, w, d, rows):
    out, bands, wv = [], [], ROAD_W
    seq = ["row", "row", "lane", "row"][: (4 if rows == 3 else 3)]
    for s in seq:
        h = LANE_W if s == "lane" else d
        if s == "row":
            fits = []
            for s0 in np.arange(0, 1000, 0.25):
                r = Polygon([npt(s0, wv), npt(s0 + w, wv), npt(s0 + w, wv + d), npt(s0, wv + d)])
                xs = [c[0] for c in r.exterior.coords]
                if min(xs) >= a and max(xs) <= b:
                    fits.append(s0)
            lo, hi = min(fits), max(fits) + w
            n = int((hi - lo) // w)
            s0 = lo + ((hi - lo) - n * w) / 2
            row = [Polygon([npt(s0 + i * w, wv), npt(s0 + (i + 1) * w, wv), npt(s0 + (i + 1) * w, wv + d),
                            npt(s0 + i * w, wv + d)]) for i in range(n)]
            out.append(row)
            bands.append(nband(wv, wv + d).intersection(box(a, -1e3, b, 1e3)))
        else:
            LANES.append(LineString([npt(-200, wv + h / 2), npt(1200, wv + h / 2)]).intersection(box(a, -1e3, b, 1e3)))
        wv += h
    return out, bands, wv


ROWS = {}
LANES = []           # centre lines of the quarter lanes
for name, w, kind, rows in QUARTERS:
    if kind is None:
        continue
    a, b = Q_RANGE[name]
    pw, pd = VILLA if kind == "villa" else HOUSE
    srows, sb, vtop = south_rows(a, b, pw, pd, rows)
    nrows, nb, wbot = north_rows(a, b, pw, pd, rows)
    region = INNER.intersection(box(a, -1e3, b, 1e3))
    ROWS[name] = (kind, srows + nrows, sb + nb)
    PARKS[name] = clean(region.intersection(sband(vtop, 1e3)).intersection(nband(wbot, 1e3)))

# exact counts: the plots taken out are the row ends next to the park, so each park opens onto the
# cross streets through a small garden (the park gates)
for kind, target in (("villa", N_VILLAS), ("house", N_HOUSES)):
    qs = [q for q in ROWS if ROWS[q][0] == kind]
    total_n = sum(len(r) for q in qs for r in ROWS[q][1])
    extra = total_n - target
    assert extra >= 0, (kind, total_n)
    i = 0
    while extra > 0:
        q = qs[i % len(qs)]
        rws = ROWS[q][1]
        inner = [rws[len(rws) // 2 - 1], rws[-1]]          # the rows facing the park, south and north
        r = inner[(i // len(qs)) % 2]
        side = (i // (2 * len(qs))) % 2
        r.pop(0 if side == 0 else -1)
        extra -= 1
        i += 1
    for q in qs:
        plots = [p for r in ROWS[q][1] for p in r]
        QPLOTS[q] = plots
        (VILLAS if kind == "villa" else HOUSES).extend(plots)
        for band in ROWS[q][2]:
            rest = band.intersection(SITE).difference(unary_union(plots).buffer(0.01))
            BITS.extend(p for p in polys(clean(rest)) if p.area > 20)
            for p in polys(rest):
                if p.area > 20 and not any(p.equals(x) for x in BITS):
                    pass
BITS = [p for p in polys(unary_union(BITS)) if p.area > 20]

# --- civic spine (across the full width, opposite the main gate) -------------------------------------------
SERV, OPEN = {}, {}
sa, sb_ = Q_RANGE["SPINE"]
SPINE = clean(INNER.intersection(box(sa, -1e3, sb_, 1e3)))
north_band, r = cut(SPINE, 9000, "v", "max")
mid_band, south_band = cut(r, 5600, "v", "max")
# north band, on the main gate: mall + its parking to the west, health, police and civil defence to the east
# (emergency services next to the gate), the civic forecourt on the gate axis between them
OPEN["PARK_MALL"], nb_ = cut(north_band, 1200, "u", "min")
SERV["MALL"], nb_ = cut(nb_, 3000, "u", "min")
FORECOURT, east_ = cut(nb_, 1600, "u", "min")
# police and civil defence on the north road (straight out to the gate and the perimeter road), the health
# centre below them on the cross street, its garden on the civic garden
_pc, east_ = cut(east_, 1200, "v", "max")
SERV["POLICE"], SERV["CIVIL_DEF"] = cut(_pc, 600, "u", "min")
SERV["HEALTH"], OPEN["G_HEALTH"] = cut(east_, 1000, "v", "max")
# middle: the mosque on the axis in the civic garden
_mc = mid_band.centroid
SERV["MOSQUE"] = box(_mc.x - 22.36, _mc.y - 22.36, _mc.x + 22.36, _mc.y + 22.36)
CIVIC_GARDEN = clean(mid_band.difference(SERV["MOSQUE"]))
# south: kindergarten and primary school on the quiet south road, their garden between them
# the kindergarten is split in two of 750 m2 (same total) so no home is more than ~300 m from one:
# one here for the middle quarters, one at the west end for the towers and quarter 1
_sbx = south_band.bounds
SERV["KG"] = box(_sbx[2] - 27.4, _sbx[1], _sbx[2], _sbx[1] + 750.0 / 27.4)   # square plot on the south road
SERV["PRIMARY"], sb2 = cut(clean(south_band.difference(SERV["KG"])), 3000, "u", "min")
OPEN["G_SCHOOL"] = sb2

# --- tower zone at the west end ---------------------------------------------------------------------------
TZ = clean(SITE.intersection(box(-1e3, -1e3, TOWER_END, 1e3)))
PLAZA_V = (62.0, 238.0)
PLAZA_ALL = clean(TZ.intersection(box(-1e3, PLAZA_V[0], 1e3, PLAZA_V[1])))
TOWER_PARK_S = clean(TZ.intersection(box(-1e3, -1e3, 1e3, PLAZA_V[0])))
SERV["KG_W"] = box(TOWER_END - 28.0, 0.0, TOWER_END, 750.0 / 28.0)      # on the cross street, by the south road
TOWER_PARK_S = clean(TOWER_PARK_S.difference(SERV["KG_W"]))
TOWER_PARK_N = clean(TZ.intersection(box(-1e3, PLAZA_V[1], 1e3, 1e3)))
TS = 31.5
TOWER_C = [(36.0, 92.0), (20.0, 150.0), (36.0, 208.0)]    # staggered, so every tower sees the parks
TOWERS = [box(x - TS / 2, y - TS / 2, x + TS / 2, y + TS / 2) for x, y in TOWER_C]
PLAZA = PLAZA_ALL.difference(unary_union(TOWERS))
DROPOFF = Point((TOWER_END, 150.0)).buffer(15.0).intersection(PLAZA)
DROP_ISLAND = Point((TOWER_END, 150.0)).buffer(5.5).intersection(PLAZA)
RAMP = box(TOWER_END - 16.0, PLAZA_V[0] + 3.0, TOWER_END - 2.0, PLAZA_V[0] + 10.0)
APRONS = unary_union([t.buffer(4.0, join_style="mitre") for t in TOWERS]).intersection(PLAZA)
_g1 = (TOWER_C[0][1] + TS / 2 + TOWER_C[1][1] - TS / 2) / 2
_g2 = (TOWER_C[1][1] + TS / 2 + TOWER_C[2][1] - TS / 2) / 2
PROMENADES = [box(-1e3, g - 4.5, TOWER_END, g + 4.5).intersection(PLAZA) for g in (_g1, _g2)]
CHANNELS = [box(-1e3, g - 1.1, TOWER_END - 16.0, g + 1.1).intersection(PLAZA.buffer(-5.0)) for g in (_g1, _g2)]
FOUNTAIN = Point((TOWER_C[1][0] + TS / 2 + 14.0, 150.0)).buffer(4.0)
FOUNTAIN_RING = Point(FOUNTAIN.centroid).buffer(5.6).difference(FOUNTAIN)
FOUNTAIN_COURT = box(TOWER_C[1][0] + TS / 2, 150.0 - 9.0, TOWER_END, 150.0 + 9.0).intersection(PLAZA)
PAVING = unary_union([APRONS, DROPOFF, FOUNTAIN_COURT, RAMP] + PROMENADES).intersection(PLAZA)
LAWN = PLAZA.buffer(-1.0).difference(PAVING.buffer(0.8))
PALMS = []
for g in (_g1, _g2):
    for u in np.arange(-5.0, TOWER_END - 18.0, 6.0):
        for dv in (-3.2, 3.2):
            q = Point(u, g + dv)
            if PLAZA.buffer(-1.5).contains(q) and not unary_union(TOWERS).buffer(1.0).contains(q):
                PALMS.append((q.x, q.y))
JETS = [Point(u, g).buffer(0.5) for c in CHANNELS for g in [c.centroid.y] if not c.is_empty
        for u in np.arange(c.bounds[0] + 3.0, c.bounds[2] - 2.0, 4.0)]
PLAZA_TREES = []
_ring = PLAZA_ALL.buffer(-3.0).exterior
for d in np.arange(0, _ring.length, 9.0):
    q = _ring.interpolate(d)
    if not PAVING.buffer(1.5).contains(q) and not unary_union(TOWERS).buffer(3).contains(q):
        PLAZA_TREES.append((q.x, q.y))

# --- east zone: secondary school, club + sports, utilities by the service gate, east park --------------
EZ = clean(SITE.intersection(box(EAST_START, -1e3, 1e3, 1e3)))
SOUTH_EXT = box(EAST_START, 0, SOUTH_ROAD_END, ROAD_W)      # the south road carries on into the east zone
_turn = Point((SOUTH_ROAD_END, ROAD_W / 2 + 4.0)).buffer(11.0).intersection(SITE)
SOUTH_EXT = unary_union([SOUTH_EXT, _turn])
EZ_ = clean(EZ.difference(SOUTH_EXT))
_w = clean(EZ_.intersection(box(-1e3, -1e3, 770.0, 1e3)))
_e = clean(EZ_.difference(_w))
UT, _w = cut(_w, 2300, "v", "min")
SERV["WATER"], ut = cut(UT, 1000, "u", "min")
SERV["POWER"], SERV["WASTE"] = cut(ut, 1000, "u", "min")
# the secondary school at the top (entrance + drop-off on the last cross street); the garden between it and
# the utilities carries the green walk on from quarter 4 to the east park
SERV["SECONDARY"], _w = cut(_w, 5000, "v", "max")
OPEN["G_SEC"] = _w
EAST_PARK = _e                  # the club was dropped from the programme (client, 2026-10-21): its land is park
UTILITIES = ("WATER", "POWER", "WASTE")

# --- roads: what is left inside the site ------------------------------------------------------------------
PARTS = (VILLAS + HOUSES + BITS + list(PARKS.values()) + list(SERV.values()) + list(OPEN.values())
         + [FORECOURT, CIVIC_GARDEN, TZ, EZ_])
ROADS = unary_union([p for p in polys(SITE.difference(unary_union(PARTS))) if p.area > 30])

# --- gates: only two, both on the long sides ---------------------------------------------------------------
GATE_U = (sa + sb_) / 2                    # main gate on the north road, on the axis of the civic spine
GATE = LineString([(GATE_U - 9, north_v(GATE_U - 9) - 0.3), (GATE_U + 9, north_v(GATE_U + 9) - 0.3)])
SGATE_U = EAST_START + 12.0                # service / emergency gate on the south road, by the utilities
SGATE = LineString([(SGATE_U - 6, 0.3), (SGATE_U + 6, 0.3)])

# --- numbers --------------------------------------------------------------------------------------------
FLOORS, FLATS_PER_FLOOR = 20, 4
N_APTS = len(TOWERS) * FLOORS * FLATS_PER_FLOOR
PARK_NEED = math.ceil(N_APTS * 1.5)


def total(gs):
    return sum(g.area for g in gs)


GARDENS = [OPEN["G_SCHOOL"], OPEN["G_SEC"], OPEN["G_HEALTH"], CIVIC_GARDEN]
POCKET = [PARKS[k] for k in PARKS]
BIG = [TOWER_PARK_N, TOWER_PARK_S, EAST_PARK]
GREEN = POCKET + BIG + GARDENS + BITS
LANDUSE = [
    (f"Villas 400 m2 ({len(VILLAS)}) - فلل 400 م2", total(VILLAS)),
    (f"Houses 240 m2 ({len(HOUSES)}) - دور 240 م2", total(HOUSES)),
    (f"Towers ({len(TOWERS)}) + plaza - الأبراج والبلازا", PLAZA_ALL.area),
    ("Community services - الخدمات", total(SERV[k] for k in SERV if k not in UTILITIES)),
    ("Utilities - المرافق الفنية", total(SERV[k] for k in UTILITIES)),
    ("Parks + gardens - الحدائق والمتنزهات", total(GREEN)),
    ("Civic forecourt + parking - الساحة المدنية والموقف", FORECOURT.area + OPEN["PARK_MALL"].area),
    ("Roads - الشوارع", ROADS.area),
]

if __name__ == "__main__":
    print("cross", CROSS, "east", EAST_START)
    for q in QPLOTS:
        print(q, len(QPLOTS[q]), round(PARKS[q].area))
    for n, a in LANDUSE:
        print(f"{n:<55s}{a:>9,.0f} {a / SITE.area * 100:5.1f}")
    print("sum", sum(a for _, a in LANDUSE), SITE.area)
    for k, g in SERV.items():
        print(k, round(g.area))
    print("forecourt", round(FORECOURT.area), "civic garden", round(CIVIC_GARDEN.area), "EZ park", round(EAST_PARK.area))
