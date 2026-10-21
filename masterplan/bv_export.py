"""Export the boulevard plan to DXF (site_v2 coordinates) and an A3 PDF sheet."""
import subprocess
import ezdxf
from shapely import affinity
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
import boulevard as B
import bv_render as R

LAYER = {"V": ("MP_LOTS_VILLA_400", 50), "D": ("MP_LOTS_DAR_200", 30), "fp": ("MP_HOUSES", 7),
         "road": ("MP_ROADS", 8), "median": ("MP_MEDIAN", 3), "jeera": ("MP_GREEN_NEIGHBOURHOOD", 82),
         "park": ("MP_PARKS", 3), "green": ("MP_GREEN", 82), "edu": ("MP_EDUCATION", 5), "health": ("MP_HEALTH", 1),
         "religious": ("MP_MOSQUE", 6), "commercial": ("MP_COMMERCIAL", 30), "community": ("MP_COMMUNITY", 4),
         "utility": ("MP_UTILITIES", 9), "towers": ("MP_TOWER_ZONE", 211), "tower": ("MP_TOWERS", 200),
         "sports": ("MP_SPORTS", 94), "belt": ("MP_BELT", 82), "label": ("MP_LABELS", 7), "gate": ("MP_GATES", 1)}
NAMES = {"edu": "تعليم", "health": "صحة", "religious": "جامع", "commercial": "تجاري", "community": "مجتمعي",
         "utility": "مرافق", "towers": "منطقة البرجين", "sports": "ملاعب", "park": "حدائق", "green": "مساحات خضراء"}


def polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [x for x in getattr(g, "geoms", []) if isinstance(x, Polygon)]


def W(g):
    return affinity.translate(g, B.OX, B.OY)


def add(msp, g, key, hatch=False):
    lay = LAYER[key][0]
    for p in polys(W(g)):
        for ring in [p.exterior] + list(p.interiors):
            msp.add_lwpolyline(list(ring.coords)[:-1], close=True, dxfattribs={"layer": lay})
        if hatch:
            h = msp.add_hatch(color=LAYER[key][1], dxfattribs={"layer": lay})
            h.paths.add_polyline_path(list(p.exterior.coords)[:-1], is_closed=True)
            for r in p.interiors:
                h.paths.add_polyline_path(list(r.coords)[:-1], is_closed=True)


