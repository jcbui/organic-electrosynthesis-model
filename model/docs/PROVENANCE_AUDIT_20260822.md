# Full provenance audit — every D, C, μ, ρ and κ in the model

**Run:** 2026-08-22, after the KHL reclassification and the two multicomponent-coupling swaps.
**Bar applied:** *directly verifiable in a paper that can be cited and referred to in the table
where the parameter appears* — i.e. state **A** (measured, with a page locator) under
`docs/PROVENANCE_STANDARD.md`.

Reproduce the census: `cd data && python audit_numeric.py` (0 FAIL, 4 known WARNs) and the
per-category counts printed by `python build_param_tables.py`.

---

## The headline

**64 of 271 registry rows (24%) clear the bar.** Another 86 (32%) are state-B derivations from
named methods, and 121 (45%) are assumptions carrying a sensitivity but no source.

Every row carries a *citation string*; only **122 of 271 (45%) carry a page locator**. That gap
is the honest measure of how much of the registry a reviewer could actually check by opening the
cited work at a stated page.

Both schema gates hold: every `measured` row has a locator, every `assumption` row has a
sensitivity. Those are asserted at build time and cannot silently regress.

| category | n | measured | derived | assumption | with locator |
|---|---|---|---|---|---|
| 1. Physical constants | 4 | 1 | 2 | 1 | 1 |
| 2. Solvents (μ, ρ, M, φ) | 100 | 34 | 48 | 18 | 50 |
| 3. Estimation methods | 21 | 18 | 2 | 1 | 20 |
| 4. Solver species diffusivities | 29 | 1 | 11 | 17 | 10 |
| 5. Concentrations | 4 | 2 | 1 | 1 | 3 |
| **6. Electrolyte conductivities** | **49** | **0** | **7** | **42** | **14** |
| 7. Reactors | 11 | 4 | 1 | 6 | 6 |
| 8. Voltage stack | 3 | 0 | 1 | 2 | 1 |
| 9. Thermal model | 42 | 4 | 13 | 25 | 16 |
| 10. Homogeneous kinetics | 1 | 0 | 0 | 1 | 1 |
| 11. Numerics | 7 | 0 | 0 | 7 | 0 |
| **TOTAL** | **271** | **64** | **86** | **121** | **122** |

---

## 1. Diffusion coefficients — 0 of 50 measured, but the derivation chain is verified

Every per-reaction D in Table S2 is a **correlation estimate**, not a measurement:

| method | rows | inputs and their state |
|---|---|---|
| Wilke-Chang + Le Bas volume | 34 | correlation **measured/cited**; increments **measured/cited** |
| Stokes-Einstein | 11 | **radius r = 4–5 Å is an ASSUMPTION, typed in per row** |
| Nernst-Einstein from λ⁰ | 5 | λ⁰ tables cited (CRC Sect. 5 Vanysek / Izutsu) |

**The chain is defensible, and that is now demonstrated rather than asserted.** Three separate
things had to hold, and all three were checked in this pass:

1. **The correlation and its constants.** `D = 7.4e-8·(φM)^0.5·T/(μ V^0.6)` is cited to Wilke &
   Chang, *AIChE J.* 1955, **1**, 264–270, pp. 264–270, with that paper's four recommended
   association parameters — φ = 2.6 water, 1.9 methanol, 1.5 ethanol, 1.0 unassociated. The φ
   values in `solvents.csv` match those exactly for all eleven pure solvents.
2. **Every Le Bas increment** is a `measured` registry row cited to Table 11-1 (Le Bas additive
   atomic volumes): C 14.8, H 3.7, O 7.4, O(acid) 12.0, N 15.6/10.5/12.0, S 25.6, F 8.7, Cl 24.6,
   Br 27.0, I 37.0, P 27.0, ring corrections −6.0/−8.5/−11.5/−15.0.
