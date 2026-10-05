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
