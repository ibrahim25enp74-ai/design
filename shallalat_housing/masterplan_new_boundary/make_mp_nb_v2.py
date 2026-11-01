# Shallalat - Ibrahim's ORIGINAL layout form (slanted double-row blocks + green strips, central spine with
# roundabouts, services at the central roundabout, towers at the narrow east tip, civic/utility zone at the
# wide west end) re-fitted on the NEW boundary minus 10 % for the municipality (taken at the west end).
# Work in sheared coordinates (s, y): s = x + K*y makes the west edge vertical; blocks are axis-aligned there
# and become parallelograms (like Ibrahim's slanted blocks) in the real frame. Shear keeps areas.
import math, json, sys
import ezdxf
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from shapely import affinity

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
A, B = (0.0, 0.0), (900.0, 0.0)
C, D = (880.9897957549033, -148.79049746055594), (38.02040849019346, -297.5809949211119)
SITE = Polygon([A, B, C, D]); TOTAL = SITE.area
K = D[0]/(-D[1])                                   # 0.1278
COSK = 1/math.hypot(1, K)
toXY = lambda g: affinity.affine_transform(g, [1, K, 0, 1, 0, 0])     # x = s + K*(y) ... see below
# s = x + K*y  ->  x = s - K*y
toXY = lambda g: affinity.affine_transform(g, [1, -K, 0, 1, 0, 0])
toSY = lambda g: affinity.affine_transform(g, [1, K, 0, 1, 0, 0])
SITE_S = toSY(SITE)

# ---- municipality: west slice (vertical in s) = 10 %
lo, hi = 1.0, 200.0
for _ in range(80):
    mid = (lo+hi)/2
    if SITE_S.intersection(box(-50, -400, mid, 10)).area < 0.10*TOTAL: lo = mid
    else: hi = mid
S0 = lo
MUNI_S = SITE_S.intersection(box(-50, -400, S0, 10))
R_S = SITE_S.difference(MUNI_S)
RW = 12.0
INNER_XY = toXY(R_S).buffer(-RW, join_style=2)
INNER = toSY(INNER_XY)
RING_S = R_S.difference(INNER)
ys_edge = lambda s: D[1] + s*(C[1]-D[1])/(C[0]+K*C[1]-0.0)     # south edge y at s (sheared)
s_C = C[0] + K*C[1]
ys_edge = lambda s: D[1] + s*(C[1]-D[1])/s_C
yc = lambda s: ys_edge(s)/2                                      # spine centre line
SPW = 20.0
si0 = S0 + RW/COSK                                               # inner west edge (s)
s_east = 900 - 3                                                 # approx inner east (top)

feat = {k: [] for k in ['villa', 'house', 'serv', 'util', 'tower', 'plaza', 'green', 'road', 'park_lot']}
labels = []
def add(kind, poly_s, en=None, ar=None, size=7, sheared=True):
    p = toXY(poly_s) if sheared else poly_s
    feat[kind].append(p)
    if en or ar:
        c = p.representative_point()
        labels.append((c.x, c.y, en, ar, size, kind))
    return p

# ---- spine (sheared band following the centre line) + main street + roundabouts
def band(s0, s1, f_top, f_bot, n=40):
    pts = [(s0 + (s1-s0)*i/n, f_top(s0 + (s1-s0)*i/n)) for i in range(n+1)]
    pts += [(s1 - (s1-s0)*i/n, f_bot(s1 - (s1-s0)*i/n)) for i in range(n+1)]
    return Polygon(pts)
SPINE_S = band(-50, 1000, lambda s: yc(s)+SPW/2, lambda s: yc(s)-SPW/2).intersection(INNER)
S_MAIN = 470.0                                                  # main street / central roundabout
MAIN_S = INNER.intersection(box(S_MAIN-10, yc(S_MAIN), S_MAIN+10, 5))
S_RB2 = 700.0
RB = toXY(Point(S_MAIN, yc(S_MAIN))).buffer(19)
RB2 = toXY(Point(S_RB2, yc(S_RB2))).buffer(13)
roads_s = [RING_S, SPINE_S, MAIN_S]
north_lim = lambda s: (-RW, yc(s)+SPW/2)           # top, bottom of north half
south_lim = lambda s: (yc(s)-SPW/2, None)

def half_rect(s0, s1, half, d0=0, d1=None):
    """rectangle in s between s0,s1 in one half; d measured from the spine edge outward"""
    if half == 'N':
        yb = max(yc(s0), yc(s1)) + SPW/2
        y0 = yb + d0; y1 = 5 if d1 is None else yb + d1
        return INNER.intersection(box(s0, y0, s1, y1))
    yt = min(yc(s0), yc(s1)) - SPW/2
    y1 = yt - d0; y0 = -400 if d1 is None else yt - d1
    return INNER.intersection(box(s0, y0, s1, y1))

