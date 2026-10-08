#!/usr/bin/env python3
"""The balanced reaction behind every row of the 50-reaction set -> data/reaction_stoichiometry.csv.

    /opt/anaconda3/envs/echem_analysis/bin/python data/build_reaction_stoichiometry.py   (needs rdkit)

For each row this records, from the exemplar: which species exchanges electrons with the working
electrode, the electrode step, the solution step that follows (for mediated and catalysed rows),
and the balanced overall transformation with its electrons. Nothing is typed twice: the printed
equation is ASSEMBLED from the same terms whose atoms and charges are summed, so an equation that
prints is an equation that balances. Three things are asserted for every row before anything is
written:

  1. atoms balance, element by element (compositions come from RDKit for named molecules and from
     explicit generic formulas where the exemplar's partner is a class, e.g. R-CO2-);
  2. charge balances, electrons included;
  3. the electrons per limiting substrate equal `n_substrate` in reactions_50.csv, the electrode
     equals data/electrode_direction.csv, and the electrons per carrier equal `n_carrier`.

Rows whose overall transformation is redox-neutral (a paired cycle, or a chain carried by a
catalytic amount of charge) balance with no electron term; their electrode count is then a
property of the cycle and the `kind` column says which.
"""
import csv, io, os, sys
from collections import Counter
from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

def comp(x):
    """Composition Counter with key 'q' for charge. x is a SMILES string or an explicit dict."""
    if isinstance(x, dict):
        return Counter(x)
    m = Chem.AddHs(Chem.MolFromSmiles(x))
    c = Counter(a.GetSymbol() for a in m.GetAtoms())
    c["q"] = sum(a.GetFormalCharge() for a in m.GetAtoms())
    return c

E   = ("e⁻", {"q": -1})
Hp  = ("H⁺", {"H": 1, "q": 1})
H2O = ("H₂O", "O")
MeOH = ("MeOH", "CO")
CO2 = ("CO₂", "O=C=O")
Brm = ("Br⁻", "[Br-]")
OHm = ("OH⁻", "[OH-]")

def side(terms):
    tot = Counter()
    for n, (_, c) in terms:
        for k, v in comp(c).items():
            tot[k] += n * v
    return +tot if False else tot

def fmt(terms):
    out = []
    for n, (lab, _) in terms:
        out.append(lab if n == 1 else "%g %s" % (n, lab))
    return " + ".join(out)

# kind: stoichiometric | paired | charge-consuming | chain | ex-cell
ROWS = []
def R(row, active, estep, sstep, lhs, rhs, kind="stoichiometric", n_limiting=1, note=""):
    ROWS.append(dict(row=row, active=active, estep=estep, sstep=sstep, lhs=lhs, rhs=rhs, kind=kind,
                     n_limiting=n_limiting, note=note))

A = lambda lab, smi: (lab, smi)
G = lambda lab, **d: (lab, dict(d))

R(1, "catalyst (nickel)", "Ni(II)(Ar)(NR₂) → Ni(III)(Ar)(NR₂)⁺ + e⁻",
  "Ni(I)Br + ArBr → Ni(III)(Ar)Br₂, reduced at the cathode to Ni(II)(Ar)Br + Br⁻; amine binds; Ni(III) eliminates Ar–NR₂ and returns Ni(I)",
  [(1, A("4-CF₃C₆H₄Br", "FC(F)(F)c1ccc(Br)cc1")), (1, A("morpholine", "C1COCCN1"))],
  [(1, A("4-CF₃C₆H₄–N(morpholino)", "FC(F)(F)c1ccc(cc1)N1CCOCC1")), (1, Hp), (1, Brm)],
  kind="paired", note="one anodic and one cathodic electron per turnover (Kawamata p. 6396, steps B–F); written at the exemplar's working electrode, the RVC anode; the overall pair is the one the exemplar takes for its DFT calculations, 'the coupling of morpholine with 4-trifluoromethylbromobenzene' (p. 6396)")
R(2, "catalyst (nickel)", "ArNi(III)Br₂ + e⁻ → ArNi(II)Br + Br⁻ (once per turnover; the first Ni(II) → Ni(I) reduction only activates the catalyst)",
  "NH₃ binds to ArNi(II); oxidation at the anode to Ni(III) releases ArNH₂ and returns Ni(I) (undivided cell, zinc anode)",
  [(1, A("4-MeC₆H₄Br", "Cc1ccc(Br)cc1")), (1, A("NH₃", "N"))],
  [(1, A("4-MeC₆H₄NH₂", "Cc1ccc(N)cc1")), (1, Hp), (1, Brm)],
  kind="paired", note="one cathodic and one anodic electron per turnover: Ni(I) adds ArBr, the cathode reduces Ni(III) to Ni(II), the anode oxidizes the amido Ni(II) to Ni(III), and reductive elimination returns Ni(I) (Liu/Qiu Fig. 4f); written at the exemplar's working electrode, the Ni-foam cathode, against a sacrificial zinc anode")
