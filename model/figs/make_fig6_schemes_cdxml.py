#!/usr/bin/env python3
"""The six reaction schemes of Figure 6 (g) and (h), drawn in ChemDraw.

Author, 2026-10-02: "those molecules look terrible, generate proper structures using chemdraw".
They were matplotlib stick figures at 5-6 pt -- fine as a sketch, not as chemistry. These are real
ChemDraw structures in Figure 2's own document style (bond 14.40, line 1.13, Arial atom labels), the
same pipeline Figures 2 and 3 use.

Each scheme is drawn in its own horizontal band of one CDXML page; after ChemDraw renders the page to
a vector PDF, each band is cropped to its own ink and written as a TRANSPARENT PNG at 1200 dpi, so
combined_figure.py can lay it into a panel rotated to its curve's slope without a white box behind it.
The resolution is deliberate: the schemes are rotated when placed, and a raster rotated at its final
output resolution goes soft -- at 1200 dpi into a 600 dpi figure the resampling is invisible.

Which transformation each one is, and where it comes from (data/reactions_50.csv):
  (g) Br-mediated Hofmann rearrangement  Malviya & Cantillo OPRD 2023: 2-phenylacetamide -> carbamate,
                                         drawn as the group change it is, amide -> methyl carbamate
  (g) ACT alcohol oxidation              Zhong & Stahl OPRD 2021: primary alcohol -> carboxylic acid
  (g) NHPI allylic C-H oxidation         Horn & Baran Nature 2016: valencene -> nootkatone, i.e. an
                                         allylic methylene oxidised to the enone
  (h) Ni-XEC                             Kelly et al. OPRD 2026: aryl bromide + alkyl bromide coupled
  (h) Co-H Markovnikov hydroamination    Gnaim et al. Nature 2022: N on the substituted carbon
  (h) Co(salen) aza-Wacker cyclization   Cai & Xu Nat. Commun. 2021: an N-tethered alkene closes

    python3 figs/make_fig6_schemes_cdxml.py [--force]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cdxml_style as cdx
from cdxml_style import Doc, Mol, emit_mol, L

OUT_DIR = os.path.join(HERE, "fig6_schemes")
OUT_CDXML = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Figures", "Fig6_schemes.cdxml")
PAGE_MARGIN = 18.0
BAND = 82.0                     # vertical pitch of one scheme's band on the page
DX, DY = 12.47, 7.20            # one bond of a 120-degree chain

def _trim(path, pad=6):
    """Crop a transparent PNG to its own ink; returns the kept box in pixels so the VECTOR crop can
    be taken from the same place."""
    import numpy as np
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    ink = (a[:, :, :3].min(2) < 200) & (a[:, :, 3] > 8)      # the drawing, not the painted white page
    ys, xs = np.nonzero(ink)
    if not len(xs):
        raise SystemExit("%s is blank" % path)
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad),
           min(im.width, xs.max() + 1 + pad), min(im.height, ys.max() + 1 + pad))
    im.crop(box).save(path)
    return box


KEYS = ["hofmann", "act", "nhpi", "nixec", "coh", "aza"]
# each scheme is drawn in the colour of the curve it belongs to, which is what ties the two together
# in the figure. Doing it HERE rather than by tinting a raster is what keeps the schemes vector all
# the way into the figure's PDF. COLORTABLE entry n carries colour index n + 2.
CURVE_COLOR = {"hofmann": "#C1611E", "act": "#8C4A1A", "nhpi": "#E3A46B",
               "nixec": "#7A1626", "coh": "#A31F34", "aza": "#D2707E"}
_BASE_N = len(cdx.COLORTABLE)
cdx.COLORTABLE = cdx.COLORTABLE + [tuple(int(CURVE_COLOR[k][i:i + 2], 16) / 255.0 for i in (1, 3, 5))
                                   for k in KEYS]
CIDX = {k: _BASE_N + 2 + i for i, k in enumerate(KEYS)}


def ring6(m, cx, cy, start=90.0, dbl=(0, 2, 4)):
    """A hexagon of bond length L; `start` is the angle of vertex 0, y measured DOWN the page."""
    idx = []
    for k in range(6):
        a = math.radians(start + 60 * k)
        idx.append(m.at(cx + L * math.cos(a), cy - L * math.sin(a)))
    for k in range(6):
        m.bd(idx[k], idx[(k + 1) % 6], 2 if k in dbl else 1)
    return idx


def outward(m, cx, cy, start, k, n=6, dist=L, **kw):
    """An atom hung from ring vertex k along the ring's own outward radius."""
    a = math.radians(start + (360.0 / n) * k)
    vx, vy = cx + L * math.cos(a), cy - L * math.sin(a)
    return m.at(vx + dist * math.cos(a), vy - dist * math.sin(a), **kw)


