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
  the registry quantifies: h_int, swept 50 W m-2 K-1 to the well-stirred limit in each cell, and the
  temperature-resolved external film h_ext(T_b), evaluated in each cell for the upper edge of every
  ceiling (results/si_sensitivity_bounds.json carries the per-cell percentages).

A bound is reported as one-sided where the registry says the range is one-sided. The THF
conductivity is the clearest case: its band is 0.2-6.6 mS/cm, with a state-B floor (Lee 2022 cell
resistance) and an upper EDGE rather than a bound, so the registry row also tests the measured-data
continuations beyond 6.6; the note travels with every THF entry.
"""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); SEC4 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SEC4, "figs"))
import thermal_model as T

## kappa in S/m. (lo, hi, one_sided_note, registry row the band comes from). The bands are READ from the registry rows'
## own sensitivity text ("Band x-y mS cm-1"), which is what SI Table S4 prints, so the bounds of Table S9 cannot be taken
## over a different band from the one the reader is shown (chemistry audit, pass 5: THF had been bounded over 0.26-8 and
## NaOH over 171-178 while Table S4 printed 0.2-6.6 and 174-182).
_BAND_ROWS = {"THF": "3.0 M LiBr/THF", "MeCN": "0.25 M Bu4NBF4/MeCN", "DMF": "0.2 M NaI/DMF", "aq. NaOH": "1 M NaOH aq"}
_BAND_NOTE = {"THF": "upper edge 6.6 mS/cm is a declared edge, not a bound; the registry row tests the measured-data "
                     "continuations beyond it"}


def _registry_bands():
    import csv as _csv, re as _re
    reg = {r["parameter"]: r for r in _csv.DictReader(io.open(os.path.join(HERE, "parameters_provenance.csv"), encoding="utf-8"))}
    out = {}
    for sl, row in _BAND_ROWS.items():
        m = _re.search(r"\bBand ([0-9.]+)-([0-9.]+) mS cm-1", reg[row]["sensitivity"])
        if not m:
            raise SystemExit("registry row %r states no 'Band x-y mS cm-1'; Table S9 cannot be bounded" % row)
        out[sl] = (float(m.group(1)) / 10.0, float(m.group(2)) / 10.0, _BAND_NOTE.get(sl), row)
    return out


KAPPA_BAND = _registry_bands()
## multiplicative widening from the two quantified model choices, per solvent
# chemistry audit pass 7: h_int is swept 50 W m-2 K-1 -> the well-stirred limit IN EACH CELL. A flat -5/+6 % factor held
# only for the beaker (declared 100); the microfluidic chip and the stack (declared 5000) move -14 to -18 % at the low end.
H_INT_SWEEP = (50.0, 1e12)
def _hint_ends(kap, gap, tb, sig, hdecl):
    ref = T.i_boil(kap, gap, tb, T.U_passive(sig, hdecl))
    return [T.i_boil(kap, gap, tb, T.U_passive(sig, h)) / ref - 1.0 for h in H_INT_SWEEP]
# resolving h_ext at the boiling point, unstirred beaker (computed from thermal_model.h_ext_at; it was typed against the
# retired 8 cm vessel)
H_EXT_T = {nm: T.i_boil(kap, T.GAP_BEAKER, tb, T.U_passive(T.SIGMA_BEAKER, 100., h_ext=T.h_ext_at(tb)))
               / T.i_boil(kap, T.GAP_BEAKER, tb, T.U_passive(T.SIGMA_BEAKER, 100.)) for nm, el, kap, tb, cls in T.SOLVENTS}

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
            sig, hdecl = {"beaker": (T.SIGMA_BEAKER, 100.), "microfluidic": (mg[2], mg[3]), "zero-gap": (zg[2], zg[3])}[label]
            vals = [T.i_boil(k, gap, tb, T.U_passive(sig, h)) for k in (lo_k, hi_k) for h in H_INT_SWEEP + (hdecl,)]
            # audit pass 40: the external film at the boiling point is evaluated IN THIS CELL for the upper edge; applying
            # the unstirred beaker's factor to every cell understated the microfluidic and zero-gap upper edges by up to 11 pct
            hot = [T.i_boil(k, gap, tb, T.U_passive(sig, h, h_ext=T.h_ext_at(tb))) for k in (lo_k, hi_k) for h in H_INT_SWEEP + (hdecl,)]
            ext = T.i_boil(kap, gap, tb, T.U_passive(sig, hdecl, h_ext=T.h_ext_at(tb))) / ref
            lo, hi = min(vals), max(vals + hot)
            e0, e1 = _hint_ends(kap, gap, tb, sig, hdecl)
            out["%s %s ceiling" % (nm, label)] = dict(
                value=round(ref, 2), lower=round(lo, 2), upper=round(hi, 2),
                driver="kappa band %.3g-%.3g S/m, widened by h_int 50 W m-2 K-1 to the well-stirred limit (%+.0f/%+.0f%%) and h_ext(T_b) (%+.1f%%)"
                       % (lo_k, hi_k, 100 * e0, 100 * e1, 100 * (ext - 1)),
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
            ## h_int enters the availability; the ratio is evaluated at both ends of its sweep in this cell
            vals = [T.U_required(idesign, k, gap, tb) / T.U_passive(sig, h) for k in (lo_k, hi_k) for h in H_INT_SWEEP + (hi_int,)]
            lo_r, hi_r = min(vals), max(vals)
            _tag = ("zero-gap" if "zero-gap" in rl else "25 um" if "microfluidic" in rl
                    else "RDE" if "RDE" in rl else "rotating-cylinder")
            key = "%s %s cooling shortfall" % (nm, _tag)
            out[key] = dict(value=round(ref, 2), lower=round(lo_r, 2), upper=round(hi_r, 2),
                driver="U'_required(i_design=%g)/U'_passive over the kappa band %.3g-%.3g S/m and h_int 50 W m-2 K-1 "
                       "to the well-stirred limit" % (idesign, lo_k, hi_k),
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
        if k not in dl:
            ## 2026-10-05: this was a silent `continue`. Six rows had been renamed in the reaction table while
            ## julia/delta_bounds.csv still carried their old names, so their 42 cells dropped out of the band
            ## edges and every "bound" was computed over 44 rows against a central value over 50 -- lower edges
            ## above the central value, and no error. A row without a film band is a stale input, not a skip.
            raise SystemExit("julia/delta_bounds.csv has no film band for %s / %s -- re-run julia/emit_deltas.jl" % k)
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
    ## one cell per mediated row and archetype, counted from the published mediated matrix (a typed 48, then 8 x 7)
    NCELL = sum(1 for _ in io.open(os.path.join(JLD, "mediated_ec_matrix.csv"), encoding="utf-8")) - 1
    if NCELL <= 0 or NCELL % len(ARCH):
        raise SystemExit("mediated_ec_matrix.csv holds %d cells, not a whole number of rows x %d archetypes" % (NCELL, len(ARCH)))
    bad = []
    for e in ("lo", "hi"):
        f = os.path.join(JLD, "mediated_ec_matrix_band_%s.csv" % e)
        if not os.path.exists(f):
            bad.append("%s missing" % e); continue
        n = sum(1 for _ in io.open(f, encoding="utf-8")) - 1
        if n != NCELL:
            bad.append("%s has %d of %d cells" % (e, n, NCELL))
    # one cell per SOURCED catalyst row and archetype; the rows are read from the published sourced solve (seven until the
    # chemistry audit of 2026-10-05, four since), never typed
    NSRC = len({r["reaction"] for r in csv.DictReader(io.open(os.path.join(JLD, "catalyst_ec_sourced.csv"), encoding="utf-8"))
                if float(r["k_M"]) > 0})
    for e, fn in (("lo", "catalyst_ec_band_lo.csv"), ("hi", "catalyst_ec_band_hi.csv")):
        f = os.path.join(JLD, fn)
        if not os.path.exists(f):
            bad.append("catalyst %s missing" % e); continue
        n = sum(1 for _ in io.open(f, encoding="utf-8")) - 1
        if NSRC == 0 or n != NSRC * len(ARCH):
            bad.append("catalyst %s has %d of %d cells" % (e, n, NSRC * len(ARCH)))
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
    # the h_int sweep's effect on every boil-off ceiling, per architecture, over the four solvents (SI S10 prints it)
    eff = {}
    for rl, gap, sig, hi_int, idesign in T.REACTORS:
        e = [_hint_ends(kap, gap, tb, sig, hi_int) for nm, el, kap, tb, cls in T.SOLVENTS]
        eff[rl.replace("\n", " ")] = {"h_int": hi_int, "low_pct": [100 * min(x[0] for x in e), 100 * max(x[0] for x in e)],
                                       "high_pct": [100 * min(x[1] for x in e), 100 * max(x[1] for x in e)]}
    res["h_int_effect"] = eff
    res["h_ext_T_pct"] = {nm: 100 * (v - 1) for nm, v in H_EXT_T.items()}
    # does any verdict (ceiling against the cell's own transport ceiling) reverse anywhere in the sweep?
    res["h_int_flips"] = [[rl.replace("\n", " "), nm] for rl, gap, sig, hi_int, idesign in T.REACTORS
                          for nm, el, kap, tb, cls in T.SOLVENTS for h in H_INT_SWEEP
                          if (T.i_boil(kap, gap, tb, T.U_passive(sig, h)) >= idesign)
                          != (T.i_boil(kap, gap, tb, T.U_passive(sig, hi_int)) >= idesign)]
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
