"""Master parameter-provenance registry for the Section 4 transport model.

Emits parameters_provenance.csv: EVERY parameter used anywhere in the model --
physical constants, solvent properties, Le Bas increments, estimation-method
constants, diffusion coefficients (solver species), concentrations, Henry/
solubility anchors, electrolyte conductivities, reactor geometry and correlation
constants, electrode-kinetics stack, thermal properties, cooling coefficients,
§S6 architecture constants, homogeneous rate constants, and numerical settings.

=============================================================================
PROVENANCE STANDARD (2026-08). See docs/PROVENANCE_STANDARD.md.
Every number ends in EXACTLY ONE of three states. There is no fourth.

  measured   (state A) -- a specific external source WITH a locator: author /
              journal / year / volume / page, or handbook + edition + section,
              page or table. A reviewer must be able to open the source and see
              the number. "CRC Handbook" alone is NOT sufficient.
  derived    (state B) -- computed by an explicitly named, citable method from
              inputs that are themselves state A or B. The method carries a
              citation with locator and the arithmetic is reproducible from this
              registry alone.
  assumption (state C) -- no source exists, or none could be page-anchored.
              MUST carry a sensitivity statement: the range tested and the
              conclusion that depends on it. If a conclusion flips inside the
              range, the conclusion is softened or cut in the SI.

The class "lit-representative" is ABOLISHED: it meant "a plausible magnitude for
this class of system", which is indistinguishable from an invented number to a
hostile reviewer. The class "correlation-est" is folded into derived; the class
"numerical" is folded into assumption (solver settings are declared choices,
with the audit gate that bounds them quoted as the sensitivity).

Two new columns:
  locator     -- page / section / table / equation. Empty ONLY for derived and
                 assumption rows.
  sensitivity -- REQUIRED on every assumption row: the range tested and the
                 conclusion it threatens. Also used on measured/derived rows to
                 record a residual exposure.

NEVER invent or guess a citation. Where no source could be page-anchored in the
sourcing pass, the row is routed to assumption and the pull needed to upgrade it
is named explicitly in method_note. A wrong citation is far worse than a
declared assumption.
=============================================================================

Per-reaction carrier D, C, and n live in Table S2 (reactions_50.csv) with their
own provenance strings; the k values live in Table S6 with citations. This file
covers everything else, plus the shared method constants those tables rely on.
"""
import csv
import io
import json as _json
import os as _os

# The kappa(T) bracket numbers in the Ea row below used to be TYPED. They were computed on the
# pre-CRC boiling points, and when those moved on 2026-08-30 the row went on asserting a flip at
# "440 -> 563" while the model gave 438 -> 560 -- and S6.3 of the SI, which quotes the same pair,
# had been corrected. The registry and the SI section disagreed about one number in the same
# document. Read them (trap 10: never type an expectation you could derive).
_KT_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "figK_kappaT_sensitivity.json")
with io.open(_KT_PATH, encoding="utf8") as _fh:
    _KT = _json.load(_fh)
_TG_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "thermal_geometry_sensitivity.json")
with io.open(_TG_PATH, encoding="utf8") as _fh:
    _TG = _json.load(_fh)   # G-THERMGEO: what the unsourced gap and sigma are worth
_TG_COND = _TG["conditional_on_inherited_gap"]
_TG_CSIG = _TG["conditional_on_sigma"]
_TG_ROWS = _TG["rows"]
import sys as _sys_tg
_sys_tg.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "figs"))
import thermal_model as _TM_TG
_TG_SIGMA_B = _TM_TG.SIGMA_BEAKER
_TG_SENS_SIGMA = (
    "Swept as a breaking point rather than as a band, because no source states the "
    "heat-rejection area of these cells. sigma is the OTHER unsourced geometric term, and it is "
    "the tighter of the two: %d verdicts reverse within a factor of 2.5 of the declared value "
    "(%s). A cell with twice the outer surface per unit of electrode area is an ordinary "
    "variation, so these are published as conditional on the declared geometry rather than "
    "as findings. Everything that CLEARS needs sigma to fall by a factor of %.0f to %.0f before it "
    "would boil, and the tetrahydrofuran failure at the rotating cylinder needs a factor of %.0f, "
    "so the robust half of the section is robust on this axis too. ONE of the four has external corroboration, and it runs in the safe direction: the parallel H-cell of Table S5 is built from two polycarbonate compartments of 2 x 2 x 0.22 in with a 1 cm2 cathode (Lobaccaro, Singh, Clark, Kwon, Bell & Ager, Phys. Chem. Chem. Phys. 2016, 18, 26777-26785, and its supporting information), which gives 74.3 cm2 of outer surface over 1 cm2 of electrode, i.e. sigma = 74.3 against the %.2f this model carries. The value used here is therefore conservative for that cell by a factor of %.1f, and adopting the sourced one would only widen a margin that already clears. It is NOT adopted, because one exemplar body is not the archetype and because that body is polycarbonate, whose wall conduction the balance omits (see the wall-conduction row). The other two rows on this value have no published body geometry at all, so they keep the beaker value."
    % (len(_TG_CSIG),
       "; ".join("%s in %s at %.2fx" % (c["arch"], c["solvent"], c["flips_at_sigma_x"])
                 for c in _TG_CSIG),
       min(1.0/r["sigma_flip_x"] for r in _TG_ROWS if r["verdict"] == "survives" and r["sigma_flip_x"]),
       max(1.0/r["sigma_flip_x"] for r in _TG_ROWS if r["verdict"] == "survives" and r["sigma_flip_x"]),
       [r["sigma_flip_x"] for r in _TG_ROWS if r["arch"].startswith("rotating cyl") and r["solvent"] == "THF"][0],
       _TG_SIGMA_B, 74.3 / _TG_SIGMA_B))
# The MeCN row used to state its Fig. 7 margins against two reactors that no longer exist (a 5 mm
# flow cell and a 250 um microfluidic) and a declared 500 mA cm-2. They are computed here from the
# same module the figure draws from, together with the conductivity at which each verdict would
# reverse, so that sentence cannot outlive an architecture set again.
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                                  "figs"))
import thermal_model as _TM


def _kappa_reversal(gap, sig, hint, Tb, i_des):
    """Conductivity at which this cell's verdict for this solvent crosses over, or None."""
    U = _TM.U_passive(sig, hint)
    f = lambda k: _TM.i_boil(k, gap, Tb, U) / i_des - 1.0
    lo, hi = 1e-3, 1e4
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo * hi) ** 0.5
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo * hi) ** 0.5


_MECN = [r for r in _TM.SOLVENTS if r[0] == "MeCN"][0]
_MECN_M, _MECN_X = [], []
for _rl, _L, _sg, _hi, _iop in _TM.REACTORS:
    _nm = _rl.replace("\n", " ").replace("$\\mu$m", "um")
    _U = _TM.U_passive(_sg, _hi)
    _MECN_M.append((_nm, _TM.i_boil(_MECN[2], _L, _MECN[3], _U) / _iop))
    _x = _kappa_reversal(_L, _sg, _hi, _MECN[3], _iop)
    if _x is not None and _x > _MECN[2]:
        _MECN_X.append((_nm, _x * 10.0, _x / _MECN[2]))
# -- THERMAL FACTS, COMPUTED ONCE FROM THE REACTOR TABLE ---------------------------------------
# 2026-09-12. Ten category-6/8/9 sensitivities still described the ladder v94 retired -- declared
# design currents of 50/100/500 mA cm-2, a "5 mm flow cell", a "250 um microfluidic", "FIVE of the
# seven archetypes" -- and three were not merely stale but FALSE at the current operating point.
# Every one of those sentences was typed. They are computed here instead, from the reactor table,
# so the ladder is written down in exactly one place. G-THERMROWS fails the build if a retired
# operating point reappears in a shipped column.
_TH_RX = [(lab.replace("\n", " ").replace("$\\mu$", "u"), gap, sig, hi, ides)
          for lab, gap, sig, hi, ides in _TM.REACTORS]
_TH_SOL = [(lab, kap, tb) for lab, _el, kap, tb, _pv in _TM.SOLVENTS]
_TH_OPEN = [r for r in _TH_RX if not ("microfluidic" in r[0] or "zero-gap" in r[0])]


def _th_ceiling(kap, tb, r):
    return _TM.i_boil(kap, r[1], tb, _TM.U_passive(r[2], r[3]))


def _th_margin(kap, tb, r):
    return _th_ceiling(kap, tb, r) / r[4]


def _th_fails(rows):
    """(architecture, solvent, margin) for every cell that boils before its transport ceiling."""
    return [(r[0], sl, _th_margin(k, tb, r))
            for r in rows for sl, k, tb in _TH_SOL if _th_margin(k, tb, r) < 1.0]


def _th_by_solvent(sl):
    return [(k, tb) for lab, k, tb in _TH_SOL if lab == sl][0]


_TH_NCELL = len(_TH_RX) * len(_TH_SOL)
import math as _math
_FILL_M = _TM._FILL_M
_TH_MIC = [r for r in _TH_RX if "microfluidic" in r[0]][0]


def _dmf_tss():
    """Passive steady state of the DMF beaker worked example at 100 mA cm-2. Typed as 187 C until
    2026-09-13; it moves with sigma, and the derived sigma raised it to 228 C."""
    b = _TH_RX[0]
    return _TM.T_ss(100.0, 0.877, b[1], _TM.U_passive(b[2], b[3]))


def _dmf_flip():
    """The kappa at which that steady state falls back to DMF's boiling point (S/m)."""
    b = _TH_RX[0]
    lo, hi = 1e-3, 1e3
    for _ in range(200):
        m = (lo*hi)**0.5
        if _TM.T_ss(100.0, m, b[1], _TM.U_passive(b[2], b[3])) > 152.8:
            lo = m
        else:
            hi = m
    return (lo*hi)**0.5


def _thf_flip(arch):
    """The multiple of the carried 3.0 mS cm-1 at which THF stops boiling in `arch`.

    Typed as 12.9x and 20.0x until 2026-09-13; both move with sigma, and the derived sigma raised
    them to 16.5x and 25.7x, so they are computed here.
    """
    r = [x for x in _TH_RX if x[0] == arch][0]
    lo, hi = 1e-4, 1e3
    for _ in range(200):
        m = (lo*hi)**0.5
        if _TM.i_boil(m, r[1], 66.0, _TM.U_passive(r[2], r[3])) > r[4]:
            hi = m
        else:
            lo = m
    return ((lo*hi)**0.5)/0.30
_TH_STACK = [r for r in _TH_RX if "zero-gap" in r[0]][0]


def _kappa_multiple(kap, tb, arch):
    """Multiple of the carried kappa (S/m) at which the verdict of `arch` reverses (2026-09-14).

    Above 1 for a cell that boils before its transport ceiling, below 1 for one that clears.
    The DMF row typed 0.87x/0.70x and a binding 2.05x at the rotating cylinder, all computed on
    the retired sigma = 12.5; at the derived sigma the binding reversal is the rotating disc.
    """
    r = [x for x in _TH_RX if x[0] == arch][0]
    U = _TM.U_passive(r[2], r[3])
    lo, hi = 1e-5, 1e4
    for _ in range(200):
        m = (lo*hi)**0.5
        if _TM.i_boil(m, r[1], tb, U) > r[4]:
            hi = m
        else:
            lo = m
    return ((lo*hi)**0.5)/kap


_DMF_FAILS = sorted([(r[0], _th_margin(0.877, 152.8, r), _kappa_multiple(0.877, 152.8, r[0]))
                     for r in _TH_RX if r is not _TH_STACK and _th_margin(0.877, 152.8, r) < 1.0],
                    key=lambda t: t[2])
_DMF_BIND = _DMF_FAILS[0]


def _th_vol(sl, mL):
    """Beaker ceiling at another charge volume: A_ext ~ V^(2/3), and sigma scales with it."""
    k, tb = _th_by_solvent(sl)
    b = _TH_RX[0]
    return _TM.i_boil(k, b[1], tb, _TM.U_passive(b[2] * (mL / 100.0) ** (2.0 / 3.0), b[3]))


# The worst open-vessel fail, for the evaporative-loss bound. Selected from the model, never named:
# until 2026-09-12 that row said "the one fail in an open vessel is THF in the unstirred beaker",
# which the transport-ceiling operating point had made false -- that cell passes at 3.60x.
_EVAP_W = min(_th_fails(_TH_OPEN), key=lambda t: t[2])
_EVAP_R = [r for r in _TH_RX if r[0] == _EVAP_W[0]][0]
_EVAP_K, _EVAP_TB = _th_by_solvent(_EVAP_W[1])
_EVAP_Q = _TM.q_Wcm2(_EVAP_R[4], _EVAP_K, _EVAP_R[1])
_EVAP_REJ = _TM.U_passive(_EVAP_R[2], _EVAP_R[3]) * (_EVAP_TB - _TM.TAMB)

_TG_SENS = ("Swept as a breaking point rather than as a band, because no source states this cell's "
            "electrode separation: %d of the %d architecture-solvent cells reverse their verdict "
            "within a factor of 2.5 of the declared gap, and all %d are acetonitrile or "
            "dimethylformamide at a rotating electrode (%s). The tetrahydrofuran verdicts at both "
            "rotating cells need a gap below about 1.6 mm to reverse, which is no longer a "
            "beaker-scale cell, and the %d architectures sharing this gap (%s) hold boil-off "
            "ceilings within %.1f pct of one another while their transport ceilings span %.1fx."
            % (len(_TG_COND), _TH_NCELL, len(_TG_COND),
               "; ".join("%s in %s at %.2fx" % (c["arch"], c["solvent"], c["flips_at_gap_x"])
                         for c in _TG_COND),
               len(_TG["shared_gap_rows"]), ", ".join(_TG["shared_gap_rows"]),
               100 * _TG["ceiling_spread_on_shared_gap"], _TG["transport_span_on_shared_gap"]))
_SX_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "schmidt_extrapolation.json")
with io.open(_SX_PATH, encoding="utf8") as _fh:
    _SX = _json.load(_fh)   # G-SCRANGE, so the Eisenberg row cannot go stale
_EX_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "excell.json")
with io.open(_EX_PATH, encoding="utf8") as _fh:
    _EX = _json.load(_fh)   # G-EXCELL: the ex-cell split the C_sat row quotes, never typed
_FC_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "free_convection_delta.json")
with io.open(_FC_PATH, encoding="utf8") as _fh:
    _FC = _json.load(_fh)   # G-FREECONV: the unstirred-film derivation and its declared inputs
_UD_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "unsourced_D_sensitivity.json")
with io.open(_UD_PATH, encoding="utf8") as _fh:
    _UD = _json.load(_fh)   # G-DSENS: the supporting-ion defaults and what perturbing them costs
_ZS_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "carrier_charge_sensitivity.json")
with io.open(_ZS_PATH, encoding="utf8") as _fh:
    _ZS = _json.load(_fh)   # G-ZSENS: what the four medium-confidence carrier charges cost
# The supporting-ion row below says "the zero is the physics"; refuse to build that sentence over a
# sweep that did not return zero (G-DSENS would fail too, but the registry must not outrun it).
if _UD.get("verdict") != "PASS" or any(v != 0 for v in _UD["max_rel_change"].values()):
    raise SystemExit("results/unsourced_D_sensitivity.json is not a clean zero (%s, %s); the "
                     "supporting-ion row's prose asserts one" % (_UD.get("verdict"), _UD["max_rel_change"]))
_relfmt = lambda x: "exactly zero" if x == 0 else "%.1e" % x
_numword = lambda n: ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][n] if 0 <= n <= 9 else str(n)

# How many reactor archetypes the model has, read from the published matrix rather than typed.
# Three sensitivity rows said "the six architectures" after the 2026-09-07 re-anchoring made it
# seven, and all three shipped into Table S7: a count of the model's own columns must never be a
# literal. The matrix is wide -- class, reaction, carrier, then one column per archetype.
with io.open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                           "julia", "tier0_ec_matrix.csv"), encoding="utf8") as _fh:
    _N_ARCH = len(_fh.readline().rstrip("\n").split(",")) - 3
assert 2 <= _N_ARCH <= 12, "implausible archetype count %r from tier0_ec_matrix.csv" % _N_ARCH
import csv as _csv
with io.open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "carrier_charge.csv"), encoding="utf8") as _fh:
    _CC = [r for r in _csv.DictReader(l for l in _fh if not l.startswith("#"))]
_CC_MED = [r for r in _CC if r["confidence"] != "high"]
_KS_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "rate_constant_sensitivity.json")
with io.open(_KS_PATH, encoding="utf8") as _fh:
    _KS = _json.load(_fh)["summary"]   # G-KSENS: what an order of magnitude in each k costs
_DSB_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                          "results", "substrate_D_sensitivity.json")
with io.open(_DSB_PATH, encoding="utf8") as _fh:
    _DSB = _json.load(_fh)   # G-DSUBSENS: what the eight substrate diffusivities cost
_CK_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "catalyst_ec_sensitivity.json")
with io.open(_CK_PATH, encoding="utf8") as _fh:
    _CK = _json.load(_fh)    # G-CATK: the eleven catalyst rows under a finite k


_CD_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "catalyst_D_sensitivity.json")
try:
    with io.open(_CD_PATH, encoding="utf8") as _fh:
        _CD = _json.load(_fh)    # G-CATD: the radius exposure of the catalyst count
except FileNotFoundError:
    _CD = None


def _cd_sentence():
    """the radius row's consequence, computed from G-CATD's artifact (2026-09-11)"""
    if not _CD:
        return "The radius sweep artifact is absent; run figs/analysis_catalyst_D_sensitivity.py."
    if _CD.get("conditional"):
        return ("At the sourced rate constants (S5.7) the ten-of-eleven count is conditional on this radius: it breaks at "
                "r_h = %.2f Angstrom on the deciding row (%s, %.1f mA cm-2 at best), inside the assigned band and above the "
                "%.2f Angstrom that size-scaling the ferrocene anchor predicts; the 1/r scaling is the k = 0 law and a bound "
                "for the sourced rows, whose kinetic-regime ceiling goes as sqrt(D) and breaks at %.2f Angstrom. The carrier "
                "dichotomy -- the central mechanistic result -- is unaffected."
                % (_CD["r_crit_from_4p5A"], _CD["deciding_row"].split(" (")[0], _CD["second_best_i_lim"],
                   _CD["r_expected_deciding_A"], _CD["r_crit_sqrt_from_4p5A"]))
    return ("All 11 catalyst-carried entries sit below 25 mA cm-2 in every architecture across the whole band; the "
            "count breaks only at r_h = %.2f Angstrom, below the %.2f Angstrom expected for the deciding row. The carrier "
            "dichotomy -- the central mechanistic result -- is unaffected." % (_CD["r_crit_from_4p5A"], _CD["r_expected_deciding_A"]))


def _ck_sci(k):
    k = float(k)
    return {1000.0: "10^3", 10000.0: "10^4", 100000.0: "10^5"}.get(k, "%g" % k)


def _ck_sentence():
    """The catalyst-class result under a finite k, in publication prose, computed from G-CATK's
    own artifact -- one function, used by both registry rows so they cannot disagree."""
    ks = [float(k) for k in _CK["k_band_M"]]; kmax = max(ks)
    surv = _CK["ten_of_eleven_survives_at_k"]
    hold = None; fail = None
    for k in ks:
        if surv["%g" % k]: hold = k
        else: fail = k; break
    top = _CK["per_k"]["%g" % kmax]
    capped = top["cells_at_substrate_cap"]; ncells = top["cells"]
    w = _CK["walls"]
    if fail is None:
        core = "no catalyst row clears 25 mA cm-2 at any k up to %s M-1 s-1" % _ck_sci(kmax)
    else:
        core = ("the ten-of-eleven result holds for k <= %s M-1 s-1 and fails at k = %s, where %d of the "
                "eleven clear 25 mA cm-2 by k = %s" % (_ck_sci(hold), _ck_sci(fail), top["clear25"], _ck_sci(kmax)))
    ctrl = ("better than 0.01" if abs(_CK["control"]["worst_rel"]) < 1e-4
            else "%.2f" % (100 * abs(_CK["control"]["worst_rel"])))
    return ("The published matrix runs the eleven catalyst-carried rows at k = 0, the floor of the EC' current. "
            "Re-solved as EC' problems over the declared band, %s; the largest amplification in the class is "
            "%.1fx and %d of the %d cells sit at their substrate cap at the top of the band. %d of the %d finite-k "
            "cells end on a ramp wall; at the concentration-control plateau that follows, the exhausted species is at "
            "most %.2f pct of bulk at the electrode, so each is a lower bound tight to that fraction and no cell sits "
            "within its own tightness of a threshold. The k = 0 member of every sweep reproduces the published cell "
            "to %s pct (worst of %d cells)."
            % (core, top["max_amplification"], capped, ncells, w["wall_cells"], w["finite_k_cells"],
               100 * w["exhausted_fraction_max_walls"], ctrl, _CK["control"]["cells"]))



def _dsb_movement(d):
    """State what the substrate-D sweep moves, in publication prose, computed from its own artifact.

    Until 2026-09-07 this branch was the literal placeholder "A COUNT MOVES -- see results", which
    was correct only while nothing moved; the seven-archetype re-solve made it fire and the string
    shipped into Table S7. It also cannot say "see results": the SI cites no repository path.
    """
    base, moves = d["base_counts"], []
    for scale, per_arch in sorted(d["counts"].items(), key=lambda kv: float(kv[0])):
        for arch, counts in per_arch.items():
            for i, thr in enumerate((25, 50)):
                b, a = base[arch][i], counts[i]
                if a != b:
                    moves.append((float(scale), arch, thr, b, a))
    n_arch = len(base)
    if not moves:
        return ("no >=25 or >=50 count moves in any of the %d architectures" % n_arch), 0
    worst = max(abs(a - b) for _, _, _, b, a in moves)
    scales_that_move = sorted({sc for sc, _, _, _, _ in moves})
    quiet = [float(sc) for sc in d["counts"] if float(sc) not in scales_that_move]
    parts = ["the >=%d mA cm-2 count of the %s falls from %d to %d of the eight mediated rows"
             % (thr, arch, b, a) if a < b else
             "the >=%d mA cm-2 count of the %s rises from %d to %d of the eight mediated rows"
             % (thr, arch, b, a)
             for _, arch, thr, b, a in moves]
    txt = "; ".join(parts)
    txt += ", in each case only at x%s" % ", x".join("%.2f" % sc for sc in scales_that_move)
    if quiet:
        txt += ", and nothing moves at x%s" % ", x".join("%.2f" % sc for sc in sorted(quiet))
    txt += ". No count moves by more than %d entr%s of eight" % (worst, "y" if worst == 1 else "ies")
    return txt, worst
_SB_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "si_sensitivity_bounds.json")
with io.open(_SB_PATH, encoding="utf8") as _fh:
    _SB = _json.load(_fh)["transport"]   # G-SIBOUNDS: what each film's band does to its column
if "status" in _SB:
    raise SystemExit("results/si_sensitivity_bounds.json has no transport bounds (%s); the flow-film "
                     "rows interpolate theirs from it -- run the band-edge solves and "
                     "data/si_sensitivity_bounds.py first" % _SB["status"])
def _sbrow(key):
    """What a film's band does to its column, in the SI's own display convention (>= 100 mA cm-2 as a
    whole number, below that to one decimal); a band that collapses onto the value is said to."""
    m = _SB["median, " + key]; a = _SB["count >=25, " + key]; b = _SB["count >=50, " + key]
    f = lambda v: ("%.0f" % v) if v >= 100 else ("%.1f" % v)
    if f(m["lower"]) == f(m["upper"]) and a["lower"] == a["upper"] and b["lower"] == b["upper"]:
        return ("a column that does not move: a median of %s mA cm-2, %d of 50 clearing 25 mA cm-2 and %d of 50 "
                "clearing 50 at both ends" % (f(m["value"]), a["value"], b["value"]))
    return ("a median of %s-%s mA cm-2 about %s, %d-%d of 50 clearing 25 mA cm-2 about %d and "
            "%d-%d of 50 clearing 50 about %d" % (f(m["lower"]), f(m["upper"]), f(m["value"]), a["lower"], a["upper"],
                                                  a["value"], b["lower"], b["upper"], b["value"]))
_FCS = _FC["sensitivity_um"]
_FC_ENV_LO = _FCS["h_5mm"] * _FCS["drho_1e-2"] / _FC["delta_centre_um"]
_FC_ENV_HI = _FCS["h_80mm"] * _FCS["drho_1e-3"] / _FC["delta_centre_um"]
_FCI = _FC["drho_rho_illustration"]
_KT_FLIPS = _KT["verdict_flips"]
if not _KT_FLIPS:
    raise SystemExit("the Ea sensitivity prose reports which verdicts the bracket reverses; the "
                     "model now reverses none. Rewrite that paragraph rather than the number.")
# 2026-09-12: this used to REFUSE any count but one, because on the five-reactor table exactly one
# verdict was bound-dependent. On the seven-archetype table five are, and they are the same four
# rotating-electrode cells the gap sweep finds conditional plus the ANEC cell in THF --
# i.e. the marginal cells are marginal on every axis at once, which is worth saying rather than
# hiding behind a guard. The prose is generated from the list, so no count is typed.
_KT_NPAIRS = _KT["factor_range"]["n_pairs"]
_KT_WORD = {1: "single", 2: "pair of", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
            8: "eight"}.get(len(_KT_FLIPS), str(len(_KT_FLIPS)))
_KT_FLIP_PROSE = "; ".join(
    "%s in the %s (%.0f -> %.0f mA cm-2 against %.0f, margin %.2fx -> %.2fx)"
    % (_f["solvent"], _f["reactor"],
       _KT["brackets"][_f["reactor"]][_f["solvent"]]["i_boil_25C"],
       _KT["brackets"][_f["reactor"]][_f["solvent"]]["i_boil_kappaT"],
       _KT["brackets"][_f["reactor"]][_f["solvent"]]["i_design"],
       _KT["brackets"][_f["reactor"]][_f["solvent"]]["margin_25C"],
       _KT["brackets"][_f["reactor"]][_f["solvent"]]["margin_kappaT"])
    for _f in _KT_FLIPS)

R = []
def add(cat, name, value, units, pclass, method, cite, locator="", sens=""):
    assert pclass in ("measured", "derived", "assumption"), (name, pclass)
    if pclass == "measured":
        assert locator, "measured row without locator: " + name
    if pclass == "assumption":
        assert sens, "assumption row without sensitivity: " + name
    R.append(dict(category=cat, parameter=name, value=value, units=units,
                  provenance_class=pclass, method_note=method, citation=cite,
                  locator=locator, sensitivity=sens, equation=equation_for(name, method)))


# ---------------------------------------------------------------------------------------
# EQUATION CROSS-REFERENCE. Every derived number in this model comes out of one of a small
# set of named equations, and until 2026-08-22 the registry said which METHOD produced a row
# but never pointed at the equation itself, so a reader could not go from a tabulated number
# to the arithmetic that made it. The tags below are the equation numbers as they appear in
# the SI; the mapping is by the method-note wording the row already carries, so a row cannot
# claim an equation it did not use.
# ---------------------------------------------------------------------------------------
_EQ_RULES = [
    ("Wilke-Chang",                       "S2"),
    ("Le Bas",                            "S23"),
    ("Stokes-Einstein",                   "S24"),
    ("Nernst-Einstein",                   "S25"),
    ("Casteel-Amis",                      "S26"),
    ("Kohlrausch",                        "S27, S28"),
    ("Onsager",                           "S29"),
    ("Perkins-Geankoplis",                "S30"),
    ("mole-fraction rule",                "S30"),
    ("kinematic viscosity computed",      "S31"),
]


def equation_for(name, method):
    """SI equation tag(s) that PRODUCE this row.

    Matched only on the LEADING method statement, not on the whole note. The first version of
    this matched anywhere in the string and tagged 24 rows as Casteel-Amis when five use it --
    every kappa row that MENTIONS Casteel-Amis while explaining why it cannot be applied was
    picking up the tag. A row must not be able to claim an equation it argues against.
    """
    lead = ((name or "") + " || " + (method or ""))[:110].lower()
    hits = [tag for key, tag in _EQ_RULES if key.lower() in lead]
    seen, out = set(), []
    for h in hits:
        for t in h.split(", "):
            if t not in seen:
                seen.add(t); out.append(t)
    return ", ".join(out)

# -- shared citations + locators ---------------------------------------------
CRC     = "CRC Handbook of Chemistry and Physics, 97th ed. (W. M. Haynes, ed.), CRC Press, 2016"
L_VISC  = "Sect. 6, 'Viscosity of Liquids', pp. 6-243 to 6-247 (25 C column)"
L_LAB   = "Sect. 15, 'Laboratory Solvents and Other Liquid Reagents', pp. 15-13 to 15-20 (density column; superscript = reference temperature)"
# PAGE-ANCHORED 2026-08-22, which closes adversarial-review finding R1. The locator used to name
# the section and the table but no page, so it was not something a reviewer could open to. The
# full CRC 97th ed. is now in the repository (Model Papers for Params/) and the table runs across
# pp. 5-75 and 5-76. Every value these rows carry was checked against it: H+ 349.65 (D 9.311),
# OH- 198 (5.273), K+ 73.48 (1.957), Na+ 50.08 (1.334), Br- 78.1 (2.080), Cl- 76.31 (2.032),
# 1/2CO3(2-) 69.3 (0.923) i.e. 138.6 per mole, HCO3- 44.5 (1.185). The registry's own note that
# K+ was "rounded 1.957e-9 -> 1.9e-9" quotes the table's D column exactly, which is the strongest
# evidence available that these were read off the page rather than recalled.
L_VAN   = ("Sect. 5, 'Ionic Conductivity and Diffusion at Infinite Dilution' (P. Vanysek), "
           "pp. 5-75 to 5-76, aqueous limiting molar conductivities and diffusion coefficients "
           "at 25 C")
L_WATER = "Sect. 6, 'Properties of Water in the Range 0-100 C'"
L_EBULL = "Sect. 5, 'Cryoscopic and Ebullioscopic Constants'"
def L_ORG(entry): return "Sect. 3, 'Physical Constants of Organic Compounds', entry '%s'" % entry

SI9     = "BIPM, The International System of Units (SI Brochure), 9th ed., 2019"
L_SI9   = "Sect. 2.3.1, Table 1 (the seven exactly defined constants: e, N_A, k_B)"
IUPAC   = "Prohaska et al., 'Standard atomic weights of the elements 2021 (IUPAC Technical Report)', Pure Appl. Chem. 2022, 94, 573-600"
WC55    = "Wilke & Chang, AIChE J. 1955, 1, 264-270"
# The association parameters were confirmed verbatim on 2026-08-22 from the held copy of Reid
# 4th ed., p. 599: "Wilke and Chang recommend that phi be chosen as 2.6 if the solvent is water,
# 1.9 if it is methanol, 1.5 if it is ethanol, and 1.0 if it is unassociated." The same page
# prints Eq. (11-9.1) in the form this project uses.
L_WC55  = ("pp. 264-270; correlation and its recommended association parameters (2.6 water, "
           "1.9 methanol, 1.5 ethanol, 1.0 unassociated), as restated at Reid 4th ed. p. 599")
# VERIFIED 2026-08-22 against the copy now in the repository, which is the FOURTH edition
# (Reid, Prausnitz & Poling, McGraw-Hill, 1987) -- see Model Papers for Params/. The edition is
# named honestly rather than left as the 5th, because the table number differs between them and a
# reviewer opening the 5th at "Table 11-1" would not find the Le Bas increments there.
POLING  = ("Reid, Prausnitz & Poling, The Properties of Gases and Liquids, 4th ed., McGraw-Hill, "
           "1987 (the edition held and verified; the 5th ed. of Poling, Prausnitz & O'Connell, "
           "2001, carries the same increments under a different table number)")
L_PG    = "Eq. 11-9.8 (Perkins-Geankoplis mole-fraction mixing rule for phi*M)"
# CLOSES adversarial-review finding R2. Every increment below was read off the page on
# 2026-08-22: Table 3-8, p. 53, "Volume Increments for the Calculation of Molar Volumes Vb",
# Le Bas column -- C 14.8, H 3.7, O 7.4 (in acids 12.0), N 15.6 doubly bonded / 10.5 primary
# amine / 12.0 secondary amine, Br 27, Cl 24.6, F 8.7, I 37, S 25.6, and ring corrections
# -6.0 / -8.5 / -11.5 / -15.0 for three- to six-membered. All sixteen match the registry exactly.
# The locator previously read "Table 11-1", which is where the 4th edition DISCUSSES Le Bas
# volumes (Sec. 11-9 points to "the Le Bas additive volume table (3-8)") but is not where the
# increments are tabulated.
# NOT IN THIS TABLE: the phosphorus increment, which the registry carries at 27.0. Table 3-8's
# Le Bas column has no phosphorus entry, so that one row is NOT page-anchored here.
L_LEBAS = ("Table 3-8, p. 53, 'Volume Increments for the Calculation of Molar Volumes Vb', "
           "Le Bas column")
BF      = "Bard & Faulkner, Electrochemical Methods: Fundamentals and Applications, 2nd ed., Wiley, 2001"
CUSSLER = "Cussler, Diffusion: Mass Transfer in Fluid Systems, 3rd ed., Cambridge Univ. Press, 2009"
INCROP  = "Incropera, DeWitt, Bergman & Lavine, Fundamentals of Heat and Mass Transfer, 6th ed., Wiley, 2007"
NIST    = "NIST Chemistry WebBook, SRD 69, Condensed-Phase Thermochemistry"
KALUGIN = "Kalugin, Lukinova & Novikov, Kharkiv Univ. Bull. Chem. Ser. 2019, 33(56), 23-33, DOI 10.26565/2220-637X-2019-33-02 (open access)"

# Shared sensitivity strings --------------------------------------------------
S_KAPPA_DISPLAY = ("Display-only. Kappa enters no transport quantity: i_lim (Eq. S1) and the "
                   "NPP / EC-prime solvers use D, C, delta and z only. Kappa appears solely in the "
                   "voltage/thermal path (cellvoltage.jl; figs make_figK.py, make_fig4B.py, "
                   "make_figs.py Fig D, make_fig_main.py panel f). This row supports no stated "
                   "conclusion; it is tabulated for scale. Most of the registered conductivities "
                   "are in this position.")
S_DISPLAY_SOLV  = (" Display-only: this solvent system is registered but is not assigned to any of "
                   "the 50 reactions in reactions_50.csv, so it enters no reported number.")

