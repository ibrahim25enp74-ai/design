"""Write master plan proposal C (الوادي الأخضر) as DXF on top of the site plan, plus a PDF/PNG preview.

    python make_masterplan_C.py [site.dxf] [out_dir]

The site DXF (boundary, cadastral coordinates, grid, roads/watercourse traced from the scan) is
loaded as the base so the master plan sits on the same UTM 38S coordinates; every master plan
layer starts with MP-.
"""
import math
import os
import sys

import arabic_reshaper
import ezdxf
import matplotlib
import numpy as np
from bidi.algorithm import get_display
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString, MultiLineString, Polygon
from shapely.ops import unary_union

import layout_C as L

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_DXF = sys.argv[1] if len(sys.argv) > 1 else "/mnt/project-files/shallalat/site/SHALLALAT_SITE_PLAN.dxf"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out")
NAME = "SHALLALAT_MASTERPLAN_C_GREEN_VALLEY"
FONT_DIR = os.environ.get("AR_FONT_DIR", os.path.join(HERE, "fonts"))

# layer: (ACI colour, lineweight, hatch RGB or None, preview fill)
LAYERS = {
    "MP-BOUNDARY": (1, 50, None, None),
    "MP-ROAD-PUBLIC": (8, 25, (150, 150, 150), "#9a9a9a"),
    "MP-ROAD-LOOP": (8, 25, (190, 190, 190), "#bdbdbd"),
    "MP-ROAD-ENTRY": (8, 25, (175, 175, 175), "#adadad"),
    "MP-ROAD-LOCAL": (9, 18, (215, 215, 215), "#d9d9d9"),
    "MP-ROAD-CL": (8, 9, None, None),
    "MP-BRIDGE": (250, 25, (90, 90, 90), "#5a5a5a"),
    "MP-PARKING": (9, 13, (225, 225, 225), "#e4e4e4"),
    "MP-GATE": (1, 50, None, None),
    "MP-PLOT-VILLA": (30, 18, (246, 196, 120), "#f6c478"),
    "MP-PLOT-HOUSE": (50, 18, (249, 228, 160), "#f9e4a0"),
    "MP-BLDG-VILLA": (7, 25, (120, 90, 60), "#8a6a4a"),
    "MP-BLDG-HOUSE": (7, 25, (140, 110, 70), "#9a7a52"),
    "MP-TOWER-ZONE": (6, 18, (234, 214, 240), "#ead6f0"),
    "MP-TOWER": (6, 35, (120, 70, 150), "#784696"),
    "MP-TOWER-PODIUM": (6, 13, None, None),
    "MP-SERVICE-PUBLIC": (200, 18, (200, 160, 220), "#c8a0dc"),
    "MP-SERVICE-EDU": (240, 18, (240, 160, 160), "#f0a0a0"),
    "MP-SERVICE-COMM": (40, 18, (240, 176, 120), "#f0b078"),
    "MP-SERVICE-MOSQUE": (7, 25, (255, 255, 255), "#ffffff"),
    "MP-SERVICE-UTIL": (160, 18, (176, 176, 216), "#b0b0d8"),
    "MP-BLDG-SERVICE": (7, 25, None, None),
    "MP-PARK": (3, 13, (196, 232, 176), "#c4e8b0"),
    "MP-WADI-PARK": (3, 13, (150, 210, 160), "#96d2a0"),
    "MP-GREEN-BELT": (3, 13, (120, 190, 105), "#78be69"),
    "MP-GREEN-FINGER": (3, 13, (140, 205, 120), "#8ccd78"),
    "MP-GREEN-COURT": (3, 13, (180, 222, 165), "#b4dea5"),
    "MP-GREEN": (3, 13, (165, 215, 150), "#a5d796"),
    "MP-PLAZA": (42, 18, (233, 226, 208), "#e9e2d0"),
    "MP-WATER": (5, 18, (110, 180, 230), "#6eb4e6"),
    "MP-WATER-CHANNEL": (5, 25, None, None),
    "MP-PATH": (42, 9, (232, 217, 192), "#e8d9c0"),
    "MP-PATH-PARK": (42, 18, None, None),
    "MP-JOG": (1, 25, None, None),
    "MP-TREES-EXIST": (3, 18, None, None),
    "MP-TREES": (3, 13, None, None),
    "MP-TEXT": (7, 18, None, None),
    "MP-PLOT-NO": (8, 9, None, None),
    "MP-TABLE": (7, 18, None, None),
}
DRAW_ORDER = list(LAYERS)  # back to front for the preview
BACK = ["MP-TOWER-ZONE", "MP-PARK", "MP-WADI-PARK"]
LINE_STYLE = {"MP-ROAD-CL": ("#888888", 0.3, (0, (8, 4))), "MP-WATER-CHANNEL": ("#2f7fc0", 0.8, "-"),
              "MP-PATH-PARK": ("#b89a6a", 0.6, (0, (2, 2))), "MP-JOG": ("#d04040", 0.9, (0, (4, 2))),
              "MP-GATE": ("#d00000", 2.2, "-"), "MP-BOUNDARY": ("#d00000", 1.4, "-")}