R(3, "substrate", "carbamate → N-acyliminium + 2 e⁻ + H⁺", "",
  [(1, A("methyl pyrrolidine-1-carboxylate", "COC(=O)N1CCCC1")), (1, MeOH)],
  [(1, A("2-methoxy carbamate", "COC(=O)N1CCCC1OC")), (2, Hp), (2, E)])
R(4, "substrate", "amidine → amidinyl radical + H⁺ + e⁻; after ring closure onto the N-aryl ring, cyclohexadienyl radical → benzimidazole + H⁺ + e⁻", "",
  [(1, A("2-fluoro-N-methyl-N-phenylbenzamidine", "CN(c1ccccc1)C(=N)c1ccccc1F"))],
  [(1, A("2-(2-fluorophenyl)-1-methylbenzimidazole", "Cn1c(-c2ccccc2F)nc2ccccc21")), (2, Hp), (2, E)])
R(5, "catalyst (manganese)", "Mn(II)–N₃ → Mn(III)–N₃ + e⁻",
  "Mn(III)–N₃ transfers an azidyl group to the alkene, twice",
  [(1, A("4-tBu-styrene", "C=Cc1ccc(cc1)C(C)(C)C")), (2, A("N₃⁻", "[N-]=[N+]=[N-]"))],
  [(1, A("1,2-diazide", "[N-]=[N+]=NCC(N=[N+]=[N-])c1ccc(cc1)C(C)(C)C")), (2, E)])
R(6, "mediator (bromide)", "2 Br⁻ → Br₂ + 2 e⁻",
  "Br₂ + RC(O)NH₂ → N-bromoamide → isocyanate, trapped by MeOH; 2 Br⁻ returned",
  [(1, A("PhCH₂C(O)NH₂", "NC(=O)Cc1ccccc1")), (1, MeOH)],
  [(1, A("PhCH₂NHCO₂Me", "COC(=O)NCc1ccccc1")), (2, Hp), (2, E)])
R(7, "substrate", "anisole → anisole•⁺ + e⁻; after pyridine adds, the adduct radical cation → N-(4-methoxyphenyl)pyridinium⁺ + H⁺ + e⁻", "",
  [(1, A("anisole", "COc1ccccc1")), (1, A("pyridine", "c1ccncc1"))],
  [(1, A("N-(4-methoxyphenyl)pyridinium⁺", "COc1ccc(cc1)[n+]1ccccc1")), (1, Hp), (2, E)])
R(8, "mediator (bromide)", "2 Br⁻ → Br₂ + 2 e⁻",
  "Br₂ brominates the amide N–H; N–Br homolysis gives the amidyl radical, which cyclizes; 2 Br⁻ returned",
  [(1, A("ArC(O)NH–OPiv", "CC(C)(C)C(=O)ONC(=O)c1ccccc1-c1ccccc1"))],
  [(1, A("N-OPiv phenanthridinone", "CC(C)(C)C(=O)ON1C(=O)c2ccccc2-c2ccccc12")), (2, Hp), (2, E)])
R(9, "catalyst (cobalt)", "Co(II)(salen) → Co(III)(salen)⁺ + e⁻, and later [Co(I)(salen)]⁻ → Co(II)(salen) + e⁻",
  "Co(III) binds the deprotonated carbamate and releases the amidyl radical by heat-induced homolysis (Co(II) returned); the radical cyclizes; Co(II) takes the alkyl radical to the alkene and a Co–H, which MeO⁻ from the cathode deprotonates to [Co(I)]⁻",
  [(1, A("cyclohex-2-enyl N-aryl carbamate", "COc1ccc(NC(=O)OC2CCCC=C2)cc1"))],
  [(1, A("bicyclic oxazolidinone", "O=C1OC2CCC=CC2N1c1ccc(OC)cc1")), (2, Hp), (2, E)])
R(10, "reagent (sulfate, 4 equiv)", "SO₄²⁻ → SO₄•⁻ + e⁻ (the S₂O₈²⁻ the radicals form is reduced back to SO₄•⁻ at the cathode)",
  "SO₄•⁻ abstracts the tertiary C–H; the carbon radical is oxidized at the anode to the cation, which MeCN and then water trap (Ritter)",
  [(1, A("1,3-dimethyladamantane", "CC12CC3CC(CC(C3)C1)(C2)C")), (1, A("MeCN", "CC#N")), (1, H2O)],
  [(1, A("N-(3,5-dimethyladamantyl)acetamide", "CC(=O)NC12CC3CC(C)(CC(C)(C3)C1)C2")), (2, Hp), (2, E)])
