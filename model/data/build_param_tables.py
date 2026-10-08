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
import re
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
# G-THERMAXIS: the cooling class of every verdict along the stack gap, the stack current, the inherited sigma and the charge
with io.open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "results", "thermal_axis_sweeps.json"),
             encoding="utf8") as _fh:
    _TAX = _json.load(_fh)
_NICE_S = {"THF": "tetrahydrofuran", "MeCN": "acetonitrile", "DMF": "dimethylformamide", "aq. NaOH": "aqueous NaOH"}
_ARCH_S = lambda a: ("rotating disc" if a.startswith("RDE") else "rotating cylinder" if "cyl" in a
                     else "zero-gap stack" if "stack" in a else a)


_KT_SIG_SAME = (sorted((f["reactor"], f["solvent"]) for f in _json.load(io.open(_os.path.join(_os.path.dirname(_os.path.dirname(
    _os.path.abspath(__file__))), "results", "figK_kappaT_sensitivity.json"), encoding="utf-8"))["verdict_flips"])
                == sorted((c["arch"], c["solvent"]) for c in _TG["conditional_on_sigma"]))
_TG_ROW = lambda arch, solv: [r for r in _TG["rows"] if r["arch"] == arch and r["solvent"] == solv][0]
assert sorted((c["arch"], c["solvent"]) for c in _TG_COND) == [("RDE 1600 rpm", "DMF"), ("RDE 1600 rpm", "MeCN")], _TG_COND
import math as _m_tg
_TG_CSIG = _TG["conditional_on_sigma"]
_TG_ROWS = _TG["rows"]
import sys as _sys_tg
_sys_tg.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "figs"))
import thermal_model as _TM_TG
_LOB_A = (2 * (2 * 2.2) + 2 * (2 * 0.96) + 2 * (2.2 * 0.96)) * 6.4516   # Lobaccaro 2016 Fig. 1, cell B, end plates excluded (cm2 per cm2)
_TG_SIGMA_B = _TM_TG.SIGMA_BEAKER
# the architectures that INHERIT the beaker sigma (every reactor at the beaker value except the two beakers themselves),
# named as G-THERMGEO's artifact names them
_TG_INH = [r["arch"] for r in _TG_ROWS if r["solvent"] == "THF"
           and not r["arch"].endswith("batch")
           and any(abs(rx[2] - _TG_SIGMA_B) < 1e-12 and rx[0].replace("\n", " ").replace("$\\mu$", "u").split()[0] == r["arch"].split()[0]
                   for rx in _TM_TG.REACTORS)]
_TG_SENS_SIGMA = (
    "Swept as a breaking point rather than as a band, because no source states the "
    "heat-rejection area of these cells. sigma is the OTHER unsourced geometric term, and it is "
    "the tighter of the two: %d passive-cooling verdicts reverse within a factor of 2.5 of the declared value "
    "(%s). "
    "A cell with twice the outer surface per unit of electrode area is an ordinary "
    "variation, so these are published as conditional on the declared geometry rather than "
    "as findings. Among the %s architectures this row covers, everything that CLEARS needs sigma to fall by a factor "
    "of %.1f to %.0f before it would boil, and the tetrahydrofuran failure at the rotating cylinder needs a factor of %.0f, "
    "so the robust half of the section is robust on this axis too. One of the %s has external corroboration, and it runs in the safe direction: the parallel H-cell of Table S1 is a modification of the cell of Lobaccaro, Singh, Clark, Kwon, Bell & Ager (Watkins et al., ACS Energy Lett. 2023, SI Fig. S1c), whose two polycarbonate compartments are drawn 2 x 2.2 in and 0.48 in thick around a 1 cm2 cathode (Phys. Chem. Chem. Phys. 2016, 18, 26777-26785, Fig. 1, p. 26778); the two compartments alone present %.0f cm2 of outer surface over 1 cm2 of electrode, i.e. sigma ~ %.0f against the %.2f this model carries. The value used here is therefore conservative for that cell by a factor of about %.0f, and adopting the sourced one would only widen a margin that already clears. It is NOT adopted, because one exemplar body is not the archetype, the modified cell's own dimensions are not published, and that body is polycarbonate, whose wall conduction the balance omits (see the wall-conduction row). The other two architectures on this value have no published body geometry at all, so they keep the beaker value."
    % (len(_TG_CSIG),
       "; ".join("%s in %s at %.2fx" % (c["arch"], c["solvent"], c["flips_at_sigma_x"])
                 for c in _TG_CSIG),
       {2: "two", 3: "three", 4: "four"}.get(len(_TG_INH), str(len(_TG_INH))),
       min(1.0/r["sigma_flip_x"] for r in _TG_ROWS if r["verdict"] == "survives" and r["sigma_flip_x"] and r["arch"] in _TG_INH),
       max(1.0/r["sigma_flip_x"] for r in _TG_ROWS if r["verdict"] == "survives" and r["sigma_flip_x"] and r["arch"] in _TG_INH),
       [r["sigma_flip_x"] for r in _TG_ROWS if r["arch"].startswith("rotating cyl") and r["solvent"] == "THF"][0],
       {2: "two", 3: "three", 4: "four"}.get(len(_TG_INH), str(len(_TG_INH))), _LOB_A, _LOB_A, _TG_SIGMA_B, _LOB_A / _TG_SIGMA_B))
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


# The beaker cell voltage at 50 mA cm-2 is linear in 1/kappa (thermal_model.E_cell), so the conductivities at which it
# leaves the 10-20 V band are closed-form: kappa = i L / (V - E_cell(i, kappa -> infinity)).
_V_FLOOR = _TM.E_cell(50.0, 1e30, _TM.GAP_BEAKER)
_V_KLO = 50.0 * 10.0 * _TM.GAP_BEAKER / (20.0 - _V_FLOOR)     # S/m at 20 V
_V_KHI = 50.0 * 10.0 * _TM.GAP_BEAKER / (10.0 - _V_FLOOR)     # S/m at 10 V
_TH_DMF_TB = [r[3] for r in _TM.SOLVENTS if r[0] == "DMF"][0]


def _th_ceiling(kap, tb, r):
    return _TM.i_boil(kap, r[1], tb, _TM.U_passive(r[2], r[3]))


def _th_ceiling_h(kap, tb, gap, sig, hint, hext):
    """Boil-off ceiling with an explicit external film (the emissivity sweep); thermal_model.i_boil with U' rebuilt."""
    return _TM.i_boil(kap, gap, tb, (1.0 / (1.0 / hint + 1.0 / hext)) * sig * 1e-4)


def _vessel_sigma(d_m, v_m3=None):
    """sigma of a right-cylinder vessel of inside diameter d holding the archetype's charge: wetted wall + base over the
    declared electrode area (the construction of thermal_model.A_EXT_BEAKER, at another diameter)."""
    v = _TM.CELL_VOLUME_M3 if v_m3 is None else v_m3
    r = d_m / 2.0
    h = v / (_math.pi * r ** 2)
    return (_math.pi * d_m * h + _math.pi * r ** 2) / _TM.A_ELEC_M2


def _h_rad(eps, ts_c=65.0, tsur=298.15):
    """Linearised radiative coefficient eps sigma_SB (Ts + Tsur)(Ts^2 + Tsur^2), W m-2 K-1."""
    ts = ts_c + 273.15
    return eps * 5.670374419e-8 * (ts + tsur) * (ts ** 2 + tsur ** 2)


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


# chemistry audit pass 7: the DMF conductivity's attenuation, read from Dorn's measured NaI/methanol isotherm (Table SI 97)
# at the molality that 0.2 M corresponds to. That conversion needs the solution density; with the apparent molar volume of
# NaI anywhere in 0-35 cm3 mol-1 the molality is 0.254-0.256 mol kg-1. The earlier 0.539 took the solution density as the
# pure solvent's (molality 0.264), which no physical apparent volume gives.
def _nai_attenuation():
    here = _os.path.dirname(_os.path.abspath(__file__))
    with io.open(_os.path.join(here, "dorn_isotherms.csv"), encoding="utf8") as fh:
        pts = sorted((float(r["m_mol_kg"]), float(r["kappa_mScm"])) for r in csv.DictReader(fh) if r["system"] == "NaI/MeOH")
    with io.open(_os.path.join(here, "solvents.csv"), encoding="utf8") as fh:
        rho0 = float([r for r in csv.DictReader(fh) if r["solvent"] == "MeOH"][0]["rho"])
    c, L0 = 0.2, 45.23 + 62.63
    def at(vphi):
        m = c / (rho0 * (1.0 - c * vphi))
        lo = max(p for p in pts if p[0] <= m); hi = min(p for p in pts if p[0] >= m)
        k = lo[1] + (hi[1] - lo[1]) * (m - lo[0]) / (hi[0] - lo[0])
        return m, k / c / L0
    (m0, r0), (m1, r1) = at(0.0), at(0.035)
    r = 0.5 * (r0 + r1)
    return {"m_lo": m0, "m_hi": m1, "r_lo": r0, "r_hi": r1, "r": r, "k": round(0.2 * 81.35 * r, 2), "rho0": rho0}
_NAI = _nai_attenuation()
_NAI_K, _NAI_S = _NAI["k"], _NAI["k"] / 10.0
with io.open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "electrolytes.csv"), encoding="utf8") as _fh:
    _nai_carried = float([r for r in csv.DictReader(_fh) if r["electrolyte"] == "0.2 M NaI/DMF"][0]["kappa_mScm"])
if abs(_nai_carried - _NAI_K) > 0.006:
    raise SystemExit("0.2 M NaI/DMF: electrolytes.csv carries %.2f, the derivation gives %.2f" % (_nai_carried, _NAI_K))


def _dmf_tss():
    """Passive steady state of the DMF beaker worked example at 100 mA cm-2. Typed as 187 C until
    2026-09-13; it moves with sigma, and the derived sigma raised it to 228 C."""
    b = _TH_RX[0]
    return _TM.T_ss(100.0, _NAI_S, b[1], _TM.U_passive(b[2], b[3]))


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


_DMF_FAILS = sorted([(r[0], _th_margin(_NAI_S, 152.8, r), _kappa_multiple(_NAI_S, 152.8, r[0]))
                     for r in _TH_RX if r is not _TH_STACK and _th_margin(_NAI_S, 152.8, r) < 1.0],
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
            "electrode separation: %s of the %d architecture-solvent cells reverse their verdict "
            "within a factor of %.1f of a gap they inherit or declare from this one (%s). Those two verdicts are therefore "
            "conditional on the gap. The tetrahydrofuran boil-off verdicts at the rotating disc and cylinder need gaps below about "
            "%.1f and %.1f mm to reverse, which is no longer a "
            "beaker-scale cell, and the %d architectures sharing this gap (%s) hold boil-off "
            "ceilings whose lowest sits within %.1f pct of the highest in each electrolyte, while their transport ceilings span %.1fx."
            % ({1: "one", 2: "two", 3: "three", 4: "four"}.get(len(_TG_COND), str(len(_TG_COND))), _TH_NCELL, 2.5,
               "; ".join("%s in %s at %.2fx" % (c["arch"], c["solvent"], c["flips_at_gap_x"])
                         for c in _TG_COND),
               _TG_ROW("RDE 1600 rpm", "THF")["gap_flip_m"] * 1e3, _TG_ROW("rotating cyl. 3000 rpm", "THF")["gap_flip_m"] * 1e3,
               len(_TG["shared_gap_rows"]), ", ".join(_TG["shared_gap_rows"]),
               _m_tg.ceil(1000 * _TG["ceiling_spread_on_shared_gap"]) / 10, _TG["transport_span_on_shared_gap"]))   # a "within" bound rounds up
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
# chemistry audit pass 4: "10 of the 12 clearing 25 mA cm-2 are concentrated rows" was typed; read it from G-DILUTE's artifact
with io.open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "results", "dilute_theory_stratify.json"), encoding="utf8") as _fh2:
    _DS_STRATA = _json.load(_fh2)["strata"]
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
_NUMW = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
_numword = lambda n: _NUMW[n] if 0 <= n <= 20 else str(n)

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
# How many rows each carrier class holds, read from the reaction table rather than typed. "the eight
# mediated rows" and "the eleven catalyst rows" were literals in a dozen sentences that ship into
# Table S7; the 2026-10-05 audit re-typed five rows and every one of them would have gone stale.
_HERE_D = _os.path.dirname(_os.path.abspath(__file__))
with io.open(_os.path.join(_HERE_D, "reactions_50.csv"), encoding="utf8") as _fh:
    _RX50 = list(_csv.DictReader(_fh))
_N_MED = sum(r["carrier_type"] == "mediator" for r in _RX50)
_N_CAT = sum(r["carrier_type"] == "catalyst" for r in _RX50)
_N_DIR = sum(r["carrier_type"] == "substrate" for r in _RX50)
assert _N_MED + _N_CAT + _N_DIR == 50, "carrier types do not partition the fifty rows"
_ALLBUT1 = "%s-of-%s" % (_numword(_N_CAT - 1), _numword(_N_CAT))
with io.open(_os.path.join(_HERE_D, "catalyst_substrates.csv"), encoding="utf8") as _fh:
    _CSUB = list(_csv.DictReader(_fh))
with io.open(_os.path.join(_HERE_D, "mediated_substrates.csv"), encoding="utf8") as _fh:
    _MSUB = list(_csv.DictReader(_fh))
with io.open(_os.path.join(_HERE_D, "reaction_stoichiometry.csv"), encoding="utf8") as _fh:
    _STOI = list(_csv.DictReader(_fh))
assert len(_CSUB) == _N_CAT and len(_MSUB) == _N_MED and len(_STOI) == 50
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
        return ("At the sourced rate constants (S5.7) the " + _ALLBUT1 + " count is conditional on this radius: it breaks at "
                "r_h = %.2f Angstrom on the deciding row (%s, %.1f mA cm-2 at best), %s the assigned band and above the "
                "%.2f Angstrom that size-scaling the ferrocene anchor predicts; the 1/r scaling is the k = 0 law and a bound "
                "for the sourced rows, whose kinetic-regime ceiling goes as sqrt(D) and breaks at %.2f Angstrom%s. The carrier "
                "dichotomy -- the central mechanistic result -- is unaffected."
                % (_CD["r_crit_from_4p5A"], _CD["deciding_row"].split(" (")[0], _CD["second_best_i_lim"],
                   "inside" if _CD.get("in_band") else "below",
                   _CD["r_expected_deciding_A"], _CD["r_crit_sqrt_from_4p5A"],
                   "" if _CD.get("conditional_under_sqrt_law") else ", below that prediction"))
    # chemistry review 2026-10-06: this branch said "All N ... sit below 25" whatever n_clear was, and once the homocoupling
    # cleared 25 and the Co-H row fell (alprenolol at 0.04 M) the sentence contradicted Section 4. It reads n_clear now.
    if _CD.get("n_clear", 0) == 0:
        return ("All " + _numword(_N_CAT) + " catalyst-carried entries sit below 25 mA cm-2 in every architecture across the whole "
                "band; the count breaks only at r_h = %.2f Angstrom, below the %.2f Angstrom expected for the deciding row. The "
                "carrier dichotomy -- the central mechanistic result -- is unaffected." % (_CD["r_crit_from_4p5A"], _CD["r_expected_deciding_A"]))
    if _CD["n_clear"] != 1:
        raise SystemExit("the radius sentence names the %s count; G-CATD reports %d catalyst rows clearing 25" % (_ALLBUT1, _CD["n_clear"]))
    return ("The " + _ALLBUT1 + " count holds across the whole band: no further catalyst-carried entry reaches 25 mA cm-2 in any "
            "architecture until r_h = %.2f Angstrom on the deciding row (%s, %.1f mA cm-2 at best), below the %.2f Angstrom expected "
            "for it. The carrier dichotomy -- the central mechanistic result -- is unaffected."
            % (_CD["r_crit_from_4p5A"], _CD["deciding_row"].split(" (")[0], _CD["second_best_i_lim"], _CD["r_expected_deciding_A"]))


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
        core = ("at most one row clears 25 mA cm-2 in any architecture for k <= %s M-1 s-1 and more than one does "
                "from k = %s; by k = %s, %d of the %s clear it" % (_ck_sci(hold), _ck_sci(fail), _ck_sci(kmax),
                                                                top["clear25"], _numword(_N_CAT)))
    ctrl = ("better than 0.01" if abs(_CK["control"]["worst_rel"]) < 1e-4
            else "%.2f" % (100 * abs(_CK["control"]["worst_rel"])))
    return ("With all " + _numword(_N_CAT) + " catalyst-carried rows held at k = 0, the floor of the EC' current, and then "
            "re-solved as EC' problems over the declared band, %s; the largest amplification in the class is "
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
    parts = ["at x%.2f the >=%d mA cm-2 count of the %s falls from %d to %d of the %s mediated rows"
             % (float(sc), thr, arch, b, a, _numword(_N_MED)) if a < b else
             "at x%.2f the >=%d mA cm-2 count of the %s rises from %d to %d of the %s mediated rows"
             % (float(sc), thr, arch, b, a, _numword(_N_MED))
             for sc, arch, thr, b, a in moves]
    txt = "; ".join(parts)
    if quiet:
        txt += ", and nothing moves at x%s" % ", x".join("%.2f" % sc for sc in sorted(quiet))
    txt += ". No count moves by more than %d entr%s of %s" % (worst, "y" if worst == 1 else "ies", _numword(_N_MED))
    return txt, worst
_SB_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "results", "si_sensitivity_bounds.json")
with io.open(_SB_PATH, encoding="utf8") as _fh:
    _SB = _json.load(_fh)["transport"]   # G-SIBOUNDS: what each film's band does to its column
if "status" in _SB:
    raise SystemExit("results/si_sensitivity_bounds.json has no transport bounds (%s); the flow-film "
                     "rows interpolate theirs from it -- run the band-edge solves and "
                     "data/si_sensitivity_bounds.py first" % _SB["status"])
def _rot_band():
    """The RDE and RCE rpm bands of Table S8, read from julia/emit_deltas.jl rather than typed."""
    src = io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "emit_deltas.jl"), encoding="utf8").read()
    rde = sorted(float(x) for x in re.findall(r"delta_rde\(D, nu; rpm = ([0-9.]+)\)", src))
    rce = sorted(float(x) for x in re.findall(r"km_rce\(D, nu; d = [0-9.]+, rpm = ([0-9.]+)\)", src))
    if len(rde) != 2 or len(rce) != 2:
        raise SystemExit("could not read the rotating-electrode bands from julia/emit_deltas.jl")
    return rde, rce
_RDE_BAND, _RCE_BAND = _rot_band()


def _sbrow(key):
    """What a film's band does to its column, in the SI's own display convention (>= 100 mA cm-2 as a
    whole number, below that to one decimal); a band that collapses onto the value is said to."""
    m = _SB["median, " + key]; a = _SB["count >=25, " + key]; b = _SB["count >=50, " + key]
    f = lambda v: ("%.0f" % v) if v >= 100 else ("%.1f" % v)
    if f(m["lower"]) == f(m["upper"]) and a["lower"] == a["upper"] and b["lower"] == b["upper"]:
        return ("a column that does not move: a median of %s mA cm-2, %d of 50 clearing 25 mA cm-2 and %d of 50 "
                "clearing 50 at both ends" % (f(m["value"]), a["value"], b["value"]))
    rng = lambda c: ("%d-%d of 50 (about %d)" % (c["lower"], c["upper"], c["value"])) if c["lower"] != c["upper"] else "%d of 50 throughout" % c["value"]
    return ("a median of %s-%s mA cm-2 about %s, %s clearing 25 mA cm-2 and %s clearing 50"
            % (f(m["lower"]), f(m["upper"]), f(m["value"]), rng(a), rng(b)))
_FCS = _FC["sensitivity_um"]
_FC_ENV_LO = _FCS["h_5mm"] * _FCS["drho_1e-2"] / _FC["delta_centre_um"]
_FC_ENV_HI = _FCS["h_80mm"] * _FCS["drho_1e-3"] / _FC["delta_centre_um"]
# chemistry audit, pass 4: these sensitivities read the published matrix and the sweep artifacts rather than quoting
# numbers from a retired matrix (they had: an eight-row, six-archetype mediated matrix and a 300 um unstirred film).
import statistics as _st
_ROOT_P4 = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
def _pub_col(a):
    with io.open(_os.path.join(_ROOT_P4, "julia", "tier0_ec_matrix.csv"), encoding="utf8") as fh:
        return [float(r[a]) for r in csv.DictReader(fh)]
with io.open(_os.path.join(_ROOT_P4, "julia", "mediated_ec_matrix.csv"), encoding="utf8") as _fh:
    _NAT_FILM = sorted({float(r["delta_um"]) for r in csv.DictReader(_fh) if r["reactor"] == "Unstirred batch"})
assert len(_NAT_FILM) == 1, _NAT_FILM
_NAT_FILM = _NAT_FILM[0]
def _nat_at(d):
    """Unstirred median and counts with the column scaled as 1/delta: exact for the direct and k = 0 rows, and a bound on
    the mediated and catalyst rows, none of which falls faster than 1/delta (Table S6 slopes)."""
    v = [x * _NAT_FILM / d for x in _pub_col("natural")]
    return _st.median(v), sum(x >= 25 for x in v), sum(x >= 50 for x in v)
with io.open(_os.path.join(_ROOT_P4, "results", "solver_species_2xD.json"), encoding="utf8") as _fh:
    _S2X = _json.load(_fh)
_S2H = _S2X.get("homogeneous_partners")
if not _S2H:
    raise SystemExit("results/solver_species_2xD.json carries no homogeneous_partners key; run "
                     "data/sensitivity_solver_species_2xD.py --group homog")
# The analytic-limit checks of julia/run_audit.jl, read from its artifact rather than typed (chemistry audit, pass 5).
with io.open(_os.path.join(_ROOT_P4, "julia", "audit_gates.csv"), encoding="utf8") as _fh:
    _AG = list(csv.DictReader(_fh))
_AG_G2 = abs(float(next(r for r in _AG if r["gate"] == "G2")["err_pct"]))
_AG_G8A = abs(float(next(r for r in _AG if r["gate"] == "G8a")["err_pct"]))
_AG_G11 = float(re.search(r"=\s*([0-9.eE+-]+)%", next(r for r in _AG if r["gate"] == "G11")["note"]).group(1)) / 100.0
_AG_G12 = max(abs(float(r["err_pct"])) for r in _AG if r["gate"] == "G12")
_AG_BIN = "reproduced to %.2f pct and %.2f pct" % (_AG_G2, _AG_G8A)
_AG_CC = "%.0e" % _AG_G11
with io.open(_os.path.join(_ROOT_P4, "results", "medium_transfer_brackets.json"), encoding="utf8") as _fh:
    _MXF = _json.load(_fh)
def _mxf(case):
    c = _MXF["cases"][case]
    mv = "; ".join("the %s >=%d mA cm-2 count %d -> %d" % (m["arch"], m["threshold"], m["from"], m["to"]) for m in c["count_moves"])
    return c, (mv or "no threshold count"), ("no architecture median" if not c["median_moves"] else "the median of " + ", ".join(m["arch"] for m in c["median_moves"]))
with io.open(_os.path.join(_ROOT_P4, "data", "reactions_50.csv"), encoding="utf8") as _fh:
    _DMED = _st.median(float(r["D_cm2s"]) for r in csv.DictReader(_fh))
_FC_COUNTS_SENT = (" Across the envelope this point spans (the derived film above), the unstirred threshold counts run "
                   "from at least %d to at most %d (>=25 mA cm-2) and from at least %d to at most %d (>=50), so those two "
                   "counts are conditional on the declared point; the three thin-film architectures clear 50 mA cm-2 for "
                   "%s of 50, several times more at either edge."
                   % (_nat_at(_FC_ENV_HI)[1], _nat_at(_FC_ENV_LO)[1], _nat_at(_FC_ENV_HI)[2], _nat_at(_FC_ENV_LO)[2],
                      "-".join(sorted({"%d" % sum(x >= 50 for x in _pub_col(a)) for a in ("micro", "rde", "rce")}))))
def _trace_sentence():
    """The trace-seed sweep, read from G-TRACE's artifact (it was typed against the retired 48-cell matrix)."""
    with io.open(_os.path.join(_ROOT_P4, "results", "trace_init_sensitivity.json"), encoding="utf8") as fh:
        t = _json.load(fh)
    hi, lo = t["per_seed"]["1e-4"], t["per_seed"]["1e-6"]
    assert not t["counts_move"], "the trace seed moves a mediated count; the registry row must say so"
    scales = lo["max_abs_mAcm2"] > 0 and 5 <= hi["max_abs_mAcm2"] / lo["max_abs_mAcm2"] <= 20
    return ("tr(C) was moved a full decade in both directions, 1e-5 -> 1e-4 and 1e-5 -> 1e-6, and every mediated row "
            "re-solved in an isolated copy each time. The seed is not exactly inert: %d of the %d (reaction, reactor) "
            "entries change at 1e-4 and %d at 1e-6, by at most %.2g mA cm-2 and %.2g mA cm-2 respectively (%.2g pct and "
            "%.2g pct)%s. The counts clearing 25 and 50 mA cm-2 among the mediated entries stay at %d and %d at both ends, "
            "so no reported quantity depends on the seed."
            % (hi["n_differ"], t["n_cells"], lo["n_differ"], hi["max_abs_mAcm2"], lo["max_abs_mAcm2"], hi["max_rel_pct"],
               lo["max_rel_pct"], ", scaling with the seed as a perturbation should" if scales else "",
               hi["counts"]["25"][0], hi["counts"]["50"][0]))
_O2R = 2.10e-5 / _DMED          # O2 in water, Cussler Table 5.2-1 p. 127, against the median carrier diffusivity
assert _O2R > 1, "O2 no longer diffuses faster than the median carrier; the stirred-row direction claim fails"
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
           "1987")
L_PG    = "Eq. 11-12.4, p. 618 (Perkins-Geankoplis mole-fraction mixing rule for phi*M)"
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
                 "DMSO/THF 5:1 v/v","tAmOH/H2O 3:1 v/v","AcOH/HCOOH 1:1 v/v",
                 # chemistry review 2026-10-06: three mixtures the solver reads from solvents.csv had no registry row
                 "EtOH/MeOH 1:1 v/v","THF/MeOH 5:1 v/v","THF/EtOH 1:1 v/v",
                 # chemistry audit 2026-10-06: the bromination row's H-cell medium
                 "H2O/MeCN 1:1 v/v"}

S_MU = ("i_lim ~ D ~ 1/mu and Sc = nu/D, so mu enters twice; a +/-25 pct property error displaces "
        "log10 i_lim by +/-0.10 (Eq. S1 is linear in D). That is small against the 1-2 order-of-"
        "magnitude spreads separating the " + _numword(_N_ARCH) + " reactor archetypes, so no architecture ranking or "
        "carrier-class conclusion can move; only per-reaction entries already within ~25 pct of a "
        "threshold can cross it.")
S_RHO = ("rho enters only through nu = mu/rho, and only in the two rotating correlations: k_m ~ "
         "nu^-1/6 at the RDE (Levich) and nu^-0.344 at the rotating cylinder (Re^0.70 Sc^0.356), so a "
         "5 pct rho error moves k_m by 0.8 and 1.7 pct and leaves the five fixed films untouched.")

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
import math as _math_dma
with io.open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "julia",
                           "catalyst_ec_sourced.csv"), encoding="utf8") as _fh:
    _DMA_K = {r["reaction"]: float(r["k_M"]) for r in csv.DictReader(_fh) if float(r["k_M"]) > 0}
def _dma_moves_sentence():
    """G-DMAMU's result, read from its artifact. Every DMA cell is RE-SOLVED at each swept viscosity
    (data/dma_viscosity_ecprime.jl): a cell carried at a finite rate constant sits on or near the kinetic plateau,
    which goes as D^(1/2), so the transport exponent mu^p would overstate it (chemistry audit, pass 6)."""
    if not _DMA:
        return "The sweep artifact is absent; run data/sensitivity_dma_viscosity.py."
    if "dma_cells" not in _DMA["swept"][0]:
        raise SystemExit("results/dma_viscosity_sensitivity.json predates the re-solved sweep; re-run "
                         "data/sensitivity_dma_viscosity.py")
    sw = sorted(_DMA["swept"], key=lambda r: -r["mu"])
    top, bot = sw[0], sw[-1]
    rows = _DMA["dma_rows"]
    ncat = _DMA["n_catalyst_rows"]
    lr = _math_dma.log(bot["mu"] / top["mu"])
    parts = []
    for rxn in sorted(rows, key=lambda x: max(top["dma_cells"][x].values())):
        c0, c1 = top["dma_cells"][rxn], bot["dma_cells"][rxn]
        p = {a: _math_dma.log(c1[a] / c0[a]) / lr for a in c0}
        pmin, pmax = min(p.values()), max(p.values())
        lo_a = ", ".join(_ARCHW[a] for a in p if abs(p[a] - pmin) < 5e-3)
        hi_a = ", ".join(_ARCHW[a] for a in p if abs(p[a] - pmax) < 5e-3)
        kval = _DMA_K.get(rxn, 0.0)
        parts.append("the %s, carried at %s, runs %.2f-%.2f mA cm-2 at the printed value and %.2f-%.2f at %.3f mPa s, an "
                     "effective exponent d ln i_lim / d ln mu of %.2f (%s) to %.2f (%s)"
                     % (rxn.split(" (")[0], "the floor k = 0" if kval == 0 else
                        "its sourced rate constant k = %g M-1 s-1 (S5.7)" % kval,
                        min(c0.values()), max(c0.values()), min(c1.values()), max(c1.values()), bot["mu"],
                        pmin, lo_a, pmax, hi_a))
    txt = ("Exposure is bounded by direct test: both DMA reactions are re-solved at %s mPa s, with the carrier, product "
           "and substrate diffusivities scaled as 1/mu, the kinematic viscosity as mu, and the supporting-ion "
           "diffusivities and rate constant held. Across that interval %s. A cell carried at a finite rate constant "
           "approaches the kinetic plateau n F C_cat (D k C_S)^(1/2) in the thin films, which is why its exponent "
           "approaches -1/2 there rather than the -1 of a transport-limited cell. "
           % (", ".join("%.3f" % r["mu"] for r in sw), "; ".join(parts)))
    mv = _DMA.get("count_moves", [])
    if not mv and not _DMA.get("catalyst_clearing_moves_at"):
        txt += ("No >=25 or >=50 threshold count moves anywhere in %.3f-%.3f mPa s, and the number of catalyst-carried "
                "rows clearing 25 mA cm-2 in some architecture stays at %d of %d."
                % (bot["mu"], top["mu"], top["catalyst_clearing"], ncat))
        return txt
    by_mu = {}
    for m in mv:
        by_mu.setdefault(m["mu"], []).append("%s %+d at >=%g" % (_ARCHW[m["arch"]], m["delta"], m["threshold"]))
    txt += ("Inside the interval a published count moves: %s; the catalyst-carried rows clearing 25 mA cm-2 number %s "
            "of %d across it." % ("; ".join("at %.3f mPa s the %s" % (mu, ", ".join(v))
                                           for mu, v in sorted(by_mu.items(), reverse=True)),
                                 "-".join(str(n) for n in sorted({r["catalyst_clearing"] for r in sw})), ncat))
    return txt
S_MU_OVERRIDE = {"DMA": (
    "The handbook entry for this solvent stands apart from its own homolog: N,N-dimethylformamide, "
    "one methylene lighter, is printed as 0.794 mPa s in the same column of the same page, so the "
    "tabulated 1.927 mPa s makes DMA 2.4 times the more viscous of the pair where that substitution "
    "normally costs a few tens of a percent. The column assignment is not in question -- ethanol "
    "1.074, 1,4-dioxane 1.177, dimethyl sulfoxide 1.987 and diethyl ether 0.224 all read correctly "
    "at the same position. The handbook carries no second viscosity for DMA. A second compilation does: "
    "Krumgalz, J. Chem. Soc., Faraday Trans. 1 1983, 79, 571-587, Table 3, p. 578, prints 0.00919 P (0.919 mPa s) "
    "at 25 C beside 0.00793 P for DMF, in line with the homolog. The handbook value is the one carried, and the "
    "re-solve below runs down to the Krumgalz value. "
    + _dma_moves_sentence())}

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
  "consequence: DMA carries the kilogram-scale Ni-xec campaign, which ran at 10 mA cm-2. At its sourced "
  "rate constant that row's best ceiling is %.1f mA cm-2 at the printed 1.927 and %.1f at 0.927 (G-DMAMU re-solve). "
  % (max(sorted(_DMA["swept"], key=lambda r: -r["mu"])[0]["dma_cells"]["Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)"].values()),
     max(sorted(_DMA["swept"], key=lambda r: r["mu"])[0]["dma_cells"]["Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)"].values()))
  + _dma_moves_sentence() + " Anyone resolving the "
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
 ("MeNO2",  61.04, 0.630, 1.137, 1.0, "measured", CRC,
  "Sect. 6, 'Viscosity of Liquids', p. 6-246, Nitromethane row (25 C column)", "measured", CRC, L_LAB, ""),
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
# Ansari & Singh, Table-1 p. 68 (wt% AN: rho g cm-3, eta cP, as printed) and their pure-AN values (rho 0.7767, eta 0.346).
_AS_PTS = {10: (0.9802, 0.982), 20: (0.9588, 0.973), 30: (0.9380, 0.910), 40: (0.9134, 0.8841), 50: (0.8920, 0.753),
           60: (0.8664, 0.656), 70: (0.8443, 0.574), 100: (0.7767, 0.346)}
_SOLV_CSV = {r["solvent"]: r for r in csv.DictReader(io.open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                                                               "solvents.csv"), encoding="utf8"))}
_RHO_AN, _RHO_W, _MU_AN = float(_SOLV_CSV["MeCN"]["rho"]), float(_SOLV_CSV["H2O"]["rho"]), float(_SOLV_CSV["MeCN"]["mu_mPas"])


def _as_wt(v_an, v_w):
    """mass per cent MeCN of a v/v mixture measured before mixing, at the pure-component densities of solvents.csv"""
    return 100.0 * v_an * _RHO_AN / (v_an * _RHO_AN + v_w * _RHO_W)


def _as_interp(wt):
    ks = sorted(_AS_PTS)
    lo = max(k for k in ks if k <= wt); hi = min(k for k in ks if k >= wt)
    f = 0.0 if hi == lo else (wt - lo) / (hi - lo)
    return tuple(_AS_PTS[lo][i] + f * (_AS_PTS[hi][i] - _AS_PTS[lo][i]) for i in (0, 1)), lo, hi


AS22 = ("Ansari & Singh, Res. J. Chem. Sci. 2022, 12(1), 67-69, Table-1 p. 68 -- measured densities and viscosities of "
        "acetonitrile-water at 25 C, 10-70 wt pct AN plus pure AN. Open access (www.isca.in). Its pure-component values, "
        "rho = 0.7767 g cm-3 and eta = 0.346 cP, set against the CRC 97th ed. MeCN entries carried here (%.3f, %.3f): the "
        "density agrees to %.1f pct and the viscosity is %.1f pct lower than the handbook's printed value"
        % (_RHO_AN, _MU_AN, 100 * abs(0.7767 / _RHO_AN - 1), 100 * (1 - 0.346 / _MU_AN)))
