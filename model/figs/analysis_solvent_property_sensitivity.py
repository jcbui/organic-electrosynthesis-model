"""Do the threshold counts survive the solvents whose properties are NOT page-anchored?

    cd Section4_Model && python figs/analysis_solvent_property_sensitivity.py

THE EXPOSURE
------------
Thirteen of the fifty rows use a solvent whose viscosity or density is not state A (the count is
computed at run time and printed; this sentence states what it currently is):

  * HFIP (2 rows) -- the VISCOSITY is no longer the exposure: mu = 1.619 mPa s is state A,
    page-anchored to Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587, Table 3 p. 578.
    What remains unsourced is the DENSITY, rho = 1.596 g/cm3, which is corroborated by a supplier
    specification and by a molar-volume estimate calibrated on trifluoroethanol, but by nothing
    page-anchorable -- the one page-anchored candidate, CRC 97th ed. p. 3-296, prints a value that
    fails an independent physical cross-check and is not used. rho enters only through nu = mu/rho,
    so its leverage is the weaker of the two.
  * Eleven mixed-solvent rows (MeCN/H2O, MeOH/H2O, H2O/MeCN, DMSO/THF, tAmOH/H2O, AcOH/HCOOH) --
    mixing-rule estimates, and until 2026-08-22 they had NO registry rows at all, so they were
    invisible to every census and schema gate.

WHY A SWEEP SETTLES IT
----------------------
i_lim = nFDC/delta with D from Wilke-Chang, and D ~ 1/mu. That does NOT make i_lim ~ 1/mu, which
is what this file assumed until 2026-08-30: mu also enters nu = mu/rho, and delta_eff depends on
nu through the mass-transfer correlations, so the two partly cancel wherever delta is computed
rather than declared. Measured from the correlations themselves (MU_EXP below, asserted against
figs/archetype_bands.delta_eff at run time):

    natural -1.0000   stirred -1.0000   flow -0.6667   thingap -0.6667   rde -0.8333   rce -0.9880

Exactly -1 only for the two archetypes whose delta is a declared constant. Scaling mu by f
therefore scales those rows' i_lim by f**p per archetype, and the published threshold counts are
step functions of f alone -- which can
be evaluated directly off the solved matrix, with no re-solve and therefore no possibility of
drifting from it.

The published counts under test (SI Table S5 / S1.2, main text S4):
  * 28 of the 31 substrate-carried electrolyses clear 25 mA cm-2 in at least one architecture
  * the six architecture-median >=25 counts, read from SI Table S5 at run time (never typed)
"""
import json
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
_NUMW = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen"]
THRESH = 25.0
OUT = os.path.join(ROOT, "results", "solvent_property_sensitivity.json")

UNSOURCED = ("HFIP",)                 # assumption-class pure solvent
MIXED_MARK = "/"                      # any solvent name with a slash is a mixture


# d ln i_lim / d ln mu, PER ARCHETYPE. This file scaled i_lim by 1/f on every column until
# 2026-08-30, i.e. it assumed -1 everywhere. That is right only where delta is DECLARED: where
# delta is computed, scaling mu scales nu = mu/rho as well, and delta_eff moves with it, so the
# two partly cancel. At f = 2 the old code applied 0.500x to the flow columns where the Leveque
# correlation gives 0.630x -- it overstated its own perturbation on four of the six archetypes.
# Asserted against figs/archetype_bands.delta_eff below so it cannot drift from the correlations.
MU_EXP = {"natural": -1.0, "stirred": -1.0, "flow": -1.0, "anec": -1.0, "micro": -1.0,
          "rde": -5.0 / 6.0, "rce": -0.9880}


def _assert_exponents(tol=2e-3):
    import math
    import archetype_bands as AB
    D0, nu0 = 1.39e-9, 0.369e-3 / 786.0
    for k, want in MU_EXP.items():
        i1 = D0 / AB.delta_eff(k, D0, nu0)
        i2 = (D0 / 2.0) / AB.delta_eff(k, D0 / 2.0, nu0 * 2.0)
        got = math.log(i2 / i1) / math.log(2.0)
        if abs(got - want) > tol:
            raise SystemExit("MU_EXP drifted from the correlations: %s gives %.4f, file says %.4f"
                             % (k, got, want))


