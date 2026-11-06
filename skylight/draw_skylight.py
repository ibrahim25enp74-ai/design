"""Shop drawing of the 6.00 x 15.00 m skylight roof between two houses.

Writes
  SKYLIGHT_6x15.dxf  - every view at full size (mm) in model space
  SKYLIGHT_6x15.pdf  - A1 sheet with the views at their plotted scales
Run:  python3 draw_skylight.py
"""
import math

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Circle as MplCircle
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

# ======================================================================= design data
SPAN, LENGTH, N_TRUSS = 6000.0, 15000.0, 8
BAY = LENGTH / (N_TRUSS - 1)               # 2142.9
PANEL = SPAN / 6                           # 1000
B = 80.0                                   # SHS outer width
PL_T = 12.0                                # base plate
YB = PL_T + B / 2                          # bottom chord centre line
YE = YB + 500.0                            # eave node
YR = YE + 500.0                            # ridge node
SLOPE = math.atan((YR - YE) / (SPAN / 2))
OVERHANG = 100.0
SHEET_T = 16.0
EDGE = 150.0                               # slab edge beyond the bearing axis
TX = [i * BAY for i in range(N_TRUSS)]     # truss axes along the length
PX = [i * PANEL for i in range(7)]         # panel points across the span


def top_y(x):
    return YE + (YR - YE) * (1 - abs(x - SPAN / 2) / (SPAN / 2))


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


# ======================================================================= geometry builders
def shs_band(pts, w=B):
    return LineString(pts).buffer(w / 2, cap_style=2, join_style=2)


def truss_members():
    """centre-line members of one truss: list of (pts, group)"""
    m = [([(0, YB), (SPAN, YB)], "bc"),
         ([(0, YE), (SPAN / 2, YR), (SPAN, YE)], "tc"),
         ([(0, PL_T), (0, YE + 200)], "post"), ([(SPAN, PL_T), (SPAN, YE + 200)], "post")]
    for x in PX[1:-1]:
        m.append(([(x, YB), (x, top_y(x))], "web"))
    for i in range(3):
        m.append(([(PX[i], top_y(PX[i])), (PX[i + 1], YB)], "web"))
        m.append(([(PX[6 - i], top_y(PX[6 - i])), (PX[5 - i], YB)], "web"))
    return m


def truss_outline():
    off = B / 2 / math.cos(SLOPE)
    env = Polygon([(-B / 2, PL_T), (SPAN + B / 2, PL_T), (SPAN + B / 2, top_y(SPAN) + off - B / 2 * math.tan(SLOPE)),
                   (SPAN / 2, YR + off), (-B / 2, YE + off - B / 2 * math.tan(SLOPE))])
    g = unary_union([shs_band(p) for p, _ in truss_members()]).intersection(env)
    return g


def top_face(x):
    return top_y(x) + B / 2 / math.cos(SLOPE)


def slope_pt(x, d):
    """point offset d normal (outwards) from the top chord centre line at x"""
    s = -1 if x > SPAN / 2 else 1
    n = (-math.sin(SLOPE) * s, math.cos(SLOPE))
    return (x + n[0] * d, top_y(x) + n[1] * d)


PH = 1000.0      # parapet height incl. RC cap (top of cap = ±0.00) - verify on site
CAP_W, CAP_H, BRICK = 300.0, 200.0, 240.0


def house(v, x_edge, side, depth=800, drop=350):
    """Parapet (brick + RC cap) on the RC roof slab of one house. side=-1 house on the left.
    x_edge = courtyard face of the RC cap; the bearing axis is the parapet axis."""
    ax_ = x_edge - side * CAP_W / 2
    x_far = ax_ + side * depth
    cap = [(ax_ - CAP_W / 2, 0), (ax_ + CAP_W / 2, 0), (ax_ + CAP_W / 2, -CAP_H), (ax_ - CAP_W / 2, -CAP_H)]
    v.pline(cap, "A-CONC", closed=True)
    v.hatch(cap, spacing=1.0)
    br = [(ax_ - BRICK / 2, -CAP_H), (ax_ + BRICK / 2, -CAP_H), (ax_ + BRICK / 2, -PH), (ax_ - BRICK / 2, -PH)]
    v.pline(br, "A-CONC", closed=True)
    v.hatch(br, spacing=1.0, angle=-45)
    xo = ax_ - side * BRICK / 2       # courtyard face of brick / building face
    slab = [(xo, -PH), (x_far, -PH), (x_far, -PH - 200), (xo, -PH - 200)]
    v.pline(slab, "A-CONC", closed=True)
    v.hatch(slab, spacing=1.6)
    w = [(xo, -PH - 200), (xo + side * 390, -PH - 200), (xo + side * 390, -PH - drop), (xo, -PH - drop)]
    v.pline([w[0], w[3]], "A-CONC"); v.pline([w[1], w[2]], "A-CONC")
    v.hatch(w, spacing=1.2, angle=-45)
    v.line((x_far, -PH + 30), (x_far, -PH - 230), "S-STEEL-THIN")


# ======================================================================= views
views = []
sheet_items = []

# ---------------------------------------------------------------- 1 roof plan 1:50
plan = View("TOP VIEW", 50, (55, 418), (0, 20000), "roof plan - trusses, purlins, bracing")
plan.title_xy = (35, 578)
views.append(plan)
P = plan
# houses
for y0, y1, name in ((-900, EDGE, "HOUSE 1 - ROOF"), (SPAN - EDGE, SPAN + 900, "HOUSE 2 - ROOF")):
    pts = [(-1000, y0), (LENGTH + 1000, y0), (LENGTH + 1000, y1), (-1000, y1)]
    P.fill(pts, color="#ececec")
    P.line((-1000, EDGE if y0 < 0 else SPAN - EDGE), (LENGTH + 1000, EDGE if y0 < 0 else SPAN - EDGE), "A-CONC")
    P.text((LENGTH / 2, (y0 + y1) / 2 + (-150 if y0 < 0 else 150)), name, 2.6, "center", "center", bold=True)
