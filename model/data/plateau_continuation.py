#!/usr/bin/env python3
"""G-PLATEAU: is a concentration-control plateau that stops short of full depletion a limit?

`solve_ilim_ec_ccontrol` ends a walk when the current stops responding to further depletion of
the electroactive form (|d ln i / d ln c| < 2e-3). For most mediated cells that happens with the
reduced mediator at a few tenths of a percent of bulk. A cell limited by its SUBSTRATE flattens
earlier -- the thioether rows in the two batch films stop with the mediator near 7-9 % of bulk --
and a reader is entitled to ask whether the walk stopped on a shoulder.

This script answers by measurement. Every mediated cell whose recorded plateau sits above
THRESH of bulk is re-solved in an isolated copy of julia/ with the plateau stop switched off, so
the walk runs on to the 1e-3 collapse criterion, and the current there is compared with the
published one. Nothing in the tree is written except results/plateau_continuation.json.

    python data/plateau_continuation.py                      # solve + verdict (a few minutes)
    python data/plateau_continuation.py --check              # fast: stored result vs the matrix
    python data/plateau_continuation.py --negative-control   # the verdict must be able to fail
"""
import csv, glob, io, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JULIA = os.path.join(ROOT, "julia")
MATRIX = os.path.join(JULIA, "mediated_ec_matrix.csv")
OUT = os.path.join(ROOT, "results", "plateau_continuation.json")
THRESH = 0.02        # plateaus above 2 % of bulk are the ones worth walking on
TOL = 0.01           # a plateau is a limit if walking to 1e-3 moves the current by < 1 %
CALL = "ic, limc, uc, frac, br = solve_ilim_ec_ccontrol(p; u0 = u_safe, i0 = i_safe)"


def shallow_cells():
    out = []
    for r in csv.DictReader(open(MATRIX)):
        m = re.search(r"c_red/cb ([0-9.eE+-]+)", r["limiter"])
        if m and float(m.group(1)) > THRESH:
            out.append((r["reaction"], r["reactor"], float(m.group(1)), float(r["i_ec_mAcm2"])))
    return out


def solve_to_collapse(row):
    d = tempfile.mkdtemp(prefix="plateau_")
    try:
        for f in glob.glob(os.path.join(JULIA, "*.jl")):
            shutil.copy(f, d)
        p = os.path.join(d, "run_mediated.jl")
        t = io.open(p, encoding="utf8").read()
        if t.count(CALL) != 1:
            raise SystemExit("run_mediated.jl no longer carries the production c-control call exactly once")
        io.open(p, "w", encoding="utf8").write(t.replace(CALL, CALL[:-1] + ", plateau_tol = 0.0)"))
        log = os.path.join(tempfile.gettempdir(), "plateau_continuation.log")
        with open(log, "w") as fh:
            rc = subprocess.call(["julia", "run_mediated.jl"], cwd=d, stdout=fh, stderr=fh,
                                 env=dict(os.environ, MED_ONLY=row))
        if rc != 0:
            raise SystemExit("the continuation solve of %r failed; see %s" % (row, log))
        return {r["reactor"]: (float(r["i_ec_mAcm2"]), r["limiter"])
                for r in csv.DictReader(open(os.path.join(d, "mediated_ec_matrix.csv")))}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def verdict(res, cells, negative=False):
    fails = []
    want = {(c[0], c[1]) for c in cells}
    have = {(c["reaction"], c["reactor"]) for c in res["cells"]}
    if want != have:
        fails.append("stored cells %s do not match the matrix's shallow plateaus %s" % (sorted(have), sorted(want)))
    pub = {(c[0], c[1]): c[3] for c in cells}
    for c in res["cells"]:
        k = (c["reaction"], c["reactor"])
        if k in pub and abs(c["i_published"] - pub[k]) > 1e-6 * max(1.0, pub[k]):
            fails.append("%s / %s: stored published current %.4f is not the matrix's %.4f"
                         % (k[0], k[1], c["i_published"], pub[k]))
        rel = c["rel_change"] * (40.0 if negative else 1.0)
        if not c["reached_collapse"]:
            fails.append("%s / %s: the continued walk did not reach the 1e-3 criterion" % k)
        if abs(rel) > TOL:
            fails.append("%s / %s: walking on to 1e-3 moves the current by %+.2f %%" % (k[0], k[1], 100 * rel))
    return fails


def main():
    cells = shallow_cells()
    if "--check" in sys.argv or "--negative-control" in sys.argv:
        res = json.load(open(OUT))
        fails = verdict(res, cells, negative="--negative-control" in sys.argv)
        if "--negative-control" in sys.argv:
            print("G-PLATEAU control: %s" % ("GOOD" if fails else "BAD -- a 40x larger movement did not fire"))
            sys.exit(0 if fails else 1)
    else:
        rows = sorted({c[0] for c in cells})
        res = {"threshold_c_red_over_bulk": THRESH, "tolerance": TOL, "cells": []}
        for row in rows:
            got = solve_to_collapse(row)
            for (rx, reactor, frac, i_pub) in cells:
                if rx != row:
                    continue
                i_c, lim = got[reactor]
                res["cells"].append({"reaction": rx, "reactor": reactor, "c_red_over_bulk_at_plateau": frac,
                                     "i_published": i_pub, "i_at_collapse": i_c,
                                     "rel_change": i_c / i_pub - 1.0,
                                     "reached_collapse": lim.startswith("collapse")})
        res["n_cells"] = len(res["cells"])
        res["max_abs_rel_change"] = max([abs(c["rel_change"]) for c in res["cells"]] or [0.0])
        res["max_c_red_over_bulk"] = max([c["c_red_over_bulk_at_plateau"] for c in res["cells"]] or [0.0])
        json.dump(res, open(OUT, "w"), indent=1)
        fails = verdict(res, cells)
    for c in res["cells"]:
        print("   %-40s %-26s plateau at %.1f %% of bulk: %.2f -> %.2f mA cm-2 at collapse (%+.2f %%)"
              % (c["reaction"][:40], c["reactor"][:26], 100 * c["c_red_over_bulk_at_plateau"],
                 c["i_published"], c["i_at_collapse"], 100 * c["rel_change"]))
    for f in fails:
        print("   FAIL: " + f)
    print("G-PLATEAU: %s -- %d cell(s) plateau above %.0f %% of bulk; walking each on to 1e-3 moves the "
          "current by at most %.2f %%" % ("FAIL" if fails else "PASS", len(res["cells"]), 100 * THRESH,
                                         100 * res.get("max_abs_rel_change", 0.0)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
