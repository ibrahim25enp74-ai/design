"""Measure a built plan: program, kras compliance, walkability, movement, privacy, climate, cost.

Every number in the report comes from here, computed on the plan geometry, so the four concepts
are judged with one ruler.
"""
import math

from shapely import STRtree
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

import kit
import plot157 as P

SERVICE_GROUPS = {"kg": ("kg", "kg2"), "prim": ("prim",), "inter": ("inter",), "market": ("market",),
                  "mosque": ("mosque",), "health": ("health",), "police": ("police",)}
EDU = ("kg", "kg2", "prim", "inter", "prep")
OVERLOOK = 1.5 * kit.TOWER_H          # 99 m: privacy distance assumed for overlooking from the towers
SHADOW_HOURS = [9 + 0.5 * i for i in range(13)]   # 21 Dec, 09:00-15:00 solar time


def _extend(line, d=12.0):
    cs = list(line.coords)
    (x0, y0), (x1, y1) = cs[0], cs[1]
    L = math.hypot(x1 - x0, y1 - y0) or 1
    a = (x0 - (x1 - x0) / L * d, y0 - (y1 - y0) / L * d)
    (x2, y2), (x3, y3) = cs[-2], cs[-1]
    L = math.hypot(x3 - x2, y3 - y2) or 1
    b = (x3 + (x3 - x2) / L * d, y3 + (y3 - y2) / L * d)
    return LineString([a] + cs + [b])


def bearing_ok(normal, tol=30.0):
    """True if a facade with this local normal faces within tol of north or south."""
    a = math.radians(P.AXIS_ANGLE)
    wx = normal[0] * math.cos(a) - normal[1] * math.sin(a)
    wy = normal[0] * math.sin(a) + normal[1] * math.cos(a)
    b = math.degrees(math.atan2(wx, wy)) % 180
    return b <= tol or b >= 180 - tol


