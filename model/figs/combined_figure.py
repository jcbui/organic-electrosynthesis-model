# -*- coding: utf-8 -*-
"""Main-text Figure X — carrier mass-transport ceilings + EC' reaction-diffusion regimes.
3 cols x 2 rows, gengrid house style.

  a) carrier schematic          b) molecular-catalyst depletion   c) intensification map
  d) EC' thick film             e) EC' kinetic (Saveant)          f) EC' thin film

GROUNDING REWRITE, 2026-08-02 (ms-figX-ungrounded).
=====================================================================================
The previous version of this file (preserved as combined_figure.py.bak_preGrounding,
its render at _archive/figX_preGrounding/) read NO data. Every curve was a closed form
typed into the script and every number on the figure was hardcoded. That violated the
project standard that a figure number must be MEASURED, DERIVED or a declared
ASSUMPTION-with-bound. This version reads the solver artifacts. What each panel now
traces to is listed in _replacement_artwork/REPLACEMENT_NOTE_FigX.md.

Specific fabrications removed (before -> after):
  * panel b  "thin gap, d=10 um, i_lim = 12 mA/cm2" and "stirred, d=100 um, i_lim = 1.2".
             Those came from n_c = 2, D = 6e-6 cm2/s, C_cat = 10 mM, none of which has a
             row in data/parameters_provenance.csv. They are replaced by the catalyst
             rows' own archetype medians: RCE d = 9.4 um / 5.39 mA cm-2 and stirred
             d = 100.0 um / 0.50 mA cm-2 (julia/tier0_ec_matrix.csv).
  * panel b  "the dilute carrier (3-30 mM) caps it below 25 mA cm-2" was FALSE as
             printed: the model's own matrix reaches 52.6 mA cm-2 for the 30 mM Ni
             aryl-aryl homocoupling at the RCE. Replaced by the count the model
             supports: 10 of the 11 catalyst systems stay under 25 in every architecture.
  * panel c  the direct band (600-15000, line 3000) and catalyst band (30-300, line 120)
             were invented nFDC constants. They are now the p10-p90 and median of
             K = 0.1 n F D C over the 31 substrate and 11 catalyst rows, at runtime.
  * panel c  the mediated curve was a hand-built "total catalysis -> 25 mA/cm2 plateau ->
             shuttle" composite with an invented plateau height of exactly 25. The
             plateau was drawn flat for every mediator; in the actual EC' solve only
             2 of the 8 mediated systems are delta-insensitive and the other 6 run at
             log-log slope -0.59 to -1.00. All 8 solves are now plotted as solved.
  * panel c  the vertical guide labelled "RDE/RCE" at delta = 13 um is neither archetype.
             All six archetypes now appear at their computed median delta.
  * panels d,e,f were freehand: clip(1 - x/7), exp(-x/6), 1 - x/2, with x_f = 7 um and
             x_k = 6 um chosen for looks and Med_red drawn as exactly 1 - Med_ox. They
             are now the solved Med_red / Med_ox / substrate profiles at 0.9 i_lim from
             julia/npp_ecprime_regimes.csv, one k per regime, with the solved c_red
             plotted as solved (c_red + c_ox is 0.96-0.98, not 1).

ANNOTATION PASS, 2026-08-02 (ms-figX-annotations). Closing the last provenance gap.
=====================================================================================
The grounding pass above left panels d-f resting on two constants that appear in NO
other document: D_med = 6.0e-10 and D_S = 1.0e-9 m^2/s (note: m^2/s, not cm^2/s — the
value in cm^2/s would be 6e-6 and 1e-5). They are the verbatim run_ecprime.jl base case,
they have no row in the 268-row data/parameters_provenance.csv, and SI S5.4 declares only
C_med, C_S and delta. So I_SUBCAP = 48.24 could not be reproduced from the SI.

Two options were on the table: declare the constants, or delete the two ratio annotations
that quote them. DELETION WAS REJECTED, because it does not close the gap. The same two D
also set the three i_lim printed on d-f, the three x_k = sqrt(D_med/kC_S) printed on d-f,
and (through delta/x_k and gamma) which regime each panel's k actually falls in. Dropping
two annotations would remove 2 of 8 exposed numbers and leave the other 6 standing.

Fix, in the layer this script controls: the base case is now DECLARED ON THE FIGURE, in
full, under panels d-f — so d-f are reproducible from the printed page whether or not the
matching SI/registry rows ever land. The SI-side additions are specified as a REQUIRED SI
ADDITION block in _replacement_artwork/REPLACEMENT_NOTE_FigX.md for the make_si.js owner.

Also fixed here: all three EC' solves carry limiter == "newton-wall (no collapse)", which
SI S5.5 defines as a STRICT LOWER BOUND on i_lim and which SI Table S6 already prints with
a ">=" prefix. Panels d-f were printing those values as equalities. They now carry ">=",
read from the artifact's own limiter column (see ge()), never hardcoded.

Panel a is a SCHEMATIC and is now labelled as one ON THE FIGURE. It has no numeric axes,
carries only the three scaling laws (closed forms, SI Eqs. S11/S13/S15), and asserts no
magnitude. That is a legitimate schematic; the label makes the status non-negotiable
rather than something a reader has to infer from the caption.

Run:  python3 combined_figure.py
Reads (all relative to ../Section4_Model):
    julia/reactions_table.jl        via figs/model_medians.py
    julia/tier0_ec_matrix.csv       via figs/model_medians.py
    julia/tier0_matrix.csv          via figs/model_medians.py (import-time self-check)
    julia/mediated_ec_matrix.csv    via figs/model_medians.py
    julia/mediated_ec_profiles.csv  directly  (julia/run_mediated_profiles.jl; since v90 -- the base-case
                                    julia/npp_ecprime_regimes.csv these panels drew until v89 is archived)
Writes: _replacement_artwork/combined_figure_grounded.{png,svg}
    NOT combined_figure.png — the currently embedded artwork is left untouched so the
    swap into the manuscript is an explicit, reviewable act.

REDESIGN, 2026-09-07 (author instruction: the captions carry the text). Titles, the annotation
paragraphs, the segment labels, the archetype guides, the legend footnote and the provenance footer
are gone from the drawing. Panel (a) is redrawn in the group's flat schematic style
(figs/figstyle.py); its state-S status is still declared ON the figure by a one-word tag, as the
provenance standard requires. Every number that used to be printed on the figure is still computed,
printed to stdout, and stated in the caption / SI Table S7d; the envelope-vs-solver gate is intact.
"""
import os
import string
import sys

import numpy as np
import pandas as pd
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.ticker import LogLocator
from matplotlib.lines import Line2D

# ── locate the model repo; every number on this figure comes from there ───────────
# Moved 2026-08-02 from "MS Drafts/" into Section4_Model/figs/, so that every figure
# generator for this manuscript lives in one place. HERE is now figs/ itself, so SEC4 is
# its parent -- not parent + "Section4_Model" as it was when this file sat outside the repo.
HERE = os.path.dirname(os.path.abspath(__file__))          # .../Section4_Model/figs
SEC4 = os.path.dirname(HERE)                               # .../Section4_Model
if not os.path.isdir(SEC4):
    raise SystemExit(f"Section4_Model not found next to this script (looked in {SEC4})")
sys.path.insert(0, HERE)
import model_medians as MM  # noqa: E402  (import-time self_check reproduces tier0_matrix.csv)

OUT = HERE                                                 # renders sit beside the script
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"mathtext.default": "regular"})
try:
    import mpl_fontkit as fontkit

    fontkit.install("Lato")
    FONT = "Lato"
except Exception as e:  # pragma: no cover
    FONT = "DejaVu Sans"
    print("Lato unavailable ->", FONT, "|", e)
mpl.rcParams.update({"text.usetex": False, "svg.fonttype": "none",
                     "font.family": "sans-serif", "font.sans-serif": FONT})
mpl.rcParams["axes.linewidth"] = 1

# categorical hues carry CARRIER IDENTITY and nothing else; fixed order, never cycled.
# validated: adjacent-pair CVD dE 13.8 (deutan) / 12.0 (tritan), normal 15.5, all >= 3:1
# contrast on white.
BLUE = "#2166AC"      # direct / substrate-carried
ORANGE = "#C1611E"    # mediated (EC')
ORANGE_LT = "#E3A46B" # mediated, resting form (same hue, lighter step)
ORANGE_ACT_C = "#EAB682"   # the active form in d-f, the schematic's own light shade (2026-09-10)
RED = "#A31F34"       # dilute molecular catalyst
RED_LT = "#C4707E"    # same hue, lighter step — used for the SLOWER reactor in panel b
DK = "#222222"
GRY = "#666666"
EL = "#585858"


def gengrid(n_cols=1, n_rows=1, dpi_fig=600, fig_size=(8, 6), genlabels=True,
            size_inches=(3.25, 2.5), ticklabel_size=8, label_pos=-0.15, bold=False,
            minor=True):
    fig, axs = plt.subplots(ncols=n_cols, nrows=n_rows, dpi=dpi_fig, figsize=fig_size)
    fig.set_size_inches(*size_inches)
    bv = "bold" if bold else "regular"

    def cfg(ax):
        ax.tick_params(axis="x", which="both", direction="in", top=True, labelsize=ticklabel_size)
        ax.tick_params(axis="y", which="both", direction="in", right=True, labelsize=ticklabel_size)
        if minor:
            ax.minorticks_on()
            ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
            ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
        for t in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            t.label1.set_fontsize(ticklabel_size)
            t.label1.set_fontweight(bv)
        [s.set_linewidth(1.25) for s in ax.spines.values()]

    for row in axs:
        for ax in row:
            cfg(ax)
    if genlabels:
        labels = np.reshape(list(string.ascii_lowercase)[0:axs.size], axs.shape)
        for i in range(axs.shape[0]):
            for j in range(axs.shape[1]):
                axs[i][j].text(label_pos, 1.12, labels[i][j] + ")", transform=axs[i][j].transAxes,
                               fontsize=10, fontweight=bv, va="top", ha="right")
    return fig, axs


def gengrid_fig6(size_inches=(6.5, 7.52), ticklabel_size=7.0, bold=True,
                 height_ratios=(2.60, 0.57, 1.85, 1.95)):
    """Figure 6's layout, rebuilt 2026-09-08 (author: panel (a) is "really poorly sized").

    The old call was gengrid(3, 2) -- a uniform 3x2. That gave the equal-aspect carrier
    schematic a near-square slot it filled about a third of, and gave the near-empty catalyst
    panel exactly as much area as the 50-row intensification map. The rows are unequal now:

        row 0   (a) (b) (c)              the three labelled boundary-layer cells (one strip axes)
        row 1   (d) (e) (f)              the three EC-prime regimes, profiles at the limiting current
        row 2   (g) (h)                  intensification: i_lim against delta for the three regime
                                         mediators (g) and for three catalyst rows at their sourced
                                         rate constant, with their k = 0 floors (h)  [2026-09-11]

    Panel letters are placed in FIGURE coordinates once the layout is solved, so a letter sits
    the same distance from its own axes whatever that axes is worth: gengrid's axes-FRACTION
    offset (-0.22) puts the letter of a 6 in wide panel more than an inch off the page.
    """
    fig = plt.figure(dpi=600, figsize=size_inches)
    fig.set_size_inches(*size_inches)
    nrow = len(height_ratios)                 # 3 when the scheme strip is dropped (FIG6_INLINE)
    gs = fig.add_gridspec(nrow, 6, height_ratios=list(height_ratios))
    axA = fig.add_subplot(gs[0, :])
    # row 1 is a thin strip of three axes carrying the reaction each EC-prime panel below solves
    # (Jonas Rein, comment 1106: "this is a paper that we also want chemists to read, it might be
    # helpful to show the reaction that was being done"). They are drawing surfaces only, no axes.
    if nrow == 4:
        axSD = fig.add_subplot(gs[1, 0:2]); axSE = fig.add_subplot(gs[1, 2:4]); axSF = fig.add_subplot(gs[1, 4:6])
    else:
        axSD = axSE = axSF = None             # the schemes move inside (g) and (h) instead
    # the intensification map (the former panel b) is still COMPUTED and its envelope-vs-solver gate
    # still runs, but it is not drawn (author's design 2026-09-10/11: a-c cells, d-f regime profiles,
    # g-h intensification); it lives on a throwaway figure
    axC = plt.figure(dpi=100).add_subplot(111)
    _r1, _r2 = (2, 3) if nrow == 4 else (1, 2)
    axD = fig.add_subplot(gs[_r1, 0:2]); axE = fig.add_subplot(gs[_r1, 2:4]); axF = fig.add_subplot(gs[_r1, 4:6])
    axG = fig.add_subplot(gs[_r2, 0:3]); axH = fig.add_subplot(gs[_r2, 3:6])
    bv = "bold" if bold else "regular"
    for ax in (axC, axD, axE, axF, axG, axH):
        ax.tick_params(axis="x", which="both", direction="in", top=True, labelsize=ticklabel_size)
        ax.tick_params(axis="y", which="both", direction="in", right=True, labelsize=ticklabel_size)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
        ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
        for t in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            t.label1.set_fontsize(ticklabel_size)
            t.label1.set_fontweight(bv)
        [sp.set_linewidth(1.25) for sp in ax.spines.values()]
    for ax in (axSD, axSE, axSF):
        if ax is not None:
            ax.set_axis_off()
    return fig, (axA, axC, axD, axE, axF, axG, axH, axSD, axSE, axSF), bv