# BOUNDS FOR THE MIXTURE PROPERTIES (data/mixture_property_bounds.py, gate G-MIXBOUND).
# These rows cannot be SOURCED -- no table gives a 25 C value at a stated v/v ratio for most of
# them -- but most of them can be BOUNDED by something citable, and the assumption behind each
# bound is stated here rather than left for a reader to reconstruct.
def _as_note(v_an, v_w, mu_c, rho_c):
    """What Ansari & Singh's table says about a MeCN/water mixture at v_an:v_w (v/v), computed."""
    wt = _as_wt(v_an, v_w)
    (rho_i, mu_i), lo, hi = _as_interp(wt)
    where = ("inside the 10-70 wt pct range Ansari & Singh measure" if wt <= 70 else
             "outside the 10-70 wt pct range Ansari & Singh measure, between their 70 wt pct row and pure acetonitrile")
    lab = lambda k: "pure AN" if k == 100 else "%d wt pct" % k
    return ("%d:%d v/v (MeCN:water) = %.1f wt pct MeCN, %s. Interpolating their Table-1 p. 68 entries at %s (%.4g cP, "
            "%.4f g cm-3) and %s (%.4g cP, %.4f g cm-3) gives eta = %.3f cP and rho = %.3f g cm-3; the carried %.3g cP and "
            "%.3g g cm-3 are %+.1f pct and %+.1f pct against that."
            % (v_an, v_w, wt, where, lab(lo), _AS_PTS[lo][1], _AS_PTS[lo][0], lab(hi), _AS_PTS[hi][1], _AS_PTS[hi][0],
               mu_i, rho_i, mu_c, rho_c, 100 * (mu_c / mu_i - 1), 100 * (rho_c / rho_i - 1)))


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
    "EtOH/MeOH 1:1 v/v": _BDISC, "THF/MeOH 5:1 v/v": _BDISC, "THF/EtOH 1:1 v/v": _BDISC,
}

# The two aqueous-alcohol mixtures read against the 20 C table they cite (chemistry audit, pass 6). Values as printed,
# verified on the page images: CRC 97th ed., 'Concentrative Properties of Aqueous Solutions', methanol block p. 5-125
# and ethanol block p. 5-121 -- (mass %, rho g cm-3, eta mPa s) at 20 C. The carried densities (0.87, 0.89) are NOT these
# entries; the rows say so and state the consequence, and the carried values are left to data/build_reactions50.py.
_AQ_PAGE = {"MeOH/H2O 1:1 v/v": ("5-125", "Methanol", "MeOH", ((44.0, 0.9273, 1.821), (46.0, 0.9235, 1.805))),
            "EtOH/H2O 1:1 v/v": ("5-121", "Ethanol", "EtOH", ((44.0, 0.9269, 2.850), (46.0, 0.9227, 2.843)))}
# Water at 20 C (CRC 97th ed. p. 6-247, the table the Ea row reads) -- a 20 C value, so it is not the 25 C property
# solvents.csv carries; the 25 C value is read from this registry's own H2O row.
_WATER_20C_MPAS = 1.002
_WATER_25C_MPAS = [p for p in PURE if p[0] == "H2O"][0][2]
_ETA_W20, _ETA_W25 = _WATER_20C_MPAS, _WATER_25C_MPAS


def _aq_page_read(n_, mu, rho):
    """Interpolate the printed 20 C entry at the 1:1 v/v composition and state what the carried values are against it,
    including what the density difference does to nu, k_m and the published matrix (rho enters only through nu)."""
    import archetype_bands as _AB
    page, block, comp, ((w0, r0, e0), (w1, r1, e1)) = _AQ_PAGE[n_]
    rho_a = [p for p in PURE if p[0] == comp][0][3]
    rho_w = [p for p in PURE if p[0] == "H2O"][0][3]
    w = 100.0 * rho_a / (rho_a + rho_w)                       # 1:1 by volume before mixing, pure densities at 25 C
    if not (w0 <= w <= w1):
        raise SystemExit("%s: %.2f mass pct lies outside the bracketing page rows" % (n_, w))
    rho_p = r0 + (r1 - r0) * (w - w0) / (w1 - w0)
    eta_p = e0 + (e1 - e0) * (w - w0) / (w1 - w0)
    eta_25 = eta_p * _ETA_W25 / _ETA_W20
    nu_c, nu_p = mu * 1e-3 / (rho * 1e3), mu * 1e-3 / (rho_p * 1e3)
    with io.open(_os.path.join(_HERE_D, "reactions_50.csv"), encoding="utf8") as fh:
        users = [r for r in csv.DictReader(fh) if r["solvent"] + " 1:1 v/v" == n_]
    with io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "tier0_ec_matrix.csv"), encoding="utf8") as fh:
        mat = {r["reaction"]: r for r in csv.DictReader(fh)}
    km_drop = {a: 1.0 - _AB.delta_eff(a, 1.0e-9, nu_p) / _AB.delta_eff(a, 1.0e-9, nu_c) for a in ("rde", "rce")}
    moves, cross = [], 0
    for u in users:
        Dm = float(u["D_cm2s"]) * 1e-4
        for a in ("natural", "stirred", "flow", "anec", "micro", "rde", "rce"):
            f = _AB.delta_eff(a, Dm, nu_c) / _AB.delta_eff(a, Dm, nu_p)
            v0 = float(mat[u["reaction"]][a])
            moves.append((f - 1.0, u["reaction"], a, v0, v0 * f))
            cross += sum((v0 >= t) != (v0 * f >= t) for t in (25.0, 50.0))
    big = max(moves, key=lambda x: abs(x[0])) if moves else None
    loc = ("p. %s, %s block, 20 C: rho = %.4f g cm-3 at %.1f mass %% and %.4f at %.1f mass %%; 1:1 v/v is %.1f mass %% "
           "(pure-component densities, volumes measured before mixing)" % (page, block, r0, w0, r1, w1, w))
    sens = ("The page prints rho = %.4f g cm-3 at %.1f mass %% (20 C, interpolated); the carried %.2f is a declared "
            "assumption %.1f pct below it. rho enters only through nu = mu/rho: the carried value makes nu %.1f pct higher "
            "than the page density would, which leaves the fixed-film, ANEC and microfluidic archetypes untouched and lowers "
            "k_m by %.1f pct at the RDE and %.1f pct at the rotating cylinder. "
            % (rho_p, w, rho, 100 * (1 - rho / rho_p), 100 * (nu_c / nu_p - 1), 100 * km_drop["rde"], 100 * km_drop["rce"]))
    if users:
        sens += ("At the page density the %s reaction%s in this solvent move by at most %.1f pct (%s, %s, %.2f -> %.2f "
                 "mA cm-2), and %s."
                 % (_numword(len(users)), "s" if len(users) > 1 else "", 100 * abs(big[0]), big[1], _ARCHW[big[2]], big[3], big[4],
                    "no 25 or 50 mA cm-2 threshold count moves" if cross == 0 else
                    "%d threshold crossing%s occur%s" % (cross, "s" if cross > 1 else "", "" if cross > 1 else "s")))
    mu_disc = (" TEMPERATURE BASIS: the source table is measured at 20 C and this model works at 25 C; the handbook has no "
               "25 C table for an aqueous alcohol mixture. The carried 25 C viscosity, %.2f mPa s, is %.1f pct %s the printed "
               "20 C entry (%.3f mPa s at %.1f mass %%, p. %s) scaled by the temperature dependence of water's own viscosity "
               "over the same interval (%.3f to %.3f mPa s), i.e. %.2f; the residual approximation is that the mixture's "
               "relative temperature dependence matches water's across 20-25 C."
               % (mu, 100 * abs(mu / eta_25 - 1), "below" if mu < eta_25 else "above", eta_p, w, page, _ETA_W20, _ETA_W25,
                  eta_25))
    return {"rho_loc": loc, "rho_sens": sens, "mu_disc": mu_disc, "rho_page": rho_p, "mass_pct": w}


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
    "EtOH/MeOH 1:1 v/v":  ("Declared bracket: pure-component viscosities of ethanol and methanol, both "
                           "page-anchored in this registry", "bracket [0.544, 1.074] mPa s", _ORG_BOUND),
    "THF/MeOH 5:1 v/v":   ("Declared bracket: pure-component viscosities of THF and methanol, both "
                           "page-anchored in this registry", "bracket [0.456, 0.544] mPa s", _ORG_BOUND),
    "THF/EtOH 1:1 v/v":   ("Declared bracket: pure-component viscosities of THF and ethanol, both "
                           "page-anchored in this registry", "bracket [0.456, 1.074] mPa s", _ORG_BOUND),
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
  ("bracket", _as_note(9, 1, 0.48, 0.82))),
 ("MeOH/H2O 1:1 v/v", 26.4, 1.60, 0.87, 1.94, GCGD07, CRC_AQ_WARN, None),
 ("EtOH/H2O 1:1 v/v", 33.0, 2.40, 0.89, 1.58, GCGD07, CRC_AQ_WARN, None),
 ("DMF/H2O 9:1 v/v",  56.0, 1.00, 0.96, 1.15, AG95, "", None),
 ("DMSO/THF 5:1 v/v", 77.1, 1.55, 1.06, 1.00, "no measured isotherm located for this pair", "", None),
 ("tAmOH/H2O 3:1 v/v",35.0, 2.80, 0.85, 1.73, "no measured isotherm located for this pair", "", None),
 ("AcOH/HCOOH 1:1 v/v",53.0,1.28, 1.13, 1.0,  "no measured isotherm located for this pair", "", None),
 # chemistry review 2026-10-06: these three are read by the solver (data/solvents.csv) and had no registry row.
 # mu is a mole-fraction log-mix of the two page-anchored pure components, rho volume-weighted, phi*M the
 # Perkins-Geankoplis mole-fraction rule; the values equal data/build_reactions50.py's SOLVENTS entries.
 ("EtOH/MeOH 1:1 v/v", 37.79, 0.719, 0.786, 1.7,   "no measured isotherm located for this pair", "", None),
 ("THF/MeOH 5:1 v/v",  60.65, 0.48,  0.867, 1.136, "no measured isotherm located for this pair", "", None),
 ("THF/EtOH 1:1 v/v",  56.96, 0.751, 0.834, 1.235, "no measured isotherm located for this pair", "", None),
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
  ("mu-declared", _as_note(1, 2, 0.90, 0.94))),
 # 1:1 v/v = 43.8 wt% MeCN (0.5 L x 0.776 against 0.5 L x 0.997), inside the same table: the 40 wt% (0.9134 g cm-3,
 # 0.8841 cP) and 50 wt% (0.8920, 0.753) rows interpolate to rho 0.905, eta 0.835. Eq. S30 at x(H2O) = 0.745:
 # 0.745 x 2.6 x 18.015 + 0.255 x 1.0 x 41.05 = 45.36 = 1.900 x 23.88. The bromination row's H-cell medium.
 ("H2O/MeCN 1:1 v/v", 23.88, 0.835, 0.905, 1.900, AS22 + "; " + CVK67 + "; " + WS94 + "; " + AG95, "",
  ("derived", _as_note(1, 1, 0.835, 0.905) + " phi*M = 45.36 by Eq. S30 at x(H2O) = 0.745.")),
]

# Every solvent a reaction runs in must have registry rows, and must be marked used. Three mixtures the solver read from
# data/solvents.csv had neither until the chemistry review of 2026-10-06, and no gate noticed, because every check here
# compared rows that EXIST against the solver; none asked whether a solver input has a row at all.
def _check_solvents_registered():
    import csv as _csv, os as _os
    _rx = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "reactions_50.csv")
    used = {r["solvent"] for r in _csv.DictReader(open(_rx, encoding="utf-8"))}
    have = {}
    for r in list(PURE) + list(MIX):                       # full name without " v/v" first, then the leading token
        have.setdefault(r[0].replace(" v/v", ""), r[0]); have.setdefault(r[0].split(" ")[0], r[0])
    miss = sorted(u for u in used if u not in have)
    if miss:
        raise AssertionError("solvents a reaction runs in have no registry row: %s" % miss)
    unmarked = sorted(have[u] for u in used if have[u] not in USED_SOLVENTS)
    if unmarked:
        raise AssertionError("solvents a reaction runs in are not in USED_SOLVENTS (they would print as display-only): %s"
                             % unmarked)


_check_solvents_registered()


def _disp(name):
    return "" if name in USED_SOLVENTS else S_DISPLAY_SOLV

# CRC 97th ed. Sect. 15, 'Laboratory Solvents and Other Liquid Reagents': the density each row prints and its reference
# temperature (the superscript), read from the page (chemistry audit, pass 5). A carried density is state A at 25 C only
# where the page prints that value at 25 C; a 20 C entry, or a carried value the page does not print, is declared.
_CRC15_RHO = {"MeCN": (0.7825, 20, "15-13"), "acetone": (0.7902, 20, "15-13"), "AcOH": (1.0510, 20, "15-13"),
              "DMA": (0.9372, 25, "15-15"), "DMF": (0.9445, 25, "15-16"), "DMSO": (1.1010, 25, "15-16"),
              "EtOH": (0.7893, 20, "15-16"), "MeOH": (0.7909, 20, "15-17"), "MeNO2": (1.1371, 20, "15-18"),
              "THF": (0.8833, 25, "15-19")}


def _rho_basis(n_, rho):
    """(state, locator, sensitivity prefix) for a CRC-cited pure-solvent density."""
    pr, tref, pg = _CRC15_RHO[n_]
    loc = "Sect. 15, 'Laboratory Solvents and Other Liquid Reagents', p. %s, density column (%.4f g cm-3 at %d C)" % (pg, pr, tref)
    same = abs(pr - rho) <= 5.0001e-4                       # the carried value is the printed entry to three decimals
    if tref == 25 and same:
        return "measured", loc, ""
    # declared: the page is still where the reader finds the printed value the sensitivity compares against
    dk = 100 * (0.356 * abs(_math.log(rho / pr)))
    if same:
        what = ("the carried %.3f is that %d C entry carried unchanged as the 25 C density, which is lower by the liquid's "
                "thermal expansion over 5 K" % (rho, tref))
    else:
        what = ("the carried %.3f is %s, %.1f pct %s the printed entry, and the page does not print it"
                % (rho, "a 25 C value" if tref == 20 else "not the printed 25 C value", 100 * abs(rho / pr - 1),
                   "below" if rho < pr else "above"))
    return "assumption", loc, (
        "CRC 97th ed. p. %s prints %.4f g cm-3 at %d C (the superscript is the reference temperature); %s. rho enters only "
        "through nu = mu/rho, and Sh ~ Sc^0.356 at the rotating cylinder, so the difference from the printed entry moves "
        "k_m there by %.2f pct and leaves every fixed-film archetype untouched. " % (pg, pr, tref, what, dk))


_PHI_DECLARED = {"HFIP"}       # pure solvents whose phi the correlation's own list does not cover


def _phi_sens(n_, phi, alt=1.5):
    """Re-scale the published matrix for the rows in this solvent at phi = alt (ethanol's value, the associated alcohol
    nearest in kind): D ~ phi^0.5, and i_lim ~ D on the fixed films, D^(2/3) at the RDE (Levich) and D^0.644 at the
    rotating cylinder (Eisenberg, Sc^0.356)."""
    with io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "tier0_ec_matrix.csv"), encoding="utf8") as fh:
        mat = list(csv.DictReader(fh))
    with io.open(_os.path.join(_HERE_D, "reactions_50.csv"), encoding="utf8") as fh:
        rows = [r["reaction"] for r in csv.DictReader(fh) if r["solvent"] == n_]
    pexp = {"natural": 1.0, "stirred": 1.0, "flow": 1.0, "anec": 1.0, "micro": 1.0, "rde": 2.0 / 3.0, "rce": 1.0 - 0.356}
    f = (alt / phi) ** 0.5
    moves = []
    for a, pe in pexp.items():
        v0 = [float(r[a]) for r in mat]
        v1 = [float(r[a]) * (f ** pe if r["reaction"] in rows else 1.0) for r in mat]
        for t in (25, 50):
            c0, c1 = sum(x >= t for x in v0), sum(x >= t for x in v1)
            if c0 != c1:
                moves.append("the %s >=%d mA cm-2 count %d -> %d" % (_ARCHW[a], t, c0, c1))
    txt = ("D ~ (phi M)^0.5. Raising phi from %.1f to %.1f, ethanol's value and the associated alcohol nearest in kind, "
           "scales D by %.3f; re-scaling the published matrix for the %s %s row%s (i_lim ~ D on the fixed films, D^(2/3) at "
           "the RDE, D^0.644 at the rotating cylinder) moves %s. "
           % (phi, alt, f, _numword(len(rows)), n_, "" if len(rows) == 1 else "s", "; ".join(moves) or "no threshold count"))
    if moves:
        txt += "That count is therefore conditional on the declared association parameter. No architecture median moves."
    return txt


for n_, M, mu, rho, phi, mus, muc, mul, rhos, rhoc, rhol, note in PURE:
    d = _disp(n_)
    if rhos == "measured" and rhoc == CRC:
        rhos, rhol, _rho_pre = _rho_basis(n_, rho)
    else:
        _rho_pre = ""
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
            ("rho", rho, "g mL-1", rhos, rhoc, rhol, _rho_pre + S_RHO, "density")):
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
                ("a declared 25 C density: the cited handbook prints this solvent's density at another reference "
                 "temperature, or a different value, as the sensitivity states." + tail)
                if (prop == "rho" and _rho_pre) else
                (f"no page-anchored primary {what}; the source below is secondary." + tail)
                if cite else (f"no page-anchored {what} located." + tail),
                cite if cite else "-- (no source supports this value)", loc, sens + d)
    if n_ in _PHI_DECLARED:
        add("2. Solvents", f"{n_}: phi (assoc.)", f"{phi}", "-", "assumption",
            "a declared modelling choice: Wilke & Chang recommend association parameters for water (2.6), methanol (1.9), "
            "ethanol (1.5) and unassociated solvents (1.0), and %s, a hydrogen-bond-donor alcohol, is not among them, so "
            "treating it as unassociated is a choice rather than a reading." % n_ + tail, WC55, L_WC55,
            _phi_sens(n_, phi) + d)
    else:
        add("2. Solvents", f"{n_}: phi (assoc.)", f"{phi}", "-", "measured",
            "Wilke-Chang association parameter as recommended by the correlation's authors", WC55,
            L_WC55,
            "D ~ (phi M)^0.5. The frequently quoted revision phi(H2O) = 2.26 in place of 2.6 would "
            "lower aqueous D by 7 pct; no threshold count in Table S5 moves by more than one entry." + d)
    add("2. Solvents", f"{n_}: nu = mu/rho", f"{mu*1e-3/(rho*1000):.3e}", "m2 s-1", "derived",
        "kinematic viscosity computed from the mu and rho rows above", "this registry", "",
        "Inherits the exposure of its two inputs." + d)

def _h2omecn21_sens():
    """H2O/MeCN 2:1: the carried viscosity against Ansari & Singh's interpolation, and what it can move."""
    (rho_i, mu_i), _lo, _hi = _as_interp(_as_wt(1, 2))
    mu_c = [m for m in MIX if m[0] == "H2O/MeCN 2:1 v/v"][0][2]
    assert abs(round(rho_i, 2) - [m for m in MIX if m[0] == "H2O/MeCN 2:1 v/v"][0][3]) < 1e-9, \
        "the 2:1 density no longer rounds to its interpolation; reconsider its state"
    rows = [r["reaction"] for r in _RX50 if r["solvent"] == "H2O/MeCN"]
    assert rows, "no reaction runs in H2O/MeCN 2:1"
    with io.open(_os.path.join(_HERE_D, "..", "julia", "tier0_ec_matrix.csv"), encoding="utf8") as fh:
        top = max(float(v) for r in _csv.DictReader(fh) if r["reaction"] in rows
                  for k, v in r.items() if k not in ("class", "reaction", "carrier"))
    pct = 100 * (1 - mu_c / mu_i)
    assert top * (mu_i / mu_c) < 25, "a row in this solvent would approach 25 mA cm-2"
    return ("A declared value: Ansari & Singh's Table 1 interpolates to %.3f cP at this composition and the carried "
            "%.2f cP is %.1f pct lower, while the carried density is their %.3f g cm-3 to its printed precision. %s run%s in this "
            "solvent, with a highest ceiling of %.2f mA cm-2; i_lim varies no faster than 1/mu, so the interpolated "
            "viscosity would lower %s ceilings by at most %.1f pct, far from either threshold. "
            % (mu_i, mu_c, pct, rho_i, _numword(len(rows)).capitalize() + (" row" if len(rows) == 1 else " rows"),
               "s" if len(rows) == 1 else "", top, "its" if len(rows) == 1 else "their", pct))


S_MU_OVERRIDE["H2O/MeCN 2:1 v/v"] = _h2omecn21_sens() + S_MU

for n_, M, mu, rho, phi, cite, warn, anchor in MIX:
    d = _disp(n_)
    # anchor = (state, note) when a measured table for this pair HAS been retrieved. Without it
    # the row names the paper that would have to be page-anchored. Leaving
    # that wording on a row whose source has since been read is exactly the stale-claim failure
    # this project keeps getting bitten by, so the wording is driven by the data, not typed.
    if anchor:
        a_state, a_note = anchor
        # "mu-declared": the interpolation reproduces the carried density to its last printed digit but not the
        # carried viscosity, so only the viscosity is a declared value.
        mu_state = "derived" if a_state == "derived" else "assumption"
        rho_state = "derived" if a_state in ("derived", "mu-declared") else "assumption"
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
    if anchor:
        _disc = _disc + " BASIS: " + anchor[1]
    if n_ in _AQ_PAGE:
        _aq = _aq_page_read(n_, mu, rho)
        add("2. Solvents", f"{n_}: mu (25 C)", f"{mu}", "mPa s", mu_state,
            mu_note + warn, mu_cite, mu_loc, S_MU_OVERRIDE.get(n_, S_MU) + _aq["mu_disc"] + d)
        add("2. Solvents", f"{n_}: rho", f"{rho}", "g mL-1", "assumption",
            "a declared 25 C density for the 1:1 v/v mixture; the handbook entry at this composition is stated in the "
            "sensitivity and is not the carried value." + warn, CRC_5118, _aq["rho_loc"], _aq["rho_sens"] + d)
    else:
        add("2. Solvents", f"{n_}: mu (25 C)", f"{mu}", "mPa s", mu_state,
            mu_note + warn, mu_cite, mu_loc, S_MU_OVERRIDE.get(n_, S_MU) + _disc + d)
        add("2. Solvents", f"{n_}: rho", f"{rho}", "g mL-1", rho_state if anchor else mu_state,
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
    "the molal conductivity kappa/m falling to 0.44 of its dilute value by 0.80 mol/kg and to 0.05 by "
    "4.50 mol/kg for Bu4NBF4/MeCN, and to 0.74 by 1.57 mol/kg for NaCl/H2O. The assumption is therefore "
    "quantitatively wrong above roughly 1 M and the model states so. What protects the reported "
    "results is that the numerics are verified against the analytic limits of the theory it does "
    "implement -- Newman's binary-electrolyte x2 migration enhancement is %s, and discrete charge "
    "conservation holds to %s -- and " % (_AG_BIN, _AG_CC) +
    "that the conclusions rest on the architecture ORDERING and on order-of-magnitude contrasts, "
    "neither of which any sweep run here inverts.")
_MUSJ = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "solution_viscosity_sensitivity.json"), encoding="utf8"))


def _musj_sentence():
    """The viscosity sweep's result, read from results/solution_viscosity_sensitivity.json and from the exponents
    data/sensitivity_solution_viscosity.py asserts against the correlations (MU_EXP, parsed, not imported)."""
    import ast as _ast
    src = io.open(_os.path.join(_HERE_D, "sensitivity_solution_viscosity.py"), encoding="utf8").read()
    mu_exp = None
    for node in _ast.parse(src).body:
        if isinstance(node, _ast.Assign) and any(getattr(t, "id", "") == "MU_EXP" for t in node.targets):
            mu_exp = _ast.literal_eval(node.value) if isinstance(node.value, _ast.Dict) and all(
                isinstance(v, _ast.Constant) for v in node.value.values) else None
            if mu_exp is None:
                mu_exp = {k.value: eval(compile(_ast.Expression(v), "<mu_exp>", "eval"))
                          for k, v in zip(node.value.keys, node.value.values)}
    arch = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
    ff = lambda x: (("%.2f" % x).rstrip("0") + "0") if ("%.2f" % x).rstrip("0").endswith(".") else ("%.2f" % x).rstrip("0")
    andj = lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
    fixed = [a for a in arch if abs(mu_exp[a] + 1.0) < 1e-9]
    base = _MUSJ["baseline_n25"]
    first = {}
    for sw in _MUSJ["sweep"]:
        for i, a in enumerate(arch):
            if a not in first and sw["n25"][i] != base[i]:
                first[a] = (sw["factor"], base[i], sw["n25"][i])
    hold = max(sw["factor"] for sw in _MUSJ["sweep"] if all(x["ordering_holds"] for x in _MUSJ["sweep"]
                                                          if x["factor"] <= sw["factor"]))
    order = sorted(first.items(), key=lambda kv: kv[1][0])
    lead = order[0] if order else None
    never = [_ARCHW[a] for a in arch if a not in first]
    txt = ("Swept rather than corrected, the %d rows at >= %.1f M total dissolved. The response is NOT 1/mu everywhere: "
           "mu also enters nu, and delta_eff moves with it wherever delta is computed, so d ln i_lim / d ln mu is -1 for "
           "the %s fixed-film archetypes (%s), %s at the RDE (Levich) and %s at the rotating cylinder (Eisenberg), "
           "asserted against the computed delta_eff at run time. "
           % (_MUSJ["n_flagged"], _MUSJ["cut_M"], _numword(len(fixed)), ", ".join(_ARCHW[a] for a in fixed),
              "-5/6" if abs(mu_exp["rde"] + 5.0 / 6.0) < 1e-9 else "%.3f" % mu_exp["rde"], "%.3f" % mu_exp["rce"]))
    if lead:
        txt += ("Result: the first >=25 count moves at mu_solution/mu_solvent = %s, and it is the %s column (%d -> %d)"
                % (ff(lead[1][0]), _ARCHW[lead[0]], lead[1][1], lead[1][2]))
        rest = ["the %s at %s (%d -> %d)" % (_ARCHW[a], ff(f[0]), f[1], f[2]) for a, f in order[1:]]
        txt += ("; %s move%s next" % (andj(rest), "s" if len(rest) == 1 else "") if rest else "") + ". "
    else:
        txt += "Result: no >=25 count moves anywhere in the swept range. "
    txt += ("The architecture ordering holds to %s, and the %s counts do not move anywhere in the swept range "
            "(to %s). The reported integers should be read with that breaking point; the ordering does not depend on "
            "it." % (ff(hold), andj(never), ff(max(sw["factor"] for sw in _MUSJ["sweep"]))))
    return txt
add("3. Estimation methods", "Viscosity used in D and in nu", "pure solvent", "-", "assumption",
    "mu is the PURE SOLVENT viscosity of Table S3, page-anchored to CRC, used both in "
    "Wilke-Chang (D ~ 1/mu) and in nu = mu/rho for the mass-transfer correlations. The cells "
    "contain solute at up to %.2f M total, and a solution is more viscous than the solvent it is " % _MUSJ["c_tot_max_M"] +
    "made from, so every affected ceiling is OVERSTATED. Chosen because no solution-viscosity "
    "measurement exists for these fifty compositions and inventing one would be worse than "
    "declaring the gap", "declared modelling choice", "",
    _musj_sentence())
# The two increments applied more widely than Table 3-8 prints them (chemistry audit, pass 5). Their exposure is computed
# by data/lebas_increment_sensitivity.py, which recomputes every Wilke-Chang volume with the table's specific entries.
_LBI = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "lebas_increment_sensitivity.json"),
                          encoding="utf8"))


def _lbi_pct(lo_hi):
    return "%+.1f to %+.1f pct" % (100 * (lo_hi[0] - 1), 100 * (lo_hi[1] - 1))


_LBI_CC = _LBI["closest_cell"]
_LBI_CCMOVE = max(100 * abs(r[k] - 1) for r in _LBI["carriers"] + _LBI["mediated_substrates"]
                  if r["row"] == _LBI_CC["row"] for k in ("D_ratio", "D_ratio_tertN12"))
_LBI_REACH = ("No cell of the published matrix lies within its own row's change of 25 or 50 mA cm-2: the closest "
              "moved-row cell, %s in the %s architecture at %.2f mA cm-2, is %.2f pct from %g and its D moves by at most "
              "%.2f pct, so no count moves."
              % (_LBI_CC["row"], _ARCHW[_LBI_CC["arch"]], _LBI_CC["value"], _LBI_CC["margin_pct"], _LBI_CC["threshold"],
                 _LBI_CCMOVE)
              if not _LBI["cells_that_could_cross"] else
              "%d cells of the published matrix lie within that change of a threshold: %s."
              % (len(_LBI["cells_that_could_cross"]),
                 "; ".join("%s, %s, %g" % (c["row"], _ARCHW[c["arch"]], c["threshold"]) for c in _LBI["cells_that_could_cross"])))
import math as _math_wc
add("3. Estimation methods", "Wilke-Chang: D = 7.4e-8 (phi M)^0.5 T / (mu V^0.6)", "7.4e-8",
    "(cgs mixed)", "measured",
    "empirical correlation as published; applies to the %d Wilke-Chang carriers of Table S2 and to the mediated-spec "
    "substrates. Ferrocene/MeCN anchor: V = %.0f cm3 mol-1 (both cyclopentadienyl ring corrections applied; iron takes "
    "the code's fallback increment, since Table 3-8 has none) and mu = %.3f mPa s give D = %.2e cm2 s-1, disclosed in S3"
    % (_LBI["n_wc_carriers"], _LBI["ferrocene_V_cm3mol"], _LBI["ferrocene_mu_MeCN_mPas"], _LBI["ferrocene_D_cm2s"]),
    WC55, L_WC55,
    "One anchor exists in this work, ferrocene in acetonitrile, and what it says depends on which measurement it is "
    "held against. Against 2.4e-5 cm2 s-1, the upper end of the textbook range 1.7-2.4e-5 and not page-anchored here, "
    "the correlation is %+.0f pct; against 1.70e-5 cm2 s-1 (Bard & Faulkner, Electrochemical Methods, 2nd ed., p. 260, "
    "Problem 6.12, quoting Mirkin, Richards & Bard, J. Phys. Chem. 1993, 97, 7672, measured in 0.5 M TBABF4) it is "
    "%+.1f pct. i_lim is at most linear in D, so even the larger miss displaces log10 i_lim by %.2f, against the 1-2 "
    "order-of-magnitude spreads that separate the reactor archetypes."
    % (_LBI["ferrocene_miss_pct"], _LBI["ferrocene_miss_secondary_pct"],
       abs(_math_wc.log10(1 + _LBI["ferrocene_miss_pct"] / 100.0))))
def _se_band_sentence():
    """The D the declared 4-5 Angstrom band gives in each solvent a Stokes-Einstein row runs in, computed from
    data/reactions_50.csv; each row's carried D must be reproduced at its own stated radius first."""
    kT = 1.380649e-23 * 298.15
    by_solv = {}
    with io.open(_os.path.join(_HERE_D, "reactions_50.csv"), encoding="utf8") as fh:
        for r in csv.DictReader(fh):
            prov = r["D_provenance"]
            if not prov.startswith("Stokes-Einstein"):
                continue
            mu = float(r["mu_mPas"]) * 1e-3
            rad = float(re.search(r"r=([0-9.]+)\s*A", prov).group(1)) * 1e-10
            d_se = kT / (6 * _math.pi * mu * rad) * 1e4
            if abs(d_se / float(r["D_cm2s"]) - 1) > 1e-3:
                raise SystemExit("Stokes-Einstein row %s: carried D %s is not kT/(6 pi mu r) at its stated radius"
                                 % (r["reaction"], r["D_cm2s"]))
            by_solv.setdefault((float(r["mu_mPas"]), r["solvent"]), []).append(r["reaction"])
    n = sum(len(v) for v in by_solv.values())
    parts = ["%s (%.3g mPa s) %.2f-%.2fe%d" % (sv, mu, *(lambda a, b: (a / 10 ** _math.floor(_math.log10(b)),
                                                                      b / 10 ** _math.floor(_math.log10(b)),
                                                                      _math.floor(_math.log10(b))))(
                kT / (6 * _math.pi * mu * 1e-3 * 5e-10) * 1e4, kT / (6 * _math.pi * mu * 1e-3 * 4e-10) * 1e4))
             for mu, sv in sorted(by_solv, reverse=True)]
    return ("D ~ 1/r, so the declared 4-5 Angstrom band spans 25 pct in D. Evaluated at 25 C in the solvent of each of "
            "the %s Stokes-Einstein entries, the band gives D (cm2 s-1) of %s; each entry's carried D is the value at "
            "its own radius inside the band (Table S2). " % (_numword(n), ", ".join(parts)))


add("3. Estimation methods", "Stokes-Einstein hydrodynamic radius r", "4-5", "Angstrom", "assumption",
    "hydrodynamic radius assigned to M(bpy)/M(salen) molecular-catalyst cores; the equation "
    "D = kB T / (6 pi mu r) itself is textbook", "declared modelling choice", "",
    _se_band_sentence() + _cd_sentence())
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
_LEBAS_SPECIAL = {
    "O (every oxygen except an acid hydroxyl)": (
        "Table 3-8 prints 7.4 for 'Oxygen (except as noted below)'. The model applies it to every oxygen other than a "
        "carboxylic-acid hydroxyl, including the oxygens the table lists separately: 9.1, 9.9 and 11.0 in methyl, ethyl "
        "and higher esters and ethers, and 8.3 joined to S, P or N. That is a declared simplification of the table, not "
        "a reading of it. Recomputing every Wilke-Chang volume with the specific entries (an ester or ether oxygen "
        "takes 9.1 when bonded to a methyl group, 9.9 to an ethyl and 11.0 otherwise; an oxygen bonded to S, P or N "
        "takes 8.3) moves %d of the %d Wilke-Chang carriers, by %s in D (D ~ V^-0.6), and %d of the %d mediated-spec "
        "substrates; the largest change anywhere is %.1f pct. %s"
        % (_LBI["n_carriers_moved"], _LBI["n_wc_carriers"], _lbi_pct(_LBI["carrier_D_ratio_range"]),
           _LBI["n_substrates_moved"], _LBI["n_mediated_substrates"], _LBI["max_abs_change_pct"], _LBI_REACH)),
    "N (every nitrogen without hydrogen)": (
        "Table 3-8 prints 15.6 for a doubly bonded nitrogen, 10.5 in primary and 12.0 in secondary amines, and has no "
        "entry for a nitrogen with three single bonds. The model applies 15.6 to every nitrogen without a hydrogen, "
        "which covers the doubly bonded and aromatic nitrogens the entry describes and also the tertiary amine, amide, "
        "carbamate and N-O nitrogens the table does not. Because no tabulated value exists for those, the exposure is "
        "bracketed rather than corrected: giving them the secondary-amine 12.0, the nearest tabulated value, together "
        "with the specific oxygen entries moves %d carriers by %s in D. %s"
        % (_LBI["n_carriers_moved_tertN12"], _lbi_pct(_LBI["carrier_D_ratio_range_tertN12"]), _LBI_REACH)),
}
for k, v in [("C",14.8),("H",3.7),("O (every oxygen except an acid hydroxyl)",7.4),("O (acid hydroxyl)",12.0),
             ("N (every nitrogen without hydrogen)",15.6),("N (primary amine)",10.5),("N (secondary)",12.0),("S",25.6),
             ("F",8.7),("Cl",24.6),("Br",27.0),("I",37.0),
             ("6-ring correction",-15.0),("5-ring",-11.5),("4-ring",-8.5),("3-ring",-6.0)]:
    add("3. Estimation methods", f"Le Bas increment: {k}", f"{v}", "cm3 mol-1", "measured",
        "additive atomic volumes at the normal boiling point, read from Table 3-8; the benzene "
        "closure check reproduces the textbook 96.0 cm3 mol-1", POLING, L_LEBAS,
        _LEBAS_SPECIAL.get(k, "D ~ V_A^-0.6; the benzene closure check bounds the increment set to a few per cent."))
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


