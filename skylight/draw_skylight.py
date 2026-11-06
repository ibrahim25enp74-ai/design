"""Drawing of the 6.70 x 15.00 m skylight between two houses: portal frames of
SHS 80x80x5 every 1.50 m with a short collar tie under the ridge (no eave tie), purlins SHS 80x80x2 at ~0.56 m,
vent windows along both 15 m sides. Legs drop 0.50 m past the parapets onto
the house roofs.

Writes  SKYLIGHT_6x15.pdf (A1: 3D, top, front, side views)  and  SKYLIGHT_6x15.dxf (full size, mm)
Run:    python3 draw_skylight.py
"""
import math

import matplotlib.pyplot as plt
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from cad import View, draw_dxf, draw_pdf

# ======================================================================= design data (mm)
PAR_AX = 6000.0                 # parapet axis to parapet axis (verify on site)
LEG_OFF = 350.0                 # leg axis beyond the parapet axis, on the house roof
SPAN = PAR_AX + 2 * LEG_OFF     # 6700 leg to leg
LENGTH, BAY = 15000.0, 1500.0
FX = [i * BAY for i in range(int(LENGTH / BAY) + 1)]          # 11 frames
N_CELL = 10
PX = [i * SPAN / N_CELL for i in range(N_CELL + 1)]           # purlins @ 670
MX = [x + BAY / 2 for x in FX[:-1]]                           # mid-bay glazing bars -> 750 x 670 cells
B = 80.0
PL_T = 12.0
PH = 500.0                      # leg below the top of the parapet (= parapet height)
YE, YR = 600.0, 1100.0          # eave node, ridge node (centre lines) above the parapet
YS = 100.0                      # side sill rail centre line
SLOPE = math.atan((YR - YE) / (SPAN / 2))
OVERHANG, SHEET_T = 100.0, 16.0
COPE_W, COPE_H, BRICK = 400.0, 100.0, 240.0
WIN_W, WIN_H = BAY - B, (YE - B / 2) - (YS + B / 2)            # 1420 x 420
CX = (4 * SPAN / N_CELL, 6 * SPAN / N_CELL)                    # collar tie ends (purlin nodes 4 and 6)


def top_y(x):
    return YE + (YR - YE) * (1 - abs(x - SPAN / 2) / (SPAN / 2))


def top_face(x):
    return top_y(x) + B / 2 / math.cos(SLOPE)


def slope_pt(x, d):
    s = -1 if x > SPAN / 2 else 1
    return (x - math.sin(SLOPE) * s * d, top_y(x) + math.cos(SLOPE) * d)


def band(pts, w=B):
    return LineString(pts).buffer(w / 2, cap_style=2, join_style=2)


def frame_outline():
    off = B / 2 / math.cos(SLOPE)
    env = Polygon([(-B / 2, -PH + PL_T), (SPAN + B / 2, -PH + PL_T),
                   (SPAN + B / 2, top_y(SPAN) + off - B / 2 * math.tan(SLOPE)),
                   (SPAN / 2, YR + off), (-B / 2, YE + off - B / 2 * math.tan(SLOPE))])
    g = unary_union([band([(0, -PH + PL_T), (0, YE + 200)]), band([(SPAN, -PH + PL_T), (SPAN, YE + 200)]),
                     band([(0, YE), (SPAN / 2, YR), (SPAN, YE)]),
                     band([(CX[0], top_y(CX[0])), (CX[1], top_y(CX[1]))])])
    return g.intersection(env)


