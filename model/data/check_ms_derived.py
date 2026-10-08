"""Every DERIVED number the manuscript quotes, recomputed from the shipped model outputs.

    cd Section4_Model && python data/check_ms_derived.py
    cd Section4_Model && python data/check_ms_derived.py --negative-control

WHY THIS EXISTS
---------------
G-MSKAPPA checks the conductivities the manuscript asserts. verify_v*.py checks that the embedded
artwork matches a fresh render, and that particular sentences contain particular strings. NOTHING
checked the DERIVED quantities the body quotes -- boil-off ceilings, architecture medians,
threshold counts, cell voltages -- against the files that produce them.

That gap shipped a stale pair. When two Fig. 5 conductivities became measured (MeCN 18.9 -> 19.95)
and derived (DMF 8.0 -> 8.77), the beaker ceilings moved with them, and the sentence reading
"DMF and MeCN follow at ~85 and ~86 mA cm-2" was left behind at values the model no longer
produces. Artwork gates could not see it: the figure was re-rendered correctly, and only the prose
was stale.

The rule this enforces is the one the project already applies to figures -- compare against a
fresh computation, never against the file the number was copied from.
"""
import json
import os
import re
import sys
import unicodedata
import zipfile

from docx_text import asserted_text as _shared_asserted_text

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
from latest_ms import latest_ms   # shared resolver; the private copy here was pinned to a
# naming scheme the lineage left behind, so it gated a document 25 builds stale (2026-09-29)


MS = latest_ms()
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]


def docx_text(p):
    """Asserted text, via the shared cross-checked reader (data/docx_text.py).

    Was a local regex here. It got the <w:del> tag boundary wrong and hid 1,846 characters
    of the manuscript -- the whole Figure 2 caption among them -- from this gate while it
    reported PASS. The shared module parses structurally and asserts the structural walk
    and the regex agree, so the bug class cannot come back in one file at a time.
    """
    return _shared_asserted_text(p)

