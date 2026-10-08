#!/usr/bin/env python3
"""G-SOLVSET -- two declared solver settings re-measured on the PRODUCTION path (slow tier, ~30 min).

Writes the two artifacts the registry's numerics rows read (Table S7k):

  results/negligible_c_sweep.json  NEGLIGIBLE_C (trust-region negligibility) swept 1e-6 ... 1e-16 on every architecture
                                   of three mediated rows: the bromination (whose anisole falls far below 1e-10 of bulk,
                                   so the rule acts), the Hofmann rearrangement and the ACT alcohol oxidation.
  results/cref_scale_sweep.json    the full mediated matrix re-solved with the residual reference WITHOUT the in-film
                                   maximum, c_ref = max(c_bulk, 0.01 c_max,bulk).

Every solve runs julia/run_mediated.jl in an ISOLATED COPY of julia/ (it truncates and rewrites its own CSV), so the
published matrix is never touched. The control is built in: at the production threshold 1e-10 the sweep must reproduce
the published matrix exactly, and a perturbed copy must actually carry the patched setting (checked by grep after the
patch; a patch that matches nothing aborts).

    cd Section4_Model && python data/solver_setting_sweeps.py            # both, then PASS/FAIL
    python data/solver_setting_sweeps.py --summarise-only [DIR]          # rebuild the JSONs from results/solvset_runs (or DIR)
"""
import csv, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
THRESH = ["1e-6", "1e-8", "1e-10", "1e-12", "1e-14", "1e-16"]
ROWS = ["Br- oxidation / electrophilic bromination", "Br-mediated Hofmann rearrangement",
        "ACT-mediated alcohol oxidation (flow, hectogram)"]
NEGC_OLD = "const NEGLIGIBLE_C = Ref(1e-10)"
NEGC_NEW = 'const NEGLIGIBLE_C = Ref(parse(Float64, get(ENV, "NEGC", "1e-10")))'
CREF_OLD = "max(p.sp[j].c_bulk, 0.01 * cscale, maximum(@view c[j, :]))"
CREF_NEW = "max(p.sp[j].c_bulk, 0.01 * cscale)"


def copy_tree(dst, patch_from, patch_to, n_expected):
    w = os.path.join(dst, "Section4_Model")
    os.makedirs(os.path.join(w, "data"), exist_ok=True)
    os.makedirs(os.path.join(w, "results"), exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "julia"), os.path.join(w, "julia"))
    for f in os.listdir(HERE):
        if f.endswith(".csv"):
            shutil.copy2(os.path.join(HERE, f), os.path.join(w, "data", f))
    p = os.path.join(w, "julia", "npp_ecprime.jl")
    s = open(p).read()
    if s.count(patch_from) != n_expected:
        raise SystemExit("patch target occurs %d times in npp_ecprime.jl, expected %d" % (s.count(patch_from), n_expected))
    open(p, "w").write(s.replace(patch_from, patch_to))
    return os.path.join(w, "julia")


def solve(jdir, env_extra, out_csv):
    env = dict(os.environ, **env_extra)
    r = subprocess.run(["julia", "run_mediated.jl"], cwd=jdir, env=env, capture_output=True, text=True)
    if r.returncode != 0 or "MATRIX DONE" not in r.stdout:
        raise SystemExit("run_mediated.jl failed in %s (%s): %s" % (jdir, env_extra, r.stderr[-400:]))
    shutil.copy2(os.path.join(jdir, "mediated_ec_matrix.csv"), out_csv)


