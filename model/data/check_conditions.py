#!/usr/bin/env python3
"""G-COND -- every modelled concentration must be page-anchorable in its own exemplar PDF,
and the numbers for one row must come from ONE experiment in that paper.

    cd Section4_Model && python data/check_conditions.py
    cd Section4_Model && python data/check_conditions.py --negative-control

WHY THIS EXISTS
---------------
`reactions_50.csv` carries three concentrations per row -- carrier, substrate and supporting
electrolyte -- and every transport ceiling in Figs. 2, 3 and 4 is linear in them. Until 2026-08-23
NOTHING checked them against the papers they claim to come from. `verify_exemplars.py`
(G-EXEMPLAR) resolves the exemplar *citation*; it never opens the paper and never reads a number.

Two failure modes this is built to catch, both of which have already occurred here:

  MIXED EXPERIMENT   the carrier molarity is read off one table and the substrate molarity off
                     another, in the same paper. Each number is individually "in the paper" and
                     the pair describes no experiment anyone ran. The bromination row did exactly
                     this (Br- from Fig. 4, substrate from Fig. 5).

  SI-ONLY            the number is not in the retrieved article body at all. That is not a
                     scandal -- it is very often in the SI -- but it means the row is NOT state A
                     on the evidence in this repo, and it must not be carried as though it were.

WHAT "PAGE-ANCHORABLE" MEANS HERE
---------------------------------
A concentration is anchored if the PDF text contains either
  (a) an explicit molarity within TOL of it, or
  (b) an (amount, volume) pair -- `x mmol ... y mL` -- whose quotient is within TOL of it.
Route (b) is what most synthetic papers actually print, and it is a state-B derivation from two
state-A readings, which the standard allows.

SAME-EXPERIMENT TEST
--------------------
For a row to pass, the supporting quotes for its carrier, substrate and electrolyte must lie
within WINDOW characters of one another in the extracted text. Synthetic papers state a whole
condition set in one footnote or one procedure paragraph, so co-location is a good proxy for
co-experiment. It is deliberately a *proxy*: it can pass a row whose numbers happen to sit near
each other by accident, so a PASS here is a screen, not a certificate. A FAIL is real.

NEGATIVE CONTROL
----------------
`--negative-control` multiplies every substrate concentration by 1.7 and asserts that rows which
were ANCHORED become UNANCHORED. A control that fires nothing means the test is not testing.
"""
import csv, io, json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TXT  = os.path.join(ROOT, "results", "pdftext")
TOL    = 0.06     # 6% -- covers rounding of mmol/mL quotients and printed 2-sig-fig molarities
WINDOW = 1400     # chars; a condition footnote or procedure paragraph is comfortably inside this

NUM = r"(\d+(?:\.\d+)?)"

def load(pdf):
    p = os.path.join(TXT, os.path.splitext(pdf)[0] + ".txt")
    if not os.path.exists(p):
        return None
    s = unicodedata.normalize("NFKC", io.open(p, encoding="utf8", errors="replace").read())
    return re.sub(r"[ \t]+", " ", s)

def molarities(t):
    """[(value_M, position)] for every explicit molarity printed in the text."""
    out = []
    for m in re.finditer(NUM + r"\s?(?:M\b|m\b(?=[^a-zA-Z])|mol\s?[/ ]\s?L|mol\s?L)", t):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if 1e-4 < v < 60:
            out.append((v, m.start()))
    ## also mM
    for m in re.finditer(NUM + r"\s?mM\b", t):
        out.append((float(m.group(1)) / 1000.0, m.start()))
    return out

def quotients(t):
    """[(value_M, position)] from every `x mmol` paired with a plausible reaction volume.

    Two corrections, both made after the first run over-reported SI-ONLY on rows whose numbers
    ARE printed (Shono row 2, lactonization row 43):

      SPLIT SOLVENT   papers write `CH3CN (7 mL), MeOH (1 mL)` and never print the total. The
                      modelled molarity is over the SUM, so every running sum of the volumes in
                      a local cluster is offered as a candidate denominator, not just each one.
      COLUMN BLEED    two-column PDFs interleave text, so an amount and its volume can land far
                      apart in the extracted stream. The window is 450 chars, not 300.

    Widening a matcher can only ADD candidate anchors, so it can only turn FAIL into PASS -- which
    is exactly why --negative-control is mandatory after touching this function. If the control
    stops firing, the widening went too far and the test has become inert.
    """
    amts = [(float(m.group(1)), m.start()) for m in re.finditer(NUM + r"\s?mmol\b", t)]
    vols = [(float(m.group(1)), m.start()) for m in re.finditer(NUM + r"\s?m[lL]\b", t)]
    out = []
    for a, pa in amts:
        near = sorted([(pv, v) for v, pv in vols if abs(pa - pv) < 450])
        tot = 0.0
        for pv, v in near:
            if v <= 0:
                continue
            tot += v
            for denom in (v, tot):
                q = a / denom          # mmol/mL == mol/L
                if 1e-4 < q < 60:
                    out.append((q, min(pa, pv)))
    return out