def fit_equal_aspect(fig, ax, yspan):
    """With aspect="equal" the DATA-span ratio must equal the AXES-BOX ratio, or matplotlib
    shrinks the box to suit the data and the drawing pillarboxes inside its slot. That is
    precisely what was wrong with the old panel (a). Take the slot the gridspec actually gave
    (original=True, i.e. before any aspect shrink) and set the x span to match it, keeping the
    drawing centred. Then the box needs no shrinking and the panel fills its row."""
    W, H = fig.get_size_inches()
    bb = ax.get_position(original=True)
    xspan = yspan * (bb.width * W) / (bb.height * H)
    x0, x1 = ax.get_xlim(); c = 0.5 * (x0 + x1)
    ax.set_xlim(c - xspan / 2, c + xspan / 2)
    return xspan


def place_letters(fig, axes, bv, dx_in=0.34, dy_in=0.04, size=10, letters="abcdef"):
    for ax, s in zip(axes, letters):
        bb = ax.get_position(original=True)
        W, H = fig.get_size_inches()
        fig.text(bb.x0 - dx_in / W, bb.y1 + dy_in / H, s + ")", fontsize=size,
                 fontweight=bv, va="bottom", ha="left")


# ═════════════════════ everything quantitative, resolved up front ═════════════════
# so that no magic number appears below and every one is printed to stdout on each run.

K_SUB = MM.K_stats("substrate")            # p10 / median / p90 of 0.1 n F D C  [mA cm^-2 um]
K_CAT = MM.K_stats("catalyst")
C_SUB = MM.guide_constant("substrate")     # median i_lim(stirred) * 100 um  = 2299.0

D_CAT_ST = MM.delta_median("stirred", "catalyst")   # 200.00 um  (fixed archetype, measured)
D_CAT_RCE = MM.delta_median("rce", "catalyst")      #   9.38 um  (Eisenberg, per-row D)
I_CAT_ST = MM.ilim_median("stirred", "catalyst")    #   0.50 mA cm^-2
I_CAT_RCE = MM.ilim_median("rce", "catalyst")       #   5.39 mA cm^-2

# catalyst-carrier cap, from the production matrix the SI quotes (not a recomputation)
_TC = MM.TIER0_EC[MM.TIER0_EC.carrier == "catalyst"]
_IMAX = _TC[MM.ARCHETYPES].max(axis=1)
N_CAT = len(_TC)
N_UNDER25 = int((_IMAX < 25).sum())
I_CAT_MAX = float(_IMAX.max())
_jmax = int(np.argmax(_IMAX.values))
NAME_CAT_MAX = str(_TC.reaction.iloc[_jmax])
C_CAT_MAX = float(MM.pop("catalyst").C.iloc[_jmax])   # mol m^-3 == mM

MED = MM.mediated_delta_slopes()                       # 8 systems, EC' solver output
# the raw matrix, for the analytic envelope of panel c: it carries the three limiting
# currents (i_tier0, i_saveant, i_subcap) per (reaction, reactor) alongside the solve
MEDM = pd.read_csv(os.path.join(SEC4, "julia", "mediated_ec_matrix.csv"))
FLAT = {k: v for k, v in MED.items() if v["slope"] > -0.5}
STEEP = {k: v for k, v in MED.items() if v["slope"] <= -0.5}
_FS = sorted(v["slope"] for v in FLAT.values())
_SS = sorted(v["slope"] for v in STEEP.values())
N_DROP = len(MM.MEDIATED) - sum(v["n"] for v in MED.values())

# EC' regime profiles -- the three mediated rows of panel (g), one per regime, at their CITED rate constants on the ANEC
# film (36.2 um, measured -- Watkins 2023, SI Table S1 -- the archetype cell every row's ANEC entry of Table S5 uses), the
# profiles AT the c-control plateau, i.e. at i_lim itself, from julia/run_mediated_profiles.jl (2026-09-11, author: "maybe we
# should show these profiles then for d-f bc they're really applicable?"). Until v89 these panels drew a DECLARED base case
# (20 mM mediator / 0.5 M substrate / 100 um at k = 1e5, 1e2, 1e-2); it is archived (_archive/fig6_basecase_regimes_20260911/)
# and the SI's own base case (S5.4, Fig. H) is untouched. The regime of each row is NAMED FROM THE SOLVE, in the solver's own
# artifact: substrate-limited when the substrate is exhausted at the wall, mediator-limited when most of the activated mediator
# leaves the film unreacted (the share consumed inside the film below one half), kinetic otherwise; G-ECPANEL
# (data/ecprime_panel_sensitivity.py) requires that label to agree with the analytic assignment and to survive the +/-25 %
# re-solves on both diffusivities. What the panel prints IS the published cell: the drawn solve is run_mediated.jl's own mesh.
REG = pd.read_csv(os.path.join(SEC4, "julia", "mediated_ec_profiles.csv"))
F_CONST = 96485.332
PANEL_ROWS = ["Hofmann", "ACT", "NHPI"]                 # (d) substrate-limited, (e) kinetic, (f) mediator-limited: k descending
PANEL_REGIME = {"Hofmann": "substrate-limited", "ACT": "kinetic", "NHPI": "mediator-limited"}
REGIME_LABEL = {"substrate-limited": "substrate-limited:  $x_k \\ll \\delta$",
                "kinetic": "kinetic:  $x_k < \\delta$",
                "mediator-limited": "mediator-limited (shuttle):  $x_k > \\delta$"}
ROW_TITLE = {"Hofmann": "Br$^{-}$/Hofmann, k = 10$^{3}$", "ACT": "ACT, k = 20", "NHPI": "NHPI, k = 0.5"}
SPECIES_LABEL = {"Hofmann": ("Br$_2$", "Br$^{-}$"), "ACT": ("ACT$^{+}$", "ACT"), "NHPI": ("PINO", "NHPI")}   # (activated, resting)


def reg(short):
    g = REG[REG["short"] == short]
    if g.empty:
        raise SystemExit(f"row {short!r} missing from mediated_ec_profiles.csv -- run julia/run_mediated_profiles.jl")
    return g


def ge(short):
    """'>=' iff the solver stopped on a Newton wall -- read from the artifact's own limiter column, never hardcoded."""
    return "$\\geq$" if str(reg(short).limiter.iloc[0]).startswith("newton-wall") else "="


print("── numbers on the figure, all resolved from artifacts ─────────────────────")
print(f"  K substrate  p10 {K_SUB['lo']:.1f}  median {K_SUB['median']:.1f}  p90 {K_SUB['hi']:.1f}  (n={K_SUB['n']})")
print(f"  K catalyst   p10 {K_CAT['lo']:.1f}  median {K_CAT['median']:.1f}  p90 {K_CAT['hi']:.1f}  (n={K_CAT['n']})")
print(f"  catalyst stirred  d {D_CAT_ST:.2f} um  i {I_CAT_ST:.3f} mA/cm2")
print(f"  catalyst RCE      d {D_CAT_RCE:.2f} um  i {I_CAT_RCE:.3f} mA/cm2  ->  "
      f"{D_CAT_ST/D_CAT_RCE:.1f}x thinner, {I_CAT_RCE/I_CAT_ST:.1f}x i_lim")
print(f"  catalyst cap: {N_UNDER25}/{N_CAT} under 25 in every archetype; max {I_CAT_MAX:.1f} "
      f"({NAME_CAT_MAX}, {C_CAT_MAX:.0f} mM)")
print(f"  mediated: {len(FLAT)} of {len(MED)} delta-insensitive (slope {_FS[0]:+.2f}..{_FS[-1]:+.2f}); "
      f"other {len(STEEP)} run {_SS[0]:+.2f}..{_SS[-1]:+.2f}; {N_DROP}/{len(MM.MEDIATED)} rows dropped (solver wall flag)")
for _s in PANEL_ROWS:
    _g = reg(_s).iloc[0]
    print(f"  EC' (d-f) {_s:8s} k={_g.k_M:<6g} delta {_g.delta_um:.1f} um  x_k {_g.xk_um:8.3f} um  gamma x_k {_g.gamma_xk_um:8.1f} um  "
          f"i_lim {_g.ilim_mAcm2:8.3f} mA/cm2 (= {_g.ilim_mAcm2/_g.i_subcap_mAcm2:.2f} x substrate cap, {_g.ilim_mAcm2/_g.i_tier0_mAcm2:.2f} x commuting bound; "
          f"fine-mesh check {_g.ilim_fine_mAcm2:.3f})  share in film {_g.share_in_film:.3f}  c_S(0) {_g.c_S_surf_norm:.2e}  "
          f"-> {_g.regime_solved} (analytic: {_g.regime_analytic})  limiter '{_g.limiter}'")
    if str(_g.regime_solved) != PANEL_REGIME[_s]:
        raise SystemExit(f"Fig. 6 panel for {_s}: the solve names the regime {_g.regime_solved!r}, the panel design expects "
                         f"{PANEL_REGIME[_s]!r} -- re-read the panels and the caption before rendering")
print("───────────────────────────────────────────────────────────────────────────")


import figstyle as FS

# 2026-09-08 quality pass: this figure was drawn at 8.0 in and PLACED at 6.5 in, so every font on
# it reached the page 19% smaller than set -- the 6.2 pt axis labels landed at 5.0 pt and the 4.9 pt
# legend at 4.0 pt, under the 6.5 pt floor. It is drawn at the printed width now and the type scale
# matches the other Section 4 figures (TICK 7.0 / ANN 7.0 / AX 8.0).
TICK, ANN, AX = 7.0, 7.0, 8.0
# FIG6_INLINE (author, 2026-10-02: "too much whitespace now that you've added the chemistry, but you also
# didn't add the chemistry for the molecular catalysts, can we maybe put little rxns on the plots panel gh
# above each respective line?").  Drops the dedicated scheme strip -- measured at 0.475 in of dead band above
# 0.17-0.31 in of ink -- and draws six compact schemes INSIDE (g) and (h), one above each curve, so the three
# catalyst rows get the chemistry the mediated rows already had.  Suffixed output: the shipped render is never
# touched by the variant (the FIG6_GH_NORM rule).
_INLINE = os.environ.get("FIG6_INLINE", "") not in ("", "0")
# the strip's height is GIVEN TO (g) and (h) rather than taken off the figure: at the old row height
# (1.54 in) panel (g) measured room for only two of its three schemes, which is the whole reason the
# first inline render refused to place the NHPI one.
_RATIOS = (2.60, 1.85, 2.95) if _INLINE else (2.60, 0.57, 1.85, 1.95)
fig, (axA, axC, axD, axE, axF, axG, axH, axSD, axSE, axSF), BV = gengrid_fig6(ticklabel_size=TICK, bold=True, height_ratios=_RATIOS,
                                                                       size_inches=(6.5, 7.52))

# ════════════════ a) carrier schematic — DECLARED SCHEMATIC, no data ══════════════
# panel (a) is DRAWN IN THE TAIL, once tight_layout has fixed the box it must fill.

# (the former panel (b), the two-line catalyst depletion profile, was dropped on 2026-09-09; its
# numbers are still computed and printed above so the stdout record is unchanged)

# ════════════════ b) intensification map — one line and one band per carrier class ═════════
# 2026-09-10, author's design ("medians with a band around them ... combine all the molecular
# catalyst into one band ... extra wide"), with one rule for all three classes:
#   solid line = the value the matrix PUBLISHES for the class (cited k for a mediator, k = 0 for a
#                catalyst, the transport bound for a direct substrate), as the class median;
#   band       = the declared uncertainty around it, combined with the middle half of the class.
# Every class is summarised the same way: each row's own trace across the seven archetype films is
# interpolated (log-log) onto one film grid and the median and quartiles are taken across rows at
# every grid point. Summarising per archetype at one median film had produced a kink in the thin
# films (the RDE and rotating-cylinder films depend on each row's D while the microfluidic film is
# 12.5 um for all, so the archetype order differs row to row); this construction cannot. A band
# ends where fewer than nine in ten of its rows still cover the grid.
D_LO, D_HI = MM.delta_median("natural"), MM.delta_median("rce")          # the archetype span
dd = np.logspace(np.log10(D_LO), np.log10(D_HI), 240)
Q_LO, Q_HI = 25, 75                                                       # the middle half


