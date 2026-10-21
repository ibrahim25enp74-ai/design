"""Writes proposal F rev 1 "towers in the heart" (الأبراج في القلب - تعديل 1): DXF + A1 sheet with large labels.

The sheet carries everything inside the image, large and bold: a label with name + area on every part,
the main gate and the service gate, a box with the unit counts, and a legend with the % of each land use.
Usage: python make_masterplan_F1.py [out_dir]
"""
import math
import os
import sys

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString
from shapely.ops import unary_union

from layout_F1 import *  # noqa: F401,F403  (geometry of the layout)

HERE = os.path.dirname(os.path.abspath(__file__))
ROT = math.degrees(math.atan2(U[1], U[0]))
BASE = "SHALLALAT_MASTERPLAN_F_REV1"


# --- indicative footprints -----------------------------------------------------------------------
def footprint(b, spec):
    ta, tb, na, nb, front = spec
    if b["kind"] == "V":   # 160 m2 ground floor (40 %), 4 m front setback, 3 m side yards
        sb, dep, side = 4.0, 16.0, 3.0
    else:                  # 144 m2 (60 %), 2.5 m front setback, attached on both sides
        sb, dep, side = 2.5, 14.4, 0.0
    if front == "t+":
        r = (tb - sb - dep, tb - sb, na + side, nb - side)
    elif front == "t-":
        r = (ta + sb, ta + sb + dep, na + side, nb - side)
    else:
        r = (ta + side, tb - side, na + sb, na + sb + dep)
    s = b["s"]
    return b["fr"].rect(r[0], r[1], s * r[2], s * r[3])


for b in BLOCKS:
    b["fps"] = [footprint(b, q) for q in b["specs"]]
ARC_FPS = [arc_footprint(*q) for q in ARC_SPECS]

NAMES = {
    "PRIMARY": ("PRIMARY SCHOOL", "مدرسة ابتدائية"), "SECONDARY": ("SECONDARY SCHOOL", "ثانوية (متوسطة + إعدادية)"),
    "MALL": ("MALL", "المول"), "HEALTH": ("HEALTH CENTRE", "مركز صحي"), "POWER": ("POWER STATION", "محطة كهرباء"),
    "POLICE": ("POLICE", "شرطة"), "CIVIL_DEF": ("CIVIL DEFENCE", "دفاع مدني"),
    "MOSQUE": ("MOSQUE", "الجامع"), "KG": ("KINDERGARTEN", "الروضة"),
    "WATER": ("WATER STATION", "محطة الماء"), "WASTE": ("WASTE", "النفايات"),
    "P_SCHOOL": ("SCHOOLS PARKING", "موقف المدارس"), "P_MALL": ("MALL PARKING", "موقف المول"),
}

TOWER_NAMES = ("A", "B", "C")
N_V, N_H = len(VILLAS), len(HOUSES)
N_UNITS = N_V + N_H + N_APTS


def table_rows():
    rows = [
        "PROPOSAL F - TOWERS IN THE HEART - REV 1 - المقترح و: الأبراج في القلب - تعديل 1",
        "Plot 157 / District 53 Baybokht - NIC 5/2026 - UTM 38S",
        f"UNITS: {N_V} villas 400 m2 + {N_H} houses 240 m2 + {N_APTS} flats = {N_UNITS}",
        "Towers: 3 x 20 floors x 4 flats; plaza over a 2-level basement, 360 cars",
        "Entrances: 1 main gate (north road) + 1 service / emergency gate (south road)",
        "",
        "LAND USE - استعمالات الأرض              m2        %",
    ]
    for n, a in LANDUSE:
        rows.append(f"{n:<60s}{a:>9,.0f}  {a / SITE.area * 100:5.1f}")
    rows.append(f"{'TOTAL':<60s}{SITE.area:>9,.0f}  100.0")
    return rows


# --- colours (same palette as the client's own proposal) ----------------------------------------------
FILL = {
    "villa": (253, 201, 90), "house": (240, 101, 34), "tower": (40, 110, 190), "plaza": (180, 220, 245),
    "serv": (232, 32, 40), "util": (204, 160, 210), "lawn": (160, 205, 85), "court": (120, 180, 60),
    "park": (105, 170, 65), "water": (110, 180, 235), "road": (215, 215, 215), "lane": (232, 232, 232),
    "parking": (185, 185, 185), "cross": (170, 170, 170),
}

