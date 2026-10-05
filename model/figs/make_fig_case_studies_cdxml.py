"""Figure 3 (the four case studies, Alex's figure) rebuilt as a ChemDraw document in Figure 2's style.

Why: Figure 3 was assembled in Illustrator (its author had no ChemDraw), so its structures used ChemDraw-default
styling, its catalytic cycles were hand-drawn paths rather than circles, and no ChemDraw source existed to share.
This builds one: every molecule is real atoms and bonds (ChemDraw computes formulae and flags valence errors),
every cycle is a circular arc, and the style is Jonas Rein's Figure 2 (Figures/Figure.cdxml + Figure.pdf):
14.4 pt bonds, 1.13 pt lines, atom labels Arial 10, all other text Lato 10 (author instruction, 2026-09-18),
Figure 2's arrowheads, electrodes and dotted dividers. The frame is 728 pt wide, Figure 2's canvas; both figures
are placed 6.50 in wide in the manuscript, so bonds and text print at the same size in both.

Outputs (Figures/):
  Organic ESynth Case Studies Figure.cdxml           the editable source, saved by ChemDraw itself
  Organic ESynth Case Studies Figure_ChemDraw.pdf    vector, cropped to the 728 x 556 pt frame
  Organic ESynth Case Studies Figure_ChemDraw.png    600 dpi (Figure 2's embed is 600 dpi)

Once the .cdxml has been edited in ChemDraw, IT is the source and this script is superseded: it refuses to
overwrite an existing .cdxml unless run with --force.

Run: /opt/anaconda3/bin/python3.12 figs/make_fig_case_studies_cdxml.py      (ChemDraw 23 opens briefly)

Chemistry corrected from the Illustrator version (each checked against its source; listed for the author):
  * epoxidation: water enters on the Cl2 -> chlorohydrin step and OH- on the chlorohydrin -> epoxide step
    (Leow et al., Science 2020, 368, 1228, Eqs. 2-5); the halohydrin is the chlorohydrin, since the cycle runs on Cl-
  * AO route: the hydroquinone is anthracene-9,10-diol (drawn before as 9,10-dihydroanthracene-9,10-diol, whose
    sp3 C9/C10 is not the AO-process species); one anthraquinone, so the cycle closes on two species
  * oxoammonium drawn N+=O (a charge on O with an N=O double bond is a formal-charge error)
  * electron labels in Figure 2's signed notation; 2 I- -> I2 is - 2 e-, TEMPOH -> TEMPO* is - e-, - H+
Corrected again on 2026-09-21 for Connor Coley's comment 17 ("show the alkene coming in with its own arrow merging
with the cycle, then show the epoxide coming off of the cycle ... double and triple check all of these schemes"):
  * epoxidation: the ring is now the MEDIATOR loop alone (2 Cl- -> Cl2 -> chlorohydrin -> 2 Cl-); the alkene enters on
    its own arrow and the epoxide leaves on its own, so the drawing no longer puts substrate species on the cycle
  * hydrazine, mediated route: the second N-I step consumes a SECOND ammonia, so that arc reads "+ NH3", not "x 2".
    With "x 2" the turn would need two I2 and four electrons against the "- 2 e-" it prints; as drawn,
    I2 + 2 NH3 -> N2H4 + 2 HI, which the anodic 2 I- -> I2 + 2 e- closes exactly. Its ring is the mediator loop
    alone too (I2 / I-NH2 / 2 I-), with both ammonias entering on arcs and the hydrazine leaving on its own arrow
  * valorization: the carboxylic acid LEAVES the cycle, so its label is "- R-COOH" in the figure's signed notation
Corrected 2026-09-21 (author: "Fix Figure 3 if it is inaccurate, but we also want it to be general"): the hydrazine
panel drew NH3 / NH2* / I-NH2 and made hydrazine directly, while the cited work couples the ketone-protected IMINE and
reaches hydrazine only by hydrolysing the azine. It now draws a general R2C=NH, its iminyl radical R2C=N* and the N-I
intermediate R2C=N-I -- which is what the two boxes already claimed -- with both routes ending at the azine and one
hydrolysis line returning hydrazine and the ketone.
"""
import math
import os
import sys

import cdxml_style as cdx
from cdxml_style import L, Doc, Mol, emit_mol, CH2OH, CH3O, CHO, COOH, width, runs, runs_width

