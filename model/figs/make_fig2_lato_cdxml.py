"""Figure 2 in Lato, from Jonas Rein's ChemDraw source, with Connor Coley's comments 7 and 8 addressed.

Author, 2026-09-21: "Fig 2, '/Users/justinbui/Downloads/Figure (1).cdxml' Jonas sent me this updated cdxml, but it needs
to be moved into Lato and the things need to be fixed." The file he sent is byte-identical to Figures/Figure.cdxml
(md5 1840df2f, Sep 7), so that is the source read here. It is NEVER written; the transformed copy is
Figures/Figure2_Lato.cdxml.

WHAT CHANGES, AND NOTHING ELSE
  font     every caption (text not inside an atom node) moves Arial -> Lato; atom labels stay Arial -- the rule Figure 3
           was built to ("Lato for everything, but Arial for the atoms in the molecules"). Captions go upright, as in the
           finished Illustrator Figure 2, except "radical/cation precursors" (italic there too).
  #8       the bottom-left header ran "chemoselectivityby" in the Illustrator export; the source has the space, and a
           ChemDraw render keeps it.
  #7       the reactions are balanced where the figure omitted a product or the electrons:
             Kolbe            "- 2 e-" and "- 2 CO2" under the arrow (2 RCO2- -> R-R + 2 CO2 + 2 e-)
             diazidation      "- 2 e-" under the arrow (alkene + 2 N3- -> 1,2-diazide + 2 e-)
             Appel-type step  ", - HBr" after "- Ph3P=O" (Ph3PBr2 + ROH -> RBr + Ph3P=O + HBr)
  sign     the bottom-left CATHODE step read "- e-, Br-": R-Br + e- -> R. + Br- is a reduction, so "+ e-, - Br-".
  typo     "N-hetrocycles" -> "N-heterocycles".
  page     one legal-landscape page with 18 pt margins (the source used 172 pt margins over a 10 x 7 page grid, which is
           why ChemDraw split it across pages), and the two off-frame URL notes to the right of the figure are dropped.

CONTENT, AUTHOR'S RULING (2026-09-21: "probably keep what Jonas did we don't want to mess up his intended goal"): the
source is richer than the Illustrator figure the manuscript embedded through v120 -- a fourth precursor in the
radical/cation box (a benzylic C-H, "e.g. in BASF Lysmeral synthesis") and the Ni cathode half of the coupled cell in the
bottom-right panel, both dropped in Illustrator (the latter for a bare blue cycle icon). Both are KEPT, as Jonas drew
them; KEEP_* stay at their defaults.

    python figs/make_fig2_lato_cdxml.py            # writes Figures/Figure2_Lato.cdxml
    python figs/make_fig2_lato_cdxml.py --render   # and renders it through ChemDraw to Figures/Figure2_Lato.{pdf,png}
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIG = os.path.join(ROOT, "Figures")
SRC = os.path.join(FIG, "Figure.cdxml")
SRC_MD5 = "1840df2fbfee07fd7c25907d63166dce"
_OUTBASE = "Figure2_Lato"
LATO = "4"                                  # font id added to the fonttable (Arial is 3, as in the source)
KEEP_BENZYLIC = os.environ.get("FIG2_KEEP_BENZYLIC", "1") == "1"
KEEP_NI_CATHODE = os.environ.get("FIG2_KEEP_NI_CATHODE", "1") == "1"
# FIG2_BALANCE -- an OPTION, off by default, so the shipped render is untouched (the FIG6_GH_NORM pattern).
#   0  the pre-2026-10-01 figure.  Every electrode step already carries its electron count, Kolbe carries "- 2 e-, - 2 CO2"
#      and the diazidation "- 2 e-" (all added at v121), so the figure is already balanced almost everywhere.
#   1  + the one genuinely unbalanced arrow: the cathodic Ni cross-electrophile coupling shows "+ 2 e-" but
#      never the two bromides it expels.  R-Br + Ar-Br + 2 e- -> R-Ar + 2 Br-.
#   2  + the stoichiometry of the radical dimerisation, which is drawn as one R* giving R-R where it takes two.
#      MEASURED AND IT DOES NOT FIT: an ink map of that region leaves exactly one clear band, y 86-89 pt, four
#      points tall, against the ten a label needs -- "transient" sits at y 92-97 and the arrow shaft at y 100.
#      Rendered, the label lands on Jonas's own annotation. Kept only so the collision can be seen; the panel
#      already teaches the 2:1 stoichiometry in its own Kolbe scheme ("2" on the carboxylate), so repeating it
#      on the cartoon above buys nothing. Use BALANCE=1.
# Document coordinates are read off the FINISHED PDF and converted: doc_x = pdf_centre_x + 23.43,
# doc_y = pdf_baseline_y + 52.90, pinned against the Kolbe label whose doc position this file already sets.
# ADOPTED 2026-10-01 (author: "do both of your recommended options"): 1 is the SHIPPED state and renders to
# the shipped names; any other value is an option and carries a suffix, so it can never overwrite them.
BALANCE = int(os.environ.get("FIG2_BALANCE", "1"))
OUT_SUFFIX = "" if BALANCE == 1 else "_balance%d" % BALANCE
OFF_FRAME_IDS = ("2118248874", "2118248630")  # the two URL notes to the right of the frame
ELECTRODES = ("2118247343", "2118247997", "2118248989", "2118248992", "2118249173")   # the five 7.5 pt grey bars
CORNER = 160                                # ChemDraw CornerRadius units; 160 -> 1.8 pt (cdxml_style.CORNER)
FRAME = (23.43, 52.88, 727.93, 362.49)      # x, y, w, h in document coordinates: the content box + 4 pt, at the embedded
                                            # figure's own 728 x 362.5 pt canvas, so bonds and text print at the same scale


OUT = os.path.join(FIG, _OUTBASE + OUT_SUFFIX + ".cdxml")


def md5(path):
    import hashlib
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def remove_element(x, tag, idd):
    """Delete the whole <tag id="idd" ...>...</tag> element (nesting-aware)."""
    m = re.search(r'<%s\b[^>]*\bid="%s"[^>]*>' % (tag, idd), x, re.S)
    if not m:
        raise SystemExit("no <%s id=%s> in the source" % (tag, idd))
    if m.group(0).endswith("/>"):
        return x[:m.start()] + x[m.end():]
    depth, pos = 1, m.end()
    for mm in re.finditer(r"<(/?)%s\b[^>]*?(/?)>" % tag, x[pos:], re.S):
        if mm.group(1):
            depth -= 1
        elif not mm.group(2):
            depth += 1
        if depth == 0:
            return x[:m.start()] + x[pos + mm.end():]
    raise SystemExit("unbalanced <%s id=%s>" % (tag, idd))


def caption_spans(x):
    """(start, end) of every <t>...</t> that is NOT inside an atom node <n>."""
    out, stack = [], []
    for m in re.finditer(r"<(/?)(\w+)\b[^>]*?(/?)>", x, re.S):
        close, tag, selfc = m.groups()
        if close:
            if stack and stack[-1][0] == tag:
                t, s = stack.pop()
                if tag == "t" and not any(a == "n" for a, _ in stack):
                    out.append((s, m.end()))
            continue
        if not selfc:
            stack.append((tag, m.start()))
    return out


def text_of(t):
    return html.unescape("".join(re.findall(r"<s\b[^>]*>(.*?)</s>", t, re.S)))


def s_run(text, face="0", size="10", color=None):
    c = ' color="%s"' % color if color else ""
    return '<s font="%s" size="%s"%s face="%s">%s</s>' % (LATO, size, c, face, html.escape(text, quote=False))


def caption(x0, y0, runs, just="Center"):
    """A new free-standing caption (CaptionJustification centred on x0), in Lato."""
    return ('<t p="%.2f %.2f" Justification="%s" CaptionJustification="%s" InterpretChemically="no">%s</t>'
            % (x0, y0, just, just, "".join(s_run(*r) for r in runs)))


def main():
    if md5(SRC) != SRC_MD5:
        raise SystemExit("Figures/Figure.cdxml is not the file Jonas sent (md5 %s)" % md5(SRC))
    x = open(SRC, encoding="utf8").read()

    # ---- page: one legal-landscape page, 18 pt margins; Lato in the fonttable; Lato as the caption default --------
    x = re.sub(r'PrintMargins="[^"]*"', 'PrintMargins="18 18 18 18"', x, count=1)
    x = re.sub(r'CaptionFont="3"', 'CaptionFont="%s"' % LATO, x, count=1)
    x = re.sub(r"(<font id=\"3\"[^>]*/>)", r'\1<font id="%s" charset="iso-8859-1" name="Lato"/>' % LATO, x, count=1)
    x = re.sub(r'(<page\b[^>]*?)BoundingBox="[^"]*"', r'\1BoundingBox="0 0 972 576"', x, count=1, flags=re.S)
    x = re.sub(r'(<page\b[^>]*?)HeightPages="\d+"', r'\1HeightPages="1"', x, count=1, flags=re.S)
    x = re.sub(r'(<page\b[^>]*?)WidthPages="\d+"', r'\1WidthPages="1"', x, count=1, flags=re.S)

    # ---- off-frame notes; optional content the Illustrator version dropped --------------------------------------
    x = remove_element(x, "group", OFF_FRAME_IDS[0])
    x = remove_element(x, "t", OFF_FRAME_IDS[1])
    if not KEEP_BENZYLIC or not KEEP_NI_CATHODE:
        raise SystemExit("trimming to the Illustrator content is not implemented yet: say which to drop and it will be")

    # ---- captions: Lato, upright (except the italic box title), and the text fixes ------------------------------
    spans = caption_spans(x)
    edits = {"lato": 0, "upright": 0}
    out, last = [], 0
    for s, e in spans:
        t = x[s:e]
        txt = text_of(t)
        t2 = re.sub(r'(<s\b[^>]*?)font="3"', r'\1font="%s"' % LATO, t)
        edits["lato"] += t2 != t
        keep_italic = txt.startswith("radical/cation precursors")
        if not keep_italic:
            def upright(m):
                f = int(m.group(1))
                return 'face="%d"' % (f & ~2)
            # every run upright except a lone italic "N" (the N- of N-heterocycles keeps its italic)
            t3 = re.sub(r'(<s\b[^>]*?)face="(\d+)"([^>]*>)(.*?)(</s>)',
                        lambda m: m.group(0) if (m.group(4) == "N" and int(m.group(2)) & 2 and "hetrocycles" in txt)
                        else m.group(1) + upright(re.match(r'face="(\d+)"', 'face="%s"' % m.group(2))) + m.group(3) + m.group(4) + m.group(5),
                        t2, flags=re.S)
            edits["upright"] += t3 != t2
            t2 = t3
        t2 = t2.replace("hetrocycles", "heterocycles")
        out.append(x[last:s])
        out.append(t2)
        last = e
    out.append(x[last:])
    x = "".join(out)
    if "hetrocycles" in x or "heterocycles" not in x:
        raise SystemExit("the heterocycles typo was not fixed")
    # chemistry review 2026-10-06: the two panel headers had "paired" and "coupled" swapped against the caption, the body
    # and the cited works -- both electrogenerated intermediates from ONE electrode is anodically COUPLED electrolysis
    # (Rein 2023, p. 8111, "anodically coupled electrolysis"); productive half-reactions at BOTH electrodes is PAIRED
    # electrolysis (Li 2021, the deoxygenative "paired electrolysis")
    for old, new in (("Anodically (or cathodically) paired electrolysis", "Anodically (or cathodically) coupled electrolysis"),
                     ("within the same cell, enabling coupled electrolysis.", "within the same cell, enabling paired electrolysis.")):
        if x.count(old) != 1:
            raise SystemExit("panel header %r occurs %d times" % (old, x.count(old)))
        x = x.replace(old, new)

    # chemistry audit 2026-10-06: of the legend's metals only Mn and Cu are supported by the works the figure cites -- Fu's
    # own catalyst screen (ref 16, SI Table S1) gives FeBr2 and Ni(OAc)2 below 10%, and no other cited work runs Fe or Ni
    # in this radical functionalization -- so the legend names the two it can show. The label's LineStarts are character
    # offsets of each line's end, so they move with the text.
    legs = [m for m in re.finditer(r"<t\b[^>]*>(?:(?!</t>).)*?M = Mn, Fe, Cu, Ni(?:(?!</t>).)*?</t>", x, re.S)]
    if len(legs) != 1:
        raise SystemExit("the metal legend occurs %d times" % len(legs))
    t_old = legs[0].group(0)
    if 'LineStarts="10 29 43"' not in t_old:
        raise SystemExit("the legend's line offsets are not the expected 10 29 43")
    t_new = t_old.replace("M = Mn, Fe, Cu, Ni", "M = Mn, Cu").replace('LineStarts="10 29 43"', 'LineStarts="10 21 35"')
    x = x[:legs[0].start()] + t_new + x[legs[0].end():]

    # the cathode step: "- e-, Br" -> "+ e-, - Br-" (a reduction), keeping the caption's own position
    m = re.search(r'(<t\b[^>]*\bp="52\.\d+ 361\.\d+"[^>]*>)(.*?)(</t>)', x, re.S)
    if not m or not text_of(m.group(2)).startswith("– e"):
        raise SystemExit("could not find the cathode step label")
    new_runs = "".join([s_run("+ e"), s_run("–", "64"), s_run(", – Br"), s_run("–", "64")])
    x = x[:m.start(2)] + new_runs + x[m.end(2):]
    # the source drew that label's Br charge as a separate Symbol graphic (x 89.0, y 353.7-361.2); the new label carries
    # the charge as a superscript run, and once "- " precedes Br the symbol would sit on the wrong glyph -- remove it
    x = remove_element(x, "graphic", "2118248928")

    # ---- #7: balancing labels, placed from the arrows' own coordinates -----------------------------------------
    add = [
        caption(314.8, 157.5, [("– 2 e",), ("–", "64")]),                     # Kolbe: bolt group ends at y 146.2
        caption(314.8, 169.0, [("– 2 CO",), ("2", "32")]),
        caption(288.8, 254.0, [("– 2 e",), ("–", "64")]),                     # diazidation: bolt ends near y 243
        caption(565.6, 406.2, [(", – HBr",)], just="Left"),                   # after "- Ph3P=O": the comma hugs the O (x 558.1-565.5)
    ]
    if BALANCE >= 1:
        # The Ni XEC arc prints "+ 2 e-" with its baseline at pdf (667.99, 321.89) and a right edge of
        # 692.9 once the superscript is counted, so its centre is doc x 703.9; one line below is 386.3.
        add.append(caption(703.9, 386.3, [("– 2 Br",), ("–", "64")]))
    if BALANCE >= 2:
        # the dimerisation R* -> R-R takes two radicals; the arrow runs pdf x 55..115 at y ~ 98
        add.append(caption(111.4, 144.9, [("\u00d7 2",)]))
    x = x.replace("</page>", "".join(add) + "</page>", 1)

    # ---- electrodes in Figure 3's style, which was measured off the finished Figure 2: 7.5 pt bar, 1.8 pt corners,
    # 0.6 grey fill, 1 pt black outline. The source's bars are colour 14 (0.6 grey STORED, which ChemDraw exports as
    # 0.664) with square corners and no outline; storing 0.532 exports as 0.600 (the calibration recorded for Figure 3).
    ct = re.search(r"<colortable>(.*?)</colortable>", x, re.S)
    n_ent = len(re.findall(r"<color [^>]*/>", ct.group(1)))
    x = x[:ct.end(1)] + '<color r="0.532" g="0.532" b="0.532"/>' + x[ct.end(1):]
    grey = n_ent + 2                                   # colortable entry k is colour index k + 1
    zmax = max(int(z) for z in re.findall(r'\bZ="(\d+)"', x))
    idmax = max(int(i) for i in re.findall(r'\bid="(\d+)"', x))
    for k, eid in enumerate(ELECTRODES):
        m = re.search(r'<graphic\b[^>]*\bid="%s"[^>]*/>' % eid, x, re.S)
        if not m or 'color="14"' not in m.group(0) or 'RectangleType="Filled"' not in m.group(0):
            raise SystemExit("electrode %s is not the grey filled bar this build expects" % eid)
        bar = (m.group(0).replace('color="14"', 'color="%d"' % grey)
                         .replace('RectangleType="Filled"', 'RectangleType="RoundEdge Filled" CornerRadius="%d"' % CORNER))
        bb = re.search(r'BoundingBox="([^"]+)"', m.group(0)).group(1)
        outline = ('<graphic id="%d" BoundingBox="%s" Z="%d" GraphicType="Rectangle" RectangleType="RoundEdge" '
                   'CornerRadius="%d" LineWidth="1" color="3"/>' % (idmax + 1 + k, bb, zmax + 1 + k, CORNER))
        x = x[:m.start()] + bar + outline + x[m.end():]

    open(OUT, "w", encoding="utf8").write(x)
    print("wrote %s: %d captions to Lato, %d set upright, cathode sign fixed, typo fixed, 4 balancing labels added, "
          "%d electrodes restyled" % (os.path.relpath(OUT, ROOT), edits["lato"], edits["upright"], len(ELECTRODES)))


PAGE_MARGIN = 18.0                          # PrintMargins: document (0, 0) lands at (18, 18) on ChemDraw's PDF page


def render():
    """ChemDraw -> vector PDF of the page -> the frame, cropped: Figures/Figure2_Lato.{pdf,png} (600 dpi)."""
    import tempfile
    import pymupdf
    sys.path.insert(0, HERE)
    from chemdraw_render import render as cd_render
    tmp = os.path.join(tempfile.mkdtemp(), "fig2_page.pdf")
    cd_render(OUT, [tmp])
    src = pymupdf.open(tmp)
    if len(src) != 1:
        raise SystemExit("ChemDraw split the figure over %d pages; the page setup is wrong" % len(src))
    x0, y0, w, h = FRAME[0] + PAGE_MARGIN, FRAME[1] + PAGE_MARGIN, FRAME[2], FRAME[3]
    hit = src[0].search_for("Anodically")                      # the frame must sit where we think it does
    if not hit or not (x0 < hit[0].x0 < x0 + w and y0 < hit[0].y0 < y0 + h):
        raise SystemExit("the top-left title is not inside the frame; the frame offset is wrong")
    out = pymupdf.open()
    pg = out.new_page(width=w, height=h)
    pg.show_pdf_page(pg.rect, src, 0, clip=pymupdf.Rect(x0, y0, x0 + w, y0 + h))
    out.save(os.path.join(FIG, _OUTBASE + OUT_SUFFIX + ".pdf"))
    pix = pg.get_pixmap(dpi=600)
    pix.save(os.path.join(FIG, _OUTBASE + OUT_SUFFIX + ".png"))
    print("rendered Figures/%s.{pdf,png}: %d x %d px" % (_OUTBASE + OUT_SUFFIX, pix.width, pix.height))


if __name__ == "__main__":
    main()
    if "--render" in sys.argv:
        render()
