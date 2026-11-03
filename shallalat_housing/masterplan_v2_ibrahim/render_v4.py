# Presentation render of V2 (dark style of the reference board) + PREVIEW RULE content.
import sys, json, math, random, ezdxf
from ezdxf import colors
from shapely.geometry import Polygon, box, Point, LineString, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, Rectangle, Circle

DXF, DATA, OUT, FONT = sys.argv[1:5]
fm.fontManager.addfont(FONT); FAM = [fm.FontProperties(fname=FONT).get_name(), 'DejaVu Sans']
FP = fm.FontProperties(family=FAM, weight='bold')
doc = ezdxf.readfile(DXF); ms = doc.modelspace(); D = json.load(open(DATA))
site = Polygon([p[:2] for p in ms.query('LWPOLYLINE[layer=="MP_BOUNDARY"]')[0].get_points()])
S = site.area
CAT = {(244, 238, 81): 'villa', (248, 153, 30): 'house', (205, 32, 39): 'mall', (242, 113, 114): 'police',
       (247, 171, 174): 'cd', (169, 83, 160): 'health', (254, 204, 102): 'admin', (39, 118, 187): 'primary',
       (16, 86, 137): 'kg', (173, 221, 247): 'mosque', (34, 52, 110): 'secondary', (120, 186, 110): 'sports',
       (19, 103, 52): 'green', (46, 139, 87): 'tgarden', (43, 47, 58): 'tower', (233, 220, 192): 'plaza',
       (79, 179, 232): 'water', (185, 188, 194): 'park', (0, 0, 0): 'gate', (0, 166, 166): 'waterst', (242, 194, 0): 'power', (139, 107, 74): 'waste'}
geo, plots = {}, {'villa': [], 'house': []}
for h in ms.query('HATCH'):
    if not h.dxf.hasattr('true_color'): continue
    k = CAT.get(colors.int2rgb(h.dxf.true_color))
    if not k: continue
    for p in h.paths:
        try: v = [tuple(x[:2]) for x in p.vertices]
        except Exception: continue
        if len(v) < 3: continue
        P = Polygon(v).buffer(0)
        if k in plots and h.dxf.layer in ('MP4_VILLA','MP4_HOUSE'): plots[k].append(P)
        geo[k] = P if k not in geo else geo[k].union(P)
TZB = box(339690, 0, 1e7, 1e8)
geo['cpark'] = geo['park'].difference(TZB); geo['park'] = geo['park'].intersection(TZB)
geo['cplaza'] = geo['plaza'].difference(TZB); geo['plaza'] = geo['plaza'].intersection(TZB)
geo['green'] = geo['green'].difference(geo['cplaza'])
stalls = [Polygon([p[:2] for p in e.get_points()]) for e in ms.query('LWPOLYLINE') if e.dxf.layer.endswith('_PARKING')]
gates = [g for g in getattr(geo['gate'], 'geoms', [geo['gate']])]

# colours (reference board)
BG, ROAD, LINE = '#1c2023', '#34383d', '#f3f3f3'
C = dict(villa='#e8916b', house='#ecd5a0', green='#5c9a3a', tgarden='#4f8f35', mall='#f4b6c8', police='#7fa7e0',
         cd='#f59a62', health='#9fd3f0', admin='#f6d36b', primary='#6aa6e8', kg='#b79be6', mosque='#c9a6e8',
         secondary='#4f7fd6', sports='#3d8f3a', services='#f2c94c', tower='#2a2e36', plaza='#efe3c4',
         water='#5cc3f0', park='#8d9299', cpark='#8d9299', cplaza='#efe3c4', waterst='#43c6c6', power='#f5d33a', waste='#a8865f')
fig = plt.figure(figsize=(32, 20.5), dpi=100, facecolor=BG)
ax = fig.add_axes([0.0, 0.27, 1.0, 0.73]); ax.set_facecolor(BG); ax.set_aspect('equal'); ax.axis('off')
minx, miny, maxx, maxy = site.bounds
ax.set_xlim(minx-70, maxx+70); ax.set_ylim(miny-45, maxy+70)
random.seed(4)
# surroundings: dark farmland patches
for i in range(900):
    x = random.uniform(minx-90, maxx+90); y = random.uniform(miny-60, maxy+90)
    w, hh = random.uniform(12, 40), random.uniform(10, 30)
    r = box(x, y, x+w, y+hh)
    if r.intersects(site.buffer(8)): continue
    ax.add_patch(Rectangle((x, y), w, hh, fc=random.choice(['#2a3329', '#2f3a2c', '#263024', '#333b2f']), ec='none', zorder=0))