def house(v, ax_, side, depth=1050, drop=350):
    """Brick parapet with overhanging coping on the RC roof slab; top of coping = ±0.00."""
    x_far = ax_ + side * depth
    cap = [(ax_ - COPE_W / 2, 0), (ax_ + COPE_W / 2, 0), (ax_ + COPE_W / 2, -COPE_H), (ax_ - COPE_W / 2, -COPE_H)]
    v.pline(cap, "A-CONC", closed=True); v.hatch(cap, spacing=1.0)
    br = [(ax_ - BRICK / 2, -COPE_H), (ax_ + BRICK / 2, -COPE_H), (ax_ + BRICK / 2, -PH), (ax_ - BRICK / 2, -PH)]
    v.pline(br, "A-CONC", closed=True); v.hatch(br, spacing=1.0, angle=-45)
    xo = ax_ - side * BRICK / 2
    slab = [(xo, -PH), (x_far, -PH), (x_far, -PH - 200), (xo, -PH - 200)]
    v.pline(slab, "A-CONC", closed=True); v.hatch(slab, spacing=1.6)
    w = [(xo, -PH - 200), (xo + side * 390, -PH - 200), (xo + side * 390, -PH - drop), (xo, -PH - drop)]
    v.pline([w[0], w[3]], "A-CONC"); v.pline([w[1], w[2]], "A-CONC")
    v.hatch(w, spacing=1.2, angle=-45)
    v.line((x_far, -PH + 30), (x_far, -PH - 230), "S-STEEL-THIN")


def square(v, c, ang, layer="S-STEEL-THIN"):
    sq = [(c[0] + dx * math.cos(ang) - dy * math.sin(ang), c[1] + dx * math.sin(ang) + dy * math.cos(ang))
          for dx, dy in ((-B / 2, -B / 2), (B / 2, -B / 2), (B / 2, B / 2), (-B / 2, B / 2))]
    v.line(sq[0], sq[2], layer); v.line(sq[1], sq[3], layer)


slope_txt = f"{math.degrees(SLOPE):.1f}° (1:{SPAN / 2 / (YR - YE):.1f})"

# ======================================================================= TOP VIEW 1:50
P = View("TOP VIEW", 50, (55, 400), (0, 20000), f"frames @ 1.50 m, cells {BAY / 2 / 1000:.2f} x {SPAN / N_CELL / 1000:.2f} m")
P.title_xy = (35, 578)
for y0, y1, name in ((-900, LEG_OFF - COPE_W / 2, "HOUSE 1 - ROOF"),
                     (SPAN - LEG_OFF + COPE_W / 2, SPAN + 900, "HOUSE 2 - ROOF")):
    P.fill([(-1000, y0), (LENGTH + 1000, y0), (LENGTH + 1000, y1), (-1000, y1)], color="#ececec")
    P.text((LENGTH / 2, (y0 + y1) / 2 + (-150 if y0 < 0 else 150)), name, 2.6, "center", "center", bold=True)
for yc in (LEG_OFF, SPAN - LEG_OFF):
    for yy in (yc - COPE_W / 2, yc + COPE_W / 2):
        outer = (yc < SPAN / 2 and yy < yc) or (yc > SPAN / 2 and yy > yc)
        P.line((-1000, yy), (LENGTH + 1000, yy), "A-CONC" if outer else "S-HIDDEN")
roof = [(-40, -OVERHANG), (LENGTH + 40, -OVERHANG), (LENGTH + 40, SPAN + OVERHANG), (-40, SPAN + OVERHANG)]
P.fill(roof, alpha=0.55, color="#555b60")
P.shape(unary_union([box(x - B / 2, -B / 2, x + B / 2, SPAN + B / 2) for x in FX] +
                    [box(FX[0], y - B / 2, FX[-1], y + B / 2) for y in PX] +
                    [box(x - B / 2, 0, x + B / 2, SPAN) for x in MX]), "S-STEEL")
P.pline(roof, "A-GLAZ", closed=True)
P.line((-40, SPAN / 2), (LENGTH + 40, SPAN / 2), "A-ALU")
for a, b in ((FX[0], FX[1]), (FX[-2], FX[-1])):
    for y0, y1 in ((0, SPAN / 2), (SPAN / 2, SPAN)):
        P.line((a + 60, y0 + 60), (b - 60, y1 - 60), "S-BRACE")
        P.line((a + 60, y1 - 60), (b - 60, y0 + 60), "S-BRACE")
for x in FX:
    for y in (0, SPAN):
        P.pline([(x - 100, y - 100), (x + 100, y - 100), (x + 100, y + 100), (x - 100, y + 100)],
                "S-STEEL-THIN", closed=True)
