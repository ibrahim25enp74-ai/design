# Shallalat - Ibrahim's proposal re-fitted on the NEW site boundary (Site_Boundary_AR-3.dxf)
# minus 10 % for the municipality, more units, fewer internal streets.
# Local frame of the boundary file: x east, y north, metres.
import math, json, sys
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
import ezdxf
from ezdxf.enums import TextEntityAlignment

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
A, B = (0.0, 0.0), (900.0, 0.0)
C, D = (880.9897957549033, -148.79049746055594), (38.02040849019346, -297.5809949211119)
SITE = Polygon([A, B, C, D])
TOTAL = SITE.area

# ---------------------------------------------------------------- municipality cut (10 %) at the narrow east end
def east_slice(d):
    return Polygon([(B[0]-d, 0), (B[0]+50, 0), (C[0]+50, -400), (C[0]-d-19.01/148.79*251.2, -400)]).intersection(SITE)
lo, hi = 1, 400
for _ in range(80):
    mid = (lo+hi)/2
    if east_slice(mid).area < 0.10*TOTAL: lo = mid
    else: hi = mid
MUNI = east_slice(lo)
R = SITE.difference(MUNI)
RING_W, SPINE = 12.0, (-62.0, -82.0)
INNER = R.buffer(-RING_W, join_style=2)
RING = R.difference(INNER)

# frame along the south edge
ux, uy = (C[0]-D[0]), (C[1]-D[1]); L = math.hypot(ux, uy); ux, uy = ux/L, uy/L
nx, ny = -uy, ux                      # normal pointing into the site
cosA = ux
def ysouth_inner(x):                   # y of inner south road edge at x
    return D[1] + (x-D[0])*uy/ux + RING_W/cosA
O = (D[0] + RING_W*nx, D[1] + RING_W*ny)   # point on the inner south edge line
def srect(s0, s1, t0, t1):
    P = lambda s, t: (O[0]+s*ux+t*nx, O[1]+s*uy+t*ny)
    return Polygon([P(s0, t0), P(s1, t0), P(s1, t1), P(s0, t1)])
def s_of_x(x):                         # s along south edge for a point on the inner edge at x
    return (x-O[0])/ux

feat = {k: [] for k in ['villa', 'house', 'serv', 'util', 'tower', 'plaza', 'green', 'road', 'park_lot']}
labels = []   # (x, y, text_en, text_ar, size)
def add(kind, poly, en=None, ar=None, size=7):
    feat[kind].append(poly)
    if en or ar:
        c = poly.representative_point() if poly.geom_type != 'Polygon' or not poly.is_valid else poly.centroid
        labels.append((c.x, c.y, en, ar, size, kind))

# ---------------------------------------------------------------- roads
SPINE_P = INNER.intersection(box(-50, SPINE[1], 1000, SPINE[0]))
X_MAIN = 330.0                          # main street (gate -> roundabout)
MAIN_ST = INNER.intersection(box(X_MAIN-10, SPINE[0], X_MAIN+10, 1))
RB = Point(X_MAIN, sum(SPINE)/2).buffer(19)
roads = [RING, SPINE_P, MAIN_ST, RB]

# ---------------------------------------------------------------- north band: villas back-to-back 16 x 25
NB = INNER.intersection(box(-50, SPINE[0], 1000, -RING_W))
gardens_main = []
nv = 0
for row, (y0, y1) in enumerate([(-37, -12), (-62, -37)]):
    x = 0.0
    while x < 900:
        if X_MAIN-24 < x+16 and x < X_MAIN+24:        # main street + entrance gardens
            x = X_MAIN+24; continue
        p = box(x, y0, x+16, y1)
        if NB.contains(p):
            nv += 1; add('villa', p); labels.append((x+8, (y0+y1)/2, f'V{nv}', None, 3.2, 'no'))
        x += 16 if NB.contains(p) else 1
