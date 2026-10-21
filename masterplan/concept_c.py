"""Concept C - the green wadi. Driver: landscape, water and climate.

The plot is read as a valley: a continuous park runs its whole length, from the existing grove in
the west to the wadi in the east, the way KAPSARC turned a dry riverbed into the spine of a
community. Cars stay on a collector ring at the edges (Radburn); the park in the middle is crossed
by one vehicle street only, at the civic heart. Every block touches the park through a green
finger, and the perimeter belt carries a continuous jogging loop.

Towers stand among the grove trees in the far north-west corner of the plot, west of the public
cross road: their winter shadow falls on the north road and the grove, and no house is within
overlooking distance of them.
"""
from shapely.geometry import LineString
from shapely.ops import unary_union

import kit
import plot157 as P
from mpkit import MPlan, N, S, NR, SR, nline, ncurve, nblob, npoly, ds, s_on_south

S_W = 236.0        # west rib (inside the public cross road)
S_AV = 450.0       # main gate and entry avenue
S_E = 692.0        # east rib (park edge on the wadi)
N1, N2 = 35.0, 89.0          # north collector / north local street centrelines (d off north edge)
S1 = 40.0                    # south collector centreline (d off south edge)


def ss(s_n, d=S1):
    return s_on_south(s_n, d)


