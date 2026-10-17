"""Redraw the preliminary site plan of the fuel station on plot (1/3453), district 43
Yarimja Al-Sharqiya, Mosul, as a DXF (metres).

Source: a phone photo of the paper print (source_photo.jpg).  The geometry is driven by the
written dimensions; the photo only places items that carry no dimension.

The plot is a right trapezoid: the 50 m rear boundary is perpendicular to both side
boundaries (30.59 and 66.02), which makes the street front sqrt(50^2 + 35.43^2) = 61.28,
exactly as written on the plan.

Everything is built in a plot frame F (origin at the rear-left corner, x along the 50 m rear
boundary, y pointing into the plot) and written in the frame of the paper sheet (street front
horizontal, front-left corner at 0,0, y up).

usage: python build_fuel_station_dxf.py OUT.dxf
"""
import math
import sys

import ezdxf
from ezdxf.enums import MTextEntityAlignment
from shapely.geometry import LineString, MultiLineString, Polygon, box
from shapely.ops import linemerge, unary_union

OUT = sys.argv[1] if len(sys.argv) > 1 else "fuel_station_site_plan.dxf"

# ------------------------------------------------------------------ plot frame
W, LL, LR = 50.0, 30.59, 66.02            # rear, left side, right side
FRONT = math.hypot(W, LR - LL)            # 61.28
TH = math.atan2(LR - LL, W)               # front makes this angle with the rear boundary
CT, ST = math.cos(TH), math.sin(TH)
U = (W / FRONT, (LR - LL) / FRONT)        # along the front, A -> B
NIN = (U[1], -U[0])                       # from the front into the plot
NOUT = (-U[1], U[0])
WT = 0.25                                 # wall thickness

D, C, B, A = (0.0, 0.0), (W, 0.0), (W, LR), (0.0, LL)
PLOT = Polygon([D, C, B, A])
INNER = PLOT.buffer(-WT, join_style=2)


def o(p):
    """Plot frame -> sheet frame."""
    x, y = p[0], LL - p[1]
    return (x * CT - y * ST, x * ST + y * CT)


def sang(a_f):
    """Direction angle in the plot frame (deg, towards +y) -> sheet angle."""
    return math.degrees(TH) - a_f


def fr(s, t=0.0):
    """Point s metres along the front from A, t metres inwards."""
    return (s * U[0] + t * NIN[0], LL + s * U[1] + t * NIN[1])


def mv(p, v, k=1.0):
    return (p[0] + k * v[0], p[1] + k * v[1])


def front_box(s0, s1, t0, t1):
    return Polygon([fr(s0, t0), fr(s1, t0), fr(s1, t1), fr(s0, t1)])


# ------------------------------------------------------------------ document
doc = ezdxf.new("R2018", setup=True)
doc.units = ezdxf.units.M
doc.header["$INSUNITS"] = 6
doc.header["$MEASUREMENT"] = 1
doc.header["$LTSCALE"] = 0.6
msp = doc.modelspace()

doc.styles.add("AR", font="arial.ttf")

LAYERS = {
    "PLOT": (1, 50, "CONTINUOUS"),
    "WALL": (7, 35, "CONTINUOUS"),
    "GATE": (4, 25, "CONTINUOUS"),
    "DOOR": (3, 18, "CONTINUOUS"),
    "SANITARY": (8, 18, "CONTINUOUS"),
    "STAIR": (7, 18, "CONTINUOUS"),
    "PAVING": (8, 18, "CONTINUOUS"),
    "PAVING-HATCH": (9, 9, "CONTINUOUS"),
    "GARDEN": (3, 18, "CONTINUOUS"),
    "CANOPY": (5, 25, "DASHED"),
    "ISLAND": (30, 25, "CONTINUOUS"),
    "TANK": (6, 25, "DASHED"),
    "TANK-FIT": (6, 18, "CONTINUOUS"),
    "FILL-POINT": (6, 25, "CONTINUOUS"),
    "PIPE": (8, 13, "DASHED"),
    "DIM": (3, 13, "CONTINUOUS"),
    "TEXT": (7, 18, "CONTINUOUS"),
    "TITLE": (7, 25, "CONTINUOUS"),
}
for name, (color, lw, lt) in LAYERS.items():
    doc.layers.add(name, color=color, linetype=lt, lineweight=lw)

ds = doc.dimstyles.new("SITE", dxfattribs={
    "dimtxsty": "AR", "dimtxt": 0.30, "dimasz": 0.15, "dimexo": 0.08, "dimexe": 0.15,
    "dimgap": 0.06, "dimtad": 1, "dimdec": 2, "dimtih": 0, "dimtoh": 0, "dimzin": 8,
    "dimclrd": 3, "dimclre": 3, "dimclrt": 7, "dimlfac": 1.0,
})
ds.set_arrows(blk="ARCHTICK")


# ------------------------------------------------------------------ primitives
def line(a, b, layer, **kw):
    msp.add_line(o(a), o(b), dxfattribs={"layer": layer, **kw})


def pline(pts, layer, close=False, width=None, **kw):
    e = msp.add_lwpolyline([o(p) for p in pts], close=close, dxfattribs={"layer": layer, **kw})
    if width:
        e.dxf.const_width = width
    return e


def bulge_pline(path, layer, close=False, **kw):
    """path: [(x, y, bulge)] in the plot frame; the frame change mirrors, so bulges flip."""
    pts = [(*o((x, y)), 0, 0, -b) for x, y, b in path]
    return msp.add_lwpolyline(pts, format="xyseb", close=close, dxfattribs={"layer": layer, **kw})


def circle(c, r, layer, **kw):
    msp.add_circle(o(c), r, dxfattribs={"layer": layer, **kw})


def arc(c, r, a1, a2, layer):
    """Arc sweeping from plot-frame angle a1 to a2 (increasing, towards +y)."""
    msp.add_arc(o(c), r, sang(a2), sang(a1), dxfattribs={"layer": layer})


def dot(c, r, layer):
    """Filled dot (donut)."""
    x, y = o(c)
    e = msp.add_lwpolyline([(x - r / 2, y, 0, 0, 1), (x + r / 2, y, 0, 0, 1)], format="xyseb",
                           close=True, dxfattribs={"layer": layer})
    e.dxf.const_width = r


def text(s, p, a_f=0.0, h=0.3, layer="TEXT", width=None, attach=MTextEntityAlignment.MIDDLE_CENTER,
         sheet_angle=None):
    a = sheet_angle if sheet_angle is not None else sang(a_f)
    a = (a + 90) % 180 - 90                     # keep the text readable
    e = msp.add_mtext(s, dxfattribs={"layer": layer, "style": "AR", "char_height": h})
    e.set_location(o(p), rotation=a, attachment_point=attach)
    if width:
        e.dxf.width = width
    return e