3. **The assembly of those increments** — the part a citation cannot vouch for. A new gate,
   **G-LEBAS** in `build_reactions50.py`, asserts the computed volumes against the published
   additive values for ten reference compounds and fails above 3%:

   ```
   Le Bas closure: 10/10 reference compounds within 3%, worst 1.7%
   ```

   benzene, toluene, methanol, ethanol, acetone, acetic acid, naphthalene, n-hexane exact;
   chlorobenzene +1.7%, diethyl ether −1.1% (published-table rounding, not implementation error).
   Negative-controlled: perturbing the carbon increment 14.8 → 15.6 fires it on benzene at +5.0%.

**So the 34 Wilke-Chang rows are sound**: right correlation, right constants for the right
compounds, correctly assembled. What remains is the correlation's intrinsic accuracy, which the
registry already states honestly — canonical ±10–20% for typical organics, and the model's one
measured anchor (ferrocene in MeCN: predicted 1.82e-5 vs measured ≈2.4e-5) is **−24%**. Since
i_lim ∝ D, no *absolute* ceiling here is better than roughly ±25%; ratios between architectures
cancel the common factor, so the rankings are unaffected.

> **The real soft spot is not Wilke-Chang — it is the 11 Stokes-Einstein rows.** Their hydrodynamic
> radius (4–5 Å) is a registry `assumption`, chosen rather than derived from structure. D ∝ 1/r,
> so the 4.0–5.0 Å spread alone is a 25% band on those rows before any correlation error. If any
> diffusivity work is done next, converting these 11 to Wilke-Chang (they have structures; the Le
> Bas path is now gated) would remove the last typed-in number from the D column.

**Registry category 4** (29 solver-species diffusivities) is 1 measured / 11 derived / 17
assumption, 10 of 29 locator-anchored. These set migration and film potential in the Tier-1 solve;
they do not set any reported i_lim, which is carried by the Table S2 carrier D.

## 2. Bulk concentrations — **48 of 50 clear the bar**

This is the strongest part of the model. 48 rows are `exemplar-verified`: the primary article's
stated amounts and solvent volumes, converted by explicit mmol/mL arithmetic, with the page,
table, figure or SI anchor quoted in the provenance string. 46 quote an explicit page/table/SI
anchor.

Two do not, and both are declared:

- **Shono α-methoxylation of amides** — 1.56 M transferred *by analogy* from the page-verified
  carbamate protocol (Shono, *JACS* 1975, Experimental p. 4267). No amide-methoxylation exemplar
  PDF was supplied.
- **Cl-mediated propylene epoxidation** — an ex-cell mediation case. The electrode current is
  carried by 2 M Cl⁻ (chlor-alkali, verified), but the substrate concentration is a Henry's-law
  saturation estimate (C_sat ≈ 5 mM, Sander, *ACP* 2015), not a reported bulk concentration.

> **Finding — SI off by one.** §S1.2 states "Forty-nine of the fifty rows are so verified". The
> literal count of `exemplar-verified` rows is **forty-eight**. The epoxidation row was being
> counted as verified on the strength of its electrolyte, while its substrate concentration is an
> estimate. This should be corrected to forty-eight, with the epoxidation row named alongside the
> Shono transfer.

The two rows added in this pass are both exemplar-verified against **open-access** primary
articles, retrieved in full text:

- Yang, Guan, Peng et al., *Nat. Commun.* 2023, **14**, 1476 (PMC10020561) — thiol 0.5 mmol
  limiting, diazo 2.0 mmol, alcohol 0.5 mL, Et₄NBF₄ 0.5 mmol, MeCN 6 mL.
- Chien, Breitschaft, Kelm, Waldvogel & Manolikakes, *ChemSusChem* 2025, **18**, e202500186
  (PMC12175053) — cinnamic acid 0.1 M in MeCN, SO₂ 10 equiv, alcohol 3 equiv, nBu₄NPF₆ 0.1 M.

## 3. Viscosities — 11 of 11 pure solvents clear the bar; the 7 mixtures do not

