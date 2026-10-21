"""Master plan proposal A2 rev. 1 - "the central boulevard" (البوليفارد الوسطي) on the client's new programme
(2026-10-21): 80 villas 400 m2, 88 houses 240 m2, 3 towers x 20 floors (240 flats) on a plaza with basement parking,
and the client's service areas; land left over goes to green. Concept unchanged from A2, a revision of proposal A for the Shallalat
residential complex, plot 157 / 53 Baybokht, after the client's reference render (2026-10-21):
the boulevard runs down the middle of the plot from a roundabout on the cross road to the Shallalat garden,
the two towers stand in an orchard west of the cross road, the service street with the market, mosque and health
centre sits mid-axis on the north side, the schools face it on the south side. The watercourse is ignored.

Local frame (as in proposal A): x = metres along the north edge from Q2 towards Q3, y = metres into the plot.
"""
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

Q = [(338955.19, 4035466.71), (339030.78, 4035766.16), (339833.37, 4035331.92), (339749.71, 4035202.20)]
P = [(338954.0, 4035462.0), (339032.0, 4035771.0), (339836.0, 4035336.0), (339747.0, 4035198.0)]
ANNOUNCED_M2 = 199175

O = np.array(Q[1])
EV = np.subtract(Q[2], Q[1]) / np.linalg.norm(np.subtract(Q[2], Q[1]))
NV = np.array([-EV[1], EV[0]])
if np.dot(np.mean(Q, axis=0) - O, NV) < 0:
    NV = -NV


def loc(p):
    d = np.subtract(p, O)
    return float(d @ EV), float(d @ NV)


def utm_xy(x, y):
    return tuple(O + x * EV + y * NV)


def to_utm(g):
    return affinity.affine_transform(g, [EV[0], NV[0], EV[1], NV[1], O[0], O[1]])


SITE = Polygon([loc(q) for q in Q])
INNER = SITE.buffer(-3, join_style=2)  # 3 m planted strip inside the boundary wall
_q1, _q4 = loc(Q[0]), loc(Q[3])


def ys(x):
    """y of the south edge at x."""
    return _q1[1] + (x - _q1[0]) * (_q4[1] - _q1[1]) / (_q4[0] - _q1[0])


def yc(x):
    """Boulevard centre line: the middle of the plot between the two long edges."""
    return ys(x) / 2


def clip(g):
    return g.intersection(SITE)


def band(x0, x1, off0, off1):
    """Strip between offsets off0 < off1 (m, + = south) from the boulevard centre line, from x0 to x1."""
    return Polygon([(x0, yc(x0) + off0), (x1, yc(x1) + off0), (x1, yc(x1) + off1), (x0, yc(x0) + off1)])


def parts(g):
    if g is None or g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon" and p.area > 0.5]


# ---------------------------------------------------------------- existing context (from the site plan)
C0, C1 = (139.962, -2.042), (217.906, 275.734)  # cross road centre line, public, kept
CD = np.subtract(C1, C0) / np.linalg.norm(np.subtract(C1, C0))
CP = np.array([CD[1], -CD[0]])  # perpendicular pointing east (+x)


def cross_strip(a, b, y0=-60, y1=380):
    p0 = np.add(C0, CD * (y0 - C0[1]) / CD[1])
    p1 = np.add(C0, CD * (y1 - C0[1]) / CD[1])
    return Polygon([tuple(p0 + a * CP), tuple(p1 + a * CP), tuple(p1 + b * CP), tuple(p0 + b * CP)])


def cross_x(y, off=0.0):
    return C0[0] + CD[0] / CD[1] * (y - C0[1]) + off / CP[0]


CROSS_W = 12.0
TREES_EXIST = [(93, 225), (80, 158), (94, 95), (132, 236), (124, 171), (135, 105), (109, 55)]