def dim(p1, p2, base, label, h=0.3, tad=1, asz=None, layer="DIM"):
    """Linear dimension p1-p2 with its dimension line through base, showing the plan's label."""
    P1, P2 = o(p1), o(p2)
    ang = math.degrees(math.atan2(P2[1] - P1[1], P2[0] - P1[0]))
    ov = {"dimtxt": h, "dimtad": tad}
    if asz:
        ov["dimasz"] = asz
    d = msp.add_linear_dim(base=o(base), p1=P1, p2=P2, angle=ang, text=label, dimstyle="SITE",
                           override=ov, dxfattribs={"layer": layer})
    d.render()


def dim_off(p1, p2, off, label, **kw):
    """Dimension line offset `off` to the left of p1->p2 (plot frame, y down: left = towards -n)."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    n = (dy / L, -dx / L)
    dim(p1, p2, mv(((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2), n, off), label, **kw)


def polys(g):
    return [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


def lines_of(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    if g.geom_type == "MultiLineString":
        m = linemerge(g)
        return [m] if m.geom_type == "LineString" else list(m.geoms)
    return [x for p in getattr(g, "geoms", []) for x in lines_of(p)]


def outline(g, layer, exclude=None):
    for p in polys(g):
        for ring in [p.exterior, *p.interiors]:
            ls = LineString(ring.coords)
            if exclude is not None:
                ls = ls.difference(exclude)
            for part in lines_of(ls):
                pts = list(part.coords)
                closed = len(pts) > 3 and pts[0] == pts[-1]
                pline(pts[:-1] if closed else pts, layer, close=closed)


def hatch(g, layer, pattern="SOLID", scale=1.0, angle=0.0, color=None):
    h = msp.add_hatch(color=color if color is not None else 256, dxfattribs={"layer": layer})
    if pattern == "SOLID":
        h.set_solid_fill(color=color if color is not None else 256)
    else:
        h.set_pattern_fill(pattern, scale=scale, angle=angle, color=color if color is not None else 256)
    for p in polys(g):
        h.paths.add_polyline_path([o(q) for q in p.exterior.coords[:-1]], is_closed=True, flags=1)
        for ring in p.interiors:
            h.paths.add_polyline_path([o(q) for q in ring.coords[:-1]], is_closed=True, flags=0)
    return h


def arc_pts(c, r, a1, a2, n=10):
    return [(c[0] + r * math.cos(math.radians(a1 + (a2 - a1) * k / n)),
             c[1] + r * math.sin(math.radians(a1 + (a2 - a1) * k / n))) for k in range(n + 1)]


def bulge_of(sweep_deg):
    return math.tan(math.radians(sweep_deg) / 4)


def door(hinge, closed_end, side, layer="DOOR"):
    """Door leaf drawn open at 90 deg; side=+1/-1 picks the swing side (plot frame)."""
    hx, hy = hinge
    vx, vy = closed_end[0] - hx, closed_end[1] - hy
    w = math.hypot(vx, vy)
    px, py = (-vy * side, vx * side)
    tip = (hx + px, hy + py)
    line(hinge, tip, layer)
    a_closed = math.degrees(math.atan2(vy, vx))
    a_open = math.degrees(math.atan2(py, px))
    a1, a2 = sorted([a_closed, a_open])
    if a2 - a1 > 180:
        a1, a2 = a2, a1 + 360
    arc(hinge, w, a1, a2, layer)


def window(x0, y0, x1, y1):
    """Window in a wall: lines on both faces plus the glass line (long side picks the direction)."""
    if x1 - x0 >= y1 - y0:
        for y in (y0, (y0 + y1) / 2, y1):
            line((x0, y), (x1, y), "DOOR")
    else:
        for x in (x0, (x0 + x1) / 2, x1):
            line((x, y0), (x, y1), "DOOR")


def zigzag(p0, p1, amp=0.15, step=0.3, layer="DOOR"):
    """Shutter symbol along p0-p1."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    n = max(2, int(round(L / step)))
    pts = []
    for k in range(n + 1):
        s = L * k / n
        side = 0 if k in (0, n) else (amp if k % 2 else -amp)
        pts.append((p0[0] + ux * s - uy * side, p0[1] + uy * s + ux * side))
    pline(pts, layer)


def ladder(p0, along, across, length, width, step=0.2, layer="ISLAND"):
    """Dotted strip (narrow rectangle with rungs) starting at p0."""
    q = [p0, mv(p0, along, length), mv(mv(p0, along, length), across, width), mv(p0, across, width)]
    pline(q, layer, close=True)
    k = step
    while k < length - 1e-6:
        a = mv(p0, along, k)
        line(a, mv(a, across, width), layer)
        k += step


def rrect_path(x0, y0, x1, y1, r):
    b = bulge_of(90)
    return [(x0 + r, y0, 0), (x1 - r, y0, b), (x1, y0 + r, 0), (x1, y1 - r, b),
            (x1 - r, y1, 0), (x0 + r, y1, b), (x0, y1 - r, 0), (x0, y0 + r, b)]


# ================================================================== plot and boundary
pline([D, C, B, A], "PLOT", close=True)

# front: 2 | 10 exit | 19.28 | 10 entrance | 8 | 5 gate | 7   (= 61.28)
PIER = 0.5
openings = [(2.0, 12.0), (31.28, 41.28), (49.28, 54.28)]
piers = [(1.5, 2.0), (12.0, 12.5), (30.78, 31.28), (41.28, 41.78), (48.78, 49.28), (54.28, 54.78)]

walls = PLOT.difference(INNER)
walls = walls.difference(unary_union([front_box(s0, s1, -1, 1) for s0, s1 in openings]))
walls = unary_union([walls] + [front_box(s0, s1, 0.0, PIER) for s0, s1 in piers])

# ================================================================== buildings along the rear
wall_parts, wall_holes = [], []

# --- building 1: transformer room 6.0 x 4.0, generator room 3.5 x 4.0
B1 = box(1.25, 1.25, 11.5, 5.75)
wall_parts.append(B1.difference(unary_union([box(1.5, 1.5, 7.5, 5.5), box(7.75, 1.5, 11.25, 5.5)])))
wall_holes += [box(3.5, 5.4, 5.5, 5.85), box(8.0, 5.4, 11.0, 5.85),            # shutter openings
               box(8.4, 1.2, 9.0, 1.55), box(9.6, 1.2, 10.2, 1.55),             # windows
               box(11.2, 2.75, 11.55, 4.5)]