def quantile_traces(df, xcol, ycol, key, grid, lo=Q_LO, hi=Q_HI, min_cover=0.90):
    """Median / quartiles across rows of `key`, each row's (xcol, ycol) trace interpolated in log-log."""
    curves = []
    for _, g in df.groupby(key):
        g = g.sort_values(xcol)
        x = np.log(g[xcol].values); y = np.log(g[ycol].values)
        # a grid point within 0.5 % of a trace's own endpoint counts as covered (three mediators end at
        # exactly the 12.5 um microfluidic film, and the nearest grid point sits a hair below it)
        gx = np.clip(np.log(grid), x[0] - np.log(1.005), x[-1] + np.log(1.005))
        inside = (np.log(grid) >= x[0] - np.log(1.005)) & (np.log(grid) <= x[-1] + np.log(1.005))
        yi = np.where(inside, np.interp(np.clip(gx, x[0], x[-1]), x, y), np.nan)
        curves.append(np.exp(yi))
    C = np.array(curves); ok = np.isfinite(C).mean(axis=0) >= min_cover
    q = dict(lo=np.nanpercentile(C, lo, axis=0), med=np.nanmedian(C, axis=0), hi=np.nanpercentile(C, hi, axis=0), n=len(curves))
    return {k: (np.where(ok, v, np.nan) if isinstance(v, np.ndarray) else v) for k, v in q.items()}


def class_traces(carrier):
    """The published matrix rows of one carrier class, long form: one (delta, i_lim) per archetype."""
    p = MM.pop(carrier); rows = []
    for k in MM.ARCHETYPES:
        for i, r in p.iterrows():
            rows.append(dict(row=i, delta_um=r["d_" + k], i_mAcm2=r["i_" + k]))
    return pd.DataFrame(rows)


# direct substrate: the transport bound of every row, class median and middle half
Q_SUB = quantile_traces(class_traces("substrate"), "delta_um", "i_mAcm2", "row", dd)
axC.fill_between(dd, Q_SUB["lo"], Q_SUB["hi"], color=BLUE, alpha=0.18, lw=0, zorder=2)
axC.plot(dd, Q_SUB["med"], color=BLUE, lw=2.2, zorder=6)
# mediated EC': the solved cells at the cited rate constants (all 56), median and middle half; if the
# rate-constant sweep has written its per-cell values, the band is widened to the tenfold change of
# each k either way (results/rate_constant_cells.csv, G-KSENS), so that the mediated band means the
# same thing as the catalyst band: population plus declared kinetic uncertainty.
Q_MED = quantile_traces(MEDM[MEDM.flag == "ok"], "delta_um", "i_ec_mAcm2", "reaction", dd)
_cells = os.path.join(SEC4, "results", "rate_constant_cells.csv")
MED_KBAND = os.path.exists(_cells)
if MED_KBAND:
    _kc = pd.read_csv(_cells)
    _lo, _hi = [], []
    for _f in ("div10", "base", "mul10"):
        _q = quantile_traces(_kc[_kc.factor == _f], "delta_um", "i_ec_mAcm2", "reaction", dd)
        _lo.append(_q["lo"]); _hi.append(_q["hi"])
    MED_LO, MED_HI = np.nanmin(np.array(_lo), axis=0), np.nanmax(np.array(_hi), axis=0)
    print(f"  mediated band: middle half widened by the tenfold k sweep ({_kc.factor.nunique()} levels, {len(_kc)} cells)")
else:
    MED_LO, MED_HI = Q_MED["lo"], Q_MED["hi"]
    print("  mediated band: middle half at the cited k only (results/rate_constant_cells.csv absent)")
axC.fill_between(dd, MED_LO, MED_HI, color=ORANGE, alpha=0.20, lw=0, zorder=2)
axC.plot(dd, Q_MED["med"], color=ORANGE, lw=2.2, zorder=6)
# molecular catalyst: the published k = 0 floor as the line; ONE band from the floor's lower quartile up
# to the upper quartile of the same rows re-solved at the top of the declared rate-constant band
# (julia/run_catalyst_ecprime.jl, G-CATK). The floor is the published number and all of the declared
# uncertainty is upward, so the band is one-sided by construction.
Q_CAT0 = quantile_traces(class_traces("catalyst"), "delta_um", "i_mAcm2", "row", dd)
_ck = pd.read_csv(os.path.join(SEC4, "julia", "catalyst_ec_sweep.csv"))
_ck_kmax = _ck.k_M.max(); _ckt = _ck[_ck.k_M == _ck_kmax]
Q_CATK = quantile_traces(_ckt, "delta_um", "i_ec_mAcm2", "reaction", dd)
axC.fill_between(dd, Q_CAT0["lo"], Q_CATK["hi"], color=RED, alpha=0.16, lw=0, zorder=2)
axC.plot(dd, Q_CAT0["med"], color=RED, lw=2.2, zorder=6)
# the record: every class median at the archetype films, read off the grid
for _nm, _q in (("direct", Q_SUB), ("mediated", Q_MED), ("catalyst k=0", Q_CAT0), (f"catalyst k={_ck_kmax:g}", Q_CATK)):
    _at = ", ".join(f"{MM.ARCH_LABEL[k]} {np.interp(np.log(MM.delta_median(k)), np.log(dd[::-1]), _q['med'][::-1]):.2f}" for k in MM.ARCHETYPES)   # grid runs thick -> thin; interp wants ascending
    print(f"  {_nm:16s} median at the archetype films: {_at}")
_ck_best = _ckt.groupby("reaction").i_ec_mAcm2.max()
print(f"  catalyst at k = {_ck_kmax:g} M-1 s-1 (G-CATK): {int((_ck_best >= 25).sum())}/{len(_ck_best)} clear 25 in some archetype; "
      f"max amplification x{_ckt.amplification.max():.1f}; {int((_ckt.i_ec_mAcm2 >= 0.95 * _ckt.i_subcap_mAcm2).sum())}/{len(_ckt)} cells at the substrate cap")
# ── the mediated envelope: the three analytic limits, swept over the real 8 ──────
# Each mediated system contributes three limits (SI Eqs. S12-S15), all read from
# julia/mediated_ec_matrix.csv, which stores them per row:
#     commuting  i_t0  = F D_red C_med /(|s| d)           ~ 1/d
#     plateau    i_sav = n_c F C_med sqrt(D_ox k C_S)     d-independent
#     substrate  i_cap = n_S F D_S C_S / d                ~ 1/d
# so the envelope is  min(i_cap, max(i_t0, i_sav))  -- a falling branch, a flat plateau,
# and a second falling branch. i*d is constant per reaction to machine precision (cv ~1e-16),
# so the two 1/d limits are fixed by one coefficient each and the sweep across the eight real
# (C_med, C_S, D) sets IS the concentration band: it is what depletion of either species buys
# or costs. Nothing here is a chosen round number.
#
# SCOPE, stated because it is a real boundary and not a convenience. The envelope holds only
# where the substrate can out-supply the mediator, A_cap/A_t0 = gamma > 1. Two of the eight run
# inverted -- Cl-mediated propylene epoxidation at C_med/C_S = 400 (2.0 M mediator against 5 mM
# substrate, gamma = 0.003) and Br- oxidation (gamma = 0.29). There the analytic substrate cap
# falls below the commuting bound, which an EC' loop cannot honour: the mediator always commutes.
# Checked against the solver: for the six in-scope systems the envelope tracks the converged
# solves to ~15%; for the two inverted ones it under-predicts by 87-99.8%. They are therefore
# drawn, but as open markers outside the band, never folded into it.
_ENV = []
for _rx, _s in MEDM.groupby("reaction"):
    _r = _s.iloc[0]
    _ENV.append(dict(rx=_rx, A_t0=_r.i_tier0_mAcm2 * _r.delta_um,
                     A_cap=_r.i_subcap_mAcm2 * _r.delta_um,
                     i_sav=_r.i_saveant_mAcm2, xk=_r.xk_um))
for _e in _ENV:
    _e["gamma"] = _e["A_cap"] / _e["A_t0"]
IN_SCOPE = [e for e in _ENV if e["gamma"] > 1.0]
INVERTED = [e for e in _ENV if e["gamma"] <= 1.0]


def _envelope(e, d):
    return np.minimum(e["A_cap"] / d, np.maximum(e["A_t0"] / d, e["i_sav"]))


_CURVES = np.array([_envelope(e, dd) for e in IN_SCOPE])   # computed for the record; no longer drawn
# (2026-09-10: the analytic envelope and the 56 solved cells are no longer drawn -- the band above is
# the solved cells' own middle half -- but the envelope-vs-solver gate below still runs on every build.)
# ── gate: the analytic envelope vs the independent solver ────────────────────────
# Not a self-check. The envelope comes from three closed forms (SI Eqs. S12-S15); i_ec comes
# from the Nernst-Planck EC' solver. They share inputs but not a code path, so comparing them
# genuinely tests the claim the panel makes. Only converged rows count -- a Newton-wall row is
# a lower bound and cannot falsify an envelope. The threshold is deliberately loose: it is here
# to catch a regression, not to certify agreement, and the measured value is printed either way.
# What can and cannot be checked here, stated exactly.
#
# This block used to keep only rows whose limiter did not start with "newton-wall" and then
# require two-sided agreement with the envelope. That looked like a strong test and was not
# one: until 2026-08-23 npp_ecprime.jl overwrote the wall marker with a PHYSICAL limiter
# whenever the stalled state happened to satisfy the collapse criterion, so 14 rows that had
# in fact ended on a Newton failure were read here as converged. The gate was validating the
# envelope against lower bounds while reporting it had validated against solutions.
#
# With the marker no longer erased, all 44 wall rows are visible -- and every genuinely
# converged row belongs to Cl-mediated propylene epoxidation, which is INVERTED (gamma =
# 0.003) and out of scope here. So NO two-sided check is available on the gamma > 1 systems.
#
# The tempting replacement -- "i_ec may not exceed i_subcap, so a row above it refutes the
# envelope" -- was written, fired on 17 rows, and is WRONG, so it is recorded here rather
# than shipped. i_subcap = n_S F D_S C_S / delta assumes the reaction front sits AT the
# electrode. When the substrate is depleted the front detaches and the rigorous bound becomes
# n_S F D_S C_S / (delta - x_f), which is larger without limit as x_f -> delta. Exceeding
# i_subcap is therefore evidence that the front has moved, not evidence of a broken solve.
#
# What IS rigorous is the other side: the homogeneous source only ADDS to the mediator flux,
# so i_ec can never sit below the commuting bound i_t0. That is checked here and is the same
# criterion run_mediated.jl writes into the `flag` column, so a disagreement between the two
# means the CSV and this figure disagree about which rows are usable -- which is worth
# catching on its own.
_in = {e["rx"] for e in IN_SCOPE}
_scope = MEDM[MEDM.reaction.isin(_in)]
_below = _scope[_scope.i_ec_mAcm2 < 0.9 * _scope.i_tier0_mAcm2]
_disagree = _scope[(_scope.i_ec_mAcm2 < 0.9 * _scope.i_tier0_mAcm2) != (_scope.flag != "ok")]
if len(_disagree):
    raise AssertionError(
        f"the commuting-bound test and run_mediated.jl's `flag` column disagree on "
        f"{len(_disagree)} row(s): the CSV and this figure would use different rows")