# ---------------------------------------------------------------- design parameters
VILLA = (25.0, 16.0)  # depth along x, frontage along y: 400 m2
HOUSE = (20.0, 12.0)  # 240 m2
N_VILLAS, N_HOUSES = 80, 88
N_APT = 240
LOCAL_W = 12.0
BLVD_HALF = 12.0  # 24 m: 2 x 10 m carriageway + 4 m planted median
VERGE = 2.0
RB_R, RB_ISLAND = 25.0, 14.0
X_RB = 182.0  # roundabout on the cross road at the head of the boulevard
RB_C = (cross_x(yc(X_RB)), yc(X_RB))
X_SRV = (418.0, 520.0)  # mid-axis services (north: market, mosque, health; south: schools)
SERVICE_X = (466.0, 478.0)  # 12 m service street off the boulevard (no gate on the north road)
X_END = 800.0  # the boulevard ends in a turning circle at the Shallalat garden
X_GARDEN = (800.0, 878.0)
EDGE_N, EDGE_S = -BLVD_HALF - VERGE, BLVD_HALF + VERGE

# ---------------------------------------------------------------- main roads
rb_outer = Point(RB_C).buffer(RB_R)
rb_island = Point(RB_C).buffer(RB_ISLAND)
blvd = band(RB_C[0], X_END, -BLVD_HALF, BLVD_HALF)
turning = Point(X_END, yc(X_END)).buffer(18)
blvd_median = band(RB_C[0] + RB_R + 8, X_END - 18, -2, 2)
gate_island = band(RB_C[0] + RB_R + 1, RB_C[0] + RB_R + 7, -2, 2)  # gatehouse island in the median
main_roads = clip(unary_union([blvd, turning, rb_outer])).difference(rb_island).difference(blvd_median).difference(gate_island)
verges = clip(band(RB_C[0], X_END, -BLVD_HALF - VERGE, BLVD_HALF + VERGE)).difference(unary_union([blvd, turning, rb_outer]))
cross_row = clip(cross_strip(-CROSS_W / 2, CROSS_W / 2)).difference(rb_outer)
cross_buffer = clip(unary_union([cross_strip(CROSS_W / 2, CROSS_W / 2 + 4), cross_strip(-CROSS_W / 2 - 4, -CROSS_W / 2)])).difference(rb_outer)
service_street = clip(box(SERVICE_X[0], 0, SERVICE_X[1], yc(470) - BLVD_HALF + 1)).difference(main_roads)

def cut(poly, target, axis="x", lo=-100.0, hi=1100.0, from_low=True):
    """Part of poly on one side of a line x=c (or y=c) with an area of target m2 (bisection)."""
    for _ in range(60):
        c = (lo + hi) / 2
        part = poly.intersection(box(-1e4, -1e4, c, 1e4) if axis == "x" else box(-1e4, -1e4, 1e4, c)) if from_low else \
            poly.intersection(box(c, -1e4, 1e4, 1e4) if axis == "x" else box(-1e4, c, 1e4, 1e4))
        if (part.area < target) == from_low:
            lo = c
        else:
            hi = c
    return part, c