def build():
    p = MPlan("C", "The Green Wadi", "الوادي الأخضر")
    W = kit.west_of_cross(5)
    wadi = kit.wadi_corridor()
    E = kit.east_of_wadi()

    # =============================================== movement
    # entry avenue from the main gate to the civic plaza
    p.road_line(nline([(S_AV, -12), (S_AV, 128)]), "blvd", "entry avenue")
    # collector ring: north, south and two ribs; the north collector bridges the wadi into the east quarter
    p.road_line(nline([(S_W, N1), (905, N1)]), "collector", "north collector")
    p.road_line(LineString([S.pt(ss(S_W), S1), S.pt(ss(S_E), S1)]), "collector", "south collector")
    p.road_line(kit.rib(P.to_local(P.Q["Q2"])[0] * 0 + kit.NORTH.pt(S_W, 0)[0], N1, S1), "collector")
    p.road_line(kit.rib(kit.NORTH.pt(S_E, 0)[0], N1, S1), "collector")
    # the single vehicle crossing of the park, at the civic plaza (shared surface)
    p.road_line(nline([(S_AV, 128), (S_AV, ds(S_AV) - S1)]), "local", "plaza crossing")
    # north local street in the deep west band
    p.road_line(nline([(S_W, N2), (S_AV, N2)]), "local")
    # east quarter: south street and two end ribs
    p.road_line(LineString([S.pt(ss(768), S1), S.pt(ss(905), S1)]), "local")
    p.road_line(kit.rib(kit.NORTH.pt(768, 0)[0], N1, S1), "local")
    p.road_line(kit.rib(kit.NORTH.pt(896, 0)[0], N1, S1), "local")
    # service gate link from the south road
    p.road_line(LineString([S.pt(ss(640, 0), -10), S.pt(ss(640, 0), S1)]), "local", "service link")

    p.gate_at(S_AV, 0, "main", "البوابة الرئيسية")
    gx = S.pt(ss(640, 0), 0)
    p.gate(gx[0], gx[1], "service")
    p.gates[-1]["label"] = "بوابة الخدمة والطوارئ"
    tg = N.pt(96, 0)
    p.gate(tg[0], tg[1], "tower")
    p.gates[-1]["label"] = "مدخل البرجين"
    # tower access road from the north road
    p.road_line(nline([(96, -12), (96, 26)]), "local", "tower drive")

    # =============================================== west of the cross road: towers in the grove + public services
    p.parcel("tower_zone", W.intersection(N.band(0, 172, -100, 400)), "tower_zone", "البرجان في البستان")
    p.tower(*N.pt(52, 36), angle=-4.79)
    p.tower(*N.pt(64, 112), angle=-4.79)
    p.service("prep", npoly([(110, 176), (186, 176), (196, 236), (120, 236)]).intersection(W))
    p.service("police", npoly([(60, 250), (110, 250), (110, 296), (60, 296)]).intersection(W))
    p.service("cd", npoly([(110, 248), (170, 248), (176, 292), (110, 292)]).intersection(W))
    p.service("power", npoly([(40, 176), (110, 176), (110, 236), (40, 236)]).intersection(W))
    p.parcel("grove", W, "park", "حديقة البستان")

    # =============================================== the park: one continuous valley
    north_edge_w = 120.0          # deep north band (west)
    north_edge_e = 68.0           # shallow north band (east)
    south_band = 73.0             # south band depth
    spine_w = npoly([(S_W - 8, north_edge_w), (S_AV - 12, north_edge_w), (S_AV - 12, 400), (S_W - 8, 400)])
    spine_e = npoly([(S_AV + 12, north_edge_e), (S_E + 8, north_edge_e), (S_E + 8, 400), (S_AV + 12, 400)])
    south_keep = S.band(0, south_band, -100, 1000)
    valley = unary_union([spine_w, spine_e]).intersection(kit.SITE).difference(south_keep)

    # civic heart around the plaza at the end of the avenue
    plaza = nblob([(S_AV - 34, 120), (S_AV + 34, 112), (S_AV + 44, 150), (S_AV, 176), (S_AV - 44, 150)])
    p.plazas.append({"poly": plaza, "kind": "plaza"})
    p.service("mosque", npoly([(S_AV - 30, 182), (S_AV + 30, 182), (S_AV + 30, ds(S_AV + 30) - 76),
                                (S_AV - 30, ds(S_AV - 30) - 76)]))
    p.service("market", npoly([(S_AV + 14, 72), (S_AV + 90, 72), (S_AV + 90, 112), (S_AV + 46, 112),
                                (S_AV + 14, 104)]))
    p.service("health", npoly([(S_AV - 60, 124), (S_AV - 14, 124), (S_AV - 14, 112), (S_AV - 60, 112)]).buffer(0)
              .union(npoly([(S_AV - 66, 124), (S_AV - 38, 124), (S_AV - 38, 160), (S_AV - 66, 160)])))
    p.service("admin", npoly([(S_AV + 92, 72), (S_AV + 120, 72), (S_AV + 120, 106), (S_AV + 92, 106)]))
    p.service("club", npoly([(S_AV + 50, 150), (S_AV + 112, 132), (S_AV + 112, 168), (S_AV + 50, 176)]))
    # schools face the park from the south band; kindergartens at each end of the valley
    p.service("prim", SR(ss(486), ss(574), 0, south_band))
    p.service("inter", SR(ss(574), ss(630), 0, south_band))
    p.service("kg", npoly([(S_W + 30, 124), (S_W + 74, 124), (S_W + 74, 164), (S_W + 30, 164)]))
    p.service("kg2", npoly([(S_E - 56, 72), (S_E - 10, 72), (S_E - 10, 110), (S_E - 56, 110)]))
    # utilities in the south-east corner on the service gate, behind a tree belt
    p.service("water", SR(ss(646), ss(684), 7, 66))
    p.service("sewage", SR(ss(684), ss(706), 7, 66).difference(wadi.buffer(3)))
    p.parcel("sports", npoly([(S_E - 120, 72), (S_E - 62, 72), (S_E - 62, 112), (S_E - 120, 112)]), "sports",
             "ملاعب")
    p.parcel("wadi", wadi, "wadi", "حديقة الوادي")
    p.parcel("valley", valley, "park", "حديقة الشلالات")

    # =============================================== housing
    rn, _ = p.rows("n", ["buf:7", "D+", "G:16", "D-", "D+", "G:12", "V-"], S_W, S_AV)
    p.res(NR(S_W - 10, S_AV - 12, 0, north_edge_w).intersection(kit.SITE), rn)
    re_, _ = p.rows("n", ["buf:7", "D+", "G:16", "V-"], S_AV + 12, S_E)
    p.res(NR(S_AV + 12, S_E + 6, 0, north_edge_e).intersection(kit.SITE), re_)
    rs, _ = p.rows("s", ["buf:7", "V+", "G:16", "V-"], ss(S_W) - 20, ss(486))
    p.res(SR(ss(S_W) - 30, ss(486), 0, south_band).intersection(kit.SITE).difference(W), rs)
    rf, _ = p.rows("n", ["buf:7", "D+", "G:16", "D-"], 760, 905)
    rg, _ = p.rows("s", ["buf:7", "V+", "G:16", "V-"], ss(760), ss(905))
    p.res(E, rf + rg)

    # =============================================== green fingers (pedestrian lanes through the blocks)
    for s in (342,):
        p.path([N.pt(s, 4), N.pt(s, north_edge_w + 4)])
    for s in (575,):
        p.path([N.pt(s, 4), N.pt(s, north_edge_e + 4)])
    p.path([S.pt(ss(360), 4), S.pt(ss(360), south_band + 4)])
    p.notes["fingers_n"] = [342, 575]
    p.notes["fingers_s"] = [ss(360)]
    # promenade along the valley, from the grove to the wadi
    prom = ncurve([(120, 205), (200, 175), (S_W + 20, 150), (300, 146), (370, 136), (420, 140),
                   (S_AV - 20, 150), (S_AV + 30, 170), (540, 140), (600, 128), (650, 126), (S_E, 128),
                   (740, 120), (800, 112)])
    p.paths_wide.append(prom)
    p.path(list(prom.coords))
    # perimeter jogging loop inside the belt
    p.path([N.pt(S_W, 3.5), N.pt(905, 3.5)])
    p.path([S.pt(ss(S_W), 3.5), S.pt(ss(905), 3.5)])

    p.section_x = N.pt(400, 0)[0]
    p.phases = [
        {"poly": W, "label": "1: البرجان والخدمات العامة على الشارع العرضي"},
        {"poly": NR(S_W - 60, S_AV + 130, -10, 400).intersection(kit.SITE).difference(W),
         "label": "2: البوابة والساحة المركزية والحديقة الغربية والسكن الغربي"},
        {"poly": NR(S_AV + 130, 1000, -10, 400).intersection(kit.SITE),
         "label": "3: السكن الشرقي والمدارس والوادي"},
    ]
    return p.build()
