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
Two of the fifty rows run in DMA, both catalyst-carried:
    Ni-catalyzed aryl amination (ArBr + amine)      best ceiling 2.75 mA cm-2
    Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)               best ceiling 8.26 mA cm-2
Both sit far below the 25 mA cm-2 threshold, and i_lim rises only as mu^p with p in [-1, -2/3].
The test below sweeps the whole interval between the two candidate viscosities and asks whether
ANY threshold count, or the 10-of-11 catalyst conclusion, moves anywhere inside it.
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

def main(neg=False):
    _assert_exponents()
    rx = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
    t0 = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    m = t0.merge(rx[["reaction", "solvent", "carrier_type"]], on="reaction")
    dma = m.solvent.str.strip() == "DMA"
    if int(dma.sum()) != 2:
        raise SystemExit("expected 2 DMA rows, found %d" % int(dma.sum()))

    lo = MU_HOMOLOG if not neg else MU_PRINTED / 200.0   # control: an absurd viscosity
    base_counts = {a: int((m[a] >= THRESH).sum()) for a in ARCH}
    base_cat = int((m[m.carrier_type == "catalyst"][ARCH].max(axis=1) >= THRESH).sum())

    print("  CRC p. 6-244 prints eta(25 C) = %.3f mPa s for DMA; DMF, one CH2 lighter, is 0.794"
          % MU_PRINTED)
    print("  in the same column of the same page. Sweeping mu(DMA) over [%.3f, %.3f] mPa s:\n"
          % (lo, MU_PRINTED))
    print("  %-46s %-9s %s" % ("row", "mu", "  ".join("%8s" % a for a in ARCH)))
    rows, worst = [], []
    for mu in (MU_PRINTED, (MU_PRINTED + lo) / 2.0, lo):
        f = mu / MU_PRINTED                      # i_lim scales as f**MU_EXP[arch]
        s = m.copy()
        for a in ARCH:
            s.loc[dma, a] = s.loc[dma, a] * (f ** MU_EXP[a])
        for _, r in s[dma].iterrows():
            print("  %-46s %-9.3f %s" % (r.reaction[:46], mu,
                                         "  ".join("%8.2f" % r[a] for a in ARCH)))
        counts = {a: int((s[a] >= THRESH).sum()) for a in ARCH}
        cat = int((s[s.carrier_type == "catalyst"][ARCH].max(axis=1) >= THRESH).sum())
        rows.append({"mu": mu, "counts": counts, "catalyst_clearing": cat})
        if counts != base_counts or cat != base_cat:
            worst.append((mu, counts, cat))
        print()

    # 2026-09-11: which counts move, by architecture, at each swept viscosity -- the registry row that
    # publishes this sweep must DECLARE each of them (existence alone is no longer the verdict: the
    # seven sourced-k catalyst rows put the Ni-XEC row close enough to 25 mA cm-2 that the homolog
    # reading carries it over in the thin films, and a sensitivity the row states is what the standard asks for)
    moves = []
    for rr in rows:
        for a in ARCH:
            d = rr["counts"][a] - base_counts[a]
            if d:
                moves.append({"mu": rr["mu"], "arch": a, "delta": d})
    json.dump({"mu_printed": MU_PRINTED, "mu_alternative_not_adopted": MU_HOMOLOG,
               "adopted": MU_PRINTED, "swept": rows, "base_counts": base_counts,
               "base_catalyst_clearing": base_cat, "count_moves": moves,
               "source": "CRC 97th ed. 2016, Sect. 6 'Viscosity of Liquids', p. 6-244, "
                         "eta(25 C) column"},
              io.open(_out(OUT, neg), "w", encoding="utf8"), indent=1)

    print("  threshold counts at the printed value: %s" % base_counts)
    print("  catalyst rows clearing %.0f in >=1 architecture: %d of 11" % (THRESH, base_cat))
    if neg:
        print("\nNEGATIVE CONTROL: mu(DMA) driven to %.4f mPa s, %.0fx below the printed value, so"
              % (lo, MU_PRINTED / lo))
        print("  at least one count MUST move.")
        print("G-DMAMU control: %s" % ("GOOD (a count moved: %s)" % worst[-1][1] if worst
                                       else "BAD -- test is inert, no count moved"))
        return 0 if worst else 1
    if worst:
        # a movement is allowed only while the registry row that publishes this sweep DECLARES it
        # (the row is built from this gate's artifact by data/build_param_tables.py; G-REGEN keeps
        # the two in step). The check reads the shipped registry, not the builder.
        import csv
        reg = list(csv.DictReader(io.open(os.path.join(HERE, "parameters_provenance.csv"), encoding="utf8")))
        row = [r for r in reg if r.get("solvent", "") == "DMA" and "viscosity" in r.get("parameter", "").lower()] or \
              [r for r in reg if "DMA" in r.get("parameter", "") and "mu" in r.get("parameter", "").lower()]
        text = " ".join(r.get("sensitivity", "") for r in row)
        undeclared = sorted({mv["arch"] for mv in moves if ARCH_WORD[mv["arch"]] not in text})
        if undeclared or not row:
            print("\nG-DMAMU: FAIL -- a published count moves inside the interval between the printed viscosity "
                  "and its homolog reading (%s) and the DMA viscosity registry row does not declare it for: %s"
                  % (worst, undeclared or "(no DMA viscosity row found)"))
            return 1
        print("\nG-DMAMU: PASS -- the printed %.3f mPa s is carried; inside the interval down to %.3f the >=%.0f "
              "count moves in %s, and the DMA viscosity row of the registry declares each movement (Table S7b)."
              % (MU_PRINTED, lo, THRESH, ", ".join(ARCH_WORD[a] for a in sorted({m["arch"] for m in moves}))))
        return 0
    print("\nG-DMAMU: PASS -- the printed %.3f mPa s is carried, and nothing published depends on "
          "it: across the whole interval down to %.3f every architecture's >=%.0f count and the "
          "10-of-11 catalyst conclusion are unchanged." % (MU_PRINTED, lo, THRESH))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
