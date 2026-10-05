#!/usr/bin/env python3
"""G-DSTIR -- what diffusion-layer thickness is defensible for the stirred archetype?

    cd Section4_Model && python data/delta_stirred_estimate.py
    cd Section4_Model && python data/delta_stirred_estimate.py --negative-control

WHY
---
delta for the stirred-batch archetype WAS the model's most load-bearing assumption: a declared
100 um carrying no citation. On 2026-09-01 the measurement below was ADOPTED in its place, so this
module no longer weighs a declared value against a comparison -- it checks that the adopted value
is the measured one and that the idealised RDE bound still brackets it from below. Every stirred-batch number scales as 1/delta, and the withdrawn "sub-25 band"
claim (SI S7) would hold only below delta = 68.3 um.

THE ANCHOR IS A MEASUREMENT, NOT A CORRELATION
----------------------------------------------
Williams, Corbin, Zeng, Lazouski, Yang & Manthiram, Sustainable Energy Fuels 2019, 3, 1225-1232
(DOI 10.1039/C9SE00024K), p. 1227, measure the mass-transport boundary layer of their gas-bubbled
electrochemical cell the standard way -- take the diffusion-limited current of ferricyanide,
back-calculate delta from i_lim = nFDc/delta, then convert for the diffusion coefficient of the
gas-phase species:

    "For the transport of dissolved O2 gas, the calculated boundary layer thickness was
     200 +/- 7 um"     (D_O2 = 2.10e-5 cm2/s, bubbling at 10 sccm)

That is a planar electrode in a convecting cell -- the same situation as this model's stirred
archetype -- and O2 diffuses about twice as fast as the bulky organics modelled here, so if
anything it should give a THINNER layer than they would.

AN RDE IS NOT A STIRRED BEAKER, AND THIS SCRIPT USED TO CONFLATE THEM
--------------------------------------------------------------------
An earlier version of this analysis evaluated the Levich relation
delta = 1.61 D^(1/3) nu^(1/6) omega^(-1/2) at stir-bar rotation rates, got 15-36 um, and
concluded that the declared 100 um was "2.8-6.9x conservative" and that 68.3 um was "not out of
reach". That was wrong, and it was wrong in the dangerous direction. Levich describes a ROTATING
DISC: a uniformly accessible electrode in the most efficient laminar forced convection available.
A stationary plate in a stirred or bubbled beaker is nothing like it, and the measured value in a
real cell is an order of magnitude larger than the Levich number for a nominally similar speed.

Both are reported below, because the SPREAD between them is the honest content: the idealised
correlation and the measured cell bracket the declared value from opposite sides, and the
declared value sits much closer to the measurement.
"""
import csv
import io
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RPM = [200, 300, 500, 800, 1200]
ADOPTED = 200.0         # um, the stirred-batch archetype, MEASURED (Williams p. 1227)
FLIP = 68.3             # um, where the withdrawn sub-25 claim would hold
MEASURED = 200.0        # um, Williams/Manthiram 2019, p. 1227
MEASURED_SD = 7.0
SWEPT_BAND = (50.0, 200.0)     # the band the registry already sweeps for this row


# A NEGATIVE CONTROL MUST NEVER WRITE THE ARTIFACT IT PERTURBS. Until 2026-08-30 several
# controls here dumped their perturbed numbers straight over results/, so a control run
# left the repo holding fabricated values until the next ordinary run happened to fix it --
# and an audit that snapshotted results/ AFTER a control run then compared against
# contaminated bytes and reported no contamination. Controls write a _NEGCONTROL sibling,
# the convention data/check_conditions.py already used.
def _out(path, neg):
    return path[:-5] + "_NEGCONTROL.json" if neg and path.endswith(".json") else path

