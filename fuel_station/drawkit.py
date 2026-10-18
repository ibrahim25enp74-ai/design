"""Drawing helpers for discipline plans: plot-frame geometry drawn onto a Sheet.

Sizes given as `mm` are paper millimetres and scale with the sheet; coordinates are plot-frame
metres (site_base.o() converts them to the site plan frame, Sheet.s() places them on the sheet).
"""
import math

from ezdxf.enums import MTextEntityAlignment

import symbols
from site_base import TH


class Plan:
    def __init__(self, sheet):
        self.sh = sheet
        self.msp = sheet.msp
        self.f = sheet.f

    def m(self, p):
        return self.sh.f2m(p)

    def pline(self, pts, layer, close=False, width_mm=None, color=None, linetype=None, ltscale=None):
        att = {"layer": layer}
        if color is not None:
            att["color"] = color
        if linetype:
            att["linetype"] = linetype
        if ltscale:
            att["ltscale"] = ltscale
        e = self.msp.add_lwpolyline([self.m(p) for p in pts], close=close, dxfattribs=att)
        if width_mm:
            e.dxf.const_width = width_mm * self.f
        return e

    def line(self, a, b, layer, **kw):
        return self.pline([a, b], layer, **kw)

    def circle(self, c, r_m, layer, color=None):
        att = {"layer": layer}
        if color is not None:
            att["color"] = color
        return self.msp.add_circle(self.m(c), r_m, dxfattribs=att)

    def hatch(self, pts, layer, color=None, pattern="SOLID", scale=1.0, transparency=None):
        h = self.msp.add_hatch(color=color if color is not None else 256, dxfattribs={"layer": layer})
        if pattern != "SOLID":
            h.set_pattern_fill(pattern, scale=scale, color=color if color is not None else 256)
        h.paths.add_polyline_path([self.m(p) for p in pts], is_closed=True)
        if transparency is not None:
            h.transparency = transparency
        return h

    def text(self, s, p, mm=2.0, layer="G-TEXT", angle=None, attach="MC", color=None, width_mm=None):
        """Text at a plot point; angle None = along the plot's x axis (rear boundary), kept readable."""
        if angle is None:
            angle = 0.0 if getattr(self.sh, "plan_up", False) else math.degrees(TH)
        a = angle
        a = (a + 90) % 180 - 90
        att = {"layer": layer, "style": "TB", "char_height": mm * self.f}
        if color is not None:
            att["color"] = color
        e = self.msp.add_mtext(s, dxfattribs=att)
        ap = {"MC": MTextEntityAlignment.MIDDLE_CENTER, "ML": MTextEntityAlignment.MIDDLE_LEFT,
              "MR": MTextEntityAlignment.MIDDLE_RIGHT, "TL": MTextEntityAlignment.TOP_LEFT,
              "BL": MTextEntityAlignment.BOTTOM_LEFT, "BC": MTextEntityAlignment.BOTTOM_CENTER}[attach]
        e.set_location(self.m(p), rotation=a, attachment_point=ap)
        if width_mm:
            e.dxf.width = width_mm * self.f
        return e

    def sym(self, code, p, layer=None, angle=0.0, scale=1.0):
        return symbols.insert(self.sh, code, self.m(p), layer, angle, scale)

    def tag(self, s, p, mm=1.8, layer="G-TEXT", color=None):
        """Short label in a box, upright on the sheet."""
        x, y = self.m(p)
        w = (len(s) * 0.62 * mm + 1.2) * self.f
        h = (mm + 1.0) * self.f
        att = {"layer": layer}
        if color is not None:
            att["color"] = color
        self.msp.add_lwpolyline([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)],
                                close=True, dxfattribs=att)
        t = self.msp.add_mtext(s, dxfattribs={**att, "style": "TB", "char_height": mm * self.f})
        t.set_location((x, y), attachment_point=MTextEntityAlignment.MIDDLE_CENTER)

    def leader(self, p, q, s, mm=1.8, layer="G-TEXT", color=None):
        """Line from point p to label point q (plot frame); label upright, left of q if q is left."""
        self.line(p, q, layer, color=color)
        x0 = self.m(p)[0]
        x1 = self.m(q)[0]
        self.text(s, q, mm, layer, angle=0, attach="ML" if x1 >= x0 else "MR", color=color)

    def dist_line(self, p, q, label, layer, color=None, mm=1.9, tick_mm=1.4):
        """Measured distance: line with ticks at both ends and the value at mid-length."""
        self.line(p, q, layer, color=color)
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        t = tick_mm * self.f
        for c in (p, q):
            self.line((c[0] - nx * t, c[1] - ny * t), (c[0] + nx * t, c[1] + ny * t), layer, color=color)
        mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        a_sheet = math.degrees(math.atan2(*reversed([b - a for a, b in zip(self.m(p), self.m(q))])))
        self.text(label, (mid[0] + nx * 1.2 * self.f * 1.6, mid[1] + ny * 1.2 * self.f * 1.6), mm, layer,
                  angle=a_sheet, color=color)

    def ring(self, c, r_m, layer, color=None, linetype=None):
        att = {"layer": layer}
        if color is not None:
            att["color"] = color
        if linetype:
            att["linetype"] = linetype
        return self.msp.add_circle(self.m(c), r_m, dxfattribs=att)


def rect(b):
    x0, y0, x1, y1 = b
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
