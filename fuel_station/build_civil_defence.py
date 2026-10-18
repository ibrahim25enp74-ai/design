"""Civil defence drawing set F-001 .. F-008.

usage: python build_civil_defence.py OUT.dxf
"""
import math
import os
import sys
from collections import Counter

import safety
import symbols
from drawkit import Plan, rect
from register import entry
from sheets import SheetSet, import_site_block

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "F_CIVIL_DEFENCE.dxf")
I = safety.ITEMS
WINDOW = (-1.5, -2.0, 51.5, 67.0)           # plot-frame window (plans are drawn rear boundary up)
KEY = (-19.0, -4.0, 63.0, 55.5)
AREA = (20, 10, 245, 287)                    # drawing area left of the side panel (paper mm)

ss = SheetSet()
symbols.define(ss.doc)
import_site_block(ss.doc, os.path.join(HERE, "FUEL_STATION_SITE_PLAN.dxf"))
for name, color in (("F-PASS", 3), ("F-FAIL", 1), ("F-ROUTE", 3), ("F-TANKER", 30), ("F-NEW", 1)):
    ss.doc.layers.add(name, color=color, lineweight=25)
RED, GREEN = 1, 3

# fire water installation (new items introduced by this set, plot frame)
FIRE_TANK = (2.0, 9.0, 10.0, 15.0)            # underground RC tank, 8.0 x 6.0 x 2.6 water depth
PUMP_ROOM = (11.75, 1.5, 14.0, 5.0)           # between building 1 and building 2
HYDRANTS = {"FH-1": (1.9, 24.0), "FH-2": (33.3, 52.0), "FH-3": (31.0, 6.9)}
HOSE_REELS = {"HR-1": (20.0, 5.75), "HR-2": (38.4, 5.75), "HR-3": (35.4, 33.0), "HR-4": (36.2, 53.6)}
DELUGE = (35.6, 24.0)
MAIN = [(12.9, 5.0), (12.9, 6.9), (35.5, 6.9), (35.5, 51.4), (33.3, 52.0)]
BRANCH_W = [(11.75, 3.25), (10.0, 3.25), (10.0, 7.9), (1.9, 7.9), (1.9, 24.0)]
SUCTION = [(10.0, 9.0), (11.0, 7.0), (11.75, 4.0)]
ASSEMBLY = (3.3, 27.0)


def plan_sheet(number, den=300):
    _, title, subtitle, _ = entry(number)
    sh = ss.add(number, title, subtitle, den)
    sh.place_site(WINDOW, area=AREA, plan_up=True)
    return sh, Plan(sh)


def panel(sh, x=250, y=280, w=86):
    """Right-hand information column inside the drawing frame (x 250..336 mm)."""
    sh.line((247, 10), (247, 287), "TB_LINES_THIN")
    return x, y, w


def notes(sh, x, y, heading, lines, h=1.55, step=3.0, layer="G-TEXT"):
    sh.text(heading, x, y, 2.2, "TB_HEADINGS")
    y -= 4.5
    for ln in lines:
        sh.text(ln, x, y, h, layer)
        y -= step
    return y - 2.0


