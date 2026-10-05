"""Deterministic accuracy/consistency audit for the Section 4 model.

Recomputes the physics and cross-checks every derived artifact against its source:
  1. Tier-0 i_lim per row x reactor (reimplemented correlations) vs julia/tier0_matrix.csv
  2. Merged-matrix override logic (mediated rows <- EC', wall floor) vs tier0_ec_matrix.csv
  3. Table S5 cells (medians, >=25, >=50) vs merged matrix
  4. Table S6 cells (x_k, stirred/thin-gap tier0->EC', system labels) vs mediated_ec_matrix.csv
  5. conc_provenance embedded arithmetic (mmol/mL) vs the C columns
  6. run_mediated.jl MedSpec values vs reactions_50.csv mediated rows
  7. Cross-file constants (F, T, delta, thresholds, kappa)
  8. Figure-label numbers embedded in make_*.py vs the CSVs
  9. SI text quantitative claims (extracted from make_si.js) vs recomputed values
Exit report: PASS/FAIL per check with the offending values.

Runnability remediation, 2026-08-02: this checker could not run from ANY working
directory. Its reads were split across three different roots -- `reactions_50.csv`
and `solvents.csv` want `data/`, the `julia/*` and `make_si.js` reads want the repo
root, and the `make_fig*.py` reads in checks 7 and 8 want `figs/` -- so every cwd
failed on at least one open(). docs/ARCHIVE_MANIFEST.md retains figs/make_fig4A.py
and figs/make_fig_main.py on the grounds that archiving them "would have broken a
provenance checker"; that justification is now true rather than hypothetical.
Every path is resolved relative to this file. No check, tolerance or expected
value was altered.
"""
import re, math, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))   # .../Section4_Model/data
ROOT = os.path.dirname(HERE)                        # .../Section4_Model
def P(*a):   return os.path.join(ROOT, *a)          # repo-root-relative
def D(n):    return os.path.join(HERE, n)           # data/-relative
def FIG(n):  return os.path.join(ROOT, "figs", n)   # figs/-relative

F = 96485.33
findings = []
def flag(sev, where, msg):
    findings.append((sev, where, msg))
    print(f"[{sev}] {where}: {msg}")

rx  = pd.read_csv(D("reactions_50.csv"))
t0  = pd.read_csv(P("julia", "tier0_matrix.csv"))
mg  = pd.read_csv(P("julia", "tier0_ec_matrix.csv"))
med = pd.read_csv(P("julia", "mediated_ec_matrix.csv"))
npm = pd.read_csv(P("julia", "all50_np_matrix.csv"))
sol = pd.read_csv(D("solvents.csv")).set_index("solvent")
gates = pd.read_csv(P("julia", "audit_gates.csv"))
# The SI CLAIMS must be read from the SHIPPED DOCUMENT, not from the generator: once a table is
# computed rather than typed, its numbers are not in make_si.js at all, and a check that greps the
# generator can only ever report a failure it created itself. `si` stays for the prose claims that
# really are authored literals; `si_doc` is the built artifact a referee opens.
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_text import asserted_text as _asserted
import re as _re
si_doc = _re.sub(r"\s+", " ", _asserted(P("SI_Section4_Transport_Model.docx")))
for _df in (t0, mg, med, gates):
    _df.columns = [c.strip() for c in _df.columns]

# ---------- 1. Tier-0 recomputation ----------------------------------------
def deltas(D, nu):
    """All seven reactor deltas [m], mirroring julia/correlations.jl."""
    # stirred adopted 200 um on 2026-09-01 (measured, Williams/Manthiram p. 1227), replacing
    # the declared 100 um. This module recomputes the matrix INDEPENDENTLY, so its copy has to
    # move too -- it was reporting every stirred row 100% high, which is the check working.
    out = {"natural": 228e-6, "stirred": 200e-6}
    # Levich RDE 1600 rpm
    w = 1600*2*math.pi/60
    out["rde"] = 1.61 * D**(1/3) * nu**(1/6) / math.sqrt(w)
    # Eisenberg RCE d=1.2 cm, 3000 rpm
    d = 1.2e-2; U = math.pi*d*3000/60
    Re = U*d/nu; Sc = nu/D
    Sh = 0.0791 * Re**0.70 * Sc**0.356
    out["rce"] = d/Sh
    # the three flow films (2026-09-07): two MEASURED (Watkins 2023 SI Table S1 -- parallel H-cell
    # 106.9 um, ANEC 36.2 um) and the Mo 2020 microfluidic cell, Leveque entrance solution at the
    # printed gap (25 um) and residence time (4 min) bounded by the half-gap film. The Leveque
    # number is 4 h^2/(D tau) exactly, and the half-gap floor binds for every row.
    out["flow"] = 106.9e-6
    out["anec"] = 36.2e-6
    h, tau = 25e-6, 4.0*60.0
    Sh = 1.85*(4*h**2/(D*tau))**(1/3)
    out["micro"] = min(2*h/Sh, h/2)
    return out

