"""DXF master plan + PDF/PNG preview for proposal A ("the axis") of the Shallalat residential complex.

Geometry comes from layout_A_r2.py (local plot frame) and is written in UTM 38S metres, on the same
coordinates as shallalat_housing/site/SHALLALAT_SITE_PLAN.dxf, so the two drawings overlay exactly.
"""
import math
import os

import arabic_reshaper
import ezdxf
import matplotlib
import numpy as np
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

import layout_A_r2 as L

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DXF = os.path.join(HERE, "SHALLALAT_MASTERPLAN_A_R2.dxf")
OUT_PDF = os.path.join(HERE, "SHALLALAT_MASTERPLAN_A_R2_preview.pdf")
OUT_PNG = os.path.join(HERE, "SHALLALAT_MASTERPLAN_A_R2_preview.png")


def parts(g):
    if g is None or g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon" and p.area > 0.5]


# ================================================================ land-use accounting (no overlaps)
roads_main = unary_union([L.main_roads])
roads_service = L.service_street
roads_local = unary_union(L.local_streets + L.connectors + L.turn_heads + [L.west_street])
roads_west = unary_union([L.tower_drive, L.west_road])
roads_public = L.cross_row
plots_v = unary_union(L.plots["V"])
plots_h = unary_union(L.plots["H"])

CATS = [  # key, english, arabic, geometry, group
    ("V", "Villa plots 400 m2", "قطع فلل 400 م²", plots_v, "RES"),
    ("H", "House plots 240 m2", "قطع دور 240 م²", plots_h, "RES"),
    ("T", "Tower plaza (3 towers x 20 floors)", "بلازا الأبراج (3 × 20 طابق)", L.tower_zone, "RES"),
]
for k, (ar, g, _need) in L.SERVICES.items():
    CATS.append(("S:" + k, k.title(), ar, g, "SRV"))
CATS += [
    ("G1", "Shallalat garden (cascades + lake)", "حديقة الشلالات (شلالات وبحيرة)", L.shallalat_garden, "GRN"),
    ("G2", "Orchard garden", "حديقة البستان", L.orchard, "GRN"),
    ("G3", "Public garden (west)", "الحديقة العامة (الغرب)", L.public_garden, "GRN"),
    ("G4", "Wooded island + medians", "الجزيرة المشجرة والجزرات الوسطية",
     unary_union([L.rb_island, L.gate_median, L.blvd_median]), "GRN"),
    ("R1", "Boulevard 24 m, roundabout, gate street", "البوليفارد 24 م والدوار وشارع البوابة", roads_main, "ROD"),
    ("R2", "Service street 16 m", "الشارع الخدمي 16 م", roads_service, "ROD"),
    ("R3", "Local streets 12 m", "الشوارع المحلية 12 م", roads_local, "ROD"),
    ("R4", "Tower drive + west service road", "مدخل البرجين وشارع الخدمات الغربي", roads_west, "ROD"),
    ("R5", "Cross road 12 m (public, kept)", "الشارع العرضي 12 م (عام)", roads_public, "ROD"),
]
assigned = Polygon()
AREAS = []
for key, en, ar, g, grp in CATS:
    net = g.intersection(L.SITE).difference(assigned)
    assigned = unary_union([assigned, net])
    AREAS.append([key, en, ar, net, grp])
residual = L.SITE.difference(assigned)
AREAS.append(["G5", "Verges, buffers, pocket gardens", "الأحزمة الخضراء والحدائق الجيبية", residual, "GRN"])
SITE_A = L.SITE.area

n_v, n_h = len(L.plots["V"]), len(L.plots["H"])
n_apt = 240
pop = n_v * 6 + n_h * 6 + 120 * 4 + 120 * 6
units = n_v + n_h + n_apt
group_area = {g: sum(r[3].area for r in AREAS if r[4] == g) for g in ("RES", "SRV", "GRN", "ROD")}
green_open = group_area["GRN"]

# ================================================================ DXF
doc = ezdxf.new("R2018", setup=True)
doc.header["$INSUNITS"] = 6
doc.header["$LUNITS"] = 2
doc.header["$LUPREC"] = 2
doc.styles.add("AR", font="arial.ttf")
msp = doc.modelspace()

LAYERS = {  # name: (aci, lineweight, linetype)
    "MP_BOUNDARY": (1, 60, "Continuous"),
    "MP_BOUNDARY_COORDS": (6, 18, "DASHED"),
    "MP_WALL": (8, 30, "DASHDOT"),
    "MP_ROAD_MAIN": (9, 35, "Continuous"),
    "MP_ROAD_LOCAL": (9, 25, "Continuous"),
    "MP_ROAD_SERVICE": (9, 30, "Continuous"),
    "MP_ROAD_PUBLIC": (8, 35, "Continuous"),
    "MP_ROAD_CL": (8, 13, "CENTER"),
    "MP_PLOT_VILLA400": (2, 25, "Continuous"),
    "MP_PLOT_HOUSE200": (30, 25, "Continuous"),
    "MP_PLOT_NUMBER": (7, 13, "Continuous"),
    "MP_TOWER": (5, 50, "Continuous"),
    "MP_TOWER_ZONE": (5, 25, "Continuous"),
    "MP_TOWER_BASEMENT": (5, 13, "DASHED"),
    "MP_SERVICE_PUBLIC": (1, 30, "Continuous"),
    "MP_SERVICE_EDU": (4, 30, "Continuous"),
    "MP_SERVICE_COMMUNITY": (6, 30, "Continuous"),
    "MP_UTILITY": (242, 30, "Continuous"),
    "MP_GREEN_PARK": (3, 25, "Continuous"),
    "MP_GREEN_BUFFER": (82, 13, "Continuous"),
    "MP_PLAY": (92, 18, "Continuous"),
    "MP_WATER": (5, 35, "Continuous"),
    "MP_TREES": (3, 13, "Continuous"),
    "MP_GATE": (1, 35, "Continuous"),
    "MP_PHASING": (211, 50, "PHANTOM"),
    "MP_DIM": (3, 13, "Continuous"),
    "MP_TEXT": (7, 18, "Continuous"),
    "MP_TABLE": (7, 18, "Continuous"),
    "MP_GRID": (8, 9, "Continuous"),
    "MP_NORTH": (7, 25, "Continuous"),
    "MP_HATCH_RES": (51, 0, "Continuous"),
    "MP_HATCH_TOWER": (151, 0, "Continuous"),
    "MP_HATCH_SERVICE": (21, 0, "Continuous"),
    "MP_HATCH_GREEN": (83, 0, "Continuous"),
    "MP_HATCH_WATER": (141, 0, "Continuous"),
    "MP_HATCH_ROAD": (252, 0, "Continuous"),
}
for name, (color, lw, lt) in LAYERS.items():
    doc.layers.add(name, color=color, lineweight=lw, linetype=lt)