# No row may publish a bare negation. These two name the BASIS for the rows that have no external
# source, so a reader learns what the number is instead of only that it is unsourced. The specific
# route that was tried and failed for each row stays in its method_note.
CEIL_NACL = ("Minc & Werblan, Electrochim. Acta 1962, 7, 257-266, Table 2, p. 261 "
             "(equivalent conductances of alkali perchlorates in acetonitrile at infinite "
             "dilution, 25 C), with Gong et al. Table 2 and Kalugin et al. Table 3, p. 28 -- "
             "bounds this row from above by Kohlrausch; see the method note for the two steps")
KAPPA_NOSRC = ("Declared, no external source: no measured conductivity for this exact "
               "salt/solvent/concentration was located, and the row is DISPLAY-ONLY -- kappa "
               "enters no transport quantity, so it supports no stated conclusion and is "
               "tabulated for completeness. The route attempted for this particular entry, and "
               "why it failed, is recorded in the row's method note.")
LEBAS_NOSRC = ("Declared, no external source: the phosphorus increment is not present in the "
               "Le Bas column of Table 3-8, p. 53, so it cannot be page-anchored to it. It is "
               "display-only -- no carrier in the 50-reaction set contains phosphorus.")

# -- 1. Physical constants ----------------------------------------------------
add("1. Physical constants", "Boltzmann constant kB", "1.380649e-23", "J K-1", "measured",
    "exact by the 2019 SI definition of the kelvin", SI9, L_SI9)
add("1. Physical constants", "Faraday constant F", "96485.332", "C mol-1", "derived",
    "F = e * N_A = 1.602176634e-19 C * 6.02214076e23 mol-1 = 96485.33212 C mol-1 (exact; rounded here)",
    SI9, "", "Exact; no exposure.")
add("1. Physical constants", "Gas constant R", "8.314463", "J mol-1 K-1", "derived",
    "R = kB * N_A = 1.380649e-23 * 6.02214076e23 = 8.31446262 J mol-1 K-1 (exact; rounded here)",
    SI9, "", "Exact; no exposure.")
add("1. Physical constants", "Temperature T", "298.15", "K", "assumption",
    "isothermal 25 C throughout; thermal excursions are treated explicitly and separately in S6.1",
    "declared modelling convention", "",
    "Not swept. All reported quantities are stated at 25 C and every archetype comparison is "
    "isothermal by construction. A +/-10 K excursion rescales every reaction's D by a common factor "
    "through D ~ T/mu(T) (~+/-20 pct for these solvents): the architecture ranking, the carrier "
    "dichotomy and the §S6 decompositions are ratios and are unaffected, but the absolute "
    ">=25 and >=50 mA cm-2 counts would move by a few entries. Every count reported in the SI is a "
    "25 C count.")

# -- 2. Solvent properties (Wilke-Chang inputs; nu = mu/rho feeds correlations) -
# STRUCTURAL FACTS THAT GOVERN THIS CATEGORY (both established in the sourcing pass):
#  (a) Only the PRODUCT phi*M enters Eq. S2 (build_reactions50.py:131). M and phi are never used
#      separately. For MIXTURES the tabulated "M" is therefore NOT a molar mass: it is one half of
#      a presentational split of a single Perkins-Geankoplis product. Stated explicitly so that a
#      reviewer does not read 36.4 or 26.4 g mol-1 as an invented molecular weight.
#  (b) 5 of the 20 registered solvent systems (EtOH, DMSO, AcOH, EtOH/H2O 1:1, DMF/H2O 9:1) are
#      never assigned to a reaction in reactions_50.csv and are display-only.
USED_SOLVENTS = {"MeCN","MeOH","DMF","DMA","THF","H2O","HFIP","acetone","MeNO2",
                 "MeCN/H2O 9:1 v/v","MeOH/H2O 1:1 v/v","H2O/MeCN 2:1 v/v",
                 "DMSO/THF 5:1 v/v","tAmOH/H2O 3:1 v/v","AcOH/HCOOH 1:1 v/v"}

S_MU = ("i_lim ~ D ~ 1/mu and Sc = nu/D, so mu enters twice; a +/-25 pct property error displaces "
        "log10 i_lim by +/-0.10 (Eq. S1 is linear in D). That is small against the 1-2 order-of-"
        "magnitude spreads separating the " + _numword(_N_ARCH) + " reactor archetypes, so no architecture ranking or "
        "carrier-class conclusion can move; only per-reaction entries already within ~25 pct of a "
        "threshold can cross it.")
S_RHO = ("rho enters only through nu = mu/rho and the Schmidt number; Sh ~ Sc^0.356 at the "
         "rotating cylinder, so a 5 pct rho error moves k_m by 1.8 pct.")

# DMA needs its own sensitivity: the generic +/-25 pct statement does not cover it. The handbook
# entry disagrees with the value in common use by roughly a factor of two, so the exposure has to
# be stated at that magnitude and tested there. Publication prose -- it ships into Table S7.
# 2026-09-11: what the DMA sweep MEASURES is read from its artifact, never typed (the seven sourced-k
# catalyst rows moved the Ni-XEC row to within 5 pct of 25 mA cm-2 in the thin films, and the homolog
# reading of the viscosity then carries it over -- a movement this row must declare, G-DMAMU).
_DMA_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                          "results", "dma_viscosity_sensitivity.json")
try:
    with io.open(_DMA_PATH, encoding="utf8") as _fh:
        _DMA = _json.load(_fh)
except FileNotFoundError:
    _DMA = None
_ARCHW = {"natural": "unstirred", "stirred": "stirred", "flow": "recirculating flow", "anec": "ANEC",
          "micro": "microfluidic", "rde": "RDE", "rce": "rotating cylinder"}
def _dma_moves_sentence():
    if not _DMA:
        return "The sweep artifact is absent; run data/sensitivity_dma_viscosity.py."
    mv = _DMA.get("count_moves", [])
    if not mv:
        return ("No >=25 or >=50 threshold count moves anywhere in %.3f-%.3f mPa s."
                % (_DMA["mu_alternative_not_adopted"], _DMA["mu_printed"]))
    by_mu = {}
    for m in mv:
        by_mu.setdefault(m["mu"], []).append("%s %+d" % (_ARCHW[m["arch"]], m["delta"]))
    parts = ["at %.3f mPa s the >=25 count of the %s" % (mu, ", ".join(v)) for mu, v in sorted(by_mu.items(), reverse=True)]
    return ("Inside the interval a published count does move: %s -- the kilogram-scale Ni-XEC row, carried at its "
            "sourced rate constant (S5.7), sits within 5 pct of 25 mA cm-2 in the thin-film architectures at the "
            "printed viscosity and clears it at the homolog reading. The unstirred and stirred counts, the "
            "carrier-class conclusion and the architecture ordering do not move." % "; ".join(parts))
S_MU_OVERRIDE = {"DMA": (
    "The handbook entry for this solvent stands apart from its own homolog: N,N-dimethylformamide, "
    "one methylene lighter, is printed as 0.794 mPa s in the same column of the same page, so the "
    "tabulated 1.927 mPa s makes DMA 2.4 times the more viscous of the pair where that substitution "
    "normally costs a few tens of a percent. The column assignment is not in question -- ethanol "
    "1.074, 1,4-dioxane 1.177, dimethyl sulfoxide 1.987 and diethyl ether 0.224 all read correctly "
    "at the same position -- and the handbook carries no second viscosity for DMA against which to "
    "adjudicate. The printed value is the one used -- an author ruling of 2026-08-31, on the "
    "grounds that the handbook is at least a primary source where the alternative is not. "
    "Exposure is bounded by direct test: the two "
    "DMA reactions are swept across the whole interval down to 0.927 mPa s, with i_lim rising as mu^p, p "
    "between -1 and -2/3 by archetype. " + _dma_moves_sentence())}

IAPWS_ETA = ("Huber et al., 'New international formulation for the viscosity of H2O' (IAPWS 2008), "
             "J. Phys. Chem. Ref. Data 2009, 38, 101-125")
IAPWS_RHO = ("Wagner & Pruss, 'The IAPWS formulation 1995 for the thermodynamic properties of "
             "ordinary water substance', J. Phys. Chem. Ref. Data 2002, 31, 387-535")


def _check_solvents_against_csv(rows):
    """The solvent properties live in TWO tables -- here and in data/build_reactions50.py, which
    writes data/solvents.csv and feeds the solver. They drifted: the H2O/MeCN association factor
    was corrected in one and not the other, and the MeCN and DMA viscosities were corrected here
    only after the same defect had been found twice. Assert they agree, so a future edit to one
    fails loudly instead of splitting the model from its own registry."""
    import csv as _csv, os as _os
    path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "solvents.csv")
    if not _os.path.exists(path):
        return
    csvrows = {r["solvent"]: r for r in _csv.DictReader(open(path))}
    bad = []
    for r in rows:
        name, M, mu, rho, phi = r[0], r[1], r[2], r[3], r[4]
        c = csvrows.get(name)
        if c is None:
            continue
        for lab, mine, theirs in (("M", M, c["M"]), ("mu", mu, c["mu_mPas"]),
                                  ("rho", rho, c["rho"]), ("phi", phi, c["phi"])):
            if abs(float(mine) - float(theirs)) > 1e-9:
                bad.append("%s.%s: build_param_tables %s vs solvents.csv %s" % (name, lab, mine, theirs))
    if bad:
        raise AssertionError("solvent tables have drifted from data/build_reactions50.py:\n  "
                             + "\n  ".join(bad))


# (name, M, mu, rho, phi, mu_state, mu_cite, mu_loc, rho_state, rho_cite, rho_loc, note)
PURE = [
 ("MeCN",  41.05, 0.369, 0.776, 1.0, "measured", CRC, L_VISC, "measured", CRC, L_LAB,
  "eta corrected 0.343 -> 0.369 on 2026-08-23. CRC 97th p. 6-243 prints 0.369 in the eta(25 C) "
  "column; 0.343 is on no printed CRC page -- Sect. 15 carries no printed viscosity column at "
  "all, its header stating viscosity is in the Internet version only. Column alignment was "
  "pinned by x-coordinate and cross-checked against DMF 0.794 and acetone 0.306 on the same "
  "page. Note for the reader: 0.369 is also the value usually tabulated for acetonitrile at "
  "20 C, and the widely quoted 25 C value is 0.341-0.345, so the CRC row may carry a 20 C "
  "number. That is an inference and is not acted on -- the printed value at the cited locator "
  "is what this registry carries. Consequence, since MeCN or a MeCN mixture carries 20 of the "
  "50 reactions and eta enters twice (D ~ 1/eta and Sc = nu/D): the architecture medians move "
  "from 6.2 / 17.4 / 20.2 / 50.2 / 111.7 / 127.4 to 6.0 / 17.1 / 19.4 / 48.4 / 108.3 / 121.4 mA "
  "cm-2 and the thin-gap >=50 count moves 25 -> 24 of 50. Every >=25 count and the architecture "
  "ordering are unchanged. the thin-gap median crosses 50, so it must not be quoted as 50"),


 ("MeOH",  32.04, 0.544, 0.786, 1.9, "measured", CRC, L_VISC, "measured", CRC, L_LAB, ""),
 ("EtOH",  46.07, 1.074, 0.785, 1.5, "measured", CRC, L_VISC, "measured", CRC, L_LAB, ""),
 ("DMF",   73.09, 0.794, 0.944, 1.0, "measured", CRC, L_VISC, "measured", CRC, L_LAB,
   "Cross-checked against Kinart, Molecules 2024, 29, 1371, Table 1 (rho = 0.943802 g mL-1, "
   "eta = 0.8455 mPa s at 298.15 K)."),
 ("DMA",   87.12, 1.927, 0.937, 1.0, "measured", CRC, L_VISC, "measured", CRC, L_LAB,
  "eta corrected 0.945 -> 1.927 on 2026-08-23. CRC 97th p. 6-244 prints 1.927 in the eta(25 C) "
  "column and 0.945 is not on that page. An earlier pass here carried 0.927 on the reasoning "
  "that 1.927 must be a leading-digit typo, since DMA would otherwise be as viscous as DMSO "
  "(1.987) while its homologue DMF is 0.794. That reasoning is not acted on: it is an inference "
  "with no source, and the standard requires the printed value at the cited locator. "
  "consequence, and it is a real one: DMA carries the kilogram-scale Ni-xec campaign. At the "
  "printed 1.927 that row transport ceiling is 8.2 mA cm-2, below the 10 mA cm-2 at which the "
  "campaign actually ran, so the S7 sentence calling that agreement a direct validation of the "
  "model no longer holds and has been withdrawn. At 0.927 the ceiling is 16.5 and the agreement "
  "returns. " + _dma_moves_sentence() + " Anyone resolving the "
  "CRC row against A primary viscosity measurement should revisit both this row and S7"),

 ("DMSO",  78.13, 1.987, 1.096, 1.0, "measured", CRC, L_VISC, "measured", CRC, L_LAB, ""),
 ("THF",   72.11, 0.456, 0.883, 1.0, "measured", CRC, L_VISC, "measured", CRC, L_LAB, ""),
 ("H2O",   18.02, 0.890, 0.997, 2.6, "measured", IAPWS_ETA,
   "pp. 101-125 (reference correlation evaluated at 298.15 K, 0.1 MPa)", "measured", IAPWS_RHO,
   "pp. 387-535 (IAPWS-95 equation of state; rho at 298.15 K)", ""),
 ("AcOH",  60.05, 1.056, 1.045, 1.0, "measured", CRC, L_VISC, "measured", CRC, L_LAB, ""),
 ("HFIP", 168.04, 1.619, 1.596, 1.0,
   "measured", "Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587", "Table 3, p. 578",
   "assumption",
   "Sigma-Aldrich product specification, 1,1,1,3,3,3-hexafluoro-2-propanol, CAS 920-66-1",
   "density 1.596 g mL-1 at 25 C, listed '(lit.)'; the same specification gives n20/D 1.275, "
   "bp 59 C and mp -4 C",
   "mu retrieved 2026-08-22: Krumgalz Table 3 p. 578 tabulates '1,1,1,3,3,3-hexafluoropropan-2-ol' "
   "at 0.01619 P = 1.619 mPa s, 25 C -- the review's own viscosity table for the 50 solvents it "
   "treats. This replaces 1.650, which was carried with no source at all (-1.9%). "
   "The Colomer/Waldvogel Nat. Rev. Chem. 2017 citation this row used to name is withdrawn: the "
   "paper was retrieved and its authors are Colomer, Chamberlain, Haughey & Donohoe (not "
   "Chinchilla/Waldvogel), and its Table 1 p. 2 carries bp and eps only -- neither mu nor rho. "
   "rho = 1.596 g cm-3 stays state C because the source is SECONDARY, not because there is none: "
   "the Sigma-Aldrich specification for CAS 920-66-1 lists 1.596 g mL-1 at 25 C, marked '(lit.)', "
   "so it is a compilation rather than a primary measurement. Three independent lines agree on it "
   "and rule out the one page-anchored alternative. CRC 97th ed. p. 3-296 entry 5801 prints "
   "den = 1.4600 at 21 C, and the column assignment is not in doubt (x-coordinate checked against "
   "a known density in the row below); but the same Sigma sheet gives n20/D = 1.275, so 1.4600 is "
   "NEITHER the density NOR the refractive index of this compound, and CRC's neighbouring entry "
   "5802 carries nD = 1.4631 one row up -- consistent with a typesetting slip into that cell. "
   "Calibrating the F-for-H molar-volume increment on 2,2,2-trifluoroethanol gives "
   "(V_TFE - V_EtOH)/3 = +4.63 cm3 mol-1 per F; six of those applied to isopropanol predict "
   "V_HFIP = 104.32 cm3 mol-1, i.e. rho = 1.611, which 1.596 matches to -0.9% and CRC's 1.4600 "
   "misses by -9.4%. Cite this as the Sigma specification, never as CRC, and do not drop the CRC "
   "disagreement: a reviewer who checks CRC will find 1.4600 and needs this note to know why it "
   "was not used. Sensitivity: rho enters only through nu = "
   "mu/rho in Sc, and Sh ~ Sc^0.356, so a +/-5% rho error moves these two rows' i_lim by <2% "
   "(gate G-solv sweeps them at +/-25-50%; the worst single count moves by 2 of 50 and the architecture ordering is preserved throughout)."),
 ("acetone", 58.08, 0.306, 0.784, 1.0, "measured", CRC, L_VISC, "measured", CRC, L_LAB, ""),
 ("MeNO2",  61.04, 0.620, 1.137, 1.0, "measured", CRC, L_VISC, "measured", CRC, L_LAB, ""),
]
_check_solvents_against_csv(PURE)


AG95   = ("Aminabhavi & Gopalakrishna, J. Chem. Eng. Data 1995, 40, 856-861 (rho and eta at "
          "298.15 K over the full composition range: DMF+H2O, DMSO+H2O, DMA+H2O, MeCN+H2O, THF+H2O)")
CVK67  = ("Cunningham, Vidulich & Kay, J. Chem. Eng. Data 1967, 12, 336-337 (rho, eta and eps for "
          "MeCN-H2O at 25 C)")
WS94   = ("Wode & Seidel, Ber. Bunsenges. Phys. Chem. 1994, 98, 927-934 (precision MeCN-H2O "
          "viscosities)")
GCGD07 = ("Gonzalez, Calvar, Gomez & Dominguez, J. Chem. Thermodyn. 2007, 39, 1578-1588 (rho and "
          "eta for MeOH+H2O and EtOH+H2O at 298.15 K)")
CRC_AQ_WARN = (" The inherited citation was the CRC 'Concentrative Properties of Aqueous Solutions' "
               "table (pp. 5-118 to 5-135), whose viscosity and density data are tabulated at 20 C, "
               "not 25 C, and which is indexed by mass per cent rather than by v/v. It cannot "
               "support a 25 C value at a stated volume ratio and has been withdrawn.")
AS22 = ("Ansari & Singh, Res. J. Chem. Sci. 2022, 12(1), 67-69, Table-1 p. 68 -- measured densities and viscosities of acetonitrile-water at 25 C, 10-70 wt%% AN plus pure AN. Open access (www.isca.in). Its pure-component values, rho = 0.7767 g cm-3 and eta = 0.346 cP, reproduce the CRC 97th ed. MeCN entries carried here (0.776, 0.343) to 0.3%% and 0.9%%, which is the quality check on a low-impact source")
# BOUNDS FOR THE MIXTURE PROPERTIES (data/mixture_property_bounds.py, gate G-MIXBOUND).
# These rows cannot be SOURCED -- no table gives a 25 C value at a stated v/v ratio for most of
# them -- but most of them can be BOUNDED by something citable, and the assumption behind each
# bound is stated here rather than left for a reader to reconstruct.
CRC_5118 = ("CRC Handbook of Chemistry and Physics, 97th ed., 2016 (Haynes), 'Concentrative "
            "Properties of Aqueous Solutions: Density, Refractive Index, Freezing Point "
            "Depression, and Viscosity'")
_AQ_BOUND = (
    " TEMPERATURE BASIS, DISCLOSED. The located table is measured at 20 C -- its header states "
    "'All data refer to a temperature of 20 C' -- while this model works at 25 C, and no 25 C "
    "table for an aqueous alcohol mixture exists in that handbook (its only 25 C mixture table "
    "covers aqueous hydroxides). The carried value is the 25 C one, and it agrees with the "
    "tabulated 20 C entry scaled by the temperature dependence of water's own viscosity over the "
    "same interval (1.002 to 0.890 mPa s, -11.2 per cent) to within about 1 per cent: 1.82 x 0.888 "
    "= 1.62 against 1.60 carried for the methanol mixture, and 2.85 x 0.888 = 2.53 against 2.40 "
    "for the ethanol one. The approximation this leaves is that the mixture's relative temperature "
    "dependence matches water's across 20-25 C. It is small -- a few per cent at most -- and far "
    "inside the +/-25-50 per cent over which G-SOLV sweeps every non-page-anchored solvent "
    "property, where the worst threshold count moves by two of fifty and the architecture ordering "
    "is preserved throughout. On density the same 20 C basis applies and matters less: liquids "
    "expand on warming, so the 25 C density is the lower of the two by roughly half a per cent, "
    "and density enters only through nu = mu/rho -- cancelling entirely for the declared-delta "
    "archetypes and for Leveque, where Re Sc is independent of nu. ASSUMED throughout: that the "
    "volume ratio is measured before mixing, the usual laboratory convention, and that the v/v to "
    "mass per cent conversion may use pure-component densities at 25 C rather than 20 C, which "
    "shifts the mass per cent by under 0.2 and the interpolated entry by under 0.5 per cent.")
_ORG_BOUND = (
    " BOUNDED, NOT SOURCED. Both pure components are page-anchored, and the mixture viscosity is "
    "bracketed between them. ASSUMED: monotone mixing. That holds for two organic liquids of "
    "similar class without strong hetero-association, and it is NOT applied to the aqueous "
    "mixtures here, where a viscosity maximum exceeding both pure components is well established "
    "-- methanol/water peaks near 1.8 mPa s against 0.54 for methanol and 0.89 for water. A "
    "pure-component bracket would be a false bound for exactly those systems.")
_NO_BOUND = (
    " NOT BOUNDED, AND SAID SO. No table for this pair was located. The pure-component bracket "
    "used for the organic-organic mixtures is not valid upward here, because an aqueous-organic "
    "mixture can exceed both of its components in viscosity. This value is therefore a declared "
    "estimate carrying no upper bound, reported as such rather than given a bracket it does not "
    "have. Its exposure is measured instead by sweeping it: G-SOLV moves every non-page-anchored "
    "solvent property by +/-25-50 per cent and reports the worst count movement.")
# Published alongside every mixture row that rests on the 20 C table. Kept short because it goes
# into Table S7 verbatim; the full working account is in the method_note, which does not ship.
_TDISC = (" TEMPERATURE BASIS: the source table is measured at 20 C and this model works at 25 C; "
          "the handbook has no 25 C table for an aqueous alcohol mixture. The value carried here "
          "is the 25 C one, and it reproduces the 20 C entry scaled by the temperature dependence "
          "of water's own viscosity over the same interval (1.002 to 0.890 mPa s) to within about "
          "1 per cent. The residual approximation -- that the mixture's relative temperature "
          "dependence matches water's across 20-25 C -- is a few per cent at most, well inside the "
          "+/-25-50 per cent this property is swept over. On density the 20 C basis matters less "
          "still: the 25 C value is lower by roughly half a per cent, and density enters only "
          "through nu = mu/rho.")
_BDISC = (" BASIS: bracketed between the two pure components, both page-anchored. Monotone mixing "
          "is assumed, which holds for two organic liquids without strong hetero-association; it "
          "is deliberately not applied to the aqueous mixtures, where the viscosity maximum "
          "exceeds both components.")
_NDISC = (" BASIS: no table for this pair was located, and a pure-component bracket is not valid "
          "upward for an aqueous-organic mixture. Carried as a declared estimate with no upper "
          "bound; its exposure is measured by sweeping it rather than by a bracket it does not "
          "have.")
MIX_DISCLOSE = {
    "MeOH/H2O 1:1 v/v": _TDISC, "EtOH/H2O 1:1 v/v": _TDISC,
    "DMSO/THF 5:1 v/v": _BDISC, "AcOH/HCOOH 1:1 v/v": _BDISC,
    "DMF/H2O 9:1 v/v": _NDISC, "tAmOH/H2O 3:1 v/v": _NDISC,
}

MIX_BOUND = {
    "MeOH/H2O 1:1 v/v":   (CRC_5118, "pp. 5-118 ff., Methanol block, 20 C, read at 44.1 mass% "
                                     "methanol (1:1 v/v)", _AQ_BOUND),
    "EtOH/H2O 1:1 v/v":   (CRC_5118, "pp. 5-118 ff., Ethanol block, 20 C, read at 44.1 mass% "
                                     "ethanol (1:1 v/v)", _AQ_BOUND),
    "DMSO/THF 5:1 v/v":   ("Declared bracket: pure-component viscosities of DMSO and THF, both "
                           "page-anchored in this registry", "bracket [0.456, 1.987] mPa s", _ORG_BOUND),
    "AcOH/HCOOH 1:1 v/v": ("Declared bracket: pure-component viscosities of acetic and formic acid, "
                           "CRC 97th ed. Sect. 6 'Viscosity of Liquids'", "bracket [1.056, 1.607] mPa s",
                           _ORG_BOUND),
    "DMF/H2O 9:1 v/v":    ("-- (no table located for this pair)", "", _NO_BOUND),
    "tAmOH/H2O 3:1 v/v":  ("-- (no table located for this pair)", "", _NO_BOUND),
}

MIX = [
 # 9:1 v/v = 87.5 wt%% MeCN, which is OUTSIDE Ansari & Singh's 10-70 wt%% range. The row
 # therefore stays an assumption, but it is now BRACKETED by two measured points of that
 # table rather than by nothing: eta(70 wt%%) = 0.574 cP and eta(pure AN) = 0.346 cP, so
 # 0.346 <= eta(87.5 wt%%) <= 0.574 and the carried 0.48 sits inside. Linear interpolation
 # between those two measured points gives 0.441 (rho 0.805); the carried 0.48/0.82 are
 # +8.9%%/+1.9%% against that, well inside the +/-25%% band over which G-SOLV shows no
 # published count moves.
 ("MeCN/H2O 9:1 v/v", 36.4, 0.48, 0.82, 1.17, AS22 + "; " + CVK67 + "; " + WS94 + "; " + AG95, "",
  ("bracket", "9:1 v/v = 87.5 wt% MeCN, outside the 10-70 wt% range Ansari & Singh measure. The "
   "row stays an assumption, but it is now bracketed by two measured points of their Table-1 "
   "p. 68 rather than by nothing: eta(70 wt%) = 0.574 cP and eta(pure an) = 0.346 cP, so "
   "0.346 <= eta <= 0.574 and the carried 0.48 sits inside. Linear interpolation between those "
   "two measured points gives eta = 0.441 cP, rho = 0.805 g cm-3; the carried 0.48/0.82 are "
   "+8.9%/+1.9% against that.")),
 ("MeOH/H2O 1:1 v/v", 26.4, 1.60, 0.87, 1.94, GCGD07, CRC_AQ_WARN, None),
 ("EtOH/H2O 1:1 v/v", 33.0, 2.40, 0.89, 1.58, GCGD07, CRC_AQ_WARN, None),
 ("DMF/H2O 9:1 v/v",  56.0, 1.00, 0.96, 1.15, AG95, "", None),
 ("DMSO/THF 5:1 v/v", 77.1, 1.55, 1.06, 1.00, "no measured isotherm located for this pair", "", None),
 ("tAmOH/H2O 3:1 v/v",35.0, 2.80, 0.85, 1.73, "no measured isotherm located for this pair", "", None),
 ("AcOH/HCOOH 1:1 v/v",53.0,1.28, 1.13, 1.0,  "no measured isotherm located for this pair", "", None),
 # 2:1 v/v = 28.0 wt%% MeCN, squarely INSIDE Ansari & Singh's measured range. Interpolating
 # their 20 wt%% (0.973 cP, 0.9588) and 30 wt%% (0.910, 0.9380) rows gives eta = 0.922 cP and
 # rho = 0.942 g cm-3. The carried values are -2.4%% and -0.2%% against that. This row is the
 # one mixed solvent in the set whose properties can now be read off a measured table.
 # phi CORRECTED 2.10 -> 1.916 on 2026-08-22. Only the PRODUCT phi*M enters Wilke-Chang, and
 # this row carried 2.10 x 24.0 = 50.40, which is the VOLUME-fraction-weighted phi times the
 # volume-fraction-weighted M -- not Eq. S30, which is the MOLE-fraction sum sum(x_j phi_j M_j).
 # At 2:1 v/v water:MeCN, x(H2O) = 0.854 and x(MeCN) = 0.146, so Eq. S30 gives
 #   0.854 x 2.6 x 18.015 + 0.146 x 1.0 x 41.05 = 45.99,
 # i.e. the tabled product was +9.6 pct high and D was overstated by sqrt(50.40/45.99) = 4.7 pct.
 # M is left at 24.0 because the Table S3 caption already tells the reader these mixture
 # entries are not molecular weights; phi carries the correction so that phi*M = 45.99.
 # The five other mixtures were re-derived the same way and reproduce their tabled products
 # to <=0.3 pct, so this row was the only one built on the wrong average.
 ("H2O/MeCN 2:1 v/v", 24.0, 0.90, 0.94, 1.916, AS22 + "; " + CVK67 + "; " + WS94 + "; " + AG95, "",
  ("derived", "2:1 v/v = 28.0 wt% MeCN, inside the range Ansari & Singh measure. Interpolating "
   "their Table-1 p. 68 rows at 20 wt% (0.973 cP, 0.9588 g cm-3) and 30 wt% (0.910, 0.9380) "
   "gives eta = 0.922 cP and rho = 0.942 g cm-3. The carried 0.90/0.94 are -2.4%/-0.2% against "
   "that measured interpolation -- the only mixed solvent in the set whose properties can be "
   "read off a measured table.")),
]

def _disp(name):
    return "" if name in USED_SOLVENTS else S_DISPLAY_SOLV

for n_, M, mu, rho, phi, mus, muc, mul, rhos, rhoc, rhol, note in PURE:
    d = _disp(n_)
    tail = ((" " + note) if note else "") + d
    add("2. Solvents", f"{n_}: M", f"{M}", "g mol-1", "derived",
        "sum of the IUPAC 2021 standard atomic weights over the molecular formula", IUPAC, "",
        "Exact to the rounding shown." + d)
    # mu and rho are emitted INDEPENDENTLY. Until 2026-08-22 one branch decided both, which was
    # safe only while every solvent had the same state for the pair. HFIP broke that: Krumgalz
    # Table 3 p. 578 page-anchors its viscosity while its density remains unsourced, and the
    # coupled branch would have silently promoted the density to `measured` with an empty
    # locator -- caught by the add() locator assert, which is why that assert exists.
    for prop, val, unit, st, cite, loc, sens, what in (
            ("mu (25 C)", mu, "mPa s", mus, muc, mul, S_MU_OVERRIDE.get(n_, S_MU), "viscosity"),
            ("rho", rho, "g mL-1", rhos, rhoc, rhol, S_RHO, "density")):
        if st == "measured":
            add("2. Solvents", f"{n_}: {prop}", f"{val}", unit, "measured",
                f"pure-solvent tabulated {what} at 25 C." + tail, cite, loc, sens + d)
        else:
            # STATE C DOES NOT MEAN "NO EVIDENCE". It means no PAGE-ANCHORED PRIMARY source. A row
            # can be state C and still rest on something a reader can open -- a supplier
            # specification, say -- and printing "no source supports this value" over the top of
            # that is a worse statement than the truth. Where a citation is supplied, print it and
            # say what tier it is; where none is, keep the blunt string.
            add("2. Solvents", f"{n_}: {prop}", f"{val}", unit, "assumption",
                (f"no page-anchored primary {what}; the source below is secondary." + tail)
                if cite else (f"no page-anchored {what} located." + tail),
                cite if cite else "-- (no source supports this value)", loc, sens + d)
    add("2. Solvents", f"{n_}: phi (assoc.)", f"{phi}", "-", "measured",
        "Wilke-Chang association parameter as recommended by the correlation's authors", WC55,
        L_WC55,
        "D ~ (phi M)^0.5. The frequently quoted revision phi(H2O) = 2.26 in place of 2.6 would "
        "lower aqueous D by 7 pct; no threshold count in Table S5 moves by more than one entry." + d)
    add("2. Solvents", f"{n_}: nu = mu/rho", f"{mu*1e-3/(rho*1000):.3e}", "m2 s-1", "derived",
        "kinematic viscosity computed from the mu and rho rows above", "this registry", "",
        "Inherits the exposure of its two inputs." + d)

for n_, M, mu, rho, phi, cite, warn, anchor in MIX:
    d = _disp(n_)
    # anchor = (state, note) when a measured table for this pair HAS been retrieved. Without it
    # the row names the paper that would have to be page-anchored. Leaving
    # that wording on a row whose source has since been read is exactly the stale-claim failure
    # this project keeps getting bitten by, so the wording is driven by the data, not typed.
    if anchor:
        a_state, a_note = anchor
        mu_state = "derived" if a_state == "derived" else "assumption"
        mu_note = a_note
        mu_cite, mu_loc = cite, "Ansari & Singh Table-1, p. 68"
    else:
        mu_state, mu_note = "assumption", ("mixture viscosity at the stated v/v ratio; not "
            "reproducible from any table located for it. Page-anchoring would require: " + cite + "." + warn)
        # A row that cannot be SOURCED can still be BOUNDED, and the bound is citable. Printing
        # "no source supports this value" over a row that has one is a worse statement than the
        # truth; the assumption behind the bound travels with it.
        _b = MIX_BOUND.get(n_)
        if _b:
            _bc, _bl, _ba = _b
            mu_cite, mu_loc = _bc, _bl
            mu_note = mu_note + _ba
        else:
            mu_cite, mu_loc = "-- (no source supports this value)", ""
    add("2. Solvents", f"{n_}: M", f"{M}", "g mol-1", "derived",
        "not a molar mass. Only the product phi*M enters Eq. S2; for mixtures phi*M is set by the "
        "Perkins-Geankoplis mole-fraction rule and the split into a nominal 'M' and a nominal 'phi' "
        "is presentational. Read the two rows as the single quantity phi*M = %.1f g mol-1." % (phi*M),
        POLING, L_PG,
        "Carries no independent exposure: only phi*M is used, and D ~ (phi M)^0.5." + d)
    # The temperature basis has to travel in the SENSITIVITY column, not method_note: method_note
    # is the internal working record and is not published, while sensitivity ships verbatim into
    # Table S7. A disclosure the reader never sees is not a disclosure.
    _disc = MIX_DISCLOSE.get(n_, "")
    add("2. Solvents", f"{n_}: mu (25 C)", f"{mu}", "mPa s", mu_state,
        mu_note + warn, mu_cite, mu_loc, S_MU_OVERRIDE.get(n_, S_MU) + _disc + d)
    add("2. Solvents", f"{n_}: rho", f"{rho}", "g mL-1", mu_state,
        mu_note + warn, mu_cite, mu_loc, S_RHO + _disc + d)
    add("2. Solvents", f"{n_}: phi (assoc.)", f"{phi}", "-", "derived",
        "fitted so that phi*M reproduces the Perkins-Geankoplis mole-fraction rule applied to the "
        "pure-component phi and M; see the M row above", POLING, L_PG,
        "Presentational half of phi*M; no independent exposure." + d)
    add("2. Solvents", f"{n_}: nu = mu/rho", f"{mu*1e-3/(rho*1000):.3e}", "m2 s-1", "derived",
        "kinematic viscosity computed from the mu and rho rows above", "this registry", "",
        ("Inherits the exposure of its two inputs." if anchor else
         "Inherits the exposure of its two inputs, both of which are assumptions.") + d)

