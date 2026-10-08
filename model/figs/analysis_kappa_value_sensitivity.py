"""Value-uncertainty sensitivity for the two ASSUMPTION conductivities in Fig. K / Fig. 5.

    cd Section4_Model && python figs/analysis_kappa_value_sensitivity.py

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
`analysis_kappaT_sensitivity.py` already brackets the effect of evaluating kappa at 25 C in a
cell running at 60-153 C. That is the TEMPERATURE axis. This script covers the other axis, which
was never quantified: **the uncertainty in the 25 C value itself.**

Two of the four Fig. K electrolytes are registry `assumption` rows -- no measured conductivity for
that salt, that solvent and that concentration was located anywhere (see
docs/KAPPA_SOURCING_DOSSIER.md). The governing standard requires an assumption to carry "the range
tested and the conclusion that depends on it". Until now those rows carried only generic sensitivity
prose. This computes the range and names the conclusion.

THE TWO ROWS AND THEIR BANDS
----------------------------
  * 3.0 M LiBr / THF, carried at 3.0 mS/cm.
    Band 0.206 - 6.6 mS/cm. The floor is state B: an unconditional ohmic-differencing bound from
    Lee et al., OPRD 2022, 26, 2674-2684 (SI Fig. S3 p. S6, CFD block p. S22). The ceiling is the
    dossier's upper band edge. No measured kappa for LiBr/THF above 5e-2 M exists anywhere.

  * 0.2 M NaI / DMF, carried at 8.0 mS/cm -- the single most exposed number in the category
    (KAPPA_SOURCING_DOSSIER.md S4.1).
    Hard ceiling 16.4 mS/cm, state B: Kohlrausch additivity at complete dissociation with zero
    relaxation, kappa_max = Lambda0 * c, Lambda0(NaI, DMF, 298 K) = 81.9 S cm2 mol-1 from
    Gopal & Jha, Indian J. Chem. 1977, 15A, 80-83, Table 2 p. 81 (Na+ 29.81, I- 52.11), which the
    dossier retrieved and verified. The carried 8.0 is 49% of that ceiling. The floor is set here
    at a factor of three below the carried value; nothing measured supports either edge, so the
    sweep is reported as a range, not as a claim about the true value.

THE CONCLUSION UNDER TEST
-------------------------
Fig. 5a / the manuscript body state that THF in an unstirred 100 mL beaker reaches its 66 C
boiling point at ~29 mA/cm2, i.e. BELOW the 50 mA/cm2 design current -- "below the operating
barrier". That is the one Fig. K claim whose truth value can flip on kappa alone, because it is a
threshold crossing rather than a ranking. Everything else in Fig. 5 is a ratio or an ordering.

This script finds the kappa at which the crossing occurs and reports whether it lies inside the
defensible band.
"""
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from thermal_model import (SOLVENTS, REACTORS, U_passive, i_boil, TAMB)  # noqa: E402

BARRIER = 50.0          # mA/cm2, the operating barrier the manuscript compares against
OUT = os.path.join(ROOT, "results", "kappa_value_sensitivity.json")

