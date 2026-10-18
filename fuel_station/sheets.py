"""A3 sheet set in modelspace with the office title block (same layout as the SOUQ set).

Model units are metres.  Every sheet is an A3 frame drawn at its own scale, side by side
in modelspace; paper positions are given in millimetres and converted with Sheet.p().
plot_sheet_set.py (repo root) crops each A3_SHEET frame to one PDF page.
"""
import math
import re

import ezdxf
from ezdxf.addons import Importer
from ezdxf.enums import MTextEntityAlignment, TextEntityAlignment

from site_base import LL, LR, W, o

ARABIC = re.compile("[؀-ۿ]")

PROJECT = {
    "project": "FUEL FILLING STATION",
    "project2": "PLOT 1/3453, DISTRICT 43 YARIMJA AL-SHARQIYA",
    "location": "MOSUL, NINEVEH, IRAQ",
    "client": "HADI HUSSEIN JUMAA - AHMED OTHMAN EID",
    "number": "FS-3453-43",
    "designer": "IBRAHIM MAHFOUDH",
    "date": "18/10/2026",
    "date_short": "18/10/26",
    "phase": "DESIGN DEVELOPMENT",
    "status": "FOR REVIEW",
    "revisions": [("00", "18/10/2026", "FIRST ISSUE - STAGE 0", "I.M.")],
}

NOTES = [
    "1. ALL DIMENSIONS ARE IN METRES UNLESS",
    "    OTHERWISE NOTED. LEVELS IN METRES.",
    "2. DO NOT SCALE FROM THIS DRAWING. USE",
    "    FIGURED DIMENSIONS ONLY.",
    "3. VERIFY ALL DIMENSIONS ON SITE BEFORE",
    "    STARTING ANY WORK.",
    "4. READ WITH THE SITE PLAN AND ALL OTHER",
    "    DISCIPLINE DRAWINGS AND THE REPORT.",
    "5. COPYRIGHT OF THIS DRAWING IS RESERVED BY",
    "    THE OFFICE.",
]

TB_LAYERS = {
    "A3_SHEET": 7, "A3_FRAME": 7, "TB_LINES_THIN": 7, "TB_LINES_THICK": 7,
    "TB_LABELS": 7, "TB_FIELDS": 7, "TB_HEADINGS": 7, "TB_SYMBOLS": 7, "TB_KEYPLAN": 8,
    "X-ARCH": 8, "G-TEXT": 7, "G-TABLE": 7,
}
LINEWEIGHTS = {"TB_LINES_THICK": 50, "A3_FRAME": 50, "TB_LINES_THIN": 18, "X-ARCH": 13}


def new_doc():
    doc = ezdxf.new("R2018", setup=True)
    doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LTSCALE"] = 0.6
    doc.styles.add("TB", font="arial.ttf")
    if "AR" not in doc.styles:
        doc.styles.add("AR", font="arial.ttf")
    for name, color in TB_LAYERS.items():
        doc.layers.add(name, color=color, lineweight=LINEWEIGHTS.get(name, 18))
    return doc


def import_site_block(doc, site_dxf, name="X-ARCH-SITE"):
    """The site plan as a grey background block (no dimensions, no title block)."""
    src = ezdxf.readfile(site_dxf)
    blk = doc.blocks.new(name)
    imp = Importer(src, doc)
    ents = [e for e in src.modelspace() if e.dxftype() != "DIMENSION" and e.dxf.layer != "TITLE"]
    imp.import_entities(ents, blk)
    imp.finalize()
    for e in blk:
        layer = e.dxf.layer
        e.dxf.layer = "X-ARCH"
        e.dxf.color = 254 if e.dxftype() == "HATCH" and layer == "PAVING-HATCH" else 8
        if e.dxftype() == "HATCH" and layer != "PAVING-HATCH":
            e.dxf.color = 253
        if e.dxftype() == "LWPOLYLINE" and e.dxf.hasattr("const_width"):
            e.dxf.const_width = min(e.dxf.const_width, 0.06)
    return name


