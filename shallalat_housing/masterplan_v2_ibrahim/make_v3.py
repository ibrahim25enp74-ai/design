# V3: new layout on the site boundary only. Keeps the user's zoning of services (west zone + civic centre
# around the roundabout) and towers (east end). Roads: ring 15 m, spine 20 m with planted median, local 12 m,
# no street longer than 150 m between junctions. Blocks = back-to-back rows bounded by streets on all sides;
# parks are separate street-bounded blocks (no green attached to a residential block).
import sys, json, ezdxf
from ezdxf import colors
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union

SRC, OUT = sys.argv[1], sys.argv[2]
src = ezdxf.readfile(SRC); sm = src.modelspace()
B = [tuple(p[:2]) for p in sm.query('LWPOLYLINE[layer=="MP_BOUNDARY"]')[0].get_points()]
SW, NW, NE, SE = B
site = Polygon(B)
RING, ST, SPW = 15.0, 12.0, 20.0
inner = site.buffer(-RING, join_style=2)
def yN(x): return NW[1] + (NE[1]-NW[1])*(x-NW[0])/(NE[0]-NW[0]) - RING
def yS(x): return SW[1] + (SE[1]-SW[1])*(x-SW[0])/(SE[0]-SW[0]) + RING
SP_BOT, SP_TOP = 4033013.0, 4033033.0
CIV = (339246.0, 339390.0); WEST_X = 339025.0

# ---- kept user zoning: hatches of the west zone and the civic centre, clipped to the inner ring
kept = []
for h in sm.query('HATCH'):
    if not h.dxf.hasattr('true_color') or h.dxf.true_color in (9672088, 0): continue
    for p in h.paths:
        try: v = [tuple(x[:2]) for x in p.vertices]
        except Exception: continue
        if len(v) < 3: continue
        xs = [a[0] for a in v]
        if (min(xs) >= CIV[0]-1 and max(xs) <= CIV[1]+1) or max(xs) <= WEST_X+2:
            g = Polygon(v).buffer(0).intersection(inner)
            if not g.is_empty: kept.append((h.dxf.true_color, g))
# roundabout island (circle path in the user's file)
kept.append((0x136734, Point(339317.0, 4033023.0).buffer(20, 64)))

doc = ezdxf.new('R2018', setup=True); ms = doc.modelspace(); doc.header['$INSUNITS'] = 6
for name, col in [('MP_BOUNDARY', 1), ('MP3_ROAD', 8), ('MP3_ZONING', 7), ('MP3_VILLA', 2), ('MP3_HOUSE', 30),
                  ('MP3_GREEN', 3), ('MP3_TOWER', 5), ('MP3_PARKING', 9), ('MP3_PLAZA', 31), ('MP3_FOUNTAIN', 4),
                  ('MP3_PLOTLINE', 7), ('MP3_TEXT', 7), ('MP3_GATE', 1)]:
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
def outline(poly, layer='MP3_PLOTLINE', col=7):
    for p in getattr(poly, 'geoms', [poly]):
        ms.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={'layer': layer, 'color': col})
hatch(site, 'MP3_ROAD', 0x939598, 1)
for tc, g in kept: hatch(g, 'MP3_ZONING', tc, 3)

# ---- plots
plots = {'villa': [], 'house': []}; parks = []
def quad(xa, xb, side, t0, t1):
    if side == 'N': return Polygon([(xa, yN(xa)-t0), (xb, yN(xb)-t0), (xb, yN(xb)-t1), (xa, yN(xa)-t1)])
    return Polygon([(xa, yS(xa)+t0), (xb, yS(xb)+t0), (xb, yS(xb)+t1), (xa, yS(xa)+t1)])
def fits(x, side, t1): return (yN(x)-t1 >= SP_TOP-0.01) if side == 'N' else (yS(x)+t1 <= SP_BOT+0.01)
def limit(xa, xb, side, t1):
    if not fits(xa, side, t1): return None
    if fits(xb, side, t1): return xb
    lo, hi = xa, xb
    for _ in range(40):
        m = (lo+hi)/2; lo, hi = (m, hi) if fits(m, side, t1) else (lo, m)
    return lo