# polycarbonate tint
P.fill([(-40, -OVERHANG), (LENGTH + 40, -OVERHANG), (LENGTH + 40, SPAN + OVERHANG), (-40, SPAN + OVERHANG)], alpha=0.8)
# steel: trusses (top chord) + purlins in plan
steel = [box(x - B / 2, 0 - B / 2, x + B / 2, SPAN + B / 2) for x in TX]
steel += [box(TX[0], y - B / 2, TX[-1], y + B / 2) for y in PX]
P.shape(unary_union(steel), "S-STEEL")
# polycarbonate edge (overhang)
P.pline([(-40, -OVERHANG), (LENGTH + 40, -OVERHANG), (LENGTH + 40, SPAN + OVERHANG), (-40, SPAN + OVERHANG)],
        "A-GLAZ", closed=True)
P.line((-40, SPAN / 2), (LENGTH + 40, SPAN / 2), "A-ALU")
# bracing in end bays, both slopes
for a, b in ((TX[0], TX[1]), (TX[-2], TX[-1])):
    for y0, y1 in ((0, SPAN / 2), (SPAN / 2, SPAN)):
        P.line((a + 60, y0 + 60), (b - 60, y1 - 60), "S-BRACE")
        P.line((a + 60, y1 - 60), (b - 60, y0 + 60), "S-BRACE")
# base plates
for x in TX:
    for y in (0, SPAN):
        P.pline([(x - 125, y - 100), (x + 125, y - 100), (x + 125, y + 100), (x - 125, y + 100)],
                "S-STEEL-THIN", closed=True)
# slope arrows
for xm in (BAY * 3.5,):
    for y0, y1 in ((SPAN / 2 - 300, 700), (SPAN / 2 + 300, SPAN - 700)):
        P.line((xm, y0), (xm, y1), "A-TEXT")
        s = 1 if y1 > y0 else -1
        P.pline([(xm, y1 + s * 350), (xm - 120, y1), (xm + 120, y1)], "A-TEXT", closed=True)
        P.text((xm + 250, (y0 + y1) / 2), "FALL 9.5° (1:6)", 2.2, "left", "center", 90 if s < 0 else -90)
P.text((BAY * 5.5, SPAN / 2 + 110), "RIDGE", 2.2, "center", "bottom", layer="A-ALU", bold=True)
P.leader((BAY * 0.5, SPAN * 0.25 - 400), (BAY * 1.5, -650), "Ø12 rod X-bracing in end bays, both slopes", 2.0)
P.leader((BAY * 2.5, SPAN - 500), (BAY * 2.0, SPAN + 600),
         "16 mm multiwall polycarbonate, sheet 2100 wide = 1 bay, ribs down the slope", 2.0)
# grids
for i, x in enumerate(TX):
    P.grid((x, -1800), (x, SPAN + 1200), str(i + 1))
P.grid((-1600, 0), (LENGTH + 400, 0), "A")
P.grid((-1600, SPAN), (LENGTH + 400, SPAN), "B")
# dims
P.dim_chain([(x, SPAN + 1100) for x in TX], 0, fmt=lambda L: f"{L:.0f}")
P.dim((TX[0], SPAN + 1100), (TX[-1], SPAN + 1100), 6, f"{LENGTH:.0f}  (8 trusses, 7 bays)")
P.dim_chain([(LENGTH + 700, y) for y in PX], 0)
P.dim((LENGTH + 700, 0), (LENGTH + 700, SPAN), -7, f"{SPAN:.0f}  bearing axes")


# ---------------------------------------------------------------- 2 truss section 1:20
sec = View("FRONT VIEW", 25, (118, 292), (0, 0), "across the 6 m - typical truss, 8 No.")
sec.title_xy = (35, 358)
views.append(sec)
S = sec
house(S, -EDGE, -1, depth=700)
house(S, SPAN + EDGE, +1, depth=700)
S.text((-EDGE - 500, -PH + 200), "HOUSE 1\nROOF", 2.6, "center", "center", bold=True)
S.text((SPAN + EDGE + 550, -PH + 200), "HOUSE 2\nROOF", 2.6, "center", "center", bold=True)
S.text((SPAN / 2, -1150), "COURTYARD BELOW", 2.4, "center", "center", layer="A-DIM", bold=True)
S.leader((SPAN + 120, -450), (SPAN + 600, -250), "PARAPET (solid brick 240)\n+ RC cap beam 300x200", 2.0)
# centre lines
for pts, _ in truss_members():
    S.pline(pts, "S-CENTER")
S.shape(truss_outline(), "S-STEEL")
# purlins (in section, rotated to slope) and bottom ties
for x in PX:
    ang = SLOPE * (-1 if x > SPAN / 2 else 1) if 0 < x < SPAN else SLOPE * (1 if x == 0 else -1)
    if x == SPAN / 2:
        ang = 0
    c = (x, top_y(x))
    sq = [(c[0] + dx * math.cos(ang) - dy * math.sin(ang), c[1] + dx * math.sin(ang) + dy * math.cos(ang))
          for dx, dy in ((-B / 2, -B / 2), (B / 2, -B / 2), (B / 2, B / 2), (-B / 2, B / 2))]
    S.line(sq[0], sq[2], "S-STEEL-THIN"); S.line(sq[1], sq[3], "S-STEEL-THIN")
for x in (PX[1], PX[3], PX[5]):
    S.line((x - B / 2, YB - B / 2), (x + B / 2, YB + B / 2), "S-STEEL-THIN")
    S.line((x - B / 2, YB + B / 2), (x + B / 2, YB - B / 2), "S-STEEL-THIN")
