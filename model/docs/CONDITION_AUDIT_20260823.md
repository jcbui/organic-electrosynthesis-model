# Condition audit — all 50 rows read against their own PDF

*2026-08-23. Gate: `data/check_conditions.py` (G-COND) + `data/exemplar_pdf_map.csv`.
Evidence: `results/condition_anchor.json`, `results/pdftext/`.*

Every carrier, substrate and supporting-electrolyte concentration in `reactions_50.csv` was read
against the paper it claims to come from. All 50 rows now map to a retrieved PDF
(`data/exemplar_pdf_map.csv`); the map is checked for existence and completeness on every run.

**The rule applied throughout: the numbers for one row must come from ONE experiment.** A carrier
molarity from one figure and a substrate molarity from another describes nothing anyone ran, even
though each number is individually "in the paper."

## What the gate can and cannot do

G-COND anchors a concentration if the PDF text contains an explicit molarity, an
`x mmol`/`y mL` quotient (including running sums, because papers write `CH3CN (7 mL), MeOH (1 mL)`
and never print the 8), or a `mol %`/`equiv` read against a nearby concentration. It then requires
the supporting quotes to lie within 1400 characters of each other.

**It checks magnitude, never identity.** Row 46 came back ANCHORED on an electrolyte molarity of
0.0625 M that is real — and belongs to a different salt than the one the row names. Co-location is
likewise a proxy for co-experiment, so a PASS is a screen and only a FAIL is conclusive. Every
verdict below comes from reading the quote, not from the gate's label.

Negative control (`--negative-control`, substrate ×1.7) collapses ANCHORED from 15 to **0**.

## CONFIRMED — page-anchored, one experiment (31 rows)

