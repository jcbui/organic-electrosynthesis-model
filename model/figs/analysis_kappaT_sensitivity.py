"""Temperature-dependence sensitivity for the Fig K thermal ceilings.

THE ISSUE: the thermal model evaluates kappa at 25 C while predicting cells running at
60-153 C. Conductivity rises with temperature, so fixing kappa at 25 C OVERSTATES ohmic
heat and therefore UNDERSTATES the boil-off ceiling. The 25 C result is a conservative
lower bound, not an estimate, and that was never disclosed.

WHY A BRACKET AND NOT A CORRECTION: two effects compete.
  (i)  viscosity falls with T -> ions move faster -> kappa rises (Walden: kappa ~ 1/eta)
  (ii) the dielectric constant falls with T -> ion pairing INCREASES -> kappa rises less
Arrhenius/Walden captures (i) only, so it is an UPPER bound on the ceiling. The literature
is explicit that a single Arrhenius law describes organic liquid electrolytes poorly for
exactly this reason (the T-dependence of the prefactor's dielectric constant), and that
VFT-type forms are needed. Absent measured kappa(T) for these specific electrolytes, the
defensible statement is a BRACKET:
      lower bound  = kappa fixed at 25 C          (current model, conservative)
      upper bound  = Walden/Arrhenius scaling      (neglects the pairing penalty)
The true ceiling lies between. Anything narrower needs measured kappa(T).

ANCHOR: the coefficient is validated against water, whose viscosity IS well tabulated:
eta(25 C)/eta(100 C) = 0.890/0.282 = 3.16, so Walden predicts kappa x3.16 at 100 C.
Arrhenius with Ea = 15 kJ/mol gives x3.37 at the same point - agreement within 7%,
which is what licenses Ea = 15 kJ/mol as the upper-bound coefficient here.

SINGLE SOURCE OF TRUTH (2026-08-02). This script used to retype its own SOLVENTS and
REACTORS tables. That is exactly the drift mechanism figs/thermal_model.py was extracted
to kill: when the 2026-08-02 kappa sourcing pass promoted MeCN 1.80 -> 1.89 S/m and
aq. NaOH 18.00 -> 17.80 S/m in the registry and in thermal_model.py, this file kept the
old numbers and regenerated results/figK_kappaT_sensitivity.json self-consistently but
WRONG, while SI section S6.3 pointed the reader at that JSON by name. Both tables are now
imported from thermal_model.py, as make_figK.py already does, so the two cannot desync
again. The kappa(T) physics below is unchanged and stays local, because it is this
analysis's own overlay on the shared 25 C model, not part of it:
    kappa_T(k25, T_C, Ea) = k25 * exp[(Ea/R)(1/298.15 - 1/(T_C + 273.15))],  Ea = 15 kJ/mol
The bracket is evaluated by feeding kappa_T() into the SHARED i_boil(), so the bisection,
the Tafel term and the q(i) form are the same code that produces Fig. K.

JSON KEYS. thermal_model's reactor labels carry newlines and LaTeX ("250 $\\mu$m\\nmicro-
fluidic") because they are axis tick labels. _plain() strips both, reproducing the plain
keys this artifact has always used, so the emitted JSON stays key-compatible with SI S6.3.
"""
import numpy as np, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); SEC4 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
# THE thermal model. SOLVENTS (kappa at 25 C, T_boil, provenance state) and REACTORS
# (gap, sigma, h_int, design current) are NOT redefined here -- see the docstring.
from thermal_model import (TAMB, H_EXT, SOLVENTS, REACTORS, U_passive, q_Wcm2, i_boil)

R = 8.314          # J/mol K, gas constant for the Arrhenius overlay
EA_UPPER = 15000.0  # J/mol, upper-bound coefficient; ASSUMPTION, anchored on water below


def _plain(label):
    """thermal_model tick label -> the plain JSON key this artifact has always used."""
    return label.replace("\n", " ").replace("$\\mu$", "u")