# leftovers of the north band -> green
nb_left = NB.difference(unary_union(feat['villa'] + [MAIN_ST]))
for g in getattr(nb_left, 'geoms', [nb_left]):
    if g.area > 60: add('green', g)

# ---------------------------------------------------------------- west civic zone (south band, x < XW)
XW = 300.0
SB = INNER.intersection(box(-50, -400, 1000, SPINE[1]))
WZ = SB.intersection(box(-50, -400, XW, SPINE[1]))
T1 = -147.0                                           # depth of spine-front tier
xw0 = 12 + RING_W/297.58*0 + (38.02/297.58)*(-T1) + 13   # inner west edge at tier bottom (approx)
west_x = lambda y: (-y)*38.02/297.58 + RING_W*1.009
# tier 1 (fronting the spine)
x0 = west_x(T1)
civ = [('SECONDARY SCHOOL', 'الثانوية', x0, x0+77, 'serv'),
       ('PRIMARY SCHOOL', 'الابتدائية', x0+77+4, x0+77+4+46, 'serv')]
for en, ar, a, b, k in civ:
    p = WZ.intersection(box(min(a, west_x(SPINE[1])) if a == x0 else a, T1, b, SPINE[1]))
    add(k, p, f'{en}\n{p.area:,.0f} m2', ar, 6)
xt0 = x0+77+4+46+4
TOWER_ZONE = WZ.intersection(box(xt0, T1, XW, SPINE[1]))
add('plaza', TOWER_ZONE)
tw = 31.0
towers = []
ntow = 3
gap = ((XW-xt0) - ntow*tw)/(ntow+1)
for i in range(ntow):
    tx = xt0 + gap + i*(tw+gap)
    t = box(tx, -95, tx+tw, -95-tw)
    towers.append(t); add('tower', t, f'TOWER {"ABC"[i]}\n120 flats', f'برج {"أبج"[i]}', 5)
# tier 3 (fronting the south road, rotated to the road)
s_w = s_of_x(west_x(-250)) + 4
T3 = 42.0
south_list = [('WATER', 'محطة الماء', 1000, 'util'), ('POWER', 'محطة الكهرباء', 1000, 'util'),
              ('WASTE', 'النفايات', 300, 'util'), ('CIVIL DEFENCE', 'الدفاع المدني', 600, 'serv'),
              ('POLICE', 'الشرطة', 600, 'serv'), ('HEALTH CENTRE', 'المركز الصحي', 1000, 'serv'),
              ('MOSQUE', 'الجامع', 2000, 'serv'), ('KINDERGARTEN', 'الروضة', 1500, 'serv')]
s = s_w
SERVICE_GATE_S = None
for en, ar, area, k in south_list:
    w = area/T3
    p = srect(s, s+w, 0, T3)
    if en == 'POLICE':
        SERVICE_GATE_S = s - 3
    if area >= 1000: add(k, p, f'{en}\n{area:,} m2', ar, 5)
    else: add(k, p, f'{area}', ar, 2.5)
    s += w + 3
s_end_w = s
# mall at the roundabout (spine front, east of the tower plaza is the roundabout; mall south of tier1 next to road)
# park = rest of west zone
used = unary_union(feat['serv'] + feat['util'] + [TOWER_ZONE])
# mall + parking: corner block at x XW-..XW below tier 1
MALL = WZ.intersection(box(XW-85, T1-4-60, XW, T1-4))
MALL_P = MALL.intersection(box(XW-85, T1-4-60, XW-85+50, T1-4))
add('serv', MALL_P, 'MALL\n%d m2' % MALL_P.area, 'المول', 6)
PARK_LOT = MALL.difference(MALL_P)
add('park_lot', PARK_LOT, 'PARKING', 'موقف', 4)
# service lane from the south road to the mall/park is NOT added (mall fronts the connector below)
park = WZ.difference(unary_union(feat['serv'] + feat['util'] + [TOWER_ZONE, MALL]))
for g in getattr(park, 'geoms', [park]):
    if g.area > 300:
        add('green', g, 'CENTRAL PARK\n%d m2' % g.area if g.area > 5000 else None,
            'الحديقة المركزية' if g.area > 5000 else None, 7)

