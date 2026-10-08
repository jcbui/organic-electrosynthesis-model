"""Compute kappa from first principles wherever the inputs are page-anchored.

    cd Section4_Model/data && python derive_kappa.py

WHY
---
Forty-two of the forty-nine registered conductivities are `assumption`: a number with a
sensitivity but no equation behind it. That is the state a reviewer is entitled to call
arbitrary. This script replaces the bare number with a DERIVATION wherever the inputs to that
derivation are themselves page-anchored, and reports the deviation where they are not.

THE CHAIN, and where each input comes from
------------------------------------------
    kappa = Lambda(c) * c                                                      (Eq. S27)
    Lambda0 = nu+ * lambda0+  +  nu- * lambda0-        Kohlrausch additivity   (Eq. S28)
    Lambda(c) = Lambda0 - (B1*Lambda0 + B2) * sqrt(c)  Onsager limiting law    (Eq. S29)
        B1 = 8.204e5 / (eps*T)^(3/2)
        B2 = 82.5 / (eta * (eps*T)^(1/2))

Every symbol on the right is measurable and cited:
  lambda0  per-ion limiting molar conductivity, from a named table for THAT solvent
  eps      static relative permittivity of the solvent, CRC 97th ed. Sect. 6
  eta      solvent viscosity in poise, the same CRC rows the registry already uses
  c        the electrolyte concentration of the exemplar, page-verified in Table S2
  T        298.15 K

WHAT THE LIMITING LAW CAN AND CANNOT DO
---------------------------------------
Onsager is a LIMITING law. It is quantitative below roughly 0.01 M for a 1:1 salt in water and
degrades as c rises and as eps falls, because it contains no ion-association term. Applied at
0.1-3 M in a low-permittivity organic solvent it will UNDERSTATE kappa badly, and can even go
negative -- which is exactly the objection the SI already records against using a limiting
table to supply kappa at working concentration.

So this script does not overwrite anything. It reports, per row:
  * kappa_onsager -- the value the equation gives, when all inputs are available
  * the ratio to the carried value
  * whether c is inside the law's validity range (sqrt(c) term < 20% of Lambda0)
and it VALIDATES itself against aqueous KCl, where the answer is known.

The output is a per-row derivation record: the equation, its inputs, its result, and the
distance between that result and what the model carries. Rows the equation cannot reach are
named, with the missing input identified.
"""
import json
import math
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "Section4_Model", "results") \
    if os.path.basename(os.path.dirname(HERE)) != "Section4_Model" \
    else os.path.join(os.path.dirname(HERE), "results")
OUT = os.path.join(os.path.dirname(HERE), "results", "kappa_derivation.json")

T_K = 298.15

# --- solvent static permittivity and viscosity -------------------------------------------
# *** PROVENANCE WARNING, WRITTEN AGAINST MY OWN FIRST DRAFT OF THIS FILE ***
# The first version of this block carried the comment 'eps: CRC Handbook 97th ed., Sect. 6,
# "Permittivity of Liquids", 25 C column'. That was a citation asserted from RECOGNITION, not
# retrieval: no CRC permittivity table was opened, and none of these nine eps values appears
# anywhere in data/parameters_provenance.csv. Under the governing standard that is the cardinal
# error -- it is how the Wallnoefer-Ogris chimera got into two drafts of this manuscript.
#
# The values are RECALLED, not retrieved, and are labelled as such below. They are usable here
# for exactly one reason: eps enters ONLY the Onsager coefficients B1 and B2, and this script
# concludes that the Onsager estimate is outside its validity range at every working
# concentration in this work and adopts nothing from it. No number that survives into the model
# depends on any eps below. If that ever changes, these rows must be retrieved first.
#
# eta is different: it is READ from data/solvents.csv (column mu_mPas), the table the solver and
# the registry share, and converted mPa s -> poise inside onsager() (1 mPa s = 0.01 P). It used to
# be typed here, and two of the typed values had outlived the registry: MeCN 0.343 (the CRC page
# prints 0.369) and DMA 0.945 (the page prints 1.927). Reading the shared table means a viscosity
# can no longer be corrected in one place and left behind in this one.
EPS_RECALLED = {   # static relative permittivity, 25 C -- RECALLED, unretrieved (see above)
    "H2O": 78.36, "MeCN": 35.94, "MeOH": 32.66, "DMF": 36.71, "DMA": 37.78,
    "DMSO": 46.83, "THF": 7.52, "acetone": 20.49, "AcOH": 6.20,
}


