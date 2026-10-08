"""Figure 6: the final artwork, rasterised live from the Illustrator-editable PDF.

STATE ON 2026-10-05 (after the reaction audit). The audit corrected the electron counts and substrate
diffusivities of several rows, which moved the curves of panels (e), (g) and (h) -- the nickel curve of
(h) now runs BELOW the cobalt-hydride one. No string on the figure face changed (137 strings, identical
before and after; `FIG6_DUMP_TEXT`), but the author's hand placement of 2026-10-05 sat over the old curves
and could not follow them. He re-placed the schemes and curve labels the same evening over the new render
(`Figures/Figure6_for_Illustrator_20261005b_JCB.pdf`, a 6.50 x 7.073 in artboard), which is SRC now, pinned
to the render he worked over. His morning artwork (`..._20261005_JCB.pdf`) is kept untouched beside it, and
`figs/make_fig6_handoff.py` still writes the generator's own placement on a closed-up canvas for the next
time the model moves before he can re-place.

What follows describes the arrangement, which is unchanged:

The source is `Figures/Figure6_for_Illustrator_20261005_JCB.pdf` -- the author's own placement of the
six reaction schemes over the generated panels (2026-10-05, "FIXED"; it supersedes his 2026-10-02
placement, which was made over a render whose cobalt scheme drew the wrong reaction).  It is read and
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
# 2026-10-05, 20:41: the author's placement of the six schemes on the 20261005c page (the page is FLAT -- Matplotlib's own
# stream under two clips -- because the form-XObject page before it would not let the schemes group in Illustrator). The
# NHPI row's rate constant had been corrected after his 20261005b placement, so that artwork drew a retired curve; this
# one is drawn over the corrected render pinned below.
# 2026-10-07, 20:36: the author's placement of the (g)/(h) schemes on the 20261006b hand-off page, with the three x_k
# markers of (d)-(f) deleted (the generator stopped drawing them the same evening, so the pinned render below has none)
SRC = os.path.join(ROOT, "Figures", "Figure6_generated_20261006b_JCB.pdf")
OUT = os.path.join(ROOT, "Figures", "Figure6_final_20261007_600dpi.png")
PANELS = os.path.join(HERE, "combined_figure_grounded_inline.png")
DPI = 600
EXPECT = (3900, 4325)                     # 6.50 x 7.073 in at 600 dpi (the author's 2026-10-05 evening artboard)
PANELS_MD5 = "fe91071cc563eb3834048d7b1198095b"


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

    # CONTROL. The author shipped no PNG export this time, so the weaker "his two files agree"
    # test is unavailable. The stronger one is available instead, and it is the one that matters:
    # his artwork must be the MODEL RENDER with the schemes moved, and nothing else. He closed the
    # vertical gaps between the three panel rows (7.52 -> 7.208 in), so the comparison is per BAND,
    # each at its own offset -- a band whose HEIGHT changed would mean content was rescaled, which an
    # Illustrator resize does silently and which would put every curve off its own axis.
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    art = np.asarray(Image.open(OUT).convert("RGB"), dtype=int)
    mod = np.asarray(Image.open(PANELS).convert("RGB"), dtype=int)
    if art.shape[1] != mod.shape[1]:
        raise SystemExit("the artwork is %d px wide and the render %d: the width must not change"
                         % (art.shape[1], mod.shape[1]))

    def bands(img, gap=25, thr=3):
        """Vertical runs of ink, i.e. the panel rows."""
        prof = (img.min(2) < 230).sum(1)
        rows = np.nonzero(prof > thr)[0]
        out, start, prev = [], rows[0], rows[0]
        for r in rows[1:]:
            if r - prev > gap:
                out.append((start, prev)); start = r
            prev = r
        out.append((start, prev))
        return out

    ba, bm = bands(art), bands(mod)
    if len(ba) != len(bm):
        raise SystemExit("the artwork has %d content bands and the render %d -- a panel row was "
                         "added or lost" % (len(ba), len(bm)))
    worst_h, worst_d, worst_px = 0.0, 0.0, 0
    for (a0, a1), (m0, m1) in zip(ba, bm):
        ha, hm = a1 - a0, m1 - m0
        # a RESCALE moves a 1000-px panel row by tens of pixels; a 1-2 px change on the 64-px axis-label strip is
        # Illustrator's rasteriser trimming an antialiased row (3.1 % on 2026-10-05, on an artwork whose bands were
        # otherwise identical to the generator's to the pixel), so the height test has a 4-px floor
        if abs(ha - hm) > 4:
            worst_h = max(worst_h, abs(ha - hm) / max(1, hm))
        worst_px = max(worst_px, abs(ha - hm))
        seg = art[a0:a1 + 1]
        # COARSE then FINE: the offset search is over ~400 positions and each full-resolution
        # comparison is a 3900 x 1500 array, so the naive loop takes minutes. Find the offset on a
        # 1/8 decimation, then refine +/-8 at full resolution -- same answer, ~60x less work.
        F = 8
        segd = seg[::F, ::F]
        coarse, cbest = 0, 1.0
        for off in range(-60, 360, F):
            s0, s1 = a0 + off, a0 + off + seg.shape[0]
            if s0 < 0 or s1 > mod.shape[0]:
                continue
            f = float((np.abs(mod[s0:s1:F, ::F] - segd).max(2) > 40).mean())
            if f < cbest:
                cbest, coarse = f, off
        best = 1.0
        for off in range(coarse - F, coarse + F + 1):
            s0, s1 = a0 + off, a0 + off + seg.shape[0]
            if s0 < 0 or s1 > mod.shape[0]:
                continue
            best = min(best, float((np.abs(mod[s0:s1] - seg).max(2) > 40).mean()))
        worst_d = max(worst_d, best)
    if worst_h > 0.03:
        raise SystemExit("a panel row's height moved by %.1f %%: the artwork was RESCALED, not just "
                         "repositioned, and the curves no longer sit on their own axes" % (100 * worst_h))
    if worst_d > 0.08:
        raise SystemExit("a panel row differs from the model render over %.1f %% of its area at every "
                         "offset: the artwork is not that render with the schemes moved" % (100 * worst_d))
    note = ("  (every panel row matches the model render at its own offset: heights to %.1f %% beyond a 4-px floor "
            "(worst %d px), content to %.1f %%)" % (100 * worst_h, worst_px, 100 * worst_d))

    print("wrote %s  %d x %d px at %d dpi%s"
          % (os.path.relpath(OUT, ROOT), pix.width, pix.height, DPI, note))


if __name__ == "__main__":
    sys.exit(main())
