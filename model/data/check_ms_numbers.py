"""Every conductivity the MANUSCRIPT asserts must be traceable to a registry row the SI prints.

    cd Section4_Model && python data/check_ms_numbers.py
    cd Section4_Model && python data/check_ms_numbers.py --negative-control

WHY THIS GATE IS DIFFERENT FROM THE OTHERS
------------------------------------------
Most checks in this project compare a figure to the file it was computed from, which cannot fail
in an interesting way. This one asserts against the PUBLISHED MANUSCRIPT: it reads document.xml
out of the .docx a reader would receive and requires every κ printed there to have a registry row
that survives into the SI.

It exists because two numbers had already slipped through, both the same way. "Used" was defined
as "named by one of the 50 reactions", and the manuscript is a consumer that definition cannot
see:

  * `1 M NaOH aq` -- one of the four conductivities carrying a Fig. K verdict -- had NO registry
    row, so the provenance shown for it in Table S4 came from a typed literal in make_si.js.
  * `0.1 M Bu4NBF4/DMF` is quoted in the body as "κ = 3.5 mS cm-1", with a worked example built on
    it (a 16.8 V cell, 14.3 V ohmic, 1.4 W cm-2), yet was carried as `unused-legacy (no registry
    row)`.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not fire merely because the manuscript NAMES an electrolyte. The body mentions
`1 M LiBF4/THF` purely as a literature precedent, attributed to Krempl, Heenan and Li; it quotes
no conductivity for it and leans on no row of ours. Demanding a registry entry there would
re-import exactly the display-only bloat the SI was trimmed of. What must be traceable is a
number the manuscript states AS OURS.

The liveness half matters because the SI now publishes only its load-bearing subset: a row can
exist in the registry and still be trimmed out of the SI. A number printed in the manuscript
whose provenance is omitted from the SI is unverifiable to a reader, so LIVENESS -- not mere
existence -- is what is asserted.
"""
import json
import os
import re
import sys
import unicodedata
import zipfile

from docx_text import asserted_text as _shared_asserted_text

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
from latest_ms import latest_ms   # shared resolver; the private copy here was pinned to a
# naming scheme the lineage left behind, so it gated a document 25 builds stale (2026-09-29)


MS = latest_ms()
# TWO unit conventions, because the manuscript uses both and the first version of this gate
# only knew one. The body writes "kappa = X mS cm-1"; the Figure 5 caption writes "X S m-1", and
# three of its four conductivities carry no "kappa =" prefix at all -- they sit inside the
# electrolyte parenthetical, "(0.2 M NaI, 0.877 S m-1)". That blind spot is exactly why the
# caption's MeCN, DMF and aq. NaOH values went stale through v27 while every artwork gate passed.
# docx_text() NFKC-normalises, so the superscripts are plain "-1" / "-2" by the time we match.
KAPPA_MS_RE = re.compile(r"κ\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*mS")
# NFKC folds the SUPERSCRIPT MINUS U+207B to MINUS SIGN U+2212, *not* to an ASCII hyphen, so
# a literal "m-1" in the pattern matches nothing. Accept the whole dash family.
DASH = "[-\u2010-\u2015\u2212]"
KAPPA_SM_RE = re.compile(r"(?<![A-Za-z\u00b5])([0-9]+(?:\.[0-9]+)?)\s*S\s*m" + DASH + "1")


def quoted_kappas(ms):
    """Every conductivity the manuscript states: (mS cm-1, printed form, surrounding context)."""
    out = []
    for rx, scale, unit in ((KAPPA_MS_RE, 1.0, "mS cm-1"), (KAPPA_SM_RE, 10.0, "S m-1")):
        for m in rx.finditer(ms):
            ctx = ms[max(0, m.start() - 160):m.end() + 60]
            out.append((float(m.group(1)) * scale, "%s %s" % (m.group(1), unit), ctx))
    return out


def tokens_of(name):
    """The identifying tokens of an electrolytes.csv row: concentration, salt, solvent.

    "0.25 M Bu4NBF4/MeCN" -> ("0.25 M", "Bu4NBF4", "MeCN");  "1 M NaOH aq" -> ("1 M","NaOH","aq")
    """
    salt_part, _, solv = name.partition("/")
    bits = salt_part.split()
    conc = " ".join(bits[:2]) if len(bits) > 1 and bits[1] == "M" else bits[0]
    rest = bits[2:] if conc.endswith("M") and len(bits) > 1 else bits[1:]
    toks = [conc] + rest + ([solv] if solv else [])
    return tuple(t for t in toks if t)


def bind(ctx, ele):
    """Which registry electrolyte does the text AROUND this number name, if any?

    Value-only matching is not enough. "1.995 S m-1" happens to sit within 5% of
    `0.3 M LiClO4/MeCN`, an electrolyte the Figure 5 caption has nothing to do with -- so a
    caption number that went stale to any coincidentally-registered value would PASS. Binding
    the number to the electrolyte printed beside it is what makes the gate about this claim.
    """
    return [n for n in (str(x) for x in ele.iloc[:, 0])
            if all(t in ctx for t in tokens_of(n))]