# electrolyte key -> (low, carried, high) mS/cm, basis, and the DIRECTION of the manuscript
# claim: "below" means the paper says this solvent boils under the 50 mA/cm2 barrier, "above"
# means the paper says it clears it. Testing both against a single direction would have scored
# DMF as failing when the paper never claimed it boils below the barrier in the first place.
# Band EDGES only. The CARRIED value is never typed here -- it is read from
# thermal_model.SOLVENTS, which _check_registry ties to data/electrolytes.csv. It used to be
# typed, and when 0.2 M NaI/DMF was promoted 8.0 -> 8.77 this gate kept the retired 8.0 on BOTH
# sides of its own comparison, reproduced the registry prose to +0.01%, and could not fail.
#
# A ceiling of None means NO UPPER BOUND IS ESTABLISHED. THF used to carry 6.6 mS cm-1 here and
# this gate printed "HOLDS across the whole band" from it -- which is exactly the band-proof
# claim SI S6 withdrew, replacing it with a solvation-stoichiometry argument that fixes the
# DIRECTION past the conductivity maximum but not its LOCATION. A gate must not keep asserting
# what the document it protects has retracted.
BANDS = {
    "3.0 M LiBr/THF": (0.206, None,
                       "floor B: ohmic-differencing bound, Lee OPRD 2022 SI Fig. S3 p. S6; "
                       "ceiling: NOT ESTABLISHED -- the conductivity maximum of LiBr in THF has "
                       "never been located (SI S6, band-proof claim withdrawn)", "below"),
    "0.2 M NaI/DMF":  (8.0 / 3.0, 16.27,
                       "ceiling B: hard Kohlrausch bound c*Lambda0 = 0.2 x 81.35, with Lambda0 "
                       "MEASURED directly (Krumgalz & Barthel, Z. Phys. Chem. 1984, 142, 167-178, "
                       "Table 2, NaI block, 25 C). Supersedes the 16.4 built on the Gopal & Jha "
                       "Kohlrausch SUM 81.9; floor: 3x below carried, unsourced", "above"),
}


# A NEGATIVE CONTROL MUST NEVER WRITE THE ARTIFACT IT PERTURBS -- see the note in
# data/sensitivity_dma_viscosity.py. Controls write a _NEGCONTROL sibling instead.
def _out(path, neg):
    return path[:-5] + "_NEGCONTROL.json" if neg and path.endswith(".json") else path

def crossing_kappa(gap, Tb, U, target_mAcm2, lo=1e-4, hi=1e2):
    """kappa (S/m) at which i_boil equals target, or None if the target is UNREACHABLE.

    The bracket used to be unchecked, so an unreachable target returned the endpoint silently.
    That is not academic: at the zero-gap stack the activation term alone puts out more heat
    than passive rejection removes, so NO conductivity reaches its 1000 mA cm-2 design current
    (thermal_model.py says so in prose) -- and the unchecked version reported that reactor as
    "binding, flips at 0.01x carried, kappa 1000 mS/cm", which is the bracket, not a root.
    """
    f_lo, f_hi = i_boil(lo, gap, Tb, U), i_boil(hi, gap, Tb, U)
    if not (min(f_lo, f_hi) <= target_mAcm2 <= max(f_lo, f_hi)):
        return None                      # target outside the bracket: no root exists here
    for _ in range(200):
        mid = np.sqrt(lo * hi)
        if i_boil(mid, gap, Tb, U) > target_mAcm2:
            hi = mid
        else:
            lo = mid
    return np.sqrt(lo * hi)

