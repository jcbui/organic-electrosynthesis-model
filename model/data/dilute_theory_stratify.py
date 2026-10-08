#!/usr/bin/env python3
"""G-DILUTE -- do the headline counts lean on the rows where dilute theory is most strained?

    cd Section4_Model && python data/dilute_theory_stratify.py
    cd Section4_Model && python data/dilute_theory_stratify.py --negative-control

WHY
---
SI S1.1 declares the first modelling choice openly: this is dilute-solution theory (Newman ch. 11),
applied to media that reach several molar. A reviewer from a concentrated-solution background does
not dispute the disclosure -- they ask the next question, which the disclosure does not answer:

    the headline is "N of 50 clear 25 mA cm-2". How many of those N are rows where the theory
    you just told me is approximate is being pushed hardest?

If the counts were carried by the concentrated rows, the disclosure would be a fig leaf. If they
survive inside the dilute stratum on its own, the theory-level exposure is bounded by construction
and no sweep is needed to say so. That is a fact about the published matrix, so it is computed
rather than argued.

WHAT IS STRATIFIED
------------------
Total dissolved concentration c_tot = carrier + substrate + supporting electrolyte, the same
quantity G-MUSOLN flags, split at 1.0 M. Below it, activity coefficients and the constant-mobility
assumption are on the ground every transport text stands on; above it they are an approximation
whose cost this repo has measured (the Dorn isotherms depart ~2x by 0.8 mol/kg).

WHAT THIS DOES NOT CLAIM
------------------------
It does not claim the concentrated rows are wrong, and it does not reweight anything. A stratum
count is not a corrected count -- it is the same model read over a subset. The verdict is about
the ORDERING, which is the conclusion Section 4 actually draws, not about the integers.
"""
import io
import json
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
CUT = 1.0
CHAIN = ["natural", "stirred", "flow", "anec"]          # claimed strictly ordered, in this order
THIN = ["micro", "rde", "rce"]                          # each claimed above the whole chain
ORDERING_TEXT = ("unstirred < stirred < recirculating flow < ANEC, with the microfluidic, RDE and "
                 "rotating-cylinder medians all above ANEC")


def ordering_claim(meds):
    """The architecture-ordering claim Section 4 makes, evaluated on one list of medians (ARCH order)."""
    m = dict(zip(ARCH, meds))
    chain = all(m[a] <= m[b] for a, b in zip(CHAIN, CHAIN[1:]))
    thin = all(m[t] >= m[CHAIN[-1]] for t in THIN)
    return bool(chain and thin)


# Electrolyte strings that state no molarity, each read from its row's provenance. Every one of them must be listed:
# an unlisted string raises rather than counting as 0 M, which is how a 56 wt% salt once entered the dilute axis.
ELYTE_NONMOLAR = {
    "56 wt% Et4NOTs aq": 1.02,                # Baizer JES 1964 Table II run 28 p. 218: 141 g of 56.5 wt% stock in 260 mL (row provenance)
    "0.3 wt% H2SO4/MeOH (BASF)": 0.024,       # 10 g H2SO4 in 2,910 g of electrolyte (US 5,507,922 Ex. 1), ~0.79 g/mL
    "5 wt% AcOH/MeOH-H2O": 0.0,               # acetic acid buffer, no supporting salt
    "Et3N 7.5 mM (no salt)/MeOH": 0.0075,     # the amine-carboxylate pair, no added salt
    "NaCl 7 mol% + pH 2 HCl/H2O-MeCN": 0.012, # ~12 mM ionics (Li/Wilden ESI p. S5)
}


def elyte_M(s):
    """Supporting-electrolyte molarity: the sum of every 'x M' / 'x mM' the string states, or its listed value."""
    s = str(s)
    hits = re.findall(r"([0-9.]+)\s*(m?)M\b", s)
    if hits:
        return sum(float(v) * (1e-3 if milli else 1.0) for v, milli in hits)
    if s in ELYTE_NONMOLAR:
        return ELYTE_NONMOLAR[s]
    raise ValueError("electrolyte %r states no molarity and is not in ELYTE_NONMOLAR" % s)