> **CORRECTION to the first issue of this audit.** It reported that "eight solvent viscosities and
> the matching densities are carried as `measured` on a bare `CRC` string" and called adding an
> edition and table the cheapest available win. **That was wrong about the registry.** All 34
> `measured` category-2 rows already carried full locators — 97th ed. (Haynes, 2016), *Sect. 6
> 'Viscosity of Liquids' pp. 6-243 to 6-247 (25 °C column)* for μ and *Sect. 15 'Laboratory
> Solvents and Other Liquid Reagents' pp. 15-13 to 15-20* for ρ. The bare `CRC` string existed only
> in the `src` column of the compact working file `data/solvents.csv`, not in the provenance
> registry. The audit conflated the two files.

**Fixed anyway, because the working file should not read as less sourced than it is.** The `src`
field of `solvents.csv` now mirrors the registry locator verbatim in substance, so the two cannot
be read as disagreeing:

| solvents | μ and ρ source, as now recorded in both files |
|---|---|
| MeCN, MeOH, EtOH, DMF, DMA, DMSO, THF, AcOH, acetone, MeNO₂ | CRC 97th ed. 2016 (Haynes), Sect. 6 pp. 6-243..6-247 (μ, 25 °C); Sect. 15 pp. 15-13..15-20 (ρ) |
| H₂O | **not CRC** — IAPWS reference correlations: Huber et al., *JPCRD* 2009, **38**, 101–125 (μ); Wagner & Pruss, ibid. 2002, **31**, 387–535 (ρ, IAPWS-95) |
| HFIP | **UNSOURCED.** Registry class `assumption`, citation literally "-- (no source supports this value)". μ = 1.65 mPa s, ρ = 1.596 are carried without provenance. |
| 7 mixtures (MeCN/H₂O, MeOH/H₂O, DMSO/THF, tAmOH/H₂O, AcOH/HCOOH, H₂O/MeCN, …) | mixing-rule estimates (Perkins-Geankoplis), or flatly `est.` — **and they have no registry rows at all** |

**Two real gaps remain, and they are not the one the first issue named:**

1. **HFIP has no source for either μ or ρ**, and it is used by a reaction row.
2. **The seven mixed solvents are invisible to the registry.** They are used by reaction rows, they
   carry estimated properties, and no `parameters_provenance.csv` row exists for them — so they
   are not counted in any census, carry no sensitivity, and cannot be audited by the schema gates.
   This is a registration gap, not a sourcing gap, and it is the largest structural hole found.

μ enters twice — i_lim ∝ D ∝ 1/μ and Sc = ν/μ·ρ — so the registry's ±25% property-error
sensitivity displaces log₁₀ i_lim by ±0.10.

## 4. Densities — same source problem, much lower stakes

21 registry rows, 11 measured / 0 derived / 10 assumption, 11 locator-anchored. ρ enters **only**
through ν = μ/ρ and the Schmidt number, and Sh ∝ Sc^0.356 at the rotating cylinder, so a 5%
density error moves k_m by 1.8%. This is the one parameter class where the sourcing gap does not
matter much, and the registry says so.

## 5. Electrolyte conductivities — 0 of 49 measured. Here is exactly how each one is obtained.

This is the weakest category in the model and the one worth being most explicit about.
**0 measured / 7 derived / 42 assumption**; 14 of 49 locator-anchored. Of the 50 reaction rows,
**43 use an assumption-class κ** and 7 a derived one.

### The 7 derived — two routes, both named and reproducible

