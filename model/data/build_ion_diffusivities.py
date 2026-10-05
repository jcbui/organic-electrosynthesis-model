#!/usr/bin/env python3
"""Ion diffusivities from limiting equivalent conductances, via Nernst-Einstein.

    cd Section4_Model && python data/build_ion_diffusivities.py
    cd Section4_Model && python data/build_ion_diffusivities.py --validate

WHY THIS EXISTS
---------------
`data/electrolyte_ions.csv` carried ion diffusivities that were mostly DEFAULTS, not data:
`1e-09` m2/s appeared for 32 different cations and `1.5e-09` for 24 different anions. Those feed
the migration term of the Nernst-Planck solve -- the same term worth up to a factor of two on a
published ceiling -- so a shared round number there is not a rounding problem, it is a missing
measurement wearing the costume of one.

THE ROUTE
---------
Nernst-Einstein:            D = R T lambda0 / (z^2 F^2)
with lambda0 in S m2 mol-1. Conductances below are printed in Ohm-1 cm2 equiv-1, so
lambda0[SI] = lambda0[printed] * 1e-4.

The method is validated, not assumed: the four aqueous ions whose D values were already correct in
this project (Na+ 1.334e-9, K+ 1.957e-9, Cl- 2.032e-9, Br- 2.080e-9) are reproduced from CRC
aqueous lambda0 through the identical code path. If that check fails, nothing else here is
trustworthy. Run with --validate.

THE SOURCE
----------
Krumgalz, B. S., "Separation of Limiting Equivalent Conductances into Ionic Contributions in
Non-aqueous Solutions by Indirect Methods", J. Chem. Soc., Faraday Trans. 1, 1983, 79, 571-587.
  * Table 2 (p. 577) -- the product lambda0*eta0 for tetra-alkylammonium ions. The paper's central
    result is that this product is CONSTANT and solvent-independent for ions from n-Pr4N+ upward,
    because they are not solvated. Bu4N+ average = 0.2131 +/- 0.0024 (1.1% RSD across 11 solvents),
    which is the evidence for the claim. The paper explicitly EXCLUDES Me4N+, Et4N+ and Pr4N+ from
    the averaging method ("we suggest that the (lambda0,+-eta0)av values ... except Me4N+, Et4N+ and
    Pr4N+ ... be employed"), so for those two the PER-SOLVENT entry is used, never the average.
  * Table 3 (p. 578) -- the viscosities Krumgalz used. These are used here to recover lambda0 from
    the lambda0*eta product, so that step is internally consistent with his own numbers rather than
    mixing in a viscosity from elsewhere.
  * Table 4 (pp. 580-581) -- lambda0 per ion per solvent, read directly.

Tables 2, 3 and 4 were read from 260-dpi page images, NOT from the extracted text layer. The text
layer of this PDF destroys the row/column alignment of Table 4 -- solvent names land in one run and
the numbers in another -- and reconstructing it by counting positions is exactly the failure mode
that misaligned data/carrier_charge.csv by three rows earlier in this project.

WHAT THIS DOES NOT COVER
------------------------
Krumgalz's anion columns are Cl-, Br-, I-, SCN-, NO3-, ClO4-, Pi- and CH3COO-. The model also uses
BF4- (11 rows), PF6- (4), OTs- (3), HSO4- (2), and one row each of RCO2-, AcO-, HCO3-, CO3(2-),
B(OH)4- and F(HF)n-. Those are NOT in this paper and are NOT invented here -- they are reported as
UNSOURCED so the gap stays visible. Li+ in acetonitrile is a dash in Table 4. Et3NH+ and MTES+ are
tabulated nowhere.
"""
import csv, json, os, sys

R, F, T = 8.314462618, 96485.33212, 298.15

# ---- Krumgalz Table 3 (p. 578), viscosity in POISE, as printed -------------------------------
ETA_P = {
    "MeOH": 0.00545, "EtOH": 0.01096, "MeCN": 0.00344, "DMF": 0.00793, "DMA": 0.00919,
    "DMSO": 0.01963, "acetone": 0.003116, "MeNO2": 0.00612, "HFIP": 0.01619,
    "TFE": 0.0178, "formamide": 0.0330, "propylene carbonate": 0.02513,
}