W = 728.0
XM = 364.7                      # vertical divider (Figure 2: 364.7)
# FIG3_COUNTER -- an OPTION, off by default, so the shipped render is untouched.
#   0  the balance is a line of text in a 16 pt footer strip (shipped JR31 to 2026-10-01).
#   1  the counter electrode is DRAWN: a grey bar of the panels' own style at the right of a 30 pt strip,
#      with its half-reaction right-justified against it, so each panel reads as a cell with two electrodes.
# WHY NOT A MIRROR BAR INSIDE THE CELL, which is the physical picture: measured over the working
# electrode's own y-band, the free strip at the panel's right edge is 41.5 pt in A and 71.5 in B but only
# 12.1 in C and 11.9 in D, against the ~16 a bar needs -- it fits in half the panels, and a counter
# electrode drawn in two panels and not the other two is worse than none. Widening the canvas is not
# available either: 728 pt IS Figure 2's canvas, and both figures are placed 6.50 in wide so that bonds and
# text print at the same size in each; widening this one alone would break that.
# ADOPTED 2026-10-01 (author: "do both of your recommended options"): 2 is the SHIPPED state.
COUNTER = int(os.environ.get("FIG3_COUNTER", "2"))
# 21 pt, not 30: ChemDraw's page is Figure 2's legal landscape (612 pt tall) with 18 pt margins and the
# frame origin at OFFSET 10, so the frame may be at most 612 - 18 - 18 - 10 = 566 pt and the two strips
# together may add at most 42. A 30 pt strip overflows and ChemDraw refuses the document outright.
FOOT = 21.0 if COUNTER else 16.0   # footer strip per row: the counter-electrode balance (Jonas Rein, Figure 3)
Y2 = 262.0 + FOOT               # horizontal divider; row 1 keeps its 262 pt of drawing and gains the strip
H = 524.0 + 2 * FOOT            # row 2 is drawn at y0 = Y2, so it moves down with it and gains its own strip


def pol(p, a, d=L):
    r = math.radians(a)
    return (p[0] + d * math.cos(r), p[1] - d * math.sin(r))


def hexagon(c, r=L):
    return [pol(c, a, r) for a in (90, 30, -30, -90, -150, 150)]


# ---------------------------------------------------------------- molecules
class M(Mol):
    """Mol with de-duplicated atoms (fused rings share vertices)."""

    def pt(self, p, **kw):
        for i, a in enumerate(self.atoms):
            if abs(a["x"] - p[0]) < 0.05 and abs(a["y"] - p[1]) < 0.05:
                return i
        return self.at(p[0], p[1], **kw)


def mol_bbox(doc, n_before):
    bs = doc.boxes[n_before:]
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def place(doc, build, cx, cy):
    """Build a molecule around (0, 0), then shift it so its drawn bounding box is centred on (cx, cy)."""
    probe = Doc("probe")
    emit_mol(probe, build(0.0, 0.0))
    x0, y0, x1, y1 = mol_bbox(probe, 0)
    dx, dy = cx - (x0 + x1) / 2, cy - (y0 + y1) / 2
    n = len(doc.boxes)
    emit_mol(doc, build(dx, dy))
    return mol_bbox(doc, n)


def mol_height(build):
    """The height of a structure's drawn bounding box, measured without emitting it (as `place` does)."""
    probe = Doc("probe")
    emit_mol(probe, build(0.0, 0.0))
    x0, y0, x1, y1 = mol_bbox(probe, 0)
    return y1 - y0


def alkene(x, y):
    m = M()
    a, b = m.at(x - 7.2, y), m.at(x + 7.2, y)
    m.bd(a, b, 2)
    for base, angs in ((a, (120, 240)), (b, (60, -60))):
        for ang in angs:
            m.bd(base, m.at(*pol((m.atoms[base]["x"], m.atoms[base]["y"]), ang)))
    return m


def chlorohydrin(x, y):
    m = M()
    a, b = m.at(x - 7.2, y), m.at(x + 7.2, y)
    m.bd(a, b)
    pa, pb = (x - 7.2, y), (x + 7.2, y)
    m.bd(a, m.at(*pol(pa, 90))); m.bd(a, m.at(*pol(pa, 180)))
    m.bd(b, m.at(*pol(pb, 90))); m.bd(b, m.at(*pol(pb, 0)))
    m.bd(a, m.at(*pol(pa, 240), 8, "OH", H=1, just="Right"))        # ChemDraw prints "HO"
    m.bd(b, m.at(*pol(pb, 300), 17, "Cl", H=0))
    return m


def epoxide(x, y):
    m = M()
    a, b = m.at(x - 7.2, y), m.at(x + 7.2, y)
    o = m.at(x, y + 12.47, 8, "O", H=0)
    m.bd(a, b); m.bd(a, o); m.bd(b, o)
    for base, angs in ((a, (135, 225)), (b, (45, -45))):
        for ang in angs:
            m.bd(base, m.at(*pol((m.atoms[base]["x"], m.atoms[base]["y"]), ang)))
    return m


def anthracene_core(m, x, y):
    d = math.sqrt(3) * L
    rings = [hexagon((x + k * d, y)) for k in (-1, 0, 1)]
    idx = [[m.pt(p) for p in r] for r in rings]
    return rings, idx