# The envelope's substrate-cap term, i_cap = n_S F D_S C_S / delta, is a FRONT-AT-THE-ELECTRODE
# construction. When the substrate is exhausted at the wall the reaction front DETACHES into the
# interior, the supply length becomes delta - x_f rather than delta, and i_cap stops binding.
# So the two-sided test is meaningful only where the front has not detached, and is applied only
# there. Rows above the cap are reported with their ratio and counted, never silently dropped --
# and the count is written onto the figure, so panel c declares the limitation on its face.
#
# This is not a hypothetical carve-out. The Br-mediated Hofmann x unstirred cell, resolved by
# delta-continuation on 2026-08-23, is the first genuinely converged in-scope row this gate has
# ever had, and it sits 2.2x above its own i_cap with the front at x_f/delta = 0.506. Judged by
# the old blanket 25% tolerance it reported a 54% "regression" in an envelope that had not
# changed at all.
_conv = [r for r in _scope.itertuples() if not str(r.limiter).startswith("newton-wall")]
_env = lambda r: min(r.i_subcap_mAcm2, max(r.i_tier0_mAcm2, r.i_saveant_mAcm2))
_attached = [r for r in _conv if r.i_ec_mAcm2 <= 1.05 * r.i_subcap_mAcm2]
_detached = [r for r in _conv if r.i_ec_mAcm2 > 1.05 * r.i_subcap_mAcm2]
N_DETACHED = len(_detached)
_wall = int(sum(str(x).startswith("newton-wall") for x in _scope.limiter))
for _r in _detached:
    print(f"  detached front: {_r.reaction[:34]} @ {_r.delta_um:.0f} um -- "
          f"i_ec {_r.i_ec_mAcm2:.1f} = {_r.i_ec_mAcm2/_r.i_subcap_mAcm2:.2f}x i_cap "
          f"({_r.i_subcap_mAcm2:.1f}); the cap does not bind here")
if _attached:
    _dev = np.array([abs(_env(r) - r.i_ec_mAcm2) / r.i_ec_mAcm2 for r in _attached])
    print(f"envelope vs solver: {len(_attached)} converged attached-front in-scope rows, "
          f"median |dev| {np.median(_dev):.3f}, max {_dev.max():.3f}; "
          f"{N_DETACHED} detached, {_wall} wall rows")
    if np.median(_dev) > 0.25:
        raise AssertionError(
            f"the EC' envelope no longer tracks the solver on the attached-front gamma > 1 "
            f"systems (median |dev| {np.median(_dev):.2f}) -- these are the rows where i_cap "
            f"DOES bind, so this is a real regression, not a front effect")
else:
    if len(_scope) == 0:
        raise AssertionError("no in-scope rows at all: nothing about panel c can be checked")
    print(f"envelope vs solver: NO attached-front converged in-scope row exists, so the envelope "
          f"is not checked two-sided. {N_DETACHED} converged rows have DETACHED fronts and sit "
          f"above their own i_cap; {_wall} rows end on the Newton wall and are lower bounds "
          f"(tight to <0.5%, docs/ECPRIME_WALL_FINDING.md). {len(_scope) - len(_below)}/"
          f"{len(_scope)} clear the commuting bound i_t0, the one rigorous relation available.")
# and the scope split the footnote states must be the one the data gives
assert len(IN_SCOPE) + len(INVERTED) == MEDM.reaction.nunique(), "scope split lost a system"


for thr, lab in ((25, "25"), (50, "50")):
    axC.axhline(thr, color=DK, ls=":", lw=0.8, zorder=1)
    # short labels: the y-axis already carries the unit, and the full string collided with the
    # legend on the left and was clipped off the axes on the right
    axC.text(0.012, thr * 1.12, lab, transform=axC.get_yaxis_transform(),
             fontsize=ANN, color=DK, va="bottom", ha="left",
             bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))
for _k in MM.ARCHETYPES:                                        # the seven archetype films
    axC.axvline(MM.delta_median(_k), color="0.88", lw=0.6, zorder=0)
axC.set_xscale("log")
axC.set_yscale("log")
axC.set_xlim(D_LO * 1.14, D_HI / 1.3)
axC.set_ylim(0.1, 1e4)
axC.set_xlabel("$\\delta$ (µm)", fontsize=AX)
axC.set_ylabel("$i_{lim}$ (mA cm$^{-2}$)", fontsize=AX)
FS.legend(axC, handles=[
    Line2D([0], [0], color=BLUE, lw=2.2, label=f"direct substrate ({Q_SUB['n']}): median, middle half of the class"),
    Line2D([0], [0], color=ORANGE, lw=2.2,
           label=f"mediated EC$^{{\\prime}}$ ({Q_MED['n']}): median at the cited k, middle half"
                 + (" widened by a tenfold k either way" if MED_KBAND else " of the class")),
    Line2D([0], [0], color=RED, lw=2.2,
           label=f"molecular catalyst ({Q_CAT0['n']}): median at k = 0, band to k = 10$^{{{int(np.log10(_ck_kmax))}}}$")],
    loc="upper left", fontsize=6.5, handlelength=1.6, labelspacing=0.3, frameon=True,
    framealpha=0.92, facecolor="white", edgecolor="none")
axC.xaxis.set_minor_locator(LogLocator(base=10, subs=tuple(np.arange(2, 10) * .1), numticks=99))
axC.yaxis.set_minor_locator(LogLocator(base=10, subs=tuple(np.arange(2, 10) * .1), numticks=99))
axC.set_xticks([100, 10])
axC.set_xticklabels(["100", "10"])

# ════════════════ d,e,f) EC' regimes — the three rows of (g), solved profiles AT i_lim on the ANEC film ═══════════════
XLO, XHI = 0.2, 40.0      # um: the first production-mesh node sits at 0.02-0.18 um; the film ends at 36.2

def reaction_share(g):
    """rho(x) = k c_ox c_S x / (s_ox i/F): the local reaction rate per DECADE of distance, in units of the
    electrode's own flux of the activated form (s_ox i/F; s_ox = 1 for ACT+ and PINO, 0.5 for Br2, which carries two
    electrons), so the area under rho against ln x is the share of the activated mediator consumed inside the film
    (author, 2026-09-10: show how the local rates differ). k is converted M^-1 s^-1 -> m^3 mol^-1 s^-1 exactly as
    run_mediated_profiles.jl does; every concentration is the row's own (the artifact carries them)."""
    k = float(g.k_M.iloc[0]); i_A = float(g.i_profile_mAcm2.iloc[0]) * 10.0            # mA cm^-2 -> A m^-2
    x_m = g.x_um.values * 1e-6
    r = (k / 1000.0) * (g.c_ox_norm.values * float(g.C_med_molm3.iloc[0])) * (g.c_S_norm.values * float(g.C_S_molm3.iloc[0]))   # mol m^-3 s^-1
    rho = r * x_m / (float(g.s_ox.iloc[0]) * i_A / F_CONST)
    _tr = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return rho, float(_tr(rho, np.log(x_m)))


def ecpanel(ax, k):
    g = reg(k).sort_values("x_um")                          # k here is the row's short name (the artifact is keyed by row)
    xk = float(g.xk_um.iloc[0])
    il = float(g.ilim_mAcm2.iloc[0])
    dlt = float(g.delta_um.iloc[0])
    ax.fill_between(g.x_um, 0, g.c_ox_norm, color=ORANGE_ACT_C, alpha=0.22, zorder=1)
    ax.plot(g.x_um, g.c_ox_norm, color=ORANGE_ACT_C, lw=1.9, zorder=4)           # active form: light, solid (as in b)
    ax.plot(g.x_um, g.c_red_norm, color=ORANGE, lw=1.6, ls=(0, (5, 2)), zorder=3)   # resting form: full shade, dashed
    ax.plot(g.x_um, g.c_S_norm, color=BLUE, lw=1.5, ls=(0, (1, 1.2)), zorder=3)
    rho, share = reaction_share(g)
    ax.fill_between(g.x_um, 0, rho, color="0.45", alpha=0.22, zorder=2)
    ax.plot(g.x_um, rho, color="0.35", lw=1.0, zorder=3.5)
    print(f"    reaction share inside delta, {k}: {share:.3f}  (area under rho d ln x; peak rho {rho.max():.2f}; the artifact says {float(g.share_in_film.iloc[0]):.3f})")
    assert abs(share - float(g.share_in_film.iloc[0])) < 0.01, (k, share, float(g.share_in_film.iloc[0]))   # the same integral, two code paths
    if xk < XHI:
        ax.axvline(xk, color="#999", lw=0.7, ls=":", zorder=2)
    ax.axvline(dlt, color=DK, lw=0.8, zorder=2)
    ax.set_xscale("log")
    ax.set_xlim(XLO, XHI)
    _ymax = max(1.0, float(g.c_ox_norm.max()), float(g.c_red_norm.max()), float(rho.max()))
    if _ymax > 1.14:
        # v90: the Hofmann row's Br2 accumulates behind its detached front to several times the bromide bulk, and the
        # regenerated Br- overshoots its bulk value at the front; a panel drawn to the shared 0-1.14 scale would clip both
        # (and the rate hump) and hide the very shape that names the regime, so this panel takes the range its own
        # curves need and says so on its axis.
        ax.set_ylim(0, 1.06 * _ymax)
        _step = 1.0 if _ymax > 3 else 0.5
        ax.set_yticks(np.arange(0, 1.06 * _ymax, _step))
        print(f"    panel y-range extended to {1.06 * _ymax:.2f} (curves reach {_ymax:.2f} x bulk)")
    else:
        ax.set_ylim(0, 1.14)                               # floor at exactly 0 (author, 2026-09-10); headroom so a curve at 1.0 stays visible and can carry its label above
    ax.set_xlabel("distance from electrode (µm)", fontsize=AX)
    ax.xaxis.set_minor_locator(LogLocator(base=10, subs=tuple(np.arange(2, 10) * .1), numticks=99))
    print(f"  panel {k}: x_k {xk:.3f} um, delta {dlt:.1f} um, i_lim {ge(k)} {il:.2f} mA cm-2")
    return il


iD = ecpanel(axD, PANEL_ROWS[0]); iE = ecpanel(axE, PANEL_ROWS[1]); iF = ecpanel(axF, PANEL_ROWS[2])
for _ax, _s in zip((axD, axE, axF), PANEL_ROWS):
    _key = str(reg(_s).regime_solved.iloc[0]); assert _key in REGIME_LABEL, _key
    _ax.set_title(ROW_TITLE[_s] + " M$^{-1}$ s$^{-1}$\n" + REGIME_LABEL[_key], fontsize=6.8, color=FS.SLATE, fontweight="bold", pad=3, linespacing=1.25)