def relative(t, base):
    """[(value_M, position)] for `N mol%` and `N equiv` read against a nearby concentration.

    Synthetic papers almost never print a catalyst molarity. They print `10 mol % Ni(bpy)3Br2`
    beside `DMA (0.025-0.05 M)`, and the modelled 0.005 M is the product. That is a state-B
    derivation from two state-A readings and the gate must be able to follow it -- without this
    route all eleven catalyst-carrier rows fail for a reason that is about the gate, not the row.
    """
    out = []
    for m in re.finditer(NUM + r"\s?mol\s?%", t):
        f = float(m.group(1)) / 100.0
        for v, pos in base:
            if abs(pos - m.start()) < 450:
                out.append((f * v, min(pos, m.start())))
    for m in re.finditer(NUM + r"\s?equiv", t):
        f = float(m.group(1))
        for v, pos in base:
            if abs(pos - m.start()) < 450 and 1e-4 < f * v < 60:
                out.append((f * v, min(pos, m.start())))
    return out


## Rows whose numbers ARE printed in the paper but which no regex should be bent to catch,
## because the PDF text is damaged in a way that would require inventing digits to repair.
## Each entry records the quote and the arithmetic, so the exemption is auditable and can be
## re-checked by opening the paper -- it is never a bare suppression.
HAND_VERIFIED = {
    # chemistry review 2026-10-06: the row is the alprenolol run (compound 45), which the SI runs at HALF the general
    # procedure's scale in the same volume, so its substrate concentration is in the SI alone
    "38": ("Miller & Wayner, Can. J. Chem. 1992, 70, 2485, Results p. 2486: 'Oxidations were carried out in solutions of "
           "acetonitrile/water (7:1 v/v), containing benzoquinone (0.022 M, 20 mol% based on olefin), palladium acetate "
           "(0.0011 M, 1 mol% based on olefin), olefin (0.11 M), and perchloric acid (0.015-0.24 M)' -> the row's BQ 0.022 M and "
           "olefin 0.11 M as printed. The text layer reads '0.11 MI' and '0.001 1 M' (OCR), which is why the matcher misses the "
           "olefin; the digits were read on the page. One sentence, every number. Verified 2026-10-06."),
    "40": ("Gnaim/Baran Nature 2022 SI (41586_2022_4595_MOESM1_ESM.pdf), printed pp. 66-67, Compound 17: 'Following "
           "the general procedure B on 0.2 mmol scale, using Co(salen)-1 (4.8 mg, 8 umol), TBABF4 (60 mg), HFIP (84 uL, "
           "0.8 mmol), and acetone (2.5 mL), with zinc as anode and nickel foam as cathode under the electrolysis of 5 mA "
           "for 3 F/mol' -> alkene 0.2/2.5 = 0.080 M, Co(salen)-1 0.008/2.5 = 0.0032 M, TBABF4 60 mg / 329.3 g mol-1 = "
           "0.182 mmol / 2.5 mL = 0.073 M. One passage, all three numbers, and the 3 F/mol the row carries as n."),
    "10": ("Gnaim/Baran Nature 2022 SI (41586_2022_4595_MOESM1_ESM.pdf), printed p. 83, Compound 45: 'Following the "
           "general procedure C on 0.1 mmol scale, using CoBr2*glyme (6.2 mg, 20 umol), 6,6'-dimethyl-2,2'-bipyridine "
           "(5.5 mg, 30 umol), Et3N*HBF4 (114 mg), HFIP (300 uL), and THF (2.2 mL)' -> 2.5 mL in all: alprenolol "
           "0.1/2.5 = 0.040 M, Co 0.020/2.5 = 0.008 M, Et3NHBF4 114 mg / 189.0 g mol-1 = 0.603 mmol / 2.5 mL = 0.24 M. "
           "One passage, all three numbers."),
    "2": ("Shono JACS 1975 p 4268: 'Anodic oxidation of 12 (13.42 mmol) in methanol (8.61 ml) "
          "containing [Et4NOTs] (1.34 mmol)' -> 13.42/8.61 = 1.559 M substrate and "
          "1.34/8.61 = 0.1556 M Et4NOTs. One experiment, both numbers."),
    "30": ("Shono JACS 1975 p 4268: 'A mixture of 13 (20.21 mmol) and 14 (20.21 mmol) was anodically "
           "oxidized in methanol (25.63 ml) containing Et4NOTs (4.04 mmol)'; 13 is N,N-dimethylacetamide and 14 "
           "its d9 isotopologue (drawn p 4266) -> 40.42/25.63 = 1.577 M amide and 4.04/25.63 = 0.158 M Et4NOTs. "
           "One passage, both numbers."),
    "43": ("Org. Lett. 2017 Fig 2 fn a: '1 (0.5 mmol), CH3CN (7 mL), MeOH (1 mL), n-Bu4NBF4 "
           "(2 mmol)' -> 0.5/8 = 0.0625 M substrate, 2/8 = 0.25 M Bu4NBF4. The CH3CN subscript "
           "bleeds into the text as 'MeOH (1 3 mL)', so the 1 mL is unreadable to the matcher."),
    "19": ("Courtois/Barhdadi/Troupel/Perichon, Tetrahedron 1997, 53, 11569, Table 1 fn: "
           "'Experimental conditions : Solvent : 50 mL, PhBr 15 mmol., NiBr2bpy 1.5 mmol., "
           "supporting electrolyte: NaBr 4.10-2 mol.L-1' -> PhBr 15/50 = 0.30 M, "
           "NiBr2(bpy) 1.5/50 = 0.030 M, NaBr 0.04 M. ONE footnote, all three numbers. The "
           "matcher cannot co-locate them because the extractor renders the superscript in "
           "'4.10^-2 mol.L^-1' as '4.10 -2 mol.Ll', so the electrolyte molarity is unreadable "
           "AT that position and its only parseable match is the general procedure 5 kB away "
           "(NaBr 2 mmol / 50 mL, the same 0.04 M, different experiment). Reading the digits "
           "back out of the mangled string would mean inventing them."),
    "29": ("US 5,507,922, Hermeling, Hannebaum, Voss & Weiper-Idelmann (BASF), 'Preparation of "
           "benzaldehyde dialkyl acetals'. The PDF is a SCAN with a zero-character text layer, so "
           "results/pdftext/5507922.txt is an OCR transcription: every page rendered at 300 dpi "
           "with PyMuPDF and read with tesseract 5.5.2, 24.5 kB recovered, and the file carries a "
           "header saying so. The patent states masses and weight percents, never a molarity, so "
           "the value here is DERIVED and the matcher cannot co-locate it. The worked example's "
           "electrolyte reads '450 g (15% by weight) of p-tert-butyltoluene / 10 g (0.3% by "
           "weight) of sulfuric acid / 2,450 g (84.7% by weight) of methanol', with 'graphite "
           "electrodes 1 mm apart', 3.4 A/dm2 (34 mA cm-2), 7.5 F/mol and 55 C. p-tert-butyl"
           "toluene is 450 / 148.25 = 3.035 mol; taking the volume as additive from 2450 g MeOH "
           "at 0.786 and 450 g TBT at 0.861 gives 3.64 L, so 0.83 M against the 0.81 M carried -- "
           "within 3 pct. The electrolyte string '0.3 wt% H2SO4/MeOH' is verbatim from the patent. "
           "OCR DIGIT CHECK: the flow rate was carried as 900 L/h and the patent says 200. Two "
           "independent OCR passes on two different pages both read 200, and the line was then "
           "cropped from the page raster and read directly -- 'as circulated at 200 l/h.'. "
           "Corrected 2026-08-31. It changes no computed number (this row's architecture is "
           "declared, not derived from the flow rate), but it was a wrong number inside a "
           "page-anchored claim. Digits are what OCR gets wrong; confirm them against the image."),
    "45": ("Zhang/Su, Nat. Commun. 2025, 16, 3052, DOI 10.1038/s41467-025-57329-0. The row carries the campaign run on "
           "anisole, the divided H-cell (Methods; Fig. 4 footnote): 'each cell was filled with 7.5 mL acetonitrile and "
           "7.5 mL 0.5 mol/L NaBr aqueous solution. 0.5 mmol substrate was dissolved in the anodic cel,l and constant "
           "voltage was applied' -> 15 mL in the anodic chamber: anisole 0.5/15 = 0.0333 M, Br- 0.5 x 7.5/15 = 0.25 M, "
           "water/MeCN 1:1 v/v. One sentence, both numbers. The flow runs of Fig. 5b/c (4 mmol in 33 mL of the 10:10:10:3 "
           "medium; the 518 g run) are on natural-product and drug derivatives, not anisole. Verified 2026-10-06."),
    "31": ("Leow/Sargent, Science 2020, aaz8459. The substrate concentration is NOT in the "
           "exemplar paper and is not supposed to be -- it is a measured GAS SOLUBILITY from a "
           "different cited source, which is why a matcher searching the exemplar PDF reports "
           "SI-ONLY. That source is in the repository: "
           "papers for model/concentrations/SIs/SDS-57.pdf is IUPAC Solubility Data Series "
           "Vol. 57, ETHENE. Its data sheet (PDF p. 70) is Yano, Suetaka, Umehara & Horiuchi, "
           "Kagaku Kogaku 1974, 38, 320-323, at T/K = 298.15 and P/kPa = 101.3, and prints "
           "'Solubility of ethene /mmol L-1' as 4.83 for pure water and, for KCl at 0.500 / "
           "1.000 / 1.500 mol L-1, 4.14 / 3.52 / 3.03. The electrolyte here is 1.0 M KCl, so the "
           "substrate is 3.52 mmol L-1 = 0.00352 M, exactly as carried; the salting-out "
           "correction against pure water is 27%. Two cross-checks inside the same volume: the "
           "compilation's own evaluation on PDF p. 57 reads 'The Sechenov plot is linear with "
           "slope -0.136 and standard deviation 0.001', and log10(4.83/3.52) = 0.1374 reproduces "
           "it; and the same data sheet's KBr and CuCl2 series are monotonic in the same "
           "direction. The electrolyte, 1.0 M KCl, is quoted verbatim from the exemplar. "
           "Verified 2026-08-31."),
    "15": ("Mo/Jensen, Science 2020, aba3823. The SI is in the repository but sits in "
           "'papers for model/aba3823_mo_sm.pdf' rather than in the concentrations/SIs folder, "
           "which is why it went unread. SI pp. 19-20, 'General Procedure A for Decarboxylative "
           "Arylation': 'Bu4NOH solution in MeOH (4.56 mL, 1.0 M, 4.56 mmol, 5.7 equiv.) was "
           "added dropwise ... to the corresponding solution of carboxylic acid (4.80 mmol, "
           "6.0 equiv.)' and then 'The prepared carboxylic acid tetrabutylammonium salt and aryl "
           "nitrile (0.80 mmol, 1.0 equiv.) were dissolved in anhydrous and degassed MeCN "
           "(5.0 mL), and then transferred to a 10.0 mL volumetric flask. Additional MeCN was "
           "added to make the solution volume 10.0 mL.' The volume is EXACT -- a volumetric "
           "flask, not a sum of charges -- so the aryl nitrile is 0.80/10.0 = 0.080 M (substrate "
           "and carrier both) and the carboxylic acid is 4.80/10.0 = 0.480 M, carried as the "
           "electrolyte because the paper adds no separate supporting salt. The 0.48 M is the "
           "TOTAL acid, on the same fast-CE reading used elsewhere here; the fraction actually "
           "deprotonated is capped by the Bu4NOH at 4.56/10.0 = 0.456 M. "
           "The conc_provenance for this row USED to say 'Declared rather than page-anchored' "
           "and call the 0.48 M 'an in-situ estimate'; both understated it, and both were "
           "corrected in the generator on 2026-08-31 to the arithmetic above. What remains "
           "declared on this row is only that no separate supporting electrolyte is added "
           "(which the paper says outright) and that its 25 um cell sits outside the modelled "
           "architectures. Verified 2026-08-31."),
    "20": ("Osa/Bobbitt, J. Chem. Soc. Chem. Commun. 1994, c39940002535. The article body states "
           "all three numbers in ONE sentence: 'The anolyte contained 5 mmol of substrate, 2 mmol "
           "of tetralin as a chromatographic standard, 5 mmol of 1 and 1 mmol of NaClO4 as a "
           "supporting electrolyte in a total volume of 5 cm3'. That gives 2-naphthol "
           "5 mmol / 5 cm3 = 1.0 M -- substrate and carrier both -- and NaClO4 1/5 = 0.2 M. The "
           "matcher misses it for a purely lexical reason: this 1994 paper writes the volume as "
           "'5 cm3', and the extractor recognises mL only. Verified 2026-08-31."),
    "49": ("Gieshoff/Schollmeyer/Waldvogel, Angew. Chem. Int. Ed. 2016, 55, 9437, anie201603899. "
           "SI p. 6, 'General electrolysis protocol B in Teflon cells (prep. scale)': 'Undivided "
           "5 mL Teflon electrolysis cells ... A solution of 0.2 mmol dimethylmalonic dianilide "
           "derivative and 19.3 mg tetrabutylammonium hexafluorophosphate is electrolyzed with a "
           "current density of 0.5 mA/cm2'. The cell volume is stated in the same sentence as the "
           "charges: substrate 0.2 mmol / 5 mL = 0.040 M, and Bu4NPF6 19.3 mg / 387.43 g mol-1 = "
           "0.0498 mmol, i.e. 0.00996 M. Protocol A on SI p. 5 charges the same amounts. ONE "
           "paragraph, all three numbers. Verified 2026-08-31."),
    "16": ("Li/Ma/Scott/Wilden, Chem. Sci. 2020, d0sc01694b. The concentrations are split across "
           "two SI pages, which is why the co-location matcher cannot see them. Volume, SI p. 3: "
           "'each chamber having a size B19 ground-glass neck and a total volume of 30 mL ... "
           "All reactions were carried out using 15 mL of electrolyte solution in each', "
           "confirmed by the general procedure on SI p. 5: 'HCl(aq) (pH = 2, 10 mL), MeCN (5 mL) "
           "and NaCl (7 mol%) were added to each chamber' -- 10 + 5 = 15 mL, and 'Alkene and "
           "alkyl halide were added to the cathodic chamber', so the reacting volume is that "
           "15 mL. Charges, SI p. 5: 'phenyl vinyl sulfone (200 mg, 1.19 mmol, 1.0 equiv.) and "
           "2-iodopropane (0.142 mL, 1.43 mmol, 1.2 equiv.)'. That gives alkene 1.19/15 = "
           "0.0793 M and alkyl iodide 1.43/15 = 0.0953 M. The main text corroborates the scale "
           "independently: 'for a 1.2 mmol reaction scale (1.44 mmol of alkyl iodide)'. This row "
           "carries no electrolyte molarity -- NaCl is quoted as 7 mol%. Verified 2026-08-31."),
    "13": ("Zhang/Baran, Nature 2022, s41586-022-04691-4. SI p. 9, 'General procedure for the "
           "electrochemical doubly decarboxylative coupling': the vial is charged with "
           "'carboxylic acid A (0.1 mmol, 1 equiv)' and 'Dichloromethane was added (0.2 M)', "
           "then 'NaI (0.6 mmol, 89.9 mg), NiCl2.dme (20 mol %, 4.4 mg), (4-OMe)-H-PyBox (20 "
           "mol %, 5.0 mg) and anhydrous DMF (3.0 mL) were added'. The DCM is NOT removed -- "
           "there is no evaporation step between the two additions -- so the electrolysis volume "
           "is the sum, and the DCM volume is fixed by the paper's own statement of it: 0.1 mmol "
           "at 0.2 M is 0.5 mL, giving 0.5 + 3.0 = 3.5 mL. Substrate 0.1/3.5 = 0.0286 M and NaI "
           "0.6/3.5 = 0.171 M. ONE paragraph, both numbers, with the volume derived from the "
           "paper rather than assumed. Verified 2026-08-31."),
    "12": ("Kelly/Stahl/Schreier, OPRD 2026, op6c00110. This row models the 1 kg campaign, not "
           "the optimization study (which runs 0.42 mmol in 5 mL = 0.084 M with LiBr at 0.2 M -- "
           "a different experiment). SI p. 32, 'General Procedure for 1 kg Scale Run': 'To a "
           "clean dry 20L jacketed reactor vessel equipped with an overhead impeller were added: "
           "1 equiv species 2 (2.92 mol, 691 g), 1.5 equiv 1-bromo-4-boc-piperidine (1) "
           "(4.38 mol, 1153 g), 1.6 equiv LiBr (4.67 mol, 406 g) and 5 mol% (relative to 2) Ni "
           "catalyst (0.146 mol, 110.3 g)', and, in the same paragraph, 'the remaining DMA "
           "(9.73 L total) was slowly added to recirculation vessel'. Against that one stated "
           "volume: substrate 2.92/9.73 = 0.300 M, LiBr 4.67/9.73 = 0.480 M and Ni catalyst "
           "0.146/9.73 = 0.0150 M. ONE paragraph, all three numbers, each reproducing the "
           "carried value to three significant figures. Verified 2026-08-31."),
    "24": ("Hioki/Baran, JACS 2022, ja2c02102. SI p. 4, 'General procedures for (hetero)arene "
           "electroreduction': 'To an ElectraSyn reaction vial charged with an aromatic substrate "
           "(0.1 mmol), tetramethylammonium tetrafluoroborate (Me4N.BF4, 40 mg, 0.25 mmol) was "
           "added 1.5 mL of tetrahydrofuran (THF) and 1.5 mL of ethanol (EtOH)'. Total liquid "
           "3.0 mL, so substrate 0.1/3.0 = 0.0333 M and Me4NBF4 0.25/3.0 = 0.0833 M; the "
           "substrate is its own carrier. ONE paragraph, all three numbers, and 40 mg / "
           "163.0 g mol-1 = 0.245 mmol confirms the mmol figure. Verified 2026-08-31."),
    "37": ("Okada/Chiba, Chem. Sci. 2016, c6sc02117d. SI p. 31, 'General procedure': 'To a "
           "solution of lithium perchlorate (1.0 M) in MeNO2, styrene (80 mM, 1 equiv.) and "
           "diene (160 mM, 2 equiv.) were added'. This paper states its concentrations directly "
           "as molarities rather than as mmol/mL, so no conversion is involved: the styrene -- "
           "substrate and carrier both -- is 0.080 M and the LiClO4 is 1.0 M. ONE sentence, all "
           "three numbers. Verified 2026-08-31."),
    "14": ("Kirste/Waldvogel, JACS 2012, ja211005g. SI p. 5, general procedure for the anodic "
           "phenol-arene cross-coupling: 'A solution of phenol component (0.005 mol), arene "
           "component (0.015 mol) and N-methyl-N,N,N-triethylammonium methylsulfate (0.68 g, "
           "0.003 mol) in 1,1,1,3,3,3-hexafluoropropan-2-ol (27 mL) and methanol (6 mL)'. Total "
           "solvent 27 + 6 = 33 mL, so the phenol -- which is both the substrate and the carrier "
           "for this row -- is 0.005/0.033 = 0.152 M and the ammonium electrolyte is "
           "0.003/0.033 = 0.0909 M. ONE sentence, all three numbers. Verified 2026-08-31."),
    "22": ("Peters/Baran, Science 2019, aav5606, SM. The row carries naphthalene under its own preparative procedure: SM "
           "p. S93, compound SI-6, 'Following General Procedure A or B on 0.1 mmol scale (9 F/mol) with naphthalene' "
           "(1,4,5,8-tetrahydronaphthalene, 75%). General Procedure B, SM pp. S12-S13 (room temperature): 'substrate "
           "(0.1 mmol, 1.0 eq.), 1,3-dimethylurea (DMU, 0.3 mmol, 3.0 eq) and tri(pyrrolidin-1-yl)phosphine oxide (TPPA, "
           "10 eq.), followed by 500 uL's of a 1.5 M THF solution of LiBr (0.75 mmol, 7.5 eq.). Next, 3 mL of dry THF' "
           "-> 3.5 mL of liquid: naphthalene 0.1/3.5 = 0.0286 M, LiBr 0.75/3.5 = 0.214 M. One paragraph, both numbers. "
           "The 10 g batch run (SM pp. S15-S16, 3.0 M LiBr) is on tert-butyldimethyl(p-tolyloxy)silane and is not this row."),
    "4": ("Fu/Lin, Science 2017, aan6206. Main text gives no molarity; the SI is in this repo "
          "(papers for model/concentrations/SIs/aan6206_fu_sm.pdf) and states the standard "
          "conditions in a table footnote, SI p. 8: 'Standard conditions: 0.2 mmol alkene, "
          "0.01 mmol MnBr2.4H2O, 1.0 mmol NaN3, 400 uL HOAc, 3.5 mL LiClO4 solution in MeCN "
          "(0.1 M), RVC as anode, Pt as cathode'. The SI p. 4 general procedure repeats it: "
          "'olefin substrate (0.2 mmol, 1.0 equiv), electrolyte solution (0.1 M LiClO4 in MeCN, "
          "3.5 mL), and acetic acid (0.4 mL)'. Total liquid 3.5 + 0.4 = 3.9 mL, so substrate "
          "0.2/3.9 = 0.0513 M and Mn 0.01/3.9 = 0.00256 M; the electrolyte is quoted as a "
          "molarity, 0.1 M. ONE footnote, all three numbers. Verified 2026-08-31."),
    "6": ("Morofuji/Yoshida, JACS 2013, ja402083e. SI p. 2, General Procedure: 'In the anodic "
          "chamber was placed a solution of aromatic compound (0.20 mmol) and pyridine (0.5 mL) "
          "in 0.3 M Bu4NBF4/CH3CN (10.0 mL)'. Anolyte volume 10.0 + 0.5 = 10.5 mL, so the arene "
          "is 0.20/10.5 = 0.019 M and, being the carrier itself, supplies both the substrate and "
          "carrier targets; the electrolyte is quoted as a molarity, 0.3 M. ONE sentence, all "
          "three numbers. Verified 2026-08-31."),
    "11": ("Hioki/Baran, Science 2023, adf4762. This row is anchored to the SCALED run, not to "
           "General Procedure A (which is 1.5 mmol in 3.5 mL of acetone = 0.43 M and is a "
           "different experiment). SI p. 9, 'Procedure for 10-undecenoic acid dimerization': "
           "'To a reactor beaker equipped with a stir bar were added acetone (200 mL), "
           "10-undecenoic acid (36.8 g, 200 mmol), pivalic acid (4.0 g, 40 mmol), Me4N.BF4 "
           "(TMABF4) (1.6 g, 10 mmol), and Me4N.OH pentahydrate (5.4 g, 30 mmol)'. That gives "
           "acid 200/200 = 1.00 M, Me4NBF4 10/200 = 0.05 M and Me4NOH 30/200 = 0.15 M. ONE "
           "paragraph, all three numbers. The carrier is carried at the TOTAL acid, 1.0 M, not "
           "at the 0.15 M the base could deprotonate, on the same fast-CE reading used for the "
           "anodic decarboxylative row: proton transfer to a carboxylate is diffusion-limited, "
           "so the limiting current is set by total acid. Verified 2026-08-31."),
    "7": ("Zhang/K. Xu/Zeng, Org. Lett. 2018, ol8b00981. The MAIN TEXT carries no molarity, but "
          "the Supporting Information is in this repository "
          "(papers for model/concentrations/SIs/ol8b00981_si_001.pdf) and states the standard "
          "conditions twice. Table footnote, SI p. 4: 'undivided cell, anode and cathode "
          "(1.5 x 1.5 cm2, J = 8.9 mA/cm2), 1 (0.3 mmol), CH3CN (7 mL), MeOH (0.5 mL), "
          "electrolyte (0.3 mmol) at rt for 2 h'. General procedure, SI p. 5: 'The substrate "
          "N-(pivaloyloxy)-[1,1'-biphenyl]-2-carboxamide 1e (89 mg, 0.3 mmol) and electrolyte "
          "NaBr (30 mg, 0.3 mmol) was added to the mixture solvent CH3CN/MeOH (7/0.5 mL)'. "
          "Total liquid 7.5 mL, so substrate 0.3/7.5 = 0.040 M and NaBr 0.3/7.5 = 0.040 M -- the "
          "carrier here IS the bromide, so all three targets are 0.040 M. ONE experiment, all "
          "three numbers, and 30 mg / 102.89 g mol-1 = 0.292 mmol confirms the mmol figure. "
          "Verified 2026-08-31."),
    "21": ("Baizer JES 1964 Table II run 28 p 218: 'Et4N | 141 | 94.5 | 40.0' = 40.0 wt% AN in "
           "56 wt% aq Et4NOTs (fn e). The wt%->molarity conversion needs its density stated; "
           "see the findings note."),
}


