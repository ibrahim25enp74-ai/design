# Shallalat master plan SITE model (no buildings, no trees) - run: python3.11 site_blender.py DXF OUTDIR [render]
import sys, os, math
import ezdxf
from ezdxf import path as dpath
import shapely
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import affinity
import bpy, bmesh

DXF, OUT = sys.argv[1], sys.argv[2]
DO_RENDER = len(sys.argv) > 3 and sys.argv[3] == 'render'
os.makedirs(OUT, exist_ok=True)
doc = ezdxf.readfile(DXF)
msp = doc.modelspace()
OX, OY = 339076.0, 4034874.0

def mv(g):
    return affinity.translate(g, -OX, -OY)

def hatch_geom(h):
    g = None
    for p in dpath.from_hatch(h):
        v = [(q.x, q.y) for q in p.flattening(0.05)]
        if len(v) > 2:
            pg = Polygon(v).buffer(0)
            g = pg if g is None else g.symmetric_difference(pg)
    return g

def layer(L):
    gs = [hatch_geom(h) for h in msp.query(f'HATCH[layer=="{L}"]')]
    gs = [g for g in gs if g is not None and not g.is_empty]
    return mv(unary_union(gs).buffer(0.08, join_style='mitre').buffer(-0.08, join_style='mitre')) if gs else Polygon()

site = mv(Polygon(msp.query('LWPOLYLINE[layer=="SITE-BOUNDARY"]')[0].get_points('xy')))
road = layer('R-ASPHALT')
road_orig = road
median = layer('R-MEDIAN')
median_orig = median
green = layer('B-GREEN')
houses = layer('B-HOUSES'); villas = layer('B-VILLAS')
services = layer('B-SERVICES'); plaza = layer('B-PLAZA'); towers = layer('B-TOWERS')
t = {L: layer(L) for L in ['T-PAVED', 'T-GARDEN-PATH', 'T-TERRACE', 'T-TOWER', 'T-PLAY', 'T-FOUNTAIN', 'T-RAMP']}

# ---- 12 m street section applied to every road edge that faces a property:
# property edge | drain 0.4 | footpath 2.0 | tree corridor 1.0 (incl. 0.15 kerb) | carriageway
def polys(g):
    if g is None or g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    if isinstance(g, MultiPolygon): return list(g.geoms)
    return [p for gg in getattr(g, 'geoms', []) for p in polys(gg)]