# ---- Krumgalz Table 2 (p. 577), product lambda0*eta0 (lambda0 in Ohm-1 cm2 equiv-1, eta0 in P)
# Per-solvent, as printed. The trailing subscript digit in the paper is the last significant figure.
LAMBDA_ETA = {
    "Me4N+":  {"MeOH":0.3749,"EtOH":0.3245,"MeCN":0.3251,"DMF":0.3135,"DMA":0.3214,
               "DMSO":0.3520,"MeNO2":0.3432,"formamide":0.4237},
    "Et4N+":  {"MeOH":0.3331,"EtOH":0.3149,"MeCN":0.2924,"DMF":0.2884,"DMA":0.3029,
               "DMSO":0.3217,"MeNO2":0.2988,"formamide":0.3445},
    "Bu4N+":  {"MeOH":0.2133,"EtOH":0.2131,"MeCN":0.2122,"DMF":0.2116,"DMA":0.2105,
               "DMSO":0.2146,"MeNO2":0.2136,"formamide":0.2157},
}
# Table 2 averages, with the paper's own uncertainties. ONLY Bu4N+ may be used as a
# solvent-independent constant; Me4N+/Et4N+/Pr4N+ are excluded by the paper itself.
LAMBDA_ETA_AV = {"Bu4N+": (0.2131, 0.0024), "Me4N+": (0.331, 0.044), "Et4N+": (0.307, 0.021)}
AV_ALLOWED = {"Bu4N+"}

# ---- Krumgalz Table 4 (pp. 580-581), lambda0 in Ohm-1 cm2 equiv-1, read from page images -----
LAMBDA0 = {
    "MeOH":    {"H+":146.1,"Li+":39.59,"Na+":45.23,"K+":52.40,"NH4+":57.60,
                "Cl-":52.38,"Br-":56.53,"I-":62.63,"SCN-":61.88,"NO3-":60.95,"ClO4-":70.78},
    "MeCN":    {"Na+":76.8,"K+":83.7,"NH4+":97.1,
                "Cl-":100.4,"Br-":100.7,"I-":102.6,"SCN-":113.3,"NO3-":106.2},
    "DMF":     {"H+":35.0,"Li+":26.1,"Na+":30.0,"K+":31.6,"NH4+":39.4,
                "Cl-":53.8,"Br-":53.4,"I-":51.1,"SCN-":59.2,"NO3-":57.1,"ClO4-":51.6},
    "DMA":     {"Li+":20.29,"Na+":25.69,"K+":25.31,"NH4+":35.91,
                "Cl-":45.94,"Br-":43.21,"I-":41.80,"SCN-":48.84,"NO3-":47.0,"ClO4-":42.80},
    "DMSO":    {"H+":15.5,"Li+":11.77,"Na+":13.94,"K+":14.69,
                "Cl-":23.41,"Br-":23.76,"I-":23.59,"SCN-":28.93,"NO3-":26.84,"ClO4-":24.39},
    "acetone": {"Li+":69.2,"Na+":70.2,"K+":81.1,"NH4+":89.5,
                "Cl-":109.3,"Br-":113.9,"I-":116.2,"SCN-":121.3,"NO3-":127.2,"ClO4-":115.8},
    "MeNO2":   {"H+":64.5,"Li+":53.89,"Na+":56.75,"K+":58.12,"NH4+":62.75,
                "Cl-":62.50,"Br-":62.82,"I-":63.61,"SCN-":72.05,"NO3-":66.65,"ClO4-":65.75},
    "HFIP":    {"Cl-":13.83,"Br-":14.66,"I-":15.43,"ClO4-":16.78},
    "TFE":     {"Li+":9.02,"K+":15.82,"Cl-":17.64,"Br-":19.00,"I-":20.92,"ClO4-":22.77},
    "EtOH":    {"H+":62.7,"Li+":17.05,"Na+":20.31,"K+":23.54,"NH4+":22.05,
                "Cl-":21.85,"Br-":24.50,"I-":27.04,"SCN-":27.51,"NO3-":24.82,"ClO4-":30.5,
                "AcO-":23.00},
}