class Sheet:
    def __init__(self, sset, number, title, subtitle, den, x0):
        self.sset, self.number, self.title, self.subtitle = sset, number, title, subtitle
        self.den = den
        self.f = den / 1000.0           # metres of model per millimetre of paper
        self.x0, self.y0 = x0, 0.0
        self.msp = sset.msp
        self.window = None              # sheet-frame window shown in the drawing area

    # ---------------------------------------------------------------- paper helpers
    def p(self, x, y):
        return (self.x0 + x * self.f, self.y0 + y * self.f)

    def line(self, a, b, layer="TB_LINES_THIN"):
        self.msp.add_line(self.p(*a), self.p(*b), dxfattribs={"layer": layer})

    def rect(self, x0, y0, x1, y1, layer="TB_LINES_THIN"):
        self.msp.add_lwpolyline([self.p(x0, y0), self.p(x1, y0), self.p(x1, y1), self.p(x0, y1)],
                                close=True, dxfattribs={"layer": layer})

    def text(self, s, x, y, h, layer="TB_FIELDS", align="LEFT", angle=0.0, width=None):
        """Text at paper position; Arabic goes into MTEXT (shaped by CAD programs)."""
        if ARABIC.search(s) or "\\P" in s or width:
            att = {"LEFT": MTextEntityAlignment.BOTTOM_LEFT, "RIGHT": MTextEntityAlignment.BOTTOM_RIGHT,
                   "CENTER": MTextEntityAlignment.BOTTOM_CENTER, "MIDDLE": MTextEntityAlignment.MIDDLE_CENTER,
                   "TOPLEFT": MTextEntityAlignment.TOP_LEFT, "TOPRIGHT": MTextEntityAlignment.TOP_RIGHT}[align]
            e = self.msp.add_mtext(s, dxfattribs={"layer": layer, "style": "TB", "char_height": h * self.f})
            e.set_location(self.p(x, y), rotation=angle, attachment_point=att)
            if width:
                e.dxf.width = width * self.f
            return e
        e = self.msp.add_text(s, height=h * self.f, rotation=angle, dxfattribs={"layer": layer, "style": "TB"})
        if align == "LEFT":
            e.dxf.insert = self.p(x, y)
        else:
            e.set_placement(self.p(x, y), align={"RIGHT": TextEntityAlignment.BOTTOM_RIGHT,
                                                  "CENTER": TextEntityAlignment.BOTTOM_CENTER,
                                                  "MIDDLE": TextEntityAlignment.MIDDLE_CENTER}[align])
        return e

    def table(self, x, y_top, widths, rows, row_h=4.5, h=1.8, header_h=None, layer="G-TABLE",
              text_layer="G-TEXT", aligns=None):
        """Grid table; rows[0] is the header (drawn bold-ruled). Returns the bottom y."""
        header_h = header_h or row_h
        total = sum(widths)
        y = y_top
        self.line((x, y), (x + total, y), "TB_LINES_THICK")
        for i, row in enumerate(rows):
            rh = header_h if i == 0 else row_h
            cx = x
            for j, (w, cell) in enumerate(zip(widths, row)):
                al = (aligns[j] if aligns else "LEFT") if i else "LEFT"
                tx = cx + 1.0 if al == "LEFT" else cx + w - 1.0 if al == "RIGHT" else cx + w / 2
                if ARABIC.search(str(cell)):
                    tx, al = cx + w - 1.0, "RIGHT"
                self.text(str(cell), tx, y - rh / 2 - h * 0.45, h if i else h * 1.05,
                          "TB_LABELS" if i == 0 else text_layer, align=al)
                cx += w
            y -= rh
            self.line((x, y), (x + total, y), "TB_LINES_THICK" if i == 0 else layer)
        cx = x
        for w in [0] + list(widths):
            cx += w
            self.line((cx, y_top), (cx, y), layer)
        return y

    # ---------------------------------------------------------------- model content
    def place_site(self, window, area=(20, 10, 335, 287), block="X-ARCH-SITE"):
        """Insert the site background so the sheet-frame window is centred in the drawing area."""
        self.window = window
        wx0, wy0, wx1, wy1 = window
        ax0, ay0, ax1, ay1 = area
        cx, cy = self.p((ax0 + ax1) / 2, (ay0 + ay1) / 2)
        self.dx = cx - (wx0 + wx1) / 2
        self.dy = cy - (wy0 + wy1) / 2
        if block:
            self.msp.add_blockref(block, (self.dx, self.dy), dxfattribs={"layer": "X-ARCH"})
        return self

    def s(self, sheet_pt):
        """Sheet-frame point (site plan coordinates) -> model point on this sheet."""
        return (sheet_pt[0] + self.dx, sheet_pt[1] + self.dy)

    def f2m(self, plot_pt):
        """Plot-frame point -> model point on this sheet."""
        return self.s(o(plot_pt))

    # ---------------------------------------------------------------- title block
    def draw_frame(self, total):
        P = PROJECT
        L, T = self.line, self.text
        self.rect(0, 0, 420, 297, "A3_SHEET")
        self.rect(20, 10, 410, 287, "A3_FRAME")
        for a, b in (((210, 0), (210, 3)), ((210, 297), (210, 294)), ((0, 148.5), (3, 148.5)), ((420, 148.5), (417, 148.5))):
            L(a, b, "A3_FRAME")
        # grid references
        for i in range(9):
            x = 20 + i * 48.75
            L((x, 287), (x, 291))
            L((x, 10), (x, 6))
            if i < 8:
                T(str(i + 1), x + 22.6, 290.8, 2.5, "TB_LABELS")
                T(str(i + 1), x + 22.6, 3.8, 2.5, "TB_LABELS")
        for j in range(7):
            y = 10 + j * 46.17
            L((410, y), (414, y))
            L((20, y), (16, y))
            if j < 6:
                T("FEDCBA"[j], 17.3, y + 21.8, 2.5, "TB_LABELS")
                T("FEDCBA"[j], 415.3, y + 21.8, 2.5, "TB_LABELS")
        # title panel
        self.rect(340, 10, 410, 287, "A3_FRAME")
        disc = {"G": ("GENERAL", "عام"), "F": ("CIVIL DEFENCE", "الدفاع المدني"), "E": ("ELECTRICAL", "الكهرباء"),
                "P": ("SANITARY", "الصحية"), "S": ("STRUCTURAL", "الانشائية")}.get(self.number[0], ("", ""))
        T(disc[0], 375, 270, 4.2, "TB_HEADINGS", align="CENTER")
        T(disc[1], 375, 259, 4.0, "TB_HEADINGS", align="CENTER")
        L((340, 251), (410, 251), "TB_LINES_THICK")
        L((340, 246), (410, 246))
        T("GENERAL NOTES", 363.1, 247.5, 2.0, "TB_HEADINGS")
        for k, n in enumerate(NOTES):
            T(n, 341.5, 243.3 - 3 * k, 1.55)
        L((340, 213), (410, 213), "TB_LINES_THICK")
        L((380, 213), (380, 181))
        T("KEY PLAN", 341.5, 209.9, 1.6, "TB_LABELS")
        self.key_plan(345, 185, 376, 207)
        T("NORTH", 381.5, 209.9, 1.6, "TB_LABELS")
        c = self.p(395, 195.5)
        self.msp.add_circle(c, 9 * self.f, dxfattribs={"layer": "TB_SYMBOLS"})
        self.msp.add_lwpolyline([self.p(395, 206.5), self.p(391, 189.5), self.p(395, 192.5), self.p(399, 189.5)],
                                close=True, dxfattribs={"layer": "TB_SYMBOLS"})
        T("N", 393.5, 208.6, 3.0, "TB_SYMBOLS")
        T("TO BE CONFIRMED", 395, 182.5, 1.2, "TB_LABELS", align="CENTER")
        L((340, 181), (410, 181), "TB_LINES_THICK")
        T("REVISIONS", 367.4, 177.5, 2.0, "TB_HEADINGS")
        L((340, 176), (410, 176))
        for y in (171, 165.8, 160.6, 155.4, 150.2):
            L((340, y), (410, y))
        for x in (348, 364, 398):
            L((x, 176), (x, 145))
        for s, x in (("REV", 341.8), ("DATE", 353.2), ("DESCRIPTION", 373.8), ("BY", 402.6)):
            T(s, x, 172.8, 1.5, "TB_LABELS")
        for k, (rev, date, desc, by) in enumerate(P["revisions"]):
            y = 167.6 - 5.2 * k
            T(rev, 342.8, y, 1.6)
            T(date, 348.9, y, 1.6)
            T(desc, 364.6, y, 1.25)
            T(by, 399.3, y, 1.4)
        L((340, 145), (410, 145), "TB_LINES_THICK")
        for y in (136, 127, 118):
            L((340, y), (410, y))
        for lab, val, y in (("PROJECT", P["project"], 141.9), ("LOCATION", P["location"], 132.9),
                            ("CLIENT / OWNER", P["client"], 123.9), ("PROJECT No.", P["number"], 114.9)):
            T(lab, 341.5, y, 1.6, "TB_LABELS")
            T(val, 343.0, y - 3.4, 2.5 if len(val) < 26 else 1.7)
        T(P["project2"], 343.0, 136.6, 1.25)
        L((340, 109), (410, 109), "TB_LINES_THICK")
        T("DRAWING TITLE", 341.5, 105.9, 1.6, "TB_LABELS")
        th = 3.5 if len(self.title) <= 18 else 2.6 if len(self.title) <= 26 else 2.0
        T(self.title, 341.5, 96.8, th, "TB_HEADINGS")
        T(self.subtitle, 408.5, 90.6, 1.7 if len(self.subtitle) < 38 else 1.3, align="RIGHT")
        L((340, 87), (410, 87), "TB_LINES_THICK")
        L((340, 82), (410, 82))
        for x in (360, 384, 398):
            L((x, 87), (x, 57))
        for s, x in (("ROLE", 347.1), ("NAME", 369.0), ("SIGN.", 388.1), ("DATE", 401.2)):
            T(s, x, 83.8, 1.5, "TB_LABELS")
        for y in (75.8, 69.5, 63.2):
            L((340, y), (410, y))
        for k, role in enumerate(("DESIGNED", "DRAWN", "CHECKED", "APPROVED")):
            y = 78.1 - 6.25 * k
            T(role, 341.5, y, 1.6, "TB_LABELS")
            T(P["designer"] if k < 2 else "-", 361.5, y - 0.1, 1.4 if k < 2 else 1.8)
            T(P["date_short"], 399.8, y + 0.2, 1.2)
        L((340, 57), (410, 57), "TB_LINES_THICK")
        L((375, 57), (375, 39))
        L((340, 48), (410, 48))
        T("SCALE", 341.5, 53.9, 1.6, "TB_LABELS")
        T(self.scale_text, 343.0, 50.1, 2.0)
        T("DATE", 376.5, 53.9, 1.6, "TB_LABELS")
        T(P["date"], 378.0, 50.1, 2.0)
        T("PHASE", 341.5, 44.9, 1.6, "TB_LABELS")
        T(P["phase"], 343.0, 41.1, 1.81)
        T("STATUS", 376.5, 44.9, 1.6, "TB_LABELS")
        T(P["status"], 378.0, 41.1, 2.0)
        L((340, 39), (410, 39), "TB_LINES_THICK")
        L((386, 39), (386, 10))
        L((390, 20.5), (406, 20.5))
        T("DRAWING No.", 341.5, 35.9, 1.6, "TB_LABELS")
        T(self.number, 363.0, 19.0, 7.0 if len(self.number) <= 5 else 5.5, "TB_HEADINGS", align="CENTER")
        T("SHEET", 387.5, 35.9, 1.6, "TB_LABELS")
        T(f"{self.index:02d}", 394.1, 23.0, 5.0, "TB_HEADINGS")
        T(f"OF  {total}", 393.3, 15.9, 2.2)
        if self.den and self.show_scale_bar:
            self.scale_bar()

    @property
    def scale_text(self):
        return self._scale_text or f"1:{self.den}"

    def scale_bar(self, x=28, y=18):
        seg = 10.0
        for k in range(5):
            pts = [self.p(x + k * seg, y), self.p(x + (k + 1) * seg, y), self.p(x + (k + 1) * seg, y + 2), self.p(x + k * seg, y + 2)]
            pl = self.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "TB_SYMBOLS"})
            if k % 2 == 0:
                h = self.msp.add_hatch(color=256, dxfattribs={"layer": "TB_SYMBOLS"})
                h.paths.add_polyline_path(pts, is_closed=True)
            self.text(f"{k * seg * self.f:g}" + ("" if k else ""), x + k * seg - 0.8, y + 3.4, 1.8, "TB_LABELS")
        self.text(f"{5 * seg * self.f:g}m", x + 5 * seg - 1.0, y + 3.4, 1.8, "TB_LABELS")
        self.text(f"SCALE 1:{self.den} (A3)", x, y - 3.5, 1.8, "TB_LABELS")

    def key_plan(self, x0, y0, x1, y1):
        """Plot outline fitted in the key plan box; the shown window is hatched."""
        corners = [o(p) for p in ((0, 0), (W, 0), (W, LR), (0, LL))]
        xs, ys = zip(*corners)
        k = min((x1 - x0 - 2) / (max(xs) - min(xs)), (y1 - y0 - 2) / (max(ys) - min(ys)))
        ox = x0 + (x1 - x0 - k * (max(xs) - min(xs))) / 2 - k * min(xs)
        oy = y0 + (y1 - y0 - k * (max(ys) - min(ys))) / 2 - k * min(ys)
        pts = [self.p(ox + k * cx, oy + k * cy) for cx, cy in corners]
        self.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "TB_LINES_THIN"})
        if self.window:
            wx0, wy0, wx1, wy1 = self.window
            w = [self.p(ox + k * a, oy + k * b) for a, b in ((wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1))]
            h = self.msp.add_hatch(color=8, dxfattribs={"layer": "TB_KEYPLAN"})
            h.set_pattern_fill("ANSI31", scale=0.02 * self.f / 0.3, color=8)
            h.paths.add_polyline_path(w, is_closed=True)
        self.text("THIS SHEET", 361.2, 181.8, 1.3, "TB_LABELS", align="CENTER")


class SheetSet:
    def __init__(self, gap_mm=25):
        self.doc = new_doc()
        self.msp = self.doc.modelspace()
        self.sheets = []
        self.next_x = 0.0
        self.gap_mm = gap_mm

    def add(self, number, title, subtitle, den, scale_text=None, scale_bar=True):
        sh = Sheet(self, number, title, subtitle, den, self.next_x)
        sh._scale_text = scale_text
        sh.show_scale_bar = scale_bar
        sh.index = len(self.sheets) + 1
        self.next_x += (420 + self.gap_mm) * sh.f
        self.sheets.append(sh)
        return sh

    def finish(self, path):
        for sh in self.sheets:
            sh.draw_frame(len(self.sheets))
        self.doc.set_modelspace_vport(height=300 * self.sheets[0].f, center=self.sheets[0].p(210, 148.5))
        self.doc.saveas(path)
        return path


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])
