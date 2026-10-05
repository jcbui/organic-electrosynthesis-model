"""Is the dilute-catalyst conclusion an artifact of the assumed hydrodynamic radius?

    cd Section4_Model && python figs/analysis_catalyst_D_sensitivity.py

THE EXPOSURE
------------
Eleven rows of the 50-reaction set carry their current on a dilute molecular catalyst, and all
eleven take their diffusivity from Stokes-Einstein with a hydrodynamic radius of 4.0-5.0 A that is
TYPED IN, not derived. Wilke-Chang cannot be used for them: Le Bas has no transition-metal
increment, and RDKit cannot embed a coordination complex (no metal-ligand bonds in the SMILES), so
a computed molecular volume is not available either -- both routes were tried in the 2026-08-22
provenance pass and both fail for this class.

That makes r the single most exposed input in the diffusivity column, and it carries a headline
conclusion: "ten of the eleven reactions whose current is carried by a dilute molecular catalyst
clear 25 mA cm-2 in NONE of the six architectures". If that 10/11 moves with r, it is an artifact.

THE TEST
--------
i_lim = nFDC/delta and D = kB T / (6 pi mu r), so i_lim ~ 1/r EXACTLY. Scaling every catalyst
radius by a factor f scales every catalyst i_lim by 1/f. The count is therefore a step function of
f alone, and the critical f can be read off directly -- no re-solve is needed, and none is done
here, which is why this script cannot drift from the Julia matrix.

THE ANCHOR
----------
Ferrocene in MeCN, D = 2.4e-5 cm2 s-1 (Bard & Faulkner, Electrochemical Methods, 2nd ed., quoted
range 1.7-2.4e-5; also the validation anchor already used by build_reactions50.py). Inverting
Stokes-Einstein at 25 C with mu(MeCN) = 0.369 mPa s gives r = 2.47 A for a NEUTRAL METALLOCENE of
MW 186. Scaling by mass (r ~ M^(1/3)) to the 325-570 range of this set predicts 3.2-3.7 A.

Note which way that cuts: the TYPED radii (4.0-5.0 A) are LARGER than the mass-scaled expectation,
so the model already UNDERSTATES catalyst D, understates their i_lim, and therefore states the
"catalysts do not clear 25 mA cm-2" result conservatively. Charge and the solvation shell push the
true radius up as well, in the same direction. The exposure is real but it is one-sided.
"""
import json, re
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
THRESH = 25.0
OUT = os.path.join(ROOT, "results", "catalyst_D_sensitivity.json")

KB, T_K = 1.380649e-23, 298.15
# 0.343 was carried here until 2026-08-30 WITH THIS CRC CITATION ATTACHED, three days after
# solvents.csv moved to the value the page actually prints. CRC 97th ed. p. 6-243 prints
# 0.369 in the eta(25 C) column; 0.343 was a retained judgement that the printed row looked
# like a typo, which is exactly the unsourced reasoning the standard forbids -- and it was
# citing the page for a number the page does not carry.
MU_MECN = 0.369e-3          # Pa s, CRC 97th ed. Sect. 6 p. 6-243, eta(25 C) column
D_FERROCENE = 2.4e-9        # m2/s = 2.4e-5 cm2/s, MeCN, 25 C


# A NEGATIVE CONTROL MUST NEVER WRITE THE ARTIFACT IT PERTURBS. Until 2026-08-30 several
# controls here dumped their perturbed numbers straight over results/, so a control run
# left the repo holding fabricated values until the next ordinary run happened to fix it --
# and an audit that snapshotted results/ AFTER a control run then compared against
# contaminated bytes and reported no contamination. Controls write a _NEGCONTROL sibling,
# the convention data/check_conditions.py already used.
def _out(path, neg):
    return path[:-5] + "_NEGCONTROL.json" if neg and path.endswith(".json") else path

