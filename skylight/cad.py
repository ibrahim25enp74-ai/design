"""Minimal 2D CAD layer: views in real mm -> A1 PDF (matplotlib) + full-size DXF (ezdxf)."""
import math

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Circle as MplCircle
from shapely.geometry import LineString, Polygon

# ======================================================================= tiny CAD layer
LAYERS = {  # name: (dxf colour, pdf colour, lineweight mm)
    "S-STEEL": (7, "#000000", 0.50),
    "S-STEEL-THIN": (7, "#000000", 0.25),
    "S-CENTER": (1, "#c0392b", 0.18),
    "S-HIDDEN": (8, "#555555", 0.18),
    "S-BRACE": (6, "#8e44ad", 0.25),
    "A-GLAZ": (4, "#1f8fb3", 0.35),
    "A-ALU": (5, "#2c3e8f", 0.30),
    "A-LOUVER": (3, "#2e7d32", 0.18),
    "A-CONC": (8, "#6d6d6d", 0.35),
    "A-HATCH": (8, "#9a9a9a", 0.13),
    "A-DIM": (2, "#7a5c00", 0.18),
    "A-TEXT": (7, "#000000", 0.18),
    "A-TITLE": (7, "#000000", 0.35),
    "A-GRID": (1, "#c0392b", 0.18),
    "A-BORDER": (7, "#000000", 0.70),
    "A-FILL": (254, "#dff3fa", 0.0),
}
LTYPE = {"S-CENTER": "CENTER", "S-HIDDEN": "DASHED", "A-GRID": "CENTER"}
MPL_LS = {"CENTER": (0, (10, 2, 2, 2)), "DASHED": (0, (4, 2)), None: "-"}


