#!/usr/bin/env python3
"""G-COVER -- how many MODEL-DERIVED numbers in the shipped documents does a gate actually assert?

    cd Section4_Model && python data/audit_number_coverage.py
    cd Section4_Model && python data/audit_number_coverage.py --verbose

WHY
---
Trap 9 in CLAUDE.md -- "a gate that covers PART of a claim reports PASS for the whole thing" --
has now bitten three separate times: G-MSDERIVED asserted the Fig. 5 (a) and (b) panels and left
(c) uncovered; it asserted the unstirred and RCE threshold counts and left the stirred one, the
TRL-E range and the Section 8 delta-ladder uncovered; and G-SIBOUNDS scanned only want() and not
want_ordered(), so every positionally-bound claim was silently exempt from the coverage rule.

Each time the hole was found by accident. This finds them on purpose: pull every number out of
the shipped SI and MS that CARRIES A MODEL UNIT, and ask whether any gate file mentions it in an
assertion. A number that appears in no gate is not necessarily wrong -- but nothing is checking it,
and that is exactly the state each of the three holes above was in before it was found.

WHAT COUNTS AS A MODEL NUMBER
-----------------------------
Only quantities this model produces: current densities (mA cm-2), threshold counts (N/50, N of 50),
cooling duties (W cm-2 [K-1]), conductivities (mS cm-1) and shortfall ratios (Nx). Deliberately
NOT page numbers, years, volumes, molarities of literature recipes, or equation numbers -- those
are provenance, checked by G-MSCITE, G-CITE and G-COND, not by the derived-value gates.

This is a REPORT, not a pass/fail gate: some uncovered numbers are legitimately uncheckable (a
figure axis label, a quantity quoted from a cited paper). It prints the list so a human can judge,
and it fails only if coverage falls below where it stands when the list was last reviewed.
"""
import io
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from docx_text import asserted_text                                    # noqa: E402

def _gate_files():
    """Every file that could assert a number about the model.

    THIS LIST HAD ITS OWN COVERAGE GAP on first run: it scanned Section4_Model/data and figs but
    not MS Drafts/scripts, where verify_v*.py checks the Fig. 2b guide constant, the corpus
    substrate median and the exemplar ceiling. Three of the five "uncovered" MS numbers it
    reported were false positives -- a coverage audit with a coverage gap. Kept as a comment
    because it is the same failure mode the audit exists to find.
    """
    out = []
    for d in (HERE, os.path.join(ROOT, "figs"),
              os.path.join(os.path.dirname(ROOT), "MS Drafts", "scripts")):
        if not os.path.isdir(d):
            continue
        # THE AUDIT MUST NOT COUNT ITSELF. Writing a reasoned note about which numbers this
        # heuristic cannot see puts every one of those numerals into a gate source, and coverage
        # then reads 100% because the gate talked about them. That is the same trap
        # check_number_closure.py records against itself, met again here on 2026-09-12: the note
        # below MIN_COVERAGE lifted coverage 95% -> 100% while nothing was actually checked.
        out += [os.path.join(d, f) for f in os.listdir(d)
                if f.endswith(".py") and os.path.join(d, f) != os.path.abspath(__file__)]
    # The Julia audit gates assert in SI units (A/m2), so a value the SI prints as
    # 785 mA cm-2 is stored as 7855 A/m2 and a literal scan cannot see it. Include the Julia
    # sources and their gate table, and match a x10 variant below.
    jd = os.path.join(ROOT, "julia")
    if os.path.isdir(jd):
        out += [os.path.join(jd, f) for f in os.listdir(jd)
                if f.endswith(".jl") or f == "audit_gates.csv"]
    return out


GATE_FILES = _gate_files()

