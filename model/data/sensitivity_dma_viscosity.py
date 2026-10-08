#!/usr/bin/env python3
"""G-DMAMU -- bound the one solvent viscosity in this model that its own homolog contradicts.

    cd Section4_Model && python data/sensitivity_dma_viscosity.py
    cd Section4_Model && python data/sensitivity_dma_viscosity.py --negative-control

WHY
---
CRC 97th ed., Sect. 6 "Viscosity of Liquids", p. 6-244, prints eta(25 C) = 1.927 mPa s for
N,N-dimethylacetamide. That is the value solvents.csv carries and the value Table S3 publishes,
because it is what the page prints.

It sits oddly against its own immediate homolog. N,N-dimethylformamide -- DMA less one CH2 --
appears in the SAME COLUMN of the SAME PAGE at 0.794 mPa s, and the column assignment is not in
doubt: at that x-position the page also prints ethanol 1.074, 1,4-dioxane 1.177, dimethyl
sulfoxide 1.987 and diethyl ether 0.224, every one of them the accepted 25 C value. So DMA is
recorded as 2.4x more viscous than the homolog it differs from by a single methylene, where the
usual increment for that substitution is a few tens of a percent. The commonly used figure for
DMA is about 0.93 mPa s, which would make the CRC entry differ from it by exactly 1.000 -- the
signature of a leading-digit error.

THIS SCRIPT DOES NOT SUBSTITUTE 0.927, AND THE REGISTRY DOES NOT EITHER.
"It looks like a typo" is a judgement, not a source, and replacing a page-anchored number with an
unsourced one is the exact move docs/PROVENANCE_STANDARD.md forbids -- the same move that kept
MeCN at 0.343 against a printed 0.369 until 2026-08-23. The handbook was searched for a second,
independent DMA viscosity and there is none: the only other DMA entries are thermal conductivity
(p. 6-255), azeotrope data and aqueous surface tension. Absent a second source, the printed value
stands and the DISAGREEMENT IS DECLARED AND BOUNDED HERE instead of being quietly resolved.

WHAT IS AT STAKE
----------------
Two of the fifty rows run in DMA, both catalyst-carried: the Ni-catalyzed aryl amination, carried at
the floor k = 0, and the kilogram-scale Ni-XEC row, carried at its sourced k = 1e2 M-1 s-1 (S5.7).
The test sweeps the whole interval between the two candidate viscosities and asks whether ANY
threshold count (>= 25 or >= 50 mA cm-2), or the count of catalyst rows clearing 25 mA cm-2 anywhere,
moves inside it.

HOW THE DMA CELLS ARE SCALED
----------------------------
Every DMA cell is RE-SOLVED at each swept viscosity (data/dma_viscosity_ecprime.jl, run in a scratch
copy, artifact results/dma_viscosity_ecprime.csv), and this script reads those solves. An earlier
version scaled every DMA cell as mu^p, p the archetype's transport exponent. That is exact for a cell
solved at k = 0 -- the whole Nernst-Planck problem scales with D -- and wrong for a cell solved as an
EC' problem at a finite rate constant: on the kinetic plateau the current is n F C_cat (D k C_S)^(1/2),
i.e. mu^(-1/2), so mu^-1 roughly doubled the Ni-XEC thin-film cells (12.4 -> 25.7 mA cm-2 in the
microfluidic cell) where the solver gives 18.1. The re-solve is refused unless, at the printed
viscosity, every one of its cells reproduces the published matrix.
"""
import io
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from sensitivity_solution_viscosity import ARCH, MU_EXP, THRESH, _assert_exponents  # noqa: E402

MU_PRINTED = 1.927        # CRC 97th ed. p. 6-244, eta(25 C) column -- what the model carries
MU_HOMOLOG = 0.927        # the figure the leading-digit reading would give; NOT adopted
MU_KRUMGALZ = 0.919       # Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571, Table 3 p. 578: 0.00919 P; NOT adopted
MU_LOW = min(MU_HOMOLOG, MU_KRUMGALZ)   # the sweep's lower edge covers both readings
OUT = os.path.join(ROOT, "results", "dma_viscosity_sensitivity.json")


# A NEGATIVE CONTROL MUST NEVER WRITE THE ARTIFACT IT PERTURBS. Until 2026-08-30 several
# controls here dumped their perturbed numbers straight over results/, so a control run
# left the repo holding fabricated values until the next ordinary run happened to fix it --
# and an audit that snapshotted results/ AFTER a control run then compared against
# contaminated bytes and reported no contamination. Controls write a _NEGCONTROL sibling,
# the convention data/check_conditions.py already used.
ARCH_WORD = {"natural": "unstirred", "stirred": "stirred", "flow": "recirculating flow", "anec": "ANEC",
             "micro": "microfluidic", "rde": "RDE", "rce": "rotating cylinder"}

