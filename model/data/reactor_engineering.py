#!/usr/bin/env python3
"""G-RXNENG -- the reactor-engineering quantities i_lim alone cannot express.

    cd Section4_Model && python data/reactor_engineering.py
    cd Section4_Model && python data/reactor_engineering.py --negative-control

WHY
---
A limiting current density is a FLUX. The quantities a reactor engineer needs to compare
architectures are a productivity and a cost of achieving it, and thinning the gap moves those in
OPPOSITE directions to the flux:

    i_lim  ~ 1/delta          rises as the gap closes
    tau    = L/u             residence time per pass, set by the channel, not by delta
    X_pass = 1 - exp(-k_m tau / h)   conversion per pass, which FALLS when h falls at fixed tau
    dP     = 12 mu u L / h^2  laminar pressure drop between plates, which rises as 1/h^2

So intensification buys flux and spends residence time and pumping power. This script computes
all four for a DECLARED pair of generic laminar parallel-plate channels (1 mm / 5 cm / 5 cm s-1
and 250 um / 2.5 cm / 10 cm s-1). Until 2026-09-07 these were the model's two flow archetypes;
the archetypes are now the measured Watkins 2023 films and the Mo 2020 microfluidic cell, and
this pair survives only as the illustration of S8.1 -- it is registered as such
("Illustrative channel pair (S8.1)", assumption class) and no archetype column is computed
from it.

WHAT IS ASSUMED
---------------
  * Plug flow with a wall sink, one active electrode, specific area a = 1/h. A real cell has a
    velocity profile; this is the standard first-pass estimate and it OVERSTATES conversion,
    which is the direction that does not flatter the intensification argument.
  * k_m is taken from the model's own Leveque correlation at the median carrier D of the set, so
    it inherits every property assumption already declared in S1.1.
  * dP is the fully developed laminar result for a parallel-plate channel; entrance effects and
    manifolding are excluded, so it is a LOWER bound on real pumping cost.
  * No reaction kinetics: X_pass is the transport-limited conversion, the same ceiling logic the
    rest of the model uses.
"""
import csv
import io
import json
import math
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# (name, gap h [m], length L [m], velocity u [m/s]) -- the declared illustrative pair of S8.1
# (registry row "Illustrative channel pair (S8.1)"); NOT the model's flow archetypes since 2026-09-07
SI_DOCX = "SI_Section4_Transport_Model.docx"
CHANNELS = [("Illustrative channel, 1 mm gap", 1.0e-3, 5.0e-2, 0.05),
            ("Illustrative channel, 250 um gap", 250e-6, 2.5e-2, 0.10)]


def km_leveque(D, nu, h, L, u):
    dh = 2.0 * h
    Re = u * dh / nu
    Sc = nu / D
    if Re >= 2300.0:
        raise AssertionError("Leveque outside laminar regime (Re=%.0f)" % Re)
    Sh = 1.85 * (Re * Sc * dh / L) ** (1.0 / 3.0)
    return max(Sh * D / dh, D / (h / 2.0))


