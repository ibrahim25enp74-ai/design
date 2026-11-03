# V2 of Ibrahim's developed master plan (2026-11-03):
#  - municipality land cancelled and merged into the compound
#  - residential blocks reorganised (back-to-back rows parallel to the long edges, 12 m streets,
#    no street segment longer than 150 m between intersections, enlarged corner plots)
#  - 50 villas 400 m2 only, as many 250 m2 houses as fit
#  - 2 towers at the east end with a semicircular entrance plaza + fountain + car park
# Keeps the user's west zone (sports, secondary school, services) and civic centre unchanged.
import sys, math, json, ezdxf
from ezdxf import colors
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union

SRC, OUT = sys.argv[1], sys.argv[2]
doc = ezdxf.readfile(SRC); ms = doc.modelspace()
B = [tuple(p[:2]) for p in ms.query('LWPOLYLINE[layer=="MP_BOUNDARY"]')[0].get_points()]
SW, NW, NE, SE = B
site = Polygon(B)
def yN(x): return NW[1] + (NE[1]-NW[1])*(x-NW[0])/(NE[0]-NW[0])
def yS(x): return SW[1] + (SE[1]-SW[1])*(x-SW[0])/(SE[0]-SW[0])

RING, ST = 12.0, 12.0
SP_BOT, SP_TOP = 4033014.0, 4033034.0          # spine 20 m, aligned with the existing roundabout
CIV = (339246.0, 339390.0)                      # civic centre kept as drawn by the user
WEST_X = 339025.0                               # sports / secondary / services kept

# ---------------- remove what is replaced
def bbox_x(e):
    try:
        if e.dxftype() == 'HATCH':
            xs = [v[0] for p in e.paths for v in getattr(p, 'vertices', [])]
            if not xs:
                return None
            return min(xs), max(xs)
        if e.dxftype() == 'LINE':
            return min(e.dxf.start.x, e.dxf.end.x), max(e.dxf.start.x, e.dxf.end.x)
        if e.dxftype() == 'LWPOLYLINE':
            xs = [p[0] for p in e.get_points()]; return min(xs), max(xs)
    except Exception:
        return None
    return None
DROP_LABELS = ('دور سكنية', 'فلل سكنية', 'برج سكني', 'ارض للبلدية')
kill = []
for e in ms:
    t = e.dxftype()
    if e.dxf.layer == 'MP_BOUNDARY' or t in ('TEXT',):
        continue
    if t == 'MULTILEADER':
        s = e.context.mtext.default_content if e.context.mtext else ''
        ins = e.context.mtext.insert if e.context.mtext else (0, 0)
        if any(k in s for k in DROP_LABELS) or s.strip().endswith('; }') or (('بوابة' in s) and ins[0] > 339500):
            kill.append(e)
        continue
    bx = bbox_x(e)
    if bx is None:
        continue
    if t == 'HATCH' and e.dxf.get('true_color') == 9672088 and bx[1] - bx[0] > 300:
        kill.append(e); continue                      # old road base
    inside_civ = bx[0] >= CIV[0] - 1 and bx[1] <= CIV[1] + 1
    inside_west = bx[1] <= WEST_X + 2
    gate1 = bx[0] >= 339300 and bx[1] <= 339335
    if not (inside_civ or inside_west or gate1):
        kill.append(e)
# multi-path hatches (e.g. all greens in one entity): keep the paths that lie in the kept zones
keep_paths = []
for e in kill:
    if e.dxftype() == 'HATCH' and e.dxf.get('true_color') != 9672088 and len(e.paths) > 1:
        for p in e.paths:
            xs = [v[0] for v in getattr(p, 'vertices', [])]
            if len(xs) > 2 and ((min(xs) >= CIV[0]-1 and max(xs) <= CIV[1]+1) or max(xs) <= WEST_X+2):
                keep_paths.append((e.dxf.layer, e.dxf.true_color, [tuple(v[:2]) for v in p.vertices]))
for e in kill:
    ms.delete_entity(e)
for layer, tc, pts in keep_paths:
    h = ms.add_hatch(dxfattribs={'layer': layer}); h.rgb = colors.int2rgb(tc)
    h.paths.add_polyline_path(pts, is_closed=True)

for name, col in [('MP2_ROAD', 8), ('MP2_VILLA', 2), ('MP2_HOUSE', 30), ('MP2_GREEN', 3), ('MP2_TOWER', 5),
                  ('MP2_PARKING', 9), ('MP2_PLAZA', 31), ('MP2_FOUNTAIN', 4), ('MP2_PLOTLINE', 7), ('MP2_TEXT', 7),
                  ('MP2_GATE', 1)]:
    if name not in doc.layers:
        doc.layers.add(name, color=col)
TC = dict(road=0x939598, villa=0xF4EE51, house=0xF8991E, green=0x136734, tower=0x2B2F3A, park=0xB9BCC2,
          plaza=0xE9DCC0, water=0x4FB3E8, gate=0x000000, garden=0x2E8B57)
