#!/usr/bin/env python3
"""G-DSENS -- bound the exposure of the model to the ion diffusivities that are still UNSOURCED.

    cd Section4_Model && python data/sensitivity_unsourced_D.py

WHY THIS EXISTS
---------------
After Krumgalz 1983, CRC 5-75/5-76 and EES 2015, 76 of the 100 (ion, row) diffusivity slots in
electrolyte_ions.csv carry a real source. 24 do not, and no source for them could be found on the
material to hand. Two shortcuts were TESTED AND REJECTED rather than quietly used:

  Walden transfer from water   median error 1.81x over 83 checkable pairs, only 7% within 30%,
                               worst 11x (H+). Unusable.
  Stokes-Einstein from the     median 0.89 but worst 6.7x over 85 pairs, 59% within 30%.
  EES printed ionic radii      Too loose to substitute for a measurement.

The per-ion lambda0*eta transfer was used ONLY for the four ions whose own data show it constant to
<12% (Bu4N+, Et4N+, Me4N+, BPh4-), which closed two slots.

For the remaining 24 the honest move is not to invent a number but to BOUND WHAT NOT KNOWING IT
COSTS. This script perturbs every unsourced diffusivity by a factor of 3 up and 3 down -- far wider
than any of the rejected estimators was wrong by -- re-solves the full 50x7 Nernst-Planck matrix
for each case, and reports how far the ceilings and the headline >=25 / >=50 counts move.

If the counts do not move, the gap is immaterial and can be stated as such WITH PROOF. If they do,
that is a real limitation and must be declared in the SI rather than discovered by a referee.

WHAT THIS SWEEP ACTUALLY MEASURES -- read before interpreting a zero
-------------------------------------------------------------------
The first run returned EXACTLY 0.0% on all 300 cells (350 since 2026-09-07), which normally means the perturbation never
reached the code. Here it is correct, and the reason is structural rather than numerical.

A species that does not react -- s = 0 at the electrode and nu = 0 in the homogeneous step -- has
ZERO NET FLUX at steady state, so its Nernst-Planck equation collapses to

    0 = -D(dc/dx) - (zDF/RT)*c*(dphi/dx)

and D cancels. Its profile is a Boltzmann distribution set by the potential alone. The limiting
current depends on the CHARGES and CONCENTRATIONS of the ion inventory and on the CARRIER's
diffusivity; a non-reacting ion's D does not enter it.

Verified directly: moving a counter-ion's D by a factor of ten in either direction leaves i_lim at
20.437 mA/cm2 and the migration factor at 2.009892 -- identical to six decimals. Moving the
CARRIER's D by 2x scales i_lim through i_Fick but leaves the enhancement at 2.009892.

Every one of the 24 unsourced slots is a supporting-ion column (D_cat / D_an). The carrier
diffusivity comes from reactions_50.csv and all 50 rows carry a D_provenance string. So a zero here
is the expected answer, not a broken harness -- and this sweep's value is as a REGRESSION test: if
it ever stops returning zero, something has started feeding a supporting-ion D into a reacting
species, which would be a modelling error worth catching.
"""
import csv, io, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JULIA = os.path.join(ROOT, "julia")
IONS = os.path.join(HERE, "electrolyte_ions.csv")
MATRIX = os.path.join(JULIA, "all50_np_matrix.csv")
FACTORS = [("div3", 1.0 / 3.0), ("mul3", 3.0)]


def load(path):
    rows = list(csv.DictReader(open(path)))
    if any(None in r for r in rows):
        raise SystemExit("electrolyte_ions.csv has malformed rows; fix quoting first")
    return rows


def perturb(rows, factor):
    out, n = [], 0
    for r in rows:
        r = dict(r)
        for d_col, b_col in (("D_cat", "D_cat_basis"), ("D_an", "D_an_basis")):
            if str(r.get(b_col, "")).startswith(("UNSOURCED", "DECLARED CLASS DEFAULT")):
                r[d_col] = "%.4g" % (float(r[d_col]) * factor)
                n += 1
        out.append(r)
    return out, n


def write(rows, path):
    fields = [k for k in rows[0].keys() if k is not None]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
    w.writeheader(); w.writerows(rows)
    txt = buf.getvalue()
    back = list(csv.DictReader(io.StringIO(txt)))
    if len(back) != len(rows) or any(None in r for r in back):
        raise SystemExit("refusing to write a perturbed table that does not round-trip")
    io.open(path, "w", encoding="utf8", newline="").write(txt)


def solve(tag):
    log = os.path.join("/tmp", "dsens_%s.log" % tag)
    with open(log, "w") as fh:
        rc = subprocess.call(["julia", "run_all50_np.jl"], cwd=JULIA, stdout=fh, stderr=fh)
    if rc != 0:
        raise SystemExit("julia failed for case %s; see %s" % (tag, log))
    return {(r["reaction"], r["reactor"]): float(r["i_np_mAcm2"])
            for r in csv.DictReader(open(MATRIX))}


