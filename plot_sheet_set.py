"""Plot every A3 sheet of the model space into one A3 PDF, ordered by sheet number."""
import os
import re
import sys

import ezdxf
import pymupdf
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext, layout, pymupdf as pdf_backend
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration, LineweightPolicy

SRC, DST = sys.argv[1], sys.argv[2]
doc = ezdxf.readfile(SRC)
msp = doc.modelspace()

sheets = []
for e in msp.query('LWPOLYLINE[layer=="A3_SHEET"]'):
    xs, ys = zip(*e.get_points("xy"))
    sheets.append((min(xs), min(ys), max(xs), max(ys)))
sheets = sorted(set(sheets))

texts = [e for e in msp.query("TEXT") if e.dxf.layer.startswith("TB")]


def image_missing(e):
    if e.dxftype() != "IMAGE":
        return False
    img = e.image_def
    name = img.dxf.filename.replace("\\", "/") if img else ""
    return not name or not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(SRC)), name))


# an IMAGE whose file is not next to the DXF would plot as a big filename
extents = [(e, bbox.extents([e])) for e in msp if not image_missing(e)]


def sheet_number(s):
    """The number written under 'SHEET' in the title block ('01' ... '21')."""
    x0, y0, x1, y1 = s
    inside = [t for t in texts if x0 < t.dxf.insert.x < x1 and y0 < t.dxf.insert.y < y1]
    nums = [t for t in inside if re.fullmatch(r"\d{2}", t.dxf.text.strip())]
    labels = [t for t in inside if t.dxf.text.strip() == "SHEET"]
    if not nums or not labels:
        return 999
    lab = labels[0].dxf.insert
    best = min(nums, key=lambda t: (t.dxf.insert - lab).magnitude)
    return int(best.dxf.text)


config = Configuration(
    background_policy=BackgroundPolicy.WHITE,
    color_policy=ColorPolicy.COLOR,  # colour 7 plots black on white paper
    lineweight_policy=LineweightPolicy.ABSOLUTE,
    min_lineweight=0.13,
)
page = layout.Page(420, 297, layout.Units.mm, margins=layout.Margins.all(0))

out = pymupdf.open()
for s in sorted(sheets, key=sheet_number):
    x0, y0, x1, y1 = s
    ents = [e for e, b in extents
            if b.has_data and b.extmax.x > x0 and b.extmin.x < x1 and b.extmax.y > y0 and b.extmin.y < y1]
    backend = pdf_backend.PyMuPdfBackend()
    ctx = RenderContext(doc)
    ctx.set_current_layout(msp)
    ctx.current_layout_properties.set_colors("#ffffff")  # white paper: colour 7 -> black
    backend.set_background("#ffffff")
    Frontend(ctx, backend, config=config).draw_entities(ents)
    settings = layout.Settings(fit_page=True, crop_at_margins=True)
    # the sheet border defines the plotted area
    backend.player().crop_rect((x0, y0), (x1, y1), distance=0.01)
    data = backend.get_pdf_bytes(page, settings=settings,
                                 render_box=ezdxf.math.BoundingBox2d([(x0, y0), (x1, y1)]))
    out.insert_pdf(pymupdf.open("pdf", data))
    print(f"sheet {sheet_number(s):02d} plotted")

out.save(DST, garbage=3, deflate=True)
