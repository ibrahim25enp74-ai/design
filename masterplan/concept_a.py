"""Concept A - the spine. Driver: movement efficiency and phasing.

One 24 m boulevard on the plot's centreline carries every trip, every utility trunk and the civic
node at its midpoint; housing rows run parallel to the two long edges and hang off it through
short ribs. The cross road stays public (no approval risk) and becomes the gate frontage.
"""
from shapely.geometry import LineString, Polygon, box

import kit
import plot157 as P
from kit import NORTH, SOUTH, SITE, xcut


def yc(x):
    return (kit.SOUTH.pt(kit.SOUTH.s_at_x(x, 0), 0)[1] + kit.NORTH.pt(kit.NORTH.s_at_x(x, 0), 0)[1]) / 2


def build():
    p = kit.Plan("A", "The Spine", "المحور")
    W = kit.west_of_cross(5)          # everything west of the public cross road
    wadi = kit.wadi_corridor()
    E = kit.east_of_wadi()
    xr = kit.cross_road()

    # ------------------------------------------------ movement
    x_gate = 116.6 + 7
    x_end = 700.0
    spine = LineString([(x_gate - 8, yc(x_gate)), (x_end, yc(x_end))])
    p.road_line(spine, "blvd", "boulevard")
    p.road_line(P.ROAD_X_L, "public", "public cross road")        # kept public, 10 m
    # ribs: short cross streets from the spine to the edge-parallel local streets
    for x in (232, 340, 548):
        p.road([(x, kit.edge_y_s(x) + 30), (x, kit.edge_y_n(x) - 30)], "local")
    # east of the wadi: bridge continues as the east loop
    p.gate(x_gate, yc(x_gate), "main")
    p.gate(620, kit.edge_y_s(620), "service")

    # ------------------------------------------------ west of the cross road: public frontage
    p.service("cd", kit.rect_c(118, 40, 46, 44, -10.9).intersection(W))
    p.service("police", kit.rect_c(104, 80, 34, 36, -10.9).intersection(W))
    p.service("prep", kit.rect_c(88, 128, 52, 80, -10.9).intersection(W))
    p.service("power", kit.rect_c(14, 20, 50, 50).intersection(W))
    p.service("club", kit.rect_c(70, 238, 62, 66, -10.9).intersection(W))
    p.parcel("sports", kit.rect_c(10, 270, 40, 40).intersection(W), "sports", "ملعب")
    p.parcel("grove", W, "park", "حديقة البستان (الأشجار القائمة)")

    # ------------------------------------------------ towers flank the gate
    tz = xcut(0, 222).difference(W).difference(xr.buffer(0.1))
    p.parcel("tower_zone", tz, "tower_zone", "منطقة البرجين")
    p.tower(178, 232)
    p.tower(178, 74)

    # ------------------------------------------------ civic node at the midpoint
    xm = 440
    p.service("market", kit.rect_c(xm, yc(xm) + 40, 70, 50))
    p.service("mosque", kit.rect_c(xm + 55, yc(xm) + 37, 40, 40))
    p.service("health", kit.rect_c(xm - 57, yc(xm) + 37, 40, 40))
    p.service("admin", kit.rect_c(xm - 95, yc(xm) + 32, 32, 34))
    p.service("prim", kit.rect_c(xm - 35, yc(xm) - 50, 110, 74))
    p.service("inter", kit.rect_c(xm + 80, yc(xm) - 50, 66, 74))
    p.service("kg", kit.rect_c(xm - 125, yc(xm) - 50, 50, 74))

    # ------------------------------------------------ park at the spine's end, utilities by the wadi
    p.service("water", kit.edge_rect("s", 596, 44, 6, 58))
    p.service("sewage", kit.edge_rect("s", 640 - 4, 30, 6, 50).difference(wadi))
    p.parcel("wadi", wadi, "wadi", "حديقة الوادي")
    park = xcut(565, 700).difference(wadi).difference(E).intersection(
        kit.band_mid(48, 48))
    p.parcel("shallalat", park, "park", "حديقة الشلالات")

    # ------------------------------------------------ housing, rows parallel to each long edge
    x0, x1 = 222, 640
    rn, _ = p.strip_rows("n", ["buf:6", "V+", "S", "D-", "D+", "S", "D-"], x0, 655)
    rs, _ = p.strip_rows("s", ["buf:6", "V+", "S", "D-", "D+", "S", "D-"], x0, 600)
    p.res(xcut(x0, 700).difference(wadi).difference(E), rn + rs)
    # east of the wadi: four villa rows around a green court
    en, _ = p.strip_rows("n", ["buf:6", "V+", "S", "V-"], 690, 860, street_ext=0)
    es, _ = p.strip_rows("s", ["buf:6", "V+", "S", "V-"], 700, 845, street_ext=0)
    p.road([(705, kit.edge_y_s(705) + 30), (690, kit.edge_y_n(690) - 30)], "local")
    p.res(E, en + es)

    p.section_x = 178
    p.phases = [
        {"poly": W.union(tz), "label": "المرحلة 1: البوابة والبرجان والخدمات العامة"},
        {"poly": xcut(222, 560).difference(W), "label": "المرحلة 2: المحور والمركز الخدمي والسكن"},
        {"poly": xcut(560, 900), "label": "المرحلة 3: الحديقة والوادي والطرف الشرقي"},
    ]
    return p.build()
