"""Site model for plot 157 / district 53 Baybokht, in a local frame on the plot's long axis.

Local frame: origin at corner Q1, +x along the plot centreline (west end -> east end),
+y across the plot towards the north long side (Q2-Q3). All design geometry is drawn in
this frame (metres) and transformed back to UTM 38S for the DXF.
"""
import math

from shapely.geometry import LineString, Point, Polygon
from shapely import affinity

# announced boundary (matches 199,175 m2), UTM WGS84 38S
Q = {
    "Q1": (338955.19, 4035466.71),
    "Q2": (339030.78, 4035766.16),
    "Q3": (339833.37, 4035331.92),
    "Q4": (339749.71, 4035202.20),
}
# approximate features traced from the scanned cadastral map (layers *_APPROX)
ROAD_S = ((339802.0, 4035173.4), (338895.2, 4035475.3))   # ~12 m, along Q4-Q1
ROAD_N = ((338982.1, 4035804.8), (339891.6, 4035312.7))   # ~12 m, along Q2-Q3
ROAD_X = ((339090.5, 4035416.6), (339155.5, 4035704.2))   # cross road, ~10 m
WADI = [(339539.0, 4035134.2), (339567.7, 4035188.2), (339596.8, 4035246.8), (339626.0, 4035316.8),
        (339637.9, 4035377.3), (339663.8, 4035432.3), (339726.0, 4035495.8), (339782.0, 4035560.1)]
TREES = [(339005.0, 4035524.0), (339025.6, 4035589.3), (339068.2, 4035637.7), (339035.0, 4035495.9),
         (339058.6, 4035556.7), (339099.5, 4035609.0), (339100.1, 4035665.9)]

LAT = 36.46  # site latitude (deg N), from UTM 38S E339300 N4035500

# centreline of the plot: midpoint of the west end edge -> midpoint of the east end edge
_W = ((Q["Q1"][0] + Q["Q2"][0]) / 2, (Q["Q1"][1] + Q["Q2"][1]) / 2)
_E = ((Q["Q3"][0] + Q["Q4"][0]) / 2, (Q["Q3"][1] + Q["Q4"][1]) / 2)
AXIS_ANGLE = math.degrees(math.atan2(_E[1] - _W[1], _E[0] - _W[0]))  # about -23.6 deg
AXIS_BEARING = (90 - AXIS_ANGLE) % 360                               # about 113.6 deg (ESE)
ORIGIN = Q["Q1"]


def to_local(p):
    x, y = p[0] - ORIGIN[0], p[1] - ORIGIN[1]
    a = math.radians(-AXIS_ANGLE)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


def to_world(p):
    a = math.radians(AXIS_ANGLE)
    x, y = p
    return (ORIGIN[0] + x * math.cos(a) - y * math.sin(a), ORIGIN[1] + x * math.sin(a) + y * math.cos(a))


def geom_to_world(g):
    a = math.radians(AXIS_ANGLE)
    m = [math.cos(a), -math.sin(a), math.sin(a), math.cos(a), ORIGIN[0], ORIGIN[1]]
    return affinity.affine_transform(g, m)


SITE = Polygon([to_local(Q[k]) for k in ("Q1", "Q2", "Q3", "Q4")])
ROAD_S_L = LineString([to_local(p) for p in ROAD_S])
ROAD_N_L = LineString([to_local(p) for p in ROAD_N])
ROAD_X_L = LineString([to_local(p) for p in ROAD_X])
WADI_L = LineString([to_local(p) for p in WADI])
TREES_L = [Point(to_local(p)) for p in TREES]


def edge_y(x, side):
    """y of the south (side='s') or north (side='n') boundary at local x."""
    q1, q2, q3, q4 = (to_local(Q[k]) for k in ("Q1", "Q2", "Q3", "Q4"))
    a, b = (q1, q4) if side == "s" else (q2, q3)
    t = (x - a[0]) / (b[0] - a[0])
    return a[1] + t * (b[1] - a[1])


if __name__ == "__main__":
    print("axis angle %.2f deg, bearing %.1f deg" % (AXIS_ANGLE, AXIS_BEARING))
    print("site area %.0f m2, bounds %s" % (SITE.area, [round(v, 1) for v in SITE.bounds]))
    for k in Q:
        print(k, [round(v, 1) for v in to_local(Q[k])])
    for name, ln in (("road S", ROAD_S_L), ("road N", ROAD_N_L), ("cross road", ROAD_X_L), ("wadi", WADI_L)):
        print(name, [(round(x, 1), round(y, 1)) for x, y in ln.coords])
    print("trees", [(round(t.x, 1), round(t.y, 1)) for t in TREES_L])
    cx = ROAD_X_L.intersection(SITE)
    wx = WADI_L.intersection(SITE)
    print("cross road inside site:", [(round(x, 1), round(y, 1)) for x, y in cx.coords], "len %.1f" % cx.length)
    print("wadi inside site: len %.1f" % wx.length, [(round(x, 1), round(y, 1)) for x, y in wx.coords])
    for x in (0, 100, 140, 200, 300, 400, 500, 600, 700, 800, 850):
        print("x=%d  y_s=%.1f y_n=%.1f width=%.1f" % (x, edge_y(x, "s"), edge_y(x, "n"), edge_y(x, "n") - edge_y(x, "s")))
    print("road S offset from boundary:", round(ROAD_S_L.distance(Point(to_local(Q["Q1"]))), 1),
          round(ROAD_S_L.distance(Point(to_local(Q["Q4"]))), 1))
    print("road N offset from boundary:", round(ROAD_N_L.distance(Point(to_local(Q["Q2"]))), 1),
          round(ROAD_N_L.distance(Point(to_local(Q["Q3"]))), 1))
