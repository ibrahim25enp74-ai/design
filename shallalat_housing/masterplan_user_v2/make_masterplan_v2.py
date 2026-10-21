"""Writes variant 2 of Ibrahim's proposal («الأحياء المتجاورة»): DXF on the site coordinates + A1 preview.

Same drawing style, colours, landscape and table as make_masterplan_user.py.
Usage: python make_masterplan_v2.py [out_dir]
"""
import math
import os
import sys

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment

from layout_v2 import *  # noqa: F401,F403  (geometry of the layout)
from landscape_v2 import LANDSCAPE, PLAZA_LS
import circulation_v2 as C

HERE = os.path.dirname(os.path.abspath(__file__))
ROT = math.degrees(math.atan2(U[1], U[0]))
TITLE_AR = "مقترح ابراهيم - البديل 2: الأحياء المتجاورة"
TITLE_EN = "IBRAHIM'S PROPOSAL - VARIANT 2: ADJACENT QUARTERS"

NAMES = {
    "MALL": ("MALL", "المول"), "MOSQUE": ("MOSQUE", "الجامع"),
    "POLICE": ("POLICE", "الشرطة"), "CIVIL_DEF": ("CIVIL DEFENCE", "الدفاع المدني"), "HEALTH": ("HEALTH CENTRE", "المركز الصحي"),
    "SECONDARY": ("SECONDARY SCHOOL", "الثانوية (متوسطة + إعدادية)"), "PRIMARY": ("PRIMARY SCHOOL", "المدرسة الابتدائية"),
    "KG": ("KINDERGARTEN", "الروضة"), "KG_W": ("KINDERGARTEN (W)", "الروضة الغربية"), "WATER": ("WATER STATION", "محطة الماء"), "POWER": ("POWER STATION", "محطة الكهرباء"),
    "WASTE": ("WASTE", "النفايات"), "CLUB": ("SOCIAL CLUB + SPORTS", "النادي والملاعب"),
    "PARK_MALL": ("PARKING", "موقف السيارات"), "G_SCHOOL": ("GARDEN", "حديقة"), "G_SEC": ("GARDEN", "حديقة"), "G_HEALTH": ("GARDEN", "حديقة"),
}
QNAMES = {"V1": ("QUARTER 1", "الحي 1"), "V2": ("QUARTER 2", "الحي 2"), "H1": ("QUARTER 3", "الحي 3"),
          "H2": ("QUARTER 4", "الحي 4")}
UTIL_KEYS = UTILITIES


def table_rows():
    units = len(VILLAS) + len(HOUSES) + N_APTS
    rows = [
        f"{TITLE_EN} - {TITLE_AR}",
        "Plot 157 / District 53 Baybokht - NIC 5/2026 - UTM 38S",
        "",
        f"UNITS: {len(VILLAS)} villas 400 m2 + {len(HOUSES)} houses 240 m2 + {N_APTS} flats = {units}",
        f"Towers: {len(TOWERS)} x {FLOORS} floors x {FLATS_PER_FLOOR} flats; parking {PARK_NEED} cars in a basement under the plaza",
        "Entrances: 1 main gate (north road) + 1 service / emergency gate (south road)",
        "",
        "LAND USE - استعمالات الأرض              m2        %",
    ]
    for n, a in LANDUSE:
        rows.append(f"{n:<52s}{a:>9,.0f}  {a / SITE.area * 100:5.1f}")
    rows.append(f"{'TOTAL':<52s}{SITE.area:>9,.0f}  100.0")
    rows.append("")
    rows.append("QUARTERS - الأحياء          plots    pocket park m2")
    for q in QPLOTS:
        rows.append(f"{QNAMES[q][0]} - {QNAMES[q][1]:<14s}{len(QPLOTS[q]):>6d}{PARKS[q].area:>12,.0f}")
    return rows


