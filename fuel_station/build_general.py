"""General sheets G-001 .. G-003: cover and drawing register, legend, design basis.

usage: python build_general.py OUT.dxf
"""
import os
import sys

import calcs
import symbols
from register import REGISTER, STAGE_STATUS, entry
from sheets import SheetSet, import_site_block

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "G_GENERAL.dxf")

ss = SheetSet()
symbols.define(ss.doc)
import_site_block(ss.doc, os.path.join(HERE, "FUEL_STATION_SITE_PLAN.dxf"))
SITE_WINDOW = (-19.0, -4.0, 63.0, 55.5)


def sheet(number, den=300, **kw):
    _, title, subtitle, _ = entry(number)
    return ss.add(number, title, subtitle, den, **kw)


# ------------------------------------------------------------------ G-001 cover + register
g1 = sheet("G-001", scale_text="NTS", scale_bar=False)
g1.window = SITE_WINDOW
T = g1.text
T("FUEL FILLING STATION", 25, 268, 8.0, "TB_HEADINGS")
T("محطة تعبئة وقود - القطعة المرقمة (1 / 3453) مقاطعة (43) يارمجة الشرقية", 172, 258, 2.7, "G-TEXT", align="RIGHT")
T("قضاء الموصل / محافظة نينوى - للمواطنين (هادي حسين جمعة - احمد عثمان عيد)", 172, 252.5, 2.7, "G-TEXT", align="RIGHT")
T("ELECTRICAL - CIVIL DEFENCE - SANITARY - STRUCTURAL", 25, 243, 3.4, "TB_HEADINGS")
T("DESIGN DRAWINGS, ISSUE 00 (STAGE 0: GENERAL SHEETS)", 25, 237.5, 2.6, "G-TEXT")
T("OWNERS: HADI HUSSEIN JUMAA - AHMED OTHMAN EID", 25, 232, 2.2, "G-TEXT")
g1.line((25, 228), (172, 228), "TB_LINES_THICK")
# site thumbnail
k = 0.62
cx, cy = g1.p(98, 150)
wx = (SITE_WINDOW[0] + SITE_WINDOW[2]) / 2
wy = (SITE_WINDOW[1] + SITE_WINDOW[3]) / 2
ss.msp.add_blockref("X-ARCH-SITE", (cx - wx * k, cy - wy * k),
                    dxfattribs={"layer": "X-ARCH", "xscale": k, "yscale": k})
T("SITE PLAN (REFERENCE - SEE FUEL_STATION_SITE_PLAN.dxf)", 25, 52, 2.0, "TB_LABELS")
T(f"PLOT AREA {calcs.PLOT_AREA:,.2f} m2   -   STREET FRONT {calcs.FRONT:.2f} m", 25, 47.5, 1.9, "G-TEXT")
s = calcs.summary()
T(f"ABOVE-GROUND STORAGE {s['total_storage']} m3 IN {len(calcs.TANKS)} TANKS   -   "
  f"{s['dispensers']} DISPENSERS", 25, 43.5, 1.9, "G-TEXT")
# register
rows = [("No.", "DRAWING", "TITLE", "STATUS")]
for n, (num, title, sub, stage) in enumerate(REGISTER, 1):
    rows.append((f"{n:02d}", num, f"{title} - {sub}", STAGE_STATUS[stage]))
T("DRAWING REGISTER", 180, 279.5, 3.0, "TB_HEADINGS")
y = g1.table(180, 277, (8, 15, 98, 34), rows, row_h=6.55, h=1.55, header_h=5.0)
T("STAGE 6 (S-008, S-009 AND THE CANOPY PARTS OF E-004, E-008, E-010, P-003) STARTS", 180, y - 4.0, 1.5, "G-TEXT")
T("AFTER THE ARCHITECTURAL 3D ELEVATIONS AND THE CANOPY FORM ARE APPROVED.", 180, y - 6.6, 1.5, "G-TEXT")

# ------------------------------------------------------------------ G-002 legend
g2 = sheet("G-002", scale_text="NTS", scale_bar=False)
g2.window = SITE_WINDOW
ROW = 6.0
WID = (14, 14, 64, 60)


def legend(sh, x, y, group, items):
    sh.text(group, x, y + 1.5, 2.6, "TB_HEADINGS")
    rows = [("SYMBOL", "CODE", "DESCRIPTION", "الوصف")] + [("", c, en, ar) for c, _l, en, ar, _f in items]
    bottom = sh.table(x, y, WID, rows, row_h=ROW, h=1.5, header_h=4.5)
    yy = y - 4.5 - ROW / 2
    for c, layer, *_ in items:
        symbols.insert(sh, c, sh.p(x + WID[0] / 2, yy), layer)
        yy -= ROW
    return bottom


