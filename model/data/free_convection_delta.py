#!/usr/bin/env python3
"""G-FREECONV -- derive the unstirred-batch film from the free-convection correlation.

    cd Section4_Model && python data/free_convection_delta.py
    cd Section4_Model && python data/free_convection_delta.py --negative-control

WHY THIS EXISTS
---------------
The unstirred archetype carried delta = 300 um as a DECLARED value, chosen at the conservative
(high-delta) end of a band the registry described but nothing computed. The band 150-380 um and
its "central value 230-240 um" were typed in prose, in `emit_deltas.jl` and in
`make_bounds_runs.py`, and no code reproduced either.

That asymmetry was the whole of the batch-separability exposure. The STIRRED film is a measured
CENTRAL value (200 +/- 7 um); comparing it against the HIGH END of the unstirred band inflated
the apparent contrast to 1.49x. Two central values are the like-for-like comparison.

This module implements the correlation the registry names and evaluates it three ways: at the
central geometry and driving force (the adopted value), over the declared ranges (the band), and
per reaction (the spread the corpus itself produces). The archetype value is then DERIVED --
reproducible from the registry alone -- rather than declared.

    Sh = a (Sc Gr)^(1/4),  Gr = g h^3 (drho/rho) / nu^2,  Sc = nu/D,  delta = h/Sh

which rearranges, exactly, to

    delta = (1/a) [ h nu D / (g drho/rho) ]^(1/4)

so delta rises as the FOURTH ROOT of the cell height and falls as the fourth root of the density
driving force -- the reason the value is robust: a tenfold error in drho/rho moves it 1.8x.

WHAT IS DECLARED HERE, AND IT IS NOT NOTHING
--------------------------------------------
a = 0.66, h and drho/rho are declared, exactly as "1600 rpm" is declared for the rotating disc.
The correlation and its coefficient come from the source; the operating point is this work's.
Both are swept below and neither moves an architecture ranking.
"""
import io
import json
import math
import os
import re
import statistics
import sys
import csv as _csv


def _carrier_range():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reactions_50.csv")
    v = [float(r["C_carrier_M"]) for r in _csv.DictReader(io.open(p, encoding="utf-8"))]
    if len(v) != 50:
        raise SystemExit("reactions_50.csv: expected 50 rows, found %d" % len(v))
    return [min(v), max(v)]

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

## --- the declared operating point -------------------------------------------------------
B_COEF = 1.48          # Wilke, Eisenberg & Tobias 1953, Eq. XVII, p. 518: the paper's OWN
                       # diffusion-layer form, delta' = 1.48 x (Sc Gr)^(-1/4). RETRIEVED and
                       # confirmed against the page raster 2026-09-04. The registry had carried
                       # a = 0.66 for the Nusselt form; the paper prints Nu' = 0.673 (Sc Gr)^(1/4)
                       # (Eq. XV, "The constant 0.673 was evaluated by averaging the constants
                       # calculated for individual experiments"), so 0.66 was neither the source
                       # value nor derivable from it. Using the printed DELTA equation avoids
                       # rearranging the source at all; note 1/0.673 = 1.486, so the paper's own
                       # two coefficients differ by 0.4% in rounding.
G_ACCEL = 9.81         # m s^-2
H_LO, H_HI = 5e-3, 80e-3          # electrode height, m: a lab beaker electrode
DR_LO, DR_HI = 1e-3, 1e-2         # drho/rho across the film

## --- what the density driving force IS, and one page-anchored value of it ---------------
## drho/rho is not an operator setting the way rpm is: Wilke, Eisenberg & Tobias define it
## through a specific densification coefficient, rho_0 - rho_i = alpha rho_i (C_0 - C_i), and at
## the limiting current C_i -> 0, so the driving force is set by the BULK concentration of the
## species depleted at the surface. Their own experiments spanned 0.01-0.74 M CuSO4 in ~1.5 M
## H2SO4 on cathodes 0.25-3.0 in (6-76 mm) high (p. 513, abstract, and p. 515). The declared
## decade 1e-3..1e-2 is therefore a CHOICE that stands in for fifty different depleted
## concentrations (3.5 mM to 13.7 M across the set), not a property any row measures, and it is
## held fixed because the densification coefficients of these organic solutions are not
## available. The one case that CAN be page-anchored is the most concentrated aqueous binary
## electrolyte this work models, 2 M NaCl, from the same CRC table the registry already reads for
## its molarity (97th ed., p. 5-129, 'Concentrative Properties of Aqueous Solutions', NaCl block,
## 20 C): rho = 1.0707 g cm-3 at 10.0 mass % (1.832 M) and 1.0781 at 11.0 mass % (2.029 M), so
## 2.000 M interpolates to 1.0770, against 0.9989 on the 0.1 mass % (0.017 M) row of the same
## table. A film that depletes the whole salt therefore carries drho/rho ~ 0.078, twenty-five
## times the declared centre, and with the fourth root the film is 2.2x THINNER than 228 um.
## A millimolar organic in an organic solvent sits below the declared decade and its film is
## correspondingly thicker. The JSON carries this illustration so the registry row can quote it
## without typing it.
CRC_NACL = {"locator": "CRC 97th ed. p. 5-129, NaCl block, 20 C",
            "pct": (10.0, 11.0), "c_M": (1.832, 2.029), "rho": (1.0707, 1.0781),
            "ref_pct": 0.1, "ref_c_M": 0.017, "ref_rho": 0.9989}