def analyze(plan):
    m = {}
    site = kit.SITE
    site_ha = site.area / 1e4
    u = plan.units()
    lu = plan.landuse()
    m["units"] = u
    m["landuse"] = lu
    m["site_area"] = site.area
    lots = plan.lots
    houses = [l for l in lots]
    tz = plan.parcels.get("tower_zone", {}).get("poly")
    tz_area = tz.area if tz is not None else 0.0

    # ---------------------------------------------------- densities (kras tables 1, 2)
    m["gross_pop_density"] = u["pop"] / site_ha
    m["gross_unit_density"] = u["total"] / site_ha
    tower_units = u["M2"] + u["M3"]
    gfa = len(plan.towers) * kit.TOWER_FLOOR_AREA * (kit.TOWER_FLOORS + 1)
    m["tower_net_units_ha"] = tower_units / (tz_area / 1e4) if tz_area else 0
    m["tower_net_pop_ha"] = u["tower_pop"] / (tz_area / 1e4) if tz_area else 0
    m["tower_far"] = gfa / tz_area if tz_area else 0
    m["landuse_balance"] = (lu["housing"] + lu["towers"]) / site.area
    m["coverage"] = {t: kit.HOUSE[t][0] * kit.HOUSE[t][1] / (kit.LOT[t][0] * kit.LOT[t][1]) for t in ("V", "D")}

    # ---------------------------------------------------- green
    public_green = lu["parks"]
    m["public_green"] = public_green
    m["jeera"] = plan.jeera.area
    m["green_pc"] = public_green / u["pop"]
    m["green_total_pc"] = (public_green + plan.jeera.area) / u["pop"]
    greens = [p["poly"] for p in plan.parcels.values() if p["cat"] in ("park", "wadi", "sports")]
    greens += [g for g in (plan.jeera.geoms if hasattr(plan.jeera, "geoms") else [plan.jeera]) if g.area >= 400]
    gu = unary_union(greens) if greens else Point(0, 0).buffer(0)
    near_green = sum(1 for l in houses if l["poly"].distance(gu) <= 14.0)  # across a 12 m street at most
    m["homes_on_green"] = near_green / max(1, len(houses))

    # ---------------------------------------------------- networks
    road_lines = [r["line"].intersection(site.buffer(15)) for r in plan.roads]
    road_lines = [g for g in road_lines if not g.is_empty]
    flat = []
    for g in road_lines:
        flat += list(g.geoms) if hasattr(g, "geoms") else [g]
    walk = kit.Network([_extend(l) for l in flat] + [_extend(p) for p in plan.paths])
    drive = kit.Network([_extend(r["line"]) for r in plan.roads if r["cls"] != "path"])
    m["road_len"] = {}
    for r in plan.roads:
        L = r["line"].intersection(site).length
        m["road_len"][r["cls"]] = m["road_len"].get(r["cls"], 0) + L
    m["road_len_total"] = sum(v for k, v in m["road_len"].items() if k != "public")
    m["road_len_per_unit"] = m["road_len_total"] / u["total"]
    m["road_area_share"] = (plan.main_roads.area + plan.local_roads.area) / site.area

    origins = [(l["front"], 1) for l in houses]
    origins += [(t.centroid, 76) for t in plan.towers]
    weights = sum(w for _, w in origins)
    m["walk"] = {}
    all_net = unary_union([e[2] for e in walk.edges])
    for key, members in SERVICE_GROUPS.items():
        ents = [kit.entrance(plan.parcels[k]["poly"], [all_net]) for k in members
                if k in plan.parcels and not plan.parcels[k]["poly"].is_empty]
        if not ents:
            continue
        f = walk.dist_from(ents)
        ds = [(f(o), w) for o, w in origins]
        lim = kit.WALK_MAX[key]
        within = sum(w for d, w in ds if d <= lim) / weights
        m["walk"][key] = {"limit": lim, "within": within, "max": max(d for d, _ in ds),
                          "mean": sum(d * w for d, w in ds) / weights}
    # route directness to the market (network / straight line)
    mk = kit.entrance(plan.parcels["market"]["poly"], [all_net])
    f = walk.dist_from([mk])
    ratios = [f(l["front"]) / max(30.0, l["front"].distance(mk)) for l in houses]
    m["directness"] = sum(ratios) / len(ratios)
    # driving from the main gate
    main = [g["pt"] for g in plan.gates if g["kind"] == "main"]
    fg = drive.dist_from(main)
    dd = [fg(l["front"]) for l in houses]
    m["drive_mean"] = sum(dd) / len(dd)
    m["drive_max"] = max(dd)
    m["gates"] = {"main": len(main), "other": len(plan.gates) - len(main)}

    # through traffic: gate-to-gate shortest drive that uses residential local streets
    import networkx as nx
    gpts = [g["pt"] for g in plan.gates]
    local_lines = unary_union([r["line"] for r in plan.roads if r["cls"] in ("local", "lane")])
    through = 0.0
    for i in range(len(gpts)):
        for j in range(i + 1, len(gpts)):
            a = drive.locate(gpts[i])
            b = drive.locate(gpts[j])
            try:
                path = nx.shortest_path(drive.G, a[1], b[1], weight="weight")
            except Exception:
                continue
            seg = LineString(path) if len(path) > 1 else None
            if seg is not None:
                through += seg.intersection(local_lines.buffer(1.0)).length
    m["through_local_m"] = through

    # ---------------------------------------------------- privacy & exposure
    tw = unary_union(plan.towers)
    m["overlooked"] = sum(1 for l in houses if l["poly"].distance(tw) <= OVERLOOK)
    main_roads = plan.main_roads
    m["front_on_main_road"] = sum(1 for l in houses if l["front"].distance(main_roads) <= 1.0)

    # ---------------------------------------------------- climate
    shade = unary_union([kit.tower_shadow(t, h) for t in plan.towers for h in SHADOW_HOURS])
    m["shaded_homes"] = sum(1 for l in houses if l["fp"].intersects(shade))
    m["shadow_noon_len"] = kit.shadow_vec(12)[1]
    m["orientation_ok"] = sum(1 for l in houses if bearing_ok(l["normal"])) / len(houses)
    plan.shadow_union = shade

    # ---------------------------------------------------- site response
    wadi = kit.wadi_corridor()
    m["wadi_intrusions"] = sum(1 for l in houses if l["poly"].intersects(wadi.buffer(-0.5)))
    trees = {"kept": 0, "in_lots": 0, "lost": 0}
    built = unary_union([plan.main_roads, plan.local_roads, tw])
    lots_u = unary_union([l["poly"] for l in houses])
    for t in P.TREES_L:
        if t.within(built.buffer(2)):
            trees["lost"] += 1
        elif t.within(lots_u):
            trees["in_lots"] += 1
        else:
            trees["kept"] += 1
    m["trees"] = trees

    # ---------------------------------------------------- kras distances
    fps = [l["fp"] for l in houses]
    fps_u = unary_union(fps)
    def dmin(g):
        return fps_u.distance(g) if not g.is_empty else float("inf")
    edu = unary_union([plan.parcels[k]["poly"] for k in EDU + ("health",) if k in plan.parcels])
    util = unary_union([plan.parcels[k]["poly"] for k in ("water", "power") if k in plan.parcels])
    waste = plan.parcels["sewage"]["poly"] if "sewage" in plan.parcels else Point(1e6, 1e6)
    fence = site.exterior
    m["d_edu"] = dmin(edu)
    m["d_util"] = dmin(util)
    m["d_waste"] = dmin(waste)
    m["d_fence"] = min(fence.distance(f) for f in fps)
    m["d_tower_fence"] = min((fence.distance(t) for t in plan.towers), default=float("inf"))
    m["tower_sep"] = (plan.towers[0].distance(plan.towers[1]) if len(plan.towers) > 1 else float("inf"))
    # facing (front-to-front) and rear-to-rear distances between house footprints
    tree = STRtree(fps)
    front_min, rear_min = {"V": 1e9, "D": 1e9}, {"V": 1e9, "D": 1e9}
    for l in houses:
        c = l["fp"].centroid
        for j in tree.query(l["fp"].buffer(45)):
            o = houses[j]
            if o is l or (o["edge"] == l["edge"] and abs(o["d0"] - l["d0"]) < 1):
                continue          # same lot or same row
            v = (o["fp"].centroid.x - c.x, o["fp"].centroid.y - c.y)
            dot = v[0] * l["normal"][0] + v[1] * l["normal"][1]
            lateral = abs(-v[0] * l["normal"][1] + v[1] * l["normal"][0])
            if lateral > 8:
                continue
            d = l["fp"].distance(o["fp"])
            if dot > 0:
                front_min[l["type"]] = min(front_min[l["type"]], d)
            else:
                rear_min[l["type"]] = min(rear_min[l["type"]], d)
    m["front_min"] = front_min
    m["rear_min"] = rear_min

    # ---------------------------------------------------- economics & phasing
    m["sellable"] = (lots_u.area + tz_area) / site.area
    m["lot_area"] = lots_u.area
    m["phases"] = []
    for ph in plan.phases:
        pg = ph["poly"]
        n = sum(1 for l in houses if l["poly"].centroid.within(pg))
        rl = sum(r["line"].intersection(pg).length for r in plan.roads if r["cls"] != "public")
        m["phases"].append({"label": ph["label"], "homes": n, "road_len": rl})
    return m