def draw_fire_installation(p, full=True):
    """Fire tank, pump room, main, hydrants, hose reels and LPG deluge (shared by F-002/F-005)."""
    p.pline(rect(FIRE_TANK), "F-PIPE", close=True, linetype="DASHED", ltscale=0.4)
    symbols.line_key(p.sh, "F-PIPE", "UNDERGROUND FIRE WATER TANK", "خزان ماء الحريق الارضي", linetype="DASHED")
    symbols.line_key(p.sh, "F-PIPE", "FIRE PUMP ROOM (HATCHED)", "غرفة مضخات الحريق")
    p.text("FIRE WATER TANK (UNDERGROUND)\\P" + f"{fw['tank']} m3 NET", ((FIRE_TANK[0] + FIRE_TANK[2]) / 2, (FIRE_TANK[1] + FIRE_TANK[3]) / 2),
           1.7, "F-TEXT", angle=0)
    p.pline(rect(PUMP_ROOM), "F-PIPE", close=True)
    p.hatch(rect(PUMP_ROOM), "F-PIPE", color=1, pattern="ANSI31", scale=0.03)
    p.leader(((PUMP_ROOM[0] + PUMP_ROOM[2]) / 2, PUMP_ROOM[1] + 0.5), (12.9, -4.0), "FIRE PUMP ROOM", 1.6, "F-TEXT")
    if not full:
        return
    symbols.line_key(p.sh, "F-PIPE", "FIRE WATER MAIN HDPE 110 mm", "خط ماء الحريق الرئيسي", width_mm=0.5)
    symbols.line_key(p.sh, "F-PIPE", "PUMP SUCTION LINE", "خط سحب المضخات", linetype="DASHED", width_mm=0.35)
    symbols.line_key(p.sh, "F-PIPE", "SPRAY RING ROUND LPG TANK", "حلقة رش تبريد خزان الغاز", width_mm=0.25)
    symbols.line_key(p.sh, "F-TEXT", "DV = DELUGE VALVE", "صمام الاغراق", color=1)
    p.pline(MAIN, "F-PIPE", width_mm=0.5)
    p.pline(BRANCH_W, "F-PIPE", width_mm=0.5)
    p.pline(SUCTION, "F-PIPE", width_mm=0.35, linetype="DASHED", ltscale=0.3)
    for k, c in HYDRANTS.items():
        p.sym("FH", c)
        p.text(k, (c[0] + 1.6, c[1] - 1.4), 1.5, "F-TEXT", angle=0)
    for k, c in HOSE_REELS.items():
        p.sym("HR", c)
        p.text(k, (c[0] + 1.6, c[1] + 1.2), 1.4, "F-TEXT", angle=0)
    for a, b in (((20.0, 6.9), HOSE_REELS["HR-1"]), ((38.4, 6.9), (38.4, 5.75)), ((35.5, 33.0), HOSE_REELS["HR-3"]),
                 ((35.5, 51.4), (36.2, 53.6))):
        p.line(a, b, "F-PIPE")
    # LPG deluge: valve outside the compartment, spray rings round both tanks
    p.line((35.5, DELUGE[1]), DELUGE, "F-PIPE")
    p.tag("DV", DELUGE, 1.5, "F-TEXT", color=1)
    p.pline([DELUGE, (37.0, DELUGE[1]), (38.4, DELUGE[1]), (38.4, 33.2)], "F-PIPE", width_mm=0.35)
    for t in ("T-02", "T-03"):
        tk = safety.TANKS[t]
        r = tk["d"] / 2 + 0.45
        ring = [(tk["x0"] - 0.45, tk["yc"] - r), (tk["x1"] + 0.45, tk["yc"] - r), (tk["x1"] + 0.45, tk["yc"] + r), (tk["x0"] - 0.45, tk["yc"] + r)]
        p.pline(ring, "F-PIPE", close=True, width_mm=0.25)
        p.line((38.4, tk["yc"]), (tk["x0"] - 0.45, tk["yc"]), "F-PIPE")
        n = int((tk["x1"] - tk["x0"] + 0.9) / 1.5) + 1
        for k in range(n):
            x = tk["x0"] - 0.45 + k * (tk["x1"] - tk["x0"] + 0.9) / (n - 1)
            for y in (tk["yc"] - r, tk["yc"] + r):
                p.sym("WS", (x, y), scale=0.6)


fw = safety.fire_water()
checks = safety.separation_checks()
fails = [c for c in checks if not c["ok"]]
size = safety.tank_size_check()
bunds = safety.bunds()

# ================================================================== F-001 safety distances
sh, p = plan_sheet("F-001")
symbols.line_key(sh, "F-PASS", "MEASURED DISTANCE - COMPLIES", "مسافة مقاسة - مطابقة", color=GREEN)
symbols.line_key(sh, "F-FAIL", "MEASURED DISTANCE - SHORTFALL", "مسافة مقاسة - غير مطابقة", color=RED)
symbols.line_key(sh, "F-ZONE", "15 m FROM LPG TANKS", "مسافة 15 م من خزانات الغاز", color=RED, linetype="DASHED")
for c in checks:
    col = GREEN if c["ok"] else RED
    lay = "F-PASS" if c["ok"] else "F-FAIL"
    p.dist_line(c["p"], c["q"], f"{c['id']} {c['provided']:.2f}", lay, color=col, mm=1.5)
# 15 m LPG circle and 4.5 m fuel tank offset, for orientation
for t in safety.LPG_TANKS:
    g = safety.TANK_POLY[t].buffer(15.0, join_style=1)
    p.pline(list(g.exterior.coords), "F-ZONE", color=RED, linetype="DASHED", ltscale=0.5)
p.text("15 m FROM LPG TANKS", (30.0, 16.0), 1.6, "F-TEXT", color=RED)
x, y, w = panel(sh)
rows = [("REF", "SEPARATION", "REQ.", "PROV.", "")]
for c in checks:
    rows.append((c["id"], c["en"][:40], f"{c['required']:.2f}", f"{c['provided']:.2f}", "OK" if c["ok"] else "NO"))
yb = sh.table(249, 284, (7, 52, 8.5, 9, 6.5), rows, row_h=3.6, h=1.15, header_h=3.8,
              aligns=["LEFT", "LEFT", "RIGHT", "RIGHT", "CENTER"])
for k, c in enumerate(checks):
    if not c["ok"]:
        yy = 284 - 3.8 - 3.6 * (k + 0.5)
        sh.rect(249.3, yy - 1.6, 331.7, yy + 1.6, "F-FAIL")
src_lines = [f"{c['id']}: {c['source']}" for c in checks]
yb = notes(sh, 250, yb - 4, "SOURCES (VERIFY AGAINST OPDC)", src_lines, h=1.05, step=2.15)
over = [f"T-01/04/05/06 = 54 m3 > {safety.NFPA30A_MAX_AST} m3 (12,000 gal), THE LARGEST",
        "ABOVEGROUND TANK ALLOWED AT A MOTOR FUEL DISPENSING",
        "FACILITY BY NFPA 30A 4.3.2.3.1."]