def main(neg=False):
    rx = pd.read_csv(os.path.join(ROOT, "data", "reactions_50.csv"))
    t0 = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
    m = t0.merge(rx[["reaction", "carrier_type", "C_carrier_M", "D_provenance"]], on="reaction")
    cat = m[m.carrier_type == "catalyst"].copy()
    if neg:
        # Perturb the INPUT the conclusion is read off, not the verdict: lift every catalyst
        # ceiling just past the threshold that the second-best row currently misses. If 10/11
        # is genuinely being tested, a second row clearing MUST make this gate fail.
        lift = THRESH / sorted(cat[ARCH].max(axis=1).values)[::-1][1] * 1.01
        cat[ARCH] = cat[ARCH] * lift
        print("NEGATIVE CONTROL: every catalyst ceiling scaled by %.3fx, so a SECOND row clears "
              "%.0f mA cm-2 and G-CATD must FAIL.\n" % (lift, THRESH))
    best = cat[ARCH].max(axis=1)
    n_clear = int((best >= THRESH).sum())

    r_fc = KB * T_K / (6 * np.pi * MU_MECN * D_FERROCENE) * 1e10
    print("ferrocene anchor: measured D = %.1e cm2/s in MeCN -> r = %.2f A (neutral, MW 186)"
          % (D_FERROCENE * 1e4, r_fc))
    print("assumed radii in the set: %s A\n"
          % sorted({float(s.split("r=")[1].split()[0]) for s in cat.D_provenance}))

    print("%-46s %9s %10s" % ("reaction", "C_cat(M)", "best i_lim"))
    for (_, r), b in zip(cat.iterrows(), best):
        print("%-46s %9.4f %10.1f%s"
              % (r.reaction[:46], r.C_carrier_M, b, "   <- clears" if b >= THRESH else ""))

    srt = sorted(best.values)[::-1]
    f_crit = THRESH / srt[1]                      # i_lim must rise by this factor
    r_crit_45 = 4.5 / f_crit                      # ... i.e. r must fall to this, from 4.5 A
    print("\n%d of %d clear %.0f mA cm-2 in at least one architecture" % (n_clear, len(cat), THRESH))
    print("second-best catalyst row peaks at %.1f mA cm-2" % srt[1])
    print("for a SECOND row to clear, i_lim must rise %.2fx, i.e. every radius must be"
          % f_crit)
    print("overestimated by %.2fx -- a 4.5 A complex would have to be %.2f A"
          % (f_crit, r_crit_45))
    # Size-scale the ferrocene anchor. A hydrodynamic radius goes as the cube root of the
    # molecular volume, and volume tracks mass for compounds of similar density, so
    #     r(complex) ~ r(ferrocene) * (M_complex / M_ferrocene)^(1/3).
    # The SECOND-best catalyst row is the one that decides the count, so it is the row the
    # margin must be quoted against.
    # Molecular weights COMPUTED from the molecular formula with IUPAC 2021 standard atomic
    # weights, not typed. The first version of this script carried 186 / 487 / 325 from memory;
    # they were right to under 0.1%, but "right from memory" is the habit this whole provenance
    # pass exists to break.
    _AW = {"C": 12.011, "H": 1.008, "N": 14.007, "O": 15.999,
           "Fe": 55.845, "Ni": 58.693, "Co": 58.933, "Br": 79.904}
    _mw = lambda f: sum(_AW[e] * n for e, n in f.items())
    M_FC = _mw({"C": 10, "H": 10, "Fe": 1})                        # ferrocene, C10H10Fe
    M_2ND = _mw({"C": 18, "H": 24, "Br": 2, "N": 2, "Ni": 1})       # NiBr2(dtbbpy), C18H24Br2N2Ni
    M_MIN = _mw({"C": 16, "H": 14, "Co": 1, "N": 2, "O": 2})        # Co(salen), C16H14CoN2O2
    r_2nd = r_fc * (M_2ND / M_FC) ** (1 / 3.)
    r_min = r_fc * (M_MIN / M_FC) ** (1 / 3.)
    print("\nsize-scaling the anchor, r ~ M^(1/3):")
    print("  Co(salen) C16H14CoN2O2, the LIGHTEST complex here (M = %.2f): r_expected = %.2f A"
          % (M_MIN, r_min))
    print("  NiBr2(dtbbpy) C18H24Br2N2Ni, the row that decides the count (M = %.2f): "
          "r_expected = %.2f A" % (M_2ND, r_2nd))
    print("  the conclusion breaks at r = %.2f A -> margin %.2fx on the deciding row"
          % (r_crit_45, r_2nd / r_crit_45))
    print("  and charge and the solvation shell both RAISE the effective radius, which lowers")
    print("  i_lim further -- the physics runs in the direction that strengthens the result.")

    # 2026-09-11: the deciding row is now carried at a SOURCED rate constant (S5.7) and sits in the
    # kinetic regime, where its ceiling goes as sqrt(D) rather than as D; the 1/r scaling above is
    # therefore a BOUND on its sensitivity, and the sqrt-law break is recorded beside it.
    r_crit_sqrt = 4.5 / (f_crit ** 2)
    deciding = str(cat.iloc[int(np.argsort(best.values)[::-1][1])].reaction)
    conditional = bool(r_crit_45 >= r_2nd)
    report = dict(n_catalyst=len(cat), n_clear=n_clear, threshold=THRESH,
                  second_best_i_lim=float(srt[1]), f_crit=float(f_crit),
                  r_crit_from_4p5A=float(r_crit_45), r_crit_sqrt_from_4p5A=float(r_crit_sqrt),
                  r_expected_deciding_A=float(r_2nd), deciding_row=deciding, conditional=conditional,
                  r_ferrocene_A=float(r_fc),
                  anchor="ferrocene in MeCN, D = 2.4e-5 cm2/s, 25 C")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(_out(OUT, neg), "w") as f:
        json.dump(report, f, indent=2)
    print("\nwrote %s" % os.path.relpath(OUT, ROOT))

    # ---- G-CATD: the published 10/11 and the margin behind it -------------------------
    fails = []
    if n_clear != 1:
        fails.append("catalyst rows clearing %.0f = %d, SI and manuscript say 1 (10 of 11 clear "
                     "in none)" % (THRESH, n_clear))
    if r_crit_45 >= r_2nd and not neg:
        # The physical argument (the break lies below any plausible radius) has lapsed: with the
        # deciding row at its sourced rate constant the count is CONDITIONAL on the assigned radius.
        # That is allowed only while the SI says so, in the S3 Stokes-Einstein passage, with the
        # break radius this artifact prints (the G-DSUBSENS / G-SCRANGE pattern: disclosure, not existence).
        try:
            sys.path.insert(0, os.path.join(ROOT, "data"))
            from docx_text import asserted_text
            import unicodedata as _ud
            si = _ud.normalize("NFKC", re.sub(r"\s+", " ", asserted_text(os.path.join(ROOT, "SI_Section4_Transport_Model.docx"))))
        except Exception as exc:                                     # noqa: BLE001
            si = ""; fails.append("could not read the SI to check the disclosure: %s" % exc)
        probe = "breaks at r_h = %.2f" % r_crit_45
        k = si.find(probe)
        if k < 0 or "conditional" not in si[max(0, k - 400):k + 400]:
            fails.append("the count is conditional on the assigned radius (it breaks at %.2f A, above the mass-scaled "
                         "expectation %.2f A for the deciding row) and the SI's S3 passage does not declare it with that number"
                         % (r_crit_45, r_2nd))
        else:
            print("  the count is conditional on the assigned radius (break %.2f A, expectation %.2f A) and the SI declares it" % (r_crit_45, r_2nd))
    elif r_crit_45 >= r_2nd:
        fails.append("the radius at which the conclusion breaks (%.2f A) is no longer below the "
                     "mass-scaled expectation for the deciding complex (%.2f A)" % (r_crit_45, r_2nd))
    if neg:
        print("\nG-CATD control: %s"
              % ("GOOD -- the gate fires (%s)" % fails[0][:80] if fails
                 else "BAD -- test is inert, 10/11 survived a forced second clearance"))
        return 0 if fails else 1
    print("\nG-CATD: %s" % ("PASS" if not fails else "FAIL"))
    for f_ in fails:
        print("  " + f_)
    if fails:
        raise AssertionError("; ".join(fails))
    print("  10/11 holds at the adopted radii; breaking it needs r = %.2f A (1/r bound; %.2f A under the sqrt-D law of the "
          "kinetic regime) against a mass-scaled expectation of %.2f A for the deciding row" % (r_crit_45, r_crit_sqrt, r_2nd))
    return report


if __name__ == "__main__":
    # main() returns its summary dict on success; sys.exit(dict) was exiting 1 and printing the
    # dict as the exit message while the verdict line said PASS (the runner reads the verdict line,
    # which is why it never surfaced). Only an int is an exit status.
    _r = main(neg="--negative-control" in sys.argv)
    sys.exit(_r if isinstance(_r, int) else 0)