ANG = math.degrees(math.atan2(L.EV[1], L.EV[0]))  # text angle along the plot axis


def upts(poly):
    return [tuple(p) for p in np.array(L.to_utm(poly).exterior.coords)[:-1]]


def outline(g, layer):
    for p in parts(g):
        msp.add_lwpolyline(upts(p), close=True, dxfattribs={"layer": layer})
        for hole in p.interiors:
            msp.add_lwpolyline([tuple(L.utm_xy(*c)) for c in list(hole.coords)[:-1]], close=True,
                               dxfattribs={"layer": layer})


def fill(g, layer, color, transparency=0.55):
    for p in parts(g):
        h = msp.add_hatch(color=color, dxfattribs={"layer": layer})
        h.paths.add_polyline_path(upts(p), is_closed=True, flags=1)
        for hole in p.interiors:
            h.paths.add_polyline_path([tuple(L.utm_xy(*c)) for c in list(hole.coords)[:-1]], is_closed=True, flags=16)
        h.transparency = transparency


def text(s, x, y, h=3.0, layer="MP_TEXT", rot=None, align=TextEntityAlignment.MIDDLE_CENTER):
    t = msp.add_text(s, height=h, rotation=ANG if rot is None else rot, dxfattribs={"layer": layer, "style": "AR"})
    t.set_placement(L.utm_xy(x, y), align=align)
    return t


def label2(en, ar, x, y, h=3.0, layer="MP_TEXT", rot=None):
    """English over Arabic, stacked across the local frame."""
    dy = h * 0.85
    text(en, x, y - dy, h, layer, rot)
    text(ar, x, y + dy, h, layer, rot)


def line(pts, layer):
    msp.add_lwpolyline([L.utm_xy(*p) for p in pts], dxfattribs={"layer": layer})


# ---- boundary
outline(L.SITE, "MP_BOUNDARY")
msp.add_lwpolyline(L.P, close=True, dxfattribs={"layer": "MP_BOUNDARY_COORDS"})
for i, q in enumerate(L.Q):
    msp.add_circle(q, 1.5, dxfattribs={"layer": "MP_BOUNDARY"})
    c = np.mean(L.Q, axis=0)
    t = np.add(q, (np.subtract(q, c) / np.linalg.norm(np.subtract(q, c))) * 12)
    msp.add_text(f"Q{i + 1}  E {q[0]:.2f}  N {q[1]:.2f}", height=3, dxfattribs={"layer": "MP_BOUNDARY", "style": "AR"}
                 ).set_placement(tuple(t), align=TextEntityAlignment.MIDDLE_CENTER)

# ---- roads
for g, lay in ((roads_main, "MP_ROAD_MAIN"), (roads_service, "MP_ROAD_SERVICE"), (roads_local, "MP_ROAD_LOCAL"),
               (roads_west, "MP_ROAD_LOCAL"), (roads_public, "MP_ROAD_PUBLIC")):
    outline(g.intersection(L.SITE), lay)
    fill(g.intersection(L.SITE), "MP_HATCH_ROAD", 252, 0.4)
by = sum(L.Y_BLVD) / 2
line([(L.GATE_X + L.RB_R, by), (L.blvd_end - 17, by)], "MP_ROAD_CL")
line([(L.GATE_X, 0), (L.GATE_X, L.RB_C[1] - L.RB_R)], "MP_ROAD_CL")
msp.add_circle(L.utm_xy(*L.RB_C), (L.RB_R + L.RB_ISLAND) / 2, dxfattribs={"layer": "MP_ROAD_CL"})
line([(sum(L.SERVICE_X) / 2, 0), (sum(L.SERVICE_X) / 2, L.ys(sum(L.SERVICE_X) / 2))], "MP_ROAD_CL")
cl = LineString([L.C0, L.C1]).intersection(L.SITE.buffer(1))
line(list(cl.coords), "MP_ROAD_CL")
for s in L.local_streets:
    b = s.bounds
    line([(b[0], (b[1] + b[3]) / 2), (b[2], (b[1] + b[3]) / 2)], "MP_ROAD_CL")
# outer roads (context, outside the plot)
for a, b_ in ((L.P[3], L.P[0]), (L.P[1], L.P[2])):
    u = np.subtract(b_, a) / np.linalg.norm(np.subtract(b_, a))
    nrm = np.array([-u[1], u[0]])
    for d in (0.0, 12.0):
        msp.add_line(tuple(np.add(a, nrm * d - u * 40)), tuple(np.add(b_, nrm * d + u * 40)),
                     dxfattribs={"layer": "MP_ROAD_PUBLIC"})

# ---- plots
for i, p in enumerate(sorted(L.plots["V"], key=lambda g: (round(g.bounds[1]), g.bounds[0]))):
    outline(p, "MP_PLOT_VILLA400")
    c = p.centroid
    text(f"V{i + 1:02d}", c.x, c.y, 2.4, "MP_PLOT_NUMBER")
for i, p in enumerate(sorted(L.plots["H"], key=lambda g: (round(g.bounds[1]), g.bounds[0]))):
    outline(p, "MP_PLOT_HOUSE200")
    c = p.centroid
    text(f"H{i + 1:02d}", c.x, c.y, 1.9, "MP_PLOT_NUMBER")
