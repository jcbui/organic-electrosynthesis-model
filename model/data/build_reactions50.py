"""
Section 4 model — build the 50-reaction representative set with transport properties.

Selection method: stratified by the reaction-class distribution of our curated corpus,
now 25,941 SciFinder-confirmed electrochemical reactions on the KHL reparse (Figure 1b of
the MS; the pre-reparse corpus was 26,790 and the current one is a strict 96.8% subset of
it). The set was ASSEMBLED against the earlier structure-difference basis below; it is
scored against the live KHL taxonomy by data/khl_stratification.py, which is the gate:
  C-N 22.2% -> 11 | C-C coupling 22.2% -> 11 | Reduction 12.7% -> 6 | C-O 9.3% -> 5
  Ox(FGI) 8.4% -> 4 | Other/redox-neutral 8.2% -> 4 | C-C cyclization 5.2% -> 3
  Halogenation 4.2% -> 2 | C-S 4.1% -> 2 | Other bond 3.4% -> 2      == 50
SUPERSEDED 2026-08-22: the shares below describe the RETIRED Polarity_Classifier
reanalysis (now in _archive/figure1_old_pipeline_20260822/). Fig. 1b is built from the KHL
pipeline (Figure_1b_Kasie/), whose classes are keyed on bond changes of the mapped reactant
atoms: cyclization is its own class and outranks the bond-forming classes, so C-C/C-N/C-O/C-S
are acyclic-only. New shares (n = 21,459): cyclization 20.9, C-C 18.7, C-N 15.1, FGI 8.9,
other bond 7.5, multicomponent 6.3, C-O 5.9, oxidation 5.2, C-S 4.6, reduction 3.9,
halogenation 3.1. The 50-reaction set has NOT been re-classified under those rules -- see
SI S1.2, where the stratification claim is withdrawn rather than restated.
Retired text follows.
Fig. 1b was reanalyzed with the atom-mapped polarity classifier
(Polarity_Classifier/): Reduction + Ox(FGI) merge into FGI (17.5%, split 54:46 red:ox);
Other/redox-neutral decomposes into dehydrative exchange 4.3% / deprotection 1.2% /
isomerization 0.2% (record noise excluded; basis n = 21,410 on that retired basis; the
live KHL basis is n = 21,459). The set composition tracks
the reanalyzed distribution within 5 points per populated class (SI section S4); the
set itself is unchanged.

Each entry: citable exemplar, transport-limiting CURRENT CARRIER (substrate | mediator |
catalyst), carrier concentration, electrons per carrier turnover at the electrode (n_c),
solvent system, supporting electrolyte. D estimated by Wilke-Chang (organics, Le Bas
molar volume from RDKit atom counts) or Stokes-Einstein (metal complexes, assigned
hydrodynamic radius). Every value carries a provenance tag for the SI.

Units: C in mol/L in the table (SI: mol/m^3 = 1000*M); D in cm^2/s; T = 298.15 K.
"""
import os as _os
import numpy as np, pandas as pd
from rdkit import Chem

T = 298.15
kB = 1.380649e-23

# ------------------------------------------------------------------ OUTPUT PATHS, cwd-independent
# This script is WRITE-ONLY: it reads no repository file and emits four. Until 2026-08-02 all four
# were bare relative names ("reactions_50.csv", "solvents.csv", "electrolytes.csv" and
# "reactions_table.jl"), so running it from anywhere but data/ deposited fresh copies into the
# CURRENT DIRECTORY and left the repository copies untouched -- silently, with a zero exit status
# and a success message naming the four files. Because reactions_50.csv and electrolytes.csv are
# the upstream of the SI registry (build_param_tables.py) and reactions_table.jl is consumed by the
# Julia solvers, that failure mode desynchronised the registry from its own generator without
# raising anything. The three CSVs belong beside this file in data/; reactions_table.jl belongs in
# the sibling julia/ directory, which is where the solvers include it from and where the shipped
# copy has always lived. All four are now anchored on __file__ so the script is cwd-independent.
_HERE = _os.path.dirname(_os.path.abspath(__file__))          # .../Section4_Model/data
_REPO = _os.path.dirname(_HERE)                               # .../Section4_Model
OUT_REACTIONS   = _os.path.join(_HERE, "reactions_50.csv")
OUT_SOLVENTS    = _os.path.join(_HERE, "solvents.csv")
OUT_ELECTROLYTE = _os.path.join(_HERE, "electrolytes.csv")
OUT_RXN_TABLE   = _os.path.join(_REPO, "julia", "reactions_table.jl")

