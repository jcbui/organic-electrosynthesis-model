#!/usr/bin/env python3
"""Figure 6 hand-off: the generated panels on the author's canvas, as a PNG and an editable vector PDF.

`combined_figure.py` (FIG6_INLINE=1) draws Figure 6 with the six reaction schemes placed by its own
ink test, on a 6.50 x 7.52 in canvas that leaves a white band above panels (d-f) where the scheme
strip used to be. The author's artwork closes that band -- his page is the same figure with everything
below panels (a-c) moved up -- so this script does the same to the generated render: it removes
CLOSE_PX rows of pure white between the two blocks and writes

    Figures/Figure6_generated_<tag>_600dpi.png      3900 x 4325 px, the size the manuscript places
    Figures/Figure6_generated_<tag>.pdf             the same page as vector, FLAT (Matplotlib's own stream, two clipped copies); the interim artwork

Nothing is redrawn: the PNG is the generator's own pixels with one white band cut out (asserted white),
and the PDF is the generator's own content stream under two clips, with the upper copy moved down by that band.

    cd Section4_Model && FIG6_INLINE=1 python figs/combined_figure.py && python figs/make_fig6_handoff.py
"""
import os, sys
import numpy as np
from PIL import Image
try:
    import pymupdf as fitz
except ImportError:
    import fitz

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PNG = os.path.join(HERE, "combined_figure_grounded_inline.png")
PDF = os.path.join(HERE, "combined_figure_grounded_inline.pdf")
TAG = "20261006b"   # 2026-10-06 night: panels (d) and (g) carry the anisole bromination in place of the Hofmann row
# (the earlier "20261006" page -- (f), (g), (h) after the chemistry review -- is left untouched beside it)
OUT_PNG = os.path.join(ROOT, "Figures", "Figure6_generated_%s_600dpi.png" % TAG)
OUT_PDF = os.path.join(ROOT, "Figures", "Figure6_generated_%s.pdf" % TAG)
CLOSE_PX = 187            # rows of white the author's layout removes (measured off his page: 4512 -> 4325 px)
EXPECT = (3900, 4325)
DPI = 600.0


def main():
    im = Image.open(PNG).convert("RGB")
    a = np.asarray(im)
    if a.shape[1] != EXPECT[0] or a.shape[0] != EXPECT[1] + CLOSE_PX:
        raise SystemExit("the generated render is %d x %d px; expected %d x %d" % (a.shape[1], a.shape[0], EXPECT[0], EXPECT[1] + CLOSE_PX))
    white = (a.min(axis=(1, 2)) >= 250)
    # the band between the first row of panels and the second: the longest run of white rows in the upper half
    best, run0 = (0, 0), None
    for y in range(600, a.shape[0] // 2 + 400):
        if white[y]:
            run0 = y if run0 is None else run0
            if y - run0 + 1 > best[0]:
                best = (y - run0 + 1, run0)
        else:
            run0 = None
    n, y0 = best
    if n < CLOSE_PX + 8:
        raise SystemExit("the white band above panels (d-f) is %d px tall; %d px cannot be removed from it" % (n, CLOSE_PX))
    cut = y0 + (n - CLOSE_PX) // 2
    if not white[cut:cut + CLOSE_PX].all():
        raise SystemExit("the rows to be removed are not white")
    out = np.concatenate([a[:cut], a[cut + CLOSE_PX:]], axis=0)
    Image.fromarray(out).save(OUT_PNG, dpi=(DPI, DPI), optimize=True)
    print("PNG: removed rows %d-%d (white band %d px at row %d) -> %s, %d x %d px" % (cut, cut + CLOSE_PX, n, y0, os.path.relpath(OUT_PNG, ROOT), out.shape[1], out.shape[0]))

    # the vector page, same cut (PDF y runs down the page; 72/600 pt per px).
    # FLAT, not form XObjects (2026-10-05, evening): laying the two pieces down with show_pdf_page wraps each in a Form
    # XObject, which Illustrator imports as nested clipping groups whose contents will not group ("the reactions aren't
    # grouping properly" -- author). The page the author edited successfully that afternoon was Matplotlib's own content
    # stream, so this writes the same thing: the original stream twice, each copy under a rectangular clip, the upper
    # copy translated down by the band, on the same page object with the same /Resources and fonts.
    src = fitz.open(PDF)
    pg = src[0]
    W, H = pg.rect.width, pg.rect.height
    k = 72.0 / DPI
    yc, dy = cut * k, CLOSE_PX * k
    y_top, y_bot = H - yc, H - yc - dy                       # the band in PDF coordinates (y up)
    body = pg.read_contents()
    lower = b"q 0 0 %.4f %.4f re W n\n" % (W, y_bot) + body + b"\nQ\n"
    upper = b"q 0 %.4f %.4f %.4f re W n 1 0 0 1 0 %.4f cm\n" % (y_bot, W, H - dy - y_bot, -dy) + body + b"\nQ\n"
    xrefs = pg.get_contents()
    src.update_stream(xrefs[0], lower + upper)
    for x in xrefs[1:]:
        src.update_stream(x, b"")
    pg.set_mediabox(fitz.Rect(0, 0, W, H - dy))
    src.save(OUT_PDF, garbage=1, deflate=True)
    chk = fitz.open(OUT_PDF)[0]
    if chk.get_xobjects() and any(x[1] == "Form" for x in chk.get_xobjects()):
        raise SystemExit("the hand-off page carries a Form XObject; it must be flat")
    # the two outputs must be the same picture
    pm = fitz.open(OUT_PDF)[0].get_pixmap(dpi=150, alpha=False)
    v = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, 3).astype(int)
    r = np.asarray(Image.fromarray(out).resize((pm.width, pm.height), Image.LANCZOS)).astype(int)
    raw = float((np.abs(v - r).max(2) > 90).mean())
    # the raw count is mostly resampling: every glyph and line edge differs by a pixel between the 150 dpi raster of the
    # vector page and the Lanczos-downsampled 600 dpi PNG. A pixel counts only if no pixel within one of it matches, so
    # a different picture (a moved panel, a missing curve) still registers and edge noise does not.
    best = np.full(v.shape[:2], 999)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            best = np.minimum(best, np.abs(v - np.roll(np.roll(r, oy, 0), ox, 1)).max(2))
    diff = float((best > 90).mean())
    print("PDF: %s, %.2f x %.2f pt; %.2f %% of pixels differ from the PNG at 150 dpi, %.2f %% beyond a 1 px shift (rasteriser differences)"
          % (os.path.relpath(OUT_PDF, ROOT), W, H - dy, 100 * raw, 100 * diff))
    if diff > 0.02:
        raise SystemExit("the vector page and the PNG are not the same picture")


if __name__ == "__main__":
    main()
