#!/usr/bin/env python3
"""G-KAPPA-CA -- check the model's tetraalkylammonium/MeCN conductivities against a MEASURED
correlation, independent of however they were originally derived.

    cd Section4_Model && python data/check_kappa_casteel.py

THE SOURCE
----------
Dorn, M.; Kareth, S.; Weidner, E.; Petermann, M. "Electrical Conductivity of Lithium, Sodium,
Potassium, and Quaternary Ammonium Salts in Water, Acetonitrile, Methanol, and Ethanol over a Wide
Concentration Range", J. Chem. Eng. Data 2024, 69, 1493-1502. TABLE 3, p. 1499, read from a
300-dpi page image: Casteel-Amis parameters at 298.15 K, with the fit's own MAPE.

    kappa = kappa_max * (m/m_max)^a * exp[ -b*(m - m_max)^2 - (a/m_max)*(m - m_max) ]

    solvent  salt          m_max     kappa_max   a         b          validity   MAPE
    ACN      (C2H5)4NBF4   4.00409   60.97       0.84952   -0.02650   2.82       0.80%
    ACN      (C4H9)4NBF4   1.48127   33.40       0.78646   -0.02156   9.10       1.65%

WHY IT IS WORTH HAVING
----------------------
Six entries of the ELECTROLYTES table in build_reactions50.py are tetraalkylammonium
tetrafluoroborate in acetonitrile, spanning 0.043 to 0.3 M. They were derived, not measured. This
gate tests them against a measurement made by someone else, by a different method, and reported
with its own fit error -- the kind of check that cannot be satisfied by an internally consistent
mistake.

A NOTE ON UNITS, which is where this kind of comparison usually goes wrong: the correlation is in
MOLALITY (mol per kg of solvent) and the model tabulates MOLARITY. For these dilute acetonitrile
solutions m = c / rho(MeCN) with rho = 0.776 g/cm3, the same density the SOLVENTS table already
carries from the CRC. At 0.3 M that is 0.387 mol/kg, comfortably inside the 2.82 mol/kg validity
range of the Et4N fit and the 9.10 of the Bu4N fit, so no extrapolation is involved.
"""
import io, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 0.10          # 10%: the fits' own MAPE is 0.8-1.65%, and the model values are derived
RHO_MECN = 0.776

CA = {"Et4NBF4": (4.00409, 60.97, 0.84952, -0.02650, 2.82, 0.80),
      "Bu4NBF4": (1.48127, 33.40, 0.78646, -0.02156, 9.10, 1.65)}


def kappa(salt, c_molar):
    mmax, kmax, a, b, valid, _ = CA[salt]
    m = c_molar / RHO_MECN
    k = kmax * (m / mmax) ** a * math.exp(-b * (m - mmax) ** 2 - (a / mmax) * (m - mmax))
    return k, m, m <= valid


def main(neg=False):
    src = io.open(os.path.join(HERE, "build_reactions50.py"), encoding="utf8").read()
    found = {}
    for mt in re.finditer(r'"([\d.]+) M (Bu4NBF4|Et4NBF4)/MeCN":\s*([\d.]+)', src):
        found[(mt.group(2), float(mt.group(1)))] = float(mt.group(3))
    if neg and found:
        # push one carried kappa 40% off: it must fall outside the 10% agreement window
        k0 = sorted(found)[0]
        found[k0] = found[k0] * 1.40
    if not found:
        print("G-KAPPA-CA: no Bu4NBF4/Et4NBF4 in MeCN entries found -- did the key format change?")
        return 1
    print("%-24s %-9s %-10s %-11s %-8s %s" %
          ("electrolyte", "molality", "measured", "model", "diff", "in validity"))
    bad = []
    for (salt, c), k_model in sorted(found.items()):
        k_ca, m, ok = kappa(salt, c)
        d = k_model / k_ca - 1
        if abs(d) > TOL or not ok:
            bad.append((salt, c, k_model, k_ca, d, ok))
        print("%-24s %-9.3f %-10.2f %-11.2f %-+8.1f%% %s"
              % ("%g M %s/MeCN" % (c, salt), m, k_ca, k_model, 100 * d, "yes" if ok else "NO"))
    print()
    print("tolerance %.0f%%; the correlations' own MAPE is 0.80%% (Et4N) and 1.65%% (Bu4N)" % (100 * TOL))
    if bad:
        if neg:
            print("G-KAPPA-CA control: GOOD (the perturbed entry was detected)")
            return 0
        print("G-KAPPA-CA: FAIL")
        for salt, c, km, kc, d, ok in bad:
            print("   %g M %s/MeCN: model %.2f vs measured %.2f (%+.1f%%)%s"
                  % (c, salt, km, kc, 100 * d, "" if ok else "  [outside fit validity]"))
        return 1
    if neg:
        print("G-KAPPA-CA control: BAD -- test is inert (a 40%% perturbation went undetected)")
        return 1
    print("G-KAPPA-CA: PASS -- all %d entries agree with the measured correlation within %.0f%%"
          % (len(found), 100 * TOL))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