# ---------------------------------------------------------------- residential south band (x >= XW)
RZ = SB.intersection(box(XW, -400, 1000, SPINE[1]))
# connector street on the civic/residential seam (also serves the mall) and inner lane loop
LANE = (-122.0, -130.0)
CONN_W = INNER.intersection(box(XW, -400, XW+8, SPINE[1]))   # west connector spine <-> south road
# east end of lane: where row D (lane-20) still leaves >= 8 m green above row B
xe = None
for x in range(int(XW), 900):
    if ysouth_inner(x) + 20/cosA > LANE[1]-20-8:
        xe = x; break
CONN_E = INNER.intersection(box(xe-8, LANE[1], xe, SPINE[1]))
LANE_P = INNER.intersection(box(XW, LANE[1], xe, LANE[0]))
roads += [CONN_W, CONN_E, LANE_P]
road_u = unary_union(roads)
nh = 0
def place_row(y0, y1, xa, xb):
    global nh
    x = xa
    while x + 12 <= xb + 1e-6:
        p = box(x, y0, x+12, y1)
        if RZ.contains(p) and not p.intersects(road_u.buffer(-0.01)):
            nh += 1; add('house', p); labels.append((x+6, (y0+y1)/2, f'H{nh}', None, 3, 'no')); x += 12
        else:
            x += 1
place_row(-102, -82, XW+8, 900)                       # row A on the spine
place_row(-122, -102, XW+8, xe-8)                     # row C on the lane (back to A)
place_row(-150, -130, XW+8, xe)                       # row D on the lane
# row B on the south road (rotated)
s = s_of_x(XW+8) + 0.5
while s < 1000:
    p = srect(s, s+12, 0, 20)
    if RZ.contains(p) and not p.intersects(road_u.buffer(-0.01)):
        nh += 1; add('house', p); c = p.centroid; labels.append((c.x, c.y, f'H{nh}', None, 3, 'no')); s += 12
    else:
        s += 1
        if s > s_of_x(900): break
res_left = RZ.difference(unary_union(feat['house'] + roads))
for g in getattr(res_left, 'geoms', [res_left]):
    if g.area > 80:
        add('green', g, 'LINEAR PARK\n%d m2' % g.area if g.area > 4000 else None,
            'الحديقة الطولية' if g.area > 4000 else None, 6)

# ---------------------------------------------------------------- numbers
FLATS = ntow*20*6
area = lambda k: sum(p.area for p in feat[k])
road_area = unary_union(roads).intersection(R).area
tbl = [('Villas 400 m2 (%d)' % nv, 'فلل 400 م٢', area('villa')),
       ('Houses 240 m2 (%d)' % nh, 'دور 240 م٢', area('house')),
       ('Towers (%d) + plaza' % ntow, 'الأبراج والساحة', area('plaza')),
       ('Community services', 'الخدمات', area('serv')),
       ('Utilities', 'المرافق الفنية', area('util')),
       ('Gardens + parks', 'الحدائق', area('green')),
       ('Parking (mall)', 'موقف المول', area('park_lot')),
       ('Roads', 'الشوارع', road_area)]
summ = sum(t[2] for t in tbl)
info = dict(total_site=TOTAL, municipality=MUNI.area, net=R.area, villas=nv, houses=nh, flats=FLATS,
            units=nv+nh+FLATS, table=[(a, round(c), round(100*c/R.area, 1)) for a, b, c in tbl], check=summ,
            muni_cut_m=lo)
print(json.dumps(info, indent=1, ensure_ascii=False))
json.dump(info, open(f'{OUT}/summary.json', 'w'), indent=1, ensure_ascii=False)

