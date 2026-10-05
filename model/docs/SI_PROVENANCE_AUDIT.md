": "Provenance audit of the Organic Electrosynthesis Perspective SI: every number traced to a source",
  "agentCount": 9,
  "logs": [],
  "result": {
    "synthesis": "# PROVENANCE AUDIT â Section 4 SI (`Section4_Model`)

Root: `/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model/`
Rendered artifact: `SI_Section4_Transport_Model_v3.docx` (verified byte-identical in text to the current output of `make_si.js`, so the shipped document *is* the generator's output â no hand edits to chase).

---

## 1. VERDICT

**The SI does not currently meet the standard "every number has to have provenance."** It is much closer than most papers, and the registry is a genuine asset â but the standard as stated is an absolute, and roughly a third of the load-bearing numbers either sit outside the registry or carry a citation that cannot support the value printed next to it.

### Quantified coverage

Denominator: **292 distinct load-bearing numbers** = the 236 registry rows + **56 numbers that enter a rendered figure, table or SI claim but have no registry row at all** (enumerated in Â§2, M-2/M-3/M-10).

| Tier | What it means | n | % of 292 |
|---|---|---|---|
| **A** | External source **+ locator** (page / table / figure / equation); value reproducible | 44 | **15.1%** |
| **B** | Specific named external source, no locator | 30 | 10.3% |
| **C** | `derived` â stated arithmetic from other registry rows (provenance inherited) | 23 | 7.9% |
| **D** | `numerical` â solver settings, verified to match the code exactly | 8 | 2.7% |
| **E** | `assumption` â declared as such, no source claimed | 10 | 3.4% |
| **F** | `lit-representative` â a source is named but **does not contain this value**; it is a judgement call over a class of similar systems | 86 | 29.5% |
| **G** | Labelled `measured-lit` (or `correlation-est`) but the **citation cannot support the quantity** | 35 | 12.0% |
| **H** | **No registry row anywhere** | 56 | 19.2% |

**Headline figures, stated plainly:**

- **25.3%** (74/292) of load-bearing numbers are traceable to an external source. **15.1%** are traceable to a specific page or table.
- **31.2%** (91/292 = G+H) are *mislabelled or missing*: either absent from the registry, or carrying a provenance class the citation does not earn. This is the part that fails the stated standard outright, and it is the fixable part.
- **29.5%** (86/292 = F) are honestly labelled `lit-representative` â these do not fail the standard as written (the class is disclosed), but the SI's robustness promise ("tolerant to a factor of ~2, with the sensitivity statement given where it matters") is not honoured: **44 of 86 lit-representative rows carry no sensitivity statement**, and the 42 that do are almost entirely the conductivities â i.e. the sensitivity discipline was applied to the parameter that turns out *not* to be load-bearing, and skipped on the one that is (Î´_stirred, C-5 below).

### The conductivity concern specifically, quantified

Of the 49 registered Îº: 6 `measured-lit`, **41 `lit-representative`, 2 other**. Breaking down the 41 by what the citation field actually contains:

| citation content | n |
|---|---|
| one boilerplate string: *"quaternary-ammonium/organic-solvent conductivity class data; Izutsu, Electrochemistry in Nonaqueous Solutions, 2nd ed. (limiting conductivities)"* | **29** |
| an author surname with no work named (*"Waldvogel HFIP electrolyte reports"* Ã2, *"Fuchigami â¦ reports"* Ã1) | 3 |
| a bare class descriptor with **no source at all** (*"alkali-halide/nitrile conductivity data"*, *"aqueous borate conductivity data"*, â¦) | **8** |
| a specific, checkable paper (Baizer, *J. Electrochem. Soc.* 1964, **111**, 215) | 1 |

So **8 of 49 conductivities name no source whatsoever**, and 29 more share a single string that names a textbook of *limiting* conductivities â a source that cannot supply Îº for a 0.25 M preparative electrolyte.

**But: this weakness barely propagates.** Three independent traces (`grep -rn kappa` over `*.jl`/`*.py`/`*.js`, plus two independent re-implementations of the Fig K heat balance) agree that Îº enters **only** `cellvoltage.jl`, `make_figK.py`, `make_fig4B.py`, `make_figs.py` Fig D and `make_fig_main.py` panel f. It enters **no** transport quantity â `i_lim_tier0` (`correlations.jl:54`) and the NPP/ECâ² solvers take D, C, Î´, z only. The `kappa_mScm` column of `reactions_50.csv` is rendered into Table S2 and consumed by nothing.

**37 of the 41 lit-representative Îº are display-only.** Exactly two carry a conclusion (0.25 M BuâNBFâ/MeCN = 18 mS cmâ»Â¹, 0.2 M NaI/DMF = 8.0), both in Fig K, and both survive Â±2Ã on every architecture except the 250 Âµm microfluidic. **The Îº weakness is real, cosmetically large, and analytically small.** The parameters that actually threaten conclusions are Î´_stirred, Ï, and the retracted electrolytes still live in un-fixed files.

---

## 2. CONFIRMED CRITICAL AND MAJOR FINDINGS, RANKED

All items below were independently re-verified by an adversarial pass; findings the adversarial pass corrected or downgraded are flagged. Every number quoted here was recomputed from the repo's own artifacts.

### CRITICAL

**C-1. A stated conclusion is falsified by the figure it introduces.** `make_si.js:370`
> *"every architecture at 500 mA cmâ»Â² and above falls short passively, in every solvent" â¦ "Passively cooled, every architecture beyond the flow cell boils at its own design current, in every solvent tested."*

`results/figK_thermal.json` `panelB`, 250 Âµm microfluidic (i_design = 500): **DMF 515.62 (margin 1.03Ã, clears)**, **aq. NaOH 841.41 (1.68Ã, clears)**. `panelC` agrees (Uâ²_req 0.008598 and 0.004721 vs `passively_available` 0.009076). Two of four solvents clear. `make_si.js:372` repeats the error ("Because passive rejection fails for the intensified architecturesâ¦"). *(Adversarial correction: the registry-coverage audit's claim that :372 does not repeat the error is itself wrong.)*
**Remediation â `make_si.js:370,372`:** replace the two absolutes with "the two low-conductivity organic media (THF, MeCN) fall short passively at 500 mA cmâ»Â²; DMF and aqueous NaOH clear it, DMF by only 3%." Also note DMF's margin breaks at **Îº Ã 0.93** â a 7% revision of a `lit-representative` value flips the sign, so this sentence must not be stated as a threshold at all.

**C-2. The flagship Â§S6 worked example runs on a retracted electrolyte at a retracted gap, and its conclusion is now false.** `make_si.js:362`
> *"At 100 mA cmâ»Â² with a 5 mm gap in 0.1 M BuâNBFâ/DMF (Îº = 3.5 mS cmâ»Â¹), E_cell = 16.8 V, of which 14.3 V is ohmic â¦ Q = 1.4 W cmâ»Â² â¦ settles just below the DMF boiling point (T_ss â 99 Â°C)"*

Reproduced exactly (16.76 V / 14.29 V / 1.476 W cmâ»Â² / 4.58 K minâ»Â¹) â so all four numbers do come from Îº = 3.5, which `make_si.js:369` **in the same section** declares absent from the registry. T_ss = 98.8 Â°C only with the **superseded** Uâ² = 0.020; with Â§S6.1's own derived Uâ² = 0.017256 it is 110.5 Â°C; with the adopted 0.2 M NaI/DMF at the canonical 2 cm gap it is **172.6 Â°C â DMF boils**, consistent with Fig K panel (a)'s DMF ceiling of 93 < 100 mA cmâ»Â².
**Remediation â `make_si.js:362`:** re-run the example on 0.2 M NaI/DMF (8.0 mS cmâ»Â¹, registered) at 2 cm, quote the resulting E_cell/Q/T_ss, and invert the conclusion to "DMF boils at 100 mA cmâ»Â² in an unstirred beaker" â which is the point the section is trying to make anyway.

**C-3. The Fig K electrolyte fix reached Fig K and the Fig K narrative only. Six other live artifacts still publish the three unregistered electrolytes.** Exact-name diff against registry category 6 confirms zero rows for `0.1 M Bu4NPF6/THF`, `0.1 M Bu4NBF4/DMF`, `1 M KOH aq`, and `Me4N carboxylate (10 mol%)/acetone` (nearest registered acetone entries are 6.0â8.0 mS cmâ»Â¹, 3â4Ã the tabled 2.0).

| file:line | what to change |
|---|---|
| `julia/cellvoltage.jl:14â19` | `ELECS` still `0.06 / 0.35 / 20.0` S mâ»Â¹ â regenerating `cellvoltage.csv` reintroduces them into 60 of its 120 rows |
| `make_si.js:243â246` | **Table S4**: 4 of 8 rows unregistered, under a caption asserting "the full 49-electrolyte registry with per-entry provenance is Table S7f" |
| `figs/make_fig4B.py:134â138` â `sec4_Fig4B_def.png` (**main-text figure**, V5 in `Section4_composite_versions.md:110`, rendered Jul 13) | panel (e) prints "boils at 31" for THF from Îº = 0.06 at 5 mm â the exact parameterisation `make_si.js:369` calls "self-invalidating" |
| `data/make_fig4B.py` | **byte-identical duplicate** (`diff` clean) â a fix to one silently misses the other |
| `figs/make_figs.py:103â107` â `sec4_figD_voltage_joule.png` | same five (Îº, gap) pairs |
| `figs/make_fig_main.py:158â160` â `sec4_MAIN_composite.png` panel f (Jul 12) | same five pairs |

Compounding it in the other direction: `figs/make_figK.py:61â62` claims every Fig K Îº "is reproduced with its class and citation in SI Table S4/S7f" â false for 3 of its 4 (only 3.0 M LiBr/THF is in S4).
**Remediation:** rebuild Table S4 mechanically from registry category 6; replace `ELECS` in `cellvoltage.jl` with registered entries and regenerate `cellvoltage.csv`; delete the duplicate `data/make_fig4B.py`; re-render 4B, D and the composite.

**C-4. The vessel-scaling series was computed with the retracted Îº and contradicts Fig K panel (a) by 1.5Ã.** `make_si.js:373`
> *"For DMF at a 2 cm gap over 10 cmÂ² electrodes the passive ceiling runs 49, 62, 106 and 134 mA cmâ»Â² at 50, 100, 500 and 1000 mL"*

Reproduced exactly (49.0 / 61.8 / 105.9 / 133.5) with Îº = 0.35 S mâ»Â¹. With the adopted 0.80 S mâ»Â¹: **73.7 / 93.1 / 159.7 / 201.4**, and the 100 mL entry then equals `panelB`'s DMF beaker value 93.07 to the digit. The V^(1/3) correction was applied *on top of* the pre-fix conductivity. The 2.15Ã ratio survives (pure 10^(1/3)); every absolute number does not. Note also there is **no volume sweep anywhere in `make_figK.py`** â the series exists only in prose and a docstring comment (`make_figK.py:41`), so it is untraceable to any artifact.
**Remediation â `make_si.js:373` + `figs/make_figK.py`:** add a volume sweep to the script so the series is emitted to `figK_thermal.json`, and quote the recomputed 73.7 / 93.1 / 159.7 / 201.4.

**C-5. The single most load-bearing weak citation in the document is Î´_stirred, not any conductivity.** `data/parameters_provenance.csv:207`
> `7. Reactors | delta (stirred batch) | 100 um | lit-representative | "magnetically stirred cell, ~500 rpm" | Pletcher & Walsh, Industrial Electrochemistry, 2nd ed.`

No page, no number, no measurement â and no sensitivity statement (it is one of the 44 lit-rep rows without one). i_lim â 1/Î´ *exactly* in the fixed-Î´ archetypes. Recomputed from `julia/tier0_ec_matrix.csv`:

| Î´_stirred | median i_lim | â¥25 | â¥50 |
|---|---|---|---|
| 50 Âµm | **34.8** | 29/50 | 17/50 |
| **100 Âµm (adopted)** | **17.4** | 17/50 | 14/50 |
| 200 Âµm | 8.7 | 14/50 | 11/50 |

`make_si.js:382` hangs the industry-validation claim on this: *"the stirred-batch median â¦ is 17 mA cmâ»Â², inside the sub-25 band where 10 of 14 companies sit."* At Î´ = 50 Âµm the median lands in the 25â50 band where **3 of 14** companies sit â **the agreement-with-industry argument inverts under a factor-of-two revision of a bare textbook attribution.** `delta (unstirred batch) = 300 Âµm` (`:206`) carries the same exposure with a self-declared 250â500 Âµm range already spanning 1.7Ã.
**Remediation:** find a page-anchored Î´ for a ~500 rpm magnetically stirred cell (Pletcher & Walsh do give worked boundary-layer estimates â locate and cite the page), **and** add an explicit sensitivity paragraph to Â§S9 showing the 50/100/200 Âµm medians. If no page can be found, the S9 validation claim must be re-worded to "the stirred-batch median falls in the same 10â35 mA cmâ»Â² decade as the surveyed operating window", dropping the band-matching argument.

**C-6 (figure-level, not SI-level).** `figs/make_fig_mediator_k.py` plots a **closed-form toy** (`I = min(300,x_k)/min(10,x_k)`, line 18) that reads no data file, and its grouped annotation "reactor Ã1" (line 54) is contradicted by `julia/mediated_ec_matrix.csv` for 4 of 6 cluster points (thingap/unstirred ratios: SCNâ» 9.9, Brâ» bromination 8.7, BQ Wacker 4.7, NHPI 4.5, Clâ» 8.8, ACT 1.4, HMF 1.7). Its headline reference line "direct substrate: full reactor benefit (Ã30)" (`:28â29`) is **Ã9.0** at the thin-gap archetype's real Î´_eff. Mitigating: `grep mediator_k make_si.js` returns nothing â **the figure is not referenced in the SI**. Fix or drop before it enters the main text.

### MAJOR

**M-1. Ï = 15 is reverse-fitted and contradicts the registry's own derived geometry.** `figs/make_figK.py:80â81` vs `parameters_provenance.csv:223`. Registry: `Vessel external area = 0.0125 m2` (derived, "cylinder ~5 cm dia Ã 8 cm from the 100 mL volume") Ã· 10 cmÂ² = **Ï = 12.5**. Fig K uses 15. The docstring (`make_figK.py:24`) and `make_si.js:369` both claim the 0.020 W cmâ»Â² Kâ»Â¹ still-air value is "recovered **from geometry**"; Ï = 15 actually gives Uâ² = 0.017257 (13.7% low) and Ï = 12.5 gives 0.014381 (28% low). Consequence at Ï = 12.5: panel (a) ceilings **THF 32.3â29.5, MeCN 92.0â83.9, DMF 93.1â84.9**. The load-bearing quantity in all three Fig K panels was chosen to land near the answer, not read off the registered geometry. **Remediation:** either use Ï = 12.5 and re-render, or register the actual vessel dimensions Fig K assumes and drop the "recovers 0.02 from geometry" claim.

**M-2. Fig K's passive-cooling derivation rests on ~20 unregistered numbers.** `figs/make_figK.py:58, 80â84, 154â156`: `H_EXT = 13.0` (registry has h_conv = 7 and h_rad = 6â8 separately, no sum); Ï = 15/15/10/7/0.8; h_int = 100/800/2000/5000 (docstring justification "stagnant ~100, stirred ~800, forced flow >2000" carries no citation); design currents 100/500/1000 (only 25/50 registered, as Ferretti thresholds); gaps 2 cm / 5 mm / 100 Âµm; the three cooling-band edges 8e-4 / 2e-2 / 8e-2 / 2e-1 / 1.0. The zero-gap PEM stack is a sixth architecture present in neither `cellvoltage.jl` `GAPS` nor registry category 7. **Remediation:** add a `9b. Passive cooling geometry` category to `build_param_tables.py` registering all of them (h_int from Incropera with chapter, Ï from the stated vessel dimensions, design currents as `assumption` with the architecture rationale).

**M-3. 18 of 68 rows of `data/electrolytes.csv` have no registry row; 11 have no provenance anywhere.** Cause: `data/build_param_tables.py:150` emits registry rows only for electrolytes appearing in `reactions_50.csv`. Seven have provenance written in `ECOND_PROV` (`:120â139`) that is silently dropped â including **`1 M KOH aq`, whose dict entry is a measured-lit CRC justification ("Îº = 184â215 mS/cm")** that would have made Table S4's 200 defensible, and `0.1 M Bu4NPF6/THF`, which cites Geiger & BarriÃ¨re, *Acc. Chem. Res.* 2010, **43**, 1030. Eleven have nothing: `0.1 M Bu4NBF4/DMF` (3.5), `0.1 M Bu4NBF4/HFIP`, `0.2 M Et4NOTs/MeOH`, `0.5 M H2SO4 aq`, `1 M LiBF4/THF`, `1 M NaBr aq`, `Et3NÂ·3HF/MeCN`, `LiBr/THF`, `Me4NBF4/MeOH`, `emulsion + Na2HPO4/TAEP`, `neat carboxylate/MeOH`. **Remediation â one line:** widen the filter at `build_param_tables.py:150` to emit all of `electrolytes.csv`, then write `ECOND_PROV` entries for the 11 or delete those rows.

**M-4. Hardcoded reactor Î´ contradict the model's own correlation-derived Î´_eff by up to 3.3Ã, and this degrades a stated Fig J reading.** Medians from `julia/mediated_ec_matrix.csv`: unstirred 300, stirred 100, **flow 84.4** (57.2â94.8), **thin-gap 33.5** (22.7â37.6), RDE 13.7, RCE 11.5 Âµm. Against these: `julia/run_profiles.jl:65â66` uses flow 30 Âµm (2.8Ã thin) and thingap 10 Âµm (3.3Ã thin); `figs/make_fig_mediator_k.py:16` `DT = 10.0` labelled "thin gap"; `figs/make_figs.py:38` flow band 20â60 Âµm; `figs/make_fig_nd.py:37` xÌ = 30â100 vs actual 8.0â32.4. **Consequence:** `figs/sec4_figJ_profiles.png` annotates "Î´ = 30 Âµm flow cell: c_surf = 0.69" (`make_fig_profiles.py:66`); at the flow archetype's real Î´ = 84.4 Âµm, i_lim = 57.2 mA cmâ»Â² and **c_surf(50) = 0.125, not 0.69** â "flow survives" is a near-miss, not comfortable. *(Adversarial corrections: `make_figs.py`'s 20â60 band does marginally overlap 57.2â60, so "non-overlapping" overstates it; the xÌ low end is 8.0, not 9.0.)* **Remediation:** drive the figure Î´ from `correlations.jl` rather than hardcoding, and re-annotate Fig J.

**M-5. Eleven `measured-lit` rows cite a CRC locator that does not contain the quantity.** `build_param_tables.py:36` defines one constant â *"CRC Handbookâ¦, 97th ed. (viscosity/density tables, 25 C)"* â reused for 27 rows. Sixteen (Î¼, Ï) are correctly located; the other 11 are not in those tables at all: conductivities at L193 (1 M KHCOâ = 80), L195 (1 M NaâCOâ = 70), **L196 (1 M NaOH = 180)**, L198 (2 M HâSOâ = 700), L199 (2 M NaCl = 160), and cp/Tb at L216âL221. These belong to *Concentrative Properties of Aqueous Solutions*, *Heat Capacity of Liquids*, and *Physical Constants of Organic Compounds*. **This is the locator behind `make_si.js:369`'s "the aqueous reference uses 1 M NaOH (Îº = 180 mS cmâ»Â¹, measured-lit, CRCÂ¹Â²)"** â the one aqueous value *upgraded during the Fig K fix* is labelled measured-lit against a citation that cannot support it. The registry already demonstrates the correct pattern (8 rows name the VanÃ½Å¡ek ion table). Also: 1 M KHCOâ = 80 mS cmâ»Â¹ looks ~20% high against commonly reported â60â66 and should be re-checked. **Remediation â `build_param_tables.py:36`:** split into three named locator constants and re-emit.

**M-6. `provenance_class` is assigned by the value, not by the source.** `build_param_tables.py:63`: `"lit-representative" if phi!=1.0 else "measured-lit"`. Consequence: the 11 Ï = 1.0 rows (MeCN, DMF, DMA, DMSO, THF, **AcOH**, acetone, MeNOâ, HFIP + two mixtures) are `measured-lit`, while HâO 2.6, MeOH 1.9, EtOH 1.5 â **the only three values Wilke & Chang 1955 actually tabulates** â are `lit-representative`. The classification is inverted relative to the source. Worse, lines 89 and 99 (DMSO/THF, AcOH/HCOOH) are `measured-lit` while their own method_note reads *"mixtures: fitted so phi*M = P-G rule"*. AcOH â a hydrogen-bonded dimerising acid â is where the Ï = 1.0 default is least defensible. **Remediation:** class Ï by source: `measured-lit` for HâO/MeOH/EtOH, `assumption` (WilkeâChang default for unassociated solvents) for the Ï = 1.0 set, `derived` for the fitted mixtures.

**M-7. Twenty `measured-lit` rows cite the literal string `standard`; for the 8 mixtures the value is a fitted quantity and the note is wrong.** `build_param_tables.py:60` emits every solvent M â pure and mixture â as `measured-lit` / `"standard"` / *"molar mass (mixtures: volume-weighted)"*. The 12 pure-solvent M are numerically correct (verified against IUPAC weights); the 8 mixture M are not molar masses at all. Reproduction attempt: three match mole-fraction averaging, one matches volume-fraction, four match neither within 5%. Independent cross-check on MeOH/HâO 1:1: **ÏM = 1.94 Ã 26.4 = 51.2, exactly the Poling mole-fraction rule Î£xáµ¢Ïáµ¢Máµ¢ = 51.15** â confirming (M, Ï) is a *fitted pair*, source Poling Eq. 11-9.8, class `derived`. **Remediation:** reclass the 8 mixture rows as `derived` citing Poling; fix the note (it is right for exactly one of eight); replace `"standard"` on the 12 pure M with "IUPAC atomic weights 2021".

**M-8. One `measured-lit` row stands in for 50 concentration values, 10 of which its own note excludes, with a self-referential citation â and it disagrees with the SI prose.** `parameters_provenance.csv:153`, citation `"Table S2 per-row citations + anchors"`, note: *"PAGE-VERIFIED â¦ for 40/50 rows; 8 rows main-text-unverifiable â¦; 1 anchored to a physically absent book chapter (BASF); 1 by stated analogy."* `make_si.js:251` says **"Forty-nine of the fifty rows are so verified â forty-one against main-article PDFs and eight more against their Supporting Materials."** The registry (40 + 8 + 1 + 1) and the prose (49/50) genuinely disagree about how many are page-verified. L154 has the same self-referential defect (citation: `Table S2`). Two `correlation-est` rows (L151, L152) cite project files (`reactions_50.csv`, `build_reactions50.py conventions`) rather than sources. **Remediation:** explode L153 into 50 individually classed rows carrying the Table S2 anchors, or at minimum reconcile the two counts and downgrade the 10 unverified rows to `lit-representative`/`assumption`.

**M-9. `3.0 M LiBr/THF = 3.0 mS cmâ»Â¹` is classed `measured-lit` but its own note describes an order-of-magnitude estimate.** `parameters_provenance.csv:187` / `build_param_tables.py:127`: the note page-anchors the **composition** (LiBr 1.0 mol / 320 mL THF, Peters *Science* 2019 SM p. S15) and then says *"heavily ion-paired ether medium, kappa order-of-mS/cm"* â a 1-decade statement. `make_si.js:369` nevertheless asserts "Îº = 3.0 mS cmâ»Â¹, **measured-lit**, from the supporting information of the 100 g Birch flow process." **This is the single most load-bearing Îº in the SI**: it drives "THF boils at 32 mA cmâ»Â²", "already failing for THF", "THF clears none of them", and the whole S6.2 cooling-duty narrative. Break factor **Îº_THF Ã 2.42** â so the claim survives a 2Ã with only ~10% margin (45.1 vs 50 mA cmâ»Â²), and does not survive the decade its own note implies. The Peters SM is not in the tree, so this could not be checked further. **Remediation:** either locate a measured Îº for a concentrated LiBr/THF medium, or reclass to `lit-representative` and re-word `make_si.js:369` to "Îº ~3 mS cmâ»Â¹ (order-of-magnitude, from the composition reported in the Peters SM)" â with the THF conclusion stated as directional, not as a threshold crossing.

**M-10. Load-bearing illustrative constants absent from the registry.**
- `julia/run_profiles.jl:2â4,11â13`: `C_S = 500` mol mâ»Â³, `D_S = 1e-9` mÂ² sâ»Â¹, `C_sup = 100`. With n = 1 and Î´ = 100 Âµm these give **i_lim = 48.2 mA cmâ»Â²** â the "the '50 mA/cmÂ² barrier' IS the stirred-beaker boundary layer" centrepiece of `figs/make_fig_profiles.py:4â5`. A rhetorical headline resting on an unregistered C/D/n triple.
- `figs/make_figL.py:36`: *"bulk GâL capacity (k_L a = 0.05 sâ»Â¹, 100 mL) â 4.8 A â« 1.3 A cell current."* Arithmetic checks (4.82 A). **`k_L a = 0.05 sâ»Â¹` appears in no registry row and no category covers gasâliquid mass transfer at all** â this number carries a quantitative sufficiency claim inside a rendered figure.
- `figs/make_fig_nd.py:27â28,56` (`mu = 0.041`, `eps = 0.060`, `C_med = 20`, `D_med = 6e-10` â Î³ = 41.7), duplicated at `make_fig_main.py:140`; `figs/make_fig_carrier.py:71,73,88` (`D = 6e-6` / `1e-5` cmÂ² sâ»Â¹, `Ccat = 0.010` M).
**Remediation:** add a `12. Illustrative figure constants` category; k_L a needs a real correlation source (Van't Riet / stirred-tank literature) before Fig L's claim can stand.

**M-11. The cooling-envelope sentence has wrong units, matches nothing, and contradicts the section written to refute it.** `make_si.js:362`: *"Passive air and stirred-liquid heat rejection saturate near 0.01 and 0.1 W cmâ»Â²."* Units must be W cmâ»Â² Kâ»Â¹. Registry gives 0.020 and 0.18; Â§S6.1's derivation gives 0.017256 and 0.019188 (both in `figK_thermal.json`), and Â§S6.1 states outright that "stirring a beaker is nearly useless thermally". Neither quoted number matches either pair. The 0.1 traces to `parameters_provenance.csv:227` â `U' stirred bath = 0.18, lit-representative, "bath-jacketed glass"` â i.e. a **jacketed bath with external coolant silently reused as an unjacketed stirred beaker**. Related: the same sentence says "heat fluxes of 1â10 W cmâ»Â² are routinely rejected" where the cited WallnÃ¶fer-Ogris anchor (`:228`) says **2â6**.

**M-12. Two figure-to-data chains are broken.**
- `sec4_figH_ecprime.png` **has no generator in the tree** (repo-wide `grep figH` returns nothing; the savefig inventory covers AâG, IâM but not H). `make_si.js:331` cites "Fig. H, open squares" for the total-catalysis substitution, and those open squares match **no data file**: `julia/npp_ecprime_sweep.csv` gives 46.4 / 29.3 / 19.3 (decreasing) at k = 3e3/1e4/1e5, `results/npp_ecprime_sweep.csv` gives 27.6 / 0.34 / 1.82 â neither is the flat ~48 cap drawn in the PNG. The filled circles are traceable (k = 1e3 â 41.863).
- `figs/make_figs.py:128` reads `julia/npp_support_sweep.csv` and `julia/npp_profiles.csv` for Fig E; **neither exists at that path** (`run_section4.jl` writes to its own cwd; both live only in `results/`, mtime Jul 10, older than the Jul 12 render). The data itself is real and matches the SI (2.000 / 1.380 / 1.180 / 1.040, `make_si.js:320`), but Fig E cannot currently be regenerated.

**M-13. `U' PEM-class cooled plates = 0.30` is classed `measured-lit` but is a mid-range pick.** `parameters_provenance.csv:228`; the note ("2â6 W cmâ»Â² across 10â20 K gradients") implies a bracket of 0.1â0.6. Reclass `derived`. This is one of two inputs to Fig K(c), so it matters before that panel's margins are read quantitatively. The citation (WallnÃ¶fer-Ogris, *Front. Chem. Eng.* 2024, **6**, 1384772) is itself specific and usable.

**M-14. The corrected inventory claim never reached the registry.** `parameters_provenance.csv:222`: `Cell volume / electrode area | 100 mL / 10 cm2 | assumption | "representative batch cell; steady state independent of volume (S6.1)"` â verbatim the claim Â§S6.1 was rewritten to refute, and it is **rendered into Table S7i of the shipped v3 `.docx`**. The registry is the machine-readable artifact; the fix is incomplete.

**M-15. "Margins of 1.8Ã each" is a Îº-artefact quoted to two significant figures.** `make_si.js:370`; JSON gives 1.840 (MeCN) and 1.861 (DMF), both off `lit-representative` Îº. Under Â±2Ã: 1.31â2.62Ã. The qualitative claim ("thermally marginal", margin > 1) is robust â MeCN's break factor is 0.288 â but the precision is not. State "margins under 2Ã" rather than "1.8Ã each".

### MINOR (confirmed, listed compactly)

`make_si.js:373` â stale "5 mm gap" beaker caveat survives the 2 cm correction and double-counts it (same stale label at `make_figK.py:188`, which prints "UNSTIRRED BEAKER, 5 mm" while `Lb = 2.0e-2`) Â· `make_si.js:373` â Ï â 16 min and â 19 min for the same beaker; **19 is correct** (193.5 J Kâ»Â¹ / 0.17256 W Kâ»Â¹), 16 uses the retired UA = 0.20 *(this supersedes the registry-coverage audit's THF/DMF reading, which the adversarial pass showed does not arithmetically work: THF gives 14.7 min, not 16)* Â· `make_si.js:373` â "some 400Ã faster" is the raw volume ratio; dividing out the UA ratio gives **210Ã**, and neither Ï is emitted by any artifact Â· `make_si.js:372` â "spanning two orders of magnitude" is 98.5Ã only across architectures; at fixed architecture the solvent-driven span is 41.7Ã / 12.4Ã / 9.7Ã Â· `parameters_provenance.csv:221` â `aq. KOH: Tb` is the only registered aqueous boiling point while Fig K now uses 1 M NaOH (value unaffected, label stale) Â· no cp registered for MeCN or water, so those two Fig K Ï are unbacked Â· `parameters_provenance.csv:231` registers film nodes N = 80/90 while `run_section4.jl:42,51,60,72` uses **N = 60** for the runs that produce `npp_support_sweep.csv` and `npp_profiles.csv` (Fig E) Â· Table S4's caption says its rows are "used in the cell-voltage stack" but 2 of 8 are not in `cellvoltage.jl`, and `0.3 wt% HâSOâ/MeOH` appears there under a different label Â· 25 orphaned registry rows (DMSO, EtOH, AcOH, EtOH/HâO, DMF/HâO Ã 5 properties each, none in `reactions_50.csv`) Â· solver species gaps: Hâº = 2.0e-9 in AcOH/HCOOH (registry has 9.3e-9 / 3.0e-9 / 5.0e-9, no 2.0e-9), B(OH)â reusing the B(OH)ââ» row, NHââº row scoped "(MeCN)" but consumed in AcOH/HCOOH, RCOââ» = 8.0e-10 unregistered *(the Aâ» = 1.5e-9 sub-claim is wrong â that value **is** registered)* Â· nine registry citations never enter the numbered `REFS` list (WallnÃ¶fer-Ogris, Sander, Incropera, Cussler, Pickett, Colomer, Amatore, VanÃ½Å¡ek, CODATA â *Izutsu is in `REFS`, contra the citation audit*) Â· 6 rows cite bare "CRC" with no edition Â· `REFS.kelly2026` has `volume: null`; Crossref gives **2026, 30, 1926â1936**.

**Downgraded by the adversarial pass â do not act on as stated:** *"roughly a factor of five"* (`make_si.js:372`) was flagged as wrong; verdict **UNCERTAIN**. THF/DMF is 7.96/6.82/6.44 but the sentence brackets MeCN *and* DMF, and THF/MeCN is 7.33/5.01/4.44 â "roughly five" is fair at two of three architectures. The compounding-of-two-lit-representative-errors concern stands (a 2Ã on DMF's Îº alone swings the ratio 3.9â14.9), so add a sensitivity note; do not change the number.

---

## 3. PRIORITISED REMEDIATION PLAN

### Tier 0 â do before anything else (statements currently false or self-contradictory)
1. `make_si.js:370,372` â rewrite the "every architecture / in every solvent" sentences (C-1).
2. `make_si.js:362` â re-run the Â§S6 worked example on a registered DMF electrolyte at 2 cm; invert its conclusion (C-2).
3. `make_si.js:373` â replace the vessel-scaling series with 73.7 / 93.1 / 159.7 / 201.4; delete the stale 5 mm caveat; fix Ï (19 min) and 400Ã â 210Ã (C-4, minors).
4. `make_si.js:362` â fix the units and values of the cooling-envelope sentence; stop reusing the jacketed-bath Uâ² for an unjacketed beaker; narrow 1â10 to the cited 2â6 W cmâ»Â² (M-11).

### Tier 1 â parameters that most urgently need a real citation (ranked by conclusion-exposure)
| rank | parameter | file | why urgent |
|---|---|---|---|
| 1 | **Î´_stirred = 100 Âµm** | `parameters_provenance.csv:207` | 2Ã revision inverts the industry-agreement claim (C-5). Needs a page anchor **and** a sensitivity statement. |
| 2 | **Ï (vessel area ratio)** | `make_figK.py:80â84` | reverse-fitted; sets every Fig K ceiling (M-1). Register the vessel dimensions or adopt Ï = 12.5 and re-render. |
| 3 | **Îº(3.0 M LiBr/THF)** | `parameters_provenance.csv:187` | only `measured-lit` Îº in Fig K; the entire THF narrative rests on it; note says "order-of-mS/cm" (M-9). |
| 4 | **h_int (100/800/2000/5000) and H_EXT = 13** | `make_figK.py:22,58,80â84` | 20 unregistered numbers doing the actual work in all three Fig K panels (M-2). |
| 5 | **Îº(1 M NaOH) = 180**, and the other 10 mis-located CRC rows | `build_param_tables.py:36` | the aqueous anchor upgraded *during the fix* is labelled `measured-lit` against a locator that cannot support it (M-5). Cheap fix: name the right CRC tables. |
| 6 | **Î´_unstirred = 300 Âµm** | `parameters_provenance.csv:206` | self-declared 250â500 range already spans 1.7Ã; sets the 300 Âµm archetype used everywhere. |
| 7 | **k_L a = 0.05 sâ»Â¹** | `make_figL.py:36` | carries a quantitative sufficiency claim in a rendered figure with zero provenance and no covering category (M-10). |
| 8 | **C_S = 500 / D_S = 1e-9 / C_sup = 100** | `run_profiles.jl:2â4,11â13` | produce the "50 mA cmâ»Â² barrier" headline (M-10). |
| 9 | The 11 electrolytes with no provenance anywhere | `build_param_tables.py:120â139` | M-3. Seven more are free â just widen the filter at line 150. |
| 10 | Îº(1 M KHCOâ) = 80 mS cmâ»Â¹ | `parameters_provenance.csv:193` | value looks ~20% high vs commonly reported 60â66; verify or correct. |

### Tier 2 â classification hygiene (no new sources needed, only honest relabelling)
- `build_param_tables.py:63` â stop assigning class by value; reclass the 11 Ï rows (M-6).
- `build_param_tables.py:60` â reclass the 8 mixture M as `derived`/Poling; replace `"standard"` with IUPAC on the 12 pure M; fix the "volume-weighted" note (M-7).
- `parameters_provenance.csv:228` â `U' PEM = 0.30` â `derived` (M-13).
- `parameters_provenance.csv:222` â delete the repudiated "independent of volume" note (M-14).
- `parameters_provenance.csv:153,154` â reconcile 40/50 vs 49/50 with `make_si.js:251`; downgrade the 10 unverified concentrations (M-8).
- `parameters_provenance.csv:221` â relabel the aqueous Tb row to NaOH; add cp for MeCN and water.
- `parameters_provenance.csv:231` â register N = 60.
- Add `REFS` entries for the nine registry-only citations, or state explicitly that the S7 tables use a separate citation system.
- Update `REFS.kelly2026` to **2026, 30, 1926â1936**.

### Tier 3 â code/artifact hygiene (correctness of the record, not of the physics)
Purge the three retracted electrolytes from `cellvoltage.jl`, Table S4, `make_fig4B.py` (+ delete the `data/` duplicate), `make_figs.py`, `make_fig_main.py`, and regenerate `cellvoltage.csv`, Fig 4B, Fig D and the composite (C-3). Drive figure Î´ from `correlations.jl` instead of hardcoding, and re-annotate Fig J's c_surf (M-4). Restore or delete Fig H's generator and fix `make_figs.py:128`'s path so Fig E is reproducible (M-12). Fix or drop `make_fig_mediator_k.py` (C-6).

### Conclusions that must be **softened** if a citation cannot be found
1. **"the stirred-batch median â¦ inside the sub-25 band where 10 of 14 companies sit"** (`make_si.js:382`) â "falls in the same 10â35 mA cmâ»Â² decade as the surveyed operating window". *This is the one that must go if Î´_stirred stays bare-cited.*
2. **"THF boils at 32 mA cmâ»Â², below the 50 mA cmâ»Â² design current"** and the S6.2 THF narrative â "THF's low conductivity puts its passive ceiling at the same order as typical design currents; the margin is order-unity and the underlying Îº is known only to within roughly a decade."
3. **"every architecture â¦ in every solvent"** (C-1) â must be replaced regardless; the JSON falsifies it.
4. **"margins of 1.8Ã each"** â "margins under 2Ã" (M-15).
5. **"required duty spanning two orders of magnitude, set by solvent conductivity"** â "spanning roughly a decade at fixed architecture, and two decades once architecture is varied."
6. **"recovers from geometry the 0.02 W cmâ»Â² Kâ»Â¹ still-air value"** (`make_si.js:369`, `make_figK.py:24`) â drop the word "recovers"; it reproduces 0.0173 from a Ï that is not the registered geometry's 12.5.
7. **Fig L's "bulk GâL capacity â« cell current"** â keep only if k_L a gets a source; otherwise state it as an order-of-magnitude sufficiency argument.
8. **Fig J's "c_surf = 0.69, flow survives"** â recompute at Î´_eff = 84.4 Âµm (c_surf = 0.13) or relabel the archetype.

---

## 4. WHAT VERIFIED CLEAN

Independently re-checked and correct:

- **Generator â artifact.** The shipped `SI_Section4_Transport_Model_v3.docx` is text-identical (128,600 chars of `word/document.xml`, both extractions) to the current output of `make_si.js`. `_v3` is a copy, not a hand-edit.
- **`auditRefOrder()` runs and passes**: 84 references, 113 citation sites, 0 uncited, first-appearance order correct, 84/84 keys used.
- **All 84 `REFS` entries are real.** 72 journal entries resolved against Crossref (59 auto-matched on volume + first page; the 13 misses were article-number/un-volumed artefacts, each confirmed by DOI). All three patents verified against Google Patents, including the SI's assertion that EP 0011712 A2's claims specify **5â50 wt%** methylbenzene. En dashes consistent throughout; "et al." used only for â¥11-author papers (all 7 checked). Only `kelly2026` is stale.
- **`solvents.csv` â registry category 2**: all 20 solvents Ã 5 properties present with identical values, including all 8 blends.
- **`reactions_50.csv` â registry category 6**: 49/49 electrolytes registered, all Îº match `electrolytes.csv` exactly, zero value mismatches, zero orphaned Îº.
- **`reactions_50.csv` solvent column** 100% resolvable in `solvents.csv`; Î¼ consistent row-by-row.
- **MedSpec kinematic viscosities** (`run_mediated.jl`, `run_scn.jl`: 4.42e-7, 8.93e-7, 3.90e-7, 5.85e-7, 9.57e-7) all reproduce Î¼/Ï of registered solvents to 3 s.f.
- **All 50 carrier D values** reconcile with the WilkeâChang / StokesâEinstein / NernstâEinstein methods of category 3 and with the solver mediator D exactly (ACT 5.93e-10, ClâNHPI 2.09e-9, HâQ 1.78e-9, Brâ»/MeCN 2.7e-9, Clâ» 2.03e-9, SCNâ» 7.8e-10). The S8 claim "45 correlation estimates â 34 WilkeâChang, 11 StokesâEinstein â and 5 NernstâEinstein" matches `reactions_50.csv` exactly.
- **Numerics (category 11) match the code character-for-character**: `tol=1e-9`, `max_log_step=2.0`, FD step `1e-7*max(|u|,1)`, collapse `1e-3`, ramp `growth=1.15`, and `dx1 = clamp(xk/50, 0.02e-6, 0.9*d/90)`.
- **Fig K's four Îº match their registry rows to the digit** (3.0 / 18 / 8.0 / 180 mS cmâ»Â¹ â 0.30 / 1.80 / 0.80 / 18.0 S mâ»Â¹), and **every number in the Fig K prose matches `results/figK_thermal.json` exactly** (32 / 92 / 93 / 316; DMF 93/98/159/516/176; THF 0.042/0.059/0.099). Two independent re-implementations of the heat balance reproduced the JSON to all printed digits.
- **Fig K's "robust to a factor of two" claim is verified** for the beaker, stirred and 5 mm flow architectures: under Â±2Ã on Îº, THF stays below its 50 mA cmâ»Â² design current (23â46) and MeCN/DMF stay above (66â131). Only the 250 Âµm microfluidic column is sign-fragile.
- **Migration-sweep numbers in Â§S5** (2.00, 1.38, 1.18, 1.04, and 1.000 at 50Ã support) match `results/npp_support_sweep.csv` to the digit.
- **Fig 3 anchors** (6.1, 17.4, 127) match the `tier0_ec_matrix.csv` medians (6.06, 17.40, 127.4).
- **`make_si.js:274â293` renders all 236 registry rows faithfully** into Tables S7aâS7k with no filtering â the registry is fully exposed, which is why its defects are auditable at all.
- **The 12 pure-solvent molar masses** cited as `"standard"` are numerically correct.
- **`us5507922` is not an error**: `REFS` gives the 1996 grant year, the registry the 1993 priority year, and the body says "prio. 1993" â Google Patents confirms priority 1993-08-14, grant 1996-04-16.

---

## 5. THE HONEST BOTTOM LINE ON THE NON-AQUEOUS BASIS

**Yes â the non-aqueous conductivity basis of this SI is representative, not measured, and it should be described that way in print.** Of 49 registered conductivities, 6 are measured (5 CRC aqueous + one THF entry whose own note concedes "order-of-mS/cm"). Forty-one are class estimates, 29 of them sharing a single boilerplate citation to a book of *limiting* conductivities, and 8 naming no source at all. The same is true, less visibly, of the non-aqueous *transport* basis: 45 of 50 carrier diffusivities are correlation estimates (WilkeâChang / StokesâEinstein), 12 solver-species D are `lit-representative`, and 27 of the 100 solvent-property rows are `lit-representative` â including the WilkeâChang association parameters, which for the mixtures were **fitted in this work** and mislabelled.

**What that does not undermine.** The transport ceilings â the actual argument of Section 4 â do not touch Îº at all. `i_lim_tier0` and the NPP/ECâ² solvers take D, C, Î´ and z only; the entire 50-reaction matrix, the carrier taxonomy, the migration/support sweep, and Figs AâC, FâJ and LâM are untouched by the conductivity weakness. Because the ceilings are ratios and scalings over a consistent D basis, systematic error in the correlation-estimated D largely cancels: the *ordering* of archetypes and the *decade* of each ceiling are robust, and the numerics, correlations and reaction-table arithmetic all check out exactly. The physics of the paper is not in question.

**What it does undermine.** Three things, precisely. (i) **The word `measured-lit` in the SI's own prose** â every place the text points at the class label as evidence ("Îº = 180 mS cmâ»Â¹, measured-lit, CRC"; "Îº = 3.0 mS cmâ»Â¹, measured-lit") is a claim the registry cannot currently back, and a referee who opens Table S7f will find that out. (ii) **Two-significant-figure quantities** â "1.8Ã margins", "a factor of five", "two orders of magnitude", "62 mA cmâ»Â² at 100 mL" â none of these carries the precision implied, and one of them (62) is 1.5Ã off the figure it introduces. (iii) **Any sentence phrased as a threshold crossing in Fig K**, because the crossings sit inside the uncertainty: DMF's microfluidic margin flips at Îº Ã 0.93.

**And the sharpest point:** the parameter the author is most worried about is not the one that will break. Conductivity is 84% representative and almost entirely decorative. **Î´_stirred = 100 Âµm is a single `lit-representative` number with a page-less textbook attribution and no sensitivity statement, and it alone decides whether the SI's central industry-validation claim holds or inverts.** Fixing Î´_stirred's citation and adding its sensitivity paragraph is worth more than re-sourcing all 41 conductivities.",
    "verdicts": [
      {
        "verdicts": [
          {
            "finding": "registry-coverage C1 / lit-rep-risk C2 â SI's "every architecture at 500 mA cmâ»Â² and above falls short passively, in every solvent" is falsified by results/figK_thermal.json",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "Read make_si.js:370 and results/figK_thermal.json directly. panelB at the 250 Î¼m microfluidic (i_design 500): DMF 515.62 (1.03Ã), aq. NaOH 841.41 (1.68Ã) â both clear. panelC agrees: U'_req 0.008598 (DMF) and 0.004721 (NaOH) vs passively_available 0.009076. Two of four solvents clear; the sentence says none do, twice. Auditors quoted the JSON values to the digit."
          },
          {
            "finding": "registry-coverage C2 / citation-integrity Â§1 / lit-rep-risk M6 / figure-data-trace C1 â the three unregistered electrolytes are still live in cellvoltage.jl, Table S4, Fig 4B, figD, MAIN_composite and the Â§S6 worked example",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "Verified each location: julia/cellvoltage.jl:13-19 ELECS = 0.06/0.35/20.0 S mâ»Â¹; make_si.js:243-246 Table S4 rows 0.6/3.5/200; figs/make_fig4B.py:134-138 and figs/make_figs.py:102-107 and figs/make_fig_main.py:158-160 all carry the same five (Îº,gap) pairs; make_si.js:362 worked example uses Îº = 3.5. Registry category 6 (49 rows, dumped in full) contains none of 0.1 M Bu4NPF6/THF, 0.1 M Bu4NBF4/DMF, 1 M KOH aq, nor Me4N carboxylate (10 mol%)/acetone (nearest acetone rows 6.0-8.0 mS/cm). sec4_Fig4B_def.png (Jul 13) and sec4_MAIN_composite.png (Jul 12) are current renders, not in _superseded/. make_figK.py:61-62 also claims Fig K's Îº are "reproduced ... in SI Table S4" â false for 3 of its 4 (only 3.0 M LiBr/THF is in S4)."
          },
          {
            "finding": "registry-coverage M1 â 18 of 67 rows of data/electrolytes.csv have no registry row; 11 have no provenance anywhere",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Set-differenced electrolytes.csv (67 rows) against registry category 6: exactly 18 missing, and the 18 names match the auditor's list item-for-item. build_param_tables.py:150 filters by reactions_50.csv, so 7 entries that DO have ECOND_PROV provenance (incl. 1 M KOH aq with a measured-lit CRC note, and 0.1 M Bu4NPF6/THF citing Geiger & Barriere) are silently dropped; the remaining 11 appear in neither the dict nor the registry."
          },
          {
            "finding": "registry-coverage M2 / figure-data-trace M3 â Fig K's passive-cooling derivation rests on ~19 unregistered numbers, and Ï=15 conflicts with the registry's own derived vessel area",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "make_figK.py:58,80-84,154-156 hardcode H_EXT=13, Ï=15/15/10/7/0.8, h_int=100/800/2000/5000, i_design=50/50/100/500/1000, and the three cooling bands. Registry category 9 has only h_conv=7 and h_rad=6-8 (no sum, no h_int), category 7 has only thresholds 25/50 (no design currents), and no Ï rows. Registry 'Vessel external area 0.0125 m2' Ã· 10 cmÂ² = 12.5, not 15. I recomputed: Ï=15 â U'=0.017257 (13.7% below the registered 0.020 from UA=0.20 W/K); Ï=12.5 â 0.014381 (28% below). The zero-gap 100 Î¼m stack is absent from cellvoltage.jl GAPS and from category 7."
          },
          {
            "finding": "lit-rep-risk M11 â Ï=15 is reverse-fitted; with the registry's own geometry the panel-(a) ceilings drop to 29.5 / 83.9 / 84.9",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Re-ran make_figK.py's own i_boil with Ï=12.5: THF 29.5, MeCN 83.9, DMF 84.9 mA cmâ»Â² (vs 32.3/92.0/93.1 at Ï=15) â matches the auditor exactly. The docstring (make_figK.py:24) and make_si.js:369 both claim the 0.02 W cmâ»Â² Kâ»Â¹ still-air value is 'recovered from geometry', but the registered geometry gives 0.0144, not 0.0173."
          },
          {
            "finding": "registry-coverage M3 â hardcoded reactor Î´ in run_profiles.jl and four figures contradict the model's own correlation-derived Î´_eff by up to 3.3Ã, degrading Fig J's 'flow survives' reading",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Computed medians from julia/mediated_ec_matrix.csv: flow 84.38 (57.22-94.83), thin-gap 33.49 (22.71-37.63), RDE 13.69, RCE 11.47 Î¼m â the auditor's values to 3 s.f. run_profiles.jl:65 uses flow 30 Î¼m / thingap 10 Î¼m; make_fig_mediator_k.py:16 DT=10.0 labelled 'thin gap'. Fig J consequence verified: at Î´=84.4 Î¼m, i_lim = 57.2 and c_surf(50) = 0.125, not the annotated 0.69 (make_fig_profiles.py:66). Two small slips: make_figs.py:38's flow band 20-60 Î¼m does marginally overlap 57.2-60 (not strictly 'non-overlapping'), and the make_fig_nd.py xÌ low end is 8.0 not 9.0. Substance unaffected."
          },
          {
            "finding": "registry-coverage M4 â load-bearing illustrative constants (C_S/D_S/C_sup, Î¼/Îµ, generic figure D, k_L a) absent from the registry",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "run_profiles.jl:11-13 C_S=500, D_S=1e-9, C_sup=100 confirmed; i_lim = 0.1Â·96485Â·1e-9Â·500/1e-4 = 48.2 mA cmâ»Â², the '50 mA cmâ»Â² barrier' centrepiece of make_fig_profiles.py:4-5. make_fig_nd.py:27-28,56 and the duplicated block at make_fig_main.py:140 confirmed. make_fig_carrier.py:71,73,88 D=6e-6/1e-5 cmÂ² sâ»Â¹, Ccat=0.010 confirmed. make_figL.py's k_L a = 0.05 sâ»Â¹ confirmed in the rendered annotation; grep of parameters_provenance.csv returns no k_L a row and no gas-liquid category. Registry category 5 registers only per-row Table S2 concentrations, propylene C_sat and trace initializations."
          },
          {
            "finding": "registry-coverage M5 â solver species diffusivity gaps (H+ 2.0e-9, B(OH)3 0.96e-9, NH4+ scope, generic A-)",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "run_scn.jl:42 and run_mediated.jl:103 use H+ = 2.0e-9 in AcOH/HCOOH; registry category 4 registers H+ only at 9.3e-9 (aq), 3.0e-9 (MeCN/organic), 5.0e-9 (1:1 aq/MeCN) â no 2.0e-9 row. B(OH)3 at 0.96e-9 (run_mediated.jl:76) reuses the B(OH)4- row. NH4+ row is scoped '(MeCN, used aq-like)' but consumed in AcOH/HCOOH. run_section4.jl:41 A- = 2.0e-9 and :48 RCO2- = 8.0e-10 are unregistered. One sub-claim is weak: A- = 1.5e-9 IS registered as 'BF4-/generic A- (organic) = 1.5e-9', so that instance is covered. Impact is documentation-level; values are defensible."
          },
          {
            "finding": "registry-coverage m1 / lit-rep-risk M8 â registry row 222 still carries the repudiated 'steady state independent of volume' note and is rendered into Table S7i",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "parameters_provenance.csv line 222 reads verbatim: 'Cell volume / electrode area,100 mL / 10 cm2,-,assumption,representative batch cell; steady state independent of volume (S6.1),--'. make_si.js:373 item (ii) explicitly refutes it. The registry is the machine-readable artifact and was not updated."
          },
          {
            "finding": "registry-coverage m2 / citation-integrity Â§7 tail / lit-rep-risk minor â 'aq. KOH: Tb' is the only registered aqueous boiling point while Fig K now uses 1 M NaOH",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Registry line 221 is 'aq. KOH: Tb, 100.0 C'; make_figK.py:71 uses '1 M NaOH aq'. Value unaffected (both 100 Â°C); the label is stale. Note the row is not strictly orphaned in the tree â make_fig4B.py still models 'aq. KOH, 1 mm' at Tb = 100."
          },
          {
            "finding": "registry-coverage m3 / lit-rep-risk M12 â stale '5 mm gap' beaker caveat survives the 2 cm correction, in both make_si.js:373 and make_figK.py:188",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "make_si.js:373 item (i): 'real beaker setups space electrodes 1-2 cm apart rather than 5 mm ... The boil-off currents quoted for 5 mm gaps are therefore upper bounds', while item (ii) in the same paragraph specifies the beaker at 2 cm. make_figK.py:188 prints '(a) UNSTIRRED BEAKER, 5 mm' with Lb = REACTORS[0][1] = 2.0e-2. Both verified in the files."
          },
          {
            "finding": "registry-coverage m4 â make_si.js:373 gives Ï â 16 min and â19 min for the same 100 mL beaker; the two come from two different solvents (THF and DMF)",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "The inconsistency is real (both figures appear in the same paragraph for the same cell), and the sub-claim that no c_p is registered for MeCN or water is correct (category 9 has c_p for THF and DMF only). But the attribution is wrong: THF gives 88.3Â·1.72/0.17256 = 14.7 min, which does not round to 16. 16.1 min is DMF with the superseded UA = 0.20 W Kâ»Â¹ (193.5/0.2), as the lit-rep-risk audit concluded. Defect confirmed, cause misdiagnosed."
          },
          {
            "finding": "registry-coverage m5 â Table S4's caption claims its eight rows are 'used in the cell-voltage stack (Section S6)', but two are not in cellvoltage.jl and one appears under a different label",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "cellvoltage.jl:13-19 holds six electrolytes; Table S4's '2 M NaCl (aq)' and 'Me4N carboxylate (10 mol%)/acetone' are absent from it, and S4's '0.3 wt% HâSOâ/MeOH' appears in the stack as '0.03 M H2SO4 / MeOH (BASF)'. build_param_tables.py:134 gives 0.3 wt% â 0.025 M, so only the label diverges."
          },
          {
            "finding": "registry-coverage m6 â registry registers film nodes N = 80/90 while run_section4.jl uses N = 60 for the datasets behind Fig E",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "julia/run_section4.jl uses FilmProblem(..., 60) at gate A, gate B, the support sweep and the profile dump â the loops that write npp_support_sweep.csv and npp_profiles.csv. Registry line 231 registers 'Film nodes N (Tier-1 / EC') = 80 / 90' only; run_profiles.jl defaults N=80 and run_ecprime.jl N=90, so 60 is uncovered."
          },
          {
            "finding": "registry-coverage m7 â 25 orphaned registry rows (five unused solvents Ã five properties)",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "reactions_50.csv uses 15 solvents; solvents.csv registers 20. DMSO, EtOH, AcOH, EtOH/H2O 1:1, DMF/H2O 9:1 appear in no reaction row â 5 Ã 5 property rows = 25. One sub-claim is wrong: the cooling ladder 0.020/0.18/0.30 is consumed by figs/make_fig4B.py:139 only; make_fig_main.py contains no COOL list (its panel f is the voltage plot). The 'not really orphans' qualification therefore rests on one file, not two."
          },
          {
            "finding": "registry-coverage m8 â data/make_fig4B.py and figs/make_fig4B.py are byte-identical duplicates",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "diff -q returns no difference; a fix to one will miss the other."
          },
          {
            "finding": "registry-coverage propagation analysis â 37 of 41 lit-representative Îº are display-only; only the two Fig K lit-rep Îº carry a conclusion, and the sign-flip risk is confined to the microfluidic column",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Îº appears only in cellvoltage.jl, make_figK.py, make_fig4B.py, make_figs.py Fig D and make_fig_main.py panel f; i_lim_tier0 (correlations.jl:54) and the NPP/EC' solvers take D, C, Î´, z only. I reproduced the perturbation results: at the 250 Î¼m microfluidic, DMF margin 1.031 â 0.770 at 0.5Îº and MeCN 0.852 â 1.034 at 2Îº, exactly as reported; beaker/stirred/flow margins for MeCN and DMF stay above 1 across 0.5-2Ã (MeCN break factor 0.288)."
          },
          {
            "finding": "citation-integrity Â§2 â 11 of the 27 CRC-cited rows cite the 'viscosity/density tables' locator for conductivity, heat-capacity and boiling-point quantities",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Filtered the registry on the exact CRC constant string (build_param_tables.py:36): 27 rows, 16 are Î¼/Ï, and the other 11 are precisely lines 193,195,196,198,199 (conductivities) and 216-221 (cp/Tb) â the auditor's table line-for-line. The locator cannot support those quantities; the registry demonstrates the correct pattern elsewhere (8 rows name the VanyÅ¡ek ion table). This is the locator behind the 'measured-lit, CRC' label on the 180 mS cmâ»Â¹ aqueous anchor of make_si.js:369. L193's note also degrades to 'CRC/electrolyte handbooks'. Values themselves not checkable here."
          },
          {
            "finding": "citation-integrity Â§3 â provenance_class for Wilke-Chang Ï is a ternary on the value, inverting the classification relative to the source",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "build_param_tables.py:63 literally reads `"lit-representative" if phi!=1.0 else "measured-lit"`. Consequence verified in the registry: the 11 Ï=1.0 rows (incl. AcOH, HFIP and two mixtures) are measured-lit while H2O 2.6, MeOH 1.9, EtOH 1.5 â the three values Wilke & Chang 1955 actually tabulates â are lit-representative. Lines 89 and 99 (DMSO/THF, AcOH/HCOOH) are measured-lit despite their own note reading 'fitted so phi*M = P-G rule'."
          },
          {
            "finding": "citation-integrity Â§4 â 20 measured-lit M rows cite the literal string 'standard'; for the 8 mixtures the value is a fitted quantity and the note ('volume-weighted') is wrong",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "build_param_tables.py:60 emits all 20 solvent M rows as measured-lit/'standard'/'molar mass (mixtures: volume-weighted)'. I reproduced the auditor's arithmetic for MeOH/H2O 1:1: mole-fraction 22.3, volume-fraction 25.0, tabled 26.4 â neither. Cross-check confirms M is fitted with Ï, not a molar mass: ÏM = 1.94Ã26.4 = 51.2 exactly matches the P-G mole-fraction rule Î£x_iÏ_iM_i = 51.15. So the pair's real source is Poling Eq. 11-9.8, class derived, not 'standard'/measured-lit."
          },
          {
            "finding": "citation-integrity Â§5 â L153 is one measured-lit row standing in for 50 values, 10 of which its own note excludes, with a self-referential citation; and it contradicts the SI prose count",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Printed the full row: class measured-lit, citation 'Table S2 per-row citations + anchors', note '...for 40/50 rows ...; 8 rows main-text-unverifiable ...; 1 anchored to a physically absent book chapter (BASF); 1 by stated analogy'. make_si.js:251 says 'Forty-nine of the fifty rows are so verified â forty-one against main-article PDFs and eight more against their Supporting Materials'. The registry note and the prose genuinely disagree. L154's citation is bare 'Table S2'; L151/L152 cite reactions_50.csv and build_reactions50.py conventions."
          },
          {
            "finding": "citation-integrity Â§6 â U' PEM-class cooled plates is classed measured-lit but is a mid-range pick from a 0.1-0.6 bracket",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Registry line 228: value 0.30 W cm-2 K-1, class measured-lit, note '2-6 W cm-2 rejected across 10-20 K gradients', citation Wallnoefer-Ogris 2024. 2/20 = 0.1 and 6/10 = 0.6, so 0.30 is a selection within the implied bracket â a derived/representative quantity, not a measured one. The citation itself is specific."
          },
          {
            "finding": "citation-integrity Â§7 â ten registry citations never enter the numbered REFS list; six rows cite bare 'CRC' with no edition",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Grepped make_si.js for all ten names: only 'izutsu' is present (REFS line 28), so nine of the ten (Wallnoefer-Ogris, Sander, Incropera, Cussler, Pickett, Colomer, Amatore, VanyÅ¡ek, CODATA) appear only as registry table text. The Izutsu item in the auditor's list is therefore wrong. The bare-'CRC' sub-claim is exact: 6 rows (MeOH/EtOH/H2O Î¼ and Ï, lines 12,13,17,18,42,43)."
          },
          {
            "finding": "citation-integrity Â§8 â REFS.kelly2026 is stale (volume null; now 2026, 30, 1926-1936)",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "make_si.js:34 has volume null with only the DOI. Crossref for 10.1021/acs.oprd.6c00110 returns Org. Process Res. Dev. 2026, vol 30, issue 7, pp. 1926-1936, 'Development of Kilogram-Scale Electrochemical Ni-Catalyzed Cross Electrophile Coupling in Flow'. Confirmed against the live record."
          },
          {
            "finding": "lit-rep-risk C1 â Î´_stirred = 100 Î¼m (lit-representative, page-less textbook citation) is the actual fragile parameter: a 2Ã revision inverts the industry-agreement claim",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "Registry line 207 is exactly as quoted, with no page and no sensitivity note. Recomputed from julia/tier0_ec_matrix.csv: median stirred 17.397 (17/50 â¥25, 14/50 â¥50); at Î´=50 Î¼m 34.79 (29/50, 17/50); at 200 Î¼m 8.70 (14/50, 11/50) â the auditor's table exactly. make_si.js:382 does hang the validation claim on '17 mA cmâ»Â², inside the sub-25 band where 10 of 14 companies sit', and at 50 Î¼m the median moves into the 25-50 band occupied by 3 of 14. i_lim â 1/Î´ exactly for the fixed-Î´ archetypes."
          },
          {
            "finding": "lit-rep-risk C3 â the flagship Â§S6 worked example uses the retracted Îº = 3.5 and a superseded U'; its 'settles just below boiling' conclusion is false under the adopted parameters",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "Reproduced all of it: Îº=0.35 S/m, 5 mm, 100 mA cmâ»Â² â E_cell 16.76 V, ohmic 14.29 V, q 1.476 W cmâ»Â², self-heating 14.76 W / 193.5 J Kâ»Â¹ = 4.58 K minâ»Â¹. T_ss = 98.8 Â°C only with U' = 0.02; with Â§S6.1's derived 0.017256 it is 110.5 Â°C. With the adopted 0.2 M NaI/DMF at the canonical 2 cm gap, T_ss = 172.6 Â°C > 153 Â°C â DMF boils, consistent with Fig K's own 93 mA cmâ»Â² ceiling. The electrolyte is absent from registry category 6, as make_si.js:369 itself states."
          },
          {
            "finding": "lit-rep-risk M4 / figure-data-trace C2 â the vessel-scaling series 49/62/106/134 was computed with the retracted Îº and contradicts Fig K's own panel (a)",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Re-implemented the Ï â V^(2/3) scaling anchored at Ï=15: with Îº=3.5 mS cmâ»Â¹ I get 49.0 / 61.8 / 105.9 / 133.5 (exact match to the SI sentence); with the adopted 8.0 mS cmâ»Â¹ it becomes 73.7 / 93.1 / 159.7 / 201.4. The 100 mL entry 93.1 is precisely results/figK_thermal.json's panelA DMF value, so the SI's '62' is 1.5Ã low against the figure it introduces. The 2.15Ã ratio is pure V^(1/3) and survives. make_figK.py:41 carries the same series in a docstring; the script contains no volume sweep and the JSON has no such field."
          },
          {
            "finding": "lit-rep-risk M5 â 3.0 M LiBr/THF is classed measured-lit but its method_note characterises Îº as 'order-of-mS/cm'",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "ECOND_PROV (build_param_tables.py:127) reads: composition page-verified from Peters 2019 SM p S15, then 'heavily ion-paired ether medium, kappa order-of-mS/cm'. What is page-anchored is the composition, not a measured conductivity; make_si.js:369 nevertheless asserts 'Îº = 3.0 mS cmâ»Â¹, measured-lit'. Break factor verified: THF clears 50 mA cmâ»Â² only up to Îº Ã 2.42 (45.5 mA cmâ»Â² at 2Ã), so the conclusion survives a 2Ã but not the decade its own note implies. Could not consult the Peters SM (not in the tree)."
          },
          {
            "finding": "lit-rep-risk M7 â 'Passive air and stirred-liquid heat rejection saturate near 0.01 and 0.1 W cmâ»Â²' has wrong units, matches neither the registry nor Â§S6.1, and contradicts the section that follows",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "make_si.js:362 quoted verbatim; the quantity is U', so units must be W cmâ»Â² Kâ»Â¹. Registry values are 0.020 (UA still air 0.20 W Kâ»Â¹ / 10 cmÂ²) and 0.18; the geometry derivation gives 0.017256 and 0.019188 (both in figK_thermal.json). 0.01/0.1 matches neither pair, and Â§S6.1 states 'stirring a beaker is nearly useless thermally'. Registry line 227's own note scopes 0.18 to 'bath-jacketed glass'."
          },
          {
            "finding": "lit-rep-risk M9 â the '1.8Ã margins' are quoted to two significant figures off lit-representative Îº with Â±40% spread",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "JSON panelA margins are 1.840 (MeCN) and 1.861 (DMF). Recomputed under Â±2Ã: MeCN 65.6-128.6, DMF 66.0-130.9 mA cmâ»Â², i.e. margins 1.31-2.62Ã. The qualitative claim is robust (MeCN break factor 0.288); the two-figure precision is not."
          },
          {
            "finding": "lit-rep-risk M10 â 'THF remains the most demanding by roughly a factor of five' is neither the baseline value nor 2Ã-robust",
            "verdict": "UNCERTAIN",
            "severity": "minor",
            "reason": "The arithmetic is right but the comparator is selective. THF/DMF from panelC is 7.96 / 6.82 / 6.44 as claimed, but the SI sentence brackets 'MeCN and DMF' together, and THF/MeCN is 7.33 / 5.01 / 4.44 â 'roughly five' is a fair description of the group at two of three architectures. The compounding-of-two-lit-rep-errors point stands; the claim that five is not the baseline does not clearly hold."
          },
          {
            "finding": "lit-rep-risk minor â Ï â 16 min vs â19 min for the same beaker; 16 is the pre-fix U' = 0.02 number",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "DMF 100 mL: C = 94.4 g Ã 2.05 = 193.5 J Kâ»Â¹. With the derived UA = 0.17256 W Kâ»Â¹, Ï = 1121 s = 18.7 min; with the retired UA = 0.20 W Kâ»Â¹, Ï = 967.5 s = 16.1 min. Both figures appear in make_si.js:373. This attribution is correct (and supersedes registry-coverage m4's THF/DMF reading)."
          },
          {
            "finding": "lit-rep-risk minor / figure-data-trace M4 â 'some 400Ã faster' is the raw volume ratio; the Ï ratio is ~210Ã, and 'Ï â 4 s' recomputes to 5.3 s",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "250 Î¼m cell, 0.25 mL DMF: C = 0.4836 J Kâ»Â¹, UA = 0.009076 Ã 10 = 0.09076 W Kâ»Â¹ â Ï = 5.33 s. 1121/5.33 = 210. 400 = 100 mL / 0.25 mL, i.e. the UA ratio (0.009076/0.017256) was not divided out. make_figK.py computes no Ï and figK_thermal.json has no Ï field, so neither number is traceable to an artifact."
          },
          {
            "finding": "lit-rep-risk minor â 'the required duty ... spanning two orders of magnitude' set by solvent conductivity",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "panelC extremes give 0.098616/0.0010014 = 98.5Ã, but that crosses architectures. At fixed architecture the solvent-driven span is 41.7Ã (5 mm flow), 12.4Ã (250 Î¼m) and 9.7Ã (PEM) â 1.0-1.6 decades, not two, for the attribution as worded."
          },
          {
            "finding": "lit-rep-risk minor â 'heat fluxes of 1-10 W cmâ»Â² are routinely rejected' widens the cited 2-6 W cmâ»Â² on both ends",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "make_si.js:362 says 1-10; registry line 228's note (the Wallnoefer-Ogris anchor) says '2-6 W cm-2 rejected across 10-20 K gradients'. Both read directly."
          },
          {
            "finding": "lit-rep-risk minor â six mixture Wilke-Chang Ï classed lit-representative and cited to Wilke & Chang 1955, though their own note says they were fitted in this work",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Lines 59, 64, 69, 74, 94, 104 hold Ï = 1.17, 1.94, 1.58, 1.15, 1.73, 2.10, all lit-representative, all cited to Wilke & Chang AIChE J. 1955, all with method_note 'mixtures: fitted so phi*M = P-G rule'. Line numbers verified exactly. I confirmed the P-G arithmetic independently on MeOH/H2O (ÏM = 51.2 = Î£x_iÏ_iM_i)."
          },
          {
            "finding": "lit-rep-risk minor â 45 of 86 lit-representative rows carry no sensitivity statement; the 41 that do are exactly the conductivities",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Counted: 86 lit-rep rows, 42 carry a sensitivity/robustness phrase â the 41 conductivities plus the homogeneous-kinetics row (whose note says 'robustness statements in S5.5'). So 44 lack one, not 45 (Solvents 27, Diffusivities 12, Reactors 3, Thermal 2), and Î´_stirred is indeed among them. Off by one; the structural point holds exactly."
          },
          {
            "finding": "figure-data-trace C3 â make_fig_mediator_k.py plots a closed-form toy whose 'reactor Ã1' plateau conclusion is contradicted by julia/mediated_ec_matrix.csv",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "The script reads no file; I = min(300,x_k)/min(10,x_k) at line 18. Computed thingap/unstirred and rce/unstirred from the solver matrix: SCNâ» 9.9/18.5, Brâ» bromination 8.7/20.3, BQ Wacker 4.7/7.5, Brâ» Hofmann 1042/3004 (unstirred flagged newton-wall), NHPI 4.5/14.1, Clâ» 8.8/20.8, ACT 1.4/1.8, HMF 1.7/2.4 â the auditor's table reproduced exactly. The grouped annotation at line 54 claiming 'reactor Ã1' is false for four of the six cluster points. The (k, x_k) transcriptions themselves are correct. The figure is not referenced in make_si.js (grep 'mediator_k' returns nothing there)."
          },
          {
            "finding": "figure-data-trace M1 â sec4_figH_ecprime.png has no generator in the tree and its open squares exist in no data file",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Repo-wide grep for 'figH' returns nothing; the complete savefig inventory over figs/ lists A,B,C,D,E,F,G,I,J,K,L,M but no H. make_si.js:331 does cite 'Fig. H, open squares' for the total-catalysis substitution. julia/npp_ecprime_sweep.csv gives 46.375 / 29.260 / 19.284 at k = 3e3/1e4/1e5 (decreasing) and results/npp_ecprime_sweep.csv gives 27.591 / 0.338 / 1.816 â neither is the flat ~48 cap drawn in the PNG. The filled circles are traceable (k=1e3 â 41.863)."
          },
          {
            "finding": "figure-data-trace M2 â Fig E's generator reads julia/npp_support_sweep.csv and julia/npp_profiles.csv, which do not exist at that path",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "make_figs.py:128 reads both from julia/; ls julia/ shows only npp_ecprime_sweep.csv and npp_ecprime_profiles.csv. Both files exist only in results/ (mtime Jul 10 12:15, older than the Jul 12 render). The data itself is real: results/npp_support_sweep.csv gives 2.000, 1.380, 1.180, 1.040 at SR 0, 0.25, 1, 5, matching make_si.js:320. run_section4.jl writes them to its own cwd, so the figure chain is broken as the tree stands."
          }
        ]
      },
      {
        "verdicts": [
          {
            "finding": "registry-coverage C1 / lit-rep-risk C2 â SI's "every architecture at 500 mA cmâ»Â² and above falls short passively, in every solvent" is falsified by results/figK_thermal.json",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "Verified directly in results/figK_thermal.json: at the 250 Âµm microfluidic (i_design = 500) panelB gives DMF 515.62 (1.03Ã) and aq. NaOH 841.41 (1.68Ã); panelC gives U'_req 0.008598 (DMF) and 0.004721 (NaOH) against passively_available 0.009076 â both clear. Two of four solvents clear the architecture the text says none clear, and make_si.js:372 repeats the error ("Because passive rejection fails for the intensified architectures"). This is a stated conclusion contradicted by the figure it introduces, independent of any provenance question. Registry-coverage's sub-claim that :372 "does not repeat the error" is itself wrong; lit-rep-risk C2 has it right, and additionally correct that DMF breaks at ÎºÃ0.93 (I get i_boil = 500.6 at 0.93Îº) â i.e. the sentence is wrong at the stated Îº and sign-fragile at 7%, not 2Ã."
          },
          {
            "finding": "registry-coverage C2 / citation-integrity Â§1 / lit-rep-risk M6 / fig-trace C1 â the Fig K electrolyte fix reached only Fig K; the three unregistered electrolytes remain live in Table S4, cellvoltage.jl, make_fig4B.py, make_figs.py, make_fig_main.py",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "Exact-name diff against category 6 of data/parameters_provenance.csv confirms 0.1 M Bu4NPF6/THF, 0.1 M Bu4NBF4/DMF, 1 M KOH aq and Me4N carboxylate (10 mol%)/acetone have zero registry rows. They are still hard-coded at julia/cellvoltage.jl:14-19 (0.06/0.35/20.0 S mâ»Â¹), still printed as 4 of 8 rows of Table S4 (make_si.js:243-246) under a caption asserting "the full 49-electrolyte registry with per-entry provenance is Table S7f", and still in figs/make_fig4B.py:134-138, figs/make_figs.py:103-107 and figs/make_fig_main.py:158-160. figs/sec4_Fig4B_def.png (Jul 13, not in _superseded/) and sec4_MAIN_composite.png (Jul 12) are current renders, and Section4_composite_versions.md ranks V5 (which uses 4B) first for main text. data/make_fig4B.py is byte-identical to figs/make_fig4B.py (diff clean). Materially serious because make_si.js:369 calls this exact parameterisation "self-invalidating" while the same document publishes it in Table S4."
          },
          {
            "finding": "citation-integrity Â§1 / lit-rep-risk C3 â the Â§S6 worked example (16.8 V, 14.3 V ohmic, 1.4 W cmâ»Â², 4.5 K minâ»Â¹, T_ss â 99 Â°C) is built on the retracted Îº = 3.5 mS cmâ»Â¹ at the retracted 5 mm gap",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "I reproduced it: at 100 mA cmâ»Â², 5 mm, Îº = 0.35 S mâ»Â¹ â ohmic 14.29 V, E_cell 16.76 V, q = 1.476 W cmâ»Â², and T_ss = 98.8 Â°C only with the superseded U' = 0.020. With Â§S6.1's own geometry-derived U' = 0.017256 the same case gives 110.5 Â°C; with the adopted 0.2 M NaI/DMF (8.0 mS cmâ»Â¹) at the canonical 2 cm beaker gap it gives 172.6 Â°C, i.e. DMF boils â consistent with Fig K panel (a)'s DMF ceiling of 93 mA cmâ»Â² < 100, and directly contradicting the paragraph's "settles just below the boiling point at 100 mA cmâ»Â²". Four quoted numbers in the flagship worked example rest on a Îº the same section declares absent from the registry, and the example's conclusion is contradicted by the figure it introduces."
          },
          {
            "finding": "lit-rep-risk M4 / fig-trace C2 â the vessel-scaling series "49, 62, 106 and 134 mA cmâ»Â²" was computed with the retracted Îº and contradicts Fig K's own panel (a) by 1.5Ã",
            "verdict": "CONFIRMED",
            "severity": "critical",
            "reason": "I reproduce 49.0 / 61.8 / 105.9 / 133.5 exactly with Îº = 0.35 S mâ»Â¹ (the unregistered 0.1 M Bu4NBF4/DMF), Ï â V^(2/3) anchored at 15. With the adopted 0.2 M NaI/DMF (0.80 S mâ»Â¹) the series is 73.7 / 93.1 / 159.7 / 201.4, and the 100 mL entry then equals panelB's DMF beaker value 93.07 to the digit. So the quoted 62 is 1.50Ã low against the very figure the sentence describes. The V^(1/3) correction (an item the ground truth lists as fixed) was applied on top of the pre-fix conductivity, so the fix is incomplete. The 2.15Ã ratio survives (pure 10^(1/3)); every absolute number does not. There is also no volume sweep anywhere in make_figK.py â the series exists only in prose and a docstring comment (line 41)."
          },
          {
            "finding": "lit-rep-risk C1 â the real load-bearing lit-representative failure is Î´_stirred = 100 Âµm (bare Pletcher & Walsh attribution, no page, no sensitivity note), which sets the industry-validation claim and flips it under a 2Ã revision",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "parameters_provenance.csv:207 is a bare textbook attribution with no locator, and it is one of the 45/86 lit-representative rows carrying no sensitivity statement (I counted: 45, split 27 Solvents / 12 Diffusivities / 3 Reactors / 2 Thermal / 1 Kinetics â matches exactly). Recomputing from julia/tier0_ec_matrix.csv: median stirred i_lim = 17.40 (matches Table S5), rising to 34.79 at Î´ = 50 Âµm (29/50 â¥ 25) and falling to 8.70 at 200 Âµm. At 50 Âµm the median leaves the sub-25 band that make_si.js:382 uses to claim agreement with the Ferretti survey ("inside the sub-25 band where 10 of 14 companies sit"), landing in the 25-50 band where 3 of 14 sit. This is a genuine qualitative flip driven by a weakly-sourced lit-representative value, and it is a materially larger exposure than the Îº concern the audit brief flagged. Caveat: 100 Âµm is a conventional value for magnetic stirring and 50 Âµm is an aggressive revision, so the physical risk is smaller than the provenance risk â but the row does not carry the sensitivity statement the S9 class definition promises."
          },
          {
            "finding": "registry-coverage M2 / fig-trace M3 / lit-rep-risk M11 â Fig K's Ï, h_int, i_design and cooling bands are unregistered, and Ï = 15 conflicts with the registry's own derived vessel geometry (12.5)",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Grep of parameters_provenance.csv finds no rows for h_int (100/800/2000/5000), for Ï (15/15/10/7/0.8), for the design currents 100/500/1000 mA cmâ»Â² (only "Thresholds 25 / 50" exists), or for the three cooling bands of make_figK.py:154-156. H_EXT = 13 is the only derivable one (7 + 6-8, registered). The registry's own derived row 'Vessel external area = 0.0125 m2' over the registered 100 mL / 10 cmÂ² gives Ï = 12.5, not 15. I recomputed at Ï = 12.5: U' drops 0.01726 â 0.01438 and panel (a) becomes THF 29.5, MeCN 83.9, DMF 84.9 (from 32.3/92.0/93.1), which also drops the quoted "1.8Ã each" margins to ~1.7Ã. Even at Ï = 15 the result is 0.0173 vs the registered 0.020 'still air' value it claims to 'reproduce from geometry' â 14% below. So the docstring's headline claim ("PASSIVE COOLING IS DERIVED FROM GEOMETRY, NOT ASSUMED") is reverse-fitted against an unregistered Ï that contradicts the registry's own geometry row. This is the largest genuine provenance exposure in the revised figure, and it is inside a fix the ground truth lists as already applied â the fix is self-inconsistent."
          },
          {
            "finding": "registry-coverage M1 â 18 of 67 rows of data/electrolytes.csv have no registry row; 11 have no provenance anywhere; the used-set filter in build_param_tables.py silently drops 7 that do have written provenance",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Programmatic diff confirms exactly 18 unregistered names and the exact split claimed: 7 present in ECOND_PROV but dropped by `_used = pd.read_csv("reactions_50.csv")[["electrolyte"]].drop_duplicates()` at build_param_tables.py:150 (1 M KOH aq, phosphate buffer aq, 0.1 M Bu4NPF6/THF, 0.5 M NaOMe/MeOH, Me4N carboxylate/acetone, no added salt/MeCN, pH 2 HCl/H2O-MeCN), and 11 with no provenance anywhere (0.1 M Bu4NBF4/DMF, 0.1 M Bu4NBF4/HFIP, 0.2 M Et4NOTs/MeOH, 0.5 M H2SO4 aq, 1 M LiBF4/THF, 1 M NaBr aq, Et3N.3HF/MeCN, LiBr/THF, Me4NBF4/MeOH, emulsion + Na2HPO4/TAEP, neat carboxylate/MeOH). Material because three of the 18 are exactly the electrolytes still driving Table S4 and cellvoltage.jl, and because 1 M KOH aq has a written measured-lit CRC justification that never reached the machine-readable registry."
          },
          {
            "finding": "registry-coverage M3 â reactor Î´ values hardcoded in run_profiles.jl and the figures contradict the model's own correlation-derived Î´_eff by up to 3.3Ã",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "Computed medians over the 8 ECâ² specs in julia/mediated_ec_matrix.csv: unstirred 300, stirred 100, flow (1 mm) 84.38 (57.2-94.8), thin-gap (250 Âµm) 33.49 (22.7-37.6), RDE 13.69, RCE 11.47 Âµm â matching the finding to 2 d.p. julia/run_profiles.jl:65-66 uses ("flow", 30e-6) and ("thingap", 10e-6), i.e. 2.8Ã and 3.3Ã thinner than the model's own flow and thin-gap archetypes. figs/make_figs.py:38 bands (20-60 flow, 6-15 RDE/RCE/thin gap) are non-overlapping with 57-95 and exclude 22.7-37.6. figs/make_fig_mediator_k.py:16 uses DT = 10.0 labelled "thin gap". So the profile figure's "Î´ = 30 Âµm flow cell: c_surf = 0.69" annotation labels a Î´ that is not the project's flow archetype. Downgraded from critical on materiality: Figs J and I are not cited anywhere in make_si.js (only Figs C, E, F, H, K are), so this contradicts an illustrative figure, not a quoted SI conclusion â but it is a genuine internal inconsistency between the figures and the production matrix."
          },
          {
            "finding": "registry-coverage M4 â load-bearing illustrative constants absent from the registry (C_S/D_S/C_sup triple behind i_lim = 48; Î¼/Îµ in make_fig_nd; generic D in make_fig_carrier; k_L a = 0.05 sâ»Â¹ in make_figL)",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Verified: run_profiles.jl:2-4 sets C_S = 500, D_S = 1e-9, C_sup = 100 with no registry rows (category 5 registers only the 50-row concentration block, propylene C_sat and trace initializations; category 4 has no generic substrate D). make_fig_nd.py:27-28 Î¼ = 0.041 / Îµ = 0.060 and :56 the Î³ = 41.7 block are unregistered, duplicated at make_fig_main.py:140. make_fig_carrier.py:71,73,88 use D = 6e-6 / 1e-5 cmÂ² sâ»Â¹ and Ccat = 0.010 M with no generic figure-level rows. A grep for kLa|k_L|gas|sparg over parameters_provenance.csv returns nothing relevant, confirming k_L a = 0.05 sâ»Â¹ (figs/make_figL.py:36) has no provenance and no covering category. Severity reduced to minor on materiality: none of these numbers is quoted in the SI (I grepped â no '48 mA', no '0.05 sâ»Â¹'), so they carry figure annotations rather than stated conclusions. Real under the "every number has provenance" standard, but not conclusion-threatening."
          },
          {
            "finding": "registry-coverage M5 â solver species diffusivity gaps (H+ at 2.0e-9, neutral B(OH)3 reusing the borate row, NH4+ scope mismatch, generic Aâ» values not covered by the 1.9e-9 row)",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "All four verified in source: run_scn.jl:42 and run_mediated.jl:103 use S("H+", +1.0, 2.0e-9, ...) while category 4 registers H+ only at 9.3e-9 (aq), 3.0e-9 (MeCN/organic) and 5.0e-9 (1:1 aq/MeCN) â no 2.0e-9 row. run_mediated.jl:76 uses S("B(OH)3", 0.0, 0.96e-9) against a registry row scoped B(OH)4- (aq). NH4+ at 2.0e-9 in AcOH/HCOOH against a row scoped "(MeCN, used aq-like)". run_section4.jl:41 uses Aâ» = 2.0e-9 and :49 Xâ» = 1.5e-9 and :48 RCO2â» = 8.0e-10, none matching the single 'Generic supporting K+/A- = 1.9e-9' row. Minor on materiality: these are supporting-ion mobilities that enter migration factors weakly; no stated conclusion moves."
          },
          {
            "finding": "citation-integrity Â§2 â 11 of 101 measured-lit rows cite the CRC "viscosity/density tables" constant for conductivity, heat capacity and boiling point",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Exactly 27 rows carry the CRC constant defined at build_param_tables.py:36; 16 are Î¼/Ï rows where the locator is correct, and the other 11 are the five aqueous conductivities (KHCO3 80, Na2CO3 70, NaOH 180, H2SO4 700, NaCl 160) plus six thermal rows (THF cp/Tb, DMF cp/Tb, MeCN Tb, aq. KOH Tb) â quantities that live in different CRC tables. The registry demonstrably knows how to do this right (8 rows name the VanyÅ¡ek ion table). Real, and it lands on the one aqueous anchor the SI upgraded during the Fig K fix. Minor on materiality: the values are standard and the aqueous case carries a 6.3Ã margin, so no conclusion is at risk â this is a locator defect, not lost provenance."
          },
          {
            "finding": "citation-integrity Â§3 / lit-rep-risk minor â provenance_class for Ï is assigned by the value, not the source, inverting the classification relative to Wilke & Chang 1955",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "build_param_tables.py:63 literally reads `"lit-representative" if phi!=1.0 else "measured-lit"`. I enumerated the result: exactly 11 Ï = 1.0 rows are classed measured-lit (MeCN, DMF, DMA, DMSO, THF, AcOH, HFIP, acetone, MeNO2, DMSO/THF, AcOH/HCOOH) while H2O 2.6, MeOH 1.9 and EtOH 1.5 â the three values Wilke & Chang actually tabulate â are demoted to lit-representative. Two of the eleven (DMSO/THF, AcOH/HCOOH) carry the method_note "mixtures: fitted so phi*M = P-G rule", i.e. fitted parameters classed as measured literature. Graded major because it is a systematic code-level defect that inflates the registry's headline measured-lit count (101), which is itself a stated provenance claim â even though no numeric conclusion changes, since the D values reconcile."
          },
          {
            "finding": "citation-integrity Â§4 â 20 measured-lit rows cite the literal string "standard"; the 8 mixture molar masses are fitted quantities whose note ("volume-weighted") is wrong",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Confirmed: 20 rows have citation == 'standard', all emitted unconditionally at build_param_tables.py:60. I reproduced the mixture arithmetic for two spot checks: DMF/H2O 9:1 stated 56.0 vs mole-fraction 55.3 and volume-fraction 67.6; MeOH/H2O 1:1 stated 26.4 vs 22.3 and 25.0 â so the stated set is not generated by the note's rule and matches no single convention. The mixture (M, Ï) pairs are set jointly "so phi*M = P-G rule" per the block's own comment, making these derived/Poling-sourced, not measured. Minor on materiality: only the product ÏM enters Wilke-Chang, and the resulting D values reconcile with the solver (already verified in the clean section), so this is a mislabelling not a wrong number."
          },
          {
            "finding": "citation-integrity Â§5 â L153 is one measured-lit row standing for 50 concentrations, 10 of which its own note excludes, and its count disagrees with the SI prose",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "parameters_provenance.csv:153 verified verbatim: class measured-lit, citation 'Table S2 per-row citations + anchors' (self-referential), method_note declaring 40/50 page-verified, 8 main-text-unverifiable, 1 BASF, 1 by analogy. make_si.js:251 states 'Forty-nine of the fifty rows are so verified â forty-one against the main-article PDFs and patents, and eight more against their Supporting Materials in a second pass'. The registry note is stale relative to the prose about the same eight rows. L154 has the same defect (citation 'Table S2'), and L151/L152 cite reactions_50.csv and build_reactions50.py conventions. Major because concentrations set i_lim linearly and are the single most load-bearing input class; the per-row provenance does exist in Table S2, so this is a registry-completeness and internal-consistency failure rather than lost provenance."
          },
          {
            "finding": "citation-integrity Â§6 â U' PEM-class cooled plates = 0.30 classed measured-lit is a mid-range pick from a 2-6 W cmâ»Â² / 10-20 K bracket",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "parameters_provenance.csv:228 confirmed: value 0.30, class measured-lit, note '2-6 W cm-2 rejected across 10-20 K gradients', citation Wallnoefer-Ogris 2024. The implied bracket is 0.1-0.6, so 0.30 is derived, not measured. However the finding's materiality claim is wrong: Fig K(c) does not consume 0.30 â make_figK.py:154-156 uses shaded bands (2e-1 to 1.0 for 'liquid cold plate (PEM-class)') and the registered 0.30 merely falls inside one. The value is still consumed by make_fig4B.py:139 and make_fig_main.py, so it is not orphaned, but it is not an input to the revised panel (c)."
          },
          {
            "finding": "citation-integrity Â§7 â ten named registry sources never enter the numbered REFS list",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Case-insensitive grep of make_si.js returns zero hits for wallnoefer, Sander, Incropera, Cussler, Pickett, Colomer, Amatore, Vanysek and CODATA â all of which appear as free-text citations in parameters_provenance.csv and are rendered into the S7 tables. Izutsu is the one exception (2 hits). The finding's own framing is right: each string is specific enough to check by hand, so this is documentation consistency, not lost provenance. auditRefOrder() has no visibility into the registry CSV, which explains the gap."
          },
          {
            "finding": "citation-integrity Â§8 â REFS.kelly2026 is stale (volume null; paginated 2026, 30, 1926-1936)",
            "verdict": "UNCERTAIN",
            "severity": "minor",
            "reason": "The verifiable half is confirmed: make_si.js:34 gives kelly2026 with volume `null` and only a DOI, so the entry is incomplete. The specific pagination (30, 1926-1936) is an external Crossref claim I cannot check in this offline tree, so I cannot confirm the reference is stale rather than genuinely unpaginated at time of writing. No material consequence either way."
          },
          {
            "finding": "lit-rep-risk M5 â 3.0 M LiBr/THF at 3.0 mS cmâ»Â¹ is classed measured-lit but its own method_note describes only the composition as page-verified and characterises Îº as "order-of-mS/cm"",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "ECOND_PROV in build_param_tables.py:131 confirmed verbatim: 'Peters 2019 SM scale-up electrolyte: LiBr 1.0 mol / 320 mL THF = 3.0 M stock (SM p S15); heavily ion-paired ether medium, kappa order-of-mS/cm'. What is page-anchored is the composition; the conductivity is a one-decade characterisation, yet make_si.js:369 asserts 'Îº = 3.0 mS cmâ»Â¹, measured-lit'. This is material because THF is the load-bearing case in the whole of Â§S6/Â§S6.2 â it drives 'THF boils at 32 mA cmâ»Â², below the 50 mA cmâ»Â² design current', 'THF clears none of them', and the entire cooling-duty narrative. I confirmed the break factor: i_boil reaches 50.0 mA cmâ»Â² at exactly ÎºÃ2.42, so the claim survives a 2Ã revision with ~10% margin but not the one-decade uncertainty the note itself implies. This is the sharpest single provenance-to-conclusion coupling in the document and it sits on the one value the SI singles out as measured."
          },
          {
            "finding": "lit-rep-risk M7 â "Passive air and stirred-liquid heat rejection saturate near 0.01 and 0.1 W cmâ»Â²" has wrong units and contradicts Â§S6.1, which the same document wrote to refute it",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "make_si.js:362 verified verbatim, units W cmâ»Â² where the quantity is W cmâ»Â² Kâ»Â¹. Â§S6.1 (make_si.js:361) derives U' = 0.017 passive and 0.019 stirred and states explicitly that 'stirring a beaker is nearly useless thermally', so the quoted 0.1 for stirred liquid is ~5Ã the derived value and traces to parameters_provenance.csv:227 (U' stirred bath = 0.18, note 'bath-jacketed glass') â an externally-cooled jacketed vessel silently reused as an unjacketed stirred beaker. Neither quoted figure matches the registry (0.02, 0.18) or the derivation (0.017, 0.019). A live internal contradiction between adjacent sections of the shipped SI."
          },
          {
            "finding": "lit-rep-risk M8 / registry-coverage m1 â the corrected inventory claim was not propagated to the registry; parameters_provenance.csv:222 still asserts "steady state independent of volume (S6.1)"",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Line 222 verified verbatim: '9. Thermal model, Cell volume / electrode area, 100 mL / 10 cm2, assumption, representative batch cell; steady state independent of volume (S6.1)'. make_si.js:373 item (ii) explicitly repudiates this ('it does not follow that boil-off is independent of cell volume, because inventory and rejecting surface are physically coupled'), and the stale note renders into Table S7i of the shipped v3 docx. Directly incomplete relative to a fix the ground truth lists as applied. Minor because the value (100 mL / 10 cmÂ²) is unaffected and only the method_note is stale â but it is the machine-readable artifact."
          },
          {
            "finding": "lit-rep-risk M12 / registry-coverage m3 â stale 5 mm-beaker caveat survives the 2 cm correction in both make_si.js:373 and make_figK.py:188",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "make_si.js:373 item (i) verified: 'real beaker setups space electrodes 1-2 cm apart rather than 5 mm, which raises the ohmic heat 2-4Ã ... The boil-off currents quoted for 5 mm gaps are therefore upper bounds for typical beaker practice' â contradicting item (ii) in the same paragraph, which specifies the beaker at 2 cm. make_figK.py:188 prints '(a) UNSTIRRED BEAKER, 5 mm' while Lb = REACTORS[0][1] = 2.0e-2. The caveat now double-counts a correction already applied. Residual pre-revision text; no number changes."
          },
          {
            "finding": "lit-rep-risk M9 â "margins of 1.8Ã each" for MeCN and DMF has no more precision than Â±40% given both Îº are lit-representative",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "The stated 1.8Ã is exactly what the figure produces (panelA margins 1.8404 and 1.8614), so the number is not wrong. The finding's own analysis concedes the qualitative claim is robust (breaks only at ÎºÃ0.29). Confirmed as a precision observation, but this is a documentation nitpick, not a materially threatened conclusion. Worth noting it compounds with the Ï = 15 issue: at the registry's own Ï = 12.5 the margins fall to ~1.68-1.70."
          },
          {
            "finding": "lit-rep-risk M10 â "THF remains the most demanding by roughly a factor of five" is neither the baseline value nor 2Ã-robust",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "From panelC of results/figK_thermal.json the THF/DMF required-U' ratios are 0.041805/0.005253 = 7.96, 0.058602/0.008598 = 6.82 and 0.098616/0.015312 = 6.44 across the three architectures â 6.4 to 8.0, not five. The finding's structural point is also correct: a ratio of two independently-uncertain values compounds rather than cancels error, and the 'iÂ²L/Îº robust to 2Ã' boilerplate does not cover it. Minor on materiality: 'roughly a factor of five' understates rather than reverses, and THF remains the most demanding solvent by a wide margin either way."
          },
          {
            "finding": "registry-coverage m4 / lit-rep-risk minor â make_si.js:373 gives two different Ï (16 min and 19 min) for the same 100 mL beaker",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Both values are present in the same paragraph, confirmed. But registry-coverage's reconstruction (16 = THF, 19 = DMF) is wrong: I compute THF at U' = 0.017256 as 151.9/0.17256 = 14.7 min, not 16. The correct diagnosis is lit-rep-risk's â 19 min = DMF with the geometry-derived UA (193.5/0.17256 = 18.7 min) and 16 min = the same DMF cell with the superseded UA = 0.20 W Kâ»Â¹ (193.5/0.20 = 16.1 min). So this is one more incompletely-propagated instance of the U' revision, not a two-solvent mixup. The associated point that category 9 registers c_p only for THF and DMF, leaving MeCN and water Ï unbacked, is confirmed."
          },
          {
            "finding": "lit-rep-risk minor â "Thin-gap cells reach their steady state some 400Ã faster" is the raw volume ratio, not the Ï ratio (correct â210Ã)",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Ï ratio = (C ratio)/(UA ratio) = (0.25/100)/(0.090764/0.172566) = 0.00475, i.e. 210Ã faster, not 400Ã. 400 is exactly 100 mL / 0.25 mL, so the UA ratio was omitted. Confirmed arithmetic error; immaterial to any conclusion (the qualitative point â thin-gap cells have no thermal inertia â is unaffected)."
          },
          {
            "finding": "lit-rep-risk minor â "the required duty ... spanning two orders of magnitude" set by solvent conductivity is 1.0-1.6 decades at fixed architecture",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "From panelC the solvent-driven spans at fixed architecture are 0.041805/0.001001 = 41.7Ã (5 mm flow), 0.058602/0.004721 = 12.4Ã (250 Âµm) and 0.098616/0.010206 = 9.7Ã (PEM stack). Two orders of magnitude is only reached by varying architecture simultaneously, which the sentence's own wording ("set by solvent conductivity") excludes. Minor overstatement, no conclusion at risk."
          },
          {
            "finding": "lit-rep-risk minor â "heat fluxes of 1-10 W cmâ»Â² are routinely rejected" widens the cited source's 2-6 W cmâ»Â² on both ends",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "make_si.js:362 says 1-10 W cmâ»Â²; parameters_provenance.csv:228 records '2-6 W cm-2 rejected across 10-20 K gradients in electrolyzer stacks' from Wallnoefer-Ogris 2024. The prose range exceeds the registered range at both ends with no additional citation. Documentation-level, immaterial to the panel (c) conclusion, which reads against bands rather than this number."
          },
          {
            "finding": "lit-rep-risk minor / registry-coverage m2 â the only registered aqueous boiling point is 'aq. KOH: Tb'; Fig K now uses 1 M NaOH",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "parameters_provenance.csv:221 confirmed as the sole aqueous Tb row; make_figK.py:71 uses '1 M NaOH aq'. The value (100 Â°C) is correct for either, so this is a stale label with zero numeric consequence. Purely cosmetic under the materiality lens, though it is a genuine loose end from the electrolyte fix."
          },
          {
            "finding": "lit-rep-risk minor â six mixture Wilke-Chang Ï values classed lit-representative cite Wilke & Chang 1955, which contains only the pure-solvent values",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Verified in build_param_tables.py:63: every Ï row, pure and mixture, is emitted with the same citation string 'Wilke & Chang, AIChE J. 1955, 1, 264-270', while the method_note says '(mixtures: fitted so phi*M = P-G rule)'. Fitted-in-this-work values should be class derived with a Poling citation. Same root cause as citation-integrity Â§3; no numeric consequence since only ÏM enters the correlation and it is set to satisfy the P-G rule by construction."
          },
          {
            "finding": "lit-rep-risk minor â 45 of 86 lit-representative rows carry no sensitivity statement, and the 41 that do are exactly the conductivities, where it is least needed",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Counted programmatically: 86 lit-representative rows, 45 with no 'sensitiv' string in method_note, split 27 Solvents / 12 Diffusivities / 3 Reactors / 2 Thermal / 1 Kinetics â matching the finding exactly, including that Î´_stirred (the C1 parameter) is among the three unstated Reactors rows. The observation that the sensitivity boilerplate is concentrated on the 41 Îº rows, which the audit itself shows are 37/41 load-bearing for nothing, is correct and is the sharpest framing of the brief's key concern."
          },
          {
            "finding": "registry-coverage m5 â Table S4's caption says the eight rows are used in the cell-voltage stack, but two are not in it and one appears under a different label",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "julia/cellvoltage.jl:13-20 contains six electrolytes; Table S4 (make_si.js:243-246) contains eight. '2 M NaCl (aq)' and 'Me4N carboxylate (10 mol%)/acetone' are in the table but not the stack, and Table S4's '0.3 wt% H2SO4/MeOH' appears in the stack as '0.03 M H2SO4 / MeOH (BASF)' at the same Îº (build_param_tables.py:134 gives 0.3 wt% â 0.025 M, so only the label diverges). Caption-accuracy issue, no numbers wrong."
          },
          {
            "finding": "registry-coverage m6 â the registered mesh (N = 80/90) does not cover N = 60, the value that produced npp_support_sweep.csv and npp_profiles.csv",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "julia/run_section4.jl uses FilmProblem(..., del, 60) for gate A (:42), gate B (:51), the support sweep (:60) and the profile dump (:72), while parameters_provenance.csv:231 registers 'Film nodes N (Tier-1 / EC') = 80 / 90'. Confirmed. Materiality is essentially nil: the same registry row records mesh-independence of â¤1% drift over N = 40-160, which covers 60, so the published values are unaffected â this is a registry-coverage gap, not a numerical one."
          },
          {
            "finding": "registry-coverage m7 â 25 orphaned registry rows (five-property blocks for DMSO, EtOH, AcOH, EtOH/H2O, DMF/H2O), and the three thermal rows that look superseded are still consumed by make_fig4B.py",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "reactions_50.csv's solvent column resolves to 15 distinct solvents; DMSO, EtOH, AcOH, EtOH/H2O and DMF/H2O are absent (DMSO and AcOH survive only inside the DMSO/THF and AcOH/HCOOH blends). figs/make_fig4B.py:139 does consume exactly COOL=[('still air',0.020),('stirred bath',0.18),('PEM-class plates',0.30)], so those three thermal rows are not orphans in practice â the finding is right about that and right that it is a consequence of C2. Trivial materiality; unused rows are a completeness observation, not a provenance failure."
          },
          {
            "finding": "registry-coverage m8 â data/make_fig4B.py and figs/make_fig4B.py are byte-identical duplicates",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "`diff` returns clean and both are 11778 bytes with identical Jul 13 22:57 mtimes. A real fix-propagation hazard given C2, but a maintenance issue rather than a provenance one. Note there is also a third copy at figs/_superseded/make_fig4B.py, which the finding does not mention."
          },
          {
            "finding": "fig-trace M1 â sec4_figH_ecprime.png has no generator anywhere in the tree and its open squares are not regenerable; the SI cites it",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Repo-wide grep for 'figH' returns zero hits outside node_modules and no savefig in figs/*.py or figs/_superseded/*.py targets sec4_figH_ecprime, while make_si.js:331 cites 'Fig. H, open squares'. Confirmed no generator. I also read the rendered PNG: the three open squares do sit flat on the ~48 mA cmâ»Â² total-catalysis cap at k = 3e3, 1e4, 1e5, while julia/npp_ecprime_sweep.csv gives 46.375 / 29.260 / 19.284 at those k. But the finding overstates: those three rows are flagged 'newton-wall (no collapse)' (strict lower bounds), the SI explicitly says 'in that regime the exact total-catalysis limit is reported instead', and the cap FD_SÂ·C_S/Î´ = 48.2 mA cmâ»Â² is arithmetically reproducible. So the squares are auditable, just not regenerable. Reproducibility gap, not a wrong conclusion."
          },
          {
            "finding": "fig-trace M2 â Fig E's generator reads julia/npp_support_sweep.csv and julia/npp_profiles.csv, neither of which exists at that path",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Confirmed: figs/make_figs.py:128 reads both from julia/; `ls` shows neither exists there, only in results/ (Jul 10, two days older than the Jul 12 render). run_section4.jl writes them to its own cwd (julia/), so the chain was consistent at generation and the files were subsequently moved. The four values quoted at make_si.js:320 (2.00, 1.38, 1.18, 1.04) check out exactly against results/npp_support_sweep.csv. Broken regeneration path, correct data â housekeeping, not provenance."
          },
          {
            "finding": "fig-trace C3 â make_fig_mediator_k.py plots a closed-form toy whose headline conclusion is contradicted by the project's own ECâ² solver output",
            "verdict": "CONFIRMED",
            "severity": "major",
            "reason": "I recomputed thin-gap/unstirred ratios from julia/mediated_ec_matrix.csv against the figure's I = min(300,x_k)/min(10,x_k): SCNâ» toy 1.00 vs solver 9.91; Brâ»/bromination 1.00 vs 8.70; BQ/Wacker 1.27 vs 4.73; ACT 1.00 vs 1.44; HMF 1.09 vs 1.70; Cl4NHPI 15.8 vs 4.52; Clâ» 16.7 vs 8.77. The grouped annotation 'reaction layer already < film -> plateau, reactor Ã1' is false for at least three of its cluster members, and the title 'only if it's slow' inverts for Cl4NHPI. The cause is real physics the toy omits: the solver's i_subcap scales as 1/Î´, so thin gaps help through the substrate cap even when the mediator plateaus. Downgraded from critical because the figure is cited nowhere in make_si.js and the script is unrunnable in this tree (hardcoded os.chdir('/home/claude/rce') at line 10), so it is plausibly a draft â but sec4_Fig_mediator_k.png was regenerated Jul 30, making it a current render, and if it ships it contradicts the SI's own mediated matrix."
          },
          {
            "finding": "Propagation analysis (all three audits) â 37 of the 41 lit-representative Îº are display-only; only four drive a conclusion, and the sign-flip risk is confined to the 250 Âµm microfluidic column",
            "verdict": "CONFIRMED",
            "severity": "minor",
            "reason": "Independently verified the scope claim: grep of kappa over *.jl/*.py/*.js shows it entering only cellvoltage.jl, run_cellvoltage.jl, run_section4.jl, make_figK.py, make_fig4B.py, make_figs.py Fig D and make_fig_main.py panel f. It appears in no transport quantity â correlations.jl's i_lim_tier0 and the NPP/ECâ² solvers take D, C, Î´, z only. The reactions_50.csv kappa_mScm column feeds Table S2 rendering and nothing else. My own Â±2Ã reruns reproduce all three audits' numbers: DMF at the 250 Âµm design point flips at ÎºÃ0.93 and MeCN flips the other way at ÎºÃ2 (I get 516.8 vs a 500 design current), while the beaker/stirred/flow conclusions hold across the whole range. So the brief's key concern is correctly answered: the Îº weakness is bounded and largely cosmetic, and the materially larger exposures are the unregistered thermal-geometry constants (Ï, h_int, i_design), Î´_stirred, and the un-propagated electrolyte fix in Table S4 / cellvoltage.jl / Fig 4B."
          }
        ]
      }
    ]
  },
  "workflowProgress": [
    {
      "type": "workflow_phase",
      "index": 1,
      "title": "Sweep"
    },
    {
      "type": "workflow_phase",
      "index": 2,
      "title": "Verify"
    },
    {
      "type": "workflow_phase",
      "index": 3,
      "title": "Synthesis"
    },
    {
      "type": "workflow_agent",
      "index": 1,
      "label": "sweep:registry-coverage",
      "phaseIndex": 1,
      "phaseTitle": "Sweep",
      "agentId": "a07f1e1c8cf1093e0",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785597857840,
      "queuedAt": 1785597857840,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "You are auditing the provenance of a scientific SI in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND TRUTH:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*.csvâ¦",
      "lastProgressAt": 1785598716272,
      "tokens": 171856,
      "toolCalls": 55,
      "durationMs": 858431,
      "resultPreview": "## PROVENANCE COVERAGE AUDIT â Section4_Model

Root: `/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model/`

---

### CRITICAL

**C1. Two absolute claims in the Fig-K narrative are falsified by Fig K's own machine-readable output.**
`make_si.js:370` (rendered at `SI_Section4_Transport_Model_v3â¦"
    },
    {
      "type": "workflow_agent",
      "index": 2,
      "label": "sweep:citation-integrity",
      "phaseIndex": 1,
      "phaseTitle": "Sweep",
      "agentId": "a406d80a6083c46dd",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785597857841,
      "queuedAt": 1785597857840,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "You are auditing the provenance of a scientific SI in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND TRUTH:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*.csvâ¦",
      "lastProgressAt": 1785598651490,
      "tokens": 110689,
      "toolCalls": 43,
      "durationMs": 793649,
      "resultPreview": "## CITATION INTEGRITY AUDIT â Section4_Model

---

### 1. CRITICAL â The Fig. K electrolyte fix was applied to the figure only; Table S4 and the Â§S6 worked example still carry all three unregistered electrolytes

`make_si.js:243â246` (Table S4 body) and `make_si.js:362` (Â§S6 text).

Table S4 rows, quoted verbatim:

```
["0.1 M Bu4NPF6 / THF","0.6","ion-paired, low-Îµ medium"],
["0.1 M Bu4NBF4 / DMFâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 3,
      "label": "sweep:lit-representative-risk",
      "phaseIndex": 1,
      "phaseTitle": "Sweep",
      "agentId": "a8e0b675992651d73",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785597857842,
      "queuedAt": 1785597857840,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "You are auditing the provenance of a scientific SI in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND TRUTH:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*.csvâ¦",
      "lastProgressAt": 1785598675890,
      "tokens": 136141,
      "toolCalls": 36,
      "durationMs": 818048,
      "resultPreview": "# Audit: lit-representative class, load-bearing use

Base dir: `/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model`

I reproduced the Fig K physics exactly from `figs/make_figK.py` (my recomputation matches `results/figK_thermal.json` to all printed digits) and re-ran every conclusion under Â±â¦"
    },
    {
      "type": "workflow_agent",
      "index": 4,
      "label": "sweep:figure-data-trace",
      "phaseIndex": 1,
      "phaseTitle": "Sweep",
      "agentId": "af7158e7af8f68af3",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785597857842,
      "queuedAt": 1785597857840,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "You are auditing the provenance of a scientific SI in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND TRUTH:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*.csvâ¦",
      "lastProgressAt": 1785598604995,
      "tokens": 140477,
      "toolCalls": 49,
      "durationMs": 747153,
      "resultPreview": "## FIGURE-TO-DATA TRACEABILITY AUDIT

Root: `.../Organic Electrosynthesis Perspective/Section4_Model`

---

### CRITICAL

**C1 â The Fig K electrolyte fix was never propagated to Fig 4B (or figD, or MAIN_composite, or `cellvoltage.jl`). The three "self-invalidating" electrolytes are still live in current, non-superseded renders.**

`figs/make_fig4B.py:134-139`:
```python
CELLS=[("THF, 5 mm (0.1 M â¦"
    },
    {
      "type": "workflow_agent",
      "index": 5,
      "label": "sweep:si-numeric-fidelity",
      "phaseIndex": 1,
      "phaseTitle": "Sweep",
      "agentId": "a1e3d6693820189ee",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785597857842,
      "queuedAt": 1785597857840,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "You are auditing the provenance of a scientific SI in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND TRUTH:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*.csvâ¦",
      "lastProgressAt": 1785598491970,
      "tokens": 123520,
      "toolCalls": 37,
      "durationMs": 634128,
      "resultPreview": "# NUMERIC-FIDELITY AUDIT â SI_Section4_Transport_Model_v3.docx

All values below were recomputed from `results/figK_thermal.json`, `figs/make_figK.py`, `julia/*.csv`, `data/*.csv` (I re-ran the FigK physics independently in Python and reproduced the JSON to <0.01%).

---

## CRITICAL

**C1. `make_si.js:370` â "every architecture at 500 mA cmâ»Â² and above falls short passively, in every solvent" is â¦"
    },
    {
      "type": "workflow_agent",
      "index": 6,
      "label": "sweep:model-assumption-audit",
      "phaseIndex": 1,
      "phaseTitle": "Sweep",
      "agentId": "a6188db8a41c24439",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785597857842,
      "queuedAt": 1785597857840,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "You are auditing the provenance of a scientific SI in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND TRUTH:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*.csvâ¦",
      "lastProgressAt": 1785598460054,
      "tokens": 116682,
      "toolCalls": 32,
      "durationMs": 602212,
      "resultPreview": "## MODEL-ASSUMPTION DISCLOSURE AUDIT â Section4_Model

All numbers below were regenerated independently. My reimplementation of `julia/correlations.jl` reproduces `julia/tier0_matrix.csv` to 4 s.f. and my reimplementation of `figs/make_figK.py` reproduces `results/figK_thermal.json` to the digit, so the deltas quoted are model deltas, not transcription differences.

---

### 1. CRITICAL â Two adjaâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 7,
      "label": "verify:source-accuracy",
      "phaseIndex": 2,
      "phaseTitle": "Verify",
      "agentId": "a2ea96b60cbec83cb",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785598716290,
      "queuedAt": 1785598716274,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "promptPreview": "You are an adversarial verifier for a provenance audit in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND TRUTH:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*â¦",
      "lastProgressAt": 1785599531733,
      "tokens": 146011,
      "toolCalls": 39,
      "durationMs": 815443,
      "resultPreview": "{"verdicts":[{"finding":"registry-coverage C1 / lit-rep-risk C2 â SI's \"every architecture at 500 mA cmâ»Â² and above falls short passively, in every solvent\" is falsified by results/figK_thermal.json","verdict":"CONFIRMED","severity":"critical","reason":"Read make_si.js:370 and results/figK_thermal.json directly. panelB at the 250 Î¼m microfluidic (i_design 500): DMF 515.62 (1.03Ã), aq. NaOH 841.4â¦"
    },
    {
      "type": "workflow_agent",
      "index": 8,
      "label": "verify:materiality",
      "phaseIndex": 2,
      "phaseTitle": "Verify",
      "agentId": "a97126e0aacdea86c",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785598716291,
      "queuedAt": 1785598716274,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "promptPreview": "You are an adversarial verifier for a provenance audit in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND TRUTH:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*â¦",
      "lastProgressAt": 1785599418738,
      "tokens": 136965,
      "toolCalls": 37,
      "durationMs": 702447,
      "resultPreview": "{"verdicts":[{"finding":"registry-coverage C1 / lit-rep-risk C2 â SI's \"every architecture at 500 mA cmâ»Â² and above falls short passively, in every solvent\" is falsified by results/figK_thermal.json","verdict":"CONFIRMED","severity":"critical","reason":"Verified directly in results/figK_thermal.json: at the 250 Âµm microfluidic (i_design = 500) panelB gives DMF 515.62 (1.03Ã) and aq. NaOH 841.41 â¦"
    },
    {
      "type": "workflow_agent",
      "index": 9,
      "label": "synthesis",
      "phaseIndex": 3,
      "phaseTitle": "Synthesis",
      "agentId": "aa8d6e9b39316f549",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785599531735,
      "queuedAt": 1785599531734,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "Synthesize a provenance audit of the Perspective SI in /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model.

GROUND:

PROJECT: Section 4 of a perspective on reaction engineering for electrified organic synthesis.
The SI is GENERATED from make_si.js (Node + docx library) reading data/*.csv; theâ¦",
      "lastProgressAt": 1785599884121,
      "tokens": 62229,
      "toolCalls": 7,
      "durationMs": 352386,
      "resultPreview": "# PROVENANCE AUDIT â Section 4 SI (`Section4_Model`)

Root: `/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model/`
Rendered artifact: `SI_Section4_Transport_Model_v3.docx` (verified byte-identical in text to the current output of `make_si.js`, so the shipped document *is* the generator's outpuâ¦"
    }
  ],
  "totalTokens": 1144570,
  "totalToolCalls": 335
}