| row | reaction | the quote that fixes all of it |
|---|---|---|
| 0 | Ni aryl amination | `10 mol % Ni(bpy)3Br2, nBu4N·Br (0.2 M), DBU (2.0 equiv), DMA (0.025−0.05 M)` |
| 1 | ArX + NH3 amination | anchored, single locus |
| 2 | Shono oxidation | `Anodic oxidation of 12 (13.42 mmol) in methanol (8.61 ml) containing [Et4NOTs] (1.34 mmol)` → 1.559 M / 0.1556 M |
| 4 | Mn diazidation | `0.2 mmol alkene, 0.01 mmol MnBr2·4H2O, 1.0 mmol NaN3, 400 µl of HOAc, 3.5 ml of LiClO4 solution in MeCN (0.1 M)` → 0.0513 / 0.00256 |
| 5 | Br-Hofmann | `100 mmol), NaBr (2.06 g, 0.2 equiv)` with `concentrations of 1a of 0.4 M (entry 5)` → 0.4 / 0.08 |
| 7 | amidyl-radical amination | `1 (0.3 mmol), CH3CN/MeOH (7/0.5 v/v), NaBr (0.3 mmol)` → 0.04 / 0.04 |
| 9 | Ritter-type | anchored, single locus |
| 10 | Co-H hydroamination | `Conditions A: CoBr2(glyme) (10 mol%), 4,4′-MeO-bpy (11 mol%), Et3NHBF4 (3 equiv), THF (0.08 M)` |
| 12 | Ni-XEC | `optimized multiday electrolysis of 0.3 M 2`; `1.6 equiv of LiBr` → 0.48 M |
| 18 | Cu benzylic cyanation | `0.2 mmol of 4, n-Bu4NBF4 (0.077 M), MeCN (5 ml), TFE (0.15 ml), H2O (0.06 ml)` + `Cu(acac)2 (10 mol%)` |
| 19 | Ni aryl-aryl homocoupling | `Solvent : 50 mL, PhBr 15 mmol., NiBr2bpy 1.5 mmol., supporting electrolyte: NaBr 4.10-2 mol.L-1` → 0.3 / 0.03 / 0.04 |
| 20 | 2-naphthol coupling | `5 mmol 2-naphthol ... in 5 ml of 0.2 mol l-1 NaClO4-MeCN` → 1.0 / 0.2 |
| 21 | acrylonitrile (ADN) | Table II **run 28**: `Et4N \| 141 \| 94.5 \| 40.0` %AN, fn e = `56% aqueous solution of tetraethylammonium p-toluenesulfonate` |
| 23 | nitroarene → aniline | fn g: `scaled up to 0.052 mol using a catholyte solution of 96 mL: 400 mm 1a, 1:1 H2O/MeOH, and 2M H2SO4(aq)` |
| 26 | aryl chloride dehalogenation | anchored, single locus |
| 27 | benzaldehyde → benzyl alcohol | anchored, single locus |
| 28 | ACT alcohol oxidation | `1272 mmol of LEV-CH2OH and 5 mol % ACT in 2540 mL of aqueous carbonate buffer, NaHCO3 (1.0M)/Na2CO3 (1.0M), pH 8.5` → 0.501 / 0.025 / 1.0 |
| 32 | lignin → vanillin | anchored, single locus |
| 34 | NHPI allylic C-H | `terpenoid substrate (0.5 mmol), Cl4NHPI (0.1 mmol) ... LiClO4 as the supporting electrolyte (0.1 M) in acetone (6 ml per mmol of substrate)` → 0.167 / 0.033 / 0.1 |
| 35 | alkenesulfonate | anchored, single locus |
| 36 | HMF → FDCA | Fig 7: `100 mM HMF and 40 mM ACT (borate buffer, pH 10)`; `0.5 M borate buffer (pH 10)` anolyte |
| 39 | decarboxylative elimination | anchored, single locus |
| 40 | Co-H isomerization | `1 (3–6 mol%), HFIP (1–4 equiv.), TBABF4 (0.1 M), acetone (2.5 ml)` with 0.2 mmol → 0.08 / 0.0048 / 0.1 |
| 41 | oxazoline cyclization | anchored, single locus |
| 43 | lactonization | `1 (0.5 mmol), CH3CN (7 mL), MeOH (1 mL), n-Bu4NBF4 (2 mmol)` → 0.0625 / 0.25 |
| 44 | benzylic fluorination | `Anodic benzylic fluorination of 1, 3, 5a–5f (1 mmol) ... in MeCN (10 ml) containing 1 M Et4NF·4HF` → 0.1 / 1.0 |
| 47 | aryl thiocyanation | `acetic and formic acids (1:1), 0.1 M LiClO4 ... 5 mmol substrate and 2 mmol NH4SCN` → 0.25 / 0.10 / 0.1 |
| 48 | C-H phosphonylation | `arene substrate (0.05 M, 1 equiv)`; `HBF4·Et2O (0.4 mmol) ... MeCN (4 mL)` → 0.1 M |
| 14 | BDD phenol-arene | **electrolyte only**: `0.68 g of Et3NMe·OSO3Me, 27 mL of HFIP, 6 mL of MeOH` → 0.0907 M |
| 37 | radical-cation Diels-Alder | **electrolyte only**: Table entry 1 `1.0 M LiClO4 / MeNO2 / 98%` |
| 45 | Br- bromination | **carrier only**: `The mixture of equal volume of 0.5 M NaBr aqueous solution and acetonitrile was found to give the best` → 0.25 M |

## DEFECTS — 10 confirmed

**D1 — row 3, wrong journal and wrong year.** Exemplar says `Zhao/H.-C. Xu Angew 2017`. The paper
is **ChemSusChem 2021, 14, 1692–1695**, `10.1002/cssc.202100254`.

**D2 — row 3, wrong solvent.** Model carries `MeOH`. Standard conditions are
`amidine (0.3 mmol), Et4NPF6 (0.3 mmol), THF/MeOH (5:1, 9 mL), reflux`. MeOH-only is entry 2 of the
optimisation table (52% vs 65%). The concentrations 0.033/0.033 are right; the solvent is not.
Also **reflux**, against the model's isothermal 25 °C.

**D3 — WITHDRAWN. Row 43's year was already right.** I recorded `OL 2018 → OL 2017` and changed
the file, then checked the PDF header: *"Cite This: Org. Lett. 2018, 20, 252−255"*, published
7 December 2017 in the January 2018 issue. **An ACS DOI's `7b`/`8b` prefix is a manuscript-ID year,
not a publication year** — `acs.orglett.7b03617` is a 2018 paper. The change has been reverted and
the reasoning recorded in the row's provenance so it is not "re-fixed" later. `ol8b00981` really is
Org. Lett. 2018, 20, 3443−3446, so row 7 was right too. The SI's `zhangzeng2018` entry
(S. Zhang, L. Li, H. Wang, Q. Li, W. Liu, K. Xu and C. Zeng, *Org. Lett.* **2018**, *20*, 252–255)
was correct all along.