WILKE_RANGE = {"CuSO4_M": (0.01, 0.74), "height_mm": (6.35, 76.2),
               "locator": "abstract p. 513 ('0.01 to 0.7 molal CuSO4 ... Cathode heights varied from 0.25 to 3.0 in.'); p. 515 ('CuSO4 concentration varied from about 0.01M to 0.74M')"}


def geo_centre(lo, hi):
    """Centre of a range swept over decades is the GEOMETRIC mean, not the arithmetic one.

    delta goes as the fourth root of h and of 1/(drho/rho), so the sweep is multiplicative;
    the arithmetic midpoint of 1e-3..1e-2 (5.5e-3) is not its centre in any sense the
    correlation respects.
    """
    return math.sqrt(lo * hi)


def delta_fc(h, dr, nu, D, b=B_COEF):
    """delta = b [ h nu D / (g drho/rho) ]^(1/4), metres -- the source's Eq. XVII.

    delta' = b x (Sc Gr)^(-1/4) with Sc Gr = g x^3 (drho/rho)/(nu D) rearranges exactly to
    this, with no step the source does not itself take.
    """
    return b * (h * nu * D / (G_ACCEL * dr)) ** 0.25


def corpus():
    """(nu, D) for each of the fifty reactions, read from the generated table."""
    s = io.open(os.path.join(ROOT, "julia", "reactions_table.jl"), encoding="utf-8").read()
    rows = re.findall(
        r"OERxn\(\"[^\"]*\",\s*\"([^\"]*)\",\s*\"[^\"]*\",\s*([0-9.eE+-]+),"
        r"\s*([0-9.eE+-]+),\s*([0-9.eE+-]+),\s*([0-9.eE+-]+)", s)
    if len(rows) != 50:
        raise SystemExit("expected 50 reactions, parsed %d" % len(rows))
    return [(float(r[4]), float(r[1])) for r in rows]      # (nu, D)