notes(sh, 250, yb, "TANK SIZE CHECK - NOT COMPLIANT", over, h=1.2, step=2.5, layer="F-FAIL")
# remedies on the plan side
rem = [
    "SHORTFALLS (RED) AND PROPOSED REMEDIES - DECISION REQUIRED BEFORE STAGE 2:",
    "S1  LPG TANKS 3.75 m FROM THE RIGHT BOUNDARY (15 m REQUIRED): NOT ACHIEVABLE ON THIS PLOT WITH 23 m3",
    "     TANKS. REMEDY: LPG CONTAINERS <= 7.6 m3 W.C. EACH (7.6 m ABOVE GROUND / 3.0 m BURIED), OR",
    "     OPDC + CIVIL DEFENCE WAIVER WITH 4-HOUR FIRE WALL ON THE BOUNDARY AND WATER SPRAY (SHOWN ON F-002).",
    "S3  LPG TANK 3.00 m FROM PETROL TANK T-04 (6 m REQUIRED): SHIFT BOTH LPG TANKS 3.0 m TOWARDS THE LPG",
    "     PUMP (CLEARANCE TO PUMP 0.9 m) - FITS INSIDE COMPARTMENT C2.",
    "S5  FUEL TANKS 1.75 m FROM THE RIGHT BOUNDARY (4.5 m REQUIRED) AND TANKS ABOVE 45.4 m3:",
    "     REMEDY A: UNDERGROUND DOUBLE-WALL TANKS (NFPA 30 CH.23: 0.3 m TO BOUNDARY, NO SIZE LIMIT).",
    "     REMEDY B: OPDC WAIVER WITH PROTECTED (UL 2085) TANKS AND A 4-HOUR FIRE WALL ON THE BOUNDARY.",
]
for k, s in enumerate(rem):
    sh.text(s, 22, 56 - 3.1 * k, 1.4, "F-FAIL" if k == 0 else "G-TEXT")
sh.text(f"{len(checks) - len(fails)} OF {len(checks)} SEPARATIONS COMPLY - {len(fails)} SHORTFALLS", 22, 62, 2.2, "TB_HEADINGS")

# ================================================================== F-002 fire water network
sh, p = plan_sheet("F-002")
draw_fire_installation(p)
x, y, w = panel(sh)
calc = [
    f"LPG TANKS SURFACE (2 TANKS)      {fw['surface']} m2",
    f"WATER SPRAY {safety.SPRAY_RATE} L/min/m2         {fw['spray']} L/min",
    f"HYDRANT HOSE STREAMS (2 x 475)   {fw['hose']} L/min",
    f"DESIGN FLOW                      {fw['total']} L/min",
    f"DURATION                         {fw['duration']} min",
    f"REQUIRED VOLUME                  {fw['volume']} m3",
    f"FIRE TANK (NET)                  {fw['tank']} m3",
    "",
    "FIRE PUMPS (NFPA 20):",
    f"  MAIN ELECTRIC  {fw['pump_flow']} L/min @ {fw['pump_head']} m",
    f"  STANDBY DIESEL {fw['pump_flow']} L/min @ {fw['pump_head']} m",
    "  JOCKEY 50 L/min @ 80 m",
]
yb = notes(sh, 250, 282, "FIRE WATER DEMAND", calc, h=1.35, step=2.9)
spec = [
    "1. FIRE MAIN: HDPE PE100 PN16, 110 mm, BURIED",
    "   0.9 m MIN.; DUCTILE IRON ABOVE GROUND.",
    "2. HYDRANTS: PILLAR TYPE 2 x 65 mm INSTANTANEOUS",
    "   OUTLETS (IRAQI CIVIL DEFENCE COUPLING),",
    "   ISOLATING VALVE ON EACH BRANCH.",
    "3. HOSE REELS: 25 mm x 30 m, IN CABINETS.",
    "4. LPG TANK COOLING: AUTOMATIC DELUGE VALVE (DV)",
    "   OUTSIDE COMPARTMENT C2, OPEN NOZZLES ON A",
    "   RING 0.45 m CLEAR OF EACH TANK, 10.2 L/min/m2",
    "   OVER THE WHOLE TANK SURFACE (NFPA 15).",
    "5. DV OPENED BY HEAT/FLAME DETECTION OVER THE",
    "   LPG TANKS AND BY MANUAL RELEASE AT THE DV.",
    "6. FIRE TANK: RC, WATERPROOFED, TRAFFIC-RATED",
    "   ROOF, FILLED FROM THE MAINS (P-001), WITH A",
    "   CIVIL DEFENCE INLET BREECHING AT THE FRONT.",
    "7. SEE F-006 FOR THE PUMP SET AND RISER DIAGRAM.",
]
notes(sh, 250, yb, "SPECIFICATION", spec, h=1.3, step=2.7)

# ================================================================== F-003 extinguishers
sh, p = plan_sheet("F-003")
ext = safety.extinguishers()
placed = Counter()


def put(code, pt, label=None):
    p.sym(code, pt)
    placed[code] += 1


for isl in I["islands"]:
    for d in isl["dispensers"]:
        put("FE-P", (d[0] - 1.0, d[1] + 1.4) if isl["tag"] in ("I-1", "I-2", "I-3") else (d[0], d[1] - 1.5))
for c in ((13.0, 13.0), (26.5, 33.0)):
    put("FE-W", c)
put("FE-W", (47.0, 54.5))
for f in I["fill_points"]:
    put("FE-P", (f["xy"][0] - 1.6, f["xy"][1] + 1.6))