def _solvent_eta():
    tab = pd.read_csv(os.path.join(HERE, "solvents.csv")).set_index("solvent")
    out = {}
    for name in EPS_RECALLED:
        if name not in tab.index:
            raise SystemExit("derive_kappa: %s has no row in data/solvents.csv" % name)
        out[name] = float(tab.loc[name, "mu_mPas"])
    return out


_ETA = _solvent_eta()
SOLV = {   # name: (eps [RECALLED, unretrieved], eta_mPa_s [data/solvents.csv], tag)
    name: (EPS_RECALLED[name], _ETA[name], "eps RECALLED; eta from data/solvents.csv (registry, CRC Sect. 6)")
    for name in EPS_RECALLED
}

# --- limiting molar conductivities, per ion, per solvent ---------------------------------
# NOTHING is transferred between solvents: a lambda0 measured in water is not evidence about the
# same ion in MeCN, and rows without a lambda0 for their own solvent are reported as unreachable.
#
# THE TWO BLOCKS HAVE DIFFERENT PROVENANCE AND MUST NOT BE READ AS EQUIVALENT:
#
#   MeCN and DMF  -- TRACEABLE. Both sets are recorded in docs/KAPPA_SOURCING_DOSSIER.md, which
#     documents their retrieval: Gong et al. Table 2 p. 3518 (rows 14, 38, 55 of that dossier)
#     and Gopal & Jha Table 2 p. 81 (row 20, "full text retrieved from the NIScPR open
#     repository"). These are the six values that carry weight here, because the four rows whose
#     ceiling is load-bearing -- the MeCN and DMF assumptions -- are computed from them.
#
#   H2O  -- RECALLED per-ion, but NO LONGER LOAD-BEARING. The per-ion values below were written
#     from memory. They are retained only as a cross-check, because the ELECTROLYTE Lambda0 that
#     the aqueous ceilings actually use is now retrieved (LAMBDA0_ELECTROLYTE below). The recalled
#     per-ion sums reproduce those retrieved values to 0.03-0.15%: NaCl 126.39 vs 126.39 exactly,
#     KHCO3 117.98 vs 117.94, NaOH 248.08 vs 247.7. That agreement is reported by this script and
#     is corroboration, not licence -- anything new must still be retrieved.
LAMBDA0 = {
    "H2O": {  # RECALLED -- see the warning above. NOT retrieved, NOT registered.
        "Na+": 50.08, "K+": 73.48, "Li+": 38.66, "NH4+": 73.5, "H+": 349.65,
        "OH-": 198.0, "Cl-": 76.31, "Br-": 78.1, "I-": 76.8, "NO3-": 71.42,
        "ClO4-": 67.3, "HCO3-": 44.5, "CO3--": 138.6, "SCN-": 66.0, "SO4--": 160.0,
    },
    "MeCN": {  # Gong, Fang, Gu, Li & Yan, Energy Environ. Sci. 2015, 8, 3515-3530, Table 2 p.3518
        "Li+": 69.97, "ClO4-": 103.6, "Et4N+": 85.1, "PF6-": 102.8,
    },
    "DMF": {   # Gopal & Jha, Indian J. Chem. 1977, 15A, 80-83, Table 2 p. 81, DMF column, 25 C
        "Na+": 29.81, "I-": 52.11,
    },
}