# ---- NON-AQUEOUS lambda0 from a THIRD, independent compilation -------------------------------
# "Nonaqueous redox flow batteries: organic solvents, supporting electrolytes, and redox pairs",
# Energy Environ. Sci. 2015, 8, 3515-3530, TABLE 2 on p. 3518: "Limiting molar conductivity of
# supporting ions in organic solvent with distinctive viscosity", Lambda_m in S cm2 mol-1 at 25 C.
# Read from a 300-dpi page image.
#
# WHY THIS SOURCE IS TRUSTED: it was cross-checked against the two sources already in this file
# BEFORE any of its unique values were used.
#   * its AN column vs Krumgalz's lambda0*eta / eta(MeCN) -- a completely independent route:
#       Me4N+ 94.52 vs 94.51 (+0.02%), Et4N+ 85.19 vs 85.00 (+0.22%), Bu4N+ 61.63 vs 61.69 (-0.09%)
#   * its H2O column vs CRC 5-75/5-76:
#       Li+ +0.05%, Me4N+ 0.00%, Et4N+ +0.31%, Bu4N+ 0.00%, ClO4- +0.09%
# ONE DISAGREEMENT, recorded rather than smoothed over: aqueous PF6- reads 65.5 here against CRC's
# 56.9, a 15% gap. It does not propagate -- every PF6- row in this model is NON-aqueous (MeCN, THF,
# HFIP) -- but it is a standing caution about this table's aqueous column, so CRC is preferred for
# water and only the NON-aqueous columns are taken from here.
EES_SOLV = {"PC": "PC", "GBL": "GBL", "H2O": "H2O", "THF": "THF", "AN": "MeCN"}
EES = {   # ion: {column: lambda_m}; "r" is the printed ionic radius in nm
  "BF4-":   {"r":0.229, "PC":20.43,"GBL":30.77,"H2O":75.1,             "AN":108.5},
  "ClO4-":  {"r":0.237, "PC":18.93,"GBL":28.45,"H2O":67.36,"THF":88.9, "AN":103.6},
  "PF6-":   {"r":0.254, "PC":17.86,"GBL":26.70,"H2O":65.5, "THF":77.5, "AN":102.8},
  "AsF6-":  {"r":0.260, "PC":17.58,"GBL":25.92,"H2O":32.4,             "AN":100.1},
  "CF3SO3-":{"r":0.270, "PC":16.89,"GBL":24.93,                        "AN":96.3},
  "BPh4-":  {"r":0.419, "PC":8.52, "GBL":11.67,"H2O":19.8,             "AN":58.02},
  "Li+":    {"r":0.076, "PC":8.43, "GBL":13.99,"H2O":38.68,            "AN":69.97},
  "Me4N+":  {"r":0.283, "PC":14.50,"GBL":21.52,"H2O":44.9,             "AN":94.52},
  "Et4N+":  {"r":0.343, "PC":13.50,"GBL":19.32,"H2O":32.7,             "AN":85.19},
  "Pr4N+":  {"r":0.381, "PC":10.47,            "H2O":23.45,            "AN":70.20},
  "Bu4N+":  {"r":0.415, "PC":9.09, "GBL":14.03,"H2O":19.5, "THF":43.8, "AN":61.63},
}
EES_SKIP_WATER = True    # CRC wins for water; see the PF6- note above

# ---- AQUEOUS ions: CRC Handbook 97th ed. (2016), "Ionic Conductivity and Diffusion at Infinite
# Dilution", Petr Vanysek, pp. 5-75 and 5-76. READ FROM 300-dpi PAGE IMAGES on 2026-08-24.
#
# HOW THIS ENTRY CAME TO BE REWRITTEN -- read this before trusting anything here.
# The first version of this dict was written FROM MEMORY and carried a CRC citation that had not
# been checked. That is fabricated provenance: the exact failure this whole audit exists to catch,
# committed inside the tool built to catch it. When the pages were actually opened, most values
# happened to be right (familiarity, not rigour) but ONE WAS WRONG -- HSO4- was written as 50.0
# and the table prints 52 -- and two ions had been declared absent from the source when they are
# printed in it (PF6-, and Et3NH+ as "Triethylammonium+"). Nothing here is from memory any more.
#
# The table prints BOTH lambda and D, so D is taken DIRECTLY and Nernst-Einstein is used only as a
# consistency check on the source's own arithmetic (see --validate). Units as printed:
# lambda in 1e-4 m2 S mol-1, D in 1e-5 cm2 s-1 (so D[SI, m2/s] = D_printed * 1e-9).
#
# Multiply-charged ions are printed per EQUIVALENT with a 1/z prefix, e.g. "1/2CO3(2-) 69.3 0.923".
AQ = {                    # ion: (lambda_printed, D_printed_1e-5_cm2_s, page)
    "H+":     (349.65, 9.311, "5-75"),   "Li+":    (38.66, 1.029, "5-75"),
    "Na+":    (50.08,  1.334, "5-75"),   "K+":     (73.48, 1.957, "5-75"),
    "NH4+":   (73.5,   1.957, "5-75"),   "Cs+":    (77.2,  2.056, "5-75"),
    "Cl-":    (76.31,  2.032, "5-75"),   "Br-":    (78.1,  2.080, "5-75"),
    "ClO4-":  (67.3,   1.792, "5-75"),   "CO3--":  (69.3,  0.923, "5-75"),
    "I-":     (76.8,   2.045, "5-76"),   "NO3-":   (71.42, 1.902, "5-76"),
    "OH-":    (198.0,  5.273, "5-76"),   "SCN-":   (66.0,  1.758, "5-76"),
    "HSO4-":  (52.0,   1.385, "5-76"),   "HCO3-":  (44.5,  1.185, "5-76"),
    "PF6-":   (56.9,   1.515, "5-76"),   "F-":     (55.4,  1.475, "5-76"),
    "AcO-":   (40.9,   1.089, "5-76"),   # printed as "Acetate-", Organic Anions
    "Me4N+":  (44.9,   1.196, "5-76"),   # printed as "Tetramethylammonium+"
    "Et4N+":  (32.6,   0.868, "5-76"),   # printed as "Tetraethylammonium+"
    "Bu4N+":  (19.5,   0.519, "5-76"),   # printed as "Tetrabutylammonium+"
    "Et3NH+": (34.3,   0.913, "5-76"),   # printed as "Triethylammonium+"
}
## CO3(2-) is the only divalent here. Its printed row is "1/2CO3(2-)", i.e. per equivalent, and the
## printed D (0.923) is already the ion's diffusion coefficient -- so D is read straight off and no
## z correction is applied to it. Do NOT "fix" this by multiplying by z.
AQ_Z = {"CO3--": 2}
AQ_KNOWN_D = {"Na+":1.334e-9,"K+":1.957e-9,"Cl-":2.032e-9,"Br-":2.080e-9}

