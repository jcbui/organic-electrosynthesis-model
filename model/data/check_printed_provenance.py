#!/usr/bin/env python3
"""G-PROVPRINT -- for every number printed with a model unit, CAN it go stale, and would we know?

    cd Section4_Model && python data/check_printed_provenance.py
    cd Section4_Model && python data/check_printed_provenance.py --verbose
    cd Section4_Model && python data/check_printed_provenance.py --negative-control

WHY THIS IS NOT A MEMBERSHIP TEST
---------------------------------
The obvious design -- "does this printed value exist somewhere in the model's outputs?" -- was
built first and thrown away, because it is nearly vacuous here. The published matrix alone holds
300 cells spanning 0.3 to 3000 mA cm-2; with the ~0.6% tolerance that printed rounding forces
(282.4 appears as 283), **54% of RANDOM values in 1-50 mA cm-2 match the pool by chance.** A gate
answering "traces to the model" would have reported 183 of 183 and meant almost nothing. That
calibration is printed below so the number cannot be over-read.

WHAT IS ACTUALLY DECIDABLE
--------------------------
Whether a printed number can drift at all, and whether anything would notice:

    COMPUTED    interpolated into the SI at build time from a model artifact -- the numeral does
                not exist in make_si.js, only an expression does. It CANNOT go stale.
    ANCHORED    typed, but sitting inside a phrase that a document-reading gate binds to a model
                value (G-MSDERIVED, G-SIDERIVED, G-MSKAPPA, G-SCRANGE, ...). Drift fails a gate.
    UNANCHORED  typed and bound by nothing. Mostly one-off analysis results and quoted exemplar
                conditions in methods prose -- they cannot move a published conclusion -- but
                nothing would catch them going stale.

UNANCHORED is the honest risk set and is held at a reviewed baseline. It is not a defect list.
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

UNITS = [(r"(\d+(?:\.\d+)?)\s*mA\s*cm[−\-]?2", "mA/cm2"),
         (r"(\d+(?:\.\d+)?)\s*mS\s*cm[−\-]?1", "mS/cm"),
         (r"(\d+(?:\.\d+)?)\s*W\s*cm[−\-]?2", "W/cm2"),
         (r"(\d+(?:\.\d+)?)\s*S\s*m[−\-]?1", "S/m")]
GATES = ["check_ms_derived.py", "check_si_derived.py", "check_ms_numbers.py",
         "check_ecprime_band.py", "schmidt_extrapolation.py", "dilute_theory_stratify.py",
         "reactor_engineering.py", "hint_series_bound.py", "check_cross_document.py",
         "check_si_bounds.py", "analysis_kappaT_sensitivity.py"]
BASELINE_MS, BASELINE_SI = 25, 101        # reviewed 2026-08-31, set to the measured residue.


def newest_ms():
    d = os.path.join(os.path.dirname(ROOT), "MS Drafts")
    c = sorted(f for f in os.listdir(d) if re.match(r"revised_outline_v\d+_RCE.*\.docx$", f))
    return os.path.join(d, c[-1])


def anchor_phrases():
    """Phrases a gate actually ASSERTS, taken from call sites -- not from prose.

    Harvesting every quoted string in the gate files swept in docstring examples and retired
    wordings alongside live anchors ("29 mA cm-2" with an ASCII hyphen appears in a comment
    explaining a past defect, while the live want() uses U+2212). That inflated the apparent
    anchor set while leaving the real coverage unmeasured -- noise in both directions. Only the
    first string argument of want(), want_ordered() and the `in t` / `not in t` membership tests
    is a phrase the gate binds to the document.
    """
    out = set()
    srcs = []
    for g in GATES:
        for d in ("data", "figs"):
            fp = os.path.join(ROOT, d, g)
            if os.path.exists(fp):
                srcs.append(fp)
    ms_scripts = os.path.join(os.path.dirname(ROOT), "MS Drafts", "scripts")
    if os.path.isdir(ms_scripts):
        srcs += [os.path.join(ms_scripts, f) for f in sorted(os.listdir(ms_scripts))
                 if f.startswith("verify_v") and f.endswith(".py")]
    pats = [r'want(?:_ordered)?\(\s*"[^"]*"\s*,\s*"([^"\n]+)"',   # want(label, phrase, ...)
            r'"([^"\n]{6,160})"\s+(?:not\s+)?in\s+(?:t|ms|si|txt)\b']
    for fp in srcs:
        src = io.open(fp, encoding="utf-8").read()
        for pat in pats:
            for m in re.finditer(pat, src):
                ph = m.group(1)
                if re.search(r"\d", ph):
                    out.add(unicodedata.normalize("NFKC", ph))
    return out


def main(verbose=False, neg=False):
    phr = anchor_phrases()
    js_str = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"',
                                io.open(os.path.join(ROOT, "make_si.js"),
                                        encoding="utf-8").read()))
    if neg:
        phr = set()                     # no gate anchors anything: everything must go UNANCHORED
    docs = {"MS": newest_ms(), "SI": os.path.join(ROOT, "SI_Section4_Transport_Model.docx")}
    report, rc = {}, {}
    for lab, path in docs.items():
        t = unicodedata.normalize("NFKC", re.sub(r"\s+", " ", asserted_text(path)))
        spans = []
        for q in phr:
            i = t.find(q)
            while i >= 0:
                spans.append((i, i + len(q)))
                i = t.find(q, i + 1)
        rows, seen = [], set()
        for pat, unit in UNITS:
            for m in re.finditer(pat, t):
                key = (m.group(1), unit)
                if key in seen:
                    continue
                seen.add(key)
                v = m.group(1)
                anchored = any(a <= m.start() < b for a, b in spans)
                # the MS is a .docx: every number in it is typed. The SI is generated, so a
                # numeral absent from make_si.js's string literals was interpolated.
                computed = (lab == "SI"
                            and not re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", js_str))
                cls = "COMPUTED" if computed else ("ANCHORED" if anchored else "UNANCHORED")
                rows.append({"value": v, "unit": unit, "class": cls,
                             "ctx": t[max(0, m.start() - 62):m.end() + 30]})
        report[lab] = rows
        rc[lab] = {c: sum(1 for r in rows if r["class"] == c)
                   for c in ("COMPUTED", "ANCHORED", "UNANCHORED")}
        print("  %-3s %3d distinct model-unit numbers: %3d computed at build time, %3d anchored "
              "by a gate, %3d unanchored"
              % (lab, len(rows), rc[lab]["COMPUTED"], rc[lab]["ANCHORED"],
                 rc[lab]["UNANCHORED"]))

    if verbose:
        print("\n  unanchored (typed, bound by nothing):")
        for lab in docs:
            for r in report[lab]:
                if r["class"] == "UNANCHORED":
                    print("    %-3s %-9s %-7s ...%s..." % (lab, r["value"], r["unit"],
                                                           r["ctx"][:72]))

    json.dump({"counts": rc, "rows": report,
               "baseline": {"MS": BASELINE_MS, "SI": BASELINE_SI}},
              io.open(os.path.join(ROOT, "results", "printed_provenance%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)

    print("\n  CALIBRATION: a membership test against the model's own outputs would be nearly "
          "vacuous here -- 54% of random values in 1-50 mA cm-2 fall within 0.6% of some cell of "
          "the 300-cell matrix. That is why this gate measures drift-exposure, not membership.")

    if neg:
        ok = rc["MS"]["ANCHORED"] == 0 and rc["SI"]["ANCHORED"] == 0
        print("\nNEGATIVE CONTROL: the anchor-phrase set was emptied, so nothing may read as "
              "ANCHORED.")
        print("G-PROVPRINT control: %s (MS anchored %d, SI anchored %d)"
              % ("GOOD" if ok else "BAD -- test is inert",
                 rc["MS"]["ANCHORED"], rc["SI"]["ANCHORED"]))
        return 0 if ok else 1
    bad = []
    if rc["MS"]["UNANCHORED"] > BASELINE_MS:
        bad.append("MS %d > %d" % (rc["MS"]["UNANCHORED"], BASELINE_MS))
    if rc["SI"]["UNANCHORED"] > BASELINE_SI:
        bad.append("SI %d > %d" % (rc["SI"]["UNANCHORED"], BASELINE_SI))
    if bad:
        print("\nG-PROVPRINT: FAIL -- the unanchored set grew: %s" % "; ".join(bad))
        return 1
    print("\nG-PROVPRINT: PASS -- unanchored sets at or below their reviewed baselines "
          "(MS %d/%d, SI %d/%d)" % (rc["MS"]["UNANCHORED"], BASELINE_MS,
                                    rc["SI"]["UNANCHORED"], BASELINE_SI))
    return 0


if __name__ == "__main__":
    sys.exit(main(verbose="--verbose" in sys.argv, neg="--negative-control" in sys.argv))
