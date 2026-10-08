#!/usr/bin/env python3
"""G-MEDXFER -- three solver diffusivities carried in a medium for which nothing is tabulated, bracketed by re-solving.

    python data/sensitivity_medium_transfer.py                    # solves every case in scratch copies (~4 min)
    python data/sensitivity_medium_transfer.py --from case:D1,D2;case:D3   # reads finished copies

Each value below is a mediated-row input whose medium has no measured limiting conductance or diffusivity, so it is a
declared state-C value (chemistry audit, pass 4). The bracket is built the same way for all three: a measured value in
each pure solvent of the medium, carried to the medium's viscosity by Walden's rule (D mu = const). Walden's rule is itself
an approximation for ions (registry, NH4+ row), so the ends are a bracket, not a derivation. The rows are re-solved at the
ends; results/medium_transfer_brackets.json records the cell ratios and whether any threshold count or architecture median
moves, and build_param_tables.py prints them on the registry rows.

  cl34   chloride of the thioether row, 6:1 MeCN / 0.1 M aq HCl (mu 0.48 mPa s), carried 2.3e-9:
         lo  Krumgalz 1983 Table 4 p. 581, lambda0(Cl-, MeCN) = 100.4 -> 2.673e-9, x 0.369/0.48 = 2.055e-9
         hi  CRC 97th ed. p. 5-75, aqueous 2.032e-9, x 0.890/0.48 = 3.768e-9
  br46   bromide (and Br2) of the bromination row, 1:1 H2O/MeCN (mu 0.835 mPa s), carried 2.08e-9 (the aqueous value):
         lo  Kalugin 2019 Table 3 p. 28, lambda0(Br-, MeCN) = 102.00 -> 2.716e-9, x 0.369/0.835 = 1.200e-9
         hi  CRC aqueous 2.080e-9 x 0.890/0.835 = 2.217e-9, with Br2 (Cussler p. 127, 1.18e-9) carried likewise to 1.258e-9
  br2    Br2 in MeCN of the Hofmann and amidyl rows, carried 2.2e-9:
         hi  Cussler Table 5.2-1 p. 127, aqueous 1.18e-9, x 0.890/0.369 = 2.846e-9
"""
import csv, io, json, os, shutil, statistics, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "medium_transfer_brackets.json")
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
REACTOR = {"Unstirred batch": "natural", "Stirred batch": "stirred", "Recirculating flow cell": "flow",
           "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro", "RDE 1600 rpm": "rde",
           "Rotating cylinder 3000 rpm": "rce"}
HOF, AMI = "Br-mediated Hofmann rearrangement", "Amidyl-radical C-H amination (phenanthridinone)"
TH, BR = "Thioether -> sulfone (kilo-scale)", "Br- oxidation / electrophilic bromination"
# (exact text in run_mediated.jl, replacement); each must occur exactly once in the file
CASES = {
 "cl34_lo": ([TH], 2.055e-9, [('MedSpec("Thioether -> sulfone (kilo-scale)", 1e3, 5.854e-7, 2.3e-9,', 'MedSpec("Thioether -> sulfone (kilo-scale)", 1e3, 5.854e-7, 2.055e-9,'),
                              ('[S("Cl-", -1.0, 2.3e-9, 14.001,', '[S("Cl-", -1.0, 2.055e-9, 14.001,')]),
 "cl34_hi": ([TH], 3.768e-9, [('MedSpec("Thioether -> sulfone (kilo-scale)", 1e3, 5.854e-7, 2.3e-9,', 'MedSpec("Thioether -> sulfone (kilo-scale)", 1e3, 5.854e-7, 3.768e-9,'),
                              ('[S("Cl-", -1.0, 2.3e-9, 14.001,', '[S("Cl-", -1.0, 3.768e-9, 14.001,')]),
 "br46_lo": ([BR], 1.200e-9, [('MedSpec("Br- oxidation / electrophilic bromination", 2.28e4, 9.227e-7, 2.08e-9,', 'MedSpec("Br- oxidation / electrophilic bromination", 2.28e4, 9.227e-7, 1.200e-9,'),
                              ('[S("Br-", -1.0, 2.08e-9, 250.001,', '[S("Br-", -1.0, 1.200e-9, 250.001,')]),
 "br46_hi": ([BR], 2.217e-9, [('MedSpec("Br- oxidation / electrophilic bromination", 2.28e4, 9.227e-7, 2.08e-9,', 'MedSpec("Br- oxidation / electrophilic bromination", 2.28e4, 9.227e-7, 2.217e-9,'),
                              ('[S("Br-", -1.0, 2.08e-9, 250.001,', '[S("Br-", -1.0, 2.217e-9, 250.001,'),
                              ('S("Br2",  0.0, 1.2e-9,  tr(250.),', 'S("Br2",  0.0, 1.258e-9,  tr(250.),')]),
 "br2_hi":  ([HOF, AMI], 2.846e-9, [('S("Br2",   0.0, 2.2e-9, tr(80.),', 'S("Br2",   0.0, 2.846e-9, tr(80.),'),
                                    ('S("Br2",   0.0, 2.2e-9, tr(40.),', 'S("Br2",   0.0, 2.846e-9, tr(40.),')]),
}
CARRIED = {"cl34": 2.3e-9, "br46": 2.08e-9, "br2": 2.2e-9}


