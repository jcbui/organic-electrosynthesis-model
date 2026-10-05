# Every source the model cites — DOI, and whether it is already in the repo

Generated 2026-08-22 from `results/citation_verification.json` (Crossref-resolved) plus a scan of
`papers for model/` and `Model Papers for Params/`.

**Verification status: `data/verify_citations.py` → G-CITE PASS.** 24 journal citations resolve
and the first author matches the resolved record in every case; **0 chimera suspects**. The gate
is negative-controlled by injecting a real DOI wearing fabricated authors, which it catches.

---

## Already in the repo — nothing to pull

| source | file | what it anchors |
|---|---|---|
| Krumgalz, *J. Chem. Soc. Faraday Trans. 1* 1983, 79, 571–587 | `Model Papers for Params/f19837900571.pdf` | η(HFIP) 1.619; λ°(SCN⁻/MeCN) 113.3; λ°(Br⁻/MeOH) 56.53; Walden products |
| Dorn et al., *J. Chem. Eng. Data* 2024, 69, 1493–1502 | `Model Papers for Params/je3c00691.pdf` | 5 Casteel–Amis Bu₄NBF₄/MeCN rows |
| **CRC Handbook, 97th ed. (2016)** | `Model Papers for Params/CRC Handbook ... 97th Edition (2016).pdf` | **closes review finding R1** — Sect. 5 ionic conductivity, Sect. 6 permittivity |
| **Reid/Poling, *Properties of Gases and Liquids*, 4th ed.** | `Model Papers for Params/2015.148102...Fourth-Edition.pdf` | **closes R2** — Le Bas increments. *NB: registry cites the 5th ed.* |
| **Minc & Werblan**, *Electrochim. Acta* 1962, 7, 257–266 | `Model Papers for Params/1-s2.0-0013468662870030-main.pdf` | pull item 9 — alkali perchlorates in MeCN |
| **González, Calvar, Gómez & Domínguez**, *J. Chem. Thermodyn.* 2007 | `Model Papers for Params/1-s2.0-S0021961407000900-main.pdf` | pull item 6 — MeOH/H₂O and EtOH/H₂O ρ, η |
| **Darling**, *J. Chem. Eng. Data* 1964, 9, 421–426 | `Model Papers for Params/je60022a041.pdf` | pull item 8 — κ of aqueous H₂SO₄ |
| Vanýsek, CRC equivalent conductivity table | `papers for model/vanysek_CRC_...pdf` | Onsager constants, KCl validation, 3 aqueous Λ° |
| Colomer, Chamberlain, Haughey & Donohoe, *Nat. Rev. Chem.* 2017, 1, 0088 | `papers for model/colomer_2017_...pdf` | HFIP ε = 15.7 (corrected from a recalled 16.7) |
| Ansari & Singh, *Res. J. Chem. Sci.* 2022, 12(1), 67–69 | `papers for model/ansari_singh_2022_...pdf` | MeCN–H₂O ρ, η. **Retrieved and verified this pass** |
| Gopal & Jha, *Indian J. Chem.* 1977, 15A, 80–83 | `papers for model/gopal_jha_1977_...pdf` | λ°(Na⁺, I⁻, Et₄N⁺, ClO₄⁻) in DMF. **Retrieved and verified this pass** |
| Bhat, Mohan & Susha, *Indian J. Chem.* 1996, 35A, 825–831 | `papers for model/bhat_mohan_susha_1996_...pdf` | Λ°(NaClO₄, DMF) cross-check. **Retrieved and verified this pass** |
| Peters et al., *Science* 2019 — Supplementary Materials | `papers for model/aav5606_peters_sm.pdf` | 3.0 M LiBr/THF composition |

## Still to pull — journal articles, by DOI

These all resolve on Crossref with the right authors, so none is a fabricated citation. They are
wanted so the *numbers* can be read off the page rather than trusted.