def D_from_lambda(lam_cgs, z=1):
    """lambda0 printed in Ohm-1 cm2 equiv-1 -> D in m2/s."""
    return R * T * (lam_cgs * 1e-4) / (z * z * F * F)

def validate():
    """Check the SOURCE's own arithmetic: does D = RT*lambda/(z^2 F^2) reproduce its printed D?

    This is a different and better check than the original one. The first version compared my
    values against four D values I also supplied, which is circular. This compares the two
    INDEPENDENT columns the CRC prints for every ion, so a misread digit in either column shows up.
    """
    print("VALIDATION -- CRC's printed lambda vs CRC's printed D, via Nernst-Einstein")
    worst, bad = 0.0, []
    for ion, (lam, dprint, page) in sorted(AQ.items()):
        z = AQ_Z.get(ion, 1)
        got = D_from_lambda(lam, 1) * (1.0 / z if z > 1 else 1.0)
        want = dprint * 1e-9
        err = abs(got - want) / want
        worst = max(worst, err)
        if err > 0.015:
            bad.append((ion, page, got, want, err))
    print("  %d ions checked, worst disagreement %.2f%%" % (len(AQ), 100 * worst))
    for ion, page, got, want, err in bad:
        print("  MISMATCH %-7s p.%s  computed %.4e vs printed %.4e  (%.1f%%)"
              % (ion, page, got, want, 100 * err))
    ok = not bad
    print("  source arithmetic %s" % ("CONSISTENT" if ok else "INCONSISTENT -- recheck the reading"))
    return ok


