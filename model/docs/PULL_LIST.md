# Pull list — the exact PDFs still needed, ranked by what each unblocks

Generated 2026-08-22, last revised after the "Model Papers for Params" delivery, from
`data/parameters_provenance.csv` — the row counts are computed, not estimated: **57 registry rows**
currently carry an explicit "PULL NEEDED" clause naming their source.

Drop PDFs anywhere in the repo and say where; I will read them, extract the specific table,
register the values with a page locator, and re-run the gates.

---

## 1. Dorn et al. 2024 — **SUPPORTING INFORMATION** ⭐ unblocks 38 rows

> Dorn, Kareth, Weidner & Petermann, *J. Chem. Eng. Data* **2024**, 69, 1493–1502.
> DOI 10.1021/acs.jced.3c00691
> **The ACS Supporting Information file, not the article body.**

**This one is worth more than everything else combined.** The article body's Table 3 carries only
four Casteel–Amis fits and I already have it — one of them supplies the five derived
Bu₄NBF₄/MeCN rows. **The 164 measured κ(c) isotherms live in the SI**, which is a separate
download I could not reach.

What it would close:
- **38 registry rows** currently saying "PULL NEEDED" point at it.
- Dorn's Table 1 salt list includes **NaBr** and **(C₄H₉)₄NBr**, so it plausibly reaches several
  MeOH rows as well.
- ~~It carries the ACN/(C₂H₅)₄NBF₄ fit, which converts `0.077 M Et4NBF4/MeCN` from a bound to a
  derived value~~ — **withdrawn on retrieval of the article body.** Table 3 p. 1499 does carry
  that fit, but evaluated at 0.077 M it returns 4.03 mS cm⁻¹, i.e. Λ/Λ° = 0.269 against 0.615 for
  Bu₄NBF₄ at the same molality in the same solvent. Two homologous R₄N⁺BF₄⁻ salts cannot differ
  that way: the fit is anchored at m_max = 4.0 mol kg⁻¹ and does not reach this concentration.
  The row was derived by same-family transfer instead (item 2).
- It should also give **λ°(Bu₄N⁺, MeCN)**, the single missing number blocking the κ analogue of
  the surrogate-anchoring method (Eqs. S32/S33).

Category 6 is currently **0 measured / 7 derived / 42 assumption**. This file is the only
realistic route to moving that census.

## 2. ~~Krumgalz 1983~~ — **DELIVERED 2026-08-22, and it closed more than it was asked for**

> Krumgalz, *J. Chem. Soc. Faraday Trans. 1* **1983**, 79, 571–587.
> Archived: `papers for model/f19837900571.pdf`

What it actually closed:

- **η(HFIP) = 1.619 mPa s** — Table 3, p. 578. This was *item 7* on this list, not item 2, and no
  search for it had ever succeeded because they all returned hexafluoro*propane*. HFIP's viscosity
  moves state C → state A and its value by −1.9 %, which is what forced manuscript **v22**.
- **λ°(SCN⁻, MeCN) = 113.3** and **λ°(Br⁻, MeOH) = 56.53** — Table 4, p. 579. Both reproduce the
  inherited values through Nernst–Einstein (+4.0 % and +0.4 %), so the two rows move to *derived*.
- **λ°(Et₄N⁺, MeCN) = 84.9 and λ°(Bu₄N⁺, MeCN) = 61.6** — Table 2 p. 577 Walden products over
  Table 3 p. 578 viscosity. Used as the *independent corroboration* of the Et₄NBF₄ transfer.

What it could **not** close, and why the rows stay assumptions:

- **λ°(ClO₄⁻, MeCN)** — the acetonitrile row of Table 4 prints a dash in that column.
- **λ°(Li⁺, MeCN)** — the acetonitrile *cation* row carries seven tokens for nine columns with no
  right-hand anchor, so H⁺ and Li⁺ cannot be separated by column position. Picking the reading
  that "looks right" would be recognition, not retrieval, so it was not done.

### A correction this list has to make about itself

Item 2 used to say Krumgalz would supply *"λ°(Bu₄N⁺, MeCN), the single missing number blocking
the κ analogue of the surrogate-anchoring method"*, and item 1 said the same of the Dorn SI.

