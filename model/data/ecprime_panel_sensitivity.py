#!/usr/bin/env python3
"""G-ECPANEL -- do the regime labels on the EC' panels survive the two diffusivities behind them?

    cd Section4_Model && python data/ecprime_panel_sensitivity.py
    cd Section4_Model && python data/ecprime_panel_sensitivity.py --negative-control

WHY
---
Which EC' regime a rate constant falls in is decided by two ratios, delta/x_k and gamma, and both are built from D_med
and D_S. Setting delta/x_k = 1 and delta/x_k = gamma for the crossing rate constants gives

    x_k = sqrt(D_ox / (k C_S))                        gamma = i_cap / i_shuttle = n_S |s_red| D_S C_S / (D_red C_med)
    k1 = D_ox / (C_S delta^2)                         -- shuttle | kinetic boundary
    k2 = gamma^2 k1 = (n_S s_red)^2 D_S^2 C_S D_ox / (D_red^2 C_med^2 delta^2)   -- kinetic | total-catalysis boundary

(Eqs. S12-S15; D_ox = D_red = D_med for the base case and for two of the three rows; the bromination row's Br2 and Br- differ).
With both mediator forms scaled together, k1 ~ D_med^(+1) and k2 ~ D_S^(+2) D_med^(-1): the two boundaries do NOT move
together, the lower one is blind to D_S and the upper one is twice as sensitive to D_S as to anything else. The exponents are MEASURED from the formulas below rather
than asserted from this docstring.

TWO SUBJECTS, SINCE v90 (2026-09-11)
------------------------------------
(1) The SI's own base case (S5.4, Fig. H; julia/run_ecprime.jl): D_med = 6e-10 and D_S = 1e-9 m2/s are DECLARED (state C,
    Table S7 category 4), so the SI states how far the boundaries move across +/-25 % and how far the Fig. H rate constants
    sit from them. The constants are parsed out of run_ecprime.jl, never retyped.
(2) Main-text Fig. 6d-f, which since v90 draws three REAL mediated rows (anisole bromination / ACT / NHPI; the bromination row replaced the
    Hofmann rearrangement on 2026-10-06, when the Hofmann constant became the measured 3.3 M-1 s-1) at their k on the
    36.2 um ANEC film (julia/run_mediated_profiles.jl). Their diffusivities are the rows' own (Table S6). The regime label
    on each panel is assigned FROM THE SOLVE (substrate exhausted at the wall / most of the activated mediator escaping /
    neither) and the same solver re-solves every row with D_med and D_S scaled by 0.75 and 1.25 and writes the label it
    gets each time (mediated_ec_profiles_dsens.csv). This gate requires, per row: the solved label equals the analytic one
    at the base values; every perturbed solve returns the same label; no perturbed solve failed to reach a plateau. The
    analytic margin of each k to its nearest boundary is reported beside the boundary's own movement so the SI can state
    both -- a margin smaller than the movement is NOT a failure once the re-solves confirm the label, it is the reason the
    re-solves exist.

Until v89 this gate read the base-case constants out of figs/combined_figure.py by parsing its source (importing that
module re-renders the figure); the figure no longer carries a base case, so nothing here touches figs/.
"""
import io, json, math, os, re, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUN_ECPRIME = os.path.join(ROOT, "julia", "run_ecprime.jl")
PROFILES = os.path.join(ROOT, "julia", "mediated_ec_profiles.csv")
DSENS = os.path.join(ROOT, "julia", "mediated_ec_profiles_dsens.csv")
FIGH_PROFILES = os.path.join(ROOT, "julia", "npp_ecprime_profiles.csv")
BAND = 0.25
WANT = {"k1": {"D_med": 1.0, "D_S": 0.0}, "k2": {"D_med": -1.0, "D_S": 2.0}}


