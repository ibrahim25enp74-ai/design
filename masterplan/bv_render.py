"""Render the boulevard plan (site_v2 coordinates, wide end up) as an SVG parcellation plan."""
import sys
from shapely.geometry import MultiPolygon, Polygon, LineString, GeometryCollection, MultiLineString
import boulevard as B

COL = {"V": "#F3E6BD", "D": "#F6D29B", "jeera": "#CDE5B5", "park": "#A6D486", "green": "#BFE0A0",
       "edu": "#8DB8E8", "health": "#EE9A9A", "religious": "#B9A3DD", "commercial": "#F4B183",
       "community": "#A9C9E6", "utility": "#BDBDBD", "towers": "#D8C8EE", "sports": "#7CC576",
       "belt": "#B7DB9A"}


def d_(g):
    if g.is_empty:
        return ""
    if isinstance(g, (MultiPolygon, GeometryCollection, MultiLineString)):
        return "".join(d_(x) for x in g.geoms)
    if isinstance(g, Polygon):
        return "".join("M" + "L".join("%.2f,%.2f" % (x, -y) for x, y in r.coords) + "Z"
                       for r in [g.exterior] + list(g.interiors))
    if isinstance(g, LineString):
        return "M" + "L".join("%.2f,%.2f" % (x, -y) for x, y in g.coords)
    return ""


def svg(p):
    o = []
    P = lambda g, f, s="none", w=0.0, ex="": o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" %s/>' % (d_(g), f, s, w, ex))
    T = lambda x, y, t, sz=5.0, wt="normal": o.append(
        '<text x="%.1f" y="%.1f" font-size="%.1f" font-weight="%s" text-anchor="middle" dominant-baseline="middle" '
        'paint-order="stroke" stroke="#fff" stroke-width="%.1f">%s</text>' % (x, -y, sz, wt, sz * 0.3, t))
    # context roads
    P(LineString([(-10.9, -80), (-10.9, 960)]).buffer(6, cap_style="flat"), "#E4E4E4", "#999", 0.3)
    P(LineString([(340207.8 - B.OX, 4035892.8 - B.OY), (340028.2 - B.OX, 4034874.4 - B.OY)]).buffer(6, cap_style="flat"),
      "#E4E4E4", "#999", 0.3)
    P(B.SITE, "#FAFAF6")
    P(p.belt_area, COL["belt"])
    for b in p.blocks:
        if b["rows"]:
            continue
        P(b["poly"], COL.get(b["use"], "#ddd"), "#6f6f6f", 0.25)
    P(p.jeera, COL["jeera"], "#86a874", 0.15)
    for l in p.lots:
        P(l["poly"], COL[l["type"]], "#7b6a4a", 0.22)
        P(l["fp"], "#FFFFFF", "#8a7a5a", 0.2)
    P(p.road_area, "#D9D9D9", "#8a8a8a", 0.3)
    P(p.medians, "#6FB04D", "#4f8a36", 0.2)
    from shapely.geometry import Point
    c = Point(B.xc(p.VC), p.VC)
    P(c.buffer(36), "#E9DCC3", "#b39d73", 0.4)
    P(c.buffer(14), "#8FD1EA", "#2E86AB", 0.6)
    for t in p.towers:
        P(t, "#7E57C2", "#3d2a63", 0.4)
    for x, y in B.TREES:
        o.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#4E8B3A" fill-opacity=".85"/>' % (x, -y))
    P(B.SITE, "none", "#D0021B", 1.1)
    for b in p.blocks:
        if b["label"] and b["poly"].area > 250:
            q = b["poly"].representative_point()
            T(q.x, q.y, b["label"], 4.6)
    for lab, (x, y), n in p.gates:
        side = -1 if x < 20 else 1
        o.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="#222"/>' % (
            x + side * 16, -y - 6, x + side * 16, -y + 6, x + side * 4, -y))
        T(x + side * 30, y + 9, lab, 5.2, "bold")
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-60 -930 440 1010" width="1300" '
            'font-family="Noto Naskh Arabic, DejaVu Sans, sans-serif">%s</svg>' % "".join(o))


if __name__ == "__main__":
    p = B.build()
    v = sum(1 for l in p.lots if l["type"] == "V"); d = sum(1 for l in p.lots if l["type"] == "D")
    print("villas", v, "dars", d, "houses", v + d)
    open("out/bv.html", "w").write('<html><body style="margin:0;background:#fff">%s</body></html>' % svg(p))