**That number was never missing.** `Kalugin, Lukinova & Novikov, Kharkiv Univ. Bull. Chem. Ser.
2019, 33(56), 23–33, Table 3, p. 28` carries Bu₄N⁺ 61.90, Et₄N⁺ 86.34 and BF₄⁻ 109.20 — and it
was **already cited in `build_param_tables.py`**, on the `Br- (MeCN)` row, the whole time. The
check that should have caught it earlier is one line: 61.90 + 109.20 = 171.10, reproducing to
0.00 % the Λ°(Bu₄NBF₄/MeCN) = 171.1 the registry independently carries as measured.

So `0.077 M Et4NBF4/MeCN` is now **derived at 9.26 mS cm⁻¹** on the Kalugin route, with Krumgalz
giving 9.20 by a fully independent tabulation — a 0.6 % spread. It did not need either pull.

## 3. CRC Handbook 97th ed. — two specific tables ⭐ closes review finding R1

> CRC Handbook of Chemistry and Physics, 97th ed. (Haynes, ed.), CRC Press, 2016.
> **Section 5, "Ionic Conductivity and Diffusion at Infinite Dilution"** (Vanýsek)
> **Section 6, "Permittivity (Dielectric Constant) of Liquids"**, 25 °C column

I retrieved Vanýsek's *companion* table (equivalent conductivity of electrolytes) and archived it,
which anchored the Onsager constants, the KCl validation and three aqueous Λ°. These two are the
ones I could not reach:

- **Sect. 5** converts 15 recalled aqueous per-ion λ° into page-anchored values. They are
  currently cross-checked to <0.1% by Kohlrausch's law against retrieved data, so this is
  hygiene rather than correction — but it is the finding a reviewer flagged as critical.
- **Sect. 6** covers the 9 solvent permittivities, which are recalled. They are verified unused
  (zero consumers), so this is the lowest-stakes item on the list — include it only if easy.

## 4. Reid, Prausnitz & Poling — Le Bas table ⭐ closes review finding R2

> *The Properties of Gases and Liquids*, **Table 3-11** (4th/5th ed.) — "Le Bas additive atomic
> volumes". Perry's *Chemical Engineers' Handbook* **Table 2-400** is an acceptable substitute.

The increments are cited row-by-row in the registry, but the **G-LEBAS gate compares computed
volumes against reference values I recalled**, and for most compounds the published value is the
same additive sum — so it is an implementation regression test, not independent verification.
This table makes it a real check. One page is enough.

## 5. A page-anchored ferrocene diffusion coefficient — underpins two gates

> Preferred: Wang, Rogers & Compton, *J. Electroanal. Chem.* **2010**, 648(1), 15–19,
> DOI 10.1016/j.jelechem.2010.07.006 — double-potential-step microdisk chronoamperometry,
> ferrocene and ferrocenium in MeCN, with temperature dependence.
> Acceptable: Bard & Faulkner, *Electrochemical Methods*, 2nd ed. — the page carrying the
> ferrocene/MeCN D.

Everything anchored by Eqs. S32/S33 scales **linearly** with this number, and it is currently a
textbook *range* (1.7–2.4 × 10⁻⁵ cm² s⁻¹) read at its upper end. A point value with an
uncertainty would firm up G-ANCHOR and G-CATD at once.

## 6. Mixed-solvent viscosity and density — 6 rows, two papers

> **Aminabhavi & Gopalakrishna**, *J. Chem. Eng. Data* **1995**, 40, 856–861 — ρ and η at
> 298.15 K over the full composition range for DMF+H₂O, DMSO+H₂O, DMA+H₂O, MeCN+H₂O, THF+H₂O.
> *(unblocks the 2 DMF/H₂O rows, and corroborates the MeCN/H₂O rows)*
>
> **González, Calvar, Gómez & Domínguez**, *J. Chem. Thermodyn.* **2007**, 39, 1578–1588 — ρ and
> η for MeOH+H₂O and EtOH+H₂O at 298.15 K.
> *(unblocks 4 rows)*

The inherited CRC citation for these was withdrawn because it is tabulated at 20 °C and indexed
by mass percent, so it cannot support a 25 °C value at a stated volume ratio.

## 7. HFIP **density** — 1 row (the viscosity is closed; see item 2)

> Any primary measurement of ρ for 1,1,1,3,3,3-hexafluoro-2-propanol at 25 °C.

The viscosity was closed by Krumgalz Table 3 p. 578. **ρ = 1.596 g cm⁻³ is still unsourced** —
supplier and aggregator listings agree but none is page-anchorable.

