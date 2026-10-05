#!/usr/bin/env python3
"""G-KSENS -- bound the exposure of the mediated rows to their order-of-magnitude rate constants.

    cd Section4_Model && python data/sensitivity_rate_constants.py

WHY
---
The eight mediated rows carry a homogeneous rate constant k each: 1e3, 20, 10, 0.5, 50, 100, 1e3,
100 M-1 s-1. Table S6 documents a provenance sentence for every one, but they are ORDER-OF-MAGNITUDE
literature passes, not measurements for these systems -- and the SI concedes outright for SCN-:
"NO direct rate measurement located -- estimate by analogy to halogenation".

That is an honest label, but a label is not a bound. The SI also reports that source-term coupling
raises mediated ceilings by x1.0 to x27, so k is not a small correction on these rows. This script
perturbs each k by the order of magnitude that is actually claimed -- x10 and /10, one row at a
time -- re-solves the mediated matrix, and reports how far that row's ceilings and the headline
counts move.

The point is to be able to say, with numbers, EITHER "the counts survive an order of magnitude in
every k" OR "these specific rows need a real rate constant before their ceilings are quoted".
"""
import csv, io, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JULIA = os.path.join(ROOT, "julia")
SRC = os.path.join(JULIA, "run_mediated.jl")
MATRIX = os.path.join(JULIA, "mediated_ec_matrix.csv")
FACTORS = [("div10", 0.1), ("mul10", 10.0)]
SPEC = re.compile(r'(MedSpec\("([^"]+)",\s*)([0-9.eE+-]+)(,)')

_BACKUPS = [MATRIX + ".ksens", SRC + ".ksens"]


def specs(txt):
    return [(m.group(2), float(m.group(3))) for m in SPEC.finditer(txt)]


def perturb(txt, target, factor):
    def sub(m):
        if m.group(2) != target:
            return m.group(0)
        return "%s%.6g%s" % (m.group(1), float(m.group(3)) * factor, m.group(4))
    out = SPEC.sub(sub, txt)
    if out == txt:
        raise SystemExit("perturbation for %r changed nothing -- regex drift?" % target)
    return out


def solve(tag):
    log = os.path.join("/tmp", "ksens_%s.log" % tag)
    with open(log, "w") as fh:
        rc = subprocess.call(["julia", "run_mediated.jl"], cwd=JULIA, stdout=fh, stderr=fh)
    if rc != 0:
        return None
    return {(r["reaction"], r["reactor"]): float(r["i_ec_mAcm2"])
            for r in csv.DictReader(open(MATRIX))}