**Route A — Casteel-Amis, 5 rows (all Bu₄NBF₄/MeCN).** Casteel & Amis, *J. Chem. Eng. Data* 1972,
**17**, 55 give a closed-form κ(m) shape function. Dorn, Kareth, Weidner & Petermann, *J. Chem.
Eng. Data* 2024, **69**, 1493–1502, **Table 3, p. 1499** publish a *measured* fit of that function
for ACN/(C₄H₉)₄NBF₄: κ_max = 33.40 mS cm⁻¹, m̄_max = 1.48127, a = 0.78646, b = −0.02156, valid to
9.10 mol kg⁻¹, MAPE 1.65%. Evaluating it at 0.043 / 0.077 / 0.10 / 0.25 / 0.30 M gives
5.2 / 8.1 / 9.9 / 18.9 / 21.3 mS cm⁻¹. Independently validated at 1 M against Gong et al., *EES*
2015, **8**, 3515–3530, Table 3 p. 3519: 32.75 derived vs 32.3 tabulated, **+1.4%**.

**Route B — CRC concentrative-properties interpolation, 2 rows** (2 M NaCl aq, 1 M Na₂CO₃ aq;
1 M NaOH aq uses the same route and is registered under the thermal category). CRC *'Electrical
Conductivity of Aqueous Solutions'* p. 5-71 tabulates κ against mass %, at 20 °C. CRC
*'Concentrative Properties of Aqueous Solutions'* converts the molarity to mass % for that salt.
Interpolate p. 5-71 at that mass %, then correct 20 → 25 °C at the tabulated α ≈ 1.9–2.2 % K⁻¹.
For NaCl: 2.000 M = 10.846 mass %, giving 133.6–134.4 at 20 °C → 146–150 at 25 °C; cross-checked
against the Foxboro 1999 conductivity guide's 25 °C NaCl column (147–149). Registry carries 148.

> Note that route B **corrected two inherited numbers rather than confirming them**: NaCl had been
> 160 (+8%) and a working note said 158 (+7%). Reconciling those two against each other would have
> converged on the wrong value. The primary pull that would settle it — Chambers, Stokes & Stokes,
> *J. Phys. Chem.* 1956, **60**, 985–986 — was **not** retrieved and must not be cited.

### The 42 assumptions — what they actually are

They are **engineering values with no source**, each carrying a sensitivity. Eight of them carry a
state-B **ceiling** derived by Kohlrausch additivity from limiting molar conductivities (Gong et
al., *EES* 2015, Table 2, p. 3518: Li⁺ 69.97, ClO₄⁻ 103.6, Et₄N⁺ 85.1, PF₆⁻ 102.8 S cm² mol⁻¹).
A ceiling is not a value: converting Λ⁰ to κ at a working concentration needs Λ/Λ⁰, and the only
route available was to transfer the attenuation ratio measured for a *different* salt. **That
transfer is refused** — it is exactly what state C exists to prevent — so those rows keep their
tabled value and gain only a bound.

The remaining 34 have neither a measurement nor a ceiling, usually for one of three reasons:
mixed solvents (no Λ⁰ table applies), HFIP (ε = 16.7, no Λ⁰ table exists at all), or a salt/solvent
pair for which no conductance study was located.

**The only state-A conductivity anywhere in this model** is `0.1 M Bu4NPF6/THF` = 0.506 mS cm⁻¹
(Zhang, Gu, Wang, Ware, Lu, Lin, Qi & See, *JACS Au* 2023, **3**(8), 2280–2290, **Table 1**,
506.3 µS cm⁻¹ at 22 ± 1 °C, Metrohm 912 conductometer; open access, PMC10466324) — and it is
`unused-legacy`, consumed by nothing. I re-checked that paper's Table 1 in this pass hoping it
also covered MeCN; **it does not** — every entry is THF-based.

### The two added in this pass

Both state C, both carried at the *derived* Bu₄NBF₄/MeCN value at matched concentration, with the
direction of the error stated:

- `0.077 M Et4NBF4/MeCN` = 8.1 — a **lower bound**. Et₄N⁺ is the more conductive cation of the pair
  (Gong Table 2), so true κ ≥ 8.1. This is the **conservative** direction for the thermal analysis:
  lower κ → more Joule heat → lower boil-off ceiling. Dorn Table 3 *does* contain the measured fit
  for ACN/(C₂H₅)₄NBF₄ that would make this derived — the ACS article is paywalled and was not
  retrieved.