window(8.4, 1.25, 9.0, 1.5)
window(9.6, 1.25, 10.2, 1.5)
window(11.25, 2.75, 11.5, 4.5)
zigzag((3.5, 5.625), (5.5, 5.625))
zigzag((8.0, 5.625), (11.0, 5.625))
ladder((8.5, 5.05), (1, 0), (0, 1), 2.1, 0.2)                                    # louvre / trench
text("غرفة المحولة", (5.4, 3.75), 90, 0.35)
text("غرفة المولدة", (9.9, 3.6), 90, 0.35)
dim((0.25, 2.0), (1.25, 2.0), (0, 2.0), "1.0", h=0.25)
dim((1.5, 2.2), (7.5, 2.2), (0, 2.2), "6.0")
dim((1.9, 1.5), (1.9, 5.5), (1.9, 0), "4.0")
dim((3.5, 5.2), (5.5, 5.2), (0, 5.2), "2.0")
dim((7.75, 2.2), (11.25, 2.2), (0, 2.2), "3.5")
dim((8.1, 1.5), (8.1, 5.5), (8.1, 0), "4.0")
dim((8.0, 6.35), (11.0, 6.35), (0, 6.35), "3.0")
dim((2.6, 0.25), (2.6, 1.25), (2.6, 0), "1.0", h=0.25)

# paved pad and well below the transformer / generator rooms
pad = Polygon([(5.75, 5.75), (7.75, 5.75)] + arc_pts((7.25, 6.25), 0.5, 0, 90)
              + arc_pts((6.25, 6.25), 0.5, 90, 180))
bulge_pline([(5.75, 5.75, 0), (5.75, 6.25, -bulge_of(90)), (6.25, 6.75, 0), (7.25, 6.75, -bulge_of(90)),
             (7.75, 6.25, 0), (7.75, 5.75, 0)], "PAVING")
pline([(5.75, 6.75), (7.75, 6.75), (7.75, 8.25), (5.75, 8.25)], "PIPE", close=True)   # well, dashed
circle((6.75, 7.5), 0.22, "TANK-FIT")
dot((6.75, 7.5), 0.12, "TANK-FIT")
dim((5.75, 8.55), (7.75, 8.55), (0, 8.55), "2.0", h=0.25)
dim((8.05, 6.75), (8.05, 8.25), (8.05, 0), "1.5", h=0.25)

# --- building 2: WC, administration, stair core, workers' room
B2 = box(14.25, 1.25, 29.75, 5.25)
SX0, SX1 = 22.1, 24.55                       # stair core between the two rooms (2.45 clear)
SY1 = 3.6                                    # foot of both flights, the lobby is below
r_wc, r_adm, r_hall, r_wrk = box(14.5, 1.5, 17.0, 5.0), box(17.25, 1.5, SX0 - WT, 5.0), \
    box(SX0, 1.5, SX1, 5.0), box(SX1 + WT, 1.5, 29.5, 5.0)
wall_parts.append(B2.difference(unary_union([r_wc, r_adm, r_hall, r_wrk])))
SXC = (SX0 + SX1) / 2
wall_parts += [box(SXC - 1.925, 5.25, SXC - 1.325, 5.85), box(SXC + 1.325, 5.25, SXC + 1.925, 5.85)]  # piers at the steps
# WC cubicles (10 cm partitions)
wall_parts += [box(15.7, 1.5, 15.8, 3.05), box(14.5, 2.95, 17.0, 3.05)]
wall_holes += [box(14.8, 2.9, 15.5, 3.1), box(16.0, 2.9, 16.7, 3.1),
               box(15.6, 4.95, 16.5, 5.3), box(SXC - 0.625, 4.95, SXC + 0.625, 5.3),
               box(SX0 - WT - 0.05, SY1, SX0 + 0.05, SY1 + 1.0), box(SX1 - 0.05, SY1, SX1 + WT + 0.05, SY1 + 1.0)]
door((15.5, 2.95), (14.8, 2.95), 1)
door((16.7, 2.95), (16.0, 2.95), 1)
door((16.5, 5.0), (15.6, 5.0), 1)
door((SX0 - WT, SY1 + 1.0), (SX0 - WT, SY1), -1)    # into the administration room
door((SX1 + WT, SY1 + 1.0), (SX1 + WT, SY1), 1)     # into the workers' room
for cx in (15.1, 16.4):                                                          # squat toilets
    pline([(cx - 0.22, 1.75), (cx + 0.22, 1.75), (cx + 0.22, 2.45), (cx - 0.22, 2.45)], "SANITARY", close=True)
    bulge_pline(rrect_path(cx - 0.1, 1.9, cx + 0.1, 2.25, 0.08), "SANITARY", close=True)
for cy in (3.7, 4.35):                                                           # wash basins
    c = o((16.78, cy))
    msp.add_ellipse(c, major_axis=tuple(a - b for a, b in zip(o((16.78, cy + 0.25)), c)), ratio=0.7,
                    dxfattribs={"layer": "SANITARY"})

# stair: two flights either side of a central wall, joined by winders at the rear
HUB = (SXC, 2.1)                              # rear end of the central wall
newel = box(SXC - 0.075, HUB[1], SXC + 0.075, SY1)
outline(newel, "STAIR")
hatch(newel, "STAIR", "SOLID")
for y in (2.35, 2.6, 2.85, 3.1, 3.35, SY1):                                      # left flight
    line((SX0, y), (SXC - 0.075, y), "STAIR")
for y in (2.8, 3.05, 3.3, SY1):                                                  # right flight
    line((SXC + 0.075, y), (SX1, y), "STAIR")
for a in range(180, 381, 20):                                                    # winders
    dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
    ts = [(SX0 - HUB[0]) / dx if dx < -1e-9 else (SX1 - HUB[0]) / dx if dx > 1e-9 else 1e9]
    if dy < -1e-9:
        ts.append((1.5 - HUB[1]) / dy)
    line(HUB, mv(HUB, (dx, dy), min(ts)), "STAIR")
for yy in (5.25, 5.65, 6.05, 6.45):                                              # entrance steps
    line((SXC - 1.05, yy), (SXC + 1.05, yy), "STAIR")
line((SXC - 1.05, 5.25), (SXC - 1.05, 6.45), "STAIR")
line((SXC + 1.05, 5.25), (SXC + 1.05, 6.45), "STAIR")
x = 15.3
while x < 17.8:                                                                  # gully grating
    line((x, 5.75), (x + 0.1, 5.95), "PAVING")
    x += 0.2
pline([(13.75, 3.8), (13.75, 6.1), (21.9, 6.1)], "PIPE")
text("غرفة الادارة", (19.55, 3.45), 90, 0.35)
text("غرفة العمال", (27.15, 3.45), 90, 0.35)
dim((17.25, 1.9), (SX0 - WT, 1.9), (0, 1.9), "4.6")
dim((17.6, 1.5), (17.6, 5.0), (17.6, 0), "3.5")
dim((SX1 + WT, 1.9), (29.5, 1.9), (0, 1.9), "4.7")
dim((SX0, 4.2), (SX1, 4.2), (0, 4.2), "2.45", h=0.25)
dim((29.1, 1.5), (29.1, 5.0), (29.1, 0), "3.5")
dim((13.25, 2.0), (14.25, 2.0), (0, 2.0), "1.0", h=0.25)
dim((19.0, 0.25), (19.0, 1.25), (19.0, 0), "1.0", h=0.25)
dim((19.0, 5.25), (19.0, 6.25), (19.0, 0), "1.0", h=0.25)

