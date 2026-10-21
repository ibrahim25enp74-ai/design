"""Writes Ibrahim's proposal, developed: DXF on the site coordinates + A1 preview.

Usage: python make_masterplan_user.py [out_dir]
"""
import math
import os
import sys

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment

from layout_user import *  # noqa: F401,F403  (geometry of the layout)

ROT = math.degrees(math.atan2(U[1], U[0]))

NAMES = {
    "MALL": ("MALL", "المول"), "MOSQUE": ("MOSQUE", "الجامع"),
    "POLICE_CD": ("POLICE + CIVIL DEFENCE", "الشرطة والدفاع المدني"), "HEALTH": ("HEALTH CENTRE", "المركز الصحي"),
    "SECONDARY": ("SECONDARY SCHOOL", "الثانوية (متوسطة + إعدادية)"), "PRIMARY": ("PRIMARY SCHOOL", "المدرسة الابتدائية"),
    "KG": ("KINDERGARTEN", "الروضة"), "WATER": ("WATER STATION", "محطة الماء"), "POWER": ("POWER STATION", "محطة الكهرباء"),
    "WASTE": ("WASTE", "النفايات"), "CLUB": ("SOCIAL CLUB + SPORTS", "النادي والملاعب"),
    "PARK_MALL": ("PARKING", "موقف السيارات"), "G_HEALTH": ("GARDEN", "حديقة"), "G_SEC": ("GARDEN", "حديقة"),
    "G_KG": ("GARDEN", "حديقة"),
}
UTIL_KEYS = ("WATER", "POWER", "WASTE")