class View:
    def __init__(self, title, scale, paper_xy, model_xy, sub=""):
        self.title, self.scale, self.sub = title, scale, sub
        self.px, self.py = paper_xy           # paper mm of the view's local origin
        self.mx, self.my = model_xy           # model mm (DXF) of the local origin
        self.items = []

    # --- primitives in real (local) mm --------------------------------------
    def line(self, p, q, layer="S-STEEL", lt=None):
        self.items.append(("pl", [p, q], False, layer, lt))

    def pline(self, pts, layer="S-STEEL", closed=False, lt=None):
        self.items.append(("pl", list(pts), closed, layer, lt))

    def circle(self, c, r, layer="S-STEEL"):
        self.items.append(("ci", c, r, layer))

    def fill(self, pts, layer="A-FILL", alpha=1.0, color=None):
        self.items.append(("fill", list(pts), layer, alpha, color))

    def hatch(self, pts, layer="A-HATCH", spacing=3.0, angle=45):
        """spacing in paper mm"""
        self.items.append(("hatch", list(pts), layer, spacing, angle))

    def text(self, p, s, h=2.5, ha="left", va="bottom", rot=0.0, layer="A-TEXT", bold=False):
        """h in paper mm"""
        self.items.append(("tx", p, s, h, ha, va, rot, layer, bold))

    def shape(self, geom, layer="S-STEEL"):
        geoms = getattr(geom, "geoms", [geom])
        for g in geoms:
            self.pline(list(g.exterior.coords), layer, closed=True)
            for r in g.interiors:
                self.pline(list(r.coords), layer, closed=True)

    # --- helpers -------------------------------------------------------------
    def dim(self, p, q, off, txt=None, h=2.2):
        """aligned dimension; off is in paper mm, + to the left of p->q"""
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        o = off * self.scale
        a = (p[0] + nx * o, p[1] + ny * o)
        b = (q[0] + nx * o, q[1] + ny * o)
        gap, ext = 1.0 * self.scale * math.copysign(1, off), 1.5 * self.scale * math.copysign(1, off)
        for s, d in ((p, a), (q, b)):
            self.line((s[0] + nx * gap, s[1] + ny * gap), (d[0] + nx * ext, d[1] + ny * ext), "A-DIM")
        self.line(a, b, "A-DIM")
        t = 1.2 * self.scale
        for c in (a, b):  # 45 degree architectural ticks
            self.line((c[0] - (ux + nx) * t * 0.7, c[1] - (uy + ny) * t * 0.7),
                      (c[0] + (ux + nx) * t * 0.7, c[1] + (uy + ny) * t * 0.7), "A-DIM")
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90.1 or ang < -89.9:
            ang -= 180 * math.copysign(1, ang)
        m = ((a[0] + b[0]) / 2 + nx * 0.6 * self.scale * math.copysign(1, ny if abs(ny) > 1e-9 else nx),
             (a[1] + b[1]) / 2 + ny * 0.6 * self.scale * math.copysign(1, ny if abs(ny) > 1e-9 else nx))
        self.text(m, txt if txt is not None else f"{L:.0f}", h, "center", "bottom", ang, "A-DIM")

    def dim_chain(self, pts, off, h=2.2, fmt=None):
        for p, q in zip(pts, pts[1:]):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            self.dim(p, q, off, fmt(L) if fmt else None, h)

    def leader(self, p, t, s, h=2.3, ha=None):
        """arrow at p, text at t (real mm)"""
        self.line(p, t, "A-TEXT")
        ang = math.atan2(t[1] - p[1], t[0] - p[0])
        a = 1.6 * self.scale
        for da in (0.35, -0.35):
            self.line(p, (p[0] + a * math.cos(ang + da), p[1] + a * math.sin(ang + da)), "A-TEXT")
        ha = ha or ("left" if t[0] >= p[0] else "right")
        sh = 0.8 * self.scale * (1 if ha == "left" else -1)
        self.line(t, (t[0] + sh * 2, t[1]), "A-TEXT")
        self.text((t[0] + sh * 2.6, t[1]), s, h, ha, "center")

    def level(self, x, y, s, side=1):
        a = 1.8 * self.scale
        self.pline([(x, y), (x - a * 0.6, y + a), (x + a * 0.6, y + a)], "A-DIM", closed=True)
        self.line((x - a * 0.6, y + a), (x + side * 12 * self.scale, y + a), "A-DIM")
        self.text((x + side * 1.2 * self.scale, y + a * 1.25), s, 2.2,
                  "left" if side > 0 else "right", "bottom", 0, "A-DIM")

    def grid(self, p, q, label, at_start=True):
        self.line(p, q, "A-GRID", "CENTER")
        r = 3.2 * self.scale
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        c = (p[0] - dx / L * r, p[1] - dy / L * r) if at_start else (q[0] + dx / L * r, q[1] + dy / L * r)
        self.circle(c, r, "A-GRID")
        self.text(c, label, 3.0, "center", "center", 0, "A-GRID")

    def section_mark(self, p, q, label, flip=False):
        """cut line p->q with view arrows; arrows point to the left of p->q (or right if flip)"""
        self.line(p, q, "A-TITLE", "CENTER")
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        if flip:
            nx, ny = -nx, -ny
        for e in (p, q):
            a = 4 * self.scale
            self.pline([e, (e[0] + nx * a, e[1] + ny * a)], "A-TITLE")
            self.pline([(e[0] + nx * a, e[1] + ny * a),
                        (e[0] + nx * a * 0.6 + dx / L * a * 0.3, e[1] + ny * a * 0.6 + dy / L * a * 0.3),
                        (e[0] + nx * a * 0.6 - dx / L * a * 0.3, e[1] + ny * a * 0.6 - dy / L * a * 0.3)],
                       "A-TITLE", closed=True)
            self.text((e[0] + nx * a * 1.5, e[1] + ny * a * 1.5), label, 4, "center", "center", 0, "A-TITLE", True)

    # --- output ---------------------------------------------------------------
    def to_paper(self, p):
        return (self.px + p[0] / self.scale, self.py + p[1] / self.scale)

    def to_model(self, p):
        return (self.mx + p[0], self.my + p[1])