R(11, "catalyst (cobalt)", "Co(II) + e⁻ → Co(I); Co(I) + H⁺ → Co(III)–H",
  "Co–H adds to the terminal alkene (with bipyridine ligands, studied under its conditions A, the exemplar suggests migratory insertion is more consistent than hydrogen-atom transfer); in the model's bookkeeping a second reduction and protonation give the alkane",
  [(1, A("alprenolol", "C=CCc1ccccc1OCC(O)CNC(C)C")), (2, Hp), (2, E)],
  [(1, A("dihydroalprenolol", "CCCc1ccccc1OCC(O)CNC(C)C"))])
R(12, "substrate", "RCO₂H → RCO₂⁻ + H⁺ (Me4NOH, 0.15 equiv); RCO₂⁻ → R• + CO₂ + e⁻", "",
  [(2, A("10-undecenoic acid", "C=CCCCCCCCCC(=O)O"))],
  [(1, A("eicosa-1,19-diene", "C=CCCCCCCCCCCCCCCCCC=C")), (2, CO2), (2, Hp), (2, E)], n_limiting=2)
R(13, "catalyst (nickel)", "Ni(II) + e⁻ → reduced nickel (the exemplar assigns no oxidation states)",
  "nickel activates the aryl bromide and captures the alkyl radical; reductive elimination forms the C–C bond (the cross-electrophile mechanism the exemplar cites, not one it reports)",
  [(1, A("5-bromo-3-isopropylindole", "CC(C)c1c[nH]c2ccc(Br)cc12")), (1, A("4-bromo-1-Boc-piperidine", "BrC1CCN(CC1)C(=O)OC(C)(C)C")), (2, E)],
  [(1, A("5-(1-Boc-piperidin-4-yl)-3-isopropylindole", "CC(C)c1c[nH]c2ccc(cc12)C1CCN(CC1)C(=O)OC(C)(C)C")), (2, Brm)])
R(14, "catalyst (nickel)", "Ni(II) + e⁻ → low-valent Ni",
  "low-valent nickel reduces each redox-active ester to an alkyl radical and couples the two",
  [(1, G("R¹CO₂NPhth", R1=1, C=1, O=2, NPhth=1)), (1, G("R²CO₂NPhth", R2=1, C=1, O=2, NPhth=1)), (2, E)],
  [(1, G("R¹–R²", R1=1, R2=1)), (2, CO2), (2, G("PhthN⁻", NPhth=1, q=-1))])
R(15, "substrate (through solvent-derived radicals)", "H₂O/MeOH → HO•/MeO• + H⁺ + e⁻ at the BDD anode; the coupled intermediate is oxidized again",
  "the solvent-derived radical takes the phenol O–H; the phenoxyl radical adds to the arene (the exemplar proposes this route because phenol and arene oxidize at almost the same potential, so direct oxidation cannot be selective)",
  [(1, A("4-methylguaiacol", "Cc1ccc(O)c(OC)c1")), (1, A("1,2,4-trimethoxybenzene", "COc1ccc(OC)c(OC)c1"))],
  [(1, A("2-hydroxy-2′,3,4′,5′-tetramethoxy-5-methylbiphenyl", "Cc1cc(OC)c(O)c(c1)-c1cc(OC)c(OC)cc1OC")), (2, Hp), (2, E)])
R(16, "substrate (the arene; the carboxylate at the anode)", "NC–C₆H₄–CN + e⁻ → radical anion (cathode); RCO₂⁻ → R• + CO₂ + e⁻ (anode)",
  "the transient alkyl radical couples with the persistent radical anion; cyanide leaves",
  [(1, G("RCO₂⁻", R=1, C=1, O=2, q=-1)), (1, A("1,4-dicyanobenzene", "N#Cc1ccc(C#N)cc1"))],
  [(1, G("4-R-benzonitrile", R=1, C=7, H=4, N=1)), (1, CO2), (1, A("CN⁻", "[C-]#N"))],
  kind="paired", note="one electron at each electrode per product, in a 25 µm interelectrode gap")
R(17, "mediator (dissolved O₂)", "O₂ + H⁺ + e⁻ → HO₂• (pH 2; pKa 4.88)",
  "HO₂• reduces hypoiodous acid to HO•, which adds to the alkyl iodide; the R–I(II)(OH)• adduct fragments to R• and HOI (the exemplar's relay, Schemes 3–4); R• adds to the alkene and the adduct radical is reduced and protonated",
  [(1, A("iPrI", "CC(C)I")), (1, A("phenyl vinyl sulfone", "C=CS(=O)(=O)c1ccccc1")), (1, Hp), (2, E)],
  [(1, A("iPrCH₂CH₂SO₂Ph", "CC(C)CCS(=O)(=O)c1ccccc1")), (1, A("I⁻", "[I-]"))])