# ---------------------------------------------------------------- west part: 3 towers on a plaza in the orchard
west_part = clip(cross_strip(-1000, -CROSS_W / 2 - 4))
_xt = 115.0
TOWER_SIDE = 28.3  # ~800 m2 typical floor, 4 flats
TOWER_C = [(_xt, yc(_xt) - 55), (_xt, yc(_xt) + 55), (62.0, yc(62.0))]  # A, B flank the axis, C closes it
towers = [Point(c).buffer(TOWER_SIDE / 2, cap_style=3) for c in TOWER_C]
tower_podium = [t.buffer(6, join_style=2) for t in towers]
tower_drive = west_part.intersection(LineString([(_xt + 20, yc(_xt + 20)), RB_C]).buffer(6, cap_style=2))
tower_loop = west_part.intersection(Point(_xt + 8, yc(_xt + 8)).buffer(16).difference(Point(_xt + 8, yc(_xt + 8)).buffer(6)))
lagoon = band(78, _xt - 12, -5, 5).union(Point(_xt - 10, yc(_xt - 10)).buffer(7))  # water channel on the axis
basement = box(48, yc(_xt) - 62, _xt + 22, yc(_xt) + 62)  # ~360 cars under the plaza
west_lane_n = west_part.intersection(box(-10, 38, 400, 44))  # back lane from the cross road
police, _ = cut(west_part.intersection(box(-10, 3, 400, 38)), 600, "x")
civil_def, _ = cut(west_part.intersection(box(-10, 3, 400, 38)), 600, "x", from_low=False)
west_garden, _y_wg = cut(west_part.intersection(INNER), 5000, "y", from_low=False)  # club dropped by the client: garden
tower_zone = west_part.difference(unary_union([police, civil_def, west_garden, west_lane_n, box(-10, -10, 400, 38)]))

# ---------------------------------------------------------------- mid-axis services (client areas)
N_EDGE = lambda x: yc(x) + EDGE_N  # noqa: E731
S_EDGE = lambda x: yc(x) + EDGE_S  # noqa: E731
north_srv = clip(Polygon([(X_SRV[0], 3), (X_SRV[1], 3), (X_SRV[1], N_EDGE(X_SRV[1])), (X_SRV[0], N_EDGE(X_SRV[0]))]))
_nw = north_srv.intersection(box(-10, -10, SERVICE_X[0], 400))
mall, _y_mall = cut(_nw, 3000, "y")
_rest = _nw.intersection(box(-10, _y_mall + 6, 1000, 400))
health, _ = cut(_rest, 1000, "y", from_low=False)
srv_lane = _nw.intersection(box(-10, _y_mall, 1000, _y_mall + 6))
_ne = north_srv.intersection(box(SERVICE_X[1], -10, 1000, 400))
mosque, _ = cut(_ne, 2000, "y", from_low=False)
srv_parking = _ne.intersection(box(-10, -10, 1000, 30)).difference(mosque)
mosque_plaza = _ne.difference(unary_union([mosque, srv_parking]))
srv_green = _nw.difference(unary_union([mall, health, srv_lane]))
X_SCH = (412.0, 528.0)
south_srv = clip(Polygon([(X_SCH[0], S_EDGE(X_SCH[0])), (X_SCH[1], S_EDGE(X_SCH[1])),
                          (X_SCH[1], 400), (X_SCH[0], 400)])).intersection(INNER)
school_st = clip(Polygon([(460, S_EDGE(460)), (472, S_EDGE(472)), (472, 400), (460, 400)])).intersection(INNER)
_sw = south_srv.intersection(box(-10, -10, 460, 400))
primary, _ = cut(_sw, 3000, "y", from_low=False)
kindergarten, _ = cut(_sw.difference(primary), 1500, "y")
secondary, _ = cut(south_srv.intersection(box(472, -10, 1000, 400)), 5000, "y", from_low=False)
school_green = south_srv.difference(unary_union([primary, kindergarten, secondary, school_st]))

# ---------------------------------------------------------------- east end: Shallalat garden + utilities
shallalat_garden = clip(box(X_GARDEN[0], -10, X_GARDEN[1], 400)).difference(turning)
lake = Polygon([(812, 0), (832, -8), (850, 2), (852, 22), (838, 32), (818, 28), (808, 14)])
lake = affinity.translate(lake, 4, yc(830) - 12).intersection(shallalat_garden.buffer(-8))
cascade_axis = band(X_END + 18, 812, -5, 5)
util = clip(box(X_GARDEN[1], -10, 1000, 400)).intersection(INNER)
waste, _y_w = cut(util, 300, "y", from_low=False)
_u = util.difference(waste)
desal, _ = cut(_u, 1000, "y", from_low=False)  # water station
_u = _u.difference(desal)
substation, _ = cut(_u, 1000, "y", from_low=False)  # power station
util_green = _u.difference(substation)

