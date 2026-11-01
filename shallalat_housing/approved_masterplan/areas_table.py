# Land-use areas + unit counts of the APPROVED master plan (read from hatch colours), rendered with the plan.
import sys, json, math, ezdxf
from ezdxf import colors
from shapely.geometry import Polygon
from shapely.ops import unary_union
SRC, OUT = sys.argv[1], sys.argv[2]
doc = ezdxf.readfile(SRC); ms = doc.modelspace()
def hatch_geom(h):
    g = None; n = 0
    for p in h.paths:
        try: v = [tuple(x[:2]) for x in p.vertices]
        except Exception: continue
        if len(v) < 3: continue
        P = Polygon(v).buffer(0); n += 1
        g = P if g is None else g.symmetric_difference(P)
    return g, n
CAT = {(244, 238, 81): 'villa', (248, 153, 30): 'house', (205, 32, 39): 'mall', (242, 113, 114): 'police',
       (247, 171, 174): 'cd', (169, 83, 160): 'health', (254, 204, 102): 'admin', (39, 118, 187): 'primary',
       (16, 86, 137): 'kg', (173, 221, 247): 'mosque', (34, 52, 110): 'secondary', (120, 186, 110): 'sports',
       (19, 103, 52): 'green', (147, 149, 152): 'road', (225, 225, 225): 'muni'}
geo = {}; cnt = {}
for h in ms.query('HATCH'):
    if h.dxf.layer != '0' or not h.dxf.hasattr('true_color'): continue
    k = CAT.get(colors.int2rgb(h.dxf.true_color))
    if not k: continue
    g, n = hatch_geom(h)
    if g is None and k not in ('villa', 'house'): continue
    if k in ('villa', 'house'):
        g = unary_union([Polygon([tuple(x[:2]) for x in p.vertices]) for p in h.paths]); cnt[k] = cnt.get(k, 0) + len(h.paths)
    geo[k] = g if k not in geo else geo[k].union(g)
bnd = Polygon([p[:2] for p in ms.query('LWPOLYLINE[layer=="MP_BOUNDARY"]')[0].get_points()])
towers = [Polygon([p[:2] for p in e.get_points()]) for e in ms.query('LWPOLYLINE[layer=="MP_PLAZA"]')]
# green hatch over the tower zone = tower plaza (east of the last house block)
twz = unary_union(towers).convex_hull.buffer(60)
plaza = geo['green'].intersection(twz).buffer(0)
geo['green'] = geo['green'].difference(twz)
geo['plaza'] = plaza
used = unary_union(list(geo.values()))
left = bnd.difference(used)
sv = geo['secondary'].bounds; sp = geo['sports'].bounds
geo['services_sw'] = left.intersection(Polygon([(sv[0]-200, sp[1]), (sp[2], sp[1]), (sp[2], sp[1]-400), (sv[0]-200, sp[1]-400)]))  # SW corner 'خدمات'
rest = left.difference(geo['services_sw'])
for g in sorted(getattr(rest, 'geoms', [rest]), key=lambda g: -g.area)[:6]: print('unassigned', round(g.area), [round(t) for t in g.bounds])
tw = unary_union(towers).buffer(0.5)
geo['towers'] = rest.intersection(tw)      # tower footprints (white squares)
geo['road'] = geo['road'].union(rest.difference(tw))   # thin gaps between hatches -> roads
A = {k: g.area for k, g in geo.items()}
FLATS = 342   # fixed by the user
units = dict(villa=cnt['villa'], house=cnt['house'], flats=FLATS)
json.dump(dict(areas=A, units=units, boundary=bnd.area), open(OUT+'_data.json', 'w'), indent=1)
print({k: round(v) for k, v in A.items()}, units, round(bnd.area), round(sum(A.values())))