R(18, "catalyst (rhodium)", "Rh(I) → Rh(III) + 2 e⁻",
  "Cp*Rh(III) activates the ortho C–H, inserts the acrylate and releases the product as Rh(I)",
  [(1, A("benzoic acid", "OC(=O)c1ccccc1")), (1, A("butyl acrylate", "C=CC(=O)OCCCC"))],
  [(1, A("3-substituted phthalide", "O=C1OC(CC(=O)OCCCC)c2ccccc12")), (2, Hp), (2, E)])
R(19, "catalyst (copper)", "Cu(I) → Cu(II) + e⁻",
  "the photoexcited anthraquinone oxidizes the arene by electron transfer and the radical cation loses a proton (not HAT); Cu(II)–CN captures the benzylic radical and eliminates the nitrile; the reduced quinone is reoxidized at the anode",
  [(1, A("n-butylbenzene", "CCCCc1ccccc1")), (1, A("CN⁻", "[C-]#N"))],
  [(1, A("2-phenylpentanenitrile", "CCCC(C#N)c1ccccc1")), (1, Hp), (2, E)])
R(20, "catalyst (nickel)", "Ni(II)bpy + 2 e⁻ → Ni(0)bpy",
  "Ni(0) adds ArBr; the arylnickel(II) is reduced to ArNi(I), which adds the second ArBr, and the diaryl-Ni(III) eliminates the biaryl (the left-hand cycle of the exemplar's Scheme 1)",
  [(2, A("PhBr", "Brc1ccccc1")), (2, E)],
  [(1, A("biphenyl", "c1ccc(cc1)-c1ccccc1")), (2, Brm)], n_limiting=2)
R(21, "substrate (on a TEMPO-modified electrode)", "ArOH → ArO• + e⁻ + H⁺", "",
  [(2, A("2-naphthol", "Oc1ccc2ccccc2c1"))],
  [(1, A("1,1′-bi-2-naphthol", "Oc1ccc2ccccc2c1-c1c(O)ccc2ccccc12")), (2, Hp), (2, E)], n_limiting=2)
R(22, "substrate", "CH₂=CHCN + 2 e⁻ → dianion (two one-electron stages), protonated by water to ⁻CH₂CH₂CN", "the carbanion adds to a second acrylonitrile; the adiponitrile anion takes a proton from water",
  [(2, A("acrylonitrile", "C=CC#N")), (2, H2O), (2, E)],
  [(1, A("adiponitrile", "N#CCCCCC#N")), (2, OHm)], n_limiting=2)
R(23, "substrate", "ArH + e⁻ → ArH•⁻ (twice per ring, with protonation by DMU)", "",
  [(1, A("naphthalene", "c1ccc2ccccc2c1")), (4, Hp), (4, E)],
  [(1, A("1,4,5,8-tetrahydronaphthalene", "C1C=CCC2=C1CC=CC2"))])
R(24, "substrate", "ArNO₂ → ArNO → ArNHOH → ArNH₂", "",
  [(1, A("3-nitrobenzotrifluoride", "O=[N+]([O-])c1cccc(c1)C(F)(F)F")), (6, Hp), (6, E)],
  [(1, A("3-(trifluoromethyl)aniline", "Nc1cccc(c1)C(F)(F)F")), (2, H2O)])
R(25, "substrate", "heteroarene + e⁻ → radical anion (twice, with protonation)", "",
  [(1, A("methyl 2-thiophenecarboxylate", "COC(=O)c1cccs1")), (2, Hp), (2, E)],
  [(1, A("methyl 2,5-dihydrothiophene-2-carboxylate", "COC(=O)C1SCC=C1"))])
R(26, "substrate (thiol)", "ArSH → ArS• + e⁻ + H⁺", "the thiyl radical adds to the diazo carbon with loss of N₂; the adduct is oxidized and captured by the alcohol",
  [(1, A("4-FC₆H₄SH", "Fc1ccc(S)cc1")), (1, A("ethyl diazoacetate", "CCOC(=O)C=[N+]=[N-]")), (1, MeOH)],
  [(1, A("ethyl 2-(arylthio)-2-methoxyacetate", "CCOC(=O)C(OC)Sc1ccc(F)cc1")), (1, A("N₂", "N#N")), (2, Hp), (2, E)])
R(27, "substrate", "ArBr + 2 e⁻ → Ar⁻ + Br⁻, then protonation", "",
  [(1, A("4-phenoxybromobenzene", "Brc1ccc(Oc2ccccc2)cc1")), (1, Hp), (2, E)],
  [(1, A("diphenyl ether", "c1ccc(Oc2ccccc2)cc1")), (1, Brm)])
R(28, "substrate (hydrogenated on Pd by surface hydrogen; H₃O⁺ takes the electrons)", "H₃O⁺ + e⁻ → Pd–H (twice)", "two surface hydrogens add to the adsorbed aldehyde (electrocatalytic hydrogenation)",
  [(1, A("benzaldehyde", "O=Cc1ccccc1")), (2, Hp), (2, E)],
  [(1, A("benzyl alcohol", "OCc1ccccc1"))])