xm = BAY * 5.5
for y0, y1 in ((SPAN / 2 - 300, 700), (SPAN / 2 + 300, SPAN - 700)):
    P.line((xm, y0), (xm, y1), "A-TEXT")
    s = 1 if y1 > y0 else -1
    P.pline([(xm, y1 + s * 350), (xm - 120, y1), (xm + 120, y1)], "A-TEXT", closed=True)
    P.text((xm + 250, (y0 + y1) / 2), f"FALL {slope_txt}", 2.2, "left", "center", 90 if s < 0 else -90)
P.text((BAY * 8.5, SPAN / 2 + 110), "RIDGE", 2.2, "center", "bottom", layer="A-ALU", bold=True)
P.leader((BAY * 0.5, SPAN * 0.25 - 400), (BAY * 1.5, -650), "Ø12 rod X-bracing in end bays, both slopes", 2.0)
P.leader((BAY * 2.5, SPAN - 450), (BAY * 0.3, SPAN + 600),
         "16 mm multiwall polycarbonate, BLACK (smoke) tint, ribs down the slope", 2.0, "left")
P.leader((BAY * 8.5, SPAN), (BAY * 8.6, SPAN + 600), "vent windows, both 15 m sides", 2.0, "left")
for i, x in enumerate(FX):
    P.grid((x, -1250), (x, SPAN + 1200), str(i + 1))
P.grid((-1600, 0), (LENGTH + 400, 0), "A")
P.grid((-1600, SPAN), (LENGTH + 400, SPAN), "B")
P.dim_chain([(x, SPAN + 1100) for x in FX], 0, h=2.0)
P.dim_chain([(x, SPAN + 500) for x in sorted(FX[:3] + MX[:2])], 0, h=1.7)
P.dim((FX[0], SPAN + 1100), (FX[-1], SPAN + 1100), 6, f"{LENGTH:.0f}  (11 frames, 10 bays @ 1500)")
P.dim_chain([(LENGTH + 700, y) for y in PX], 0, h=1.7)
P.dim((LENGTH + 700, 0), (LENGTH + 700, SPAN), -7, f"{SPAN:.0f}  leg axes  ({N_CELL} cells @ {SPAN / N_CELL:.0f})")

# ======================================================================= FRONT VIEW 1:25
S = View("FRONT VIEW", 25, (118, 286), (0, 0), "across the width - typical frame, 11 No.")
S.title_xy = (35, 358)
house(S, LEG_OFF, -1)
house(S, SPAN - LEG_OFF, +1)
S.text((-390, -PH + 190), "HOUSE 1\nROOF", 2.3, "center", "center", bold=True)
S.text((SPAN + 390, -PH + 190), "HOUSE 2\nROOF", 2.3, "center", "center", bold=True)
S.text((SPAN / 2, -1150), "COURTYARD BELOW", 2.4, "center", "center", layer="A-DIM", bold=True)
for pts in ([(0, -PH + PL_T), (0, YE)], [(SPAN, -PH + PL_T), (SPAN, YE)], [(0, YE), (SPAN / 2, YR), (SPAN, YE)]):
    S.pline(pts, "S-CENTER")
S.shape(frame_outline(), "S-STEEL")
S.line((CX[0], top_y(CX[0])), (CX[1], top_y(CX[1])), "S-CENTER")
for x in (0, SPAN):  # knee gusset plates
    s = 1 if x == 0 else -1
    S.pline([(x + s * B / 2, YE - 60), (x + s * 260, YE - 8), (x + s * 260, top_y(x + s * 260) - B / 2 / math.cos(SLOPE)),
             (x + s * B / 2, YE + 20)], "S-STEEL-THIN", closed=True)
# purlins and sill rails in section
for x in PX:
    ang = 0 if x == SPAN / 2 else SLOPE * (1 if x < SPAN / 2 else -1)
    square(S, (x, top_y(x)), ang)
