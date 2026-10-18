"""Plot the DXF to a PDF/PNG preview (white paper).

The DXF stores Arabic in logical order, which CAD programs shape themselves; the matplotlib
backend does not apply the bidi algorithm, so the preview converts each text line to visual order.

usage: python preview.py IN.dxf OUT.pdf|OUT.png [dpi]
"""
import sys

import arabic_reshaper
import ezdxf
import matplotlib
from bidi.algorithm import get_display
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration, LineweightPolicy
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

src, dst = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 200

doc = ezdxf.readfile(src)
msp = doc.modelspace()
for e in msp.query("MTEXT"):
    lines = e.text.split("\\P")
    e.text = "\\P".join(get_display(arabic_reshaper.reshape(s)) for s in lines)

x0, y0, x1, y1 = -20.0, -12.0, 66.0, 57.0          # sheet window incl. title block
fig = plt.figure(figsize=(16.54, 16.54 * (y1 - y0) / (x1 - x0)))  # A2 width
ax = fig.add_axes([0, 0, 1, 1])
cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR,
                    lineweight_policy=LineweightPolicy.RELATIVE, lineweight_scaling=0.5)
Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(msp, finalize=False)
ax.set_xlim(x0, x1)
ax.set_ylim(y0, y1)
ax.set_aspect("equal")
ax.axis("off")
fig.savefig(dst, dpi=dpi, facecolor="white")
print("saved", dst)