R(29, "mediator (ACT aminoxyl)", "ACT → ACT⁺ + e⁻",
  "the oxoammonium oxidizes the alcohol to the aldehyde and its hydrate to the acid",
  [(1, A("RCH₂OH (levetiracetam alcohol)", "CCC(CO)N1CCCC1=O")), (1, H2O)],
  [(1, A("RCO₂H", "CCC(C(=O)O)N1CCCC1=O")), (4, Hp), (4, E)])
R(30, "substrate", "ArCH₃ → benzylic cation (2 e⁻), trapped by MeOH; repeated", "",
  [(1, A("4-tBu-toluene", "Cc1ccc(cc1)C(C)(C)C")), (2, MeOH)],
  [(1, A("4-tBu-benzaldehyde dimethyl acetal", "COC(OC)c1ccc(cc1)C(C)(C)C")), (4, Hp), (4, E)])
R(31, "substrate", "amide → N-acyliminium + 2 e⁻ + H⁺", "",
  [(1, A("N,N-dimethylacetamide", "CC(=O)N(C)C")), (1, MeOH)],
  [(1, A("N-(methoxymethyl)-N-methylacetamide", "COCN(C)C(C)=O")), (2, Hp), (2, E)])
R(32, "mediator (chloride)", "2 Cl⁻ → Cl₂ + 2 e⁻",
  "Cl₂/HOCl and ethylene give the chlorohydrin in the anolyte; mixing with the hydroxide-rich catholyte after electrolysis closes the epoxide and returns the second Cl⁻",
  [(1, A("ethylene", "C=C")), (1, H2O)],
  [(1, A("ethylene oxide", "C1CO1")), (2, Hp), (2, E)])
R(33, "substrate (carbonate; oxidant used ex-cell)", "2 CO₃²⁻ → C₂O₆²⁻ + 2 e⁻",
  "peroxodicarbonate is pumped out of the cell and oxidizes lignin to vanillin in a separate vessel",
  [(2, A("CO₃²⁻", "[O-]C([O-])=O"))],
  [(1, A("C₂O₆²⁻", "[O-]C(=O)OOC(=O)[O-]")), (2, E)], kind="ex-cell", n_limiting=2)
R(34, "mediator (chloride)", "2 Cl⁻ → Cl₂ + 2 e⁻",
  "the electrogenerated chlorine oxidant takes the thioether to the sulfoxide and then the sulfone; Cl⁻ returned",
  [(1, A("4-methyl-2-(methylthio)pyrimidine", "CSc1nccc(C)n1")), (2, H2O)],
  [(1, A("4-methyl-2-(methylsulfonyl)pyrimidine", "CS(=O)(=O)c1nccc(C)n1")), (4, Hp), (4, E)])
R(35, "mediator (Cl₄NHPI)", "Cl₄NHPI⁻ → Cl₄PINO• + e⁻",
  "the N-oxyl radical abstracts the allylic H; tBuOOH, oxidized to tBuOO• (a separate −e⁻ step in the exemplar's mechanism), traps the allylic radical, and the peroxide eliminates tBuOH; the model routes both anodic electrons through the mediator",
  [(1, A("valencene", "CC1CCC=C2CCC(CC12C)C(C)=C")), (1, A("tBuOOH", "CC(C)(C)OO"))],
  [(1, A("nootkatone", "CC1CC(=O)C=C2CCC(CC12C)C(C)=C")), (1, A("tBuOH", "CC(C)(C)O")), (2, Hp), (2, E)])
R(36, "substrate (cinnamate)", "ArCH=CHCO₂⁻ → radical + e⁻",
  "the monoalkyl sulfite (from ROH, SO₂ and base) adds; a second oxidation and loss of CO₂ give the alkenesulfonate",
  [(1, A("cinnamate⁻", "[O-]C(=O)/C=C/c1ccccc1")), (1, A("neopentyl alcohol", "CC(C)(C)CO")), (1, A("SO₂", "O=S=O"))],
  [(1, A("neopentyl (E)-styrenesulfonate", "CC(C)(C)COS(=O)(=O)/C=C/c1ccccc1")), (1, CO2), (1, Hp), (2, E)])
R(37, "mediator (ACT aminoxyl)", "ACT → ACT⁺ + e⁻",
  "the oxoammonium oxidizes the alcohol and both aldehyde groups in turn",
  [(1, A("HMF", "OCc1ccc(C=O)o1")), (2, H2O)],
  [(1, A("FDCA", "OC(=O)c1ccc(o1)C(=O)O")), (6, Hp), (6, E)])