**D4 — row 46, wrong supporting electrolyte.** Model: `0.0625 M LiClO4/MeOH`. The paper's standard
conditions are `1a (0.5 mmol), 2 (1.0 mmol), MeOH (8 mL), TsOH (0.5 mmol), 4 Å MS (200 mg),
constant current = 10 mA` — **no LiClO4**. Table 1 entry 15 (no electrolyte, TsOH only) gives 82%,
beating entry 6 with LiClO4 (79%). LiClO4 appears in the introduction describing *Lei's* prior
work. The added electrolyte is TsOH at 0.5 mmol/8 mL = 0.0625 M — same molarity, different salt,
and a strong acid in MeOH rather than a 1:1 lithium salt, so κ and the migration factor both move.

**D5 — row 46, carrier is not the limiting reagent.** The anodically discharged species is the
sulfinate at 2 equiv = **0.125 M**; the row carries the styrene at 0.0625 M on a declared
"conservative limiting-reagent basis". Conservatism is not a justification — it halves a published
ceiling by choosing the smaller of two real numbers.

**D6 — row 45, two different experiments.** Model pairs carrier 0.25 M with substrate 0.121 M.
Neither figure supports that pair:

| | Br- | substrate | solvent |
|---|---|---|---|
| Fig 4 `NaBr (0.5 M in deionized water, 7.5 mL), CH3CN (7.5 mL) in each chamber, 1 (0.5 mmol)` | 0.25 M | 0.033 M | 1:1 water/MeCN |
| Fig 5c `NaBr (0.5 M ..., 12.5 mL), CH3CN (12.5 mL) ..., 1 (0.5 mmol)` | 0.25 M | 0.020 M | 1:1 |
| **Fig 5b — the 518 g flow run the exemplar cites as "0.61 kg"** `Substrate (4 mmol), solvent (0.5 M NaBr in deionized water (10 mL):CH3CN:CH3OH:CH2Cl2 = 10:10:10:3)` | **0.152 M** | **0.121 M** | 10:10:10:3 |

The substrate 0.121 M comes from Fig 5b, the carrier 0.25 M from Fig 4. Since the exemplar cites
the kg-scale run, the same-experiment fix is **Fig 5b: Br- 0.152 M, substrate 0.121 M**. This is
one of the eight mediated EC′ rows — the γ = 0.288 inverted cell — so it must be re-solved.

**D7 — row 31, wrong salt and wrong Henry basis.** Model: `2 M NaCl aq`. Paper: `1.0 M potassium
chloride (KCl) electrolyte`; NaCl does not appear. Substrate is pure-water Henry's law, and must be
saturation in 1 M KCl (salting-out reference `je60038a033.pdf` is on hand for this).

**D8 — rows 10 and 40, wrong DOI.** `10.1038/s41557-021-00640-2` is a *Nature Chemistry*
desaturation paper. The Conditions A/B text verified above is
**`10.1038/s41586-022-04595-3`** (Nature 2022).

**D9 — row 15, an electrolyte the paper says it did not use.** Model carries
`0.48 M Bu4N carboxylate (in situ)`. The paper states: *"No additional supporting electrolyte was
required, because of the excellent conductivity in the microfluidic channel."* Note also the cell
is **25 µm**, not the generic architectures modelled.

**D10 — row 19, wrong solvent.** Model: `MeOH`. Paper: `DMF (10 ml) + EtOH (40 ml) or in EtOH
(25 ml) + MeOH (25 ml)`. The three concentrations are right; pure MeOH is not one of the media.

## NOT PAGE-ANCHORABLE — state C, not state A (11 rows)

These numbers are consistent and plausible but are **not in the retrieved article body** — they
live in SIs we do not have. They must not be carried as measured values.

| row | what is missing |
|---|---|
| 6 | `0.20 mmol scale` is printed; the volume is not. 0.02 M implies 10 mL. Electrolyte 0.3 M Bu4NBF4 **is** anchored. Solvent is `CH3CN/pyridine (100/5)`, not neat MeCN. |
| 11 | Kolbe: nothing on Me4NOH / Me4NBF4 / hexanoate concentration in the body |
| 13 | `NaI (0.2 M)` anchored; `0.1 mmol scale` printed, volume not. 0.029 M implies 3.5 mL. |
| 14 | phenol amount never printed — only `2 F/mol of phenol, ratio phenol/arene = 1:3`. 0.15 M implies 5 mmol/33 mL. |
| 16 | Giese: carrier and substrate |
| 22 | Birch: all three. LiBr is named as replacing LiClO4; no molarity in body. |
| 24 | `0.1 mmol scale` printed; volume and the standard electrolyte equiv are not (footnotes give 1 equiv and 5 equiv only as deviations) |
| 29 | BASF US 5,507,922 — **no text layer**, 5 characters extracted. Needs OCR. |
| 37 | anethole concentration (electrolyte anchored) |
| 38 | substrate concentration |
| 49 | all three (solvent HFIP anchored) |