def fill(g, fc, ec='none', lw=0, z=2, alpha=1):
    for p in getattr(g, 'geoms', [g]):
        if p.is_empty or p.geom_type != 'Polygon': continue
        ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha))
        for r in p.interiors:
            ax.add_patch(MPoly(list(r.coords), closed=True, fc=ROAD, ec='none', zorder=z+0.01))
fill(site, ROAD, z=1)
ax.add_patch(MPoly(list(site.exterior.coords), closed=True, fc='none', ec='#7a8a5a', lw=2.5, ls=(0, (2, 2)), zorder=9))
# ring road + spine centre lines
ring = site.buffer(-7.5, join_style=2).intersection(box(339025, 0, 1e7, 1e8)).exterior
ax.plot(*ring.xy, color='#d8d8d8', lw=1.2, ls=(0, (6, 6)), zorder=3)
for xa, xb in ((339040, 339337), (339437, 339700)):
    ax.plot([xa, xb], [4033023, 4033023], color='#d8d8d8', lw=1.2, ls=(0, (6, 6)), zorder=3)
ax.plot([339387, 339387], [4033073, 4033143], color='#d8d8d8', lw=1.2, ls=(0, (6, 6)), zorder=3)
for xa, xb in ():
    for x in range(int(xa)+4, int(xb)-2, 9): ax.add_patch(Circle((x, 4033023), 1.7, fc='#3f7d2a', ec='#2f5f20', lw=0.6, zorder=4))
# perimeter trees
tline = site.buffer(-1.6).exterior
for i in range(0, int(tline.length), 9):
    p = tline.interpolate(i); ax.add_patch(Circle((p.x, p.y), 1.9, fc='#4f8f35', ec='#2f5f20', lw=0.6, zorder=8))
# civic + zones
for k in ('mall', 'police', 'cd', 'health', 'admin', 'primary', 'kg', 'mosque', 'secondary', 'waterst', 'power', 'waste', 'green', 'tgarden', 'plaza', 'cplaza', 'park', 'cpark'):
    fill(geo[k], C[k], ec='#1c2023', lw=1, z=2)
fill(geo['sports'], C['sports'], z=2)
# trees in parks (grid jitter)
for k in ('green', 'tgarden'):
    g = geo[k].buffer(-2.5)
    if g.is_empty: continue
    bx = g.bounds
    for x in range(int(bx[0]), int(bx[2]), 8):
        for y in range(int(bx[1]), int(bx[3]), 8):
            if random.random() < 0.45:
                q = Point(x+random.uniform(-2, 2), y+random.uniform(-2, 2))
                if g.contains(q): ax.add_patch(Circle((q.x, q.y), random.uniform(1.6, 2.6), fc=random.choice(['#3f7d2a', '#4a8a30', '#356b24']), ec='#2a5520', lw=0.5, zorder=4))
# paths in linear parks
for p in getattr(geo['green'], 'geoms', [geo['green']]):
    if p.area > 2500 and p.minimum_rotated_rectangle.area < 3*p.area:
        c = p.centroid; ax.add_patch(Circle((c.x, c.y), 5, fc='#d9c9a0', ec='none', zorder=4.5))
        ax.add_patch(Circle((c.x, c.y), 2.2, fc='#5cc3f0', ec='none', zorder=4.6))
# plots
for k in ('villa', 'house'):
    for p in plots[k]:
        fill(p, C[k], ec=LINE, lw=0.8, z=5)
        if k == 'villa':   # villa footprint (front 5, rear 3, sides 1.5) hint
            b = p.buffer(-2.2); fill(b, '#f6c3a8', ec='#b9674a', lw=0.5, z=5.2)
# block ids
def blocks(ps):
    u = unary_union([p.buffer(0.3) for p in ps]); return list(getattr(u, 'geoms', [u]))