# ---------------------------------------------------------------- housing: comb of 12 m streets off the boulevard
reserved = unary_union([cross_row, cross_buffer, west_part, main_roads, verges, service_street, north_srv, south_srv,
                        shallalat_garden, clip(box(X_GARDEN[1], -10, 1000, 400)), rb_outer.buffer(4)])
north_half = Polygon([(-50, -50), (1000, -50), (1000, yc(1000) + EDGE_N), (-50, yc(-50) + EDGE_N)])
south_half = Polygon([(-50, 500), (1000, 500), (1000, yc(1000) + EDGE_S), (-50, yc(-50) + EDGE_S)])


def comb(x0, x1, side, ptype, keep_out=None):
    """Housing between x0 and x1 on one side of the boulevard: a single row backing onto the west neighbour, then
    pairs of back-to-back rows between 12 m streets running from the boulevard to the boundary wall. Streets are
    paired into loops by a 12 m link along the wall; an unpaired last street ends in a turning circle. Plots are
    packed from the wall towards the boulevard."""
    half = north_half if side == "N" else south_half
    zone = INNER.intersection(half).intersection(box(x0, -50, x1, 500)).difference(reserved)
    if keep_out is not None:
        zone = zone.difference(keep_out)
    d, f = VILLA if ptype == "V" else HOUSE
    xs_st, x, rows = [], x0, [(x0, x0 + d)]
    x += d
    while x + LOCAL_W + d <= x1 + 0.01:
        xs_st.append(x)
        x += LOCAL_W
        rows.append((x, x + d))
        x += d
        if x + 2 * d + LOCAL_W <= x1 + 0.01:
            rows.append((x, x + d))
            x += d
        else:
            break
    streets = []
    for xs in xs_st:
        a, b = xs, xs + LOCAL_W
        if side == "N":
            s = Polygon([(a, 3), (b, 3), (b, yc(b) - BLVD_HALF + 0.5), (a, yc(a) - BLVD_HALF + 0.5)])
        else:
            s = Polygon([(a, yc(a) + BLVD_HALF - 0.5), (b, yc(b) + BLVD_HALF - 0.5), (b, ys(b) - 3), (a, ys(a) - 3)])
        streets.append(s.difference(reserved.difference(verges)).buffer(0))
    wall_band = INNER.difference(INNER.buffer(-LOCAL_W, join_style=2)).intersection(half)
    links = []
    for i in range(0, len(streets) - 1, 2):
        links.append(wall_band.intersection(box(streets[i].bounds[0], -50, streets[i + 1].bounds[2], 500)))
    if len(streets) % 2 == 1:
        s = streets[-1]
        cx = (s.bounds[0] + s.bounds[2]) / 2
        cy = 3 + 10 if side == "N" else ys(cx) - 3 - 10
        links.append(Point(cx, cy).buffer(10).intersection(INNER))
    free = zone.difference(unary_union(streets + links)).buffer(0.01)
    plots = []
    for (a, b) in rows:
        col = free.intersection(box(a, -50, b, 500))
        if col.is_empty:
            continue
        ylo, yhi = col.bounds[1], col.bounds[3]
        if side == "N":
            y = ylo
            while y + f <= yhi + 0.01:
                p = box(a, y, b, y + f)
                if free.contains(p):
                    plots.append(p)
                    y += f
                else:
                    y += 0.5
        else:
            y = yhi
            while y - f >= ylo - 0.01:
                p = box(a, y - f, b, y)
                if free.contains(p):
                    plots.append(p)
                    y -= f
                else:
                    y -= 0.5
    return plots, streets, links, zone


