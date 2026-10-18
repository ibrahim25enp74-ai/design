"""Drawing symbols shared by all discipline sets, defined as blocks in paper millimetres.

Insert a symbol with Sheet scale (xscale = sheet.f) so it plots at the same size on every
sheet.  SYMBOLS also feeds the legend sheet (G-002).
"""
import math

from ezdxf.enums import TextEntityAlignment

# discipline layers: name -> (ACI colour, lineweight)
DISCIPLINE_LAYERS = {
    "F-SYMB": (1, 25), "F-PIPE": (1, 35), "F-ZONE": (1, 18), "F-TEXT": (1, 18),
    "E-SYMB": (5, 25), "E-POWR": (5, 35), "E-LITE": (4, 25), "E-GRND": (3, 25), "E-HAZD": (30, 18), "E-TEXT": (5, 18),
    "P-SYMB": (140, 25), "P-WATR": (150, 35), "P-SANR": (34, 35), "P-STRM": (94, 35), "P-TEXT": (140, 18),
    "S-SYMB": (2, 25), "S-CONC": (2, 35), "S-GRID": (8, 13), "S-TEXT": (2, 18),
}


def _txt(blk, s, x, y, h, align=TextEntityAlignment.MIDDLE_CENTER):
    t = blk.add_text(s, height=h, dxfattribs={"style": "TB"})
    t.set_placement((x, y), align=align)


def _circle(blk, r, x=0, y=0):
    blk.add_circle((x, y), r)


def _rect(blk, w, h, x=0, y=0):
    blk.add_lwpolyline([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], close=True)


def _fill(blk, pts):
    h = blk.add_hatch(color=0)
    h.paths.add_polyline_path(pts, is_closed=True)


def _circle_text(s, r=2.2, h=1.6):
    def f(b):
        _circle(b, r)
        _txt(b, s, 0, 0, h)
    return f


def _box_text(s, w=6.0, hh=3.0, h=1.5):
    def f(b):
        _rect(b, w, hh)
        _txt(b, s, 0, 0, h)
    return f


def _extinguisher(letter):
    def f(b):
        b.add_lwpolyline([(-1.5, -2.2), (1.5, -2.2), (1.5, 1.6), (0, 2.6), (-1.5, 1.6)], close=True)
        _txt(b, letter, 0, -0.3, 1.8)
    return f


def _hydrant(b):
    _circle(b, 2.2)
    b.add_line((-2.2, 0), (2.2, 0))
    b.add_line((0, -2.2), (0, 2.2))
    _fill(b, [(0, 0), (2.2, 0)] + [(2.2 * math.cos(math.radians(a)), 2.2 * math.sin(math.radians(a))) for a in range(0, 91, 15)])


def _hose_reel(b):
    _circle(b, 2.2)
    _circle(b, 1.0)
    _txt(b, "HR", 0, -3.3, 1.2)


def _esd(b):
    _circle(b, 2.4)
    _fill(b, [(1.6 * math.cos(math.radians(a)), 1.6 * math.sin(math.radians(a))) for a in range(0, 360, 20)])
    _txt(b, "ESD", 0, -3.4, 1.2)


def _assembly(b):
    _rect(b, 5, 5)
    for a in (0, 90, 180, 270):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        b.add_line((0.4 * c, 0.4 * s), (2.0 * c, 2.0 * s))
    _txt(b, "AP", 0, -3.6, 1.2)


def _spray(b):
    b.add_lwpolyline([(0, 0), (-1.2, 2.0), (1.2, 2.0)], close=True)
    b.add_line((0, 0), (0, -1.5))


def _light_panel(b):
    _rect(b, 4, 4)
    b.add_line((-2, -2), (2, 2))
    b.add_line((-2, 2), (2, -2))


def _ex_light(b):
    _circle(b, 2.2)
    b.add_line((-1.55, -1.55), (1.55, 1.55))
    b.add_line((-1.55, 1.55), (1.55, -1.55))
    _txt(b, "Ex", 0, -3.4, 1.2)


