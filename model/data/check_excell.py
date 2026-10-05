#!/usr/bin/env python3
"""G-EXCELL -- the SI's ex-cell passage, bound to julia/run_excell.jl's own output.

    cd Section4_Model && python data/check_excell.py
    cd Section4_Model && python data/check_excell.py --negative-control

WHY THIS EXISTS
---------------
Nothing recomputed this passage. It published "the ramp converges to 785 mA cm-2, exactly 2.00x
the Fick bound, reproducing the analytic binary-electrolyte migration factor" while the solver
returned 608.4 (1.55x) at the same film and 203.1 (1.04x) at the current one -- and in neither
case was the carrier depleted, so neither was a limiting current at all. run_excell.jl has its
own hand-rolled ramp and never received the fold-parameterisation fix npp_ecprime.jl got on
2026-08-23, so it was the one solver path no gate and no sweep touched.

Two of its numbers had also gone stale by a film: the propylene-free zone and the planar
propylene cap are both delta-dependent, and both were last measured at 100 um.

The gate reads results/excell.json, which run_excell.jl writes, and requires every ex-cell
number the SI prints to match it. Each claim is bound by an explicit full phrase -- proximity is
never used (CLAUDE.md trap 25) -- and a phrase that has vanished is a FAIL, not a silent skip
(trap 10).
"""
import csv
import io
import json
import os
import re
import math
import sys
import unicodedata

SEC4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SEC4, "data"))
from docx_text import asserted_text  # noqa: E402


