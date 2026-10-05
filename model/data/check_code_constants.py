#!/usr/bin/env python3
"""G-CODECONST -- every physical constant hardcoded in the solvers must match its registry row.

    cd Section4_Model && python data/check_code_constants.py
    cd Section4_Model && python data/check_code_constants.py --negative-control

WHY THIS EXISTS
---------------
The registry records provenance for the model's parameters. Nothing was checking that the SOLVERS
actually compute with the values the registry publishes. Two real divergences were live when this
gate was written (2026-08-24):

  * `julia/correlations.jl` used a Levich coefficient of 1.61 while the registry published 1.613.
    The registry had DERIVED 1.613 as 1/0.62, and 0.62 is itself a 2-significant-figure constant,
    so the inversion manufactured precision the input never had: 1/0.62 = 1.6129 against the exact
    1/0.62048 = 1.6117. Retrieval settled it -- Bard & Faulkner prints 1.61 -- so the registry was
    corrected to the code's value, not the other way round.

  * `julia/npp.jl` accepted Newton at `norm(Fv, Inf) < 1e-6` while the registry publishes
    "Newton tolerance ||F||_inf = 1e-9" and the function's own signature declared `tol = 1e-9`.
    That solver is what audit gates G1-G4 (the migration-physics validations) run on. Its twin
    `npp_ecprime.jl` had the identical defect fixed on 2026-08-23; npp.jl was missed.

HOW IT AVOIDS BEING TAUTOLOGICAL
--------------------------------
Both sides are READ FROM FILES -- the literal is extracted from the source line by regex, the
expected value is parsed out of `parameters_provenance.csv`. Neither is typed into this script.
That is deliberate: a gate that types the number on both sides of its own comparison stops testing
the moment the number moves (CLAUDE.md trap 14).
"""
import csv, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEC4 = os.path.dirname(HERE)
REG  = os.path.join(HERE, "parameters_provenance.csv")