# quantities the MODEL produces, with the unit that identifies them
PATTERNS = [
    (r"(\d+(?:\.\d+)?)\s*mA\s*cm[−\-]?2", "mA/cm2"),
    (r"(\d+)\s*/\s*50\b", "count/50"),
    (r"(\d+)\s+of\s+(?:50|31|11|48)\b", "count of N"),
    (r"(\d+(?:\.\d+)?)\s*[×x]\b", "ratio"),
    (r"(\d+(?:\.\d+)?)\s*W\s*cm[−\-]?2", "W/cm2"),
    (r"(\d+(?:\.\d+)?)\s*mS\s*cm[−\-]?1", "mS/cm"),
]
# REVIEWED 2026-09-12, lowered 0.97 -> 0.95 with reasons, after the thermal table moved to the seven
# transport archetypes. The twelve SI numbers this heuristic cannot see split three ways, and none of
# them is unchecked:
#   * the MeCN margin series (10.71, 9.92, 2.11 ...) and the two reversal conductivities (27.3, 42.2)
#     are asserted by "S7f MeCN margin series" and the two "S9 MeCN flip" pins in check_si_derived.py,
#     which GENERATE their expected phrase from the model. A generated pin puts no numeral in a gate
#     source, so a heuristic that greps gate sources for numerals structurally cannot count it -- the
#     alternative is typing the expectation, which this repository forbids for good reason.
#   * the kappa(T) margin pair (1.11) is generated the same way by the Ea registry row and is checked
#     as a SET by G-KAPPAT, which compares declared flips against computed flips.
#   * the remainder (196, 392, 111.342, 87.6, 25.64, 49.9, 31.5) predate this change and are the
#     narrative residue the 2026-08-30 review already accepted.
# Raising this number back is the goal; lowering it again needs the same kind of accounting.
#
# REVIEWED AGAIN 2026-09-12 (post-v94 audit), lowered 0.95 -> 0.92, and the reason is the one the
# note above already describes rather than a new hole. Ten category-6/8/9 sensitivities were TYPED
# sentences describing a retired ladder; they are now generated from thermal_model.REACTORS and the
# sweep JSONs. A generated sentence puts no numeral in a gate source, so every number that moved
# from typed to computed LEFT this heuristic's numerator while becoming harder, not easier, to get
# wrong. The twelve that moved:
#   * 0.662, 11.41, 12.08 -- the evaporative-loss bound, computed from the worst open-vessel fail
#     the model reports (the row named a fail that the transport-ceiling operating point had made
#     false, which is why it is generated now);
#   * 110.7, 7.37, 14.51, 21.36 -- the microfluidic sigma sweep, computed against that cell's own
#     transport ceiling; the SET is asserted by G-THERMGEO's conditional_on_sigma census;
#   * 1118.1 -- the h_int series on the thinnest-gap row, whose headline bound G-HINT now measures
#     (it selected that row by the string "250" and had gone vacuous);
#   * 1427 -- the kappa(T) microfluidic ceiling, re-solved by G-SIDERIVED from a phrase that gate
#     GENERATES from the model (it had been pinned to a hardcoded 250 um gap);
#   * 65.6 -- the THF band series across the architectures;
#   * 34.5, 34.8 -- the aqueous margin against its own transport ceiling.
# What actually checks them is G-REGEN: parameters_provenance.csv must equal what its generator
# produces today, and that generator computes each of these from thermal_model.py. A drift in the
# model therefore fails the build rather than being greppable in a gate source. G-THERMROWS
# additionally fails if any shipped thermal sensitivity names an operating point the reactor table
# does not carry, which is the defect this whole class of number had.
#
# REVIEWED A THIRD TIME 2026-09-13, lowered 0.915 -> 0.895, and for the third time the cause is
# numbers CEASING to be typed rather than ceasing to be checked. Deriving sigma from the declared
# archetype moved every beaker-family ceiling and margin, and the sentences that state them --
# the THF band series across the architectures, the h_int sweep on the beaker, the MeCN margin
# series, the DMF volume sweep, the two THF flip conductivities, the sigma breaking points -- are
# now generated from thermal_model.REACTORS at build time. A generated sentence leaves no numeral
# in a gate source for this heuristic to grep, so each one LEFT the numerator while becoming
# impossible to get wrong by hand.
#
# What checks them is the chain this heuristic cannot see: G-REGEN requires
# parameters_provenance.csv to equal what its generator produces today, that generator computes
# each of these from thermal_model.py, and G-KAPPA re-derives six of them from a second code path
# and requires the registry row to state a value within 1% of each. G-THERMROWS additionally fails
# on any shipped thermal sensitivity naming an operating point the reactor table does not carry.
#
# The measured coverage at this review is 90.0% (260 of 289). RAISE as holes close; lowering it
# again needs this same accounting, written here, naming which numbers moved and what checks them.
# REVIEWED A FOURTH TIME 2026-09-14, lowered 0.895 -> 0.885, and the cause is the same one. The
# sigma derivation of 2026-09-13 reached the model and the registry but NOT the SI's own S6 prose,
# Table S4's margin column or the S3.2 electrolyte paragraph, which still TYPED numbers computed on
# the retired sigma = 12.5 (U' 0.0144/0.0160, T_ss 187 C, flip 11.15 / 1.27x, THF 12.9x / 20.0x,
# DMF 2.05x "band-proof" at the cylinder, a 70/89/152/192 volume series, tau 22/48 min) plus a
# stale S10 substrate-D paragraph (25.3 mA cm-2, 12 -> 11). Those typed numerals were mentioned by
# gates, so removing them took 12 covered numbers out of the denominator (289 -> 277); their
# replacements are GENERATED from results/figK_thermal.json (make_figK.py emits kappa_flips and
# beaker_dmf_example) and results/substrate_D_sensitivity.json, so they leave no numeral here:
# 0.0127 (U' stirred), 14.78 and 1.69 (the DMF binding reversal, now the rotating DISC, inside its
# own band), 49.5 (the THF disc reversal) and 25.64 (the substrate-D closest cell).
# What checks them: G-SIDERIVED re-solves U' still-air/stirred, the DMF T_ss and its flip, the DMF
# binding multiple and the THF disc reversal from thermal_model.py (six pins added the same day);
# G-KAPPA re-derives the THF 16.5x, the DMF 228 C and 14.09 against the registry; G-REGEN requires
# the registry text computing 14.78/1.69 to equal what its generator produces; G-SIFRESH requires
# the SI to equal a fresh build; G-DSUBSENS-REG binds the substrate-D sweep to its registry row.
# Measured at this review: 88.8% (246 of 277). RAISE as holes close.
# REVIEWED A FIFTH TIME 2026-10-06 (chemistry audit pass 5), lowered 0.885 -> 0.880, same cause again. The pass replaced
# typed registry and SI sentences with generated ones -- the emissivity, vessel-area, zero-gap sigma, Ea, NaI/DMF, RDE and
# RCE operating-point, UA and stirring rows of Table S7, and the S6/S6.2 thermal passages -- and a generated sentence puts
# no numeral in any gate source for this heuristic to find. The numbers that left the "mentioned" set are generated from
# figs/thermal_model.py, results/si_sensitivity_bounds.json and results/thermal_conditional_flips.json, and G-REGEN checks
# the registry against its generator and G-SIFRESH the SI against make_si.js. Measured 88.4% (258 of 292).
# REVIEWED A SIXTH TIME 2026-10-06 (chemistry audit pass 6), lowered 0.880 -> 0.860, same cause. The registry's i0,
# zero-gap gap, T_amb, stirring-U', evaporative-loss, operating-point, DMA re-solve, Casteel-Amis and channel-pair rows
# of Table S7 became generated sentences (from figs/thermal_model.py sweeps, results/dma_viscosity_sensitivity.json,
# data/casteel_amis.py on data/dorn_isotherms.csv, results/reactor_engineering.json), so 40 SI numerals -- W cm-2 heat
# terms, the micro/stack margins, the DMA cells, 20.03/7.041 -- left every gate source. G-REGEN checks the registry
# against its generator, G-SIFRESH the SI against make_si.js, G-DMAMU the DMA cells against the re-solve, G-CA the
# Casteel-Amis arithmetic. The one MS numeral, 868 mA cm-2, is generated by ms_phrases (Section 4, Figure 6 (d-f))
# and pinned by G-MSDERIVED against julia/mediated_ec_matrix.csv. Measured 86.3% (259 of 300).
MIN_COVERAGE = 0.860       # reviewed 2026-10-06 at a measured 86.3% (259 of 300); see the six notes
                           # above. Previously reviewed 2026-09-13 at 90.0% (260 of 289); see all three
                           # notes above. The rest are literature
                           # values quoted in prose, not model outputs. RAISE as holes close,
                           # never lower silently -- a lowered floor is a hidden regression.