bid = []
for k, pre in (('villa', 'V'), ('house', 'H')):
    bl = sorted(blocks(plots[k]), key=lambda g: (round(-g.centroid.y/60), g.centroid.x))
    for i, g in enumerate(bl, 1):
        c = g.representative_point(); n = sum(1 for p in plots[k] if g.contains(p.representative_point()))
        ax.text(c.x, c.y, f'{pre}{i}', ha='center', va='center', fontsize=8.5, color='#333', fontweight='bold', zorder=7,
                bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
        bid.append((f'{pre}{i}', n))
# sports details
pitch = box(338965, 4033015, 339005, 4033085)
fill(pitch, '#2f7d2c', ec='white', lw=1.6, z=6)
ax.plot([338965, 339005], [4033050, 4033050], color='white', lw=1.4, zorder=6.1)
ax.add_patch(Circle((338985, 4033050), 6, fc='none', ec='white', lw=1.4, zorder=6.1))
for yy, sgn in ((4033015, 1), (4033085, -1)):
    ax.add_patch(Rectangle((338977, yy if sgn > 0 else yy-8), 16, 8, fc='none', ec='white', lw=1.2, zorder=6.1))
for x0 in (338985, 339005):
    fill(box(x0, 4032966, x0+17, 4033002), '#c8643c', ec='white', lw=1.3, z=6)
    ax.plot([x0, x0+17], [4032984, 4032984], color='white', lw=1.2, zorder=6.1)
# building footprints inside civic plots
def bld(k, inset, fc, court=0):
    for p in getattr(geo[k], 'geoms', [geo[k]]):
        b = p.buffer(-inset, join_style=2)
        if b.is_empty: continue
        fill(b, fc, ec='#555', lw=0.8, z=6)
        if court:
            cc = b.buffer(-court, join_style=2)
            if not cc.is_empty: fill(cc, '#d9efd0', ec='#555', lw=0.6, z=6.1)
bld('mall', 6, '#fbe3ea'); bld('secondary', 7, '#dfe9fb', 8); bld('primary', 6, '#e3eefc', 7); bld('kg', 5, '#efe6fc', 6)
bld('health', 4, '#e8f6fd'); bld('police', 3, '#e6eefb'); bld('cd', 3, '#fde6d6'); bld('admin', 2.5, '#fdf1c9')
bld('mosque', 5, '#efe3fb')
m = geo['mosque'].centroid; ax.add_patch(Circle((m.x, m.y), 6, fc='#d8c2f0', ec='#6b4a9a', lw=1.2, zorder=6.3))
h = geo['health'].centroid; ax.add_patch(Rectangle((h.x-1.2, h.y-4), 2.4, 8, fc='#d22', zorder=6.4)); ax.add_patch(Rectangle((h.x-4, h.y-1.2), 8, 2.4, fc='#d22', zorder=6.4))
# towers, fountain, parking
for t in getattr(geo['tower'], 'geoms', [geo['tower']]):
    sh = affinity.translate(t, 4, -4); fill(sh, '#0d0f12', z=5.8, alpha=0.6)
    fill(t, C['tower'], ec='#9fd3f0', lw=1.5, z=6); fill(t.buffer(-6, join_style=2), '#3b414c', ec='#9fd3f0', lw=0.8, z=6.1)
    c = t.centroid; ax.add_patch(Rectangle((c.x-3.6, c.y-6.9), 7.2, 13.8, fc='#59606d', ec='none', zorder=6.2))
for f in getattr(geo['water'], 'geoms', [geo['water']]):
    f = f.centroid
    for r, fc in ((13, '#d9c9a0'), (11, '#5cc3f0'), (7, '#8fd8f6'), (4, '#5cc3f0'), (1.5, 'white')):
        ax.add_patch(Circle((f.x, f.y), r, fc=fc, ec='white' if r == 11 else 'none', lw=1, zorder=6.5))
    for a in range(0, 360, 45):
        import math as _m; ax.plot([f.x+14*_m.cos(_m.radians(a)), f.x+30*_m.cos(_m.radians(a))], [f.y+14*_m.sin(_m.radians(a)), f.y+30*_m.sin(_m.radians(a))], color='#d9c9a0', lw=3, zorder=4.8)
for s in stalls: fill(s, '#7d828a', ec='white', lw=0.5, z=6)
# gates
for i, g in enumerate(sorted(gates, key=lambda g: g.centroid.x), 1):
    c = g.centroid; fill(g, 'white', z=9)
    ax.add_patch(MPoly([(c.x-9, c.y+34), (c.x+9, c.y+34), (c.x, c.y+12)], closed=True, fc='white', ec='none', zorder=10))
    ax.text(c.x, c.y+48, f'البوابة الرئيسية {i}\nMAIN GATE {i}', ha='center', va='center', fontproperties=FP, fontsize=17, color='white', zorder=10)
# zone labels (name + area)
def lab(x, y, s, a=None, fs=12, fc='white', tc='#222'):
    t = s if a is None else f'{s}\n{a:,.0f} m²'
    ax.text(x, y, t, ha='center', va='center', fontproperties=FP, fontsize=fs, color=tc, zorder=11, linespacing=1.15,
            bbox=dict(boxstyle='round,pad=0.25', fc=fc, ec='#222', lw=0.8, alpha=0.93))
A = {k: g.intersection(site).area for k, g in geo.items()}
A['villa'] = sum(p.area for p in plots['villa']); A['house'] = sum(p.area for p in plots['house'])
A['towerzone'] = D['tower_zone']; A['garden'] = D['garden']
NAME = dict(mall='مول تجاري', police='مركز شرطة', cd='دفاع مدني', health='مركز صحي', admin='إدارة المجمع',
            primary='مدرسة ابتدائية', kg='روضة', mosque='جامع', secondary='مدرسة ثانوية', sports='ملاعب', waterst='محطة ماء', power='محطة كهرباء', waste='نفايات', cpark='مواقف')
for k in NAME:
    p = geo[k].representative_point(); fs = 9.5 if k in ('police', 'cd', 'health', 'admin') else 12
    for g in sorted(getattr(geo[k], 'geoms', [geo[k]]), key=lambda g: -g.area)[:2 if k == 'cpark' else 1]:
        p = g.representative_point(); dy = {'sports': -60, 'secondary': 10, 'primary': 8}.get(k, 0)
        lab(p.x, p.y+dy, NAME[k], g.area, 9 if k in ('police', 'cd', 'health', 'waste', 'power', 'waterst') else fs)
for L in D['labels']:
    if L.get('dark'): lab(L['x'], L['y'], L['t'], fs=11, fc='#2a2e36', tc='white')
    else: lab(L['x'], L['y'], L['t'], L.get('a'), fs=10, fc='#cfe8c4' if 'حديقة' in L['t'] or 'نافورة' in L['t'] else '#eeeeee')
lab(339757, 4032975, f'منطقة الأبراج {A["towerzone"]:,.0f} m²', fs=11, fc='#cfe8c4')
for z in D.get('zones', []): lab(z['x'], z['y'], f"{z['name']} ({z['n']})", z['area'], fs=11, fc='#fff7e0')

# site dimensions
pts = list(site.exterior.coords)[:-1]
for a, b in zip(pts, pts[1:]+pts[:1]):
    L = math.dist(a, b); mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2
    ang = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    nx, ny = -(b[1]-a[1])/L, (b[0]-a[0])/L
    ax.text(mx-nx*14, my-ny*14, f'{L:.1f} m', rotation=ang, ha='center', va='center', fontsize=13, color='#e0e0e0', zorder=10,
            bbox=dict(boxstyle='round,pad=0.2', fc=BG, ec='#888', lw=0.8))
# north + scale
ax.add_patch(Circle((minx-35, maxy+30), 16, fc='none', ec='white', lw=2, zorder=10))
ax.add_patch(MPoly([(minx-35, maxy+44), (minx-41, maxy+22), (minx-35, maxy+27), (minx-29, maxy+22)], fc='white', zorder=10))
ax.text(minx-35, maxy+53, 'N', color='white', fontsize=20, ha='center', fontweight='bold')
for i, (a, b) in enumerate(((0, 25), (25, 50), (50, 100))):
    ax.add_patch(Rectangle((minx+a, miny-35), b-a, 4, fc='white' if i % 2 == 0 else BG, ec='white', lw=1.2, zorder=10))
for v in (0, 25, 50, 100): ax.text(minx+v, miny-27, str(v), color='white', ha='center', fontsize=12)
ax.text(minx+108, miny-33, 'm', color='white', fontsize=12)

# ---------------- bottom panel
def T(axp, x, y, s, fs=14, c='white', ha='right', **kw):
    axp.text(x, y, s, ha=ha, va='center', fontproperties=FP, fontsize=fs, color=c, **kw)
p0 = fig.add_axes([0, 0, 1, 0.26]); p0.set_facecolor('#20252a'); p0.set_xlim(0, 320); p0.set_ylim(0, 100); p0.axis('off')
p0.add_patch(Rectangle((0, 0), 320, 100, fc='#20252a', zorder=0))
for x in (75, 175, 240): p0.plot([x, x], [6, 94], color='#555', lw=1)
T(p0, 72, 86, 'مجمع الشلالات السكني', 34); T(p0, 72, 74, 'المخطط الأساسي V4', 24, '#f2c94c')
T(p0, 4, 62, 'Shallalat Residential Compound - Master Plan V4', 17, '#ddd', ha='left')
T(p0, 4, 52, f'Site area: {S:,.0f} m²  ({S/1e4:.2f} ha)', 15, '#bbb', ha='left')
T(p0, 4, 43, f'{D["villas"]+D["houses"]+D["flats"]} units  •  2 gates  •  T-junctions  •  max 150 m between junctions', 13, '#bbb', ha='left')
T(p0, 72, 30, 'المدخل الوسطي: ساحة خدمات حول حديقة مركزية ونافورة', 14, '#9fd39a')
T(p0, 72, 20, 'الأبراج: نافورة وحدائق بينهما ومواقف على الجانبين', 14, '#9fd39a')
# land use table
T(p0, 172, 92, 'استعمالات الأرض  Land Use', 18)
rows = [('villa', 'فلل 400 م²', A['villa']), ('house', 'دور 250 م²', A['house']), ('tgarden', 'منطقة الأبراج', A['towerzone']),
        ('green', 'الحديقة المركزية', A['garden']), ('sports', 'ملاعب', A['sports']), ('mall', 'مول تجاري', A['mall']),
        ('secondary', 'مدرسة ثانوية', A['secondary']), ('primary', 'مدرسة ابتدائية', A['primary']), ('kg', 'روضة', A['kg']),
        ('mosque', 'جامع', A['mosque']), ('health', 'مركز صحي', A['health']), ('police', 'مركز شرطة', A['police']),
        ('cd', 'دفاع مدني', A['cd']), ('admin', 'إدارة المجمع', A['admin']), ('waterst', 'محطة ماء', A['waterst']), ('power', 'محطة كهرباء', A['power']), ('waste', 'نفايات', A['waste']), ('cpark', 'مواقف الخدمات', A['cpark'])]
used = sum(r[2] for r in rows); rows.append(('road', 'شوارع وأرصفة', S-used)); C['road'] = ROAD
for i, (k, n, a) in enumerate(rows):
    col, r = divmod(i, 10); x = 172 - col*49; y = 83 - r*8.4
    p0.add_patch(Rectangle((x-6, y-3), 6, 6, fc=C[k], ec='#999', lw=0.8))
    T(p0, x-8, y, n, 12.5); T(p0, x-27, y, f'{a:,.0f} m²', 12.5, '#ddd'); T(p0, x-40, y, f'{100*a/S:.1f}%', 12.5, '#f2c94c')
# road hierarchy + plot types
T(p0, 237, 92, 'تدرج الشوارع  Roads', 18)
for i, (n, w) in enumerate((('الشارع الرئيسي والمدخل الوسطي', '20 m'), ('الشارع الدائري المحيطي', '15 m'), ('الشوارع المحلية', '12 m'), ('تقاطعات T فقط، أقصى طول', '150 m'))):
    y = 82 - i*8.5; p0.add_patch(Rectangle((229, y-2), 8, 4, fc=ROAD, ec='#999')); T(p0, 227, y, n, 12.5); T(p0, 180, y, w, 13, '#f2c94c', ha='left')
T(p0, 237, 44, 'أنواع القطع  Plot types', 18)
for i, (k, n) in enumerate((('villa', f'فلل 16 × 25 = 400 م²  ({D["villas"]})'), ('house', f'دور 10 × 25 = 250 م²  ({D["houses"]})'),
                            ('tower', f'برجين × 114 شقة  ({D["flats"]})'))):
    y = 34 - i*9; p0.add_patch(Rectangle((229, y-2.5), 8, 5, fc=C[k], ec='#999')); T(p0, 227, y, n, 13)
# summary / units box
p0.add_patch(Rectangle((244, 8), 72, 86, fc='#2b3036', ec='#f2c94c', lw=2.5))
T(p0, 312, 86, 'عدد الوحدات  Units', 20, '#f2c94c')
pop = D['villas']*6 + D['houses']*6 + D['flats']*4.5
for i, (n, v) in enumerate((('فلل 400 م²', D['villas']), ('دور 250 م²', D['houses']), ('شقق (برجين)', D['flats']),
                            ('مجموع الوحدات', D['villas']+D['houses']+D['flats']))):
    y = 72 - i*11; big = i == 3
    T(p0, 312, y, n, 19 if big else 16, '#ff8a6a' if big else 'white'); T(p0, 250, y, str(v), 22 if big else 18, '#ff8a6a' if big else 'white', ha='left')
T(p0, 312, 24, f'السكان التقديري ≈ {pop:,.0f} نسمة', 13, '#ccc'); T(p0, 312, 15, f'الكثافة ≈ {pop/(S/1e4):.0f} نسمة/هكتار', 13, '#ccc')
fig.savefig(OUT, dpi=100, facecolor=BG)
print({k: round(v) for k, v in A.items()}, bid[:3], len(bid))