def anthraquinone(x, y):
    m = M()
    rings, idx = anthracene_core(m, x, y)
    L_, C_, R_ = idx          # vertex order: top, UR, LR, bottom, LL, UL
    # left ring (benzenoid, fused bond UR-LR double)
    for i, j, o in ((0, 1, 1), (1, 2, 2), (2, 3, 1), (3, 4, 2), (4, 5, 1), (5, 0, 2)):
        m.bd(L_[i], L_[j], o)
    for i, j, o in ((0, 1, 2), (1, 2, 1), (2, 3, 2), (3, 4, 1), (4, 5, 2), (5, 0, 1)):
        m.bd(R_[i], R_[j], o)
    for i, j in ((0, 1), (2, 3), (3, 4), (5, 0)):
        m.bd(C_[i], C_[j])
    m.bd(C_[0], m.at(x, y - 2 * L, 8, "O", H=0), 2)
    m.bd(C_[3], m.at(x, y + 2 * L, 8, "O", H=0), 2)
    return m


def anthrahydroquinone(x, y):
    """Anthracene-9,10-diol (the hydroquinone of the AO process), a valid Kekule structure."""
    m = M()
    rings, idx = anthracene_core(m, x, y)
    L_, C_, R_ = idx
    for i, j, o in ((0, 1, 1), (1, 2, 2), (2, 3, 1), (3, 4, 2), (4, 5, 1), (5, 0, 2)):
        m.bd(L_[i], L_[j], o)                      # left ring benzenoid
    m.bd(C_[0], C_[1], 2); m.bd(C_[2], C_[3], 2)   # C9=C8a, C10=C10a
    m.bd(C_[3], C_[4]); m.bd(C_[5], C_[0])
    m.bd(C_[1], C_[2])                             # fused bond with the right ring (R_[5]-R_[4]), single
    for i, j, o in ((5, 0, 1), (0, 1, 2), (1, 2, 1), (2, 3, 2), (3, 4, 1)):
        m.bd(R_[i], R_[j], o)                      # right ring o-quinoid: the only Kekule form with C9/C10 aromatic
    m.bd(C_[0], m.at(x, y - 2 * L, 8, "OH", H=1), 1)
    m.bd(C_[3], m.at(x, y + 2 * L, 8, "OH", H=1), 1)
    return m


def tempo(x, y, state):
    """TEMPO species with N at (x, y): '+' oxoammonium (N+=O), '.' nitroxyl, 'H' hydroxylamine."""
    m = M()
    N = m.at(x, y, 7, "N", H=0, charge=(1 if state == "+" else 0))
    v = hexagon((x, y + L))
    ring = [N] + [m.at(*p) for p in v[1:]]
    for i in range(6):
        m.bd(ring[i], ring[(i + 1) % 6])
    for ci, angs in ((1, (0, 60)), (5, (180, 120))):
        for ang in angs:
            m.bd(ring[ci], m.at(*pol(v[ci], ang)))
    if state == "+":
        m.bd(N, m.at(x, y - L, 8, "O", H=0), 2)
    elif state == ".":
        m.bd(N, m.at(x, y - L, 8, "O", H=0, radical=True))
    else:
        m.bd(N, m.at(x, y - L, 8, "OH", H=1))
    return m


def benzyl(x, y, top):
    """Vanillyl alcohol (top='CH2OH') or vanillin (top='CHO'): 4-substituted 2-methoxyphenol, ring pointy-top."""
    m = M()
    v = hexagon((x, y))
    r = [m.at(*p) for p in v]
    for i, o in zip(range(6), (1, 2, 1, 2, 1, 2)):
        m.bd(r[i], r[(i + 1) % 6], o)
    inner = CH2OH if top == "CH2OH" else CHO
    m.bd(r[0], m.at(x, y - 2 * L, 6, top, just="Left", inner=inner))
    m.bd(r[3], m.at(x, y + 2 * L, 8, "OH", H=1))
    om = pol(v[4], -150)
    m.bd(r[4], m.at(om[0], om[1], 8, "OCH3", just="Right", inner=CH3O))    # displays H3CO
    return m


def furan(x, y, g2, g5):
    """2,5-disubstituted furan, ring O on the left, substituents up (C2) and down (C5)."""
    m = M()
    R5 = L / (2 * math.sin(math.radians(36)))
    c = (x, y)
    O = m.at(*pol(c, 0, R5), 8, "O", H=0)
    c2, c3, c4, c5 = (m.at(*pol(c, a, R5)) for a in (72, 144, -144, -72))
    m.bd(O, c2); m.bd(c2, c3, 2); m.bd(c3, c4); m.bd(c4, c5, 2); m.bd(c5, O)
    inner = {"CHO": CHO, "CH2OH": CH2OH, "COOH": COOH}
    for cc, g, a in ((c2, g2, 72), (c5, g5, -72)):
        p = pol((m.atoms[cc]["x"], m.atoms[cc]["y"]), a)
        m.bd(cc, m.at(p[0], p[1], 6, g, just="Left", inner=inner[g]))
    return m


