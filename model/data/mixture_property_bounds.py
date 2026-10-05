#!/usr/bin/env python3
"""G-MIXBOUND -- put a SOURCEABLE bound under every mixed-solvent viscosity and density.

    cd Section4_Model && python data/mixture_property_bounds.py
    cd Section4_Model && python data/mixture_property_bounds.py --negative-control

WHY
---
Twelve rows of category 2 read "-- (no source supports this value)": the mu and rho of six
solvent MIXTURES. They are blend estimates. Nothing can page-anchor a 25 C value at a stated
volume ratio for most of them, and inventing one is not an option. What IS possible is to bound
them with numbers that can be cited, and to say exactly what assumption each bound rests on.

TWO KINDS OF MIXTURE, AND THEY NEED DIFFERENT ARGUMENTS
-------------------------------------------------------
A pure-component bracket is NOT generally valid for viscosity. Aqueous-organic mixtures show a
viscosity MAXIMUM that exceeds both pure components -- methanol/water peaks near 1.8 mPa s against
0.54 for methanol and 0.89 for water -- so "between the two pure values" would be a false bound
for exactly the systems where it is most tempting. The two families are therefore separated:

  MEASURED MIXTURE DATA (aqueous alcohols). CRC 97th ed., "Concentrative Properties of Aqueous
  Solutions", pp. 5-118 ff., tabulates rho and eta for aqueous methanol and ethanol against mass
  per cent. Its own header states "All data refer to a temperature of 20 C", which is why it
  cannot SOURCE a 25 C value -- and why it can BOUND one: eta and rho both decrease monotonically
  with temperature over 20 -> 25 C for these liquids, so the 20 C entry is a rigorous UPPER BOUND
  on the 25 C value. That is the conservative direction for the model: i_lim ~ mu^p with p in
  [-1, -2/3], so an upper bound on mu is a LOWER bound on i_lim.

  PURE-COMPONENT BRACKET (organic-organic). For mixtures of two organic liquids of similar class
  and no strong hetero-association, viscosity is monotone between the pure values, so the bracket
  is [min, max] of two page-anchored numbers. Applied ONLY to DMSO/THF and AcOH/HCOOH, and flagged
  as an assumption rather than a measurement.

WHAT IS STILL ASSUMED, STATED PLAINLY
-------------------------------------
  1. v/v -> mass per cent uses the pure-component densities at 25 C, not 20 C. The two differ by
     about 0.3 pct, which moves the mass per cent by under 0.2 and the interpolated eta by under
     0.5 pct -- far inside the bound being drawn.
  2. "1:1 v/v" is read as volumes measured BEFORE mixing, the usual laboratory convention. Excess
     volume is not modelled; it is absorbed by the fact that the CRC row is indexed by MASS, which
     is conserved.
  3. DMF/H2O and tAmOH/H2O appear in NO table located here. They are aqueous-organic, so the
     pure-component bracket is not valid upward, and they keep no upper bound -- only the
     statement that they are estimates. This is a declared gap, not a silent one.
  4. The bracket for the two organic-organic pairs assumes monotone mixing. It is an assumption,
     not a measurement, and is labelled as such.
"""
import csv
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CRC = os.path.join(os.path.dirname(ROOT), "Model Papers for Params",
                   "CRC Handbook of Chemistry and Physics - 97th Edition (2016).pdf")
# CRC 5-118 blocks: (pdf page, table name, names that start the NEXT table)
CRC_TABLES = {
    "MeOH": (990, "Methanol", ["Nitric acid", "Perchloric", "Phosphoric", "Potassium"]),
    "EtOH": (986, "Ethanol", ["Ethylene glycol", "Formic acid", "Glycerol", "Hydrochloric"]),
}
# mixture -> (component A, component B, volume ratio A:B), A is the non-water component
MIX = {
    "MeOH/H2O":   ("MeOH", "H2O", 1.0, 1.0, "aqueous-measured"),
    "EtOH/H2O":   ("EtOH", "H2O", 1.0, 1.0, "aqueous-measured"),
    "DMSO/THF":   ("DMSO", "THF", 5.0, 1.0, "organic-bracket"),
    "AcOH/HCOOH": ("AcOH", "HCOOH", 1.0, 1.0, "organic-bracket"),
    "DMF/H2O":    ("DMF", "H2O", 9.0, 1.0, "aqueous-unsourced"),
    "tAmOH/H2O":  ("tAmOH", "H2O", 3.0, 1.0, "aqueous-unsourced"),
}
# pure components not in solvents.csv, with their own page anchors
EXTRA_PURE = {
    # CRC 97th ed., Sect. 6 'Viscosity of Liquids' p. 6-243 ff. (eta, 25 C) and Sect. 15 (rho)
    "HCOOH": (1.607, 1.220, "CRC 97th ed., formic acid"),
    "tAmOH": (3.85, 0.805, "CRC 97th ed., 2-methyl-2-butanol"),
}


