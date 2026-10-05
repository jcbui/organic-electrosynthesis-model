"""Minimal CDXML writer in Figure 2's ChemDraw style (ChemDraw 23.1.2, Jonas Rein's Figure.cdxml).

Style constants are copied from Figures/Figure.cdxml (the document settings) and from its finished export
Figures/Figure.pdf (electrode geometry, fonts): bond length 14.40 pt, line width 1.13, bold 2.27, margin 1.58,
hash spacing 2.49, bond spacing 18 %; atom labels Arial 10 (formula face); all other text Lato 10 (bold titles);
straight arrows HeadSize 1000/875/250, curved 800/700/200; electrodes 7.5 pt wide, 1.8 pt corners, 0.6 grey,
1 pt black outline; dividers 2.27 pt dotted.

Coordinates are points, y down, in the figure's own frame; OFFSET places the frame on ChemDraw's page.
"""
import math
from xml.sax.saxutils import escape

import os
import re

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the project folder
FIG2_CDXML = os.path.join(ROOT, "Figures", "Figure.cdxml")

L = 14.40                       # bond length
FA, FL = 3, 4                   # font ids: Arial (atom labels), Lato (everything else)
OFFSET = (10.0, 10.0)           # frame origin on the ChemDraw page
GREY = 4                        # colour index of the electrode grey (colortable entry 3 -> index 4)
# ChemDraw's PDF export applies a colour conversion: a stored 0.532 grey exports as 0.600 (measured).
COLORTABLE = [(1, 1, 1), (0, 0, 0), (0.532, 0.532, 0.532)]
CORNER = 160                    # ChemDraw CornerRadius units; 160 -> 1.8 pt, Figure 2's electrode corners (measured)

_FONTS = {
    ("L", 0): os.path.expanduser("~/Library/Fonts/Lato-Regular.ttf"),
    ("L", 1): os.path.expanduser("~/Library/Fonts/Lato-Bold.ttf"),
    ("L", 2): os.path.expanduser("~/Library/Fonts/Lato-Italic.ttf"),
    ("A", 0): "/System/Library/Fonts/Supplemental/Arial.ttf",
}
_cache = {}


def _font(fam, bold):
    key = (fam, bold if fam == "L" else 0)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(_FONTS[key], 1000)
    return _cache[key]


def width(text, fam="L", size=10.0, bold=0):
    return _font(fam, bold).getlength(text) / 1000.0 * size


# ---------------------------------------------------------------- rich text
ARIAL_CHARS = set("η→")          # Lato lacks these; set them in Arial deliberately rather than by fallback


def runs(markup, bold=0, fam="L"):
    """Parse '_x' / '_{..}' subscripts and '^x' / '^{..}' superscripts into (text, face, fam) runs."""
    out, i, buf = [], 0, ""

    def flush():
        nonlocal buf
        if buf:
            out.append((buf, bold, fam))
            buf = ""
    while i < len(markup):
        c = markup[i]
        if c in "_^" and i + 1 < len(markup):
            flush()
            if markup[i + 1] == "{":
                j = markup.index("}", i)
                t, i = markup[i + 2:j], j + 1
            else:
                t, i = markup[i + 1], i + 2
            out.append((t, (32 if c == "_" else 64) | bold, fam))
            continue
        buf += c
        i += 1
    flush()
    # split out the characters Lato lacks
    res = []
    for t, face, f in out:
        cur, cf = "", None
        for ch in t:
            want = "A" if ch in ARIAL_CHARS else f
            if cf is not None and want != cf:
                res.append((cur, face, cf))
                cur = ""
            cur, cf = cur + ch, want
        if cur:
            res.append((cur, face, cf))
    return res


def runs_width(rs):
    w = 0.0
    for t, face, fam in rs:
        size = 7.5 if face & 96 in (32, 64) else 10.0
        w += width(t, fam, size, face & 1)
    return w


