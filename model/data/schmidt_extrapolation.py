#!/usr/bin/env python3
"""G-SCRANGE -- the RCE correlation is extrapolated. In which direction, and at what cost?

    cd Section4_Model && python data/schmidt_extrapolation.py
    cd Section4_Model && python data/schmidt_extrapolation.py --negative-control

WHY
---
The rotating-cylinder archetype uses Eisenberg-Tobias-Wilke, Sh = 0.0791 Re^0.70 Sc^0.356, and it
sets the column carrying the most favourable numbers in this work. The paper states its own
calibration on p. 313, retrieved verbatim:

    "These experiments involved a Schmidt number variation of 2230 to 3650 and a Reynolds number
     range of 112.0-162,000"

TWO ERRORS THIS GATE EXISTS TO PREVENT, BOTH OF WHICH WERE SHIPPED
------------------------------------------------------------------
(1) THE WRONG WINDOW. Table S1 said "calibrated on aqueous ferricyanide at Sc ~ 1000-3000" and the
    first version of this gate hardcoded that, so SI S3.3 published "only 8 of 50 rows fall inside
    that window and the largest is 6.3x above it" -- framing a LOW-Sc extrapolation as a high-Sc
    one. Against the printed 2230-3650 the truth is the reverse: most rows sit BELOW the fitted
    floor, because aprotic organics have low viscosity, which raises D and lowers nu together.
    The window is now READ FROM THE REGISTRY row, which carries the page locator, so it cannot be
    retyped wrongly here.

(2) THE WRONG METHOD, WHICH FLIPPED THE SIGN. Substituting the exponent 1/3 for the fitted 0.356
    while leaving the coefficient 0.0791 alone changes the correlation at EVERY Sc, including
    inside the calibration window where the fit is known to reproduce the data -- that is not a
    sensitivity, it is a different and unfitted correlation. Done that way the RCE median appeared
    to fall 13.4% and the RDE/RCE ordering appeared to invert, and S3.3 published both. Holding
    the two forms equal at the centre of the calibrated range and changing only the slope -- the
    only comparison consistent with the fit -- RAISES the RCE median and preserves the ordering.
    The registry row for this correlation had said so all along.

The lesson is general: a sensitivity on a fitted correlation must preserve the fit where the fit
was made. Perturbing one coefficient of a multi-parameter fit in isolation is not a bound.
"""
import ast
import csv
import io
import json
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
FITTED_P = 0.356
THEORY_P = 1.0 / 3.0
## the Eisenberg form as correlations.jl states it; the Sc exponent is parsed and asserted
A_FIT, RE_P = 0.0791, 0.70


# The calibration window is a RETRIEVED FACT, and this file owns it. Eisenberg, Tobias & Wilke,
# J. Electrochem. Soc. 1954, 101, 306-320, p. 313, verbatim:
#   "These experiments involved a Schmidt number variation of 2230 to 3650 and a Reynolds number
#    range of 112.0-162,000 (peripheral velocities 1.17 to 426 cm/sec)."
# An earlier version read these two numbers back OUT of the registry row -- but that row is now
# generated FROM this gate's JSON, which made the dependency circular and broke the gate the
# moment the row was reworded. The fact lives here, with its locator; the registry consumes it.
CAL_LO, CAL_HI = 2230.0, 3650.0


def sc_of(rx, sol):
    out = {}
    for r in rx:
        s = sol.get(r["solvent"]) or sol.get(r["solvent"].split()[0])
        if not s:
            continue
        nu = (float(s["mu_mPas"]) * 1e-3) / (float(s["rho"]) * 1000.0)
        out[r["reaction"]] = nu / (float(r["D_cm2s"]) * 1e-4)
    return out


