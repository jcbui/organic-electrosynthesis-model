"""Casteel-Amis, implemented once and validated against the source paper's own kappa_calc column.

    cd Section4_Model && python data/casteel_amis.py

WHY THIS FILE EXISTS
--------------------
Five registry rows were state B, "derived by Casteel-Amis from Dorn's Table 3". State B requires
that a reader can redo the arithmetic from the registry alone -- and there was NO IMPLEMENTATION
ANYWHERE IN THE REPOSITORY. The values were typed literals, computed once by hand, with nothing
able to catch them drifting or being wrong in the first place.

They were wrong. Casteel-Amis appears in the literature in forms that differ by the sign of the
b term, and the literals were produced with the wrong one. The test is not an argument, it is
Dorn's own kappa_calc column, printed beside every measured point in the Supporting Information:

    kappa = kappa_max (m/m_max)^a exp[ -b (m - m_max)^2 - a (m/m_max - 1) ]

reproduces it, and the opposite sign does not. Gate G-CA below checks all 21 points of both
acetonitrile isotherms and both aqueous ones against the paper.

WHERE THE FIT IS USED AND WHERE IT IS NOT
-----------------------------------------
The Supporting Information carries the RAW MEASURED POINTS, so for most concentrations this
project needs, the fit is unnecessary: the value is read between two measurements. The fit is used
only where the measured bracket is too wide for linear interpolation to be honest -- concretely,
0.043 M Bu4NBF4/MeCN sits at m = 0.056 between measurements at m = 0 and m = 0.0905, and kappa(m)
is strongly curved there, so interpolating linearly would understate it by about 15 per cent.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ISO = os.path.join(HERE, "dorn_isotherms.csv")

# Dorn Table SI 2, verbatim: (m_max, kappa_max, a, b)
FITS = {
    "Bu4NBF4/MeCN": (1.48127, 33.40, 0.78646, -0.02156),
    "Et4NBF4/MeCN": (4.00409, 60.97, 0.84952, -0.02650),
    "NaOH/H2O":     (4.55648, 403.97, 1.19618, -0.00547),
    "NaCl/H2O":     (6.69673, 251.64, 0.92381, 0.00375),
    "KHCO3/H2O":    (6.20820, 190.27, 0.92552, 0.00078),
    "Na2CO3/H2O":   None,
    # PUBLISHED SIGN TYPO, documented rather than silently patched. Dorn prints b = +0.00153 for
    # this system in both Table SI 2 and Table SI 97, but their own kappa_calc column is
    # reproduced only by b = -0.00153: at m = 0.1429 the table says 7.25, the printed sign gives
    # 6.75 (-6.9 pct) and the opposite gives 7.246. Every other system here is reproduced by the
    # printed sign to better than 0.1 pct, so this is one row's typo, not a different convention.
    # It is EXCLUDED from the gate rather than corrected, because nothing in this project uses it:
    # the registry's sodium-iodide row is 0.2 M NaI in DMF, and Dorn measured no DMF at all.
    "NaI/MeOH":     None,
    "KSCN/MeOH":    (4.62780, 68.90, 0.85355, 0.00351),
}


def kappa(m, m_max, k_max, a, b):
    """Casteel & Amis, J. Chem. Eng. Data 1972, 17, 55, in Dorn's sign convention."""
    m = np.asarray(m, dtype=float)
    return k_max * (m / m_max) ** a * np.exp(-b * (m - m_max) ** 2 - a * (m / m_max - 1.0))


def main():
    d = pd.read_csv(ISO)
    print("G-CA: implementation vs the kappa_calc column Dorn prints beside every measured point")
    fails, worst = [], 0.0
    for sysname, fit in FITS.items():
        if fit is None:
            continue
        g = d[d.system == sysname]
        if g.empty:
            continue
        pred = kappa(g.m_mol_kg.values, *fit)
        ref = g.kappa_calc.values
        ok = ref > 0.05                      # the m = 0 row is 0.00 by construction
        dev = np.abs(pred[ok] - ref[ok]) / ref[ok] * 100
        worst = max(worst, dev.max())
        flag = "ok  " if dev.max() < 1.0 else "FAIL"
        if dev.max() >= 1.0:
            fails.append("%s: worst %.2f%%" % (sysname, dev.max()))
        print("  [%s] %-14s %2d points, worst deviation %.3f%%" % (flag, sysname, ok.sum(), dev.max()))
    # the wrong sign must NOT reproduce the paper -- otherwise this gate proves nothing
    g = d[d.system == "Bu4NBF4/MeCN"]
    mm, kk, aa, bb = FITS["Bu4NBF4/MeCN"]
    wrong = kk * (g.m_mol_kg.values / mm) ** aa * np.exp(
        +bb * (g.m_mol_kg.values - mm) ** 2 - aa * (g.m_mol_kg.values / mm - 1.0))
    ok = g.kappa_calc.values > 0.05
    wdev = np.abs(wrong[ok] - g.kappa_calc.values[ok]) / g.kappa_calc.values[ok] * 100
    print("\n  control: the OPPOSITE sign deviates by up to %.1f%% on the same points" % wdev.max())
    if wdev.max() < 2.0:
        fails.append("the two sign conventions are indistinguishable; this gate proves nothing")

    print("\nG-CA: %s" % ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("  " + f)
    if fails:
        raise AssertionError("; ".join(fails))
    print("  worst deviation across all validated isotherms: %.3f%%" % worst)
    return worst


if __name__ == "__main__":
    main()