# --- DXF --------------------------------------------------------------------------------------------
LAYERS = {
    "MP_BOUNDARY": (1, 50), "MP_BOUNDARY_COORDS": (6, 18), "MP_FENCE": (8, 35), "MP_GATES": (1, 50),
    "MP_ROADS": (8, 25), "MP_ROAD_CL": (8, 13), "MP_LANES": (8, 18), "MP_PARKING": (9, 13),
    "MP_PLOT_VILLA": (30, 18), "MP_PLOT_HOUSE": (40, 18), "MP_FOOTPRINT": (7, 25), "MP_TOWERS": (5, 50),
    "MP_PODIUM": (5, 13), "MP_SERVICES": (1, 25), "MP_UTILITIES": (6, 25),
    "MP_GREEN_COURT": (3, 13), "MP_GREEN_PARK": (94, 13), "MP_WATER": (5, 18), "MP_TREES": (3, 13),
    "MP_CONTEXT": (8, 13), "MP_TEXT": (7, 18), "MP_TEXT_PLOTNO": (8, 9), "MP_TABLE": (7, 18), "MP_NORTH": (7, 25),
    "MP_HATCH_RES": (31, 0), "MP_HATCH_SERV": (1, 0), "MP_HATCH_GREEN": (93, 0), "MP_HATCH_ROAD": (252, 0),
    "MP_HATCH_WATER": (151, 0), "MP_HATCH_TOWER": (5, 0),
}


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

    def line(ls, layer):
        msp.add_lwpolyline([utm(q) for q in ls.coords], dxfattribs={"layer": layer})

    def text(s, at, h=3.0, rot=0.0, layer="MP_TEXT"):
        t = msp.add_text(s, height=h, rotation=rot + ROT, dxfattribs={"layer": layer, "style": "AR"})
        t.set_placement(utm(at), align=TextEntityAlignment.MIDDLE_CENTER)

    hatch(R_IN, "MP_HATCH_GREEN", FILL["lawn"])
    hatch(ORCHARD, "MP_HATCH_GREEN", FILL["park"])
    hatch(ROADS, "MP_HATCH_ROAD", FILL["road"])
    hatch(PARK, "MP_HATCH_GREEN", FILL["park"])
    hatch(PODIUM, "MP_HATCH_ROAD", FILL["plaza"])
    hatch(LAKE, "MP_HATCH_WATER", FILL["water"])
    hatch(CASCADE, "MP_HATCH_WATER", FILL["water"])
    for b in BLOCKS:
        hatch(b["court"], "MP_HATCH_GREEN", FILL["court"])
        hatch(b["lane"], "MP_HATCH_ROAD", FILL["lane"])
        for p in b["plots"]:
            hatch(p, "MP_HATCH_RES", FILL["villa" if b["kind"] == "V" else "house"])
    for p in ARC:
        hatch(p, "MP_HATCH_RES", FILL["house"])
    hatch(T_DROP, "MP_HATCH_ROAD", FILL["road"])
    for r in RAMPS:
        hatch(r, "MP_HATCH_ROAD", FILL["parking"])
    hatch(CROSS_IN, "MP_HATCH_ROAD", FILL["cross"])
    for g in list(PUB.values()) + list(SERV.values()):
        hatch(g, "MP_HATCH_SERV", FILL["serv"])
    for g in list(PUB_PARK.values()) + [HEART_PARK]:
        hatch(g, "MP_HATCH_ROAD", FILL["parking"])
    for g in UTIL_ITEMS.values():
        hatch(g, "MP_HATCH_SERV", FILL["util"])
    for t in TOWERS:
        hatch(t, "MP_HATCH_TOWER", FILL["tower"])

    outline(SITE, "MP_BOUNDARY")
    outline(SITE_RAW, "MP_BOUNDARY_COORDS")
    outline(REST.buffer(-0.5, join_style="mitre"), "MP_FENCE")
    outline(ROADS, "MP_ROADS")
    outline(RING_INN, "MP_ROADS")
    for a, b_ in SPINES.values():
        line(LineString([a, b_]), "MP_ROAD_CL")
    msp.add_ellipse(utm(HC), major_axis=tuple(np.append(U * RING_A, 0)), ratio=RING_B / RING_A, dxfattribs={"layer": "MP_ROAD_CL"})
    outline(CROSS_IN, "MP_ROADS")
    line(GATE_LINE, "MP_GATES")
    outline(GUARD, "MP_GATES")
    outline(GUARD_ISL, "MP_GATES")
    line(U_GATE, "MP_GATES")
    outline(PARK, "MP_GREEN_PARK")
    for t in TOWERS:
        outline(t, "MP_TOWERS")
    outline(PODIUM, "MP_PODIUM")
    outline(T_DROP, "MP_ROADS")
    for r in RAMPS:
        outline(r, "MP_PARKING")
    outline(LAKE, "MP_WATER")
    outline(CASCADE, "MP_WATER")
    for p in PATHS:
        line(p, "MP_GREEN_PARK")
    for b in BLOCKS:
        outline(b["lane"], "MP_LANES")
        outline(b["court"], "MP_GREEN_COURT")
        lay = "MP_PLOT_VILLA" if b["kind"] == "V" else "MP_PLOT_HOUSE"
        for p in b["plots"]:
            outline(p, lay)
        for fp in b["fps"]:
            outline(fp, "MP_FOOTPRINT")
    for p in ARC:
        outline(p, "MP_PLOT_HOUSE")
    for fp in ARC_FPS:
        outline(fp, "MP_FOOTPRINT")
    for g in list(PUB.values()) + list(SERV.values()):
        outline(g, "MP_SERVICES")
    for g in list(PUB_PARK.values()) + [HEART_PARK]:
        outline(g, "MP_PARKING")
    for g in UTIL_ITEMS.values():
        outline(g, "MP_UTILITIES")
    outline(ORCHARD, "MP_GREEN_PARK")
    for g in GARDENS:
        outline(g, "MP_GREEN_PARK")
    for t in TREES:
        msp.add_circle(utm(t), 4, dxfattribs={"layer": "MP_TREES"})
    for a, b_ in ((P[3], P[0]), (P[1], P[2])):   # outer roads, approx. from the cadastral scan
        la, lb = loc(a), loc(b_)
        dv = np.subtract(lb, la) / math.dist(la, lb)
        for d in (0.0, 12.0):
            nn = np.array([-dv[1], dv[0]]) * d * (1 if a == P[1] else -1)
            msp.add_line(utm(tuple(np.add(la, nn - dv * 40))), utm(tuple(np.add(lb, nn + dv * 40))), dxfattribs={"layer": "MP_CONTEXT"})

    for b in BLOCKS:
        kind = f"{len(b['plots'])} villas 400 m2 - فلل" if b["kind"] == "V" else f"{len(b['plots'])} houses 240 m2 - دور"
        cc = b["court"].representative_point()
        text(b["name"], (cc.x, cc.y + 4), 5, rot=90)
        text(kind, (cc.x + 4, cc.y), 2.2, rot=90)
        for j, p in enumerate(b["plots"]):
            q = p.centroid
            text(f"{b['name']}-{j + 1:02d}", (q.x, q.y), 1.2, layer="MP_TEXT_PLOTNO")
    for j, p in enumerate(ARC):
        q = p.centroid
        text(f"R-{j + 1:02d}", (q.x, q.y), 1.2, layer="MP_TEXT_PLOTNO")
    for k, g in {**PUB, **SERV, **UTIL_ITEMS, **PUB_PARK}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        text(n1, (q.x, q.y + 2.5), 3)
        text(f"{n2}  {g.area:,.0f} m2", (q.x, q.y - 2.5), 2.2)
    for t, nm in zip(TOWERS, TOWER_NAMES):
        text(f"TOWER {nm}", (t.centroid.x, t.centroid.y + 3), 3.5)
        text("G+19, 80 flats", (t.centroid.x, t.centroid.y - 3), 2.2)
    text("MAIN GATE - البوابة الرئيسية", (HC[0], GV + 10), 5)
    text("SERVICE / EMERGENCY GATE - بوابة الخدمة والطوارئ", (U_GATE.centroid.x, -10), 4)
    text("SHALLALAT CENTRAL PARK - حديقة الشلالات المركزية", (HC[0], HC[1] - 8), 3.5)

    na = (-120, 260)
    gn = np.array([U[1], V[1]])
    tip = tuple(np.add(na, gn * 30))
    msp.add_lwpolyline([utm(tuple(np.add(na, np.array([-gn[1], gn[0]]) * 8 - gn * 10))), utm(tip),
                        utm(tuple(np.add(na, np.array([gn[1], -gn[0]]) * 8 - gn * 10)))], close=True, dxfattribs={"layer": "MP_NORTH"})
    text("N", tuple(np.add(na, gn * 40)), 10, layer="MP_NORTH")
    tx, ty = 338560.0, 4035840.0
    for i, row in enumerate(table_rows()):
        msp.add_text(row, height=5 if i == 0 else 3.6, dxfattribs={"layer": "MP_TABLE", "style": "AR"}).set_placement(
            (tx, ty - i * 6.5), align=TextEntityAlignment.TOP_LEFT)
    doc.saveas(path)


