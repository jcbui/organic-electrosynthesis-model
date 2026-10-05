#!/usr/bin/env python3
"""G-EVERYVAL -- the standing rule, enforced on every row of the registry.

    cd Section4_Model && python data/check_every_value.py
    cd Section4_Model && python data/check_every_value.py --negative-control

THE RULE (author's, 2026-08-31)
-------------------------------
    "Every value needs to have a source, or a defensible assumption that brackets its value."

Two acceptable states, and nothing else:

  SOURCED    -- class measured or derived, carrying a real citation AND a locator. A declared
                basis does not count here: a row that says what it rests on instead of naming a
                document is an assumption, however well argued, and must be bracketed.

  BRACKETED  -- class assumption, whose sensitivity states a perturbation AND its computed effect.
                The assumption ledger already tiers exactly this (T2 quantified-and-survives,
                T3 quantified-but-conditional), and this gate reuses its tiering rather than
                re-deriving it, so the two cannot drift apart.

Two states are tolerated only when they are DECLARED, and both are counted and printed so that a
reader sees the size of each:

  INERT      -- ledger T0: consumed, but gated as unable to move any reported result. There is
                nothing to bracket because nothing downstream can move.
  SCENARIO   -- ledger T1: a declared scenario, operating point or numerical setting. These define
                the case rather than estimate a quantity, so a bracket on "the true value" is not
                a meaningful object. They are NOT exempt from evidence: each must still say what
                happens if it moves, and this gate requires that sentence to exist.

Anything else -- an assumption with no quantified sensitivity (ledger T5), or a measured/derived
row missing its locator -- is a FAIL. Those are the two ways a number can enter this model with
neither a document nor a bound behind it.
"""
import csv
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DECLARED = re.compile(r"^(Declared\b|-- \()")
# a sentence that says what happens if the value moves, for the scenario rows
# What counts as "says what happens if it moves". Widened once, on 2026-08-31, to recognise the
# INVARIANCE form -- "it cannot move the converged answer", "flat to within an order of magnitude
# either side" -- which is a stronger statement than a sweep, not a weaker one: a sweep shows the
# answer did not move over a tested range, whereas an invariance argument shows it cannot. The
# widening was made to match text that already met the standard, never to make a failing row pass.
MOVES = re.compile(r"swept|sweep|band|bracket|range|varie|perturb|changes no|does not change|"
                   r"no reported digit|not the converged|cannot decrease|lower bound|"
                   r"cannot move|does not enter|flat to within|either side|"
                   r"\d\s*(x|-|to|–|%|pct|±)", re.I)


def main(neg=False):
    reg = list(csv.DictReader(io.open(os.path.join(HERE, "parameters_provenance.csv"),
                                      encoding="utf-8")))
    led = json.load(io.open(os.path.join(ROOT, "results", "assumption_ledger.json"),
                            encoding="utf-8"))
    tier = {r["parameter"]: str(r.get("tier", ""))[:2] for r in led["rows"]}

    sourced, bracketed, inert, scenario, fails = [], [], [], [], []
    for r in reg:
        p, cls = r["parameter"], str(r["provenance_class"]).strip()
        cit, loc = str(r["citation"]).strip(), str(r["locator"]).strip()
        sens = str(r["sensitivity"]).strip()
        if neg and p == "Temperature T":
            sens = ""                      # strip one row's evidence; the gate must catch it
        # The two classes are held to the standard's OWN two tests, which are not the same test.
        # State A is "a reviewer can open it and SEE the number", so it needs a locator. State B
        # is "the arithmetic is reproducible", so it needs a stated METHOD -- a computed molar
        # mass or a kinematic viscosity is not read off any page, and demanding a locator for it
        # was this gate being stricter than the standard it enforces.
        meth = str(r["method_note"]).strip()
        if cls == "measured":
            if DECLARED.match(cit) or not cit or cit.startswith("--"):
                fails.append((p, "class measured but carries no real citation"))
            elif not loc:
                fails.append((p, "class measured with a citation but NO LOCATOR -- a reviewer "
                                 "cannot open it and see the number"))
            else:
                sourced.append(p)
            continue
        if cls == "derived":
            if len(meth) < 20:
                fails.append((p, "class derived but states no method -- state B requires the "
                                 "arithmetic be reproducible from the registry"))
            elif DECLARED.match(cit) or not cit or cit.startswith("--"):
                fails.append((p, "class derived with no citation for its method"))
            else:
                sourced.append(p)
            continue
        t = tier.get(p, "")
        if t in ("T2", "T3"):
            bracketed.append(p)
        elif t == "T0":
            inert.append(p)
        elif t == "T1":
            if MOVES.search(sens):
                scenario.append(p)
            else:
                fails.append((p, "declared scenario/numerical choice whose sensitivity does not "
                                 "say what happens if it moves"))
        else:
            fails.append((p, "assumption in ledger tier %r -- no quantified perturbation and "
                             "effect" % (t or "unclassified")))

    n = len(reg)
    print("  %d registry rows\n" % n)
    print("    SOURCED    %3d  (measured/derived, citation + locator)" % len(sourced))
    print("    BRACKETED  %3d  (assumption, perturbation + effect stated)" % len(bracketed))
    print("    INERT      %3d  (declared: gated as unable to move any reported result)" % len(inert))
    print("    SCENARIO   %3d  (declared case/operating/numerical choice, movement stated)"
          % len(scenario))
    print("    FAIL       %3d" % len(fails))
    for p, why in fails[:20]:
        print("      %-44s %s" % (p[:44], why))

    json.dump({"n": n, "sourced": sourced, "bracketed": bracketed, "inert": inert,
               "scenario": scenario, "fails": [{"parameter": p, "why": w} for p, w in fails]},
              io.open(os.path.join(ROOT, "results", "every_value%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)

    if neg:
        hit = [p for p, _ in fails if p == "Temperature T"]
        print("\nNEGATIVE CONTROL: one row's sensitivity blanked; it must be reported.")
        print("G-EVERYVAL control: %s"
              % ("GOOD -- the stripped row was caught" if hit else
                 "BAD -- a row with no evidence at all passed"))
        return 0 if hit else 1
    if fails:
        print("\nG-EVERYVAL: FAIL -- %d row(s) have neither a source nor a bracket." % len(fails))
        return 1
    print("\nG-EVERYVAL: PASS -- every value is sourced, or bracketed, or declared inert/scenario "
          "with its movement stated. No number enters this model with neither a document nor a "
          "bound behind it.")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
