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
  (h) Co-H alkene reduction (e-HAT)     Gnaim et al. Nature 2022, conditions C (Fig. 3 p 689,
                                         'Scope of e-HAT reduction'; Fig. 4a p 691): a terminal
                                         monosubstituted alkene is reduced to the alkane
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
CLEARANCE = 56.0                # clear space demanded between two bands' ink boxes on the page
CLIP_PAD_Y = 12.0               # vertical margin of a band's crop, before _trim cuts to the ink
CLIP_PAD_X = 34.0               # horizontal margin of the same crop
PAGE_W = 430.0
# The band pitch is MEASURED, not declared.  It was a fixed 82 pt until 2026-10-05, which worked only
# because every scheme happened to be shorter than that: Jonas's aza-Wacker drawing is 83 pt tall and
# left the tightest gap at 42.8 pt against the 40 pt the two crop margins consume, so a band could
# have pulled its neighbour's ink into its own crop.  build() now lays the bands out from their own
# measured heights with CLEARANCE between them, and asserts the page still fits ChemDraw's legal-
# landscape sheet -- past which ChemDraw refuses the document with "The objects will not fit".
PAGE_H_MAX = 612.0 - 36.0       # legal landscape less the 18 pt print margins (Figure 2's own setup)
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


KEYS = ["hofmann", "act", "nhpi", "nixec", "coh", "homo", "brom"]
# each scheme is drawn in the colour of the curve it belongs to, which is what ties the two together
# in the figure. Doing it HERE rather than by tinting a raster is what keeps the schemes vector all
# the way into the figure's PDF. COLORTABLE entry n carries colour index n + 2.
# chemistry audit, 2026-10-05 (night): the third row of (h) is the Ni aryl-aryl homocoupling, which replaced the
# Co(salen) allylic C-H amination once that row lost its rate constant; the "aza" crops it leaves behind are in
# _archive/fig6_aza_scheme_20261005/.
CURVE_COLOR = {"hofmann": "#C1611E", "act": "#8C4A1A", "nhpi": "#E3A46B",
               "nixec": "#7A1626", "coh": "#A31F34", "homo": "#D2707E",
               "brom": "#C1611E"}   # 2026-10-06: the substrate-limited curve of (d)/(g), Hofmann's colour carried over
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
    """e-HAT reduction of a terminal monosubstituted alkene to the alkane.

    NOT a hydroamination. Gnaim et al. Nature 2022 captions Fig. 3 "Scope of e-HAT reduction" and
    the text reads "the selective reduction of monosubstituted alkenes was similarly achieved by
    relying on e-HAT (conditions C)"; conditions C is CoBr2.glyme / 6,6'-Me-bpy / HFIP / Et3NHBF4 in
    THF, which is the row this curve plots. The word "hydroamination" occurs once in that paper, in
    its own reference 13 (Gui et al., olefin hydroamination with nitroarenes) -- a cited title, not
    its chemistry, which is how this scheme came to draw an amine (Jonas Rein, 2026-10-05).

    Drawn as the paper draws it: no reagent on the arrow, the hydride coming from HFIP and the
    current. The change is the terminal double bond.
    """
    m = Mol()
    a0 = m.at(0, y, label="R")
    a1 = m.at(DX, y - DY)
    a2 = m.at(2 * DX, y)
    m.bd(a0, a1); m.bd(a1, a2, 2)
    emit_mol(doc, m, color=c)
    doc.arrow((2 * DX + 22, y - DY), (2 * DX + 48, y - DY), color=c)
    x = 2 * DX + 60
    p = Mol()
    b0 = p.at(x, y, label="R")
    b1 = p.at(x + DX, y - DY)
    b2 = p.at(x + 2 * DX, y, H=3)
    p.bd(b0, b1); p.bd(b1, b2)
    emit_mol(doc, p, color=c)


