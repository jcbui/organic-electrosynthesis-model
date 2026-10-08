"""Every thermal number the SI PROSE prints must equal what the model computes today.

    cd Section4_Model && python data/check_si_derived.py
    cd Section4_Model && python data/check_si_derived.py --negative-control

WHY THIS EXISTS
---------------
data/check_ms_numbers.py and data/check_ms_derived.py gate the MANUSCRIPT. Nothing gated the SI,
and the SI is where most of these numbers actually live: §S6.1 quotes the Fig. K ceilings, §S9
quotes the conductivities and their flip margins, and both are typed literals inside make_si.js
and build_param_tables.py rather than computed at build time.

The cost of that gap, measured on 2026-08-22: when MeCN went 18.9 -> 19.95 mS cm-1 (measured) and
the aqueous reference 178 -> 174.5, the artwork re-rendered, every artwork gate passed, and
EIGHTEEN numbers plus two provenance statements were left behind in the SI -- including "none is
measured", which the registry census on the same page contradicted. The registry's own history
string had already been restated once for the identical reason after the previous promotion. A
number that has gone stale twice by the same mechanism is not an accident; it is an ungated one.

WHAT IT ASSERTS AGAINST
-----------------------
figs/thermal_model.py, re-solved here -- NOT results/figK_thermal.json. The JSON is what the
figure was drawn from, so checking the caption against it would only prove the caption matches
the picture. Re-solving is a second code path: it catches a stale JSON too.

A phrase that has GONE MISSING is a FAILURE, not a skip. The two Fig. 5a checks in
check_ms_derived.py silently stopped checking anything the moment v28 reworded the sentence they
matched, and reported PASS while covering nothing.
"""
import os
import re
import sys
import unicodedata
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "figs"))
import thermal_model as TM                                              # noqa: E402

SI = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")
SOL = {n: (k, Tb) for n, _, k, Tb, _ in TM.SOLVENTS}
RX = {r[0].replace("\n", " "): r for r in TM.REACTORS}
DES = {k: v[4] for k, v in RX.items()}          # each architecture at its own transport ceiling
BEAKER, FLOW = "unstirred batch", "recirculating flow"
MICRO, STACK = "microfluidic 25 $\\mu$m", "zero-gap PEM stack"


def si_text():
    x = zipfile.ZipFile(SI).read("word/document.xml").decode("utf8")
    from docx_text import mark_subscripts                       # a subscript run reads as "_" + text (2026-09-11 convention)
    return unicodedata.normalize("NFKC", re.sub("<[^>]+>", "", mark_subscripts(x)))


def ceiling(sol, reactor, kappa=None, sigma=None):
    _, gap, sg, h_int, i_des = RX[reactor]
    k, Tb = SOL[sol]
    return TM.i_boil(kappa if kappa is not None else k, gap, Tb,
                     TM.U_passive(sigma if sigma is not None else sg, h_int)), i_des


def kappa_at(sol, reactor, target):
    """The conductivity at which this reactor's ceiling passes `target` mA cm-2."""
    lo, hi = 1e-4, 1e3
    for _ in range(120):
        mid = (lo + hi) / 2
        if ceiling(sol, reactor, kappa=mid)[0] > target:
            hi = mid
        else:
            lo = mid
    return lo


