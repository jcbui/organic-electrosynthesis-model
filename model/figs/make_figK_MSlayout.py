"""MS-layout render of the REMEDIATED Fig. K, for the manuscript's Figure 5 slot.

WHY THIS FILE EXISTS. figs/make_figK.py renders the analysis at 10.6 x 3.3 in (3 panels in
one row). The manuscript places every figure at 6.5 in printed width, so this file re-lays
the SAME three panels onto two rows at the printed size. NOTHING ABOUT THE PHYSICS OR THE
PANEL CONTENT IS CHANGED. Every constant comes from figs/thermal_model.py (the single source
of truth). This script does NOT write results/figK_thermal.json; it READS that file and
asserts that what it is about to draw is numerically identical to what the canonical
generator recorded, so the artwork can never drift from the published table. Run
make_figK.py first if the JSON is stale.

LAYOUT
    row 1 : (a) SOLVENT  |  (b) ARCHITECTURE
    row 2 : (c) COOLING DUTY, full width
    figure 6.5 x 5.33 in @ 600 dpi.

Panel (c) is kept in the main text on purpose: (b) is passive-cooling-only, and under the
remediated model the zero-gap PEM stack has a LOWER passive ceiling than the 250 um
microfluidic, so (a)+(b) alone read as "intensification does not fix boil-off". (c) shows
the fix is an ACTIVE cooling duty.

Redesign, 2026-09-07 (author instruction: the captions carry the text). The boil-off
markers stay; their "X boils at N" labels, the operating-condition box, the design-current
label and the reference-line labels are gone (all still printed to stdout and gated). The
three cooling bands in (c) keep one short name each, which is how the y-axis is read.

Output goes to the MS staging folder, never over figs/sec4_figK_boiloff.*.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))          # .../Section4_Model/figs
SEC4 = os.path.dirname(HERE)                               # .../Section4_Model
PERSP = os.path.dirname(SEC4)                              # .../Organic Electrosynthesis Perspective
OUTDIR = os.path.join(PERSP, "MS Drafts", "_replacement_artwork")

for cand in (SEC4, HERE, os.path.expanduser("~/Documents/CO2R-Bulk-Scale-Julia-Model")):
    if os.path.exists(os.path.join(cand, "customplot.py")):
        sys.path.insert(0, cand)
        os.chdir(cand)      # customplot loads "Color Swatches from UC Berkeley.xlsx" from cwd
        break
else:
    raise SystemExit("customplot.py not found; cannot run.")
from customplot import gengrid, rainbow_2

sys.path.insert(0, HERE)
import figstyle as FS
import matplotlib.patheffects as _pe
HALO = [_pe.withStroke(linewidth=2.4, foreground="white")]   # 2026-09-12 (author: "a lot of clashing
# here, the text on the lines and spilling out of the borders"): every label on this figure sits over
# a curve, a shaded band or a marker somewhere in the four-solvent sweep, so each carries a halo and
# each is placed in a gutter the data cannot enter.
from thermal_model import (TAMB, H_EXT, SIGMA_BEAKER, GAP_BEAKER, GAP_MICRO,
                           SOLVENTS as _SOLV, REACTORS,
                           COOLING_BANDS, U_passive, q_Wcm2, i_boil, U_required)

TICK, ANN, AX, SMALL = 7.0, 7.0, 8.5, 6.6   # 2026-09-08: nothing under 6.5 pt at 6.5 in printed width
BLUE = rainbow_2[1]; LBLUE = rainbow_2[2]; RED = rainbow_2[5]
GREEN = rainbow_2[0]; ORANGE = rainbow_2[6]
_SOLV_COL = {"THF": RED, "MeCN": LBLUE, "DMF": ORANGE, "aq. NaOH": BLUE}
SOLVENTS = [row + (_SOLV_COL[row[0]],) for row in _SOLV]

fig, axs, _ = gengrid(n_cols=2, n_rows=2, size_inches=(6.5, 6.15),
                      ticklabel_size=TICK, genlabels=False)
a, bx = axs[0][0], axs[0][1]
cx, dx = axs[1][0], axs[1][1]
# 2026-09-12 (author: "let's add the cooling info as a panel d"): the bottom row splits, so the
# figure carries the two geometric levers side by side -- (c) the gap, which sets how much heat is
# generated, and (d) the rejection duty that heat then demands.
# The grid is positioned EXPLICITLY rather than by tight_layout. With the architecture names on
# the inner side of (b) and (d) the figure needs a real gutter between the columns, and
# tight_layout does not reserve one for axes whose subplotspec is reassigned after creation -- it
# left the names lying across panels (a) and (c). wspace is a fraction of the axes width, so
# 0.46 x 2.37 in is about 1.1 in, which clears "rotating cyl. 3000 rpm" at 6.6 pt.
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.90], width_ratios=[1.0, 1.0],
                      left=0.098, right=0.988, top=0.955, bottom=0.095,   # top 0.972 -> 0.955 (2026-09-15): the letters ride above the axes and "a)"/"b)" ran off the canvas
                      wspace=0.46, hspace=0.26)
a.set_subplotspec(gs[0, 0]); bx.set_subplotspec(gs[0, 1])
cx.set_subplotspec(gs[1, 0]); dx.set_subplotspec(gs[1, 1])

# ── (a) SOLVENT: one reactor (unstirred beaker), four electrolytes ───────────
Lb, sigb, hib, iopb = REACTORS[0][1], REACTORS[0][2], REACTORS[0][3], REACTORS[0][4]
Ub = U_passive(sigb, hib)
ii = np.linspace(0.5, 150, 600)
print(f"(a) unstirred beaker: L {Lb} cm, U' {Ub:.4f} W cm-2 K-1, design current {iopb:.0f} mA cm-2")
a.set_xlim(0, 150); a.set_ylim(25, 200)     # set before any rotation: the angles are display-space


def _along_curve(ax, xs, ys, text, col, x_at, side=+1, fs=SMALL, gap_pt=8.0):
    """Write `text` along the curve at x = x_at, offset to one side along the display-space normal.
    The rotation is measured from the curve as DRAWN, so it follows the eye rather than the data
    units (2026-09-12, author: "the solvent should be labeled on the curve")."""
    f = lambda v: float(np.interp(v, xs, ys))
    dx = 0.06 * (ax.get_xlim()[1] - ax.get_xlim()[0])
    pa = ax.transData.transform((max(xs[0], x_at - dx), f(max(xs[0], x_at - dx))))
    pb = ax.transData.transform((min(xs[-1], x_at + dx), f(min(xs[-1], x_at + dx))))
    rot = float(np.degrees(np.arctan2(pb[1] - pa[1], pb[0] - pa[0])))
    nx, ny = -np.sin(np.radians(rot)), np.cos(np.radians(rot))
    pc = ax.transData.transform((x_at, f(x_at)))
    q = ax.transData.inverted().transform((pc[0] + side * gap_pt * fig.dpi / 72 * nx,
                                           pc[1] + side * gap_pt * fig.dpi / 72 * ny))
    ax.text(q[0], q[1], text, color=col, fontsize=fs, ha="center", va="center", rotation=rot,
            rotation_mode="anchor", zorder=7, path_effects=HALO)
    return rot


# where each solvent's name sits on its own curve: the temperature the curve has reached there, or,
# for a curve that never gets that hot inside the frame, a fraction of the way across it
_NAME_AT = {"THF": ("T", 168.0), "DMF": ("T", 138.0), "MeCN": ("T", 112.0), "aq. NaOH": ("x", 0.60)}
# the temperature sits at the right edge of its own rule, except for DMF: the MeCN curve crosses
# 153 C at 133 mA cm-2, so that one label stops short of the crossing
_TLAB_X = {"THF": 0.985, "MeCN": 0.985, "DMF": 0.845, "aq. NaOH": 0.985}
for lab, elyte, kap, Tb, prov, col in SOLVENTS:
    tt = TAMB + q_Wcm2(ii, kap, Lb) / Ub
    a.plot(ii, tt, color=col, lw=1.8, label=lab)
    ib = i_boil(kap, Lb, Tb, Ub)
    a.axhline(Tb, color=col, ls=":", lw=0.8, alpha=0.65)
    # ONLY the temperature on the rule; the solvent name goes on the curve (author, 2026-09-12)
    a.text(_TLAB_X[lab], Tb + 2.5, "%.0f $^\\circ$C" % Tb, transform=a.get_yaxis_transform(),
           fontsize=SMALL, color=col, ha="right", va="bottom", zorder=7, path_effects=HALO)
    mode, val = _NAME_AT[lab]
    if mode == "T" and tt.max() > val:
        x_at = float(np.interp(val, tt, ii))
    else:
        x_at = (val if mode == "x" else 0.6) * 150.0
    rot = _along_curve(a, ii, tt, lab, col, x_at)
    if ib < 150:
        a.plot([ib], [Tb], "o", color=col, ms=5.5, mec="white", mew=0.7, zorder=6)
    print(f"(a) {lab:9s} boils at {ib:.0f} mA cm-2 (T_b {Tb} C)" + ("" if ib < 150 else "  [off scale]")
          + f"; name on the curve at i = {x_at:.0f} mA cm-2, {rot:+.0f} deg")
# 2026-09-12 (author): the transport-ceiling rule comes off panel (a) -- panels (b) and (c) already
# carry that comparison for every architecture, and here it only crowded the four curves. What the
# panel did NOT say is what its horizontal rules are, so one legend entry now says it.
from matplotlib.lines import Line2D as _L2Da
# a white FRAME, not a new position (the Figure 5 quality-pass ruling): the only thing it covers is
# the THF curve above 170 C, which is a hundred degrees past that solvent's own boiling point and
# carries nothing a reader needs. Every clear corner of this panel is small enough that a frameless
# legend would sit on a curve that still matters.
FS.legend(a, handles=[_L2Da([0], [0], color="0.45", ls=":", lw=1.3, label="boil-off temperature")],
          loc="upper left", fontsize=ANN, bbox_to_anchor=(0.02, 0.99),
          frameon=True, framealpha=1.0, facecolor="white", edgecolor="0.85", borderpad=0.5)
a.set_xlabel("current density (mA cm$^{-2}$)", fontsize=AX)
a.set_ylabel("steady-state cell temperature ($^\\circ$C)", fontsize=AX)
# No legend in (a): each dotted rule is now labelled with the solvent it belongs to, which is
# what the legend was for. One less box over the curves.

# ── (b) THERMAL MARGIN: can each architecture run where transport says it can? ───────────────
# 2026-09-12, rebuilt (author: "what the fuck is b showing"). It had plotted the absolute boil-off
# ceiling per architecture per solvent AND the architecture's transport ceiling as a separate black
# tick, so answering the panel's own question meant comparing two encodings across a log axis: four
# coloured markers against a floating tick. That is two numbers where the question is one.
#
# The question is whether the cell can reject the heat at the current transport allows, which is the
# RATIO of those two numbers. Plotted directly, with the boils/survives boundary at 1, it needs no
# comparison at all: anything left of the rule boils before it reaches its own transport ceiling.
# Nothing about the model changed -- the ceilings are the same solves, and the provenance gate below
# still checks them against the recorded JSON.
_DK = "#222222"
_NARCH = len(REACTORS) - 1          # the zero-gap stack is a reference, not one of the seven
yr = np.arange(len(REACTORS))[::-1]          # first archetype at the top
bx.axvspan(1e-3, 1.0, color=RED, alpha=0.07, zorder=0)
bx.axvline(1.0, color=_DK, lw=1.0, zorder=2)
ceilings, margins = {}, {}
for lab, elyte, kap, Tb, prov, col in SOLVENTS:
    ib = [i_boil(kap, L, Tb, U_passive(sig, hi)) for rl, L, sig, hi, iop in REACTORS]
    ceilings[lab] = ib
    margins[lab] = [v / r[4] for v, r in zip(ib, REACTORS)]
    print(f"(b) {lab:9s} margin (boil-off / transport): "
          + " ".join(f"{v:.2f}" for v in margins[lab]))

# 2026-09-12 (author: "they should be on a gray line that is horizontal and spans the lowest to
# highest relative ceiling and the colored dots sit on it"). One grey rule per architecture, from
# that row's own lowest margin to its highest, with the four solvents sitting on it at their true
# values. A row's y is the ARCHITECTURE and nothing else -- the markers were briefly dodged down
# the row and the offset read as data, which is exactly what an unlabelled position does.
for _j, _yv in enumerate(yr):
    _v = [margins[s[0]][_j] for s in SOLVENTS]
    bx.plot([min(_v), max(_v)], [_yv, _yv], "-", color="0.72", lw=1.5,
            solid_capstyle="round", zorder=2)

# Wherever the gap is centimetre-scale, MeCN and DMF land within about one per cent of each other,
# because their conductivities and boiling points trade off. On this log axis that is about two
# pixels, against a marker forty across, so on a shared rule one of them would be invisible on six
# of the eight rows. A distinct shape per solvent is what keeps both readable without moving either
# off its own value; it also survives a greyscale print, which the colour key alone does not.
_MK = {"THF": ("o", 4.8, True), "MeCN": ("s", 4.4, True), "aq. NaOH": ("D", 4.0, True),
       "DMF": ("o", 6.9, False)}
# DMF is an OPEN ring and is drawn LAST, which is the only ordering that cannot hide anything: a
# filled marker drawn on top of another simply covers it, and equal nominal sizes are not equal
# areas (a 4.4 pt square swallows a 5.2 pt triangle whole). Coincident MeCN and DMF therefore read
# as a brown ring around a blue square, which is what they are.
for lab, elyte, kap, Tb, prov, col in sorted(SOLVENTS, key=lambda _s: (_MK[_s[0]][2] is False,
                                                                      -_MK[_s[0]][1])):
    mg, (_m, _ms, _fill) = margins[lab], _MK[lab]
    _kw = (dict(color=col, mec="white", mew=0.6) if _fill
           else dict(color=col, mfc="none", mec=col, mew=1.25))
    bx.plot(mg[:_NARCH], yr[:_NARCH], _m, ls="none", ms=_ms, label=lab, zorder=4, **_kw)
    bx.plot(mg[_NARCH:], yr[_NARCH:], _m, ls="none", ms=_ms, zorder=4, **_kw)

bx.axhline(yr[_NARCH] + 0.5, color="0.75", lw=0.9, ls=(0, (3, 3)), zorder=1)
bx.text(0.72, 0.012, "boils", transform=bx.get_xaxis_transform(), fontsize=SMALL, color=RED,
        ha="right", va="bottom", zorder=6, path_effects=HALO)
bx.set_xscale("log"); bx.set_xlim(0.045, 90)
# one empty row above the topmost architecture, so the key sits over blank panel rather
# than over the unstirred markers
bx.set_ylim(-0.7, len(REACTORS) + 0.75)
# 2026-09-12 (author: "we should put each design current in the y-axis legend"). Panels (b)
# and (d) are the two that consume it -- (b) divides by it and (d) evaluates the duty at it --
# so both rows carry it. (a) and (c) are free of it and say nothing about it.
# (b) is a RATIO OF TWO CEILINGS and evaluates nothing AT a current, so its rows carry the
# architecture name alone. The transport ceiling used to be printed here too; it belongs only where
# a current is actually used, which is (d). (author, 2026-09-13)
_NAME = lambda r: r[0].replace("\n", " ")
# (d) DOES evaluate U'_required at a current, so each row names it -- on a second line, with its
# unit, so the label column does not widen into the panel.
_ROWLAB = lambda r: "%s\n%.0f mA cm$^{-2}$" % (_NAME(r), r[4])
bx.set_yticks(yr); bx.set_yticklabels([_NAME(r) for r in REACTORS], fontsize=SMALL)
# 2026-09-12 (author: "a b and cd don't share y axis anymore, so the axis labels should probably
# go on the left hand side of b and d"). They sat on the figure's outer edge from 2026-09-11, when
# (b) shared a row with (a) and long names ran back into it; with four panels each axis is its own
# and the names belong beside the axis they label. The gutter between the columns carries them.
bx.yaxis.tick_left(); bx.yaxis.set_label_position("left")
bx.tick_params(axis="y", which="minor", left=False, right=False)
from matplotlib.ticker import LogLocator as _LL
bx.xaxis.set_minor_locator(_LL(base=10, subs=tuple(np.arange(2, 10) * .1), numticks=99))
bx.set_xlabel("boil-off ceiling / transport ceiling", fontsize=AX)
# The four solvents are keyed here rather than only on (a), because (b) and (d) separate them by
# SHAPE as well as colour and a reader should not have to infer the mapping (author, 2026-09-12).
# It sits top-left, the one corner of this panel no marker reaches, and takes a white frame because
# it overlaps the shaded band -- the Figure 5 ruling, not a new position.
_solv_handles = [_L2Da([0], [0], ls="none", marker=_MK[_l][0], ms=_MK[_l][1],
                       **(dict(color=_c, mec="white", mew=0.6) if _MK[_l][2]
                          else dict(color=_c, mfc="none", mec=_c, mew=1.25)), label=_l)
                 for _l, _e, _k, _tb, _pv, _c in SOLVENTS]
_lg = bx.legend(handles=_solv_handles, loc="upper left", fontsize=ANN, ncol=2, frameon=True,
                handletextpad=0.35, columnspacing=0.9, borderpad=0.42, labelspacing=0.32,
                borderaxespad=0.5)
_lg.get_frame().set(facecolor="white", edgecolor="0.75", linewidth=0.6); _lg.set_zorder(7)

# ── (c) WHY (b)'s ORDERING CHANGES: the boil-off ceiling against the gap ─────
# 2026-09-12 (author: "we need a better way to show that, maybe panel c since it seems redundant to
# panel b?"). It WAS redundant, and measurably so: required U' against what the cell rejects
# passively is the same comparison as boil-off ceiling against transport ceiling, and across all 24
# cells the two panels never disagreed on a single verdict. The duty numbers are kept in
# results/figK_thermal.json and in the SI tables; the panel draws what (b) cannot explain about
# itself -- its own ordering.
#
# THE PHYSICS THE PANEL SHOWS. The gap enters the dissipation ONLY through the ohmic term. At a
# centimetre gap that term is 85-98 % of the heat, the ceiling goes as sqrt(kappa dT / L), and
# conductivity rules: aqueous NaOH conducts twenty times better than DMF and sits at the right of
# every thick-gap row in (b). Thin the gap and the ohmic term collapses onto the kinetic
# overpotential floor, which is the SAME for every solvent, so conductivity stops mattering and all
# that is left is the temperature rise each solvent allows before it boils, T_b - T_amb: DMF
# boils 53 K above water and takes the right-hand
# end of the two thin-gap rows. The curves cross where the two terms trade, and only the
# architectures that actually thin the gap are on the far side of it.
#
# DECLARED REFERENCE GEOMETRY: see make_figK.py. sigma = SIGMA_BEAKER, h_int = 2000 W m-2 K-1 is
# exactly the recirculating, ANEC and RDE rows; the microfluidic cell's own sigma is 7.0 and the
# stack's 0.8, so their ceilings are panel (b)'s, not this curve's. The RATIO between two solvents
# is U'-independent in both limits, which is why one reference geometry can carry the crossing.
SIG_REF, HINT_REF = SIGMA_BEAKER, 2000.0
U_REF = U_passive(SIG_REF, HINT_REF)
GAPS = np.logspace(np.log10(5e-6), np.log10(1.0e-1), 61)
sweep = {}
for lab, elyte, kap, Tb, prov, col in SOLVENTS:
    sweep[lab] = [i_boil(kap, float(g), Tb, U_REF) for g in GAPS]
    cx.plot(GAPS * 1e3, sweep[lab], "-", color=col, lw=1.7, zorder=3, solid_capstyle="round")

# the gaps the model actually carries: five archetypes share one, and only two sit thin
# each name runs ALONG its own rule, on the side of it the curves leave clear: the thin-gap rule
# is crossed high, the centimetre rule low, so one label hangs low and the other high
# "five archetypes" said nothing about WHICH (author, 2026-09-12), so each rule is named by the
# cells that sit on it: the 2 cm rule carries both batch cells, both flow cells and the rotating
# disc, and the rotating cylinder's 2.44 cm is the same place at this scale.
for _g, _t, _yf, _va in ((GAP_MICRO, "microfluidic", 0.035, "bottom"),
                         (GAP_BEAKER, "batch, flow, RDE", 0.965, "top")):
    cx.axvline(_g * 1e3, color="0.55", lw=0.9, ls=(0, (2, 2)), zorder=1)
    cx.text(_g * 1e3, _yf, _t, transform=cx.get_xaxis_transform(), fontsize=SMALL, color="0.35",
            ha="center", va=_va, rotation=90, zorder=6, path_effects=HALO)
cx.set_xscale("log"); cx.set_yscale("log")
cx.set_xlim(GAPS[0] * 1e3, GAPS[-1] * 1e3)
_allv = [v for _l in sweep for v in sweep[_l]]
cx.set_ylim(10 ** (np.log10(min(_allv)) - 0.12), 10 ** (np.log10(max(_allv)) + 0.30))
# The solvent is named on its own curve (author, 2026-09-12), at the thin-gap end, which is the
# only place all four are separated: there the ranking is by T_b - T_amb and the four are
# 805 / 1204 / 1588 / 2241 mA cm-2 apart, whereas at a centimetre gap MeCN and DMF coincide. The
# two regime words the panel used to carry are in the caption instead -- the figure does not need
# to explain itself in prose when the caption can.
# MeCN and DMF are only separated at the THIN end (1204 against 2241) and THF and aq. NaOH only
# at the THICK end (14 against 141, with the other two between them), so each pair is named where
# it is legible and the two of each pair take opposite sides of their own curve.
_CNAME_AT = {"DMF": (0.017, +1), "MeCN": (0.017, -1), "aq. NaOH": (3.0, +1), "THF": (3.0, -1)}
for lab, elyte, kap, Tb, prov, col in SOLVENTS:
    _x_at, _sd = _CNAME_AT[lab]
    _along_curve(cx, list(GAPS * 1e3), sweep[lab], lab, col, _x_at, side=_sd, gap_pt=6.5)
cx.set_ylabel("boil-off ceiling (mA cm$^{-2}$)", fontsize=AX)
cx.set_xlabel("interelectrode gap (mm)", fontsize=AX)

# ── (d) WHAT THE HEAT THEN DEMANDS: cooling duty at the transport ceiling ────
# 2026-09-12 (author: "let's add the cooling info as a panel d"). This is the ACTIONABLE half of
# the panel that was retired an hour earlier: its boil-or-survive bit duplicated (b) exactly, on
# all 24 cells, but the CLASS of cooling a failing cell would need is carried nowhere else in the
# figure. Rows are the six architectures that intensify transport; the two beakers are left out
# because the question this panel asks is what intensification costs to cool.
INT = REACTORS[2:]
yd = np.arange(len(INT))[::-1]
_BAND_NAME = {"natural convection\n(passive)": "natural\nconvection", "forced air": "forced\nair",
              "liquid cold plate\n(PEM-class)": "liquid\ncold plate"}
for nm, lo, hi, cshade in COOLING_BANDS:
    dx.axvspan(lo, hi, color=cshade, alpha=0.55, zorder=0)
    dx.text(np.sqrt(lo * hi), 0.985, _BAND_NAME.get(nm, nm.replace("\n", " ")),
            transform=dx.get_xaxis_transform(), fontsize=SMALL, color="0.35", ha="center",
            va="top", zorder=3, linespacing=1.2, path_effects=HALO)
req = {}
for lab, elyte, kap, Tb, prov, col in sorted(SOLVENTS, key=lambda _s: (_MK[_s[0]][2] is False,
                                                                      -_MK[_s[0]][1])):
    req[lab] = [U_required(iop, kap, L, Tb) for rl, L, sig, hi, iop in INT]
    _m, _ms, _fill = _MK[lab]
    _kw = (dict(color=col, mec="white", mew=0.6) if _fill
           else dict(color=col, mfc="none", mec=col, mew=1.25))
    dx.plot(req[lab], yd, _m, ls="none", ms=_ms, zorder=4, **_kw)
# what each architecture's own cell actually rejects, as a caret on its row: a solvent marker to
# the LEFT of it runs passively, one to the right needs the class its band names
avail = [U_passive(sig, hi) for rl, L, sig, hi, iop in INT]
for _y0, _a0 in zip(yd, avail):
    dx.plot([_a0, _a0], [_y0 - 0.30, _y0 + 0.30], color=_DK, lw=1.7, zorder=5, solid_capstyle="butt")
_avail_handle = _L2Da([0], [0], color=_DK, lw=1.7, label="this cell, passive")
dx.set_xscale("log")
_allr = [v for _l in req for v in req[_l]] + avail
# the right edge reaches the TOP of the highest cooling band, so no band is cut off under
# its own name; the left edge clears the smallest duty
dx.set_xlim(10 ** (np.log10(min(_allr)) - 0.30),
            max(COOLING_BANDS[-1][2] * 1.25, 10 ** (np.log10(max(_allr)) + 0.45)))
# headroom for the band names along the top, and a blank row at the foot for the key, the same
# reason (b) carries one: a legend laid over the rows hides the markers it exists to explain
dx.set_ylim(-1.85, len(INT) + 0.30)
dx.set_yticks(yd); dx.set_yticklabels([_ROWLAB(r) for r in INT], fontsize=SMALL)
dx.yaxis.tick_left(); dx.yaxis.set_label_position("left")
dx.tick_params(axis="y", which="minor", left=False, right=False)
dx.xaxis.set_minor_locator(_LL(base=10, subs=tuple(np.arange(2, 10) * .1), numticks=99))
dx.set_xlabel("$U'$ needed to stay below boiling\n(W cm$^{-2}$ K$^{-1}$)", fontsize=AX)
# (d) carries the solvents too rather than sending the reader back to (b) (author, 2026-09-12)
_lgd = dx.legend(handles=_solv_handles + [_avail_handle], loc="lower left", fontsize=ANN, ncol=3,
                 frameon=True, handletextpad=0.35, columnspacing=0.9, borderpad=0.42,
                 labelspacing=0.3, borderaxespad=0.4)
_lgd.get_frame().set(facecolor="white", edgecolor="0.75", linewidth=0.6); _lgd.set_zorder(7)
print("(d) cooling duty at the transport ceiling, %d architectures" % len(INT))
for lab, elyte, kap, Tb, prov, col in SOLVENTS:
    print("  %-9s " % lab + " ".join("%7.4f" % v for v in req[lab]))
print("  %-9s " % "passive" + " ".join("%7.4f" % v for v in avail))

# the right margin is reserved explicitly: (b) AND (d) both put their architecture names
# outside the axes on the figure edge, and the longest is "rotating cyl. 3000 rpm"
# no tight_layout: the gridspec above is already the final geometry. Every letter sits at the same
# offset: they ride ABOVE the axes, where the row names never reach (the topmost sits at 0.82 of
# the height), so a letter pushed out into the gutter only reads as belonging to the panel to its
# left (author, 2026-09-12: "letters for panel b and d are too far left").
for ax, ltr in ((a, "a)"), (bx, "b)"), (cx, "c)"), (dx, "d)")):
    FS.panel_letter(ax, ltr, x=-0.15, y=1.03)

# ── PROVENANCE GATE: what we are about to draw must equal the recorded JSON ──
J = json.load(open(os.path.join(SEC4, "results", "figK_thermal.json")))
tol = 1e-9


def close(x, y):
    return abs(x - y) <= tol*max(1.0, abs(y))


for lab, elyte, kap, Tb, prov, col in SOLVENTS:
    assert close(i_boil(kap, Lb, Tb, Ub), J["panelA"][lab]["i_boil"]), f"panelA {lab}"
    for (rl, L, sig, hi, iop), v in zip(REACTORS, ceilings[lab]):
        assert close(v, J["panelB"][lab][rl.replace("\n", " ")]), f"panelB {lab} {rl}"
    assert "panelC_gapsweep" in J, "results/figK_thermal.json predates the gap sweep -- run make_figK.py first"
    _S = J["panelC_gapsweep"]
    assert close(U_REF, _S["U_passive_ref"]), "panelC reference geometry"
    for _g, _v in zip(GAPS, sweep[lab]):
        assert close(_v, _S["i_boil"][lab][list(GAPS).index(_g)]), f"panelC sweep {lab} {_g}"
    for _g, _gj in zip(GAPS, _S["gap_m"]):
        assert close(float(_g), _gj), "panelC sweep grid"
    for (rl, L, sig, hi, iop), v in zip(INT, req[lab]):
        assert close(v, J["panelC"][lab][rl.replace("\n", " ")]), f"panelD {lab} {rl}"
for (rl, L, sig, hi, iop), v in zip(INT, avail):
    assert close(v, J["panelC"]["passively_available"][rl.replace("\n", " ")]), f"panelD avail {rl}"
assert close(Ub, J["reactors"][0]["U_passive"])
print("provenance gate PASSED: every plotted value equals results/figK_thermal.json")

os.makedirs(OUTDIR, exist_ok=True)
stem = os.path.join(OUTDIR, "MS_Fig5_figK_boiloff_remediated")
DPI = 600
fig.savefig(stem + ".svg")
fig.savefig(stem + ".png", dpi=DPI)
print("wrote -> " + stem + ".{svg,png}")
w, h = fig.get_size_inches()
print("figure %.2f x %.2f in @%d dpi = %d x %d px" % (w, h, DPI, round(w*DPI), round(h*DPI)))