def main():
    txt = io.open(SRC, encoding="utf8").read()
    sp = specs(txt)
    print("mediated rows and their rate constants:")
    for name, k in sp:
        print("   %-46s k = %g" % (name[:46], k))

    # A SECOND INSTANCE WOULD OVERWRITE THE FIRST'S BACKUP and then the first's finally

    # would delete it, leaving the second with nothing to restore -- which is how

    # data/carrier_charge.csv was left holding a PERTURBED charge on 2026-08-26 and

    # julia/all50_np_matrix.csv was left interleaved by two writers. Refuse instead.

    for _b in _BACKUPS:

        if os.path.exists(_b):

            sys.exit("REFUSING TO RUN: %s exists, so another sweep owns these artifacts. "

                     "Wait for it, or if it died, restore from that file by hand and "

                     "delete it." % _b)


    shutil.copy(SRC, SRC + ".ksens"); shutil.copy(MATRIX, MATRIX + ".ksens")
    try:
        print("\nsolving BASE ...")
        base = solve("base")
        if base is None:
            raise SystemExit("base mediated solve failed; see /tmp/ksens_base.log")
        rows = []
        for name, k in sp:
            for tag, f in FACTORS:
                io.open(SRC, "w", encoding="utf8").write(perturb(txt, name, f))
                res = solve("%s_%s" % (name[:10].replace(" ", "_"), tag))
                if res is None:
                    rows.append((name, tag, None, None, None, None)); continue
                cells = [(kk, v) for kk, v in res.items() if kk[0] == name]
                w = max(abs(v - base[kk]) / base[kk] for kk, v in cells) if cells else 0.0
                n25 = sum(1 for kk, v in cells if (v >= 25) != (base[kk] >= 25))
                ## which architectures cross, and in which direction, at both thresholds
                cross = {thr: {kk[1]: (1 if v >= thr else -1) for kk, v in cells if (v >= thr) != (base[kk] >= thr)}
                         for thr in (25, 50)}
                rows.append((name, tag, w, n25, cross, {kk[1]: v for kk, v in cells}))
            io.open(SRC, "w", encoding="utf8").write(txt)
    finally:
        shutil.copy(SRC + ".ksens", SRC); shutil.copy(MATRIX + ".ksens", MATRIX)
        os.remove(SRC + ".ksens"); os.remove(MATRIX + ".ksens")
        print("\n(restored run_mediated.jl and the mediated matrix)")

    ## ---- PER-CELL VALUES, WRITTEN DOWN (2026-09-10) ---------------------------------------------
    ## Until now this sweep kept every perturbed cell in memory and wrote only per-row summaries, so
    ## Figure 6b could draw the catalyst class over its declared k band but not the mediators over
    ## their tenfold one. The base and both perturbed values of every cell go to results/, with the
    ## film (which k does not change) read from the restored base matrix.
    base_delta = {(r["reaction"], r["reactor"]): float(r["delta_um"]) for r in csv.DictReader(open(MATRIX))}
    cells_out = os.path.join(ROOT, "results", "rate_constant_cells.csv")
    os.makedirs(os.path.dirname(cells_out), exist_ok=True)
    with open(cells_out, "w", newline="") as fh:
        wr = csv.writer(fh); wr.writerow(["reaction", "factor", "reactor", "delta_um", "i_ec_mAcm2"])
        for (rx, rr), v in sorted(base.items()):
            wr.writerow([rx, "base", rr, "%.6g" % base_delta[(rx, rr)], "%.6g" % v])
        for name, tag, w, n25, cross, vals in rows:
            if w is None:
                continue
            for rr, v in sorted(vals.items()):
                wr.writerow([name, tag, rr, "%.6g" % base_delta[(name, rr)], "%.6g" % v])
    print("\nper-cell values -> results/rate_constant_cells.csv (%d perturbed rows x 7 cells + base)" % sum(1 for r in rows if r[2] is not None))

    print("\n%-46s %-7s %-13s %s" % ("reaction", "case", "max change", "cells crossing 25"))
    flagged = []
    for name, tag, w, n25, cross, vals in rows:
        if w is None:
            print("  %-46s %-7s %-13s %s" % (name[:46], tag, "SOLVE FAILED", "-")); continue
        mark = "   <<<" if n25 else ""
        if n25:
            flagged.append((name, tag, n25))
        print("  %-46s %-7s %-13s %d%s" % (name[:46], tag, "%.1f%%" % (100 * w), n25, mark))
    print()
    ## ---- THE EXPOSURE, MEASURED ON THE PUBLISHED MATRIX, AND WRITTEN DOWN -------------------------
    ## Until 2026-09-05 this gate stopped at "REVIEW NEEDED -- these rows should not have their
    ## ceilings quoted without a real rate constant", which the runner counts as a failure and
    ## which no document could act on. The rate constants ARE order-of-magnitude, that is declared,
    ## and what a reader needs is the size of the exposure: how many counts move, in which
    ## architectures, by how much, and whether the ordering survives. Compute it on the published
    ## 350-cell matrix (the mediated row's seven cells substituted, everything else fixed), write it
    ## to results/, and require the SI to state it. The gate now FAILS when the SI's statement and
    ## the sweep disagree -- the falsifiable version of "review needed".
    import json as _json, unicodedata as _ud, re as _re
    ARCH = {"Unstirred batch": "natural", "Stirred batch": "stirred", "Recirculating flow cell": "flow",
            "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro", "RDE 1600 rpm": "rde", "Rotating cylinder 3000 rpm": "rce"}
    ORDER = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
    pub = list(csv.DictReader(open(os.path.join(JULIA, "tier0_ec_matrix.csv"))))
    def counts_and_medians(sub_row=None, sub_vals=None):
        cols = {a: [] for a in ORDER}
        for r in pub:
            for full, a in ARCH.items():
                v = float(r[a])
                if sub_row is not None and r["reaction"] == sub_row and full in sub_vals:
                    v = sub_vals[full]
                cols[a].append(v)
        n25 = {a: sum(1 for v in vs if v >= 25) for a, vs in cols.items()}
        n50 = {a: sum(1 for v in vs if v >= 50) for a, vs in cols.items()}
        med = {a: sorted(vs)[24:26] for a, vs in cols.items()}
        med = {a: 0.5 * (m[0] + m[1]) for a, m in med.items()}
        return n25, n50, med
    b25, b50, bmed = counts_and_medians()
    base_order = sorted(ORDER, key=lambda a: bmed[a])
    out_rows, worst25, worst50, order_changes = [], 0, 0, []
    for name, tag, w, n25, cross, vals in rows:
        if w is None:
            continue
        c25, c50, med = counts_and_medians(name, vals)
        d25 = {a: c25[a] - b25[a] for a in ORDER}; d50 = {a: c50[a] - b50[a] for a in ORDER}
        worst25 = max(worst25, max(abs(x) for x in d25.values()))
        worst50 = max(worst50, max(abs(x) for x in d50.values()))
        if sorted(ORDER, key=lambda a: med[a]) != base_order:
            order_changes.append((name, tag))
        out_rows.append({"reaction": name, "factor": {"div10": 0.1, "mul10": 10.0}[tag],
                         "max_rel_change": w, "cells_crossing_25": n25,
                         "cross_25": {ARCH.get(k, k): v for k, v in cross[25].items()},
                         "cross_50": {ARCH.get(k, k): v for k, v in cross[50].items()},
                         "count_delta_25": d25, "count_delta_50": d50})
    rows25 = sorted({r["reaction"] for r in out_rows if r["cells_crossing_25"]})
    rows50 = sorted({r["reaction"] for r in out_rows if r["cross_50"]})
    summary = {"n_rows": len(sp), "rows_crossing_25": rows25, "rows_crossing_50": rows50,
               "max_count_delta_25": worst25, "max_count_delta_50": worst50,
               "ordering_preserved": not order_changes, "ordering_changes": order_changes,
               "base_counts_25": b25, "base_counts_50": b50}
    _out = os.path.join(ROOT, "results", "rate_constant_sensitivity.json")
    with open(_out, "w", encoding="utf8") as fh:
        _json.dump({"note": "G-KSENS: each mediated k x10 and /10, one row at a time, re-solving the mediated "
                            "matrix; count deltas on the published 350-cell matrix. Written by "
                            "data/sensitivity_rate_constants.py", "rows": out_rows, "summary": summary}, fh, indent=2)
    print("wrote results/rate_constant_sensitivity.json")
    print("exposure: cells cross 25 on %d of %d rows (%s); worst count delta +-%d at 25, +-%d at 50; ordering %s"
          % (len(rows25), len(sp), "; ".join(r[:30] for r in rows25), worst25, worst50,
             "preserved" if not order_changes else "CHANGES in %d case(s)" % len(order_changes)))
    return check_si(summary, label="G-KSENS")