# ---------------------------------------------------------------- solvents (CRC/Riddick, 25 C)
# key: (M g/mol, mu mPa.s, rho g/mL, phi_assoc, note)
# The fifth field is the PROVENANCE LOCATOR, not a bare source tag. It mirrors, verbatim in
# substance, the locator carried by the matching rows of data/parameters_provenance.csv
# (category 2), so the compact working table and the registry cannot drift apart or be read as
# disagreeing about how well sourced a property is. Before 2026-08-22 this field said "CRC",
# which the governing standard explicitly rejects as a locator ("CRC Handbook alone is not
# enough") -- the registry rows were properly anchored all along, only this file was not.
# Mixed solvents keep their mixing-rule descriptions: they are estimates and have NO registry
# rows at all, which is a real gap and is recorded in docs/PROVENANCE_AUDIT_20260822.md.
SOLVENTS = {
    "MeCN":      (41.05, 0.369, 0.776, 1.0, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids': MeCN p.6-243 and DMA p.6-244, eta(25 C) column, column assignment pinned by x-coordinate and confirmed in that same column against DMF 0.794, dimethyl sulfoxide 1.987, ethanol 1.074, 1,4-dioxane 1.177 and diethyl ether 0.224, each of which reads its accepted 25 C value; Sect.15 pp.15-13..15-20 (rho only -- that table carries no printed viscosity column)"),
    "MeOH":      (32.04, 0.544, 0.786, 1.9, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids' pp.6-243..6-247 (mu, 25 C); Sect.15 'Laboratory Solvents' pp.15-13..15-20 (rho)"),
    "EtOH":      (46.07, 1.074, 0.785, 1.5, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids' pp.6-243..6-247 (mu, 25 C); Sect.15 'Laboratory Solvents' pp.15-13..15-20 (rho)"),
    "DMF":       (73.09, 0.794, 0.944, 1.0, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids' pp.6-243..6-247 (mu, 25 C); Sect.15 'Laboratory Solvents' pp.15-13..15-20 (rho)"),
    "DMA":       (87.12, 1.927, 0.937, 1.0, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids': MeCN p.6-243 and DMA p.6-244, eta(25 C) column, column assignment pinned by x-coordinate and confirmed in that same column against DMF 0.794, dimethyl sulfoxide 1.987, ethanol 1.074, 1,4-dioxane 1.177 and diethyl ether 0.224, each of which reads its accepted 25 C value; Sect.15 pp.15-13..15-20 (rho only -- that table carries no printed viscosity column)"),
    "DMSO":      (78.13, 1.987, 1.096, 1.0, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids' pp.6-243..6-247 (mu, 25 C); Sect.15 'Laboratory Solvents' pp.15-13..15-20 (rho)"),
    "THF":       (72.11, 0.456, 0.883, 1.0, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids' pp.6-243..6-247 (mu, 25 C); Sect.15 'Laboratory Solvents' pp.15-13..15-20 (rho)"),
    "H2O":       (18.02, 0.890, 0.997, 2.6, "IAPWS reference correlations: Huber et al., J. Phys. Chem. Ref. Data 2009, 38, 101-125 (mu, 298.15 K / 0.1 MPa); Wagner & Pruss, ibid. 2002, 31, 387-535 (rho, IAPWS-95)"),
    "AcOH":      (60.05, 1.056, 1.045, 1.0, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids' pp.6-243..6-247 (mu, 25 C); Sect.15 'Laboratory Solvents' pp.15-13..15-20 (rho)"),
    "HFIP":      (168.04, 1.619, 1.596, 1.0, "mu MEASURED: Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587, Table 3 p. 578, '1,1,1,3,3,3-hexafluoropropan-2-ol' = 0.01619 P = 1.619 mPa s at 25 C (was 1.650, unsourced, -1.9%). rho 1.596: NO LONGER UNSOURCED, but it CONFLICTS with the one page-anchored source found. CRC 97th ed. 2016, 'Physical Constants of Organic Compounds' p. 3-296 entry 5801 (1,1,1,3,3,3-Hexafluoro-2-propanol, CAS 920-66-1, MW 168.037, liq, mp -2.0, bp 59(3)) prints den = 1.4600 at 21 C. Column assignment verified by x-coordinate, not by eye: 1.4600 sits at x=463.3, identical to a known density in the row below (0.8643 for hexamethylenimine), and 28 pt left of that row's nD (1.4631 at x=491.3). So CRC really does print 1.4600 as the density. IT FAILS AN INDEPENDENT PHYSICAL CROSS-CHECK. Calibrating the F-for-H molar-volume increment on 2,2,2-trifluoroethanol -- the directly analogous fluorinated alcohol -- gives (V_TFE - V_EtOH)/3 = (72.27 - 58.37)/3 = +4.63 cm3/mol per F. Applying 6 of those to isopropanol (V = 76.51) predicts V_HFIP = 104.32 cm3/mol, i.e. rho = 168.037/104.32 = 1.611. 1.596 is -0.9% from that; CRC's 1.4600 is -9.4%. Note also that CRC's neighbouring entry 5802 carries nD = 1.4631(20), numerically adjacent to HFIP's printed den 1.4600(21) one row up, which is consistent with a typesetting slip in that cell -- suggestive, not proven. THIRD SOURCE SETTLES IT (2026-08-24): the Sigma-Aldrich product specification for 1,1,1,3,3,3-hexafluoro-2-propanol lists density 1.596 g/mL at 25 C (lit.) AND refractive index n20/D 1.275 (lit.), alongside bp 59 C and mp -4 C which both match CRC. Because nD is 1.275, CRC's 1.4600 is NEITHER the density NOR the refractive index of this compound -- that rules out the last benign reading of the cell and confirms it as an error there, most likely a slip from the neighbouring entry 5802 whose nD is 1.4631(20). DECISION: rho = 1.596 g/cm3 at 25 C. Three independent lines agree -- the Sigma specification, the TFE-calibrated molar-volume estimate (1.611, -0.9%), and CRC's own bp/mp for the same entry. CAVEAT ON THE SOURCE TIER: the Sigma value is a supplier compilation marked '(lit.)', i.e. secondary, not a primary measurement, so this is state A- rather than state A. It must be cited as the Sigma-Aldrich specification, never as CRC, and the CRC disagreement must not be quietly dropped -- a reviewer checking CRC will find 1.4600 and needs this note to know why it was not used. A primary densitometry measurement would upgrade this to state A."),
    ## mixtures: mu from CRC mixture data at 25 C (water/alcohol mixtures sit at or
    ## near the viscosity MAXIMUM, well above volume-weighted estimates); phi chosen
    ## so that phi*M equals the Perkins-Geankoplis mole-fraction rule
    ## (phi*M)_mix = sum_j x_j phi_j M_j  (Poling 5th ed. Eq. 11-9.8).
    "MeCN/H2O":  (36.4,  0.48,  0.82,  1.17, "9:1 v/v; mu lit, phiM Perkins-Geankoplis"),
    "MeOH/H2O":  (26.4,  1.60,  0.87,  1.94, "1:1 v/v; CRC mu, phiM P-G"),
    "EtOH/H2O":  (33.0,  2.40,  0.89,  1.58, "1:1 v/v; CRC mu (40-50 wt%: 2.3-2.4), phiM P-G"),
    "DMF/H2O":   (56.0,  1.00,  0.96,  1.15, "9:1 v/v; mu lit, phiM P-G"),
    "acetone":   (58.08, 0.306, 0.784, 1.0, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids' pp.6-243..6-247 (mu, 25 C); Sect.15 'Laboratory Solvents' pp.15-13..15-20 (rho)"),
    "MeNO2":     (61.04, 0.620, 1.137, 1.0, "CRC 97th ed. 2016 (Haynes), Sect.6 'Viscosity of Liquids' pp.6-243..6-247 (mu, 25 C); Sect.15 'Laboratory Solvents' pp.15-13..15-20 (rho)"),
    "DMSO/THF":  (77.1,  1.55,  1.06,  1.00, "5:1 v/v; P-G"),
    "tAmOH/H2O": (35.0,  2.80,  0.85,  1.73, "3:1 v/v; mu est (viscous alcohol/water), phiM P-G"),
    "AcOH/HCOOH":(53.0,  1.28,  1.13,  1.0, "1:1 v/v est."),
    # phi 2.10 -> 1.916: the old pair was the VOLUME-fraction-weighted phi times the
    # volume-fraction-weighted M, not Eq. S30's mole-fraction sum(x_j phi_j M_j). At 2:1 v/v
    # water:MeCN, x(H2O)=0.854, so Eq. S30 gives 0.854*2.6*18.015 + 0.146*1.0*41.05 = 45.99,
    # against the tabled 2.10*24.0 = 50.40 (+9.6%). Only the product enters Wilke-Chang.
    "H2O/MeCN":  (24.0,  0.90,  0.94,  1.916, "2:1 v/v; phiM Eq. S30"),
    ## Added 2026-08-23 by the condition audit. Both are ORGANIC-ORGANIC mixtures, so unlike
    ## the water/alcohol entries above they do NOT sit near a viscosity maximum and a
    ## mole-fraction log-mixing rule is defensible; mu is an ESTIMATE, not a measurement, and is
    ## labelled as such. phi is set so phi*M reproduces the Perkins-Geankoplis mole-fraction sum,
    ## the same convention as every other mixture in this table.
    "THF/MeOH":  (60.65, 0.480, 0.867, 1.136, "5:1 v/v (ChemSusChem 2021 standard conditions). x(THF)=0.714. phi*M = 0.714*1.0*72.11 + 0.286*1.9*32.04 = 68.90 (Perkins-Geankoplis, Poling 5th ed. Eq. 11-9.8). mu 0.480 mPa s is a MOLE-FRACTION LOG-MIX ESTIMATE from THF 0.456 and MeOH 0.544 (CRC 97th ed.), not a measured mixture value; both endpoints lie within 20% of it so the estimate is tightly bracketed. rho volume-weighted."),
    "EtOH/MeOH": (37.79, 0.719, 0.786, 1.700, "1:1 v/v (Courtois/Perichon Tetrahedron 1997). x(EtOH)=0.410. phi*M = 0.410*1.5*46.07 + 0.590*1.9*32.04 = 64.25 (Perkins-Geankoplis). mu 0.719 mPa s is a MOLE-FRACTION LOG-MIX ESTIMATE from EtOH 1.074 and MeOH 0.544 (CRC 97th ed.), not measured; alcohol-alcohol mixtures are near-ideal. rho volume-weighted."),
}

# ------------------------------------------------- electrolytes (kappa mS/cm)
# 2026-08-02 RETRACTION PRUNE, REVERSED SAME DAY. Three keys were briefly deleted from this
# dict because SI §S6.1 and the Table S4 caption retract them BY NAME:
#     "0.1 M Bu4NBF4/DMF"                   3.5 mS/cm   (§S6.1, Table S4 caption)
#     "1 M KOH aq"                        200.0         (§S6.1, Table S4 caption)
#     "Me4N carboxylate (10 mol%)/acetone"  2.0         (Table S4 caption)
# All three are RESTORED below, marked `## RETRACTED`, for two reasons.
#  * FAITHFULNESS. This dict is the sole upstream of data/electrolytes.csv, and all three are
#    still rows of that CSV. With them pruned, running this script DELETED three shipped rows,
#    i.e. the generator did not reproduce its own output. A generator that silently prunes its
#    artifact is a worse defect than a retracted number sitting inertly in a dict.
#  * VERIFIABILITY OF THE RETRACTION. The Table S4 caption retracts these three by name AND
#    quotes their values (3.5, 2.0, 200). If the CSV rows disappear, that by-name retraction
#    becomes uncheckable against the data -- a reader cannot confirm what was withdrawn.
#    The retraction record is only useful while the withdrawn row is still visible.
# The prune's stated worry -- that shipping the keys lets someone regenerate a retracted
# conductivity -- is not answered by deletion, because the CSV ships those same three numbers
# regardless. It is answered by CLASSIFICATION, which is already in place: all three emit with
# status `unused-legacy (no registry row)`, computed (not typed) from the `electrolyte` column
# of reactions_50.csv, where each is used by 0 of 50 rows. Nothing consumes them, none carries a
# registry row in parameters_provenance.csv, and none reaches SI Table S7f. Restoring the keys
# changes NO value, state or status in electrolytes.csv -- the CSV is byte-for-byte unchanged;
# only the generator's ability to reproduce it changes.
#
# TWO KEYS WERE KEPT THAT LOOK LIKE THEY BELONG ON THAT LIST. Both deliberately.
#  * "0.1 M Bu4NPF6/THF" is retracted by §S6.1 at kappa = 0.6, but the value here is no
#    longer 0.6: it is now 0.51, MEASURED (Zhang, Gu, Wang, Ware, Lu, Lin, Qi & See,
#    JACS Au 2023, 3(8), 2280-2290, Table 1, TBAPF6 0.1 M in THF, 506.3 uS/cm at
#    22 +/- 1 C; docs/KAPPA_SOURCING_DOSSIER.md item P11). What §S6.1 retracts is the
#    number and its use in the thermal figures, not the existence of the electrolyte.
#    Deleting the key would delete the only state-A conductivity in the registry the
#    next time this script runs, so the key is kept and the value synced to the
#    registry instead. The row remains `unused-legacy`; nothing consumes it.
#  * "0.1 M Bu4NBF4/MeCN" is the actually-reported electrolyte of the Ritter-type
#    C(sp3)-H amination exemplar (Zhang/Ye, Nat. Commun. 2022), data row 10 of
#    reactions_50.csv, and is `registered`. Deleting it would falsify a reported
#    experimental condition.
#
# RECONCILED 2026-08-02 (second pass). This dict is the upstream of data/electrolytes.csv
# (emitted near the bottom of this file). It had drifted out of agreement with that CSV after the
# kappa sourcing pass hand-edited the CSV: nine values were stale here, the `LiBr/THF` stub had
# been deleted there but not here, and the emitter hardcoded state="assumption", so a regeneration
# would have flattened nine `derived` rows and one `measured` row back to `assumption` and
# resurrected the stub. All four defects are now closed -- the nine values are synced, the stub is
# gone, and the state column is a per-row lookup (ELECTROLYTE_STATE, below).
#
# NO DIVERGENCE REMAINS. With the three retracted keys restored, this dict holds 66 entries and
# data/electrolytes.csv holds 66 data rows (67 lines, the first being the header -- an earlier
# version of this comment quoted the line count as if it were the row count). All 66 reproduce
# byte-for-byte in name, value, state and status, in the same order. The dict is therefore the
# faithful upstream of the CSV, and `python build_reactions50.py` is a no-op on that file.
# CHECKED 2026-08-02 without touching any artifact: the two dicts were parsed out of this file with
# ast.literal_eval, the `status` set was rebuilt from the `electrolyte` column of reactions_50.csv,
# the emitter below was re-run in isolation (no rdkit, no pandas) and its output compared with the
# shipped data/electrolytes.csv -- byte-identical, and equal field by field in order, kappa, state
# and status across all 66 rows. Census unchanged: 49 registered (9 derived, 40 assumption, 0
# measured) and 17 unused-legacy, the single measured row being one of the 17.
ELECTROLYTES = {
    ## --- 2026-08-22, the two multicomponent-coupling rows. Both are state C. ---
    ## 0.077 M Et4NBF4/MeCN: DERIVED 2026-08-22 by same-family transfer, replacing the 8.1 lower
    ## bound this row carried. Dorn Table 3 p. 1499 was retrieved and DOES carry the
    ## ACN/(C2H5)4NBF4 Casteel-Amis fit (m_max 4.00409, kappa_max 60.97, a 0.84952, b -0.02650),
    ## but evaluating it at this concentration is NOT defensible: it returns 4.03 mS cm-1, i.e.
    ## Lambda/Lambda0 = 0.269, against 0.615 for Bu4NBF4 at the SAME molality in the SAME solvent.
    ## Two homologous tetraalkylammonium tetrafluoroborates cannot differ that way; the fit is
    ## anchored at m_max = 4.0 mol/kg and does not reach 0.077 M. What IS defensible is the
    ## transfer at equal Lambda/Lambda0 -- same solvent, same anion, same concentration, homologous
    ## cation -- which needs only the two limiting conductances. Kalugin 2019 Table 3 p. 28, a
    ## source THIS PROJECT ALREADY CITED on another row, carries all three: Et4N+ 86.34,
    ## BF4- 109.20, Bu4N+ 61.90. Their sum Lambda0(Bu4NBF4/MeCN) = 171.10 reproduces to 0.00% the
    ## 171.1 carried independently as measured -- the check on the route -- and
    ## Lambda0(Et4NBF4) = 195.54, so kappa = 8.1 x 195.54/171.10 = 9.26 mS cm-1. Krumgalz 1983
    ## (Walden products, Table 2 p. 577, over his own viscosity, Table 3 p. 578) gives 84.9 and
    ## 61.6 independently, i.e. 9.20 mS cm-1 -- the two tabulations agree to 0.6%.
    "0.077 M Et4NBF4/MeCN": 9.26,
    ## 0.1 M Bu4NPF6/MeCN: carried at the DERIVED 0.1 M Bu4NBF4/MeCN value (9.9); the assumption is
    ## the anion swap. PF6- is the LESS conductive anion of the pair (Gong Table 2 p. 3518: PF6-
    ## 102.8), so 9.9 is a mild OVER-estimate and this row's thermal ceiling is correspondingly
    ## optimistic. No measured kappa for Bu4NPF6/MeCN at any concentration was located.
    "0.1 M Bu4NPF6/MeCN": 9.9,
    "0.1 M Bu4NBF4/MeCN": 9.93,
    "0.1 M Bu4NBF4/DMF": 4.76,   ## RETRACTED §S6.1 + Table S4 caption; unused-legacy, kept so
                                  ## the CSV row the caption retracts by name stays inspectable
    "0.1 M Bu4NPF6/THF": 0.51,   # 0.51: measured, see above
    "1 M LiBF4/THF":       5.0,   "0.5 M NaOMe/MeOH":  15.0, "0.1 M Bu4NBF4/HFIP": 2.5,
    "1 M KOH aq":        200.0,   ## RETRACTED §S6.1 + Table S4 caption; unused-legacy (see above)
    "0.5 M H2SO4 aq":    200.0,   "phosphate buffer aq": 15.0,
    "1 M NaBr aq":        80.0,   "0.2 M Et4NOTs/MeOH": 8.0, "Et3N.3HF/MeCN": 30.0,
    "0.1 M LiClO4/MeCN":  10.0,   "emulsion + Na2HPO4/TAEP": 50.0,
    "neat carboxylate/MeOH": 30.0,
    "0.2 M nBu4NBr/DMA": 6.0,      "0.21 M TBAB/DMSO-THF": 4.0,  "0.48 M LiBr/DMA": 12.0,
    "0.2 M NaI/DMF": 8.77,
    ## Row 13's NaI is 0.6 mmol in the PHYSICAL volume 3.5 mL (3.0 mL DMF + 0.5 mL DCM retained
    ## from the activation step -- Fig 2a says "No solvent exchange"), = 0.171 M. The paper's own
    ## "NaI (0.2 M)" is computed on the DMF alone. The row used to take the substrate on 3.5 mL and
    ## the electrolyte on 3.0 mL -- two bases in one row. Scaled linearly from the 0.2 M entry.
    "0.171 M NaI/DMF": 7.50,          "0.24 M Et3NHBF4/THF-HFIP": 5.0, "0.1 M TBABF4/acetone": 8.0,
    "0.033 M Et4NPF6/MeOH": 3.0,   "1 M LiClO4/MeNO2": 12.0,     "0.25 M KOAc/tAmOH-H2O": 8.0,
    "2 M H2SO4 aq": 700.0,         "1 M carbonate buffer pH 8.5 aq": 60.0, "0.5 M borate buffer pH 10 aq": 25.0,
    "1 M NaOH aq": 174.5,          "1 M Na2CO3 aq": 80.0,        "1 M KHCO3 aq": 76.0,
    "1 M Et4NF.4HF/MeCN": 60.0,    "0.1 M HBF4/MeCN": 15.0,      "0.1 M LiClO4/AcOH-HCOOH": 3.0,
    "0.0625 M LiClO4/MeOH": 4.0,
    ## ---------------------------------------------------------------------------------
    ## Added 2026-08-23 by the condition audit, which changed five electrolyte strings.
    ## NONE of these is a measured value. Each is DERIVED from an anchor already in this
    ## table, and the derivation is written out so it can be attacked. They are listed in
    ## KAPPA_ESTIMATED below and the build prints them as a banner on every run -- they must
    ## not be read as page-anchored numbers, and each needs a row in KAPPA_SOURCING_DOSSIER.md.
    "0.033 M Et4NPF6/THF-MeOH 5:1": 0.35,
    "0.04 M NaBr/EtOH-MeOH 1:1":    1.8,
    "1 M KCl aq":                   111.6,
    "0.152 M NaBr/H2O-MeCN-MeOH-DCM 10:10:10:3": 19.0,
    "0.0625 M TsOH/MeOH":           7.5,
    # "LiBr/THF": 3.0 -- DELETED 2026-08-02 (dossier P10). Concentration-free stub, a duplicate
    # of the real "3.0 M LiBr/THF" key below; `unused-legacy`, consumed by nothing. Deleted from
    # data/electrolytes.csv in the same pass; keeping it here would resurrect it on regeneration.
    "Me4N carboxylate (10 mol%)/acetone": 2.0,   ## RETRACTED Table S4 caption; unused-legacy
                                                 ## (see the RETRACTION note at the top of this dict)
    "0.3 M LiClO4/MeCN": 20.0,     "0.1 M Et4NClO4/DMF": 4.0,    "0.2 M NaClO4/MeCN": 12.0,
    "0.091 M MTES/HFIP-MeOH": 2.0, "0.01 M Bu4NPF6/HFIP": 0.3,   "0.085 M Et4NPF6/MeCN-HCl aq": 8.0,
    "0.08 M NaBr/MeCN": 4.0,       "0.5 M NaBr aq/MeCN 1:1": 40.0, "Et3N 7.5 mM (no salt)/MeOH": 0.5,
    "0.1 M TBAP/MeCN-H2O": 10.0,   "5 wt% AcOH/MeOH-H2O": 10.0,  "Me4NBF4/MeOH": 6.0,
    "0.1 M LiClO4/acetone": 8.0,   "56 wt% Et4NOTs aq": 80.0,
    ## verified-conditions pass (Jul 2026): keys matching the extracted exemplar electrolytes
    "0.156 M Et4NOTs/MeOH": 7.0,   "0.3 M Bu4NBF4/MeCN": 22.50,   "0.04 M NaBr/MeCN": 1.5,
    "0.033 M Et4NPF6/MeCN": 3.5,   "0.077 M Bu4NBF4/MeCN": 8.26,  "0.043 M Bu4NBF4/MeCN": 5.66,
    "0.25 M Bu4NBF4/MeCN": 19.95,   "0.04 M NaBr/MeOH": 2.5,      "2 M NaCl aq": 148.9,
    "no added salt (25 um flow gap)/MeCN": 0.5,  "pH 2 HCl (salt in ESI)/H2O-MeCN": 5.0,
    "3.0 M LiBr/THF": 3.0,   # Peters 2019 SM scale-up electrolyte (ion-paired; battery-like)
    "0.3 wt% H2SO4/MeOH (BASF)": 3.0,   # patent electrolyte, US 5,507,922 Ex. 1; lambda0-est
    ## SI-verification pass (Jul 2026, second batch)
    ## Renamed 2026-08-23 to state the molarities rather than mol% of an unstated basis. Same
    ## experiment, same value: the 200-mmol 10-undecenoic acid run has Me4NOH 30 mmol/200 mL =
    ## 0.15 M and Me4NBF4 10 mmol/200 mL = 0.05 M, so "15 mol% / 5 mol%" and "0.15 M / 0.05 M"
    ## are the same numbers -- the mol% form just hid which basis it was mol% OF.
    "0.15 M Me4NOH + 0.05 M Me4NBF4/acetone": 6.0,      # Hioki 200-mmol run (SI p 9)
    "0.48 M Bu4N carboxylate (in situ)/MeCN": 15.0,     # Mo/Jensen GP A (SI p 19)
    "NaCl 7 mol% + pH 2 HCl/H2O-MeCN": 1.2,             # Li/Wilden ESI p S5 (~12 mM ionics)
    "0.08 M Me4NBF4/MeOH": 5.0,  "0.0833 M Me4NBF4/MeOH": 5.21,                          # Kawamata rAP GP (SI p 14)
}

# ------------------------------------------- provenance STATE per electrolyte (three-state
# standard, docs/PROVENANCE_STANDARD.md). The emitter below used to hardcode state="assumption"
# for every row of electrolytes.csv, which made the ten promotions of the 2026-08-02 sourcing pass
# UNREACHABLE from this script: regenerating flattened nine `derived` rows and the single
# `measured` row back to `assumption` while leaving their (correct) values in place, i.e. it broke
# the value/class pairing that electrolytes.csv exists to keep together. The class is now a per-row
# lookup. DEFAULT IS "assumption" -- only the keys below reach state B or state A, and the
# assertion underneath fails loudly if a key here is not a real electrolyte.
#
# Every entry is docs/KAPPA_SOURCING_DOSSIER.md Section 2.1 (items P1-P9, P11); the full citation
# strings live with the registry rows in build_param_tables.py (ECOND_PROV), not here.
ELECTROLYTE_STATE = {
    # -- state B, DERIVED. Five Casteel-Amis evaluations of the measured kappa(c) isotherm fit for
    #    Bu4NBF4/MeCN (Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502,
    #    Table 3, p. 1499: kappa_max 33.40 mS/cm, m_max 1.48127, a 0.78646, b -0.02156).
    # -- state A, MEASURED. The Dorn SUPPORTING INFORMATION (je3c00691_si_001.pdf, now in
    #    papers for model/) carries the raw isotherms, not just the four fits of the article body:
    #    Table SI 85, p. 171 is Bu4NBF4 in acetonitrile at 298.15 K, 21 measured points. Every
    #    concentration below is read between two of them. The one exception is 0.043 M, whose
    #    bracket (m = 0 to 0.0905) is too wide for linear interpolation because kappa(m) is
    #    strongly curved there; it uses the Casteel-Amis fit instead, which data/casteel_amis.py
    #    validates against Dorn's own kappa_calc column to 0.088 pct on this very isotherm.
    "0.043 M Bu4NBF4/MeCN": "derived",   # m = 0.056, CA fit 5.66 (was a typed 5.2)
    "0.077 M Bu4NBF4/MeCN": "measured",  # m = 0.101, between (0.0905, 7.66) and (0.1896, 13.36)
    # -- state A, MEASURED. Shinkle, Pomaville, Sleightholme, Thompson & Monroe, J. Power Sources
    #    2014, 248, 1299-1305, Table 1: conductivity of each 0.1 M supporting-electrolyte/solvent
    #    combination at room temperature, in mS cm-1. TBABF4: ACN 9.93, DMF 4.76.
    "0.1 M Bu4NBF4/MeCN":   "measured",  # was derived 9.9 by Casteel-Amis; measured 9.93 (-0.3%)
    "0.1 M Bu4NBF4/DMF":    "measured",  # was an unsourced 3.5; measured 4.76 (the 3.5 was -26%)
    "0.25 M Bu4NBF4/MeCN":  "measured",  # m = 0.347, between (0.2960, 18.16) and (0.4094, 22.13)
    "0.3 M Bu4NBF4/MeCN":   "measured",  # m = 0.423, between (0.4094, 22.13) and (0.5312, 25.48)
    # -- state B, DERIVED. Same-family transfer at equal Lambda/Lambda0 onto the row above,
    #    using the two limiting conductances from Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983,
    #    79, 571-587 (Table 2 p. 577 Walden products / Table 3 p. 578 viscosity). Evaluating
    #    Dorn's OWN Et4NBF4 fit here is not defensible -- see the note at the value below.
    "0.077 M Et4NBF4/MeCN": "derived",   # 8.1 x 194.4/171.1 = 9.20
    # -- state B, DERIVED. Four CRC derivations for the concentrated aqueous rows: c <-> mass %
    #    from "Concentrative Properties of Aqueous Solutions", kappa(mass %) from "Electrical
    #    Conductivity of Aqueous Solutions", p. 5-71 (20 C), then a 20 -> 25 C correction.
    # -- state B, DERIVED 2026-08-22. The attenuation Lambda/Lambda0 at 0.2 M is transferred from
    #    Dorn's MEASURED NaI-in-methanol isotherm (Table SI 97, p. 197) at the same concentration,
    #    0.539, onto the page-anchored Lambda0(NaI, DMF) = 81.92 from Gopal & Jha. It replaces an
    #    unsourced 8.0 that had no derivation at all. Conservative: DMF's higher permittivity
    #    means it pairs less, so 0.539 is a floor on its attenuation and 8.83 a floor on kappa.
    "0.2 M NaI/DMF": "derived",
    # -- state A, MEASURED, from the same Supporting Information. The CRC p. 5-71 derivations
    #    these rows used to carry are RETAINED IN THE REGISTRY as the cross-check, and they were
    #    good: 178 vs 174.5, 148 vs 148.9, 75.5 vs 76.0 -- 2.0, 0.6 and 0.6 per cent.
    "1 M NaOH aq":   "measured",         # Table SI 16, p. 61; m = 0.9984
    "2 M NaCl aq":   "measured",         # Table SI 13, p. 54; m = 2.0816 (a measured point at 2.0714)
    "1 M KHCO3 aq":  "measured",         # Table SI 31, p. 94; m = 1.0405
    "1 M Na2CO3 aq": "derived",          # P9, band 79-81
    # -- state A, MEASURED. The only measured conductivity anywhere in this work.
    "0.1 M Bu4NPF6/THF": "measured",     # P11, Zhang, Gu, Wang, Ware, Lu, Lin, Qi & See, JACS Au
                                         # 2023, 3(8), 2280-2290, Table 1: 506.3 uS/cm, 22 +/- 1 C.
                                         # Row is `unused-legacy`; a provenance win, not a numerical one.
}
## Conductivities that are ESTIMATES, with the derivation that produced each one. Kept separate
## from ELECTROLYTE_STATE (whose values are only "measured"/"derived") so that nothing can mistake
## an estimate for a sourced number, and printed as a banner by main().
KAPPA_ESTIMATED = {
    "0.033 M Et4NPF6/THF-MeOH 5:1":
        "Bracketed by two entries in this table: 0.1 M Bu4NPF6/THF = 0.5063 mS/cm (MEASURED, P11) "
        "scaled to 0.033 M gives ~0.13 in pure THF; 0.033 M Et4NPF6/MeOH = 3.0 is the MeOH end. "
        "Mole-fraction log-mix at x(THF)=0.714 -> 0.32. Carried as 0.35. The bracket [0.13, 3.0] "
        "is wide -- this row's kappa is the weakest in the table.",
    "0.04 M NaBr/EtOH-MeOH 1:1":
        "Walden (Lambda ~ 1/eta) from 0.04 M NaBr/MeOH = 2.5 in this table: 2.5 * 0.544/0.719 "
        "= 1.89, rounded down to 1.8 for the extra ion pairing at EtOH's lower permittivity.",
    "1 M KCl aq":
        "NO LONGER AN ESTIMATE -- traced to a PRIMARY STANDARD on 2026-08-24. CRC Handbook 97th "
        "ed. 2016, 'Standard KCl Solutions for Calibrating Conductivity Cells', p. 5-72 (read from "
        "a 300-dpi page image): NIST measurements, ITS-90, stated uncertainty 0.04% for the 1.0 "
        "molal column, primary refs Wu, Koch & Pratt J. Res. NIST 96, 191 (1991) and Wu et al. "
        "ibid. 99, 241 (1994). At 25 C the table gives 10^4*kappa(1.0 mol/kg) = 108620 S/m, i.e. "
        "kappa = 108.62 mS/cm. "
        "THAT IS MOLAL, NOT MOLAR, and the row needs molar. 1.0 mol/kg is 74.5513 g KCl in 1000 g "
        "water = 1074.55 g of solution; at rho = 1.0455 g/cm3 that is 1.0278 L, so 1.0 molal = "
        "0.9730 M. Lambda = kappa/c = 111.64 S cm2/mol, and taking Lambda flat over the 2.7% "
        "extrapolation to 1.000 M gives kappa = 111.6 mS/cm. "
        "REMAINING STATE-B STEP: the density 1.0455 g/cm3 for 1 molal KCl at 25 C is not itself "
        "page-anchored here, and the flat-Lambda extrapolation adds a little more. Both affect the "
        "answer at the sub-percent level -- the previous unsourced estimate of 111.3 sits 0.30% "
        "from this -- and neither can matter, because kappa never enters the transport solvers "
        "(see the note on KAPPA_ESTIMATED). It is recorded so the chain is visible, not because "
        "the number is delicate.",
    "0.152 M NaBr/H2O-MeCN-MeOH-DCM 10:10:10:3":
        "From the entry this row replaced, 0.5 M NaBr aq/MeCN 1:1 = 40.0 at 0.25 M effective Br-. "
        "Linear in concentration: 40.0 * 0.152/0.25 = 24.3; times ~0.8 because MeOH and DCM "
        "replace part of the aqueous/MeCN medium. Carried as 19.0.",
    "0.0833 M Me4NBF4/MeOH":
        "Linear-in-concentration scaling of 0.08 M Me4NBF4/MeOH = 5.00 in this table: "
        "5.00 * 0.0833/0.08 = 5.21. The SI gives Me4N.BF4 40 mg = 0.25 mmol in 3.0 mL MeOH "
        "= 0.0833 M (2.5 equiv to the 0.1 mmol substrate), not the 0.08 M / 2 equiv the row "
        "previously carried.",
    "0.171 M NaI/DMF":
        "Linear-in-concentration scaling of the DERIVED 0.2 M NaI/DMF = 8.77 in this table: "
        "8.77 * 0.171/0.2 = 7.50. Inherits that entry's derivation (Dorn's measured NaI-in-methanol "
        "attenuation transferred onto Gopal & Jha's Lambda0(NaI, DMF)), so it is a derived value "
        "scaled from a derived value -- weaker than either, and flagged accordingly.",
    "0.0625 M TsOH/MeOH":
        "TsOH is a STRONG acid in MeOH, so this is not a like-for-like swap for the 0.0625 M "
        "LiClO4 = 4.0 it replaces. Lambda0(HCl/MeOH) ~ 192 S cm2/mol; TsO- is bulkier, ~160; at "
        "0.0625 M take attenuation ~0.75 -> Lambda ~ 120 -> kappa = 120 * 0.0625e-3 S/cm = 7.5. "
        "Nearly 2x the LiClO4 value -- the physically meaningful consequence of the correction.",
}
assert set(KAPPA_ESTIMATED) <= set(ELECTROLYTES), "KAPPA_ESTIMATED names an unknown electrolyte"

assert set(ELECTROLYTE_STATE) <= set(ELECTROLYTES), (
    "ELECTROLYTE_STATE names an electrolyte that is not in ELECTROLYTES: "
    + str(sorted(set(ELECTROLYTE_STATE) - set(ELECTROLYTES))))
assert set(ELECTROLYTE_STATE.values()) <= {"measured", "derived"}, "state must be measured/derived"

def _kappa(elec):
    if elec not in ELECTROLYTES:
        raise SystemExit(
            "ELECTROLYTES has no conductivity for %r.\n"
            "A row's electrolyte string was changed without adding its kappa. Add the entry (and, "
            "if it is not measured or derived from a sourced anchor, a KAPPA_ESTIMATED rationale) "
            "rather than letting the row carry NaN." % elec)
    return ELECTROLYTES[elec]


# ------------------------------------------------- Le Bas additive volumes (Poling 5th ed.)
LEBAS = {"C":14.8,"H":3.7,"O":7.4,"O_acid":12.0,"N":15.6,"N_prim":10.5,"N_sec":12.0,
         "S":25.6,"F":8.7,"Cl":24.6,"Br":27.0,"I":37.0,"P":27.0,
         "ring6":-15.0,"ring5":-11.5,"ring4":-8.5,"ring3":-6.0}

def lebas_volume(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None: raise ValueError(f"bad SMILES {smiles}")
    m = Chem.AddHs(m)
    V = 0.0
    acid_O = set()
    for pat in [Chem.MolFromSmarts("C(=O)[OX2H1]")]:          # carboxylic acid: ONLY the
        for match in m.GetSubstructMatches(pat):              # hydroxyl O takes the acid
            for a in match:                                   # increment (12.0); the
                at = m.GetAtomWithIdx(a)                      # carbonyl O stays at 7.4
                if at.GetSymbol()=="O" and any(nb.GetSymbol()=="H" for nb in at.GetNeighbors()):
                    acid_O.add(a)
    for a in m.GetAtoms():
        s = a.GetSymbol()
        if s == "O":
            V += LEBAS["O_acid"] if a.GetIdx() in acid_O else LEBAS["O"]
        elif s == "N":
            nH = sum(1 for nb in a.GetNeighbors() if nb.GetSymbol()=="H")
            V += LEBAS["N_prim"] if nH>=2 else (LEBAS["N_sec"] if nH==1 else LEBAS["N"])
        elif s in LEBAS:
            V += LEBAS[s]
        else:
            V += 20.0   # fallback for exotic atoms; flagged
    ri = m.GetRingInfo()
    # Le Bas applies ONE ring correction per independent ring. RDKit's AtomRings() returns the
    # symmetrized ring set, which over-counts fused/bridged systems: 1,3-dimethyladamantane gets
    # 4 rings where the cyclomatic number (bonds - atoms + 1) is 3, over-subtracting 15 cm3/mol
    # and inflating D by 4.4%. Take the smallest `n_indep` rings so the count is right and the
    # sizes are the SSSR ones.
    n_indep = m.GetNumBonds() - m.GetNumAtoms() + 1   # H-invariant: each H adds 1 atom + 1 bond
    for ring in sorted(ri.AtomRings(), key=len)[:max(0, n_indep)]:
        n = len(ring)
        V += LEBAS.get(f"ring{min(n,6)}", -15.0) if n>=3 else 0.0
    return V

def wilke_chang(smiles, solvent):
    Msol, mu, rho, phi, _ = SOLVENTS[solvent]
    V = lebas_volume(smiles)
    D = 7.4e-8 * np.sqrt(phi*Msol) * T / (mu * V**0.6)        # cm^2/s (mu in cP)
    return D, V

def stokes_einstein(r_angstrom, solvent):
    mu = SOLVENTS[solvent][1] * 1e-3                          # Pa.s
    D = kB*T/(6*np.pi*mu*r_angstrom*1e-10) * 1e4              # cm^2/s
    return D

# Small inorganic ions: Wilke-Chang is invalid; use Nernst-Einstein D from limiting
# molar conductivities (CRC / Izutsu "Electrochemistry in Nonaqueous Solutions").
# D = lambda0*R*T/(z^2 F^2). Values in cm^2/s, 25 C. Provenance: NE(lambda0).
ION_D = {  # (species SMILES, solvent-class) -> D
    ("[Br-]","H2O"): 2.08e-5, ("[Br-]","MeOH"): 1.5e-5, ("[Br-]","MeCN"): 2.7e-5,
    ("[Cl-]","H2O"): 2.03e-5, ("[Cl-]","MeOH"): 1.4e-5, ("[Cl-]","MeCN"): 2.3e-5,
    ("[S-]C#N","H2O"): 1.76e-5, ("[S-]C#N","MeCN"): 2.9e-5, ("[S-]C#N","AcOH"): 7.8e-6,
    ("[O-]C([O-])=O","H2O"): 9.2e-6,   # CO3^2-: lambda0 = 138.6 S cm2/mol, z=2 (CRC)
}
def ion_override(smiles, solvent):
    base = solvent.split("/")[0]
    ov = ION_D.get((smiles, base)) or ION_D.get((smiles, solvent))
    ## guard: a bare small ion must NEVER fall through to Wilke-Chang (Le Bas
    ## volumes are meaningless for it) — fail loudly instead of silently.
    if ov is None and smiles.startswith("[") and len(smiles) <= 10:
        raise ValueError(f"no Nernst-Einstein D tabulated for ion {smiles} in {solvent}")
    return ov

# =====================================================================================
# THE 50 REACTIONS.
# carrier: 'substrate' | 'mediator' | 'catalyst'
# n_c = electrons delivered per carrier round-trip at the electrode
# C_carrier in mol/L. For carrier='substrate', C_carrier = C_substrate.
# cond tag = provenance of concentration ("rep. of <exemplar conditions>").
# D_method: WC = Wilke-Chang(SMILES), SE:r = Stokes-Einstein radius Angstrom
# =====================================================================================
R = []  # (cls, name, exemplar, carrier, carrier_species, D_method, smiles_or_r, C_carrier, n_c, C_substrate, n_substrate, solvent, electrolyte)

# ---- C-N formation (11) ----
## conditions: PAGE-VERIFIED against the primary PDFs (papers-for-model corpus, Jul 2026)
R += [
 ("C-N formation","Ni-catalyzed aryl amination (ArBr + amine)","Kawamata/Baran JACS 2019","catalyst","Ni(bpy) complex","SE",4.5, 0.005, 2, 0.05, 2, "DMA","0.2 M nBu4NBr/DMA"),
 ("C-N formation","Electrochemical amination of ArX with NH3","Liu/Qiu Angew 2025","catalyst","Ni(bpy) complex","SE",4.5, 0.0052, 2, 0.104, 2, "DMSO/THF","0.21 M TBAB/DMSO-THF"),
 ("C-O formation","Shono oxidation (N-acyliminium capture)","Shono JACS 1975; Deprez/Merck OL 2021","substrate","N-Boc-pyrrolidine","WC","O=C(OC(C)(C)C)N1CCCC1", 1.56, 2, 1.56, 2, "MeOH","0.156 M Et4NOTs/MeOH"),
 ("Cyclization","Oxidative benzimidazole annulation (C-H/N-H)","Zhao/H.-C. Xu ChemSusChem 2021","substrate","N-aryl amidine","WC","CC(=Nc1ccccc1)Nc1ccccc1", 0.033, 2, 0.033, 2, "THF/MeOH","0.033 M Et4NPF6/THF-MeOH 5:1"),
 ("C-N formation","Mn-catalyzed alkene diazidation","Fu/Lin Science 2017","catalyst","Mn(azide) complex","SE",4.0, 0.0026, 1, 0.051, 2, "MeCN","0.1 M LiClO4/MeCN"),
 ("Functional group intraconversion","Br-mediated Hofmann rearrangement","Malviya/Cantillo OPRD 2023 (multigram)","mediator","bromide","WC","[Br-]", 0.08, 1, 0.40, 2, "MeCN","0.08 M NaBr/MeCN"),
 ("C-N formation","Arene C-H pyridination","Morofuji/Yoshida JACS 2013","substrate","anisole","WC","COc1ccccc1", 0.02, 2, 0.02, 2, "MeCN","0.3 M Bu4NBF4/MeCN"),
 ("Cyclization","Amidyl-radical C-H amination (phenanthridinone)","Zhang/K. Xu/Zeng OL 2018","substrate","biaryl amide","WC","O=C(Nc1ccccc1-c1ccccc1)C", 0.04, 2, 0.04, 2, "MeCN","0.04 M NaBr/MeCN"),
 ("Cyclization","Co-catalyzed aza-Wacker cyclization","Cai/H.-C. Xu Nat Commun 2021 (Co-salen)","catalyst","Co(salen)","SE",5.0, 0.0033, 1, 0.033, 2, "MeCN","0.033 M Et4NPF6/MeCN"),
 ("C-N formation","Ritter-type C(sp3)-H amination","Zhang/Ye Nat Commun 2022","substrate","1,3-dimethyladamantane","WC","CC12CC3CC(CC(C3)C1)(C2)C", 0.167, 2, 0.167, 2, "MeCN","0.1 M Bu4NBF4/MeCN"),
 ("C-N formation","Co-H alkene reduction (e-HAT)","Gnaim/Baran Nature 2022 (e-HAT)","catalyst","CoBr2(glyme)/bpy","SE",5.0, 0.008, 1, 0.08, 2, "THF","0.24 M Et3NHBF4/THF-HFIP"),
]
# ---- C-C coupling (11) ----
R += [
 ("C-C formation","Kolbe homocoupling of 10-undecenoate","Hioki/Baran Science 2023 (rAP; acetone)","substrate","10-undecenoate anion","WC","C=CCCCCCCCCC(=O)[O-]", 1.00, 1, 1.00, 1, "acetone","0.15 M Me4NOH + 0.05 M Me4NBF4/acetone"),
 ("C-C formation","Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)","Kelly/Stahl/Schreier OPRD 2026 (kg, flow, BMS)","catalyst","Ni(dtbbpy) complex","SE",4.5, 0.015, 2, 0.30, 2, "DMA","0.48 M LiBr/DMA"),
 ("C-C formation","Doubly decarboxylative Csp3-Csp3","Zhang/Baran Nature 2022","substrate","N-Cbz-proline (limiting monoacid, via RAE)","WC","O=C(O)C1CCCN1C(=O)OCc1ccccc1", 0.029, 1, 0.029, 1, "DMF","0.171 M NaI/DMF"),
 ("C-C formation","BDD phenol-arene cross-coupling","Kirste/Waldvogel JACS 2012","substrate","4-methylguaiacol","WC","Cc1ccc(O)c(OC)c1", 0.15, 2, 0.15, 2, "HFIP","0.091 M MTES/HFIP-MeOH"),
 ("C-C formation","Decarboxylative Minisci alkylation","Mo/Jensen Science 2020","substrate","1,4-dicyanobenzene (limiting)","WC","N#Cc1ccc(C#N)cc1", 0.08, 1, 0.08, 1, "MeCN","0.48 M Bu4N carboxylate (in situ)/MeCN"),
 ("C-C formation","Cathodic Giese (R-I + alkene)","Li/Wilden Chem Sci 2020","substrate","2-iodopropane (electroactive)","WC","CC(C)I", 0.095, 1, 0.079, 1, "H2O/MeCN","NaCl 7 mol% + pH 2 HCl/H2O-MeCN"),
 ("C-C formation","Rh-catalyzed electrooxidative C-H alkenylation","Qiu/Ackermann Angew 2018","catalyst","[Cp*RhCl2]2 complex","SE",4.5, 0.0031, 2, 0.125, 2, "tAmOH/H2O","0.25 M KOAc/tAmOH-H2O"),
 ("C-C formation","Cu-catalyzed benzylic cyanation","Cai/H.-C. Xu Nat Catal 2022 (PEC)","catalyst","Cu(acac)2/BOX complex","SE",4.0, 0.0038, 1, 0.038, 2, "MeCN","0.077 M Bu4NBF4/MeCN"),
 ("C-C formation","Cathodic Ni aryl-aryl homocoupling","Courtois/Perichon Tetrahedron 1997","catalyst","Ni(bpy) complex","SE",4.5, 0.030, 2, 0.30, 2, "EtOH/MeOH","0.04 M NaBr/EtOH-MeOH 1:1"),
 ("C-C formation","Anodic dehydrogenative 2-naphthol coupling","Osa/Bobbitt Chem Commun 1994","substrate","2-naphthol","WC","Oc1ccc2ccccc2c1", 1.00, 1, 1.00, 1, "MeCN","0.2 M NaClO4/MeCN"),
 ("C-C formation","Acrylonitrile hydrodimerization (ADN)","Baizer JES 1964 (Monsanto)","substrate","acrylonitrile","WC","C=CC#N", 6.85, 1, 6.85, 1, "H2O","56 wt% Et4NOTs aq"),
]
# ---- Reduction (6) ----
R += [
 ("Reduction","Birch reduction of naphthalene","Peters/Baran Science 2019","substrate","naphthalene (repr.; scale-up runs TBS-cresol)","WC","c1ccc2ccccc2c1", 0.141, 2, 0.141, 2, "THF","3.0 M LiBr/THF"),
 ("Reduction","Nitroarene -> aniline","Kisukuri/Waldvogel OPRD 2024","substrate","3-nitrobenzotrifluoride","WC","O=[N+]([O-])c1cccc(c1)C(F)(F)F", 0.40, 6, 0.40, 6, "MeOH/H2O","2 M H2SO4 aq"),
 ("Reduction","Rapid-alternating-polarity imide reduction","Hayashi/Baran JACS 2022 (rAP)","substrate","N-methylphthalimide","WC","O=C1c2ccccc2C(=O)N1C", 0.0333, 4, 0.0333, 4, "MeOH","0.0833 M Me4NBF4/MeOH"),
 ("Multicomponent coupling","Diazo difunctionalization (thiol + alcohol)","Yang/Lei Nat Commun 2023 (diazo difunctionalization)","substrate","thiophenol (anodic)","WC","Sc1ccccc1", 0.077, 2, 0.077, 2, "MeCN","0.077 M Et4NBF4/MeCN"),
 ("Functional group intraconversion","Cathodic aryl chloride dehalogenation","Ke/Chi Chem Eur J 2019","substrate","4-chloroanisole","WC","COc1ccc(Cl)cc1", 0.043, 2, 0.043, 2, "MeCN","0.043 M Bu4NBF4/MeCN"),
 ("Reduction","Benzaldehyde -> benzyl alcohol","Lopez-Ruiz ACS SCE 2018 (ECH)","substrate","benzaldehyde","WC","O=Cc1ccccc1", 0.02, 2, 0.02, 2, "MeOH/H2O","5 wt% AcOH/MeOH-H2O"),
]
# ---- C-O formation (5) ----
R += [
 ("Oxidation","ACT-mediated alcohol oxidation (flow, hectogram)","Zhong/Stahl OPRD 2021 (levetiracetam)","mediator","ACT (4-AcNH-TEMPO)","WC","CC1(C)CC(NC(C)=O)CC(C)(C)N1[O]", 0.025, 1, 0.50, 2, "H2O","1 M carbonate buffer pH 8.5 aq"),
 ("C-O formation","Anodic methoxylation of 4-tBu-toluene (Lysmeral)","BASF capillary-gap, >10 kt/yr (US 5,507,922)","substrate","4-tBu-toluene","WC","Cc1ccc(cc1)C(C)(C)C", 0.81, 4, 0.81, 4, "MeOH","0.3 wt% H2SO4/MeOH (BASF)"),
 ("C-O formation","Shono alpha-methoxylation of amides","Shono JACS 1975 (carbamate protocol, by analogy)","substrate","DMF-amide substrate","WC","O=C(N(C)C)c1ccccc1", 1.56, 2, 1.56, 2, "MeOH","0.156 M Et4NOTs/MeOH"),
 ("Oxidation","Cl-mediated ethylene epoxidation","Leow/Sargent Science 2020","mediator","chloride","WC","[Cl-]", 1.00, 1, 0.00352, 2, "H2O","1 M KCl aq"),
 ("Unclassified","Alkaline lignin -> vanillin (pilot)","Rücker/Waldvogel ACS SCE 2024 (pilot, ex-cell)","substrate","carbonate (ex-cell oxidizer carrier)","WC","[O-]C([O-])=O", 1.00, 1, 1.00, 1, "H2O","1 M Na2CO3 aq"),
]
# ---- Oxidation FGI (4) ----
R += [
 ("Oxidation","Thioether -> sulfone (kilo-scale)","Bottecchia/Strotman OPRD 2022","substrate","Ar-S-Me thioether","WC","CSc1ccccc1", 0.47, 4, 0.47, 4, "MeCN/H2O","0.085 M Et4NPF6/MeCN-HCl aq"),
 ("Oxidation","NHPI-mediated allylic C-H -> enone","Horn/Baran Nature 2016","mediator","Cl4NHPI","WC","O=C1c2c(Cl)c(Cl)c(Cl)c(Cl)c2C(=O)N1O", 0.033, 1, 0.167, 4, "acetone","0.1 M LiClO4/acetone"),
 ("Multicomponent coupling","Alkenesulfonate from cinnamic acid, SO2 and alcohol","Chien/Manolikakes ChemSusChem 2025","substrate","cinnamate (decarboxylative)","WC","[O-]C(=O)/C=C/c1ccccc1", 0.10, 1, 0.10, 2, "MeCN","0.1 M Bu4NPF6/MeCN"),
 ("Oxidation","HMF -> FDCA (biomass)","Cardiel/Choi ACS SCE 2019","mediator","ACT (4-AcNH-TEMPO)","WC","CC1(C)CC(NC(C)=O)CC(C)(C)N1[O]", 0.040, 1, 0.10, 6, "H2O","0.5 M borate buffer pH 10 aq"),
]
# ---- Other / redox-neutral (4) ----
R += [
 ("Cyclization","Radical-cation Diels-Alder (catalytic in e-)","Okada/Chiba Chem Sci 2016","substrate","trans-anethole","WC","COc1ccc(/C=C/C)cc1", 0.08, 0.1, 0.08, 0.1, "MeNO2","1 M LiClO4/MeNO2"),
 ("C-O formation","BQ-mediated Wacker-Tsuji oxidation","Miller/Wayner Can J Chem 1992","mediator","H2Q (diffusing reduced form of BQ)","WC","Oc1ccc(O)cc1", 0.0235, 2, 0.118, 2, "MeCN/H2O","0.1 M TBAP/MeCN-H2O"),
 ("Functional group intraconversion","Non-Kolbe decarboxylative alpha-methoxylation","Walecka-Kurczyk RSC Adv 2022","substrate","N-Piv-alpha-amino acid","WC","CC(C)(C)C(=O)NC(C)C(=O)O", 0.10, 2, 0.10, 2, "MeOH","Et3N 7.5 mM (no salt)/MeOH"),
 ("Isomerization","Co-H alkene isomerization (catalytic)","Gnaim/Baran Nature 2022 (e-HAT isomerization)","catalyst","Co(salen)","SE",5.0, 0.0048, 0.2, 0.08, 0.2, "acetone","0.1 M TBABF4/acetone"),
]
# ---- C-C cyclization (3) ----
R += [
 ("Cyclization","Anodic oxazoline/oxazole cyclization","Bao OL 2022","substrate","aryl ketone (N(PMP)3-mediated)","WC","CC(=O)c1ccccc1", 0.05, 2, 0.05, 2, "MeCN","0.3 M LiClO4/MeCN"),
 ("Cyclization","Cathodic aryl-halide radical 5-exo cyclization","Ozaki/Ohmori Tet Lett 1994","catalyst","Ni(tet a) complex","SE",4.5, 0.010, 1, 0.05, 1, "DMF","0.1 M Et4NClO4/DMF"),
 ("Cyclization","Dehydrogenative lactonization (C-H/O-H)","Zhang/K. Xu/Zeng OL 2018","substrate","biphenyl-2-carboxylic acid","WC","OC(=O)c1ccccc1-c1ccccc1", 0.0625, 2, 0.0625, 2, "MeCN","0.25 M Bu4NBF4/MeCN"),
]
# ---- Halogenation (2) ----
R += [
 ("Halogenation","Anodic benzylic fluorination","Tajima/Fuchigami Electrochem Commun 2002","substrate","ethylbenzene (benzylic C-H)","WC","CCc1ccccc1", 0.10, 2, 0.10, 2, "MeCN","1 M Et4NF.4HF/MeCN"),
 ("Halogenation","Br- oxidation / electrophilic bromination","Zhang/Su Nat Commun 2025 (scalable arene bromination)","mediator","bromide","WC","[Br-]", 0.152, 1, 0.121, 2, "H2O/MeCN","0.152 M NaBr/H2O-MeCN-MeOH-DCM 10:10:10:3"),
]
# ---- C-S (2) ----
R += [
 ("Multicomponent coupling","Sulfonylation of alkenes with sulfinates","Mei/Han ACS Omega 2019","substrate","Na benzenesulfinate","WC","O=S([O-])c1ccccc1", 0.0625, 1, 0.0625, 1, "MeOH","0.0625 M TsOH/MeOH"),
 ("C-S formation","Aryl thiocyanation (NH4SCN)","Gitkis/Becker Electrochim Acta 2010","mediator","thiocyanate","WC","[S-]C#N", 0.1, 1, 0.25, 2, "AcOH/HCOOH","0.1 M LiClO4/AcOH-HCOOH"),
]
# ---- Other bond (2) ----
R += [
 ("Other bond formation","Anodic C-H phosphonylation of azoles","Long/H.-C. Xu Nat Commun 2021 (flow)","substrate","triethyl phosphite (arene-limited basis)","WC","CCOP(OCC)OCC", 0.05, 2, 0.05, 2, "MeCN","0.1 M HBF4/MeCN"),
 ("Other bond formation","N-N azo/pyrazole formation (N-H/N-H)","Gieshoff/Waldvogel Angew 2016","substrate","2,2-dimethylmalonic dianilide","WC","CC(C)(C(=O)Nc1ccccc1)C(=O)Nc1ccccc1", 0.04, 2, 0.04, 2, "HFIP","0.01 M Bu4NPF6/HFIP"),
]

rows=[]
for (cls,name,ex,carrier,cspec,meth,arg,Cc,nc,Cs,ns,solv,elec) in R:
    if meth=="WC":
        ov = ion_override(arg, solv)
        if ov is not None:
            D,V = ov, np.nan; dprov="Nernst-Einstein from lambda0 (CRC/Izutsu)"
        else:
            D,V = wilke_chang(arg, solv); dprov=f"Wilke-Chang, Le Bas V={V:.0f} cm3/mol"
    else:
        D = stokes_einstein(arg, solv); V=np.nan; dprov=f"Stokes-Einstein r={arg} A"
    rows.append(dict(cls=cls, reaction=name, exemplar=ex, carrier_type=carrier,
        carrier_species=cspec, D_cm2s=D, V_lebas=V, D_provenance=dprov,
        C_carrier_M=Cc, n_carrier=nc, C_substrate_M=Cs, n_substrate=ns,
        solvent=solv, mu_mPas=SOLVENTS[solv][1], electrolyte=elec,
        ## A missing electrolyte used to fall through to NaN. Changing five electrolyte strings
        ## in the 2026-08-23 condition audit silently blanked kappa on five rows, and nothing
        ## complained -- the same class of failure as the Tier-0 fallback that build_merged_matrix
        ## used to substitute for a failed EC-prime solve. It is now a hard stop.
        kappa_mScm=_kappa(elec),
        cond_provenance=f"Representative of exemplar conditions ({ex})"))
df = pd.DataFrame(rows)
## ── concentration provenance (SI S4): PAGE-VERIFIED against the primary-source PDF
## corpus supplied 2026-07-11 ("papers for model", 49 PDFs). Tiers:
##   exemplar-verified      = value read directly from the cited page/table of the PDF
##   main-text-unverifiable = the supplied PDF is main-text only (no SI); the model
##                            value is retained and flagged; SI PDF requested
##   exemplar-anchored      = primary source physically absent (truncated book scan)
VERIFIED = {
 "Ni-catalyzed aryl amination (ArBr + amine)": "Exemplar-verified: ArX 0.025-0.05 M in DMA, Ni(bpy)3Br2 10 mol% (2.5-5 mM), nBu4NBr 0.2 M (Kawamata JACS 2019, Table 4 fn a p 6399; conditions D pp 6396-7); model uses the 0.05 M / 5 mM end",
 "Electrochemical amination of ArX with NH3": "Exemplar-verified: ArX 0.104 M (0.5 mmol/4.8 mL), NiBr2.3H2O+bpy 5.2 mM (5 mol%), TBAB 0.208 M, DMSO/THF 5:1, 85 C, undivided (Liu/Qiu Angew 2025, Table 1 fn a)",
 "Shono oxidation (N-acyliminium capture)": "Exemplar-verified: carbamate 1.56 M (0.05 mol/32 mL MeOH), Et4NOTs 0.156 M, 0.5 A, undivided, water-cooled (Shono JACS 1975, Experimental p 4267); modern partner exemplar SI-verified: pyrrolidine 0.149 M (250 mg = 0.819 mmol / 5.5 mL MeCN-H2O 10:1), ketoABNO 60 mol% = 89 mM, LiClO4 0.15 M, CPE 2.0 V ElectraSyn (Deprez OL 2021, SI pp S2, S19-20)",
 "Oxidative benzimidazole annulation (C-H/N-H)": "Standard conditions of ChemSusChem 2021, 14, 1692-1695, DOI 10.1002/cssc.202100254: 'amidine (0.3 mmol), Et4NPF6 (0.3 mmol), THF/MeOH (5:1, 9 mL), reflux' -> amidine 0.033 M, Et4NPF6 0.033 M, solvent THF/MeOH 5:1. MeOH alone is entry 2 of the optimisation table (52% against 65%), so the mixed medium is the one modelled. The paper runs at reflux against this model's isothermal 25 C -- a declared deviation.",
 "Mn-catalyzed alkene diazidation": "Exemplar-verified: alkene 0.051 M (0.2 mmol/3.9 mL), MnBr2.4H2O 2.6 mM (5 mol%), LiClO4 0.1 M in MeCN + 10 vol% HOAc, NaN3 5 equiv (Fu/Lin Science 2017, Fig 3 fn p 577) SI-ANCHORED (Fu/Lin, Science 2017, aan6206_fu_sm.pdf, Table S1 footnote, standard conditions): '0.2 mmol alkene, 0.01 mmol MnBr2.4H2O, 1.0 mmol NaN3, 400 uL HOAc, 3.5 mL LiClO4 solution in MeCN (0.1 M)'. Total volume 3.5 + 0.4 = 3.9 mL, so alkene 0.2/3.9 = 0.0513 M, Mn 0.01/3.9 = 0.00256 M, LiClO4 0.1 M -- all three as carried.",
 "Br-mediated Hofmann rearrangement": "Exemplar-verified (scale-up): amide 0.4 M, NaBr 0.08 M (20 mol%) in MeCN (MeOH 10 equiv is a REAGENT, not solvent; no NaOMe), spinning-anode flow, ~50 C, 136 mA/cm3 (Malviya/Cantillo OPRD 2023, Table 2 entry 5 p 2186, Table 3 pp 2187-8)",
 "Arene C-H pyridination": "Exemplar-verified (SI): anisole 0.020 M (0.20 mmol / 10.0 mL anodic chamber + 0.5 mL pyridine), Bu4NBF4 0.3 M both chambers, DIVIDED H-cell (4G frit), carbon-felt anode / Pt cathode, 8.0 mA, 25 C, 3 F/mol (Morofuji/Yoshida JACS 2013, SI pp S2-S3)",
 "Amidyl-radical C-H amination (phenanthridinone)": "Exemplar-verified: amide 0.04 M (0.3 mmol/7.5 mL MeCN/MeOH 14:1), NaBr 0.04 M = catalyst AND electrolyte, Pt, 8.9 mA/cm2, undivided (Zhang/K. Xu/Zeng OL 2018, Scheme 2 fn a p 3444) SI-ANCHORED (Zhang/Xu/Zeng, Org. Lett. 2018, ol8b00981_si_001.pdf, Table S1 footnote a): 'undivided cell, anode and cathode (1.5 x 1.5 cm2, J = 8.9 mA/cm2), 1 (0.3 mmol), CH3CN (7 mL), MeOH (0.5 mL), electrolyte (0.3 mmol) at rt for 2 h'. Total volume 7.5 mL, so substrate and NaBr are both 0.3/7.5 = 0.040 M, as carried; the current density matches too.",
 "Co-catalyzed aza-Wacker cyclization": "Exemplar-verified: carbamate 0.033 M (0.2 mmol/6 mL MeCN/MeOH 5:1), Co(salen) 3.3 mM (10 mol%), Et4NPF6 0.033 M, reflux, RVC/Pt (Cai/H.-C. Xu Nat Commun 2021, Table 1 fn p 3; Methods p 7)",
 "Ritter-type C(sp3)-H amination": "Exemplar-verified: 1,3-dimethyladamantane 0.167 M (0.5 mmol/3 mL MeCN), H2SO4 4 equiv (sulfate-radical HAT), Bu4NBF4 0.1 M, Pt/Pt, 5 mA, undivided (Zhang/Ye Nat Commun 2022, Table 1 fn p 3)",
 "Co-H alkene reduction (e-HAT)": "Exemplar-verified (Conditions C): substrate 0.08 M (0.2 mmol/2.5 mL THF + HFIP 9 equiv), CoBr2(glyme) 8 mM (10 mol%), Et3NHBF4 0.24 M, Mg/C, undivided (Gnaim/Baran Nature 2022, Fig 3 p 689, Fig 4a p 691)",
 "Kolbe homocoupling of 10-undecenoate": "Exemplar-verified against the 10-undecenoic acid scale-up, one experiment: 'To a reactor beaker equipped with a stir bar were added acetone (200 mL), 10-undecenoic acid (36.8 g, 200 mmol), pivalic acid (4.0 g, 40 mmol), Me4N.BF4 (TMABF4) (1.6 g, 10 mmol), and Me4N.OH pentahydrate (5.4 g, 30 mmol)' -> acid 200/200 = 1.00 M, Me4NBF4 10 mmol/200 mL = 0.05 M (5 mol%), Me4NOH 30 mmol/200 mL = 0.15 M (15 mol%). 20 Vpp, RVC plates, ~1 A decaying to ~0.4 A over 48 h. The substrate is 10-undecenoate (C11) and D is computed for it. Pivalic acid at 40 mmol (0.2 M, 20 mol%) is present as a co-acid and is not modelled. SI-ANCHORED (Hioki/Baran, Science 2023, science.adf4762_sm.pdf, 'Procedure for 10-undecenoic acid dimerization'): the quoted recipe is verbatim from that SI section.",
 "Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)": "Exemplar-verified (kg flow): ArBr 0.3 M nominal in DMA (13 L/kg), Ni(dtbbpy)2Br2 5 mol% = 15 mM, LiBr 0.48 M, 10 mA/cm2, 8.41 A/841 cm2, undivided recirculating flow, Zn anode (Kelly/Stahl/Schreier OPRD 2026, Table 1, Fig 4a, Fig 6a) SI-ANCHORED (Kelly/Stahl/Schreier, Org. Process Res. Dev. 2026, op6c00110_si_001.pdf, multiday/flow-cell run): 'a starting material 2 concentration of 0.3M and electrolyzed at 10 mA cm2' with '1.6 equiv LiBr and 5 mol% (relative to species 2) Ni catalyst' -- so LiBr 1.6 x 0.3 = 0.48 M and Ni 5 mol% x 0.3 = 0.015 M, all three as carried.",
 "Doubly decarboxylative Csp3-Csp3": "Exemplar-verified (SI): limiting acid 0.029 M during ELECTROLYSIS (0.1 mmol / 3.0 mL DMF + 0.5 mL retained DCM; the oft-quoted 0.2 M is the DCM activation step only), acid B 3 equiv, NaI 0.2 M (0.6 mmol/3.0 mL DMF), 4 mA, Zn/Ni-foam ElectraSyn (Zhang/Baran Nature 2022, SI pp 8, 10-13, 38); gram scale 0.057 M, 35 mA (SI pp 16-17); TWO monoacids via in-situ NHPI RAEs -- not diacids",
 "BDD phenol-arene cross-coupling": "Exemplar-verified: phenol 0.15 M (5 mmol/33 mL HFIP + 18 vol% MeOH), arene 3 equiv (0.45 M), MTES (Et3NMe.O3SOMe) 0.091 M, BDD anode, 2.8 mA/cm2, 2 F/mol, 50 C, undivided (Kirste/Waldvogel JACS 2012, Experimental pp 3571-2) SI-ANCHORED (Kirste/Waldvogel, J. Am. Chem. Soc. 2012, ja211005g_si_001.pdf, 'General procedure for the anodic phenol-arene cross-coupling reaction'): 'phenol component (0.005 mol), arene component (0.015 mol) and N-methyl-N,N,N-triethylammonium methylsulfate (0.68 g, 0.003 mol) in 1,1,1,3,3,3-hexafluoropropan-2-ol (27 mL) and methanol (6 mL)'. Total 33 mL, so phenol 0.152 M, arene 0.455 M, MTES 0.091 M -- all as carried.",
 "Decarboxylative Minisci alkylation": "SI-anchored (Mo/Jensen, Science 2020, aba3823_mo_sm.pdf, 'General Procedure A for Decarboxylative Arylation', p. 19). The modelled concentrations are stated arithmetic, not estimates: 'aryl nitrile (0.80 mmol, 1.0 equiv.)' and the carboxylic acid (4.80 mmol, 6.0 equiv.) are taken up in MeCN and 'transferred to a 10.0 mL volumetric flask. Additional MeCN was added to make the solution volume 10.0 mL' -- an exact final volume rather than a sum of charges -- giving 0.080 M for the 1,4-dicyanobenzene this row transports as both carrier and substrate, and 0.48 M for the carboxylate. The carboxylate is generated in situ from Bu4NOH (4.56 mmol, 5.7 equiv.), which is sub-stoichiometric to the acid, so the salt itself is capped near 0.456 M and the 0.48 M recorded here is the acid charge, about 5% above it; the difference is immaterial because that number enters only as a supporting-electrolyte concentration behind a declared conductivity and not as a transported species. Two things on this row are genuinely declared rather than page-anchored: no separate supporting salt is added -- 'No additional supporting electrolyte was required, because of the excellent conductivity in the microfluidic channel' -- so kappa is declared; and the 25 um interelectrode gap sits outside the architectures modelled here, so the architecture assignment is declared too. The general procedure notes that 'lower concentrations were used for some aryl nitrile substrates due to their low solubility', so this row is anchored to the general procedure rather than to any single substrate entry.",
 "Cathodic Giese (R-I + alkene)": "Exemplar-verified (ESI): R-I 0.095 M electroactive (1.43 mmol / 15 mL catholyte = 10 mL pH-2 HCl aq + 5 mL MeCN) + alkene 0.079 M limiting (1.19 mmol), NaCl 7 mol% (~5.6 mM) + HCl ~6.7 mM = only ionics (~12 mM total -- very low kappa), DIVIDED H-cell (frit), graphite 4.12 cm2, CPE -1.0 V vs Ag QRE, rt, 20-45 h (Li/Wilden Chem Sci 2020, ESI pp S3, S5); largest run 0.25 M alkene (ESI p S10); alkyl BROMIDES marginal (21%, main text)",
 "Rh-catalyzed electrooxidative C-H alkenylation": "Exemplar-verified: acrylate 0.125 M limiting + benzoic acid 0.25 M (4 mL tAmOH/H2O 3:1), [Cp*RhCl2]2 2.5 mol% = 3.1 mM (6.25 mM Rh), KOAc 0.25 M = electrolyte + CMD base, 4 mA RVC, 100 C, undivided (Qiu/Ackermann Angew 2018, Table 1 fn a p 5828)",
 "Cu-catalyzed benzylic cyanation": "Exemplar-verified: alkylarene 0.038 M (0.2 mmol/5.21 mL), Cu(acac)2 3.8 mM + BOX 5.0 mM + AQDS 1.9 mM (PEC, 395 nm), Bu4NBF4 0.077 M, MeCN/TFE/H2O, TMSCN 3 equiv, RVC/Pt, 3 mA, undivided (Cai/H.-C. Xu Nat Catal 2022, Fig 2b fn pp 944-5; Methods p 949)",
 "Cathodic Ni aryl-aryl homocoupling": "All three numbers from one footnote: 'Experimental conditions : Solvent : 50 mL, PhBr 15 mmol., NiBr2bpy 1.5 mmol., supporting electrolyte: NaBr 4.10-2 mol.L-1' -> PhBr 15/50 = 0.30 M, NiBr2(bpy) 1.5/50 = 0.030 M, NaBr 0.04 M (Courtois/Barhdadi/Troupel/Perichon, Tetrahedron 1997, 53, 11569). The medium is the paper's own, 'DMF (10 ml) + EtOH (40 ml) or in EtOH (25 ml) + MeOH (25ml)'; neat MeOH is not one of its media.",
 "Anodic dehydrogenative 2-naphthol coupling": "Exemplar-verified: 2-naphthol 1.0 M (5 mmol/5 mL MeCN anolyte) + sparteine 1 equiv, NaClO4 0.2 M, TEMPO immobilized ON the graphite-felt anode (not in solution), DIVIDED Nafion H-cell, CPE +0.60 V (Osa/Bobbitt Chem Commun 1994, p 2535 + Table 1 p 2536) PAGE-ANCHORED IN THE ARTICLE BODY (no SI exists; 1994 ChemComm communications carry none, and none is needed): 'The anolyte contained 5 mmol of substrate, 2 mmol of tetralin as a chromatographic standard, 5 mmol of 1 and 1 mmol of NaClO4 as a supporting electrolyte in a total volume of 5 cm3.' So 2-naphthol 5/5 = 1.0 M, sparteine 5/5 = 1.0 M (1 equiv) and NaClO4 1/5 = 0.2 M -- all three exactly as carried. The automatic anchor check misses the electrolyte only because the paper writes the volume as cm3 and the quotient matcher looks for mL.",
 "Acrylonitrile hydrodimerization (ADN)": "Exemplar-verified: AN 40 wt% = 6.85 M in 56 wt% aq Et4NOTs (~1.0 M salt), DIVIDED (alundum diaphragm), Hg pool, ~55 mA/cm2, pH ~8, 25 C (Baizer JES 1964, Table II run 28 p 218, Tables III-IV p 219); <10 wt% AN favors propionitrile, so the lean-electrolyte regime is explicitly avoided",
 "Birch reduction of naphthalene": "Against the SI. LiBr 3.0 M comes from the 10 g batch scale-up ('10 g scale-up (in batch) Mg(+)/Stainless steel plate(-) undivided 3.0 M LiBr, 12.0 eq. DMU, 3.5 eq. TPPA, 500 mA, 10 F, rt'; 'Preparation of LiBr solution in THF (3.0 M)'). The same run charges 'tert-butyldimethyl(p-tolyloxy)silane (10.0 g, 45.0 mmol), DMU (47.5 g, 540.0 mmol), TPPA (40.5 g, 157.5 mmol) and LiBr solution (320 mL)' -> 45.0/320 = 0.141 M substrate, and the added solids only raise the volume, so 0.141 M is itself an upper bound. The 0.1 mmol ElectraSyn general procedure is a different experiment (0.0286 M substrate, 0.214 M LiBr) and is not what this row models. The carrier is naphthalene as a declared class representative; the scale-up substrate is TBS-cresol.",
 "Nitroarene -> aniline": "Exemplar-verified: 3-O2N-C6H4-CF3 0.4 M standard (0.6 M max flow), MeOH/H2O 1:1, 2 M H2SO4 (3-5 M in scale-up; EtOH failed), DIVIDED Nafion, leaded-bronze cathode, 30 mA/cm2, 12 F (Kisukuri/Waldvogel OPRD 2024, Tables 1-4, Schemes 5-6 pp 1475-80)",
 "Rapid-alternating-polarity imide reduction": "Against the SI: 'the corresponding aromatic substrate (15 mg, 0.1 mmol), tetramethylammonium tetrafluoroborate (40 mg, 0.25 mmol) and pivalic acid (31 mg, 0.3 mmol) in 3.0 mL of MeOH', 20 mA, rAP 100 ms 5 Hz, 20 F/mol -> substrate 0.1/3.0 = 0.0333 M and Me4N.BF4 0.25/3.0 = 0.0833 M (2.5 equiv), in MeOH with the PivOH additive. One experiment, both numbers. Hayashi/Baran, J. Am. Chem. Soc. 2022, 144, 5762-5768, DOI 10.1021/jacs.2c02102; Kawamata is a corresponding middle author.",
 "Cathodic aryl chloride dehalogenation": "Declared rather than exemplar-verified. The exemplar is Ke, Wang, Zhou, Mou, Zhang, Pan, Chi, 'Hydrodehalogenation of Aryl Halides through Direct Electrolysis', Chem. Eur. J. 2019, DOI 10.1002/chem.201901082, but the conditions this row carries (ArX 0.043 M in MeCN, nBu3N 2 equiv, Bu4NBF4 0.043 M, graphite, 15 mA, undivided) are class-representative and carry no page locator. Eq. S1 is linear in C, so this row rescales in proportion and no architecture ranking depends on it.",
 "Benzaldehyde -> benzyl alcohol": "Exemplar-verified: PhCHO 0.02 M standard (0.18 M max studied; aq solubility 28.3 mM), MeOH/H2O 50:50 wt + 5 wt% AcOH catholyte, DIVIDED Nafion 117 flow cell, Pd/C felt cathode, 5-15 mA/cm2 (Lopez-Ruiz ACS SCE 2018, Methods pp 16074-5, Table 1)",
 "ACT-mediated alcohol oxidation (flow, hectogram)": "Exemplar-verified (200-g campaign): alcohol 0.5 M, ACT 5 mol% = 25 mM, NaHCO3 1 M / Na2CO3 1 M pH 8.5 -- purely AQUEOUS (no MeCN), DIVIDED recirculating flow (Nafion 324), 100-300 mA/cm2 graphite felt (Zhong/Stahl OPRD 2021, Table 1 p 2602, Fig 5 p 2603, Fig 6 p 2604)",
 "Anodic methoxylation of 4-tBu-toluene (Lysmeral)": "Page-anchored to US 5,507,922, Hermeling, Hannebaum, Voss & Weiper-Idelmann (BASF), 'Preparation of benzaldehyde dialkyl acetals', 16 Apr 1996. The patent PDF carries no text layer (5 characters extracted), so it was rendered at 300 dpi with PyMuPDF and read with tesseract 5.5.2, recovering 24 kB. The worked example's electrolyte composition reads: '450 g (15% by weight) of p-tert-butyltoluene / 10 g (0.3% by weight) of sulfuric acid / 2,450 g (84.7% by weight) of methanol', graphite electrodes 1 mm apart, 3.4 A/dm2 (34 mA/cm2), 7.5 F/mol, 55 C, electrolyte circulated 200 L/h. 450 g / 148.25 g/mol = 3.035 mol in ~3.65 L (volume-additive from 2450 g MeOH at 0.786 and 450 g TBT at 0.861) = 0.83 M, against the row's 0.81 M -- within 3%. The 0.3 wt% H2SO4/MeOH in the electrolyte column is verbatim from the patent.",
 "Shono alpha-methoxylation of amides": "Class-representative by analogy: 1.56 M / Et4NOTs 0.156 M / MeOH transferred from the page-verified carbamate protocol (Shono JACS 1975, Experimental p 4267); no amide-methoxylation exemplar PDF supplied",
 "Cl-mediated ethylene epoxidation": "Measured and page-anchored. Electrolyte: the paper's flow cell uses '1.0 M potassium chloride (KCl) electrolyte, in which ethylene was continuously sparged into the anolyte', 70(+/-1)% FE to ethylene oxide at 300 mA/cm2. Substrate 0.00352 M = ethene in 1.000 M KCl at 298.15 K, 101.3 kPa, measured: IUPAC Solubility Data Series Vol. 57 (ethene, compiled by C. L. Young), original measurement Yano, T.; Suetaka, T.; Umehara, T.; Horiuchi, A., Kagaku Kogaku 1974, 38, 320-323 -- KCl series 0.500/1.000/1.500 M giving 4.14/3.52/3.03 mmol/L, against 4.83 mmol/L in pure water, so the salting-out correction is 27%. Two independent cross-checks inside the same volume: the compilation's own Sechenov evaluation gives slope -0.136 +/- 0.001 L/mol and log10(4.83/3.52) = 0.1374; and the series is monotonic across KBr, KCl and CuCl2.",
 "Alkaline lignin -> vanillin (pilot)": "Exemplar-verified (ex-cell, TRL-6 pilot): the CELL electrolyzes 1 M Na2CO3(aq) to peroxodicarbonate (<=0.2 M, FE ~40%) on BDD at up to 675 mA/cm2, 10-11 C; lignin (0.1-3 wt% in 3 M NaOH) reacts DOWNSTREAM in an 80-L thermal PFR at 150 C and never enters the cell (Ruecker/Waldvogel ACS SCE 2024, Figs 4-9 pp 11285-92); row therefore models the carbonate carrier",
 "Thioether -> sulfone (kilo-scale)": "Exemplar-verified (kilo run): thioether 0.47 M intensified (0.1 M development; 0.35 M appears nowhere), MeCN / 0.1 M aq HCl 6:1, Cl- 14 mM (3 mol%) in-situ mediator, Et4NPF6 0.085 M (0.18 equiv), 30 mA/cm2, 48 A/1600 cm2 undivided flow stack, <20 C (Bottecchia/Merck OPRD 2022, pp 2429-31, Figs 6-8)",
 "NHPI-mediated allylic C-H -> enone": "Exemplar-verified: substrate 0.167 M (0.5 mmol/3 mL ACETONE; Fig 2 caption states 'acetone (0.16 M in substrate)'), Cl4NHPI 20 mol% = 33 mM, pyridine 2 equiv, tBuOOH 1.5 equiv, LiClO4 0.1 M, 10 mA per mmol substrate, RVC, undivided (Horn/Baran Nature 2016, 533, 77-81; Fig 2 caption p 78, Fig 3 caption p 79)",
 "HMF -> FDCA (biomass)": "Exemplar-verified (concentrated run): HMF 100 mM + ACT 40 mM (40 mol% optimum), 0.5 M borate buffer pH 10 anolyte / 0.1 M NaOH catholyte, DIVIDED (AEM), CPE 1.6 V vs RHE, carbon felt (Cardiel/Choi ACS SCE 2019, pp 11139-40, Fig 6-7 + Tables 1-2 pp 11144-5)",
 "Radical-cation Diels-Alder (catalytic in e-)": "Exemplar-verified: anethole 0.08 M (1.6 mmol/20 mL) + diene 2 equiv (0.16 M), LiClO4 1.0 M in NITROMETHANE (MeCN 26%, MeOH 0%), 0.05-0.5 F/mol, rt (Okada/Chiba Chem Sci 2016, Table 1 fn a p 6388) SI-ANCHORED (Okada/Chiba, Chem. Sci. 2016, c6sc02117d1_suppl.pdf, worked example): 'trans-anethole 1 (237 mg, 1.60 mmol), isoprene 2 (218 mg, 3.20 mmol), lithium perchlorate (2.13 g) and nitromethane (20 mL), 0.1 F/mol'. So anethole 0.080 M, isoprene 0.160 M, and LiClO4 2.13 g / 106.39 g mol-1 = 20.0 mmol / 20 mL = 1.00 M -- all three as carried.",
 "BQ-mediated Wacker-Tsuji oxidation": "Fully anchored in the article body; this paper has no SI and needs none. Experimental: 'Palladium(II) acetate (0.1 mmol), benzoquinone (2 mmol), and perchloric acid (0.015-0.36 M) were dissolved in acetonitrile/water (7 : 1 v/v, 85 mL containing 0.1 M TBAP) in the anode compartment', with the Table 1 footnote '10 mmol olefin, 20 mol% benzoquinone, 1 mol% Pd(OAc)2, 7:1 CH3CN/H2O, 25 C, 0.90 V vs. SCE, 0.1 M TBAP at a platinum mesh working electrode'. One experiment, every number: olefin 10/85 = 0.118 M, BQ 2/85 = 0.0235 M (20 mol%, consistent), TBAP 0.1 M, MeCN/H2O 7:1, divided cell. Miller & Wayner, Can. J. Chem. 1992, 70, 2485; the '2011' in the filename is a re-hosting date.",
 "Non-Kolbe decarboxylative alpha-methoxylation": "Exemplar-verified: N-Piv-alanine 0.1 M (0.4 mmol/4 mL MeOH), Et3N 7.5 mM only -- NO added salt, graphite, 60 mA, 2.1 F/mol, undivided ElectraSyn (Walecka-Kurczyk RSC Adv 2022, Table 1 p 2109; procedure p 2110)",
 "Co-H alkene isomerization (catalytic)": "Exemplar-verified (Conditions B): alkene 0.08 M (0.2 mmol/2.5 mL ACETONE + HFIP 1-4 equiv), Co(salen)-1 3-6 mol% = 2.4-4.8 mM, TBABF4 0.1 M, Zn/Ni, 5 mA, undivided (Gnaim/Baran Nature 2022, Fig 2 scheme p 688; 100-g flow: 2 mol%, TBABF4 0.06 M, 2 mA/cm2, Fig 4b p 691-2)",
 "Anodic oxazoline/oxazole cyclization": "Exemplar-verified: ketone 0.05 M (0.4 mmol/8 mL MeCN anolyte), N(PMP)3 5 mM (10 mol%) as redox mediator with TFAA/Ac2O activators, LiClO4 0.3 M, divided H-cell, E_cell 2.5 V, carbon felt (Bao OL 2022, Table 1 fn a p 5763). The row is modelled on the ketone as carrier.",
 "Cathodic aryl-halide radical 5-exo cyclization": "Exemplar-verified: ArX 0.05 M (1 mmol/20 mL DMF), Ni(tet a)(ClO4)2 10 mM (20 mol%) = the current-carrying CATALYST, Et4NClO4 0.1 M, NH4ClO4 2 equiv, DIVIDED H-cell, CPE -1.3 V vs SCE, graphite (Ozaki/Ohmori Tet Lett 1994, p 726 + Table 1)",
 "Dehydrogenative lactonization (C-H/O-H)": "Org. Lett. 2018, 20, 252-255, DOI 10.1021/acs.orglett.7b03617. The DOI carries a 2017 manuscript id while the paper's own header reads 'Cite This: Org. Lett. 2018, 20, 252-255' (published December 7, 2017, in the January 2018 issue); an ACS DOI's year prefix is not a publication year. Conditions from Fig 2 fn a: 'undivided cell, Pt anode and cathode (1.5x1.5 cm2, J = 13.3 mA/cm2), 1 (0.5 mmol), CH3CN (7 mL), MeOH (1 mL), n-Bu4NBF4 (2 mmol) at room temperature for 1.5-2.5 h' -> substrate 0.5/8 = 0.0625 M, Bu4NBF4 2/8 = 0.25 M. One experiment, both numbers. Anchored by hand because the CH3CN subscript bleeds into the extracted text as 'MeOH (1 3 mL)'.",
 "Anodic benzylic fluorination": "Exemplar-verified: substrate 0.1 M (1 mmol/10 mL MeCN), Et4NF.4HF 1 M = F source AND electrolyte (NOT Et3N.3HF), Pt 2x2 cm, 2-3.5 F/mol, undivided, rt (Tajima/Fuchigami Electrochem Commun 2002, Sec 2.3 p 590, Tables 2/4)",
 "Br- oxidation / electrophilic bromination": "Against 10.1038/s41467-025-57329-0, which reports three condition sets: Fig 4 'NaBr (0.5 M in deionized water, 7.5 mL), CH3CN (7.5 mL) in each chamber, 1 (0.5 mmol)' -> Br- 0.25 M, substrate 0.033 M; Fig 5c 'NaBr (0.5 M ..., 12.5 mL), CH3CN (12.5 mL) ..., 1 (0.5 mmol)' -> Br- 0.25 M, substrate 0.020 M; and Fig 5b, the 518 g flow run this exemplar cites as '0.61 kg': 'Substrate (4 mmol), solvent (0.5 M NaBr in deionized water (10 mL):CH3CN:CH3OH:CH2Cl2 = 10:10:10:3)' -> 33 mL total, Br- 0.5x10/33 = 0.152 M, substrate 4/33 = 0.121 M. Because the exemplar cites the kg-scale run, this row carries Fig 5b throughout -- Br- 0.152 M and substrate 0.121 M, one experiment. It is one of the eight mediated EC' rows and is solved with the full EC' treatment of S5.4.",
 "Diazo difunctionalization (thiol + alcohol)": "Exemplar-verified: thiol 0.5 mmol LIMITING + diazo 2.0 mmol (4 equiv) + alcohol 0.5 mL, Et4NBF4 0.5 mmol, MeCN 6 mL (6.5 mL total liquid) -> thiol 0.077 M, diazo 0.31 M, Et4NBF4 0.077 M; carbon rod anode / Pt plate 1.5x1.5 cm cathode, undivided, 10 mA, 50 C, N2, 5 h = 3.7 F on the thiol (Yang, Guan, Peng et al., Nat. Commun. 2023, 14, 1476, DOI 10.1038/s41467-023-37032-8, general procedure; open access, retrieved in full text via PMC10020561). THREE-COMPONENT: diazo + thiol + alcohol, two new ACYCLIC bonds (C-S and C-O at the same carbon)",
 "Alkenesulfonate from cinnamic acid, SO2 and alcohol": "Exemplar-verified: cinnamic acid 0.3 mmol at 0.1 M in MeCN (3 mL anolyte), SO2 10.0 equiv from a 5.0 M MeCN stock, neopentyl alcohol 3.0 equiv, 2,6-lutidine 6.0 equiv, nBu4NPF6 0.1 M; graphite anode and cathode, DIVIDED (glass frit), 10 mA cm-2, 3.5 F, 20 C; catholyte nBu4NPF6 0.1 M + AcOH 5.0 equiv (Chien, Breitschaft, Kelm, Waldvogel & Manolikakes, ChemSusChem 2025, 18(12), e202500186, DOI 10.1002/cssc.202500186, general procedure; open access, retrieved in full text via PMC12175053). THREE-COMPONENT: cinnamate + SO2 + alcohol, no ring formed",
 "Sulfonylation of alkenes with sulfinates": "The paper's standard conditions carry no added salt: '1a (0.5 mmol), 2 (1.0 mmol), MeOH (8 mL), TsOH (0.5 mmol), 4 A MS (200 mg), and constant current = 10 mA, in undivided cell at room temperature under nitrogen atmosphere for 2.5 h'. Table 1 entry 15 (TsOH only) gives 82% against 79% for entry 6 with LiClO4, and the LiClO4 named in the introduction describes prior work, so the electrolyte modelled is TsOH at 0.5 mmol/8 mL = 0.0625 M -- the same molarity as a 1:1 lithium salt but a strong acid in MeOH, which moves both kappa and the migration factor. The anodically discharged species is the sulfinate at 2 equiv = 0.125 M; this row carries the styrene at 0.0625 M on a conservative limiting-reagent basis, which halves the ceiling by choosing the smaller of two real numbers.",
 "Aryl thiocyanation (NH4SCN)": "Exemplar-verified against the CONSTANT-CURRENT runs, which are the ones this row models: 'Constant current electrolyses were performed in a divided H-type two-compartment cell equipped with a medium glass frit as a membrane. Both electrodes were made of Pt foils (5 cm2) and distant from each other by 3-5 mm. The volume of the electrolyte solution (1:1 AcOH-HCOOH and 0.1 M LiClO4) in each compartment was 20 ml and the ratio between substrate (5 mmol) and NH4SCN (2 mmol) was 5:2' (Exp. 2.1, p. 5856). So ArH = 5/20 = 0.25 M, NH4SCN = 2/20 = 0.10 M and LiClO4 = 0.1 M, all from one sentence that also fixes the solvent and the cell. THE PAPER DESCRIBES A SECOND, DIFFERENT EXPERIMENT and the two must not be mixed: the controlled-potential variant puts '5 mmol of aromatic substrate and 2 mmol of NH4SCN, both dissolved in 30 ml' into the anode compartment, giving 0.1667 and 0.0667 M. On 2026-08-30 this row was switched to those CPE numbers on the reading that 20 mL was an error; it was not. The switch happened because the cached text extraction for this paper had DROPPED the constant-current sentence, so only the CPE one was visible, and a correct value was overwritten with a wrong one. Restored 2026-08-31 after a better extraction recovered the passage. This row is constant-current throughout -- Pt 1-10 mA/cm2 (best 1), 2.25 F/mol, divided cell -- and the 0.5 M LiClO4 value belongs to the glacial-AcOH CPE variant, not here. NO SUPPORTING INFORMATION EXISTS for this paper (Gitkis/Becker, Electrochim. Acta 2010, 10.1016/j.electacta.2010.05.035); the conditions are read from the article body alone.",
 "Anodic C-H phosphonylation of azoles": "Exemplar-verified: arene 0.05 M limiting (0.2 mmol/4 mL MeCN) + P(OEt)3 5 equiv (0.25 M), HBF4.Et2O 0.1 M = only electrolyte, graphite/Pt 5.5 mA/cm2, 0.25 mm-gap flow, 75 s residence, 3.4 F/mol (Long/H.-C. Xu Nat Commun 2021, Table 1 fn, Fig 2-3); conservative limiting-reagent basis",
 "N-N azo/pyrazole formation (N-H/N-H)": "Exemplar-verified (SI): dianilide 0.040 M at BOTH scales (0.2 mmol / 5 mL Teflon cell, Protocol A/B; 1.0 mmol / 25 mL glass cell, Protocol C), Bu4NPF6 0.01 M exactly (19.3 mg/5 mL; 96.5 mg/25 mL -- both = 9.96 mM), HFIP, graphite/Pt, 0.5 mA/cm2 galvanostatic, 2.2 F for the parent (Gieshoff/Waldvogel Angew 2016, SI pp S4-S6, S14)",
}
missing = [n for n in df.reaction if n not in VERIFIED]
assert not missing, f"rows without conc provenance: {missing}"
df["conc_provenance"] = [VERIFIED[n] for n in df.reaction]
## ex-cell mediation note (Cl-/propylene): the in-film total-catalysis cap
## F*n*D_S*C_sat/delta (~1 mA/cm2 at C_sat ~ 5 mM) does NOT bind because the mediator
## is consumed in the BULK (sparged propylene), not in the film -- see SI S4.
assert len(df)==50, len(df)


# ---------------------------------------------------------------------------
# Everything below WRITES production data files (reactions_50.csv, solvents.csv,
# electrolytes.csv, julia/reactions_table.jl). It is guarded because the module is
# legitimately imported for wilke_chang()/SOLVENTS/lebas_volume, and an unguarded
# import silently rewrote all four on 2026-08-22. The regeneration happened to be
# idempotent, but a side-effecting import is not something to rely on being safe.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # ---- G-LEBAS: implementation regression test on the Le Bas assembly ----
    #
    # WHAT THIS IS, STATED HONESTLY. The reference volumes below are RECALLED standard Le Bas
    # values, not values read out of Reid/Poling Table 3-11 or Perry's Table 2-400 in this pass.
    # For most of them the published number IS the additive sum of the same increments, so for
    # those compounds this test compares the code's arithmetic against a remembered result of
    # the same arithmetic. It is therefore an IMPLEMENTATION REGRESSION TEST, not an independent
    # verification of the increment set -- the increments are separately cited, row by row, in
    # data/parameters_provenance.csv (Table 11-1).
    #
    # It is not worthless: it catches the ways the assembly can silently go wrong -- ring
    # detection, implicit-H counting, the acid-hydroxyl special case, increment lookup. Break
    # ring detection and benzene returns 111 instead of 96 and this fires.
    #
    # The two compounds where the recalled value does NOT equal naive addition -- chlorobenzene
    # (115.0 vs 116.9 computed) and diethyl ether (104.8 vs 103.6) -- are the only genuinely
    # external checks here, and both are the ones that disagree, at 1.7% and 1.1%. Read the 3%
    # tolerance as accommodating that, not as a measured agreement.
    LEBAS_CLOSURE = {
        "c1ccccc1": ("benzene", 96.0),        "Cc1ccccc1": ("toluene", 118.2),
        "CO": ("methanol", 37.0),             "CCO": ("ethanol", 59.2),
        "CC(C)=O": ("acetone", 74.0),         "CC(=O)O": ("acetic acid", 63.8),
        "c1ccc2ccccc2c1": ("naphthalene", 147.6), "Clc1ccccc1": ("chlorobenzene", 115.0),
        "CCCCCC": ("n-hexane", 140.6),        "CCOCC": ("diethyl ether", 104.8),
    }
    _worst = 0.0
    for _smi, (_nm, _lit) in LEBAS_CLOSURE.items():
        _v = lebas_volume(_smi)
        _d = 100.0 * (_v - _lit) / _lit
        _worst = max(_worst, abs(_d))
        if abs(_d) > 3.0:
            raise AssertionError("Le Bas closure failed for %s: %.1f vs published %.1f (%+.1f%%)"
                                 % (_nm, _v, _lit, _d))
    print("Le Bas assembly regression: 10/10 reference compounds within 3%%, worst %.1f%% "
          "(recalled reference values; see the note above for what this does and does not test)"
          % _worst)

    # ---- validation anchor: ferrocene/MeCN (measured 2.4e-5 cm2/s) ----
    D_fc,_ = wilke_chang("[cH-]1cccc1.[cH-]1cccc1.[Fe+2]", "MeCN")
    print(f"validation: ferrocene/MeCN Wilke-Chang D = {D_fc:.2e} cm2/s  (measured ~2.4e-5)")

    df.to_csv(OUT_REACTIONS, index=False)
    pd.DataFrame([dict(solvent=k,M=v[0],mu_mPas=v[1],rho=v[2],phi=v[3],src=v[4]) for k,v in SOLVENTS.items()]).to_csv(OUT_SOLVENTS,index=False)
    # electrolytes.csv carries the provenance STATE alongside kappa so that no conductivity can be
    # consumed without its class travelling with it. Under the three-state standard
    # (docs/PROVENANCE_STANDARD.md) the 2026-08-02 sourcing pass moved TEN rows off `assumption`:
    # nine to `derived` (state B) and one to `measured` (state A) -- see ELECTROLYTE_STATE above for
    # which, and why. Of the 49 REGISTERED conductivities, nine are now derived and the remaining 40
    # are assumptions; the one measured row (0.1 M Bu4NPF6/THF) is `unused-legacy`, so no measured
    # conductivity is registered. The per-row sensitivity lives in parameters_provenance.csv,
    # category 6. The `status` column separates the 49 rows that are actually assigned to a reaction
    # -- and therefore reach the SI registry (Table S7f) -- from the legacy entries that are defined
    # here but used nowhere and carry NO provenance row at all.
    #
    # The state column is a LOOKUP, not a constant. It was `state="assumption"` hardcoded, which meant
    # this generator could not express the ten promotions and would have flattened them on the next run.
    _used_elyte = set(df["electrolyte"])
    # SECOND CONSUMER. `_used_elyte` sees only reactions_50.csv, but julia/cellvoltage.jl
    # independently hardcodes five electrolytes for the cell-voltage / thermal stack (its ELECS
    # list) and refuses any whose status is not `registered`. Before 2026-08-22 those five
    # happened to be covered because some reaction row also used them -- "1 M NaOH aq" was
    # registered solely by the octadecanol row. Swapping that row out for a multicomponent
    # coupling therefore broke run_section4.jl with "has status 'unused-legacy'", even though
    # nothing about the thermal analysis had changed. Registration must follow ALL consumers,
    # not whichever one happens to be enumerated here.
    # Consumers OTHER than the 50-reaction table. An electrolyte reaches the registry if any of
    # these uses it -- not only if a reaction names it.
    _CELLVOLTAGE_ELYTES = {"3.0 M LiBr/THF", "0.25 M Bu4NBF4/MeCN", "0.2 M NaI/DMF",
                           "1 M NaOH aq", "0.3 wt% H2SO4/MeOH (BASF)",
                           # Quoted in the MANUSCRIPT BODY, in the TRL-E 6 worked example:
                           # "0.1 M Bu4NBF4 in DMF, kappa = 3.5 mS cm-1" -> a 16.8 V cell of which
                           # 14.3 V is ohmic, dissipating 1.4 W cm-2. It was carried as
                           # `unused-legacy (no registry row)` because no entry of the 50-reaction
                           # table names it, so a number printed in the manuscript had no provenance
                           # row anywhere. Gate G-MSELYTE now asserts the manuscript's electrolytes
                           # against this set.
                           "0.1 M Bu4NBF4/DMF"}
    pd.DataFrame([dict(electrolyte=k, kappa_mScm=v,
                       state=ELECTROLYTE_STATE.get(k, "assumption"),
                       status=("registered" if k in _used_elyte or k in _CELLVOLTAGE_ELYTES
                               else "unused-legacy (no registry row)"))
                  for k, v in ELECTROLYTES.items()]).to_csv(OUT_ELECTROLYTE, index=False)

    # ---- emit Julia include (matches co2r_bulk params.jl style) ----
    # Written to julia/, not to this directory: julia/reactions_table.jl is the only copy in the tree
    # and the one every consumer reads (`include("reactions_table.jl")` at julia/run_section4.jl:8 and
    # julia/run_tier0.jl:4, and the parsers in figs/archetype_bands.py and figs/model_medians.py).
    # Emitting it beside this script instead would leave that copy stale and create a second one that
    # nothing reads.
    with open(OUT_RXN_TABLE,"w") as f:
        f.write("## reactions_table.jl - GENERATED by build_reactions50.py. Do not edit by hand.\n")
        f.write("## 50 representative organic electrosyntheses, stratified by the 25,941-rxn corpus.\n")
        f.write("struct OERxn\n    cls::String\n    name::String\n    carrier::String\n")
        f.write("    D::Float64      # m^2/s\n    C::Float64      # mol/m^3 (carrier)\n")
        f.write("    n::Float64      # e- per carrier turnover\n    nu::Float64     # solvent kinematic viscosity m^2/s\n")
        f.write("    Csub::Float64   # mol/m^3 substrate\n    nsub::Float64\nend\n\nconst RXNS = OERxn[\n")
        for _,r in df.iterrows():
            mu = SOLVENTS[r.solvent][1]*1e-3; rho = SOLVENTS[r.solvent][2]*1000.0
            nu = mu/rho
            f.write(f'    OERxn("{r.cls}", "{r.reaction}", "{r.carrier_type}", {r.D_cm2s*1e-4:.4e}, '
                    f'{r.C_carrier_M*1000:.1f}, {r.n_carrier}, {nu:.4e}, {r.C_substrate_M*1000:.1f}, {r.n_substrate}),\n')
        f.write("]\n")
    print(df.groupby('cls').size().to_string())
    print("\n" + "="*78)
    print("KAPPA VALUES THAT ARE ESTIMATES, NOT SOURCED NUMBERS (%d):" % len(KAPPA_ESTIMATED))
    for _k in sorted(KAPPA_ESTIMATED):
        print("  %-46s %8.3f mS/cm" % (_k[:46], ELECTROLYTES[_k]))
    print("  -> each needs a docs/KAPPA_SOURCING_DOSSIER.md row; KAPPA_ESTIMATED carries the")
    print("     derivation behind each. Do not cite these as measured.")
    print("="*78)
    print(f"\nD range: {df.D_cm2s.min():.2e} - {df.D_cm2s.max():.2e} cm2/s")
    for _p in (OUT_REACTIONS, OUT_SOLVENTS, OUT_ELECTROLYTE, OUT_RXN_TABLE):
        print("wrote", _p)   # absolute, so a run from the wrong cwd cannot be mistaken for a good one