put("FE-W", (34.0, 18.0))
for c in ((34.0, 37.0), (34.0, 44.0)):
    put("FE-F", c)
for c in ((36.0, 16.0), (36.0, 26.0), (36.0, 47.5)):
    put("FE-W", c)
put("FE-F", (36.0, 45.5))
put("FE-P", (39.6, 21.5))
rooms = I["rooms"]


def room_c(k, dx=0.0, dy=0.0):
    b = rooms[k]
    return ((b[0] + b[2]) / 2 + dx, (b[1] + b[3]) / 2 + dy)


for k, code, dx in (("transformer", "FE-C", -1.0), ("transformer", "FE-C", 1.0), ("generator", "FE-C", -0.8),
                    ("generator", "FE-P", 0.8), ("admin", "FE-C", -0.8), ("admin", "FE-P", 0.8), ("workers", "FE-P", 0),
                    ("spares", "FE-P", 0), ("paints", "FE-P", -0.8), ("paints", "FE-C", 0.8), ("prayer", "FE-P", 0)):
    put(code, room_c(k, dx, 1.2))
put("FE-P", ((PUMP_ROOM[0] + PUMP_ROOM[2]) / 2, PUMP_ROOM[3] - 0.6))
draw_fire_installation(p, full=False)
need = Counter()
for _l, t, q in ext:
    need[t] += q
assert need == placed, (need, placed)
rows = [("LOCATION", "TYPE", "QTY")] + [(l[:34], t, str(q)) for l, t, q in ext]
yb = sh.table(249, 284, (56, 13, 14), rows, row_h=3.4, h=1.15, header_h=3.8, aligns=["LEFT", "CENTER", "CENTER"])
tot = [f"{t}  {dict((c, en) for g in symbols.SYMBOLS.values() for c, _l, en, _a, _f in g)[t][:36]}: {n}" for t, n in sorted(need.items())]
yb = notes(sh, 250, yb - 4, "TOTALS", tot, h=1.25, step=2.6)
notes(sh, 250, yb, "NOTES", [
    "1. MOUNT PORTABLE UNITS WITH THE TOP <= 1.5 m",
    "   ABOVE FLOOR, IN CABINETS OUTDOORS.",
    "2. MAX. TRAVEL DISTANCE TO A UNIT 15 m (CLASS B).",
    "3. CO2 ONLY IN ELECTRICAL ROOMS; NO WATER TYPE",
    "   NEAR ELECTRICAL EQUIPMENT.",
    "4. INSPECT MONTHLY, SERVICE YEARLY (NFPA 10).",
], h=1.25, step=2.6)

# ================================================================== F-004 fire alarm and ESD
sh, p = plan_sheet("F-004")
for k in ("admin", "workers", "spares", "paints", "prayer", "stair"):
    p.sym("SD", room_c(k, 0, -0.6))
for k in ("transformer", "generator"):
    p.sym("HD", room_c(k, 0, -0.6))
p.sym("HD", ((PUMP_ROOM[0] + PUMP_ROOM[2]) / 2, 2.4))
p.sym("FACP", (18.4, 2.2))
p.text("FACP IN ADMINISTRATION", (18.4, -2.5), 1.4, "F-TEXT", angle=0)
for c in ((3.3, 6.2), (10.0, 6.2), (16.0, 5.7), (23.3, 6.4), (34.0, 5.7), (38.0, 5.7), (42.0, 5.7)):
    p.sym("MCP", c)
for c in ((6.0, 6.3), (27.4, 5.7), (44.4, 5.7)):
    p.sym("SNDR", c)
esd = [isl["post"] for isl in I["islands"] if isl["post"]] + [(35.0, 29.6), (35.0, 41.0), (17.6, 4.4), (33.0, 53.4), (36.6, 24.5)]
for c in esd:
    p.sym("ESD", c if isinstance(c, tuple) else tuple(c))
for c in ((14.25, 5.5), (2.0, 7.2), (35.0, 12.0), (37.0, 54.2)):
    p.sym("EXIT", c)
x, y, w = panel(sh)
notes(sh, 250, 282, "FIRE ALARM", [
    "CONVENTIONAL 4-ZONE PANEL (NFPA 72 / EN 54):",
    "Z1 BUILDING 1 (TRANSFORMER, GENERATOR)",
    "Z2 BUILDING 2 (WC, ADMIN, STAIR, WORKERS)",
    "Z3 BUILDING 3 (SHOPS, PRAYER, WC)",
    "Z4 FIRE PUMP ROOM + LPG DELUGE STATUS",
    "CABLE: FIRE-RESISTANT 2 x 1.5 mm2 (PH120).",
    "STANDBY BATTERIES 24 h + 30 min ALARM.",
], h=1.3, step=2.7)
notes(sh, 250, 250, "EMERGENCY SHUT-DOWN (ESD)", [
    f"{len(esd)} RED MUSHROOM PUSH BUTTONS (STAY-PUT):",
    "AT EVERY ISLAND, THE UNLOADING POINTS, THE",
    "LPG COMPARTMENT, THE OFFICE AND THE GATE.",
    "ANY BUTTON TRIPS: ALL DISPENSERS, SUBMERSIBLE",
    "AND TRANSFER PUMPS, LPG PUMP AND THE CANOPY",
    "POWER (NFPA 30A 6.7). FIRE PUMPS, FIRE ALARM",
    "AND EMERGENCY LIGHTING STAY ON.",
    "RESET ONLY AT THE PANEL IN THE OFFICE.",
    "BUTTONS 6 - 30 m FROM DISPENSERS, IN VIEW.",
], h=1.3, step=2.7)
notes(sh, 250, 215, "SAFETY SIGNS (ARABIC + ENGLISH)", [
    "NO SMOKING / NO NAKED FLAME - AT EVERY ISLAND,",
    "  THE TANK AREA AND THE UNLOADING POINTS.",
    "STOP ENGINE - SWITCH OFF MOBILE PHONES.",
    "LPG - FLAMMABLE GAS (TANK COMPARTMENT C2).",
    "EMERGENCY SHUT-DOWN - AT EVERY ESD BUTTON.",
    "FIRE EXIT / ASSEMBLY POINT - SEE F-005.",
], h=1.3, step=2.7)