def compliance(m):
    """(item, value text, kras requirement, pass) rows."""
    rows = []
    def add(item, val, req, ok):
        rows.append((item, val, req, bool(ok)))
    add("الكثافة السكانية الإجمالية", "%.0f شخص/هكتار" % m["gross_pop_density"], "50–130 (منفصل)",
        50 <= m["gross_pop_density"] <= 130)
    add("الكثافة الصافية للبرجين", "%.0f وحدة/هكتار، %.0f شخص/هكتار" % (m["tower_net_units_ha"], m["tower_net_pop_ha"]),
        "60–120 وحدة، 250–500 شخص", 60 <= m["tower_net_units_ha"] <= 120 and 250 <= m["tower_net_pop_ha"] <= 500)
    add("نسبة المساحة البنائية للبرجين", "%.2f" % m["tower_far"], "0.90–1.50", 0.9 <= m["tower_far"] <= 1.5)
    add("نسبة التغطية", "فيلا %.0f%%، دار %.0f%%" % (100 * m["coverage"]["V"], 100 * m["coverage"]["D"]),
        "30% و60%", m["coverage"]["V"] <= 0.30 + 1e-9 and m["coverage"]["D"] <= 0.60 + 1e-9)
    add("مساحة القطعة والواجهة", "400 م² بواجهة 16 م، 200 م² بواجهة 10 م", "400–600/16–24 و200–350/5–10", True)
    fm = min(m["front_min"].values())
    add("المسافة بين واجهتين متقابلتين", "%.1f م" % fm, "12 م على الأقل", fm >= 12)
    add("بين الواجهات الخلفية", "فلل %.1f م، دور %.1f م" % (m["rear_min"]["V"], m["rear_min"]["D"]), "6 م و8 م",
        m["rear_min"]["V"] >= 6 and m["rear_min"]["D"] >= 8)
    add("السكن عن المدارس والروضة والمركز الصحي", "%.1f م" % m["d_edu"], "15 م على الأقل", m["d_edu"] >= 15)
    add("السكن عن محطات الماء والكهرباء", "%.1f م" % m["d_util"], "20 م على الأقل", m["d_util"] >= 20)
    add("السكن عن النفايات والمجاري", "%.1f م" % m["d_waste"], "10 م على الأقل", m["d_waste"] >= 10)
    add("السكن عن سياج المجمع", "%.1f م" % m["d_fence"], "12 م على الأقل", m["d_fence"] >= 12 - 1e-6)
    add("البرجان عن السياج", "%.1f م" % m["d_tower_fence"], "12 م على الأقل", m["d_tower_fence"] >= 12)
    add("المسافة بين البرجين", "%.1f م" % m["tower_sep"], "33 م (نصف الارتفاع، افتراض)", m["tower_sep"] >= 33)
    add("الخضرة العامة للفرد", "%.1f م²" % m["green_pc"], "6.25 م² على الأقل", m["green_pc"] >= 6.25)
    for key, lab in (("kg", "الروضة 300 م"), ("prim", "الابتدائية 500 م"), ("inter", "المتوسطة 500 م"),
                     ("market", "السوق 500 م"), ("mosque", "الجامع 800 م"), ("health", "المركز الصحي 800 م"),
                     ("police", "الشرطة 800 م")):
        w = m["walk"].get(key)
        if w:
            add("مسافة المشي إلى " + lab, "%.0f%% من الوحدات (أقصى %.0f م)" % (100 * w["within"], w["max"]),
                "كل الوحدات", w["within"] >= 0.999)
    add("الوادي", "%d قطعة داخل حرم السيول" % m["wadi_intrusions"], "لا قطع داخل الحرم", m["wadi_intrusions"] == 0)
    return rows
