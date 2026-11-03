# V4 (2026-11-03): new master plan from the site boundary only.
# Concept: central gate -> 20 m boulevard -> civic square (big garden + fountain inside a loop road, services around it);
# E-W spine 20 m; ring 15 m; local 12 m; T-junctions only (streets staggered); no green strips;
# villas 16x25 = 400 (50), houses 10x25 = 250 (max); towers at the east end with fountain garden + side parking.
import sys, json, ezdxf
from ezdxf import colors
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union

SRC, OUT = sys.argv[1], sys.argv[2]
sm = ezdxf.readfile(SRC).modelspace()
B = [tuple(p[:2]) for p in sm.query('LWPOLYLINE[layer=="MP_BOUNDARY"]')[0].get_points()]
SW, NW, NE, SE = B
site = Polygon(B)
RING, ST = 15.0, 12.0
inner = site.buffer(-RING, join_style=2)
def yN(x): return NW[1] + (NE[1]-NW[1])*(x-NW[0])/(NE[0]-NW[0]) - RING     # inner edge of the north ring road
import math
KS = math.hypot(SE[0]-SW[0], SE[1]-SW[1])/(SE[0]-SW[0])
def yS(x): return SW[1] + (SE[1]-SW[1])*(x-SW[0])/(SE[0]-SW[0]) + RING*KS    # inner edge of the south ring road
SP_BOT, SP_TOP = 4033013.0, 4033033.0; CY = 4033023.0
inN = lambda xa, xb: Polygon([(xa, yN(xa)), (xb, yN(xb)), (xb, SP_TOP), (xa, SP_TOP)])
inS = lambda xa, xb: Polygon([(xa, SP_BOT), (xb, SP_BOT), (xb, yS(xb)), (xa, yS(xa))])

doc = ezdxf.new('R2018', setup=True); ms = doc.modelspace(); doc.header['$INSUNITS'] = 6
for name, col in [('MP_BOUNDARY', 1), ('MP4_ROAD', 8), ('MP4_SERVICES', 7), ('MP4_VILLA', 2), ('MP4_HOUSE', 30),
                  ('MP4_GREEN', 3), ('MP4_TOWER', 5), ('MP4_PARKING', 9), ('MP4_PLAZA', 31), ('MP4_FOUNTAIN', 4),
                  ('MP4_PLOTLINE', 7), ('MP4_TEXT', 7), ('MP4_GATE', 1)]:
    doc.layers.add(name, color=col)
ms.add_lwpolyline(B, close=True, dxfattribs={'layer': 'MP_BOUNDARY'})
order = {}
def hatch(poly, layer, col, key=5):
    for p in getattr(poly, 'geoms', [poly]):
        if p.is_empty or p.geom_type != 'Polygon' or p.area < 1: continue
        h = ms.add_hatch(dxfattribs={'layer': layer}); h.rgb = colors.int2rgb(col)
        h.paths.add_polyline_path(list(p.exterior.coords)[:-1], is_closed=True)
        for r in p.interiors: h.paths.add_polyline_path(list(r.coords)[:-1], is_closed=True)
        order[h.dxf.handle] = key
def outline(poly, layer='MP4_PLOTLINE', col=7):
    for p in getattr(poly, 'geoms', [poly]):
        if p.geom_type == 'Polygon': ms.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={'layer': layer, 'color': col})
def text(s, x, y, h=4.0):
    ms.add_text(s, dxfattribs={'layer': 'MP4_TEXT', 'height': h}).set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
hatch(site, 'MP4_ROAD', 0x939598, 1)

# ---------------- plots
plots = {'villa': [], 'house': []}
def quad(xa, xb, side, t0, t1):
    if side == 'N': return Polygon([(xa, yN(xa)-t0), (xb, yN(xb)-t0), (xb, yN(xb)-t1), (xa, yN(xa)-t1)])
    return Polygon([(xa, yS(xa)+t0), (xb, yS(xb)+t0), (xb, yS(xb)+t1), (xa, yS(xa)+t1)])