# ================================================================== F-005 evacuation
sh, p = plan_sheet("F-005")
p.sym("AP", ASSEMBLY, scale=1.4)
p.text("ASSEMBLY POINT", (ASSEMBLY[0] + 2.5, ASSEMBLY[1] + 2.0), 1.8, "F-ROUTE", angle=0, attach="ML")
routes = [
    [(18.5, 6.4), (8.0, 8.5), (3.3, 25.0)],
    [(40.0, 6.4), (30.0, 9.5), (10.0, 11.0), (3.8, 25.0)],
    [(20.0, 26.0), (8.0, 26.5), (4.8, 27.0)],
    [(34.5, 45.0), (30.0, 40.0), (12.0, 30.0), (4.9, 27.6)],
    [(5.0, 6.3), (3.0, 10.0), (2.8, 25.0)],
]
for r in routes:
    p.pline(r, "F-ROUTE", width_mm=0.6, color=GREEN)
    a, b = r[-2], r[-1]
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    s = 1.6 * sh.f
    p.hatch([b, (b[0] - s * math.cos(ang - 0.4), b[1] - s * math.sin(ang - 0.4)),
             (b[0] - s * math.cos(ang + 0.4), b[1] - s * math.sin(ang + 0.4))], "F-ROUTE", color=GREEN)
from site_base import fr  # noqa: E402
tanker = [fr(36.3, 1.5), (34.4, 48.0), (34.4, 10.5), (31.0, 8.8), (13.0, 8.8), (9.5, 10.5), (8.0, 20.0), (6.5, 33.0)]
p.pline(tanker, "F-TANKER", width_mm=0.5, color=30, linetype="DASHED", ltscale=0.6)
symbols.line_key(sh, "F-ROUTE", "ESCAPE ROUTE TO ASSEMBLY POINT", "مسار الاخلاء الى نقطة التجمع", color=GREEN, width_mm=0.6)
symbols.line_key(sh, "F-TANKER", "FUEL TANKER ROUTE", "مسار الصهريج", color=30, linetype="DASHED", width_mm=0.5)
p.text("TANKER ROUTE: IN AT THE ENTRY, UNLOAD FORWARD-FACING AT THE CURB, OUT THROUGH THE EXIT - NO REVERSING",
       (20.0, 9.9), 1.35, "F-TEXT", color=30)
for gate, lab in (("exit", "EXIT 10 m"), ("entry", "ENTRY 10 m"), ("yard", "YARD GATE 5 m")):
    s0, s1 = I["gates"][gate]
    p.text(lab, fr((s0 + s1) / 2, -2.2), 1.8, "F-TEXT", color=GREEN)
draw_fire_installation(p, full=False)
notes(sh, 250, 282, "EVACUATION", [
    "1. ON ALARM: STOP ALL DISPENSING (ESD), STOP",
    "   UNLOADING, CLOSE TANKER VALVES.",
    "2. STAFF AND CUSTOMERS WALK TO THE ASSEMBLY",
    "   POINT AT THE FRONT-LEFT CORNER, AWAY FROM",
    "   THE TANKS (> 30 m), AS SHOWN.",
    "3. GATES STAY OPEN FOR CIVIL DEFENCE VEHICLES;",
    "   CLEAR WIDTH 10 m AT ENTRY AND EXIT.",
    "4. A TANKER UNLOADS ONLY WHEN THE STATION",
    "   ATTENDANT, EXTINGUISHERS AND THE STATIC",
    "   EARTH CLAMP ARE IN PLACE (E-009).",
    "5. ROUTES ARE PAVED, LIT (E-004) AND KEPT",
    "   FREE OF PARKED VEHICLES.",
], h=1.3, step=2.7)

# ================================================================== F-006 fire water schematic (NTS)
_, title, subtitle, _ = entry("F-006")
sh = ss.add("F-006", title, subtitle, 300, scale_text="NTS", scale_bar=False)
sh.window = KEY
T, L = sh.text, sh.line


def box_(x0, y0, x1, y1, label, h=1.8, layer="F-PIPE"):
    sh.rect(x0, y0, x1, y1, layer)
    T(label, (x0 + x1) / 2, (y0 + y1) / 2 - 0.4 * h - 0.6 * h * (label.count("\\P")), h, "F-TEXT", align="MIDDLE")