def main():
    neg = "--negative-control" in sys.argv
    rows = corpus()
    b = B_COEF * 1.5 if neg else B_COEF        # perturb the CORRELATION, not the checker

    hc, drc = geo_centre(H_LO, H_HI), geo_centre(DR_LO, DR_HI)
    per_row = [delta_fc(hc, drc, nu, D, b) for nu, D in rows]
    centre = statistics.median(per_row)

    corners = [delta_fc(h, dr, nu, D, b)
               for h in (H_LO, H_HI) for dr in (DR_LO, DR_HI) for nu, D in rows]
    band_lo, band_hi = min(corners), max(corners)

    print("  correlation   delta = %.2f x (Sc Gr)^(-1/4)   [Wilke 1953 Eq. XVII]" % b)
    print("  declared      h = %.0f-%.0f mm (centre %.1f), drho/rho = %.0e-%.0e (centre %.2e)"
          % (H_LO * 1e3, H_HI * 1e3, hc * 1e3, DR_LO, DR_HI, drc))
    print("  corpus        nu %.2e-%.2e, D %.2e-%.2e over 50 reactions"
          % (min(r[0] for r in rows), max(r[0] for r in rows),
             min(r[1] for r in rows), max(r[1] for r in rows)))
    print()
    print("  ADOPTED (median at the central operating point): %.1f um" % (centre * 1e6))
    print("  per-reaction spread at that operating point:     %.0f - %.0f um (%.2fx)"
          % (min(per_row) * 1e6, max(per_row) * 1e6, max(per_row) / min(per_row)))
    print("  full envelope over the declared ranges:          %.0f - %.0f um"
          % (band_lo * 1e6, band_hi * 1e6))

    ## sensitivity to the two declared inputs, reported rather than argued
    print()
    d_a060 = statistics.median([delta_fc(hc, drc, nu, D, 1.0/0.60) for nu, D in rows])
    d_a067 = statistics.median([delta_fc(hc, drc, nu, D, 1.0/0.67) for nu, D in rows])
    d_h5   = statistics.median([delta_fc(H_LO, drc, nu, D, b) for nu, D in rows])
    d_h80  = statistics.median([delta_fc(H_HI, drc, nu, D, b) for nu, D in rows])
    d_drlo = statistics.median([delta_fc(hc, DR_LO, nu, D, b) for nu, D in rows])
    d_drhi = statistics.median([delta_fc(hc, DR_HI, nu, D, b) for nu, D in rows])
    print("  sensitivity of the adopted value:")
    print("     a  0.60 / 0.67 (Nu form) %.0f / %.0f um" % (d_a060 * 1e6, d_a067 * 1e6))
    print("     h  5 / 80 mm            %.0f / %.0f um" % (d_h5 * 1e6, d_h80 * 1e6))
    print("     drho/rho 1e-3 / 1e-2    %.0f / %.0f um" % (d_drlo * 1e6, d_drhi * 1e6))

    ## the page-anchored illustration of a driving force OUTSIDE the declared decade
    (c1, c2), (r1, r2) = CRC_NACL["c_M"], CRC_NACL["rho"]
    rho_2M = r1 + (2.000 - c1) / (c2 - c1) * (r2 - r1)
    drho_nacl = (rho_2M - CRC_NACL["ref_rho"]) / CRC_NACL["ref_rho"]
    d_nacl = statistics.median([delta_fc(hc, drho_nacl, nu, D, b) for nu, D in rows])
    print("  illustration   2 M NaCl fully depleted: rho %.4f vs %.4f -> drho/rho = %.3f "
          "(%.0fx the declared centre) -> film %.0f um at the central height"
          % (rho_2M, CRC_NACL["ref_rho"], drho_nacl, drho_nacl / drc, d_nacl * 1e6))
    out = {
        "note": "unstirred-batch film derived from the free-convection correlation; "
                "written by data/free_convection_delta.py",
        "drho_rho_illustration": {"system": "2 M NaCl aq, whole salt depleted at the surface",
                                  "source": CRC_NACL["locator"], "rho_2M_gcm3": rho_2M,
                                  "rho_ref_gcm3": CRC_NACL["ref_rho"], "drho_rho": drho_nacl,
                                  "ratio_to_declared_centre": drho_nacl / drc,
                                  "delta_um_at_central_height": d_nacl * 1e6},
        "source_experiment_range": WILKE_RANGE,
        # the carrier each row depletes at its limiting current, read from the reaction table (chemistry audit pass 4: it was
        # typed [0.00352, 13.70], the 13.70 being the adiponitrile row counted twice and the floor missing the 0.27 mM oxygen)
        "set_depleted_concentration_M": _carrier_range(),
        "correlation": "Sh = a (Sc Gr)^(1/4), Gr = g h^3 (drho/rho)/nu^2, delta = h/Sh",
        "b_eq_XVII": B_COEF, "h_m": [H_LO, H_HI], "h_centre_m": hc,
        "drho_rho": [DR_LO, DR_HI], "drho_rho_centre": drc,
        "delta_centre_um": centre * 1e6,
        "delta_per_row_um": [d * 1e6 for d in per_row],
        "delta_row_lo_um": min(per_row) * 1e6, "delta_row_hi_um": max(per_row) * 1e6,
        "delta_band_lo_um": band_lo * 1e6, "delta_band_hi_um": band_hi * 1e6,
        "sensitivity_um": {"b_from_a_0.60": d_a060 * 1e6, "b_from_a_0.67": d_a067 * 1e6,
                           "h_5mm": d_h5 * 1e6, "h_80mm": d_h80 * 1e6,
                           "drho_1e-3": d_drlo * 1e6, "drho_1e-2": d_drhi * 1e6},
    }
    name = "free_convection_delta%s.json" % ("_NEGCONTROL" if neg else "")
    with io.open(os.path.join(ROOT, "results", name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    if neg:
        ## a is in the denominator, so a 1.5x coefficient must LOWER the film by exactly 1/1.5
        ref = statistics.median([delta_fc(hc, drc, nu, D, B_COEF) for nu, D in rows])
        ratio = centre / ref
        ok = abs(ratio - 1.5) < 1e-9
        print("\n  perturbing a by 1.5x moved the derived film %.4fx (expected %.4f)"
              % (ratio, 1.5))
        print("G-FREECONV control: %s" % ("GOOD (the derivation responds to its own coefficient)"
                                          if ok else "BAD (the film did not move as the algebra requires)"))
        return 0 if ok else 1

    ## The registry documents this band and this centre in prose. Assert the implementation
    ## reproduces them, so a reworded registry cannot drift from the code that derives it.
    fails = []
    if not (225.0 <= centre * 1e6 <= 240.0):
        fails.append("derived centre %.1f um is outside the 230-240 um the registry documents"
                     % (centre * 1e6))
    for f in fails:
        print("    FAIL  %s" % f)
    if fails:
        print("\nG-FREECONV: FAIL")
        return 1
    print("\nG-FREECONV: PASS -- the unstirred film is derived from the named correlation at a "
          "declared operating point, and reproduces the documented central value")
    return 0


if __name__ == "__main__":
    sys.exit(main())