# rows whose carrier IS an ion of their own supporting salt (bromide in NaBr, chloride in KCl, carbonate); its
# concentration is already in the electrolyte term, so it is counted once. Asserted: the carrier and the salt must agree.
CARRIER_IS_ELECTROLYTE = {"Br-mediated Hofmann rearrangement", "Amidyl-radical C-H amination (phenanthridinone)",
                          "Cl-mediated ethylene epoxidation", "Br- oxidation / electrophilic bromination",
                          "Alkaline lignin -> vanillin (pilot)"}


def c_total(rx):
    """Total dissolved concentration per row of reactions_50.csv: each species counted once."""
    rx = rx.copy()
    rx["c_elyte"] = rx.electrolyte.map(elyte_M)
    for n in CARRIER_IS_ELECTROLYTE:
        r = rx[rx.reaction == n]
        if len(r) != 1:
            raise SystemExit("CARRIER_IS_ELECTROLYTE names %r, which is not one row" % n)
    own_car = (rx.carrier_type != "substrate") & ~rx.reaction.isin(CARRIER_IS_ELECTROLYTE)
    own_sub = ~((rx.carrier_type == "substrate") & rx.reaction.isin(CARRIER_IS_ELECTROLYTE))   # carbonate: substrate AND salt
    rx["c_tot"] = (rx.C_substrate_M.astype(float).where(own_sub, 0.0)
                   + rx.C_carrier_M.astype(float).where(own_car, 0.0) + rx.c_elyte)
    return rx