# base plates
for x in (0, SPAN):
    S.pline([(x - 100, 0), (x + 100, 0), (x + 100, PL_T), (x - 100, PL_T)], "S-STEEL", closed=True)
    S.line((x, PL_T + 15), (x, -120), "S-HIDDEN")
# polycarbonate + ridge cap
for side in (-1, 1):
    x0 = 0 if side < 0 else SPAN
    xe = x0 + side * OVERHANG          # eave end, horizontal projection
    xr = SPAN / 2 + side * 25
    a = (xe, top_face(x0) - OVERHANG * math.tan(SLOPE))
    b = (xr, top_face(xr))
    nx, ny = (-math.sin(SLOPE) * -side, math.cos(SLOPE))
    pts = [a, b, (b[0] + nx * SHEET_T, b[1] + ny * SHEET_T), (a[0] + nx * SHEET_T, a[1] + ny * SHEET_T)]
    S.pline(pts, "A-GLAZ", closed=True)
    S.fill(pts, alpha=1.0, color="#bfe6f3")
cap_h = top_face(SPAN / 2) + SHEET_T
S.pline([(SPAN / 2 - 170, cap_h - 170 * math.tan(SLOPE) + 6), (SPAN / 2, cap_h + 22),
         (SPAN / 2 + 170, cap_h - 170 * math.tan(SLOPE) + 6)], "A-ALU")
# side louvers (seen in section at the end posts)
for x in (0, SPAN):
    s = -1 if x == 0 else 1
    for y in range(int(YB + 70), int(YE - 40), 60):
        S.line((x + s * B / 2, y), (x + s * (B / 2 + 45), y - 35), "A-LOUVER")
# labels
S.leader(slope_pt(1700, 48), (1500, 1520), "16 mm multiwall polycarbonate", 2.2, "right")
S.leader((SPAN / 2 + 60, cap_h + 15), (3700, 1520), "aluminium ridge cap", 2.2)
S.leader(slope_pt(4500, 0), (5000, 1250), "TOP CHORD  SHS 80x80x3", 2.2)
S.leader((2500, YB - B / 2), (2200, -470), "BOTTOM CHORD  SHS 80x80x3", 2.2, "right")
S.leader((4500, (YB + top_y(4500)) / 2), (3900, -470), "VERTICALS + DIAGONALS  SHS 80x80x2", 2.2, "left")
S.leader((-B / 2, 380), (-650, 900), "END POST SHS 80x80x3\n+ alu. louvers", 2.0)
S.leader((PX[1], top_y(PX[1]) + 20), (700, 1250), "PURLIN SHS 80x80x2", 2.0, "right")
S.leader((-60, PL_T / 2), (-650, 260), "BASE PL 250x200x12\n2 M12 into RC cap", 2.0)
# dims
S.dim_chain([(x, -10) for x in PX], -4)
S.dim((0, -10), (SPAN, -10), -9, f"{SPAN:.0f}  bearing axes")
S.dim((-EDGE, -CAP_H), (SPAN + EDGE, -CAP_H), -8, f"{SPAN - 2 * EDGE:.0f}  clear between parapets  (verify on site)")
S.dim((-EDGE - 1000, -PH), (-EDGE - 1000, 0), -4, f"{PH:.0f}")
S.dim_chain([(SPAN + 420, YB), (SPAN + 420, YE), (SPAN + 420, YR)], -4)
S.level(-EDGE - 100, 0, "±0.00 top of parapet", -1)
S.level(-EDGE - 400, -PH, f"-{PH / 1000:.2f} house roof (verify)", -1)
S.level(SPAN + EDGE + 120, top_face(SPAN), f"+{top_face(SPAN) / 1000:.2f} eave", 1)
S.level(SPAN / 2 - 30, YR + 300, f"+{(top_face(SPAN / 2) + SHEET_T) / 1000:.2f} ridge", -1)
S.text((1900, top_face(1900) + 70), "slope 9.5° (1:6)", 2.2, "center", "bottom", math.degrees(SLOPE), "A-DIM")


# ---------------------------------------------------------------- 3 side elevation 1:50
el = View("SIDE VIEW", 50, (55, 152), (0, -6000), "along the 15 m - louvred ventilation band")
el.title_xy = (35, 210)
views.append(el)
E_ = el
cap = [(-500, 0), (LENGTH + 500, 0), (LENGTH + 500, -CAP_H), (-500, -CAP_H)]
E_.pline(cap, "A-CONC", closed=True); E_.hatch(cap, spacing=1.0)
br = [(-500, -CAP_H), (LENGTH + 500, -CAP_H), (LENGTH + 500, -PH), (-500, -PH)]
E_.pline(br, "A-CONC", closed=True); E_.hatch(br, spacing=1.6, angle=-45)
roof = [(-40, top_face(0) - OVERHANG * math.tan(SLOPE)), (LENGTH + 40, top_face(0) - OVERHANG * math.tan(SLOPE)),
        (LENGTH + 40, top_face(SPAN / 2) + SHEET_T), (-40, top_face(SPAN / 2) + SHEET_T)]
E_.fill(roof, color="#bfe6f3")
E_.pline(roof, "A-GLAZ", closed=True)
for x in TX:
    E_.line((x, top_face(0)), (x, top_face(SPAN / 2)), "A-ALU")
frame = [box(x - B / 2, PL_T, x + B / 2, YE + B / 2) for x in TX]
frame += [box(TX[0], YB - B / 2, TX[-1], YB + B / 2), box(TX[0], YE - B / 2, TX[-1], YE + B / 2)]
E_.shape(unary_union(frame), "S-STEEL")
for a, b in zip(TX, TX[1:]):
    for y in range(int(YB + B / 2 + 40), int(YE - B / 2), 60):
        E_.line((a + B / 2 + 20, y), (b - B / 2 - 20, y), "A-LOUVER")