def main():
    base_rows = load(IONS)
    n_uns = sum(1 for r in base_rows for b in ("D_cat_basis", "D_an_basis")
                if str(r.get(b, "")).startswith(("UNSOURCED", "DECLARED CLASS DEFAULT")))
    import re as _re
    pairs = set()
    for r in base_rows:
        for b in ("D_cat_basis", "D_an_basis"):
            m = _re.search(r"no lambda0 for (\S+) in (\S+) in", str(r.get(b, "")))
            if m and str(r.get(b, "")).startswith(("UNSOURCED", "DECLARED CLASS DEFAULT")):
                pairs.add((m.group(1), m.group(2)))
    print("declared-default diffusivity slots being perturbed: %d (%d ion/solvent pairs)" % (n_uns, len(pairs)))
    if not n_uns:
        print("nothing unsourced -- G-DSENS trivially PASSES"); return

    shutil.copy(IONS, IONS + ".dsens_backup")
    shutil.copy(MATRIX, MATRIX + ".dsens_backup")
    try:
        print("\nsolving BASE case ...")
        base = solve("base")
        results = {}
        for tag, f in FACTORS:
            rows, n = perturb(base_rows, f)
            write(rows, IONS)
            print("solving %s (x%.3f on %d slots) ..." % (tag, f, n))
            results[tag] = solve(tag)
    finally:
        shutil.copy(IONS + ".dsens_backup", IONS)
        shutil.copy(MATRIX + ".dsens_backup", MATRIX)
        os.remove(IONS + ".dsens_backup"); os.remove(MATRIX + ".dsens_backup")
        print("\n(restored the unperturbed table and matrix)")

    RM = {"Unstirred batch": "natural", "Stirred batch": "stirred",
          "Recirculating flow cell": "flow", "RDE 1600 rpm": "rde",
          "Rotating cylinder 3000 rpm": "rce", "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro"}
    print("\n%-9s %-14s %-14s" % ("case", "max |change|", "cells >5% off"))
    worst_rows = {}
    for tag, res in results.items():
        worst, n5 = 0.0, 0
        for k, v in res.items():
            b = base.get(k)
            if not b:
                continue
            d = abs(v - b) / b
            if d > 0.05:
                n5 += 1
            if d > worst:
                worst, worst_rows[tag] = d, k
        print("  %-9s %-14s %-14s" % (tag, "%.1f%%" % (100 * worst), "%d of %d" % (n5, len(res))))
    print("\nworst-affected cell per case:")
    for tag, k in worst_rows.items():
        print("  %-6s %s / %s" % (tag, k[0][:46], k[1]))

    print("\nheadline counts per case (threshold crossings are what matter):")
    for label, res in [("base", base)] + list(results.items()):
        per = {}
        for (rxn, rct), v in res.items():
            per.setdefault(RM.get(rct, rct), []).append(v)
        line = "  %-6s" % label
        for c in ("natural", "stirred", "flow", "anec", "micro", "rde", "rce"):
            vals = per.get(c, [])
            line += "  %s:%d/%d" % (c[:4], sum(1 for v in vals if v >= 25),
                                    sum(1 for v in vals if v >= 50))
        print(line)
    ## THE VERDICT. Until 2026-09-05 this gate printed "read the count lines" and exited 0, so the
    ## runner -- which believes a gate's own PASS/FAIL line and falls back to the exit code only
    ## when there is none -- could never see it fail. A gate that cannot fail is not a gate. The
    ## physics says the answer is exactly zero (a supporting ion carries no flux), so that is what
    ## is asserted: identical threshold counts in every architecture AND no cell moving by more
    ## than 1e-6 relative under x3 either way.
    import json as _json
    counts = {}
    for label, res in [("base", base)] + list(results.items()):
        per = {}
        for (rxn, rct), v in res.items():
            per.setdefault(RM.get(rct, rct), []).append(v)
        counts[label] = {c: [sum(1 for v in per.get(c, []) if v >= 25), sum(1 for v in per.get(c, []) if v >= 50)]
                         for c in ("natural", "stirred", "flow", "anec", "micro", "rde", "rce")}
    worst = {tag: max(abs(v - base[k]) / base[k] for k, v in res.items() if k in base and base[k])
             for tag, res in results.items()}
    same_counts = all(counts[t] == counts["base"] for t in results)
    small = all(w <= 1e-6 for w in worst.values())
    verdict = "PASS" if (same_counts and small) else "FAIL"
    out = {"note": "G-DSENS: every declared-default supporting-ion diffusivity perturbed together; "
                   "written by data/sensitivity_unsourced_D.py",
           "n_slots": n_uns, "n_pairs": len(pairs), "pairs": sorted(pairs),
           "factors": {t: f for t, f in FACTORS}, "max_rel_change": worst,
           "counts": counts, "counts_identical": same_counts, "verdict": verdict}
    _out = os.path.join(ROOT, "results", "unsourced_D_sensitivity.json")
    with open(_out, "w", encoding="utf8") as fh:
        _json.dump(out, fh, indent=2)
    print("\nwrote results/unsourced_D_sensitivity.json")
    if verdict == "PASS":
        print("G-DSENS: PASS -- %d declared-default supporting-ion diffusivities (%d ion/solvent pairs) "
              "perturbed x1/3 and x3 with the 350-cell layer re-solved: largest relative change %.1e, "
              "no threshold count moves" % (n_uns, len(pairs), max(worst.values())))
    else:
        print("G-DSENS: FAIL -- a supporting-ion diffusivity moved a published number (counts identical: %s; "
              "largest relative change %.3e). A supporting ion's D must not enter i_lim; something now "
              "feeds one into a reacting species." % (same_counts, max(worst.values())))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
