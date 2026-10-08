#!/usr/bin/env python3
"""G-SIBOUNDS -- the SI sensitivity table must bracket its own values and cover the MS numbers.

    cd Section4_Model && python data/check_si_bounds.py
    cd Section4_Model && python data/check_si_bounds.py --negative-control

Two assertions, because a bounds table can fail in two independent ways:

  (1) BRACKETING. Every reported value must satisfy lower <= value <= upper. A table whose central
      value falls outside its own band is not a sensitivity, it is an arithmetic error -- and it is
      easy to produce, because the bound at one edge of a kappa band is not always the one that
      moves the quantity in the obvious direction (U'_required carries an iL/kappa term and so runs
      OPPOSITE to the ceiling).

  (2) COVERAGE. Every quantity G-MSDERIVED checks against the manuscript must have a bounds entry.
      Without this the table can look complete while silently omitting a published number -- the
      failure mode of CLAUDE.md trap 9, where a gate covered part of Fig. 5 and reported PASS for
      the whole figure.
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); SEC4 = os.path.dirname(HERE)

## MS claim label (as G-MSDERIVED names it) -> the bounds key that covers it
COVERS = {
 "Fig5a THF ceiling":            "THF beaker ceiling",
 "Fig5a MeCN+DMF, caption":      "MeCN beaker ceiling",
 "Fig5a DMF+MeCN, body":         "DMF beaker ceiling",
 "Fig5a aq. NaOH ceiling":       "aq. NaOH beaker ceiling",
 "Fig5b zero-gap THF":           "THF zero-gap ceiling",
 "Fig5b zero-gap MeCN":          "MeCN zero-gap ceiling",
 "Fig5b zero-gap DMF":           "DMF zero-gap ceiling",
 "Fig5b zero-gap aq. NaOH":      "aq. NaOH zero-gap ceiling",
 "Fig5c MeCN short at 250 um":   "MeCN 25 um cooling shortfall",
 "Fig5c zero-gap aq. NaOH":      "aq. NaOH zero-gap cooling shortfall",
 "Fig5c zero-gap DMF":           "DMF zero-gap cooling shortfall",
 "Fig5c zero-gap MeCN":          "MeCN zero-gap cooling shortfall",
 "Fig5c zero-gap THF":           "THF zero-gap cooling shortfall",
 "count clearing 25, unstirred": "count >=25, natural",
 # the Section 4 body states the same quantity in its own words; v42 corrected it from 11
 # to 12, and it is bounded by the same entry as the abstract's phrasing.
 "count clearing 25, unstirred (Sec 4 body)": "count >=25, natural",
 "count clearing 25, RCE":       "count >=25, rce",
 # v79 (the CODEX review pass) states these counts in merged sentences, so the pins that bind
 # them were renamed; each still resolves to the same bounds-table entry as before.
 "median + count clearing 50, stirred (Sec 4 body)":     "count >=50, stirred",
 "count clearing 50, unstirred -> RCE (Sec 4 body)":     "count >=50, natural",
 "count clearing 50, unstirred -> RCE (Fig 5 caption)":  "count >=50, natural",
 "count clearing 50, thinning the film (abstract)":       "count >=50, natural",
 "count clearing 25, unstirred -> RCE (Sec 8)":          "count >=25, natural",
 "median, stirred (Sec 3 body)":                         "median, stirred",
 "Fig7a beaker ceilings":                                "THF beaker ceiling",
 # v106: the absolute THF microfluidic ceiling left the main text (it is still stated, and bounded, in the
 # SI); Section 5 now states the Figure 7d cooling margins instead, each bounded over the same kappa band.
 # The entry named is the solvent that SETS the quoted end of each range.
 "Fig7d microfluidic passive margin":                    "THF 25 um cooling shortfall",
 "Fig7d THF rotating shortfall":                         "THF rotating-cylinder cooling shortfall",
 "Fig7d MeCN/DMF rotating shortfall":                    "MeCN rotating-cylinder cooling shortfall",
 "Fig7d stack shortfall":                                "THF zero-gap cooling shortfall",
 "architecture medians (Sec 8 ladder)":                  "median, natural",
 "count clearing 50, unstirred": "count >=50, natural",
 "count clearing 50, RCE":       "count >=50, rce",
 "count clearing 50, stirred":   "count >=50, stirred",
 "TRL-E flow/micro counts":      "count >=25, flow",
 "Fig2b caption medians":        "median, natural",
 "Sec 8 delta-ladder medians":   "median, stirred",
 "Fig5a MeCN+DMF, caption ":     "MeCN beaker ceiling",
 "median, unstirred (Sec 4 body)":  "median, natural",
 "median, unstirred (Fig 1b body)": "median, natural",
 "median, unstirred (TRL-E table)": "median, natural",
 "median, RCE (Fig 1b body)":       "median, rce",
 "median, stirred (TRL-E table)":   "median, stirred",
 "median, stirred (Sec 3 body)":    "median, stirred",
 "median, stirred (Fig 3b body)":   "median, stirred",
 "Fig2b caption medians":           "median, natural",
 # Table 1's current-density gate. It printed the UNSTIRRED median until JR5 (2026-09-28)
 # collapsed the rung onto the stirred one for Jonas Rein's #199 -- "I don't see a world where
 # the median reaction is not stirred" -- an undivided batch cell being a stirred one; the
 # band it carries is therefore the stirred median's. (2026-09-12: it had printed 8.0 against
 # the matrix's 8.2, one quantity in two roundings.)
 "Table 1 readiness gate, stirred median": "median, stirred",
}
## deliberately NOT bounded, with the reason -- so an omission is a DECISION, not an oversight
EXEMPT = {
 # The Section 8.2 worked example is an ILLUSTRATION of a tight batch cell -- 100 mA cm-2 across a
 # DECLARED 5 mm gap -- and not one of the modelled thermal archetypes, so it feeds no ceiling, no
 # margin and no count. Its one uncertain input is the conductivity, which is MEASURED and carries
 # its own registry row and band (0.1 M Bu4NBF4/DMF, 4.76 mS cm-1, Table S7f); the SI states the
 # interval over which the 10-20 V claim holds. A separate bounds row would restate that band.
 "Sec 8.2 worked example: cell voltage and heat":
     "illustrative worked example at a declared gap; its only uncertain input is a measured "
     "conductivity whose band is tabulated, and the SI states the interval the claim holds over",
 "Sec 8.2 worked example: the batch steady state":
     "same illustration; T_ss is q/U' from that same measured conductivity and the tabulated "
     "beaker geometry, both of which carry their own bounds entries",
 # The two starvation panels (Fig. 2c, Fig. 3a) are ILLUSTRATIVE single-system solves, not
 # reported ceilings: every input is declared on the figure itself (0.5 M, 1 e-, D = 1.0e-9 for
 # the exemplar; 0.1 M, 2 e-, D = 1.39e-9 for the corpus-substrate median), and i_lim is exactly
 # nFDC/delta for them. The only input carrying an experimental uncertainty is the measured
 # stirred film, whose 193-207 um band IS tabulated ("delta (stirred) / operating point"), and
 # these ceilings scale exactly as 1/delta, so that entry brackets them at -3.4/+3.6%. They feed
 # no count, no median and no threshold. A separate bounds row would restate the film's band.
 "Fig2c exemplar film + ceiling": "illustrative panel; the film is the tabulated measured value",
 "Fig2c exemplar ceiling": "illustrative single-system solve, exactly nFDC/delta from inputs "
                           "declared on the figure; bracketed by the tabulated film band",
 "Fig2c corpus-median ceiling and both barrier ratios": "as above, expressed as a ratio to the "
                                                        "50 mA cm-2 barrier",
 "Fig2c corpus-median ceiling": "as above, at the corpus-median substrate parameters",
 "Fig2c corpus-median barrier ratio": "as above, expressed as a ratio to the barrier",


 "Fig3a exemplar ceiling restated": "the Fig. 2c exemplar ceiling, restated",
 # 2026-09-16: two quantities of the catalyst paragraph whose only uncertain input is the DECLARED rate
 # constant, whose bracket the SI already tabulates per row in S5.7 -- and both scale on it analytically,
 # so a bounds row would restate that bracket under a square root.
 "catalyst kinetic ceilings, body":
     "the Saveant plateau nFD_catC_cat/x_k scales as sqrt(k), so the measured rate-constant bracket "
     "tabulated in S5.7 (10-10^4 M^-1 s^-1 for the nickel and the cobalt-hydride rows) brackets it directly; the band-edge solves "
     "for these rows are published in the same section",
 "catalyst kinetic gains, body":
     "the unstirred-to-rotating-cylinder gain of each sourced catalyst row, a ratio of two cells of the SAME row whose "
     "only uncertain input is the declared rate constant; the band-edge re-solves of S5.7 bracket both cells, and the "
     "gain's own range over the band is printed in Table S11",
 "catalyst homocoupling sentence, body":
     "a statement of which catalyst row clears 25 mA cm-2 and from which architecture on; the row's ceilings are cells of "
     "the published matrix bracketed by the band-edge re-solves of S5.7, and no number of its own is printed",
 # 2026-09-05: Fig. 3a draws its convective profiles at the archetype MEDIAN films of Fig. 2b and
 # prints the exact linear-profile surface value 1 - i/i_lim for each; films are geometric
 # (delta_range has no bounds row), surfaces follow from them by identity.

 "Fig3a supplied surfaces": "c_surf = 1 - i/i_lim at the barrier current for the two films above, "
                            "an identity of the linear profile; nothing for a band to bracket "
                            "beyond the films themselves",

 "Fig3a corpus-median restated": "the Fig. 2c corpus-median ceiling, restated",
 "substrate clearing": "a partition of the 50-reaction set by carrier type, not a modelled quantity",
 "catalyst never clearing": "as above",
 "Fig4b catalyst medians": "a per-class median of the same matrix; bounded by the architecture rows",
 "Fig4b catalyst uplift": "a ratio of two per-class medians of the same matrix; bounded as above",
 "catalyst medians, body": "the same per-class medians the Fig. 4b entry covers, quoted in the body "
                           "at unstirred and RCE instead of stirred and RCE",
 "catalyst uplift, body": "the same per-class ratio, unstirred -> RCE; bounded by the architecture rows",
 "Fig2b guide shortfall": "a property of the GUIDE LINE, not of a reported ceiling: how far the "
                         "archetype medians fall below a 1/delta line anchored at the stirred "
                         "archetype. It is a geometric consequence of delta_eff correlating with "
                         "D across the corpus, so the SI bounds table -- which brackets reported "
                         "i_lim -- has nothing to bracket it with. Recomputed from the matrix and "
                         "the archetype delta medians instead.",
 "Fig2a flow delta label": "a delta_eff RANGE over the fifty rows, geometric rather than a "
                           "transport ceiling; the SI bounds table brackets reported i_lim and "
                           "carries no delta entry. Checked against archetype delta_range(), the "
                           "same source the figure draws from.",
 "Fig2a ANEC delta label": "as above, for the ANEC flow cell (a measured film).",
 "Fig2a micro delta label": "as above, for the microfluidic cell (the half-gap, derived).",
 "Fig2a RCE delta label": "as above, for the rotating-cylinder archetype.",
 "Tier 2 band, body": "a delta_eff RANGE over the members of the tier (recirculating and ANEC flow cells), "
                      "geometric rather than a ceiling; checked against archetype delta_range().",
 "Tier 3 band, body": "as above, for the microfluidic, RDE and rotating-cylinder archetypes.",
 "Fig3a starved films": "the illustrative barrier-current profiles of Fig. 3a: three films at which the 0.5 M "
                        "exemplar's own ceiling sits below the barrier, read from the profile solve.",
 "Fig3a starved ceilings": "as above: the exemplar's own i_lim at those three films, nFDC/delta exactly.",
 "Fig3a supplied films": "the illustrative barrier-current profiles of Fig. 3a at the archetype films; each "
                         "film is the archetype value (or median) Fig. 2b draws, checked against the profile solve.",
 "Fig2b model floor (thinnest delta)": "a MINIMUM over the fifty rows of delta_eff, which is a "
                                       "GEOMETRIC/hydrodynamic quantity set by the archetype's "
                                       "own correlation, not a transport ceiling. The SI bounds "
                                       "table brackets reported i_lim; a delta has no entry there "
                                       "and no perturbation of a transport property is bracketed "
                                       "by one. It is checked directly against archetype_bands "
                                       "instead, which is the same source the figure draws from.",
 "Fig4c rows plotted / dropped": "a CARDINALITY -- how many of the solver's rows the panel plots -- "
                                 "not a magnitude, so no perturbation of a physical property can "
                                 "move it and there is nothing for a sensitivity band to bracket. "
                                 "It is checked directly against mediated_ec_matrix.csv instead, "
                                 "including the Newton-wall flag the caption used to count wrong.",
 # 2026-09-05: fifteen Fig. 2c / Fig. 4 / Section 3-4 numbers that no gate had pinned (the 52.6
 # among them was two corrections stale). None is a reported transport ceiling of the kind the
 # bounds table brackets; each says what it is instead.
 "Fig2c corpus-median D": "an INPUT declared on the figure (the corpus-median Wilke-Chang D of the "
                          "substrate rows), not a reported ceiling; checked against the constant the "
                          "profile solve computed with, so the printed input reproduces the printed "
                          "ceiling.",
 "Fig4b catalyst exception ceiling": "a single matrix cell (the one catalyst row reaching 25 mA cm-2 "
                                     "in any architecture), read from the matrix; its sensitivity is "
                                     "the per-row property sweep of Table S7, not a class band.",
 "Fig4b catalyst exception loading": "a page-verified INPUT (that row's 30 mM loading, Table S2), "
                                     "not a modelled quantity.",
 "catalyst loading range, body": "the range of page-verified inputs across the catalyst rows "
                                 "(Table S2), not a modelled quantity.",
 "Fig4c flat slopes": "fitted log-log slopes of the solver's own output across the six architectures "
                      "-- a SHAPE descriptor of each mediated trace, not a ceiling -- recomputed by "
                      "model_medians from the matrix, the same source the figure draws.",
 "Fig4c steep slopes": "as above, for the six reactor-sensitive traces.",
 # 2026-10-05: Section 4 now names the four nearly architecture-independent mediated rows and gives both
 # slope ranges in one sentence (eleven mediated rows since the reaction audit re-typed three).
 "mediated slopes, flat and steep":
     "fitted log-log slopes of the solver's own output across the seven architectures -- a SHAPE descriptor "
     "of each mediated trace, not a ceiling -- recomputed by model_medians from the matrix. What can move a "
     "slope is the rate constant, and the tenfold sweep of S5.5 is where that is measured per row.",
 "Fig4d ceiling and cap ratio": "the DECLARED generic base case of Fig. 4 (d-f), not a measured "
                                "system: the sensitivity of its two declared diffusivities is computed "
                                "separately (S5.4: +/-25% moves the regime boundaries by at most 0.67 "
                                "decades) and the value is read from the regimes solve.",
 "Fig4e ceiling": "as above.",
 "Fig4f ceiling and commuting ratio": "as above.",
 "Fig4d-f surface depletion": "the solver's own convergence record for the three base-case panels "
                              "(resting mediator at the surface at the plateau), read from the regimes "
                              "solve; a numerical criterion, not a physical ceiling.",
 "RCE second-correlation bound, body": "this IS a bound -- the size of the S3.3 comparison against the "
                                       "second fitted correlation -- so bracketing it with a band would "
                                       "be circular. Recomputed from the S3.3 artifact.",
 "Tier 2 gain, body": "a ratio of two architecture medians (stirred, parallel-plate), both of which the "
                      "bounds table brackets individually.",
 "mediated intensification, low end": "a ratio of two cells of one mediated row (rotating cylinder over "
                                      "unstirred), read from the matrix; the row-level sensitivity is the "
                                      "substrate-D and rate-constant sweeps of S5.5.",
 "mediated intensification, high end": "as above, for the row with the largest ratio.",
 # v79 merged the two ends into one sentence ("approximately 1.6-fold to 17-fold"), so the pin
 # that binds them is now a single ordered check. Same quantity, same reason for exemption.
 # v79 renamed these pins when CODEX merged their sentences and renumbered the figures
 # (old Fig. 4 -> Fig. 6, old Fig. 5 -> Fig. 7). Each keeps the exemption its twin carried.
 "Fig6c flat slopes": "a log-log SLOPE, not a magnitude: a property perturbation moves every "
   "architecture of the row together, so the slope is invariant and no band brackets it.",
 "Fig6c steep slopes": "as above.",
 "Fig6c rows plotted": "a CARDINALITY, not a magnitude -- no perturbation of a physical property "
   "can change how many cells the panel plots, so there is nothing for a band to bracket.",
 "Tier 1 band, body": "a tier BAND is the delta_eff span of its own members, computed from the "
   "correlations rather than measured, so the bounds table brackets the ceilings it implies, "
   "not the band itself.",
 "catalyst span and exception, body": "a ratio of two architecture medians WITHIN the "
   "catalyst-carried subset plus the subset's own extremum; the individual medians are bracketed, "
   "the ratio moves numerator and denominator together.",
 # 2026-10-05: G-MSDERIVED pins the two ends separately, each at half its own last printed digit
 "mediated intensification range, low end, body": "the low end of the mediated range: a ratio of two cells of ONE "
   "mediated row, so a property perturbation moves numerator and denominator together and there is no band for it to sit in.",
 "mediated intensification range, high end, body": "the high end of the mediated range: a ratio of two cells of ONE "
   "mediated row, so a property perturbation moves numerator and denominator together and there is no band for it to sit in.",
 # 2026-09-09: the catalyst class under a finite rate constant (G-CATK, SI S5.7). The suite's first run
 # after the sweep failed here, correctly: three new pins, no declared decision for any of them.
 "catalyst finite-k uplift, body": "the TOP EDGE of a declared sensitivity band -- the class's largest "
   "amplification at k = 10^4 M-1 s-1, the upper limit of the rate-constant band S5.7 sweeps and "
   "tabulates -- so bracketing it with a band would be circular, the same shape as the S3.3 "
   "second-correlation bound above. Its remaining dependence is on the declared substrate "
   "diffusivity, whose own registry row states the direction and size (linear, on the "
   "substrate-capped cells only). Recomputed from the S5.7 artifact.",
 "catalyst restatement, Sec 8": "a CARDINALITY -- the size of the catalyst-carried class, fixed by the "
   "carrier classification of S3 -- not a magnitude; no property perturbation can move it. Checked "
   "against the matrix by G-MSDERIVED.",
 "Fig. 6 caption pointer to S5.7": "a CROSS-REFERENCE (the SI section range the caption cites), not a "
   "magnitude; G-GHOST resolves it, and G-MSDERIVED pins it only so the pointer cannot vanish silently.",
 # 2026-09-11: seven catalyst rows carried at a SOURCED rate constant (S5.7, Table S7j); Figure 6 redesigned.
 "catalyst gain at the sourced k, body": "a RATIO of two cells of one row (unstirred -> rotating cylinder) "
   "across the seven sourced rows, plus the count at the top edge of the nickel bracket: the ratio moves "
   "numerator and denominator together under a property perturbation, and its kinetic sensitivity is the "
   "measured bracket itself, which S5.7 and the Table S7j rows state per row (the counts at both edges are "
   "computed there, not bracketed here). Recomputed from the S5.7 artifact.",
 "Fig. 6 (d-f) regime currents, caption": "three PUBLISHED CELLS of the mediated matrix (the ANEC column of Table S5 "
   "for the three rows drawn), restated by the profile solve on the same mesh and asserted equal to them by G-MSDERIVED; "
   "their bounds are the matrix's own -- the film band of Table S8 per architecture and the tenfold rate-constant sweep of "
   "S5.5 per row -- not a separate band for the caption.",
 # 2026-09-21 (v118, Connor Coley's comment 21): the loading separation between the two homogeneous classes.
 "carrier loading separation, body":
     "four of its seven numbers are page-verified INPUTS -- the carrier concentrations of the mediated and "
     "catalyst rows, read from the exemplar papers and printed per row in Table S2 -- so no property "
     "perturbation moves them, and the fifth is their median ratio. The sixth and seventh are the class median "
     "ceiling ratio at its lowest and highest architecture, a ratio of two medians in the SAME column, so a "
     "property perturbation moves numerator and denominator together; re-solved at both edges of the "
     "architecture film band it reads 22-47 against the 24-47 printed at the central films (2026-10-05, on "
     "the 11 mediated and 12 stoichiometric catalyst rows; chain rows are outside both medians).",
 "carrier loading overlap, body":
     "two carrier concentrations read from the exemplar papers and printed per row in Table S2 -- page-verified "
     "INPUTS, not model outputs, so no property perturbation can move them; data/ms_phrases.py asserts that no "
     "other mediated row has entered the catalyst range.",
 "porous-electrode need, Sec 8":
     "a restatement of bounded quantities: the two films are the thinnest archetype median films, whose film bands "
     "Table S8 tabulates, and 14 is 50 minus the >=25 count at those architectures, whose own band the bounds table "
     "carries (count >=25 at the rotating cylinder); the 50 and the 25 are the set size and the threshold.",
 "Fig. 6 (d-f) reaction shares, caption": "an integral of the same three solves (the share of the activated "
   "mediator consumed inside the film), a SHAPE descriptor of each profile, not a ceiling; its sensitivity is the "
   "regime-label test of S5.5 (the label survives +/-25 % on both diffusivities, re-solved).",
}
# The claim scan below reads want() AND want_ordered(). It read only want() until 2026-08-25, so
# every positionally-bound claim -- the Fig. 2b caption medians among them -- was exempt from the
# coverage requirement without anyone declaring it exempt. Same shape as CLAUDE.md trap 9.

def main(neg=False):
    B = json.load(io.open(os.path.join(SEC4, "results", "si_sensitivity_bounds.json"), encoding="utf-8"))
    flat = {}
    for grp in ("thermal", "transport"):
        g = B.get(grp, {})
        if "status" in g:
            print("G-SIBOUNDS: FAIL -- %s bounds incomplete: %s" % (grp, g["status"])); raise SystemExit(1)
        flat.update(g)
    fails = []

    ## (1) bracketing
    nb = 0
    for k, v in flat.items():
        lo, val, hi = v["lower"], v["value"], v["upper"]
        if neg and k == "median, natural":
            lo = val * 1.5                                   # perturb the TABLE, not the model
        if not (lo <= val <= hi):
            fails.append("%s: value %.4g outside its own bounds [%.4g, %.4g]" % (k, val, lo, hi))
        else:
            nb += 1
    ## (1b) CURRENCY, not just bracketing. The bracketing test asks lower <= value <= upper and
    ## nothing more, so a stale central value passes as long as its old band still contains it --
    ## which is exactly what happened: after the stirred film moved, "median, stirred" sat at
    ## 17.09 inside a band of 9.11-31.76 while the matrix said 9.11, and every count had been
    ## computed over ~11 class-collapsed rows for longer than that. Bind each central value to
    ## the matrix it claims to summarise.
    import csv as _csv
    _m = {}
    with io.open(os.path.join(SEC4, "julia", "tier0_ec_matrix.csv"), encoding="utf-8") as _fh:
        for _r in _csv.DictReader(_fh):
            for _k in ("natural", "stirred", "flow", "anec", "micro", "rde", "rce"):
                _m.setdefault(_k, []).append(float(_r[_k]))
    import statistics as _st
    for _k, _v in flat.items():
        _parts = _k.split(", ")
        if len(_parts) != 2 or _parts[1] not in _m:
            continue
        _col = _m[_parts[1]]
        if _parts[0].startswith("median"):
            _want = _st.median(_col)
        elif _parts[0].startswith("count >="):
            _want = float(sum(1 for x in _col if x >= float(_parts[0].split(">=")[1])))
        else:
            continue
        if abs(_v["value"] - _want) > max(0.01 * abs(_want), 0.02):
            fails.append("%s: bounds table central value %.2f but the matrix gives %.2f"
                         % (_k, _v["value"], _want))

    ## (2) coverage of every MS number the derived-value gate checks
    src = io.open(os.path.join(HERE, "check_ms_derived.py"), encoding="utf-8").read()
    src = "\n".join(re.sub(r"#.*$", "", ln) for ln in src.split("\n"))
    claims = set(re.findall(r'want(?:_ordered)?\(\s*"([^"]+)"', src))
    claims -= {"label"}
    missing = sorted(c for c in claims if c not in COVERS and c not in EXEMPT)
    unknown = sorted(k for k in COVERS.values() if k not in flat)
    for c in missing:
        fails.append("MS claim %r has no bounds entry and is not exempt" % c)
    for u in unknown:
        fails.append("bounds key %r referenced by COVERS does not exist in the table" % u)

    print("%d bounded quantities, all bracketing their value" % nb)
    print("%d manuscript claims checked by G-MSDERIVED; %d covered, %d exempt with a stated reason"
          % (len(claims), len([c for c in claims if c in COVERS]), len([c for c in claims if c in EXEMPT])))
    if fails:
        if neg:
            fired = any("outside its own bounds" in f for f in fails)
            print("G-SIBOUNDS control: %s (bracketing perturbation was %sdetected)"
                  % ("GOOD" if fired else "BAD", "" if fired else "NOT "))
            raise SystemExit(0 if fired else 1)
        print("\nG-SIBOUNDS: FAIL")
        for f in fails: print("   ", f)
        raise SystemExit(1)
    print("\nG-SIBOUNDS: PASS -- every value lies inside its bounds and every reported MS number is "
          "either bounded or exempt with a reason")

if __name__ == "__main__":
    main("--negative-control" in sys.argv)
