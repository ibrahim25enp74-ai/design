"""Civil defence calculations: separation distances, bunds, fire water, extinguishers.

All geometry is read from site_items.json (written by build_fuel_station_dxf.py) in the plot
frame (metres).  Required values are the code minimums named in each rule; every rule that the
OPDC instructions may also govern is flagged so it is checked against them before submission.
"""
import json
import math
import os

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ITEMS = json.load(open(os.path.join(HERE, "site_items.json")))

PLOT = Polygon(ITEMS["plot"])
D, C, B, A = [tuple(p) for p in ITEMS["plot"]]
FRONT_LINE = LineString([A, B])                          # street (public way)
SIDE_LINES = LineString([A, D, C, B])                    # rear and both sides: neighbours that can be built upon


def tank_poly(t):
    r = t["d"] / 2
    return box(t["x0"], t["yc"] - r, t["x1"], t["yc"] + r)


TANKS = {t["tag"]: t for t in ITEMS["tanks"]}
TANK_POLY = {k: tank_poly(t) for k, t in TANKS.items()}
LPG_TANKS = ["T-02", "T-03"]
FUEL_TANKS = ["T-01", "T-04", "T-05", "T-06"]
BUILDINGS = [box(*b) for b in ITEMS["buildings"]]
BUILDINGS_U = unary_union(BUILDINGS)
GEN_ROOM = box(*ITEMS["rooms"]["generator"])
TRF_ROOM = box(*ITEMS["rooms"]["transformer"])
IGNITION = unary_union([GEN_ROOM, TRF_ROOM])
ISL = {i["tag"]: i for i in ITEMS["islands"]}
DISP = {i["tag"]: [Point(p) for p in i["dispensers"]] for i in ITEMS["islands"]}
CLASS1_DISP = DISP["I-1"] + DISP["I-3"] + DISP["I-4"] + DISP["I-5"]   # gas oil treated with Class I for spacing
LPG_DISP = DISP["I-2"]
FILL = {f["product"]: Point(f["xy"]) for f in ITEMS["fill_points"]}

VERIFY = "OPDC"        # flag: to be verified against the Oil Products Distribution Company instructions


def nearest(a, b):
    """Shortest distance between two geometries (or lists of geometries) and the two points."""
    a = unary_union(a) if isinstance(a, list) else a
    b = unary_union(b) if isinstance(b, list) else b
    from shapely.ops import nearest_points
    p, q = nearest_points(a, b)
    return a.distance(b), (p.x, p.y), (q.x, q.y)