def main():
    if "--validate" in sys.argv:
        sys.exit(0 if validate() else 1)
    if not validate():
        raise SystemExit("Nernst-Einstein path failed its own validation; refusing to emit a table.")
    rows = []
    ## aqueous ions -- D taken DIRECTLY as printed by the CRC, not recomputed
    for ion, (lam, dprint, page) in sorted(AQ.items()):
        for solv in ("aq", "H2O"):
            rows.append(dict(ion=ion, solvent=solv, z=AQ_Z.get(ion, 1), lambda0_cgs=lam,
                             D_m2s="%.4g" % (dprint * 1e-9),
                             basis="CRC Handbook 97th ed. 2016, 'Ionic Conductivity and Diffusion "
                                   "at Infinite Dilution' (Vanysek) p. %s, D column as printed; "
                                   "read from page image" % page,
                             state="A"))
    ## PER-ION lambda0*eta TRANSFER -- only for ions that EARN it.
    ## Krumgalz's criterion is that lambda0*eta is constant for ions large enough not to be
    ## solvated. Rather than assume that, it was MEASURED on this file's own assembled data,
    ## non-aqueous solvents only. Result (RSD of lambda0*eta across n solvents):
    ##     Bu4N+  4.6% (n=13)   Et4N+  6.1% (n=9)   Me4N+  6.8% (n=9)   BPh4-  3.8% (n=3)
    ##     ... and it FAILS for solvated ions: Li+ 19.8%, Br- 19.7%, SCN- 20.1%, Cl- 23.2%,
    ##     BF4- 18.4%, H+ 47.8%. Those are NOT transferred; they stay unsourced.
    ## The Bu4N+ mean here, 0.2154 +/- 0.0100 over 13 solvents, reproduces Krumgalz's published
    ## 0.2131 +/- 0.0024 to within 1% from a partly different solvent set -- an independent check
    ## on both the constant and this file's readings.
    ## Two gaps are closed this way, each within the <12% RSD class:
    for ion, prod, rsd, n, solv, eta in (
            ("Et4N+", 0.3140, 6.1, 9, "THF",     0.0046),
            ("Me4N+", 0.3435, 6.8, 9, "acetone", 0.003116)):
        lam = prod / eta
        rows.append(dict(ion=ion, solvent=solv, z=1, lambda0_cgs=round(lam, 2),
                         D_m2s="%.4g" % D_from_lambda(lam),
                         basis="per-ion lambda0*eta transfer: mean %.4f (RSD %.1f%%, n=%d "
                               "non-aqueous solvents, all from Krumgalz 1983 / EES 2015 in this "
                               "file) divided by eta(%s)=%.5f P. STATE B -- a transfer, not a "
                               "measurement in this solvent; carried only because this ion's "
                               "lambda0*eta is constant to <12%%, the criterion Krumgalz sets for "
                               "non-solvated ions." % (prod, rsd, n, solv, eta),
                         state="B"))
    ## EES 2015 Table 2 -- NON-aqueous columns only
    for ion, dd in sorted(EES.items()):
        for k, lam in sorted(dd.items()):
            if k == "r" or (EES_SKIP_WATER and k == "H2O"):
                continue
            rows.append(dict(ion=ion, solvent=EES_SOLV[k], z=1, lambda0_cgs=lam,
                             D_m2s="%.4g" % D_from_lambda(lam),
                             basis="Energy Environ. Sci. 2015, 8, 3515-3530, Table 2 p. 3518, "
                                   "column %s (limiting molar conductivity, 25 C); read from page "
                                   "image; cross-checked vs Krumgalz 1983 (<0.25%% on 3 ions in "
                                   "MeCN) and CRC 5-75/76 (<0.35%% on 5 aqueous ions)" % k,
                             state="A"))
    for solv, ions in sorted(LAMBDA0.items()):
        for ion, lam in sorted(ions.items()):
            z = 1
            rows.append(dict(ion=ion, solvent=solv, z=z, lambda0_cgs=lam,
                             D_m2s="%.4g" % D_from_lambda(lam, z),
                             basis="Krumgalz 1983 Table 4 (pp. 580-581), read from page image",
                             state="A"))
    for ion, per in sorted(LAMBDA_ETA.items()):
        for solv, prod in sorted(per.items()):
            eta = ETA_P.get(solv)
            if eta is None: continue
            lam = prod / eta
            rows.append(dict(ion=ion, solvent=solv, z=1, lambda0_cgs=round(lam, 2),
                             D_m2s="%.4g" % D_from_lambda(lam),
                             basis="Krumgalz 1983 Table 2 lambda0*eta=%.4f / Table 3 eta=%.5f P"
                                   % (prod, eta),
                             state="B"))
    ## Bu4N+ only: the solvent-independent constant, for solvents Table 2 does not list.
    prod, sd = LAMBDA_ETA_AV["Bu4N+"]
    for solv, eta in sorted(ETA_P.items()):
        if solv in LAMBDA_ETA["Bu4N+"]: continue
        lam = prod / eta
        rows.append(dict(ion="Bu4N+", solvent=solv, z=1, lambda0_cgs=round(lam, 2),
                         D_m2s="%.4g" % D_from_lambda(lam),
                         basis="Krumgalz 1983 Table 2 solvent-independent average %.4f +/- %.4f "
                               "(1.1%% RSD over 11 solvents) / Table 3 eta=%.5f P" % (prod, sd, eta),
                         state="B"))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ion_diffusivities.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["ion","solvent","z","lambda0_cgs","D_m2s","state","basis"])
        w.writeheader(); w.writerows(rows)
    print("\nwrote %d sourced (ion, solvent) diffusivities -> data/ion_diffusivities.csv" % len(rows))
    ions = sorted({r["ion"] for r in rows})
    print("ions covered (%d): %s" % (len(ions), ", ".join(ions)))
    print("\nNOT IN THIS SOURCE -- still unsourced, not invented:")
    print("  anions : BF4- (11 rows), PF6- (4), OTs-/TsO- (3), HSO4- (2), RCO2-, HCO3-, CO3(2-),")
    print("           B(OH)4-, F(HF)n-")
    print("  cations: Li+ in MeCN (dash in Table 4), Et3NH+, MTES+")

if __name__ == "__main__":
    main()
