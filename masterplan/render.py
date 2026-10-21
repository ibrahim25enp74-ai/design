"""SVG drawings of a plan in the local frame (long axis horizontal, north arrow shows true north)."""
import math

from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon, GeometryCollection

import kit
import plot157 as P

COL = {
    "V": "#FBE3A0", "D": "#F3BD4E", "fp": "#8A6D3B", "jeera": "#D7EBC4", "tower_zone": "#EDB98A",
    "tower": "#B5562A", "edu": "#7FB2E5", "health": "#B4A7D6", "civic": "#9FC5E8", "market": "#E58C7A",
    "util": "#B7B7B7", "park": "#A9D18E", "wadi": "#8FD1E6", "sports": "#7BC46E", "buffer": "#C4E0AE",
    "parking": "#D9D9D9", "main": "#FFFFFF", "local": "#FFFFFF", "site": "#F7F5EF",
}
KIND = {k: v[2] for k, v in kit.SERVICES.items()}


def _paths(g, ty):
    """SVG path data for a shapely geometry; y is flipped (SVG y down)."""
    if g.is_empty:
        return ""
    if isinstance(g, (MultiPolygon, GeometryCollection, MultiLineString)):
        return "".join(_paths(p, ty) for p in g.geoms)
    if isinstance(g, Polygon):
        out = ""
        for ring in [g.exterior] + list(g.interiors):
            cs = list(ring.coords)
            out += "M" + " L".join("%.2f,%.2f" % (x, ty(y)) for x, y in cs) + "Z"
        return out
    if isinstance(g, LineString):
        cs = list(g.coords)
        return "M" + " L".join("%.2f,%.2f" % (x, ty(y)) for x, y in cs)
    return ""


class Canvas:
    def __init__(self, x0=-70, y0=-40, x1=880, y1=330):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.items = []

    def ty(self, y):
        return -y

    def poly(self, g, fill, stroke="none", sw=0.0, op=1.0, extra=""):
        d = _paths(g, self.ty)
        if d:
            self.items.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%.2f" fill-opacity="%.2f" %s/>'
                              % (d, fill, stroke, sw, op, extra))

    def line(self, g, stroke, sw, dash=None, op=1.0, cap="butt"):
        d = _paths(g, self.ty)
        if d:
            da = ' stroke-dasharray="%s"' % dash if dash else ""
            self.items.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-opacity="%.2f"'
                              ' stroke-linecap="%s"%s/>' % (d, stroke, sw, op, cap, da))

    def circle(self, x, y, r, fill, stroke="none", sw=0, op=1.0):
        self.items.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" stroke="%s" stroke-width="%.2f" '
                          'fill-opacity="%.2f"/>' % (x, self.ty(y), r, fill, stroke, sw, op))

    def text(self, x, y, s, size=6, fill="#222", anchor="middle", weight="normal", rot=0.0, halo=True):
        h = ' paint-order="stroke" stroke="#fff" stroke-width="%.2f" stroke-linejoin="round"' % (size * 0.35) if halo else ""
        tr = ' transform="rotate(%.1f %.2f %.2f)"' % (rot, x, self.ty(y)) if rot else ""
        self.items.append('<text x="%.2f" y="%.2f" font-size="%.2f" fill="%s" text-anchor="%s" font-weight="%s"'
                          ' dominant-baseline="middle"%s%s>%s</text>' % (x, self.ty(y), size, fill, anchor, weight, h, tr, s))

    def raw(self, s):
        self.items.append(s)

    def svg(self, width_px=None, cls=""):
        w, h = self.x1 - self.x0, self.y1 - self.y0
        vb = "%.1f %.1f %.1f %.1f" % (self.x0, -self.y1, w, h)
        size = ' width="%d" height="%d"' % (width_px, width_px * h / w) if width_px else ""
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s"%s class="%s" '
                'font-family="Noto Naskh Arabic, Noto Sans Arabic, DejaVu Sans, sans-serif">%s</svg>'
                % (vb, size, cls, "".join(self.items)))