- `0.1 M Bu4NPF6/MeCN` = 9.9 — the anion swap is the assumption. PF₆⁻ is the *less* conductive
  anion, so this is a mild **over**-estimate and this row's thermal ceiling is correspondingly
  optimistic. No measured κ for Bu₄NPF₆/MeCN at any concentration was located.

### The exposure is bounded, and the bounds are now computable

The first issue of this audit left the impression that 42 unsourced conductivities sit under the
thermal analysis unchecked. That is not what is there, and the correction matters.

**Only two assumption-class conductivities reach Fig. K at all**: 3.0 M LiBr/THF and 0.2 M NaI/DMF.
The other two Fig. K electrolytes are derived. For both assumptions the registry already carried a
quantitative sensitivity — a band, a critical κ, and the named conclusion that turns on it. Those
numbers were **typed prose that nothing recomputed**. They are now recomputed, and they are right:

| claim | registry says | recomputed | |
|---|---|---|---|
| THF beaker i_boil crosses 50 mA cm⁻² at κ = | 8.78 mS cm⁻¹ | 8.78 | ✓ |
| DMF T_ss(100 mA cm⁻²) crosses 153 °C at κ = | 11.15 mS cm⁻¹ | 11.15 | ✓ |
| DMF T_ss at the carried κ | 202 °C | 202.1 | ✓ |
| DMF E_cell at 50 mA cm⁻² | 14.9 V | 14.90 | ✓ |
| DMF E_cell stays in 10–20 V over κ = | 5.68–13.16 mS cm⁻¹ | 5.68–13.16 | ✓ |

**What the sweep establishes.** `figs/analysis_kappa_value_sensitivity.py` sweeps each assumption
across its defensible band and tests the manuscript's own claim for that solvent:

- **THF — the headline Fig. 5 claim is robust.** Across the entire band 0.206–6.6 mS cm⁻¹ the
  unstirred-beaker ceiling runs 7.8–43.5 mA cm⁻², always below the 50 mA cm⁻² barrier. Breaking
  "THF boils below the operating barrier" needs κ **2.9× higher** than carried, which is above the
  band ceiling. The claim survives its own uncertainty.
- **DMF — holds with a stated margin.** The claim is the opposite direction (DMF clears the barrier
  at ≈85 mA cm⁻²) and it holds down to κ = 2.75 mS cm⁻¹, i.e. it needs a **2.9× overestimate** to
  break. It fails only at the very bottom of the band, and that floor is an unsourced
  3×-below-carried placeholder rather than a measurement.

**Both live DMF claims are already qualified in the SI**, contrary to what the registry note asked
for as an outstanding action. §S6 states: *"Both of those statements are conditional on the adopted
κ and must be quoted with the condition, because that κ is a declared assumption whose honest band
is 4–16 mS cm⁻¹."* That was verified in this pass, not assumed.

**New gate: G-KAPPA.** The six values above are recomputed from the shared `thermal_model.py` on
every run and fail on >1% drift, so the registry's sensitivity prose can no longer silently
separate from the physics it describes. Negative-controlled: perturbing the beaker gap 2.0 → 2.2 cm
fires all six.

**What genuinely remains open** is narrower than "42 unsourced values": no measured κ exists for
LiBr/THF above 5×10⁻² M, or for NaI/DMF at working concentration, anywhere that was located. The
conclusions that rest on them are bounded and survive with a 2.9× margin — but the numbers
themselves are still assumptions, and the withdrawn 500 mA cm⁻² DMF microfluidic pass (1.078×
margin) stays withdrawn.

### Why the category can be this weak without invalidating the model

