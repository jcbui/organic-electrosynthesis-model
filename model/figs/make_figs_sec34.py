"""Regrouped Section 3 / Section 4 figures.
  Fig sec3  : (a) reactor schematic  (b) delta-ladder  (c) substrate starvation
  Fig sec4c : (a) barrier-crossing profiles  (b) 50-reaction x 7-architecture scatter
4B-ac and 4B-def are unchanged (built by make_fig4B.py).

Provenance remediation, 2026-08-02 (figure-provenance-audit findings 2, 3, 4):
  * F3  the ladder's `C = 1740` is no longer hardcoded. It is computed at import time
        by model_medians.guide_constant() as the all-50 median i_lim at the stirred
        archetype x 200 um -- the one archetype where delta is exactly 200 um for every
        row, so the median needs no assumption about which reaction is typical.
  * F4  the single "RDE / RCE" anchor at delta = 14 um (which is neither: the model's
        medians are RDE 12.65 um, RCE 10.94 um) is replaced by all six archetypes
        plotted at their computed median delta. The guide line is a 1/delta reference
        anchored at the stirred median, not `nFDC/delta` for any reaction, and it
        overstates the thin-film medians because delta_eff correlates with D across the
        corpus -- stated in the caption, not on the figure.
  * F2  the starvation panel's exemplar (0.5 M, 1 e-, D = 1e-9) is one specific system
        and is shown against the corpus substrate median (0.1 M, 2 e-, D = 1.394e-9,
        julia/run_profiles_median.jl). The normalised fan is identical for the two to
        5 decimal places (asserted below), so one set of curves is drawn.

Redesign, 2026-09-07 (author instruction: "we have figure captions, we don't need the text to
be in the figures"). Every title, annotation paragraph and on-figure sentence is gone; the
schematic is redrawn in the group's flat schematic style (figs/figstyle.py) with no text at all.
The numbers those annotations carried are still computed here and printed to stdout, and the
caption states them (gated by data/check_ms_derived.py). Nothing about the data changed.
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, matplotlib as mpl, matplotlib.pyplot as plt, sys, os
from matplotlib.lines import Line2D

# ── portable paths: resolve everything relative to this file, not /home/claude/rce ──
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.chdir(ROOT)          # customplot reads the Berkeley swatch workbook from cwd at import
from customplot import gengrid, rainbow_2
import model_medians as MM
import figstyle as FS
def _find(*cands):
    for c in cands:
        if os.path.exists(os.path.join(ROOT, c)): return os.path.join(ROOT, c)
    raise FileNotFoundError(cands)

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]
BARRIER=50.0; OPER=25.0
# type scale at the PRINTED width (the figures are drawn at 6.5 in, 1:1 on the page): nothing under 7 pt
TICK, ANN, AX, TIER = 7.0, 7.5, 8.5, 8.0

rx=pd.read_csv(_find("reactions_50.csv","data/reactions_50.csv"))
t0=pd.read_csv(_find("julia/tier0_ec_matrix.csv"))
df=pd.concat([rx.reset_index(drop=True), t0[["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]]],axis=1)
pf=pd.read_csv(_find("julia/profiles_direct.csv"))
pfm=pd.read_csv(_find("julia/profiles_direct_median.csv"))   # F2: corpus-median companion run

def style(ax, ts=TICK):
    ax.tick_params(axis="x", which="both", direction="in", top=True, labelsize=ts)
    ax.tick_params(axis="y", which="both", direction="in", right=True, labelsize=ts)
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    [s.set_linewidth(1.25) for s in ax.spines.values()]

def with_surface(g):
    x=g.x_um.values; c=g.c_norm.values
    c0=max(c[0]-(c[1]-c[0])*x[0]/(x[1]-x[0]),0.0)
    return np.r_[0.0,x], np.r_[c0,c]

# ───────────────────────── panel draw functions ─────────────────────────────
def draw_schematic(a, w_in, h_in):
    """Six archetypes, left to right in order of thinning film: unstirred batch, stirred batch,
    recirculating flow cell (Watkins 2023's parallel-inlet H-cell), the ANEC flow cell (inlet angled
    20 degrees toward the working electrode), the 25 um microfluidic cell (Mo 2020) and the rotating
    cylinder. The film drawn beside the working electrode is the archetype's film (model_medians:
    fixed for the five measured/derived cells, the median for the cylinder) on one scale for the
    four open cells; the microfluidic channel and the cylinder are cartoons of their geometry (the
    caption says so). Two label lines under each cell.

    2026-09-22 (author): the ROTATING DISK was missing -- panel (b) plots seven architectures and the caption names
    seven, while this panel drew six. It is drawn now, between the microfluidic cell and the cylinder: the shaft and
    its disk seen edge-on, the film BELOW the disk face (the only horizontal film in the figure), the counter
    electrode on the far wall."""
    # data units are inches: the drawing spans the full axes box, which spans panels b and c
    a.set_xlim(0, w_in); a.set_ylim(0, h_in); a.set_aspect("equal"); a.axis("off")
    LAB = 0.58                                 # inches reserved under the cells for the label lines
    G = 0.22                                   # gap between cells
    KEYS = ("natural", "stirred", "flow", "anec", "micro", "rde", "rce")
    N = len(KEYS)
    W = (w_in - (N - 1) * G) / N; H = h_in - LAB - 0.04; Y0 = LAB
    NAMES = {"natural": "unstirred\nbatch", "stirred": "stirred\nbatch", "flow": "recirculating\nflow cell",
             "anec": "ANEC\nflow cell", "micro": "microfluidic\n25 µm gap", "rde": "rotating\ndisk",
             "rce": "rotating\ncylinder"}
    XS = [i * (W + G) for i in range(N)]
    delta = {k: MM.delta_median(k) for k in KEYS}
    SCALE = (W - 0.28) / 450.0                 # electrolyte width per um of film, open cells
    for i, (key, x) in enumerate(zip(KEYS, XS)):
        FS.frame(a, x, Y0, W, H)
        a.text(x + W / 2, Y0 - 0.07, NAMES[key], ha="center", va="top", fontsize=ANN, color="0.2", linespacing=1.05)
        a.text(x + W / 2, Y0 - 0.41, "$\\delta$ ≈ %.0f µm" % delta[key] if key != "micro" else "$\\delta$ = %.1f µm" % delta[key],
               ha="center", va="top", fontsize=ANN, color=BLUE)
        ex, ey, ew, eh = x + 0.06, Y0 + 0.06, 0.09, H - 0.12   # working-electrode slab
        cx_ce = x + W - 0.06 - ew                              # counter electrode on the far wall
        SGN_Y = ey + eh - 0.10                                 # the + / - sit at the top of the electrolyte
        if key in ("natural", "stirred"):
            FS.electrolyte(a, ex, ey, W - 0.12, eh)
            FS.film(a, ex + ew, ey, delta[key] * SCALE, eh)
            FS.electrode(a, ex, ey, ew, eh)
            FS.electrode(a, cx_ce, ey, ew, eh, color=FS.ELECTRODE_CE)
            FS.sign(a, ex + ew + 0.07, SGN_Y, "+"); FS.sign(a, cx_ce - 0.07, SGN_Y, "−")
            if key == "stirred":
                FS.stir_bar(a, (ex + ew + cx_ce) / 2, ey + 0.13, 0.34 * W, 0.028, angle=0)   # centred between the two electrodes
        elif key == "flow":
            # recirculating cell, inlet parallel to the plates: electrolyte flows ALONG the working electrode
            FS.electrolyte(a, ex, ey, W - 0.12, eh)
            FS.film(a, ex + ew, ey, delta[key] * SCALE, eh)
            FS.electrode(a, ex, ey, ew, eh)
            FS.electrode(a, cx_ce, ey, ew, eh, color=FS.ELECTRODE_CE)
            FS.sign(a, ex + ew + 0.07, SGN_Y, "+"); FS.sign(a, cx_ce - 0.07, SGN_Y, "−")
            gmid = ((ex + ew) + cx_ce) / 2                        # centre of the gap
            for xx in (gmid - 0.15 * W, gmid, gmid + 0.15 * W):
                FS.arrow(a, (xx, ey + 0.20 * eh), (xx, ey + 0.80 * eh), ms=6, lw=0.9)
        elif key == "anec":
            # the ANEC cell: recirculating, with the inlet angled 20 degrees TOWARD the working electrode, so
            # the jet impinges obliquely on its face; the inlet port sits low on the far wall, three parallel
            # streamlines leave it at 20 degrees off the electrode plane and end on the electrode face at three
            # heights, and the flow returns along the top
            FS.electrolyte(a, ex, ey, W - 0.12, eh)
            FS.film(a, ex + ew, ey, delta[key] * SCALE, eh)
            FS.electrode(a, ex, ey, ew, eh)
            FS.electrode(a, cx_ce, ey, ew, eh, color=FS.ELECTRODE_CE)
            FS.sign(a, ex + ew + 0.07, ey + eh - 0.06, "+"); FS.sign(a, cx_ce - 0.07, ey + eh - 0.06, "−")
            # a true 20-degree jet would need a cell three times taller than wide to cross the gap, so the
            # cartoon draws the impingement at 35 degrees; the caption states the real angle
            th = np.deg2rad(35.0); sn, cs = np.sin(th), np.cos(th)
            xend = ex + ew + 0.025; y_start = ey + 0.08 * eh
            for fy in (0.30, 0.50, 0.70):                                # streamlines end on the electrode face
                yend = ey + fy * eh; L_ = (yend - y_start) / cs
                FS.arrow(a, (xend + sn * L_, y_start), (xend, yend), ms=6, lw=0.9)
            px = xend + sn * (ey + 0.70 * eh - y_start) / cs             # the port sits where the streamlines start
            a.add_patch(mpl.patches.Rectangle((px - 0.02, y_start - 0.055), min(0.14 * W, cx_ce - px), 0.05,
                                              fc=FS.STEEL, ec=FS.EDGE, lw=0.5, zorder=7))
            FS.arrow(a, (ex + ew + 0.05, ey + 0.82 * eh), (cx_ce - 0.05, ey + 0.82 * eh), ms=6, lw=0.8, rad=0.30)   # return flow
        elif key == "micro":
            # the microfluidic cell: two plates at a 25 um gap, drawn as a narrow channel between them; the film
            # is the half-gap, so it spans half the channel
            gap = 0.28 * W; gx0 = x + W / 2 - gap / 2
            FS.electrolyte(a, gx0, ey, gap, eh)
            FS.film(a, gx0, ey, gap * delta["micro"] / 25.0, eh)
            FS.electrode(a, gx0 - ew, ey, ew, eh)
            FS.electrode(a, gx0 + gap, ey, ew, eh, color=FS.ELECTRODE_CE)
            FS.sign(a, gx0 - ew - 0.07, SGN_Y, "+"); FS.sign(a, gx0 + gap + ew + 0.07, SGN_Y, "−")
            for yy in (ey + 0.18 * eh, ey + 0.56 * eh):
                FS.arrow(a, (gx0 + 0.5 * gap, yy), (gx0 + 0.5 * gap, yy + 0.24 * eh), ms=5, lw=0.8)
        elif key == "rde":
            # rotating disk: a shaft carrying a disk electrode, seen edge-on, with the film below the disk face
            FS.electrolyte(a, ex, ey, W - 0.12, eh)
            cx = x + W / 2 - 0.06
            dw, dh = 0.40 * W, 0.05                       # disk seen edge-on
            dy = ey + 0.34 * eh
            fw = max(delta[key] * SCALE, 0.012)
            FS.film(a, cx - dw / 2, dy - fw, dw, fw, down=True)
            FS.electrode(a, cx - 0.028, dy + dh, 0.056, ey + eh - (dy + dh), color=FS.ELECTRODE_CE, z=5)   # shaft
            FS.electrode(a, cx - dw / 2, dy, dw, dh)                                                       # the disk
            FS.electrode(a, cx_ce, ey, ew, eh, color=FS.ELECTRODE_CE)                                      # counter
            FS.sign(a, cx - dw / 2 - 0.055, dy + dh / 2, "+"); FS.sign(a, cx_ce - 0.07, SGN_Y, "−")
            # the rotation loop rides on the SHAFT at mid height rather than up at the sign row: the disk is wide, so
            # there is no clear space beside it, and at SGN_Y the loop runs into the counter electrode's "−" and the
            # two read as one mark (author, 2026-09-22)
            FS.spin_arrow(a, cx, dy + dh + 0.30 * (ey + eh - dy - dh), 0.098, 0.036, ms=7, lw=0.9)
        else:
            # rotating cylinder: the working electrode is the cylindrical jacket around the electrolyte and the
            # whole jacket rotates -- side view, two curved walls with a rim on top and the film on each inner face
            xl, xr = x + 0.11, x + W - 0.11 - ew
            top = ey + 0.78 * eh
            fw = max(delta["rce"] * SCALE, 0.012)
            FS.electrolyte(a, xl + ew, ey, xr - xl - ew, top - ey)
            FS.film(a, xl + ew, ey, fw, top - ey)
            FS.film(a, xr - fw, ey, fw, top - ey, flip=True)
            FS.electrode(a, xl, ey, ew, top - ey); FS.electrode(a, xr, ey, ew, top - ey)
            FS.electrode(a, x + W / 2 - 0.026, ey + 0.04, 0.052, top - ey - 0.04, color=FS.ELECTRODE_CE, z=7)   # axial counter rod, wide enough to carry its sign
            # 2026-09-21 (Connor Coley, review comment 19): the jacket is one working electrode, so it carries "+" on
            # BOTH inner faces and the axial counter rod carries "−". 2026-09-22: the first attempt put the right "+"
            # out in the electrolyte with the "−" just under it, so the two read as one "±" cluster and the rod -- the
            # actual counter electrode -- was unlabelled. Each sign now sits ON the electrode it names, all at one
            # height: "+" hugging each jacket face, "−" centred on the rod.
            sgn_y = ey + 0.45 * (top - ey)
            FS.sign(a, xl + ew / 2, sgn_y, "+"); FS.sign(a, xr + ew / 2, sgn_y, "+")   # on the jacket itself
            FS.sign(a, x + W / 2, sgn_y, "−", size=6.5)   # ON the rod, as each "+" sits on its jacket; beside it the
            # minus reads as the left jacket's, and at full size on a thin rod it reads as a break in the rod
            rim_w, rim_h = xr + ew - xl, 0.16 * W
            a.add_patch(mpl.patches.Ellipse((x + W / 2, top), rim_w, rim_h, fc=FS.ELECTROLYTE, ec=FS.EDGE, lw=0.9, zorder=8))
            FS.spin_arrow(a, x + W / 2, top, rim_w / 2 + 0.06, rim_h / 2 + 0.035, z=9, ms=7, lw=0.95)

def draw_ladder(ax):
    # ── F3: guide constant computed at runtime, never hardcoded ────────────────
    C = MM.guide_constant()
    ANCH = [(k, MM.delta_median(k), MM.ilim_median(k)) for k in
            ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]]
    D_MIN = min(MM.delta_range(k)[0] for k in MM.ARCHETYPES)   # model floor (um)
    ## TIER BANDS ARE COMPUTED FROM THE ARCHETYPES EACH CLASS CONTAINS, not typed (see the
    ## 2026-08-31 note in CLAUDE.md): each band is the delta_eff range of its own members, so
    ## the ladder and the markers cannot disagree. Tier 4 (GDE/MEA) holds no modelled archetype
    ## and runs from the model floor down off the axis.
    _TG=[("Tier 1",["natural","stirred"],"#E9F1F7"),("Tier 2",["flow","anec"],"#CFE2EF"),
         ("Tier 3",["micro","rde","rce"],"#A9CCE3")]
    TIERS=[]
    for _lab,_ks,_c in _TG:
        _lo=min(MM.delta_range(k)[0] for k in _ks); _hi=max(MM.delta_range(k)[1] for k in _ks)
        TIERS.append((_lo,_hi,_lab,_c))
    TIERS.append((0.3, min(MM.delta_range(k)[0] for k in ("micro","rde","rce")), "Tier 4", "#7FB0D3"))
    xtr=ax.get_xaxis_transform()
    for dlo,dhi,tl,col in TIERS:
        ax.axvspan(dlo,dhi,color=col,alpha=0.75,zorder=0,lw=0)
        ax.text(np.sqrt(dlo*dhi),1.02,tl,transform=xtr,fontsize=TIER,fontweight="bold",color="0.25",
                ha="center",va="bottom",clip_on=False)
    dm=np.logspace(np.log10(D_MIN),np.log10(500),80); ax.plot(dm,C/dm,color=BLUE,lw=1.8,zorder=5)
    dfr=np.logspace(np.log10(0.3),np.log10(D_MIN),80); ax.plot(dfr,C/dfr,color=BLUE,lw=1.8,ls=(0,(4,2)),zorder=5)
    for k,d,il in ANCH:
        ax.plot([d],[il],"o",color=BLUE,ms=5.2,mec="white",mew=0.9,zorder=7)
    # short name labels only; every number is in the caption. Offsets avoid collisions.
    # every label sits below-right of its marker (off the guide line, which runs up-right); the RCE label goes
    # above-left because RDE sits just below-right of it. The two batch markers nearly coincide, so both labels
    # stack below-right with parallel leaders, top label = top marker.
    # the microfluidic (12.5 um) and RDE (12.6 um median) markers nearly coincide, so both go on leaders,
    # one above-left and one below-right, and the RCE label sits above-left further out
    OFF={"natural":(26,-16,"left","center"),"stirred":(26,-2,"left","center"),
         "flow":(22,-5,"left","center"),"anec":(14,-9,"left","center"),
         "micro":(-14,14,"right","center"),"rde":(12,-12,"left","center"),"rce":(-12,32,"right","center")}
    LEAD=("natural","stirred","flow","anec","micro","rde","rce")
    for k,d,il in ANCH:
        dx,dy,ha,va=OFF[k]
        lead = dict(arrowstyle="-",color=BLUE,lw=0.5,shrinkA=0,shrinkB=3) if k in LEAD else None
        ax.annotate(MM.ARCH_LABEL[k],xy=(d,il),xytext=(dx,dy),textcoords="offset points",
                    fontsize=ANN,color=BLUE,ha=ha,va=va,zorder=8,arrowprops=lead)
    dev = max(100.0*(1.0 - il/(C/d)) for k,d,il in ANCH if k not in ("stirred",))
    print(f"ladder: C = {C:.0f} mA cm-2 um; model floor {D_MIN:.2f} um; medians sit up to {dev:.0f}% below the guide")
    for thr,lab in [(OPER,"25"),(BARRIER,"50")]:
        ax.axhline(thr,color=RED,ls=":",lw=1.0,zorder=3,alpha=0.85)
        ax.text(0.02,thr*1.07,lab+" mA cm$^{-2}$",transform=ax.get_yaxis_transform(),fontsize=ANN,color=RED,ha="left",va="bottom",zorder=6)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(500,0.3); ax.set_ylim(3,3000)
    ax.set_xlabel("$\\delta$ ($\\mu$m)",fontsize=AX)
    ax.set_ylabel("$i_{lim}$ (mA cm$^{-2}$)",fontsize=AX)
    ax.set_xticks([500,100,10,1]); ax.set_xticklabels(["500","100","10","1"])

def draw_starvation(b):
    # ── F2: the exemplar is one specific system, not the corpus ───────────────
    fan=pf[pf.case=="fan"]; fanm=pfm[pfm.case=="fan_median"]
    DELTA_STIR=float(fan.delta_um.iloc[0])          # read, never retyped
    ivals=sorted(fan.i_mAcm2.unique()); imvals=sorted(fanm.i_mAcm2.unique())
    ILIM_EX=float(fan.ilim_mAcm2.iloc[0]); ILIM_MED=float(fanm.ilim_mAcm2.iloc[0])
    for ie,im in zip(ivals,imvals):
        ce=fan[fan.i_mAcm2==ie].sort_values("x_um").c_norm.values
        cm=fanm[fanm.i_mAcm2==im].sort_values("x_um").c_norm.values
        assert np.abs(ce-cm).max() < 1e-4, "normalised fans no longer coincide"
    ILIM_ROWMED = MM.ilim_median("stirred", "substrate")
    keep=[0,1,2,4]; ivals=[ivals[i] for i in keep]; imvals=[imvals[i] for i in keep]
    shades=plt.cm.Blues(np.linspace(0.40,0.95,len(ivals)))
    for col,i_ex,i_md in zip(shades,ivals,imvals):
        g=fan[fan.i_mAcm2==i_ex]; x,cn=with_surface(g)
        x=np.r_[x,DELTA_STIR]; cn=np.r_[cn,1.0]          # the film edge: c = C_bulk at x = delta (Dirichlet)
        frac=i_ex/ILIM_EX
        b.plot(x,cn,color=col,lw=1.6,label=f"{frac:.1f} $i_{{lim}}$" if frac<0.99 else "$i_{lim}$")
    FS.legend(b, loc="lower right", fontsize=ANN)       # the four lines converge at the film edge: a key, not in-line labels
    print(f"starvation: stirred delta {DELTA_STIR:.0f} um; i/ilim " + ", ".join(f"{i/ILIM_EX:.2f}" for i in ivals)
          + f"; exemplar ilim {ILIM_EX:.1f}, corpus-median {ILIM_MED:.1f}, median of the {len(MM.class_matrix('substrate'))} stoichiometric substrate rows {ILIM_ROWMED:.1f} mA cm-2;"
          + f" fractions of the barrier {ILIM_EX/BARRIER:.2f} / {ILIM_MED/BARRIER:.2f}")
    b.set_xlim(0,DELTA_STIR); b.set_ylim(0,1.05)
    b.set_xlabel("distance from electrode ($\\mu$m)",fontsize=AX); b.set_ylabel("$c_S$ / $C_S$",fontsize=AX)

def draw_barrier(c):
    # 2026-09-07: six archetype films (the RDE is omitted: its median film coincides with the
    # microfluidic one), every one read from the profile solve. c_surf = 1 - i/i_lim.
    # 2026-09-08 quality pass: the line STYLE now carries the physics the caption states. Three
    # architectures hold a steady state at the 50 mA cm-2 barrier (solid); three cannot and are
    # drawn at their own limiting current (dashed). `flow` was solid while being starved
    # (i_lim 45.1 < 50), so the figure contradicted its own caption. Supplied/starved is decided
    # from the solve, never typed.
    styles={"rce":(GREEN,1.7),"micro":(ORANGE,1.5),"anec":(LBLUE,1.7),"flow":(BLUE,1.7),
            "stirred":(RED,1.4),"unstirred":("0.55",1.4)}
    names={"rce":"rotating cylinder","micro":"microfluidic (25 µm)","anec":"ANEC flow cell","flow":"recirculating flow cell",
           "stirred":"stirred","unstirred":"unstirred"}
    sup_h, sta_h = [], []
    for case,(colr,lw) in styles.items():
        g=pf[pf.case==case].sort_values("x_um"); x,cn=with_surface(g); delta=g.delta_um.iloc[0]
        i=float(g.i_mAcm2.iloc[0]); il=float(g.ilim_mAcm2.iloc[0])
        supplied = il > BARRIER + 1e-6
        ls = "-" if supplied else "--"
        x=np.r_[x,delta,300.0]; cn=np.r_[cn,1.0,1.0]
        h,=c.plot(x,cn,color=colr,ls=ls,lw=lw,label=names[case])
        (sup_h if supplied else sta_h).append(h)
        print(f"barrier: {names[case]:22s} delta {float(delta):6.1f} um  " +
              (f"c_surf {1-i/il:.2f}  SUPPLIED at {BARRIER:.0f}" if supplied else f"starved (ilim {il:.1f})"))
    ILIM_MED = float(pfm.ilim_mAcm2.iloc[0]); print(f"barrier: corpus-median substrate at the stirred film gives {ILIM_MED:.1f} mA cm-2")
    # One legend, supplied first then starved, ordered so the solid/dashed split reads down the
    # list. What the two styles MEAN is the caption's job; two on-figure legend titles crowded the
    # curves and were removed.
    FS.legend(c, handles=sup_h + sta_h, loc="lower right", fontsize=ANN, labelspacing=0.30)
    c.set_xlim(0,240); c.set_ylim(0,1.06)
    c.set_xlabel("distance from electrode ($\\mu$m)",fontsize=AX); c.set_ylabel("$c_S$ / $C_S$",fontsize=AX)

def draw_scatter(d):
    # 2026-09-08 quality pass: the caption's headline statistic is the MEDIAN per architecture and
    # the panel never drew it, so the reader had to estimate it from a jittered cloud. A median bar
    # is drawn per column, computed here from the same matrix the counts come from. Thresholds now
    # are labelled at the left, where no data sits, instead of into the top-right corner where the
    # points are densest. AUTHOR RULING 2026-09-08: they are RED dotted with red labels, the same
    # language as Fig. 4b, even though red is also the catalyst carrier here -- the reference lines
    # are dotted rules and the carriers are markers, so the two do not read as the same thing, and
    # matching Fig. 4b matters more than reserving the hue.
    cols6=["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
    labs6=["unstirred","stirred","recirc.\nflow","ANEC","micro-\nfluidic","RDE","RCE"]
    mk={"substrate":("o",BLUE),"mediator":("s",ORANGE),"catalyst":("^",RED)}; rng=np.linspace(-0.22,0.22,50)
    for j,cn in enumerate(cols6):
        for i,(_,r) in enumerate(df.iterrows()):
            m,cc=mk[r.carrier_type]; d.plot(j+rng[(i*17)%50],r[cn],m,ms=2.8,color=cc,alpha=0.55,mec="none",zorder=3)
        med=float(df[cn].median())
        d.plot([j-0.34,j+0.34],[med,med],color="0.12",lw=1.9,solid_capstyle="butt",zorder=6)
        print(f"scatter: {cn:8s} median {med:7.2f}  {(df[cn]>=BARRIER).sum():2d}/50 clear {BARRIER:.0f}, {(df[cn]>=OPER).sum():2d}/50 clear {OPER:.0f}")
    for thr,lab,va,off in ((BARRIER,"50 mA cm$^{-2}$","bottom",1.10),(OPER,"25 mA cm$^{-2}$","top",0.91)):
        d.axhline(thr,color=RED,ls=":",lw=1.0,zorder=2)
        d.text(0.015,thr*off,lab,transform=d.get_yaxis_transform(),fontsize=ANN,color=RED,
               ha="left",va=va,zorder=7,
               bbox=dict(fc="white",ec="none",alpha=0.72,pad=0.8))
    d.set_yscale("log"); d.set_ylim(0.03,4000); d.set_xlim(-0.6,len(cols6)-0.4)
    d.set_xticks(range(len(cols6))); d.set_xticklabels(labs6,fontsize=TICK,rotation=20,ha="right",rotation_mode="anchor")
    d.set_ylabel("$i_{lim}$ (mA cm$^{-2}$)",fontsize=AX)
    h=[Line2D([0],[0],marker=m,ls="",ms=3.8,color=cc,label=t) for t,(m,cc) in mk.items()]
    h.append(Line2D([0],[0],color="0.12",lw=1.9,label="median"))
    FS.legend(d, handles=h, loc="lower right", fontsize=ANN, handletextpad=0.3, ncol=2,
          columnspacing=1.0, frameon=True, framealpha=0.80, facecolor="white", edgecolor="none")

# ───────────────────────── Figure: Section 3 ────────────────────────────────
fig = plt.figure(figsize=(6.5, 4.7), dpi=200)
gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 2.0], hspace=0.30, wspace=0.32,
                      left=0.105, right=0.975, top=0.985, bottom=0.125)
ax_sch = fig.add_subplot(gs[0, :])
ax_lad = fig.add_subplot(gs[1, 0]); style(ax_lad)
ax_star = fig.add_subplot(gs[1, 1]); style(ax_star)
_ps, _pl = ax_sch.get_position(), ax_lad.get_position()
draw_schematic(ax_sch, _ps.width * fig.get_figwidth(), _ps.height * fig.get_figheight()); draw_ladder(ax_lad); draw_starvation(ax_star)
FS.panel_letter(ax_lad, "b)", x=-0.22, y=1.05, size=10); FS.panel_letter(ax_star, "c)", x=-0.22, y=1.05, size=10)
fig.text(_pl.x0 - 0.22 * _pl.width, _ps.y1, "a)", fontsize=10, fontweight="bold", va="top", ha="right")   # same column as b)
fig.savefig("figs/sec4_Fig_sec3.svg"); fig.savefig("figs/sec4_Fig_sec3.png", dpi=600)
print("Fig sec3 written")

# ───────────────────────── Figure: Section 4 ceiling ────────────────────────
fig2, axs2, _ = gengrid(2, 1, size_inches=(6.5, 3.0), ticklabel_size=TICK, genlabels=False)
c2, d2 = axs2
draw_barrier(c2); draw_scatter(d2)
FS.panel_letter(c2, "a)", x=-0.16, y=1.02, size=10); FS.panel_letter(d2, "b)", x=-0.16, y=1.02, size=10)
fig2.tight_layout(w_pad=2.6)
fig2.savefig("figs/sec4_Fig_ceiling.svg"); fig2.savefig("figs/sec4_Fig_ceiling.png", dpi=600)
print("Fig ceiling written")