# --- building 3: spare parts, paints showroom, prayer room, WC
B3 = box(32.0, 1.25, 45.25, 5.25)
rooms3 = [box(32.25, 1.5, 36.0, 5.0), box(36.25, 1.5, 40.0, 5.0), box(40.25, 1.5, 43.75, 5.0),
          box(44.0, 1.5, 45.0, 5.0)]
wall_parts.append(B3.difference(unary_union(rooms3)))
for x0 in (32.65, 36.65, 40.65):                                                 # 2.0 shutter openings
    wall_holes.append(box(x0, 4.95, x0 + 2.0, 5.3))
    pline([(x0, 5.125), (x0 + 2.0, 5.125)], "PIPE")
    bulge_pline(rrect_path(x0 + 2.0, 5.03, x0 + 2.35, 5.22, 0.09), "DOOR", close=True)
wall_holes.append(box(44.1, 4.95, 44.9, 5.3))
door((44.1, 5.0), (44.9, 5.0), -1)
pline([(44.2, 1.6), (44.8, 1.6), (44.8, 2.2), (44.2, 2.2)], "SANITARY", close=True)
c = o((44.5, 3.8))
msp.add_ellipse(c, major_axis=tuple(a - b for a, b in zip(o((44.5, 4.05)), c)), ratio=0.7,
                dxfattribs={"layer": "SANITARY"})
text("أدوات\\Pاحتياطية", (34.1, 3.0), 90, 0.4)
text("معرض\\Pدهون", (38.1, 3.0), 90, 0.4)
text("مصلى", (42.0, 3.0), 90, 0.4)
dim((32.25, 4.6), (36.0, 4.6), (0, 4.6), "3.75")
dim((36.25, 4.6), (40.0, 4.6), (0, 4.6), "3.75")
dim((40.25, 4.6), (43.75, 4.6), (0, 4.6), "3.50")
for xd in (32.5, 36.5, 40.5):
    dim((xd, 1.5), (xd, 5.0), (xd, 0), "3.50")
dim((38.0, 0.25), (38.0, 1.25), (38.0, 0), "1.0", h=0.25)
dim((38.0, 5.25), (38.0, 6.25), (38.0, 0), "1.0", h=0.25)

# --- garden / septic area in the rear-right corner
garden = rrect_path(45.9, 1.4, 48.75, 5.75, 0.5)
bulge_pline(garden, "GARDEN", close=True)
g_poly = Polygon([(x, y) for x, y, _ in garden]).buffer(0)
hatch(g_poly, "GARDEN", "NET", scale=0.08, angle=math.degrees(TH), color=8)
for c, r in (((46.7, 4.7), 0.55), ((47.8, 4.9), 0.5)):
    circle(c, r, "GARDEN")
dim((48.75, 2.2), (49.75, 2.2), (0, 2.2), "1.0", h=0.25)

# ================================================================== tank area (right strip)
# right-side chain from the rear corner: 12.87 | 6.4 | 15 | 14.25 | 17.5  (= 66.02)
Y0 = LR - 17.5 - 14.25 - 15.0 - 6.4          # 12.87, top of the tank area
Y1, Y2, Y3 = Y0 + 6.4, Y0 + 21.4, Y0 + 35.65  # cross walls
XL = 37.0                                     # tank-area wall, curb 36.0 - 37.0 in front of it
wall_parts += [box(XL, Y0, W, Y0 + WT), box(XL, Y0, XL + WT, LR),
               box(XL, Y1, W, Y1 + WT), box(XL, Y2, W, Y2 + WT), box(XL, Y3, W, Y3 + WT)]
SEP = Y2 + WT + 1.0 + 2.75 + 1.0 + 2.75 + 1.0   # separating wall between the 2nd and 3rd 54 m3 tank
wall_parts.append(box(XL + WT, SEP, W, SEP + WT))
wall_holes.append(box(XL - 0.1, Y3 + 0.45, XL + WT + 0.1, Y3 + 1.65))           # door into the kerosene yard
door((XL + WT, Y3 + 1.65), (XL + WT, Y3 + 0.45), 1)


def tank(x0, x1, yc, dia, head, labels, label_pos):
    r = dia / 2
    R = (r * r + head * head) / (2 * head)
    phi = math.degrees(math.asin(r / R))
    for y in (yc - r, yc + r):
        line((x0 + head, y), (x1 - head, y), "TANK")
    for x in (x0 + head, x1 - head):
        line((x, yc - r), (x, yc + r), "TANK")
    arc((x0 + R, yc), R, 180 - phi, 180 + phi, "TANK")
    arc((x1 - R, yc), R, -phi, phi, "TANK")
    for s, p, a in zip(labels, label_pos, (48, 60)):
        text(s, p, a, 0.3)


TL54, TR54 = XL + WT + 1.0, W - WT - 1.5      # 1.0 and 1.5 clear to the walls -> 10.0 long
D54 = 2.75
yc_go = Y0 + WT + 1.0 + D54 / 2               # gas oil tank
yc_b1 = Y2 + WT + 1.0 + D54 / 2
yc_b2 = yc_b1 + D54 + 1.0
yc_k = SEP + WT + 1.0 + D54 / 2
for yc, name in ((yc_go, "خزان زيت\\Pالغاز"), (yc_b1, "خزان\\Pالبنزين"), (yc_b2, "خزان\\Pالبنزين"),
                 (yc_k, "خزان النفط\\Pالأبيض")):
    tank(TL54, TR54, yc, D54, 1.0, ("سعة 54 م3", name), ((40.3, yc), (46.4, yc)))
    xc = (TL54 + TR54) / 2
    pline([(xc - 0.8, yc - 0.8), (xc + 0.8, yc - 0.8), (xc + 0.8, yc + 0.8), (xc - 0.8, yc + 0.8)],
          "TANK-FIT", close=True)
    circle((xc, yc), 0.45, "TANK-FIT")
# two 23 m3 LPG tanks
D23 = 2.3
yB = Y2 - 1.75 - D23 / 2                       # 1.75 to the wall, 3.0 to the first 54 m3 tank
yA = yB - D23 - 1.5
tank(XL + WT + 2.0, XL + WT + 9.0, yA, D23, 0.9, ("خزان غاز\\Pسائل", "سعة 23 م3"), ((40.7, yA), (44.6, yA)))
tank(XL + WT + 1.8, XL + WT + 8.8, yB, D23, 0.9, ("خزان غاز\\Pسائل", "سعة 23 م3"), ((40.5, yB), (44.4, yB)))
circle((W - WT - 7.5, yA), 0.3, "TANK-FIT")
circle((W - WT - 7.5, yB), 0.3, "TANK-FIT")
# LPG pump, 2.0 x 2.0, 1.0 below the wall
pump = box(40.25, Y1 + WT + 1.0, 42.25, Y1 + WT + 3.0)
outline(pump, "TANK-FIT")
hatch(pump, "TANK-FIT", "ANSI31", scale=0.08, angle=math.degrees(TH))
text("مضخات\\Pالغاز السائل", (38.75, pump.bounds[1] + 1.2), 90, 0.3)