# ---------------------------------------------------------------- cycles
def inside(p, b, g):
    return b[0] - g <= p[0] <= b[2] + g and b[1] - g <= p[1] <= b[3] + g


def cycle_arc(doc, c, R, a0, a1, b0, b1, gap=3.0, heads=True):
    """Circular arc from species box b0 (near angle a0) to b1 (near a1), clockwise when a1 < a0, trimmed to
    leave `gap` pt clear of both boxes."""
    step = 0.1 if a1 > a0 else -0.1
    n = int(round((a1 - a0) / step))
    pts = [(a0 + k * step, pol(c, a0 + k * step, R)) for k in range(n + 1)]
    s = next(a for a, p in pts if not inside(p, b0, gap))
    e = next(a for a, p in reversed(pts) if not inside(p, b1, gap))
    doc.arc(c, R, R, s, e, heads)
    return s, e


def species(doc, x, y, markup):
    """A text species centred on (x, y), where y is the visual centre of capitals."""
    return doc.text(x, y + 3.6, markup, "Center")


def build():
    d = Doc("Organic ESynth Case Studies Figure.cdxml")
    # dividers, as Figure 2
    d.divider((XM, 3.9), (XM, H - 3.9))
    d.divider((4.6, Y2), (XM - 1.3, Y2))
    d.divider((XM + 4.6, Y2), (W - 3.3, Y2))

    # ============================================================ A. olefin epoxidation
    d.text(XM / 2, 10.8, "Olefin Epoxidation", "Center", bold=1)
    d.text(XM / 2, 24.8, "Anodically generated halogen mediators shuttle\noxidizing equivalents to the olefin", "Center")
    d.electrode(5.65, 46, 228, "anode")
    R, c = 76.0, (14.5 + 76.0, 140.0)
    # The RING is the mediator loop (2 Cl- -> Cl2 -> chlorohydrin -> 2 Cl-); the substrate joins it on its own
    # arrow and the product leaves on its own (Connor Coley, comment 17). Leow et al., Science 2020, Eqs. 2-5:
    #   2 Cl- -> Cl2 + 2 e-  |  Cl2 + alkene + H2O -> chlorohydrin + H+ + Cl-  |  chlorohydrin + OH- -> epoxide + Cl- + H2O
    bCl2 = species(d, *pol(c, 128, R), "Cl_2")
    bCH = place(d, chlorohydrin, *pol(c, 34, R))
    b2Cl = species(d, *pol(c, 232, R), "2 Cl^–")
    cycle_arc(d, c, R, 128, 34, bCl2, bCH)
    cycle_arc(d, c, R, 34, -128, bCH, b2Cl)
    cycle_arc(d, c, R, 232, 128, b2Cl, bCl2)
    # the alkene enters, merging into the Cl2 -> chlorohydrin arc; water enters on the arc itself
    bAlk = place(d, alkene, 182, 57)
    d.arrow((bAlk[0] - 5, 66), pol(c, 56, R))      # the head lands ON the arc, so the alkene visibly merges into it
    d.text(c[0] + 4, c[1] - R - 5, "+ H_2O", "Center")
    # the epoxide leaves the chlorohydrin -> 2 Cl- arc; hydroxide enters it
    bEp = place(d, epoxide, 182, 215)
    d.arrow(pol(c, -55, R), (bEp[0] - 5, 211))     # springs from the arc itself
    d.text(*pol(c, -8, R + 5), "OH^–")
    d.text(14.5 + 6, c[1] + 3.6, "– 2 e^–")
    # box
    bx = 268
    d.box(bx - 66, 124, bx + 66, 155)
    d.text(bx, 136.5, "j = 1 A cm^{–2}\nProduct specificity ≈ 97%", "Center")

    # ============================================================ B. electrochemical H2O2
    xB = XM
    d.text(xB + XM / 2, 10.8, "Electrochemical H_2O_2", "Center", bold=1)
    d.text(xB + 72, 24.8, "Direct Electrosynthesis", "Center")
    d.text(xB + 256, 24.8, "Mediated AO Route", "Center")
    # direct
    e1 = xB + 16.1
    d.electrode(e1, 40, 222, "cathode")
    ax = e1 + 7.5 + 14.5
    d.text(ax + 4, 72 + 3.6, "O_2")
    d.text(ax + 4, 140 + 3.6, "H_2O_2")
    d.arc((ax, 106), ax - (e1 + 8.3), 34, 90, 270)
    d.text(e1 + 8.3 + 5, 106 + 3.6, "+ 2 e^–, + 2 H^+")
    d.box(e1 + 11, 163, e1 + 11 + 94, 207)
    d.text(e1 + 11 + 47, 175.5, "30 wt% H_2O_2;\n~1,000 h at 20 wt%\nvia PSE reactors", "Center")
    # mediated AO
    e2 = xB + 142
    d.electrode(e2, 40, 222, "cathode")
    R2 = 60.0
    c2 = (e2 + 8.3 + R2, 130.0)
    bTop = place(d, anthrahydroquinone, c2[0], c2[1] - R2)
    bBot = place(d, anthraquinone, c2[0], c2[1] + R2)
    cycle_arc(d, c2, R2, 270, 90, bBot, bTop)
    cycle_arc(d, c2, R2, 90, -90, bTop, bBot)
    d.text(e2 + 8.3 + 5, c2[1] + 3.6, "+ 2 e^–, + 2 H^+")
    d.text(*pol(c2, 32, R2 + 5), "+ O_2")
    d.text(*pol(c2, -40, R2 + 5), "– H_2O_2")
    d.box(c2[0] - 26 - 3, 230, c2[0] - 26 + 160 + 3, 256)
    d.text(c2[0] - 26 + 80, 240.5, "Pd- and distillation-free H_2O_2 via\nquinone-mediated electrochemistry", "Center")

    # ============================================================ C. electrochemical hydrazine
    y0 = Y2
    d.text(XM / 2, y0 + 19, "Electrochemical Hydrazine", "Center", bold=1)
    d.text(78, y0 + 33, "Base-Promoted PCET", "Center")
    d.text(266, y0 + 33, "Redox-Mediated Route", "Center")
    d.electrode(5.65, y0 + 45, y0 + 200, "anode")
    px = 5.65 + 7.5 + 14.0
    # The substrate is the KETONE-PROTECTED imine, not ammonia: Wang, Gerken, Bates, Kim & Stahl couple benzophenone
    # imine, "a readily accessible ammonia surrogate ... with only one N-H bond", and "oxidative coupling of the imine
    # affords the N-N-coupled ketazine, and subsequent hydrolysis affords hydrazine and regenerates the ketone"
    # (JACS 2020, p. 1). Drawn as R2C=NH so the panel stays general, which is also how Section 2.2.3 puts it
    # ("ketones as recyclable protecting groups: imine formation stabilizes the N-N-forming intermediates").
    d.text(px + 4, y0 + 72 + 3.6, "R_2C=NH")
    d.text(px + 4, y0 + 136 + 3.6, "R_2C=N^•")
    d.arc((px, y0 + 104), px - 13.95, 32, 90, 270)
    d.text(13.95 + 5, y0 + 104 + 3.6, "– e^–, – H^+")
    d.arrow((px + 52, y0 + 136), (px + 88, y0 + 136))
    d.text(px + 70, y0 + 131, "× 2", "Center")
    d.text(px + 92, y0 + 136 + 3.6, "azine")
    d.box(38, y0 + 158, 38 + 128, y0 + 203)
    d.text(38 + 64, y0 + 170.5, "High-energy iminyl radical\nintermediate incurs steep\noverpotential (η ≈ 1.6 V)", "Center")
    # redox-mediated
    e3 = 176.0
    d.electrode(e3, y0 + 45, y0 + 200, "anode")
    R3 = 58.0                       # 66 before the imine labels: '+ R2C=NH' on the right arc ran off the panel
    c3 = (e3 + 8.3 + R3, y0 + 126.0)
    # as in panel A, the ring is the mediator loop alone: ammonia enters on each N-I step and hydrazine leaves.
    # I2 + NH3 -> I-NH2 + HI, then I-NH2 + NH3 -> N2H4 + HI, so one I2 (2 e-) turns two ammonias into one hydrazine
    bI2 = species(d, *pol(c3, 125, R3), "I_2")
    bIN = species(d, *pol(c3, 55, R3), "R_2C=N–I")
    bI = species(d, *pol(c3, 235, R3), "2 I^–")
    cycle_arc(d, c3, R3, 125, 55, bI2, bIN)
    cycle_arc(d, c3, R3, 55, -125, bIN, bI)
    cycle_arc(d, c3, R3, 235, 125, bI, bI2)
    d.text(*pol(c3, 90, R3 + 9), "+ R_2C=NH", "Center")
    d.text(c3[0] + R3 + 6, c3[1] + 3.6, "+ R_2C=NH")
    bN2 = d.text(c3[0] + 56, c3[1] + 68, "azine")
    d.arrow(pol(c3, -68, R3), (bN2[0] - 5, c3[1] + 64))
    # both routes stop at the azine; one hydrolysis returns the hydrazine and the ketone
    d.text(44, y0 + 222, "azine = R_2C=N–N=CR_2\n+ 2 H_2O → N_2H_4 + 2 R_2C=O")   # clear of the "anode" label
    d.text(e3 + 8.3 + 5, c3[1] + 3.6, "– 2 e^–")
    d.box(c3[0] - 30, y0 + 206, c3[0] + 102, y0 + 251)    # clear of the anode label after the ring moved left
    d.text(c3[0] + 36, y0 + 218.5, "N–I bond formation stabilizes\nthe N-intermediate, lowering\noverpotential to η ≈ 0.47 V",
           "Center")

    # ============================================================ D. feedstock valorization
    xD = XM
    d.text(xD + XM / 2, y0 + 19, "Electrochemical Feedstock Valorization", "Center", bold=1)
    d.text(xD + XM / 2, y0 + 33, "Electrogenerated oxoammonium ions drive alcohol\noxidation in diverse substrates",
           "Center")
    e4 = xD + 16.1
    d.electrode(e4, y0 + 56, y0 + 234, "anode")
    tx = e4 + 59.0
    ys = (y0 + 86, y0 + 144, y0 + 202)
    for yy, st in zip(ys, ("+", ".", "H")):
        emit_mol(d, tempo(tx, yy, st))
    lx = tx - 12.47 - 14.4 - 3.5           # left methyl end, minus a gap
    for (ya, yb), lab in (((ys[2], ys[1]), "– e^–\n– H^+"), ((ys[1], ys[0]), "– e^–")):
        yt, yh = ya + 7.2 - 3, yb + 7.2 + 3
        d.arc((lx, (yt + yh) / 2), lx - (e4 + 8.3), (yt - yh) / 2, 270, 90)
        nl = lab.count("\n")
        d.text(e4 + 8.3 + 5, (yt + yh) / 2 + 3.6 - 6 * nl, lab)
    rx0 = tx + 26.9 + 5
    d.text(rx0, ys[0] + 3.6, "+ R–CH_2OH")
    d.text(rx0, ys[2] + 3.6, "– R–COOH")
    ax4 = rx0 + 60
    d.arc((ax4, ys[1]), 16, (ys[2] - ys[0]) / 2, 90, -90)
    d.text(ax4 - 3, ys[1] + 3.6, "(via aldehyde)", "Right")
    # examples, each drawn top-to-bottom
    bx0 = ax4 + 22
    # Both example panels stand reactant and product on the same two baselines, so ONE arrow length and one
    # midpoint serve both. Alexandria, 2026-09-22: the lignin arrow must be as long as the HMF one -- drawn to
    # each structure's own bounding box they came out 18.4 and 25.3 pt, which reads as two different steps.
    # The shared span is the HMF panel's own clearance, which is the wider of the two, so the taller lignin
    # structures set the tighter margin; the assertion below binds it to that panel rather than to a literal.
    # The lignin product is an aromatic ALDEHYDE (vanillin), not the generic "monomer" the box claimed.
    YT, YB = y0 + 124, y0 + 220
    FTOP = lambda x, y: furan(x, y, "CHO", "CH2OH")
    FBOT = lambda x, y: furan(x, y, "COOH", "COOH")
    a_half = ((YB - mol_height(FBOT) / 2 - 3) - (YT + mol_height(FTOP) / 2 + 3)) / 2
    a_mid = (YT + YB) / 2
    b1 = (bx0, y0 + 54, bx0 + 96, y0 + 260)
    d.box(*b1)
    d.text((b1[0] + b1[2]) / 2, y0 + 66, "Ex: Lignin fragment\n→ aromatic aldehyde", "Center", bold=2)
    mc = (b1[0] + b1[2]) / 2
    t1 = place(d, lambda x, y: benzyl(x, y, "CH2OH"), mc, YT)
    t2 = place(d, lambda x, y: benzyl(x, y, "CHO"), mc, YB)
    d.arrow((mc - 14, a_mid - a_half), (mc - 14, a_mid + a_half))
    d.text(mc - 9, a_mid + 3.6, "[TEMPO^+]")
    b2 = (b1[2] + 5, y0 + 54, W - 4, y0 + 260)
    d.box(*b2)
    d.text((b2[0] + b2[2]) / 2, y0 + 66, "Ex: HMF\n→ FDCA", "Center", bold=2)
    mc2 = (b2[0] + b2[2]) / 2
    f1 = place(d, FTOP, mc2, YT)
    f2 = place(d, FBOT, mc2, YB)
    assert abs((f1[3] + 3) - (a_mid - a_half)) < 1e-9 and abs((f2[1] - 3) - (a_mid + a_half)) < 1e-9, \
        "the shared arrow span must reproduce the HMF panel's own clearance"
    d.arrow((b2[0] + 12, a_mid - a_half), (b2[0] + 12, a_mid + a_half))
    d.text(b2[0] + 16, a_mid + 3.6, "[TEMPO^+]")

    counter_electrode(d)
    return d


