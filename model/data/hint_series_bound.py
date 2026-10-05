#!/usr/bin/env python3
"""G-HINT -- can the internal film coefficient move any thermal verdict?

    cd Section4_Model && python data/hint_series_bound.py
    cd Section4_Model && python data/hint_series_bound.py --negative-control

WHY
---
A reaction-engineering reviewer asks the right question about the thin-gap microfluidic row: the
model lumps the internal heat transfer into a single h_int = 5000 W m-2 K-1, but at that gap the
thermal entry length is a large fraction of the channel and axial conduction is not obviously
negligible, so a fully developed Nusselt number is the wrong basis. Both objections are correct
as physics.

They are also unable to change anything, and the reason is structural rather than numerical.
h_int sits in SERIES with the external film H_EXT:

    U' = [ 1/h_int + 1/H_EXT ]^-1 * sigma

H_EXT is 13 W m-2 K-1 (natural convection plus linearised radiation to room air). Every h_int in
the model is between 8x and 380x larger, so the external film is the controlling resistance and
h_int is a small correction to it. Entry length and axial conduction are corrections to h_int --
corrections to the term that is already almost irrelevant. This computes the bound instead of
asserting it, by pushing h_int to INFINITY, which is the strongest any internal-flow refinement
could ever be.

WHAT THE BOUND IS, AND WHERE IT IS NOT SMALL
--------------------------------------------
The bound is tightest exactly where the reviewer aimed: for the thinnest-gap row, h_int ->
infinity moves U' by well under one percent. It is loosest for the unstirred beaker, whose declared
h_int = 100 is only ~8x H_EXT, where the boil-off ceilings move by several percent. That is
already the registry's stated -5/+6%, and this gate keeps it honest: it FAILS if any verdict
flips anywhere in the sweep, not if a number moves.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "figs"))

SWEEP = [50.0, 100.0, 200.0, 800.0, 2000.0, 5000.0, 2.0e4, float("inf")]


def main(neg=False):
    import thermal_model as T

    hext = T.H_EXT
    if neg:
        # Make the internal film the CONTROLLING resistance by collapsing the external one.
        # Perturbing h_int itself would only re-run the sweep the gate already does; the claim
        # under test is that the SERIES puts h_int in the minor role, so the control removes
        # exactly that.
        T.H_EXT = 1.0e9
        hext = T.H_EXT

    print("  U' = [1/h_int + 1/H_EXT]^-1 * sigma,  H_EXT = %.4g W m-2 K-1" % hext)
    print("\n  how much can h_int alone move U', per reactor row (declared -> infinity):")
    rows = {}
    for lab, gap, sigma, h_int, i_design in T.REACTORS:
        name = lab.replace("\n", " ")
        u_dec = T.U_passive(sigma, h_int)
        u_inf = sigma * hext * 1e-4
        u_lo = T.U_passive(sigma, min(SWEEP))
        # TWO DIFFERENT PERTURBATIONS, deliberately not combined into one number.
        # `up` is the rigorous bound on any refinement that RAISES h_int -- entry-length and
        # developing-flow corrections both do, so this is the one that answers the reviewer, and
        # h_int -> infinity is the strongest such correction that can exist.
        # `down` is the drop to the bottom of the whole sweep (50, free convection in liquids),
        # which is not a physical h_int for a forced microchannel at all. An earlier version
        # took max(up, down) and reported 25.67% for the 250 um row, which reads as though the
        # reviewer's objection were large when the quantity it actually bounds is 0.26%.
        up = u_inf / u_dec - 1.0
        down = 1.0 - u_lo / u_dec
        rows[name] = {"gap_m": gap, "sigma": sigma, "h_int": h_int, "i_design": i_design,
                      "U_declared": u_dec, "U_hint_infinite": u_inf, "U_hint_lowest": u_lo,
                      "rel_change_up": up, "rel_change_down": down,
                      "h_int_over_hext": h_int / hext}
        print("    %-24s h_int/H_EXT %7.1f   U' %.6f  ->inf %+.2f%%   ->%g %+.2f%%"
              % (name, h_int / hext, u_dec, 100 * up, min(SWEEP), -100 * down))

    # the verdict that actually matters: does i_design clear the boil-off ceiling, anywhere?
    print("\n  boil-off verdicts across the whole sweep (i_design vs i_boil):")
    flips, table = [], {}
    beaker = T.BEAKER
    for lab, el, kap, Tb in [(r[0], r[1], r[2], r[3]) for r in T.SOLVENTS]:
        vals = [T.i_boil(kap, beaker[1], Tb, T.U_passive(beaker[2], h)) for h in SWEEP]
        verd = set(v >= beaker[4] for v in vals)
        table[lab] = {"i_boil": vals, "i_design": beaker[4], "verdict_constant": len(verd) == 1}
        if len(verd) != 1:
            flips.append(lab)
        print("    %-12s i_boil %7.1f -> %7.1f mA cm-2 vs i_design %5.1f   verdict %s"
              % (lab, vals[0], vals[-1], beaker[4],
                 "CONSTANT" if len(verd) == 1 else "FLIPS"))

    # The thin-gap row is selected by its GEOMETRY, never by a substring of its label: this
    # gate selected it with `"250" in k` and went silently vacuous the day the archetype became
    # the 25 um microfluidic cell -- `thin` empty, the headline bound None, PASS printed anyway.
    # `preparative` excludes the zero-gap stack, which is an industrial reference rather than a
    # modelled archetype and would otherwise always win the minimum.
    preparative = {k: v for k, v in rows.items() if "zero-gap" not in k}
    _thin_gap = min(v["gap_m"] for v in preparative.values())
    thin = [v for v in preparative.values() if v["gap_m"] == _thin_gap]
    thin_name = [k for k, v in preparative.items() if v["gap_m"] == _thin_gap]
    if len(thin) != 1:
        print("\nG-HINT: FAIL -- the thinnest-gap preparative row is not unique (%s); the bound "
              "this gate reports has no single row to belong to." % ", ".join(thin_name))
        return 1
    json.dump({"H_EXT": hext, "sweep": [s for s in SWEEP if s != float("inf")] + ["inf"],
               "reactors": rows, "boiloff": table, "flips": flips,
               "thin_gap_row": thin_name[0], "thin_gap_m": _thin_gap,
               "thin_gap_rel_change_up": thin[0]["rel_change_up"]},
              io.open(os.path.join(ROOT, "results", "hint_series_bound%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)

    if neg:
        print("\nNEGATIVE CONTROL: H_EXT collapsed to 1e9, so the internal film becomes the "
              "controlling resistance and the 'h_int cannot matter' bound must break.")
        worst = max(r["rel_change_up"] for r in rows.values())
        ok = worst > 0.5
        print("G-HINT control: %s (largest U' movement %.0f%%)"
              % ("GOOD (the bound is broken as it must be)" if ok else
                 "BAD -- test is inert", 100 * worst))
        return 0 if ok else 1
    if flips:
        print("\nG-HINT: FAIL -- a boil-off verdict changes inside the h_int sweep: %s"
              % ", ".join(flips))
        return 1
    thin_pct = 100 * thin[0]["rel_change_up"]
    print("\nG-HINT: PASS -- h_int is in series with an external film %.0fx to %.0fx smaller. "
          "Pushing it to INFINITY -- the strongest form any entry-length or developing-flow "
          "correction could take -- moves U' by %.2f%% on the %s row (%.0f um gap, the thinnest "
          "preparative archetype) and by at most %.2f%% on "
          "any row, so the objection cannot reach a published number. Ceilings DO move -- the "
          "DMF beaker ceiling the registry quotes runs %.1f -> %.1f mA cm-2 across the sweep, "
          "and the largest movement of any single solvent's ceiling is %.0f%% -- but no verdict "
          "flips at any h_int in the sweep."
          % (min(r["h_int_over_hext"] for r in rows.values()),
             max(r["h_int_over_hext"] for r in rows.values()), thin_pct,
             thin_name[0].replace("\n", " ").replace("$\\mu$", "u"), _thin_gap * 1e6,
             100 * max(r["rel_change_up"] for r in rows.values()),
             table["DMF"]["i_boil"][0], table["DMF"]["i_boil"][-1],
             100 * max(max(v["i_boil"]) / min(v["i_boil"]) - 1.0 for v in table.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