big = lambda g, a: unary_union([p for p in polys(g) if p.area > a])
props = site.difference(road).difference(median)
props = big(props.buffer(-0.6, join_style='mitre').buffer(0.6, join_style='mitre'), 60)
road = road.union(site.difference(props).difference(median))
# narrow pedestrian fingers of the road hatch -> part of the adjacent plaza; footpath runs straight past
narrow0 = big(road.difference(road.buffer(-5.0).buffer(5.0, join_style='round')).difference(median.buffer(12)), 40)
fill = []
_pu = props.union(narrow0)
for nk in polys(narrow0):
    side_ = [p for p in polys(_pu) if p.intersects(nk)][0]
    other = props.difference(side_.buffer(0.5))
    L_ = road.intersection(nk.buffer(25))
    bd = side_.boundary.intersection(L_.buffer(0.5)).difference(nk.buffer(1))
    ds = sorted(other.distance(Point(c)) for g_ in getattr(bd, 'geoms', [bd]) for c in getattr(g_, 'coords', []))
    if not ds: continue
    Wm = ds[len(ds) // 2]
    sm = side_.buffer(25.0, join_style='round').buffer(-25.0, join_style='round')   # smooth the tower-side edge (fills dents/bulges)
    fill.append(sm.difference(side_).intersection(road).intersection(side_.buffer(5.0)).union(L_.intersection(nk.buffer(3.0))))
    print('finger', round(nk.centroid.x), round(nk.centroid.y), 'road width', round(Wm, 2))
fill = unary_union(fill).intersection(road) if fill else Polygon()
ped = narrow0.union(fill.intersection(narrow0.buffer(3.0)))   # paved finger + its mouth
fill_green = fill.difference(ped)                              # rest of the bulge -> lawn behind a straight footpath
green = green.union(fill_green)
props = props.union(ped).union(fill_green)
road = unary_union(polys(shapely.make_valid(road.difference(ped).difference(fill_green)))).buffer(0)
props = unary_union(polys(shapely.make_valid(props))).buffer(0)
# round acute tips of blocks/greens: the clipped tip becomes footpath paving
_pr = props.buffer(-6.0, join_style='round').buffer(6.0, join_style='round')
tip = unary_union([p for p in polys(props.difference(_pr)) if 0.5 < p.area < 75 and p.intersects(road.buffer(0.3))])
props = props.difference(tip)
road = road.union(tip)          # tips become road: kerb/footpath follow a smooth arc
green, houses, villas, services, plaza, towers = [big(g_.difference(tip).difference(road.buffer(-0.05)), 1.0) for g_ in (green, houses, villas, services, plaza, towers)]
print('tips', len(polys(tip)), round(tip.area))
b = lambda d: props.buffer(d, join_style='mitre', mitre_limit=2.0)
drain = road.intersection(b(0.4))
def polys(g):
    if g is None or g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    if isinstance(g, MultiPolygon): return list(g.geoms)
    return [p for gg in getattr(g, 'geoms', []) for p in polys(gg)]

# ---- classify 15 m roads by measuring width along the centre lines
cls = []
for e in msp.query('*[layer=="R-CL"]'):
    try: p = dpath.make_path(e)
    except Exception: continue
    v = [(q.x - OX, q.y - OY) for q in p.flattening(0.05)]
    if len(v) > 1: cls.append(LineString(v))
pb = props.boundary
c15, c20, ticks = [], [], []
for ln in cls:
    s = 0.0
    while s < ln.length:
        pt = ln.interpolate(s)
        wdt = 2 * pt.distance(pb)
        if 18.5 <= wdt <= 21.5 and median.buffer(0.5).contains(pt):
            seg = shapely.ops.substring(ln, max(s - 1.0, 0), min(s + 1.0, ln.length))
            c20.append(seg.buffer(10.0, cap_style='flat'))
            if abs((s % 6.0)) < 0.5:
                a = ln.interpolate(max(s - 0.5, 0)); bb = ln.interpolate(min(s + 0.5, ln.length))
                dx, dy = bb.x - a.x, bb.y - a.y; L = math.hypot(dx, dy) or 1
                ticks.append(LineString([(pt.x - dy / L * 10, pt.y + dx / L * 10), (pt.x + dy / L * 10, pt.y - dx / L * 10)]).buffer(0.06, cap_style='flat'))
        elif 13.8 <= wdt <= 16.2 and road.contains(pt):
            seg = shapely.ops.substring(ln, max(s - 1.0, 0), min(s + 1.0, ln.length))
            c15.append(seg.buffer(8.0, cap_style='flat'))
            if abs((s % 6.0)) < 0.5:   # parking bay ticks every 6 m
                a = ln.interpolate(max(s - 0.5, 0)); bb = ln.interpolate(min(s + 0.5, ln.length))
                dx, dy = bb.x - a.x, bb.y - a.y; L = math.hypot(dx, dy) or 1
                ticks.append(LineString([(pt.x - dy / L * 8, pt.y + dx / L * 8), (pt.x + dy / L * 8, pt.y - dx / L * 8)]).buffer(0.06, cap_style='flat'))
        s += 1.0
for mp in [m_ for m_ in polys(median) if m_.area > 150]:
    rr = list(mp.minimum_rotated_rectangle.exterior.coords)[:4]
    e1 = (rr[1][0]-rr[0][0], rr[1][1]-rr[0][1]); e2 = (rr[2][0]-rr[1][0], rr[2][1]-rr[1][1])
    if math.hypot(*e1) < math.hypot(*e2): e1, e2 = e2, e1
    c = mp.minimum_rotated_rectangle.centroid; l1 = math.hypot(*e1); u = (e1[0]/l1, e1[1]/l1); n = (-u[1], u[0])
    c20.append(Polygon([(c.x+sa*u[0]*l1/2+sb*n[0]*10, c.y+sa*u[1]*l1/2+sb*n[1]*10) for sa, sb in ((-1,-1),(1,-1),(1,1),(-1,1))]))
    for k in range(int(l1 // 6) + 1):
        q = (c.x + u[0]*(-l1/2 + 3 + 6*k), c.y + u[1]*(-l1/2 + 3 + 6*k))
        ticks.append(LineString([(q[0]-n[0]*10, q[1]-n[1]*10), (q[0]+n[0]*10, q[1]+n[1]*10)]).buffer(0.06, cap_style='flat'))
zone20 = road.union(median).intersection(unary_union(c20).buffer(0.01))
med20 = median.buffer(-1.0).intersection(zone20)          # 2 m central planting strip
median = median.difference(zone20).union(med20)
zone15 = road.intersection(unary_union(c15)).difference(zone20)
zone15 = big(zone15, 400)
zone12 = road.difference(zone15).difference(zone20)
core = road.union(median).difference(zone20).difference(props.buffer(8.2)).buffer(0.5)   # junction / wide areas
core = big(core, 20)
nopark = core.buffer(9.0).union(towers.buffer(20))   # no parking along the tower-zone road
# ---- edge-based sections: every block edge gets the section of the road it faces;
# changes happen at a single radial cut on the block corner (flat caps) -> clean junctions
SEC = {12: dict(foot=2.0, plant=2.85, kerb=3.0, park=None),
       15: dict(foot=1.8, plant=2.10, kerb=2.25, park=4.5),
       20: dict(foot=2.4, plant=3.45, kerb=3.6, park=6.0)}
import numpy as np
from shapely.geometry.polygon import orient as _orient
KEYS = ('foot', 'plant', 'kerb', 'park')
VAL = {T: [SEC[T][k] or SEC[T]['kerb'] for k in KEYS] for T in SEC}   # 12 m: no parking -> park = kerb line
STEP, HALF = 0.5, 16          # smoothing window +-8 m -> ~16 m long realistic taper
strips = {k: [] for k in KEYS}
for P in polys(props):
    P = _orient(P, 1.0)
    for ring in [P.exterior, *P.interiors]:
        pts = np.array(ring.segmentize(STEP).coords)[:-1]
        keep = np.hypot(*(np.roll(pts, -1, axis=0) - pts).T) > 0.05
        pts = pts[keep]
        n = len(pts)
        if n < 4: continue
        nxt = np.roll(pts, -1, axis=0); d = nxt - pts; L = np.hypot(d[:, 0], d[:, 1]); L[L == 0] = 1e-9
        sn = np.stack([d[:, 1] / L, -d[:, 0] / L], 1)          # right-hand normal = outward of props
        vn = sn + np.roll(sn, 1, axis=0); vl = np.hypot(vn[:, 0], vn[:, 1]); vl[vl == 0] = 1; vn /= vl[:, None]
        W = np.zeros((n, 4))
        for i in range(n):
            mx, my = (pts[i] + nxt[i]) / 2
            q = Point(mx + sn[i, 0] * 5, my + sn[i, 1] * 5)
            if road.contains(q):
                T = 20 if zone20.contains(q) else 15 if zone15.contains(q) else 12
                W[i] = VAL[T]
        k = np.ones(2 * HALF + 1) / (2 * HALF + 1)
        Ws = np.stack([np.convolve(np.pad(W[:, j], HALF, mode='wrap'), k, 'valid') for j in range(4)], 1)
        Wv = (Ws + np.roll(Ws, 1, axis=0)) / 2                 # per-vertex widths
        for j, key in enumerate(KEYS):
            off = pts + vn * Wv[:, j:j + 1]
            qs = [Polygon([pts[i], pts[(i + 1) % n], off[(i + 1) % n], off[i]]) for i in range(n) if Wv[i, j] > 0.02 or Wv[(i + 1) % n, j] > 0.02]
            qs = [q.buffer(0) for q in qs]
            strips[key] += [q for q in qs if not q.is_empty]
narrow = Polygon()
S = {k: unary_union(v).buffer(0.05).buffer(-0.05).intersection(road).difference(narrow).simplify(0.03) for k, v in strips.items()}
drain = props.buffer(0.4, join_style='round').intersection(S['foot'])
foot = S['foot'].union(narrow)          # drain is laid on top as an overlay
side = S['kerb']
plant = S['plant'].difference(S['foot'])
kerb = side.difference(S['plant'])
park15 = S['park'].difference(side).difference(nopark).difference(med20)
park15 = big(park15, 15)
parkline = park15.buffer(0.1).difference(park15).difference(side.buffer(0.05)).intersection(road).difference(med20)
parkline = parkline.union(unary_union(ticks).intersection(park15))
carr = road.difference(side).difference(park15).difference(med20).difference(narrow)
print('20 m', round(zone20.area), '15 m road area', round(zone15.area), '12 m road area', round(zone12.area))
med_kerb = median.difference(median.buffer(-0.15))
med_grass = median.buffer(-0.15)

# centre-line dashes (3 m dash / 3 m gap) only inside carriageway, away from medians
dashes = []
carr_in = carr.buffer(-0.5)
for e in msp.query('*[layer=="R-CL"]'):
    try:
        p = dpath.make_path(e)
    except Exception:
        continue
    v = [(q.x - OX, q.y - OY) for q in p.flattening(0.05)]
    if len(v) < 2:
        continue
    ln = LineString(v)
    s = 1.5
    while s + 3 < ln.length:
        seg = shapely.ops.substring(ln, s, s + 3)
        if carr_in.contains(seg) and median.buffer(2).disjoint(seg) and core.disjoint(seg):
            dashes.append(seg.buffer(0.075, cap_style='flat'))
        s += 6
dashes = unary_union(dashes)

# plot boundary lines
lot_lines = []
lot_polys = []
for L in ['L-HOUSE-LOTS', 'L-VILLA-LOTS', 'L-SERVICE-PLOTS']:
    for e in msp.query(f'LWPOLYLINE[layer=="{L}"]'):
        pts = e.get_points('xy')
        if len(pts) > 2:
            lot_lines.append(mv(Polygon(pts)).exterior); lot_polys.append(mv(Polygon(pts)).buffer(0))
lot_lines = unary_union(lot_lines).buffer(0.15, cap_style='flat').intersection(houses.union(villas).union(services).buffer(0.01))

# external streets (context)
ext = []
ls = [e for e in msp.query('LINE[layer=="EXT-STREET"]')]
for a, c in [(0, 1), (2, 3)]:
    p1, p2 = ls[a], ls[c]
    ext.append(mv(Polygon([tuple(p1.dxf.start)[:2], tuple(p1.dxf.end)[:2], tuple(p2.dxf.end)[:2], tuple(p2.dxf.start)[:2]]).buffer(0)))
ext = unary_union(ext).difference(site)

# ---------------- Blender ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

def mat(name, col, rough=0.8, tex=None, scale=1.0, col2=None, emit=None, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Base Color'].default_value = (*col, 1)
    if tex:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        if tex == 'brick':
            tx = nt.nodes.new('ShaderNodeTexBrick')
            tx.inputs['Scale'].default_value = scale
            tx.inputs['Color1'].default_value = (*col, 1)
            tx.inputs['Color2'].default_value = (*(col2 or col), 1)
            tx.inputs['Mortar'].default_value = (col[0] * .7, col[1] * .7, col[2] * .7, 1)
            tx.inputs['Mortar Size'].default_value = 0.01
            nt.links.new(tc.outputs['Object'], tx.inputs['Vector'])
            nt.links.new(tx.outputs['Color'], bsdf.inputs['Base Color'])
        else:
            tx = nt.nodes.new('ShaderNodeTexNoise')
            tx.inputs['Scale'].default_value = scale
            tx.inputs['Detail'].default_value = 8
            nt.links.new(tc.outputs['Object'], tx.inputs['Vector'])
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
            mix.inputs['A'].default_value = (*col, 1)
            mix.inputs['B'].default_value = (*(col2 or col), 1)
            nt.links.new(tx.outputs['Fac'], mix.inputs['Factor'])
            nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1)
        bsdf.inputs['Emission Strength'].default_value = 0.0
    return m

M = {
    'asphalt': mat('Asphalt', (0.045, 0.047, 0.05), 0.9, 'noise', 3.0, (0.07, 0.07, 0.075)),
    'foot': mat('Footpath_paving', (0.62, 0.55, 0.45), 0.85, 'brick', 2.5, (0.55, 0.48, 0.40)),
    'plant': mat('Tree_corridor_grass', (0.10, 0.22, 0.05), 0.95, 'noise', 1.5, (0.20, 0.17, 0.08)),
    'park': mat('Parking_asphalt', (0.07, 0.07, 0.075), 0.9, 'noise', 3.0, (0.09, 0.09, 0.095)),
    'wall': mat('Boundary_wall', (0.78, 0.74, 0.66), 0.8, 'brick', 1.2, (0.72, 0.68, 0.60)),
    'kerb': mat('Kerb_concrete', (0.70, 0.70, 0.68), 0.7),
    'drain': mat('Stormwater_drain', (0.42, 0.42, 0.42), 0.6, 'brick', 12, (0.30, 0.30, 0.30), metal=0.3),
    'dash': mat('Road_marking', (0.95, 0.95, 0.92), 0.5),
    'grass': mat('Grass', (0.08, 0.25, 0.04), 0.95, 'noise', 0.3, (0.15, 0.32, 0.06)),
    'plot': mat('Residential_plot', (0.70, 0.62, 0.50), 0.95, 'noise', 0.2, (0.62, 0.55, 0.44)),
    'villa': mat('Villa_plot', (0.74, 0.66, 0.52), 0.95, 'noise', 0.2, (0.66, 0.58, 0.46)),
    'lotline': mat('Plot_boundary', (0.85, 0.83, 0.78), 0.7),
    'service': mat('Service_plot', (0.72, 0.70, 0.66), 0.9, 'noise', 0.3, (0.66, 0.64, 0.60)),
    'plaza': mat('Plaza_paving', (0.80, 0.76, 0.68), 0.7, 'brick', 1.0, (0.70, 0.66, 0.58)),
    'paved': mat('Tower_zone_paving', (0.78, 0.74, 0.66), 0.7, 'brick', 1.5, (0.68, 0.64, 0.57)),
    'water': mat('Fountain_water', (0.05, 0.25, 0.35), 0.05),
    'play': mat('Play_rubber', (0.65, 0.25, 0.15), 0.9),
    'ramp': mat('Basement_ramp', (0.10, 0.10, 0.11), 0.8),
    'terrain': mat('Surrounding_ground', (0.45, 0.38, 0.28), 1.0, 'noise', 0.02, (0.36, 0.31, 0.24)),
}

def polys(g):
    if g is None or g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    if isinstance(g, MultiPolygon): return list(g.geoms)
    return [p for gg in getattr(g, 'geoms', []) for p in polys(gg)]

from shapely.geometry.polygon import orient
from shapely.ops import split as ssplit

def holefree(p, depth=0):
    """split a polygon with holes into hole-free pieces by cutting through hole centroids"""
    if not p.interiors or depth > 40:
        return [p]
    h = Polygon(p.interiors[0]).representative_point()
    x0, y0, x1, y1 = p.bounds
    cut = LineString([(h.x, y0 - 1), (h.x, y1 + 1)])
    out = []
    for q in polys(ssplit(p, cut)):
        out += holefree(q, depth + 1)
    return out

def prism(name, g, z0, z1, m, tiles=None):
    bm = bmesh.new()
    g = shapely.set_precision(g, 0.005) if not g.is_empty else g
    tops = []
    if tiles:
        cover = unary_union(tiles)
        for t_ in tiles:
            tops += polys(shapely.set_precision(t_, 0.005))
        tops += polys(g.difference(cover))
    else:
        tops = polys(g)
    for p in tops:
        if p.area < 0.01: continue
        for q in holefree(p):
            q = orient(q.simplify(0.01), 1.0)
            if q.is_empty or q.area < 0.01 or q.geom_type != 'Polygon': continue
            c = list(q.exterior.coords)[:-1]
            vs = [bm.verts.new((x, y, z1)) for x, y in c]
            try: bm.faces.new(vs)
            except ValueError: pass
    for p in polys(g):
        if p.area < 0.01: continue
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)
            for (xa, ya), (xb, yb) in zip(c[:-1], c[1:]):
                vs = [bm.verts.new(v) for v in ((xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1))]
                try: bm.faces.new(vs)
                except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.003)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = False
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m)
    scn.collection.objects.link(ob)
    return ob