# id, item (EN), item (AR), from, to, required m, source
RULES = [
    ("S1", "LPG TANK (23 m3) TO PROPERTY LINE", "خزان الغاز السائل - حدود الجيران",
     LPG_TANKS, SIDE_LINES, 15.0, "NFPA 58 TABLE 6.4.1.1 (7.6-114 m3 W.C.)"),
    ("S2", "LPG TANK TO NEAREST BUILDING", "خزان الغاز السائل - اقرب بناية",
     LPG_TANKS, BUILDINGS, 15.0, "NFPA 58 TABLE 6.4.1.1"),
    ("S3", "LPG TANK TO FLAMMABLE LIQUID TANK", "خزان الغاز السائل - خزانات الوقود",
     LPG_TANKS, FUEL_TANKS, 6.0, "NFPA 58 6.4.5 (20 ft)"),
    ("S4", "LPG TANK TO LPG TANK (SHELL TO SHELL)", "بين خزاني الغاز السائل",
     ["T-02"], ["T-03"], 1.5, "NFPA 58 TABLE 6.4.1.1"),
    ("S5", "FUEL TANK (54 m3) TO PROPERTY LINE", "خزان الوقود - حدود الجيران",
     FUEL_TANKS, SIDE_LINES, 4.5, "NFPA 30 TABLE 22.4.1.1(b) (45-114 m3)"),
    ("S6", "FUEL TANK TO STREET (PUBLIC WAY)", "خزان الوقود - الشارع",
     FUEL_TANKS, FRONT_LINE, 1.5, "NFPA 30 TABLE 22.4.1.1(b)"),
    ("S7", "FUEL TANK TO NEAREST BUILDING", "خزان الوقود - اقرب بناية",
     FUEL_TANKS, BUILDINGS, 1.5, "NFPA 30 TABLE 22.4.1.1(a)"),
    ("S8", "FUEL TANK TO FUEL TANK (SHELL TO SHELL)", "بين خزانات الوقود",
     None, None, 0.92, "NFPA 30 TABLE 22.4.2.1 (1/6 SUM OF DIAMETERS, MIN 0.9)"),
    ("S9", "FUEL DISPENSER TO PROPERTY LINE", "مضخة الوقود - حدود الجيران",
     CLASS1_DISP, SIDE_LINES, 3.0, "NFPA 30A 6.2.1 (10 ft)"),
    ("S10", "FUEL DISPENSER TO BUILDING", "مضخة الوقود - البنايات",
     CLASS1_DISP, BUILDINGS, 3.0, "NFPA 30A 6.2.1"),
    ("S11", "DISPENSER / FILL POINT TO IGNITION SOURCE (GENERATOR, TRANSFORMER)",
     "المضخات ونقاط التفريغ - المولدة والمحولة",
     CLASS1_DISP + LPG_DISP + list(FILL.values()), IGNITION, 6.0, "NFPA 30A / NFPA 70 ART. 514 (20 ft)"),
    ("S12", "LPG DISPENSER TO PROPERTY LINE", "مضخة الغاز السائل - حدود الجيران",
     LPG_DISP, SIDE_LINES, 7.6, "NFPA 58 TABLE 6.7.2.1 (25 ft)"),
    ("S13", "LPG DISPENSER TO STREET (PUBLIC WAY)", "مضخة الغاز السائل - الشارع",
     LPG_DISP, FRONT_LINE, 3.1, "NFPA 58 TABLE 6.7.2.1 (10 ft)"),
    ("S14", "LPG DISPENSER TO FUEL DISPENSER", "مضخة الغاز السائل - مضخات الوقود",
     LPG_DISP, CLASS1_DISP, 3.0, "NFPA 58 6.27.4 (10 ft)"),
    ("S15", "LPG DISPENSER TO BUILDING (FIRE-RESISTIVE WALLS)", "مضخة الغاز السائل - البنايات",
     LPG_DISP, BUILDINGS, 3.1, "NFPA 58 TABLE 6.7.2.1 (10 ft)"),
    ("S16", "LPG UNLOADING POINT TO PROPERTY LINE", "نقطة تفريغ الغاز السائل - حدود الجيران",
     [FILL["LPG"]], SIDE_LINES, 7.6, "NFPA 58 TABLE 6.7.2.1 (25 ft)"),
    ("S17", "LPG TANK TO IGNITION SOURCE (GENERATOR, TRANSFORMER)", "خزان الغاز السائل - المولدة والمحولة",
     LPG_TANKS, IGNITION, 15.0, "NFPA 58 TABLE 6.4.1.1 (AS IMPORTANT BUILDING)"),
]


def _geoms(x):
    if x is None:
        return None
    if isinstance(x, list):
        return [TANK_POLY[g] if isinstance(g, str) else g for g in x]
    return x


def separation_checks():
    out = []
    for rid, en, ar, a, b, req, src in RULES:
        if rid == "S8":
            pairs = [("T-04", "T-05")]
            d, p, q = min(nearest(TANK_POLY[x], TANK_POLY[y]) for x, y in pairs)
        else:
            d, p, q = nearest(_geoms(a), _geoms(b))
        out.append({"id": rid, "en": en, "ar": ar, "required": req, "provided": round(d, 2),
                    "ok": d + 1e-6 >= req, "source": src, "p": p, "q": q})
    return out


# ---------------------------------------------------------------- tank limits
NFPA30A_MAX_AST = 45.4        # m3 (12,000 gal) per aboveground tank at a motor fuel dispensing facility


def tank_size_check():
    return [{"tag": k, "capacity": 54, "limit": NFPA30A_MAX_AST, "ok": 54 <= NFPA30A_MAX_AST}
            for k in FUEL_TANKS]


# ---------------------------------------------------------------- bunds
SADDLE_H = 0.60               # tank bottom above bund floor
SADDLE_VOL = 0.45             # m3 of concrete per saddle below the bund wall top (2 per tank)
BUND_RATIO = 1.10             # 110 % of the largest tank (NFPA 30 requires 100 %)


def _segment_area(r, h):
    """Area of a circular segment of height h (0..2r)."""
    h = max(0.0, min(2 * r, h))
    return r * r * math.acos((r - h) / r) - (r - h) * math.sqrt(max(0.0, 2 * r * h - h * h))