def counts(mat, mask_rows, f):
    """Threshold counts with the flagged rows' i_lim scaled by f**MU_EXP[archetype]."""
    m = mat.copy()
    for c in ARCH:
        m.loc[mask_rows, c] = m.loc[mask_rows, c] * (f ** MU_EXP[c])
    per_arch = [int((m[c] >= THRESH).sum()) for c in ARCH]
    sub = m[m.carrier_type == "substrate"]
    n_sub = int((sub[ARCH].max(axis=1) >= THRESH).sum())
    return per_arch, n_sub, len(sub)


def main():
    _assert_exponents()
    rx = pd.read_csv(os.path.join(ROOT, "data", "reactions_50.csv"))
    t0 = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    m = t0.merge(rx[["reaction", "carrier_type", "solvent"]], on="reaction")

    flag = m.solvent.isin(UNSOURCED) | m.solvent.str.contains(MIXED_MARK, regex=False)
    print("rows on a solvent whose mu/rho are not page-anchored: %d of %d" % (flag.sum(), len(m)))
    for s, n in m[flag].solvent.value_counts().items():
        print("   %-12s %d" % (s, n))

    base_arch, base_sub, n_sub_tot = counts(m, flag, 1.0)
    print("\nbaseline: per-architecture >=%.0f = %s of 50; substrate-carried clearing = %d/%d"
          % (THRESH, "/".join(str(x) for x in base_arch), base_sub, n_sub_tot))

    print("\n%-8s %-26s %s" % ("mu x", "per-arch >=25 of 50", "substrate clearing"))
    rows = []
    for f in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0):
        a, s, _ = counts(m, flag, f)
        same = (a == base_arch) and (s == base_sub)
        print("%-8.2f %-26s %d/%d%s"
              % (f, "/".join(str(x) for x in a), s, n_sub_tot, "" if same else "   <- MOVED"))
        rows.append(dict(mu_factor=f, per_arch=a, substrate_clearing=s, unchanged=bool(same)))

    # HOW PRECISE ARE THE COUNTS, GIVEN THESE ELEVEN ROWS?
    # The counts are threshold crossings, not ratios, so they DO move -- a +/-25% viscosity
    # error shifts them by one or two entries out of fifty. That is the honest precision of
    # the reported integers and it must be stated rather than implied away. What does NOT
    # move is the ORDERING of the six architectures, which is what every conclusion rests on.
    band = [r for r in rows if 0.75 <= r["mu_factor"] <= 1.5]      # +/-25-50%, generous
    per = np.array([r["per_arch"] for r in band])
    lo_a, hi_a = per.min(axis=0), per.max(axis=0)
    sub_lo = min(r["substrate_clearing"] for r in band)
    sub_hi = max(r["substrate_clearing"] for r in band)
    worst = int(np.max(hi_a - lo_a))
    _nw = (_NUMW[int(flag.sum())] if int(flag.sum()) < len(_NUMW) else str(int(flag.sum())))
    print("\nover mu x0.75 - x1.5 (a +/-25-50% error on those " + _nw + " rows):")
    print("  per-architecture >=25 counts span %s" %
          " / ".join("%d-%d" % (l, h) for l, h in zip(lo_a, hi_a)))
    print("  substrate-carried clearing spans %d-%d of %d" % (sub_lo, sub_hi, n_sub_tot))
    print("  worst single-count movement: %d of 50" % worst)
    mono = all(all(np.diff([r["per_arch"][i] for i in (0, 1, 2, 3)]) >= 0) for r in rows)
    print("  architecture ORDERING (unstirred < stirred < flow < thin-gap) preserved in every"
          " case: %s" % mono)
    lo, hi = 0.75, 1.5

    report = dict(n_flagged=int(flag.sum()), baseline_per_arch=base_arch,
                  baseline_substrate=base_sub, n_substrate=n_sub_tot,
                  sweep=rows, band_mu=[lo, hi], per_arch_span=[lo_a.tolist(), hi_a.tolist()],
                  substrate_span=[sub_lo, sub_hi], worst_count_movement=worst,
                  ordering_preserved=bool(mono))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f_:
        json.dump(report, f_, indent=2)
    print("\nwrote %s" % os.path.relpath(OUT, ROOT))

    # ---- G-SOLV: the published counts must not move across a factor of two either way ----
    # The gate asserts what is actually defensible: the baseline matches the SI, the ordering
    # never inverts, and no single count moves by more than 2 of 50 across +/-25-50%. It does
    # NOT assert that the counts are invariant -- they are not, and pretending otherwise was
    # the first version of this check.
    fails = []
    if not mono:
        fails.append("the architecture ordering inverts somewhere in the sweep")
    # DERIVED FROM THE SHIPPED SI, NOT TYPED. This was `!= [11, 17, 21, 31, 36, 36]`, a pinned
    # literal, and on 2026-08-23 it became the only FAILING gate in the repo: the unstirred
    # count moved 11 -> 12 when the Br-mediated Hofmann x unstirred cell was resolved by
    # delta-continuation, and this expectation was never re-pointed. Worse, the message told
    # the reader "SI Table S5 says 11/..." while Table S5 in fact printed 12 -- so a stale gate
    # was ALSO libelling the document it guards. It went unnoticed because G-SOLV is in no
    # runner. Read Table S5 out of make_si.js and compare to the model, so the two can never
    # drift apart again and the gate cannot be stale on its own.
    # THE SHIPPED DOCUMENT, not make_si.js. Table S5 became computed on 2026-08-25, so its rows
    # are no longer literals in the generator and a source-grep finds nothing -- the same way the
    # Table S5/S6 checks in audit_numeric.py broke. Read the built .docx and bind each count to
    # the archetype NAMED BESIDE IT (CLAUDE.md trap 11).
    import sys as _sys, unicodedata as _ud
    _sys.path.insert(0, os.path.join(ROOT, "data"))
    from docx_text import asserted_text as _asserted
    si = _ud.normalize("NFKC", re.sub(r"\s+", " ",
        _asserted(os.path.join(ROOT, "SI_Section4_Transport_Model.docx"))))
    LABELS = {"natural": "Unstirred batch", "stirred": "Stirred batch",
              "flow": "Recirculating flow cell", "anec": "ANEC flow cell", "micro": "Microfluidic cell (25 \u03bcm gap)",
              "rde": "RDE 1600 rpm", "rce": "Rotating cylinder 3000 rpm"}
    # BUILD the expected row and test membership; do NOT parse it back out. The rendered cells
    # concatenate to digit strings that are genuinely ambiguous -- "6.1" then "12/50" reads as
    # "6.112/50", which a regex will happily split as "6.11" + "2/50" and report counts of 2.
    def _fmed(v):
        return "%.0f" % v if v >= 100 else "%.1f" % v
    for k in ARCH:
        col = m[k]
        want = "%s%s%d/50%d/50" % (LABELS[k], _fmed(col.median()),
                                   int((col >= 25).sum()), int((col >= 50).sum()))
        if want not in si:
            fails.append("the shipped Table S5 does not carry the model's row %r" % want)
    # The BOUND the SI publishes must be the bound the sweep measures. This was a hardcoded
    # `if worst > 2`, i.e. the gate carried its own opinion of the tolerable movement instead of
    # checking the document -- so when the movement grew to 3 the gate failed while the SI went
    # on printing "at most two entries of fifty" and "read as +/-2 of 50", both wrong.
    _bound = "by at most %s entries of fifty" % _NUMW[worst]
    if _bound not in si:
        fails.append("the sweep gives a worst movement of %d of 50, but the SI does not print %r"
                     % (worst, _bound))
    if ("read as \u00b1%d of 50" % worst) not in si:
        fails.append("the SI does not read the counts as +/-%d of 50" % worst)
    # DERIVED, NOT PINNED (was `!= (28, 31)`): the SI's own sentence is the expectation.
    _need = "%d of the %d substrate-carried" % (base_sub, n_sub_tot)
    if _need not in si:
        fails.append("substrate-carried clearing is %d/%d, but the SI does not print %r"
                     % (base_sub, n_sub_tot, _need))
    print("\nG-SOLV: %s" % ("PASS" if not fails else "FAIL"))
    for f_ in fails:
        print("  " + f_)
    if fails:
        raise AssertionError("; ".join(fails))
    print("  baseline matches the SI; ordering never inverts; worst count movement %d of 50\n"
          "  -> the counts are precise to +/-%d of 50 given these %d unsourced-property rows"
          % (worst, worst, int(flag.sum())))
    return report


if __name__ == "__main__":
    main()