def counter_electrode(d):
    """The balancing half-reaction at the COUNTER electrode of each panel (Jonas Rein, Figure 3 comment:
    "add balance at the counter electrode for each of the examples in the figure ... because that is critical
    for the actual greenness of the process").  Only the working electrode is drawn in each scheme, so each
    line names the electrode that is NOT drawn and gives the reaction its own paper reports.

    Each is retrieved, not assumed, and the two that the literature leaves open are written as it leaves them:

    A  epoxidation (anode drawn).  Leow et al., Science 2020, 368, 1228-1233, p. 1229 Eq. 4, verbatim:
       "Cathode: 2H2O + 2e- -> H2 + 2OH-", and p. 1229: "The hydrogen evolution reaction ... at the cathode
       during electrolysis generates the necessary OH- (Eq. 4)".  So the cathode is not a sink here: it makes
       the hydroxide the drawn cycle consumes, and the overall Eq. 7 is C2H4 + H2O -> C2H4O + H2 -- water in,
       epoxide and H2 out, which is the greenness point.
    B  H2O2 (two cathodes drawn, so the counter electrode is the ANODE).  Both cited routes offer more than
       one anode reaction, so BOTH are printed rather than one being picked.  Xi et al., Nat. Chem. 2025
       (ref 28), p. 1888, on the condition that "the ionic charge carriers into the cathode are protons":
       "we show that the hydrogen oxidation reaction (HOR) against a cation exchange membrane (CEM), acidic
       oxygen evolution reaction (OER) against a CEM or alkaline OER against a bipolar membrane (BPM) can be
       used on the anode side", and the trade-off is theirs too -- "the HOR has the lowest energy cost but
       consumes hydrogen gas"; the acidic OER "commonly requires noble metal catalysts, such as IrO2"; "The
       alkaline OER with a BPM is a noble metal-free alternative".  Xia et al., Science 2019 (ref 27) runs HOR
       in its headline cell ("pure H2 and O2 streams separately introduced to the anode and cathode") and
       shows water oxidation as the alternative ("the oxidation reaction on the anode side could be flexibly
       modified").  An earlier draft of this note quoted ref 28 as saying "the only requirement for the counter
       electrode are protons"; THAT SENTENCE IS NOT IN THE PAPER -- it was a grep window read as a sentence,
       and the gate on this claim is what caught it.
    C  hydrazine (two anodes drawn).  Wang, Gerken, Bates, Kim & Stahl, JACS 2020 (ref 29): alcohols "serve as
       proton donors that facilitate H2 formation at the cathode".  The proton DONOR is deliberately not drawn:
       the same sentence is explicit that it is "postulated", and that the alkoxide co-products "may then
       diffuse into the bulk solution where they can serve as bases" -- a postulate belongs in prose, not on a
       figure, so the line claims only the proton reduction the paper states.
    D  valorization (anode drawn).  Rafiee, Konz, Graaf, Koolman & Stahl, ACS Catal. 2018 (ref 30): "H+ to H2
       at the cathode counter electrode maintains the pH during the reactions", and its Eq. 1 gives H2 as the
       sole byproduct.  That sentence calls it an "oxidation", which is a slip in the paper -- H+ -> H2 is a
       reduction -- so the reaction is written correctly here and the wording is not reproduced.
    """
    LEAD = "counter electrode"
    TXT = {"A": "%s (cathode): 2 H_2O + 2 e^– → H_2 + 2 OH^–" % LEAD,
           "B": "%s (anode): H_2 → 2 H^+ + 2 e^–   or   2 H_2O → O_2 + 4 H^+ + 4 e^–" % LEAD,
           "C": "%s (cathode): 2 H^+ + 2 e^– → H_2" % LEAD,
           "D": "%s (cathode): 2 H^+ + 2 e^– → H_2" % LEAD}
    if not COUNTER:
        y1, y2 = Y2 - 5.4, H - 5.4                  # one baseline in each row's footer strip
        d.text(5.65, y1, TXT["A"])
        d.text(XM + 16.1, y1, TXT["B"])
        d.text(5.65, y2, TXT["C"])
        d.text(XM + 16.1, y2, TXT["D"])
        return

    # FIG3_COUNTER=1: the electrode is drawn at the right of its own panel's strip, in the panels' own
    # style (electrode() is the same 7.5 pt bar with 1.8 pt corners the working electrodes use), and the
    # half-reaction is right-justified against it so the eye runs reaction -> electrode exactly as it does
    # left-to-right inside each cell.
    # COUNTER=1 puts the bar at the panel's RIGHT, so the eye runs reaction -> electrode, as it does
    # left-to-right inside each cell; COUNTER=2 puts it at the LEFT, directly under that panel's working
    # electrode, so the two bars line up and the pair reads as one cell in cross-section.
    for key, (px0, px1, strip_top) in {"A": (5.65, XM, Y2 - FOOT), "B": (XM + 16.1, W, Y2 - FOOT),
                                       "C": (5.65, XM, H - FOOT), "D": (XM + 16.1, W, H - FOOT)}.items():
        if COUNTER == 2:
            bx = px0                                # aligned with the working electrode above it
            d.electrode(bx, strip_top + 3.0, strip_top + 18.0)
            d.text(bx + 7.5 + 7.0, strip_top + 14.0, TXT[key])
        else:
            bx = px1 - 4.0 - 7.5                    # 4 pt clear of the panel edge
            d.electrode(bx, strip_top + 3.0, strip_top + 18.0)
            d.text(bx - 7.0, strip_top + 14.0, TXT[key], "Right")