def main(neg=False):
    rx = list(csv.DictReader(io.open(os.path.join(HERE, "reactions_50.csv"), encoding="utf-8")))
    sol = {r["solvent"]: r for r in
           csv.DictReader(io.open(os.path.join(HERE, "solvents.csv"), encoding="utf-8"))}
    Ds, nus = [], []
    for r in rx:
        s = sol.get(r["solvent"].strip()) or sol.get(r["solvent"].split()[0])
        if not s:
            continue
        Ds.append(float(r["D_cm2s"]) * 1e-4)
        nus.append(float(s["mu_mPas"]) * 1e-3 / (float(s["rho"]) * 1000.0))
    D, nu = st.median(Ds), st.median(nus)
    mu = st.median([float(s["mu_mPas"]) * 1e-3 for s in sol.values()])
    if neg:
        # The factor has to respect the correlation. Leveque gives Sh ~ Sc^(1/3), so
        # k_m = Sh D / d_h scales as D^(2/3), NOT as D: a first attempt used D x100, which lifts
        # k_m only 21.5x and reaches 33 per cent conversion, and the control reported the balance
        # broken when it was the control's own arithmetic that was wrong. Saturation needs
        # k_m tau / h > 5, i.e. a factor above ~4500 on D.
        D *= 1.0e4
    print("  corpus medians: D = %.3e m2/s, nu = %.3e m2/s, mu = %.3f mPa s\n" % (D, nu, mu * 1e3))

    print("  %-28s %8s %8s %9s %10s %10s" % ("archetype", "delta/um", "tau/s", "k_m/(um/s)",
                                             "X_pass/%", "dP/kPa"))
    rep = []
    for name, h, L, u in CHANNELS:
        km = km_leveque(D, nu, h, L, u)
        delta = D / km
        tau = L / u
        X = 1.0 - math.exp(-km * tau / h)          # plug flow, wall sink, a = 1/h
        dP = 12.0 * mu * u * L / (h * h)
        rep.append(dict(archetype=name, gap_m=h, length_m=L, velocity_m_s=u,
                        delta_um=delta * 1e6, tau_s=tau, km_um_s=km * 1e6,
                        conversion_per_pass=X, dP_Pa=dP))
        print("  %-28s %8.2f %8.3f %9.2f %10.2f %10.3f"
              % (name, delta * 1e6, tau, km * 1e6, 100 * X, dP / 1e3))

    a, b = rep[0], rep[1]
    r_delta = a["delta_um"] / b["delta_um"]
    r_X = b["conversion_per_pass"] / a["conversion_per_pass"]
    r_dP = b["dP_Pa"] / a["dP_Pa"]
    r_tau = b["tau_s"] / a["tau_s"]
    print("\n  THINNING 1 mm -> 250 um, AT THE MODEL'S OWN OPERATING POINTS:")
    print("    delta falls %.2fx  (so i_lim rises by about the same factor)" % r_delta)
    print("    residence time falls %.2fx" % (1.0 / r_tau))
    print("    conversion per pass changes %.2fx" % r_X)
    print("    pressure drop rises %.1fx" % r_dP)
    print("\n  The flux gain is real and it is NOT free: the same step costs %.0f%% of the "
          "residence\n  time and %.0fx the pumping pressure, and conversion per pass %s."
          % (100 * (1 - r_tau), r_dP, "falls" if r_X < 1 else "rises"))

    out = os.path.join(ROOT, "results",
                       "reactor_engineering%s.json" % ("_NEGCONTROL" if neg else ""))
    json.dump({"median_D_m2_s": D, "median_nu_m2_s": nu, "channels": rep,
               "ratios": {"delta": r_delta, "tau": r_tau, "X_pass": r_X, "dP": r_dP}},
              io.open(out, "w", encoding="utf8"), indent=1)
    print("\n  -> %s" % os.path.relpath(out, ROOT))

    if neg:
        ok = all(e["conversion_per_pass"] > 0.99 for e in rep)
        print("\nNEGATIVE CONTROL: D x1e4 (Leveque makes k_m ~ D^(2/3)), so a wall sink must take "
              "conversion per pass to ~1.")
        print("G-RXNENG control: %s"
              % ("GOOD -- conversion saturates as it must" if ok else
                 "BAD -- conversion did not saturate under an absurd D; the balance is wrong"))
        return 0 if ok else 1
    bad = [e for e in rep if not (0.0 < e["conversion_per_pass"] < 1.0)]
    if bad:
        print("\nG-RXNENG: FAIL -- conversion per pass outside (0,1)")
        return 1
    print("\nG-RXNENG: PASS -- residence time, conversion per pass and pumping cost computed "
          "for the declared S8.1 channel pair (an illustration; no archetype is computed from it)")
    return 0