def split(L, f, n=None):
    k = n or max(1, int(L // f)); e = L - k*f; w = [f]*k
    if k == 1: w[0] += e
    else: w[0] += e/2; w[-1] += e/2
    return w
def hrow(xa, xb, side, t0, d, f, kind, n=None):
    xe = limit(xa, xb, side, t0+d)
    if xe is None or xe-xa < f: return
    x = xa
    for w in split(xe-xa, f, n):
        plots[kind].append(quad(x, x+w, side, t0, t0+d)); x += w
def hblock(xa, xb, side, t0, d, f, kind, n=None):
    hrow(xa, xb, side, t0, d, f, kind, n); hrow(xa, xb, side, t0+d, d, f, kind, n)
def vblock(xa, xb, t0, f, kind, nmax=None):
    """south-half block perpendicular to the edge: 2 columns back to back, from street (t0) up to the spine"""
    xm = (xa+xb)/2; placed = 0
    for c0, c1 in ((xa, xm), (xm, xb)):
        y0 = max(yS(c0), yS(c1)) + t0; L = SP_BOT - y0
        if L < f: continue
        ws = split(L, f);
        if nmax: ws = ws[:nmax];
        y = SP_BOT
        for i, w in enumerate(ws):
            top = y; bot = y - w
            if i == len(ws)-1 and not nmax: q = Polygon([(c0, top), (c1, top), (c1, yS(c1)+t0), (c0, yS(c0)+t0)])
            else: q = box(c0, bot, c1, top)
            plots[kind].append(q); y = bot; placed += 1
    return placed

HF, HD = 12.5, 20.0                 # house 12.5 x 20 = 250
VF, VD = 15.75, 25.4                # villa 15.75 x 25.4 = 400
# --- north half, both zones: outer block | 12 m street | inner block | spine
NWs = [(339040.0, 339134.5), (339146.5, 339241.0)]
NEs = [(339393.0, 339483.3), (339495.3, 339585.7), (339597.7, 339688.0)]
for seg in NWs + NEs:
    hblock(*seg, 'N', 0, HD, HF, 'house')
    if seg == NEs[1]: parks.append(quad(*seg, 'N', 2*HD+ST, 4*HD+ST)); continue      # pocket park block
    hblock(*seg, 'N', 2*HD+ST, HD, HF, 'house')
# --- south-west: villa block on the ring, street, perpendicular blocks to the spine
for seg in NWs: hblock(*seg, 'S', 0, VD, VF, 'villa', 6)
t_in = 2*VD + ST
vb = [(339040.0, 339081.25), (339093.25, 339134.5), (339146.5, 339187.75), (339199.75, 339241.0)]
VCOL = 20.625; VFV = 400/VCOL; HFV = 250/VCOL
# --- south-east: villa block where it fits, then houses
SEs = NEs
for seg in SEs[:2]: hblock(*seg, 'S', 0, VD, VF, 'villa', 5)
nv = len(plots['villa'])
need = 50 - nv
for i, (a, b) in enumerate(vb):
    if need > 0:
        before = len(plots['villa'])
        vblock(a, b, t_in, VFV, 'villa', nmax=None)
        got = len(plots['villa']) - before
        if got > need:                     # keep exactly 50: drop extra from the top of the block
            del plots['villa'][before+need:]
            got = need
        need -= got
    else:
        vblock(a, b, t_in, HFV, 'house')
hblock(*SEs[2], 'S', 0, HD, HF, 'house')
# SE wedge between the villa street and the spine = park (bounded by streets on both sides)
def wedge(xa, xb, t_from):
    xs = [xa + (xb-xa)*i/30 for i in range(31)]
    top = [(x, SP_BOT) for x in xs]; bot = [(x, yS(x)+t_from) for x in reversed(xs)]
    return Polygon(top+bot).buffer(0).intersection(box(xa, yS(xb)+t_from, xb, SP_BOT))
for seg in SEs[:2]:
    w = wedge(*seg, 2*VD+ST)
    if w.area > 200: parks.append(w)
# spine planted median
med = [box(339040, 4033021, 339241, 4033025), box(339393, 4033021, 339688, 4033025)]

# ---- tower zone (east end, former municipality land)
TX = 339700.0; cy = (SP_BOT+SP_TOP)/2
tz = inner.intersection(box(TX, 4032000, 340500, 4034000))
plaza = Point(TX, cy).buffer(30, 64).intersection(box(TX, cy-31, TX+31, cy+31))
fount = Point(TX+13, cy).buffer(9, 48)
tN = box(339752, 4033080, 339752+34.8, 4033080+32.4); tS = box(339752, 4032994, 339752+34.8, 4032994+32.4)
park = box(339740, 4033035, 339900, 4033070).intersection(tz)
garden = tz.difference(unary_union([plaza, tN, tS, park]))

G = unary_union(parks + med)
hatch(G, 'MP3_GREEN', 0x136734, 5)
hatch(garden, 'MP3_GREEN', 0x2E8B57, 5)
hatch(plaza, 'MP3_PLAZA', 0xE9DCC0, 6); hatch(fount, 'MP3_FOUNTAIN', 0x4FB3E8, 7)
hatch(park, 'MP3_PARKING', 0xB9BCC2, 6)
for t in (tN, tS): hatch(t, 'MP3_TOWER', 0x2B2F3A, 7); outline(t, 'MP3_TOWER', 4)
pb = park.bounds; stalls = 0
for y0 in (pb[1], pb[1]+17.5):
    for yy in (y0, y0+12):
        x = pb[0]+2
        while x+2.5 <= pb[2]-2:
            s = box(x, yy, x+2.5, yy+5)
            if park.contains(s): outline(s, 'MP3_PARKING', 7); stalls += 1
            x += 2.5
for k, lay, col in (('villa', 'MP3_VILLA', 0xF4EE51), ('house', 'MP3_HOUSE', 0xF8991E)):
    for p in plots[k]: hatch(p, lay, col, 5); outline(p)
gates = []
for gx in (339318.5, 339694.0):
    yb = yN(gx) + RING; g = box(gx-13.5, yb-6, gx+13.5, yb); hatch(g, 'MP3_GATE', 0x000000, 9); gates.append(gx)
def text(s, x, y, h=4.0):
    ms.add_text(s, dxfattribs={'layer': 'MP3_TEXT', 'height': h}).set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
names = {0xCD2027: 'مول تجاري', 0xF27172: 'مركز شرطة', 0xF7ABAE: 'دفاع مدني', 0xA953A0: 'مركز صحي', 0xFECC66: 'ادارة المجمع',
         0x2776BB: 'مدرسة ابتدائية', 0x105689: 'روضة', 0xADDDF7: 'جامع', 0x22346E: 'مدرسة ثانوية', 0x78BA6E: 'ملاعب'}
for tc, g in kept:
    if tc in names and g.area > 300: c = g.representative_point(); text(names[tc], c.x, c.y, 3)
text('برج سكني 1', tN.centroid.x, tN.centroid.y, 3.5); text('برج سكني 2', tS.centroid.x, tS.centroid.y, 3.5)
text('ساحة المدخل ونافورة', TX+16, cy+20, 3); text('مواقف سيارات', park.centroid.x+8, park.centroid.y, 3.5)
for i, gx in enumerate(gates, 1): text(f'بوابة المشروع {i}', gx, yN(gx)+RING+6, 4)
ms.set_redraw_order(order)
doc.saveas(OUT + '.dxf')

zones = []
def zlab(name, kind, poly, x, y):
    ps = [p for p in plots[kind] if poly.contains(p.representative_point())]
    if ps: zones.append(dict(name=name, n=len(ps), area=sum(p.area for p in ps), x=x, y=y))
zlab('فلل', 'villa', box(339035, 4032800, 339245, 4033013), 339140, 4032935)
zlab('فلل', 'villa', box(339390, 4032800, 339600, 4033013), 339490, 4032952)
zlab('دور', 'house', box(339035, 4033033, 339245, 4033200), 339140, 4033085)
zlab('دور', 'house', box(339390, 4033033, 339690, 4033200), 339540, 4033085)
zlab('دور', 'house', box(339035, 4032800, 339245, 4033013), 339200, 4032990)
zlab('دور', 'house', box(339590, 4032800, 339690, 4033013), 339640, 4032985)
data = dict(villas=len(plots['villa']), houses=len(plots['house']), towers=2, flats=228, stalls=stalls,
            site=site.area, zones=zones, parks=[dict(x=p.representative_point().x, y=p.representative_point().y, area=p.area) for p in parks])
json.dump(data, open(OUT + '_data.json', 'w'), indent=1, ensure_ascii=False)
print(len(plots['villa']), len(plots['house']), stalls, [(z['name'], z['n']) for z in zones], [round(p.area) for p in parks])