class Doc:
    def __init__(self, name):
        self.name = name
        self.items = []
        self._id = 1000
        self.boxes = []          # (x0, y0, x1, y1) of placed objects, for arc trimming

    def nid(self):
        self._id += 1
        return self._id

    @staticmethod
    def P(x, y):
        return x + OFFSET[0], y + OFFSET[1]

    # ------------------------------------------------------------ text
    def text(self, x, y, markup, just="Left", bold=0, fam="L", lh=12.0, color=0, keep=True):
        """A caption; '\\n' breaks lines. (x, y) is the first baseline at the left / centre / right edge."""
        lines = markup.split("\n")
        line_runs = [runs(ln, bold, fam) for ln in lines]
        ws = [runs_width(r) for r in line_runs]
        s_xml, plain_len, starts = [], 0, []
        for k, r in enumerate(line_runs):
            for t, face, f in r:
                s_xml.append('<s font="%d" size="10" color="%d"%s>%s</s>' % (
                    FA if f == "A" else FL, color, (' face="%d"' % face) if face else "", escape(t)))
                plain_len += len(t)
            if k < len(line_runs) - 1:
                s_xml.append('<s font="%d" size="10" color="%d">\n</s>' % (FL, color))
                plain_len += 1
            starts.append(plain_len)
        W = max(ws)
        x0 = {"Left": x, "Center": x - W / 2, "Right": x - W}[just]
        bb = (x0, y - 8.0, x0 + W, y + 2.6 + lh * (len(lines) - 1))
        if keep:
            self.boxes.append(bb)
        px, py = self.P(x, y)
        attrs = 'p="%.2f %.2f" BoundingBox="%.2f %.2f %.2f %.2f" LineHeight="%g"' % (
            px, py, bb[0] + OFFSET[0], bb[1] + OFFSET[1], bb[2] + OFFSET[0], bb[3] + OFFSET[1], lh)
        if just != "Left":
            attrs += ' CaptionJustification="%s" Justification="%s"' % (just, just)
        if len(lines) > 1:
            attrs += ' LineStarts="%s"' % " ".join(str(s) for s in starts)
        self.items.append('<t id="%d" %s>%s</t>' % (self.nid(), attrs, "".join(s_xml)))
        return bb

    # ------------------------------------------------------------ graphics
    def rect(self, x0, y0, x1, y1, kind="Plain", color=None, corner=None, lw=None):
        a, b = self.P(x0, y0)
        c, d = self.P(x1, y1)
        extra = (' color="%d"' % color if color is not None else "") + \
                (' CornerRadius="%d"' % corner if corner else "") + (' LineWidth="%g"' % lw if lw else "")
        self.items.append('<graphic id="%d" BoundingBox="%.2f %.2f %.2f %.2f" GraphicType="Rectangle" '
                          'RectangleType="%s"%s/>' % (self.nid(), c, d, a, b, kind, extra))

    def box(self, x0, y0, x1, y1):
        self.rect(x0, y0, x1, y1, "Plain")

    def electrode(self, x, y0, y1, label=None):
        """Figure 2's electrode: 7.5 pt bar, 1.8 pt corners, 0.6 grey fill, 1 pt black outline."""
        self.rect(x, y0, x + 7.5, y1, "RoundEdge Filled", GREY, CORNER)
        self.rect(x, y0, x + 7.5, y1, "RoundEdge", None, CORNER, 1)
        self.boxes.append((x, y0, x + 7.5, y1))
        if label:
            self.text(x, y1 + 14.2, label)

    def _arrow(self, tail, head, center, major, minor, extra):
        pts = [self.P(*p) for p in (tail, head)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        c, M, m = self.P(*center), self.P(*major), self.P(*minor)
        self.items.append(
            '<arrow id="%d" BoundingBox="%.2f %.2f %.2f %.2f" FillType="None" %s Head3D="%.2f %.2f 0" '
            'Tail3D="%.2f %.2f 0" Center3D="%.2f %.2f 0" MajorAxisEnd3D="%.2f %.2f 0" MinorAxisEnd3D="%.2f %.2f 0"/>'
            % (self.nid(), min(xs), min(ys), max(xs), max(ys), extra, pts[1][0], pts[1][1], pts[0][0], pts[0][1],
               c[0], c[1], M[0], M[1], m[0], m[1]))

    def arrow(self, tail, head, heads=True, color=0):
        cx, cy = (tail[0] + head[0]) / 2, (tail[1] + head[1]) / 2
        extra = ('ArrowheadHead="Full" ' if heads else "") + \
            'ArrowheadType="Solid" HeadSize="1000" ArrowheadCenterSize="875" ArrowheadWidth="250"' + \
            ((' color="%d"' % color) if color else "")
        self._arrow(tail, head, (cx, cy), (cx + 10, cy), (cx, cy + 10), extra)

    def divider(self, a, b):
        cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        self._arrow(a, b, (cx, cy), (cx + 10, cy), (cx, cy + 10), 'LineType="Dashed Bold" ArrowheadType="Solid"')

    def arc(self, center, rx, ry, a_tail, a_head, heads=True):
        """Elliptical (rx != ry) or circular arc arrow from visual angle a_tail to a_head (degrees, CCW positive,
        y-up sense); the sweep is a_head - a_tail and may exceed 180 in magnitude."""
        cx, cy = center

        def pt(a):
            r = math.radians(a)
            return (cx + rx * math.cos(r), cy - ry * math.sin(r))
        extra = ('ArrowheadHead="Full" ' if heads else "") + \
            'ArrowheadType="Solid" HeadSize="800" ArrowheadCenterSize="700" ArrowheadWidth="200" AngularSize="%.2f"' % (
                a_head - a_tail)
        self._arrow(pt(a_tail), pt(a_head), center, (cx + rx, cy), (cx, cy + ry), extra)


# ---------------------------------------------------------------- molecules
class Mol:
    """Atoms at explicit coordinates. Heteroatom labels are Arial formula-face text anchored the way ChemDraw
    anchors them: the attached character centred on the atom, baseline 3.9 pt below it."""

    def __init__(self):
        self.atoms, self.bonds = [], []

    def at(self, x, y, el=6, label=None, H=None, charge=0, radical=False, just="Left", inner=None):
        self.atoms.append(dict(x=x, y=y, el=el, label=label, H=H, charge=charge, radical=radical, just=just,
                               inner=inner))
        return len(self.atoms) - 1

    def bd(self, a, b, order=1, dpos=None):
        self.bonds.append(dict(a=a, b=b, order=order, dpos=dpos))


def emit_mol(doc, mol, color=0):
    P = doc.P
    fid = doc.nid()
    ids = [doc.nid() for _ in mol.atoms]
    cat = (' color="%d"' % color) if color else ""
    out, extras = ['<fragment id="%d"%s>' % (fid, cat)], []
    for k, a in enumerate(mol.atoms):
        x, y = P(a["x"], a["y"])
        attrs = 'id="%d" p="%.2f %.2f"%s' % (ids[k], x, y, cat)
        body = ""
        if a["inner"] is not None:
            attrs += ' NodeType="Fragment"'
            body += a["inner"](doc, (x, y))
        else:
            if a["el"] != 6 or a["label"]:
                attrs += ' Element="%d"' % a["el"]
            if a["H"] is not None:
                attrs += ' NumHydrogens="%d"' % a["H"]
            if a["charge"]:
                attrs += ' Charge="%d"' % a["charge"]
            if a["radical"]:
                attrs += ' Radical="Doublet"'
        if a["label"]:
            lab = a["label"]
            rs = runs(lab.replace("2", "_2").replace("3", "_3"), fam="A")
            # the attached atom is the first stored character; ChemDraw displays a right-justified label with
            # its tokens reversed (stored "OCH3" prints "H3CO"), so that atom is last on the page
            half = width(lab[0], "A") / 2
            tx = x - half if a["just"] == "Left" else x + half
            ty = y + 3.9
            w = runs_width(rs)
            bx0 = tx if a["just"] == "Left" else tx - w
            doc.boxes.append((bx0 - OFFSET[0], ty - 11 - OFFSET[1], bx0 + w - OFFSET[0], ty + 3 - OFFSET[1]))
            body += '<t p="%.2f %.2f" LabelJustification="%s"%s><s font="%d" size="10" color="%d" face="96">%s</s></t>' % (
                tx, ty, a["just"], (' Justification="Right" LabelAlignment="Right"' if a["just"] == "Right" else ""),
                FA, color, escape(lab))
            # charge / radical symbols at the label's upper right, as Figure 2 attaches them
            # symbol graphics: the first BoundingBox pair is where ChemDraw draws the symbol (read off Figure 2)
            rx = tx + w if a["just"] == "Left" else tx
            if a["charge"]:
                qx, qy = rx + 3.2, y - 5.6
                extras.append('<graphic id="%d" BoundingBox="%.2f %.2f %.2f %.2f" GraphicType="Symbol" SymbolType="%s">'
                              '<represent attribute="Charge" object="%d"/></graphic>' % (
                                  doc.nid(), qx, qy, qx - 7.5, qy, "Plus" if a["charge"] > 0 else "Minus", ids[k]))
            if a["radical"]:
                qx, qy = rx + 2.4, y - 5.0
                extras.append('<graphic id="%d" BoundingBox="%.2f %.2f %.2f %.2f" GraphicType="Symbol" SymbolType="Electron">'
                              '<represent attribute="Radical" object="%d"/></graphic>' % (
                                  doc.nid(), qx, qy, qx - 12.75, qy, ids[k]))
        out.append("<n %s>%s</n>" % (attrs, body) if body else "<n %s/>" % attrs)
    for b in mol.bonds:
        attrs = 'id="%d" B="%d" E="%d"%s' % (doc.nid(), ids[b["a"]], ids[b["b"]], cat)
        if b["order"] != 1:
            attrs += ' Order="%d"' % b["order"]
        if b["dpos"]:
            attrs += ' DoublePosition="%s"' % b["dpos"]
        out.append("<b %s/>" % attrs)
    out.append("</fragment>")
    doc.items.append("".join(out) + "".join(extras))
    xs = [a["x"] for a in mol.atoms]
    ys = [a["y"] for a in mol.atoms]
    doc.boxes.append((min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2))


def inner_group(atoms, bonds, attach=0):
    """A nested fragment for a condensed label (e.g. CH2OH): atoms as (dx, dy, el, H) relative to the node,
    bonds as (i, j, order); an ExternalConnectionPoint is bonded to atoms[attach]."""
    def f(doc, xy):
        x, y = xy
        ids = [doc.nid() for _ in atoms]
        ext = doc.nid()
        s = ['<fragment id="%d">' % doc.nid()]
        for k, (dx, dy, el, H) in enumerate(atoms):
            s.append('<n id="%d" p="%.2f %.2f"%s NumHydrogens="%d"/>' % (
                ids[k], x + dx, y + dy, (' Element="%d"' % el) if el != 6 else "", H))
        s.append('<n id="%d" p="%.2f %.2f" NodeType="ExternalConnectionPoint"/>' % (ext, x - 12, y))
        for i, j, o in bonds:
            s.append('<b id="%d" B="%d" E="%d"%s/>' % (doc.nid(), ids[i], ids[j], (' Order="%d"' % o) if o > 1 else ""))
        s.append('<b id="%d" B="%d" E="%d"/>' % (doc.nid(), ext, ids[attach]))
        s.append("</fragment>")
        return "".join(s)
    return f


CH2OH = inner_group([(0, 0, 6, 2), (14.4, 0, 8, 1)], [(0, 1, 1)])
CH3O = inner_group([(0, 0, 8, 0), (-14.4, 0, 6, 3)], [(0, 1, 1)])
CHO = inner_group([(0, 0, 6, 1), (14.4, 0, 8, 0)], [(0, 1, 2)])
COOH = inner_group([(0, 0, 6, 0), (12.5, -7.2, 8, 0), (12.5, 7.2, 8, 1)], [(0, 1, 2), (0, 2, 1)])


def write(doc, path, page=(972, 576)):
    ct = "".join('<color r="%g" g="%g" b="%g"/>' % c for c in COLORTABLE)
    # Figure 2's own print setup (legal landscape), so the whole figure lies on page 1 of ChemDraw's PDF export
    fig2 = open(FIG2_CDXML, encoding="utf8").read()
    mpi = re.search(r'MacPrintInfo="([^"]*)"', fig2).group(1)
    head = ('<?xml version="1.0" encoding="UTF-8" ?>\n'
            '<!DOCTYPE CDXML SYSTEM "https://static.chemistry.revvitycloud.com/cdxml/CDXML.dtd" >\n'
            '<CDXML CreationProgram="ChemDraw 23.1.2.7" Name="%s" BoundingBox="0 0 %d %d" FractionalWidths="yes" '
            'InterpretChemically="yes" ShowAtomQuery="yes" ShowAtomStereo="no" ShowAtomEnhancedStereo="yes" '
            'ShowAtomNumber="no" ShowBondQuery="yes" ShowBondRxn="yes" ShowBondStereo="no" '
            'ShowTerminalCarbonLabels="no" ShowNonTerminalCarbonLabels="no" HideImplicitHydrogens="no" '
            'LabelFont="3" LabelSize="10" LabelFace="96" CaptionFont="4" CaptionSize="10" HashSpacing="2.49" '
            'MarginWidth="1.58" LineWidth="1.13" BoldWidth="2.27" BondLength="14.40" BondSpacing="18" ChainAngle="120" '
            'LabelJustification="Auto" CaptionJustification="Left" AminoAcidTermini="HOH" LabelLineHeight="14" '
            'CaptionLineHeight="14" PrintMargins="18 18 18 18" MacPrintInfo="%s" color="0" bgcolor="1">'
            '<colortable>%s</colortable><fonttable><font id="3" charset="iso-8859-1" name="Arial"/>'
            '<font id="4" charset="iso-8859-1" name="Lato"/></fonttable>'
            '<page id="1" BoundingBox="0 0 %d %d" WidthPages="1" HeightPages="1" HeaderPosition="36" FooterPosition="36">'
            % (escape(doc.name), page[0], page[1], mpi, ct, page[0], page[1]))
    with open(path, "w", encoding="utf8") as fh:
        fh.write(head + "\n".join(doc.items) + "</page></CDXML>\n")