def table_rows():
    units = len(VILLAS) + len(HOUSES) + N_APTS
    rows = [
        "IBRAHIM'S PROPOSAL - DEVELOPED - مقترح ابراهيم المطور",
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
    return rows


LAYERS = {
    "MP_BOUNDARY": (1, 50), "MP_BOUNDARY_COORDS": (6, 18), "MP_GATES": (1, 50), "MP_ROADS": (8, 25),
    "MP_PLOT_VILLA": (30, 18), "MP_PLOT_HOUSE": (40, 18), "MP_TOWERS": (5, 50), "MP_PLAZA": (4, 18),
    "MP_SERVICES": (1, 25), "MP_UTILITIES": (6, 25), "MP_PARKING": (9, 13), "MP_GREEN": (3, 13),
    "MP_TEXT": (7, 18), "MP_TEXT_PLOTNO": (8, 9), "MP_TABLE": (7, 18), "MP_NORTH": (7, 25),
    "MP_HATCH_RES": (31, 0), "MP_HATCH_SERV": (1, 0), "MP_HATCH_GREEN": (3, 0), "MP_HATCH_ROAD": (252, 0),
    "MP_HATCH_TOWER": (5, 0),
}
# the architect's own colours
FILL = {
    "villa": (254, 204, 102), "house": (242, 103, 34), "serv": (237, 31, 36), "util": (209, 156, 199),
    "green": (19, 103, 52), "park": (120, 186, 110), "plaza": (173, 221, 247), "tower": (39, 118, 187),
    "road": (225, 225, 225), "parking": (190, 190, 190),
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

    def text(s, at, h=3.0, rot=0.0, layer="MP_TEXT"):
        t = msp.add_text(s, height=h, rotation=rot + ROT, dxfattribs={"layer": layer, "style": "AR"})
        t.set_placement(utm(at), align=TextEntityAlignment.MIDDLE_CENTER)

    hatch(ROADS, "MP_HATCH_ROAD", FILL["road"])
    for p in VILLAS:
        hatch(p, "MP_HATCH_RES", FILL["villa"])
    for p in HOUSES:
        hatch(p, "MP_HATCH_RES", FILL["house"])
    for g in STRIPS + [ROUNDABOUT_ISLAND]:
        hatch(g, "MP_HATCH_GREEN", FILL["green"])
    for g in [BIG_PARK, OPEN["G_HEALTH"], OPEN["G_SEC"], OPEN["G_KG"]]:
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
    msp.add_circle(utm(RB_C), RB_R, dxfattribs={"layer": "MP_ROADS"})
    for p in VILLAS:
        outline(p, "MP_PLOT_VILLA")
    for p in HOUSES:
        outline(p, "MP_PLOT_HOUSE")
    for t in TOWERS:
        outline(t, "MP_TOWERS")
    outline(PLAZA, "MP_PLAZA")
    for g in STRIPS + [ROUNDABOUT_ISLAND, BIG_PARK, OPEN["G_HEALTH"], OPEN["G_SEC"], OPEN["G_KG"]]:
        outline(g, "MP_GREEN")
    outline(OPEN["PARK_MALL"], "MP_PARKING")
    for k, g in SERV.items():
        outline(g, "MP_UTILITIES" if k in UTIL_KEYS else "MP_SERVICES")
    msp.add_lwpolyline([utm(q) for q in GATE.coords], dxfattribs={"layer": "MP_GATES"})
    msp.add_lwpolyline([utm(q) for q in SGATE.coords], dxfattribs={"layer": "MP_GATES"})

    for i, p in enumerate(VILLAS):
        text(f"V{i + 1:02d}", tuple(p.centroid.coords[0]), 1.6, layer="MP_TEXT_PLOTNO")
    for i, p in enumerate(HOUSES):
        text(f"H{i + 1:02d}", tuple(p.centroid.coords[0]), 1.4, layer="MP_TEXT_PLOTNO")
    for k, g in {**SERV, **OPEN}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        text(n1, (q.x, q.y + 2.5), 3 if g.area > 900 else 1.8)
        text(f"{n2}  {g.area:,.0f} m2", (q.x, q.y - 2.5), 2.2 if g.area > 900 else 1.4)
    q = BIG_PARK.representative_point()
    text("CENTRAL PARK", (q.x, q.y + 4), 5)
    text(f"الحديقة الكبرى  {BIG_PARK.area:,.0f} m2", (q.x, q.y - 4), 3.5)
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

    def f(g, key, ec="#555", lw=0.3, z=1):
        for p in polys(g):
            ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=rgb[key] if key else "none", ec=ec, lw=lw, zorder=z))
            for h in p.interiors:
                ax.add_patch(MPoly(list(h.coords), closed=True, fc="none", ec=ec, lw=lw, zorder=z))

    def t(s, at, size=6, ar_s=None, w="normal", color="#111", z=10, rot=0):
        ax.text(at[0], at[1], s if ar_s is None else f"{ar_s}\n{s}", fontsize=size, ha="center", va="center",
                fontweight=w, color=color, zorder=z, linespacing=1.1, rotation=rot,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75) if ar_s else None)

    f(ROADS, "road", ec="#888", lw=0.4)
    for p in VILLAS:
        f(p, "villa", ec="#8a6a40", lw=0.3)
    for p in HOUSES:
        f(p, "house", ec="#7a3a10", lw=0.3)
    for g in STRIPS + [ROUNDABOUT_ISLAND]:
        f(g, "green", ec="none")
    for g in [BIG_PARK, OPEN["G_HEALTH"], OPEN["G_SEC"], OPEN["G_KG"]]:
        f(g, "park", ec="#3a6a2a", lw=0.4)
    f(OPEN["PARK_MALL"], "parking", ec="#555", lw=0.4)
    f(PLAZA, "plaza", ec="#468", lw=0.5)
    for tw in TOWERS:
        f(tw, "tower", ec="#123", lw=0.8, z=3)
    for k, g in SERV.items():
        f(g, "util" if k in UTIL_KEYS else "serv", ec="#333", lw=0.6, z=2)
    f(SITE, None, ec="#c00", lw=1.6, z=6)
    ax.add_patch(plt.Circle(RB_C, RB_R, fc="none", ec="#888", lw=0.5, ls="--", zorder=2))
    for g in (GATE, SGATE):
        ax.plot(*g.xy, color="#d00", lw=5, zorder=7, solid_capstyle="butt")

    for k, g in {**SERV, **OPEN}.items():
        q = g.representative_point()
        n1, n2 = NAMES[k]
        t(f"{n1}\n{g.area:,.0f} m²", (q.x, q.y), 7 if g.area > 900 else 5.5, ar_s=n2)
    q = BIG_PARK.representative_point()
    t(f"CENTRAL PARK\n{BIG_PARK.area:,.0f} m²", (q.x, q.y + 30), 9, ar_s="الحديقة الكبرى", w="bold")
    for i, tw in enumerate(TOWERS):
        t(f"{'ABC'[i]}\nG+{FLOORS - 1}", tw.centroid.coords[0], 7, color="white", w="bold", z=11)
    q = PLAZA.representative_point()
    t("PLAZA", (PLAZA.bounds[2] - 10, PLAZA.bounds[3] - 10), 6, ar_s="البلازا")
    t("MAIN GATE", (GATE_U, north_v(GATE_U) + 10), 9, ar_s="البوابة الرئيسية", w="bold", color="#b00")
    t("SERVICE / EMERGENCY GATE", (SGATE_U, -10), 8, ar_s="بوابة الخدمة والطوارئ", w="bold", color="#b00")
    t(f"{len(VILLAS)} VILLAS 400 m²", (243, north_v(243) + 8), 9, ar_s="فلل 400 متر", w="bold")
    t(f"{len(HOUSES)} HOUSES 240 m²", (655, north_v(655) + 8), 9, ar_s="دور 240 متر", w="bold")

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

    fig.text(0.5, 0.965, "المخطط العام - مقترح ابراهيم المطوّر   |   MASTER PLAN - IBRAHIM'S PROPOSAL, DEVELOPED",
             ha="center", fontsize=26, fontweight="bold")
    fig.text(0.5, 0.945, "مجمع الشلالات السكني - القطعة 157 م53 بايبوخت - فرصة هيئة استثمار نينوى 5/2026", ha="center", fontsize=15)
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
        ("tower", f"Tower G+{FLOORS - 1}", "الأبراج"), ("plaza", "Plaza over the basement car park", "البلازا فوق موقف السرداب"),
        ("serv", "Community services", "الخدمات"), ("util", "Utilities", "المرافق الفنية"),
        ("green", "Green strips", "الأشرطة الخضراء"), ("park", "Parks + gardens", "الحدائق"),
        ("parking", "Parking", "موقف سيارات"), ("road", "Roads", "الشوارع"),
    ]
    lg = fig.add_axes([0.50, 0.02, 0.22, 0.26])
    lg.axis("off")
    for i, (k, en, a) in enumerate(key):
        y = 1 - i * 0.085
        lg.add_patch(plt.Rectangle((0, y - 0.055), 0.08, 0.055, fc=rgb[k], ec="#555", transform=lg.transAxes))
        lg.text(0.11, y - 0.027, f"{en}  -  {a}", fontsize=10.5, va="center", transform=lg.transAxes)
    yg = 1 - len(key) * 0.085 - 0.027
    lg.plot([0, 0.08], [yg] * 2, color="#d00", lw=3, transform=lg.transAxes)
    lg.text(0.11, yg, "Gate  -  بوابة", fontsize=10.5, va="center", transform=lg.transAxes)
    nt = fig.add_axes([0.74, 0.02, 0.24, 0.26])
    nt.axis("off")
    notes = [
        "تقسيم ابراهيم محفوظ كما رسمه: صفوف الفلل والدور، الأشرطة الخضراء،",
        "المحور الوسطي والدوار، الشارع المحيط، والأبراج على البلازا.",
        "الخدمات بالمساحات التي حددها: مول 3000، صحي 1000، شرطة ودفاع 600،",
        "ابتدائية 3000، ثانوية 5000، ماء 1000، كهرباء 1000.",
        "أضيف: روضة 1500، جامع 2000، نادي وملاعب 5000، نفايات 300،",
        f"وموقف سرداب تحت البلازا لـ {PARK_NEED} سيارة (1.5 لكل شقة).",
        "المول والجامع والصحي والشرطة قرب البوابة الرئيسية،",
        "والمدارس والروضة في الداخل جنوب المحور.",
        "الماء والكهرباء والنفايات على الشارع الجنوبي عند بوابة الخدمة.",
        "المساحة الزائدة صارت الحديقة الكبرى وحدائق داخل البلوكات.",
        "مدخلان فقط، كلاهما على الشارعين الطويلين.",
        "",
        "Layers MP_*; colours follow the architect's sketch.",
    ]
    for i, n in enumerate(notes):
        nt.text(1, 1 - i * 0.07, n, fontsize=11, ha="right", va="top", transform=nt.transAxes)
    fig.savefig(png, dpi=110)
    fig.savefig(pdf)


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
    base = os.path.join(out_dir, "SHALLALAT_MASTERPLAN_IBRAHIM_DEVELOPED")
    write_dxf(base + ".dxf")
    write_preview(base + "_preview.png", base + "_preview.pdf")
    print("\n".join(table_rows()))