def draw_pdf(views, sheet_items, path, size=(841, 594)):
    fig = plt.figure(figsize=(size[0] / 25.4, size[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, size[0]); ax.set_ylim(0, size[1]); ax.set_aspect("equal"); ax.axis("off")
    pt = 72 / 25.4
    for v in views:
        for it in v.items:
            k = it[0]
            if k == "pl":
                _, pts, closed, layer, lt = it
                P = [v.to_paper(p) for p in pts]
                if closed:
                    P.append(P[0])
                c, lw = LAYERS[layer][1], LAYERS[layer][2]
                ls = MPL_LS[lt or LTYPE.get(layer)]
                ax.plot(*zip(*P), color=c, lw=lw * pt, ls=ls, solid_capstyle="butt",
                        solid_joinstyle="miter", zorder=3)
            elif k == "ci":
                _, c, r, layer = it
                ax.add_patch(MplCircle(v.to_paper(c), r / v.scale, fill=False,
                                       ec=LAYERS[layer][1], lw=LAYERS[layer][2] * pt, zorder=3))
            elif k == "fill":
                _, pts, layer, alpha, color = it
                ax.add_patch(MplPolygon([v.to_paper(p) for p in pts], closed=True, fc=color or LAYERS[layer][1],
                                        ec="none", alpha=alpha, zorder=1))
            elif k == "hatch":
                _, pts, layer, sp, ang = it
                P = Polygon([v.to_paper(p) for p in pts])
                x0, y0, x1, y1 = P.bounds
                d = math.hypot(x1 - x0, y1 - y0)
                a = math.radians(ang)
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                n = int(d / sp) + 1
                for i in range(-n, n + 1):
                    ox, oy = cx - math.sin(a) * i * sp, cy + math.cos(a) * i * sp
                    seg = LineString([(ox - math.cos(a) * d, oy - math.sin(a) * d),
                                      (ox + math.cos(a) * d, oy + math.sin(a) * d)]).intersection(P)
                    for g in getattr(seg, "geoms", [seg]):
                        if not g.is_empty and g.geom_type == "LineString":
                            ax.plot(*zip(*g.coords), color=LAYERS[layer][1], lw=LAYERS[layer][2] * pt, zorder=2)
            elif k == "tx":
                _, p, s, h, ha, va, rot, layer, bold = it
                ax.text(*v.to_paper(p), s, fontsize=h * pt / 0.72, ha=ha, va=va, rotation=rot,
                        rotation_mode="anchor", color=LAYERS[layer][1], family="DejaVu Sans",
                        weight="bold" if bold else "normal", zorder=4, linespacing=1.35)
    for it in sheet_items:
        it(ax)
    fig.savefig(path)
    plt.close(fig)


def draw_dxf(views, path):
    doc = ezdxf.new("R2010", setup=True, units=ezdxf.units.MM)
    msp = doc.modelspace()
    for name, (col, _, lw) in LAYERS.items():
        doc.layers.add(name, color=col, lineweight=int(round(lw * 100)) if lw else -3,
                       linetype=LTYPE.get(name, "CONTINUOUS"))
    for v in views:
        s = v.scale
        for it in v.items:
            k = it[0]
            if k == "pl":
                _, pts, closed, layer, lt = it
                e = msp.add_lwpolyline([v.to_model(p) for p in pts], close=closed, dxfattribs={"layer": layer})
                if lt or LTYPE.get(layer):
                    e.dxf.linetype = lt or LTYPE[layer]
                    e.dxf.ltscale = s * 0.6
            elif k == "ci":
                _, c, r, layer = it
                msp.add_circle(v.to_model(c), r, dxfattribs={"layer": layer})
            elif k == "fill":
                continue
            elif k == "hatch":
                _, pts, layer, sp, ang = it
                h = msp.add_hatch(dxfattribs={"layer": layer})
                h.set_pattern_fill("ANSI31", scale=sp * s / 3.175, angle=ang - 45)
                h.paths.add_polyline_path([v.to_model(p) for p in pts], is_closed=True)
            elif k == "tx":
                _, p, txt, hh, ha, va, rot, layer, bold = it
                lines = txt.split("\n")
                step = hh * s * 1.6
                n = len(lines)
                for j, ln in enumerate(lines):
                    if va == "top":
                        dy = -j * step
                    elif va == "center":
                        dy = ((n - 1) / 2 - j) * step
                    else:
                        dy = (n - 1 - j) * step
                    r = math.radians(rot)
                    q = (p[0] - math.sin(r) * dy, p[1] + math.cos(r) * dy)
                    al = {"left": "LEFT", "center": "CENTER", "right": "RIGHT"}[ha] + "_" + \
                         {"bottom": "BOTTOM", "center": "MIDDLE", "top": "TOP"}[va]
                    al = al.replace("CENTER_MIDDLE", "MIDDLE_CENTER").replace("_", "_")
                    t = msp.add_text(ln, height=hh * s * 0.72 / 0.72 * 0.75, rotation=rot,
                                     dxfattribs={"layer": layer, "style": "OpenSans"})
                    align = {"LEFT_BOTTOM": "BOTTOM_LEFT", "CENTER_BOTTOM": "BOTTOM_CENTER",
                             "RIGHT_BOTTOM": "BOTTOM_RIGHT", "LEFT_MIDDLE": "MIDDLE_LEFT",
                             "MIDDLE_CENTER": "MIDDLE_CENTER", "RIGHT_MIDDLE": "MIDDLE_RIGHT",
                             "LEFT_TOP": "TOP_LEFT", "CENTER_TOP": "TOP_CENTER", "RIGHT_TOP": "TOP_RIGHT"}[al]
                    t.set_placement(v.to_model(q), align=ezdxf.enums.TextEntityAlignment[align])
    doc.saveas(path)