def _med_specs():
    """{spec label: [species dicts]} parsed from julia/run_mediated.jl (code only, comments stripped), so the rows that
    describe the EC' specs read the specs instead of restating them (chemistry audit, pass 5)."""
    src = io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "run_mediated.jl"), encoding="utf8").read()
    body = src[src.index("SPECS = MedSpec["):src.index("## ONE-ROW MODE")]
    specs, lab = {}, None
    pat = re.compile(r'S\("([^"]+)",\s*([-+0-9.]+),\s*([0-9.eE+-]+),\s*([^,]+?),\s*([-+0-9.]+),\s*([-+0-9./]+)\)')
    for line in body.split("\n"):
        code = line.split("#")[0]
        m = re.match(r'\s*MedSpec\("([^"]+)"', code)
        if m:
            lab = m.group(1); specs[lab] = []
        for m in pat.finditer(code):
            name, z, D, cb, s_, nu = m.groups()
            specs[lab].append(dict(name=name, z=float(z), D=float(D),
                                   c=float(eval(cb, {"__builtins__": {}}, {"tr": lambda C: C * 1e-5})),
                                   s=float(s_), nu=float(eval(nu, {"__builtins__": {}}))))
    if len(specs) < 10 or any(not v for v in specs.values()):
        raise SystemExit("could not parse the EC' specs of julia/run_mediated.jl")
    return specs


_SPECS = _med_specs()
with io.open(_os.path.join(_HERE_D, "electrolyte_ions.csv"), encoding="utf8") as _fh:
    _EIONS = list(csv.DictReader(_fh))


def _spec_users(species, D=None):
    """Spec labels that carry `species` (at diffusivity D, if given)."""
    return [lab for lab, sp in _SPECS.items()
            if any(x["name"] == species and (D is None or abs(x["D"] - D) <= 1e-12 * max(1.0, D) + 1e-15) for x in sp)]


def _short(lab):
    return lab.split(" (")[0]
S_SOLVER = ("Solver species: supporting-electrolyte ions, mediators and mediator counter-ions. "
            "These set migration and the film potential in the Stage-1 and EC-prime solves, and "
            "the mediators and the ions that react do reach reported quantities; an ion that no reaction consumes or "
            "produces enters only through its concentration, its diffusivity cancelling at steady state. In the Stage-0 film model only the Table S2 carrier "
            "D sets i_lim, but that is not true of the mediated entries, whose plotted "
            "current comes from the EC-prime solve these species enter. Doubling ClO4-, SCN-, Br- "
            "and Br2 together and re-solving the %s mediated rows that carry them moves %d of the %d "
            "cells of the published matrix by more than 1 pct (the largest by %.0f pct) and raises %s by one "
            "entry each; the ordering the main text claims %s, and the largest median shift is %+.1f pct "
            "(%s). The doubling probes how strongly these declared inputs couple into the counts rather than "
            "estimating their error, and no count it moves moves by more than one entry. "
            % (_numword(len(_S2X["rows_resolved"])), _S2X["n_moved_gt1pct"], _S2X["n_cells"], _S2X["max_cell_change_pct"],
               ("%s counts (%s)" % (_numword(len(_S2X["count_moves"])), ", ".join("%s >=%d" % ({"natural": "unstirred",
                   "stirred": "stirred", "flow": "recirculating flow", "anec": "ANEC", "micro": "microfluidic", "rde": "RDE",
                   "rce": "rotating cylinder"}[m["arch"]], m["threshold"]) for m in _S2X["count_moves"]))) if _S2X["count_moves"] else "no count",
               "is preserved" if _S2X["ordering_preserved"] else "is NOT preserved",
               max(_S2X["median_shift_pct"].values()),
               max(_S2X["median_shift_pct"], key=_S2X["median_shift_pct"].get)) + "The discrete charge-conservation check "
            "(maximum deviation %s) and the binary-migration bound (2.00x Fick, %s) are insensitive to "
            "these values, because they test charge bookkeeping rather than the reported counts." % (_AG_CC, _AG_BIN))
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
add("4. Solver species diffusivities", "Br2 (aq)", "1.2e-09", "m2 s-1", "derived",
    "the measured aqueous molecular-bromine diffusivity rounded to two significant figures: Cussler Table 5.2-1 p. 127 "
    "tabulates 1.18e-5 cm2 s-1 = 1.18e-9 m2 s-1, and this row carries 1.2e-9 (+1.7 pct)",
    CUSSLER, "Table 5.2-1, p. 127 ('Diffusion coefficients at infinite dilution in water at "
    "25 C', Bromine row: 1.18e-5 cm2 s-1)",
    "The carried value is the printed 1.18e-9 rounded up by 1.7 pct; i_lim of the rows that carry it is at most linear "
    "in it, so the rounding moves those ceilings by at most 1.7 pct.")
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
# OXYGEN, MEASURED. The cathodic Giese row is carried by dissolved O2 (2026-10-05): its exemplar
# shows that oxygen is the only species reduced at the applied potential. Same table and page as
# Br2 and ethylene; the digits were read from the page raster (Chlorine 1.25 and Ethylene 1.87 on
# the same rows of the scan as the controls).
add("4. Solver species diffusivities", "O2 (aq)", "2.1e-09", "m2 s-1", "measured",
    "measured aqueous dioxygen diffusivity at infinite dilution, 25 C; the carrier D of the "
    "oxygen-mediated Giese row, whose medium is water/acetonitrile 2:1 at essentially water's "
    "viscosity (0.90 against 0.89 mPa s), so no scaling is applied",
    CUSSLER, "Table 5.2-1, p. 127 ('Diffusion coefficients at infinite dilution in water at "
    "25 C', Oxygen row: 2.10e-5 cm2 s-1)", "")
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
# chemistry audit, pass 4: rows whose value was re-solved at the end of a bracket carry that result ahead of the shared note
_c, _mv, _md = _mxf("br2_hi")
_S_EXTRA = {"Br2 (MeCN)": ("Re-solving the two rows that carry it (the Hofmann rearrangement and the amidyl amination) at "
                          "the Walden value moves their ceilings by x%.3f-x%.3f, and %s and %s moves. "
                          % (_c["ratio_lo"], _c["ratio_hi"], _mv, _md)
                          # 2026-10-07: at the Hofmann constant measured for HOBr (3.3 M-1 s-1) the amidyl row's recirculating
                          # cell sits at 25.8 mA cm-2, and this bracket carries it under 25; the same rule as the other rows
                          + ("The published count that moves is therefore conditional on where this declared value sits in "
                             "its bracket. " if _c["count_moves"] else ""))}
# The homogeneous partners (chemistry audit, pass 5): electrode spectators that the homogeneous step consumes or releases, so
# their D does not cancel. data/sensitivity_solver_species_2xD.py --group homog doubles each in its own spec and re-solves.
def _s2h_row(spec):
    r = _S2H["per_row"][spec]
    return "%+.2f to %+.2f pct" % (r["min_pct"], r["max_pct"])
def _s2h_counts():
    return ("no threshold count moves" if not _S2H["count_moves"] else
            "; ".join("the %s >=%d count %d -> %d" % (_ARCHW[m["arch"]], m["threshold"], m["from"], m["to"])
                      for m in _S2H["count_moves"]))
_S2H_HMF = [k for k in _S2H["per_row"] if k.startswith("HMF")][0]
_S2H_SCN = [k for k in _S2H["per_row"] if "thiocyanation" in k][0]
_S2H_SENT = {
    "borate": ("Doubling B(OH)4- and B(OH)3 together and re-solving the %s row in a scratch copy (an unperturbed control "
               "reproduces the published cells exactly) moves its seven ceilings by %s; %s, and the architecture ordering %s. "
               % (_S2H_HMF, _s2h_row(_S2H_HMF), _s2h_counts(), "holds" if _S2H["ordering_preserved"] else "does NOT hold")),
    "h_acid": ("Doubling it and re-solving the %s row in a scratch copy (an unperturbed control reproduces the published "
               "cells exactly) moves its seven ceilings by %s; %s, and the architecture ordering %s. "
               % (_S2H_SCN, _s2h_row(_S2H_SCN), _s2h_counts(), "holds" if _S2H["ordering_preserved"] else "does NOT hold")),
}
_S_EXTRA["B(OH)4- (aq)"] = _S2H_SENT["borate"]
_S_EXTRA["B(OH)3 (aq)"] = _S2H_SENT["borate"]
_S_EXTRA["H+ (AcOH/HCOOH)"] = _S2H_SENT["h_acid"]
with io.open(_os.path.join(_HERE_D, "reactions_50.csv"), encoding="utf8") as _fh:
    _RX_SOLV = {r["reaction"]: r["solvent"] for r in csv.DictReader(_fh)}
_LI_DECL = [lab for lab in _spec_users("Li+", 1.0e-9)]
_LI_NP = {r["electrolyte"]: float(r["D_cat"]) for r in _EIONS if r["cation"] == "Li+"}
_LI_NP_DECL = sorted(e for e, r in ((r["electrolyte"], r) for r in _EIONS)
                     if r["cation"] == "Li+" and r["D_cat_basis"].upper().startswith("DECLARED"))
_LI_MECN = [v for e, v in _LI_NP.items() if e.endswith("/MeCN")][0]
_LI_ACET = [v for e, v in _LI_NP.items() if e.endswith("/acetone")][0]
# the NHPI row's spectators re-solved at Krumgalz's acetone values (data/pyridinium_bracket.py writes the verdict)
_lc = lambda nm: nm[0].lower() + nm[1:] if nm[1:2].islower() else nm   # sentence-case a row name mid-sentence
_CLO4_NP = {r["electrolyte"]: float(r["D_an"]) for r in _EIONS if r["anion"] == "ClO4-"}
_CLO4_MECN = {v for e, v in _CLO4_NP.items() if e.endswith("/MeCN") or e.endswith("/MeCN-H2O")}
assert len(_CLO4_MECN) == 1, _CLO4_MECN
_CLO4_MECN = _CLO4_MECN.pop()
_CLO4_ACET = [v for e, v in _CLO4_NP.items() if e.endswith("/acetone")][0]
_CLO4_ONE = lambda solv: [v for e, v in _CLO4_NP.items() if e.endswith("/" + solv)][0]
assert abs(_CLO4_ACET - 115.8e-4 * 8.314462618 * 298.15 / 96485.33212 ** 2) < 2e-12, _CLO4_ACET
_PYH_SPECT = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "pyridinium_bracket.json"),
                                encoding="utf-8"))["spectators_krumgalz_bitidentical"]
SOLVER_BASIS = {
 "Li+ (generic organic)": (
   "Declared at 1.0e-9 in the EC' specs of the %s rows and in the %s slot%s of the Nernst-Planck ion table. Krumgalz, "
   "J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587, Table 4, p. 580 tabulates lambda0(Li+) in neither THF nor acetic "
   "acid; for formic acid it prints 19.5 S cm2 mol-1, i.e. %.2e m2 s-1 by Nernst-Einstein, %.1f times below the "
   "declared value, and the 1:1 acetic/formic mixture has no entry. For acetonitrile the same table prints a dash for "
   "H+ and Li+, and Gong et al., Energy Environ. "
   "Sci. 2015, 8, 3515-3530, Table 2, p. 3518 gives lambda0(Li+, AN) = 69.97 S cm2 mol-1, which the Nernst-Planck layer "
   "and the oxazole spec use (%.3e m2 s-1). For acetone Krumgalz prints 69.2 S cm2 mol-1 (p. 580), which the "
   "Nernst-Planck layer uses (%.3e m2 s-1) while the NHPI EC' spec keeps the declared value. Li+ is a spectator "
   "(s = 0, nu = 0) wherever it appears, so its D does not enter i_lim"
   % (" and ".join("%s (%s)" % (_short(l), _RX_SOLV.get(l, "?")) for l in _LI_DECL), " and ".join(_LI_NP_DECL),
      "s" if len(_LI_NP_DECL) > 1 else "", 19.5 * 8.314462618 * 298.15e-4 / 96485.33212 ** 2,
      1.0e-9 / (19.5 * 8.314462618 * 298.15e-4 / 96485.33212 ** 2), _LI_MECN, _LI_ACET)),
 "NH4+ (AcOH/HCOOH, thiocyanation spec)": (
   "Declared TRANSFER of a page-anchored aqueous value: CRC 97th ed., Sect. 5, p. 5-75 gives NH4+ lambda0 = 73.5 "
   "S cm2 mol-1 and D = 1.957e-5 cm2 s-1, carried at 2e-9 into the acetic/formic acid medium of the aryl-thiocyanation "
   "spec, the only spec that uses it (%s). No value for the mixture is tabulated: Krumgalz 1983, Table 4, p. 580 "
   "prints NH4+ 27.1 S cm2 mol-1 in formic acid, i.e. %.2e m2 s-1 by Nernst-Einstein, %.1f times below the carried "
   "value, and has no acetic-acid entry. NH4+ is a spectator there (s = 0, nu = 0), so its D does not enter i_lim"
   % ("; ".join(_short(l) for l in _spec_users("NH4+")), 27.1 * 8.314462618 * 298.15e-4 / 96485.33212 ** 2,
      2e-9 / (27.1 * 8.314462618 * 298.15e-4 / 96485.33212 ** 2))),
 "ClO4- (MeCN, aq-like)": (
   "Declared at 1.7e-9, 5 pct below the aqueous value (CRC 97th ed., p. 5-75, 1.792e-9). It is carried as a supporting "
   "ion in the EC' specs of three rows, %s, and in the Stage-1 slot of the %s row. Elsewhere the Stage-1 layer uses anchored "
   "values: %.3e in MeCN (the ClO4- (MeCN) row, Gong 2015, Table 2, p. 3518), also carried into MeCN/H2O as its "
   "major component, and %.3e in acetone "
   "(115.8 S cm2 mol-1 by Nernst-Einstein), %.3e in MeNO2 and %.3e in DMF from Krumgalz 1983, Table 4, p. 581, which "
   "prints a dash for ClO4- in the acetonitrile row. Re-solving the NHPI row's EC' spec with ClO4- and its Li+ counter-ion at "
   "Krumgalz's acetone values leaves its seven ceilings bit-identical. That holds for every spec carrying the "
   "declared value: an ion that neither the electrode reaction nor a solution reaction consumes or produces carries no "
   "flux at steady state, so its profile follows the potential alone and its diffusivity cannot enter a ceiling, "
   "although its concentration does, through electroneutrality"
   % (" and ".join(", ".join("%s (%s)" % (_lc(_short(l)), _RX_SOLV[l]) for l in _spec_users("ClO4-", 1.7e-9)).rsplit(", ", 1)),
      ", ".join(sorted({_lc(_short(r["reaction"])) for r in _EIONS if r["anion"] == "ClO4-" and abs(float(r["D_an"]) - 1.7e-9) < 1e-15})),
      _CLO4_MECN, _CLO4_ACET, _CLO4_ONE("MeNO2"), _CLO4_ONE("DMF")) + ("" if _PYH_SPECT and set(_CLO4_NP.values()) == {_CLO4_MECN, _CLO4_ACET, _CLO4_ONE("MeNO2"), _CLO4_ONE("DMF"), 1.7e-9} and len(_spec_users("ClO4-", 1.7e-9)) == 3 else 1 / 0)),
 "SCN- (AcOH/HCOOH)": (
   "Declared: Walden scaling of the MeCN row (Nernst-Einstein from Krumgalz's lambda0 = 113.3) by "
   "mu(MeCN)/mu(AcOH-HCOOH) = 0.369/1.28. The Walden transfer into a carboxylic-acid medium is unverified"),
 "Br2 (MeCN)": (
   "Declared at 2.2e-9: no measurement in MeCN was located. Walden scaling of the measured aqueous "
   "value (Cussler, Diffusion 3rd ed., Table 5.2-1, p. 127, 1.18e-9) by 0.890/0.369 gives 2.85e-9, 29 pct "
   "above the carried value; the ~2.4e-9 quoted for MeCN voltammetry lies between the two but was not "
   "page-anchored here, so it corroborates rather than sources"),
 "Cl2/HOCl lumped OX (aq)": (
   "Declared LUMP at 1.4e-9, 12 pct above the one member with a measured value, Cl2(aq) 1.25e-9 "
   "(Cussler, Diffusion 3rd ed., Table 5.2-1, p. 127); HOCl, the other member, has no value in that table. "
   "No single measurement can cover a lumped species, so none is claimed; the lump is the modelling choice"),
 "Cl2/HOCl lumped OX (MeCN/H2O)": (
   "Declared: the aqueous lump scaled by viscosity (Walden) to the acetonitrile/0.1 M aqueous HCl "
   "medium of the thioether row, 1.4e-9 x 0.890/0.48. No measurement of an oxidized-chlorine "
   "diffusivity in that mixture was located"),
 "O2- / HO2 (aq)": (
   "Declared equal to the measured diffusivity of dioxygen (Cussler Table 5.2-1): the reduced "
   "oxygen species of the Giese row, carried as the neutral hydroperoxyl radical at the medium's "
   "pH 2 (pKa 4.88), is taken to diffuse as its parent does. No measurement in the row's medium "
   "was located"),
 "(SCN)2 (AcOH/HCOOH)": (
   "Declared at 5.5e-10, 5 pct below the Walden transfer (x 0.369/1.28 = 5.8e-10) of a 2.0e-9 MeCN estimate "
   "that is itself unverified. No measurement "
   "of this species' diffusivity was located in either medium"),
 "H+ (MeCN/organic)": (
   "Declared BY ARGUMENT, not measurement: an aprotic medium supports no Grotthuss shuttle, so the "
   "aqueous value is reduced to roughly a third"),
 "H+ (1:1 aq/MeCN)": (
   "Declared: interpolated between the aprotic 3.0e-9 assumption and the page-anchored aqueous "
   "9.3e-9, on partial Grotthuss transport in a water-rich mixture"),
 "B(OH)4- (aq)": (
   "Declared: borate mobility taken as comparable to HCO3- for the pH-10 borate buffer of the HMF -> FDCA spec; no "
   "lambda0(B(OH)4-) was page-anchored. It takes no electrons at the electrode (s = 0), but the homogeneous step "
   "consumes it -- the buffer base takes up the protons the oxidation releases -- so its D does not cancel; its "
   "measured effect is in the sensitivity column"),
 "H+ (AcOH/HCOOH)": (
   "Declared BY ARGUMENT: set between the aprotic 3.0e-9 and a slower carboxylic-acid medium. It takes no electrons "
   "at the electrode (s = 0), but the homogeneous step of the aryl-thiocyanation spec releases it "
   "(ArH + (SCN)2 -> ArSCN + SCN- + H+), so its D does not cancel; its measured effect is in the sensitivity column"),
 "B(OH)3 (aq)": (
   "Declared: the neutral borate partner given the same mobility as B(OH)4-, which the buffer spec pairs it with. "
   "It takes no electrons at the electrode (s = 0), but the homogeneous step releases it as the buffer base is "
   "consumed, so its D does not cancel; its measured effect is in the sensitivity column"),
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
# chemistry audit, 2026-10-05: the triarylamine-mediated oxazole row became an EC' spec, which carries its 0.3 M LiClO4
# supporting anion explicitly; the value is the one the NP layer's ion table already uses (state A there).
add("4. Solver species diffusivities", "ClO4- (MeCN)", "2.759e-09", "m2 s-1", "derived",
    NE + "; lambda0(ClO4-, MeCN) = 103.6 S cm2 mol-1 gives 2.759e-9 m2 s-1, the value data/ion_diffusivities.csv "
    "carries for the k = 0 layer", "Gong, Fang, Gu, Li & Yan, Energy Environ. Sci. 2015, 8, 3515-3530",
    "Table 2, p. 3518, column AN (limiting molar conductivity, 25 C)",
    "Supporting anion of the oxazole row's EC' spec (zero electrode and homogeneous stoichiometry, 300 mM against a 5 mM "
    "mediator), so it carries no net flux at the limit and its diffusivity does not enter i_lim; the Kohlrausch route from "
    "Minc & Werblan's perchlorate salts gives 113.3 S cm2 mol-1 (+9 pct), which moves nothing for the same reason.")
# RETRIEVED 2026-08-22. Krumgalz Table 4, pp. 580-581 is a 25 C ion-by-solvent table of limiting
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
for n_, v, lam, sol in [("SCN- (MeCN)", "3.02e-09", 113.3, "acetonitrile"),
                        ("Br- (MeOH)", "1.5e-09", 56.53, "methanol")]:
    add("4. Solver species diffusivities", n_, v, "m2 s-1", "derived",
        NE + f"; lambda0({n_.split(' ')[0]}, {sol}) = {lam} S cm2 mol-1, z = 1. Replaces the "
        "inherited Izutsu citation, which could not be opened",
        "Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587", "Table 4, pp. 580-581 (limiting equivalent conductances of anions in organic "
        f"solvents at 25 C; {sol} row)", S_SOLVER)

for n_, v, meth in [
 ("Li+ (generic organic)", "1e-09",
  "order of the aqueous value, declared for the media in which no limiting conductance of Li+ is tabulated; where one "
  "is (acetonitrile, Gong Table 2; acetone and the other Krumgalz Table 4 solvents) the Nernst-Planck ion table "
  "uses it"),
 ("NH4+ (AcOH/HCOOH, thiocyanation spec)", "2e-09",
  "aqueous lambda0 = 73.5 -> 1.957e-9 (CRC 97th ed. p. 5-75), carried rounded into the AcOH/HCOOH medium of the "
  "thiocyanation spec; a cross-solvent transfer, declared"),
 ("ClO4- (MeCN, aq-like)", "1.7e-09",
  "aqueous 1.79e-9 reused in MeCN; same cross-solvent objection. Page-anchoring would require Krumgalz 1983"),
 ("SCN- (AcOH/HCOOH)", "8.7e-10",
  "Walden scaling of the MeCN row (3.02e-9) by mu(MeCN)/mu(AcOH-HCOOH) = 0.369/1.28; the Walden transfer "
  "into a carboxylic-acid medium is unverified"),
 ("Br2 (MeCN)", "2.2e-09",
  "declared; the Walden transfer of the measured aqueous value would give 2.85e-9, and ~2.4e-9 is quoted "
  "for MeCN voltammetry but not page-anchored"),
 ("Cl2/HOCl lumped OX (aq)", "1.4e-09",
  "a lumped oxidant at 1.4e-9, 12 pct above the measured Cl2(aq) 1.25e-9 (Cussler p. 127); no single "
  "measurement covers the lump"),
 ("Cl2/HOCl lumped OX (MeCN/H2O)", "2.6e-09",
  "the aqueous lump Walden-scaled to the MeCN / aqueous HCl medium of the thioether row (mu 0.48 mPa s)"),
 ("O2- / HO2 (aq)", "2.1e-09",
  "taken equal to the measured O2 value; the reduced oxygen species of the Giese row"),
 ("(SCN)2 (AcOH/HCOOH)", "5.5e-10",
  "no measurement located; 5 pct below the Walden transfer (5.8e-10) of a 2.0e-9 MeCN estimate that is "
  "itself unverified"),
 ("H+ (MeCN/organic)", "3e-09",
  "no Grotthuss shuttle in aprotic media, so set to ~1/3 of the aqueous value by argument rather "
  "than by measurement"),
 ("H+ (1:1 aq/MeCN)", "5e-09",
  "partial Grotthuss in a water-rich mixture; interpolated between the aprotic 3.0e-9 assumption "
  "and the aqueous 9.3e-9 derived value"),
 ("H+ (AcOH/HCOOH)", "2e-09",
  "the aryl-thiocyanation spec runs in an AcOH/HCOOH mixture; H+ there is set between the aprotic "
  "3.0e-9 assumption and a slower carboxylic-acid medium, by argument rather than measurement. "
  "added 2026-08-24: run_mediated.jl had used 2.0e-9 for this species with no registry row, and a "
  "value-only audit bound it by coincidence to the unrelated NH4+ row, which also reads 2e-9 -- "
  "exactly the wrong-row binding of claude.md trap 11. An electrode spectator (s = 0) that the homogeneous "
  "step releases (nu = +1), so its D does not cancel; G-SPEC2X (homogeneous partners) measures the effect"),
 ("Generic supporting K+/A- (Stage-1 verification cases)", "1.9e-09",
  "aqueous values reused in the verification cases, which test physics rather than chemistry"),
]:
    add("4. Solver species diffusivities", n_, v, "m2 s-1", "assumption", meth,
        SOLVER_BASIS[n_], "", _S_EXTRA.get(n_, "") + S_SOLVER)
# 2026-10-07: the HMF row's borate pair, sourced (previously declared by analogy to bicarbonate)
_HMFB = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "hmf_buffer_speciation.json"), encoding="utf-8"))
assert _HMFB["carried_matches"], "run_mediated.jl does not carry the computed borate speciation"
add("4. Solver species diffusivities", "B(OH)4- (aq)", "9.39e-10", "m2 s-1", "derived",
    "Nernst-Einstein D = R T lambda0 / F^2 from the measured limiting conductance, 35.27 S cm2 mol-1 -> 9.39e-10 m2 s-1. "
    "An electrode spectator (s = 0) that the homogeneous step consumes (nu = -1), so its D does not cancel",
    "Corti, Crovetto & Fernandez-Prini, J. Solution Chem. 1980, 9, 617-625",
    "Table III, p. 621: lambda0(B(OH)4-) = 35.27 +/- 0.23 S cm2 mol-1, 25 C",
    _S_EXTRA.get("B(OH)4- (aq)", "") + S_SOLVER)
add("4. Solver species diffusivities", "B(OH)3 (aq)", "1.64e-09", "m2 s-1", "measured",
    "Stokes diaphragm-cell diffusion coefficient of aqueous boric acid, unbuffered, 25 C, at infinite dilution (the "
    "intercept of the authors' fit), as every solver diffusivity is carried. At its 48 mM in the buffer the same fit gives "
    "1.49e-9. An electrode spectator (s = 0) that the homogeneous step releases (nu = +1), so its D does not cancel",
    "Park & Lee, J. Chem. Eng. Data 1994, 39, 891-894",
    "Eq. 8, p. 894: 1e5 D/(cm2 s-1) = 1.640516 - 0.678597 c^(1/2)",
    _S_EXTRA.get("B(OH)3 (aq)", "") + S_SOLVER)
# 2026-10-07: the NHPI row's pyridinium, bracketed by measured acetone cations (data/pyridinium_bracket.py, G-PYH)
_PYH = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "pyridinium_bracket.json"), encoding="utf-8"))
assert (_PYH["carried_inside_brookes"] and not _PYH["counts_move_inside_brookes"] and _PYH["spectators_krumgalz_bitidentical"]
        and _PYH["unstirred_clears_25_at_krumgalz_edge"] and not _PYH["other_cells_at_krumgalz_edge_cross"]), \
    "the pyridinium row's claims no longer hold"
with io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "tier0_ec_matrix.csv"), encoding="utf8") as _fh:
    _N25_UNST = sum(float(r["natural"]) >= 25 for r in _csv.DictReader(_fh))
add("4. Solver species diffusivities", "Pyridinium pyH+ (acetone, NHPI row)", "3e-09", "m2 s-1", "assumption",
    "the proton released by the NHPI row's homogeneous step, carried as pyridinium (pyridine, 2 equiv, takes it) at 33 mM in "
    "the bulk as the N-oxide anion's counter-cation; no limiting conductance of pyridinium in acetone or acetonitrile was "
    "located",
    "Declared: no measurement located. Two assignments of single-ion conductances in anhydrous acetone at 25 C bound it "
    "differently: Brookes, Hotz & Spong, J. Chem. Soc. A 1971, 2415-2420, Table 2, p. 2418, split by measured KSCN "
    "transference numbers, give NH4+ 116.0 (smaller than pyH+, an upper bound; %.2e by Nernst-Einstein) and Me4N+ 93 (of "
    "similar size; %.2e); Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587, Table 4, p. 580, the assignment the "
    "acetone ion table carries, gives NH4+ 89.5 (%.2e)"
    % (_PYH["brookes_bracket_m2s"][1], _PYH["brookes_bracket_m2s"][0], _PYH["krumgalz_nh4_D_m2s"]), "",
    "Inside Brookes's bracket, re-solving the NHPI row moves its seven ceilings by %+.1f to %+.1f pct and no count moves. "
    "On Krumgalz's assignment pyridinium would sit at or below %.2e; there the unstirred cell reaches %.2f mA cm-2, "
    "crossing 25 mA cm-2 at D = %.2e, and no other cell crosses a threshold. The unstirred >=25 count is therefore "
    "conditional on this diffusivity: %d of 50 at the carried value, %d at the Krumgalz edge. Homoconjugation to "
    "(py)2H+ (K_f = 4 in MeCN; Coetzee & Padmanabhan, J. Am. Chem. Soc. 1965, 87, 5005, Table I, p. 5007) would lower "
    "the effective D further, toward the second count."
    % (_PYH["change_inside_brookes_pct"][0], _PYH["change_inside_brookes_pct"][1], _PYH["krumgalz_nh4_D_m2s"],
       _PYH["unstirred_at_krumgalz_edge_mAcm2"], _PYH["unstirred_crosses_25_at_D"], _N25_UNST, _N25_UNST + 1))
_SCH = _HMFB["schemes"]
assert not _SCH["I"]["counts_move"] and not _SCH["II"]["counts_move"] and not _SCH["I"]["printed_medians_move"] \
    and not _SCH["II"]["printed_medians_move"], "a polyborate scheme now moves a count or a printed median"
_BIG = sorted(_SCH["II"]["resolve_by_reactor_pct"], key=lambda a: _SCH["II"]["resolve_by_reactor_pct"][a])[:2]
assert set(_BIG) == {"Unstirred batch", "Stirred batch"}, "the largest polyborate shifts are no longer the batch films"
_HMF_C = [float(r["C_carrier_M"]) for r in _RX50 if r["reaction"] == "HMF -> FDCA (biomass)"][0] * 1000
add("5. Concentrations", "Borate buffer speciation (HMF row)",
    "%.0f / %.0f / %.0f" % (_HMFB["monomers_mM"]["B(OH)4-"], _HMFB["monomers_mM"]["B(OH)3"], _HMFB["monomers_mM"]["Na+"]),
    "mM", "derived",
    "B(OH)4- / B(OH)3 / Na+ of 0.500 M boric acid adjusted to pH 10.00 with NaOH (the exemplar's recipe), from B(OH)3 + "
    "OH- = B(OH)4- at the solution's own ionic strength (%.3f m; log Q11 = %.3f), a_OH from pH and pKw = %.3f with a "
    "Davies activity coefficient, Na+ by charge balance" % (_HMFB["ionic_strength"], _HMFB["log_Q11_at_I"], _HMFB["pKw_declared"]),
    "Mesmer, Baes & Sweeton, Inorg. Chem. 1972, 11, 537-543, DOI 10.1021/ic50109a023; Cardiel, Taitt & Choi, ACS "
    "Sustainable Chem. Eng. 2019, 7, 11138-11149, DOI 10.1021/acssuschemeng.9b00203 (the buffer recipe)",
    "abstract p. 537 and Table III, p. 541 (log Q11 against T and I); Table VI, p. 542 (polyborates); Cardiel et al., "
    "Experimental",
    "Polyborates are not carried. Mesmer's Table VI quotients, fitted in 1 m KCl at 50-200 C and so extrapolated here to "
    "25 C, evaluated at this solution's pH and ionic strength, put %.0f pct of the boron in polyborates on scheme I (its Q4,2 "
    "with the Q2,1 and Q3,1 expressions the table gives, which are fitted on scheme II) and %.0f pct on scheme II. Re-solving the HMF row at each composition, the polyborate charge lumped as an inert anion, "
    "moves its seven ceilings by %+.2f to %+.2f pct (scheme I) and %+.1f to %+.2f pct (scheme II). The large shifts are "
    "the two batch films, where lumping removes the base capacity the polyborates actually carry, so these runs bound the "
    "omission from the pessimistic side; no count and no printed median moves in either. Sodium, the buffer's cation, is "
    "%.0f times the %.0f mM ACT carrier as carried and about %.0f times with polyborates."
    % (_SCH["I"]["fraction_of_boron_pct"], _SCH["II"]["fraction_of_boron_pct"], _SCH["I"]["resolve_pct"][0],
       _SCH["I"]["resolve_pct"][1], _SCH["II"]["resolve_pct"][0], _SCH["II"]["resolve_pct"][1],
       _HMFB["Na_over_carrier_monomer"] * 40.0 / _HMF_C, _HMF_C,
       min(_SCH[k]["carried_mM"]["Na+"] for k in _SCH) / _HMF_C))
for _nm, _val, _case, _meth, _basis, _cond in [
 ("Cl- (6:1 MeCN/aq HCl, thioether row)", "2.3e-09", "cl34",
  "the chloride mediator of the thioether row in its own medium, 6:1 MeCN / 0.1 M aqueous HCl (0.48 mPa s), for which "
  "no limiting conductance is tabulated",
  "Declared: no measurement in this medium. The pure-solvent values bracket it when carried to the medium's viscosity by "
  "Walden's rule: Krumgalz 1983, Table 4, pp. 580-581, lambda0(Cl-, MeCN) = 100.4 S cm2 mol-1 (2.67e-9 by "
  "Nernst-Einstein) gives 2.06e-9, and the aqueous 2.03e-9 (CRC 97th ed., p. 5-75) gives 3.77e-9", False),
 ("Br- (1:1 H2O/MeCN, bromination row)", "2.08e-09", "br46",
  "the bromide mediator of the arene-bromination row in its own medium, 0.5 M aqueous NaBr diluted 1:1 with MeCN "
  "(0.835 mPa s), carried at the aqueous value; no limiting conductance is tabulated for the mixture",
  "Declared: the aqueous value (CRC 97th ed., p. 5-75) carried into the mixture. The pure-solvent values bracket it when "
  "carried to the medium's viscosity by Walden's rule: Kalugin 2019, Table 3, p. 28, lambda0(Br-, MeCN) = 102.00 S cm2 "
  "mol-1 (2.72e-9) gives 1.20e-9, and the aqueous 2.08e-9 gives 2.22e-9 (with Br2, Cussler p. 127, carried likewise to "
  "1.26e-9)", True)]:
    _lo, _mvl, _mdl = _mxf(_case + "_lo"); _hi, _mvh, _mdh = _mxf(_case + "_hi")
    _ends = ("no threshold count or architecture median moves at either end" if not (_lo["count_moves"] or _hi["count_moves"]
             or _lo["median_moves"] or _hi["median_moves"]) else "at the lower end %s and %s moves; at the upper end %s and %s "
             "moves" % (_mvl, _mdl, _mvh, _mdh))
    _sens = ("Re-solved at both ends of the bracket: at the lower end the row's ceilings move x%.3f-x%.3f, at the upper "
             "end x%.3f-x%.3f, and its lowest cell is %.1f and %.1f mA cm-2; %s. Walden's rule is itself approximate for ions (see the NH4+ row), so the ends are a "
             "bracket rather than a derivation."
             % (_lo["ratio_lo"], _lo["ratio_hi"], _hi["ratio_lo"], _hi["ratio_hi"], _lo["lowest_cell_mAcm2"],
                _hi["lowest_cell_mAcm2"], _ends))
    if _cond:
        assert _lo["count_moves"], "the bromination bracket no longer moves a count; reword its row"
        _sens += (" The published count that moves is therefore conditional on where this declared value sits in its "
                  "bracket; the carried value is the aqueous one, near the upper end.")
    else:
        assert not _lo["count_moves"] and not _hi["count_moves"], "the thioether bracket now moves a count; reword its row"
    add("4. Solver species diffusivities", _nm, _val, "m2 s-1", "assumption", _meth, _basis, "", _sens)
