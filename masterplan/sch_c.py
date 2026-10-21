"""Concept C - the green wadi, as a parcellation plan.

West: housing bands either side of a valley park (Radburn: houses back onto the park, cars on the
loop streets). Centre: the civic heart on the main gate axis - admin and clinic west of the
roundabout, market east of it, mosque on the axis at the far side of the plaza, the two schools on
the south loop street; the valley continues between them as a green mall. East of the wadi: a
complete housing quarter. Utilities sit on the low wadi bank. West of the public cross road: the
towers stand among the existing grove with the public-facing services and the club.
"""
from shapely.geometry import LineString, Point

import kit
import plot157 as P
from mpkit import s_on_south as ss, ds
from parcel import N, S, Scheme, nline, npoly, ncurve

AV = 450.0                      # gate axis
ER = 684.0                      # east rib (west bank of the wadi)
N1, N2 = 36.0, 95.0             # north loop street (16 m) and inner street (12 m) centrelines
S1 = 34.5                       # south loop street centreline, off the south edge
PL = 91.5                       # park lane centreline, off the south edge (west valley)
MALL = (69.0, 86.0)             # green mall behind the park-front villas (north-frame d)


def NR(s0, s1, d0, d1):
    return N.rect(s0, s1, d0, d1)


def SR(s0, s1, d0, d1):
    m = (d0 + d1) / 2
    return S.rect(ss(s0, m), ss(s1, m), d0, d1)


def sline(d, s0, s1):
    return LineString([S.pt(ss(s0, d), d), S.pt(ss(s1, d), d)])


def snormal(s_n, d0, d1):
    x = ss(s_n, (d0 + d1) / 2)
    return LineString([S.pt(x, d0), S.pt(x, d1)])


def west_street():
    """Edge street parallel to the public cross road, 21 m east of its centreline."""
    a, b = (139.2, -4.9), (218.9, 279.0)
    L = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, ny = uy, -ux
    off = 21.0
    return nline([(a[0] + nx * off - ux * 30, a[1] + ny * off - uy * 30),
                  (b[0] + nx * off + ux * 30, b[1] + ny * off + uy * 30)])


def south_kerb(s_n):
    """North-frame d of the south loop street's inner kerb."""
    return ds(s_n) - S1 - 8


