"""Writes revision 2 of the proposal B master plan (client program of 2026-10-21 evening): DXF (on top of the site plan), A3 PDF/PNG preview and a JSON summary."""
import json
import math
import os
import sys

import ezdxf
import matplotlib
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plan_B_r2 as P  # noqa: E402

SITE_DXF = os.path.join(HERE, "..", "site", "SHALLALAT_SITE_PLAN.dxf")
OUT_DXF = os.path.join(HERE, "SHALLALAT_MASTERPLAN_B_GREEN_HEART_R2.dxf")
OUT_PDF = os.path.join(HERE, "SHALLALAT_MASTERPLAN_B_GREEN_HEART_R2.pdf")
OUT_PNG = os.path.join(HERE, "SHALLALAT_MASTERPLAN_B_GREEN_HEART_R2.png")
OUT_JSON = os.path.join(HERE, "masterplan_B_R2_summary.json")
FONT_DIR = os.environ.get("AR_FONT_DIR", "")

AXIS_DEG = math.degrees(math.atan2(P.U[1], P.U[0]))  # local s axis in UTM (about -18.4 deg)

# --- quantities -------------------------------------------------------------------------------------------
villas = sorted(P.villas, key=lambda g: (round(g.bounds[0]), g.bounds[1]))
houses = sorted(P.houses, key=lambda g: (round(g.bounds[0]), g.bounds[1]))
N_V, N_H = len(villas), len(houses)
N_APT = P.N_TOWERS * 20 * 4
PEOPLE = N_V * 6 + N_H * 6 + (N_APT // 2) * 4 + (N_APT // 2) * 6
site_a = P.SITE.area

services_a = sum(g.area for g in P.SERVICES.values())
greens = {
    "Central park (oval) - الحديقة المركزية البيضوية": P.PARK.area,
    "Orchard green - البستان": P.ORCHARD.area,
    "Pocket gardens, east park, belts & verges - حدائق جيرة وحزام أخضر وأرصفة مزروعة": P.BUFFERS.area,
}
LANDUSE = [
    (f"Villa lots ({N_V} x 400 m2) - قطع الفلل", sum(g.area for g in villas)),
    (f"House lots ({N_H} x 240 m2) - قطع الدور", sum(g.area for g in houses)),
    (f"Tower plaza ({P.N_TOWERS} towers, {N_APT} apts) - بلازا الأبراج", P.TOWER_ZONE.area),
    ("Services & utilities - الخدمات والبنى التحتية", services_a),
    *greens.items(),
    ("Roads (ring, boulevard, avenue, local) - الطرق", P.ALL_ROADS.area),
]
total = sum(a for _, a in LANDUSE)
assert abs(total - site_a) < 5, (total, site_a)
green_total = sum(greens.values())

PROGRAM = P.PROGRAM  # m2, client program of 2026-10-21


def program_of(name):
    for k, v in PROGRAM.items():
        if name.upper().startswith(k) or k in name.upper().split(" - ")[0]:
            return v
    return None


# --- DXF ----------------------------------------------------------------------------------------------------
doc = ezdxf.readfile(SITE_DXF)
msp = doc.modelspace()
for e in list(msp.query("TEXT[layer=='TEXT']")):  # the site plan's plot title sits on the park
    if e.dxf.text.startswith(("PLOT 157", "مقاطعة 53")):
        msp.delete_entity(e)
if "WATER_APPROX" in doc.layers:  # watercourse ignored at the client's request (2026-10-21)
    doc.layers.get("WATER_APPROX").off()
LAYERS = {  # name: (ACI colour, lineweight)
    "MP_HATCH_RES": (31, 0), "MP_HATCH_SERVICE": (202, 0), "MP_HATCH_GREEN": (82, 0), "MP_HATCH_ROAD": (252, 0),
    "MP_HATCH_TOWER": (11, 0), "MP_HATCH_WATER": (151, 0),
    "MP_ROAD_EDGE": (8, 35), "MP_ROAD_CL": (9, 13), "MP_LOT_VILLA": (30, 25), "MP_LOT_HOUSE": (40, 18),
    "MP_LOT_NO": (7, 9), "MP_BLDG_INDICATIVE": (7, 18), "MP_TOWER": (1, 50), "MP_SERVICE": (6, 35),
    "MP_PARK": (3, 35), "MP_GREEN": (82, 25), "MP_PATH": (52, 18), "MP_TREE": (3, 13), "MP_WATER": (5, 35),
    "MP_GATE": (1, 50), "MP_TEXT": (7, 25), "MP_TABLE": (7, 18),
}
for name, (color, lw) in LAYERS.items():
    if name not in doc.layers:
        doc.layers.add(name, color=color, lineweight=lw)


def utm_ring(coords):
    return [P.to_utm(s, t) for s, t in coords]


def polys(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon" and p.area > 1]


def add_outline(g, layer, closed=True):
    for p in polys(g):
        msp.add_lwpolyline(utm_ring(p.exterior.coords[:-1]), close=closed, dxfattribs={"layer": layer})
        for hole in p.interiors:
            msp.add_lwpolyline(utm_ring(hole.coords[:-1]), close=True, dxfattribs={"layer": layer})


def add_hatch(g, layer, color, transparency=0.35):
    for p in polys(g):
        h = msp.add_hatch(color=color, dxfattribs={"layer": layer})
        h.paths.add_polyline_path(utm_ring(p.exterior.coords[:-1]), is_closed=True, flags=1)
        for hole in p.interiors:
            h.paths.add_polyline_path(utm_ring(hole.coords[:-1]), is_closed=True, flags=16)
        h.transparency = transparency


def add_text(txt, s, t, h, layer="MP_TEXT", rot=AXIS_DEG):
    e = msp.add_text(txt, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "AR"})
    e.set_placement(P.to_utm(s, t), align=TextEntityAlignment.MIDDLE_CENTER)


def add_line(coords, layer, linetype=None):
    attrs = {"layer": layer}
    if linetype:
        attrs["linetype"] = linetype
    msp.add_lwpolyline(utm_ring(coords), dxfattribs=attrs)


for lt in ("DASHED", "CENTER", "DOT"):
    if lt not in doc.linetypes:
        doc.linetypes.add(lt, pattern=[2.0, 1.0, -1.0], description=lt)

# fills first so the linework stays on top
add_hatch(P.ALL_ROADS, "MP_HATCH_ROAD", 252, 0.2)
add_hatch(unary_union(villas), "MP_HATCH_RES", 31)
add_hatch(unary_union(houses), "MP_HATCH_RES", 51)
add_hatch(P.TOWER_ZONE, "MP_HATCH_TOWER", 11)
add_hatch(unary_union(list(P.SERVICES.values())), "MP_HATCH_SERVICE", 202)
add_hatch(unary_union([P.PARK, P.ORCHARD, P.BUFFERS]), "MP_HATCH_GREEN", 82)

# roads: edges of the merged network + centre lines
add_outline(P.ALL_ROADS, "MP_ROAD_EDGE")
ring_cl = P.PARK.buffer(P.RING_W / 2, resolution=48).exterior
add_line(list(ring_cl.coords), "MP_ROAD_CL", "CENTER")
add_line([(P.GATE_S, P.PARK_C[1] + P.PARK_B + P.RING_W), (P.GATE_S, P.t_north(P.GATE_S))], "MP_ROAD_CL", "CENTER")
add_line(list(P.CROSS_ROAD.coords), "MP_ROAD_CL", "CENTER")
for tc in P.VILLA_STREETS_T:
    add_line([(P.WEST_LOOP.bounds[0] + 10, tc), (P.avenue_edge(-1, tc), tc)], "MP_ROAD_CL", "CENTER")
for tc in P.HOUSE_STREETS_T:
    add_line([(P.avenue_edge(1, tc), tc), (P.WEST_COLL_S[0], tc)], "MP_ROAD_CL", "CENTER")
add_line([(P.PARK_C[0] + P.PARK_A + P.RING_W, P.PARK_C[1]), (P.EAST_LOOP_S, P.PARK_C[1])], "MP_ROAD_CL", "CENTER")
add_outline(P.BOULEVARD_MEDIAN.difference(P.GATEHOUSE.buffer(2)), "MP_GREEN")
# avenue: planted median
add_outline(P.CROSS_ROAD.buffer(2.5, cap_style=2).intersection(P.SITE).difference(
    P.ALL_ROADS.difference(P.AVENUE).buffer(1)), "MP_GREEN")

# lots, numbers and indicative footprints
for i, lot in enumerate(villas, 1):
    add_outline(lot, "MP_LOT_VILLA")
    add_outline(P.footprint(lot, "V", P.lot_front(lot)), "MP_BLDG_INDICATIVE")
    c = lot.centroid
    add_text(f"V{i:02d}", c.x, c.y, 2.2, "MP_LOT_NO")
for i, lot in enumerate(houses, 1):
    add_outline(lot, "MP_LOT_HOUSE")
    add_outline(P.footprint(lot, "H", P.lot_front(lot)), "MP_BLDG_INDICATIVE")
    c = lot.centroid
    add_text(f"H{i:03d}", c.x, c.y, 1.6, "MP_LOT_NO")

# towers
add_outline(P.TOWER_ZONE, "MP_TOWER")
for i, tw in enumerate(P.TOWERS, 1):
    add_outline(tw, "MP_TOWER")
    add_outline(tw.buffer(-3), "MP_TOWER")
    c = tw.centroid
    add_text(f"TOWER {i} - البرج {i}", c.x, c.y + 3, 3.2, "MP_TOWER")
    add_text("20 FLOORS / 80 APTS", c.x, c.y - 3, 2.6, "MP_TOWER")

# services
for name, g in P.SERVICES.items():
    add_outline(g, "MP_SERVICE")
    c = g.representative_point()
    en, ar = name.split(" - ")
    if g.bounds[2] - g.bounds[0] < 40:  # narrow parcel: label along it
        add_text(ar, c.x - 3, c.y, 3.0, "MP_SERVICE", rot=AXIS_DEG + 90)
        add_text(f"{en}  {g.area:,.0f} m2", c.x + 2.5, c.y, 2.0, "MP_SERVICE", rot=AXIS_DEG + 90)
    else:
        add_text(ar, c.x, c.y + 3, 3.0, "MP_SERVICE")
        add_text(f"{en}  {g.area:,.0f} m2", c.x, c.y - 2.5, 2.0, "MP_SERVICE")
add_outline(P.GATEHOUSE, "MP_GATE")

# greens, paths, water, trees
add_outline(P.PARK, "MP_PARK")
add_outline(P.ORCHARD, "MP_GREEN")
lake = P.affinity.scale(Point(P.PARK_C).buffer(1.0, resolution=64), 32, 14)
lake = P.affinity.translate(lake, -40, 4)
add_outline(lake, "MP_WATER")
cascade = P.affinity.scale(Point(P.PARK_C).buffer(1.0, resolution=32), 9, 9)
cascade = P.affinity.translate(cascade, 0, 34)
add_outline(cascade, "MP_WATER")
park_loop = P.affinity.scale(Point(P.PARK_C).buffer(1.0, resolution=96), P.PARK_A - 12, P.PARK_B - 10).exterior
add_line(list(park_loop.coords), "MP_PATH")
add_line([(P.GATE_S, P.PARK_C[1] + P.PARK_B), (P.GATE_S, P.PARK_C[1] - P.PARK_B)], "MP_PATH")
add_line([(P.GATE_S - 2, P.PARK_C[1] + P.PARK_B), (P.GATE_S - 2, P.PARK_C[1] - P.PARK_B)], "MP_PATH")
for s, t in P.TREES:
    msp.add_circle(P.to_utm(s, t), 4.0, dxfattribs={"layer": "MP_TREE"})
for k in range(0, 9):  # orchard planting grid
    for j in range(0, 5):
        s, t = 44 + k * 6.5, 109 + j * 9.5
        if all(math.dist((s, t), tr) > 7 for tr in P.TREES):
            msp.add_circle(P.to_utm(s, t), 2.0, dxfattribs={"layer": "MP_TREE"})
# trees along the avenue and the ring
for d in (-7.5, 7.5):
    line = P.CROSS_ROAD.parallel_offset(abs(d), "left" if d < 0 else "right")
    for k in range(0, int(line.length // 12) + 1):
        p = line.interpolate(k * 12)
        if P.SITE.contains(p) and not P.ALL_ROADS.difference(P.AVENUE).buffer(2).contains(p):
            msp.add_circle(P.to_utm(p.x, p.y), 2.5, dxfattribs={"layer": "MP_TREE"})
outer_trees = P.PARK.buffer(P.RING_W + 4).exterior
for k in range(0, int(outer_trees.length // 12)):
    p = outer_trees.interpolate(k * 12)
    if not P.BOULEVARD.buffer(3).contains(p) and not P.ALL_ROADS.difference(P.RING).contains(p):
        msp.add_circle(P.to_utm(p.x, p.y), 2.5, dxfattribs={"layer": "MP_TREE"})
inner_trees = P.PARK.buffer(-4).exterior
for k in range(0, int(inner_trees.length // 10)):
    p = inner_trees.interpolate(k * 10)
    if abs(p.x - P.GATE_S) > 8:
        msp.add_circle(P.to_utm(p.x, p.y), 2.5, dxfattribs={"layer": "MP_TREE"})

# gates
gates = [
    ("MAIN GATE - البوابة الرئيسية", P.GATE_S, P.t_north(P.GATE_S), 1),
    ("SECONDARY GATE - بوابة ثانوية", sum(P.WEST_COLL_S) / 2, 0.0, -1),
]
for label, s, t, side in gates:
    add_line([(s - 8, t), (s + 8, t)], "MP_GATE")
    add_line([(s - 8, t - 2 * side), (s - 8, t + 2 * side)], "MP_GATE")
    add_line([(s + 8, t - 2 * side), (s + 8, t + 2 * side)], "MP_GATE")
    add_text(label, s, t + side * 9, 3.0, "MP_GATE")

# zone labels
for txt, s, t, h in [
    ("THE GREEN HEART - القلب الأخضر", P.PARK_C[0], P.PARK_C[1] + 12, 6),
    (f"CENTRAL PARK {P.PARK.area:,.0f} m2 - حديقة الشلالات المركزية", P.PARK_C[0], P.PARK_C[1] - 18, 3.5),
    ("RING ROAD 16 m - الطريق الحلقي", P.PARK_C[0] - 70, P.PARK_C[1] + P.PARK_B + 4, 2.6),
    ("ORCHARD VILLAS - حي فلل البستان", 60, 278, 5),
    ("ORCHARD - البستان", 68, 128, 3.5),
    ("NEIGHBOURHOOD PARK - حديقة حي الدور", 215, 228, 4),
    ("EAST VILLAS - حي الفلل الشرقي", 729, 176, 3.0),
    ("TOWER PLAZA (BASEMENT PARKING ~360 CARS) - بلازا الأبراج", 420, 160, 3.0),
    ("EAST PARK - الحديقة الشرقية", 840, 110, 3.0),
    ("NORTH GREEN BELT - حزام أخضر", 120, 292, 3),
]:
    add_text(txt, s, t, h)
# avenue label along its own direction
av_deg = AXIS_DEG + math.degrees(math.atan2(P.CROSS_ROAD.coords[1][1] - P.CROSS_ROAD.coords[0][1],
                                              P.CROSS_ROAD.coords[1][0] - P.CROSS_ROAD.coords[0][0]))
add_text("ORCHARD AVENUE 20 m (EX CROSS ROAD - NEEDS APPROVAL) - جادة البستان", 133, 140, 2.6, rot=av_deg)
add_text("GATE BOULEVARD 24 m", P.GATE_S, 190, 2.4, rot=AXIS_DEG + 90)
add_text("WEST COLLECTOR 16 m", 308, 210, 2.4, rot=AXIS_DEG + 90)

# table
x0, y0 = 338470.0, 4035590.0
rows = [
    ("MASTER PLAN - PROPOSAL B: THE GREEN HEART - REV. 2", 6.0),
    ("المخطط العام - المقترح ب: القلب الأخضر - التعديل 2", 6.0),
    ("Plot 157 / District 53 Baybokht - NIC opportunity 5/2026", 3.6),
    ("", 3.6),
    ("LAND USE                                          AREA m2      %", 3.6),
]
rows += [(f"{n[:52]:<52}{a:>10,.0f}  {100 * a / site_a:5.1f}", 3.2) for n, a in LANDUSE]
rows += [(f"{'TOTAL':<52}{site_a:>10,.0f}  100.0", 3.4), ("", 3.2)]
rows += [
    ("UNITS                                             No.   PERSONS", 3.6),
    (f"{'Villas 400 m2 (16 x 25) - فلل':<50}{N_V:>5}   {N_V * 6:>6}", 3.2),
    (f"{'Houses 240 m2 (10 x 24) - دور':<50}{N_H:>5}   {N_H * 6:>6}", 3.2),
    (f"{'Apartments M2 140 m2 (3 towers x 20 x 2)':<50}{N_APT // 2:>5}   {N_APT // 2 * 4:>6}", 3.2),
    (f"{'Apartments M3 180 m2 (3 towers x 20 x 2)':<50}{N_APT // 2:>5}   {N_APT // 2 * 6:>6}", 3.2),
    (f"{'TOTAL':<50}{N_V + N_H + N_APT:>5}   {PEOPLE:>6}", 3.4),
    ("", 3.2),
    (f"Gross density {PEOPLE / (site_a / 1e4):.0f} persons/ha (guide 50-130)  |  "
     f"green space {green_total / PEOPLE:.1f} m2/person", 3.2),
    ("", 3.2),
    ("SERVICES                                          PLAN m2   PROGRAM m2", 3.6),
]
for name, g in P.SERVICES.items():
    prog = program_of(name)
    rows.append((f"{name.split(' - ')[0][:50]:<50}{g.area:>8,.0f}   {prog if prog else '-':>8}", 3.0))
rows += [
    ("", 3.2),
    ("NOTES", 3.6),
    ("1. Merging the existing cross road into the plan (Orchard Avenue) needs the", 3.0),
    ("   approval of the municipality / NIC - raise it at the 25/10 conference.", 3.0),
    ("2. Roads: ring 16 m, gate boulevard 24 m, collector 16 m, avenue 20 m, local 14 m.", 3.0),
    ("3. Building footprints are indicative (villa 30 %, house 60 % coverage).", 3.0),
    ("4. Towers 31.5 x 31.5 m, 33 m apart, 12 m off the fence, on a plaza over ~360 basement spaces.", 3.0),
    ("5. Watercourse and club dropped at the client's request; leftover land is green.", 3.0),
    ("6. Two gates only, both on the long sides; no streets along the short ends.", 3.0),
]
y = y0
for txt, h in rows:
    msp.add_text(txt, height=h, dxfattribs={"layer": "MP_TABLE", "style": "AR"}).set_placement(
        (x0, y), align=TextEntityAlignment.TOP_LEFT)
    y -= h * 1.7

doc.saveas(OUT_DXF)

# --- preview (A3 landscape, 1:2500) --------------------------------------------------------------------------
if FONT_DIR:
    for f in os.listdir(FONT_DIR):
        if f.endswith(".ttf"):
            try:
                font_manager.fontManager.addfont(os.path.join(FONT_DIR, f))
            except RuntimeError:
                pass
plt.rcParams["font.family"] = ["Noto Sans Arabic", "DejaVu Sans"]


def ar(s):
    return s  # matplotlib >= 3.10 shapes and orders Arabic itself (libraqm)


def bil(name):
    en, a = name.split(" - ")
    return f"{ar(a)}\n{en}"


COL = {"villa": "#f3c58f", "house": "#f7e39a", "tower": "#e88f8f", "service": "#c9b3e6", "park": "#8fcf7a",
       "green": "#b9e0a5", "road": "#d9d9d9", "water": "#7fb8e6", "buffer": "#dcefd2"}

W_MM, H_MM, SCALE = 420, 297, 2500
fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
xs, ys = zip(*P.Q_UTM)
cx, cy = (min(xs) + max(xs)) / 2 + 40, (min(ys) + max(ys)) / 2 - 25
wm, hm = W_MM / 1000 * SCALE, H_MM / 1000 * SCALE
ax.set_xlim(cx - wm / 2, cx + wm / 2)
ax.set_ylim(cy - hm / 2, cy + hm / 2)
ax.set_aspect("equal")
ax.axis("off")


def fill(g, fc, ec="none", lw=0.0, z=1, alpha=1.0):
    for p in polys(g):
        verts, codes = [], []
        for ring in [p.exterior, *p.interiors]:
            pts = utm_ring(ring.coords)
            verts += pts
            codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha))


def line(coords, **kw):
    x, y = zip(*utm_ring(coords))
    ax.plot(x, y, **kw)


def label(txt, s, t, size, rot=AXIS_DEG, z=20, **kw):
    x, y = P.to_utm(s, t)
    ax.text(x, y, txt, fontsize=size, rotation=rot, rotation_mode="anchor", ha="center", va="center", zorder=z,
            linespacing=1.05, **kw)


# context: external roads, scan watercourse, raw coordinate polygon
for a, b in ((3, 0), (1, 2)):
    p0, p1 = P.Q_UTM[a], P.Q_UTM[b]
    for d in (0, 12):
        u = (p1[0] - p0[0], p1[1] - p0[1])
        L = math.hypot(*u)
        n = (-u[1] / L, u[0] / L) if (a, b) == (3, 0) else (-u[1] / L, u[0] / L)
        q0 = (p0[0] + n[0] * (4.84 + d) - u[0] / L * 60, p0[1] + n[1] * (4.84 + d) - u[1] / L * 60)
        q1 = (p1[0] + n[0] * (4.84 + d) + u[0] / L * 60, p1[1] + n[1] * (4.84 + d) + u[1] / L * 60)
        ax.plot([q0[0], q1[0]], [q0[1], q1[1]], color="#999", lw=0.5, zorder=0)
raw = [(338954.0, 4035462.0), (339032.0, 4035771.0), (339836.0, 4035336.0), (339747.0, 4035198.0)]
ax.plot(*zip(*(raw + raw[:1])), color="#b05fb0", lw=0.4, ls="--", zorder=0)

fill(P.SITE, "#f4f1ea", z=0)
fill(P.BUFFERS, COL["buffer"], z=1)
fill(P.ALL_ROADS, COL["road"], "#8c8c8c", 0.3, z=2)
fill(P.PARK, COL["park"], "#3f8f3f", 0.5, z=2)
fill(P.ORCHARD, COL["green"], "#3f8f3f", 0.3, z=2)
fill(lake, COL["water"], "#3a78b5", 0.3, z=3)
fill(cascade, COL["water"], "#3a78b5", 0.3, z=3)
line(list(park_loop.coords), color="#f4ecd8", lw=1.4, zorder=3)
line([(P.GATE_S, P.PARK_C[1] + P.PARK_B), (P.GATE_S, P.PARK_C[1] - P.PARK_B)], color="#f4ecd8", lw=2.2, zorder=3)
fill(P.BOULEVARD_MEDIAN.difference(P.GATEHOUSE.buffer(2)), COL["green"], z=3)
fill(P.CROSS_ROAD.buffer(2.5, cap_style=2).intersection(P.SITE).difference(
    P.ALL_ROADS.difference(P.AVENUE).buffer(1)), COL["green"], z=3)
for lot in villas:
    fill(lot, COL["villa"], "#9a6b3a", 0.3, z=4)
    fill(P.footprint(lot, "V", P.lot_front(lot)), "#ffffff", "#6b4a2a", 0.3, z=5)
for lot in houses:
    fill(lot, COL["house"], "#9a8a3a", 0.25, z=4)
    fill(P.footprint(lot, "H", P.lot_front(lot)), "#ffffff", "#6b5f2a", 0.25, z=5)
fill(P.TOWER_ZONE, "#f6d2d2", "#a33", 0.4, z=4)
for tw in P.TOWERS:
    fill(tw, COL["tower"], "#7a1f1f", 0.8, z=5)
for g in P.SERVICES.values():
    fill(g, COL["service"], "#5b3f8a", 0.5, z=4)
fill(P.GATEHOUSE, "#b33", z=6)
fill(P.SITE, "none", "#c00000", 1.2, z=7)

tree_pts = [(s, t) for s, t in P.TREES]
tree_pts += [(44 + k * 6.5, 109 + j * 9.5) for k in range(9) for j in range(5)]
for p in [outer_trees.interpolate(k * 12) for k in range(int(outer_trees.length // 12))]:
    if not P.BOULEVARD.buffer(3).contains(p) and not P.ALL_ROADS.difference(P.RING).contains(p):
        tree_pts.append((p.x, p.y))
for p in [inner_trees.interpolate(k * 10) for k in range(int(inner_trees.length // 10))]:
    if abs(p.x - P.GATE_S) > 8:
        tree_pts.append((p.x, p.y))
for d in (-7.5, 7.5):
    ln = P.CROSS_ROAD.parallel_offset(abs(d), "left" if d < 0 else "right")
    for k in range(int(ln.length // 12) + 1):
        p = ln.interpolate(k * 12)
        if P.SITE.contains(p) and not P.ALL_ROADS.difference(P.AVENUE).buffer(2).contains(p):
            tree_pts.append((p.x, p.y))
tx, ty = zip(*[P.to_utm(s, t) for s, t in tree_pts])
ax.scatter(tx, ty, s=4, c="#2f7a2f", zorder=6, linewidths=0)

for i, tw in enumerate(P.TOWERS, 1):
    c = tw.centroid
    label(f"{ar(f'البرج {i}')}\n20F", c.x, c.y, 4.2, z=21, color="white", weight="bold")
for name, g in P.SERVICES.items():
    c = g.representative_point()
    size = 3.6 if g.area > 2500 else 3.0
    narrow = g.bounds[2] - g.bounds[0] < 40
    label(bil(name), c.x, c.y, size, rot=AXIS_DEG + (90 if narrow else 0), z=21, color="#2d1f4a")
for txt, s, t, size in [
    (ar("القلب الأخضر") + "\nTHE GREEN HEART", P.PARK_C[0] + 40, P.PARK_C[1] + 6, 6.5),
    (ar(f"حديقة الشلالات {P.PARK.area:,.0f} م²"), P.PARK_C[0] + 40, P.PARK_C[1] - 16, 4.2),
    (ar("حي فلل البستان") + "\nORCHARD VILLAS", 60, 285, 5.5),
    (ar("البستان"), 68, 128, 4.2),
    (ar("حديقة حي الدور") + "\nNEIGHBOURHOOD PARK", 215, 228, 4.6),
    (ar("حي الفلل الشرقي") + "\nEAST VILLAS", 729, 178, 3.8),
    (ar("الحديقة الشرقية") + "\nEAST PARK", 845, 115, 3.8),
    (ar("بلازا الأبراج - مواقف تحت الأرض"), 420, 163, 3.4),
    (ar("حزام أخضر"), 130, 290, 3.2),
]:
    label(txt, s, t, size, color="#1f3b1f", weight="bold")
label(ar("جادة البستان 20 م (الشارع العرضي مدموجاً: يحتاج موافقة)"), 133, 150, 3.4, rot=av_deg, color="#333")
label(ar("الطريق الحلقي 16 م"), P.PARK_C[0] - 85, P.PARK_C[1] + 47, 3.2, rot=AXIS_DEG + 22, color="#333")
for lbl, s, t, side in gates:
    x, y = P.to_utm(s, t)
    ax.plot(x, y, marker="v" if side > 0 else "^", ms=7, color="#c00000", zorder=22)
    en, a = lbl.split(" - ")
    label(f"{ar(a)}", s, t + side * 13, 3.8, color="#c00000", weight="bold")

# title block (top right), legend, table (bottom left)
X0, Y1 = cx + wm / 2, cy + hm / 2


def tx_(x, y, s, size, **kw):
    ax.text(x, y, s, fontsize=size, zorder=30, **kw)


tx_(X0 - 12, Y1 - 14, ar("المخطط العام - المقترح ب: القلب الأخضر (التعديل 2)"), 15, ha="right", va="top", weight="bold")
tx_(X0 - 12, Y1 - 44, "MASTER PLAN - PROPOSAL B: THE GREEN HEART - REV. 2", 10, ha="right", va="top")
tx_(X0 - 12, Y1 - 64, ar("مجمع الشلالات السكني · القطعة 157 مقاطعة 53 بايبوخت · فرصة هيئة استثمار نينوى 5/2026"),
    7.5, ha="right", va="top")
tx_(X0 - 12, Y1 - 82, f"UTM 38S  ·  SCALE 1:2500 (A3)  ·  {site_a:,.0f} m2  ·  2026-10-21", 6.5, ha="right", va="top",
    color="#555")
legend = [(COL["villa"], f"{ar('فلل 400 م²')}  ({N_V})"), (COL["house"], f"{ar('دور 240 م²')}  ({N_H})"),
          (COL["tower"], ar("3 أبراج 20 طابقاً (240 شقة)")), (COL["service"], ar("خدمات وبنى تحتية")),
          (COL["park"], ar("الحديقة المركزية")), (COL["green"], ar("حدائق جيرة وبستان وأحزمة خضراء")),
          (COL["road"], ar("طرق")), (COL["water"], ar("ماء"))]
for i, (c, t) in enumerate(legend):
    yy = Y1 - 110 - i * 17
    ax.add_patch(plt.Rectangle((X0 - 40, yy - 5), 26, 11, fc=c, ec="#555", lw=0.4, zorder=30))
    tx_(X0 - 46, yy, t, 7, ha="right", va="center")

XL, YB = cx - wm / 2 + 6, cy - hm / 2 + 10
trow = [(ar("استعمالات الأرض"), "m²", "%")]
trow += [(ar(n.split(" - ")[1]), f"{a:,.0f}", f"{100 * a / site_a:.1f}") for n, a in LANDUSE]
trow += [(ar("المجموع"), f"{site_a:,.0f}", "100")]
trow += [("", "", ""), (ar("الوحدات السكنية"), ar("العدد"), ar("السكان"))]
trow += [(ar("فلل 400 م²"), f"{N_V}", f"{N_V * 6}"), (ar("دور 240 م²"), f"{N_H}", f"{N_H * 6}"),
         (ar("شقق M2 140 م²"), f"{N_APT // 2}", f"{N_APT // 2 * 4}"),
         (ar("شقق M3 180 م²"), f"{N_APT // 2}", f"{N_APT // 2 * 6}"),
         (ar("المجموع"), f"{N_V + N_H + N_APT}", f"{PEOPLE:,}")]
trow += [("", "", ""), (ar(f"الكثافة الإجمالية {PEOPLE / (site_a / 1e4):.0f} شخص/هكتار"), "", ""),
         (ar(f"الخضرة العامة {green_total / PEOPLE:.1f} م² للفرد"), "", "")]
for i, (a, b, c) in enumerate(trow[::-1]):
    yy = YB + i * 10.5
    bold = a in (ar("المجموع"), ar("استعمالات الأرض"), ar("الوحدات السكنية"))
    tx_(XL + 215, yy, a, 5.6, ha="right", va="bottom", weight="bold" if bold else "normal")
    tx_(XL + 268, yy, b, 5.6, ha="right", va="bottom")
    tx_(XL + 300, yy, c, 5.6, ha="right", va="bottom")

# north arrow + scale bar
nx, ny = X0 - 60, cy - hm / 2 + 120
ax.annotate("", xy=(nx, ny + 45), xytext=(nx, ny), arrowprops=dict(arrowstyle="-|>", lw=1.2, color="k"), zorder=30)
tx_(nx, ny + 52, "N", 11, ha="center", va="bottom", weight="bold")
sx, sy = X0 - 230, cy - hm / 2 + 40
for i in range(5):
    ax.add_patch(plt.Rectangle((sx + i * 20, sy), 20, 5, fc="k" if i % 2 == 0 else "w", ec="k", lw=0.5, zorder=30))
    tx_(sx + i * 20, sy - 4, f"{i * 20}", 5.5, ha="center", va="top")
tx_(sx + 100, sy - 4, "100 m", 5.5, ha="center", va="top")

fig.savefig(OUT_PDF)
fig.savefig(OUT_PNG, dpi=220)

summary = {
    "villas": N_V, "houses": N_H, "apartments": N_APT, "units": N_V + N_H + N_APT, "persons": PEOPLE,
    "site_m2": round(site_a), "park_m2": round(P.PARK.area), "green_m2_per_person": round(green_total / PEOPLE, 1),
    "density_pph": round(PEOPLE / (site_a / 1e4)),
    "landuse": {n: round(a) for n, a in LANDUSE},
    "services": {n: round(g.area) for n, g in P.SERVICES.items()},
}
json.dump(summary, open(OUT_JSON, "w"), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