# tank-area dimensions (labels as written on the plan)
pb = pump.bounds
dim((41.0, Y0 + WT), (41.0, yc_go - D54 / 2), (41.0, 0), "1", h=0.25)
dim((XL + WT, yc_go + 0.7), (TL54, yc_go + 0.7), (0, yc_go + 0.7), "1", h=0.25)
dim((TR54, yc_go - 0.1), (W - WT, yc_go - 0.1), (0, yc_go - 0.1), "1.5", h=0.25)
dim(((TL54 + TR54) / 2 + 0.2, yc_go), ((TL54 + TR54) / 2 + 0.2, Y1), (43.45, 0), "3.75")
dim((40.7, yc_go), (40.7, pb[1]), (40.7, 0), "5.0")
dim((42.35, Y1 + WT), (42.35, pb[1]), (42.35, 0), "1.0", h=0.25)
dim((pb[2], pb[1]), (pb[2], pb[3]), (42.5, 0), "2.0", h=0.25)
dim((pb[0], pb[3]), (pb[2], pb[3]), (0, pb[3] + 0.5), "2.0", h=0.25)
dim((pb[2], 22.6), (W - WT, 22.6), (0, 22.6), "7.5")
dim((44.0, Y1 + WT), (44.0, yA - D23 / 2), (44.0, 0), "6.9")
dim((W - WT - 7.5, pb[3]), (W - WT - 7.5, yA), (W - WT - 7.5, 0), "5.0")
dim((XL + WT, yA + 0.6), (XL + WT + 2.0, yA + 0.6), (0, yA + 0.6), "2", h=0.25)
dim((41.5, yA + D23 / 2), (41.5, yB - D23 / 2), (41.5, 0), "1.5", h=0.25)
dim((XL + WT, yB + 0.9), (XL + WT + 1.8, yB + 0.9), (0, yB + 0.9), "1.8", h=0.25)
dim((W - WT - 7.5, yB), (W - WT, yB), (0, yB + 1.25), "7.5")
dim((40.3, yB + D23 / 2), (40.3, Y2), (40.3, 0), "1.75", h=0.25)
dim((43.3, yB + D23 / 2), (43.3, yc_b1 - D54 / 2), (43.3, 0), "3.0")
line(pb[:2], (36.5, 29.6), "DIM")
text("6.9", (38.0, 26.0), math.degrees(math.atan2(29.6 - pb[1], 36.5 - pb[0])), 0.3)
line((W - WT - 7.5, yB), (36.5, 37.6), "DIM")
text("7.5", (38.9, 34.6), math.degrees(math.atan2(37.6 - yB, 36.5 - (W - WT - 7.5))), 0.3)
for y_top, y_bot, lab in ((Y2 + WT, yc_b1 - D54 / 2, "1.0"), (yc_b1 + D54 / 2, yc_b2 - D54 / 2, "1.0"),
                          (yc_b2 + D54 / 2, SEP, "1.0"), (SEP + WT, yc_k - D54 / 2, "1.0"),
                          ):
    dim((44.3, y_top), (44.3, y_bot), (44.3, 0), lab, h=0.25)
dim((39.6, yc_k + D54 / 2), (39.6, Y3), (39.6, 0), "1.50", h=0.25)
for yc in (yc_b1, yc_b2, yc_k):
    dim((XL + WT, yc + 0.3), (TL54, yc + 0.3), (0, yc + 0.3), "1.0", h=0.25)
    dim((TR54, yc - 0.1), (W - WT, yc - 0.1), (0, yc - 0.1), "1.5", h=0.25)
text("سياج بارتفاع لا يقل عن 2م", (44.2, Y3 - 0.3), 0, 0.25)

# unloading points on the curb: 15.0 | 8.0 | 4.00
FP_Y = (14.6, 29.6, 37.6, 41.6)
FP_NAMES = ("نقطة تفريغ\\Pزيت الغاز", "نقطة تفريغ\\Pالغاز السائل", "نقطة تفريغ\\Pالبنزين",
            "نقطة تفريغ\\Pالنفط الأبيض")
for yc, name in zip(FP_Y, FP_NAMES):
    x0, x1 = 36.2, 36.8
    pline([(x0, yc - 0.3), (x1, yc - 0.3), (x1, yc + 0.3), (x0, yc + 0.3)], "FILL-POINT", close=True)
    pline([(x0 + 0.1, yc - 0.2), (x1 - 0.1, yc - 0.2), (x1 - 0.1, yc + 0.2), (x0 + 0.1, yc + 0.2)],
          "FILL-POINT", close=True)
    line((x0 + 0.1, yc - 0.2), (x1 - 0.1, yc + 0.2), "FILL-POINT")
    line((x0 + 0.1, yc + 0.2), (x1 - 0.1, yc - 0.2), "FILL-POINT")
    ladder((36.0, yc - 0.6), (0, 1), (1, 0), 1.2, 0.15, step=0.15, layer="FILL-POINT")
    line((35.1, yc), (36.0, yc), "FILL-POINT")
    text(name, (34.3, yc + 1.3), 90, 0.35)
for (y0, y1), lab in zip(zip(FP_Y, FP_Y[1:]), ("15.0", "8.0", "4.00")):
    dim((36.5, y0), (36.5, y1), (35.35, 0), lab, h=0.35)

# ================================================================== paving (1.0 m walks and curbs)
R = 0.75                                      # corner radius written on the plan
CURB_TOP = 6.25 + 6.0                         # 6.0 from the rear walk to the curb of the tank area


def at_t(x, t):
    """Point on the line x = const whose inward distance from the front is t."""
    return (x, LL + (t - x * NIN[0]) / NIN[1])


def s_of(p):
    return (p[0] - A[0]) * U[0] + (p[1] - A[1]) * U[1]


def unit(v):
    L = math.hypot(*v)
    return (v[0] / L, v[1] / L)


def fillet(P, d1, d2, r, n=8):
    """Arc points rounding the corner at P between rays d1 and d2 (unit vectors leaving P)."""
    ang = math.acos(max(-1.0, min(1.0, d1[0] * d2[0] + d1[1] * d2[1])))
    t = r / math.tan(ang / 2)
    T1, T2 = mv(P, d1, t), mv(P, d2, t)
    bis = unit((d1[0] + d2[0], d1[1] + d2[1]))
    cen = mv(P, bis, r / math.sin(ang / 2))
    a1 = math.degrees(math.atan2(T1[1] - cen[1], T1[0] - cen[0]))
    a2 = math.degrees(math.atan2(T2[1] - cen[1], T2[0] - cen[0]))
    if a2 - a1 > 180:
        a2 -= 360
    if a1 - a2 > 180:
        a2 += 360
    return arc_pts(cen, r, a1, a2, n)