order = {}
def hatch(poly, layer, col, key):
    polys = getattr(poly, 'geoms', [poly])
    for p in polys:
        if p.is_empty or p.area < 1:
            continue
        h = ms.add_hatch(dxfattribs={'layer': layer})
        h.rgb = colors.int2rgb(col)
        h.paths.add_polyline_path([c for c in p.exterior.coords][:-1], is_closed=True)
        for r in p.interiors:
            h.paths.add_polyline_path([c for c in r.coords][:-1], is_closed=True)
        order[h.dxf.handle] = key
def outline(poly, layer='MP2_PLOTLINE', col=7):
    for p in getattr(poly, 'geoms', [poly]):
        ms.add_lwpolyline(list(p.exterior.coords), close=True, dxfattribs={'layer': layer, 'color': col})

# ---------------- road base (everything east of the kept west zone)
road_base = site.intersection(box(WEST_X, 4032000, 340500, 4034000))
hatch(road_base, 'MP2_ROAD', TC['road'], 1)

# ---------------- plot rows
def quad(xa, xb, side, t0, t1):
    if side == 'N':
        return Polygon([(xa, yN(xa)-t0), (xb, yN(xb)-t0), (xb, yN(xb)-t1), (xa, yN(xa)-t1)])
    return Polygon([(xa, yS(xa)+t0), (xb, yS(xb)+t0), (xb, yS(xb)+t1), (xa, yS(xa)+t1)])
def fits(x, side, t1):
    return (yN(x)-t1 >= SP_TOP - 0.01) if side == 'N' else (yS(x)+t1 <= SP_BOT + 0.01)
def fit_limit(xa, xb, side, t1):
    """largest sub-range [xa, xe] (from the west) in which the row fits beside the spine"""
    if fits(xa, side, t1) and fits(xb, side, t1):
        return xb
    if not fits(xa, side, t1):
        return None
    lo, hi = xa, xb
    for _ in range(40):
        m = (lo+hi)/2
        lo, hi = (m, hi) if fits(m, side, t1) else (lo, m)
    return lo