LAYERS = {
    "MP_BOUNDARY": (1, 50), "MP_BOUNDARY_COORDS": (6, 18), "MP_GATES": (1, 50), "MP_ROADS": (8, 25),
    "MP_PLOT_VILLA": (30, 18), "MP_PLOT_HOUSE": (40, 18), "MP_TOWERS": (5, 50), "MP_PLAZA": (4, 18),
    "MP_SERVICES": (1, 25), "MP_UTILITIES": (6, 25), "MP_PARKING": (9, 13), "MP_GREEN": (3, 13),
    "MP_TEXT": (7, 18), "MP_TEXT_PLOTNO": (8, 9), "MP_TABLE": (7, 18), "MP_NORTH": (7, 25),
    "MP_HATCH_RES": (31, 0), "MP_HATCH_SERV": (1, 0), "MP_HATCH_GREEN": (3, 0), "MP_HATCH_ROAD": (252, 0),
    "MP_HATCH_TOWER": (5, 0), "MP_LANDSCAPE": (94, 13), "MP_GARDEN_PATH": (41, 13), "MP_GARDEN_BEDS": (84, 13), "MP_TREES": (3, 13), "MP_HATCH_LANDSCAPE": (94, 0),
    "MP_CIRC_VEH_COLLECTOR": (250, 50), "MP_CIRC_VEH_LOCAL": (8, 35), "MP_CIRC_VEH_ACCESS": (9, 18),
    "MP_CIRC_PED_GREENWALK": (3, 50), "MP_CIRC_PED_LINK": (94, 25), "MP_CIRC_SERVICE": (200, 35),
    "MP_CIRC_EMERGENCY": (1, 35), "MP_CROSSINGS": (7, 18), "MP_DROPOFF": (40, 18),
}
CIRC_LT = {"MP_CIRC_VEH_ACCESS": "DASHED", "MP_CIRC_PED_GREENWALK": "DASHED2", "MP_CIRC_PED_LINK": "DOT",
           "MP_CIRC_SERVICE": "DASHDOT", "MP_CIRC_EMERGENCY": "DIVIDE"}
# the architect's own colours
FILL = {
    "villa": (254, 204, 102), "house": (242, 103, 34), "serv": (237, 31, 36), "util": (209, 156, 199),
    "green": (19, 103, 52), "park": (120, 186, 110), "plaza": (173, 221, 247), "tower": (39, 118, 187),
    "road": (225, 225, 225), "parking": (190, 190, 190),
    "paving": (236, 226, 204), "lawn": (150, 205, 120), "water": (110, 180, 235), "play": (240, 214, 150),
    "shrub": (78, 120, 52), "flower": (232, 150, 180), "tree": (46, 120, 50),
    "ls_lawn": (150, 196, 74), "ls_pave": (214, 214, 210), "ls_track": (226, 150, 132), "ls_gravel": (196, 194, 186),
    "ls_deck": (204, 146, 100), "ls_pit": (110, 160, 70),
}
GREEN_AREAS = POCKET + BIG + GARDENS