def main():
    p = B.build()
    doc = ezdxf.readfile("site_v2.dxf")
    for name, col in LAYER.values():
        if name not in doc.layers:
            doc.layers.add(name, color=col)
    msp = doc.modelspace()
    for e in list(msp.query('*[layer=="WATER_APPROX"]')):
        msp.delete_entity(e)                       # watercourse cancelled
    add(msp, p.road_area, "road", True)
    add(msp, p.medians, "median", True)
    add(msp, p.belt_area, "belt", True)
    for b in p.blocks:
        if not b["rows"]:
            add(msp, b["poly"], b["use"] if b["use"] in LAYER else "green", True)
    add(msp, p.jeera, "jeera", True)
    for l in p.lots:
        add(msp, l["poly"], l["type"])
        add(msp, l["fp"], "fp")
    for t in p.towers:
        add(msp, t, "tower", True)
    for b in p.blocks:
        if b["label"]:
            q = W(b["poly"].representative_point())
            msp.add_text(b["label"], height=4, dxfattribs={"layer": LAYER["label"][0], "style": "OpenSans"}).set_placement(
                (q.x, q.y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    for lab, (x, y), n in p.gates:
        msp.add_text("%s (%d)" % (lab, n), height=6, dxfattribs={"layer": LAYER["gate"][0]}).set_placement(
            (x + B.OX, y + B.OY), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    doc.saveas("MP_A_BOULEVARD.dxf")

    # ---------------- figures for the sheet
    v = sum(1 for l in p.lots if l["type"] == "V"); d = sum(1 for l in p.lots if l["type"] == "D")
    area = {}
    for b in p.blocks:
        if not b["rows"]:
            area[b["use"]] = area.get(b["use"], 0) + b["poly"].area
    lots = sum(l["poly"].area for l in p.lots)
    housing = lots + p.jeera.area
    rows = [("السكن الأفقي (قطع وحدائق جيرة)", housing, "#F3E6BD"),
            ("منطقة البرجين", area.get("towers", 0), "#D8C8EE"),
            ("الخدمات العامة والبنى التحتية", sum(area.get(k, 0) for k in ("edu", "health", "religious", "commercial", "community", "utility")), "#F2B8A8"),
            ("الحدائق العامة والملاعب", sum(area.get(k, 0) for k in ("park", "green", "sports")) + p.belt_area.area, "#A6D486"),
            ("الشوارع والساحات", p.road_area.area, "#D9D9D9")]
    tot = sum(r[1] for r in rows)
    tr = "".join('<tr><td><span class="sw" style="background:%s"></span>%s</td><td>%s</td><td>%.1f%%</td></tr>'
                 % (c, n, f"{a:,.0f}", 100 * a / tot) for n, a, c in rows)
    html = """<html><head><meta charset="utf-8"><style>
@page{size:420mm 297mm;margin:0} body{margin:0;font-family:'Noto Naskh Arabic','DejaVu Sans',sans-serif;direction:rtl}
.sheet{width:420mm;height:297mm;display:flex;flex-direction:row-reverse;background:#fff}
.plan{width:260mm;height:297mm;display:flex;align-items:center;justify-content:center;border-left:1px solid #ccc}
.plan svg{height:285mm;width:auto}
.panel{width:160mm;padding:12mm 12mm;box-sizing:border-box;color:#1f3b2c}
h1{font-size:26pt;margin:0} h2{font-size:15pt;margin:6mm 0 2mm;border-bottom:1px solid #9bb;padding-bottom:1mm}
p{font-size:11pt;line-height:1.6;margin:2mm 0} table{width:100%%;border-collapse:collapse;font-size:10.5pt}
td{border:1px solid #cfd8d3;padding:1.6mm 2mm} td:nth-child(n+2){text-align:center;direction:ltr}
.sw{display:inline-block;width:5mm;height:4mm;margin-left:2mm;border:1px solid #888;vertical-align:middle}
ul{font-size:10.5pt;line-height:1.7;margin:1mm 0;padding-right:5mm}
</style></head><body><div class="sheet"><div class="plan">%s</div><div class="panel">
<h1>مجمع الشلالات السكني</h1><div style="font-size:14pt">محافظة نينوى · القطعة 157 م53 بايبوخت</div>
<h2>المخطط العام - المقترح (أ): المحور</h2>
<p>بوليفارد مشجر بجزيرة وسطية يمتد بطول القطعة من دوّار البوابة الرئيسية إلى دوّار البوابة الخدمية، تتوسطه ساحة النافورة الدائرية وحولها الجامع والسوق والخدمات. البرجان بين أشجار البستان شمال الشارع العرضي العام. المجرى المائي ملغى.</p>
<h2>توزيع استعمالات الأرض (محسوب من المخطط)</h2>
<table><tr style="background:#eef3ef"><td>الاستعمال</td><td>المساحة م²</td><td>النسبة</td></tr>%s
<tr style="font-weight:bold"><td>المجموع</td><td>%s</td><td>100%%</td></tr></table>
<h2>الوحدات</h2><ul><li>فلل منفصلة 400 م²: %d</li><li>دور متصلة 200 م²: %d</li><li>برجان سكنيان: 152 شقة</li>
<li>المجموع: %d وحدة</li></ul>
<h2>الشوارع</h2><ul><li>بوليفارد 24 م بجزيرة وسطية</li><li>دوّارات على المحور وساحة دائرية مركزية</li><li>شوارع محلية 12 م</li></ul>
<p style="font-size:9pt;color:#666">رسم على إحداثيات ملف المسح SHALLALAT_SITE_PLAN.dxf · مقياس الرسم 1:2500 تقريباً على A3</p>
</div></div></body></html>""" % (R.svg(p).replace('width="1300"', ''), tr, f"{tot:,.0f}", v, d, v + d + 152)
    open("out/MP_A_BOULEVARD.html", "w").write(html)
    subprocess.run(["node", "shot.js", "pdf", "out/MP_A_BOULEVARD.html", "MP_A_BOULEVARD.pdf"], check=True)
    subprocess.run(["node", "shot.js", "png", "out/MP_A_BOULEVARD.html", "out/MP_A_sheet.png", "1587"], check=True)
    print(v, d, round(tot))


main()