def _pole(b):
    _circle(b, 1.2)
    _fill(b, [(0.7 * math.cos(math.radians(a)), 0.7 * math.sin(math.radians(a))) for a in range(0, 360, 30)])
    b.add_line((1.2, 0), (3.5, 0))
    b.add_lwpolyline([(3.5, -0.9), (5.3, -0.9), (5.3, 0.9), (3.5, 0.9)], close=True)


def _emergency(b):
    _circle(b, 2.2)
    _fill(b, [(-1.2, -1.0), (1.2, -1.0), (0, 1.3)])


def _socket(b):
    b.add_arc((0, 0), 2.0, 0, 180)
    b.add_line((-2.0, 0), (2.0, 0))
    b.add_line((-0.7, 2.0), (-0.7, 3.0))
    b.add_line((0.7, 2.0), (0.7, 3.0))


def _switch(b):
    _circle(b, 1.0)
    _fill(b, [(1.0 * math.cos(math.radians(a)), 1.0 * math.sin(math.radians(a))) for a in range(0, 360, 30)])
    b.add_line((0.7, 0.7), (2.6, 2.6))
    b.add_line((2.6, 2.6), (3.3, 1.9))


def _db(b):
    _rect(b, 6, 3)
    _fill(b, [(-3, -1.5), (3, -1.5), (3, 0), (-3, 0)])


def _jbox(b):
    _rect(b, 2.4, 2.4)
    b.add_line((-1.2, -1.2), (1.2, 1.2))


def _earth_pit(b):
    _circle(b, 2.4)
    b.add_line((0, 1.6), (0, 0))
    for k, w in enumerate((1.6, 1.1, 0.6)):
        b.add_line((-w, -0.5 * k), (w, -0.5 * k))


def _air_terminal(b):
    _circle(b, 2.0)
    _fill(b, [(0.6 * math.cos(math.radians(a)), 0.6 * math.sin(math.radians(a))) for a in range(0, 360, 30)])
    _txt(b, "AT", 0, -3.2, 1.2)


def _transformer(b):
    _circle(b, 1.8, -1.0, 0)
    _circle(b, 1.8, 1.0, 0)


def _manhole(b):
    _rect(b, 4, 4)
    _circle(b, 1.4)


def _gully(b):
    _circle(b, 1.8)
    _fill(b, [(0.8 * math.cos(math.radians(a)), 0.8 * math.sin(math.radians(a))) for a in range(0, 360, 30)])


def _floor_drain(b):
    _circle(b, 1.8)
    b.add_line((-1.27, -1.27), (1.27, 1.27))
    b.add_line((-1.27, 1.27), (1.27, -1.27))


def _cleanout(b):
    _circle(b, 1.4)
    _txt(b, "CO", 0, -2.8, 1.1)


def _gate_valve(b):
    _fill(b, [(-2, -1.2), (-2, 1.2), (0, 0)])
    _fill(b, [(2, -1.2), (2, 1.2), (0, 0)])


def _check_valve(b):
    b.add_lwpolyline([(-2, -1.2), (-2, 1.2), (2, -1.2), (2, 1.2)], close=True)
    b.add_line((2, -1.6), (2, 1.6))


def _pump(b):
    _circle(b, 2.2)
    b.add_lwpolyline([(-1.4, -1.2), (-1.4, 1.2), (1.8, 0)], close=True)


def _grid_bubble(b):
    _circle(b, 3.0)


def _column(b):
    _fill(b, [(-1.2, -1.2), (1.2, -1.2), (1.2, 1.2), (-1.2, 1.2)])


def _footing(b):
    _rect(b, 6, 6)
    _rect(b, 2.4, 2.4)


def _section(b):
    _circle(b, 2.6)
    b.add_line((-2.6, 0), (2.6, 0))
    _fill(b, [(2.6, 0.0), (5.0, 0.0), (2.6, 2.4)])