t0max = 0.0
for i, r in rx.iterrows():
    D = r.D_cm2s*1e-4
    nu = sol.loc[r.solvent].mu_mPas*1e-3/(sol.loc[r.solvent].rho*1000)
    dl = deltas(D, nu)
    for col in ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]:
        i_lim = r.n_carrier*F*D*(r.C_carrier_M*1000)/dl[col]*0.1  # mA/cm2
        ref = t0.iloc[i][col]
        relerr = abs(i_lim-ref)/max(ref,1e-12)
        t0max = max(t0max, relerr)
        if relerr > 0.02:
            flag("FAIL","tier0",f"row {i+1} {r.reaction[:38]} {col}: recomputed {i_lim:.2f} vs csv {ref:.2f} ({relerr:.1%})")
print(f"tier0 recompute: max rel err {t0max:.2%} across {len(rx)*7} cells "+("PASS" if t0max<=0.02 else "FAIL"))

# ---------- 2. Merged override logic ----------------------------------------
MEDIATED = set(med.reaction.unique())
# 2026-09-11: the seven catalyst rows carried at a SOURCED rate constant are EC' overlays too
# (julia/catalyst_ec_sourced.csv, k > 0), merged exactly as the mediated rows are; their published
# cell must equal the sourced solve, not the NP layer.
_cs = pd.read_csv(P("julia", "catalyst_ec_sourced.csv"))
_cs = _cs[_cs.k_M > 0]
SOURCED = {(r.reaction, r.reactor): float(r.i_ec_mAcm2) for r in _cs.itertuples()}
rmap = {"Unstirred batch":"natural","Stirred batch":"stirred","Recirculating flow cell":"flow",
        "ANEC flow cell":"anec","Microfluidic cell (25 um gap)":"micro",
        "RDE 1600 rpm":"rde","Rotating cylinder 3000 rpm":"rce"}
ok = True
for i, r in rx.iterrows():
    for col in rmap.values():
        m_val = mg.iloc[i][col]
        if any(k[0] == r.reaction for k in SOURCED):
            inv = {v: k for k, v in rmap.items()}
            expect = SOURCED[(r.reaction, inv[col])]
            if abs(m_val-expect)/max(expect,1e-9) > 2e-3:
                flag("FAIL","merge",f"sourced catalyst {r.reaction[:30]} {col}: merged {m_val} != sourced solve {expect}"); ok=False
        elif r.reaction not in MEDIATED:
            # The published matrix has been FULL-PHYSICS (Nernst-Planck + migration) for all 50
            # rows since 2026-08-24, so the non-mediated cells must equal all50_np_matrix.csv --
            # NOT tier0_matrix.csv, which is the migration-free Fick layer and differs on every
            # charged carrier (Kolbe x2.006, decarboxylative elimination x2.876). This compared
            # against tier0 until 2026-08-25 and reported all 300 cells as failures: the checker
            # was asserting an invariant the model had deliberately left behind.
            sub = npm[(npm.reaction == r.reaction) & (npm.reactor.map(rmap) == col)]
            if not len(sub):
                flag("FAIL","merge",f"non-mediated row {i+1} {col}: no NP cell for this (row, reactor)"); ok=False; continue
            t_val = float(sub.iloc[0].i_np_mAcm2)
            if abs(m_val-t_val)/max(t_val,1e-9) > 2e-3:
                flag("FAIL","merge",f"non-mediated row {i+1} {col}: merged {m_val} != NP {t_val}"); ok=False
        else:
            sub = med[(med.reaction==r.reaction)]
            row = sub[sub.reactor.map(rmap)==col].iloc[0]
            expect = max(row.i_ec_mAcm2, row.i_tier0_mAcm2) if row.flag=="wall" else row.i_ec_mAcm2
            if abs(m_val-expect)/max(expect,1e-9) > 2e-3:
                flag("FAIL","merge",f"mediated {r.reaction[:30]} {col}: merged {m_val} != expected {expect}"); ok=False