def base_case_consts():
    """The verbatim `const` declarations of julia/run_ecprime.jl (delta, C_med, C_S, D_med, D_S), read from the file."""
    src = io.open(RUN_ECPRIME, encoding="utf-8").read()
    out = {}
    for name in ("delta", "C_med", "C_S", "D_med", "D_S"):
        m = re.search(r"^const\s+%s\s*=\s*([0-9.eE+-]+)" % name, src, re.M)
        if not m:
            raise SystemExit("run_ecprime.jl no longer declares `const %s`" % name)
        out[name] = float(m.group(1))
    return out


def k1(D_med, D_S, C_S, C_med, delta, nS_s=1.0, r_ox=1.0):
    """delta/x_k = 1; D_ox = r_ox * D_med (r_ox = 1 unless the two mediator forms differ)."""
    return r_ox * D_med / (C_S * delta ** 2)


def k2(D_med, D_S, C_S, C_med, delta, nS_s=1.0, r_ox=1.0):
    """delta/x_k = gamma, gamma = n_S |s_red| D_S C_S / (D_red C_med), D_red = D_med, D_ox = r_ox D_med."""
    return (nS_s ** 2) * D_S ** 2 * C_S * r_ox / (D_med * C_med ** 2 * delta ** 2)


def boundaries(base):
    """The two crossing rate constants at the base values and across the +/-BAND band on D_med (both forms together) and D_S."""
    rep = {}
    for fname, f in (("k1", k1), ("k2", k2)):
        vals = []
        for fm in (1 - BAND, 1.0, 1 + BAND):
            for fs in (1 - BAND, 1.0, 1 + BAND):
                d = dict(base, D_med=base["D_med"] * fm, D_S=base["D_S"] * fs)
                vals.append(f(**d))
        rep[fname] = {"base": f(**base) * 1e3, "lo": min(vals) * 1e3, "hi": max(vals) * 1e3,     # m3/mol/s -> M-1 s-1
                      "span_decades": math.log10(max(vals) / min(vals))}
    return rep


## Three labels along the kinetic axis (2026-10-05), as julia/run_mediated_profiles.jl names them: the share of the activated
## mediator consumed inside the film is 1 - 1/cosh(delta/x_k) for a first-order step with the substrate in excess, so one
## third and two thirds are delta/x_k = acosh(3/2) and acosh(3), i.e. k = A_LO k1 and k = A_HI k1 (k1 is delta = x_k).
A_LO, A_HI = math.acosh(1.5) ** 2, math.acosh(3.0) ** 2


def margin(k_M, rep):
    """Decades to the nearest label boundary: the two edges of the mixed band (both move as k1) and k2."""
    return min(abs(math.log10(k_M / (A_LO * rep["k1"]["base"]))), abs(math.log10(k_M / (A_HI * rep["k1"]["base"]))),
               abs(math.log10(k_M / rep["k2"]["base"])))


def margin_two(k_M, rep):
    """The SI's base case (Fig. H) is read against the two analytic crossings k1 and k2 themselves."""
    return min(abs(math.log10(k_M / rep["k1"]["base"])), abs(math.log10(k_M / rep["k2"]["base"])))


def analytic_two(k_M, rep):
    return "mediator-limited" if k_M < rep["k1"]["base"] else ("substrate-limited" if k_M > rep["k2"]["base"] else "kinetic")


def analytic_regime(k_M, rep):
    if k_M < A_LO * rep["k1"]["base"]:
        return "mediator-limited"
    if k_M > rep["k2"]["base"]:
        return "substrate-limited"
    return "kinetic" if k_M > A_HI * rep["k1"]["base"] else "mixed"