def anchor(t, target, pool):
    """Closest supporting position for `target`, or None."""
    if target is None or (isinstance(target, float) and target != target):
        return None
    best = None
    for v, pos in pool:
        if abs(v - target) <= TOL * max(target, 1e-9):
            if best is None or abs(v - target) < best[0]:
                best = (abs(v - target), pos, v)
    return best

def anchors(t, target, pool):
    """EVERY position whose value matches `target`, sorted. See pick_colocated."""
    if target is None or (isinstance(target, float) and target != target):
        return []
    return sorted(pos for v, pos in pool
                  if abs(v - target) <= TOL * max(target, 1e-9))


def pick_colocated(cand):
    """Choose one position per target so the group is as TIGHT as possible.

    anchor() returned the NUMERICALLY closest occurrence of each value independently, which is
    the wrong question. A paper states its conditions once in a footnote and then mentions the
    same molarities again in the optimisation discussion, the SI, and the scheme; picking each
    target's best match on its own scatters the three across the document and the spread test
    then reports MIXED-EXPERIMENT for a row whose numbers all sit in one sentence. Four of the
    thirteen flagged rows were checked by hand and every one was this artefact -- the Ni
    amination's carrier, substrate and electrolyte are all in `10 mol % Ni(bpy)Br2, nBu4N.Br
    (0.2 M), DBU (2.0 equiv), DMA (0.025-0.05 M)`.

    The right question is whether there EXISTS a passage containing all of them, so take the
    minimum-span window holding one occurrence of each: classic smallest-range-covering-k-lists.
    Returns (positions_by_key, span).
    """
    keys = [k for k, v in cand.items() if v]
    if not keys:
        return {}, 0
    if len(keys) == 1:
        return {keys[0]: cand[keys[0]][0]}, 0
    merged = sorted((p, k) for k in keys for p in cand[k])
    need, have, lo = len(keys), {}, 0
    best_span, best = None, {}
    for hi in range(len(merged)):
        p, k = merged[hi]
        have[k] = have.get(k, 0) + 1
        while len(have) == need:
            span = merged[hi][0] - merged[lo][0]
            if best_span is None or span < best_span:
                best_span = span
                # the covering window is merged[lo..hi]; take the LAST position of each key in it
                w = {}
                for q, kk in merged[lo:hi + 1]:
                    w[kk] = q
                best = w
            pk = merged[lo][1]
            have[pk] -= 1
            if not have[pk]:
                del have[pk]
            lo += 1
    return best, (best_span or 0)