## Rows needing an author decision

- **Row 21** — `40.0 wt% AN` is confirmed, but the conversion to **6.85 M** requires a solution
  density that is nowhere stated. Volume-additive mixing of run 28 (94.5 g AN + 141 g of 56 wt%
  aq Et4NOTs) gives ≈7.2 M; 6.85 M implies ρ = 0.908 g mL⁻¹. State the density and its source, or
  carry the row as state B with the arithmetic shown.
- **Row 2 carrier identity** — Shono 1975 compound 12 is an **N-carbomethoxy** pyrrolidine; the row
  names `N-Boc-pyrrolidine`. Same n, near-identical D, but the name should match the paper.
- **Row 30** — declared `by analogy` in the exemplar column, so it is state C by construction and
  should be labelled as such wherever the row is counted.


## What changed in the files

`data/build_reactions50.py` (backup `.bak_conditionAudit`), rebuilt to `data/reactions_50.csv`
(backup `.bak_conditionAudit`). Ten rows moved and **only** those ten — verified by diffing the
rebuilt table against the backup field by field:

| row | change |
|---|---|
| 3 | exemplar → ChemSusChem 2021; solvent MeOH → THF/MeOH 5:1 (μ 0.544 → 0.480, D +21%) |
| 19 | solvent MeOH → EtOH/MeOH 1:1 (μ 0.544 → 0.719, D −24%) |
| 24 | exemplar → Hayashi/Baran JACS **2022** (first author, and the year) |
| 25 | exemplar → Yang/**Lei** (Wang is a middle author) |
| 31 | propylene → **ethylene**; carrier 2.0 → **1.0 M**; `2 M NaCl aq` → **`1 M KCl aq`** |
| 32 | Ruecker → **Rücker** |
| 33 | Bottecchia/**Merck** → Bottecchia/**Strotman** (Merck is the employer, not the last author) |
| 43 | exemplar year touched and then **reverted** — OL 2018 was correct (see D3) |
| 45 | carrier 0.25 → **0.152 M**, substrate 0.12 → **0.121 M**, solvent string → the Fig 5b medium |
| 46 | electrolyte `0.0625 M LiClO4/MeOH` → **`0.0625 M TsOH/MeOH`** |

`julia/run_mediated.jl` (backup `.bak_conditionAudit`) additionally: bromination
`250./120.` → `152./121.`; chloride `2000.` Na⁺ → `1000.` **K⁺** (D 1.33e-9 → 1.96e-9, a 47% more
mobile counter-ion, so not a cosmetic relabel) and renamed to ethylene.

### The most serious defect this audit exposed: the mediated solver ignored the fix

After correcting the bromination row in `reactions_50.csv` (Br⁻ 0.25 → 0.152 M) and regenerating
`julia/reactions_table.jl` — which updated correctly to `152.0` — I re-ran the mediated EC′ matrix.
It completed cleanly, all 48 cells converged, no walls, exit 0. **And it reported the old ceiling.**

`run_mediated.jl` never loaded `reactions_table.jl` at all. Every mediated row's carrier and
substrate concentration was **duplicated by hand** inside its `MedSpec`, and the bromination entry
still read `250.` and `120.`. A clean run with a fresh timestamp produced a stale number and
nothing anywhere complained. This is the same failure mode as a silent Tier-0 fallback, and it is
worse than the condition defects themselves, because it means *any* correction to the audited CSV
could fail to reach the physics without leaving a trace.

Fixed by **G-MEDSYNC** (`julia/run_mediated.jl`): the file now includes `reactions_table.jl` and
asserts, for all 8 mediated rows, that its own `C_med`/`C_S` agree with the audited table, erroring
out with both values named if they do not. Tolerance is 1% relative floored at 0.06 mol m⁻³, which
absorbs the table's one-decimal rounding (5.67 → 5.7) while still failing on real drift.

Negative-controlled: restoring the old `250.` makes it error with
`run_mediated.jl has 250.0 mol/m^3, the audited table has 152.0 mol/m^3`. It caught a second, benign
mismatch on first run (the 5.67/5.7 rounding), which is how the tolerance got set.

### A second latent defect this audit exposed

`build_reactions50.py` read conductivity as `ELECTROLYTES.get(elec, np.nan)`. Changing five
electrolyte strings **silently blanked κ on five rows and nothing complained** — the same class of
failure as the Tier-0 fallback that `build_merged_matrix.py` used to substitute for a failed EC′
solve. It is now a hard stop (`_kappa`), and the stop is negative-controlled: asking for a
nonexistent electrolyte raises rather than returning NaN.

### Five κ values are ESTIMATES and are labelled as such

The five changed electrolytes have no measured conductivity here. Each is derived from an anchor
already in the table, the derivation is written out in `KAPPA_ESTIMATED`, and **the build prints
them as a banner on every run** so they cannot be mistaken for sourced numbers:

| electrolyte | κ (mS/cm) | derived from |
|---|---|---|
| 0.033 M Et₄NPF₆/THF-MeOH 5:1 | 0.35 | bracketed by the MEASURED 0.1 M Bu₄NPF₆/THF (0.5063) and 0.033 M Et₄NPF₆/MeOH (3.0); bracket is wide — the weakest κ in the table |
| 0.04 M NaBr/EtOH-MeOH 1:1 | 1.8 | Walden from 0.04 M NaBr/MeOH = 2.5 × 0.544/0.719 |
| 1 M KCl aq | 111.3 | textbook, but **not yet page-anchored here** — needs a dossier row |
| 0.152 M NaBr/H₂O-MeCN-MeOH-DCM | 19.0 | from 0.5 M NaBr aq/MeCN 1:1 = 40.0, linear in c, ×0.8 for the medium |
| 0.0625 M TsOH/MeOH | 7.5 | Λ°(HCl/MeOH)≈192, TsO⁻ bulkier ≈160, attenuation 0.75 — **~2× the LiClO₄ value it replaces** |

Two new solvent mixtures (`THF/MeOH`, `EtOH/MeOH`) were added on the same Perkins–Geankoplis
φ·M convention as the existing mixtures; their viscosities are mole-fraction log-mix **estimates**,
defensible because both are organic–organic and so, unlike the water/alcohol entries, do not sit
near a viscosity maximum.

## Still open

1. **Table S6's numbers must be regenerated into the SI text** from the corrected re-solve
   (labels are already updated). See the re-solve result below.
2. **Row 31's substrate is unresolved.** Needs a source reporting ethylene solubility in KCl
   directly — the salting-out paper on hand measures argon in KCl and ethylene only in NaCl.
3. **Row 46's carrier basis** — sulfinate 0.125 M (the discharged species) vs styrene 0.0625 M
   (the limiting reagent the row uses). Author decision.
4. **Eleven rows are state C, not state A** (§ "NOT PAGE-ANCHORABLE"). Anywhere the manuscript
   counts these rows, the count is over a mixed-provenance set.
5. **`5507922.pdf` still has no text layer** — the Lysmeral row cannot be checked without OCR.
6. Five κ dossier rows, per the table above.


## The re-solve, after G-MEDSYNC

48/48 cells converged. No newton-walls, no unresolved cells, no lost branches. G-MEDSYNC and the
`Σz·s = 1` / `Σz·ν = 0` / bulk-electroneutrality invariants all pass.

**Br⁻ / electrophilic bromination** (0.25 → 0.152 M Br⁻, 0.12 → 0.121 M arene):

| architecture | i_EC before | after | Δ |
|---|---|---|---|
| Rotating cylinder 3000 rpm | 745.5 | 480.6 | −36% |
| RDE 1600 rpm | 702.0 | 452.6 | −36% |
| Thin-gap microflow | 320.4 | 206.7 | −35% |
| Parallel-plate flow | 127.0 | 82.0 | −35% |
| Stirred batch | 106.0 | 71.3 | −33% |
| Unstirred batch | 16.4 | 14.3 | −13% |

**Cl⁻ / ethylene epoxidation** (2 M NaCl/Na⁺ → 1 M KCl/K⁺): every architecture exactly **−50%**,
tracking the halved carrier — 5477 → 2740, 5093 → 2550, 2301 → 1153, 914 → 458, 788 → 395,
263 → 132 mA cm⁻². Amplification is unchanged at **×2.01**, which is the correct physics: for a 1:1
binary salt whose anion is the reactant, the migration enhancement is exactly 2 regardless of the
counter-ion's mobility, so swapping Na⁺ (D = 1.33e-9) for K⁺ (1.96e-9) must not move it. It didn't.

**No cell crosses 25 mA cm⁻² in either direction, so no manuscript count changes.** The bromination
cells were all far above 25 except unstirred, which was far below it before (16.4) and after (14.3);
every chloride cell stays far above.

### A claim in ONE_PHYSICS_20260823.md had to be withdrawn

That document states that Br⁻ × unstirred *requires* k-continuation, having defeated the ramp,
c-control, δ-continuation and four mesh refinements. On the corrected same-experiment
concentrations **the cell no longer needs k-continuation** — it solves on the ordinary c-control
path. The k-continuation result was real, but it was a fact about a mixed-experiment
parameterisation, not about the physics. Corrected in place, with the original text kept and the
update appended rather than overwritten.

---

# Part 2 — the SI pass (same day)

Ten SIs plus IUPAC SDS-57 were retrieved, extracted (`results/sitext/`), and read. **Every one
resolved its row.** The BASF patent was OCR'd. Nothing from Part 1's "NOT PAGE-ANCHORABLE" list
remains unresolved.

## Confirmed exactly as modelled

| row | quote |
|---|---|
| 6 | `aromatic compound (0.20 mmol) and pyridine (0.5 mL) in 0.3 M Bu4NBF4/CH3CN (10.0 mL)` |
| 14 | `phenol component (0.005 mol), arene component (0.015 mol) and ...(0.68 g, 0.003 mol) in ...(27 mL) and methanol (6 mL)` → 0.1515 / 0.0909 M |
| 16 | `HCl(aq) (pH = 2, 10 mL), MeCN (5 mL)` with 1.19 mmol alkene / 1.43 mmol iPrI → 0.079 / 0.095 M |
| 37 | `styrene (80 mM, 1 equiv.)`; `trans-anethole 1 (237 mg, 1.60 mmol) ... lithium perchlorate (2.13 g) and nitromethane (20 mL)` → 0.080 / 1.00 M |
| 49 | 0.2 mmol in an undivided **5 mL** cell; `19.3 mg tetrabutylammonium hexafluorophosphate` / 387.43 = 0.00996 M — the unusually dilute support is real |

## Corrected

| row | was | now | source |
|---|---|---|---|
| 13 | NaI 0.2 M | **0.171 M** | row took substrate on 3.5 mL (DMF + retained DCM; Fig 2a "No solvent exchange") and electrolyte on 3.0 mL — two bases in one row. Fixed on the physical volume. |
| 22 | 0.18 M | **0.141 M** | `tert-butyldimethyl(p-tolyloxy)silane (10.0 g, 45.0 mmol) ... and LiBr solution (320 mL)`. Added solids only raise V, so 0.141 is itself an upper bound. LiBr 3.0 M confirmed. |
| 24 | 0.04 M / 0.08 M | **0.0333 M / 0.0833 M** | `(15 mg, 0.1 mmol), tetramethylammonium tetrafluoroborate (40 mg, 0.25 mmol) and pivalic acid (31 mg, 0.3 mmol) in 3.0 mL of MeOH` — 2.5 equiv, not 2 |
| 38 | 0.11 / 0.022 M | **0.118 / 0.0235 M** | `85 mL containing 0.1 M TBAP` + `10 mmol olefin, 20 mol% benzoquinone`. **No SI exists or is needed** — fully in the article body. |

## Row 11 — relabelled, not renumbered

The row was `Kolbe homocoupling of hexanoate` at 1.0 M with `Me4NOH 15 mol% + Me4NBF4 5 mol%`.
Plain hexanoic acid is **not a substrate anywhere in that paper** (the only C6 acid is
6-(Boc-amino)hexanoic acid, General Procedure A, 1.5 mmol). The three concentrations match the
10-undecenoic acid scale-up exactly: `acetone (200 mL), 10-undecenoic acid (36.8 g, 200 mmol),
pivalic acid (4.0 g, 40 mmol), Me4N·BF4 (1.6 g, 10 mmol), and Me4N·OH pentahydrate (5.4 g,
30 mmol)` → 1.00 M / 0.05 M (5 mol%) / 0.15 M (15 mol%).

So the **label** was wrong, not the data. The row is now `Kolbe homocoupling of 10-undecenoate`
and **no concentration changed** — only `D`, recomputed for C11 rather than C6, which is the
number that was actually wrong. The alternative (bind to General Procedure A: 0.43 M, 10 mol%, no
Me4NBF4) would have replaced three anchored numbers with three others and still required choosing
a substrate. Pivalic acid at 0.2 M (20 mol%) is a co-acid and is not modelled.

The electrolyte key was renamed `Me4NOH 15 mol% + Me4NBF4 5 mol%` → `0.15 M Me4NOH + 0.05 M
Me4NBF4`. Same numbers; the mol% form hid what it was mol% *of*. **This closes one of the three
unresolved electrolyte definitions flagged in `ONE_PHYSICS_20260823.md`.**

## Row 31 is now STATE A — measured

`SDS-57` carries the primary data. **Ethene in 1.000 M KCl = 3.52 mmol L⁻¹** at 298.15 K,
101.3 kPa — IUPAC Solubility Data Series Vol. 57 (ethene, comp. C. L. Young), original measurement
**Yano, T.; Suetaka, T.; Umehara, T.; Horiuchi, A., *Kagaku Kogaku* 1974, 38, 320–323**. The KCl
series reads 0.500/1.000/1.500 M → 4.14/3.52/3.03 mmol L⁻¹ against 4.83 in pure water.

Cross-checked twice inside the same volume: the compilation's own Sechenov slope is
−0.136 ± 0.001 L mol⁻¹, and log₁₀(4.83/3.52) = 0.1374; and the series is monotonic across KBr, KCl
and CuCl₂. The salting-out correction is **−27%**, applied, not flagged.

*A near-miss worth recording:* the volume contains **two** Yano tables. The first string match is
the HCl/HNO₃/H₂SO₄ series and parsing it yields nonsense (`log(0/0)`). The correct block is keyed
on `Potassiumbromide,potassiumchlorideorcopperchloride`. Parsing the numbers positionally and
checking the Setschenow slope is what caught it.

## Row 29 — the patent, OCR'd

`5507922.pdf` had no text layer (5 characters). Rendered at 300 dpi with PyMuPDF, OCR'd with
tesseract 5.5.2 → **24 kB**. The worked example:

> `450 g (15% by weight) of p-tert-butyltoluene` / `10 g (0.3% by weight) of sulfuric acid` /
> `2,450 g (84.7% by weight) of methanol`, graphite 1 mm apart, 3.4 A dm⁻² (34 mA cm⁻²),
> 7.5 F mol⁻¹, 55 °C, 900 L h⁻¹.

450 g / 148.25 = 3.035 mol in ≈3.65 L = **0.83 M** against the row's 0.81 M (3%). The 0.3 wt%
H₂SO₄/MeOH is now verbatim. This was the last completely unverified row.

## Final state of the pipeline

`build_reactions50 → run_tier0 → run_mediated → run_all50_np → build_merged_matrix`, all green.
G-MEDSYNC passes; `Σz·s = 1`, `Σz·ν = 0` and bulk electroneutrality pass; 48/48 mediated cells and
all 300 NP cells converge with **no newton-walls, no unresolved cells, no lost branches**.

G-MEDSYNC earned itself twice more this pass, blocking the solver until the ethylene (4.67 → 3.52)
and BQ (22 → 23.5) values were synced from the audited table.

### Counts moved — v40 text change required

| architecture | ≥25 before → after | ≥50 before → after |
|---|---|---|
| **natural** | **12 → 11** | 9 → 9 |
| stirred | 17 → 17 | 14 → 14 |
| **flow** | **21 → 20** | 14 → 14 |
| thingap | 31 → 31 | 24 → 24 |
| rde | 36 → 36 | 32 → 32 |
| **rce** | 36 → 36 | **34 → 33** |

Only two rows crossed 25 mA cm⁻², both downward:

- **Br⁻ bromination × unstirred: 36.8 → 14.3** — the mixed-experiment fix (Fig 4 carrier paired
  with Fig 5b substrate).
- **rAP imide × flow: 29.6 → 24.6** — the substrate correction 0.04 → 0.0333 M. **This is
  knife-edge**: 24.6 against a 25 threshold is a 1.6% margin, far inside the uncertainty of its own
  inputs. The flow count of 20/50 should not be presented as robust without saying so.

**v39 carries 12/50 and 9/50. The 9/50 still holds; the 12/50 is now 11/50.**