# -- 3. Property-estimation methods and their constants ----------------------
## ---- the two THEORY-LEVEL choices ---------------------------------------------------------
## These are not quantities anyone could cite; they are the model's statement of what it is
## solving. They are registered so that a reader meets them as declared choices with a measured
## bound, rather than discovering them by reading the solver source.
add("3. Estimation methods", "Transport theory level", "dilute-solution", "-", "assumption",
    "the film problem is solved on DILUTE-SOLUTION theory: Nernst-Planck fluxes with a constant "
    "diffusivity per species, local electroneutrality, unit activity coefficients, and no "
    "Stefan-Maxwell cross-coefficients (Newman, Electrochemical Systems, Ch. 11). Chosen because "
    "the Onsager/Stefan-Maxwell coefficients required by concentrated-solution theory do not "
    "exist in the literature for these fifty organic electrolyte compositions; obtaining them is "
    "a measurement programme, not a modelling choice",
    "Newman & Thomas-Alyea, Electrochemical Systems, 3rd ed., Ch. 11 (dilute-solution theory) "
    "and Ch. 12 (concentrated-solution theory)", "Ch. 11-12",
    "Bounded from this project's own measured isotherms rather than argued. Dilute-solution "
    "theory with concentration-independent mobilities predicts kappa proportional to c, i.e. a "
    "constant equivalent conductance; the 21-point isotherms show "
    "Lambda falling to 0.44 of its dilute value by 0.80 mol/kg and to 0.05 by 4.50 mol/kg for "
    "Bu4NBF4/MeCN, and to 0.74 by 1.57 mol/kg for NaCl/H2O. The assumption is therefore "
    "quantitatively wrong above roughly 1 M and the model states so. What protects the reported "
    "results is that the numerics are verified against the analytic limits of the theory it does "
    "implement -- Newman's binary-electrolyte x2 migration enhancement is reproduced to 0.5 pct "
    "and 0.26 pct, and discrete charge conservation holds to 3e-12 -- and "
    "that the conclusions rest on the architecture ORDERING and on order-of-magnitude contrasts, "
    "neither of which any sweep run here inverts.")
add("3. Estimation methods", "Viscosity used in D and in nu", "pure solvent", "-", "assumption",
    "mu is the PURE SOLVENT viscosity of Table S3, page-anchored to CRC, used both in "
    "Wilke-Chang (D ~ 1/mu) and in nu = mu/rho for the mass-transfer correlations. The cells "
    "contain solute at up to 13.7 M total, and a solution is more viscous than the solvent it is "
    "made from, so every affected ceiling is OVERSTATED. Chosen because no solution-viscosity "
    "measurement exists for these fifty compositions and inventing one would be worse than "
    "declaring the gap", "declared modelling choice", "",
    "Swept rather than corrected, "
    "the 14 rows at >= 1.0 M total dissolved. The response is NOT 1/mu: mu also enters nu, and "
    "delta_eff moves with it wherever delta is computed, so d ln i_lim / d ln mu is -1.000 for "
    "the two declared-delta archetypes but -0.667 (Leveque), -0.833 (Levich) and -0.988 "
    "(Eisenberg) for the rest, asserted against the computed delta_eff at run time. "
    "Result: the first >=25 count moves at mu_solution/mu_solvent = 1.5, and it is the unstirred "
    "column that moves; the architecture ordering survives to 3.0, and the thin-gap, RDE and RCE "
    "counts do not move anywhere in that range. The reported integers should be read with that "
    "breaking point; the ordering does not depend on it.")
add("3. Estimation methods", "Wilke-Chang: D = 7.4e-8 (phi M)^0.5 T / (mu V^0.6)", "7.4e-8",
    "(cgs mixed)", "measured",
    "empirical correlation as published; applies to the 43 molecular carriers and the mediated-spec "
    "substrates. Ferrocene/MeCN anchor: predicted 1.8e-5 vs measured 2.4e-5 cm2 s-1 (-24 pct), "
    "disclosed in S3", WC55, L_WC55,
    "Canonical accuracy +/-10-20 pct for typical organics; our worst anchor is -24 pct. I_lim is "
    "linear in D, so this displaces log10 i_lim by at most 0.10.")
add("3. Estimation methods", "Stokes-Einstein hydrodynamic radius r", "4-5", "Angstrom", "assumption",
    "hydrodynamic radius assigned to M(bpy)/M(salen) molecular-catalyst cores; the equation "
    "D = kB T / (6 pi mu r) itself is textbook", "declared modelling choice", "",
    "D ~ 1/r, so the declared 4-5 Angstrom band spans 25 pct in D. The resulting D = 3-7e-6 cm2 s-1 "
    "brackets the range reported for such complexes in amide solvents. " + _cd_sentence())
# PAGE-ANCHORED 2026-08-22: Cussler Eq. (5.2-1), p. 127, prints exactly this form,
# D = kB T / f = kB T / (6 pi mu R0), on the same page as Table 5.2-1.
add("3. Estimation methods", "Stokes-Einstein: D = kB T / (6 pi mu r)", "--", "-", "derived",
    "molecular catalysts; radius from the row above, mu from category 2", CUSSLER,
    "Eq. (5.2-1), p. 127",
    "See the hydrodynamic-radius row.")
# LOCATOR CORRECTED 2026-08-22. This row cited Bard & Faulkner "Eq. 2.3.22", which was retrieved
# and is NOT the Nernst-Einstein relation: it is the reversible charge transfer through a liquid
# junction, H+(beta) + e(Pt') = H+(alpha), in the liquid-junction-potential derivation of Sect.
# 2.3. Sect. 2.4 of that book is ion-selective electrodes, so the neighbouring numbering does not
# rescue it either. The relation IS stated, with a locator this project has already opened, in the
# header text of the CRC table the aqueous diffusivities come from -- and better still, that same
# table prints its own D column, so the implementation can be checked rather than merely cited:
# lambda 349.65 -> D 9.311, 73.48 -> 1.957, 138.6 (z=2) -> 0.923, 44.5 -> 1.185 e-5 cm2/s, all
# reproduced to better than 0.1 pct.
add("3. Estimation methods", "Nernst-Einstein: D = R T lambda0 / (z2 F2)", "--", "-", "derived",
    "small inorganic ions from limiting molar conductivity. The relation is stated in the header "
    "of the cited table, and that table's own D column reproduces this implementation to better "
    "than 0.1 pct for H+, K+, HCO3- and the divalent CO3^2-, which is the check that the z^2 is "
    "handled correctly", CRC, L_VAN,
    "Exact identity at infinite dilution; the exposure sits in lambda0, not in the method.")
for k, v in [("C",14.8),("H",3.7),("O (ether/carbonyl)",7.4),("O (acid hydroxyl)",12.0),
             ("N (tertiary)",15.6),("N (primary amine)",10.5),("N (secondary)",12.0),("S",25.6),
             ("F",8.7),("Cl",24.6),("Br",27.0),("I",37.0),
             ("6-ring correction",-15.0),("5-ring",-11.5),("4-ring",-8.5),("3-ring",-6.0)]:
    add("3. Estimation methods", f"Le Bas increment: {k}", f"{v}", "cm3 mol-1", "measured",
        "additive atomic volumes at the normal boiling point, read from Table 3-8; the benzene "
        "closure check reproduces the textbook 96.0 cm3 mol-1", POLING, L_LEBAS,
        "D ~ V_A^-0.6; the benzene closure check bounds the increment set to a few per cent.")
# Phosphorus is carried in the increment dictionary of build_reactions50.py but is NOT in the
# Le Bas column of Table 3-8, so it cannot claim that locator. It is also unused: no entry of the
# 50-reaction set has a phosphorus-bearing carrier whose volume is built by Le Bas. Registering it
# as `measured` against a table that does not contain it is exactly the kind of borrowed locator
# this project treats as a fabrication, so it is declared an assumption and its own sensitivity
# records that it reaches nothing.
add("3. Estimation methods", "Le Bas increment: P", "27.0", "cm3 mol-1", "assumption",
    "phosphorus increment carried in the code's increment table. Not present in the Le Bas column "
    "of Table 3-8, p. 53, and therefore not page-anchored to it",
    LEBAS_NOSRC, "",
    "Display-only: no carrier in the 50-reaction set contains phosphorus, so this increment "
    "enters no reported volume, no D and no i_lim. Verified by scanning reactions_50.csv for a "
    "phosphorus-bearing Le Bas construction: zero rows.")

# -- 4. Diffusion coefficients fixed in solver species lists -----------------
# Aqueous rows are DERIVED: D = R T lambda0 / (z^2 F^2) reproduces every tabulated value to the
# digits shown from the CRC/Vanysek lambda0 (verified here, e.g. lambda0(Br-) = 78.1 -> 2.079e-9).
# Non-aqueous rows that rested on the Izutsu limiting-conductivity tables are routed to assumption:
# that book could not be opened (Wiley 402; the public mirror is dead). The one exception is
# Br-(MeCN), whose lambda0 = 102.00 S cm2 mol-1 is page-anchored in Kalugin 2019 Table 3, p. 28
# and reproduces 2.716e-9 exactly.
NE = "Nernst-Einstein D = R T lambda0 / (z^2 F^2) with R, T and F from category 1"
S_SOLVER = ("Solver species: supporting-electrolyte ions, mediators and mediator counter-ions. "
            "These set migration and the film potential in the Stage-1 and EC-prime solves, and "
            "they do reach reported quantities. In the Stage-0 film model only the Table S2 carrier "
            "D sets i_lim, but that is not true of the eight mediated entries, whose plotted "
            "current comes from the EC-prime solve these species enter. Doubling ClO4-, SCN-, Br- "
            "and Br2 together and re-solving the mediated matrix moves 18 of the 300 cells of the "
            "merged matrix by more than 1 pct and moves two published counts by one entry "
            "each: the stirred >=25 mA cm-2 count and the parallel-plate >=50 mA cm-2 count, "
            "each rising by one of fifty. The absolute values that perturbation was measured "
            "against predate the acetonitrile viscosity correction, which moved both baselines "
            "down by one independently, so the one-entry movement is quoted here rather than "
            "a pair of from/to integers that no longer describe the current matrix. The "
            "unstirred, thin-gap, RDE and rotating-cylinder counts are "
            "unchanged and the architecture ordering is preserved; the largest median shift is "
            "+11 pct at the rotating cylinder (121.7 -> 135.7 mA cm-2). A factor of two is far "
            "wider than the uncertainty on any of these values, so the counts are stable in "
            "practice, but they are not invariant to them. The discrete charge-conservation check "
            "(maximum deviation 3e-12) and the binary-migration bound (2.00x Fick, reproduced to "
            "0.2 pct) are insensitive to these values, because they test charge bookkeeping rather "
            "than the reported counts.")
for n_, v, lam, z in [("H+ (aq)","9.3e-09",349.7,1), ("OH- (aq)","5.27e-09",198.0,1),
                      ("K+ (aq)","1.96e-09",73.5,1), ("Na+ (aq)","1.33e-09",50.1,1),
                      ("Br- (aq)","2.08e-09",78.1,1), ("Cl- (aq)","2.03e-09",76.3,1),
                      ("CO3^2- (aq)","9.2e-10",138.6,2), ("HCO3- (aq)","1.18e-09",44.5,1)]:
    add("4. Solver species diffusivities", n_, v, "m2 s-1", "derived",
        f"{NE}; lambda0 = {lam} S cm2 mol-1, z = {z}"
        + (" (K+: the derivation gives 1.957e-9; published as 1.96e-9, which is what "
           "run_mediated.jl computes with. This row previously published 1.9e-9 -- a "
           "2-significant-figure rounding 2.9% below its own derived value and 2.9% below the "
           "code, so the registry and the solver disagreed. K+ is a spectator in the only spec "
           "that uses it (s = 0, nu = 0), and a non-reacting species' D cancels from its own "
           "Nernst-Planck equation, verified by perturbation: x10 and /10 leave i_lim identical "
           "to 6 decimals. So nothing reported moves -- but a published value must be the value "
           "used.)" if n_.startswith("K+") else ""),
        CRC, L_VAN, S_SOLVER)
# PAGE-ANCHORED 2026-08-22 from the retrieved Chapter 5 (papers for model/). Table 5.2-1,
# "Diffusion coefficients at infinite dilution in water at 25 C", p. 127, lists Bromine at
# 1.18 x 10-5 cm2 s-1 = 1.18e-9 m2 s-1. The registry carries 1.2e-9, i.e. the tabulated value
# rounded to two significant figures (+1.7 pct); the exact figure is recorded here so the
# rounding is visible rather than inferred.
add("4. Solver species diffusivities", "Br2 (aq)", "1.2e-09", "m2 s-1", "measured",
    "measured aqueous molecular-bromine diffusivity; Cussler Table 5.2-1 p. 127 tabulates "
    "1.18e-5 cm2 s-1 = 1.18e-9 m2 s-1 and this row carries it rounded to 1.2e-9 (+1.7 pct)",
    CUSSLER, "Table 5.2-1, p. 127 ('Diffusion coefficients at infinite dilution in water at "
    "25 C', Bromine row)", "")
# ETHYLENE, MEASURED (2026-09-05, author instruction). The Cl-/ethylene row is Leow's headline
# system -- ethylene sparged into 1.0 M KCl -- and carries ethene's measured solubility, yet its
# substrate diffusivity was propene's Wilke-Chang value under an "ethylene" label. The same Cussler
# table that anchors Br2 (aq) lists Ethylene 1.87e-5 cm2 s-1; read from the page raster, with
# Bromine 1.18 on the same page as the control. Wilke-Chang on ethene (V_LeBas 44.4) gives 1.74e-9,
# 7 pct below the measurement, and is recorded beside it in data/mediated_substrates.csv.
add("4. Solver species diffusivities", "Ethylene (aq)", "1.87e-09", "m2 s-1", "measured",
    "measured aqueous ethylene diffusivity at infinite dilution, 25 C; the substrate D of the "
    "Cl-/ethylene EC' row (generated table data/mediated_substrates.csv, method 'measured'; the "
    "Wilke-Chang estimate for ethene, 1.74e-9, sits 7 pct below it and is recorded beside it)",
    CUSSLER, "Table 5.2-1, p. 127 ('Diffusion coefficients at infinite dilution in water at "
    "25 C', Ethylene row: 1.87e-5 cm2 s-1)", "")
# PROPYLENE, DERIVED. The ex-cell illustrative solve (julia/run_excell.jl, S4) is propylene at its
# aqueous saturation; Cussler's Table 5.2-1 lists propane but no propylene, so the diffusivity is
# Wilke-Chang from the registered Le Bas increments and water's registered properties -- state B,
# with the arithmetic here. Until 2026-09-05 this value lived only in the generated substrate table
# (as the ethylene row's surrogate); when that row became ethylene the ex-cell solver's input lost
# its row, which G-EXCELL reported.
add("4. Solver species diffusivities", "Propylene (aq)", "1.3663e-09", "m2 s-1", "derived",
    "Wilke-Chang, D = 7.4e-8 (phi M_B)^0.5 T / (mu_B V_A^0.6) cm2 s-1 with phi = 2.6 (water), "
    "M_B = 18.015, T = 298.15 K, mu_B = 0.890 cP and V_A = 66.6 cm3 mol-1 (Le Bas: 3 C x 14.8 + "
    "6 H x 3.7) = 1.3663e-5 cm2 s-1; the same routine that generates the mediated substrate table "
    "(data/build_reactions50.py wilke_chang). Used by the ex-cell solve of S4 only",
    WC55,
    "Wilke & Chang correlation as registered above; Le Bas increments C 14.8, H 3.7 from the "
    "registered Le Bas row (Reid, Prausnitz & Poling 4th ed., Table 3-8 p. 53)", "")
# EVERY ROW STATES WHAT IT RESTS ON. "-- (no source supports this value)" is a true sentence and a
# useless one: it tells a reader that a number is unsourced without telling them what it IS, and
# these rows are not arbitrary -- each was chased to a specific source and each failed for a
# specific, recorded reason. That reason belongs in the PUBLISHED citation column, not only in the
# internal method_note. State C means no page-anchored measurement; it never means no basis.
SOLVER_BASIS = {
 "Li+ (generic organic)": (
   "Declared: the aqueous value reused for organic media. The table that would carry it is "
   "Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587, Table 4, p. 579, whose "
   "acetonitrile CATION row cannot be read unambiguously -- seven tokens for nine columns with no "
   "right-hand anchor, so Li+ and H+ cannot be separated without deciding which value looks right"),
 "NH4+ (MeCN, used aq-like)": (
   "Declared TRANSFER of a page-anchored aqueous value: CRC 97th ed., Sect. 5, p. 5-75 gives "
   "NH4+ lambda0 = 73.5 S cm2 mol-1 and D = 1.957e-5 cm2 s-1. The aqueous number is measured; what "
   "is assumed is its reuse in MeCN, and that is the weak step -- the Walden route was tested for "
   "DMF in this pass and fails by about 70 per cent"),
 "ClO4- (MeCN, aq-like)": (
   "Declared: the aqueous value reused in MeCN. Krumgalz 1983, Table 4, p. 579 prints a DASH for "
   "ClO4- in the acetonitrile column, so no lambda0 for this ion in this solvent can be "
   "page-anchored from it"),
 "SCN- (AcOH/HCOOH)": (
   "Declared: Walden scaling of the MeCN row by mu(MeCN)/mu(AcOH-HCOOH) = 0.34/1.28. Both the "
   "input lambda0 and the Walden transfer into a carboxylic-acid medium are unverified"),
 "Br2 (MeCN)": (
   "Declared: Walden-scaled from the measured aqueous value. It agrees with the ~2.4e-9 quoted for "
   "MeCN voltammetry, but that figure was not itself page-anchored here, so it corroborates rather "
   "than sources"),
 "Cl2/HOCl lumped OX (aq)": (
   "Declared LUMP, placed deliberately between Cl2(aq) 1.38e-9 and HOCl 1.4e-9. No single "
   "measurement can cover a lumped species, so none is claimed; the lump is the modelling choice"),
 "(SCN)2 (AcOH/HCOOH)": (
   "Declared: Walden-scaled from a 2.0e-9 MeCN estimate that is itself unverified. No measurement "
   "of this species' diffusivity was located in either medium"),
 "H+ (MeCN/organic)": (
   "Declared BY ARGUMENT, not measurement: an aprotic medium supports no Grotthuss shuttle, so the "
   "aqueous value is reduced to roughly a third"),
 "H+ (1:1 aq/MeCN)": (
   "Declared: interpolated between the aprotic 3.0e-9 assumption and the page-anchored aqueous "
   "9.3e-9, on partial Grotthuss transport in a water-rich mixture"),
 "B(OH)4- (aq)": (
   "Declared: borate mobility taken as comparable to HCO3- for the pH-10 borate buffer spec; no "
   "lambda0(B(OH)4-) was page-anchored. It is a SPECTATOR in that spec (s = 0), so its D cancels "
   "and no reported quantity depends on it"),
 "H+ (AcOH/HCOOH)": (
   "Declared BY ARGUMENT: set between the aprotic 3.0e-9 and a slower carboxylic-acid medium. It "
   "is a SPECTATOR in this spec (s = 0), so its D cancels and nothing reported depends on it"),
 "B(OH)3 (aq)": (
   "Declared: the neutral borate partner given the same mobility as B(OH)4-, which the buffer spec "
   "pairs it with. Both borate species are SPECTATORS (s = 0), so their D cancels"),
 "Generic supporting K+/A- (Stage-1 verification cases)": (
   "Declared: aqueous values reused inside the verification cases, which exercise physics rather "
   "than chemistry. Enters no reported result"),
 "D_med, mediator (EC-prime base case)": (
   "Declared constant of the EC-prime base case -- a round order-of-magnitude value for a "
   "TEMPO-like organic mediator. No lambda0 and no measurement for the modelled couple could be "
   "page-anchored, and none is claimed; it is a base case for the regime map, not a property of any "
   "specific mediator"),
 "D_S, substrate (EC-prime base case)": (
   "Declared constant of the EC-prime base case -- the generic small-organic-solute value "
   "already used across the solver species lists, adopted without a measurement for any specific "
   "substrate"),
}

add("4. Solver species diffusivities", "Br- (MeCN)", "2.7e-09", "m2 s-1", "derived",
    NE + "; lambda0(Br-, MeCN) = 102.00 S cm2 mol-1 gives 2.716e-9 m2 s-1, reproduced in this pass. "
    "Replaces the inherited Izutsu citation, which could not be opened", KALUGIN,
    "Table 3, p. 28 (limiting ionic conductivities in MeCN at 25 C: Bu4N+ 61.90, BF4- 109.20, "
    "Br- 102.00, Et4N+ 86.34, BPh4- 58.13 S cm2 mol-1)", S_SOLVER)
# RETRIEVED 2026-08-22. Krumgalz Table 4, p. 579 is a 25 C ion-by-solvent table of limiting
# equivalent conductances, and it carries two of the four ions the registry had been listing as
# page-anchoring against this very paper. Both reproduce the inherited values, which is the check
# that the inherited numbers were sound and that the OCR columns were read correctly:
#   lambda0(SCN-, MeCN) = 113.3  -> 3.017e-9 m2 s-1 against the carried 2.9e-9  (+4.0 pct)
#   lambda0(Br-,  MeOH) =  56.53 -> 1.505e-9 m2 s-1 against the carried 1.5e-9  (+0.4 pct)
# A third check: Krumgalz gives lambda0(Br-, MeCN) = 100.7 against the Kalugin Table 3 value of
# 102.00 already registered on the Br-(MeCN) row above, a 1.3 pct agreement between two
# independent tabulations.
# The other two ions this paper was pulled for are NOT registered from it. lambda0(ClO4-) is
# absent from the acetonitrile row (the table prints a dash in that column), and the acetonitrile
# CATION row cannot be read unambiguously -- it carries seven tokens for nine columns with no
# right-hand anchor, so Li+ and H+ cannot be separated. Resolving that by recognising which
# values "look right" is precisely what this project forbids, so `Li+ (generic organic)` and
# `ClO4- (MeCN, aq-like)` stay assumptions.
for n_, v, lam, sol in [("SCN- (MeCN)", "2.9e-09", 113.3, "acetonitrile"),
                        ("Br- (MeOH)", "1.5e-09", 56.53, "methanol")]:
    add("4. Solver species diffusivities", n_, v, "m2 s-1", "derived",
        NE + f"; lambda0({n_.split(' ')[0]}, {sol}) = {lam} S cm2 mol-1, z = 1. Replaces the "
        "inherited Izutsu citation, which could not be opened",
        "Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587", "Table 4, p. 579 (limiting equivalent conductances of anions in organic "
        f"solvents at 25 C; {sol} row)", S_SOLVER)

for n_, v, meth in [
 ("Li+ (generic organic)", "1e-09",
  "order of the aqueous value reused for organic media; no lambda0 in an organic solvent could be "
  "page-anchored. page-anchoring would require Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587 "
  "(limiting ionic conductances in 50 organic solvents at 25 C)"),
 ("NH4+ (MeCN, used aq-like)", "2e-09",
  "aqueous lambda0 = 73.5 -> 1.957e-9 reused in MeCN (corrected 2026-08-22 from a recalled 73.6 "
  "on retrieval of the CRC 97th ed.: Sect. 5 p. 5-75 gives NH4+ 73.5, D 1.957e-5 cm2 s-1; the "
  "carried 2e-9 is that value rounded and is unchanged). Cross-solvent transfer of lambda0 is not "
  "defensible: the Walden route was tested for DMF in this pass and fails by ~70 pct"),
 ("ClO4- (MeCN, aq-like)", "1.7e-09",
  "aqueous 1.79e-9 reused in MeCN; same cross-solvent objection. Page-anchoring would require Krumgalz 1983"),
 ("SCN- (AcOH/HCOOH)", "7.8e-10",
  "Walden scaling of the MeCN row by mu(MeCN)/mu(AcOH-HCOOH) = 0.34/1.28; both the input lambda0 "
  "and the Walden transfer are unverified"),
 ("Br2 (MeCN)", "2.2e-09",
  "Walden-scaled from the measured aqueous value; consistent with the ~2.4e-9 quoted for MeCN "
  "voltammetry but not page-anchored"),
 ("Cl2/HOCl lumped OX (aq)", "1.4e-09",
  "a lumped oxidant between Cl2(aq) 1.38e-9 and HOCl 1.4e-9; no single measurement covers the lump"),
 ("(SCN)2 (AcOH/HCOOH)", "5.5e-10",
  "no measurement located; Walden-scaled from a 2.0e-9 MeCN estimate that is itself unverified"),
 ("H+ (MeCN/organic)", "3e-09",
  "no Grotthuss shuttle in aprotic media, so set to ~1/3 of the aqueous value by argument rather "
  "than by measurement"),
 ("H+ (1:1 aq/MeCN)", "5e-09",
  "partial Grotthuss in a water-rich mixture; interpolated between the aprotic 3.0e-9 assumption "
  "and the aqueous 9.3e-9 derived value"),
 ("B(OH)4- (aq)", "9.6e-10",
  "borate mobility taken as comparable to HCO3- for the pH-10 borate buffer spec; no "
  "lambda0(B(OH)4-) was page-anchored"),
 ("H+ (AcOH/HCOOH)", "2e-09",
  "the aryl-thiocyanation spec runs in an AcOH/HCOOH mixture; H+ there is set between the aprotic "
  "3.0e-9 assumption and a slower carboxylic-acid medium, by argument rather than measurement. "
  "added 2026-08-24: run_mediated.jl had used 2.0e-9 for this species with no registry row, and a "
  "value-only audit bound it by coincidence to the unrelated NH4+ row, which also reads 2e-9 -- "
  "exactly the wrong-row binding of claude.md trap 11. H+ is a spectator in this spec "
  "(s = 0), so its D cancels and nothing reported depends on it"),
 ("B(OH)3 (aq)", "9.6e-10",
  "the neutral borate partner is given the same mobility as B(OH)4-, which the buffer spec pairs "
  "it with. Added 2026-08-24: previously used by run_mediated.jl with no row of its own. Both "
  "borate species are spectators (s = 0) in that spec, so their D cancels"),
 ("Generic supporting K+/A- (Stage-1 verification cases)", "1.9e-09",
  "aqueous values reused in the verification cases, which test physics rather than chemistry"),
]:
    add("4. Solver species diffusivities", n_, v, "m2 s-1", "assumption", meth,
        SOLVER_BASIS[n_], "", S_SOLVER)
add("4. Solver species diffusivities", "Bu4N+/Q+ (organic)", "1e-09", "m2 s-1", "assumption",
    "deliberately conservative: the page-anchored lambda0(Bu4N+, MeCN) = 61.90 gives 1.648e-9 m2 "
    "s-1 by Nernst-Einstein, and 1.0e-9 was adopted instead", KALUGIN, "",
    "Tested 1.0e-9 to 1.65e-9 (the derived value). " + S_SOLVER)
add("4. Solver species diffusivities", "BF4-/generic A- (organic)", "1.5e-09", "m2 s-1", "assumption",
    "deliberately conservative: the page-anchored lambda0(BF4-, MeCN) = 109.20 gives 2.908e-9 m2 "
    "s-1 by Nernst-Einstein, and 1.5e-9 was adopted instead", KALUGIN, "",
    "Tested 1.5e-9 to 2.91e-9 (the derived value). " + S_SOLVER)
add("4. Solver species diffusivities", "Supporting-ion diffusivities without conductance data",
    "%d slots, %d ion/solvent pairs" % (_UD["n_slots"], _UD["n_pairs"]), "m2 s-1", "assumption",
    "the supporting-electrolyte cation and anion slots of the 50-row table for which no limiting "
    "conductance is tabulated; each takes the class default of the two rows above (1.0e-9 for a "
    "cation, 1.5e-9 for an anion) and records that basis beside the value",
    "Declared class default: no lambda0 for these ion/solvent pairs (tosylate, BF4-, PF6-, HSO4-, "
    "carboxylates, Li+ and Br- in THF, and the like, in methanol, THF, acetone, HFIP, acetic acid "
    "and acetonitrile; tosylate and borate in water) in Krumgalz 1983 Table 4 or CRC 97th ed. "
    "pp. 5-75/5-76, so the acetonitrile values of the two rows above are reused. A supporting ion "
    "carries no flux, so under local electroneutrality its diffusivity shapes the potential profile "
    "but does not enter the limiting current; the default is therefore a choice that costs nothing "
    "reported, and the sensitivity beside it states the measured size of that nothing.",
    "",
    "All %d slots divided by 3 together, then all multiplied by 3 together, re-solving the full "
    "300-cell Nernst-Planck layer each time: the largest relative change in any cell is %s "
    "(divided) and %s (multiplied), and no threshold count in any of the %s architectures "
    "moves. The zero is the physics, not a coincidence -- a species with zero flux drops out of "
    "its own conservation equation -- and the sweep exists as a regression test: a non-zero here "
    "would mean a supporting-ion diffusivity had started feeding a reacting species."
    % (_UD["n_slots"], _relfmt(_UD["max_rel_change"]["div3"]), _relfmt(_UD["max_rel_change"]["mul3"]),
       _numword(_N_ARCH)))
add("4. Solver species diffusivities", "Carrier charge z (all 50 rows)",
    "z = 0 on %d rows, -1 on %d, -2 on %d, +2 on %d" % tuple(sum(1 for r in _CC if r["z_carrier"] == z) for z in ("0", "-1", "-2", "2")),
    "-", "assumption",
    "the charge of the carrier as it reaches the electrode, read from each exemplar paper; it "
    "decides whether the migration term acts on the carrier (a charged carrier in its own salt is "
    "lifted above its Fick bound, a neutral one is not). %d of 50 are read directly from the "
    "exemplar's written species (high confidence); %d are metal complexes whose electroactive "
    "species is written neutral and were declared neutral (medium confidence): %s"
    % (len(_CC) - len(_CC_MED), len(_CC_MED), "; ".join("%s -- %s" % (r["reaction"], r["basis"][:140]) for r in _CC_MED)),
    "Declared per row from the exemplar's own written species (each row's source is the exemplar "
    "cited beside it in Table S2); the value is printed in Table S2, column z, with medium-confidence "
    "rows marked *",
    "",
    "The %s medium-confidence rows were each re-solved at every alternative charge in %s, the whole "
    "300-cell layer each time: the largest change in any of their ceilings is %.1f pct, and no "
    "threshold count in any of the %s architectures moves at any alternative. The residual "
    "uncertainty in those %s charges is real and is provably immaterial to every published "
    "number." % (_numword(len(_CC_MED)), "{" + ", ".join(str(a) for a in _ZS["alternatives"]) + "}", _ZS["worst_ceiling_change_pct"], _numword(_N_ARCH), _numword(len(_CC_MED))))
add("4. Solver species diffusivities", "All 50 carrier D values", "(Table S2)", "m2 s-1", "derived",
    "Wilke-Chang / Nernst-Einstein / Stokes-Einstein per row by the category-3 methods; the route "
    "and citation for each row are given in Table S2", "Table S2", "",
    "See the Wilke-Chang row: +/-25 pct displaces log10 i_lim by +/-0.10.")
add("4. Solver species diffusivities", "8 mediated-spec substrate D values", "(S5.5)", "m2 s-1",
    "derived",
    "Seven by Wilke-Chang on named structures and one (ethylene/H2O) measured, all generated by "
    "data/build_mediated_substrates.py into "
    "data/mediated_substrates.csv and asserted against julia/run_mediated.jl by gate G-dsub in "
    "both places the solver uses them (the MedSpec D_S field and the S(\"Sub\") species entry). "
    "The arithmetic is therefore reproducible, which is the state-B test. Until 2026-08-24 these "
    "eight were hand-typed with nothing computing them, and running the arithmetic showed three "
    "were not Wilke-Chang values at all: Hofmann carried 2.00e-9 where 2-phenylacetamide/MeCN "
    "gives 1.861e-9 (7.5 pct high); nhpi carried 1.78e-9 where valencene/acetone gives 1.945e-9 "
    "(8.5 pct low); and the bromination row carried 6.25e-10 for a substrate this registry had "
    "misnamed as naproxen-arene -- the exemplar (s41467-025-57329-0) brominates anisole, which in "
    "H2O/MeCN gives 9.148e-10, so that value ran 46 pct low. Substrates now: 2-phenylacetamide/"
    "MeCN, 2-(2-oxopyrrolidin-1-yl)butan-1-ol/H2O, ethylene/H2O (MEASURED, Cussler Table 5.2-1 -- "
    "its own row above; the seven others are Wilke-Chang), valencene/acetone, hmf/H2O, "
    "1-decene/MeCN-H2O, anisole/H2O-MeCN, anisole/AcOH-HCOOH. Five were confirmed by exact "
    "reproduction of the carried value (ratios 1.000, 0.997, 1.000, 1.002, 0.999); the three "
    "corrected ones were read out of the exemplar PDFs, because a 3-significant-figure D does not "
    "identify a structure uniquely -- 4-fluorobenzamide and cyclopentanecarboxamide both reproduce "
    "2.00e-9 to 3 s.f.",
    WC55 + " -- applied to the named surrogate structures; the ethylene row carries the measured "
    "Cussler value instead (its own row above)",
    "structures from the exemplar PDFs: op3c00332.pdf (2-phenylacetamide 1a, 0.4 M), "
    "nature17431.pdf (valencene 4 -> nootkatone 5), s41467-025-57329-0.pdf (anisole; 4 mmol in "
    "33 mL = 0.121 M = C_sub, and 0.5 M NaBr x 10/33 = 152 mol/m3 = C_carrier)",
    "Swept together over x%.2f to x%.2f (the +/-25-30 pct usually quoted for Wilke-Chang, and wider "
    "than the +/-25 pct this registry carries as its working property error), re-solving the full "
    "%d-cell mediated matrix at each scale: %s. The mediated cell closest to the 25 mA cm-2 "
    "threshold is %s in the %s, at %.2f mA cm-2 (%.1f pct away)%s"
    % (min(_DSB["scales"]), max(_DSB["scales"]),
       8 * len(_DSB["base_counts"]),
       _dsb_movement(_DSB)[0],
       _DSB["closest_cell_to_25"]["reaction"], _DSB["closest_cell_to_25"]["reactor"],
       _DSB["closest_cell_to_25"]["i_mAcm2"], _DSB["closest_cell_to_25"]["margin_pct_to_25"],
       "." if _DSB["counts_moved"] else
       "; every other mediated cell sits further from a threshold than the sweep can move it."))