for i, x in enumerate(TX):
    E_.grid((x, 1750), (x, top_face(SPAN / 2) + 60), str(i + 1), at_start=True)
    E_.pline([(x - 125, 0), (x + 125, 0), (x + 125, PL_T), (x - 125, PL_T)], "S-STEEL-THIN", closed=True)
E_.dim_chain([(x, -PH) for x in TX], -4)
E_.dim((LENGTH + 500, 0), (LENGTH + 500, top_face(0)), -4, f"{top_face(0):.0f}")
E_.dim((LENGTH + 500, top_face(0)), (LENGTH + 500, top_face(SPAN / 2) + SHEET_T), -4,
       f"{top_face(SPAN / 2) + SHEET_T - top_face(0):.0f}")
E_.leader((BAY * 0.5, (YB + YE) / 2), (BAY * 0.2, -1900), "alu. weather louvers + insect mesh", 2.0, "left")
E_.leader((BAY * 3.5, YB), (BAY * 3.4, -1900), "SILL SHS 80x80x2", 2.0, "left")
E_.leader((BAY * 5.5, YE), (BAY * 5.3, -1900), "EAVE PURLIN SHS 80x80x2", 2.0, "left")
E_.leader((BAY * 6.6, -500), (BAY * 6.8, -1900), "PARAPET + RC cap", 2.0, "left")
E_.dim((LENGTH + 500, -PH), (LENGTH + 500, 0), -4, f"{PH:.0f}")

# ---------------------------------------------------------------- 4 isometric (no scale)
iso = View("3D VIEW", 1, (0, 0), (25000, -6000), "not to scale")
iso.title_xy = (440, 578)
views.append(iso)
k = 1 / 68.0
c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))


def pj(x, y, z):  # x along length, y across, z up  ->  iso paper mm
    return ((x * c30 - y * c30) * k, (x * s30 + y * s30 + z * 1.0) * k)


def box3(x0, x1, y0, y1, z0, z1, layer="A-CONC"):
    for z in (z0, z1):
        iso.pline([pj(x0, y0, z), pj(x1, y0, z), pj(x1, y1, z), pj(x0, y1, z)], layer, closed=True)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        iso.line(pj(x, y, z0), pj(x, y, z1), layer)


for yc in (0, SPAN):  # parapets with RC cap under the bearings
    box3(-800, LENGTH + 800, yc - CAP_W / 2, yc + CAP_W / 2, -PH, 0)
for y0, y1 in ((-1800, BRICK / 2), (SPAN - BRICK / 2, SPAN + 1800)):  # houses as simple blocks
    for z in (-PH, -PH - 1500):
        iso.pline([pj(-800, y0, z), pj(LENGTH + 800, y0, z), pj(LENGTH + 800, y1, z), pj(-800, y1, z)],
                  "A-CONC", closed=True)
    for x, y in ((-800, y0), (LENGTH + 800, y0), (LENGTH + 800, y1), (-800, y1)):
        iso.line(pj(x, y, -PH), pj(x, y, -PH - 1500), "A-CONC")
for side in (0, 1):  # glazing planes
    ye, z_e = (0, YE) if side == 0 else (SPAN, YE)
    iso.fill([pj(0, ye, z_e), pj(LENGTH, ye, z_e), pj(LENGTH, SPAN / 2, YR), pj(0, SPAN / 2, YR)],
             alpha=0.55, color="#9fd6ea")
for x in TX:
    for pts, g in truss_members():
        iso.pline([pj(x, p[0], p[1]) for p in pts], "S-STEEL" if g in ("tc", "bc", "post") else "S-STEEL-THIN")
for px in PX:
    iso.line(pj(0, px, top_y(px)), pj(LENGTH, px, top_y(px)), "S-STEEL-THIN")
for px in (PX[1], PX[3], PX[5]):
    iso.line(pj(0, px, YB), pj(LENGTH, px, YB), "S-HIDDEN")
for px in (0, SPAN):
    iso.line(pj(0, px, YB), pj(LENGTH, px, YB), "S-STEEL-THIN")
for a, b in ((TX[0], TX[1]), (TX[-2], TX[-1])):
    for y0, y1 in ((0, SPAN / 2), (SPAN / 2, SPAN)):
        iso.line(pj(a, y0, top_y(y0)), pj(b, y1, top_y(y1)), "S-BRACE")
        iso.line(pj(a, y1, top_y(y1)), pj(b, y0, top_y(y0)), "S-BRACE")
iso.text(pj(LENGTH + 800, -1000, -PH - 700), "HOUSE 1", 2.6, "left", "center", bold=True)
iso.text(pj(-800, SPAN + 1000, -PH - 700), "HOUSE 2", 2.6, "right", "center", bold=True)
_all = [p for it in iso.items if it[0] in ("pl", "fill") for p in it[1]]
_x0, _x1 = min(p[0] for p in _all), max(p[0] for p in _all)
_y0, _y1 = min(p[1] for p in _all), max(p[1] for p in _all)
iso.px, iso.py = 636 - (_x0 + _x1) / 2, 385 - (_y0 + _y1) / 2

# ---------------------------------------------------------------- 5 details 1:5
DET_Y = 128


def det_view(title, px, sub):
    v = View(title, 5, (px, DET_Y), (32000 + px * 20, -6000), sub)
    v.title_xy = (0, 0)
    views.append(v)
    return v