The inherited citation for this row was not merely unopened, it was **wrong on two counts** and
has been withdrawn: it named *Colomer, Chinchilla, Waldvogel et al.*, whereas the paper
(*Nat. Rev. Chem.* 2017, 1, 0088) is by **Colomer, Chamberlain, Haughey & Donohoe**; and it
claimed the paper carries μ and ρ, whereas its Table 1 p. 2 carries boiling point and
permittivity only. That same table did correct HFIP's ε from a recalled **16.7 to 15.7**.

Low stakes: ρ enters only through ν = μ/ρ in the Schmidt number, and Sh ∼ Sc^0.356, so a 5 %
error moves k_m by 1.8 %.

## 7b. A measured κ(c) for Bu₄NBF₄ in DMF — 1 row, and it is **quoted in the manuscript body**

> Any measured conductivity isotherm for tetrabutylammonium tetrafluoroborate in
> *N,N*-dimethylformamide at 25 °C. The **Dorn et al. Supporting Information** (item 1) is the most
> likely source.

This is the highest-priority single row on the list, because it is the only unsourced number that
a reader meets in the **manuscript** rather than in the SI. The TRL-E 6 passage reads
*"0.1 M Bu₄NBF₄ in DMF, κ = 3.5 mS cm⁻¹"* and builds a worked example on it — a 16.8 V cell of
which 14.3 V is ohmic, dissipating 1.4 W cm⁻².

It was carried as `unused-legacy (no registry row)` until 2026-08-22, i.e. a number printed in the
manuscript had no provenance entry anywhere, because "used" was defined as "named by one of the 50
reactions". It is now registered as a **state-C assumption with a manuscript-anchored
sensitivity**: the model reproduces the passage exactly (16.76 V, 1.476 W cm⁻²), and the claim the
passage actually makes — that this reproduces the 10–20 V cells common in academic non-aqueous
reports — survives for **κ ∈ [2.85, 6.64] mS cm⁻¹, i.e. 0.82× to 1.90×** the carried value.

Gate **G-MSKAPPA** (`data/check_ms_numbers.py`) now reads the shipped `.docx` and asserts that
every κ the manuscript states has a registry row the SI prints.

The Walden transfer from the derived 0.1 M Bu₄NBF₄/MeCN row (9.9 mS cm⁻¹) would give
9.9 × 0.343/0.794 = 4.3 mS cm⁻¹, but cross-solvent Walden transfer into DMF was tested and fails
by ~70 %, so it is recorded as a consistency note and **not** used.

## 8. Darling 1964 — 1 row

> Darling, *J. Chem. Eng. Data* **1964**, 9, 421–426, DOI 10.1021/je60022a041.
> κ of aqueous H₂SO₄, 0.5–99 wt %, 0–240 °F. **Read the ~17.5 wt % / 25 °C cell.**

Would convert `2 M H2SO4 aq` from assumption to derived.

## 9. Minc & Werblan 1962 — 3 rows

> Minc & Werblan, *Electrochim. Acta* **1962**, 7, 257–266 — alkali perchlorates in MeCN.

Named in the registry as the correct source for `0.04 M NaBr/MeCN`, `0.08 M NaBr/MeCN` and
`0.2 M NaClO4/MeCN`; until it is opened those three carry neither a value nor a ceiling. Likely
superseded by item 1 if the Dorn SI covers them.

---

## Literature search, 2026-08-22 — the two Fig. 5 conductivities

Searched deliberately across four literatures for a measured κ at **preparative** concentration
for `0.2 M NaI/DMF` and `3.0 M LiBr/THF`. **A clear pattern came out of it, and it is the finding:**

> The physical-chemistry conductance literature for non-aqueous solvents is **dilute by
> construction**. Fuoss–Onsager, Fuoss–Justice and the c^3/2 series equations are low-concentration
> expansions, and every study that reports Λ°, K_A or Walden products is measuring in the range
> those theories require — typically 10⁻⁴ to 10⁻² M. Nobody in that community publishes κ at 0.2 M
> in DMF, because it is not a quantity their analysis needs.
>
> The applied literature (batteries, Li-mediated ammonia, DSSCs) *does* work at 0.1–3 M — but on
> different salt/solvent pairs: glymes and carbonates rather than DMF, and LiTFSI/LiTf/LiBF₄
> rather than NaI or LiBr.