# code: (block name, layer, English, Arabic, draw function)
SYMBOLS = {
    "CIVIL DEFENCE": [
        ("FE-P", "F-SYMB", "PORTABLE EXTINGUISHER, DRY POWDER 12 kg", "مطفأة بودرة جافة 12 كغم", _extinguisher("P")),
        ("FE-C", "F-SYMB", "PORTABLE EXTINGUISHER, CO2 6 kg", "مطفأة ثاني اوكسيد الكاربون 6 كغم", _extinguisher("C")),
        ("FE-F", "F-SYMB", "PORTABLE EXTINGUISHER, AFFF FOAM 9 L", "مطفأة رغوة 9 لتر", _extinguisher("F")),
        ("FE-W", "F-SYMB", "WHEELED EXTINGUISHER, DRY POWDER 50 kg", "مطفأة بودرة جافة بعجلات 50 كغم", _circle_text("50")),
        ("FH", "F-SYMB", "FIRE HYDRANT (2 x 65 mm OUTLETS)", "حنفية حريق", _hydrant),
        ("HR", "F-SYMB", "FIRE HOSE REEL 25 mm x 30 m", "بكرة خرطوم حريق", _hose_reel),
        ("FACP", "F-SYMB", "FIRE ALARM CONTROL PANEL", "لوحة سيطرة انذار الحريق", _box_text("FACP", 7)),
        ("SD", "F-SYMB", "SMOKE DETECTOR", "كاشف دخان", _circle_text("S")),
        ("HD", "F-SYMB", "HEAT DETECTOR", "كاشف حرارة", _circle_text("H")),
        ("MCP", "F-SYMB", "MANUAL CALL POINT", "نقطة انذار يدوية", _box_text("MCP", 4.4, 4.4, 1.2)),
        ("SNDR", "F-SYMB", "ALARM SOUNDER / FLASHER", "جرس وضوء انذار", _circle_text("B")),
        ("ESD", "F-SYMB", "EMERGENCY SHUT-DOWN PUSH BUTTON", "زر ايقاف الطوارئ", _esd),
        ("EXIT", "F-SYMB", "EMERGENCY EXIT SIGN (ILLUMINATED)", "علامة مخرج طوارئ", _box_text("EXIT", 6, 2.6, 1.4)),
        ("AP", "F-SYMB", "ASSEMBLY POINT", "نقطة تجمع", _assembly),
        ("FP", "F-SYMB", "FIRE PUMP SET", "مضخة حريق", _pump),
        ("WS", "F-SYMB", "WATER SPRAY NOZZLE (LPG TANK COOLING)", "مرش ماء لتبريد خزان الغاز", _spray),
    ],
    "ELECTRICAL": [
        ("TRF", "E-SYMB", "TRANSFORMER 11/0.4 kV", "محولة 11/0.4 ك.ف", _transformer),
        ("GEN", "E-SYMB", "STANDBY DIESEL GENERATOR", "مولدة احتياط", _circle_text("G")),
        ("ATS", "E-SYMB", "AUTOMATIC TRANSFER SWITCH", "مفتاح تحويل اوتوماتيكي", _box_text("ATS")),
        ("MDB", "E-SYMB", "MAIN / SUB DISTRIBUTION BOARD", "لوحة توزيع رئيسية / فرعية", _db),
        ("LP", "E-LITE", "LED PANEL 600x600, 36 W", "وحدة انارة LED", _light_panel),
        ("LEX", "E-LITE", "Ex-d LED LUMINAIRE (HAZARDOUS AREA)", "وحدة انارة مقاومة للانفجار", _ex_light),
        ("POLE", "E-LITE", "YARD LIGHTING POLE, LED FLOODLIGHT", "عمود انارة ساحة", _pole),
        ("EM", "E-LITE", "EMERGENCY LIGHT, 3 h BATTERY", "انارة طوارئ", _emergency),
        ("SO", "E-POWR", "SWITCHED SOCKET OUTLET 13 A", "مأخذ قدرة 13 امبير", _socket),
        ("SW", "E-LITE", "LIGHTING SWITCH", "مفتاح انارة", _switch),
        ("JB", "E-POWR", "JUNCTION BOX", "صندوق توصيل", _jbox),
        ("EP", "E-GRND", "EARTH PIT WITH TEST LINK", "بئر تأريض", _earth_pit),
        ("AT", "E-GRND", "LIGHTNING AIR TERMINAL", "مانعة صواعق", _air_terminal),
    ],
    "SANITARY": [
        ("MH", "P-SYMB", "MANHOLE / INSPECTION CHAMBER", "منهول / غرفة تفتيش", _manhole),
        ("GT", "P-SYMB", "GULLY TRAP", "مصيدة مياه", _gully),
        ("FD", "P-SYMB", "FLOOR DRAIN", "بالوعة ارضية", _floor_drain),
        ("CO", "P-SYMB", "CLEAN-OUT", "فتحة تنظيف", _cleanout),
        ("WM", "P-SYMB", "WATER METER", "مقياس ماء", _circle_text("M")),
        ("GV", "P-SYMB", "GATE VALVE", "صمام بوابي", _gate_valve),
        ("NRV", "P-SYMB", "NON-RETURN VALVE", "صمام عدم رجوع", _check_valve),
        ("PU", "P-SYMB", "BOOSTER PUMP", "مضخة رفع", _pump),
    ],
    "STRUCTURAL": [
        ("GRID", "S-GRID", "GRID LINE BUBBLE", "محور انشائي", _grid_bubble),
        ("COL", "S-SYMB", "RC COLUMN", "عمود خرساني", _column),
        ("FTG", "S-SYMB", "ISOLATED FOOTING", "اساس منفرد", _footing),
        ("SEC", "S-SYMB", "SECTION MARK", "علامة مقطع", _section),
    ],
}