def sch_brom(doc, y, c=0):
    """Bromide-mediated electrophilic bromination of anisole to 4-bromoanisole (Zhang/Su, Nat. Commun. 2025;
    Br2 + anisole measured by Sivey et al., ES&T 2015). Panel (d) and (g)'s substrate-limited row since 2026-10-06,
    replacing the Hofmann rearrangement, whose declared k puts its substrate-limited label inside its own band.

    Drawn as the other schemes are: no reagent on the arrow, the change is the para C-Br bond. The methoxy sits
    on the LEFT vertex and is stored "OMe": ChemDraw right-justifies a left-hand label and reverses its tokens,
    so it prints "MeO" (the rule the case-studies figure already records for "OCH3")."""
    m = Mol()
    cx = 4.0 * L                    # the right-justified "MeO" must clear the page's left edge, or the crop clamps it
    r = ring6(m, cx, y, start=0.0, dbl=(0, 2, 4))
    m.bd(r[3], outward(m, cx, y, 0.0, 3, el=8, label="OMe"))
    emit_mol(doc, m, color=c)
    # Jonas's scheme geometry, measured from his three groups in Fig6_schemes.cdxml (2026-10-06): every arrow is 49.2 pt,
    # its tail sits 18.3-19.2 pt after the reactant's ink and its head 20.9-21.7 pt before the product's. MEO_LEFT is how
    # far the right-justified "MeO" label's ink reaches left of its O atom (17 pt, measured on the first render).
    JR_ARROW, JR_GAP_TAIL, JR_GAP_HEAD, MEO_LEFT = 49.2, 19.0, 21.0, 17.0
    ax0 = cx + L + JR_GAP_TAIL
    doc.arrow((ax0, y), (ax0 + JR_ARROW, y), color=c)
    px = ax0 + JR_ARROW + JR_GAP_HEAD + MEO_LEFT + 2.0 * L
    p = Mol()
    q = ring6(p, px, y, start=0.0, dbl=(0, 2, 4))
    p.bd(q[3], outward(p, px, y, 0.0, 3, el=8, label="OMe"))
    p.bd(q[0], outward(p, px, y, 0.0, 0, el=35, label="Br"))
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


# ═══════════════════ Jonas Rein's redrawn structures (2026-10-05) ═══════════════════
# "I redrew the structures in Fig 6 (the structures looked a bit off)".  His file carries FIVE of the
# six schemes -- Hofmann, Ni-XEC, ACT, aza-Wacker and NHPI -- each a self-contained ChemDraw <group>
# with its own fragments, arrow and plus sign, drawn in THIS document's style (measured: BondLength
# 14.40, LineWidth 1.13, BoldWidth 2.27, HashSpacing 2.49, Arial 9.9 pt labels -- identical to
# cdxml_style's, so his drawings need translation only, never scaling).
#
# The sixth, the cobalt row, he did not redraw: he flagged it as the WRONG REACTION instead, and
# sch_coh above is the correction.  So five schemes come from his file and one from ours.
#
# His groups are found by SIGNATURE -- fragment count plus the multiset of atom labels -- and never
# by position in the file, so re-saving his document in ChemDraw (which reorders objects) cannot
# silently swap two schemes.  Each signature is required to match exactly one group.
JR_CDXML = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Figures",
                        "Fig6_schemes_JR_20261005.cdxml")
JR_SIG = {
    "hofmann": (3, ("NH", "NH2", "O", "O", "OMe", "R", "R")),
    "nixec":   (3, ("Alkyl", "Alkyl", "Ar", "Ar", "Br", "Br")),
    "act":     (2, ("O", "OH", "OH", "R", "R")),
    "aza":     (2, ("H", "N", "NH", "O", "O", "R", "R", "X", "X")),
    "nhpi":    (2, ("O",)),
}
# What each of his drawings is, checked against the exemplar the row is read from:
#   hofmann  R-C(=O)NH2 -> R-NH-C(=O)OMe        amide to methyl carbamate (Malviya & Cantillo)
#   nixec    Ar-Br + Alkyl-Br -> Ar-Alkyl       cross-electrophile coupling (Kelly et al.)
#   act      R-CH2OH -> R-C(=O)OH               primary alcohol to acid (Zhong & Stahl)
#   aza      N-tethered alkene closes, X=NH,O,CH2   aza-Wacker (Cai & Xu)
#   nhpi     cyclohexene -> cyclohex-2-enone    allylic C-H oxidation to the enone (Horn & Baran).
#            He generalised this one: the exemplar is valencene -> nootkatone, and a sesquiterpene
#            skeleton is unreadable at the size this scheme is placed.  The manuscript caption names
#            the transformation, not the substrate, so it still describes the drawing.
_JR_CACHE = {}