def _out(path, neg):
    return path[:-5] + "_NEGCONTROL.json" if neg and path.endswith(".json") else path

ECP = os.path.join(ROOT, "results", "dma_viscosity_ecprime.csv")
THRESHOLDS = (25.0, 50.0)


def _resolved_cells(m, dma):
    """{mu: {reaction: {arch: i_lim}}} from the scratch re-solve, after the control: at the printed viscosity each
    re-solved cell must reproduce the published matrix to its printed precision (four decimals, so 5e-5 absolute)."""
    if not os.path.exists(ECP):
        raise SystemExit("G-DMAMU: %s is absent; run data/dma_viscosity_ecprime.jl in a scratch copy" % ECP)
    ec = pd.read_csv(ECP)
    out = {}
    for _, r in ec.iterrows():
        out.setdefault(round(float(r.mu_mPas), 6), {}).setdefault(r.reaction, {})[r.reactor_key] = float(r.i_ec_mAcm2)
    want_rx = set(m[dma].reaction)
    for mu, d in out.items():
        if set(d) != want_rx or any(set(v) != set(ARCH) for v in d.values()):
            raise SystemExit("G-DMAMU: the re-solve at mu = %g does not cover the %d DMA rows x %d architectures"
                             % (mu, len(want_rx), len(ARCH)))
    base = out.get(round(MU_PRINTED, 6))
    if base is None:
        raise SystemExit("G-DMAMU: the re-solve carries no solve at the printed viscosity %.3f" % MU_PRINTED)
    bad = []
    for _, r in m[dma].iterrows():
        for a in ARCH:
            if abs(base[r.reaction][a] - r[a]) > 5.0001e-5:
                bad.append("%s/%s: re-solve %.6g vs published %.6g" % (r.reaction[:30], a, base[r.reaction][a], r[a]))
    if bad:
        raise SystemExit("G-DMAMU: the re-solve does not reproduce the published matrix at the printed viscosity "
                         "(stale artifact?):\n  " + "\n  ".join(bad))
    return out


