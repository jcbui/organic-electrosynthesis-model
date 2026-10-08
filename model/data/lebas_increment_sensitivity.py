#!/usr/bin/env python3
"""G-LEBASINC -- what Reid's specific O and N increments would do to the Wilke-Chang diffusivities.

    /opt/anaconda3/envs/echem_analysis/bin/python data/lebas_increment_sensitivity.py   (needs RDKit)

WHAT IS DECLARED. lebas_volume() in data/build_reactions50.py applies two simplifications to the Le Bas increments of
Reid, Prausnitz & Poling, The Properties of Gases and Liquids, 4th ed., Table 3-8, p. 53 (read from the page raster):
  * every oxygen that is not a carboxylic-acid hydroxyl takes 7.4, the table's "Oxygen (except as noted below)" entry,
    although the table gives 9.1 / 9.9 / 11.0 for an oxygen in methyl / ethyl / higher esters and ethers and 8.3 for an
    oxygen joined to S, P or N;
  * every nitrogen without a hydrogen takes 15.6, the table's "Doubly bonded" entry; the table gives 10.5 and 12.0 for
    primary and secondary amines and has NO entry for a tertiary (three single bonds) nitrogen.
This script recomputes each Wilke-Chang volume with the specific entries and reports the diffusivity ratio,
D_specific / D_carried = (V_specific / V_carried)^-0.6, for every Wilke-Chang carrier of reactions_50 and every mediated-
spec substrate of data/mediated_substrates.csv. It imports lebas_volume, wilke_chang and the SOLVENTS table from
build_reactions50.py (importing that module writes nothing; its writes sit under its __main__ guard).

THE RULES APPLIED, stated so they can be checked:
  * an oxygen with two carbon neighbours and no hydrogen that is not part of a carboxylic acid is an ester/ether
    oxygen; it takes 9.1 if either carbon neighbour is a methyl group, 9.9 if either is the CH2 of an ethyl group, and
    11.0 otherwise (aryl, cyclic and higher ethers and esters). A carbonyl oxygen stays at 7.4 ("except as noted").
  * an oxygen bonded to S, P or N takes 8.3.
  * a nitrogen with no hydrogen and no double, triple or aromatic bond is tertiary: the table has no entry, so it is
    BRACKETED -- the main variant keeps 15.6, the low variant gives it 12.0 (the secondary-amine entry, the nearest
    tabulated value). Every other nitrogen keeps the carried assignment.

THE FERROCENE BENCHMARK. build_reactions50.py's own validation call passes ferrocene as three disconnected fragments,
for which its cyclomatic ring count (bonds - atoms + 1) is zero, so both cyclopentadienyl ring corrections are dropped.
Here the volume is summed fragment by fragment, so each ring takes its correction; iron has no Le Bas increment and takes
the function's 20.0 fallback. mu(MeCN) is read from the same SOLVENTS table (0.369 mPa s, CRC p. 6-243).

Writes results/lebas_increment_sensitivity.json, which build_param_tables.py reads.
"""
import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "lebas_increment_sensitivity.json")
sys.path.insert(0, HERE)

import numpy as np                                     # noqa: E402
from rdkit import Chem                                 # noqa: E402
import build_reactions50 as BR                         # noqa: E402

REID = {"O_methyl": 9.1, "O_ethyl": 9.9, "O_higher": 11.0, "O_SPN": 8.3, "N_tert_low": 12.0}
REID_LOCATOR = ("Reid, Prausnitz & Poling, The Properties of Gases and Liquids, 4th ed., McGraw-Hill, 1987, "
                "Table 3-8, p. 53, Le Bas column")


def _is_methyl(c):
    return c.GetSymbol() == "C" and c.GetTotalNumHs() == 3


def _is_ethyl_ch2(c, o_idx):
    if c.GetSymbol() != "C" or c.GetTotalNumHs() != 2:
        return False
    others = [n for n in c.GetNeighbors() if n.GetIdx() != o_idx and n.GetSymbol() != "H"]
    return len(others) == 1 and _is_methyl(others[0])