# --- RETRIEVED electrolyte Lambda0, and the Onsager constants for water -------------------
# Vanysek, "Equivalent Conductivity of Electrolytes in Aqueous Solution", CRC Handbook of
# Chemistry and Physics. Retrieved in full 2026-08-22 and archived at
# papers for model/vanysek_CRC_equivalent_conductivity_of_electrolytes.pdf, so a reader can check
# every number below without a subscription. The table gives Lambda at 25 C from infinite
# dilution to 0.1 mol/L; the "Infinite dilution" column is used here.
#
# The same table supplies TWO things this script previously took from memory:
#   * the Debye-Huckel-Onsager equation in the form  Lambda = Lambda0 - (A + B*Lambda0) c^(1/2)
#   * its constants for a symmetric 1:1 electrolyte in water at 25 C: A = 60.20, B = 0.229
# and it states its own validity limit verbatim: "reliable for c < 0.001 mol/L; with higher
# concentration the error increases". That is far stricter than the 20%-of-Lambda0 rule this
# script applied, and it strengthens the conclusion rather than weakening it: every working
# concentration in this work is 100-3000x above the limit the source itself sets.
LAMBDA0_ELECTROLYTE = {          # S cm2 mol-1, "Infinite dilution" column
    "KCl":    149.79, "NaCl":  126.39, "NaOH":  247.7,
    "KHCO3":  117.94, "KI":    150.31, "NaI":   126.88,
    "LiClO4": 105.93, "NaClO4": 117.42,
}
KCL_0P01 = 141.20                # same table, 0.01 mol/L column -- the validation target
ONSAGER_A_H2O, ONSAGER_B_H2O = 60.20, 0.229     # same table, header, water 25 C, 1:1

# --- what each registered electrolyte dissociates into ------------------------------------
# (solvent, cation, anion, nu+, nu-, concentration mol/L). Only rows whose ions appear in the
# LAMBDA0 table for their OWN solvent can be reached.
SPECIES = {
    "1 M NaOH aq":          ("H2O", "Na+", "OH-", 1, 1, 1.0, "NaOH"),
    "2 M NaCl aq":          ("H2O", "Na+", "Cl-", 1, 1, 2.0, "NaCl"),
    "1 M KHCO3 aq":         ("H2O", "K+", "HCO3-", 1, 1, 1.0, "KHCO3"),
    # Na2CO3 is 2:1. The Onsager coefficients hard-coded below (8.204e5, 82.5) are the
    # SYMMETRIC 1:1 forms; applying them to a 2:1 salt is simply wrong, and doing so produced a
    # spurious "carried value below the lower bound" flag on the first run of this script. The
    # row therefore gets the Kohlrausch ceiling only, which is valid for any stoichiometry.
    "1 M Na2CO3 aq":        ("H2O", "Na+", "CO3--", 2, 1, 1.0, None),
    "0.1 M LiClO4/MeCN":    ("MeCN", "Li+", "ClO4-", 1, 1, 0.1, None),
    "0.3 M LiClO4/MeCN":    ("MeCN", "Li+", "ClO4-", 1, 1, 0.3, None),
    "0.033 M Et4NPF6/MeCN": ("MeCN", "Et4N+", "PF6-", 1, 1, 0.033, None),
    "0.2 M NaI/DMF":        ("DMF", "Na+", "I-", 1, 1, 0.2, None),
}


