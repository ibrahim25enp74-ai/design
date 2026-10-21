"""Writes variant 1 of Ibrahim's proposal - the green ring: DXF on the site coordinates + A1 preview.

Same layers, colours, landscape and table as make_masterplan_user.py (Ibrahim's developed proposal).
Usage: python make_masterplan_v1.py [out_dir]
"""
import math
import os
import sys

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import Polygon

from layout_v1 import *  # noqa: F401,F403  (geometry of the layout)
from landscape_v1 import LANDSCAPE, PLAZA_LS

HERE = os.path.dirname(os.path.abspath(__file__))
ROT = math.degrees(math.atan2(U[1], U[0]))
SITE_RAW = Polygon([loc(p) for p in P])

NAMES = {
    "MALL": ("MALL", "المول"), "MOSQUE": ("MOSQUE", "الجامع"),
    "POLICE": ("POLICE", "الشرطة"), "CIVIL_DEF": ("CIVIL DEFENCE", "الدفاع المدني"), "HEALTH": ("HEALTH CENTRE", "المركز الصحي"),
    "SECONDARY": ("SECONDARY SCHOOL", "الثانوية (متوسطة + إعدادية)"), "PRIMARY": ("PRIMARY SCHOOL", "المدرسة الابتدائية"),
    "KG_W": ("KINDERGARTEN (W)", "الروضة الغربية"), "KG_E": ("KINDERGARTEN (E)", "الروضة الشرقية"), "WATER": ("WATER STATION", "محطة الماء"), "POWER": ("POWER STATION", "محطة الكهرباء"),
    "WASTE": ("WASTE", "النفايات"),
    "PARK_MALL": ("PARKING", "موقف السيارات"), "G_MOSQUE": ("GARDEN", "حديقة"), "G_MALL": ("GARDEN", "حديقة"),
    "G_HEALTH": ("GARDEN", "حديقة"), "G_PRIM": ("GARDEN", "حديقة"),
}
UTIL_KEYS = UTILITIES


def table_rows():
    units = len(VILLAS) + len(HOUSES) + N_APTS
    rows = [
        "VARIANT 1 - THE GREEN RING, REV 1 - البديل 1: الحلقة الخضراء، تعديل 1",
        "Plot 157 / District 53 Baybokht - NIC 5/2026 - UTM 38S",
        "",
        f"UNITS: {len(VILLAS)} villas 400 m2 + {len(HOUSES)} houses 240 m2 + {N_APTS} flats = {units}",
        f"Towers: {len(TOWERS)} x {FLOORS} floors x {FLATS_PER_FLOOR} flats; parking {PARK_NEED} cars in a basement under the plaza",
        "Entrances: 1 main gate (north road) + 1 service / emergency gate (south road)",
        "",
        "LAND USE - استعمالات الأرض              m2        %",
    ]
    for n, a in LANDUSE:
        rows.append(f"{n:<56s}{a:>9,.0f}  {a / SITE.area * 100:5.1f}")
    rows.append(f"{'TOTAL':<56s}{SITE.area:>9,.0f}  100.0")
    return rows


LAYERS = {
    "MP_BOUNDARY": (1, 50), "MP_BOUNDARY_COORDS": (6, 18), "MP_GATES": (1, 50), "MP_ROADS": (8, 25),
    "MP_PLOT_VILLA": (30, 18), "MP_PLOT_HOUSE": (40, 18), "MP_TOWERS": (5, 50), "MP_PLAZA": (4, 18),
    "MP_SERVICES": (1, 25), "MP_UTILITIES": (6, 25), "MP_PARKING": (9, 13), "MP_GREEN": (3, 13), "MP_WATER": (4, 13),
    "MP_TEXT": (7, 18), "MP_CROSSINGS": (7, 13), "MP_RAMPS": (8, 25),
    "MP_CIRC_VEHICLE": (250, 50), "MP_CIRC_LOCAL": (8, 25), "MP_CIRC_PED": (3, 35), "MP_CIRC_SERVICE": (1, 35),
    "MP_CIRC_TOWER": (5, 35), "MP_CIRC_EMERGENCY": (30, 35), "MP_TEXT_PLOTNO": (8, 9), "MP_TABLE": (7, 18), "MP_NORTH": (7, 25),
    "MP_HATCH_RES": (31, 0), "MP_HATCH_SERV": (1, 0), "MP_HATCH_GREEN": (3, 0), "MP_HATCH_ROAD": (252, 0),
    "MP_HATCH_TOWER": (5, 0), "MP_LANDSCAPE": (94, 13), "MP_GARDEN_PATH": (41, 13), "MP_GARDEN_BEDS": (84, 13), "MP_TREES": (3, 13), "MP_HATCH_LANDSCAPE": (94, 0),
}
# the architect's own colours
FILL = {
    "villa": (254, 204, 102), "house": (242, 103, 34), "serv": (237, 31, 36), "util": (209, 156, 199),
    "green": (19, 103, 52), "park": (120, 186, 110), "plaza": (173, 221, 247), "tower": (39, 118, 187),
    "road": (225, 225, 225), "parking": (190, 190, 190),
    "paving": (236, 226, 204), "lawn": (150, 205, 120), "water": (110, 180, 235), "play": (240, 214, 150),
    "shrub": (78, 120, 52), "flower": (232, 150, 180), "tree": (46, 120, 50),
    "ls_lawn": (150, 196, 74), "ls_pave": (214, 214, 210), "ls_track": (226, 150, 132), "ls_gravel": (196, 194, 186),
    "ls_deck": (204, 146, 100), "ls_pit": (110, 160, 70), "ramp": (120, 120, 120),
}
PARK_LABELS = [(CENTRAL_PARK, "CENTRAL PARK + LAKE", "الحديقة المركزية والبحيرة"),
               (WEST_PARK, "WEST PARK", "الحديقة الغربية"),
               (EAST_GARDEN, "SHALLALAT GARDEN - CASCADES", "حديقة الشلالات")]