def kappa_T(k25, T_C, Ea):
    """Arrhenius/Walden scaling of kappa from 25 C to T_C. Ea = 0 recovers the 25 C model."""
    return k25*np.exp((Ea/R)*(1/298.15 - 1/(T_C + 273.15)))


def i_boil_T(k25, gap, Tb, U, Ea):
    """Boil-off ceiling with kappa evaluated AT the boiling point, via the shared solver."""
    return i_boil(kappa_T(k25, Tb, Ea), gap, Tb, U)


# water anchor, from CRC tabulated viscosity
anchor = {"eta_25_cP": 0.890, "eta_100_cP": 0.282, "walden_ratio": 0.890/0.282,
          "arrhenius_ratio_Ea15": float(kappa_T(1.0, 100., EA_UPPER)),
          "agreement_pct": 100*abs(kappa_T(1.0, 100., EA_UPPER) - 0.890/0.282)/(0.890/0.282)}
print(f"WATER ANCHOR: Walden x{anchor['walden_ratio']:.2f} vs Arrhenius(Ea=15 kJ/mol) "
      f"x{anchor['arrhenius_ratio_Ea15']:.2f}  -> {anchor['agreement_pct']:.1f}% apart\n")

out = {"note": "25 C kappa is a conservative LOWER bound on the ceiling; Walden/Arrhenius "
               "(Ea=15 kJ/mol) is an UPPER bound because it neglects the ion-pairing "
               "penalty from falling dielectric constant. True ceiling lies between.",
       "source_of_truth": "SOLVENTS and REACTORS imported from figs/thermal_model.py; "
                          "kappa values are the registry values of data/electrolytes.csv "
                          "as of the 2026-08-02 sourcing pass (MeCN 1.89, aq. NaOH 17.80 S/m).",
       "T_amb_C": TAMB, "h_ext_Wm2K": H_EXT,
       "Ea_upper_J_per_mol": EA_UPPER, "water_anchor": anchor,
       "solvents": {}, "brackets": {}}

# kappa multiplier at each solvent's boiling point (depends on T_boil only, not on k25)
print(f"{'solvent':10}{'kappa25 S/m':>13}{'state':>12}{'T_boil C':>10}{'kappa(Tb)/kappa(25)':>21}")
for sl, elyte, k25, Tb, prov in SOLVENTS:
    fac = float(kappa_T(1.0, Tb, EA_UPPER))
    out["solvents"][sl] = {"electrolyte": elyte, "kappa_25C_S_per_m": k25,
                           "kappa_provenance_state": prov, "T_boil_C": Tb,
                           "kappa_factor_at_Tboil": fac,
                           "kappa_at_Tboil_S_per_m": float(kappa_T(k25, Tb, EA_UPPER))}
    print(f"{sl:10}{k25:13.2f}{prov:>12}{Tb:10.0f}{fac:21.2f}")

print(f"\n{'reactor':26}{'solvent':10}{'i_design':>9}{'25C (low)':>11}{'kap(T) (high)':>14}{'factor':>8}")
for rl, L, sig, hi, iop in REACTORS:
    U = U_passive(sig, hi)
    rkey = _plain(rl)
    for sl, elyte, k25, Tb, prov in SOLVENTS:
        lo_ = i_boil_T(k25, L, Tb, U, 0.0); hi_ = i_boil_T(k25, L, Tb, U, EA_UPPER)
        out["brackets"].setdefault(rkey, {})[sl] = {
            "electrolyte": elyte, "i_design": iop, "i_boil_25C": lo_, "i_boil_kappaT": hi_,
            "factor": hi_/lo_, "margin_25C": lo_/iop, "margin_kappaT": hi_/iop,
            "verdict_changes": bool((lo_ < iop) != (hi_ < iop))}
        flag = "  <-- VERDICT FLIPS" if (lo_ < iop) != (hi_ < iop) else ""
        print(f"{rkey:26}{sl:10}{iop:9.0f}{lo_:11.0f}{hi_:14.0f}{hi_/lo_:8.2f}{flag}")

