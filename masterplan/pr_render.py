"""Parcellation-plan drawing in the north-edge frame (north road along the top)."""
import math

from shapely import affinity
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon, GeometryCollection

import kit
import plot157 as P
from parcel import N, S

_M = [N.u[0], N.u[1], N.n[0], N.n[1], -(N.o[0] * N.u[0] + N.o[1] * N.u[1]), -(N.o[0] * N.n[0] + N.o[1] * N.n[1])]


def F(g):
    """Local frame -> drawing frame (x = s, y = d)."""
    return affinity.affine_transform(g, _M)


USE_COL = {
    "V": "#F3E9C6", "D": "#F7D9A8", "jeera": "#CFE6B8", "park": "#A8D58A", "green": "#BFE0A0", "wadi": "#9ED3EA",
    "edu": "#8DB8E8", "health": "#EE9A9A", "religious": "#B9A3DD", "commercial": "#F4B183", "community": "#A9C9E6",
    "utility": "#BDBDBD", "towers": "#C9B6E4", "sports": "#7CC576", "belt": "#B7DB9A", "res": "#F3E9C6",
}


def d_attr(g):
    if g.is_empty:
        return ""
    if isinstance(g, (MultiPolygon, GeometryCollection, MultiLineString)):
        return "".join(d_attr(x) for x in g.geoms)
    if isinstance(g, Polygon):
        out = ""
        for r in [g.exterior] + list(g.interiors):
            out += "M" + "L".join("%.2f,%.2f" % c[:2] for c in r.coords) + "Z"
        return out
    if isinstance(g, LineString):
        return "M" + "L".join("%.2f,%.2f" % c[:2] for c in g.coords)
    return ""


class SVG:
    def __init__(self, x0, y0, x1, y1):
        self.vb = (x0, y0, x1 - x0, y1 - y0)
        self.items = []

    def path(self, g, fill="none", stroke="none", sw=0.0, extra=""):
        d = d_attr(g)
        if d:
            self.items.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" %s/>' % (d, fill, stroke, sw, extra))

    def text(self, x, y, s, size=4.0, fill="#1a1a1a", weight="normal", anchor="middle", halo=True, rot=0):
        h = ' paint-order="stroke" stroke="#ffffff" stroke-width="%.2f" stroke-linejoin="round"' % (size * 0.3) if halo else ""
        r = ' transform="rotate(%.1f %.2f %.2f)"' % (rot, x, y) if rot else ""
        self.items.append('<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" font-weight="%s" text-anchor="%s" '
                          'dominant-baseline="middle"%s%s>%s</text>' % (x, y, size, fill, weight, anchor, h, r, s))

    def raw(self, s):
        self.items.append(s)

    def render(self, width_mm=None, height_mm=None):
        x0, y0, w, h = self.vb
        size = ' width="%.1fmm" height="%.1fmm"' % (width_mm, height_mm) if width_mm else ""
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.1f %.1f %.1f %.1f"%s '
                'font-family="Noto Naskh Arabic, Noto Sans Arabic, DejaVu Sans, sans-serif">%s</svg>'
                % (x0, y0, w, h, size, "".join(self.items)))


def plan_svg(c, labels=True):
    v = SVG(-90, -60, 1000, 360)
    site = F(kit.SITE)
    # context: public roads
    for ln, w in ((P.ROAD_N_L, 12), (P.ROAD_S_L, 12)):
        g = F(ln.buffer(w / 2, cap_style="flat"))
        v.path(g, "#E3E3E3", "#9b9b9b", 0.3)
    v.path(F(P.ROAD_X_L.buffer(5, cap_style="flat").difference(kit.SITE)), "#E3E3E3", "#9b9b9b", 0.3)
    v.path(site, "#FBFBF7")
    v.path(F(c.belt_area), USE_COL["belt"])
    for b in c.blocks:
        u = b["use"]
        if u == "res":
            continue
        col = USE_COL.get(u, "#dddddd")
        v.path(F(b["poly"]), col, "#6f6f6f", 0.25)
    v.path(F(c.jeera), USE_COL["jeera"], "#7a9a66", 0.15)
    for l in c.lots:
        v.path(F(l["poly"]), USE_COL[l["type"]], "#7b6a4a", 0.22)
    v.path(F(c.road_area), "#DCDCDC", "#8a8a8a", 0.3)
    v.path(F(c.medians), "#7DBB5C", "#4f8a36", 0.2)
    for r in c.roads:
        if r["cls"] == "finger":
            v.path(F(r["line"].buffer(4, cap_style="flat").intersection(kit.SITE)), "#CFE6B8", "none")
            v.path(F(r["line"].intersection(kit.SITE)), "none", "#6a9c4c", 0.6, 'stroke-dasharray="2 1.2"')
    for pth in c.paths:
        v.path(F(pth.intersection(kit.SITE.buffer(2))), "none", "#C9A96E", 1.6, 'stroke-linecap="round"')
    for t in c.towers:
        v.path(F(t), "#7E57C2", "#3d2a63", 0.4)
    v.path(F(P.WADI_L.intersection(kit.SITE.buffer(4))), "none", "#2E86AB", 1.4)
    for t in P.TREES_L:
        q = F(t)
        v.raw('<circle cx="%.2f" cy="%.2f" r="4" fill="#4E8B3A" fill-opacity="0.8"/>' % (q.x, q.y))
    v.path(site, "none", "#D0021B", 1.0)
    if labels:
        for b in c.blocks:
            if b["label"] and b["poly"].area > 300:
                q = F(b["poly"].representative_point())
                v.text(q.x, q.y, b["label"], 4.2 if b["poly"].area < 3000 else 5.0)
        for g in c.gates:
            q = F(g["pt"])
            tri = Polygon([(q.x - 5, q.y - 12), (q.x + 5, q.y - 12), (q.x, q.y - 3)]) if q.y < 150 else \
                Polygon([(q.x - 5, q.y + 12), (q.x + 5, q.y + 12), (q.x, q.y + 3)])
            v.path(tri, "#222", "none")
            v.text(q.x, q.y - 18 if q.y < 150 else q.y + 18, "%s %d" % ("بوابة", g["n"]), 5, weight="bold")
    return v


def preview(c, path):
    v = plan_svg(c)
    with open(path, "w") as f:
        f.write('<html><body style="margin:0;background:#fff">%s</body></html>' % v.render().replace(
            "<svg ", '<svg width="2600" '))