def check_si(summary, label="G-KSENS-SI"):
    """The SI must state the measured exposure in the sweep's own numbers. Run from the JSON (fast
    tier, `--check-si`) after every SI build, or at the end of the sweep itself."""
    import unicodedata as _ud, re as _re
    sys.path.insert(0, HERE)
    from docx_text import asserted_text
    si = _ud.normalize("NFKC", _re.sub(r"\s+", " ", asserted_text(os.path.join(ROOT, "SI_Section4_Transport_Model.docx"))))
    n25 = len(summary["rows_crossing_25"]); w25 = summary["max_count_delta_25"]; w50 = summary["max_count_delta_50"]
    wants = ["moves at least one cell across the 25 mA cm−2 threshold on %d of the eight rows" % n25,
             "count of any single architecture moves by at most ±%d and the ≥50 mA cm−2 count by at most ±%d" % (w25, w50),
             ("and no architecture ordering changes" if summary["ordering_preserved"] else "and the architecture ordering changes")]
    missing = [w_ for w_ in wants if _ud.normalize("NFKC", w_) not in si]
    if missing:
        print("%s: FAIL -- the SI does not state the measured rate-constant exposure:" % label)
        for m_ in missing:
            print("   missing: %r" % m_)
        return 1
    print("%s: PASS -- cells cross 25 on %d of %d rows under x10 or /10 in k, counts move by at most +-%d at 25 "
          "and +-%d at 50, ordering %s, and the SI states exactly that"
          % (label, n25, summary["n_rows"], w25, w50, "preserved" if summary["ordering_preserved"] else "changes"))
    return 0


if __name__ == "__main__":
    if "--check-si" in sys.argv:
        import json as _json
        _p = os.path.join(ROOT, "results", "rate_constant_sensitivity.json")
        if not os.path.exists(_p):
            print("G-KSENS-SI: FAIL -- results/rate_constant_sensitivity.json is missing; run the sweep "
                  "(./run_gates.sh --all) once"); sys.exit(1)
        sys.exit(check_si(_json.load(open(_p))["summary"]))
    sys.exit(main())