# levels (m): carriageway 0.00 | planting 0.10 | footpath/kerb 0.15 | drain 0.12 | plots 0.25
prism('Surrounding_ground', box(-1300, -900, 1300, 900).difference(site).difference(ext), -0.6, -0.05, M['terrain'])
prism('External_streets_30m_20m', ext, -0.6, 0.0, M['asphalt'])
prism('Site_base', site.union(road), -0.8, -0.35, M['kerb'])
prism('Road_base', road, -0.7, -0.2, M['asphalt'])
prism('Sidewalk_base', side.union(narrow), -0.6, 0.0, M['kerb'])
prism('Carriageway', carr, -0.4, 0.0, M['asphalt'])
prism('Centre_line_dashed', dashes, 0.0, 0.006, M['dash'])
prism('Parking_lanes_2_25m', park15, -0.4, 0.0, M['park'])
prism('Parking_marking', parkline, 0.0, 0.006, M['dash'])
prism('Kerb', kerb, -0.4, 0.15, M['kerb'])
prism('Tree_strip', plant, -0.4, 0.10, M['plant'])
prism('Footpath', foot, -0.4, 0.15, M['foot'])
prism('Pedestrian_paving', ped, -0.4, 0.25, M['paved'])
# perimeter wall between the project and the external streets, open only at the gates
gates = unary_union([m_.buffer(10.5) for m_ in polys(median_orig)])   # 4 gates, each around its median
wl = site.exterior.difference(gates)
wl = unary_union([l for l in getattr(wl, 'geoms', [wl]) if l.length > 1.0])
wall = wl.buffer(0.15, cap_style='flat', join_style='mitre').intersection(site.buffer(0.01))
prism('Perimeter_wall_2_4m', wall, -0.4, 2.4, M['wall'])
print('wall length', round(wl.length))
prism('Stormwater_drain', drain, 0.15, 0.156, M['drain'])
prism('Median_kerb', med_kerb, -0.4, 0.18, M['kerb'])
prism('Median_green', med_grass, -0.4, 0.15, M['grass'])
prism('Green_areas', green, -0.4, 0.25, M['grass'])
tl = lambda blk: [q for lp in lot_polys for q in polys(lp.intersection(blk)) if q.area > 1]
prism('House_plots', houses, -0.4, 0.25, M['plot'], tl(houses))
prism('Villa_plots', villas, -0.4, 0.25, M['villa'], tl(villas))
prism('Plot_boundaries', lot_lines, 0.25, 0.32, M['lotline'])
prism('Service_plots', services, -0.4, 0.25, M['service'], tl(services))
prism('Central_plaza', plaza, -0.4, 0.25, M['plaza'])
tz_hard = unary_union([t['T-PAVED'], t['T-GARDEN-PATH'], t['T-TERRACE'], t['T-TOWER']])
prism('Tower_zone_garden', towers.difference(tz_hard).difference(t['T-FOUNTAIN']).difference(t['T-PLAY']).difference(t['T-RAMP']), -0.4, 0.25, M['grass'])
prism('Tower_zone_paving', tz_hard.intersection(towers).difference(t['T-FOUNTAIN']).difference(t['T-PLAY']).difference(t['T-RAMP']), -0.4, 0.27, M['paved'])
prism('Fountain_water', t['T-FOUNTAIN'], -0.4, 0.15, M['water'])
prism('Fountain_edge', t['T-FOUNTAIN'].difference(t['T-FOUNTAIN'].buffer(-0.4)), -0.4, 0.55, M['kerb'])
prism('Play_area', t['T-PLAY'], -0.4, 0.27, M['play'])
prism('Basement_ramps', t['T-RAMP'], -0.4, 0.26, M['ramp'])