print("merge override logic:", "PASS" if ok else "FAIL")

# ---------- 3. Table S5 cells ------------------------------------------------
cols = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
s5 = {c: (mg[c].median(), int((mg[c]>=25).sum()), int((mg[c]>=50).sum())) for c in cols}
# DERIVED, NOT PINNED. This block used to carry a typed s5_expect dict, so every property
# correction forced an edit here and the gate reported a "failure" that was only its own
# staleness -- the trap CLAUDE.md names as "never type a pinned expectation you could derive".
# The model is the authority: format each row the way make_si.js does and require THAT string
# to appear in the shipped SI. A drift between model and SI still fails; a drift between the
# model and this file is now impossible.
def _fmt_med(v):
    return f"{v:.0f}" if v >= 100 else f"{v:.1f}"
ARCH_LABEL = {"natural": "Unstirred batch", "stirred": "Stirred batch",
              "flow": "Recirculating flow cell", "anec": "ANEC flow cell", "micro": "Microfluidic cell (25 \u03bcm gap)",
              "rde": "RDE 1600 rpm", "rce": "Rotating cylinder 3000 rpm"}
for c,(md,n25,n50) in s5.items():
    # Bind the numbers to the archetype NAMED BESIDE THEM in the shipped table, so a value that
    # happens to coincide with another row's cannot satisfy this (CLAUDE.md trap 11).
    row = f"{ARCH_LABEL[c]}{_fmt_med(md)}{n25}/50{n50}/50"
    if row not in si_doc:
        flag("FAIL","TableS5",
             f"{c}: the shipped SI does not carry the model's row {row!r} -- Table S5 is stale "
             f"against julia/tier0_ec_matrix.csv")
print("Table S5 cells: checked")

# ---------- 4. Table S6 cells ------------------------------------------------
s6 = {}
for rxn in med.reaction.unique():
    g = med[med.reaction==rxn]
    st = g[g.reactor=="Stirred batch"].iloc[0]; tg = g[g.reactor=="ANEC flow cell"].iloc[0]
    s6[rxn] = (g.xk_um.iloc[0], st.i_tier0_mAcm2, st.i_ec_mAcm2, tg.i_tier0_mAcm2, tg.i_ec_mAcm2)