box_(30, 60, 100, 110, f"FIRE WATER TANK\\P{fw['tank']} m3 NET (UNDERGROUND RC)")
T("FROM MUNICIPAL MAINS (P-001)", 32, 115, 1.6, "F-TEXT")
L((65, 113), (65, 110), "F-PIPE")
pumps = [("JOCKEY PUMP", "50 L/min @ 80 m", 150), ("MAIN ELECTRIC PUMP", f"{fw['pump_flow']} L/min @ {fw['pump_head']} m", 120),
         ("STANDBY DIESEL PUMP", f"{fw['pump_flow']} L/min @ {fw['pump_head']} m", 90)]
for name, duty, yy in pumps:
    L((100, yy - 25 if yy < 110 else 95), (100, 95), "F-PIPE") if False else None
for k, (name, duty, yy) in enumerate(pumps):
    y = 70 + k * 22
    L((100, 75), (115, 75), "F-PIPE")
    L((115, 75), (115, y), "F-PIPE")
    L((115, y), (130, y), "F-PIPE")
    symbols.insert(sh, "GV", sh.p(124, y), "F-PIPE")
    symbols.insert(sh, "FP", sh.p(137, y), "F-PIPE", scale=1.6)
    L((141, y), (160, y), "F-PIPE")
    symbols.insert(sh, "NRV", sh.p(149, y), "F-PIPE")
    symbols.insert(sh, "GV", sh.p(156, y), "F-PIPE")
    L((160, y), (170, y), "F-PIPE")
    T(name, 128, y + 4.5, 1.6, "F-TEXT")
    T(duty, 128, y - 6.5, 1.4, "F-TEXT")
L((170, 70), (170, 150), "F-PIPE")
T("SUCTION", 103, 77, 1.4, "F-TEXT")
T("DISCHARGE HEADER 150 mm", 172, 152, 1.6, "F-TEXT")
box_(176, 108, 206, 122, "PRESSURE\\PSWITCHES", 1.4)
L((170, 115), (176, 115), "F-PIPE")
box_(176, 82, 206, 98, "TEST HEADER\\P+ FLOW METER", 1.4)
L((170, 90), (176, 90), "F-PIPE")
L((170, 150), (230, 150), "F-PIPE")
outs = [(230, 205, "FH-1 PILLAR HYDRANT"), (230, 190, "FH-2 PILLAR HYDRANT"), (230, 175, "FH-3 PILLAR HYDRANT"),
        (230, 160, "HR-1 .. HR-4 HOSE REELS"), (230, 140, "DV-1 DELUGE VALVE -> SPRAY RINGS T-02 / T-03")]
L((230, 140), (230, 205), "F-PIPE")
for x0, y0, lab in outs:
    L((x0, y0), (245, y0), "F-PIPE")
    symbols.insert(sh, "GV", sh.p(238, y0), "F-PIPE")
    T(lab, 248, y0 - 0.7, 1.6, "F-TEXT")
box_(30, 140, 100, 165, "CIVIL DEFENCE INLET\\P2 x 65 mm BREECHING (FRONT)", 1.5)
L((100, 152), (170, 152), "F-PIPE")
symbols.insert(sh, "NRV", sh.p(135, 152), "F-PIPE")
T("FIRE WATER SYSTEM - SCHEMATIC (NOT TO SCALE)", 30, 270, 3.0, "TB_HEADINGS")
sh.legend_at = (249.0, 15.0)
symbols.line_key(sh, "F-PIPE", "FIRE WATER PIPE", "انبوب ماء الحريق")
for k, s in enumerate([
    "1. PUMP SET TO NFPA 20: JOCKEY STARTS AT 7.0 bar, MAIN AT 6.0 bar, DIESEL AT 5.5 bar;",
    "   MAIN AND DIESEL STOP MANUALLY ONLY.",
    "2. DIESEL PUMP WITH ITS OWN 8 h FUEL TANK AND TWO BATTERY SETS; EXHAUST LED OUTSIDE.",
    "3. MAIN PUMP FED FROM THE MDB AHEAD OF THE MAIN BREAKER AND FROM THE GENERATOR (E-007).",
    f"4. DESIGN FLOW {fw['total']} L/min FOR {fw['duration']} min = {fw['volume']} m3; TANK {fw['tank']} m3 NET.",
    "5. ALL VALVES LOCKED OPEN; PUMP RUN AND FAULT SIGNALS TO THE FIRE ALARM PANEL.",
]):
    T(s, 30, 255 - 4.0 * k, 1.7, "G-TEXT")

# ================================================================== F-007 bunds (1:150, tank area turned to horizontal)
_, title, subtitle, _ = entry("F-007")
sh = ss.add("F-007", title, subtitle, 150)
sh.window = (30, 5, 60, 45)
T = sh.text
K = 1000 / 150
OX, OY = 30.0, 268.0                         # paper position of plot point (x=37, y=12)


def q(x, y):
    """Plot point -> paper mm: plot y along the paper x axis, plot x downwards."""
    return (OX + (y - 12.0) * K, OY - (x - 37.0) * K)


def qline(a, b, layer="S-CONC"):
    sh.line(q(*a), q(*b), layer)


