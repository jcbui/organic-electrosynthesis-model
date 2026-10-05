"""FigH — EC' mediator amplification vs the homogeneous rate constant k.

  a) i_lim(k) for the generic EC' base case, against the three analytic references
     (commuting bound, Saveant sqrt(k) law, total-catalysis / substrate cap).
  b) mediator and substrate profiles at 0.9 i_lim for k = 1, 100, 1000 M^-1 s^-1,
     showing the reaction layer collapsing toward the electrode as k grows.

RECONSTRUCTED GENERATOR (2026-08). PROVENANCE NOTE — READ BEFORE EDITING.
------------------------------------------------------------------------
`figs/sec4_figH_ecprime.{png,svg}` existed in the repo (rendered 2026-07-11) with
NO generator anywhere in the tree (grep "figH" returned zero hits in any .py/.jl/.js),
yet SI Sec. S5.4 cites it by name ("...the exact total-catalysis limit is reported
instead (Fig. H, open squares)"). The figure-provenance audit flagged it as the single
most unauditable artifact in the set.

Decision: RECONSTRUCT rather than delete. Evidence for reconstruction:
  * every mark in the archived figure traces to a file that is still in the repo —
    panel a to julia/npp_ecprime_sweep.csv (the seven k <= 1e3 markers reproduce the
    `ilim_mAcm2` column exactly: 1.188 / 1.449 / 3.241 / 9.481 / 23.98 / 33.26 / 41.86),
    panel b to julia/npp_ecprime_profiles.csv (c_ox(0) = 0.857 / 0.827 / 0.708 and
    c_S(0) = 0.961 / 0.574 / 0.237 at k = 1 / 100 / 1000);
  * the three analytic references are closed forms in julia/run_ecprime.jl and SI
    Eqs. S13-S15, and recompute here to the printed precision;
  * the SI sentence that cites it is CORRECT — the archived figure really does draw
    the analytic substitutions as open squares inside a labelled moving-front band.
    Deleting the figure would delete the only rendering in the set that carries that
    flag, and would force an edit to SI prose that is not wrong.
So the honest repair is to restore the source of truth, not to remove the artifact.
The archived orphan render is preserved at _archive/figs/sec4_figH_ecprime.{png,svg}.

Two deliberate departures from the archived render, both in the direction of MORE
disclosure (the archived image is superseded, not reproduced pixel-for-pixel):
  1. The moving-front band now starts at the k where x_k is exactly 1 um, computed at
     runtime (k = D_med/(x_k^2 C_S) = 1200 M^-1 s^-1), instead of the hardcoded
     k = 2000 back-solved into the archived SVG. The band's own label says
     "x_k < 1 um", so the band edge must be that boundary and nothing else.
  2. Solver points whose ramp ended on a Newton wall rather than on species collapse
     (`limiter == "newton-wall (no collapse)"`) are STRICT LOWER BOUNDS by SI Sec. S5.5's
     own definition. The archived figure drew them as ordinary filled circles,
     indistinguishable from converged plateaus. They are now drawn as up-triangles and
     named in the legend. Four of the seven plotted points (k = 1e-2, 1e-1, 1e2, 3e2)
     are affected; the shape of the curve is unchanged.

PROVENANCE OF THE INPUTS (flagged, not silently propagated). The base case constants
C_med = 20 mM, C_S = 0.5 M, D_med = 6e-10 m^2/s, D_S = 1e-9 m^2/s, delta = 100 um are
julia/run_ecprime.jl declarations and have NO row in data/parameters_provenance.csv.
They are read here FROM that file's header block via the constants below and are
presented on-figure as a stated generic base case, not as a measured system; the
figure's claims are regime statements (which of three analytic laws binds, and where),
all of which are invariant to the absolute scale of these constants. This is a state-C
declaration and is recorded as such in the SI provenance register.
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SEC4 = os.path.dirname(HERE)
for cand in (SEC4, HERE, os.path.expanduser("~/Documents/CO2R-Bulk-Scale-Julia-Model")):
    if os.path.exists(os.path.join(cand, "customplot.py")):
        sys.path.insert(0, cand); break
os.chdir(SEC4)
from customplot import gengrid, rainbow_2
from matplotlib.lines import Line2D

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]

# ── base case: julia/run_ecprime.jl lines 9-14 (verbatim) ────────────────────
F      = 96485.33
delta  = 100e-6      # m
C_med  = 20.0        # mol m^-3
C_S    = 500.0       # mol m^-3
D_med  = 6.0e-10     # m^2 s^-1
D_S    = 1.0e-9      # m^2 s^-1

i_sh  = 0.1*F*D_med*C_med/delta      # Eq. S13, mA cm^-2
i_cap = 0.1*F*D_S  *C_S  /delta      # Eq. S15, mA cm^-2

sw = pd.read_csv("julia/npp_ecprime_sweep.csv")
pr = pd.read_csv("julia/npp_ecprime_profiles.csv")

# The moving-front boundary IS x_k = 1 um, solved for k (x_k = sqrt(D_ox/(k C_S)), Eq. S12).
XK_CUT_UM = 1.0
K_CUT = 1000.0 * D_med / ((XK_CUT_UM*1e-6)**2 * C_S)      # -> 1200 M^-1 s^-1
sub  = sw[sw.xk_um <  XK_CUT_UM]      # analytic substitution (k = 3e3, 1e4, 1e5)
sol  = sw[sw.xk_um >= XK_CUT_UM]      # solver-reported  (k = 1e-2 ... 1e3)
conv = sol[sol.limiter != "newton-wall (no collapse)"]
wall = sol[sol.limiter == "newton-wall (no collapse)"]
amp  = sol.ilim_mAcm2.max()/i_sh

fig, axs, _ = gengrid(1, 2, size_inches=(6.8, 3.0), ticklabel_size=7.5, label_pos=-0.10)
a, b = axs

# ═══ a) i_lim vs k ════════════════════════════════════════════════════════════
a.axvspan(K_CUT, 2.5e5, color="0.94", zorder=0)
kk = np.logspace(-2.6, 5.6, 200)
a.axhline(i_sh,  color="0.5",  ls="--", lw=0.9)
a.axhline(i_cap, color="0.15", lw=1.2)
a.plot(kk, 0.1*F*C_med*np.sqrt(D_med*(kk/1000)*C_S), color="0.5", ls=":", lw=1.0)

a.plot(sol.k_M, sol.ilim_mAcm2, "-", color=BLUE, lw=1.4, zorder=3)
a.plot(conv.k_M, conv.ilim_mAcm2, "o", color=BLUE, ms=5.0, mec="none", zorder=5)
a.plot(wall.k_M, wall.ilim_mAcm2, "^", color=BLUE, ms=5.4, mfc="white", mew=1.2, mec=BLUE, zorder=5)
a.plot(sub.k_M, [i_cap]*len(sub), "s", mfc="white", mec="0.15", mew=1.1, ms=5.0, zorder=5)

a.text(1.5e-2, i_sh*0.70, "commuting bound  $FD_{med}C_{med}/\\delta$", fontsize=5.6, color="0.45")
a.text(1.5e-2, i_cap*0.60, "total-catalysis cap  $FD_SC_S/\\delta$  =  substrate-carried ceiling",
       fontsize=5.6, color="0.15")
a.text(2.2, 11.5, "Savéant  $FC_{med}\\sqrt{D_{med}kC_S}$", fontsize=5.8, color="0.5", rotation=27)
a.text(1.5e-2, 190, "20 mM mediator, 0.5 M substrate, $\\delta$ = 100 $\\mu$m", fontsize=5.8, color="0.15")
a.text(60, 2.6, f"$\\times${amp:.0f} over the\ncommuting bound", fontsize=5.8, color=BLUE)
a.annotate("", xy=(9e2, 34), xytext=(2.2e2, 11),
           arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9))
a.text(1.6e4, 130, "moving-front regime ($x_k$ < 1 $\\mu$m):\nanalytic cap applies",
       fontsize=5.8, color="0.45", ha="center", va="center")

leg = [Line2D([0],[0], ls="", marker="o", ms=4.2, color=BLUE,
              label="solver plateau (converged)"),
       Line2D([0],[0], ls="", marker="^", ms=4.6, mfc="white", mec=BLUE, mew=1.1, color=BLUE,
              label="solver ramp ended on a Newton wall:\nstrict lower bound (SI §S5.5)"),
       Line2D([0],[0], ls="", marker="s", ms=4.2, mfc="white", mec="0.15", mew=1.0, color="0.15",
              label="ANALYTIC substitution, not a solve:\ntotal-catalysis cap (SI §S5.4)")]
a.legend(handles=leg, fontsize=4.6, loc="lower right", handletextpad=0.35,
         borderaxespad=0.3, labelspacing=0.45, frameon=True, framealpha=0.9,
         facecolor="white", edgecolor="none")

a.set_xscale("log"); a.set_yscale("log")
a.set_xlim(1e-2, 2.5e5); a.set_ylim(0.5, 300)
a.set_xlabel("Homogeneous rate constant $k$ (M$^{-1}$ s$^{-1}$)", fontsize=8)
a.set_ylabel("$i_{lim}$ (mA cm$^{-2}$)", fontsize=8)

# ═══ b) reaction-layer profiles at 0.9 i_lim ══════════════════════════════════
for k, cc in [(1.0, LBLUE), (100.0, ORANGE), (1000.0, RED)]:
    g = pr[pr.k_M == k]
    b.plot(g.x_um, g.c_ox_norm, color=cc, lw=1.6, label=f"k = {k:.0f}")
    b.plot(g.x_um, g.c_S_norm,  color=cc, lw=1.4, ls="--")
b.text(14.6, 0.62, "reaction layer collapses toward\nthe electrode as $k$ grows",
       fontsize=5.8, color="0.35", ha="right", va="center")
b.legend(fontsize=5.8, frameon=False, loc="upper center", ncol=3,
         handletextpad=0.4, columnspacing=1.4, borderaxespad=0.15)
b.set_xlim(0, 15); b.set_ylim(0, 1.30); b.set_yticks([0.0, 0.5, 1.0])
b.set_xlabel("Distance from electrode ($\\mu$m)", fontsize=8)
b.set_ylabel("c$_{ox}$/C$_{med}$ (—),  c$_S$/C$_S$ (- -)", fontsize=8)

fig.tight_layout()
fig.savefig("figs/sec4_figH_ecprime.svg")
fig.savefig("figs/sec4_figH_ecprime.png", dpi=600)
print(f"figH written | i_sh = {i_sh:.4f}  i_cap = {i_cap:.4f} mA/cm2 | "
      f"moving-front band starts at k = {K_CUT:.0f} (x_k = 1 um) | "
      f"max amplification x{amp:.2f} at k = {sol.k_M[sol.ilim_mAcm2.idxmax()]:.0f}")
print("  converged      :", conv.k_M.tolist())
print("  lower bounds   :", wall.k_M.tolist())
print("  analytic subst.:", sub.k_M.tolist(), "-> i_cap; solver lower bounds there were",
      [round(v,2) for v in sub.ilim_mAcm2.tolist()])