# curb of the tank area: 1.0 wide, ends at the front in a 0.75 foot that runs to the entrance pier
WALK_T = 0.75                                 # inner edge of the walk along the front fence
foot_c = at_t(36.0 - R, WALK_T + R)
a_foot = math.degrees(math.atan2(-NIN[1], -NIN[0]))
foot_t = mv(foot_c, NIN, -R)
band2 = Polygon(
    [(13.25, WT), (W - WT, WT), (W - WT, Y0), (XL, Y0), (XL, 70.0), fr(41.78, -1.0), fr(41.78, WALK_T)]
    + arc_pts(foot_c, R, a_foot, 0, 12)
    + arc_pts((36.0 + R, CURB_TOP + R), R, 180, 270, 8)
    + arc_pts((48.25 - R, CURB_TOP - R), R, 90, 0, 8)
    + [(48.25, 6.25), (13.25, 6.25)])
band2 = band2.intersection(INNER).difference(unary_union([B2, B3, g_poly, front_box(41.28, 41.78, -1, PIER)]))
bulge_pline([(*fr(41.78, PIER), 0), (*fr(41.78, WALK_T), 0), (*foot_t, -bulge_of(a_foot)),
             (36.0, foot_c[1], 0), (36.0, CURB_TOP + R, bulge_of(90)), (36.0 + R, CURB_TOP, 0),
             (48.25 - R, CURB_TOP, -bulge_of(90)), (48.25, CURB_TOP - R, 0), (48.25, 6.25, 0),
             (13.25, 6.25, 0), (13.25, WT, 0)], "PAVING")

# walk along the left boundary and around building 1, with the paved pad in front of it
band1 = unary_union([
    box(WT, WT, 11.5, 1.25),
    Polygon([(WT, WT), (1.25, WT), (1.25, 40.0), (WT, 40.0)]),
    Polygon([(1.25, 5.75), (3.0, 5.75)] + arc_pts((2.25, 5.75), R, 0, 90) + arc_pts((2.0, 7.25), R, 270, 180)),
    pad,
]).intersection(INNER).difference(unary_union([B1, front_box(1.5, 2.0, -1, PIER)]))
bulge_pline([(*at_t(1.25, WT), 0), (1.25, 7.25, bulge_of(90)), (2.0, 6.5, 0), (2.25, 6.5, -bulge_of(90)),
             (3.0, 5.75, 0)], "PAVING")
line((11.5, WT), (11.5, 1.25), "PAVING")

# kerosene yard (bottom right): rounded yard outline, open towards the 5 m gate
ZX0, ZY0, ZX1 = 39.25, Y3 + WT + 2.43, W - WT - 0.75     # 39.25 / 51.2 / 49.0
zone = Polygon([(XL + WT, Y3 + WT), (W - WT, Y3 + WT), (W - WT, 80), (XL + WT, 80)]).intersection(INNER)
p_bl, p_br = at_t(ZX0, WALK_T), at_t(ZX1, WALK_T)
p_tl, p_tr = (ZX0, ZY0), (ZX1, ZY0)
yard = (fillet(p_tl, (0, 1), (1, 0), R) + fillet(p_tr, (-1, 0), (0, 1), R)
        + fillet(p_br, (0, -1), unit((p_bl[0] - p_br[0], p_bl[1] - p_br[1])), R)
        + fillet(p_bl, unit((p_br[0] - p_bl[0], p_br[1] - p_bl[1])), (0, -1), R))
yard_poly = Polygon(yard)
gate_gap = front_box(49.28, 54.28, -0.5, WALK_T + 0.3)
zone_band = zone.difference(unary_union([yard_poly, gate_gap, box(XL + WT, Y3 + WT, ZX0, ZY0),
                                        box(38.75, ZY0, ZX0, 80), box(47.75, Y3 + WT, ZX1, ZY0)]))
for part in lines_of(LineString(yard + [yard[0]]).difference(gate_gap)):
    pline(list(part.coords), "PAVING")
line((38.75, ZY0), at_t(38.75, WT), "PAVING")
line((XL + WT, ZY0), (38.75, ZY0), "PAVING")

for g in (band1, band2, zone_band):
    hatch(g, "PAVING-HATCH", "AR-SAND", scale=0.02, color=8)

# ================================================================== kerosene yard furniture
plat = box(ZX0, Y3 + WT, 47.75, Y3 + WT + 2.18)
outline(plat, "ISLAND")
yI = Y3 + WT + 1.48


def d_symbol(c, facing, layer="ISLAND", r=0.18):
    """'D' end-stop of an island: flat side, round side towards `facing` (plot-frame angle)."""
    t = math.radians(facing)
    ux, uy = math.cos(t), math.sin(t)
    a = mv(c, (-uy, ux), r)
    b = mv(c, (uy, -ux), r)
    line(a, b, layer)
    arc(c, r, facing - 90, facing + 90, layer)


def dispenser(c, along_deg, layer="ISLAND", l=0.5, w=0.24):
    t = math.radians(along_deg)
    u = (math.cos(t), math.sin(t))
    n = (-u[1], u[0])
    p0 = mv(mv(c, u, -l / 2), n, -w / 2)
    path = [(*p0, 0), (*mv(p0, u, l), bulge_of(180)), (*mv(mv(p0, u, l), n, w), 0), (*mv(p0, n, w), bulge_of(180))]
    bulge_pline(path, layer, close=True)


def post(c, along_deg, s=0.24, layer="ISLAND"):
    t = math.radians(along_deg)
    u = (math.cos(t), math.sin(t))
    n = (-u[1], u[0])
    q = mv(mv(c, u, -s / 2), n, -s / 2)
    pline([q, mv(q, u, s), mv(mv(q, u, s), n, s), mv(q, n, s)], layer, close=True)


