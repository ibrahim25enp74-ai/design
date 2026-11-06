"""Structural check of the 6.70 x 15.00 m skylight: portal frames of SHS 80x80x5
every 1.50 m (pinned bases, no eave tie) with a short collar tie SHS 80x80x2 under the ridge.

2D frame (beam elements, direct stiffness), EN 1993-1-1, S235.
Run:  python3 frame_calc.py
"""
import math
import numpy as np

# ---------------------------------------------------------------- geometry (m)
SPAN = 6.70          # leg axis to leg axis (parapet axes 6.00 + 2 x 0.35)
LENGTH = 15.0
BAY = 1.50           # frame spacing -> 11 frames
LEG = 0.50           # leg below the top of the parapet (house roof)
EAVE = 0.60          # eave node above the top of the parapet (room for vent windows)
RISE = 0.50          # ridge above eave
N_PURLIN_SP = 12     # purlin spaces across -> 0.56 m cells (even: ridge purlin)
N_FRAMES = round(LENGTH / BAY) + 1

E, FY = 210e6, 235e3     # kPa


def shs(b, t):
    bi = b - 2 * t
    A = b * b - bi * bi - (4 - math.pi) * ((2 * t) ** 2 - t ** 2)
    I = (b ** 4 - bi ** 4) / 12 * 0.96
    Wpl = (b * b ** 2 - bi * bi ** 2) / 4 * 0.96
    return dict(name=f"SHS {b*1e3:.0f}x{b*1e3:.0f}x{t*1e3:.0f}", A=A, I=I, W=I / (b / 2), Wpl=Wpl,
                i=math.sqrt(I / A), kg=A * 7850)


FRAME = shs(0.080, 0.005)        # legs + rafters
PURLIN = shs(0.080, 0.002)
TIE_D = 0.016
TIE_A = math.pi * TIE_D ** 2 / 4

# ---------------------------------------------------------------- loads kN/m2 (plan)
G_SHEET, G_DUST, Q, W_UP = 0.10, 0.15, 0.60, 1.00
G = G_SHEET + G_DUST

# ---------------------------------------------------------------- model
xs = [i * SPAN / N_PURLIN_SP for i in range(N_PURLIN_SP + 1)]
ytop = lambda x: EAVE + RISE * (1 - abs(x - SPAN / 2) / (SPAN / 2))
nodes = [(0.0, -LEG)] + [(x, ytop(x)) for x in xs] + [(SPAN, -LEG)]
if SPAN / 2 not in xs:   # make sure the ridge is a node
    raise SystemExit("odd number of purlin spaces needs a ridge node")
iBL, iBR = 0, len(nodes) - 1
iKL, iKR = 1, len(nodes) - 2
beams = [(iBL, iKL)] + [(k, k + 1) for k in range(1, len(nodes) - 2)] + [(iKR, iBR)]


COLLAR = (6, 8)  # collar tie between rafter nodes 6 and 8 (1.12 m long, 83 mm below the ridge), SHS 80x80x2


