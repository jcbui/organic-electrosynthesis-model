#!/usr/bin/env python3
"""G-ANACONST -- no solvent property typed into the ANALYSIS layer may disagree with the registry.

    cd Section4_Model && python data/check_analysis_constants.py
    cd Section4_Model && python data/check_analysis_constants.py --negative-control

WHY
---
G-CODECONST (data/check_code_constants.py) compares 16 solver constants against the registry, but
it scans `julia/` ONLY -- five files. Nothing checked the Python analysis layer, and on 2026-08-30
that gap was found to be live: `figs/analysis_catalyst_D_sensitivity.py` and
`figs/anchored_diffusivity.py` both still carried mu(MeCN) = 0.343 mPa s, three days after
solvents.csv moved to the 0.369 the CRC page actually prints -- and the first of them carried a
CRC citation on the same line, i.e. it cited a page for a number the page does not carry.

Nothing about that was subtle. It survived because no gate looked at those files.

HOW IT DECIDES, WITHOUT AN ENUMERATED LIST
------------------------------------------
An enumerated list of (file, constant) pairs goes stale the moment someone adds a file -- the
defect this gate exists to catch is exactly a file nobody remembered. So it DISCOVERS instead:
walk every .py under data/ and figs/, find assignments and keyword arguments whose NAME denotes a
solvent property (mu/eta/visc, rho/dens, M/mw), attribute each to a solvent named on the same line
or within three lines, and require the literal to equal what solvents.csv carries for that pair.

Binding the number to the solvent NAMED BESIDE IT is deliberate: CLAUDE.md trap 11 records a gate
that accepted any registry entry within 5% and so resolved a conductivity to an electrolyte the
caption had nothing to do with. A value-only match passes on coincidence.

Units are handled by trying the registry value in both mPa s and Pa s (and g/mL vs kg/m3), because
the analysis layer stores viscosity both ways; a literal matching EITHER convention is accepted.
"""
import io
import os
import re
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKIP = re.compile(r"\.bak_|_archive|__pycache__")
# property name -> (csv column, plausible unit multipliers applied to the registry value)
PROPS = {
    "mu":   ("mu_mPas", [1.0, 1e-3]),
    "eta":  ("mu_mPas", [1.0, 1e-3]),
    "visc": ("mu_mPas", [1.0, 1e-3]),
    "rho":  ("rho",     [1.0, 1000.0]),
    "dens": ("rho",     [1.0, 1000.0]),
    "mw":   ("M",       [1.0]),
}
# case-insensitive: the second real defect site was `MU_MECN = 0.343e-3`, in caps, and a
# case-sensitive pattern walked straight past it.
NAME = re.compile(r"\b(\w*?(mu|eta|visc|rho|dens|mw)\w*?)\s*=\s*(-?\d+\.\d+(?:[eE][-+]?\d+)?)",
                  re.IGNORECASE)