axD.set_ylabel("c / $c_{bulk}$", fontsize=AX)
import matplotlib.patheffects as _pe
def label_curves(ax, g, names=("Med$_{ox}$", "Med$_{red}$"), fs=6.5, off=0.075, y_top=1.04, y_bot=0.06):
    """Direct labels on the profiles (author, 2026-09-10). Placement runs in a NORMALISED frame -- the panel's y-range mapped
    onto 0-1.14, so every threshold means the same fraction of the panel whatever range the panel needed (v90: the Hofmann
    panel runs to 5 x bulk). For each curve, every candidate position (above or below it, over an x range the label's own
    width fits inside the frame) is scored by the distance from the LABEL'S CENTRE to the other curves, to labels already
    placed, and to the grey reaction fill; positions where the curve is steep under the text are excluded. If no flat
    position exists the label runs ALONG the curve, clipped by its rotated footprint and kept inside the frame; if it cannot
    be kept inside that way either, it sits on the flat stretch immediately before the curve begins to rise (the one place
    left when a curve rises only in the last quarter-decade of a panel). Positions come from the solve, not by hand."""
    x = g.x_um.values
    rho_raw, share = reaction_share(g)
    y0, y1 = ax.get_ylim(); ysc = (y1 - y0) / 1.14                # data units per normalised unit
    N = lambda arr: (np.asarray(arr, float) - y0) / ysc
    D = lambda yn: y0 + yn * ysc
    rho = N(rho_raw)
    curves = {names[0]: (N(g.c_ox_norm.values), "#C98A45", 0.6), names[1]: (N(g.c_red_norm.values), ORANGE, 0.6),
              "substrate": (N(g.c_S_norm.values), BLUE, 0.7), "reaction rate": (rho, "0.30", 1.5)}
    lo, hi = np.log10(XLO) + 0.06, np.log10(XHI) - 0.06
    # each label's width in decades, from its own text and the panel's real size (author 2026-09-10:
    # "keep it inside the lines"): ~0.55 em per character at this size, plus the halo
    pts_per_dec = ax.get_window_extent().width * 72.0 / ax.figure.dpi / (np.log10(XHI) - np.log10(XLO))
    def _wdec(text):
        import re as _re
        plain = _re.sub(r"[\\$_{}^]", "", text.replace("\\delta", "d"))
        return (0.55 * fs * len(plain) + 3.0) / pts_per_dec + 0.08
    def _put(n, col, xi, yi, rot=0.0):
        ax.text(xi, D(yi), n, color=col, fontsize=fs, ha="center", va="center", rotation=rot, rotation_mode="anchor",
                path_effects=[_pe.withStroke(linewidth=2.2, foreground="white")], zorder=8)
    placed = []
    for n, (v, col, _unused) in curves.items():
        wdec = _wdec(n)
        xs = np.logspace(lo + wdec / 2, hi - wdec / 2, 90)
        ys = {m: np.interp(np.log(xs), np.log(x), vv) for m, (vv, cc, ww) in curves.items()}
        rho_x = np.interp(np.log(xs), np.log(x), rho)
        others = [ys[m] for m in ys if m != n]
        best = None
        if n.startswith("reaction"):
            # the reaction label sits ON its hump: candidates around the peak, at whatever height is
            # clearest of the other curves and the labels already placed
            xp = float(x[int(np.argmax(rho))]); xc = np.clip(np.log10(xp) + np.linspace(-0.5, 0.5, 11), lo + wdec / 2, hi - wdec / 2)
            xc = 10 ** np.unique(np.round(xc, 4))
            oth = {m: np.interp(np.log(xc), np.log(x), vv) for m, (vv, cc, ww) in curves.items() if m != n}
            pk = float(rho.max())
            def _search(y_hi):
                bb = None
                for yc0 in np.linspace(y_bot, y_hi, 40):
                    score = np.minimum.reduce([np.abs(yc0 - o) for o in oth.values()])
                    for (px, py) in placed:
                        score = np.where((np.abs(np.log10(xc / px)) < 0.5 * (wdec + 0.6)) & (abs(yc0 - py) < 0.13), -1.0, score)
                    k = int(np.argmax(score))
                    if bb is None or score[k] > bb[0]: bb = (score[k], xc[k], yc0)
                return bb
            best = _search(min(y_top, pk + 0.18)); leader = False              # first: near the hump
            if best[0] < 0.08:
                best = _search(y_top); leader = True                           # else: wherever it is clear, with a leader
            sc, xi, yi = best; placed.append((xi, yi))
            # a label more than a quarter-decade from the peak, or well above it, gets a leader too (v90: the Hofmann hump)
            leader = leader or abs(np.log10(xi / xp)) > 0.25 or (yi - pk) > 0.25
            _put(n, col, xi, yi)
            if leader:
                ax.plot([xi, xp], [D(yi - 0.045), D(pk + 0.01)], color="0.45", lw=0.6, zorder=7)
            print(f"    label {n[:22]:22s} at x = {xi:.2f} um, y = {D(yi):.2f}, clearance {sc:.2f}")
            continue
        for off_i, guard in ((off, 0.8), (2 * off, 1.6), (3 * off, 2.4)):        # widen the offset only if nothing fits
          for sgn in (+1, -1):
              yc = ys[n] + sgn * off_i
              score = np.minimum.reduce([np.abs(yc - o) for o in others])
              # a label belongs where its curve carries information, not on a stretch flat at zero (author
              # 2026-09-10, the Med_ox spike at k = 1e5) -- unless the curve is like that everywhere
              if (ys[n] > 0.03).any():
                  score = np.where(ys[n] > 0.03, score, -1.0)
              own_l = np.interp(np.log(xs / 10 ** (wdec / 2)), np.log(x), v); own_r = np.interp(np.log(xs * 10 ** (wdec / 2)), np.log(x), v)
              score = np.where(np.maximum(np.abs(own_l - ys[n]), np.abs(own_r - ys[n])) > guard * off, -1.0, score)
              score = np.where(yc < rho_x + 0.05, -1.0, score)                     # keep out of the grey fill
              for (px, py) in placed:
                  score = np.where((np.abs(np.log10(xs / px)) < 0.5 * (wdec + 0.6)) & (np.abs(yc - py) < 0.13), -1.0, score)
              score = np.where((yc > y_top) | (yc < y_bot), -1.0, score)
              k = int(np.argmax(score))
              if best is None or score[k] > best[0]: best = (score[k], xs[k], yc[k])
          if best is not None and best[0] >= 0.05: break
        sc, xi, yi = best
        rot = 0.0
        if sc < 0.05:
            # no flat position exists (a line rising ~0.6 per decade is crossed by any horizontal text): run the label
            # ALONG the curve, on the clearer side, anchored where the curve passes a level that keeps the rotated text
            # inside the frame; the anchor is clipped by the text's ROTATED footprint, not its full width
            vmono = v.min() < v.max()
            vmax_n = min(1.14, max(float(v.max()), 1.0))
            def _rot_at(xq):
                xa, xb = xq / 10 ** 0.3, xq * 10 ** 0.3
                ya, yb = float(np.interp(np.log(xa), np.log(x), v)), float(np.interp(np.log(xb), np.log(x), v))
                pa, pb = ax.transData.transform((xa, D(ya))), ax.transData.transform((xb, D(yb)))
                return float(np.degrees(np.arctan2(pb[1] - pa[1], pb[0] - pa[0])))
            px_h = ax.get_window_extent().height
            best_c = None
            for lvl in (0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8):
                lv = lvl * vmax_n
                xr = float(np.interp(lv, v, x)) if (vmono and v.min() < lv < v.max()) else float(x[int(np.argmax(np.abs(np.gradient(v))))])
                rot_c = _rot_at(float(np.clip(xr, 10 ** lo, 10 ** hi)))
                wrot = wdec * abs(np.cos(np.radians(rot_c))) + 0.04
                xr = float(np.clip(xr, 10 ** (lo + wrot / 2), 10 ** (hi - wrot / 2)))
                rot_c = _rot_at(xr)
                nx, ny = -np.sin(np.radians(rot_c)), np.cos(np.radians(rot_c))                 # unit normal, display
                yr = float(np.interp(np.log(xr), np.log(x), v)); pc = ax.transData.transform((xr, D(yr)))
                gap = 7.0 * ax.figure.dpi / 72.0
                half_pts = 0.5 * (0.55 * fs * len(n.replace("$", "")) * abs(np.sin(np.radians(rot_c))) + fs * abs(np.cos(np.radians(rot_c))))
                half_n = half_pts * ax.figure.dpi / 72.0 / px_h * 1.14
                for sgn in (+1, -1):
                    q = ax.transData.inverted().transform((pc[0] + sgn * gap * nx, pc[1] + sgn * gap * ny))
                    qn = float(N(q[1]))
                    inside = (qn - half_n >= 0.0) and (qn + half_n <= 1.14)
                    oth = min(abs(qn - float(np.interp(np.log(q[0]), np.log(x), o_v))) for o_v in [vv for m, (vv, cc, ww) in curves.items() if m != n])
                    cand = (1 if inside else 0, oth, q[0], qn, rot_c)
                    if best_c is None or cand[:2] > best_c[:2]: best_c = cand
                if best_c[0] == 1 and best_c[1] > 0.08: break
            _ins, sc, xi, yi, rot = best_c
            if _ins == 0:
                # nothing fits along the curve inside the frame either: the flat stretch just before the rise
                rise = np.where(v > 0.03)[0]
                if len(rise) and rise[0] > 0:
                    xr0 = float(x[rise[0]])
                    xi = float(np.clip(10 ** (np.log10(xr0) - wdec / 2 - 0.03), 10 ** (lo + wdec / 2), 10 ** (hi - wdec / 2)))
                    yi = float(np.interp(np.log(xi), np.log(x), v)) + off; rot = 0.0
                    sc = min(abs(yi - float(np.interp(np.log(xi), np.log(x), o_v))) for o_v in [vv for m, (vv, cc, ww) in curves.items() if m != n])
                    print(f"    label {n[:22]:22s}: no in-frame position on or along the curve; placed before its rise")
        placed.append((xi, yi))
        _put(n, col, xi, yi, rot)
        print(f"    label {n[:22]:22s} at x = {xi:.2f} um, y = {D(yi):.2f}, clearance {sc:.2f}" + (f", rotated {rot:.0f} deg" if rot else ""))
for _ax, _s in zip((axD, axE, axF), PANEL_ROWS):
    label_curves(_ax, reg(_s).sort_values("x_um"), names=SPECIES_LABEL[_s])
axF2 = axF.twinx(); axF2.set_ylim(axF.get_ylim())   # (shares the 0-1.14 range; ticks to 1.0)
axF2.tick_params(axis="y", which="both", direction="in", labelsize=TICK, colors="0.35", length=3)
axF2.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0]); axF2.minorticks_off()
axF2.set_ylabel("$k\\,c_{ox}\\,c_S\\,x\\,/\\,(s_{ox}\\,i/F)$", fontsize=AX, color="0.35")   # author 2026-09-10: the expression only; the caption says what it is
for _sp in axF2.spines.values(): _sp.set_visible(False)


# ════════════════ g) h) intensification: i_lim against the film thickness ═══════════════════════
# (g) three of the eight mediated rows at their cited rate constants, one per regime, across seventeen films
#     (the seven archetype medians and log-spaced fill) from julia/run_mediated_delta.jl.
# (h) three of the seven catalyst rows the matrix now carries at a SOURCED rate constant (2026-09-11,
#     docs/CATALYST_RATE_CONSTANTS_20260911.md): one per basis -- Ni(I)-bipyridine + aryl bromide
#     (Ni-XEC, k = 1e2), cobalt hydride + alkene (hydroamination, 7e2) and the Co(salen) aza-Wacker
#     step (1e1, the class median row) -- each with its own k = 0 floor dashed beneath it, from
#     julia/run_catalyst_delta.jl on the same seventeen films. Every curve is a solve; nothing is drawn
#     from a formula.
_CAT = pd.read_csv(os.path.join(SEC4, "julia", "catalyst_ec_delta.csv"))
_FILMS = [MM.delta_median(_k) for _k in MM.ARCHETYPES]
_DK = "#222222"
# VARIANT (author question, 2026-09-11: "normalize the i_lims by the concentration and the diffusivity of the mediator ...
# to isolate the effect of intensification"): with FIG6_GH_NORM=1 in the environment, (g) and (h) plot
# i_lim / (F D_carrier C_carrier) in um^-1 -- each row divided by its own Fick bound times the film, a row CONSTANT, so no
# curve changes shape and no gain changes; what changes is that every neutral carrier's k = 0 floor collapses onto the ONE
# line 1/delta, and a row's height above that line is what its chemistry buys per unit of carrier. In the kinetic regime
# the normalised current is exactly 1/x_k (Saveant), so the flat ACT curve reads as its reaction layer. The 25 and 50
# mA cm-2 thresholds cannot be drawn on that axis (they sit at a different height for every row), which is the cost. The
# variant writes combined_figure_grounded_normalized_gh.{png,svg} and never touches the shipped render.
_NORM = os.environ.get("FIG6_GH_NORM") == "1"
def _yv(i, i_fick, d):
    """the quantity plotted on (g)/(h): the current itself, or the current per F D_carrier C_carrier (um^-1)"""
    return (np.asarray(i) / (np.asarray(i_fick) * np.asarray(d))) if _NORM else np.asarray(i)
_THRESH_LINES = []
for _ax in (axG, axH):
    _ax.set_xscale("log"); _ax.set_yscale("log"); _ax.set_xlim(260 * 1.02, 8 / 1.02); _ax.set_ylim(0.1, 1500)
    _ax.set_xticks([100, 10]); _ax.set_xticklabels(["100", "10"])
    _ax.xaxis.set_minor_locator(LogLocator(base=10, subs=tuple(np.arange(2, 10) * .1), numticks=99))
    _ax.yaxis.set_minor_locator(LogLocator(base=10, subs=tuple(np.arange(2, 10) * .1), numticks=99))
    _ax.set_xlabel("$\\delta$ (µm)", fontsize=AX)
    if _NORM:
        _dd = np.logspace(np.log10(8), np.log10(260), 50)
        _ax.plot(_dd, 1.0 / _dd, color="0.45", lw=1.0, zorder=2)                   # the common k = 0 floor of a neutral carrier
    else:
        for _thr in (25, 50):      # v92 (author): red dotted with red "mA cm-2" labels, as Figure 5 draws them
            _THRESH_LINES.append(_ax.axhline(_thr, color=RED, ls=":", lw=1.0, zorder=1, alpha=0.85))
            _ax.text(0.02, _thr * 1.07, str(_thr) + " mA cm$^{-2}$", transform=_ax.get_yaxis_transform(), fontsize=ANN, color=RED, ha="left", va="bottom", zorder=6)
axG.set_ylabel("$i_{lim}\\,/\\,(F\\,D_{carrier}\\,C_{carrier})$ (µm$^{-1}$)" if _NORM else "$i_{lim}$ (mA cm$^{-2}$)", fontsize=AX)
axH.tick_params(axis="y", labelleft=False)

