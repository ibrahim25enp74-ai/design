"""Plot geometry shared by the site plan and the discipline drawing sets (metres).

Plot frame F: origin at the rear-left plot corner D, x along the 50 m rear boundary,
y pointing into the plot.  Sheet frame: street front horizontal, front-left corner A at 0,0, y up.
"""
import math

from shapely.geometry import Polygon

W, LL, LR = 50.0, 30.59, 66.02            # rear, left side, right side
FRONT = math.hypot(W, LR - LL)            # 61.28
TH = math.atan2(LR - LL, W)               # front makes this angle with the rear boundary
CT, ST = math.cos(TH), math.sin(TH)
U = (W / FRONT, (LR - LL) / FRONT)        # along the front, A -> B
NIN = (U[1], -U[0])                       # from the front into the plot
NOUT = (-U[1], U[0])
WT = 0.25                                 # wall thickness

D, C, B, A = (0.0, 0.0), (W, 0.0), (W, LR), (0.0, LL)
PLOT = Polygon([D, C, B, A])
INNER = PLOT.buffer(-WT, join_style=2)


def o(p):
    """Plot frame -> sheet frame."""
    x, y = p[0], LL - p[1]
    return (x * CT - y * ST, x * ST + y * CT)


def sang(a_f):
    """Direction angle in the plot frame (deg, towards +y) -> sheet angle."""
    return math.degrees(TH) - a_f


def fr(s, t=0.0):
    """Point s metres along the front from A, t metres inwards."""
    return (s * U[0] + t * NIN[0], LL + s * U[1] + t * NIN[1])


def mv(p, v, k=1.0):
    return (p[0] + k * v[0], p[1] + k * v[1])


def front_box(s0, s1, t0, t1):
    return Polygon([fr(s0, t0), fr(s1, t0), fr(s1, t1), fr(s0, t1)])
