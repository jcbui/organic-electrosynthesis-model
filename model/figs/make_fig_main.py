"""Section 4 MAIN composite figure (6 panels).
a) reactor-architecture schematic (delta shrinks) — Illustrator placeholder art
b) carrier taxonomy schematic with ceiling formulas
c) gap chart, 9 named exemplars (batch -> engineered reactor)
d) all 50 reactions, no text: strip distribution across architectures
e) EC' mediator amplification (three regimes)
f) cell-voltage / ohmic ceiling

2026-08-02. Panel f no longer carries its own electrolyte set or its own copy of the
voltage stack. It previously hardcoded kappa = 0.06 (THF), 0.35 (DMF), 0.90 (MeCN) and
20.0 (aq. KOH) S/m across a mixture of 5 mm / 1 mm / 250 um gaps, and re-implemented
E_cell inline with RT_F = 8.314*298.15/F = 0.0256912 rather than the 0.025693 of the
shared model. Three of those four conductivities are retracted BY NAME by SI S6.1 and
the Table S4 caption (0.6, 3.5 and 200 mS/cm), so the shipped generator could regenerate
a retracted claim, and the rendered composite still printed the label "aq. KOH, 1 mm".
The panel now imports figs/thermal_model.py and is driven from SOLVENTS and REACTORS,
exactly as make_fig4B.py panel d and make_figs.py FIG D already are.
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, sys, os
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle
from matplotlib.lines import Line2D

# Portable paths (2026-08). The previous header hardcoded /home/claude/rce, which no
# longer exists; the script could not be re-run at all, so the rendered composite could
# not be re-derived from its source. Same resolution pattern as make_figK.py.
HERE = os.path.dirname(os.path.abspath(__file__))
SEC4 = os.path.dirname(HERE)
for cand in (SEC4, HERE, os.path.expanduser("~/Documents/CO2R-Bulk-Scale-Julia-Model")):
    if os.path.exists(os.path.join(cand, "customplot.py")):
        sys.path.insert(0, cand); break
sys.path.insert(0, HERE)          # figs/ itself, for thermal_model
os.chdir(SEC4)
from customplot import gengrid, rainbow_2
from thermal_model import SOLVENTS, REACTORS, E_cell

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]
F=96485.33; BARRIER=50.0; OPER=25.0

rx=pd.read_csv("data/reactions_50.csv"); t0=pd.read_csv("julia/tier0_ec_matrix.csv")
df=pd.concat([rx.reset_index(drop=True), t0[["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]]],axis=1)
df["best"]=df[["anec","rde","rce"]].max(axis=1)
sw=pd.read_csv("julia/npp_ecprime_sweep.csv")

fig, axs, _ = gengrid(2, 3, size_inches=(7.2, 8.8), ticklabel_size=7, label_pos=-0.12)
a,b = axs[0]; c,d = axs[1]; e,f = axs[2]

# ═══ a) reactor architectures: delta shrinks (placeholder schematic) ═══════════
a.set_xlim(0,10); a.set_ylim(0,10); a.axis("off")
cells=[("unstirred\nbatch","300 µm",1.66,None),("stirred\nbatch","100 µm",1.4,"stir"),
       ("flow cell\n1 mm gap","30–60 µm",0.7,"flow"),("thin gap / RCE","<10 µm",0.25,"spin")]
for i,(nm,dl,filmw,icon) in enumerate(cells):
    x0=0.4+i*2.45
    a.add_patch(Rectangle((x0,2.6),2.0,4.6,fc="0.965",ec="0.55",lw=0.9))       # cell
    a.add_patch(Rectangle((x0+0.08,2.75),0.22,4.3,fc="0.35",ec="none"))         # electrode
    a.add_patch(Rectangle((x0+0.30,2.75),filmw,4.3,fc=LBLUE,alpha=0.55,ec="none"))  # film
    a.text(x0+1.0,8.05,nm,ha="center",fontsize=5.6,color="0.15")
    a.text(x0+1.0,1.95,"$\\delta\\approx$ "+dl,ha="center",fontsize=5.6,color=BLUE)
    if icon=="stir": a.add_patch(Rectangle((x0+1.0,2.95),0.6,0.18,fc="0.5",angle=20))
    if icon=="flow":
        for yy in (4.0,5.2,6.4):
            a.add_patch(FancyArrowPatch((x0+0.75,yy),(x0+1.75,yy),arrowstyle="-|>",mutation_scale=6,color="0.45",lw=0.9))
    if icon=="spin":
        a.add_patch(FancyArrowPatch((x0+1.05,6.3),(x0+1.75,6.3),arrowstyle="-|>",mutation_scale=6,
                    connectionstyle="arc3,rad=0.9",color="0.45",lw=0.9))
a.add_patch(FancyArrowPatch((1.4,9.3),(9.2,9.3),arrowstyle="-|>",mutation_scale=9,color=BLUE,lw=1.3))
a.text(5.3,9.75,"engineering convection: $\\delta$ shrinks, $i_{lim}=n_cFD_cC_c/\\delta$ rises",
       ha="center",fontsize=6.0,color=BLUE)
a.text(5.3,0.8,"(schematic placeholder — final art in Illustrator)",ha="center",fontsize=4.8,color="0.6",style="italic")

# ═══ b) carrier taxonomy with ceiling formulas (schematic) ═════════════════════
b.set_xlim(0,10); b.set_ylim(0,10); b.axis("off")
def electrode(x0):
    b.add_patch(Rectangle((x0,1.6),0.28,6.6,fc="0.35",ec="none"))
for i,(ttl,form) in enumerate([("direct\n(substrate-carried)","$i_{lim}\\propto n\\,C_{sub}D/\\delta$"),
                               ("mediated (EC$'$)","$i_{lim}\\propto C_{med}\\sqrt{kC_{sub}D}$\n$\\rightarrow$ substrate cap"),
                               ("molecular catalyst","$i_{lim}\\propto n\\,C_{cat}D_{cat}/\\delta$\n$C_{cat}$ = 3–30 mM")]):
    x0=0.5+i*3.2; electrode(x0)
    b.text(x0+1.45,8.7,ttl,ha="center",fontsize=5.6,color="0.15")
    b.text(x0+1.45,0.35,form,ha="center",fontsize=5.4,color=BLUE)
if True:
    # direct: S arrow in, P out
    b.add_patch(FancyArrowPatch((2.7,5.9),(1.0,5.9),arrowstyle="-|>",mutation_scale=8,color=GREEN,lw=1.4))
    b.text(2.15,6.25,"S",fontsize=6.5,color=GREEN)
    b.add_patch(FancyArrowPatch((1.0,3.6),(2.7,3.6),arrowstyle="-|>",mutation_scale=8,color="0.5",lw=1.1))
    b.text(2.15,2.9,"P",fontsize=6.5,color="0.5")
    # mediated: shuttle cycle inside reaction layer x_k
    x0=3.7
    b.add_patch(Rectangle((x0+0.28,1.6),0.9,6.6,fc=ORANGE,alpha=0.18,ec="none"))
    b.text(x0+0.73,7.55,"$x_k$",fontsize=5.5,color=ORANGE,ha="center")
    b.add_patch(FancyArrowPatch((x0+0.35,4.4),(x0+1.5,5.5),arrowstyle="-|>",mutation_scale=7,
                connectionstyle="arc3,rad=-0.55",color=ORANGE,lw=1.3))
    b.add_patch(FancyArrowPatch((x0+1.5,4.6),(x0+0.35,3.6),arrowstyle="-|>",mutation_scale=7,
                connectionstyle="arc3,rad=-0.55",color=ORANGE,lw=1.3))
    b.text(x0+1.05,5.9,"Med$_{ox}$",fontsize=5.2,color=ORANGE)
    b.text(x0+1.05,2.9,"Med$_{red}$",fontsize=5.2,color=ORANGE)
    b.add_patch(FancyArrowPatch((x0+2.75,5.05),(x0+1.75,5.05),arrowstyle="-|>",mutation_scale=7,color=GREEN,lw=1.2))
    b.text(x0+2.35,5.4,"S",fontsize=6,color=GREEN)
    # catalyst: cycle pinned at electrode, sparse dots
    x0=6.9
    b.add_patch(FancyArrowPatch((x0+0.35,4.6),(x0+1.25,5.4),arrowstyle="-|>",mutation_scale=7,
                connectionstyle="arc3,rad=-0.6",color=RED,lw=1.3))
    b.add_patch(FancyArrowPatch((x0+1.25,4.4),(x0+0.35,3.7),arrowstyle="-|>",mutation_scale=7,
                connectionstyle="arc3,rad=-0.6",color=RED,lw=1.3))
    b.text(x0+0.85,5.75,"M$^{n}$/M$^{n-2}$",fontsize=5.0,color=RED)
    for (dx,dy) in [(1.9,6.6),(2.4,5.0),(2.0,3.0),(2.6,6.0),(2.7,3.8)]:
        b.add_patch(Circle((x0+dx,dy),0.09,fc=RED,ec="none",alpha=0.7))
    b.text(x0+2.3,2.2,"dilute",fontsize=5.0,color=RED,ha="center")

# ═══ c) gap chart: 9 named exemplars ═══════════════════════════════════════════
picks=[("Anodic methoxylation of 4-tBu-toluene (Lysmeral)","BASF methoxylation (0.8 M)"),
       ("Acrylonitrile hydrodimerization (ADN)","ADN hydrodimerization (6.9 M)"),
       ("Kolbe homocoupling of 10-undecenoate","Kolbe coupling (1 M)"),
       ("Thioether -> sulfone (kilo-scale)","sulfone oxidation, kg-scale (0.47 M)"),
       ("Shono oxidation (N-acyliminium capture)","Shono oxidation (1.56 M)"),
       ("Birch reduction of naphthalene","Birch reduction (0.14 M)"),
       ("Doubly decarboxylative Csp3-Csp3","decarboxylative C–C (0.03 M)"),
       ("ACT-mediated alcohol oxidation (flow, hectogram)","ACT-mediated alcohol ox.  [med. 25 mM]"),
       ("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)","Ni-XEC, kg-scale in flow  [cat. 15 mM]")]
c.axvspan(0.2,OPER,color="0.93",zorder=0)
c.axvline(OPER,color="0.55",ls=":",lw=0.9); c.axvline(BARRIER,color="0.15",lw=1.1)
for i,(full,lab) in enumerate(picks):
    r=df[df.reaction==full].iloc[0]
    col = GREEN if r.best>=BARRIER else (ORANGE if r.best>=OPER else RED)
    bcap=min(r.best,5200)
    c.plot([r.natural,bcap],[i,i],color=col,lw=1.4,zorder=3)
    c.plot(r.natural,i,"o",ms=3.6,mfc="white",mec=col,mew=1.1,zorder=4)
    c.plot(bcap,i,">",ms=4.6,color=col,zorder=4)
    if r.best>5200: c.text(6300,i,"$\\gg$",fontsize=5.5,color=col,va="center")
c.set_yticks(range(9)); c.set_yticklabels([l for _,l in picks],fontsize=5.4)
c.tick_params(axis="y",length=0); c.invert_yaxis()
c.set_xscale("log"); c.set_xlim(0.2,7000); c.set_ylim(8.8,-1.6)
c.set_xlabel("$i_{lim}$ (mA cm$^{-2}$)",fontsize=7.5)
c.text(0.28,-0.95,"batch $\\circ\\!\\rightarrow\\!\\blacktriangleright$ engineered reactor",fontsize=5.2,color="0.3")
c.text(BARRIER*1.25,-0.95,"50: 1/14 exceed",fontsize=5.0,color="0.15")
c.text(0.28,-0.35,"< 25: 10/14 pharma scale-ups operate here",fontsize=4.8,color="0.4",style="italic")

# ═══ d) all 50, no text: strip across architectures ═══════════════════════════
cols6=["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
labs6=["unstirred","stirred","recirc. flow","ANEC","microfluidic","RDE","RCE"]   # legacy generator, not run; kept consistent with the seven-column matrix
mk={"substrate":("o",BLUE),"mediator":("s",ORANGE),"catalyst":("^",RED)}
rng=np.linspace(-0.2,0.2,50)
for j,cn in enumerate(cols6):
    for i,(_,r) in enumerate(df.iterrows()):
        m,cc=mk[r.carrier_type]
        d.plot(j+rng[(i*17)%50], r[cn], m, ms=2.7, color=cc, alpha=0.75, mec="none", zorder=3)
    nab=(df[cn]>=BARRIER).sum()
    d.text(j,0.017,f"{nab}",ha="center",fontsize=5.6,color="0.15",
           bbox=dict(fc="white",ec="none",alpha=0.8,pad=0.4))
d.text(-0.62,0.017,"$\\geq$50:",ha="right",fontsize=5.6,color="0.15")
d.axhline(BARRIER,color="0.15",lw=1.1); d.axhline(OPER,color="0.55",ls=":",lw=0.9)
d.annotate("50", xy=(1.005,0.585), xycoords="axes fraction", fontsize=5.2, color="0.15", annotation_clip=False)
d.set_yscale("log"); d.set_ylim(0.008,4000)
d.set_xticks(range(len(labs6))); d.set_xticklabels(labs6,fontsize=5.6,rotation=25,ha="right")
d.set_ylabel("$i_{lim}$, all 50 reactions (mA cm$^{-2}$)",fontsize=7.5)
from matplotlib.lines import Line2D
h=[Line2D([0],[0],marker=m,ls="",ms=3.5,color=cc,label=t) for t,(m,cc) in mk.items()]
d.legend(handles=h,fontsize=5.0,frameon=False,loc="upper left",handletextpad=0.2,borderaxespad=0.15)

# ═══ e) EC' mediator amplification ════════════════════════════════════════════
# PROVENANCE OF EVERY MARK IN THIS PANEL (2026-08 remediation of audit finding 11).
# Three different kinds of point used to be drawn identically here, and one solver
# result was dropped by a hardcoded filter. All three are now typed on-figure:
#   (i)   converged solver plateaus                          -> filled circles
#   (ii)  ramps that ended on a Newton wall (STRICT LOWER     -> open triangles
#         BOUNDS by SI Sec. S5.5's own definition)
#   (iii) the analytic total-catalysis cap SUBSTITUTED for    -> open squares
#         the solver in the unresolved moving-front regime
#         (SI Sec. S5.4: "the exact total-catalysis limit is
#         reported instead (Fig. H, open squares)")
# The old code used `val = sw[sw.k_M <= 1e3]`, a hardcoded threshold that selected the
# solver markers, and drew the squares at a hardcoded [3e3, 1e4, 1e5]. The split is now
# the PHYSICAL criterion the SI states -- x_k < 1 um, read from the sweep's own xk_um
# column -- so the two sets cannot drift apart. It selects exactly the same rows
# (solver k = 1e-2...1e3; substituted k = 3e3, 1e4, 1e5), so no plotted value changed.
# Additionally, the solver's own numbers in the substituted regime (46.38, 29.26,
# 19.28 mA/cm2 at k = 3e3, 1e4, 1e5) are no longer omitted: they are drawn as small grey
# lower-bound triangles. They are consistent with the cap, not in conflict with it --
# every one is a stalled-ramp lower bound, so i_solver <= i_true <= i_cap holds at all
# three, and the apparent "peak then collapse" in the raw column is a numerical artefact
# of the stall, not a physical maximum.
delta=100e-6;C_med=20.;C_S=500.;D_med=6e-10;D_S=1e-9
i_sh=0.1*F*D_med*C_med/delta; i_cap=0.1*F*D_S*C_S/delta
XK_CUT_UM=1.0                                        # SI Sec. S5.4 moving-front criterion
WALL="newton-wall (no collapse)"
sol=sw[sw.xk_um>=XK_CUT_UM]; subst=sw[sw.xk_um<XK_CUT_UM]
conv=sol[sol.limiter!=WALL]; wall=sol[sol.limiter==WALL]
kk=np.logspace(-2.4,5.4,80)
e.axhline(i_sh,color="0.5",ls="--",lw=0.9); e.text(1.6e-2,i_sh*0.62,"mediator commuting bound",fontsize=5.0,color="0.45")
e.plot(kk,0.1*F*C_med*np.sqrt(D_med*(kk/1000)*C_S),color="0.5",ls=":",lw=0.9)
e.text(6,10.5,"$\\propto\\sqrt{k}$",fontsize=5.6,color="0.45",rotation=26)
e.axhline(i_cap,color="0.15",lw=1.1)
e.text(1.6e-2,i_cap*1.35,"substrate cap = direct-electrolysis ceiling",fontsize=5.0,color="0.15")
e.axvspan(1000.0*D_med/((XK_CUT_UM*1e-6)**2*C_S),2e5,color="0.94",zorder=0)
e.plot(sol.k_M,sol.ilim_mAcm2,"-",color=ORANGE,lw=1.3,zorder=4)
e.plot(conv.k_M,conv.ilim_mAcm2,"o",color=ORANGE,ms=3.6,mec="none",zorder=5)
e.plot(wall.k_M,wall.ilim_mAcm2,"^",color=ORANGE,mfc="white",mec=ORANGE,mew=0.9,ms=3.8,zorder=5)
e.plot(subst.k_M,subst.ilim_mAcm2,"^",color="0.55",mfc="white",mec="0.55",mew=0.9,ms=3.0,ls=":",lw=0.8,zorder=4)
e.plot(subst.k_M,[i_cap]*len(subst),"s",mfc="white",mec="0.15",mew=0.9,ms=3.4,zorder=5)
e.text(2.2e4,110,"moving-front regime\n($x_k$ < 1 $\\mu$m)",fontsize=4.6,color="0.45",ha="center",va="center")
e.legend(handles=[Line2D([0],[0],ls="",marker="o",ms=3.2,color=ORANGE,label="solver plateau"),
                  Line2D([0],[0],ls="",marker="^",ms=3.4,mfc="white",mec=ORANGE,mew=0.9,color=ORANGE,
                         label="solver lower bound (Newton wall)"),
                  Line2D([0],[0],ls="",marker="s",ms=3.2,mfc="white",mec="0.15",mew=0.9,color="0.15",
                         label="ANALYTIC cap substituted (SI §S5.4)")],
         fontsize=4.0,loc="lower right",handletextpad=0.3,borderaxespad=0.25,labelspacing=0.35,
         frameon=True,framealpha=0.9,facecolor="white",edgecolor="none")
e.set_xscale("log"); e.set_yscale("log"); e.set_xlim(1.2e-2,2e5); e.set_ylim(0.5,200)
e.set_xlabel("homogeneous rate constant $k$ (M$^{-1}$s$^{-1}$)",fontsize=7.5)
e.set_ylabel("mediated $i_{lim}$ (mA cm$^{-2}$)",fontsize=7.5)
e.text(0.03,0.94,"fast mediator kinetics substitute for convection",transform=e.transAxes,fontsize=5.4,color="0.25",va="top")
print("panel e | solver plateaus k =",conv.k_M.tolist(),
      "| Newton-wall lower bounds k =",wall.k_M.tolist()+subst.k_M.tolist(),
      "| analytic cap substituted at k =",subst.k_M.tolist(),
      f"(i_cap = {i_cap:.2f}; solver lower bounds there:",
      [round(v,2) for v in subst.ilim_mAcm2.tolist()],")")

# ═══ f) cell voltage / ohmic-thermal ceiling ═══════════════════════════════════
# Registry electrolytes and gaps, both from figs/thermal_model.py, so this panel,
# Fig. 4B(d) and FIG D cannot disagree: the four SOLVENTS rows at the 5 mm flow-cell
# gap of REACTORS[2] (one variable per curve), plus the same DMF at the 250 um
# microfluidic gap of REACTORS[3] to show the geometric remedy. See module docstring
# for what this replaced and why.
SCOL={"THF":RED,"MeCN":LBLUE,"DMF":ORANGE,"aq. NaOH":BLUE}   # same as Fig. K / 4B
GAP_FLOW=REACTORS[2][1]; GAP_THIN=REACTORS[4][1]   # recirculating flow vs the microfluidic chip
ii=np.linspace(1,300,200)
for lab,elyte,kap,Tb,prov in SOLVENTS:
    f.plot(ii,E_cell(ii,kap,GAP_FLOW),lw=1.3,color=SCOL[lab],
           label=f"{lab}, {GAP_FLOW*1e3:.0f} mm")
_dmf=[s for s in SOLVENTS if s[0]=="DMF"][0]
f.plot(ii,E_cell(ii,_dmf[2],GAP_THIN),lw=1.3,color=GREEN,
       label=f"DMF, {GAP_THIN*1e6:.0f} $\\mu$m")
f.axhspan(10,20,color="0.93",zorder=0)
f.text(294,14.2,"academic non-aqueous cells",fontsize=5.0,color="0.45",ha="right")
f.axvline(BARRIER,color="0.15",ls=":",lw=0.9)
# y-limit raised 40 -> 60 to match Fig. 4B(d). At the registry conductivities THF
# reaches 52.6 V at 300 mA/cm2; a 40 V axis would clip the one curve the panel exists
# to make a point about.
f.set_xlim(0,300); f.set_ylim(0,60)
f.set_xlabel("current density (mA cm$^{-2}$)",fontsize=7.5)
f.set_ylabel("cell voltage (V)",fontsize=7.5)
f.legend(fontsize=4.8,frameon=False,loc="upper left",bbox_to_anchor=(0.30,1.0),borderaxespad=0.2)
print("panel f | E_cell (V) at 50 / 100 / 300 mA cm-2, gaps %.0f mm and %.0f um:"
      % (GAP_FLOW*1e3, GAP_THIN*1e6))
for lab,elyte,kap,Tb,prov in SOLVENTS:
    print("   %-9s kappa=%5.2f S/m  %8.3f %8.3f %8.3f"
          % (lab,kap,*[E_cell(i,kap,GAP_FLOW) for i in (50.,100.,300.)]))
print("   %-9s kappa=%5.2f S/m  %8.3f %8.3f %8.3f  (250 um)"
      % ("DMF",_dmf[2],*[E_cell(i,_dmf[2],GAP_THIN) for i in (50.,100.,300.)]))


fig.tight_layout(h_pad=1.6, w_pad=2.0)
fig.savefig("figs/sec4_MAIN_composite.svg"); fig.savefig("figs/sec4_MAIN_composite.png",dpi=400)
print("main composite written")