# --- land use ---------------------------------------------------------------------------------------
CATS = [  # (name, layers) in precedence order
    ("فلل 400 م²", ["MP-PLOT-VILLA"]),
    ("دور 200 م²", ["MP-PLOT-HOUSE"]),
    ("منطقة البرجين", ["MP-TOWER-ZONE"]),
    ("الخدمات العامة والتعليمية والتجارية والبنى التحتية",
     ["MP-SERVICE-PUBLIC", "MP-SERVICE-EDU", "MP-SERVICE-COMM", "MP-SERVICE-MOSQUE", "MP-SERVICE-UTIL"]),
    ("الشوارع والمواقف والساحة", ["MP-ROAD-PUBLIC", "MP-ROAD-LOOP", "MP-ROAD-ENTRY", "MP-ROAD-LOCAL",
                                  "MP-BRIDGE", "MP-PARKING", "MP-PLAZA"]),
    ("الحدائق والمساحات الخضراء والممرات", ["MP-PARK", "MP-WADI-PARK", "MP-GREEN-BELT", "MP-GREEN-FINGER",
                                           "MP-GREEN-COURT", "MP-GREEN", "MP-PATH", "MP-WATER"]),
]


def land_use():
    taken = Polygon()
    rows = []
    for name, lays in CATS:
        g = unary_union([geom for lay, geom, _ in L.F if lay in lays and not isinstance(geom, (LineString, MultiLineString))])
        g = g.intersection(L.SITE).difference(taken)
        taken = taken.union(g)
        rows.append((name, g.area))
    rows.append(("فضلات وحواف", L.SITE.area - taken.area))
    return rows


