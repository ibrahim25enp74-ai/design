"""Writes proposal F "towers in the heart" (الأبراج في القلب): DXF on the site coordinates + A1 preview.

Usage: python make_masterplan_F.py [out_dir]
"""
import math
import os
import sys

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString
from shapely.ops import unary_union

from layout_F import *  # noqa: F401,F403  (geometry of the layout)

HERE = os.path.dirname(os.path.abspath(__file__))
ROT = math.degrees(math.atan2(U[1], U[0]))


# --- indicative footprints -----------------------------------------------------------------------
def footprint(b, spec):
    ta, tb, na, nb, front = spec
    if b["kind"] == "V":   # 160 m2 ground floor (40 %), 4 m front setback, 3 m side yards
        sb, dep, side = 4.0, 16.0, 3.0
    else:                  # 120 m2 (60 %), 2.5 m front setback, attached on both sides
        sb, dep, side = 2.5, 12.0, 0.0
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

NAMES = {
    "PRIMARY": ("PRIMARY SCHOOL", "مدرسة ابتدائية"), "SUBSTATION": ("33/11 kV SUBSTATION", "محطة كهرباء"),
    "INT_SCHOOL": ("INTERMEDIATE SCHOOL", "مدرسة متوسطة"), "SEC_SCHOOL": ("SECONDARY SCHOOL", "مدرسة إعدادية"),
    "HEALTH": ("HEALTH CENTRE", "مركز صحي"), "SPORTS": ("SPORTS GROUND", "ملعب رياضي"),
    "POLICE": ("POLICE", "مركز شرطة"), "CIVIL_DEF": ("CIVIL DEFENCE", "دفاع مدني"),
    "MOSQUE": ("FRIDAY MOSQUE + PARKING", "الجامع وموقفه"), "SOUQ": ("SOUQ + CAFES", "السوق والمقاهي"),
    "KG": ("KINDERGARTEN + NURSERY", "روضة وحضانة"), "CLUB": ("SOCIAL CLUB + ADMIN", "النادي الاجتماعي والإدارة"),
    "DESAL": ("DESALINATION + TANK", "محطة تحلية وخزان"), "SEWAGE": ("SEWAGE + WASTE", "معالجة ونفايات"),
    "GATE": ("MAIN GATE (ONLY ENTRANCE)", "البوابة الرئيسية - المدخل الوحيد"),
    "SPINE_W": ("SPINE 16 m", "المحور الأخضر"), "SPINE_E": ("SPINE 16 m", "المحور الأخضر"),
    "RING": ("RING ROAD 14 m", "الطريق الحلقي"),
    "PARK": ("SHALLALAT CENTRAL PARK", "حديقة الشلالات المركزية"),
    "LAKE": ("LAKE + CASCADES", "البحيرة والشلالات"),
    "CROSS": ("CROSS ROAD - STAYS PUBLIC", "الشارع العرضي يبقى عاما"),
    "PUBLIC": ("PUBLIC FRONT", "الواجهة العامة"),
    "UGATE": ("SERVICE / EMERGENCY GATE", "بوابة خدمة وطوارئ"),
    "ORCHARD": ("ORCHARD PARK", "حديقة البستان"),
}
LABELS = {
    "GATE": (HC[0], GV + 14),
    "SPINE_W": FR["W"].p(FR["W"].L * 0.08, 0),
    "SPINE_E": FR["E"].p(FR["E"].L * 0.55, 0),
    "PARK": (HC[0], HC[1] - 9),
    "LAKE": (HC[0], HC[1] - 40),
    "CROSS": tuple(np.add(CROSS_A, cross_dir * 60)),
    "PUBLIC": (40, 330),
    "UGATE": (U_GATE.coords[0][0] + 6, -12),
    "ORCHARD": tuple(ORCHARD.representative_point().coords[0]),
}


def table_rows():
    units = len(VILLAS) + len(HOUSES) + N_APTS
    rows = [
        "PROPOSAL F - TOWERS IN THE HEART - المقترح و: الأبراج في القلب",
        "Plot 157 / District 53 Baybokht - NIC 5/2026 - UTM 38S",
        "",
        f"UNITS: {len(VILLAS)} villas 400 m2 + {len(HOUSES)} houses 200 m2 + {N_APTS} flats = {units}",
        f"Court blocks: {len(BLOCKS)}, every house fronts a green court (court greens {total(COURTS):,.0f} m2)",
        "Entrances: 1 main gate (north road, tower axis) + 1 service/emergency gate",
        f"Towers: 2 x (G+19) in the central park, 800 m2 plate, clear gap {TOWER_GAP:.1f} m",
        "",
        "LAND USE - استعمالات الأرض              m2        %",
    ]
    for n, a in LANDUSE:
        rows.append(f"{n:<52s}{a:>9,.0f}  {a / SITE.area * 100:5.1f}")
    rows.append(f"{'TOTAL':<52s}{SITE.area:>9,.0f}  100.0")
    return rows