def main(neg=False):
    bad = []
    # (1) MEASURE the exponents rather than assert them
    base = base_case_consts()
    b0 = dict(D_med=base["D_med"], D_S=base["D_S"], C_S=base["C_S"], C_med=base["C_med"], delta=base["delta"])
    meas = {}
    for fname, f in (("k1", k1), ("k2", k2)):
        meas[fname] = {}
        for var in ("D_med", "D_S"):
            fac = 1.10
            a = dict(b0); b = dict(b0); b[var] = b0[var] * fac
            if neg and fname == "k2" and var == "D_S":
                b[var] = b0[var]                     # make the response vanish
            r = f(**b) / f(**a)
            p = math.log(r) / math.log(fac) if r > 0 else float("nan")
            meas[fname][var] = p
            if abs(p - WANT[fname][var]) > 1e-6:
                bad.append("%s responds to %s as ^%.4f; the stated algebra says ^%.1f" % (fname, var, p, WANT[fname][var]))
    print("  measured response exponents (perturb the input, read the output):")
    print("    %-26s %-12s %s" % ("boundary", "d ln k / d ln D_med", "d ln k / d ln D_S"))
    print("    %-26s %-12.4f %.4f" % ("k1  shuttle | kinetic", meas["k1"]["D_med"], meas["k1"]["D_S"]))
    print("    %-26s %-12.4f %.4f" % ("k2  kinetic | total cat.", meas["k2"]["D_med"], meas["k2"]["D_S"]))

    # (2) the SI's own base case (S5.4 / Fig. H): boundaries, their movement, the Fig. H rate constants' margins
    gamma0 = base["D_S"] * base["C_S"] / (base["D_med"] * base["C_med"])
    rep0 = boundaries(b0)
    figh_k = sorted(set(pd.read_csv(FIGH_PROFILES).k_M.astype(float))) if os.path.exists(FIGH_PROFILES) else []
    m0 = [margin_two(k, rep0) for k in figh_k]
    print("\n  base case (julia/run_ecprime.jl, the SI's S5.4 / Fig. H): D_med %.3g  D_S %.3g m2/s ; C_med %.4g  C_S %.4g mol/m3 ; delta %.4g m ; gamma %.2f"
          % (base["D_med"], base["D_S"], base["C_med"], base["C_S"], base["delta"], gamma0))
    for f in ("k1", "k2"):
        print("    %s: %.4g M-1 s-1, band [%.4g, %.4g] = %.2f decades" % (f, rep0[f]["base"], rep0[f]["lo"], rep0[f]["hi"], rep0[f]["span_decades"]))
    for k, m in zip(figh_k, m0):
        print("    Fig. H k = %-8g -> %-18s nearest boundary %.2f decades away" % (k, analytic_two(k, rep0), m))
    worst0 = max(rep0[f]["span_decades"] for f in rep0)

    # (3) the three rows of main-text Fig. 6d-f: solved labels, analytic labels, margins, and the re-solved labels
    prof = pd.read_csv(PROFILES).groupby("short").first()
    ds = pd.read_csv(DSENS)
    if neg:
        ds = ds.copy(); ds.loc[ds.index[0], "regime_solved"] = "kinetic" if ds.iloc[0].regime_solved != "kinetic" else "mediator-limited"
    rows = {}
    print("\n  main-text Fig. 6d-f (julia/run_mediated_profiles.jl, delta = %.1f um):" % float(prof.delta_um.iloc[0]))
    for short, r in prof.iterrows():
        nS_s = float(r.n_S) * float(r.s_red)
        b = dict(D_med=float(r.D_red), D_S=float(r.D_S), C_S=float(r.C_S_molm3), C_med=float(r.C_med_molm3), delta=float(r.delta_um) * 1e-6,
                 nS_s=nS_s, r_ox=float(r.D_ox) / float(r.D_red))
        rep = boundaries(b)
        k_M = float(r.k_M)
        ana = analytic_regime(k_M, rep)
        pert = ds[ds["short"] == short]
        labels = sorted(set(pert.regime_solved.astype(str)))
        survive = (len(pert) == 4) and labels == [str(r.regime_solved)]
        rows[short] = {"k_M": k_M, "delta_um": float(r.delta_um), "xk_um": float(r.xk_um), "gamma": float(r.gamma),
                       "ilim_mAcm2": float(r.ilim_mAcm2), "share_in_film": float(r.share_in_film), "c_S_surf_norm": float(r.c_S_surf_norm),
                       "regime_solved": str(r.regime_solved), "regime_analytic_solver": str(r.regime_analytic), "regime_analytic_gate": ana,
                       "boundaries": rep, "margin_decades": margin(k_M, rep), "worst_span_decades": max(rep[f]["span_decades"] for f in rep),
                       "perturbations": [{"var": str(p["var"]), "factor": float(p.factor), "ilim_mAcm2": float(p.ilim_mAcm2), "regime_solved": str(p.regime_solved)}
                                         for _, p in pert.iterrows()],
                       "label_survives": bool(survive)}
        print("    %-8s k = %-6g %-18s solved | analytic %-18s | k1 %.3g  k2 %.3g M-1 s-1 | margin %.2f dec, boundaries move %.2f dec | re-solved labels: %s -> %s"
              % (short, k_M, r.regime_solved, ana, rep["k1"]["base"], rep["k2"]["base"], rows[short]["margin_decades"],
                 rows[short]["worst_span_decades"], ", ".join(labels), "survive" if survive else "MOVE"))
        if ana != str(r.regime_solved):
            bad.append("%s: the solve names %s where the analytic assignment gives %s" % (short, r.regime_solved, ana))
        if ana != str(r.regime_analytic):
            bad.append("%s: this gate's analytic assignment (%s) disagrees with the solver's own (%s)" % (short, ana, r.regime_analytic))
        if not survive:
            bad.append("%s: the regime label does not survive +/-%.0f%% on the diffusivities (re-solved labels %s)" % (short, 100 * BAND, labels))
        if "no-plateau" in labels:
            bad.append("%s: a perturbed solve reached no plateau" % short)

    out = {"band": BAND, "exponents": meas,
           "base": {"source": "julia/run_ecprime.jl", "D_med": base["D_med"], "D_S": base["D_S"], "C_S": base["C_S"], "C_med": base["C_med"],
                    "delta": base["delta"], "gamma": gamma0, "boundaries": rep0, "figH_k": figh_k, "figH_margin_decades": m0,
                    "worst_span_decades": worst0},
           "rows": rows, "labels_survive": all(v["label_survives"] for v in rows.values()),
           "rows_min_margin_decades": min(v["margin_decades"] for v in rows.values()),
           "rows_worst_span_decades": max(v["worst_span_decades"] for v in rows.values()),
           # kept for the SI's base-case sentence
           "worst_span_decades": worst0, "margin_decades": m0}
    json.dump(out, io.open(os.path.join(ROOT, "results", "ecprime_panel_sensitivity%s.json" % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"), indent=1)

    if neg:
        print("\nNEGATIVE CONTROL: k2's response to D_S suppressed AND one re-solved label flipped in memory; both must be detected.")
        exp_hit = any("responds to" in b for b in bad); lab_hit = any("does not survive" in b for b in bad)
        print("G-ECPANEL control: %s" % ("GOOD (exponent disagreement and label movement both detected)" if (exp_hit and lab_hit)
                                          else "BAD -- test is inert (exponent %s, label %s)" % (exp_hit, lab_hit)))
        return 0 if (exp_hit and lab_hit) else 1
    if bad:
        print("\nG-ECPANEL: FAIL -- " + "; ".join(bad))
        return 1
    print("\nG-ECPANEL: PASS -- k1 ~ D_med and k2 ~ D_S^2/D_med as stated; the base case's boundaries move at most %.2f decades across "
          "+/-%.0f%% (Fig. H rate constants %s decades from the nearest); on the three Fig. 6d-f rows the solved regime equals the analytic one "
          "and every label survives the +/-%.0f%% re-solves (analytic margins %.2f decades or more against boundaries moving up to %.2f)"
          % (worst0, 100 * BAND, "/".join("%.2f" % m for m in m0), 100 * BAND, out["rows_min_margin_decades"], out["rows_worst_span_decades"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