def main(neg=False):
    mat = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    rx = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
    m = mat.merge(c_total(rx)[["reaction", "c_elyte", "c_tot"]], on="reaction")
    if neg:
        # Perturb the MODEL side into a state where the ordering must break inside a stratum:
        # invert the concentrated rows' ceilings so unstirred outruns RCE there. A control that
        # merely reclassified rows would test the split, not the verdict, and the verdict is what
        # this gate reports.
        m.loc[m.c_tot >= CUT, ARCH] = m.loc[m.c_tot >= CUT, ARCH[::-1]].values

    # tier0_ec_matrix.csv is WIDE: one column per architecture, not an `architecture` column.
    dil = m[m.c_tot < CUT]
    con = m[m.c_tot >= CUT]
    nrx = m.reaction.nunique()
    print("  %d reactions x %d architectures; split at c_tot = %.1f M "
          "(carrier + substrate + supporting electrolyte)" % (nrx, len(ARCH), CUT))
    print("    dilute      c_tot <  %.1f M : %2d reactions" % (CUT, dil.reaction.nunique()))
    print("    concentrated c_tot >= %.1f M : %2d reactions" % (CUT, con.reaction.nunique()))

    rep, order_ok = {}, {}
    for label, sub in (("all", m), ("dilute", dil), ("concentrated", con)):
        n = sub.reaction.nunique()
        meds, c25, c50 = [], [], []
        for a in ARCH:
            s = sub[a].astype(float)
            meds.append(float(s.median()))
            c25.append(int((s >= 25).sum()))
            c50.append(int((s >= 50).sum()))
        rep[label] = {"n": n, "median": meds, "n25": c25, "n50": c50}
        # the conclusion Section 4 draws is the ORDERING, not the integers. Since 2026-09-07 the
        # claim has the shape ordering_claim() states: the four-step chain through the ANEC cell,
        # with every thin-film archetype (microfluidic, RDE, rotating cylinder) above it. The three
        # thin-film medians sit within ~20 % of one another and are not claimed to be ordered.
        order_ok[label] = ordering_claim(meds)
        print("\n  %s stratum (n = %d)" % (label.upper(), n))
        print("    %-14s %s" % ("", "  ".join("%8s" % a for a in ARCH)))
        print("    %-14s %s" % ("median mA cm-2", "  ".join("%8.1f" % v for v in meds)))
        print("    %-14s %s" % ("clearing 25", "  ".join("%5d/%-2d" % (v, n) for v in c25)))
        print("    %-14s %s" % ("clearing 50", "  ".join("%5d/%-2d" % (v, n) for v in c50)))
        print("    ordering %s: %s" % (ORDERING_TEXT, "HOLDS" if order_ok[label] else "BROKEN"))

    # SECOND AXIS, AND IT IS THE PHYSICALLY RIGHT ONE.
    # c_tot lumps a 6.85 M neutral organic substrate with 3 M LiBr, and those strain dilute theory
    # differently. What the Dorn isotherms in this repo actually measure departing -- ~2x by
    # 0.8 mol/kg -- is the constant-mobility assumption for an ELECTROLYTE, so the second split is on the
    # supporting-electrolyte molarity alone, where a concentrated neutral substrate does not count.
    esplit = {}
    for label, sub in (("elyte >= 1 M", m[m.c_elyte >= CUT]), ("elyte <  1 M", m[m.c_elyte < CUT])):
        n = sub.reaction.nunique()
        meds = [float(sub[a_].astype(float).median()) for a_ in ARCH]
        esplit[label] = {"n": n, "median": meds,
                         "n25": [int((sub[a_].astype(float) >= 25).sum()) for a_ in ARCH],
                         "ordering_holds": ordering_claim(meds)}
        print("\n  %-13s n = %2d   medians %s   ordering %s"
              % (label, n, " ".join("%7.1f" % v for v in meds),
                 "HOLDS" if esplit[label]["ordering_holds"] else "BROKEN"))

    print()
    # what share of each headline count is carried by the concentrated rows?
    share = []
    for i, a in enumerate(ARCH):
        tot = rep["all"]["n25"][i]
        share.append(rep["concentrated"]["n25"][i] / tot if tot else 0.0)
        print("  %-8s of the %2d rows clearing 25, %2d (%.0f%%) are c_tot >= %.1f M; "
              "the concentrated stratum is %.0f%% of the set"
              % (a, tot, rep["concentrated"]["n25"][i], 100 * share[-1], CUT,
                 100.0 * con.reaction.nunique() / nrx))

    out = os.path.join(ROOT, "results",
                       "dilute_theory_stratify%s.json" % ("_NEGCONTROL" if neg else ""))
    json.dump({"cut_M": CUT, "architectures": ARCH, "strata": rep,
               "ordering_holds": order_ok, "conc_share_of_25_count": share,
               "by_electrolyte_molarity": esplit,
               "c_tot_max_M": float(m.c_tot.max()),
               "c_tot_max_reaction": str(m.loc[m.c_tot.idxmax(), "reaction"]),
               "c_tot_max_elyte_M": float(m.loc[m.c_tot.idxmax(), "c_elyte"])},
              io.open(out, "w", encoding="utf8"), indent=1)
    print("\n  -> %s" % os.path.relpath(out, ROOT))

    if neg:
        ok = not order_ok["concentrated"]
        print("\nNEGATIVE CONTROL: the concentrated rows' seven architecture ceilings are REVERSED, "
              "so the ordering must break inside that stratum.")
        print("G-DILUTE control: %s"
              % ("GOOD (the broken ordering was detected)" if ok else
                 "BAD -- test is inert; the ordering verdict cannot fail"))
        return 0 if ok else 1
    if not all(v["ordering_holds"] for v in esplit.values()):
        print("\nG-DILUTE: FAIL -- the ordering breaks when the set is split on supporting-"
              "electrolyte molarity, the axis on which dilute theory actually degrades")
        return 1
    if not (order_ok["dilute"] and order_ok["concentrated"]):
        print("\nG-DILUTE: FAIL -- the architecture ordering does not survive inside both strata, "
              "so it depends on where dilute theory is being pushed")
        return 1
    print("\nG-DILUTE: PASS -- the architecture ordering holds INSIDE the dilute stratum on its "
          "own and inside the concentrated stratum on its own, so Section 4's conclusion does not "
          "rest on the rows where dilute-solution theory is most strained. The integers do differ "
          "between strata, which is why they are reported here rather than only in aggregate.")
    return 0