# ---- WEST civic / utility zone
WZ_W = 50.0
sW1 = si0 + WZ_W
sec = half_rect(si0, sW1, 'N')
add('serv', sec, 'SECONDARY\n%d m2' % sec.area, 'الثانوية', 5)
s = si0; yt = min(yc(si0), yc(sW1)) - SPW/2
south_w = [('WATER', 'محطة الماء', 1000, 'util'), ('POWER', 'محطة الكهرباء', 1000, 'util'), ('WASTE', 'النفايات', 300, 'util'),
           ('POLICE', 'الشرطة', 600, 'serv'), ('CIVIL DEF.', 'الدفاع المدني', 600, 'serv')]
# stack from the south road upward (each full zone width)
ybot = ys_edge(sW1) + RW
y = ybot
for en, ar, area, k in south_w:
    h = area/WZ_W
    p = INNER.intersection(box(si0, y, sW1, y+h))
    if area >= 1000: add(k, p, f'{en}\n{area:,} m2', ar, 4.5)
    else: add(k, p, f'{area}', ar, 2.5)
    y += h
wg = INNER.intersection(box(si0, y, sW1, yt))
add('green', wg)
GATE_SERV_S = (si0 + WZ_W/2, ys_edge(si0 + WZ_W/2))

# ---- block generator: [row | lane | row] blocks separated by green strips, both halves
LANE, G = 8.0, 14.0
VIL = (25.0/COSK, 16.0*COSK)          # (s-width, y-height) parallelogram = 400 m2
HOU = (20.0/COSK, 12.0*COSK)          # 240 m2
cnt = {'villa': 0, 'house': 0}
def zone_blocks(sa, sb, kind, lead_green=True):
    pw, ph = VIL if kind == 'villa' else HOU
    bw = 2*pw + LANE
    s = sa
    if lead_green:
        s += G
    blocks = []
    while s + bw <= sb + 1e-6:
        blocks.append(s); s += bw + G
    # spread leftover into the green strips
    left = sb - (blocks[-1] + bw) if blocks else 0
    extra = left/(len(blocks) + (1 if lead_green else 0)) if blocks else 0
    pos = []
    s = sa + ((G + extra) if lead_green else 0)
    for i in range(len(blocks)):
        pos.append(s); s += bw + G + extra
    for s0 in pos:
        roads_s.append(INNER.intersection(box(s0+pw, -400, s0+pw+LANE, 5)).difference(SPINE_S))
        for half in 'NS':
            for col in (s0, s0+pw+LANE):
                if half == 'N':
                    y = max(yc(col), yc(col+pw)) + SPW/2
                    while True:
                        p = box(col, y, col+pw, y+ph)
                        if not INNER.contains(p): break
                        cnt[kind] += 1; tag = ('V' if kind == 'villa' else 'H') + str(cnt[kind])
                        q = add(kind, p); c = q.centroid; labels.append((c.x, c.y, tag, None, 3, 'no')); y += ph
                else:
                    y = min(yc(col), yc(col+pw)) - SPW/2
                    while True:
                        p = box(col, y-ph, col+pw, y)
                        if not INNER.contains(p): break
                        cnt[kind] += 1; tag = ('V' if kind == 'villa' else 'H') + str(cnt[kind])
                        q = add(kind, p); c = q.centroid; labels.append((c.x, c.y, tag, None, 3, 'no')); y -= ph
    return pos

# zones along s
C0, C1 = S_MAIN - 100, S_MAIN + 80                                 # central services zone
T0 = 805.0                                                       # tower tip
zone_blocks(sW1, C0, 'villa', lead_green=False)
zone_blocks(C1, T0, 'house', lead_green=True)

# ---- CENTRAL services around the roundabout
mall = half_rect(C0+G, C0+G+38, 'N', 0, 80); add('serv', mall, 'MALL\n%d m2' % mall.area, 'المول', 5)
park = half_rect(C0+G+38+3, S_MAIN-10, 'N', 0, 60); add('park_lot', park, 'PARKING', 'موقف', 3.5)
hlt = half_rect(S_MAIN+10, S_MAIN+10+22, 'N', 0, 46); add('serv', hlt, 'HEALTH\n%d m2' % hlt.area, 'المركز الصحي', 4)
mos = half_rect(C0+G, C0+G+30, 'S', 0, 68); add('serv', mos, 'MOSQUE\n%d m2' % mos.area, 'الجامع', 4.5)
kg = half_rect(C0+G+30+4, S_MAIN+12, 'S', 0, 50); add('serv', kg, 'KG\n%d m2' % kg.area, 'الروضة', 4.5)
pri = half_rect(S_MAIN+16, S_MAIN+16+44, 'S', 0, 70); add('serv', pri, 'PRIMARY\n%d m2' % pri.area, 'الابتدائية', 4.5)

