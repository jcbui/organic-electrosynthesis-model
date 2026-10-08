## run_mediated.jl — the full EC' matrix: every mediated reaction x every reactor archetype,
## with mediator generation at the electrode BC and substrate consumption coupled
## through the homogeneous source term R = k*c_ox*c_S in the film (npp_ecprime.jl).
##
## k values are order-of-magnitude literature-anchored ESTIMATES (provenance in
## SI Table S6); conclusions are regime placements (x_k vs delta), robust on a
## log scale. Substrate D from Wilke-Chang (build_reactions50.py conventions).
## Electron bookkeeping: s_j per ELECTRON (s_red=-1/n_c per molecule); nu_S =
## -1/(n_S*s_ox) substrates consumed per Med_ox in the homogeneous event.
##   nohup /opt/julia/bin/julia run_mediated.jl > run_mediated.log 2>&1 &

using Printf
include("params.jl"); include("correlations.jl"); include("npp_ecprime.jl")

struct MedSpec
    label::String
    k_M::Float64            # M^-1 s^-1 (estimate; SI Table S6)
    nu_solv::Float64        # kinematic viscosity m^2/s
    D_red::Float64          # for delta correlations (carrier)
    n_c::Float64            # electrons per mediator molecule
    n_S::Float64            # electrons per substrate molecule
    C_med::Float64          # mol/m^3
    C_S::Float64
    D_S::Float64
    species::Vector{ECSpecies}
end

## species tuple: (name, z, D, c_bulk, s per e-, nu per homogeneous event)
S(args...) = ECSpecies(args...)
tr(C) = C * 1e-5     # trace bulk value for the electrogenerated form