def check_si(neg=False):
    """G-DILUTE-SI -- bind S1.1's stratification paragraph to the computed split.

    Every magnitude in that paragraph is interpolated from this script's JSON, so the numbers
    cannot drift. Its two DIRECTIONAL claims are typed English and can:

      "the split is not neutral"    -- the concentrated rows must carry a LARGER share of the
                                       unstirred >=25 count than their share of the set. If a
                                       property update ever equalised them, the sentence would be
                                       announcing a bias that is no longer there.
      "weakens as the reactor improves" -- the concentrated share must FALL from unstirred to RCE.

    Both are the kind of claim that survives a green numeric gate while being false. It FAILS if
    the paragraph is absent (trap 10).
    """
    sys.path.insert(0, HERE)
    from docx_text import asserted_text
    import unicodedata
    d = json.load(io.open(os.path.join(ROOT, "results", "dilute_theory_stratify.json"),
                          encoding="utf-8"))
    t = unicodedata.normalize("NFKC", re.sub(r"\s+", " ", asserted_text(
        os.path.join(ROOT, "SI_Section4_Transport_Model.docx"))))
    fails, checked = [], 0
    if "The influence of concentrated rows can be isolated by splitting" not in t:
        print("    FAIL  S1.1's stratification paragraph is no longer in the SI")
        print("\nG-DILUTE-SI: FAIL")
        return 1

    st, sh = d["strata"], list(d["conc_share_of_25_count"])
    if neg:                                  # perturb the MODEL side, never the document
        sh = [0.10] * len(sh)
        st = json.loads(json.dumps(st))
        st["concentrated"]["n25"][0] = st["concentrated"]["n"]  # break the printed integer too

    conc_frac = st["concentrated"]["n"] / float(st["all"]["n"])
    checked += 1
    if not sh[0] > conc_frac:
        fails.append("S1.1 says concentration 'affects the two groups differently', but the "
                     "concentrated rows carry "
                     "%.0f%% of the unstirred >=25 count against %.0f%% of the set"
                     % (100 * sh[0], 100 * conc_frac))
    checked += 1
    if not sh[-1] < sh[0]:
        fails.append("S1.1 says the dependence 'weakens as the reactor improves', but the "
                     "concentrated share goes %.0f%% (unstirred) -> %.0f%% (RCE)"
                     % (100 * sh[0], 100 * sh[-1]))

    # the printed integers, each bound to the stratum named beside it (trap 11)
    for phrase, want in (
            ("Of the %d reactions that clear 25 mA cm\u22122 in the unstirred beaker, %d are "
             "concentrated rows" % (st["all"]["n25"][0], st["concentrated"]["n25"][0]), True),
            ("within the dilute stratum alone the count is %d of %d"
             % (st["dilute"]["n25"][0], st["dilute"]["n"]), True),
            ("division gives %d concentrated rows and %d dilute rows"
             % (st["concentrated"]["n"], st["dilute"]["n"]), True),
            # the two DIRECTIONAL claims must still be present as sentences: the data checks above
            # cannot fire on a claim that has simply been reworded away (trap 10).
            ("concentration affects the two groups differently", True),
            ("The dependence weakens as the reactor improves", True)):
        checked += 1
        if (phrase in t) != want:
            fails.append("S1.1 does not say %r -- the model and the prose disagree" % phrase)

    print("  S1.1 claims bound to results/dilute_theory_stratify.json: %d" % checked)
    for f in fails:
        print("    FAIL  %s" % f)
    if neg:
        print("\nNEGATIVE CONTROL: concentrated share flattened to 10% at every architecture and "
              "the unstirred count inflated, so both directional claims must be refuted.")
        print("G-DILUTE-SI control: %s"
              % ("GOOD (the stale directional claims were caught)" if len(fails) >= 2 else
                 "BAD -- test is inert (%d finding(s))" % len(fails)))
        return 0 if len(fails) >= 2 else 1
    if fails:
        print("\nG-DILUTE-SI: FAIL")
        return 1
    print("\nG-DILUTE-SI: PASS -- S1.1's stratification paragraph agrees with the computed split, "
          "in its integers and in both directional claims")
    return 0


if __name__ == "__main__":
    _neg = "--negative-control" in sys.argv
    sys.exit(check_si(_neg) if "--check-si" in sys.argv else main(_neg))