def check_si(neg=False):
    """G-RXNENG-SI -- bind the DIRECTION WORDS of S8.1 to the computed ratios.

    The four magnitudes in S8.1 are already interpolated from this script's JSON, so they cannot
    drift. What CAN drift is the prose around them: the section's whole point is that conversion
    per pass RISES against the intuition that it falls, and that word is typed. If a property
    update ever pushed the ratio below 1, the SI would read "RISES 0.8x" -- a sentence that
    contradicts its own number while every numeric gate stayed green. The same applies to
    "under 5%", which bounds two computed conversions with a typed literal.

    It FAILS if the sentence is absent (trap 10): a claim that has been reworded away is not a
    claim that passes.
    """
    sys.path.insert(0, HERE)
    from docx_text import asserted_text
    import unicodedata
    d = json.load(io.open(os.path.join(ROOT, "results", "reactor_engineering.json"),
                          encoding="utf-8"))
    r, ch = d["ratios"], d["channels"]
    t = unicodedata.normalize("NFKC", re.sub(r"\s+", " ",
                                            asserted_text(os.path.join(ROOT, SI_DOCX))))
    if neg:                       # perturb the MODEL side, never the shipped document
        r = dict(r, X_pass=0.80)
    fails, checked = [], 0

    # (1) the direction word must agree with the sign of the ratio it introduces
    # Each entry is (the typed word, the ratio it introduces, what >1 MEANS for that word).
    # delta's ratio is a FALL factor -- S8.1 writes "lowers delta by 2.52x" -- so >1 is still the
    # direction the word claims; X_pass and dP are rise factors. Both must exceed 1 or the word
    # contradicts its own number. The pattern allows the few words the sentence puts between the
    # verb and the numeral ("lowers delta by"), which is why the first draft of this gate reported
    # the phrase missing when it was present.
    # Each pattern is anchored on the SUBJECT the ratio belongs to, not on the verb alone. The
    # earlier version matched the bare word "rises" and took the FIRST ratio after it, so once a
    # voice pass put the conversion sentence ahead of the pumping sentence it read the conversion
    # ratio and compared it against the pressure drop. Binding the number to the quantity named
    # beside it is the rule this repository already applies to every other prose check.
    for word, key, pat in (
            ("conversion per pass rises", "X_pass",
             r"conversion per pass rises by ([0-9]+\.[0-9]+)\u00d7"),
            ("pressure drop rises", "dP",
             r"at fixed velocity and rises ([0-9]+\.[0-9]+)\u00d7"),
            ("lowers delta", "delta",
             r"lowers \u03b4 by ([0-9]+\.[0-9]+)\u00d7")):
        m = re.search(pat, t)
        if not m:
            fails.append("S8.1 no longer states %r with its ratio -- reworded or removed" % word)
            continue
        checked += 1
        got, want = float(m.group(1)), r[key]
        if abs(got - want) > 0.02 * want:
            fails.append("S8.1 says %s %.2fx but the model gives %.2fx" % (word, got, want))
        if want <= 1.0:
            fails.append("S8.1 says %r but the computed ratio %s = %.3f does not go that way"
                         % (word, key, want))

    # (2) the typed bound on the two computed conversions
    if "under 5%" not in t:
        fails.append("S8.1's 'under 5%' bound on conversion per pass is no longer in the SI")
    else:
        checked += 1
        worst = max(100.0 * c["conversion_per_pass"] for c in ch)
        if worst >= 5.0:
            fails.append("S8.1 says conversion per pass is 'under 5%%' but the larger is %.2f%%"
                         % worst)
    if not checked:
        fails.append("nothing was checked -- every S8.1 phrase this gate binds has vanished")

    print("  S8.1 phrases bound to results/reactor_engineering.json: %d" % checked)
    for f in fails:
        print("    FAIL  %s" % f)
    if neg:
        print("\nNEGATIVE CONTROL: X_pass forced to 0.80, so the conversion-per-pass claim must be refuted.")
        print("G-RXNENG-SI control: %s"
              % ("GOOD (the direction word was caught)" if fails else "BAD -- test is inert"))
        return 0 if fails else 1
    if fails:
        print("\nG-RXNENG-SI: FAIL")
        return 1
    print("\nG-RXNENG-SI: PASS -- every direction word and typed bound in S8.1 agrees with the "
          "computed ratio it stands beside")
    return 0


if __name__ == "__main__":
    _neg = "--negative-control" in sys.argv
    sys.exit(check_si(_neg) if "--check-si" in sys.argv else main(_neg))