fill(plots_v, "MP_HATCH_RES", 51, 0.5)
fill(plots_h, "MP_HATCH_RES", 30, 0.5)

# ---- towers
outline(L.tower_zone, "MP_TOWER_ZONE")
fill(L.tower_zone.difference(roads_west), "MP_HATCH_TOWER", 151, 0.7)
for i, (t, pod) in enumerate(zip(L.towers, L.tower_podium)):
    outline(t, "MP_TOWER")
    outline(pod, "MP_TOWER")
    fill(t, "MP_HATCH_TOWER", 5, 0.2)
    c = t.centroid
    label2(f"TOWER {'ABC'[i]}  20 FL", f"البرج {'أبج'[i]}  20 طابق", c.x, c.y, 2.6, "MP_TOWER")
outline(L.basement, "MP_TOWER_BASEMENT")
text("BASEMENT PARKING 360 CARS - سرداب مواقف 360 سيارة", 80, 84, 2.4, "MP_TOWER_BASEMENT")
label2("TOWER PLAZA OVER BASEMENT", "بلازا الأبراج فوق السرداب", 128, 128, 3.0, "MP_TOWER_ZONE")

# ---- services
SRV_LAYER = {"POLICE": "MP_SERVICE_PUBLIC", "CIVIL DEFENCE": "MP_SERVICE_PUBLIC", "HEALTH CENTRE": "MP_SERVICE_PUBLIC",
             "GATE & ADMIN": "MP_SERVICE_PUBLIC", "KINDERGARTEN": "MP_SERVICE_EDU", "PRIMARY SCHOOL": "MP_SERVICE_EDU",
             "INTERMEDIATE SCHOOL": "MP_SERVICE_EDU", "PREPARATORY SCHOOL": "MP_SERVICE_EDU",
             "POWER STATION": "MP_UTILITY", "WATER STATION": "MP_UTILITY", "WASTE POINT": "MP_UTILITY",
             "SECONDARY SCHOOL": "MP_SERVICE_EDU"}
for k, (ar, g, _need) in L.SERVICES.items():
    lay = SRV_LAYER.get(k, "MP_SERVICE_COMMUNITY")
    outline(g, lay)
    fill(g, "MP_HATCH_SERVICE", {"MP_SERVICE_EDU": 4, "MP_UTILITY": 8, "MP_SERVICE_PUBLIC": 1}.get(lay, 6), 0.65)
    c = g.representative_point() if k in ("GATE & ADMIN", "CIVIL DEFENCE") else g.centroid
    h = 2.6 if g.area < 2600 else 3.4
    label2(k, ar, c.x, c.y - 2, h, lay)
    text(f"{g.area:,.0f} m2", c.x, c.y + h * 2.3, h * 0.75, lay)

# ---- greens, water, play
for g in (L.shallalat_garden, L.orchard, L.public_garden, L.rb_island):
    outline(g, "MP_GREEN_PARK")
fill(unary_union([L.shallalat_garden, L.orchard, L.public_garden, L.rb_island]), "MP_HATCH_GREEN", 83, 0.55)
outline(unary_union([L.gate_median, L.blvd_median, residual]), "MP_GREEN_BUFFER")
fill(unary_union([L.gate_median, L.blvd_median, residual]), "MP_HATCH_GREEN", 63, 0.75)
for g in L.playgrounds:
    outline(g, "MP_PLAY")
    c = g.centroid
    label2("PLAYGROUND", "ملعب أطفال", c.x, c.y, 1.9, "MP_PLAY")
outline(L.lake, "MP_WATER")
fill(L.lake, "MP_HATCH_WATER", 141, 0.3)
for k in range(5):  # cascades (the "Shallalat") stepping down to the lake
    y = 104 - k * 2.2
    line([(787 - 6 + k, y), (787 + 6 - k, y)], "MP_WATER")
label2("SHALLALAT GARDEN", "حديقة الشلالات", 792, 162, 3.6, "MP_GREEN_PARK")
label2("CASCADES + LAKE", "شلالات وبحيرة", 792, 138, 2.6, "MP_WATER")
label2("ORCHARD GARDEN", "حديقة البستان", 318, 255, 3.0, "MP_GREEN_PARK")
label2("PUBLIC GARDEN", "حديقة عامة", 100, 190, 3.6, "MP_GREEN_PARK")
label2("WOODED ISLAND", "الجزيرة المشجرة", L.RB_C[0], L.RB_C[1], 2.2, "MP_GREEN_PARK")
label2("GREEN BELT", "حزام أخضر", 660, 196, 2.4, "MP_GREEN_BUFFER")

# ---- trees: existing (kept) + proposed avenue, garden and orchard trees
for p in L.TREES_EXIST:
    msp.add_circle(L.utm_xy(*p), 4.5, dxfattribs={"layer": "MP_TREES"})
    msp.add_circle(L.utm_xy(*p), 0.6, dxfattribs={"layer": "MP_TREES"})
tree_pts = []
for x in np.arange(L.GATE_X + L.RB_R + 6, L.blvd_end - 20, 10):
    tree_pts += [(x, 86.0), (x, 71.0), (x, L.S0 - 1.5)]
for x in np.arange(6, 900, 9):
    tree_pts.append((x, 3.0))
for x in np.arange(150, 360, 8):
    for y in np.arange(200, 300, 8):
        tree_pts.append((x, y))
gx, gy = np.meshgrid(np.arange(738, 912, 11), np.arange(100, 200, 11))
tree_pts += list(zip(gx.ravel() + (gy.ravel() % 22) / 2, gy.ravel()))
gx, gy = np.meshgrid(np.arange(0, 220, 13), np.arange(0, 300, 13))
tree_pts += list(zip(gx.ravel(), gy.ravel()))
hold_out = unary_union([roads_main, roads_local, roads_service, roads_west, roads_public, plots_v, plots_h, L.lake.buffer(3),
                        *L.towers, *L.tower_podium, *[g for _, g, _ in L.SERVICES.values()], *L.playgrounds]).buffer(1.5)