def published():
    return {(r["reaction"], r["reactor"]): r for r in csv.DictReader(open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv")))}


def summarise(work):
    pub = published()
    cells, worst = {}, 0.0
    for t in THRESH:
        for i in range(len(ROWS)):
            for r in csv.DictReader(open(os.path.join(work, "negc_%s_%d.csv" % (t, i)))):
                cells.setdefault((r["reaction"], r["reactor"]), {})[t] = float(r["i_ec_mAcm2"])
    for k, d in cells.items():
        worst = max(worst, max(abs(v / float(pub[k]["i_ec_mAcm2"]) - 1) for v in d.values()))
    control = all(d["1e-10"] == float(pub[k]["i_ec_mAcm2"]) for k, d in cells.items())

    def csub(lim):
        m = re.search(r"c_sub/cb ([0-9.eE+-]+)", lim)
        return float(m.group(1)) if m else None
    below = sorted((k[0], k[1], csub(pub[k]["limiter"])) for k in cells
                   if csub(pub[k]["limiter"]) is not None and csub(pub[k]["limiter"]) < 1e-10)
    negc = {"note": "NEGLIGIBLE_C swept with julia/run_mediated.jl in isolated copies (data/solver_setting_sweeps.py)",
            "thresholds": [float(t) for t in THRESH], "rows": sorted({k[0] for k in cells}), "n_cells": len(cells),
            "max_rel_change_vs_published": worst, "control_1e-10_reproduces_published": control,
            "cells_with_a_species_below_1e-10_of_bulk": [{"reaction": a, "reactor": b, "c_sub_over_bulk": c} for a, b, c in below]}
    alt = {(r["reaction"], r["reactor"]): r for r in csv.DictReader(open(os.path.join(work, "cref.csv")))}
    if set(alt) != set(pub):
        raise SystemExit("the c_ref re-solve does not cover the published cells (%d vs %d)" % (len(alt), len(pub)))
    moved, same, tiny = [], 0, 0
    for k in pub:
        a, b = float(pub[k]["i_ec_mAcm2"]), float(alt[k]["i_ec_mAcm2"])
        if pub[k]["i_ec_mAcm2"] == alt[k]["i_ec_mAcm2"]:
            same += 1
        elif abs(b / a - 1) < 1e-9:
            tiny += 1
        else:
            moved.append({"reaction": k[0], "reactor": k[1], "published": a, "alternative": b, "rel_change": b / a - 1,
                          "published_limiter": pub[k]["limiter"], "alternative_limiter": alt[k]["limiter"]})
    # pass 18: the md5 is the one recorded WHEN THE SOLVES RAN (matrix_md5.txt in the run directory); stamping the
    # current matrix at summarise time would certify stale runs against a matrix they never saw
    rec = os.path.join(work, "matrix_md5.txt")
    if not os.path.exists(rec):
        raise SystemExit("%s has no matrix_md5.txt: the runs cannot be tied to a matrix" % work)
    mmd5 = open(rec).read().strip()
    if mmd5 != hashlib.md5(open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"), "rb").read()).hexdigest():
        raise SystemExit("the runs in %s were solved against a different mediated matrix; re-run without --summarise-only" % work)
    negc["matrix_md5"] = mmd5      # the registry refuses to build on these once the matrix moves (pass 17)
    # pass 18: the rule switched OFF (threshold 0) must move something, or the sweep could not tell an immaterial setting
    # from an inert one
    offr = {(r["reaction"], r["reactor"]): r for r in csv.DictReader(open(os.path.join(work, "negc_0_0.csv")))}
    off = {k: float(r["i_ec_mAcm2"]) for k, r in offr.items()}
    negc["rule_off"] = sorted(({"reaction": k[0], "reactor": k[1], "rel_change": v / float(pub[k]["i_ec_mAcm2"]) - 1,
                                "limiter": offr[k]["limiter"], "flag": offr[k]["flag"]}
                               for k, v in off.items()
                               if not (abs(v / float(pub[k]["i_ec_mAcm2"]) - 1) <= 1e-6)),   # a NaN counts as moved
                              key=lambda c: c["rel_change"])
    walk = []
    log = open(os.path.join(work, "excell_alt.log")).read()
    if not re.search(r"reachable-film check, delta = \d+ um: i = .*= 2\.00\d+x Fick", log):
        raise SystemExit("excell_alt.log: the reachable-film check did not reproduce 2.00x Fick")
    for m in re.finditer(r"delta-continuation to\s+(\d+) um: i =\s+([0-9.]+) mA/cm2 = ([0-9.]+)x Fick \((\d+)% of the "
                         r"analytic limit\).*\[(converged|branch ends)\]", log):
        walk.append({"delta_um": int(m.group(1)), "i_mAcm2": float(m.group(2)), "ratio_fick": float(m.group(3)),
                     "pct_of_limit": int(m.group(4)), "converged": m.group(5) == "converged"})
    if [w["delta_um"] for w in walk] != [50, 100, 200]:
        raise SystemExit("excell_alt.log: the delta-continuation walk is not 50/100/200 um: %r" % walk)
    cref = {"matrix_md5": mmd5, "excell_walk_alt_scale": walk, "note": "julia/run_mediated.jl re-solved in an isolated copy with c_ref = max(c_bulk, 0.01 c_max_bulk), no "
                    "in-film maximum (data/solver_setting_sweeps.py)",
            "n_cells": len(pub), "bit_identical": same, "within_1e-9": tiny, "moved": moved}
    return negc, cref


def main():
    RUNS = os.path.join(ROOT, "results", "solvset_runs")   # the per-solve CSVs are kept in the tree (a reboot wipes /tmp)
    if "--summarise-only" in sys.argv:
        i = sys.argv.index("--summarise-only")
        work = sys.argv[i + 1] if len(sys.argv) > i + 1 else RUNS
    else:
        work = tempfile.mkdtemp(prefix="solvset_")
        jobs = []
        for t in THRESH:
            jd = copy_tree(os.path.join(work, "negc_" + t), NEGC_OLD, NEGC_NEW, 1)
            jobs.append((jd, t))
        cj = copy_tree(os.path.join(work, "cref_tree"), CREF_OLD, CREF_NEW, 2)
        j0 = copy_tree(os.path.join(work, "negc_0"), NEGC_OLD, NEGC_NEW, 1)   # its OWN copy: run_mediated.jl writes @__DIR__
        open(os.path.join(work, "matrix_md5.txt"), "w").write(
            hashlib.md5(open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"), "rb").read()).hexdigest())

        def run_thr(job):
            jd, t = job
            for i, row in enumerate(ROWS):
                solve(jd, {"NEGC": t, "MED_ONLY": row}, os.path.join(work, "negc_%s_%d.csv" % (t, i)))
        with ThreadPoolExecutor(max_workers=7) as ex:
            def cref_then_excell():
                solve(cj, {}, os.path.join(work, "cref.csv"))
                # run_excell.jl under the alternative scale: its delta-continuation walk is what the c_ref row quotes.
                # The script then refuses to publish (its k-sweep cannot converge without the in-film term), so its
                # exit status is not the verdict; the walk lines it prints before that are.
                r = subprocess.run(["julia", "run_excell.jl"], cwd=cj, capture_output=True, text=True)
                open(os.path.join(work, "excell_alt.log"), "w").write(r.stdout + r.stderr)
            futs = [ex.submit(run_thr, j) for j in jobs] + [ex.submit(cref_then_excell)]
            futs.append(ex.submit(solve, j0, {"NEGC": "0", "MED_ONLY": ROWS[0]}, os.path.join(work, "negc_0_0.csv")))
            for f in futs:
                f.result()
        os.makedirs(RUNS, exist_ok=True)
        for f in os.listdir(work):
            if f.endswith(".csv") or f in ("matrix_md5.txt", "excell_alt.log"):
                shutil.copy2(os.path.join(work, f), os.path.join(RUNS, f))
    negc, cref = summarise(work)
    for name, obj in (("negligible_c_sweep.json", negc), ("cref_scale_sweep.json", cref)):
        txt = json.dumps(obj, indent=1)
        open(os.path.join(ROOT, "results", name), "w").write(txt)
    ok = (negc["control_1e-10_reproduces_published"] and negc["max_rel_change_vs_published"] == 0.0
          and len(negc["rule_off"]) > 0)
    print("NEGLIGIBLE_C: %d cells x %d thresholds, max change %.2e, control %s; c_ref: %d bit-identical, %d within 1e-9, "
          "%d moved %s" % (negc["n_cells"], len(THRESH), negc["max_rel_change_vs_published"],
                           negc["control_1e-10_reproduces_published"], cref["bit_identical"], cref["within_1e-9"],
                           len(cref["moved"]), [(m["reactor"], round(100 * m["rel_change"], 2)) for m in cref["moved"]]))
    print("G-SOLVSET: %s" % ("PASS -- the NEGLIGIBLE_C control reproduces the published matrix and no threshold moves a cell"
                             if ok else "FAIL -- the threshold sweep moved a cell, its control did not reproduce, or switching the rule off moved nothing (inert)"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