# DERIVED, NOT PINNED. This block used to hold an `s6_expect` dict of typed numbers -- the trap
# CLAUDE.md names -- so it compared the model against literals that nobody re-derived when the
# solver moved, and it went on "failing" against a table that was itself stale. Now the expected
# cell text is BUILT from the matrix with the same formatters make_si.js uses, and required to
# appear in the SHIPPED SI. A drift between model and document fails; a drift between the model
# and this file is impossible.
S6_LABEL = {
    "Br-mediated Hofmann rearrangement": "Br\u207b / Hofmann rearrangement (80 mM, MeCN)",
    "ACT-mediated alcohol oxidation (flow, hectogram)": "ACT / alcohol oxidation (25 mM, aq. pH 8.5)",
    "Cl-mediated ethylene epoxidation": "Cl\u207b / ethylene epoxidation (1 M KCl, aq.)",
    "NHPI-mediated allylic C-H -> enone": "NHPI / allylic C\u2013H (33 mM, acetone)",
    "HMF -> FDCA (biomass)": "ACT / HMF \u2192 FDCA (40 mM, aq. pH 10)",
    "BQ-mediated Wacker-Tsuji oxidation": "BQ / Wacker\u2013Tsuji (22 mM, MeCN/H\u2082O)",
    "Br- oxidation / electrophilic bromination": "electrophilic bromination (0.152 M",
    "Aryl thiocyanation (NH4SCN)": "SCN\u207b / thiocyanation (0.1 M, AcOH/HCOOH)",
}
def _fxk(v):  return f"{v:.0f}" if v >= 100 else f"{v:.1f}"
def _fcur(v): return f"{v:.0f}" if v >= 10  else f"{v:.1f}"
for rxn, (xk, st0, stEC, tg0, tgEC) in s6.items():
    want = f"{_fxk(xk)}{_fcur(st0)} \u2192 {_fcur(stEC)}{_fcur(tg0)} \u2192 {_fcur(tgEC)}"
    if want not in si_doc:
        flag("FAIL","TableS6",
             f"{rxn[:38]}: the shipped SI does not carry the model's cells {want!r} -- Table S6 "
             f"is stale against julia/mediated_ec_matrix.csv")
    # and the numbers must sit on the row that NAMES this system, not merely somewhere in the doc
    lab = S6_LABEL.get(rxn)
    if lab and lab in si_doc:
        seg = si_doc[si_doc.index(lab): si_doc.index(lab) + 1600]
        if want not in seg:
            flag("FAIL","TableS6", f"{rxn[:38]}: cells {want!r} do not appear on its own row")
print("Table S6 cells: checked")

# ---------- 5. conc_provenance embedded arithmetic ---------------------------
n_checked = 0
for i, r in rx.iterrows():
    m = re.search(r"([\d.]+)\s*mmol\s*/\s*([\d.]+)(?:\.0)?\s*mL", str(r.conc_provenance))
    if not m: continue
    mmol, mL = float(m.group(1)), float(m.group(2))
    conc = mmol/mL
    # the row C should equal this within rounding IF the string describes the adopted value
    tgt = min([r.C_carrier_M, r.C_substrate_M], key=lambda c: abs(c-conc))
    n_checked += 1
    if abs(conc-tgt)/max(tgt,1e-9) > 0.12:
        flag("WARN","provenance-arith",f"row {i+1} {r.reaction[:36]}: string implies {conc:.3f} M, table has Cc={r.C_carrier_M} Cs={r.C_substrate_M}")
print(f"provenance arithmetic: {n_checked} rows with mmol/mL strings checked")

# ---------- 6. Julia MedSpec vs table ----------------------------------------
jl = open(P("julia", "run_mediated.jl")).read()
specs = re.findall(r'MedSpec\("([^"]+)",\s*([\d.e+-]+),\s*([\d.e+-]+),\s*([\d.e+-]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.e+-]+)', jl)
for label, k, nu_s, Dred, nc, nS, Cmed, CS, DS in specs:
    row = rx[rx.reaction==label]
    if not len(row): flag("FAIL","medspec",f"spec '{label}' has no table row"); continue
    r = row.iloc[0]
    if abs(float(Cmed)-r.C_carrier_M*1000)/max(r.C_carrier_M*1000,1e-9) > 0.01:
        flag("FAIL","medspec",f"{label}: C_med {Cmed} vs table {r.C_carrier_M*1000}")
    if abs(float(CS)-r.C_substrate_M*1000)/max(r.C_substrate_M*1000,1e-9) > 0.01:
        flag("FAIL","medspec",f"{label}: C_S {CS} vs table {r.C_substrate_M*1000}")
    if abs(float(Dred)-r.D_cm2s*1e-4)/max(r.D_cm2s*1e-4,1e-30) > 0.03:
        flag("FAIL","medspec",f"{label}: D_red {Dred} vs table {r.D_cm2s*1e-4:.3e}")
    nu_tab = sol.loc[r.solvent].mu_mPas*1e-3/(sol.loc[r.solvent].rho*1000)
    if abs(float(nu_s)-nu_tab)/nu_tab > 0.02:
        flag("FAIL","medspec",f"{label}: nu {nu_s} vs solvent table {nu_tab:.3e}")
print(f"MedSpec vs table: {len(specs)} specs checked")

