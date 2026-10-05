# KAPPA SOURCING DOSSIER — Registry Category 6 (49 electrolyte conductivities)

Assembled 2026-08-02 from four family sourcing passes (THF/ethers, MeCN/nitriles, DMF-DMSO-amides,
aqueous), a consumption triage, and independent adversarial verification of each. Every number in
this dossier that is presented as sourced was re-derived or re-retrieved here; the arithmetic in
§3 was recomputed against `figs/thermal_model.py` in this session, not copied from the reports.

**This file is the only artefact of this pass. Nothing has been applied.** `data/electrolytes.csv`,
`data/build_param_tables.py`, `make_si.js` and the generators are untouched, per the concurrent-edit
constraint.

## Scope and standard

| state | requirement |
|---|---|
| **A — MEASURED** | external source WITH page/table locator, value stated at a defined T and molarity, retrieved in full text |
| **B — DERIVED** | named citable method, **all inputs A or B**, arithmetic shown |
| **C — ASSUMPTION** | declared, with a sensitivity bound |

Anything seen only in an abstract, only in a search snippet, or only through a secondary citation is
marked UNVERIFIED and does **not** count as A. Two candidate promotions were rejected on exactly this
ground and are listed in §4.

**Starting position:** 0 measured / 0 derived / 49 assumption.
**Ending position: 0 measured / 9 derived / 40 assumption** among the 49 registered rows.
One state-A measurement was found, but it lands on an *unused-legacy* row, not a registered one.

---

# 1. PER-ROW TABLE — all 49 registered electrolytes

`line` = line number in `data/electrolytes.csv` (header = line 1). Values in mS cm⁻¹.

Consumed-by codes:
- **FIGK** = `figs/thermal_model.py` → Fig K(a,b,c), Fig 4B(d,e,f), `make_figs.py` Fig D,
  `analysis_kappaT_sensitivity.py`, `make_si.js` §S6 prose (L405/413/415/421), Table S4, Table S7f.
  Only four rows are in this class.
- **S4** = printed in SI Table S4 as display-only (`make_si.js` L247–255) + Table S7f.
- **S7f** = Table S7f registry dump only. Enters no figure, no equation, no sentence.

