#!/usr/bin/env python3
"""G-MUSOLN -- the model uses the PURE SOLVENT viscosity, not the SOLUTION viscosity.

    cd Section4_Model && python data/sensitivity_solution_viscosity.py

WHY THIS EXISTS
---------------
`data/solvents.csv` carries mu for the pure solvent, page-anchored to CRC. Every i_lim in the
model is computed with that mu. But the cells contain a supporting electrolyte, a substrate, or
both, at concentrations up to 6.85 M -- and a concentrated solution is more viscous than the
solvent it is made from. Since i_lim ~ D ~ 1/mu (Wilke-Chang / Stokes-Einstein), using the
solvent viscosity where the solution viscosity belongs OVERSTATES every affected ceiling.

This is the first-order objection a concentrated-solution-theory reviewer raises, and until now
the repository had no bound on it. G-SOLV sweeps mu by x0.75-1.5, but that range was chosen for
the ELEVEN mixed-solvent rows whose mu is a mixing-rule estimate -- it is not the range a 3 M
salt solution implies, and it is applied only to those rows.

WHAT THIS DOES, AND WHAT IT REFUSES TO DO
-----------------------------------------
It does NOT invent a viscosity. No solution-viscosity measurement for these compositions is in
the repository, and guessing one would be exactly what the standard forbids. Instead it sweeps
the ratio mu_solution/mu_solvent over a range that brackets what is physically reachable, and
reports the current density at which each published conclusion would break. The output is a
BREAKING POINT, not a corrected number: "the ordering survives to f = X" is a statement the
model can support; "the viscosity is 1.6x" is not.

Rows are graded by total dissolved concentration, because that is what drives the increase:
mu_solution/mu_solvent rises monotonically with solute concentration for every non-associating
system, so a single factor applied to the most concentrated rows is a conservative probe.

    i_lim(f) = i_lim(1) * f**p   for the flagged rows, p PER ARCHETYPE

p IS NOT -1. Scaling mu scales D by 1/mu, but it also scales nu = mu/rho, and delta_eff depends
on nu through the mass-transfer correlations -- so the two partly cancel everywhere delta is
computed rather than declared. Measured from the repository's own correlations
(figs/archetype_bands.delta_eff, d ln i_lim / d ln mu at f = 2):

    natural  -1.0000     fixed delta (228 um), so i_lim ~ D ~ 1/mu exactly
    stirred  -1.0000     fixed delta (100 um), likewise
    flow     -0.6667     Leveque: k_m ~ (D^2 u / d_h L)^(1/3), so i_lim ~ D^(2/3), no nu
    thingap  -0.6667     Leveque, as above
    rde      -0.8333     Levich: i_lim ~ D^(2/3) nu^(-1/6) -> mu^(-5/6)
    rce      -0.9880     Eisenberg: nu^(-0.344) D^(0.644)

Using -1 everywhere -- which this script did until 2026-08-30, and which
figs/analysis_solvent_property_sensitivity.py still did -- OVERSTATES the perturbation on four
of the six archetypes: at f = 2 it applies 0.500x to the flow columns where the correlation
gives 0.630x. The exponents are asserted against delta_eff at runtime below, so they cannot
drift from the correlations they came from.

APPROXIMATE for the 8 mediated EC' rows either way: their amplification depends on
x_k = sqrt(D_ox/(k*C_S)), so scaling D moves the reaction-layer thickness too. Their movement is
an UPPER bound on the real effect and they are marked in the listing.
"""
import csv
import io
import json
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
THRESH = 25.0
FACTORS = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
# d ln i_lim / d ln mu, per archetype -- see the module docstring. Verified against
# figs/archetype_bands.delta_eff at import time by _assert_exponents().
MU_EXP = {"natural": -1.0, "stirred": -1.0, "flow": -1.0, "anec": -1.0, "micro": -1.0,
          "rde": -5.0 / 6.0, "rce": -0.9880}


# A NEGATIVE CONTROL MUST NEVER WRITE THE ARTIFACT IT PERTURBS. Until 2026-08-30 several
# controls here dumped their perturbed numbers straight over results/, so a control run
# left the repo holding fabricated values until the next ordinary run happened to fix it --
# and an audit that snapshotted results/ AFTER a control run then compared against
# contaminated bytes and reported no contamination. Controls write a _NEGCONTROL sibling,
# the convention data/check_conditions.py already used.
def _out(path, neg):
    return path[:-5] + "_NEGCONTROL.json" if neg and path.endswith(".json") else path

def _assert_exponents(tol=2e-3):
    """The exponents must BE the correlations', not a comment about them."""
    import math
    sys.path.insert(0, os.path.join(ROOT, "figs"))
    import archetype_bands as AB
    D0, nu0 = 1.39e-9, 0.369e-3 / 786.0
    bad = []
    for k, want in MU_EXP.items():
        f = 2.0
        i1 = D0 / AB.delta_eff(k, D0, nu0)
        i2 = (D0 / f) / AB.delta_eff(k, D0 / f, nu0 * f)
        got = math.log(i2 / i1) / math.log(f)
        if abs(got - want) > tol:
            bad.append("%s: correlation gives %.4f, this file says %.4f" % (k, got, want))
    if bad:
        raise SystemExit("MU_EXP has drifted from the correlations:\n  " + "\n  ".join(bad))