def write_dxf(path):
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 6
    doc.styles.add("AR", font="arial.ttf")
    for n, (c, lw) in LAYERS.items():
        doc.layers.add(n, color=c, lineweight=lw if lw else -3)
    msp = doc.modelspace()

    def outline(g, layer):
        for p in polys(g):
            msp.add_lwpolyline([utm(q) for q in p.exterior.coords[:-1]], close=True, dxfattribs={"layer": layer})
            for h in p.interiors:
                msp.add_lwpolyline([utm(q) for q in h.coords[:-1]], close=True, dxfattribs={"layer": layer})

    def hatch(g, layer, rgb):
        for p in polys(g):
            h = msp.add_hatch(dxfattribs={"layer": layer})
            h.rgb = rgb
            h.paths.add_polyline_path([utm(q) for q in p.exterior.coords[:-1]], is_closed=True)
            for hole in p.interiors:
                h.paths.add_polyline_path([utm(q) for q in hole.coords[:-1]], is_closed=True)

    def text(s, at, h=3.0, rot=0.0, layer="MP_TEXT"):
        t = msp.add_text(s, height=h, rotation=rot + ROT, dxfattribs={"layer": layer, "style": "AR"})
        t.set_placement(utm(at), align=TextEntityAlignment.MIDDLE_CENTER)

    hatch(ROADS, "MP_HATCH_ROAD", FILL["road"])
    for p in VILLAS:
        hatch(p, "MP_HATCH_RES", FILL["villa"])
    for p in HOUSES:
        hatch(p, "MP_HATCH_RES", FILL["house"])
    for g in FINGERS + POCKETS + [UT_GREEN, MEDIAN]:
        hatch(g, "MP_HATCH_GREEN", FILL["lawn"])
    hatch(RB_ISLAND, "MP_HATCH_GREEN", FILL["green"])
    for g in PARKS:
        hatch(g, "MP_HATCH_GREEN", FILL["park"])
    hatch(OPEN["PARK_MALL"], "MP_HATCH_ROAD", FILL["parking"])
    hatch(PLAZA, "MP_HATCH_TOWER", FILL["plaza"])
    for t in TOWERS:
        hatch(t, "MP_HATCH_TOWER", FILL["tower"])
    for k, g in SERV.items():
        hatch(g, "MP_HATCH_SERV", FILL["util" if k in UTIL_KEYS else "serv"])

    outline(SITE, "MP_BOUNDARY")
    outline(SITE_RAW, "MP_BOUNDARY_COORDS")
    outline(ROADS, "MP_ROADS")
    for p in VILLAS:
        outline(p, "MP_PLOT_VILLA")
    for p in HOUSES:
        outline(p, "MP_PLOT_HOUSE")
    for t in TOWERS:
        outline(t, "MP_TOWERS")
    outline(PLAZA, "MP_PLAZA")
    for g in [LAWN, PAVING] + FOUNTAINS:
        outline(g, "MP_LANDSCAPE")
    for q in PALMS:
        msp.add_circle(utm(q), 1.4, dxfattribs={"layer": "MP_TREES"})
    for d in LANDSCAPE + [PLAZA_LS]:
        for key, fill, lay in (("paving", "ls_pave", "MP_LANDSCAPE"), ("gravel", "ls_gravel", "MP_LANDSCAPE"),
                               ("lawn", "ls_lawn", "MP_GARDEN_BEDS"), ("shrub", "shrub", "MP_GARDEN_BEDS"),
                               ("deck", "ls_deck", "MP_LANDSCAPE"), ("track", "ls_track", "MP_GARDEN_PATH"),
                               ("pits", "ls_pit", "MP_LANDSCAPE"), ("bench", "paving", "MP_LANDSCAPE")):
            for g in d[key]:
                hatch(g, "MP_HATCH_LANDSCAPE", FILL[fill])
                outline(g, lay)
        for ln in d["contour"] + d["stripes"]:
            msp.add_lwpolyline([utm(q) for q in ln.coords], dxfattribs={"layer": "MP_LANDSCAPE"})
        for x, y, r in d["trees"] + d["palms"]:
            msp.add_circle(utm((x, y)), r, dxfattribs={"layer": "MP_TREES"})
    for g in WATER + FOUNTAINS:
        hatch(g, "MP_HATCH_LANDSCAPE", FILL["water"])
        outline(g, "MP_WATER")
    for g in PARKS + FINGERS + POCKETS + [UT_GREEN, RB_ISLAND, MEDIAN]:
        outline(g, "MP_GREEN")
    outline(OPEN["PARK_MALL"], "MP_PARKING")
    for k, g in SERV.items():
        outline(g, "MP_UTILITIES" if k in UTIL_KEYS else "MP_SERVICES")
    msp.add_lwpolyline([utm(q) for q in GATE.coords], dxfattribs={"layer": "MP_GATES"})
    msp.add_lwpolyline([utm(q) for q in SGATE.coords], dxfattribs={"layer": "MP_GATES"})
    for g in LAYBYS:
        hatch(g, "MP_HATCH_ROAD", FILL["parking"])
        outline(g, "MP_PARKING")
    hatch(SPINE_PATH, "MP_HATCH_LANDSCAPE", FILL["paving"])
    outline(SPINE_PATH, "MP_GARDEN_PATH")
    for g in CROSSINGS:
        outline(g, "MP_CROSSINGS")
    for g in RAMPS:
        hatch(g, "MP_HATCH_ROAD", FILL["ramp"])
        outline(g, "MP_RAMPS")
    outline(GATEHOUSE, "MP_GATES")
    for q in RING_TREES:
        msp.add_circle(utm(q), 2.2, dxfattribs={"layer": "MP_TREES"})

    def line(ln, layer):
        msp.add_lwpolyline([utm(q) for q in ln.coords], dxfattribs={"layer": layer})

    line(RING_CL, "MP_CIRC_VEHICLE")
    line(AXIS_CL, "MP_CIRC_VEHICLE")
    for ln in LANE_CL:
        line(ln, "MP_CIRC_LOCAL")
    for ln in [SPINE] + FINGER_WALKS:
        line(ln, "MP_CIRC_PED")
    for ln in (SERVICE_ROUTE, MALL_ROUTE):
        line(ln, "MP_CIRC_SERVICE")
    line(TOWER_ROUTE, "MP_CIRC_TOWER")
    line(RING_CL, "MP_CIRC_EMERGENCY")

    for i, p in enumerate(VILLAS):
        text(f"V{i + 1:02d}", tuple(p.centroid.coords[0]), 1.6, layer="MP_TEXT_PLOTNO")
    for i, p in enumerate(HOUSES):
        text(f"H{i + 1:02d}", tuple(p.centroid.coords[0]), 1.4, layer="MP_TEXT_PLOTNO")
    for k, g in {**SERV, **OPEN}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        text(n1, (q.x, q.y + 2.5), 3 if g.area > 900 else 1.8)
        text(f"{n2}  {g.area:,.0f} m2", (q.x, q.y - 2.5), 2.2 if g.area > 900 else 1.4)
    for g, en, ar in PARK_LABELS:
        q = g.representative_point()
        text(en, (q.x, q.y + 4), 4)
        text(f"{ar}  {g.area:,.0f} m2", (q.x, q.y - 3), 3)
    for i, t in enumerate(TOWERS):
        text(f"TOWER {'ABC'[i]}", (t.centroid.x, t.centroid.y + 3), 3.5)
        text(f"G+{FLOORS - 1}, {FLOORS * FLATS_PER_FLOOR} flats", (t.centroid.x, t.centroid.y - 3), 2.2)
    text("MAIN GATE - البوابة الرئيسية", (GATE_U, north_v(GATE_U) + 8), 3.5)
    text("SERVICE GATE - بوابة الخدمة", (SGATE_U, -8), 3.5)

    tx, ty = 338560.0, 4035840.0
    for i, row in enumerate(table_rows()):
        msp.add_text(row, height=5 if i == 0 else 3.6, dxfattribs={"layer": "MP_TABLE", "style": "AR"}).set_placement(
            (tx, ty - i * 6.5), align=TextEntityAlignment.TOP_LEFT)
    doc.saveas(path)