# D1 base plate
d1 = det_view("DETAIL 1  BASE PLATE", 52, "at every truss end (16 No.)")
d = d1
sl = [(-260, 0), (260, 0), (260, -160), (-260, -160)]
d.pline(sl, "A-CONC", closed=True); d.hatch(sl, spacing=1.4)
d.pline([(-100, 0), (100, 0), (100, PL_T), (-100, PL_T)], "S-STEEL", closed=True)
d.pline([(-40, PL_T), (-40, 330)], "S-STEEL"); d.pline([(40, PL_T), (40, 330)], "S-STEEL")
d.pline([(-37, PL_T), (-37, 330)], "S-STEEL-THIN"); d.pline([(37, PL_T), (37, 330)], "S-STEEL-THIN")
d.pline([(40, PL_T), (260, PL_T)], "S-STEEL"); d.pline([(40, PL_T + B), (260, PL_T + B)], "S-STEEL")
d.pline([(40, PL_T + 3), (260, PL_T + 3)], "S-STEEL-THIN"); d.pline([(40, PL_T + B - 3), (260, PL_T + B - 3)], "S-STEEL-THIN")
for x in (-70, 70):
    d.pline([(x - 6, PL_T + 14), (x + 6, PL_T + 14), (x + 6, -110), (x - 6, -110)], "S-HIDDEN", closed=True)
    d.pline([(x - 11, PL_T), (x + 11, PL_T), (x + 11, PL_T + 10), (x - 11, PL_T + 10)], "S-STEEL-THIN", closed=True)
d.line((-40 - 60, 330), (40 + 60, 330), "S-STEEL-THIN")
d.line((260, PL_T - 20), (260, PL_T + B + 20), "S-STEEL-THIN")
for x in (-40, 40):
    s = -1 if x < 0 else 1
    d.pline([(x, PL_T), (x + s * 5, PL_T), (x, PL_T + 5)], "S-STEEL", closed=True)
d.text((0, 345), "END POST SHS 80x80x3", 2.0, "center", "bottom")
d.text((265, PL_T + B / 2), "BOTTOM\nCHORD\n80x80x3", 2.0, "left", "center")
d.leader((-70, -60), (-300, -230), "M12 chemical anchor\nembed 110, edge ≥ 100", 2.0)
d.leader((100, 6), (200, -230), "PL 200x200x12", 2.0)
d.leader((-40, PL_T + 3), (-300, 150), "fillet weld a=4\nall round", 2.0)
d.dim((-100, 0), (100, 0), -14)
d.dim((-70, PL_T + 14), (70, PL_T + 14), 23)
# plan of the plate
d.pline([(-100, -420), (100, -420), (100, -620), (-100, -620)], "S-STEEL", closed=True)
d.pline([(-40, -480), (40, -480), (40, -560), (-40, -560)], "S-STEEL", closed=True)
d.pline([(-37, -483), (37, -483), (37, -557), (-37, -557)], "S-STEEL-THIN", closed=True)
for x in (-70, 70):
    for y in (-450, -590):
        d.circle((x, y), 7, "S-STEEL-THIN")
d.text((0, -640), "PLAN OF PLATE  (holes Ø14)", 2.0, "center", "top")
d.dim((-70, -620), (70, -620), -4)
d.dim((-100, -620), (-100, -420), 6)

# D2 eave
d2 = det_view("DETAIL 2  EAVE", 200, "polycarbonate end closure")
d = d2
ex0 = 0
c = (0, YE)  # eave node (local coordinates shifted so the node is at origin)
sh = lambda p: (p[0], p[1] - YE)
g = unary_union([shs_band([(0, YE), (600, top_y(600))]), shs_band([(0, YE - 400), (0, YE + 200)]),
                 shs_band([(0, YB), (300, YB)]) if False else shs_band([(0, YE - 400), (0, YE - 399)])])
env = Polygon([(-40, YE - 400), (600, YE - 400), (600, top_face(600)), (-40, top_face(0) - 40 * math.tan(SLOPE))])
g = g.intersection(env)
for gg in getattr(g, "geoms", [g]):
    d.pline([sh(p) for p in gg.exterior.coords], "S-STEEL", closed=True)
# eave purlin in section (rotated)
ang = SLOPE
sq = [(dx * math.cos(ang) - dy * math.sin(ang), dx * math.sin(ang) + dy * math.cos(ang))
      for dx, dy in ((-40, -40), (40, -40), (40, 40), (-40, 40))]
d.line(sq[0], sq[2], "S-STEEL-THIN"); d.line(sq[1], sq[3], "S-STEEL-THIN")
tf = lambda x: top_face(x) - YE
# glazing bar base + sheet + U profile + drip
pts = [(-OVERHANG, tf(0) - OVERHANG * math.tan(SLOPE)), (600, tf(600))]
n_ = (-math.sin(SLOPE), math.cos(SLOPE))
off = lambda p, t: (p[0] + n_[0] * t, p[1] + n_[1] * t)
sheet = [off(pts[0], 4), off(pts[1], 4), off(pts[1], 4 + SHEET_T), off(pts[0], 4 + SHEET_T)]
d.fill(sheet, color="#bfe6f3"); d.pline(sheet, "A-GLAZ", closed=True)
for t in (4 + 1, 4 + SHEET_T - 1):
    d.pline([off(pts[0], t), off(pts[1], t)], "A-GLAZ")
d.pline([off(pts[0], 0), off(pts[1], 0)], "A-ALU")      # EPDM / base
e0 = pts[0]
u = [off((e0[0] + 25 * math.cos(SLOPE), e0[1] + 25 * math.sin(SLOPE)), 2), off(e0, 2), off(e0, 6 + SHEET_T),
     off((e0[0] + 25 * math.cos(SLOPE), e0[1] + 25 * math.sin(SLOPE)), 6 + SHEET_T)]
d.pline([(u[0][0] - 2, u[0][1]), *u], "A-ALU")
d.pline([(40, tf(40) - 4), (-60, tf(40) - 4 - 100 * math.tan(SLOPE) + 0), (-60, -140), (-80, -160)], "A-ALU")
for y in range(-360, -60, 60):
    d.line((-40, y), (-85, y - 35), "A-LOUVER")