## (label, source file, regex capturing ONE literal, registry parameter (exact), how to pull the
##  expected number out of the registry `value` field, relative tolerance)
CHECKS = [
 ("Levich coefficient",       "julia/correlations.jl", r"return\s+([\d.]+)\s*\*\s*D\^\(1/3\)",
  "Levich: delta = 1.61 D^(1/3) nu^(1/6) omega^(-1/2)", r"^([\d.]+)$", 0.0),
 ("Leveque coefficient",      "julia/correlations.jl", r"Sh\s*=\s*([\d.]+)\s*\*\s*\(Re",
  "Leveque: Sh = 1.85 (Re Sc dh/L)^(1/3)", r"^([\d.]+)$", 0.0),
 ("Eisenberg coefficient",    "julia/correlations.jl", r"Sh\s*=\s*([\d.]+)\s*\*\s*Re\^",
  "Eisenberg RCE: Sh = 0.0791 Re^0.70 Sc^0.356", r"^([\d.]+)$", 0.0),
 ("RDE speed (rpm)",          "julia/correlations.jl", r"delta_rde\(.*rpm::Float64\s*=\s*([\d.]+)",
  "RDE operating point", r"^([\d.]+)$", 0.0),
 ("RCE cylinder diameter",    "julia/correlations.jl", r"km_rce\(.*d::Float64\s*=\s*([\d.]+)",
  "RCE operating point", r"d\s*([\d.]+)\s*cm", 0.0, 1e-2),          # cm -> m
 ("RCE speed (rpm)",          "julia/correlations.jl", r"km_rce\(.*rpm::Float64\s*=\s*([\d.]+)",
  "RCE operating point", r"([\d.]+)\s*rpm", 0.0),
 ("delta unstirred batch",    "julia/correlations.jl", r"return\s+([\d.]+)e-6\s*$",
  "delta (unstirred batch)", r"^([\d.]+)$", 0.0),
 ## the three flow films adopted 2026-09-07: two measured (Watkins 2023 SI Table S1) and the
 ## microfluidic gap / residence time (Mo 2020 SI p. 13) the derived half-gap film rests on
 ("delta recirculating flow", "julia/correlations.jl", r"DELTA_FLOW\s*=\s*([\d.]+)e-6",
  "delta (recirculating flow cell)", r"^([\d.]+)$", 0.0),
 ("delta ANEC flow cell",     "julia/correlations.jl", r"DELTA_ANEC\s*=\s*([\d.]+)e-6",
  "delta (ANEC flow cell)", r"^([\d.]+)$", 0.0),
 ("microfluidic gap (um)",    "julia/correlations.jl", r"H_MICRO\s*=\s*([\d.]+)e-6",
  "Microfluidic cell operating point (Mo 2020)", r"gap\s*([\d.]+)\s*um", 0.0),
 ("microfluidic tau (min)",   "julia/correlations.jl", r"TAU_MICRO\s*=\s*([\d.]+)\s*\*\s*60",
  "Microfluidic cell operating point (Mo 2020)", r"tau\s*([\d.]+)\s*min", 0.0),
 ("Faraday constant",         "julia/params.jl",       r"F_const\s*=\s*([\d.]+)",
  "Faraday constant F", r"^([\d.]+)$", 0.0),
 ("Gas constant",             "julia/params.jl",       r"R_gas\s*=\s*([\d.]+)",
  "Gas constant R", r"^([\d.]+)$", 1e-6),
 ("Temperature",              "julia/params.jl",       r"T_K\s*=\s*([\d.]+)",
  "Temperature T", r"^([\d.]+)$", 0.0),
 ("Reporting threshold",      "julia/params.jl",       r"I_THRESH\s*=\s*([\d.]+)",
  "Thresholds 25 / 50 mA cm-2", r"^([\d.]+)", 0.0),
 ("E0 voltage floor",         "julia/cellvoltage.jl",  r"E0\s*=\s*([\d.]+)",
  "E0 (thermodynamic + kinetic floor)", r"^([\d.]+)$", 0.0),
 ("i0 exchange current",      "julia/cellvoltage.jl",  r"i0\s*=\s*([\d.]+)\)",
  "i0 (exchange current density)", r"^([\d.]+)$", 0.0),
 ("Newton tolerance (EC')",   "julia/npp_ecprime.jl",  r"newton_ec!\(u::Vector\{Float64\}, p::ECProblem, i_app::Float64;\s*\n?\s*tol\s*=\s*([\d.e-]+)",
  "Newton tolerance ||F||_inf", r"^([\d.e-]+)$", 0.0),
 ("Newton tolerance (film)",  "julia/npp.jl",          r"newton_solve!\(u::Vector\{Float64\}, p::FilmProblem, i_app::Float64;\s*\n?\s*tol\s*=\s*([\d.e-]+)",
  "Newton tolerance ||F||_inf", r"^([\d.e-]+)$", 0.0),
 ("Trust-region threshold",   "julia/npp_ecprime.jl",  r"NEGLIGIBLE_C\s*=\s*Ref\(([\d.e-]+)\)",
  "Trust-region negligibility NEGLIGIBLE_C", r"^([\d.e-]+)$", 0.0),
]

def registry():
    return list(csv.DictReader(io.open(REG, encoding="utf-8")))