def _jr_groups():
    """{key: (group element, bbox)} for the five schemes Jonas redrew."""
    if _JR_CACHE:
        return _JR_CACHE
    import xml.etree.ElementTree as ET
    if not os.path.exists(JR_CDXML):
        raise SystemExit("Jonas's redrawn schemes are missing: %s" % JR_CDXML)
    root = ET.parse(JR_CDXML).getroot()
    bond = float(root.get("BondLength", "0"))
    if abs(bond - L) > 0.01:
        raise SystemExit("JR document BondLength %s, ours %s: his drawings would need scaling"
                         % (bond, L))
    found = {}
    for g in root.find(".//page").findall("group"):
        frags = g.findall(".//fragment")
        labs = tuple(sorted("".join(sp.text or "" for sp in t.findall(".//s"))
                            for f in frags for t in f.findall(".//t")))
        sig = (len(frags), labs)
        for key, want in JR_SIG.items():
            if sig == want:
                if key in found:
                    raise SystemExit("two groups match the %s signature" % key)
                xs, ys = [], []
                for n in g.findall(".//n"):
                    if n.get("p"):
                        a, b = n.get("p").split()[:2]
                        xs.append(float(a)); ys.append(float(b))
                for el in g.iter():
                    bb = el.get("BoundingBox")
                    if bb:
                        v = [float(x) for x in bb.split()]
                        xs += [v[0], v[2]]; ys += [v[1], v[3]]
                found[key] = (g, (min(xs), min(ys), max(xs), max(ys)))
    missing = set(JR_SIG) - set(found)
    if missing:
        raise SystemExit("no group matches the signature for: %s" % ", ".join(sorted(missing)))
    _JR_CACHE.update(found)
    return _JR_CACHE


def _bbox(el):
    return [float(t) for t in el.get("BoundingBox").split()]


def _extent(g):
    """The group's extent the way _jr_groups measures it: node positions and every BoundingBox."""
    xs, ys = [], []
    for n in g.findall(".//n"):
        if n.get("p"):
            a, b = n.get("p").split()[:2]
            xs.append(float(a)); ys.append(float(b))
    for el in g.iter():
        if el.get("BoundingBox"):
            v = _bbox(el)
            xs += [v[0], v[2]]; ys += [v[1], v[3]]
    return min(xs), min(ys), max(xs), max(ys)


def _shift(el, dx):
    """Translate one element and everything under it by dx points."""
    for e in el.iter():
        for attr in ("p", "Head3D", "Tail3D", "Center3D", "MajorAxisEnd3D", "MinorAxisEnd3D"):
            v = e.get(attr)
            if v:
                w = v.split()
                w[0] = "%.2f" % (float(w[0]) + dx)
                e.set(attr, " ".join(w))
        bb = e.get("BoundingBox")
        if bb:
            v = [float(t) for t in bb.split()]
            e.set("BoundingBox", "%.2f %.2f %.2f %.2f" % (v[0] + dx, v[1], v[2] + dx, v[3]))


def _homo_from_nixec(g):
    """Ar-Br + Br-Ar -> Ar-Ar, made from Jonas's Ar-Br + Br-Alkyl -> Ar-Alkyl by relabelling each Alkyl as Ar.

    The two rows of Figure 6h that run on nickel differ in exactly this: the cross-electrophile coupling joins an
    aryl to an alkyl bromide, the homocoupling joins two aryl bromides (Courtois/Perichon, Tetrahedron 1997:
    bromobenzene to biphenyl). Drawing the second as his first with one word changed keeps his style exactly and
    makes that difference the only thing a reader sees. ChemDraw stores his "Ar" as an element node (it reads the
    label as argon) and his "Alkyl" as an unspecified node, so each relabelled node takes the Ar node's own
    attributes; the label is narrower by the difference of the two labels' measured widths, and the arrow and the
    product are moved left by that much so the gap before the arrow stays his.
    """
    frags = g.findall("fragment")
    lab = lambda n: "".join(s.text or "" for s in n.findall("./t/s"))
    ar = [n for f in frags for n in f.findall("n") if lab(n) == "Ar"]
    al = [n for f in frags for n in f.findall("n") if lab(n) == "Alkyl"]
    if len(ar) != 2 or len(al) != 2:
        raise SystemExit("the Ni-XEC drawing should carry two Ar and two Alkyl labels; found %d and %d" % (len(ar), len(al)))
    w_ar = _bbox(ar[0].find("t"))[2] - _bbox(ar[0].find("t"))[0]
    w_al = _bbox(al[0].find("t"))[2] - _bbox(al[0].find("t"))[0]
    shrink = w_al - w_ar
    if not 5.0 < shrink < 20.0:
        raise SystemExit("unexpected label widths: Ar %.2f pt, Alkyl %.2f pt" % (w_ar, w_al))
    for n in al:
        for k in ("NodeType", "Warning"):
            n.attrib.pop(k, None)
        for k in ("Element", "NumHydrogens", "Warning"):
            if ar[0].get(k) is not None:
                n.set(k, ar[0].get(k))
        n.find("./t/s").text = "Ar"
        t = n.find("t"); v = _bbox(t)
        t.set("BoundingBox", "%.2f %.2f %.2f %.2f" % (v[0], v[1], v[2] - shrink, v[3]))
    for f in frags:
        if any(n in al for n in f.findall("n")):
            v = _bbox(f)
            f.set("BoundingBox", "%.2f %.2f %.2f %.2f" % (v[0], v[1], v[2] - shrink, v[3]))
    # the arrow (and the line graphic it supersedes) and the product fragment sit right of the reactant pair
    arrow = g.find("arrow")
    tail = float(arrow.get("Tail3D").split()[0])
    prod = [f for f in frags if _bbox(f)[0] > tail]
    if len(prod) != 1:
        raise SystemExit("expected exactly one product fragment right of the arrow, found %d" % len(prod))
    for m in [arrow] + g.findall("graphic") + prod:
        _shift(m, -shrink)
    labs = sorted(lab(n) for f in g.findall("fragment") for n in f.findall("n"))
    if labs != ["Ar", "Ar", "Ar", "Ar", "Br", "Br"]:
        raise SystemExit("the homocoupling scheme reads %r" % labs)
    # the group carries its own BoundingBox, which still spans the wider original; reset it to its children's
    if g.get("BoundingBox"):
        kids = [e for e in g.iter() if e is not g and e.get("BoundingBox")]
        xs = [c for e in kids for c in (_bbox(e)[0], _bbox(e)[2])]
        ys = [c for e in kids for c in (_bbox(e)[1], _bbox(e)[3])]
        g.set("BoundingBox", "%.2f %.2f %.2f %.2f" % (min(xs), min(ys), max(xs), max(ys)))
    return g


