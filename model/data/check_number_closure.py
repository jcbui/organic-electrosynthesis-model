#!/usr/bin/env python3
"""G-NUMCLOSE -- is there any number in the computational chain that nothing accounts for?

    cd Section4_Model && python data/check_number_closure.py
    cd Section4_Model && python data/check_number_closure.py --verbose
    cd Section4_Model && python data/check_number_closure.py --negative-control

WHY
---
The repo already checks numbers from several directions, but each covers a slice:

    G-EVERYVAL    every REGISTRY row is sourced, bracketed, inert or a declared scenario
    G-CODECONST   16 NAMED solver constants in julia/ equal their registry value
    G-ANACONST    PROPERTY-NAMED assignments across data/ and figs/ match the registry
    G-SPECIES     every (species, D) pair in run_mediated.jl is a registered row
    G-COND        every concentration is page-anchored or hand-verified
    G-COVER       every number PRINTED in the documents is mentioned by some gate

None of them asks the closure question: take every numeric LITERAL in the code that computes a
published result, and account for it. A literal that is not a named constant, not property-named
and not printed in either document falls through all six. The 2026-08-24 sweep did this once by
hand over 554 literals and found six defects; it was never made standing, so nothing has re-run it
since the model moved.

WHAT "ACCOUNTED FOR" MEANS
-------------------------
Each literal is placed in exactly one class:

    COSMETIC    a plotting quantity -- font size, colour, coordinate, linewidth, axis limit.
                Cannot reach a computed result. Detected by the keyword on its own line.
    STRUCTURAL  array indices, loop bounds, unit conversions by powers of ten, and the small
                integers of arithmetic identities (0, 1, 2, 100, 1000...).
    REGISTRY    the value equals a registry row's value, so G-EVERYVAL already governs it.
    GATED       the literal appears in a gate under data/ or figs/, so some check names it.
    UNACCOUNTED everything else. NOT necessarily wrong -- but nothing in the repo is watching it,
                which is the state each of the six 2026-08-24 defects was in.

This reports rather than adjudicates: the verdict is that the unaccounted set has not GROWN past
the reviewed baseline. Lower the baseline as literals are retired; never raise it silently.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# the chain that produces published results
SOURCES = [
    "julia/npp.jl", "julia/npp_ecprime.jl", "julia/correlations.jl", "julia/params.jl",
    "julia/cellvoltage.jl", "julia/run_mediated.jl", "julia/run_all50_np.jl",
    "figs/thermal_model.py", "figs/model_medians.py", "figs/archetype_bands.py",
    "data/build_merged_matrix.py", "data/casteel_amis.py",
]
COSMETIC = re.compile(
    r"fontsize|color|colour|lw\s*=|linewidth|alpha\s*=|zorder|ha\s*=|va\s*=|figsize|dpi"
    r"|rotation|pad\s*=|bbox|set_[xy]lim|set_[xy]ticks|annotate|\.text\(|markersize|ms\s*="
    r"|labelsize|width\s*=|height\s*=|hspace|wspace|\bcmap\b|edgecolor|facecolor|axvspan"
    r"|axhspan|transform|xytext|arrowprops|legend|tick_params|subplots_adjust|savefig", re.I)
STRUCT = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0, 100.0, 1000.0, 0.5, 1e-3, 1e-6, 1e-9, 1e4,
          1e3, 1e6, 60.0, 24.0, 273.15, 1e-2, 1e-1, 12.0, 50.0, 25.0}
# Reviewed 2026-08-31 and driven to its floor. The single survivor is the fold-detection
# tolerance tol = 1.0002 in npp_ecprime.jl's _push_to_fold, reached only from the k-continuation
# cascade -- and the published matrices contain ZERO rows on that path (G-ECBAND asserts the path
# column holds only direct-ramp and c-control), so it cannot reach a published number. It is a
# bisection stopping criterion, 0.02% in current, not a physical quantity.
# RAISING THIS IS A REGRESSION: each increment is a number entering a published calculation that
# no registry row, no data artifact and no named gate accounts for.
BASELINE = 1


def literals(path):
    """Numeric literals in EXECUTABLE code only.

    The first version stripped only line comments and quoted strings, so Julia block comments
    (#= ... =#) and Python docstrings leaked their prose numbers into the audit -- a comment
    reading "i flat at 108.32" was reported as an unwatched literal. Prose describing the model
    is not the model (the recurring trap in this repo), so both forms are removed first.
    """
    txt = io.open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
    txt = re.sub(r"#=.*?=#", lambda m: "\n" * m.group(0).count("\n"), txt, flags=re.S)
    txt = re.sub(r'"""(?:.|\n)*?"""', lambda m: "\n" * m.group(0).count("\n"), txt)
    out = []
    for n, line in enumerate(txt.split("\n"), 1):
        code = re.sub(r"(#|##|//).*$", "", line)          # strip comments (py and jl)
        code = re.sub(r'"[^"]*"', '""', code)             # and string contents
        if not code.strip():
            continue
        for m in re.finditer(r"(?<![\w.])(\d+\.\d+(?:[eE][-+]?\d+)?|\d+[eE][-+]?\d+)", code):
            out.append((n, float(m.group(1)), line.strip()[:110]))
    return out


def _covered_by_named_gate(path, ctx):
    """Literals a specific gate verifies STRUCTURALLY, which a textual search cannot see.

    G-SPECIES checks every (species, D) pair in run_mediated.jl against a category-4 registry row
    or a generated carrier D; G-CA reproduces six Dorn isotherms from the Casteel-Amis tuples to
    <0.1%, which is a far stronger check than naming the coefficient; and the eight nu_solv
    literals are compared to mu/rho below, in this file. None of those gates contains the literal
    in its own source, so all three looked unwatched.
    """
    if path == "julia/run_mediated.jl":
        if re.search(r'S\("', ctx) or "MedSpec(" in ctx:          # species D and nu_solv
            return True
    if path == "data/casteel_amis.py" and re.search(r'":\s*\(', ctx):
        return True                                               # Dorn fit tuple
    # chemistry audit pass 7: the Stefan-Boltzmann constant, exact in the SI since 2019, inside the registry's
    # 'h radiation (linearized)' formula; build_param_tables.py prints the h_r it gives (6.6 W m-2 K-1 at 65 C)
    if path == "figs/thermal_model.py" and "5.670374419e-8" in ctx:
        return True
    return False


def _near(val, pool):
    """RELATIVE match, tolerant of the decimal unit conversions this chain uses.

    An earlier version scaled the tolerance by the REGISTRY value, so for quantities of order
    1e-9 (every diffusivity) the window collapsed to ~1e-15 and registered values were reported
    as unwatched. Scale by the larger of the two magnitudes instead.
    """
    for f in (1.0, 1e-6, 1e6, 1e-3, 1e3, 1e-4, 1e4, 1e-9, 1e9, 1e-2, 1e2):
        for r in pool:
            t = r * f
            if abs(val - t) <= 1e-6 * max(abs(val), abs(t), 1e-30):
                return True
    return False


def main(verbose=False, neg=False):
    reg = set()
    with io.open(os.path.join(HERE, "parameters_provenance.csv"), encoding="utf-8") as fh:
        import csv
        for r in csv.DictReader(fh):
            for tok in re.findall(r"\d+\.?\d*(?:[eE][-+]?\d+)?", r["value"]):
                try:
                    reg.add(float(tok))
                except ValueError:
                    pass
    # THIS FILE IS EXCLUDED FROM ITS OWN EVIDENCE. Writing the baseline comment naming
    # tol = 1.0002 made that literal "mentioned by a gate" and the count silently fell 1 -> 0:
    # the audit had accounted for a number by talking about it. That is the repo's recurring
    # prose-quoting trap, occurring inside the gate written to find unwatched numbers.
    gate_src = ""
    for d in ("data", "figs"):
        for f in sorted(os.listdir(os.path.join(ROOT, d))):
            if f.endswith(".py") and f != os.path.basename(__file__):
                gate_src += io.open(os.path.join(ROOT, d, f), encoding="utf-8",
                                    errors="replace").read()

    import csv as _csv
    # every numeric column of the generated artifacts the gates verify
    data_vals = set()
    for fn in ("reactions_50.csv", "solvents.csv", "electrolytes.csv",
               "mediated_substrates.csv", "carrier_charge.csv"):
        fp = os.path.join(HERE, fn)
        if not os.path.exists(fp):
            continue
        with io.open(fp, encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                for v in row.values():
                    for tok in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", str(v)):
                        try:
                            data_vals.add(float(tok))
                        except ValueError:
                            pass

    tally = {"COSMETIC": 0, "STRUCTURAL": 0, "REGISTRY": 0, "DATA": 0, "GATED": 0,
             "NAMED-GATE": 0}
    unacc = []
    for path in SOURCES:
        if not os.path.exists(os.path.join(ROOT, path)):
            continue
        for ln, val, ctx in literals(path):
            if COSMETIC.search(ctx):
                tally["COSMETIC"] += 1
            elif val in STRUCT or (val != 0 and abs(val) in STRUCT):
                tally["STRUCTURAL"] += 1
            # The registry stores each quantity in ITS OWN units -- delta in um, concentration
            # in M -- while the solvers work in SI (m, mol/m3). Comparing raw floats reported
            # delta = 300e-6 m as unwatched when "300 um" is a registered row. Accept a match
            # under the decimal unit conversions this chain actually uses.
            elif _near(val, reg):
                tally["REGISTRY"] += 1
            elif _near(val, data_vals):
                # equals a value in a generated data artifact that gates already verify
                # (reactions_50.csv via G-COND/G-REGEN, mediated_substrates.csv via G-DSUB,
                # the species D via G-SPECIES). Those gates read the value from the file rather
                # than hardcoding it, so a purely textual search of gate sources cannot see them.
                tally["DATA"] += 1
            elif re.search(r"(?<![\d.])" + re.escape(repr(val).rstrip("0").rstrip("."))
                           + r"(?![\d])", gate_src):
                tally["GATED"] += 1
            elif _covered_by_named_gate(path, ctx):
                tally["NAMED-GATE"] += 1
            else:
                unacc.append({"file": path, "line": ln, "value": val, "context": ctx})

    # ---- HARD CHECK the audit turned up: the eight EC-prime kinematic viscosities ----------
    # run_mediated.jl carries nu_solv per mediated system as a hand-entered literal. nu is a
    # DERIVED quantity, mu/rho from solvents.csv, so it goes stale the moment either moves --
    # and mu(MeCN) did move, 0.343 -> 0.369, which changes nu from 4.420e-7 to 4.755e-7. It was
    # updated by hand that time. Nothing was checking it.
    nu_fail = []
    sol_nu, sol_of = {}, {}
    with io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            sol_nu[r["solvent"]] = float(r["mu_mPas"]) * 1e-3 / (float(r["rho"]) * 1000.0)
    with io.open(os.path.join(HERE, "reactions_50.csv"), encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            sol_of[r["reaction"]] = r["solvent"]
    med = io.open(os.path.join(ROOT, "julia", "run_mediated.jl"), encoding="utf-8").read()
    n_nu = 0
    for label, _k, nu_txt in re.findall(
            r'MedSpec\("([^"]+)",\s*([0-9.e+-]+),\s*([0-9.e+-]+)', med):
        solv = sol_of.get(label)
        if solv is None:
            nu_fail.append("%s: no row in reactions_50.csv, so its solvent is unknown" % label)
            continue
        want = sol_nu.get(solv) or sol_nu.get(solv.split()[0])
        if want is None:
            nu_fail.append("%s: solvent %r not in solvents.csv" % (label, solv))
            continue
        got = float(nu_txt)
        if neg:
            want *= 1.5
        # the literals are written to 3 s.f., so compare at that precision
        if abs(got - want) > 5e-3 * want:
            nu_fail.append("%s (%s): run_mediated.jl has nu = %.4g, mu/rho gives %.4g"
                           % (label, solv, got, want))
        n_nu += 1
    n_spec = len(re.findall(r'MedSpec\("', med))
    if n_nu + len([f for f in nu_fail if "no row" in f or "not in solvents" in f]) != n_spec:
        nu_fail.append("parsed %d MedSpec viscosities of %d specs" % (n_nu, n_spec))
    print("  EC-prime kinematic viscosities checked against mu/rho: %d of %d" % (n_nu, n_spec))
    for f in nu_fail:
        print("    FAIL  %s" % f)

    if neg:
        unacc.append({"file": "<control>", "line": 0, "value": 123456.789,
                      "context": "injected literal that no gate and no registry row accounts for"})

    total = sum(tally.values()) + len(unacc)
    print("  %d numeric literals across %d source files in the computed chain"
          % (total, len(SOURCES)))
    for k in ("COSMETIC", "STRUCTURAL", "REGISTRY", "DATA", "GATED", "NAMED-GATE"):
        print("    %-11s %4d" % (k, tally[k]))
    print("    %-11s %4d   <- nothing in the repo is watching these" % ("UNACCOUNTED", len(unacc)))
    print()
    show = unacc if verbose else unacc[:25]
    for u in show:
        print("    %-28s:%-5d %-14g %s" % (u["file"], u["line"], u["value"], u["context"][:72]))
    if not verbose and len(unacc) > 25:
        print("    (+%d more; --verbose)" % (len(unacc) - 25))

    json.dump({"tally": tally, "unaccounted": unacc, "baseline": BASELINE},
              io.open(os.path.join(ROOT, "results", "number_closure%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)
    if neg:
        ok = any(u["file"] == "<control>" for u in unacc) and len(nu_fail) == n_spec
        print("\nNEGATIVE CONTROL: an unaccountable literal was injected AND every solvent nu was "
              "scaled x1.5, so every viscosity check must fire.")
        print("G-NUMCLOSE control: %s (unaccounted caught: %s; nu failures: %d of %d)"
              % ("GOOD" if ok else "BAD -- test is inert",
                 any(u["file"] == "<control>" for u in unacc), len(nu_fail), n_spec))
        return 0 if ok else 1
    if nu_fail:
        print("\nG-NUMCLOSE: FAIL -- %d EC-prime viscosity(ies) no longer equal mu/rho from "
              "solvents.csv" % len(nu_fail))
        return 1
    if len(unacc) > BASELINE:
        print("\nG-NUMCLOSE: FAIL -- %d unaccounted literals, above the reviewed baseline of %d. "
              "Each new one is a number entering a published calculation that no registry row and "
              "no gate names." % (len(unacc), BASELINE))
        return 1
    print("\nG-NUMCLOSE: PASS -- %d unaccounted literals, at or below the reviewed baseline of %d"
          % (len(unacc), BASELINE))
    return 0


if __name__ == "__main__":
    sys.exit(main(verbose="--verbose" in sys.argv, neg="--negative-control" in sys.argv))