# The two EC-prime base-case diffusivities. NEW ROWS. S5.4 asserts that both are 'registered as
# assumptions in Table S7d'; until this pass they were not in the registry at all, so the SI
# contradicted the machine-generated table printed in the same document. Values are verbatim from
# julia/run_ecprime.jl (const D_med = 6.0e-10, const D_S = 1.0e-9), the file that defines the base
# case, and they are the same two constants the figure generators retype.
S_ECP = ("Base case of the EC-prime sweep: C_med = 20 mM, C_S = 0.5 M, delta = 100 um. Consumed by "
         "the EC-prime base case, by the mediated EC-prime panel of the Section 4 main composite "
         "(figs/make_fig_main.py) and by §S5.4 (figs/make_figH_ecprime.py), which print the "
         "commuting bound F D_med C_med / delta and the substrate cap F D_S C_S / delta as annotated "
         "reference lines, and by the regime classification of S5.4.")
add("4. Solver species diffusivities", "D_med, mediator (EC-prime base case)", "6e-10", "m2 s-1",
    "assumption",
    "declared constant with no source, from the EC-prime base case. It is a round "
    "order-of-magnitude value for a tempo-like organic mediator; no lambda0 and no measurement for "
    "the modelled couple could be page-anchored, and no attempt is made to attach one. " + S_ECP,
    SOLVER_BASIS["D_med, mediator (EC-prime base case)"], "",
    "Swept x1/3 to x3 (2e-10 to 1.8e-9 m2 s-1), the band S5.4 reports. Two printed quantities are "
    "linear in it: the commuting bound F D_med C_med / delta = 1.16 mA cm-2 runs 0.39-3.47, and the "
    "k -> 0 solver plateau recovers that bound to within 1-8 pct at every point of the sweep. It "
    "also sets x_k = sqrt(D_med / (k C_S)) as sqrt(D_med) -- 1.10 um at k = 1e3 M-1 s-1, spanning "
    "0.63-1.90 um, i.e. delta/x_k = 91 spanning 53-158 -- and gamma = D_S C_S / (D_med C_med) = "
    "41.67 as 1/D_med, spanning 13.9-125. The regime classification is invariant to it: regimes are "
    "selected by delta/x_k and gamma, both computed from the adopted values and reported with the "
    "case that uses them, and the existence and ordering of the three regimes do not change anywhere in "
    "the sweep. What is not invariant is which regime a fixed k occupies, which is why the base case "
    "supports regime statements and not scale-invariant ones (S5.4). No conclusion flips.")
add("4. Solver species diffusivities", "D_S, substrate (EC-prime base case)", "1e-09", "m2 s-1",
    "assumption",
    "declared constant with no source, from the EC-prime base case. It is the generic small "
    "organic solute value already used across the solver species lists, adopted here without a "
    "measurement for any specific substrate. " + S_ECP,
    SOLVER_BASIS["D_S, substrate (EC-prime base case)"], "",
    "Swept x1/3 to x3 (3.3e-10 to 3e-9 m2 s-1). The substrate cap F D_S C_S / delta = 48.24 mA cm-2 "
    "is linear in it and runs 16.1-144.7, and gamma = 41.67 runs 13.9-125. The k -> 0 shuttle result "
    "is exactly independent of D_S, and so is x_k, which contains D_med only. The regime "
    "classification is invariant to it for the same reason as the row above -- it is made by "
    "delta/x_k and gamma, and the existence and ordering of the three regimes survive the whole "
    "sweep -- but the regime a fixed k occupies does move: at k = 1e3 M-1 s-1 a threefold larger "
    "D_S carries the system out of total catalysis and back into the Saveant regime (S5.4). The two "
    "annotated ratios are therefore sensitive to this row and the classification is not. No "
    "conclusion flips.")

# -- 5. Concentrations & solubility anchors ----------------------------------
add("5. Concentrations", "All 50 C_carrier / C_substrate", "(Table S2)", "M", "measured",
    "page-verified against the primary-source PDF corpus: for each row the stated amounts and "
    "solvent volumes of the paper's standard or scaled conditions were converted to molarity by "
    "explicit mmol/mL arithmetic. 49 of 50 are exemplar-verified (41 against main-article PDFs and "
    "patents, 8 more against their Supporting Materials); the remaining row, the amide "
    "alpha-methoxylation, transfers the verified Shono carbamate conditions by stated analogy",
    "Table S2 per-row citations",
    "Table S2, final column (per-row page / table / figure / procedure anchor inside the cited "
    "source)",
    "i_lim is linear in C (Eq. S1), so residual error in any row rescales exactly that row. The "
    "architecture ranking and the carrier dichotomy rest on 1-2 order-of-magnitude contrasts and "
    "cannot move under factor-of-two revisions.")
add("5. Concentrations", "Supporting-electrolyte concentrations in EC' specs", "0.033-1.0 M", "M",
    "measured",
    "matched to each verified exemplar's electrolyte; buffer compositions (carbonate pH 8.5, borate "
    "pH 10, HClO4 0.15 M) taken from the cited experimental sections",
    "Table S2 per-row citations", "Table S2, final column", "")
add("5. Concentrations", "Propylene C_sat (aq, 1 atm)", "5.67e-3", "M", "derived",
    "Henry's law: C_sat = H_cp * p = 5.6e-5 mol m-3 Pa-1 * 101325 Pa = 5.67 mol m-3 = 5.67 mM. "
    "corrected 2026-08-22 on retrieval of the source. This row previously used H_cp = 4.9e-5, "
    "giving 5.0 mM, and cited the 2015 edition of Sander's compilation -- which was never "
    "retrieved. the edition now held carries exactly one propene entry, 5.6e-5 mol m-3 Pa-1, "
    "attributed to Plyasunov and Shock (2000). Where 4.9e-5 came from could not be established, "
    "so it is withdrawn rather than defended. the +14 pct move is safe and moves no reported "
    "current: this row bounds the gas-liquid delivery duty, not the electrode current, because "
    "%.1f pct of the generated oxidant is exported from the film (see the sensitivity)" % _EX["exported_pct"],
    "Sander, 'Compilation of Henry's law constants (version 5) for water as solvent', "
    "Atmos. Chem. Phys. 2023, 23, 10901-12440, DOI 10.5194/acp-23-10901-2023",
    "propene entry, H_cp = 5.6e-5 mol m-3 Pa-1 at 298 K, attributed to Plyasunov and Shock (2000); "
    "the sole propene entry in the compilation",
    "The ex-cell propylene epoxidation entry is bulk-reaction-limited: at %.0f mA cm-2 the solver "
    "shows %.1f pct of the generated oxidant exported from the film (%.1f pct on a %.0f um film), so "
    "this row bounds the gas-liquid delivery duty, not the electrode current. It enters the solve "
    "through the reaction layer x_k = (D/kC)^(1/2) = %.0f um and the planar propylene cap "
    "%.2f mA cm-2; a 14 pct change in C_sat moves x_k by 7 pct and the in-film share by half a "
    "percentage point." % (_EX["i_op_mAcm2"], _EX["exported_pct"], _EX["exported_pct_half_delta"],
                            _EX["half_delta_um"], _EX["x_k_um"], _EX["i_cap_P_mAcm2"]))
add("5. Concentrations", "n_carrier (electrons per carrier turnover)",
    "0.1 - 6.0 (per reaction; see Table S2)", "-", "assumption",
    "new row 2026-08-23. N is one of the four factors of i_lim = n F D C / delta and was the only "
    "one with no registry row at all -- D, C and delta each had one. It is exactly as linear in "
    "i_lim as C is. Assigned per reaction from the balanced half-reaction of the carrier as "
    "written in the source, which is a reading of the mechanism, not a measurement",
    "the balanced half-reaction of each exemplar, as reported", "",
    "sensitivity. 48 of the 50 rows take integer n from an unambiguous half-reaction and are not "
    "in doubt. The exposure is the two fractional rows, where n < 1 encodes a chain-carrying "
    "regime -- catalytic in electrons -- rather than a stoichiometry: the radical-cation "
    "Diels-Alder at n = 0.1 and the Co-H alkene isomerization at n = 0.2. Those are declared "
    "mechanistic choices with no measurement behind them, and i_lim scales linearly with them. "
    "Both sit far below every threshold in every architecture, and raising each to n = 1 -- i.e. "
    "abandoning the chain entirely, the most generous possible revision -- multiplies them by 10x "
    "and 5x and leaves both still below 25 mA cm-2 in every architecture. No published count "
    "moves anywhere in the range, so the fractional-n choice cannot flip a reported verdict."),
add("5. Concentrations", "Trace initializations (Med_ox, H+ in aprotic)",
    "1e-5 x C_med; 1e-3 mol m-3", "mol m-3", "assumption",
    "nonzero Dirichlet and initial values for the log-concentration degrees of freedom; a solver "
    "necessity, not a physical claim", "declared solver setting", "",
    "tr(C) was moved a full decade in both directions, 1e-5 -> 1e-4 and 1e-5 -> 1e-6, and the "
    "mediated matrix re-solved in an isolated copy each time. The seed is not exactly inert: 45 "
    "of the 48 (reaction, reactor) entries change at 1e-4 and 42 of 48 at 1e-6. The changes are "
    "negligible in size, and they scale with the seed as a perturbation should -- the largest "
    "absolute movement is 0.0059 mA cm-2 at 1e-4 and 0.00059 mA cm-2 at 1e-6, a factor of ten "
    "for a factor of ten in the seed, and in relative terms at most 0.008 pct. The largest "
    "movers are the two fastest systems at the rotating cylinder and the RDE, where the current "
    "is largest in absolute terms. The counts clearing 25 and 50 mA cm-2 among the mediated "
    "entries are unchanged at 31 and 24 at both ends, so no reported quantity depends on the "
    "seed.")

# -- 6. Electrolyte conductivities (Table S4; the i2L/kappa stack) -----------
# HEADLINE RESULT OF THE 2026-08-02 SOURCING PASS (docs/KAPPA_SOURCING_DOSSIER.md), which SUPERSEDES
# the earlier "not one reaches state A or B": NINE of the 49 registered conductivities are now
# DERIVED (state B) and forty remain assumptions. None reaches measured (state A) -- the one state-A
# measurement found in the whole category (0.1 M Bu4NPF6/THF = 0.51 mS cm-1 at 22.0 +/- 1.0 C, Zhang
# et al., JACS Au 2023, 3, 2280-2290, Table 1) lands on an UNUSED-LEGACY row of
# data/electrolytes.csv and therefore emits no registry row here.
#   DERIVED, five by Casteel-Amis from Dorn et al. 2024 Table 3 p. 1499:
#       0.043 / 0.077 / 0.1 / 0.25 / 0.3 M Bu4NBF4/MeCN
#   DERIVED, four by the CRC p. 5-71 + Concentrative-Properties route:
#       1 M NaOH aq, 2 M NaCl aq, 1 M KHCO3 aq, 1 M Na2CO3 aq
# Two structural facts still hold and are recorded on every row:
#   (1) kappa enters ONLY the voltage/thermal path. It enters no transport quantity. 45 of the 49
#       rows are therefore display-only (9 of those 45 are now derived display-only).
#   (2) Exactly four rows carry a §S6 conclusion, and their margins were computed individually.
#       The inherited blanket claim "conclusions robust to 2x" is provably FALSE: the DMF margin is
#       1.18x. Those four rows carry their own sensitivity strings below. Of the four, one is now
#       derived (1 M NaOH aq) and one is derived (0.25 M Bu4NBF4/MeCN); THF and DMF stay C.
QAM_METH = ("no measured conductivity for this exact salt / solvent / concentration was located. "
            "The inherited citation was a limiting-conductivity table (Izutsu, 2nd ed.), which "
            "cannot supply kappa at 0.03-1 M at any concentration in this registry: for "
            "Bu4NBF4/MeCN the Onsager limiting law Lambda = Lambda0 - S sqrt(c), with the verified "
            "Lambda0 = 171.1 and S = 358.7 computed from the verified eps and eta, goes negative "
            "above 0.228 M, and the Lee-Wheaton / Fuoss-Justice extension reaches only ~0.02 M. "
            "The citation did not support the value and has been withdrawn")
# B12. The earlier promise -- that the Dorn SI "may convert 8-10 of these rows to state A in a
# single pass" -- is NOT supported by what was retrieved and has been corrected. Dorn's Table 3
# (p. 1499) contains exactly FOUR Casteel-Amis fits: ACN/(C2H5)4NBF4, ACN/(C4H9)4NBF4, MeOH/NaI and
# MeOH/KSCN. Only one matches a registry salt (Bu4NBF4/MeCN), and it has already been adopted here
# on five rows. NaI and KSCN in MeOH appear in no registry row.
KAPPA_PULL = (" dorn'S supporting information has now been retrieved (2026-08-22), which closes "
              "the item that used to head this list and narrows what remains. Je3c00691_si_001.pdf "
              "carries the raw isotherms for 41 salts x 4 solvents, 21 measured points each: "
              "water, acetonitrile, methanol and ethanol, and nothing else. It supplied the "
              "Bu4NBF4/MeCN rows and three aqueous rows directly. it cannot reach: any DMF row "
              "(no DMF was measured), any THF row (no THF), or any perchlorate (NaClO4 is not "
              "among the 41 salts). Its NaBr in acetonitrile is a dash -- attempted, no fit -- so "
              "the two NaBr/MeCN rows are not closable from it either, which is a definitive "
              "negative rather than an untried lead. "
              "what remains, in order of yield: (i) Barthel & Neueder, Electrolyte Data "
              "Collection, dechema Vol. Xii (print-only; still the highest yield per unit effort "
              "for the amide family, and the only broad source that covers DMF). "
              "(ii) for the THF rows, Das, J. Solution Chem. 2008, 37, 947-955, "
              "DOI 10.1007/s10953-008-9288-9, has now been retrieved (papers for model/) and it "
              "does not settle them, which is worth stating so nobody pulls it twice. Its Table 1 "
              "measures LiBr in THF at 298.15 K over c = 0.01155 to 0.31623 mol dm-3, twenty "
              "points, with Lambda falling to a minimum of 0.1795 S cm2 mol-1 at 0.0205 M and "
              "then rising to 0.8100 at the top point, i.e. kappa from 0.0023 to 0.2561 mS cm-1 "
              "-- still roughly 10x below the 3.0 M this project uses. (An earlier reading gave "
              "the range as 0.0071-0.035 M at Lambda = 0.18-0.20: the three salts interleave in "
              "the text layer, and that pairs LiCl's concentration column with LiBr's Lambda "
              "column, truncated at the eighth row. Separated by x-coordinate on 2026-09-13, the "
              "same discipline the CRC viscosity and Chambers-Stokes conductance tables needed.) It confirms the "
              "physics that makes this row hard (LiCl, LiBr and LiBF4 form symmetrical triple "
              "ions, and the conductivity minimum sits at c_min = 4.9e-3 mol dm-3, so at 3.0 M "
              "the solution is ~600x above the minimum and deep in the triple-ion regime where "
              "Lambda rises again with concentration). Consequence for this row: the carried "
              "3.0 mS cm-1 at 3.0 M implies Lambda = 1.0 S cm2 mol-1, a five-fold rise over "
              "Das's measured value at 0.01 M. Triple-ion formation makes that direction "
              "correct, but the magnitude is unverified and no measurement at preparative "
              "concentration was located. "
              "(iii) Minc & Werblan, Electrochim. Acta 1962, 7, 257-266 (retrieved, in "
              "papers for model/) for alkali perchlorates in acetonitrile. "
              "(iv) One benchtop conductivity measurement per salt/solvent family calibrates B in "
              "Lambda(c) = Lambda0/(1 + B sqrt(c)) and upgrades the whole family to state B at "
              "+/-15 pct -- and for the two rows that still carry a §S6 verdict this is the "
              "cheapest route to state A by a wide margin.")
# Casteel-Amis (Casteel & Amis, J. Chem. Eng. Data 1972, 17, 55), the named method behind the five
# Bu4NBF4/MeCN derivations. Written out here so the arithmetic is reproducible from this registry
# alone, as state B requires:
#     kappa(m)/kappa_max = (m/m_max)^a * exp[ -b (m - m_max)^2 - a (m/m_max - 1) ]
# SIGN CORRECTED 2026-08-22. The comment previously showed +b, which is the convention
# that does NOT reproduce Dorn's own kappa_calc column: -b matches six independent
# isotherms to better than 0.1 pct and +b misses by 6-95 pct. See data/casteel_amis.py,
# which implements this once and gates it (G-CA); the values here were typed literals
# produced with the wrong sign before that file existed.
# with the MEASURED fit parameters of Dorn et al. Table 3, p. 1499 for ACN / (C4H9)4NBF4:
#     kappa_max = 33.40 mS cm-1, m_max = 1.48127 mol kg-1, a = 0.78646, b = -0.02156
# Molalities used (from the registered molarity via the solution density; see CA_CONV below):
#     0.043 M -> 0.056 -> 5.18 | 0.077 M -> 0.101 -> 8.07 | 0.100 M -> 0.133 -> 9.87
#     0.250 M -> 0.347 -> 18.95 | 0.300 M -> 0.423 -> 21.34   (all mS cm-1, 25 C)
CA_CONV = ("molarity -> molality, stated explicitly because state B requires the arithmetic to be "
           "reproducible and because the convention matters at the 4 pct level. The route is the "
           "solution density, not the pure-solvent density: rho_soln = (rho0 + c M/1000) / "
           "(1 + c V_phi/1000) and m = c / (rho_soln - c M/1000), with M = 329.27 g mol-1, "
           "rho0 = rho(MeCN) = 0.7768 g cm-3 and an apparent molar volume V_phi = 287 cm3 mol-1 "
           "(an ordinary value for Bu4NBF4, and the value the adopted molalities imply). This "
           "reproduces every adopted molality to three decimals: 0.043 M -> 0.056, 0.077 -> 0.101, "
           "0.100 -> 0.133, 0.250 -> 0.348, 0.300 -> 0.424 mol kg-1. V_phi is itself a declared "
           "assumption, so the convention spread is bounded rather than ignored: the pure-solvent "
           "shortcut m = c/rho0 gives m = 0.322 and kappa = 18.1, and the salt-displacement "
           "shortcut m = c/(rho0 - cM/1000) gives m = 0.360 and kappa = 19.4, against the adopted "
           "18.9 at m = 0.347. That 18.1-19.4 spread sits well inside the declared 15-23 band and "
           "moves the microfluidic MeCN ceiling only over 674-680 mA cm-2 against that cell's own "
           "transport ceiling of 111 mA cm-2, a margin of 6.09x to 6.14x, so no verdict "
           "anywhere in §S6 turns on the choice.")
