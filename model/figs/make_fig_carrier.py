"""Redesigned carrier-physics figure (replaces the old 4B-ac payoff map).
2x2: (a) carrier taxonomy schematic
     (b) mediated (EC') concentration profiles — fast mediator plateaus
     (c) molecular-catalyst concentration profiles — dilute carrier, reactor-responsive
     (d) i_lim vs delta for all three carriers, in real units — the reactor-design payoff

Provenance remediation, 2026-08-02 (figure-provenance-audit findings 3, 4, 5, 6):
  * F5  panels c and d contain no invented carrier constants: both use the per-row nFDC of
        the 11 catalyst rows of reactions_50.csv (via julia/reactions_table.jl).
  * F3  the "median substrate" line is the substrate-only median, computed at runtime.
  * F4  all six archetypes appear at their computed median delta.
  * F6  all 8 EC' solves are plotted from julia/mediated_ec_matrix.csv, the delta-insensitive
        ones identified by their fitted log-log slope rather than by eye.

Redesign, 2026-09-07 (author instruction: the captions carry the text). Titles and every
annotation are gone; the schematic is the shared flat one (figs/figstyle.carrier_schematic).
Every number that used to be on the figure is printed to stdout.
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, sys, os
from matplotlib.lines import Line2D

# ── portable paths: resolve everything relative to this file, not /home/claude/rce ──
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.chdir(ROOT)          # customplot reads the Berkeley swatch workbook from cwd at import
from customplot import gengrid, rainbow_2
import model_medians as MM
import figstyle as FS

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]
F=96485.33
pr=pd.read_csv(os.path.join(ROOT,"julia/npp_ecprime_profiles.csv"))

# ── population statistics, all computed at runtime from the 50-reaction table ──
K_SUB = MM.K_stats("substrate")
K_CAT = MM.K_stats("catalyst")
C_SUB = MM.guide_constant("substrate")
MED   = MM.mediated_delta_slopes()
FLAT  = {k: v for k, v in MED.items() if v["slope"] > -0.5}   # delta-insensitive subset
STEEP = {k: v for k, v in MED.items() if v["slope"] <= -0.5}

fig, axs, _ = gengrid(2,2, size_inches=(7.2,6.0), ticklabel_size=7, genlabels=False)
a,b = axs[0]; c,d = axs[1]

# ═══ a) carrier taxonomy schematic ═════════════════════════════════════════════
FS.carrier_schematic(a, blue=BLUE, orange=ORANGE, red=RED)

# ═══ b) mediated (EC') profiles — reactor can't reach the reaction layer ════════
cols={1.0:LBLUE,1000.0:RED}
handles=[]
for k,g in pr[pr.k_M.isin([1.0,1000.0])].groupby("k_M"):
    h,=b.plot(g.x_um,g.c_ox_norm,color=cols[k],lw=1.6,label=("$k$ = 1 M$^{-1}$ s$^{-1}$" if k==1.0 else "$k$ = 10$^3$ M$^{-1}$ s$^{-1}$"))
    b.plot(g.x_um,g.c_S_norm,color=cols[k],lw=1.0,ls="--"); handles.append(h)
handles += [Line2D([0],[0],color="0.4",lw=1.4,label="mediator"), Line2D([0],[0],color="0.4",lw=1.0,ls="--",label="substrate")]
FS.legend(b, handles=handles, loc="center right", fontsize=5.8, bbox_to_anchor=(0.98, 0.47))
b.set_xlim(0,15); b.set_ylim(0,1.05)
b.set_xlabel("distance from electrode (µm)",fontsize=7.5); b.set_ylabel("c / $c_{bulk}$",fontsize=7.5)

# ═══ c) molecular-catalyst profiles — dilute carrier, but reactor-responsive ════
D_CAT_ST  = MM.delta_median("stirred", "catalyst")
D_CAT_RCE = MM.delta_median("rce",     "catalyst")
I_CAT_ST  = MM.ilim_median("stirred",  "catalyst")
I_CAT_RCE = MM.ilim_median("rce",      "catalyst")
CATROWS   = MM.pop("catalyst")
_imax     = CATROWS[["i_"+k for k in MM.ARCHETYPES]].max(axis=1)
N_UNDER25 = int((_imax < 25).sum()); N_CAT = len(CATROWS)
I_CAT_MAX = float(_imax.max())
C_AT_MAX  = float(CATROWS.C.iloc[int(np.argmax(_imax.values))])
for dl,il,col,tag in [(D_CAT_RCE,I_CAT_RCE,GREEN,"RCE"),(D_CAT_ST,I_CAT_ST,RED,"stirred")]:
    c.plot([0,dl],[0,1.0],color=col,lw=1.9,label=tag)   # fully developed (i = i_lim): 0 at wall -> 1 at delta
print(f"catalyst: stirred delta {D_CAT_ST:.1f} um median ilim {I_CAT_ST:.2f}; RCE delta {D_CAT_RCE:.1f} um median ilim {I_CAT_RCE:.2f} "
      f"({D_CAT_ST/D_CAT_RCE:.1f}x thinner -> {I_CAT_RCE/I_CAT_ST:.1f}x); {N_UNDER25} of {N_CAT} under 25 everywhere; max {I_CAT_MAX:.1f} at {C_AT_MAX:.0f} mM")
FS.legend(c, loc="lower right", fontsize=5.8)
c.set_xlim(0,120); c.set_ylim(0,1.08)
c.set_xlabel("distance from electrode (µm)",fontsize=7.5); c.set_ylabel("$c_{cat}$ / $C_{cat}$",fontsize=7.5)

# ═══ d) i_lim vs delta for all three carriers (real units) ═════════════════════
dd=np.logspace(np.log10(0.5),np.log10(500),200)
d.fill_between(dd, K_SUB["lo"]/dd, K_SUB["hi"]/dd, color=BLUE, alpha=0.20, lw=0, zorder=4)
d.plot(dd, C_SUB/dd, color=BLUE, lw=2.0, zorder=6)
d.fill_between(dd, K_CAT["lo"]/dd, K_CAT["hi"]/dd, color=RED, alpha=0.30, lw=0, zorder=3)
d.plot(dd, K_CAT["median"]/dd, color=RED, lw=1.4, zorder=5)
for nm,v in STEEP.items():
    o=np.argsort(v["delta"]); d.plot(v["delta"][o],v["i_ec"][o],color=ORANGE,lw=0.8,alpha=0.45,zorder=2)
for nm,v in FLAT.items():
    o=np.argsort(v["delta"]); d.plot(v["delta"][o],v["i_ec"][o],color=ORANGE,lw=1.8,zorder=6,marker="o",ms=2.2,mec="none")
# ── the eleven catalyst rows at the top of the DECLARED rate-constant band (G-CATK, SI S5.7) ──
# The red band is the published catalyst treatment (2026-09-11: seven rows at a SOURCED rate constant,
# four at the k = 0 floor, docs/CATALYST_RATE_CONSTANTS_20260911.md); the open markers are the same rows
# re-solved at the top of the declared band, so the band cannot be read as the class ceiling.
_ck = pd.read_csv(os.path.join(ROOT, "julia", "catalyst_ec_sweep.csv"))
_ck_kmax = _ck.k_M.max(); _ckt = _ck[_ck.k_M == _ck_kmax]
d.scatter(_ckt.delta_um, _ckt.i_ec_mAcm2, s=9, facecolors="none", edgecolors=RED, lw=0.7, zorder=6)
print(f"catalyst at k = {_ck_kmax:g} M-1 s-1 (G-CATK): {int((_ckt.groupby('reaction').i_ec_mAcm2.max() >= 25).sum())}/{_ckt.reaction.nunique()} "
      f"clear 25 in some archetype; max amplification x{_ckt.amplification.max():.1f}")
for thr,lab in ((25,"25"),(50,"50")):
    d.axhline(thr,color="0.35",ls=":",lw=0.9,zorder=1)
    d.text(0.015,thr*1.08,lab,transform=d.get_yaxis_transform(),fontsize=5.6,color="0.35",va="bottom",ha="left")
_fs = sorted(v["slope"] for v in FLAT.values()); _ss = sorted(v["slope"] for v in STEEP.values())
print(f"map: substrate K p10/median/p90 {K_SUB['lo']:.0f}/{K_SUB['median']:.0f}/{K_SUB['hi']:.0f} (n={K_SUB['n']}); catalyst {K_CAT['lo']:.1f}/{K_CAT['median']:.1f}/{K_CAT['hi']:.1f} (n={K_CAT['n']}); "
      f"mediated {len(FLAT)} flat (slopes {_fs[0]:+.2f}..{_fs[-1]:+.2f}), {len(STEEP)} steep ({_ss[0]:+.2f}..{_ss[-1]:+.2f}); "
      f"{len(MM.MEDIATED)-sum(v['n'] for v in MED.values())} of {len(MM.MEDIATED)} rows dropped")
FS.legend(d, handles=[Line2D([0],[0],color=BLUE,lw=2.0,label=f"direct substrate ({K_SUB['n']})"),
                      Line2D([0],[0],color=RED,lw=1.4,label=f"molecular catalyst ({K_CAT['n']}), published k"),
                      Line2D([0],[0],ls="none",marker="o",mfc="none",mec=RED,ms=3.2,mew=0.7,label="catalyst, k = 10$^{4}$"),
                      Line2D([0],[0],color=ORANGE,lw=1.8,marker="o",ms=2.2,mec="none",label="mediated, $\\delta$-insensitive"),
                      Line2D([0],[0],color=ORANGE,lw=0.8,alpha=0.6,label="mediated, $\\delta$-dependent")],
          loc="lower right", fontsize=5.6, frameon=True, framealpha=0.92, facecolor="white", edgecolor="none")
d.set_xscale("log"); d.set_yscale("log"); d.set_xlim(500,0.5); d.set_ylim(0.3,1e4)
d.set_xlabel("$\\delta$ (µm)",fontsize=7.5)
d.set_ylabel("$i_{lim}$ (mA cm$^{-2}$)",fontsize=7.5)
d.set_xticks([500,100,10,1]); d.set_xticklabels(["500","100","10","1"])

for ax,l in [(a,"a)"),(b,"b)"),(c,"c)"),(d,"d)")]:
    FS.panel_letter(ax,l, x=-0.16, y=1.03)
fig.tight_layout(h_pad=2.0, w_pad=2.2)
fig.savefig("figs/sec4_Fig_carrier.svg"); fig.savefig("figs/sec4_Fig_carrier.png",dpi=600)
print("Fig carrier written")