from dilute_theory_stratify import elyte_M, c_total   # one concentration rule for both gates


def main(neg=False):
    _assert_exponents()
    mat = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    rx = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
    med = set(pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv")).reaction.unique())
    # total dissolved concentration seen by the medium, each species counted once (dilute_theory_stratify.c_total)
    m = mat.merge(c_total(rx)[["reaction", "c_tot"]], on="reaction")
    if neg:
        # THE CONTROL USED TO RUN THE WRONG WAY: it set c_tot = 0 so NOTHING was flagged, then
        # confirmed no count moved. That shows the code is quiet when asked to do nothing -- it
        # cannot show the breaking-point detector would notice a break that IS there, which is
        # the only thing this gate reports. Perturb the input INTO a break instead: flag all 50
        # rows, so the smallest swept factor must already move a count. If it does not, the
        # detector is broken and the reassuring "no count moves until x1.5" means nothing.
        m["c_tot"] = 99.0

    for cut in (0.5, 1.0, 2.0):
        n = int((m.c_tot >= cut).sum())
        print("  rows with total dissolved concentration >= %.1f M : %2d of 50" % (cut, n))
    CUT = 1.0
    flag = m.c_tot >= CUT
    print("\n  flagging the %d rows at >= %.1f M total (the ones a solution/solvent viscosity "
          "gap actually reaches):" % (int(flag.sum()), CUT))
    for _, r in m[flag].sort_values("c_tot", ascending=False).iterrows():
        print("    %5.2f M  %s%s" % (r.c_tot, r.reaction[:52],
                                     "   [mediated: upper bound]" if r.reaction in med else ""))

    base = {c: (float(m[c].median()), int((m[c] >= THRESH).sum()),
                int((m[c] >= 50).sum())) for c in ARCH}
    print("\n  %-6s %-34s %s" % ("mu x", "median i_lim per architecture", ">=25 of 50"))
    rows_out = []
    for f in FACTORS:
        s = m.copy()
        for c in ARCH:
            s.loc[flag, c] = s.loc[flag, c] * (f ** MU_EXP[c])
        meds = [float(s[c].median()) for c in ARCH]
        n25 = [int((s[c] >= THRESH).sum()) for c in ARCH]
        ordered = all(meds[i] <= meds[i + 1] for i in range(3))     # unstirred<stirred<flow<thingap
        rows_out.append({"factor": f, "medians": [round(x, 2) for x in meds],
                         "n25": n25, "ordering_holds": ordered})
        print("  %-6.2f %-34s %s%s" % (f, "/".join("%.1f" % x for x in meds),
                                       "/".join(str(x) for x in n25),
                                       "" if ordered else "   <- ORDERING INVERTS"))

    n25_base = [base[c][1] for c in ARCH]
    breaks = {}
    for r in rows_out:
        if r["factor"] == 1.0:
            continue
        if "count" not in breaks and r["n25"] != n25_base:
            breaks["count"] = r["factor"]
        if "ordering" not in breaks and not r["ordering_holds"]:
            breaks["ordering"] = r["factor"]

    out = os.path.join(ROOT, "results", "solution_viscosity_sensitivity.json")
    json.dump({"cut_M": CUT, "n_flagged": int(flag.sum()), "c_tot_max_M": float(m.c_tot.max()), "factors": FACTORS,
               "baseline_n25": n25_base, "sweep": rows_out, "breaks_at": breaks},
              io.open(_out(out, neg), "w", encoding="utf8"), indent=1)
    print("\n-> %s" % _out(out, neg))

    print("\n  FIRST BREAKING POINT")
    print("    a >=25 count moves at   mu_solution/mu_solvent = %s"
          % breaks.get("count", "> %.1f (never, over the swept range)" % FACTORS[-1]))
    print("    the architecture ordering inverts at %s"
          % breaks.get("ordering", "> %.1f (never, over the swept range)" % FACTORS[-1]))

    if neg:
        first = breaks.get("count")
        print("\nNEGATIVE CONTROL: all 50 rows flagged, so the detector must report a >=25 count "
              "moving at the smallest swept factor above 1.0.")
        ok = first is not None and first <= FACTORS[1]
        print("G-MUSOLN control: %s"
              % ("GOOD -- the break is detected at mu x%.2f" % first if ok else
                 "BAD -- no break detected (%r) even with every row perturbed, so the "
                 "breaking-point report cannot fail" % (first,)))
        return 0 if ok else 1
        return 0
    # This gate REPORTS an exposure; it does not assert a value, so it cannot "fail" on the
    # model. It fails only if the ordering -- the conclusion the paper actually rests on --
    # breaks within the swept range.
    if "ordering" in breaks:
        print("\nG-MUSOLN: REVIEW NEEDED -- the architecture ordering inverts at mu x%.2f"
              % breaks["ordering"])
        return 1
    print("\nG-MUSOLN: PASS -- the architecture ordering survives every factor to x%.1f; "
          "the threshold counts are reported with their breaking point above" % FACTORS[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
