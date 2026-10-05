#!/usr/bin/env python3
"""Lower and upper bounds on every number the MANUSCRIPT reports, for the SI.

    MPLBACKEND=Agg /opt/anaconda3/bin/python3.12 data/si_sensitivity_bounds.py

WHAT THIS IS
------------
Each reported number is recomputed at the edges of the ranges the registry already declares for
its dominant inputs. Nothing here invents a range: every band is quoted from a
parameters_provenance.csv sensitivity, and the row it came from is named in the output.

TWO FAMILIES, BOUNDED DIFFERENTLY BECAUSE THEY SCALE DIFFERENTLY
----------------------------------------------------------------
* TRANSPORT (medians, >=25 / >=50 counts). Dominant input is the diffusion-layer thickness of each
  architecture. For the 42 Nernst-Planck rows i_lim ~ 1/delta is EXACT (i*delta is invariant), so
  those columns are scaled analytically. For the 8 EC' rows it is NOT: amplification depends on
  delta/x_k and, measured across the delta range, varies by up to 1757% (ACT-mediated), 1232%
  (HMF), 233% (BQ), 95% (NHPI) and 46% (thiocyanation) -- only bromination (0.12%), Cl-epoxidation
  (0.15%) and Hofmann (4.0%) are near-invariant. So the mediated rows are RE-SOLVED at each band
  edge by julia/_bounds_lo.jl and _bounds_hi.jl, which override delta_eff and redirect output.

* THERMAL (Fig. 5 ceilings, zero-gap currents, shortfall ratios). Dominant input is the electrolyte
  conductivity, whose per-electrolyte bands the registry states. Widened by the two model choices
  the registry quantifies: h_int (-5/+6% on every ceiling, swept 50 -> infinity) and the
  temperature-resolved external film h_ext(T_b), which raises ceilings by THF -0.1%, MeCN +3.5%,
  DMF +15.7%, aq. NaOH +7.3% and is held constant in the code.

A bound is reported as one-sided where the registry says the range is one-sided. The THF
conductivity is the clearest case: its floor is MEASURED at 0.256 mS/cm (Das 2008, Table 1) but the
top "can no longer be defended at 6.6", so the upper bound on kappa -- and hence the LOWER bound on
the THF ceiling -- is not established, and the beaker verdict is conditional on the conductivity
maximum lying below about 8 mS/cm.
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); SEC4 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SEC4, "figs"))
import thermal_model as T

## kappa in S/m. (lo, hi, one_sided_note, registry row the band comes from)
KAPPA_BAND = {
 "THF":      (0.026, 0.80, "upper end NOT ESTABLISHED; 8 mS/cm is the conditional ceiling the "
                           "registry names, not a bound", "3.0 M LiBr/THF"),
 "MeCN":     (1.50, 2.30, None, "0.25 M Bu4NBF4/MeCN"),
 "DMF":      (0.40, 1.60, None, "0.2 M NaI/DMF (hard state-B ceiling 16.38 mS/cm)"),
 "aq. NaOH": (17.10, 17.80, None, "1 M NaOH aq (measured; +/-2%)"),
}
## multiplicative widening from the two quantified model choices, per solvent
H_INT   = (0.95, 1.06)                       # every ceiling, swept h_int 50 -> infinity
H_EXT_T = {"THF": 0.999, "MeCN": 1.035, "DMF": 1.157, "aq. NaOH": 1.073}   # resolving h_ext(T_b)

def thermal_bounds():
    out = {}
    Ub = T.U_passive(T.SIGMA_BEAKER, 100.)                      # unstirred beaker
    zg = [r for r in T.REACTORS if "zero-gap" in r[0]][0]
    Uz = T.U_passive(zg[2], zg[3])
    # The 250 um gap ceiling is quoted in the main text ("raises the modeled THF ceiling to
    # 182 mA cm-2 in a 250 um-gap cell") and, until 2026-09-07, was bracketed by nothing: the
    # table carried the beaker and zero-gap ceilings and the 250 um COOLING SHORTFALL, but not
    # the 250 um ceiling itself.
    # 2026-09-11: the thermal ladder is Fig. 5's seven archetypes + the zero-gap reference, so the
    # thin-gap cell is the 25 um microfluidic (Mo 2020), not the retired 250 um illustration.
    mg = [r for r in T.REACTORS if "microfluidic" in r[0]][0]
    Um = T.U_passive(mg[2], mg[3])
    for nm, el, kap, tb, cls in T.SOLVENTS:
        lo_k, hi_k, note, row = KAPPA_BAND[nm]
        for label, gap, U, idesign in (("beaker", 2.0e-2, Ub, T.REACTORS[0][4]),
                                       ("microfluidic", mg[1], Um, mg[4]),
                                       ("zero-gap", zg[1], Uz, zg[4])):
            ref = T.i_boil(kap,  gap, tb, U)
            a   = T.i_boil(lo_k, gap, tb, U)
            b   = T.i_boil(hi_k, gap, tb, U)
            lo, hi = min(a, b), max(a, b)
            lo *= H_INT[0]
            hi *= H_INT[1] * H_EXT_T[nm]
            out["%s %s ceiling" % (nm, label)] = dict(
                value=round(ref, 2), lower=round(lo, 2), upper=round(hi, 2),
                driver="kappa band %.3g-%.3g S/m, widened by h_int (-5/+6%%) and h_ext(T_b) (%+.1f%%)"
                       % (lo_k, hi_k, 100 * (H_EXT_T[nm] - 1)),
                registry_row=row, one_sided=note)

    ## Fig. 5c is a COOLING-DUTY ratio: U'_required(i_design) / U'_passively_available. It is NOT
    ## i_design / i_boil -- that mistake gives 15.2x for THF where the figure reports 95.1x.
    ## U'_req carries an iL/kappa term, so it is kappa-sensitive in the OPPOSITE direction to the
    ## ceiling: a higher kappa means less ohmic heat, so a SMALLER required duty.
    for nm, el, kap, tb, cls in T.SOLVENTS:
        lo_k, hi_k, note, row = KAPPA_BAND[nm]
        # 2026-09-16: the two ROTATING archetypes join the tabulated pair. Since v94 each architecture is
        # judged at its own median transport current, and Section 5 now states their cooling shortfalls
        # (THF 15-23x, MeCN/DMF 1.7-2.6x), so those numbers need a published band like any other.
        _WANT = ("zero-gap", "microfluidic", "RDE", "rotating cyl.")
        for rl, gap, sig, hi_int, idesign in T.REACTORS:
            if not any(w in rl for w in _WANT):
                continue
            avail = T.U_passive(sig, hi_int)
            ref = T.U_required(idesign, kap,  gap, tb) / avail
            a   = T.U_required(idesign, lo_k, gap, tb) / avail
            b   = T.U_required(idesign, hi_k, gap, tb) / avail
            lo_r, hi_r = min(a, b), max(a, b)
            ## h_int moves BOTH the requirement and the availability; the registry's -5/+6% band on
            ## ceilings is the net effect, applied here to the ratio in the widening direction.
            lo_r /= H_INT[1]; hi_r /= H_INT[0]
            _tag = ("zero-gap" if "zero-gap" in rl else "25 um" if "microfluidic" in rl
                    else "RDE" if "RDE" in rl else "rotating-cylinder")
            key = "%s %s cooling shortfall" % (nm, _tag)
            out[key] = dict(value=round(ref, 2), lower=round(lo_r, 2), upper=round(hi_r, 2),
                driver="U'_required(i_design=%g)/U'_passive over the kappa band %.3g-%.3g S/m"
                       % (idesign, lo_k, hi_k),
                registry_row=row, one_sided=note)
    return out


ARCH = {"Unstirred batch": "natural", "Stirred batch": "stirred",
        "Recirculating flow cell": "flow", "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro",
        "RDE 1600 rpm": "rde", "Rotating cylinder 3000 rpm": "rce"}

def _matrix(edge):
    """The 50x7 published matrix at a band edge.

    42 Nernst-Planck rows are scaled analytically: i ~ 1/delta is EXACT for them (i*delta is
    invariant, audit gate G4). The 8 EC' rows are read from the band-edge RE-SOLVE, because their
    amplification depends on delta/x_k and is not delta-invariant."""
    import csv
    JLD = os.path.join(SEC4, "julia")
    dl = {}
    for r in csv.DictReader(io.open(os.path.join(JLD, "delta_bounds.csv"), encoding="utf-8")):
        dl[(r["reaction"], r["reactor"])] = (float(r["delta_ref_um"]),
                                             float(r["delta_lo_um"]), float(r["delta_hi_um"]))
    out = {}
    for r in csv.DictReader(io.open(os.path.join(JLD, "all50_np_matrix.csv"), encoding="utf-8")):
        k = (r["reaction"], r["reactor"])
        if k not in dl: continue
        dref, dlo, dhi = dl[k]
        d = dlo if edge == "lo" else dhi
        out[k] = float(r["i_np_mAcm2"]) * dref / d
    med = os.path.join(JLD, "mediated_ec_matrix_band_%s.csv" % edge)
    if os.path.exists(med):
        for r in csv.DictReader(io.open(med, encoding="utf-8")):
            out[(r["reaction"], r["reactor"])] = float(r["i_ec_mAcm2"])
    # 2026-09-11: the seven catalyst rows carried at a SOURCED rate constant are EC' solves too, in the
    # kinetic regime, and do not scale as 1/delta; they are read from their own band-edge re-solve
    # (julia/run_catalyst_band.jl), exactly as the mediated rows are.
    cat = os.path.join(JLD, {"lo": "catalyst_ec_band_lo.csv", "hi": "catalyst_ec_band_hi.csv"}[edge])
    if os.path.exists(cat):
        for r in csv.DictReader(io.open(cat, encoding="utf-8")):
            if r.get("flag", "ok") != "ok":
                raise SystemExit("catalyst band-edge cell %s / %s (%s) reached no plateau" % (r["reaction"], r["reactor"], edge))
            out[(r["reaction"], r["reactor"])] = float(r["i_ec_mAcm2"])
    return out

def transport_bounds():
    import csv, statistics
    JLD = os.path.join(SEC4, "julia")
    ## BOTH band matrices are required. With only one present, _matrix() would silently fall back
    ## to the Nernst-Planck value for the 8 mediated rows at the missing edge -- an EC' row scored
    ## without its source term, which is a different model, not a bound.
    ## EXISTENCE IS NOT COMPLETENESS. run_mediated writes its matrix INCREMENTALLY, so the file
    ## appears with the first cell and grows. Checking os.path.exists let a 6-row matrix through and
    ## produced a "lower bound" in which 42 of the 48 mediated cells had silently fallen back to
    ## their Nernst-Planck value -- an EC' row scored without its source term. That is the
    ## partially-written-matrix trap this repository has already been bitten by once. Require the
    ## full 48 rows.
    NCELL = 8 * len(ARCH)          # 56: eight mediated rows x seven archetypes (was a typed 48)
    bad = []
    for e in ("lo", "hi"):
        f = os.path.join(JLD, "mediated_ec_matrix_band_%s.csv" % e)
        if not os.path.exists(f):
            bad.append("%s missing" % e); continue
        n = sum(1 for _ in io.open(f, encoding="utf-8")) - 1
        if n != NCELL:
            bad.append("%s has %d of %d cells" % (e, n, NCELL))
    for e, fn in (("lo", "catalyst_ec_band_lo.csv"), ("hi", "catalyst_ec_band_hi.csv")):   # 2026-09-11: the seven sourced rows, 49 cells each edge
        f = os.path.join(JLD, fn)
        if not os.path.exists(f):
            bad.append("catalyst %s missing" % e); continue
        n = sum(1 for _ in io.open(f, encoding="utf-8")) - 1
        if n != 7 * len(ARCH):
            bad.append("catalyst %s has %d of %d cells" % (e, n, 7 * len(ARCH)))
    if bad:
        return {"status": "band-edge mediated/catalyst solve(s) incomplete: " + "; ".join(bad)}
    ref = {}
    for r in csv.DictReader(io.open(os.path.join(JLD, "tier0_ec_matrix.csv"), encoding="utf-8")):
        for lbl, key in ARCH.items():
            if key in r and r[key] not in ("", "nan"):
                # KEY ON THE REACTION, not on the first column. tier0_ec_matrix.csv is wide
                # and its first column is `class`, so keying on it collapsed all 50 rows onto
                # the ~11 distinct classes: the medians survived that (they are medians of a
                # correct subset) but every COUNT was computed over ~11 rows and read 3 where
                # the matrix gives 12. The bracketing check could not see it, because it only
                # asks whether lower <= value <= upper.
                ref[(r["reaction"], lbl)] = float(r[key])
    res = {}
    edges = {e: _matrix(e) for e in ("lo", "hi")}
    for lbl, key in ARCH.items():
        cur = [v for (rx, rr), v in ref.items() if rr == lbl]
        if not cur: continue
        lo = [v for (rx, rr), v in edges["hi"].items() if rr == lbl]   # hi delta -> LOW current
        hi = [v for (rx, rr), v in edges["lo"].items() if rr == lbl]
        res["median, %s" % key] = dict(
            value=round(statistics.median(cur), 2), lower=round(statistics.median(lo), 2),
            upper=round(statistics.median(hi), 2),
            driver="architecture delta band", registry_row="delta (%s) / operating point" % key,
            one_sided=None)
        for thr in (25, 50):
            res["count >=%d, %s" % (thr, key)] = dict(
                value=sum(v >= thr for v in cur), lower=sum(v >= thr for v in lo),
                upper=sum(v >= thr for v in hi),
                driver="architecture delta band", registry_row="delta (%s) / operating point" % key,
                one_sided=None)
    return res

def main():
    res = {"thermal": thermal_bounds()}
    res["transport"] = transport_bounds()
    print("%-34s %10s %10s %10s   %s" % ("reported quantity", "lower", "value", "upper", "dominant driver"))
    for k, v in res["thermal"].items():
        print("%-34s %10.2f %10.2f %10.2f   %s" % (k, v["lower"], v["value"], v["upper"], v["driver"][:52]))
        if v["one_sided"]:
            print("%-34s %s" % ("", "ONE-SIDED: " + v["one_sided"][:90]))
    tr = res["transport"]
    if "status" not in tr:
        print()
        print("%-34s %10s %10s %10s   %s" % ("reported quantity", "lower", "value", "upper", "driver"))
        for k, v in tr.items():
            print("%-34s %10.2f %10.2f %10.2f   %s" % (k, v["lower"], v["value"], v["upper"], v["driver"]))
    else:
        print("\n  transport bounds: " + tr["status"])
    os.makedirs(os.path.join(SEC4, "results"), exist_ok=True)
    json.dump(res, io.open(os.path.join(SEC4, "results", "si_sensitivity_bounds.json"), "w"), indent=2)
    print("\nwrote -> results/si_sensitivity_bounds.json")

if __name__ == "__main__":
    main()
