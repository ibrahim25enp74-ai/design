"""Structural check of the 6 m x 15 m skylight roof between two houses.

Pin-jointed plane truss (direct stiffness), steel SHS 80x80, checked to
EN 1993-1-1 (S235, cold-formed tubes -> buckling curve c).
Run:  python3 truss_calc.py
"""
import math
import numpy as np

# ------------------------------------------------------------------ geometry
import sys
SPAN = float(sys.argv[1]) if len(sys.argv) > 1 else 6.7   # m, leg axis to leg axis
H_END, RISE = 0.50, 0.50                     # m
LENGTH, N_TRUSS = 15.0, 8                    # 8 trusses -> 7 bays
BAY = LENGTH / (N_TRUSS - 1)                 # 2.143 m = 2.1 m sheet + H-profile
PANEL = SPAN / 6                             # m, 6 panels per truss

xs = [i * PANEL for i in range(7)]
top_y = lambda x: H_END + RISE * (1 - abs(x - SPAN / 2) / (SPAN / 2))
nodes = [(x, 0.0) for x in xs] + [(x, top_y(x)) for x in xs]   # 0..6 bottom, 7..13 top
B = lambda i: i
T = lambda i: 7 + i

members = []  # (i, j, group)
for i in range(6):
    members.append((B(i), B(i + 1), "bottom chord"))
    members.append((T(i), T(i + 1), "top chord"))
for i in range(7):
    members.append((B(i), T(i), "end post" if i in (0, 6) else "vertical"))
# Pratt: diagonals run down towards mid-span (tension under gravity)
for i in range(3):
    members.append((T(i), B(i + 1), "diagonal"))
    members.append((T(6 - i), B(5 - i), "diagonal"))

# ------------------------------------------------------------------ sections
E, FY, GM0, GM1 = 210e6, 235e3, 1.0, 1.0       # kPa
def shs(b, t):
    """Square hollow section, cold formed, corner radius ~ 2t (outer)."""
    bi = b - 2 * t
    A = b * b - bi * bi - (4 - math.pi) * ((2 * t) ** 2 - t ** 2)
    I = (b ** 4 - bi ** 4) / 12 * 0.96          # small reduction for corners
    return dict(name=f"SHS {b*1e3:.0f}x{b*1e3:.0f}x{t*1e3:.0f}", b=b, t=t, A=A, I=I,
                W=I / (b / 2), i=math.sqrt(I / A), kg=A * 7850)
S3 = shs(0.080, 0.003)
S2 = shs(0.080, 0.002)
SEC = {"top chord": S3, "bottom chord": S3, "end post": S3, "vertical": S2, "diagonal": S2}

def length(m):
    (x1, y1), (x2, y2) = nodes[m[0]], nodes[m[1]]
    return math.hypot(x2 - x1, y2 - y1)

# ------------------------------------------------------------------ loads
# kN/m2 on plan
G_SHEET = 0.10   # 16 mm multiwall polycarbonate + aluminium profiles + fixings
G_DUST = 0.15    # dust / sand build-up (Mosul)
Q_ROOF = 0.60    # maintenance live load, roof not accessible
W_UP = 1.00      # wind uplift, net (qp ~0.8 kN/m2, net cp ~ -1.25)
W_DOWN = 0.30    # wind pressure
PURLIN = S2      # purlins SHS 80x80x2, 7 lines, continuous over trusses

def node_loads(w_area, with_self=True, self_factor=1.0):
    """Vertical nodal loads (kN, +down) on one internal truss."""
    F = np.zeros(2 * len(nodes))
    trib_x = [PANEL / 2 + 0.10] + [PANEL] * 5 + [PANEL / 2 + 0.10]   # 100 mm eave overhang
    for i, tx in enumerate(trib_x):
        F[2 * T(i) + 1] -= w_area * tx * BAY
        if with_self:
            F[2 * T(i) + 1] -= self_factor * PURLIN["kg"] * 9.81e-3 * BAY
    if with_self:
        for m in members:
            wgt = SEC[m[2]]["kg"] * 9.81e-3 * length(m) * 1.10  # +10% welds/plates
            for n in m[:2]:
                F[2 * n + 1] -= self_factor * wgt / 2
    return F

def solve(F):
    n = len(nodes)
    K = np.zeros((2 * n, 2 * n))
    for m in members:
        (x1, y1), (x2, y2) = nodes[m[0]], nodes[m[1]]
        L = length(m); c, s = (x2 - x1) / L, (y2 - y1) / L
        k = E * SEC[m[2]]["A"] / L
        kl = k * np.array([[c*c, c*s, -c*c, -c*s], [c*s, s*s, -c*s, -s*s],
                           [-c*c, -c*s, c*c, c*s], [-c*s, -s*s, c*s, s*s]])
        dofs = [2*m[0], 2*m[0]+1, 2*m[1], 2*m[1]+1]
        for a in range(4):
            for b in range(4):
                K[dofs[a], dofs[b]] += kl[a, b]
    fixed = [2*B(0), 2*B(0)+1, 2*B(6)+1]          # pin + roller
    free = [d for d in range(2*n) if d not in fixed]
    u = np.zeros(2*n)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    R = K @ u - F
    N = []
    for m in members:
        (x1, y1), (x2, y2) = nodes[m[0]], nodes[m[1]]
        L = length(m); c, s = (x2 - x1) / L, (y2 - y1) / L
        du = u[2*m[1]] - u[2*m[0]]; dv = u[2*m[1]+1] - u[2*m[0]+1]
        N.append(E * SEC[m[2]]["A"] / L * (c*du + s*dv))   # + tension
    return np.array(N), u, R