def qrect(x0, y0, x1, y1, layer="S-CONC"):
    pts = [q(x0, y0), q(x1, y0), q(x1, y1), q(x0, y1)]
    sh.msp.add_lwpolyline([sh.p(*pp) for pp in pts], close=True, dxfattribs={"layer": layer})


ta = I["tank_area"]
qrect(ta["x0"], ta["walls_y"][0], ta["x1"], ta["walls_y"][-1] + ta["wt"])
qrect(ta["x0"] + ta["wt"], ta["walls_y"][0] + ta["wt"], ta["x1"] - ta["wt"], ta["walls_y"][-1])
for yw in ta["walls_y"][1:-1]:
    qrect(ta["x0"] + ta["wt"], yw, ta["x1"] - ta["wt"], yw + ta["wt"])
for t in I["tanks"]:
    r = t["d"] / 2
    qrect(t["x0"], t["yc"] - r, t["x1"], t["yc"] + r, "F-SYMB")
    tx, ty = q((t["x0"] + t["x1"]) / 2, t["yc"])
    T(t["tag"], tx, ty - 0.8, 2.0, "F-TEXT", align="MIDDLE")
    for sx in (t["x0"] + 1.6, t["x1"] - 1.6):
        qrect(sx - 0.25, t["yc"] - r - 0.1, sx + 0.25, t["yc"] + r + 0.1, "S-CONC")
bdict = {b["cmp"]: b for b in bunds}
cmps = I["compartments"]
for key, label in (("C1", "C1 GAS OIL BUND"), ("C2", "C2 LPG - NOT BUNDED"), ("C3a", "C3 PETROL + KEROSENE BUND")):
    x0, y0, x1, y1 = cmps[key]
    tx, ty = q(x0 + 0.7, (y0 + y1) / 2)
    T(label, tx, ty, 1.8, "F-TEXT", align="MIDDLE")
    if key != "C2":
        sx, sy = q(x1 - 0.7, y0 + 0.8)
        sh.rect(sx - 2.5, sy - 2.5, sx + 2.5, sy + 2.5, "F-PIPE")
        T("SUMP", sx, sy - 5.0, 1.4, "F-TEXT", align="MIDDLE")
        symbols.insert(sh, "GV", sh.p(sx + 9, sy), "F-PIPE")
        sh.line((sx + 2.5, sy), (sx + 18, sy), "F-PIPE")
        T("LOCKED DRAIN VALVE -> OIL SEPARATOR (P-003)", sx - 2.5, sy - 9.5, 1.3, "F-TEXT")
x0, y0, x1, y1 = cmps["C3b"]
tx, ty = q(x0 + 0.7, (y0 + y1) / 2)
T("C3 (CONT.) - KERB 0.30 ONLY", tx, ty, 1.5, "F-TEXT", align="MIDDLE")
rows = [("BUND", "TANKS", "AREA m2", "LARGEST x 1.10", "h MIN", "WALL h", "NET m3")]
for b in bunds:
    rows.append((b["cmp"], " ".join(b["tanks"]), f"{b['area']:.1f}", f"{b['required']:.1f}", f"{b['h_min']:.2f}",
                 f"{b['h']:.2f}", f"{b['net']:.1f}"))
yb = sh.table(30, 160, (14, 40, 18, 26, 14, 14, 16), rows, row_h=5.0, h=1.6, header_h=5.0,
              aligns=["LEFT", "LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"])
for k, s in enumerate([
    f"1. NET CAPACITY = FLOOR AREA x h - TANK VOLUME BELOW h (TANK BOTTOM {safety.SADDLE_H:.2f} m ABOVE FLOOR) - SADDLES.",
    "2. REQUIRED: 110 % OF THE LARGEST TANK (NFPA 30 22.11.2 ASKS 100 %); WALL h = h MIN + 0.15 FREEBOARD.",
    "3. C3a AND C3b FORM ONE BUND; THE WALL BETWEEN THEM IS CUT DOWN TO A 0.30 m KERB.",
    "4. LPG COMPARTMENT C2 IS NOT BUNDED: FLOOR FALLS 1 % AWAY FROM UNDER THE TANKS TO AN OPEN",
    "   GULLY OUTSIDE (NFPA 58 6.4.5 - NO LPG CONTAINER INSIDE A FLAMMABLE LIQUID DIKE).",
    "5. BUND FLOOR 1 % TO THE SUMP; WALLS AND FLOOR LIQUID-TIGHT RC TO ACI 350 (S-005).",
    "6. DRAIN VALVES KEPT CLOSED AND LOCKED; RAINWATER RELEASED ONLY AFTER INSPECTION.",
]):
    T(s, 30, yb - 6 - 3.4 * k, 1.6, "G-TEXT")
