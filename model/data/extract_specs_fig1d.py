#!/usr/bin/env python3
"""One-shot extraction of the 384 per-well yields of the SPECS reproducibility plate (Górski et al., Nature 2025).

    cd Section4_Model && python data/extract_specs_fig1d.py   -> data/specs_fig1d_yields.csv

SOURCE (state A, two locators for the same table).
  B. Górski, ..., J. Rein, ..., S. Lin, "Light-harvesting microelectronic devices for wireless electrosynthesis",
  Nature 2025, 637, 354-361, DOI 10.1038/s41586-024-08373-1.
  * Supplementary Information, Section 5.4 "Reproducibility studies", printed p. 29 (PDF p. 30): the 16 x 24
    table of UPLC yields (%) for the 384 quality-controlled SPECS re-subjected to the TMB bromination assay
    (Setup B), followed by the statement: "a narrow distribution of yields around the average of 56.6% was
    observed with a standard deviation of 2.6% (one device provided a yield more than 3σ smaller than the
    average yield on this plate). This corresponds to an average current of 7.6 µA with a standard deviation
    of 0.3 µA." The same table is printed on the plate image of main-text Fig. 1d (p. 355).
  * Main text p. 355: "we randomly selected 384 of the working devices ... average yield of 57(3)%, which
    corresponds to a current of 7.6 µA with a narrow standard deviation of 0.3 µA, with only one device
    producing a current outside the 3σ range."
  * SI Section 5.1 (p. 25): the assay "shows a 100% faradaic efficiency", 0.5 µmol TMB per well, 2 h, so the
    yield converts to a mean current; figs/make_fig_specs.py does that conversion with 2 F per bromination and
    asserts the printed 7.6 +/- 0.3 µA against it.
The SI PDF is kept at papers for model/s41586-024-08373-1_SI_Gorski2025.pdf. This is deliberately NOT a
build-time parse; the CSV is the shipped artifact and the generator asserts the printed summary against it.
"""
import csv, os, re, statistics as st, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), "papers for model", "s41586-024-08373-1_SI_Gorski2025.pdf")
OUT = os.path.join(HERE, "specs_fig1d_yields.csv")
doc = pymupdf.open(SI)
def _rows(i):
    ls = [ln.strip() for ln in doc[i].get_text().split("\n")]
    return ls, [[int(x) for x in ln.split()] for ln in ls if re.fullmatch(r"(\d{2} ){23}\d{2}", ln)]
# the heading also appears in the table of contents, so the page is the one that carries the heading AND the table
page = next(i for i in range(len(doc)) if "Reproducibility studies" in doc[i].get_text() and len(_rows(i)[1]) == 16)
lines, rows = _rows(page)
if len(rows) != 16:
    raise SystemExit("expected 16 rows of 24 yields on SI p. %d, found %d" % (page + 1, len(rows)))
vals = [v for r in rows for v in r]
stated = re.search(r"average of ([\d.]+)% was observed with a standard deviation of ([\d.]+)%", " ".join(lines))
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["# Gorski et al., Nature 2025, 637, 354-361, DOI 10.1038/s41586-024-08373-1: SI Section 5.4 'Reproducibility studies', printed p. 29 (PDF p. %d) -- UPLC yield (%%) of the TMB bromination assay per well, 384 quality-controlled SPECS, rows A-P x columns 1-24; the same table is printed on main-text Fig. 1d (p. 355). Read by data/extract_specs_fig1d.py; the SI states an average of %s%% and a standard deviation of %s%%." % (page + 1, stated.group(1), stated.group(2))])
    w.writerow(["row"] + [str(c) for c in range(1, 25)])
    for i, r in enumerate(rows):
        w.writerow([chr(65 + i)] + r)
print("wrote %s from SI PDF p. %d: %d wells, min %d, max %d, mean %.2f, sd %.2f (SI states %s / %s)"
      % (os.path.relpath(OUT, ROOT), page + 1, len(vals), min(vals), max(vals), st.mean(vals), st.stdev(vals), stated.group(1), stated.group(2)))