# ---------- 7. cross-file constants ------------------------------------------
pj = open(P("julia", "params.jl")).read()
fj = re.search(r"F_const\s*=\s*([\d.e]+)", pj)
if fj and abs(float(fj.group(1))-96485.33) > 0.5: flag("FAIL","constants",f"params.jl F={fj.group(1)}")
for fname in ["make_fig4A.py","make_figs.py","make_fig_main.py"]:
    s = open(FIG(fname)).read()
    if "BARRIER=50" not in s.replace(" ","") and "BARRIER = 50" not in s:
        flag("WARN","constants",f"{fname}: BARRIER definition not found/nonstandard")
print("constants: checked")

# ---------- 8. figure-label numbers vs CSV ------------------------------------
def get_row(frag): return rx[rx.reaction.str.contains(frag, regex=False)].iloc[0]
label_checks = [
 ("make_figs.py","BASF methoxylation (0.8 M)", get_row("4-tBu-toluene").C_carrier_M, 0.81),
 ("make_figs.py","ADN (6.9 M)", get_row("Acrylonitrile").C_carrier_M, 6.85),
 ("make_figs.py","sulfone, kilo-scale (0.47 M)", get_row("sulfone").C_carrier_M, 0.47),
 ("make_figs.py","Birch (0.14 M)", get_row("Birch").C_carrier_M, 0.141),
 ("make_figs.py","Ni-XEC (cat. 15 mM)", get_row("Ni-XEC").C_carrier_M, 0.015),
 ("make_figs.py","ACT-mediated (med. 25 mM)", get_row("ACT-mediated").C_carrier_M, 0.025),
 ("make_figs.py","Kolbe (1 M)", get_row("Kolbe").C_carrier_M, 1.00),
 ("make_fig_main.py","Shono oxidation (1.56 M)", get_row("Shono oxidation").C_carrier_M, 1.56),
 ("make_fig_main.py","decarboxylative C–C (0.03 M)", get_row("Doubly").C_carrier_M, 0.029),
]
# The expected value is READ OUT OF THE LABEL, not typed beside it: the third element is only a
# convenience for the message. A label and a table that disagree fail; this file cannot go stale.
_LBL = re.compile(r"\(\s*(?:cat\.\s*|med\.\s*)?([\d.]+)\s*(mM|M)\s*\)")
for fname, lab, actual, printed in label_checks:
    s = open(FIG(fname)).read()
    if lab not in s:
        flag("FAIL","fig-labels",f"{fname}: label '{lab}' missing -- reworded labels stop being checked")
        continue
    m = _LBL.search(lab)
    if not m:
        flag("FAIL","fig-labels",f"{lab}: no concentration parsed out of the label"); continue
    shown = float(m.group(1)) * (1e-3 if m.group(2) == "mM" else 1.0)
    if abs(actual-shown)/shown > 0.05:
        flag("FAIL","fig-labels",f"{lab}: table C={actual} vs label {shown}")
print("figure labels: checked")