def ring5(m, cx, cy, start=90.0):
    idx = []
    for k in range(5):
        a = math.radians(start + 72 * k)
        idx.append(m.at(cx + L * math.cos(a), cy - L * math.sin(a)))
    for k in range(5):
        m.bd(idx[k], idx[(k + 1) % 5])
    return idx


def chain(m, x, y, n, down_first=True, start=None):
    """n bonds of a 120-degree zig-zag; returns the atom indices."""
    idx = [start if start is not None else m.at(x, y)]
    for k in range(n):
        dy = -DY if (k % 2 == 0) == down_first else DY
        x, y = x + DX, y + dy
        idx.append(m.at(x, y))
        m.bd(idx[-2], idx[-1])
    return idx


# ------------------------------------------------------------------ the six schemes
def sch_hofmann(doc, y, c=0):
    """R-C(=O)NH2 -> R-NH-C(=O)-OMe: the amide nitrogen keeps the carbon it loses."""
    m = Mol()
    a0 = m.at(0, y, label="R")
    a1 = m.at(DX, y - DY)
    a2 = m.at(DX, y - DY - L)                      # the carbonyl oxygen
    a3 = m.at(2 * DX, y, label="NH2")
    m.bd(a0, a1); m.bd(a1, a2, 2); m.bd(a1, a3)
    emit_mol(doc, m, color=c)
    doc.arrow((2 * DX + 30, y - DY), (2 * DX + 56, y - DY), color=c)
    x = 2 * DX + 68
    p = Mol()
    b0 = p.at(x, y, label="R")
    b1 = p.at(x + DX, y - DY, el=7, H=0)           # N, its H implicit as the skeleton elsewhere
    b2 = p.at(x + 2 * DX, y)
    b3 = p.at(x + 2 * DX, y - L, el=8)             # C=O
    b4 = p.at(x + 3 * DX, y + DY, el=8)
    b5 = p.at(x + 4 * DX, y, H=3)                  # OCH3
    p.bd(b0, b1); p.bd(b1, b2); p.bd(b2, b3, 2); p.bd(b2, b4); p.bd(b4, b5)
    emit_mol(doc, p, color=c)


def sch_act(doc, y, c=0):
    """Primary alcohol -> carboxylic acid."""
    m = Mol()
    a = chain(m, 0, y, 2)
    a3 = m.at(2 * DX + DX, y - DY, el=8, H=1)      # OH
    m.bd(a[2], a3)
    emit_mol(doc, m, color=c)
    doc.arrow((3 * DX + 24, y - DY), (3 * DX + 50, y - DY), color=c)
    x = 3 * DX + 62
    p = Mol()
    b = chain(p, x, y, 2)
    b3 = p.at(x + 2 * DX, y - DY - L, el=8)        # C=O
    b4 = p.at(x + 3 * DX, y - DY, el=8, H=1)       # OH
    p.bd(b[2], b3, 2); p.bd(b[2], b4)
    emit_mol(doc, p, color=c)