ECOND_PROV = {
 # -- the four rows that carry a §S6 conclusion -----------------------------------------
 "0.25 M Bu4NBF4/MeCN": (
   "measured: read off the raw kappa(c) isotherm in the Dorn et al. Supporting Information. "
   "The Casteel-Amis reconstruction this row used to carry (Casteel & Amis, J. Chem. Eng. "
   "Data 1972, 17, 55) is retained below as the superseded route, applied to the measured fit "
   "of Dorn et al., Table 3, p. 1499 for ACN / (C4H9)4NBF4: kappa_max = 33.40 mS cm-1, "
   "m_max = 1.48127 mol kg-1, a = 0.78646, b = -0.02156, validity range 9.10, MAPE 1.65 pct. At "
   "m = 0.347 mol kg-1 (0.25 M; conversion below) that fit returns kappa = 18.95 mS cm-1, which "
   "was the adopted 18.9 before the raw isotherm was read; the measurement gives 19.95, so the "
   "fit-and-invert route was 5.6 pct low. " + CA_CONV + " Independently validated at 1 M against Gong et al. Table 3, p. 3519 "
   "(32.75 derived vs 32.3 tabulated, +1.4 pct). Supersedes the earlier mass-action treatment: the "
   "bound of 24-36 mS cm-1 built on Lambda0 = 171.1 and K_A = 5.6 was a Lee-Wheaton extrapolation "
   "25x above its own fitted range (2e-4 to 1e-2 mol dm-3) and has been withdrawn, as has the "
   "inherited Izutsu limiting-conductivity citation",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502; Gong, Fang, Gu, Li & "
   "Yan, Energy Environ. Sci. 2015, 8, 3515-3530; method: Casteel & Amis, J. Chem. Eng. Data 1972, "
   "17, 55",
   "Dorn supporting information, Table SI 85, p. 171 (ACN / (C4H9)4NBF4, 298.15 K, 101 kPa): "
   "0.25 M is m = 0.347 mol kg-1, read between the measured points (0.2960, 18.16) and "
   "(0.4094, 22.13) mS cm-1, which interpolate to 19.95. The alternative locator is the "
   "article-body Casteel-Amis fit -- Table 3, p. 1499 (m_max 1.48127, kappa_max 33.40, "
   "a 0.78646, b -0.02156, MAPE 1.65 pct), the fit-and-invert route, which returns 18.9; "
   "a reader opening p. 1499 would not have found 19.95 there. Cross-check: Gong Table 3, "
   "p. 3519 (Bu4NBF4/AN, 1 M, 32.3 mS cm-1, tabulated after Izutsu 2009)",
   "Carries a conclusion. Band 15-23 mS cm-1, wider than +/-10 pct because Dorn's own "
   "dissertation, p. 74, applies his own Casteel-Amis equation at m = 0.075 and prints "
   "kappa_ref = 7.04 where the published Table 3 parameters give 6.465, a +8.9 pct unexplained "
   "self-inconsistency. " +
   "Fig. 7 margins recomputed at the adopted 19.95 mS cm-1, and judged against each "
   "architecture's OWN transport ceiling rather than a declared design current: " +
   ", ".join("%s %.2fx" % (_n, _m) for _n, _m in _MECN_M[:-1]) +
   ". The two shortfalls would reverse only at " +
   " and ".join("%.1f mS cm-1 (%.2fx carried, %s)" % (_k, _f, _n) for _n, _k, _f in _MECN_X) +
   ", both far outside the 15-23 band, so no MeCN verdict turns on where inside its own "
   "measurement band the value sits. Those same two ARE bound-dependent on the kappa(T) axis of "
   "S6.3 and on the beaker gap these cells share, and are flagged on both."),
 "0.2 M NaI/DMF": (
   "derived 2026-08-22, replacing an unsourced 8.0 that had no derivation of any kind. The "
   "reason for the change is provenance, not preference: 8.0 was a number with no chain behind "
   "it, and this one has a two-step chain a reader can redo. "
   "step 1, Lambda0, now directly measured rather than summed: Lambda0(NaI, DMF) = "
   "81.35 +/- 0.04 S cm2 mol-1 at 25 C [Krumgalz & Barthel, Z. Phys. Chem. 1984, 142, 167-178, "
   "Table 2, NaI block, 25 C column; PDF retrieved and read off the page]. That replaces the "
   "Kohlrausch sum this row used to carry -- lambda0(Na+) 29.81 + lambda0(I-) 52.11 = 81.92 from "
   "Gopal & Jha Table 2 p. 81 -- which agrees with it to -0.70 pct and is retained as the "
   "cross-check. The same table's literature column quotes 81.9 from both Singh and Ames. "
   "The hard Kohlrausch ceiling therefore becomes kappa <= c Lambda0 = 16.27 mS cm-1. "
   "step 2, the attenuation at 0.2 M: taken from a measurement of the same salt. Dorn's "
   "Supporting Information measures NaI in methanol across the full range (Table SI 97, p. 197); "
   "with Lambda0(NaI, MeOH) = 45.23 + 62.63 = 107.86 from the CRC/Vanysek table verified in this "
   "pass, the measured Lambda/Lambda0 at 0.2 M is 0.539. Transferring it gives "
   "kappa = 0.2 x 81.35 x 0.539 = 8.77 mS cm-1. "
   "third route, independent of both and using only same-system measurements: Krumgalz & Barthel "
   "also report the association constant, K_A = 7.50 +/- 0.57 dm3 mol-1 for NaI in DMF at 25 C "
   "(same table). Solving the association equilibrium with Debye-Huckel activity coefficients at "
   "their own distance parameter R2 = 1.131 nm gives a free-ion fraction alpha = 0.702 at 0.2 M, "
   "and with Onsager relaxation Lambda = alpha(Lambda0 - S sqrt(alpha c)) = 41.5, i.e. "
   "Lambda/Lambda0 = 0.510 and kappa = 8.30 mS cm-1 -- within 5 pct of the adopted value, from "
   "entirely different inputs. it is not adopted as primary, and the reason is consistency: it "
   "extrapolates a dilute conductance treatment some 20-200x beyond the range Krumgalz & Barthel "
   "fitted, and this registry has already withdrawn a value (the Lee-Wheaton bound on "
   "Bu4NBF4/MeCN) for being a 25x extrapolation beyond its own fitted range. The methanol route "
   "is preferred because it is measured at the right concentration and transfers one solvent "
   "step in a known direction, rather than measured in the right solvent and extrapolated in "
   "concentration. That the two disagree by only 5 pct is the useful fact. "
   "the one assumption, stated: that the attenuation at equal molarity is the same in DMF as in "
   "methanol. It is not exactly, and the direction is known -- DMF has the higher permittivity "
   "(36.7 against 32.7) so it pairs less and attenuates less -- which makes 8.83 a floor on "
   "kappa rather than a best estimate. Calibrating the Onsager limiting law on that same "
   "methanol measurement (it overshoots by 1.136x there) and applying the correction to DMF "
   "gives Lambda/Lambda0 = 0.593, i.e. 9.72 mS cm-1, which is the better estimate. The floor is "
   "carried because its derivation is the shorter and more checkable of the two, and the "
   "difference between them is recorded here rather than hidden in a choice. "
   "Prue & Sherrington, Trans. Faraday Soc. 1961, 57, 1795-1808 report the iodides in DMF in "
   "excellent accord with Fuoss-Onsager assuming complete dissociation, which supports the "
   "direction; not retrieved, taken from the abstract, and used for direction only. "
   "what this does to the dependent claims, reported whichever way it fell: the unstirred-beaker "
   "steady state at 100 mA cm-2 drops 202 -> 186 C (still far above DMF's 153 C boiling point, "
   "but the margin to the kappa = 11.15 flip narrows from 1.39x to 1.26x); the cell voltage at "
   "50 mA cm-2 drops 14.9 -> 13.7 V (still inside the 10-20 V range); the unstirred-beaker "
   "i_boil rises 84.8 -> 88.8 and the microfluidic 1093 -> 1116 mA cm-2. No verdict "
   "changes in either direction. "
   "what is still missing is Lambda(c) at 0.2 M: no "
   "measurement of the conductance attenuation of NaI in DMF at working concentration was located, "
   "so the value cannot be derived and the row stays state C. Solvent properties verified as "
   "before: DMF eps = 36.81, eta = 0.8455 mPa s, rho = 0.943802 g mL-1 at 298.15 K. Cheapest route "
   "to state A: measure it -- 0.2 M NaI in dry DMF, calibrated probe, 25 C, ten minutes; the result "
   "must land in (0, 16.4) mS cm-1, so the row is now checkable, which it was not before",
   "Gopal & Jha, Indian J. Chem. 1977, 15A, 80-83 (lambda0, state A); Bhat, Mohan & Susha, Indian "
   "J. Chem. 1996, 35A, 825-831 (cross-validation); Kinart, Molecules 2024, 29, 1371 (solvent "
   "properties only; not the conductivity)",
   "Gopal & Jha Table 2, p. 81, DMF column, 25 C (Na+ 29.81, I- 52.11 S cm2 mol-1); Bhat Table I, "
   "p. 827; Kinart Table 1 (DMF properties at 298.15 K) -- supports the solvent constants, not "
   "kappa",
   "Carries a conclusion, and is the most exposed number in the category. Band 4-16 mS "
   "cm-1, with a hard physical ceiling at state B: kappa <= c Lambda0 = 2.000e-4 mol cm-3 x 81.92 S "
   "cm2 mol-1 = 16.38 mS cm-1, since Lambda(c) <= Lambda0 for all c > 0. The tabled 8.0 implies "
   "Lambda/Lambda0 = 0.488 and the microfluidic flip requires 0.453. Which side of 0.453 the "
   "truth falls on is bounded by measurement. "
   "Two routes, both anchored on measured data rather than on a correlation read outside its "
   "range. (A) same-salt transfer: Dorn's Supporting Information measures NaI in methanol across "
   "the full range (Table SI 97, p. 197); with Lambda0(NaI, MeOH) = 45.23 + 62.63 = 107.86 from "
   "the CRC/Vanysek table, the measured attenuation at 0.2 M is "
   "Lambda/Lambda0 = 0.539, which transferred unchanged to DMF gives 8.77 mS cm-1. That is a "
   "lower bound rather than an estimate, because DMF has the higher permittivity (36.7 against "
   "32.7) and so must pair less and attenuate less than methanol. (B) onsager calibrated on that "
   "same measurement: the 1:1 limiting law overshoots the measured methanol attenuation by a "
   "factor 1.136 here; applying that correction to the DMF limiting law (0.674) gives 0.593, "
   "i.e. 9.72 mS cm-1. Physical support, direction only: Prue & Sherrington, Trans. Faraday Soc. "
   "1961, 57, 1795-1808 measured twelve salts in DMF and report the iodides in excellent accord "
   "with Fuoss-Onsager assuming complete dissociation, so no ion-pairing term should drive DMF "
   "below methanol; not retrieved in full text -- taken from the abstract and used for direction, never as a "
   "number. so the carried 8.0 is conservative, and 0.453 lies below the measured attenuation of "
   "the same salt in a lower-permittivity solvent, which is backwards. The value is kept at 8.0: "
   "a higher kappa only makes every thermal conclusion safer, so holding the low end costs "
   "nothing and cascades into no figure. The adopted value is the "
   "derived 8.77 of step 2 above, and what follows uses it. "
   "(a) Judged against each architecture's own transport ceiling, DMF clears every modelled "
   "archetype except %s and the stack, and its microfluidic margin is %.1fx. The binding "
   "kappa-axis verdict is the %s, which reverses if kappa rises to %.2f mS cm-1, i.e. %.2fx the "
   "carried 8.77, %s. What is still missing is a direct measurement of Lambda(0.2 M) for this "
   "salt in this solvent. The cheapest route to settling it: 0.2 M NaI in dry DMF, calibrated "
   "probe, 25 C, ten minutes. "
   % (" and ".join("the %s (margin %.2fx)" % (a.replace("RDE 1600 rpm", "rotating disc")
                                               .replace("rotating cyl. 3000 rpm", "rotating cylinder"), m)
                   for a, m, _ in _DMF_FAILS),
      _th_margin(0.877, 152.8, _TH_MIC),
      _DMF_BIND[0].replace("RDE 1600 rpm", "rotating disc").replace("rotating cyl. 3000 rpm", "rotating cylinder"),
      _DMF_BIND[2]*8.77, _DMF_BIND[2],
      ("inside this row's own 4-16 band, so that failure is conditional on where in the band the "
       "value sits" if _DMF_BIND[2]*8.77 < 16.0 else
       "above the top of this row's own 4-16 band, so that failure is band-proof"))
   +    "(b) two further sentences rest on this row, at the adopted 8.77: 'the full lumped balance places its passive steady state at "
   "T_ss ~ %.0f C, far above DMF's 153 C boiling point' flips at kappa_crit = %.2f mS cm-1, "
   "a margin of %.2fx, which is inside the honest 4-16 band; and 'the same cell at 50 mA cm-2 "
   % (_dmf_tss(), _dmf_flip()*10, _dmf_flip()/0.877)
   + "draws 13.8 V, which is the 10-20 V range common in academic non-aqueous reports' holds only "
   "over kappa = 5.68-13.16 mS cm-1 (x0.648 down, x1.501 up). Both are stated as conditional on "
   "the adopted kappa in S6. The binding kappa-axis margin for this row is %.2fx, at the %s; "
   "it and the two statements above are labelled as conditional where they appear."
   % (_DMF_BIND[2], _DMF_BIND[0].replace("RDE 1600 rpm", "rotating disc")
      .replace("rotating cyl. 3000 rpm", "rotating cylinder"))),
 "3.0 M LiBr/THF": (
   "reclassified. this row was labelled measured-lit, but the cited source supports the "
   "concentration, not the conductivity: Peters et al. Give LiBr 1.0 mol / 320 mL THF = 3.0 M "
   "stock. The value 3.0 mS cm-1 came from the row's own note -- 'heavily ion-paired ether medium, "
   "kappa order-of-mS/cm' -- which is an assumption. It cannot be derived either: THF has "
   "eps = 7.6, so the Bjerrum critical distance q = e^2/(8 pi eps0 eps kB T) = 3.7 nm at 25 C, an "
   "order of magnitude beyond contact distance, and ionic association is essentially complete",
   "Peters et al., Science 2019 (Supplementary Materials)",
   "SM pp. S15 and S21 -- supports the 3.0 M concentration only",
   "Carries a conclusion, and its support is weaker than the value alone suggests. "
   "Das, J. Solution Chem. 2008, 37, 947-955 (retrieved) measures LiBr in THF at 298.15 K over "
   "c = 0.0116 to 0.3162 mol dm-3 -- ten times closer to the working 3.0 M than anything this "
   "is available -- and the picture it gives is not reassuring. "
   "(1) A hard measured floor: kappa(0.3162 M) = "
   "0.256 mS cm-1 (Table 1). Since kappa rises with c up to the conductivity maximum, "
   "kappa(3.0 M) >= 0.256, which independently corroborates the 0.206 floor "
   "derived from Lee's cell resistance -- two unrelated routes, 24 pct apart, in the right order. "
   "(2) the carried 3.0 implies A flattening that is not measured. over the measured "
   "triple-ion branch (0.05-0.32 M) the data scale as kappa ~ c^1.75. Getting from the highest "
   "measured point to 3.0 mS cm-1 at 3.0 M requires kappa ~ c^1.09 over the remaining 9.5-fold "
   "rise in concentration. Such flattening is physically expected -- it is the approach to the "
   "conductivity maximum as viscosity takes over -- but where that turnover sits has never been "
   "measured for LiBr in THF, and the carried value assumes it happens early. "
   "(3) the measured scaling cannot simply continue, and A stoichiometric calculation shows why. "
   "Continuing kappa ~ c^1.75 to 3.0 M would give 13.1 mS cm-1, four times the carried value, "
   "so the extrapolation had to be tested, not waved away. It fails on solvent availability. Peters' own recipe is 1.0 mol LiBr in 320 mL "
   "THF; at rho = 0.8833 g cm-3 and M = 72.106 that is 3.92 mol THF per mole of LiBr. Li+ in an "
   "ether is four-coordinate, so the solvation shell of the cation alone requires 4.0 -- there is "
   "a 2 pct deficit, and nothing at all is left for Br- or for bulk. The conclusion is not "
   "sensitive to the exact coordination number: at n = 3 only 23 pct of the THF is free, at "
   "n = 4 none is, at n = 5 there is a 28 pct shortfall. "
   "By contrast Das's highest measured point, 0.3162 M, has 39 mol THF per mole of LiBr -- ten "
   "times the solvation requirement, with abundant bulk solvent for triple ions to move through. "
   "the two concentrations are not the same kind of liquid. The c^1.75 branch is the behaviour "
   "of ions migrating through bulk THF; at 3.0 M that bulk does not exist, the system is a "
   "solvate rather than a solution, and kappa must have passed its maximum before that point. "
   "independent support, same solvent and nearly the same concentration: Cai et al., J. Am. "
   "Chem. Soc. 2023, 145, 25716-25725 run 2 M LiBF4 in THF and report from MD that in cyclic "
   "ethers Li+ is only partially solvated and the ions form contact ion pairs and aggregates, "
   "whereas linear ethers keep Li+ fully solvated and the ions dispersed -- exactly the "
   "solvation-starved picture the stoichiometry predicts. BOTH PAPERS AND BOTH SUPPORTING "
   "INFORMATIONS WERE RETRIEVED AND READ ON 2026-08-31, and the earlier note that their numeric "
   "conductivities were merely unretrieved is now settled the other way: neither reports an "
   "extractable number. Cai's conductivity figure (Fig. 2) turns out to plot MD-derived Li+ "
   "migration rates, radial distribution functions and coordination numbers, not measured "
   "conductivities; its only measured electrochemistry is the EIS profiles of SI Figs. S2-S3, "
   "which are Nyquist plots with no tabulated resistance or cell constant, and the whole SI "
   "text layer contains the word conductivity exactly once, in the methods. Fu reports the "
   "ranking LiTFSI > LiPF6 > LiBOB > LiClO4 > LiBF4 in the body and puts the values in Fig. S4, "
   "whose caption carries no text layer at all. So both remain corroboration of the REGIME and "
   "neither can be promoted to a value -- which is now a checked statement rather than an open "
   "action. Reading either figure by eye off the raster was rejected: a plotted axis is not a "
   "source. "
   "what this settles and what it does not. It excludes the 13.1 extrapolation, which is why "
   "that number is not carried, and it places 3.0 M on the far side of the conductivity maximum "
   "where the carried value's implied flattening is the physically correct behaviour. It does "
   "not locate the maximum, so it does not put a number on kappa(3.0 M) and does not restore an "
   "upper bound. "
   "what this does to the band: the old 0.2-6.6 was built before any of this data existed -- its "
   "floor from Lee's cell resistance and its top from an ohmic-differencing argument. The floor "
   "is 0.256, measured. the top cannot be defended at 6.6: nothing located excludes "
   "values above it, and the only extrapolation anchored in measurement points higher. The band "
   "is therefore reported as 0.26 mS cm-1 to not established above; the two rotating-electrode THF verdicts reverse only "
   "above %.1f mS cm-1 (the rotating disc), which every measured-data continuation below stays "
   "under. The arithmetic behind the floor: " % (10*_thf_flip("RDE 1600 rpm")*0.30)
   + "Carries a conclusion. Band 0.2-6.6 mS cm-1 at a value of "
   "3.0. The lower end is a state-B hard floor: total cell resistance <= V/I = 3.2 V / 0.520 A = "
   "6.154 ohm in a coaxial annulus with R_i 9.5 mm, R_o 11.0 mm and L = 18.43 cm derived from the "
   "stated 17.8 mL annulus volume, giving kappa >= 1.266e-3 / 6.154 = 0.206 mS cm-1 [Lee et al., "
   "Org. Process Res. Dev. 2022, 26, 2674-2684, main text Results & Discussion, SI Fig. S3 p. S6 "
   "and CFD block p. S22]. The upper end is not 8.8 and not the 3.29 that ohmic differencing first "
   "returned: that construction assumes equal non-ohmic overpotential across LiBr concentrations, "
   "which is refuted for Al anodes in THF by Zhang, Guan, Wang, Lin & See, Chem. Sci. 2023, 14, "
   "13108-13118 (Br- concentration is precisely what relieves Al2O3 passivation, so Lee's voltage "
   "differences are partly anodic, not ohmic), and it rests on dV = 0.2 V between two "
   "two-significant-figure voltages, so dV = 0.10 V -- admitted by rounding alone -- raises it to "
   "6.58. do not adopt 1.5 mS cm-1 as a derived point value: it fails state B (its point value is "
   "set by an assumed kappa(1.5 M) with no source, its own bracket spans 1.24-2.48), and it would "
   "state a ceiling ~30 pct below the model's own best estimate in the manuscript'S favour. "
   "what the band buys, judged against each architecture's OWN transport ceiling rather than a "
   "declared design current: %s. So the band does not decide the verdicts this section reports -- "
   "the thin-gap chip clears throughout and both rotating cells and the stack fail throughout, "
   "and what the band alone decides is the three centimetre-gap cells, which pass at the carried "
   "value and above and fail only at the state-B floor, where the ceiling has fallen to the "
   "transport ceiling itself. One live sentence is tighter than any architecture verdict: the zero-gap 'beyond passive and forced-air rejection' "
   "claim flips at only 1.297x (U'_req crosses the 0.08 W cm-2 K-1 forced-air ceiling at "
   "kappa = 3.89 mS cm-1; U' = 0.0986 at 3.0, 0.0544 at 6.58, 1.2013 at the floor), so it does "
   "not survive the top of the band and is quoted with that margin where it appears. Recomputed "
   "from "
   % "; ".join(
       "at %.3f mS cm-1 the ceilings are %s mA cm-2 against transport ceilings of %s, so %d of "
       "the %d architectures clear"
       % (kk * 10.0,
          "/".join("%.1f" % _th_ceiling(kk, 66.0, r) for r in _TH_RX),
          "/".join("%.1f" % r[4] for r in _TH_RX),
          sum(_th_margin(kk, 66.0, r) >= 1.0 for r in _TH_RX), len(_TH_RX))
       for kk in (0.0206, 0.30, 0.658))
   + "the thermal model at kappa = 3.0 mS cm-1 and T_b = 66 C, and judged against each architecture's "
   "OWN median transport ceiling rather than a declared design current, THF does NOT boil in either "
   "batch cell, in the recirculating cell or in the microfluidic chip: those four verdicts would "
   "reverse only at %.2f-%.2fx the carried conductivity, far below it, because transport binds "
   % (min(_kappa_multiple(0.30, 66.0, r[0]) for r in _TH_RX if r is not _TH_STACK and _th_margin(0.30, 66.0, r) >= 1.0),
      max(_kappa_multiple(0.30, 66.0, r[0]) for r in _TH_RX if r is not _TH_STACK and _th_margin(0.30, 66.0, r) >= 1.0))
   + "before heat does in a cell that reaches only 8-17 mA cm-2. Where THF does fall short the "
   "multipliers are %.1fx (rotating disc) and %.1fx (rotating cylinder), with the zero-gap "
   % (_thf_flip("RDE 1600 rpm"), _thf_flip("rotating cyl. 3000 rpm"))
   + "stack unreachable on kappa at all (at 1000 mA cm-2 its activation term alone puts out "
   "0.71 W cm-2 against 0.043 W cm-2 of passive rejection, so no conductivity saves it). "
   "The binding verdict is the rotating disc at %.1fx, against a band whose top is 2.19x "
   % _thf_flip("RDE 1600 rpm")
   + "the carried value, so every THF verdict in this section is band-proof. "
   "A SECOND AND TIGHTER TEST, because the band is not the only thing a reader can do with the "
   "measured data. Das's twenty points rise as kappa ~ c^n over the top decade, with n = 1.75 "
   "fitting from 0.05 M, 1.94 from 0.10 M and 2.20 from 0.15 M; continued to 3.0 M those give "
   "10.9, 18.3 and 35.6 mS cm-1. The rotating-disc verdict reverses at %.1f mS cm-1 and the "
   "rotating-cylinder verdict at %.1f, so both survive every one of those continuations, the "
   "disc clearing the steepest of them by %.0f pct."
   % (10*_thf_flip("RDE 1600 rpm")*0.30, 10*_thf_flip("rotating cyl. 3000 rpm")*0.30,
      100*(10*_thf_flip("RDE 1600 rpm")*0.30/35.6 - 1)) + " None of those continuations is itself sound: each "
   "crosses a conductivity maximum the measured range never reaches, and at 3.0 M there are 4.08 "
   "THF per Li+, so on four-coordinate lithium essentially the whole solvent is bound and the "
   "dilute triple-ion law has no free solvent left to work with. The carried 3.0 mS cm-1 "
   "corresponds to n = 1.39 from Das's 0.1 M point, i.e. it already assumes the roll-off rather "
   "than extrapolating through it. "
   "A SECOND SAME-SOLVENT ANCHOR, state A: Zhang, Gu, Wang, Ware, Lu, Lin, Qi and See, JACS Au "
   "2023, 3, 2280-2290, Table 1 measures 0.1 M LiClO4 in THF at 62.6 uS cm-1 (22.0 +/- 1.0 C), "
   "against Das's LiBr at the same 0.1 M and 25 C of 26.8 uS cm-1 -- same solvent, same cation, "
   "different anion, a factor of 2.3 apart, which is the agreement this pair should show."),
 "1 M NaOH aq": (
   "derived, not measured -- reclassified 2026-08-23. Dorn's supporting information, Table SI "
   "16, p. 61 (sodium hydroxide in water at 298.15 K, 101 kPa, 21 measured points) is the "
   "source, but 1 M is not one of its measured points: at m = 0.9984 mol kg-1 -- the molality "
   "CRC's 'Concentrative Properties' assigns to 1.000 M, 3.840 mass pct -- the value is linearly "
   "interpolated between (0.6111, 112.49) and (1.2560, 215.78) mol kg-1 / mS cm-1, giving 174.5. "
   "A chord is not a measurement, and this one spans 0.645 molal through a visibly concave "
   "region. Dorn's own Casteel-Amis fit for NaOH/H2O (m_max 4.55648, kappa_max 403.97, a "
   "1.19618, b -0.00547) gives 179.23 at the same molality -- and data/casteel_amis.py "
   "reproduces Dorn's printed kappa_calc column to <0.1 pct, so the fit is trustworthy here. "
   "The chord is therefore 2.6 pct below the source's own best estimate, while the superseded "
   "CRC route (178.0) sits 0.7 pct below it -- i.e. the value this row replaced was the closer "
   "of the two. Author decision outstanding: casteel_amis.py's own rule is that the fit is used "
   "where the bracket is too wide for honest interpolation, which is exactly this case, so 179.23 "
   "is arguably the value to carry. it moves no verdict: at 179.23 the Fig. 5 aqueous ceilings "
   "run 285.9 / 302.6 / 486.2 / 841.0 / 148.9 against 282.5 / 298.9 / 481.1 / 838.4 / 148.8, "
   "margins 5.72 / 6.05 / 4.86 / 1.68 / 0.15 against 5.65 / 5.98 / 4.81 / 1.68 / 0.15 -- the "
   "same four passes and the same zero-gap failure. The 174.5 is retained pending that decision. "
   "the CRC derivation it replaces is retained as the cross-check and it was good: the p. 5-71 "
   "route (20 C table plus a temperature correction) gave 178.0, i.e. +2.0 pct against the "
   "measurement. That is the strongest available evidence that the same route is sound for the "
   "carbonate rows, which have no measured 25 C overlap table of their own. "
   "This row also matters because it is the aqueous reference of §S6: the figure's aqueous "
   "entry is now measured rather than derived.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting "
   "Information (je3c00691_si_001.pdf); cross-checked against CRC Handbook of Chemistry and "
   "Physics, 97th ed., 'Electrical Conductivity of Aqueous Solutions', p. 5-71",
   "Table SI 16, p. 61 (298.15 K, 101 kPa); CRC p. 5-71 NaOH row (20 C) with 'Concentrative "
   "Properties of Aqueous Solutions' (1.000 M = 3.840 mass pct)",
   "carries A FIG. K verdict -- this row is the figure's aqueous reference and enters a "
   "reported result. "
   "The -2.0 pct move from the derived 178.0 to the measured 174.5 lowers the unstirred-beaker "
   "boil-off ceiling from 285.05 to 282.50 mA cm-2, i.e. the margin against that cell's own "
   "transport ceiling of %.1f mA cm-2 goes from %.1fx to %.1fx. The aqueous reference clears "
   "every preparative architecture either way, so no verdict moves. "
   % (_TH_RX[0][4], 285.05 / _TH_RX[0][4], 282.50 / _TH_RX[0][4])
   + "Recomputed from the thermal model, which asserts this value against the electrolyte table "
     "before rendering."),
 "2 M NaCl aq": (
   "derived by the CRC p. 5-71 route (see the 1 M NaOH aq row for the method and its ASTM "
   "validation). CRC 'Concentrative Properties', NaCl block: 10.0 pct = 1.832 M and 12.0 pct = "
   "2.229 M, so 2.000 M = 10.846 mass pct. CRC p. 5-71 NaCl row (20 C): 5 pct = 70.1, 10 pct = 126, "
   "15 pct = 171 mS cm-1 -> 133.6-134.4 at 20 C; alpha = 1.9-2.2 pct/K -> 146-150 at 25 C. Foxboro "
   "1999 25 C NaCl column read at the same mass pct gives 147-149. Both inherited numbers are high: "
   "the tabled 160 by +8 pct and the row's own note of ~158 by +7 pct, so resolving the two against "
   "each other -- which the earlier note proposed -- would have converged on the wrong value. "
   "CLOSED 2026-08-31: Chambers, Stokes & Stokes was named here as the correct primary pull and "
   "as not retrieved. It has now been retrieved and read, and it settles the row independently. "
   "'Conductances of Concentrated Aqueous Sodium and Potassium Chloride Solutions at 25 deg', "
   "Table II, p. 986, tabulates equivalent conductances at ROUND concentrations; at c = 2.0 mol "
   "l-1 the sodium chloride column reads Lambda = 74.71 int. ohm-1 mol-1 cm2 (the potassium "
   "chloride column at the same row reads 105.23, and the two columns were separated by "
   "x-coordinate rather than by reading order, which interleaves them). kappa = Lambda c / 1000 "
   "= 74.71 x 2.0 / 1000 = 0.14942 S cm-1 = 149.4 mS cm-1 at exactly 2.000 mol l-1 and 25 C. "
   "That agrees with the carried 148.9 -- itself measured, from Dorn's isotherm at m = 2.0816 -- "
   "to 0.3 pct, by a route sharing neither apparatus nor decade with it, and it confirms that "
   "both inherited numbers were high. The international ohm of the 1956 paper is 1.00049 "
   "absolute ohm, which shifts the value by 0.05 pct and is below the agreement already shown",
   "Chambers, Stokes & Stokes, J. Phys. Chem. 1956, 60, 985-986; cross-checked against the CRC "
   "Section 5 route and the Foxboro Conductivity Ordering Guide 1999",
   "Table II, p. 986 (equivalent conductances at round concentrations, NaCl column, c = 2.0 mol "
   "l-1); CRC 'Electrical Conductivity of Aqueous Solutions', p. 5-71 (NaCl row, 20 C) with "
   "'Concentrative Properties of Aqueous Solutions', NaCl block (2.000 M = 10.846 mass pct)",
   S_KAPPA_DISPLAY),
 "2 M H2SO4 aq": (
   "stays an assumption. CRC p. 5-71 cannot support this row even though it supports the other four "
   "aqueous ones: its H2SO4 entry stops at 5 mass pct (0.5 pct = 24.3, 1 pct = 47.8, 2 pct = 92, "
   "5 pct = 211 mS cm-1) and 2 M is 17.496 mass pct -- a factor-3.5 extrapolation that returns 487 "
   "(quadratic) against 707 (linear), i.e. nonsense. The Foxboro 1999 25 C column does reach it and "
   "gives 638-651 mS cm-1 at 17.50 mass pct, but that is a vendor table with no primary attribution "
   "and therefore reaches neither state A nor state B. Note further that alpha for H2SO4 spans "
   "0.29 pct/K (at 1 mass pct) to 2.46 pct/K (at 5 mass pct) between the CRC 20 C and Foxboro 25 C "
   "tables -- a factor-8 spread proving the two lineages disagree by several per cent independent "
   "of temperature, so no temperature-corrected derivation is available for this solute at all. "
   "Page-anchoring would require Darling, J. Chem. Eng. Data 1964, 9, 421-426, DOI 10.1021/je60022a041 (kappa "
   "tabulated 0.5-99 wt pct, 0-240 F); read the ~17.5 wt pct / 25 C cell. Corroborating and "
   "actually read in this pass: Al-Salih & Abu-Lebdeh, Sci. Rep. 2024, 14, 7894, Table 1 quotes "
   "kappa_max = 836 mS cm-1 at x = 0.08 from Darling, so 700 at 2 M sits plausibly below the "
   "maximum but is not verified equal to any tabulated entry",
   "-- (no source reaching state A or B supports this value; Foxboro Conductivity Ordering Guide "
   "1999 is a vendor table and is quoted only as a bound)", "",
   S_KAPPA_DISPLAY + " Declared bound 620-720 mS cm-1 (+/- 8 pct); the tabled 700 sits at the top "
   "of it."),
 "1 M KHCO3 aq": (
   "derived by the CRC p. 5-71 route (see the 1 M NaOH aq row). CRC 'Concentrative Properties', "
   "KHCO3 block: 1.000 M = 9.434 mass pct; CRC p. 5-71 KHCO3 row (20 C) -> 68.6-68.8 at 20 C; "
   "alpha = 1.8-2.2 pct/K -> 75-76 at 25 C. The carbonates have no 25 C overlap table, so the "
   "alpha used is the asti/Ricca declared 2 pct/K +/- 0.2 and is declared as such rather than "
   "measured",
   "CRC Handbook of Chemistry and Physics, Section 5",
   "'Electrical Conductivity of Aqueous Solutions', p. 5-71 (KHCO3 row, 20 C) with 'Concentrative "
   "Properties of Aqueous Solutions', KHCO3 block (1.000 M = 9.434 mass pct)",
   S_KAPPA_DISPLAY),
 "1 M Na2CO3 aq": (
   "derived by the CRC p. 5-71 route (see the 1 M NaOH aq row). CRC p. 5-71 Na2CO3 row (20 C) read "
   "at the mass per cent that CRC 'Concentrative Properties' assigns to 1.000 M -> 72.4-72.9 at "
   "20 C; alpha = 1.8-2.2 pct/K (asti/Ricca declared 2 pct/K +/- 0.2, as for KHCO3) -> 79-81 at "
   "25 C. The registry's inherited 70 was 12 pct low",
   "CRC Handbook of Chemistry and Physics, Section 5",
   "'Electrical Conductivity of Aqueous Solutions', p. 5-71 (Na2CO3 row, 20 C) with 'Concentrative "
   "Properties of Aqueous Solutions', Na2CO3 block",
   S_KAPPA_DISPLAY),
 "56 wt% Et4NOTs aq": (
   "concentrated hydrotropic salt solution per the adiponitrile exemplar. Check needed: confirm "
   "whether Baizer reports kappa itself or only the electrolyte composition. If only the "
   "composition, this is the same failure mode as the LiBr/THF row",
   "Baizer, J. Electrochem. Soc. 1964, 111, 215", "", S_KAPPA_DISPLAY),
 "0.3 wt% H2SO4/MeOH (BASF)": (
   "the patent supports the composition (US 5,507,922 Ex. 1: 0.3 wt pct = ~0.025 M H2SO4 in MeOH), "
   "not kappa. The value was estimated from a lambda0(H+/MeOH) = 146 with an unquantified "
   "ion-pairing discount, and that lambda0 could not be page-anchored. the low kappa is "
   "nevertheless the documented reason BASF runs 0.5-1 mm capillary gaps",
   "US 5,507,922 (BASF, 1993)", "Example 1 -- supports the composition only", S_KAPPA_DISPLAY),
 "1 M Et4NF.4HF/MeCN": (
   "amine-HF fluorination media are highly conducting, but the inherited citation -- 'Fuchigami "
   "electrochemical fluorination reports' -- names no paper and is not a citation",
   KAPPA_NOSRC, "", S_KAPPA_DISPLAY),
 "0.5 M NaBr aq/MeCN 1:1": (
   "aqueous NaBr halved for 1:1 MeCN dilution. Mixed-solvent transfer is not defensible: "
   "preferential solvation invalidates any lambda0 or kappa transfer, and no isotherm exists for "
   "this composition", KAPPA_NOSRC, "", S_KAPPA_DISPLAY),
 "Et3N 7.5 mM (no salt)/MeOH": (
   "7.5 mM Et3N-carboxylate only, with no added supporting salt; the speciation is unknown",
   KAPPA_NOSRC, "", S_KAPPA_DISPLAY),
 "0.48 M Bu4N carboxylate (in situ)/MeCN": (
   "the conducting species is generated in situ and its speciation is not known, so no method can "
   "apply. Permanently an assumption", KAPPA_NOSRC, "", S_KAPPA_DISPLAY),
 "Me4NOH 15 mol% + Me4NBF4 5 mol%/acetone": (
   "an in-situ base/salt mixture of unknown speciation. Permanently an assumption",
   KAPPA_NOSRC, "", S_KAPPA_DISPLAY),
 "0.1 M Bu4NBF4/MeCN": (
   "measured, retrieved 2026-08-22: Shinkle et al. Table 1 gives 9.93 mS cm-1 for 0.1 M TBABF4 in "
   "ACN at room temperature. This row was previously derived at 9.9 by evaluating Dorn's "
   "Casteel-Amis fit (Table 3, p. 1499; kappa_max 33.40, m_max 1.48127, a 0.78646, b -0.02156) at "
   "m = 0.133 mol kg-1, which returned 9.87. The agreement is 0.3 pct, and that is the load-bearing "
   "fact on this row: it is the only point where a Casteel-Amis evaluation of Dorn's fit can be "
   "checked against a direct measurement of the same composition, and it is what licenses the four "
   "remaining Bu4NBF4/MeCN rows (0.043, 0.077, 0.25, 0.3 M) that have no measurement of their own. "
   "The molarity-to-molality conversion used there is therefore also validated at this point. "
   "caveat: Shinkle states 'room temperature', not 25.0 C; at 2-3 pct per K a +/-2 K ambiguity is "
   "+/-5 pct, which is larger than the 0.3 pct agreement and means the agreement should not be "
   "read as better than about +/-5 pct.",
   "Shinkle, Pomaville, Sleightholme, Thompson & Monroe, J. Power Sources 2014, 248, 1299-1305, "
   "DOI 10.1016/j.jpowsour.2013.10.034; cross-check against Dorn, Kareth, Weidner & Petermann, "
   "J. Chem. Eng. Data 2024, 69, 1493-1502",
   "Shinkle Table 1 (0.1 M supporting-electrolyte/solvent conductivities at room temperature, "
   "mS cm-1: TBABF4 = 9.93 ACN, 4.76 DMF, 0.30 THF, 0.06 dmc); Dorn Table 3, p. 1499",
   S_KAPPA_DISPLAY + " Display-only: it enters no figure and no sentence. Its value is that it "
   "validates the Casteel-Amis route used by four other rows."),
 "0.1 M Bu4NBF4/DMF": (
   "measured, retrieved 2026-08-22. This is the one number a reader meets in the manuscript body "
   "-- the TRL-E 6 passage quotes it and builds a worked example on it -- and until now it was an "
   "unsourced 3.5 mS cm-1 carried as `unused-legacy (no registry row)`, i.e. A number printed in "
   "the paper with no provenance entry anywhere. Shinkle et al. Table 1 measures exactly this "
   "composition, 0.1 M TBABF4 in DMF, at 4.76 mS cm-1. The carried 3.5 was 26 pct low. "
   "two independent checks on the same table, both of which this registry can make against values "
   "it already held: (i) Shinkle's 0.1 M TBABF4 in ACN is 9.93 against the 9.9 this registry had "
   "derived from Dorn's Casteel-Amis fit -- agreement to 0.3 pct, which is what validates that "
   "route for the four remaining Bu4NBF4/MeCN rows that have no direct measurement; and "
   "(ii) Shinkle's 0.1 M TBAPF6 in THF is 0.57 against the 0.51 this registry carries as measured "
   "from Zhang et al., jacs Au 2023, 3(8), 2280-2290 -- two independent laboratories 10 pct apart. "
   "superseded: the derivation recorded on this row before the measurement arrived gave 4.21 by "
   "Walden transfer of lambda0(BF4-) from MeCN plus Gopal & Jha's measured lambda0(Bu4N+, DMF), "
   "with a Kohlrausch ceiling of 7.28. It is retained here only because it is the check on that "
   "method: it landed 12 pct below the measurement and on the correct side of the carried value, "
   "so the method is usable but is not a substitute for measuring. "
   "caveat on the locator: Shinkle states 'room temperature', not 25.0 C. Every other "
   "conductivity in this registry is at 25 C. For a 2-3 pct per K temperature coefficient a "
   "+/-2 K ambiguity is +/-5 pct, which is inside the band the manuscript claim tolerates.",
   "Shinkle, Pomaville, Sleightholme, Thompson & Monroe, J. Power Sources 2014, 248, 1299-1305, DOI 10.1016/j.jpowsour.2013.10.034",
   "Table 1 (conductivity of each 0.1 M supporting-electrolyte/solvent combination at room temperature, mS cm-1: TBABF4 = 9.93 ACN, 4.76 DMF, 0.30 THF, 0.06 dmc)",
   "carries the worked example of the main text, which is an ILLUSTRATION of a tight batch cell "
   "rather than one of the modelled thermal archetypes: 100 mA cm-2 across a declared 5 mm gap. "
   "At the measured 4.76 mS cm-1 the model gives E_cell = %.2f V, of which %.2f V is ohmic, "
   "q = %.3f W cm-2, and a passive steady state of %.1f C. The claim the passage makes -- that "
   "the model reproduces the 10-20 V cells common in academic non-aqueous reports -- holds for "
   "kappa in [2.85, 6.64] mS cm-1, and the measured 4.76 sits inside it."
   % (_TM.E_cell(100., 0.476, 5.0e-3), 100. * 10. * 5.0e-3 / 0.476,
      _TM.q_Wcm2(100., 0.476, 5.0e-3),
      _TM.T_ss(100., 0.476, 5.0e-3, _TM.U_passive(_TH_RX[0][2], _TH_RX[0][3])))),
 "0.077 M Et4NBF4/MeCN": (
   "derived 2026-08-22 by same-family transfer at equal Lambda/Lambda0 from the derived "
   "0.077 M Bu4NBF4/MeCN row (8.1 mS cm-1): same solvent, same anion, same concentration, "
   "homologous tetraalkylammonium cation, so the degree of dissociation and the relaxation/"
   "electrophoretic attenuation are taken as common and only the limiting conductances differ. "
   "The two limiting conductances come from Kalugin Table 3, p. 28 -- Et4N+ 86.34, BF4- 109.20, "
   "Bu4N+ 61.90 S cm2 mol-1 -- a source already registered in this file, on the Br-(MeCN) row. "
   "Lambda0(Bu4NBF4/MeCN) = 61.90 + 109.20 = 171.10 reproduces to 0.00 pct the 171.1 this "
   "registry carries independently as measured, which is the self-consistency check on the "
   "route; Lambda0(Et4NBF4/MeCN) = 86.34 + 109.20 = 195.54, giving "
   "kappa = 8.1 x 195.54/171.10 = 9.26 mS cm-1. "
   "independent corroboration: Krumgalz's Walden products (Table 2 p. 577, acetonitrile row: "
   "Et4N+ 0.292, Bu4N+ 0.212) over his own acetonitrile viscosity (Table 3 p. 578, 0.00344 P) "
   "give 84.9 and 61.6, agreeing with Kalugin to -1.7 and -0.5 pct and yielding 9.20 mS cm-1 by "
   "the same construction -- a 0.6 pct spread between two independent tabulations. Gong Table 2 "
   "p. 3518 gives Et4N+ 85.1, between the two. "
   "Note: some sources call "
   "lambda0(Bu4N+, MeCN) the single missing number blocking this transfer. It was never "
   "missing -- Kalugin p. 28 carried it all along, cited on another row of this same file. "
   "why not dorn'S own fit: Dorn Table 3 p. 1499 does carry ACN/(C2H5)4NBF4 (m_max 4.00409, "
   "kappa_max 60.97, a 0.84952, b -0.02650) and it was retrieved -- but evaluated at this "
   "concentration it returns 4.03 mS cm-1, i.e. lambda/Lambda0 = 0.269 against 0.615 for "
   "Bu4NBF4 at the same molality in the same solvent. Two homologous R4N+BF4- salts cannot "
   "differ that way; the fit is anchored at m_max = 4.0 mol/kg and does not reach 0.077 M. "
   "That fit is therefore not used, and this row does not claim it. "
   "Supersedes an 8.1 lower bound.",
   KALUGIN + "; Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587; Dorn, Kareth, "
   "Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502; Gong, Fang, Gu, Li & Yan, "
   "Energy Environ. Sci. 2015, 8, 3515-3530",
   "Kalugin Table 3, p. 28 (Et4N+ 86.34, BF4- 109.20, Bu4N+ 61.90 S cm2 mol-1); Krumgalz "
   "Table 2, p. 577 (Walden products, acetonitrile row: Et4N+ 0.292, Bu4N+ 0.212) and "
   "Table 3, p. 578 (acetonitrile 0.00344 P); Dorn Table 3, p. 1499; Gong Table 2, p. 3518",
   S_KAPPA_DISPLAY),
 "0.01 M Bu4NPF6/HFIP": (
   "deliberately dilute optimum per the exemplar. HFIP (eps = 15.7 -- Colomer, Chamberlain, "
   "Haughey & Donohoe, Nat. Rev. Chem. 2017, 1, 0088, Table 1 p. 2; the 16.7 this row used to "
   "quote was recalled and wrong) has no lambda0 table in Krumgalz or anywhere retrieved, so "
   "even the dilute-limit route is unavailable",
   KAPPA_NOSRC, "", S_KAPPA_DISPLAY),
 # -- the four further Casteel-Amis rows (display-only, but DERIVED) ------------------------
 **{name: (
   "derived by Casteel-Amis (Casteel & Amis, J. Chem. Eng. Data 1972, 17, 55) from the measured fit "
   "of Dorn et al., Table 3, p. 1499 for ACN / (C4H9)4NBF4 (kappa_max = 33.40 mS cm-1, m_max = "
   "1.48127 mol kg-1, a = 0.78646, b = -0.02156). At m = %s mol kg-1 the fit returns %s mS cm-1. "
   % (mm, kk) + CA_CONV + " %s" % extra,
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502; method: Casteel & "
   "Amis, J. Chem. Eng. Data 1972, 17, 55",
   "Dorn Table 3, p. 1499 (ACN / (C4H9)4NBF4)",
   S_KAPPA_DISPLAY + " Derived display-only: the row now has a method and a locator, but it still "
   "enters no figure and no sentence. Declared band %s mS cm-1." % (band,))
   for name, mm, kk, band, moved, extra in [
     ("0.043 M Bu4NBF4/MeCN", "0.056", "5.66", "5.0-6.0", "5.2 -> 5.66",
      "the only row still using the fit. Dorn's supporting information (Table SI 85, p. 171) "
      "measures this isotherm at 21 concentrations, and every other Bu4NBF4/MeCN row in this "
      "registry is now read between two of those measurements. This one cannot be: m = 0.056 "
      "falls between measured points at m = 0 (0.17 mS cm-1) and m = 0.0905 (7.66), and kappa(m) "
      "is strongly curved there, so linear interpolation gives 4.80 against the fit's 5.66 -- a "
      "15 pct disagreement that is the interpolation's error, not the fit's. "
      "the fit is now implemented and validated rather than typed: data/casteel_amis.py "
      "reproduces Dorn's own kappa_calc column on this isotherm to 0.088 pct (gate G-CA). The "
      "5.18 sometimes quoted for this pair comes from applying the wrong sign to the b term; "
      "the opposite sign misses Dorn's kappa_calc by up to 32 pct on this same isotherm."),
   ]},
 "0.077 M Bu4NBF4/MeCN": (
   "measured. read between two measured points of Dorn's isotherm in the supporting "
   "information, which carries the raw data the article body's Table 3 only summarises: "
   "Table SI 85, p. 171, at m = 0.101 mol kg-1, between the measured points (0.0905, 7.66) and (0.1896, 13.36) "
   "mol kg-1 / mS cm-1, giving 8.26 mS cm-1. Supersedes a typed 8.07 produced from the Casteel-Amis fit with the wrong sign on b.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information (je3c00691_si_001.pdf)",
   "Table SI 85, p. 171 (298.15 K, 101 kPa; 21 measured points with combined "
   "uncertainties)",
   S_KAPPA_DISPLAY),
 "0.3 M Bu4NBF4/MeCN": (
   "measured. read between two measured points of Dorn's isotherm in the supporting "
   "information, which carries the raw data the article body's Table 3 only summarises: "
   "Table SI 85, p. 171, at m = 0.423 mol kg-1, between the measured points (0.4094, 22.13) and (0.5312, 25.48) "
   "mol kg-1 / mS cm-1, giving 22.50 mS cm-1. Supersedes a typed 21.34 produced the same way.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information (je3c00691_si_001.pdf)",
   "Table SI 85, p. 171 (298.15 K, 101 kPa; 21 measured points with combined "
   "uncertainties)",
   S_KAPPA_DISPLAY),
 "2 M NaCl aq": (
   "measured. read between two measured points of Dorn's isotherm in the supporting "
   "information, which carries the raw data the article body's Table 3 only summarises: "
   "Table SI 13, p. 54, at m = 2.0816 mol kg-1, between the measured points (2.0714, 148.36) and (2.3325, 161.37) "
   "mol kg-1 / mS cm-1, giving 148.9 mS cm-1. The target molality is 0.5 pct above a measured point, so this is effectively a direct reading. The CRC p. 5-71 derivation it replaces gave 148.0, i.e. -0.6 pct -- an independent confirmation of that route, which is retained in the registry.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information (je3c00691_si_001.pdf)",
   "Table SI 13, p. 54 (298.15 K, 101 kPa; 21 measured points with combined "
   "uncertainties)",
   S_KAPPA_DISPLAY),
 "1 M KHCO3 aq": (
   "measured. read between two measured points of Dorn's isotherm in the supporting "
   "information, which carries the raw data the article body's Table 3 only summarises: "
   "Table SI 31, p. 94, at m = 1.0405 mol kg-1, between the measured points (0.9676, 71.84) and (1.1207, 80.55) "
   "mol kg-1 / mS cm-1, giving 76.0 mS cm-1. The CRC p. 5-71 derivation it replaces gave 75.5, i.e. -0.6 pct.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information (je3c00691_si_001.pdf)",
   "Table SI 31, p. 94 (298.15 K, 101 kPa; 21 measured points with combined "
   "uncertainties)",
   S_KAPPA_DISPLAY),
 # -- rows that stay C but now carry a state-B Kohlrausch ceiling ---------------------------
 "0.1 M Et4NClO4/DMF": (
   "stays an assumption, now with a state-B ceiling. Kohlrausch additivity: Lambda0(Et4NClO4, DMF, "
   "298 K) = 35.39 + 52.67 = 88.06 S cm2 mol-1 [Gopal & Jha, Indian J. Chem. 1977, 15A, 80-83, "
   "Table 2, p. 81, DMF column, 25 C -- a single convention; do not blend it with the Bu4NBPh4 "
   "reference-electrolyte split of Vermani et al. 2019], so kappa <= c Lambda0 = 8.81 mS cm-1. The "
   "tabled 4.0 implies Lambda/Lambda0 = 0.454, which is not established. A cross-salt "
   "Lambda/Lambda0 monotonicity argument would raise this row to ~6 mS cm-1, but that "
   "argument is invalid: Lambda(c)/Lambda0 is monotone in c only for a given salt in a given "
   "solvent -- and the anomaly it rested on (7.2 pct, falling to 3.7 pct if the other retrieved "
   "lambda0 is substituted) is smaller than the 5.6 pct disagreement between the two retrieved "
   "values of lambda0(ClO4-, DMF). do not apply it",
   "Gopal & Jha, Indian J. Chem. 1977, 15A, 80-83 (supports the ceiling, not the value)",
   "Table 2, p. 81, DMF column, 25 C (Et4N+ 35.39, ClO4- 52.67 S cm2 mol-1)",
   S_KAPPA_DISPLAY + " Hard ceiling kappa <= 8.81 mS cm-1 (state B), which makes the row "
   "falsifiable while it stays an assumption."),
 **{name: (
   "stays an assumption, now with a state-B ceiling. Kohlrausch additivity from Gong et al., Energy "
   "Environ. Sci. 2015, 8, 3515-3530, Table 2, p. 3518 (Li+ 69.97, ClO4- 103.6, Et4N+ 85.1, PF6- "
   "102.8 S cm2 mol-1; Et4N+ corroborated at 86.34 by Kalugin et al. 2019, Table 3) gives "
   "Lambda0 = %s S cm2 mol-1 and hence kappa <= %s mS cm-1. The tabled value is not confirmed: "
   "converting a ceiling into a value requires Lambda/Lambda0, and the only route available was to "
   "transfer the ratio measured for a different salt (Bu4NBF4). That transfer is an assumption, so "
   "it does not upgrade the row and must not be used to overwrite the tabled value" % (l0, ceil),
   "Gong, Fang, Gu, Li & Yan, Energy Environ. Sci. 2015, 8, 3515-3530 (supports the ceiling, not "
   "the value)", "Table 2, p. 3518",
   S_KAPPA_DISPLAY + " Hard ceiling kappa <= %s mS cm-1 (state B).%s" % (ceil, note))
   for name, l0, ceil, note in [
     ("0.1 M LiClO4/MeCN",    "173.6", "17.4", ""),
     ("0.3 M LiClO4/MeCN",    "173.6", "52.1", ""),
     ("0.033 M Et4NPF6/MeCN", "187.9", "6.20",
      " A cross-salt ratio transfer (Lambda/Lambda0 = 0.749 measured for Bu4NBF4) would give 4.6 "
      "in place of 3.5. It is not applied: substituting an unnamed cross-salt heuristic for a "
      "registry value is exactly what state C exists to prevent."),
   ]},
 # -- rows that stay C and cannot even carry a ceiling --------------------------------------
 **{name: (
   "CEILING RECOVERED 2026-08-31. This row read 'no source supports this value, and none bounds "
   "it', on the ground that lambda0(Na+, MeCN) is absent from Gong et al. Table 2 (whose cation "
   "block runs Li+ 69.97 straight to Me4N+ 94.5) and from Kalugin et al. (R4N+ and anions only), "
   "so the Kohlrausch route could not close. It names Minc & Werblan as the source that would "
   "close it -- and that paper is IN THIS REPOSITORY and had simply not been opened for this "
   "purpose: Model Papers for Params/1-s2.0-0013468662870030-main.pdf, 'Electrical conductivity "
   "of electrolyte solutions in organic solvents - I. Alkali perchlorates in acetonitrile'. Its "
   "Table 2, p. 261 gives EQUIVALENT CONDUCTANCES AT INFINITE DILUTION in acetonitrile at 25 C: "
   "LiClO4 183.25 and NaClO4 192.40 S cm2 mol-1, cross-checked by its own Table 4, p. 263 "
   "(183.40 and 192.30, agreeing to 0.05 pct). Kohlrausch then closes in two steps from values "
   "already registered here: lambda0(ClO4-) = 183.25 - 69.97 = 113.28, hence lambda0(Na+) = "
   "192.40 - 113.28 = 79.12, hence Lambda0(NaBr, MeCN) = 79.12 + 102.00 = 181.12 using "
   "lambda0(Br-, MeCN) = 102.00 from Kalugin Table 3, p. 28. As a check, lambda0(ClO4-) = 113.28 "
   "sits alongside Krumgalz's lambda0(SCN-, MeCN) = 113.3 for a similarly sized anion",
   CEIL_NACL, "",
   S_KAPPA_DISPLAY + " CEILING, NOT AN ESTIMATE: kappa <= Lambda0 c is the infinite-dilution "
   "limit, and the true conductivity at working concentration is lower -- Minc & Werblan measure "
   "an association constant of K = 10.92 for NaClO4 in this solvent, and relaxation and "
   "electrophoretic effects reduce Lambda further. The ceilings are 38.5 mS cm-1 at 0.2 M NaClO4, "
   "14.5 at 0.08 M NaBr and 7.2 at 0.04 M NaBr, against carried values of 12.0, 4.0 and 1.5, so "
   "every one sits well beneath its bound. What is still absent is the concentration dependence, "
   "which is why these stay state C rather than becoming derived.")
   for name in ("0.2 M NaClO4/MeCN", "0.08 M NaBr/MeCN", "0.04 M NaBr/MeCN")},
 "0.21 M tbab/DMSO-THF": (
   "stays an assumption on two independent grounds. (i) Mixed solvent (DMSO/THF 5:1 v/v): "
   "preferential solvation invalidates any lambda0 or kappa transfer from either pure component, "
   "and no measured conductivity for Bu4NBr in DMSO or in DMSO/THF mixtures at any concentration "
   "was located. (ii) off-convention temperature: the exemplar runs at 85 C while Table S4 is "
   "headed 25 C. Do not propagate any 85 C estimate -- that would stack an assumption on an "
   "assumption",
   KAPPA_NOSRC, "",
   S_KAPPA_DISPLAY + " The 25 C / 85 C convention mismatch should be flagged in the table rather "
   "than silently carried."),
}
MIXED_SOLVENT = {  # preferential solvation invalidates any transfer; permanently state C
 "0.085 M Et4NPF6/MeCN-HCl aq","0.091 M mtes/HFIP-MeOH","0.1 M LiClO4/AcOH-HCOOH",
 "0.1 M TBAP/MeCN-H2O","0.21 M tbab/DMSO-THF","0.24 M Et3NHBF4/THF-HFIP",
 "0.25 M KOAc/tAmOH-H2O","5 wt% AcOH/MeOH-H2O","NaCl 7 mol% + pH 2 HCl/H2O-MeCN",
}
import pandas as _pd
# Inputs and output are anchored on __file__, not on the cwd. Before 2026-08-02 these were bare
# relative paths, so running this script from anywhere but data/ either died on the read or -- if
# copies of the two input CSVs happened to sit in the cwd -- wrote a complete, correct registry
# INTO THAT DIRECTORY and exited 0, while the real registry silently went stale with no warning.
# Same idiom as build_reactions50.py and build_merged_matrix.py.
_HERE = _os.path.dirname(_os.path.abspath(__file__))          # .../Section4_Model/data
_REPO = _os.path.dirname(_HERE)                               # .../Section4_Model
IN_REACTIONS = _os.path.join(_HERE, "reactions_50.csv")
IN_ELECTROLY = _os.path.join(_HERE, "electrolytes.csv")
OUT_REGISTRY = _os.path.join(_HERE, "parameters_provenance.csv")
_used = _pd.read_csv(IN_REACTIONS)[["electrolyte"]].drop_duplicates()
_ecsv = _pd.read_csv(IN_ELECTROLY).set_index("electrolyte")
_kap  = _ecsv["kappa_mScm"]