# --- DXF --------------------------------------------------------------------------------------------
LAYERS = {
    "MP_BOUNDARY": (1, 50), "MP_BOUNDARY_COORDS": (6, 18), "MP_FENCE": (8, 35), "MP_GATES": (1, 50),
    "MP_ROADS": (8, 25), "MP_ROAD_CL": (8, 13), "MP_LANES": (8, 18), "MP_PARKING": (9, 13),
    "MP_PLOT_VILLA": (30, 18), "MP_PLOT_HOUSE": (40, 18), "MP_FOOTPRINT": (7, 25), "MP_TOWERS": (1, 50),
    "MP_PODIUM": (1, 13), "MP_SERVICES": (200, 25), "MP_SERVICES_HEART": (210, 25), "MP_UTILITIES": (8, 25),
    "MP_GREEN_COURT": (3, 13), "MP_GREEN_PARK": (94, 13), "MP_WATER": (5, 18), "MP_TREES": (3, 13),
    "MP_CONTEXT": (8, 13), "MP_TEXT": (7, 18), "MP_TEXT_PLOTNO": (8, 9), "MP_TABLE": (7, 18), "MP_NORTH": (7, 25),
    "MP_HATCH_RES": (31, 0), "MP_HATCH_SERV": (211, 0), "MP_HATCH_GREEN": (93, 0), "MP_HATCH_ROAD": (252, 0),
    "MP_HATCH_WATER": (151, 0), "MP_HATCH_TOWER": (11, 0),
}
FILL = {
    "villa": (244, 214, 160), "house": (238, 170, 120), "tower": (196, 96, 86), "pub": (190, 160, 220),
    "sc": (214, 176, 230), "util": (170, 170, 170), "court": (150, 205, 120), "park": (120, 186, 110),
    "garden": (196, 226, 172), "road": (205, 205, 205), "lane": (228, 228, 228), "water": (150, 200, 240),
    "fore": (215, 215, 215), "plaza": (236, 226, 204),
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

    # hatches
    hatch(R_IN, "MP_HATCH_GREEN", FILL["garden"])
    hatch(ORCHARD, "MP_HATCH_GREEN", FILL["park"])
    hatch(ROADS, "MP_HATCH_ROAD", FILL["road"])
    hatch(PARK, "MP_HATCH_GREEN", FILL["park"])
    hatch(T_PLAZA.union(PODIUM).intersection(PARK), "MP_HATCH_ROAD", FILL["plaza"])
    hatch(LAKE, "MP_HATCH_WATER", FILL["water"])
    hatch(CASCADE, "MP_HATCH_WATER", FILL["water"])
    for b in BLOCKS:
        hatch(b["court"], "MP_HATCH_GREEN", FILL["court"])
        hatch(b["lane"], "MP_HATCH_ROAD", FILL["lane"])
        for p in b["plots"]:
            hatch(p, "MP_HATCH_RES", FILL["villa" if b["kind"] == "V" else "house"])
    hatch(T_DROP, "MP_HATCH_ROAD", FILL["road"])
    hatch(CROSS_IN, "MP_HATCH_ROAD", FILL["road"])
    for g in PUB.values():
        hatch(g, "MP_HATCH_SERV", FILL["pub"])
    for g in SERV.values():
        hatch(g, "MP_HATCH_SERV", FILL["sc"])
    for g in UTIL_ITEMS.values():
        hatch(g, "MP_HATCH_SERV", FILL["util"])
    for t in TOWERS:
        hatch(t, "MP_HATCH_TOWER", FILL["tower"])

    # boundary, wall, roads
    outline(SITE, "MP_BOUNDARY")
    outline(SITE_RAW, "MP_BOUNDARY_COORDS")
    outline(REST.buffer(-0.5, join_style="mitre"), "MP_FENCE")
    outline(UTIL, "MP_FENCE")
    outline(ROADS, "MP_ROADS")
    outline(RING_INN, "MP_ROADS")
    for k, (a, b_) in SPINES.items():
        line(LineString([a, b_]), "MP_ROAD_CL")
    msp.add_ellipse(utm(HC), major_axis=tuple(np.append(U * RING_A, 0)), ratio=RING_B / RING_A, dxfattribs={"layer": "MP_ROAD_CL"})
    outline(CROSS_IN, "MP_ROADS")
    line(GATE_LINE, "MP_GATES")
    outline(GUARD, "MP_GATES")
    outline(GUARD_ISL, "MP_GATES")
    line(U_GATE, "MP_GATES")
    # heart
    outline(PARK, "MP_GREEN_PARK")
    for t in TOWERS:
        outline(t, "MP_TOWERS")
    outline(PODIUM, "MP_PODIUM")
    outline(T_PLAZA.intersection(PARK), "MP_GREEN_PARK")
    outline(T_DROP, "MP_ROADS")
    outline(LAKE, "MP_WATER")
    outline(CASCADE, "MP_WATER")
    for p in PATHS:
        line(p, "MP_GREEN_PARK")
    # blocks
    for b in BLOCKS:
        outline(b["lane"], "MP_LANES")
        outline(b["court"], "MP_GREEN_COURT")
        lay = "MP_PLOT_VILLA" if b["kind"] == "V" else "MP_PLOT_HOUSE"
        for p in b["plots"]:
            outline(p, lay)
        for fp in b["fps"]:
            outline(fp, "MP_FOOTPRINT")
    for g in PUB.values():
        outline(g, "MP_SERVICES")
    for g in SERV.values():
        outline(g, "MP_SERVICES_HEART")
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

    # labels
    for b in BLOCKS:
        kind = f"{len(b['plots'])} villas 400 m2 - فلل" if b["kind"] == "V" else f"{len(b['plots'])} houses 200 m2 - دور"
        cc = b["court"].representative_point()
        text(b["name"], (cc.x, cc.y + 4), 5, rot=90)
        text(kind, (cc.x + 4, cc.y), 2.2, rot=90)
        for j, p in enumerate(b["plots"]):
            q = p.centroid
            text(f"{b['name']}-{j + 1:02d}", (q.x, q.y), 1.2, layer="MP_TEXT_PLOTNO")
    for k, g in {**PUB, **SERV, **UTIL_ITEMS}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        text(n1, (q.x, q.y + 2.5), 3)
        text(f"{n2}  {g.area:,.0f} m2", (q.x, q.y - 2.5), 2.2)
    for k, at in LABELS.items():
        n1, n2 = NAMES[k]
        text(n1, (at[0], at[1] + 2.8), 3.4)
        text(n2, (at[0], at[1] - 2.8), 2.6)
    for t, nm in zip(TOWERS, ("TOWER A", "TOWER B")):
        text(nm, (t.centroid.x, t.centroid.y + 3), 3.5)
        text("G+19, 76 flats", (t.centroid.x, t.centroid.y - 3), 2.2)

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


# --- preview ----------------------------------------------------------------------------------------
def write_preview(png, pdf):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import Polygon as MPoly

    for fp in (os.path.join(HERE, "..", "fonts"), "/usr/share/fonts"):
        if os.path.isdir(fp):
            for f in font_manager.findSystemFonts(fp):
                if "Arabic" in f:
                    font_manager.fontManager.addfont(f)
    plt.rcParams["font.family"] = ["DejaVu Sans", "Noto Sans Arabic"]

    def ar(s):  # matplotlib >= 3.10 shapes and orders Arabic itself
        return s

    fig = plt.figure(figsize=(33.1, 23.4))  # A1
    ax = fig.add_axes([0.02, 0.30, 0.96, 0.64])
    rgb = {k: tuple(c / 255 for c in v) for k, v in FILL.items()}

    def f(g, key, ec="#555", lw=0.3, z=1):
        for p in polys(g):
            ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=rgb[key] if key else "none", ec=ec, lw=lw, zorder=z))
            for h in p.interiors:
                ax.add_patch(MPoly(list(h.coords), closed=True, fc="none", ec=ec, lw=lw, zorder=z))

    def t(s, at, size=6, ar_s=None, w="normal", color="#222", z=10, rot=0):
        ax.text(at[0], at[1], s if ar_s is None else f"{ar(ar_s)}\n{s}", fontsize=size, ha="center", va="center",
                fontweight=w, color=color, zorder=z, linespacing=1.1, rotation=rot)

    f(SITE, "garden", ec="none")
    f(ORCHARD, "park", ec="none")
    f(CROSS_IN, "road", ec="#777")
    f(ROADS, "road", ec="#666", lw=0.5)
    f(PARK, "park", ec="none")
    f(T_PLAZA.union(PODIUM).intersection(PARK), "plaza", ec="#999", lw=0.4, z=2)
    f(LAKE, "water", ec="#468", z=2)
    f(CASCADE, "water", ec="#468", z=2)
    for p in PATHS:
        ax.plot(*p.xy, color="#e8dcc0", lw=3, zorder=2, solid_capstyle="round")
    for b in BLOCKS:
        f(b["court"], "court", ec="none")
        f(b["lane"], "lane", ec="#888", lw=0.3)
        for p in b["plots"]:
            f(p, "villa" if b["kind"] == "V" else "house", ec="#8a6a40", lw=0.25)
        for fp in b["fps"]:
            f(fp, None, ec="#444", lw=0.35)
        cc = b["court"].representative_point()
        t(b["name"], (cc.x, cc.y), 7, w="bold", color="#2b5a1e", rot=90)
    f(T_DROP, "road", ec="#666", lw=0.4, z=2)
    f(GUARD, "util", ec="#333", z=3)
    f(GUARD_ISL, "util", ec="#333", z=3)
    ax.plot(*GATE_LINE.xy, color="#d00", lw=3, zorder=5)
    ax.plot(*U_GATE.xy, color="#d00", lw=3, zorder=5)
    for g in PUB.values():
        f(g, "pub", ec="#6a4a8a", lw=0.5)
    for g in SERV.values():
        f(g, "sc", ec="#6a4a8a", lw=0.5)
    for g in UTIL_ITEMS.values():
        f(g, "util", ec="#444", lw=0.5)
    f(PODIUM, None, ec="#a55", lw=0.5, z=4)
    for tw in TOWERS:
        f(tw, "tower", ec="#5a1e1e", lw=0.8, z=5)
    f(SITE, None, ec="#c00", lw=1.6, z=6)
    f(REST, None, ec="#333", lw=1.0, z=6)
    for tr in TREES:
        ax.add_patch(plt.Circle(tr, 4, fc="#3d8a3d", ec="#1f4f1f", lw=0.4, zorder=7))

    for k, g in {**PUB, **SERV, **UTIL_ITEMS}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        t(f"{n1}\n{g.area:,.0f} m²", (q.x, q.y), 6.5, ar_s=n2)
    for k, at in LABELS.items():
        n1, n2 = NAMES[k]
        t(n1, at, 7.5, ar_s=n2, w="bold")
    for tw, nm in zip(TOWERS, ("A", "B")):
        t(f"TOWER {nm}\nG+19", tw.centroid.coords[0], 6.5, color="white", w="bold", z=11)

    na = np.array([-45.0, 296.0])
    gn = np.array([U[1], V[1]])
    side_v = np.array([-gn[1], gn[0]])
    ax.add_patch(MPoly([tuple(na - gn * 12 + side_v * 9), tuple(na + gn * 30), tuple(na - gn * 12 - side_v * 9)], closed=True, fc="k", zorder=12))
    t("N", tuple(na + gn * 44), 14, w="bold")
    for i in range(5):
        ax.add_patch(plt.Rectangle((560 + i * 20, 300), 20, 4, fc="k" if i % 2 == 0 else "w", ec="k", lw=0.6))
        t(f"{i * 20}", (560 + i * 20, 296), 7)
    t("100 m", (660, 296), 7)
    ax.set_xlim(-80, 900)
    ax.set_ylim(-25, 360)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.5, 0.965, ar("المخطط العام - المقترح و: الأبراج في القلب") + "   |   MASTER PLAN - PROPOSAL F: TOWERS IN THE HEART",
             ha="center", fontsize=26, fontweight="bold")
    fig.text(0.5, 0.945, ar("مجمع الشلالات السكني - القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026"),
             ha="center", fontsize=15)
    rows = table_rows()
    tx = fig.add_axes([0.03, 0.02, 0.45, 0.26])
    tx.axis("off")
    head = [r for r in rows[:8] if r]
    head[0] = "PROPOSAL F - TOWERS IN THE HEART"
    tx.text(0, 1, "\n".join(head), family="DejaVu Sans Mono", fontsize=10.5, va="top", linespacing=1.5)
    y0 = 0.60
    tx.text(0, y0, "LAND USE", fontsize=10.5, fontweight="bold", va="top")
    tx.text(0.62, y0, "m²", fontsize=10.5, fontweight="bold", va="top", ha="right")
    tx.text(0.72, y0, "%", fontsize=10.5, fontweight="bold", va="top", ha="right")
    tx.text(1.0, y0, ar("استعمالات الأرض"), fontsize=10.5, fontweight="bold", va="top", ha="right")
    for i, (n, a) in enumerate(LANDUSE + [("TOTAL - المجموع", SITE.area)]):
        en, arb = n.split(" - ")
        y = y0 - 0.05 * (i + 1)
        tx.text(0, y, en, fontsize=10, va="top")
        tx.text(0.62, y, f"{a:,.0f}", fontsize=10, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(0.72, y, f"{a / SITE.area * 100:.1f}", fontsize=10, va="top", ha="right", family="DejaVu Sans Mono")
        tx.text(1.0, y, ar(arb), fontsize=10, va="top", ha="right")
    key = [
        ("villa", "Villa plot 400 m² (16 x 25)", "قطعة فيلا"), ("house", "Attached house 200 m² (10 x 20)", "دار متصلة"),
        ("tower", "Tower G+19 on a basement car park", "برج فوق موقف سرداب"), ("pub", "Public front services", "خدمات الواجهة العامة"),
        ("sc", "Heart services around the park", "خدمات القلب حول الحديقة"), ("util", "Utilities", "مرافق فنية"),
        ("court", "Green court of each block", "الساحة الخضراء للبلوك"), ("park", "Central park / orchard", "الحديقة المركزية والبستان"),
        ("garden", "Gardens, belts", "حدائق وأحزمة خضراء"), ("water", "Lake + cascades", "بحيرة وشلالات"),
        ("road", "Ring road, spine", "الطريق الحلقي والمحور"), ("lane", "Court lane 7 m (shared surface)", "زقاق البلوك"),
    ]
    lg = fig.add_axes([0.50, 0.02, 0.22, 0.26])
    lg.axis("off")
    for i, (k, en, a) in enumerate(key):
        y = 1 - i * 0.075
        lg.add_patch(plt.Rectangle((0, y - 0.05), 0.08, 0.05, fc=rgb[k], ec="#555", transform=lg.transAxes))
        lg.text(0.11, y - 0.025, f"{en}  -  {ar(a)}", fontsize=10.5, va="center", transform=lg.transAxes)
    lg.plot([0, 0.08], [1 - len(key) * 0.075 - 0.025] * 2, color="#d00", lw=2.5, transform=lg.transAxes)
    lg.text(0.11, 1 - len(key) * 0.075 - 0.025, "Gate  -  " + ar("بوابة"), fontsize=10.5, va="center", transform=lg.transAxes)
    nt = fig.add_axes([0.74, 0.02, 0.24, 0.26])
    nt.axis("off")
    notes = [
        "الفكرة: البرجان في قلب المشروع",
        "البرجان وسط حديقة الشلالات المركزية، تحيطها بحيرة وشلالات",
        "وطريق حلقي، وعلى زوايا الحلقة: الجامع، السوق، الروضة، النادي.",
        "مدخل رئيسي واحد على الشارع الشمالي على محور البرجين،",
        "وبوابة خدمة وطوارئ واحدة للمرافق. باقي المحيط سور وحزام أشجار.",
        "محور أخضر 16 م من الحلقة غربا وشرقا، تتفرع منه بلوكات سكنية:",
        "كل بلوك زقاق على شكل U يلتف حول ساحة خضراء، فكل بيت يطل على حديقة.",
        "الفلل في الجناح الغربي الأعرض، والدور المتصلة في الجناح الشرقي.",
        "غرب الشارع العرضي واجهة عامة: مدارس، شرطة، دفاع مدني، مركز صحي.",
        "الوادي المائي مهمل بطلب صاحب العمل (الأرض متصلة).",
        "",
        "Layers MP_*: plots, footprints, gates, hatches are separate.",
        "Outer roads, cross road, trees: approx. from the cadastral scan.",
    ]
    for i, n in enumerate(notes):
        nt.text(1, 1 - i * 0.07, n, fontsize=11, ha="right", va="top", transform=nt.transAxes)
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    base = os.path.join(out_dir, "SHALLALAT_MASTERPLAN_F")
    write_dxf(base + ".dxf")
    write_preview(base + "_preview.png", base + "_preview.pdf")
    print("\n".join(table_rows()))