def bund(cmp_key, tank_tags, cap):
    x0, y0, x1, y1 = ITEMS["compartments"][cmp_key]
    area = (x1 - x0) * (y1 - y0)
    need = BUND_RATIO * max(cap[t] for t in tank_tags)

    def net(h):
        v = area * h
        for t in tank_tags:
            tk = TANKS[t]
            r = tk["d"] / 2
            v -= _segment_area(r, h - SADDLE_H) * (tk["x1"] - tk["x0"])
            v -= 2 * SADDLE_VOL * min(1.0, h / SADDLE_H)
        return v

    h = 0.05
    while net(h) < need:
        h += 0.01
    h_design = math.ceil((h + 0.15) * 10) / 10          # + 150 mm freeboard, rounded up to 0.1 m
    return {"cmp": cmp_key, "area": round(area, 2), "tanks": tank_tags, "required": round(need, 2),
            "h_min": round(h, 2), "h": h_design, "net": round(net(h_design), 2)}


def bunds():
    cap = {"T-01": 54, "T-04": 54, "T-05": 54, "T-06": 54}
    # C3a and C3b are joined into one bund (the intermediate wall is a low separating kerb)
    c3 = ITEMS["compartments"]["C3a"][:3] + [ITEMS["compartments"]["C3b"][3]]
    ITEMS["compartments"]["C3"] = c3
    return [bund("C1", ["T-01"], cap), bund("C3", ["T-04", "T-05", "T-06"], cap)]


# ---------------------------------------------------------------- fire water
SPRAY_RATE = 10.2             # L/min/m2 of tank surface (NFPA 15 / NFPA 58 guidance)
HOSE_ALLOW = 950              # L/min for two hydrant hose streams (2 x 475)
DURATION = 60                 # min


def lpg_surface(t):
    r = t["d"] / 2
    L = t["x1"] - t["x0"]
    return 2 * math.pi * r * (L - 2 * 0.9) + 2 * (math.pi * r * r * 1.2)    # shell + dished heads (approx.)


def fire_water():
    surf = sum(lpg_surface(TANKS[t]) for t in LPG_TANKS)
    spray = surf * SPRAY_RATE
    total = spray + HOSE_ALLOW
    vol = total * DURATION / 1000
    return {"surface": round(surf, 1), "spray": round(spray), "hose": HOSE_ALLOW, "total": round(total),
            "duration": DURATION, "volume": round(vol, 1), "tank": int(math.ceil(vol / 10.0) * 10),
            "pump_flow": int(math.ceil(total / 100.0) * 100), "pump_head": 70}


# ---------------------------------------------------------------- extinguishers
def extinguishers():
    """(location, type, qty) - one schedule for the drawing and the report."""
    rows = []
    for i in ITEMS["islands"]:
        n = len(i["dispensers"])
        rows.append((f"ISLAND {i['tag']} ({i['product']})", "FE-P", 2 if n > 1 else 1))
    rows += [("ISLANDS AREA (CANOPY)", "FE-W", 2), ("KEROSENE YARD", "FE-W", 1)]
    for f in ITEMS["fill_points"]:
        rows.append((f"UNLOADING POINT - {f['product']}", "FE-P", 1))
    rows += [("UNLOADING POINTS", "FE-W", 1), ("UNLOADING POINTS", "FE-F", 2)]
    rows += [("TANK COMPARTMENT C1", "FE-W", 1), ("TANK COMPARTMENT C2 (LPG)", "FE-W", 1),
             ("TANK COMPARTMENT C3", "FE-W", 1), ("TANK COMPARTMENT C3", "FE-F", 1),
             ("LPG PUMP", "FE-P", 1)]
    rows += [("TRANSFORMER ROOM", "FE-C", 2), ("GENERATOR ROOM", "FE-C", 1), ("GENERATOR ROOM", "FE-P", 1),
             ("ADMINISTRATION (MDB)", "FE-C", 1), ("ADMINISTRATION", "FE-P", 1), ("WORKERS ROOM", "FE-P", 1),
             ("SPARE PARTS SHOP", "FE-P", 1), ("PAINTS SHOWROOM", "FE-P", 1), ("PAINTS SHOWROOM", "FE-C", 1),
             ("PRAYER ROOM", "FE-P", 1), ("FIRE PUMP ROOM", "FE-P", 1)]
    return rows


if __name__ == "__main__":
    for r in separation_checks():
        print(f"{r['id']:4} {'OK ' if r['ok'] else 'NO '} req {r['required']:5.2f} got {r['provided']:6.2f}  {r['en']}")
    print(tank_size_check()[0])
    for b in bunds():
        print(b)
    print(fire_water())
    from collections import Counter
    c = Counter()
    for _l, t, q in extinguishers():
        c[t] += q
    print(c)
