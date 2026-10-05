#!/usr/bin/env python3
"""G-TRANSCRIBE -- the Python transcription of correlations.jl must agree with the solver.

    cd Section4_Model && python data/check_transcription.py
    cd Section4_Model && python data/check_transcription.py --negative-control

WHY
---
delta_eff exists THREE times: julia/correlations.jl (the solver), figs/model_medians.py and
figs/archetype_bands.py (Python transcriptions used by the figure and sensitivity modules).
`archetype_bands.verify_against_tier0()` was written to catch exactly the drift that follows --
it re-derives the Tier-0 matrix from its own transcription and asserts agreement with
julia/tier0_ec_matrix.csv.

It works. Nothing called it. When the stirred film moved 100 -> 200 um the Julia solver and
model_medians.py were both updated and archetype_bands.py was not, so it sat one factor of two
out of step, silently, while every registered gate passed. The drift surfaced only because a new
assertion built on that module returned a nonsense number.

A self-check nothing runs is a self-check that does not exist. This registers it, and checks the
other transcription the same way.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "figs"))

ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]


def main(neg=False):
    import csv
    import io
    import statistics as st
    import archetype_bands as AB
    import model_medians as MM
    import pandas as pd

    rx = list(csv.DictReader(io.open(os.path.join(HERE, "reactions_50.csv"), encoding="utf-8")))
    sol = {r["solvent"]: r for r in
           csv.DictReader(io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8"))}
    fails = []

    # (1) the module's own re-derivation of the whole matrix
    try:
        AB.verify_against_tier0()
        print("  archetype_bands.verify_against_tier0(): agrees with tier0_ec_matrix.csv")
    except Exception as e:
        fails.append("archetype_bands: %s" % str(e)[:180])

    # (2) the two transcriptions must agree with EACH OTHER, per archetype
    print("  %-9s %-14s %-14s" % ("archetype", "archetype_bands", "model_medians"))
    for k in ARCH:
        a = b = None
        for r in rx:
            s = sol.get(r["solvent"]) or sol.get(r["solvent"].split()[0])
            if not s:
                continue
            nu = (float(s["mu_mPas"]) * 1e-3) / (float(s["rho"]) * 1000.0)
            D = float(r["D_cm2s"]) * 1e-4
            a = AB.delta_eff(k, D, nu) * 1e6
            b = MM.delta_eff(k, D, nu) * 1e6
            break
        if neg:
            b = b * 2.0
        print("  %-9s %-14.3f %-14.3f" % (k, a, b))
        if abs(a - b) > 1e-6 * max(abs(a), 1.0):
            fails.append("%s: archetype_bands gives %.4f um, model_medians gives %.4f um"
                         % (k, a, b))

    for f in fails:
        print("    FAIL  %s" % f)
    if neg:
        ok = len(fails) >= len(ARCH)
        print("\nNEGATIVE CONTROL: model_medians' delta doubled, so every archetype must disagree.")
        print("G-TRANSCRIBE control: %s (%d finding(s))"
              % ("GOOD" if ok else "BAD -- test is inert", len(fails)))
        return 0 if ok else 1
    if fails:
        print("\nG-TRANSCRIBE: FAIL -- a Python transcription has drifted from the solver")
        return 1
    print("\nG-TRANSCRIBE: PASS -- both transcriptions agree with correlations.jl and with each "
          "other, and the module's own matrix re-derivation agrees with the published matrix")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
