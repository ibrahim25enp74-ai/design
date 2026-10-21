"""Shared design kit for the four master plan concepts.

Every concept is described with the same vocabulary (roads, parcels, residential strips) and
measured with the same metrics, so the comparison between concepts is like for like.
Units: metres, local frame of plot157.py (x along the long axis, y towards the north side).
"""
import math

import networkx as nx
from shapely import STRtree
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box
from shapely.ops import unary_union

import plot157 as P

SITE = P.SITE

# ---------------------------------------------------------------- fixed design data
LOT = {"V": (16.0, 25.0), "D": (10.0, 20.0)}          # frontage x depth (kras table 1/10)
HOUSE = {"V": (10.0, 12.0, 4.0), "D": (10.0, 12.0, 2.5)}  # footprint w x d, front setback
PERSONS = {"V": 6, "D": 6, "M2": 4, "M3": 6}           # occupancy (kras table 13)
TOWER_FLOORS, TOWER_UNITS_PER_FLOOR, TOWER_FLOOR_AREA = 19, 4, 800.0
TOWER_H = 66.0                                          # G + 19 floors at 3.3 m
TOWER_W, TOWER_D = 40.0, 20.0                            # 800 m2 plate, long side on the axis
ROAD_W = {"blvd": 24.0, "collector": 16.0, "local": 12.0, "lane": 8.0, "gate": 20.0, "public": 10.0}
MAIN_ROADS = ("blvd", "collector", "gate", "public")
WADI_HALF = 20.0                                        # assumed flood corridor: 20 m each side

SERVICES = {   # name: (area m2, arabic label, kind)
    "kg": (1800, "روضة وحضانة 1", "edu"),
    "kg2": (1800, "روضة وحضانة 2", "edu"),
    "prim": (7700, "مدرسة ابتدائية", "edu"),
    "inter": (4800, "مدرسة متوسطة", "edu"),
    "prep": (4100, "مدرسة إعدادية", "edu"),
    "health": (1500, "مركز صحي", "health"),
    "mosque": (1500, "جامع", "civic"),
    "police": (1200, "مركز شرطة", "civic"),
    "cd": (2000, "دفاع مدني", "civic"),
    "market": (3500, "سوق ومقاهٍ ومطاعم", "civic"),
    "admin": (1000, "إدارة وبريد وأمن", "civic"),
    "club": (4000, "النادي الاجتماعي", "civic"),
    "water": (2500, "محطة تحلية ومعالجة ماء", "util"),
    "power": (2500, "محطة كهرباء 33/11", "util"),
    "sewage": (1500, "مجاري ونفايات", "util"),
}
# maximum walking distance (kras tables 3 and 6)
WALK_MAX = {"kg": 300, "prim": 500, "inter": 500, "market": 500, "mosque": 800, "health": 800, "police": 800}


# ---------------------------------------------------------------- edge-parallel frames
class Edge:
    """A long boundary edge. s runs along it, d is the inward distance from it."""

    def __init__(self, a, b, inward):
        self.o = a
        L = math.dist(a, b)
        self.u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        self.n = (-self.u[1] * inward, self.u[0] * inward)
        self.length = L

    def pt(self, s, d):
        return (self.o[0] + s * self.u[0] + d * self.n[0], self.o[1] + s * self.u[1] + d * self.n[1])

    def rect(self, s0, s1, d0, d1):
        return Polygon([self.pt(s0, d0), self.pt(s1, d0), self.pt(s1, d1), self.pt(s0, d1)])

    def sd(self, p):
        x, y = p[0] - self.o[0], p[1] - self.o[1]
        return (x * self.u[0] + y * self.u[1], x * self.n[0] + y * self.n[1])

    def s_at_x(self, x, d):
        return (x - self.o[0] - d * self.n[0]) / self.u[0]

    def line(self, d, x0, x1):
        return LineString([self.pt(self.s_at_x(x0, d), d), self.pt(self.s_at_x(x1, d), d)])

    def band(self, d0, d1, x0, x1):
        return Polygon([self.pt(self.s_at_x(x0, d0), d0), self.pt(self.s_at_x(x1, d0), d0),
                        self.pt(self.s_at_x(x1, d1), d1), self.pt(self.s_at_x(x0, d1), d1)])


_q = {k: P.to_local(v) for k, v in P.Q.items()}
SOUTH = Edge(_q["Q1"], _q["Q4"], +1)
NORTH = Edge(_q["Q2"], _q["Q3"], -1)
EDGES = {"s": SOUTH, "n": NORTH}


def edge_y_s(x):
    return P.edge_y(x, "s")


def edge_y_n(x):
    return P.edge_y(x, "n")


