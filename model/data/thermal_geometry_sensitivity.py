#!/usr/bin/env python3
"""G-THERMGEO -- the bound on the thermal geometry the exemplars do not state.

WHY THIS EXISTS.  A transport archetype is fixed by one measured quantity, its diffusion layer.
A thermal archetype needs three quite different ones: the inter-electrode GAP (which sets the
ohmic heat), the heat-rejection area ratio SIGMA = A_ext/A_elec, and the internal film h_int.
An exemplar that measures delta need state none of them, and for the seven-archetype table only
two gaps are sourceable -- Mo's 25 um FEP spacer (measured) and Eisenberg's annulus (derived).
Three rows INHERIT the declared beaker gap (recirculating flow, ANEC, RDE) and three inherit or
derive its sigma.  h_int is bounded separately and to infinity by data/hint_series_bound.py.

WHAT IT DOES *NOT* DO.  It invents no geometry.  There is no source for the electrode separation
in Watkins' recirculating H-cell, so this file does not manufacture a band and call it one.  It
sweeps each declared quantity and reports the BREAKING POINT -- the multiple of the declared
value at which a published verdict would change -- which is the pattern G-MUSOLN established for
the solution viscosity the model cannot measure.  A reader then judges the declared value against
a stated distance, instead of against an invented interval.

THE ONE STRUCTURAL RESULT.  The gap enters q only through the ohmic term:

    q = [ 2 b asinh(i/2 i0)  +  i L / kappa ] * i        (the first term carries no L)

so as L -> 0 the dissipation does not vanish; it falls to the KINETIC floor.  Every cell therefore
has a boil-off ceiling that no electrode geometry whatsoever can raise, and a verdict that still
reads "boils" at L = 0 is immune to the inherited gap entirely -- not bounded by it, independent
of it.  That is a stronger statement than any band, and it is what this gate reports first.

REGISTERED as G-THERMGEO in run_gates.sh (fast tier: it takes about a second). It bounds the
SEVEN-archetype thermal table, so it could not be registered while that table was staged; it landed
with the table on 2026-09-12. thermal_model.py's comment block cites it at this path.

Run:  python3.12 thermal_geometry_sensitivity.py [--negative-control]
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "figs"))
S4 = ROOT
STAGE = os.path.join(ROOT, "results")

import thermal_model as TM

# Which of the three thermal quantities each row actually has a source for.  The sweep is ABOUT
# the rows marked inherited or declared; the two sourced gaps are swept as well, so the gate
# reports one table rather than two, but they are not what it exists to bound.
GAP_STATE = {"unstirred batch": "declared", "stirred batch": "declared",
             "recirculating flow": "inherited", "ANEC flow cell": "inherited",
             "microfluidic 25 um": "measured", "RDE 1600 rpm": "inherited",
             "rotating cyl. 3000 rpm": "derived", "zero-gap PEM stack": "reference"}
SIG_STATE = {"unstirred batch": "derived", "stirred batch": "derived",
             "recirculating flow": "inherited", "ANEC flow cell": "inherited",
             "microfluidic 25 um": "declared", "RDE 1600 rpm": "derived",
             "rotating cyl. 3000 rpm": "inherited", "zero-gap PEM stack": "reference"}

short = lambda n: n.replace("\n", " ").replace("$\\mu$m", "um")
SOLV = [s[0] for s in TM.SOLVENTS]
KAP = {s[0]: s[2] for s in TM.SOLVENTS}
TB = {s[0]: s[3] for s in TM.SOLVENTS}


def margin(kappa, gap, Tb, sigma, h_int, i_des):
    return TM.i_boil(kappa, gap, Tb, TM.U_passive(sigma, h_int)) / i_des


def cross(f, lo, hi, n=200):
    """Smallest x in [lo, hi] where f changes sign, by bisection; None if it never does."""
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(n):
        mid = np.sqrt(lo * hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return np.sqrt(lo * hi)


def run(design_scale=1.0):
    rows, immune, flips = [], [], []
    for lab, gap0, sig0, hint, i_des0 in TM.REACTORS:
        name = short(lab)
        i_des = i_des0 * design_scale
        for s in SOLV:
            k, Tb = KAP[s], TB[s]
            m0 = margin(k, gap0, Tb, sig0, hint, i_des)
            # The kinetic floor: the ceiling no electrode geometry can raise.
            m_zero = margin(k, 1e-12, Tb, sig0, hint, i_des)
            gstar = cross(lambda g: margin(k, g, Tb, sig0, hint, i_des) - 1.0,
                          1e-6, 1.0)
            sstar = cross(lambda sg: margin(k, gap0, Tb, sg, hint, i_des) - 1.0,
                          1e-3, 1e4)
            rec = {"arch": name, "solvent": s, "gap_state": GAP_STATE[name],
                   "sigma_state": SIG_STATE[name], "margin": m0,
                   "margin_zero_gap": m_zero, "verdict": "survives" if m0 >= 1 else "boils",
                   "gap_flip_m": gstar, "gap_flip_x": (gstar / gap0) if gstar else None,
                   "sigma_flip": sstar, "sigma_flip_x": (sstar / sig0) if sstar else None}
            rows.append(rec)
            if m0 < 1 and m_zero < 1:
                immune.append(rec)
            if m0 < 1 and m_zero >= 1:
                flips.append(rec)
    return rows, immune, flips


def report(rows, immune, flips, label=""):
    print("\nBASE MARGIN  (boil-off ceiling / transport ceiling; < 1 means the solvent boils "
          "before the cell reaches the current transport allows)%s" % label)
    print("  %-24s %-10s %s" % ("architecture", "gap", "  ".join("%9s" % s for s in SOLV)))
    for lab, gap0, _s, _h, _i in TM.REACTORS:
        n = short(lab)
        vals = [r for r in rows if r["arch"] == n]
        cells = "  ".join("%9.2f" % next(r["margin"] for r in vals if r["solvent"] == s)
                          for s in SOLV)
        print("  %-24s %-10s %s" % (n, GAP_STATE[n], cells))

    print("\nAT ZERO GAP -- the ohmic term removed entirely, leaving only the kinetic floor")
    print("  %-24s %s" % ("architecture", "  ".join("%9s" % s for s in SOLV)))
    for lab, _g, _s, _h, _i in TM.REACTORS:
        n = short(lab)
        vals = [r for r in rows if r["arch"] == n]
        cells = "  ".join("%9.2f" % next(r["margin_zero_gap"] for r in vals if r["solvent"] == s)
                          for s in SOLV)
        print("  %-24s %s" % (n, cells))

    print("\nIMMUNE TO THE GAP: %d of %d cells boil at the declared gap AND still boil at zero gap."
          % (len(immune), len(rows)))
    for r in immune:
        print("    %-24s %-9s margin %.2f -> %.2f at L = 0   (gap %s)"
              % (r["arch"], r["solvent"], r["margin"], r["margin_zero_gap"], r["gap_state"]))
    print("\nRESCUABLE BY THINNING THE GAP: %d cells boil as declared but clear at some thinner gap."
          % len(flips))
    for r in flips:
        print("    %-24s %-9s would need L <= %.3g mm (%.3gx the declared %.3g mm)"
              % (r["arch"], r["solvent"], r["gap_flip_m"] * 1e3, r["gap_flip_x"],
                 next(g for l, g, _a, _b, _c in TM.REACTORS if short(l) == r["arch"]) * 1e3))

    print("\nBREAKING POINTS on the rows whose gap is INHERITED (the ones this gate exists for)")
    for r in rows:
        if r["gap_state"] != "inherited":
            continue
        g = "no flip in [1e-6, 1] m" if r["gap_flip_x"] is None else "flips at %.2fx" % r["gap_flip_x"]
        sg = "no flip" if r["sigma_flip_x"] is None else "flips at %.2fx" % r["sigma_flip_x"]
        print("    %-24s %-9s %-9s gap %-24s sigma %s"
              % (r["arch"], r["solvent"], r["verdict"], g, sg))


_WORD = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10}


def _num(tok):
    return _WORD.get(tok.lower(), int(tok) if tok.isdigit() else None)


def _check_si_counts(n_sigma, n_shared, n_arch):
    """Bind the two counts this sweep produces to the sentences that publish them.

    Returns (ok, notes).  Each claim must be PRESENT -- a missing sentence fails, because a
    phrase check that stops matching is a check that stopped checking.
    """
    import re
    import unicodedata
    import zipfile
    si = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")
    if not os.path.exists(si):
        return False, ["SI not built, so the published counts cannot be checked"]
    sys.path.insert(0, os.path.join(ROOT, "data"))
    from docx_text import mark_subscripts
    xml = zipfile.ZipFile(si).read("word/document.xml").decode("utf8")
    txt = unicodedata.normalize("NFKC", re.sub("<[^>]+>", "", mark_subscripts(xml)))
    notes, ok = [], True

    m = re.search(r"([A-Za-z]+|\d+)\s+verdicts turn over within a factor of", txt)
    if m is None:
        ok = False
        notes.append("SI: the sigma breaking-point sentence is ABSENT (S6.4)")
    elif _num(m.group(1)) != n_sigma:
        ok = False
        notes.append("SI: S6.4 says %s verdicts turn over on sigma; the sweep gives %d"
                     % (m.group(1), n_sigma))
    else:
        notes.append("SI: S6.4's sigma count (%s) matches the sweep" % m.group(1))

    m = re.search(r"([A-Za-z]+|\d+) of the ([a-z]+|\d+) archetypes share this gap", txt,
                  re.IGNORECASE)
    if m is None:
        ok = False
        notes.append("SI: the shared-gap sentence is ABSENT (Table S7, beaker gap row)")
    elif (_num(m.group(1)), _num(m.group(2))) != (n_shared, n_arch):
        ok = False
        notes.append("SI: the beaker-gap row says %s of the %s archetypes share the gap; "
                     "the model gives %d of %d" % (m.group(1), m.group(2), n_shared, n_arch))
    else:
        notes.append("SI: the shared-gap count (%s of %s) matches the model"
                     % (m.group(1), m.group(2)))
    return ok, notes


def main():
    neg = "--negative-control" in sys.argv
    rows, immune, flips = run()
    report(rows, immune, flips)

    # ---- the claims the figure makes, asserted against the sweep -----------------------------
    # Two of these were stated more strongly than the sweep supports, and the first version of
    # this gate FAILED on both.  They are corrected here rather than loosened.
    #
    #  (i) "five rows share the 2 cm path, so their boil-off ceilings are FLAT" -- not flat.
    #      They differ by 5.7-6.0 % per solvent, because h_int runs 100 -> 2000 W m-2 K-1 across
    #      them.  That the spread is only 6 % is itself the point: the external film H_EXT = 13
    #      dominates the series, the same reason h_int taken to infinity moves U' by 0.26 %
    #      (data/hint_series_bound.py).  So the claim is a MEASURED spread set against the
    #      transport ladder's own span, not an assertion of equality.
    # (ii) "both rotating cells boil in every organic AT ANY GAP" -- false, and this is the
    #      exposure the gate exists to find.  Their gap is inherited, and MeCN and DMF clear at
    #      0.73x / 0.75x of it (RDE) and 0.47x / 0.49x (rotating cylinder).  A rotating cell built
    #      with 1.2-1.5 cm of separation instead of 2 cm reverses those four verdicts.  Only the
    #      THF verdicts are robust: they need a gap under ~1.6 mm, which is no longer a
    #      beaker-scale cell.  The four MeCN/DMF verdicts are CONDITIONAL on an inherited number
    #      and must be declared wherever they are published.
    ORG = ["THF", "MeCN", "DMF"]
    ROT = ("RDE 1600 rpm", "rotating cyl. 3000 rpm")
    ceil = {}
    for lab, g, sg, hi, _i in TM.REACTORS:
        ceil[short(lab)] = {s: TM.i_boil(KAP[s], g, TB[s], TM.U_passive(sg, hi)) for s in SOLV}
    ides = {short(l): d for l, _g, _s, _h, d in TM.REACTORS}

    shared = [short(l) for l, g, _a, _b, _c in TM.REACTORS if abs(g - TM.GAP_BEAKER) < 1e-12]
    spread = max((max(ceil[n][s] for n in shared) - min(ceil[n][s] for n in shared))
                 / max(ceil[n][s] for n in shared) for s in SOLV)
    tspan = max(ides[n] for n in shared) / min(ides[n] for n in shared)
    ident = [n for n in shared
             if all(abs(ceil[n][s] - ceil["recirculating flow"][s]) < 1e-9 for s in SOLV)]
    ispan = max(ides[n] for n in ident) / min(ides[n] for n in ident)

    micro_ok = all(margin(KAP[s], TM.GAP_MICRO, TB[s], 7.0, 5000.,
                          ides["microfluidic 25 um"]) >= 1 for s in ORG)
    thf_robust = all(r["gap_flip_m"] is not None and r["gap_flip_m"] <= 2.0e-3
                     for r in rows if r["arch"] in ROT and r["solvent"] == "THF")
    conditional = [{"arch": r["arch"], "solvent": r["solvent"], "verdict": r["verdict"],
                    "flips_at_gap_x": r["gap_flip_x"], "flips_at_gap_mm": r["gap_flip_m"] * 1e3}
                   for r in rows if r["gap_state"] in ("inherited", "declared") and r["gap_flip_x"]
                   and 1 / 2.5 <= r["gap_flip_x"] <= 2.5]
    # 2026-10-07 (audit pass 28): the list was "every MeCN/DMF cell at a rotating electrode", which counted the rotating
    # cylinder although its gap is derived from Eisenberg (2.435 cm), not inherited, and which reverses only at 0.39-0.40x
    # of it. It is now every inherited or declared gap that reverses within the same factor of 2.5 used for sigma: the
    # rotating disc in MeCN and DMF, at 0.66x.
    # SIGMA IS THE OTHER UNSOURCED GEOMETRIC TERM, and the row that declares it must say what it is
    # worth. Until 2026-09-12 this gate swept sigma and printed the breaking points but published
    # only the gap side, so the sigma row carried a sensitivity about a different quantity. A cell
    # with twice the outer surface per unit of electrode is an ordinary variation, so the threshold
    # is the same factor of 2.5 used for the gap.
    cond_sigma = [{"arch": r["arch"], "solvent": r["solvent"], "verdict": r["verdict"],
                   "flips_at_sigma_x": r["sigma_flip_x"]}
                  for r in rows if r["sigma_state"] in ("inherited", "derived")
                  and r["sigma_flip_x"] is not None and 0.4 <= r["sigma_flip_x"] <= 2.5]

    print("\n--- claims ---")
    print("  %d rows on the 2 cm ohmic path: %s" % (len(shared), ", ".join(shared)))
    print("  their boil-off ceilings span %.1f%%, their transport ceilings %.1fx"
          % (100 * spread, tspan))
    print("  identical thermal geometry, hence identical ceilings: %s (transport span %.2fx)"
          % (", ".join(ident), ispan))
    print("  microfluidic cell survives all three organics: %s" % micro_ok)
    print("  THF boils at both rotating cells for any gap above ~1.6 mm: %s" % thf_robust)
    print("  CONDITIONAL on sigma, the other unsourced geometric term -- declare wherever published:")
    for c in cond_sigma:
        print("      %-24s %-5s %-8s reverses at %.2fx the area ratio"
              % (c["arch"], c["solvent"], c["verdict"], c["flips_at_sigma_x"]))
    print("  CONDITIONAL on the declared gap -- declare wherever published:")
    for c in conditional:
        print("      %-24s %-5s %-8s reverses at %.2fx the gap (%.1f mm)"
              % (c["arch"], c["solvent"], c["verdict"], c["flips_at_gap_x"], c["flips_at_gap_mm"]))

    # THE COUNTS MUST BE THE ONES THE DOCUMENTS PRINT, not just the ones this gate computes.
    # Until 2026-09-12 the gate asserted len(conditional) == 4 and published the sigma list, but
    # nothing compared either number with the sentence that states it: S6.4 said "five verdicts
    # turn over within a factor of 2.5" of sigma where the sweep gives four, and the beaker-gap
    # row said "FIVE of the seven archetypes share this gap" where four of six do. Both drifted
    # when the reactor table changed, behind a green gate. `si_counts` reads them back out of the
    # built SI and fails on disagreement; a vanished sentence is a FAIL, not a pass (trap 10).
    si_ok, si_notes = _check_si_counts(len(cond_sigma), len(shared), len(rows) // 4)
    for note in si_notes:
        print("  %s" % note)

    ok = (spread <= 0.07 and tspan >= 10.0 and len(ident) == 2 and ispan >= 5.0
          and micro_ok and thf_robust and len(conditional) == 2 and si_ok)

    if neg:
        # Drop every transport ceiling tenfold.  The two rotating cells then clear their boil-off
        # ceilings outright, so the THF verdicts this gate asserts must STOP holding.  A control
        # that leaves them unchanged would mean the gate reads something other than the model.
        rows2, _i2, _f2 = run(design_scale=0.1)
        thf2 = [r for r in rows2 if r["arch"] in ROT and r["solvent"] == "THF"]
        still = all(r["verdict"] == "boils" for r in thf2)
        print("\nNEGATIVE CONTROL: transport ceilings x0.1 -> THF still boils at both rotating "
              "cells: %s" % still)
        print("G-THERMGEO control: %s" % ("BAD -- test is inert" if still else "GOOD"))
        return 0 if not still else 1

    out = {"rows": rows, "n_immune_to_gap": len(immune), "n_rescuable": len(flips),
           "shared_gap_rows": shared, "ceiling_spread_on_shared_gap": spread,
           "transport_span_on_shared_gap": tspan, "identical_geometry_rows": ident,
           "identical_geometry_transport_span": ispan,
           "microfluidic_survives_organics": micro_ok,
           "thf_boils_at_both_rotating_above_1p6mm": thf_robust,
           "conditional_on_inherited_gap": conditional,
           "conditional_on_sigma": cond_sigma}
    p = os.path.join(STAGE, "thermal_geometry_sensitivity.json")
    json.dump(out, open(p, "w"), indent=1, default=lambda o: None)
    print("\nwrote %s" % p)
    print("G-THERMGEO: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