def sch_nhpi(doc, y, c=0):
    """Cyclohexene -> cyclohex-2-enone: the allylic methylene becomes the enone."""
    m = Mol()
    ring6(m, L, y, dbl=())
    m.bonds[1]["order"] = 2                        # the alkene, between vertices 1 and 2
    emit_mol(doc, m, color=c)
    doc.arrow((2 * L + 16, y), (2 * L + 42, y), color=c)
    x = 2 * L + 56 + L
    p = Mol()
    r2 = ring6(p, x, y, dbl=())
    p.bonds[1]["order"] = 2
    o = outward(p, x, y, 90.0, 0, el=8)            # the carbonyl, conjugated to that alkene: an enone
    p.bd(r2[0], o, 2)
    emit_mol(doc, p, color=c)


def sch_nixec(doc, y, c=0):
    """Aryl bromide + alkyl bromide coupled C(sp2)-C(sp3)."""
    m = Mol()
    r = ring6(m, L, y)
    br = outward(m, L, y, 90.0, 3, el=35, just="Right")
    m.bd(r[3], br)
    emit_mol(doc, m, color=c)
    doc.text(2 * L + 14, y + 4, "+", fam="L", color=c)
    q = Mol()
    c0 = q.at(2 * L + 32, y, label="R")
    c1 = q.at(2 * L + 32 + DX, y - DY, el=35)
    q.bd(c0, c1)
    emit_mol(doc, q, color=c)
    doc.arrow((2 * L + 32 + DX + 26, y - DY), (2 * L + 32 + DX + 52, y - DY), color=c)
    x = 2 * L + 32 + DX + 66 + L
    p = Mol()
    r2 = ring6(p, x, y)
    rr = outward(p, x, y, 90.0, 3, label="R", just="Right")
    p.bd(r2[3], rr)
    emit_mol(doc, p, color=c)


def sch_coh(doc, y, c=0):
    """Markovnikov hydroamination: the nitrogen lands on the substituted carbon."""
    m = Mol()
    a0 = m.at(0, y, label="R")
    a1 = m.at(DX, y - DY)
    a2 = m.at(2 * DX, y)
    m.bd(a0, a1); m.bd(a1, a2, 2)
    emit_mol(doc, m, color=c)
    doc.text(2 * DX + 16, y + 4, "+  HNR_2", fam="L", color=c)
    doc.arrow((2 * DX + 66, y - DY), (2 * DX + 92, y - DY), color=c)
    x = 2 * DX + 104
    p = Mol()
    b0 = p.at(x, y, label="R")
    b1 = p.at(x + DX, y - DY)
    b2 = p.at(x + DX, y - DY - L, el=7, label="NR2", just="Left")
    b3 = p.at(x + 2 * DX, y, H=3)
    p.bd(b0, b1); p.bd(b1, b2); p.bd(b1, b3)
    emit_mol(doc, p, color=c)


def sch_aza(doc, y, c=0):
    """An N-tethered alkene closes onto the ring."""
    m = Mol()
    a0 = m.at(0, y, el=7, H=1, just="Right")
    a = chain(m, 0, y, 4, start=a0)
    m.bonds[-1]["order"] = 2
    emit_mol(doc, m, color=c)
    doc.arrow((4 * DX + 22, y - DY), (4 * DX + 48, y - DY), color=c)
    x = 4 * DX + 62 + L
    p = Mol()
    r = ring5(p, x, y)
    p.atoms[0]["el"] = 7                            # N at the top vertex
    p.atoms[0]["H"] = 0                             # implicit, as the skeleton elsewhere
    me = outward(p, x, y, 90.0, 4, n=5, H=3)        # the 2-methyl, away from the arrow
    p.bd(r[4], me)
    emit_mol(doc, p, color=c)


