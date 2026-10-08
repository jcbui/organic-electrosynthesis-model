# DOIs to pull — 2026-08-23

**CORRECTION, recorded at the top because I got this wrong once already.** Three exemplars were
reported as non-existent and I called two of them fabricated. **All three papers exist.** Two
carried a wrong SECOND author (a middle author, where this file's convention is first/last),
which made them unfindable by name; the third was correct all along and my search queries were
simply bad. No row is dropped and no count changes. What IS wrong is that the recorded
*conditions* for those rows were never checked against the papers.

The general lesson, which cost real time today: **"my search cannot find it" is not
"it does not exist."** Automated citation checking here produced false positives (an earthquake
paper, a carbon-markets paper for real citations) AND false negatives (three real papers judged
missing). It is a screen, never a certificate.

---

> **SUPERSEDED 2026-10-06.** Sections A-E below are the 2026-08-23 list. Every paper they name is on disk, and the
> class B and C flags were failures of that day's DOI search, not bad citations: all ten exemplars resolve on Crossref
> to the paper the row cites (the one genuine misattribution, Zhao Angew 2017 for the benzimidazole row, was corrected to
> Zhao ChemSusChem 2021 in v98). Kept for history; the live list is the 2026-10-06 section at the end.

## A. UPLOAD THESE FIRST — real papers, conditions never verified, numbers live in the model

| # | DOI | paper | row |
|---|---|---|---|
| 1 | **10.1038/s41467-025-57329-0** | Zhang … Su, *Scalable and efficient electrochemical bromination of arenes with Faradaic efficiencies surpassing 90%*, Nat. Commun. 2025 | Br⁻ oxidation / electrophilic bromination — **one of the 8 mediated EC′ rows**, the γ = 0.288 inverted cell |
| 2 | **10.1002/chem.201901082** | Ke … Chi, *Hydrodehalogenation of Aryl Halides through Direct Electrolysis*, Chem. Eur. J. 2019 | Cathodic aryl chloride dehalogenation |
| 3 | **10.1038/s41467-023-37032-8** | Yang … Lei, *Electrochemical oxidative difunctionalization of diazo compounds with two different nucleophiles*, Nat. Commun. 2023 | Diazo difunctionalization (thiol + alcohol) |

**What to check in each:** carrier concentration, substrate concentration, supporting electrolyte
and its molarity, solvent, and scale. The previously recorded strings for rows 1 and 2 carried
page locators ("Fig 4-5 fn pp 6-7", "Table 1 fn pp 6911-2") that were never checked; both have
been replaced with `NEEDS RE-VERIFICATION AGAINST THE PAPER` and the unverified numbers removed.

## B. NO DOI RESOLVED — pull by hand

| exemplar | row |
|---|---|
| Liu/Qiu Angew 2025 | Electrochemical amination of ArX with NH₃ |
| Fu/Lin Science 2017 | Mn-catalyzed alkene diazidation |
| Cai/H.-C. Xu Nat Commun 2021 | Co-catalyzed aza-Wacker cyclization |
| Cai/H.-C. Xu Nat Catal 2022 | Cu-catalyzed benzylic cyanation |
| Bao OL 2022 | Anodic oxazoline/oxazole cyclization |
| Mei/Han ACS Omega 2019 | Sulfonylation of alkenes with sulfinates |
| BASF US 5,507,922 | Lysmeral methoxylation (patent, not in Crossref) |

## C. DOI SEARCH RETURNED THE WRONG PAPER — the citation may still be fine, but check

| exemplar | what the search wrongly returned |
|---|---|
| Zhao/H.-C. Xu Angew 2017 | a macrolide synthesis paper |
| Courtois/Perichon Tetrahedron 1997 | an allylation paper |
| Peters/Baran Science 2019 | a halloysite nanocomposite paper in *Applied Clay Science* |

## D. RESOLVED AND PLAUSIBLE — spot-check the conditions only

| DOI | row |
|---|---|
| 10.1021/jacs.9b01886 | Ni-catalyzed aryl amination |
| 10.1021/ja00848a020 | Shono oxidation / α-methoxylation |
| 10.1021/acs.oprd.3c00332 | Br-mediated Hofmann rearrangement |
| 10.1021/ja402083e | Arene C–H pyridination |
| 10.1021/acs.orglett.8b00981 | Amidyl-radical C–H amination |
| 10.1038/s41467-022-31813-3 | Ritter-type C(sp3)–H amination |
| 10.1038/s41557-021-00640-2 | Co-H hydroamination + isomerization |
| 10.1126/science.adf4762 | Kolbe homocoupling |
| 10.1021/acs.oprd.6c00110 | Ni-XEC kg flow |
| 10.1038/s41586-022-04691-4 | Doubly decarboxylative |
| 10.1021/ja211005g | BDD phenol-arene |
| 10.1126/science.aba3823 | Decarboxylative Minisci |
| 10.1039/d0sc01694b | Cathodic Giese |
| 10.1002/anie.201803342 | Rh electrooxidative C–H |
| 10.1039/c39940002535 | Anodic 2-naphthol coupling |
| 10.1149/1.2426086 | Acrylonitrile hydrodimerization |
| 10.1021/acs.oprd.3c00067 | Nitroarene → aniline |
| 10.1021/jacs.2c02102 | rAP imide reduction |
| 10.1021/acssuschemeng.8b02637 | Benzaldehyde → benzyl alcohol |
| 10.1021/acs.oprd.1c00036 | ACT alcohol oxidation (hectogram) |
| 10.1126/science.aaz8459 | Cl-mediated propylene epoxidation |
| 10.1021/acssuschemeng.4c02898 | Lignin → vanillin (pilot) — the binary z = −2 carbonate row |
| 10.1021/acs.oprd.2c00111 | Thioether → sulfone (kilo) |
| 10.1038/nature17431 | NHPI allylic C–H → enone |
| 10.1002/cssc.202501920 | Alkenesulfonate from cinnamic acid |
| 10.1021/acssuschemeng.9b00203 | HMF → FDCA |
| 10.1039/c6sc02117d | Radical-cation Diels–Alder |
| 10.1139/v92-314 | BQ-mediated Wacker–Tsuji |
| 10.1039/d1ra08124a | Non-Kolbe decarboxylative alpha-methoxylation |
| 10.1016/s0040-4039(00)75801-1 | Cathodic aryl-halide 5-exo cyclization |
| 10.1016/s1388-2481(02)00381-8 | Anodic benzylic fluorination |
| 10.1016/j.electacta.2010.05.035 | Aryl thiocyanation |
| 10.1038/s41467-021-26960-y | Anodic C–H phosphonylation |
| 10.1002/anie.201603899 | N–N azo/pyrazole formation |

---

## E. Why the exemplar column had no gate

`verify_citations.py` (G-CITE) resolves the SI bibliography; `verify_ms_citations.py` (G-MSCITE)
resolves the manuscript's Sections 3–4. **Neither ever read `reactions_50.csv`** — the column that
carries every carrier, substrate, mediator and electrolyte concentration in the model. A
provenance audit the same morning reported "0 chimera suspects" without touching it.

`data/verify_exemplars.py` now exists and should be run, but on today's evidence its verdicts must
be read as leads. The reliable check is opening the paper.

## Pull list from chemistry audit pass 11 (2026-10-06): sources no audit could open

The manuscript DOIs below are read from the manuscript's own bibliography. The SI DOIs were resolved on Crossref by
first author, volume and first page.

### Manuscript, Section 6 (stability)

| ref | work | DOI |
|---|---|---|
| 63 | Kim & See, ACS Appl. Mater. Interfaces (Mg electrolytes; cited for Al anodes, check fit) | 10.1021/acsami.0c19053 |
| 64 | He, Luo & Liu, J. Mater. Chem. A (MgCl2/AlCl3 electrolytes; cited for Al anodes, check fit) | 10.1039/c7ta01769c |
| 65 | Fangmeyer et al., Angew. Chem. 2020 (MS imaging of electrode fouling) | 10.1002/anie.202010134 |
| 66 | Hanssen, Siraj & Wong, Rev. Anal. Chem. 2016 (antifouling strategies) | 10.1515/revac-2015-0008 |
| 67 | Vidal, Garcia-Ruiz & Castillo, Microchim. Acta 2003 (electropolymerized films) | 10.1007/s00604-003-0067-4 |
| 68 | Yang et al., Electrochim. Acta 2013 (electrode fouling model) | 10.1016/j.electacta.2013.01.019 |
| 69 | Ware et al., Chem. Sci. 2024 (sacrificial anodes) | 10.1039/d3sc06885d |
| 71 | Chaplin et al., J. Appl. Electrochem. 2011 (BDD failure) | 10.1007/s10800-011-0351-7 |
| 72 | Razmi & Heidari, Anal. Biochem. 2009 | 10.1016/j.ab.2009.01.036 |
| 73 | Perez et al., Langmuir 2012 | 10.1021/la303022a |
| 74 | Kaeffer & Leitner, JACS Au 2022 | 10.1021/jacsau.2c00031 |
| 75 | Brown, Chem. Rec. 2021 (extended-path flow cells) | 10.1002/tcr.202100163 |
| 77 | Klein & Waldvogel, Angew. Chem. 2022 (counter-electrode reactions) | 10.1002/anie.202204140 |
| 78 | Francke, ECS Meet. Abstr. 2024 | 10.1149/MA2024-01412342mtgabs |
| 79 | Broese & Francke, Org. Lett. 2016 (ionically tagged mediator-electrolyte) | 10.1021/acs.orglett.6b02979 |
| 80 | Blanco et al., React. Chem. Eng. 2020 (membrane-separated electrosynthesis) | 10.1039/c9re00389d |
| 81 | Jaroszek & Dydo, Open Chem. 2016 (ion-exchange membranes) | 10.1515/chem-2016-0002 |
| 85 | Abbel et al., MRS Commun. 2017 (lifetime limitations) | 10.1557/mrc.2017.46 |

### Manuscript, earlier pending

| ref | work | DOI |
|---|---|---|
| 20 | Go et al., JACS 2022 | 10.1021/jacs.2c03213 |
| 21 | Sheng et al., Org. Lett. 2020 | 10.1021/acs.orglett.0c02799 |
| 22 | Li et al., JACS 2021 | 10.1021/jacs.0c13093 |

### SI

| work | used for | DOI |
|---|---|---|
| Heeb, Criquet, Zimmermann-Steffens & von Gunten, Water Res. 2014, 48, 15 | HOBr/amine range bracketing the Hofmann and amidyl k | 10.1016/j.watres.2013.08.030 |
| Grennberg, Gogoll & Bäckvall, Organometallics 1993, 12, 1790 | Pd(0)/BQ -> Pd(II) + hydroquinone (Wacker row) | 10.1021/om00029a040 |
| Wallis & Lane, Org. React. 1946, 3, 267 | Hofmann rearrangement review | 10.1002/0471264180.or003.07 |
| Lobaccaro et al., PCCP 2016, 18, 26777 -- **the supporting information** | H-cell compartment dimensions behind S6.4's sigma | 10.1039/c6cp05287h |
| Zhang et al., JACS Au 2023, 3, 2280 | Table 1 THF conductivities (S6.1, S3.2) | 10.1021/jacsau.3c00305 |

### Status 2026-10-06 (after the Downloads check)

Retrieved without a login and filed in `papers for model/pull_20261006/`: Fangmeyer 2020 (PDF); Ware 2024, Kaeffer &
Leitner 2022, Klein & Waldvogel 2022, Zhang 2023 (Europe PMC full-text XML). Already in Zotero: Lobaccaro 2016 (the
article; its ESI is still needed). Everything else on this list is still to pull.