R(38, "substrate (initiator)", "anethole → anethole•⁺ + e⁻",
  "the radical cation adds the diene; the adduct radical cation oxidizes the next anethole (chain)",
  [(1, A("trans-anethole", "COc1ccc(/C=C/C)cc1")), (1, A("isoprene", "C=CC(C)=C"))],
  [(1, A("cyclohexene adduct", "COc1ccc(cc1)C1CC=C(C)CC1C"))], kind="chain",
  note="no net electrons; the paper completes the reaction with 0.1 F mol⁻¹, the count carried")
R(39, "mediator (hydroquinone)", "H₂Q → BQ + 2 H⁺ + 2 e⁻",
  "Pd(II) oxidizes the alkene (Wacker); BQ reoxidizes Pd(0) and returns H₂Q, at the rate the palladium turns over",
  [(1, A("1-decene", "C=CCCCCCCCC")), (1, H2O)],
  [(1, A("2-decanone", "CC(=O)CCCCCCCC")), (2, Hp), (2, E)])
R(40, "substrate", "RCO₂H → R⁺ + CO₂ + H⁺ + 2 e⁻", "",
  [(1, A("N-Piv-alanine", "CC(C)(C)C(=O)NC(C)C(=O)O")), (1, MeOH)],
  [(1, A("N,O-acetal", "CC(C)(C)C(=O)NC(C)OC")), (1, CO2), (2, Hp), (2, E)])
R(41, "catalyst (cobalt, initiator)", "Co(II) + e⁻ + H⁺ → Co(III)–H",
  "Co–H adds to and leaves the alkene, moving the double bond and regenerating itself (chain)",
  [(1, A("5-methyl-1-phenylhex-5-en-3-ol", "CC(=C)CC(O)CCc1ccccc1"))],
  [(1, A("5-methyl-1-phenylhex-4-en-3-ol", "CC(C)=CC(O)CCc1ccccc1"))], kind="chain",
  note="no net electrons; 3 F mol⁻¹ is the charge the exemplar passes for this compound, and that charge is carried")
R(42, "mediator (triarylamine)", "Ar₃N → Ar₃N•⁺ + e⁻",
  "the ketone is activated and adds MeCN (Ritter) to an enamide; the aminium oxidizes it and the cation cyclizes",
  [(1, A("benzyl phenyl ketone", "O=C(Cc1ccccc1)c1ccccc1")), (1, A("MeCN", "CC#N"))],
  [(1, A("2-methyl-4,5-diphenyloxazole", "Cc1nc(-c2ccccc2)c(-c2ccccc2)o1")), (2, Hp), (2, E)])
R(43, "catalyst (nickel)", "Ni(II)(tet a)²⁺ + e⁻ → Ni(I)(tet a)⁺",
  "Ni(I) transfers an electron to the aryl iodide; the aryl radical cyclizes 5-exo and takes a hydrogen atom from the solvent (the exemplar's Scheme 1); the second electron and proton assume the solvent radical is reduced and protonated, which the exemplar does not state",
  [(1, A("allyl 2-iodophenyl ether", "C=CCOc1ccccc1I")), (1, Hp), (2, E)],
  [(1, A("3-methyl-2,3-dihydrobenzofuran", "CC1COc2ccccc12")), (1, A("I⁻", "[I-]"))])
R(44, "substrate", "ArCO₂H → aroyloxy radical + e⁻ + H⁺; cyclized radical oxidized", "",
  [(1, A("biphenyl-2-carboxylic acid", "OC(=O)c1ccccc1-c1ccccc1"))],
  [(1, A("benzo[c]chromen-6-one", "O=C1Oc2ccccc2-c2ccccc12")), (2, Hp), (2, E)])
R(45, "substrate", "ArCH₂R → benzylic cation + 2 e⁻ + H⁺, trapped by fluoride", "",
  [(1, A("ethylbenzene", "CCc1ccccc1")), (1, A("F⁻", "[F-]"))],
  [(1, A("(1-fluoroethyl)benzene", "CC(F)c1ccccc1")), (1, Hp), (2, E)])
R(46, "mediator (bromide)", "2 Br⁻ → Br₂ + 2 e⁻",
  "Br₂ brominates the arene; one Br⁻ returned",
  [(1, A("anisole", "COc1ccccc1")), (1, Brm)],
  [(1, A("4-bromoanisole", "COc1ccc(Br)cc1")), (1, Hp), (2, E)])
R(47, "reagent (sulfinate, 2 equiv), then the adduct radical", "ArSO₂⁻ → ArSO₂• + e⁻",
  "the sulfonyl radical adds to the alkene; the benzylic radical is oxidized at the anode and captured by MeOH",
  [(1, A("α-methylstyrene", "CC(=C)c1ccccc1")), (1, A("TolSO₂⁻", "Cc1ccc(cc1)S(=O)[O-]")), (1, MeOH)],
  [(1, A("β-methoxy sulfone", "COC(C)(CS(=O)(=O)c1ccc(C)cc1)c1ccccc1")), (1, Hp), (2, E)])
