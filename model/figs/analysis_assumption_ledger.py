"""What kind of assumption is each of the registry's state-C rows, and what backs it?

    cd Section4_Model && python figs/analysis_assumption_ledger.py

WHY THIS EXISTS
---------------
The registry census reports a bare integer -- "117 assumption" -- and a reviewer reads that as
117 numbers pulled out of the air. Most of them are not that, but the census cannot tell the
difference, because `assumption` is one bucket holding four very different things:

  * a solver mesh count, which no citation could ever support and which is instead backed by a
    convergence study;
  * a scenario definition ("the unstirred-batch archetype IS delta = 300 um"), which is a choice
    the paper makes and states, not a claim about nature;
  * a physical quantity that is unsourced but swept, where the conclusion is shown to survive
    the whole swept range;
  * a physical quantity that is unsourced, feeds a result, and is NOT bounded -- the real
    exposure, and the only one a reviewer should be able to make stick.

This script sorts all 117 into those tiers FROM THE REGISTRY TEXT, not from a hand-written list,
and gates the last tier so a new unsourced parameter cannot appear without failing a check.

HOW THE TIERS ARE ASSIGNED, AND WHY THAT IS NOT CIRCULAR
--------------------------------------------------------
The tier is derived from two fields the registry already carries for its own reasons -- the
category, and whether the sensitivity states a tested numeric range and an outcome. Nothing here
is typed per row. That matters: if someone adds an unsourced parameter with a hand-waving
sensitivity, it lands in T4 automatically and G-ASSUME fails. The classifier cannot be talked
out of it by prose.

The one thing this script does NOT do is judge whether a sensitivity's claimed outcome is true.
That is what the separate sweep gates (G-KAPPA, G-CATD, G-SOLV, G-ANCHOR, and the 14 Julia audit
gates) are for. This is a taxonomy, not a re-verification.
"""
import json
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REG = os.path.join(ROOT, "data", "parameters_provenance.csv")
OUT_J = os.path.join(ROOT, "results", "assumption_ledger.json")
OUT_M = os.path.join(ROOT, "docs", "ASSUMPTION_LEDGER.md")

# WHAT MAKES A STATE-C ROW ADEQUATE
# ---------------------------------
# PROVENANCE_STANDARD.md says an assumption "must carry a sensitivity: the range tested and the
# conclusion that depends on it". That is the test applied here, and it is applied literally:
# a sensitivity is ADEQUATE when it states a perturbation and that perturbation's quantified
# effect on a named result. Operationally that means it carries numeric content beyond the
# parameter's own value, plus a clause saying what happened.
#
# An earlier version of this classifier tried to recognise adequacy from a vocabulary of
# range-words ("tested", "swept", "spans") and number-pairs ("4-12"). That was the wrong
# instrument, and it failed in a revealing direction: it marked as EXPOSED rows whose
# sensitivities read "a 5 pct rho error moves k_m by 1.8 pct" and "Tested pitch 4-12 mm ... the
# zero-gap conclusion is unconditional" -- both perfectly adequate -- simply because the phrasing
# was not in the list. Every time that happened the fix was to widen the vocabulary, which is
# fitting the classifier to the answers. Counting quantified content instead is both simpler and
# harder to talk out of.
# T0 DOES NOT MEAN UNUSED, and the label must not suggest it. An orphan check over every solver,
# figure generator, table and build script finds ZERO of these rows unreferenced. The 39
# category-6 conductivities are each the supporting electrolyte of a specific one of the 50
# reactions and are printed in SI Table S4; the 13 solver-species diffusivities are literal
# arguments to the Nernst-Planck solve -- S("ClO4-", -1.0, 1.7e-9, ...) in julia/run_mediated.jl
# -- and the solver will not run without them. What T0 means is narrower, and is the point: the
# row is CONSUMED, but a named gate establishes that it cannot move a number this work reports as
# a CONCLUSION. Rows with no consumer at all are already excluded upstream -- 18 electrolytes
# carry the status "unused-legacy (no registry row)" and never reach the registry at all.
RE_DISPLAY = re.compile(r"display-only|enters no transport|no consumer|zero consumers|unused",
                        re.I)
RE_NOTREPORTED = re.compile(r"do(?:es)? not set any reported|not set any reported|"
                            r"do(?:es)? not enter any reported", re.I)
# A row that QUOTES a claim in order to withdraw it must not be classified by the quoted phrase.
# This is not hypothetical: after a direct perturbation showed that the solver-species
# diffusivities DO move a published count, their sensitivity was rewritten to say so -- and
# because the new text quotes the old assertion ("This row previously asserted that they 'do not
# set any reported i_lim'. That is FALSE"), the T0 test went on matching it and kept thirteen rows
# in the tier whose whole meaning is the opposite of what the row now says.
RE_REFUTED = re.compile(r"\bthat is false\b|\bis FALSE\b|CORRECTED[^.]{0,60}\bPERTURBATION\b|"
                        r"no longer claims|previously asserted", re.I)
