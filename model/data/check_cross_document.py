#!/usr/bin/env python3
"""G-XDOC -- do the manuscript, the SI and the matrix state the same counts?

    cd Section4_Model && python data/check_cross_document.py
    cd Section4_Model && python data/check_cross_document.py --negative-control

WHY
---
G-MSDERIVED checks the manuscript against the model and G-SIDERIVED checks the SI against it, each
through an explicit list of anchored phrases. A number stated in a sentence that is on NEITHER
list is checked by nothing -- and one was: the SI read "9/50 reactions clear it in an unstirred
cell, 34/50 at a rotating-cylinder electrode" for weeks. The matrix gives 33, and the manuscript
says 33. It was found by reading, not by a gate.

THE TEST, AND WHY IT IS NOT PROXIMITY MATCHING
----------------------------------------------
The first version of this gate took a +/-90-character window around each "N/50" and tagged it to
every architecture named inside. A sentence reading "the 9/50 clearing 50 unstirred rises to 33/50
in a rotating-cylinder cell" then attributed 33 to BOTH archetypes, and the gate reported three
disagreements that did not exist. That is CLAUDE.md trap 25 -- text proximity is not evidence --
committed inside a new gate.

What actually caught the real defect needs no window at all: **34 is not a number the matrix
produces for any architecture at either threshold.** Membership in the model's own set of counts
is the whole test. It is blind to which architecture a sentence is about, which is exactly why it
cannot be fooled by a sentence that mentions two.
"""
import io
import json
import os
import re
import sys
import unicodedata

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from docx_text import asserted_text                                    # noqa: E402
from latest_ms import latest_ms   # one resolver for every gate (see its docstring)

ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
# "N/50"-shaped strings that are NOT architecture counts, each declared with what it is so the
# membership test cannot be quietly widened to swallow a real error.
DECLARED_NON_COUNTS = {
    50: "the set size itself (\"50 of 50\", \"one of 50\")",
    56: "the 56 mediated solver cells (8 mediated rows x 7 architectures)",
}


def newest_ms():
    # was: sorted(...)[-1] over revised_outline_v\d+, which is a LEXICAL sort -- "v99" sorts after
    # "v130" -- on a naming scheme the lineage left behind, so this gate had been reading v99.
    return latest_ms()


def norm(p):
    return unicodedata.normalize("NFKC", re.sub(r"\s+", " ", asserted_text(p)))