areas = dict(carriageway=carr.area, footpath=foot.area, tree_corridor=plant.area, kerb=kerb.area,
             drain=drain.area, median=median.area, green=green.area, houses=houses.area, villas=villas.area,
             services=services.area, plaza=plaza.area, towers=towers.area, road_total=road.area, site=site.area)
print({k: round(v) for k, v in areas.items()})

# ---- world, light, cameras
w = bpy.data.worlds.new('Sky'); scn.world = w; w.use_nodes = True
sky = w.node_tree.nodes.new('ShaderNodeTexSky')
for st in ('MULTIPLE_SCATTERING', 'NISHITA'):
    try: sky.sky_type = st; break
    except TypeError: pass
sky.sun_elevation = math.radians(38); sky.sun_rotation = math.radians(215)
w.node_tree.links.new(sky.outputs['Color'], w.node_tree.nodes['Background'].inputs['Color'])
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.5; sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(52), 0, math.radians(215 - 180 + 90))
scn.collection.objects.link(sun)

def cam(name, loc, target, lens=35):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); c.data.lens = lens
    c.data.clip_end = 5000; c.location = loc
    scn.collection.objects.link(c)
    from mathutils import Vector
    d = Vector(target) - Vector(loc)
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return c

# street-level camera on the internal 12 m road nearest its label
lab = Point(339248 - OX, 4034973 - OY)
best = None
for e in msp.query('*[layer=="R-CL"]'):
    try: p = dpath.make_path(e)
    except Exception: continue
    ln = LineString([(q.x - OX, q.y - OY) for q in p.flattening(0.1)])
    dd = ln.distance(lab)
    if best is None or dd < best[0]: best = (dd, ln)