R(48, "mediator (thiocyanate)", "2 SCN⁻ → (SCN)₂ + 2 e⁻",
  "thiocyanogen thiocyanates the arene; one SCN⁻ returned",
  [(1, A("anisole", "COc1ccccc1")), (1, A("SCN⁻", "[S-]C#N"))],
  [(1, A("4-thiocyanatoanisole", "COc1ccc(SC#N)cc1")), (1, Hp), (2, E)])
R(49, "reagent (phosphite, 5 equiv), then the adduct", "P(OEt)₃ → P(OEt)₃•⁺ + e⁻",
  "the arene captures the phosphorus radical cation; the adduct is oxidized and loses an ethyl group",
  [(1, A("mesitylene", "Cc1cc(C)cc(C)c1")), (1, A("P(OEt)₃", "CCOP(OCC)OCC")), (1, H2O)],
  [(1, A("diethyl mesitylphosphonate", "CCOP(=O)(OCC)c1c(C)cc(C)cc1C")), (1, A("EtOH", "CCO")), (2, Hp), (2, E)])
R(50, "substrate", "anilide N–H → amidyl radical + e⁻ + H⁺ (twice); N–N bond formed (one of the two routes the exemplar proposes; the other closes the ring by nucleophilic attack after one oxidation, with the same two electrons)", "",
  [(1, A("2,2-dimethyl-N,N′-di(4-methylphenyl)malonamide", "CC(C)(C(=O)Nc1ccc(C)cc1)C(=O)Nc1ccc(C)cc1"))],
  [(1, A("4,4-dimethyl-1,2-di(4-methylphenyl)pyrazolidine-3,5-dione", "CC1(C)C(=O)N(c2ccc(C)cc2)N(c2ccc(C)cc2)C1=O")), (2, Hp), (2, E)])

## Electrons per carrier in the electrode step as written above, for the rows whose carrier is not
## the substrate. Asserted against n_carrier in reactions_50.csv.
NC_STEP = {1: 1, 2: 1, 5: 1, 6: 1, 8: 1, 9: 1, 11: 1, 13: 1, 14: 1, 17: 1, 18: 2, 19: 1, 20: 2, 29: 1, 32: 1,
           34: 1, 35: 1, 37: 1, 39: 2, 41: 1, 42: 1, 43: 1, 46: 1, 48: 1}

## Electrode steps written as balanced half-reactions in the electrode_step column, checked in atoms and charge
## by the same composition code as the overall equations: row -> list of (lhs, rhs), one pair per half-reaction.
ESTEP_CHECK = {
 4: [([(1, A("amidine", "CN(c1ccccc1)C(=N)c1ccccc1F"))],
      [(1, A("amidinyl radical", "CN(c1ccccc1)C(=[N])c1ccccc1F")), (1, Hp), (1, E)]),
     ([(1, A("cyclohexadienyl radical", "CN1C(c2ccccc2F)=NC2C=CC=C[C]12"))],
      [(1, A("benzimidazole", "Cn1c(-c2ccccc2F)nc2ccccc21")), (1, Hp), (1, E)])],
 7: [([(1, A("anisole", "COc1ccccc1"))],
      [(1, A("anisole•⁺", "C[O+]=C1C=C[CH]C=C1")), (1, E)]),
     ([(1, A("adduct radical cation", "CO[C]1C=CC([n+]2ccccc2)C=C1"))],
      [(1, A("N-(4-methoxyphenyl)pyridinium⁺", "COc1ccc(cc1)[n+]1ccccc1")), (1, Hp), (1, E)])],
}