_NP_BU4NBF4 = [r for r in _EIONS if r["cation"] == "Bu4N+" and r["anion"] == "BF4-" and r["electrolyte"].endswith("/MeCN")][0]
_QA_SENT = {
    "Q+": ("The generic supporting cation Q+ of the EC' specs of the %s rows, and the class default for a declared "
           "supporting cation of the Nernst-Planck ion table (see the next-but-one row). Where Bu4N+ itself appears in "
           "acetonitrile, the Nernst-Planck layer does not use this value: it carries %.3e m2 s-1 (%s), and Kalugin's "
           "lambda0 = 61.90 S cm2 mol-1 gives 1.648e-9 by Nernst-Einstein. Q+ is a spectator wherever it appears "
           "(s = 0, nu = 0): with zero flux at the limit its diffusivity cancels from its own conservation equation, so "
           "it does not enter i_lim (the supporting-ion row measures that zero). "
           % (" and ".join(_short(l) for l in _spec_users("Q+")), float(_NP_BU4NBF4["D_cat"]),
              _NP_BU4NBF4["D_cat_basis"].split(";")[1].strip() if ";" in _NP_BU4NBF4["D_cat_basis"] else _NP_BU4NBF4["D_cat_basis"])),
    "A-": ("The generic supporting anion A- of the EC' spec%s of the %s row%s, and the class default for a declared "
           "supporting anion of the Nernst-Planck ion table (see the next row). Where BF4- itself appears in "
           "acetonitrile, the Nernst-Planck layer does not use this value: it carries %.3e m2 s-1 (Gong et al., Energy "
           "Environ. Sci. 2015, 8, 3515-3530, Table 2, p. 3518, lambda0 = 108.5), and Kalugin's lambda0 = 109.20 S cm2 "
           "mol-1 gives 2.908e-9 by Nernst-Einstein. A- is a spectator wherever it appears (s = 0, nu = 0), so its "
           "diffusivity does not enter i_lim. "
           % ("s" if len(_spec_users("A-")) > 1 else "", " and ".join(_short(l) for l in _spec_users("A-")),
              "s" if len(_spec_users("A-")) > 1 else "", float(_NP_BU4NBF4["D_an"]))),
}
add("4. Solver species diffusivities", "Bu4N+/Q+ (organic)", "1e-09", "m2 s-1", "assumption",
    "a round value below the page-anchored lambda0(Bu4N+, MeCN) = 61.90 (1.648e-9 m2 s-1 by Nernst-Einstein), used "
    "for the generic supporting cation of the EC' specs and as the class default of the declared supporting-cation slots",
    "Declared class default, set below the page-anchored lambda0(Bu4N+, MeCN) = 61.90 S cm2 mol-1 of " + KALUGIN,
    "", _QA_SENT["Q+"] + S_SOLVER)
add("4. Solver species diffusivities", "BF4-/generic A- (organic)", "1.5e-09", "m2 s-1", "assumption",
    "a round value below the page-anchored lambda0(BF4-, MeCN) = 109.20 (2.908e-9 m2 s-1 by Nernst-Einstein), used "
    "for the generic supporting anion of the EC' specs and as the class default of the declared supporting-anion slots",
    "Declared class default, set below the page-anchored lambda0(BF4-, MeCN) = 109.20 S cm2 mol-1 of " + KALUGIN,
    "", _QA_SENT["A-"] + S_SOLVER)
def _decl_census():
    """The declared supporting-ion slots of data/electrolyte_ions.csv, counted at build time: a slot is declared when its
    basis begins 'DECLARED'; it sits at the class default when its D is 1.0e-9 (cation) or 1.5e-9 (anion)."""
    dflt, other = [], []
    for r in _EIONS:
        for side, ion, D, b, cls in (("cat", r["cation"], r["D_cat"], r["D_cat_basis"], 1.0e-9),
                                     ("an", r["anion"], r["D_an"], r["D_an_basis"], 1.5e-9)):
            if not b.upper().startswith("DECLARED"):
                continue
            med = r["electrolyte"].split("/", 1)[1] if "/" in r["electrolyte"] else r["electrolyte"]
            at_default = abs(float(D) - cls) <= 1e-15
            if b.upper().startswith("DECLARED CLASS DEFAULT") != at_default:
                raise SystemExit("electrolyte_ions.csv labels %s in %s as %r at D = %s, which is %s the class default"
                                 % (ion, med, b.split(" (")[0], D, "not" if not at_default else ""))
            (dflt if at_default else other).append((ion, med, float(D)))
    return dflt, other
_DC_DEF, _DC_OTH = _decl_census()
# ion/solvent pairs counted exactly as data/sensitivity_unsourced_D.py counts them (the medium named in each basis string)
_DC_PAIRS = set()
for _r in _EIONS:
    for _b in ("D_cat_basis", "D_an_basis"):
        _m = re.search(r"no lambda0 for (\S+?)(?: \([^)]*\))? in (\S+) in", _r[_b])   # a basis may qualify the ion
        if _m and _r[_b].upper().startswith("DECLARED"):
            _DC_PAIRS.add((_m.group(1), _m.group(2)))
_DC_N = len(_DC_DEF) + len(_DC_OTH)
if _UD["n_slots"] != _DC_N or _UD["n_pairs"] != len(_DC_PAIRS):
    raise SystemExit("ERROR: results/unsourced_D_sensitivity.json perturbed %d slots / %d pairs but data/electrolyte_ions.csv now "
          "declares %d / %d; re-run data/sensitivity_unsourced_D.py (G-DSENS) and rebuild, or the supporting-ion row's "
          "sensitivity describes a different slot set from its value column" % (_UD["n_slots"], _UD["n_pairs"], _DC_N,
                                                                                 len(_DC_PAIRS)))
add("4. Solver species diffusivities", "Supporting-ion diffusivities without conductance data",
    "%d slots, %d ion/solvent pairs" % (_DC_N, len(_DC_PAIRS)), "m2 s-1", "assumption",
    "the supporting-electrolyte cation and anion slots of the 50-row table for which no limiting "
    "conductance is tabulated in the row's medium, counted from data/electrolyte_ions.csv at build time: %d declared "
    "slots, %d at the class default of the two rows above (1.0e-9 for a cation, 1.5e-9 for an anion) and %d at another "
    "declared value, each recording its basis beside the value" % (len(_DC_DEF) + len(_DC_OTH), len(_DC_DEF), len(_DC_OTH)),
    "Declared: no lambda0 for these ion/solvent pairs (tosylate, BF4-, PF6-, HSO4-, carboxylates, Li+ and Br- in THF, "
    "and the like, in methanol, THF, acetone, HFIP, acetic acid and acetonitrile; tosylate in water) in "
    "Krumgalz 1983 Table 4 or CRC 97th ed. pp. 5-75/5-76. Of the %d declared slots, %d take the class default of the two "
    "rows above; the other %d carry a declared value of another origin, recorded slot by slot with its basis in the ion "
    "table (%s). A supporting ion "
    % (len(_DC_DEF) + len(_DC_OTH), len(_DC_DEF), len(_DC_OTH),
       "; ".join("%s in %s, %.3g" % o for o in sorted(set(_DC_OTH)))) +
    "carries no flux, so under local electroneutrality its diffusivity shapes the potential profile "
    "but does not enter the limiting current; the default is therefore a choice that costs nothing "
    "reported, and the sensitivity beside it states the measured size of that nothing.",
    "",
    "All %d slots divided by 3 together, then all multiplied by 3 together, re-solving the full "
    "%d-cell Nernst-Planck layer each time: the largest relative change in any cell is %s "
    "(divided) and %s (multiplied), and no threshold count in any of the %s architectures "
    "moves. The zero is the physics, not a coincidence -- a species with zero flux drops out of "
    "its own conservation equation -- and the sweep exists as a regression test: a non-zero here "
    "would mean a supporting-ion diffusivity had started feeding a reacting species."
    % (_UD["n_slots"], 50 * _N_ARCH, _relfmt(_UD["max_rel_change"]["div3"]), _relfmt(_UD["max_rel_change"]["mul3"]),
       _numword(_N_ARCH)))
# chemistry audit 2026-10-06: the medium rows split in two. Four are carried at k = 0 and G-ZSENS re-solves them; the Ni
# homocoupling is carried at a finite rate constant and G-HOMOZ re-solves it at the alternatives at that constant.
_HZ = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "homocoupling_charge_sensitivity.json"), encoding="utf8"))
# chemistry audit, pass 4: the cross-electrophile coupling is medium-confidence and published at its sourced k, so G-ZSENS's
# k = 0 re-solve is not its published layer; G-XECZ re-solves it at that k
_XZ = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "xec_charge_sensitivity.json"), encoding="utf8"))
_ARCHNM = {"natural": "unstirred", "stirred": "stirred", "flow": "recirculating-flow", "anec": "ANEC", "micro": "microfluidic",
           "rde": "RDE", "rce": "rotating-cylinder"}


def _zs_sens():
    zs_rows = {r["reaction"] for r in _ZS["rows"]}
    swept = [r for r in _CC_MED if r["reaction"] in zs_rows]
    rest = [r["reaction"] for r in _CC_MED if r["reaction"] not in zs_rows]
    if rest != [_HZ["reaction"]]:
        raise SystemExit("medium-confidence charges outside both sweeps: %s" % rest)
    mv = lambda z: "; ".join("the %s >=%d mA cm-2 count %d -> %d" % (_ARCHNM[m["arch"]], m["threshold"], m["from"], m["to"])
                             for m in _HZ["count_moves"][z]) or "no threshold count"
    xmv = lambda z: "; ".join("the %s >=%d mA cm-2 count %d -> %d" % (_ARCHNM[m["arch"]], m["threshold"], m["from"], m["to"])
                              for m in _XZ["count_moves"][z]) or "no threshold count moves"
    xz = ("%s of them are published in that layer; the cross-electrophile coupling is published at its sourced rate "
          "constant (%g M-1 s-1), and re-solved there its ceilings move x%.3f-x%.3f at z = -1 (%s), x%.3f-x%.3f at z = +1 (%s) "
          "and x%.3f-x%.3f at z = +2 (%s). "
          % (_numword(len(swept) - 1).capitalize(), _XZ["k_adopted"], _XZ["ratio"]["-1"][0], _XZ["ratio"]["-1"][1], xmv("-1"), _XZ["ratio"]["1"][0], _XZ["ratio"]["1"][1],
             xmv("1"), _XZ["ratio"]["2"][0], _XZ["ratio"]["2"][1], xmv("2")))
    assert _XZ["reaction"] in [r["reaction"] for r in swept], "the cross-coupling is no longer among the k = 0-swept medium rows"
    return ("The %s medium-confidence rows other than the homocoupling were each re-solved at every alternative charge in %s "
            "in the k = 0 layer, the whole %d-cell layer each time: the largest change in any of their ceilings there is %.1f "
            "pct, and no threshold count in any of the %s architectures moves at any alternative. %sThe cathodic Ni homocoupling is carried at the neutral charge of its "
            "precursor, NiBr2bpy, but its exemplar writes the complex it reduces as Nibpy2+; re-solved at its adopted rate "
            "constant (%g M-1 s-1) at z = +1 its ceilings rise %.1f-%.1f-fold, moving %s, and at z = +2 %.1f-%.1f-fold, moving %s. "
            "It is the one carrier charge in the model on which a published count depends."
            % (_numword(len(swept)), "{" + ", ".join(str(a) for a in _ZS["alternatives"]) + "}", 50 * _N_ARCH,
               _ZS["worst_ceiling_change_pct"], _numword(_N_ARCH), xz, _HZ["k_adopted"], _HZ["ratio"]["1"][0], _HZ["ratio"]["1"][1],
               mv("1"), _HZ["ratio"]["2"][0], _HZ["ratio"]["2"][1], mv("2")))


add("4. Solver species diffusivities", "Carrier charge z (all 50 rows)",
    "z = 0 on %d rows, -1 on %d, -2 on %d, +2 on %d" % tuple(sum(1 for r in _CC if r["z_carrier"] == z) for z in ("0", "-1", "-2", "2")),
    "-", "assumption",
    "the charge of the carrier as it reaches the electrode, read from each exemplar paper; it "
    "decides whether the migration term acts on the carrier (a charged carrier in its own salt is "
    "lifted above its Fick bound, a neutral one is not). %d of 50 are read directly from the "
    "exemplar's written species (high confidence); %d are metal complexes carried neutral at medium "
    "confidence: %s"
    % (len(_CC) - len(_CC_MED), len(_CC_MED), "; ".join("%s -- %s" % (r["reaction"], r["basis"][:140]) for r in _CC_MED)),
    "Declared per row from the exemplar's own written species (each row's source is the exemplar "
    "cited beside it in Table S2); the value is printed in Table S2, column z, with medium-confidence "
    "rows marked *",
    "",
    _zs_sens())
add("4. Solver species diffusivities", "All 50 carrier D values", "(Table S2)", "m2 s-1", "derived",
    "Wilke-Chang / Nernst-Einstein / Stokes-Einstein per row by the category-3 methods; the route "
    "and citation for each row are given in Table S2", "Table S2", "",
    "See the Wilke-Chang row: +/-25 pct displaces log10 i_lim by +/-0.10.")
add("4. Solver species diffusivities", "%d mediated-spec substrate D values" % _N_MED, "(S5.5)", "m2 s-1",
    "derived",
    "All but one by Wilke-Chang on named structures and one (ethylene/H2O) measured, all generated by "
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
    "1-decene/MeCN-H2O, anisole/H2O-MeCN, anisole/AcOH-HCOOH, and for the three rows carried as "
    "mediated since 2026-10-05, N-(pivaloyloxy)biphenyl-2-carboxamide/MeCN, phenyl vinyl sulfone/"
    "H2O-MeCN and thioanisole/MeCN-H2O (a declared surrogate: the exemplar draws its thioether "
    "without naming it). Five were confirmed by exact "
    "reproduction of the carried value (ratios 1.000, 0.997, 1.000, 1.002, 0.999); the three "
    "corrected ones were read out of the exemplar PDFs, because a 3-significant-figure D does not "
    "identify a structure uniquely -- 4-fluorobenzamide and cyclopentanecarboxamide both reproduce "
    "2.00e-9 to 3 s.f.",
    WC55 + " -- applied to the named surrogate structures; the ethylene row carries the measured "
    "Cussler value instead (its own row above)",
"each structure is the model substrate its exemplar names: " + "; ".join(
        "%s (%s)" % (r["substrate"], r["reaction"].split(" (")[0]) for r in _MSUB),
    "Swept together over x%.2f to x%.2f (wider than the +/-25 pct this registry "
    "carries as its working property error), re-solving the full "
    "%d-cell mediated matrix at each scale: %s. The mediated cell closest to the 25 mA cm-2 "
    "threshold is %s in the %s, at %.2f mA cm-2 (%.1f pct away)%s"
    % (min(_DSB["scales"]), max(_DSB["scales"]),
       _N_MED * len(_DSB["base_counts"]),
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
def _ec_support():
    """Spectator ions of the EC' specs (no electrode and no homogeneous stoichiometry): supporting salts and the
    counter-ions of the carrier salts. A spec that carries a buffer (a charged species the homogeneous step consumes
    or releases at >= 0.1 M) has its spectator counter-ion reported separately as the buffer's."""
    sup, buf = [], []
    for lab, sp in _SPECS.items():
        buffered = any(x["s"] == 0 and x["nu"] != 0 and x["z"] != 0 and x["c"] >= 100.0 and x["name"] != "Sub" for x in sp)
        for x in sp:
            if x["s"] == 0 and x["nu"] == 0 and x["name"] != "Sub":
                (buf if buffered else sup).append((x["c"], x["name"], lab))
    return sorted(sup), sorted(buf)
_ECS_SUP, _ECS_BUF = _ec_support()
add("5. Concentrations", "Supporting-electrolyte concentrations in EC' specs",
    "%.4g-%.1f" % (_ECS_SUP[0][0] / 1000.0, _ECS_SUP[-1][0] / 1000.0), "M",
    "measured",
    "matched to each verified exemplar's electrolyte; buffer compositions (carbonate pH 8.5, borate "
    "pH 10, HClO4) taken from the cited experimental sections. Read from the specs of julia/run_mediated.jl at build time",
    "Table S2 per-row citations", "Table S2, final column",
    "The spectator ions of the %d EC' specs (no electrode and no homogeneous stoichiometry: the supporting salts and the "
    "counter-ions of the carrier salts) run from %.1f mM (%s, %s) to %.1f M (%s, %s). The two buffered specs add the "
    "buffer's counter-ion, up to %.1f M (%s, %s). A spectator carries no flux at the limit, so these concentrations set the "
    "film potential, not i_lim. One acid concentration is a choice inside a reported range rather than a reading: the "
    "Wacker-Tsuji spec carries 150 mM HClO4, mid-range of the 0.015-0.36 M perchloric acid its exemplar's experimental "
    "section uses (Miller & Wayner, Can. J. Chem. 1992, 70, 2485)."
    % (len(_SPECS), _ECS_SUP[0][0], _ECS_SUP[0][1], _short(_ECS_SUP[0][2]), _ECS_SUP[-1][0] / 1000.0, _ECS_SUP[-1][1],
       _short(_ECS_SUP[-1][2]), _ECS_BUF[-1][0] / 1000.0, _ECS_BUF[-1][1], _short(_ECS_BUF[-1][2])))
add("5. Concentrations", "Propylene C_sat (aq, 1 atm)", "5.67e-3", "M", "derived",
    "Henry's law: C_sat = H_cp * p = 5.6e-5 mol m-3 Pa-1 * 101325 Pa = 5.67 mol m-3 = 5.67 mM. "
    "corrected 2026-08-22 on retrieval of the source. This row previously used H_cp = 4.9e-5, "
    "giving 5.0 mM, and cited the 2015 edition of Sander's compilation -- which was never "
    "retrieved. the edition now held lists more than twenty propene entries; the value used is the "
    "first-listed literature-review (type L) entry, 5.6e-5 mol m-3 Pa-1, Plyasunov and Shock (2000). "
    "Where 4.9e-5 came from could not be established, "
    "so it is withdrawn rather than defended. the +14 pct move is safe and moves no reported "
    "current: this row bounds the gas-liquid delivery duty, not the electrode current, because "
    "%.1f pct of the generated oxidant is exported from the film (see the sensitivity)" % _EX["exported_pct"],
    "Sander, 'Compilation of Henry's law constants (version 5) for water as solvent', "
    "Atmos. Chem. Phys. 2023, 23, 10901-12440, DOI 10.5194/acp-23-10901-2023",
    "propene, H_cp = 5.6e-5 mol m-3 Pa-1 at 298 K, Plyasunov and Shock (2000), the first-listed "
    "literature-review (type L) value; the measured (type M) entries are 5.4e-5 (Maassen 1995; Reichl "
    "1995) and 4.8e-5 (McAuliffe 1966)",
    "At the declared rate constant of the HOCl pathway (k = %g M-1 s-1) the ex-cell propylene epoxidation "
    "entry is bulk-reaction-limited: at %.0f mA cm-2 the solver shows %.1f pct of the generated oxidant "
    "exported from the film (%.1f pct on a %.0f um film), so "
    "this row bounds the gas-liquid delivery duty, not the electrode current. It enters the solve "
    "through the reaction layer x_k = (D/kC)^(1/2) = %.0f um and the planar propylene cap "
    "%.2f mA cm-2. The measured entries of the same compilation lie 4-14 pct below the carried "
    "value; a 14 pct change in C_sat moves x_k by %.0f pct (x_k ~ C^-1/2) and the in-film share by half a "
    "percentage point. Faster Cl2 constants raise the in-film share (\u00a7S4.2)." % (_EX["k_M"], _EX["i_op_mAcm2"], _EX["exported_pct"], _EX["exported_pct_half_delta"],
                            _EX["half_delta_um"], _EX["x_k_um"], _EX["i_cap_P_mAcm2"], 100 * ((1 / 0.86) ** 0.5 - 1)))
add("5. Concentrations", "O2 C_sat (air-saturated water, 25 C)", "2.66e-4", "M", "derived",
    "mole-fraction solubility of O2 at 298.15 K and 101.325 kPa partial pressure, X1 = 2.293e-5, times the "
    "molar concentration of water (997.05 g/L / 18.015 g/mol = 55.345 mol/L) and the mole fraction of O2 in "
    "dry air (0.2095): 2.293e-5 x 55.345 x 0.2095 = 2.66e-4 M. The carrier concentration of the "
    "oxygen-mediated Giese row, whose medium is water/acetonitrile 2:1; the aqueous value is a declared "
    "stand-in for that mixture",
    CRC, "Sect. 5, 'Solubility of Selected Gases in Water' (Gevantman), p. 5-134, Oxygen at 298.15 K: X1 = 2.293e-5",
    "Oxygen is more soluble in acetonitrile than in water, so the aqueous value is a lower estimate for the "
    "mixed medium. The row's rate constant is fixed by its exemplar's own current at this concentration, "
    "so what the row carries is the product C k^(1/2): a higher solubility lowers the inferred rate constant "
    "in proportion and leaves the ceiling where it is wherever the film is thicker than the reaction layer. The "
    "dry-air basis omits water vapour (3.17 kPa at 25 C), which lowers air-saturated water's O2 by 3 pct, to 2.58e-4 M; "
    "the inferred rate constant absorbs that in the same way.")
# n: the electrons each row carries. Since 2026-10-05 every row's overall reaction is balanced in
# data/reaction_stoichiometry.csv (atoms and charge asserted by build_reaction_stoichiometry.py) and
# printed as Table S10, so this row is computed from that table and from the published matrix.
# The sentence this replaces said the two chain rows stay "below 25 mA cm-2 in every architecture"
# at n = 1; on the seven-archetype matrix that is false for the Diels-Alder row, and nothing had
# been checking it.
def _n_row_sens():
    kinds = {}
    for r in _STOI:
        kinds.setdefault(r["kind"], []).append(r["reaction"])
    with io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "tier0_ec_matrix.csv"), encoding="utf8") as fh:
        M = {r["reaction"]: r for r in _csv.DictReader(fh)}
    arch = [k for k in next(iter(M.values())).keys() if k not in ("class", "reaction", "carrier")]
    names = {"natural": "unstirred", "stirred": "stirred", "flow": "recirculating-flow", "anec": "ANEC",
             "micro": "microfluidic", "rde": "rotating-disk", "rce": "rotating-cylinder"}
    da = next(r for r in _STOI if r["kind"] == "chain" and r["ceiling_set_by"] == "substrate")
    iso = next(r for r in _STOI if r["kind"] == "chain" and r["ceiling_set_by"] == "catalyst")
    n_da = float(da["n_substrate"]); hi = 0.5 / n_da                     # the paper's own top charge, 0.5 F/mol
    v = {a: float(M[da["reaction"]][a]) for a in arch}
    cross25 = [a for a in arch if v[a] < 25 <= v[a] * hi]; cross50 = [a for a in arch if v[a] < 50 <= v[a] * hi]
    with io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "catalyst_ec_sourced.csv"), encoding="utf8") as fh:
        plateau = max(float(r["i_saveant_mAcm2"]) for r in _csv.DictReader(fh)
                      if r["reaction"] == iso["reaction"] and float(r["k_M"]) > 0)
    if plateau >= 25:
        raise SystemExit("the isomerization row's kinetic plateau (%.1f mA cm-2) no longer keeps it below 25; "
                         "rewrite the n_carrier sensitivity rather than the number" % plateau)
    neutral = kinds.get("paired", []) + kinds.get("charge-consuming", [])
    txt = ("The overall reaction of every row is balanced in Table S10, atoms and charge, with its electrode step: %d of the "
           "fifty take n from that stoichiometry and are not in doubt. %s are redox-neutral couplings (%s), whose electrode "
           "count is the cycle's own: one electron at each electrode per turnover. Two are chain processes, redox-neutral overall, for which n "
           "is the charge the exemplar passes per substrate: %g F mol-1 for the radical-cation Diels-Alder reaction and "
           "%g F mol-1 for the cobalt-hydride isomerization, the charge passed for the compound that row carries. i_lim is "
           "linear in n. "
           % (len(kinds.get("stoichiometric", [])) + len(kinds.get("ex-cell", [])), _numword(len(neutral)).capitalize(),
              "; ".join(n.split(" (")[0] for n in neutral), n_da, float(iso["n_substrate"])))
    if cross25:
        txt += ("Across the Diels-Alder paper's own range, 0.05-0.5 F mol-1, that row reaches %.0f-%.0f mA cm-2 in the %s "
                "cells at the top of the range, so the >=25 mA cm-2 count of %s is conditional on the charge carried "
                "(one entry higher at 0.5 F mol-1)%s. "
                % (min(v[a] * hi for a in cross25), max(v[a] * hi for a in cross25),
                   ", ".join(names[a] for a in cross25),
                   "each of those architectures" if len(cross25) > 1 else "that architecture",
                   "; no >=50 mA cm-2 count moves" if not cross50 else
                   ", and the >=50 mA cm-2 count of the %s likewise" % ", ".join(names[a] for a in cross50)))
    else:
        txt += "Across the Diels-Alder paper's own range, 0.05-0.5 F mol-1, that row crosses no threshold in any architecture. "
    txt += ("The isomerization row is held below 25 mA cm-2 at any substrate count by its kinetic plateau, %.1f mA cm-2." % plateau)
    return txt
add("5. Concentrations", "n_carrier (electrons per carrier turnover)",
    "0.1 - 6.0 (per reaction; see Tables S2 and S10)", "-", "assumption",
    "N is one of the four factors of i_lim = n F D C / delta and is exactly as linear in i_lim as C is. "
    "Assigned per reaction from the balanced reaction of Table S10 as written in the source, which is a "
    "reading of the mechanism, not a measurement",
    "the balanced reaction of each exemplar, as reported (Table S10)", "",
    _n_row_sens())
add("5. Concentrations", "Trace initializations (Med_ox, H+ in aprotic)",
    "1e-5 x C_med; 1e-3 mol m-3", "mol m-3", "assumption",
    "nonzero Dirichlet and initial values for the log-concentration degrees of freedom; a solver "
    "necessity, not a physical claim", "declared solver setting", "",
    _trace_sentence())

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
# The Onsager slope for MeCN is READ from results/kappa_derivation.json (data/derive_kappa.py), whose
# eta comes from data/solvents.csv. It used to be typed (S = 358.7, negative above 0.228 M) on the
# retired eta = 0.343. Lambda0(Bu4NBF4, MeCN) = lambda0(Bu4N+) + lambda0(BF4-) = 61.90 + 109.20, both
# Kalugin et al. Table 3, p. 28.
with io.open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "results",
                           "kappa_derivation.json"), encoding="utf8") as _fh:
    _KD = _json.load(_fh)
_KD_MECN = [r for r in _KD["rows"] if r["solvent"] == "MeCN"][0]
_KD_L0 = 61.90 + 109.20
_KD_S = _KD_MECN["B1"] * _KD_L0 + _KD_MECN["B2"]
_KD_CNEG = (_KD_L0 / _KD_S) ** 2
QAM_METH = ("no measured conductivity for this exact salt / solvent / concentration was located. "
            "The inherited citation was a limiting-conductivity table (Izutsu, 2nd ed.), which "
            "cannot supply kappa at 0.03-1 M at any concentration in this registry: for "
            "Bu4NBF4/MeCN the Onsager limiting law Lambda = Lambda0 - S sqrt(c), with "
            "Lambda0 = %.1f (Kalugin Table 3, p. 28) and S = %.1f computed from eta = %.3f mPa s and a "
            "recalled, unretrieved eps = %.2f, goes negative above %.3f M, and the Lee-Wheaton / "
            "Fuoss-Justice extension reaches only ~0.02 M. The citation did not support the value and "
            "has been withdrawn" % (_KD_L0, _KD_S, _KD_MECN["eta_mPas"], _KD_MECN["eps"], _KD_CNEG))
# B12. The earlier promise -- that the Dorn SI "may convert 8-10 of these rows to state A in a
# single pass" -- is NOT supported by what was retrieved and has been corrected. Dorn's Table 3
# (p. 1499) contains exactly FOUR Casteel-Amis fits: ACN/(C2H5)4NBF4, ACN/(C4H9)4NBF4, MeOH/NaI and
# MeOH/KSCN. Only one matches a registry salt (Bu4NBF4/MeCN), and it has already been adopted here
# on five rows. NaI and KSCN in MeOH appear in no registry row.
# The 3.0 M LiBr/THF row, computed (chemistry audit, pass 5). Das's LiBr columns are carried as printed (Table 1, p. 949:
# 10^4 c / mol dm-3 and Lambda / S cm2 mol-1); every number the row derives from them, from the band and from the thermal
# model is computed here, so the row cannot state two values for one quantity.
_DAS_C = [115.5, 133.2, 154.0, 177.8, 205.3, 237.1, 273.8, 316.2, 365.2, 421.7, 486.9, 562.3, 649.4, 749.9, 1000.0,
          1333.5, 1778.3, 2053.5, 2440.6, 3162.3]
_DAS_L = [0.1999, 0.1900, 0.1826, 0.1805, 0.1795, 0.1796, 0.1809, 0.1833, 0.1871, 0.1924, 0.1933, 0.2080, 0.2188, 0.2320,
          0.2679, 0.3219, 0.4083, 0.4602, 0.5612, 0.8100]
_DAS_LOC = "Das, J. Solution Chem. 2008, 37, 947-955, Table 1, p. 949, LiBr columns"
_LB_FLOOR, _LB_TOP, _LB_VAL = 0.0206, 0.66, 0.30
_LB_TOP_RAW = 0.658   # what the ohmic differencing returns; the band's upper end is that value to its printed precision, 6.6
_NAOH_BAND = (174.0, 182.0)          # mS/cm, the CRC p. 5-71 route as Table S4 constructs it (20 C table, 25 C correction)          # S/m: Lee's state-B floor, the rounding-limit top, the carried value


def _das_fit(c0):
    xs = [_math.log(c * 1e-4) for c in _DAS_C if c * 1e-4 >= c0 - 1e-12]
    ys = [_math.log(l * c * 1e-4) for c, l in zip(_DAS_C, _DAS_L) if c * 1e-4 >= c0 - 1e-12]
    n_ = len(xs); mx = sum(xs) / n_; my = sum(ys) / n_
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return slope, _math.exp(my + slope * (_math.log(3.0) - mx)), n_