# --- helpers ----------------------------------------------------------------------------------------
def polys(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


def lines(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "LineString"]


def utm(coords):
    return [L.to_utm(u, v) for u, v in coords]


def ar(s):
    """matplotlib >= 3.11 shapes and orders Arabic itself; older versions need reshape + bidi."""
    if tuple(int(x) for x in matplotlib.__version__.split(".")[:2]) >= (3, 11):
        return s
    return get_display(arabic_reshaper.reshape(s))


TEXT_ROT = L.ROT_DEG  # labels run along the plot's long axis
BIG = {"الحديقة المتصلة": 9, "حديقة الوادي": 6, "منطقة البرجين": 6, "ساحة الشلالات": 4.5,
       "الحلقة التجميعية 12 م": 3.5, "حزام أخضر ومسار جري": 3, "شارع الدخول 24 م": 3.5}
SKIP_LABEL = {"شجرة قائمة", "", None}


def label_points():
    out = []
    for lay, g, lab in L.F:
        if lab in SKIP_LABEL or lay in ("MP-PLOT-VILLA", "MP-PLOT-HOUSE"):
            continue
        if isinstance(g, (LineString, MultiLineString)):
            p = g.interpolate(0.5, normalized=True)
        else:
            big = max(polys(g), key=lambda q: q.area, default=None)
            if big is None:
                continue
            p = big.representative_point()
            if lab in ("الحديقة المتصلة",):
                p = big.intersection(L.rect(250, 0, 400, 400)).representative_point()
        out.append((lay, lab, p.x, p.y, BIG.get(lab, 3.2)))
    return out


EXTRA_NOTES = [  # (text, u, v, height)
    ("إصبع أخضر 20 م بقناة أمطار", 264, 150, 2.2),
    ("ممر أخضر 6 م خلف الحدائق", 210, 168, 2.0),
    ("زقاق مغلق 7 م ينتهي على الحديقة", 330, 70, 2.0),
    ("مجرى الحديقة يصب في الوادي", 580, 104, 2.4),
    ("الشارع الوحيد الذي يعبر الحديقة", 520, 120, 2.2),
    ("ستارة أشجار - البرجان لا يطلان على أي بيت", 165, 238, 2.2),
]


# --- DXF ----------------------------------------------------------------------------------------------
def write_dxf(path, table_rows, summary):
    doc = ezdxf.readfile(SITE_DXF)
    msp = doc.modelspace()
    if "AR" not in doc.styles:
        doc.styles.add("AR", font="arial.ttf")
    for name, (color, lw, _, _) in LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color, lineweight=lw)
    # the approximate traces under the plot are superseded by the design
    for name in ("TREES_APPROX",):
        if name in doc.layers:
            doc.layers.get(name).off()

    for lay, g, lab in L.F:
        for ln in lines(g):
            msp.add_lwpolyline(utm(ln.coords), dxfattribs={"layer": lay})
        for p in polys(g):
            ext = utm(p.exterior.coords)[:-1]
            msp.add_lwpolyline(ext, close=True, dxfattribs={"layer": lay})
            for hole in p.interiors:
                msp.add_lwpolyline(utm(hole.coords)[:-1], close=True, dxfattribs={"layer": lay})
            rgb = LAYERS[lay][2]
            if rgb is not None:
                hl = lay + "-HATCH"
                if hl not in doc.layers:
                    doc.layers.add(hl, color=LAYERS[lay][0], lineweight=0)
                h = msp.add_hatch(dxfattribs={"layer": hl})
                h.rgb = rgb
                h.transparency = 0.0
                h.paths.add_polyline_path(ext, is_closed=True, flags=1)
                for hole in p.interiors:
                    h.paths.add_polyline_path(utm(hole.coords)[:-1], is_closed=True, flags=16)
        if lay in ("MP-PLOT-VILLA", "MP-PLOT-HOUSE") and lab:
            c = g.centroid
            msp.add_text(lab, height=1.6 if lay == "MP-PLOT-HOUSE" else 2.0, rotation=TEXT_ROT,
                         dxfattribs={"layer": "MP-PLOT-NO", "style": "AR"}).set_placement(
                L.to_utm(c.x, c.y), align=TextEntityAlignment.MIDDLE_CENTER)
    # hatch layers draw behind outlines
    for lay, lab, x, y, h in label_points() + [("MP-TEXT", t, u, v, hh) for t, u, v, hh in EXTRA_NOTES]:
        msp.add_mtext(lab, dxfattribs={"layer": "MP-TEXT", "style": "AR", "char_height": h,
                                       "rotation": TEXT_ROT, "attachment_point": 5}).set_location(L.to_utm(x, y))
    # trees in the park (indicative): rows along the park paths and the belts
    for lay, g, _ in L.F:
        if lay == "MP-PATH-PARK":
            for d in np.arange(0, g.length, 14):
                p = g.interpolate(d)
                msp.add_circle(L.to_utm(p.x, p.y), 2.5, dxfattribs={"layer": "MP-TREES"})

    # title + land use table, east of the plot
    x0, y0 = 339960.0, 4035700.0
    rows = [f"{NAME}", "المقترح ج - الوادي الأخضر  |  مجمع الشلالات السكني - القطعة 157 م53 بايبوخت",
            "مخطط عام - مرحلة المقترحات - UTM 38S - المقياس 1:1000 على A1", ""]
    rows += summary + ["", "استعمالات الأرض:"]
    rows += [f"{n}:  {a:,.0f} م²  ({a / L.SITE.area * 100:.1f}%)" for n, a in table_rows]
    rows += [f"المجموع:  {L.SITE.area:,.0f} م²", "", "الخدمات (المرسوم / البرنامج م²):"]
    rows += [f"{k}:  {a:,.0f} / {p:,}" if p else f"{k}:  {a:,.0f}" for k, (a, p) in L.AREAS.items()]
    for i, r in enumerate(rows):
        msp.add_mtext(r, dxfattribs={"layer": "MP-TABLE", "style": "AR", "char_height": 6 if i == 0 else 4.2,
                                     "attachment_point": 1}).set_location((x0, y0 - i * 7.5))
    doc.saveas(path)


