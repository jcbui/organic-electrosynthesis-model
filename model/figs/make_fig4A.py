"""Figure 4A — the transport ceiling and the reactor cure (V5, panel set 1).
a) reactor-architecture schematic (Illustrator placeholder)
b) stirred beaker: substrate starvation vs current (NPP solver)
c) same chemistry at the 50 mA/cm2 barrier across four reactors (NPP solver)
d) all 50 reactions x 6 architectures (mediated rows EC'-coupled)

Runnability remediation, 2026-08-02: the two `/home/claude/rce` hardcodes on the old
lines 11 and 13 made this file unrunnable anywhere in this repository. Paths now
resolve relative to this file, matching make_figs_sec34.py. No plotted quantity,
label or annotation was changed by that remediation.
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, sys, os
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D

# ── portable paths: resolve everything relative to this file, not /home/claude/rce ──
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.chdir(ROOT)          # customplot reads the Berkeley swatch workbook from cwd at import
from customplot import gengrid, rainbow_2
def _find(*cands):
    for c in cands:
        if os.path.exists(os.path.join(ROOT, c)): return os.path.join(ROOT, c)
    raise FileNotFoundError(cands)

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]
BARRIER=50.0; OPER=25.0

rx=pd.read_csv(_find("data/reactions_50.csv","reactions_50.csv"))
t0=pd.read_csv(_find("julia/tier0_ec_matrix.csv"))
t0.columns=[c.strip() for c in t0.columns]
df=pd.concat([rx.reset_index(drop=True), t0[["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]]],axis=1)
pf=pd.read_csv(_find("julia/profiles_direct.csv"))

def with_surface(g):
    x=g.x_um.values; c=g.c_norm.values
    c0=max(c[0]-(c[1]-c[0])*x[0]/(x[1]-x[0]),0.0)
    return np.r_[0.0,x], np.r_[c0,c]

fig, axs, _ = gengrid(2, 2, size_inches=(7.2, 6.1), ticklabel_size=7, label_pos=-0.12)
a,b = axs[0]; c,d = axs[1]

# ═══ a) reactor architectures: delta shrinks (placeholder schematic) ═══════════
a.set_xlim(0,10); a.set_ylim(0,10); a.axis("off")
cells=[("unstirred\nbatch","300 µm",1.66,None),("stirred\nbatch","100 µm",1.4,"stir"),
       ("flow cell\n1 mm gap","30–60 µm",0.7,"flow"),("thin gap / RCE","<10 µm",0.25,"spin")]
for i,(nm,dl,filmw,icon) in enumerate(cells):
    x0=0.4+i*2.45
    a.add_patch(Rectangle((x0,2.6),2.0,4.6,fc="0.965",ec="0.55",lw=0.9))
    a.add_patch(Rectangle((x0+0.08,2.75),0.22,4.3,fc="0.35",ec="none"))
    a.add_patch(Rectangle((x0+0.30,2.75),filmw,4.3,fc=LBLUE,alpha=0.55,ec="none"))
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

# ═══ b) stirred beaker: crank the current (NPP profiles) ═══════════════════════
fan=pf[pf.case=="fan"]
ivals=sorted(fan.i_mAcm2.unique()); ivals=[ivals[0],ivals[1],ivals[2],ivals[4]]
shades=plt.cm.Blues(np.linspace(0.40,0.95,len(ivals)))
for col,i_app in zip(shades,ivals):
    g=fan[fan.i_mAcm2==i_app]; x,cn=with_surface(g)
    b.plot(x,cn,color=col,lw=1.5)
    lab=f"{i_app:.0f} mA cm$^{{-2}}$"+(" = $i_{lim}$" if i_app==ivals[-1] else "")
    b.text(1.8,cn[0]+0.025,lab,fontsize=5.0,color=col)
b.annotate("at $i_{lim}$ = 48 mA cm$^{-2}$ the electrode\nhas consumed everything the stirrer\ncan resupply — the '50 mA cm$^{-2}$\nbarrier' is this line, not the catalysis",
           xy=(20,0.20), xytext=(37,0.06), fontsize=5.3, color=BLUE,
           arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.8))
b.text(0.03,0.97,"0.5 M substrate, 1 e$^-$, D = 10$^{-9}$ m$^2$ s$^{-1}$\nstirred beaker, $\\delta$ = 100 $\\mu$m",
       transform=b.transAxes, fontsize=5.4, va="top", color="0.3")
b.set_xlim(0,100); b.set_ylim(0,1.05)
b.set_xlabel("distance from electrode ($\\mu$m)",fontsize=7.5)
b.set_ylabel("c$_S$ / C$_S$",fontsize=7.5)

# ═══ c) same chemistry at the barrier current, four reactors ═══════════════════
styles={"anec":(GREEN,"-",1.7),"flow":(BLUE,"-",1.7),
        "stirred":(RED,"--",1.4),"unstirred":("0.55","--",1.4)}
for case,(colr,ls,lw) in styles.items():
    g=pf[pf.case==case].sort_values("x_um"); x,cn=with_surface(g)
    delta=g.delta_um.iloc[0]
    x=np.r_[x,delta,300.0]; cn=np.r_[cn,1.0,1.0]
    c.plot(x,cn,color=colr,ls=ls,lw=lw)
c.text(104,0.92,"all at the barrier current, 50 mA cm$^{-2}$\n(dashed: shown at their own $i_{lim}$ —\n50 mA cm$^{-2}$ has no steady state)",
       fontsize=5.3, va="top", color="0.3")
c.text(295,0.335,"$\\delta$ = 10 $\\mu$m  thin gap / RCE:  c$_{surf}$ = 0.90",fontsize=5.2,color=GREEN,ha="right")
c.text(295,0.265,"$\\delta$ = 30 $\\mu$m  flow cell:  c$_{surf}$ = 0.69",fontsize=5.2,color=BLUE,ha="right")
c.text(295,0.195,"$\\delta$ = 100 $\\mu$m  stirred beaker:  starved ($i_{lim}$ = 48)",fontsize=5.2,color=RED,ha="right")
c.text(295,0.125,"$\\delta$ = 300 $\\mu$m  unstirred:  starved ($i_{lim}$ = 16)",fontsize=5.2,color="0.45",ha="right")
c.set_xlim(0,300); c.set_ylim(0,1.05)
c.set_xlabel("distance from electrode ($\\mu$m)",fontsize=7.5)
c.set_ylabel("c$_S$ / C$_S$",fontsize=7.5)

# ═══ d) all 50 x 6 architectures (EC'-coupled) ═════════════════════════════════
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
d.set_xticks(range(6)); d.set_xticklabels(labs6,fontsize=5.6,rotation=25,ha="right")
d.set_ylabel("$i_{lim}$, all 50 reactions (mA cm$^{-2}$)",fontsize=7.5)
h=[Line2D([0],[0],marker=m,ls="",ms=3.5,color=cc,label=t) for t,(m,cc) in mk.items()]
d.legend(handles=h,fontsize=5.0,frameon=False,loc="upper left",handletextpad=0.2,borderaxespad=0.15)

fig.tight_layout(h_pad=1.6, w_pad=2.0)
fig.savefig("figs/sec4_Fig4A.svg"); fig.savefig("figs/sec4_Fig4A.png",dpi=400)
print("Fig4A written")