def main(neg=False):
    rows = {r["parameter"]: r for r in registry()}
    fails, checked = [], 0
    print("%-26s %14s %14s   %s" % ("constant", "in code", "in registry", "source file"))
    for chk in CHECKS:
        label, f, pat, param, vpat, tol = chk[:6]
        scale = chk[6] if len(chk) > 6 else 1.0
        path = os.path.join(SEC4, f)
        if not os.path.exists(path):
            fails.append("%s: %s missing" % (label, f)); continue
        src = io.open(path, encoding="utf-8").read()
        m = re.search(pat, src, re.M)
        if not m:
            fails.append("%s: pattern found nothing in %s -- the code was reworded and this check "
                         "silently stopped testing" % (label, f)); continue
        code_v = float(m.group(1))
        if neg and label == "Levich coefficient":
            code_v *= 1.05                      # perturb the CODE side, not the text
        r = rows.get(param)
        if r is None:
            fails.append("%s: no registry row named %r" % (label, param)); continue
        vm = re.search(vpat, str(r["value"]).strip())
        if not vm:
            fails.append("%s: registry value %r does not parse with %r"
                         % (label, r["value"], vpat)); continue
        reg_v = float(vm.group(1)) * scale
        checked += 1
        ok = (code_v == reg_v) if tol == 0 else (abs(code_v - reg_v) <= tol * abs(reg_v))
        print("%-26s %14.9g %14.9g   %s%s" % (label, code_v, reg_v, f, "" if ok else "   <-- MISMATCH"))
        if not ok:
            fails.append("%s: code has %g, registry publishes %g (%s)"
                         % (label, code_v, reg_v, r["provenance_class"]))
    ## ---------------------------------------------------------------------------------------
    ## THE DECLARED DEFAULT IS NOT WHAT IS ENFORCED. The two "Newton tolerance" checks above read
    ## `tol = 1e-9` out of the function SIGNATURE -- and the signature said 1e-9 the whole time
    ## npp.jl was accepting at a hardcoded 1e-6. So those checks would have passed the exact defect
    ## this gate exists to catch. What has to be asserted is that the convergence test compares
    ## against the DECLARED VARIABLE, never against a literal of its own.
    print("enforcement check -- the convergence test must compare against `tol`, not a literal:")
    for f, fn in (("julia/npp.jl", "newton_solve!"), ("julia/npp_ecprime.jl", "newton_ec!")):
        src = io.open(os.path.join(SEC4, f), encoding="utf-8").read()
        i = src.find("function " + fn)
        if i < 0:
            fails.append("%s: %s not found" % (f, fn)); continue
        ## STRIP COMMENTS FIRST. On this check's first run it reported BOTH solvers as violations
        ## because the comments documenting the fix quote the retired code verbatim -- "This read
        ## `norm(Fv, Inf) < 1e-6`". Prose quoting what it withdraws, read as the thing itself: the
        ## same trap that has now bitten five gates in this repository (CLAUDE.md traps 13/16 and
        ## the registry-liveness and ledger cases). A gate that reads source must read CODE.
        body = "\n".join(re.sub(r"#.*$", "", ln) for ln in src[i:i + 6000].split("\n"))
        lits = re.findall(r"norm\((?:Fv|R|F), Inf\)\s*<\s*([0-9][\w.e-]*)", body)
        uses_tol = re.search(r"norm\((?:Fv|R|F), Inf\)\s*<\s*tol", body) is not None
        if neg and f == "julia/npp.jl":
            lits, uses_tol = ["1e-6"], False        # perturb the CODE side
        status = "OK" if (uses_tol and not lits) else "VIOLATION"
        print("   %-22s %-16s %s%s" % (fn, f.split("/")[-1], status,
              "" if status == "OK" else "  accepts at literal %s while declaring tol" % ", ".join(lits)))
        if status != "OK":
            fails.append("%s/%s: convergence accepted at hardcoded %s instead of the declared `tol`"
                         % (f, fn, ", ".join(lits) or "?"))
    print()
    if fails:
        if neg:
            ## A NEGATIVE CONTROL THAT FIRES IS WORKING. It must not print the failure verdict of
            ## the gate proper -- run_gates.sh reads the verdict line, and a control reporting FAIL
            ## is indistinguishable from a broken gate.
            hit_val = any("Levich" in x for x in fails)
            hit_enf = any("npp.jl" in x for x in fails)
            ok = hit_val and hit_enf
            print("G-CODECONST control: %s (value perturbation fired: %s; enforcement perturbation "
                  "fired: %s)" % ("GOOD" if ok else "BAD", hit_val, hit_enf))
            for x in fails: print("   ", x)
            raise SystemExit(0 if ok else 1)
        print("G-CODECONST: FAIL")
        for x in fails: print("   ", x)
        raise SystemExit(1)
    print("G-CODECONST: PASS -- %d solver constants match the registry value they are published "
          "under" % checked)

if __name__ == "__main__":
    main("--negative-control" in sys.argv)
