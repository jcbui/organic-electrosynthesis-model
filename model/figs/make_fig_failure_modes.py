"""Figure 8 (Section 5): the failure-modes component map, rasterised from the author's artwork.

The source is `Figures/Organic ESynth Failure Modes Figure_v3.pdf`, read live and never copied (the
SPECS convention of 2026-09-07).  This script does no drawing of its own; it renders the artboard at
600 dpi to `Figures/Organic ESynth Failure Modes Figure_v3_600dpi.png`, the file the manuscript
embeds, so an edit to the artwork changes the figure and G-FIGRUN reports the render stale until it
is re-run.

WHY THE .pdf AND NOT THE .ai (2026-09-28).  The .ai carries an Illustrator private-data stream
(`AIPrivateData1..6`, `/LastModified D:20260908110722`) that no PDF renderer reads, so that file says
two different things: its PDF content stream carries the 2026-09-21 label fix while Illustrator still
reads "Hofmann elimination" from the private blocks -- which are byte-identical before and after that
edit.  The author re-made the label change in Illustrator and exported this PDF on 2026-09-28, so the
PDF is the current artwork and the .ai is behind it.  The PDF is read and never written.

REVERTED 2026-09-29 (author: "I don't like the letter legend it's ugly can we just revert to what it
was originally").  The A-L letter tokens `fig8_letters.py` drew over the leaders are NOT drawn any
more, and the caption's legend went with them; the figure is the author's artwork rasterised and
nothing else.  `fig8_letters.py` is kept on disk unused -- re-adding the call and the caption legend
is all it takes -- and `verify_fig8_20260928.py` now asserts the tokens are ABSENT, so a re-add has
to be deliberate.  Jonas Rein's comment about crossing leaders is therefore OPEN again, and the
author's ruling is that re-routing them waits for the revision round.

Why 600 dpi over the full media box: the raster v80 embedded (2026-09-08 01:30) was 16000 x 10142 px,
which is exactly the 1920 x 1217 pt media box at 600 dpi, and every figure in the manuscript is 600 dpi
(author instruction, 2026-09-07). The size is asserted so a changed artboard cannot pass silently.
"""
import os, sys
try:
    import pymupdf as fitz
except ImportError:                       # older PyMuPDF exposes only the `fitz` name
    import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))            # the project folder
AI = os.path.join(ROOT, "Figures", "Organic ESynth Failure Modes Figure_v3.pdf")
OUT = os.path.join(ROOT, "Figures", "Organic ESynth Failure Modes Figure_v3_600dpi.png")
DPI = 600
EXPECT = (16000, 10142)

doc = fitz.open(AI)
if doc.page_count != 1:
    sys.exit(f"expected one artboard, found {doc.page_count}")
page = doc[0]
pix = page.get_pixmap(dpi=DPI, alpha=False)
if (pix.width, pix.height) != EXPECT:
    sys.exit(f"artboard rasterises to {pix.width} x {pix.height}, expected {EXPECT}: the media box changed")
pix.save(OUT)
print(f"media box {page.rect.width:.0f} x {page.rect.height:.0f} pt -> {pix.width} x {pix.height} px at {DPI} dpi")
print(f"wrote {OUT}")