green_ok = unary_union([L.shallalat_garden, L.orchard, L.public_garden, L.tower_zone, L.blvd_median, residual])
for p in tree_pts:
    pt = Point(p)
    if green_ok.contains(pt) and not hold_out.contains(pt):
        msp.add_circle(L.utm_xy(*p), 2.5, dxfattribs={"layer": "MP_TREES"})

# ---- gated wall, gates
wall = L.SITE.intersection(L.cross_strip(L.CROSS_W / 2 + 4, 1000)).buffer(-0.5, join_style=2)
outline(wall, "MP_WALL")
for (x, y, en, ar) in [(L.GATE_X, 8, "MAIN GATE", "البوابة الرئيسية"),
                       (sum(L.SERVICE_X) / 2, L.ys(sum(L.SERVICE_X) / 2) - 6, "SECOND GATE", "البوابة الثانية")]:
    msp.add_lwpolyline([L.utm_xy(x - 1.5, y - 2.5), L.utm_xy(x + 1.5, y - 2.5), L.utm_xy(x + 1.5, y + 2.5),
                        L.utm_xy(x - 1.5, y + 2.5)], close=True, dxfattribs={"layer": "MP_GATE"})
    label2(en, ar, x + 22, y, 2.6, "MP_GATE")
label2("TOWERS GATE", "بوابة البرجين", 120, 107, 2.2, "MP_GATE")
label2("ROUNDABOUT", "دوار", L.GATE_X - 36, 92, 2.4, "MP_ROAD_MAIN")

# ---- road names and widths
label2("BOULEVARD 24 m (THE AXIS)", "البوليفارد 24 م (المحور)", 300, by, 3.2, "MP_ROAD_MAIN")
label2("BOULEVARD 24 m", "البوليفارد 24 م", 560, by, 3.2, "MP_ROAD_MAIN")
label2("SERVICE STREET 16 m", "شارع خدمي 16 م", sum(L.SERVICE_X) / 2, 150, 2.6, "MP_ROAD_SERVICE", ANG + 90)
label2("CROSS ROAD 12 m (PUBLIC)", "الشارع العرضي 12 م (عام)", L.C0[0] + 0.28 * 180, 180, 2.6, "MP_ROAD_PUBLIC",
       math.degrees(math.atan2(*(L.EV * L.CD[1] + L.NV * L.CD[0])[::-1])) + 180)
label2("EXISTING ROAD ~12 m (OUTSIDE PLOT)", "شارع قائم ~12 م (خارج القطعة)", 450, -12, 3.0, "MP_ROAD_PUBLIC")
label2("EXISTING ROAD ~12 m (OUTSIDE PLOT)", "شارع قائم ~12 م (خارج القطعة)", 450, L.ys(450) + 12, 3.0, "MP_ROAD_PUBLIC")
label2("WEST SERVICE ROAD 12 m", "شارع الخدمات الغربي 12 م", 60, 142, 2.2, "MP_ROAD_LOCAL")
dim = doc.dimstyles.new("MP_M")
dim.dxf.dimtxt = 2.5
dim.dxf.dimasz = 1.8
dim.dxf.dimdec = 0
dim.dxf.dimexo = 0.5
dim.dxf.dimexe = 1
dim.dxf.dimgap = 0.6
dim.dxf.dimtad = 1
dim.dxf.dimtxsty = "AR"
dim.dxf.dimpost = "<> m"


def dim_y(x, y0, y1, off=0):
    msp.add_aligned_dim(p1=L.utm_xy(x, y0), p2=L.utm_xy(x, y1), distance=off, dimstyle="MP_M",
                        dxfattribs={"layer": "MP_DIM"}).render()


def dim_x(y, x0, x1, off=0):
    msp.add_aligned_dim(p1=L.utm_xy(x0, y), p2=L.utm_xy(x1, y), distance=off, dimstyle="MP_M",
                        dxfattribs={"layer": "MP_DIM"}).render()


dim_y(255, *L.Y_BLVD)
dim_y(620, *L.Y_BLVD)
dim_y(255, 31, 43)
dim_y(250, *L.V_S_STREETS[0])
dim_y(580, *L.H_S_STREETS[0])
dim_x(200, *L.SERVICE_X)
dim_x(20, L.GATE_X - 12, L.GATE_X + 12)
dim_y(240, 6, 31)
dim_y(610, L.S0, L.S0 + 20)

# ---- phasing (the axis is built from the gate eastwards)
PH = [
    ("PHASE 1", "المرحلة الأولى", L.SITE.intersection(box(-10, -10, 356, 400))),
    ("PHASE 2", "المرحلة الثانية", L.SITE.intersection(box(356, -10, 690, 400))),
    ("PHASE 3", "المرحلة الثالثة", L.SITE.intersection(box(690, -10, 1000, 400))),
]
for en, ar, g in PH:
    outline(g.buffer(-1.5, join_style=2), "MP_PHASING")
    b = g.bounds
    label2(en, ar, (b[0] + b[2]) / 2 + (40 if en == "PHASE 1" else 0), -24, 5, "MP_PHASING")