plots = {'villa': [], 'house': []}
pockets = []
def row(xa, xb, side, t0, depth, front, kind, n=None):
    xe = fit_limit(xa, xb, side, t0+depth)
    if xe is None:
        return
    L = xe - xa
    k = n if n else int(L // front)
    if k < 1:
        return
    extra = L - k*front                          # corner plots enlarged to fill the block
    if n:                                        # fixed count (villas): no enlargement, rest -> pocket park
        pockets.append(quad(xa+k*front, xe, side, t0, t0+depth)); extra = 0
    w = [front]*k
    if k == 1: w[0] += extra
    else: w[0] += extra/2; w[-1] += extra/2
    x = xa
    for wi in w:
        plots[kind].append(quad(x, x+wi, side, t0, t0+depth)); x += wi
def block(xa, xb, side, t0, depth, front, kind, n=None):
    row(xa, xb, side, t0, depth, front, kind, n)
    row(xa, xb, side, t0+depth, depth, front, kind, n)

VF, VD = 14.0, 28.6          # villa 14 x 28.6 = 400 m2
HF, HD = 12.5, 20.0          # house 12.5 x 20 = 250 m2
# west zone (villas) : vertical street 339134-339146
W1, W2 = (339035.0, 339134.0), (339146.0, 339246.0)
for seg in (W1, W2):
    block(*seg, 'N', RING, VD, VF, 'villa', 7)                     # 2 x 7 per segment north
    row(*seg, 'N', RING+2*VD+ST, HD, HF, 'house')                 # single house row on the street
block(*W1, 'S', RING, VD, VF, 'villa', 6)
block(*W2, 'S', RING, VD, VF, 'villa', 5)
for seg in (W1, W2):
    block(*seg, 'S', RING+2*VD+ST, HD, HF, 'house')
# east zone (houses) : vertical streets 339482-339494, 339582-339594
E = [(339390.0, 339482.0), (339494.0, 339582.0), (339594.0, 339688.0)]
for seg in E:
    block(*seg, 'N', RING, HD, HF, 'house')
    block(*seg, 'N', RING+2*HD+ST, HD, HF, 'house')
    block(*seg, 'S', RING, HD, HF, 'house')
    block(*seg, 'S', RING+2*HD+ST, HD, HF, 'house')

# ---------------- green: residual land inside each zone half, between the last street and the spine
def band(xa, xb, side, t_from):
    xs = [xa + (xb-xa)*i/40 for i in range(41)]
    if side == 'N':
        top = [(x, yN(x)-t_from) for x in xs]; bot = [(x, SP_TOP) for x in reversed(xs)]
    else:
        top = [(x, SP_BOT) for x in xs]; bot = [(x, yS(x)+t_from) for x in reversed(xs)]
    p = Polygon(top+bot).buffer(0)
    return p
green = []
for seg in (W1, W2):
    green.append(band(*seg, 'N', RING+2*VD+ST+HD))
    green.append(band(*seg, 'S', RING+2*VD+ST+2*HD))
for seg in E:
    green.append(band(*seg, 'N', RING+4*HD+ST))
    green.append(band(*seg, 'S', RING+2*HD+ST))
G = unary_union([g for g in green if g.is_valid]+pockets).difference(unary_union(plots['house']+plots['villa']).buffer(0.01))
G = unary_union([g for g in getattr(G, 'geoms', [G]) if g.area > 30 and g.minimum_rotated_rectangle.length/4 > 0])
hatch(G, 'MP2_GREEN', TC['green'], 5)

for kind in ('villa', 'house'):
    for p in plots[kind]:
        hatch(p, 'MP2_VILLA' if kind == 'villa' else 'MP2_HOUSE', TC[kind], 5)
        outline(p)

# ---------------- tower zone (former municipality land + east tip)
TX = 339700.0
def xE(y): return SE[0] + (NE[0]-SE[0])*(y-SE[1])/(NE[1]-SE[1])
ys = [yS(TX)+RING + i*(yN(TX)-RING - yS(TX)-RING)/40 for i in range(41)]
tz = site.intersection(box(TX, 4032000, 340500, 4034000))
tz_in = Polygon([(TX, yS(TX)+RING), (TX, yN(TX)-RING)] +
                [(xE(y)-RING*1.003, y) for y in (yN(xE(yN(TX)))-RING, yS(xE(yS(TX)))+RING)])
tz_in = tz_in.intersection(site.buffer(-RING))
cy = (SP_BOT+SP_TOP)/2
plaza = Point(TX, cy).buffer(30, 64).intersection(box(TX, cy-31, TX+31, cy+31))
fount = Point(TX+13, cy).buffer(9, 48)
fount_c = Point(TX+13, cy).buffer(3.5, 32)
T_W, T_D = 34.8, 32.4
tN = box(339752, 4033078, 339752+T_W, 4033078+T_D)
tS = box(339752, 4032995, 339752+T_W, 4032995+T_D)
park = box(339740, 4033035, 339900, 4033068).intersection(tz_in)
garden = tz_in.difference(unary_union([plaza, tN, tS, park]))
hatch(garden, 'MP2_GREEN', TC['garden'], 5)
hatch(plaza, 'MP2_PLAZA', TC['plaza'], 6)
hatch(fount, 'MP2_FOUNTAIN', TC['water'], 7)
hatch(fount_c, 'MP2_FOUNTAIN', 0xFFFFFF, 8)
hatch(park, 'MP2_PARKING', TC['park'], 6)
for t in (tN, tS):
    hatch(t, 'MP2_TOWER', TC['tower'], 7); outline(t, 'MP2_TOWER', 4)
# parking stalls: 2 bays of (5 m stall | 6 m aisle | 5 m stall)
pb = park.bounds; stalls = 0
for y0 in (pb[1], pb[1]+16.5):
    for yy in (y0, y0+11):
        x = pb[0]+2
        while x+2.5 <= pb[2]-2:
            s = box(x, yy, x+2.5, yy+5)
            if park.contains(s):
                outline(s, 'MP2_PARKING', 7); stalls += 1
            x += 2.5
# gate 2 moved to the street that leads to the tower zone
gx = 339694.0
g2 = box(gx-13.5, yN(gx)-6, gx+13.5, yN(gx))
hatch(g2, 'MP2_GATE', TC['gate'], 9)

# ---------------- text labels in the DXF
def text(s, x, y, h=4.0):
    ms.add_text(s, dxfattribs={'layer': 'MP2_TEXT', 'height': h, 'style': 'Standard'}).set_placement((x, y), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
text('برج سكني 1', tN.centroid.x, tN.centroid.y, 3.5); text('برج سكني 2', tS.centroid.x, tS.centroid.y, 3.5)
text('ساحة المدخل ونافورة', TX+16, cy+20, 3); text('مواقف سيارات', park.centroid.x+8, park.centroid.y, 3.5)
text('بوابة المشروع 2', gx, yN(gx)+6, 4)

ms.set_redraw_order(order)
doc.saveas(OUT + '.dxf')

FLATS_PER_TOWER = 114     # 342 flats / 3 towers in the approved plan
data = dict(villas=len(plots['villa']), houses=len(plots['house']), towers=2, flats=2*FLATS_PER_TOWER,
            stalls=stalls, site=site.area,
            villa_area=sum(p.area for p in plots['villa']), house_area=sum(p.area for p in plots['house']),
            green_res=G.area, tower_zone=tz_in.area, towers_fp=tN.area+tS.area, plaza=plaza.area, park=park.area,
            garden=garden.area)
json.dump(data, open(OUT + '_data.json', 'w'), indent=1, ensure_ascii=False)
print({k: (round(v) if isinstance(v, float) else v) for k, v in data.items()})