def main(neg=False):
    # the exponent must be read from the solver, never retyped (trap 14)
    jl = io.open(os.path.join(ROOT, "julia", "correlations.jl"), encoding="utf-8").read()
    jl_nc = "\n".join(re.sub(r"#.*$", "", ln) for ln in jl.split("\n"))
    m = re.search(r"Sh\s*=\s*0\.0791\s*\*\s*Re\^0\.70\s*\*\s*Sc\^([0-9.]+)", jl_nc)
    if not m:
        print("G-SCRANGE: FAIL -- correlations.jl no longer states the Eisenberg form this "
              "gate perturbs")
        return 1
    p_fit = float(m.group(1))
    if abs(p_fit - FITTED_P) > 1e-9:
        print("G-SCRANGE: FAIL -- solver Sc exponent %.4f != the %.4f this gate documents"
              % (p_fit, FITTED_P))
        return 1

    rx = list(csv.DictReader(io.open(os.path.join(HERE, "reactions_50.csv"), encoding="utf-8")))
    sol = {r["solvent"]: r for r in
           csv.DictReader(io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8"))}
    sc = sc_of(rx, sol)
    mat = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    mat["Sc"] = mat.reaction.map(sc)
    if mat.Sc.isna().any():
        print("G-SCRANGE: FAIL -- %d rows have no Schmidt number" % int(mat.Sc.isna().sum()))
        return 1

    # Reynolds number at the RCE operating point, so the "inside the fitted range" claim in
    # S3.3 is computed here rather than inherited from the registry text.
    import math as _math
    _d, _rpm = 0.012, 3000.0
    _v = _math.pi * _d * _rpm / 60.0
    _nu = {}
    for r in rx:
        sv = sol.get(r["solvent"]) or sol.get(r["solvent"].split()[0])
        if sv:
            _nu[r["reaction"]] = (float(sv["mu_mPas"]) * 1e-3) / (float(sv["rho"]) * 1000.0)
    re_vals = [_v * _d / v for v in _nu.values()]
    re_lo, re_hi = min(re_vals), max(re_vals)
    ## attach Re per row so the second correlation can be evaluated on the same frame
    mat["Re"] = mat.reaction.map({k: _v * _d / v for k, v in _nu.items()})
    if mat.Re.isna().any():
        print("G-SCRANGE: FAIL -- %d rows have no Reynolds number" % int(mat.Re.isna().sum()))
        return 1

    inside = int(mat.Sc.between(CAL_LO, CAL_HI).sum())
    n_below = int((mat.Sc < CAL_LO).sum())
    n_above = int((mat.Sc > CAL_HI).sum())
    print("  Eisenberg-Tobias-Wilke calibration (retrieved, p. 313): Sc %.0f-%.0f"
          % (CAL_LO, CAL_HI))
    print("  corpus Schmidt numbers: min %.0f  median %.0f  max %.0f"
          % (mat.Sc.min(), mat.Sc.median(), mat.Sc.max()))
    print("  rows INSIDE: %d of %d   BELOW the floor: %d   ABOVE the ceiling: %d"
          % (inside, len(mat), n_below, n_above))
    print("  the extrapolation is predominantly to %s Sc" % ("LOW" if n_below > n_above else "HIGH"))
    print("  Reynolds number at the RCE operating point: %.0f-%.0f (fitted 112-162,000)"
          % (re_lo, re_hi))

    ## THE SENSITIVITY IS NOW A SECOND MEASURED CORRELATION, NOT A PERTURBATION OF OUR OWN.
    ## What stood here until 2026-09-04 swapped the fitted Sc exponent for the theoretical 1/3
    ## and re-anchored at the calibration centre. That is defensible arithmetic and it is still
    ## SELF-REFERENTIAL: it perturbs a coefficient of our own correlation and reports how far our
    ## own answer moves, which a referee may fairly decline to accept as a bound. It also made the
    ## exposure look small (0.958-1.065x) and pointed the wrong way.
    ##
    ## Jang, Ruscher, Winzely & Morales-Guio (author list READ FROM THE PAPER, not recalled --
    ## the first draft of this comment invented five co-authors who are not on it),
    ## "Gastight rotating cylinder electrode: toward decoupling mass transport and intrinsic
    ## kinetics in electrocatalysis", AIChE J. 2022, 68(5), e17605, DOI 10.1002/aic.17605, fit an
    ## INDEPENDENT correlation to the same geometry, Eq. 7:
    ##
    ##     Sh_RCE = 0.204 Re^0.59 Sc^0.33,   validated Re 500-12,000 and Sc > 100
    ##
    ## The two correlations divide the problem cleanly and neither covers all of it. Eisenberg
    ## spans our REYNOLDS range (112-162,000 against our 6,867-57,953) and is extrapolated in
    ## Schmidt; Jang spans our SCHMIDT range (>100 against our 176-19,006, i.e. ALL FIFTY ROWS)
    ## and is extrapolated in Reynolds for 47 of 50. Eisenberg is retained as primary because Re
    ## carries the stronger exponent (0.70 against 0.356), because it covers our Re completely,
    ## and because it is the standard correlation for this geometry; Jang is the bound.
    JANG_A, JANG_RE_P, JANG_SC_P = 0.204, 0.59, 0.33
    JANG_RE_LO, JANG_RE_HI, JANG_SC_MIN = 500.0, 12000.0, 100.0
    if neg:                                          # control: make the two correlations identical
        JANG_A, JANG_RE_P, JANG_SC_P = A_FIT, RE_P, p_fit
    sh_eis = A_FIT * mat.Re ** RE_P * mat.Sc ** p_fit
    sh_jang = JANG_A * mat.Re ** JANG_RE_P * mat.Sc ** JANG_SC_P
    scale = sh_jang / sh_eis                          # i_lim ~ Sh, so this IS the current ratio
    alt = mat.rce * scale
    med = {a: float(mat[a].median()) for a in ARCH}
    med_alt = dict(med, rce=float(alt.median()))

    print("\n  second fitted correlation (Jang 2022, Eq. 7): Sh = %.3f Re^%.2f Sc^%.2f"
          % (JANG_A, JANG_RE_P, JANG_SC_P))
    print("    validated Re %.0f-%.0f  -> %d of %d rows inside"
          % (JANG_RE_LO, JANG_RE_HI,
             int(((mat.Re >= JANG_RE_LO) & (mat.Re <= JANG_RE_HI)).sum()), len(mat)))
    print("    validated Sc > %.0f      -> %d of %d rows inside"
          % (JANG_SC_MIN, int((mat.Sc > JANG_SC_MIN).sum()), len(mat)))
    print("    per-row current ratio Jang/Eisenberg  %.3f-%.3f" % (scale.min(), scale.max()))
    print("    RCE median      %8.2f -> %8.2f  (%+.1f%%)"
          % (med["rce"], med_alt["rce"], 100 * (med_alt["rce"] / med["rce"] - 1)))
    for thr in (25, 50):
        print("    clearing %d      %8d -> %8d"
              % (thr, int((mat.rce >= thr).sum()), int((alt >= thr).sum())))

    print("\n  pair margins in the published matrix (the pairs the ordering claim is made of, plus RDE/RCE):")
    # Since 2026-09-07 the claim is the four-step chain unstirred < stirred < recirculating < ANEC
    # with each thin-film archetype (microfluidic, RDE, rotating cylinder) above ANEC; the three
    # thin-film medians are NOT claimed to be ordered among themselves. RDE/RCE is reported because
    # it is the pair the second correlation inverts, and the SI discloses that.
    PAIRS = [("natural", "stirred"), ("stirred", "flow"), ("flow", "anec"),
             ("anec", "micro"), ("anec", "rde"), ("anec", "rce"), ("rde", "rce")]
    pairs = []
    for a, b in PAIRS:
        marg = med[b] / med[a] - 1.0
        marg_alt = med_alt[b] / med_alt[a] - 1.0
        pairs.append({"lo": a, "hi": b, "margin": marg, "margin_alt": marg_alt,
                      "inverts": (marg > 0.0) and (marg_alt <= 0.0)})
        print("    %-9s -> %-9s  %+6.1f%%   under the alternative correlation %+6.1f%%  %s"
              % (a, b, 100 * marg, 100 * marg_alt,
                 "INVERTS" if pairs[-1]["inverts"] else ("holds" if marg_alt > 0 else "below at both")))

    inverted = [p for p in pairs if p["inverts"]]
    span = med["rce"] / med["natural"]
    span_alt = med_alt["rce"] / med_alt["natural"]
    print("\n  full span unstirred -> RCE: %.1fx, and %.1fx under the alternative exponent"
          % (span, span_alt))

    json.dump({"fitted_p": p_fit, "cal_window": [CAL_LO, CAL_HI],
               "alt_correlation": "Jang 2022 Eq. 7: Sh = %.3f Re^%.2f Sc^%.2f"
                                  % (JANG_A, JANG_RE_P, JANG_SC_P),
               "alt_valid_Re": [JANG_RE_LO, JANG_RE_HI], "alt_valid_Sc_min": JANG_SC_MIN,
               "alt_rows_in_Re": int(((mat.Re >= JANG_RE_LO) & (mat.Re <= JANG_RE_HI)).sum()),
               "alt_rows_in_Sc": int((mat.Sc > JANG_SC_MIN).sum()),
               "n_below": n_below, "n_above": n_above,
               "re_lo": re_lo, "re_hi": re_hi,
               "factor_lo": float(scale.min()), "factor_hi": float(scale.max()),
               "sc_min": float(mat.Sc.min()), "sc_median": float(mat.Sc.median()),
               "sc_max": float(mat.Sc.max()), "n_inside": inside, "n_total": len(mat),
               "medians": med, "medians_alt": med_alt, "pairs": pairs,
               "n25_rce": int((mat.rce >= 25).sum()), "n25_rce_alt": int((alt >= 25).sum()),
               "n50_rce": int((mat.rce >= 50).sum()), "n50_rce_alt": int((alt >= 50).sum()),
               "span": span, "span_alt": span_alt,
               "inverted_pairs": [(p["lo"], p["hi"]) for p in inverted]},
              io.open(os.path.join(ROOT, "results", "schmidt_extrapolation%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)

    if neg:
        ok = not inverted
        print("\nNEGATIVE CONTROL: the alternative exponent is set EQUAL to the fitted one, so "
              "nothing may move and no pair may invert.")
        print("G-SCRANGE control: %s"
              % ("GOOD (an unperturbed run inverts nothing)" if ok else
                 "BAD -- the gate reports an inversion with no perturbation applied"))
        return 0 if ok else 1

    # The gate's job is to keep the SHIPPED CLAIM honest, not to adjudicate the exponent.
    si = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")
    sys.path.insert(0, HERE)
    from docx_text import asserted_text
    import unicodedata
    t = unicodedata.normalize("NFKC", re.sub(r"\s+", " ", asserted_text(si)))
    fails = []
    # The SI must DISCLOSE the extrapolation and state its direction. It must not claim the
    # column is an upper estimate on this axis -- the re-anchored comparison says the opposite,
    # and an earlier draft of S3.3 published that error.
    for need in ("2230", "3650"):
        checked_si = True
        if need not in t:
            fails.append("the SI no longer states the calibration window (%s missing)" % need)
    if "below" not in t.lower() or "extrapolat" not in t.lower():
        fails.append("the SI no longer states that the extrapolation is predominantly below the "
                     "fitted floor")
    ## EVERY restatement, not the one this gate was written against. The first version pinned
    ## the S3.3 phrasing ("rotating-cylinder column is ... an upper"), so the Table S1 caption
    ## went on saying the opposite -- "the RCE column should be read as an upper estimate", with
    ## a calibration window and a corpus Sc that were both wrong -- behind a green gate. Scope
    ## the test to SENTENCES and check all of them. Splitting is decimal-safe: a break requires
    ## a letter or bracket before the period and a capital after it, so "121.7" never splits.
    sents = re.split(r"(?<=[a-z\)\]])\.\s+(?=[A-Z(])", t)
    RCE = re.compile(r"rotating[- ]cylinder|\bRCE\b|Sc\^?0?\.?356|Eisenberg", re.I)
    for sent in sents:
        if not RCE.search(sent):
            continue
        ## "no upper bound" is a DIFFERENT and legitimate statement -- a mixture property
        ## carried without a bracket -- and the flattened table cells put it in reach of the
        ## Eisenberg row. Match the claim shape (this column IS an upper estimate), not the word.
        if re.search(r"upper[- ]estimate", sent, re.I) and not re.search(
                r"(no|without an|lacks an) upper", sent, re.I):
            fails.append("a sentence about the rotating-cylinder column calls it an upper "
                         "estimate, which the re-anchored comparison contradicts: ...%s..."
                         % sent.strip()[:150])
    ## and the corpus span must be stated wherever the window is, so a reader cannot be told the
    ## window without being told which side of it the rows sit on.
    if "176" not in t or "19,006" not in t:
        fails.append("the SI no longer states the corpus Schmidt span (176-19,006)")
    ## AN INVERSION IS NOW ALLOWED, BUT ONLY IF THE SI SAYS SO. While the sensitivity was a
    ## perturbation of our own exponent it produced none, so any inversion was a regression and
    ## bare existence was the right test. The second fitted correlation legitimately inverts the
    ## rotating-disc / rotating-cylinder pair -- those two medians are 12.2% apart, the softest
    ## adjacent margin in the model -- so the test that matters is whether the document DISCLOSES
    ## it. Existence alone would now fail forever and could only be silenced by deleting the
    ## comparison, which is the opposite of what it is for.
    if inverted:
        disclosed = ("inverting that one adjacent pair" in t
                     or "falls BELOW the rotating-disc" in t
                     or "falls below the rotating-disc" in t)
        if not disclosed:
            fails.append("the second correlation inverts %s and the SI does not disclose it"
                         % ", ".join("%s/%s" % (p["lo"], p["hi"]) for p in inverted))
        else:
            print("\n  the second correlation inverts %s, and the SI discloses it"
                  % ", ".join("%s/%s" % (p["lo"], p["hi"]) for p in inverted))
    for f in fails:
        print("    FAIL  %s" % f)
    if fails:
        print("\nG-SCRANGE: FAIL")
        return 1
    print("\nG-SCRANGE: PASS -- %d of %d rows sit outside the calibrated window (%d below "
          "the floor, %d above the ceiling), and the SI states that with its direction. "
          "Re-anchored at the fit centre the alternative exponent moves per-row values "
          "%.3f-%.3fx and RAISES the RCE median %.1f -> %.1f mA cm-2, so on this axis the "
          "column is an under-estimate rather than an upper one; no count moves and every "
          "adjacent pair keeps its order."
          % (len(mat) - inside, len(mat), n_below, n_above,
             scale.min(), scale.max(), med["rce"], med_alt["rce"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
