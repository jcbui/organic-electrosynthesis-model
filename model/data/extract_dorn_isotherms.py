"""Pull the MEASURED conductivity isotherms out of the Dorn Supporting Information.

    cd Section4_Model && python data/extract_dorn_isotherms.py

WHY THIS EXISTS
---------------
The five Bu4NBF4/MeCN rows were state B, "derived by Casteel-Amis from Dorn's Table 3". Two things
turned out to be wrong with that.

1. THE ARITHMETIC WAS NOT REPRODUCIBLE. State B requires that a reader can redo the sum from the
   registry alone. There was no Casteel-Amis implementation anywhere in the repository -- the
   values 5.18 / 8.07 / 9.87 / 18.9 / 21.34 were typed literals in build_param_tables.py, computed
   once by hand and never recomputed. Nothing could have caught them drifting.

2. THE SIGN CONVENTION IS AMBIGUOUS AND WAS PROBABLY WRONG. Casteel-Amis is written in several
   equivalent-looking ways. Against Dorn's OWN kappa_calc column, only

       kappa = kappa_max (m/m_max)^a exp[ -b (m - m_max)^2 - a (m/m_max - 1) ]

   reproduces the paper: at m = 0.0905 it gives 8.086 against the tabulated 8.08, and at
   m = 1.2560 for NaOH/water it gives 218.3 against the tabulated 218.32. The opposite sign gives
   9.87 at m = 0.133 where this form gives 10.68 -- and 9.87 is exactly the literal the registry
   carried, which is the evidence that the literals were produced with the wrong sign.

THE FIX IS NOT A BETTER FIT EVALUATION
--------------------------------------
The SI carries the RAW MEASURED POINTS, not just the fit parameters -- 164 isotherms over 167
pages. Every concentration this project needs is inside the measured range of its isotherm, so
the values can be read off the measurements and interpolated, and the fit is not needed at all.
That converts these rows from "state B by a correlation whose sign we got wrong" to "state A,
interpolated between two measured points that are printed in the source".

The extraction is deliberately a SEPARATE, one-shot script writing a CSV, not a build-time parse
of a 318-page PDF: the PDF is the primary source and must stay auditable, but a build that depends
on pdf text extraction is a build that breaks silently when a library changes.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(os.path.dirname(ROOT), "papers for model", "je3c00691_si_001.pdf")
OUT = os.path.join(HERE, "dorn_isotherms.csv")

# (salt as printed in the SI table title, solvent, our short name)
WANTED = [
    ("tetrabutylammonium tetrafluoroborate", "acetonitrile", "Bu4NBF4/MeCN"),
    ("tetraethylammonium tetrafluoroborate", "acetonitrile", "Et4NBF4/MeCN"),
    ("sodium hydroxide", "water", "NaOH/H2O"),
    ("sodium chloride", "water", "NaCl/H2O"),
    ("potassium hydrogen carbonate", "water", "KHCO3/H2O"),
    ("sodium carbonate", "water", "Na2CO3/H2O"),
    ("sodium iodide", "methanol", "NaI/MeOH"),
    ("potassium thiocyanate", "methanol", "KSCN/MeOH"),
]
ROW = re.compile(r"^([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+This work\s+([\d.]+)")


def main():
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    if not os.path.exists(PDF):
        sys.exit("missing %s" % PDF)
    r = PdfReader(PDF)
    pages = [(i, r.pages[i].extract_text() or "") for i in range(len(r.pages))]

    out = ["system,table,page,m_mol_kg,u_m,kappa_mScm,u_kappa,kappa_calc"]
    found = {}
    for salt, solvent, short in WANTED:
        pat = re.compile(r"Electrical conductivity of %s in %s" % (re.escape(salt),
                                                                  re.escape(solvent)), re.I)
        hit = None
        for i, t in pages:
            if pat.search(t):
                hit = (i, t)
                break
        if hit is None:
            print("  NOT FOUND: %s in %s" % (salt, solvent))
            continue
        i, t = hit
        tbl = re.search(r"Table SI (\d+)", t)
        n = 0
        for ln in t.split("\n"):
            m = ROW.match(ln.strip())
            if m:
                out.append("%s,SI %s,%d,%s,%s,%s,%s,%s"
                           % (short, tbl.group(1) if tbl else "?", i + 1,
                              m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)))
                n += 1
        found[short] = (tbl.group(1) if tbl else "?", i + 1, n)
        print("  %-14s Table SI %-3s p.%-4d %d measured points" % (short, found[short][0], i + 1, n))

    with open(OUT, "w") as f:
        f.write("\n".join(out) + "\n")
    print("\nwrote %s (%d rows)" % (os.path.relpath(OUT, ROOT), len(out) - 1))
    return found


if __name__ == "__main__":
    main()