def north_arrow(c, x, y, r=14):
    a = math.radians(90 - P.AXIS_ANGLE)   # true north in the local frame
    dx, dy = math.cos(a), math.sin(a)
    tip = (x + dx * r, y + dy * r)
    left = (x - dy * r * 0.35 - dx * r * 0.4, y + dx * r * 0.35 - dy * r * 0.4)
    right = (x + dy * r * 0.35 - dx * r * 0.4, y - dx * r * 0.35 - dy * r * 0.4)
    c.poly(Polygon([tip, left, (x, y), right]), "#222")
    c.circle(x, y, r * 1.05, "none", "#222", 0.6)
    c.text(tip[0] + dx * 7, tip[1] + dy * 7, "N", 7, weight="bold")


def scale_bar(c, x, y, L=100):
    for i in range(5):
        seg = LineString([(x + i * L / 5, y), (x + (i + 1) * L / 5, y)])
        c.line(seg, "#222" if i % 2 == 0 else "#fff", 3)
    c.line(LineString([(x, y - 1.6), (x + L, y - 1.6), (x + L, y + 1.6), (x, y + 1.6), (x, y - 1.6)]), "#222", 0.4)
    for v in (0, L / 2, L):
        c.text(x + v, y - 7, "%d" % v, 5)
    c.text(x + L + 4, y - 7, "م", 5, anchor="start")


def base(c, plan):
    c.poly(kit.SITE, COL["site"])
    # external roads
    for ln in (P.ROAD_S_L, P.ROAD_N_L):
        c.line(ln, "#CFCFCF", 12)
        c.line(ln, "#9A9A9A", 0.4, dash="6 4")


def masterplan(plan, labels=True, lots=True, phases=False):
    c = Canvas()
    base(c, plan)
    for name, p in plan.parcels.items():
        cat = p["cat"]
        if cat in ("service",):
            col = COL["market"] if name == "market" else COL[KIND[name]]
        elif cat == "util":
            col = COL["util"]
        else:
            col = COL.get(cat, "#eee")
        c.poly(p["poly"], col, "#666", 0.25)
    c.poly(plan.jeera, COL["jeera"])
    c.poly(plan.leftover, COL["park"], op=0.8)
    if lots:
        for l in plan.lots:
            c.poly(l["poly"], COL[l["type"]], "#7a6a3a", 0.18)
            c.poly(l["fp"], COL["fp"])
    c.poly(plan.main_roads, "#FFFFFF", "#8c8c8c", 0.35)
    c.poly(plan.local_roads, "#FFFFFF", "#b0b0b0", 0.25)
    for r in plan.roads:
        if r["cls"] in ("blvd",):
            c.line(r["line"], "#9CC27A", 4, op=0.9)     # planted median
    for pth in plan.paths:
        c.line(pth, "#6E9E4F", 1.0, dash="2 1.5")
    # wadi line
    c.line(P.WADI_L.intersection(kit.SITE.buffer(5)), "#2E86AB", 1.6)
    for t in plan.towers:
        c.poly(t, COL["tower"], "#5a2a10", 0.4)
    for t in P.TREES_L:
        c.circle(t.x, t.y, 4, "#4E8B3A", "#2f5a22", 0.3, op=0.85)
    c.poly(kit.SITE, "none", "#C0392B", 1.2)
    for g in plan.gates:
        col = "#C0392B" if g["kind"] == "main" else "#E67E22"
        c.circle(g["pt"].x, g["pt"].y, 4.5 if g["kind"] == "main" else 3.2, col, "#fff", 0.8)
    if labels:
        for name, p in plan.parcels.items():
            if p["poly"].is_empty or not p.get("label"):
                continue
            pt = p["poly"].representative_point()
            size = 4.2 if p["poly"].area < 3000 else 5.2
            c.text(pt.x, pt.y, p["label"], size)
    north_arrow(c, 830, 300)
    scale_bar(c, -50, -28)
    return c


def preview(plan, path):
    c = masterplan(plan)
    html = ('<html><body style="margin:0;background:#fff">%s</body></html>' % c.svg(2400))
    with open(path, "w") as f:
        f.write(html)