X_W_N = cross_x(3, CROSS_W / 2 + 4)
X_W_S = cross_x(yc(260) + EDGE_S, CROSS_W / 2 + 4)
_ga_y = yc(200) + EDGE_S
gate_admin = clip(Polygon([(cross_x(_ga_y, CROSS_W / 2 + 4) + 1, _ga_y), (X_W_S + 22, yc(X_W_S + 22) + EDGE_S),
                           (X_W_S + 22, _ga_y + 46), (cross_x(_ga_y + 46, CROSS_W / 2 + 4) + 1, _ga_y + 46)])).difference(reserved)


def build(xv):
    """Villas west of the services and east of them up to xv, then houses up to the Shallalat garden."""
    bands = [(X_W_N, X_SRV[0], "N", "V"), (X_W_S, X_SCH[0], "S", "V"),
             (X_SRV[1], xv, "N", "V"), (X_SCH[1], xv, "S", "V"),
             (xv, X_GARDEN[0], "N", "H"), (xv, X_GARDEN[0], "S", "H")]
    out = {"V": [], "H": []}
    sts, lks = [], []
    for x0, x1, side, pt in bands:
        if x1 - x0 < 30:
            continue
        p, s_, lk, _z = comb(x0, x1, side, pt, gate_admin)
        out[pt] += p
        sts += s_
        lks += lk
    return out, sts, lks


XV = next(x for x in np.arange(X_SCH[1], X_GARDEN[0], 2.0) if len(build(x)[0]["V"]) >= N_VILLAS)
plots, local_streets, links = build(XV)
# exact programme counts: surplus plots (furthest from the boulevard head) become pocket gardens
for k, n in (("V", N_VILLAS), ("H", N_HOUSES)):
    plots[k] = sorted(plots[k], key=lambda p: (p.centroid.x > XV if k == "V" else p.centroid.x, abs(p.centroid.y - yc(p.centroid.x))))
    if k == "V":
        plots[k] = sorted(plots[k], key=lambda p: (p.centroid.x > XV, -p.centroid.x if p.centroid.x > XV else 0, 0))[::1]
SURPLUS = {"V": plots["V"][N_VILLAS:], "H": plots["H"][N_HOUSES:]}
plots = {"V": plots["V"][:N_VILLAS], "H": plots["H"][:N_HOUSES]}
SHORT = {"V": N_VILLAS - len(plots["V"]), "H": N_HOUSES - len(plots["H"])}

ALL_ROADS = unary_union([main_roads, service_street, cross_row, tower_drive, tower_loop, school_st, west_lane_n]
                        + local_streets + links)
playgrounds = [box(70, yc(70) + 30, 96, yc(70) + 46).intersection(tower_zone),
               box(836, yc(836) + 30, 862, yc(836) + 48).intersection(shallalat_garden)]

SERVICES = {
    "GATEHOUSE": ("بيت البوابة", gate_admin, 0),
    "POLICE": ("مركز شرطة", police, 600),
    "CIVIL DEFENCE": ("دفاع مدني", civil_def, 600),
    "MALL": ("المول", mall, 3000),
    "HEALTH CENTRE": ("مركز صحي", health, 1000),
    "MOSQUE": ("الجامع", mosque, 2000),
    "KINDERGARTEN": ("روضة", kindergarten, 1500),
    "PRIMARY SCHOOL": ("مدرسة ابتدائية", primary, 3000),
    "SECONDARY SCHOOL": ("مدرسة ثانوية (متوسطة + إعدادية)", secondary, 5000),
    "WATER STATION": ("محطة ماء", desal, 1000),
    "POWER STATION": ("محطة كهرباء", substation, 1000),
    "WASTE": ("النفايات", waste, 300),
}

if __name__ == "__main__":
    print("XV", XV, "villas", len(plots["V"]), "houses", len(plots["H"]), "short", SHORT,
          "surplus", {k: len(v) for k, v in SURPLUS.items()})
    for k, (a, g, need) in SERVICES.items():
        print(f"{k:20s} {g.area:8.0f} need {need}")
    print("tower zone", round(tower_zone.area), "garden", round(shallalat_garden.area))