ln = best[1]; s0 = ln.project(lab)
pA = ln.interpolate(max(s0 - 40, 0)); pB = ln.interpolate(min(s0 + 20, ln.length))
dx, dy = pB.x - pA.x, pB.y - pA.y; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
cams = [
    cam('CAM_01_AERIAL_SW', (-620, -820, 520), (-20, 20, 0), 32),
    cam('CAM_02_AERIAL_TOP', (0, 0, 1350), (0, 0.01, 0), 30),
    cam('CAM_03_DRONE_STREET', (pA.x + nx * 25, pA.y + ny * 25, 22), (pB.x + 40 * dx / L, pB.y + 40 * dy / L, 0), 30),
    cam('CAM_04_STREET_LEVEL', (pA.x - nx * 1.5, pA.y - ny * 1.5, 1.65), (pB.x + 60 * dx / L - nx * 1.5, pB.y + 60 * dy / L - ny * 1.5, 1.0), 24),
]
scn.camera = cams[0]

scn.render.engine = 'CYCLES'
scn.cycles.samples = int(os.environ.get('SPP', 48)); scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = int(os.environ.get('RX',1920)), int(os.environ.get('RX',1920))*9//16
scn.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in scn.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
scn.view_settings.exposure = float(os.environ.get('EXP',-3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'SHALLALAT_SITE_MODEL.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'SHALLALAT_SITE_MODEL.glb'), export_format='GLB', export_cameras=False, export_lights=False)
if DO_RENDER:
    for c in [c for c in cams if os.environ.get('CAMS','') in c.name]:
        scn.camera = c
        scn.render.filepath = os.path.join(OUT, c.name.replace('CAM_', '') + '.png')
        bpy.ops.render.render(write_still=True)
        print('rendered', c.name, flush=True)