facs = [d["factor"] for v in out["brackets"].values() for d in v.values()]
out["factor_range"] = {"min": min(facs), "max": max(facs), "n_pairs": len(facs)}
flips = [(r, s) for r, v in out["brackets"].items() for s, d in v.items() if d["verdict_changes"]]
out["n_verdict_flips"] = len(flips)
out["verdict_flips"] = [{"reactor": r, "solvent": s} for r, s in flips]

_NEG = "--negative-control" in sys.argv
_OUTP = os.path.join(SEC4, "results", "figK_kappaT_sensitivity" +
                     ("_NEGCONTROL" if _NEG else "") + ".json")
json.dump(out, open(_OUTP, "w"), indent=2)
print(f"\nbracket factor spans {min(facs):.2f}x - {max(facs):.2f}x over {len(facs)} pairs")
print(f"{len(flips)} of {len(facs)} (reactor, solvent) verdicts flip between the bounds:")
for r, s in flips: print(f"   {r} / {s}")
print("\nsaved -> %s" % os.path.relpath(_OUTP, SEC4))


# ── G-KAPPAT: the flip set must match the one the SI DECLARES BY NAME ──────────────────────
# This file was a report with no verdict of any kind: it printed the flip list and stopped, so a
# NEW flip -- a conclusion silently becoming conditional on kappa(T) -- would have scrolled past
# as ordinary output.
#
# Two weaker designs were tried and thrown away, both green lights from noise. Splitting the SI
# into sentences does not work (decimals split mid-number, and flattened tables read as prose),
# and matching a window around the words "reverses"/"flips" does not either: a 440-character
# window sweeps in whatever else is nearby, so an unrelated paragraph about the flow cell
# "disclosed" a microfluidic flip. Both reported PASS on evidence that meant nothing.
#
# What is actually checkable is that the SI names the flip explicitly, in a sentence built for
# the purpose, WITH ITS NUMBERS. That sentence is parsed here and compared against the computed
# set. If the sentence is missing the gate FAILS rather than skipping (trap 10: a vanished phrase
# is a failure, not an exemption).
sys.path.insert(0, os.path.join(SEC4, "data"))
from docx_text import asserted_text                                          # noqa: E402
import re as _re                                                             # noqa: E402

_SI = _re.sub(r"\s+", " ", asserted_text(os.path.join(SEC4, "SI_Section4_Transport_Model.docx")))
# 2026-09-12: the bracket reverses a SET of verdicts on the seven-archetype table, not one, so the
# gate parses every declared flip and compares the SET. The SI writes each as
# "<solvent> in the <architecture> (<lo> -> <hi> mA cm-2 against <design>)".
_UNIT = r"mA cm[^0-9]{0,3}2"
_M = _re.findall(r"(THF|MeCN|DMF|aqueous NaOH|aq\. NaOH) in the ([A-Za-z0-9.\s$\\]+?) \((\d+) ?(?:->|\u2192|\u2013) ?"
                 r"(\d+) " + _UNIT + r" against (\d+)\)", _SI)
_NEG = "--negative-control" in sys.argv

if _NEG:
    _EA_N = EA_UPPER * 4.0
    _new = []
    for rl, L, sig, hi, iop in REACTORS:
        U = U_passive(sig, hi)
        for sl, elyte, k25, Tb, prov in SOLVENTS:
            lo_ = i_boil_T(k25, L, Tb, U, 0.0); hi2 = i_boil_T(k25, L, Tb, U, _EA_N)
            if (lo_ < iop) != (hi2 < iop):
                _new.append((_plain(rl), sl))
    print("\nNEGATIVE CONTROL: Ea raised 4x to %.0f kJ/mol -> %d flip(s) against the %d the SI "
          "declares." % (_EA_N / 1000.0, len(_new), len(flips)))
    ok = len(_new) != len(flips)
    print("G-KAPPAT control: %s"
          % ("GOOD -- the flip set moved to %s, which no longer matches the declared "
             "flip set" % (_new,) if ok else "BAD -- test is inert, the flip set did not move"))
    sys.exit(0 if ok else 1)