_LBL_OFF = 5.2                        # points from the curve centre to the label centre
def _along(ax, xs, ys, text, col, xc, side, fs=ANN):
    """a label running along a curve, offset to one side of it (display-space normal); the curve is
    solved on a decreasing delta grid, so it is reversed for interpolation"""
    lx, ly = np.log(xs[::-1]), ys[::-1]
    f = lambda v: float(np.interp(np.log(v), lx, ly))
    pa, pb, pc = (ax.transData.transform((xc * 2, f(xc * 2))), ax.transData.transform((xc / 2, f(xc / 2))),
                  ax.transData.transform((xc, f(xc))))
    rot = float(np.degrees(np.arctan2(pb[1] - pa[1], pb[0] - pa[0]))); nx, ny = -np.sin(np.radians(rot)), np.cos(np.radians(rot))
    q = ax.transData.inverted().transform((pc[0] + side * _LBL_OFF * fig.dpi / 72 * nx,
                                          pc[1] + side * _LBL_OFF * fig.dpi / 72 * ny))
    ax.text(q[0], q[1], text, fontsize=fs, color=col, ha="center", va="center", rotation=rot, rotation_mode="anchor",
            path_effects=[_pe.withStroke(linewidth=1.6, foreground="white")], zorder=8)
    return rot, pc, (nx, ny)

fig.tight_layout(pad=0.6, w_pad=1.5, h_pad=1.45)      # the along-curve rotations need the final axes geometry
# -- (g) mediated: three of the eight rows, one per regime, at their CITED rate constants (2026-09-11,
#    author: "I LOVE how h corresponds to 3 different chemistries, can we do that for the mediated g?").
#    ACT alcohol oxidation (k = 20, x_k 7.7 um: kinetic, flat), NHPI allylic C-H (k = 0.5, x_k 158 um:
#    mediator-limited, on its own transport bound) and the bromide-mediated Hofmann rearrangement (k = 1e3,
#    x_k 2.4 um: substrate-limited on a DETACHED front, above its planar substrate cap). Same species,
#    conditions and accept sequence as the published cells (julia/run_mediated_delta.jl); every point a solve.
_MEDD = pd.read_csv(os.path.join(SEC4, "julia", "mediated_ec_delta.csv"))
# the ACT and NHPI curves cross near 30 um, so their labels sit at opposite ends: ACT above its flat curve at the
# thick-film end, NHPI above its rising curve at the thin-film end
_GROWS = [("ACT-mediated alcohol oxidation (flow, hectogram)", "#8C4A1A", "ACT, k = 20: kinetic", 18, -1),        # v92: below, thin end, clear of the 25 line
          ("NHPI-mediated allylic C-H -> enone", "#E3A46B", "NHPI, k = 0.5: mediator-limited", 85, -1),             # v92: below its curve mid-panel, clear of the 50 line and inside both frame edges
          ("Br-mediated Hofmann rearrangement", "#C1611E", "Br$^{-}$/Hofmann, k = 10$^{3}$: substrate-limited", 60, +1)]
if _NORM:   # normalised, ACT and Hofmann cross near 60 um and NHPI rides the grey line: labels where each curve is alone
    _GROWS = [("ACT-mediated alcohol oxidation (flow, hectogram)", "#8C4A1A", "ACT, k = 20: kinetic", 170, +1),
              ("NHPI-mediated allylic C-H -> enone", "#E3A46B", "NHPI, k = 0.5: mediator-limited", 30, -1),
              ("Br-mediated Hofmann rearrangement", "#C1611E", "Br$^{-}$/Hofmann, k = 10$^{3}$: substrate-limited", 40, +1)]
_GCURVES, _HCURVES = [], []
_GFRAME, _HFRAME = {}, {}
for _rx, _col, _lab, _xc, _side in _GROWS:
    _g = _MEDD[_MEDD.reaction == _rx].sort_values("delta_um", ascending=False)
    if len(_g) == 0:
        raise SystemExit(f"{_rx!r} missing from mediated_ec_delta.csv")
    if (_g.flag != "ok").any():
        raise SystemExit(f"{_rx}: {int((_g.flag != 'ok').sum())} film(s) did not reach a plateau above the floor")
    axG.plot(_g.delta_um, _yv(_g.i_ec_mAcm2, _g.i_tier0_mAcm2, _g.delta_um), color=_col, lw=2.0, zorder=5)
    _gf = _g[_g.delta_um.round(3).isin([round(_f, 3) for _f in _FILMS])]
    axG.scatter(_gf.delta_um, _yv(_gf.i_ec_mAcm2, _gf.i_tier0_mAcm2, _gf.delta_um), s=9, color=_col, zorder=6)
    if _rx.startswith("Br-mediated Hofmann") and _NORM:   # v91 (author): the cap and floor lines come off the shipped panel; the variant keeps them
        axG.plot(_g.delta_um, _yv(_g.i_subcap_mAcm2, _g.i_tier0_mAcm2, _g.delta_um), color=_col, ls=(0, (1, 1.5)), lw=0.9, alpha=0.8, zorder=2)   # the cap the front detaches from
        axG.plot(_g.delta_um, _yv(_g.i_k0_mAcm2, _g.i_tier0_mAcm2, _g.delta_um), color=_col, lw=1.1, ls=(0, (4, 2)), alpha=0.75, zorder=4)   # its own k = 0 floor, 2/delta (migration)
    print(f"  (g) {_rx[:34]:34s} k={_g.k_M.iloc[0]:g}: {_g.i_ec_mAcm2.iloc[0]:.2f} -> {_g.i_ec_mAcm2.iloc[-1]:.2f} mA cm-2 over "
          f"{_g.delta_um.iloc[0]:.0f} -> {_g.delta_um.iloc[-1]:.0f} um, x{_g.i_ec_mAcm2.iloc[-1]/_g.i_ec_mAcm2.iloc[0]:.1f}; "
          f"i_ec/i_k0 {float((_g.i_ec_mAcm2 / _g.i_k0_mAcm2).min()):.2f}-{float((_g.i_ec_mAcm2 / _g.i_k0_mAcm2).max()):.2f}; "
          f"i_ec/cap {float((_g.i_ec_mAcm2 / _g.i_subcap_mAcm2).min()):.2f}-{float((_g.i_ec_mAcm2 / _g.i_subcap_mAcm2).max()):.2f}")
    _GCURVES.append((_rx, _col, _g.delta_um.values,
                     _yv(_g.i_ec_mAcm2.values, _g.i_tier0_mAcm2.values, _g.delta_um.values), _xc))
    _GFRAME[_rx] = _along(axG, _g.delta_um.values, _yv(_g.i_ec_mAcm2.values, _g.i_tier0_mAcm2.values, _g.delta_um.values), _lab, _col, _xc, _side) + (_side,)
if _NORM:
    axG.set_ylim(0.002, 4); axH.set_ylim(0.002, 4)
else:
    # 2026-10-02: the ranges open a little so each curve has a band of its own for its reaction
    # scheme. Nothing about the data moves -- (g)'s curves span 4.5-3342 and (h)'s 0.57-24 either
    # way -- but at the old limits (h)'s three curves left ONE usable band and three schemes
    # competed for it, which is what pushed two of them away from the lines they belong to.
    axG.set_ylim(1, 5000) if not _INLINE else axG.set_ylim(0.6, 12000)
    axH.set_ylim(0.4, 300) if not _INLINE else axH.set_ylim(0.13, 900)
axG.text(0.03, 0.96, "mediated, cited k", transform=axG.transAxes, fontsize=6.8, color=FS.SLATE, fontweight="bold", va="top")
if _NORM:
    axG.text(0.97, 0.06, "grey: k = 0, neutral carrier (1/$\\delta$)\ndashed: Hofmann at k = 0 (2/$\\delta$); dotted: its substrate cap",
             transform=axG.transAxes, fontsize=6, color="0.4", ha="right", va="bottom", linespacing=1.3)
# -- (h) molecular catalyst, three sourced rows and their floors
# the nickel and cobalt-hydride rows nearly coincide (4.4 -> 24 and 4.8 -> 18 mA cm-2), so their labels sit at
# opposite ends of the film range: nickel below its curve at the thick end, cobalt above at the thin end
_HROWS = [("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "#7A1626", "Ni–XEC, k = 10$^{2}$", 150, +1 if _INLINE else -1),
          ("Co-H alkene reduction (e-HAT)", "#A31F34", "Co–H, k = 7×10$^{2}$", 30, -1),        # v92: below, thin end, clear of the 25 line
          ("Co-catalyzed aza-Wacker cyclization", "#D2707E", "aza-Wacker, k = 10", 110, +1)]   # v91: above its curve, clear of the tightened frame
if _NORM:   # the aza-Wacker curve merges with the grey line at thin films; its label goes above it at the thick end
    _HROWS = [("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "#7A1626", "Ni–XEC, k = 10$^{2}$", 150, -1),
              ("Co-H alkene reduction (e-HAT)", "#A31F34", "Co–H, k = 7×10$^{2}$", 16, +1),
              ("Co-catalyzed aza-Wacker cyclization", "#D2707E", "aza-Wacker, k = 10", 110, +1)]
_FLOOR = "#E4A19B"
for _rx, _col, _lab, _xc, _side in _HROWS:
    _c = _CAT[_CAT.reaction == _rx]
    if len(_c) == 0:
        raise SystemExit(f"{_rx!r} missing from catalyst_ec_delta.csv")
    _k = float(_c[_c.k_M > 0].k_M.iloc[0])
    _s = _c[_c.k_M == _k].sort_values("delta_um", ascending=False); _z = _c[_c.k_M == 0].sort_values("delta_um", ascending=False)
    axH.plot(_s.delta_um, _yv(_s.i_ec_mAcm2, _s.i_fick_mAcm2, _s.delta_um), color=_col, lw=2.0, zorder=5)
    _sf = _s[_s.delta_um.round(3).isin([round(_f, 3) for _f in _FILMS])]
    axH.scatter(_sf.delta_um, _yv(_sf.i_ec_mAcm2, _sf.i_fick_mAcm2, _sf.delta_um), s=9, color=_col, zorder=6)
    print(f"  (h) {_rx[:34]:34s} k={_k:g}: {_s.i_ec_mAcm2.iloc[0]:.2f} -> {_s.i_ec_mAcm2.iloc[-1]:.2f} (x{_s.i_ec_mAcm2.iloc[-1]/_s.i_ec_mAcm2.iloc[0]:.1f}); "
          f"floor {_z.i_ec_mAcm2.iloc[0]:.2f} -> {_z.i_ec_mAcm2.iloc[-1]:.2f} (x{_z.i_ec_mAcm2.iloc[-1]/_z.i_ec_mAcm2.iloc[0]:.1f})")
    _HCURVES.append((_rx, _col, _s.delta_um.values,
                     _yv(_s.i_ec_mAcm2.values, _s.i_fick_mAcm2.values, _s.delta_um.values), _xc))
    _HFRAME[_rx] = _along(axH, _s.delta_um.values, _yv(_s.i_ec_mAcm2.values, _s.i_fick_mAcm2.values, _s.delta_um.values), _lab, _col, _xc, _side) + (_side,)
axH.text(0.03, 0.96, "molecular catalyst, cited k", transform=axH.transAxes, fontsize=6.8, color=FS.SLATE, fontweight="bold", va="top")
if _NORM:
    axH.text(0.97, 0.06, "grey: k = 0 (1/$\\delta$)", transform=axH.transAxes, fontsize=6, color="0.4", ha="right", va="bottom")

_W, _H = fig.get_size_inches()
_bb = axA.get_position(original=True)
_xspan = FS.LBL_YSPAN * (_bb.width * _W) / (_bb.height * _H)
# ADOPTED v118 (author, 2026-09-21: "make the edits for that section", answering Connor Coley's comment 21):
# the catalyst cell draws its own carrier loading (figstyle.CARRIER_AMP). The two homogeneous cells are the same
# EC' problem and were drawn alike, so the only visible difference had been the substrate's dip and a 2-vs-1
# sphere count in the bulk lane -- which reads as "two mediator species", not as "abundant".
FS.carrier_schematic_lbl(axA, blue=BLUE, orange=ORANGE, red=RED, xspan=_xspan, tag=False, abundance=True)   # author 2026-09-09: the
# one-word tag comes off the face; the state-S declaration moves into the caption's (a) clause (v86)
axA.set_xlim(0, _xspan); axA.set_ylim(0, FS.LBL_YSPAN)
print(f"  panel a: drawn to a {_xspan:.3f} x {FS.LBL_YSPAN:.2f} span "
      f"({_bb.width * _W:.2f} x {_bb.height * _H:.2f} in), cells "
      f"{(_xspan - 2 * FS.CELL_GAP) / 3:.3f} wide")
# ════════════ the reaction each EC-prime panel solves, drawn above it (Jonas Rein, comment 1106) ═══════════
# "because this is a paper that we also want chemists to read, it might be helpful to show the reaction that
# was being done."  Each strip carries the EXEMPLAR its row is anchored to in data/reactions_50.csv:
#   (d) Br-mediated Hofmann rearrangement   -- Malviya & Cantillo, OPRD 2023: 2-phenylacetamide -> the methyl
#       carbamate ("the transformation of 2-phenylacetamide 1a into carbamate 2a was selected as a model").
#   (e) ACT-mediated alcohol oxidation      -- Zhong & Stahl, OPRD 2021 (levetiracetam): primary alcohol to
#       carboxylic acid, ACT = 4-acetamido-TEMPO at 25 mM against 0.5 M substrate.
#   (f) NHPI-mediated allylic C-H oxidation -- Horn & Baran, Nature 2016: valencene -> nootkatone, i.e. an
#       allylic methylene oxidised to the enone, drawn as that bond change on the ring that carries it.
#
# TWO THINGS THAT HAD TO BE GOT RIGHT, both caught by looking at the first render:
#   * the strip is about 2.1 x 0.5 in, so drawing in a 0-1 x 0-1 data box makes every ring a 4:1 ellipse.
#     Each strip sets its x-span to its own box aspect, so one data unit is square and a hexagon is a hexagon.
#   * LATO HAS NO RIGHT-ARROW GLYPH (it prints as tofu), so every arrow here is mathtext, never a literal.
SCH_LW, SCH_FS, SCH_COL = 0.85, 5.4, FS.EDGE


def _ring(ax, cx, cy, r, dbl=(), lw=SCH_LW, col=SCH_COL, tr=None):
    """A hexagon, flat-topped; `dbl` lists edges drawn with a second inner line (a double bond)."""
    a = np.deg2rad(90 + 60 * np.arange(6))
    vx, vy = cx + r * np.cos(a), cy + r * np.sin(a)
    for k in range(6):
        k2 = (k + 1) % 6
        ax.plot([vx[k], vx[k2]], [vy[k], vy[k2]], color=col, lw=lw, solid_capstyle="round", zorder=9,
                    **({"transform": tr} if tr is not None else {}))
        if k in dbl:
            mx, my = (vx[k] + vx[k2]) / 2, (vy[k] + vy[k2]) / 2
            ex, ey = (vx[k2] - vx[k]) * 0.30, (vy[k2] - vy[k]) * 0.30
            ux, uy = cx - mx, cy - my
            n = np.hypot(ux, uy); ux, uy = ux / n * 0.22 * r, uy / n * 0.22 * r
            ax.plot([mx - ex + ux, mx + ex + ux], [my - ey + uy, my + ey + uy],
                    color=col, lw=lw, solid_capstyle="round", zorder=9,
                    **({"transform": tr} if tr is not None else {}))
    return vx, vy


def _b(ax, p0, p1, lw=SCH_LW, col=SCH_COL, tr=None):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=col, lw=lw, solid_capstyle="round", zorder=9,
            **({"transform": tr} if tr is not None else {}))


def _carbonyl(ax, base, d=(0.0, 0.19), gap=0.030, col=SCH_COL, tr=None, rot=0.0):
    """C=O from `base` along `d`, as two parallel bonds with ONE O label at the far end.

    The first version took a signed `up` and its caller added a second O of its own, so the enone
    printed two oxygens, one of them sitting on the strip caption. The label belongs to the helper."""
    (x, y), (dx, dy) = base, d
    n = np.hypot(dx, dy); px, py = -dy / n * gap, dx / n * gap          # unit normal, for the parallel pair
    _b(ax, (x + px, y + py), (x + px + dx, y + py + dy), col=col, tr=tr)
    _b(ax, (x - px, y - py), (x - px + dx, y - py + dy), col=col, tr=tr)
    ax.text(x + dx * 1.16, y + dy * 1.16, "O", ha="center", va="center", fontsize=SCH_FS, color=col,
            rotation=rot, rotation_mode="anchor", zorder=9,
            **({"transform": tr} if tr is not None else {}))


def _arrow(ax, x0, x1, y, over, col=SCH_COL, fs=SCH_FS, tr=None, rot=0.0):
    from matplotlib.patches import FancyArrowPatch
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=5, color=col,
                                 lw=0.85, zorder=9, shrinkA=0, shrinkB=0,
                                 **({"transform": tr} if tr is not None else {})))
    if over:
        ax.text((x0 + x1) / 2, y + 0.055, over, ha="center", va="bottom", fontsize=fs, color=col,
                rotation=rot, rotation_mode="anchor", zorder=9,
                **({"transform": tr} if tr is not None else {}))