# ---- TOWER tip
TZ = INNER.intersection(box(T0, -400, 1000, 5))
tz_xy = add('plaza', TZ)
ntow = 3
c = tz_xy.centroid; minx, miny, maxx, maxy = tz_xy.bounds
for i, dy in enumerate([44, 0, -44]):
    t = Point(c.x-K*dy-4, c.y+dy).buffer(16.5, cap_style=3)
    feat['tower'].append(t); labels.append((t.centroid.x, t.centroid.y, f'TOWER {"ABC"[i]}\n120 flats', f'برج {"أبج"[i]}', 4, 'tower'))

# ---- greens = everything left in the inner area
built = unary_union([toXY(g) for g in roads_s] + feat['villa'] + feat['house'] + feat['serv'] + feat['util'] + feat['park_lot'] + [tz_xy])
rest = INNER_XY.difference(built)
for g in getattr(rest, 'geoms', [rest]):
    if g.area > 40:
        add('green', g, sheared=False)

print('lanes', sum(g.area for g in roads_s[3:]))
R = toXY(R_S); MUNI = toXY(MUNI_S)
roads = [toXY(g) for g in roads_s] + [RB, RB2]
nv, nh = cnt['villa'], cnt['house']
FLATS = ntow*20*6
GATE_MAIN = (S_MAIN - K*0, 0.0)
gx = GATE_SERV_S[0] - K*GATE_SERV_S[1]; GATE_SERV = (gx, GATE_SERV_S[1])
X_MAIN = S_MAIN - K*yc(S_MAIN); SPINE = (yc(S_MAIN)+10, yc(S_MAIN)-10)
RBc = (X_MAIN, yc(S_MAIN))

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
for i, line in enumerate(['SHALLALAT - IBRAHIM ORIGINAL LAYOUT ON NEW BOUNDARY (10% MUNICIPALITY DEDUCTED)',
                          'UNITS: %d villas + %d houses + %d flats = %d' % (nv, nh, FLATS, nv+nh+FLATS)] +
                         ['%-28s %9s %6s' % (a, f'{c:,.0f}', f'{100*c/R.area:.1f}') for a, b, c in tbl] +
                         ['NET SITE %s m2 / MUNICIPALITY %s m2 / ORIGINAL %s m2' % (f'{R.area:,.0f}', f'{MUNI.area:,.0f}', f'{TOTAL:,.0f}')]):
    msp.add_text(line, height=4, dxfattribs={'layer': 'MP_TABLE'}).set_placement((0, ty+14*7 - i*7))
doc.saveas(f'{OUT}/SHALLALAT_MASTERPLAN_IBRAHIM_NEW_BOUNDARY_V2.dxf')

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
        if R.buffer(-2).contains(Point(x, y)) :
            pass
ax.add_patch(plt.Circle(RBc, 9, fc=hexc('green'), ec='#333')); ax.add_patch(plt.Circle((S_RB2-K*yc(S_RB2), yc(S_RB2)), 6, fc=hexc('green'), ec='#333'))
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
ax.text(620, yc(620+K*yc(620))-14, ar('الشارع الرئيسي') + '  MAIN STREET 20 m', ha='center', va='center', fontproperties=AR, size=11, color='#333')
ax.set_xlim(-20, 920); ax.set_ylim(-345, 80); ax.set_aspect('equal'); ax.axis('off')
ax.annotate('N', xy=(880, 45), xytext=(880, 15), ha='center', fontsize=22, fontweight='bold', arrowprops=dict(arrowstyle='-|>', lw=3, color='k'))
ax.text(560, 75, ar('مقترح ابراهيم المطور (نفس التوزيع الأصلي) على الحدود الجديدة - بعد استقطاع 10٪ للبلدية'), fontproperties=AR, size=22, va='top')
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
fig.savefig(f'{OUT}/SHALLALAT_MASTERPLAN_IBRAHIM_NEW_BOUNDARY_V2.png', dpi=110, facecolor='white')
fig.savefig(f'{OUT}/SHALLALAT_MASTERPLAN_IBRAHIM_NEW_BOUNDARY_V2.pdf', facecolor='white')