# ---- grid, north, scale
uq = np.array(L.Q)
gx0, gx1 = int(uq[:, 0].min() // 100 * 100) - 100, int(uq[:, 0].max() // 100 * 100) + 200
gy0, gy1 = int(uq[:, 1].min() // 100 * 100) - 100, int(uq[:, 1].max() // 100 * 100) + 200
for x in range(gx0, gx1 + 1, 100):
    msp.add_line((x, gy0), (x, gy1), dxfattribs={"layer": "MP_GRID"})
    msp.add_text(f"E {x}", height=4, rotation=90, dxfattribs={"layer": "MP_GRID", "style": "AR"}).set_placement(
        (x - 2, gy0 + 4), align=TextEntityAlignment.BOTTOM_LEFT)
for y in range(gy0, gy1 + 1, 100):
    msp.add_line((gx0, y), (gx1, y), dxfattribs={"layer": "MP_GRID"})
    msp.add_text(f"N {y}", height=4, dxfattribs={"layer": "MP_GRID", "style": "AR"}).set_placement(
        (gx0 + 4, y + 2), align=TextEntityAlignment.BOTTOM_LEFT)
nx, ny = gx1 - 60, gy1 - 90
msp.add_lwpolyline([(nx, ny), (nx - 10, ny - 25), (nx, ny + 30), (nx + 10, ny - 25)], close=True,
                   dxfattribs={"layer": "MP_NORTH"})
msp.add_hatch(color=7, dxfattribs={"layer": "MP_NORTH"}).paths.add_polyline_path([(nx, ny), (nx, ny + 30), (nx + 10, ny - 25)])
msp.add_text("N", height=12, dxfattribs={"layer": "MP_NORTH", "style": "AR"}).set_placement(
    (nx, ny + 42), align=TextEntityAlignment.MIDDLE_CENTER)
sx, sy = gx0 + 40, gy0 + 40
for i in range(5):
    seg = [(sx + i * 20, sy), (sx + (i + 1) * 20, sy), (sx + (i + 1) * 20, sy + 4), (sx + i * 20, sy + 4)]
    msp.add_lwpolyline(seg, close=True, dxfattribs={"layer": "MP_NORTH"})
    if i % 2 == 0:
        msp.add_hatch(color=7, dxfattribs={"layer": "MP_NORTH"}).paths.add_polyline_path(seg)
    msp.add_text(f"{i * 20}", height=4, dxfattribs={"layer": "MP_NORTH", "style": "AR"}).set_placement(
        (sx + i * 20, sy - 6), align=TextEntityAlignment.MIDDLE_CENTER)
msp.add_text("100 m", height=4, dxfattribs={"layer": "MP_NORTH", "style": "AR"}).set_placement(
    (sx + 100, sy - 6), align=TextEntityAlignment.MIDDLE_CENTER)

# ---- land-use table + data block (placed west of the grid, like the site plan)
TX, TY = gx0 - 420, gy1


def trow(cells, y, widths, h=3.6, layer="MP_TABLE"):
    x = TX
    for c, w in zip(cells, widths):
        msp.add_text(c, height=h, dxfattribs={"layer": layer, "style": "AR"}).set_placement(
            (x + 2, y - 2), align=TextEntityAlignment.TOP_LEFT)
        x += w


W = [150, 110, 60, 40]
y = TY
msp.add_text("MASTER PLAN - PROPOSAL A: THE AXIS - REV. 2", height=8, dxfattribs={"layer": "MP_TABLE", "style": "AR"}
             ).set_placement((TX, y), align=TextEntityAlignment.TOP_LEFT)
y -= 11
msp.add_text("المخطط العام - المقترح أ: المحور", height=8, dxfattribs={"layer": "MP_TABLE", "style": "AR"}
             ).set_placement((TX, y), align=TextEntityAlignment.TOP_LEFT)
y -= 12
for s in ["Shallalat residential complex - NIC opportunity 5/2026 - plot 157 / 53 Baybokht",
          "مجمع الشلالات السكني - فرصة هيئة استثمار نينوى 5/2026 - القطعة 157 م53 بايبوخت",
          f"Site area {SITE_A:,.0f} m2 (79 dunam 16 olk 75 m2) - UTM WGS84 zone 38S - units: metres"]:
    msp.add_text(s, height=3.6, dxfattribs={"layer": "MP_TABLE", "style": "AR"}).set_placement(
        (TX, y), align=TextEntityAlignment.TOP_LEFT)
    y -= 6.5
y -= 4
msp.add_text("LAND-USE TABLE - جدول استعمالات الأرض", height=5, dxfattribs={"layer": "MP_TABLE", "style": "AR"}
             ).set_placement((TX, y), align=TextEntityAlignment.TOP_LEFT)
y -= 9
ROWH = 6.5
top = y
trow(["USE", "الاستعمال", "AREA m2", "%"], y, W, 3.6)
y -= ROWH
GROUP_EN = {"RES": "RESIDENTIAL - السكن", "SRV": "SERVICES & UTILITIES - الخدمات والبنى التحتية",
            "GRN": "GREEN & OPEN SPACE - الخضراء والمفتوحة", "ROD": "ROADS - الطرق"}
for grp in ("RES", "SRV", "GRN", "ROD"):
    trow([GROUP_EN[grp], "", f"{group_area[grp]:,.0f}", f"{100 * group_area[grp] / SITE_A:.1f}"], y, W, 3.8)
    y -= ROWH
    for key, en, ar, g, gg in AREAS:
        if gg != grp:
            continue
        extra = f" ({n_v})" if key == "V" else f" ({n_h})" if key == "H" else ""
        trow(["   " + en + extra, ar, f"{g.area:,.0f}", f"{100 * g.area / SITE_A:.1f}"], y, W, 3.2)
        y -= ROWH * 0.85
total = sum(r[3].area for r in AREAS)
trow(["TOTAL - المجموع", "", f"{total:,.0f}", "100.0"], y, W, 3.8)
y -= ROWH
for yy in (top + 1, top - ROWH + 1, y + 1):
    msp.add_line((TX, yy), (TX + sum(W), yy), dxfattribs={"layer": "MP_TABLE"})
for xx in np.cumsum([0] + W):
    msp.add_line((TX + xx, top + 1), (TX + xx, y + 1), dxfattribs={"layer": "MP_TABLE"})

y -= 10
gfa_t = 3 * 990 * 20
all_plots = L.plots["V"] + L.plots["H"]
WALK = {k: max(g.distance(p.centroid) for p in all_plots) for k, (_a, g, _n) in L.SERVICES.items()}
roads_area = group_area["ROD"]
summary = [
    "PROGRAMME - البرنامج (revision 2, client's areas 21/10/2026)",
    f"Villas 400 m2 (16 x 25): {n_v}    -  فلل 400 م²: {n_v}",
    f"Houses 240 m2 (12 x 20): {n_h}    -  دور 240 م²: {n_h}",
    f"Tower apartments: {n_apt} (3 towers x 20 floors x 4; M2 2-bed + M3 3-bed, half each), basement 360 cars",
    f"TOTAL UNITS: {units}    -  مجموع الوحدات: {units}",
    f"Population (6 per house, 4 per M2, 6 per M3): ~{pop:,}",
    f"Gross density: {units / (SITE_A / 1e4):.1f} units/ha, {pop / (SITE_A / 1e4):.0f} persons/ha",
    f"Towers GFA {gfa_t:,} m2, FAR on the tower plaza {gfa_t / L.tower_zone.area:.2f}",
    f"Green + open space: {green_open:,.0f} m2 = {100 * green_open / SITE_A:.1f}% = {green_open / pop:.1f} m2/person",
    f"Roads: {roads_area:,.0f} m2 = {100 * roads_area / SITE_A:.1f}%",
    "",
    "DESIGN CONCEPT - فكرة التصميم",
    "Driver: movement efficiency and phasing (linear city / Baghdad houses).",
    "Two gates only, both on the long sides: main gate on the north road ~200 m from the west end",
    "with a roundabout at the head of the axis; second gate on the south road at the mid-axis service street.",
    "No streets on the short ends. 24 m boulevard parallel to the north edge, wooded median, blocks every ~150 m.",
    "Cross road kept public: west part = 3 towers on a plaza + health, police, civil defence, power, water, waste.",
    "Mid-axis: mall + mosque to the north, kindergarten + primary + secondary school to the south.",
    "No club (client): its land is public garden. Leftover land goes to the Shallalat garden at the east end.",
    "Phasing: 1 west part + gate + first blocks, 2 centre (schools, mall, mosque), 3 east end + Shallalat garden.",
    "",
    "KURRASA CHECKS (معايير الإسكان الحضري 2010) - farthest plot, straight line",
    f"Kindergarten {WALK['KINDERGARTEN']:.0f} m (300) / primary {WALK['PRIMARY SCHOOL']:.0f} m (500) / "
    f"secondary {WALK['SECONDARY SCHOOL']:.0f} m (800)",
    f"Mosque {WALK['MOSQUE']:.0f} m (500) / mall {WALK['MALL']:.0f} m (500) / health {WALK['HEALTH CENTRE']:.0f} m (800)",
    "Tower spacing 33.5 m and more (>= 33 m)",
    "Approximate from the scan: cross road and existing trees - confirm by survey. Watercourse ignored per client.",
]
for i, s in enumerate(summary):
    msp.add_text(s, height=4.2 if s.isupper() or i == 0 else 3.4,
                 dxfattribs={"layer": "MP_TABLE", "style": "AR"}).set_placement((TX, y - i * 6.2), align=TextEntityAlignment.TOP_LEFT)

doc.saveas(OUT_DXF)

# ================================================================ preview (local frame, north edge on top)
matplotlib.font_manager.fontManager.addfont(os.path.join(HERE, "..", "fonts", "NotoSansArabic-Regular.ttf"))
FONT = ["DejaVu Sans", "Noto Sans Arabic"]  # Latin from DejaVu, shaped Arabic from Noto


def ar(s):
    return arabic_reshaper.reshape(s)  # this matplotlib lays out RTL runs itself; get_display would reverse twice


COL = {"V": "#f3d36b", "H": "#f4a582", "T": "#bcd7ef", "SRV_PUBLIC": "#e7837a", "SRV_EDU": "#8fc5d6",
       "SRV_COMM": "#c7a0d6", "UTIL": "#b3b3b3", "GREEN": "#a9d18e", "GREEN2": "#cfe7b5", "ROAD": "#d9d9d9",
       "WATER": "#7fb8e6"}


def pfill(ax, g, fc, ec="#555", lw=0.25, z=1, alpha=1.0):
    for p in parts(g):
        x, y = p.exterior.xy
        ax.fill(x, y, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha)


def ptxt(ax, s_en, s_ar, x, y, size=5, rot=0, z=9, color="#222"):
    ax.text(x, y, ar(s_ar) + "\n" + s_en, fontsize=size, ha="center", va="center", rotation=rot, zorder=z,
            color=color, family=FONT, linespacing=1.1)


fig = plt.figure(figsize=(33.1, 23.4))  # A1
ax = fig.add_axes([0.02, 0.30, 0.96, 0.62])
pfill(ax, L.SITE, "#f6f3ea", "none")
pfill(ax, residual, COL["GREEN2"], "none")
pfill(ax, unary_union([L.shallalat_garden, L.orchard, L.public_garden]), COL["GREEN"], "#6d9a52", 0.3)
pfill(ax, L.tower_zone.difference(roads_west), COL["T"], "#4a7fb0", 0.4)
pfill(ax, unary_union([roads_main, roads_service, roads_local, roads_west]), COL["ROAD"], "#9a9a9a", 0.3, 2)
pfill(ax, roads_public, "#c4c4c4", "#888", 0.4, 2)
pfill(ax, unary_union([L.rb_island, L.gate_median, L.blvd_median]), "#7fb069", "#557a45", 0.3, 3)
pfill(ax, L.lake, COL["WATER"], "#3d7fb8", 0.4, 3)
for p in L.plots["V"]:
    pfill(ax, p, COL["V"], "#8a6d12", 0.35, 4)
for p in L.plots["H"]:
    pfill(ax, p, COL["H"], "#9a4a2a", 0.35, 4)
for t, pod in zip(L.towers, L.tower_podium):
    pfill(ax, pod, "#dbe9f6", "#4a7fb0", 0.4, 4)
    pfill(ax, t, "#3f6e9a", "#1f3f60", 0.6, 5)
for k, (a_, g, _n) in L.SERVICES.items():
    lay = SRV_LAYER.get(k, "MP_SERVICE_COMMUNITY")
    fc = {"MP_SERVICE_PUBLIC": COL["SRV_PUBLIC"], "MP_SERVICE_EDU": COL["SRV_EDU"], "MP_UTILITY": COL["UTIL"]}.get(lay, COL["SRV_COMM"])
    pfill(ax, g, fc, "#555", 0.4, 4)
    c = g.representative_point() if k in ("GATE & ADMIN", "CIVIL DEFENCE") else g.centroid
    ptxt(ax, f"{k}\n{g.area:,.0f} m²", a_, c.x, c.y, 4.6 if g.area < 2600 else 5.6, 0)
for g in L.playgrounds:
    pfill(ax, g, "#ffe08a", "#b08a00", 0.4, 5)
ex = np.array(L.TREES_EXIST)
ax.scatter(ex[:, 0], ex[:, 1], s=90, facecolors="none", edgecolors="#2f6b2f", lw=0.8, zorder=6)
tp = [p for p in tree_pts if green_ok.contains(Point(p)) and not hold_out.contains(Point(p))]
tp = np.array(tp)
ax.scatter(tp[:, 0], tp[:, 1], s=9, c="#4f8f3a", alpha=0.75, lw=0, zorder=5)
x, y = L.SITE.exterior.xy
ax.plot(x, y, color="#c0392b", lw=2.0, zorder=7)
x, y = wall.exterior.xy
ax.plot(x, y, color="#555", lw=0.7, ls="-.", zorder=7)
for en, ar_, g in PH:
    x, y = g.buffer(-1.5, join_style=2).exterior.xy
    ax.plot(x, y, color="#8e44ad", lw=1.0, ls=(0, (8, 4)), zorder=8)
    b = g.bounds
    ptxt(ax, en, ar_, (b[0] + b[2]) / 2 + (40 if en == "PHASE 1" else 0), -26, 9, 0, color="#8e44ad")
# labels
ptxt(ax, "BOULEVARD 24 m - THE AXIS", "البوليفارد 24 م - المحور", 300, by, 6.5)
ptxt(ax, "BOULEVARD 24 m", "البوليفارد 24 م", 600, by, 6.5)
ptxt(ax, "SERVICE ST. 16 m", "شارع خدمي 16 م", sum(L.SERVICE_X) / 2, 150, 4.5, 90)
ptxt(ax, "CROSS ROAD 12 m (PUBLIC)", "الشارع العرضي 12 م (عام)", L.C0[0] + 0.2806 * 200, 200, 5, -74.3)
ptxt(ax, "MAIN GATE", "البوابة الرئيسية", L.GATE_X, -8, 6, color="#c0392b")
ptxt(ax, "SECOND GATE", "البوابة الثانية", sum(L.SERVICE_X) / 2, L.ys(sum(L.SERVICE_X) / 2) + 9, 6, color="#c0392b")
ptxt(ax, "TOWERS GATE", "بوابة البرجين", 128, 106, 4.5, color="#c0392b")
ptxt(ax, "WOODED ISLAND", "الجزيرة المشجرة", L.RB_C[0], L.RB_C[1], 4.2)
ptxt(ax, "SHALLALAT GARDEN", "حديقة الشلالات", 792, 162, 7)
ptxt(ax, "CASCADES + LAKE", "شلالات وبحيرة", 792, 138, 5)
ptxt(ax, "ORCHARD GARDEN", "حديقة البستان", 255, 268, 6, -10)
ptxt(ax, "PUBLIC GARDEN", "حديقة عامة", 100, 190, 7)
ptxt(ax, "GREEN BELT", "حزام أخضر", 670, 195, 4.5, -10)
for i, t in enumerate(L.towers):
    c = t.centroid
    ax.text(c.x, c.y, f"{'ABC'[i]}\n20 FL", color="white", fontsize=7, ha="center", va="center", zorder=9, weight="bold")
ptxt(ax, "TOWER PLAZA", "بلازا الأبراج", 128, 128, 5.5)
ptxt(ax, "EXISTING ROAD ~12 m", "شارع قائم ~12 م", 450, -16, 5.5, 0, color="#666")
ptxt(ax, "EXISTING ROAD ~12 m", "شارع قائم ~12 م", 450, L.ys(450) + 10, 5.5, -10, color="#666")
for g in L.playgrounds:
    c = g.centroid
    ax.text(c.x, c.y, ar("ملعب"), fontsize=4, ha="center", va="center", zorder=9, family=FONT)
# north arrow (grid north in the local frame)
nloc = np.array([L.EV[1], L.NV[1]])
ang = math.degrees(math.atan2(-nloc[1], nloc[0]))
ax.annotate("", xy=(925 + 22 * nloc[0], 250 + 22 * nloc[1]), xytext=(925, 250),
            arrowprops=dict(arrowstyle="-|>", lw=2, color="k"))
ax.text(925 + 30 * nloc[0], 250 + 30 * nloc[1], "N", fontsize=14, ha="center", va="center", weight="bold")
for i in range(5):
    ax.fill([820 + i * 20, 840 + i * 20, 840 + i * 20, 820 + i * 20], [300, 300, 304, 304],
            fc="k" if i % 2 == 0 else "white", ec="k", lw=0.6)
    ax.text(820 + i * 20, 309, str(i * 20), fontsize=7, ha="center")
ax.text(920, 309, "100 m", fontsize=7, ha="center")
ax.set_aspect("equal")
ax.set_xlim(-20, 950)
ax.set_ylim(318, -40)
ax.axis("off")

fig.text(0.98, 0.965, ar("المخطط العام - المقترح أ: المحور (تعديل 2)") + "    MASTER PLAN - PROPOSAL A: THE AXIS - REV. 2",
         fontsize=26, ha="right", va="center", family=FONT, weight="bold")
fig.text(0.98, 0.94, ar("مجمع الشلالات السكني · فرصة هيئة استثمار نينوى 5/2026 · القطعة 157 م53 بايبوخت · 199,175 م²"),
         fontsize=15, ha="right", va="center", family=FONT, color="#444")

# table in the preview
tax = fig.add_axes([0.52, 0.02, 0.46, 0.27])
tax.axis("off")
rows = [["%", ar("المساحة م²"), ar("الاستعمال"), "USE"]]
for grp in ("RES", "SRV", "GRN", "ROD"):
    gen = GROUP_EN[grp].split(" - ")
    rows.append([f"{100 * group_area[grp] / SITE_A:.1f}", f"{group_area[grp]:,.0f}", ar(gen[1]), gen[0]])
    for key, en, ar_, g, gg in AREAS:
        if gg == grp:
            extra = f" ({n_v})" if key == "V" else f" ({n_h})" if key == "H" else ""
            rows.append([f"{100 * g.area / SITE_A:.1f}", f"{g.area:,.0f}", ar(ar_) + extra, en + extra])
rows.append(["100", f"{total:,.0f}", ar("المجموع"), "TOTAL"])
half = (len(rows) + 1) // 2
for j, chunk in enumerate((rows[:half], [rows[0]] + rows[half:])):
    tb = tax.table(cellText=chunk, loc="upper left", colWidths=[0.04, 0.07, 0.19, 0.19],
                   bbox=[0.5 * (1 - j), 1 - 0.054 * len(chunk), 0.495, 0.054 * len(chunk)])
    tb.auto_set_font_size(False)
    tb.set_fontsize(7.2)
    for (r, c), cell in tb.get_celld().items():
        cell.set_linewidth(0.3)
        cell.get_text().set_family(FONT)
        txt = chunk[r][3] if r < len(chunk) else ""
        if r == 0 or txt.isupper():
            cell.set_facecolor("#e8efe1")
            cell.get_text().set_weight("bold")
        cell.get_text().set_ha("right" if c == 2 else "left" if c == 3 else "center")

# programme + legend
sax = fig.add_axes([0.02, 0.02, 0.48, 0.27])
sax.axis("off")
def ok(k, lim):
    return f"{WALK[k]:.0f} " + ar("م") + (" ✓" if WALK[k] <= lim else " ✗")


lines = [
    (ar("البرنامج (التعديل الثاني على مساحات 21/10)") + " - PROGRAMME", 11, "bold"),
    (f"{n_v} " + ar("فيلا 400 م² (16×25)") + f"   ·   {n_h} " + ar("داراً 240 م² (12×20)") + f"   ·   {n_apt} " + ar("شقة في 3 أبراج"), 9.5, None),
    (ar("الشقق: 3 أبراج × 20 طابقاً × 4 شقق، نصفها M2 بغرفتين ونصفها M3 بثلاث غرف، وسرداب مواقف 360 سيارة تحت البلازا"), 9.5, None),
    (ar("مجموع الوحدات") + f" {units}   ·   " + ar("السكان") + f" ~{pop:,}   ·   " + f"{units / (SITE_A / 1e4):.1f} " + ar("وحدة/هكتار") + f"   ·   {pop / (SITE_A / 1e4):.0f} " + ar("شخص/هكتار"), 9.5, None),
    (ar("الخضراء والمفتوحة") + f" {100 * green_open / SITE_A:.1f}% ({green_open / pop:.1f} " + ar("م² للفرد") + ")   ·   " + ar("الطرق") + f" {100 * roads_area / SITE_A:.1f}%", 9.5, None),
    ("", 6, None),
    (ar("فكرة التصميم") + " - CONCEPT", 11, "bold"),
    (ar("بوابتان فقط على الضلعين الطويلين: الرئيسية على الشارع الشمالي ودوار عند رأس المحور، والثانية على الشارع الجنوبي عند الشارع الخدمي."), 9, None),
    (ar("لا شوارع على الطرفين القصيرين. بوليفارد 24 م موازٍ للحافة الشمالية بجزرة وسطية مشجرة، وأضلاع كل ~150 م."), 9, None),
    (ar("الجزء الغربي (الشارع العرضي يبقى عاماً): 3 أبراج على بلازا + المركز الصحي والشرطة والدفاع المدني ومحطتا الماء والكهرباء والنفايات."), 9, None),
    (ar("منتصف المحور: المول والجامع شمالاً، والروضة والابتدائية والثانوية جنوباً. ألغي النادي وصارت أرضه حديقة عامة."), 9, None),
    (ar("المراحل: 1 الجزء الغربي والبوابة والبلوكات الأولى، 2 الوسط، 3 الطرف الشرقي وحديقة الشلالات."), 9, None),
    ("", 6, None),
    (ar("أبعد قطعة عن الخدمة (خط مستقيم) مقابل حد الكراس: الروضة ") + ok("KINDERGARTEN", 300) + ar(" (300)، الابتدائية ") + ok("PRIMARY SCHOOL", 500) + ar(" (500)، الثانوية ") + ok("SECONDARY SCHOOL", 800) + ar(" (800)"), 9, None),
    (ar("الجامع ") + ok("MOSQUE", 500) + ar(" (500)، المول ") + ok("MALL", 500) + ar(" (500)، المركز الصحي ") + ok("HEALTH CENTRE", 800) + ar(" (800). المسافة بين الأبراج 33.5 م فأكثر."), 9, None),
    (ar("الشارع العرضي والأشجار القائمة منقولة من الخارطة الممسوحة وتحتاج تأكيداً بالمسح الموقعي."), 9, "italic"),
]
yy = 0.98
for s, fs, wt in lines:
    sax.text(0.99, yy, s, fontsize=fs, ha="right", va="top", family=FONT, weight="bold" if wt == "bold" else "normal",
             style="italic" if wt == "italic" else "normal")
    yy -= 0.062 if fs > 7 else 0.03

fig.savefig(OUT_PDF)
fig.savefig(OUT_PNG, dpi=110)
print(OUT_DXF)
print(f"villas {n_v}  houses {n_h}  apartments {n_apt}  units {units}  population {pop}")
for key, en, ar_, g, grp in AREAS:
    print(f"{grp} {en:42s} {g.area:9,.0f}  {100 * g.area / SITE_A:5.1f}%")
print(f"total {total:,.1f}  site {SITE_A:,.1f}")
for g in group_area:
    print(g, f"{group_area[g]:,.0f}", f"{100 * group_area[g] / SITE_A:.1f}%")