def norm(x):
    return unicodedata.normalize("NFKC", x)


def main(verbose=False):
    gate_src = "\n".join(io.open(f, encoding="utf-8", errors="replace").read() for f in GATE_FILES)
    docs = {"SI": os.path.join(ROOT, "SI_Section4_Transport_Model.docx")}
    ms = sorted(f for f in os.listdir(os.path.join(os.path.dirname(ROOT), "MS Drafts"))
                if re.match(r"revised_outline_v\d+_RCE.*\.docx$", f))
    if ms:
        docs["MS"] = os.path.join(os.path.dirname(ROOT), "MS Drafts", ms[-1])

    report, tot, cov = {}, 0, 0
    for name, path in docs.items():
        t = norm(re.sub(r"\s+", " ", asserted_text(path)))
        seen, rows = set(), []
        for pat, kind in PATTERNS:
            for m in re.finditer(pat, t):
                val = m.group(1)
                key = (val, kind)
                if key in seen:
                    continue
                seen.add(key)
                # covered if any gate mentions this exact numeral
                # A/m2 vs mA cm-2 differ by exactly 10, so accept the x10 variant as well --
                # otherwise a unit convention hides real coverage (785 mA cm-2 == 7855 A/m2).
                cands = {val}
                try:
                    f = float(val)
                    for alt in (f * 10.0, f / 10.0):
                        cands.add(("%.4f" % alt).rstrip("0").rstrip("."))
                except ValueError:
                    pass
                hit = any(re.search(r"(?<![\d.])" + re.escape(c) + r"(?![\d])", gate_src)
                          for c in cands)
                rows.append({"value": val, "kind": kind, "covered": hit,
                             "context": t[max(0, m.start() - 55):m.end() + 35]})
        rows.sort(key=lambda r: (r["covered"], r["kind"], r["value"]))
        n = len(rows); c = sum(1 for r in rows if r["covered"])
        tot += n; cov += c
        report[name] = rows
        print("  %-3s %3d distinct model numbers, %3d mentioned by a gate  (%.0f%%)"
              % (name, n, c, 100.0 * c / max(n, 1)))
        unc = [r for r in rows if not r["covered"]]
        print("      %d not mentioned by ANY gate:" % len(unc))
        for r in (unc if verbose else unc[:12]):
            print("        %-8s %-10s ...%s..." % (r["value"], r["kind"], r["context"][:88]))
        if not verbose and len(unc) > 12:
            print("        (+%d more; run with --verbose)" % (len(unc) - 12))
        print()

    frac = cov / max(tot, 1)
    json.dump({"total": tot, "covered": cov, "fraction": frac, "min_coverage": MIN_COVERAGE,
               "by_doc": {k: [r for r in v] for k, v in report.items()}},
              io.open(os.path.join(ROOT, "results", "number_coverage.json"), "w",
                      encoding="utf8"), indent=1)
    print("  overall: %d of %d model numbers are mentioned by some gate (%.0f%%)"
          % (cov, tot, 100 * frac))
    print("\n  A mention is NOT a proof of coverage -- the numeral may appear in an unrelated")
    print("  gate. It is a NECESSARY condition: a number no gate mentions is certainly unchecked.")
    if frac < MIN_COVERAGE:
        print("\nG-COVER: FAIL -- coverage %.0f%% is below the %.0f%% last reviewed"
              % (100 * frac, 100 * MIN_COVERAGE))
        return 1
    print("\nG-COVER: PASS -- coverage %.0f%% at or above the %.0f%% last reviewed"
          % (100 * frac, 100 * MIN_COVERAGE))
    return 0


if __name__ == "__main__":
    sys.exit(main(verbose="--verbose" in sys.argv))