SCHEMES = [("hofmann", sch_hofmann), ("act", sch_act), ("nhpi", sch_nhpi),
           ("nixec", sch_nixec), ("coh", sch_coh), ("aza", sch_aza)]


def build():
    doc = Doc("Fig6 schemes")
    bands = {}
    for k, (key, fn) in enumerate(SCHEMES):
        y = BAND * k + BAND / 2
        n0 = len(doc.boxes)
        fn(doc, y, CIDX[key])
        bx = doc.boxes[n0:]
        if not bx:
            raise SystemExit("%s drew nothing" % key)
        bands[key] = (min(b[0] for b in bx), min(b[1] for b in bx),
                      max(b[2] for b in bx), max(b[3] for b in bx))
    return doc, bands


def main(force=False):
    import shutil, tempfile
    import fitz
    from chemdraw_render import render
    if os.path.exists(OUT_CDXML) and not force:
        raise SystemExit("%s exists and may carry edits made in ChemDraw; refusing (use --force)" % OUT_CDXML)
    doc, bands = build()
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="fig6_schemes_")
    gen = os.path.join(tmp, "fig6_schemes_generated.cdxml")
    cdx.write(doc, gen, page=(430, BAND * len(SCHEMES) + 40))
    page_pdf, saved = os.path.join(tmp, "page.pdf"), os.path.join(tmp, "Fig6_schemes.cdxml")
    print("open after render:", render(gen, [page_pdf, saved]))

    ox, oy = cdx.OFFSET[0] + PAGE_MARGIN, cdx.OFFSET[1] + PAGE_MARGIN
    src = fitz.open(page_pdf)
    sp = src[0]
    fonts = {f[3].split("+")[-1] for f in sp.get_fonts()}
    if not fonts <= {"Lato-Regular", "Lato-Bold", "ArialMT"}:
        raise SystemExit("unexpected fonts in the ChemDraw export: %r" % fonts)
    for key, (x0, y0, x1, y1) in bands.items():
        # INTERSECT with the page first.  The band boxes can start LEFT of the drawing origin, so
        # ox + x0 - 34 goes negative; get_pixmap silently clamps such a clip to the page while the
        # vector crop below would still measure from the unclamped rect -- which shifted every
        # structure right by 6-10 pt and cut that much off its right edge (ACT's "OH" lost its H).
        # Measured against the PNGs, not noticed by eye.
        clip = fitz.Rect(ox + x0 - 34, oy + y0 - 20, ox + x1 + 34, oy + y1 + 20) & sp.rect
        pix = sp.get_pixmap(dpi=1200, clip=clip, alpha=True)
        pix.set_dpi(1200, 1200)
        p = os.path.join(OUT_DIR, key + ".png")
        pix.save(p)
        box = _trim(p)
        # the same crop as VECTOR, for anyone who wants to edit the structures rather than place them.
        # The scale comes from the pixmap the raster was actually made at, so the two crops cannot
        # drift by the pixel rounding get_pixmap applies to a clip.
        kx, ky = clip.width / pix.width, clip.height / pix.height
        vclip = fitz.Rect(clip.x0 + box[0] * kx, clip.y0 + box[1] * ky,
                          clip.x0 + box[2] * kx, clip.y0 + box[3] * ky)
        vout = fitz.open()
        vpg = vout.new_page(width=vclip.width, height=vclip.height)
        vpg.show_pdf_page(vpg.rect, src, 0, clip=vclip)
        vout.save(os.path.join(OUT_DIR, key + ".pdf"), garbage=4, deflate=True)
        print("  %-8s %6.1f x %5.1f pt  ->  %4d x %4d px  %s"
              % (key, x1 - x0, y1 - y0, pix.width, pix.height, os.path.basename(p)))
    shutil.copyfile(saved, OUT_CDXML)
    print("wrote", OUT_CDXML)
    print("fonts:", ", ".join(sorted(fonts)))


if __name__ == "__main__":
    main("--force" in sys.argv)