def sch_jr(key, edit=None):
    """A scheme function that lays Jonas's `key` group into its band, translated, never scaled.

    `edit`, if given, is applied to the copied group before it is placed (the homocoupling is his Ni-XEC
    drawing relabelled; see _homo_from_nixec)."""
    def draw(doc, y, c=0):
        import copy
        import xml.etree.ElementTree as ET
        g, (x0, y0, x1, y1) = _jr_groups()[key]
        g = copy.deepcopy(g)
        if edit is not None:
            g = edit(g)
            x0, y0, x1, y1 = _extent(g)
        # his left edge to our x = 0, his vertical centre to our baseline band centre
        px, py = doc.P(0.0, y)
        dx, dy = px - x0, py - (y0 + y1) / 2.0
        # renumber every id above ours so two documents' objects cannot collide
        base = doc.nid() + 10000
        remap = {}
        for el in g.iter():
            if el.get("id"):
                remap[el.get("id")] = str(base + len(remap) + 1)
        for el in g.iter():
            if el.get("id"):
                el.set("id", remap[el.get("id")])
            for ref in ("B", "E", "BeginAttach", "EndAttach"):
                if el.get(ref) in remap:
                    el.set(ref, remap[el.get(ref)])
            for attr in ("p", "Head3D", "Tail3D", "Center3D", "MajorAxisEnd3D", "MinorAxisEnd3D"):
                v = el.get(attr)
                if v:
                    w = v.split()
                    if len(w) >= 2:
                        w[0] = "%.2f" % (float(w[0]) + dx)
                        w[1] = "%.2f" % (float(w[1]) + dy)
                        el.set(attr, " ".join(w))
            bb = el.get("BoundingBox")
            if bb:
                v = [float(t) for t in bb.split()]
                el.set("BoundingBox", "%.2f %.2f %.2f %.2f"
                       % (v[0] + dx, v[1] + dy, v[2] + dx, v[3] + dy))
        # his ink is black; colour it like ours so the six schemes agree on the scratch page.
        # (combined_figure re-tints every crop to its curve's colour anyway, but it derives coverage
        # from how far each pixel is from WHITE normalised by the target colour, so a black source
        # clips to full coverage where a coloured one does not, and the edges come out heavier.)
        if c:
            for el in g.iter():
                if el.tag in ("fragment", "n", "b", "graphic", "arrow", "s", "t"):
                    el.set("color", str(c))
        doc.items.append(ET.tostring(g, encoding="unicode"))
        doc.boxes.append((x0 + dx, y0 + dy, x1 + dx, y1 + dy))
    draw.__name__ = "sch_jr_" + key + ("_edited" if edit is not None else "")
    draw.__doc__ = "Jonas Rein's redrawn %s scheme, lifted from %s." % (key, os.path.basename(JR_CDXML))
    return draw


