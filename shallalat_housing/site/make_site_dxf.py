"""Site plan of plot 157 / district 53 Baybokht (Nineveh), drawn from the four corner coordinates.

Everything on the BOUNDARY / CORNERS / DIMS layers comes from the UTM 38S coordinates printed on the
cadastral map. Layers ending in _APPROX are traced from the scanned map through an affine fit of the
four corners (residual < 2 m) and are for orientation only.
"""
import math
import os

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = "site_scan.png"
OUT = os.path.join(HERE, "SHALLALAT_SITE_PLAN.dxf")

# UTM zone 38S, metres. Order: NW, NE, SE, SW (map orientation; true axis runs WNW -> ESE)
P = {
    "P1": (338954.0, 4035462.0),
    "P2": (339032.0, 4035771.0),
    "P3": (339836.0, 4035336.0),
    "P4": (339747.0, 4035198.0),
}
ANNOUNCED_M2 = 79 * 2500 + 16 * 100 + 75  # 79 dunam 16 olk 75 m2

# corners as picked on the scan (pixels, y down) -> affine to UTM
PIX = np.array([(259.3, 156), (468.3, 119.3), (395, 731.7), (290, 712.3)])
A = np.linalg.lstsq(np.c_[PIX, np.ones(4)], np.array(list(P.values())), rcond=None)[0]


def px(x, y):
    return tuple(np.array([x, y, 1.0]) @ A)


def area(pts):
    s = 0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def bearing(a, b):
    """Whole-circle bearing from grid north, degrees."""
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360


def dms(d):
    deg = int(d)
    m = (d - deg) * 60
    return f"{deg}%%d{int(m):02d}'{(m - int(m)) * 60:04.1f}\""


def unit(a, b):
    v = np.subtract(b, a)
    return v / np.linalg.norm(v)


def offset_line(a, b, dist, ext=0.0):
    """Line a-b moved `dist` to its left, extended `ext` past both ends."""
    u = unit(a, b)
    n = np.array([-u[1], u[0]])
    return tuple(np.add(a, n * dist - u * ext)), tuple(np.add(b, n * dist + u * ext))


def intersect(p1, p2, p3, p4):
    d1, d2 = np.subtract(p2, p1), np.subtract(p4, p3)
    w = np.subtract(p3, p1)
    t = (w[0] * d2[1] - w[1] * d2[0]) / (d1[0] * d2[1] - d1[1] * d2[0])
    return tuple(np.add(p1, d1 * t))


doc = ezdxf.new("R2018", setup=True)
doc.header["$INSUNITS"] = 6  # metres
doc.header["$LUNITS"] = 2
doc.header["$LUPREC"] = 2
doc.styles.add("AR", font="arial.ttf")
msp = doc.modelspace()

LAYERS = {
    "BOUNDARY": (1, 50),
    "CORNERS": (7, 25),
    "DIMS": (3, 18),
    "TEXT": (7, 18),
    "GRID": (8, 9),
    "NORTH": (7, 25),
    "ROADS_APPROX": (8, 25),
    "WATER_APPROX": (5, 35),
    "TREES_APPROX": (3, 13),
    "SCAN_UNDERLAY": (7, 0),
}
for name, (color, lw) in LAYERS.items():
    doc.layers.add(name, color=color, lineweight=lw)

pts = list(P.values())
names = list(P.keys())
centroid = tuple(np.mean(pts, axis=0))

# --- boundary --------------------------------------------------------------------------------------
msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "BOUNDARY", "const_width": 0.6})

# --- corners ---------------------------------------------------------------------------------------
for n, p in P.items():
    msp.add_point(p, dxfattribs={"layer": "CORNERS"})
    msp.add_circle(p, 2.0, dxfattribs={"layer": "CORNERS"})
    away = unit(centroid, p)
    tp = np.add(p, away * 14)
    align = TextEntityAlignment.MIDDLE_LEFT if away[0] >= 0 else TextEntityAlignment.MIDDLE_RIGHT
    msp.add_text(n, height=6, dxfattribs={"layer": "CORNERS", "style": "AR"}).set_placement(
        (tp[0], tp[1] + 5), align=align
    )
    msp.add_text(f"E {p[0]:.2f}  N {p[1]:.2f}", height=3.5, dxfattribs={"layer": "CORNERS", "style": "AR"}).set_placement(
        (tp[0], tp[1] - 3), align=align
    )

# --- edge dimensions -------------------------------------------------------------------------------
dim = doc.dimstyles.new("SITE_M")
dim.dxf.dimtxt = 4.0
dim.dxf.dimasz = 3.0
dim.dxf.dimdec = 2
dim.dxf.dimexo = 1.5
dim.dxf.dimexe = 1.5
dim.dxf.dimgap = 1.0
dim.dxf.dimtad = 1
dim.dxf.dimtxsty = "AR"
dim.dxf.dimpost = "<> m"
edges = []
for i in range(4):
    a, b = pts[i], pts[(i + 1) % 4]
    L = math.dist(a, b)
    edges.append((f"{names[i]}-{names[(i + 1) % 4]}", L, bearing(a, b)))
    u = unit(a, b)
    n = np.array([-u[1], u[0]])
    mid = np.add(a, b) / 2
    outward = 1 if np.dot(n, np.subtract(mid, centroid)) > 0 else -1
    msp.add_aligned_dim(p1=a, p2=b, distance=outward * 30, dimstyle="SITE_M", dxfattribs={"layer": "DIMS"}).render()