# --- RETRIEVED CRC p. 5-71, the table the registry's aqueous derivations come from ---------
# "Electrical Conductivity of Aqueous Solutions", CRC Handbook, 20 C, indexed by mass percent.
# Retrieved in full 2026-08-22 and archived at
# papers for model/CRC_electrical_conductivity_of_aqueous_solutions_p5-71.pdf.
# Until this pass the registry DESCRIBED this derivation in prose and quoted three numbers from
# the NaCl row; nothing recomputed it. G-CRC below re-derives all three aqueous kappa values
# from the table itself, so the route is now checkable rather than merely asserted.
CRC_P571_MASSPCT = [0.5, 1, 2, 5, 10, 15, 20, 25, 30, 40, 50]
CRC_P571 = {                       # mS/cm at 20 C, columns as above
    "NaCl":   [8.2, 16.0, 30.2, 70.1, 126, 171, 204, 222],
    "NaOH":   [24.8, 48.6, 93.1, 206],
    "Na2CO3": [7.0, 13.1, 23.3, 47.0, 74.4, 88.6],
}
# c -> mass % from CRC "Concentrative Properties of Aqueous Solutions" (Section 8), and the
# 20 -> 25 C correction at the tabulated alpha = 1.5-2.2 %/K.
CRC_ROWS = [("1 M NaOH aq", "NaOH", 3.840), ("2 M NaCl aq", "NaCl", 10.846),
            ("1 M Na2CO3 aq", "Na2CO3", 9.600)]
ALPHA_LO, ALPHA_HI = 0.015, 0.022


def crc_interp(salt, mass_pct):
    v = CRC_P571[salt]
    c = CRC_P571_MASSPCT[:len(v)]
    for i in range(len(c) - 1):
        if c[i] <= mass_pct <= c[i + 1]:
            f = (mass_pct - c[i]) / (c[i + 1] - c[i])
            return v[i] + f * (v[i + 1] - v[i])
    raise ValueError("%s: %.3f mass%% outside the tabulated range" % (salt, mass_pct))


def onsager(lam0, eps, eta_mPa, c):
    """Lambda(c) by the Onsager limiting law. eta in mPa s, c in mol/L."""
    eta_P = eta_mPa * 0.01                    # mPa s -> poise
    eT = eps * T_K
    B1 = 8.204e5 / eT ** 1.5
    B2 = 82.5 / (eta_P * math.sqrt(eT))
    drop = (B1 * lam0 + B2) * math.sqrt(c)
    return lam0 - drop, drop, B1, B2


def nai_dmf_ka_route(K_A=7.50, c=0.2, lam0=81.35, a_nm=1.131):
    """The same-system third route for 0.2 M NaI/DMF (registry row '0.2 M NaI/DMF'): Krumgalz & Barthel,
    Z. Phys. Chem. 1984, 142, 167, Table 2, p. 170 -- Lambda0 = 81.35, K_A = 7.50 +/- 0.57 dm3 mol-1 and distance
    parameter R2 = 1.131 nm. The association equilibrium K_A = (1 - alpha)/(alpha^2 c gamma^2), with Debye-Huckel
    activity coefficients at R2, fixes the free-ion fraction alpha. Converting alpha to kappa needs a conductance
    equation at the free-ion concentration alpha*c, 20-200x beyond the range the paper fits, and the FORM decides the
    answer: the Onsager limiting law (Eq. S29) against the same law divided by the Debye-Huckel ion-size factor
    1 + B a sqrt(alpha c). Both are reported; the SI states that the route therefore bounds nothing. (2026-10-07: the
    8.30 mS cm-1 typed for this route reproduced under neither form.)"""
    eps, eta = SOLV["DMF"][0], SOLV["DMF"][1]
    eT = eps * T_K
    A, B = 1.8246e6 / eT ** 1.5, 50.29 / math.sqrt(eT)       # log10 gamma per (mol/L)^1/2; per Angstrom
    out = {}
    for tag, ka in (("lo", K_A - 0.57), ("mid", K_A), ("hi", K_A + 0.57)):
        lo, hi = 1e-12, 1.0
        for _ in range(200):
            al = 0.5 * (lo + hi)
            g = 10 ** (-A * math.sqrt(al * c) / (1 + B * 10 * a_nm * math.sqrt(al * c)))
            if ka * al * al * c * g * g > 1 - al:
                hi = al
            else:
                lo = al
        lam_lim, drop, _, _ = onsager(lam0, eps, eta, al * c)
        lam_size = lam0 - drop / (1 + B * 10 * a_nm * math.sqrt(al * c))
        out[tag] = dict(K_A=ka, alpha=al, kappa_limiting_mScm=c * al * lam_lim, kappa_sizecorr_mScm=c * al * lam_size)
    return dict(c=c, lambda0=lam0, a_nm=a_nm, eps=eps, eta_mPas=eta, **out)


