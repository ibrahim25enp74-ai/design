# V5 (2026-11-03): from the site boundary. Central gate -> boulevard -> CIRCULAR civic square (round garden +
# fountain, ring road) with services around it at the user's areas; no surface parking anywhere (basements);
# all residential blocks double (back to back); villas 16x25 = 400 (50), houses 10x25 = 250 (max);
# north/south cross streets staggered ~30 m so every junction is a T; towers at the east end in a landscaped court.
import sys, json, math, ezdxf
from ezdxf import colors
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union

SRC, OUT = sys.argv[1], sys.argv[2]
sm = ezdxf.readfile(SRC).modelspace()
B = [tuple(p[:2]) for p in sm.query('LWPOLYLINE[layer=="MP_BOUNDARY"]')[0].get_points()]
SW, NW, NE, SE = B
site = Polygon(B)
RING, ST = 15.0, 12.0
inner = site.buffer(-RING, join_style=2)
KS = math.hypot(SE[0]-SW[0], SE[1]-SW[1])/(SE[0]-SW[0])
def yN(x): return NW[1] + (NE[1]-NW[1])*(x-NW[0])/(NE[0]-NW[0]) - RING
def yS(x): return SW[1] + (SE[1]-SW[1])*(x-SW[0])/(SE[0]-SW[0]) + RING*KS
SP_BOT, SP_TOP = 4033013.0, 4033033.0; CY = 4033023.0

doc = ezdxf.new('R2018', setup=True); ms = doc.modelspace(); doc.header['$INSUNITS'] = 6
for name, col in [('MP_BOUNDARY', 1), ('MP5_ROAD', 8), ('MP5_SERVICES', 7), ('MP5_VILLA', 2), ('MP5_HOUSE', 30),
                  ('MP5_GREEN', 3), ('MP5_TOWER', 5), ('MP5_PAVING', 31), ('MP5_FOUNTAIN', 4), ('MP5_RAMP', 8),
                  ('MP5_PLOTLINE', 7), ('MP5_TEXT', 7), ('MP5_GATE', 1)]:
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
def outline(poly, layer='MP5_PLOTLINE', col=7):
    for p in getattr(poly, 'geoms', [poly]):
        if p.geom_type == 'Polygon': ms.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={'layer': layer, 'color': col})
def text(s, x, y, h=4.0):
    ms.add_text(s, dxfattribs={'layer': 'MP5_TEXT', 'height': h}).set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
hatch(site, 'MP5_ROAD', 0x939598, 1)

# ---------------- residential
plots = {'villa': [], 'house': []}
def quad(xa, xb, side, t0, t1):
    if side == 'N': return Polygon([(xa, yN(xa)-t0), (xb, yN(xb)-t0), (xb, yN(xb)-t1), (xa, yN(xa)-t1)])
    return Polygon([(xa, yS(xa)+t0), (xb, yS(xb)+t0), (xb, yS(xb)+t1), (xa, yS(xa)+t1)])