# --- approximate context traced from the scan ------------------------------------------------------
P1, P2, P3, P4 = pts
ROAD_W = 12.0  # read off the scan (~8 px x 1.5 m/px); confirm on site
# the scan shows the long-side roads running outside the red line
for a, b in ((P4, P1), (P2, P3)):  # left of a->b is outside the plot for both
    for d in (0.0, ROAD_W):
        s, e = offset_line(a, b, d, ext=60)
        msp.add_line(s, e, dxfattribs={"layer": "ROADS_APPROX"})
    s, e = offset_line(a, b, ROAD_W / 2, ext=60)
    msp.add_line(s, e, dxfattribs={"layer": "ROADS_APPROX", "linetype": "CENTER"})
# cross road near the north end, inside the red line
cr_a, cr_b = px(267, 251), px(455, 214)
CROSS_W = 10.0
for d in (-CROSS_W / 2, CROSS_W / 2):
    s, e = offset_line(cr_a, cr_b, d, ext=0)
    msp.add_line(intersect(s, e, P1, P4), intersect(s, e, P2, P3), dxfattribs={"layer": "ROADS_APPROX"})
cl0, cl1 = intersect(cr_a, cr_b, P1, P4), intersect(cr_a, cr_b, P2, P3)
msp.add_line(cl0, cl1, dxfattribs={"layer": "ROADS_APPROX", "linetype": "CENTER"})
# watercourse / valley near the south end
wc = [px(x, y) for x, y in [(200, 603), (240, 606), (283, 608), (333, 607), (373, 598), (413, 599), (467, 620), (520, 637)]]
msp.add_spline(wc, dxfattribs={"layer": "WATER_APPROX"})
for d in (-4, 4):
    msp.add_spline([tuple(np.add(q, (0, d))) for q in wc], dxfattribs={"layer": "WATER_APPROX", "linetype": "DASHED"})
# existing trees north of the cross road
for x, y in [(310, 170), (355, 165), (395, 178), (300, 196), (343, 194), (385, 205), (420, 190)]:
    msp.add_circle(px(x, y), 4, dxfattribs={"layer": "TREES_APPROX"})


def label(text, at, h=5, rot=0.0, layer="TEXT"):
    t = msp.add_text(text, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "AR"})
    t.set_placement(at, align=TextEntityAlignment.MIDDLE_CENTER)


long_rot = math.degrees(math.atan2(P4[1] - P1[1], P4[0] - P1[0]))
across_rot = math.degrees(math.atan2(cl1[1] - cl0[1], cl1[0] - cl0[0]))
w_mid = offset_line(P4, P1, ROAD_W / 2)
label("ROAD (APPROX. 12 m) - شارع", tuple(np.mean(w_mid, axis=0)), 4, long_rot, "ROADS_APPROX")
e_mid = offset_line(P2, P3, ROAD_W / 2)
e_rot = math.degrees(math.atan2(P3[1] - P2[1], P3[0] - P2[0]))
label("ROAD (APPROX. 12 m) - شارع", tuple(np.mean(e_mid, axis=0)), 4, e_rot, "ROADS_APPROX")
label("CROSS ROAD (APPROX.) - شارع عرضي", tuple(np.add(np.mean([cl0, cl1], axis=0), (0, 0))), 3.5, across_rot, "ROADS_APPROX")
wc_mid = wc[3]
label("WATERCOURSE (APPROX.) - مجرى مائي", tuple(np.add(wc_mid, (0, 14))), 4, across_rot, "WATER_APPROX")
label("EXISTING TREES (APPROX.) - أشجار قائمة", px(360, 185), 4, across_rot, "TREES_APPROX")
label("PLOT 157 - القطعة 157", (centroid[0], centroid[1] + 12), 10, long_rot)
label("مقاطعة 53 بايبوخت - DISTRICT 53 BAYBOKHT", (centroid[0], centroid[1] - 4), 6, long_rot)

