#!/usr/bin/env python3
"""G-XECZ -- the carrier charge of the Ni cross-electrophile coupling, re-solved at its published rate constant.

The row carries z = 0 at medium confidence. G-ZSENS re-solves the medium-confidence charges in the k = 0 layer, which is
the published layer for three of them; this row alone among them is published at a sourced rate constant (10^2 M-1 s-1,
SI S5.7), where a charged catalyst's migration changes the in-film regeneration as well as the transport bound, as the
homocoupling's G-HOMOZ shows (chemistry audit, pass 4). This script reads the catalyst sweep re-solved at z = -1, +1 and +2
(julia/run_catalyst_ecprime.jl, CAT_ROWS of this row, in scratch copies) and writes results/xec_charge_sensitivity.json:
the ceiling ratio per architecture at the adopted k and how each published threshold count would move.

    python data/xec_charge_sensitivity.py                         # solves (about 20 min)
    python data/xec_charge_sensitivity.py --from Dm1,Dp1,Dp2      # reads catalyst_ec_sweep.csv written at z = -1, +1, +2

Control: the z = 0 member read from the published sweep must reproduce the published matrix's cells for this row.
"""
import csv, io, json, os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import homocoupling_charge_sensitivity as H                      # noqa: E402

ROW = "Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)"
ZS = (-1, 1, 2)
OUT = os.path.join(H.ROOT, "results", "xec_charge_sensitivity.json")
H.ROW = ROW


def solve(z):
    d = tempfile.mkdtemp(prefix="xecz%d_" % z)
    for sub in ("julia", "data"):
        shutil.copytree(os.path.join(H.ROOT, sub), os.path.join(d, sub),
                        ignore=shutil.ignore_patterns("*.bak*", "*.ksens", "*.zsens", "*.dsens"))
    p = os.path.join(d, "data", "carrier_charge.csv")
    L = io.open(p, encoding="utf-8").read().split("\n")
    hit = [i for i, l in enumerate(L) if l.startswith(ROW + ",")]
    if len(hit) != 1:
        raise SystemExit("carrier_charge.csv: %d rows for %s" % (len(hit), ROW))
    parts = L[hit[0]].split(","); parts[3] = str(z); L[hit[0]] = ",".join(parts)
    io.open(p, "w", encoding="utf-8").write("\n".join(L))
    i = H.cat_index()
    rc = subprocess.call(["julia", "run_catalyst_ecprime.jl"], cwd=os.path.join(d, "julia"),
                         env=dict(os.environ, CAT_ROWS="%d:%d" % (i, i)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc:
        raise SystemExit("the z = %d solve exited %d" % (z, rc))
    return d


def main():
    k = H.k_adopted()
    if "--from" in sys.argv:
        dirs = dict(zip(ZS, sys.argv[sys.argv.index("--from") + 1].split(",")))
    else:
        with ThreadPoolExecutor(max_workers=len(ZS)) as ex:
            dirs = dict(zip(ZS, ex.map(solve, ZS)))
    paths = {z: os.path.join(d, "julia", "catalyst_ec_sweep.csv") for z, d in dirs.items()}
    base = H.sweep_at(os.path.join(H.ROOT, "julia", "catalyst_ec_sweep.csv"), k)
    mat = list(csv.DictReader(io.open(os.path.join(H.ROOT, "julia", "tier0_ec_matrix.csv"), encoding="utf-8")))
    pub = next(r for r in mat if r["reaction"] == ROW)
    worst = max(abs(base[a] / float(pub[a]) - 1) for a in H.ARCH)
    if worst > 1e-5:
        raise SystemExit("control: the z = 0 sweep at k = %g does not reproduce the published cells (worst %.2e)" % (k, worst))
    print("control: the z = 0 sweep at k = %g reproduces the published %s cells to %.1e" % (k, ROW, worst))
    alt, moves = {}, {}
    for z, p in paths.items():
        v = H.sweep_at(p, k)
        alt[str(z)] = {a: round(v[a], 3) for a in H.ARCH}
        mv = []
        for a in H.ARCH:
            for thr in (25, 50):
                b = sum(float(r[a]) >= thr for r in mat)
                s = sum((v[a] if r["reaction"] == ROW else float(r[a])) >= thr for r in mat)
                if b != s:
                    mv.append({"arch": a, "threshold": thr, "from": b, "to": s})
        moves[str(z)] = mv
        print("z = %+d: ceilings x%.3f-x%.3f; %s" % (z, min(v[a] / base[a] for a in H.ARCH), max(v[a] / base[a] for a in H.ARCH),
                                                    "; ".join("%s >=%d %d->%d" % (m["arch"], m["threshold"], m["from"], m["to"]) for m in mv) or "no count moves"))
    res = {"reaction": ROW, "k_adopted": k, "z_carried": 0, "carried": {a: round(base[a], 3) for a in H.ARCH},
           "alternatives": alt, "count_moves": moves,
           "ratio": {z: [round(min(alt[z][a] / base[a] for a in H.ARCH), 3), round(max(alt[z][a] / base[a] for a in H.ARCH), 3)] for z in alt}}
    json.dump(res, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("G-XECZ: PASS -- wrote %s" % os.path.relpath(OUT, H.ROOT))


if __name__ == "__main__":
    main()