d_symbol((40.0, yI), 180)
dispenser((41.75, yI), 0)
post((43.5, yI), 0)
dispenser((45.25, yI), 0)
d_symbol((46.95, yI), 0)
ladder((39.75, Y3 + WT + 2.18), (1, 0), (0, 1), 7.5, 0.25)
dim((41.75, yI), (45.25, yI), (0, ZY0 + 0.45), "3.5")
apex = (43.4, ZY0 + 1.75)
line((41.75, yI), apex, "TEXT")
line((45.25, yI), apex, "TEXT")
text("مضخات النفط\\Pالأبيض", (43.4, ZY0 + 3.2), 90, 0.3)
pline([(47.75, Y3 + WT), (47.75, ZY0 - 0.25)], "ISLAND")
pline([(48.0, Y3 + WT), (48.0, ZY0 - 0.25)], "ISLAND")
dim((48.0, Y3 + WT), (48.0, Y3 + WT + 2.0), (48.55, 0), "2.0", h=0.25)
dim((49.35, Y3 + WT), (49.35, Y3 + WT + 2.0), (49.35, 0), "2.0", h=0.25)
dim((48.0, ZY0 + 0.3), (ZX1, ZY0 + 0.3), (0, ZY0 + 0.3), "1.0", h=0.25)
bulge_pline(rrect_path(ZX0 + 0.15, Y3 + WT, ZX1 - 0.2, ZY0 + 1.25, 0.75), "CANOPY", close=True)
# hand-cart island along the left walk
xI = 38.0
d_symbol((xI, ZY0 + 1.6), 270)
dispenser((xI, ZY0 + 3.0), 90)
d_symbol((xI, ZY0 + 4.3), 90)
bulge_pline(rrect_path(38.85, ZY0 + 1.1, 40.45, ZY0 + 5.5, 0.4), "CANOPY", close=True)
dim((39.35, ZY0 + 1.6), (39.35, ZY0 + 4.3), (39.35, 0), "2.7", h=0.25)
text("جزرة تجهيز النفط الأبيض\\Pللعربات", (40.95, ZY0 + 3.3), 90, 0.25)
text("ساحة النفط\\Pالأبيض", (44.4, 57.5), 90, 0.35)
dim((XL + WT, Y3 + 1.0), (ZX0, Y3 + 1.0), (0, Y3 + 1.0), "2.0", h=0.25)
dim((XL + WT, ZY0 + 0.6), (38.75, ZY0 + 0.6), (0, ZY0 + 0.6), "1.5", h=0.25)
dim((ZX1, 59.2), (W - WT, 59.2), (0, 59.2), "0.75", h=0.25)
# manhole in the corner of the yard
pline([(47.0, 61.0), (48.5, 61.0), (48.5, 62.5), (47.0, 62.5)], "PIPE", close=True)
circle((47.75, 61.75), 0.25, "TANK-FIT")
dot((47.75, 61.75), 0.14, "TANK-FIT")
dim((48.5, 61.0), (48.5, 62.5), (48.8, 0), "1.5", h=0.22)
dim((47.0, 62.5), (48.5, 62.5), (0, 62.8), "1.5", h=0.22)

# ================================================================== canopy and dispenser islands
ISL_L, ISL_W, GAP = 10.0, 1.25, 6.0
Q1 = (1.25 + 14.12, 6.25 + 10.0)               # 14.12 from the walk, 10.0 from the rear walk
step_n, step_u = ISL_W + GAP, (ISL_W + GAP) * U[1] / U[0]   # keep the left ends on one vertical
QS = [mv(mv(Q1, NOUT, k * step_n), U, k * step_u) for k in range(3)]
ISL_NAMES = ("جزرة منتوج زيت الغاز", "جزرة منتوج الغاز السائل", "جزرة منتوج البنزين")


def isl(Q, a, b):
    return mv(mv(Q, U, a), NOUT, b)


for k, Q in enumerate(QS):
    r = ISL_W / 2
    p0, p1 = isl(Q, r, 0), isl(Q, ISL_L - r, 0)
    path = [(*p0, 0), (*p1, bulge_of(180)), (*isl(Q, ISL_L - r, ISL_W), 0), (*isl(Q, r, ISL_W), bulge_of(180))]
    bulge_pline(path, "ISLAND", close=True)
    a_isl = math.degrees(TH)
    d_symbol(isl(Q, 0.45, r), a_isl + 180)
    d_symbol(isl(Q, ISL_L - 0.45, r), a_isl)
    dispenser(isl(Q, 2.0, r), a_isl)
    dispenser(isl(Q, 8.0, r), a_isl)
    post(isl(Q, 5.0, r), a_isl)
    if k == 0:                                   # gas-oil island has kerb strips on both sides
        ladder(isl(Q, 1.4, -0.4), U, NOUT, 7.6, 0.25)
        ladder(isl(Q, 1.0, ISL_W + 0.15), U, NOUT, 7.6, 0.25)
    dim(isl(Q, 0, 0), isl(Q, ISL_L, 0), isl(Q, 5, -0.9 if k else -1.0), "10.0", h=0.35)
    dim(isl(Q, 0, 0), isl(Q, 0, ISL_W), isl(Q, -0.35, 0), "1.25", h=0.25)
    dim(isl(Q, 2.0, r), isl(Q, 8.0, r), isl(Q, 5, ISL_W + 0.9), "6.0", h=0.35)
    text(ISL_NAMES[k], isl(Q, 6.0, -1.75), math.degrees(TH), 0.45)
    if k < 2:
        dim(isl(Q, 7.0, ISL_W), isl(Q, 7.0, ISL_W + GAP), isl(Q, 7.0, ISL_W), "6.00", h=0.35)

# canopy outline (dashed), parallel to the islands, vertical sides
cv = [(14.0, 11.15), (25.0, 11.15 + 11.0 * U[1] / U[0]), (25.0, 37.70 + 11.0 * U[1] / U[0]), (14.0, 37.70)]
cpath = []
for i, P in enumerate(cv):
    pts = fillet(P, unit((cv[i - 1][0] - P[0], cv[i - 1][1] - P[1])), unit((cv[(i + 1) % 4][0] - P[0], cv[(i + 1) % 4][1] - P[1])), R, 6)
    cpath += pts
pline(cpath, "CANOPY", close=True)

# distances of the canopy islands
Q3 = QS[2]
dim((1.25, Q1[1]), Q1, (0, Q1[1]), "14.12", h=0.4)
dim((Q1[0], 6.25), Q1, (Q1[0], 0), "10.0", h=0.4)
low3 = isl(Q3, 6.77, ISL_W)
s3 = (low3[0] - A[0]) * U[0] + (low3[1] - A[1]) * U[1]
dim(low3, fr(s3, 0.336), low3, "4.50", h=0.4)
tip3 = isl(Q3, ISL_L, 0)
dim(tip3, (36.0, tip3[1]), (0, tip3[1]), "12.50", h=0.4)
dim((40.3, 6.25), (40.3, 12.25), (40.3, 0), "6.0", h=0.4)
text("0.75", (43.0, 11.75), 0, 0.25)
text("0.75", (3.25, 7.0), 0, 0.25)
dim((0.25, 11.0), (1.25, 11.0), (0, 11.0), "1.0", h=0.25)

# ================================================================== gates on the front
TK = 0.4                                        # sliding-gate track line, t from the plot line


def gate_bar(s0, s1, t=0.45):
    pline([fr(s0, t), fr(s1, t)], "GATE", width=0.12)


