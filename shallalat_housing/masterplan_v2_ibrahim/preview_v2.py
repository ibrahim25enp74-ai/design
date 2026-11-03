# Preview sheet for V2 (PREVIEW RULE: legend, label + area on every zone, gates, unit counts, land-use %).
import sys, json, ezdxf
from ezdxf import colors
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import arabic_reshaper
from bidi.algorithm import get_display

DXF, DATA, OUT, FONT = sys.argv[1:5]
fm.fontManager.addfont(FONT); _fam = fm.FontProperties(fname=FONT).get_name()
FP = fm.FontProperties(family=[_fam, 'DejaVu Sans'], weight='bold')
def ar(s): return s.replace('²', '2')   # matplotlib >= 3.10 shapes Arabic itself
doc = ezdxf.readfile(DXF); ms = doc.modelspace(); D = json.load(open(DATA))
site = Polygon([p[:2] for p in ms.query('LWPOLYLINE[layer=="MP_BOUNDARY"]')[0].get_points()])

CAT = {(244, 238, 81): 'villa', (248, 153, 30): 'house', (205, 32, 39): 'mall', (242, 113, 114): 'police',
       (247, 171, 174): 'cd', (169, 83, 160): 'health', (254, 204, 102): 'admin', (39, 118, 187): 'primary',
       (16, 86, 137): 'kg', (173, 221, 247): 'mosque', (34, 52, 110): 'secondary', (120, 186, 110): 'sports',
       (19, 103, 52): 'green'}
geo = {}
for h in ms.query('HATCH'):
    if not h.dxf.hasattr('true_color'): continue
    k = CAT.get(colors.int2rgb(h.dxf.true_color))
    if h.dxf.layer in ('MP2_TOWER', 'MP2_PLAZA', 'MP2_FOUNTAIN', 'MP2_PARKING') or (h.dxf.layer == 'MP2_GREEN' and colors.int2rgb(h.dxf.true_color) == (46, 139, 87)):
        k = 'towerzone'
    if not k: continue
    for p in h.paths:
        try: v = [tuple(x[:2]) for x in p.vertices]
        except Exception: continue
        if len(v) < 3: continue
        P = Polygon(v).buffer(0)
        geo[k] = P if k not in geo else geo[k].union(P)
west = site.intersection(box(0, 0, 339025, 1e8))
geo['services'] = west.difference(unary_union([geo['sports'], geo['secondary']]))
# priority: built uses over green (old civic greens overlap a few hatches)
for k in list(geo):
    if k != 'green': geo['green'] = geo['green'].difference(geo[k])
A = {k: g.intersection(site).area for k, g in geo.items()}
A['road'] = site.area - unary_union(list(geo.values())).intersection(site).area
S = site.area
NAME = dict(villa='فلل 400 م²', house='دور 250 م²', towerzone='منطقة الأبراج (برجين + ساحة + مواقف)', mall='مول تجاري',
            police='مركز شرطة', cd='دفاع مدني', health='مركز صحي', admin='إدارة المجمع', primary='مدرسة ابتدائية',
            kg='روضة', mosque='جامع', secondary='مدرسة ثانوية', sports='ملاعب كرة قدم وتنس', services='خدمات',
            green='مساحات خضراء وحدائق', road='شوارع وأرصفة')
COL = dict(villa='#F4EE51', house='#F8991E', towerzone='#2E8B57', mall='#CD2027', police='#F27172', cd='#F7ABAE',
           health='#A953A0', admin='#FECC66', primary='#2776BB', kg='#105689', mosque='#ADDDF7', secondary='#22346E',
           sports='#78BA6E', services='#FFFFFF', green='#136734', road='#939598')

fig = plt.figure(figsize=(30, 17), dpi=100)
ax = fig.add_axes([0.0, 0.29, 1.0, 0.70])
ctx = RenderContext(doc)
Frontend(ctx, MatplotlibBackend(ax)).draw_layout(ms, finalize=False,
    filter_func=lambda e: e.dxftype() not in ('MULTILEADER', 'TEXT', 'MTEXT'))
ax.set_facecolor('white'); ax.set_aspect('equal')
minx, miny, maxx, maxy = site.bounds
ax.set_xlim(minx-45, maxx+45); ax.set_ylim(miny-25, maxy+75)

def lab(x, y, s, a=None, c='black', fs=15, bg='white'):
    t = ar(s) if a is None else ar(s) + '\n' + f'{a:,.0f} m²'
    ax.text(x, y, t, ha='center', va='center', fontproperties=FP, fontsize=fs, color=c, zorder=1e7,
            bbox=dict(boxstyle='round,pad=0.25', fc=bg, ec='black', lw=1.2, alpha=0.92))
def ctr(k): return geo[k].representative_point().coords[0]
for k in ('mall', 'police', 'cd', 'health', 'admin', 'primary', 'kg', 'mosque', 'secondary', 'sports', 'services'):
    x, y = ctr(k); fs = 11 if k in ('police', 'cd', 'health', 'admin') else 14
    lab(x, y, NAME[k], A[k], fs=fs)