for x in (0, SPAN):
    square(S, (x, YS), 0)
    s = -1 if x == 0 else 1      # vent window, outside face of the leg
    S.pline([(x + s * B / 2, YS + B / 2), (x + s * (B / 2 + 50), YS + B / 2),
             (x + s * (B / 2 + 50), YE - B / 2), (x + s * B / 2, YE - B / 2)], "A-ALU")
    S.line((x + s * (B / 2 + 25), YS + B / 2 + 10), (x + s * (B / 2 + 25), YE - B / 2 - 10), "A-GLAZ")
# base plates + anchors
for x in (0, SPAN):
    S.pline([(x - 100, -PH), (x + 100, -PH), (x + 100, -PH + PL_T), (x - 100, -PH + PL_T)], "S-STEEL", closed=True)
    for a in (-70, 70):
        S.line((x + a, -PH + PL_T + 15), (x + a, -PH - 110), "S-HIDDEN")
# polycarbonate + ridge cap
for side in (-1, 1):
    x0 = 0 if side < 0 else SPAN
    a = (x0 + side * OVERHANG, top_face(x0) - OVERHANG * math.tan(SLOPE))
    xr = SPAN / 2 + side * 25
    b = (xr, top_face(xr))
    nx, ny = (math.sin(SLOPE) * side, math.cos(SLOPE))
    pts = [a, b, (b[0] + nx * SHEET_T, b[1] + ny * SHEET_T), (a[0] + nx * SHEET_T, a[1] + ny * SHEET_T)]
    S.fill(pts, color="#3a3f44"); S.pline(pts, "A-GLAZ", closed=True)
cap_h = top_face(SPAN / 2) + SHEET_T
S.pline([(SPAN / 2 - 170, cap_h - 170 * math.tan(SLOPE) + 6), (SPAN / 2, cap_h + 22),
         (SPAN / 2 + 170, cap_h - 170 * math.tan(SLOPE) + 6)], "A-ALU")
# labels
S.leader(slope_pt(1700, 48), (1500, 1560), "16 mm multiwall polycarbonate", 2.2, "right")
S.leader((SPAN / 2 + 60, cap_h + 15), (3800, 1560), "aluminium ridge cap", 2.2)
S.leader(slope_pt(4700, 0), (5100, 1350), "RAFTER  SHS 80x80x5", 2.2)
S.leader((PX[2], top_y(PX[2]) + 20), (650, 1300), f"PURLINS SHS 80x80x2 @ {SPAN / N_CELL:.0f}", 2.0, "right")
S.leader((SPAN / 2 + 300, top_y(CX[0]) - B / 2), (3900, 400),
         f"COLLAR TIE SHS 80x80x2, L={CX[1] - CX[0]:.0f}, welded under the rafters", 2.0, "left")
S.leader((B / 2 + 150, YE - 30), (1000, 400), "knee gusset PL 8, both faces", 2.0, "left")
S.leader((-B / 2 - 50, 350), (-650, 820), f"VENT WINDOW {WIN_W:.0f}x{WIN_H:.0f}\nalu. top-hung + mesh", 2.0)
S.leader((-B / 2, 200), (-800, 450), "LEG  SHS 80x80x5", 2.0)
S.leader((-60, -PH + PL_T / 2), (-800, -250), "BASE PL 200x200x12\n4 M12 into roof slab", 2.0)
S.leader((SPAN - LEG_OFF + 120, -300), (SPAN - 1250, -400), "PARAPET + overhanging coping: NOT loaded", 2.0, "right")
S.leader((SPAN - B / 2, YS), (SPAN - 900, 120), "SILL RAIL 80x80x2", 2.0, "right")
# dims and levels
S.dim_chain([(x, -PH) for x in PX], -5, h=1.6)
S.dim((0, -PH), (SPAN, -PH), -15, f"{SPAN:.0f}  leg axes")
S.dim((LEG_OFF, -PH), (SPAN - LEG_OFF, -PH), -10, f"{PAR_AX:.0f}  parapet axes (verify on site)")
S.dim((0, -PH), (LEG_OFF, -PH), -10)
S.dim((SPAN - LEG_OFF, -PH), (SPAN, -PH), -10)
S.dim_chain([(SPAN + 450, -PH), (SPAN + 450, 0), (SPAN + 450, YE), (SPAN + 450, YR)], -4)
S.level(-160, 0, "±0.00 top of parapet", -1)
S.level(-700, -PH, f"-{PH / 1000:.2f} house roof", -1)
S.level(SPAN / 2 - 30, YR + 300, f"+{(top_face(SPAN / 2) + SHEET_T) / 1000:.2f} ridge", -1)
S.text((1900, top_face(1900) + 70), f"slope {slope_txt}", 2.2, "center", "bottom", math.degrees(SLOPE), "A-DIM")