# ---------- 9. SI headline claims ---------------------------------------------
# DERIVED FROM THE SHIPPED SI, NOT PINNED. These were typed numbers compared against the model,
# so every property correction turned them into false failures and nothing checked the document.
# Now each is built from the matrix with make_si.js's own formatters and required to appear in the
# SI, bound to the architecture named beside it.
import unicodedata as _ud
# The shipped document is NFKC-folded by docx_text, which turns the superscript minus U+207B into
# U+2212 and the superscript two into an ASCII 2 (CLAUDE.md trap 12). Needles must be folded the
# same way or they match nothing while the document is perfectly correct.
def _n(x): return _ud.normalize("NFKC", x)
def _fmed(v):  return f"{v:.0f}" if v >= 100 else f"{v:.1f}"
def _fmedI(v): return f"{v:.0f}"
claims = [
 ("unstirred median in the SI headline sentence",
  _n(f"rises from {_fmed(mg.natural.median())} mA cm\u207b\u00b2 in an unstirred batch cell") in si_doc),
 ("flow median in the SI headline sentence",
  _n(f"to {_fmedI(mg.flow.median())} mA cm\u207b\u00b2 in a recirculating flow cell") in si_doc),
 ("RCE median in the SI headline sentence",
  _n(f"\u2248{_fmedI(mg.rce.median())} mA cm\u207b\u00b2 at a turbulent rotating-cylinder") in si_doc),
 (">=25 uplift in the SI headline sentence",
  f"rises from {int((mg.natural>=25).sum())}/50 to {int((mg.rce>=25).sum())}/50" in si_doc),
 ("subs 28/31 clear25", None),  # computed below
]
m2 = mg.merge(rx[["reaction","carrier_type","C_carrier_M"]], on="reaction")
m2["best"] = m2[cols].max(axis=1)
sub_ok = ((m2[m2.carrier_type=="substrate"].best>=25).sum(), (m2.carrier_type=="substrate").sum())
cat_no = ((m2[m2.carrier_type=="catalyst"].best<25).sum(), (m2.carrier_type=="catalyst").sum())
act_best = m2[m2.reaction.str.contains("ACT-mediated")].best.iloc[0]
print(f"substrate clear-25-somewhere: {sub_ok[0]}/{sub_ok[1]} (SI claims 28/31)")
print(f"catalyst never-25: {cat_no[0]}/{cat_no[1]} (SI claims 10/11)")
print(f"ACT best {act_best:.1f} (SI claims plateau 22)")
# DERIVED, NOT PINNED: build the phrase the SI would have to print and require it there.
# These were typed tuples (28,31) and (10,11), so they compared the model to two literals and
# nothing checked the document; a partition change would have been reported as a gate failure
# rather than as prose drift.
_p_sub = _n(f"{sub_ok[0]} of the {sub_ok[1]} substrate-carried")
_p_cat = _n(f"{cat_no[0]} of the {cat_no[1]} reactions whose current is carried")
if _p_sub not in si_doc:
    flag("FAIL","SI-claims",f"the shipped SI does not carry {_p_sub!r}")
if _p_cat not in si_doc:
    flag("FAIL","SI-claims",f"the shipped SI does not carry {_p_cat!r}")
if not (21.5 <= act_best <= 23):  flag("FAIL","SI-claims",f"ACT best {act_best} vs claimed 22")
for pat, cond in claims:
    if cond is None: continue
    if not cond: flag("FAIL","SI-claims", pat)
# The three EC'-uplift claims that lived here ("stirred >=50 13 -> 14", "flow 13 -> 14",
# "thingap 22 -> 24") were pinned integers testing a sentence the SI NO LONGER CONTAINS -- the
# uplift claim was replaced by the sensitivity bracket of S5.5, which data/check_ecprime_band.py
# (G-ECBAND) derives from both matrices and gates properly. They were also comparing the published
# matrix against tier0_matrix.csv, which since the 2026-08-24 one-physics merge differs by
# migration as well as by the EC' source, so the difference was no longer an EC' uplift at all.
# Removed rather than re-pinned; G-ECBAND is the gate for that claim.
print("SI headline claims: checked")

# ---------- 10. gate table vs SI S5.6 text -------------------------------------
# This check was a stub: it assigned g11 and never used it, then printed the gate NAMES and
# returned. The pass column -- the only thing that says whether the Julia solver audit actually
# succeeded -- was never inspected, so a failing solver gate reached this summary as "present".
_bad = gates[~gates["pass"].astype(str).str.strip().str.lower().isin(["true","1"])]
for _, _r in _bad.iterrows():
    flag("FAIL", "julia-audit",
         f"{_r.gate} did NOT pass in julia/audit_gates.csv: {str(_r.description)[:70]} "
         f"(solver {_r.solver} vs analytic {_r.analytic}, err {_r.err_pct}%)")
_missing = {"G1","G2","G3","G4","G5","G6","G7","G8a","G8b","G9","G10","G11"} - set(gates.gate)
if _missing:
    flag("FAIL", "julia-audit", f"audit_gates.csv is missing gates {sorted(_missing)}")
print(f"julia audit gates: {len(gates)} rows, {len(gates)-len(_bad)} pass, {len(_bad)} fail")

print("\n================ SUMMARY ================")
if not findings: print("ALL DETERMINISTIC CHECKS PASS — no discrepancies found")
else:
    print(f"{len(findings)} findings:")
    for sev, wh, msg in findings: print(f"  [{sev}] {wh}: {msg}")
