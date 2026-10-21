"""Concept A - the spine. Driver: movement efficiency and phasing.

One 24 m boulevard carries every trip and every utility trunk, with the civic "high street" at
its midpoint (Soria y Mata's linear city at neighbourhood scale). The boulevard runs parallel to
the north edge, so the north residential band is one continuous stack of rows with no waste; the
plot's 10 deg taper is taken entirely by the south band, which is wide in the west (more housing
rows) and narrow in the east (schools, utilities and the park take that narrow end).

The cross road stays public: the towers and the public-facing services sit west of it in the
grove, so 152 apartments and all outside visitors never enter the gated low-rise streets, and
phase 1 needs no internal road at all.
"""
import kit
import plot157 as P
from kit import ncut

SPINE_D = 105.0             # spine centreline, metres off the north edge
X_GATE = 112.0              # main gate on the cross road, at the head of the spine
CIVIC = (376.0, 540.0)      # civic high street between two collector ribs


def build():
    p = kit.Plan("A", "The Spine", "المحور")
    W = kit.west_of_cross(5)
    wadi = kit.wadi_corridor()
    E = kit.east_of_wadi()
    N = kit.NORTH

    # ------------------------------------------------ movement
    p.road_line(N.line(SPINE_D, X_GATE - 30, 708), "blvd", "boulevard")
    p.road_line(P.ROAD_X_L, "public", "public cross road")
    p.road_line(kit.rib(CIVIC[0] - 8, 28, 28), "collector")
    p.road_line(kit.rib(CIVIC[1] + 8, 28, 28), "collector")
    p.road_line(kit.rib(250, 28, 28), "local")
    p.road_line(kit.rib(708, 28, 28), "local")
    p.road_line(kit.rib(846, 28, 28), "local")
    gx, gy = N.pt(N.s_at_x(X_GATE, SPINE_D), SPINE_D)
    p.gate(gx, gy, "main")
    p.gate(600, kit.edge_y_s(600), "service")

    # ------------------------------------------------ west of the cross road: towers in the grove, public services
    p.parcel("tower_zone", W.intersection(kit.band_mid(112, 0)), "tower_zone", "منطقة البرجين")
    p.tower(22, 236)
    p.tower(40, 170)
    p.service("power", kit.edge_rect("s", -2, 40, 6, 40))
    p.service("police", kit.edge_rect("s", 38, 34, 6, 40))
    p.service("cd", kit.edge_rect("s", 72, 52, 6, 40))
    p.service("prep", kit.edge_rect("s", 6, 60, 50, 62))
    p.service("club", kit.edge_rect("s", 66, 56, 50, 62))
    p.parcel("grove", W, "park", "حديقة البستان")

    # ------------------------------------------------ civic high street: shops north, schools south
    spine_s = kit.band_mid(0, SPINE_D + 12)          # everything south of the spine
    p.service("admin", kit.edge_rect("n", CIVIC[0], 20, 40, 53))
    p.service("market", kit.edge_rect("n", CIVIC[0] + 20, 66, 40, 53))
    p.service("mosque", kit.edge_rect("n", CIVIC[0] + 86, 32, 40, 53))
    p.service("health", kit.edge_rect("n", CIVIC[0] + 118, 32, 40, 53))
    p.service("kg2", ncut(CIVIC[0], CIVIC[0] + 22).intersection(spine_s).intersection(kit.band_edge("s", 6, 200)))
    p.service("prim", ncut(CIVIC[0] + 22, CIVIC[0] + 102).intersection(spine_s).intersection(kit.band_edge("s", 6, 200)))
    p.service("inter", ncut(CIVIC[0] + 102, CIVIC[1]).intersection(spine_s).intersection(kit.band_edge("s", 6, 200)))
    p.service("kg", ncut(150, 178).intersection(spine_s).intersection(kit.band_edge("s", 95, 200)))
    p.service("water", kit.edge_rect("s", 604, 38, 3, 66))
    p.service("sewage", kit.edge_rect("s", 642, 26, 3, 66).difference(wadi.buffer(2)))
    p.parcel("wadi", wadi, "wadi", "حديقة الوادي")
    p.parcel("shallalat", ncut(604, 708).intersection(spine_s).difference(wadi).difference(kit.band_edge("s", 0, 69)), "park", "حديقة الشلالات")

    # ------------------------------------------------ housing
    rn, _ = p.strip_rows("n", ["buf:3", "V+", "S", "V-", "D+", "L"], 60, 708)
    p.res(ncut(60, 708).intersection(kit.band_edge("n", 0, SPINE_D)).difference(W).difference(wadi), rn)
    rs, _ = p.strip_rows("s", ["buf:3", "V+", "S", "D-", "D+", "S", "D-", "D+", "L"], 140, CIVIC[0] - 8)
    p.res(ncut(60, CIVIC[0] - 8).intersection(spine_s).difference(W), rs)
    gs, _ = p.strip_rows("s", ["buf:3", "D+", "S", "D-"], CIVIC[1] + 8, 604)
    p.res(ncut(CIVIC[1] + 14, 604).intersection(spine_s), gs)
    fn, _ = p.strip_rows("n", ["buf:3", "V+", "S", "D-", "D+", "L"], 708, 846)
    fs, _ = p.strip_rows("s", ["buf:3", "V+", "S", "D-"], 708, 846)
    p.res(E, fn + fs)

    p.section_x = 300
    p.phases = [
        {"poly": W, "label": "1: البرجان والخدمات العامة غرب الشارع العرضي (بلا طرق داخلية)"},
        {"poly": ncut(60, CIVIC[1]).difference(W), "label": "2: البوابة والمحور والمركز الخدمي والسكن الغربي"},
        {"poly": ncut(CIVIC[1], 900), "label": "3: السكن الشرقي وحديقة الشلالات والوادي"},
    ]
    return p.build()