def reid_delta(smiles, tert_n_value=None):
    """Volume change (cm3/mol) from replacing the carried O/N increments by Reid's specific ones, and the atoms moved."""
    m = Chem.MolFromSmiles(smiles)
    acid = Chem.MolFromSmarts("C(=O)[OX2H1]")
    acid_o = {a for match in m.GetSubstructMatches(acid) for a in match if m.GetAtomWithIdx(a).GetSymbol() == "O"}
    dv, moved = 0.0, []
    for a in m.GetAtoms():
        s = a.GetSymbol()
        if s == "O" and a.GetIdx() not in acid_o:
            heavy = [n for n in a.GetNeighbors()]
            if any(n.GetSymbol() in ("S", "P", "N") for n in heavy):
                dv += REID["O_SPN"] - BR.LEBAS["O"]; moved.append("O-S/P/N 8.3")
            elif len(heavy) == 2 and all(n.GetSymbol() == "C" for n in heavy) and a.GetTotalNumHs() == 0:
                if any(_is_methyl(n) for n in heavy):
                    v, lab = REID["O_methyl"], "O methyl ester/ether 9.1"
                elif any(_is_ethyl_ch2(n, a.GetIdx()) for n in heavy):
                    v, lab = REID["O_ethyl"], "O ethyl ester/ether 9.9"
                else:
                    v, lab = REID["O_higher"], "O higher ester/ether 11.0"
                dv += v - BR.LEBAS["O"]; moved.append(lab)
        elif s == "N" and a.GetTotalNumHs() == 0 and tert_n_value is not None:
            multiple = a.GetIsAromatic() or any(b.GetBondType() != Chem.BondType.SINGLE for b in a.GetBonds())
            if not multiple:
                dv += tert_n_value - BR.LEBAS["N"]; moved.append("tertiary N %.1f" % tert_n_value)
    return dv, moved


def per_row(label, smiles, solvent):
    v0 = BR.lebas_volume(smiles)
    dv, moved = reid_delta(smiles)
    dv_low, moved_low = reid_delta(smiles, REID["N_tert_low"])
    r = (v0 + dv) / v0
    r_low = (v0 + dv_low) / v0
    return dict(row=label, smiles=smiles, solvent=solvent, V_carried=round(v0, 2),
                V_reid=round(v0 + dv, 2), V_reid_tertN12=round(v0 + dv_low, 2),
                D_ratio=round(r ** -0.6, 5), D_ratio_tertN12=round(r_low ** -0.6, 5),
                atoms_moved=moved, atoms_moved_tertN12=moved_low)


def ferrocene():
    frags = ["[cH-]1cccc1", "[cH-]1cccc1", "[Fe+2]"]
    v = sum(BR.lebas_volume(f) for f in frags)
    msol, mu, _rho, phi, _src = BR.SOLVENTS["MeCN"]
    d = 7.4e-8 * np.sqrt(phi * msol) * BR.T / (mu * v ** 0.6)
    d_disc, v_disc = BR.wilke_chang("[cH-]1cccc1.[cH-]1cccc1.[Fe+2]", "MeCN")
    return v, float(d), mu, float(d_disc), float(v_disc)