d.leader(off((300, tf(300)), 4 + SHEET_T), (280, 140), "16 mm multiwall PC, UV side up", 2.0)
d.leader(u[1], (-200, 130), "alu. U-profile over\nvented (breather) tape", 2.0)
d.leader((-60, -100), (-210, -60), "alu. drip / flashing", 2.0)
d.leader((0, 0), (250, -170), "EAVE PURLIN SHS 80x80x2\nrotated to slope", 2.0)
d.leader((-60, -300), (-210, -280), "louvers", 2.0)
d.leader((520, tf(520) - 60), (560, -40), "TOP CHORD", 2.0)
d.dim(off(pts[0], 30), off((0, tf(0)), 30), 8, f"{OVERHANG:.0f}")

# D3 ridge
d3 = det_view("DETAIL 3  RIDGE", 380, "")
d = d3
sh = lambda p: (p[0] - SPAN / 2, p[1] - YR)
g = unary_union([shs_band([(SPAN / 2 - 400, top_y(SPAN / 2 - 400)), (SPAN / 2, YR), (SPAN / 2 + 400, top_y(SPAN / 2 + 400))]),
                 shs_band([(SPAN / 2, YR), (SPAN / 2, YR - 300)])])
for gg in getattr(g, "geoms", [g]):
    d.pline([sh(p) for p in gg.exterior.coords], "S-STEEL", closed=True)
d.line((-40, -40), (40, 40), "S-STEEL-THIN"); d.line((-40, 40), (40, -40), "S-STEEL-THIN")
d.text((0, -300), "", 2.0)
for side in (-1, 1):
    ps = [(side * 25, top_face(SPAN / 2 + side * 25) - YR), (side * 400, top_face(SPAN / 2 + side * 400) - YR)]
    nn = (side * math.sin(SLOPE), math.cos(SLOPE))
    of = lambda p, t: (p[0] + nn[0] * t, p[1] + nn[1] * t)
    sheet = [of(ps[0], 4), of(ps[1], 4), of(ps[1], 4 + SHEET_T), of(ps[0], 4 + SHEET_T)]
    d.fill(sheet, color="#bfe6f3"); d.pline(sheet, "A-GLAZ", closed=True)
    d.pline([of(ps[0], 0), of(ps[1], 0)], "A-ALU")
    d.pline([of(ps[0], 1), of(ps[0], 4 + SHEET_T + 2)], "A-ALU")
top = top_face(SPAN / 2) - YR + SHEET_T + 8
d.pline([(-180, top - 180 * math.tan(SLOPE) - 2), (-170, top - 170 * math.tan(SLOPE) + 6), (0, top + 16),
         (170, top - 170 * math.tan(SLOPE) + 6), (180, top - 180 * math.tan(SLOPE) - 2)], "A-ALU")
d.leader((0, top + 16), (120, 160), "aluminium ridge cap\nwith EPDM seals, screwed\nto ridge purlin @ 400", 2.0)
d.leader((-25, top - 30), (-150, 150), "solid tape on\nsheet ends", 2.0)
d.leader((0, -10), (180, -150), "RIDGE PURLIN SHS 80x80x2", 2.0)
d.leader((-300, top_face(SPAN / 2 - 300) - YR - 60), (-260, -190), "TOP CHORD 80x80x3", 2.0)
d.dim((-25, top_face(SPAN / 2 - 25) - YR + 25), (25, top_face(SPAN / 2 + 25) - YR + 25), -14, "50 gap")

# D4 glazing bar / purlin connection (section along the length, through a truss)
d4 = det_view("DETAIL 4  JOINT ON TRUSS", 560, "section along the length")
d = d4
d.pline([(-40, -40), (40, -40), (40, 40), (-40, 40)], "S-STEEL", closed=True)
d.pline([(-37, -37), (37, -37), (37, 37), (-37, 37)], "S-STEEL-THIN", closed=True)
d.text((0, -60), "TOP CHORD\n80x80x3 (cut)", 2.0, "center", "top")
for s in (-1, 1):
    d.pline([(s * 40, 40), (s * 300, 40)], "S-STEEL"); d.pline([(s * 40, -40), (s * 300, -40)], "S-STEEL")
    d.pline([(s * 40, 37), (s * 300, 37)], "S-STEEL-THIN"); d.pline([(s * 40, -37), (s * 300, -37)], "S-STEEL-THIN")
    d.line((s * 300, -55), (s * 300, 55), "S-STEEL-THIN")
    d.pline([(s * 40, 40), (s * 45, 40), (s * 40, 45)], "S-STEEL", closed=True)
    sheet = [(s * 6, 46), (s * 300, 46), (s * 300, 46 + SHEET_T), (s * 6, 46 + SHEET_T)]
    d.fill(sheet, color="#bfe6f3"); d.pline(sheet, "A-GLAZ", closed=True)
    for t in (47, 45 + SHEET_T):
        d.line((s * 6, t), (s * 300, t), "A-GLAZ")
# aluminium glazing bar: base + snap cap + gaskets
d.pline([(-30, 40), (30, 40), (30, 46), (-30, 46)], "A-ALU", closed=True)
d.pline([(-3, 46), (-3, 46 + SHEET_T), (3, 46 + SHEET_T), (3, 46)], "A-ALU")
d.pline([(-32, 46 + SHEET_T + 2), (-32, 46 + SHEET_T + 8), (32, 46 + SHEET_T + 8), (32, 46 + SHEET_T + 2)], "A-ALU")
d.line((0, 46 + SHEET_T + 8), (0, 20), "S-HIDDEN")
d.leader((20, 46 + SHEET_T + 8), (120, 140), "alu. glazing bar: base + snap cap,\nEPDM gaskets both sides", 2.0)
d.leader((0, 25), (-120, 140), "stainless self-drilling\nscrew @ 300", 2.0)
d.leader((-200, 46 + SHEET_T), (-230, -150), "PC sheet, 3 mm expansion gap", 2.0)
d.leader((200, -40), (200, -150), "PURLIN 80x80x2 butt-welded\nto top chord, tops flush", 2.0)
d.leader((42, 42), (110, -100), "weld a=3", 2.0)