def main(neg=False):
    _assert_exponents()
    rx = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
    t0 = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    m = t0.merge(rx[["reaction", "solvent", "carrier_type"]], on="reaction")
    dma = m.solvent.str.strip() == "DMA"
    if int(dma.sum()) != 2:
        raise SystemExit("expected 2 DMA rows, found %d" % int(dma.sum()))
    solved = _resolved_cells(m, dma)
    mus = sorted(solved, reverse=True)
    if abs(mus[-1] - MU_LOW) > 1e-9:
        raise SystemExit("G-DMAMU: the re-solve's lowest viscosity is %g, not %g (the lower of the homolog reading and "
                         "Krumgalz's Table 3 value)" % (mus[-1], MU_LOW))

    cat = (m.carrier_type == "catalyst")
    def counts(s):
        return {str(int(t)): {a: int((s[a] >= t).sum()) for a in ARCH} for t in THRESHOLDS}
    def cat_clear(s):
        return int((s[cat][ARCH].max(axis=1) >= THRESH).sum())
    base_counts = counts(m)
    base_cat = cat_clear(m)

    print("  CRC p. 6-244 prints eta(25 C) = %.3f mPa s for DMA; DMF, one CH2 lighter, is 0.794" % MU_PRINTED)
    print("  in the same column of the same page. Every DMA cell RE-SOLVED at mu(DMA) in %s mPa s:\n"
          % ", ".join("%.3f" % u for u in mus))
    print("  %-46s %-9s %s" % ("row", "mu", "  ".join("%8s" % a for a in ARCH)))
    sweep = []
    if neg:
        # control: an absurd viscosity, every DMA cell scaled as mu^p (exact at k = 0, an overestimate on the plateau);
        # the counting and declaring logic below must see a count move
        lo = MU_PRINTED / 200.0
        cases = [(lo, {r.reaction: {a: r[a] * (lo / MU_PRINTED) ** MU_EXP[a] for a in ARCH}
                       for _, r in m[dma].iterrows()})]
    else:
        cases = [(mu, solved[mu]) for mu in mus]
    for mu, cells in cases:
        s = m.copy()
        for rxn, row in cells.items():
            for a in ARCH:
                s.loc[s.reaction == rxn, a] = row[a]
        for _, r in s[dma].iterrows():
            print("  %-46s %-9.3f %s" % (r.reaction[:46], mu, "  ".join("%8.2f" % r[a] for a in ARCH)))
        best = max(((r.reaction, a, float(r[a])) for _, r in s[dma].iterrows() for a in ARCH), key=lambda x: x[2])
        sweep.append({"mu": mu, "counts": counts(s), "catalyst_clearing": cat_clear(s),
                      "dma_cells": {r.reaction: {a: float(r[a]) for a in ARCH} for _, r in s[dma].iterrows()},
                      "dma_best": {"reaction": best[0], "arch": best[1], "i_lim": best[2]}})
        print()

    moves = []
    for rr in sweep:
        for t in rr["counts"]:
            for a in ARCH:
                d = rr["counts"][t][a] - base_counts[t][a]
                if d:
                    moves.append({"mu": rr["mu"], "threshold": float(t), "arch": a, "delta": d})
    cat_moves = [rr["mu"] for rr in sweep if rr["catalyst_clearing"] != base_cat]
    # the scaling the re-solve replaces, kept so the artifact records what it would have said
    naive = {}
    for _, r in m[dma].iterrows():
        naive[r.reaction] = {a: float(r[a] * (MU_HOMOLOG / MU_PRINTED) ** MU_EXP[a]) for a in ARCH}
    out = {"mu_printed": MU_PRINTED, "mu_alternative_not_adopted": MU_HOMOLOG, "mu_krumgalz": MU_KRUMGALZ,
           "mu_low": MU_LOW, "adopted": MU_PRINTED,
           "method": "every DMA cell re-solved at each swept viscosity (data/dma_viscosity_ecprime.jl); "
                     "carrier, product and substrate D scale as 1/mu, nu as mu, supporting ions and k held",
           "dma_rows": {r.reaction: {"carrier_type": r.carrier_type} for _, r in m[dma].iterrows()},
           "swept": sweep, "base_counts": base_counts, "base_catalyst_clearing": base_cat,
           "n_catalyst_rows": int(cat.sum()), "count_moves": moves, "catalyst_clearing_moves_at": cat_moves,
           "mu_power_law_at_homolog": naive,
           "source": "CRC 97th ed. 2016, Sect. 6 'Viscosity of Liquids', p. 6-244, eta(25 C) column"}
    json.dump(out, io.open(_out(OUT, neg), "w", encoding="utf8"), indent=1)

    print("  threshold counts at the printed value: %s" % base_counts)
    print("  catalyst rows clearing %.0f in >=1 architecture: %d of %d" % (THRESH, base_cat, int(cat.sum())))
    if neg:
        print("\nNEGATIVE CONTROL: mu(DMA) driven to %.4f mPa s, %.0fx below the printed value, so"
              % (cases[0][0], MU_PRINTED / cases[0][0]))
        print("  at least one count MUST move.")
        print("G-DMAMU control: %s" % ("GOOD (counts moved: %s)" % moves if moves
                                       else "BAD -- test is inert, no count moved"))
        return 0 if moves else 1
    if moves or cat_moves:
        # a movement is allowed only while the registry row that publishes this sweep DECLARES it
        import csv
        reg = list(csv.DictReader(io.open(os.path.join(HERE, "parameters_provenance.csv"), encoding="utf8")))
        row = [r for r in reg if r.get("parameter", "") == "DMA: mu (25 C)"]
        text = " ".join(r.get("sensitivity", "") for r in row)
        undeclared = sorted({mv["arch"] for mv in moves if ARCH_WORD[mv["arch"]] not in text})
        if undeclared or not row:
            print("\nG-DMAMU: FAIL -- a published count moves inside the interval between the printed viscosity "
                  "and its homolog reading (%s) and the DMA viscosity registry row does not declare it for: %s"
                  % (moves, undeclared or "(no DMA viscosity row found)"))
            return 1
        print("\nG-DMAMU: PASS -- the printed %.3f mPa s is carried; inside the interval down to %.3f a count moves "
              "(%s), and the DMA viscosity row of the registry declares each movement (Table S7b)."
              % (MU_PRINTED, MU_LOW, moves))
        return 0
    b = sweep[-1]["dma_best"]
    print("\nG-DMAMU: PASS -- the printed %.3f mPa s is carried; re-solving every DMA cell across the whole interval "
          "down to %.3f moves no >=25 or >=50 count and leaves %d catalyst row(s) clearing 25 (best DMA cell at the "
          "lowest swept viscosity: %s, %s, %.2f mA cm-2)." % (MU_PRINTED, MU_LOW, base_cat, b["reaction"], b["arch"], b["i_lim"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