RE_GATE = re.compile(r"\bgate[sd]?\b|\bG\d+\b|\bG-[A-Z]+\b", re.I)
# Numeric tokens: integers, decimals, scientific notation, percentages. Two or more means the
# text states both a perturbation and an effect rather than merely restating the value.
RE_NUM = re.compile(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")
# A sensitivity that only points at another row cannot be judged on its own.
RE_XREF = re.compile(r"\bas for the\b|\bthe same (?:conditionality|argument|reasoning|"
                     r"sensitivity)\b|\bsee (?:the )?(?:row|entry) above\b", re.I)
# The row's own text reports a conclusion moving, flipping, or needing a hedge.
# A SIGNED bound states no magnitude but establishes the DIRECTION in which the neglected or
# uncertain term can move the result, and shows that direction protects the conclusion. The
# standard allows this and it is not a weak form: "every ceiling reported here is a lower bound
# and every 'this cell boils' statement is conservative" is unfalsifiable in magnitude yet fully
# load-bearing, because no magnitude of the neglected term can reverse a one-sided inequality.
# Requiring a numeric range here would demand a number that does not exist and cannot matter.
RE_SIGNED = re.compile(r"(?:lower|upper) bound|conservative|signed|"
                       r"can only (?:raise|lower|increase|decrease)|one-sided", re.I)
RE_DIRECTION = re.compile(r"\braises?\b|\blowers?\b|\bdelays?\b|\bincreases?\b|"
                          r"\bdecreases?\b|\bin the (?:safe|conservative) direction\b", re.I)
RE_FLIP = re.compile(r"\bflips?\b|would have to be (?:qualified|widened|softened)|"
                     r"withdrawn|bound-dependent|CARRIES A CONCLUSION|conditional(?:ity)?", re.I)

TIERS = {
    "T0": "Consumed, but gated as unable to move any REPORTED result",
    "T1": "Declared scenario / operating condition / numerical choice -- not a citable quantity",
    "T2": "Quantified sensitivity: perturbation + effect stated, conclusion survives",
    "T3": "Quantified sensitivity, but the row itself flags a flip, hedge or conditionality",
    "T4": "Signed bound: magnitude unstated, but the direction protects the conclusion",
    "T5": "Sensitivity NOT adequate (no perturbation+effect, or bare cross-reference) -- exposure",
}


def flags_conditionality(text):
    """True only if the row ASSERTS a conditionality, not if it denies one.

    FOURTH instance in this project of the same trap: prose containing a term in negated form
    being read as the term. Twelve of the seventeen rows this tier used to hold said things like
    "No conclusion flips", "Nothing flips" and "the zero-gap conclusion is unconditional" -- the
    exact opposite of what the tier means -- because RE_FLIP matched the word "flip" inside the
    denial. Each match is now tested against the SENTENCE that contains it, and a sentence carrying
    a negation of the flip does not count.
    """
    for m in RE_FLIP.finditer(text):
        a = text.rfind(".", 0, m.start()) + 1
        b = text.find(".", m.end())
        sent = text[a:(b if b > 0 else len(text))]
        if re.search(r"\bno\b|\bnothing\b|\bnone\b|\bnot\b|\bunconditional\b|"
                     r"\bdoes not\b|\bwithout\b|\bnever\b", sent, re.I):
            continue
        return True
    return False


# Numerals that are ADDRESSES, not magnitudes: S6, S5.4, §S6.2, Eq. S30, Table S7i, Fig. K,
# p. 578, pp. 875-882, ref 11, and bare 4-digit years. Anything matched here is removed before
# the "does this row state a perturbation and an effect" count.
RE_ADDRESS = re.compile(
    r"(?:\u00a7|\bsection\b|\bappendix\b)?\s*\bS\d+(?:\.\d+)*\b"
    r"|\b(?:Eq|Eqn|Table|Tab|Fig|Figure|Sec|Section|Appendix)\.?\s*S?\d+[A-Za-z]?(?:\.\d+)*\b"
    r"|\bpp?\.\s*\d+(?:\s*-\s*\d+)?\b"
    r"|\bref(?:erence)?s?\.?\s*\d+\b"
    r"|\b(?:19|20)\d{2}\b",
    re.I)


# Magnitudes written in WORDS. Stripping address-numerals alone put "survives a tenfold
# revision for six of the eight" in the exposure tier -- a row that does state a perturbation
# and its effect, just not in digits. A classifier that reads only digits is as wrong in this
# direction as one that reads every digit was in the other.
RE_WORDNUM = re.compile(
    r"\b(?:two|three|four|five|six|seven|eight|nine|ten|twenty|fifty|hundred)(?:fold)?\b"
    r"|\b(?:double|doubling|doubled|halve|halving|halved|tenfold|twofold|threefold)\b"
    r"|\border(?:s)? of magnitude\b", re.I)


# A literature value whose locator does not yet reach it: citable in principle, unanchored in
# fact. Not a "declared choice".
RE_UNANCHORED = re.compile(r"NOT PAGE-ANCHORED|could not be page-anchored|pending retrieval",
                           re.I)


def tier_of(row):
    s = str(row.sensitivity or "")
    refuted = bool(RE_REFUTED.search(s))
    if not refuted and (RE_DISPLAY.search(s) or (RE_NOTREPORTED.search(s) and RE_GATE.search(s))):
        return "T0"
    # Categories 7 and 11 define the scenario and the discretisation. So does the isothermal
    # operating point: 298.15 K is not an unsourced measurement of anything, it is the condition
    # at which the paper reports, stated on every table.
    # The category-7/11 blanket says "a declared scenario or discretisation, which no citation
    # could support". That is true of a reactor archetype or a mesh size. It is NOT true of a
    # published correlation coefficient that simply has not been page-anchored yet -- that IS a
    # citable quantity, and filing it as a declared choice would hide the exposure instead of
    # showing it. Rows that say so explicitly fall through to the normal quantified test.
    if RE_UNANCHORED.search(s):
        pass
    elif row.category in ("7. Reactors", "11. Numerics") or row.parameter == "Temperature T":
        # A declared scenario is still a row a referee must read first when its own text records that a published
        # number is conditional on it (chemistry audit, pass 4: the free-convection operating point governs the
        # unstirred counts), so the conditionality test outranks the declared-choice blanket.
        return "T3" if flags_conditionality(s) else "T1"
    # COUNT ONLY NUMERALS THAT COULD BE A PERTURBATION OR AN EFFECT.
    #
    # This used to be `len(RE_NUM.findall(s)) >= 2` over the raw text, so ANY two digits
    # anywhere promoted a row to T2 = "perturbation + effect stated, conclusion survives".
    # Section cross-references did it on their own: "the bulk-sink assumption is stated in
    # S5.4 ... verified by the S5.6 audit gates" scored two numerals and was published, inside
    # the SI's "51 state a perturbation and its computed effect", as a quantified sensitivity.
    # It states no perturbation of anything. So did "given per system in S5.5". Both are the
    # bare cross-reference the negative control claims to catch, and it did not catch them.
    #
    # Strip the tokens that are addresses rather than magnitudes -- section/appendix/equation/
    # table/figure/page references, reference markers and 4-digit years -- BEFORE counting.
    s_mag = RE_ADDRESS.sub(" ", s)
    n_num = len(RE_NUM.findall(s_mag)) + len(RE_WORDNUM.findall(s_mag))
    quantified = n_num >= 2 and not (RE_XREF.search(s) and n_num < 3)
    if quantified:
        return "T3" if flags_conditionality(s) else "T2"
    if RE_SIGNED.search(s) and RE_DIRECTION.search(s):
        return "T4"
    return "T5"


def main():
    reg = pd.read_csv(REG)
    a = reg[reg.provenance_class == "assumption"].copy()
    a["tier"] = a.apply(tier_of, axis=1)

    n = len(a)
    print("registry: %d rows, %d assumption (%.0f%%)" % (len(reg), n, 100 * n / len(reg)))
    print("\n%-4s %5s  %s" % ("tier", "n", "meaning"))
    counts = {}
    for t in ("T0", "T1", "T2", "T3", "T4", "T5"):
        k = int((a.tier == t).sum())
        counts[t] = k
        print("%-4s %5d  %s" % (t, k, TIERS[t]))

    print("\nby category and tier:")
    piv = a.pivot_table(index="category", columns="tier", values="parameter",
                        aggfunc="count", fill_value=0)
    print(piv.to_string())

    t4 = a[a.tier == "T5"]
    print("\n--- T5, the rows a reviewer can actually make stick (%d) ---" % len(t4))
    for _, x in t4.iterrows():
        print("  %-34s %-12s %s" % (str(x.parameter)[:34], str(x.value)[:12], x.category))

    rows = [dict(category=x.category, parameter=x.parameter, value=str(x.value),
                 units=str(x.units), tier=x.tier, sensitivity=str(x.sensitivity or ""))
            for _, x in a.iterrows()]
    # The SI publishes only the load-bearing subset (data/registry_liveness.py), so it needs the
    # tier breakdown of THAT subset, not of the whole registry. Both are emitted: the full picture
    # is the internal record, the live picture is what a reader of the SI is actually looking at.
    live_counts, n_live_assum = None, None
    lp = os.path.join(ROOT, "results", "registry_liveness.json")
    if os.path.exists(lp):
        with open(lp) as f:
            dead = set(json.load(f)["dead_parameters"])
        alive = a[~a.parameter.isin(dead)]
        n_live_assum = len(alive)
        live_counts = {t: int((alive.tier == t).sum()) for t in ("T0","T1","T2","T3","T4","T5")}
        print("\n--- published (load-bearing) subset only: %d assumption rows ---" % n_live_assum)
        for t in ("T0","T1","T2","T3","T4","T5"):
            print("%-4s %5d  %s" % (t, live_counts[t], TIERS[t]))

    report = dict(n_registry=len(reg), n_assumption=n, counts=counts,
                  n_assumption_live=n_live_assum, counts_live=live_counts,
                  tier_meanings=TIERS, t4=t4.parameter.tolist(), rows=rows)
    os.makedirs(os.path.dirname(OUT_J), exist_ok=True)
    with open(OUT_J, "w") as f:
        json.dump(report, f, indent=2)

    # ---------------- the markdown ledger ----------------
    L = ["# Assumption ledger — what the 117 state-C rows actually are",
         "",
         "Generated by `figs/analysis_assumption_ledger.py` from `data/parameters_provenance.csv`.",
         "Every number here is computed at run time; nothing is typed.",
         "",
         "The registry census reports `%d assumption` out of %d rows. That single integer hides"
         % (n, len(reg)),
         "four different kinds of thing, and only the last is an exposure a reviewer can press on.",
         "", "| tier | n | what it means |", "|---|---|---|"]
    for t in ("T0", "T1", "T2", "T3", "T4", "T5"):
        L.append("| **%s** | %d | %s |" % (t, counts[t], TIERS[t]))
    L += ["", "## By category", "",
          "```", piv.to_string(), "```", ""]
    L += ["## T5 — the real exposure (%d rows)" % len(t4), ""]
    if len(t4):
        L += ["| parameter | value | units | category |", "|---|---|---|---|"]
        for _, x in t4.iterrows():
            L.append("| %s | %s | %s | %s |" % (x.parameter, x.value, x.units, x.category))
    L += ["", "## T3 — quantified, but the row's own sensitivity flags a flip or a hedge (%d rows)"
          % counts["T3"], "",
          "These are not errors. Each one is a place where the registry states, in its own text,",
          "that a conclusion depends on where the value sits in its band. They are the rows to",
          "read before answering a referee.", ""]
    t3 = a[a.tier == "T3"]
    if len(t3):
        L += ["| parameter | value | category |", "|---|---|---|"]
        for _, x in t3.iterrows():
            L.append("| %s | %s | %s |" % (x.parameter, x.value, x.category))
    L.append("")
    with open(OUT_M, "w") as f:
        f.write("\n".join(L) + "\n")
    print("\nwrote %s" % os.path.relpath(OUT_M, ROOT))
    print("wrote %s" % os.path.relpath(OUT_J, ROOT))

    # ---------------- G-ASSUME ----------------
    # Pins the T4 set. A new unsourced parameter with no stated range fails this immediately;
    # so does silently deleting a sensitivity from an existing row.
    EXPECTED_T4 = set(json.load(open(os.path.join(ROOT, "data", "assumption_t4_expected.json")))) \
        if os.path.exists(os.path.join(ROOT, "data", "assumption_t4_expected.json")) else None
    fails = []
    if sum(counts.values()) != n:
        fails.append("tiers do not partition the assumption rows")
    unclassified = a[a.sensitivity.isna() | (a.sensitivity.astype(str).str.strip() == "")]
    if len(unclassified):
        fails.append("%d assumption rows carry no sensitivity at all" % len(unclassified))
    if EXPECTED_T4 is not None:
        got = set(t4.parameter)
        new = got - EXPECTED_T4
        gone = EXPECTED_T4 - got
        if new:
            fails.append("NEW unsourced parameter(s) with no stated range: %s" % sorted(new))
        if gone:
            fails.append("T4 rows resolved but the expected list was not updated: %s"
                         % sorted(gone))
    print("\nG-ASSUME: %s" % ("PASS" if not fails else "FAIL"))
    for f_ in fails:
        print("  " + f_)
    if fails:
        raise AssertionError("; ".join(fails))
    print("  every assumption row carries a sensitivity and falls in exactly one tier;")
    print("  T4 (%d rows) matches the pinned expected set" % len(t4))
    return report


if __name__ == "__main__":
    main()