def scheme_hofmann(ax, W):
    """2-phenylacetamide -> the methyl carbamate. The benzylic CH2 is a real vertex: drawn without it
    the substrate is benzamide, a different compound (caught by reading the first render)."""
    # this panel carries the two longest labels in the strip, so its ring and bonds are a little smaller
    # and its arrow sits further right; at the first geometry "CONH2" ran straight through the arrow.
    r, cy, fs = 0.165, 0.58, SCH_FS - 0.4
    for cx, lab in ((0.115 * W, "CONH$_2$"), (0.575 * W, "NHCO$_2$Me")):
        vx, vy = _ring(ax, cx, cy, r, dbl=(0, 2, 4))
        mid = (vx[5] + 0.13, vy[5] - 0.09)                      # the benzylic carbon
        _b(ax, (vx[5], vy[5]), mid)
        _b(ax, mid, (mid[0] + 0.13, mid[1] + 0.09))
        ax.text(mid[0] + 0.155, mid[1] + 0.09, lab, ha="left", va="center", fontsize=fs, color=SCH_COL)
    _arrow(ax, 0.405 * W, 0.505 * W, cy, "Br$^-$")


def scheme_act(ax, W):
    cy, d = 0.56, 0.17
    x = 0.10 * W
    _b(ax, (x, cy - d / 2), (x + 0.20, cy + d / 2)); _b(ax, (x + 0.20, cy + d / 2), (x + 0.40, cy - d / 2))
    ax.text(x + 0.44, cy - d / 2 - 0.01, "OH", ha="left", va="center", fontsize=SCH_FS, color=SCH_COL)
    _arrow(ax, 0.44 * W, 0.55 * W, cy, "ACT")
    x = 0.66 * W
    _b(ax, (x, cy - d / 2), (x + 0.20, cy + d / 2)); _b(ax, (x + 0.20, cy + d / 2), (x + 0.40, cy - d / 2))
    _carbonyl(ax, (x + 0.40, cy - d / 2), d=(0.0, 0.20))
    _b(ax, (x + 0.40, cy - d / 2), (x + 0.58, cy - d / 2 - 0.09))
    ax.text(x + 0.61, cy - d / 2 - 0.10, "OH", ha="left", va="center", fontsize=SCH_FS, color=SCH_COL)


def scheme_nhpi(ax, W):
    r, cy = 0.21, 0.60
    vx, vy = _ring(ax, 0.19 * W, cy, r, dbl=(1,))
    ax.text(vx[0], vy[0] + 0.045, "H", ha="center", va="bottom", fontsize=SCH_FS, color=SCH_COL)
    _arrow(ax, 0.42 * W, 0.53 * W, cy, "Cl$_4$NHPI")
    vx, vy = _ring(ax, 0.70 * W, cy, r, dbl=(1,))
    _carbonyl(ax, (vx[0], vy[0]), d=(0.0, 0.17))                 # conjugated to the C=C on edge 1: an enone


_Wfig, _Hfig = fig.get_size_inches()
for _ax, _fn, _cap in ([] if _INLINE else [(axSD, scheme_hofmann, "2-phenylacetamide $\\rightarrow$ carbamate"),
                       (axSE, scheme_act,     "alcohol $\\rightarrow$ carboxylic acid"),
                       (axSF, scheme_nhpi,    "valencene $\\rightarrow$ nootkatone")]):
    _bb = _ax.get_position(original=True)
    _W = (_bb.width * _Wfig) / (_bb.height * _Hfig)              # one data unit square -> rings stay round
    _ax.set_xlim(0, _W); _ax.set_ylim(0, 1); _ax.set_axis_off()
    _fn(_ax, _W)
    _ax.text(_W / 2, 0.015, _cap, ha="center", va="bottom", fontsize=SCH_FS - 0.3, color="0.45")
if not _INLINE:
    print("  panels d-f: reaction schemes drawn above each EC-prime panel (Jonas #1106)")


place_letters(fig, (axD, axE, axF), BV, letters="def")
place_letters(fig, (axG, axH), BV, letters="gh")
_w = (_xspan - 2 * FS.CELL_GAP) / 3
for _i, _s in enumerate("abc"):                                   # one letter per cell of the strip
    axA.text(_i * (_w + FS.CELL_GAP) - 0.012 * _w, 0.118 + 0.760 + 0.052, _s + ")", fontsize=10, fontweight=BV, va="bottom", ha="left")

# ════════ FIG6_INLINE: six compact schemes, one above each curve of (g) and (h) ════════
# Author, 2026-10-02.  The dedicated strip cost ~0.95 in of figure height for 0.17-0.31 in of ink
# (measured: a 0.475 in dead band above the structures and 0.275 in below), and it carried only the
# three MEDIATED chemistries -- the three catalyst rows of (h) had their chemistry drawn nowhere.
#
# Each scheme is the transformation its own curve solves, taken from that row's exemplar in
# data/reactions_50.csv.  Drawn at the strip's own scale (SCH_FS), never shrunk: the NHPI scheme
# already measures 0.60 x 0.31 in there, which is why a box of that size is the target here.
#
# PLACEMENT IS MEASURED, NOT TYPED.  The figure is rendered once without the schemes, the panel's
# own ink is read out of the RGBA buffer, and each scheme takes the clearest box that sits ABOVE
# its curve near that curve's label.  A box that would touch any existing ink is never offered, so
# a curve moving (a re-solve, a new rate constant) re-places the scheme instead of colliding with it.
# Author, 2026-10-02: "those molecules look terrible, generate proper structures using chemdraw".
# They were matplotlib stick figures at 5-6 pt. The six schemes are REAL ChemDraw structures now, in
# Figure 2's own document style, built by figs/make_fig6_schemes_cdxml.py and rendered through the same
# pipeline Figures 2 and 3 use; each is a transparent PNG at 1200 dpi, cropped to its own ink.
#
# They are placed as images rather than redrawn, which means two things worth stating. The scale is set
# by the BOND LENGTH the scheme prints at, not by a box height, so every scheme in both panels shows the
# same bond length whatever its own extent. And each is TINTED to its curve's colour at load time --
# ChemDraw draws in black, and the colour is what ties a scheme to the line it belongs to.
_SCHEME_DIR = os.path.join(HERE, "fig6_schemes")
_CD_BOND_PT = 14.40                  # cdxml_style.L, the bond length the schemes are drawn at
_CD_DPI = 1200.0                     # what make_fig6_schemes_cdxml.py renders them at


def _scheme_img(key, col):
    """The ChemDraw raster for `key`, tinted to `col`, with its drawn size in points."""
    import matplotlib.image as mpimg
    a = mpimg.imread(os.path.join(_SCHEME_DIR, key + ".png"))
    if a.shape[2] != 4:
        raise SystemExit("%s.png has no alpha; the schemes must be transparent" % key)
    # ChemDraw's PDF paints a white PAGE, so the file's own alpha is opaque almost everywhere: the
    # coverage has to come from how dark each pixel is, not from the alpha channel. (The first version
    # used the alpha and drew six solid colour blocks.)
    rgb = np.array(mpl.colors.to_rgb(col), dtype=float)
    out = np.empty(a.shape, dtype=float)
    out[:, :, :3] = rgb
    # ChemDraw's PDF paints a white PAGE, so the file's own alpha is opaque almost everywhere and the
    # coverage has to come from how far each pixel is from white -- normalised against this scheme's
    # OWN colour, because the ink is already coloured and a pale row would otherwise come out faint.
    lum0 = float(rgb.mean())
    cov = (1.0 - a[:, :, :3].mean(2)) / max(1e-6, 1.0 - lum0)
    out[:, :, 3] = np.clip(cov, 0.0, 1.0) * a[:, :, 3]
    return out, a.shape[1] / _CD_DPI * 72.0, a.shape[0] / _CD_DPI * 72.0


_MINI_G = [("Br-mediated Hofmann rearrangement", "hofmann", None),
           ("ACT-mediated alcohol oxidation (flow, hectogram)", "act", None),
           ("NHPI-mediated allylic C-H -> enone", "nhpi", None)]