def solvents():
    return {r["solvent"]: r for r in
            csv.DictReader(io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8"))}


def crc_block(doc, page, name, stops):
    t = doc[page].get_text()
    i = t.find("\n%s\n" % name)
    if i < 0:
        i = t.find(name)
    seg = t[i + len(name):]
    for s in stops:
        j = seg.find("\n%s\n" % s)
        if j > 0:
            seg = seg[:j]
    nums = [float(x.replace(" ", "")) for x in re.findall(r"\d+\.\s?\d+", seg)]
    rows = [nums[k:k + 7] for k in range(0, len(nums) - 6, 7)]
    out, last = [], -1
    for r in rows:                       # keep the monotone mass% run; drop parse spill-over
        if len(r) == 7 and last < r[0] <= 100 and r[3] < 1.2:
            out.append(r); last = r[0]
    return out


def interp(rows, x, col):
    xs = [r[0] for r in rows]
    if x <= xs[0]:
        return rows[0][col]
    if x >= xs[-1]:
        return rows[-1][col]
    for a, b in zip(rows, rows[1:]):
        if a[0] <= x <= b[0]:
            f = (x - a[0]) / (b[0] - a[0])
            return a[col] + f * (b[col] - a[col])
    return None


def main(neg=False):
    import pymupdf
    sol = solvents()
    doc = pymupdf.open(CRC)
    pure = {}
    for k, r in sol.items():
        if "/" not in k:
            pure[k] = (float(r["mu_mPas"]), float(r["rho"]))
    for k, (mu, rho, _) in EXTRA_PURE.items():
        pure.setdefault(k, (mu, rho))

    rep, fails = [], []
    print("  %-12s %-8s %-8s %-22s %s" % ("mixture", "mu", "rho", "bound on mu (25 C)", "basis"))
    for name, (A, B, va, vb, kind) in MIX.items():
        row = sol.get(name)
        if row is None:
            continue
        mu_c, rho_c = float(row["mu_mPas"]), float(row["rho"])
        muA, rhoA = pure[A]; muB, rhoB = pure[B]
        if neg:
            mu_c *= 3.0                                    # must break every bound it has
        entry = {"mixture": name, "carried_mu": mu_c, "carried_rho": rho_c, "kind": kind}

        if kind == "aqueous-measured":
            mA, mB = va * rhoA, vb * rhoB                  # grams from volumes before mixing
            wpc = 100.0 * mA / (mA + mB)
            pg, nm, stops = CRC_TABLES[A]
            rows = crc_block(doc, pg, nm, stops)
            eta20 = interp(rows, wpc, 6); rho20 = interp(rows, wpc, 3)
            entry.update(mass_pct=wpc, eta_20C=eta20, rho_20C=rho20,
                         source="CRC 97th ed. 'Concentrative Properties of Aqueous Solutions', "
                                "pp. 5-118 ff., %s block, 20 C" % nm)
            ok = mu_c <= eta20 * 1.001
            entry["mu_within_bound"] = bool(ok)
            if not ok:
                fails.append("%s: carried mu %.3f EXCEEDS the 20 C measured %.3f, and a 25 C "
                             "viscosity cannot exceed its own 20 C value" % (name, mu_c, eta20))
            # DENSITY GETS THE SAME BOUND, and for the same reason: a liquid expands on warming,
            # so rho(25 C) < rho(20 C). Checking only the viscosity would leave half the row
            # unbounded while the citation covers both.
            rho_ok = rho_c <= rho20 * 1.001
            entry["rho_within_bound"] = bool(rho_ok)
            if not rho_ok:
                fails.append("%s: carried rho %.4f EXCEEDS the 20 C measured %.4f, and a 25 C "
                             "density cannot exceed its own 20 C value" % (name, rho_c, rho20))
            print("  %-12s %-8.3f %-8.3f <= %-19.3f %s at %.1f mass%%"
                  % (name, mu_c, rho_c, eta20, "CRC 5-118 (20 C)", wpc))
            print("  %-12s %-8s %-8s    rho(20 C) = %-14.4f (carried rho is %+.1f%% of it)"
                  % ("", "", "", rho20, 100.0 * (rho_c - rho20) / rho20))
        elif kind == "organic-bracket":
            lo, hi = min(muA, muB), max(muA, muB)
            entry.update(bracket=[lo, hi],
                         source="pure-component viscosities, both page-anchored; monotone mixing "
                                "ASSUMED (valid for organic-organic pairs without strong "
                                "hetero-association, not for aqueous-organic)")
            ok = lo * 0.999 <= mu_c <= hi * 1.001
            entry["mu_within_bound"] = bool(ok)
            if not ok:
                fails.append("%s: carried mu %.3f is outside the pure-component bracket "
                             "[%.3f, %.3f]" % (name, mu_c, lo, hi))
            print("  %-12s %-8.3f %-8.3f in [%.3f, %.3f]%s   pure-component bracket (assumed)"
                  % (name, mu_c, rho_c, lo, hi, " " * 6))
        else:
            entry.update(source="NONE LOCATED -- aqueous-organic, so a pure-component bracket is "
                                "not valid upward; carried as a declared estimate")
            entry["mu_within_bound"] = None
            print("  %-12s %-8.3f %-8.3f %-22s no table located; declared estimate"
                  % (name, mu_c, rho_c, "(none)"))
        rep.append(entry)

    out = os.path.join(ROOT, "results", "mixture_property_bounds%s.json"
                       % ("_NEGCONTROL" if neg else ""))
    json.dump(rep, io.open(out, "w", encoding="utf8"), indent=1)
    print("\n  -> %s" % os.path.relpath(out, ROOT))

    bounded = [e for e in rep if e["mu_within_bound"] is not None]
    print("\n  %d of %d mixtures now carry a sourceable bound on mu; %d remain declared estimates."
          % (len(bounded), len(rep), len(rep) - len(bounded)))
    if neg:
        ok = len(fails) >= len(bounded)
        print("\nNEGATIVE CONTROL: every carried viscosity tripled, so every bound must break.")
        print("G-MIXBOUND control: %s"
              % ("GOOD -- all %d bounded mixtures broke their bound" % len(fails) if ok else
                 "BAD -- only %d of %d broke; a bound that survives x3 is not a bound"
                 % (len(fails), len(bounded))))
        return 0 if ok else 1
    if fails:
        print("\nG-MIXBOUND: FAIL")
        for f in fails:
            print("  " + f)
        return 1
    print("\nG-MIXBOUND: PASS -- every mixture with a locatable bound sits inside it; the two "
          "without one are declared, not silently unsourced")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