# --- UTM grid --------------------------------------------------------------------------------------
xs, ys = zip(*pts)
gx0, gx1 = int(min(xs) // 100 * 100) - 100, int(max(xs) // 100 * 100) + 200
gy0, gy1 = int(min(ys) // 100 * 100) - 100, int(max(ys) // 100 * 100) + 200
for x in range(gx0, gx1 + 1, 100):
    msp.add_line((x, gy0), (x, gy1), dxfattribs={"layer": "GRID"})
    msp.add_text(f"E {x}", height=4, rotation=90, dxfattribs={"layer": "GRID", "style": "AR"}).set_placement(
        (x - 2, gy0 + 4), align=TextEntityAlignment.BOTTOM_LEFT
    )
for y in range(gy0, gy1 + 1, 100):
    msp.add_line((gx0, y), (gx1, y), dxfattribs={"layer": "GRID"})
    msp.add_text(f"N {y}", height=4, dxfattribs={"layer": "GRID", "style": "AR"}).set_placement(
        (gx0 + 4, y + 2), align=TextEntityAlignment.BOTTOM_LEFT
    )

# --- north arrow + scale bar -----------------------------------------------------------------------
nx, ny = gx1 - 60, gy1 - 90
msp.add_lwpolyline([(nx, ny), (nx - 10, ny - 25), (nx, ny + 30), (nx + 10, ny - 25)], close=True, dxfattribs={"layer": "NORTH"})
msp.add_hatch(color=7, dxfattribs={"layer": "NORTH"}).paths.add_polyline_path([(nx, ny), (nx, ny + 30), (nx + 10, ny - 25)])
label("N", (nx, ny + 42), 12, 0, "NORTH")
label("GRID NORTH - UTM 38S", (nx, ny - 36), 4, 0, "NORTH")
sx, sy = gx0 + 40, gy0 + 40
for i in range(5):
    seg = [(sx + i * 20, sy), (sx + (i + 1) * 20, sy), (sx + (i + 1) * 20, sy + 4), (sx + i * 20, sy + 4)]
    msp.add_lwpolyline(seg, close=True, dxfattribs={"layer": "NORTH"})
    if i % 2 == 0:
        msp.add_hatch(color=7, dxfattribs={"layer": "NORTH"}).paths.add_polyline_path(seg)
for i in range(0, 6):
    label(f"{i * 20}", (sx + i * 20, sy - 6), 4, 0, "NORTH")
label("SCALE (m)", (sx + 50, sy + 12), 4, 0, "NORTH")

# --- data table ------------------------------------------------------------------------------------
A_calc = area(pts)
dunam = int(A_calc // 2500)
olk = int((A_calc - dunam * 2500) // 100)
rem = A_calc - dunam * 2500 - olk * 100
rows = [
    "SITE DATA - بيانات الموقع",
    "Investment opportunity 5/2026 - NIC - Residential complex",
    "Plot 157 / District 53 Baybokht - Nineveh",
    "Coordinates: UTM WGS84 zone 38S (from cadastral map)",
    "",
    "CORNER    EASTING       NORTHING",
]
rows += [f"{n:<8}  {p[0]:.2f}   {p[1]:.2f}" for n, p in P.items()]
rows += ["", "EDGE      LENGTH (m)   BEARING"]
rows += [f"{n:<8}  {L:9.2f}    {dms(b)}" for n, L, b in edges]
rows += [
    "",
    f"AREA FROM COORDINATES : {A_calc:,.0f} m2 = {dunam} dunam {olk} olk {rem:.0f} m2",
    f"AREA IN ANNOUNCEMENT  : {ANNOUNCED_M2:,.0f} m2 = 79 dunam 16 olk 75 m2",
    f"DIFFERENCE            : {A_calc - ANNOUNCED_M2:,.0f} m2 ({(A_calc - ANNOUNCED_M2) / ANNOUNCED_M2:.1%})",
    "",
    "Layers *_APPROX are traced from the scanned map (affine fit, residual < 2 m):",
    "road widths, cross road, watercourse and trees must be confirmed by survey.",
]
tx, ty = gx0 - 330, gy1
for i, r in enumerate(rows):
    msp.add_text(r, height=5 if i == 0 else 3.6, dxfattribs={"layer": "TEXT", "style": "AR"}).set_placement(
        (tx, ty - i * 6.5), align=TextEntityAlignment.TOP_LEFT
    )

# --- scan underlay (georeferenced, off by default) -------------------------------------------------
img_def = doc.add_image_def(filename=SCAN, size_in_pixel=(642, 852))
img = msp.add_image(img_def, insert=px(0, 852), size_in_units=(642 * 1.5, 852 * 1.5), rotation=0,
                    dxfattribs={"layer": "SCAN_UNDERLAY"})
img.dxf.u_pixel = (A[0][0], A[0][1], 0)
img.dxf.v_pixel = (-A[1][0], -A[1][1], 0)
img.dxf.fade = 40
doc.layers.get("SCAN_UNDERLAY").off()

doc.saveas(OUT)
print(OUT)
print(f"area {A_calc:.1f} m2  ({dunam} dunam {olk} olk {rem:.0f} m2)")
for e in edges:
    print(e[0], f"{e[1]:.2f}", dms(e[2]))
for name, p in (("cross road W", cl0), ("cross road E", cl1)):
    print(name, f"{p[0]:.1f} {p[1]:.1f}", "from P1/P2:", f"{math.dist(p, P1 if 'W' in name else P2):.1f}")
print("watercourse at W edge from P4:", f"{math.dist(intersect(wc[1], wc[3], P1, P4), P4):.1f}",
      " at E edge from P3:", f"{math.dist(intersect(wc[4], wc[6], P2, P3), P3):.1f}")