lab(339140, 4033098, 'فلل 400 م² (28 فلة)', None, fs=15)
lab(339140, 4032885, 'فلل 400 م² (22 فلة)', None, fs=15)
lab(339540, 4033110, 'دور 250 م²', None, fs=15)
lab(339540, 4032960, 'دور 250 م²', None, fs=15)
lab(339080, 4032995, 'حديقة خطية', None, fs=12, bg='#d9f2d9')
lab(339440, 4033004, 'حديقة', None, fs=12, bg='#d9f2d9')
lab(339769, 4033094, 'برج سكني 1', None, fs=12, c='white', bg='#2B2F3A')
lab(339769, 4033011, 'برج سكني 2', None, fs=12, c='white', bg='#2B2F3A')
lab(339778, 4033052, 'مواقف سيارات', None, fs=12, bg='#E0E0E0')
lab(339712, 4033068, 'ساحة المدخل\nونافورة', None, fs=11, bg='#F4ECD8')
lab(339560, 4033024, 'الشارع الرئيسي 20 م', None, fs=12, bg='#E8E8E8')
# gates
for i, (gx, gy) in enumerate([(339318.5, 4033144.5), (339694, 4033140.4)], 1):
    ax.annotate('', xy=(gx, gy+2), xytext=(gx, gy+30), zorder=1e7,
                arrowprops=dict(arrowstyle='-|>,head_width=1.2,head_length=1.6', lw=6, color='#D00000'))
    ax.text(gx, gy+40, ar(f'البوابة الرئيسية {i}'), ha='center', va='center', fontproperties=FP, fontsize=20,
            color='#D00000', zorder=1e7, bbox=dict(boxstyle='round', fc='white', ec='#D00000', lw=3))
ax.text(minx-25, maxy+42, 'N', fontsize=30, fontweight='bold', ha='center')
ax.annotate('', xy=(minx-25, maxy+30), xytext=(minx-25, maxy), arrowprops=dict(arrowstyle='-|>', lw=4, color='black'))
ax.plot([minx, minx+100], [miny-15, miny-15], lw=6, color='black'); ax.text(minx+50, miny-22, '100 m', ha='center', fontsize=14)
ax.text((minx+maxx)/2, maxy+68, ar('مجمع الشلالات السكني - مخطط ابراهيم المطوّر V2 (ضم أرض البلدية + تنظيم البلوكات)'), fontproperties=FP, fontsize=30, ha='center', va='center', zorder=1e7)
ax.axis('off')

# legend + land-use table
lx = fig.add_axes([0.01, 0.01, 0.62, 0.28]); lx.axis('off'); lx.set_xlim(0, 100); lx.set_ylim(0, 100)
order = ['villa', 'house', 'towerzone', 'green', 'sports', 'road', 'mall', 'secondary', 'primary', 'mosque',
         'kg', 'health', 'police', 'cd', 'admin', 'services']
lx.text(99, 100, ar('دليل الألوان واستعمالات الأرض'), ha='right', va='top', fontproperties=FP, fontsize=22)
for i, k in enumerate(order):
    c, r = divmod(i, 8); x = 99 - c*50; y = 84 - r*10.5
    lx.add_patch(Rectangle((x-5, y-3.5), 5, 7, fc=COL[k], ec='black', lw=1.5))
    lx.text(x-6.5, y, ar(NAME[k]).replace(' (برجين + ساحة + مواقف)', ''), ha='right', va='center', fontproperties=FP, fontsize=15)
    lx.text(x-30, y, f'{A[k]:,.0f} m²', ha='right', va='center', fontproperties=FP, fontsize=15)
    lx.text(x-42, y, f'{100*A[k]/S:.1f}%', ha='right', va='center', fontproperties=FP, fontsize=15, color='#B00000')
cx = fig.add_axes([0.65, 0.01, 0.34, 0.28]); cx.axis('off'); cx.set_xlim(0, 100); cx.set_ylim(0, 100)
cx.add_patch(Rectangle((1, 2), 98, 95, fc='#FFF8E1', ec='black', lw=3))
rows = [('فلل 400 م²', D['villas']), ('دور 250 م²', D['houses']), ('شقق (برجين)', D['flats']),
        ('مجموع الوحدات السكنية', D['villas']+D['houses']+D['flats'])]
cx.text(95, 90, ar('عدد الوحدات'), ha='right', va='top', fontproperties=FP, fontsize=26)
for i, (n, v) in enumerate(rows):
    y = 70 - i*15; big = i == 3
    cx.text(95, y, ar(n), ha='right', va='center', fontproperties=FP, fontsize=24 if big else 21, color='#B00000' if big else 'black')
    cx.text(8, y, f'{v}', ha='left', va='center', fontsize=28 if big else 24, fontweight='bold', color='#B00000' if big else 'black')
cx.text(50, 8, ar(f'مساحة الموقع {S:,.0f} م²  |  مواقف سطحية {D["stalls"]} سيارة + سرداب الأبراج'),
        ha='center', va='center', fontproperties=FP, fontsize=14)
fig.set_size_inches(30, 17); fig.savefig(OUT, dpi=100, facecolor='white')
json.dump({k: round(v) for k, v in A.items()}, open(OUT.replace('.png', '_areas.json'), 'w'), ensure_ascii=False, indent=1)
print({k: (round(v), round(100*v/S, 1)) for k, v in A.items()}, round(sum(A.values())), round(S))