GATE_MAIN = (X_MAIN, 0.0)
xs = O[0] + (SERVICE_GATE_S or 0)*ux; GATE_SERV = (xs, D[1] + (xs-D[0])*uy/ux)

# ---------------------------------------------------------------- DXF
doc = ezdxf.new('R2010', setup=True); doc.units = 6
msp = doc.modelspace()
COL = dict(villa=(247, 214, 120), house=(240, 150, 50), serv=(222, 50, 46), util=(230, 120, 200),
           tower=(40, 120, 200), plaza=(170, 215, 240), green=(80, 175, 70), road=(205, 205, 205),
           park_lot=(150, 150, 150), muni=(185, 185, 215))
LAY = dict(villa='MP_PLOT_VILLA', house='MP_PLOT_HOUSE', serv='MP_SERVICES', util='MP_UTILITIES',
           tower='MP_TOWERS', plaza='MP_PLAZA', green='MP_GREEN', road='MP_ROADS', park_lot='MP_PARKING',
           muni='MP_MUNICIPALITY')
for k, l in LAY.items():
    doc.layers.add(l); doc.layers.add('MP_HATCH_'+k.upper())
for l in ['MP_BOUNDARY', 'MP_TEXT', 'MP_GATES', 'MP_TABLE', 'MP_TREES']: doc.layers.add(l)
def polys(g): return getattr(g, 'geoms', [g]) if not g.is_empty else []
def dxf_poly(g, k):
    for p in polys(g):
        if p.geom_type != 'Polygon': continue
        pts = list(p.exterior.coords)[:-1]
        msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': LAY[k]})
        h = msp.add_hatch(dxfattribs={'layer': 'MP_HATCH_'+k.upper()}); h.rgb = COL[k]
        h.paths.add_polyline_path(pts, is_closed=True)
        for i in p.interiors: h.paths.add_polyline_path(list(i.coords)[:-1], is_closed=True)
dxf_poly(unary_union(roads).intersection(R), 'road')
dxf_poly(MUNI, 'muni')
for k in ['green', 'plaza', 'park_lot', 'util', 'serv', 'tower', 'house', 'villa']:
    for p in feat[k]: dxf_poly(p, k)
msp.add_lwpolyline(list(SITE.exterior.coords), close=True, dxfattribs={'layer': 'MP_BOUNDARY', 'color': 6, 'const_width': 0.8})
msp.add_lwpolyline(list(R.exterior.coords), close=True, dxfattribs={'layer': 'MP_BOUNDARY', 'color': 1})
for x, y, en, ar, sz, k in labels:
    if en: msp.add_text(en.replace('\n', ' '), height=sz*0.5 if k == 'no' else sz*0.45,
                        dxfattribs={'layer': 'MP_TEXT'}).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)
m = MUNI.centroid
msp.add_text('MUNICIPALITY 10%% - %d m2' % MUNI.area, height=4, dxfattribs={'layer': 'MP_TEXT'}).set_placement((m.x, m.y), align=TextEntityAlignment.MIDDLE_CENTER)
for (gx, gy), t in [(GATE_MAIN, 'MAIN GATE'), (GATE_SERV, 'SERVICE GATE')]:
    msp.add_circle((gx, gy), 6, dxfattribs={'layer': 'MP_GATES', 'color': 1})
    msp.add_text(t, height=4, dxfattribs={'layer': 'MP_GATES', 'color': 1}).set_placement((gx, gy+(10 if gy > -5 else -10)), align=TextEntityAlignment.MIDDLE_CENTER)
ty = 60
for i, line in enumerate(['SHALLALAT - IBRAHIM PROPOSAL ON NEW BOUNDARY (10% MUNICIPALITY DEDUCTED)',
                          'UNITS: %d villas + %d houses + %d flats = %d' % (nv, nh, FLATS, nv+nh+FLATS)] +
                         ['%-28s %9s %6s' % (a, f'{c:,.0f}', f'{100*c/R.area:.1f}') for a, b, c in tbl] +
                         ['NET SITE %s m2 / MUNICIPALITY %s m2 / ORIGINAL %s m2' % (f'{R.area:,.0f}', f'{MUNI.area:,.0f}', f'{TOTAL:,.0f}')]):
    msp.add_text(line, height=4, dxfattribs={'layer': 'MP_TABLE'}).set_placement((0, ty+14*7 - i*7))