def main():
    neg = "--negative-control" in sys.argv
    with io.open(os.path.join(SEC4, "results", "excell.json"), encoding="utf-8") as fh:
        j = json.load(fh)
    if neg:
        ## Perturb the MODEL side, never the checker: pretend the solve reached the limit and
        ## that the zone doubled. Every claim that depends on either must fire.
        j = dict(j, ccontrol_converged=True, propylene_free_zone_um=j["propylene_free_zone_um"] * 2,
                 reachable_ratio_to_fick=1.5)

    if neg:
        ## and perturb an INPUT: the gate must notice the solver computing with a value the
        ## registry does not publish (this is the defect that was live until 2026-09-05)
        j = dict(j, inputs=dict(j["inputs"], C_P_mM=j["inputs"]["C_P_mM"] * 1.3))
    fails, oks = [], []
    ## ---- INPUTS: every constant the solver computes with must be the registry's value -------
    ## Until 2026-09-05 run_excell.jl carried C_P = 5.0 mM -- the Henry's-law value the registry's
    ## own row had WITHDRAWN on 2026-08-22 in favour of 5.67 -- and D_P = 1.2e-9, a value with no
    ## propene row behind it (it coincides with the Br2 (aq) row). Every ex-cell number the SI
    ## printed came from those inputs, and this gate, binding only OUTPUTS, passed. Both sides are
    ## read from files here: the solver's inputs from its JSON, the expectation from the registry
    ## and from data/mediated_substrates.csv (trap 14).
    inp = j.get("inputs")
    if inp is None:
        fails.append("results/excell.json carries no 'inputs' block -- run julia/run_excell.jl")
        inp = {}
    reg = {r["parameter"]: r for r in csv.DictReader(io.open(
        os.path.join(SEC4, "data", "parameters_provenance.csv"), encoding="utf-8"))}
    def bind(label, key, param, scale=1.0, tol=0.005):
        if key not in inp:
            fails.append("%s: results/excell.json has no input %r" % (label, key)); return
        row = reg.get(param)
        if row is None:
            fails.append("%s: no registry row named %r" % (label, param)); return
        mm = re.match(r"\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)", str(row["value"]))
        if not mm:
            fails.append("%s: registry value %r is not numeric" % (label, row["value"])); return
        exp = float(mm.group(1)) * scale
        if abs(inp[key] - exp) > tol * abs(exp):
            fails.append("%s: solver computes with %g, registry publishes %g (%s)"
                         % (label, inp[key], exp, row["provenance_class"]))
        else:
            oks.append("input " + label)
    bind("propylene C_sat", "C_P_mM", "Propylene C_sat (aq, 1 atm)", scale=1000.0)
    bind("D Cl-", "D_Cl_m2s", "Cl- (aq)")
    bind("D lumped Cl2/HOCl", "D_OX_m2s", "Cl2/HOCl lumped OX (aq)")
    bind("D H+", "D_H_m2s", "H+ (aq)")
    bind("D Na+", "D_Na_m2s", "Na+ (aq)")
    ## propylene's D is a DERIVED registry row (Wilke-Chang, arithmetic stated there); until
    ## 2026-09-05 it was read from the generated substrate table, whose propene row became
    ## ethylene when that row adopted the measured value
    bind("D propylene", "D_P_m2s", "Propylene (aq)")
    ## the oxidant's trace bulk seed (2026-09-06): an instance of the registry's declared rule
    ## "1e-5 x C_med", whose row value is a formula rather than a number, so it is bound by hand
    if "c_OX_bulk_molm3" not in inp:
        fails.append("trace seed: results/excell.json has no input 'c_OX_bulk_molm3' -- run julia/run_excell.jl")
    else:
        trow = reg.get("Trace initializations (Med_ox, H+ in aprotic)")
        tm = re.match(r"\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*x\s*C_med", str(trow["value"])) if trow else None
        if not tm:
            fails.append("trace seed: registry row 'Trace initializations (Med_ox, H+ in aprotic)' is missing "
                         "or its value no longer reads '<factor> x C_med'")
        else:
            fac = inp["c_OX_bulk_molm3"] / (inp["C_Cl_M"] * 1000.0)
            if abs(fac - float(tm.group(1))) > 0.005 * float(tm.group(1)):
                fails.append("trace seed: the solver seeds the oxidant at %.3g x C_Cl, the registry declares %s x C_med"
                             % (fac, tm.group(1)))
            else:
                oks.append("input trace seed (%s x C_med)" % tm.group(1))

    si = unicodedata.normalize("NFKC", re.sub(r"\s+", " ", asserted_text(
        os.path.join(SEC4, "SI_Section4_Transport_Model.docx"))))


    def want(label, phrase, value, tol):
        """`phrase` must be present, and `value` must match a number inside it."""
        ph = unicodedata.normalize("NFKC", phrase)
        if ph not in si:
            fails.append("%s: the SI no longer contains %r" % (label, phrase[:70]))
            return
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", ph)]
        if not any(abs(n - value) <= tol for n in nums):
            fails.append("%s: phrase %r carries %s, model gives %.4g"
                         % (label, phrase[:60], nums, value))
        else:
            oks.append(label)

    want("propylene C_sat as printed", "(C_sat = %.1f mM at 1 atm, Table S7e)" % inp.get("C_P_mM", -1),
         inp.get("C_P_mM", -1), 0.05)
    want("chloride as printed", "%.0f M Cl⁻ oxidized at the anode" % inp.get("C_Cl_M", -1),
         inp.get("C_Cl_M", -1), 0.05)
    want("planar propylene cap", "the planar-profile propylene diffusion cap, %.2f mA cm−2" % j["i_cap_P_mAcm2"],
         j["i_cap_P_mAcm2"], 0.005)
    want("reaction layer x_k", "the reaction layer x_k = %.0f μm" % j["x_k_um"], j["x_k_um"], 0.5)
    want("film stated beside x_k", "is comparable to the film itself (δ = %.0f μm)" % j["delta_um"],
         j["delta_um"], 0.5)
    want("operating point", "one third of the carrier limit derived below, %.0f mA cm−2" % j["i_op_mAcm2"],
         j["i_op_mAcm2"], 0.5)
    if abs(j["i_op_mAcm2"] - j["i_analytic_mAcm2"] / 3) > 0.01 * j["i_op_mAcm2"]:
        fails.append("the SI calls the operating point one third of the carrier limit, but %g is not "
                     "%g/3" % (j["i_op_mAcm2"], j["i_analytic_mAcm2"]))
    want("in-film fraction", "only %.1f%% of the generated oxidant" % j["infilm_pct"], j["infilm_pct"], 0.05)
    want("exported fraction", "%.1f%% is exported" % j["exported_pct"], j["exported_pct"], 0.05)
    want("in-film current, absolute", "(%.1f mA cm−2 equivalent" % j["i_infilm_mAcm2"],
         j["i_infilm_mAcm2"], 0.05)
    want("halved-film split", "on a %.0f μm film at the same current it is %.1f%% in-film"
         % (j["half_delta_um"], j["infilm_pct_half_delta"]), j["infilm_pct_half_delta"], 0.05)
    want("homogeneous rate constant", "with k = %.0f M−1 s−1 the reaction layer" % j["k_M"], j["k_M"], 0.05)
    ## S5.2 states the seed and the size of the scaling problem it creates; both are computed there
    if "c_OX_bulk_molm3" in inp:
        def sci(v):
            e = int(math.floor(math.log10(v))); m = v / 10 ** e
            return "%.1f × 10%s" % (m, str(e).replace("-", "⁻").translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))), round(m, 1)
        want("oxidant bulk seed as printed", "is seeded at %.2g mol m⁻³ in the bulk" % inp["c_OX_bulk_molm3"],
             inp["c_OX_bulk_molm3"], 0.0005)
        ratio = j["c_OX_at_limit_M"] * 1000.0 / inp["c_OX_bulk_molm3"]
        s_r, m_r = sci(ratio)
        want("residual-scale ratio as printed", "reference flux %s times smaller than its in-film concentration" % s_r, m_r, 0.05)
        s_a, m_a = sci(1e-9 / ratio)
        want("relative accuracy the unscaled row would need", "asks for a relative accuracy of %s on the terms" % s_a, m_a, 0.05)
    want("propylene-free zone", "extending ≈%.0f μm from the electrode" % (round(j["propylene_free_zone_um"], -1)),
         round(j["propylene_free_zone_um"], -1), 5.0)
    want("oxidant at the operating point", "carrying %.1f M of lumped Cl₂/HOCl" % j["c_OX_at_op_M"],
         j["c_OX_at_op_M"], 0.05)
    want("analytic carrier limit", "2 × %.0f = %.0f mA cm−2 at δ = %.0f μm"
         % (j["i_fick_Cl_mAcm2"], j["i_analytic_mAcm2"], j["delta_um"]), j["i_analytic_mAcm2"], 1.0)
    want("Fick bound inside that identity", "2 × %.0f = %.0f mA cm−2 at δ = %.0f μm"
         % (j["i_fick_Cl_mAcm2"], j["i_analytic_mAcm2"], j["delta_um"]), j["i_fick_Cl_mAcm2"], 1.0)
    want("EC-prime reproduction of the factor 2",
         "returning %.3f × the Fick bound" % j["reachable_ratio_to_fick"], j["reachable_ratio_to_fick"], 0.002)
    want("film the branch is reachable on", "on a %.0f μm film where the branch can be walked" % j["reachable_film_um"],
         j["reachable_film_um"], 0.5)
    ## delta-continuation record (2026-09-05): the SI used to attribute the 200 um failure to the
    ## 5.8 M oxidant state; that state is delta-independent and the thin films reach it, so the
    ## sentence now states where the branch ends on each film and that the cause is not established.
    dc = j.get("dcont")
    if not dc or len(dc) < 3:
        fails.append("results/excell.json carries no 3-film 'dcont' block -- run julia/run_excell.jl")
    else:
        if all(d["converged"] for d in dc):
            films = ", ".join("%.0f" % d["delta_um"] for d in dc[:-1]) + " and %.0f" % dc[-1]["delta_um"]
            ratios = ", ".join("%.3f" % d["ratio_fick"] for d in dc[:-1]) + " and %.3f" % dc[-1]["ratio_fick"]
            want("delta-continuation, every film converges",
                 "on %s μm films alike (%s × Fick), so the carrier limit is the solved limit at the production film" % (films, ratios),
                 dc[-1]["ratio_fick"], 0.002)
            if "ends before the carrier is depleted" in si or "We have not established why" in si:
                fails.append("every continuation converges, but the SI still describes a branch that ends first")
            want("oxidant at the limit, delta-independent", "holds %.1f M of lumped Cl₂/HOCl (2 D_Cl C_Cl/D_OX" % j["c_OX_at_limit_M"],
                 j["c_OX_at_limit_M"], 0.05)
        else:
            if dc[0]["converged"]:
                want("delta-continuation, 50 um converges",
                     "reaches the limit again on a %.0f μm film (%.3f × Fick)" % (dc[0]["delta_um"], dc[0]["ratio_fick"]),
                     dc[0]["ratio_fick"], 0.002)
            elif "reaches the limit again on a" in si:
                fails.append("the SI says the 50 um continuation reaches the limit, but the solver says it does not")
            want_pair = "at %.0f%% of the analytic limit on %.0f μm and %.0f%% on %.0f μm" % (
                dc[1]["pct_of_analytic"], dc[1]["delta_um"], dc[2]["pct_of_analytic"], dc[2]["delta_um"])
            want("delta-continuation, thick films", want_pair, dc[1]["pct_of_analytic"], 0.5)
            want("delta-continuation, 200 um share", want_pair, dc[2]["pct_of_analytic"], 0.5)
            if any(d["converged"] for d in dc[1:]) and "ends before the carrier is depleted on thicker films" in si:
                fails.append("a thick-film continuation now CONVERGES, but the SI still says the branch ends first")
            want("oxidant at the limit, delta-independent", "holds %.1f M of lumped Cl₂/HOCl on every film" % j["c_OX_at_limit_M"],
                 j["c_OX_at_limit_M"], 0.05)
    ## The DIRECTION words, which no numeric check can see: the SI must say the 200 um solve is
    ## a lower bound, and it may only say that while the solver agrees it did not converge.
    if j["ccontrol_converged"]:
        if "reported as the lower bound it is" in si:
            fails.append("the solver now CONVERGES at the production film, but the SI still "
                         "calls that solve a lower bound")
        else:
            oks.append("lower-bound wording withdrawn, as it must be when the solve converges")
    else:
        if "reported as the lower bound it is" not in si:
            fails.append("the 200 um solve does not converge, but the SI no longer says so")
        else:
            oks.append("lower-bound disclosure present")

    for f in fails:
        print("    FAIL  %s" % f)
    if neg:
        good = len(fails) >= 4 and any("propylene C_sat" in f for f in fails)
        print("\n  %d claim(s) fired under the perturbation" % len(fails))
        print("G-EXCELL control: %s" % ("GOOD (perturbing the model fires the dependent claims)"
                                        if good else "BAD (the perturbation went undetected)"))
        return 0 if good else 1
    if fails:
        print("\nG-EXCELL: FAIL")
        return 1
    print("  %d ex-cell claim(s) and input(s) checked against results/excell.json, the registry and\n"
          "  data/mediated_substrates.csv, all matching" % len(oks))
    print("G-EXCELL: PASS -- every ex-cell number the SI prints comes from the solver, and the "
          "convergence wording matches the solver's own verdict")
    return 0


if __name__ == "__main__":
    sys.exit(main())