FIGDIR = os.path.join(cdx.ROOT, "Figures")
BASE = "Organic ESynth Case Studies Figure"
# An option render NEVER writes the shipped names (the FIG6_GH_NORM rule).
_SFX = "" if COUNTER == 2 else "_counter%d" % COUNTER
OUT_CDXML = os.path.join(FIGDIR, BASE + _SFX + ".cdxml")
OUT_PDF = os.path.join(FIGDIR, BASE + _SFX + "_ChemDraw.pdf")
OUT_PNG = os.path.join(FIGDIR, BASE + _SFX + "_ChemDraw.png")
PAGE_MARGIN = 18.0              # PrintMargins: the frame's (0, 0) lands at OFFSET + 18 pt on ChemDraw's PDF page


def main(force=False):
    import shutil
    import tempfile
    import fitz
    from chemdraw_render import render
    if os.path.exists(OUT_CDXML) and not force:
        raise SystemExit("%s exists and may carry edits made in ChemDraw; refusing to overwrite (use --force)"
                         % OUT_CDXML)
    tmp = tempfile.mkdtemp(prefix="fig3_chemdraw_")
    gen = os.path.join(tmp, "case_studies_generated.cdxml")
    cdx.write(build(), gen)
    page_pdf, saved = os.path.join(tmp, "page.pdf"), os.path.join(tmp, BASE + ".cdxml")
    print("open after render:", render(gen, [page_pdf, saved]))

    ox, oy = cdx.OFFSET[0] + PAGE_MARGIN, cdx.OFFSET[1] + PAGE_MARGIN
    src = fitz.open(page_pdf)
    sp = src[0]
    # the frame must sit where we think it does: the vertical divider at x = XM
    xs = [dr["rect"].x0 for dr in sp.get_drawings() if dr.get("dashes") not in (None, "[] 0") and dr["rect"].height > 400]
    assert xs and abs(xs[0] - (ox + XM)) < 1.5, "divider not at the expected page position: %r" % xs
    fonts = {f[3].split("+")[-1] for f in sp.get_fonts()}
    assert fonts <= {"Lato-Regular", "Lato-Bold", "Lato-Italic", "ArialMT", "Arial-ItalicMT"}, "unexpected fonts: %r" % fonts
    # Arial italic may carry only the arrow of the italic box headers (Lato has no U+2192)
    ai = {s["text"] for b in sp.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]
          if s["font"].endswith("Arial-ItalicMT")}
    assert ai <= {"→", " →", "→ "}, "Arial italic used for %r" % ai
    greys = {round(dr["fill"][0], 3) for dr in sp.get_drawings() if dr.get("fill") and 0.3 < dr["fill"][0] < 0.9}
    assert greys and all(abs(v - 0.6) <= 1 / 255 for v in greys), "electrode grey %r; Figure 2's is 0.600" % greys
    out = fitz.open()
    pg = out.new_page(width=W, height=H)
    pg.show_pdf_page(pg.rect, src, 0, clip=fitz.Rect(ox, oy, ox + W, oy + H))
    out.save(OUT_PDF, garbage=4, deflate=True)
    pix = pg.get_pixmap(dpi=600)
    pix.set_dpi(600, 600)
    pix.save(OUT_PNG)
    shutil.copyfile(saved, OUT_CDXML)
    print("fonts: %s; electrode grey %s" % (", ".join(sorted(fonts)), sorted(greys)))
    for p in (OUT_CDXML, OUT_PDF, OUT_PNG):
        print("wrote", p)
    print("PNG %d x %d px (%.2f x %.2f in at 600 dpi)" % (pix.width, pix.height, pix.width / 600, pix.height / 600))


if __name__ == "__main__":
    main("--force" in sys.argv)