# ======================================================================= SIDE VIEW 1:50
E_ = View("SIDE VIEW", 50, (55, 152), (0, -6000), "along the 15 m - vent windows in every bay")
E_.title_xy = (35, 210)
cap = [(-500, 0), (LENGTH + 500, 0), (LENGTH + 500, -COPE_H), (-500, -COPE_H)]
E_.pline(cap, "A-CONC", closed=True); E_.hatch(cap, spacing=1.0)
br = [(-500, -COPE_H), (LENGTH + 500, -COPE_H), (LENGTH + 500, -PH), (-500, -PH)]
E_.pline(br, "A-CONC", closed=True); E_.hatch(br, spacing=1.6, angle=-45)
roofE = [(-40, top_face(0) - OVERHANG * math.tan(SLOPE)), (LENGTH + 40, top_face(0) - OVERHANG * math.tan(SLOPE)),
         (LENGTH + 40, top_face(SPAN / 2) + SHEET_T), (-40, top_face(SPAN / 2) + SHEET_T)]
E_.fill(roofE, color="#6b7177"); E_.pline(roofE, "A-GLAZ", closed=True)
for x in FX:
    E_.line((x - B / 2, -PH), (x - B / 2, 0), "S-HIDDEN"); E_.line((x + B / 2, -PH), (x + B / 2, 0), "S-HIDDEN")
E_.shape(unary_union([box(x - B / 2, 0, x + B / 2, YE + B / 2) for x in FX] +
                     [box(FX[0], YS - B / 2, FX[-1], YS + B / 2), box(FX[0], YE - B / 2, FX[-1], YE + B / 2)]),
         "S-STEEL")
for a, b in zip(FX, FX[1:]):
    x0, x1, y0, y1 = a + B / 2 + 15, b - B / 2 - 15, YS + B / 2 + 15, YE - B / 2 - 15
    E_.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "A-ALU", closed=True)
    E_.pline([(x0 + 30, y0 + 20), ((x0 + x1) / 2, y1 - 20), (x1 - 30, y0 + 20)], "A-GLAZ")   # top-hung symbol
for i, x in enumerate(FX):
    E_.grid((x, 1750), (x, top_face(SPAN / 2) + 60), str(i + 1), at_start=True)
E_.dim_chain([(x, -PH) for x in FX], -4, h=2.0)
E_.dim_chain([(LENGTH + 500, -PH), (LENGTH + 500, 0), (LENGTH + 500, YE), (LENGTH + 500, top_face(SPAN / 2) + SHEET_T)],
             -4, h=2.0)
E_.text((BAY * 5, -PH / 2), "legs behind the parapet (dashed)", 2.0, "center", "center", layer="A-DIM")
E_.leader((BAY * 0.5, (YS + YE) / 2), (BAY * 0.2, -1900), f"VENT WINDOW {WIN_W:.0f}x{WIN_H:.0f} alu. top-hung + mesh",
          2.0, "left")
E_.leader((BAY * 4.5, YS), (BAY * 4.4, -1900), "SILL RAIL 80x80x2", 2.0, "left")
E_.leader((BAY * 7.5, YE), (BAY * 7.0, -1900), "EAVE PURLIN 80x80x2", 2.0, "left")
E_.leader((BAY * 9.4, -300), (BAY * 9.4, -1900), "PARAPET", 2.0, "left")

# ======================================================================= 3D VIEW
iso = View("3D VIEW", 1, (0, 0), (25000, -6000), "not to scale")
iso.title_xy = (440, 578)
k = 1 / 68.0
c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))