# --- A1 sheet with large labels -----------------------------------------------------------------------
def write_preview(png, pdf):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import FancyArrow, FancyBboxPatch
    from matplotlib.patches import Polygon as MPoly

    fd = os.path.join(HERE, "..", "fonts")
    if os.path.isdir(fd):
        for f in font_manager.findSystemFonts(fd):
            font_manager.fontManager.addfont(f)
    plt.rcParams["font.family"] = ["DejaVu Sans", "Noto Sans Arabic"]

    fig = plt.figure(figsize=(33.1, 23.4))  # A1
    ax = fig.add_axes([0.01, 0.30, 0.98, 0.63])
    rgb = {k: tuple(c / 255 for c in v) for k, v in FILL.items()}

    def f(g, key, ec="#555", lw=0.3, z=1):
        for p in polys(g):
            ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=rgb[key] if key else "none", ec=ec, lw=lw, zorder=z))
            for h in p.interiors:
                ax.add_patch(MPoly(list(h.coords), closed=True, fc="none", ec=ec, lw=lw, zorder=z))

    def lab(s, at, size=13, rot=0, color="#111", bg="white", z=20, w="bold"):
        ax.text(at[0], at[1], s, fontsize=size, ha="center", va="center", fontweight=w, color=color, rotation=rot,
                zorder=z, linespacing=1.15,
                bbox=dict(boxstyle="round,pad=0.25", fc=bg, ec="#333", lw=0.8, alpha=0.92) if bg else None)

    # land
    f(SITE, "lawn", ec="none")
    f(ORCHARD, "park", ec="none")
    f(CROSS_IN, "cross", ec="#777")
    f(ROADS, "road", ec="#666", lw=0.5)
    f(PARK, "park", ec="none")
    f(PODIUM, "plaza", ec="#2a6ab0", lw=0.8, z=2)
    f(LAKE, "water", ec="#468", z=2)
    f(CASCADE, "water", ec="#468", z=2)
    for p in PATHS:
        ax.plot(*p.xy, color="#efe3c4", lw=4, zorder=2, solid_capstyle="round")
    for b in BLOCKS:
        f(b["court"], "court", ec="none")
        f(b["lane"], "lane", ec="#888", lw=0.3)
        for p in b["plots"]:
            f(p, "villa" if b["kind"] == "V" else "house", ec="#6b4a1e", lw=0.35)
        for fp in b["fps"]:
            f(fp, None, ec="#3a2a10", lw=0.35)
    for p in ARC:
        f(p, "house", ec="#6b4a1e", lw=0.35)
    for fp in ARC_FPS:
        f(fp, None, ec="#3a2a10", lw=0.35)
    f(T_DROP, "road", ec="#666", lw=0.4, z=2)
    for r in RAMPS:
        f(r, "parking", ec="#555", lw=0.4, z=3)
    f(GUARD, "parking", ec="#333", z=3)
    f(GUARD_ISL, "parking", ec="#333", z=3)
    for g in list(PUB.values()) + list(SERV.values()):
        f(g, "serv", ec="#7a0000", lw=0.6)
    for g in list(PUB_PARK.values()) + [HEART_PARK]:
        f(g, "parking", ec="#666", lw=0.5)
    for g in UTIL_ITEMS.values():
        f(g, "util", ec="#6a4a8a", lw=0.6)
    for tw in TOWERS:
        f(tw, "tower", ec="#0c2c5a", lw=1.0, z=5)
    f(SITE, None, ec="#c00", lw=2.2, z=6)
    for tr in TREES:
        ax.add_patch(plt.Circle(tr, 4, fc="#2f7a2f", ec="#1f4f1f", lw=0.4, zorder=7))

    # --- labels on every part (name + area) ---
    for b in BLOCKS:
        cc = b["court"].representative_point()
        kind = "villas 400 m²" if b["kind"] == "V" else "houses 240 m²"
        kind_ar = "فيلا" if b["kind"] == "V" else "دار"
        lab(f"{b['name']}\n{len(b['plots'])} {kind}\n{len(b['plots'])} {kind_ar}\ngreen {b['court'].area:,.0f} m²",
            (cc.x, cc.y), 10.5, rot=90)
    lab(f"{len(ARC)} HOUSES 240 m² ROUND THE PARK\n{len(ARC)} دار 240 م² حول الحديقة", (HC[0], 12), 13,
        bg="#ffe2cc")
    for tw, nm in zip(TOWERS, TOWER_NAMES):
        lab(f"TOWER {nm}\nG+19\n80 flats", tw.centroid.coords[0], 11, color="white", bg=None, z=21)
    lab(f"SHALLALAT CENTRAL PARK - حديقة الشلالات\n{PARK.area - PODIUM.area:,.0f} m²", (HC[0], HC[1] + 4), 12, bg="#e6f5d6")
    lab(f"TOWER PLAZA over basement (2 levels, {PARK_CARS} cars)\nبلازا الأبراج فوق سرداب {PARK_CARS} سيارة - {PODIUM.area:,.0f} m²",
        (HC[0], HC[1] - 42), 9.5, bg="#dff0fb")
    lab("LAKE + CASCADES - البحيرة والشلالات", (HC[0], HC[1] - 63), 9, bg="#dff0fb")
    for k, g in {**PUB, **SERV, **UTIL_ITEMS, **PUB_PARK}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        small = g.area < 1100
        lab(f"{n1}\n{n2}\n{g.area:,.0f} m²", (q.x, q.y), 9 if small else 11.5, bg="#ffe9e9" if k not in PUB_PARK else "white")
    q = HEART_PARK.representative_point()
    lab(f"PARKING - موقف\n{HEART_PARK.area:,.0f} m²", (q.x, q.y), 9)
    q = ORCHARD.representative_point()
    lab(f"ORCHARD PARK - حديقة البستان\n{ORCHARD.area:,.0f} m²", (q.x, q.y), 12, bg="#e6f5d6")
    for g in GARDENS:
        if g.area > 1500:
            q = g.representative_point()
            lab(f"GARDEN - حديقة\n{g.area:,.0f} m²", (q.x, q.y), 10, bg="#e6f5d6")
    lab("SPINE 16 m - المحور", FR["W"].p(FR["W"].L * 0.5, 0), 10, rot=-6, bg="#eeeeee")
    lab("SPINE 16 m - المحور", FR["E"].p(FR["E"].L * 0.45, 0), 10, rot=-6, bg="#eeeeee")
    lab("RING ROAD 14 m\nالطريق الحلقي", (HC[0] - RING_A * 0.72, HC[1] + RING_B * 0.72), 9, rot=40, bg="#eeeeee")
    lab("CROSS ROAD (PUBLIC)\nالشارع العرضي العام", tuple(np.add(CROSS_A, cross_dir * 150)), 10, rot=84, bg="#eeeeee")
    lab("NORTH ROAD - الشارع الشمالي", (650, north_v(650) + 14), 12, rot=-10, bg=None, color="#444")
    lab("SOUTH ROAD - الشارع الجنوبي", (560, -16), 12, bg=None, color="#444")

    # --- gates: big red arrows + boxes ---
    gx, gy = HC[0], GV
    ax.add_patch(FancyArrow(gx, gy + 40, 0, -36, width=7, head_width=18, head_length=12, fc="#d00000", ec="#600", zorder=30,
                            length_includes_head=True))
    ax.plot(*GATE_LINE.xy, color="#d00000", lw=5, zorder=30)
    lab("MAIN GATE\nالبوابة الرئيسية", (gx, gy + 56), 18, color="white", bg="#d00000", z=31)
    ux, uy = U_GATE.centroid.coords[0]
    ax.add_patch(FancyArrow(ux, -40, 0, 36, width=6, head_width=15, head_length=10, fc="#d00000", ec="#600", zorder=30,
                            length_includes_head=True))
    ax.plot(*U_GATE.xy, color="#d00000", lw=5, zorder=30)
    lab("SERVICE / EMERGENCY GATE\nبوابة الخدمة والطوارئ", (ux - 75, -30), 14, color="white", bg="#d00000", z=31)

    # north arrow + scale
    na = np.array([-50.0, 330.0])
    gn = np.array([U[1], V[1]])
    side_v = np.array([-gn[1], gn[0]])
    ax.add_patch(MPoly([tuple(na - gn * 12 + side_v * 9), tuple(na + gn * 30), tuple(na - gn * 12 - side_v * 9)], closed=True, fc="k", zorder=12))
    ax.text(*(na + gn * 44), "N", fontsize=22, fontweight="bold", ha="center", va="center")
    for i in range(5):
        ax.add_patch(plt.Rectangle((620 + i * 20, 330), 20, 5, fc="k" if i % 2 == 0 else "w", ec="k", lw=0.8))
        ax.text(620 + i * 20, 324, f"{i * 20}", fontsize=11, ha="center", va="top")
    ax.text(722, 324, "100 m", fontsize=11, ha="left", va="top")
    ax.set_xlim(-80, 900)
    ax.set_ylim(-48, 345)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.5, 0.968, "المخطط العام - المقترح و: الأبراج في القلب (تعديل 1)   |   MASTER PLAN - PROPOSAL F: TOWERS IN THE HEART - REV 1",
             ha="center", fontsize=30, fontweight="bold")
    fig.text(0.5, 0.945, "مجمع الشلالات السكني - القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026", ha="center", fontsize=18)

    # --- counts box ---
    cb = fig.add_axes([0.015, 0.025, 0.22, 0.26])
    cb.axis("off")
    cb.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.0,rounding_size=0.03", fc="#fff8e6", ec="#333",
                                lw=2.5, transform=cb.transAxes))
    cb.text(0.5, 0.92, "الوحدات السكنية - HOUSING UNITS", ha="center", va="center", fontsize=20, fontweight="bold",
            transform=cb.transAxes)
    rows = [("villa", "فلل 400 م² - Villas", N_V), ("house", "دور 240 م² - Houses", N_H),
            ("tower", "شقق (3 أبراج × 20 طابق × 4) - Flats", N_APTS)]
    for i, (k, t, n) in enumerate(rows):
        y = 0.74 - i * 0.17
        cb.add_patch(plt.Rectangle((0.05, y - 0.055), 0.09, 0.11, fc=rgb[k], ec="#333", transform=cb.transAxes))
        cb.text(0.17, y, t, fontsize=16, va="center", fontweight="bold", transform=cb.transAxes)
        cb.text(0.95, y, f"{n}", fontsize=24, va="center", ha="right", fontweight="bold", transform=cb.transAxes)
    cb.plot([0.05, 0.95], [0.17, 0.17], color="#333", lw=2, transform=cb.transAxes)
    cb.text(0.17, 0.09, "المجموع - TOTAL UNITS", fontsize=19, va="center", fontweight="bold", transform=cb.transAxes)
    cb.text(0.95, 0.09, f"{N_UNITS}", fontsize=30, va="center", ha="right", fontweight="bold", color="#c00000",
            transform=cb.transAxes)

    # --- legend with % of each land use ---
    LG = [
        ("villa", "Villa plots 400 m²", "قطع الفلل", LANDUSE[0][1]),
        ("house", "House plots 240 m²", "قطع الدور", LANDUSE[1][1]),
        ("plaza", "Tower plaza + 3 towers", "الأبراج والبلازا", LANDUSE[2][1]),
        ("serv", "Public services", "الخدمات العامة", LANDUSE[3][1]),
        ("util", "Utilities (water, waste)", "المرافق الفنية", LANDUSE[4][1]),
        ("road", "Ring, spine, gates, parking", "الطرق والمواقف", LANDUSE[5][1]),
        ("lane", "Court lanes 7 m", "أزقة البلوكات", LANDUSE[6][1]),
        ("cross", "Cross road (public)", "الشارع العرضي", LANDUSE[7][1]),
        ("park", "Green: park, courts, gardens", "المساحات الخضراء", LANDUSE[8][1]),
    ]
    lg = fig.add_axes([0.25, 0.025, 0.47, 0.26])
    lg.axis("off")
    lg.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.0,rounding_size=0.03", fc="white", ec="#333", lw=2.5,
                                transform=lg.transAxes))
    lg.text(0.5, 0.94, "مفتاح الألوان واستعمالات الأرض - LEGEND + LAND USE", ha="center", va="center", fontsize=19,
            fontweight="bold", transform=lg.transAxes)
    hy = 0.855
    for x, t, ha in ((0.10, "USE", "left"), (0.66, "m²", "right"), (0.76, "%", "right"), (0.97, "الاستعمال", "right")):
        lg.text(x, hy, t, fontsize=14, fontweight="bold", ha=ha, va="center", transform=lg.transAxes)
    for i, (k, en, a_r, area) in enumerate(LG + [(None, "TOTAL", "المجموع", SITE.area)]):
        y = 0.78 - i * 0.075
        if k:
            lg.add_patch(plt.Rectangle((0.02, y - 0.028), 0.06, 0.056, fc=rgb[k], ec="#333", transform=lg.transAxes))
        wt = "bold"
        lg.text(0.10, y, en, fontsize=14, va="center", fontweight=wt, transform=lg.transAxes)
        lg.text(0.66, y, f"{area:,.0f}", fontsize=14, va="center", ha="right", fontweight=wt, transform=lg.transAxes)
        lg.text(0.76, y, f"{area / SITE.area * 100:.1f}%", fontsize=15, va="center", ha="right", fontweight="bold",
                color="#c00000" if k else "#111", transform=lg.transAxes)
        lg.text(0.97, y, a_r, fontsize=14, va="center", ha="right", fontweight=wt, transform=lg.transAxes)

    # --- key for symbols + facts ---
    kb = fig.add_axes([0.735, 0.025, 0.25, 0.26])
    kb.axis("off")
    kb.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.0,rounding_size=0.03", fc="white", ec="#333", lw=2.5,
                                transform=kb.transAxes))
    kb.text(0.5, 0.92, "رموز ومعلومات - KEY", ha="center", va="center", fontsize=19, fontweight="bold", transform=kb.transAxes)
    keys = [
        ("tower", "Tower G+19 (80 flats each) - برج"),
        ("court", "Green court of each block - ساحة خضراء"),
        ("water", "Lake + cascades - بحيرة وشلالات"),
        ("parking", "Parking / basement ramp - موقف"),
    ]
    for i, (k, t) in enumerate(keys):
        y = 0.78 - i * 0.1
        kb.add_patch(plt.Rectangle((0.04, y - 0.035), 0.08, 0.07, fc=rgb[k], ec="#333", transform=kb.transAxes))
        kb.text(0.15, y, t, fontsize=13.5, va="center", fontweight="bold", transform=kb.transAxes)
    y = 0.78 - 4 * 0.1
    kb.plot([0.04, 0.12], [y, y], color="#d00000", lw=6, transform=kb.transAxes)
    kb.text(0.15, y, "Gate - بوابة", fontsize=13.5, va="center", fontweight="bold", transform=kb.transAxes)
    facts = [
        "Entrances: 1 main gate + 1 service gate only",
        "المداخل: بوابة رئيسية واحدة + بوابة خدمة",
        f"Green {LANDUSE[8][1] / SITE.area * 100:.1f}%  -  Roads {ROADS_M2 / SITE.area * 100:.1f}%",
        f"Site area {SITE.area:,.0f} m² - مساحة الموقع",
    ]
    for i, t in enumerate(facts):
        kb.text(0.04, 0.27 - i * 0.07, t, fontsize=13.5, va="center", fontweight="bold", transform=kb.transAxes)
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    base = os.path.join(out_dir, BASE)
    write_dxf(base + ".dxf")
    write_preview(base + "_preview.png", base + "_preview.pdf")
    print("\n".join(table_rows()))