# ---------------------------------------------------------------- sheet frame, titles, notes
W, H = 841, 594


def frame(ax):
    lw = 72 / 25.4
    ax.add_patch(plt.Rectangle((20, 10), W - 30, H - 20, fill=False, lw=0.7 * lw))
    ax.add_patch(plt.Rectangle((10, 5), W - 15, H - 10, fill=False, lw=0.25 * lw))
    # view titles
    for v in views:
        tx, ty = v.title_xy
        v.title_w = 9 + 2.35 * len(v.title)
        ax.text(tx, ty, v.title, fontsize=4.2 * lw / 0.72 * 0.72 / 0.72 / 1.0 * 0.75 / 0.75, weight="bold",
                ha="left", va="bottom")
        ax.plot([tx, tx + v.title_w], [ty - 1.2, ty - 1.2], color="k", lw=0.5 * lw)
        sub = (f"SCALE 1:{v.scale:.0f}" if v.scale > 1 else "") + (("   " if v.scale > 1 and v.sub else "") + v.sub)
        ax.text(tx, ty - 2.5, sub, fontsize=2.4 * lw / 0.72 * 0.72, ha="left", va="top")


views_titles = {
    "ROOF PLAN": (0, 165, 52),
    "SECTION A-A  /  TRUSS T1 (8 No.)": (-52, 105, 115),
    "ELEVATION B-B  (side, from courtyard)": (0, 52, 110),
    "3D VIEW": (0, 72, 30),
}
for v in views:
    dx, dy, w = views_titles.get(v.title, (-40, 100, 80))
    v.title_dx, v.title_dy, v.title_w = dx, dy, w
d1.title_dx, d1.title_dy, d1.title_w = -10, 85, 70
d2.title_dx, d2.title_dy, d2.title_w = -45, 85, 52
d3.title_dx, d3.title_dy, d3.title_w = -85, 85, 54
d4.title_dx, d4.title_dy, d4.title_w = -65, 85, 72

NOTES = """GENERAL NOTES
1. Dimensions in mm, levels in m. ±0.00 = top of house roof slab at the
   bearings. Check both roof levels and the real gap on site before cutting.
2. Steel: cold-formed square hollow sections, min. S235 (ST-37).
   Chords + end posts SHS 80x80x3. Verticals, diagonals, purlins, ties
   and sills SHS 80x80x2.
3. All joints fully welded, fillet all round: a=3 (t=2), a=4 (t=3).
   Grind welds flush where glazing bars sit. Cap all open tube ends.
4. Bearings: PL 200x200x12 + 4 M12 chemical anchors (embed 110,
   edge ≥ 100) into the RC slab / ring beam over the wall. Never anchor
   into brick parapets: cut the parapet at bearings or cast RC pad 300x300.
5. Purlins framed between trusses at every panel point, rotated to the
   9.5° slope, tops flush with the top chord (flat glazing plane).
6. Bottom-chord ties SHS 80x80x2 at 1/6, 1/2, 5/6 of span (uplift).
7. Bracing: Ø12 rods + turnbuckles, roof plane, bays 1-2 and 7-8, both
   slopes. Tension after erection, before glazing.
8. Glazing: 16 mm multiwall polycarbonate, UV face up, opal or bronze
   (clear overheats in summer). Ribs down the slope, sheet 2100 wide,
   cut length 3140. Alu. glazing bar on every truss, U-profile + breather
   tape at eave, solid tape + alu. cap at ridge. Screws with EPDM
   washers in Ø+6 holes @ ≤ 500 on purlins. Expansion gap 3 mm/m.
9. Gable ends: 10 mm multiwall PC on the end trusses.
10. Sides: 0.5 m band of fixed alu. weather louvers + insect mesh on both
   15 m sides lets hot air out (stack ventilation).
11. Rain drains off both eaves onto the house roofs: check their drains.
12. Finish: wire-brush/blast, 2 coats zinc-rich primer + 2 coats enamel.
13. Do not walk on the polycarbonate; use boards spanning the purlins.

DESIGN BASIS (EN 1990 / 1991 / 1993-1-1)
Dead: PC + profiles 0.10, dust 0.15 kN/m² + steel self-weight
Roof live (maintenance) 0.60 kN/m²
Wind: uplift 1.00, pressure 0.30 kN/m² (net)
Max utilisation 0.11 (diagonal) | truss deflection 0.9 mm
Purlin: utilisation 0.22, deflection 2 mm (L/1070)
Reaction per base plate (ULS): 11.5 kN down, 7.5 kN uplift
(checked for span 6.00 and 6.30 m - see truss_calc.py)"""


def notes(ax):
    lw = 72 / 25.4
    ax.text(636, 584, NOTES, fontsize=2.25 * lw / 0.72 * 0.72 * 0.98, va="top", ha="left", linespacing=1.38,
            family="DejaVu Sans")


# material schedule
L3 = 0.0
L2 = 0.0
for pts, g in truss_members():
    L = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts, pts[1:]))
    if g == "post":
        L = YE - PL_T
    if g in ("tc", "bc", "post"):
        L3 += L
    else:
        L2 += L
