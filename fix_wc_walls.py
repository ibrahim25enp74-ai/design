"""Fix the PUBLIC TOILETS sheet (WC 1 + WC 2) in SOUQ_A3_SHEET_SET.dxf.

- completes the missing outer walls (WC 1 north / west / women's south wall,
  WC 2 west wall above the men's door) and trims wall openings to the doors
- rebuilds the cubicle walls as clean 20 cm walls with 0.70 door openings
  that match the drawn doors
- merges all walls of each plan into one clean outline (no overlapping lines)
"""
import sys

import ezdxf
from shapely.geometry import box, LineString, Polygon
from shapely.ops import unary_union

SRC, DST = sys.argv[1], sys.argv[2]
doc = ezdxf.readfile(SRC)
msp = doc.modelspace()

# Remove every existing wall polyline of the two WC plans.
REGION = (3605, 3660, 5, 28)
for e in list(msp.query('LWPOLYLINE[layer=="A-WALL"]')):
    pts = list(e.get_points("xy"))
    if all(REGION[0] < x < REGION[1] and REGION[2] < y < REGION[3] for x, y in pts):
        msp.delete_entity(e)

T = 0.20  # wall thickness

# ---------------------------------------------------------------- WC 1
wc1 = [
    # outer walls
    box(3614.14, 13.10, 3622.34, 23.30).difference(box(3614.34, 13.30, 3622.14, 23.10)),
    # men/women spine
    box(3618.14, 13.10, 3618.34, 23.30),
    # lobby / wet area walls, with doors 0.90
    box(3614.34, 15.61, 3618.14, 15.81).difference(box(3614.34, 15.61, 3615.29, 15.81)),
    box(3618.34, 15.61, 3622.14, 15.81).difference(box(3621.19, 15.61, 3622.14, 15.81)),
]
# 1.30 entrances from the souq corridor
wc1_openings = [box(3616.44, 13.10, 3617.74, 13.30), box(3618.74, 13.10, 3620.04, 13.30)]

wc1_part = []
door_y = [16.06, 17.56, 19.06, 20.55, 22.05]  # hinge of each 0.70 cubicle door
for xf, xb in ((3616.44, 3618.14), (3620.04, 3618.34)):  # front line, spine face
    ys = [15.81]
    for y in door_y:
        ys += [y, y + 0.70]
    ys.append(23.10)
    for a, b in zip(ys[::2], ys[1::2]):
        wc1_part.append(((xf, a), (xf, b)))
    for y in (17.21, 18.71, 20.20, 21.70):
        x0 = xf + (0.10 if xb < xf else -0.10)  # reach the outer face of the front wall
        wc1_part.append(((x0, y), (xb, y)))

# ---------------------------------------------------------------- WC 2
east = Polygon([(3647.86, 13.11), (3648.48, 18.31), (3648.68, 18.29), (3648.06, 13.09)])
wc2 = [
    box(3627.17, 18.10, 3648.50, 18.30),  # north
    box(3627.17, 13.10, 3647.95, 13.30),  # south
    east,
    box(3627.17, 14.30, 3637.84, 14.50),  # corridor wall
    box(3637.64, 13.10, 3637.84, 18.30),  # men / women divider
    box(3627.17, 14.30, 3627.37, 18.30),  # west wall
    box(3629.04, 15.01, 3629.24, 17.41),  # privacy screen
]
wc2_openings = [
    box(3627.17, 15.71, 3627.37, 16.71),  # men's door (1.00)
    box(3637.64, 13.30, 3637.84, 14.30),  # women's door from the corridor
]

wc2_part = []
y_front, y_back = 16.50, 18.10
for xs, x_end in (
    ([3630.54, 3631.94, 3633.34, 3634.74, 3636.14], 3637.64),
    ([3639.04, 3640.44, 3641.84, 3643.24, 3644.64, 3646.04, 3647.44], None),
):
    for x in xs:
        wc2_part.append(((x, y_front - 0.10), (x, y_back)))
    hinges = [x + 0.35 for x in xs[:-1]] if x_end is None else [x + 0.35 for x in xs]
    stop = x_end if x_end is not None else xs[-1]
    xs_front = [xs[0]]
    for h in hinges:
        xs_front += [h, h + 0.70]
    xs_front.append(stop)
    for a, b in zip(xs_front[::2], xs_front[1::2]):
        wc2_part.append(((a, y_front), (b, y_front)))


def write_walls(polys, openings):
    shape = unary_union(polys).difference(unary_union(openings))
    geoms = getattr(shape, "geoms", [shape])
    for g in geoms:
        for ring in [g.exterior, *g.interiors]:
            pts = list(ring.coords)[:-1]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-WALL"})


def cubicle_walls(segments):
    return [LineString([a, b]).buffer(T / 2, cap_style=2) for a, b in segments]


write_walls(wc1 + cubicle_walls(wc1_part), wc1_openings)
write_walls(wc2 + cubicle_walls(wc2_part), wc2_openings)

# The last men's cubicle in WC 2 now closes on the divider (clear 1.40).
for e in msp.query('LINE[layer=="DIM"]'):
    s, t = e.dxf.start, e.dxf.end
    if 18.4 < min(s.y, t.y) and max(s.y, t.y) < 19.5:
        if abs(s.x - 3637.44) < 0.02 and abs(t.x - 3637.44) < 0.02:
            e.dxf.start, e.dxf.end = (3637.64, s.y), (3637.64, t.y)
        elif abs(t.x - 3637.44) < 0.02:  # dimension line
            e.dxf.end = (3637.64, t.y)
        elif abs((s.x + t.x) / 2 - 3637.44) < 0.02:  # tick
            e.dxf.start, e.dxf.end = (s.x + 0.2, s.y), (t.x + 0.2, t.y)
for e in msp.query("TEXT"):
    if abs(e.dxf.insert.x - 3636.68) < 0.05 and abs(e.dxf.insert.y - 19.06) < 0.05:
        e.dxf.text = "1.40"
        e.dxf.insert = (e.dxf.insert.x + 0.1, e.dxf.insert.y)

doc.saveas(DST)
