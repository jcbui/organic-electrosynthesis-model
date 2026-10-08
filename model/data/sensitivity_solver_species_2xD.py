#!/usr/bin/env python3
"""G-SPEC2X -- the solver-species diffusivities that are not carriers' own Table S2 values, doubled together.

The mediated EC' solve carries species whose diffusivities are declared rather than measured in their medium: perchlorate
(a supporting anion), thiocyanate, bromide and bromine. Table S7d states what doubling all four together does to the
published matrix. That sentence was typed in 2026-08 against an eight-row, six-archetype matrix and was never re-run when
the matrix grew to twelve mediated rows and seven archetypes (chemistry audit, pass 4); this script re-runs it and writes
results/solver_species_2xD.json, which build_param_tables.py reads.

    python data/sensitivity_solver_species_2xD.py                 # solves the affected rows in scratch copies (~5 min)
    python data/sensitivity_solver_species_2xD.py --from D1,D2,..  # reads mediated_ec_matrix.csv from finished copies

What is doubled, in a scratch copy of julia/run_mediated.jl only: the D of every S("ClO4-"|"SCN-"|"Br-"|"Br2") species,
and the MedSpec mediator diffusivity of the rows whose mediator is bromide or thiocyanate. Rows that carry none of these
are not re-solved, since nothing in them changes. The published matrix is never written.

SECOND GROUP, the homogeneous partners (--group homog):

    python data/sensitivity_solver_species_2xD.py --group homog   # ~5 min; writes the key "homogeneous_partners"

B(OH)4- and B(OH)3 (the borate buffer of the HMF -> FDCA spec) and H+ in the aryl-thiocyanation spec (AcOH/HCOOH) take
no electrons at the electrode (s = 0) but are consumed or released by the homogeneous step (nu != 0), so their
diffusivities do not cancel. Each is doubled in its own spec, the two specs are re-solved in scratch copies exactly as
the first group, and an UNPERTURBED solve of each spec is run beside them as a control: the effect is reported against
the published matrix only when the control reproduces it. The first group's keys are left exactly as they are; the
second group writes only its own key, and a run of the first group keeps it.
"""
import csv, io, json, os, re, shutil, statistics, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "solver_species_2xD.json")
SPECIES = ("ClO4-", "SCN-", "Br-", "Br2")
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
REACTOR = {"Unstirred batch": "natural", "Stirred batch": "stirred", "Recirculating flow cell": "flow",
           "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro", "RDE 1600 rpm": "rde",
           "Rotating cylinder 3000 rpm": "rce"}
# The homogeneous partners: species -> the MedSpec label it is doubled in (None = every spec that carries it).
HOMOG = {"B(OH)4-": None, "B(OH)3": None, "H+": "Aryl thiocyanation (NH4SCN)"}
HOMOG_KEY = "homogeneous_partners"


def affected_rows(src):
    """MedSpec labels whose block names one of the doubled species, and those whose mediator is one of them."""
    rows, med_is, lab = [], set(), None
    for l in src.split("\n"):
        m = re.match(r'\s*MedSpec\("([^"]+)"', l)
        if m:
            lab = m.group(1)
        if lab and re.search(r'S\("(?:%s)"' % "|".join(re.escape(s) for s in SPECIES), l):
            if lab not in rows:
                rows.append(lab)
            mm = re.search(r'S\("([^"]+)",\s*[-+0-9.]+,\s*[0-9.e-]+,\s*[0-9.e+()tr]+,\s*-1\.0', l)
            if mm and mm.group(1) in ("Br-", "SCN-"):
                med_is.add(lab)
    return rows, med_is


