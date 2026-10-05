"""Section 4 figures from the Julia model outputs. customplot style, no titles.

2026-08 REMEDIATION (finding 10 of docs/FIGURE_PROVENANCE_AUDIT.md). FIG D used
to carry a THIRD thermal/ohmic model, disagreeing with both Fig. K and Fig. 4B:
unregistered electrolytes (0.1 M Bu4NPF6/THF kappa = 0.06 S/m, 0.1 M Bu4NBF4/DMF
0.35, MeCN 0.90, 1 M KOH aq 20.0), and — the harder error — a cooling comparison
made on the WRONG QUANTITY. Panel b plotted Joule heat FLUX (W/cm2) against three
shaded bands labelled "passive air" 0.005-0.02, "stirred liquid" 0.05-0.2 and
"engineered cooling" 1-10. Those numbers are heat-transfer COEFFICIENTS in Fig. K
(W/cm2 K); a flux and a coefficient are only comparable through a temperature
difference, which was never applied. Read literally, the old panel asserted that
passive air rejects 0.02 W/cm2 while Fig. K's own passive coefficient rejects
0.0144 W/cm2 K x (T_b - 25 K) = 0.59 W/cm2 for THF -- a factor of 30 apart.

FIG D now imports figs/thermal_model.py (the model of Fig. K): registry
electrolytes, gaps taken from the REACTORS table, and panel b re-expressed as the
required heat-rejection coefficient U'_req = q(i)/(T_b - T_amb), which is the
quantity the cooling bands are actually in.
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SEC4 = os.path.dirname(HERE)
for cand in (SEC4, HERE, os.path.expanduser("~/Documents/CO2R-Bulk-Scale-Julia-Model")):
    if os.path.exists(os.path.join(cand, "customplot.py")):
        sys.path.insert(0, cand); break
sys.path.insert(0, HERE)
# customplot reads the Berkeley swatch workbook by BARE FILENAME at import time, so
# without this the script only ran from Section4_Model/ and died on any other cwd.
# Same idiom as make_figs_sec34.py and make_fig_main.py. Every path this script reads
# or writes is already absolute (P() off SEC4, OUT() off HERE), so the chdir moves no
# number and changes no output filename -- it only makes the import work from anywhere.
os.chdir(SEC4)
from customplot import gengrid, rainbow_2, tableau20
from thermal_model import (SOLVENTS, REACTORS, COOLING_BANDS,
                           U_passive, q_Wcm2, E_cell, U_required)

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]
GREY=(0.55,0.55,0.55); THRESH=25.0
F=96485.33
SCOL={"THF":RED,"MeCN":LBLUE,"DMF":ORANGE,"aq. NaOH":BLUE}   # same as Fig. K / 4B

def P(*a):  return os.path.join(SEC4, *a)
def OUT(n): return os.path.join(HERE, n)

rx  = pd.read_csv(P("data","reactions_50.csv"))
t0  = pd.read_csv(P("julia","tier0_ec_matrix.csv"))
t0.columns = [c.strip() for c in t0.columns]
df  = pd.concat([rx.reset_index(drop=True), t0[["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]]], axis=1)
CARRIER_MK = {"substrate":"o", "mediator":"s", "catalyst":"^"}
# Keys are the KHL classes carried by reactions_50.csv since 2026-08-22 (the set was
# reclassified to match main-text Fig. 1b). The retired keys were C-N / C-C coupling /
# C-O / C-S / Ox (FGI) / Other/RN / Other bond.
CLS_COL = {"C-N formation":LBLUE, "C-C formation":GREEN, "Reduction":(0.98,0.42,0.42),
           "C-O formation":BLUE, "Oxidation":RED, "Cyclization":(0.55,0.78,0.55),
           "Halogenation":ORANGE, "C-S formation":rainbow_2[3],
           "Other bond formation":(0.45,0.45,0.5),
           "Multicomponent coupling":(0.35,0.55,0.85),
           "Functional group intraconversion":(0.75,0.75,0.75),
           "Isomerization":(0.85,0.80,0.60), "Unclassified":(0.60,0.60,0.60)}

# ── FIG A: i_lim vs delta, representative reactions + reactor bands ───────────
fig, ax, _ = gengrid(1,1, size_inches=(3.7,2.9), genlabels=False)
delta = np.logspace(np.log10(5e-6), np.log10(500e-6), 100)
picks = ["Anodic methoxylation of 4-tBu-toluene (Lysmeral)", "Kolbe homocoupling of 10-undecenoate",
         "Acrylonitrile hydrodimerization (ADN)", "Thioether -> sulfone (kilo-scale)",
         "Birch reduction of naphthalene", "Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)",
         "ACT-mediated alcohol oxidation (flow, hectogram)"]
labs  = ["BASF methoxylation (0.8 M)","Kolbe (1 M)","ADN (6.9 M)","sulfone, kilo-scale (0.47 M)",
         "Birch (0.14 M)","Ni-XEC (cat. 15 mM)","ACT-mediated (med. 25 mM)"]
cols  = [BLUE, GREEN, LBLUE, RED, (0.98,0.42,0.42), ORANGE, (0.45,0.45,0.5)]
for name,lab,c in zip(picks,labs,cols):
    r = df[df.reaction==name].iloc[0]
    il = 0.1*r.n_carrier*F*(r.D_cm2s*1e-4)*(r.C_carrier_M*1000)/delta
    ls = "--" if r.carrier_type!="substrate" else "-"
    ax.plot(delta*1e6, il, lw=1.5, color=c, ls=ls, label=lab)
ax.axhline(THRESH, color="0.3", ls=":", lw=1.1)
ax.text(5.6, THRESH*1.18, "25 mA cm$^{-2}$", fontsize=6, color="0.3")
# archetype bands: COMPUTED from the model's own films (min/max over the fifty rows, model_medians),
# never typed -- the typed bands this panel carried until 2026-09-07 (70-140 um "stirred", 20-60 um
# "flow") had drifted from the archetypes they named.
import model_medians as _MM
_BANDS = [("unstirred", ["natural"]), ("stirred", ["stirred"]), ("flow", ["flow"]),
          ("ANEC", ["anec"]), ("micro /\nRDE / RCE", ["micro", "rde", "rce"])]
for lab, keys in _BANDS:
    x0 = min(_MM.delta_range(k)[0] for k in keys); x1 = max(_MM.delta_range(k)[1] for k in keys)
    if x1 <= x0 * 1.02:
        x0, x1 = x0 / 1.06, x1 * 1.06            # a fixed film: draw a thin band around it
    ax.axvspan(x0,x1,color=BLUE,alpha=0.06)
    ax.text(np.sqrt(x0*x1), 3800, lab, fontsize=5.2, ha="center", color=BLUE)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(5,500); ax.set_ylim(0.5,9000)
ax.set_xlabel("Diffusion-layer thickness $\\delta$ ($\\mu$m)", fontsize=8.5)
ax.set_ylabel("Limiting current density (mA cm$^{-2}$)", fontsize=8.5)
ax.legend(fontsize=5.0, frameon=False, loc="lower left", handlelength=1.6)
fig.tight_layout(); fig.savefig(OUT("sec4_figA_ilim_vs_delta.svg")); fig.savefig(OUT("sec4_figA_ilim_vs_delta.png"),dpi=600); plt.close(fig)

# ── FIG B: i_lim (flow cell) vs carrier concentration, all 50 ────────────────
fig, ax, _ = gengrid(1,1, size_inches=(3.7,2.9), genlabels=False)
for _,r in df.iterrows():
    ax.scatter(r.C_carrier_M, r["flow"], s=26, marker=CARRIER_MK[r.carrier_type],
               color=CLS_COL[r.cls], edgecolor="white", lw=0.4, zorder=3)
ax.axhline(THRESH, color="0.3", ls=":", lw=1.1)
nb = (df["flow"]<THRESH).sum()
ax.text(0.0045, THRESH*1.25, f"{nb}/50 below threshold", fontsize=6.5, color="0.25")
# guide slope i ∝ C
Cg = np.logspace(-2.5,0.4,10)
ax.plot(Cg, 0.1*2*F*8e-10*Cg*1000/50e-6*np.ones_like(Cg)*0+0.1*2*F*8e-10*(Cg*1000)/5.0e-5, color="0.85", lw=0.8, zorder=1)
from matplotlib.lines import Line2D
h1=[Line2D([0],[0],marker=m,ls="",ms=4.5,color="0.35",label=k) for k,m in CARRIER_MK.items()]
ax.legend(handles=h1, fontsize=5.4, frameon=False, loc="lower right", title="current carrier", title_fontsize=5.8)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(0.003,3); ax.set_ylim(0.4,3000)
ax.set_xlabel("Current-carrier concentration (M)", fontsize=8.5)
ax.set_ylabel("$i_{lim}$ in parallel-plate flow cell (mA cm$^{-2}$)", fontsize=8.5)
fig.tight_layout(); fig.savefig(OUT("sec4_figB_ilim_vs_C.svg")); fig.savefig(OUT("sec4_figB_ilim_vs_C.png"),dpi=600); plt.close(fig)

# ── FIG C: 50 × 7 heatmap ─────────────────────────────────────────────────────
order_cls = ["C-C formation","Cyclization","C-N formation","Oxidation","C-O formation",
             "Reduction","Multicomponent coupling","Functional group intraconversion",
             "Halogenation","Other bond formation","C-S formation","Isomerization",
             "Unclassified"]
df["_c"]=pd.Categorical(df.cls, order_cls); dfs=df.sort_values(["_c","flow"], ascending=[True,False]).reset_index(drop=True)
cols6=["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
labs6=["unstirred\nbatch","stirred\nbatch","recirculating\nflow cell","ANEC\nflow cell","microfluidic\n25 $\\mu$m","RDE\n1600 rpm","RCE\n3000 rpm"]
M=np.log10(dfs[cols6].values.astype(float))
fig, ax, _ = gengrid(1,1, size_inches=(6.4,7.6), genlabels=False, minor=False)
pc=ax.pcolormesh(np.arange(len(cols6)+1), np.arange(51), M, cmap="RdYlBu", vmin=-1, vmax=3.2, edgecolors="white", linewidth=0.4)
# threshold hatch: mark cells below 25
for i in range(50):
    for j in range(len(cols6)):
        if dfs[cols6[j]].iloc[i] < THRESH:
            ax.plot(j+0.5, i+0.5, marker="x", ms=3.2, color="0.15", mew=0.9, zorder=4)
ax.set_xticks(np.arange(len(cols6))+0.5); ax.set_xticklabels(labs6, fontsize=6.0)
short=[n if len(n)<=42 else n[:40]+"…" for n in dfs.reaction]
mk={"substrate":"","mediator":" [M]","catalyst":" [C]"}
ax.set_yticks(np.arange(50)+0.5)
ax.set_yticklabels([s+mk[c] for s,c in zip(short,dfs.carrier_type)], fontsize=4.6)
ax.tick_params(length=0); ax.invert_yaxis()
# class separators
brk=dfs.groupby("_c",observed=True).size().cumsum().values[:-1]
for b in brk: ax.axhline(b, color="0.2", lw=0.8)
for j,c in enumerate(cols6):
    nbel=(dfs[c]<THRESH).sum()
    ax.text(j+0.5, 51.6, f"{50-nbel}/50\n$\\geq$25", ha="center", fontsize=6, color="0.2")
cb=fig.colorbar(pc, ax=ax, fraction=0.035, pad=0.02)
cb.set_label("log$_{10}$ $i_{lim}$ (mA cm$^{-2}$)", fontsize=7); cb.ax.tick_params(labelsize=6)
ax.set_ylim(52.4,-0.2)
fig.tight_layout(); fig.savefig(OUT("sec4_figC_heatmap.svg")); fig.savefig(OUT("sec4_figC_heatmap.png"),dpi=600); plt.close(fig)

# ── FIG D: cell voltage + the cooling duty it implies (figK thermal model) ────
# Scenarios: the four registry electrolytes of thermal_model.SOLVENTS at the 5 mm
# flow-cell gap (REACTORS[2]), plus the same DMF at the 250 um microfluidic gap
# (REACTORS[3]). One variable per curve, every kappa carrying a registry row.
GAP_FLOW=REACTORS[2][1]; GAP_THIN=REACTORS[3][1]
_dmf=[s for s in SOLVENTS if s[0]=="DMF"][0]
scen=[(lab,kap,GAP_FLOW,Tb,SCOL[lab],f"{lab}, {GAP_FLOW*1e3:.0f} mm")
      for lab,el,kap,Tb,prov in SOLVENTS]
scen.append(("DMF",_dmf[2],GAP_THIN,_dmf[3],GREEN,f"DMF, {GAP_THIN*1e6:.0f} $\\mu$m"))

# 1 col x 2 rows (gengrid takes n_cols, n_rows); the pre-existing 2.9 in height
# left both panels ~1.2 in tall and clipped the y-labels.
fig, axes, _ = gengrid(1,2, size_inches=(6.8,5.0), ticklabel_size=8)
a,b=axes
ii=np.linspace(1,300,200)
for lab,k,g,Tb,c,leg in scen:
    a.plot(ii,E_cell(ii,k,g),lw=1.5,color=c,label=leg)
a.axhspan(10,20,color="0.92",zorder=0); a.text(292,11.2,"reported academic\nnon-aqueous cells",fontsize=5.4,color="0.4",ha="right")
a.axvline(THRESH,color="0.3",ls=":",lw=1)
a.set_xlabel("Current density (mA cm$^{-2}$)",fontsize=8.5); a.set_ylabel("Cell voltage (V)",fontsize=8.5)
a.set_xlim(0,300); a.set_ylim(0,60); a.legend(fontsize=5.2,frameon=False,loc="upper left",bbox_to_anchor=(0.04,1.0))

# Panel b: the cooling DUTY, in the same units as the cooling classes. Plotting
# heat flux against coefficient bands (the previous version) compared W/cm2 with
# W/cm2 K. U'_req = q(i)/(T_b - T_amb) is the quantity the bands are in.
for nm,lo,hi,cshade in COOLING_BANDS:
    b.axhspan(lo,hi,color=cshade,alpha=0.6,zorder=0)
    b.text(1.15,np.sqrt(lo*hi),nm.replace("\n"," "),fontsize=5,color="0.30",va="center")
for lab,k,g,Tb,c,leg in scen:
    b.plot(ii,U_required(ii,k,g,Tb),lw=1.5,color=c)
for idx,ls,xt,ha in [(2,"--",1.15,"left"),(3,":",295,"right")]:
    rl,L,sig,hi_,iop=REACTORS[idx]
    b.axhline(U_passive(sig,hi_),color="0.25",ls=ls,lw=1.0)
    b.text(xt,U_passive(sig,hi_)*1.15,f"passively available: {rl.replace(chr(10),' ')}",
           fontsize=5.2,color="0.25",ha=ha,va="bottom")
b.set_xscale("log"); b.set_yscale("log")
b.set_xlabel("Current density (mA cm$^{-2}$)",fontsize=8.5)
b.set_ylabel("Required $U'$ to avoid boiling (W cm$^{-2}$ K$^{-1}$)",fontsize=8.5)
b.set_xlim(1,300); b.set_ylim(1e-5,3)
fig.tight_layout(); fig.savefig(OUT("sec4_figD_voltage_joule.svg")); fig.savefig(OUT("sec4_figD_voltage_joule.png"),dpi=600); plt.close(fig)

# ── FIG E (SI): NPP migration enhancement + profiles ─────────────────────────
# 2026-08-02 correction. This block used to carry a comment and an else-branch
# asserting that julia/npp_support_sweep.csv and julia/npp_profiles.csv "are NOT
# present in this repository", that Fig. E "cannot be regenerated here" and that
# the committed renders were "produced elsewhere". That was false on all three
# counts. Both files are present and are written by julia/run_section4.jl (lines
# 57 and 69, and named in its own output list at lines 3-4). They also reproduce
# the SI's own quoted numbers exactly: the sweep gives i_lim/i_Fick = 2.00, 1.38,
# 1.18, 1.04 at support ratios 0, 0.25, 1, 5, and the profiles give a film
# potential drop of 57.3 mV (SR0) falling to 1.1 mV (SR10) -- which is verbatim
# what SI Sec. S5.3 states. Fig. E is a normal, reproducible SI figure.
# The existence guard is kept, but only as a genuine missing-input error: if the
# CSVs are absent the fix is to run julia/run_section4.jl, not to declare the
# figure unreproducible.
_E_IN=[P("julia","npp_support_sweep.csv"), P("julia","npp_profiles.csv")]
if all(os.path.exists(f) for f in _E_IN):
    sw=pd.read_csv(_E_IN[0]); pr=pd.read_csv(_E_IN[1])
    fig, axes, _ = gengrid(1,2, size_inches=(6.6,2.8), ticklabel_size=8)
    a,b=axes
    a.semilogx(sw.support_ratio.replace(0,0.05), sw.ilim_over_fick, "o-", color=BLUE, ms=4, lw=1.4)
    a.axhline(2.0,color=RED,ls="--",lw=1); a.text(0.07,2.04,"binary-electrolyte limit (2.00)",fontsize=6,color=RED)
    a.axhline(1.0,color="0.4",ls=":",lw=1); a.text(4,1.03,"Fickian ($i_{lim}=nFDC/\\delta$)",fontsize=6,color="0.35")
    a.set_xlabel("Support ratio $C_{elec}/C_{substrate}$",fontsize=8.5)
    a.set_ylabel("$i_{lim}$ / $i_{lim,Fick}$",fontsize=8.5); a.set_ylim(0.9,2.15)
    for tag,c,lab in [("SR0",RED,"no support"),("SR10",BLUE,"SR = 10")]:
        d=pr[pr.case==tag]
        b.plot(d.x_um,d.c_S_norm,color=c,lw=1.5,label=f"{lab}: c$_S$/c$_b$")
        b.plot(d.x_um,d.phi_mV/50,color=c,lw=1.2,ls="--")
    b.set_xlabel("Distance from electrode ($\\mu$m)",fontsize=8.5)
    b.set_ylabel("c$_S$/c$_{bulk}$ (—),  $\\phi$/50 mV (- -)",fontsize=8.5)
    b.legend(fontsize=5.6,frameon=False,loc="lower right")
    fig.tight_layout(); fig.savefig(OUT("sec4_figE_npp.svg")); fig.savefig(OUT("sec4_figE_npp.png"),dpi=600); plt.close(fig)
else:
    raise FileNotFoundError(
        "FIG E inputs missing: "
        + ", ".join(os.path.relpath(f,SEC4) for f in _E_IN if not os.path.exists(f))
        + " — run julia/run_section4.jl, which writes both (run_section4.jl:57,69). "
          "Fig. E is cited in SI Sec. S5.3 and must not be left stale.")

# which reactions remain below threshold in the BEST reactor
best=df[["rde","rce","anec","micro"]].max(axis=1)
stuck=df[best<THRESH][["reaction","carrier_type","C_carrier_M"]]
print("STUCK below 25 mA/cm2 even in best reactor:"); print(stuck.to_string(index=False))
print("\ncounts by carrier:", df.assign(stuck=best<THRESH).groupby("carrier_type").stuck.sum().to_dict())
print("figures written")