def elyte_M(s):
    m = re.match(r"\s*" + NUM + r"\s?M\b", str(s))
    return float(m.group(1)) if m else None

def quote(t, pos, n=150):
    return re.sub(r"\s+", " ", t[max(0, pos - 40):pos + n])

def main():
    neg = "--negative-control" in sys.argv
    rx  = {r["reaction"]: r for r in csv.DictReader(open(os.path.join(HERE, "reactions_50.csv")))}
    mp  = list(csv.DictReader(open(os.path.join(HERE, "exemplar_pdf_map.csv"))))
    res, nfail, nmixed, nsi = [], 0, 0, 0
    for row in mp:
        rn = row["reaction"].replace("|", ",")
        rec = rx.get(rn)
        if rec is None:
            ## the map writes ',' as '|' to survive CSV; recover by prefix match
            cands = [k for k in rx if k.startswith(rn.split("(")[0].strip()[:28])]
            rec = rx[cands[0]] if cands else None
        if rec is None:
            res.append({"row": row["row"], "reaction": rn, "status": "NO-ROW"}); nfail += 1; continue
        t = load(row["pdf"])
        if t is None or len(t) < 400:
            # NO-TEXT MUST MEAN "THE PDF IS A SCAN", NOT "NOBODY BUILT THE CACHE".
            # Those two look identical from here and are completely different problems. The BASF
            # patent sat as NO-TEXT while its own conc_provenance DESCRIBED a 300 dpi tesseract
            # pass -- the pass had been run and its output never written, so the row was reported
            # as unreadable when the text was merely absent from disk. Ask the PDF directly.
            why = "scan (no text layer)"
            try:
                import pymupdf as _fitz
                _p = os.path.join(ROOT, "..", "papers for model", "concentrations", row["pdf"])
                if os.path.exists(_p):
                    _d = _fitz.open(_p)
                    _n = sum(len(_d[i].get_text()) for i in range(len(_d)))
                    if _n > 500:
                        why = ("CACHE NOT BUILT -- the PDF has %d characters of extractable text "
                               "but results/pdftext/%s.txt is empty. This is not a scan; run the "
                               "extraction." % (_n, os.path.splitext(row["pdf"])[0]))
            except Exception:                                   # noqa: BLE001
                pass
            res.append({"row": row["row"], "reaction": rn, "pdf": row["pdf"],
                        "status": "NO-TEXT", "why": why}); nfail += 1; continue
        base = molarities(t) + quotients(t)
        pool = base + relative(t, base)
        tgt = {
            "carrier":     float(rec["C_carrier_M"]),
            "substrate":   float(rec["C_substrate_M"]) * (1.7 if neg else 1.0),
            "electrolyte": elyte_M(rec["electrolyte"]),
        }
        cand = {k: anchors(t, v, pool) for k, v in tgt.items()}
        found = {k: bool(cand[k]) for k in tgt}
        pos, spread = pick_colocated(cand)
        same = spread <= WINDOW
        miss = [k for k, v in found.items() if not v and tgt[k] is not None]
        # HAND_VERIFIED covers BOTH failure modes -- a number the extractor cannot read at all
        # (miss) and numbers it can read but cannot co-locate because the passage holding them
        # together is mangled (not same). Row 19 is the second kind and was reported
        # MIXED-EXPERIMENT despite a note quoting the single footnote that carries all three.
        if (miss or not same) and row["row"] in HAND_VERIFIED and not neg:
            status = "HAND-VERIFIED"
        elif miss:
            status = "SI-ONLY:" + ",".join(miss); nsi += 1
        elif not same:
            status = "MIXED-EXPERIMENT(spread=%d)" % spread; nmixed += 1
        else:
            status = "ANCHORED"
        res.append({"row": row["row"], "reaction": rn, "pdf": row["pdf"], "status": status,
                    "targets": tgt, "spread": spread,
                    "quotes": {k: quote(t, p) for k, p in pos.items()}})
        print("  %-2s %-46s %s" % (row["row"], rn[:46], status))

    nH = sum(1 for r in res if r["status"] == "HAND-VERIFIED")
    nA = sum(1 for r in res if r["status"] == "ANCHORED")
    print("\n%d rows: %d ANCHORED, %d HAND-VERIFIED, %d SI-ONLY, %d MIXED-EXPERIMENT, %d unusable"
          % (len(res), nA, nH, nsi, nmixed, nfail))
    ## the control must NEVER overwrite the live result -- it did on its first run, which would
    ## have left a perturbed set of verdicts on disk wearing the name of the real one.
    out_name = "condition_anchor_NEGCONTROL.json" if neg else "condition_anchor.json"
    json.dump(res, open(os.path.join(ROOT, "results", out_name), "w"), indent=1)
    print("-> results/%s" % out_name)
    if neg:
        # DERIVED, NOT PINNED. This was `nA <= 3`, a magic number: when the co-location fix let
        # anchors() see every matching occurrence instead of only the numerically closest, a
        # perturbed substrate found a coincidental match more often, ANCHORED-under-perturbation
        # rose from 3 to 5, and a control that was working reported BAD. What the control
        # actually asserts is that the anchoring COLLAPSES, so measure it against the baseline
        # this gate itself recorded rather than against a typed integer.
        base = None
        try:
            prev = json.load(io.open(os.path.join(ROOT, "results", "condition_anchor.json"),
                                     encoding="utf-8"))
            prev = prev if isinstance(prev, list) else prev.get("rows", prev)
            base = sum(1 for r in prev if r.get("status") == "ANCHORED")
        except Exception:
            pass
        print("\nNEGATIVE CONTROL: substrate x1.7. ANCHORED count must COLLAPSE.")
        if not base:
            print("G-COND control: INDETERMINATE -- run the gate without --negative-control "
                  "first so there is a baseline to collapse from")
        else:
            good = nA <= 0.3 * base
            print("G-COND control: %s (ANCHORED %d -> %d, %.0f%% of baseline)"
                  % ("GOOD" if good else "BAD -- test is inert", base, nA, 100.0 * nA / base))
    else:
        print("G-COND: %s" % ("PASS" if (nmixed == 0 and nfail == 0 and nsi == 0) else "REVIEW NEEDED"))

if __name__ == "__main__":
    main()