doc.saveas(f'{OUT}/SHALLALAT_MASTERPLAN_IBRAHIM_NEW_BOUNDARY.dxf')

# ---------------------------------------------------------------- preview PNG / PDF
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, Patch
import arabic_reshaper
from bidi.algorithm import get_display
FD = '/mnt/project-files/shallalat/03_archive/fonts/'
fm.fontManager.addfont(FD+'NotoSansArabic-Bold.ttf')
AR = fm.FontProperties(fname=FD+'NotoSansArabic-Bold.ttf')
ar = lambda t: t
plt.rcParams['font.family'] = ['Noto Sans Arabic', 'DejaVu Sans']
AR = fm.FontProperties(family=['Noto Sans Arabic', 'DejaVu Sans'], weight='bold')
hexc = lambda k: '#%02x%02x%02x' % COL[k]
fig = plt.figure(figsize=(30, 17)); ax = fig.add_axes([0.01, 0.27, 0.98, 0.72])
def draw(g, k, ec='#555', lw=0.4, alpha=1, hatch=None):
    for p in polys(g):
        if p.geom_type != 'Polygon': continue
        ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=hexc(k), ec=ec, lw=lw, alpha=alpha, hatch=hatch))
draw(unary_union(roads).intersection(R), 'road', ec='#999')
draw(MUNI, 'muni', ec='#6a4c93', lw=1.5, hatch='//')
for k in ['green', 'plaza', 'park_lot', 'util', 'serv', 'tower', 'house', 'villa']:
    for p in feat[k]: draw(p, k, ec={'villa': '#b07a10', 'house': '#a85a00'}.get(k, '#333'), lw=0.6)
# trees along roads and in parks (simple)
for g in feat['green']:
    if g.area > 1500:
        minx, miny, maxx, maxy = g.bounds
        yy = miny + 6
        while yy < maxy:
            xx = minx + 6
            while xx < maxx:
                if g.buffer(-3).contains(Point(xx, yy)): ax.add_patch(plt.Circle((xx, yy), 2.2, fc='#2e7d32', ec='none'))
                xx += 14
            yy += 14
for x in range(10, 900, 14):
    for y in [-6, -72]:
        if R.buffer(-2).contains(Point(x, y)) and not MAIN_ST.contains(Point(x, y)) and not RB.contains(Point(x, y)):
            pass
ax.add_patch(plt.Circle((X_MAIN, sum(SPINE)/2), 9, fc=hexc('green'), ec='#333'))
ax.plot(*SITE.exterior.xy, color='#c2185b', lw=2.5)
ax.plot(*R.exterior.xy, color='#d32f2f', lw=1.2, ls='--')
for x, y, en, a, sz, k in labels:
    if k == 'no':
        ax.text(x, y, en, ha='center', va='center', fontsize=4.3, color='#3a2a00'); continue
    t = (ar(a) + '\n' if a else '') + (en or '')
    ax.text(x, y, t, ha='center', va='center', fontproperties=AR, color='white' if k in ('serv', 'tower', 'util', 'green') else 'black',
            size=sz+5)
ax.text(m.x, m.y, ar('مساحة البلدية (10٪)') + '\nMUNICIPALITY 10%%\n%s m2' % f'{MUNI.area:,.0f}', ha='center', va='center',
        fontproperties=AR, size=15, color='#3b1f66', bbox=dict(fc='white', ec='#6a4c93', lw=2))