y = legend(g2, 22, 278, "CIVIL DEFENCE", symbols.SYMBOLS["CIVIL DEFENCE"])
y = legend(g2, 22, y - 9, "STRUCTURAL", symbols.SYMBOLS["STRUCTURAL"])
y_r = legend(g2, 178, 278, "ELECTRICAL", symbols.SYMBOLS["ELECTRICAL"])
y_r = legend(g2, 178, y_r - 9, "SANITARY", symbols.SYMBOLS["SANITARY"])
g2.text("LINE TYPES", 178, y_r - 7.5, 2.6, "TB_HEADINGS")
rows = [("LINE", "LAYER", "DESCRIPTION", "الوصف")] + [("", lay, en, ar) for lay, _lt, en, ar in symbols.LINE_TYPES]
g2.table(178, y_r - 9, WID, rows, row_h=ROW, h=1.5, header_h=4.5)
yy = y_r - 9 - 4.5 - ROW / 2
for lay, lt, *_ in symbols.LINE_TYPES:
    ss.msp.add_line(g2.p(180, yy), g2.p(190, yy), dxfattribs={"layer": lay, "linetype": lt, "ltscale": 0.5,
                                                             "lineweight": 50 if lay == "E-HAZD" else -1})
    yy -= ROW

# ------------------------------------------------------------------ G-003 design basis
g3 = sheet("G-003", scale_text="NTS", scale_bar=False)
g3.window = SITE_WINDOW


def block(sh, x, y, heading, lines, h=1.7, step=3.3):
    sh.text(heading, x, y, 2.6, "TB_HEADINGS")
    y -= 5.0
    for ln in lines:
        sub = not ln.startswith(" ")
        sh.text(ln.strip() if not sub else ln, x if sub else x + 3, y, h, "TB_LABELS" if sub and ln.isupper() else "G-TEXT")
        y -= step
    return y - 3.0


data = [
    "SITE",
    f"  PLOT AREA {calcs.PLOT_AREA:,.2f} m2 (RIGHT TRAPEZOID 50 x 30.59 / 66.02)",
    f"  STREET FRONT {calcs.FRONT:.2f} m, ONE EXIT 10 m, ONE ENTRY 10 m, YARD GATE 5 m",
    "PRODUCTS AND STORAGE (ALL TANKS ABOVE GROUND IN RC BUNDS)",
]
for prod, (n, v) in s["by_product"].items():
    data.append(f"  {prod:<9} {n} TANK(S)   {v} m3")
data += [
    f"  TOTAL {s['total_storage']} m3 - BUND COMPARTMENTS C1 (GAS OIL), C2 (LPG), C3 (PETROL, KEROSENE)",
    "DISPENSING",
] + [f"  {isl}  {prod:<22} {n} DISPENSER(S)" for isl, prod, n in calcs.DISPENSERS] + [
    "UTILITIES",
    "  POWER: 11 kV SUPPLY, DEDICATED 11/0.4 kV TRANSFORMER IN THE TRANSFORMER",
    "    ROOM, STANDBY DIESEL GENERATOR WITH AUTOMATIC TRANSFER SWITCH.",
    "  WATER: MUNICIPAL MAINS + GROUND STORAGE TANK + BOOSTER PUMP.",
    "  DRAINAGE: NO PUBLIC SEWER - SEPTIC TANK AND SOAKAWAY; OILY WATER",
    "    THROUGH AN OIL SEPARATOR BEFORE DISPOSAL.",
    "DESIGN ASSUMPTIONS (TO BE CONFIRMED)",
    f"  ALLOWABLE SOIL BEARING {calcs.SOIL_BEARING} kN/m2 PENDING A SOIL INVESTIGATION.",
    "  BUILDINGS: REINFORCED CONCRETE FRAME AND SOLID ROOF SLAB.",
    "  CANOPY: FORM AND STRUCTURE PENDING ARCHITECTURAL DESIGN (STAGE 6).",
    "  NORTH POINT NOT SHOWN ON THE SOURCE PLAN - TO BE CONFIRMED ON SITE.",
]
y1 = block(g3, 22, 280, "PROJECT DATA", data, h=2.0, step=4.15)

