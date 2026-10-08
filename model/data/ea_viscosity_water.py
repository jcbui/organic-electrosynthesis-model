#!/usr/bin/env python3
"""Water's viscous activation energy from the CRC 'Viscosity of Liquids' table -- the row data/ea_viscosity_crc.py drops.

    cd Section4_Model && /opt/anaconda3/bin/python3.12 data/ea_viscosity_water.py

WHY
---
data/ea_viscosity_crc.py (G-EAVISC) reads Ea(eta) for MeCN, DMF and THF from CRC 97th ed. 'Viscosity of Liquids'
(p. 6-243 ff.) and reports that water "fails" its eta(25 C) acceptance check. It does not: that script takes the FIRST
'Water' token in PDF pages 1294-1299, which is the gas-viscosity table on p. 6-242 (PDF index 1294), so it reads a
row of gas viscosities in uPa s against liquid column positions. The liquid table prints water on p. 6-247 (PDF index
1299): eta = 1.793 / 0.890 / 0.547 / 0.378 / 0.282 mPa s at 0 / 25 / 50 / 75 / 100 C, and 0.890 is the registry value.

This script reads that row ONLY from a page whose header is 'Viscosity of Liquids', assigns columns by x-position
against the eta(T) headers of the same table, applies the same acceptance rule (eta(25 C) must reproduce the
registry's page-anchored viscosity), and writes results/ea_viscosity_water.json. It edits nothing else.
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
PAGES = range(1294, 1300)
R = 8.314
OUT = os.path.join(ROOT, "results", "ea_viscosity_water.json")


def main():
    import pymupdf
    reg = {r["solvent"]: float(r["mu_mPas"]) for r in
           csv.DictReader(io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8"))}
    doc = pymupdf.open(CRC)
    # column x-positions from the eta(T) headers of the liquid table (they are printed on the even pages)
    def liquid(pg):
        return "Viscosity of Liquids" in " ".join(w[4] for w in doc[pg].get_text("words") if w[1] < 40)
    colx = {}
    for pg in PAGES:
        if not liquid(pg):
            continue
        for w in doc[pg].get_text("words"):
            m = re.fullmatch(r"η\((-?\d+)", w[4])
            if m:
                colx.setdefault(int(m.group(1)), []).append(w[0])
    colx = {t: sum(v) / len(v) for t, v in colx.items()}
    if sorted(colx) != [-25, 0, 25, 50, 75, 100]:
        sys.exit("eta(T) headers not found as expected: %s" % sorted(colx))
    found = None
    for pg in PAGES:
        page = doc[pg]
        words = page.get_text("words")
        if not liquid(pg):
            continue
        hit = [w for w in words if w[4] == "Water"]
        if not hit:
            continue
        y = hit[0][1]
        line = sorted([w for w in words if abs(w[1] - y) < 3], key=lambda w: w[0])
        vals, i = {}, 0
        while i < len(line):                    # the table prints "0. 890" as two tokens
            if re.fullmatch(r"\d+\.", line[i][4]) and i + 1 < len(line) and re.fullmatch(r"\d+", line[i + 1][4]):
                xr = line[i + 1][0] + 0.0
                T = min(colx, key=lambda c: abs(colx[c] - xr))
                vals[T] = float(line[i][4] + line[i + 1][4])
                i += 2
            else:
                i += 1
        label = [w[4] for w in words if w[1] < 40 and re.fullmatch(r"6-\d+", w[4])]
        found = {"pdf_index": pg, "page": label[0] if label else "?", "eta": vals}
        break
    if not found:
        sys.exit("water row not found on a 'Viscosity of Liquids' page")
    eta = found["eta"]
    if abs(eta.get(25, -1) - reg["H2O"]) > 0.02 * reg["H2O"]:
        sys.exit("water eta(25 C) = %s does not reproduce the registry %.3f" % (eta.get(25), reg["H2O"]))
    Ts = sorted(t for t in eta if t >= 25)
    pairs = [(a, b, R * math.log(eta[a] / eta[b]) / (1 / (a + 273.15) - 1 / (b + 273.15))) for a, b in zip(Ts, Ts[1:])]
    overall = R * math.log(eta[25] / eta[100]) / (1 / 298.15 - 1 / 373.15)
    json.dump({"source": "CRC 97th ed., 'Viscosity of Liquids', p. %s (PDF index %d), Water row" % (found["page"], found["pdf_index"]),
               "eta_mPas": {str(k): v for k, v in sorted(eta.items())},
               "registry_eta25": reg["H2O"],
               "Ea_intervals_J_per_mol": [{"T1": a, "T2": b, "Ea": e} for a, b, e in pairs],
               "Ea_25_100_J_per_mol": overall,
               "walden_factor_25_100": eta[25] / eta[100]},
              io.open(OUT, "w", encoding="utf8"), indent=1)
    print("  water, %s: eta %s mPa s; registry eta(25) = %.3f -> accepted"
          % (found["page"], ", ".join("%d C %.3f" % (k, v) for k, v in sorted(eta.items())), reg["H2O"]))
    print("  Ea(eta): %s; over 25-100 C %.1f kJ/mol" % (", ".join("%d-%d C %.1f" % (a, b, e / 1000) for a, b, e in pairs),
                                                      overall / 1000))
    print("  -> %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