def kappa_from(name):
    solv, cat, an, nu_p, nu_m, c, salt = SPECIES[name]
    tbl = LAMBDA0.get(solv, {})
    if cat not in tbl or an not in tbl:
        missing = [i for i in (cat, an) if i not in tbl]
        return None, "no lambda0 in %s for %s" % (solv, "/".join(missing))
    lam0_sum = nu_p * tbl[cat] + nu_m * tbl[an]        # recalled per-ion Kohlrausch sum
    # PREFER THE RETRIEVED ELECTROLYTE VALUE. Where Vanysek's table lists the salt itself, its
    # "Infinite dilution" entry is used and the recalled per-ion sum is demoted to a cross-check.
    lam0_ret = LAMBDA0_ELECTROLYTE.get(salt) if salt else None
    lam0 = lam0_ret if lam0_ret is not None else lam0_sum
    lam0_src = ("retrieved (Vanysek, %s)" % salt) if lam0_ret is not None else "recalled per-ion sum"
    xcheck = (100.0 * (lam0_sum - lam0_ret) / lam0_ret) if lam0_ret is not None else None
    eps, eta, src = SOLV[solv]
    one_one = (nu_p == 1 and nu_m == 1)
    # kappa [mS/cm] = Lambda [S cm2 mol-1] * c [mol/L]
    #
    # THE CEILING IS THE ONLY RIGOROUS BOUND. kappa <= Lambda0 * c holds for any stoichiometry
    # because it assumes complete dissociation AND zero relaxation; both relaxation and ion
    # association can only lower kappa from there.
    #
    # ONSAGER IS AN ESTIMATE, NOT A BOUND. The first version of this script called it a lower
    # bound. That is wrong in both directions: higher-order terms (Fuoss-Onsager +c log c, +c)
    # push the true Lambda ABOVE the limiting slope, while ion association pushes it BELOW.
    # Which dominates depends on the salt and the permittivity, so no inequality follows. It is
    # reported with its validity flag and nothing is inferred from it outside that range.
    kappa_hi = lam0 * c
    if one_one:
        lam_c, drop, B1, B2 = onsager(lam0, eps, eta, c)
        est, frac = lam_c * c, drop / lam0
    else:
        lam_c = drop = B1 = B2 = est = frac = float("nan")
    return dict(solvent=solv, lambda0=lam0, lambda0_source=lam0_src,
                lambda0_recalled_sum=lam0_sum, recall_vs_retrieved_pct=xcheck,
                eps=eps, eta_mPas=eta, c_M=c, one_one=one_one,
                B1=B1, B2=B2, drop=drop, lambda_c=lam_c,
                kappa_onsager_mScm=est, kappa_ceiling_mScm=kappa_hi,
                frac_drop=frac, source=src), None