def band_mid(ds, dn, x0=-100, x1=1000):
    """Part of the site at least ds from the south edge and dn from the north edge."""
    return SOUTH.band(ds, 400, x0, x1).intersection(NORTH.band(dn, 400, x0, x1)).intersection(SITE)


def band_edge(edge, d0, d1, x0=-100, x1=1000):
    return EDGES[edge].band(d0, d1, x0, x1).intersection(SITE)


def rib(x, d_n, d_s, edge="n"):
    """Cross street along the normal of an edge at local x, from d_n off the north edge to d_s off the south."""
    e = EDGES[edge]
    s = e.s_at_x(x, 0)
    far = LineString([e.pt(s, -50), e.pt(s, 450)])
    a = far.intersection(NORTH.line(d_n, -200, 1100))
    b = far.intersection(SOUTH.line(d_s, -200, 1100))
    return LineString([(a.x, a.y), (b.x, b.y)])


def ncut(x0, x1, edge="n"):
    """Slice of the site between two lines normal to an edge, at local x0 and x1."""
    e = EDGES[edge]
    s0, s1 = e.s_at_x(x0, 0), e.s_at_x(x1, 0)
    return Polygon([e.pt(s0, -60), e.pt(s1, -60), e.pt(s1, 460), e.pt(s0, 460)]).intersection(SITE)


def xcut(x0, x1, y0=-50, y1=400):
    """Slice of the site between two cross-lines perpendicular to the long axis."""
    return box(x0, y0, x1, y1).intersection(SITE)


def wadi_corridor(half=WADI_HALF):
    return P.WADI_L.buffer(half, cap_style="flat").intersection(SITE)


def cross_road(width=10.0):
    return P.ROAD_X_L.buffer(width / 2, cap_style="flat").intersection(SITE)


def west_of_cross(margin=0.0):
    """Part of the site west of the cross road."""
    line = P.ROAD_X_L
    a, b = line.coords[0], line.coords[-1]
    far = Polygon([a, b, (b[0] - 400, b[1]), (a[0] - 400, a[1])])
    return far.buffer(0).difference(cross_road().buffer(margin)).intersection(SITE)


def east_of_wadi(half=WADI_HALF):
    c = list(P.WADI_L.coords)
    far = Polygon(c + [(c[-1][0] + 500, c[-1][1]), (c[0][0] + 500, c[0][1])])
    return far.buffer(0).difference(wadi_corridor(half)).intersection(SITE)


def rect_c(cx, cy, w, h, angle=0.0):
    """Rectangle centred on (cx, cy), w along local x, rotated by angle (deg)."""
    r = box(-w / 2, -h / 2, w / 2, h / 2)
    from shapely import affinity
    return affinity.translate(affinity.rotate(r, angle, origin=(0, 0)), cx, cy)


def edge_rect(edge, x0, w, d0, depth):
    """Parcel of given along-edge width and depth, starting at local x0, d0 from the edge."""
    e = EDGES[edge]
    s0 = e.s_at_x(x0, d0)
    return e.rect(s0, s0 + w, d0, d0 + depth)