clear = BAY - B
purl = 7 * (N_TRUSS - 1) * clear
ties = 3 * (N_TRUSS - 1) * clear
sills = 2 * (N_TRUSS - 1) * clear
T3, T2 = L3 * N_TRUSS / 1000, (L2 * N_TRUSS + purl + ties + sills) / 1000
brace = 8 * math.hypot(BAY, math.hypot(SPAN / 2, YR - YE)) / 1000
kg3, kg2 = 7.07, 4.82
pc_roof = 2 * LENGTH * 3140 / 1e6
SCHED = [
    ("ITEM", "SIZE", "QTY"),
    ("Trusses T1 (8 No.) chords+posts", "SHS 80x80x3", f"{T3:.0f} m"),
    ("Truss webs", "SHS 80x80x2", f"{L2 * N_TRUSS / 1000:.0f} m"),
    ("Purlins (7 lines)", "SHS 80x80x2", f"{purl / 1000:.0f} m"),
    ("Bottom-chord ties (3 lines)", "SHS 80x80x2", f"{ties / 1000:.0f} m"),
    ("Side sills (2 lines)", "SHS 80x80x2", f"{sills / 1000:.0f} m"),
    ("Total 80x80x3  (6 m bars)", f"{T3 * kg3:.0f} kg", f"{math.ceil(T3 * 1.05 / 6)} bars"),
    ("Total 80x80x2  (6 m bars)", f"{T2 * kg2:.0f} kg", f"{math.ceil(T2 * 1.05 / 6)} bars"),
    ("Bracing rods + turnbuckles", "Ø12", f"8 No. / {brace:.0f} m"),
    ("Base plates", "PL 200x200x12", "16 No."),
    ("Chemical anchors", "M12 x 160", "64 No."),
    ("Roof glazing", "PC multiwall 16 mm", f"{pc_roof:.0f} m² (5 sh. 2.1x12 m)"),
    ("Gable ends", "PC multiwall 10 mm", "9 m²"),
    ("Louvers + insect mesh", "aluminium", f"2 x {LENGTH / 1000:.0f} m x 0.45 m"),
    ("Glazing bars / ridge cap / U-prof.", "aluminium", "8x3.2 m / 15 m / 30 m"),
]


def schedule(ax):
    lw = 72 / 25.4
    x0, y = 636, 226
    ax.text(x0, y, "MATERIAL SCHEDULE (approx., add 5% waste)", fontsize=2.6 * lw, weight="bold", va="top")
    y -= 5
    cols = (x0, x0 + 98, x0 + 140)
    for i, row in enumerate(SCHED):
        for c, s in zip(cols, row):
            ax.text(c, y, s, fontsize=2.1 * lw, va="top", weight="bold" if i == 0 else "normal")
        y -= 4.0
        ax.plot([x0, 830], [y + 0.8, y + 0.8], color="#999", lw=0.13 * lw)
    tot = T3 * kg3 + T2 * kg2
    ax.text(x0, y - 0.5, f"Total steel ≈ {tot / 1000:.1f} t  (+ plates, rods, welds)", fontsize=2.2 * lw,
            va="top", weight="bold")


def title_block(ax):
    lw = 72 / 25.4
    x0, y0, x1, y1 = 633, 10, 831, 62
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=0.5 * lw))
    for y in (50, 36, 24):
        ax.plot([x0, x1], [y, y], color="k", lw=0.25 * lw)
    ax.plot([732, 732], [y0, 36], color="k", lw=0.25 * lw)
    ax.text(x0 + 3, 59, "PROJECT", fontsize=1.8 * lw, va="top", color="#555")
    ax.text(x0 + 3, 55.5, "SKYLIGHT ROOF BETWEEN TWO HOUSES  6.00 x 15.00 m", fontsize=3.0 * lw, va="top",
            weight="bold")
    ax.text(x0 + 3, 47.5, "DRAWING", fontsize=1.8 * lw, va="top", color="#555")
    ax.text(x0 + 3, 44, "STEEL SKYLIGHT (SHS 80x80) + POLYCARBONATE\n3D VIEW, TOP, FRONT AND SIDE VIEWS",
            fontsize=2.4 * lw, va="top")
    for (x, lab, val) in ((x0 + 3, "SCALE", "AS SHOWN @ A1"), (735, "SHEET", "S-01")):
        ax.text(x, 33.5, lab, fontsize=1.8 * lw, va="top", color="#555")
        ax.text(x, 30, val, fontsize=3.0 * lw, va="top", weight="bold")
    for (x, lab, val) in ((x0 + 3, "DATE", "2026-11-06"), (735, "REV", "0  - for review")):
        ax.text(x, 21.5, lab, fontsize=1.8 * lw, va="top", color="#555")
        ax.text(x, 18, val, fontsize=2.6 * lw, va="top")


LEGEND = [
    ("MEMBERS", ""),
    ("Top chord, bottom chord, end posts", "SHS 80x80x3"),
    ("Verticals, diagonals", "SHS 80x80x2"),
    ("Purlins (7 lines), bottom ties (3), sills (2)", "SHS 80x80x2"),
    ("Bracing, end bays", "Ø12 rod"),
    ("Base plates (16 No.)", "PL 250x200x12 + 2 M12 chem."),
    ("Bearing: parapet, solid brick 240", "+ RC cap beam 300x200, 4Ø12"),
    ("Glazing", "16 mm multiwall polycarbonate"),
    ("Sides 0.5 m", "alu. louvers + insect mesh"),
    ("", ""),
    ("Trusses: 8 No. @ 2143 mm  |  slope 9.5° (1:6)", ""),
    ("Dimensions in mm, levels in m (±0.00 = top of parapet cap)", ""),
]


def legend(ax):
    lw = 72 / 25.4
    x0, y = 440, 108
    for i, (a, b) in enumerate(LEGEND):
        ax.text(x0, y, a, fontsize=(3.0 if i == 0 else 2.4) * lw, va="top", weight="bold" if i == 0 else "normal")
        ax.text(x0 + 100, y, b, fontsize=2.4 * lw, va="top")
        y -= 5.6 if i == 0 else 4.6


sheet_items += [frame, legend, title_block]
views = [plan, sec, el, iso]

if __name__ == "__main__":
    draw_pdf(views, sheet_items, "SKYLIGHT_6x15.pdf")
    draw_dxf(views, "SKYLIGHT_6x15.dxf")
    print("steel 80x80x3:", round(T3, 1), "m   80x80x2:", round(T2, 1), "m   PC roof", round(pc_roof, 1), "m2")