def _libr_thf_sens():
    c_top, k_top = _DAS_C[-1] * 1e-4, _DAS_L[-1] * _DAS_C[-1] * 1e-4          # mol/L, mS/cm
    k_01 = [l * c * 1e-4 for c, l in zip(_DAS_C, _DAS_L) if abs(c - 1000.0) < 1e-9][0]
    fits = [(c0,) + _das_fit(c0) for c0 in (0.05, 0.10, 0.15)]
    n_branch = fits[0][1]
    k_cont_top = k_top * (3.0 / c_top) ** n_branch
    n_need = _math.log(3.0 / k_top) / _math.log(3.0 / c_top)
    n_carried = _math.log(3.0 / k_01) / _math.log(3.0 / 0.1)
    thf = [r for r in _TM.SOLVENTS if r[0] == "THF"][0]
    rho_thf = float(next(r for r in csv.DictReader(io.open(_os.path.join(_HERE_D, "solvents.csv"), encoding="utf8"))
                         if r["solvent"] == "THF")["rho"])
    # Peters/Baran Science 2019 SI p. S15 (and S17): 'LiBr (83.4 g, 1.0 mol)' ... 'THF (320 mL) was added'. The printed
    # mass is the quantity; 1.0 mol is its rounding. M(LiBr) from the IUPAC standard atomic weights, Li 6.94 + Br 79.904.
    n_libr = 83.4 / (6.94 + 79.904)
    thf_per_li = 320.0 * rho_thf / 72.106 / n_libr
    thf_per_li_das = 1000.0 * rho_thf / 72.106 / c_top
    rde_flip = 10 * _thf_flip("RDE 1600 rpm") * _LB_VAL
    rce_flip = 10 * _thf_flip("rotating cyl. 3000 rpm") * _LB_VAL
    stk = _TH_STACK
    # Liquid-cooling breakpoints: for each architecture whose THF duty needs liquid cooling at the carried value, the
    # conductivity below which U'_req exceeds the best cooler that architecture's own construction gives (U_liquid hi).
    # _TH_RX[i] and _TM.REACTORS[i] are the same reactor (the labels differ only by the relabel above).
    _liq = []
    for _r, _R in zip(_TH_RX, _TM.REACTORS):
        _top = _TM.U_liquid(_R)[1]
        _ureq = _TM.U_required(_r[4], _LB_VAL, _r[1], thf[3])
        if not (_TM.U_passive(_r[2], _r[3]) < _ureq <= _top):
            continue
        lo, hi = 1e-4, _LB_VAL
        for _ in range(200):
            m = (lo * hi) ** 0.5
            if _TM.U_required(_r[4], m, _r[1], thf[3]) > _top:
                lo = m
            else:
                hi = m
        _liq.append((_r[0], (lo * hi) ** 0.5, _top))
    _liq.sort(key=lambda t: -t[1])
    # the boil-off multiples of the three centimetre-gap cells that pass at the carried value (unstirred, stirred, flow)
    _cmg = [_kappa_multiple(_LB_VAL, thf[3], r[0]) for r in _TH_OPEN
            if not ("RDE" in r[0] or "rotating" in r[0]) and _th_margin(_LB_VAL, thf[3], r) >= 1.0]
    assert len(_cmg) == 3 and all(_LB_FLOOR / _LB_VAL < m < 1 for m in _cmg), _cmg
    # the row says the microfluidic, rotating-cell and stack boil-off verdicts do not turn across the band: swept, not typed
    _grid = [_LB_FLOOR * (_LB_TOP / _LB_FLOOR) ** (j / 59.0) for j in range(60)]
    for _r in _TH_RX:
        if "micro" in _r[0] or "RDE" in _r[0] or "rotating" in _r[0] or "zero-gap" in _r[0]:
            _v = {_th_margin(kk, thf[3], _r) >= 1.0 for kk in _grid}
            assert _v == {"micro" in _r[0]}, ("the LiBr row says the microfluidic cell clears and the rotating cells and "
                                               "the stack fail throughout the band; %s does not" % _r[0])
    assert len(_liq) == 3 and all(_LB_FLOOR < k < _LB_VAL for _, k, _ in _liq), _liq
    _liq_short = {"RDE 1600 rpm": "rotating disc", "rotating cyl. 3000 rpm": "rotating cylinder",
                  "zero-gap PEM stack": "zero-gap stack"}
    act = 2 * _TM.B_TAFEL * _math.asinh(stk[4] / (2 * _TM.I0)) * stk[4] * 10 * 1e-4
    rej = _TM.U_passive(stk[2], stk[3]) * (thf[3] - _TM.TAMB)
    clr = [r for r in _TH_RX if r is not _TH_STACK and _th_margin(_LB_VAL, thf[3], r) >= 1.0]
    txt = ("Carries a conclusion, and its support is weaker than the value alone suggests. Das (%s) measures LiBr in THF "
           "at 298.15 K over c = %.4f to %.4f mol dm-3 -- ten times closer to the working 3.0 M than any other measurement "
           "available -- and the picture it gives is not reassuring. (1) A measured reference: kappa(%.4f M) = %.3f mS "
           "cm-1. It would bound kappa(3.0 M) from below only if 3.0 M sat below the conductivity maximum, which (3) argues "
           "it does not, so it corroborates the order of magnitude rather than bounding the row; the hard floor is the "
           "%.3f mS cm-1 derived below from Lee's cell resistance, and the two routes agree within %.0f pct. (2) The carried "
           "3.0 implies a flattening that is not measured. Over the measured triple-ion branch (%.2f-%.2f M) the data scale "
           "as kappa ~ c^%.2f (least squares); getting from the highest measured point to 3.0 mS cm-1 at 3.0 M requires "
           "kappa ~ c^%.2f over the remaining %.1f-fold rise in concentration. Such flattening is physically expected -- it "
           "is the approach to the conductivity maximum as viscosity takes over -- but where that turnover sits has never "
           "been measured for LiBr in THF, and the carried value assumes it happens early. (3) The measured scaling cannot "
           "simply continue, and a stoichiometric calculation shows why. Continuing kappa ~ c^%.2f from the top measured "
           "point to 3.0 M would give %.1f mS cm-1, %.0f times the carried value, so the extrapolation had to be tested. It "
           "fails on solvent availability. Peters' own recipe is 83.4 g LiBr (%.3f mol) in 320 mL THF (SI p. S15); at "
           "rho = %.3f g cm-3 and M = 72.106 that is %.2f mol THF per mole of LiBr. Li+ in an ether is four-coordinate, so "
           "the solvation shell of the cation alone takes %.0f pct of the THF, leaving %.0f pct for Br- and for bulk. The "
           "conclusion holds for any nearby coordination number: at n = 3 only %.0f pct of the THF is free, at n = 5 "
           "there is a %.0f pct shortfall. By contrast Das's highest measured point has %.0f mol THF per mole of LiBr, ten times the "
           "solvation requirement, with abundant bulk solvent for triple ions to move through. The two concentrations are "
           "not the same kind of liquid: at 3.0 M almost no unbound solvent remains, the system is a solvate rather than a "
           "solution, and kappa must have passed its maximum before that point. Independent support for the regime, same solvent and "
           "nearly the same concentration: Cai et al., J. Am. Chem. Soc. 2023, 145, 25716-25725 run 2 M LiBF4 in THF and "
           "report from MD that in cyclic ethers Li+ is only partially solvated and the ions form contact ion pairs and "
           "aggregates. Neither Cai et al. nor Fu et al. reports an extractable conductivity value (Cai's conductivity "
           "figure plots MD-derived quantities and its measured EIS is untabulated; Fu's values are in an untexted figure), "
           "so both corroborate the regime and neither supplies a number; reading a value off a plotted axis was rejected. "
           % (_DAS_LOC, _DAS_C[0] * 1e-4, c_top, c_top, k_top, _LB_FLOOR * 10, 100 * (k_top / (_LB_FLOOR * 10) - 1),
              fits[0][0], c_top, n_branch, n_need, 3.0 / c_top, n_branch, k_cont_top, k_cont_top / 3.0, n_libr, rho_thf,
              thf_per_li, 100 * min(4.0, thf_per_li) / thf_per_li, 100 * max(0.0, thf_per_li - 4.0) / thf_per_li,
              100 * (thf_per_li - 3.0) / thf_per_li, 100 * (5.0 - thf_per_li) / thf_per_li, thf_per_li_das))
    txt += ("Band %.1f-%.1f mS cm-1 at a value of 3.0. The lower end is a state-B hard floor: total cell resistance "
            "<= V/I = 3.2 V / 0.520 A = 6.154 ohm in a coaxial annulus with R_i 9.5 mm, R_o 11.0 mm and L = 18.43 cm "
            "derived from the stated 17.8 mL annulus volume, giving kappa >= 1.266e-3 / 6.154 = %.3f mS cm-1 [Lee et al., "
            "Org. Process Res. Dev. 2022, 26, 2674-2684, main text Results & Discussion, SI Fig. S3 p. S6 and CFD block "
            "p. S22]. The upper end, %.1f, is an edge rather than a bound: ohmic differencing of Lee's voltages returns %.2f "
            "at the rounding limit of two two-significant-figure voltages (dV = 0.10 V), and that construction assumes equal "
            "non-ohmic overpotential across LiBr concentrations, which is refuted for Al anodes in THF by Zhang, Guan, Wang, "
            "Lin & See, Chem. Sci. 2023, 14, 13108-13118 (Br- relieves Al2O3 passivation, so Lee's voltage differences are "
            "partly anodic). Nothing located excludes values above it, so the verdicts are also tested beyond it, below. "
            "What the band buys, judged against each architecture's OWN transport ceiling: %s. Across the band the "
            "microfluidic, rotating-cell and stack boil-off verdicts do not turn -- the microfluidic cell clears throughout and both "
            "rotating cells and the stack fail throughout -- and what it decides is the unstirred, stirred and recirculating cells, which pass at the "
            "carried value and above and fail only below %s the carried conductivity. Three cooling-class verdicts are tighter than "
            "any boil-off verdict: the %s each hold their THF duty with liquid cooling at the carried value, and each "
            "passes beyond what its own cooler rejects below %s the carried conductivity (%s mS cm-1, against the top of "
            "each cooler's declared range, %s W cm-2 K-1 respectively). All three breakpoints lie inside the band, so those three verdicts are conditional "
            "on where in it the conductivity sits and are stated that way where they appear. "
            % (_LB_FLOOR * 10, _LB_TOP * 10, _LB_FLOOR * 10, _LB_TOP * 10, _LB_TOP_RAW * 10,
               "; ".join("at %.3f mS cm-1 the ceilings are %s mA cm-2 against transport ceilings of %s, so %d of the %d "
                         "architectures clear"
                         % (kk * 10.0, "/".join("%.1f" % _th_ceiling(kk, thf[3], r) for r in _TH_RX),
                            "/".join("%.1f" % r[4] for r in _TH_RX),
                            sum(_th_margin(kk, thf[3], r) >= 1.0 for r in _TH_RX), len(_TH_RX))
                         for kk in (_LB_FLOOR, _LB_VAL, _LB_TOP)),
               "%.2f-%.2fx" % (min(_cmg), max(_cmg)),
               ", ".join(_liq_short[a] for a, _, _ in _liq[:-1]) + " and " + _liq_short[_liq[-1][0]],
               ", ".join("%.2fx" % (k / _LB_VAL) for _, k, _ in _liq[:-1]) + " and %.2fx" % (_liq[-1][1] / _LB_VAL),
               "/".join("%.2f" % (k * 10) for _, k, _ in _liq), "/".join("%.3f" % t for _, _, t in _liq)))
    txt += ("At kappa = 3.0 mS cm-1 and T_b = %.1f C, THF does NOT boil in either batch cell, in the recirculating cell or "
            "in the microfluidic cell: those verdicts would reverse only at %.2f-%.2fx the carried conductivity, because "
            "transport binds before heat in cells whose transport ceilings are %.1f-%.1f mA cm-2 (the microfluidic cell "
            "aside). Where THF does fall short the multipliers are %.1fx (rotating disc) and %.1fx (rotating cylinder), with "
            "the zero-gap stack unreachable on kappa at all (at %.0f mA cm-2 its activation term alone puts out %.2f W cm-2 "
            "against %.3f W cm-2 of passive rejection). The binding verdict is the rotating disc at %.1fx, against a band "
            "whose top is %.2fx the carried value, so the failing THF verdicts are band-proof. A second and tighter "
            "test uses the measured data directly: least-squares fits kappa ~ c^n over Das's top decade give n = %s, and "
            "the fitted lines continued to 3.0 M give %s mS cm-1. The rotating-disc verdict reverses at %.1f mS cm-1 and the "
            "rotating-cylinder verdict at %.1f, so both survive every one of those continuations, the disc clearing the "
            "steepest of them by %.0f pct. None of those continuations is itself sound: each crosses a conductivity maximum "
            "the measured range never reaches, and at 3.0 M there are %.2f THF per Li+, so four-coordinate lithium binds "
            "%.0f pct of the solvent. The carried 3.0 mS cm-1 corresponds to n = %.2f from Das's 0.1 M point (%.1f uS cm-1), "
            "i.e. it already assumes the roll-off rather than extrapolating through it. A second same-solvent value, "
            "Zhang, Gu, Wang, Ware, Lu, Lin, Qi and See, JACS Au 2023, 3, 2280-2290, Table 1 measures 0.1 M LiClO4 in THF "
            "at 62.6 uS cm-1 (22.0 +/- 1.0 C), against Das's LiBr at the same 0.1 M of %.1f uS cm-1 -- same solvent, same "
            "cation, different anion, a factor of %.1f apart."
            % (thf[3],
               min(_kappa_multiple(_LB_VAL, thf[3], r[0]) for r in clr if "micro" not in r[0] or True),
               max(_kappa_multiple(_LB_VAL, thf[3], r[0]) for r in clr),
               min(r[4] for r in clr if "micro" not in r[0]), max(r[4] for r in clr if "micro" not in r[0]),
               _thf_flip("RDE 1600 rpm"), _thf_flip("rotating cyl. 3000 rpm"), stk[4], act, rej,
               _thf_flip("RDE 1600 rpm"), _LB_TOP / _LB_VAL,
               ", ".join("%.2f from %.2f M" % (f[1], f[0]) for f in fits),
               ", ".join("%.1f" % f[2] for f in fits), rde_flip, rce_flip, 100 * (rde_flip / fits[-1][2] - 1),
               thf_per_li, 100 * min(4.0, thf_per_li) / thf_per_li, n_carried, k_01 * 1000, k_01 * 1000,
               62.6 / (k_01 * 1000)))
    return txt


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
# Every Casteel-Amis number below is evaluated by data/casteel_amis.py (Dorn's -b convention, gated by G-CA) and the
# measured isotherm is read from data/dorn_isotherms.csv (Table SI 85), never typed (chemistry audit, pass 6: the
# fit values this block carried, 5.18 / 8.07 / 9.87 / 18.95 / 21.34, were the +b convention).
import sys as _sys_ca
_sys_ca.path.insert(0, _HERE_D)
import casteel_amis as _CA
_CA_FIT = _CA.FITS["Bu4NBF4/MeCN"]
with io.open(_os.path.join(_HERE_D, "dorn_isotherms.csv"), encoding="utf8") as _fh:
    _CA_ISO = [(float(r["m_mol_kg"]), float(r["kappa_mScm"]), float(r["u_kappa"]))
               for r in csv.DictReader(_fh) if r["system"] == "Bu4NBF4/MeCN"]


def _ca_fit(m):
    return float(_CA.kappa(m, *_CA_FIT))


def _ca_meas(m):
    """Linear interpolation between the two measured points of Table SI 85 that bracket m."""
    for (m0, k0, _u0), (m1, k1, _u1) in zip(_CA_ISO, _CA_ISO[1:]):
        if m0 <= m <= m1:
            return k0 + (k1 - k0) * (m - m0) / (m1 - m0)
    raise ValueError("m = %g outside the measured Bu4NBF4/MeCN isotherm" % m)


def _ca_molal(c, rule):
    """molarity -> molality for Bu4NBF4/MeCN: 'soln' through the solution density (V_phi = 287 cm3 mol-1), 'pure'
    m = c/rho0, 'disp' m = c/(rho0 - cM/1000); M = 329.27 g mol-1, rho0 = 0.7768 g cm-3."""
    M, rho0, vphi = 329.27, 0.7768, 287.0
    if rule == "pure":
        return c / rho0
    if rule == "disp":
        return c / (rho0 - c * M / 1000.0)
    rs = (rho0 + c * M / 1000.0) / (1.0 + c * vphi / 1000.0)
    return c / (rs - c * M / 1000.0)


with io.open(_os.path.join(_HERE_D, "electrolytes.csv"), encoding="utf8") as _fh:
    _CA_DERIVED = [r["electrolyte"] for r in csv.DictReader(_fh)
                   if r["electrolyte"].endswith("Bu4NBF4/MeCN") and r["state"] == "derived"]
assert _CA_DERIVED, "no derived Bu4NBF4/MeCN row: reword the 0.1 M cross-check sentence"
_CA_M = {k: _ca_molal(0.25, k) for k in ("soln", "pure", "disp")}
_CA_KM = {k: _ca_meas(v) for k, v in _CA_M.items()}
# the molality at which the carried kappa (thermal_model / electrolytes.csv) sits on the measured isotherm: 0.347, which is
# the solution-density conversion (0.3476) to within its third decimal, i.e. 0.1 pct in kappa
_CA_KC = _MECN[2] * 10.0
_CA_MC = [m0 + (_CA_KC - k0) * (m1 - m0) / (k1 - k0) for (m0, k0, _a), (m1, k1, _b) in zip(_CA_ISO, _CA_ISO[1:])
          if k0 <= _CA_KC <= k1][0]
assert abs(_CA_MC - _CA_M["soln"]) < 1.0e-3, (_CA_MC, _CA_M["soln"])
_CA_MA = round(_CA_MC, 3)
_CA_KM["soln"] = _ca_meas(_CA_MA)
_CA_MIC_I = {k: _TM.i_boil(v / 10.0, _TH_MIC[1], _MECN[3], _TM.U_passive(_TH_MIC[2], _TH_MIC[3])) for k, v in _CA_KM.items()}
_CA_BR = [(m0, k0, u0) for m0, k0, u0 in _CA_ISO if m0 <= _CA_MA][-1], [(m0, k0, u0) for m0, k0, u0 in _CA_ISO if m0 > _CA_MA][0]
CA_CONV = ("molarity -> molality, stated explicitly because state B requires the arithmetic to be "
           "reproducible and because the convention matters at the 4 pct level. The route is the "
           "solution density, not the pure-solvent density: rho_soln = (rho0 + c M/1000) / "
           "(1 + c V_phi/1000) and m = c / (rho_soln - c M/1000), with M = 329.27 g mol-1, "
           "rho0 = rho(MeCN) = 0.7768 g cm-3 and an apparent molar volume V_phi = 287 cm3 mol-1 "
           "(an ordinary value for Bu4NBF4, and the value the adopted molalities imply). This "
           "reproduces every adopted molality to three decimals: 0.043 M -> 0.056, 0.077 -> 0.101, "
           "0.100 -> 0.133, 0.250 -> 0.348, 0.300 -> 0.424 mol kg-1. V_phi is itself a declared "
           "assumption, so the convention spread is bounded rather than ignored: on the measured 0.25 M "
           "isotherm the pure-solvent shortcut m = c/rho0 gives m = %.3f and kappa = %.2f, and the "
           "salt-displacement shortcut m = c/(rho0 - cM/1000) gives m = %.3f and kappa = %.2f, against "
           "%.2f at the adopted m = %.3f. That %.2f-%.2f spread sits inside the declared 15-23 band and "
           "moves the microfluidic MeCN ceiling only over %.0f-%.0f mA cm-2 against that cell's own "
           "transport ceiling of %.1f mA cm-2, a margin of %.2fx to %.2fx, so no verdict "
           "anywhere in §S6 turns on the choice."
           % (_CA_M["pure"], _CA_KM["pure"], _CA_M["disp"], _CA_KM["disp"], _CA_KM["soln"], _CA_MA,
              _CA_KM["pure"], _CA_KM["disp"], _CA_MIC_I["pure"], _CA_MIC_I["disp"], _TH_MIC[4],
              _CA_MIC_I["pure"] / _TH_MIC[4], _CA_MIC_I["disp"] / _TH_MIC[4]))
ECOND_PROV = {
 # -- the four rows that carry a §S6 conclusion -----------------------------------------
 "0.25 M Bu4NBF4/MeCN": (
   "measured: read off the raw kappa(c) isotherm in the Dorn et al. Supporting Information. "
   "The Casteel-Amis reconstruction this row used to carry (Casteel & Amis, J. Chem. Eng. "
   "Data 1972, 17, 55) is retained below as the superseded route, applied to the measured fit "
   "of Dorn et al., Table 3, p. 1499 for ACN / (C4H9)4NBF4: kappa_max = 33.40 mS cm-1, "
   "m_max = 1.48127 mol kg-1, a = 0.78646, b = -0.02156, validity range 9.10, MAPE 1.65 pct. At "
   "m = %.3f mol kg-1 (0.25 M; conversion below) that fit, in Dorn's eq. 5 sign convention (-b, p. 1499), "
   "returns kappa = %.2f mS cm-1, %+.1f pct from the %.2f the measured isotherm gives at the same molality. "
   % (_CA_MA, _ca_fit(_CA_MA), 100 * (_ca_fit(_CA_MA) / _CA_KM["soln"] - 1), _CA_KM["soln"]) + CA_CONV + " Independently validated at 1 M against Gong et al. Table 3, p. 3519 "
   "(32.75 derived vs 32.3 tabulated, +1.4 pct). Supersedes the earlier mass-action treatment: the "
   "bound of 24-36 mS cm-1 built on Lambda0 = 171.1 and K_A = 5.6 was a Lee-Wheaton extrapolation "
   "25x above its own fitted range (2e-4 to 1e-2 mol dm-3) and has been withdrawn, as has the "
   "inherited Izutsu limiting-conductivity citation",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502; Gong, Fang, Gu, Li & "
   "Yan, Energy Environ. Sci. 2015, 8, 3515-3530; method: Casteel & Amis, J. Chem. Eng. Data 1972, "
   "17, 55",
   "Dorn supporting information, Table SI 85, p. 170 (ACN / (C4H9)4NBF4, 298.15 K, 101 kPa): "
   "0.25 M is m = %.3f mol kg-1 by the solution-density conversion; the carried value lies on the isotherm at "
   "m = %.3f, between the measured points (%.4f, %.2f) and "
   "(%.4f, %.2f) mS cm-1, which interpolate to %.2f there. The article-body Casteel-Amis fit -- "
   "Table 3 and eq. 5, p. 1499 (m_max 1.48127, kappa_max 33.40, a 0.78646, b -0.02156, MAPE 1.65 pct) -- "
   "returns %.2f at the same molality. Cross-check: Gong Table 3, "
   "p. 3519 (Bu4NBF4/AN, 1 M, 32.3 mS cm-1, tabulated after Izutsu 2009)"
   % (_CA_M["soln"], _CA_MA, _CA_BR[0][0], _CA_BR[0][1], _CA_BR[1][0], _CA_BR[1][1], _CA_KM["soln"], _ca_fit(_CA_MA)),
   "Carries a conclusion. Band 15-23 mS cm-1, a declared test range rather than an uncertainty "
   "estimate: it is wider than the measurement's own expanded uncertainty at the two bracketing points "
   "(%.2f and %.2f mS cm-1, Table SI 85), than the spread the molality convention produces on the measured "
   "isotherm (%.2f-%.2f), and than the gap between the isotherm and Dorn's Casteel-Amis fit at this molality "
   "(%.2f, %+.1f pct). The fit is self-consistent with Dorn's own use of it: at m = 0.075 the published "
   "Table 3 parameters give %.3f mS cm-1, the kappa_ref = 7.04 his dissertation prints (p. 74). "
   % (_CA_BR[0][2], _CA_BR[1][2], _CA_KM["pure"], _CA_KM["disp"], _ca_fit(_CA_MA),
      100 * (_ca_fit(_CA_MA) / _CA_KM["soln"] - 1), _ca_fit(0.075)) +
   "Fig. 7 margins recomputed at the adopted 19.95 mS cm-1, and judged against each "
   "architecture's OWN transport ceiling rather than a declared design current: " +
   ", ".join("%s %.2fx" % (_n, _m) for _n, _m in _MECN_M[:-1]) +
   ". The two shortfalls would reverse only at " +
   " and ".join("%.1f mS cm-1 (%.2fx carried, %s)" % (_k, _f, _n) for _n, _k, _f in _MECN_X) +
   ", both far outside the 15-23 band, so no MeCN verdict turns on where inside its own "
   "measurement band the value sits. Those same two are bound-dependent on the kappa(T) axis of S6.3 and on "
   "the area ratio sigma, reversing at %.2fx of it at the rotating disc and %.2fx at the cylinder, and the disc one "
   "also on its inherited beaker gap, at %.2fx; each is stated conditionally where it is reported."
   % (_TG_ROW("RDE 1600 rpm", "MeCN")["sigma_flip_x"], _TG_ROW("rotating cyl. 3000 rpm", "MeCN")["sigma_flip_x"],
      _TG_ROW("RDE 1600 rpm", "MeCN")["gap_flip_x"])),
 "0.2 M NaI/DMF": (
   "derived 2026-08-22, replacing an unsourced 8.0 that had no derivation of any kind. The "
   "reason for the change is provenance, not preference: 8.0 was a number with no chain behind "
   "it, and this one has a two-step chain a reader can redo. "
   "step 1, Lambda0, now directly measured rather than summed: Lambda0(NaI, DMF) = "
   "81.35 +/- 0.03 S cm2 mol-1 at 25 C [Krumgalz & Barthel, Z. Phys. Chem. 1984, 142, 167-178, "
   "Table 2, p. 170, NaI block, 25 C column; PDF retrieved and read off the page]. That replaces the "
   "Kohlrausch sum this row used to carry -- lambda0(Na+) 29.81 + lambda0(I-) 52.11 = 81.92 from "
   "Gopal & Jha Table 2 p. 81 -- which agrees with it to -0.70 pct and is retained as the "
   "cross-check. The same table's literature column quotes 81.9 from both Singh and Ames. "
   "The hard Kohlrausch ceiling therefore becomes kappa <= c Lambda0 = 16.27 mS cm-1. "
   "step 2, the attenuation at 0.2 M: taken from a measurement of the same salt. Dorn's "
   "Supporting Information measures NaI in methanol across the full range (Table SI 97, p. 196); "
   "with Lambda0(NaI, MeOH) = 45.23 + 62.63 = 107.86 from Krumgalz 1983 Table 4, pp. 580-581 "
   "(methanol row), " + ("the measured Lambda/Lambda0 at 0.2 M (molality %.3f-%.3f mol kg-1 for an apparent molar volume "
   "of NaI of 0-35 cm3 mol-1) is %.3f-%.3f. Transferring the mean gives kappa = 0.2 x 81.35 x %.3f = %.2f mS cm-1. "
   % (_NAI["m_lo"], _NAI["m_hi"], _NAI["r_lo"], _NAI["r_hi"], _NAI["r"], _NAI_K)) +
   "third route, independent of both and using only same-system measurements: Krumgalz & Barthel "
   "also report the association constant, K_A = 7.50 +/- 0.57 dm3 mol-1 for NaI in DMF at 25 C "
   "(same table). Solving the association equilibrium with Debye-Huckel activity coefficients at "
   "their own distance parameter R2 = 1.131 nm gives a free-ion fraction alpha = 0.702 at 0.2 M, "
   "but converting alpha to kappa depends on the conductance form: the Onsager limiting law gives "
   "about 3.1 mS cm-1 and the same law with its Debye-Huckel ion-size factor 8.5-8.8 "
   "(data/derive_kappa.py, nai_dmf_ka_route; the 8.30 once typed here reproduced under neither), so "
   "the route bounds nothing. it is not adopted as primary, and the reason is consistency: it "
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
   "Krumgalz & Barthel, Z. Phys. Chem. (N. F.) 1984, 142, 167-178 (Lambda0 of NaI in DMF, state A); Dorn, Kareth, "
   "Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information (NaI in methanol: the "
   "attenuation); Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587 (lambda0 of Na+ and I- in methanol); "
   "Gopal & Jha, Indian J. Chem. 1977, 15A, 80-83 (Kohlrausch cross-check); Kinart, Molecules 2024, 29, 1371 "
   "(DMF permittivity)",
   "Krumgalz & Barthel Table 2, p. 170, NaI, 25 C (Lambda0 = 81.35 +/- 0.03 S cm2 mol-1); Dorn SI Table SI 97, p. 196 "
   "(NaI in methanol, 298.15 K, 101 kPa); Krumgalz 1983 Table 4, pp. 580-581, methanol row (Na+ 45.23, I- 62.63); "
   "Gopal & Jha Table 2, p. 81, DMF column, 25 C (Na+ 29.81, I- 52.11); Kinart Table 1 (eps_r = 36.81 at 298.15 K)",
   "Carries a conclusion, and is the most exposed number in the category. Band 4-16 mS cm-1, with a hard physical "
   "ceiling: kappa <= c Lambda0 = 0.2 M x 81.35 S cm2 mol-1 = %.2f mS cm-1, since Lambda(c) <= Lambda0 for all "
   "c > 0; the Kohlrausch sum of Gopal & Jha, 29.81 + 52.11 = 81.92, corroborates that Lambda0 to %.1f pct. The "
   "carried value is c Lambda0 times the attenuation measured for the same salt in methanol at the same molarity: "
   "Dorn's isotherm (Table SI 97), read at the molality 0.2 M corresponds to (%.3f-%.3f mol kg-1 for an apparent molar volume "
   "of NaI of 0-35 cm3 mol-1, with methanol's density %.3f g cm-3), gives Lambda/Lambda0 = %.3f-%.3f against Lambda0(NaI, MeOH) = "
   "45.23 + 62.63 = 107.86 S cm2 mol-1 (Krumgalz 1983, Table 4, methanol row), so kappa = 0.2 x 81.35 x %.3f = %.2f mS cm-1. The "
   "transfer is expected to err low, a direction rather than a bound: DMF has the higher permittivity (36.81, Kinart Table 1, against "
   "a recalled, unretrieved 32.7 for methanol), so it pairs less and attenuates less than methanol. Physical support, "
   "direction only: Prue & Sherrington, Trans. Faraday Soc. 1961, 57, 1795-1808 measured twelve salts in DMF and report "
   "the iodides in excellent accord with Fuoss-Onsager assuming complete dissociation, so no ion-pairing term should "
   "drive DMF below methanol; not retrieved in full text -- taken from the abstract and used for direction, never as a "
   "number. What is still missing is a direct measurement of Lambda(0.2 M) for this salt in this solvent. "
   % (0.2 * 81.35, 100 * (81.92 / 81.35 - 1), _NAI["m_lo"], _NAI["m_hi"], _NAI["rho0"], _NAI["r_lo"], _NAI["r_hi"], _NAI["r"], _NAI_K) +
   "(a) Judged against each architecture's own transport ceiling, DMF clears every modelled "
   "archetype except %s and the stack, and its microfluidic margin is %.1fx. The binding "
   "kappa-axis verdict is the %s, which reverses if kappa rises to %.2f mS cm-1, i.e. %.2fx the "
   "carried %.2f, %s. The cheapest route to settling it: 0.2 M NaI in dry DMF, calibrated "
   "probe, 25 C, ten minutes. "
   % (" and ".join("the %s (margin %.2fx)" % (a.replace("RDE 1600 rpm", "rotating disc")
                                               .replace("rotating cyl. 3000 rpm", "rotating cylinder"), m)
                   for a, m, _ in _DMF_FAILS),
      _th_margin(_NAI_S, 152.8, _TH_MIC),
      _DMF_BIND[0].replace("RDE 1600 rpm", "rotating disc").replace("rotating cyl. 3000 rpm", "rotating cylinder"),
      _DMF_BIND[2]*_NAI_K, _DMF_BIND[2], _NAI_K,
      ("inside this row's own 4-16 band, so that failure is conditional on where in the band the "
       "value sits" if _DMF_BIND[2]*_NAI_K < 16.0 else
       "above the top of this row's own 4-16 band, so that failure is band-proof"))
   +    "(b) two further sentences rest on this row, at the adopted %.2f: 'the full lumped balance of \u00a7S6.1 places its passive steady state at "
   "T_ss \u2248 %.0f \u00b0C, above DMF's %.0f \u00b0C boiling point' flips at kappa_crit = %.2f mS cm-1, "
   "a margin of %.2fx, which is inside the honest 4-16 band; and the same cell at 50 mA cm-2 "
   % (_NAI_K, _dmf_tss(), _TH_DMF_TB, _dmf_flip()*10, _dmf_flip()/_NAI_S)
   + "draws %.1f V, a cell voltage that lies between 10 and 20 V for kappa = %.2f-%.2f mS cm-1 "
   "(x%.3f down, x%.3f up). Both are stated as conditional on "
   "the adopted kappa in S6. The binding kappa-axis margin for this row is %.2fx, at the %s; "
   "it and the two statements above are labelled as conditional where they appear."
   % (_TM.E_cell(50.0, _NAI_S, _TM.GAP_BEAKER), _V_KLO * 10, _V_KHI * 10, _V_KLO / _NAI_S, _V_KHI / _NAI_S,
      _DMF_BIND[2], _DMF_BIND[0].replace("RDE 1600 rpm", "rotating disc")
      .replace("rotating cyl. 3000 rpm", "rotating cylinder"))),
 "3.0 M LiBr/THF": (
   "reclassified. this row was labelled measured-lit, but the cited source supports the "
   "concentration, not the conductivity: Peters et al. give LiBr 83.4 g (1.0 mol) / 320 mL THF = 3.0 M "
   "stock. The value 3.0 mS cm-1 came from the row's own note -- 'heavily ion-paired ether medium, "
   "kappa order-of-mS/cm' -- which is an assumption. It cannot be derived either: THF has "
   "eps = 7.6, so the Bjerrum critical distance q = e^2/(8 pi eps0 eps kB T) = 3.7 nm at 25 C, an "
   "order of magnitude beyond contact distance, and ionic association is essentially complete",
   "Peters et al., Science 2019 (Supplementary Materials)",
   "SM pp. S15 and S21 -- supports the 3.0 M concentration only",
   _libr_thf_sens()),
 "1 M NaOH aq": (
   "derived, not measured -- reclassified 2026-08-23. Dorn's supporting information, Table SI "
   "16, p. 60 (sodium hydroxide in water at 298.15 K, 101 kPa, 21 measured points) is the "
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
   "Information; cross-checked against CRC Handbook of Chemistry and "
   "Physics, 97th ed., 'Electrical Conductivity of Aqueous Solutions', p. 5-71",
   "Table SI 16, p. 60 (298.15 K, 101 kPa); CRC p. 5-71 NaOH row (20 C) with 'Concentrative "
   "Properties of Aqueous Solutions' (1.000 M = 3.840 mass pct)",
   "the aqueous reference of the thermal analysis (§S6), so it enters a reported result. Band %.0f-%.0f mS cm-1, the "
   "CRC p. 5-71 route of Table S4 (the 20 C table corrected to 25 C); the measured value sits at its lower edge. Across "
   "the band the unstirred-beaker boil-off ceiling runs %.1f-%.1f mA cm-2 against that cell's own transport ceiling of "
   "%.1f mA cm-2, a margin of %.1f-%.1fx, and the aqueous reference clears every preparative architecture throughout, so "
   "no verdict moves. Recomputed from the thermal model, which asserts this value against the electrolyte table before "
   "rendering."
   % (_NAOH_BAND[0], _NAOH_BAND[1], _th_ceiling(_NAOH_BAND[0] / 10, 99.974, _TH_RX[0]),
      _th_ceiling(_NAOH_BAND[1] / 10, 99.974, _TH_RX[0]), _TH_RX[0][4],
      _th_ceiling(_NAOH_BAND[0] / 10, 99.974, _TH_RX[0]) / _TH_RX[0][4],
      _th_ceiling(_NAOH_BAND[1] / 10, 99.974, _TH_RX[0]) / _TH_RX[0][4])),
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
 "0.25 M NaBr/H2O-MeCN 1:1": (
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
   "ACN at room temperature. At the same composition (m = %.3f mol kg-1) Dorn's measured isotherm "
   "(Table SI 85) gives %.2f and Dorn's Casteel-Amis fit (Table 3, eq. 5, p. 1499; -b convention) gives %.2f, "
   "so the two measurements agree to %.1f pct and the fit sits %.1f pct above Shinkle's value and %.1f pct above "
   "Dorn's. (An evaluation of the fit "
   "with the opposite sign of b, %.2f, is what an earlier note on this row compared against.) "
   % (_ca_molal(0.1, "soln"), _ca_meas(_ca_molal(0.1, "soln")), _ca_fit(_ca_molal(0.1, "soln")),
      100 * abs(9.93 / _ca_meas(_ca_molal(0.1, "soln")) - 1), 100 * (_ca_fit(_ca_molal(0.1, "soln")) / 9.93 - 1),
      100 * (_ca_fit(_ca_molal(0.1, "soln")) / _ca_meas(_ca_molal(0.1, "soln")) - 1),
      float(_CA_FIT[1] * (_ca_molal(0.1, "soln") / _CA_FIT[0]) ** _CA_FIT[2]
            * _math.exp(_CA_FIT[3] * (_ca_molal(0.1, "soln") - _CA_FIT[0]) ** 2
                        - _CA_FIT[2] * (_ca_molal(0.1, "soln") / _CA_FIT[0] - 1))))
   + "The molarity-to-molality conversion is checked at this point too. "
   "caveat: Shinkle states 'room temperature', not 25.0 C; at 2-3 pct per K a +/-2 K ambiguity is "
   "+/-5 pct, which is larger than the agreement with Dorn's measurement and means that agreement should not be "
   "read as better than about +/-5 pct.",
   "Shinkle, Pomaville, Sleightholme, Thompson & Monroe, J. Power Sources 2014, 248, 1299-1305, "
   "DOI 10.1016/j.jpowsour.2013.10.034; cross-check against Dorn, Kareth, Weidner & Petermann, "
   "J. Chem. Eng. Data 2024, 69, 1493-1502",
   "Shinkle Table 1 (0.1 M supporting-electrolyte/solvent conductivities at room temperature, "
   "mS cm-1: TBABF4 = 9.93 ACN, 4.76 DMF, 0.30 THF, 0.06 dmc); Dorn Table 3, p. 1499",
   S_KAPPA_DISPLAY + " Display-only: it enters no figure and no sentence. Its value is as a cross-check: at the "
   "same composition Dorn's measured isotherm gives %.2f mS cm-1 (%.1f pct from this measurement), while Dorn's "
   "Casteel-Amis fit gives %.2f (%+.1f pct), which bounds the fit route used by the %s." %
   (_ca_meas(_ca_molal(0.1, "soln")), 100 * abs(9.93 / _ca_meas(_ca_molal(0.1, "soln")) - 1),
    _ca_fit(_ca_molal(0.1, "soln")), 100 * (_ca_fit(_ca_molal(0.1, "soln")) / 9.93 - 1),
    " and ".join("%s row" % e for e in _CA_DERIVED))),
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
   "q = %.3f W cm-2, and a passive steady state of %.1f C. A +/-5 pct change in kappa moves the cell voltage over "
   "%.2f-%.2f V; it reaches 20 V at kappa = %.2f mS cm-1 and 10 V at %.2f."
   % (_TM.E_cell(100., 0.476, 5.0e-3), 100. * 10. * 5.0e-3 / 0.476,
      _TM.q_Wcm2(100., 0.476, 5.0e-3),
      _TM.T_ss(100., 0.476, 5.0e-3, _TM.U_passive(_TH_RX[0][2], _TH_RX[0][3])),
      _TM.E_cell(100., 0.476 * 1.05, 5.0e-3), _TM.E_cell(100., 0.476 * 0.95, 5.0e-3),
      100. * 10. * 5.0e-3 / (20.0 - _TM.E_cell(100., 1e30, 5.0e-3)) * 10,
      100. * 10. * 5.0e-3 / (10.0 - _TM.E_cell(100., 1e30, 5.0e-3)) * 10)),
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
   S_KAPPA_DISPLAY + " Derived display-only: the row has a method and a locator, but it "
   "enters no figure and no sentence. Declared band %s mS cm-1." % (band,))
   for name, mm, kk, band, moved, extra in [
     ("0.043 M Bu4NBF4/MeCN", "0.056", "5.66", "5.0-6.0", "5.2 -> 5.66",
      "the only row still using the fit. Dorn's supporting information (Table SI 85, p. 170) "
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
   "Table SI 85, p. 170, at m = 0.101 mol kg-1, between the measured points (0.0905, 7.66) and (0.1896, 13.36) "
   "mol kg-1 / mS cm-1, giving 8.26 mS cm-1. Supersedes a typed 8.07 produced from the Casteel-Amis fit with the wrong sign on b.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information",
   "Table SI 85, p. 170 (298.15 K, 101 kPa; 21 measured points with combined "
   "uncertainties)",
   S_KAPPA_DISPLAY),
 "0.3 M Bu4NBF4/MeCN": (
   "measured. read between two measured points of Dorn's isotherm in the supporting "
   "information, which carries the raw data the article body's Table 3 only summarises: "
   "Table SI 85, p. 170, at m = 0.423 mol kg-1, between the measured points (0.4094, 22.13) and (0.5312, 25.48) "
   "mol kg-1 / mS cm-1, giving 22.50 mS cm-1. Supersedes a typed 21.34 produced the same way.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information",
   "Table SI 85, p. 170 (298.15 K, 101 kPa; 21 measured points with combined "
   "uncertainties)",
   S_KAPPA_DISPLAY),
 "2 M NaCl aq": (
   "measured. read between two measured points of Dorn's isotherm in the supporting "
   "information, which carries the raw data the article body's Table 3 only summarises: "
   "Table SI 13, p. 54, at m = 2.0816 mol kg-1, between the measured points (2.0714, 148.36) and (2.3325, 161.37) "
   "mol kg-1 / mS cm-1, giving 148.9 mS cm-1. The target molality is 0.5 pct above a measured point, so this is effectively a direct reading. The CRC p. 5-71 derivation it replaces gave 148.0, i.e. -0.6 pct -- an independent confirmation of that route, which is retained in the registry.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information",
   "Table SI 13, p. 54 (298.15 K, 101 kPa; 21 measured points with combined "
   "uncertainties)",
   S_KAPPA_DISPLAY),
 "1 M KHCO3 aq": (
   "measured. read between two measured points of Dorn's isotherm in the supporting "
   "information, which carries the raw data the article body's Table 3 only summarises: "
   "Table SI 31, p. 94, at m = 1.0405 mol kg-1, between the measured points (0.9676, 71.84) and (1.1207, 80.55) "
   "mol kg-1 / mS cm-1, giving 76.0 mS cm-1. The CRC p. 5-71 derivation it replaces gave 75.5, i.e. -0.6 pct.",
   "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502, Supporting Information",
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
# chemistry audit pass 7: per-solvent page, and the sensitivity is computed (it quoted shifts against a retired rounding)
def _tb_1K(sl):
    k, tb = _th_by_solvent(sl)
    v = [_TM.i_boil(k, r[1], tb + 1.0, _TM.U_passive(r[2], r[3])) / _TM.i_boil(k, r[1], tb, _TM.U_passive(r[2], r[3])) - 1
         for r in _TH_RX]
    return 100 * min(v), 100 * max(v)
for nm_, used_, printed_, sl_, page_ in [
    ("THF",      "66.0",   "66.0",   "THF",      "15-19"),
    ("MeCN",     "81.6",   "81.6",   "MeCN",     "15-13"),
    ("DMF",      "152.8",  "152.8",  "DMF",      "15-16"),
    ("H2O (used for 1 M NaOH aq)", "99.974", "99.974", "aq. NaOH", "15-20")]:
    _lo, _hi = _tb_1K(sl_)
    add("9. Thermal model", "T_boil: %s" % nm_, used_, "deg C", "measured",
        "normal boiling point as printed by the source: %s deg C, and figs/thermal_model.py now "
        "uses exactly that. It previously used a rounding (66/82/153/100); the printed values were "
        "adopted on 2026-08-24 at the author's direction" % printed_,
        CRCB, "Sect. 15, 'Laboratory Solvents and Other Liquid Reagents', p. %s, normal boiling point column" % page_,
        "T_boil enters only as (T_boil - T_amb); a 1 K error in it moves this solvent's boil-off ceilings by %+.2f to %+.2f%% "
        "across the seven cells. For 1 M NaOH the pure-water "
        "boiling point is used; the real solution boils higher by about %.1f K (ideal van't Hoff: two ions x "
        "E_b(water) = 0.513 K kg mol-1, CRC 97th ed. p. 15-25, x 0.998 mol kg-1), so the pure-water value is the "
        "conservative choice for a boil-off ceiling."
        % (_lo, _hi, 2 * 0.513 * 0.9984))

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
    "solution, cathode heights 0.25-3.0 in., i_lim 0.4-108 mA cm-2 -- the same archetype as this "
    "work's unstirred cell). Derivation, reproducible from this table: the paper's "
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
    "the per-reaction spread in nu and D is included. The unstirred median is %.2f mA cm-2 at the "
    "carried %.0f um, with %d of 50 clearing 25 mA cm-2 and %d of 50 clearing 50. Scaling the unstirred "
    "column as 1/delta across the envelope -- exact for the direct and k = 0 rows, and a bound on the "
    "mediated and catalyst rows, none of which falls faster than 1/delta (Table S6) -- gives a median "
    "of %.1f mA cm-2 with at most %d and %d of 50 at the thin edge, and %.1f mA cm-2 with at least %d "
    "and %d at the thick edge, so the unstirred counts are conditional on the declared operating point "
    "(its own row states this). The contrast with the stirred archetype is %.2fx at the central value and %.2f-%.2fx "
    "across the envelope; it is the softest comparison in the model and is bounded rather "
    "than asserted: the unstirred film exceeds the stirred one only for electrode heights above "
    "about 12 mm at the central driving force, so the ordering of the two batch archetypes is a "
    "property of the declared geometry and not a measured separation."
    % ((_FCS["h_5mm"], _FCS["h_80mm"], _FCS["drho_1e-2"], _FCS["drho_1e-3"], _FC_ENV_LO, _FC_ENV_HI,
       _FC["delta_band_lo_um"], _FC["delta_band_hi_um"]) + (_nat_at(_NAT_FILM)[0], _NAT_FILM) + _nat_at(_NAT_FILM)[1:]
       + _nat_at(_FC_ENV_LO) + _nat_at(_FC_ENV_HI) + (_NAT_FILM / 200.0, _FC_ENV_LO / 200.0, _FC_ENV_HI / 200.0)))
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
    "fifty rows deplete %.2f mM to %.2f M of carrier and the densification coefficients of these organic "
    "solutions are not available, so one value is declared for all fifty and what it costs is "
    "stated here rather than hidden inside the derived film." % (1000 * _FC["set_depleted_concentration_M"][0], _FC["set_depleted_concentration_M"][1]),
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
    "force would thin the film for exactly the rows that carry the unstirred counts (%d of the %d "
    "clearing 25 mA cm-2 are concentrated rows, S1.1). The direction is established by the fourth "
    "root; the magnitude per row is not computed here because the coefficients are unavailable. "
    "The ordering from the stirred cell upward does not rest on it; the order of the two batch "
    "archetypes does (the derived film's row)." % (_FCI["source"], _FCI["rho_2M_gcm3"], _FCI["rho_ref_gcm3"], _FCI["drho_rho"],
                _FCI["ratio_to_declared_centre"], _FCI["delta_um_at_central_height"],
                _FC["delta_centre_um"], _DS_STRATA["concentrated"]["n25"][0], _DS_STRATA["all"]["n25"][0]) + _FC_COUNTS_SENT)
