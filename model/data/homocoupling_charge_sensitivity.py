#!/usr/bin/env python3
"""G-HOMOZ -- the carrier charge of the cathodic Ni aryl-aryl homocoupling, re-solved at the alternatives.

The row carries z = 0, the charge of the precursor its exemplar adds (NiBr2bpy, Courtois/Perichon 1997). The same paper
writes the complex it reduces as the dication ('Nibpy2+ + 2 e -> Ni0bpy', eq. 2; eq. 4 balances only with it), so z is
not established, and unlike the four medium-confidence rows of G-ZSENS this row is carried at a finite rate constant
(10^2, SI S5.7), where migration of a charged catalyst changes the in-film regeneration as well as the transport bound.
This script re-solves the row's catalyst sweep (julia/run_catalyst_ecprime.jl, CAT_ROWS of that row) at z = +1 and +2
in scratch copies, reads the ceilings at the adopted k, and writes results/homocoupling_charge_sensitivity.json: the
ceiling ratio per architecture and how each published threshold count would move.

    python data/homocoupling_charge_sensitivity.py              # solves (about 15 min)
    python data/homocoupling_charge_sensitivity.py --from Z1,Z2 # reads catalyst_ec_sweep.csv written at z=+1, z=+2

Control: the z = 0 member read from the published sweep must reproduce the published matrix's cells for this row.
"""
import csv, io, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROW = "Cathodic Ni aryl-aryl homocoupling"
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
REACTOR = {"natural": "Unstirred batch", "stirred": "Stirred batch", "flow": "Recirculating flow cell",
           "anec": "ANEC flow cell", "micro": "Microfluidic cell (25 um gap)", "rde": "RDE 1600 rpm",
           "rce": "Rotating cylinder 3000 rpm"}
OUT = os.path.join(ROOT, "results", "homocoupling_charge_sensitivity.json")


def k_adopted():
    for r in csv.DictReader(io.open(os.path.join(HERE, "rate_constant_basis.csv"), encoding="utf-8")):
        if r["reaction"] == ROW:
            return float(r["k_M1s1"])
    raise SystemExit("no rate-constant record for " + ROW)


def sweep_at(path, k):
    rows = [r for r in csv.DictReader(io.open(path, encoding="utf-8")) if r["reaction"] == ROW and abs(float(r["k_M"]) - k) < 1e-9]
    got = {r["reactor"]: float(r["i_ec_mAcm2"]) for r in rows}
    out = {a: got[REACTOR[a]] for a in ARCH if REACTOR[a] in got}
    if len(out) != len(ARCH):
        raise SystemExit("%s: the sweep at k = %g covers %d of %d architectures" % (path, k, len(out), len(ARCH)))
    return out


def cat_index():
    cat = [r["reaction"] for r in csv.DictReader(io.open(os.path.join(HERE, "reactions_50.csv"), encoding="utf-8"))
           if "catalyst" in r["carrier_type"].lower()]
    return cat.index(ROW) + 1


def solve(z):
    d = tempfile.mkdtemp(prefix="homoz%d_" % z)
    for sub in ("julia", "data"):
        shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub),
                        ignore=shutil.ignore_patterns("*.bak*", "*.ksens", "*.zsens", "*.dsens"))
    p = os.path.join(d, "data", "carrier_charge.csv")
    L = io.open(p, encoding="utf-8").read().split("\n")
    hit = [i for i, l in enumerate(L) if l.startswith(ROW + ",")]
    if len(hit) != 1:
        raise SystemExit("carrier_charge.csv: %d rows for %s" % (len(hit), ROW))
    parts = L[hit[0]].split(","); parts[3] = str(z); L[hit[0]] = ",".join(parts)
    io.open(p, "w", encoding="utf-8").write("\n".join(L))
    i = cat_index()
    rc = subprocess.call(["julia", "run_catalyst_ecprime.jl"], cwd=os.path.join(d, "julia"),
                         env=dict(os.environ, CAT_ROWS="%d:%d" % (i, i)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc:
        raise SystemExit("the z = %d solve exited %d" % (z, rc))
    return os.path.join(d, "julia", "catalyst_ec_sweep.csv")


def main():
    k = k_adopted()
    if "--from" in sys.argv:
        paths = dict(zip((1, 2), sys.argv[sys.argv.index("--from") + 1].split(",")))
        paths = {z: os.path.join(p, "julia", "catalyst_ec_sweep.csv") if os.path.isdir(p) else p for z, p in paths.items()}
    else:
        paths = {z: solve(z) for z in (1, 2)}
    base = sweep_at(os.path.join(ROOT, "julia", "catalyst_ec_sweep.csv"), k)
    mat = list(csv.DictReader(io.open(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"), encoding="utf-8")))
    pub = next(r for r in mat if r["reaction"] == ROW)
    worst = max(abs(base[a] / float(pub[a]) - 1) for a in ARCH)
    if worst > 1e-5:                                           # the published matrix is written to 6 s.f.
        raise SystemExit("control: the z = 0 sweep at k = %g does not reproduce the published cells (worst %.2e)" % (k, worst))
    print("control: the z = 0 sweep at k = %g reproduces the published %s cells to %.1e" % (k, ROW, worst))
    alt, moves = {}, {}
    for z, p in paths.items():
        v = sweep_at(p, k)
        alt[str(z)] = {a: round(v[a], 3) for a in ARCH}
        mv = []
        for a in ARCH:
            for thr in (25, 50):
                b = sum(float(r[a]) >= thr for r in mat)
                s = sum((v[a] if r["reaction"] == ROW else float(r[a])) >= thr for r in mat)
                if b != s:
                    mv.append({"arch": a, "threshold": thr, "from": b, "to": s})
        moves[str(z)] = mv
        print("z = +%d: ceilings x%.2f-x%.2f; %s" % (z, min(v[a] / base[a] for a in ARCH), max(v[a] / base[a] for a in ARCH),
                                                     "; ".join("%s >=%d %d->%d" % (m["arch"], m["threshold"], m["from"], m["to"]) for m in mv) or "no count moves"))
    res = {"reaction": ROW, "k_adopted": k, "z_carried": 0, "carried": {a: round(base[a], 3) for a in ARCH},
           "alternatives": alt, "count_moves": moves,
           "ratio": {z: [round(min(alt[z][a] / base[a] for a in ARCH), 3), round(max(alt[z][a] / base[a] for a in ARCH), 3)] for z in alt},
           "clears25_every_arch": {z: all(alt[z][a] >= 25 for a in ARCH) for z in alt},
           "clears25_from": {z: next((a for a in ARCH if all(alt[z][b] >= 25 for b in ARCH[ARCH.index(a):])), None) for z in alt}}
    res["clears25_from"]["0"] = next((a for a in ARCH if all(base[b] >= 25 for b in ARCH[ARCH.index(a):])), None)
    json.dump(res, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("G-HOMOZ: PASS -- wrote %s" % os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
