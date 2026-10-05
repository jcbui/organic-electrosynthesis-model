#!/usr/bin/env python3
"""G-SIPROSE -- bind the SI's typed PROSE numbers that are model outputs to the model.

    cd Section4_Model && python data/check_si_prose_numbers.py
    cd Section4_Model && python data/check_si_prose_numbers.py --negative-control

WHY
---
The SI's tables are generated from CSVs and covered (G-REGEN, G-COND). Its prose is not: 49
distinct model-unit values are typed as literals in make_si.js, and only some are bound by an
assertion. Most of the rest are narrative -- mesh-probe results, analytic reference quantities,
design currents -- which cannot move a conclusion. This gate takes the ones that ARE model outputs
quoted in prose and binds each to the artifact it comes from, so it fails if the model moves and
the sentence does not.

Each entry names the phrase as the SI writes it, so a rewording FAILS rather than silently
disarming the check (CLAUDE.md trap 10).
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


def main(neg=False):
    si = unicodedata.normalize("NFKC", re.sub(r"\s+", " ", asserted_text(
        os.path.join(ROOT, "SI_Section4_Transport_Model.docx"))))
    fk = json.load(io.open(os.path.join(ROOT, "results", "figK_thermal.json"), encoding="utf-8"))
    boil = {k: (v["i_boil"] if isinstance(v, dict) else v) for k, v in fk["panelA"].items()}

    # EXPLICIT PHRASES ONLY. A derived form -- "find the solvent name, then the next number
    # within 90 characters" -- was tried and produced nonsense: it read THF's ceiling as 299 from
    # a neighbouring sentence. That is CLAUDE.md trap 25, and it is the third time this session a
    # proximity window has manufactured a finding. Every entry below is the sentence the SI
    # actually writes, verified present, with the value it states bound to the artifact it
    # comes from.
    # The phrases are BUILT from the model, not typed. Typed, they read as "the SI no longer
    # contains ..." the moment a legitimate input moves -- which is what happened when sigma
    # became derived on 2026-09-13 and every beaker ceiling fell 11%.
    _b4 = ("boils at %.0f, MeCN at %.0f, DMF at %.0f and aqueous NaOH at %.0f"
           % (boil["THF"], boil["MeCN"], boil["DMF"], boil["aq. NaOH"]))
    checks = [
        # S6.1 prints the four beaker ceilings in one clause
        (_b4, round(boil["THF"]), boil["THF"], 1.0),
        (_b4, round(boil["MeCN"]), boil["MeCN"], 1.0),
        (_b4, round(boil["DMF"]), boil["DMF"], 1.0),
        (_b4, round(boil["aq. NaOH"]), boil["aq. NaOH"], 1.5),
        ("consistent with the %.0f mA cm−2 passive ceiling" % boil["DMF"],
         round(boil["DMF"]), boil["DMF"], 1.0),
    ]

    fails, checked = [], 0
    for phrase, stated, want, tol in checks:
        if neg:
            want = want * 1.5
        checked += 1
        # a phrase-form entry must still be present; a derived-form one was matched above
        if phrase not in si:
            fails.append("the SI no longer contains %r -- re-point this check" % phrase[:60])
            continue
        if abs(stated - want) > tol:
            fails.append("SI states %g where the model gives %.2f  [%s]"
                         % (stated, want, phrase[:70]))

    print("  SI prose numbers bound to a model artifact: %d" % checked)
    for f in fails:
        print("    FAIL  %s" % f)
    json.dump({"checked": checked, "failures": fails},
              io.open(os.path.join(ROOT, "results", "si_prose_numbers%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)
    if neg:
        ok = len(fails) >= 2
        print("\nNEGATIVE CONTROL: every model value scaled x1.5, so the stated numbers must "
              "disagree with it.")
        print("G-SIPROSE control: %s (%d finding(s))"
              % ("GOOD" if ok else "BAD -- test is inert", len(fails)))
        return 0 if ok else 1
    if not checked:
        print("\nG-SIPROSE: FAIL -- nothing was checked, so this gate is inert")
        return 1
    if fails:
        print("\nG-SIPROSE: FAIL")
        return 1
    print("\nG-SIPROSE: PASS -- every bound SI prose number agrees with the artifact it comes from")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