# ---------------------------------------------------------------- the plan model
class Plan:
    def __init__(self, key, name, name_ar):
        self.key, self.name, self.name_ar = key, name, name_ar
        self.roads = []        # dict(line, cls, name)
        self.paths = []        # pedestrian lines (walk network only)
        self.parcels = {}      # name -> dict(poly, cat, label)
        self.res_zones = []    # dict(poly, rows=[(edge, d0, type, facing)])
        self.lots = []
        self.towers = []       # footprints
        self.gates = []        # dict(pt, kind)
        self.phases = []       # dict(poly, label)
        self.notes = {}
        self.section_x = None
        self.tower_units = {"M2": 76, "M3": 76}

    # -- authoring helpers
    def road(self, coords, cls, name=""):
        self.roads.append({"line": LineString(coords), "cls": cls, "name": name})

    def road_line(self, line, cls, name=""):
        self.roads.append({"line": line, "cls": cls, "name": name})

    def path(self, coords):
        self.paths.append(LineString(coords))

    def parcel(self, name, poly, cat, label=""):
        self.parcels[name] = {"poly": poly, "cat": cat, "label": label}

    def service(self, key, poly):
        area, label, kind = SERVICES[key]
        self.parcels[key] = {"poly": poly, "cat": "util" if kind == "util" else "service", "label": label,
                             "target": area}

    def tower(self, cx, cy, angle=0.0):
        self.towers.append(rect_c(cx, cy, TOWER_W, TOWER_D, angle))

    def gate(self, x, y, kind):
        self.gates.append({"pt": Point(x, y), "kind": kind})

    def strip_rows(self, edge, seq, x0, x1, d_start=0.0, street_ext=0.0):
        """Lay a cross-section of rows along an edge.

        seq items: 'buf:6', 'V+', 'V-', 'D+', 'D-', 'S' (12 m local street), 'L' (8 m lane),
        'G:20' (green strip). '+' means the lot fronts the street on its inner (larger d) side.
        Returns row specs; streets are added to the plan as local roads between x0 and x1.
        """
        e = EDGES[edge]
        d = d_start
        rows = []
        for item in seq:
            if item.startswith("buf") or item.startswith("G"):
                d += float(item.split(":")[1])
            elif item in ("S", "L"):
                w = ROAD_W["local"] if item == "S" else ROAD_W["lane"]
                self.road_line(e.line(d + w / 2, x0 - street_ext, x1 + street_ext),
                               "local" if item == "S" else "lane")
                d += w
            else:
                t, f = item[0], item[1]
                rows.append((edge, d, t, f))
                d += LOT[t][1]
        return rows, d

    def res(self, poly, rows):
        self.res_zones.append({"poly": poly, "rows": rows})

    # -- building the plan
    def build(self):
        site = SITE
        self.road_polys = {}
        main, local = [], []
        for r in self.roads:
            w = ROAD_W[r["cls"]]
            g = r["line"].buffer(w / 2, cap_style="flat", join_style="mitre")
            (main if r["cls"] in MAIN_ROADS else local).append(g)
        self.main_roads = unary_union(main).intersection(site) if main else Polygon()
        self.local_roads = (unary_union(local).intersection(site).difference(self.main_roads)
                            if local else Polygon())
        roads = self.main_roads.union(self.local_roads)
        taken = roads
        for name, p in self.parcels.items():
            p["poly"] = p["poly"].intersection(site).difference(taken)
            taken = taken.union(p["poly"])
        self.taken_nonres = taken
        # residential zones, lot packing
        lot_id = 0
        for z in self.res_zones:
            zp = z["poly"].intersection(site).difference(taken)
            z["poly"] = zp
            for edge, d0, t, f in z["rows"]:
                for lot in pack_row(EDGES[edge], d0, t, f, zp):
                    lot_id += 1
                    lot["id"] = lot_id
                    lot["edge"] = edge
                    self.lots.append(lot)
            taken = taken.union(zp)
        self.res_area = unary_union([z["poly"] for z in self.res_zones]) if self.res_zones else Polygon()
        lots_u = unary_union([l["poly"] for l in self.lots]) if self.lots else Polygon()
        self.jeera = self.res_area.difference(lots_u)
        self.leftover = site.difference(taken)
        return self

    # -- accounting
    def landuse(self):
        A = lambda g: g.area
        cat = {"housing": 0.0, "towers": 0.0, "services": 0.0, "parks": 0.0, "roads": 0.0}
        cat["housing"] = A(self.res_area) + 0  # lots + jeera inside zones
        local_in = self.local_roads.area
        cat["housing"] += local_in
        cat["roads"] = A(self.main_roads)
        detail = {}
        for name, p in self.parcels.items():
            c = p["cat"]
            a = A(p["poly"])
            detail[name] = a
            if c in ("service", "util"):
                cat["services"] += a
            elif c == "tower_zone":
                cat["towers"] += a
            elif c in ("park", "wadi", "sports", "buffer"):
                cat["parks"] += a
            elif c == "parking":
                cat["roads"] += a
            elif c == "jeera":
                cat["housing"] += a
            else:
                raise ValueError(c)
        cat["parks"] += A(self.leftover)
        self.detail = detail
        return cat

    def units(self):
        v = sum(1 for l in self.lots if l["type"] == "V")
        d = sum(1 for l in self.lots if l["type"] == "D")
        m2, m3 = self.tower_units["M2"], self.tower_units["M3"]
        pop = v * PERSONS["V"] + d * PERSONS["D"] + m2 * PERSONS["M2"] + m3 * PERSONS["M3"]
        return {"V": v, "D": d, "M2": m2, "M3": m3, "total": v + d + m2 + m3, "pop": pop,
                "tower_pop": m2 * PERSONS["M2"] + m3 * PERSONS["M3"]}