# chemistry audit pass 3: the stirred row's sensitivity typed the unstirred film (233 um, retired), the batch contrast
# (1.16x), the crossover height (11 mm) and the unstirred-to-RCE span (15.2x); all four are computed now
def _med_col(col):
    with io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "tier0_ec_matrix.csv"), encoding="utf8") as fh:
        v = sorted(float(r[col]) for r in csv.DictReader(fh))
    return 0.5 * (v[len(v) // 2 - 1] + v[len(v) // 2]) if len(v) % 2 == 0 else v[len(v) // 2]
_SPAN_NAT_RCE = _med_col("rce") / _med_col("natural")
with io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "mediated_ec_matrix.csv"), encoding="utf8") as fh:
    _UNSTIRRED_UM = sorted({float(r["delta_um"]) for r in csv.DictReader(fh) if r["reactor"] == "Unstirred batch"})
assert len(_UNSTIRRED_UM) == 1, _UNSTIRRED_UM
_UNSTIRRED_UM = _UNSTIRRED_UM[0]
_H_CROSS_MM = 1000 * _FC["h_centre_m"] * (200.0 / _FC["delta_centre_um"]) ** 4
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
    "p. 1228: 'For the transport of dissolved O2 gas, the calculated boundary layer thickness "
    "was 200 +/- 7 um' (D_O2 = 2.10e-5 cm2 s-1, bubbling at 10 sccm)",
    "IT IS A PROXY, NOT THIS SYSTEM, and that is stated rather than glossed: the measurement is "
    "dissolved O2 in a gas-bubbled aqueous cell, not an organic electrolyte under magnetic "
    "stirring. It is the same GEOMETRY CLASS -- a planar electrode in a convecting cell -- and "
    "O2 diffuses about " + "%.1f" % _O2R + " times as fast as the median carrier modelled here, and a convective film "
    "thickens with the diffusivity (delta ~ D^(1/3) for a laminar boundary layer, D^(1/2) under "
    "penetration theory), so the real layer for these systems should if anything be THINNER, by "
    "roughly " + "%.0f-%.0f" % (100 * (1 - _O2R ** (-1 / 3)), 100 * (1 - _O2R ** (-1 / 2))) + " pct, and the adopted value stays conservative (it lowers the ceilings). "
    "The unstirred archetype is derived at the centre of the same free-convection correlation, "
    "%.0f um, so the two batch films are compared centre against centre, a contrast of %.2fx. The "
    "two archetypes remain close, and that is a property of the systems rather than of the "
    "choice: the unstirred film exceeds this one only for electrode heights above about "
    "%.0f mm at the central driving force, so the separation is bounded by declared geometry "
    "and is not a measured result. The measurement's own uncertainty, +/-7 um, "
    "carries through to " % (_UNSTIRRED_UM, _UNSTIRRED_UM / 200.0, _H_CROSS_MM) + _sbrow("stirred") + "; the architecture ordering and the "
    "unstirred-to-RCE span of %.1fx hold across the whole interval, so no conclusion depends on "
    "where within it the value sits." % _SPAN_NAT_RCE)
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
    "entrance solution would overtake the fully-developed film only for D below 1.0e-12 m2/s, more than "
    "two decades under any row; over Table S1's tau = 4-12 min the band therefore collapses onto the "
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
    "0.08% above, a 0.186% spread end to end. The film scales linearly with the coefficient, so every "
    "RDE ceiling moves by at most that 0.19%, and the RDE cell nearest a threshold sits "
    + "%.1f%%" % min(100 * abs(x - t) / t for x in _pub_col("rde") for t in (25, 50)) + " from 25 "
    "or 50 mA cm-2, so no count can move. No reported number or count depends on the "
    "choice. The rotating-disc film carries no laminar-regime assertion, unlike the Leveque "
    "coefficient, which is asserted only below Re = 2300.")
_ROT_M = lambda k: _SB["median, " + k]
_ROT_C = lambda k, t: _SB["count >=%d, %s" % (t, k)]
_ANEC_HI = _ROT_M("anec")["upper"]
assert _ROT_M("rde")["lower"] > _ANEC_HI and _ROT_M("rce")["lower"] > _ANEC_HI, \
    "a rotating archetype's band now reaches below ANEC's; reword the RDE and RCE operating-point rows"
add("7. Reactors", "RDE operating point", "1600", "rpm", "assumption",
    "a declared convention, not a measured quantity: 1600 rpm is the customary RDE reference speed. "
    "It is not the measured quantity of the Levich row, though it is sometimes tabulated there as though it were the "
    "quantity", "declared operating point", "",
    "Swept over %.0f-%.0f rpm (Table S8). delta ~ omega^(-1/2), so that band spans a factor of %.1f in delta and in "
    "i_lim, and the RDE column gives a median of %.1f-%.1f mA cm-2 about %.1f, %d-%d of 50 clearing 25 mA cm-2 and "
    "%d-%d clearing 50. Its upper edge passes the rotating-cylinder median (%.1f), so the order of the RDE and the "
    "rotating cylinder is a property of the two declared operating points, not of the architectures, and is not "
    "claimed. The RDE's two threshold counts are conditional on the declared rotation rate. What holds across the whole band is that the RDE stays above ANEC, whose own band tops out at %.1f mA "
    "cm-2, so the four-step ordering below it is unaffected."
    % (_RDE_BAND[0], _RDE_BAND[1], (_RDE_BAND[1] / _RDE_BAND[0]) ** 0.5, _ROT_M("rde")["lower"], _ROT_M("rde")["upper"],
       _ROT_M("rde")["value"], _ROT_C("rde", 25)["lower"], _ROT_C("rde", 25)["upper"], _ROT_C("rde", 50)["lower"],
       _ROT_C("rde", 50)["upper"], _ROT_M("rce")["value"], _ANEC_HI))
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
    "10.1016/0013-4686(74)85036-X; Walsh & Ponce de Leon, Electrochim. Acta 2018, 280, "
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
def _channel_pair_sentence():
    """The S8.1 ratios decomposed into the pair's three changes, read from results/reactor_engineering.json (chemistry
    audit, pass 6: the typed version gave delta ~ h^(2/3) and credited the whole 2.5x film step to the gap). In the
    Leveque entrance regime Sh = 1.85 (Re Sc d_h/L)^(1/3) with d_h = 2h, so delta = d_h/Sh = (2 h D L/u)^(1/3)/1.85."""
    with io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "reactor_engineering.json"), encoding="utf8") as fh:
        re_ = _json.load(fh)
    a, b = re_["channels"]
    fh_, fl_, fu_ = a["gap_m"] / b["gap_m"], a["length_m"] / b["length_m"], b["velocity_m_s"] / a["velocity_m_s"]
    d_pred = (fh_ * fl_ * fu_) ** (1.0 / 3.0)
    if abs(d_pred / re_["ratios"]["delta"] - 1) > 1e-6:
        raise SystemExit("the channel films are not in the Leveque entrance regime (half-gap floor binding?): "
                         "(h L / u)^(1/3) predicts %.4f, reactor_engineering.json gives %.4f" % (d_pred, re_["ratios"]["delta"]))
    dp_pred = fh_ ** 2 * (b["velocity_m_s"] / a["velocity_m_s"]) * (b["length_m"] / a["length_m"])
    if abs(fu_ / fl_ - 1) > 1e-9:
        raise SystemExit("the channel pair no longer holds u L fixed; reword the pressure-drop clause")
    if abs(dp_pred / re_["ratios"]["dP"] - 1) > 1e-6:
        raise SystemExit("pressure-drop ratio %.4f is not 12 mu u L / h^2 (%.4f)" % (re_["ratios"]["dP"], dp_pred))
    return ("A declared geometry that reaches no reported ceiling, count or median. The S8.1 quantities it feeds are "
            "reported as ratios between the two channels. In the Leveque entrance regime delta = d_h/Sh scales as "
            "(h L / u)^(1/3) at fixed D, so the film falls %.2fx between the channels: %.2fx from the %.0fx gap step, "
            "%.2fx from the %.0fx shorter channel and %.2fx from the %.0fx faster flow. The pressure drop of laminar slot "
            "flow, 12 mu u L / h^2, rises %.0fx: the gap step alone gives %.0fx, and the %.0fx faster flow and the "
            "%.0fx shorter channel cancel. Changing the pair changes the absolute per-pass conversions, which S8.1 reports only as "
            "being under 5 %%."
            % (re_["ratios"]["delta"], fh_ ** (1 / 3.0), fh_, fl_ ** (1 / 3.0), fl_, fu_ ** (1 / 3.0), fu_,
               re_["ratios"]["dP"], fh_ ** 2, fu_, fl_))


add("7. Reactors", "Illustrative channel pair (S8.1)",
    "1 mm / 5 cm / 5 cm/s; 250 um / 2.5 cm / 10 cm/s", "-", "assumption",
    "the declared pair of generic laminar parallel-plate channels behind the S8.1 illustration of "
    "what thinning a gap costs (residence time, conversion per pass, pressure drop). These were the "
    "model's two flow archetypes until 2026-09-07 and are kept for that illustration alone; no "
    "archetype column is computed from them", "declared illustration", "",
    _channel_pair_sentence())
add("7. Reactors", "Eisenberg RCE: Sh = 0.0791 Re^0.70 Sc^0.356", "0.0791", "-", "measured",
    "turbulent rotating-cylinder correlation, Eq. IX of the source, fitted to the mass-transfer data of five systems "
    "-- three for benzoic acid dissolution and the electrolytic reduction of ferricyanide and oxidation of "
    "ferrocyanide -- at rotating cylinders",
    "Eisenberg, Tobias & Wilke, J. Electrochem. Soc. 1954, 101, 306-320, DOI 10.1149/1.2781252",
    _SX["cal_locator"],
    "Extrapolation flagged, and its DIRECTION matters. The source fits Eq. IX to five systems over Schmidt numbers "
    "%d-%d (Fig. 10, p. 314) and gives the straight line for Reynolds numbers %d-%d (p. 312). Computed over the fifty "
    "rows: Sc runs %.0f (min) / %.0f (median) / %.0f (max), so %d of %d sit BELOW the fitted floor, %d inside and only "
    "%d above the ceiling. The extrapolation is therefore predominantly to LOW Sc -- aprotic organics are low-Sc "
    "relative to the aqueous systems of the fit, because their low viscosity raises D and lowers nu "
    "together -- and Re runs %.0f-%.0f, inside the fitted range throughout. A sensitivity on "
    "a fitted correlation must preserve the fit where it was made: swapping the exponent "
    "alone leaves the coefficient 0.0791 attached to a curve that no longer reproduces the "
    "calibration data, so it is not a bound. The bound used instead is a second fitted "
    "correlation validated in the direction this set extrapolates, that of Jang et al. (Sh = "
    "0.204 Re^0.59 Sc^0.33, Sc > 100): it moves per-row values by %.3f-%.3fx, the RCE median "
    "%.1f -> %.1f mA cm-2 and the RCE counts %d -> %d (>=25) and %d -> %d (>=50), and inverts the "
    "RDE/RCE pair; the four-step ordering and both rotating archetypes above ANEC survive (S3.3)."
    % (_SX["cal_window"][0], _SX["cal_window"][1], _SX["cal_re"][0], _SX["cal_re"][1], _SX["sc_min"], _SX["sc_median"],
       _SX["sc_max"], _SX["n_below"], _SX["n_total"], _SX["n_inside"], _SX["n_above"], _SX["re_lo"],
       _SX["re_hi"], _SX["factor_lo"], _SX["factor_hi"], _SX["medians"]["rce"],
       _SX["medians_alt"]["rce"], _SX["n25_rce"], _SX["n25_rce_alt"], _SX["n50_rce"], _SX["n50_rce_alt"]))
assert _SX["medians_alt"]["rce"] > _SX["medians_alt"]["anec"] and _SX["medians_alt"]["rde"] > _SX["medians_alt"]["anec"], \
    "the Eisenberg row says both rotating archetypes stay above ANEC under the Jang bound; they no longer do"
## RETIRED 2026-09-01: "delta (stirred batch): measured comparison". That row existed to
## keep a DECLARED 100 um honest by standing the measurement beside it. The measurement is
## now the adopted value of the row above, so keeping a second row for the same number left
## the registry carrying two entries of 200 um with contradictory framings, one of them
## describing a state that no longer exists. Its content -- the +/- 7 um, the O2 proxy
## caveat and the direction it errs in -- is carried in the adopted row.
add("7. Reactors", "RCE operating point", "d 1.2 cm, 3000 rpm", "-", "assumption",
    "a declared laboratory operating point", "declared operating point", "",
    "Swept over %.0f-%.0f rpm (Table S8). Sh ~ Re^0.70 with Re ~ omega d^2, so k_m runs x%.2f to x%.2f about the "
    "3000 rpm point (%.1fx end to end), and the rotating-cylinder column gives a median of %.1f-%.1f mA cm-2 about %.1f, "
    "%d-%d of 50 clearing 25 mA cm-2 and %d-%d clearing 50. At the low end that median falls below the microfluidic "
    "(%.1f) and RDE (%.1f) medians, so the rotating cylinder is the highest rung only at the declared operating point. "
    "Its two threshold counts are therefore conditional on the declared rotation rate, at which the main text quotes them. "
    "Across the whole band it stays above ANEC (upper edge %.1f mA cm-2), which is what the four-step ordering needs."
    % (_RCE_BAND[0], _RCE_BAND[1], (_RCE_BAND[0] / 3000.0) ** 0.70, (_RCE_BAND[1] / 3000.0) ** 0.70,
       (_RCE_BAND[1] / _RCE_BAND[0]) ** 0.70, _ROT_M("rce")["lower"], _ROT_M("rce")["upper"], _ROT_M("rce")["value"],
       _ROT_C("rce", 25)["lower"], _ROT_C("rce", 25)["upper"], _ROT_C("rce", 50)["lower"], _ROT_C("rce", 50)["upper"],
       _ROT_M("micro")["value"], _ROT_M("rde")["value"], _ANEC_HI))
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
# chemistry audit pass 11: the alpha sensitivity is computed at each architecture's own current (it had claimed
# "under 60 mV against ohmic terms of 1-50 V", false at the thin-cell and stack currents).
import numpy as _np_t
_ash = lambda i: _np_t.arcsinh(i / (2 * _TM.I0))
_dA = lambda i: 1000 * 2 * (_TM.RT_F / 0.3 - 2 * _TM.RT_F) * _ash(i)          # alpha = 0.3 on both electrodes, mV
_dI = lambda i: 1000 * 2 * (2 * _TM.RT_F) * (_np_t.arcsinh(i / 0.02) - _ash(i))  # i0 = 0.01 against 1 mA cm-2, mV
_cmI = [r[4] for r in _TM.REACTORS if r[1] >= 0.01]; _thI = [r[4] for r in _TM.REACTORS if r[1] < 0.01]
assert all(_dA(i) <= _dI(i) * (1 + 1e-6) for i in _cmI + _thI)
_TAFEL_SENS = ("The only free choice is alpha = 1/2. Taking alpha = 0.3 on both electrodes, the end of [0.3, 0.7] "
               "that raises the term, adds %.0f-%.0f mV at the centimetre-gap cells' operating currents and %.0f-%.0f mV "
               "at the microfluidic chip and the stack; at every one of those currents that is no more than the i0 "
               "sweep of the next row adds, and that row states the consequence."
               % (min(map(_dA, _cmI)), max(map(_dA, _cmI)), min(map(_dA, _thI)), max(map(_dA, _thI))))
add("8. Voltage stack", "Tafel slope b = 2RT/F per electrode", "0.0514", "V", "derived",
    "2RT/F at 298.15 K with R and F from category 1; symmetric Butler-Volmer with alpha = 1/2, "
    "inverted through asinh and applied to both electrodes", BF,
    "ch. 3 (Butler-Volmer and Tafel forms)",
    _TAFEL_SENS)
def _nice(arch):
    return (arch.replace("RDE 1600 rpm", "rotating disc").replace("rotating cyl. 3000 rpm", "rotating cylinder")
            .replace("microfluidic 25 um", "25 um microfluidic cell").replace("zero-gap PEM stack", "zero-gap stack"))


def _tm_sweep(attr, values, fn):
    """Evaluate fn() with thermal_model.<attr> set to each value in turn, restoring it afterwards."""
    keep = getattr(_TM, attr)
    out = []
    try:
        for v in values:
            setattr(_TM, attr, v)
            out.append(fn())
    finally:
        setattr(_TM, attr, keep)
    return out


def _all_ceilings():
    return {(r[0], sl): _th_ceiling(k, tb, r) for r in _TH_RX for sl, k, tb in _TH_SOL}


def _i0_sentence():
    """The i0 sweep of the thermal model over 0.01-10 mA cm-2, every architecture x electrolyte, generated (chemistry
    audit, pass 6: the typed version quoted MeCN's thin-gap ranges as the whole set's and centimetre-gap moves of
    'at most 3 pct' where aqueous NaOH moves -7.1/+3.8)."""
    grid = [10 ** (-2 + 3 * j / 30.0) for j in range(31)]
    base = _all_ceilings()
    sw = _tm_sweep("I0", grid, _all_ceilings)
    chg = {key: (min(s[key] for s in sw) / base[key] - 1, max(s[key] for s in sw) / base[key] - 1) for key in base}
    mrg = {key: (min(s[key] for s in sw) / r[4], max(s[key] for s in sw) / r[4])
           for r in _TH_RX for key in base if key[0] == r[0]}
    flips = [key for key in base if (mrg[key][0] < 1.0) != (mrg[key][1] < 1.0)]
    cm = [r[0] for r in _TH_OPEN]
    ohm = []
    for r in _TH_OPEN:
        for sl, k, tb in _TH_SOL:
            i = base[(r[0], sl)]
            ohm.append((i * 10.0 * r[1] / k) * i * 10.0 * 1e-4 / _TM.q_Wcm2(i, k, r[1]))
    mic, stk = _TH_MIC[0], _TH_STACK[0]
    def rng(arch, sl):
        return "%+.0f/%+.0f" % (100 * chg[(arch, sl)][0], 100 * chg[(arch, sl)][1])
    cm_sol = ", ".join("%s %+.1f/%+.1f" % (sl, 100 * min(chg[(a, sl)][0] for a in cm), 100 * max(chg[(a, sl)][1] for a in cm))
                       for sl, _k, _tb in _TH_SOL)
    txt = ("Treating i0 as negligible is safe only where ohmic heat dominates. That holds in the centimetre-gap cells and "
           "fails in the thin ones, and the split is sharp: the activation term is gap-independent, so it matters exactly "
           "where the ohmic term has been removed. "
           "Swept %.2g-%.0f mA cm-2 across all %s §S6 electrolytes, every boil-off ceiling of the %s centimetre-gap "
           "architectures (%s) moves by at most %s pct (%s), because %.0f-%.0f pct of their heat at the ceiling is ohmic. "
           "The %s moves by %s pct and the %s by %s pct (%s respectively), because in a thin gap the activation term is "
           "most of q. "
           % (grid[0], grid[-1], _numword(len(_TH_SOL)), _numword(len(cm)), ", ".join(_nice(a) for a in cm),
              "%.1f" % (100 * max(max(abs(chg[(a, sl)][0]), abs(chg[(a, sl)][1])) for a in cm for sl, _k, _tb in _TH_SOL)),
              cm_sol, 100 * min(ohm), 100 * max(ohm),
              _nice(mic), ", ".join(rng(mic, sl) for sl, _k, _tb in _TH_SOL), _nice(stk),
              ", ".join(rng(stk, sl) for sl, _k, _tb in _TH_SOL), ", ".join(sl for sl, _k, _tb in _TH_SOL)))
    if flips:
        txt += ("Across that range %d verdicts reverse: %s." % (len(flips), "; ".join("%s / %s" % f for f in flips)))
        return txt
    txt += ("Every verdict holds across the range. At the stack all %s electrolytes fail (margins %.2f-%.2fx); at the "
            "microfluidic cell all %s clear (%s), judged against its median transport ceiling of %.1f mA cm-2."
            % (_numword(len(_TH_SOL)), min(mrg[(stk, sl)][0] for sl, _k, _tb in _TH_SOL), max(mrg[(stk, sl)][1] for sl, _k, _tb in _TH_SOL),
               _numword(len(_TH_SOL)), ", ".join("%s %.2f-%.2fx" % (sl, *mrg[(mic, sl)]) for sl, _k, _tb in _TH_SOL),
               _TH_MIC[4]))
    return txt


add("8. Voltage stack", "i0 (exchange current density)", "1.0", "mA cm-2", "assumption",
    "an illustrative symmetric value for both electrodes; no measured i0 exists for these couples "
    "on these electrodes in these media", "declared modelling choice", "",
    _i0_sentence())

# -- 9. Thermal model + the §S6 architecture constants ---------------------
# STRUCTURAL RESULT OF THE THERMAL SOURCING PASS, stated once and reused: because
# U' = [(1/h_int + 1/h_ext)^-1] * sigma with h_ext ~ 13 W m-2 K-1, the EXTERNAL film is 87-99.7 pct
# of the series resistance. Sweeping h_int from 50 to infinity -- a range above 2e4, spanning the
# entire Incropera Table 1.1 liquid band -- moves the beaker ceilings by about -6/+7 pct and the thin cells' by up to -19 pct. The genuinely
# load-bearing thermal parameters are, in order: sigma > i_design > h_ext > everything else.
_HINT_SWEEP = (50., 100., 800., 2000., 1.0e12)


def _hint_series(reactor, sl="DMF"):
    k, tb = _th_by_solvent(sl)
    return " / ".join("%.1f" % _TM.i_boil(k, reactor[1], tb,
                                          _TM.U_passive(reactor[2], h)) for h in _HINT_SWEEP)


# chemistry audit pass 7: the sweep's effect differs by cell (beaker -6/+7 pct, thin cells -15 to -19 pct), so it is
# computed per architecture group rather than stated once
# 2026-10-06 (liquid-cooling audit J1): h_int and the coolant temperature sit inside the liquid-cooling verdicts too,
# so the h_int and T_amb rows must report those verdicts, not only the boil-off ones
_LQ_THF = [r for r in _TM.SOLVENTS if r[0] == "THF"][0]
_LQ_CELLS = [(lab, [r for r in _TM.REACTORS if key in r[0]][0]) for lab, key in
             (("rotating disc", "RDE"), ("rotating cylinder", "cyl"), ("stack", "stack"))]
def _lq_ok(r, h=None, tc=None):
    """True when THF's duty is within the declared construction range of the cell's own cooler (<= U_liquid hi)."""
    rr = r if h is None else (r[0], r[1], r[2], h, r[4])
    tc = _TM.TAMB if tc is None else tc
    return _TM.q_Wcm2(r[4], _LQ_THF[2], r[1]) / (_LQ_THF[3] - tc) <= _TM.U_liquid(rr)[1]
def _lq_bisect(f, lo, hi):
    assert f(lo) != f(hi)
    flo = f(lo)
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) == flo else (lo, mid)
    return 0.5 * (lo + hi)
_LQ_HMIN = [(lab, r, _lq_bisect(lambda h: _lq_ok(r, h), 10.0, 1.0e5)) for lab, r in _LQ_CELLS]
_LQ_TMAX = [(lab, r, _lq_bisect(lambda t: _lq_ok(r, tc=t), -20.0, _LQ_THF[3] - 1.0)) for lab, r in _LQ_CELLS]
assert all(_lq_ok(r) for lab, r in _LQ_CELLS)
_HINT_OF = {r[0].replace("\n", " ").replace("$\\mu$m", "um"): r[3] for r in _TM.REACTORS}
def _lq_hint_txt(hv):
    """The liquid-cooling clause for the h_int row whose declared value is hv, from Table S12's h_int axis."""
    ax = [a for a in _TAX["axes"] if a["key"] == "h_int"][0]
    use = [(c["arch"], c["solvent"], x) for c in ax["cells"] if abs(_HINT_OF[c["arch"]] - hv) < 1e-9
           for x, a, b in c["changes"] if {a, b} == {"liquid cooling", "beyond liquid cooling"}]
    if not use:
        return ""
    cells = sorted({_ARCH_S(a) for a, _s, _x in use})
    return (" The S6.2 liquid-cooling verdicts of the %s run through this film and depend on it, because it sits in series "
            "inside the cooler: each can be met within the declared construction range only for h_int above %s, against the "
            "declared %.0f W m-2 K-1, so those verdicts are conditional on this film as well."
            % (" and the ".join(cells), "; ".join("%.0f W m-2 K-1 (%s, %s)" % (x, _ARCH_S(a), sl) for a, sl, x in use), hv))
def _hint_group(names):
    v = []
    for r in _TH_RX:
        if r[0].replace("\n", " ") not in names:
            continue
        for sl, k, tb in _TH_SOL:
            ref = _TM.i_boil(k, r[1], tb, _TM.U_passive(r[2], r[3]))
            v += [100 * (_TM.i_boil(k, r[1], tb, _TM.U_passive(r[2], h)) / ref - 1) for h in (50., 1.0e12)]
    assert v, names
    return "%+.0f/%+.1f pct" % (min(v), max(v))
_HINT_FLIPS = [(r[0].replace("\n", " "), sl) for r in _TH_RX for sl, k, tb in _TH_SOL for h in (50., 1.0e12)
               if (_TM.i_boil(k, r[1], tb, _TM.U_passive(r[2], h)) >= r[4]) != (_TM.i_boil(k, r[1], tb, _TM.U_passive(r[2], r[3])) >= r[4])]
S_HINT = ("h_int decides no boil-off verdict. Swept 50 -> infinity (a range above 2e4, spanning "
          "the whole Incropera Table 1.1 liquid band), the boil-off ceilings move by %s in the unstirred beaker, %s in the "
          "stirred, recirculating and rotating cells and %s in the microfluidic chip and the stack: "
          "the dimethylformamide ceiling runs %s mA cm-2 at h_int = 50 / 100 / 800 / 2000 / "
          "infinity in the %s, and %s mA cm-2 in the %s, which is the thinnest-gap architecture "
          "and the one where a developing-flow correction to h_int would be largest. %s"
          % (_hint_group(["unstirred batch"]), _hint_group(["stirred batch", "recirculating flow", "RDE 1600 rpm", "rotating cyl. 3000 rpm"]),
             _hint_group(["microfluidic 25 um", "zero-gap PEM stack"]),
             _hint_series(_TH_RX[0]), _TH_RX[0][0], _hint_series(_TH_MIC), _TH_MIC[0],
             "No boil-off verdict of S6.1 reverses anywhere in the sweep." if not _HINT_FLIPS else
             "The sweep reverses " + "; ".join("%s in the %s" % (b, a) for a, b in _HINT_FLIPS) + "."))
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
    "unstirred transport ceiling of %.1f mA cm-2, so transport binds before heat at every volume, and no batch or "
    "recirculating verdict turns on the vessel. Both rotating cells inherit the beaker's sigma, though, which a 50, 500 "
    "and 1000 mL charge sets at %.2fx, %.2fx and %.2fx of its 100 mL value, and their verdicts do move; every change of "
    "class, with the charge at which it occurs, is listed in Table S12. "
    % (" / ".join("%.0f" % _th_vol("DMF", V) for V in (50, 100, 500, 1000)),
       _th_vol("DMF", 1000) / _th_vol("DMF", 50),
       " / ".join("%.0f" % _th_vol("THF", V) for V in (50, 100, 500, 1000)), _TH_RX[0][4],
       *[_TAX["volume"]["sigma"][v] / _TAX["volume"]["sigma"]["100"] for v in ("50", "500", "1000")])
    + "Those verdicts are therefore conditional on the declared 100 mL charge as well as on sigma.")
_VS = {d: _vessel_sigma(d) for d in (0.04, 0.06)}
_VS_BEAK = _TH_RX[0]
_VS_CEIL = {sl: {d: _th_ceiling(k, tb, (_VS_BEAK[0], _VS_BEAK[1], _VS[d], _VS_BEAK[3], _VS_BEAK[4])) / _th_ceiling(k, tb, _VS_BEAK) - 1
                 for d in _VS} for sl, k, tb in _TH_SOL}
_VS_DMF = [r for r in _TH_SOL if r[0] == "DMF"][0]
add("9. Thermal model", "Vessel external area", "%.5f" % _TM.A_EXT_BEAKER, "m2", "derived",
    "DERIVED from the declared archetype: the area that rejects heat from a 100 mL charge in a 5 cm vessel is the "
    "wetted wall plus the base, a consequence of the declared charge and diameter rather than a free parameter: fill "
    "height = 0.1 L / (pi x 0.025^2) = %.2f cm, A = pi x 0.05 x %.4f + pi x 0.025^2 = %.5f + %.5f = %.5f m2. Computed in "
    "figs/thermal_model.py from the declared archetype so the construction cannot drift from it"
    % (100*_FILL_M, _FILL_M, _math.pi*0.05*_FILL_M, _math.pi*0.025**2, _TM.A_EXT_BEAKER),
    "elementary geometry of the declared vessel (wetted wall + base of a right cylinder)", "",
    "The residual exposure is the declared 5 cm diameter, which sets how the same 100 mL is distributed between wall "
    "and base. The same construction gives %.5f m2 for a 4 cm vessel and %.5f m2 for a 6 cm one (sigma %.2f and %.2f, a "
    "span of %.2fx), and the unstirred-beaker ceilings move by %+.1f to %+.1f pct at 4 cm and %+.1f to %+.1f pct at 6 cm "
    "across the four electrolytes (DMF %.1f and %.1f against %.1f mA cm-2). No verdict changes class."
    % (_VS[0.04] * _TM.A_ELEC_M2, _VS[0.06] * _TM.A_ELEC_M2, _VS[0.04], _VS[0.06], _VS[0.04] / _VS[0.06],
       100 * min(v[0.04] for v in _VS_CEIL.values()), 100 * max(v[0.04] for v in _VS_CEIL.values()),
       100 * min(v[0.06] for v in _VS_CEIL.values()), 100 * max(v[0.06] for v in _VS_CEIL.values()),
       _th_ceiling(_VS_DMF[1], _VS_DMF[2], _VS_BEAK) * (1 + _VS_CEIL["DMF"][0.04]),
       _th_ceiling(_VS_DMF[1], _VS_DMF[2], _VS_BEAK) * (1 + _VS_CEIL["DMF"][0.06]),
       _th_ceiling(_VS_DMF[1], _VS_DMF[2], _VS_BEAK)))
# Air at 1 atm, Incropera 6th ed. Table A.4, p. 941 (verified on the page): T K -> (nu 1e-6 m2/s, k 1e-3 W/m K,
# alpha 1e-6 m2/s, Pr). The plate height is the wetted height of the declared 100 mL / 5 cm vessel
# (thermal_model._FILL_M), the same surface A_EXT_BEAKER credits (chemistry audit, pass 6: the row used an 8 cm plate).
_AIR_A4 = {300.0: (15.89, 26.3, 22.5, 0.707), 350.0: (20.92, 30.0, 29.9, 0.700), 400.0: (26.41, 33.8, 38.3, 0.690)}


