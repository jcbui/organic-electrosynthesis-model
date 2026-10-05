#!/usr/bin/env python3
"""G-SPECIATE -- for the two rows whose carrier is an acid/base pair, which form is present?

    cd Section4_Model && python data/acid_base_speciation.py
    cd Section4_Model && python data/acid_base_speciation.py --negative-control

WHY
---
Two of the fifty carriers exist as an acid/conjugate-base pair, and the model has to commit to
one. Get it wrong and BOTH the charge (which sets migration) and the concentration (which sets
i_lim linearly) are wrong together.

    row 34  Cl4NHPI / Cl4NHPI-      carried z = -1
    row 39  N-Piv-a-amino acid / carboxylate    carried z = -1 at the ACID's concentration

THE POINT: pKa IS NOT THE BINDING CONSTRAINT -- BASE STOICHIOMETRY IS
---------------------------------------------------------------------
Neither answer needs a pKa in a non-aqueous solvent, which is just as well: pKa values for
carboxylic acids in methanol and for Cl4NHPI in acetone are not values this project can source,
and inventing them would be worse than the gap. What decides both rows is how much base the
procedure actually charges, and it points OPPOSITE WAYS:

  row 34, Horn/Baran Nature 2016: "20 mol% Cl4NHPI, pyridine (2.0 equiv.), tBuOOH (1.5 equiv.),
  and LiClO4 as the supporting electrolyte (0.1 M) in acetone (6 ml per mmol of substrate)".
  Pyridine at 2.0 equiv against a mediator at 0.2 equiv is a TENFOLD EXCESS, so the mediator is
  essentially fully deprotonated whatever the exact pKa. The paper corroborates it directly: its
  cyclic voltammetry reports the reversible couple "in the presence of excess pyridine".
  -> z = -1 at the full mediator concentration is self-consistent. Carried correctly.

  row 39, Walecka-Kurczyk RSC Adv. 2022: "N-protected a-amino acid 1 (0.4 mmol, 1 equiv.),
  MeOH (4 mL), and Et3N (4.2 uL, 0.03 mmol, 0.075 equiv.)". The base is SUB-STOICHIOMETRIC, so
  the carboxylate is capped by the Et3N loading no matter how favourable the proton transfer.
  Sweeping the equilibrium constant over six orders of magnitude leaves [RCOO-] between about
  0.002 and 0.0075 M -- 13 to 50 times BELOW the 0.1 M this row carries.
  -> z = -1 at 0.1 M is NOT self-consistent: it takes the charge of a 7.5% minority species and
     the concentration of the 92.5% majority one.

WHAT TO DO ABOUT ROW 39 IS AN AUTHOR DECISION, and the two self-consistent pairings are:
  (a) z ~ 0 at 0.1 M -- transport the neutral acid. Proton transfer between a carboxylic acid and
      a tertiary amine is essentially diffusion-limited, so the pre-equilibrium re-equilibrates far
      faster than diffusion across a 100-300 um film: a fast CE case, in which the limiting current
      is set by the TOTAL acid and the transported species is 92.5% neutral (population-weighted
      z = -0.075).
  (b) z = -1 at ~0.0075 M -- transport the carboxylate itself, which drops that ceiling 13x.
This script does not choose; it shows that the carried pairing is neither.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KS = [0.01, 0.1, 1.0, 10.0, 100.0, 1e4]


# A NEGATIVE CONTROL MUST NEVER WRITE THE ARTIFACT IT PERTURBS. Until 2026-08-30 several
# controls here dumped their perturbed numbers straight over results/, so a control run
# left the repo holding fabricated values until the next ordinary run happened to fix it --
# and an audit that snapshotted results/ AFTER a control run then compared against
# contaminated bytes and reported no contamination. Controls write a _NEGCONTROL sibling,
# the convention data/check_conditions.py already used.
def _out(path, neg):
    return path[:-5] + "_NEGCONTROL.json" if neg and path.endswith(".json") else path

def carboxylate(Ca, Cb, K):
    """[RCOO-] for RCOOH + B <=> RCOO- + BH+ at equilibrium constant K."""
    A, B, C = 1.0 - K, K * (Ca + Cb), -K * Ca * Cb
    if abs(A) < 1e-12:
        return -C / B
    for sign in (+1, -1):
        x = (-B + sign * (B * B - 4 * A * C) ** 0.5) / (2 * A)
        if 0 < x < min(Ca, Cb) * (1 + 1e-9):
            return x
    return float("nan")


def main(neg=False):
    Ca, Cb = 0.1, 0.0075                      # row 39, from the paper's own procedure
    if neg:
        Cb = 10.0                             # flood with base: the cap must disappear
    print("  ROW 39  N-Piv-a-amino acid / carboxylate")
    print("    charged: acid %.4f M, Et3N %.4f M (%.3f equiv) -- base is %s"
          % (Ca, Cb, Cb / Ca, "LIMITING" if Cb < Ca else "in excess"))
    print("    %-10s %-14s %s" % ("K", "[RCOO-] (M)", "of the base converted"))
    vals = []
    for K in KS:
        x = carboxylate(Ca, Cb, K)
        vals.append(x)
        print("    %-10g %-14.5f %.1f%%" % (K, x, 100 * x / Cb))
    lo, hi = min(vals), max(vals)
    print("    over six orders of magnitude in K: [RCOO-] = %.4f-%.4f M, i.e. %.0f-%.0fx below "
          "the %.2f M carried" % (lo, hi, Ca / hi, Ca / lo, Ca))

    print("\n  ROW 34  Cl4NHPI / Cl4NHPI-")
    print("    charged: mediator 0.20 equiv, pyridine 2.0 equiv -- base in TENFOLD EXCESS,")
    print("    so the mediator is essentially fully deprotonated for any plausible pKa, and the")
    print("    paper's own CV reports the couple 'in the presence of excess pyridine'.")
    print("    -> z = -1 at the full mediator concentration is self-consistent.")

    json.dump({"row39": {"acid_M": Ca, "base_M": Cb, "K": KS, "carboxylate_M": vals,
                         "range_M": [lo, hi], "carried_M": Ca,
                         "factor_below_carried": [Ca / hi, Ca / lo]},
               "row34": {"base_equiv": 2.0, "mediator_equiv": 0.2, "excess": 10.0}},
              io.open(_out(os.path.join(ROOT, "results", "acid_base_speciation.json"), neg),
                      "w", encoding="utf8"), indent=1)

    capped = hi <= Cb * 1.001
    if neg:
        print("\nNEGATIVE CONTROL: base flooded to %.1f M, so the cap must lift." % Cb)
        print("G-SPECIATE control: %s ([RCOO-] reaches %.4f M, vs %.4f M when base-limited)"
              % ("GOOD" if hi > 0.05 else "BAD -- test is inert", hi, 0.0075))
        return 0 if hi > 0.05 else 1
    if not capped:
        print("\nG-SPECIATE: REVIEW NEEDED -- the carboxylate is not capped by the base loading, "
              "so the bound this row relies on does not hold")
        return 1
    print("\nG-SPECIATE: PASS -- row 34's base is in excess (z = -1 self-consistent); row 39's is "
          "sub-stoichiometric, so its carboxylate is capped at %.4f M and the carried pairing of "
          "z = -1 with %.2f M is not self-consistent (author decision, see the module docstring)"
          % (hi, Ca))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
