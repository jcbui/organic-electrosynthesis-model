#!/usr/bin/env python3
"""Generate the catalyst-row substrate diffusivities by Wilke-Chang, from the exemplars' own molecules.

    /opt/anaconda3/envs/echem_analysis/bin/python data/build_catalyst_substrates.py   (needs rdkit)

The catalyst-carried rows are solved as EC' problems, and the substrate's diffusivity sets the
substrate cap n_S F D_S C_S / delta and enters the source term. Until 2026-10-05 every one of them
used one declared value, 1.0e-9 m2/s scaled by viscosity. Each row now carries the molecule its
exemplar actually runs, read from the paper or its supporting information, and the value is
computed here by the same Wilke-Chang / Le Bas code the carriers use (build_reactions50.py), in
the row's own solvent. Written to data/catalyst_substrates.csv, which the catalyst solvers read.
"""
import csv, importlib.util, io, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("br50", os.path.join(HERE, "build_reactions50.py"))
br = importlib.util.module_from_spec(spec); spec.loader.exec_module(br)

## reaction label (must match reactions_50.csv), substrate, SMILES, how it was identified
ROWS = [
 ("Ni-catalyzed aryl amination (ArBr + amine)", "4-bromobenzotrifluoride", "FC(F)(F)c1ccc(Br)cc1",
  "ja9b01886.pdf: the aryl bromide of the paper's optimization and mechanistic study"),
 ("Electrochemical amination of ArX with NH3", "4-bromotoluene", "Cc1ccc(Br)cc1",
  "Liu/Qiu Angew 2025: 'Employing Ni(I) complex B and 4-bromotoluene (1a) as substrates'"),
 ("Mn-catalyzed alkene diazidation", "4-tert-butylstyrene", "C=Cc1ccc(cc1)C(C)(C)C",
  "Fu/Lin Science 2017: the model alkene of the optimization"),
 ("Co-catalyzed allylic C-H amination", "cyclohex-2-en-1-yl (4-methoxyphenyl)carbamate",
  "COc1ccc(NC(=O)OC2CCCC=C2)cc1",
  "Cai/Xu Nat Commun 2021, SI gram-scale procedure: 14.5 g, 58.7 mmol, i.e. C14H17NO3"),
 ("Co-H alkene reduction (e-HAT)", "alprenolol", "C=CCc1ccccc1OCC(O)CNC(C)C",
  "Gnaim/Baran Nature 2022, Fig. 3 product 45 (64%) and its SI entry: the commercially available "
  "terminal alkene, reduced to C15H25NO2"),
 ("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "5-bromo-3-isopropyl-1H-indole", "CC(C)c1c[nH]c2ccc(Br)cc12",
  "op6c00110_si_001.pdf: '5-bromo-3-isopropyl-1H-indole', species 2 of the campaign (HRMS C11H12BrN)"),
 ("Doubly decarboxylative Csp3-Csp3", "N-hydroxyphthalimide ester of 3-(4'-cyanobiphenyl-4-yl)propanoic acid",
  "N#Cc1ccc(cc1)-c1ccc(CCC(=O)ON2C(=O)c3ccccc3C2=O)cc1",
  "Zhang/Baran Nature 2022 SI pp. 8-9: the representative limiting acid A is '3-(4'-cyano-[1,1'-biphenyl]-4-yl)propanoic "
  "acid 4' (25.1 mg, 0.1 mmol), coupled as its in-situ N-hydroxyphthalimide ester"),
 ("Rh-catalyzed electrooxidative C-H alkenylation", "n-butyl acrylate", "C=CC(=O)OCCCC",
  "Qiu/Ackermann Angew 2018, Table 1: the limiting acrylate"),
 ("Cu-catalyzed benzylic cyanation", "n-butylbenzene", "CCCCc1ccccc1",
  "Cai/Xu Nat Catal 2022: the model alkylarene"),
 ("Cathodic Ni aryl-aryl homocoupling", "bromobenzene", "Brc1ccccc1",
  "Courtois/Perichon Tetrahedron 1997: 'PhBr 15 mmol' in the footnote this row is read from"),
 ("Co-H alkene isomerization (catalytic)", "5-methyl-1-phenylhex-5-en-3-ol", "CC(=C)CC(O)CCc1ccccc1",
  "Gnaim/Baran Nature 2022 SI, compound 17 (general procedure B, 0.2 mmol): the product is the "
  "trisubstituted alkene 5-methyl-1-phenylhex-4-en-3-ol (C13H18O), so the substrate is its "
  "1,1-disubstituted isomer; the Le Bas volume is the same for both"),
## the oxazole row moved to data/build_mediated_substrates.py on 2026-10-05 (reclassified: triarylamine mediator)
 ("Cathodic aryl-halide radical 5-exo cyclization", "allyl 2-iodophenyl ether", "C=CCOc1ccccc1I",
  "Ozaki/Ohmori Tet Lett 1994, Table 1: aryl iodide 5a, the 5-exo substrate of this row"),
]

def main():
    rx = {r["reaction"]: r for r in csv.DictReader(io.open(os.path.join(HERE, "reactions_50.csv"), encoding="utf-8"))}
    cat = [n for n, r in rx.items() if r["carrier_type"] == "catalyst"]
    named = [r[0] for r in ROWS]
    if sorted(cat) != sorted(named):
        raise SystemExit("catalyst rows and ROWS disagree:\n  only in reactions_50: %s\n  only here: %s"
                         % (sorted(set(cat) - set(named)), sorted(set(named) - set(cat))))
    out = []
    print("%-48s %-44s %-10s %8s %11s" % ("reaction", "substrate", "solvent", "V_LeBas", "D_S m2/s"))
    for label, name, smi, prov in ROWS:
        solv = rx[label]["solvent"]
        Dcm2, V = br.wilke_chang(smi, solv)
        out.append(dict(reaction=label, substrate=name, smiles=smi, solvent=solv,
                        lebas_V_cm3mol="%.2f" % V, D_sub_m2s="%.4e" % (Dcm2 * 1e-4), identified_by=prov))
        print("%-48s %-44s %-10s %8.1f %11.4e" % (label[:48], name[:44], solv, V, Dcm2 * 1e-4))
    with io.open(os.path.join(HERE, "catalyst_substrates.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print("\nwrote -> data/catalyst_substrates.csv (%d rows)" % len(out))

if __name__ == "__main__":
    main()