print("")
if _M:
    _SOLNAME = {"aqueous NaOH": "aq. NaOH"}
    _declared = sorted({(_r.strip(), _SOLNAME.get(_s.strip(), _s.strip()))
                        for _s, _r, _a, _b, _c in _M})
    _computed = sorted({(r, s) for r, s in flips})
    if _declared != _computed:
        print("G-KAPPAT: FAIL -- the SI declares the flip set %s but the model computes %s"
              % (_declared, _computed))
        sys.exit(1)
    print("G-KAPPAT: PASS -- the SI declares every one of the %d verdicts the bracket reverses, "
          "and no others" % len(_computed))
    sys.exit(0)
if not _M:
    print("G-KAPPAT: FAIL -- the SI no longer contains the sentence declaring which verdict the "
          "kappa(T) bracket reverses ('The single flip is <solvent> in the <reactor>, "
          "<lo> -> <hi> mA cm-2 against a <design> mA cm-2'). The flip set computed here is %s "
          "and nothing published states it." % (flips,))
    sys.exit(1)
_si_solv, _si_react = _M.group(1).strip(), _M.group(2).strip()
_si_lo, _si_hi, _si_design = (float(_M.group(3)), float(_M.group(4)), float(_M.group(5)))
_want = [(_si_react, _si_solv)]
_fails = []
if [(r, s_) for r, s_ in flips] != _want:
    _fails.append("computed flip set %s but the SI declares %s" % (flips, _want))
else:
    _d = out["brackets"][_si_react][_si_solv]
    if abs(_d["i_boil_25C"] - _si_lo) > 1.5 or abs(_d["i_boil_kappaT"] - _si_hi) > 1.5:
        _fails.append("the SI declares %.0f -> %.0f mA cm-2 for %s / %s; the model gives "
                      "%.1f -> %.1f" % (_si_lo, _si_hi, _si_react, _si_solv,
                                        _d["i_boil_25C"], _d["i_boil_kappaT"]))
    if abs(_d["i_design"] - _si_design) > 0.5:
        _fails.append("the SI declares a %.0f mA cm-2 design current for that cell; the model "
                      "uses %.0f" % (_si_design, _d["i_design"]))
# TRAP 9: the check above covers ONE sentence, and the same pair is quoted in three places --
# S6.3's declaration, S6.1's narrative, and the Ea row of Table S7. When the boiling points moved,
# S6.1 was corrected and the other two were not, so the document disagreed with itself in a
# quantity it states three times. Cover EVERY claim of that ceiling, not the one that was noticed.
for _m2 in _re.finditer(r"ceiling reaches (\d+)\s*mA cm", _SI):
    _w = _SI[max(0, _m2.start() - 260): _m2.end() + 260]
    if _si_solv not in _w and "bracket" not in _w.lower():
        continue                       # a different solvent's ceiling, legitimately different
    if abs(float(_m2.group(1)) - _si_hi) > 1.5:
        _fails.append("a second statement of the same bracket ceiling reads %s mA cm-2 where the "
                      "SI's own declaration and the model both give %.0f -- the document states "
                      "this quantity in more than one place and they disagree"
                      % (_m2.group(1), _si_hi))
print("G-KAPPAT: %s" % ("PASS" if not _fails else "FAIL"))
for _f in _fails:
    print("  " + _f)
if _fails:
    sys.exit(1)
print("  SI declares one reversal -- %s in the %s, %.0f -> %.0f mA cm-2 against %.0f -- and the"
      % (_si_solv, _si_react, _si_lo, _si_hi, _si_design))
print("  model reproduces exactly that pair and those numbers. The other %d of %d verdicts hold"
      % (len(facs) - len(flips), len(facs)))
print("  across the whole 25 C-to-Arrhenius bracket.")