def main(negative_control=False):
    if negative_control:
        # Perturb the MODEL and leave the registry prose alone -- the exact failure this gate
        # exists to catch, and the one it could not catch while its own kappa was typed. The
        # 8.0 -> 8.77 promotion did precisely this and G-KAPPA reported +0.01% agreement.
        import thermal_model as _tm
        _tm.SOLVENTS = [(n, k_, (kap * 1.25 if n == "DMF" else kap), Tb, st)
                        for n, k_, kap, Tb, st in _tm.SOLVENTS]
        globals()["SOLVENTS"] = _tm.SOLVENTS
    beaker = REACTORS[0]                      # unstirred 100 mL beaker
    _, gap, sigma, h_int, _ = beaker
    U = U_passive(sigma, h_int)

    report = {"reactor": "unstirred 100 mL beaker", "barrier_mAcm2": BARRIER, "rows": []}
    print("unstirred 100 mL beaker, U' = %.4f W cm-2 K-1, barrier %.0f mA cm-2\n" % (U, BARRIER))

    for name, key, kappa_Sm, Tb, state in SOLVENTS:
        if key not in BANDS:
            i0 = i_boil(kappa_Sm, gap, Tb, U)
            print("%-9s %-22s [%s] kappa %5.2f S/m -> i_boil %6.1f  (not swept)"
                  % (name, key, state, kappa_Sm, i0))
            continue
        lo_mS, hi_mS, basis, claim = BANDS[key]
        lo = lo_mS / 10.0
        hi = (hi_mS / 10.0) if hi_mS is not None else None
        mid = kappa_Sm                       # READ from the model, never typed here
        i_lo, i_mid = i_boil(lo, gap, Tb, U), i_boil(mid, gap, Tb, U)
        i_hi = i_boil(hi, gap, Tb, U) if hi is not None else None
        k_cross = crossing_kappa(gap, Tb, U, BARRIER)
        # i_boil rises with kappa, so the claim survives the band iff the WORST edge still holds.
        # With no established ceiling, a "boils BELOW the barrier" claim CANNOT be band-proof --
        # and saying so is the point, not a defect.
        if claim == "below":
            holds = None if hi is None else bool(i_hi < BARRIER)
        else:
            holds = bool(i_lo > BARRIER)
        # Margin is quoted against the CARRIED value: "how many-fold wrong would the number we
        # actually use have to be?" Quoting it against a band edge makes the answer an artifact
        # of where the edge was drawn.
        margin = (k_cross / mid) if claim == "below" else (mid / k_cross)
        print("%-9s %-22s [%s]  paper claims it boils %s the barrier"
              % (name, key, state, claim.upper()))
        print("    band %.3f - %s S/m (carried %.3f, read from thermal_model.SOLVENTS)"
              % (lo, "NOT ESTABLISHED" if hi is None else "%.3f" % hi, mid))
        print("    i_boil across the band: %.1f - %s mA cm-2 (carried %.1f)"
              % (i_lo, "?" if i_hi is None else "%.1f" % i_hi, i_mid))
        print("    barrier crossing at kappa = %.3f S/m (%.1f mS/cm)" % (k_cross, k_cross * 10))
        if holds is None:
            print("    -> NOT BAND-PROOF: no upper bound is established, and the claim fails for "
                  "any kappa above %.2f mS/cm" % (k_cross * 10))
        else:
            print("    -> %s" % ("HOLDS across the whole band" if holds
                                 else "holds except at the worst band edge"))
        print("       breaking it needs kappa %.1fx %s than carried (this reactor)\n"
              % (margin, "higher" if claim == "below" else "lower"))

        # WHICH reactor is binding? This gate used to evaluate REACTORS[0] only and print the
        # unstirred beaker's 2.9x for THF -- but the STIRRED beaker flips first, at 2.6x, because
        # stirring lifts U' and its ceiling climbs faster with kappa. Quoting a margin that is not
        # the binding one overstates the headroom.
        binding = None
        for lab_r, gap_r, sg_r, hint_r, ides_r in REACTORS:
            U_r = U_passive(sg_r, hint_r)
            k_r = crossing_kappa(gap_r, Tb, U_r, ides_r)
            if k_r is None:
                continue                 # this reactor's design current is unreachable at any kappa
            fold = (k_r / mid) if claim == "below" else (mid / k_r)
            if fold > 0 and (binding is None or fold < binding[1]):
                binding = (lab_r.replace("\n", " "), fold, k_r, ides_r)
        if binding is None:
            print("    binding reactor: NONE -- no reactor's design current is reachable at any "
                  "conductivity, so no kappa-axis margin exists for this solvent\n")
        else:
            print("    binding reactor: %s -- flips at %.2fx carried (kappa %.2f mS/cm, "
                  "i_design %.0f)\n" % (binding[0], binding[1], binding[2] * 10, binding[3]))

        report["rows"].append(dict(
            solvent=name, electrolyte=key, state=state, claim_direction=claim,
            band_Sm=[lo, hi], band_ceiling_established=hi is not None, carried_Sm=mid,
            binding_reactor=binding[0] if binding else None,
            binding_fold=float(binding[1]) if binding else None,
            binding_kappa_mScm=float(binding[2] * 10.0) if binding else None,
            i_boil_lo=i_lo, i_boil_carried=i_mid, i_boil_hi=i_hi,
            crossing_kappa_Sm=k_cross, crossing_kappa_mScm=k_cross * 10.0,
            claim_holds_across_band=holds,
            kappa_fold_error_to_break=float(margin),
            band_basis=basis))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(_out(OUT, negative_control), "w") as f:
        json.dump(report, f, indent=2)
    print("wrote %s" % os.path.relpath(_out(OUT, negative_control), ROOT))

    # ---------------------------------------------------------------------------------
    # G-KAPPA: assert the CRITICAL kappa values that the registry states in prose.
    #
    # data/build_param_tables.py carries three quantitative sensitivity claims for the two
    # assumption-class Fig. K conductivities, and SI S6 quotes them. They were typed, and
    # nothing recomputed them -- so a change in thermal_model.py could silently falsify the
    # registry's own sensitivity text while every other gate stayed green. These recompute
    # them from the shared model and fail on a >1% drift.
    # ---------------------------------------------------------------------------------
    import numpy as _np
    from thermal_model import T_ss as _T_ss, E_cell as _E_cell

    def _solve_dec(f, target, lo=1e-3, hi=1e3):
        for _ in range(200):
            m = _np.sqrt(lo * hi)
            lo, hi = (m, hi) if f(m) > target else (lo, m)
        return _np.sqrt(lo * hi)

    # carried DMF kappa, read from the model -- was a typed 0.80 that survived the
    # 8.0 -> 8.77 promotion and made this gate compare the retired value to itself.
    _kD = next(k for n, _, k, _, _ in SOLVENTS if n == "DMF")
    checks = []
    thf = next(r for r in report["rows"] if r["solvent"] == "THF")
    # RE-POINTED 2026-09-12. This check used to be "THF beaker i_boil crosses 50 mA/cm2" at
    # kappa = 8.78 mS/cm, which was the flip point against a DECLARED design current of
    # 50 mA cm-2. Every architecture is judged at its own median transport ceiling since v94, so
    # that claim left the registry and the gate was left pinned to a number no row states -- which
    # is what it reported, correctly, rather than passing on a stale literal. The THF row's
    # BINDING verdict is now the rotating disc, and the multiple it states is what is checked.
    _thf_k = next(k for n, _, k, _, _ in SOLVENTS if n == "THF")
    _rde = next(r for r in REACTORS if r[0].replace("\n", " ").startswith("RDE"))
    _U_rde = U_passive(_rde[2], _rde[3])
    # i_boil INCREASES with kappa, so _solve_dec (written for a decreasing f) walks the wrong
    # way and returns its own bracket; bisect in the increasing direction here.
    _lo, _hi = 1e-4, 1e3
    for _ in range(200):
        _m = _np.sqrt(_lo * _hi)
        _lo, _hi = (_lo, _m) if i_boil(_m, _rde[1], 66.0, _U_rde) > _rde[4] else (_m, _hi)
    _k_rde = _np.sqrt(_lo * _hi)
    # the expectation is the THERMAL ARTIFACT's own value (results/figK_thermal.json, the number the registry row
    # interpolates), not a literal typed here: a typed 16.5 outlived the matrix that gave it (2026-10-05) and read as
    # a disagreement between the two code paths when both agreed on 15.2
    _fk = json.load(open(os.path.join(ROOT, "results", "figK_thermal.json")))
    _want_rde = float(_fk["si_support"]["kappa_flips"]["THF"]["RDE 1600 rpm"]["multiple"])
    checks.append(("THF rotating-disc ceiling reaches its transport ceiling (x carried kappa)",
                   _k_rde / _thf_k, round(_want_rde, 1)))
    k_tss = _solve_dec(lambda k: _T_ss(100.0, k, gap, U), 153.0)
    checks.append(("DMF T_ss(100 mA/cm2) crosses 153 C", k_tss * 10, round(k_tss * 10, 2)))
    checks.append(("DMF T_ss at carried kappa (C)", _T_ss(100.0, _kD, gap, U),
                   round(_T_ss(100.0, _kD, gap, U))))
    checks.append(("DMF E_cell at 50 mA/cm2 (V)", _E_cell(50.0, _kD, gap), round(_E_cell(50.0, _kD, gap), 1)))
    checks.append(("DMF E_cell 20 V edge", _solve_dec(lambda k: _E_cell(50.0, k, gap), 20.0) * 10, 5.68))
    checks.append(("DMF E_cell 10 V edge", _solve_dec(lambda k: _E_cell(50.0, k, gap), 10.0) * 10, 13.16))

    # THE EXPECTATIONS MUST ALSO APPEAR IN THE REGISTRY PROSE. Without this the gate is a pin:
    # it compares the model to a literal typed HERE, and the registry text it claims to protect
    # could say anything. Requiring each number to appear in the row's own sensitivity string
    # ties all three together -- model, gate, published prose -- so no two can drift apart.
    import csv as _csv
    _reg = {r["parameter"]: r.get("sensitivity", "")
            for r in _csv.DictReader(open(os.path.join(ROOT, "data",
                                                       "parameters_provenance.csv")))}
    _prose = {"THF": _reg.get("3.0 M LiBr/THF", ""), "DMF": _reg.get("0.2 M NaI/DMF", "")}
    print("\nG-KAPPA: registry sensitivity claims recomputed from thermal_model.py")
    bad = []
    # The registry must STATE the quantity, but it need not state it to this gate's rounding.
    # An exact-string test made the two code paths' last digit load-bearing: the gate bisects to
    # 14.09 and the registry's own helper to 14.11, which is 0.14% and a convergence difference,
    # not a disagreement. Search the row for a number within 1% of the expectation instead --
    # still a real test that the row carries the claim, with no rounding coupling.
    _NUM = re.compile(r"\d+(?:\.\d+)?")
    for _label, _got, _want in checks:
        _who = "DMF" if _label.startswith("DMF") else "THF"
        _nums = [float(x) for x in _NUM.findall(_prose[_who].replace(",", ""))]
        if not any(abs(n - _want) <= 0.01 * max(abs(n), abs(_want)) for n in _nums):
            bad.append("%s: no number within 1%% of the expectation %.4g appears in the %s "
                       "registry row's sensitivity text -- the gate is pinned to a quantity the "
                       "registry does not state" % (_label, _want, _who))
    for label, got, want in checks:
        dev = 100.0 * (got - want) / want
        ok = abs(dev) <= 1.0
        print("  %-5s %-38s got %8.2f  registry %8.2f  (%+.2f%%)"
              % ("PASS" if ok else "FAIL", label, got, want, dev))
        if not ok:
            bad.append(label)
    report["gate"] = {"checks": [dict(label=l, got=g, registry=w) for l, g, w in checks],
                      "failed": bad}
    with open(_out(OUT, negative_control), "w") as f:
        json.dump(report, f, indent=2)
    if negative_control:
        fired = [b for b in bad if "DMF" in b]
        print("\nnegative control: pushed kappa(DMF) up 25% in the MODEL, registry prose untouched")
        for b in bad:
            print("    " + str(b))
        # run_gates.sh reads a verdict LINE; an exception alone is not one, and a control whose
        # only signal is a traceback reads as a crash rather than as a working control.
        print("G-KAPPA control: %s"
              % ("GOOD -- the gate fires on the DMF rows" if fired else
                 "BAD -- test is inert, the promotion moved out from under the registry text "
                 "without the gate noticing"))
        if not fired:
            raise AssertionError("negative control did not fire; this gate cannot detect a "
                                 "conductivity promotion moving out from under the registry text "
                                 "-- which is exactly what it missed on 2026-08-22")
        return report
    if bad:
        raise AssertionError("registry kappa sensitivity prose no longer matches the model: %s"
                             % ", ".join(str(b) for b in bad))
    print("  -> all six match; the registry's kappa sensitivity text is reproducible")
    return report


if __name__ == "__main__":
    import sys
    main(negative_control="--negative-control" in sys.argv)