def patch(src):
    rows, med_is = affected_rows(src)
    L, n = src.split("\n"), 0
    pat = re.compile(r'(S\("(?:%s)",\s*[-+0-9.]+,\s*)([0-9.]+e-?[0-9]+)' % "|".join(re.escape(s) for s in SPECIES))
    for i, l in enumerate(L):
        m = pat.search(l)
        if m:
            L[i] = l[:m.start(2)] + "%.6g" % (2 * float(m.group(2))) + l[m.end(2):]; n += 1
        m = re.match(r'(\s*MedSpec\("([^"]+)",\s*[^,]+,\s*[^,]+,\s*)([0-9.]+e-?[0-9]+)', L[i])
        if m and m.group(2) in med_is:
            L[i] = L[i][:m.start(3)] + "%.6g" % (2 * float(m.group(3))) + L[i][m.end(3):]; n += 1
    return "\n".join(L), rows, n


def solve():
    src = io.open(os.path.join(ROOT, "julia", "run_mediated.jl"), encoding="utf-8").read()
    new, rows, n = patch(src)

    def one(lab):
        d = tempfile.mkdtemp(prefix="spec2x_")
        for sub in ("julia", "data"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub),
                            ignore=shutil.ignore_patterns("*.bak*", "*.ksens", "*.zsens", "*.dsens"))
        io.open(os.path.join(d, "julia", "run_mediated.jl"), "w", encoding="utf-8").write(new)
        rc = subprocess.call(["julia", "run_mediated.jl"], cwd=os.path.join(d, "julia"),
                             env=dict(os.environ, MED_ONLY=lab), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if rc:
            raise SystemExit("the doubled solve of %s exited %d" % (lab, rc))
        return d
    with ThreadPoolExecutor(max_workers=len(rows)) as ex:
        return list(ex.map(one, rows)), rows, n


def patch_homog(src):
    """Double the D of each homogeneous partner inside the spec(s) HOMOG names. Each doubled species must be an
    electrode spectator (s = 0) that the homogeneous step consumes or releases (nu != 0) -- the property that makes
    'its D cancels' false -- or the patch refuses."""
    L, lab, done = src.split("\n"), None, []
    pat = re.compile(r'(\s*S\("([^"]+)",\s*[-+0-9.]+,\s*)([0-9.]+e-?[0-9]+)(,\s*[^,]+,\s*)([-+0-9.]+)(,\s*)([-+0-9./]+)')
    for i, l in enumerate(L):
        m = re.match(r'\s*MedSpec\("([^"]+)"', l)
        if m:
            lab = m.group(1)
        m = pat.match(l)
        if not (m and lab and m.group(2) in HOMOG):
            continue
        if HOMOG[m.group(2)] not in (None, lab):
            continue
        s_e, nu = float(m.group(5)), eval(m.group(7))
        if s_e != 0.0 or nu == 0.0:
            raise SystemExit("%s in %s is not a homogeneous partner (s = %g, nu = %g)" % (m.group(2), lab, s_e, nu))
        L[i] = l[:m.start(3)] + "%.6g" % (2 * float(m.group(3))) + l[m.end(3):]
        done.append({"spec": lab, "species": m.group(2), "D": float(m.group(3)), "s": s_e, "nu": nu})
    for sp, lab_req in HOMOG.items():
        if not any(d["species"] == sp and (lab_req is None or d["spec"] == lab_req) for d in done):
            raise SystemExit("homogeneous partner %s (%s) was not found in run_mediated.jl" % (sp, lab_req or "any spec"))
    rows = []
    for d in done:
        if d["spec"] not in rows:
            rows.append(d["spec"])
    return "\n".join(L), rows, done


def _solve_copy(src_text, lab, tag):
    d = tempfile.mkdtemp(prefix="spec2x_%s_" % tag)
    for sub in ("julia", "data"):
        shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub),
                        ignore=shutil.ignore_patterns("*.bak*", "*.ksens", "*.zsens", "*.dsens"))
    io.open(os.path.join(d, "julia", "run_mediated.jl"), "w", encoding="utf-8").write(src_text)
    rc = subprocess.call(["julia", "run_mediated.jl"], cwd=os.path.join(d, "julia"),
                         env=dict(os.environ, MED_ONLY=lab), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc:
        raise SystemExit("the %s solve of %s exited %d (%s)" % (tag, lab, rc, d))
    return d


def _read_cells(d):
    out = {}
    for r in csv.DictReader(io.open(os.path.join(d, "julia", "mediated_ec_matrix.csv"), encoding="utf-8")):
        out[(r["reaction"], REACTOR[r["reactor"]])] = float(r["i_ec_mAcm2"])
    return out


def main_homog():
    src = io.open(os.path.join(ROOT, "julia", "run_mediated.jl"), encoding="utf-8").read()
    new, rows, done = patch_homog(src)
    if "--from" in sys.argv:                      # --from <doubled dirs>;<control dirs>, comma-separated in row order
        a, b = sys.argv[sys.argv.index("--from") + 1].split(";")
        ddirs, cdirs = a.split(","), b.split(",")
    else:
        jobs = [(new, lab, "x2") for lab in rows] + [(src, lab, "ctl") for lab in rows]
        with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
            dirs = list(ex.map(lambda j: _solve_copy(*j), jobs))
        ddirs, cdirs = dirs[:len(rows)], dirs[len(rows):]
    dbl, ctl = {}, {}
    for d in ddirs:
        dbl.update(_read_cells(d))
    for d in cdirs:
        ctl.update(_read_cells(d))
    if sorted({k[0] for k in dbl}) != sorted(rows) or sorted({k[0] for k in ctl}) != sorted(rows):
        raise SystemExit("the solves cover %r / %r, the partner rows are %r"
                         % (sorted({k[0] for k in dbl}), sorted({k[0] for k in ctl}), sorted(rows)))
    mat = list(csv.DictReader(io.open(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"), encoding="utf-8")))
    # The control is held against the solver's own full-precision output (tier0_ec_matrix.csv rounds to four
    # decimals), and the effect of the doubling is read against the control.
    full = {}
    for r in csv.DictReader(io.open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"), encoding="utf-8")):
        full[(r["reaction"], REACTOR[r["reactor"]])] = float(r["i_ec_mAcm2"])
    ctl_dev = max(abs(ctl[k] / full[k] - 1) for k in ctl)
    if ctl_dev > 1e-9:
        raise SystemExit("the unperturbed control does not reproduce julia/mediated_ec_matrix.csv (max deviation %.3g); "
                         "the doubled solve cannot be read against it" % ctl_dev)
    per_row = {}
    for lab in rows:
        ch = [100 * (dbl[(lab, a)] / ctl[(lab, a)] - 1) for a in ARCH]
        per_row[lab] = {"change_pct": {a: round(c, 3) for a, c in zip(ARCH, ch)},
                        "min_pct": round(min(ch), 3), "max_pct": round(max(ch), 3)}
    cnt, med0, med1 = {}, {}, {}
    for a in ARCH:
        v0 = [float(r[a]) for r in mat]
        v1 = [dbl.get((r["reaction"], a), float(r[a])) for r in mat]
        med0[a], med1[a] = statistics.median(v0), statistics.median(v1)
        for t in (25, 50):
            cnt["%s_%d" % (a, t)] = [sum(x >= t for x in v0), sum(x >= t for x in v1)]
    order = ["natural", "stirred", "flow", "anec"]
    keep = all(med1[order[i]] < med1[order[i + 1]] for i in range(3)) and all(med1[t] > med1["anec"] for t in ("micro", "rde", "rce"))
    allch = [abs(c) for v in per_row.values() for c in v["change_pct"].values()]
    res = {"species_doubled": done, "factor": 2.0, "rows_resolved": rows,
           "control_max_deviation": ctl_dev, "per_row": per_row,
           "max_cell_change_pct": round(max(allch), 3),
           "count_moves": [{"arch": k.split("_")[0], "threshold": int(k.split("_")[1]), "from": v[0], "to": v[1]}
                           for k, v in cnt.items() if v[0] != v[1]],
           "median_shift_pct": {a: round(100 * (med1[a] / med0[a] - 1), 3) for a in ARCH},
           "ordering_preserved": keep}
    try:
        full = json.load(io.open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        raise SystemExit("run the first group first: %s is missing" % os.path.relpath(OUT, ROOT))
    full[HOMOG_KEY] = res
    json.dump(full, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("homogeneous partners: %s; control max deviation %.2g; max cell change %.3f pct; count moves: %s"
          % ("; ".join("%s %+.3f..%+.3f pct" % (k, v["min_pct"], v["max_pct"]) for k, v in per_row.items()),
             ctl_dev, res["max_cell_change_pct"], res["count_moves"] or "none"))
    print("G-SPEC2X (homogeneous partners): %s -- wrote key %s of %s"
          % ("PASS" if keep else "FAIL (the ordering inverts)", HOMOG_KEY, os.path.relpath(OUT, ROOT)))
    sys.exit(0 if keep else 1)


def main():
    if "--group" in sys.argv and sys.argv[sys.argv.index("--group") + 1] == "homog":
        return main_homog()
    src = io.open(os.path.join(ROOT, "julia", "run_mediated.jl"), encoding="utf-8").read()
    _, rows, n = patch(src)
    if "--from" in sys.argv:
        dirs = sys.argv[sys.argv.index("--from") + 1].split(",")
    else:
        dirs, rows, n = solve()
    new = {}
    for d in dirs:
        for r in csv.DictReader(io.open(os.path.join(d, "julia", "mediated_ec_matrix.csv"), encoding="utf-8")):
            new[(r["reaction"], REACTOR[r["reactor"]])] = float(r["i_ec_mAcm2"])
    got = sorted({k[0] for k in new})
    if got != sorted(rows):
        raise SystemExit("the doubled solves cover %r, the affected rows are %r" % (got, sorted(rows)))
    mat = list(csv.DictReader(io.open(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"), encoding="utf-8")))
    moved, med0, med1, cnt = [], {}, {}, {}
    for a in ARCH:
        v0 = [float(r[a]) for r in mat]
        v1 = [new.get((r["reaction"], a), float(r[a])) for r in mat]
        med0[a], med1[a] = statistics.median(v0), statistics.median(v1)
        for t in (25, 50):
            cnt["%s_%d" % (a, t)] = [sum(x >= t for x in v0), sum(x >= t for x in v1)]
        moved += [(r["reaction"], a, x0, x1) for r, x0, x1 in zip(mat, v0, v1) if abs(x1 / x0 - 1) > 0.01]
    order = ["natural", "stirred", "flow", "anec"]
    keep = all(med1[order[i]] < med1[order[i + 1]] for i in range(3)) and all(med1[t] > med1["anec"] for t in ("micro", "rde", "rce"))
    res = {"species": list(SPECIES), "factor": 2.0, "rows_resolved": rows, "values_doubled": n,
           "n_cells": len(mat) * len(ARCH), "n_moved_gt1pct": len(moved),
           "count_moves": [{"arch": k.split("_")[0], "threshold": int(k.split("_")[1]), "from": v[0], "to": v[1]}
                           for k, v in cnt.items() if v[0] != v[1]],
           "median_shift_pct": {a: round(100 * (med1[a] / med0[a] - 1), 2) for a in ARCH},
           "medians": {a: [round(med0[a], 3), round(med1[a], 3)] for a in ARCH},
           "max_cell_change_pct": round(max((100 * abs(x1 / x0 - 1) for _, _, x0, x1 in moved), default=0.0), 1),
           "ordering_preserved": keep}
    try:
        prev = json.load(io.open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        prev = {}
    if HOMOG_KEY in prev:
        res[HOMOG_KEY] = prev[HOMOG_KEY]
    json.dump(res, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("rows %s; %d of %d cells move > 1 pct (max %.1f pct); count moves: %s; median shifts %s"
          % (len(rows), len(moved), res["n_cells"], res["max_cell_change_pct"],
             res["count_moves"] or "none", res["median_shift_pct"]))
    print("G-SPEC2X: %s -- wrote %s" % ("PASS" if keep else "FAIL (the ordering inverts)", os.path.relpath(OUT, ROOT)))
    sys.exit(0 if keep else 1)


if __name__ == "__main__":
    main()
