"""Master plan proposal A - "the axis" (المحور) for the Shallalat residential complex, plot 157 / 53 Baybokht.

All design geometry is laid out in a local frame tied to the plot:
  x = metres along the north edge from corner Q2 towards Q3 (WNW -> ESE)
  y = metres perpendicular to the north edge, into the plot
and transformed to UTM 38S on output. The plot boundary is the announcement-matching net polygon Q1..Q4.
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
_q1, _q4 = loc(Q[0]), loc(Q[3])


def ys(x):
    """y of the south edge at x."""
    return _q1[1] + (x - _q1[0]) * (_q4[1] - _q1[1]) / (_q4[0] - _q1[0])


def clip(g):
    return g.intersection(SITE)


# ---------------------------------------------------------------- existing context (from the site plan)
# cross road centreline, traced from the cadastral scan (public road, kept)
C0, C1 = (139.962, -2.042), (217.906, 275.734)
CD = np.subtract(C1, C0) / np.linalg.norm(np.subtract(C1, C0))
CP = np.array([CD[1], -CD[0]])  # perpendicular pointing east (+x)


def cross_strip(a, b, y0=-60, y1=380):
    """Band between offsets a and b (m, east positive) from the cross road centreline."""
    p0 = np.add(C0, CD * (y0 - C0[1]) / CD[1])
    p1 = np.add(C0, CD * (y1 - C0[1]) / CD[1])
    return Polygon([tuple(p0 + a * CP), tuple(p1 + a * CP), tuple(p1 + b * CP), tuple(p0 + b * CP)])


CROSS_W = 12.0
WC = LineString([(752, 380), (748, 314), (747, 253), (745, 187), (737, 112), (719, 53), (716, -8), (740, -93)])
TREES_EXIST = [(93, 225), (80, 158), (94, 95), (132, 236), (124, 171), (135, 105), (109, 55)]

# ---------------------------------------------------------------- design parameters
Y_BLVD = (74.0, 98.0)  # 24 m boulevard, parallel to the north edge
GATE_X = 200.0  # main gate on the north road, ~200 m from the west end
RB_C, RB_R, RB_ISLAND = (GATE_X, 86.0), 25.0, 14.0  # roundabout at the head of the axis
SERVICE_X = (452.0, 468.0)  # 16 m service street at mid-axis
VILLA = (16.0, 25.0)  # 400 m2
HOUSE = (10.0, 20.0)  # 200 m2
LOCAL_W = 12.0
S0 = Y_BLVD[1] + 3  # 3 m planted verge south of the boulevard

# ---------------------------------------------------------------- roads
cross_row = clip(cross_strip(-CROSS_W / 2, CROSS_W / 2))
cross_buffer = clip(unary_union([cross_strip(CROSS_W / 2, CROSS_W / 2 + 4), cross_strip(-CROSS_W / 2 - 4, -CROSS_W / 2)]))
blvd_end = 878.0
boulevard = clip(box(GATE_X, Y_BLVD[0], blvd_end, Y_BLVD[1]))
turning = Point(blvd_end, sum(Y_BLVD) / 2).buffer(17)
rb_outer = Point(RB_C).buffer(RB_R)
rb_island = Point(RB_C).buffer(RB_ISLAND)
gate_street = box(GATE_X - 12, 0, GATE_X + 12, RB_C[1])
gate_median = box(GATE_X - 2, 0, GATE_X + 2, 40)
blvd_median = box(GATE_X + RB_R, 84.0, blvd_end - 17, 88.0)  # 4 m planted median
main_roads = clip(unary_union([boulevard, turning, rb_outer, gate_street])).difference(rb_island).difference(
    gate_median).difference(blvd_median)
service_street = clip(box(SERVICE_X[0], 0, SERVICE_X[1], 400)).difference(main_roads)
west_street = clip(cross_strip(10, 22, 70, 380))  # skewed local street along the cross-road buffer

# ---------------------------------------------------------------- valley / Shallalat garden
valley_garden = clip(unary_union([WC.buffer(28), Point(738, 148).buffer(48)]))
valley_free = valley_garden.difference(main_roads)
lake = Polygon([(720, 120), (738, 110), (756, 122), (760, 150), (748, 172), (728, 170), (716, 150)]).buffer(2)
x_valley_w = lambda y: valley_garden.bounds[0]

# ---------------------------------------------------------------- west part (public, west of the cross road)
west_part = clip(cross_strip(-1000, -CROSS_W / 2 - 4))
west_road = clip(box(0, 136, 400, 148)).intersection(west_part)
tower_zone = west_part.intersection(box(-10, -10, 400, 136))
TOWER_SIDE = 28.3  # ~800 m2 typical floor
towers = [Point(c).buffer(TOWER_SIDE / 2, cap_style=3) for c in [(45.0, 46.0), (107.0, 46.0)]]
tower_podium = [t.buffer(6, join_style=2) for t in towers]
tower_drive = west_part.intersection(unary_union([box(25, 92, 400, 100), box(39, 66, 51, 92), box(101, 66, 113, 92)]))
basement = box(20, 18, 132, 80)
club = west_part.intersection(box(52, 154, 132, 204))
health = west_part.intersection(box(138, 154, 400, 196))
police = west_part.intersection(box(108, 238, 158, 400))
civil_def = west_part.intersection(box(164, 228, 400, 400))

# ---------------------------------------------------------------- services east of the cross road
gate_admin = clip(box(-10, 0, GATE_X - 12, 68)).intersection(cross_strip(CROSS_W / 2 + 4, 1000))
market = box(392, 6, 452, 68)
mosque = box(468, 6, 512, 68)
kg = box(362, S0, 452, 144)
primary = clip(box(362, 144, 452, 400))
intermediate = box(468, S0, 550, 163)
preparatory = clip(box(468, 163, 550, 400))
substation = clip(box(856, 0, 920, 50))
sewage = clip(box(866, S0, 920, 400))
utilities = sewage
desal = west_part.intersection(box(30, 232, 104, 400))
public_garden = west_part.difference(unary_union([tower_zone, west_road, club, health, police, civil_def, desal]))

# ---------------------------------------------------------------- residential zones and street schemes
north_buffer = clip(box(-10, 0, 1000, 6)).difference(unary_union([gate_street, service_street, substation]))
CONN = {  # 12 m connectors linking local streets to the boulevard ("blocks every ~150 m")
    "N1": box(298, 31, 310, Y_BLVD[0]),
    "N2": box(600, 31, 612, Y_BLVD[0]),
    "S1": box(350, Y_BLVD[1], 362, 400),
    "S2": box(550, Y_BLVD[1], 562, 400),
    "S3": box(640, Y_BLVD[1], 652, 400),
    "E1": box(806, 31, 818, Y_BLVD[0]),
    "E2": box(790, Y_BLVD[1], 802, 400),
}
reserved = unary_union([cross_row, cross_buffer, west_part, main_roads, service_street, west_street, valley_garden,
                        gate_admin, market, mosque, kg, primary, intermediate, preparatory, substation,
                        utilities.buffer(18, join_style=2), north_buffer])

# (zone polygon, plot type, [(street y0, y1)], [(row y0, row y1, front street index)])
N_STREETS = [(31, 43)]
V_N_ROWS = [(6, 31, 0), (43, 68, 0)]
H_N_ROWS = [(11, 31, 0), (43, 63, 0)]
V_S_STREETS = [(S0 + 25, S0 + 37), (S0 + 87, S0 + 99), (S0 + 149, S0 + 161)]
V_S_ROWS = [(S0, S0 + 25, 0), (S0 + 37, S0 + 62, 0), (S0 + 62, S0 + 87, 1), (S0 + 99, S0 + 124, 1),
            (S0 + 124, S0 + 149, 2), (S0 + 161, S0 + 186, 2)]
H_S_STREETS = [(S0 + 20, S0 + 32), (S0 + 72, S0 + 84), (S0 + 124, S0 + 136)]
H_S_ROWS = [(S0, S0 + 20, 0), (S0 + 32, S0 + 52, 0), (S0 + 52, S0 + 72, 1), (S0 + 84, S0 + 104, 1),
            (S0 + 104, S0 + 124, 2), (S0 + 136, S0 + 156, 2)]

ZONES = {
    "N-W": (box(GATE_X + 12, 6, 392, 68), "V", N_STREETS, V_N_ROWS, ["N1"]),
    "N-E": (box(512, 6, 712, 68), "V", N_STREETS, V_N_ROWS, ["N2"]),
    "S-W": (box(150, S0, 350, 400), "V", V_S_STREETS, V_S_ROWS, ["S1"]),
    "S-E": (box(562, S0, 760, 400), "H", H_S_STREETS, H_S_ROWS, ["S2", "S3"]),
    "E-N": (box(725, 6, 856, 68), "H", N_STREETS, H_N_ROWS, ["E1"]),
    "E-S": (box(760, S0, 860, 400), "H", H_S_STREETS, H_S_ROWS, ["E2"]),
}

plots = {"V": [], "H": []}
local_streets, connectors, zone_polys = [], [], {}
for zname, (zbox, ptype, streets, rows, conns) in ZONES.items():
    zone = clip(zbox).difference(reserved)
    zone_polys[zname] = zone
    cpoly = unary_union([CONN[c] for c in conns]) if conns else Polygon()
    # streets: the longest run of x where the full street width lies inside the zone
    st_polys = []
    for (a, b) in streets:
        xs = [x for x in np.arange(zbox.bounds[0], zbox.bounds[2], 1.0)
              if zone.buffer(0.01).contains(box(x, a, x + 1, b))]
        if len(xs) < 20:
            st_polys.append(None)
            continue
        st_polys.append(box(min(xs), a, max(xs) + 1, b))
    used = [s for s in st_polys if s is not None]
    st_union = unary_union(used) if used else Polygon()
    # connectors stop at the deepest street they meet
    for c in conns:
        cb = CONN[c]
        hit = [s for s in used if s.intersects(cb)]
        if hit:
            y_top, y_bot = cb.bounds[1], cb.bounds[3]
            if y_top >= Y_BLVD[1]:  # south connector, runs down from the boulevard
                y_bot = max(s.bounds[3] for s in hit)
            else:
                y_top = min(s.bounds[1] for s in hit)
            connectors.append(box(cb.bounds[0], y_top, cb.bounds[2], y_bot).intersection(SITE))
    conn_here = unary_union(connectors) if connectors else Polygon()
    w, d = VILLA if ptype == "V" else HOUSE
    free = zone.difference(conn_here).buffer(0.01)
    for (r0, r1, si) in rows:
        st = st_polys[si] if si < len(st_polys) else None
        if st is None:
            continue
        # x columns (0.5 m) where both the plot strip and its front street are clear, packed run by run
        step = 0.5
        ok = [x for x in np.arange(zbox.bounds[0], zbox.bounds[2], step)
              if free.contains(box(x, r0, x + step, r1)) and st.buffer(0.01).contains(box(x, st.bounds[1], x + step, st.bounds[3]))]
        runs, start = [], None
        for i, x in enumerate(ok):
            if start is None:
                start = x
            if i + 1 == len(ok) or ok[i + 1] - x > step + 1e-6:
                runs.append((start, x + step))
                start = None
        for a, b in runs:
            n = int((b - a + 1e-6) // w)
            for k in range(n):
                plots[ptype].append(box(a + k * w, r0, a + (k + 1) * w, r1))
    local_streets += [s.intersection(zone).difference(conn_here) for s in used]

# west street only as far south as the deepest street of zone S-W
sw_streets = [s for s in local_streets if s.intersects(zone_polys["S-W"]) and s.bounds[1] > 100]
if sw_streets:
    west_street = west_street.intersection(box(-10, 0, 1000, max(s.bounds[3] for s in sw_streets)))
local_streets = [s for s in local_streets if not s.is_empty]
connectors = [c.difference(main_roads) for c in connectors]

# turning heads at the dead ends of local streets that stop at the valley garden
turn_heads = []
for s in local_streets:
    x1 = s.bounds[2]
    if valley_garden.distance(box(x1 - 1, s.bounds[1], x1, s.bounds[3])) < 3:
        turn_heads.append(Point(x1 - 8, (s.bounds[1] + s.bounds[3]) / 2).buffer(9).intersection(SITE).difference(
            valley_garden))

ALL_ROADS = unary_union([main_roads, service_street, west_street, cross_row, tower_drive, west_road]
                        + local_streets + connectors + turn_heads)

# orchard garden: the wedge south of the last villa rows in S-W
built = unary_union(plots["V"] + plots["H"] + [ALL_ROADS])
sw_left = zone_polys["S-W"].difference(built)
orchard = max(sw_left.geoms, key=lambda g: g.area) if sw_left.geom_type == "MultiPolygon" else sw_left

# green pockets left inside the housing zones (S-W wedge = orchard garden)
pockets = []
for zname, z in zone_polys.items():
    left = z.difference(built)
    for g in (left.geoms if hasattr(left, "geoms") else [left]):
        if g.area > 150 and not g.equals(orchard):
            pockets.append(g)
se_wedge = max((g for g in pockets if g.intersects(zone_polys["S-E"])), key=lambda g: g.area)
sports = west_part.intersection(box(40, 208, 135, 228))  # youth sports court
public_garden = public_garden.difference(sports)


playgrounds = [box(296, 229, 344, 246).intersection(orchard), box(604, 187, 640, 201).intersection(se_wedge),
               box(691, 10, 709, 44).intersection(valley_free)]

SERVICES = {
    "POLICE": ("مركز شرطة", police, 1200),
    "CIVIL DEFENCE": ("دفاع مدني", civil_def, 2000),
    "HEALTH CENTRE": ("مركز صحي", health, 1500),
    "SOCIAL CLUB": ("النادي الاجتماعي", club, 4000),
    "GATE & ADMIN": ("البوابة والإدارة", gate_admin, 1000),
    "MARKET": ("السوق", market, 3500),
    "MOSQUE": ("الجامع", mosque, 1500),
    "KINDERGARTEN": ("روضة", kg, 3600),
    "PRIMARY SCHOOL": ("مدرسة ابتدائية", primary, 7700),
    "INTERMEDIATE SCHOOL": ("مدرسة متوسطة", intermediate, 4800),
    "PREPARATORY SCHOOL": ("مدرسة إعدادية", preparatory, 4100),
    "SUBSTATION 33/11kV": ("محطة كهرباء", substation, 2500),
    "DESALINATION": ("محطة تحلية", desal, 2500),
    "SEWAGE & WASTE": ("معالجة المجاري والنفايات", sewage, 1500),
    "YOUTH SPORTS": ("ساحة رياضية للشباب", sports, 1500),
}

if __name__ == "__main__":
    print("villas", len(plots["V"]), "houses", len(plots["H"]))
    for k, (ar, g, need) in SERVICES.items():
        print(f"{k:22s} {g.area:8.0f} need {need}")
    print("tower zone", tower_zone.area, "west part", west_part.area, "valley", valley_garden.area, "orchard", orchard.area)
    for z, p in zone_polys.items():
        print(z, round(p.area))