def patched(case):
    s = io.open(os.path.join(ROOT, "julia", "run_mediated.jl"), encoding="utf-8").read()
    for a, b in CASES[case][2]:
        if s.count(a) != 1:
            raise SystemExit("%s: %r occurs %d times in run_mediated.jl" % (case, a[:60], s.count(a)))
        s = s.replace(a, b)
    return s


def solve_one(args):
    case, lab = args
    d = tempfile.mkdtemp(prefix="medxfer_%s_" % case)
    for sub in ("julia", "data"):
        shutil.copytree(os.path.join(ROOT, sub), os.path.join(d, sub),
                        ignore=shutil.ignore_patterns("*.bak*", "*.ksens", "*.zsens", "*.dsens"))
    io.open(os.path.join(d, "julia", "run_mediated.jl"), "w", encoding="utf-8").write(patched(case))
    rc = subprocess.call(["julia", "run_mediated.jl"], cwd=os.path.join(d, "julia"), env=dict(os.environ, MED_ONLY=lab),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc:
        raise SystemExit("%s, %s: the solve exited %d" % (case, lab, rc))
    return case, d


def main():
    for c in CASES:
        patched(c)                                            # every patch target exists, before anything is solved
    if "--from" in sys.argv:
        spec = sys.argv[sys.argv.index("--from") + 1]
        dirs = {c: v.split(",") for c, v in (p.split(":", 1) for p in spec.split(";"))}
    else:
        jobs = [(c, lab) for c in CASES for lab in CASES[c][0]]
        with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
            done = list(ex.map(solve_one, jobs))
        dirs = {c: [d for cc, d in done if cc == c] for c in CASES}
    mat = list(csv.DictReader(io.open(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"), encoding="utf-8")))
    res = {"carried": CARRIED, "cases": {}}
    for c, (rows, val, _) in CASES.items():
        new = {}
        for d in dirs[c]:
            for r in csv.DictReader(io.open(os.path.join(d, "julia", "mediated_ec_matrix.csv"), encoding="utf-8")):
                new[(r["reaction"], REACTOR[r["reactor"]])] = float(r["i_ec_mAcm2"])
        if sorted({k[0] for k in new}) != sorted(rows):
            raise SystemExit("%s: the re-solves cover %r, the case is %r" % (c, sorted({k[0] for k in new}), rows))
        ratios, cmoves, mmoves = [], [], []
        for a in ARCH:
            v0 = [float(r[a]) for r in mat]
            v1 = [new.get((r["reaction"], a), float(r[a])) for r in mat]
            ratios += [new[(r["reaction"], a)] / float(r[a]) for r in mat if (r["reaction"], a) in new]
            for t in (25, 50):
                b0, b1 = sum(x >= t for x in v0), sum(x >= t for x in v1)
                if b0 != b1:
                    cmoves.append({"arch": a, "threshold": t, "from": b0, "to": b1})
            m0, m1 = statistics.median(v0), statistics.median(v1)
            if abs(m1 / m0 - 1) > 1e-9:
                mmoves.append({"arch": a, "from": round(m0, 3), "to": round(m1, 3)})
        low = min(min(new[(r, a)] for a in ARCH) for r in rows)
        res["cases"][c] = {"rows": rows, "D": val, "ratio_lo": round(min(ratios), 4), "ratio_hi": round(max(ratios), 4),
                           "lowest_cell_mAcm2": round(low, 2), "count_moves": cmoves, "median_moves": mmoves}
        print("%-8s D %.3e: cells x%.3f-x%.3f, lowest cell %.1f; counts %s; medians %s"
              % (c, val, min(ratios), max(ratios), low, cmoves or "unchanged", mmoves or "unchanged"))
    json.dump(res, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("G-MEDXFER: PASS -- wrote %s" % os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