codes_iq = [
    "IRAQI BUILDING CODES (IRAQI BUILDING COUNCIL - MINISTRY OF",
    "CONSTRUCTION AND HOUSING):",
    "  مدونة التأسيسات الكهربائية - الطبعة الاولى 2016",
    "  المواصفات الفنية للأعمال الكهربائية 2015",
    "  مدونة التأسيسات المائية في المباني",
    "  المواصفات الفنية للأعمال الصحية",
    "  مدونات الاحمال والخرسانة المسلحة والزلازل العراقية",
    "CIVIL DEFENCE DIRECTORATE REQUIREMENTS (مديرية الدفاع المدني).",
    "OIL PRODUCTS DISTRIBUTION COMPANY (MINISTRY OF OIL):",
    "  INSTRUCTIONS FOR PRIVATE FUEL FILLING STATIONS - LATEST",
    "  EDITION TO BE OBTAINED; CLAUSES MARKED (OPDC) ARE TO BE",
    "  VERIFIED AGAINST IT.",
]
codes_int = [
    "NFPA 30 / NFPA 30A   FLAMMABLE LIQUIDS / MOTOR FUEL DISPENSING",
    "NFPA 58              LIQUEFIED PETROLEUM GAS CODE",
    "NFPA 10 / 15 / 72    EXTINGUISHERS / WATER SPRAY / FIRE ALARM",
    "NFPA 70 ART. 514     MOTOR FUEL DISPENSING FACILITIES",
    "IEC 60079-10-1       HAZARDOUS AREA CLASSIFICATION",
    "EI MODEL CODE PART 15 AREA CLASSIFICATION (PETROLEUM)",
    "IEC 60364 / IEC 62305 LV INSTALLATIONS / LIGHTNING PROTECTION",
    "ACI 318 / ACI 350    STRUCTURAL CONCRETE / LIQUID-RETAINING",
    "IPC                  INTERNATIONAL PLUMBING CODE (REFERENCE)",
]
y2 = block(g3, 182, 280, "IRAQI CODES AND AUTHORITY REQUIREMENTS", codes_iq, h=2.0, step=4.3)
y2 = block(g3, 182, y2, "INTERNATIONAL STANDARDS", codes_int, h=1.9, step=4.0)
notes = [
    "1. THIS PACKAGE IS BASED ON THE PRELIMINARY SITE PLAN",
    "   (FUEL_STATION_SITE_PLAN.dxf) REDRAWN FROM ITS WRITTEN",
    "   DIMENSIONS. ANY CHANGE TO THE SITE PLAN IS TO BE",
    "   REFLECTED IN ALL DISCIPLINES.",
    "2. ALL SAFETY DISTANCES ARE CHECKED ON F-001; ANY",
    "   SHORTFALL IS REPORTED, NOT HIDDEN.",
    "3. ALL ELECTRICAL EQUIPMENT INSIDE ZONE 1 / ZONE 2 SHALL",
    "   BE CERTIFIED FOR THE ZONE (Ex d / Ex e, IIA T3 MINIMUM,",
    "   IIB FOR LPG AREAS).",
    "4. ALL CALCULATED VALUES SHOWN ON THE DRAWINGS COME FROM",
    "   THE DESIGN REPORT (calcs.py).",
    "5. THE DRAWINGS ARE FOR AUTHORITY SUBMISSION AND REVIEW",
    "   AND REQUIRE THE SIGNATURE OF A REGISTERED ENGINEER",
    "   (IRAQI ENGINEERS UNION).",
    "6. CANOPY-DEPENDENT ITEMS ARE ON HOLD UNTIL THE",
    "   ARCHITECTURAL CANOPY DESIGN IS APPROVED (STAGE 6).",
]
block(g3, 22, y1, "GENERAL NOTES", notes, h=2.0, step=4.0)
hold = [
    "1. OPDC INSTRUCTIONS (LATEST EDITION) - SEPARATION DISTANCES,",
    "   TANK AND DISPENSER REQUIREMENTS.",
    "2. CIVIL DEFENCE DIRECTORATE - FIRE WATER STORAGE AND",
    "   HYDRANT REQUIREMENTS FOR THE STATION CATEGORY.",
    "3. ELECTRICITY DIRECTORATE - 11 kV CONNECTION POINT AND",
    "   TRANSFORMER RATING.",
    "4. MUNICIPAL WATER CONNECTION POINT AND PRESSURE.",
    "5. SOIL INVESTIGATION REPORT (BEARING CAPACITY, GYPSUM",
    "   CONTENT, WATER TABLE).",
    "6. TRUE NORTH AND SITE LEVELS (TOPOGRAPHIC SURVEY).",
    "7. ARCHITECTURAL CANOPY FORM, HEIGHT AND ELEVATIONS.",
]
block(g3, 182, y2, "INFORMATION REQUIRED FROM THE AUTHORITIES / CLIENT", hold, h=1.9, step=4.0)

ss.finish(OUT)
print("saved", OUT)