def main():
    neg = "--negative-control" in sys.argv
    if neg:      # three perturbations, one per assertion: an unbalanced atom, a wrong electron count, a wrong carrier count
        ROWS[2]["rhs"] = [t for t in ROWS[2]["rhs"] if t[1][0] != Hp[0]] + [(1, Hp)]
        ROWS[23]["lhs"] = [(4, t[1]) if t[1][0] in (E[0], Hp[0]) else t for t in ROWS[23]["lhs"]] ; ROWS[23]["rhs"] = [(1, t[1]) if t[1][0] == H2O[0] else t for t in ROWS[23]["rhs"]]
        NC_STEP[39] = 1
    rx = list(csv.DictReader(io.open(os.path.join(HERE, "reactions_50.csv"), encoding="utf-8")))
    ed = list(csv.DictReader(io.open(os.path.join(HERE, "electrode_direction.csv"), encoding="utf-8")))
    assert [r["row"] for r in ROWS] == list(range(1, 51)), "rows must be 1..50 in order"
    out, bad = [], []
    for k, pairs in ESTEP_CHECK.items():
        for lhs, rhs in pairs:
            L, Rr = side(lhs), side(rhs)
            dd = {x: L[x] - Rr[x] for x in set(L) | set(Rr) if L[x] != Rr[x]}
            if dd:
                bad.append("row %d: electrode half-reaction %s does not balance, lhs - rhs = %s" % (k, fmt(lhs) + " → " + fmt(rhs), dd))
    for r, t, d in zip(ROWS, rx, ed):
        assert d["reaction"] == t["reaction"]
        L, Rr = side(r["lhs"]), side(r["rhs"])
        keys = set(L) | set(Rr)
        diff = {k: L[k] - Rr[k] for k in keys if L[k] != Rr[k]}
        if diff:
            bad.append("row %d %s: does not balance, lhs - rhs = %s" % (r["row"], t["reaction"], diff))
        ne_l = sum(n for n, (lab, _) in r["lhs"] if lab == E[0]); ne_r = sum(n for n, (lab, _) in r["rhs"] if lab == E[0])
        direction = "cathodic" if ne_l else ("anodic" if ne_r else d["direction"])
        ne = (ne_l or ne_r) / r["n_limiting"]
        ns, nc = float(t["n_substrate"]), float(t["n_carrier"])
        if r["kind"] in ("stoichiometric", "ex-cell"):
            if direction != d["direction"]:
                bad.append("row %d: equation is %s, electrode_direction.csv says %s" % (r["row"], direction, d["direction"]))
            if abs(ne - ns) > 1e-9:
                bad.append("row %d %s: %g e- per limiting substrate in the equation, n_substrate = %g" % (r["row"], t["reaction"], ne, ns))
        else:
            if ne_l or ne_r:
                bad.append("row %d: a %s row must balance without electrons" % (r["row"], r["kind"]))
        if t["carrier_type"] == "substrate":
            if abs(nc - ns) > 1e-9:
                bad.append("row %d: a substrate-carried row with n_carrier %g != n_substrate %g" % (r["row"], nc, ns))
        elif abs(NC_STEP.get(r["row"], -1) - nc) > 1e-9:
            bad.append("row %d %s: electrode step carries %s e- per carrier, n_carrier = %g" % (r["row"], t["reaction"], NC_STEP.get(r["row"]), nc))
        ctype = t["carrier_type"]
        want = {"substrate": ("substrate", "reagent"), "mediator": ("mediator",), "catalyst": ("catalyst",)}[ctype]
        if not r["active"].startswith(want):
            bad.append("row %d: electroactive species '%s' but carrier_type is %s" % (r["row"], r["active"], ctype))
        eq = fmt(r["lhs"]) + " → " + fmt(r["rhs"])
        out.append(dict(row=r["row"], reaction=t["reaction"], electrode={"anodic": "anode", "cathodic": "cathode"}[d["direction"]],
                        electroactive=r["active"], electrode_step=r["estep"], solution_step=r["sstep"],
                        overall=eq, kind=r["kind"], n_substrate=("%g" % ns), n_carrier=("%g" % nc),
                        ceiling_set_by=ctype, note=r["note"]))
    if neg:
        hit = (any("row 3 " in b and "does not balance" in b for b in bad), any("row 24 " in b for b in bad), any("row 39 " in b and "per carrier" in b for b in bad))
        print("\n".join(bad))
        print("G-STOICH control: %s (unbalanced atom %s, wrong electron count %s, wrong carrier count %s)"
              % ("GOOD" if all(hit) else "BAD", *["caught" if h else "MISSED" for h in hit]))
        sys.exit(0 if all(hit) else 1)
    if bad:
        print("\n".join(bad)); print("G-STOICH: FAIL (%d problems)" % len(bad)); sys.exit(1)
    dst = os.path.join(HERE, "reaction_stoichiometry.csv")
    if "--check" in sys.argv:
        ## the gate form: build in memory and compare with the shipped table; nothing is written
        buf = io.StringIO(newline="")
        w = csv.DictWriter(buf, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
        have = io.open(dst, encoding="utf-8", newline="").read() if os.path.exists(dst) else ""
        if buf.getvalue() != have:
            print("G-STOICH: FAIL -- data/reaction_stoichiometry.csv is not what this builder produces; re-run it without --check")
            sys.exit(1)
        print("G-STOICH: PASS -- all 50 rows balance in atoms and charge; electrons, electrodes and carrier types agree with the reaction table; shipped table is current")
        return
    with io.open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    from collections import Counter as C
    print("all 50 rows balance in atoms and charge; electron counts, electrodes and carrier types agree with the model")
    print("kinds:", dict(C(o["kind"] for o in out)))
    print("wrote -> data/reaction_stoichiometry.csv")
    print("G-STOICH: PASS")

if __name__ == "__main__":
    main()