T("TANK AREA - BUND PLAN 1:150", 30, 280, 3.0, "TB_HEADINGS")
sh.legend_at = (130.0, 15.0)
symbols.line_key(sh, "S-CONC", "RC BUND / COMPARTMENT WALL, SADDLE", "جدار الحوض الخرساني، قاعدة الخزان")
symbols.line_key(sh, "F-SYMB", "ABOVEGROUND TANK (OUTLINE)", "خزان فوق الارض")
symbols.line_key(sh, "F-PIPE", "SUMP AND DRAIN PIPE", "حوضة التجميع وانبوب التصريف")
# typical bund section
SX, SY = 225, 70
sh.rect(SX, SY, SX + 4, SY + 6.67, "S-CONC")
sh.rect(SX, SY - 2.0, SX + 90, SY, "S-CONC")
sh.msp.add_circle(sh.p(SX + 40, SY + 4 + 9.2), 9.2 * sh.f, dxfattribs={"layer": "F-SYMB"})
for sx in (SX + 30, SX + 50):
    sh.rect(sx - 2, SY, sx + 2, SY + 4.0, "S-CONC")
T("TYPICAL BUND SECTION 1:150", SX, SY + 30, 2.2, "TB_HEADINGS")
T("WALL h (TABLE)", SX + 5, SY + 3, 1.4, "F-TEXT")
T("SADDLE", SX + 52, SY + 1, 1.3, "F-TEXT")

# ================================================================== F-008 typical details (NTS)
_, title, subtitle, _ = entry("F-008")
sh = ss.add("F-008", title, subtitle, 300, scale_text="NTS", scale_bar=False)
sh.window = KEY
T = sh.text


def det(x, y, w, h, title_):
    sh.rect(x, y, x + w, y + h, "TB_LINES_THIN")
    T(title_, x + 2, y + h - 5, 2.0, "TB_HEADINGS")


det(25, 160, 100, 120, "1  EXTINGUISHER CABINET")
sh.rect(55, 185, 95, 255, "F-SYMB")
sh.rect(58, 188, 92, 252, "F-SYMB")
symbols.insert(sh, "FE-P", sh.p(75, 215), "F-SYMB", scale=6)
T("STEEL CABINET, RED, 1.2 mm", 30, 175, 1.5, "G-TEXT")
T("GLASS FRONT, TOP <= 1.5 m ABOVE GROUND", 30, 171, 1.5, "G-TEXT")
T("PLATE: 'EXTINGUISHER - طفاية حريق'", 30, 167, 1.5, "G-TEXT")
det(130, 160, 100, 120, "2  PILLAR HYDRANT")
sh.rect(172, 185, 188, 245, "F-SYMB")
sh.msp.add_circle(sh.p(180, 245), 8 * sh.f, dxfattribs={"layer": "F-SYMB"})
for yy in (225, 210):
    sh.rect(160, yy - 3, 172, yy + 3, "F-SYMB")
    sh.rect(188, yy - 3, 200, yy + 3, "F-SYMB")
sh.line((140, 185), (220, 185), "S-CONC")
T("FINISHED GROUND", 141, 187, 1.4, "G-TEXT")
T("2 x 65 mm OUTLETS, BREAKABLE BASE, DRAIN", 135, 175, 1.5, "G-TEXT")
T("VALVE; ISOLATING VALVE IN A CHAMBER 1.5 m", 135, 171, 1.5, "G-TEXT")
T("AWAY; THRUST BLOCK; 0.9 m MIN COVER.", 135, 167, 1.5, "G-TEXT")
det(235, 160, 100, 120, "3  ESD PUSH BUTTON")
sh.rect(270, 210, 300, 245, "F-SYMB")
sh.msp.add_circle(sh.p(285, 228), 8 * sh.f, dxfattribs={"layer": "F-SYMB"})
T("EMERGENCY STOP", 285, 249, 1.6, "F-TEXT", align="CENTER")
T("ايقاف الطوارئ", 285, 203, 1.8, "F-TEXT", align="CENTER")
T("Ex d IIB T4 STATION, RED MUSHROOM, LATCHING", 240, 175, 1.5, "G-TEXT")
T("ON A POST 1.2 m ABOVE GROUND; ALL BUTTONS", 240, 171, 1.5, "G-TEXT")
T("IN SERIES IN THE DISPENSER CONTROL CIRCUIT.", 240, 167, 1.5, "G-TEXT")
det(25, 20, 310, 130, "4  SAFETY SIGNS (MIN. 600 x 400 mm, REFLECTIVE)")
sh.legend_at = False
signs = [("NO SMOKING", "ممنوع التدخين"), ("STOP ENGINE", "اطفئ المحرك"), ("NO MOBILE PHONES", "ممنوع استخدام الهاتف"),
         ("LPG - FLAMMABLE GAS", "غاز سائل - قابل للاشتعال"), ("EMERGENCY STOP", "ايقاف الطوارئ"), ("ASSEMBLY POINT", "نقطة تجمع")]
for k, (en, ar) in enumerate(signs):
    x = 35 + (k % 3) * 100
    y = 95 - (k // 3) * 55
    sh.rect(x, y, x + 85, y + 40, "F-SYMB")
    sh.msp.add_circle(sh.p(x + 15, y + 20), 11 * sh.f, dxfattribs={"layer": "F-SYMB"})
    sh.line((x + 7.2, y + 12.2), (x + 22.8, y + 27.8), "F-SYMB")
    T(en, x + 30, y + 24, 2.4, "F-TEXT")
    T(ar, x + 82, y + 12, 2.6, "F-TEXT", align="RIGHT")

ss.finish(OUT)
print("saved", OUT, "-", len(fails), "separation shortfalls")