def write_dxf(path):
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 6
    doc.styles.add("AR", font="arial.ttf")
    for n, (c, lw) in LAYERS.items():
        lay = doc.layers.add(n, color=c, lineweight=lw if lw else -3)
        if n in CIRC_LT and CIRC_LT[n] in doc.linetypes:
            lay.dxf.linetype = CIRC_LT[n]
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
    for g in GREEN_AREAS:
        hatch(g, "MP_HATCH_GREEN", FILL["park"])
    for g in BITS:
        hatch(g, "MP_HATCH_GREEN", FILL["lawn"])
    hatch(OPEN["PARK_MALL"], "MP_HATCH_ROAD", FILL["parking"])
    hatch(FORECOURT, "MP_HATCH_LANDSCAPE", FILL["paving"])
    hatch(PLAZA, "MP_HATCH_TOWER", FILL["plaza"])
    hatch(unary_union(CHANNELS + [FOUNTAIN]), "MP_HATCH_LANDSCAPE", FILL["water"])
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
    outline(PLAZA_ALL, "MP_PLAZA")
    for g in [LAWN, PAVING, FOUNTAIN, FOUNTAIN_RING, RAMP] + CHANNELS + JETS:
        outline(g, "MP_LANDSCAPE")
    hatch(DROP_ISLAND, "MP_HATCH_LANDSCAPE", FILL["shrub"])
    outline(DROP_ISLAND, "MP_GARDEN_BEDS")
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
    for g in GREEN_AREAS + BITS:
        outline(g, "MP_GREEN")
    outline(OPEN["PARK_MALL"], "MP_PARKING")
    outline(FORECOURT, "MP_LANDSCAPE")
    for k, g in SERV.items():
        outline(g, "MP_UTILITIES" if k in UTIL_KEYS else "MP_SERVICES")
    msp.add_lwpolyline([utm(q) for q in GATE.coords], dxfattribs={"layer": "MP_GATES"})
    msp.add_lwpolyline([utm(q) for q in SGATE.coords], dxfattribs={"layer": "MP_GATES"})
    # circulation: one centre line per route on its own layer
    for lay, lines in (("MP_CIRC_VEH_COLLECTOR", C.COLLECTORS + [C.GATE_IN, C.SGATE_IN]), ("MP_CIRC_VEH_LOCAL", C.LOCALS),
                       ("MP_CIRC_VEH_ACCESS", C.ACCESS), ("MP_CIRC_PED_GREENWALK", [C.GREEN_WALK]),
                       ("MP_CIRC_PED_LINK", C.PED_LINKS), ("MP_CIRC_SERVICE", C.SERVICE),
                       ("MP_CIRC_EMERGENCY", [C.EMERGENCY, C.CD_OUT])):
        for ln in lines:
            msp.add_lwpolyline([utm(q) for q in ln.coords], dxfattribs={"layer": lay, "ltscale": 0.5})
    for g in C.CROSSINGS:
        outline(g, "MP_CROSSINGS")
        for x_ in np.arange(g.bounds[0] + 1.0, g.bounds[2] - 0.5, 1.5):
            msp.add_lwpolyline([utm((x_, g.bounds[1])), utm((x_, g.bounds[3]))], dxfattribs={"layer": "MP_CROSSINGS"})
    for g in C.DROPOFFS:
        hatch(g, "MP_DROPOFF", FILL["play"])
        outline(g, "MP_DROPOFF")
    text("RAISED CROSSING - معبر مشاة مرتفع", (C.CROSSINGS[2].centroid.x, C.CROSSINGS[2].centroid.y + 6), 1.8)

    for i, p in enumerate(VILLAS):
        text(f"V{i + 1:02d}", tuple(p.centroid.coords[0]), 1.6, layer="MP_TEXT_PLOTNO")
    for i, p in enumerate(HOUSES):
        text(f"H{i + 1:02d}", tuple(p.centroid.coords[0]), 1.4, layer="MP_TEXT_PLOTNO")
    for k, g in {**SERV, **OPEN}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        text(n1, (q.x, q.y + 2.5), 3 if g.area > 900 else 1.8)
        text(f"{n2}  {g.area:,.0f} m2", (q.x, q.y - 2.5), 2.2 if g.area > 900 else 1.4)
    for q_, g in PARKS.items():
        c = g.representative_point()
        text(f"{QNAMES[q_][0]} PARK", (c.x, c.y + 3), 3.5)
        text(f"حديقة {QNAMES[q_][1]}  {g.area:,.0f} m2", (c.x, c.y - 3), 2.6)
    for g, en, ar in ((TOWER_PARK_N, "TOWER PARK (N)", "حديقة الأبراج الشمالية"),
                      (TOWER_PARK_S, "TOWER PARK (S)", "حديقة الأبراج الجنوبية"),
                      (EAST_PARK, "EAST PARK", "الحديقة الشرقية"), (CIVIC_GARDEN, "CIVIC GARDEN", "حديقة الجامع"),
                      (FORECOURT, "CIVIC FORECOURT", "الساحة المدنية")):
        c = g.representative_point()
        text(en, (c.x, c.y + 3), 3.0)
        text(f"{ar}  {g.area:,.0f} m2", (c.x, c.y - 3), 2.2)
    for i, t in enumerate(TOWERS):
        text(f"TOWER {'ABC'[i]}", (t.centroid.x, t.centroid.y + 3), 3.5)
        text(f"G+{FLOORS - 1}, {FLOORS * FLATS_PER_FLOOR} flats", (t.centroid.x, t.centroid.y - 3), 2.2)
    text("RAMP", RAMP.centroid.coords[0], 2.0)
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
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    fdir = os.path.join(HERE, "..", "fonts")
    for f in font_manager.findSystemFonts(fdir):
        font_manager.fontManager.addfont(f)
    plt.rcParams["font.family"] = ["DejaVu Sans", "Noto Sans Arabic"]

    fig = plt.figure(figsize=(33.1, 23.4))  # A1
    ax = fig.add_axes([0.02, 0.30, 0.96, 0.64])
    rgb = {k: tuple(c / 255 for c in v) for k, v in FILL.items()}

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
    for g in GREEN_AREAS:
        f(g, "ls_gravel", ec="#777", lw=0.4)
    for g in BITS:
        f(g, "lawn", ec="#5d7f2a", lw=0.3)
    f(OPEN["PARK_MALL"], "parking", ec="#555", lw=0.4)
    for u in np.arange(OPEN["PARK_MALL"].bounds[0] + 2.5, OPEN["PARK_MALL"].bounds[2], 2.5):
        ax.plot([u, u], [OPEN["PARK_MALL"].bounds[1] + 2, OPEN["PARK_MALL"].bounds[1] + 7], color="white", lw=0.4, zorder=1.5)
    f(FORECOURT, "ls_pave", ec="#777", lw=0.4)
    f(PLAZA, "plaza", ec="#468", lw=0.5)

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
    for g in BITS:
        c = g.representative_point()
        if g.area > 60:
            ax.add_patch(plt.Circle((c.x, c.y), 2.4, fc="#4f8f3a", ec="#2c5a20", lw=0.35, alpha=0.85, zorder=4))
    f(unary_union(CHANNELS + [FOUNTAIN]), "water", ec="#357", lw=0.4, z=3)
    f(DROP_ISLAND, "shrub", ec="#2f5a28", lw=0.3, z=3)
    f(FOUNTAIN_RING, "ls_pave", ec="#999", lw=0.3, z=3)
    f(FOUNTAIN, "water", ec="#357", lw=0.4, z=3.1)
    f(RAMP, "parking", ec="#333", lw=0.5, z=3)
    for g in JETS:
        f(g, None, ec="white", lw=0.5, z=4)
    for x, y in PALMS:
        palm(x, y, 2.2)
    for tw in TOWERS:
        f(tw, "tower", ec="#123", lw=0.8, z=3)
    for k, g in SERV.items():
        f(g, "util" if k in UTIL_KEYS else "serv", ec="#333", lw=0.6, z=2)
    f(SITE, None, ec="#c00", lw=1.6, z=6)
    for g in (GATE, SGATE):
        ax.plot(*g.xy, color="#d00", lw=5, zorder=7, solid_capstyle="butt")
    for g in C.CROSSINGS:
        f(g, "ls_pave", ec="#666", lw=0.4, z=5)
        for x_ in np.arange(g.bounds[0] + 1.0, g.bounds[2] - 0.5, 1.6):
            ax.plot([x_, x_], [g.bounds[1] + 0.4, g.bounds[3] - 0.4], color="white", lw=1.6, zorder=5.1)
    for g in C.DROPOFFS:
        f(g, "play", ec="#975", lw=0.4, z=5)

    for k, g in {**SERV, **OPEN}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        t(f"{n1}\n{g.area:,.0f} m²", (q.x, q.y), 7 if g.area > 900 else 5.5, ar_s=n2)
    for q_, g in PARKS.items():
        c = g.centroid
        t(f"{QNAMES[q_][0]} PARK\n{g.area:,.0f} m²", (c.x, c.y), 7.5, ar_s=f"حديقة {QNAMES[q_][1]}", w="bold")
        a, b = Q_RANGE[q_]
        kind = "VILLAS" if q_.startswith("V") else "HOUSES"
        t(f"{QNAMES[q_][0]}: {len(QPLOTS[q_])} {kind}", ((a + b) / 2, north_v((a + b) / 2) + 9), 8.5,
          ar_s=f"{QNAMES[q_][1]}: {len(QPLOTS[q_])} {'فيلا' if kind == 'VILLAS' else 'دار'}", w="bold")
    for g, en, ar, dy in ((TOWER_PARK_N, "TOWER PARK", "حديقة الأبراج", 0), (TOWER_PARK_S, "TOWER PARK", "حديقة الأبراج", 0),
                          (EAST_PARK, "EAST PARK", "الحديقة الشرقية", 0), (CIVIC_GARDEN, "CIVIC GARDEN", "حديقة الجامع", 26),
                          (FORECOURT, "CIVIC FORECOURT", "الساحة المدنية", 0)):
        c = g.centroid
        t(f"{en}\n{g.area:,.0f} m²", (c.x, c.y + dy), 6.5, ar_s=ar, w="bold")
    for i, tw in enumerate(TOWERS):
        t(f"{'ABC'[i]}\nG+{FLOORS - 1}", tw.centroid.coords[0], 7, color="white", w="bold", z=11)
    t("RAMP", RAMP.centroid.coords[0], 4, ar_s="منحدر")
    t("DROP-OFF", (TOWER_END - 2, 150.0), 4.5, ar_s="نزول")
    sa_, sb2_ = Q_RANGE["SPINE"]
    t("CIVIC SPINE", ((sa_ + sb2_) / 2, north_v((sa_ + sb2_) / 2) + 9), 8.5, ar_s="المحور المدني", w="bold")
    t("MAIN GATE", (GATE_U + 40, north_v(GATE_U + 40) + 12), 9, ar_s="البوابة الرئيسية", w="bold", color="#b00")
    t("SERVICE / EMERGENCY GATE", (SGATE_U, -10), 8, ar_s="بوابة الخدمة والطوارئ", w="bold", color="#b00")
    t("3 TOWERS + PLAZA", (20, north_v(20) + 9), 8.5, ar_s="الأبراج والبلازا", w="bold")

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

    fig.text(0.5, 0.965, f"المخطط العام - {TITLE_AR}   |   MASTER PLAN - {TITLE_EN}", ha="center", fontsize=26, fontweight="bold")
    fig.text(0.5, 0.945, "مجمع الشلالات السكني - القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026", ha="center", fontsize=15)
    rows = table_rows()
    tx = fig.add_axes([0.03, 0.02, 0.45, 0.26])
    tx.axis("off")
    head = [r for r in rows[1:7] if r]
    tx.text(0, 1, "\n".join(head), family="DejaVu Sans Mono", fontsize=10.5, va="top", linespacing=1.5)
    y0 = 0.70
    tx.text(0, y0, "LAND USE", fontsize=10.5, fontweight="bold", va="top")
    tx.text(0.62, y0, "m²", fontsize=10.5, fontweight="bold", va="top", ha="right")
    tx.text(0.72, y0, "%", fontsize=10.5, fontweight="bold", va="top", ha="right")
    tx.text(1.0, y0, "استعمالات الأرض", fontsize=10.5, fontweight="bold", va="top", ha="right")
    for i, (n, a) in enumerate(LANDUSE + [("TOTAL - المجموع", SITE.area)]):
        en, arb = n.split(" - ")
        y = y0 - 0.055 * (i + 1)
        tx.text(0, y, en, fontsize=10, va="top")
        tx.text(0.62, y, f"{a:,.0f}", fontsize=10, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(0.72, y, f"{a / SITE.area * 100:.1f}", fontsize=10, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(1.0, y, arb, fontsize=10, va="top", ha="right")
    y = y0 - 0.055 * (len(LANDUSE) + 2) - 0.01
    tx.text(0, y, "QUARTERS: " + "   ".join(f"{QNAMES[q][0][-1]}: {len(QPLOTS[q])} {'villas' if q[0] == 'V' else 'houses'}, park {PARKS[q].area:,.0f} m²"
                                           for q in QPLOTS), fontsize=10, va="top")
    key = [
        ("villa", "Villa plot 400 m²", "فلل 400 متر"), ("house", "House plot 240 m²", "دور 240 متر"),
        ("tower", f"Tower G+{FLOORS - 1}", "الأبراج"), ("plaza", "Plaza over the basement car park", "البلازا فوق السرداب"),
        ("serv", "Community services", "الخدمات"), ("util", "Utilities", "المرافق الفنية"),
        ("ls_lawn", "Lawn mounds", "مسطحات خضراء"), ("ls_track", "Coloured jogging track", "مسار ملون"),
        ("ls_pave", "Paving", "تبليط"), ("ls_deck", "Timber deck", "رصيف خشبي"),
        ("shrub", "Shrub beds", "أحواض شجيرات"),
        ("parking", "Parking", "موقف سيارات"), ("road", "Roads", "الشوارع"),
    ]
    lg = fig.add_axes([0.50, 0.02, 0.22, 0.26])
    lg.axis("off")
    for i, (k, en, a) in enumerate(key):
        y = 1 - i * 0.064
        lg.add_patch(plt.Rectangle((0, y - 0.047), 0.08, 0.047, fc=rgb[k], ec="#555", transform=lg.transAxes))
        lg.text(0.11, y - 0.025, f"{en}  -  {a}", fontsize=10.5, va="center", transform=lg.transAxes)
    yg = 1 - len(key) * 0.064 - 0.025
    lg.plot([0, 0.08], [yg] * 2, color="#d00", lw=3, transform=lg.transAxes)
    lg.text(0.11, yg, "Gate  -  بوابة", fontsize=10.5, va="center", transform=lg.transAxes)
    nt = fig.add_axes([0.74, 0.02, 0.24, 0.26])
    nt.axis("off")
    notes = [
        "الفكرة: أحياء متجاورة على طول الموقع، لكل حي حديقته في وسطه.",
        "الأبراج الثلاثة في الطرف الغربي العريض على بلازا بين حديقتين.",
        "حيّان للفلل (40 + 40) ثم المحور المدني ثم حيّان للدور (58 + 30).",
        "صفوف القطع موازية للشارعين الطويلين، والتفاوت في العرض تأخذه الحدائق.",
        "شوارع عرضية 12 م بين الأحياء، وممرات داخلية 10 م، والشارعان الطويلان 14 م.",
        "نهايات الصفوف المطلة على الحديقة صارت مداخل خضراء للحديقة من الشارع العرضي.",
        "المحور المدني مقابل البوابة الرئيسية: مول وموقفه، ساحة مدنية،",
        "صحي 1000، شرطة 600 ودفاع مدني 600 على الشارع الشمالي، جامع 2000 وسط حديقته، ابتدائية 3000.",
        "روضتان 750 + 750 (غربية للأبراج والحي 1، ووسطية) لتقريب الروضة من كل الأحياء (أبعد بيت ~370 م).",
        "الطرف الشرقي: الثانوية 5000 ومرافق الماء والكهرباء والنفايات عند بوابة الخدمة، والباقي حديقة (أُلغي النادي).",
        f"ممر أخضر متصل {C.GREEN_WALK.length:,.0f} م يربط البلازا بكل الحدائق والمحور المدني، و6 معابر مشاة مرتفعة.",
        "البلازا: نزول عند الشارع العرضي، نافورة، ممشيان بقناة ماء ونخيل بين الأبراج.",
        f"موقف سرداب تحت البلازا لـ {PARK_NEED} سيارة (1.5 لكل شقة)، منحدر في الزاوية الجنوبية.",
        "الحدائق على أسلوب الصورة المرجعية: مسار ملون بزوايا، مسطحات مضلعة، ساحات مبلطة، رصيف خشبي.",
        "مدخلان فقط: رئيسي شمالا وخدمة جنوبا، ولا شوارع على الضلعين القصيرين.",
        "مخطط الحركة والعلاقات في لوحة منفصلة. Layers MP_*, circulation on MP_CIRC_*.",
    ]
    for i, n in enumerate(notes):
        nt.text(1, 1 - i * 0.064, n, fontsize=10.5, ha="right", va="top", transform=nt.transAxes)
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)


def write_circulation(png, pdf):
    """Sheet 2: circulation and relationships - zones in pale colours, routes on top, distance matrix."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch, FancyArrowPatch

    fig = plt.figure(figsize=(33.1, 23.4))
    ax = fig.add_axes([0.02, 0.30, 0.96, 0.64])
    rgb = {k: tuple(c / 255 for c in v) for k, v in FILL.items()}

    def f(g, key, alpha=0.35, ec="#999", lw=0.3, z=1):
        for p in polys(g):
            verts, codes = [], []
            for ring in [p.exterior] + list(p.interiors):
                c = list(ring.coords)
                verts += c
                codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), fc=rgb[key] if key else "none", ec=ec, lw=lw, zorder=z,
                                   alpha=alpha))

    def line(ln, color, lw, ls="-", z=5):
        ax.plot(*ln.xy, color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="round", dash_capstyle="round")

    def t(s, at, size=8, w="normal", color="#111", z=10):
        ax.text(at[0], at[1], s, fontsize=size, ha="center", va="center", fontweight=w, color=color, zorder=z,
                linespacing=1.1, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85))

    f(ROADS, "road", 0.6)
    for p in VILLAS:
        f(p, "villa", 0.35, ec="none")
    for p in HOUSES:
        f(p, "house", 0.3, ec="none")
    for g in GREEN_AREAS + BITS:
        f(g, "park", 0.35, ec="none")
    f(PLAZA_ALL, "plaza", 0.5, ec="none")
    for tw in TOWERS:
        f(tw, "tower", 0.6, ec="none")
    for k, g in SERV.items():
        f(g, "util" if k in UTIL_KEYS else "serv", 0.45, ec="#c66", lw=0.5)
        q = g.representative_point()
        ax.text(q.x, q.y, NAMES[k][1], fontsize=6.5, ha="center", va="center", zorder=9, color="#600")
    f(SITE, None, 1, ec="#c00", lw=1.6, z=6)

    COL = {"col": "#333333", "loc": "#777777", "acc": "#aaaaaa", "walk": "#1f9a3a", "link": "#7cc36a",
           "serv": "#8e44ad", "emer": "#e01b24"}
    for ln in C.COLLECTORS + [C.GATE_IN, C.SGATE_IN]:
        line(ln, COL["col"], 5.5)
    for ln in C.LOCALS:
        line(ln, COL["loc"], 3.2)
    for ln in C.ACCESS:
        line(ln, COL["acc"], 1.8, "--")
    line(C.EMERGENCY.parallel_offset(4.5, "left"), COL["emer"], 1.6, (0, (6, 2, 1, 2)), z=6)
    line(C.CD_OUT, COL["emer"], 2.4, z=6)
    for ln in C.SERVICE:
        line(ln.parallel_offset(3.5, "right") if ln.length > 0 else ln, COL["serv"], 2.6, (0, (5, 2)), z=6.5)
    line(C.GREEN_WALK, COL["walk"], 4.5, (0, (3, 1.5)), z=7)
    for ln in C.PED_LINKS:
        line(ln, COL["link"], 2.4, ":", z=7)
    for g in C.CROSSINGS:
        f(g, None, 1, ec="#1f9a3a", lw=1.4, z=8)
    for g in C.DROPOFFS:
        f(g, "play", 1, ec="#975", lw=0.8, z=8)
    for g in (GATE, SGATE):
        ax.plot(*g.xy, color="#d00", lw=7, zorder=9, solid_capstyle="butt")
    t("البوابة الرئيسية\nMAIN GATE", (GATE_U, north_v(GATE_U) + 14), 10, "bold", "#b00")
    t("بوابة الخدمة والطوارئ\nSERVICE / EMERGENCY GATE", (SGATE_U, -13), 9, "bold", "#b00")

    # relationship arrows: each residential zone -> its kindergarten, the civic spine, the secondary school
    sp = SERV["MOSQUE"].centroid
    hubs = {"KG_W": SERV["KG_W"].centroid, "KG": SERV["KG"].centroid, "SP": sp, "SEC": SERV["SECONDARY"].centroid}
    zones = {"Towers": PLAZA_ALL.centroid, "V1": PARKS["V1"].centroid, "V2": PARKS["V2"].centroid,
             "H1": PARKS["H1"].centroid, "H2": PARKS["H2"].centroid}
    links = [("Towers", "KG_W"), ("V1", "KG_W"), ("V2", "SP"), ("V1", "SP"), ("Towers", "SP"), ("H1", "SP"),
             ("H2", "SP"), ("H1", "KG"), ("H2", "KG"), ("H2", "SEC"), ("H1", "SEC")]
    for a, b in links:
        pa, pb = zones[a], hubs[b]
        ax.add_patch(FancyArrowPatch((pa.x, pa.y), (pb.x, pb.y), arrowstyle="-|>", mutation_scale=14,
                                     connectionstyle="arc3,rad=0.18", color="#1d4f91", lw=1.2, alpha=0.7, zorder=8))
    for z, lab in (("Towers", "الأبراج 240 شقة"), ("V1", "الحي 1: 40 فيلا"), ("V2", "الحي 2: 40 فيلا"),
                   ("H1", "الحي 3: 58 دار"), ("H2", "الحي 4: 30 دار")):
        t(lab, (zones[z].x, zones[z].y + 9), 10, "bold", "#1d4f91")
    t("المحور المدني\nCIVIC SPINE", (sp.x, sp.y), 10, "bold", "#600")

    ax.set_xlim(-80, 900)
    ax.set_ylim(-25, 330)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.5, 0.965, f"مخطط الحركة والعلاقات - {TITLE_AR}   |   CIRCULATION + RELATIONSHIPS - VARIANT 2",
             ha="center", fontsize=26, fontweight="bold")
    fig.text(0.5, 0.945, "مجمع الشلالات السكني - القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026", ha="center", fontsize=15)

    # legend
    lg = fig.add_axes([0.03, 0.02, 0.27, 0.26])
    lg.axis("off")
    items = [(COL["col"], 5.5, "-", "Collector road 14 m (north + south)", "شارع تجميعي 14 م"),
             (COL["loc"], 3.2, "-", "Cross street 12 m", "شارع عرضي محلي 12 م"),
             (COL["acc"], 1.8, "--", "Quarter lane 10 m (access only)", "ممر خدمة الحي 10 م"),
             (COL["walk"], 4.5, (0, (3, 1.5)), "Green walk through all parks", "الممر الأخضر للمشاة"),
             (COL["link"], 2.4, ":", "Pedestrian links to services", "روابط المشاة للخدمات"),
             (COL["serv"], 2.6, (0, (5, 2)), "Service vehicles", "حركة الخدمة"),
             (COL["emer"], 1.6, (0, (6, 2, 1, 2)), "Emergency ring + civil defence exit", "حلقة الطوارئ"),
             ("#1d4f91", 1.2, "-", "Relationship: zone -> service it uses", "علاقة: الحي -> الخدمة")]
    for i, (c, w, ls, en, ar) in enumerate(items):
        y = 1 - i * 0.1
        lg.plot([0, 0.12], [y, y], color=c, lw=w, ls=ls, transform=lg.transAxes)
        lg.text(0.15, y, f"{en}  -  {ar}", fontsize=11, va="center", transform=lg.transAxes)
    y = 1 - len(items) * 0.1
    lg.add_patch(plt.Rectangle((0.0, y - 0.025), 0.12, 0.05, fc="none", ec="#1f9a3a", lw=1.4, transform=lg.transAxes))
    lg.text(0.15, y, "Raised pedestrian crossing  -  معبر مشاة مرتفع", fontsize=11, va="center", transform=lg.transAxes)
    y -= 0.1
    lg.add_patch(plt.Rectangle((0.0, y - 0.025), 0.12, 0.05, fc=rgb["play"], ec="#975", transform=lg.transAxes))
    lg.text(0.15, y, "School / KG drop-off lay-by  -  موقف إنزال المدارس", fontsize=11, va="center", transform=lg.transAxes)

    # distance matrix
    mx = fig.add_axes([0.33, 0.02, 0.38, 0.26])
    mx.axis("off")
    cols = list(next(iter(C.DIST.values())).keys())
    mx.text(0, 1.0, "Walking distance from the farthest home (m)  -  مسافة المشي من أبعد بيت (م)", fontsize=12,
            fontweight="bold", va="top")
    for j, c in enumerate(cols):
        en, ar = c.split(" - ")
        mx.text(0.24 + j * 0.128, 0.88, f"{ar}\n{en}", fontsize=9, ha="center", va="top", fontweight="bold")
    for i, (z, row) in enumerate(C.DIST.items()):
        y = 0.72 - i * 0.1
        en, ar = z.split(" - ")
        mx.text(0, y, f"{ar}  {en}", fontsize=10.5, va="center")
        for j, c in enumerate(cols):
            d = row[c]
            limit = 350 if "Kinder" in c else (500 if "Primary" in c or "Mosque" in c or "Own" in c else 800)
            mx.text(0.24 + j * 0.128, y, f"{d:,.0f}", fontsize=10.5, ha="center", va="center",
                    color="#1a7a2a" if d <= limit else "#c0392b", fontweight="bold", family="DejaVu Sans Mono")
    mx.text(0, 0.12, "Green = within the target (KG 350, primary / mosque / park 500, others 800 m); "
            "measured along the street grid.", fontsize=9.5, va="top")
    mx.text(0, 0.05, "أخضر = ضمن الحد (روضة 350، ابتدائية وجامع وحديقة 500، الباقي 800 م)، مقاسة على شبكة الشوارع.",
            fontsize=9.5, va="top")

    nt = fig.add_axes([0.74, 0.02, 0.24, 0.26])
    nt.axis("off")
    notes = [
        "هرمية الشوارع: تجميعي 14 م على الضلعين الطويلين، عرضي 12 م بين الأحياء،",
        "وممرات 10 م للوصول فقط، فلا حركة عابرة داخل الأحياء.",
        "الزوار والمول من البوابة الرئيسية مباشرة إلى الساحة المدنية، دون دخول الأحياء.",
        "الخدمة من بوابة الخدمة على الشارع الجنوبي إلى المرافق والثانوية فقط.",
        "الدفاع المدني والشرطة على الشارع الشمالي، وحلقة الطوارئ تصل كل قطعة.",
        f"الممر الأخضر {C.GREEN_WALK.length:,.0f} م: البلازا - حدائق الأحياء - حديقة الجامع - الحديقة الشرقية،",
        "يعبر الشوارع العرضية بمعابر مرتفعة؛ الأطفال يمشون للمدارس داخل الحدائق.",
        "مواقف إنزال للروضتين والابتدائية والثانوية خارج مسار السيارات.",
        "الأبراج: نزول على الشارع العرضي الأول، منحدر السرداب في الزاوية الجنوبية،",
        "وممشى البلازا يستمر عبر المعبر إلى حديقة الحي 1.",
    ]
    for i, n in enumerate(notes):
        nt.text(1, 1 - i * 0.085, n, fontsize=11, ha="right", va="top", transform=nt.transAxes)
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    base = os.path.join(out_dir, "SHALLALAT_MASTERPLAN_IBRAHIM_V2_QUARTERS")
    write_dxf(base + ".dxf")
    write_preview(base + "_preview.png", base + "_preview.pdf")
    write_circulation(base + "_CIRCULATION.png", base + "_CIRCULATION.pdf")
    print("\n".join(table_rows()))