def main(negative_control=False):
    ms = docx_text(MS)
    if negative_control:
        # v40 prints "12/50 to 36/50"; the control perturbed "11/50 to 36/50", which the
        # manuscript stopped containing at v39, so the wrong-number branch was perturbing
        # NOTHING and only the deleted-phrase branch was really being exercised. A control
        # must perturb text that exists (CLAUDE.md trap 10).
        # Re-pointed 2026-09-07 with the pins: the CODEX prose stopped containing both phrases the
        # control used to perturb, so the control had gone inert -- CLAUDE.md trap 10, aimed at a
        # control instead of a gate. Both probes below are asserted present before being perturbed.
        # RE-POINTED 2026-09-13: the second probe was "compared with 88-89 mA cm−2", which v96
        # replaced when sigma became derived. A control pinned to a phrase the document has
        # stopped carrying asserts nothing (CLAUDE.md trap 10, aimed at a control), so both
        # probes are asserted present below before anything is perturbed.
        _rce25 = int((pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))["rce"] >= 25).sum())   # the matrix's own count
        # pass 7: the worked example's steady state is read from the thermal artifact (121 -> 116 C when H_EXT was derived)
        _tss = "reaches approximately %.0f °C" % json.load(open(os.path.join(ROOT, "results", "figK_thermal.json")))["si_support"]["worked_example"]["T_ss_C"]
        _probes = [("rises from 12 to %d of 50" % _rce25, "rises from 12/50 to %d/50" % _rce25), (_tss,)]
        for _alts in _probes:
            assert any(_p in ms for _p in _alts), "negative control is perturbing a phrase the MS lacks: %r" % (_alts,)
        # either wording of the Section 8 sentence (Connor Coley's review redlined it to "12/50 to 36/50")
        ms = ms.replace("rises from 12 to %d of 50" % _rce25, "rises from 12 to 41 of 50").replace("rises from 12/50 to %d/50" % _rce25, "rises from 12/50 to 41/50")
        ms = ms.replace(_tss, "reaches a warmer temperature")

    fk = json.load(open(os.path.join(ROOT, "results", "figK_thermal.json")))
    m = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv")).merge(
        pd.read_csv(os.path.join(HERE, "reactions_50.csv"))[["reaction", "carrier_type"]],
        on="reaction")
    med = {c: float(m[c].sort_values().iloc[24:26].mean()) for c in ARCH}
    n25 = {c: int((m[c] >= 25).sum()) for c in ARCH}
    n50 = {c: int((m[c] >= 50).sum()) for c in ARCH}
    sub, cat = m[m.carrier_type == "substrate"], m[m.carrier_type == "catalyst"]
    boil = {k: v["i_boil"] for k, v in fk["panelA"].items()}

    checks = []
    fails_pre = []       # cross-checks that fail before the phrase loop runs

    def want(label, phrase, value, tol=0.75):
        """The manuscript must contain `phrase`; `value` is what the model now gives.

        Matches `value` against ANY number in `phrase`. That is correct only when the phrase
        carries ONE meaningful number -- see want_ordered for the rest.
        """
        checks.append((label, phrase, value, tol))

    def want_ordered(prefix, phrase, values, tol=0.75):
        """Bind the k-th number in `phrase` to the k-th entry of `values`, by POSITION.

        This exists because want() alone was letting a whole sentence pass on coincidence. The
        Fig. 2b caption prints all six architecture medians in one sentence; six want() calls
        against that one phrase each accepted any number in it, so a caption reading
        "121, 108, 48, 19, 17 and 6 ... from unstirred batch to rotating cylinder" -- every
        median attributed to the WRONG architecture -- passed all six. That is CLAUDE.md trap 11
        (a value-only match binding to the wrong entity) in the file whose own comment cites
        trap 11.

        Positional matching also kills a second false accept: the trailing "cm-2" contributes a
        spurious 2 to the number list, so "29 mA cm-2" at tol 1.0 was accepting a model value
        near 2.0 as readily as near 29.0.
        """
        checks.append((prefix, phrase, list(values), tol))

    # =====================================================================================
    # WHAT THE MAIN TEXT ASSERTS -- rebuilt 2026-09-07 for the v79 prose.
    #
    # AUTHOR RULING (2026-09-07): "This is also supposed to be a review, the exact numbers can
    # be in the SI, we just want the main points of the analysis in the main text." The CODEX
    # revision acted on that: it shortened every figure caption and moved the per-panel values
    # into SI cross-references. Sixty pins here then reported "the manuscript no longer contains
    # ..." -- correctly, because the sentence was gone, and NOT because a number was wrong (the
    # same run reported zero wrong values).
    #
    # The response is NOT to delete those pins quietly. A pin is either RE-POINTED at the
    # sentence that still carries the number, or RETIRED into RETIRED_TO_SI below, which names
    # the quantity and asserts the SI still states it. Silently dropping a check is how a number
    # goes unwatched, which is the failure this gate exists to prevent.
    # =====================================================================================

    # --- the rate ceiling, Sections 3 and 4 ------------------------------------------------
    want("median, stirred (Sec 3 body)", "supports only about %.0f mA cm−2 in a stirred beaker" % med["stirred"],
         med["stirred"], 0.55)
    # 2026-09-11: the printed strings are BUILT from the model the way apply_v88_fixes.py builds them, so the
    # pin follows the document's own rounding rule rather than a typed literal (trap 10)
    _c0 = lambda v: "%.0f" % v
    _f1 = lambda v: ("%.0f" % v) if v >= 100 else ("%.1f" % v)
    want_ordered("Tier 2 gain, body",
                 "raises the median ceiling from %s to %s mA cm−2 in a recirculating flow cell "
                 "and to %s mA cm−2 in the angled-inlet ANEC" % (_c0(med["stirred"]), _c0(med["flow"]), _c0(med["anec"])),
                 [med["stirred"], med["flow"], 2, med["anec"], 2], 0.6)
    want_ordered("median + count clearing 50, stirred (Sec 4 body)",
                 "the median limiting current is %.0f mA cm−2 and only %d of 50 reactions exceed "
                 "50 mA cm−2" % (med["stirred"], n50["stirred"]),
                 [med["stirred"], 2, n50["stirred"], 50, 50, 2], 0.55)
    want_ordered("count clearing 50, unstirred -> RCE (Sec 4 body)",
                 "from %d of 50 in the unstirred archetype to %d of 50 at a rotating-cylinder "
                 "electrode" % (n50["natural"], n50["rce"]), [n50["natural"], 50, n50["rce"], 50], 0.01)
    want_ordered("count clearing 50, unstirred -> RCE (Fig 5 caption)",
                 "from %d/50 in an unstirred cell to %d/50 at a rotating-cylinder electrode" % (n50["natural"], n50["rce"]),
                 [n50["natural"], 50, n50["rce"], 50], 0.01)
    # 2026-10-06 (chemistry audit, pass 2): the abstract printed "from 9 to 34" for the >=50 count -- 34 is the >=25
    # count -- and nothing pinned it. The top of the range is the thinnest-film archetypes' count, read from the matrix.
    want_ordered("count clearing 50, thinning the film (abstract)",
                 "raises the number exceeding 50 mA cm−2, the current density needed for commercial applications, "
                 "from %d to %d" % (n50["natural"], max(n50.values())), [50, 2, n50["natural"], max(n50.values())], 0.01)
    # and the Fig. 4 caption counted THREE films measured on the cells themselves while the methods (and Table S1) give
    # two, the stirred film being measured on a comparable cell; the count is in words, so presence is the check
    _fig4_films = "two of the seven are measured on the cells themselves and one in a comparable convecting cell"
    if _fig4_films not in ms or "three of the seven are measured on the cells themselves" in ms:
        fails_pre.append(("Fig. 4 caption: how the seven films are anchored", _fig4_films[:60], 0.0, [1.0]))

    # --- the delta ladder, Section 8 (the one place the full median set survives) -----------
    want_ordered("architecture medians (Sec 8 ladder)",
                 "rises from %s mA cm−2 in the unstirred archetype to %s mA cm−2 in stirred "
                 "batch, %s mA cm−2 in recirculating flow, %s mA cm−2 in the ANEC cell, "
                 "%s mA cm−2 in the 25 μm microfluidic cell, and %s mA cm−2 at a "
                 "rotating-cylinder electrode" % (_f1(med["natural"]), _f1(med["stirred"]), _f1(med["flow"]),
                                                  _f1(med["anec"]), _f1(med["micro"]), _f1(med["rce"])),
                 [med["natural"], 2, med["stirred"], 2, med["flow"], 2, med["anec"], 2,
                  med["micro"], 2, 25, med["rce"], 2], 0.55)
    # 2026-09-21: Connor Coley's review redlined this sentence to "12/50 to 36/50". Both wordings carry the same two
    # counts, so the pin binds whichever the manuscript prints -- a pin typed to one wording turns a reviewer's
    # rewording into a false failure (the v105/v106 lesson). If neither is present the gate still reports it GONE.
    _sec8_slash = "The number clearing 25 mA cm−2 rises from %d/50 to %d/50" % (n25["natural"], n25["rce"])
    if _sec8_slash in ms:
        want_ordered("count clearing 25, unstirred -> RCE (Sec 8)", _sec8_slash,
                     [25, 2, n25["natural"], 50, n25["rce"], 50], 0.01)
    else:
        want_ordered("count clearing 25, unstirred -> RCE (Sec 8)",
                     "The number clearing 25 mA cm−2 rises from %d to %d of 50" % (n25["natural"], n25["rce"]),
                     [25, 2, n25["natural"], n25["rce"], 50], 0.01)

    # --- the carrier classes, Section 4 -----------------------------------------------------
    sys.path.insert(0, os.path.join(ROOT, "figs"))
    import model_medians as _MM
    # 2026-10-05: class MEDIANS are over the catalyst rows that are stoichiometric in charge (the chain row,
    # tabulated at the charge it passes, is left out; SI S4.2 and Table S10); class COUNTS are over every row.
    _cat_st = cat[~cat.reaction.isin(_MM.CHAIN)]
    if len(cat) - len(_cat_st) != 1:
        raise SystemExit("expected one chain row in the catalyst class, found %d" % (len(cat) - len(_cat_st)))
    _cn, _cr = float(_cat_st["natural"].median()), float(_cat_st["rce"].median())
    # 2026-09-11: the sentence is COMPUTED by ms_phrases.py (seven catalyst rows carried at a sourced k), and
    # pinned here from that module, NFKC-normalised as this gate reads the manuscript; its numbers are the
    # class median gain, the two medians, the rows below 25 everywhere, the class size (Figure 5b is a
    # cross-reference and carries no number to bind).
    import unicodedata as _ud0
    sys.path.insert(0, HERE)
    from ms_phrases import phrases as _phrases0
    _P0 = _phrases0()
    # chemistry audit, 2026-10-05: the sentence now also says how many rows sit at the floor ("because 8 of the 12 carry no
    # measured rate constant"), read here from the sweep artifact, not from the phrase module
    _n_floor0 = int(json.load(open(os.path.join(ROOT, "results", "catalyst_ec_sensitivity.json")))["sourced"]["n_floor"])
    # 2026-10-07 (author: restore the pedagogy of the pre-audit text): the span sentence states the two medians and the
    # one exception; "two-thirds" at the floor and "all but one of the twelve" are words, asserted in ms_phrases and
    # checked here against the sweep artifact and the matrix, a second path
    want_ordered("catalyst span and exception, body", _ud0.normalize("NFKC", _P0["catalyst_span_short"]).split(" (Figure 5b)")[0],
                 [_cn, _cr] + list(_P0["catalyst_span_short_values"])[2:], 0.06)   # the two medians from THIS gate's matrix read
    if 3 * _n_floor0 != 2 * len(cat) or int((cat[ARCH].max(axis=1) < 25).sum()) != len(cat) - 1:
        fails_pre.append(("catalyst span words ('two-thirds' at k = 0; all but one below 25)",
                          "%d of %d at the floor, %d below 25" % (_n_floor0, len(cat), int((cat[ARCH].max(axis=1) < 25).sum())), 0.0, [1.0]))
    # --- the catalyst class under a finite k (G-CATK; SI S5.7) ------------------------------
    # The ten-of-eleven count above is a k = 0 statement. v83 added the sentences that say so,
    # every number in them read from results/catalyst_ec_sensitivity.json by ms_phrases.py; the
    # pins below are those same computed strings, NFKC-normalised the way this gate reads the
    # manuscript (superscripts fold to digits, so "cm⁻²" must be sought as "cm−2").
    import unicodedata as _ud, json as _json
    sys.path.insert(0, HERE)
    from ms_phrases import phrases as _phrases
    _P = _phrases()
    _ck = _json.load(open(os.path.join(ROOT, "results", "catalyst_ec_sensitivity.json")))
    _ck_amp = _ck["per_k"]["%g" % max(float(k) for k in _ck["k_band_M"])]["max_amplification"]
    _nf = lambda t: _ud.normalize("NFKC", t)
    # 2026-09-11: the catalyst paragraph is four computed sentences (ms_phrases.py): the span (pinned above),
    # the sourced-k sentence, the gain sentence and, in Section 8, the restatement. The first two carry
    # rate constants whose superscripts NFKC folds into digits, so they are PRESENCE checks; the gain sentence
    # and the restatement bind their numbers. The Fig. 6 caption pins are the three regime currents and the
    # three reaction shares (d-f, at the plateau) and the S5.7 pointer; the former panel-(b) map pins are
    # retired (the map is no longer drawn: a-c cells, d-f profiles, g-h intensification).
    _sr = _ck.get("sourced") or {}
    # v106: the author states the three sourced rows individually rather than as a range. Each number is
    # bound to its own clause: the kinetic ceiling a row approaches is the Savéant plateau, computed in
    # ms_phrases from i(k = 0) at the 12.5 µm film and that row's x_k, never typed.
    _pr = _sr.get("per_row", {})
    _NIXEC, _COH, _HOMO = ("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "Co-H alkene reduction (e-HAT)",
                           "Cathodic Ni aryl-aryl homocoupling")
    _kin = lambda r: _pr[r]["i_k0_mAcm2"]["micro"] * 12.5 / _pr[r]["xk_um"]
    if _pr:
        # two pins, each at half the last digit it prints: the ceilings are printed as integers, the gains to 0.1.
        # chemistry audit, 2026-10-05 (night): Figure 6h's third row is the Ni aryl-aryl homocoupling at the nickel constant
        # (the Co(salen) allylic C-H amination has no measured constant and left the panel), so both pins carry three rows
        if _HOMO not in _pr:
            fails_pre.append(("Fig. 6h third row at a sourced k", "the sweep artifact does not carry the homocoupling", 0.0, [1.0]))
        else:
            _kc = _nf(_P["catalyst_kinetic_ceilings"])
            want_ordered("catalyst kinetic ceilings, body", _kc[:_kc.index(", like ACT")],
                         [_kin(_NIXEC), _kin(_COH), _kin(_HOMO), 2], 0.5)
            want_ordered("catalyst kinetic gains, body", _kc[_kc.index("so their ceilings rise"):],
                         [_pr[r]["gain_unstirred_to_rce"] for r in (_NIXEC, _COH, _HOMO)], 0.06)
            # the homocoupling sentence says it is the only catalyst-carried row to clear 25 mA cm-2, from the recirculating
            # flow cell on: checked here against the published matrix, a second path from the one ms_phrases asserts on
            _a25 = sorted(cat[cat[ARCH].max(axis=1) >= 25].reaction)
            _hrow = cat[cat.reaction == _HOMO][ARCH].iloc[0]
            _from = [a for a in ARCH if _hrow[a] >= 25]
            if _a25 != [_HOMO] or _from != list(ARCH)[list(ARCH).index("flow"):]:
                fails_pre.append(("catalyst homocoupling sentence, body",
                                  "rows clearing 25: %r; the homocoupling clears it at %r" % (_a25, _from), 1.0, [float(len(_a25))]))
    want_ordered("catalyst gain at the sourced k, body", _nf(_P["catalyst_gain_tail"]),
                 [_sr.get("rows_clearing25_anywhere_at_band", [0, 0])[1], len(cat), 25, 2], 0.01)
    if _nf(_P["catalyst_gain"]) not in ms or "limited by substrate supply" in ms:
        fails_pre.append(("catalyst gain sentence at the band top, body", _nf(_P["catalyst_gain"])[:60], 0.0, [1.0]))
    # 2026-10-07: the "restatement" and "medians" pins read the same Section 4 sentence the span pin now covers (the
    # catalyst_conclusion / catalyst_sec8_medians strings appear nowhere else in the manuscript), so they are retired with it
    want("Fig. 6 caption pointer to S5.7", _nf("are given in SI §§S5.1-S5.7 and Tables S6-S8"), 5.7, 0.05)

    # ---- the thermal numbers the main text prints (added 2026-09-12 by the post-v94 audit) -----
    # Three of these were checked by nothing. Table 1's readiness gate printed the unstirred
    # median as 8.0 while Section 8.2 printed 8.2 for the same quantity; the Section 8.2 worked
    # example's three numbers had no pin and no registry row behind them; and the ohmic clause
    # beside them quoted a sub-range ("5-18 V") that appears in no gate, registry row, SI sentence
    # or build script in this repository.
    import json as _json2
    with open(os.path.join(ROOT, "results", "figK_thermal.json"), encoding="utf8") as _fh:
        _TH = _json2.load(_fh)
    _we = _TH["si_support"]["worked_example"]
    # JR5 (2026-09-28) collapsed this rung onto the STIRRED median for Jonas's #199 -- an undivided
    # batch cell is still a stirred one -- so the cell reads "~9 median (stirred)" and the pin follows
    # the document rather than the retired unstirred value.
    # the tolerance is absolute (abs(n - value) <= tol) and the CELL prints one significant figure,
    # "~9", against a model median of 9.3, so it must admit half of the last printed digit.
    want("Table 1 readiness gate, stirred median", _nf("~%.0f median (stirred)" % med["stirred"]),
         med["stirred"], 0.5)
    want_ordered("Sec 8.2 worked example: cell voltage and heat",
                 _nf("the model gives a 13 V cell dominated by ohmic loss and approximately "
                     "1 W cm−2 of heat"),
                 [_we["E_cell_V"], _we["q_Wcm2"], 2], 0.6)
    want("Sec 8.2 worked example: the batch steady state",
         _nf("The corresponding batch reactor reaches approximately %.0f °C" % _we["T_ss_C"]),
         _we["T_ss_C"], 3.0)
    # "dominated by ohmic resistance" is a DIRECTION word, and a direction word that contradicts
    # its own model is exactly what a numeric gate cannot see. Bind it: the ohmic share of the
    # dissipated voltage in the worked example must actually be the larger part.
    _ohmic_share = _we["ohmic_V"] / _we["E_cell_V"]
    assert _ohmic_share > 0.5, ("Section 4 calls the 10-20 V cell 'dominated by ohmic resistance' "
                                "while the worked example puts the ohmic term at %.0f%% of it"
                                % (100 * _ohmic_share))
    # Section 5's "10-20 V in our energy balance" is the band the SI computes for ONE case -- 0.2 M NaI/DMF at 50 mA cm-2
    # across the 2 cm beaker gap, inside 10-20 V for kappa between the two thresholds -- and the sentence scopes it to that
    # case (pass 42, 2026-10-07: unscoped, it read as what the model gives for any poorly conducting electrolyte, when THF
    # gives 36 V and MeCN 7 V). The printed conductivities are the thresholds rounded INWARD, so the band holds across them,
    # and "dominated by ohmic resistance" must hold at both edges.
    _dx = json.load(open(os.path.join(ROOT, "results", "figK_thermal.json")))["si_support"]["beaker_dmf_example"]
    _klo, _khi = int(-(-_dx["kappa_E50_20V_mScm"] // 1)), int(_dx["kappa_E50_10V_mScm"] // 1)
    assert abs(_dx["gap_m"] - 0.02) < 1e-12, "the DMF cell-voltage example is no longer at the 2 cm beaker gap"
    for _k, _v in ((_dx["kappa_E50_20V_mScm"], 20.0), (_dx["kappa_E50_10V_mScm"], 10.0)):
        assert 50.0 * 10.0 * _dx["gap_m"] / (0.1 * _k) / _v > 0.5, (
            "at kappa = %.2f mS cm-1 the 50 mA cm-2 DMF cell is no longer ohmic-dominated" % _k)
    _sec5 = _nf("the cell-voltage model presented in SI §S6 estimates 10–20 V across a 2 cm gap at 50 mA cm⁻² in DMF conducting "
                "%d–%d mS cm⁻¹, dominated primarily by ohmic resistance" % (_klo, _khi))
    assert negative_control or _sec5 in _nf(ms), (
        "Section 5's cell-voltage band is not scoped to the computed case: expected %r" % _sec5)
    # skipped under the control, which perturbs this very clause
    # The claim is what is pinned, not one wording of it: the author writes "dominated primarily by
    # ohmic resistance" since v104, and an adverb between the two words must not read as a vanished
    # phrase (2026-09-16).
    assert negative_control or re.search(r"dominated(?: \w+)? by ohmic (?:resistance|loss)", _nf(ms)), (
        "the ohmic-dominance clause of Section 4 is not in the manuscript; it was pinned here "
        "because the sub-range it replaced ('5-18 V') had no basis anywhere in the tree")
    for _dead in ("5-18 V", "8.0 median"):
        assert negative_control or _dead not in _nf(ms), (
            "retired thermal phrase back in the manuscript: %r" % _dead)
    # v93: the caption is short again (author); its currents, shares and per-row gains moved to Section 4 (pinned by presence
    # below) and to the SI (retired-to-SI probes in RETIRED). The caption itself is one computed phrase, pinned by presence.
    # 2026-09-11 (v90): the (d-f) panels ARE published cells -- the profile solve runs run_mediated.jl's own mesh on the ANEC film --
    # so the current each panel prints must equal the row's ANEC cell of the mediated matrix (a second artifact, written by a
    # different script), and the fine-mesh check the solver carries beside it must sit within 1 %.
    _prof = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_profiles.csv")).groupby("short").first()
    _mmx = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"))
    for _sh, _rx in (("Bromination", "Br- oxidation / electrophilic bromination"), ("ACT", "ACT-mediated alcohol oxidation (flow, hectogram)"),
                     ("NHPI", "NHPI-mediated allylic C-H -> enone")):
        _cell = float(_mmx[(_mmx.reaction == _rx) & (_mmx.reactor == "ANEC flow cell")].i_ec_mAcm2.iloc[0])
        _pan = float(_prof.loc[_sh, "ilim_mAcm2"]); _fine = float(_prof.loc[_sh, "ilim_fine_mAcm2"])
        if abs(_pan / _cell - 1) > 1e-4:
            fails_pre.append(("Fig. 6 (d-f) %s panel == its ANEC cell" % _sh, "%.4f vs matrix %.4f" % (_pan, _cell), _cell, [_pan]))
        if abs(_fine / _pan - 1) > 0.01:
            fails_pre.append(("Fig. 6 (d-f) %s fine-mesh check" % _sh, "%.4f vs %.4f" % (_fine, _pan), _pan, [_fine]))
    for _lab, _ph in (("catalyst both limits, body", _P["catalyst_both_limits"]),
                      ("catalyst sourced-k sentence, body", _P["catalyst_finite_k"]),
                      ("catalyst sourced-k numbers, body", _P["catalyst_finite_k2"]),
                      ("catalyst homocoupling sentence, body", _P["catalyst_homo_short"]),
                      # pass 16: the span pin above stops at "(Figure 5b)", so the sentence after it is pinned whole here
                      ("catalyst span with its explanation, body", _P["catalyst_span_short"]),
                      ("rate-constant provenance, body", _P["k_provenance_short"]),
                      ("mediated regimes sort the twelve rows, body", _P["med_regime_sort"]),
                      ("Fig. 6 caption, body", _P["fig6_caption_body"]),
                      ("Sec 4 (d-f) analysis, body", _P["sec4_fig6df"]),        # v92: computed passages, presence = correctness
                      ("Sec 4 (g) analysis, body", _P["sec4_fig6g"]),
                      # v118: the mediated/catalyst sentences carry no number, so presence IS the check
                      ("Sec 4 one mechanism, body", _P["carrier_same_mechanism"]),
                      ("Fig. 6 (a-c) loading clause", _P["fig6ac_loading"].strip())):
        if _nf(_ph) not in ms:
            fails_pre.append((_lab, _nf(_ph)[:60], 0.0, [1.0]))
    # the count is a word, so the digits are the two gains; split so each is held to half its own last printed digit
    # (2026-10-05: the top gain is printed as an integer, 24 against 23.6, which the old single 0.2 tolerance refused)
    _mr = _nf(_P["mediated_range"])
    want_ordered("mediated intensification range, low end, body", _mr[:_mr.index("-fold to ")], [_P["med_amp_values"][0]], 0.05)
    want_ordered("mediated intensification range, high end, body", _mr[_mr.index("-fold to ") + 1:], [_P["med_amp_values"][1]], 0.5)
    # v118: carrier loading, the one thing that separates the two homogeneous classes (Connor Coley, comment 21).
    # Six numbers in one sentence, so POSITIONAL: 2.6 / 30 mM (catalyst range), 24 mM / 1.0 M (mediator range) and
    # the 17- to 23-fold span of the class median ceiling ratio. v129: the author writes the median loading ratio
    # as "order-of-magnitude" instead of printing 12-fold, and ms_phrases asserts that description against the
    # model, so the claim is still gated -- see RETIRED below for the number itself.
    want_ordered("carrier loading separation, body", _nf(_P["carrier_loading_short"]),
                 list(_P["carrier_loading_short_values"]), 0.06)
    # v120 (Connor's comment 48): what the model shows about porous electrodes -- the thinnest planar films modeled and
    # how many reactions still fall short there -- bound positionally (11, 13, 14, 50, 25)
    want_ordered("porous-electrode need, Sec 8", _nf(_P["porous_need"]), list(_P["porous_need_values"]), 0.75)
    _slopes = _MM.mediated_delta_slopes()
    _flat = sorted(-v["slope"] for v in _slopes.values() if v["slope"] > -0.5)
    _steep = sorted(-v["slope"] for v in _slopes.values() if v["slope"] <= -0.5)
    # 2026-10-05: eleven mediated rows, four of them nearly flat; the sentence is computed in ms_phrases
    # (it names the four and asserts they are the flat ones) and its four slopes are bound here.
    # 2026-10-06 (chemistry audit, pass 4): three of the four are kinetic; the thioether's shallow fit is a rise through
    # its substrate cap and a fall to a kinetic plateau, and the sentence now says so with its peak and thin-film currents.
    # 2026-10-07: the slope-by-slope sentence left the manuscript (author: "you flooded them with numbers"); SI S7 and
    # Table S6 print every slope, watched by the RETIRED entry below
    # (the "summarising all 56 mediator-architecture calculations" pin of the v87 caption (b) is retired with
    # that panel, 2026-09-11; the 56-cell census is asserted by G-ECBAND)

    # --- the Joule-heating ceiling, Section 4 ----------------------------------------------
    # pass 7: MeCN and DMF can round to one value (80 and 80 at H_EXT 13.8), and the manuscript then prints it once
    if round(boil["MeCN"]) == round(boil["DMF"]):
        want_ordered("Fig7a beaker ceilings",
                     "boiling point of THF at approximately %.0f mA cm−2, compared with approximately %.0f "
                     "mA cm−2 for MeCN and DMF" % (boil["THF"], boil["MeCN"]),
                     [boil["THF"], 2, 0.5 * (boil["MeCN"] + boil["DMF"]), 2], 1.0)
    else:
        want_ordered("Fig7a beaker ceilings",
                     "boiling point of THF at approximately %.0f mA cm−2, compared with %.0f-%.0f "
                     "mA cm−2 for MeCN and DMF"
                     % (boil["THF"], min(boil["MeCN"], boil["DMF"]), max(boil["MeCN"], boil["DMF"])),
                     [boil["THF"], 2, min(boil["MeCN"], boil["DMF"]), max(boil["MeCN"], boil["DMF"]), 2], 1.0)
    # v106: the author replaced the absolute THF microfluidic ceiling with the passive-cooling margins
    # of Figure 7d. Each margin is required cooling duty over what the cell rejects passively, both from
    # results/figK_thermal.json; the retired ceiling is still stated (and gated) in the SI, see RETIRED.
    _pc, _av = fk["panelC"], fk["panelC"]["passively_available"]
    _MICRO, _ROT = "microfluidic 25 $\\mu$m", ("RDE 1600 rpm", "rotating cyl. 3000 rpm")
    _SOLV = ("THF", "MeCN", "DMF", "aq. NaOH")
    _mm = [_av[_MICRO] / _pc[s][_MICRO] for s in _SOLV]
    want_ordered("Fig7d microfluidic passive margin", "the microfluidic cell by %.1f- to %.0f-fold"
                 % (min(_mm), max(_mm)), [min(_mm), max(_mm)], 0.4)
    _thf = [_pc["THF"][r] / _av[r] for r in _ROT]
    want_ordered("Fig7d THF rotating shortfall",
                 "THF requires %.0f- to %.0f-fold more heat rejection than these cells provide" % (min(_thf), max(_thf)),
                 [min(_thf), max(_thf)], 0.5)          # printed as integers: half the last digit
    _org = [_pc[s][r] / _av[r] for s in ("MeCN", "DMF") for r in _ROT]
    want_ordered("Fig7d MeCN/DMF rotating shortfall", "MeCN and DMF %.1f- to %.1f-fold more" % (min(_org), max(_org)),
                 [min(_org), max(_org)], 0.06)
    _st = [_pc[s]["zero-gap PEM stack"] / _av["zero-gap PEM stack"] for s in _SOLV]
    want_ordered("Fig7d stack shortfall", "%.0f- to %.0f-fold beyond what passive rejection supplies"
                 % (min(_st), max(_st)), [min(_st), max(_st)], 0.5)      # printed as integers: half the last digit

    # --- the tier bands, Section 3 ----------------------------------------------------------
    _d = {k: _MM.delta_range(k) for k in ARCH}
    # Each tier band is the delta_eff span of its own members, computed -- never typed.
    want_ordered("Tier 1 band, body", "Tier 1 (δ ≈ 200–228 μm)",
                 [1, _d["stirred"][0], _d["natural"][1]], 1.0)
    want_ordered("Tier 2 band, body", "Tier 2 spans δ ≈ 36–107 μm",
                 [2, _d["anec"][0], _d["flow"][1]], 1.0)
    want_ordered("Tier 3 band, body", "Tier 3 spans δ ≈ 8–16 μm",
                 [3, min(_d["rde"][0], _d["rce"][0]), max(_d["rde"][1], _d["micro"][1])], 1.0)

    # The Fig. 4(d-f) panels are no longer quoted by value in the manuscript, but the caption's
    # DIRECTION words still are: it may call them lower bounds only while a panel really ends on
    # a Newton wall. That test needs the regime solve regardless of which numbers are printed.
    _rg = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_profiles.csv")).groupby("short").first()
    _all_plateau = all(str(x).startswith(("plateau", "collapse")) for x in _rg["limiter"])

    # =====================================================================================
    # RETIRED FROM THE MAIN TEXT -- each still stated, and still gated, in the SI.
    # (quantity, the SI phrase that must still carry it)
    # =====================================================================================
    # Each entry says where the quantity went, and BOTH answers are falsifiable:
    #   "si"          -- the SI must still state it, so the SI-side gates keep watching it;
    #   "unpublished" -- NEITHER document may state it, so it cannot quietly reappear unwatched.
    # Without the second case this list would be a way to silence a check by asserting nothing.
    RETIRED = [
        ("Fig. 5 zero-gap and cooling-duty values", "si", "zero-gap ceiling"),     # pass 16: a Table S9 row label; bare "zero-gap" occurs 36 times
        ("the aq. NaOH beaker ceiling", "si", "aq. NaOH beaker ceiling"),     # pass 16: "283" matched only a page range
        ("the rotating-cylinder second-correlation bound", "si", "Against the correlation of Jang et al."),   # "30%" matched S4.1
        ("the Fig. 2b model floor (8.46 um)", "unpublished", "8.46"),
        ("the Fig. 2c/3a illustrative corpus-median ceiling (13.5 mA cm-2)", "unpublished", "13.5 mA"),
        # probe carries the unit: a bare "3.96" is also the aza-Wacker row's k = 0 ceiling in the
        # S5.7 census table (found 2026-09-09), and a value-only match is trap 11
        ("the catalyst uplift at fixed delta (0.19 -> 3.96 mA cm-2)", "unpublished", "3.96 mA cm"),
        # v93: the Figure 6 caption detail moved to the SI (S5.5 for the three (d-f) solves, S5.7 for the (h) rows)
        ("the Fig. 6 (d-f) limiting currents", "si", _P["fig6_si_probe_currents"]),
        ("the Fig. 6 (d-f) reaction shares", "si", _P["fig6_si_probe_shares"]),
        ("the Fig. 6h per-row gains against k = 0", "si", _P.get("fig6h_si_probe", "gain ×")),
        # v106: the author's Figure 7 discussion states the cooling margins, not the absolute ceiling.
        # The probe is the SI's own row label, because a bare "395" also matches "395 nm" in Table S2.
        ("the THF microfluidic boil-off ceiling (395 mA cm-2)", "si", "THF microfluidic ceiling"),
        # v129: the author reworded the carrier-loading sentence and removed the v119 overlap sentence with it.
        # The median loading RATIO is no longer printed -- he writes "order-of-magnitude", which ms_phrases
        # asserts against the model (3.2x-32x) -- and the two overlapping loadings are still in Table S2, which
        # prints every row's carrier concentration, so the SI keeps watching them.
        ("the median carrier-loading ratio (12-fold)", "unpublished", "12-fold difference"),
        ("the two mediated rows inside the catalyst range (25 and 23.5 mM)", "si", "ACT 5 mol% = 25 mM"),   # Table S2's own cell
        # 2026-10-07 (author: the modelling sections read as they did before the audits; the detail lives in the SI)
        ("the fitted log-log slopes of the twelve mediated rows", "si", "of the 12 are nearly flat"),
        ("the homocoupling's carrier-charge sensitivity (neutral precursor vs the dication)", "si",
         "carries the neutral charge of its precursor"),
        ("the Br2 accumulation multiple behind the bromination front", "si", "times the bromide bulk"),   # the SI computes the multiple
        ("the substrate each Figure 6 (g)/(h) curve is solved for", "si", "dihydroalprenolol"),   # Table S10's balanced row
        ("the loading decomposition of the catalyst-mediator gap (k = 0 and turnover gaps)", "unpublished",
         "when no in-film turnover is credited"),
        ("the mediator loading range quoted from 5 mM", "unpublished", "5 mM to 1.0 M for the mediators"),
    ]
    _si_path = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")
    _si = _shared_asserted_text(_si_path) if os.path.exists(_si_path) else ""
    for _what, _where, _probe in RETIRED:
        _probe = _nf(_probe)                        # the SI text is NFKC-normalised (cm⁻² reads cm−2); so must the probe be
        if _where == "si" and _probe not in _si:
            fails_pre.append(("retired-to-SI but the SI dropped it: %s" % _what,
                              "the SI must still state %r" % _probe, 0.0, [1.0]))
        if _where == "unpublished" and (_probe in _si or _probe in ms):
            fails_pre.append(("retired as unpublished but it is printed again: %s" % _what,
                              "%r reappeared, so it needs a pin" % _probe, 0.0, [1.0]))



    fails, oks, absent = list(fails_pre), [], []
    for label, phrase, value, tol in checks:
        if phrase not in ms:
            # A MISSING phrase is a FAILURE, not a skip. Every one of these numbers went stale
            # through v27 while the artwork gates passed; when v28 corrected the wording the
            # two checks that covered them silently stopped checking anything. A gate that
            # disarms itself the moment a sentence is reworded is worse than no gate.
            # normalise an ordered expectation to a printable scalar for the report
            _shown = value[0] if isinstance(value, list) and value else (
                float("nan") if isinstance(value, list) else value)
            absent.append((label, phrase, _shown))
            fails.append((label, phrase, _shown, []))
            continue
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", phrase)]
        if isinstance(value, list):
            # ORDERED: the k-th number in the phrase must be the k-th model value. Anything
            # shorter than the expectation is a failure, not a pass by omission.
            hit = (len(nums) >= len(value)
                   and all(abs(n - v) <= tol for n, v in zip(nums, value)))
            shown = value[0] if value else float("nan")
            (oks if hit else fails).append((label, phrase, shown, nums))
        else:
            hit = any(abs(n - value) <= tol for n in nums)
            (oks if hit else fails).append((label, phrase, value, nums))

    # the caption may call the Fig. 4 (d-f) values lower bounds ONLY while a panel ends on a wall
    if _all_plateau and "strict lower bounds" in ms:
        fails.append(("Fig4d-f wall wording", "strict lower bounds", 0.0, [0.0]))
    elif not _all_plateau and "reach the collapse criterion" in ms:
        fails.append(("Fig4d-f wall wording", "reach the collapse criterion", 0.0, [0.0]))
    print("recomputed from julia/tier0_ec_matrix.csv and results/figK_thermal.json\n")
    print("%-38s %-26s %10s" % ("claim", "as printed", "model now"))
    for label, phrase, value, nums in oks:
        print("  ok   %-32s %-24s %9.1f" % (label[:32], phrase[:24], value))
    for label, phrase, value, nums in fails:
        print("  FAIL %-32s %-24s %9.1f" % (label[:32], phrase[:24], value))
    for label, phrase, value in absent:
        print("  GONE %-32s %-24s %9.1f  (phrase not in the manuscript)"
              % (label[:32], phrase[:24], value))

    print("\narchitecture medians now: %s" % ", ".join("%.0f" % med[c] for c in ARCH))
    print("G-MSDERIVED: %s" % ("PASS" if not fails else "FAIL"))
    for label, phrase, value, nums in fails:
        if nums:
            print("  %s: manuscript prints %r, model gives %.1f" % (label, phrase, value))
        else:
            print("  %s: the manuscript no longer contains %r, so nothing checks the model's "
                  "%.1f -- re-point this check at the new wording" % (label, phrase, value))

    if negative_control:
        # Both probes are asserted present above before being perturbed, so neither can go inert.
        # the perturbed count must make the Section 8 pin fail, whichever wording the document carries and
        # whether the gate reports it as a wrong number or as a vanished phrase (both are failures)
        fired = any(f[0].startswith("count clearing 25, unstirred -> RCE (Sec 8)") for f in fails)
        # the second probe is the Sec 8.2 steady state, whose phrase the control rewrites; the
        # "88-89" probe it used to look for left the manuscript when sigma became derived.
        gone = any(not f[3] and _tss.replace("reaches ", "") in f[1] for f in fails)
        print("\nnegative control: rewrote 'rises from 12 to 36 of 50' as '... 12 to 41 of 50',"
              " and rewrote the Sec 8.2 steady-state phrase outright")
        print("  wrong-number branch fired: %s" % fired)
        print("  deleted-phrase branch fired: %s" % gone)
        if not (fired and gone):
            raise AssertionError("negative control did not fire on both (wrong number %s, "
                                 "deleted phrase %s)" % (fired, gone))
        return
    if fails:
        raise AssertionError("; ".join(f[0] for f in fails))


if __name__ == "__main__":
    main(negative_control="--negative-control" in sys.argv)