# --- preview ------------------------------------------------------------------------------------------
def preview(pdf, png, table_rows, summary):
    for f in ("NotoSansArabic-Regular.ttf", "NotoSansArabic-Bold.ttf"):
        fp = os.path.join(FONT_DIR, f)
        if os.path.exists(fp):
            font_manager.fontManager.addfont(fp)
    plt.rcParams["font.family"] = ["Noto Sans Arabic", "DejaVu Sans"]
    fig = plt.figure(figsize=(33.11, 23.39))  # A1 landscape
    ax = fig.add_axes([0.02, 0.17, 0.96, 0.78])
    order = {k: i for i, k in enumerate(BACK + [k for k in DRAW_ORDER if k not in BACK])}
    for lay, g, lab in sorted(L.F, key=lambda f: order.get(f[0], 99)):
        fill = LAYERS[lay][3]
        for p in polys(g):
            ax.add_patch(MplPolygon(utm(p.exterior.coords), closed=True, fc=fill or "none",
                                    ec="#333333" if lay != "MP-BOUNDARY" else "#d00000",
                                    lw=0.15 if lay not in ("MP-BOUNDARY",) else 1.6, zorder=order.get(lay, 99)))
        for ln in lines(g):
            c, w, ls = LINE_STYLE.get(lay, ("#555555", 0.5, "-"))
            xs, ys = zip(*utm(ln.coords))
            ax.plot(xs, ys, color=c, lw=w, ls=ls, zorder=200)
        if lay in ("MP-PLOT-VILLA", "MP-PLOT-HOUSE") and lab:
            x, y = L.to_utm(g.centroid.x, g.centroid.y)
            ax.text(x, y, lab, fontsize=3.2, ha="center", va="center", rotation=TEXT_ROT, zorder=210, color="#444")
    for lay, g, _ in L.F:  # indicative trees
        if lay == "MP-PATH-PARK":
            for d in np.arange(0, g.length, 14):
                p = g.interpolate(d)
                ax.add_patch(plt.Circle(L.to_utm(p.x, p.y), 2.5, fc="#5aa050", ec="#3d7a35", lw=0.3, zorder=150))
        if lay == "MP-TREES-EXIST":
            c = g.centroid
            ax.add_patch(plt.Circle(L.to_utm(c.x, c.y), 4, fc="#2e7d32", ec="k", lw=0.4, zorder=150))
    # cadastral boundary + outside roads for context
    ax.plot(*zip(*(list(L.Q.values()) + [L.Q["Q1"]])), color="#d00000", lw=1.6, zorder=220)
    for lay, lab, x, y, h in label_points() + [("MP-TEXT", t, u, v, hh) for t, u, v, hh in EXTRA_NOTES]:
        X, Y = L.to_utm(x, y)
        ax.text(X, Y, ar(lab), fontsize=h * 3.1, ha="center", va="center", rotation=TEXT_ROT, zorder=230,
                fontweight="bold" if h >= 4 else "normal", color="#222",
                bbox=dict(fc="white", ec="none", alpha=0.55, pad=0.6) if h < 4 else None)
    xs, ys = zip(*L.Q.values())
    ax.set_xlim(min(xs) - 20, max(xs) + 30)
    ax.set_ylim(min(ys) - 25, max(ys) + 25)
    ax.set_aspect("equal")
    ax.axis("off")
    # north arrow + scale bar
    nx, ny = max(xs) - 40, max(ys) - 90
    ax.annotate("", xy=(nx, ny + 40), xytext=(nx, ny), arrowprops=dict(arrowstyle="-|>", lw=2.5, color="k"))
    ax.text(nx, ny + 46, "N", fontsize=26, ha="center", fontweight="bold")
    sx, sy = min(xs), min(ys) - 15
    for i in range(5):
        ax.add_patch(plt.Rectangle((sx + i * 20, sy), 20, 4, fc="k" if i % 2 == 0 else "w", ec="k", lw=0.8))
        ax.text(sx + i * 20, sy - 6, str(i * 20), fontsize=11, ha="center")
    ax.text(sx + 100, sy - 6, "100 m", fontsize=11, ha="center")
    # title
    fig.text(0.98, 0.975, ar("مجمع الشلالات السكني - المقترح ج: الوادي الأخضر"), fontsize=34,
             fontweight="bold", ha="right", va="top")
    fig.text(0.98, 0.945, ar("المخطط العام - القطعة 157 مقاطعة 53 بايبوخت - 199,175 م² - إحداثيات UTM 38S"),
             fontsize=18, ha="right", va="top")
    fig.text(0.02, 0.975, "MASTER PLAN - PROPOSAL C - GREEN VALLEY", fontsize=20, ha="left", va="top")
    # summary + land use table + legend along the bottom
    tx = fig.add_axes([0.02, 0.01, 0.96, 0.15])
    tx.axis("off")
    col1 = summary
    col2 = ["استعمالات الأرض"] + [f"{n}:  {a:,.0f} م²  ({a / L.SITE.area * 100:.1f}%)" for n, a in table_rows] + \
        [f"المجموع:  {L.SITE.area:,.0f} م²"]
    items = list(L.AREAS.items())
    col3 = ["الخدمات - المرسوم / البرنامج (م²)"] + [f"{k}: {a:,.0f}" + (f" / {p:,}" if p else "") for k, (a, p) in items[:9]]
    col4 = [""] + [f"{k}: {a:,.0f}" + (f" / {p:,}" if p else "") for k, (a, p) in items[9:]]
    for j, col in enumerate((col1, col2, col3, col4)):
        x = 1.0 - j * 0.22
        for i, r in enumerate(col):
            tx.text(x, 1 - i * 0.085, ar(r), fontsize=13 if i else 15, ha="right", va="top",
                    fontweight="bold" if i == 0 else "normal", transform=tx.transAxes)
    leg = [("MP-PLOT-VILLA", "فيلا 400 م²"), ("MP-PLOT-HOUSE", "دار 200 م²"), ("MP-TOWER", "برج 20 طابق"),
           ("MP-SERVICE-EDU", "تعليم"), ("MP-SERVICE-PUBLIC", "خدمات عامة"), ("MP-SERVICE-COMM", "تجاري ونادي"),
           ("MP-SERVICE-UTIL", "بنى تحتية"), ("MP-PARK", "حديقة"), ("MP-GREEN-FINGER", "إصبع أخضر"),
           ("MP-GREEN-BELT", "حزام أخضر"), ("MP-WATER", "ماء"), ("MP-ROAD-LOOP", "شوارع")]
    for i, (lay, t) in enumerate(leg):
        x, y = 0.12 - (i // 6) * 0.11, 1 - (i % 6) * 0.16
        tx.add_patch(plt.Rectangle((x, y - 0.1), 0.012, 0.09, fc=LAYERS[lay][3], ec="k", lw=0.5, transform=tx.transAxes))
        tx.text(x - 0.004, y - 0.055, ar(t), fontsize=12, ha="right", va="center", transform=tx.transAxes)
    tx.plot([0.155, 0.17], [0.05, 0.05], color="#d04040", lw=1.5, ls=(0, (4, 2)), transform=tx.transAxes)
    tx.text(0.152, 0.05, ar("مسار جري"), fontsize=12, ha="right", va="center", transform=tx.transAxes)
    fig.savefig(pdf)
    fig.savefig(png, dpi=110)
    plt.close(fig)


def main():
    L.build()
    os.makedirs(OUT_DIR, exist_ok=True)
    table = land_use()
    nv, nh = L.COUNT["villa"], L.COUNT["house"]
    apts = 2 * 19 * 4
    green = dict(table)["الحدائق والمساحات الخضراء والممرات"]
    summary = [
        "البرنامج",
        f"فلل 400 م²: {nv}",
        f"دور 200 م²: {nh}",
        f"شقق البرجين: {apts} (2 برج × 19 طابقاً سكنياً × 4)",
        f"المجموع: {nv + nh + apts} وحدة",
        f"السكان التقريبي: {(nv + nh) * 6 + apts // 2 * 4 + apts // 2 * 6:,} نسمة",
        f"الخضرة: {green / L.SITE.area * 100:.0f}% من القطعة",
        "كل بيت يطل من الخلف على خضرة",
    ]
    write_dxf(os.path.join(OUT_DIR, NAME + ".dxf"), table, summary)
    preview(os.path.join(OUT_DIR, NAME + ".pdf"), os.path.join(OUT_DIR, NAME + ".png"), table, summary)
    print(L.COUNT, nv + nh + apts)
    for n, a in table:
        print(f"{n:50s} {a:9.0f} {a / L.SITE.area * 100:5.1f}%")


if __name__ == "__main__":
    main()
