"""FigK — does the solvent actually boil? Lumped thermal balance on a 100 mL,
10 cm^2-electrode cell, consistent with the cellvoltage.jl stack.

Heat generation per electrode area (dissipated overpotential heat, conservative:
excludes reaction entropy and radiation/evaporation losses):
    q(i) = [ 2b*asinh(i/2i0) + i_SI*L/kappa ] * i_SI   [W/m^2] -> W/cm^2
Steady state:  T_ss = T_amb + q / U'   with U' the effective heat-rejection
coefficient PER ELECTRODE AREA (UA / A_elec):
    still air        : UA = 0.20 W/K on a 100 mL vessel  -> U' = 0.020 W/cm^2 K
                       (h_conv ~ 7 + h_rad ~ 6-8 W/m^2K on ~0.015 m^2; radiation
                        is NOT negligible at 60-150 C and omitting it would
                        overstate the boiling problem)
    stirred bath     : UA = 1.8  W/K                     -> U' = 0.18  W/cm^2 K
    PEM-class plates : U' = 0.30 W/cm^2 K (2-6 W/cm^2 at 10-20 K gradients)
Boil-off ceiling: i_boil solves q(i) = U'*(T_b - T_amb).
Transient: exact lumped response T(t) = T_amb + (P/UA)(1 - exp(-t UA/C)), so
time-to-boil = (C/UA) ln[P/(P - UA dT_b)] and only exists when P > UA dT_b.
Evaporative loss is omitted on BOTH sides (it delays boil-off but IS solvent loss).
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, sys, os

# ── RETIRED GENERATOR — DO NOT USE FOR NEW ARTWORK ───────────────────────────
# This script produced the two-panel image that was pasted into the manuscript as
# MS Fig 5 (v17 word/media/image5.png, 2880x1320, MD5 6d9ed9c1350547221937134eb76b552b).
# Its physics is SUPERSEDED by figs/make_figK.py + figs/thermal_model.py, which
# replaced the unregistered electrolytes used below (0.1 M Bu4NPF6/THF 0.06 S/m,
# 0.1 M Bu4NBF4/DMF 0.35, MeCN 0.90, aq. KOH 20.0), the 5 mm beaker gap and the
# ASSUMED "still air" UA = 0.2 W/K with registry electrolytes, a 2 cm canonical
# beaker gap and a U' DERIVED from vessel geometry. It is kept only so that the
# provenance of the already-printed image is reconstructible.
#
# 2026-08-02, two runnability/safety fixes (physics untouched):
#   (1) PATHS. The original hardcoded sys.path/os.chdir to /home/claude/rce, so it
#       could not run anywhere else and its own output could not be reproduced.
#       Paths are now resolved from __file__.
#   (2) OUTPUT COLLISION. The original savefig()'d to figs/sec4_figK_boiloff.{png,svg}
#       — the SAME paths the LIVE figs/make_figK.py writes — so running it would
#       silently overwrite the current, remediated Fig. K with the retracted one.
#       Output is now redirected into this _superseded/ directory.
HERE = os.path.dirname(os.path.abspath(__file__))          # figs/_superseded
FIGS = os.path.dirname(HERE)                               # figs
SEC4 = os.path.dirname(FIGS)                               # Section4_Model
for _cand in (SEC4, FIGS, os.path.expanduser("~/Documents/CO2R-Bulk-Scale-Julia-Model")):
    if os.path.exists(os.path.join(_cand, "customplot.py")):
        sys.path.insert(0, _cand)
        os.chdir(_cand)          # customplot reads "Color Swatches from UC Berkeley.xlsx" from cwd
        break
else:
    raise SystemExit("customplot.py not found next to this script; cannot run.")
from customplot import gengrid, rainbow_2

# Every render of this retired script lands HERE, never on the live Fig. K.
OUT = os.path.join(HERE, "sec4_figK_boiloff_preThermalSplit")

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]
RT_F=0.025693; b=2*RT_F; i0=1.0; E0=2.0; TAMB=25.0

# (label, kappa S/m, gap m, T_boil C, color)
CELLS=[("THF, 5 mm (0.1 M Bu$_4$NPF$_6$)",  0.06, 5e-3,  66., RED),
       ("DMF, 5 mm (0.1 M Bu$_4$NBF$_4$)",  0.35, 5e-3, 153., ORANGE),
       ("MeCN, 5 mm (0.1 M Bu$_4$NBF$_4$)", 0.90, 5e-3,  82., LBLUE),
       ("DMF, 250 $\\mu$m thin gap",         0.35, 2.5e-4,153., GREEN),
       ("aq. KOH, 1 mm",                    20.0, 1e-3, 100., BLUE)]
COOL=[("still air", 0.020), ("stirred bath", 0.18), ("PEM-class plates", 0.30)]

def q_Wcm2(i, kappa, gap):                       # i in mA/cm2
    i_SI = i*10.0
    return (2*b*np.arcsinh(i/(2*i0)) + i_SI*gap/kappa) * i_SI * 1e-4

def i_boil(kappa, gap, Tb, Uprime):
    target = Uprime*(Tb-TAMB)
    lo, hi = 1e-3, 1e5
    for _ in range(80):
        mid = np.sqrt(lo*hi)
        if q_Wcm2(mid, kappa, gap) > target: hi = mid
        else: lo = mid
    return np.sqrt(lo*hi)

fig, axes, _ = gengrid(2,1, size_inches=(7.2,3.3), ticklabel_size=7.5)
a,bx = axes

# ── a) steady-state temperature in STILL AIR (the default academic setup) ────
Uair = COOL[0][1]
ii = np.linspace(0.5,150,600)
for lab,kap,gap,Tb,col in CELLS:
    T = TAMB + q_Wcm2(ii,kap,gap)/Uair
    a.plot(ii, T, color=col, lw=1.7)
    ib = i_boil(kap,gap,Tb,Uair)
    if ib < 150:
        a.plot([ib],[Tb],"o",color=col,ms=5,mec="white",mew=0.6,zorder=6)
        a.annotate(f"boils at {ib:.0f}", xy=(ib,Tb), xytext=(ib+6,Tb-13),
                   fontsize=5.4, color=col)
for lab,kap,gap,Tb,col in CELLS[:3]:
    a.axhline(Tb, color=col, ls=":", lw=0.8, alpha=0.7)
a.text(147, 68, "THF b.p.", fontsize=5.0, color=RED, ha="right", va="bottom")
a.text(147, 84, "MeCN b.p.", fontsize=5.0, color=LBLUE, ha="right", va="bottom")
a.text(147, 155, "DMF b.p.", fontsize=5.0, color=ORANGE, ha="right", va="bottom")
a.text(0.03,0.97,"100 mL cell, 10 cm$^2$ electrodes, still air\n(UA = 0.2 W K$^{-1}$, incl. radiation) — no active cooling",
       transform=a.transAxes, fontsize=6.0, va="top", color="0.3")
a.annotate("thin gap: heat source\nremoved at the root\n($Q \\propto L/\\kappa$)", xy=(120,32), xytext=(60,44),
           fontsize=5.6, color=GREEN, arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.8))
a.set_xlim(0,150); a.set_ylim(25,200)
a.set_xlabel("Current density (mA cm$^{-2}$)", fontsize=8)
a.set_ylabel("Steady-state cell temperature ($^\\circ$C)", fontsize=8)

# ── b) boil-off ceiling vs cooling strategy ──────────────────────────────────
ylabels=[]
for row,(lab,kap,gap,Tb,col) in enumerate(CELLS):
    ibs=[i_boil(kap,gap,Tb,U) for _,U in COOL]
    y=len(CELLS)-1-row
    bx.plot(ibs,[y]*3,"-",color=col,lw=1.1,alpha=0.6,zorder=3)
    for (cl,_),ib,mk in zip(COOL,ibs,["o","s","^"]):
        bx.plot([ib],[y],mk,color=col,ms=5.5,mec="white",mew=0.6,zorder=5)
    ylabels.append(lab)
bx.axvline(25, color="0.6", ls=":", lw=0.9); bx.text(25,-0.45,"25",fontsize=5.4,color="0.4",ha="center")
bx.axvline(50, color="0.25", lw=1.0);  bx.text(58,4.62,"50 (the barrier)",fontsize=5.4,color="0.2",ha="left")
bx.set_yticks(range(len(CELLS))); bx.set_yticklabels(reversed(ylabels), fontsize=6.0)
bx.set_xscale("log"); bx.set_xlim(5,2e4); bx.set_ylim(-0.6,4.6)
# marker legend (grey)
for mk,cl,xx in zip(["o","s","^"],[c[0] for c in COOL],[0.60,0.72,0.86]):
    bx.plot([],[],mk,color="0.45",ms=5,mec="white",mew=0.5,label=cl)
bx.legend(fontsize=5.4, frameon=False, loc="lower right", ncol=1, handletextpad=0.4)
bx.set_xlabel("Boil-off current density (mA cm$^{-2}$)", fontsize=8)

fig.tight_layout(w_pad=2.0)
fig.savefig(OUT + ".svg"); fig.savefig(OUT + ".png", dpi=400)
print("retired generator -> " + OUT + ".{svg,png}  (live Fig. K NOT touched)")

# ── console: the numbers for the text ────────────────────────────────────────
print(f"{'cell':38s}" + "".join(f"{c[0]:>18s}" for c in COOL))
for lab,kap,gap,Tb,col in CELLS:
    plain = lab.replace('$_4$','4').replace('$\\mu$m','um').replace('$','')
    print(f"{plain:38s}" + "".join(f"{i_boil(kap,gap,Tb,U):18.0f}" for _,U in COOL))
# transient time-to-boil at 50 and 100 mA/cm2 in still air (exact lumped response:
# t_boil = (C/UA) ln[P/(P - UA*dT_b)], defined only when P exceeds the loss at T_b)
UA_air = 0.20
for lab,kap,gap,Tb,cp_rho in [("THF 5mm",0.06,5e-3,66.,(1.72,0.889)),("DMF 5mm",0.35,5e-3,153.,(2.05,0.944))]:
    cp,rho = cp_rho; C = 100*rho*cp     # J/K for 100 mL
    for i in (50.,100.):
        P = q_Wcm2(i,kap,gap)*10.0      # W
        loss_at_boil = UA_air*(Tb-TAMB)
        if P <= loss_at_boil:
            Tss = TAMB + P/UA_air
            print(f"{lab} @ {i:.0f} mA/cm2: P_diss = {P:5.1f} W — never boils (T_ss = {Tss:.0f} C)")
        else:
            t = (C/UA_air)*np.log(P/(P-loss_at_boil))/60
            print(f"{lab} @ {i:.0f} mA/cm2: P_diss = {P:5.1f} W, time to boil = {t:5.1f} min")