# B17. The provenance CLASS of a conductivity row is no longer hard-coded. The loop below used to
# emit "assumption" for every electrolyte, which silently overrode the nine rows the 2026-08-02
# sourcing pass promoted to derived (docs/KAPPA_SOURCING_DOSSIER.md Sections 2.1 and 2.2). The class
# is now READ FROM data/electrolytes.csv, which is the file that carries the state alongside the
# value so the two cannot separate, and it is cross-checked against the explicit DERIVED_KAPPA set
# below so that a silent edit to either one fails loudly instead of shipping.
DERIVED_KAPPA = {
 # What remains state B after the Dorn Supporting Information arrived (2026-08-22). Everything
 # else that used to be here is now state A, read off a measured isotherm -- see ELECTROLYTE_STATE
 # in build_reactions50.py for which table and page each one comes from.
 "0.043 M Bu4NBF4/MeCN",   # m = 0.056 sits in a bracket (0 to 0.0905) too wide to interpolate
                           # across, so this one still uses the Casteel-Amis fit -- now with a
                           # real implementation (data/casteel_amis.py, gate G-CA) instead of a
                           # typed literal, and with the sign convention settled against Dorn's
                           # own kappa_calc column.
 "0.077 M Et4NBF4/MeCN",   # same-family transfer at equal Lambda/Lambda0; Dorn measured
                           # Et4NBF4/MeCN but not at a concentration this low, and his fit does
                           # not reach it (see that row's note).
 "0.2 M NaI/DMF",          # Lambda0 from Gopal & Jha p. 81, attenuation from Dorn's MEASURED
                           # NaI/methanol isotherm at the same molarity. Replaces an unsourced 8.0.
 "1 M Na2CO3 aq",          # the CRC p. 5-71 route; Dorn HAS Na2CO3 in water and it is the obvious
                           # next upgrade, but the isotherm was not extracted in this pass.
}
_csv_derived = set(_ecsv.index[(_ecsv.state == "derived") & (_ecsv.status == "registered")])
assert _csv_derived == DERIVED_KAPPA, (
    "electrolytes.csv derived set != DERIVED_KAPPA; csv-only=%s, code-only=%s"
    % (sorted(_csv_derived - DERIVED_KAPPA), sorted(DERIVED_KAPPA - _csv_derived)))

# Iterate every REGISTERED electrolyte, not merely those a reaction names. Until 2026-08-22 this
# loop read `_used.electrolyte`, i.e. the electrolytes of the 50 reactions -- which silently
# excluded `1 M NaOH aq`, whose only consumer is the cell-voltage stack (see _CELLVOLTAGE_ELYTES
# in build_reactions50.py). That row is one of the FOUR conductivities carrying a §S6 verdict,
# it is printed in SI Table S4 as `derived, 10-42x margin`, and it had NO registry row at all: the
# provenance shown for it in the SI came from a hand-typed literal in make_si.js rather than from
# this file. A conclusion-carrying number was outside the registry that is supposed to cover every
# number. The assert below makes the omission impossible to reintroduce.
_registered = set(_ecsv.index[_ecsv.status == "registered"])
assert set(_used.electrolyte) <= _registered, (
    "a reaction names an electrolyte that is not registered: %s"
    % sorted(set(_used.electrolyte) - _registered))
for e_ in sorted(_registered):
    k_ = float(_kap[e_])
    cls_ = str(_ecsv.loc[e_, "state"])
    assert cls_ in ("measured", "derived", "assumption"), (e_, cls_)
    assert (cls_ == "derived") == (e_ in DERIVED_KAPPA), (e_, cls_)
    if e_ in ECOND_PROV:
        meth, cit, loc, sens = ECOND_PROV[e_]
    elif e_ in MIXED_SOLVENT:
        meth = ("mixed-solvent composition: no limiting-conductivity table exists for it, and "
                "preferential solvation makes transfer from either pure component invalid. "
                "Permanently an assumption")
        cit, loc, sens = KAPPA_NOSRC, "", S_KAPPA_DISPLAY
    else:
        meth, cit, loc, sens = QAM_METH, KAPPA_NOSRC, "", S_KAPPA_DISPLAY
    # The pull-needed string is a statement about rows that still need a source. It is dropped from
    # the nine rows that now have one, where it would contradict the method note it follows.
    add("6. Electrolyte conductivities", e_, f"{k_}", "mS cm-1", cls_,
        meth + "." + ("" if cls_ == "derived" else KAPPA_PULL), cit, loc, sens)

# -- 7. Reactor archetypes: geometry + correlations --------------------------

## ---------------------------------------------------------------------------------------------
## SOLVENT BOILING POINTS -- ADDED 2026-08-24.
## These four temperatures set the boil-off ceiling in Fig. 5 (they enter as T_boil - T_amb) and
## were HARDCODED in figs/thermal_model.py with no registry row, no citation and no sensitivity,
## while every other constant in that file had one. They are the last unprovenanced numbers found
## by the code audit. Retrieved from the CRC table that solvents.csv already cites for mu and rho.
## The code carries rounded values; both the printed value and the rounding are recorded here, and
## the rounding's effect on the ceiling is bounded per solvent.
CRCB = ("CRC Handbook of Chemistry and Physics, 97th ed. (W. M. Haynes, ed.), CRC Press, 2016")
LOCB = ("Sect. 15, 'Laboratory Solvents and Other Liquid Reagents', pp. 15-13 ff., normal boiling "
        "point column (from the PDF in Model Papers for Params/, layout-"
        "preserving extraction; M cross-checked: 41.052 / 73.094 / 72.106)")
for nm_, used_, printed_, shift_ in [
    ("THF",      "66.0",   "66.0",   "+0.000"),
    ("MeCN",     "81.6",   "81.6",   "-0.702"),
    ("DMF",      "152.8",  "152.8",  "-0.156"),
    ("H2O (used for 1 M NaOH aq)", "99.974", "99.974", "-0.035")]:
    add("9. Thermal model", "T_boil: %s" % nm_, used_, "deg C", "measured",
        "normal boiling point as printed by the source: %s deg C, and figs/thermal_model.py now "
        "uses exactly that. It previously used a rounding (66/82/153/100); the printed values were "
        "adopted on 2026-08-24 at the author's direction" % printed_,
        CRCB, LOCB,
        "T_boil enters only as (T_boil - T_amb), so the rounding shifts that solvent's boil-off "
        "ceiling by %s%% relative to a 3-significant-figure rounding of it. For 1 M NaOH the pure-water "
        "boiling point is used; the real solution boils slightly higher (boiling-point elevation, "
        "~0.5 K at 1 M), so 100 deg C is the conservative choice for a boil-off ceiling."
        % shift_)

add("7. Reactors", "delta (unstirred batch)", "228", "um", "derived",
    "DERIVED 2026-09-04 from the source's OWN diffusion-layer equation, replacing a declared "
    "300 um. Two defects were removed in the process. (i) The value had been chosen at the "
    "conservative (high-delta) END of a band nothing computed, while the stirred film is a "
    "measured CENTRAL value, so the contrast between the two batch archetypes was an artefact of "
    "comparing an edge against a centre. (ii) The correlation coefficient carried here was "
    "a = 0.66 for the Nusselt form, which is neither what the source prints nor derivable from "
    "it: Wilke, Eisenberg & Tobias print Nu' = 0.673 (Sc Gr)^(1/4) (Eq. XV) and, for this exact "
    "quantity, delta' = 1.48 x (Sc Gr)^(-1/4) (Eq. XVII, p. 518). Both were confirmed against the "
    "page raster. The printed DELTA equation is used, so the source is not rearranged at all. "
    "A third defect was corrected at the same time: the row had cited Katona et al. 2021 as an "
    "'independent measured cross-check' for 230, 250, 150 and ~800 um, but that paper measures "
    "aqueous NaCl by RDE/Levich with the electrode perpendicular to gravity and states in its own "
    "words that those values come 'from Liu et al. and Charles-Granville et al., ... and 10 mM "
    "potassium ferrocyanide from Amatore et al.' -- a secondary citation, which is not state A. "
    "The ferrocyanide measurement has now been retrieved and is cited directly, below.",
    "Wilke, Eisenberg & Tobias, 'Correlation of limiting currents under free convection "
    "conditions', J. Electrochem. Soc. 1953, 100, 513-523 (plane vertical cathodes in quiescent "
    "solution, cathode heights 0.25-3.0 in., i_lim 0.4-108 mA cm-2 -- the archetype and the "
    "current range match this work exactly). Derivation, reproducible from this table: the paper's "
    "Eq. XVII, delta' = 1.48 x (Sc Gr)^(-1/4) with Sc Gr = g x^3 (drho/rho)/(nu D), evaluated at "
    "x = %.0f mm and drho/rho = %.2e -- the geometric centres of the declared ranges on the "
    "operating-point row that follows -- over each of the fifty rows' own nu and D, gives a median "
    "of %.0f um. " % (_FC["h_centre_m"] * 1e3, _FC["drho_rho_centre"], _FC["delta_centre_um"]) + 
    "INDEPENDENT MEASURED CORROBORATION: Amatore, Szunerits, Thouin & Warkocz, J. Electroanal. "
    "Chem. 2001, 500, 62-70, DOI 10.1016/S0022-0728(00)00378-8, determine delta = (230 +/- 10) um "
    "for the one-electron oxidation of 10 mM Fe(CN)6(4-) in aqueous 1 M KCl at a millimetric "
    "electrode in quiescent solution, from the steady-state limiting current at long times. The "
    "derived value sits inside that interval.",
    "Eq. XVII p. 518 (delta form) and Eq. XV (Nusselt form, constant 0.673); Amatore et al. "
    "p. 68: 'we thus determined delta = (230 +/- 10) um'",
    "The two inputs that are declared rather than sourced are the electrode height and the "
    "density driving force (their own row follows), and delta goes as the fourth root of each: "
    "across x = 5-80 mm it runs %.0f-%.0f um and across drho/rho = 1e-2 to 1e-3 it runs %.0f-%.0f "
    "um, an envelope of %.0f-%.0f um over both declarations together, widening to %.0f-%.0f um once "
    "the per-reaction spread in nu and D is included. The unstirred median is 8.01 mA cm-2 at "
    "%.0f um and 6.11 at 300 um, the top of the typed band, while 12 of 50 clear 25 mA cm-2 and 9 "
    "of 50 clear 50 mA cm-2 at either film, so no headline integer depends on where in the "
    "envelope the value sits. The contrast with the stirred archetype is 1.14x at the central "
    "value and 1.49x at 300 um; it is the softest comparison in the model and is bounded rather "
    "than asserted: the unstirred film exceeds the stirred one only for electrode heights above "
    "about 12 mm at the central driving force, so the ordering of the two batch archetypes is a "
    "property of the declared geometry and not a measured separation."
    % (_FCS["h_5mm"], _FCS["h_80mm"], _FCS["drho_1e-2"], _FCS["drho_1e-3"], _FC_ENV_LO, _FC_ENV_HI,
       _FC["delta_band_lo_um"], _FC["delta_band_hi_um"], _FC["delta_centre_um"]))
add("7. Reactors", "Free-convection operating point (unstirred batch)",
    "x %.0f mm; drho/rho %.2e" % (_FC["h_centre_m"] * 1e3, _FC["drho_rho_centre"]), "-", "assumption",
    "the declared operating point of the free-convection correlation: the geometric centres of "
    "x = 5-80 mm and drho/rho = 1e-3 to 1e-2. The analogue of the RDE's 1600 rpm and the RCE's "
    "3000 rpm rows, given its own row on 2026-09-05 so that the derived film above is derived from "
    "inputs a reader can see are declared",
    "Declared operating point. The height is an operator choice like a rotation speed and is "
    "declared as one. The density driving force is not: Wilke, Eisenberg & Tobias define it "
    "through a specific densification coefficient, rho_0 - rho_i = alpha rho_i (C_0 - C_i), so at "
    "the limiting current it is fixed by the bulk concentration of whichever species the surface "
    "depletes, and their own experiments span 0.01-0.74 M CuSO4 on cathodes 6-76 mm high. The "
    "fifty rows deplete 3.5 mM to 13.7 M and the densification coefficients of these organic "
    "solutions are not available, so one value is declared for all fifty and what it costs is "
    "stated here rather than hidden inside the derived film.",
    "declared; Wilke, Eisenberg & Tobias p. 513 (abstract: '0.01 to 0.7 molal CuSO4 ... cathode "
    "heights varied from 0.25 to 3.0 in.') and p. 515 for the source's own range",
    "delta goes as (drho/rho)^(-1/4). The one case that can be page-anchored is the most "
    "concentrated aqueous binary electrolyte modelled, 2 M NaCl: %s gives rho = 1.0707 g cm-3 at "
    "10.0 mass pct (1.832 M) and 1.0781 at 11.0 mass pct (2.029 M), so 2.000 M interpolates to "
    "%.4f against %.4f on the table's 0.1 mass pct row, drho/rho = %.3f, %.0fx the declared "
    "centre, and a film that depletes the whole salt would be %.0f um at the central height rather "
    "than %.0f. A millimolar organic in an organic solvent sits below the declared decade and its "
    "film is correspondingly thicker. The lumped film is therefore an upper estimate for the "
    "concentrated aqueous rows and a lower one for the dilute organic rows; a per-row driving "
    "force would thin the film for exactly the rows that carry the unstirred counts (10 of the 12 "
    "clearing 25 mA cm-2 are concentrated rows, S1.1). The direction is established by the fourth "
    "root; the magnitude per row is not computed here because the coefficients are unavailable, "
    "and the ordering of the archetypes, which every sweep reported here preserves, does not rest "
    "on it." % (_FCI["source"], _FCI["rho_2M_gcm3"], _FCI["rho_ref_gcm3"], _FCI["drho_rho"],
                _FCI["ratio_to_declared_centre"], _FCI["delta_um_at_central_height"],
                _FC["delta_centre_um"]))
add("7. Reactors", "delta (stirred batch)", "200", "um", "measured",
    "ADOPTED 200 um on 2026-09-01 (author decision), replacing a declared 100 um whose "
    "inherited citation had been withdrawn -- no passage in Pletcher & Walsh, Industrial "
    "Electrochemistry, 2nd ed., giving delta ~ 100 um for a magnetically stirred cell could be "
    "located, and no universal correlation can replace it, because mass transfer in a stirred "
    "beaker depends on stir-bar length, vessel diameter, electrode position and baffling, none "
    "of which is a registry parameter. The adopted value is a direct MEASUREMENT of the "
    "mass-transport boundary layer of a planar electrode in a convecting cell, obtained the "
    "standard way: diffusion-limited ferricyanide current, back-calculated through "
    "i_lim = nFDc/delta, then converted for the diffusivity of the dissolved gas.",
    "Williams, Corbin, Zeng, Lazouski, Yang & Manthiram, Sustainable Energy Fuels 2019, 3, "
    "1225-1232, DOI 10.1039/C9SE00024K",
    "p. 1227: 'For the transport of dissolved O2 gas, the calculated boundary layer thickness "
    "was 200 +/- 7 um' (D_O2 = 2.10e-5 cm2 s-1, bubbling at 10 sccm)",
    "IT IS A PROXY, NOT THIS SYSTEM, and that is stated rather than glossed: the measurement is "
    "dissolved O2 in a gas-bubbled aqueous cell, not an organic electrolyte under magnetic "
    "stirring. It is the same GEOMETRY CLASS -- a planar electrode in a convecting cell -- and "
    "O2 diffuses about twice as fast as the bulky organics modelled here, so the real layer for "
    "these systems should be THICKER and the adopted value stays conservative in that direction. "
    "The unstirred archetype is now DERIVED at the centre of the same free-convection "
    "correlation, 233 um, so the two batch films are compared centre against centre and the "
    "contrast is 1.16x rather than the 1.49x an edge-against-centre pairing gave. The two "
    "archetypes remain close, and that is a property of the systems rather than of the "
    "choice: the unstirred film exceeds this one only for electrode heights above about "
    "11 mm at the central driving force, so the separation is bounded by declared geometry "
    "and is not a measured result. The measurement's own uncertainty, +/-7 um, "
    "carries through to " + _sbrow("stirred") + "; the architecture ordering and the "
    "unstirred-to-RCE span of 15.2x hold across the whole interval, so no conclusion depends on "
    "where within it the value sits.")
add("7. Reactors", "delta (recirculating flow cell)", "106.9", "um", "measured",
    "ADOPTED 2026-09-07 (author decision) in place of the declared Leveque operating point "
    "'gap 1 mm, L 5 cm, u 5 cm/s', which had no source for any of its three numbers and computed "
    "to a per-row film of 38-95 um. Watkins et al. measured the diffusion boundary layer of four "
    "cells by the ferricyanide limiting-current method of Clark et al. (10 mM, D = 0.720e-5 cm2/s) "
    "and tabulate them with the COMSOL value beside each. The parallel-inlet recirculating H-cell "
    "at 280 uL/s is the archetype: 106.9 um experimental against 242 um simulated. Only the Ager "
    "H-cell entry of that table carries replicate error (177.9 +/- 21.6 um, six experiments), so "
    "the sensitivity band applied here is that same-method, same-study scatter, 12.1 %, declared "
    "as a transfer. The old row text is preserved in docs/ARCHETYPE_REANCHOR_20260907.md.",
    "Watkins, Schiffer, Lai, Musgrave III, Atwater, Goddard III, Agapie, Peters & Gregoire, "
    "'Hydrodynamics Change Tafel Slopes in Electrochemical CO2 Reduction on Copper', ACS Energy "
    "Lett. 2023, 8, 2185-2192, DOI 10.1021/acsenergylett.3c00442, Supporting Information",
    "SI p. 6, Table S1, 'Parallel H-cell (280 uL/s)': experimental boundary layer 106.9 um, "
    "COMSOL 242 um; method per Figure S2 on the same page",
    "The film is an aqueous ferricyanide measurement applied unscaled to every row, exactly as the "
    "stirred film is, and it is the cell's value at one printed flow rate (280 uL/s). The table "
    "prints replicate error for one cell only, the Ager H-cell, at 12.1 % of its mean over six "
    "experiments; that scatter is the band applied to this value, 94-120 um, and it is a declared "
    "transfer rather than a measured uncertainty of this cell. Across that band the recirculating "
    "column gives " + _sbrow("flow") + "; the architecture ordering is unchanged throughout. The "
    "authors' own simulation of the same cell gives 242 um, 2.3 times the measured value, and the "
    "measured value is carried because it is the quantity the standard requires; a reader who "
    "prefers the simulated film should halve this column's currents.")
add("7. Reactors", "delta (ANEC flow cell)", "36.2", "um", "measured",
    "ADOPTED 2026-09-07 (author decision), the second measured film from the same table. The ANEC "
    "cell is a recirculating cell whose inlet is angled 20 degrees toward the working electrode, "
    "so the jet impinges obliquely on its face; at the typical 140 uL/s its film is 36.2 um "
    "(COMSOL 57 um). The angled-inlet H-cell in the same table reads 33.4 um at 280 uL/s (COMSOL "
    "128 um), and the two agree to 8 %.",
    "Watkins, Schiffer, Lai, Musgrave III, Atwater, Goddard III, Agapie, Peters & Gregoire, ACS "
    "Energy Lett. 2023, 8, 2185-2192, DOI 10.1021/acsenergylett.3c00442, Supporting Information",
    "SI p. 6, Table S1, 'ANEC (140 uL/s)': experimental boundary layer 36.2 um, COMSOL 57 um; "
    "footnote: '140 uL/s is the typical flow rate for ANEC experiments'",
    "An aqueous ferricyanide measurement applied unscaled to every row, at the one printed flow "
    "rate. The band is the same-method scatter of 12.1 %, 32-41 um, declared as a transfer; the "
    "angled-inlet H-cell of the same table, 33.4 um, lies inside it. Across that band the ANEC "
    "column gives " + _sbrow("anec") + "; the architecture ordering is unchanged throughout. The "
    "authors' simulation gives 57 um for this cell, 1.6 times the measured value.")
add("7. Reactors", "Microfluidic cell operating point (Mo 2020)", "gap 25 um; tau 4 min", "-", "measured",
    "the interelectrode gap and residence time of the Mo/Jensen microfluidic cell, both printed "
    "on one SI page: the optimisation experiments 'were conducted in a small-scale electrochemical "
    "flow cell with the thinnest FEP spacer (0.001\", 25 um)', and Table S1 on that page prints "
    "tau = 4 min for entries 9-12, entry 12 being the published optimum (MeCN, 3.3 V, 50 C, 64 %). "
    "Registered 2026-09-07 as the inputs the derived microfluidic film rests on, in place of the "
    "retired 250 um 'thin-gap' geometry (Watts 2011), which was a different cell from a different "
    "paper and had never been the cell the reaction set contains.",
    "Mo, Lu, Rughoobur, Patil, Gershenfeld, Akinwande, Buchwald & Jensen, Science 2020, 368, "
    "1352-1357, DOI 10.1126/science.aba3823, Supporting Information",
    "SI p. 13: '0.001\", 25 um' spacer; Table S1 (same page), column tau/min, entries 9-12 = 4; "
    "p. 3: FEP spacers 0.001-0.005 in, 50 x 50 x 3 mm glassy-carbon plates",
    "The gap is a spacer thickness the source states is not compressed in the cell (15.2 MPa "
    "compressive strength at 5 % strain, p. 3), and the residence time is tabulated. The same table "
    "prints tau = 12 min for entries 3-8; the derived film's own row states what that range does.")
add("7. Reactors", "delta (microfluidic cell)", "12.5", "um", "derived",
    "DERIVED 2026-09-07 from the two printed inputs above by the rule every flow cell in this model "
    "has always used, the Leveque entrance solution bounded by the fully-developed half-gap film. "
    "No channel width or length is needed: with u = Q/(w h) and Q tau = w h L, the Leveque group "
    "Re Sc d_h/L = 4 u h^2/(D L) reduces to 4 h^2/(D tau) exactly. At h = 25 um and tau = 4 min "
    "that group is 1.0e-11 m2/s divided by D, i.e. 0.003-0.06 over the fifty rows, so the entrance "
    "Sherwood number 1.85 (4 h^2/(D tau))^(1/3) lies far below the fully-developed value of 4 "
    "(delta = h/2) for every row and the floor binds: delta = 12.5 um, independent of D and nu.",
    "Leveque entrance solution (Pickett & Ong, Electrochim. Acta 1974, 19, 875-882) with the "
    "half-gap floor delta <= h/2 stated in Table S1; inputs from the row above",
    "derivation reproducible from this table: delta = D / max(1.85 (4 h^2/(D tau))^(1/3) D/(2h), "
    "D/(h/2)) = h/2 for all fifty rows",
    "The film is the half-gap for every row and at both printed residence times, because the "
    "entrance solution would overtake the fully-developed film only for D below 1.0e-12 m2/s, three "
    "decades under any row; over Table S1's tau = 4-12 min the band therefore collapses onto the "
    "value itself, and the microfluidic column gives " + _sbrow("micro") + ". What the column is "
    "exposed to is the half-gap rule, the same fully-developed bound that limits every channel "
    "cell in this model; the exact fully-developed Sherwood number for one active wall is somewhat "
    "above 4, so the rule errs toward a thicker film and a lower ceiling.")
add("7. Reactors", "Levich: delta = 1.61 D^(1/3) nu^(1/6) omega^(-1/2)", "1.61", "-", "measured",
    "the coefficient printed BY the source for the diffusion-layer form. This row previously "
    "carried 1.613, derived as 1/0.62 from the RDE mass-transfer constant m0 = 0.62 D^(2/3) "
    "omega^(1/2) nu^(-1/6). That derivation is arithmetically fine but propagates a rounding: 0.62 "
    "is itself a 2-significant-figure value, and 1/0.62 = 1.6129 whereas 1/0.62048 = 1.6117, so "
    "1.613 presented precision the input did not carry and disagreed with julia/correlations.jl, "
    "which computes with 1.61. Retrieved 2026-08-24 from the source PDF in papers for model/: the "
    "constant survives OCR only in the Sect. 12.4 zone-diagram passage, as "
    "delta^2/D = (1.61)^2 nu^(1/3) / (omega D^(1/3)) -- algebraically exactly "
    "delta = 1.61 D^(1/3) nu^(1/6) omega^(-1/2). Origin: Levich, Physicochemical Hydrodynamics, "
    "Prentice-Hall, 1962, for which no page could be verified; the accessible locator below is "
    "used instead", BF,
    "p. 30, footnote 11 (cross-referring Sect. 9.3.2); coefficient confirmed in Sect. 12.4",
    "The exact coefficient is 1.6117; the printed 1.61 is 0.11% below it, and 1.613 -- the value "
    "obtained by inverting the 2-significant-figure 0.62 -- is "
    "0.08% above, a 0.186% spread end to end. Bounded by direct recomputation of the RDE column at "
    "all three values: median 108.49 / 108.37 / 108.29 mA cm-2, and the counts are identical in "
    "every case (36/50 clearing 25, 32/50 clearing 50). No reported number or count depends on the "
    "choice. The rotating-disc film carries no laminar-regime assertion, unlike the Leveque "
    "coefficient, which is asserted only below Re = 2300.")
add("7. Reactors", "RDE operating point", "1600", "rpm", "assumption",
    "a declared convention, not a measured quantity: 1600 rpm is the customary RDE reference speed. "
    "It is not the measured quantity of the Levich row, though it is sometimes tabulated there as though it were the "
    "quantity", "declared operating point", "",
    "delta ~ omega^(-1/2), so 400-3600 rpm spans 2x in delta and 2x in i_lim. The RDE is a "
    "reference rung rather than a preparative architecture, and it brackets the rotating cylinder "
    "from below in every solvent across that range, so the architecture ordering is unchanged.")
