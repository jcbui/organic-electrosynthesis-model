"""FigF: the engineering-gap chart (batch -> engineered reactor, per reaction).
FigG: paired waterfalls — the two engineering levers that break the 50 mA/cm2 barrier.
customplot style, no titles.

Runnability remediation, 2026-08-02: the two `/home/claude/rce` hardcodes on the old
lines 6 and 8 made this file — the SOLE generator of SI Fig. F and Fig. G, both cited
in make_si.js — unrunnable anywhere in this repository, freezing both renders at
2026-07-12. Paths now resolve relative to this file, matching make_figs_sec34.py."""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, sys, os

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
df["best"]=df[["anec","micro","rde","rce"]].max(axis=1)

# ── FIG F: gap chart ──────────────────────────────────────────────────────────
order={"substrate":0,"mediator":1,"catalyst":2}
dfs=df.assign(_o=df.carrier_type.map(order)).sort_values(["_o","natural"],ascending=[True,False]).reset_index(drop=True)
fig, ax, _ = gengrid(1,1, size_inches=(6.6,7.6), genlabels=False, minor=False)
ax.axvspan(0.05, OPER, color="0.93", zorder=0)
ax.text(0.4, -1.7, "pharma operating reality: 10/14 scale-ups < 25 (Ferretti 2025)", fontsize=6.0, color="0.35", style="italic")
ax.axvline(OPER, color="0.55", ls=":", lw=1.0)
ax.axvline(BARRIER, color="0.15", ls="-", lw=1.3)
ax.text(BARRIER*1.12, -0.5, "the 50 mA cm$^{-2}$ barrier: 1/14 exceed", fontsize=6.0, color="0.15", style="italic")
for i,r in dfs.iterrows():
    y=i
    col = GREEN if r.best>=BARRIER else (ORANGE if r.best>=OPER else RED)
    ax.plot([r.natural, r.best],[y,y], color=col, lw=1.1, zorder=3, alpha=0.85)
    ax.plot(r.natural, y, marker="o", ms=3.4, mfc="white", mec=col, mew=1.0, zorder=4)
    ax.plot(r.best, y, marker=">", ms=4.2, color=col, zorder=4)
mk={"substrate":"","mediator":"  [M]","catalyst":"  [C]"}
short=[n if len(n)<=44 else n[:42]+"…" for n in dfs.reaction]
ax.set_yticks(range(50)); ax.set_yticklabels([s+mk[c] for s,c in zip(short,dfs.carrier_type)], fontsize=4.6)
ax.tick_params(axis="y", length=0); ax.invert_yaxis()
brk=dfs.groupby("_o").size().cumsum().values[:-1]
for b in brk: ax.axhline(b-0.5, color="0.25", lw=0.9)
for y0,lab in [(16,"substrate-carried"),(36.2,"mediator-carried"),(45.0,"catalyst-carried")]:
    ax.text(2450, y0, lab, fontsize=6.4, rotation=270, va="center", color="0.25")
ax.set_xscale("log"); ax.set_xlim(0.05,3000); ax.set_ylim(50.6,-2.4)
ax.set_xlabel("Transport-limited current density (mA cm$^{-2}$)", fontsize=9)
# legend: what the ends mean + outcome colors
from matplotlib.lines import Line2D
h=[Line2D([0],[0],marker="o",ls="",ms=4,mfc="white",mec="0.3",label="unstirred batch cell"),
   Line2D([0],[0],marker=">",ls="",ms=5,color="0.3",label="best engineered reactor\n(ANEC / microfluidic / RDE / RCE)"),
   Line2D([0],[0],ls="-",lw=1.6,color=GREEN,label=f"crosses 50 mA cm$^{{-2}}$ ({int((dfs.best>=BARRIER).sum())}/50)"),
   Line2D([0],[0],ls="-",lw=1.6,color=ORANGE,label="reaches 25–50"),
   Line2D([0],[0],ls="-",lw=1.6,color=RED,label=f"transport-capped by dilute carrier ({int((dfs.best<OPER).sum())}/50)")]