def pack_row(e, d0, t, facing, zone):
    """Fill one row of lots along an edge inside the zone, centred in each free run."""
    w, depth = LOT[t]
    d1 = d0 + depth
    strip = e.rect(-200, e.length + 200, d0, d1)
    free = strip.intersection(zone)
    pieces = list(free.geoms) if hasattr(free, "geoms") else [free]
    zone_t = zone.buffer(0.05)
    out = []
    for pc in pieces:
        if pc.is_empty or pc.area < w * depth:
            continue
        ss = [e.sd(c)[0] for c in pc.exterior.coords]
        s_min, s_max = min(ss), max(ss)
        # slide the start inside [s_min, s_min + w) to fit the most lots, then centre the run
        best = []
        for k in range(8):
            start = s_min + k * w / 8
            run = []
            s = start
            while s + w <= s_max + 1e-6:
                r = e.rect(s, s + w, d0, d1)
                if zone_t.contains(r):
                    run.append(s)
                s += w
            if len(run) > len(best):
                best = run
        for s in best:
            poly = e.rect(s, s + w, d0, d1)
            hw, hd, sb = HOUSE[t]
            side = (w - hw) / 2
            if facing == "+":   # street at larger d
                fp = e.rect(s + side, s + side + hw, d1 - sb - hd, d1 - sb)
                front = e.pt(s + w / 2, d1)
                normal = e.n
            else:
                fp = e.rect(s + side, s + side + hw, d0 + sb, d0 + sb + hd)
                front = e.pt(s + w / 2, d0)
                normal = (-e.n[0], -e.n[1])
            out.append({"poly": poly, "type": t, "facing": facing, "fp": fp, "front": Point(front),
                        "normal": normal, "d0": d0})
    return out


# ---------------------------------------------------------------- networks
def _noded(lines):
    u = unary_union(lines)
    return list(u.geoms) if hasattr(u, "geoms") else [u]


class Network:
    def __init__(self, lines):
        self.G = nx.Graph()
        self.edges = []
        for seg in _noded([l for l in lines if l.length > 0]):
            cs = list(seg.coords)
            for a, b in zip(cs[:-1], cs[1:]):
                a, b = (round(a[0], 2), round(a[1], 2)), (round(b[0], 2), round(b[1], 2))
                if a == b:
                    continue
                L = math.dist(a, b)
                self.G.add_edge(a, b, weight=L)
                self.edges.append((a, b, LineString([a, b])))
        self.tree = STRtree([e[2] for e in self.edges])

    def locate(self, pt):
        i = self.tree.nearest(pt)
        a, b, ln = self.edges[i]
        t = ln.project(pt)
        return i, a, b, t, ln.length - t, ln.distance(pt)

    def dist_from(self, pts):
        """Multi-source network distance from a set of points; returns a function point -> metres."""
        G = self.G
        G.add_node("SRC")
        locs = []
        for p in pts:
            i, a, b, ta, tb, off = self.locate(p)
            locs.append((i, ta, off))
            for n, w in ((a, ta + off), (b, tb + off)):
                if G.has_edge("SRC", n):
                    G["SRC"][n]["weight"] = min(G["SRC"][n]["weight"], w)
                else:
                    G.add_edge("SRC", n, weight=w)
        D = nx.single_source_dijkstra_path_length(G, "SRC", weight="weight")
        G.remove_node("SRC")

        def f(p):
            i, a, b, ta, tb, off = self.locate(p)
            best = min(D.get(a, 1e9) + ta, D.get(b, 1e9) + tb) + off
            for j, tsa, soff in locs:   # same edge: direct along the edge
                if j == i:
                    best = min(best, abs(ta - tsa) + off + soff)
            return best
        return f


def entrance(poly, net_lines):
    """Point of a parcel closest to the vehicle/walk network (its entrance)."""
    from shapely.ops import nearest_points
    return nearest_points(poly.exterior if hasattr(poly, "exterior") else poly.boundary,
                          unary_union(net_lines))[0]


# ---------------------------------------------------------------- sun & shadow
def sun(hour, lat=P.LAT, decl=-23.44):
    """Solar altitude and azimuth (deg, from north clockwise) at local solar time."""
    H = math.radians(15 * (hour - 12))
    phi, dl = math.radians(lat), math.radians(decl)
    alt = math.asin(math.sin(phi) * math.sin(dl) + math.cos(phi) * math.cos(dl) * math.cos(H))
    az = math.atan2(math.sin(H), math.cos(H) * math.sin(phi) - math.tan(dl) * math.cos(phi))
    return math.degrees(alt), (math.degrees(az) + 180) % 360


def shadow_vec(hour, h=TOWER_H):
    """Shadow vector of a point at height h, in the local frame."""
    alt, az = sun(hour)
    L = h / math.tan(math.radians(alt))
    b = math.radians((az + 180) % 360)               # bearing the shadow points to
    wx, wy = L * math.sin(b), L * math.cos(b)          # world east, north
    a = math.radians(-P.AXIS_ANGLE)
    return (wx * math.cos(a) - wy * math.sin(a), wx * math.sin(a) + wy * math.cos(a)), L


def tower_shadow(fp, hour):
    from shapely import affinity
    (vx, vy), _ = shadow_vec(hour)
    return unary_union([fp, affinity.translate(fp, vx, vy)]).convex_hull