# DEMOTED measured -> assumption on 2026-08-22. This row was state A while its OWN sensitivity
# field said "The coefficient 1.85 could not be page-anchored inside either source in this pass".
# By the standard's definition of measured -- a locator a reader can open to SEE the number -- a
# whole-article page range beside a text that admits the number was never located there is not
# state A. It is load-bearing: 1.85 sets delta for BOTH flow archetypes, i.e. two of the six
# columns of Table S5 and two rungs of the architecture ladder. Reinstate it as measured the
# moment someone opens pp. 875-882 and records the equation number.
add("7. Reactors", "Leveque: Sh = 1.85 (Re Sc dh/L)^(1/3)", "1.85", "-", "assumption",
    "laminar entrance-region correlation for parallel plates with dh = 2h. The code asserts "
    "Re < 2300 and floors delta at h/2. Since 2026-09-07 NO archetype film is computed from it: "
    "the two flow archetypes are measured films (Watkins 2023) and the microfluidic film is the "
    "half-gap floor, which this correlation is evaluated only to confirm binds. It still computes "
    "the S8.1 illustration of what intensification costs.",
    "Pickett & Ong, 'The influence of hydrodynamic and mass transfer entrance effects on the "
    "operation of a parallel plate electrolytic cell', Electrochim. Acta 1974, 19, 875-882, DOI "
    "10.1016/0013-4686(74)85036-X; restated in Walsh & Ponce de Leon, Electrochim. Acta 2018, 280, "
    "121-148", "Electrochim. Acta 1974, 19, 875-882 (experimental validation in this exact geometry)",
    "Not page-anchored, which is why this row is state C rather than state A: the coefficient "
    "1.85 is not located to an equation within either source, and a whole-article page range is "
    "not a locator. It sets no reported number. The microfluidic film would leave the half-gap "
    "floor only if the coefficient exceeded about 10 at the largest Leveque group any row reaches, "
    "so no plausible value of it moves that column, and the other six columns never see it. In the "
    "S8.1 illustration the conversion per pass scales with it directly and the pressure drop not at "
    "all, so a 10 % change in the coefficient moves the per-pass conversions by 10 % and leaves the "
    "1 mm to 250 um ratios, which are what that section reports, unchanged.")
## RETIRED 2026-09-07: "Parallel-plate flow-cell geometry" (assumption: gap 1 mm, L 5 cm, u 5 cm/s),
## "Thin-gap microflow gap" (measured 250 um, Watts 2011 / Noel 2019) and "Thin-gap microflow
## operating point" (assumption: L 2.5 cm, u 10 cm/s). The two flow archetypes were declared
## operating points with no source for their velocities; they are replaced by measured films and
## the Mo 2020 cell above. Verbatim text of the retired rows: docs/ARCHETYPE_REANCHOR_20260907.md.
add("7. Reactors", "Illustrative channel pair (S8.1)",
    "1 mm / 5 cm / 5 cm/s; 250 um / 2.5 cm / 10 cm/s", "-", "assumption",
    "the declared pair of generic laminar parallel-plate channels behind the S8.1 illustration of "
    "what thinning a gap costs (residence time, conversion per pass, pressure drop). These were the "
    "model's two flow archetypes until 2026-09-07 and are kept for that illustration alone; no "
    "archetype column is computed from them", "declared illustration", "",
    "A declared geometry that reaches no reported ceiling, count or median. The S8.1 quantities it "
    "feeds are reported as ratios between the two channels, and those ratios are set by the gap "
    "ratio alone: delta scales as h^(2/3) L^(1/3) u^(-1/3) in the entrance regime, so the 4x gap "
    "step gives a 2.5x film step at any common length and velocity, and the pressure-drop ratio "
    "1/h^2 is 16x whatever the velocity. Changing the pair changes the absolute per-pass "
    "conversions, which S8.1 reports only as being under 5 %.")
add("7. Reactors", "Eisenberg RCE: Sh = 0.0791 Re^0.70 Sc^0.356", "0.0791", "-", "measured",
    "turbulent rotating-cylinder correlation, fitted by the limiting-current technique to the "
    "ferri/ferrocyanide couple at nickel cylinders in alkaline aqueous solution",
    "Eisenberg, Tobias & Wilke, J. Electrochem. Soc. 1954, 101, 306-320, DOI 10.1149/1.2781252",
    "J. Electrochem. Soc. 1954, 101, 306-320",
    "Extrapolation flagged, and its DIRECTION matters. Eisenberg, Tobias & Wilke 1954 state "
    "their own calibration on p. 313, retrieved verbatim: 'a Schmidt number variation of "
    "%d to %d and a Reynolds number range of 112.0-162,000'. Computed over the fifty rows "
    ": Sc runs %.0f (min) / %.0f (median) / "
    "%.0f (max), so %d of %d sit BELOW the fitted floor and only %d above the ceiling. The "
    "extrapolation is therefore predominantly to LOW Sc -- aprotic organics are low-Sc "
    "relative to aqueous ferricyanide, because their low viscosity raises D and lowers nu "
    "together -- and Re runs %.0f-%.0f, inside the fitted range throughout. A sensitivity on "
    "a fitted correlation must preserve the fit where it was made: swapping the exponent "
    "alone leaves the coefficient 0.0791 attached to a curve that no longer reproduces the "
    "calibration data, so it is not a bound. Re-anchored at the calibration centre, the "
    "Sc^(1/3) asymptote moves per-row values by %.3f-%.3fx and the RCE median %.1f -> %.1f "
    "mA cm-2, so on this axis the tabulated column is if anything an under-estimate rather "
    "than an upper one, and no threshold count moves."
    % (_SX["cal_window"][0], _SX["cal_window"][1], _SX["sc_min"], _SX["sc_median"],
       _SX["sc_max"], _SX["n_below"], _SX["n_total"], _SX["n_above"], _SX["re_lo"],
       _SX["re_hi"], _SX["factor_lo"], _SX["factor_hi"], _SX["medians"]["rce"],
       _SX["medians_alt"]["rce"]))
## RETIRED 2026-09-01: "delta (stirred batch): measured comparison". That row existed to
## keep a DECLARED 100 um honest by standing the measurement beside it. The measurement is
## now the adopted value of the row above, so keeping a second row for the same number left
## the registry carrying two entries of 200 um with contradictory framings, one of them
## describing a state that no longer exists. Its content -- the +/- 7 um, the O2 proxy
## caveat and the direction it errs in -- is carried in the adopted row.
add("7. Reactors", "RCE operating point", "d 1.2 cm, 3000 rpm", "-", "assumption",
    "a declared laboratory operating point", "declared operating point", "",
    "Sh ~ Re^0.70 with Re ~ omega d^2, so 1000-5000 rpm spans about 3x in k_m. The rotating "
    "cylinder remains the highest rung across that range.")
add("7. Reactors", "Thresholds 25 / 50 mA cm-2", "25; 50", "mA cm-2", "measured",
    "industry-survey bins, n = 14 companies reporting scale-up current density: 10 below 25, three "
    "between 25 and 50, one above 50 mA cm-2. Already at state A before this pass and preserved "
    "unchanged",
    "Ferretti, Cohen, Deng, Diwan, Frederick & Lehnherr, Org. Process Res. Dev. 2025, 29, 322-332",
    "Fig. 11 (page-verified)",
    "The thresholds themselves are sound. The exposure lies in the claim built on them, not in this "
    "row: see the delta (stirred batch) sensitivity.")

# -- 8. Electrode-kinetics / voltage stack ------------------------------------
add("8. Voltage stack", "E0 (thermodynamic + kinetic floor)", "2.0", "V", "assumption",
    "a representative organic-electrolysis cell floor; no single reaction in the set fixes it",
    "declared modelling choice", "",
    "E0 is a constant offset in E_cell and does not enter the dissipation q(i) of Eq. S20 at all, "
    "so it moves no boil-off ceiling and no §S6 margin. Tested 1.5-3.0 V: E_cell shifts by the "
    "same amount, and the ohmic term dominates E_cell above ~10 mA cm-2 in every solvent in the "
    "set.")
add("8. Voltage stack", "Tafel slope b = 2RT/F per electrode", "0.0514", "V", "derived",
    "2RT/F at 298.15 K with R and F from category 1; symmetric Butler-Volmer with alpha = 1/2, "
    "inverted through asinh and applied to both electrodes", BF,
    "ch. 3 (Butler-Volmer and Tafel forms)",
    "The only free choice is alpha = 1/2; alpha in [0.3, 0.7] moves the activation term by under "
    "60 mV against ohmic terms of 1-50 V in these cells.")
add("8. Voltage stack", "i0 (exchange current density)", "1.0", "mA cm-2", "assumption",
    "an illustrative symmetric value for both electrodes; no measured i0 exists for these couples "
    "on these electrodes in these media", "declared modelling choice", "",
    "Treating i0 as negligible holds only where ohmic heat dominates, which is not "
    "everywhere, and the split is sharp: the activation term is gap-INDEPENDENT, so it matters "
    "exactly where the ohmic "
    "term has been removed. Swept 0.01-10 mA cm-2 across all four §S6 solvents: every "
    "centimetre-gap architecture -- both batch cells, both flow cells and both rotating "
    "electrodes -- moves by at most 3 pct, because 85-98 pct of its heat is ohmic; the 25 um "
    "microfluidic moves by -35/+32 pct and the zero-gap stack by -42/+47 pct, because in a "
    "thin gap the activation term is most of q. No stated conclusion flips inside "
    "0.01-10 mA cm-2: at the stack all four solvents still fail (margins 0.04-0.23x); at the "
    "microfluidic all four still clear (THF 2.60-4.26x, MeCN 4.02-8.09x, DMF 7.49-11.93x, "
    "aqueous NaOH 5.40-11.83x). i0 can matter only where activation heat is comparable to ohmic "
    "heat, and no verdict reported in this section sits in that regime.")

# -- 9. Thermal model + the §S6 architecture constants ---------------------
# STRUCTURAL RESULT OF THE THERMAL SOURCING PASS, stated once and reused: because
# U' = [(1/h_int + 1/h_ext)^-1] * sigma with h_ext ~ 13 W m-2 K-1, the EXTERNAL film is 87-99.7 pct
# of the series resistance. Sweeping h_int from 50 to infinity -- a range above 2e4, spanning the
# entire Incropera Table 1.1 liquid band -- moves every boil-off ceiling by -5/+6 pct. The genuinely
# load-bearing thermal parameters are, in order: sigma > i_design > h_ext > everything else.
_HINT_SWEEP = (50., 100., 800., 2000., 1.0e12)


def _hint_series(reactor, sl="DMF"):
    k, tb = _th_by_solvent(sl)
    return " / ".join("%.1f" % _TM.i_boil(k, reactor[1], tb,
                                          _TM.U_passive(reactor[2], h)) for h in _HINT_SWEEP)


S_HINT = ("h_int is not load-bearing anywhere. Swept 50 -> infinity (a range above 2e4, spanning "
          "the whole Incropera Table 1.1 liquid band), every boil-off ceiling moves by -5/+6 pct: "
          "the dimethylformamide ceiling runs %s mA cm-2 at h_int = 50 / 100 / 800 / 2000 / "
          "infinity in the %s, and %s mA cm-2 in the %s, which is the thinnest-gap architecture "
          "and the one where a developing-flow correction to h_int would be largest. No conclusion "
          "in S6.1 or S6.2 is sensitive to any of the four h_int values."
          % (_hint_series(_TH_RX[0]), _TH_RX[0][0], _hint_series(_TH_MIC), _TH_MIC[0]))
# The four `<solvent>: Tb` rows predate the `T_boil: <solvent>` rows the thermal model actually
# reads, and Table S7i was printing two boiling points for the same solvent. Nothing is deleted --
# they are marked display-only, which is this registry's own mechanism for a row that feeds no
# result, so the liveness rule omits them from the published subset while the internal record
# keeps them with their history.
_DUP_TB = (" This row is display-only: the thermal model reads the CRC value from the "
           "'T_boil: %s' row of this registry, and this entry predates it. It is kept as the "
           "internal record of the value carried before, and is omitted from the published "
           "subset so that no solvent is given two boiling points in one table.")

add("9. Thermal model", "THF: cp", "1.72", "J g-1 K-1", "derived",
    "Cp,liquid = 124.1 J mol-1 K-1 at 298.15 K divided by M = 72.106 g mol-1 gives 1.721 J g-1 K-1. "
    "The inherited citation (CRC viscosity/density tables) does not contain heat capacities and has "
    "been withdrawn",
    NIST + " -- tetrahydrofuran, CAS 109-99-9 (primary reference Costas & Patterson 1985)", "",
    "cp enters only the transient tau = m cp / UA, never a steady-state ceiling.")
add("9. Thermal model", "THF: Tb", "66.0", "C", "measured", "normal boiling point, 65-66 C",
    CRC, L_ORG("Tetrahydrofuran"), (_DUP_TB % "THF").strip())
add("9. Thermal model", "DMF: cp", "2.05", "J g-1 K-1", "derived",
    "150.0 J mol-1 K-1 divided by M = 73.095 g mol-1 gives 2.052 J g-1 K-1. Note that this is the "
    "top of the measured spread: NIST lists 146.05 (Grolier 1993), 148.16 (Kolker 1992), 148.36 "
    "(Zegers & Somsen 1984), 150.0 (Petrov 1989) and 150.8 (de Visser & Somsen 1979) J mol-1 K-1",
    NIST + " -- N,N-dimethylformamide, CAS 68-12-2", "",
    "The measured spread 146.05-150.8 J mol-1 K-1 corresponds to cp = 2.00-2.06 J g-1 K-1, i.e. "
    "+/-1.5 pct. It affects only tau (the S6.1 accounting note), never a ceiling or a margin.")
add("9. Thermal model", "DMF: Tb", "153.0", "C", "measured",
    "T_boil = 426 +/- 1 K, the average of eight reported values, i.e. 152.9 C",
    NIST + " -- N,N-dimethylformamide, Phase-Change Data", "T_boil, Phase-Change Data table",
    (_DUP_TB % "DMF").strip())
add("9. Thermal model", "MeCN: cp", "2.23", "J g-1 K-1", "derived",
    "91.7 J mol-1 K-1 (de Visser & Somsen 1979; Kolker 1992) divided by M = 41.05 g mol-1 gives "
    "2.234 J g-1 K-1. New row: previously unregistered",
    NIST + " -- acetonitrile, CAS 75-05-8", "", "Enters only the transient tau.")
add("9. Thermal model", "aqueous electrolyte: cp", "4.18", "J g-1 K-1", "measured",
    "liquid water at 25 C, used for the aqueous §S6 trace. New row: previously unregistered",
    CRC, L_WATER, "")
add("9. Thermal model", "MeCN: Tb", "82.0", "C", "assumption",
    "the model uses 82.0 C; the tabulated normal boiling point is 81.6 C. Retained as a rounding so "
    "that the registry describes what make_figK.py actually computes", CRC, L_ORG("Acetonitrile"),
    "The +0.4 K rounding raises every MeCN ceiling by under 0.5 pct and no conclusion is affected. "
    "The tabulated 81.6 C is registered on this row as its sensitivity rather than applied."
    + _DUP_TB % "MeCN")
add("9. Thermal model", "aq. NaOH/KOH: Tb", "100.0", "C", "assumption",
    "the model uses the pure-water boiling point. The ebullioscopic elevation is not in fact "
    "negligible and is computable: dTb = Kb i m = 0.512 K kg mol-1 x 2 x 1.0 mol kg-1 = 1.0 K, so "
    "the correct value for 1 M NaOH is 101.0 C", CRC, L_WATER + "; " + L_EBULL,
    "Adopting 101.0 C raises the aqueous ceiling by 1.4 pct. The aqueous reference clears every "
    "preparative architecture either way, so nothing is affected; the elevation is small but not "
    "negligible, and the computed 1.0 K is stated rather than assumed away."
    + _DUP_TB % "H2O (used for 1 M NaOH aq)")
add("9. Thermal model", "Cell volume / electrode area", "100 mL / 10 cm2", "-", "assumption",
    "the batch archetype the whole thermal section is built on. The inherited note, 'steady state "
    "independent of volume', is wrong and has been withdrawn: inventory and rejecting surface are "
    "physically coupled, A_ext ~ V^(2/3), so i_boil ~ V^(1/3)", "declared archetype", "",
    "Swept 50 / 100 / 500 / 1000 mL: A_ext scales as V^(2/3) and so does sigma, so the "
    "dimethylformamide passive ceiling runs %s mA cm-2, a %.2fx span. The batch verdict does not "
    "turn on the vessel: tetrahydrofuran's ceiling runs %s mA cm-2 over the same sweep against an "
    "unstirred transport ceiling of %.1f mA cm-2, so transport binds before heat at every volume. "
    "No conclusion flips."
    % (" / ".join("%.0f" % _th_vol("DMF", V) for V in (50, 100, 500, 1000)),
       _th_vol("DMF", 1000) / _th_vol("DMF", 50),
       " / ".join("%.0f" % _th_vol("THF", V) for V in (50, 100, 500, 1000)), _TH_RX[0][4]))
add("9. Thermal model", "Vessel external area", "%.5f" % _TM.A_EXT_BEAKER, "m2", "derived",
    "DERIVED from the declared archetype, 2026-09-13. The tabled 0.0125 m2 was the external area "
    "of a 5 cm diameter by 8 cm cylinder -- which encloses 157 mL, not the 100 mL this archetype "
    "declares -- so it credited about 3 cm of dry headspace wall as rejecting surface. The area "
    "that rejects heat from a 100 mL charge in a 5 cm vessel is the wetted wall plus the base, and "
    "it is a consequence of the declared charge and diameter rather than a free parameter: fill "
    "height = 0.1 L / (pi x 0.025^2) = %.2f cm, A = pi x 0.05 x %.4f + pi x 0.025^2 = %.5f + "
    "%.5f = %.5f m2. Computed in figs/thermal_model.py from the declared archetype so the "
    "construction cannot drift from it"
    % (100*_FILL_M, _FILL_M, _math.pi*0.05*_FILL_M, _math.pi*0.025**2, _TM.A_EXT_BEAKER),
    "elementary geometry of the declared vessel (wetted wall + base of a right cylinder)", "",
    "The alternative is 0.0125 m2, the external area of the full 5 x 8 cm cylinder including its "
    "dry headspace wall. Working from the wetted area instead lowers every ceiling computed on "
    "this row by 10.8-11.4 pct "
    "(THF 29.5 -> 26.3, MeCN 87.8 -> 78.2, DMF 88.8 -> 79.2, aqueous NaOH 282.4 -> 250.2 "
    "mA cm-2) and changes none of the 20 architecture-solvent verdicts that rest on it. The move "
    "is conservative in the sense that matters here: less rejecting surface, lower ceilings, the "
    "boiling problem stated as slightly worse. The residual exposure is the declared 5 cm "
    "diameter, which sets how the same 100 mL is distributed between wall and base; a 4 cm vessel "
    "gives 0.01115 m2 and a 6 cm vessel 0.00920 m2, a span of 1.21x.")
add("9. Thermal model", "h natural convection (air)", "7", "W m-2 K-1", "derived",
    "RE-derived. the inherited citation (Incropera Table 1.1) contains only the range 2-25 W m-2 "
    "K-1 for free convection in gases and cannot support the value 7. Computed instead from the "
    "laminar vertical-plate correlation Nu_L = 0.68 + 0.670 Ra_L^(1/4) / "
    "[1 + (0.492/Pr)^(9/16)]^(4/9), valid for Ra_L below about 1e9, with L = 0.08 m and "
    "T_inf = 298.15 K: Ra_L = 1.42e6, Nu = 18.4, h = 6.4 W m-2 K-1 at Ts = 65 C, 7.3 at 100 C and "
    "8.2 at 153 C",
    "Churchill & Chu, Int. J. Heat Mass Transfer 1975, 18, 1323-1329; restated as " + INCROP +
    ", Eq. 9.26-9.27, with air properties from " + INCROP + ", Table A.4",
    "Int. J. Heat Mass Transfer 1975, 18, 1323-1329; Incropera 6th ed., Eq. 9.26-9.27 and Table A.4",
    "The vertical-cylinder criterion D/L >= 35/Gr_L^(1/4) gives 0.625 < 0.93 and is not satisfied, "
    "so curvature raises Nu and the flat-plate value is a conservative underestimate.")
add("9. Thermal model", "h radiation (linearized)", "6-8", "W m-2 K-1", "derived",
    "h_r = eps sigma_SB (Ts + Tsur)(Ts^2 + Tsur^2) with eps = 0.9 and Tsur = 298.15 K gives 6.6 at "
    "65 C, 7.2 at 82 C, 7.8 at 100 C and 10.0 at 153 C. Radiation is comparable to convection over "
    "this range, so omitting it would overstate the boiling problem", INCROP, "Eq. 1.9",
    "See the emissivity row for the residual exposure.")
add("9. Thermal model", "Surface emissivity eps (borosilicate)", "0.9", "-", "assumption",
    "used in the radiation row. New row: previously unregistered and never stated. the Incropera "
    "Table A.11 glass entry was not located for it, and it is deliberately not cited",
    "-- (not page-verified)", "",
    "Tested eps in [0.7, 0.95]: h_ext moves over 11.5-13.3 W m-2 K-1 and every beaker ceiling by "
    "about +/-6 pct (DMF 80.3-85.8 mA cm-2). Nothing flips.")
add("9. Thermal model", "H_EXT (external film: convection + radiation)", "13.0", "W m-2 K-1",
    "derived",
    "the sum of the two rows above evaluated at Ts = 65 C, eps = 0.9, L = 0.08 m and T_amb = 25 C: "
    "6.36 + 6.60 = 12.96, i.e. 13.0. New row: this sum is the constant make_figK.py actually uses "
    "(H_EXT) and it had no registry row -- only its two addends did",
    "rows 'h natural convection (air)' and 'h radiation (linearized)' of this registry", "",
    "Held temperature-independent in the code while the real h_ext runs 13.0 (66 C) -> 14.0 (82 C) "
    "-> 15.1 (100 C) -> 18.2 (153 C), so rejection at the DMF boiling point is understated by about "
    "40 pct. Resolving h_ext(T_b) moves ceilings by THF -0.1 pct, MeCN +3.5 pct, DMF +15.7 pct and "
    "aq. NaOH +7.3 pct; nothing flips. Note that this correction and the vessel-area correction "
    "nearly cancel for DMF (88.8 -> 91.8, i.e. +3 pct).")
add("9. Thermal model", "UA still air (incl. radiation)", "0.1625", "W K-1", "derived",
    "corrected value. UA = H_EXT x A_ext = 13.0 W m-2 K-1 x 0.0125 m2 = 0.1625 W K-1. The inherited "
    "0.20 W K-1 was not reproducible from its own stated inputs (it implies h ~ 16 W m-2 K-1) and "
    "was the row through which the reverse-fitted 0.02 W cm-2 K-1 still-air coefficient entered the "
    "analysis", "rows 'H_EXT' and 'Vessel external area' of this registry", "",
    "With the wetted-area sensitivity (0.00996 m2) UA falls further to 0.129 W K-1. UA sets the "
    "transient tau = m cp / UA (22 min for a 100 mL DMF beaker) and, through U' = UA/A_elec, the "
    "steady state.")
add("9. Thermal model", "sigma (unstirred 100 mL beaker)", "%.2f" % _TM.SIGMA_BEAKER, "-",
    "derived",
    "sigma = A_ext / A_elec = %.5f m2 / 1.0e-3 m2 = %.2f, computed in figs/thermal_model.py "
    "(SIGMA_BEAKER) from the declared archetype so that it cannot be re-tuned silently; "
    "U' = %.5f W cm-2 K-1. Both inputs are declared rows of this registry with their own "
    "sensitivities, and the construction between them is the citation -- the same shape as "
    "delta (unstirred batch), which is derived from a named equation evaluated at a declared "
    "operating point. Note: this does not reproduce the 0.02 W cm-2 K-1 still-air value assumed "
    "in earlier treatments -- the geometric construction lands about 43 pct below it, and no "
    "sigma consistent with the declared vessel recovers 0.02"
    % (_TM.A_EXT_BEAKER, _TM.SIGMA_BEAKER, _TM.U_passive(_TM.SIGMA_BEAKER, 100.)),
    "elementary geometry of the declared vessel; see row 'Vessel external area'", "",
    "Inherits the vessel-geometry exposure of that row: across the 4-6 cm diameter span sigma "
    "runs 11.15-9.20 and the beaker ceilings move by about -8/+8 pct. Nothing flips.")
add("9. Thermal model", "sigma (stirred 100 mL beaker)", "%.2f" % _TM.SIGMA_BEAKER, "-",
    "derived",
    "the same vessel as the unstirred beaker; stirring changes h_int, not the external area. "
    "U' = %.5f W cm-2 K-1" % _TM.U_passive(_TM.SIGMA_BEAKER, 800.),
    "elementary geometry of the declared vessel; see row 'Vessel external area'", "",
    "Stirring raises U' only from %.5f to %.5f W cm-2 K-1, i.e. %.0f pct, because h_ext and not "
    "h_int is the limiting resistance -- the quantitative basis for the statement that stirring a "
    "beaker is nearly useless thermally."
    % (_TM.U_passive(_TM.SIGMA_BEAKER, 100.), _TM.U_passive(_TM.SIGMA_BEAKER, 800.),
       100*(_TM.U_passive(_TM.SIGMA_BEAKER, 800.)/_TM.U_passive(_TM.SIGMA_BEAKER, 100.) - 1)))
add("9. Thermal model", "sigma (recirculating flow, RDE, rotating cylinder)",
    "%.2f" % _TM.SIGMA_BEAKER, "-",
    "assumption",
    "INHERITED from the beaker vessel. A transport archetype is fixed by its diffusion layer; a "
    "thermal archetype needs the ohmic path, the heat-rejection area ratio and the internal film, "
    "and an exemplar that measures a boundary layer need state none of them. Watkins' supporting "
    "information gives the copper foil size and the flow rates but no electrode separation and no "
    "electrode areas, and a rotating disc turns in a beaker, so these four take the registered "
    "beaker geometry rather than a housing invented for them",
    "declared basis: the value of row 'sigma (unstirred 100 mL beaker)'", "", _TG_SENS_SIGMA)
add("9. Thermal model", "sigma (microfluidic 25 um)", "7.0", "-", "assumption",
    "the single load-bearing sigma. No source exists. The declared chip that reproduces it is a "
    "5 x 3.5 cm footprint, 2.05 cm thick, with 1 cm plates: A_ext = 69.8 cm2 over 10 cm2 gives "
    "6.98; a thinner 1.1 cm chip gives 5.4. New row: previously unregistered",
    "declared chip geometry, now bracketed by the exemplar's own drawings: Mo et al., Science "
    "2020, 368, 1352-1357, Supplementary Materials Appendix A, Fig. S20A p. 58 (the aluminium "
    "holder for the small-scale cell, 3.00 x 3.00 inch, 'Unit: inch'), with the glassy carbon "
    "plates given as 50 x 50 x 3 mm on p. 3",
    "SM Appendix A, Fig. S20A p. 58; electrode plates p. 3",
    "Corroborated by the exemplar, which is what this row lacked until 2026-09-13. The two outer "
    "aluminium faces alone give 2 x (3.00 in)^2 = 116 cm2, a lower bound on the rejecting area, "
    "and the channel area follows from V = Q tau at the 25 um gap with tau = 4 min (Table S1 "
    "entries 9-12) and the 5-15 uL min-1 the procedures use, i.e. 8-24 cm2. Together they bracket "
    "sigma at 4.8-14.5 for that cell and the declared 7.0 sits inside, the mid-range flow rate "
    "giving 7.3. Neither end is adopted: the bracket is wide, and the archetype's electrode is "
    "the declared 10 cm2 rather than Mo's channel. "
    "Tested sigma in [3.5, 21], half to three times the declared value. Judged against this "
    "cell's own median transport ceiling of %.1f mA cm-2, every electrolyte clears at every point "
    "in that range (%s), and the breaking points lie far below it -- the tightest is %.2fx the "
    "declared 7.0. This row carries no verdict that turns inside its own band. It remains the one "
    "surface-area ratio in the model with no source of any kind, which is why the band is stated."
    % (_TH_MIC[4],
       ", ".join("%s %.2f-%.2fx"
                 % (sl,
                    _th_margin(k, tb, (_TH_MIC[0], _TH_MIC[1], 3.5, _TH_MIC[3], _TH_MIC[4])),
                    _th_margin(k, tb, (_TH_MIC[0], _TH_MIC[1], 21.0, _TH_MIC[3], _TH_MIC[4])))
                 for sl, k, tb in _TH_SOL),
       max(r["sigma_flip_x"] for r in _TG["rows"]
           if r["arch"].startswith("micro") and r["sigma_flip_x"] is not None)))
add("9. Thermal model", "sigma (zero-gap PEM stack)", "0.8", "-", "assumption",
    "no source exists. An interior cell of a stack rejects heat only through the plate edge, so "
    "sigma = (perimeter x cell pitch) / A_elec: a square 10 cm2 cell of perimeter 12.65 cm at 8.7 mm "
    "pitch gives 1.10 and a circular one 0.98. The 8.7 mm pitch itself came from a stack design "
    "that could not be opened (403) and is deliberately not cited. new row: previously unregistered",
    "declared stack geometry", "",
    "Tested pitch 4-12 mm, i.e. sigma in [0.51, 1.52]: the zero-gap margin runs 0.11x-0.23x against "
    "i_design = 1000 mA cm-2, so all four solvents fail at every point in the range and the "
    "zero-gap conclusion is unconditional. Adopting sigma = 1.0 instead of 0.8 would move the "
    "margins from 0.07-0.18x to 0.08-0.21x.")
for lab, hv in [("stagnant electrolyte", 100.), ("stirred electrolyte", 800.),
                ("forced flow, centimetre gap", 2000.), ("forced flow, thin gap", 5000.)]:
    extra = ""
    cite = INCROP
    if lab == "stirred electrolyte":
        extra = (" Independently recovered from an agitated-vessel correlation: Nu = 0.36 Re_a^0.67 "
                 "Pr^0.33 (mu/mu_w)^0.14 with Re_a = N D_a^2 rho / mu gives h = 669 W m-2 K-1 for "
                 "DMF in a 5 cm vessel with a 2.5 cm impeller at 300 rpm, 1203 at 3 cm and 500 rpm, "
                 "and 3087 at 3.5 cm and 1500 rpm.")
        cite = INCROP + "; Chilton, Drew & Jebens, Ind. Eng. Chem. 1944, 36, 510-516"
    if lab == "forced flow, centimetre gap":
        extra = (" Not defensible from internal-flow theory -- D_h = 10 mm laminar with Nu = 8.23 "
                 "gives h ~ 132 W m-2 K-1, not 2000 -- but per the sweep opposite it does not "
                 "matter: correcting 2000 to 132 moves the flow-cell DMF ceiling from 158.5 to "
                 "149.4 mA cm-2.")
    add("9. Thermal model", f"h_int ({lab})", f"{hv:g}", "W m-2 K-1", "assumption",
        "a declared internal film coefficient, bounded but not fixed by the tabulated ranges (free "
        "convection in liquids 50-1000; forced convection in liquids 100-20 000 W m-2 K-1). New "
        "row: previously unregistered." + extra, cite,
        "Table 1.1 (ranges only; the table does not license any single value)", S_HINT)
# 2026-09-12: the four DECLARED archetype design currents are RETIRED. Each architecture is now
# run at the median limiting current the published 50-reaction matrix computes for it, which is a
# number Figure 5b already prints, so the transport figure and the thermal figure became one
# argument: at the current transport allows, can the cell reject the heat? Three of the four
# retired rows were ledger-conditional, i.e. among the entries the standard flags to read before
# answering a referee, and retiring them removes that conditionality rather than restating it.
# The zero-gap stack keeps a declared current, because it is an industrial REFERENCE and not one of
# the modelled archetypes -- Figure 5 reaches no Tier-4 cell, so the matrix computes nothing for it.
_IDES_ROW = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                          "julia", "tier0_ec_matrix.csv")
with io.open(_IDES_ROW, encoding="utf8") as _fh:
    _IR = list(_csv.DictReader(_fh))