LINE_TYPES = [
    ("F-PIPE", "CONTINUOUS", "FIRE WATER MAIN (HDPE PN16 BURIED)", "خط ماء الحريق"),
    ("E-POWR", "DASHED", "BURIED POWER CABLE IN TRENCH / DUCT", "كابل قدرة مدفون"),
    ("E-GRND", "DASHDOT", "BARE COPPER EARTH CONDUCTOR 70 mm2", "موصل تأريض نحاسي"),
    ("E-HAZD", "CONTINUOUS", "HAZARDOUS AREA BOUNDARY (ZONE 1 / 2)", "حدود المنطقة الخطرة"),
    ("P-WATR", "CONTINUOUS", "COLD WATER SUPPLY (PPR)", "خط ماء بارد"),
    ("P-SANR", "DASHED", "FOUL DRAIN (uPVC)", "خط صرف صحي"),
    ("P-STRM", "DASHDOT", "OILY / SURFACE WATER DRAIN", "خط تصريف مياه سطحية / زيتية"),
]


def define(doc):
    """Create the discipline layers and every symbol block in doc."""
    for name, (color, lw) in DISCIPLINE_LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color, lineweight=lw)
    for group in SYMBOLS.values():
        for code, layer, _en, _ar, draw in group:
            name = "SYM-" + code
            if name in doc.blocks:
                continue
            blk = doc.blocks.new(name)
            draw(blk)
            for e in blk:
                e.dxf.layer = "0"
                if e.dxftype() != "HATCH":
                    e.dxf.color = 0        # BYBLOCK: takes the insert's layer colour
    return doc


def insert(sheet, code, model_pt, layer=None, angle=0.0, scale=1.0):
    """Place a symbol at a model point, sized for the sheet scale."""
    lay = layer or next(l for g in SYMBOLS.values() for c, l, *_ in g if c == code)
    return sheet.msp.add_blockref("SYM-" + code, model_pt, dxfattribs={
        "layer": lay, "xscale": sheet.f * scale, "yscale": sheet.f * scale, "rotation": angle})