def pj(x, y, z):
    return ((x * c30 - y * c30) * k, (x * s30 + y * s30 + z) * k)


def box3(x0, x1, y0, y1, z0, z1, layer="A-CONC"):
    for z in (z0, z1):
        iso.pline([pj(x0, y0, z), pj(x1, y0, z), pj(x1, y1, z), pj(x0, y1, z)], layer, closed=True)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        iso.line(pj(x, y, z0), pj(x, y, z1), layer)


for yc in (LEG_OFF, SPAN - LEG_OFF):
    box3(-800, LENGTH + 800, yc - COPE_W / 2, yc + COPE_W / 2, -PH, 0)
for y0, y1 in ((-1800, LEG_OFF + BRICK / 2), (SPAN - LEG_OFF - BRICK / 2, SPAN + 1800)):
    for z in (-PH, -PH - 1500):
        iso.pline([pj(-800, y0, z), pj(LENGTH + 800, y0, z), pj(LENGTH + 800, y1, z), pj(-800, y1, z)],
                  "A-CONC", closed=True)
    for x, y in ((-800, y0), (LENGTH + 800, y0), (LENGTH + 800, y1), (-800, y1)):
        iso.line(pj(x, y, -PH), pj(x, y, -PH - 1500), "A-CONC")
for ye in (0, SPAN):
    iso.fill([pj(0, ye, YE), pj(LENGTH, ye, YE), pj(LENGTH, SPAN / 2, YR), pj(0, SPAN / 2, YR)],
             alpha=0.6, color="#4a5056")
    iso.fill([pj(0, ye, YS), pj(LENGTH, ye, YS), pj(LENGTH, ye, YE), pj(0, ye, YE)], alpha=0.35, color="#c9e9c9")
for x in FX:
    iso.pline([pj(x, 0, -PH), pj(x, 0, YE), pj(x, SPAN / 2, YR), pj(x, SPAN, YE), pj(x, SPAN, -PH)], "S-STEEL")
    iso.line(pj(x, CX[0], top_y(CX[0])), pj(x, CX[1], top_y(CX[1])), "S-STEEL-THIN")
for y in PX:
    iso.line(pj(0, y, top_y(y)), pj(LENGTH, y, top_y(y)), "S-STEEL-THIN")
for x in MX:
    iso.pline([pj(x, 0, YE), pj(x, SPAN / 2, YR), pj(x, SPAN, YE)], "S-STEEL-THIN")
for y in (0, SPAN):
    iso.line(pj(0, y, YS), pj(LENGTH, y, YS), "S-STEEL-THIN")
for a, b in ((FX[0], FX[1]), (FX[-2], FX[-1])):
    for y0, y1 in ((0, SPAN / 2), (SPAN / 2, SPAN)):
        iso.line(pj(a, y0, top_y(y0)), pj(b, y1, top_y(y1)), "S-BRACE")
        iso.line(pj(a, y1, top_y(y1)), pj(b, y0, top_y(y0)), "S-BRACE")
iso.text(pj(LENGTH + 800, -1000, -PH - 700), "HOUSE 1", 2.6, "left", "center", bold=True)
iso.text(pj(-800, SPAN + 1000, -PH - 700), "HOUSE 2", 2.6, "right", "center", bold=True)
_all = [p for it in iso.items if it[0] in ("pl", "fill") for p in it[1]]
_x0, _x1 = min(p[0] for p in _all), max(p[0] for p in _all)
_y0, _y1 = min(p[1] for p in _all), max(p[1] for p in _all)
iso.px, iso.py = 636 - (_x0 + _x1) / 2, 385 - (_y0 + _y1) / 2

views = [P, S, E_, iso]

# ======================================================================= sheet
W, H = 841, 594
LW = 72 / 25.4