# ---------------- image: plan + table
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy
fm.fontManager.addfont('/mnt/project-files/shallalat/03_archive/fonts/NotoSansArabic-Bold.ttf')
AR = dict(fontfamily=['Noto Sans Arabic', 'DejaVu Sans'], fontweight='bold')
fig = plt.figure(figsize=(30, 21), facecolor='white')
ax = fig.add_axes([0.0, 0.40, 1.0, 0.56])
Frontend(RenderContext(doc), MatplotlibBackend(ax), config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(
    ms, finalize=False, filter_func=lambda e: e.dxftype() not in ('MULTILEADER', 'TEXT') or e.dxf.layer == 'MP_SPORT_TEXT')
NAMES = dict(villa='فلل سكنية 400 م٢', house='دور سكنية متصلة 250 م٢', towers='الأبراج السكنية (3)', plaza='حديقة وساحة الأبراج', mall='مول تجاري',
             police='مركز شرطة', cd='دفاع مدني', health='مركز صحي', admin='إدارة المجمع', primary='مدرسة ابتدائية',
             kg='روضة', mosque='جامع', secondary='مدرسة ثانوية', sports='ملاعب كرة قدم وتنس وسلة',
             services_sw='خدمات (مرافق فنية)', green='حدائق وأشرطة خضراء', road='شوارع', muni='أرض للبلدية')
lab = ['mall', 'police', 'cd', 'health', 'admin', 'primary', 'kg', 'mosque', 'secondary', 'sports', 'services_sw', 'muni']
for k in lab:
    g = geo[k]; big = max(getattr(g, 'geoms', [g]), key=lambda x: x.area); c = big.representative_point()
    if k == 'sports': c = type(c)(338915, 4032960)
    ax.text(c.x, c.y, NAMES[k].split(' (')[0] + '\n%s م٢' % f'{A[k]:,.0f}', ha='center', va='center', size=10 if A[k] < 1000 else 13,
            color='black' if k in ('police', 'cd', 'admin', 'mosque', 'muni', 'services_sw', 'sports') else 'white', zorder=5000, **AR)
for i, t in enumerate(towers):
    c = t.centroid; ax.text(c.x, c.y, 'برج %d' % (i+1), ha='center', va='center', size=13, zorder=5000, **AR)
gates = [e for e in ms.query('HATCH') if e.dxf.hasattr('true_color') and colors.int2rgb(e.dxf.true_color) == (0, 0, 0)]
for gi, gh in enumerate(gates):
    v = [tuple(x[:2]) for x in gh.paths[0].vertices]; cx = sum(p[0] for p in v)/len(v); cy = max(p[1] for p in v)
    ax.annotate('', xy=(cx, cy), xytext=(cx, cy+28), arrowprops=dict(arrowstyle='simple', fc='#d50000', ec='#d50000', mutation_scale=40))
    ax.text(cx, cy+40, 'بوابة المشروع %d' % (gi+1), ha='center', size=17, color='#d50000', bbox=dict(fc='white', ec='#d50000', lw=2.5), **AR)
fig.set_size_inches(30, 21)
minx, miny, maxx, maxy = bnd.bounds
ax.set_xlim(minx-45, maxx+15); ax.set_ylim(miny-10, maxy+60); ax.set_aspect('equal'); ax.axis('off')
ax.text(maxx-5, maxy+50, 'N ↑', size=26, ha='right', fontweight='bold')
fig.text(0.5, 0.985, 'مجمع الشلالات السكني - المخطط الأساسي المعتمد: جدول المساحات وعدد الوحدات', ha='center', va='top', size=30, **AR)
# ---- table
rows = [('villa', units['villa']), ('house', units['house']), ('towers', units['flats']), ('plaza', None), ('mall', None), ('health', None),
        ('police', None), ('cd', None), ('admin', None), ('mosque', None), ('primary', None), ('secondary', None), ('kg', None),
        ('sports', None), ('services_sw', None), ('green', None), ('road', None)]
net = bnd.area - A['muni']
cells = [[f'{100*A[k]/bnd.area:.1f}', f'{A[k]:,.0f}', '' if u is None else f'{u}', NAMES[k], str(i+1)] for i, (k, u) in enumerate(rows)]
cells.append([f'{100*A["muni"]/bnd.area:.1f}', f'{A["muni"]:,.0f}', '', NAMES['muni'], str(len(rows)+1)])
cells.append(['100.0', f'{bnd.area:,.0f}', str(sum(units.values())), 'المجموع (مساحة الموقع)', ''])
tax = fig.add_axes([0.03, 0.01, 0.60, 0.40]); tax.axis('off')
tb = tax.table(cellText=cells, colLabels=['النسبة ٪', 'المساحة م٢', 'عدد الوحدات', 'الاستعمال', 'ت'], loc='center', cellLoc='center',
               colWidths=[0.12, 0.17, 0.14, 0.45, 0.06])
tb.auto_set_font_size(False); tb.set_fontsize(18); tb.scale(1, 2.25)
for (r, c), cell in tb.get_celld().items():
    cell.get_text().set_fontfamily(['Noto Sans Arabic', 'DejaVu Sans']); cell.get_text().set_fontweight('bold')
    if r == 0: cell.set_facecolor('#37474f'); cell.get_text().set_color('white')
    elif r == len(cells): cell.set_facecolor('#ffe0b2')
    elif c == 3 and r <= len(rows):
        k = rows[r-1][0]; col = {v: kk for kk, v in CAT.items()}.get(k)
        if col: cell.set_facecolor('#%02x%02x%02x' % tuple(int(0.35*255 + 0.65*x) for x in col))
# ---- units box
ub = ('عدد الوحدات السكنية\n\nفلل 400 م٢:  %d\nدور 250 م٢:  %d\nشقق (3 أبراج):  %d\n\nالمجموع:  %d وحدة' %
      (units['villa'], units['house'], units['flats'], sum(units.values())))
fig.text(0.80, 0.22, ub, ha='center', va='center', size=24, bbox=dict(fc='#fff8e1', ec='#e65100', lw=4, boxstyle='round,pad=0.8'), **AR)
fig.text(0.80, 0.02, 'عدد الشقق ثابت: 342 شقة (3 أبراج)\nالمساحة الصافية بعد أرض البلدية: %s م٢' % f'{net:,.0f}',
         ha='center', size=14, color='#444', **AR)
fig.savefig(OUT + '.png', dpi=100, facecolor='white'); fig.savefig(OUT + '.pdf', facecolor='white')