def analyse(w_line, tie=True):
    """w_line kN/m on plan, + down. Returns end moments, axial forces, tie force, reactions, disp."""
    n = len(nodes); K = np.zeros((3 * n, 3 * n)); F = np.zeros(3 * n)
    elems = []
    for a, b in beams:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        L = math.hypot(x2 - x1, y2 - y1); c, s = (x2 - x1) / L, (y2 - y1) / L
        EA, EI = E * FRAME["A"], E * FRAME["I"]
        kl = np.array([[EA/L, 0, 0, -EA/L, 0, 0],
                       [0, 12*EI/L**3, 6*EI/L**2, 0, -12*EI/L**3, 6*EI/L**2],
                       [0, 6*EI/L**2, 4*EI/L, 0, -6*EI/L**2, 2*EI/L],
                       [-EA/L, 0, 0, EA/L, 0, 0],
                       [0, -12*EI/L**3, -6*EI/L**2, 0, 12*EI/L**3, -6*EI/L**2],
                       [0, 6*EI/L**2, 2*EI/L, 0, -6*EI/L**2, 4*EI/L]])
        T = np.zeros((6, 6))
        for o in (0, 3):
            T[o:o+2, o:o+2] = [[c, s], [-s, c]]; T[o+2, o+2] = 1
        d = [3*a, 3*a+1, 3*a+2, 3*b, 3*b+1, 3*b+2]
        K[np.ix_(d, d)] += T.T @ kl @ T
        elems.append((d, kl, T, L))
    if tie:
        (x1, y1), (x2, y2) = nodes[iKL], nodes[iKR]
        k = E * TIE_A / (x2 - x1)
        d = [3*iKL, 3*iKR]
        K[np.ix_(d, d)] += k * np.array([[1, -1], [-1, 1]])
    if COLLAR:
        a, b = COLLAR
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        k = E * PURLIN["A"] / (x2 - x1)
        d = [3*a, 3*b]
        K[np.ix_(d, d)] += k * np.array([[1, -1], [-1, 1]])
    # nodal loads from purlins + self weight
    trib = SPAN / N_PURLIN_SP
    for k in range(1, len(nodes) - 1):
        t = trib / 2 if k in (iKL, iKR) else trib
        if k in (iKL, iKR):
            t += 0.10                     # eave overhang
        F[3*k+1] -= w_line * t
    fixed = [3*iBL, 3*iBL+1, 3*iBR, 3*iBR+1]          # pinned bases
    free = [i for i in range(3*n) if i not in fixed]
    u = np.zeros(3*n)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    R = K @ u - F
    forces = [kl @ (T @ u[d]) for d, kl, T, L in elems]
    Ntie = E * TIE_A / SPAN * (u[3*iKR] - u[3*iKL]) if tie else 0.0
    return forces, Ntie, R, u


def line_load(g_fac, q_fac, w_fac):
    sw = (FRAME["kg"] * 1.03 + PURLIN["kg"] * (N_PURLIN_SP + 1) * BAY / SPAN) * 9.81e-3   # kN/m
    return g_fac * (G * BAY + sw) + q_fac * Q * BAY - w_fac * W_UP * BAY


def chi(lb, a=0.49):
    ph = 0.5 * (1 + a * (lb - 0.2) + lb ** 2)
    return min(1, 1 / (ph + math.sqrt(max(ph ** 2 - lb ** 2, 0))))


def check(name, w, tie):
    forces, Nt, R, u = analyse(w, tie)
    Mmax = max(max(abs(f[2]), abs(f[5])) for f in forces)
    Nmax = max(max(abs(f[0]), abs(f[3])) for f in forces)
    rafter_len = math.hypot(SPAN / 2, RISE)
    lb = rafter_len / FRAME["i"] / (math.pi * math.sqrt(E / FY))
    Nb = chi(lb) * FRAME["A"] * FY
    Mrd = FRAME["Wpl"] * FY
    util = Nmax / Nb + 1.5 * Mmax / Mrd if Nmax > 0 else Mmax / Mrd     # simple, conservative interaction
    util = max(Mmax / Mrd, Nmax / Nb + Mmax / Mrd)
    print(f"{name:34s} w={w:6.2f} kN/m  Mmax={Mmax:5.2f} kNm  Nmax={Nmax:5.1f} kN  "
          f"tie={Nt:5.1f} kN  util={util:4.2f}  base V={R[3*iBL+1]:5.1f} H={R[3*iBL]:5.1f} kN  "
          f"ridge dy={u[3*(1 + N_PURLIN_SP // 2) + 1]*1e3:6.1f} mm")
    return Nt


print(f"frames: {N_FRAMES} @ {BAY} m, cells {SPAN / N_PURLIN_SP:.3f} m, slope "
      f"{math.degrees(math.atan(RISE / (SPAN / 2))):.1f} deg; frame {FRAME['name']} ({FRAME['kg']:.2f} kg/m), "
      f"purlins {PURLIN['name']}, collar between nodes {COLLAR}")
check("ULS 1.35G+1.5Q", line_load(1.35, 1.5, 0), False)
check("ULS 1.0G-1.5W uplift", line_load(1.0, 0, 1.5), False)
check("SLS G+Q   (limit L/200 = 33 mm)", line_load(1.0, 1.0, 0), False)
check("SLS G-W", line_load(1.0, 0, 1.0), False)

# purlins, simply supported over 1.5 m
trib = SPAN / N_PURLIN_SP
w = 1.35 * (G * trib + PURLIN["kg"] * 9.81e-3) + 1.5 * Q * trib
print(f"purlin {PURLIN['name']}: M={w*BAY**2/8:.2f} kNm util={w*BAY**2/8/(PURLIN['W']*FY):.2f}")