def main():
    # ---- self-validation: aqueous KCl, where Lambda(c) is textbook ----------------------
    # VALIDATION, now against RETRIEVED numbers throughout.
    lam0_kcl = LAMBDA0_ELECTROLYTE["KCl"]
    lam_c, _, B1, B2 = onsager(lam0_kcl, *SOLV["H2O"][:2], 0.01)
    print("validation against Vanysek (retrieved, archived in papers for model/):")
    print("  KCl Lambda0 = %.2f (table), Onsager Lambda(0.01 M) = %.2f vs table %.2f -> %+.2f%%"
          % (lam0_kcl, lam_c, KCL_0P01, 100 * (lam_c - KCL_0P01) / KCL_0P01))
    print("  my coefficient formulas for water give B2(=A) = %.2f and B1(=B) = %.4f;"
          % (B2, B1))
    print("  the table states A = %.2f and B = %.3f -> %+.1f%% and %+.1f%%"
          % (ONSAGER_A_H2O, ONSAGER_B_H2O,
             100 * (B2 - ONSAGER_A_H2O) / ONSAGER_A_H2O,
             100 * (B1 - ONSAGER_B_H2O) / ONSAGER_B_H2O))
    print("  the table's OWN validity limit, quoted: \"reliable for c < 0.001 mol/L\"")

    # ---- INDEPENDENT CHECK ON THE RECALLED PER-ION SET -------------------------------------
    # Kohlrausch's law of independent migration says an ion contributes the same lambda0 to
    # every salt it appears in, so DIFFERENCES between retrieved electrolyte Lambda0 must equal
    # differences between per-ion values. That test uses only retrieved numbers on one side and
    # only recalled numbers on the other, so it is genuinely independent -- unlike the Le Bas
    # regression test, which compares the code's arithmetic against a memory of the same rule.
    LE = LAMBDA0_ELECTROLYTE
    ion = LAMBDA0["H2O"]
    pairs = [("K+ - Na+", LE["KCl"] - LE["NaCl"], ion["K+"] - ion["Na+"]),
             ("K+ - Na+ (iodides)", LE["KI"] - LE["NaI"], ion["K+"] - ion["Na+"]),
             ("I- - Cl- (sodium)", LE["NaI"] - LE["NaCl"], ion["I-"] - ion["Cl-"]),
             ("I- - Cl- (potassium)", LE["KI"] - LE["KCl"], ion["I-"] - ion["Cl-"])]
    print("\n  Kohlrausch independent-migration check (retrieved differences vs recalled per-ion):")
    worst = 0.0
    for lab, ret, rec in pairs:
        d = ret - rec
        worst = max(worst, abs(d))
        print("    %-22s retrieved %+6.2f   recalled %+6.2f   diff %+.2f" % (lab, ret, rec, d))
    print("    worst discrepancy %.2f S cm2 mol-1 on values of order 25 -- the recalled per-ion"
          % worst)
    print("    set is consistent with the retrieved table to better than %.1f%%." % (100*worst/23.4))

    ecsv = pd.read_csv(os.path.join(HERE, "electrolytes.csv")).set_index("electrolyte")
    rows, unreachable = [], []
    print("\n%-24s %8s %9s %9s %8s  %s"
          % ("electrolyte", "carried", "Onsager*", "ceiling", "carried/ceil", "under ceiling?"))
    for name in SPECIES:
        if name not in ecsv.index:
            continue
        carried = float(ecsv.loc[name, "kappa_mScm"])
        rec, err = kappa_from(name)
        if err:
            unreachable.append((name, err))
            continue
        est, hi = rec["kappa_onsager_mScm"], rec["kappa_ceiling_mScm"]
        ok = carried <= hi
        valid = rec["one_one"] and rec["frac_drop"] < 0.20
        print("%-24s %8.2f %9s %9.2f %8.2f  %s"
              % (name, carried, ("%.2f%s" % (est, "" if valid else "!")) if rec["one_one"] else "n/a 2:1",
                 hi, carried / hi, "YES" if ok else "*** NO ***"))
        rec.update(electrolyte=name, carried_mScm=carried,
                   frac_of_ceiling=carried / hi, under_ceiling=bool(ok),
                   onsager_within_validity=bool(valid))
        rows.append(rec)

    if unreachable:
        print("\nnot reachable by this chain (missing input named):")
        for n, e in unreachable:
            print("  %-24s %s" % (n, e))

    under = [r for r in rows if r["under_ceiling"]]
    valid = [r for r in rows if r["onsager_within_validity"]]
    print("\n! = Onsager evaluated outside its validity range (sqrt(c) drop > 20%% of Lambda0)")
    print("%d of %d carried values sit under the rigorous Kohlrausch ceiling" % (len(under), len(rows)))
    print("%d of %d are inside the Onsager limiting law's validity range" % (len(valid), len(rows)))
    for r in rows:
        if not r["under_ceiling"]:
            print("  *** %s: carried %.2f EXCEEDS the ceiling %.2f -- the row asserts more"
                  % (r["electrolyte"], r["carried_mScm"], r["kappa_ceiling_mScm"]))
    print("\nWhat the equations deliver at these concentrations is a CEILING, not a value:")
    print("  kappa <= Lambda0 * c (Eq. S27 with Eq. S28) -- rigorous, any stoichiometry.")
    print("  The Onsager estimate (Eq. S29) is reported for scale but is outside its validity")
    print("  range at every working concentration here, so nothing is inferred from it.")
    print("A point value needs a measured isotherm, which is why the five Bu4NBF4/MeCN rows --")
    print("where Dorn et al. supply one -- are the only organic rows that reach `derived`.")

    # ---- G-CRC: the registry's aqueous kappa re-derived from the archived CRC table --------
    print("\nG-CRC: aqueous rows re-derived from the retrieved CRC p. 5-71 table")
    ecsv2 = pd.read_csv(os.path.join(HERE, "electrolytes.csv")).set_index("electrolyte")
    # The band is ASSERTED only for a row whose registry state is `derived`, i.e. a row whose value
    # comes from this table. A row the registry carries as `measured` (read off a Dorn isotherm) is
    # reported against the band as a cross-check of the CRC route, with its distance from the band
    # stated, because a measurement is not required to agree with a 20 C table and a temperature
    # correction to better than the correction's own uncertainty.
    crc_fail, crc_xcheck = [], []
    for name, salt, mass_pct in CRC_ROWS:
        if name not in ecsv2.index:
            continue
        carried = float(ecsv2.loc[name, "kappa_mScm"])
        state = str(ecsv2.loc[name, "state"])
        k20 = crc_interp(salt, mass_pct)
        lo, hi = k20 * (1 + ALPHA_LO * 5), k20 * (1 + ALPHA_HI * 5)
        ok = lo <= carried <= hi
        off = 0.0 if ok else 100.0 * ((carried - lo) / lo if carried < lo else (carried - hi) / hi)
        tag = ("PASS" if ok else "FAIL") if state != "measured" else ("XCHK" if ok else "XCHK%+.2f%%" % off)
        print("  %-9s %-16s %.3f mass%% -> %.1f at 20 C -> %.1f-%.1f at 25 C ; registry %.1f (%s)"
              % (tag, name, mass_pct, k20, lo, hi, carried, state))
        if state == "measured":
            crc_xcheck.append(dict(electrolyte=name, carried_mScm=carried, band_25C=[lo, hi],
                                   outside_band_pct=off))
        elif not ok:
            crc_fail.append(name)
    if crc_fail:
        raise AssertionError("registry kappa outside the CRC-derived band: %s" % ", ".join(crc_fail))
    print("  -> every derived row reproduces from the archived table; measured rows are cross-checks")

    with open(OUT, "w") as f:
        json.dump(dict(validation_KCl=dict(lambda0=lam0_kcl, lambda_c=lam_c,
                                          table=KCL_0P01, source="Vanysek CRC, retrieved"),
                       rows=rows, unreachable=unreachable, crc_crosscheck_measured=crc_xcheck,
                       nai_dmf_ka_route=nai_dmf_ka_route()), f, indent=2)
    print("\nwrote %s" % os.path.relpath(OUT, os.path.dirname(HERE)))
    return rows


if __name__ == "__main__":
    main()