def docx_text(p):
    """Asserted text, via the shared cross-checked reader (data/docx_text.py).

    Was a local regex here. It got the <w:del> tag boundary wrong and hid 1,846 characters
    of the manuscript -- the whole Figure 2 caption among them -- from this gate while it
    reported PASS. The shared module parses structurally and asserts the structural walk
    and the regex agree, so the bug class cannot come back in one file at a time.
    """
    return _shared_asserted_text(p)

def main(negative_control=False):
    ms = docx_text(MS)
    if negative_control:
        # One injection per unit convention: a gate that only proves the mS branch fires would
        # have said nothing about the S m-1 branch, which is the one that was missing.
        # Each injection is padded apart: bind() reads a +/-160-character window, so controls
        # written back-to-back land in one another's context and cross-attribute.
        pad = " ." * 200
        ms += pad + " The supporting electrolyte had κ = 77.7 mS cm-1 throughout."
        ms += pad + " A second cell used an electrolyte of 6.66 S m\u22121."
        # The failure this gate was BUILT for: a caption number left behind by a provenance
        # upgrade. 0.877 is a real registry value -- DMF's -- so value-only matching passes it.
        ms += pad + " and MeCN (0.25 M Bu4NBF4, 0.877 S m\u22121) follows"

    ele = pd.read_csv(os.path.join(HERE, "electrolytes.csv"))
    reg = pd.read_csv(os.path.join(HERE, "parameters_provenance.csv"))
    with open(os.path.join(ROOT, "results", "registry_liveness.json")) as f:
        dead = set(json.load(f)["dead_parameters"])
    regset = set(reg.parameter)

    fails = []
    quoted = quoted_kappas(ms)
    print("conductivities asserted in the manuscript (body + captions): %d" % len(quoted))
    for q, shown, ctx in quoted:
        named = bind(ctx, ele)
        if named:
            # BOUND: the text names an electrolyte, so that row's value is what must agree.
            ok = [n for n in named
                  if abs(float(ele.loc[ele.iloc[:, 0] == n, "kappa_mScm"].iloc[0]) - q)
                  <= 0.05 * max(q, 1e-9)]
            if not ok:
                have = ", ".join("%s = %g" % (n, float(ele.loc[ele.iloc[:, 0] == n,
                                                              "kappa_mScm"].iloc[0]))
                                 for n in named)
                fails.append("MS prints %s for %s, but the registry carries %s mS/cm -- the "
                             "manuscript is STALE against the model" % (shown, named[0], have))
                print("   %-12s (= %-7g mS/cm) -> %-26s STALE (registry: %s)"
                      % (shown, q, named[0], have))
                continue
            names = ok
        else:
            hit = ele[(ele.kappa_mScm - q).abs() <= 0.05 * max(q, 1e-9)]
            if hit.empty:
                fails.append("MS asserts kappa = %g mS/cm but no electrolyte in the registry "
                             "carries that value" % q)
                print("   %-12s (= %-7g mS/cm) -> NO MATCHING ELECTROLYTE" % (shown, q))
                continue
            names = [str(n) for n in hit.iloc[:, 0]]
        live = [n for n in names if n in regset and n not in dead]
        print("   %-12s (= %-7g mS/cm) -> %-26s %s"
              % (shown, q, names[0],
                 "traceable in the SI" if live else "NOT TRACEABLE IN THE SI"))
        if not live:
            fails.append("MS asserts kappa = %g mS/cm (%s) but no registry row that the SI prints "
                         "backs it" % (q, names[0]))

    named = []
    for e in ele.iloc[:, 0]:
        e = str(e)
        salt, _, solv = e.partition("/")
        pats = [e, e.replace("/", " in "), e.replace("/", " / ")]
        if solv:
            pats.append(salt + " in " + solv.split(" ")[0])
        if any(p in ms for p in pats):
            named.append(e)
    print("\nelectrolytes the manuscript names (informational, not asserted): %d" % len(named))
    for e in named:
        st = reg.loc[reg.parameter == e, "provenance_class"]
        print("   %-28s %-14s %s" % (e, st.iloc[0] if len(st) else "no registry row",
                                     "trimmed from SI" if e in dead else "in SI"))

    print("\nG-MSKAPPA: %s" % ("PASS" if not fails else "FAIL"))
    for f_ in fails:
        print("  " + f_)

    if negative_control:
        ms_fired = any("77.7" in f_ for f_ in fails)
        sm_fired = any("66.6" in f_ for f_ in fails)
        bind_fired = any("STALE" in f_ and "Bu4NBF4/MeCN" in f_ for f_ in fails)
        print("\nnegative control: injected 'κ = 77.7 mS cm-1' AND '6.66 S m-1'")
        print("  mS cm-1 branch fired: %s" % ms_fired)
        print("  S m-1   branch fired: %s" % sm_fired)
        print("  stale-caption binding fired (0.877 attributed to MeCN): %s" % bind_fired)
        if not (ms_fired and sm_fired and bind_fired):
            raise AssertionError("negative control did not fire on all three (mS %s, S/m %s, "
                                 "binding %s); the gate cannot detect the failure it exists to "
                                 "catch" % (ms_fired, sm_fired, bind_fired))
        return
    if fails:
        raise AssertionError("; ".join(fails))
    print("  every conductivity the manuscript asserts has a registry row that the SI prints")


if __name__ == "__main__":
    main(negative_control="--negative-control" in sys.argv)
