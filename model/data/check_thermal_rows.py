#!/usr/bin/env python3
"""G-THERMROWS -- do the shipped thermal sensitivities describe the reactors the model has?

    cd Section4_Model && python data/check_thermal_rows.py
    cd Section4_Model && python data/check_thermal_rows.py --negative-control

WHY THIS GATE EXISTS
--------------------
Every other thermal gate compares a NUMBER against the model. None of them compares a
sensitivity's DESCRIPTION OF ITS OPERATING POINT against the reactor table, and on 2026-09-12 an
audit found ten category-6/8/9 rows still describing the ladder v94 retired -- declared design
currents of 50/100/500 mA cm-2, a "5 mm flow cell", a "250 um microfluidic", "FIVE of the seven
archetypes". Those strings ship verbatim into Table S7. Three of them were not merely stale but
FALSE at the current operating point: the evaporative-loss row called the unstirred THF beaker
"the one fail in an open vessel" when that cell passes at 3.60x, the microfluidic sigma row said
its exposure "crosses unity" when it survives down to 0.05x the area ratio, and the cell-volume
row had the direction of its own conclusion reversed.

WHAT IT ASSERTS
---------------
For the thermal categories, in the columns that SHIP (value, units, citation, locator,
sensitivity, equation -- method_note is the internal column and is deliberately not read):

  1. every "i_design = N" and "design current(s) ... N mA cm-2" names a current the reactor
     table actually carries, to 1%;
  2. no row names an architecture the reactor table does not have;
  3. no row carries the editing vocabulary this area kept re-acquiring, which G-VOICE's
     general patterns do not cover ("has already turned over", "rather than 1.07x",
     "requires them to read", "The manuscript prints").

Exemptions are per row, verbatim, with the reason -- never a blanket suppression.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "figs"))
import thermal_model as TM                                              # noqa: E402

REG = os.path.join(HERE, "parameters_provenance.csv")
SHIPPED = ("value", "units", "citation", "locator", "sensitivity", "equation")
CATEGORIES = ("6", "8", "9")

# Rows allowed to name a retired geometry, each with the reason it is legitimate.
EXEMPT = {
    "Illustrative channel pair (S8.1)":
        "S8.1's per-pass conversion comparison IS the 1 mm / 250 um channel pair; it is a "
        "declared illustration of intensification, not a thermal archetype, and the row says so.",
    "Leveque: Sh = 1.85 (Re Sc dh/L)^(1/3)":
        "the same S8.1 illustration, quoted as the ratio that section reports.",
}

# Architectures the reactor table no longer has. Matched case-insensitively as whole phrases.
RETIRED_ARCH = [r"5\s*mm\s+flow", r"5-mm\s+flow", r"250\s*(?:um|µm|μm)\s*microfluidic",
                r"250\s*(?:um|µm|μm)\s*(?:gap\s*)?cell", r"thin[- ]gap\s+archetype"]

# Process narrative specific to this area. G-VOICE catches the general vocabulary; these are the
# forms that survived it, every one found shipped in Table S7 on 2026-09-12.
RETIRED_VOICE = [r"has already turned over", r"rather than 1\.07x", r"requires them to read",
                 r"The manuscript prints", r"which 2\.9x has already"]


def design_currents():
    return sorted(r[4] for r in TM.REACTORS)


def arch_labels():
    return [r[0].replace("\n", " ").replace("$\\mu$", "u") for r in TM.REACTORS]


def scan(rows, currents):
    """Return a list of (parameter, column, kind, detail) findings."""
    out = []
    for r in rows:
        if not r["category"].strip()[:1] in CATEGORIES:
            continue
        name = r["parameter"]
        if name in EXEMPT:
            continue
        for col in SHIPPED:
            cell = r.get(col) or ""
            if not cell:
                continue
            for m in re.finditer(r"i_design\s*=\s*([0-9]+(?:\.[0-9]+)?)", cell):
                v = float(m.group(1))
                if not any(abs(v - c) <= 0.01 * max(v, c) for c in currents):
                    out.append((name, col, "design current",
                                "i_design = %s is not a current the reactor table carries (%s)"
                                % (m.group(1), ", ".join("%.1f" % c for c in currents))))
            for m in re.finditer(r"design currents?\s+((?:[0-9]+\s*/\s*)+[0-9]+)", cell):
                for tok in re.split(r"\s*/\s*", m.group(1)):
                    v = float(tok)
                    if not any(abs(v - c) <= 0.01 * max(v, c) for c in currents):
                        out.append((name, col, "design current",
                                    "the series '%s' names %s, which no reactor carries"
                                    % (m.group(1), tok)))
                        break
            for pat in RETIRED_ARCH:
                m = re.search(pat, cell, re.IGNORECASE)
                if m:
                    out.append((name, col, "retired architecture",
                                "names '%s', which is not a row of the reactor table"
                                % m.group(0)))
            for pat in RETIRED_VOICE:
                m = re.search(pat, cell)
                if m:
                    out.append((name, col, "editing narrative",
                                "carries '%s'" % m.group(0)))
    return out


def main(neg=False):
    rows = list(csv.DictReader(open(REG, encoding="utf8")))
    currents = design_currents()
    print("G-THERMROWS -- shipped thermal sensitivities against the reactor table")
    print("  reactor table: %d rows, design currents %s mA cm-2"
          % (len(TM.REACTORS), ", ".join("%.1f" % c for c in currents)))
    print("  architectures: %s" % ", ".join(arch_labels()))
    print("  scanning categories %s in columns %s (method_note is internal and is not read)"
          % ("/".join(CATEGORIES), ", ".join(SHIPPED)))
    for k, v in EXEMPT.items():
        print("  exempt: %s -- %s" % (k, v))

    if neg:
        # Inject one retired operating point into a row that is currently clean, and require the
        # gate to find it. Perturbs a COPY -- the registry on disk is never written by a control.
        victim = next(r for r in rows if r["parameter"] == "Vessel external area")
        victim = dict(victim)
        victim["sensitivity"] = (victim["sensitivity"] or "") + \
            " Judged against i_design = 500 in the 250 um microfluidic cell."
        rows = [victim if r["parameter"] == "Vessel external area" else r for r in rows]

    found = scan(rows, currents)
    for name, col, kind, detail in found:
        print("  %-46s %-12s %-22s %s" % (name[:46], col, kind, detail))

    if neg:
        hit = any(n == "Vessel external area" for n, _, _, _ in found)
        print("\nNEGATIVE CONTROL: a retired design current and a retired architecture were "
              "injected into one clean row.")
        print("G-THERMROWS control: %s (%d finding(s))"
              % ("GOOD" if hit else "BAD -- test is inert", len(found)))
        return 0 if hit else 1

    if found:
        print("\nG-THERMROWS: FAIL -- %d shipped thermal cell(s) describe an operating point or "
              "an architecture the model does not have." % len(found))
        return 1
    print("\nG-THERMROWS: PASS -- every shipped thermal sensitivity names an architecture the "
          "reactor table carries and a design current it computes.")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