def code_only(path):
    """Return the source with every COMMENT and STRING token blanked, line numbers preserved.

    THIS IS THE SIXTH TIME THIS REPOSITORY HAS HIT THE SAME TRAP: prose that DESCRIBES a value,
    read as the value. The first version of this gate reported 13 findings and every one of them
    was inside a docstring or a citation note -- lines like "eta = 0.346 cP, reproduce the CRC
    MeCN entries" are provenance prose, not constants. G-CODECONST learned this and strips
    comments; a regex over raw text cannot tell an assignment from a sentence about one.
    """
    lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    try:
        with io.open(path, "rb") as fh:
            toks = list(tokenize.tokenize(fh.readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return None                      # unparseable: report rather than guess
    # Blanking EVERY string went too far the other way: solvent names live in string literals
    # ("MeCN", or a dict key), so removing them left nothing to attribute a value to and the gate
    # checked zero constants -- inert, which is worse than noisy. Blank comments always, and
    # blank only strings long enough to be PROSE. A citation note runs to hundreds of characters;
    # a solvent key is six. PROSE_MIN is the line between them.
    # A LENGTH threshold was tried first and is wrong: implicit concatenation splits a citation
    # across fragments, and a short continuation like "eta = 0.8455 mPa s at 298.15 K)." fell
    # under it and was read as code. Prose is distinguished by WHITESPACE, not by length --
    # a key or an identifier ("MeCN") has none, a sentence always does.
    def _keepable(tok):
        body = tok.string.lstrip("rbufRBUF").strip("\"'")
        return len(body) <= 24 and not re.search(r"\s", body)
    for t in toks:
        if t.type == tokenize.STRING and _keepable(t):
            continue
        if t.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        (r1, c1), (r2, c2) = t.start, t.end
        for r in range(r1, r2 + 1):
            if r - 1 >= len(lines):
                break
            ln = lines[r - 1]
            a_ = c1 if r == r1 else 0
            b_ = c2 if r == r2 else len(ln)
            lines[r - 1] = ln[:a_] + " " * max(0, b_ - a_) + ln[b_:]
    return lines


def solvents():
    import csv
    out = {}
    with io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["solvent"]] = r
    return out


def main(neg=False):
    sol = solvents()
    # longest names first so "MeCN/H2O" is preferred over "MeCN" on the same line
    names = sorted(sol, key=len, reverse=True)
    files = []
    for d in ("data", "figs"):
        p = os.path.join(ROOT, d)
        for f in sorted(os.listdir(p)):
            if f.endswith(".py") and not SKIP.search(f):
                files.append(os.path.join(p, f))

    inject = None
    if neg:
        # Put the real defect back, in the file it actually occurred in, and require the gate to
        # find it. A control that perturbs something the gate was never going to read proves
        # nothing; this reproduces the 2026-08-30 defect exactly.
        inject = os.path.join(ROOT, "figs", "anchored_diffusivity.py")
        orig = io.open(inject, encoding="utf-8").read()
        io.open(inject, "w", encoding="utf-8").write(
            orig.replace("mu_mPas=0.369", "mu_mPas=0.343"))

    bad, checked = [], 0
    try:
        for path in files:
            lines = code_only(path)
            if lines is None:
                bad.append((os.path.relpath(path, ROOT), 0, "<unparseable>", 0.0, "-", "-", 0.0))
                continue
            for i, ln in enumerate(lines):
                for m in NAME.finditer(ln):
                    var, kind, lit = m.group(1), m.group(2).lower(), float(m.group(3))
                    col, mults = PROPS[kind]
                    # Attribute from the VARIABLE NAME first -- `MU_MECN = 0.369e-3` names its
                    # own solvent and is one of the two real 2026-08-30 defect sites -- then fall
                    # back to a solvent named in the surrounding code.
                    up = var.upper()
                    hit = next((n for n in names
                                if re.search(r"(^|[^A-Z])%s([^A-Z]|$)" % re.escape(n.upper()), up)),
                               None)
                    if hit is None:
                        ctx = "\n".join(lines[max(0, i - 3): i + 1])
                        hit = next((n for n in names
                                    if re.search(r"\b%s\b" % re.escape(n), ctx)), None)
                    if hit is None:
                        continue
                    try:
                        want = float(sol[hit][col])
                    except (KeyError, ValueError):
                        continue
                    checked += 1
                    cands = [want * k for k in mults]
                    if any(abs(lit - c) <= 1e-9 * max(1.0, abs(c)) for c in cands):
                        continue
                    # only a literal that is PLAUSIBLY this property is a finding; a number three
                    # orders of magnitude away is some other quantity that happens to be spelled
                    # with these letters.
                    if not any(0.2 <= abs(lit / c) <= 5.0 for c in cands if c):
                        continue
                    bad.append((os.path.relpath(path, ROOT), i + 1, var, lit, hit, col, want))
    finally:
        if neg:
            io.open(inject, "w", encoding="utf-8").write(orig)

    print("  scanned %d analysis sources; %d typed solvent properties resolved to a named solvent"
          % (len(files), checked))
    for f, n, var, lit, s, col, want in bad:
        print("    %s:%d  %s = %g  but solvents.csv gives %s[%s] = %g"
              % (f, n, var, lit, s, col, want))

    if neg:
        found = [b for b in bad if "anchored_diffusivity" in b[0]]
        print("\nNEGATIVE CONTROL: mu(MeCN) reset to the retired 0.343 in anchored_diffusivity.py")
        print("G-ANACONST control: %s"
              % ("GOOD -- the gate finds it (%d finding(s))" % len(found) if found else
                 "BAD -- test is inert, the exact defect this gate exists for went undetected"))
        return 0 if found else 1
    if checked == 0:
        print("\nG-ANACONST: FAIL -- the scan resolved ZERO typed properties to a solvent, so it "
              "asserted nothing. That is an inert gate, not a clean repository; the attribution "
              "step is broken.")
        return 1
    if bad:
        print("\nG-ANACONST: FAIL -- %d typed solvent property/properties in the analysis layer "
              "disagree with solvents.csv. A number the registry has moved on from is not a "
              "rounding difference; if the analysis needs a different value it must say why on "
              "the line, not carry the old one silently." % len(bad))
        return 1
    print("\nG-ANACONST: PASS -- every solvent property typed into data/ and figs/ matches the "
          "registry value for the solvent named beside it")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
