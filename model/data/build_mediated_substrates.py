#!/usr/bin/env python3
"""Generate the mediated-spec substrate diffusivities by Wilke-Chang, from named structures.

    /opt/anaconda3/envs/echem_analysis/bin/python data/build_mediated_substrates.py
    (needs rdkit; the base env does not have it -- see CLAUDE.md 2)

WHY THIS EXISTS
---------------
`parameters_provenance.csv` published these eight as class `derived`, method "Wilke-Chang on named
surrogate structures". But OERxn has no substrate-D field, build_reactions50.py computed none, and
the eight numbers were HAND-TYPED into julia/run_mediated.jl. Nothing reproduced them, which fails
the state-B test in PROVENANCE_STANDARD.md -- "the arithmetic reproducible from the registry
alone". Exactly the defect Casteel-Amis had before it was implemented.

WHAT THE AUDIT FOUND WHEN THE ARITHMETIC WAS ACTUALLY RUN (2026-08-24)
----------------------------------------------------------------------
Inverting Wilke-Chang gives the Le Bas volume each typed value implies, and the inversion is exact
(round-tripped against lebas_volume() on five structures, agreeing to 2 dp). Five of the eight
typed values ARE reproduced to 3-4 digits by the structure the registry names -- so those were
genuinely computed this way, and both the structure and the method are confirmed:

    levetiracetam-alcohol  ratio 1.000     propene 0.997     HMF 1.000
    1-decene               ratio 1.002     anisole 0.999

THREE WERE NOT. For those the substrate was read out of the exemplar PDF rather than guessed,
because matching a 3-significant-figure D does not identify a structure uniquely (4-fluorobenzamide
V=137.40 and cyclopentanecarboxamide V=135.90 both reproduce 2.00e-9 to 3 s.f.):

  * Hofmann -- op3c00332.pdf (Malviya/Cantillo OPRD 2023) states "the transformation of
    2-phenylacetamide 1a into carbamate 2a was selected as a model" and "concentrations of 1a of
    0.4 M", matching C_sub = 400 mol/m3. The registry's NAME was right; the typed 2.00e-9 was not
    the Wilke-Chang value for it (WC gives 1.861e-9, so the typed number ran 7.5% high).
  * NHPI -- nature17431.pdf (Horn/Baran Nature 2016) uses valencene (4) -> nootkatone (5). The
    registry's "sesquiterpene-core" is vague; valencene is the paper's model substrate. WC gives
    1.945e-9 against a typed 1.78e-9, 8.5% low.
  * Bromination -- s41467-025-57329-0.pdf (Zhang/Su Nat Commun 2025) is anisole bromination, NOT
    the "naproxen-arene" the registry named. The scale-up is "Substrate (4 mmol), solvent (0.5 M
    NaBr in deionized water (10 mL): CH3CN: CH3OH: CH2Cl2 = 10:10:10:3)": 4 mmol / 33 mL =
    0.1212 M = 121 mol/m3, which is C_sub exactly, and 0.5 M x 10/33 = 152 mol/m3, which is the
    carrier exactly. WC gives 9.148e-10 against a typed 6.25e-10 -- 46% low, the largest error of
    the three.

So the registry's blanket "Wilke-Chang on named surrogate structures" was true for five rows and
false for three, and one surrogate NAME did not match its own paper.
"""
import csv, importlib.util, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("br50", os.path.join(HERE, "build_reactions50.py"))
br = importlib.util.module_from_spec(spec); spec.loader.exec_module(br)

