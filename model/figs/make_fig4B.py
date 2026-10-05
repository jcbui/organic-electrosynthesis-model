"""Figure 4B, split into two figures (V6):
  Fig 4B-ac — carrier physics and the design map:
     a) carrier taxonomy schematic with ceiling formulas
     b) mediated (EC'): the reaction layer no stirrer can reach (NPP solver)
     c) nondimensional architecture payoff map
  Fig 4B-def — the engineering penalty:
     d) cell voltage / ohmic stack
     e) boil-off: steady-state cell temperature, passively cooled beaker
     f) absolute boil-off ceiling vs reactor architecture
Panel letters d-f are retained across the split so existing cross-references
(e.g. "Fig. 4B-c" in the SI) remain valid until final MS renumbering.

2026-08 REMEDIATION (findings 8 and 10 of docs/FIGURE_PROVENANCE_AUDIT.md).

(8) Panel c's archetype bands were hardcoded at x-hat = (2.5,3.5) / (5,15) /
    (30,100). Two of the three are contradicted by the model's own correlations
    (flow is 3.13-7.90; nothing in the 50-reaction set passes x-hat = 35.5).
    They are now computed at runtime by figs/archetype_bands.py from
    julia/correlations.jl + julia/reactions_table.jl. The legend title also still
    read "mu=0.041" although the constant had already been corrected to 0.0205 —
    a live on-figure dependency on the superseded value. It is now formatted from
    the variable and cannot go stale again.

(10) Panels d/e/f carried a SECOND, contradictory thermal and ohmic model:
     unregistered electrolytes (0.1 M Bu4NPF6/THF kappa = 0.06 S/m, 0.1 M
     Bu4NBF4/DMF 0.35, MeCN 0.90, 1 M KOH aq 20.0), a 5 mm beaker gap, and
     ASSUMED cooling coefficients (0.020 "still air", 0.18 "stirred bath", 0.30
     "PEM-class plates"). Fig. K meanwhile used registry electrolytes, the
     canonical 2 cm beaker gap, and a U' DERIVED from vessel geometry
     (0.01438 W/cm2 K passive, ~30% BELOW the 0.020 that was assumed here). All
     three panels now import figs/thermal_model.py, the single source of truth
     extracted from make_figK.py, so the main-text figure and the SI figure state
     the same physics. Panels e and f are the main-text condensation of Fig. K
     panels (a) and (b) and are generated from the identical model.
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, sys, os
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
SEC4 = ROOT = os.path.dirname(HERE)
# Portable paths: resolve everything relative to this file, and chdir to the repo root before
# importing customplot, which reads "Color Swatches from UC Berkeley.xlsx" from the CURRENT WORKING
# DIRECTORY at import time. Without the chdir this script only runs from the repo root; with it,
# it runs from anywhere, matching make_figs_sec34.py / make_fig4A.py / make_figFG.py /
# make_fig_carrier.py / make_figK_MSlayout.py. Every read and write below is already an absolute
# path built from HERE or SEC4 (and archetype_bands.py resolves its own inputs the same way), so
# the chdir changes NO number and NO output location.
for cand in (SEC4, HERE, os.path.expanduser("~/Documents/CO2R-Bulk-Scale-Julia-Model")):
    if os.path.exists(os.path.join(cand, "customplot.py")):
        sys.path.insert(0, cand); os.chdir(cand); break
else:
    raise SystemExit("customplot.py not found; cannot run.")
sys.path.insert(0, HERE)
from customplot import gengrid, rainbow_2
from archetype_bands import xhat_bands, xhat_ceiling
from thermal_model import (SOLVENTS, REACTORS, TAMB, U_passive, q_Wcm2, i_boil,
                           E_cell, T_ss, BEAKER, U_BEAKER)

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]
F=96485.33; BARRIER=50.0
SCOL={"THF":RED,"MeCN":LBLUE,"DMF":ORANGE,"aq. NaOH":BLUE}   # same as Fig. K
pr=pd.read_csv(os.path.join(SEC4,"julia","npp_ecprime_profiles.csv"))

def plabel(ax, s):
    ax.text(-0.20, 1.12, s, transform=ax.transAxes, fontsize=10,
            fontweight="regular", va="top", ha="right")

# ═════════════════════════════ FIGURE 4B-ac (1 x 3) ════════════════════════════
fig1, axs1, _ = gengrid(3, 1, size_inches=(7.2, 2.6), ticklabel_size=6.5, genlabels=False)
a, b, c = np.ravel(axs1)

# ─── a) carrier taxonomy with ceiling formulas (schematic) ─────────────────────
a.set_xlim(0,10); a.set_ylim(0,10); a.axis("off")
def electrode(x0):
    a.add_patch(Rectangle((x0,1.6),0.28,6.6,fc="0.35",ec="none"))
for i,(ttl,form) in enumerate([("direct\n(substrate)","$i_{lim}\\propto n\\,C_{sub}D/\\delta$"),
                               ("mediated\n(EC$'$)","$i_{lim}\\propto C_{med}\\sqrt{kC_{sub}D}$\n$\\rightarrow$ substrate cap"),
                               ("molecular\ncatalyst","$i_{lim}\\propto n\\,C_{cat}D_{cat}/\\delta$\n$C_{cat}$ = 3–30 mM")]):
    x0=0.5+i*3.2; electrode(x0)
    a.text(x0+1.45,9.0,ttl,ha="center",fontsize=4.8,color="0.15")
    a.text(x0+1.45,0.35,form,ha="center",fontsize=4.4,color=BLUE)
a.add_patch(FancyArrowPatch((2.7,5.9),(1.0,5.9),arrowstyle="-|>",mutation_scale=8,color=GREEN,lw=1.4))
a.text(2.15,6.25,"S",fontsize=6.5,color=GREEN)
a.add_patch(FancyArrowPatch((1.0,3.6),(2.7,3.6),arrowstyle="-|>",mutation_scale=8,color="0.5",lw=1.1))
a.text(2.15,2.9,"P",fontsize=6.5,color="0.5")
x0=3.7
a.add_patch(Rectangle((x0+0.28,1.6),0.9,6.6,fc=ORANGE,alpha=0.18,ec="none"))
a.text(x0+0.73,7.55,"$x_k$",fontsize=5.5,color=ORANGE,ha="center")
a.add_patch(FancyArrowPatch((x0+0.35,4.4),(x0+1.5,5.5),arrowstyle="-|>",mutation_scale=7,
            connectionstyle="arc3,rad=-0.55",color=ORANGE,lw=1.3))
a.add_patch(FancyArrowPatch((x0+1.5,4.6),(x0+0.35,3.6),arrowstyle="-|>",mutation_scale=7,
            connectionstyle="arc3,rad=-0.55",color=ORANGE,lw=1.3))
a.text(x0+1.05,5.9,"Med$_{ox}$",fontsize=5.2,color=ORANGE)
a.text(x0+1.05,2.9,"Med$_{red}$",fontsize=5.2,color=ORANGE)
a.add_patch(FancyArrowPatch((x0+2.75,5.05),(x0+1.75,5.05),arrowstyle="-|>",mutation_scale=7,color=GREEN,lw=1.2))
a.text(x0+2.35,5.4,"S",fontsize=6,color=GREEN)
x0=6.9
a.add_patch(FancyArrowPatch((x0+0.35,4.6),(x0+1.25,5.4),arrowstyle="-|>",mutation_scale=7,
            connectionstyle="arc3,rad=-0.6",color=RED,lw=1.3))
a.add_patch(FancyArrowPatch((x0+1.25,4.4),(x0+0.35,3.7),arrowstyle="-|>",mutation_scale=7,
            connectionstyle="arc3,rad=-0.6",color=RED,lw=1.3))
a.text(x0+0.85,5.75,"M$^{n}$/M$^{n-2}$",fontsize=5.0,color=RED)
for (dx,dy) in [(1.9,6.6),(2.4,5.0),(2.0,3.0),(2.6,6.0),(2.7,3.8)]:
    a.add_patch(Circle((x0+dx,dy),0.09,fc=RED,ec="none",alpha=0.7))
a.text(x0+2.3,2.2,"dilute",fontsize=5.0,color=RED,ha="center")

# ─── b) mediated: the layer no stirrer can reach ───────────────────────────────
cols={1.0:LBLUE,1000.0:RED}
for k,g in pr[pr.k_M.isin([1.0,1000.0])].groupby("k_M"):
    b.plot(g.x_um,g.c_ox_norm,color=cols[k],lw=1.5)
    b.plot(g.x_um,g.c_S_norm,color=cols[k],lw=1.0,ls="--")
b.text(11.6,0.63,"$k$ = 1 M$^{-1}$s$^{-1}$",fontsize=4.8,color=LBLUE)
b.text(1.2,0.035,"$k$ = 10$^3$ M$^{-1}$s$^{-1}$",fontsize=4.8,color=RED)
b.annotate("fast mediator: activated form\nconsumed within $x_k \\approx$ 1 $\\mu$m —\nno stirrer reaches this layer;\nconvection cannot help",
           xy=(1.0,0.40), xytext=(5.0,0.47), fontsize=4.8, color=RED, va="center",
           arrowprops=dict(arrowstyle="->", color=RED, lw=0.8))
b.text(8.8,0.255,"substrate dips too\n(total catalysis)",fontsize=4.6,color=RED,alpha=0.8,va="top")
b.text(0.97,0.04,"solid: c$_{ox}$/C$_{med}$ (act. mediator)\ndashed: c$_S$/C$_S$ (substrate)\n$\\delta$ = 100 $\\mu$m, at 0.9 $i_{lim}$",
       transform=b.transAxes, fontsize=4.6, va="bottom", ha="right", color="0.3")
b.set_xlim(0,15); b.set_ylim(0,1.05)
b.set_xlabel("distance from electrode ($\\mu$m)",fontsize=7.5)
b.set_ylabel("c / c$_{bulk}$",fontsize=7.5)

# ─── c) nondimensional architecture payoff map ─────────────────────────────────
# mu = (n_c C_med D_med)/(n_S C_S D_S). The n_S = 2 stoichiometry (electrons per
# substrate, run_mediated.jl MedSpec) was previously omitted, overstating the mediated
# plateau 2x. ACT row (Zhong/Stahl OPRD 2021, page-verified): n_c 1, n_S 2, C_med 25,
# C_S 500 mol/m3, D_med 5.93e-10, D_S 7.22e-10 m2/s -> 0.02053.
mu=0.0205; eps=0.060   # eps: Ni-amination 5 mM/50 mM (Kawamata JACS 2019 Tbl 4 fn a p.6399) x D ratio 0.6 [0.6 UNSOURCED]
x=np.logspace(0,np.log10(300),400)
c.plot(x,x,color=BLUE,lw=1.9,zorder=5)
c.plot(x,eps*x,color=RED,lw=1.6,zorder=4)
for sl,ls in [(1,":"),(10,"--"),(100,"-")]:
    y=np.minimum(x,np.maximum(mu*x,mu*sl))
    c.plot(x,y,color=ORANGE,lw=1.3,ls=ls,zorder=4,label=f"$\\delta_{{batch}}/x_k$ = {sl}")
# Archetype bands: min-max of x-hat over the 50 rows, computed at runtime from
# julia/correlations.jl + julia/reactions_table.jl (figs/archetype_bands.py).
# Thin gap is drawn SEPARATELY from RDE/RCE -- the old (30,100) band lumped them
# and put both a factor of 2-3 to the right of where the model places them.
BANDS=xhat_bands(); XMAX=xhat_ceiling()
ROWS={"stirred":175,"flow":430,"anec":175,"micro":300,"rotating":430}   # label heights; "micro" joined the archetypes on 2026-09-07
for x0,x1,lab,key in BANDS:
    if x1-x0 < 1e-9:                      # stirred: one fixed delta for every row
        c.axvline(x0,color=BLUE,alpha=0.35,lw=1.1,zorder=0)
        c.text(x0,ROWS.get(key,300),lab,fontsize=4.8,ha="center",va="center",color=BLUE)
    else:
        c.axvspan(x0,x1,color=BLUE,alpha=0.08,zorder=0)
        c.text(np.sqrt(x0*x1),ROWS.get(key,300),lab,fontsize=4.8,ha="center",va="center",color=BLUE)
c.text(1.02,430,"unstirred\nbatch",fontsize=4.8,ha="left",va="center",color=BLUE)
c.axvspan(XMAX,300,color="0.5",alpha=0.10,zorder=0)
c.text(np.sqrt(XMAX*300),430,f"no archetype\nreaches $\\hat{{x}}$ > {XMAX:.0f}",
       fontsize=4.6,ha="center",va="center",color="0.35")
c.annotate("direct: every $\\delta$ gain\nconverts 1:1 into rate",xy=(40,40),xytext=(1.05,55),
           fontsize=4.8,color=BLUE,ha="left",
           arrowprops=dict(arrowstyle="->",color=BLUE,lw=0.8))
c.annotate("dilute catalyst: parallel —\nonly $C_{cat}$ closes the gap",
           xy=(150,9.0),xytext=(120,0.9),fontsize=4.8,color=RED,ha="center",va="center",
           arrowprops=dict(arrowstyle="->",color=RED,lw=0.8))
c.annotate("mediated plateau:\nconvection buys nothing",xy=(2.6,2.05),xytext=(1.05,6.5),
           fontsize=4.8,color=ORANGE,va="bottom",ha="left",
           arrowprops=dict(arrowstyle="->",color=ORANGE,lw=0.8))
c.set_xscale("log"); c.set_yscale("log")
c.set_xlim(1,300); c.set_ylim(0.02,900)
c.set_xlabel("reactor intensification  $\\hat{x}=\\delta_{batch}/\\delta$",fontsize=7.5)
c.set_ylabel("$i_{lim}$ / $i_{lim}^{direct}$(unstirred batch)",fontsize=7.5)
c.legend(fontsize=4.8,frameon=False,loc="lower right",
         title=f"mediated (EC$'$), $\\mu$={mu:g}",title_fontsize=4.8)

plabel(a,"a)"); plabel(b,"b)"); plabel(c,"c)")
fig1.tight_layout(w_pad=1.3)
fig1.savefig(os.path.join(HERE,"sec4_Fig4B_ac.svg"))
fig1.savefig(os.path.join(HERE,"sec4_Fig4B_ac.png"),dpi=600)
print("Fig4B-ac written")

# ═════════════════════════════ FIGURE 4B-def (1 x 3) ═══════════════════════════
fig2, axs2, _ = gengrid(3, 1, size_inches=(7.2, 2.6), ticklabel_size=6.5, genlabels=False)
d, e, f = np.ravel(axs2)

# ─── d) cell voltage / ohmic stack ─────────────────────────────────────────────
# Registry electrolytes from thermal_model.SOLVENTS at the 5 mm flow-cell gap of
# REACTORS[2] (one variable: solvent), plus the same DMF in the 250 um gap of
# REACTORS[3] to show the geometric remedy. The previous version used a set of
# electrolytes with no row in data/parameters_provenance.csv, and quietly mixed
# three different gaps across the five curves.
# REACTORS[2] is the recirculating flow cell (2 cm) and REACTORS[4] the microfluidic chip
# (25 um): a centimetre-gap flow cell against the geometric remedy, which is the contrast
# this panel exists for. Before 2026-09-12 index 3 was the 250 um microfluidic; it is now
# the ANEC cell, which shares the beaker gap and would have shown no remedy at all.
GAP_FLOW = REACTORS[2][1]; GAP_THIN = REACTORS[4][1]
ii=np.linspace(1,300,200)
for lab,elyte,kap,Tb,prov in SOLVENTS:
    d.plot(ii,E_cell(ii,kap,GAP_FLOW),lw=1.3,color=SCOL[lab],
           label=f"{lab}, {GAP_FLOW*1e3:.0f} mm")
_dmf=[s for s in SOLVENTS if s[0]=="DMF"][0]
d.plot(ii,E_cell(ii,_dmf[2],GAP_THIN),lw=1.3,color=GREEN,
       label=f"DMF, {GAP_THIN*1e6:.0f} $\\mu$m")
d.axhspan(10,20,color="0.93",zorder=0)
d.text(294,14.2,"academic non-aqueous cells",fontsize=5.0,color="0.45",ha="right")
d.axvline(BARRIER,color="0.15",ls=":",lw=0.9)
d.set_xlim(0,300); d.set_ylim(0,60)
d.set_xlabel("current density (mA cm$^{-2}$)",fontsize=7.5)
d.set_ylabel("cell voltage (V)",fontsize=7.5)
d.legend(fontsize=4.8,frameon=False,loc="upper left",bbox_to_anchor=(0.03,1.0),borderaxespad=0.2)

# ─── e) boil-off, passively cooled beaker (= Fig. K panel a) ───────────────────
# Model, electrolytes, gap and U' all imported from figs/thermal_model.py, so this
# panel and Fig. K(a) cannot disagree. U' is DERIVED from the registered vessel
# geometry (sigma = 12.5), not assumed: 0.01438 W/cm2 K, ~30% below the 0.020
# "still air" value this panel used to assume.
L_BEAKER = BEAKER[1]; I_DESIGN_BEAKER = BEAKER[4]
ii2=np.linspace(0.5,150,600)
for lab,elyte,kap,Tb,prov in SOLVENTS:
    col=SCOL[lab]
    e.plot(ii2,T_ss(ii2,kap,L_BEAKER,U_BEAKER),color=col,lw=1.5)
    e.axhline(Tb,color=col,ls=":",lw=0.8,alpha=0.65)
    ib=i_boil(kap,L_BEAKER,Tb,U_BEAKER)
    if ib<150:
        e.plot([ib],[Tb],"o",color=col,ms=4.5,mec="white",mew=0.6,zorder=6)
        e.annotate(f"boils at {ib:.0f}",xy=(ib,Tb),xytext=(ib+4,Tb-20),
                   fontsize=5.0,color=col,ha="left")
    else:
        # Off scale: say so. dT grows as i^2, so a flat-looking curve at 150
        # still boils not far beyond it, and silence invites the wrong inference.
        e.annotate(f"{lab}: {Tb:.0f} $^\\circ$C at\n{ib:.0f} mA cm$^{{-2}}$ (off scale)",
                   xy=(148,T_ss(148.,kap,L_BEAKER,U_BEAKER)),xytext=(4,116),
                   fontsize=4.5,color=col,ha="left",
                   arrowprops=dict(arrowstyle="->",color=col,lw=0.7))
e.axvline(I_DESIGN_BEAKER,color="0.35",lw=1.0,ls="--")
e.text(I_DESIGN_BEAKER+3,30,f"design current\n{I_DESIGN_BEAKER:.0f} mA cm$^{{-2}}$",
       fontsize=4.8,color="0.35",va="bottom")
e.text(0.03,0.97,"unstirred 100 mL beaker, %.0f cm gap, 10 cm$^2$\npassive cooling, $U'$ = %.4f W cm$^{-2}$K$^{-1}$\n(derived from vessel geometry, $\\sigma$ = %.1f)"
       %(L_BEAKER*1e2,U_BEAKER,BEAKER[2]),
       transform=e.transAxes,fontsize=5.0,va="top",color="0.3")
# curves are labelled at their own boiling lines rather than by a legend box,
# which would sit on top of the off-scale annotation
for lab,elyte,kap,Tb,prov in SOLVENTS:
    if lab=="DMF":       # highest b.p.: label at the left, the right edge is busy
        e.text(3,Tb+3,f"{lab} b.p. {Tb:.0f} $^\\circ$C",fontsize=4.6,color=SCOL[lab],
               ha="left",va="bottom")
    else:
        e.text(148,Tb+2,f"{lab} b.p. {Tb:.0f} $^\\circ$C",fontsize=4.6,color=SCOL[lab],
               ha="right",va="bottom")
e.set_xlim(0,150); e.set_ylim(25,200)
e.set_xlabel("current density (mA cm$^{-2}$)",fontsize=7.5)
e.set_ylabel("steady-state cell T ($^\\circ$C)",fontsize=7.5)

# ─── f) absolute boil-off ceiling vs architecture (= Fig. K panel b) ───────────
# ABSOLUTE ceiling, not normalised: dividing by a design current that changes from
# column to column hides the trend behind an arbitrary divisor. Design currents
# appear as reference lines only. All five architectures are PASSIVELY cooled,
# each with the U' its own geometry delivers -- which is why the ceiling does NOT
# rise monotonically with intensification.
xr=np.arange(len(REACTORS))
ceil_f={}
for lab,elyte,kap,Tb,prov in SOLVENTS:
    ib=[i_boil(kap,L,Tb,U_passive(sig,hi)) for rl,L,sig,hi,iop in REACTORS]
    ceil_f[lab]=ib
    f.plot(xr,ib,"-o",color=SCOL[lab],lw=1.5,ms=4.5,mec="white",mew=0.6,label=lab,zorder=4)
for lvl,txt,side in [(50.,"50 (the barrier)","l"),(500.,"500","r"),(1000.,"1 A cm$^{-2}$","r")]:
    f.axhline(lvl,color="0.45",ls="--",lw=0.9,zorder=1)
    f.text(-0.42 if side=="l" else len(REACTORS)-0.55, lvl*1.12, txt, fontsize=5.0,
           color="0.4", ha="left" if side=="l" else "right", va="bottom")
f.set_yscale("log"); f.set_ylim(3,3e3); f.set_xlim(-0.5,len(REACTORS)-0.5)
f.set_xticks(xr)
# short forms of thermal_model.REACTORS labels; the full names are in the caption
# 2026-09-12: DERIVED from thermal_model.REACTORS rather than typed. The typed list carried
# five labels against an eight-row table and matplotlib refused the mismatch, which is the
# good outcome; a typed label list is a stale label list waiting for the next architecture.
FSHORT=[r[0] for r in REACTORS]
f.set_xticklabels(FSHORT,fontsize=5.0)
f.set_ylabel("boil-off current density (mA cm$^{-2}$)",fontsize=7.5)
f.set_xlabel("reactor architecture (passive cooling only)",fontsize=7.5)
f.legend(fontsize=4.8,frameon=True,framealpha=0.9,edgecolor="0.85",
         loc="upper left",handletextpad=0.4,borderpad=0.35)

plabel(d,"d)"); plabel(e,"e)"); plabel(f,"f)")
fig2.tight_layout(w_pad=1.3)
fig2.savefig(os.path.join(HERE,"sec4_Fig4B_def.svg"))
fig2.savefig(os.path.join(HERE,"sec4_Fig4B_def.png"),dpi=600)
print("Fig4B-def written (thermal model = figs/thermal_model.py, shared with Fig. K)")
print("  panel e, unstirred beaker ceilings (mA/cm2), U' = %.5f:" % U_BEAKER)
for lab,elyte,kap,Tb,prov in SOLVENTS:
    print("    %-9s %-22s kappa=%5.2f  Tb=%5.0f  i_boil=%8.1f"
          %(lab,elyte,kap,Tb,i_boil(kap,L_BEAKER,Tb,U_BEAKER)))
print("  panel f, absolute ceilings by architecture (mA/cm2):")
print("    %-9s"%"solvent"+"".join("%22s"%r[0].replace("\n"," ") for r in REACTORS))
for lab,elyte,kap,Tb,prov in SOLVENTS:
    print("    %-9s"%lab+"".join("%22.0f"%v for v in ceil_f[lab]))