κ appears in **no transport quantity**. i_lim (Eq. S1) and the NPP / EC′ solvers use D, C, δ and z
only. κ enters solely the voltage and thermal path (`cellvoltage.jl`; Figs D, K, 4B, main panel f).
45 of the 49 registered conductivities are display-only and support no stated conclusion. The
exposure is concentrated in the handful driving Fig. 5, and `KAPPA_SOURCING_DOSSIER.md` §4.1
already names `0.2 M NaI/DMF` as the single most exposed number in the model.

## Round 2 — closing the gaps a reviewer would actually attack

The first pass measured the gap. This one closes what can be closed and **bounds what cannot**,
because for D and kappa no measurement exists to close it with. Three new gates, and three
corrections to this audit's own earlier claims.

### Corrections to this audit

1. **"CRC is not a locator"** — withdrawn. All 34 measured solvent rows already carried
   97th ed. + section + table + page range. I had conflated the registry with `solvents.csv`.
2. **"The 7 mixed solvents have no registry rows at all"** — **wrong**. They have 52. My query
   searched for `MeCN/H2O:` while the registry names them `MeCN/H2O 9:1 v/v:`. A string-matching
   artifact, the third in this audit.
3. **The DMF kappa claim** was initially scored against "boils below the barrier", which the paper
   never asserts for DMF. Each solvent is now tested against its own claim direction.

That is three self-inflicted errors in one audit, every one of which passed the gates at the time.
It is the clearest available evidence that green gates measure consistency, not correctness.

### G-CATD — the dilute-catalyst conclusion does not rest on the typed radius

Eleven rows take D from Stokes-Einstein with r = 4.0-5.0 A **typed in**. Neither alternative works
for this class: Le Bas has no transition-metal increment, and RDKit cannot embed a coordination
complex, so no computed volume is available. Both were tried.

What settles it is that i_lim ~ 1/r exactly, so the published "10 of 11 clear 25 mA cm-2 in none"
is a step function of the radius alone:

- Inverting Stokes-Einstein on ferrocene's measured D in MeCN (2.4e-5 cm2/s) gives **r = 2.65 A**
  for a neutral metallocene of MW 186. Mass-scaling (r ~ M^(1/3)) to this set's 325-570 range
  predicts **3.2-3.7 A**.
- The conclusion breaks only if the deciding complex's radius is **2.91 A** — a **1.26x** margin
  against its 3.66 A mass-scaled expectation.
- **The typed radii are LARGER than the scaled expectation**, so the model already understates
  catalyst D and states the result conservatively. Charge and solvation push the same way.

### G-SOLV — the threshold counts are +/-2 of 50, and the SI now says so

Eleven rows run on a solvent whose mu and rho are not page-anchored (HFIP; nine mixed-solvent
rows). i_lim ~ 1/mu exactly, so this is again a direct sweep.

**This one found a real problem.** The counts are threshold crossings, not ratios, and they move:
a +/-25-50% viscosity error confined to those eleven rows shifts each architecture count by up to
**2 of 50** (11-17-21-31-36-36 spans 9-11 / 16-18 / 19-21 / 30-32 / 36-37 / 36), and the
substrate-carried count from 28/31 to 29/31. My earlier "the rankings are ratios so the errors
cancel" was right about the rankings and **wrong about the counts**.

What does not move is the ordering: unstirred < stirred < flow < thin-gap holds at every point.
`make_si.js` now states the counts as **+/-2 of 50 rather than exact integers**, with the ordering
named as what the conclusions actually rest on.

### G-KAPPA — the registry's kappa sensitivity prose is now reproducible

Six quantitative claims (critical kappa for the THF boil-off crossing, DMF T_ss, DMF E_cell and its
10-20 V window) were typed into `build_param_tables.py` and recomputed by nothing. All six now
recompute from `thermal_model.py` to under 0.1%, and both live DMF sentences were confirmed already
qualified in SI S6 -- verified, not assumed.

### One real sourcing win

`Ansari & Singh, Res. J. Chem. Sci. 2022, 12(1), 67-69, Table-1 p. 68` (open access, retrieved in
full) measures acetonitrile-water density and viscosity at 25 C over 10-70 wt% plus pure AN. Its
pure-component values reproduce the CRC MeCN entries to 0.3% and 0.9%, which is the quality check
on a low-impact source.