| DOI | source | why |
|---|---|---|
| `10.1021/je00020a026` | Aminabhavi & Gopalakrishna, *J. Chem. Eng. Data* 1995, 40, 856–861 | ρ, η for DMF+H₂O, DMSO+H₂O, MeCN+H₂O at 298.15 K |
| `10.1021/je60034a013` | Cunningham, Vidulich & Kay, *J. Chem. Eng. Data* 1967, 12, 336–337 | MeCN–H₂O ρ, η, ε — corroborates Ansari |
| `10.1002/bbpc.19940980706` | Wode & Seidel, *Ber. Bunsenges. Phys. Chem.* 1994, 98, 927–934 | precision MeCN–H₂O viscosities |
| `10.1039/c5ee02341f` | Gong, Fang, Gu, Li & Yan, *Energy Environ. Sci.* 2015, 8, 3515–3530 | λ°(Et₄N⁺, MeCN) = 85.1, Table 2 p. 3518 |
| `10.3390/molecules29061371` | Kinart, *Molecules* 2024, 29, 1371 | DMF solvent properties (ε, η, ρ) — **not** the conductivity |
| `10.1149/1.2781252` | Eisenberg, Tobias & Wilke, *J. Electrochem. Soc.* 1954, 101, 306–320 | the rotating-cylinder Sh correlation |
| `10.1149/1.2780889` | Wilke, Eisenberg & Tobias, *J. Electrochem. Soc.* 1953, 100, 513–523 | free-convection limiting currents |
| `10.1016/0013-4686(74)85036-x` | Pickett & Ong, *Electrochim. Acta* 1974, 19 | parallel-plate entrance effects |
| `10.1149/1945-7111/abc58e` | Perry, Ponce de León & Walsh, *J. Electrochem. Soc.* 2020, 167, 155525 | reactor mass-transfer review |
| `10.1002/aic.690010222` | Wilke & Chang, *AIChE J.* 1955, 1, 264–270 | the correlation itself + φ values |
| `10.1021/ie50414a006` | Chilton, Drew & Jebens, *Ind. Eng. Chem.* 1944, 36, 510 | jacketed-vessel heat transfer |
| `10.1063/1.3088050` | Huber et al., *J. Phys. Chem. Ref. Data* 2009, 38, 101–125 | IAPWS-2008 water viscosity |
| `10.1063/1.1461829` | Wagner & Pruß, *J. Phys. Chem. Ref. Data* 2002, 31, 387–535 | IAPWS-95 water density |
| `10.5194/acp-15-4399-2015` | Sander, *Atmos. Chem. Phys.* 2015, 15, 4399–4981 | Henry's law constants (open access) |
| `10.1515/pac-2019-0603` | Prohaska et al., *Pure Appl. Chem.* 2022, 94, 573–600 | IUPAC 2021 atomic weights (open access) |
| `10.3762/bjoc.7.127` | Watts, Gattrell & Wirth, *Beilstein J. Org. Chem.* 2011, 7, 1108–1114 | microreactor current densities (open access) |
| `10.1021/acs.accounts.9b00412` | Noël, Cao & Laudadio, *Acc. Chem. Res.* 2019, 52, 2858–2869 | flow-cell mass transport |
| `10.1021/acs.oprd.4c00353` | Ferretti et al., *Org. Process Res. Dev.* 2025, 29, 322–332 | the ETC industry survey behind Fig. 6 |
| `10.26565/2220-637X-2019-33-02` | Kalugin, Lukinova & Novikov, *Kharkiv Univ. Bull. Chem. Ser.* 2019, 33(56), 23–33 | λ°(Bu₄N⁺, Et₄N⁺, BF₄⁻, Br⁻) in MeCN. Open access; **Crossref carries no author list for it**, so it is the one record the automated check cannot clear |
| **⭐ the Dorn *Supporting Information*** | ACS SI for `10.1021/acs.jced.3c00691` | **the highest-value pull on the list** — 164 measured κ(c) isotherms; the only realistic route to a *measured* conductivity anywhere in the model |
| `10.1021/acs.jced.3c00691` — *or* a measured κ(c) for **Bu₄NBF₄ in DMF** | — | the one unsourced number a reader meets in the **manuscript body** (κ = 3.5 mS cm⁻¹) |

## Books — cannot be pulled by DOI

| source | ISBN | page wanted |
|---|---|---|
| Bard & Faulkner, *Electrochemical Methods*, 2nd ed., Wiley 2001 | 978-0-471-04372-0 | Sect. 1.4.2 pp. 29–31; the Levich coefficient |
| Cussler, *Diffusion*, 3rd ed., CUP 2009 | 978-0-521-87121-1 | Table 5.2-1 |
| Incropera, DeWitt, Bergman & Lavine, *Fundamentals of Heat and Mass Transfer*, 6th ed., Wiley 2007 | 978-0-471-45728-2 | the Churchill–Chu correlation |
| Barthel & Neueder, *Electrolyte Data Collection*, DECHEMA Vol. XII | print only | highest yield for the whole amide family |

*(BIPM SI Brochure 9th ed. and the NIST Chemistry WebBook are free on the web; no pull needed.)*

---

## Bottom line

Nothing in the registry is a fabricated citation — that is now gated, not asserted. What remains
is the weaker risk: a **real** paper cited for a number nobody read off the page. The three items
above already in `Model Papers for Params/` (Minc & Werblan, González, Darling) close three
open pull items on their own, and the CRC 97th ed. closes review finding R1.