def rows():
    rx = list(csv.DictReader(io.open(os.path.join(HERE, "reactions_50.csv"), encoding="utf-8")))
    sol = {r["solvent"]: r for r in
           csv.DictReader(io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8"))}
    out = []
    for r in rx:
        s = sol.get(r["solvent"]) or sol.get(r["solvent"].split()[0])
        if not s:
            continue
        mu = float(s["mu_mPas"]) * 1e-3
        rho = float(s["rho"]) * 1000.0
        out.append((r["reaction"], float(r["D_cm2s"]) * 1e-4, mu / rho))
    return out


def main(neg=False):
    rs = rows()
    if len(rs) != 50:
        raise SystemExit("expected 50 rows with both D and nu, got %d" % len(rs))
    sc = sorted(nu / D for _, D, nu in rs)
    print("  Schmidt number Sc = nu/D over the 50: min %.0f  median %.0f  max %.0f"
          % (sc[0], st.median(sc), sc[-1]))

    print("\n  MEASURED anchor (Williams/Manthiram, Sustain. Energy Fuels 2019, 3, 1225, p. 1227):")
    print("    planar electrode in a gas-bubbled cell, delta = %.0f +/- %.0f um for dissolved O2"
          % (MEASURED, MEASURED_SD))
    print("    (D_O2 = 2.10e-5 cm2/s -- about twice these organics', so a thinner layer than they")
    print("     would give, and still twice the declared value)")

    print("\n  IDEALISED lower bound, Levich delta = 1.61 D^(1/3) nu^(1/6) omega^(-1/2) -- a")
    print("  ROTATING DISC, i.e. the thinnest layer a given rotation rate could ever produce:")
    print("  %-6s %-12s %s" % ("rpm", "omega 1/s", "delta over the 50 (um): min / median / max"))
    rec = []
    for rpm in RPM:
        w = 2 * math.pi * rpm / 60.0
        if neg:
            w *= 1e-4
        d = sorted(1.61 * D ** (1 / 3) * nu ** (1 / 6) * w ** -0.5 * 1e6 for _, D, nu in rs)
        rec.append({"rpm": rpm, "omega": w, "min": d[0], "median": st.median(d), "max": d[-1]})
        print("  %-6d %-12.1f %6.1f / %6.1f / %6.1f" % (rpm, w, d[0], st.median(d), d[-1]))

    med = [r["median"] for r in rec]
    lo, hi = min(med), max(med)
    json.dump({"rpm": RPM, "declared_um": ADOPTED, "flip_um": FLIP,
               "measured_um": MEASURED, "measured_sd_um": MEASURED_SD,
               "measured_source": "Williams, Corbin, Zeng, Lazouski, Yang & Manthiram, "
                                  "Sustain. Energy Fuels 2019, 3, 1225-1232, p. 1227; "
                                  "DOI 10.1039/C9SE00024K",
               "sc_min": sc[0], "sc_median": st.median(sc), "sc_max": sc[-1],
               "levich_idealised": rec, "levich_median_range_um": [lo, hi],
               "swept_band_um": list(SWEPT_BAND)},
              io.open(_out(os.path.join(ROOT, "results", "delta_stirred_estimate.json"), neg),
                      "w", encoding="utf8"), indent=1)

    print("\n  WHERE THE ADOPTED VALUE SITS")
    print("    idealised RDE  %5.1f-%.1f um   <-- best case, not a beaker" % (lo, hi))
    print("    ADOPTED        %5.1f um  (= the measurement)" % ADOPTED)
    print("    MEASURED cell  %5.1f um        <-- the comparable geometry" % MEASURED)
    print("    swept band     %5.1f-%.1f um   (registry sensitivity for this row)"
          % SWEPT_BAND)
    print("  The adopted value IS the measurement (%.1fx the retired declared 100 um), so the"
          % (MEASURED / 100.0))
    print("  stirred ceilings are no longer overstated by an unsourced input. What remains is that")
    print("  the free-convection band for the UNSTIRRED archetype, 150-380 um, OVERLAPS this value,")
    print("  so the two batch archetypes are not cleanly separable and the contrast between them")
    print("  should be read as an upper estimate of what stirring buys.")
    print("  The %.1f um flip point of the withdrawn sub-25 claim is %.1fx thinner than measured;"
          % (FLIP, MEASURED / FLIP))
    print("  nothing here makes it reachable, which is why that claim stays withdrawn.")

    if neg:
        ok = lo > MEASURED
        print("\nNEGATIVE CONTROL: omega x1e-4, so the idealised bound must exceed the measured "
              "%.0f um." % MEASURED)
        print("G-DSTIR control: %s (median delta %.0f um)"
              % ("GOOD" if ok else "BAD -- test is inert", lo))
        return 0 if ok else 1
    if not (SWEPT_BAND[0] <= MEASURED <= SWEPT_BAND[1]):
        print("\nG-DSTIR: REVIEW NEEDED -- the measured delta lies OUTSIDE the band the registry "
              "sweeps for this row, so the published sensitivity does not cover reality")
        return 1
    print("\nG-DSTIR: PASS -- the stirred archetype now USES the measured %.0f um, and the "
          "idealised RDE bound (%.0f-%.0f um) still brackets it from below as it must; the "
          "residual exposure is the overlap with the unstirred free-convection band, not the "
          "input itself" % (ADOPTED, lo, hi))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