def main(neg=False):
    ms_path = newest_ms()
    ms, si = norm(ms_path), norm(os.path.join(ROOT, "SI_Section4_Transport_Model.docx"))
    mat = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    _rce50 = int((mat["rce"] >= 50).sum())
    if neg:
        # 2026-09-11: the probe follows the matrix (trap 10 aimed at a control): the SI prints the CURRENT
        # rotating-cylinder >=50 count, and the control rewrites it one higher, which the matrix never produces
        _cur, _bad = "%d/50 at a rotating-cylinder" % _rce50, "%d/50 at a rotating-cylinder" % (_rce50 + 1)
        if _cur not in si:
            print("G-XDOC control: BAD -- the probe %r is not in the SI, so the control cannot perturb it" % _cur); return 1
        si = si.replace(_cur, _bad)

    legal = {int((mat[k] >= thr).sum()) for k in ARCH for thr in (25, 50)}
    legal |= set(DECLARED_NON_COUNTS)
    print("  MS: %s" % os.path.basename(ms_path))
    print("  counts the matrix produces: %s" % sorted(legal - set(DECLARED_NON_COUNTS)))
    print("  declared non-counts: %s" % sorted(DECLARED_NON_COUNTS))

    fails, checked = [], 0

    # (1) MEMBERSHIP, applied to the MANUSCRIPT only. The manuscript states published counts; the
    # SI additionally reports counts UNDER STATED PERTURBATIONS ("the count falls from 12/50 to
    # 11/50 once D_S is 7.6% below its Wilke-Chang value"), which are legitimately not baseline
    # values. Running membership over the SI flagged seven such sentences plus two unit strings
    # ("25 / 50 mA cm-2"), i.e. it could not tell a swept count from a stale one. Rather than
    # bolt on a hypothetical-sentence detector -- proximity matching again, by another name --
    # the blanket test is applied where it is sound, and the SI's one headline sentence is
    # anchored explicitly below.
    for m in re.finditer(r"(?<![\d.])(\d+)\s*(?:/|of)\s*50\b", ms):
        n = int(m.group(1))
        checked += 1
        if n not in legal:
            fails.append("MS states %d/50, which is no architecture count the matrix produces: "
                         "...%s..." % (n, ms[max(0, m.start() - 70):m.end() + 40]))

    # (2) the SI sentence that carried the stale 34/50, anchored by its own wording and required
    # to be present (trap 10: a vanished phrase is a failure, not a skip).
    anchor = r"(\d+)/50 reactions clear it in an unstirred cell, (\d+)/50 at a rotating-cylinder"
    m = re.search(anchor, si)
    checked += 1
    if not m:
        fails.append("the SI's unstirred/rotating-cylinder sentence is gone; re-point this check")
    else:
        want = (int((mat["natural"] >= 50).sum()), int((mat["rce"] >= 50).sum()))
        got = (int(m.group(1)), int(m.group(2)))
        if got != want:
            fails.append("SI says %d/50 unstirred and %d/50 rotating-cylinder clear 50 mA cm-2; "
                         "the matrix gives %d and %d" % (got + want))

    # the MS median ladder: one sentence, each value bound to its architecture BY POSITION, printed at the
    # document's precision (one decimal below 100 mA cm-2, integers above). Declared omission: the RDE, which
    # the sentence leaves out (it lists the six reactor archetypes; the RDE is the analytical reference).
    med = [round(float(mat[k].median()), 1) for k in ARCH]
    LADDER = [k for k in ARCH if k != "rde"]
    fmt = lambda v: ("%.0f" % v) if v >= 100 else ("%.1f" % v)
    m = re.search(r"median limiting current density rises from (.*?)\.\s+[A-Z]", ms)
    checked += 1
    if not m:
        fails.append("the MS median-ladder sentence is gone; re-point this check")
    else:
        _lad = m.group(1)
        if neg:      # perturb the DOCUMENT's third rung, so the sentence regex is exercised, not a parsed list
            _r3 = re.findall(r"(\d+(?:\.\d+)?) mA cm", _lad)[2]
            _lad = _lad.replace(_r3 + " mA cm", "%.1f mA cm" % (float(_r3) + 0.5), 1)
        got = re.findall(r"(\d+(?:\.\d+)?) mA cm", _lad)
        want = [fmt(float(mat[k].median())) for k in LADDER]
        if got != want:
            fails.append("MS median ladder prints %s; the matrix gives %s (in the order %s)"
                         % (got, want, LADDER))

    print("\n  %d comparisons" % checked)
    for f in fails:
        print("    FAIL  %s" % f[:190])
    json.dump({"ms": os.path.basename(ms_path), "checked": checked,
               "legal_counts": sorted(legal), "medians": med, "failures": fails},
              io.open(os.path.join(ROOT, "results", "cross_document%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)
    if neg:
        ok = any(("%d/50" % (_rce50 + 1)) in f for f in fails) and any("median ladder prints" in f for f in fails)
        print("\nNEGATIVE CONTROL: the SI's rotating-cylinder count rewritten %d -> %d, the exact "
              "kind of stale literal this gate exists to catch." % (_rce50, _rce50 + 1))
        print("G-XDOC control: %s (%d finding(s))"
              % ("GOOD" if ok else "BAD -- test is inert", len(fails)))
        return 0 if ok else 1
    if not checked:
        print("\nG-XDOC: FAIL -- nothing was compared, so this gate is inert")
        return 1
    if fails:
        print("\nG-XDOC: FAIL -- %d disagreement(s)" % len(fails))
        return 1
    print("\nG-XDOC: PASS -- every 'N/50' the manuscript states is a count the matrix produces, "
          "the SI's unstirred/rotating-cylinder sentence matches the matrix, and the MS median ladder prints "
          "each archetype's median in order, the RDE declared omitted (%d checks)" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