def main(negative_control=False):
    si = si_text()
    if negative_control:
        # Perturb the MODEL, not the text. Editing a number out of the prose only makes the
        # literal phrase absent, which exercises the GONE branch; the failure this gate exists
        # to catch is the opposite -- the model moves and the prose does not, which is exactly
        # what a conductivity promotion does. So push the aqueous conductivity 10% and leave
        # the SI alone.
        k, Tb = SOL["aq. NaOH"]
        SOL["aq. NaOH"] = (k * 1.10, Tb)
    checks = []

    def want(label, phrase, *values, tol=0.75):
        checks.append((label, phrase, list(values), tol))

    b = {s: ceiling(s, BEAKER)[0] for s in SOL}
    want("S6.1 beaker ceilings",
         "boils at %.0f, MeCN at %.0f, DMF at %.0f and aqueous NaOH at %.0f"
         % (b["THF"], b["MeCN"], b["DMF"], b["aq. NaOH"]),
         b["THF"], b["MeCN"], b["DMF"], b["aq. NaOH"])
    want("S6.1 transport binds first in the beaker",
         "the unstirred beaker reaches only %.1f mA cm−2 on transport grounds, where even THF has "
         "a margin of %.2f×" % (DES[BEAKER], b["THF"] / DES[BEAKER]),
         DES[BEAKER], b["THF"] / DES[BEAKER], tol=0.055)       # the sentence prints one decimal
    want("S6.1 rotating transport ceilings",
         # GENERATED (2026-10-05): the typed "108 and 122" read as a vanished phrase the moment the matrix
         # moved, although make_si.js interpolates both -- a pin that types its expectation fails on every
         # legitimate model change.
         "the highest in the model at %.0f and %.0f mA cm−2"
         % (DES["RDE 1600 rpm"], DES["rotating cyl. 3000 rpm"]),
         DES["RDE 1600 rpm"], DES["rotating cyl. 3000 rpm"], tol=1.0)
    _rd = (min(ceiling(x, "RDE 1600 rpm")[0] for x in ("THF", "MeCN", "DMF")) / DES["RDE 1600 rpm"],    # pass 8: over all three organics
           max(ceiling(x, "RDE 1600 rpm")[0] for x in ("THF", "MeCN", "DMF")) / DES["RDE 1600 rpm"])
    want("S6.1 rotating disc margins", "margins %.2f–%.2f× at the disc" % _rd, *_rd, tol=0.02)
    _rc = (min(ceiling(x, "rotating cyl. 3000 rpm")[0] for x in ("THF", "MeCN", "DMF")) / DES["rotating cyl. 3000 rpm"],    # pass 8: over all three organics
           max(ceiling(x, "rotating cyl. 3000 rpm")[0] for x in ("THF", "MeCN", "DMF")) / DES["rotating cyl. 3000 rpm"])
    want("S6.1 rotating cylinder margins", "and %.2f–%.2f× at the cylinder" % _rc, *_rc, tol=0.02)
    want("S6.1 microfluidic clears THF", "by %.2f× in THF" % (ceiling("THF", MICRO)[0] / DES[MICRO]),
         ceiling("THF", MICRO)[0] / DES[MICRO], tol=0.02)
    want("S6.1 DMF across architectures",
         "for DMF it runs " + ", ".join("%.0f" % ceiling("DMF", r)[0] for r in RX),
         *[ceiling("DMF", r)[0] for r in RX], tol=1.0)
    # Table S7f's MeCN row prints the whole margin series against each architecture's own
    # transport ceiling; every one of those numerals is a model output and is asserted here.
    _MEC = [a for a in RX if "zero-gap" not in a]
    want("S7f MeCN margin series",
         ", ".join("%s %.2fx" % (a.replace("$\\mu$m", "um"), ceiling("MeCN", a)[0] / DES[a]) for a in _MEC),
         *[ceiling("MeCN", a)[0] / DES[a] for a in _MEC], tol=0.02)
    # pass 7: generated from the re-solve (it was typed, and the derived H_EXT moved every factor)
    _zg = [DES[STACK] / ceiling(s_, STACK)[0] for s_ in ("THF", "MeCN", "DMF", "aq. NaOH")]
    want("S6.1 zero-gap shortfall",
         "by factors of %.1f× (THF), %.1f× (MeCN), %.1f× (DMF), %.1f× (aqueous NaOH)" % tuple(_zg),
         *_zg, tol=0.3)
    # ---- holes found by G-COVER (data/audit_number_coverage.py) on 2026-08-30 -----------
    # Each of these was a PARTIAL PAIR: the SI prints two numbers in one clause and only one of
    # them was asserted. Trap 9, three more instances.
    _U = {n.replace("\n", " "): TM.U_passive(sig, hint) for n, gap, sig, hint, idz in TM.REACTORS}
    want("S6.2 passive duties, centimetre-gap + microfluidic",
         "%.4f W cm−2 K−1 for the centimetre-gap cells at σ = %.2f, %.4f for the microfluidic "
         "chip at σ = 7.0 and only %.4f for an interior cell of a stack"
         % (_U["recirculating flow"], TM.SIGMA_BEAKER, _U["microfluidic 25 $\\mu$m"],
            _U["zero-gap PEM stack"]),
         _U["recirculating flow"], _U["microfluidic 25 $\\mu$m"],
         _U["zero-gap PEM stack"], tol=0.0002)
    # the PEM thermodynamic cross-check is plain arithmetic and states both legs; assert both
    want("S6 PEM thermodynamic check",
         "at 2 A cm−2 and 1.9 V against a 1.48 V thermoneutral voltage generates 0.84 W cm−2",
         2.0 * (1.9 - 1.48), tol=0.01)
    want("S6 PEM thermodynamic check, 3 A",
         "at 3 A cm−2 and 2.1 V, 1.9 W cm−2", 3.0 * (2.1 - 1.48), tol=0.06)
    # RETIRED 2026-09-12. This pinned the paragraph that apologised for LEAVING the rotating disc
    # and rotating cylinder out of the thermal analysis and estimated what they would have shown.
    # Both are modelled architectures now, with their own rows in Fig. K(b) and their own pins
    # above, so the paragraph and its estimate are gone. The quantity it protected -- the aqueous
    # ceiling of a 2 cm cell at stirred-beaker cooling -- is published directly as the stirred
    # batch ceiling and is asserted by "S6.1 beaker ceilings" and its stirred companion.
    # the kappa(T) bracket prints its DMF pair in both the beaker and the microfluidic; 535 was
    # asserted and 994 was not, and both had been computed on the retired boiling points
    import json as _json
    with open(os.path.join(ROOT, "results", "figK_kappaT_sensitivity.json"),
              encoding="utf-8") as _fh:
        _ktall = _json.load(_fh)["solvents"]
    _kt = _ktall["DMF"]
    # The geometry of BOTH rows is read from the reactor table, never typed: this pin carried a
    # hardcoded gap of 2.5e-4 m -- the retired 250 um illustration -- and so re-derived, and
    # passed on, a ceiling the model had stopped producing (trap 14).
    _beaker, _micro = RX[BEAKER], RX[MICRO]
    _Ub = TM.U_passive(_beaker[2], _beaker[3])
    _Um = TM.U_passive(_micro[2], _micro[3])

    def _pair(sol, reactor, U):
        """(25 C ceiling, boiling-point ceiling) for one solvent in one reactor."""
        j = _ktall[sol]
        return (TM.i_boil(j["kappa_25C_S_per_m"], reactor[1], j["T_boil_C"], U),
                TM.i_boil(j["kappa_25C_S_per_m"] * j["kappa_factor_at_Tboil"],
                          reactor[1], j["T_boil_C"], U))

    _bk = {sol: _pair(sol, _beaker, _Ub) for sol in ("THF", "MeCN", "DMF", "aq. NaOH")}
    want("S6.3 beaker bracket, all four solvents",
         "then move from %.0f to %.0f, %.0f to %.0f, %.0f to %.0f and %.0f to %.0f"
         % tuple(v for sol in ("THF", "MeCN", "DMF", "aq. NaOH") for v in _bk[sol]),
         *[v for sol in ("THF", "MeCN", "DMF", "aq. NaOH") for v in _bk[sol]], tol=1.0)
    _md = _pair("DMF", _micro, _Um)
    want("S6.3 DMF kappa(T) pair, beaker + microfluidic",
         "(%.0f → %.0f mA cm−2 in the beaker, %.0f → %.0f mA cm−2 in the microfluidic)"
         % (_bk["DMF"][0], _bk["DMF"][1], _md[0], _md[1]),
         _bk["DMF"][0], _bk["DMF"][1], _md[0], _md[1], tol=1.5)
    # G-COVER, 2026-08-30: the S5.5 Hofmann sentence prints a floor, a ceiling and their ratio,
    # and NONE of the three was asserted. Its ceiling had drifted 335 -> 314 and the ratio
    # x16 -> x15 without anything noticing.
    import csv as _csv
    with open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"), encoding="utf-8") as _fh:
        _med = [r for r in _csv.DictReader(_fh)
                if "Hofmann" in r["reaction"] and r["reactor"] == "Stirred batch"]
    if _med:
        _f = float(_med[0]["i_tier0_mAcm2"]); _e = float(_med[0]["i_ec_mAcm2"])
        want("S5.5 Hofmann stirred floor + ceiling",
             "from a %.0f mA cm−2 floor to %.0f mA cm−2" % (_f, _e), _f, _e, tol=1.0)   # the SI computes this sentence (2026-09-07)
        # 2026-10-07: at the measured constant (3.3 M-1 s-1) the stirred Hofmann cell is kinetic with the amide drawn down,
        # not exhausted; the amplification, the reaction layer and the wall depletion are each read from the matrix
        import re as _re
        _xk = float(_med[0]["xk_um"]); _cs = float(_re.search(r"c_sub/cb ([0-9.eE+-]+)", _med[0]["limiter"]).group(1))
        want("S5.5 Hofmann amplification", "mA cm−2 (×%.0f), with the amide" % (_e / _f), _e / _f, tol=0.6)
        want("S5.5 Hofmann reaction layer", "turns its mediator over in a %.0f μm reaction layer" % _xk, _xk, tol=0.6)
        want("S5.5 Hofmann wall depletion", "drawn down to %.1f %% of bulk at the wall" % (100 * _cs), 100 * _cs, tol=0.06)
    # S5.2's Hofmann/unstirred passage is computed in the SI since 2026-09-07 (it had typed the 300 um
    # values -- delta/x_k 128, floor 6.95, ceiling 104.7 -- for two film changes). At the 228 um film the
    # matrix gives delta/x_k 97, a commuting bound of 9.14 mA cm-2, a resolved 137.8 mA cm-2 and an
    # amplification of 15.1; every one is read from the matrix here, and the numerals above are the
    # vintage record, not the expectation.
    # 2026-10-07: since the Hofmann row took its measured constant, the stiffest cell S5.2 names is the anisole bromination
    # in the unstirred beaker; its numbers are read from the matrix here, as the Hofmann ones were.
    with open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"), encoding="utf-8") as _fh:
        _un = [r for r in _csv.DictReader(_fh)
               if "electrophilic bromination" in r["reaction"] and r["reactor"] == "Unstirred batch"]
    if _un:
        _ut0 = float(_un[0]["i_tier0_mAcm2"]); _uec = float(_un[0]["i_ec_mAcm2"])
        _udx = float(_un[0]["delta_um"]) / float(_un[0]["xk_um"])
        want("S5.2 stiffest cell delta/x_k", "at its measured rate constant, with δ/x_k = %.0f" % _udx, _udx, tol=0.6)
        want("S5.2 stiffest cell floor", "commuting bound of %.2f mA cm−2" % _ut0, _ut0, tol=0.006)
        want("S5.2 stiffest cell ceiling + ratio",
             "resolves it at %.1f mA cm−2, %.2f times" % (_uec, _uec / _ut0), _uec, _uec / _ut0, tol=0.06)
    # ---- 2026-09-14: the S6/S3.2/Table S4 thermal numbers that had been TYPED on the retired
    # sigma = 12.5 (U' 0.0144/0.0160, T_ss 187 C, flip 11.15 / 1.27x, 12.9x / 20.0x, 2.05x at the
    # cylinder) are generated from figK_thermal.json now; these pins re-solve them here from
    # thermal_model.py, the second code path, so the prose cannot drift from the model again.
    want("S6 passive U' beaker, still air -> stirred",
         "for a 100 mL beaker in still air, rising only to %.4f" % _U["stirred batch"],
         _U["stirred batch"], tol=0.00006)
    want("S6.1 beaker U' at the derived sigma",
         "so σ = %.2f and U′ = %.4f W cm−2 K−1" % (TM.SIGMA_BEAKER, _U["unstirred batch"]),
         TM.SIGMA_BEAKER, _U["unstirred batch"], tol=0.006)
    _gapb = RX[BEAKER][1]
    _kd = SOL["DMF"][0]
    _tss = TM.T_ss(100.0, _kd, _gapb, _U["unstirred batch"])
    want("S6 DMF worked example steady state", "passive steady state at T_ss ≈ %.0f °C" % _tss, _tss, tol=0.6)
    _lo, _hi = 1e-3, 1e3
    for _ in range(200):
        _m = (_lo * _hi) ** 0.5
        if TM.T_ss(100.0, _m, _gapb, _U["unstirred batch"]) > SOL["DMF"][1]:
            _lo = _m
        else:
            _hi = _m
    _kflip = (_lo * _hi) ** 0.5 * 10
    want("S6 DMF T_ss flip", "boiling point at κ = %.2f mS cm−1, a margin of %.2f×" % (_kflip, _kflip / (_kd * 10)),
         _kflip, _kflip / (_kd * 10), tol=0.02)
    _dfail = sorted(((kappa_at("DMF", a, DES[a]) / _kd, a) for a in RX
                     if "zero-gap" not in a and ceiling("DMF", a)[0] < DES[a]))
    want("S3.2 DMF binding kappa-axis verdict",
         "its binding verdict (the rotating disc) reverses at %.2f×" % _dfail[0][0], _dfail[0][0], tol=0.01)
    _thf_rde = kappa_at("THF", "RDE 1600 rpm", DES["RDE 1600 rpm"]) * 10
    want("S3.2 THF rotating-disc reversal", "rotating-disc reversal at %.1f mS" % _thf_rde, _thf_rde, tol=0.06)
    # the registry writes ASCII units, so the pin must not carry a typographic minus
    _mf = kappa_at("MeCN", "RDE 1600 rpm", DES["RDE 1600 rpm"]) * 10
    _mc = kappa_at("MeCN", "rotating cyl. 3000 rpm", DES["rotating cyl. 3000 rpm"]) * 10
    want("S9 MeCN flip", "reverse only at %.1f mS" % _mf, _mf, tol=0.05)
    want("S9 MeCN flip, rotating cylinder", "and %.1f mS" % _mc, _mc, tol=0.05)
    want("S9 MeCN kappa", "0.25 M Bu4NBF4 (κ = 19.95 mS cm−1)", SOL["MeCN"][0] * 10, tol=0.01)
    want("S9 DMF kappa", "0.2 M NaI (κ = %.2f mS cm−1)" % (SOL["DMF"][0] * 10), SOL["DMF"][0] * 10, tol=0.01)
    want("S9 aqueous kappa", "1 M NaOH (κ = 174.5 mS cm−1, interpolated between two measured points of the Dorn isotherm)", SOL["aq. NaOH"][0] * 10, tol=0.01)

    if negative_control:
        si = si.replace("MeCN (438, 0.88×)", "MeCN falls short")

    fails, oks, gone = [], [], []
    for label, phrase, values, tol in checks:
        if phrase not in si:
            gone.append((label, phrase))
            fails.append((label, phrase, None))
            continue
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", phrase)]
        missed = [v for v in values if not any(abs(n - v) <= tol for n in nums)]
        (fails if missed else oks).append((label, phrase, missed))

    print("re-solved from figs/thermal_model.py (a second code path, not results/*.json)\n")
    print("%-32s %-52s" % ("claim", "phrase in the SI"))
    for label, phrase, _ in oks:
        print("  ok   %-30s %s" % (label[:30], phrase[:64]))
    for label, phrase, missed in fails:
        tag = "GONE" if missed is None else "FAIL"
        print("  %s %-30s %s" % (tag, label[:30], phrase[:64]))
        if missed:
            print("         model gives %s" % ", ".join("%.2f" % v for v in missed))

    print("\nG-SIDERIVED: %s" % ("PASS" if not fails else "FAIL"))
    for label, phrase, missed in fails:
        if missed is None:
            print("  %s: the SI no longer contains %r, so nothing checks it -- re-point this "
                  "check at the new wording" % (label, phrase))
        else:
            print("  %s: the SI prints %r but the model gives %s"
                  % (label, phrase, ", ".join("%.2f" % v for v in missed)))

    if negative_control:
        # RE-POINTED 2026-09-13. Both branches used to test the SHAPE of the failure -- a
        # wrong-number FAIL carrying "aqueous NoOH", and a GONE on one literal phrase. Since the
        # pins generate their phrases from the model, a model perturbation now makes the
        # GENERATED phrase absent from the SI, so it lands in the GONE branch instead. Testing
        # for the old shape made the control report BAD while the gate was working perfectly --
        # CLAUDE.md trap 10, aimed at a control. What matters is that perturbing the model makes
        # the affected claims fail AT ALL, by whichever branch.
        touched = [lab for lab, p, m in fails if "aqueous NaOH" in p or "NaOH" in lab]
        touched += [lab for lab, p in gone if "aqueous NaOH" in p or "NaOH" in lab]
        fired = len(touched) > 0
        print("\nnegative control: pushed kappa(aq. NaOH) up 10% in the MODEL with the SI text "
              "untouched -- every claim that reads that conductivity must stop matching")
        print("  claims that fired: %s" % (", ".join(sorted(set(touched))) or "NONE"))
        print("G-SIDERIVED control: %s (%d claim(s) fired, %d total failure(s))"
              % ("GOOD" if fired else "BAD -- test is inert", len(set(touched)),
                 len(fails) + len(gone)))
        if not fired:
            raise AssertionError("negative control did not fire: a 10%% move in a published "
                                 "conductivity left every SI claim matching, which means this "
                                 "gate cannot see a promotion moving out from under the prose")
        return
    if fails:
        raise AssertionError("; ".join(f[0] for f in fails))
    print("  %d SI claims re-solved and matched" % len(oks))


if __name__ == "__main__":
    main(negative_control="--negative-control" in sys.argv)