def frame(ax):
    ax.add_patch(plt.Rectangle((20, 10), W - 30, H - 20, fill=False, lw=0.7 * LW))
    ax.add_patch(plt.Rectangle((10, 5), W - 15, H - 10, fill=False, lw=0.25 * LW))
    for v in views:
        tx, ty = v.title_xy
        ax.text(tx, ty, v.title, fontsize=11.9, weight="bold", ha="left", va="bottom")
        ax.plot([tx, tx + 9 + 2.35 * len(v.title)], [ty - 1.2, ty - 1.2], color="k", lw=0.5 * LW)
        sub = (f"SCALE 1:{v.scale:.0f}   " if v.scale > 1 else "") + v.sub
        ax.text(tx, ty - 2.5, sub, fontsize=6.8, ha="left", va="top")


LEGEND = [
    ("MEMBERS", ""),
    ("Frames (11 No. @ 1.50 m): legs + rafters", "SHS 80x80x5"),
    ("Collar tie under the ridge, every frame", f"SHS 80x80x2, L={CX[1] - CX[0]:.0f}"),
    ("Knee gussets, every frame", "PL 8 both faces"),
    (f"Purlins ({N_CELL + 1} lines @ {SPAN / N_CELL:.0f}), mid-bay bars, sill rails", "SHS 80x80x2"),
    ("Bracing, end bays, roof plane", "Ø12 rod"),
    ("Base plates (22 No.) on the house roof slab", "PL 200x200x12 + 4 M12 chem."),
    ("Glazing (roof + windows)", "BLACK / smoke tint, 16 mm multiwall PC"),
    ("Vent windows (20 No.) on both 15 m sides", f"{WIN_W:.0f} x {WIN_H:.0f} alu. top-hung"),
    ("Legs drop 0.5 m past the parapet onto the house roof; parapet not loaded", ""),
    ("", ""),
    (f"Span {SPAN / 1000:.2f} m leg to leg  |  slope {math.degrees(SLOPE):.1f}°  |  "
     f"cells {BAY / 2000:.2f} x {SPAN / N_CELL / 1000:.2f} m", ""),
    ("Dimensions in mm, levels in m (±0.00 = top of parapet)", ""),
]


def legend(ax):
    x0, y = 440, 112
    for i, (a, b) in enumerate(LEGEND):
        ax.text(x0, y, a, fontsize=(3.0 if i == 0 else 2.4) * LW, va="top", weight="bold" if i == 0 else "normal")
        ax.text(x0 + 100, y, b, fontsize=2.4 * LW, va="top")
        y -= 5.6 if i == 0 else 4.6


def title_block(ax):
    x0, y0, x1, y1 = 633, 10, 831, 62
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=0.5 * LW))
    for y in (50, 36, 24):
        ax.plot([x0, x1], [y, y], color="k", lw=0.25 * LW)
    ax.plot([732, 732], [y0, 36], color="k", lw=0.25 * LW)
    ax.text(x0 + 3, 59, "PROJECT", fontsize=1.8 * LW, va="top", color="#555")
    ax.text(x0 + 3, 55.5, "SKYLIGHT ROOF BETWEEN TWO HOUSES  6.00 x 15.00 m", fontsize=3.0 * LW, va="top",
            weight="bold")
    ax.text(x0 + 3, 47.5, "DRAWING", fontsize=1.8 * LW, va="top", color="#555")
    ax.text(x0 + 3, 44, "STEEL FRAMES SHS 80x80 + POLYCARBONATE\n3D VIEW, TOP, FRONT AND SIDE VIEWS",
            fontsize=2.4 * LW, va="top")
    for (x, lab, val) in ((x0 + 3, "SCALE", "AS SHOWN @ A1"), (735, "SHEET", "S-01")):
        ax.text(x, 33.5, lab, fontsize=1.8 * LW, va="top", color="#555")
        ax.text(x, 30, val, fontsize=3.0 * LW, va="top", weight="bold")
    for (x, lab, val) in ((x0 + 3, "DATE", "2026-11-06"), (735, "REV", "3  - cells 750x670, black glazing")):
        ax.text(x, 21.5, lab, fontsize=1.8 * LW, va="top", color="#555")
        ax.text(x, 18, val, fontsize=2.6 * LW, va="top")


if __name__ == "__main__":
    draw_pdf(views, [frame, legend, title_block], "SKYLIGHT_6x15.pdf")
    draw_dxf(views, "SKYLIGHT_6x15.dxf")
    print("done")
