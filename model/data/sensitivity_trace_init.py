#!/usr/bin/env python3
"""G-TRACE -- perturb the trace initialisation of the electrogenerated form and re-solve the mediated matrix.

    /opt/anaconda3/bin/python3.12 data/sensitivity_trace_init.py                 # solves in scratch copies (~10 min)
    /opt/anaconda3/bin/python3.12 data/sensitivity_trace_init.py --from hi:D1,..;lo:D1,..   # reads finished copies

`tr(C) = C * 1e-5` seeds the oxidised mediator (and H+ in aprotic media) at a trace of bulk. The registry states the size
of that seed's effect; this moves it a full decade in both directions and re-solves every mediated row, each in its own
scratch copy (MED_ONLY), so the statement is measured. It writes results/trace_init_sensitivity.json, which
build_param_tables.py reads; the registry sentence was once typed from this script's printout and described a retired
eight-row, six-archetype matrix (chemistry audit, pass 4). Production files are never written.
"""
import csv, io, json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); JL = os.path.join(ROOT, "julia")
SRC = os.path.join(JL, "run_mediated.jl")
OUT = os.path.join(ROOT, "results", "trace_init_sensitivity.json")
SEEDS = {"hi": "1e-4", "lo": "1e-6"}


def labels():
    return re.findall(r'^\s*MedSpec\("([^"]+)"', io.open(SRC, encoding="utf-8").read(), flags=re.M)


def patched(val):
    s = io.open(SRC, encoding="utf-8").read()
    s2, n = re.subn(r'tr\(C\)\s*=\s*C\s*\*\s*[\d.e-]+', 'tr(C) = C * %s' % val, s)
    if n != 1:
        raise SystemExit("tr(C) definition not found (n=%d)" % n)
    return s2


def solve_one(args):
    tag, lab = args
    d = tempfile.mkdtemp(prefix="trace_%s_" % tag)
    for sub in ("julia", "data"):
        shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub),
                        ignore=shutil.ignore_patterns("*.bak*", "*.ksens", "*.zsens", "*.dsens"))
    io.open(os.path.join(d, "julia", "run_mediated.jl"), "w", encoding="utf-8").write(patched(SEEDS[tag]))
    rc = subprocess.call(["julia", "run_mediated.jl"], cwd=os.path.join(d, "julia"), env=dict(os.environ, MED_ONLY=lab),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc:
        raise SystemExit("seed %s, %s: the solve exited %d" % (tag, lab, rc))
    return tag, d


def read(dirs):
    out = {}
    for d in dirs:
        for x in csv.DictReader(io.open(os.path.join(d, "julia", "mediated_ec_matrix.csv"), encoding="utf-8")):
            out[x["reaction"] + "|" + x["reactor"]] = float(x["i_ec_mAcm2"])
    return out


def main():
    base = {x["reaction"] + "|" + x["reactor"]: float(x["i_ec_mAcm2"])
            for x in csv.DictReader(io.open(os.path.join(JL, "mediated_ec_matrix.csv"), encoding="utf-8"))}
    if "--from" in sys.argv:
        spec = sys.argv[sys.argv.index("--from") + 1]
        dirs = {t: v.split(",") for t, v in (part.split(":", 1) for part in spec.split(";"))}
    else:
        jobs = [(t, lab) for t in SEEDS for lab in labels()]
        with ThreadPoolExecutor(max_workers=min(12, len(jobs))) as ex:
            done = list(ex.map(solve_one, jobs))
        dirs = {t: [d for tt, d in done if tt == t] for t in SEEDS}
    res = {"seed_carried": "1e-5", "n_cells": len(base), "per_seed": {}}
    for t, val in SEEDS.items():
        p = read(dirs[t])
        if set(p) != set(base):
            raise SystemExit("seed %s: the re-solve covers %d cells, the matrix has %d" % (val, len(p), len(base)))
        diffs = [(k, base[k], p[k]) for k in base if base[k] != p[k]]
        res["per_seed"][val] = {
            "n_differ": len(diffs),
            "max_abs_mAcm2": max((abs(b - a) for _, a, b in diffs), default=0.0),
            "max_rel_pct": max((100 * abs(b / a - 1) for _, a, b in diffs), default=0.0),
            "counts": {str(thr): [sum(v >= thr for v in base.values()), sum(v >= thr for v in p.values())] for thr in (25, 50)}}
        r = res["per_seed"][val]
        print("tr = C x %s: %d of %d cells differ; largest change %.3g mA/cm2 (%.3g pct); >=25 %s, >=50 %s"
              % (val, r["n_differ"], len(base), r["max_abs_mAcm2"], r["max_rel_pct"], r["counts"]["25"], r["counts"]["50"]))
    moved = any(v["counts"][t][0] != v["counts"][t][1] for v in res["per_seed"].values() for t in ("25", "50"))
    res["counts_move"] = moved
    json.dump(res, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("G-TRACE: %s -- wrote %s" % ("FAIL (a count moves)" if moved else "PASS", os.path.relpath(OUT, ROOT)))
    sys.exit(1 if moved else 0)


if __name__ == "__main__":
    main()