| line | electrolyte | current | verified | state | locator | verdict | consumed-by |
|---|---|---|---|---|---|---|---|
| 63 | 3.0 M LiBr/THF | 3.0 | band 0.2–6.6; hard floor **0.206** is B | **C** (floor B) | Lee et al. *OPRD* 2022, 26, 2674–2684, main text R&D + SI Fig. S3 p. S6, CFD block p. S22 | **KEEP 3.0, REPLACE BAND.** No measured κ for LiBr/THF above 5×10⁻² M exists anywhere. Ohmic-differencing gives an unconditional floor of 0.206; the 3.29 "ceiling" is refuted (§4) | **FIGK** |
| 58 | 0.25 M Bu4NBF4/MeCN | 18.0 | **18.9** | **B** | Dorn et al. *JCED* 2024, 69, 1493–1502, **Table 3, p. 1499** (κmax 33.40, m̄max 1.48127, a 0.78646, b −0.02156); cross-check Gong et al. *EES* 2015, 8, 3515–3530, **Table 3, p. 3519** | **REPLACE → 18.9.** Casteel–Amis, all inputs A, reproduced independently twice. Band **15–23** | **FIGK** |
| 20 | 0.2 M NaI/DMF | 8.0 | not fixable; ceiling **≤16.38** is B | **C** (ceiling B) | Gopal & Jha, *Indian J. Chem.* 1977, **15A**, 80–83, **Table 2, p. 81, DMF column, 25 °C** (λ⁰ Na⁺ 29.81, I⁻ 52.11) | **KEEP 8.0, ADD CEILING.** λ⁰ is now state A; Λ(0.2 M) is not. Λ/Λ⁰ = 0.488 is not established | **FIGK** |
| 29 | 1 M NaOH aq | 180 | **178** (band 174–182) | **B** | CRC Handbook §5 **"Electrical Conductivity of Aqueous Solutions", p. 5-71** (NaOH 2 % = 93.1, 5 % = 206, 20 °C) + CRC **"Concentrative Properties of Aqueous Solutions"** NaOH block (1.000 M = 3.840 mass %) | **PROMOTE C→B, adopt 178 or keep 180 at the band's upper edge.** The inherited CRC withdrawal was written against the **wrong CRC table** | **FIGK** |
| 2 | 0.1 M Bu4NBF4/MeCN | 9.0 | **9.9** | **B** | Dorn Table 3, p. 1499 (same fit) | REPLACE → 9.9. Band 9.0–10.5 | S4 |
| 53 | 0.3 M Bu4NBF4/MeCN | 20.0 | **21.3** | **B** | Dorn Table 3, p. 1499 | REPLACE → 21.3. Band 19.5–23 | S7f |
| 56 | 0.077 M Bu4NBF4/MeCN | 7.0 | **8.1** | **B** | Dorn Table 3, p. 1499 | REPLACE → 8.1. Band 7.0–8.5 (moderate confidence) | S7f |
| 57 | 0.043 M Bu4NBF4/MeCN | 4.5 | **5.2** | **B−** | Dorn Table 3, p. 1499 | REPLACE → 5.2, **low confidence**: m̄ = 0.056 is below Dorn's own apparatus validation floor (Table 2, p. 1496). Band 4.0–5.5 | S7f |
| 60 | 2 M NaCl aq | 160 | **148** (146–150) | **B** | CRC p. 5-71 NaCl row + Concentrative Properties (2.000 M = 10.846 mass %) | **REPLACE → 148.** Both registry numbers (160 and the note's ≈158) are high by 7–8 % | S4 |
| 31 | 1 M KHCO3 aq | 80 | **75.5** (75–76) | **B** | CRC p. 5-71 KHCO₃ row + Concentrative Properties (1.000 M = 9.434 mass %) | REPLACE → 75.5 | S7f |
| 30 | 1 M Na2CO3 aq | 70 | **80** (79–81) | **B** | CRC p. 5-71 Na₂CO₃ row + Concentrative Properties | REPLACE → 80. Registry is 12 % low | S7f |
| 26 | 2 M H2SO4 aq | 700 | 638–651 provisional | **C** | Foxboro *Conductivity Ordering Guide* 1999, p. 1, 25 °C, H₂SO₄ column, 17.50 mass % | **STAYS C.** Vendor table with no primary attribution. CRC p. 5-71 H₂SO₄ row stops at 5 mass % and cannot reach 17.5 %. Bound ±8 % (620–720) | S7f |
| 27 | 1 M carbonate buffer pH 8.5 aq | 60 | — | **C** | — | STAYS C. Composition under-specified (Na⁺/K⁺ unstated); CRC NaHCO₃ block stops at 6.0 mass % = 0.743 M. Bound **45–75** | S7f |
| 28 | 0.5 M borate buffer pH 10 aq | 25 | — | **C** | — | STAYS C. No borate entry in any retrieved table. Bound **15–32** | S7f |
| 51 | 56 wt% Et4NOTs aq | 80 | — | **C** | Baizer *JES* 1964, 111, 215 (locator EMPTY) | STAYS C. Citation attached with no locator; unresolved whether Baizer reports κ or only composition | S7f |
| 14 | 0.1 M LiClO4/MeCN | 10.0 | ceiling **≤17.4** | **C** | Gong *EES* 2015 Table 2, p. 3518 (λ⁰ Li⁺ 69.97, ClO₄⁻ 103.6) | **STAYS C — do not action the "confirmed-equivalent" claim.** Λ/Λ⁰ = 0.576 was transferred from a *different salt* (Bu₄NBF₄). Kohlrausch ceiling is the only B content | S7f |
| 38 | 0.3 M LiClO4/MeCN | 20.0 | ceiling **≤52.1** | **C** | Gong Table 2, p. 3518 | STAYS C, same defect. Keep ceiling only | S7f |
| 55 | 0.033 M Et4NPF6/MeCN | 3.5 | ceiling **≤6.20** | **C** | Gong Table 2, p. 3518 (Et₄N⁺ 85.1 + PF₆⁻ 102.8 = Λ⁰ 187.9) | **STAYS C — DO NOT overwrite 3.5 with 4.6.** That replacement rests on cross-salt ratio transfer, which is exactly what state C exists to prevent | S7f |
| 39 | 0.1 M Et4NClO4/DMF | 4.0 | ceiling **≤8.81** | **C** | Gopal & Jha Table 2, p. 81 (Et₄N⁺ 35.39 + ClO₄⁻ 52.67 = Λ⁰ 88.06) | **STAYS C — DO NOT apply the "≈6" upward revision.** It rested on a cross-salt Λ/Λ⁰ monotonicity argument that does not hold and a gap smaller than its own error bar | S7f |
| 17 | 0.2 M nBu4NBr/DMA | 6.0 | ceiling ≲12.5 (Λ⁰ Bu₄N⁺ 22.90 + Br⁻ n/a) | **C** | Vermani et al. *Asian J. Chem.* 2019, 31(7), 1476–1480, Table 5 (DMA λ⁰) | STAYS C. λ⁰(Br⁻, DMA) not retrieved; ceiling is itself incomplete | S7f |
| 19 | 0.48 M LiBr/DMA | 12.0 | — | **C** | — | STAYS C. Das/Das/Hazra 2002 (DMAc) closed; no isotherm at 0.48 M | S7f |
| 18 | 0.21 M TBAB/DMSO-THF | 4.0 | — | **C** | — | STAYS C. No Bu₄NBr/DMSO value found in any pass. Mixed solvent (5:1 v/v) **and** off-convention temperature (exemplar runs at 85 °C vs the table's 25 °C header) | S7f |
| 21 | 0.24 M Et3NHBF4/THF-HFIP | 5.0 | — | **C** | — | STAYS C. Mixed solvent; preferential solvation forbids transfer | S7f |
| 32 | 1 M Et4NF.4HF/MeCN | 60.0 | — | **C** | — | STAYS C. Inherited citation ("Fuchigami reports") names no paper | S7f |
| 33 | 0.1 M HBF4/MeCN | 15.0 | — | **C** | — | STAYS C | S7f |
| 40 | 0.2 M NaClO4/MeCN | 12.0 | — | **C** | — | STAYS C. **λ⁰(Na⁺, MeCN) is absent from every source retrieved** (Gong Table 2 cation block runs Li⁺ → Me₄N⁺ with no Na⁺). Not even a ceiling is available | S7f |
| 44 | 0.08 M NaBr/MeCN | 4.0 | — | **C** | — | STAYS C, same Na⁺ gap | S7f |
| 54 | 0.04 M NaBr/MeCN | 1.5 | — | **C** | — | STAYS C, same Na⁺ gap | S7f |
| 66 | 0.48 M Bu4N carboxylate (in situ)/MeCN | 15.0 | — | **C** | — | STAYS C **permanently**. Conducting species generated in situ; speciation unknown | S7f |
| 43 | 0.085 M Et4NPF6/MeCN-HCl aq | 8.0 | — | **C** | — | STAYS C. Mixed solvent | S7f |
| 45 | 0.5 M NaBr aq/MeCN 1:1 | 40.0 | — | **C** | — | STAYS C. Mixed solvent; the "aqueous value halved" construction is not defensible | S7f |
| 47 | 0.1 M TBAP/MeCN-H2O | 10.0 | — | **C** | — | STAYS C. Mixed solvent | S7f |
| 67 | NaCl 7 mol% + pH 2 HCl/H2O-MeCN | 1.2 | — | **C** | — | STAYS C. Mixed solvent | S7f |
| 25 | 0.25 M KOAc/tAmOH-H2O | 8.0 | — | **C** | — | STAYS C. Mixed solvent | S7f |
| 34 | 0.1 M LiClO4/AcOH-HCOOH | 3.0 | — | **C** | — | STAYS C. Mixed solvent | S7f |
| 41 | 0.091 M MTES/HFIP-MeOH | 2.0 | — | **C** | — | STAYS C. Mixed solvent | S7f |
| 48 | 5 wt% AcOH/MeOH-H2O | 10.0 | — | **C** | — | STAYS C. Mixed solvent | S7f |
| 23 | 0.033 M Et4NPF6/MeOH | 3.0 | — | **C** | — | **STAYS C — NO FAMILY PASS WAS RUN.** See §4.3 | S7f |
| 35 | 0.0625 M LiClO4/MeOH | 4.0 | — | **C** | — | STAYS C — no family pass run | S7f |
| 52 | 0.156 M Et4NOTs/MeOH | 7.0 | — | **C** | — | STAYS C — no family pass run | S7f |
| 59 | 0.04 M NaBr/MeOH | 2.5 | — | **C** | — | STAYS C — no family pass run | S7f |
| 68 | 0.08 M Me4NBF4/MeOH | 5.0 | — | **C** | — | STAYS C — no family pass run | S7f |
| 46 | Et3N 7.5 mM (no salt)/MeOH | 0.5 | — | **C** | — | STAYS C. No supporting salt; speciation unknown | S7f |
| 64 | 0.3 wt% H2SO4/MeOH (BASF) | 3.0 | — | **C** | US 5,507,922 Ex. 1 — **supports composition only** | STAYS C. Also a **name mismatch** with `julia/cellvoltage.jl`, which calls it `0.03 M H2SO4 / MeOH (BASF)` | S4 |
| 22 | 0.1 M TBABF4/acetone | 8.0 | — | **C** | — | STAYS C — no family pass run (acetone) | S7f |
| 50 | 0.1 M LiClO4/acetone | 8.0 | — | **C** | — | STAYS C — no family pass run (acetone) | S7f |
| 65 | Me4NOH 15 mol% + Me4NBF4 5 mol%/acetone | 6.0 | — | **C** | — | STAYS C **permanently**. In-situ base/salt mixture, unknown speciation | S4 |
| 42 | 0.01 M Bu4NPF6/HFIP | 0.3 | — | **C** | — | STAYS C. HFIP (ε = 16.7) has no λ⁰ table; even the dilute-limit route is unavailable | S7f |
| 24 | 1 M LiClO4/MeNO2 | 12.0 | — | **C** | — | STAYS C — no family pass run (nitromethane) | S7f |

**Registered totals: A = 0 · B = 9 · C = 40.**
B rows are lines **2, 29, 30, 31, 53, 56, 57, 58, 60**.

## 1b. Unused-legacy rows that changed state (18 rows, none consumed by anything)

Recorded because one of them is the only state-A measurement in the entire category and because
three of them are already printed in an SI caption as *retired* entries.

| line | electrolyte | current | verified | state | locator | verdict |
|---|---|---|---|---|---|---|
| 4 | 0.1 M Bu4NPF6/THF | 0.6 | **0.506 at 22.0 ± 1.0 °C** (≈0.54 at 25 °C) | **A** | Zhang, Gu, Wang, Ware, Lu, Lin, Qi & See, *JACS Au* **2023**, 3(8), 2280–2290, DOI 10.1021/jacsau.3c00305, **Table 1, TBAPF₆ row**; footnote "Conductivity is measured at 22.0 ± 1.0 °C"; Metrohm 912 conductometer. Open access, PMC10466324. **Retrieved in full text and re-verified independently in this session.** | **THE ONLY STATE-A ROW IN CATEGORY 6.** Registry 0.6 is +11 % vs the measured 0.506 |
| 8 | 1 M KOH aq | 200 | **206** (204–209) | **B** | CRC p. 5-71 KOH row + Concentrative Properties; 0.364-pt extrapolation, declared | DERIVABLE |
| 9 | 0.5 M H2SO4 aq | 200 | **201.8** at **20 °C** | **B (20 °C only)** | CRC p. 5-71 H₂SO₄ row (reaches 5 mass %) + Concentrative Properties | κ₂₀ is B. The 25 °C leg is **C**: α for H₂SO₄ spans 0.29–2.46 %/K between the two retrieved tables |
| 11 | 1 M NaBr aq | 80 | **89** (88–90) | **B** | CRC p. 5-71 NaBr row + Concentrative Properties; α from family default, declared | DERIVABLE |
| 5 | 1 M LiBF4/THF | 5.0 | contradicted | **C** | *JACS Au* 2023 Table 1: 0.1 M LiClO₄/THF = **62.6 µS/cm**, 0.1 M TBABF₄/THF = **288.5 µS/cm**, both at 22 °C | 5 mS/cm at 1 M would require ~80× over the 0.1 M Li-salt anchor for a 10× concentration step against rising viscosity. **Not credible.** Delete or re-declare at ~1 mS/cm |
| 37 | LiBr/THF | 3.0 | — | **C** | — | **DELETE.** Concentration-free stub duplicate of line 63. A κ with no molarity must not sit in a registry |
| 3, 6, 7, 10, 12, 13, 15, 16, 36, 49, 61, 62 | (12 further legacy rows) | — | — | **C** | — | Unchanged; none consumed |

---

# 2. PATCH PLAN

**Do not apply from this document.** Written as `(file, row/key, old → new, citation string)`.
Another workflow holds the generators.

## 2.1 `data/electrolytes.csv`

Nine value edits, all on `registered` rows. The `state` column moves `assumption` → `derived` on
exactly these nine.

| # | file | row (line, key) | old → new | citation string to attach |
|---|---|---|---|---|
| P1 | `data/electrolytes.csv` | L58 `0.25 M Bu4NBF4/MeCN` | `18.0,assumption` → **`18.9,derived`** | Casteel–Amis with κmax = 33.40 mS cm⁻¹, m̄max = 1.48127 mol kg⁻¹, a = 0.78646, b = −0.02156 from Dorn, Kareth, Weidner & Petermann, *J. Chem. Eng. Data* 2024, 69, 1493–1502, Table 3, p. 1499; c → m̄ via MW 329.27, ρ(MeCN) 0.7768 g cm⁻³ → m̄ = 0.347; cross-checked at 1 M against Gong, Fang, Gu, Li & Yan, *Energy Environ. Sci.* 2015, 8, 3515–3530, Table 3, p. 3519 (32.3 vs 32.75, +1.4 %). Band 15–23. |
| P2 | `data/electrolytes.csv` | L2 `0.1 M Bu4NBF4/MeCN` | `9.0,assumption` → **`9.9,derived`** | same fit, m̄ = 0.133. Band 9.0–10.5. |
| P3 | `data/electrolytes.csv` | L53 `0.3 M Bu4NBF4/MeCN` | `20.0,assumption` → **`21.3,derived`** | same fit, m̄ = 0.423. Band 19.5–23. |
| P4 | `data/electrolytes.csv` | L56 `0.077 M Bu4NBF4/MeCN` | `7.0,assumption` → **`8.1,derived`** | same fit, m̄ = 0.101. Band 7.0–8.5. |
| P5 | `data/electrolytes.csv` | L57 `0.043 M Bu4NBF4/MeCN` | `4.5,assumption` → **`5.2,derived`** | same fit, m̄ = 0.056 — **below Dorn's own apparatus validation floor (Table 2, p. 1496)**; declare low confidence, band 4.0–5.5. |
| P6 | `data/electrolytes.csv` | L29 `1 M NaOH aq` | `180.0,assumption` → **`178.0,derived`** | CRC Handbook §5 "Electrical Conductivity of Aqueous Solutions", p. 5-71 (NaOH: 2 % = 93.1, 5 % = 206 mS cm⁻¹, **20 °C**) with CRC "Concentrative Properties of Aqueous Solutions" NaOH block (1.000 M = 3.840 mass %, 20 °C) → 162–166 mS cm⁻¹ at 20 °C; ×1.075–1.095 for 20 → 25 °C (α = 1.5–1.9 %/K, from the CRC/Foxboro overlap at 1, 3 and 5 wt%) → **174–182**. Independent 25 °C read of Foxboro *Conductivity Ordering Guide* 1999, p. 1 at 3.840 % gives 177–179. |
| P7 | `data/electrolytes.csv` | L60 `2 M NaCl aq` | `160.0,assumption` → **`148.0,derived`** | CRC p. 5-71 NaCl row + Concentrative Properties (2.000 M = 10.846 mass %) → 133.6–134.4 at 20 °C; α = 1.9–2.2 %/K → **146–150**. Foxboro 25 °C read at the same mass % gives 147–149. |
| P8 | `data/electrolytes.csv` | L31 `1 M KHCO3 aq` | `80.0,assumption` → **`75.5,derived`** | CRC p. 5-71 KHCO₃ row + Concentrative Properties (1.000 M = 9.434 mass %) → 68.6–68.8 at 20 °C; α = 1.8–2.2 %/K → **75–76**. |
| P9 | `data/electrolytes.csv` | L30 `1 M Na2CO3 aq` | `70.0,assumption` → **`80.0,derived`** | CRC p. 5-71 Na₂CO₃ row + Concentrative Properties → 72.4–72.9 at 20 °C; α = 1.8–2.2 %/K → **79–81**. |
| P10 | `data/electrolytes.csv` | L37 `LiBr/THF` | **DELETE ROW** | concentration-free stub duplicate of L63; `unused-legacy`, consumed by nothing. |
| P11 | `data/electrolytes.csv` | L4 `0.1 M Bu4NPF6/THF` | `0.6,assumption` → **`0.51,measured`** | Zhang, Gu, Wang, Ware, Lu, Lin, Qi & See, *JACS Au* 2023, 3(8), 2280–2290, DOI 10.1021/jacsau.3c00305, **Table 1**, TBAPF₆ entry, 0.1 M in THF, σ = 506.3 µS cm⁻¹; footnote b "Conductivity is measured at 22.0 ± 1.0 °C"; Metrohm 912 conductometer. Open access. **Row is `unused-legacy` — this is a provenance win, not a numerical one.** |

**No edit to L63 (`3.0 M LiBr/THF`), L20 (`0.2 M NaI/DMF`), L14, L38, L55 or L39.** All six keep
their current value and their `assumption` state. Their patch is a *sensitivity-string* patch only
(§2.2), not a value patch. This is deliberate — see §4.

## 2.2 `data/build_param_tables.py`

Edits are to the category-6 block, lines ~390–530. No structural change; the `ECOND_PROV` dict gains
entries and `provenance_class` must become `derived` for the nine rows above (the loop at L534–546
currently hard-codes `assumption` for every row not in `ECOND_PROV` — it will need a `derived` set or
a per-row class field).

| # | file | key | old → new | citation string |
|---|---|---|---|---|
| B1 | `build_param_tables.py` | `ECOND_PROV["1 M NaOH aq"]` method_note | `"no concentrated-NaOH conductivity table could be page-anchored. The inherited CRC citation is wrong on its face…"` → **derived-state note** | "DERIVED. The earlier withdrawal was written against the wrong CRC table. CRC Section 5 carries two conductivity tables: 'Equivalent Conductivity of Electrolytes in Aqueous Solution' (Vanysek, p. 5-74, 25 C, c <= 0.1 mol/L, whose NaOH row in fact terminates at 0.01 mol/L) and 'Electrical Conductivity of Aqueous Solutions' (p. 5-71, 20 C, **0.5-50 mass %**), which reaches every concentrated aqueous row in this registry. Method: read c <-> mass % off CRC 'Concentrative Properties of Aqueous Solutions' (20 C, prints c/mol L-1 directly, so no density model is invoked), read kappa(mass %) off p. 5-71 (20 C), correct 20 -> 25 C with alpha = 1.5-1.9 %/K for hydroxides. Pipeline validated against ASTM D 1125-95(2005) Table 1 Reference Solution A (1 demal KCl, 7.11352 mass %, 111.342 mS/cm at 25 C): steps 1-2 land within +0.3 to +1.2 %." |
| B2 | `build_param_tables.py` | `ECOND_PROV["1 M NaOH aq"]` citation / locator | `"-- (no source supports this value)"`, `""` → **CRC pair** | citation: "CRC Handbook of Chemistry and Physics, Section 5"; locator: "'Electrical Conductivity of Aqueous Solutions', p. 5-71 (NaOH row: 2 % = 93.1, 5 % = 206 mS/cm, 20 C) with 'Concentrative Properties of Aqueous Solutions', NaOH block (1.000 M = 3.840 mass %, 20 C)". **Verify the folio against the author's own edition before printing** — the retrieved facsimile is the 91st ed. (`pdfinfo` Title: 'CRC Handbook of Chemistry and Physics, 91th Edition'); the repo cites the 97th elsewhere. The unambiguous fingerprint is the title + "All values refer to 20 °C" + its two refs (CRC 70th ed. p. D-221; Wolf, *Aqueous Solutions and Body Fluids*, 1966). |
| B3 | `build_param_tables.py` | `ECOND_PROV["1 M NaOH aq"]` sensitivity | `"…Margins are 10-42x…"` → **unchanged margins, add band** | "CARRIES A CONCLUSION (the aqueous reference trace of Fig. K). Now DERIVED, band 174-182 mS cm-1; 180 sits at the upper edge of that band and 178 is the centre. Margins are 10-42x across all five architectures (flip factors 0.0236 / 0.0262 / 0.0301 / 0.0961), so every aqueous statement in S6.1 and S6.2 survives even a tenfold error, and the +/-2 % band moves no ceiling by more than 1 %." |
| B4 | `build_param_tables.py` | `ECOND_PROV["0.25 M Bu4NBF4/MeCN"]` (whole tuple) | assumption + mass-action bound → **derived + measured global ceiling** | method: "DERIVED by Casteel-Amis (Casteel & Amis, J. Chem. Eng. Data 1972, 17, 55) from the measured fit of Dorn et al., Table 3, p. 1499. Independently validated at 1 M against Gong et al. Table 3, p. 3519 (32.75 derived vs 32.3 tabulated, +1.4 %)." citation: "Dorn, Kareth, Weidner & Petermann, J. Chem. Eng. Data 2024, 69, 1493-1502; Gong, Fang, Gu, Li & Yan, Energy Environ. Sci. 2015, 8, 3515-3530". locator: "Dorn Table 3, p. 1499 (ACN / (C4H9)4NBF4: m_max 1.48127, kappa_max 33.40, a 0.78646, b -0.02156, validity range 9.10, MAPE 1.65 %); Gong Table 3, p. 3519 (Bu4NBF4/AN, 1 M, 32.3 mS cm-1, after Izutsu 2009)". |
| B5 | `build_param_tables.py` | `ECOND_PROV["0.25 M Bu4NBF4/MeCN"]` sensitivity | `"…flips at kappa >= 31.6 mS cm-1, which lies INSIDE the rigorous upper bound of 36…"` → **the flip is now excluded on the kappa axis** | "CARRIES A CONCLUSION. Band 15-23 mS cm-1 (the +/-10 % first estimate is too tight: Dorn's own dissertation, p. 74, applies his own Casteel-Amis equation at m = 0.075 and prints kappa_ref = 7.04 where the published Table 3 parameters give 6.465, a +8.9 % unexplained self-inconsistency). The microfluidic statement -- 'MeCN falls short at 500 mA cm-2' -- flips at kappa >= 31.6 mS cm-1. That is now EXCLUDED on the kappa axis: 31.6 is 94.6 % of the MEASURED global maximum kappa_max = 33.40 mS cm-1 for this salt in this solvent over all concentrations, while 0.25 M sits at m/m_max = 0.234, i.e. 23 % of peak molality, where kappa/kappa_max = 0.567. Solving the fit for kappa >= 31.6 requires c in [0.64, 1.09] M, a 2.6-4.4x higher concentration. The earlier mass-action bound of 24-36 mS cm-1 is superseded and should be deleted: it was a Lee-Wheaton extrapolation 25x above its own fitted range (2e-4 to 1e-2 mol dm-3). The verdict remains bound-dependent, but on the kappa(T) axis of S6.3 ONLY, not on kappa itself." |
| B6 | `build_param_tables.py` | `ECOND_PROV["3.0 M LiBr/THF"]` sensitivity | `"Sensitivity band 0.5-8.8 mS cm-1 … survives to 2.9x"` → **narrower band, and two corrected margins** | "CARRIES A CONCLUSION. Band REVISED to 0.2-6.6 mS cm-1. Lower end is a state-B hard floor: total cell resistance <= V/I = 3.2 V / 0.520 A = 6.154 ohm in a coaxial annulus with R_i 9.5 mm, R_o 11.0 mm and L = 18.43 cm derived from the stated 17.8 mL annulus volume, giving kappa >= 1.266e-3 / 6.154 = 0.206 mS cm-1 [Lee et al., Org. Process Res. Dev. 2022, 26, 2674-2684, main text Results & Discussion + SI Fig. S3 p. S6 and CFD block p. S22]. Upper end is NOT 8.8 and NOT the 3.29 first reported: the ohmic-differencing ceiling assumes equal non-ohmic overpotential across LiBr concentrations, which is refuted for Al anodes in THF by Zhang, Guan, Wang, Lin & See, Chem. Sci. 2023, 14, 13108-13118, and rests on dV = 0.2 V between two 2-significant-figure voltages, so dV = 0.1 V (admitted by rounding) raises it to 6.58. **The registered 2.9x margin is WRONG for two live sentences**: the zero-gap 'beyond forced-air rejection' claim of S6.2 flips at 1.297x and the 25 mA cm-2 'marginal pass' concession of S6.1 flips at 1.395x. Across the full 0.2-6.6 band THF nonetheless fails every architecture at every design current (see below), which the currently registered 0.5-8.8 band did NOT guarantee." |
| B7 | `build_param_tables.py` | `ECOND_PROV["0.2 M NaI/DMF"]` method_note | `"lambda0 for NaI in DMF could not be verified…"` → **correct the record; lambda0 IS verified** | "STAYS AN ASSUMPTION, but the earlier note is superseded: lambda0 for NaI in DMF CAN be verified and now is. lambda0(Na+, DMF, 25 C) = 29.81 and lambda0(I-, DMF, 25 C) = 52.11 S cm2 mol-1 [Gopal & Jha, Indian J. Chem. 1977, 15A, 80-83, Table 2, p. 81, DMF column, 25 C; full text retrieved from the NIScPR open repository]. Kohlrausch additivity gives Lambda0(NaI, DMF, 298 K) = 81.9 +/- 0.8, cross-validated against measured Lambda0(NaClO4, DMF) = 83.3 [Bhat, Mohan & Susha, Indian J. Chem. 1996, 35A, 825-831, Table 1, p. 826, interpolated 293/303 K] versus 82.48 predicted. The earlier failure was a paywall-routing problem, not an absence of data, and the note's own sanity figures ('near 30 and 51') are now confirmed as 29.81 and 52.11. What is STILL missing is Lambda(c) at 0.2 M: no measurement of the conductance attenuation of NaI in DMF at working concentration was located, so the value cannot be derived." |
| B8 | `build_param_tables.py` | `ECOND_PROV["0.2 M NaI/DMF"]` sensitivity | append hard ceiling + the two unqualified sentences | "…Hard physical ceiling, state B: kappa <= c*Lambda0 = 2.000e-4 mol cm-3 * 81.92 S cm2 mol-1 = 16.38 mS cm-1, since Lambda(c) <= Lambda0 for all c > 0. The tabled 8.0 implies Lambda/Lambda0 = 0.488 and the microfluidic flip requires 0.453; which side of 0.453 the true attenuation falls on is NOT established. Honest band 4-16 mS cm-1. TWO FURTHER LIVE SENTENCES rest on this row and are currently UNQUALIFIED: (a) S6 preamble 'T_ss ~ 202 C, far above DMF's 153 C boiling point' flips at kappa_crit = 11.15 mS cm-1, margin 1.394x -- inside the honest band; (b) S6 preamble 'the same cell at 50 mA cm-2 draws 14.9 V, which is the 10-20 V range' holds only over kappa = 5.7-13.2 mS cm-1 (x0.710 down / x1.645 up). Both must be restated as conditional on the adopted kappa, exactly as the withdrawn 500 mA cm-2 pass already is." |
| B9 | `build_param_tables.py` | `ECOND_PROV["2 M NaCl aq"]` | `"the inherited CRC citation cannot support this value…"` → **derived** | "DERIVED by the CRC p. 5-71 route (see the NaOH row). CRC 'Concentrative Properties', NaCl block: 10.0 % = 1.832 M, 12.0 % = 2.229 M, so 2.000 M = 10.846 mass %. CRC p. 5-71 NaCl row (20 C): 5 % = 70.1, 10 % = 126, 15 % = 171 mS/cm -> 133.6-134.4 at 20 C; alpha = 1.9-2.2 %/K -> 146-150 at 25 C. Foxboro 1999 25 C NaCl column read at the same mass % gives 147-149. **Both inherited numbers are high**: 160 by +8 %, the note's 158 by +7 %. Resolving them against each other would have converged on the wrong value. Chambers, Stokes & Stokes, J. Phys. Chem. 1956, 60, 985-986 remains the correct primary pull and was NOT retrieved -- do not cite it." |
| B10 | `build_param_tables.py` | new `ECOND_PROV` entries for `1 M KHCO3 aq`, `1 M Na2CO3 aq` | `"same CRC objection…"` → **derived** | same CRC p. 5-71 + Concentrative-Properties method; KHCO₃ 1.000 M = 9.434 mass %, Na₂CO₃ per its own block; alpha = 1.8-2.2 %/K (carbonates: no 25 C overlap table exists, so the ASTI/Ricca declared 2 %/K +/- 0.2 is used and is declared as such). |
| B11 | `build_param_tables.py` | `ECOND_PROV["2 M H2SO4 aq"]` | keep as assumption, replace the note | "STAYS AN ASSUMPTION. CRC p. 5-71 CANNOT support this row: its H2SO4 entry stops at 5 mass % (0.5 % = 24.3, 1 % = 47.8, 2 % = 92, 5 % = 211) and 2 M is 17.496 mass % -- a factor-3.5 extrapolation that returns 487 (quadratic) against 707 (linear), i.e. nonsense. The Foxboro 1999 25 C column does reach it and gives 638-651 mS cm-1 at 17.50 mass %, but that is a vendor table with no primary attribution and therefore does not reach state A or B. Declared bound 620-720 mS cm-1 (+/-8 %); the tabled 700 sits at the top of it. Note further that alpha for H2SO4 spans 0.29 %/K (at 1 mass %) to 2.46 %/K (at 5 mass %) between the CRC 20 C and Foxboro 25 C tables -- a factor-8 spread proving the two lineages disagree by several percent independent of temperature, so no temperature-corrected derivation is available for this solute at all. PULL: Darling, J. Chem. Eng. Data 1964, 9, 421-426, DOI 10.1021/je60022a041." |
| B12 | `build_param_tables.py` | `KAPPA_PULL` (the shared string on ~40 rows) | `"…its SI may convert 8-10 of these rows to state A in a single pass"` → **corrected** | The promise is not supported by what was retrieved. Dorn's **Table 3 (p. 1499) contains exactly four Casteel-Amis fits**: ACN/(C2H5)4NBF4, ACN/(C4H9)4NBF4, MeOH/NaI, MeOH/KSCN. Of those, one matches a registry salt (Bu4NBF4/MeCN → 5 registry rows, now derived); NaI and KSCN in MeOH appear in no registry row. The 164 measured isotherms are in the **ACS Supporting Information**, a separate file that was NOT retrieved — the open-access dissertation (Ruhr-Universität Bochum, DOI 10.13154/294-13199) reproduces the article body only and itself points to the ACS SI. Rewrite as: "PULL NEEDED: the **Supporting Information** of Dorn et al. 2024 (not the article body, which yields only 4 fits, one of them already adopted here). Dorn's Table 1 salt list does include NaBr and (C4H9)4NBr, so the SI plausibly reaches several MeOH rows, but this is unverified." |
| B13 | `build_param_tables.py` | `ECOND_PROV["0.1 M Et4NClO4/DMF"]` (new) | add ceiling | "STAYS AN ASSUMPTION. Kohlrausch ceiling, state B: Lambda0(Et4NClO4, DMF, 298 K) = 35.39 + 52.67 = 88.06 S cm2 mol-1 [Gopal & Jha, Indian J. Chem. 1977, 15A, 80-83, Table 2, p. 81, DMF column, 25 C -- single convention, do NOT blend with the Bu4NBPh4 reference-electrolyte split of Vermani et al. 2019], so kappa <= 8.81 mS cm-1. The tabled 4.0 implies Lambda/Lambda0 = 0.454. **An earlier pass proposed raising this to ~6 mS cm-1 on a cross-salt Lambda/Lambda0 monotonicity argument; that argument is invalid (Lambda(c)/Lambda0 is monotone in c only for a GIVEN salt in a GIVEN solvent) and the anomaly it rested on is smaller than the 5.6 % disagreement between the two retrieved lambda0(ClO4-, DMF) values. Do not apply it.**" |
| B14 | `build_param_tables.py` | `ECOND_PROV` entries for `0.1 M LiClO4/MeCN`, `0.3 M LiClO4/MeCN`, `0.033 M Et4NPF6/MeCN` (new) | add ceilings, keep values | "STAYS AN ASSUMPTION. Kohlrausch ceiling, state B, from Gong et al., Energy Environ. Sci. 2015, 8, 3515-3530, Table 2, p. 3518 (Li+ 69.97, ClO4- 103.6, Et4N+ 85.1, PF6- 102.8 S cm2 mol-1; Et4N+ corroborated at 86.34 by Kalugin et al. 2019, Table 3): kappa <= 17.4 / 52.1 / 6.20 mS cm-1 respectively. The tabled values are NOT confirmed: converting the ceiling to a value requires Lambda/Lambda0, and the only route available was to transfer the ratio measured for a DIFFERENT salt (Bu4NBF4). That transfer is an assumption, so it does not upgrade the row and MUST NOT be used to overwrite the tabled value." |
| B15 | `build_param_tables.py` | `ECOND_PROV` for `0.2 M NaClO4/MeCN`, `0.08 M NaBr/MeCN`, `0.04 M NaBr/MeCN` (new) | record the structural gap | "STAYS AN ASSUMPTION, and no ceiling is available either. **lambda0(Na+, MeCN) is absent from every source retrieved in this pass** -- the Gong et al. Table 2 cation block runs Li+ (69.97) straight to Me4N+ (94.5) with no Na+ entry, and Kalugin et al. tabulate only R4N+ and anions. Minc & Werblan, Electrochim. Acta 1962, 7, 257-266 (alkali perchlorates in MeCN) is the correct pull and is closed. Until it is opened these three rows cannot even carry a Kohlrausch ceiling." |
| B16 | `build_param_tables.py` | `ECOND_PROV["0.21 M TBAB/DMSO-THF"]` (new) | flag the temperature convention | "STAYS AN ASSUMPTION. Mixed solvent (DMSO/THF 5:1 v/v) AND off-convention temperature: the exemplar runs at **85 C** while Table S4 is headed '25 C'. No measured conductivity for Bu4NBr in DMSO or in DMSO/THF mixtures at any concentration was located in this pass. Do not propagate any 85 C estimate -- that would be an assumption stacked on an assumption." |
| B17 | `build_param_tables.py` | five MeCN rows L2/L53/L56/L57/L58 | `provenance_class` `assumption` → `derived` | the loop at L534-546 hard-codes `assumption` for rows absent from `ECOND_PROV`; it needs a `DERIVED` set (or a per-row class) so the nine promoted rows emit `derived`. |
| B18 | `build_param_tables.py` | `S_KAPPA_DISPLAY` | `"45 of the 49 registered conductivities are in this position"` | still correct (only 4 rows are consumed by a figure) — **no change**, but note that 9 of the 45 are now `derived` display-only rather than `assumption` display-only. |

## 2.3 Not a κ patch, but found in the same pass and blocking

Three defects sit in files this workflow may not touch and are recorded here so they are not lost.
None is fixed by any amount of literature retrieval.

- **`figs/make_fig_main.py` L208–210** hardcodes `(0.06, 0.35, 0.90, 0.35, 20.0)` S m⁻¹ with **no
  `thermal_model` import**, while `figs/make_fig4B.py:48` imports the registry values. The main-text
  composite and SI Fig. 4B(d) plot the same solvent labels at the same 5 mm gap and disagree by
  **2.3–5×** (THF 85.8 V vs 19.1 V at 100 mA cm⁻²; crossings of the shared 10–20 V band at 21 vs
  105 mA cm⁻²). §S6.1 explicitly disowns 0.06 and 0.35 as unregistered while the main text still
  plots them.
- **`julia/cellvoltage.jl`** retains the same retired shadow list (3 of 6 κ values unregistered), and
  `run_section4.jl:101` still prints the **withdrawn** worked example (`ELECS[2]` = 0.1 M
  Bu4NBF4/DMF at 5 mm) that §S6 says inverts. `cellvoltage.csv` ships with the SI.
- **`make_si.js` L415** lists THF's 0.042 (5 mm flow) and 0.059 (microfluidic) W cm⁻² K⁻¹ under
  "beyond passive **and forced-air** rejection". `COOLING_BANDS` puts forced air at 0.02–0.08, so
  both are **inside** it. Only the zero-gap 0.099 is beyond, and by 1.23×. The error is stated twice
  in the same paragraph. This is a prose/band inconsistency, independent of κ.

---

# 3. NUMBERS THAT MOVE

All recomputed in this session against `figs/thermal_model.py` (bisection on i_boil, U_passive from
geometry). **Exactly one figure-consumed κ changes value: MeCN, 18.0 → 18.9 mS cm⁻¹.** The aqueous
NaOH change (180 → 178) is inside the band and moves nothing; THF and DMF keep their values.

## 3.1 MeCN 18.0 → 18.9 mS cm⁻¹ (+5.0 %)

| quantity | old | new | figure / SI sentence | flips? |
|---|---|---|---|---|
| unstirred beaker i_boil | 83.9 | **85.9** | Fig K(a), Fig K(b); `make_si.js` **L413** "MeCN reaches 84 and DMF 85 mA cm⁻², margins of roughly 1.7× each" → **86 and 85** | no (design 50) |
| stirred beaker i_boil | 88.5 | **90.6** | Fig K(b) | no |
| 5 mm flow i_boil | 153.8 | **157.3** | Fig K(b) | no (design 100) |
| **250 µm microfluidic i_boil** | **426.1** | **432.6** | Fig K(b); **L413** "MeCN (426, 0.85×) falls short" → **(433, 0.87×)** | **no** — flip needs 31.56 mS cm⁻¹ |
| zero-gap i_boil | 109.0 | **109.4** | Fig K(b); **L413** "all four fall short, by factors of … 9.2× (MeCN)" → **9.1×** | no |
| U′_req 5 mm flow | 0.00570 | **0.00547** | Fig K(c); **L415** "MeCN and DMF need 0.005–0.022 W cm⁻² K⁻¹" | no — range text unchanged |
| U′_req microfluidic | 0.01169 | **0.01140** | Fig K(c) | no |
| U′_req zero-gap | 0.02220 | **0.02174** | Fig K(c); upper end of the "0.005–0.022" range | no — still rounds to 0.022 |
| κ(T) upper bracket, microfluidic | 551.2 | **557.0** | **L421** "whose ceiling runs 426 mA cm⁻² at 25 °C and 551 mA cm⁻² at the upper bound against a 500 mA cm⁻² design current" → **433 and 557** | no — still straddles 500 |
| κ(T) upper bracket, beaker | 133.7 | **136.8** | **L421** "84 to 134" → **86 to 137** | no |
| Table S4 margin cell | "0.57× microfluidic" | **"0.60×"** | `make_si.js` **L248** | no |

**No published conclusion flips from the MeCN value change.** Every threshold is cleared or missed
by the same margin sign as before.

**But one conclusion is materially strengthened, and this is the only place in the pass where a
stated hedge should be *reduced*.** Table S4 (L248) and `build_param_tables.py` currently say the
mass-action bound is 24–36 mS cm⁻¹ and that the 31.6 flip point "lies INSIDE" it — i.e. the shortfall
verdict is undetermined by κ's own uncertainty. That is now wrong in the safe direction:

- κ_max = **33.40 mS cm⁻¹** is the *measured* global maximum for Bu₄NBF₄ in MeCN over **all**
  concentrations at 25 °C (Dorn Table 3; the maximum lies inside the measured range, m̄max = 1.481
  against a validity range of 9.10).
- The flip point 31.6 is **94.6 %** of that global maximum, while 0.25 M sits at m̄/m̄max = **0.234**
  and κ/κ_max = 0.567.
- Solving the fit for κ ≥ 31.6 requires **c ∈ [0.64, 1.09] M**, a 2.6–4.4× higher concentration.

So the κ-axis half of "MeCN's shortfall must not be asserted" can be retired. The κ(T)-axis half
(§S6.3: the ceiling reaches 557 at the boiling-point bracket) **survives unchanged**, so the sentence
at L413 must still be flagged bound-dependent — but for one reason instead of two. The old 24–36
mass-action bound should be deleted outright: it was a Lee–Wheaton extrapolation 25× above its own
fitted range of 2×10⁻⁴–1×10⁻² mol dm⁻³.

## 3.2 aq. NaOH 180 → 178 mS cm⁻¹ (−1.1 %), and the state change from C to B

| quantity | at 180 | at 178 | band 174–182 | flips? |
|---|---|---|---|---|
| unstirred beaker i_boil | 286.5 | 285.0 | 282.1–287.9 | no (design 50) |
| stirred beaker i_boil | 303.2 | 301.6 | 298.5–304.7 | no |
| 5 mm flow i_boil | 487.1 | 484.9 | 480.6–489.2 | no (design 100) |
| **250 µm microfluidic i_boil** | **841.4** | **840.3** | **838.1–842.5** | **no** (design 500; margin 1.68×) |
| zero-gap i_boil | 148.9 | 148.9 | 148.8–148.9 | no (design 1000; fails by 6.7×, unchanged) |

`make_si.js` **L413** "aqueous NaOH reaches 286 mA cm⁻²" → 285; "aqueous NaOH at 841 mA cm⁻², a
margin of 1.68×" → 840, 1.68×. **L421** "286 to 484" → 285 to 483.

**No conclusion flips. The figure is visually unchanged.** The whole value of this row's change is
the *provenance state*, not the number:

> **This is the single most consequential result of the pass.** The claim that carries Fig. K —
> aqueous NaOH clears the 500 mA cm⁻² microfluidic passively — previously rested on a κ whose
> registry citation field read literally `-- (no source supports this value)`. It now rests on a
> **derived** value with two page-anchored inputs, arithmetic shown, and a pipeline validated against
> a certified standard (ASTM D 1125-95(2005) Table 1, 1 demal KCl = 111.342 µS cm⁻¹ at 25 °C;
> steps 1–2 land +0.3 to +1.2 %).

**A published statement must therefore be WITHDRAWN — the withdrawal itself.** Table S4 L249 and
`PROVENANCE_STANDARD.md` §5 both assert that the CRC citation is withdrawn because "the CRC
concentrative-properties tables carry no conductivity, and its equivalent-conductivity table stops at
0.1 M." Both halves of that sentence are factually true and the conclusion drawn from them is wrong:
CRC Section 5 carries a **third** table, "Electrical Conductivity of Aqueous Solutions", p. 5-71,
κ in mS cm⁻¹ over **0.5–50 mass %** at 20 °C, covering NaOH, KOH, NaCl, Na₂SO₄, Na₂CO₃, KHCO₃,
NaHCO₃, H₂SO₄, NaBr, K₂CO₃, KCl and ~36 others. The withdrawal was written against p. 5-74 and never
opened p. 5-71. **Reinstate the CRC citation with the correct table and folio.** (Two caveats travel
with it: verify the folio against the author's own edition — the retrieved facsimile is the 91st;
and the "Concentrative Properties" PDF that was retrieved is a 1998 PageMaker re-typeset, not a CRC
facsimile, so cite the author's own copy for that locator, which the SI already does at
pp. 5-118–5-135, 97th ed.)

Note also that §2.2 of the aqueous pass found the old objection *understated*: the Vanýsek NaOH row
terminates at **0.01 mol L⁻¹**, not 0.1 — the gap to 1 M was two orders of magnitude, not one.

## 3.3 THF: the value does not move, but the band does — and that is what matters

3.0 mS cm⁻¹ is **kept**. The registered band 0.5–8.8 mS cm⁻¹ is **replaced by 0.2–6.6**.
i_boil (mA cm⁻²) across the band, against each architecture's design current:

| κ (mS cm⁻¹) | beaker (50) | stirred (50) | 5 mm (100) | 250 µm (500) | zero-gap (1000) |
|---|---|---|---|---|---|
| 0.206 (state-B floor) | 7.8 ✗ | 8.2 ✗ | 14.7 ✗ | 53.7 ✗ | 26.3 ✗ |
| **3.0 (adopted)** | **29.5 ✗** | **31.1 ✗** | **55.1 ✗** | **181.7 ✗** | **65.6 ✗** |
| 6.58 (rounding-admitted ceiling) | 43.4 ✗ | 45.8 ✗ | 80.6 ✗ | 247.2 ✗ | 75.9 ✗ |
| *8.78 (top of the OLD registered band)* | *50.0 ✓* | *52.8 ✓* | *92.4 ✗* | *274.1 ✗* | *78.9 ✗* |

**THF fails every architecture at every design current across the entire new band.** The old band did
**not** guarantee that: its top end, 8.8 mS cm⁻¹, is numerically the beaker flip point (κ_crit = 8.78),
so the currently registered sensitivity string admits the very flip the figure's punchline denies.
Tightening the band from 0.5–8.8 to 0.2–6.6 is therefore a real, if unglamorous, repair — the THF
punchline becomes band-proof for the first time, without the value changing at all.

**Two live sentences must nonetheless be re-margined — the registered "2.9×" is too generous:**

| SI sentence | locator | true flip factor | verdict |
|---|---|---|---|
| "requiring … 0.099 W cm⁻² K⁻¹ in a zero-gap stack: beyond passive and forced-air rejection" | `make_si.js` **L415** | **1.297×** (U′ crosses 0.08 at κ = 3.89 mS cm⁻¹) | inside the new band → **must be softened**. (U′ = 0.0986 at 3.0; 0.0914 at 3.29; 1.2013 at the floor — the claim itself survives the band, but not at 2.9× as advertised) |
| "at a 25 mA cm⁻² design current … the THF beaker ceiling of 26–30 mA cm⁻² becomes a marginal pass rather than a failure" | `make_si.js` **L413** | **1.395×** (flips at κ = 2.15 mS cm⁻¹) | **undetermined across the band**: 7.8 at the floor (fail), 43.4 at the ceiling (pass). Must be restated as conditional |
| "the THF statements below survive to 2.9× and should be read as directional at that precision" | `make_si.js` **L412** | — | **false as written.** True of the Fig. K(b) pass/fail verdicts only. Rewrite to name the two exceptions |

## 3.4 DMF: value unchanged, but two unqualified sentences now have numbers

8.0 mS cm⁻¹ is kept, state C. No figure number changes. The 500 mA cm⁻² pass is already withdrawn.
What the pass adds is a **state-B hard ceiling of 16.38 mS cm⁻¹** and, from the triage, two live
sentences that no one had margined:

| SI sentence | locator | value | flip point | margin | status |
|---|---|---|---|---|---|
| "the full lumped balance places its passive steady state at T_ss ≈ 202 °C — far above DMF's 153 °C boiling point … the conclusion is that it boils" | **L405** | T_ss = 202.1 °C | κ_crit = 11.15 | **1.394×** | **LIVE AND UNQUALIFIED** — inside the honest 4–16 band |
| "the same cell at 50 mA cm⁻² draws 14.9 V, which is the 10–20 V range common in academic non-aqueous reports" | **L405** | E = 14.90 V (12.50 ohmic) | 20 V at ×0.710; 10 V at ×1.645 | **1.41× / 1.64×** | **LIVE AND UNQUALIFIED** |
| "DMF at 516 mA cm⁻², a margin of 1.03×" | **L413** | 515.6 | κ_crit = 7.42 | 1.078× | already withdrawn ✓ |

Both unqualified sentences must be given the same treatment the 500 mA cm⁻² pass already has. Neither
is *wrong* — 202 °C and 14.9 V are what the model returns at the adopted κ — but each is a conclusion
resting on an assumed input whose honest band straddles the threshold.

## 3.5 Display-only aqueous rows

`2 M NaCl aq` 160 → 148 (−7.5 %), `1 M KHCO3 aq` 80 → 75.5 (−5.6 %), `1 M Na2CO3 aq` 70 → 80 (+14 %).
All three are **S7f / S4 display-only**; κ enters no transport quantity, and none is plotted. **No
figure and no sentence moves.** One caption sentence does: Table S4 L251, "The registry's own note
reads ≈158; no table was opened to resolve the discrepancy" — both numbers are wrong and resolving
them against each other would have converged on the wrong value. Retire the note with the correction.

---

# 4. STAYS STATE C

**40 of 49 registered rows.** Grouped by *why*, because the reason determines whether anything must
be withdrawn.

## 4.1 The two conclusion-carrying rows that stay C

### `0.2 M NaI/DMF` = 8.0 mS cm⁻¹ — **the most exposed number in the category**

- **Sensitivity bound that makes it honest:** 8.0 mS cm⁻¹, assumption, band **4–16 mS cm⁻¹
  (÷2 to ×2)**, hard upper ceiling **16.38 mS cm⁻¹** (state B: κ ≤ c·Λ⁰ with Λ⁰(NaI, DMF, 298 K) =
  81.9 ± 0.8 S cm² mol⁻¹ from λ⁰(Na⁺) = 29.81 + λ⁰(I⁻) = 52.11, Gopal & Jha 1977, Table 2, p. 81).
- **Must anything be withdrawn?** The 500 mA cm⁻² pass — already withdrawn, correctly, and it must
  **stay** withdrawn. Do not reinstate it on the strength of the new λ⁰ work: λ⁰ is state A now, but
  Λ(0.2 M) is not, and the verdict turns entirely on whether the attenuation Λ/Λ⁰ at 0.2 M is above
  or below 0.453. No retrieved source fixes it.
- **Must anything be softened?** Yes — **two sentences at L405 that are currently stated flat**
  (T_ss ≈ 202 °C, margin 1.394×; and 14.9 V in the 10–20 V band, margin 1.41×/1.64×). Both sit
  inside the honest band. Softening them is not optional if the 500 mA cm⁻² sentence was softened
  for a 1.078× margin.
- **Correct the record:** the registry's own note that "λ⁰ for NaI in DMF could not be verified" is
  now **superseded**. It can be, and has been. The failure was paywall routing, not absent data.
- **Cheapest route to A:** measure it. 0.2 M NaI in dry DMF, calibrated probe, 25 °C, ten minutes.
  The result must land in (0, 16.4) mS cm⁻¹ — the row is now *checkable*, which it was not before.

### `3.0 M LiBr/THF` = 3.0 mS cm⁻¹

- **Sensitivity bound that makes it honest:** 3.0 mS cm⁻¹, assumption, band **0.2–6.6 mS cm⁻¹**,
  with a state-B hard floor of **0.206 mS cm⁻¹** (R_tot ≤ V/I = 3.2 V / 0.520 A in a coaxial annulus
  of known geometry; Lee et al. *OPRD* 2022).
- **Must anything be withdrawn?** **No.** THF fails every architecture at every design current across
  the whole band (§3.3). The punchline is safe.
- **Must anything be softened?** Yes, two sentences (§3.3), and the blanket "survives to 2.9×" claim
  at L412 must be rewritten to name them.
- **Do NOT adopt 1.5 mS cm⁻¹ as a derived point value.** The first pass proposed this. It fails the
  state-B standard: the point value is set by an *assumed* κ(1.5 M) with no source, the report's own
  bracket spans 1.24–2.48, the "hard ceiling" of 3.29 is a two-significant-figure artefact
  (ΔV = 3.2 − 3.0 admits ΔV ∈ [0.1, 0.3] on rounding alone, and ΔV = 0.10 V puts the ceiling at
  6.58), and the equal-non-ohmic-overpotential premise is refuted for Al anodes in THF by Zhang et
  al., *Chem. Sci.* 2023, 14, 13108–13118, where Br⁻ concentration is precisely what relieves Al₂O₃
  passivation — so Lee's voltage differences are partly anodic, not ohmic. Adopting 1.5 would state
  a ceiling ~30 % lower than the model's own best estimate, **in the manuscript's favour**. A referee
  will read that as a thumb on the scale. Keep 3.0 and widen honestly.
- **There is no state-A route.** No published direct measurement of κ for LiBr in THF above
  ~5×10⁻² M exists anywhere. That is itself a reportable finding.

## 4.2 Rows that stay C with a state-B ceiling (partial credit, no conclusion at risk)

All display-only (S7f). Each should carry its ceiling in the registry so the row is *falsifiable*
even while it stays an assumption.

| row | value | state-B ceiling | source of the ceiling |
|---|---|---|---|
| 0.1 M LiClO4/MeCN | 10.0 | ≤ **17.4** | Gong *EES* 2015 Table 2, p. 3518 |
| 0.3 M LiClO4/MeCN | 20.0 | ≤ **52.1** | same |
| 0.033 M Et4NPF6/MeCN | 3.5 | ≤ **6.20** | same |
| 0.1 M Et4NClO4/DMF | 4.0 | ≤ **8.81** | Gopal & Jha 1977 Table 2, p. 81 |
| 2 M H2SO4 aq | 700 | 620–720 (vendor-bounded, not a ceiling) | Foxboro 1999, p. 1 |

**Two proposed upgrades were rejected here and must not be applied.** Both were arithmetically
correct and methodologically invalid:

1. `0.033 M Et4NPF6/MeCN` 3.5 → 4.6 — rests on transferring Λ/Λ⁰ = 0.749 measured for **Bu₄NBF₄** to
   **Et₄NPF₆**. Overwriting a registry value with an unnamed cross-salt heuristic is exactly what
   state C exists to prevent.
2. `0.1 M Et4NClO4/DMF` 4.0 → ≈6 — a 50 % upward revision resting on a claim that Λ/Λ⁰ must decrease
   monotonically *across different salts*. It need not; and the 7.2 % anomaly it rested on falls to
   3.7 % — below the two sources' own 5.6 % disagreement on λ⁰(ClO₄⁻) — if the other retrieved value
   is substituted.

## 4.3 Rows that stay C because **no family pass was run on them** — an honest gap in this pass

Twelve registered rows are in solvents no family covered. They were not investigated and failed; they
were **not investigated at all**.

- **MeOH (7):** L23 `0.033 M Et4NPF6/MeOH`, L35 `0.0625 M LiClO4/MeOH`, L52 `0.156 M Et4NOTs/MeOH`,
  L59 `0.04 M NaBr/MeOH`, L68 `0.08 M Me4NBF4/MeOH`, L46 `Et3N 7.5 mM/MeOH`, L64
  `0.3 wt% H2SO4/MeOH (BASF)`
- **Acetone (3):** L22, L50, L65
- **HFIP (1):** L42 · **MeNO₂ (1):** L24

This is the largest single tranche of unexamined rows and it is worth naming, because the registry's
own `KAPPA_PULL` string — repeated on ~40 rows — promises that Dorn et al. 2024 "may convert 8–10 of
these rows to state A in a single pass." **That promise is not supported by what was retrieved.**
Dorn's Table 3 (p. 1499), read directly in this session, contains exactly four Casteel–Amis fits:
ACN/(C₂H₅)₄NBF₄, ACN/(C₄H₉)₄NBF₄, MeOH/NaI, MeOH/KSCN. One matches a registry salt (already adopted,
P1–P5). NaI and KSCN in MeOH appear in **no** registry row. The 164 measured isotherms live in the
**ACS Supporting Information**, a separate file that was never obtained — the open-access dissertation
route reproduces the article body only and itself points to the ACS SI. Dorn's Table 1 salt list does
include NaBr and (C₄H₉)₄NBr, so the SI *plausibly* reaches several MeOH rows, but that is unverified
and must be stated as such.

## 4.4 Rows that are C permanently

- **Mixed solvents (10 registered):** L18, L21, L25, L34, L41, L43, L45, L47, L48, L67. Preferential
  solvation invalidates any λ⁰ or κ transfer, and no isotherm exists for any of these compositions.
  L18 additionally runs at **85 °C** against a 25 °C table header — a convention mismatch that should
  be flagged in the table, not silently carried.
- **In-situ / unknown speciation (3):** L65 `Me4NOH + Me4NBF4/acetone`, L66 `Bu4N carboxylate
  (in situ)/MeCN`, L46 `Et3N 7.5 mM (no salt)/MeOH`. The conducting species is generated in the cell.
  No method can apply.
- **Na⁺ in MeCN (3):** L40, L44, L54. λ⁰(Na⁺, MeCN) is absent from every source retrieved, so these
  cannot carry even a Kohlrausch ceiling. Pull: Minc & Werblan, *Electrochim. Acta* 1962, 7, 257–266
  (closed).
- **HFIP (1):** L42. ε = 16.7, no λ⁰ table exists; even the dilute-limit route is unavailable.

## 4.5 Sources that were NOT retrieved — do not cite any of these

Every one resolves correctly via Crossref (checked; no chimera), but **none was opened**, so none may
appear as support for a value: LeSuer, Buttolph & Geiger *Anal. Chem.* 2004, 76, 6395–6401 · Minc &
Werblan *Electrochim. Acta* 1962, 7, 257–266 · Ue, Ida & Mori *JES* 1994, 141, 2989–2996 · Izutsu,
*Electrochemistry in Nonaqueous Solutions*, 2009 (seen only through Gong Table 3 — cite as "tabulated
by Gong et al. 2015, Table 3, after Izutsu 2009") · Chambers, Stokes & Stokes *J. Phys. Chem.* 1956,
60, 985–986 · Darling *JCED* 1964, 9, 421–426 (DOI 10.1021/je60022a041) · Krumgalz & Barthel
*Z. Phys. Chem.* 1984, 142, 167–178 · Boruń & Bald *JCED* 2012, 57, 2037–2043 (DOI 10.1021/je300252d;
the `je300323w` circulating in search results returns no Crossref record) · Das *J. Solution Chem.*
2008, 37, 947–955 · Dudley et al. *J. Power Sources* 1991, 35, 59–82 · Peters et al. *Science* 2019
Supplementary Materials (403; contains no conductivity data in the retrievable main text) ·
International Critical Tables Vol. VI (OCR too corrupt to quote; needs a page scan) · Barthel &
Neueder, *Electrolyte Data Collection*, DECHEMA Vol. XII (print-only; **highest yield per unit effort
for the whole amide family**) · Dorn et al. 2024 **Supporting Information**.

Also on the do-not-cite list for a different reason: **Artemkina et al., *Russ. J. Electrochem.*
2025, 61(4), 221–234** — the paper is real and the pagination is correct (Russian original; the
Pleiades translation is 150–161), but the DOI advertised on the journal's own page,
`10.31857/S0424857025040031`, returns **404 at doi.org and is absent from Crossref**. Cite by
journal/volume/pages, never that string. And the value drawn from its abstract was
temperature-misattributed in the first pass (c_max = 1.258 M is the **10 °C** figure, not 25 °C;
interpolation gives ≈1.40 M) — the conclusion drawn from it survives, but the number had drifted.

---

# 5. BOTTOM LINE

Nine of the forty-nine registered conductivities reached **derived (B)**; none reached **measured
(A)**; forty stay **assumption (C)**. That is the honest headline, and it is a modest one: 82 % of
the category is still an assumption, and twelve of those rows — every MeOH, acetone, HFIP and
nitromethane entry — were never investigated at all rather than investigated and failed. What did
move is the part that mattered most. **The Fig. K punchline is now half-measured and half-assumed,
and the measured half is the aqueous one:** "aqueous NaOH clears 500 mA cm⁻² passively" rests on a
derived κ = 178 mS cm⁻¹ (band 174–182) built from two page-anchored CRC tables with the arithmetic
shown and the pipeline validated against a certified ASTM standard — replacing a registry field that
read literally "no source supports this value." The CRC withdrawal printed in the SI was written
against the wrong CRC table and should be reversed. "THF fails everywhere" still rests on a pure
assumption, 3.0 mS cm⁻¹, and always will — no measurement of LiBr in THF above 0.05 M exists in the
literature — but the Lee et al. flow-Birch data now pin a hard floor of 0.206 mS cm⁻¹ and shrink the
honest band from 0.5–8.8 to 0.2–6.6, and across that whole band THF fails every architecture at every
design current. The old band did not guarantee that: its upper end, 8.8, *is* the beaker flip point.
So the THF punchline is band-proof for the first time, on an input that never became a measurement.
**No published conclusion flips**, and only one figure-consumed number changes at all (MeCN
18.0 → 18.9 mS cm⁻¹, moving the microfluidic ceiling 426 → 433 against a 500 threshold). One hedge
should be *reduced* — MeCN's shortfall is no longer undetermined by κ's own uncertainty, because the
measured global maximum for that salt in that solvent is 33.40 mS cm⁻¹ and the flip needs 31.6 at
2.6–4.4× the actual concentration — though it stays bound-dependent on the κ(T) axis. **The single
weakest remaining number is 0.2 M NaI/DMF at 8.0 mS cm⁻¹**: still state C, now bounded above at
16.38 mS cm⁻¹, and carrying two live sentences in the §S6 preamble (T_ss ≈ 202 °C, margin 1.394×;
"draws 14.9 V, in the 10–20 V range", margin 1.41×/1.64×) that are stated flat while a *looser*
claim on the same row was withdrawn for a 1.078× margin. Both must be softened, and the row's own
note that "λ⁰ for NaI in DMF could not be verified" is now wrong — it has been, from primary full
text, so the row is at last a *checkable* one-probe measurement away from closing.