def _h_nat(ts_c, L=None):
    """Churchill-Chu laminar vertical plate, film properties interpolated linearly in Table A.4."""
    L = _TM._FILL_M if L is None else L
    ts, tinf = ts_c + 273.15, 298.15
    tf = 0.5 * (ts + tinf)
    lo = max(t for t in _AIR_A4 if t <= tf)
    hi = min(t for t in _AIR_A4 if t >= tf) if tf < max(_AIR_A4) else lo
    f = 0.0 if hi == lo else (tf - lo) / (hi - lo)
    nu, k, al, pr = (a + f * (b - a) for a, b in zip(_AIR_A4[lo], _AIR_A4[hi]))
    ra = 9.81 * (1.0 / tf) * (ts - tinf) * L ** 3 / (nu * 1e-6 * al * 1e-6)
    nul = 0.68 + 0.670 * ra ** 0.25 / (1.0 + (0.492 / pr) ** (9.0 / 16.0)) ** (4.0 / 9.0)
    return {"Ra": ra, "Nu": nul, "h": nul * k * 1e-3 / L, "Gr": ra / pr}


_HN = {t: _h_nat(t) for t in (65.0, 100.0, 152.8)}
assert _TM.VESSEL_ID_M / _TM._FILL_M < 35.0 / _HN[65.0]["Gr"] ** 0.25, "the vertical-cylinder criterion now holds; reword"
assert round(_HN[65.0]["h"]) == 7, "the derived h at 65 C no longer rounds to the carried 7; reword the h_nat row"
add("9. Thermal model", "h natural convection (air)", "7", "W m-2 K-1", "derived",
    "RE-derived. the inherited citation (Incropera Table 1.1) contains only the range 2-25 W m-2 "
    "K-1 for free convection in gases and cannot support the value 7. Computed instead from the "
    "laminar vertical-plate correlation Nu_L = 0.68 + 0.670 Ra_L^(1/4) / "
    "[1 + (0.492/Pr)^(9/16)]^(4/9), valid for Ra_L below about 1e9, with L = %.4f m (the wetted height of the "
    "declared 100 mL charge in the 5 cm vessel) and T_inf = 298.15 K: Ra_L = %.3g, Nu = %.1f, h = %.1f W m-2 K-1 "
    "at Ts = 65 C, %.1f at 100 C and %.1f at 152.8 C"
    % (_TM._FILL_M, _HN[65.0]["Ra"], _HN[65.0]["Nu"], _HN[65.0]["h"], _HN[100.0]["h"], _HN[152.8]["h"]),
    "Churchill & Chu, Int. J. Heat Mass Transfer 1975, 18, 1323-1329; restated as " + INCROP +
    ", Eq. 9.26-9.27, with air properties from " + INCROP + ", Table A.4",
    "Int. J. Heat Mass Transfer 1975, 18, 1323-1329; Incropera 6th ed., Eq. 9.26-9.27 and Table A.4",
    "Evaluated over the wetted height of the declared vessel (L = %.2f cm), the correlation gives h = %.1f W m-2 K-1 at "
    "Ts = 65 C, %.1f at 100 C and %.1f at 152.8 C; the carried 7 is the 65 C value. The vertical-cylinder criterion "
    "D/L >= 35/Gr_L^(1/4) gives %.2f against %.2f at 65 C. The criterion fails, so curvature raises Nu and the "
    "flat-plate value is a conservative underestimate."
    % (100 * _TM._FILL_M, _HN[65.0]["h"], _HN[100.0]["h"], _HN[152.8]["h"], _TM.VESSEL_ID_M / _TM._FILL_M,
       35.0 / _HN[65.0]["Gr"] ** 0.25))
add("9. Thermal model", "h radiation (linearized)", "6-8", "W m-2 K-1", "derived",
    "h_r = eps sigma_SB (Ts + Tsur)(Ts^2 + Tsur^2) with eps = 0.9 and Tsur = 298.15 K gives 6.6 at "
    "65 C, 7.2 at 82 C, 7.8 at 100 C and 10.0 at 153 C. Radiation is comparable to convection over "
    "this range, so omitting it would overstate the boiling problem", INCROP, "Eq. 1.9",
    "See the emissivity row for the residual exposure.")
_EMIS_H = {e: _TM.H_EXT - _h_rad(0.9) + _h_rad(e) for e in (0.7, 0.95)}
_EMIS_C = {sl: {e: _th_ceiling_h(k, tb, _VS_BEAK[1], _VS_BEAK[2], _VS_BEAK[3], _EMIS_H[e]) / _th_ceiling(k, tb, _VS_BEAK) - 1
                for e in _EMIS_H} for sl, k, tb in _TH_SOL}
_EMIS_DMF = {e: _th_ceiling(_VS_DMF[1], _VS_DMF[2], _VS_BEAK) * (1 + _EMIS_C["DMF"][e]) for e in _EMIS_H}
# "Nothing flips" is checked, not asserted: every architecture-solvent verdict at both emissivity edges, and every verdict of
# the architectures that inherit the beaker sigma at both vessel diameters.
for _e in _EMIS_H:
    for _r in _TH_RX:
        for _sl, _k, _tb in _TH_SOL:
            assert (_th_ceiling_h(_k, _tb, _r[1], _r[2], _r[3], _EMIS_H[_e]) >= _r[4]) == (_th_ceiling(_k, _tb, _r) >= _r[4]), \
                "an emissivity edge now reverses %s / %s; reword the emissivity row" % (_r[0], _sl)
for _d in _VS:
    for _r in _TH_RX:
        if abs(_r[2] - _TM.SIGMA_BEAKER) < 1e-12:
            _r2 = (_r[0], _r[1], _VS[_d], _r[3], _r[4])
            for _sl, _k, _tb in _TH_SOL:
                assert (_th_ceiling(_k, _tb, _r2) >= _r[4]) == (_th_ceiling(_k, _tb, _r) >= _r[4]), \
                    "a vessel diameter edge now reverses %s / %s; reword the vessel-area row" % (_r[0], _sl)
add("9. Thermal model", "Surface emissivity eps (borosilicate)", "0.9", "-", "assumption",
    "used in the radiation row. New row: previously unregistered and never stated. the Incropera "
    "Table A.11 glass entry was not located for it, and it is deliberately not cited",
    "-- (not page-verified)", "",
    "Tested eps in [0.7, 0.95], re-solving the unstirred-beaker ceilings with the radiative part of the external film "
    "coefficient scaled accordingly (h_r = eps sigma (Ts + Tsur)(Ts² + Tsur²), sigma the Stefan-Boltzmann constant, at Ts = 65 C): h_ext moves over %.2f-%.2f W m-2 K-1 and "
    "the four ceilings by %+.1f to %+.1f pct (DMF %.1f-%.1f mA cm-2 against %.1f). Nothing flips."
    % (_EMIS_H[0.7], _EMIS_H[0.95], 100 * min(v[0.7] for v in _EMIS_C.values()), 100 * max(v[0.95] for v in _EMIS_C.values()),
       _EMIS_DMF[0.7], _EMIS_DMF[0.95], _th_ceiling(_VS_DMF[1], _VS_DMF[2], _VS_BEAK)))
# chemistry audit pass 7: the sum is evaluated at the declared vessel's wetted height, as the two addend rows are (it had been
# summed over a retired 8 cm plate, 6.36 + 6.60 = 12.96); the temperature series and the ceiling shifts are computed
_HX_T = [(t, _TM.h_ext_at(t)) for t in (66.0, 81.6, 100.0, 152.8)]
_HX = {sl: _th_ceiling_h(k, tb, _VS_BEAK[1], _VS_BEAK[2], _VS_BEAK[3], _TM.h_ext_at(tb)) / _th_ceiling(k, tb, _VS_BEAK) - 1
       for sl, k, tb in _TH_SOL}
_HX_FLIPS = [(r[0].replace("\n", " "), sl) for r in _TH_RX for sl, k, tb in _TH_SOL
             if (_th_ceiling_h(k, tb, r[1], r[2], r[3], _TM.h_ext_at(tb)) >= r[4]) != (_th_ceiling(k, tb, r) >= r[4])]
add("9. Thermal model", "H_EXT (external film: convection + radiation)", "%.1f" % _TM.H_EXT, "W m-2 K-1",
    "derived",
    "the sum of the two rows above evaluated at Ts = 65 C, eps = 0.9, L = %.4f m (the wetted height of the declared vessel) "
    "and T_amb = 25 C: %.2f + %.2f = %.2f" % (_TM._FILL_M, _TM.h_nat(65.0), _TM.h_rad(65.0), _TM.H_EXT),
    "rows 'h natural convection (air)' and 'h radiation (linearized)' of this registry", "",
    "Held temperature-independent in the code while the real h_ext runs %s, so rejection near the higher boiling points is "
    "understated. Resolving h_ext at each solvent's boiling point moves the unstirred-beaker ceilings by %s; %s."
    % (" -> ".join("%.1f (%.0f C)" % (h, t) for t, h in _HX_T),
       ", ".join("%s %+.1f pct" % (sl, 100 * v) for sl, v in _HX.items()),
       "no architecture-solvent verdict reverses" if not _HX_FLIPS else
       "the verdict reverses for " + "; ".join("%s in %s" % (b, a) for a, b in _HX_FLIPS)))
_UA = _TM.H_EXT * _TM.A_EXT_BEAKER
_UA_SER = _TM.U_passive(_TM.SIGMA_BEAKER, 100.) * _TM.A_ELEC_M2 * 1e4          # W K-1, internal + external film
_RHO_DMF = float(next(r for r in csv.DictReader(io.open(_os.path.join(_HERE_D, "solvents.csv"), encoding="utf8"))
                      if r["solvent"] == "DMF")["rho"])
_CP_DMF = float(next(r for r in R if r["parameter"] == "DMF: cp")["value"])
_MCP_DMF = 100.0 * _RHO_DMF * _CP_DMF
add("9. Thermal model", "UA still air (incl. radiation)", "%.4f" % _UA, "W K-1", "derived",
    "UA = H_EXT x A_ext = %.1f W m-2 K-1 x %.5f m2 = %.4f W K-1: the external film (convection plus radiation) over "
    "the derived wetted area of the 100 mL beaker" % (_TM.H_EXT, _TM.A_EXT_BEAKER, _UA),
    "rows 'H_EXT' and 'Vessel external area' of this registry", "",
    "UA is the external film alone. The passive coefficient the model uses puts the stagnant internal film "
    "(h_int = 100 W m-2 K-1) in series with it, U' A_elec = %.4f W K-1, and that sets both the steady state and the "
    "transient: tau = m cp / (U' A_elec) = %.0f min for a 100 mL DMF beaker (m cp = 100 mL x %.3f g mL-1 x %.2f J g-1 "
    "K-1 = %.0f J K-1). Every input is a registry row, and the series film is the one Table S7i lists under h_int."
    % (_UA_SER, _MCP_DMF / _UA_SER / 60.0, _RHO_DMF, _CP_DMF, _MCP_DMF))
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
    "Inherits the vessel-geometry exposure of that row: across the 4-6 cm diameter span sigma runs %.2f-%.2f and the "
    "unstirred-beaker ceilings move by %+.1f to %+.1f pct. No verdict changes class."
    % (_VS[0.04], _VS[0.06], 100 * min(min(v.values()) for v in _VS_CEIL.values()),
       100 * max(max(v.values()) for v in _VS_CEIL.values())))
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
    "electrode areas, and a rotating disc turns in a beaker, so these three take the registered "
    "beaker geometry rather than a housing invented for them",
    "declared basis: the value of row 'sigma (unstirred 100 mL beaker)'", "", _TG_SENS_SIGMA)
add("9. Thermal model", "sigma (microfluidic 25 um)", "7.0", "-", "assumption",
    "the single load-bearing sigma. No source exists. The declared chip that reproduces it is a "
    "5 x 3.5 cm footprint, 2.05 cm thick, with 1 cm plates: A_ext = 69.8 cm2 over 10 cm2 gives "
    "6.98; a thinner 1.1 cm chip gives 5.4. New row: previously unregistered",
    "declared chip geometry, bracketed by the exemplar's own drawings: Mo et al., Science "
    "2020, 368, 1352-1357, Supplementary Materials Appendix A, Fig. S20A p. 58 (the aluminium "
    "holder for the small-scale cell, 3.00 x 3.00 inch, 'Unit: inch'), with the glassy carbon "
    "plates given as 50 x 50 x 3 mm on p. 3",
    "SM Appendix A, Fig. S20A p. 58; electrode plates p. 3",
    "Corroborated by the exemplar's own drawings. The two outer "
    "aluminium faces alone give 2 x (3.00 in)^2 = 116 cm2, a lower bound on the rejecting area, "
    "and the channel area follows from V = Q tau at the 25 um gap with tau = 4 min (Table S1 "
    "entries 9-12) and the 5-15 uL min-1 the procedures use, i.e. 8-24 cm2. Together they bracket "
    "sigma at 4.8-14.5 for that cell and the declared 7.0 sits inside, the mid-range flow rate "
    "giving 7.3. Neither end is adopted: the bracket is wide, and the archetype's electrode is "
    "the declared 10 cm2 rather than Mo's channel. "
    "Tested sigma in [3.5, 21], half to three times the declared value. Judged against this "
    "cell's own median transport ceiling of %.1f mA cm-2, every electrolyte clears at every point "
    "in that range (%s), and the breaking points lie far below it -- the tightest is %.2fx the "
    "declared 7.0. This row carries no verdict that turns inside its own band. It is the one "
    "surface-area ratio in the model that rests on a declared chip geometry, bracketed by the exemplar's drawings "
    "rather than computed from them, which is why the band is stated."
    % (_TH_MIC[4],
       ", ".join("%s %.2f-%.2fx"
                 % (sl,
                    _th_margin(k, tb, (_TH_MIC[0], _TH_MIC[1], 3.5, _TH_MIC[3], _TH_MIC[4])),
                    _th_margin(k, tb, (_TH_MIC[0], _TH_MIC[1], 21.0, _TH_MIC[3], _TH_MIC[4])))
                 for sl, k, tb in _TH_SOL),
       max(r["sigma_flip_x"] for r in _TG["rows"]
           if r["arch"].startswith("micro") and r["sigma_flip_x"] is not None)))
def _zg_gap_sentence(gaps=(50e-6, 200e-6)):
    """The zero-gap stack's boil-off ceiling at gaps of 50 and 200 um against the declared 100 um, every electrolyte,
    computed from thermal_model (chemistry audit, pass 6: the typed version said q ~ L, i.e. a 1.4x ceiling span either
    way, which holds only where ohmic heat dominates; at this gap activation heat is most of q)."""
    stk = _TH_STACK
    out, act, fails = [], [], True
    for sl, k, tb in _TH_SOL:
        c0 = _th_ceiling(k, tb, stk)
        cs = [_th_ceiling(k, tb, (stk[0], g, stk[2], stk[3], stk[4])) for g in gaps]
        out.append("%s x%.3g / x%.3g" % (sl, cs[0] / c0, cs[1] / c0))
        q = _TM.q_Wcm2(c0, k, stk[1])
        act.append(1.0 - (c0 * 10.0 * stk[1] / k) * c0 * 10.0 * 1e-4 / q)
        fails = fails and all(c / stk[4] < 1.0 for c in cs + [c0])
    if not fails:
        raise SystemExit("a stack electrolyte clears %.0f mA cm-2 inside the 50-200 um gap band; reword the gap row" % stk[4])
    return ("Tested %.0f-%.0f um: the ceiling moves by %s (%.0f um / %.0f um against the declared %.0f um), far less "
            "than q ~ L would give, because at this gap %.0f-%.0f pct of the heat at the ceiling is activation heat, "
            "which the gap does not touch. All four still need active cooling at %.0f mA cm-2 across the range."
            % (gaps[0] * 1e6, gaps[1] * 1e6, ", ".join(out), gaps[0] * 1e6, gaps[1] * 1e6, stk[1] * 1e6,
               100 * min(act), 100 * max(act), stk[4]))


# sigma of an interior stack cell = (perimeter x pitch) / A_elec, square 10 cm2 cell, pitch 4-12 mm
_ZG_S = tuple(4.0 * _math.sqrt(_TM.A_ELEC_M2) * pitch / _TM.A_ELEC_M2 for pitch in (4e-3, 12e-3))
def _ZG_M(sig):
    r = (_TH_STACK[0], _TH_STACK[1], sig, _TH_STACK[3], _TH_STACK[4])
    m = [_th_margin(k, tb, r) for _sl, k, tb in _TH_SOL]
    return min(m), max(m)
assert _ZG_M(_ZG_S[1])[1] < 1.0, "a stack electrolyte now clears inside the pitch band; reword the zero-gap sigma row"
add("9. Thermal model", "sigma (zero-gap PEM stack)", "0.8", "-", "assumption",
    "no source exists. An interior cell of a stack rejects heat only through the plate edge, so "
    "sigma = (perimeter x cell pitch) / A_elec: a square 10 cm2 cell of perimeter 12.65 cm at 8.7 mm "
    "pitch gives 1.10 and a circular one 0.98. The 8.7 mm pitch itself came from a stack design "
    "that could not be opened (403) and is deliberately not cited. new row: previously unregistered",
    "declared stack geometry", "",
    "Tested pitch 4-12 mm, i.e. sigma in [%.2f, %.2f] for the square 10 cm2 cell: across that range the zero-gap margin "
    "runs %.3fx-%.2fx against i_design = %.0f mA cm-2 over the four electrolytes (%.3fx-%.2fx at the declared %.1f, "
    "%.3fx-%.2fx at 1.0), so all four fail at every point in the range and the zero-gap conclusion is unconditional."
    % (_ZG_S[0], _ZG_S[1], _ZG_M(_ZG_S[0])[0], _ZG_M(_ZG_S[1])[1], _TH_STACK[4], _ZG_M(_TH_STACK[2])[0],
       _ZG_M(_TH_STACK[2])[1], _TH_STACK[2], _ZG_M(1.0)[0], _ZG_M(1.0)[1]))
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
        "Table 1.1 (ranges only; the table does not license any single value)", S_HINT + _lq_hint_txt(hv))
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
with io.open(_os.path.join(_HERE_D, "reactions_50.csv"), encoding="utf8") as _fh:
    _N_CT = {}
    for _r in csv.DictReader(_fh):
        _N_CT[_r["carrier_type"]] = _N_CT.get(_r["carrier_type"], 0) + 1
assert set(_N_CT) == {"substrate", "catalyst", "mediator"} and sum(_N_CT.values()) == 50, _N_CT
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
    "the median over the solved 50-reaction transport matrix, per architecture: the Stage-1 Nernst-Planck "
    "solve with migration for the %d direct and %d k = 0 catalyst entries, and the EC' solver for the %d "
    "mediated entries and the %d catalyst rows carried at a sourced rate constant (Tables S2 and S5)"
    % (_N_CT["substrate"], _N_CT["catalyst"] - len(_DMA_K), _N_CT["mediator"], len(_DMA_K)), "",
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
    "over 200 h). Tested 500-2000 mA cm-2: the stack cannot reject its heat passively in any of the four "
    "electrolytes at any point, and that holds at a gap of zero as well, so the passive verdict rests on no geometry at all. "
    "")
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
  "the rotating-cylinder ceilings fall about 1.6x and every boil-off verdict at this cell holds: tetrahydrofuran, "
  "acetonitrile and dimethylformamide boil throughout it, reversing only at gaps of about "
  + "%.1f mm, %.2f cm and %.2f cm, all below the band, and aqueous NaOH clears throughout it, reversing only above %.1f cm. "
  ""
  % (_TG_ROW("rotating cyl. 3000 rpm", "THF")["gap_flip_m"] * 1e3, _TG_ROW("rotating cyl. 3000 rpm", "MeCN")["gap_flip_m"] * 1e2,
     _TG_ROW("rotating cyl. 3000 rpm", "DMF")["gap_flip_m"] * 1e2, _TG_ROW("rotating cyl. 3000 rpm", "aq. NaOH")["gap_flip_m"] * 1e2)
  + ("" if all(_TG_ROW("rotating cyl. 3000 rpm", x)["verdict"] == "boils" and _TG_ROW("rotating cyl. 3000 rpm", x)["gap_flip_m"] < 0.02435
               for x in ("THF", "MeCN", "DMF")) and _TG_ROW("rotating cyl. 3000 rpm", "aq. NaOH")["gap_flip_m"] > 0.0625 else 1 / 0)),
 ("microfluidic 25 um", "2.5e-5 m",
  "MEASURED, and the same number the transport archetype derives its 12.5 um half-gap film from: "
  "the thinnest FEP spacer of the cell the exemplar was run in",
  "Mo, Lu, Rughoobur, Patil, Gershenfeld, Akinwande, Buchwald & Jensen, Science 2020, 368, 1352-1357, "
  "Supplementary Materials",
  "Supplementary Materials p. 3 (\"The inter-electrode distance is controlled by the thickness of FEP spacer\") and "
  "p. 13 (\"the thinnest FEP spacer (0.001\", 25 um)\")", ""),
 ("zero-gap PEM stack", "1.0e-4 m",
  "intended as a membrane thickness, but no named membrane with a page-anchored thickness is "
  "attached to it. Thin-gap preparative cells at 100 um do exist (a 4-methylanisole thin-gap cell, "
  "J. Appl. Electrochem. 2008, DOI 10.1007/s10800-007-9444-8), but that paper could not be opened "
  "and its contents are not asserted here", "-- (no page-anchored source)", "",
  _zg_gap_sentence() + " Page-anchoring would require a named separator (Nafion 115, 117 or 212) with a "
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
def _wall_sentence():
    """Vessel-wall conduction put in series for the glass-bodied cells (the beaker's sigma), at the declared 2-3 mm
    borosilicate wall, and every boil-off ceiling re-solved. thermal_conditional_flips.py computes the same thing for
    the SI's S6.4 sentence; this is the registry's own evaluation."""
    du, di, flips, n = [], [], 0, 0
    for _s in _TM.SOLVENTS:
        for r in _TM.REACTORS:
            if abs(r[2] - _TM.SIGMA_BEAKER) > 1e-9:
                continue
            n += 1
            u0 = _TM.U_passive(r[2], r[3]); i0 = _TM.i_boil(_s[2], r[1], _s[3], u0)
            for L in _TM.T_VESSEL_WALL:
                uw = r[2] * 1e-4 / (1.0 / r[3] + 1.0 / _TM.H_EXT + L / _TM.K_PYREX)
                iw = _TM.i_boil(_s[2], r[1], _s[3], uw)
                du.append(100 * (1 - uw / u0)); di.append(100 * (1 - iw / i0)); flips += (i0 >= r[4]) != (iw >= r[4])
    assert flips == 0, "the wall row says no verdict changes"
    return ("Through the %.0f-%.0f mm borosilicate wall declared for the jacketed cell (k = %.1f W m-1 K-1, the Pyrex row), "
            "the omitted term lowers U' of the cells computed on the beaker body by %.1f-%.1f pct and their boil-off ceilings by %.1f-%.1f "
            "pct, and changes none of the %d verdicts those cells carry. No archetype in \u00a7S6 is computed on a plastic "
            "body, whose conductivity this registry does not carry; the bound is registered because such a body would need "
            "the term restored." % (1e3 * _TM.T_VESSEL_WALL[0], 1e3 * _TM.T_VESSEL_WALL[1], _TM.K_PYREX,
                                    min(du), max(du), min(di), max(di), n))

add("9. Thermal model", "Vessel wall conduction (omitted from U')", "0", "m2 K W-1", "assumption",
    "the heat balance puts the internal and external films in series and carries NO conduction "
    "resistance through the vessel wall between them. That is why it is declared rather than "
    "silent: the omission is invisible for glass and is not for a machined plastic body",
    "declared model simplification", "",
    _wall_sentence())
# DEMOTED derived -> assumption 2026-08-22. PROVENANCE_STANDARD.md rule B: "A bound is not a
# derivation. If a method yields a range that CONTAINS the tabled value but does not PRODUCE
# it, the row is state C." All three cooling bands are in exactly that position, and each
# said so in its own sensitivity field while carrying the derived label:
#   natural convection -- plotted edges "rounded outward by about 25 pct" from the derived
#                         1.04e-3..1.63e-2 interval;
#   forced air         -- (retired 2026-10-06: the author ruled forced air is not how such cells are cooled)
#                         for a sigma window of about 3-8 that is registered nowhere;
#   liquid cold plate  -- "the plotted band sits inside the derived interval".
# (historical) The forced-air row was the one that mattered: S6.2's zero-gap verdict was drawn from its
# UPPER EDGE while the row calls itself "shading only".
_SIG_LO = min(r[2] for r in _TM.REACTORS); _SIG_HI = max(r[2] for r in _TM.REACTORS)
_NB = [b for b in _TM.COOLING_BANDS if b[0].startswith("natural")][0]
_NAT_LO, _NAT_HI = _TM.H_EXT * _SIG_LO * 1e-4, _TM.H_EXT * _SIG_HI * 1e-4
_E1 = lambda x: ("%.0e" % x).replace("e-0", "e-").replace("e+0", "e+")
add("9. Thermal model", "Cooling band: natural convection", "%s - %s" % (_E1(_NB[1]), _E1(_NB[2])), "W cm-2 K-1", "assumption",
    "the shaded availability band of §S6.2, reproduced from this registry's own inputs: H_EXT = %.0f W m-2 K-1 times "
    "sigma in [%.2f, %.2f], the model's full sigma range (thermal_model.REACTORS), gives %.2e to %.2e W cm-2 K-1"
    % (_TM.H_EXT, _SIG_LO, _SIG_HI, _NAT_LO, _NAT_HI),
    "rows 'H_EXT' and the four sigma rows of this registry", "",
    "The plotted edges lie outside the derived interval -- the lower edge %.2fx below it and the upper edge %.2fx above "
    "it -- which visually credits passive cooling the model does not have. The derived edges, %.1e to %.1e W cm-2 K-1, "
    "are registered on this row as its sensitivity rather than applied, so that the band this section reports is "
    "unchanged. No numeric conclusion depends on it; the band is shading only."
    % (_NAT_LO / _NB[1], _NB[2] / _NAT_HI, _NAT_LO, _NAT_HI))
# LIQUID COOLING, BUILT AS EACH ARCHITECTURE WOULD BE COOLED (2026-10-06, author: "do whatever is more rigorous and
# correct and consistent with actual devices"). Replaces the declared 0.2-1.0 "PEM-class cold plate" band and the
# U' = 0.30 row: thermal_model.U_liquid puts the cell's own electrolyte-side film, the wall and a laminar coolant
# channel heated from one wall in series, and every verdict uses the architecture's own cooler.
import math as _m_lq
_jk = [r for r in _TM.REACTORS if _TM.cooler_type(r) == "jacket"]
_pl = [r for r in _TM.REACTORS if _TM.cooler_type(r) == "plate"]
_thf_lq = [r for r in _TM.SOLVENTS if r[0] == "THF"][0]
_ROT = [(lab, [r for r in _TM.REACTORS if key in r[0]][0]) for lab, key in (("rotating disc", "RDE"), ("rotating cylinder", "cyl"))]
_STK = [r for r in _TM.REACTORS if "stack" in r[0]][0]
def _lq_mult(r, U):                                                  # THF conductivity multiple where U_required = U
    f = lambda m: _TM.U_required(r[4], m * _thf_lq[2], r[1], _thf_lq[3]) - U
    lo, hi = 1e-4, 10.0
    assert f(lo) > 0 and f(hi) < 0
    for _ in range(200):
        mid = _m_lq.sqrt(lo * hi); lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return _m_lq.sqrt(lo * hi)
_duty = lambda r: _TM.U_required(r[4], _thf_lq[2], r[1], _thf_lq[3])
_byh = {}
for r in _jk:
    _byh.setdefault(r[3], _TM.U_liquid(r))
_JK_FF = _TM.U_liquid(_ROT[0][1])                                    # the forced-flow vessel cells (h_int 2000)
_PL = _TM.U_liquid(_STK)
for _lab, _r in _ROT:
    assert _JK_FF[0] < _duty(_r) <= _JK_FF[1], "rotating-cell THF duty no longer inside the jacket range"
assert _PL[0] < _duty(_STK) <= _PL[1], "stack THF duty no longer inside the cooled-plate range"
def _one(r, attr, vals):                                             # sweep one construction input, the others favourable
    keep = getattr(_TM, attr); out = []
    for v in vals:
        setattr(_TM, attr, (v, v) if isinstance(keep, tuple) else v)
        out.append(_TM.U_liquid(r)[1]); setattr(_TM, attr, keep)
    return min(out), max(out)
def _met(duty, lo, hi, every="met within the declared construction range"):   # 2026-10-07: one liquid class (author)
    return every if duty <= hi else "beyond what the declared construction range can meet"
def _rot_txt(lo, hi):
    return "; ".join("the %s's THF duty, %.3f, is %s" % (lab, _duty(r), _met(_duty(r), lo, hi)) for lab, r in _ROT)
def _dim_break(r, attr, duty):
    """The value of one jacket dimension, the other at its favourable end, above which the duty exceeds U_liquid hi."""
    keep = getattr(_TM, attr)
    def ok(v):
        setattr(_TM, attr, (v, v))
        try:
            return _TM.U_liquid(r)[1] >= duty
        finally:
            setattr(_TM, attr, keep)
    return _lq_bisect(ok, keep[0], keep[1])
def _dim_txt(lo, hi, end, attr=None, noun=None):
    """A one-at-a-time construction-dimension sweep: which THF duties are met across it, and which only toward one end."""
    parts, part = [], []
    for lab, r in _ROT:
        d = _duty(r)
        m = ("met across that range" if d <= lo else "not met anywhere in it" if d > hi else
             "met only for %s of at most %.2f mm" % (noun, 1e3 * _dim_break(r, attr, d)) if attr
             else "met only toward the %s end of that range" % end)
        parts.append("the %s's THF duty, %.3f, is %s" % (lab, d, m))
        if lo < d <= hi:
            part.append(lab)
    t = "; ".join(parts)
    if part:
        t += (". The %s THF liquid-cooling verdict %s therefore conditional on the declared %s end of this dimension"
              % (" and the ".join("%s's" % c for c in part), "is" if len(part) == 1 else "are", end))
    return t
_PL_COND = ""   # 2026-10-07: no verdict is classed by where it sits inside the declared construction range
add("9. Thermal model", "Water (coolant): k", "0.613", "W m-1 K-1", "measured",
    "saturated water at 300 K, the coolant of both liquid-cooling constructions", INCROP,
    "Table A.6, p. 949 (saturated water, 300 K)", "")
add("9. Thermal model", "Coolant channel Nu (one wall heated)", "5.39", "-", "measured",
    "laminar, fully developed flow between parallel plates with one side insulated and uniform heat flux on the "
    "other: the geometry of a jacket heated from the vessel side and of a cooled-plate channel heated from the "
    "electrode side", INCROP, "Table 8.1, p. 519", "")
add("9. Thermal model", "Pyrex: k", "1.4", "W m-1 K-1", "measured",
    "borosilicate wall of a jacketed glass cell", INCROP, "Table A.3, p. 939 (Pyrex, 300 K)", "")
add("9. Thermal model", "Pyrolytic graphite: k through the layers", "5.70", "W m-1 K-1", "measured",
    "through-plane conduction of a graphite cooled plate; the value perpendicular to the layers is the low end of "
    "graphite, so the plate is not credited with conduction it may lack", INCROP,
    "Table A.2, p. 933 (pyrolytic graphite, k perpendicular to layers, 300 K)", "")
add("9. Thermal model", "Vessel wall thickness (jacketed cell)", "2e-3 - 3e-3", "m", "assumption",
    "declared device dimension of a jacketed glass electrochemical cell", "Declared device dimension", "",
    "Across 2-3 mm, with the jacket at its narrow end, the forced-flow vessel cells' liquid U' runs %.3f-%.3f W cm-2 "
    "K-1; %s." % (_one(_ROT[0][1], "T_VESSEL_WALL", _TM.T_VESSEL_WALL)
                  + (_dim_txt(*_one(_ROT[0][1], "T_VESSEL_WALL", _TM.T_VESSEL_WALL), "thin", "T_VESSEL_WALL", "a wall"),)))
add("9. Thermal model", "Cooling-jacket gap", "2e-3 - 5e-3", "m", "assumption",
    "declared annular gap of the water jacket (hydraulic diameter twice the gap)", "Declared device dimension", "",
    "Across 2-5 mm, with the wall at its thin end, the forced-flow vessel cells' liquid U' runs %.3f-%.3f W cm-2 K-1; "
    "%s." % (_one(_ROT[0][1], "JACKET_GAP", _TM.JACKET_GAP) + (_dim_txt(*_one(_ROT[0][1], "JACKET_GAP", _TM.JACKET_GAP), "narrow", "JACKET_GAP", "a jacket gap"),)))
add("9. Thermal model", "Cooled-plate thickness", "2e-3 - 3e-3", "m", "assumption",
    "declared thickness of the graphite plate between the stack electrode and its coolant channels",
    "Declared device dimension", "",
    "Across 2-3 mm, with the channels at their favourable end, the stack's liquid U' runs %.3f-%.3f W cm-2 K-1 "
    "against its THF duty of %.3f." % (_one(_STK, "T_COOLED_PLATE", _TM.T_COOLED_PLATE) + (_duty(_STK),)) + _PL_COND)
add("9. Thermal model", "Cooled-plate channel D_h", "1e-3 - 3e-3", "m", "assumption",
    "declared hydraulic diameter of the coolant channels in the cooled plate", "Declared device dimension", "",
    "Across 1-3 mm, with the plate at its favourable end, the stack's liquid U' runs %.3f-%.3f W cm-2 K-1 against "
    "its THF duty of %.3f." % (_one(_STK, "D_H_PLATE", _TM.D_H_PLATE) + (_duty(_STK),)) + _PL_COND)
add("9. Thermal model", "Cooled-plate rib area factor", "1 - 2", "-", "assumption",
    "declared coolant-side wetted area per unit cooled face (channel walls and ribs)", "Declared device dimension", "",
    "Across 1-2, with the plate and channels at their favourable end, the stack's liquid U' runs %.3f-%.3f W cm-2 K-1 "
    "against its THF duty of %.3f." % (_one(_STK, "RIB_AREA", _TM.RIB_AREA) + (_duty(_STK),)) + _PL_COND)
def _jk_with(wall, gap):
    kw, kg = _TM.T_VESSEL_WALL, _TM.JACKET_GAP
    _TM.T_VESSEL_WALL, _TM.JACKET_GAP = (wall, wall), (gap, gap)
    try:
        return _TM.U_liquid(_ROT[1][1])[1]
    finally:
        _TM.T_VESSEL_WALL, _TM.JACKET_GAP = kw, kg
_rcd = _duty(_ROT[1][1])
_wmax = _lq_bisect(lambda w: _jk_with(w, _TM.JACKET_GAP[0]) >= _rcd, _TM.T_VESSEL_WALL[0], _TM.T_VESSEL_WALL[1])
_gmax = _lq_bisect(lambda g: _jk_with(_TM.T_VESSEL_WALL[0], g) >= _rcd, _TM.JACKET_GAP[0], _TM.JACKET_GAP[1])
_JK_CORNER = ("The rotating cylinder's duty is met only in a corner of the declared construction: a wall of at most "
              "%.2f mm with a %.0f mm jacket, or a jacket of at most %.2f mm with a %.0f mm wall."
              % (1e3 * _wmax, 1e3 * _TM.JACKET_GAP[0], 1e3 * _gmax, 1e3 * _TM.T_VESSEL_WALL[0]))
_TC_CHILL = 10.0
def _chill(r):
    q = _TM.q_Wcm2(r[4], _thf_lq[2], r[1]); d = q / (_thf_lq[3] - _TM.TAMB); dc = q / (_thf_lq[3] - _TC_CHILL)
    lo, hi = _TM.U_liquid(r)
    return "%s %.3f -> %.3f, %s" % (lab_of(r), d, dc, _met(dc, lo, hi))
lab_of = lambda r: {"RDE": "rotating disc", "cyl": "rotating cylinder", "stack": "stack"}[[k for k in ("RDE", "cyl", "stack") if k in r[0]][0]]
add("9. Thermal model", "Coolant inlet temperature (liquid cooling)", "25.0", "C", "assumption",
    "the coolant of both liquid-cooling constructions is taken at T_amb, i.e. tap or loop water at room temperature",
    "Declared modelling convention", "",
    "A chilled coolant widens the driving force T_b - T_coolant and lowers each duty in inverse proportion to it. At %.0f C THF's "
    "duties fall as follows (W cm-2 K-1): %s. Warmer coolant works the other way, and the T_amb row gives the "
    "coolant temperatures above which THF's duties leave the declared construction range (%s). %s"
    % (_TC_CHILL, "; ".join(_chill(r) for lab, r in _ROT + [("stack", _STK)]),
       ", ".join("%.1f C for the %s" % (t, lab) for lab, r, t in _LQ_TMAX),
       " ".join("The %s's verdict reverses inside the 20-30 C range that row tests, so it is conditional on the "
                "coolant temperature as well." % lab for lab, r, t in _LQ_TMAX if 20.0 <= t <= 30.0)))
def _others_txt(cells, rng):
    """The other electrolytes at these cells, classed by their own duties against passive rejection and the construction."""
    need, pas = [], []
    for nm, _e, k, tb, _s in _TM.SOLVENTS:
        if nm == "THF":
            continue
        d = [_TM.U_required(r[4], k, r[1], tb) for r in cells]
        if all(v <= _TM.U_passive(r[2], r[3]) for v, r in zip(d, cells)):
            pas.append(nm)
        else:
            assert all(v > _TM.U_passive(r[2], r[3]) for v, r in zip(d, cells)), (nm, "mixed passive/active across cells")
            need.append((nm, d))
    nice = lambda n: "the aqueous reference" if n == "aq. NaOH" else n
    lst = lambda a: a[0] if len(a) == 1 else ", ".join(a[:-1]) + " and " + a[-1]
    cap = lambda t: t[0].upper() + t[1:]
    out = []
    if need:
        dd = [v for nm, d in need for v in d]
        out.append(cap("%s need liquid cooling there too, at duties of %.3f-%.3f W cm-2 K-1, %s."
                   % (lst([nice(nm) for nm, d in need]), min(dd), max(dd),
                      "all met within the declared construction range" if max(dd) <= rng[1] else "not all met within the declared construction range")))
    if pas:
        out.append(cap("%s %s its heat passively there." % (lst([nice(n) for n in pas]), "rejects" if len(pas) == 1 else "reject")))
    return " ".join(out)
add("9. Thermal model", "Liquid cooling: water jacket (forced-flow vessel cells)", "%.3f - %.3f" % _JK_FF, "W cm-2 K-1", "derived",
    "series construction over the vessel's own sigma: the cell's electrolyte-side film (h_int), a Pyrex wall and a "
    "laminar water jacket heated from one wall; value shown for the forced-flow vessel cells (h_int 2000)", INCROP,
    "Table 8.1, p. 519; Table A.3, p. 939; Table A.6, p. 949",
    "The range spans the declared wall thickness and jacket gap. By electrolyte-side film (h_int in W m-2 K-1) it is "
    "%s, in W cm-2 K-1. "
    "Against the forced-flow range, %s; below %.2fx and %.2fx the carried THF conductivity those two duties exceed "
    "the top of that range. Each one-at-a-time sweep in the dimension rows above holds the other dimension at "
    "its favourable end. %s" %
    ("; ".join("%.3f-%.3f at h_int %.0f" % (v[0], v[1], h) for h, v in sorted(_byh.items())), _rot_txt(*_JK_FF),
     _lq_mult(_ROT[0][1], _JK_FF[1]), _lq_mult(_ROT[1][1], _JK_FF[1]), _others_txt([r for lab, r in _ROT], _JK_FF)))
add("9. Thermal model", "Liquid cooling: cooled plate (stack and chip)", "%.3f - %.3f" % _PL, "W cm-2 K-1", "derived",
    "series construction behind the electrode, cooled face equal to the electrode area: the cell's electrolyte-side "
    "film (h_int 5000), a graphite plate and laminar water channels heated from one wall", INCROP,
    "Table 8.1, p. 519; Table A.2, p. 933; Table A.6, p. 949",
    "The range spans the declared plate thickness, channel size and rib factor. The stack's THF duty, %.3f W cm-2 "
    "K-1, is %s (%.3f-%.3f). Below %.2fx "
    "the carried THF conductivity it exceeds the top of that range. %s Nu = 5.39 is the wide-channel (parallel-plate) limit and the "
    "ribs are credited at full fin efficiency, so the range is an upper estimate in those two respects; it is also "
    "one-sided (one cooled face per cell), credits no cooling by the process fluid, omits contact and porous-layer "
    "resistances and takes graphite at its low through-plane conductivity, so its other errors run both ways. "
    "The electrolyte-side film and the thinnest plate cap it: even a "
    "perfect coolant would give at most %.3f." % (_duty(_STK), _met(_duty(_STK), *_PL), _PL[0], _PL[1], _lq_mult(_STK, _PL[1]), _others_txt([_STK], _PL),
                                                   1e-4 / (1.0 / _STK[3] + _TM.T_COOLED_PLATE[0] / _TM.K_GRAPHITE_THROUGH)))
add("9. Thermal model", "§S6 reference lines", "none drawn", "mA cm-2", "assumption",
    "the figure drew horizontal rules at declared design currents of 50, 500 and 1000 mA cm-2 "
    "while the thermal operating point was declared. Each architecture is now judged against its "
    "own median transport ceiling, which is a different number per row, so no reference line is "
    "drawn and the row records only that the constant has left the figure", "display element", "",
    "display-only: no quantity is computed from this row, and no figure draws it.")
def _tamb_sentence(lo=20.0, hi=30.0):
    """Every boil-off ceiling at T_amb = 20 and 30 C against 25 C, computed from thermal_model (chemistry audit,
    pass 6: the typed version said 2 pct, which is DMF's; THF, with the smallest T_b - T_amb, moves about 6 pct)."""
    base = _all_ceilings()
    s_lo, s_hi = _tm_sweep("TAMB", (lo, hi), _all_ceilings)
    per = []
    cmn = {r[0] for r in _TH_OPEN}
    for sl, _k, tb in _TH_SOL:
        grp = []
        for inside in (True, False):
            ks = [key for key in base if key[1] == sl and ((key[0] in cmn) == inside)]
            grp.append((100 * max(s_lo[key] / base[key] - 1 for key in ks), 100 * min(s_hi[key] / base[key] - 1 for key in ks)))
        per.append("%s %+.1f/%+.1f pct in the centimetre-gap cells and %+.1f/%+.1f in the thin-gap ones (T_b - T_amb = %.0f K)"
                   % (sl, grp[0][0], grp[0][1], grp[1][0], grp[1][1], tb - _TM.TAMB))
    rev = [key for r in _TH_RX for key in base if key[0] == r[0]
           and len({(s[key] / r[4] >= 1.0) for s in (base, s_lo, s_hi)}) > 1]
    txt = ("Tested %.0f-%.0f C. The rejection driving force T_b - T_amb moves by 5 K either way, so the ceilings move "
           "most for the lowest-boiling electrolyte: %s, at %.0f / %.0f C. "
           % (lo, hi, ", ".join(per), lo, hi))
    if rev:
        return txt + "Across that range %d verdicts reverse: %s." % (len(rev), "; ".join("%s / %s" % (_nice(k[0]), k[1]) for k in rev))
    inside = [(lab, t) for lab, r, t in _LQ_TMAX if lo <= t <= hi]
    outside = [(lab, t) for lab, r, t in _LQ_TMAX if not lo <= t <= hi]
    lq = ("The coolant of the liquid-cooling constructions is taken at T_amb, so those verdicts move with it as well: "
          "THF's duty can be met within the declared construction range up to a coolant at %s." % ", ".join("%.1f C (%s)" % (t, lab) for lab, r, t in _LQ_TMAX))
    if inside:
        lq += (" The %s verdict therefore reverses inside this range and is conditional on the coolant temperature."
               % " and ".join(lab for lab, t in inside))
    return txt + "Every boil-off verdict holds across the range. " + lq


add("9. Thermal model", "T_amb (§S6)", "25.0", "C", "assumption",
    "standard laboratory ambient, the same 298.15 K as category 1. New row: previously "
    "unregistered as a §S6 constant", "declared modelling convention", "",
    _tamb_sentence())
# Ea(eta) per solvent from the CRC 'Viscosity of Liquids' table: the three organic rows from G-EAVISC's artifact, water
# from data/ea_viscosity_water.py (G-EAVISC's page range starts on the gas table, p. 6-242, so its first 'Water' hit
# is a gas; the liquid row on p. 6-247 prints 0.890 mPa s at 25 C, the registry value).
with io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "ea_viscosity_crc.json"), encoding="utf8") as _fh:
    _EAC = _json.load(_fh)
