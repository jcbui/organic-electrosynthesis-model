#!/usr/bin/env python3
"""Perturb named solver species in the mediated solver and report the effect on published counts.

    /opt/anaconda3/bin/python3.12 data/sensitivity_solver_species.py --species ClO4- SCN- Br- Br2 --factor 2

Supports the category-4 sensitivity statement that the supporting-electrolyte and mediator
counter-ion diffusivities DO reach a reported count through the EC' solve, which the eight mediated
entries use. Patches a COPY of run_mediated.jl and redirects its output; production is untouched.
"""
import argparse, csv, io, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); JL = os.path.join(os.path.dirname(HERE), "julia")
SRC = os.path.join(JL, "run_mediated.jl")

def patch(species, factor, tag):
    s = io.open(SRC, encoding="utf-8").read(); n = 0
    for sp in species:
        pat = re.compile(r'(S\("%s",\s*[-\d.+]+,\s*)([\d.e+-]+)' % re.escape(sp))
        s, k = pat.subn(lambda m: "%s%.6g" % (m.group(1), float(m.group(2)) * factor), s)
        n += k
    out = "mediated_ec_matrix_%s.csv" % tag
    s = s.replace('open(joinpath(@__DIR__, "mediated_ec_matrix.csv"), "w")',
                  'open(joinpath(@__DIR__, "%s"), "w")' % out)
    p = os.path.join(JL, "_sp_%s.jl" % tag)
    io.open(p, "w", encoding="utf-8").write(s)
    return p, out, n

def counts(path):
    import statistics
    rows = list(csv.DictReader(io.open(path, encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault(r["reactor"], []).append(float(r["i_ec_mAcm2"]))
    return {k: (sum(v >= 25 for v in vs), sum(v >= 50 for v in vs)) for k, vs in by.items()}, \
           {r["reaction"] + "|" + r["reactor"]: float(r["i_ec_mAcm2"]) for r in rows}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--species", nargs="+", required=True)
    ap.add_argument("--factor", type=float, required=True)
    a = ap.parse_args()
    tag = ("x%g" % a.factor).replace(".", "p")
    p, out, n = patch(a.species, a.factor, tag)
    print("patched %d species literals (%s x%g) -> %s" % (n, ", ".join(a.species), a.factor,
                                                          os.path.basename(p)))
    sys.stdout.flush()
    r = subprocess.run(["julia", os.path.basename(p)], cwd=JL, capture_output=True, text=True)
    if r.returncode != 0:
        print("solver failed:", r.stderr[-500:]); return
    base_c, base_i = counts(os.path.join(JL, "mediated_ec_matrix.csv"))
    new_c,  new_i  = counts(os.path.join(JL, out))
    moved = [(k, base_i[k], new_i[k]) for k in base_i
             if k in new_i and abs(new_i[k] - base_i[k]) > 0.01 * abs(base_i[k])]
    print("\nmediated cells moving by more than 1%%: %d of %d" % (len(moved), len(base_i)))
    for k, a_, b_ in sorted(moved, key=lambda t: -abs(t[2]/t[1]-1))[:8]:
        print("   %-56s %8.3f -> %8.3f (%+.2f%%)" % (k[:56], a_, b_, 100*(b_/a_-1)))
    print("\n%-30s %14s %14s" % ("reactor", "base >=25/>=50", "pert >=25/>=50"))
    for k in sorted(base_c):
        print("%-30s %6d/%-7d %6d/%-7d%s" % (k[:30], base_c[k][0], base_c[k][1],
              new_c[k][0], new_c[k][1], "   <-- MOVES" if base_c[k] != new_c[k] else ""))
    os.remove(p)

if __name__ == "__main__":
    main()