for (gx, gy), en, a, dy in [(GATE_MAIN, 'MAIN GATE', 'البوابة الرئيسية', 22), (GATE_SERV, 'SERVICE GATE', 'بوابة الخدمة', -24)]:
    ax.annotate('', xy=(gx, gy), xytext=(gx, gy+dy), arrowprops=dict(arrowstyle='simple', fc='#d50000', ec='#d50000', lw=1, mutation_scale=45))
    ax.text(gx, gy+dy*1.55, ar(a) + '  ' + en, ha='center', va='center', fontproperties=AR, size=17, color='#d50000',
            bbox=dict(fc='white', ec='#d50000', lw=2.5, boxstyle='round,pad=0.3'))
ax.text(450, 12, ar('الشارع الحولي يحيط بالموقع') , ha='center', fontproperties=AR, size=11, color='#555')
ax.text(640, -72, ar('الشارع الرئيسي') + '  MAIN STREET 20 m', ha='center', va='center', fontproperties=AR, size=11, color='#333')
ax.set_xlim(-20, 920); ax.set_ylim(-345, 55); ax.set_aspect('equal'); ax.axis('off')
ax.annotate('N', xy=(880, 45), xytext=(880, 15), ha='center', fontsize=22, fontweight='bold', arrowprops=dict(arrowstyle='-|>', lw=3, color='k'))
ax.text(420, 50, ar('مقترح ابراهيم المطور على حدود الموقع الجديدة - بعد استقطاع 10٪ للبلدية'), fontproperties=AR, size=22, va='top')
# legend + units box + land use table (inside the image)
legend = [Patch(fc=hexc(k), ec='#333', label=ar(a) + '  ' + e) for k, e, a in
          [('villa', 'Villas 400 m2', 'فلل'), ('house', 'Houses 240 m2', 'دور'), ('tower', 'Towers', 'أبراج'),
           ('plaza', 'Tower plaza', 'ساحة الأبراج'), ('serv', 'Services', 'خدمات'), ('util', 'Utilities', 'مرافق فنية'),
           ('green', 'Gardens', 'حدائق'), ('road', 'Roads', 'شوارع'), ('park_lot', 'Parking', 'مواقف'), ('muni', 'Municipality 10%', 'البلدية')]]
fig.legend(handles=legend, loc='lower left', bbox_to_anchor=(0.01, 0.01), ncol=2, prop=fm.FontProperties(family=['Noto Sans Arabic', 'DejaVu Sans'], weight='bold', size=15), frameon=True, title='LEGEND', title_fontsize=16)
ub = (ar('عدد الوحدات السكنية') + '\n' + ar('فلل') + f'  {nv}\n' + ar('دور') + f'  {nh}\n' + ar('شقق') + f'  {FLATS}\n' +
      ar('المجموع') + f'  {nv+nh+FLATS}')
fig.text(0.35, 0.03, ub, fontproperties=AR, size=21, va='bottom', bbox=dict(fc='#fff8e1', ec='#e65100', lw=3, boxstyle='round,pad=0.6'))
rows = '\n'.join(f'{ar(b)}  {c:>9,.0f}  {100*c/R.area:5.1f}%' for a, b, c in tbl)
fig.text(0.52, 0.02, ar('استعمالات الأرض (م٢ / ٪ من الصافي)') + '\n' + rows + '\n' + ar('الصافي') + f'  {R.area:,.0f}\n' +
         ar('البلدية') + f'  {MUNI.area:,.0f}   ' + ar('الأصلي') + f'  {TOTAL:,.0f}', fontproperties=AR, size=14, va='bottom',
         bbox=dict(fc='white', ec='#333', lw=2, boxstyle='round,pad=0.5'))
fig.savefig(f'{OUT}/SHALLALAT_MASTERPLAN_IBRAHIM_NEW_BOUNDARY.png', dpi=110, facecolor='white')
fig.savefig(f'{OUT}/SHALLALAT_MASTERPLAN_IBRAHIM_NEW_BOUNDARY.pdf', facecolor='white')