with io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "ea_viscosity_water.json"), encoding="utf8") as _fh:
    _EAW = _json.load(_fh)
_EA_DECL = 15000.0
_EA_ARR100 = _math.exp(_EA_DECL / 8.314 * (1 / 298.15 - 1 / 373.15))


def _ea_measured_sentence():
    org = []
    for sl in ("MeCN", "DMF", "THF"):
        e = _EAC["solvents"][sl]["Ea_J_per_mol"]
        org.append("%s %s" % (sl, " and ".join("%.1f" % (x / 1000) for x in e)))
    ew = [x["Ea"] for x in _EAW["Ea_intervals_J_per_mol"]]
    eo = [x for sl in ("MeCN", "DMF", "THF") for x in _EAC["solvents"][sl]["Ea_J_per_mol"]]
    return ("MEASURED COMPARISON: the same CRC table that page-anchors mu(25 C) for these solvents (p. 6-243 ff.) also "
            "prints eta at 50 and 75 C, and at 100 C for water, and each row used here reproduces the registry viscosity "
            "at 25 C. The viscous activation energy it implies, in kJ mol-1 over successive 25 K intervals from 25 C, is "
            "%s, and water %s (p. 6-247; %.1f over 25-100 C). By Walden (Lambda eta ~ const) that is the quantity to "
            "judge an Ea(kappa) bound against. The declared 15 kJ mol-1 is %.1f-%.1fx the organic values, an upper bound "
            "by roughly a factor of two for the three organic electrolytes. For the aqueous electrolyte it is %.2f-%.2fx "
            "water's interval values and %.2fx its 25-100 C value, so at the %.0f C boiling point its Arrhenius factor, "
            "%.2f, exceeds the Walden factor %.2f by %.1f pct: an upper bound there by a few per cent, and %s water's "
            "own 25-50 C value."
            % ("; ".join(org), " / ".join("%.1f" % (x / 1000) for x in ew), _EAW["Ea_25_100_J_per_mol"] / 1000,
               _EA_DECL / max(eo), _EA_DECL / min(eo), _EA_DECL / max(ew), _EA_DECL / min(ew),
               _EA_DECL / _EAW["Ea_25_100_J_per_mol"], 100.0, _EA_ARR100, _EAW["walden_factor_25_100"],
               100 * (_EA_ARR100 / _EAW["walden_factor_25_100"] - 1),
               "below" if _EA_DECL < ew[0] else "above"))


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
    "that licenses it is measured: " + CRC,
    "Sect. 6, 'Viscosity of Liquids', p. %s, Water row (eta = %.3f mPa s at 25 C and %.3f mPa s at 100 C); MeCN, DMF "
    "and THF rows of the same table, p. 6-243 ff."
    % (_EAW["source"].split("p. ")[1].split(" ")[0], _EAW["eta_mPas"]["25"], _EAW["eta_mPas"]["100"]),
    "anchor. Walden (kappa ~ 1/eta) on water gives eta(25 C)/eta(100 C) = %.3f/%.3f = %.2f at "
    "100 C, against %.2f from Arrhenius at Ea = 15 kJ mol-1 at the same point -- %.1f pct apart. That "
    % (_EAW["eta_mPas"]["25"], _EAW["eta_mPas"]["100"], _EAW["walden_factor_25_100"], _EA_ARR100,
       100 * (_EA_ARR100 / _EAW["walden_factor_25_100"] - 1)) +
    "agreement is what licenses 15 kJ mol-1 as the upper-bound coefficient rather than a fitted "
    "value; the anchor depends on temperature only, so no conductivity value enters "
    "it. Bracket. The lower bound of the bracket is kappa fixed at 25 C, i.e. the model as it stands "
    "everywhere else in S6, so this row cannot make any ceiling smaller. At the upper bound the "
    "multipliers kappa(T_b)/kappa(25 C) are a function of T_b alone -- %s -- and the unstirred-beaker "
    "ceilings run %s mA cm-2. Across all %d (architecture, solvent) pairs the bracket "
    "factor spans %.2fx-%.2fx. What depends on it: %d of the %d pass/fail verdicts are unchanged "
    "between the two bounds. " % (", ".join("%s %.2fx" % (sl, v["kappa_factor_at_Tboil"])
                                            for sl, v in sorted(_KT["solvents"].items(),
                                                                key=lambda kv: kv[1]["kappa_factor_at_Tboil"])),
                                  ", ".join("%.1f -> %.1f (%s)" % (v["i_boil_25C"], v["i_boil_kappaT"], sl)
                                            for sl, v in _KT["brackets"]["unstirred batch"].items()),
                                  _KT_NPAIRS, _KT["factor_range"]["min"],
                                  _KT["factor_range"]["max"],
                                  _KT_NPAIRS - len(_KT_FLIPS), _KT_NPAIRS) +
    "The %s bound-dependent verdict%s: %s. " % (_KT_WORD, "" if len(_KT_FLIPS) == 1 else "s are",
                                                _KT_FLIP_PROSE) +
    "Every one of them is reported as bound-dependent rather than as a finding. They are exactly the "
    "four cells the surface-area sweep flags, and the two at the rotating disc are also conditional on the gap, "
    "so the marginal cells are marginal on more than one axis, and no cell that clears comfortably at "
    "25 C is put at risk by the bracket." + ("" if _KT_SIG_SAME else 1 / 0) + " The "
    "DMF 6.14x is the least trustworthy entry -- a 128 K extrapolation against a 75 K anchor, in the "
    "solvent and temperature regime where the neglected pairing term is largest -- and no conclusion "
    "rests on it. " + _ea_measured_sentence())
add("9. Thermal model", "U' stirred bath", "0.18", "W cm-2 K-1", "assumption",
    "RE-scoped. this row is inconsistent with the figure's own physics by elevenfold: make_figK.py "
    "computes the stirred beaker at U' = 0.0160 W cm-2 K-1, not 0.18. The two are not the same "
    "architecture -- the registry row assumes a stirred thermostat bath is the external boundary "
    "(h_ext 100-300 rather than 13 W m-2 K-1), whereas §S6 assumes still air. The row is "
    "retained only as the jacketed-glass reference case and is not the §S6 stirred beaker",
    "declared architecture (bath-jacketed glass)", "",
    "Enters no figure and no stated conclusion; retained for comparison. It is %.0f times the still-air "
    "coefficient the \u00a7S6 stirred beaker uses (%.4f W cm-2 K-1), the difference between a thermostat "
    "bath and room air as the external boundary." % (0.18 / _TM.U_passive(*[r[2:4] for r in _TH_RX if
                                                     r[0].startswith("stirred")][0]),
                                                    _TM.U_passive(*[r[2:4] for r in _TH_RX if r[0].startswith("stirred")][0])))
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
add("10. Homogeneous kinetics", "%d mediated rate constants k" % _N_MED, "(Table S6)", "M-1 s-1", "assumption",
    "declared values, each set beside the system it was measured on in data/rate_constant_basis.csv (Table S11): "
    "one measured for the row's own carrier and substrate (Br2 + anisole, Sivey 2015), the NHPI row on PINO + "
    "cyclohexene (Ueda/Masui 1987; it carried a benzylic 0.5 until 2026-10-05), the two ACT rows on turnover "
    "frequencies (Rafiee 2018), the Hofmann and amidyl rows on aqueous HOBr + propionamide (Heeb 2014 Table 6, "
    "3.3 M-1 s-1; a declared 10^3 until 2026-10-07), two bounds from the exemplar's own operation, the rest with no "
    "measurement of the step. Retained as assumptions because none is a measurement in the exemplar's own electrolyte",
    "Table S6 and Table S11",
    "Table S6, k-provenance column (per-row sources); Table S11 (the system each constant was measured on)",
    "The reaction layer x_k = sqrt(D/kC) decides whether the homogeneous step falls inside or outside "
    "the film, and enters only as sqrt(k). Measured, not argued: each k perturbed by 10x and 1/10 one "
    "row at a time with the mediated matrix re-solved moves a cell across 25 mA cm-2 on %d of the "
    "%s rows (%s), the >=25 count of any architecture by at most %d and the >=50 count by at most "
    "%d, and the ordering %s. Table S11 marks the rows that have no measurement of the step."
    % (len(_KS["rows_crossing_25"]), _numword(_KS["n_rows"]) + (" finite-k" if _KS["n_rows"] != _N_MED else ""), "; ".join(_KS["rows_crossing_25"]), _KS["max_count_delta_25"],
       _KS["max_count_delta_50"], "the main text claims (unstirred below stirred below recirculating flow below the ANEC "
       "cell, the three thin-film archetypes above it) holds in every case" if _KS["ordering_preserved"] else "CHANGES"))

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
          "; ".join("%s >=%s count %+d at the low edge, %+d at the high edge" % ({"natural": "unstirred", "stirred": "stirred",
                    "flow": "recirculating flow", "anec": "ANEC", "micro": "microfluidic", "rde": "RDE", "rce": "rotating cylinder"}[a], t, x0, x1)
                    for a, t, x0, x1 in moved))
    return ("Adopted for %d row(s); swept over the declared band %s-%s M-1 s-1 (Table S7j). Across the seven architectures the "
            "unstirred-to-rotating-cylinder gain is %.1f-%.1fx at the adopted value against %.1f-%.1fx at k = 0. "
            "With every sourced row moved to the edges of that band at once, %s (the tally over the %s catalyst rows, "
            "which is the whole of what the fifty-row counts can move by). %s of the %s clears 25 mA cm-2 in some "
            "architecture at the adopted values, %s at the low edges and %s at the high edges."
            % (len(rows), _ck_sci(lo), _ck_sci(hi), gains[0], gains[-1], gains0[0], gains0[-1], mv,
               _numword(_N_CAT), _numword(_SR["rows_clearing25_anywhere"]).capitalize(), _numword(_N_CAT),
               _numword(_SR["rows_clearing25_anywhere_at_band"][0]), _numword(_SR["rows_clearing25_anywhere_at_band"][1])))
add("10. Homogeneous kinetics", "k, low-valent nickel bipyridine + aryl bromide (2 catalyst rows)", "1e2", "M-1 s-1", "assumption",
    "adopted for the Ni-XEC and biaryl-homocoupling rows, whose substrate-consuming step is oxidative addition "
    "of an aryl bromide to a low-valent nickel bipyridine (Ni(0)(bpy) in the homocoupling, by its exemplar's own "
    "account, so the Ni(I) values are an analogue in oxidation state as well as ligand there); the value sits "
    "inside a measured bracket -- the isolated complex [(CO2Et-bpy)NiCl]4 + PhBr gives 7.1 +/- 0.3 in THF at "
    "26 C (3.4-56 across para substituents, Hammett rho +1.1), the amination exemplar's own voltammetry in DMF "
    "loses the Ni(II/I) return wave at 100 mV/s with 4-bromoanisole (k >~ 1e2), and pulse radiolysis of "
    "(dtbbpy)NiBr with 4-bromobenzotrifluoride bounds it below 1e4 -- and is transferred to each row's ligand, "
    "solvent and arene as a declared choice",
    "Ting, S. I.; Williams, W. L.; Doyle, A. G. J. Am. Chem. Soc. 2022, 144, 5575-5582, Fig. 6 p. 5579 "
    "(DOI 10.1021/jacs.2c00462); Kawamata, Y. et al. J. Am. Chem. Soc. 2019, 141, 6392-6402, Fig. 2B p. 6394 "
    "(DOI 10.1021/jacs.9b01886); Till, N. A.; Oh, S.; MacMillan, D. W. C.; Bird, M. J. J. Am. Chem. Soc. 2021, "
    "143, 9332-9337, p. 9334 (DOI 10.1021/jacs.1c04652); Courtois, V.; Barhdadi, R.; Troupel, M.; Perichon, J. "
    "Tetrahedron 1997, 53, 11569-11576, eq. 3 (the zerovalent complex)",
    "S5.7",
    _src_sens("Ni(I)bpy+ArBr"))
add("10. Homogeneous kinetics", "k, cobalt hydride + alkene (2 catalyst rows)", "7e2", "M-1 s-1", "assumption",
    "adopted for the two cobalt-electrocatalytic rows (alkene reduction, isomerization), whose substrate-consuming "
    "step is the reaction of Co(III)-H with the alkene; the value is k_MHAT from the voltammetric simulations of the "
    "Co(salen) hydride with styrene, in which it 'was found to give the observed current decrease and E1/2 shift' "
    "(measured in 0.1 M TBAPF6 in DMF); the authors 'emphasize the qualitative agreement of our simulations and "
    "experiments, as a full parametric fit for every styrene derivative at every concentration was not undertaken', "
    "so it is a value that reproduces the voltammograms rather than a fitted constant, for a step they find proceeds by "
    "insertion of Co-H into the styrene before Co-alkyl homolysis. It is transferred to the rows' unactivated alkenes "
    "and cathodically generated hydride as a declared choice; the authors restrict that picture to styrenes ('non-aryl "
    "and non-activated alkenes ... could adopt distinct mechanisms'), so the bracket reaches a decade below the value. "
    "The exemplar's own kinetics, measured on its Co(salen) cycloisomerization, are first order in the alkene, "
    "consistent with a turnover-limiting step at the alkene; no kinetics are reported for the conditions of the "
    "reduction",
    "Boucher, D. G.; Pendergast, A. D.; Wu, X.; Nguyen, Z. A.; Jadhav, R. G.; Lin, S.; White, H. S.; Minteer, S. D. "
    "J. Am. Chem. Soc. 2023, 145, 17665-17677, p. 17674 (DOI 10.1021/jacs.3c03815); Wilson, C. V.; Holland, P. L. "
    "J. Am. Chem. Soc. 2024, 146, 2685-2700 (DOI 10.1021/jacs.3c12329); Gnaim, S. et al. Nature 2022, 605, 687-695 "
    "(kinetics of conditions B)",
    "S5.7",
    _src_sens("Co-H+alkene"))
_N_FLOOR = _N_CAT - int(_SR.get("n_sourced", 0))
add("10. Homogeneous kinetics", "k, %s catalyst rows with no measured constant" % _numword(_N_FLOOR), "0 (floor); 1-%s swept" % _ck_sci(max(float(k) for k in _CK["k_band_M"])),
    "M-1 s-1", "assumption",
    "the two nickel aminations (their cycles are split between the electrodes: Ni(I) made at the cathode adds the "
    "aryl bromide, and the amine leaves after an anodic oxidation to Ni(III), so no single electrode regenerates the "
    "carrier inside its own film), the Co(salen) allylic C-H amination (no catalyst is regenerated at room "
    "temperature; it turns over by a heat-driven homolysis, a first-order step), "
    "the Ni(tet a) macrocycle aryl-halide cyclization, the Mn-catalyzed diazidation (an azidyl-radical step), "
    "the Cu/anthraquinone photoelectrochemical cyanation (the substrate is consumed by the photoexcited "
    "quinone), the Rh(III) C-H alkenylation and the nickel-electrocatalytic doubly decarboxylative coupling "
    "(low-valent nickel reducing a redox-active ester) carry no measured bimolecular constant "
    "for the step the model needs, so the published matrix keeps them at k = 0 -- turned over at the electrode, "
    "no regeneration inside the film, the floor of the EC' current -- and the declared band is swept instead of "
    "a value being invented",
    "Declared modelling choice; no literature k is claimed for these %s rows" % _numword(_N_FLOOR),
    "S5.7",
    _ck_sentence())
_CSUB_D = sorted(float(r["D_sub_m2s"]) for r in _CSUB)
add("4. Solver species diffusivities", "D_S, substrate (%d catalyst-carried rows, S5.7)" % _N_CAT,
    "%.1e - %.1e" % (_CSUB_D[0], _CSUB_D[-1]), "m2 s-1", "derived",
    "Wilke-Chang on the molecule each exemplar runs, in the row's own solvent, generated by "
    "data/build_catalyst_substrates.py into data/catalyst_substrates.csv, which the catalyst solvers read; "
    "until 2026-10-05 every catalyst row used one declared value, 1.0e-9 m2 s-1 scaled as 1/mu",
    WC55 + " -- applied to each exemplar's own substrate",
    "each structure is the substrate its exemplar names: " + "; ".join(
        "%s (%s)" % (r["substrate"], r["reaction"].split(" (")[0]) for r in _CSUB),
    "Enters only through the substrate cap n_S F D_S C_S/delta and the reaction layer. %d of the %d cells sit "
    "at that cap at the top of the k band, where the ceiling scales linearly with D_S: the +/-25 pct carried "
    "for Wilke-Chang moves those cells' ceilings by the same factor and the others not at all. The k = 0 "
    "ceilings do not depend on it; of the %d published cells carried at a sourced k, %d sit at their substrate cap."
    % (_CK["per_k"]["%g" % max(float(k) for k in _CK["k_band_M"])]["cells_at_substrate_cap"],
       _CK["per_k"]["%g" % max(float(k) for k in _CK["k_band_M"])]["cells"],
       (_CK.get("sourced") or {}).get("n_sourced", 0) * _N_ARCH,
       sum(v["cells_at_substrate_cap"] for v in (_CK.get("sourced") or {}).get("per_row", {}).values())))

# -- 11. Numerical settings (declared solver choices; audited in S5.6) --------
def _solvset_current(d, name):
    """The two solver-setting sweeps were measured against one mediated matrix; once it moves they must be re-run."""
    import hashlib as _hl
    m = _hl.md5(open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "mediated_ec_matrix.csv"), "rb").read()).hexdigest()
    if d.get("matrix_md5") != m:
        raise SystemExit("%s was measured against a different mediated matrix; re-run data/solver_setting_sweeps.py" % name)


def _xc():
    """The residual-scale argument (pass 17): under c_ref = max(c_bulk, 0.01 c_max,bulk) the ex-cell oxidant is referenced to
    1 pct of the largest bulk (the chloride, seeded at C_Cl + 1e-3 mol m-3 in run_excell.jl), and the first-cell terms carry
    delta/dx1 as well; dx1 is read from run_excell.jl's make_problem signature, never typed."""
    src = io.open(_os.path.join(_os.path.dirname(_HERE_D), "julia", "run_excell.jl"), encoding="utf-8").read()
    m = re.search(r"function make_problem\(k_M; N = \d+, dx1 = ([0-9.e-]+), d = delta\)", src)
    assert m, "run_excell.jl's make_problem signature no longer carries dx1"
    dx1 = float(m.group(1)); cref = 0.01 * (_EX["inputs"]["C_Cl_M"] * 1000 + 1e-3); cmax = _EX["c_OX_at_limit_M"] * 1000
    return {"cref": cref, "ratio": cmax / cref, "dx1_um": dx1 * 1e6, "terms": (cmax / cref) * (_EX["delta_um"] * 1e-6 / dx1)}


_XC = _xc()
# the ex-cell delta-continuation walk under the alternative scale (run_excell.jl, isolated copy; data/solver_setting_sweeps.py)
_WALK = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "cref_scale_sweep.json"),
                           encoding="utf-8"))["excell_walk_alt_scale"]
assert any(w["converged"] for w in _WALK) and any(not w["converged"] for w in _WALK), _WALK

def _cref_sentence():
    """The mediated matrix re-solved without the in-film maximum (results/cref_scale_sweep.json, run_mediated.jl in an
    isolated copy)."""
    d = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "cref_scale_sweep.json"), encoding="utf-8"))
    _solvset_current(d, "results/cref_scale_sweep.json")
    mv = d["moved"]
    assert d["n_cells"] == d["bit_identical"] + d["within_1e-9"] + len(mv)
    assert all(m["rel_change"] < 0 and "ceases" in m["alternative_limiter"] and "plateau" in m["published_limiter"] for m in mv), mv
    rx = sorted({m["reaction"] for m in mv})
    assert rx == ["Br- oxidation / electrophilic bromination"], rx
    return ("Re-solving all %d mediated cells without the in-film maximum leaves %d of them unchanged (%d bit-identical, "
            "the rest within 1e-9), while the bromination in its %s stops short of the plateau the adopted rule reaches, "
            "%s low: the bromine that accumulates behind its detached front lies far above the 1 pct floor, and these are the "
            "two thickest films, where the scale's 1/delta factor bites hardest -- the mechanism described above for the "
            "chloride oxidant."
            % (d["n_cells"], d["n_cells"] - len(mv), d["bit_identical"],
               " and ".join(m["reactor"].lower() for m in mv) + (" films" if len(mv) > 1 else " film"),
               " and ".join("%.1f pct" % (-100 * m["rel_change"]) for m in mv)))

def _negc_sentence():
    """NEGLIGIBLE_C swept on the production path (results/negligible_c_sweep.json, from run_mediated.jl in isolated copies)."""
    d = _json.load(io.open(_os.path.join(_os.path.dirname(_HERE_D), "results", "negligible_c_sweep.json"), encoding="utf-8"))
    _solvset_current(d, "results/negligible_c_sweep.json")
    below = [c for c in d["cells_with_a_species_below_1e-10_of_bulk"]]
    assert d["max_rel_change_vs_published"] == 0.0 and below, d["max_rel_change_vs_published"]
    rx = sorted({c["reaction"] for c in below})
    assert rx == ["Br- oxidation / electrophilic bromination"], rx
    assert d.get("rule_off") and all(c["rel_change"] < 0 for c in d["rule_off"]), "the rule-off control must stall cells LOW"
    _lim = {(r["reaction"], r["reactor"]): r["limiter"] for r in csv.DictReader(io.open(_os.path.join(
        _os.path.dirname(_HERE_D), "julia", "mediated_ec_matrix.csv"), encoding="utf-8"))}
    assert all("ceases" in c["limiter"] or "wall" in c["flag"] + c["limiter"] for c in d["rule_off"]), \
        "the sentence says the rule-off solves STALL; one ended on something else: %r" % [c["limiter"][:40] for c in d["rule_off"]]
    assert all(_lim[(c["reaction"], c["reactor"])].startswith("plateau") for c in d["rule_off"]), \
        "the sentence says the rule-off cells stall short of their PLATEAU; a published limiter is not a plateau"
    return ("Swept over ten decades, %s to %s, re-solving every architecture of three mediated rows by the production "
            "path: the electrophilic bromination, whose anisole falls below 1e-10 of bulk at the electrode in %s "
            "(down to %.0e) so that the rule excludes it from the step norm there, the Hofmann rearrangement "
            "and the ACT alcohol oxidation. All %d cells return the published value at every threshold, to every printed "
            "digit. Switching the rule off (threshold 0, the whole step rescaled by its largest component) stalls %s of the "
            "bromination's cells short of their plateau, by up to %.0f pct, which is why the rule exists; the dead zone "
            "that triggers it is described in \u00a7S5.5."
            % (("%.0e" % max(d["thresholds"])).replace("e-0", "e-"), ("%.0e" % min(d["thresholds"])).replace("e-0", "e-"),
               "every one of its seven cells" if len(below) == 7 else "%d of its seven cells" % len(below), min(c["c_sub_over_bulk"] for c in below),
               d["n_cells"], _numword(len(d["rule_off"])), -100 * min(c["rel_change"] for c in d["rule_off"])))

for n_, v, meth, sens in [
 ("Film nodes N (Stage-1 / EC')", "80 / 90", "finite-volume mesh resolution",
  "Mesh independence verified: at most 1 pct drift over N = 40-160 (\u00a7S5.6)."),
 ("First cell dx1", "max(0.02 um, min(x_k/50, 0.9 delta/N))",
  "first-cell size matched to the reaction layer x_k",
  "Matched to the reaction layer so that the mesh does not hyper-stretch; on the production stretch the binary "
  "migration comparison sits within %.2f pct of the analytic ceiling (\u00a7S5.6)."
  % abs(float(next(r for r in _AG if r["gate"] == "G8b")["err_pct"]))),
 ("Residual scale c_ref (per species)", "max(c_bulk, 0.01 c_max,bulk, max_x c)",
  "reference concentration in the flux D c_ref/delta that each conservation residual is divided by "
  "before the ||F||_inf test, in both solvers (the verification solver of \u00a7S5.3 and \u00a7S5.6, and "
  "the production solver, which carries Stage 1 at k = 0 and Stage 2); the last term is the "
  "species' largest concentration in the current "
  "iterate, so an electrogenerated species that is a trace in the bulk but molar at the electrode "
  "is held to the same relative tolerance as the rest",
  ("Perturbation: c_ref = max(c_bulk, 0.01 c_max,bulk) alone. The chloride ex-cell system's oxidant "
  "(%.2g mol m-3 in the bulk, %.1f M of oxidizing equivalents at its carrier limit, %.1f M as Cl2 or HOCl) is then "
  "referenced to the 1 pct floor, %.0f mol m-3, about %.0f times below the concentration it reaches; on the %.0f um "
  "film, whose first cell is %g um, its first-cell flux terms are then of order %s in scaled units, so the 1e-9 "
  "tolerance asks for a relative accuracy of %s on them, the double-precision floor, and the concentration-control "
  "walk stops on an existing branch at "
  "%s, reaching it only on the %s film. With the in-film maximum included every film reaches 2.00x Fick. "
  % (_EX["inputs"]["c_OX_bulk_molm3"], _EX["c_OX_at_limit_M"], _EX["c_OX_at_limit_M"] / 2,
     _XC["cref"], _XC["ratio"], _EX["delta_um"], _XC["dx1_um"], ("%.1e" % _XC["terms"]).replace("e+0", "e"),
     "%.1e" % (1e-9 / _XC["terms"]),
     " and ".join(("%d pct of the analytic carrier limit on a %d um film" if j == 0 else "%d pct on a %d um film")
                  % (w["pct_of_limit"], w["delta_um"])
                  for j, w in enumerate(sorted([w for w in _WALK if not w["converged"]], key=lambda w: -w["delta_um"]))),
     " and ".join("%d um" % w["delta_um"] for w in _WALK if w["converged"])))
  + _cref_sentence() + " The verification solver of \u00a7S5.3 and \u00a7S5.6 uses the same rule; "
  "under its own alternative, max(c_bulk, 1 mol m-3), every closed-form agreement of \u00a7S5.6 is "
  "identical, the \u00a7S5.3 support-ratio sweep is byte-identical, and the illustrative "
  "concentration profiles move by at most 4e-6 relative."),
 ("Newton tolerance ||F||_inf", "1e-9", "row-scaled residual convergence criterion",
  "Tightening below 1e-9 changes no reported digit; the discrete charge-conservation check passes "
  "at %s." % _AG_CC),
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
  "refining the continuation 7.5-fold moves it by at most %.2f pct (\u00a7S5.6)." % _AG_G12),
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
  _negc_sentence()),
]:
    add("11. Numerics", n_, v, "-", "assumption",
        meth + ". A declared solver setting with no physical content",
        "Declared numerical setting; verified against the analytic limits of \u00a7S5.6", "", sens)

# -- Table S12 pointers (G-THERMAXIS) ------------------------------------------
# Every registry row whose input changes a cooling class inside its tested range points to SI Table S12, which lists each
# change, and states the dependence as conditional in its own sentence (so the assumption ledger tiers it T3). A row named
# by the sweep must exist; a row that already carries the pointer is left alone.
_S12_ROWS = sorted({rn for t in _TAX["table"] for rn in t["rows"]})
_S12_NAMES = {r["parameter"] for r in R}
assert set(_S12_ROWS) <= _S12_NAMES, sorted(set(_S12_ROWS) - _S12_NAMES)
for _r in R:
    if _r["parameter"] in _S12_ROWS and "Table S12" not in _r["sensitivity"]:
        _r["sensitivity"] = (_r["sensitivity"].rstrip().rstrip(".") + ". Every change of cooling class this input causes "
                             "over the range Table S12 sweeps for it is listed there. Those verdicts are conditional on it.")

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