fig.legend(handles=h, fontsize=5.6, frameon=False, loc="lower center", ncol=3, bbox_to_anchor=(0.56,-0.005), columnspacing=1.4, handlelength=1.6)
ax.text(0.062, 2.1, "same chemistry, same concentration —\nonly the reactor changes", fontsize=6.2, color="0.25", style="italic")
fig.tight_layout(rect=(0,0.035,1,1)); fig.savefig("figs/sec4_figF_gap.svg"); fig.savefig("figs/sec4_figF_gap.png",dpi=600); plt.close(fig)

# ── FIG G: paired waterfalls ─────────────────────────────────────────────────
fig, axes, _ = gengrid(1,2, size_inches=(6.8,3.0), ticklabel_size=7.5)
a,b=axes
def waterfall(ax, vals, labels, cols, barrier_note=True):
    x=np.arange(len(vals))
    ax.bar(x, vals, color=cols, width=0.62, zorder=3)
    for k in range(len(vals)-1):
        ax.plot([x[k]+0.31, x[k+1]-0.31],[vals[k],vals[k]], color="0.55", lw=0.8, ls=":", zorder=2)
        mult=vals[k+1]/vals[k]
        ax.text(x[k]+0.5, np.sqrt(vals[k]*vals[k+1]), f"×{mult:.1f}", fontsize=5.6, ha="center", color="0.3")
    ax.axhline(BARRIER, color="0.15", lw=1.2)
    ax.axhline(OPER, color="0.55", ls=":", lw=1.0)
    ax.set_yscale("log"); ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=5.6, rotation=32, ha="right")
    ax.set_ylim(0.15, 3000)

# left: dehydrogenative lactonization (substrate-carried, SI-verified 0.0625 M) — reactor levers
r=df[df.reaction.str.contains("Dehydrogenative lactonization")].iloc[0]
valsL=[r.natural, r.stirred, r.flow, r.anec, r.micro, r.rce, r.rce*2]
labsL=["unstirred\nbatch","stirred\nbatch","recirculating\nflow cell","ANEC\nflow cell","microfluidic\n25 $\\mu$m","RCE\n3000 rpm","RCE +\n2× conc. (0.125 M)"]
colsL=[BLUE]*6+[GREEN]
waterfall(a, valsL, labsL, colsL)
a.set_ylabel("$i_{lim}$ (mA cm$^{-2}$)", fontsize=8.5)
a.text(0.02,0.955,"dehydrogenative C–H/O–H lactonization (K. Xu/Zeng 2018): substrate-carried, 0.0625 M (verified)",
       transform=a.transAxes, fontsize=6.4, va="top")
a.text(6.45, 58, "50", fontsize=5.5, color="0.15", ha="right")
a.text(6.45, 19.5, "25: industry ceiling", fontsize=5.2, color="0.45", ha="right")

# right: Ni-catalyzed amination (catalyst-carried, 10 mM) — reactor levers stall
r2=df[df.reaction.str.contains("Ni-catalyzed aryl amination")].iloc[0]
valsR=[r2.natural, r2.stirred, r2.flow, r2.anec, r2.micro, r2.rce, r2.rce*5]
labsR=["unstirred\nbatch","stirred\nbatch","recirculating\nflow cell","ANEC\nflow cell","microfluidic\n25 $\\mu$m","RCE\n3000 rpm","RCE +\n5× cat. (25 mM)"]
colsR=[RED]*6+[GREEN]
waterfall(b, valsR, labsR, colsR)
b.text(0.02,0.955,"Ni-catalyzed amination: current carried by 5 mM catalyst (verified)",
       transform=b.transAxes, fontsize=6.4, va="top")
b.text(0.02,0.86,"reactor levers alone never cross the barrier;\nthe missing lever is carrier concentration",
       transform=b.transAxes, fontsize=5.6, va="top", color=RED)
fig.tight_layout(); fig.savefig("figs/sec4_figG_waterfall.svg"); fig.savefig("figs/sec4_figG_waterfall.png",dpi=600); plt.close(fig)
print("F endpoints: batch>=50:",(df.natural>=BARRIER).sum(),"best>=50:",(df.best>=BARRIER).sum())
print("sulfone chain:", [round(v,1) for v in valsL]); print("NiAm chain:", [round(v,2) for v in valsR])