# Four of the six are Jonas's redrawn structures as he drew them, the homocoupling is his Ni-XEC drawing
# relabelled, and the cobalt one is ours, corrected.  His aza-Wacker drawing is still matched by signature
# (so a re-saved file that lost it is caught) but no longer placed: its row has no rate constant and left
# panel (h) in the chemistry audit of 2026-10-05.  The original matplotlib-era functions sch_hofmann/sch_act/
# sch_nhpi/sch_nixec/sch_aza are kept above: they are what produced the 2026-10-02 crops, and they are the
# fallback if his file is ever unavailable.
SCHEMES = [("brom", sch_brom), ("act", sch_jr("act")), ("nhpi", sch_jr("nhpi")),
           ("nixec", sch_jr("nixec")), ("coh", sch_coh), ("homo", sch_jr("nixec", _homo_from_nixec))]


def build():
    """Lay every scheme out in its own horizontal band, the pitch measured from the drawings.

    Pass 1 draws each scheme into a throwaway document at a common baseline and measures the height
    and the offset of its ink box from that baseline; pass 2 places the bands so that consecutive ink
    boxes are CLEARANCE apart, and draws for real.
    """
    probe = Doc("probe")
    span = {}
    for key, fn in SCHEMES:
        n0 = len(probe.boxes)
        fn(probe, 0.0, CIDX[key])
        bx = probe.boxes[n0:]
        if not bx:
            raise SystemExit("%s drew nothing" % key)
        span[key] = (min(b[1] for b in bx), max(b[3] for b in bx))   # relative to baseline y = 0

    # 2026-10-06: the bromination scheme takes the Hofmann band's HEIGHT, centred in it, so every band below keeps the
    # position it had and the five unchanged crops re-render byte-identically (a shorter first band shifted them by a
    # fraction of a pixel and re-antialiased 0.3-0.9 % of their pixels).
    n0 = len(probe.boxes)
    sch_jr("hofmann")(probe, 0.0, CIDX["hofmann"])
    hb = probe.boxes[n0:]
    held = {"brom": max(b[3] for b in hb) - min(b[1] for b in hb)}
    doc = Doc("Fig6 schemes")
    bands, y_at, cursor = {}, {}, PAGE_MARGIN
    for key, fn in SCHEMES:
        lo, hi = span[key]
        if key in held:
            pad = (held[key] - (hi - lo)) / 2.0
            if pad < 0:
                raise SystemExit("%s is taller than the band it holds" % key)
            y_at[key] = cursor - lo + pad
            cursor = cursor + held[key] + CLEARANCE
            continue
        y_at[key] = cursor - lo                      # so the band's top ink lands on the cursor
        cursor = y_at[key] + hi + CLEARANCE
    for key, fn in SCHEMES:
        n0 = len(doc.boxes)
        fn(doc, y_at[key], CIDX[key])
        bx = doc.boxes[n0:]
        bands[key] = (min(b[0] for b in bx), min(b[1] for b in bx),
                      max(b[2] for b in bx), max(b[3] for b in bx))
    page_h = cursor - CLEARANCE + PAGE_MARGIN
    if page_h > PAGE_H_MAX:
        raise SystemExit("the schemes need a %.0f pt page; ChemDraw's sheet gives %.0f"
                         % (page_h, PAGE_H_MAX))
    # a crop may not reach a neighbour's ink: 2 * CLIP_PAD_Y is what two adjacent crops consume
    boxes = sorted((v[1], v[3], k) for k, v in bands.items())
    for (a0, a1, ka), (b0, b1, kb) in zip(boxes, boxes[1:]):
        if b0 - a1 < 2 * CLIP_PAD_Y:
            raise SystemExit("%s and %s are %.1f pt apart, the crops need %.1f"
                             % (ka, kb, b0 - a1, 2 * CLIP_PAD_Y))
    widest = max(v[2] for v in bands.values())
    if widest + CLIP_PAD_X > PAGE_W:
        raise SystemExit("%.0f pt of drawing plus its crop margin exceeds the %.0f pt page"
                         % (widest, PAGE_W))
    return doc, bands, page_h


def main(force=False):
    import shutil, tempfile
    import fitz
    from chemdraw_render import render
    if os.path.exists(OUT_CDXML) and not force:
        raise SystemExit("%s exists and may carry edits made in ChemDraw; refusing (use --force)" % OUT_CDXML)
    doc, bands, page_h = build()
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="fig6_schemes_")
    gen = os.path.join(tmp, "fig6_schemes_generated.cdxml")
    cdx.write(doc, gen, page=(PAGE_W, page_h))
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
        clip = fitz.Rect(ox + x0 - CLIP_PAD_X, oy + y0 - CLIP_PAD_Y,
                         ox + x1 + CLIP_PAD_X, oy + y1 + CLIP_PAD_Y) & sp.rect
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
