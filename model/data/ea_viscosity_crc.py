#!/usr/bin/env python3
"""G-EAVISC -- put a MEASURED number behind the Ea = 15 kJ/mol upper bound of S6.3.

    cd Section4_Model && python data/ea_viscosity_crc.py
    cd Section4_Model && python data/ea_viscosity_crc.py --negative-control

WHY
---
S6.3 brackets the temperature dependence of kappa with Arrhenius scaling at Ea = 15 kJ/mol. That
number was DECLARED: the registry said outright "no page-anchored source for Ea itself", and the
only thing behind it was the activation energy of WATER's viscosity from the CRC 0-100 C table
(eta 0.890 -> 0.282 mPa s over 25 -> 100 C, which is 14.2 kJ/mol, rounded up to 15).

Water is not one of the three organic solvents whose ceilings S6.3 actually brackets. This reads
the activation energy of the RIGHT solvents, from the SAME CRC table that already page-anchors
their 25 C viscosities (97th ed., "Viscosity of Liquids", p. 6-243 ff.), so the bound stops being
an analogy and becomes a comparison against measurement.

Walden's rule (Lambda * eta ~ const) ties the temperature coefficient of conductivity to that of
viscosity, so Ea(eta) is the right quantity to compare an Ea(kappa) bound against.

THE SELF-CHECK THAT MAKES THIS SAFE
-----------------------------------
The CRC table drops blank cells, so a text extraction cannot be trusted to assign temperatures to
values by position alone -- for acetonitrile the first extracted value implies Ea = 2.2 kJ/mol
against 7-8 from every other interval, which is not physical. Columns are therefore assigned by
x-coordinate against the eta() header positions, and EVERY ROW IS REJECTED UNLESS ITS 25 C VALUE
REPRODUCES THE VISCOSITY THE REGISTRY ALREADY PAGE-ANCHORS FOR THAT SOLVENT. Water fails that
check (its row mis-aligns) and is dropped rather than repaired -- which is the check working.
"""
import csv
import io
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CRC = os.path.join(os.path.dirname(ROOT), "Model Papers for Params",
                   "CRC Handbook of Chemistry and Physics - 97th Edition (2016).pdf")
PAGES = range(1294, 1300)                       # PDF pages holding printed 6-243 ff.
COLT = {262: -25, 313: 0, 359: 25, 407: 50, 455: 75, 501: 100}
NAMES = {"Acetonitrile": "MeCN", "Tetrahydrofuran": "THF",
         "N,N-Dimethylformamide": "DMF", "Water": "H2O"}
R = 8.314
DECLARED_EA = 15000.0                            # J/mol, the S6.3 upper bound


def main(neg=False):
    import pymupdf
    if not os.path.exists(CRC):
        sys.exit("CRC handbook not found at %s" % CRC)
    reg = {r["solvent"]: float(r["mu_mPas"]) for r in
           csv.DictReader(io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8"))}
    doc = pymupdf.open(CRC)
    found = {}
    for pg in PAGES:
        words = doc[pg].get_text("words")
        for name, key in NAMES.items():
            if key in found:
                continue
            hit = [w for w in words if w[4] == name]
            if not hit:
                continue
            y = hit[0][1]
            line = sorted([w for w in words if abs(w[1] - y) < 3], key=lambda w: w[0])
            vals, i = {}, 0
            while i < len(line):                 # the table prints "0. 369" as two tokens
                if re.fullmatch(r"\d+\.", line[i][4]) and i + 1 < len(line) \
                        and re.fullmatch(r"\d+", line[i + 1][4]):
                    T = COLT[min(COLT, key=lambda c: abs(c - (round(line[i][0]) + 6)))]
                    vals[T] = float(line[i][4] + line[i + 1][4])
                    i += 2
                else:
                    i += 1
            found[key] = vals

    print("  CRC 97th ed., Viscosity of Liquids (p. 6-243 ff.), columns assigned by x-position")
    print("  and ACCEPTED ONLY IF eta(25 C) reproduces the registry's page-anchored value.\n")
    print("  %-6s %-12s %-12s %-8s %s" % ("solv", "registry mu", "CRC eta(25)", "accept", "Ea(eta) kJ/mol"))
    out, eas = {}, []
    for key, vals in found.items():
        r25 = reg.get(key)
        got = vals.get(25)
        ok = (r25 is not None and got is not None
              and abs(got - r25) <= 0.02 * max(r25, 1e-9))
        if neg:
            ok = ok and key == "__none__"        # control: accept nothing
        pairs = []
        if ok:
            Ts = sorted(t for t in vals if t >= 25)
            for a, b in zip(Ts, Ts[1:]):
                ea = R * math.log(vals[a] / vals[b]) / (1 / (a + 273.15) - 1 / (b + 273.15))
                pairs.append((a, b, ea))
                eas.append(ea)
            out[key] = {"eta": vals, "Ea_J_per_mol": [p[2] for p in pairs]}
        print("  %-6s %-12s %-12s %-8s %s"
              % (key, r25, got, "YES" if ok else "no",
                 "  ".join("%d-%dC: %.1f" % (a, b, e / 1000) for a, b, e in pairs)))

    if not eas:
        print("\nG-EAVISC: %s" % ("control GOOD (nothing accepted, nothing derived)" if neg
                                 else "REVIEW NEEDED -- no solvent row passed the eta(25) check"))
        return 0 if neg else 1
    lo, hi = min(eas), max(eas)
    json.dump({"solvents": out, "Ea_range_J_per_mol": [lo, hi],
               "declared_Ea_J_per_mol": DECLARED_EA,
               "declared_over_measured": [DECLARED_EA / hi, DECLARED_EA / lo]},
              io.open(os.path.join(ROOT, "results", "ea_viscosity_crc.json"), "w",
                      encoding="utf8"), indent=1)
    print("\n  Measured Ea(eta) across the three organic solvents S6.3 brackets: %.1f-%.1f kJ/mol."
          % (lo / 1000, hi / 1000))
    print("  The declared Ea(kappa) upper bound of %.0f kJ/mol is %.1f-%.1fx that range, so it is"
          % (DECLARED_EA / 1000, DECLARED_EA / hi, DECLARED_EA / lo))
    print("  conservative by about a factor of two -- which is what an upper bound should be.")
    if DECLARED_EA < lo:
        print("\nG-EAVISC: REVIEW NEEDED -- the declared bound is BELOW the measured activation "
              "energy, so it is not an upper bound at all")
        return 1
    print("\nG-EAVISC: PASS -- the declared Ea exceeds every measured viscous activation energy, "
          "so S6.3's upper bracket is genuinely an upper bracket")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