def main():
    rows = []
    for rec in BR.R:
        cls, name, ex, carrier, cspec, meth, arg, *rest = rec
        solv = rest[4]
        if meth != "WC" or BR.ion_override(arg, solv) is not None:
            continue
        rows.append(per_row(name, arg, solv))
    subs = []
    with io.open(os.path.join(HERE, "mediated_substrates.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["method"].startswith("Wilke"):
                subs.append(per_row(r["reaction"], r["smiles"], r["solvent"]))
    moved = [r for r in rows if r["atoms_moved"]]
    moved_low = [r for r in rows if r["atoms_moved_tertN12"]]
    sub_moved = [r for r in subs if r["atoms_moved"] or r["atoms_moved_tertN12"]]

    def ext(rs, key):
        v = [r[key] for r in rs]
        return (min(v), max(v)) if v else (1.0, 1.0)
    # Can a published count move? i_lim is at most LINEAR in D (fixed films; the correlations give D^(2/3) and
    # D^0.644, the EC' solve less), so a cell can cross a threshold only if it sits within its row's D change of it.
    with io.open(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"), encoding="utf-8") as fh:
        mat = {r["reaction"]: r for r in csv.DictReader(fh)}
    arch = [k for k in next(iter(mat.values())) if k not in ("class", "reaction", "carrier")]
    reach, closest, missing = [], None, []
    neg = "--negative-control" in sys.argv       # magnify every D change 1000-fold: some cell must then cross
    for r in rows + subs:
        for key in ("D_ratio", "D_ratio_tertN12"):
            f = r[key]
            if f == 1.0:
                continue
            if r["row"] not in mat:
                missing.append(r["row"])
                continue
            if neg:
                f = 1 + (f - 1) * 1e3
            for a in arch:
                v = float(mat[r["row"]][a])
                for t in (25.0, 50.0):
                    gap = abs(v / t - 1)
                    if closest is None or gap < closest[0]:
                        closest = (gap, r["row"], a, t, v)
                    if (v - t) * (v * f - t) < 0:
                        reach.append(dict(row=r["row"], arch=a, threshold=t, value=v, scaled=v * f, variant=key))
    v_fc, d_fc, mu_fc, d_disc, v_disc = ferrocene()
    res = dict(
        locator=REID_LOCATOR, increments_specific=REID, carried=dict(O=BR.LEBAS["O"], N=BR.LEBAS["N"]),
        n_wc_carriers=len(rows), n_carriers_moved=len(moved),
        carriers_moved=[r["row"] for r in moved],
        carrier_D_ratio_range=list(ext(moved, "D_ratio")),
        n_carriers_moved_tertN12=len(moved_low),
        carrier_D_ratio_range_tertN12=list(ext(moved_low, "D_ratio_tertN12")),
        max_abs_change_pct=round(100 * max(abs(r[k] - 1) for r in rows + subs for k in ("D_ratio", "D_ratio_tertN12")), 3),
        n_mediated_substrates=len(subs), n_substrates_moved=len(sub_moved),
        substrate_D_ratio_range=list(ext(subs, "D_ratio")),
        substrate_D_ratio_range_tertN12=list(ext(subs, "D_ratio_tertN12")),
        cells_that_could_cross=reach,
        closest_cell=dict(row=closest[1], arch=closest[2], threshold=closest[3], value=closest[4],
                          margin_pct=round(100 * closest[0], 2)) if closest else None,
        carriers=rows, mediated_substrates=subs,
        ferrocene_V_cm3mol=round(v_fc, 2), ferrocene_D_cm2s=d_fc, ferrocene_mu_MeCN_mPas=mu_fc,
        ferrocene_Fe_increment="none tabulated; the 20.0 fallback of lebas_volume()",
        ferrocene_disconnected_V_cm3mol=round(v_disc, 2), ferrocene_disconnected_D_cm2s=d_disc,
        ferrocene_measured_cm2s=2.4e-5,
        ferrocene_measured_basis=("upper end of the textbook range 1.7-2.4e-5 cm2 s-1; no page carrying 2.4e-5 has been "
                                  "located, so it is not a page-anchored value"),
        ferrocene_miss_pct=round(100 * (d_fc / 2.4e-5 - 1), 1),
        ferrocene_secondary_cm2s=1.70e-5,
        ferrocene_secondary_basis=("Bard & Faulkner, Electrochemical Methods, 2nd ed., Wiley, 2001, Problem 6.12(a), p. 260: "
                                   "D_R = 1.70 x 10^-5 cm2/s for ferrocene in acetonitrile (0.5 M TBABF4), quoting Mirkin, "
                                   "Richards & Bard, J. Phys. Chem. 1993, 97, 7672 (secondary; the primary was not retrieved)"),
        ferrocene_miss_secondary_pct=round(100 * (d_fc / 1.70e-5 - 1), 1),
    )
    if neg:                                      # a control never writes the artifact it perturbs (trap 23)
        print("G-LEBASINC control: %s (%d crossing(s) at 1000x the D changes)" % ("GOOD" if reach else "BAD -- test is inert", len(reach)))
        sys.exit(0 if reach else 1)
    if missing:
        print("G-LEBASINC: FAIL -- %d moved row(s) absent from the published matrix: %s" % (len(set(missing)), sorted(set(missing))))
        sys.exit(1)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("Wilke-Chang carriers: %d, moved by Reid's specific O increments: %d (D x %.4f-%.4f); with tertiary N at 12.0: "
          "%d (D x %.4f-%.4f); mediated substrates moved: %d of %d; max |change| %.2f pct"
          % (len(rows), len(moved), *res["carrier_D_ratio_range"], len(moved_low), *res["carrier_D_ratio_range_tertN12"],
             len(sub_moved), len(subs), res["max_abs_change_pct"]))
    print("ferrocene/MeCN: V = %.1f cm3/mol, D = %.3e cm2/s (%+.1f pct vs 2.4e-5; %+.1f pct vs 1.70e-5); "
          "disconnected call gives V = %.1f, D = %.3e"
          % (v_fc, d_fc, res["ferrocene_miss_pct"], res["ferrocene_miss_secondary_pct"], v_disc, d_disc))
    print("cells a linear-in-D bound lets cross 25 or 50 mA cm-2: %d; closest moved-row cell %s" % (len(reach), res["closest_cell"]))
    # The registry and SI state that no cell can cross a threshold under Reid's specific increments; assert it.
    if reach:
        print("G-LEBASINC: FAIL -- %d cell(s) could cross a threshold under Reid's increments" % len(reach))
        sys.exit(1)
    print("G-LEBASINC: PASS -- no cell can cross 25 or 50 mA cm-2 under Reid's specific increments "
          "(closest %.2f pct); wrote %s" % (res["closest_cell"]["margin_pct"] if res["closest_cell"] else float("nan"),
                                            os.path.relpath(OUT, ROOT)))


if __name__ == "__main__":
    main()