# the Ni-XEC and Co-H curves nearly coincide (4.4 -> 24 and 4.8 -> 18 mA cm-2), so their
# schemes are split ACROSS the pair -- one above, one below -- rather than stacked in the
# single band beneath both of them.
_MINI_H = [("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "nixec", +1),
           ("Co-H alkene reduction (e-HAT)", "coh", -1),
           ("Co-catalyzed aza-Wacker cyclization", "aza", -1)]



if _INLINE:
    # ---- measure the panel's own ink, then set each scheme ALONG its own curve --------------------
    # Author, 2026-10-02: "allow yourself to angle the reactions so they run parallel to the lines
    # they match".  Each scheme is drawn into the PANEL's axes through an affine that scales local
    # inches, rotates to the curve's display-space slope at that point (the same slope _along uses
    # for the curve labels) and translates to the chosen centre -- so the drawing, its atom labels
    # and its arrow all run with the line.  Placement is MEASURED: the panel is rendered once
    # without the schemes, its ink read out of the RGBA buffer, and the ROTATED footprint of every
    # candidate position sampled against that ink, so a scheme can never be laid over a curve, a
    # label or a threshold rule.
    from matplotlib.transforms import Affine2D
    from matplotlib.patches import Rectangle
    for _ln in _THRESH_LINES:          # a scheme may sit over a threshold rule, so the rules are not ink
        _ln.set_visible(False)
    fig.canvas.draw()
    _buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(np.int16)
    for _ln in _THRESH_LINES:
        _ln.set_visible(True)
    _INK = (_buf.mean(2) < 245).astype(np.int32)
    _IH, _IW = _INK.shape
    _II = np.pad(np.cumsum(np.cumsum(_INK, 0), 1), ((1, 0), (1, 0)))

    def _ink_in(x0, y0, x1, y1):
        x0, y0 = max(0, int(x0)), max(0, int(y0)); x1, y1 = min(_IW, int(x1)), min(_IH, int(y1))
        if x1 <= x0 or y1 <= y0:
            return 1
        return int(_II[y1, x1] - _II[y0, x1] - _II[y1, x0] + _II[y0, x0])

    _BH_IN = 0.32                       # larger than the strip's own scale (author, 2026-10-02)
    _DPI = fig.dpi
    _PAD = int(0.020 * _DPI)            # clearance a drawn scheme keeps from any existing ink
    _SEP = int(0.05 * _DPI)             # two schemes that abut read as one drawing

    def _thr_py(ax):
        return [float(ax.transData.transform((ax.get_xlim()[0], t))[1]) for t in (25, 50)]

    def _place(ax, frames, minis, tag, bond, arts):
        """Hang each ChemDraw scheme in its own curve LABEL's frame, angled to that curve.

        The label placer already knows the right frame -- the curve's display-space slope and its
        normal -- so the scheme inherits it and alignment is by CONSTRUCTION rather than by search.
        What the search still decides is how far out, how far along, which side and at what scale, and
        it decides them on ONE cost so the trade is explicit: stay beside your own line first, then
        near your label, then be as large as the panel allows.  Collision is MEASURED against the
        panel's own ink, sampled under the rotated footprint; the threshold rules are excluded from
        that ink, because a scheme may sit over them (author, 2026-10-02).
        """
        bb = ax.get_window_extent()
        x_lo, x_hi, y_lo, y_hi = bb.x0 + 3, bb.x1 - 3, bb.y0 + 3, bb.y1 - 3
        taken = []
        for key, png, pref in minis:
            if key not in frames:
                raise SystemExit("FIG6_INLINE: %s has no label frame in panel %s" % (key, tag))
            rot, pc, (nx, ny), side = frames[key]
            _cv = [c for c in (_GCURVES + _HCURVES) if c[0] == key][0]
            col, xd, yd = _cv[1], _cv[2], _cv[3]
            _lx, _ly = np.log(xd[::-1]), yd[::-1]
            fy = lambda v: float(np.interp(np.log(v), _lx, _ly))

            def _chord(cx_px, half_px):
                """The angle of the curve's own CHORD across the span this scheme will occupy.

                The frame hands back the slope at the curve LABEL's x; a scheme slid along a curved
                line then sits where the slope is different, which is what made them read as not quite
                parallel. This measures the segment the scheme is actually beside."""
                inv = ax.transData.inverted()
                lo, hi = float(min(xd)), float(max(xd))
                xa = min(max(float(inv.transform((cx_px - half_px, y_lo))[0]), lo), hi)
                xb = min(max(float(inv.transform((cx_px + half_px, y_lo))[0]), lo), hi)
                if xa == xb:
                    return rot
                pa = ax.transData.transform((xa, fy(xa)))
                pb = ax.transData.transform((xb, fy(xb)))
                return float(np.degrees(np.arctan2(pb[1] - pa[1], pb[0] - pa[0])))

            img, w_pt, h_pt = _scheme_img(png, col)
            placed = False
            _st = np.arange(14.0, 620.0, 14.0)
            _SLIDES = np.concatenate([[0.0], np.repeat(_st, 2) * np.tile([1.0, -1.0], len(_st))])
            # the scale ladder is in PRINTED BOND LENGTH, so every scheme in the figure shows the
            # same bond whatever its own extent; Figure 3 prints its structures at about 9 pt.
            _cands = []
            if True:
                sc = bond / _CD_BOND_PT
                bw, bh = w_pt * sc * _DPI / 72, h_pt * sc * _DPI / 72
                for sgn in (side, -side):
                    _b0 = (_LBL_OFF + 0.5 * ANN + 0.5) * _DPI / 72 + bh / 2 if sgn == side \
                        else bh / 2 + 2.5 * _DPI / 72
                    if pref is not None:
                        _pen = 0.0 if sgn == pref else 4.0 * _DPI
                    else:
                        _pen = 0.0 if sgn == side else 0.10 * _DPI
                    for d in np.arange(0.0, 0.62, 0.025):
                        for sl in _SLIDES:
                            _cands.append((abs(sl) + 3.4 * d * _DPI + _pen,
                                           sgn, _b0 + d * _DPI, float(sl), bw, bh))
            _cands.sort()
            _rej = {"off": 0, "ink": 0, "near": 0}
            for _cost, sgn, out, slide, bw, bh in _cands:
                # the footprint is the scheme's own extent; the raster is already cropped to its ink
                PTS = np.column_stack([np.repeat(np.linspace(-0.5, 0.5, 17), 5),
                                       np.tile(np.linspace(-0.5, 0.5, 5), 17)])
                ux, uy = np.cos(np.radians(rot)), np.sin(np.radians(rot))
                cx = pc[0] + sgn * out * nx + slide * ux
                cy = pc[1] + sgn * out * ny + slide * uy
                rot_d = _chord(cx, bw / 2 * abs(np.cos(np.radians(rot))))   # parallel to THIS segment
                R = Affine2D().scale(bw, bh).rotate_deg(rot_d)
                q = R.transform(PTS) + np.array([cx, cy])
                if (q[:, 0].min() < x_lo or q[:, 0].max() > x_hi
                        or q[:, 1].min() < y_lo or q[:, 1].max() > y_hi):
                    _rej["off"] += 1
                    continue
                if any(_ink_in(px - _PAD, _IH - py - _PAD, px + _PAD, _IH - py + _PAD)
                       for px, py in zip(q[:, 0], q[:, 1])):
                    _rej["ink"] += 1
                    continue
                ax0, ax1 = q[:, 0].min(), q[:, 0].max()
                ay0, ay1 = q[:, 1].min(), q[:, 1].max()
                if any(not (ax1 + _SEP < t[0] or t[1] < ax0 - _SEP or
                            ay1 + _SEP < t[2] or t[3] < ay0 - _SEP) for t in taken):
                    _rej["near"] += 1
                    continue
                taken.append((ax0, ax1, ay0, ay1))
                _PLACED.append((png, cx, cy, bw, bh, rot_d))
                T = Affine2D().scale(bw, bh).rotate_deg(rot_d).translate(cx, cy)
                # (2) a scheme laid over a threshold rule gets a white backing, so the rule does not
                # run through the structure (author, 2026-10-02). Only where it actually crosses one.
                if any(ay0 < ty < ay1 for ty in _thr_py(ax)):
                    arts.append(ax.add_patch(Rectangle((-0.5, -0.5), 1.0, 1.0, transform=T, zorder=8,
                                                       facecolor="white", edgecolor="none", clip_on=False)))
                arts.append(ax.imshow(img, extent=(-0.5, 0.5, -0.5, 0.5), transform=T, zorder=9,
                                      interpolation="antialiased", aspect="auto", clip_on=False))
                print("    (%s) %-42s %-5s the line at %+5.1f deg, bond %.1f pt (%.2f x %.2f in), "
                      "%.2f in out, slid %+.2f in"
                      % (tag, key[:42], "above" if sgn > 0 else "below", rot_d, bond,
                         bw / _DPI, bh / _DPI, out / _DPI, slide / _DPI))
                placed = True
                break
            if not placed:
                return False
        return True

    _PLACED = []
    print("  FIG6_INLINE: scheme strip dropped; six schemes set along the curves of (g) and (h)")
    for _bond in np.arange(8.0, 3.4, -0.2):
        _arts = []
        if _place(axG, _GFRAME, _MINI_G, "g", _bond, _arts) and _place(axH, _HFRAME, _MINI_H, "h", _bond, _arts):
            print("    all six placed at a bond length of %.1f pt" % _bond)
            break
        for _a in _arts:
            _a.remove()
        _PLACED.clear()
    else:
        raise SystemExit("FIG6_INLINE: the six schemes do not fit at any common bond length down to 3.5 pt")

_SFX = "_normalized_gh" if _NORM else ("_inline" if _INLINE else "")            # the variant never overwrites the shipped render
fig.savefig(os.path.join(OUT, f"combined_figure_grounded{_SFX}.png"), dpi=600, facecolor="white")
fig.savefig(os.path.join(OUT, f"combined_figure_grounded{_SFX}.svg"), facecolor="white")
# a PDF too, for hand placement in Illustrator: the plot is vector and each scheme is a discrete
# VECTOR object (ChemDraw's own paths and text) that can be selected, moved and edited
# (author, 2026-10-02).  The only rasters in the file are the three gradient films of panels (a-c),
# which the shipped figure carries as well.
_PDF = os.path.join(OUT, f"combined_figure_grounded{_SFX}.pdf")
fig.savefig(_PDF, facecolor="white")
if _INLINE:
    # matplotlib's PDF backend SILENTLY DROPS an imshow drawn through a custom rotation transform --
    # the first PDF had the plot and no schemes at all, and nothing warned. So the schemes go in as
    # ChemDraw's own VECTOR crops, stamped at the placements the layout chose: editable structures in
    # Illustrator rather than images, and no raster anywhere in the figure.
    import fitz
    _doc = fitz.open(_PDF)
    _pg = _doc[0]
    _k = 72.0 / fig.dpi
    for _key, _cx, _cy, _bw, _bh, _rot in _PLACED:
        _src = fitz.open(os.path.join(_SCHEME_DIR, _key + ".pdf"))
        w, h = _bw * _k, _bh * _k
        x, y = _cx * _k, _pg.rect.height - _cy * _k          # PDF y runs down the page
        # show_pdf_page spins the source about the rect it is GIVEN and then fits the ROTATED page
        # inside it with keep_proportion.  So the rect is the AXIS-ALIGNED BOUNDING BOX of the target
        # w x h box turned by rot: the fit factor is then exactly w/page_width, which is the scale
        # matplotlib drew the PNG at, and the vector copy lands at the same size and place.
        # MEASURED, not reasoned: a rect of w x h comes out shrunk by the fit factor, and inflating
        # BOTH axes by its inverse overshoots on the non-binding axis (the first two attempts).
        th = np.radians(_rot)
        rw = (abs(w * np.cos(th)) + abs(h * np.sin(th))) / 2
        rh = (abs(w * np.sin(th)) + abs(h * np.cos(th))) / 2
        # MEASURED: PyMuPDF's rotate runs the same way as matplotlib's rotate_deg, so the sign
        # is NOT flipped for the page's y-down convention -- negating it tilted every scheme
        # the opposite way to the curve it labels.
        _pg.show_pdf_page(fitz.Rect(x - rw, y - rh, x + rw, y + rh), _src, 0, rotate=_rot)
    _doc.saveIncr()
    print(f"  PDF: {len(_PLACED)} schemes stamped as vector into {os.path.basename(_PDF)}")
    if os.environ.get("FIG6_DUMP_PLACED"):
        import json
        json.dump([[k, float(a), float(b), float(c), float(d), float(e)]
                   for k, a, b, c, d, e in _PLACED],
                  open(os.environ["FIG6_DUMP_PLACED"], "w"))
print(f"saved -> {OUT}/combined_figure_grounded{_SFX}.{{png,svg}} | font {FONT}")
