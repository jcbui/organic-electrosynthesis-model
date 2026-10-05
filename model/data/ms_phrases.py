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
    if len(_flat) != 2:
        raise SystemExit("Fig. 4c caption phrase assumes exactly two delta-insensitive mediated traces; model has %d" % len(_flat))
    P["fig4c_flat"] = "slopes −%.2f and −%.2f" % (_flat[0], _flat[1])
    P["fig4c_flat_values"] = [_flat[0], _flat[1]]
    P["fig4c_steep"] = "the other %s run −%.2f to −%.2f" % (["zero","one","two","three","four","five","six","seven","eight"][len(_steep)], _steep[0], _steep[-1])
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
                                  "ceilings by as much as %s-fold without carrying any of the 11 above 25 mA cm⁻² (SI §S5.7)."
                                  % (P["ck_kmax"], P["ck_amp"]))
    else:
        P["catalyst_finite_k"] = ("That count credits the catalyst with no turnover inside the film (k = 0), the floor of what a "
                                  "homogeneous carrier can deliver; allowing it to turn over at up to %s M⁻¹ s⁻¹ lifts the class's best "
                                  "ceilings by as much as %s-fold and carries %s of the 11 above 25 mA cm⁻², each then pinned by its "
                                  "substrate at %s rather than by the catalyst (SI §S5.7)."
                                  % (P["ck_kmax"], P["ck_amp"], P["ck_n25"], P["ck_cs_range"]))
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
        _cn, _cr = float(_cat["natural"].median()), float(_cat["rce"].median())
        _below = int((_cat[["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]].max(axis=1) < 25).sum())
        P["cat_gain_median"] = "%.0f" % (_cr / _cn); P["cat_med_natural"] = _fmed(_cn); P["cat_med_rce"] = _fmed(_cr)
        P["cat_below25"] = str(_below); P["cat_n"] = str(len(_cat))
        # v106 (2026-09-16): the author's own wording in the submission draft; every number still computed
        P["catalyst_span"] = ("Across the seven architectures, the median ceiling of catalyst-carried reactions rises only %s-fold, "
                              "from %s to %s mA cm⁻², and %s of the %s remain below 25 mA cm⁻² (Figure 5b)."
                              % (P["cat_gain_median"], P["cat_med_natural"], P["cat_med_rce"], P["cat_below25"], P["cat_n"]))
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
        _AZA = "Co-catalyzed aza-Wacker cyclization"
        # SPLIT 2026-10-03: the author moved the Figure 6 caption between these two sentences, so the
        # passage is no longer one contiguous run of text.  Two pins, not one -- the second still
        # carries every number, so the numeric check is unchanged.
        P["catalyst_finite_k"] = ("Using literature rate constants (SI §S5.7), Figure 6h shows three catalysts that move across "
                                  "limiting regimes as δ decreases.")
        P["catalyst_finite_k2"] = ("The nickel-catalyzed cross-electrophile coupling "
                                   "(k = %s M⁻¹ s⁻¹, x_k = %.1f µm) and the cobalt-hydride hydroamination (k = %s M⁻¹ s⁻¹, "
                                   "x_k = %.1f µm) possess x_k smaller than δ in every architecture."
                                   % (_kfmt_k(_pr[_NIXEC]["k_M"]), _pr[_NIXEC]["xk_um"],
                                      _kfmt_k(_pr[_COH]["k_M"]), _pr[_COH]["xk_um"]))
        P["catalyst_kinetic_ceilings"] = ("as δ decreases they approach their kinetic ceilings of %.0f and %.0f mA cm⁻², like ACT, "
                                          "so their ceilings rise only %.1f- and %.1f-fold."
                                          % (_kin(_NIXEC), _kin(_COH),
                                             _pr[_NIXEC]["gain_unstirred_to_rce"], _pr[_COH]["gain_unstirred_to_rce"]))
        P["catalyst_azawacker"] = ("The Co(salen) aza-Wacker cyclization has a much smaller rate constant (k = %s M⁻¹ s⁻¹), so its "
                                   "reaction layer, x_k = %.0f µm, is larger than δ in the ANEC, microfluidic and rotating-electrode "
                                   "cells" % (_kfmt_k(_pr[_AZA]["k_M"]), _pr[_AZA]["xk_um"]))
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
        P["k_provenance"] = (
            "Each of the six rate constants is an order-of-magnitude literature value for the "
            "elementary carrier\u2013substrate step, measured on model substrates in separate kinetic "
            "studies rather than reported by the electrosyntheses that set each row\u2019s concentrations "
            "and architecture. Each therefore carries the uncertainty its source reports, and we "
            "perform a sensitivity analysis to bracket that uncertainty: moving any one mediated rate "
            "constant by a factor of ten in either direction shifts a single architecture\u2019s count by "
            "at most one reaction and changes no ordering, and the catalyst rows are re-solved across "
            "a declared band that spans every adopted value (SI \u00a7\u00a7S5.5 and S5.7).")
        P["catalyst_gain"] = ("Even at the upper bound of the measured nickel rate constants, only %s of the 11 would clear "
                              "25 mA cm⁻², and those would then be limited by substrate supply at %s."
                              % (_hi_edge_n, P["ck_cs_range"]))
        # the author's wording (v113): both catalyst pins now land in one Section 4 sentence
        P["catalyst_conclusion"] = ("%s of the %s remain below 25 mA cm⁻²" % (P["cat_below25"], P["cat_n"]))
        # ---- v118: ONE mechanism at two loadings (Connor Coley, comment 21 on v35: "the distinction between EC
        # mediated and molecular catalyst is (almost) only the substrate concentration at the surface"). Both classes
        # are solved by the same EC' solver at their cited k; what the 50-reaction set keeps apart is carrier loading.
        _rx50 = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
        _cc = _rx50.merge(mat[["reaction", "carrier"]], on="reaction", how="left")
        _mC = _cc[_cc.carrier == "mediator"]["C_carrier_M"]
        _cC = _cc[_cc.carrier == "catalyst"]["C_carrier_M"]
        _load = float(_mC.median() / _cC.median())
        _gaps = [float(mat[mat.carrier == "mediator"][a].median() / mat[mat.carrier == "catalyst"][a].median()) for a in ARCH]
        # JR28 (2026-09-29): U+2032 PRIME, not U+2019. The prime IS the mechanism (catalytic
        # regeneration); the SI writes it that way in all 29 of its occurrences, and the manuscript
        # carried a curly apostrophe here until JR28 -- including in this template's own output.
        P["carrier_same_mechanism"] = ("Molecular catalysts are mechanistically identical to mediators: the electrode "
                                       "activates the carrier, the carrier reacts with the substrate in solution, and both "
                                       "are solved here as the same EC\u2032 problem, with the catalyst in place of the "
                                       "mediator and")
        # the author's wording (v129): he writes the median loading ratio as "order-of-magnitude" rather than
        # printing it, so the template ASSERTS that description against the model instead of carrying a number
        # the manuscript no longer has -- a qualitative claim is as gateable as a quantitative one when it names
        # a magnitude. 3.2x to 32x is what rounds to one decade in log10; the set gives 12x.
        assert 0.5 <= np.log10(_load) < 1.5, "the median loading ratio is %.1fx, not an order of magnitude" % _load
        P["carrier_loading"] = ("The key differentiator between the molecular catalysts and the mediators is that the "
            "molecular catalysts are much more dilute in concentration. Catalysts are loaded at %.1f to %.0f mM, as opposed to "
                                "%.0f mM to %.1f M for the mediators, and that order-of-magnitude difference at the "
                                "median sets the %d- to %d-fold gap between the two class rate ceilings."
                                % (_cC.min() * 1000, _cC.max() * 1000, _mC.min() * 1000, _mC.max(),
                                   round(min(_gaps)), round(max(_gaps))))
        P["carrier_loading_values"] = [_cC.min() * 1000, _cC.max() * 1000, _mC.min() * 1000, _mC.max(),
                                       round(min(_gaps)), round(max(_gaps))]
        P["carrier_loading_ratio"] = _load
        # v119 (author: "address all of these"): the two ranges OVERLAP at their edges, so the labels mark a difference
        # in typical loading, never a boundary. The overlapping rows are read from the table, not named by hand.
        _disp = {"ACT-mediated alcohol oxidation (flow, hectogram)": "ACT alcohol oxidation",
                 "BQ-mediated Wacker-Tsuji oxidation": "benzoquinone-mediated Wacker–Tsuji oxidation"}
        _ov = _cc[(_cc.carrier == "mediator") & (_cc.C_carrier_M <= _cC.max())].sort_values("C_carrier_M", ascending=False)
        assert set(_ov.reaction) <= set(_disp), "a new mediated row sits in the catalyst range: %s" % list(_ov.reaction)
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
                            "any planar architecture provides. Even at the thinnest planar films modeled (δ ≈ %.0f–%.0f μm), "
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
              "Co-catalyzed aza-Wacker cyclization": "aza-Wacker"}
        P["fig6h_gains"] = ("gain from the unstirred to the rotating-cylinder film, " +
                            "; ".join("%s ×%.1f against ×%.0f at k = 0" % (_h[r], sr["per_row"][r]["gain_unstirred_to_rce"], sr["per_row"][r]["gain_at_k0"]) for r in _h))
        # Section 8 restates the class medians at the two ends of the architecture ladder
        # the author's wording (v113): he states the gain and carries _cr to one decimal, which is a
        # digit more than the retired template printed; both agree with the matrix (0.8042, 5.2673)
        P["catalyst_sec8_medians"] = ("the median ceiling of catalyst-carried reactions rises only "
                                      "%d-fold, from %.1f to %.1f mA cm⁻²" % (round(_cr / _cn), _cn, _cr))
        P["fig6h_gain_values"] = [sr["per_row"][r]["gain_unstirred_to_rce"] for r in _h]
    # ---- Fig. 6g: three mediated rows at their cited k across the archetype films (julia/mediated_ec_matrix.csv
    # for the unstirred -> rotating-cylinder gain, the same convention as (h); julia/run_mediated_delta.jl draws the curve)
    _mm = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"))
    _g3 = [("ACT-mediated alcohol oxidation (flow, hectogram)", "ACT alcohol oxidation", "kinetic"),
           ("NHPI-mediated allylic C-H -> enone", "NHPI allylic C–H oxidation", "mediator-limited"),
           ("Br-mediated Hofmann rearrangement", "bromide-mediated Hofmann rearrangement", "substrate-limited")]
    _gg = {}
    for _r, _nm, _reg in _g3:
        _u = float(_mm[(_mm.reaction == _r) & (_mm.reactor == "Unstirred batch")].i_ec_mAcm2.iloc[0])
        _c = float(_mm[(_mm.reaction == _r) & (_mm.reactor == "Rotating cylinder 3000 rpm")].i_ec_mAcm2.iloc[0])
        _gg[_r] = (_nm, _reg, _u, _c)
    P["fig6g_gain_values"] = [v[3] / v[2] for v in _gg.values()]
    P["fig6g_gains"] = ("gain from the unstirred to the rotating-cylinder film, " +
                        "; ".join("%s ×%.1f" % (v[0], v[3] / v[2]) for v in _gg.values()))
    P["fig6g_sentence"] = ("(g) Limiting current against the diffusion-layer thickness for three mediated rows at their cited rate "
                           "constants, one per regime: ACT alcohol oxidation (k = 20 M⁻¹ s⁻¹, kinetic, %.0f to %.0f mA cm⁻² across the "
                           "films), NHPI allylic C–H oxidation (k = 0.5, mediator-limited, on its own transport bound) and the "
                           "bromide-mediated Hofmann rearrangement (k = 10³, substrate-limited on a detached reaction front, above its "
                           "planar substrate cap, dotted); %s."
                           % (_gg[_g3[0][0]][2], _gg[_g3[0][0]][3], P["fig6g_gains"]))
    # ---- Fig. 6d-f (v90): the three rows of (g) at their cited k on the ANEC film (36.2 um, measured), profiles at the
    # c-control plateau (julia/mediated_ec_profiles.csv). The regime word is the one the SOLVE assigns (regime_solved: substrate
    # exhausted at the wall / most of the activated mediator escaping / neither); G-ECPANEL requires it to agree with the analytic
    # assignment and to survive +/-25 % on both diffusivities. Panel order (d) substrate-limited, (e) kinetic, (f) mediator-limited.
    _rg = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_profiles.csv"))
    _order = ["Hofmann", "ACT", "NHPI"]
    _first = {s: _rg[_rg["short"] == s].iloc[0] for s in _order}
    _expect = ["substrate-limited", "kinetic", "mediator-limited"]
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
    def _kfmt(k):                                   # a decade prints as a power of ten, anything else as itself
        e = np.log10(k)
        return ("10" + ("%d" % round(e)).translate(_sup)) if (k >= 100 and abs(e - round(e)) < 1e-9) else ("%g" % k)
    _f3 = lambda v: ("%.0f" % v) if v >= 100 else ("%.1f" % v)          # three significant figures at these magnitudes
    P["fig6_regime_ilim_text"] = ", ".join(_f3(v) for v in P["fig6_regime_ilim"])
    P["fig6_regime_share_text"] = ", ".join("%.0f %%" % (100 * v) for v in P["fig6_regime_share"])
    _how = {"substrate-limited": "the substrate is exhausted at a front inside the film",
            "kinetic": "the activated mediator is consumed within x_k of the electrode",
            "mediator-limited": "most of the activated mediator leaves the film unreacted"}
    P["fig6_regime_sentence"] = ("(d–f) Concentration profiles at the limiting current for three of the eight mediated rows at their cited rate "
                                 "constants on the ANEC film (δ = %.0f µm, their cells in Table S5): the bromide-mediated Hofmann rearrangement "
                                 "(k = %s M⁻¹ s⁻¹, substrate-limited: %s), ACT alcohol oxidation (k = %s, kinetic: %s) and NHPI allylic C–H "
                                 "oxidation (k = %s, mediator-limited: %s), i_lim = %s mA cm⁻²; the grey curve is the local reaction rate per decade "
                                 "of distance, k c_ox c_S x/(s_ox i/F), whose area is the share of the activated mediator consumed inside the "
                                 "film: %s."
                                 % (P["fig6_regime_delta_um"], _kfmt(P["fig6_regime_ks"][0]), _how["substrate-limited"],
                                    _kfmt(P["fig6_regime_ks"][1]), _how["kinetic"], _kfmt(P["fig6_regime_ks"][2]), _how["mediator-limited"],
                                    P["fig6_regime_ilim_text"], P["fig6_regime_share_text"]))
    # (g) follows (d-f) in the caption, so it names the rows once more only by their behaviour across the films
    P["fig6g_sentence"] = ("(g) The same three rows against the diffusion-layer thickness across the archetype films: ACT alcohol oxidation "
                           "stays at %.0f to %.0f mA cm⁻² because its reaction layer is thinner than every film, NHPI allylic C–H oxidation "
                           "rides its own transport bound, and the bromide-mediated Hofmann rearrangement sits above its planar substrate cap "
                           "on a detached front; %s."
                           % (_gg[_g3[0][0]][2], _gg[_g3[0][0]][3], P["fig6g_gains"]))
    # ---- Section 4 body (v92, author: "propagate the analysis in each panel into section 4"): the (d-f) and (g) analyses as
    # prose, every number read from the same artifacts as the caption (the profile solve, the film sweep, the published matrix) ----
    _W = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    _cox_max = float(_rg[_rg["short"] == "Hofmann"].c_ox_norm.max())
    _dd = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_delta.csv"))
    _d_un = float(_mm[_mm.reactor == "Unstirred batch"].delta_um.iloc[0])
    _act_un = _dd[(_dd.reaction == _g3[0][0]) & (np.isclose(_dd.delta_um, _d_un))]
    if len(_act_un) != 1:
        raise SystemExit("mediated_ec_delta.csv carries no ACT solve at the unstirred film (%.1f um)" % _d_un)
    P["act_amp_unstirred"] = float(_act_un.i_ec_mAcm2.iloc[0] / _act_un.i_k0_mAcm2.iloc[0])
    if min(_order, key=lambda s: float(_first[s].D_red)) != "ACT":
        raise SystemExit("the Section 4 sentence calls ACT the slowest-diffusing carrier of the three; the artifact says otherwise")
    _gain = dict(zip([v[0] for v in _gg.values()], P["fig6g_gain_values"]))
    P["sec4_fig6df"] = ("Comparing x_k with δ (illustratively in the ANEC cell, δ = %.0f µm) then identifies what limits the "
                        "current when the substrate itself is not exhausted. "   # the author's wording, 2026-10-02
                        "In the bromide-mediated Hofmann rearrangement "
                        "(k = %s M⁻¹ s⁻¹, x_k = %.1f µm, Figure 6d), the reaction layer is much smaller than δ, and the substrate "
                        "is exhausted at a front inside the diffusion layer. Thus, bromine accumulates behind the front to %s times "
                        "the bromide bulk concentration, and the ceiling of %s mA cm⁻² is set by how fast amide substrate diffuses "
                        "to the front, not by the depletion of the mediator. Conversely, in ACT alcohol oxidation (k = %s M⁻¹ s⁻¹, "
                        "x_k = %.1f µm), the reaction layer is also smaller than δ, but the substrate stays at %.0f%% of its bulk "
                        "concentration, so the ceiling of %s mA cm⁻² is kinetically controlled and does not depend on δ (Figure 6e). "
                        "In NHPI allylic C–H oxidation (k = %s M⁻¹ s⁻¹, x_k = %.0f µm), the homogeneous reaction is so slow that the "
                        "reaction layer is larger than δ: the activated mediator (PINO) leaves the diffusion layer before it reacts, "
                        "so no NHPI is regenerated near the electrode, and the ceiling of %s mA cm⁻² is the same as it would be with "
                        "no substrate present, nFD_medC_med/δ (Figure 6f)."
                        % (P["fig6_regime_delta_um"],
                           _kfmt(float(_first["Hofmann"].k_M)), float(_first["Hofmann"].xk_um), _W[int(round(_cox_max))],
                           _f3(float(_first["Hofmann"].ilim_mAcm2)),
                           _kfmt(float(_first["ACT"].k_M)), float(_first["ACT"].xk_um),
                           100 * float(_first["ACT"].c_S_surf_norm), _f3(float(_first["ACT"].ilim_mAcm2)),
                           _kfmt(float(_first["NHPI"].k_M)), float(_first["NHPI"].xk_um), _f3(float(_first["NHPI"].ilim_mAcm2))))
    _act_i = float(_act_un.i_ec_mAcm2.iloc[0])
    _act_k0 = float(_act_un.i_k0_mAcm2.iloc[0])
    P["sec4_fig6g"] = ("These regimes determine how each reaction responds to intensification (Figure 6g). From the unstirred cell "
                       "to the rotating cylinder, the Hofmann rearrangement gains %.0f-fold, nearly the full reduction in δ, because "
                       "substrate transport limits it in every architecture. NHPI gains %.0f-fold: in the batch cells, where δ exceeds "
                       "x_k, it is held near its kinetic ceiling, but in every thinner diffusion layer the activated mediator escapes "
                       "before reacting and its current falls to the mediator-limited rate, nFD_medC_med/δ. ACT gains only %.1f-fold, "
                       "because x_k is smaller than δ in every architecture and its current remains limited by kinetics. In the ANEC "
                       "cell and every thinner diffusion layer (δ ≤ %.0f µm), ACT has the lowest ceiling of the three, not because its "
                       "chemistry is weak but because it carries only %.0f mM of mediator in water, and its mediator is the "
                       "slowest-diffusing carrier of the three. The mediator nonetheless provides a large benefit. Because the "
                       "activated mediator reacts with the alcohol within %.1f µm of the electrode, ACT is regenerated there and "
                       "returns to the electrode over that short distance rather than diffusing in from the bulk across δ. In the "
                       "unstirred cell (δ = %.0f µm), this local regeneration raises the ceiling to %.1f mA cm⁻², %.0f times the "
                       "%.2f mA cm⁻² the mediator could carry by transport from the bulk alone."
                       % (_gain["bromide-mediated Hofmann rearrangement"], _gain["NHPI allylic C–H oxidation"],
                          _gain["ACT alcohol oxidation"], P["fig6_regime_delta_um"], float(_first["ACT"].C_med_molm3),
                          float(_first["ACT"].xk_um), _d_un, _act_i, P["act_amp_unstirred"], _act_k0))
    # the range is the unstirred -> rotating-cylinder gain over the eight mediated rows, derived here
    _medm = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv")).merge(
        pd.read_csv(os.path.join(HERE, "reactions_50.csv"))[["reaction", "carrier_type"]], on="reaction")
    _medg = (_medm[_medm.carrier_type == "mediator"].rce / _medm[_medm.carrier_type == "mediator"].natural)
    if len(_medg) != 8:
        raise SystemExit("expected 8 mediated rows, found %d" % len(_medg))
    P["med_amp_lo"], P["med_amp_hi"] = "%.1f" % _medg.min(), "%.0f" % _medg.max()
    P["med_amp_values"] = [float(_medg.min()), float(_medg.max())]
    P["mediated_range"] = ("Across all eight mediated reactions, intensification raises limiting currents by approximately "
                           "%s-fold to %s-fold." % (P["med_amp_lo"], P["med_amp_hi"]))
    # ---- Fig. 6 caption, v93 (author: "its caption is WAYYY too long"): the panels named, the numbers moved to Section 4 and the SI ----
    _reg = {s: str(_first[s].regime_solved) for s in _order}
    P["fig6_caption_body"] = ("(a–c) The three current carriers in one boundary-layer idiom (schematic): substrate in and product out, the carrier "
                              "cycle between the electrode and the reaction site, and each cell's concentration profiles (substrate dotted, "
                              "activated carrier solid, resting carrier dashed); x_k marks the reaction layer." + P["fig6ac_loading"] + " (d–f) Concentration profiles at the "
                              "limiting current for three mediated rows at their cited rate constants on the ANEC film (δ = %.0f µm), "
                              "each with the transformation it solves drawn above it: the "
                              "bromide-mediated Hofmann rearrangement (%s), ACT alcohol oxidation (%s), and NHPI allylic C–H oxidation (%s); the "
                              "grey curve is the local reaction rate per decade of distance, k c_ox c_S x/(s_ox i/F). (g) The same three rows "
                              "against the diffusion-layer thickness across the archetype films. (h) Three catalyst rows at their cited rate "
                              "constants (Ni-catalyzed cross-electrophile coupling of an aryl and an alkyl bromide, "
                              "cobalt-hydride Markovnikov hydroamination, and Co(salen) aza-Wacker cyclization) "
                              "(SI §S5.7); dotted lines mark 25 and 50 mA cm⁻². The governing equations, numerical method, regime "
                              "definitions and sensitivity analysis are given in SI §§S5.1-S5.7 and Tables S6-S8."
                              % (P["fig6_regime_delta_um"], _reg["Hofmann"], _reg["ACT"], _reg["NHPI"]))
    # the SI sentences that carry what the caption dropped (S5.5, S5.7), as probes for the retired-quantity registry
    _and = lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1]
    P["fig6_si_probe_currents"] = "i_lim = %s mA cm⁻²" % _and([_f3(v) for v in P["fig6_regime_ilim"]])
    P["fig6_si_probe_shares"] = _and(["%.0f %%" % (100 * v) for v in P["fig6_regime_share"]]) + " of the activated mediator consumed inside the film"
    if sr:
        P["fig6h_si_probe"] = "gain ×%.1f (Ni–XEC), ×%.1f (cobalt hydride) and ×%.1f (aza-Wacker)" % tuple(
            sr["per_row"][r]["gain_unstirred_to_rce"] for r in ("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "Co-H alkene reduction (e-HAT)", "Co-catalyzed aza-Wacker cyclization"))
    return P


if __name__ == "__main__":
    for k, v in phrases().items():
        if not isinstance(v, dict):
            print("%-28s %s" % (k, v))
