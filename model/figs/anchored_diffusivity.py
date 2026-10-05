"""Surrogate-anchored diffusivities: correct a MEASURED D onto a structurally similar species.

    cd Section4_Model && python figs/anchored_diffusivity.py

THE IDEA, AND WHY IT BEATS PREDICTING ABSOLUTELY
------------------------------------------------
Wilke-Chang and Stokes-Einstein predict D from scratch. Their weakness is the PREFACTOR: on the
one system in this work where a measurement exists, Wilke-Chang lands 24% low on ferrocene in
MeCN (1.82e-5 predicted against 2.4e-5 measured). That error is systematic in the prefactor,
not in the shape of the size dependence.

Taking a RATIO to a measured reference cancels the prefactor exactly. Writing Wilke-Chang for
two solutes A and ref in the same solvent at the same temperature,

    D = 7.4e-8 (phi M_solv)^(1/2) T / (mu V^0.6)

everything except V is common, so

    D_A = D_ref (V_ref / V_A)^0.6                                              (Eq. S32)

and the correlation's constant, the association factor, the solvent molar mass, T and mu all
drop out. The only thing assumed is that the V^-0.6 SHAPE holds between two similar solutes --
a far weaker assumption than trusting the absolute prefactor.

The same construction on Stokes-Einstein, D = kB T / (6 pi mu r), allows a solvent change too,
because mu is the only solvent property that appears:

    D_A(s) = D_ref(s_ref) * (mu_ref / mu_s) * (r_ref / r_A)                    (Eq. S33)

and where no molar volume is available -- which is the case for every coordination complex here,
since Le Bas has no transition-metal increment -- the radius ratio is taken structurally from
the molar masses, r ~ M^(1/3), i.e. assuming comparable partial molar density between reference
and target. Ferrocene is 1.49 g cm-3 and bipyridyl/salen complexes are 1.4-1.5, so that holds
to a few per cent for this family.

WHAT THIS IS USED FOR HERE, AND WHAT IT IS NOT
----------------------------------------------
It is NOT used to overwrite the eleven catalyst rows. Two estimates of those diffusivities exist
and they bracket the answer rather than agreeing:

  * the TYPED hydrodynamic radius, r = 4.0-5.0 A, which gives the LOWER D;
  * this anchored construction, which gives D 1.14-1.56x higher.

Neither is obviously right. The typed radius is unsourced. The anchored value inherits ferrocene's
neutrality: these complexes are charged and more strongly solvated, which raises the effective
radius and pushes their true D back DOWN toward the typed value. The honest statement is that the
truth lies between, and the useful statement is that the conclusion does not care -- which is what
this script tests and what G-CATD now gates across the whole bracket.

Where this construction IS the right tool is filling a gap: if a measured D exists for a
structurally similar species in any solvent, Eq. S33 transfers it with one stated assumption
instead of trusting a correlation's absolute prefactor.
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
THRESH = 25.0
OUT = os.path.join(ROOT, "results", "anchored_diffusivity.json")

# IUPAC 2021 standard atomic weights; molar masses are COMPUTED from formula, never typed.
AW = {"C": 12.011, "H": 1.008, "N": 14.007, "O": 15.999, "S": 32.06, "P": 30.974,
      "Cl": 35.45, "Br": 79.904, "Fe": 55.845, "Ni": 58.693, "Co": 58.933,
      "Cu": 63.546, "Mn": 54.938, "Rh": 102.906}


def mw(formula):
    return sum(AW[e] * n for e, n in formula.items())


# --- the measured anchor -------------------------------------------------------------------
# Ferrocene in MeCN. D is the value build_reactions50.py already validates Wilke-Chang against,
# and it is a textbook RANGE (1.7-2.4e-5) read at its upper end, not a page-anchored point
# measurement -- see docs/ADVERSARIAL_REVIEW_20260822.md R3. Every number this script produces
# scales linearly with it, so that limitation propagates directly and is stated wherever the
# output is used.
ANCHOR = dict(name="ferrocene", formula={"C": 10, "H": 10, "Fe": 1},
              # mu: CRC 97th ed. p. 6-243, eta(25 C) column -- the value solvents.csv carries.
              # Was 0.343 until 2026-08-30; every anchored D scales LINEARLY with this number.
              solvent="MeCN", mu_mPas=0.369, D_cm2s=2.4e-5)

# Parent complex as written in the Table S2 carrier column, by molecular formula.
COMPLEX_FORMULA = {
    "Ni-catalyzed aryl amination (ArBr + amine)":      {"C": 10, "H": 8, "N": 2, "Br": 2, "Ni": 1},
    "Electrochemical amination of ArX with NH3":       {"C": 10, "H": 8, "N": 2, "Br": 2, "Ni": 1},
    "Mn-catalyzed alkene diazidation":                 {"C": 18, "H": 12, "N": 2, "O": 2, "Mn": 1},
    "Co-catalyzed aza-Wacker cyclization":             {"C": 16, "H": 14, "Co": 1, "N": 2, "O": 2},
    "Co-H alkene reduction (e-HAT)":         {"C": 10, "H": 8, "N": 2, "Br": 2, "Co": 1},
    "Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)":               {"C": 18, "H": 24, "Br": 2, "N": 2, "Ni": 1},
    "Rh-catalyzed electrooxidative C-H alkenylation":  {"C": 20, "H": 30, "Cl": 4, "Rh": 2},
    "Cu-catalyzed benzylic cyanation":                 {"C": 10, "H": 14, "O": 4, "Cu": 1},
    "Cathodic Ni aryl-aryl homocoupling":              {"C": 10, "H": 8, "N": 2, "Br": 2, "Ni": 1},
    "Co-H alkene isomerization (catalytic)":           {"C": 16, "H": 14, "Co": 1, "N": 2, "O": 2},
    "Cathodic aryl-halide radical 5-exo cyclization":  {"C": 16, "H": 36, "N": 4, "Ni": 1},
}


def anchored_D(formula, mu_target_mPas, anchor=ANCHOR):
    """Eq. S33: transfer a measured D onto a similar solute, with a solvent change."""
    m_ref, m_a = mw(anchor["formula"]), mw(formula)
    return anchor["D_cm2s"] * (anchor["mu_mPas"] / mu_target_mPas) * (m_ref / m_a) ** (1 / 3.), m_a


def main():
    rx = pd.read_csv(os.path.join(ROOT, "data", "reactions_50.csv"))
    sol = pd.read_csv(os.path.join(ROOT, "data", "solvents.csv")).set_index("solvent")
    t0 = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))

    se = rx[rx.D_provenance.str.startswith("Stokes-Einstein")]
    print("anchor: %s in %s, measured D = %.2e cm2/s, M = %.2f"
          % (ANCHOR["name"], ANCHOR["solvent"], ANCHOR["D_cm2s"], mw(ANCHOR["formula"])))
    print("\n%-44s %-9s %9s %10s %7s" % ("carrier row", "solvent", "D typed", "D anchored", "ratio"))
    rows = []
    for _, r in se.iterrows():
        f = COMPLEX_FORMULA[r.reaction]
        mu = float(sol.loc[r.solvent, "mu_mPas"])
        D_a, M_a = anchored_D(f, mu)
        ratio = D_a / r.D_cm2s
        print("%-44s %-9s %.3e %.3e %6.2fx" % (r.reaction[:44], r.solvent, r.D_cm2s, D_a, ratio))
        rows.append(dict(reaction=r.reaction, solvent=r.solvent, M=M_a,
                         D_typed=float(r.D_cm2s), D_anchored=D_a, ratio=ratio))

    lo, hi = min(x["ratio"] for x in rows), max(x["ratio"] for x in rows)
    print("\nthe two estimates bracket a factor of %.2f-%.2fx; the anchored value is the HIGHER"
          % (lo, hi))
    print("(ferrocene is neutral, these complexes are charged and more solvated, which raises")
    print(" their effective radius and pushes the true D back down toward the typed value)")

    # ---- does the published conclusion survive the TOP of the bracket? -------------------
    m = t0.merge(rx[["reaction", "carrier_type"]], on="reaction")
    cat = m[m.carrier_type == "catalyst"].copy()
    rmap = {x["reaction"]: x["ratio"] for x in rows}
    best_typed = cat[ARCH].max(axis=1).values
    best_anch = [b * rmap[n] for b, n in zip(best_typed, cat.reaction)]
    n_typed = int((best_typed >= THRESH).sum())
    n_anch = sum(1 for x in best_anch if x >= THRESH)
    second = sorted(best_anch)[-2]
    print("\ncatalyst rows clearing %.0f mA cm-2:  typed %d/11   anchored %d/11"
          % (THRESH, n_typed, n_anch))
    print("second-best at the TOP of the bracket: %.1f mA cm-2" % second)

    report = dict(anchor=ANCHOR["name"], anchor_D=ANCHOR["D_cm2s"], rows=rows,
                  bracket=[lo, hi], n_clear_typed=n_typed, n_clear_anchored=n_anch,
                  second_best_anchored=second)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(report, f, indent=2)
    print("wrote %s" % os.path.relpath(OUT, ROOT))

    fails = []
    if n_anch != n_typed:
        fails.append("the 10/11 catalyst result is NOT bracket-proof: typed %d/11 vs anchored "
                     "%d/11. The SI states it unconditionally and would have to be qualified."
                     % (n_typed, n_anch))
    print("\nG-ANCHOR: %s" % ("PASS" if not fails else "FAIL"))
    for x in fails:
        print("  " + x)
    if fails:
        raise AssertionError("; ".join(fails))
    print("  the catalyst conclusion holds at BOTH ends of the bracket -- it does not depend on")
    print("  which of the two diffusivity estimates is adopted (%.1f mA cm-2 headroom at the top)"
          % (THRESH - second))
    return report


if __name__ == "__main__":
    main()