def write_preview(png, pdf):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import Polygon as MPoly

    fdir = os.path.join(HERE, "..", "fonts")
    for f in font_manager.findSystemFonts(fdir):
        font_manager.fontManager.addfont(f)
    plt.rcParams["font.family"] = ["DejaVu Sans", "Noto Sans Arabic"]

    fig = plt.figure(figsize=(33.1, 23.4))  # A1
    ax = fig.add_axes([0.02, 0.30, 0.96, 0.64])
    rgb = {k: tuple(c / 255 for c in v) for k, v in FILL.items()}

    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    def f(g, key, ec="#555", lw=0.3, z=1):
        for p in polys(g):
            verts, codes = [], []
            for ring in [p.exterior] + list(p.interiors):
                c = list(ring.coords)
                verts += c
                codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), fc=rgb[key] if key else "none", ec=ec, lw=lw, zorder=z))

    def t(s, at, size=6, ar_s=None, w="normal", color="#111", z=10, rot=0):
        ax.text(at[0], at[1], s if ar_s is None else f"{ar_s}\n{s}", fontsize=size, ha="center", va="center",
                fontweight=w, color=color, zorder=z, linespacing=1.1, rotation=rot,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75) if ar_s else None)

    f(ROADS, "road", ec="#888", lw=0.4)
    for p in VILLAS:
        f(p, "villa", ec="#8a6a40", lw=0.3)
    for p in HOUSES:
        f(p, "house", ec="#7a3a10", lw=0.3)
    for g in PARKS + FINGERS + POCKETS + [UT_GREEN]:
        f(g, "ls_gravel", ec="#777", lw=0.4)
    f(RB_ISLAND, "green", ec="none")
    f(MEDIAN, "shrub", ec="none")
    f(OPEN["PARK_MALL"], "parking", ec="#555", lw=0.4)
    f(PLAZA, "plaza", ec="#468", lw=0.5)

    def zebra(g):
        """White bars across a crossing."""
        c = list(g.exterior.coords)
        a, b, d = np.array(c[0]), np.array(c[1]), np.array(c[3])
        for k in np.arange(0.08, 0.95, 0.16):
            p0, p1 = a + (d - a) * k, b + (d - a) * k
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color="white", lw=2.2, zorder=3.5, solid_capstyle="butt")

    def palm(x, y, r, z=5):
        ax.add_patch(plt.Circle((x, y), r * 0.35, fc="#7a9a3a", ec="none", zorder=z))
        for a_ in np.linspace(0, 2 * np.pi, 9, endpoint=False):
            ax.plot([x, x + r * np.cos(a_)], [y, y + r * np.sin(a_)], color="#4f7a22", lw=0.9, zorder=z,
                    solid_capstyle="round")

    for d in LANDSCAPE + [PLAZA_LS]:
        for g in d["gravel"]:
            f(g, "ls_gravel", ec="#999", lw=0.2, z=2)
        for g in d["paving"]:
            f(g, "ls_pave", ec="#9a9a96", lw=0.25, z=2)
        for ln in d["stripes"]:
            ax.plot(*ln.xy, color="#c4c4bf", lw=0.25, zorder=2.1)
        for g in d["lawn"]:
            f(g, "ls_lawn", ec="#5d7f2a", lw=0.45, z=2.2)
        for ln in d["contour"]:
            ax.plot(*ln.xy, color="#7aa040", lw=0.3, zorder=2.3)
        for g in d["shrub"]:
            f(g, "shrub", ec="#3f6328", lw=0.25, z=2.4)
        for g in d["deck"]:
            f(g, "ls_deck", ec="#8a5a30", lw=0.4, z=2.2)
        for g in d["bench"]:
            f(g, "paving", ec="#555", lw=0.4, z=2.5)
        for g in d["track"]:
            f(g, "ls_track", ec="#b07060", lw=0.3, z=2.6)
        for g in d["pits"]:
            f(g, "ls_pit", ec="#4a6a2a", lw=0.2, z=2.7)
        for x, y, r in d["trees"]:
            ax.add_patch(plt.Circle((x, y), r, fc="#4f8f3a", ec="#2c5a20", lw=0.35, alpha=0.85, zorder=4))
        for x, y, r in d["palms"]:
            palm(x, y, r)
    for g in WATER:
        f(g, "water", ec="#357", lw=0.5, z=3)
    for g in FOUNTAINS:
        f(g.buffer(1.4), "ls_pave", ec="#999", lw=0.3, z=3)
        f(g, "water", ec="#357", lw=0.4, z=3.1)
    for x, y in PALMS:
        palm(x, y, 2.2)
    f(SPINE_PATH, "paving", ec="#a08a60", lw=0.35, z=4.5)
    for g in LAYBYS:
        f(g, "parking", ec="#555", lw=0.3, z=2)
    for g in CROSSINGS:
        f(g, None, ec="none", z=2)
        zebra(g)
    for g in RAMPS:
        f(g, "ramp", ec="#333", lw=0.4, z=3.6)
    f(GATEHOUSE, "serv", ec="#333", lw=0.4, z=3)
    for x, y in RING_TREES:
        ax.add_patch(plt.Circle((x, y), 2.0, fc="#4f8f3a", ec="#2c5a20", lw=0.3, alpha=0.9, zorder=4))
    for tw in TOWERS:
        f(tw, "tower", ec="#123", lw=0.8, z=3)
    for k, g in SERV.items():
        f(g, "util" if k in UTIL_KEYS else "serv", ec="#333", lw=0.6, z=2)
    f(SITE, None, ec="#c00", lw=1.6, z=6)
    for g in (GATE, SGATE):
        ax.plot(*g.xy, color="#d00", lw=5, zorder=7, solid_capstyle="butt")

    for k, g in {**SERV, **OPEN}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        t(f"{n1}\n{g.area:,.0f} m²", (q.x, q.y), 7 if g.area > 900 else 5.5, ar_s=n2)
    for g, en, ar in PARK_LABELS:
        q = g.representative_point()
        t(f"{en}\n{g.area:,.0f} m²", (q.x, q.y + (9 if g is CENTRAL_PARK else 0)), 8, ar_s=ar, w="bold")
    for i, tw in enumerate(TOWERS):
        t(f"{'ABC'[i]}\nG+{FLOORS - 1}", tw.centroid.coords[0], 7, color="white", w="bold", z=11)
    t("PLAZA - BASEMENT PARKING", (PLAZA.centroid.x + 30, PLAZA.bounds[1] + 12), 5, ar_s="بلازا الأبراج - سرداب")
    for g in RAMPS:
        t("RAMP", g.centroid.coords[0], 3.5, color="white", w="bold", z=11)
    t("GREEN SPINE 6 m", (300, 106), 5, ar_s="الممشى الأخضر")
    t("RING ROAD 14 m", (300, IN0 - 7), 6, ar_s="الطريق الحلقي")
    t("MAIN GATE", (GATE_U, north_v(GATE_U) + 10), 9, ar_s="البوابة الرئيسية", w="bold", color="#b00")
    t("SERVICE / EMERGENCY GATE", (SGATE_U, -10), 8, ar_s="بوابة الخدمة والطوارئ", w="bold", color="#b00")
    t(f"{len(VILLAS)} VILLAS 400 m² ON THE OUTER RING", (250, north_v(250) + 9), 9, ar_s="فلل 400 متر على الحلقة الخارجية", w="bold")
    t(f"{len(HOUSES)} HOUSES 240 m² IN 11 CLUSTERS", (300, -12), 9, ar_s="دور 240 متر في 11 عنقود", w="bold")

    na = np.array([-60.0, 250.0])
    gn = np.array([U[1], V[1]])
    side_v = np.array([-gn[1], gn[0]])
    ax.add_patch(MPoly([tuple(na - gn * 12 + side_v * 9), tuple(na + gn * 30), tuple(na - gn * 12 - side_v * 9)], closed=True, fc="k", zorder=12))
    t("N", tuple(na + gn * 44), 14, w="bold")
    for i in range(5):
        ax.add_patch(plt.Rectangle((680 + i * 20, 300), 20, 4, fc="k" if i % 2 == 0 else "w", ec="k", lw=0.6))
        t(f"{i * 20}", (680 + i * 20, 296), 7)
    t("100 m", (780, 296), 7)
    ax.set_xlim(-80, 900)
    ax.set_ylim(-25, 330)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.5, 0.965, "المخطط العام - البديل 1: الحلقة الخضراء (تعديل 1)   |   MASTER PLAN - VARIANT 1: THE GREEN RING - REV 1",
             ha="center", fontsize=26, fontweight="bold")
    fig.text(0.5, 0.945, "مجمع الشلالات السكني - القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026  -  بنفس إظهار مقترح ابراهيم المطوّر",
             ha="center", fontsize=15)
    rows = table_rows()
    tx = fig.add_axes([0.03, 0.02, 0.45, 0.26])
    tx.axis("off")
    head = [r for r in rows[1:7] if r]
    tx.text(0, 1, "\n".join(head), family="DejaVu Sans Mono", fontsize=10.5, va="top", linespacing=1.5)
    y0 = 0.66
    tx.text(0, y0, "LAND USE", fontsize=10.5, fontweight="bold", va="top")
    tx.text(0.62, y0, "m²", fontsize=10.5, fontweight="bold", va="top", ha="right")
    tx.text(0.72, y0, "%", fontsize=10.5, fontweight="bold", va="top", ha="right")
    tx.text(1.0, y0, "استعمالات الأرض", fontsize=10.5, fontweight="bold", va="top", ha="right")
    for i, (n, a) in enumerate(LANDUSE + [("TOTAL - المجموع", SITE.area)]):
        en, arb = n.split(" - ")
        y = y0 - 0.06 * (i + 1)
        tx.text(0, y, en, fontsize=10, va="top")
        tx.text(0.62, y, f"{a:,.0f}", fontsize=10, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(0.72, y, f"{a / SITE.area * 100:.1f}", fontsize=10, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(1.0, y, arb, fontsize=10, va="top", ha="right")
    key = [
        ("villa", "Villa plot 400 m²", "فلل 400 متر"), ("house", "House plot 240 m²", "دور 240 متر"),
        ("tower", f"Tower G+{FLOORS - 1}", "الأبراج"), ("plaza", "Plaza over the basement car park", "البلازا فوق السرداب"),
        ("serv", "Community services", "الخدمات"), ("util", "Utilities", "المرافق الفنية"),
        ("ls_lawn", "Lawns, raised mounds", "مسطحات خضراء مرتفعة"), ("ls_track", "Coloured jogging track", "مسار ملون"),
        ("shrub", "Shrub beds", "أحواض شجيرات"), ("water", "Lake, cascades, fountains", "بحيرة وشلالات ونوافير"),
        ("parking", "Parking, drop-off bays", "مواقف وأماكن إنزال"), ("road", "Roads", "الشوارع"),
        ("paving", "Green spine + finger walks", "الممشى الأخضر وممرات الأصابع"),
    ]
    lg = fig.add_axes([0.50, 0.02, 0.22, 0.26])
    lg.axis("off")
    for i, (k, en, a) in enumerate(key):
        y = 1 - i * 0.068
        lg.add_patch(plt.Rectangle((0, y - 0.05), 0.08, 0.05, fc=rgb[k], ec="#555", transform=lg.transAxes))
        lg.text(0.11, y - 0.027, f"{en}  -  {a}", fontsize=10.5, va="center", transform=lg.transAxes)
    yg = 1 - len(key) * 0.068 - 0.027
    lg.plot([0, 0.08], [yg] * 2, color="#d00", lw=3, transform=lg.transAxes)
    lg.text(0.11, yg, "Gate  -  بوابة", fontsize=10.5, va="center", transform=lg.transAxes)
    nt = fig.add_axes([0.74, 0.02, 0.24, 0.26])
    nt.axis("off")
    green_pct = sum(g.area for g in GREEN) / SITE.area * 100
    notes = [
        "الفكرة: طريق حلقي مشجّر بعرض 14 م يطوّق المجمع؛ الفلل خارجه والدور في عناقيد داخله.",
        "تعديل 1 (العلاقات والمسارات):",
        "1. كل إصبع أخضر (10 م) يقابل حديقة جيب بين الفلل ومعبر مشاة مرتفع على الحلقة:",
        "    الفيلا تمشي مباشرة عبر الإصبع إلى الممشى الأخضر والحديقة المركزية.",
        "2. ممشى أخضر 6 م من الحديقة الغربية إلى حديقة الشلالات، يعبر المحور بمعبر واحد.",
        f"3. الروضة قسمت إلى روضتين 750+750 م2 (غرب وشرق): أبعد بيت {walk_max(('KG_W', 'KG_E')):.0f} م بدل 538 م.",
        "4. أماكن إنزال طلاب على الحلقة أمام الابتدائية والثانوية والروضة الغربية.",
        "5. سيارات الأبراج تدخل السرداب من منحدرين بين الأبراج مباشرة من الحلقة.",
        "6. شاحنات الخدمة: بوابة الخدمة ثم القوس الجنوبي الشرقي فقط، بلا مرور بين البيوت.",
        "7. كشك حراسة عند البوابة الرئيسية؛ الشرطة عند بوابة الخدمة.",
        "8. حذف النادي (طلب المعماري) وتحويل أرضه إلى الحديقة الغربية.",
        f"الشوارع {ROADS.area / SITE.area * 100:.0f}% والخضرة {green_pct:.0f}%؛ سرداب {PARK_NEED} سيارة.",
        "مخطط المسارات والعلاقات في لوحة مستقلة.",
        "",
        "Layers MP_*, circulation on MP_CIRC_*; colours and landscape follow Ibrahim's proposal.",
    ]
    for i, n in enumerate(notes):
        nt.text(1, 1 - i * 0.064, n, fontsize=10.5, ha="right", va="top", transform=nt.transAxes)
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)


def write_circulation(png, pdf):
    """Circulation + relationships sheet: vehicles, pedestrians, service / emergency, walking distances."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.lines import Line2D
    from matplotlib.path import Path
    from matplotlib.patches import FancyArrowPatch, PathPatch

    fdir = os.path.join(HERE, "..", "fonts")
    for f_ in font_manager.findSystemFonts(fdir):
        font_manager.fontManager.addfont(f_)
    plt.rcParams["font.family"] = ["DejaVu Sans", "Noto Sans Arabic"]
    fig = plt.figure(figsize=(33.1, 23.4))
    ax = fig.add_axes([0.02, 0.30, 0.96, 0.62])

    def f(g, fc, ec="none", lw=0.3, z=1, alpha=1.0):
        for p in polys(g):
            verts, codes = [], []
            for ring in [p.exterior] + list(p.interiors):
                c = list(ring.coords)
                verts += c
                codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha))

    def ln(g, **kw):
        ax.plot(*g.xy, solid_capstyle="round", **kw)

    def lab(s_, at, size=8, color="#111", w="normal"):
        ax.text(at[0], at[1], s_, fontsize=size, ha="center", va="center", color=color, fontweight=w, zorder=20,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85))

    f(SITE, "#f4f4f2", ec="#c00", lw=1.6)
    f(ROADS, "#dcdcdc")
    for p in VILLAS:
        f(p, "#fde6b4", ec="#d9b878", lw=0.2)
    for p in HOUSES:
        f(p, "#f8c4a6", ec="#d08a60", lw=0.2)
    for g in GREEN:
        f(g, "#d5ebc6")
    f(PLAZA, "#d6ecf8")
    for tw in TOWERS:
        f(tw, "#2776bb", z=3)
    for k, g in SERV.items():
        f(g, "#e8a9c8" if k in UTILITIES else "#f19a9c", ec="#a33", lw=0.4, z=2)
        q = g.representative_point()
        ax.text(q.x, q.y, NAMES[k][1], fontsize=6.5, ha="center", va="center", zorder=21)
    for g in WATER:
        f(g, "#9cc9ee", z=2)

    # vehicles
    ln(RING_CL, color="#333", lw=5, zorder=6)
    ln(AXIS_CL, color="#333", lw=5, zorder=6)
    for g in LANE_CL:
        ln(g, color="#777", lw=1.8, zorder=6)
    ln(LineString([(SGATE_U, 0), (SGATE_U, BELT + RING_W / 2)]), color="#333", lw=3, zorder=6)
    # emergency loop, just outside the carriageway
    ln(R_OUT.buffer(-2.5).exterior, color="#f39200", lw=1.6, ls=(0, (2, 2)), zorder=7)
    # tower cars and service trucks
    for g, c in ((TOWER_ROUTE, "#1f5fbf"), (SERVICE_ROUTE, "#d00"), (MALL_ROUTE, "#d00")):
        ln(g, color=c, lw=2.6, ls=(0, (5, 2)), zorder=8)
        p0, p1 = g.coords[-2], g.coords[-1]
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=22, color=c, lw=2.6, zorder=8))
    for g in RAMPS:
        f(g, "#1f5fbf", z=8)
    # pedestrians
    for edge in (R_OUT.buffer(-1.6).exterior, INNER.buffer(1.6).exterior):
        ln(edge, color="#2e8b3a", lw=1.2, ls=(0, (1, 2)), zorder=7)
    ln(SPINE, color="#2e8b3a", lw=5, zorder=9)
    for g in FINGER_WALKS:
        ln(g, color="#2e8b3a", lw=2.4, zorder=9)
    for g in CROSSINGS:
        f(g, "white", ec="#111", lw=0.8, z=10)
    # walking catchments
    for k in ("KG_W", "KG_E"):
        c = SERV[k].centroid
        ax.add_patch(plt.Circle((c.x, c.y), 300, fc="none", ec="#8a3fb0", lw=1.4, ls="--", zorder=5))
    for g in [OPEN["PARK_MALL"]] + LAYBYS:
        f(g, "#bdbdbd", z=2)
    for g in (GATE, SGATE):
        ax.plot(*g.xy, color="#d00", lw=6, zorder=11, solid_capstyle="butt")
    lab("MAIN GATE\nالبوابة الرئيسية", (GATE_U, north_v(GATE_U) + 12), 10, "#b00", "bold")
    lab("SERVICE / EMERGENCY GATE\nبوابة الخدمة والطوارئ", (SGATE_U, -13), 9, "#b00", "bold")
    lab("الطريق الحلقي 14 م باتجاهين\nRING ROAD, TWO-WAY", (250, IN0 - 7), 7)
    lab("الممشى الأخضر 6 م\nGREEN SPINE", (300, 112), 7, "#1d6b28", "bold")
    lab("دخول سرداب الأبراج\nTOWER BASEMENT", RAMPS[0].centroid.coords[0], 6.5, "#1f5fbf")
    lab("شاحنات الخدمة\nSERVICE TRUCKS", (770, 22), 6.5, "#d00")
    lab("تحميل المول\nMALL DELIVERY", (400, north_in(400) + 18), 6.5, "#d00")
    lab("نطاق 300 م للروضة\nKG 300 m", (SERV["KG_W"].centroid.x + 160, SERV["KG_W"].centroid.y + 230), 7, "#8a3fb0")
    ax.set_xlim(-80, 900)
    ax.set_ylim(-25, 330)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.5, 0.965, "مخطط المسارات والعلاقات - البديل 1: الحلقة الخضراء (تعديل 1)   |   CIRCULATION + RELATIONSHIPS - VARIANT 1",
             ha="center", fontsize=26, fontweight="bold")
    fig.text(0.5, 0.945, "مجمع الشلالات السكني - القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026", ha="center", fontsize=15)

    key = [
        (dict(color="#333", lw=5), "الطريق الحلقي ومحور البوابة (سيارات)  -  Ring + gate axis"),
        (dict(color="#777", lw=1.8), "أزقة العناقيد المغلقة (8 دور لكل زقاق)  -  Cul-de-sacs"),
        (dict(color="#1f5fbf", lw=2.6, ls=(0, (5, 2))), "سيارات الأبراج إلى السرداب  -  Tower cars to basement"),
        (dict(color="#d00", lw=2.6, ls=(0, (5, 2))), "شاحنات الخدمة وتحميل المول  -  Service + delivery"),
        (dict(color="#f39200", lw=1.6, ls=(0, (2, 2))), "مسار الطوارئ: الحلقة كاملة + رؤوس الأزقة  -  Emergency loop"),
        (dict(color="#2e8b3a", lw=5), "الممشى الأخضر 6 م  -  Green spine"),
        (dict(color="#2e8b3a", lw=2.4), "ممرات الأصابع الخضراء  -  Finger walks"),
        (dict(color="#2e8b3a", lw=1.2, ls=(0, (1, 2))), "ممشى الحلقة المشجّر 1.9 كم  -  Tree-lined ring walk"),
        (dict(color="#8a3fb0", lw=1.4, ls="--"), "نطاق مشي 300 م للروضتين  -  KG catchments"),
        (dict(color="#bdbdbd", lw=6), "موقف المول وأماكن إنزال الطلاب  -  Parking + drop-off bays"),
    ]
    lg = fig.add_axes([0.03, 0.03, 0.30, 0.24])
    lg.axis("off")
    for i, (st, txt) in enumerate(key):
        y = 1 - i * 0.095
        lg.add_line(Line2D([0, 0.1], [y, y], transform=lg.transAxes, **st))
        lg.text(0.13, y, txt, fontsize=11, va="center", transform=lg.transAxes)
    lg.add_patch(plt.Rectangle((0.02, 1 - len(key) * 0.095 - 0.02), 0.06, 0.04, fc="white", ec="#111", transform=lg.transAxes))
    lg.text(0.13, 1 - len(key) * 0.095, "معبر مشاة مرتفع  -  Raised zebra crossing", fontsize=11, va="center", transform=lg.transAxes)

    rows = [("الروضتان (750+750)", ("KG_W", "KG_E")), ("المدرسة الابتدائية", ("PRIMARY",)),
            ("الجامع", ("MOSQUE",)), ("المول", ("MALL",)), ("المركز الصحي", ("HEALTH",)),
            ("الثانوية", ("SECONDARY",))]
    tb = fig.add_axes([0.36, 0.03, 0.27, 0.24])
    tb.axis("off")
    tb.text(1, 1, "أبعد مسافة مشي من أي سكن (خط مستقيم)", fontsize=13, fontweight="bold", ha="right", va="top")
    tb.text(1, 0.9, "الخدمة", fontsize=11.5, fontweight="bold", ha="right", va="top")
    tb.text(0.35, 0.9, "المسافة م", fontsize=11.5, fontweight="bold", ha="right", va="top")
    for i, (n, ks) in enumerate(rows):
        y = 0.8 - i * 0.1
        tb.text(1, y, n, fontsize=11.5, ha="right", va="top")
        tb.text(0.35, y, f"{walk_max(ks):,.0f}", fontsize=11.5, ha="right", va="top", family="DejaVu Sans Mono")
    tb.text(1, 0.8 - len(rows) * 0.1, "الروضة كانت 538 م قبل التقسيم؛ دليل الإسكان: 300 م للروضة.", fontsize=10.5, ha="right", va="top")

    nt = fig.add_axes([0.66, 0.03, 0.32, 0.24])
    nt.axis("off")
    notes = [
        "العلاقات:",
        "• الفلل: واجهة على الحلقة، ظهر للسور؛ كل مجموعة تطل على حديقة جيب ومعبر إلى إصبع أخضر.",
        "• الدور: أزقة قصيرة بلا مرور عابر، تنتهي على الممشى الأخضر والحديقة المركزية.",
        "• الأبراج: على المحور قرب البوابة، سياراتها لا تمر بالأحياء، والروضة الشرقية بجانبها.",
        "• المركز المدني على محور البوابة: المول والجامع عند الدخول، الابتدائية والصحي جنوب الدوار.",
        "• الأطفال: الروضتان والابتدائية على الممشى الأخضر، والوصول مشيا دون عبور غير معبر واحد.",
        "• الخدمة: الماء والكهرباء والنفايات والشرطة والدفاع المدني على بوابة الخدمة بعيدا عن السكن.",
        "• الطوارئ: الحلقة دائرة مغلقة بمدخلين، وكل زقاق برأس دوران 24×10 م لسيارة الإطفاء.",
        "• لا شارع عند الطرفين القصيرين، ولا شارع داخلي يفتح على الشوارع الخارجية.",
    ]
    for i, n in enumerate(notes):
        nt.text(1, 1 - i * 0.105, n, fontsize=11, ha="right", va="top", transform=nt.transAxes,
                fontweight="bold" if i == 0 else "normal")
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    base = os.path.join(out_dir, "SHALLALAT_MASTERPLAN_V1_GREEN_RING")
    write_dxf(base + ".dxf")
    write_preview(base + "_preview.png", base + "_preview.pdf")
    write_circulation(base + "_CIRCULATION.png", base + "_CIRCULATION.pdf")
    print("\n".join(table_rows()))