def split(L, f, n=None):
    """n plots of frontage f; the leftover (whole metres) goes to the two corner plots"""
    k = n or int(L // f); e = L - k*f; w = [f]*k
    if k == 1: w[0] += e
    elif k > 1: w[0] += e/2; w[-1] += e/2
    return w
def hrow(xa, xb, side, t0, d, f, kind, n=None):
    x = xa
    for w in split(xb-xa, f, n):
        plots[kind].append(quad(x, x+w, side, t0, t0+d)); x += w
def vblock(xa, xb, t0, f, kind):
    """block perpendicular to the south edge: 2 columns back to back, plots stacked from the spine down to t0"""
    xm = (xa+xb)/2
    for c0, c1 in ((xa, xm), (xm, xb)):
        L = SP_BOT - max(yS(c0), yS(c1)) - t0
        k = int(L // f); y = SP_BOT
        for i in range(k):
            if i == k-1: q = Polygon([(c0, y), (c1, y), (c1, yS(c1)+t0), (c0, yS(c0)+t0)])   # corner plot takes the rest
            else: q = box(c0, y-f, c1, y)
            plots[kind].append(q); y -= f

VF, VD, HF, HD = 16.0, 25.0, 10.0, 25.0
# north band: villa block on the ring | 12 m street | house row facing the street, backing on the spine verge
#   west 339040-339278 (cross street 339152-339164), east 339496-339688 (cross street 339592-339604)
for xa, xb in ((339040, 339152), (339164, 339278), (339496, 339592), (339604, 339688)):
    hrow(xa, xb, 'N', 0, VD, VF, 'villa'); hrow(xa, xb, 'N', VD, VD, VF, 'villa')
for xa, xb in ((339040, 339120), (339132, 339278), (339496, 339688)):          # inner cross street 339120-339132 (T to spine)
    hrow(xa, xb, 'N', 2*VD+ST, HD, HF, 'house')
# south-west: house block on the ring (cross street 339121-339133) | street | perpendicular blocks up to the spine
for xa, xb in ((339040, 339121), (339133, 339214)):
    hrow(xa, xb, 'S', 0, HD, HF, 'house'); hrow(xa, xb, 'S', HD, HD, HF, 'house')
for xa, xb in ((339040, 339090), (339102, 339152), (339164, 339214)):
    vblock(xa, xb, 2*HD+ST, HF, 'house')
# south-east: perpendicular blocks from the ring to the spine
for xa, xb in ((339514, 339564), (339576, 339626), (339638, 339688)):
    vblock(xa, xb, 0, HF, 'house')

# ---------------- civic square (centre)
GX = 339387.0                                   # gate 1 / boulevard axis
loop = box(GX-50, CY-50, GX+50, CY+50); garden = box(GX-38, CY-38, GX+38, CY+38)
svc = []                                        # (key, poly, colour)
def S_(k, poly, col): svc.append((k, poly.intersection(inner), col))
S_('mall', box(339290, CY+50, GX-10, 4033200), 0xCD2027)
S_('health', box(GX+10, CY+50, GX+39, 4033200), 0xA953A0)
S_('police', box(GX+39, CY+50, GX+68, 4033200), 0xF27172)
S_('cd', box(GX+68, CY+50, 339484, 4033200), 0xF7ABAE)
S_('cpark', box(339290, SP_TOP, GX-50, CY+50), 0xB9BCC2)
S_('admin', box(GX+50, SP_TOP, 339484, CY+50), 0xFECC66)
S_('mosque', box(339287, CY-50, GX-50, SP_BOT), 0xADDDF7)
S_('cpark', box(339226, CY-50, 339287, SP_BOT), 0xB9BCC2)
S_('cpark', box(GX+50, CY-50, 339502, SP_BOT), 0xB9BCC2)
S_('kg', box(339226, 4032940, 339287, CY-50), 0x105689)
S_('cpark', box(339226, 4032800, 339287, 4032940), 0xB9BCC2)
S_('secondary', box(339287, 4032800, GX-6, CY-50), 0x22346E)
S_('primary', box(GX+6, 4032800, 339502, CY-50), 0x2776BB)
# ---------------- west zone: sports + utilities
west = inner.intersection(box(338800, 4032800, 339025, 4033200))
S_('sports', west.intersection(box(338800, 4032955, 339025, 4033200)), 0x78BA6E)
S_('waterst', west.intersection(box(338800, 4032911, 339025, 4032943)), 0x00A6A6)
S_('power', west.intersection(box(338800, 4032878, 339025, 4032911)), 0xF2C200)
S_('waste', west.intersection(box(338800, 4032800, 339025, 4032878)), 0x8B6B4A)
for k, g, c in svc: hatch(g, 'MP4_SERVICES', c, 3); outline(g, 'MP4_SERVICES', 7)
hatch(garden, 'MP4_GREEN', 0x136734, 4)
cf = Point(GX, CY)
hatch(cf.buffer(16, 64), 'MP4_PLAZA', 0xE9DCC0, 5); hatch(cf.buffer(11, 64), 'MP4_FOUNTAIN', 0x4FB3E8, 6)

# ---------------- tower zone (east end): towers N + S, central fountain garden, parking on both sides
TX = 339700.0
tz = inner.intersection(box(TX, 4032000, 340500, 4034000))
tN = box(339752, 4033088, 339752+34.8, 4033088+32.4); tS = box(339752, 4032998, 339752+34.8, 4032998+32.4)
pW = [box(TX, 4033052, TX+16, 4033200).intersection(tz)]
pE = [tz.intersection(box(339794, 4032900, 340000, 4033200))]
plaza = Point(TX, CY).buffer(26, 64).intersection(box(TX, CY-27, TX+27, CY+27))
tf = Point(339769, 4033059)
tgarden = tz.difference(unary_union([tN, tS, plaza] + pW + pE))
hatch(tgarden, 'MP4_GREEN', 0x2E8B57, 4); hatch(plaza, 'MP4_PLAZA', 0xE9DCC0, 5)
hatch(tf.buffer(17, 64), 'MP4_PLAZA', 0xE9DCC0, 5); hatch(tf.buffer(12, 64), 'MP4_FOUNTAIN', 0x4FB3E8, 6)
for t in (tN, tS): hatch(t, 'MP4_TOWER', 0x2B2F3A, 7); outline(t, 'MP4_TOWER', 4)
stalls = 0
for p in pW + pE:
    hatch(p, 'MP4_PARKING', 0xB9BCC2, 5)
    b = p.bounds
    for x0 in ((b[0], b[2]-5) if b[2]-b[0] > 15 else (b[0],)):
        y = b[1]+1
        while y+2.5 <= b[3]-1:
            s = box(x0, y, x0+5, y+2.5)
            if p.contains(s): outline(s, 'MP4_PARKING', 7); stalls += 1
            y += 2.5
for k, lay, col in (('villa', 'MP4_VILLA', 0xF4EE51), ('house', 'MP4_HOUSE', 0xF8991E)):
    for p in plots[k]: hatch(p, lay, col, 5); outline(p)
for gx in (GX, 339694.0):
    yb = yN(gx) + RING; hatch(box(gx-13.5, yb-6, gx+13.5, yb), 'MP4_GATE', 0x000000, 9)

NAMES = dict(mall='مول تجاري', health='مركز صحي', police='مركز شرطة', cd='دفاع مدني', kg='روضة', admin='ادارة المجمع',
             mosque='جامع', cpark='مواقف', secondary='مدرسة ثانوية', primary='مدرسة ابتدائية', sports='ملاعب',
             waterst='محطة ماء', power='محطة كهرباء', waste='نفايات')
for k, g, c in svc: p = g.representative_point(); text(NAMES[k], p.x, p.y, 3)
text('حديقة مركزية ونافورة', GX, CY+28, 4); text('برج سكني 1', tN.centroid.x, tN.centroid.y, 3.5); text('برج سكني 2', tS.centroid.x, tS.centroid.y, 3.5)
ms.set_redraw_order(order); doc.saveas(OUT + '.dxf')

# ---------------- checks + data for the board
allp = plots['villa'] + plots['house']
overlap = sum(a.intersection(b).area for i, a in enumerate(allp) for b in allp[i+1:i+40])
outside = sum(p.difference(inner).area for p in allp)
svc_u = unary_union([g for _, g, _ in svc])
clash = sum(p.intersection(svc_u).area for p in allp)
zones = []
def zlab(name, kind, poly, x, y):
    ps = [p for p in plots[kind] if poly.contains(p.representative_point())]
    if ps: zones.append(dict(name=name, n=len(ps), area=sum(p.area for p in ps), x=x, y=y))
zlab('فلل', 'villa', box(339035, 4033033, 339280, 4033200), 339158, 4033104)
zlab('فلل', 'villa', box(339490, 4033033, 339690, 4033200), 339598, 4033104)
zlab('دور', 'house', box(339035, 4033033, 339280, 4033200), 339200, 4033052)
zlab('دور', 'house', box(339490, 4033033, 339690, 4033200), 339640, 4033052)
zlab('دور', 'house', box(339035, 4032800, 339220, 4033013), 339127, 4032925)
zlab('دور', 'house', box(339510, 4032800, 339690, 4033013), 339601, 4032975)
labels = [dict(t='برج سكني 1', x=tN.centroid.x, y=tN.centroid.y, dark=1), dict(t='برج سكني 2', x=tS.centroid.x, y=tS.centroid.y, dark=1),
          dict(t='نافورة وحدائق الأبراج', x=339769, y=4033078), dict(t='مواقف', x=TX+8, y=4033100), dict(t='مواقف', x=339803, y=4033060), dict(t='ساحة المدخل', x=339714, y=CY),
          dict(t='حديقة مركزية ونافورة', x=GX, y=CY+26, a=garden.area), dict(t='الشارع الرئيسي 20 م', x=339560, y=CY),
          dict(t='الشارع الرئيسي 20 م', x=339180, y=CY)]
data = dict(villas=len(plots['villa']), houses=len(plots['house']), towers=2, flats=228, stalls=stalls, site=site.area,
            tower_zone=tz.area, garden=garden.area, zones=zones, labels=labels,
            checks=dict(overlap=round(overlap, 2), outside=round(outside, 2), clash=round(clash, 2)))
json.dump(data, open(OUT + '_data.json', 'w'), indent=1, ensure_ascii=False)
print(data['villas'], data['houses'], stalls, data['checks'], [(z['name'], z['n']) for z in zones])
