"""Concept C - the green wadi, as a parcellation plan."""
import kit
import plot157 as P
from mpkit import s_on_south as ss, ds
from parcel import N, S, Scheme, nline, npoly, ncurve

AV = 450.0                  # main gate / entry avenue
WR, ER = 245.0, 680.0       # west and east ribs
N1, N2 = 34.0, 91.0         # north loop street, north inner street (centrelines, d off the north edge)
S1 = 33.0                   # south loop street (d off the south edge)


def NR(s0, s1, d0, d1):
    return N.rect(s0, s1, d0, d1)


def SRn(s0, s1, d0, d1):
    """South-frame rectangle given north-frame s limits."""
    return S.rect(ss(s0, (d0 + d1) / 2), ss(s1, (d0 + d1) / 2), d0, d1)


def build():
    c = Scheme("C", "The Green Wadi", "الوادي الأخضر")
    c.belt = 3.0
    W = kit.west_of_cross(5)
    wadi = kit.wadi_corridor()

    # ------------------------------------------------ network
    c.road([(AV, -8), (AV, 104)], "avenue")
    c.ring(AV, 126, 22)
    c.road([(WR, N1), (905, N1)], "local")
    c.road([(WR, N2), (AV, N2)], "local")
    c.road_geom(S.line(S1, ss(WR), ss(ER)) if False else
                __import__("shapely.geometry", fromlist=["LineString"]).LineString(
                    [S.pt(ss(WR, S1), S1), S.pt(ss(ER, S1), S1)]), "local")
    for s in (WR, ER):
        c.road_geom(kit.rib(N.pt(s, 0)[0], N1, S1), "collector")
    # east quarter beyond the wadi
    LS = __import__("shapely.geometry", fromlist=["LineString"]).LineString
    c.road_geom(LS([S.pt(ss(838, S1), S1), S.pt(ss(905, S1), S1)]), "local")
    c.road_geom(kit.rib(N.pt(840, 0)[0], N1, S1), "local")
    c.road_geom(kit.rib(N.pt(896, 0)[0], N1, S1), "local")
    # service gate link and tower drive
    c.road_geom(LS([S.pt(ss(800, 0), -8), S.pt(ss(800, 0), S1)]), "local")
    c.road([(96, -8), (96, 22)], "local")
    # green fingers through the north band
    c.road([(342, 0), (342, N2 + 6)], "finger")
    c.road([(560, 0), (560, N1)], "finger")
    c.road_geom(LS([S.pt(ss(352, 20), 0), S.pt(ss(352, 20), S1)]), "finger")
    c.road_geom(LS([S.pt(ss(600, 20), 0), S.pt(ss(600, 20), S1)]), "finger")

    c.gate(AV, -2, "main", "البوابة الرئيسية", 1)
    c.gate(96, -2, "tower", "مدخل البرجين", 2)
    g = S.pt(ss(800, 0), 0)
    c.gates.append({"pt": __import__("shapely.geometry", fromlist=["Point"]).Point(g), "kind": "service",
                    "label": "بوابة الخدمة", "n": 3})

    # ------------------------------------------------ carved parcels
    c.carve(wadi, "wadi", "حديقة الوادي")
    c.carve(W.intersection(N.band(0, 172, -100, 400)), "towers", "منطقة البرجين")
    c.tower(52, 36)
    c.tower(64, 112)
    c.carve(npoly([(110, 176), (186, 176), (198, 236), (122, 236)]).intersection(W), "edu", "مدرسة إعدادية")
    c.carve(npoly([(60, 250), (110, 250), (110, 300), (60, 300)]).intersection(W), "community", "مركز شرطة")
    c.carve(npoly([(110, 248), (176, 248), (186, 300), (110, 300)]).intersection(W), "community", "دفاع مدني")
    c.carve(npoly([(36, 176), (108, 176), (108, 236), (36, 236)]).intersection(W), "utility", "محطة كهرباء 33/11")
    # civic heart around the plaza
    c.carve(npoly([(AV - 26, 150), (AV + 26, 150), (AV + 26, ds(AV + 26) - S1 - 6),
                   (AV - 26, ds(AV - 26) - S1 - 6)]), "religious", "الجامع")
    c.carve(NR(474, 546, N1 + 6, 86), "commercial", "السوق والمقاهي")
    c.carve(NR(548, 580, N1 + 6, 86), "health", "مركز صحي")
    c.carve(NR(582, 604, N1 + 6, 86), "community", "إدارة وأمن")
    c.carve(NR(606, 646, N1 + 6, 86), "edu", "روضة 2")
    c.carve(SRn(480, 598, S1 + 6, 104), "edu", "مدرسة ابتدائية")
    c.carve(SRn(598, 672, S1 + 6, 104), "edu", "مدرسة متوسطة")
    c.carve(NR(252, 312, N2 + 6, 162), "community", "النادي الاجتماعي")
    c.carve(NR(314, 352, N2 + 6, 146), "edu", "روضة 1")
    c.carve(SRn(762, 828, 6, S1 - 6), "utility", "محطة معالجة ماء")
    c.carve(SRn(860, 900, 6, S1 - 6), "utility", "مجاري ونفايات")

    # ------------------------------------------------ block uses
    c.zone(W, "park", "حديقة البستان")
    c.zone(NR(-100, 1000, 0, N1 - 5), "res", "", rows=[("n", "far", "V")])
    c.zone(NR(WR, AV, N1, N2), "res", "", rows=[("n", "near", "V"), ("n", "far", "D")])
    c.zone(NR(WR, AV, N2, 400), "res", "", rows=[("n", "near", "V"), ("s", "near", "V")])
    c.zone(NR(AV, ER, N1, 400), "res", "", rows=[("n", "near", "V"), ("s", "near", "V")])
    c.zone(S.band(0, S1 - 5, -100, 1000), "res", "", rows=[("s", "far", "D")])
    c.zone(NR(ER + 60, 1000, N1, 400), "res", "", rows=[("n", "near", "D"), ("s", "near", "D")])

    # ------------------------------------------------ paths
    c.paths.append(ncurve([(150, 200), (WR - 10, 170), (300, 178), (380, 168), (AV - 30, 160), (AV, 150),
                           (AV + 40, 120), (520, 108), (600, 104), (ER - 10, 112), (740, 120), (790, 110)]))
    c.paths.append(nline([(0, 1.5), (905, 1.5)]))
    c.paths.append(__import__("shapely.geometry", fromlist=["LineString"]).LineString(
        [S.pt(-20, 1.5), S.pt(840, 1.5)]))
    return c.build()