_IDES = {}
for _k in ("natural", "stirred", "flow", "anec", "micro", "rde", "rce"):
    _v = sorted(float(_r[_k]) for _r in _IR)
    _IDES[_k] = 0.5 * (_v[len(_v) // 2 - 1] + _v[len(_v) // 2]) if len(_v) % 2 == 0 else _v[len(_v) // 2]
add("9. Thermal model", "Transport ceiling, used as the thermal operating point (six architectures)",
    " / ".join("%.1f" % _IDES[_k] for _k in ("natural", "stirred", "flow", "micro", "rde", "rce")),
    "mA cm-2", "derived",
    "each architecture's own median limiting current over the 50-reaction set, read from the "
    "published matrix rather than declared: unstirred, stirred, recirculating flow, "
    "microfluidic, rotating disc, rotating cylinder. This replaces four declared design currents "
    "(50, 50, 100 and 500 mA cm-2) whose only basis was practice quoted for a reactor class",
    "the median over the solved 50-reaction transport matrix, per architecture (Stage 0 for the "
    "direct and catalyst-carried entries, the EC-prime solver for the mediated ones; Tables S2 "
    "and S5)", "",
    "Not an assumption: it moves only when the transport model moves, and the transport model's own "
    "sensitivities bound it. IT IS NOT A DESIGN CURRENT, and the distinction matters for how the "
    "figure is read. The thermal margin is the ratio of two CEILINGS -- how much current the cell can shed "
    "heat at, over how much it can supply reactant at -- so it says which limit binds first and is "
    "agnostic to whatever current an operator actually chooses. Only the cooling-duty analysis "
    "evaluates a quantity AT a current, and it evaluates it at this one, which is the strongest "
    "case the architecture can be asked to meet.")
add("9. Thermal model", "i_design (zero-gap PEM stack)", "1000", "mA cm-2", "assumption",
    "the declared design current of the industrial REFERENCE, kept declared because Figure 5 "
    "reaches no Tier-4 architecture and the matrix therefore computes no ceiling for it",
    "declared operating point", "",
    "PEM water electrolysis operates nominally at "
    "1.0-2.0 A cm-2 (Carmo, Fritz, Mergel & Stolten, Int. J. Hydrogen Energy 2013, 38, 4901-4934) "
    "and zero-gap CO2 electrolysis sustains A cm-2-class operation (Endrodi, Samu, Kecsenovity, "
    "Halmagyi, Sebok & Janaky, Nature Energy 2021, 6, 439-448: 420 +/- 50 mA cm-2 partial current "
    "over 200 h). Tested 500-2000 mA cm-2: the stack fails in all four electrolytes at every point, "
    "and it fails at a gap of zero as well, so its verdict rests on no geometry at all.")
for lab, gv, meth, cit, loc, sens in [
 ("beaker", "2.0e-2 m",
  "the canonical 'beaker, 2 cm' archetype of julia/cellvoltage.jl. A 5 mm gap "
  "which is that file's tight-batch spacing rather than beaker practice, and understated beaker "
  "ohmic heat fourfold", "declared archetype", "",
  "Tested 1-2 cm (real beaker setups space electrodes 1-2 cm apart): q ~ L, so ceilings scale as "
  "L^-1/2 and every ceiling on this gap rises by up to 1.4x at 1 cm. %d of the %d archetypes "
  "share this gap (%s), because rotation and recirculation thin the diffusion layer and move no "
  "electrode. " % (len(_TG["shared_gap_rows"]), len(_TM.REACTORS),
                   ", ".join(_TG["shared_gap_rows"])) + _TG_SENS),
 ("rotating cylinder", "2.435e-2 m",
  "DERIVED from the cell the rotating-cylinder correlation was built in. Eisenberg, Tobias & Wilke "
  "turn nickel rotors of 1.273, 2.48 and 5.024 cm diameter inside concentric outer cylinders of "
  "6.07, 9.87 and 13.69 cm inside diameter, and state that those combinations span gap-to-inner-"
  "diameter ratios of 0.104 to 4.88, which the printed dimensions reproduce. At the 1.2 cm rotor "
  "this model turns, the tightest annulus that cell offers is (6.07 - 1.2)/2 = 2.44 cm",
  "Eisenberg, Tobias & Wilke, J. Electrochem. Soc. 1954, 101, 306-320",
  "p. 308 (rotor and outer-cylinder dimensions; gap ratios 0.104-4.88)",
  "The same paper's widest annulus at this rotor is 6.25 cm, and that is the row's band. Across it "
  "the rotating-cylinder ceilings fall about 1.6x, and the tetrahydrofuran verdict holds throughout "
  "while the acetonitrile and dimethylformamide verdicts are the conditional pair reported on the "
  "beaker-gap row."),
 ("microfluidic 25 um", "2.5e-5 m",
  "MEASURED, and the same number the transport archetype derives its 12.5 um half-gap film from: "
  "the thinnest FEP spacer of the cell the exemplar was run in",
  "Mo, Rughoobur, Nambiar, Zhang, Jensen et al., Science 2020, 368, 1352-1357",
  "supplementary material p. 13 (\"the inter-electrode distance is controlled by the thickness of "
  "FEP spacer ... the thinnest FEP spacer (0.001\", 25 um)\")", ""),
 ("zero-gap PEM stack", "1.0e-4 m",
  "intended as a membrane thickness, but no named membrane with a page-anchored thickness is "
  "attached to it. Thin-gap preparative cells at 100 um do exist (a 4-methylanisole thin-gap cell, "
  "J. Appl. Electrochem. 2008, DOI 10.1007/s10800-007-9444-8), but that paper could not be opened "
  "and its contents are not asserted here", "-- (no page-anchored source)", "",
  "Tested 50-200 um: q ~ L, so ceilings span 1.4x either way and all four solvents still fail at "
  "1 A cm-2 across the range. Page-anchoring would require a named separator (Nafion 115, 117 or 212) with a "
  "page-anchored thickness before 100 um is published as a membrane figure.")]:
    add("9. Thermal model", f"Inter-electrode gap ({lab})", gv, "m",
        "measured" if cit.startswith("Mo,") else
        ("derived" if cit.startswith("Eisenberg") else "assumption"),
        meth + ". New row: previously unregistered", cit, loc, sens)
add("9. Thermal model", "kappa (0.1 M KHCO3 aq, exemplar cell-resistance check)", "8.9",
    "mS cm-1", "measured",
    "measured at 20 C and used for one purpose only: to test the INHERITED 2 cm ohmic path of the "
    "two flow archetypes against a resistance their own exemplar reports. 0.1 M KHCO3 is 0.996 "
    "mass pct (M = 100.114 g mol-1, rho = 1.005 g mL-1), so it lands on the table's 1 mass pct "
    "column. Carried to 25 C with the same 1.5-1.9 pct/K bracket the 1 M NaOH aq row uses it is "
    "9.57-9.75 mS cm-1. The column was read by x-coordinate, not token order: the header '1%' sits "
    "at x = 271 and the value at x = 270.8, the same discipline the interleaved NaCl/KCl columns "
    "of this table needed", CRC,
    "'Electrical Conductivity of Aqueous Solutions', p. 5-71, potassium hydrogen carbonate "
    "(KHCO3) row, 1 mass pct column, 20 C", "")
add("9. Thermal model", "Vessel wall conduction (omitted from U')", "0", "m2 K W-1", "assumption",
    "the heat balance puts the internal and external films in series and carries NO conduction "
    "resistance through the vessel wall between them. That is why it is declared rather than "
    "silent: the omission is invisible for glass and is not for a machined plastic body",
    "declared model simplification", "",
    "A 1.5 mm borosilicate beaker wall adds L/k = 0.0014 m2 K W-1 against the external film's "
    "1/h_ext = 0.0769, i.e. 2 pct of the series, which is below the reporting precision of every "
    "ceiling in this section. A 5.6 mm polycarbonate block -- the body of the cell the two flow "
    "archetypes are anchored to -- adds 0.0294, i.e. 28 pct, and would lower that cell's ceilings "
    "by about 15 pct. No archetype in §S6 is computed on a plastic body, so no published number "
    "moves; the bound is registered because any future architecture with a thick low-conductivity "
    "wall would need the term restored.")
# DEMOTED derived -> assumption 2026-08-22. PROVENANCE_STANDARD.md rule B: "A bound is not a
# derivation. If a method yields a range that CONTAINS the tabled value but does not PRODUCE
# it, the row is state C." All three cooling bands are in exactly that position, and each
# said so in its own sensitivity field while carrying the derived label:
#   natural convection -- plotted edges "rounded outward by about 25 pct" from the derived
#                         1.04e-3..1.63e-2 interval;
#   forced air         -- plotted band is a SUBSET of the derivable 2.0e-3..3.1e-1, drawn
#                         for a sigma window of about 3-8 that is registered nowhere;
#   liquid cold plate  -- "the plotted band sits inside the derived interval".
# The forced-air row is the one that matters: S6.2's zero-gap verdict is drawn from its
# UPPER EDGE while the row calls itself "shading only".
add("9. Thermal model", "Cooling band: natural convection", "8e-4 - 2e-2", "W cm-2 K-1", "assumption",
    "the shaded availability band of §S6.2, reproduced from this registry's own inputs: "
    "H_EXT = 13 W m-2 K-1 times sigma in [0.8, 12.5], the figure's full sigma range, gives 1.04e-3 "
    "to 1.63e-2 W cm-2 K-1. New row: previously unregistered",
    "rows 'H_EXT' and the four sigma rows of this registry", "",
    "The plotted edges are rounded outward by about 25 pct relative to the derived interval, which "
    "visually credits passive cooling the model does not have. The tightened edges, 1.0e-3 to "
    "1.6e-2 W cm-2 K-1, are registered on this row as its sensitivity rather than applied, so that "
    "the band this section reports is unchanged. No numeric conclusion depends on it.")
add("9. Thermal model", "Cooling band: forced air", "2e-2 - 8e-2", "W cm-2 K-1", "assumption",
    "forced convection in gases, 25-250 W m-2 K-1, times sigma. New row: previously unregistered",
    INCROP, "Table 1.1 (forced convection, gases: 25-250 W m-2 K-1)",
    "Over the full sigma range [0.8, 12.5] the derivable interval is 2.0e-3 to 3.1e-1 W cm-2 K-1, "
    "so the plotted band is a subset of the derivable range, drawn for sigma of about 3-8. That "
    "must be stated rather than left implicit; the band is shading only.")
add("9. Thermal model", "Cooling band: liquid cold plate", "2e-1 - 1.0", "W cm-2 K-1", "assumption",
    "laminar-to-transitional water channels: k = 0.60 W m-1 K-1 with D_h = 1-3 mm and Nu = 4.36 "
    "(circular, uniform heat flux) to 8.23 (parallel plates) gives h = 872-4938 W m-2 K-1, i.e. "
    "0.09-0.49 W cm-2 K-1, and times sigma of about 1-2 gives 0.13-2.6. New row: previously "
    "unregistered. relabelled from 'PEM-class': the PEM attribution is what fails -- see the "
    "U' liquid cold plate row", INCROP,
    "Table 8.1 and Eq. 8.53 (laminar internal flow); Eq. 8.60 (Dittus-Boelter)",
    "sensitivity (this row is state C: the derivation yields a range that contains the plotted "
    "band but does not produce it). The derivable interval is 0.13-2.6 W cm-2 K-1 for sigma of "
    "about 1-2, against the plotted 0.2-1.0, so the plotted band is a subset drawn near the "
    "middle. One statement rests on it: S6.2 places the zero-gap cooling duty of 0.099 W cm-2 "
    "K-1 inside liquid-loop territory, i.e. it asserts a water-channel cold plate delivers it. "
    "That claim survives the whole derivable interval and does not depend on where the band was "
    "drawn: 0.099 sits below even the bottom edge, 0.13, so the cheapest cold plate in the "
    "construction still clears the duty by 1.3x, and the margin runs to 26x at the top. The "
    "conclusion is therefore insensitive to this row, unlike the forced-air band immediately "
    "above it, whose upper edge does carry a verdict.")
add("9. Thermal model", "§S6 reference lines", "none drawn", "mA cm-2", "assumption",
    "the figure drew horizontal rules at declared design currents of 50, 500 and 1000 mA cm-2 "
    "while the thermal operating point was declared. Each architecture is now judged against its "
    "own median transport ceiling, which is a different number per row, so no reference line is "
    "drawn and the row records only that the constant has left the figure", "display element", "",
    "display-only: no quantity is computed from this row, and no figure draws it.")
add("9. Thermal model", "T_amb (§S6)", "25.0", "C", "assumption",
    "standard laboratory ambient, the same 298.15 K as category 1. New row: previously "
    "unregistered as a §S6 constant", "declared modelling convention", "",
    "Tested 20-30 C: (T_b - T_amb) changes by 5/128, i.e. 4 pct for DMF, so ceilings move by about "
    "2 pct. Nothing flips.")
add("9. Thermal model", "Ea (kappa(T) Arrhenius upper bound, S6.3)", "15", "kJ mol-1", "assumption",
    "new row: previously unregistered, and it set every number in S6.3 while appearing in no table. "
    "The thermal model evaluates kappa at 25 C while predicting cells that run at 60-153 C, so its "
    "ceilings are lower bounds; S6.3 brackets that omission rather than correcting it, because no "
    "measured kappa(T) exists for any of these four compositions. The upper end of the bracket is "
    "Arrhenius scaling, kappa(T) = kappa_25 exp[(Ea/R)(1/298.15 - 1/T_b)] with Ea = 15 kJ mol-1 "
    "(EA_UPPER = 15000.0 J mol-1 in figs/analysis_kappaT_sensitivity.py, fed into the shared i_boil() "
    "of the thermal model). it is an upper bound and not A fit: Walden/Arrhenius captures only "
    "the falling viscosity, and neglects the competing rise in ion pairing as the dielectric constant "
    "falls, which is why the literature reports that single-Arrhenius forms describe organic liquid "
    "electrolytes poorly and that vft-type forms are needed. no source was located for Ea of these "
    "electrolytes; the coefficient's only external support is the water anchor in the locator column, "
    "and it is declared here as an assumption on that basis. It enters no 25 C quantity: setting "
    "Ea = 0 recovers the whole of S6.1 and S6.2 exactly",
    "-- (declared upper-bound coefficient; no page-anchored source for Ea itself). The water anchor "
    "that licenses it is measured: " + CRC, L_WATER +
    " (eta = 0.890 mPa s at 25 C and 0.282 mPa s at 100 C)",
    "anchor. Walden (kappa ~ 1/eta) on water gives eta(25 C)/eta(100 C) = 0.890/0.282 = 3.16 at "
    "100 C, against 3.37 from Arrhenius at Ea = 15 kJ mol-1 at the same point -- 6.9 pct apart. That "
    "agreement is what licenses 15 kJ mol-1 as the upper-bound coefficient rather than a fitted "
    "value; the anchor depends on temperature only, so the conductivity promotions do not touch "
    "it. Bracket. The lower bound of the bracket is kappa fixed at 25 C, i.e. the model as it stands "
    "everywhere else in S6, so this row cannot make any ceiling smaller. At the upper bound the "
    "multipliers kappa(T_b)/kappa(25 C) are a function of T_b alone -- THF 2.08x, MeCN 2.63x, "
    "aq. NaOH 3.37x, DMF 6.14x -- and the unstirred-beaker ceilings run 29 -> 42, 88 -> 140, "
    "89 -> 215 and 282 -> 478 mA cm-2. Across all %d (architecture, solvent) pairs the bracket "
    "factor spans %.2fx-%.2fx. What depends on it: %d of the %d pass/fail verdicts are unchanged "
    "between the two bounds. " % (_KT_NPAIRS, _KT["factor_range"]["min"],
                                  _KT["factor_range"]["max"],
                                  _KT_NPAIRS - len(_KT_FLIPS), _KT_NPAIRS) +
    "The %s bound-dependent verdict%s: %s. " % (_KT_WORD, "" if len(_KT_FLIPS) == 1 else "s are",
                                                _KT_FLIP_PROSE) +
    "Every one of them is reported as bound-dependent rather than as a finding. They are also very "
    "nearly the same cells the gap sweep finds conditional, which is the honest summary: "
    "the marginal cells are marginal on every axis at once, and no cell that clears comfortably at "
    "25 C is put at risk by the bracket. The "
    "DMF 6.14x is the least trustworthy entry -- a 128 K extrapolation against a 75 K anchor, in the "
    "solvent and temperature regime where the neglected pairing term is largest -- and no conclusion "
    "rests on it. MEASURED COMPARISON: the same CRC table that page-anchors mu(25 C) for these solvents also prints eta at 25/50/75 C, and the viscous activation energy it implies is 8.4 and 7.2 kJ mol-1 for MeCN (25-50 and 50-75 C), 7.7 for DMF and 7.7 for THF. Every row is accepted only if its eta(25 C) reproduces the registry viscosity, which water fails and is dropped. By Walden (Lambda eta ~ const) that is the right quantity to judge an Ea(kappa) bound against, so the declared 15 kJ mol-1 is 1.8-2.1x the measured range -- an upper bound by roughly a factor of two, rather than an unanchored guess.")
add("9. Thermal model", "U' stirred bath", "0.18", "W cm-2 K-1", "assumption",
    "RE-scoped. this row is inconsistent with the figure's own physics by elevenfold: make_figK.py "
    "computes the stirred beaker at U' = 0.0160 W cm-2 K-1, not 0.18. The two are not the same "
    "architecture -- the registry row assumes a stirred thermostat bath is the external boundary "
    "(h_ext 100-300 rather than 13 W m-2 K-1), whereas §S6 assumes still air. The row is "
    "retained only as the jacketed-glass reference case and is not the §S6 stirred beaker",
    "declared architecture (bath-jacketed glass)", "",
    "Enters no figure and no stated conclusion; retained for comparison. The adjacent SI sentence "
    "quoting stirred-liquid heat rejection near 0.1 W cm-2 K-1 is scoped to this row.")
add("9. Thermal model", "U' liquid cold plate", "0.30", "W cm-2 K-1", "derived",
    "RE-derived, and the inherited citation is broken. The registry cited 'Wallnoefer-Ogris et al., "
    "Front. Chem. Eng. 2024, 6, 1384772' for '2-6 W cm-2 rejected across 10-20 K gradients'. That "
    "volume and article number is a different paper -- Eichner, Amiri, Burheim & Lamb, '2D "
    "simulation of temperature distribution within a large-scale PEM electrolysis stack', Front. "
    "Chem. Eng. 2024, 6, 1384772 -- and it contradicts the claim: it reports heat flux into the "
    "anodic fluid of 3200-4200 W m-2, i.e. 0.32-0.42 W cm-2 at 2 A cm-2, in-cell gradients of "
    "13.6-17.1 K, and a coolant heat-transfer coefficient of 45 W m-2 K-1, implying U' of about "
    "0.026 W cm-2 K-1, an order of magnitude below the tabled 0.30. The citation was a chimera of "
    "two sources and has been withdrawn. 0.30 survives instead as the mid-laminar value of the "
    "internal-flow derivation: water with k = 0.60 W m-1 K-1, D_h = 1-3 mm and Nu = 4.36-8.23",
    INCROP, "Table 8.1 and Eq. 8.53",
    "Derived interval 0.09-0.49 W cm-2 K-1 laminar; Dittus-Boelter at Re = 3e3-3e4, Pr = 6 and "
    "D_h = 2 mm gives 0.86-5.4 W cm-2 K-1 turbulent. 0.30 is the mid-laminar value, and the "
    "conclusion it supports -- that THF's 0.099 W cm-2 K-1 duty in a stack is within cold-plate "
    "reach -- holds across the laminar interval.")
add("9. Thermal model", "Evaporative loss", "omitted", "-", "assumption",
    "omitted on both sides of the balance. Including it would delay boiling by carrying latent heat "
    "away, but evaporation is the solvent-loss failure mode the analysis is about, so omitting it "
    "is conservative for the temperature and neutral for the failure mode",
    "declared modelling choice", "",
    "Including evaporation removes latent heat, so the cell runs cooler, so it takes more current "
    "to reach Tb: every i_boil reported here is a lower bound on the true ceiling. "
    "The sign alone does not make every 'this cell boils' statement conservative. A lower bound protects the "
    "passes ('does not boil at i_design' needs i_boil > i_design, and the true ceiling is higher "
    "still), and leaves the fails exposed ('boils at i_design' needs i_boil < i_design, which a "
    "higher true ceiling can overturn). The sign alone is therefore not sufficient for the fail "
    "verdicts, and they are defended separately: "
    "(i) the zero-gap PEM stack is a closed cell with no free liquid surface, so evaporative "
    "cooling is not available to it at all and its fails -- all four electrolytes, at margins "
    "%s -- stand unaffected; "
    "(ii) the fails in open vessels are the two rotating cells (%s), and they are quantified "
    "rather than left to the sign. Taking the worst, %s at the %s: at that architecture's own "
    "transport ceiling of %.1f mA cm-2 the dissipation is %.2f W cm-2 while the passive path "
    "removes %.3f W cm-2 at T = Tb, so evaporation would have to carry %.2f W cm-2, which is "
    "%.0f pct of the total heat. A latent path asked to remove that share of the dissipation is "
    "not a correction to this balance but a different experiment, and it is the experiment the "
    "failure mode describes: what is being modelled is loss of solvent, which is reached either "
    "way. The omission is therefore neutral for these verdicts rather than conservative for them."
    % (", ".join("%.2fx" % m for _a, _s, m in _th_fails([_TH_STACK])),
       "; ".join("%s in %s at %.2fx" % (a, sl, m) for a, sl, m in _th_fails(_TH_OPEN)),
       _EVAP_W[1], _EVAP_R[0], _EVAP_R[4], _EVAP_Q, _EVAP_REJ, _EVAP_Q - _EVAP_REJ,
       100 * (_EVAP_Q - _EVAP_REJ) / _EVAP_Q))

# -- 10. Homogeneous kinetics -------------------------------------------------
add("10. Homogeneous kinetics", "8 mediated rate constants k", "(Table S6)", "M-1 s-1", "assumption",
    "order-of-magnitude values anchored to the literature of each system, two of the eight "
    "explicitly analogy-only. Retained as assumptions because none is a measurement in the "
    "exemplar's own electrolyte",
    "Table S6 per-row citations (verified against the primary sources)",
    "Table S6, k-provenance column",
    "The reaction layer x_k = sqrt(D/kC) decides whether the homogeneous step falls inside or outside "
    "the film, and enters only as sqrt(k). Measured, not argued: each k perturbed by 10x and 1/10 one "
    "row at a time with the mediated matrix re-solved moves a cell across 25 mA cm-2 on %d of the "
    "eight rows (%s), the >=25 count of any architecture by at most %d and the >=50 count by at most "
    "%d, and the architecture ordering %s. The two analogy-only rows are flagged in Table S6."
    % (len(_KS["rows_crossing_25"]), "; ".join(_KS["rows_crossing_25"]), _KS["max_count_delta_25"],
       _KS["max_count_delta_50"], "is preserved in every case" if _KS["ordering_preserved"] else "CHANGES"))

# -- 10. the catalyst rows' rate constants (2026-09-11: seven rows SOURCED, four at the floor) ----------
# Each adopted value is a measured rate constant for the step that consumes the substrate, transferred
# to the row's own ligand/solvent/substrate as a DECLARED choice (state C): the measurement is page-
# anchored, the transfer is not. The sensitivity is read from G-CATK's artifact, which pushes every
# adopted value to both edges of its measured bracket and counts what moves.
_SR = _CK.get("sourced") or {}
def _src_sens(tag_prefix):
    """publication prose for the band sensitivity of the rows carrying one basis"""
    rows = {r: v for r, v in _SR.get("per_row", {}).items() if v["basis"].startswith(tag_prefix)}
    if not rows:
        return "Sensitivity not yet computed (G-CATK sourced block absent)."
    lo, hi = next(iter(rows.values()))["band_M"]
    gains = sorted(v["gain_unstirred_to_rce"] for v in rows.values())
    gains0 = sorted(v["gain_at_k0"] for v in rows.values())
    # what the eleven-row counts do when EVERY sourced row sits at its band edge (the joint case)
    d = _SR["count_delta_at_band_edges"]
    moved = [(a, t, x[0], x[1]) for a, tt in d.items() for t, x in tt.items() if x[0] != 0 or x[1] != 0]
    mv = ("no architecture's >=25 or >=50 count moves" if not moved else
          "; ".join("%s >=%s count %+d at the low edge, %+d at the high edge" % (a, t, x0, x1) for a, t, x0, x1 in moved))
    return ("Adopted for %d row(s); measured bracket %s-%s M-1 s-1 (Table S7j). Across the seven architectures the "
            "unstirred-to-rotating-cylinder gain is %.1f-%.1fx at the adopted value against %.1f-%.1fx at k = 0. "
            "With every sourced row moved to the edges of its bracket at once, %s (the eleven-row tally, "
            "which is the whole of what the fifty-row counts can move by); the ten-of-eleven result holds at both "
            "edges: %s." % (len(rows), _ck_sci(lo), _ck_sci(hi), gains[0], gains[-1], gains0[0], gains0[-1], mv,
                            "yes" if all(_SR["ten_of_eleven_holds_at_band"]) else "NO"))
add("10. Homogeneous kinetics", "k, Ni(I)-bipyridine + aryl bromide (4 catalyst rows)", "1e2", "M-1 s-1", "assumption",
    "adopted for the Ni-XEC, aryl-amination, amination-with-NH3 and biaryl-homocoupling rows, whose "
    "substrate-consuming step is oxidative addition of an aryl bromide to Ni(I)-bipyridine; the value sits "
    "inside a measured bracket -- the isolated complex [(CO2Et-bpy)NiCl]4 + PhBr gives 7.1 +/- 0.3 in THF at "
    "26 C (3.4-56 across para substituents, Hammett rho +1.1), the amination exemplar's own voltammetry in DMF "
    "loses the Ni(II/I) return wave at 100 mV/s with 4-bromoanisole (k >~ 1e2), and pulse radiolysis of "
    "(dtbbpy)NiBr with 4-bromobenzotrifluoride bounds it below 1e4 -- and is transferred to each row's ligand, "
    "solvent and arene as a declared choice",
    "Ting, S. I.; Williams, W. L.; Doyle, A. G. J. Am. Chem. Soc. 2022, 144, 5575-5582, Fig. 6 p. 5579 "
    "(DOI 10.1021/jacs.2c00462); Kawamata, Y. et al. J. Am. Chem. Soc. 2019, 141, 6392-6402, Fig. 2B p. 6394 "
    "(DOI 10.1021/jacs.9b01886); Till, N. A.; Oh, S.; MacMillan, D. W. C.; Bird, M. J. J. Am. Chem. Soc. 2021, "
    "143, 9332-9337, p. 9334 (DOI 10.1021/jacs.1c04652)",
    "S5.7",
    _src_sens("Ni(I)bpy+ArBr"))
add("10. Homogeneous kinetics", "k, cobalt hydride + alkene (2 catalyst rows)", "7e2", "M-1 s-1", "assumption",
    "adopted for the two cobalt-electrocatalytic HAT rows (hydroamination, isomerization), whose "
    "substrate-consuming step is hydrogen-atom transfer from Co(III)-H to the alkene; the value is the "
    "finite-element fit to Co(salen) voltammetry with 4-tert-butylstyrene in DMF, and is transferred to the "
    "rows' unactivated alkenes and cathodically generated hydride as a declared choice (the hydride-formation "
    "step, rate-limiting in both cited studies, is not the model's k)",
    "Boucher, D. G.; Pendergast, A. D.; Wu, X.; Nguyen, Z. A.; Jadhav, R. G.; Lin, S.; White, H. S.; Minteer, S. D. "
    "J. Am. Chem. Soc. 2023, 145, 17665-17677, p. 17674 (DOI 10.1021/jacs.3c03815); Wilson, C. V.; Holland, P. L. "
    "J. Am. Chem. Soc. 2024, 146, 2685-2700 (DOI 10.1021/jacs.3c12329)",
    "S5.7",
    _src_sens("Co-H+alkene"))
add("10. Homogeneous kinetics", "k, Co(salen) aza-Wacker step (1 catalyst row)", "1e1", "M-1 s-1", "assumption",
    "adopted for the Co(salen) aza-Wacker cyclization row from the exemplar's own voltammetry: with the "
    "reaction's base (Na2CO3) and 10 mM substrate the Co(II)/Co(III) wave is unchanged at 100 mV/s at room "
    "temperature, which bounds the step below ~4e1 M-1 s-1 there; the synthesis runs at reflux, for which "
    "nothing is printed, so the adopted decade is a declared choice inside the room-temperature bound",
    "Cai, C.-Y.; Wu, Z.-J.; Liu, J.-Y. et al. Nat. Commun. 2021, 12, 3745, Supplementary Fig. 2 (DOI "
    "10.1038/s41467-021-24125-5)",
    "S5.7",
    _src_sens("own CV"))
add("10. Homogeneous kinetics", "k, four catalyst rows with no measured constant", "0 (floor); 1-%s swept" % _ck_sci(max(float(k) for k in _CK["k_band_M"])),
    "M-1 s-1", "assumption",
    "the Ni(tet a) macrocycle aryl-halide cyclization, the Mn-catalyzed diazidation (an azidyl-radical step), "
    "the Cu/anthraquinone photoelectrochemical cyanation (the substrate is consumed by the photoexcited "
    "quinone) and the Rh(III) C-H alkenylation carry no measured bimolecular constant for the step the model "
    "needs, so the published matrix keeps them at k = 0 -- turned over at the electrode, no regeneration inside "
    "the film, the floor of the EC' current -- and the declared band is swept instead of a value being invented",
    "Declared modelling choice; no literature k is claimed for these four rows",
    "S5.7",
    _ck_sentence())
add("4. Solver species diffusivities", "D_S, substrate (catalyst-carried rows, S5.7)", "1.0e-9 x (0.369 / mu)", "m2 s-1", "assumption",
    "a typical small-organic diffusivity in acetonitrile, scaled as 1/mu to each row's solvent "
    "(Stokes-Einstein / Wilke-Chang scaling); the eleven substrates are the papers' model substrates "
    "and are not individually structure-resolved here",
    "Declared rule; the mediated rows' eight page-anchored substrate diffusivities span 6.9e-10 to 1.9e-9 m2 s-1",
    "S5.7",
    "Enters only through the substrate cap n_S F D_S C_S/delta and the reaction layer. %d of the %d cells sit "
    "at that cap at the top of the k band, where the ceiling scales linearly with D_S: a x0.5-2 band moves "
    "those cells' ceilings by the same factor and the others not at all. The k = 0 ceilings do not depend on it; "
    "of the %d published cells carried at a sourced k, %d sit at their substrate cap."
    % (_CK["per_k"]["%g" % max(float(k) for k in _CK["k_band_M"])]["cells_at_substrate_cap"],
       _CK["per_k"]["%g" % max(float(k) for k in _CK["k_band_M"])]["cells"],
       (_CK.get("sourced") or {}).get("n_sourced", 0) * 7,
       sum(v["cells_at_substrate_cap"] for v in (_CK.get("sourced") or {}).get("per_row", {}).values())))

# -- 11. Numerical settings (declared solver choices; audited in S5.6) --------
for n_, v, meth, sens in [
 ("Film nodes N (Stage-1 / EC')", "80 / 90", "finite-volume mesh resolution",
  "Mesh independence verified: at most 1 pct drift over N = 40-160 (\u00a7S5.6)."),
 ("First cell dx1", "max(0.02 um, min(x_k/50, 0.9 delta/N))",
  "first-cell size matched to the reaction layer x_k",
  "Introduced to remove a hyper-stretched-mesh stall; the affected binary comparison now converges to "
  "within 0.2 pct of the analytic ceiling (\u00a7S5.6)."),
 ("Residual scale c_ref (per species)", "max(c_bulk, 0.01 c_max,bulk, max_x c)",
  "reference concentration in the flux D c_ref/delta that each conservation residual is divided by "
  "before the ||F||_inf test, in both solvers (the verification solver of \u00a7S5.3 and \u00a7S5.6, and "
  "the production solver, which carries Stage 1 at k = 0 and Stage 2); the last term is the "
  "species' largest concentration in the current "
  "iterate, so an electrogenerated species that is a trace in the bulk but molar at the electrode "
  "is held to the same relative tolerance as the rest",
  "Perturbation: c_ref = max(c_bulk, 0.01 c_max,bulk) alone. The chloride ex-cell system's oxidant "
  "(%.2g mol m-3 in the bulk, %.1f M at its carrier limit) is then normalised by a reference flux "
  "%.1e times smaller than its in-film concentration implies, so the 1e-9 tolerance asks for a "
  "relative accuracy of %.1e on that row, and the concentration-control walk stops on an existing branch at "
  "52 pct of the analytic carrier limit on a 200 um film and 86 pct on 100 um, reaching it only on "
  "films of 50 um or less; the stop moves with nothing else (reaction off, substrate removed, mesh "
  "refined at either edge, proton mobility halved). With the in-film maximum included every film "
  "reaches 2.00x Fick, and the 48 production cells move by less than 1e-4 pct (33 bit-identical), "
  "because their oxidized mediators never exceed a few hundred mol m-3, and the 300 cells of the "
  "Stage-1 layer, re-solved in an isolated copy under the alternative scale, are bit-identical at "
  "the published precision. The verification solver of \u00a7S5.3 and \u00a7S5.6 uses the same rule; "
  "under its own alternative, max(c_bulk, 1 mol m-3), every closed-form agreement of \u00a7S5.6 is "
  "identical, the \u00a7S5.3 support-ratio sweep is byte-identical, and the illustrative "
  "concentration profiles move by at most 4e-6 relative."
  % (_EX["inputs"]["c_OX_bulk_molm3"], _EX["c_OX_at_limit_M"],
     _EX["c_OX_at_limit_M"] * 1000 / _EX["inputs"]["c_OX_bulk_molm3"],
     1e-9 / (_EX["c_OX_at_limit_M"] * 1000 / _EX["inputs"]["c_OX_bulk_molm3"]))),
 ("Newton tolerance ||F||_inf", "1e-9", "row-scaled residual convergence criterion",
  "Tightening below 1e-9 changes no reported digit; the discrete charge-conservation check passes "
  "at 3e-12."),
 ("Log-step clamp", "2.0-3.0", "positivity-preserving damped-Newton step limit",
  "Affects iteration count, not the converged solution."),
 ("Collapse threshold c_surf/c_bulk", "1e-3",
  "definition of surface depletion for electroactive species only; the crossing is bisected rather "
  "than quantized by the ramp",
  "Tested 1e-2 to 1e-4: i_lim moves by under 1 pct because the concentration profile is "
  "near-vertical at collapse."),
 ("Galvanostatic ramp growth", "1.08-1.15", "warm-started continuation step",
  "The ramp only supplies a warm start: the reported value comes from concentration control, "
  "which reaches the collapse criterion rather than stalling at the ramp's fold, so the growth "
  "factor sets how quickly that start is found and not the answer. Doubling the mesh while "
  "refining the continuation 7.5-fold moves it by at most 0.01 pct (\u00a7S5.6)."),
 ("FD Jacobian step", "1e-7 x max(|u|,1)", "dense forward-difference Jacobian on log DOFs",
  "The step enters the JACOBIAN, which chooses the Newton direction; it does not enter the "
  "RESIDUAL, which defines the solution. Convergence is declared on ||F||_inf < 1e-9 evaluated "
  "exactly, so a badly chosen h costs iterations or, at worst, convergence -- it cannot move "
  "the converged answer, which satisfies the same residual test either way. The value is the "
  "standard forward-difference optimum for double precision, h ~ sqrt(eps) ~ 1.5e-8, where "
  "truncation error growing as h balances round-off growing as eps/h; the total error is flat "
  "to within an order of magnitude either side. Every check passes against closed-form "
  "limits at this setting."),
 ("Trust-region negligibility NEGLIGIBLE_C", "1e-10",
  "species below this fraction of their own bulk value are excluded from the Newton step-limiting "
  "norm and clamped individually instead (limit_step! In npp_ecprime.jl). Introduced 2026-08-24: "
  "rescaling the whole step by its largest component let a substrate at ~1e-22 of bulk, in a dead "
  "zone where it reacts with nothing, return Newton components of 1e9-1e12 and throttle the entire "
  "step by ~1e-12, so the boundary constraint could not move at all. Where no species is below the "
  "threshold the rule is identical to the old one",
  "Swept over ten decades, 1e-6 to 1e-16, re-solving four cells (the two the change moved and two "
  "it must not): every value identical to 6 decimal places at every threshold. RDE and RCE, which "
  "never drive a species below 1e-3 of bulk, additionally return their pre-change values exactly. "
  "See \u00a7S5.5."),
]:
    add("11. Numerics", n_, v, "-", "assumption",
        meth + ". A declared solver setting with no physical content",
        "Declared numerical setting; verified against the analytic limits of \u00a7S5.6", "", sens)

# -- emit ---------------------------------------------------------------------
FIELDS = ["category","parameter","value","units","provenance_class","method_note","citation",
          "locator","sensitivity", "equation"]
with open(OUT_REGISTRY,"w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for r in R: w.writerow(r)

from collections import Counter
print(f"{len(R)} parameters registered")
print(Counter(r['provenance_class'] for r in R))
print("--- per category ---")
cats = []
for r in R:
    if r['category'] not in cats: cats.append(r['category'])
for cat in cats:
    cc = Counter(r['provenance_class'] for r in R if r['category'] == cat)
    n = sum(cc.values())
    print(f"{cat:32s} n={n:4d}  measured={cc['measured']:4d}  derived={cc['derived']:4d}  "
          f"assumption={cc['assumption']:4d}")
missing_loc = [r['parameter'] for r in R if r['provenance_class'] == "measured" and not r['locator']]
missing_sen = [r['parameter'] for r in R if r['provenance_class'] == "assumption" and not r['sensitivity']]
assert not missing_loc, missing_loc
assert not missing_sen, missing_sen
print("schema check: every measured row carries a locator; every assumption row carries a sensitivity.")