- **H2O/MeCN 2:1 v/v = 28.0 wt% MeCN** is inside that range. Interpolating the measured 20 and
  30 wt% rows gives eta = 0.922 cP, rho = 0.942; the carried 0.90/0.94 are -2.4%/-0.2%. This row
  moved from `assumption` to **`derived`**.
- **MeCN/H2O 9:1 v/v = 87.5 wt%** is outside it, but is now **bracketed by two measured points**
  (0.346 <= eta <= 0.574) instead of by nothing.

Registry census moved **121 -> 119 assumption, 86 -> 88 derived**. The `MIX` loop is now
anchor-aware, so a row whose source has been retrieved stops printing "PULL NEEDED" -- leaving that
wording on a row someone has since read is exactly the stale-claim failure this project keeps
hitting.

## Pull list — what would actually move the needle, in order

*(The first issue's top item — "CRC edition + table for the solvent viscosities" — is **withdrawn**:
the registry already had them. See the correction in §3.)*

1. **Register the seven mixed solvents.** They are used by reaction rows, carry estimated μ and ρ,
   and have **no registry rows at all**, so they escape every census and schema gate. This is a
   structural hole, costs no literature retrieval, and is now the cheapest real win.
2. **A source for HFIP μ and ρ.** Used by a reaction row, citation currently reads
   "-- (no source supports this value)".
3. **Convert the 11 Stokes-Einstein diffusivities to Wilke-Chang.** Removes the last typed-in
   number (the 4–5 Å radius) from the D column; the Le Bas path is now gated by G-LEBAS.
4. **Supporting Information of Dorn et al. 2024** (not the article body, which yields only the four
   fits already adopted). Dorn's Table 1 salt list includes NaBr and (C₄H₉)₄NBr, so the SI
   plausibly reaches several MeOH rows. The ACS SI was not retrieved; the open-access Bochum
   dissertation reproduces the article body only.
5. **Dorn Table 3 row for ACN/(C₂H₅)₄NBF₄** — would make the new `0.077 M Et4NBF4/MeCN` row derived
   rather than a bound.
6. **A measured D for any carrier in any working solvent.** One would convert the ferrocene anchor
   from a lone validation point into a calibration.
7. **A measured κ for Bu₄NPF₆/MeCN at any concentration.** None was located.

## What was checked and found sound

- **G-KAPPA (new)** — the registry's six quantitative κ sensitivity claims recomputed from
  `thermal_model.py`: all six match to <0.1%. Negative-controlled (beaker gap 2.0 → 2.2 cm
  fires all six).
- **G-LEBAS (new)** — Le Bas increment closure against ten published reference volumes:
  10/10 within 3%, worst 1.7%. Negative-controlled (perturbing C 14.8 → 15.6 fires it).
- `julia/run_audit.jl` — **14/14** with the new reaction set.
- `data/audit_numeric.py` — **0 FAIL**, 4 known checker-side WARNs (three provenance-arithmetic
  regex artifacts on rows 3, 14 and 23, and a BARRIER-constant regex miss).
- Registry schema gates — every measured row has a locator; every assumption row has a
  sensitivity; 271 rows.
- `MS Drafts/scripts/verify_v21.py` — **30 checks, 0 FAIL**, negative-controlled.
- `data/khl_stratification.py --check-si` — 0 FAIL, negative-controlled.

## What this audit does **not** claim

It does not claim the numbers are wrong. Most of the assumptions are ordinary, defensible
engineering values, and every one carries a stated sensitivity. What it claims is narrower and
exact: **for 207 of 271 registry rows, and for every diffusion coefficient and every electrolyte
conductivity in the model, a reviewer cannot open a cited paper at a stated page and read the
number off.** That is the gap between what the model uses and what the standard demands, measured
rather than estimated.
