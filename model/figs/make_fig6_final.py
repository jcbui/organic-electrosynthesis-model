"""Figure 6: the author's final artwork, rasterised live from his Illustrator PDF.

The source is `Figures/Figure6_with_schemes_20261002.pdf` -- the author's own placement of the six
reaction schemes over the generated panels (2026-10-02, "these are the final figs").  It is read and
never written, the convention Figure 8 and the SPECS plate already follow.  This script draws
nothing: it rasterises the artboard at 600 dpi to the file the manuscript embeds, so an edit to the
PDF changes the figure and G-FIGRUN reports the render stale until it is re-run.  The author's own
PNG export is left untouched beside it and is NOT what the manuscript embeds -- same arrangement as
Figure 8's `..._v3.png`.

WHY THIS FIGURE NEEDED ITS OWN SCRIPT.  Until now Figure 6 WAS `combined_figure.py`'s output, and
every artwork gate compared the embedded bytes to that render.  It is now hand-placed artwork, so
that comparison no longer reaches the shipped figure, and the model-to-figure path and the
figure-to-document path have to be watched separately.

THE SECOND ASSERTION IS THE ONE THAT MATTERS.  The artwork was laid out over
`figs/combined_figure_grounded_inline.png` as it stood at the pinned md5 below.  That render is a
MODEL OUTPUT -- every curve, marker, threshold and printed rate constant in it comes from the solved
matrix -- and an Illustrator file cannot follow a model change on its own.  So if that render moves,
this figure is stale and has to be re-made by hand.  The gate says so instead of letting it pass,
which is the exact failure this repository has shipped before: author artwork frozen against a model
that moved underneath it, behind a green suite.

    cd Section4_Model && python3 figs/make_fig6_final.py
"""
import hashlib, os, sys
try:
    import pymupdf as fitz
except ImportError:                       # older PyMuPDF exposes only the `fitz` name
    import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))            # the project folder
SRC = os.path.join(ROOT, "Figures", "Figure6_with_schemes_20261002.pdf")
AUTHOR_PNG = os.path.join(ROOT, "Figures", "Figure6_with_schemes_20261002.png")
OUT = os.path.join(ROOT, "Figures", "Figure6_with_schemes_20261002_600dpi.png")
PANELS = os.path.join(HERE, "combined_figure_grounded_inline.png")
DPI = 600
EXPECT = (3900, 4319)                     # 6.50 x 7.20 in at 600 dpi
PANELS_MD5 = "21a3d0e046454f2361f1b784589f1d3c"


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def main():
    for p in (SRC, PANELS):
        if not os.path.exists(p):
            raise SystemExit("missing %s" % p)

    # (ii) provenance: the hand placement sits on a MODEL render, which can move without it.
    got = md5(PANELS)
    if got != PANELS_MD5:
        raise SystemExit(
            "STALE: Figure 6's artwork was laid out over combined_figure_grounded_inline.png at\n"
            "  %s, and that render is now\n  %s.\n"
            "The curves, markers, thresholds or rate constants the author placed the schemes over\n"
            "have changed, and an Illustrator file cannot follow a model change. Re-make the figure\n"
            "from the new render and re-pin PANELS_MD5 -- do not re-pin it on its own."
            % (PANELS_MD5, got))

    doc = fitz.open(SRC)
    if doc.page_count != 1:
        raise SystemExit("%s has %d pages; expected 1" % (os.path.basename(SRC), doc.page_count))
    pix = doc[0].get_pixmap(dpi=DPI)
    if (pix.width, pix.height) != EXPECT:
        raise SystemExit("artboard rasterises to %d x %d px, expected %d x %d -- the page size moved"
                         % (pix.width, pix.height, *EXPECT))
    pix.set_dpi(DPI, DPI)
    pix.save(OUT)

    # control: the author's own export of the same PDF must agree with this rasterisation, which is
    # what proves the two files he delivered are one figure and not two. Antialiasing differs, so the
    # test is on content, not bytes.
    note = ""
    if os.path.exists(AUTHOR_PNG):
        import numpy as np
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        a = np.asarray(Image.open(OUT).convert("RGB"), dtype=int)
        b = np.asarray(Image.open(AUTHOR_PNG).convert("RGB"), dtype=int)
        if a.shape != b.shape:
            raise SystemExit("the author's PNG is %s and this render is %s" % (b.shape, a.shape))
        diff = float((np.abs(a - b).max(2) > 12).mean())
        if diff > 0.03:
            raise SystemExit("the author's PNG differs from his PDF over %.2f %% of the canvas; they "
                             "are not the same figure" % (100 * diff))
        note = "  (author's own export agrees to %.2f %%)" % (100 * diff)

    print("wrote %s  %d x %d px at %d dpi%s"
          % (os.path.relpath(OUT, ROOT), pix.width, pix.height, DPI, note))


if __name__ == "__main__":
    sys.exit(main())
