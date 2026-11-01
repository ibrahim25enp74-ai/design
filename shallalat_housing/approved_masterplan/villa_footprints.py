# Adds villa building footprints to the APPROVED master plan (new copy; original untouched).
# Villa plots = yellow hatch paths (RGB 244,238,81). Footprint: front setback 5 m, rear 3 m, sides 1.5 m.
import sys, math, ezdxf
from ezdxf import colors
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
SRC, OUT = sys.argv[1], sys.argv[2]
FRONT, REAR, SIDE = 5.0, 3.0, 1.5
doc = ezdxf.readfile(SRC); ms = doc.modelspace()
plots = []
for h in ms.query('HATCH'):
    if h.dxf.hasattr('true_color') and colors.int2rgb(h.dxf.true_color) == (244, 238, 81):
        for p in h.paths:
            v = [tuple(x[:2]) for x in p.vertices]
            if len(v) > 4 and math.dist(v[0], v[-1]) < 0.01: v = v[:-1]
            if len(v) == 4: plots.append(v)
print('villa plots', len(plots))
U = unary_union([Polygon(v) for v in plots])
grey = None
for h in ms.query('HATCH'):
    if h.dxf.hasattr('true_color') and colors.int2rgb(h.dxf.true_color) == (147, 149, 152):
        grey = True
for n in ['MP_VILLA_FOOTPRINT', 'MP_VILLA_FOOTPRINT_HATCH', 'MP_VILLA_ENTRY']:
    if n not in doc.layers: doc.layers.add(n)
doc.layers.get('MP_VILLA_FOOTPRINT').color = 7
fp_areas = []
for v in plots:
    P = Polygon(v)
    edges = [(v[i], v[(i+1) % 4]) for i in range(4)]
    L = [math.dist(a, b) for a, b in edges]
    shorts = sorted(range(4), key=lambda i: L[i])[:2]
    # front = short edge whose outside neighbourhood is not another villa plot
    def outside_free(i):
        a, b = edges[i]; m = ((a[0]+b[0])/2, (a[1]+b[1])/2); c = P.centroid
        dx, dy = m[0]-c.x, m[1]-c.y; d = math.hypot(dx, dy)
        q = Point(m[0]+dx/d*2, m[1]+dy/d*2)
        return not U.contains(q)
    fr = [i for i in shorts if outside_free(i)]
    fi = fr[0] if fr else shorts[0]
    a, b = edges[fi]; c2, d2 = edges[(fi+2) % 4]      # rear edge runs d2->c2 reversed
    rb, ra = c2, d2                                    # rear points opposite a,b: a<->ra(d2)? keep orientation
    # quad order a,b,c2,d2 : a-b front, b-c2 side, c2-d2 rear, d2-a side
    W = math.dist(a, b); D = (math.dist(b, c2) + math.dist(d2, a))/2
    def P_(s, t):   # s along front (0..W), t depth (0..D) bilinear
        fs, ft = s/W, t/D
        fx = a[0] + (b[0]-a[0])*fs; fy = a[1] + (b[1]-a[1])*fs
        rx = d2[0] + (c2[0]-d2[0])*fs; ry = d2[1] + (c2[1]-d2[1])*fs
        return (fx + (rx-fx)*ft, fy + (ry-fy)*ft)
    fp = [P_(SIDE, FRONT), P_(W-SIDE, FRONT), P_(W-SIDE, D-REAR), P_(SIDE, D-REAR)]
    fp_areas.append(Polygon(fp).area)
    ms.add_lwpolyline(fp, close=True, dxfattribs={'layer': 'MP_VILLA_FOOTPRINT', 'lineweight': 35})
    hh = ms.add_hatch(dxfattribs={'layer': 'MP_VILLA_FOOTPRINT_HATCH'}); hh.rgb = (255, 255, 255)
    hh.paths.add_polyline_path(fp, is_closed=True)
    # entry marker: small triangle on the front setback centre
    m0 = P_(W/2, 0.6); m1 = P_(W/2-1.2, 2.4); m2 = P_(W/2+1.2, 2.4)
    ms.add_lwpolyline([m0, m1, m2], close=True, dxfattribs={'layer': 'MP_VILLA_ENTRY', 'color': 1})
print('footprint m2 avg %.1f min %.1f max %.1f, coverage %.0f%%' % (sum(fp_areas)/len(fp_areas), min(fp_areas), max(fp_areas),
      100*sum(fp_areas)/sum(Polygon(v).area for v in plots)))
# keep hatch draw order: move footprints to the top
doc.saveas(OUT)
