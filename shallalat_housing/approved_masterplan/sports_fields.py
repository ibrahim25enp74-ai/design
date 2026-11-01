# Draws the sports fields (football 7-a-side, 2 tennis courts, 2 basketball/volleyball courts) in the
# green 'ملاعب كرة قدم وتنس' zone of the APPROVED master plan. Works on the copy made by villa_footprints.py.
import sys, math, ezdxf
F = sys.argv[1]
doc = ezdxf.readfile(F); ms = doc.modelspace()
for n, c in [('MP_SPORT_SURFACE', 3), ('MP_SPORT_LINES', 7), ('MP_SPORT_TEXT', 7), ('MP_SPORT_FENCE', 8)]:
    if n not in doc.layers: doc.layers.add(n, color=c)
def rect(x0, y0, x1, y1, layer='MP_SPORT_LINES', rgb=None, fill=None):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if fill:
        h = ms.add_hatch(dxfattribs={'layer': 'MP_SPORT_SURFACE'}); h.rgb = fill; h.paths.add_polyline_path(pts, is_closed=True)
    e = ms.add_lwpolyline(pts, close=True, dxfattribs={'layer': layer})
    if rgb: e.rgb = rgb
    return e
def line(a, b): ms.add_line(a, b, dxfattribs={'layer': 'MP_SPORT_LINES'}).rgb = (255, 255, 255)
def text(t, x, y, h=2.2):
    ms.add_text(t, height=h, dxfattribs={'layer': 'MP_SPORT_TEXT'}).set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
W = (255, 255, 255)
# ---- football 7-a-side 40 x 70 (N-S), enclosure 46 x 76
cx, cy, PW, PL = 338998.5, 4033060.0, 40.0, 70.0
rect(cx-23, cy-38, cx+23, cy+38, 'MP_SPORT_FENCE', fill=(46, 125, 50))
rect(cx-PW/2, cy-PL/2, cx+PW/2, cy+PL/2, rgb=W)
line((cx-PW/2, cy), (cx+PW/2, cy))
ms.add_circle((cx, cy), 6, dxfattribs={'layer': 'MP_SPORT_LINES'}).rgb = W
for s in (1, -1):
    yb = cy + s*PL/2
    rect(cx-12, min(yb, yb-s*10), cx+12, max(yb, yb-s*10), rgb=W)          # penalty area 24 x 10
    rect(cx-5, min(yb, yb-s*4), cx+5, max(yb, yb-s*4), rgb=W)             # goal area 10 x 4
    rect(cx-2.5, min(yb, yb+s*1.2), cx+2.5, max(yb, yb+s*1.2), rgb=W)     # goal 5 m
    ms.add_circle((cx, yb-s*7.5), 0.3, dxfattribs={'layer': 'MP_SPORT_LINES'}).rgb = W
text('FOOTBALL 7-A-SIDE 40x70', cx, cy+16, 2.4)
# ---- 2 tennis courts (each enclosure 18.3 x 36.6, N-S)
for i, x0 in enumerate([338984.9, 338984.9+18.3]):
    y0 = 4032974.0
    rect(x0, y0, x0+18.3, y0+36.6, 'MP_SPORT_FENCE', fill=(36, 92, 160))
    mx, my = x0+9.15, y0+18.3
    rect(mx-5.485, my-11.885, mx+5.485, my+11.885, rgb=W)                 # doubles
    rect(mx-4.115, my-11.885, mx+4.115, my+11.885, rgb=W)                 # singles
    line((mx-4.115, my-6.4), (mx+4.115, my-6.4)); line((mx-4.115, my+6.4), (mx+4.115, my+6.4))
    line((mx, my-6.4), (mx, my+6.4)); line((mx-6.4, my), (mx+6.4, my))      # centre service + net
    text('TENNIS %d' % (i+1), mx, my-15.5, 1.8)
# ---- 2 basketball / volleyball courts (enclosure 19 x 32, court 15 x 28)
for i, x0 in enumerate([338980.0, 339002.5]):
    y0 = 4032930.0
    rect(x0, y0, x0+19, y0+32, 'MP_SPORT_FENCE', fill=(200, 110, 60))
    mx, my = x0+9.5, y0+16
    rect(mx-7.5, my-14, mx+7.5, my+14, rgb=W); line((mx-7.5, my), (mx+7.5, my))
    ms.add_circle((mx, my), 1.8, dxfattribs={'layer': 'MP_SPORT_LINES'}).rgb = W
    for s in (1, -1):
        yb = my + s*14
        rect(mx-2.45, min(yb, yb-s*5.8), mx+2.45, max(yb, yb-s*5.8), rgb=W)
        a0, a1 = (180, 360) if s > 0 else (0, 180)
        ms.add_arc((mx, yb-s*1.575), 6.75, a0, a1, dxfattribs={'layer': 'MP_SPORT_LINES'}).rgb = W
    text('BASKETBALL %d' % (i+1), mx, my-8, 1.6)
doc.saveas(F)
print('ok')