## reaction label (must match reactions_table.jl / run_mediated.jl), substrate, SMILES, solvent key,
## how the identity was established, and the value run_mediated.jl carried before this script
ROWS = [
 ("Br-mediated Hofmann rearrangement", "2-phenylacetamide", "NC(=O)Cc1ccccc1", "MeCN",
  "op3c00332.pdf: 'the transformation of 2-phenylacetamide 1a into carbamate 2a was selected as a "
  "model'; 'concentrations of 1a of 0.4 M' = C_sub 400 mol/m3", 2.00e-9),
 ("ACT-mediated alcohol oxidation (flow, hectogram)", "(S)-2-(2-oxopyrrolidin-1-yl)butan-1-ol",
  "CC[C@@H](CO)N1CCCC1=O", "H2O",
  "confirmed by exact reproduction of the carried value (ratio 1.000)", 7.22e-10),
 ## 2026-09-05 (author instruction): the row is Leow's HEADLINE system -- ethylene sparged into
 ## 1.0 M KCl, C_sat = ethene's measured solubility -- so the substrate is ethylene, and its
 ## diffusivity is MEASURED rather than estimated: Cussler, Diffusion 3rd ed., Table 5.2-1, p. 127,
 ## "Diffusion coefficients at infinite dilution in water at 25 C", Ethylene 1.87e-5 cm2 s-1,
 ## digits confirmed against the page raster (Bromine 1.18 on the same page is the value the
 ## registry's Br2 (aq) row already carries). Under the four-state rule a measured value with a
 ## locator displaces a derived one. Wilke-Chang on ethene gives 1.74e-9, 7 pct below the
 ## measurement; it is still computed and recorded beside the measured value for the record.
 ## Until this date the row carried PROPENE's Wilke-Chang value (1.366e-9) under an ethylene label
 ## with ethene's solubility -- an inconsistency, not a wrong number.
 ("Cl-mediated ethylene epoxidation", "ethylene", "C=C", "H2O",
  "MEASURED: Cussler, Diffusion: Mass Transfer in Fluid Systems, 3rd ed., Table 5.2-1 p. 127 "
  "(infinite dilution in water, 25 C), Ethylene 1.87e-5 cm2 s-1 = 1.87e-9 m2 s-1; read from the "
  "page raster 2026-09-05. Substrate is Leow's headline alkene (1.0 M KCl, ethylene sparged); the "
  "solubility this row carries is ethene's (IUPAC SDS vol. 57)", 1.3663e-9,
  {"D_m2s": 1.87e-9, "source": "Cussler 3rd ed. Table 5.2-1 p. 127"}),
 ("NHPI-mediated allylic C-H -> enone", "valencene", "CC1CCC=C2CCC(CC12C)C(C)=C", "acetone",
  "nature17431.pdf: valencene (4) -> nootkatone (5), the paper's model substrate. The SMILES is the decalin of "
  "Horn Fig. 2a (C15H24); until 2026-10-06 it encoded a C14H22 hydrindane, which put D_S 4 pct high", 1.78e-9),
 ("HMF -> FDCA (biomass)", "5-hydroxymethylfurfural", "OCc1ccc(C=O)o1", "H2O",
  "confirmed by exact reproduction of the carried value (ratio 1.000)", 9.52e-10),
 ("BQ-mediated Wacker-Tsuji oxidation", "1-decene", "C=CCCCCCCCC", "MeCN/H2O",
  "confirmed by exact reproduction of the carried value (ratio 1.002)", 1.17e-9),
 ("Br- oxidation / electrophilic bromination", "anisole", "COc1ccccc1", "H2O/MeCN 1:1",
  "s41467-025-57329-0.pdf: anisole is brominated in the H-cell (Methods; Fig 4), 0.5 mmol in 7.5 mL MeCN + "
  "7.5 mL 0.5 M aqueous NaBr = 0.0333 M substrate, 0.25 M Br-, water/MeCN 1:1 v/v", 6.25e-10),
 ("Aryl thiocyanation (NH4SCN)", "anisole", "COc1ccccc1", "AcOH/HCOOH",
  "confirmed by exact reproduction of the carried value (ratio 0.999)", 6.91e-10),
 ## Three rows carried as mediated since 2026-10-05, when each exemplar was read for the species
 ## that exchanges electrons with the electrode. `None` in the last slot: no typed value preceded
 ## these, so there is nothing to compare the Wilke-Chang result against.
 ("Amidyl-radical C-H amination (phenanthridinone)", "N-(pivaloyloxy)biphenyl-2-carboxamide",
  "CC(C)(C)C(=O)ONC(=O)c1ccccc1-c1ccccc1", "MeCN",
  "ol8b00981.pdf: 'the pivaloyloxy group (OPiv) proved to be the optimal substituents to furnish "
  "the lactam (2e)', i.e. the N-OPiv biaryl amide is the model substrate", None),
 ("Cathodic Giese (R-I + alkene)", "2-iodopropane", "CC(C)I", "H2O/MeCN",
  "d0sc01694b.pdf: 'the reaction of isopropyliodide with phenylvinylsulfone under the optimal "
  "conditions'; the relay the exemplar proposes activates the iodide (1.43 mmol), so it is the substrate of "
  "the solution step; the sulfone (1.19 mmol) is the limiting reagent of the product",
  None),
 ("Thioether -> sulfone (kilo-scale)", "4-methyl-2-(methylthio)pyrimidine", "CSc1nccc(C)n1",
  "MeCN/H2O",
  "op2c00111.pdf Scheme 1C (p. 2424) draws thioether 1 as 4-methyl-2-(methylthio)pyrimidine, oxidized to "
  "sulfoxide 2 and sulfone 3 (C6H8N2S; read from the page raster)", None),
 ## reclassified from the catalyst rows on 2026-10-05 (a triarylamine is an outer-sphere mediator); same molecule, same method
 ("Oxazole synthesis from ketones and acetonitrile", "benzyl phenyl ketone", "O=C(Cc1ccccc1)c1ccccc1", "MeCN",
  "ol2c02252.pdf: 'benzyl phenyl ketone (1a) was chosen as the model substrate'", None),
]

def main():
    out = os.path.join(HERE, "mediated_substrates.csv")
    rows = []
    print("%-46s %-26s %10s %10s %7s" % ("reaction", "substrate", "D_WC", "was", "ratio"))
    for row in ROWS:
        label, name, smi, solv, prov, old = row[:6]
        new_row = old is None
        measured = row[6] if len(row) > 6 else None
        Dcm2, V = br.wilke_chang(smi, solv)
        D_wc = Dcm2 * 1e-4
        ## a MEASURED, page-anchored value displaces the estimate; the estimate stays in its own
        ## column so the two can be compared (G-DSUB binds the solver to D_sub_m2s only)
        D = measured["D_m2s"] if measured else D_wc
        if new_row:
            old = D
        method = ("measured (%s)" % measured["source"]) if measured else "Wilke-Chang"
        rows.append(dict(reaction=label, substrate=name, smiles=smi, solvent=solv,
                         lebas_V_cm3mol="%.2f" % V, D_sub_m2s="%.4e" % D,
                         previous_typed_value=("" if new_row else "%.4e" % old),
                         ratio_new_over_old=("" if new_row else "%.4f" % (D / old)), identified_by=prov,
                         method=method, D_wilke_chang_m2s="%.4e" % D_wc))
        print("%-46s %-26s %10.4g %10.4g %7.3f  %s" % (label[:46], name[:26], D, old, D / old, method))
    with io.open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("\nwrote -> data/mediated_substrates.csv")

if __name__ == "__main__":
    main()
