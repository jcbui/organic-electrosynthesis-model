#!/usr/bin/env python3
"""Perturb the trace initialisation of the electrogenerated form and re-solve the mediated matrix.

    /opt/anaconda3/bin/python3.12 data/sensitivity_trace_init.py

`tr(C) = C * 1e-5` seeds the oxidised mediator (and H+ in aprotic media) at a trace of bulk. The
registry claims the results are independent of that seed. This moves it a full decade in both
directions and re-solves, so the claim is measured rather than asserted. Patches a COPY; production
is untouched.
"""
import csv, io, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); JL = os.path.join(os.path.dirname(HERE), "julia")
SRC = os.path.join(JL, "run_mediated.jl")

def run(val, tag):
    s = io.open(SRC, encoding="utf-8").read()
    s2, n = re.subn(r'tr\(C\)\s*=\s*C\s*\*\s*[\d.e-]+', 'tr(C) = C * %s' % val, s)
    assert n == 1, "tr(C) definition not found (n=%d)" % n
    out = "mediated_ec_matrix_tr%s.csv" % tag
    s2 = s2.replace('open(joinpath(@__DIR__, "mediated_ec_matrix.csv"), "w")',
                    'open(joinpath(@__DIR__, "%s"), "w")' % out)
    p = os.path.join(JL, "_tr_%s.jl" % tag)
    io.open(p, "w", encoding="utf-8").write(s2)
    print("  tr(C) = C * %s -> solving" % val); sys.stdout.flush()
    r = subprocess.run(["julia", os.path.basename(p)], cwd=JL, capture_output=True, text=True)
    os.remove(p)
    if r.returncode != 0:
        print("   solver failed:", r.stderr[-300:]); return None
    return {x["reaction"] + "|" + x["reactor"]: float(x["i_ec_mAcm2"])
            for x in csv.DictReader(io.open(os.path.join(JL, out), encoding="utf-8"))}

def main():
    base = {x["reaction"] + "|" + x["reactor"]: float(x["i_ec_mAcm2"])
            for x in csv.DictReader(io.open(os.path.join(JL, "mediated_ec_matrix.csv"), encoding="utf-8"))}
    for val, tag in (("1e-4", "hi"), ("1e-6", "lo")):
        p = run(val, tag)
        if p is None: continue
        diffs = [(k, base[k], p[k]) for k in base if k in p and base[k] != p[k]]
        worst = max((abs(b-a) for _, a, b in diffs), default=0.0)
        print("   %d of %d cells differ at all; largest absolute change %.3g mA/cm2"
              % (len(diffs), len(base), worst))
        for k, a, b in sorted(diffs, key=lambda t: -abs(t[2]-t[1]))[:4]:
            print("      %-54s %9.4f -> %9.4f" % (k[:54], a, b))
        for thr in (25, 50):
            cb = sum(v >= thr for v in base.values()); cp = sum(v >= thr for v in p.values())
            print("      mediated cells >=%d: %d -> %d%s" % (thr, cb, cp, "  MOVES" if cb != cp else ""))

if __name__ == "__main__":
    main()