**Retrieved and used** (all now in `papers for model/`):

| source | what it gave | limit |
|---|---|---|
| Krumgalz & Barthel, *Z. Phys. Chem.* 1984, **142**, 167–178 | Λ° = 81.35 ± 0.04 and K_A = 7.50 ± 0.57 for NaI/DMF at 25 °C, Table 2 | dilute |
| Das, *J. Solution Chem.* 2008, **37**, 947–955 | LiBr/THF Λ at 0.007–0.035 M; triple ions; c_min = 4.9 mM | ~100× too dilute |
| Dorn *et al.* SI | 164 isotherms, full range | no DMF, no THF |

**Found, not yet retrieved, worth pulling:**

| DOI | source | why |
|---|---|---|
| `10.1007/BF00807559` | Szejgis, Bald & Gregorowicz, *Monatsh. Chem.* 1997, **128**, 1093–1100 | NaI in water/DMF over the **whole composition range** at 298.15 K, Fuoss–Justice Λ₀/Walden/K_A. Reaches neat DMF, so it gives a **third independent** Λ₀ and K_A. Dilute, so it will not close the row — but it would make Λ° triply-sourced |
| — (print only) | **Barthel & Neueder, *Electrolyte Data Collection*, DECHEMA Chemistry Data Series Vol. XII**, Parts 1/1a/1b/1c | the definitive compilation of non-aqueous conductivities. **The single realistic route to concentrated data.** Barthel's group measured to high concentration for battery work; if κ(0.2 M, NaI/DMF) exists anywhere, it is here |
| `10.1021/acs.jpcc.9b00864` | Horwitz, Rodríguez, Factorovich & Corti, *J. Phys. Chem. C* 2019, **123**, 12081–12087 | **method**, not data: how to treat strongly associated Li salts in low-ε ethers, including Casteel–Amis for the conductivity maximum. Uses glymes with LiTf/LiTFSI, not THF/LiBr — so it is a template for `3.0 M LiBr/THF`, not a source for it |
| `10.1021/acsenergylett.4c01655` | Fu, Li, Deissler, Mygind, Kibsgaard & Chorkendorff, *ACS Energy Lett.* 2024, **9**, 3790–3795 | Li-salt comparison for Li-mediated ammonia in THF at working concentration; the closest applied match to `3.0 M LiBr/THF` |
| `10.1021/jacs.3c08965` | Cai *et al.*, *JACS* 2023, **145**, 25716–25725 | ether-based electrolytes for the same chemistry |

**Honest conclusion.** For `0.2 M NaI/DMF` the value now rests on a measured Λ° and a measured
attenuation transferred one solvent step, corroborated to 5 % by a measured K_A — three sources,
no invented numbers. For `3.0 M LiBr/THF` the concentrated data does not appear to exist in the
accessible literature at all, and the triple-ion regime means no Λ°-based construction can
substitute. Both would be settled in an afternoon at a bench, and that remains the cheapest route.

## Not obtainable, and not worth your time

- **Measured D for the actual metal-complex carriers in their actual solvents.** Does not exist
  for this family. Handled by bracketing (Eqs. S32/S33, gate G-ANCHOR) — the conclusion holds at
  both ends.
- **Measured κ for LiBr/THF above 5 × 10⁻² M, or NaI/DMF at 0.2 M.** Does not exist. Both are
  bounded, both need a 2.9× error to break their conclusion.
- **Six mixed-solvent rows** (DMSO/THF, tAmOH/H₂O, AcOH/HCOOH) — no measured isotherm exists for
  those pairs at all. These stay assumptions permanently unless someone measures them.
- **Anything that would make Figure 1 externally reproducible.** CAS grant terms; disclosed in
  §S11 instead.

---

## If you only get me one thing

**Item 1, the Dorn SI.** It is still worth the most: the 164 measured κ(c) isotherms are the only
realistic route to moving category 6, which remains 0 measured / 8 derived / 41 assumption.

But the clause that used to follow this — "and the one number blocking the κ version of the
anchoring method" — is **withdrawn**. There was no such number; see the correction under item 2.
The lesson is worth more than the pull was: before adding anything to this list, grep the registry
for the quantity first. Kalugin p. 28 sat in `build_param_tables.py` for the whole time item 1 and
item 2 both claimed to be the only way to reach it.