## conditions PAGE-VERIFIED against the primary-source PDFs (papers-for-model corpus,
## Jul 2026); see build_reactions50.py VERIFIED dict for anchors.
SPECS = MedSpec[
 MedSpec("Br-mediated Hofmann rearrangement", 3.3, 4.755e-7, 2.7e-9, 1, 2, 80., 400., 1.8611e-09,
   ## k = 3.3 M-1 s-1 (2026-10-06, author): HOBr + propionamide, the unbranched primary amide nearest 2-phenylacetamide,
   ## apparent at pH 7.2-7.5 and 22 C; Heeb, Criquet, Zimmermann-Steffens & von Gunten, Water Res. 2014, 48, 15, Table 6
   ## p. 30, compiled from Pattison & Davies 2004 (2-methylpropionamide 1.5, trimethylacetamide 0.9). It was a declared 1e3.
   ## Malviya/Cantillo OPRD 2023 scale-up: 0.4 M amide, NaBr 0.08 M in MeCN
   ## (MeOH 10 equiv = reagent, no alkoxide base). RC(O)NH2 + Br2 + MeOH ->
   ## carbamate + 2 H+ + 2 Br-: sum z_j*nu_j = 0 (charge-conserving)
   [S("Br-",  -1.0, 2.7e-9, 80.001,  -1.0, +2.0),      # 2 Br- returned per Br2
    S("Br2",   0.0, 2.2e-9, tr(80.), +0.5, -1.0),
    S("Sub",   0.0, 1.8611e-09, 400.,    0.0, -1.0),      # phenylacetamide, 2 e-, 1 Br2/S
    S("H+",   +1.0, 3.0e-9, 1e-3,     0.0, +2.0),      # HBr released; sum z*nu = 0
    S("Na+",  +1.0, 1.33e-9, 80.,     0.0,  0.0)]),
 MedSpec("ACT-mediated alcohol oxidation (flow, hectogram)", 20., 8.93e-7, 5.93e-10, 1, 4, 25., 500., 7.2207e-10,
   ## Zhong/Stahl OPRD 2021 200-g campaign: 0.5 M alcohol, ACT 25 mM (5 mol%),
   ## purely aqueous 1 M NaHCO3 / 1 M Na2CO3 pH 8.5 -- released H+ is buffered
   [S("ACT",  0.0, 5.93e-10, 25.,    -1.0, +1.0),
    S("ACT+",+1.0, 5.93e-10, tr(25.),+1.0, -1.0),
    S("Sub",  0.0, 7.2207e-10, 500.,    0.0, -0.25),     # 4 ox per alcohol: the paper takes the
                                                         # primary alcohol to the carboxylic acid
    S("Na+", +1.0, 1.33e-9, 3000.,    0.0,  0.0),
    S("CO3--",-2.0, 0.92e-9, 1000.,   0.0, -1.0),      # buffer absorbs the proton:
    S("HCO3-",-1.0, 1.18e-9, 1000. + tr(25.), 0.0, +1.0)]),  # sum z*nu = 0
 MedSpec("Cl-mediated ethylene epoxidation", 10., 8.93e-7, 2.03e-9, 1, 2, 1000., 3.52, 1.87e-09,
   ## SUBSTRATE D = 1.87e-9 is MEASURED (Cussler, Diffusion 3rd ed., Table 5.2-1 p. 127, ethylene
   ## at infinite dilution in water, 25 C), adopted 2026-09-05 in place of propene's Wilke-Chang
   ## value: the row is the ethylene system and carries ethene's solubility, so the diffusivity is
   ## ethene's too. Both copies below are bound to data/mediated_substrates.csv by G-DSUB.
   ## Leow/Sargent Science 2020. CORRECTED 2026-08-23: the row carried "2 M NaCl aq". NaCl does
   ## not appear in the paper and 2 M is not a condition it reports. The quoted condition is
   ## "a flow-cell setup with 1.0 M potassium chloride (KCl) electrolyte, in which ethylene was
   ## continuously sparged into the anolyte" -- 70(+/-1)% FE to ethylene oxide at 300 mA/cm2.
   ## Propylene appears only in fig. S9, so the row now models the paper's headline system.
   ## The counter-ion is K+ (D = 1.96e-9), NOT Na+ (1.33e-9) -- a 47% more mobile cation, which
   ## changes the migration split, so this is not a cosmetic relabel.
   ## SUBSTRATE 3.52 mol/m3 = ethene in 1.000 M KCl at 298.15 K, 101.3 kPa -- MEASURED, not
   ## estimated: IUPAC Solubility Data Series Vol. 57 (ethene, comp. C. L. Young), original
   ## measurement Yano, Suetaka, Umehara & Horiuchi, Kagaku Kogaku 1974, 38, 320-323. The KCl
   ## series reads 0.500/1.000/1.500 M -> 4.14/3.52/3.03 mmol/L against 4.83 in pure water.
   ## Cross-checked twice inside the same volume: the compilation's own Sechenov slope is
   ## -0.136 +/- 0.001 L/mol and log10(4.83/3.52) = 0.1374; and the series is monotonic across
   ## KBr, KCl and CuCl2. The salting-out correction (-27%) is now APPLIED, not flagged -- this
   ## row's substrate-limited ceiling is a real value, no longer an upper bound.
   [S("Cl-", -1.0, 2.03e-9, 1000.001, -1.0, +1.0),
    S("OX",   0.0, 1.4e-9,  tr(1000.),+1.0, -1.0),     # per-electron chlorine equiv
    S("Sub",  0.0, 1.87e-09, 3.52,      0.0, -0.5),
    S("H+",  +1.0, 9.3e-9, 1e-3,       0.0, +1.0),     # Cl2 hydrolysis/chlorohydrin H+
    S("K+",  +1.0, 1.96e-9, 1000.,     0.0,  0.0)]),
 MedSpec("NHPI-mediated allylic C-H -> enone", 20.2, 3.90e-7, 2.09e-9, 1, 2, 33., 167., 1.8660e-09,
   ## Horn/Baran Nature 2016: Cl4NHPI 33 mM (20 mol%), substrate 167 mM,
   ## k = 20.2 M-1 s-1 (2026-10-05): electrogenerated PINO + cyclohexene in MeCN with pyridine, Ueda, Noyama,
   ## Ohmori & Masui, Chem. Pharm. Bull. 1987, 35, 1372, Table II p. 1375 (allylic substrates 12.8-77.6). It was
   ## 0.5, the order of PINO + substituted TOLUENES in acetic acid (Koshino 2003) -- a benzylic value in another
   ## solvent, carried for an ALLYLIC oxidation whose own exemplar cites the Masui study as its kinetic reference.
   ## ACETONE, LiClO4 0.1 M, pyridine base takes the anodic proton
   ## The species at the anode is the N-oxide ANION: 'deprotonation of Cl4NHPI by pyridine, followed by anodic
   ## oxidation, leads to the tetra-chlorophthalimido N-oxyl radical' (Horn p. 81), carrier_charge.csv z = -1.
   ## Electrode: NHPI(-) -> PINO + e-. Solution: PINO + 1/2 Sub -> NHPI, which pyridine deprotonates back to the
   ## anion, the proton leaving as pyridinium ("H+" below, 33 mM in the bulk as the anion's counter-cation).
   [S("NHPI", -1.0, 2.09e-9, 33.,    -1.0, +1.0),
    S("PINO", 0.0, 2.09e-9, tr(33.),+1.0, -1.0),
    S("H+",  +1.0, 3.0e-9, 33.,      0.0, +1.0),       # pyridinium; sum z*nu = -1 + 1 = 0
    S("Sub",  0.0, 1.8660e-09, 167.,    0.0, -0.5),       # 2 anodic e- per enone; tBuOOH (1.5 equiv)
                                                          # supplies the oxygen and the other two
    S("Li+", +1.0, 1.0e-9, 100.,     0.0,  0.0),
    S("ClO4-",-1.0, 1.7e-9, 100.,    0.0,  0.0)]),
 MedSpec("HMF -> FDCA (biomass)", 50., 8.93e-7, 5.93e-10, 1, 6, 40., 100., 9.5163e-10,
   ## Cardiel/Choi ACS SCE 2019 concentrated run: HMF 100 mM + ACT 40 mM,
   ## 0.5 M borate buffer pH 10 (not KOH); borate absorbs the released proton
   [S("ACT",   0.0, 5.93e-10, 40.,    -1.0, +1.0),
    S("ACT+", +1.0, 5.93e-10, tr(40.),+1.0, -1.0),
    S("Sub",   0.0, 9.5163e-10, 100.,    0.0, -1/6),
    ## 0.500 M boron at pH 10 (Mesmer 1972 Q11, activity-corrected; data/hmf_buffer_speciation.py, G-BORATE):
    ## B(OH)4- 452 / B(OH)3 48 / Na+ 452 mM. D(B(OH)4-) from Corti 1980 lambda0 by Nernst-Einstein; D(B(OH)3) Park & Lee 1994
    S("Na+",  +1.0, 1.33e-9, 452.,     0.0,  0.0),
    S("B(OH)4-",-1.0, 9.39e-10, 452. + tr(40.), 0.0, -1.0),  # buffer base consumed;
    S("B(OH)3", 0.0, 1.64e-9, 48.,    0.0, +1.0)]),        # sum z*nu = 0
 ## k = 0.06 M-1 s-1 (chemistry audit, 2026-10-05; was a declared 1e2). BQ is not consumed by the alkene but by Pd(0), and
 ## the palladium turns over no faster than 0.14 s-1 with stoichiometric BQ (0.025 s-1 at the maximum electrolysis current),
 ## Miller & Wayner, Can. J. Chem. 1992, 70, 2485, p. 2487. In-film regeneration of H2Q is therefore capped at
 ## TOF x [Pd] = 0.14 s-1 x 1.18 mM (0.1 mmol / 85 mL); as the rate law below writes it, k = TOF [Pd] / (C_BQ C_S)
 ## = 0.14 x 1.18e-3 / (0.0235 x 0.118) = 0.0595 M-1 s-1. x_k ~ 0.4 mm: thicker than every film (the shuttle limit).
 MedSpec("BQ-mediated Wacker-Tsuji oxidation", 0.06, 5.85e-7, 1.78e-9, 2, 2, 22., 110., 1.1729e-09,
   ## Miller/Wayner CJC 1992 print the molarities themselves (Results, p 2486): "benzoquinone (0.022 M ...),
   ## palladium acetate (0.0011 M ...), olefin (0.11 M)" -- BQ 22 mM, olefin 110 mM (2 and 10 mmol over the
   ## 85 mL of solvent and the olefin's own volume). HClO4 0.015-0.36 M in the paper; 150 mM is mid-range.
   [S("H2Q", 0.0, 1.78e-9, 22.,      -0.5, +1.0),
    S("BQ",  0.0, 1.78e-9, tr(22.), +0.5, -1.0),
    S("H+", +1.0, 3.0e-9, 150.,     +1.0,  0.0),
    S("Sub", 0.0, 1.1729e-09, 110.,     0.0, -1.0),       # BQ = 2 e-; 1 BQ per alkene
    S("Q+", +1.0, 1.0e-9, 100.,      0.0,  0.0),
    S("ClO4-",-1.0, 1.7e-9, 250.,    0.0,  0.0)]),
 MedSpec("Br- oxidation / electrophilic bromination", 2.28e4, 9.227e-7, 2.08e-9, 1, 2, 250., 33.3, 9.7945e-10,
   ## k = 2.28e4 M-1 s-1 (2026-10-05): Br2 + ANISOLE, this row's own carrier and substrate, measured in water at
   ## 20 C: (2.23 +/- 0.14)e4 para + (5.4 +/- 0.6)e2 ortho, Sivey, Bickley & Victor, Environ. Sci. Technol. 2015,
   ## 49, 4937, Table 1 p. 4941. It was a declared 1e3 ("conservative low end") while the measurement sat in a
   ## source the row already cited. The row is transport-limited: no cell moves by more than 0.4 %.
   ## Zhang/Su Nat Commun 2025, the campaign run on ANISOLE (2026-10-06): the divided H-cell of Methods and Fig 4,
   ## "each cell was filled with 7.5 mL acetonitrile and 7.5 mL 0.5 mol/L NaBr aqueous solution. 0.5 mmol
   ## substrate was dissolved in the anodic cell": anisole 0.5/15 = 33.3 mM, Br- 0.5 x 7.5/15 = 250 mM, water/MeCN
   ## 1:1. The flow runs of Fig 5b/c (10:10:10:3 medium, 518 g) are on drug and natural-product derivatives.
   [S("Br-", -1.0, 2.08e-9, 250.001, -1.0, +1.0),      # 1 Br- returned (1 Br into product)
    S("Br2",  0.0, 1.2e-9,  tr(250.),+0.5, -1.0),
    S("Sub",  0.0, 9.7945e-10, 33.3,    0.0, -1.0),
    S("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),      # ArH + Br2 -> ArBr + Br- + H+; sum z*nu = 0
    S("Na+", +1.0, 1.33e-9, 250.,     0.0,  0.0)]),
 ## ArH + (SCN)2 -> ArSCN + SCN- + H+ (2 e- per substrate): SCN mass and charge
 ## both close (2 SCN in -> 1 in product + 1 regenerated; +1 charge in H+, -1 in SCN-)
 MedSpec("Aryl thiocyanation (NH4SCN)", 100., 1.13e-6, 8.7e-10, 1, 2, 100., 250., 6.9056e-10,
   ## Gitkis/Becker EA 2010 constant-current runs: NH4SCN 0.1 M + ArH 0.25 M,
   ## LiClO4 0.1 M in the AcOH/HCOOH 1:1 CC medium (0.5 M belongs to the glacial-
   ## AcOH CPE variant); D(SCN-) Walden-scaled from lambda0(MeCN)
   [S("SCN-",  -1.0, 8.7e-10, 100.,    -1.0, +1.0),       # Walden: 3.02e-9 (MeCN, NE from lambda0 113.3) x 0.369/1.28
    S("(SCN)2", 0.0, 5.5e-10, tr(100.),+0.5, -1.0),
    S("Sub",    0.0, 6.9056e-10, 250.,    0.0, -1.0),    # 1 ArH per (SCN)2, 2 e-/ArH
    S("H+",    +1.0, 2.0e-9, 1e-3,      0.0, +1.0),
    S("NH4+",  +1.0, 2.0e-9, 100.,      0.0,  0.0),
    S("Li+",   +1.0, 1.0e-9, 100.,      0.0,  0.0),
    S("ClO4-", -1.0, 1.7e-9, 100.001,   0.0,  0.0)]),
 ## ── THREE ROWS CARRIED AS MEDIATED SINCE 2026-10-05 ──────────────────────────────────────────
 ## Each was typed as a direct electrolysis of its substrate until the exemplars were read for the
 ## species that actually exchanges electrons with the electrode (docs/REACTION_AUDIT_20261005.md).
 ##
 ## Zhang/K. Xu/Zeng OL 2018: N-OPiv biaryl amide 0.04 M and NaBr 0.04 M (1 equiv) in MeCN/MeOH
 ## 14:1, "NaBr as the catalyst and electrolyte"; "anodically in situ generated bromine is
 ## intercepted by the substrate" to give the N-Br intermediate. ArC(O)NH-OPiv + Br2 -> lactam +
 ## 2 H+ + 2 Br-: sum z*nu = 0. k: N-bromination of an amide N-H by Br2 -- the step, and so the
 ## decade, of the Hofmann row above.
 MedSpec("Amidyl-radical C-H amination (phenanthridinone)", 3.3, 4.755e-7, 2.7e-9, 1, 2, 40., 40., 1.1580e-09,
   ## k = 3.3 (2026-10-06): the same N-bromination step as the Hofmann row, carried over from it as before (Heeb Table 6).
   [S("Br-",  -1.0, 2.7e-9, 40.001,  -1.0, +2.0),
    S("Br2",   0.0, 2.2e-9, tr(40.), +0.5, -1.0),
    S("Sub",   0.0, 1.1580e-09, 40.,   0.0, -1.0),      # N-OPiv biaryl amide, 2 e-, 1 Br2/S
    S("H+",   +1.0, 3.0e-9, 1e-3,     0.0, +2.0),
    S("Na+",  +1.0, 1.33e-9, 40.,     0.0,  0.0)]),
 ## Bottecchia/Strotman OPRD 2022 kilo run: thioether 0.47 M in MeCN / 0.1 M aq HCl 6:1, so
 ## chloride 14 mM (3 mol%), Et4NPF6 0.085 M. "Cl- being oxidized at the anode ... and acting as
 ## the mediator". R2S + 2 Cl2 + 2 H2O -> R2SO2 + 4 HCl, written per electron-equivalent of
 ## oxidant as for the ethylene row: OX + 1/4 S -> Cl- + H+, sum z*nu = 0.
 ## k IS BOUNDED BELOW BY THE EXEMPLAR'S OWN OPERATION. Its planar RuO2/Ti flow cell ran at
 ## 40 mA/cm2 with 0.1 M thioether and the same 14 mM chloride; a mediated cell cannot exceed
 ## the plateau n F C_med sqrt(D_ox k C_S) once the film is thicker than the reaction layer, so
 ##   k >= (i / (F C_med))^2 / (D_ox C_S) = (400 / (96485 x 14))^2 / (2.6e-9 x 100) = 0.34 m3/mol/s
 ## i.e. 3.4e2 M-1 s-1 (2.2e2 if only the 80 pct faradaic efficiency is credited). The adopted
 ## 1e3 is the lowest decade not below that bound.
 MedSpec("Thioether -> sulfone (kilo-scale)", 1e3, 5.854e-7, 2.3e-9, 1, 4, 14., 470., 1.4265e-09,
   [S("Cl-", -1.0, 2.3e-9, 14.001, -1.0, +1.0),
    S("OX",   0.0, 2.6e-9, tr(14.), +1.0, -1.0),      # per-electron chlorine equiv, Walden-scaled
    S("Sub",  0.0, 1.4265e-09, 470.,  0.0, -0.25),    # 4 e- per sulfone; 4-methyl-2-(methylthio)pyrimidine
    S("H+",  +1.0, 3.0e-9, 14.001,   0.0, +1.0),      # the HCl proton; one more per oxidant consumed
    S("Q+",  +1.0, 1.0e-9, 85.,      0.0,  0.0),
    S("A-",  -1.0, 1.5e-9, 85.,      0.0,  0.0)]),
 ## Li/Wilden Chem Sci 2020 -- A CATHODIC ROW (sum z*s = -1). "the only species that was redox
 ## active at the potentials employed was molecular oxygen"; "the alkyl halide is not reduced
 ## within the redox window of the solvent". Alkene 79 mM (limiting), iodide 95 mM, in 10 mL
 ## pH-2 HCl + 5 mL MeCN with NaCl 7 mol%; O2 at air saturation, 0.266 mol/m3 (CRC p. 5-134).
 ## Written as O2 + H+ + e- -> HO2. at the cathode (pH 2, pKa 4.88) and HO2. + 1/2 S -> O2 + 1/2 P in solution
 ## (2 e- per product, the proton from the aqueous acid): sum z*nu = 0.
 ## k IS FIXED BY THE EXEMPLAR'S OWN CHARGE RECORD. The electrolysis is potentiostatic on the
 ## oxygen wave, so the current it draws is the mediated limit of that cell: "around 300 C" over
 ## the ~84 ks charge record (Fig. 2) on 4.12 cm2 is a mean 8.7 A/m2, and the plateau n F C_med sqrt(D k C_S) reaches it at
 ##   k = (8.7 / (96485 x 0.266))^2 / (2.1e-9 x 79) = 0.69 m3/mol/s, i.e. 7e2 M-1 s-1: decade 1e3.
 ## The product C_med sqrt(k) is what the record fixes, so the ceiling does not depend on the
 ## oxygen solubility assumed for the mixed solvent.
 MedSpec("Cathodic Giese (R-I + alkene)", 1e3, 9.574e-7, 2.1e-9, 1, 2, 0.266, 95., 1.0055e-09,
   ## the reduced oxygen is the NEUTRAL hydroperoxyl radical at pH 2 (pKa 4.88, Li/Wilden Chem. Sci. 2020 p. 5336), so the
   ## electrode step consumes the proton: O2 + H+ + e- -> HO2. It was O2- (z = -1) until the chemistry audit of 2026-10-05.
   [S("O2",   0.0, 2.1e-9, 0.266,      -1.0, +1.0),
    S("HO2",  0.0, 2.1e-9, tr(0.266),  +1.0, -1.0),
    S("Sub",  0.0, 1.0055e-09, 95.,     0.0, -0.5),    # 2-iodopropane, the species the relay activates (chemistry audit pass 2); 2 e- per product
    S("H+",  +1.0, 9.3e-9, 6.7,        -1.0,  0.0),
    S("Na+", +1.0, 1.33e-9, 5.6,        0.0,  0.0),
    S("Cl-", -1.0, 2.03e-9, 12.3, 0.0, 0.0)]),
 ## Reclassified from the catalyst rows (chemistry audit, 2026-10-05): tri(p-tolyl)amine is an outer-sphere electron-transfer
 ## mediator. No rate constant exists for its radical cation with the ketone, and the exemplar runs on carbon felt at constant
 ## voltage (Bao OL 2022, Table 1), so no bound can be read from its operation either: k = 0, the floor, with the declared
 ## band of S5.7 as its sensitivity. 5 mM amine (10 mol%), 0.05 M benzyl phenyl ketone, 0.3 M LiClO4/MeCN.
 MedSpec("Oxazole synthesis from ketones and acetonitrile", 0.0, 4.755e-7, 1.1225e-9, 1, 2, 5., 50., 1.4703e-09,
   [S("Ar3N",   0.0, 1.1225e-9, 5.,       -1.0, +1.0),
    S("Ar3N+", +1.0, 1.1225e-9, tr(5.),   +1.0, -1.0),
    S("Sub",    0.0, 1.4703e-09, 50.,      0.0, -0.5),   # 2 e- per oxazole
    S("H+",    +1.0, 3.0e-9, 1e-3,         0.0, +1.0),
    S("Li+",   +1.0, 1.863e-9, 300.,       0.0,  0.0),
    S("ClO4-", -1.0, 2.759e-9, 300. + 1e-3 + tr(5.), 0.0, 0.0)]),
]


## ONE-ROW MODE, for the sensitivity sweeps. MED_ONLY="<label>" restricts this run to that spec, so
## a perturbation of one row re-solves its seven cells in an isolated copy of this directory
## rather than every cell of the matrix in place. Unset in production, where it changes nothing.
if !isempty(get(ENV, "MED_ONLY", ""))
    filter!(s -> s.label == ENV["MED_ONLY"], SPECS)
    isempty(SPECS) && error("MED_ONLY=$(ENV["MED_ONLY"]) matches no MedSpec label")
    println("ONE-ROW MODE: ", SPECS[1].label)
end

## ---------------------------------------------------------------------------------------------
## reactions_table.jl was never loaded here at all -- run_mediated.jl was fully self-contained,
## which is exactly why its numbers could drift from the audited ones without anything noticing.
include("reactions_table.jl")

## G-MEDSYNC. Every MedSpec below duplicates a carrier and substrate concentration that also lives
## in reactions_table.jl, which build_reactions50.py generates from the audited reactions_50.csv.
## Nothing tied the two together. On 2026-08-23 the condition audit corrected the bromination row
## in the CSV (Br- 0.25 -> 0.152 M, arene 0.12 -> 0.121 M), the table regenerated correctly, this
## file did not, and the re-solve silently reported the OLD ceiling with no warning of any kind.
## That is the same failure mode as a silent Tier-0 fallback: a stale number wearing a fresh
## timestamp. This assertion makes the two sources agree or stops the run.
for spec in SPECS
    k = findfirst(r -> r.name == spec.label, RXNS)
    k === nothing && error("G-MEDSYNC: MedSpec \"$(spec.label)\" matches no row in " *
                           "reactions_table.jl. If a row was renamed, rename it here too.")
    r = RXNS[k]
    ## nu is checked at 0.5% because this file writes it to 3 s.f. while the table carries the
    ## full mu/rho quotient; anything larger is real drift between the two sources.
    if abs(spec.nu_solv - r.nu) > 0.005 * r.nu
        error("G-MEDSYNC: $(spec.label) disagrees with reactions_table.jl on nu: " *
              "run_mediated.jl has $(spec.nu_solv) m^2/s, the generated table has $(r.nu). " *
              "solvents.csv is the source of truth -- fix this file, not the table.")
    end
    for (what, mine, theirs) in (("C_med", spec.C_med, r.C), ("C_S", spec.C_S, r.Csub))
        ## reactions_table.jl prints concentrations to four decimals of mol/m^3 (one decimal until
        ## 2026-10-05, which is why this floor used to be 0.06). 1% relative, floored at 0.0006
        ## mol/m^3 absolute so that the 0.266 mol/m^3 oxygen row is held as tightly as the rest.
        ## Real drift is tens of percent (the bromination row this gate was written for was out by
        ## 64%), so this still fails loudly on anything that matters.
        if abs(mine - theirs) > max(0.0006, 0.01 * abs(theirs))
            error("G-MEDSYNC: $(spec.label) disagrees with reactions_table.jl on $what: " *
                  "run_mediated.jl has $mine mol/m^3, the audited table has $theirs mol/m^3. " *
                  "reactions_50.csv is the source of truth -- fix this file, not the table.")
        end
    end
end
println("G-MEDSYNC: all $(length(SPECS)) MedSpecs agree with reactions_table.jl")

## ── invariant checks: every spec must satisfy the model's conservation laws ──
for spec in SPECS
    zs  = sum(sp.z * sp.s  for sp in spec.species)
    znu = sum(sp.z * sp.nu for sp in spec.species)
    en  = sum(sp.z * sp.c_bulk for sp in spec.species)
    ## +1 for an anodic row, -1 for a cathodic one (the Giese row, oxygen reduced at the cathode)
    @assert isapprox(abs(zs), 1.0; atol = 1e-9)  "sum z*s != +/-1 (electrode BC): $(spec.label)"
    @assert isapprox(znu, 0.0; atol = 1e-9) "homogeneous step injects charge (div i != 0): $(spec.label)"
    @assert abs(en) < 1e-6 * maximum(sp.c_bulk for sp in spec.species) "bulk not electroneutral: $(spec.label)"
end
println("invariants OK: |sum z*s| = 1, sum z*nu = 0, bulk EN for all $(length(SPECS)) specs")

open(joinpath(@__DIR__, "mediated_ec_matrix.csv"), "w") do io
    println(io, "reaction,reactor,delta_um,xk_um,i_tier0_mAcm2,i_saveant_mAcm2,i_subcap_mAcm2,i_ec_mAcm2,amplification,limiter,flag,path")
    for spec in SPECS
        ## nu COMES FROM THE GENERATED TABLE, not from the MedSpec literal. nu = mu/rho is a
        ## DERIVED quantity: build_reactions50.py computes it from solvents.csv at full precision
        ## and writes it into reactions_table.jl, which run_all50_np.jl already uses. This file
        ## carried its own 3-s.f. copy, so the two could drift -- and they nearly did: nu(MeCN) is
        ## 4.755e-7 at the printed mu = 0.369 mPa s but 4.420e-7 at the retired 0.343, and the
        ## literal was updated by hand when that correction landed, with nothing checking it.
        ## The MedSpec field is retained as an inline record and is asserted against this value
        ## by G-MEDSYNC above; the solve uses the generated number.
        nu_rx = RXNS[findfirst(r -> r.name == spec.label, RXNS)].nu
        km = spec.k_M / 1000.0                       # m^3/mol/s
        xk = sqrt(spec.species[2].D / (km * spec.C_S))
        isb = findfirst(s -> s.name == "Sub", spec.species)
        @printf("=== %s  (k = %g M-1s-1, x_k = %.1f um)\n", spec.label, spec.k_M, xk*1e6)
        flush(stdout)
        ## mesh matched to the physics (audit finding, SI S5.6): resolve the
        ## reaction layer (dx1 ~ x_k/50) but do NOT hyper-stretch when x_k is
        ## large — a fixed 0.03 um first cell ill-conditions the Jacobian in
        ## the deep-depletion migration regime and stalls the Newton ramp.
        mkprob = dd -> ECProblem(spec.species, 2, isb, km,
                                 geometric_faces(dd, clamp(xk / 50, 0.02e-6, 0.9 * dd / 90),
                                                 90))
        ## THE SAME PROBLEM WITH THE HOMOGENEOUS SOURCE SWITCHED OFF. This is the correct floor
        ## for an EC-prime answer: the source can only ADD flux, so i_ec must be at least the k = 0
        ## solve of the identical species set, mesh and boundary conditions.
        ##
        ## The acceptance test used to compare against `0.9 * i_t0`, where i_t0 is the FICK
        ## expression F*D*C/(|s|*delta) -- no migration at all. Once migration is in the model that
        ## bound is far too weak: for Br- oxidation x unstirred the Fick figure is 10.17 mA/cm2
        ## while the k = 0 solve WITH migration is 20.44, so a c-control walk that died at 14.26
        ## cleared 0.9*10.17 comfortably and was published, even though it sits 30% BELOW the
        ## no-source floor of its own physics. Four of the 48 cells were being accepted that way.
        mkprob0 = dd -> ECProblem(spec.species, 2, isb, 0.0,
                                  geometric_faces(dd, clamp(xk / 50, 0.02e-6, 0.9 * dd / 90),
                                                  90))
        ## k = 0 floor, solved with the same ramp-then-c-control treatment the real cells get, so
        ## the floor is not itself a fold-limited underestimate.
        ## Returns BOTH the k = 0 limit and the converged state at it. solve_ilim_ec_ktrack
        ## continues the fold from that state, and re-solving it there would repeat this work.
        function k0_floor(dd, i_scale)
            p0 = mkprob0(dd)
            i0, lim0, u0s, i0s = solve_ilim_ec(p0; i_start = 0.02 * i_scale, growth = 1.15)
            u0 = copy(u0s)
            if i0s > 0.0
                ic0, limc0, uc0, _, _ = solve_ilim_ec_ccontrol(p0; u0 = u0s, i0 = i0s)
                if (startswith(limc0, "collapse") || startswith(limc0, "plateau") ||
                    startswith(limc0, "limit reached")) && ic0 > i0
                    i0 = ic0; u0 = copy(uc0)
                end
            end
            (i0, u0)
        end
        ## Solve in order of INCREASING delta so that a cell which cannot be reached by ramping
        ## the current from bulk can be continued from the next-smaller delta, which can. The
        ## direct solve is still tried FIRST for every cell and accepted whenever it clears the
        ## commuting bound, so the 47 cells that already worked are untouched and bit-identical;
        ## only a cell that would otherwise be published as a dead solve takes the new path.
        ## See the delta-continuation note in npp_ecprime.jl.
        order = sort(collect(REACTORS), by = r -> delta_eff(r.key, spec.D_red, nu_rx))
        rows = Dict{String,String}()
        anchor = nothing        # (d, p, u, i) from the last cell that solved cleanly
        for r in order
            d = delta_eff(r.key, spec.D_red, nu_rx)
            i_t0  = F_const * spec.D_red * spec.C_med / (abs(spec.species[1].s) * d)
            i_sav = spec.n_c * F_const * spec.C_med * sqrt(spec.species[2].D * km * spec.C_S)
            i_cap = spec.n_S * F_const * spec.D_S * spec.C_S / d
            ## the migration-inclusive no-source floor for THIS cell
            i_k0, u_k0 = k0_floor(d, i_t0)
            floor_i = max(0.9 * i_t0, i_k0)
            p = mkprob(d)
            il, lim, u_safe, i_safe = solve_ilim_ec(p; i_start = 0.02 * i_t0, growth = 1.15)
            path = "direct-ramp"
            ## THE CURRENT RAMP HAS A FOLD AT THE LIMITING CURRENT and cannot cross it:
            ## dc_surf/di -> -infinity as i -> i_lim, so the Jacobian degenerates exactly at the
            ## answer. 44 of these 48 cells used to stop there and be published as lower bounds.
            ## Concentration-controlled continuation has no such fold -- c_surf is monotone
            ## through it -- so the criterion is reached rather than approached. Run it on EVERY
            ## cell, starting from the ramp's last safe state, and take it whenever it actually
            ## reaches collapse. See docs/ECPRIME_WALL_FINDING.md.
            if i_safe > 0.0
                ic, limc, uc, frac, br = solve_ilim_ec_ccontrol(p; u0 = u_safe, i0 = i_safe)
                ## Accept c-control ONLY if the answer also clears the commuting bound. The
                ## homogeneous source can only ADD to the mediator flux, so i_ec < i_t0 is not a
                ## physical answer whatever terminated the walk -- and a continuation started
                ## from a dead ramp state can die early and report exactly that. Without this
                ## guard Br- oxidation x unstirred was accepted at 11.54 against its own bound
                ## of 16.72, with the mediator still at 76% of bulk.
                if (startswith(limc, "collapse") || startswith(limc, "plateau") ||
                    startswith(limc, "limit reached")) && ic >= floor_i
                    il, lim, path = ic, limc, "c-control"
                    u_safe, i_safe = uc, ic
                else
                    lim = lim * "; " * limc
                end
            end
            ## CONTINUATION CASCADE. No cell is ever allowed to fall back to simpler physics;
            ## instead each continuation is tried in turn and the first result that clears the
            ## commuting bound is taken. Different cells need different paths, which is a fact
            ## about the branch structure, not a fudge:
            ##   * k-continuation starts from the ANALYTIC k = 0 solution (i_t0, gate G5) and
            ##     walks k up. It is the only thing that reaches the inverted (gamma < 1)
            ##     deep-total-catalysis cells -- Br- oxidation x unstirred, gamma = 0.29, which
            ##     defeats the ramp, c-control, delta-continuation and four mesh refinements.
            ##   * delta-continuation walks in from a solved smaller-delta neighbour. It is what
            ##     reaches Hofmann x unstirred, which k-continuation does not.
            if il < floor_i
                ## ANCHOR THE CONTINUATION ON THE MIGRATION-INCLUSIVE k = 0 LIMIT, not the Fick
                ## one. solve_ilim_ec_kcont ramps the k = 0 problem to frac_i (0.85) of the limit
                ## it is handed, walks k up at that FIXED current, then reads the limit off the
                ## polarisation curve. Handing it i_t0 -- the Fick expression, no migration --
                ## anchored Br- oxidation x unstirred at 0.85 x 10.17 = 8.65 mA/cm2 when the true
                ## k = 0 limit for that cell is 20.44. Starting less than half way up, the
                ## subsequent c-control walk settled on a lower branch and returned 15.53, BELOW
                ## the no-source floor -- which cannot happen physically, since the homogeneous
                ## source only regenerates mediator. i_k0 is the same quantity computed with
                ## migration, so the continuation now starts where it should.
                rk = solve_ilim_ec_kcont(kk -> ECProblem(spec.species, 2, isb, kk,
                        geometric_faces(d, clamp(xk / 50, 0.02e-6, 0.9 * d / 90), 90)),
                        km, max(i_t0, i_k0))
                if rk !== nothing && rk[1] > il
                    @printf("  %-28s k-continuation from the analytic k=0 limit -> %.2f mA/cm2\n",
                            r.label, rk[1]*0.1)
                    il, lim, path = rk[1], rk[2], "k-continuation"
                    u_safe, i_safe = rk[3], rk[1]
                end
            end
            if il < floor_i && anchor !== nothing
                res = solve_ilim_ec_continued(mkprob, anchor[1], d, anchor[2], anchor[3], anchor[4])
                if res !== nothing && res.i > il
                    @printf("  %-28s ramp and c-control both died (%.2f < commuting bound %.2f); delta-continued from %.1f um -> %.2f mA/cm2\n",
                            r.label, il*0.1, floor_i*0.1, anchor[1]*1e6, res.i*0.1)
                    il, path = res.i, "delta-continued"
                    lim = "delta-continued; " * lim
                    p, u_safe, i_safe = res.p, res.u, res.i
                    ## and now c-control FROM THE RECOVERED STATE. The first pass above began
                    ## at the ramp's last safe point, which for a dead cell IS the dead solve --
                    ## c-control cannot climb out of that, which is why this cell alone was
                    ## still being published as a delta-continued bound rather than a collapse.
                    ic2, limc2, uc2, _f2, _br2 = solve_ilim_ec_ccontrol(p; u0 = u_safe, i0 = i_safe)
                    if startswith(limc2, "collapse") || startswith(limc2, "plateau") || startswith(limc2, "limit reached")
                        il, lim, path = ic2, limc2, "delta-continued + c-control"
                        u_safe, i_safe = uc2, ic2
                    end
                end
            end
            ## LIMIT-TRACKING IN k -- the last step, and the one that reaches the cell no other
            ## path does. It runs only when everything above has left the cell below its own
            ## no-source floor, so the 47 cells that already clear the bound are untouched and
            ## bit-identical. Unlike k-continuation it carries the state ALONG the fold as k
            ## rises rather than holding the current fixed beneath it; see npp_ecprime.jl.
            if il < floor_i
                rt = solve_ilim_ec_ktrack(kk -> ECProblem(spec.species, 2, isb, kk,
                        geometric_faces(d, clamp(xk / 50, 0.02e-6, 0.9 * d / 90), 90)),
                        km, i_k0, u_k0)
                if rt !== nothing && rt[1] > il
                    @printf("  %-28s k-limit-tracked from the k=0 fold -> %.2f mA/cm2\n",
                            r.label, rt[1]*0.1)
                    il, lim, path = rt[1], rt[2], "k-limit-tracked"
                    u_safe, i_safe = rt[3], rt[1]
                end
            end
            flag = il >= floor_i ? "ok" : "wall"
            amp = il / i_t0
            if flag == "ok" && i_safe > 0.0
                anchor = (d, p, copy(u_safe), i_safe)
            end
            @printf("  %-28s delta %7.1f um  tier0 %8.1f  EC' %8.1f mA/cm2  (x%.2f, %s)\n",
                    r.label, d*1e6, i_t0*0.1, il*0.1, amp, lim)
            flush(stdout)
            rows[r.label] = "\"$(spec.label)\",\"$(r.label)\",$(d*1e6),$(xk*1e6),$(i_t0*0.1),$(i_sav*0.1),$(i_cap*0.1),$(il*0.1),$(amp),\"$lim\",\"$flag\",\"$path\""
        end
        ## write back in the canonical REACTORS order, not the solve order
        for r in REACTORS
            println(io, rows[r.label]); flush(io)
        end
    end
end
println("MATRIX DONE")
