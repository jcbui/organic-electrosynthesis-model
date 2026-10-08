"""The manuscript phrases that carry archetype numbers, computed from the model artifacts.

CHARACTERS: the .docx writes the micron as MICRO SIGN (U+00B5) and the unit as "mA cm" + SUPERSCRIPT MINUS
+ SUPERSCRIPT TWO; the phrases below use exactly those, so they match the document byte for byte. Gates that
read NFKC-normalised text must normalise the phrase too (check_ms_derived.py does).

ONE SOURCE for two consumers: MS Drafts/scripts/apply_v76_fixes.py writes these phrases into the
manuscript, and data/check_ms_derived.py (G-MSDERIVED) pins the manuscript to them. Neither types a
number: every value is read from julia/tier0_ec_matrix.csv, julia/profiles_direct.csv,
julia/mediated_ec_matrix.csv and figs/model_medians.py, rounded the way the manuscript prints it.

    cd Section4_Model && python data/ms_phrases.py        # prints every phrase
"""
import os
import numpy as np, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "figs"))

ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
BAR = 50.0


def _fmed(v):
    return "%.0f" % v if v >= 100 else "%.1f" % v


_NW = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
       "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def phrases():
    import pandas as pd
    import model_medians as MM
    mat = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    pf = pd.read_csv(os.path.join(ROOT, "julia", "profiles_direct.csv"))
    med = {k: float(mat[k].median()) for k in ARCH}
    n25 = {k: int((mat[k] >= 25).sum()) for k in ARCH}
    n50 = {k: int((mat[k] >= 50).sum()) for k in ARCH}
    dmed = {k: MM.delta_median(k) for k in ARCH}
    drng = {k: MM.delta_range(k) for k in ARCH}
    P = {}
    # ---- Section 3 tiers (bands are the delta_eff ranges of each tier's members, as Fig. 2b draws them)
    t2lo = min(drng["flow"][0], drng["anec"][0]); t2hi = max(drng["flow"][1], drng["anec"][1])
    t3lo = min(drng[k][0] for k in ("micro", "rde", "rce")); t3hi = max(drng[k][1] for k in ("micro", "rde", "rce"))
    P["tier2_band"] = "Tier 2 (δ ≈ %.0f–%.0f µm)" % (t2lo, t2hi)
    P["tier2_gain"] = ("raises the median ceiling from %.0f to %.0f mA cm⁻² in a recirculating flow cell "
                       "and to %.0f in a cell whose inlet is aimed at the electrode" % (med["stirred"], med["flow"], med["anec"]))
    P["tier2_gain_values"] = [med["stirred"], med["flow"], 2, med["anec"]]   # the "cm⁻²" between flow and ANEC parses as a 2
    P["tier3_band"] = "Tier 3 (δ ≈ %.0f–%.0f µm)" % (t3lo, t3hi)
    P["tier3_values"] = [3, t3lo, t3hi]
    P["tier2_values"] = [2, t2lo, t2hi]          # "Tier 2 (" contributes the leading 2 to a positional match
    # ---- Fig. 2 caption (a): six cells on one film scale
    P["fig2a_cells"] = ("(a) Six reactor archetypes, from unstirred batch (δ ≈ %.0f µm) through stirred batch "
                        "(%.0f µm), a recirculating flow cell (%.0f µm) and the ANEC flow cell, whose inlet is angled "
                        "20° toward the electrode (%.0f µm), to a 25 µm-gap microfluidic cell (%.1f µm, the "
                        "half-gap) and a rotating cylinder (%.0f–%.0f µm); the two flow-cell films are measured "
                        "on the cells themselves"
                        % (dmed["natural"], dmed["stirred"], dmed["flow"], dmed["anec"], dmed["micro"],
                           drng["rce"][0], drng["rce"][1]))
    P["fig2a_flow"] = "a recirculating flow cell (%.0f µm)" % dmed["flow"]
    P["fig2a_flow_values"] = [dmed["flow"]]
    P["fig2a_anec"] = "toward the electrode (%.0f µm)" % dmed["anec"]
    P["fig2a_anec_values"] = [dmed["anec"]]
    P["fig2a_micro"] = "microfluidic cell (%.1f µm, the half-gap)" % dmed["micro"]
    P["fig2a_micro_values"] = [dmed["micro"]]
    P["fig2a_rce"] = "a rotating cylinder (%.0f–%.0f µm)" % (drng["rce"][0], drng["rce"][1])
    P["fig2a_rce_values"] = [drng["rce"][0], drng["rce"][1]]
    # ---- Fig. 2 caption (b): the seven medians in architecture order
    # "a, b, c, d, e, f and g", in architecture order
    _ints = ["%.0f" % med[k] for k in ARCH]
    P["fig2b_medians"] = "%s and %s mA cm⁻² from unstirred batch to rotating cylinder" % (", ".join(_ints[:-1]), _ints[-1])
    P["fig2b_median_values"] = [med[k] for k in ARCH]
    P["fig2b_seven"] = "in each of seven architectures"
    P["fig2b_tiers"] = "the seven archetype medians populate Tiers 1–3"
    # ---- Fig. 3 caption (a): six films, every value from the profile solve
    cv = {c: pf[pf.case == c].iloc[0] for c in ("rce", "micro", "anec", "flow", "stirred", "unstirred")}
    cs = {c: 1.0 - float(cv[c].i_mAcm2) / float(cv[c].ilim_mAcm2) for c in cv}
    P["fig3a_supplied"] = ("a rotating cylinder (δ = %.0f µm), a 25 µm microfluidic cell (δ = %.1f µm) and the "
                           "ANEC flow cell (δ = %.0f µm) keep the surface supplied (c_surf = %.2f, %.2f and %.2f)"
                           % (cv["rce"].delta_um, cv["micro"].delta_um, cv["anec"].delta_um, cs["rce"], cs["micro"], cs["anec"]))
    P["fig3a_supplied_films_values"] = [float(cv["rce"].delta_um), 25, float(cv["micro"].delta_um), float(cv["anec"].delta_um)]
    P["fig3a_supplied_films"] = ("a rotating cylinder (δ = %.0f µm), a 25 µm microfluidic cell (δ = %.1f µm) and the "
                                 "ANEC flow cell (δ = %.0f µm)" % (cv["rce"].delta_um, cv["micro"].delta_um, cv["anec"].delta_um))
    P["fig3a_surfaces"] = "(c_surf = %.2f, %.2f and %.2f)" % (cs["rce"], cs["micro"], cs["anec"])
    P["fig3a_surface_values"] = [cs["rce"], cs["micro"], cs["anec"]]
    # the recirculating cell's own ceiling for this exemplar sits below the barrier, so it is starved
    # like the two batch cells; the profile solve ran it at its own i_lim (c_surf -> 0)
    starved = [c for c in ("flow", "stirred", "unstirred") if float(cv[c].ilim_mAcm2) < BAR]
    if starved != ["flow", "stirred", "unstirred"]:
        raise SystemExit("Fig. 3a starved set is %r; the caption phrase below assumes flow, stirred and unstirred" % starved)
    P["fig3a_starved"] = ("whereas a recirculating flow cell (δ = %.0f µm), a stirred beaker (δ = %.0f µm) and an "
                          "unstirred cell (δ = %.0f µm) are starved, with no steady state at 50 mA cm⁻² (their curves "
                          "are shown at their own lower i_lim of %.0f, %.0f and %.0f mA cm⁻²)"
                          % (cv["flow"].delta_um, cv["stirred"].delta_um, cv["unstirred"].delta_um,
                             cv["flow"].ilim_mAcm2, cv["stirred"].ilim_mAcm2, cv["unstirred"].ilim_mAcm2))
    P["fig3a_starved_films"] = ("a recirculating flow cell (δ = %.0f µm), a stirred beaker (δ = %.0f µm) and an "
                                "unstirred cell (δ = %.0f µm) are starved"
                                % (cv["flow"].delta_um, cv["stirred"].delta_um, cv["unstirred"].delta_um))
    P["fig3a_starved_films_values"] = [float(cv[c].delta_um) for c in ("flow", "stirred", "unstirred")]
    P["fig3a_starved_ceilings"] = "i_lim of %.0f, %.0f and %.0f mA cm⁻²" % tuple(float(cv[c].ilim_mAcm2) for c in ("flow", "stirred", "unstirred"))
    P["fig3a_starved_ceiling_values"] = [float(cv[c].ilim_mAcm2) for c in ("flow", "stirred", "unstirred")]
    P["sec4_supplied"] = "while an angled-inlet flow cell, a microfluidic cell or a rotating cylinder keeps the surface well supplied"
    P["fig3a_six"] = "across six reactors, each at its archetype's film from Figure 2b"
    P["fig3a_films_note"] = ("The two batch films are the archetype values of Table S1 and the four convective films are the "
                             "archetype films Figure 2b plots (the rotating cylinder at its median);")
    # ---- Fig. 3 (b), Fig. 4: seven architectures, 56 solver rows
    P["fig3b_seven"] = "across seven architectures"
    import csv
    with open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"), encoding="utf-8") as fh:
        n_med_rows = sum(1 for _ in csv.DictReader(fh))
    P["fig4c_rows"] = "All %d solver rows are plotted" % n_med_rows
    P["fig4c_rows_values"] = [n_med_rows]
    P["fig4_every_seven"] = "in every one of the seven architectures"
    P["fig4_own_seven"] = "across their own seven architectures"
    # ---- Section 8 ladder and the TRL-E table
    P["sec8_ladder"] = ("stirred batch reaches %s, a recirculating flow cell %s, the ANEC flow cell %s, a 25 µm "
                        "microfluidic cell %s, and a rotating-cylinder electrode %s mA cm⁻²"
                        % (_fmed(med["stirred"]), _fmed(med["flow"]), _fmed(med["anec"]), _fmed(med["micro"]), _fmed(med["rce"])))
    P["sec8_ladder_values"] = [med["stirred"], med["flow"], med["anec"], 25, med["micro"], med["rce"]]   # "25 µm" sits between ANEC and the microfluidic median
    lo25 = min(n25["flow"], n25["anec"], n25["micro"]); hi25 = max(n25["flow"], n25["anec"], n25["micro"])
    P["trle_counts"] = "%d–%d/50 clear" % (lo25, hi25)
    P["trle_count_values"] = [lo25, hi25, 50]
    P["trle_arch"] = "flow cell / micro-flow"
    # ---- Fig. 4c: the fitted log-log slopes of the eight mediated traces across the seven films
    _sl = MM.mediated_delta_slopes()
    _flat = sorted(-v["slope"] for v in _sl.values() if v["slope"] > -0.5)
    _steep = sorted(-v["slope"] for v in _sl.values() if v["slope"] <= -0.5)
    if len(_flat) < 2 or not _steep:
        raise SystemExit("the slope sentence needs at least two flat mediated traces and one steep one; model has %d and %d" % (len(_flat), len(_steep)))
    P["fig4c_flat"] = "slopes −%.2f and −%.2f" % (_flat[0], _flat[1])
    P["fig4c_flat_values"] = [_flat[0], _flat[1]]
    P["fig4c_steep"] = "the other %s run −%.2f to −%.2f" % (_NW[len(_steep)], _steep[0], _steep[-1])
    # the Section 4 sentence that names the architecture-independent mediated rows (2026-10-05: four of eleven) and, since the
    # NHPI row took the rate constant measured for an allylic C-H (20.2 M-1 s-1), the one row that crosses from mediator-transport
    # control in the thin films to a kinetic plateau in the thick ones: three bins, flat above -0.3, crossover, steep at -0.5 and below
    _FLATNAME = {"ACT-mediated alcohol oxidation (flow, hectogram)": "ACT alcohol oxidation",
                 "HMF -> FDCA (biomass)": "HMF → FDCA oxidation",
                 "Thioether -> sulfone (kilo-scale)": "the chloride-mediated thioether oxidation",
                 "Cathodic Giese (R-I + alkene)": "the oxygen-mediated Giese addition"}
    # 2026-10-07: at the constant measured for HOBr with propionamide (3.3 M-1 s-1) the Hofmann row's reaction layer
    # (x_k = 41 um) is wider than the thin films and lies inside the batch films, so it crosses over the way NHPI does
    # (mediator transport in the thin films, in-film reaction in the thick ones, where it reaches its amide supply cap).
    # It is binned with NHPI by that mechanism, asserted below, whichever side of -0.3 its fitted slope falls.
    _HOF = "Br-mediated Hofmann rearrangement"
    _flatrows = [r for r, v in _sl.items() if v["slope"] > -0.3 and r != _HOF]
    _cross = [r for r, v in _sl.items() if -0.5 < v["slope"] <= -0.3 and r != _HOF]
    if set(_flatrows) != set(_FLATNAME):
        raise SystemExit("the architecture-independent mediated rows are %r; the sentence names %r" % (sorted(_flatrows), sorted(_FLATNAME)))
    if _cross != ["NHPI-mediated allylic C-H -> enone"]:
        raise SystemExit("the sentence names NHPI as the one crossover row (slope between -0.3 and -0.5); the model gives %r" % _cross)
    # Pass 4 of the chemistry audit (2026-10-06): a near-zero fitted slope is not the same thing as kinetic control. A row
    # whose current sits at (or above) its substrate cap in some film is substrate-limited there, and its shallow fit
    # comes from a rise and fall, not a plateau -- the thioether row: capped in the three thick films, peaking on the
    # ANEC film, kinetic in the thin ones (SI S5.5 says so). The kinetic set is therefore the flat rows with no capped cell.
    import pandas as _pd
    _mm = _pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"))
    # chemistry audit pass 7: the same test SI Table S6 and S5.5 use -- the current reaches the planar substrate cap (a 0.9
    # factor counted the thioether flow cell, at 0.95 of its cap with 11 % of the substrate left at the wall, where the SI
    # does not)
    _capped = {r for r, g in _mm.groupby("reaction") if (g.i_ec_mAcm2 >= g.i_subcap_mAcm2).any()}
    _hf = _mm[_mm.reaction == _HOF].sort_values("delta_um", ascending=False)
    _hfcap = _hf[_hf.i_ec_mAcm2 >= _hf.i_subcap_mAcm2]
    if not (-0.5 < _sl[_HOF]["slope"] < -0.2) or list(_hfcap.delta_um) != list(_hf.delta_um[:len(_hfcap)]) or len(_hfcap) < 2 \
            or (_hf[_hf.delta_um < 20].xk_um <= _hf[_hf.delta_um < 20].delta_um).any() \
            or (_hf[_hf.delta_um > 150].xk_um >= _hf[_hf.delta_um > 150].delta_um).any():
        raise SystemExit("the sentence bins the Hofmann row with NHPI (shallow slope; x_k above the thin films and below the batch "
                         "films; supply-capped in its thickest films only); the model disagrees")
    # which Hofmann cells the amide supply limits is MEASURED, not read off the cap test: a cell at its supply cap moves little
    # when k rises tenfold (results/rate_constant_cells.csv, the G-KSENS sweep). The two batch cells do; the recirculating cell,
    # above its planar cap but not limited by it in this sense, does not, so the sentence names the batch cells only.
    _kc = _pd.read_csv(os.path.join(ROOT, "results", "rate_constant_cells.csv"))
    _kh = _kc[_kc.reaction == _HOF].pivot(index="reactor", columns="factor", values="i_ec_mAcm2")
    _hb = _hf[_hf.reactor.str.contains("batch")]
    if len(_hb) != 2 or any(abs(float(_kh.loc[r, "base"]) / float(_hb[_hb.reactor == r].i_ec_mAcm2.iloc[0]) - 1) > 1e-4 for r in _hb.reactor):
        raise SystemExit("results/rate_constant_cells.csv was not swept at the Hofmann row's published constant; re-run G-KSENS")
    _hup = {r: float(_kh.loc[r, "mul10"]) / float(_kh.loc[r, "base"]) - 1 for r in _kh.index}
    _hsup = sorted(r for r in _hf.reactor if r in _hfcap.reactor.values and _hup.get(r, 9) <= 0.15)
    if _hsup != sorted(_hb.reactor):
        raise SystemExit("the sentence says the amide supply caps the Hofmann row in the two batch cells; the k sweep says %r" % _hup)
    _nh = _mm[_mm.reaction == "NHPI-mediated allylic C-H -> enone"]
    if (_nh[_nh.delta_um < 20].xk_um <= _nh[_nh.delta_um < 20].delta_um).any() or (_nh[_nh.delta_um > 150].xk_um >= _nh[_nh.delta_um > 150].delta_um).any():
        raise SystemExit("the sentence says NHPI passes from mediator transport in the thin films to in-film reaction in the thick ones")
    _kin = [r for r in _FLATNAME if r not in _capped]
    _flatcap = [r for r in _FLATNAME if r in _capped]
    if _flatcap != ["Thioether -> sulfone (kilo-scale)"]:
        raise SystemExit("the flat rows that reach their substrate cap are %r; the sentence singles out the thioether" % _flatcap)
    _th = _mm[_mm.reaction == "Thioether -> sulfone (kilo-scale)"].sort_values("delta_um", ascending=False)
    _thcap = _th[_th.i_ec_mAcm2 >= _th.i_subcap_mAcm2]
    if list(_thcap.delta_um) != list(_th.delta_um[:len(_thcap)]):
        raise SystemExit("the thioether's substrate-capped films are not its thickest ones")
    _pk = _th.loc[_th.i_ec_mAcm2.idxmax()]
    if not str(_pk.reactor).startswith("ANEC"):
        raise SystemExit("the thioether peaks on %r, not the ANEC film" % _pk.reactor)
    _thin = _th[_th.delta_um < 20]
    _kin4 = sorted(-_sl[r]["slope"] for r in _kin)
    _th_slope = -_sl["Thioether -> sulfone (kilo-scale)"]["slope"]
    _nhpi_slope = -_sl["NHPI-mediated allylic C-H -> enone"]["slope"]
    _kn = [_FLATNAME[r] for r in _kin]
    _steep_nh = sorted(-v["slope"] for r, v in _sl.items() if v["slope"] <= -0.5 and r != _HOF)
    P["med_flat_sentence"] = ("%s, %s, are nearly architecture-independent (kinetically controlled over most of the range), with log–log slopes of "
                              "−%.2f to −%.2f; the chloride-mediated thioether oxidation fits a similarly shallow slope (−%.2f) only "
                              "because it is substrate-limited in the %s thickest films, peaks on the ANEC film and falls again in "
                              "the %s thin films; NHPI allylic C–H oxidation and the bromide-mediated Hofmann rearrangement pass from "
                              "mediator-transport control in the thin films to reaction inside the thick ones (a kinetic plateau for NHPI, "
                              "the amide supply cap for the Hofmann row in the two batch cells), with slopes of −%.2f and −%.2f; and the other %s span −%.2f to −%.2f (SI Table S6)."
                              % (_NW[len(_kin)].capitalize(), ", ".join(_kn[:-1]) + " and " + _kn[-1],
                                 _kin4[0], _kin4[-1], _th_slope, _NW[len(_thcap)], _NW[len(_thin)],
                                 _nhpi_slope, -_sl[_HOF]["slope"], _NW[len(_steep_nh)], _steep_nh[0], _steep_nh[-1]))
    # The peak and thin-film currents are not printed: they rest on the chloride's declared diffusivity in its medium and
    # move by up to a factor of two across its bracket (registry, Table S7d), while the shape -- capped in the thick films,
    # a peak on the ANEC film, lower again in the thin ones -- holds at both ends of it.
    P["med_flat_values"] = [_kin4[0], _kin4[-1], _th_slope, _nhpi_slope, -_sl[_HOF]["slope"], _steep_nh[0], _steep_nh[-1]]
    P["fig4c_steep_values"] = [_steep[0], _steep[-1]]
    P["med"] = med; P["n25"] = n25; P["n50"] = n50; P["dmed"] = dmed; P["drng"] = drng
    # ---- the catalyst class under a finite k (results/catalyst_ec_sensitivity.json, G-CATK) ----
    # The matrix runs the eleven catalyst rows at k = 0, the floor of the EC' current; these phrases
    # state what the declared k band buys, from the sweep's own artifact, so the manuscript, its
    # gate and SI S5.7 read one number.
    import json
    ck = json.load(open(os.path.join(ROOT, "results", "catalyst_ec_sensitivity.json")))
    ks = [float(k) for k in ck["k_band_M"]]; kmax = max(ks)
    top = ck["per_k"]["%g" % kmax]
    sci = lambda k: {1000.0: "10³", 10000.0: "10⁴", 100000.0: "10⁵"}.get(float(k), "%g" % float(k))
    surv = ck["ten_of_eleven_survives_at_k"]
    hold = None; fail = None
    for k in ks:
        if surv["%g" % k]: hold = k
        else: fail = k; break
    cs = [r["C_S_M"] for r in ck["per_row"].values() if r.get("C_S_M") is not None]
    capped = sum(1 for r in ck["per_row"].values() if r["substrate_capped_at_kmax"])
    P["ck_kmax"] = sci(kmax); P["ck_amp"] = "%.0f" % top["max_amplification"]
    P["ck_n25"] = str(top["clear25"]); P["ck_hold"] = None if hold is None else sci(hold); P["ck_fail"] = None if fail is None else sci(fail)
    P["ck_cs_range"] = "%.2f–%.1f M" % (min(cs), max(cs)) if cs else ""
    P["ck_capped"] = str(capped)
    # the Section 4 sentence that follows the k = 0 count
    if fail is None:
        P["catalyst_finite_k"] = ("That count credits the catalyst with no turnover inside the film (k = 0), the floor of what a "
                                  "homogeneous carrier can deliver; allowing it to turn over at up to %s M⁻¹ s⁻¹ lifts the class's best "
                                  "ceilings by as much as %s-fold without carrying any of the %d above 25 mA cm⁻² (SI §S5.7)."
                                  % (P["ck_kmax"], P["ck_amp"], len(ck["per_row"])))
    else:
        P["catalyst_finite_k"] = ("That count credits the catalyst with no turnover inside the film (k = 0), the floor of what a "
                                  "homogeneous carrier can deliver; allowing it to turn over at up to %s M⁻¹ s⁻¹ lifts the class's best "
                                  "ceilings by as much as %s-fold and carries %s of the %d above 25 mA cm⁻², each then pinned by its "
                                  "substrate at %s rather than by the catalyst (SI §S5.7)."
                                  % (P["ck_kmax"], P["ck_amp"], P["ck_n25"], len(ck["per_row"]), P["ck_cs_range"]))
    P["catalyst_conclusion"] = (
        "yet 10 of 11 remain below 25 mA cm⁻² in every architecture when the catalyst is credited with no turnover "
        "inside the film; with fast homogeneous turnover the cap moves to the dilute substrate (SI §S5.7)."
        if fail is not None else
        "yet 10 of 11 remain below 25 mA cm⁻² in every architecture, at any rate constant in the declared band (SI §S5.7).")
    P["catalyst_caption_c"] = ("its band reaches from that floor to the eleven reactions re-solved at the top of the declared "
                               "rate-constant band (k = %s M⁻¹ s⁻¹)" % P["ck_kmax"])
    P["catalyst_both_limits"] = ("Catalyst-carried reactions are therefore limited by concentration either way: by the dilute "
                                 "substrate or the kinetic ceiling when catalysis is fast, and by the dilute catalyst when it "
                                 "is slow.")
    # ---- 2026-09-11: seven catalyst rows carried at a SOURCED rate constant (G-CATK "sourced" block) ----
    # The published matrix now overlays, for the seven rows whose substrate-consuming step has a measured
    # rate constant, the EC' solve at that constant (docs/CATALYST_RATE_CONSTANTS_20260911.md, SI S5.7).
    # Every number in these phrases is read from the gate's artifact or from the merged matrix.
    sr = ck.get("sourced")
    if sr:
        _m = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv")).merge(
            pd.read_csv(os.path.join(HERE, "reactions_50.csv"))[["reaction", "carrier_type"]], on="reaction")
        _cat = _m[_m.carrier_type == "catalyst"]
        # 2026-10-05: class MEDIANS leave out the chain row (the cobalt-hydride isomerization, tabulated at the
        # 0.5 F/mol it passes; SI Table S10 and S4.2), class COUNTS are over every catalyst row of the table.
        _cat_st = _cat[~_cat.reaction.isin(MM.CHAIN)]
        if len(_cat) - len(_cat_st) != 1:
            raise SystemExit("expected exactly one chain row in the catalyst class, found %d" % (len(_cat) - len(_cat_st)))
        _cn, _cr = float(_cat_st["natural"].median()), float(_cat_st["rce"].median())
        P["cat_med_natural_all"], P["cat_med_rce_all"] = float(_cat["natural"].median()), float(_cat["rce"].median())
        _below = int((_cat[["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]].max(axis=1) < 25).sum())
        P["cat_gain_median"] = "%.0f" % (_cr / _cn); P["cat_med_natural"] = _fmed(_cn); P["cat_med_rce"] = _fmed(_cr)
        P["cat_below25"] = str(_below); P["cat_n"] = str(len(_cat))
        # v106 (2026-09-16): the author's own wording in the submission draft; every number still computed
        # chemistry audit, 2026-10-05: with eight of the twelve rows at the k = 0 floor the class median IS a floor row, so it gains
        # the full reduction in delta; the author's "rises only N-fold" would now be backwards. The sentence says why, and asserts it.
        # a floor row's ceiling is nFD_catC_cat/delta, so its gain IS its own film ratio (the rotating-cylinder film depends on
        # the row's D and viscosity, so that ratio is per row, not the 50-row median film ratio)
        _fl = _cat[_cat.reaction.isin(sr["rows_floor"])]
        _flg = (_fl["rce"] / _fl["natural"]).values
        _nfl = int(sr["n_floor"])
        if not (_flg.min() * 0.97 <= _cr / _cn <= _flg.max() * 1.03) or 2 * _nfl <= len(_cat):
            raise SystemExit("the catalyst-median sentence says the median gains the full reduction in delta because most rows sit at "
                             "the floor; gain %.1f against floor-row gains %.1f-%.1f, %d of %d at the floor"
                             % (_cr / _cn, _flg.min(), _flg.max(), _nfl, len(_cat)))
        P["cat_n_floor"] = str(_nfl)
        P["catalyst_span"] = ("Across the seven architectures, the median ceiling of catalyst-carried reactions rises %s-fold, "
                              "from %s to %s mA cm⁻² over the %s that are not chain reactions, the full reduction in δ, because "
                              "%s of the %s carry no measured rate constant and sit at the transport floor; %s of the %s still "
                              "remain below 25 mA cm⁻² (Figure 5b)."
                              % (P["cat_gain_median"], P["cat_med_natural"], P["cat_med_rce"], _NW[len(_cat_st)], P["cat_n_floor"],
                                 P["cat_n"], P["cat_below25"], P["cat_n"]))
        # 2026-10-07 (author: restore the pedagogy): the same facts as catalyst_span, told as cause and effect -- the class
        # median rises with the film because most rows carry no in-film turnover (k = 0) and so ARE their transport floor
        _w23 = "two-thirds" if 3 * _nfl == 2 * len(_cat) else ("%s of the %s" % (_NW[_nfl], _NW[len(_cat)]))
        if int(P["cat_below25"]) != len(_cat) - 1:
            raise SystemExit("the catalyst sentence says all but one of the %d remain below 25 mA cm-2; %s do" % (len(_cat), P["cat_below25"]))
        P["catalyst_span_short"] = ("Across the seven architectures, the median ceiling of catalyst-carried reactions rises from %s "
                                    "to %s mA cm⁻² (one chain reaction excluded), and all but one of the %s remain below "
                                    "25 mA cm⁻² (Figure 5b). That rise is simply the reduction in δ, because %s of these "
                                    "catalysts are carried with no homogeneous turnover (k = 0) and sit at the transport floor."
                                    % (P["cat_med_natural"], P["cat_med_rce"], _NW[len(_cat)], _w23))
        P["catalyst_span_short_values"] = [_cn, _cr, 2, 25, 2]
        _gl, _gh = sr["gain_sourced_min"], sr["gain_sourced_max"]
        P["cat_gain_lo"] = "%.0f" % _gl; P["cat_gain_hi"] = "%.0f" % _gh; P["cat_gain_floor"] = "%.0f" % sr["gain_floor_median"]
        _hi_edge_n = sr["rows_clearing25_anywhere_at_band"][1]
        # v106: the author expanded this into three per-row sentences. The kinetic ceiling a row approaches
        # as δ -> 0 is the Savéant plateau nFD_catC_cat/x_k, which is i(k=0) at the 12.5 µm microfluidic film
        # scaled by that film over x_k -- computed here, never typed.
        _SUP = {"0": "\u2070", "1": "\u00b9", "2": "\u00b2", "3": "\u00b3", "4": "\u2074"}

        def _kfmt_k(v):
            """100 -> 10², 700 -> 7 × 10², 10 -> 10: the way the manuscript prints a rate constant."""
            import math
            e = int(math.floor(math.log10(v)))
            m = v / 10 ** e
            if v < 100:
                return ("%g" % v)
            pw = "10" + "".join(_SUP[c] for c in str(e))
            return pw if abs(m - 1) < 1e-9 else "%g \u00d7 %s" % (m, pw)

        _pr = sr["per_row"]
        _D_MICRO = 12.5                                  # µm, the microfluidic half-gap (Mo 2020 SI p. 13; D-independent)
        _kin = lambda r: _pr[r]["i_k0_mAcm2"]["micro"] * _D_MICRO / _pr[r]["xk_um"]
        _NIXEC = "Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)"
        _COH = "Co-H alkene reduction (e-HAT)"
        _AZA = "Co-catalyzed allylic C-H amination"
        # SPLIT 2026-10-03: the author moved the Figure 6 caption between these two sentences, so the
        # passage is no longer one contiguous run of text.  Two pins, not one -- the second still
        # carries every number, so the numeric check is unchanged.
        # chemistry audit, 2026-10-05: the Co(salen) allylic C-H amination left the sourced set (no catalyst is regenerated at
        # room temperature and it turns over by a heat-driven homolysis, Cai/Xu Nat Commun 2021 p. 6-7). At k = 0 it could only
        # be drawn as its transport floor, a straight 1/delta line (author: "looks sus"), and no measured constant exists for
        # the Ni(tet a) cyclization either (Ozaki/Matsushita/Ohmori Perkin Trans 1 1993, 649 and Olivero/Rolland/Dunach
        # Organometallics 1998, 17, 3747 were read for one), so the third row of (h) is the Ni aryl-aryl homocoupling, carried
        # at the cross-coupling's nickel constant. Every claim the sentences below make about it is asserted here.
        _HOMO = "Cathodic Ni aryl-aryl homocoupling"
        if _AZA in _pr:
            raise SystemExit("the allylic C-H amination is carried at a sourced k again; Figure 6h no longer draws it")
        if _HOMO not in _pr or _pr[_HOMO]["k_M"] != _pr[_NIXEC]["k_M"]:
            raise SystemExit("the Figure 6h sentences say the homocoupling is carried at the cross-coupling's nickel constant")
        P["catalyst_finite_k"] = ("Using literature-anchored rate constants (SI §S5.7), Figure 6h shows three catalysts that move across "
                                  "limiting regimes as δ decreases.")
        _h3 = (_NIXEC, _COH, _HOMO)
        if not all(_pr[r]["xk_um"] < 8.0 for r in _h3):          # 8 um: below the thinnest archetype film of any row
            raise SystemExit("a Figure 6h row has x_k above the thinnest film; the sentence says x_k < delta in every architecture")
        P["catalyst_finite_k2"] = ("The nickel-catalyzed cross-electrophile coupling "
                                   "(k = %s M⁻¹ s⁻¹, x_k = %.1f µm), the cobalt-hydride alkene reduction (k = %s M⁻¹ s⁻¹, "
                                   "x_k = %.1f µm) and the nickel-catalyzed aryl–aryl homocoupling (k = %s M⁻¹ s⁻¹, x_k = %.1f µm) "
                                   "possess x_k smaller than δ in every architecture."
                                   % (_kfmt_k(_pr[_NIXEC]["k_M"]), _pr[_NIXEC]["xk_um"],
                                      _kfmt_k(_pr[_COH]["k_M"]), _pr[_COH]["xk_um"],
                                      _kfmt_k(_pr[_HOMO]["k_M"]), _pr[_HOMO]["xk_um"]))
        _rce = {r: _pr[r]["i_mAcm2"]["rce"] for r in (_NIXEC, _COH, _HOMO)}
        if any(not 0.8 < _rce[r] / _kin(r) < 1.15 for r in _rce):
            raise SystemExit("the sentence says the three level off near their kinetic plateaus; rotating-cylinder/plateau = %r"
                             % {r: round(_rce[r] / _kin(r), 3) for r in _rce})
        P["catalyst_kinetic_ceilings"] = ("as δ decreases they level off near their kinetic plateaus of %.0f, %.0f and %.0f mA cm⁻², like "
                                          "ACT, so their ceilings rise only %.1f-, %.1f- and %.1f-fold."
                                          % (_kin(_NIXEC), _kin(_COH), _kin(_HOMO),
                                             _pr[_NIXEC]["gain_unstirred_to_rce"], _pr[_COH]["gain_unstirred_to_rce"],
                                             _pr[_HOMO]["gain_unstirred_to_rce"]))
        # the homocoupling sentence: why it sits highest, and that it alone clears 25 mA cm-2 -- each word asserted
        _r50 = pd.read_csv(os.path.join(HERE, "reactions_50.csv")).set_index("reaction")
        _cr_ = _r50.loc[_HOMO, "C_carrier_M"] / _r50.loc[_NIXEC, "C_carrier_M"]
        if not 1.9 < _cr_ < 2.1:
            raise SystemExit("the homocoupling sentence says twice the catalyst; the loadings give %.2f" % _cr_)
        if (_r50.loc[_HOMO, "n_carrier"], _r50.loc[_NIXEC, "n_carrier"]) != (2.0, 1.0):
            raise SystemExit("the homocoupling sentence says two electrons per catalyst against one")
        if not _r50.loc[_HOMO, "mu_mPas"] < min(_r50.loc[_NIXEC, "mu_mPas"], 0.927):   # 0.927: DMA's homolog reading (Table S7)
            raise SystemExit("the homocoupling sentence says a less viscous solvent")
        if not _kin(_HOMO) > max(_kin(_NIXEC), _kin(_COH)):
            raise SystemExit("the homocoupling sentence says its kinetic ceiling is the highest of the three")
        _hi = _pr[_HOMO]["i_mAcm2"]
        _clear = [a for a in ARCH if _hi[a] >= 25]
        _above = [r for r in _pr if max(_pr[r]["i_mAcm2"].values()) >= 25]
        _cmax = MM.class_matrix("catalyst")[ARCH].max(axis=1)
        if _above != [_HOMO] or int((_cmax >= 25).sum()) != 1 or _clear != ARCH[ARCH.index(_clear[0]):] or _clear[0] != "flow":
            raise SystemExit("the homocoupling sentence says it alone clears 25 mA cm-2, in every architecture from the "
                             "recirculating flow cell on; the model gives %r (rows above 25: %r)" % (_clear, _above))
        # chemistry review 2026-10-06: Courtois 1997 Scheme 1 adds the first aryl bromide to Ni(0)(bpy) and the second
        # to the aryl-Ni(I) it forms, so "adds the aryl bromide to Ni(0)" was half the cycle; and 10^2 is taken from
        # rates measured on Ni(I) complexes (Table S11), not measured itself
        _HZ = json.load(open(os.path.join(ROOT, "results", "homocoupling_charge_sensitivity.json"), encoding="utf-8"))
        if _HZ["clears25_from"]["0"] != "flow":
            raise SystemExit("the homocoupling sentence says it clears 25 from the recirculating flow cell on; at z = 0 it clears from %s"
                             % _HZ["clears25_from"]["0"])
        _homoz_where = ("in every architecture" if _HZ["clears25_every_arch"]["2"] else
                        "from the %s on" % {"natural": "unstirred cell", "stirred": "stirred cell", "flow": "recirculating flow cell",
                                            "anec": "ANEC cell", "micro": "microfluidic cell", "rde": "RDE", "rce": "rotating cylinder"}[_HZ["clears25_from"]["2"]])
        P["catalyst_homo"] = ("The homocoupling shares the cross-coupling’s rate constant, taken from rates measured on Ni(I) "
                              "complexes, although its exemplar adds one aryl bromide to Ni(0) and the second to an aryl–Ni(I) "
                              "intermediate (SI Table S11). It carries twice the catalyst, at "
                              "two electrons per catalyst and in a less viscous solvent, so its kinetic ceiling is the highest of the "
                              "three, and it is the only catalyst-carried reaction to clear 25 mA cm⁻², in every architecture from "
                              "the recirculating flow cell on, at the neutral charge of its precursor; written as the dication its "
                              "exemplar reduces, it clears 25 mA cm⁻² %s (SI Table S2)." % _homoz_where)
        P["catalyst_homo_values"] = [_kin(_HOMO), _pr[_HOMO]["gain_unstirred_to_rce"]]
        # 2026-10-07 (author: restore the pedagogy): the cause and the consequence only. The borrowed-constant clause is
        # covered by the provenance sentence ("in most cases for a related substrate or catalyst", Table S11), and the
        # charge sensitivity stays in SI Table S7d; "from the recirculating flow cell on" is dropped because it depends on
        # that charge, while "the only catalyst-carried reaction to clear 25" holds at every charge swept.
        if any(r != _HOMO and max(_pr[r]["i_mAcm2"].values()) >= 25 for r in _pr) or not _HZ["clears25_from"]["2"]:
            raise SystemExit("the short homocoupling sentence says it alone clears 25 mA cm-2 at any charge swept")
        if _pr[_HOMO]["k_M"] != _pr[_NIXEC]["k_M"]:
            raise SystemExit("the homocoupling sentence says it shares the cross-coupling's rate constant")
        P["catalyst_homo_short"] = ("The homocoupling’s kinetic ceiling is the highest of the three. Against the cross-coupling, "
                                    "whose rate constant it shares, it carries twice the catalyst, at two electrons per catalyst "
                                    "and in a less viscous solvent. It is also the only catalyst-carried reaction to clear "
                                    "25 mA cm⁻².")
        # The author (2026-10-02) asked for ONE high-level provenance sentence at the END of the carrier
        # analysis, covering all six rate constants Section 4 prints (three mediated in the (d-f) passage,
        # three catalyst here).  NOT ONE of the six is a rate constant its own electrosynthesis reports:
        # Hofmann 10^3 is an aqueous analogy from the water-treatment literature, ACT 20 and HMF from de Nooy's
        # alkaline oxoammonium kinetics, NHPI 0.5 from Koshino's PINO HAT on toluenes in AcOH, the Ni rows from
        # Ting/Kawamata/Till on other ligands and media, Co-H from Boucher's Co(salen)+styrene in DMF, and the
        # aza-Wacker from a bound READ OFF its own paper's voltammogram at room temperature (the paper prints
        # no rate constant).  Dossier: docs/CATALYST_RATE_CONSTANTS_20260911.md; brackets in SI S5.5 / S5.7.
        # The author asked for this as TWO sentences (2026-10-02).  It claims only what was verified
        # against the fifteen k values: not one of the six is a rate constant the electrosynthesis
        # that sets its row's conditions reports.
        # The author asked for this as TWO sentences and for "uncertainty" rather than "bracket"
        # as a noun, with the sensitivity analysis named (2026-10-02).  Every clause is checked
        # against the SI's own words: S5.5 "perturbing each rate constant by a factor of ten in
        # either direction ... the >=25 count of any single architecture moves by at most +/-1 ...
        # and no architecture ordering changes"; S5.7 "All eleven rows are also re-solved over a
        # declared band k in {0, 1, 10, 100, 10^3, 10^4} ... which brackets every adopted value".
        # The SI uses neither "tenfold" nor "sensitivity analysis", so neither is quoted at it.
        # chemistry audit, 2026-10-05 (finding 4): the earlier sentence called all six constants measured literature
        # values for the elementary step, which Table S11 contradicts (Hofmann has none; ACT is a turnover frequency;
        # Co-H a voltammetric simulation). It now says what each rests on, read from data/rate_constant_basis.csv.
        _kb = {r["reaction"]: r for r in csv.DictReader(open(os.path.join(HERE, "rate_constant_basis.csv"), encoding="utf-8"))}
        _used = ["Br- oxidation / electrophilic bromination", "ACT-mediated alcohol oxidation (flow, hectogram)", "NHPI-mediated allylic C-H -> enone", _NIXEC, _COH]
        _rel = [_kb[r]["relation"] for r in _used]
        if _rel != ["same carrier and substrate", "same carrier, other substrates", "analogue of the carrier", "analogue of the carrier", "analogue of the carrier"]:
            raise SystemExit("the k-provenance sentence describes the five constants Section 4 uses differently from the record: %r" % _rel)
        # 2026-10-07 (author): the count is the constants Section 4 PRINTS -- six, the homocoupling's included -- while the
        # sources named are five, because the homocoupling borrows the cross-coupling's constant (asserted here)
        _kprinted = _used + [_HOMO]
        if float(_kb[_HOMO]["k_M1s1"]) != float(_kb[_NIXEC]["k_M1s1"]):
            raise SystemExit("the k-provenance sentence counts the homocoupling under the nickel source; its k no longer equals the cross-coupling's")
        P["k_provenance"] = (
            "None of the %s rate constants in this section is reported by the electrosynthesis that sets its row\u2019s bulk "
            "concentrations and architecture. The bromination value was measured for bromine with anisole itself, in water; "
            "two were measured for an analogue of the step (the PINO radical with cyclohexene, and Ni(I) bipyridine complexes "
            "with aryl bromides), the cobalt-hydride value was estimated by simulating cyclic voltammograms of a cobalt hydride "
            "with a styrene, and the ACT value is read from the mediator\u2019s turnover frequencies with other alcohols "
            "(SI Table S11)." % _NW[len(_kprinted)])
        # 2026-10-07: the author's own framing ("We note that the six rate constants ... come from literature sources that differ
        # from the source that reports the reaction conditions"), scoped to the constants QUOTED here (the model carries more,
        # three of them bounded by their own exemplars' data, Table S11) and to what the record says of each: all six from a
        # separate kinetic study, all but the bromination for a related substrate or catalyst rather than the row's own pair.
        _same = [r for r in _kprinted if _kb[r]["relation"] == "same carrier and substrate"]
        if _same != ["Br- oxidation / electrophilic bromination"] or any("exemplar" in _kb[r]["relation"] for r in _kprinted):
            raise SystemExit("the provenance sentence says each quoted constant comes from a separate kinetic study, in most cases for "
                             "a related substrate or catalyst; the record gives %r" % [_kb[r]["relation"] for r in _kprinted])
        P["k_provenance_short"] = ("We note that each of the %s rate constants quoted in this section comes from a kinetic study "
                                   "separate from the electrosynthesis that supplies its simulation’s concentrations, solvent and electrolyte, "
                                   "in most cases for a related substrate or catalyst (SI Table S11)." % _NW[len(_kprinted)])
        # chemistry audit pass 3 (2026-10-06): the sentence said "at the upper bound of the measured NICKEL rate constants ...
        # 4 of the 12 would clear 25 ..., and those would then be limited by substrate supply at 0.03-0.3 M". The 4 counts all
        # four sourced rows (nickel AND cobalt hydride) at the top of the band; no clearing cell sits at its substrate cap
        # (catalyst_ec_sensitivity.json, at_substrate_cap); and 0.03-0.3 M is the substrate range of all twelve rows.
        _bands = sorted({tuple(r["band_M"]) for r in sr["per_row"].values()})
        if len(_bands) != 1:
            raise SystemExit("the sourced catalyst rows no longer share one band: %r" % _bands)
        _bhi = _bands[0][1]
        _be = int(round(float(np.log10(_bhi))))
        if abs(_bhi - 10 ** _be) > 1e-9 * _bhi:
            raise SystemExit("the band top %g is not a power of ten" % _bhi)
        _sup = "⁰¹²³⁴⁵⁶⁷⁸⁹"
        P["catalyst_gain"] = ("Even with the %s literature-anchored rate constants raised to the top of the band we test (10%s M⁻¹ s⁻¹), "
                              "only %s of the %s would clear 25 mA cm⁻²."
                              % (_NW[sr["n_sourced"]], "".join(_sup[int(c)] for c in str(_be)), _hi_edge_n, P["cat_n"]))
        P["catalyst_gain_tail"] = "only %s of the %s would clear 25 mA cm⁻²." % (_hi_edge_n, P["cat_n"])
        # the author's wording (v113): both catalyst pins now land in one Section 4 sentence
        # 2026-10-05: the catalyst-span sentence now reads "...; 11 of the 12 still remain below 25", so the pin carries "still"
        P["catalyst_conclusion"] = ("%s of the %s still remain below 25 mA cm⁻²" % (P["cat_below25"], P["cat_n"]))
        # ---- v118: ONE mechanism at two loadings (Connor Coley, comment 21 on v35: "the distinction between EC
        # mediated and molecular catalyst is (almost) only the substrate concentration at the surface"). Both classes
        # are solved by the same EC' solver at their cited k; what the 50-reaction set keeps apart is carrier loading.
        _rx50 = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
        _cc = _rx50.merge(mat[["reaction", "carrier"]], on="reaction", how="left")
        _mC = _cc[_cc.carrier == "mediator"]["C_carrier_M"]
        _cC = _cc[_cc.carrier == "catalyst"]["C_carrier_M"]
        _load = float(_mC.median() / _cC.median())
        _gaps = [float(mat[mat.carrier == "mediator"][a].median() / MM.class_matrix("catalyst")[a].median()) for a in ARCH]
        # one mediated row is carried by dissolved oxygen at a fraction of a millimolar; the range the sentence
        # gives for "the mediators" is over the others, and that row is named beside it
        _lowmed = _cc[(_cc.carrier == "mediator") & (_cc.C_carrier_M < 1e-3)]
        if list(_lowmed.reaction) != ["Cathodic Giese (R-I + alkene)"]:
            raise SystemExit("the sub-millimolar mediated rows are %r; the loading sentence names the oxygen-carried one only" % list(_lowmed.reaction))
        _mC_main = _mC[_mC >= 1e-3]
        # JR28 (2026-09-29): U+2032 PRIME, not U+2019. The prime IS the mechanism (catalytic
        # regeneration); the SI writes it that way in all 29 of its occurrences, and the manuscript
        # carried a curly apostrophe here until JR28 -- including in this template's own output.
        # chemistry audit, 2026-10-05 (finding 14): "mechanistically identical" is too strong for paired and multi-step
        # inner-sphere cycles; the claim the model supports is that both are treated with the same formalism
        P["carrier_same_mechanism"] = ("A molecular catalyst whose cycle closes at one electrode behaves like a mediator: the "
                                       "electrode activates the carrier, the carrier reacts with the substrate in solution, and "
                                       "both are treated here with the same EC\u2032 formalism, with the catalyst in place of the "
                                       "mediator and")
        # the author's wording (v129): he writes the median loading ratio as "order-of-magnitude" rather than
        # printing it, so the template ASSERTS that description against the model instead of carrying a number
        # the manuscript no longer has -- a qualitative claim is as gateable as a quantitative one when it names
        # a magnitude. 3.2x to 32x is what rounds to one decade in log10; the set gives 12x.
        # Chemistry audit, pass 5: the sentence said this loading difference "sets" the ceiling gap. It does not: at the
        # median the loading is about sixfold, the catalysts' slower diffusion adds about threefold, and the in-film
        # turnover credited to the mediated rows widens the k = 0 gap further in the thick films. Each factor is read from
        # the table or the two matrices and asserted, over the same class rows the gap is taken across (chains excluded).
        _catR = set(MM.class_matrix("catalyst").reaction)
        _cK = _cc[_cc.reaction.isin(_catR)]
        _mK = _cc[_cc.carrier == "mediator"]
        _loadK = float(_mK.C_carrier_M.median() / _cK.C_carrier_M.median())
        _dK = float(_mK.D_cm2s.median() / _cK.D_cm2s.median())
        _np = pd.read_csv(os.path.join(ROOT, "julia", "all50_np_matrix.csv"))
        _rN = {"natural": "Unstirred batch", "stirred": "Stirred batch", "flow": "Recirculating flow cell", "anec": "ANEC flow cell",
               "micro": "Microfluidic cell (25 um gap)", "rde": "RDE 1600 rpm", "rce": "Rotating cylinder 3000 rpm"}
        _k0 = []
        for a in ARCH:
            _s = _np[_np.reactor == _rN[a]]
            _k0.append(float(_s[_s.reaction.isin(_mK.reaction)].i_np_mAcm2.median() / _s[_s.reaction.isin(_catR)].i_np_mAcm2.median()))
        assert _loadK > 1 and _dK > 1, "the catalysts are no longer both more dilute and slower-diffusing than the mediators"
        assert min(_k0) > _loadK, "the k = 0 gap no longer exceeds the loading ratio; the diffusion clause is wrong"
        assert all(g >= k - 1e-9 for g, k in zip(_gaps, _k0)), "in-film turnover no longer widens the gap in every architecture"
        assert float(_mK.n_carrier.median()) == float(_cK.n_carrier.median()), "the class electron counts now differ; say so"
        P["carrier_loading"] = ("The key differentiator between the molecular catalysts and the mediators is that the "
            "molecular catalysts are much more dilute in concentration. Catalysts are loaded at %.1f to %.0f mM, as opposed to "
                                "%.0f mM to %.1f M for the mediators (apart from dissolved oxygen, which mediates one reaction at "
                                "%.2f mM), a %.0f-fold difference at the median. Together with the catalysts' slower diffusion "
                                "(%.0f-fold at the median), that dilution puts the catalyst class rate ceilings %d- to %d-fold "
                                "below the mediators' when no in-film turnover is credited, and the turnover credited to the "
                                "mediated rows widens the gap to %d- to %d-fold, most in the thickest films."
                                % (_cC.min() * 1000, _cC.max() * 1000, _mC_main.min() * 1000, _mC_main.max(),
                                   float(_lowmed.C_carrier_M.iloc[0]) * 1000, round(_loadK), round(_dK),
                                   round(min(_k0)), round(max(_k0)), round(min(_gaps)), round(max(_gaps))))
        P["carrier_loading_values"] = [_cC.min() * 1000, _cC.max() * 1000, _mC_main.min() * 1000, _mC_main.max(),
                                       float(_lowmed.C_carrier_M.iloc[0]) * 1000, round(_loadK), round(_dK),
                                       round(min(_k0)), round(max(_k0)), round(min(_gaps)), round(max(_gaps))]
        P["carrier_loading_ratio"] = _load
        # 2026-10-07 (author: restore the pedagogy of the pre-audit text): ONE sentence for the reader -- the catalysts are
        # more dilute and slower-diffusing, so their class sits more than a decade below the mediators' everywhere. The
        # decomposition the audit added (loading, diffusion, the k = 0 gap, the turnover gap) is asserted above and left
        # out of the manuscript; each clause of the short form is asserted here.
        if round(_loadK) not in range(2, 11) or min(_gaps) < 10:
            raise SystemExit("the loading sentence says a median several-fold lower and ceilings more than a decade below in every "
                             "architecture; loading ratio %.1f, class gaps %s" % (_loadK, [round(g, 1) for g in _gaps]))
        P["carrier_loading_short"] = ("The key differentiator between the molecular catalysts and the mediators is that the "
                                      "molecular catalysts are much more dilute in concentration. Catalysts are loaded in a typical range of %.1f to "
                                      "%.0f mM, with a median about %s times below that of the mediators, and they also diffuse "
                                      "more slowly, so the catalyst-carried ceilings sit more than an order of magnitude below the "
                                      "mediated ones in every architecture."
                                      % (_cC.min() * 1000, _cC.max() * 1000, _NW[int(round(_loadK))]))
        P["carrier_loading_short_values"] = [_cC.min() * 1000, _cC.max() * 1000]
        # v119 (author: "address all of these"): the two ranges OVERLAP at their edges, so the labels mark a difference
        # in typical loading, never a boundary. The overlapping rows are read from the table, not named by hand.
        _disp = {"ACT-mediated alcohol oxidation (flow, hectogram)": "ACT alcohol oxidation",
                 "BQ-mediated Wacker-Tsuji oxidation": "benzoquinone-mediated Wacker–Tsuji oxidation"}
        # (the overlap sentence left the manuscript in v129; its two named rows are kept for the retired-quantity probe)
        _ov = _cc[_cc.reaction.isin(list(_disp))].sort_values("C_carrier_M", ascending=False)
        assert len(_ov) == 2, "the two rows the retired overlap sentence named are no longer in the table"
        P["carrier_overlap"] = ("The ranges overlap at their edges: the %s (%.0f mM) and the %s (%.0f mM) sit inside the "
                                "catalyst range, so the two labels mark a difference in typical loading rather than a "
                                "sharp boundary."
                                % (_disp[_ov.reaction.iloc[0]], _ov.C_carrier_M.iloc[0] * 1000,
                                   _disp[_ov.reaction.iloc[1]], _ov.C_carrier_M.iloc[1] * 1000))
        P["carrier_overlap_values"] = [float(v) * 1000 for v in _ov.C_carrier_M]
        P["carrier_overlap_n"] = len(_ov)
        # v120 (Connor's comment 48; author: "we don't show directly, but we show that we need really thin transport
        # distances, which could only conceivably be achieved in a porous electrode"). The model has no porous electrode,
        # so the sentence claims only what it computes: the thinnest planar films and what still falls short there.
        _thin = [dmed[k] for k in ("micro", "rde", "rce")]
        _short = 50 - max(n25[k] for k in ("micro", "rde", "rce"))
        P["porous_need"] = ("The transport simulations above do not model porous electrodes directly, but they show that "
                            "commercially relevant rates for commodity chemicals require transport distances shorter than "
                            # 2026-10-04: the author split the sentence at the colon and the document carries a
                            # GREEK mu and the NFKC-normalised superscript, so the pin matches his characters.
                            "any planar architecture provides. Even at the thinnest planar films modeled (median δ ≈ %.0f–%.0f μm), "
                            "%d of the 50 reactions remain below 25 mA cm−2, and shorter distances could only conceivably "
                            "be reached in porous electrode architectures that mediate multiphase transport."
                            % (min(_thin), max(_thin), _short))
        P["porous_need_values"] = [min(_thin), max(_thin), _short, 50, 25]
        # Fig. 6 caption (a-c): the two homogeneous cells draw one cycle, and (c) draws its own loading
        # the author's wording (v129): he says WHY the two cells differ rather than only that they do
        P["fig6ac_loading"] = (" The mediated and catalyst cells draw the same cycle, with the only difference between "
                               "them being that the homogeneous catalysts are generally much more dilute, so (c) is "
                               "drawn at the lower carrier loading of the molecular-catalyst rows.")
        # Fig. 6h: the three rows drawn, their gains at the sourced k and at the floor
        _h = {"Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)": "nickel", "Co-H alkene reduction (e-HAT)": "cobalt-hydride",
              "Cathodic Ni aryl-aryl homocoupling": "nickel homocoupling"}
        P["fig6h_gains"] = ("gain from the unstirred to the rotating-cylinder film, " +
                            "; ".join("%s ×%.1f against ×%.0f at k = 0" % (_h[r], sr["per_row"][r]["gain_unstirred_to_rce"], sr["per_row"][r]["gain_at_k0"]) for r in _h))
        # Section 8 restates the class medians at the two ends of the architecture ladder
        # the author's wording (v113): he states the gain and carries _cr to one decimal, which is a
        # digit more than the retired template printed; both agree with the matrix (0.8042, 5.2673)
        P["ec_rate_source"] = ("are solved with a reaction–diffusion model at a rate constant set row by row from a measurement "
                               "on the same or an analogous step, a bound from the exemplar\u2019s own data, or a declared value, and "
                               "at k = 0 where none of these exists (SI Table S11)")
        P["catalyst_sec8_medians"] = ("the median ceiling of catalyst-carried reactions rises "
                                      "%d-fold, from %.1f to %.1f mA cm⁻²" % (round(_cr / _cn), _cn, _cr))
        P["fig6h_gain_values"] = [sr["per_row"][r]["gain_unstirred_to_rce"] for r in _h]
    # ---- Fig. 6g: three mediated rows at their cited k across the archetype films (julia/mediated_ec_matrix.csv
    # for the unstirred -> rotating-cylinder gain, the same convention as (h); julia/run_mediated_delta.jl draws the curve)
    _mm = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"))
    _g3 = [("ACT-mediated alcohol oxidation (flow, hectogram)", "ACT alcohol oxidation", "kinetic"),
           ("NHPI-mediated allylic C-H -> enone", "NHPI allylic C–H oxidation", "mixed"),
           ("Br- oxidation / electrophilic bromination", "bromide-mediated bromination of anisole", "substrate-limited")]
    _gg = {}
    for _r, _nm, _reg in _g3:
        _u = float(_mm[(_mm.reaction == _r) & (_mm.reactor == "Unstirred batch")].i_ec_mAcm2.iloc[0])
        _c = float(_mm[(_mm.reaction == _r) & (_mm.reactor == "Rotating cylinder 3000 rpm")].i_ec_mAcm2.iloc[0])
        _gg[_r] = (_nm, _reg, _u, _c)
    P["fig6g_gain_values"] = [v[3] / v[2] for v in _gg.values()]
    P["fig6g_gains"] = ("gain from the unstirred to the rotating-cylinder film, " +
                        "; ".join("%s ×%.1f" % (v[0], v[3] / v[2]) for v in _gg.values()))
    # ---- Fig. 6d-f (v90): the three rows of (g) at their cited k on the ANEC film (36.2 um, measured), profiles at the
    # c-control plateau (julia/mediated_ec_profiles.csv). The regime word is the one the SOLVE assigns (regime_solved: substrate
    # exhausted at the wall / most of the activated mediator escaping / neither); G-ECPANEL requires it to agree with the analytic
    # assignment and to survive +/-25 % on both diffusivities. Panel order (d) substrate-limited, (e) kinetic, (f) mixed control
    # (2026-10-05: the NHPI row at the rate constant measured for PINO and an allylic C-H, 20.2 M-1 s-1; it was mediator-limited at 0.5).
    _rg = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_profiles.csv"))
    _order = ["Bromination", "ACT", "NHPI"]
    _first = {s: _rg[_rg["short"] == s].iloc[0] for s in _order}
    _expect = ["substrate-limited", "kinetic", "mixed"]
    P["fig6_regime_rows"] = _order
    P["fig6_regime_regimes"] = [str(_first[s].regime_solved) for s in _order]
    if P["fig6_regime_regimes"] != _expect:
        raise SystemExit("Fig. 6d-f: the solve names the regimes %r where the panel order expects %r -- re-read the panels"
                         % (P["fig6_regime_regimes"], _expect))
    P["fig6_regime_ks"] = [float(_first[s].k_M) for s in _order]
    P["fig6_regime_ilim"] = [float(_first[s].ilim_mAcm2) for s in _order]
    P["fig6_regime_share"] = [float(_first[s].share_in_film) for s in _order]
    P["fig6_regime_delta_um"] = float(_first["ACT"].delta_um)
    _sup = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
    def _kfmt(k):                                   # a decade prints as a power of ten; above 100 three figures times one; else itself
        e = np.log10(k)
        if k >= 100 and abs(e - round(e)) < 1e-9:
            return "10" + ("%d" % round(e)).translate(_sup)
        if k >= 1000:
            ee = int(np.floor(e)); return "%s × 10%s" % (("%.3g" % (k / 10 ** ee)), ("%d" % ee).translate(_sup))
        return "%g" % k
    _f3 = lambda v: ("%.0f" % v) if v >= 100 else ("%.1f" % v)          # three significant figures at these magnitudes
    P["fig6_regime_ilim_text"] = ", ".join(_f3(v) for v in P["fig6_regime_ilim"])
    P["fig6_regime_share_text"] = ", ".join("%.0f %%" % (100 * v) for v in P["fig6_regime_share"])
    _how = {"substrate-limited": "the substrate is exhausted at a front inside the film",
            "kinetic": "the activated mediator is consumed within x_k of the electrode",
            "mixed": "about half of the activated mediator reacts inside the film and the rest leaves it",
            "mediator-limited": "most of the activated mediator leaves the film unreacted"}
    _rword = {"substrate-limited": "substrate-limited", "kinetic": "kinetic", "mixed": "mixed control", "mediator-limited": "mediator-limited"}
    P["fig6_regime_sentence"] = ("(d–f) Concentration profiles at the limiting current for three of the mediated rows at their cited rate "
                                 "constants on the ANEC film (δ = %.0f µm, their cells in Table S5): the bromide-mediated bromination of anisole "
                                 "(k = %s M⁻¹ s⁻¹, substrate-limited: %s), ACT alcohol oxidation (k = %s, kinetic: %s) and NHPI allylic C–H "
                                 "oxidation (k = %s, mixed control: %s), i_lim = %s mA cm⁻²; the grey curve is the local reaction rate per unit "
                                 "of ln x, k c_ox c_S x/(s_ox i/F), whose area is the share of the activated mediator consumed inside the "
                                 "film: %s."
                                 % (P["fig6_regime_delta_um"], _kfmt(P["fig6_regime_ks"][0]), _how["substrate-limited"],
                                    _kfmt(P["fig6_regime_ks"][1]), _how["kinetic"], _kfmt(P["fig6_regime_ks"][2]), _how["mixed"],
                                    P["fig6_regime_ilim_text"], P["fig6_regime_share_text"]))
    # (g) follows (d-f) in the caption, so it names the rows once more only by their behaviour across the films
    P["fig6g_sentence"] = ("(g) The same three rows against the diffusion-layer thickness across the archetype films: ACT alcohol oxidation "
                           "stays at %.0f to %.0f mA cm⁻² because its reaction layer is thinner than every film, NHPI allylic C–H oxidation "
                           "follows its own transport bound in the thin films and levels off at a kinetic plateau in the thick ones, and the bromide-mediated bromination of anisole sits above its planar substrate cap "
                           "on a detached front; %s."
                           % (_gg[_g3[0][0]][2], _gg[_g3[0][0]][3], P["fig6g_gains"]))
    # ---- Section 4 body (v92, author: "propagate the analysis in each panel into section 4"): the (d-f) and (g) analyses as
    # prose, every number read from the same artifacts as the caption (the profile solve, the film sweep, the published matrix) ----
    _W = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    _cox_max = float(_rg[_rg["short"] == "Bromination"].c_ox_norm.max())
    _dd = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_delta.csv"))
    _d_un = float(_mm[_mm.reactor == "Unstirred batch"].delta_um.iloc[0])
    _act_un = _dd[(_dd.reaction == _g3[0][0]) & (np.isclose(_dd.delta_um, _d_un))]
    if len(_act_un) != 1:
        raise SystemExit("mediated_ec_delta.csv carries no ACT solve at the unstirred film (%.1f um)" % _d_un)
    P["act_amp_unstirred"] = float(_act_un.i_ec_mAcm2.iloc[0] / _act_un.i_k0_mAcm2.iloc[0])
    if min(_order, key=lambda s: float(_first[s].D_red)) != "ACT":
        raise SystemExit("the Section 4 sentence calls ACT the slowest-diffusing carrier of the three; the artifact says otherwise")
    _gain = dict(zip([v[0] for v in _gg.values()], P["fig6g_gain_values"]))
    # Section 4 (g) names where the NHPI row sits on each side of x_k and calls ACT the lowest of the three everywhere:
    # both are claims about the matrix, asserted here so the sentence cannot outlive it.
    _nh = _mm[_mm.reaction == "NHPI-mediated allylic C-H -> enone"].set_index("reactor")
    _rt = _nh.delta_um / _nh.xk_um
    if not (all(_rt[r] >= 3.0 for r in ("Unstirred batch", "Stirred batch", "Recirculating flow cell")) and
            all(_rt[r] < 1.0 for r in ("Microfluidic cell (25 um gap)", "RDE 1600 rpm", "Rotating cylinder 3000 rpm"))):
        raise SystemExit("Section 4 (g): the NHPI row is not several x_k thick in the batch and recirculating cells and thinner "
                         "than x_k in the microfluidic and rotating cells: delta/x_k = %s" % dict(_rt.round(2)))
    for _rr in _mm.reactor.unique():
        _v = {full: float(_mm[(_mm.reaction == full) & (_mm.reactor == _rr)].i_ec_mAcm2.iloc[0]) for full, _nm, _rg0 in _g3}
        if min(_v, key=_v.get) != _g3[0][0]:
            raise SystemExit("Section 4 (g) says ACT has the lowest ceiling of the three in every architecture; in %s it does not: %s" % (_rr, _v))
    P["sec4_fig6df"] = ("Comparing x_k with δ (illustratively in the ANEC cell, δ = %.0f µm) then identifies what limits the "
                        "current. "   # the author's wording, 2026-10-02; 2026-10-07: "when the substrate itself is not exhausted" dropped -- the first example is the exhausted one
                        "In the bromide-mediated bromination of anisole "
                        # 2026-10-07 (author: restore the pedagogy of his pre-audit text): each regime is NAMED in the
                        # sentence that shows it, as the panel titles name it; the Br2 multiple is left to SI S5.2, where
                        # its caveat (no Br3- speciation, no Br2 solubility ceiling) sits beside it
                        "(k = %s M⁻¹ s⁻¹, x_k = %.1f µm, Figure 6d), the reaction layer is much smaller than δ, and the reaction is so fast "
                        "that the anisole is exhausted at a front inside the diffusion layer: the reaction is substrate-limited. Bromine therefore "
                        "accumulates behind the front, where no anisole remains to consume it, and the ceiling of %s mA cm⁻² is set "
                        "by the transport of the bromide itself: anisole at %.0f mM can regenerate little of the %.0f mM bromide, so "
                        "regeneration lifts the ceiling only %.0f%% above its value with no reaction. "
                        "Conversely, in ACT alcohol oxidation (k = %s M⁻¹ s⁻¹, "
                        "x_k = %.1f µm), the reaction layer is also smaller than δ, but the substrate stays at %.0f%% of its bulk "
                        "concentration, so the ceiling of %s mA cm⁻² is kinetically controlled and depends only weakly on δ (Figure 6g). "
                        "In NHPI allylic C–H oxidation (k = %s M⁻¹ s⁻¹, x_k = %.0f µm), the reaction layer is comparable to δ, a regime "
                        "of mixed control: about half "
                        "of the activated mediator (the N-oxyl radical) reacts inside the diffusion layer and the rest leaves it before it reacts, "
                        "so the ceiling of %s mA cm⁻² is only %.1f times the mediator's Fick bound, "
                        "nFD_medC_med/δ (Figure 6f)."
                        % (P["fig6_regime_delta_um"],
                           _kfmt(float(_first["Bromination"].k_M)), float(_first["Bromination"].xk_um),
                           _f3(float(_first["Bromination"].ilim_mAcm2)),
                           float(_first["Bromination"].C_S_molm3), float(_first["Bromination"].C_med_molm3),
                           100 * (float(_first["Bromination"].ilim_mAcm2) / float(_first["Bromination"].i_k0_mAcm2) - 1),
                           _kfmt(float(_first["ACT"].k_M)), float(_first["ACT"].xk_um),
                           100 * float(_first["ACT"].c_S_surf_norm), _f3(float(_first["ACT"].ilim_mAcm2)),
                           _kfmt(float(_first["NHPI"].k_M)), float(_first["NHPI"].xk_um), _f3(float(_first["NHPI"].ilim_mAcm2)),
                           float(_first["NHPI"].ilim_mAcm2) / float(_first["NHPI"].i_tier0_mAcm2)))
    # "about half" and "comparable to delta" are claims about the solve: hold them to it
    if not (0.4 <= float(_first["NHPI"].share_in_film) <= 0.6 and 0.5 <= float(_first["NHPI"].delta_um) / float(_first["NHPI"].xk_um) <= 2.0):
        raise SystemExit("Section 4 says about half of the activated NHPI mediator reacts inside a film comparable to x_k; the solve gives "
                         "share %.2f at delta/x_k %.2f" % (float(_first["NHPI"].share_in_film), float(_first["NHPI"].delta_um) / float(_first["NHPI"].xk_um)))
    # 2026-10-06: the (d) sentence says the anisole is exhausted at the wall, the bromide is depleted there (its own transport sets
    # the ceiling) and the reaction lifts the ceiling only a few percent; and (g) says the gain is nearly the full reduction in delta
    _b = _first["Bromination"]
    if not (float(_b.c_S_surf_norm) < 1e-3 and float(_b.c_red_surf_norm) < 1e-2 and float(_b.ilim_mAcm2) / float(_b.i_k0_mAcm2) - 1 < 0.10):
        raise SystemExit("Section 4 (d): the bromination row is not anisole-exhausted and bromide-transport-limited on the ANEC film: "
                         "c_S %.2e, c_red %.2e, i/i_k0 %.3f" % (float(_b.c_S_surf_norm), float(_b.c_red_surf_norm), float(_b.ilim_mAcm2) / float(_b.i_k0_mAcm2)))
    _bm = _mm[_mm.reaction == _g3[2][0]].set_index("reactor")
    _dratio = float(_bm.delta_um["Unstirred batch"] / _bm.delta_um["Rotating cylinder 3000 rpm"])
    if not (0.8 <= _gain["bromide-mediated bromination of anisole"] / _dratio <= 1.1):
        raise SystemExit("Section 4 (g): the bromination gain %.1f is not nearly the %.1f-fold reduction in delta" % (_gain["bromide-mediated bromination of anisole"], _dratio))
    _act_i = float(_act_un.i_ec_mAcm2.iloc[0])
    _act_k0 = float(_act_un.i_k0_mAcm2.iloc[0])
    P["sec4_fig6g"] = ("These regimes determine how each reaction responds to intensification (Figure 6g). From the unstirred cell "
                       "to the rotating cylinder, the bromination of anisole gains %.0f-fold, nearly the full reduction in δ, because "
                       "its current is the bromide's own transport in every architecture. NHPI gains %.1f-fold: in the batch and recirculating-flow cells, where δ is "
                       "several times x_k, it is held near its kinetic ceiling, but in the microfluidic and rotating cells, where δ is smaller "
                       "than x_k, the activated mediator escapes "
                       "before reacting and its current follows the mediator-limited rate, nFD_medC_med/δ. ACT gains only %.1f-fold, "
                       "because x_k is smaller than δ in every architecture and its current remains limited by kinetics. "
                       "ACT has the lowest ceiling of the three in every architecture, not because its "
                       "chemistry is weak but because it carries only %.0f mM of mediator in water, and its mediator is the "
                       "slowest-diffusing carrier of the three. The mediator nonetheless provides a large benefit. Because the "
                       "activated mediator reacts with the alcohol within %.1f µm of the electrode, ACT is regenerated there and "
                       "returns to the electrode over that short distance rather than diffusing in from the bulk across δ. In the "
                       "unstirred cell (δ = %.0f µm), this local regeneration raises the ceiling to %.1f mA cm⁻², %.0f times the "
                       "%.2f mA cm⁻² the mediator could carry by transport from the bulk alone."
                       % (_gain["bromide-mediated bromination of anisole"], _gain["NHPI allylic C–H oxidation"],
                          _gain["ACT alcohol oxidation"], float(_first["ACT"].C_med_molm3),
                          float(_first["ACT"].xk_um), _d_un, _act_i, P["act_amp_unstirred"], _act_k0))
    # the range is the unstirred -> rotating-cylinder gain over the eight mediated rows, derived here
    _medm = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv")).merge(
        pd.read_csv(os.path.join(HERE, "reactions_50.csv"))[["reaction", "carrier_type"]], on="reaction")
    _medg = (_medm[_medm.carrier_type == "mediator"].rce / _medm[_medm.carrier_type == "mediator"].natural)
    if len(_medg) != len(_sl):
        raise SystemExit("the reaction table holds %d mediated rows and the mediated matrix %d" % (len(_medg), len(_sl)))
    P["med_amp_lo"], P["med_amp_hi"] = "%.1f" % _medg.min(), "%.0f" % _medg.max()
    P["med_amp_values"] = [float(_medg.min()), float(_medg.max())]
    P["med_n_word"] = _NW[len(_medg)]
    P["mediated_range"] = ("Across all %s mediated reactions, intensification raises limiting currents by approximately "
                           "%s-fold to %s-fold" % (P["med_n_word"], P["med_amp_lo"], P["med_amp_hi"]))
    # 2026-10-07 (author: "you flooded them with numbers no one wants to read, it just needs to be a way of educating the
    # reader on what happens in each of the different limits"): the slope-by-slope catalogue (med_flat_sentence, kept above
    # for the record and for SI Table S6, which prints every slope) gives way to ONE causal sentence. Its two example
    # sets are claims about the model, asserted here: the kinetic examples respond only weakly and are never at their
    # substrate cap; the transport examples gain at least 90 % of their own film reduction and move by under 15 % when k
    # rises tenfold in every architecture (results/rate_constant_cells.csv), i.e. transport, not kinetics, holds them.
    _KIN_EX = ["ACT-mediated alcohol oxidation (flow, hectogram)"]   # pass 16: HMF has x_k > delta in the RDE and rotating cylinder
    _TR_EX = ["Br- oxidation / electrophilic bromination", "Cl-mediated ethylene epoxidation"]
    _mmi = _mm.set_index(["reaction", "reactor"])
    for _r in _KIN_EX:
        _gk = float(_medg[_medm[_medm.carrier_type == "mediator"].reaction == _r].iloc[0])
        if _gk > 2.5 or _r in _capped:
            raise SystemExit("the regime sentence calls %s a weakly responding kinetic row; gain %.2f, capped %s" % (_r, _gk, _r in _capped))
    for _r in _TR_EX:
        _g = _mm[_mm.reaction == _r].set_index("reactor")
        _dr = float(_g.delta_um["Unstirred batch"] / _g.delta_um["Rotating cylinder 3000 rpm"])
        _gt = float(_g.i_ec_mAcm2["Rotating cylinder 3000 rpm"] / _g.i_ec_mAcm2["Unstirred batch"])
        _kr = _kc[_kc.reaction == _r].pivot(index="reactor", columns="factor", values="i_ec_mAcm2")
        _up = float((_kr["mul10"] / _kr["base"] - 1).abs().max())
        if _gt / _dr < 0.9 or _up > 0.15:
            raise SystemExit("the regime sentence says %s is held by transport in every architecture and gains nearly the full "
                             "reduction in delta; gain/film ratio %.2f, largest tenfold-k movement %.2f" % (_r, _gt / _dr, _up))
    P["med_regime_sort"] = (P["mediated_range"] + ", and the regime decides where in that range each falls: reactions held "
                            "by kinetics, such as the ACT-mediated alcohol oxidation, respond only weakly, while those held by "
                            "transport in every architecture, such as the bromination and the chloride-mediated epoxidation, "
                            "gain nearly the full reduction in δ (SI Tables S5 and S6).")
    # ---- Fig. 6 caption, v93 (author: "its caption is WAYYY too long"): the panels named, the numbers moved to Section 4 and the SI ----
    _reg = {s: str(_first[s].regime_solved) for s in _order}
    # 2026-10-05 (author: "in the caption of the figure 6, it would be good to list the substrates"). The schemes
    # on the figure are generic (R groups; Jonas Rein redrew the NHPI one as cyclohexene), so the caption names the
    # substrate each curve is actually solved for, read from the two generated substrate tables.
    import csv as _csv2
    _ms = {r["reaction"]: r["substrate"] for r in _csv2.DictReader(open(os.path.join(HERE, "mediated_substrates.csv"), encoding="utf-8"))}
    _cs = {r["reaction"]: r["substrate"] for r in _csv2.DictReader(open(os.path.join(HERE, "catalyst_substrates.csv"), encoding="utf-8"))}
    _subs = [(_ms["Br- oxidation / electrophilic bromination"], "bromination"), (_ms["ACT-mediated alcohol oxidation (flow, hectogram)"], "ACT"),
             (_ms["NHPI-mediated allylic C-H -> enone"], "NHPI"), (_cs["Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)"], "Ni–XEC"),
             (_cs["Co-H alkene reduction (e-HAT)"], "Co–H"), (_cs["Cathodic Ni aryl-aryl homocoupling"], "Ni homocoupling")]
    P["fig6_substrate_names"] = [s for s, _t in _subs]
    P["fig6_substrates_long"] = ("The reaction schemes drawn beside the curves of (g) and (h) are generic; each curve is computed for the "
                                 "substrate its source reports: " + ", ".join("%s (%s)" % st for st in _subs[:-1]) +
                                 ", and %s (%s); SI Table S10 gives each balanced reaction." % _subs[-1])
    # 2026-10-07: the six names move to SI Table S10, which prints each balanced reaction; the bromination scheme is the
    # only one drawn on its own substrate (anisole), so the caption says so rather than calling all six generic
    if _subs[0][0].lower() != "anisole":
        raise SystemExit("the caption says the bromination scheme draws its own substrate, anisole; the table gives %r" % _subs[0][0])
    P["fig6_substrates"] = ("Except for the bromination, the reaction schemes drawn beside the curves of (g) and (h) are generic; "
                            "each curve is computed for its exemplar’s own substrate (SI Table S10).")
    P["fig6_caption_body"] = ("(a–c) The three current carriers in one boundary-layer idiom (schematic): substrate in and product out, the carrier "
                              "cycle between the electrode and the reaction site, and each cell's concentration profiles (substrate dotted, "
                              "activated carrier solid, resting carrier dashed); x_k marks the reaction layer." + P["fig6ac_loading"] + " (d–f) Concentration profiles at the "
                              "limiting current for three mediated rows at their rate constants (SI Table S11) on the ANEC film (δ = %.0f µm): the "
                              "bromide-mediated bromination of anisole (%s), ACT alcohol oxidation (%s), and NHPI allylic C–H oxidation (%s); the "
                              "grey curve is the local reaction rate per unit of ln x, k c_ox c_S x/(s_ox i/F). (g) The same three rows "
                              "against the diffusion-layer thickness across the archetype films. (h) Three catalyst rows at their literature-anchored "
                              "rate constants (Ni-catalyzed cross-electrophile coupling of an aryl and an alkyl bromide, cobalt-hydride "
                              "alkene reduction, and Ni-catalyzed homocoupling of an aryl bromide) (SI §S5.7); dotted lines mark 25 and "
                              "50 mA cm⁻². %s The governing equations, numerical method, regime "
                              "definitions and sensitivity analysis are given in SI §§S5.1-S5.7 and Tables S6-S8."
                              % (P["fig6_regime_delta_um"], _rword[_reg["Bromination"]], _rword[_reg["ACT"]], _rword[_reg["NHPI"]],
                                 P["fig6_substrates"]))
    # the SI sentences that carry what the caption dropped (S5.5, S5.7), as probes for the retired-quantity registry
    _and = lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1]
    P["fig6_si_probe_currents"] = "i_lim = %s mA cm⁻²" % _and([_f3(v) for v in P["fig6_regime_ilim"]])
    P["fig6_si_probe_shares"] = _and(["%.0f %%" % (100 * v) for v in P["fig6_regime_share"]]) + " of the activated mediator consumed inside the film"
    if sr:
        P["fig6h_si_probe"] = "gain ×%.1f (Ni–XEC), ×%.1f (cobalt hydride) and ×%.1f (Ni homocoupling)" % tuple(
            sr["per_row"][r]["gain_unstirred_to_rce"] for r in ("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "Co-H alkene reduction (e-HAT)",
                                                                "Cathodic Ni aryl-aryl homocoupling"))
    return P


if __name__ == "__main__":
    for k, v in phrases().items():
        if not isinstance(v, dict):
            print("%-28s %s" % (k, v))