G = G_SHEET + G_DUST
combos = {
    "ULS1 1.35G+1.5Q":        (1.35 * G + 1.5 * Q_ROOF, 1.35),
    "ULS2 1.35G+1.5Wdown+1.05Q": (1.35 * G + 1.5 * W_DOWN + 1.05 * Q_ROOF, 1.35),
    "ULS3 1.0G-1.5Wup":       (1.0 * G - 1.5 * W_UP, 1.0),
}
res = {k: solve(node_loads(w, self_factor=sf)) for k, (w, sf) in combos.items()}

# ------------------------------------------------------------------ member checks
def chi(lam_bar, alpha=0.49):                   # curve c (cold formed)
    phi = 0.5 * (1 + alpha * (lam_bar - 0.2) + lam_bar ** 2)
    return min(1.0, 1 / (phi + math.sqrt(max(phi ** 2 - lam_bar ** 2, 0))))

# out-of-plane buckling length: top chord held by purlins at every node,
# bottom chord held by longitudinal ties at x = 1, 3, 5 m (L = 2 m)
def Lcr_out(m):
    g = m[2]
    if g == "top chord":
        return length(m)
    if g == "bottom chord":
        return 2 * PANEL
    return length(m)

print(f"Bay (truss spacing) = {BAY:.3f} m, slope = {math.degrees(math.atan(RISE/(SPAN/2))):.1f} deg")
for s in (S3, S2):
    print(f"{s['name']}: A={s['A']*1e4:.2f} cm2  I={s['I']*1e8:.1f} cm4  "
          f"W={s['W']*1e6:.1f} cm3  i={s['i']*1e2:.2f} cm  {s['kg']:.2f} kg/m")
print()
groups = {}
for idx, m in enumerate(members):
    for k, (N, u, R) in res.items():
        g = groups.setdefault(m[2], dict(Nt=0, Nc=0, Lc=0, util=0))
        n = N[idx]
        s = SEC[m[2]]
        if n > 0:
            ut = n / (s["A"] * FY / GM0)
            g["Nt"] = max(g["Nt"], n)
        else:
            L = max(length(m), Lcr_out(m))
            lam = L / s["i"] / (math.pi * math.sqrt(E / FY))
            Nb = chi(lam) * s["A"] * FY / GM1
            ut = -n / Nb
            g["Nc"] = max(g["Nc"], -n); g["Lc"] = max(g["Lc"], L)
        g["util"] = max(g["util"], ut)

print(f"{'member':14s}{'section':16s}{'max T kN':>10s}{'max C kN':>10s}{'util':>8s}")
for g, v in groups.items():
    print(f"{g:14s}{SEC[g]['name']:16s}{v['Nt']:10.1f}{v['Nc']:10.1f}{v['util']:8.2f}")

print("\nSupport reactions per truss end (kN, +up):")
for k, (N, u, R) in res.items():
    print(f"  {k:28s} V = {R[2*B(0)+1]:6.2f}")

# serviceability: G + Q characteristic
N, u, R = solve(node_loads(G + Q_ROOF))
dmax = -min(u[1::2]) * 1e3
print(f"\nTruss deflection (G+Q, SLS) = {dmax:.1f} mm  (limit L/250 = {SPAN*1e3/250:.0f} mm)")

# ------------------------------------------------------------------ purlin check
# continuous over 8 supports, 1.0 m tributary (plan), bending about axis normal to roof
# conservatively as simply supported (M = wL2/8)
w_d = 1.35 * (G + PURLIN["kg"] * 9.81e-3) + 1.5 * Q_ROOF   # kN/m
w_u = 1.5 * W_UP - 1.0 * G
L = BAY
for name, w in (("gravity", w_d), ("uplift", w_u)):
    M = w * PANEL * L ** 2 / 8
    print(f"Purlin {PURLIN['name']} span {L:.2f} m, {name}: M = {M:.2f} kNm, "
          f"util = {M / (PURLIN['W'] * FY):.2f}")
w_s = G + Q_ROOF + PURLIN["kg"] * 9.81e-3
d = 5 * w_s * PANEL * L ** 4 / (384 * E * PURLIN["I"]) * 1e3
print(f"Purlin deflection (SLS) = {d:.1f} mm  (limit L/200 = {L*1e3/200:.1f} mm)")

# ------------------------------------------------------------------ anchors
down = max(r[2][2*B(0)+1] for r in res.values())
uplift = -min(r[2][2*B(0)+1] for r in res.values())
print(f"\nBase plate: max down = {down:.1f} kN, max uplift = {uplift:.1f} kN per plate (ULS)")

# ------------------------------------------------------------------ steel take-off
tot = {}
for m in members:
    tot.setdefault(SEC[m[2]]["name"], 0)
    tot[SEC[m[2]]["name"]] += length(m)
print("\nSteel per truss:", {k: round(v, 2) for k, v in tot.items()})