def build():
    c = Scheme("C", "The Green Wadi", "الوادي الأخضر")
    c.belt = 3.0
    W = kit.west_of_cross(5)
    wadi = kit.wadi_corridor()

    # ================================================= network
    c.road([(AV, -8), (AV, 46)], "avenue")
    c.ring(AV, 64, 20)
    c.road_geom(west_street(), "collector")
    c.road([(160, N1), (912, N1)], "collector")                      # north loop, bridges the wadi
    c.road([(180, N2), (AV - 18, N2)], "local")                     # inner street, west quarter
    c.road_geom(sline(S1, 190, ER + 4), "collector")                 # south loop
    c.road_geom(kit.rib(N.pt(ER, 0)[0], N1, S1), "collector")        # east rib
    c.road_geom(sline(PL, 190, 300), "local")                        # park lane (west valley)
    c.road_geom(snormal(300, S1, PL + 4), "local")                   # its link to the south loop
    # east quarter
    c.road([(760, 95), (900, 95)], "local")
    c.road_geom(sline(S1, 742, 912), "local")
    c.road_geom(kit.rib(N.pt(760, 0)[0], N1, S1), "local")
    c.road_geom(kit.rib(N.pt(898, 0)[0], N1, S1), "local")
    # tower drive and service drive
    c.road([(96, -8), (96, 24)], "local")
    c.road_geom(LineString([S.pt(ss(708, 0), -8), S.pt(ss(708, 0), 30)]), "local")
    # pedestrian fingers from the loop streets into the valley and mall
    c.road([(330, N1 + 8), (330, N2 - 6)], "finger")
    c.road([(330, N2 + 6), (330, N2 + 34)], "finger")
    c.road([(614, N1 + 8), (614, MALL[0] + 2)], "finger")
    c.road_geom(snormal(386, S1 + 8, S1 + 36), "finger")

    c.gate(AV, -2, "main", "البوابة الرئيسية", 1)
    c.gate(96, -2, "tower", "مدخل البرجين والنادي", 2)
    c.gates.append({"pt": Point(S.pt(ss(708, 0), 0)), "kind": "service", "label": "بوابة الخدمة", "n": 3})

    # ================================================= west of the public cross road
    c.carve(wadi, "wadi", "حديقة الوادي")
    c.carve(W.intersection(N.band(0, 182, -100, 400)), "towers", "منطقة البرجين")
    c.tower(52, 40)
    c.tower(68, 126)
    c.carve(npoly([(46, 190), (104, 190), (104, 236), (46, 236)]).intersection(W), "utility", "محطة كهرباء 33/11")
    c.carve(npoly([(106, 190), (176, 190), (188, 236), (106, 236)]).intersection(W), "community", "النادي الاجتماعي")
    c.carve(npoly([(56, 240), (112, 240), (112, 304), (56, 304)]).intersection(W), "edu", "مدرسة إعدادية")
    c.carve(npoly([(114, 240), (150, 240), (150, 304), (114, 304)]).intersection(W), "community", "مركز شرطة")
    c.carve(npoly([(152, 240), (204, 240), (216, 304), (152, 304)]).intersection(W), "community", "دفاع مدني")

    # ================================================= civic heart on the gate axis
    c.carve(NR(374, AV - 22, N1 + 8, N2 - 6), "health", "مركز صحي")
    c.carve(NR(AV + 22, 548, N1 + 8, N2 - 6), "commercial", "السوق والمقاهي")
    c.carve(npoly([(AV - 22, N2 - 6), (AV + 22, N2 - 6), (AV + 22, south_kerb(AV + 22)),
                   (AV - 22, south_kerb(AV - 22))]), "religious", "الجامع وساحته")
    c.carve(npoly([(474, MALL[1]), (580, MALL[1]), (580, south_kerb(580)), (474, south_kerb(474))]),
            "edu", "مدرسة ابتدائية (18 صفاً)")
    c.carve(npoly([(582, MALL[1]), (676, MALL[1]), (676, south_kerb(676)), (582, south_kerb(582))]),
            "edu", "مدرسة متوسطة")
    c.carve(NR(348, 372, N1 + 8, N2 - 6), "community", "إدارة وأمن")
    c.carve(NR(300, 342, N2 + 6, N2 + 50), "edu", "روضة 1")
    c.carve(NR(718, 760, N1 + 8, 92), "edu", "روضة 2")
    # utilities on the low west bank of the wadi, off the service gate
    bank = N.rect(ER + 8, 760, 0, 400).intersection(kit.SITE).difference(wadi)
    c.carve(bank.intersection(S.band(0, 50, -100, 1000)).intersection(SR(690, 760, 0, 60)), "utility",
            "محطة معالجة ماء ومجاري")

    # ================================================= block uses (first match wins)
    c.zone(W, "park", "حديقة البستان")
    c.zone(S.band(0, S1 - 6, -100, 1000), "res", rows=[("s", "far", "D")])
    c.zone(NR(-100, 1000, 0, N1 - 6), "res", rows=[("n", "far", "V")])
    c.zone(NR(150, AV, N1, N2), "res", rows=[("n", "near", "V"), ("n", "far", "D")])
    c.zone(SR(180, 302, S1, PL - 4), "res", rows=[("s", "near", "V"), ("s", "far", "D")])
    c.zone(NR(150, AV, N2, 400), "res", rows=[("n", "near", "D"), ("s", "near", "V")], residual="park")
    c.zone(NR(AV, ER, N1, MALL[1]), "res", rows=[("n", "near", "V")], residual="park")
    c.zone(NR(ER + 20, 1000, N1, 89), "res", rows=[("n", "near", "D"), ("n", "far", "D")])
    c.zone(NR(ER + 20, 1000, 89, 400), "res", rows=[("n", "near", "D"), ("s", "near", "D")])

    # ================================================= paths
    c.paths.append(ncurve([(196, 214), (240, 196), (290, 196), (350, 182), (400, 168), (AV - 30, 150),
                           (AV, 140), (AV + 30, 100), (520, 78), (600, 78), (676, 80), (ER, 90),
                           (720, 100), (740, 110)]))
    c.paths.append(LineString([S.pt(ss(190, 3), 3.2), S.pt(ss(ER, 3), 3.2)]))
    return c.build()
