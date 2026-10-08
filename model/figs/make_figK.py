"""FigK — does the solvent actually boil, and what does it take to stop it?

Lumped thermal balance on 10 cm^2 electrodes, consistent with the cellvoltage.jl stack.
Dissipated overpotential heat per electrode area (conservative: excludes reaction
entropy; evaporative loss omitted on BOTH sides because evaporation IS the failure
mode in question):
    q(i) = [ 2b*asinh(i/2i0) + i*L/kappa ] * i        [W/cm^2]
Steady state:  T_ss = T_amb + q/U',  with U' = UA/A_elec.

STRUCTURE (2026-08 revision). The previous version crossed solvent, geometry and
cooling on a single axis, which conflated the variables and let "PEM-class plates"
silently bundle a thin gap (geometry) with active coolant (thermal management).
Each panel now varies exactly one thing:

  (a) SOLVENT       -- one reactor (unstirred beaker), four electrolytes.
  (b) ARCHITECTURE  -- five reactor types, every solvent, ALL PASSIVELY COOLED.
  (c) COOLING DUTY  -- the heat-rejection coefficient each intensified architecture
                       REQUIRES to hold its design current without boiling.

PASSIVE COOLING IS DERIVED FROM GEOMETRY, NOT ASSUMED. The external film is natural
convection + radiation, h_ext ~ 13 W/m^2 K; internal transport adds a series
resistance h_int (stagnant liquid ~100, stirred ~800, forced flow >2000):
    U' = [ (1/h_int + 1/h_ext)^-1 ] * sigma,     sigma = A_external / A_electrode
The 100 mL beaker takes sigma = 12.5 DIRECTLY from the registry row "Vessel external
area = 0.0125 m^2" (derived: ~5 cm dia x 8 cm cylinder) over 10 cm^2 = 1e-3 m^2 of
electrode. That geometry gives U' = 0.01438 W/cm^2 K, about 30% BELOW the 0.02
W/cm^2 K "still air" value assumed in earlier treatments -- it does NOT recover it.
The earlier sigma = 15 was reverse-fitted to land nearer 0.02 and gave 0.01726, which
does not recover it either. Using the geometric value makes the passive analysis more
conservative (lower ceilings, smaller margins), not less. Compact cells have smaller sigma and
a stack interior cell is nearly enclosed (sigma ~ 0.8), so intensification carries a
heat-REJECTION penalty that partly offsets its heat-GENERATION advantage. Stirring a
beaker barely helps (h_ext, not h_int, is limiting) -- panel (b) shows this directly.

Each architecture is judged against ITS OWN design current, since nobody builds a
250 um cell to run at 50 mA/cm^2, but panel (b) plots the ABSOLUTE ceiling and shows
the design currents as reference lines, so the architecture trend is not hidden behind
a divisor that changes from column to column.

VESSEL SIZE MATTERS, VIA SURFACE AREA (not via heat capacity). Heat capacity does not
appear in T_ss = T_amb + q/U' at all -- it only sets the approach time tau = C/UA. But
inventory and rejecting surface are physically coupled: scaling a vessel scales A_ext,
hence sigma, hence U'. With ohmic heat ~ i^2 L/kappa and A_ext ~ V^(2/3),
        i_boil ~ V^(1/3)
so a 1 L beaker tolerates 2.16x the current density of a 100 mL one at the same gap and
electrode area. The series is COMPUTED HERE (VOLUMES below, emitted to the JSON as
"volume_sweep") rather than quoted in prose, so it can never drift from the figure again:
an earlier prose series (49 / 62 / 106 / 134) was left over from kappa = 0.35 S/m.
The beaker rows below are specified as a 100 mL vessel (sigma = 12.5 from the registry
geometry); the claim that boil-off is independent of electrolyte inventory holds only if
UA is pinned while inventory changes, which is not physically realisable.

PROVENANCE (2026-08, CLOSED). Every constant of the shared thermal model
(figs/thermal_model.py) and of this script now carries a row in
data/parameters_provenance.csv under the three-state standard of
docs/PROVENANCE_STANDARD.md -- measured (state A, source + locator), derived (state B,
named method from A/B inputs) or assumption (state C, declared + sensitivity). The 22
constants below were previously unregistered and are now registered, category 9:
    H_EXT = 13.8 W/m^2 K        derived  (h_conv 7.22 + h_rad 6.60 at Ts = 65 C, L = 5.09 cm)
    sigma = 12.5 / 12.5         derived  (A_ext/A_elec from the registered vessel area)
    sigma = 10 / 7 / 0.8        assumption (declared package geometries; the 250 um chip
                                 value is THE load-bearing one -- sigma in [3.5, 21] moves
                                 the DMF margin 0.69x-1.90x, crossing unity)
    h_int = 100 / 800 / 2000 / 5000 W/m^2 K   assumption x4, ONE shared sensitivity:
                                 h_int swept 50 -> inf moves every ceiling -5/+6 pct
    i_design = 50 / 50 / 100 / 500 / 1000 mA/cm^2   assumption x5; the 100 (flow cell) is
                                 conclusion-critical -- at 50 the THF S6.2 claim flips
    gaps = 2 cm / 2 cm / 5 mm / 250 um / 100 um     assumption, except 250 um = MEASURED
                                 (Watts, Gattrell & Wirth, Beilstein J. Org. Chem. 2011,
                                 7, 1108-1114: 254 um FEP spacer)
    cooling-band edges = 8e-4, 2e-2, 8e-2, 2e-1, 1.0 W/cm^2 K   derived from H_EXT x sigma
                                 and Incropera Table 1.1 / Table 8.1
    eps = 0.9 (radiation)       assumption; i0 = 1.0 mA/cm^2 assumption (cat. 8);
    b = 2*RT/F derived; T_amb = 25 C assumption
PENDING CODE CHANGES registered as sensitivities, NOT yet applied here (applying them
would move published numbers and requires a re-render):
    vessel external area 0.0125 -> 0.00996 m^2 (the quoted cylinder holds 157 mL, not
        100 mL); sigma_beaker 12.5 -> 9.96; every beaker ceiling -11 pct (conservative)
    natural-convection band edges 8e-4 - 2e-2 -> 1.0e-3 - 1.6e-2 (shading only)
APPLIED (thermal_model.py, which this file imports): the CRC 97th ed. boiling points,
    MeCN Tb 82.0 -> 81.6 C, THF 66.0, DMF 152.8, water 99.974, registered as T_boil rows.
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
SEC4 = ROOT = os.path.dirname(HERE)
# Portable paths: resolve everything relative to this file, and chdir to the repo root before
# importing customplot, which reads "Color Swatches from UC Berkeley.xlsx" from the CURRENT WORKING
# DIRECTORY at import time. Without the chdir this script only runs from the repo root; with it,
# it runs from anywhere, matching make_figs_sec34.py / make_fig4A.py / make_figFG.py /
# make_fig_carrier.py / make_figK_MSlayout.py. Every read and write below is already an absolute
# path built from HERE or SEC4, so the chdir changes NO number and NO output location.
for cand in (SEC4, HERE, os.path.expanduser("~/Documents/CO2R-Bulk-Scale-Julia-Model")):
    if os.path.exists(os.path.join(cand, "customplot.py")):
        sys.path.insert(0, cand); os.chdir(cand); break
else:
    raise SystemExit("customplot.py not found; cannot run.")
from customplot import gengrid, rainbow_2

# THE thermal model now lives in figs/thermal_model.py -- a verbatim extract of the
# constants and functions that used to be defined here. make_fig4B.py (panels e/f)
# and make_figs.py (FIG D) import the SAME module, so the three figures can no
# longer drift into three different thermal models as they had by 2026-08. The
# constants, their values and their provenance gaps are unchanged; see that file's
# docstring for the reconciliation record.
sys.path.insert(0, HERE)
import thermal_model as _TM_HX
from thermal_model import (TAMB, H_EXT, SIGMA_BEAKER, SOLVENTS as _SOLV, REACTORS,
                           COOLING_BANDS, U_passive, q_Wcm2, i_boil, U_required,
                           E_cell, T_ss)

BLUE=rainbow_2[1]; LBLUE=rainbow_2[2]; RED=rainbow_2[5]; GREEN=rainbow_2[0]; ORANGE=rainbow_2[6]

# figK's own colour assignment, appended to the shared solvent rows
_SOLV_COL = {"THF": RED, "MeCN": LBLUE, "DMF": ORANGE, "aq. NaOH": BLUE}
SOLVENTS = [row + (_SOLV_COL[row[0]],) for row in _SOLV]

fig, axes, _ = gengrid(3,1, size_inches=(10.6,3.3), ticklabel_size=7.5)
a, bx, cx = axes

# ── (a) SOLVENT: one reactor (unstirred beaker), four electrolytes ───────────
Lb, sigb, hib, iopb = REACTORS[0][1], REACTORS[0][2], REACTORS[0][3], REACTORS[0][4]
Ub = U_passive(sigb, hib)
ii = np.linspace(0.5,150,600)
for lab,elyte,kap,Tb,prov,col in SOLVENTS:
    a.plot(ii, TAMB + q_Wcm2(ii,kap,Lb)/Ub, color=col, lw=1.8, label=lab)
    ib = i_boil(kap,Lb,Tb,Ub)
    a.axhline(Tb, color=col, ls=":", lw=0.8, alpha=0.65)
    if ib < 150:
        a.plot([ib],[Tb],"o",color=col,ms=5.5,mec="white",mew=0.7,zorder=6)
        a.annotate(f"{lab} boils\nat {ib:.0f}", xy=(ib,Tb), xytext=(ib+5,Tb-24),
                   fontsize=5.6, color=col, ha="left")
    else:
        # Ceiling lies beyond the plotted range. State it, otherwise the flat curve
        # invites the reader to infer a far higher ceiling than the i^2 scaling gives:
        # dT grows as i^2, so 19 K at 150 mA/cm2 becomes 75 K (boiling) at only ~2x
        # the current. Without this label panel (a) appears to contradict panel (b).
        a.annotate(f"{lab}: {Tb:.0f} $^\\circ$C reached\nat {ib:.0f} mA cm$^{{-2}}$ (off scale)",
                   xy=(148, TAMB + q_Wcm2(148.,kap,Lb)/Ub), xytext=(96, 62),
                   fontsize=5.4, color=col, ha="left",
                   arrowprops=dict(arrowstyle="->", color=col, lw=0.7))
a.axvline(iopb, color="0.35", lw=1.0, ls="--")
a.text(iopb+3, 33, f"median transport\nceiling {iopb:.0f} mA cm$^{{-2}}$", fontsize=5.6,
       color="0.35", va="bottom")
a.text(0.035,0.965,"unstirred 100 mL beaker, 2 cm gap, 10 cm$^2$\npassive cooling ($U' = $%.3f W cm$^{-2}$K$^{-1}$)"%Ub,
       transform=a.transAxes, fontsize=6.0, va="top", color="0.3")
a.set_xlim(0,150); a.set_ylim(25,200)
a.set_xlabel("Current density (mA cm$^{-2}$)", fontsize=8)
a.set_ylabel("Steady-state cell temperature ($^\\circ$C)", fontsize=8)
a.legend(fontsize=6.0, frameon=False, loc="center left", bbox_to_anchor=(0.015,0.50))

# ── (b) ARCHITECTURE: the seven transport archetypes + the zero-gap reference ─
# Absolute boil-off ceiling, NOT normalised: normalising by a design current that
# differs per architecture hides the underlying trend behind an arbitrary divisor.
# Each architecture's OWN median transport ceiling (Fig. 5b, the published matrix)
# is drawn as a black dash, so where the dash sits above a solvent's curve that
# solvent boils before the architecture reaches what transport allows.
xr = np.arange(len(REACTORS))
ceilings = {}
for lab,elyte,kap,Tb,prov,col in SOLVENTS:
    ib=[i_boil(kap,L,Tb,U_passive(sig,hi)) for rl,L,sig,hi,iop in REACTORS]
    ceilings[lab]=ib
    bx.plot(xr, ib, "-o", color=col, lw=1.6, ms=5.5, mec="white", mew=0.6, label=lab, zorder=4)
for _x0, _r in zip(xr, REACTORS):
    bx.plot([_x0-0.30, _x0+0.30], [_r[4], _r[4]], color="0.15", lw=2.0, solid_capstyle="butt", zorder=6)
bx.set_yscale("log"); bx.set_ylim(3, 3e3); bx.set_xlim(-0.5, len(REACTORS)-0.5)
bx.set_xticks(xr); bx.set_xticklabels([r[0] for r in REACTORS], fontsize=6.0)
bx.set_ylabel("Boil-off current density (mA cm$^{-2}$)", fontsize=8)
bx.set_xlabel("Reactor architecture (passive cooling only)", fontsize=8)
from matplotlib.lines import Line2D as _L2Dk
bx.plot([], [], color="0.15", lw=2.0, label="median transport ceiling")
bx.legend(fontsize=6.0, frameon=True, framealpha=0.9, edgecolor="0.85",
          loc="upper right", handletextpad=0.4, borderpad=0.35)

# ── (c) COOLING DUTY required by the intensified architectures ───────────────
INT = REACTORS[2:]
xi = np.arange(len(INT))
for nm,lo,hi,cshade in COOLING_BANDS:      # shared with make_figs.py FIG D
    cx.axhspan(lo,hi,color=cshade,alpha=0.55,zorder=0)
    cx.text(-0.44, np.sqrt(lo*hi), nm, fontsize=5.4, color="0.30",
            ha="left", va="center", zorder=1)
req = {}
for lab,elyte,kap,Tb,prov,col in SOLVENTS:
    r=[U_required(iop,kap,L,Tb) for rl,L,sig,hi,iop in INT]
    req[lab]=r
    cx.plot(xi, r, "-o", color=col, lw=1.5, ms=5.5, mec="white", mew=0.6, label=lab, zorder=4)
cx.plot(xi, [U_passive(sig,hi) for rl,L,sig,hi,iop in INT], "--s", color="0.35",
        lw=1.2, ms=4.5, label="passively available", zorder=5)
cx.set_yscale("log"); cx.set_ylim(5e-4, 3.0); cx.set_xlim(-0.5, len(INT)-0.5)
cx.set_xticks(xi); cx.set_xticklabels([r[0] for r in INT], fontsize=6.0)
cx.set_ylabel("Required $U'$ to avoid boiling (W cm$^{-2}$ K$^{-1}$)", fontsize=8)
cx.set_xlabel("Architecture, run at its median transport ceiling", fontsize=8)
cx.legend(fontsize=5.6, frameon=True, framealpha=0.92, edgecolor="0.85",
          loc="lower right", handletextpad=0.4, borderpad=0.35, ncol=1)

fig.tight_layout(w_pad=1.8)
fig.savefig(os.path.join(HERE,"sec4_figK_boiloff.svg"))
fig.savefig(os.path.join(HERE,"sec4_figK_boiloff.png"), dpi=600)

# ── console + machine-readable dump for the SI ───────────────────────────────
out = {"h_ext_Wm2K": H_EXT, "T_amb_C": TAMB, "reactors": [], "panelA": {}, "panelB": {}, "panelC": {}}
print("PASSIVE U' BY ARCHITECTURE  (U' = [1/h_int + 1/h_ext]^-1 * sigma)")
for rl,L,sig,hi,iop in REACTORS:
    U=U_passive(sig,hi)
    print(f"  {rl.replace(chr(10),' '):26s} L={L*1e3:7.3f} mm  sigma={sig:5.1f}  h_int={hi:6.0f}"
          f"  U'={U:.5f} W/cm2K   i_design={iop:6.0f}")
    out["reactors"].append({"name":rl.replace(chr(10)," "),"gap_m":L,"sigma":sig,
                            "h_int":hi,"U_passive":U,"i_design":iop})
print("\n(a) UNSTIRRED 100 mL BEAKER, 2 cm gap — boil-off ceiling by solvent (mA/cm2)")
for lab,elyte,kap,Tb,prov,col in SOLVENTS:
    ib=i_boil(kap,Lb,Tb,Ub); out["panelA"][lab]={"i_boil":ib,"margin":ib/iopb}
    print(f"  {lab:9s} kappa={kap:6.2f} S/m  Tb={Tb:5.0f} C   i_boil={ib:8.0f}  margin={ib/iopb:6.2f}x")
print("\n(b) ABSOLUTE BOIL-OFF CEILING, PASSIVE COOLING (mA/cm2); design current in header")
hdr=f"  {'solvent':9s}"+"".join(f"{r[0].replace(chr(10),' ')+' @'+str(int(r[4])):>28s}" for r in REACTORS)
print(hdr)
for lab,elyte,kap,Tb,prov,col in SOLVENTS:
    print(f"  {lab:9s}"+"".join(f"{v:28.0f}" for v in ceilings[lab]))
    out["panelB"][lab]=dict(zip([r[0].replace(chr(10)," ") for r in REACTORS], ceilings[lab]))
out["panelB"]["_design_currents"]=dict(zip([r[0].replace(chr(10)," ") for r in REACTORS],
                                           [r[4] for r in REACTORS]))
print("\n(c) REQUIRED U' AT DESIGN CURRENT (W/cm2 K); passive availability in last row")
hdr=f"  {'solvent':9s}"+"".join(f"{r[0].replace(chr(10),' '):>22s}" for r in INT)
print(hdr)
for lab,elyte,kap,Tb,prov,col in SOLVENTS:
    print(f"  {lab:9s}"+"".join(f"{v:22.4f}" for v in req[lab]))
    out["panelC"][lab]=dict(zip([r[0].replace(chr(10)," ") for r in INT], req[lab]))
avail=[U_passive(sig,hi) for rl,L,sig,hi,iop in INT]
print(f"  {'passive':9s}"+"".join(f"{v:22.4f}" for v in avail))
out["panelC"]["passively_available"]=dict(zip([r[0].replace(chr(10)," ") for r in INT], avail))

# ── the gap sweep the MS-layout panel (c) draws (2026-09-12) ─────────────────
# Panel (c) of the manuscript figure used to restate panel (b)'s verdict on a different axis:
# required U' against what the cell rejects passively is the SAME comparison as boil-off ceiling
# against transport ceiling, and on all 24 cells the two returned the same verdict. It draws this
# sweep instead, which explains (b)'s ORDERING. The duty numbers above are kept and still shipped,
# because the SI tables and the parameter registry read them.
#
# DECLARED REFERENCE GEOMETRY. A sweep in the gap needs one heat-rejection geometry, and this uses
# sigma = SIGMA_BEAKER with h_int = 2000 W m-2 K-1, which is exactly the recirculating, ANEC and
# RDE rows and within 12 % of the other three centimetre-gap archetypes. The microfluidic cell
# carries sigma = 7.0 and the zero-gap stack 0.8, so their own ceilings are panel (b)'s, not this
# curve's. What the curve carries is the SHAPE and the crossing, and in both limits the RATIO
# between two solvents is U'-independent: ohmic-limited it goes as sqrt(kappa dT), kinetics-limited
# as dT, and U' cancels either way.
SIG_REF, HINT_REF = SIGMA_BEAKER, 2000.0
U_REF = U_passive(SIG_REF, HINT_REF)
GAP_GRID = np.logspace(np.log10(5e-6), np.log10(1.0e-1), 61)
out["panelC_gapsweep"] = {
    "gap_m": [float(g) for g in GAP_GRID], "sigma_ref": SIG_REF, "h_int_ref": HINT_REF,
    "U_passive_ref": U_REF,
    "i_boil": {lab: [i_boil(kap, float(g), Tb, U_REF) for g in GAP_GRID]
               for lab, elyte, kap, Tb, prov, col in SOLVENTS}}
print("\n(c) GAP SWEEP at sigma=%.1f, h_int=%.0f (U'=%.5f): %d gaps, %.0f um to %.0f mm"
      % (SIG_REF, HINT_REF, U_REF, len(GAP_GRID), GAP_GRID[0]*1e6, GAP_GRID[-1]*1e3))
for lab, elyte, kap, Tb, prov, col in SOLVENTS:
    _v = out["panelC_gapsweep"]["i_boil"][lab]
    print("  %-9s i_boil %8.0f at %.0f um -> %6.0f at %.0f mm  (dT %.1f K, kappa %.3f S/m)"
          % (lab, _v[0], GAP_GRID[0]*1e6, _v[-1], GAP_GRID[-1]*1e3, Tb - TAMB, kap))

# ── vessel-size sweep: sigma scales as V^(2/3) about the registry 100 mL geometry ──
# Emitted so the SI never has to hard-code the series in prose. Unstirred beaker,
# 2 cm gap, 10 cm^2 electrodes; V_REF = 100 mL is the registry vessel.
VOLUMES=[50., 100., 500., 1000.]; V_REF=100.
out["volume_sweep"]={"basis":"unstirred beaker, 2 cm gap, 10 cm2 electrodes; "
                              "sigma = %.1f x (V/%.0f mL)^(2/3)"%(SIGMA_BEAKER,V_REF),
                     "volumes_mL":VOLUMES, "sigma":{}, "U_passive":{}, "i_boil_mAcm2":{}}
print("\n(d) VESSEL-SIZE SWEEP, unstirred beaker, 2 cm gap (i_boil ~ V^1/3)")
print(f"  {'solvent':9s}"+"".join(f"{str(int(v))+' mL':>12s}" for v in VOLUMES))
for v in VOLUMES:
    sg=SIGMA_BEAKER*(v/V_REF)**(2.0/3.0)
    out["volume_sweep"]["sigma"][str(int(v))]=sg
    out["volume_sweep"]["U_passive"][str(int(v))]=U_passive(sg,REACTORS[0][3])
for lab,elyte,kap,Tb,prov,col in SOLVENTS:
    ser=[i_boil(kap,REACTORS[0][1],Tb,U_passive(SIGMA_BEAKER*(v/V_REF)**(2.0/3.0),REACTORS[0][3]))
         for v in VOLUMES]
    out["volume_sweep"]["i_boil_mAcm2"][lab]=dict(zip([str(int(v)) for v in VOLUMES], ser))
    print(f"  {lab:9s}"+"".join(f"{s:12.1f}" for s in ser)+
          f"   ratio 1L/100mL = {ser[3]/ser[1]:.2f}x")

os.makedirs(os.path.join(SEC4,"results"), exist_ok=True)
# ── the quantities the SI's S6 prose states in words, emitted rather than typed ────────────────
# 2026-09-12. Five S6 sentences carried typed numbers that the reactor table had moved past: the
# drop from the assumed 0.02 W cm-2 K-1 to the geometric U' read "~9%" where the model gives 15-16%,
# the wetted-area pairs and the h_ext/sigma cancellation were computed on retired conductivities,
# and the worked example of the main text had no emitted basis at all. They are computed here so
# the SI interpolates them and G-SIDERIVED can re-solve them from a second code path.
_B = REACTORS[0]
_Ub = U_passive(_B[2], _B[3])
_Uw = U_passive(0.00996/1.0e-3, _B[3])          # wetted wall + base for a 100 mL charge
_ASSUMED = 0.02                                  # the still-air value earlier treatments assumed
_HEXT_HOT = round(_TM_HX.h_ext_at(152.8), 1)    # h_ext at DMF's boiling point (thermal_model.h_ext_at)
_Uh = (1.0/(1.0/_B[3] + 1.0/_HEXT_HOT))*_B[2]*1e-4
_Ubh = (1.0/(1.0/_B[3] + 1.0/_HEXT_HOT))*SIGMA_BEAKER*1e-4
_si = {"assumed_U": _ASSUMED, "geometric_U": _Ub, "wetted_U": _Uw,
       "h_ext_hot_Wm2K": _HEXT_HOT, "beaker": {}, "worked_example": {}}
for _lab, _el, _kap, _Tb, _pv, _col in SOLVENTS:
    _si["beaker"][_lab] = {
        "at_assumed_U": i_boil(_kap, _B[1], _Tb, _ASSUMED),
        "at_geometric_U": i_boil(_kap, _B[1], _Tb, _Ub),
        "at_wetted_sigma": i_boil(_kap, _B[1], _Tb, _Uw),
        "at_hot_h_ext": i_boil(_kap, _B[1], _Tb, _Uh),
        "at_wetted_sigma_and_hot_h_ext": i_boil(_kap, _B[1], _Tb, _Ubh)}
# The main text's illustration: 0.1 M Bu4NBF4/DMF, measured 4.76 mS cm-1, across a declared 5 mm
# gap at 100 mA cm-2. A tighter cell than the beaker archetype and NOT one of the modelled
# architectures, which is why it is emitted separately and labelled as an illustration.
_si["worked_example"] = {"electrolyte": "0.1 M Bu4NBF4/DMF", "kappa_S_per_m": 0.476,
                         "gap_m": 5.0e-3, "i_mAcm2": 100.0,
                         "E_cell_V": E_cell(100.0, 0.476, 5.0e-3),
                         "ohmic_V": 100.0*10.0*5.0e-3/0.476,
                         "q_Wcm2": q_Wcm2(100.0, 0.476, 5.0e-3),
                         "T_ss_C": T_ss(100.0, 0.476, 5.0e-3, _Ub)}
# ── kappa-axis reversal points, emitted so S3.2/S6 never type them (2026-09-14) ─────────────────
# For every preparative architecture and solvent: the multiple of the carried conductivity at which
# the boil-off verdict against that architecture's own transport ceiling reverses (above 1 for a
# cell that boils, below 1 for one that clears), and the zero-gap stack's reachability. Typed
# multiples (12.9x, 20.0x, 2.05x, 1.27x) outlived the sigma derivation of 2026-09-13 in the SI.
def _kappa_at(target, gap, Tb, U, lo=1e-5, hi=1e4):
    if i_boil(hi, gap, Tb, U) < target:
        return None
    for _ in range(200):
        m = np.sqrt(lo*hi)
        if i_boil(m, gap, Tb, U) > target:
            hi = m
        else:
            lo = m
    return float(np.sqrt(lo*hi))
_flips = {}
for _lab, _el, _kap, _Tb, _pv, _col in SOLVENTS:
    _flips[_lab] = {}
    for _r in REACTORS:
        _nm = _r[0].replace("\n", " ")
        _U = U_passive(_r[2], _r[3])
        _ib = i_boil(_kap, _r[1], _Tb, _U)
        _k = _kappa_at(_r[4], _r[1], _Tb, _U)
        _flips[_lab][_nm] = {"margin": _ib/_r[4], "passes": bool(_ib >= _r[4]),
                             "kappa_reverse_mScm": (None if _k is None else 10.0*_k),
                             "multiple": (None if _k is None else _k/_kap)}
_si["kappa_flips"] = _flips
_kD = [x for x in SOLVENTS if x[0] == "DMF"][0][2]
_tbD = [x for x in SOLVENTS if x[0] == "DMF"][0][3]
def _kappa_dec(f, target, lo=1e-4, hi=1e3):
    for _ in range(200):
        m = np.sqrt(lo*hi)
        lo, hi = (m, hi) if f(m) > target else (lo, m)
    return float(np.sqrt(lo*hi))
_si["beaker_dmf_example"] = {
    "electrolyte": "0.2 M NaI/DMF", "kappa_S_per_m": _kD, "gap_m": _B[1], "i_mAcm2": 100.0,
    "E_cell_V": float(E_cell(100.0, _kD, _B[1])), "ohmic_V": 100.0*10.0*_B[1]/_kD,
    "E_cell_50_V": float(E_cell(50.0, _kD, _B[1])), "q_Wcm2": float(q_Wcm2(100.0, _kD, _B[1])),
    "T_ss_C": float(T_ss(100.0, _kD, _B[1], _Ub)), "T_boil_C": _tbD,
    "kappa_Tss_at_boil_mScm": 10.0*_kappa_dec(lambda k: T_ss(100.0, k, _B[1], _Ub), _tbD),
    "kappa_E50_20V_mScm": 10.0*_kappa_dec(lambda k: E_cell(50.0, k, _B[1]), 20.0),
    "kappa_E50_10V_mScm": 10.0*_kappa_dec(lambda k: E_cell(50.0, k, _B[1]), 10.0)}
out["si_support"] = _si
json.dump(out, open(os.path.join(SEC4,"results","figK_thermal.json"),"w"), indent=2)
print("\nsaved -> results/figK_thermal.json")