def split(L, f):
    """whole-metre frontages; the leftover goes to the two corner plots (rounded to whole metres)"""
    k = int(L // f); e = round(L - k*f); w = [f]*k
    if k == 1: w[0] += e
    elif k > 1: w[0] += e//2; w[-1] += e - e//2
    return w
def hblock(xa, xb, side, t0, d, f, kind):           # double block parallel to the edge
    for r in (0, 1):
        x = xa
        for w in split(xb-xa, f):
            plots[kind].append(quad(x, x+w, side, t0+r*d, t0+(r+1)*d)); x += w
def vblock(xa, xb, side, t0, f, kind):              # double block perpendicular to the edge, up to the spine
    xm = (xa+xb)/2
    for c0, c1 in ((xa, xm), (xm, xb)):
        if side == 'S':
            L = SP_BOT - max(yS(c0), yS(c1)) - t0; y = SP_BOT; k = int(L // f)
            for i in range(k):
                q = Polygon([(c0, y), (c1, y), (c1, yS(c1)+t0), (c0, yS(c0)+t0)]) if i == k-1 else box(c0, y-f, c1, y)
                plots[kind].append(q); y -= f
        else:
            L = min(yN(c0), yN(c1)) - t0 - SP_TOP; y = SP_TOP; k = int(L // f)
            for i in range(k):
                q = Polygon([(c0, y), (c1, y), (c1, yN(c1)-t0), (c0, yN(c0)-t0)]) if i == k-1 else box(c0, y, c1, y+f)
                plots[kind].append(q); y += f
VF, VD, HF, HD = 16.0, 25.0, 10.0, 25.0
TI = 2*VD + ST                                       # depth of the inner street edge from the ring
# north-west: villa block on the ring (cross street 339151-339163), inner perpendicular house blocks
hblock(339071, 339151, 'N', 0, VD, VF, 'villa'); hblock(339163, 339307, 'N', 0, VD, VF, 'villa')
for a in (339071, 339133, 339195, 339257): vblock(a, a+50, 'N', TI, HF, 'house')
# north-east: villas (cross streets 339548-339560, 339640-339652) + small house block, inner perpendicular blocks
hblock(339452, 339548, 'N', 0, VD, VF, 'villa'); hblock(339560, 339640, 'N', 0, VD, VF, 'villa')
hblock(339652, 339688, 'N', 0, HD, HF, 'house')
for a in (339452, 339514, 339576, 339638): vblock(a, a+50, 'N', TI, HF, 'house')
# south-west: house block on the ring (cross street 339121-339133), inner perpendicular blocks
hblock(339040, 339121, 'S', 0, HD, HF, 'house'); hblock(339133, 339276, 'S', 0, HD, HF, 'house')
for a in (339040, 339102, 339164, 339226): vblock(a, a+50, 'S', 2*HD+ST, HF, 'house')
# south-east: perpendicular blocks from the ring to the spine
for a in (339483, 339545, 339607): vblock(a, a+50, 'S', 0, HF, 'house')

# ---------------- circular civic square
GX = (339319 + 339440)/2
RG, RL = 30.0, 42.0                                  # garden radius, outer edge of the ring road
disc = Point(GX, CY).buffer(RL + 3, 96)
NREG = Polygon([(339319, SP_TOP), (339440, SP_TOP), (339440, yN(339440)), (339319, yN(339319))])
SREG = Polygon([(339288, SP_BOT), (339471, SP_BOT), (339471, yS(339471)), (339288, yS(339288))])
boul = box(GX-10, CY, GX+10, 4033200)
def grow(xa, xb, start, sign, target, ymin=None, ymax=None, cut=()):
    """lot [xa,xb] growing from y=start in direction sign until its area (minus the square) reaches target"""
    def lot(d):
        y0, y1 = sorted((start, start + sign*d))
        g = box(xa, y0, xb, y1).intersection(inner).difference(disc).difference(boul).difference(box(0, SP_BOT, 1e7, SP_TOP))
        for c in cut: g = g.difference(c)
        return g
    lo, hi = 0.0, 400.0
    for _ in range(50):
        m = (lo+hi)/2
        lo, hi = (m, hi) if lot(m).area < target else (lo, m)
    return lot(hi)
svc = {}
svc['mall'] = grow(339319, GX-10, yN(339319)+1, -1, 3500)
y = yN(339440)+1
svc['health'] = grow(339415, 339440, y, -1, 800)
y2 = svc['health'].bounds[1]; svc['police'] = grow(339415, 339440, y2, -1, 600)
y3 = svc['police'].bounds[1]; svc['cd'] = grow(339415, 339440, y3, -1, 600)
svc['admin'] = grow(GX+10, 339415, yN(339415)+1, -1, 300)
svc['secondary'] = grow(339288, GX-6, 4032800, 1, 4000 + 0)
svc['kg'] = grow(339288, 339334, svc['secondary'].bounds[3], 1, 1500, cut=[svc['secondary']])
svc['primary'] = grow(GX+6, 339471, 4032800, 1, 3000)
svc['mosque'] = grow(339427, 339471, svc['primary'].bounds[3], 1, 1000, cut=[svc['primary']])
COLS = dict(mall=0xCD2027, health=0xA953A0, police=0xF27172, cd=0xF7ABAE, admin=0xFECC66, secondary=0x22346E,
            kg=0x105689, primary=0x2776BB, mosque=0xADDDF7)
# west zone: sports (north incl. the strip up to the jogged west road) + utilities (south)
westN = inner.intersection(box(338800, SP_TOP, 339059, 4033200))
westS = inner.intersection(box(338800, 4032800, 339025, SP_BOT))
svc['sports'] = unary_union([westN, westS.intersection(box(338800, 4032955, 339025, SP_BOT))])
svc['waterst'] = westS.intersection(box(338800, 4032911, 339025, 4032943))
svc['power'] = westS.intersection(box(338800, 4032878, 339025, 4032911))
svc['waste'] = westS.intersection(box(338800, 4032800, 339025, 4032878))
COLS.update(sports=0x78BA6E, waterst=0x00A6A6, power=0xF2C200, waste=0x8B6B4A)
for k, g in svc.items(): hatch(g, 'MP5_SERVICES', COLS[k], 3); outline(g, 'MP5_SERVICES', 7)
garden = Point(GX, CY).buffer(RG, 96)
spine_c = box(339288, SP_BOT, 339471, SP_TOP)
paving = unary_union([NREG, SREG]).difference(unary_union(list(svc.values()))).difference(Point(GX, CY).buffer(RL, 96)) \
    .difference(boul.intersection(box(0, CY+RL-1, 1e7, 1e8))).difference(spine_c)
paving = unary_union([g for g in getattr(paving, 'geoms', [paving]) if g.area > 20])
hatch(paving, 'MP5_PAVING', 0xD8CCB0, 3)
hatch(garden, 'MP5_GREEN', 0x136734, 4)
hatch(Point(GX, CY).buffer(14, 64), 'MP5_PAVING', 0xE9DCC0, 5); hatch(Point(GX, CY).buffer(9, 64), 'MP5_FOUNTAIN', 0x4FB3E8, 6)

# ---------------- tower court (east end): 2 towers on the north side, fountain court on the spine axis,
# gardens with paths, basement ramps from the streets; no surface parking
tzN = inner.intersection(box(339700, CY, 340500, 4034000)); tzS = inner.intersection(box(339669, 4032000, 340500, CY))
tz = unary_union([tzN, tzS])
T1 = box(339704, 4033082, 339704+34.8, 4033082+32.4); T2 = box(339752, 4033082, 339752+34.8, 4033082+32.4)
FC = Point(339745.4, 4033040)
park = tz.intersection(box(339792, 4032900, 340500, 4034000))   # tower parking: far east only
court = FC.buffer(22, 96)
entry = Point(339700, CY).buffer(18, 64).intersection(box(339700, CY-19, 339740, CY+19))
paths = unary_union([LineString([(339700, CY), FC.coords[0]]).buffer(3), LineString([FC.coords[0], (339721, 4033082)]).buffer(2.5),
                     LineString([FC.coords[0], (339769, 4033082)]).buffer(2.5), LineString([FC.coords[0], (339792, 4033040)]).buffer(2.5),
                     LineString([(339690, 4033000), (339792, 4033000)]).buffer(1.6)]).intersection(tz)
fore = unary_union([box(339704, 4033072, 339738.8, 4033082), box(339752, 4033072, 339786.8, 4033082)])
ramps = [box(339700, 4033118, 339712, 4033124), box(339786.8, 4033100, 339792, 4033106)]
play = Point(339728, 4033006).buffer(9, 48)
tgarden = tz.difference(unary_union([T1, T2, court, entry, paths, fore, play, park] + ramps))
paths = paths.difference(park)
hatch(park, 'MP5_PAVING', 0xB9BCC2, 5)
stalls = 0
pb = park.bounds
for x0 in (pb[0]+1, pb[0]+12):
    y = pb[1]+1
    while y+2.5 <= pb[3]-1:
        s_ = box(x0, y, x0+5, y+2.5)
        if park.contains(s_): outline(s_, 'MP5_PAVING', 7); stalls += 1
        y += 2.5
hatch(tgarden, 'MP5_GREEN', 0x2E8B57, 4)
hatch(unary_union([entry, paths, fore, court]), 'MP5_PAVING', 0xE9DCC0, 5)
hatch(FC.buffer(13, 64), 'MP5_FOUNTAIN', 0x4FB3E8, 6); hatch(play, 'MP5_PAVING', 0xF2B27A, 5)
for r in ramps: hatch(r, 'MP5_RAMP', 0x555555, 6)
for t in (T1, T2): hatch(t, 'MP5_TOWER', 0x2B2F3A, 7); outline(t, 'MP5_TOWER', 4)

for k, lay, col in (('villa', 'MP5_VILLA', 0xF4EE51), ('house', 'MP5_HOUSE', 0xF8991E)):
    for p in plots[k]: hatch(p, lay, col, 5); outline(p)
for gx in (GX, 339694.0):
    yb = yN(gx) + RING; hatch(box(gx-13.5, yb-6, gx+13.5, yb), 'MP5_GATE', 0x000000, 9)
NAMES = dict(mall='مول تجاري', health='مركز صحي', police='مركز شرطة', cd='دفاع مدني', kg='روضة', admin='ادارة المجمع',
             mosque='جامع', secondary='مدرسة ثانوية', primary='مدرسة ابتدائية', sports='ملاعب',
             waterst='محطة ماء', power='محطة كهرباء', waste='نفايات')
for k, g in svc.items(): p = g.representative_point(); text(NAMES[k], p.x, p.y, 3)
text('الساحة المركزية', GX, CY+20, 4); text('برج سكني 1', T1.centroid.x, T1.centroid.y, 3.5); text('برج سكني 2', T2.centroid.x, T2.centroid.y, 3.5)
ms.set_redraw_order(order); doc.saveas(OUT + '.dxf')

# ---------------- checks + board data
allp = plots['villa'] + plots['house']
U = unary_union([p.buffer(-0.05) for p in allp])
checks = dict(overlap=round(sum(p.area for p in allp) - unary_union(allp).area, 2),
              outside=round(sum(p.difference(inner).area for p in allp), 2),
              clash=round(U.intersection(unary_union(list(svc.values()) + [tz, paving])).area, 2))
zones = []
def zlab(name, kind, poly, x, y):
    ps = [p for p in plots[kind] if poly.contains(p.representative_point())]
    if ps: zones.append(dict(name=name, n=len(ps), area=sum(p.area for p in ps), x=x, y=y))
zlab('فلل', 'villa', box(339060, 4033033, 339310, 4033200), 339157, 4033104)
zlab('فلل', 'villa', box(339450, 4033033, 339650, 4033200), 339554, 4033104)
zlab('دور', 'house', box(339060, 4033033, 339310, 4033200), 339190, 4033052)
zlab('دور', 'house', box(339450, 4033033, 339690, 4033200), 339610, 4033052)
zlab('دور', 'house', box(339035, 4032800, 339280, 4033013), 339160, 4032930)
zlab('دور', 'house', box(339480, 4032800, 339660, 4033013), 339570, 4032985)
labels = [dict(t='برج سكني 1', x=T1.centroid.x, y=T1.centroid.y, dark=1), dict(t='برج سكني 2', x=T2.centroid.x, y=T2.centroid.y, dark=1),
          dict(t='ساحة النافورة', x=FC.x, y=FC.y-28), dict(t='مواقف الأبراج', x=339803, y=4033060), dict(t='ألعاب أطفال', x=339728, y=4032992),
          dict(t='الساحة المركزية الدائرية', x=GX, y=CY-24, a=garden.area), dict(t='الشارع الرئيسي 20 م', x=339560, y=CY),
          dict(t='الشارع الرئيسي 20 م', x=339180, y=CY)]
data = dict(villas=len(plots['villa']), houses=len(plots['house']), towers=2, flats=228, stalls=stalls, site=site.area,
            tower_zone=tz.area, garden=garden.area, paving=paving.area, zones=zones, labels=labels, GX=GX,
            svc={k: round(g.area) for k, g in svc.items()}, checks=checks)
json.dump(data, open(OUT + '_data.json', 'w'), indent=1, ensure_ascii=False)
print(data['villas'], data['houses'], data['svc'], checks, [(z['name'], z['n']) for z in zones], round(paving.area))