def gate_box(s0, s1, rounded_end):
    t0, t1 = 0.3, 0.62
    r = (t1 - t0) / 2
    b = bulge_of(180)
    if rounded_end == "right":
        path = [(*fr(s0, t0), 0), (*fr(s1 - r, t0), -b), (*fr(s1 - r, t1), 0), (*fr(s0, t1), 0)]
    else:
        path = [(*fr(s0 + r, t0), 0), (*fr(s1, t0), 0), (*fr(s1, t1), 0), (*fr(s0 + r, t1), -b)]
    bulge_pline(path, "GATE", close=True)


def wheel(s):
    dot(fr(s, 0.72), 0.16, "GATE")
    line(fr(s, 0.62), fr(s, 0.42), "GATE")


# exit: 3.0 swing leaf on the left pier + sliding leaf parked to the right
door(fr(2.0, WT), fr(5.0, WT), -1, "GATE")
pline([fr(5.0, 0.35), fr(11.5, 0.35)], "GATE")
pline([fr(5.0, 0.48), fr(11.5, 0.48)], "GATE")
wheel(5.3)
gate_box(12.5, 16.6, "right")
gate_bar(12.7, 16.2)
line(fr(16.3, 0.62), fr(16.3, 1.0), "DIM")
text("0.75", fr(17.0, 1.05), sheet_angle=0, h=0.25)
# entrance: sliding leaf parked to the left + 3.0 swing leaf on the right pier
gate_box(26.4, 30.75, "left")
gate_bar(26.7, 30.5)
pline([fr(31.3, 0.35), fr(38.0, 0.35)], "GATE")
pline([fr(31.3, 0.48), fr(38.0, 0.48)], "GATE")
gate_bar(31.3, 32.3)
gate_bar(37.3, 38.0)
wheel(37.8)
door(fr(41.28, WT), fr(38.28, WT), 1, "GATE")
# 5 m gate of the kerosene yard: two sliding leaves parked behind the side walls
gate_box(45.6, 48.75, "left")
gate_bar(45.8, 48.6)
gate_box(54.8, 58.2, "right")
gate_bar(55.0, 58.0)
for s0, s1, sw in ((49.4, 51.3, 50.9), (52.3, 54.2, 52.6)):
    pline([fr(s0, 0.4), fr(s1, 0.4)], "GATE")
    wheel(sw)
for s in (47.3, 56.4):
    line(fr(s, 0.62), fr(s, 1.0), "DIM")
    text("0.75", fr(s + 0.7, 1.05), sheet_angle=0, h=0.25)


def arrow(s, up, label):
    """Exit / entrance arrow under the front (sheet frame: front point s has sheet x = s)."""
    tip, tail = (-2.0, -4.0) if up else (-4.0, -2.0)
    neck = tip - 0.7 if up else tip + 0.7
    msp.add_lwpolyline([(s, tail), (s, neck)], dxfattribs={"layer": "TEXT", "const_width": 0.15})
    head = [(s - 0.4, neck), (s + 0.4, neck), (s, tip)]
    msp.add_lwpolyline(head, close=True, dxfattribs={"layer": "TEXT"})
    h = msp.add_hatch(color=256, dxfattribs={"layer": "TEXT"})
    h.paths.add_polyline_path(head, is_closed=True)
    e = msp.add_mtext(label, dxfattribs={"layer": "TEXT", "style": "AR", "char_height": 0.7})
    e.set_location((s + (-1.7 if up else 1.7), -3.2), rotation=0,
                   attachment_point=MTextEntityAlignment.MIDDLE_CENTER)


arrow(6.1, False, "خروج")
arrow(38.3, True, "دخول")

# ================================================================== walls
all_walls = unary_union([walls] + wall_parts).intersection(PLOT).difference(unary_union(wall_holes))
outline(all_walls, "WALL", exclude=PLOT.exterior.buffer(0.005))

# ================================================================== site dimensions
# rear 50 and left 30.59 / right 66.02
dim(D, C, (0, -1.5), "50", h=1.3, tad=0, asz=0.35)
dim(A, D, (-1.6, 0), "30.59", h=1.3, tad=0, asz=0.35)
chain = [0.0, Y0, Y1, Y2, Y3, LR]
for (y0, y1), lab in zip(zip(chain[1:], chain[2:]), ("6.4", "15", "14.25", "17.5")):
    dim((W, y0), (W, y1), (W + 0.8, 0), lab, h=0.45, tad=0)
dim((W, Y0), (W, Y3), (W + 1.6, 0), "35.6", h=0.35, tad=0)
dim((W, 0), (W, LR), (W + 2.8, 0), "66.02", h=1.3, tad=0, asz=0.35)
# front chain and overall
marks = [0, 2, 12, 31.28, 41.28, 49.28, 54.28, 61.28]
for (s0, s1), lab in zip(zip(marks, marks[1:]), ("2", "10", "19.28", "10", "8", "5", "7")):
    dim(fr(s0), fr(s1), fr((s0 + s1) / 2, -0.9), lab, h=0.4, tad=0)
dim(A, B, fr(FRONT / 2, -2.6), "61.28", h=1.3, tad=0, asz=0.35)

# ================================================================== title block (sheet frame)
TB = (-18.0, -11.0, 64.0, -5.0)
x0, y0, x1, y1 = TB
msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "TITLE"})
for xv in (-7.0, 57.0):
    msp.add_line((xv, y0), (xv, y1), dxfattribs={"layer": "TITLE"})
TITLE = ("مخطط اولي (لاغراض الكشف الموقعي فقط) لمحطة تعبئة وقود مشيدة والمراد انشائها على قطعة الارض",
         "المرقمة ( ١ / ٣٤٥٣ ) مقاطعة (٤٣) يارمجة الشرقية / قضاء الموصل / محافظة نينوى والعائدة",
         "للمواطنين (هادي حسين جمعة - احمد عثمان عيد)")
for k, s in enumerate(TITLE):
    e = msp.add_mtext(s, dxfattribs={"layer": "TITLE", "style": "AR", "char_height": 0.9})
    e.set_location((56.3, -6.3 - k * 1.7), attachment_point=MTextEntityAlignment.MIDDLE_RIGHT)
for k, s in enumerate(("رقم المخطط :", "مقياس الرسم :")):
    e = msp.add_mtext(s, dxfattribs={"layer": "TITLE", "style": "AR", "char_height": 0.6})
    e.set_location((-7.6, -6.6 - k * 1.4), attachment_point=MTextEntityAlignment.MIDDLE_RIGHT)
e = msp.add_mtext("المهندس", dxfattribs={"layer": "TITLE", "style": "AR", "char_height": 0.5})
e.set_location((63.4, -6.6), attachment_point=MTextEntityAlignment.MIDDLE_RIGHT)

doc.set_modelspace_vport(height=85, center=(23, 22))
doc.saveas(OUT)
print("saved", OUT)
