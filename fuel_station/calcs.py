"""Design data and calculations shared by the drawings and the report (one source of numbers)."""
from site_base import FRONT, LL, LR, W

PLOT_AREA = (LL + LR) / 2 * W                      # right trapezoid, 2415.25 m2

# above-ground tanks (shown on the site plan); diameter / overall length in metres
TANKS = [
    # tag, product (EN), product (AR), capacity m3, D, L, compartment
    ("T-01", "GAS OIL", "زيت الغاز", 54, 2.75, 10.0, "C1"),
    ("T-02", "LPG", "الغاز السائل", 23, 2.30, 7.0, "C2"),
    ("T-03", "LPG", "الغاز السائل", 23, 2.30, 7.0, "C2"),
    ("T-04", "GASOLINE", "البنزين", 54, 2.75, 10.0, "C3"),
    ("T-05", "GASOLINE", "البنزين", 54, 2.75, 10.0, "C3"),
    ("T-06", "KEROSENE", "النفط الأبيض", 54, 2.75, 10.0, "C3"),
]

DISPENSERS = [
    # island, product, number of dispensers
    ("I-1", "GAS OIL", 2),
    ("I-2", "LPG", 2),
    ("I-3", "GASOLINE", 2),
    ("I-4", "KEROSENE (YARD)", 2),
    ("I-5", "KEROSENE (HAND CARTS)", 1),
]

SOIL_BEARING = 100      # kN/m2, assumed until a soil investigation report is available


def summary():
    by_product = {}
    for _tag, prod, _ar, cap, *_ in TANKS:
        n, v = by_product.get(prod, (0, 0))
        by_product[prod] = (n + 1, v + cap)
    return {
        "plot_area": PLOT_AREA,
        "front": FRONT,
        "by_product": by_product,
        "total_storage": sum(t[3] for t in TANKS),
        "dispensers": sum(d[2] for d in DISPENSERS),
    }
