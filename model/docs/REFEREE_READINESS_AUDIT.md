# Referee-readiness audit — the two questions, answered with numbers

2026-08-30. Written against the question: *is the model fully provenanced with directly
verifiable numbers for everything, and full physics for all 50 reactions, ready for the harshest
reviewer of the Newman/Weber lineage?*

**The honest answer to both halves is no, and neither is achievable as literally stated.** What
follows is what is true instead, measured rather than asserted, and what a referee of that
lineage will actually attack.

---

## 1. "Fully provenanced with directly verifiable numbers for everything" — NO, and it cannot be

The registry is 282 rows: **74 measured / 83 derived / 125 assumption.**

Assumptions are not a defect to be eliminated; some are *the model's own statement of what it is
simulating* and no citation could ever supply them. The ledger sorts all 125 by what backs them:

| tier | n (live) | meaning |
|---|---|---|
| T0 | 0 | reaches nothing reported |
| **T1** | **15** | **declared choice** — reactor archetypes, δ, design currents, mesh. No citation exists for "the stirred beaker in this study is 100 µm" |
| T2 | 58 | states a perturbation and its computed effect; the conclusion survives |
| **T3** | **5** | same, but a conclusion is conditional on where the value sits in its band |
| T4/T5 | 0 | signed-only / inadequate |

**The 15 T1 rows can never become "directly verifiable numbers."** A reviewer does not ask you to
cite δ = 100 µm; they ask you to *declare* it and show what it costs. That is done, and the
sensitivity is gated.

Where provenance genuinely falls short of what it claims:

- **Category 6 (conductivities): 6 measured / 4 derived / 42 assumption.** Most are display-only
  and G-LIVE proves they reach no conclusion, but the census is unflattering because the
  published subset (3/1/1) is what actually carries weight.
- **17 of 50 concentrations are SI-ONLY** — not page-anchorable in the retrieved article body
  (G-COND). **10 of the 17 do not name an SI source in their own provenance string.** Two of
  those ten are known non-gaps (row 31 draws from IUPAC SDS vol. 57; row 45's volume is a sum).
  **Eight rows want their SIs opened.** This is the single largest remaining provenance gap.
- **1 row (BASF patent) has no text layer** and is OCR-verified to 3%.

**Verdict: the provenance framework is referee-grade — every number is in a declared state, every
assumption carries a sensitivity, and 26 gates with negative controls enforce it. The *content*
has eight rows of unfinished business.**

---

## 2. "Full physics for all 50" — TRUE in one narrow sense, and that sense is not the one a
Newman-school reviewer means

**What is true:** since the 2026-08-24 one-physics merge, all 300 cells come from the same
solver. There is no mixed-physics layer. `julia/npp.jl` solves, per its own header:

> 1D steady Nernst–Planck + electroneutrality across the diffusion film, galvanostatic,
> **dilute-solution theory (Newman ch. 11)**

**What that buys, measured:** migration is active on all 50 rows but does almost nothing on most
of them, because 39 of 50 carriers are neutral.

| migration factor | rows |
|---|---|
| 1.001 – 1.05 | **40 of 50** |
| 1.05 – 1.5 | 5 |
| > 1.5 | 5 (max ×2.876, anodic decarboxylative elimination) |

So "full physics for all 50" honestly means *one uniform physics, whose extra term is worth less
than 5% on 40 of the 50 rows.* Stated that way it is defensible. Stated as "full physics" to a
reviewer who works in concentrated-solution theory, it will not survive.

### What is NOT in the model

| missing | consequence | status |
|---|---|---|
| **Concentrated-solution theory** (Stefan–Maxwell, thermodynamic factor) | dilute theory is used at up to 6.85 M | **quantified below — the central exposure** |
| **Activity coefficients** | γ ≡ 1 throughout | not bounded |
| **Kinetics** (Butler–Volmer) | i_lim only; no η_act in the transport solve. i₀ appears only in the thermal model | declared; the model computes a *ceiling*, not an operating point |
| **Solved hydrodynamics** | δ from correlations (Nernst film), not a momentum solve | declared; δ is a lumped parameter with a swept sensitivity |
| **Secondary/tertiary current distribution** | 1-D primary only | declared in §S6 (the i·L/κ term is planar) |
| **Concentration-dependent properties** | D, μ, κ all constant in c | **partly quantified below** |
| **Double layer / Frumkin** | absent | irrelevant at film scales ≫ Debye length (stated in the SI) |

---

## 3. The central exposure, measured from data already in the repository

### 3a. Dilute-solution theory is measurably violated at these concentrations

Constant-mobility dilute theory predicts κ ∝ c, i.e. Λ = κ/c is constant. `data/dorn_isotherms.csv`
holds 21 **measured** points per system. Λ normalised to its lowest measured point:

| system | m range (mol/kg) | Λ/Λ(min) at increasing m |
|---|---|---|
| Bu₄NBF₄/MeCN | 0.09 – 4.50 | 1.00 → **0.44** @0.80 → 0.17 @2.17 → **0.05** @4.50 |
| Et₄NBF₄/MeCN | 0.08 – 2.53 | 1.00 → 0.60 @0.65 → 0.38 @1.52 → 0.26 @2.53 |
| NaOH/H₂O | 0.61 – 20.8 | 1.00 → 0.47 @4.72 → 0.13 @11.3 → 0.04 @20.8 |
| NaCl/H₂O | 0.21 – 5.40 | 1.00 → 0.74 @1.57 → 0.57 @3.45 → 0.44 @5.40 |
| NaI/MeOH | 0.14 – 4.83 | 1.00 → 0.58 @1.15 → 0.37 @2.78 → 0.24 @4.83 |

**The constant-mobility assumption is wrong by a factor of two by ~0.8 mol/kg and by twenty at the
top of the measured range**, in this repository's own retrieved data. This bounds the **κ path**
(ohmic and thermal) directly. It is a *proxy* for the transport path — via Nernst–Einstein the same
ion–ion interaction reduces D — but it is not a measurement of D(c) and must not be quoted as one.

### 3b. The model uses PURE SOLVENT viscosity where SOLUTION viscosity belongs

`solvents.csv` carries μ for the pure solvent, page-anchored to CRC. The cells contain solute at
up to 13.7 M total. Since i_lim ∝ D ∝ 1/μ, this **overstates** every affected ceiling. Until now
the repository had no bound on it: G-SOLV sweeps ±25–50% but only over the eleven mixed-solvent
rows, for a different reason.

`data/sensitivity_solution_viscosity.py` (**G-MUSOLN**, negative-controlled) sweeps the ratio
μ_solution/μ_solvent over the 14 rows at ≥1.0 M total, and reports a **breaking point** rather
than inventing a viscosity:

    mu x   median i_lim per architecture      >=25 of 50
    1.00   6.1/17.1/19.4/48.6/108.5/121.7     12/18/20/31/36/36
    1.50   6.1/16.8/19.4/48.6/108.5/121.7     11/18/20/31/36/36   <- first count moves
    2.00   6.1/16.8/19.4/48.6/108.5/121.7     10/17/20/31/36/36
    3.00   5.3/15.9/19.4/48.6/108.5/112.9      9/16/19/31/36/36

- **A ≥25 count moves at μ_solution/μ_solvent = 1.5** — a ratio a 3 M salt solution reaches
  easily. The headline integers are exposed, and it is the UNSTIRRED column that moves first,
  because that is one of the two archetypes whose δ is declared rather than computed.
- **The architecture ordering never inverts, out to ×3.0.** The conclusion the paper actually
  rests on is robust. Thin-gap, RDE and RCE counts do not move at all across the whole sweep.

### 3c. i_lim is NOT proportional to 1/μ, and two sweeps had assumed it was

Both viscosity sweeps scaled i_lim by 1/f on every column. That is right only where δ is a
declared constant. Where δ is computed, scaling μ also scales ν = μ/ρ, δ_eff moves with it, and
the two partly cancel. Measured from the repository's own correlations:

| archetype | d ln i_lim / d ln μ | why |
|---|---|---|
| natural, stirred | **−1.0000** | δ declared (300 µm, 100 µm), so i_lim ∝ D ∝ 1/μ |
| flow, thin-gap | **−0.6667** | Lévêque: k_m ∝ (D²u/d_hL)^⅓, so i_lim ∝ D^⅔, no ν |
| RDE | **−0.8333** | Levich: i_lim ∝ D^⅔ν^−⅙ |
| RCE | **−0.9880** | Eisenberg: ν^−0.344 D^0.644 |

Using −1 everywhere overstated the perturbation on four of six archetypes — at f = 2 it applied
0.500× to the flow columns where the correlation gives 0.630×. Both gates now carry per-archetype
exponents, **asserted against `archetype_bands.delta_eff` at run time** so they cannot drift from
the correlations they came from. Consequences: G-SOLV's worst count movement fell **3 → 2 of 50**,
and the SI sentence — which is computed from that sweep — updated itself on rebuild. The SI's
claim "Because i_lim ∝ 1/μ exactly" was **false** and is now stated as i_lim ∝ μ^p with p between
−1 and −2⁄3.

That asymmetry is the honest summary of the whole model: **the ordering and the
order-of-magnitude contrasts are safe; the individual integers are soft.**

---

## 3d. The strongest card: the solver is validated against Newman's own analytic limits

This is the part of the work that *does* meet the standard the question implies, and it should be
led with rather than buried. `julia/run_audit.jl` is **16/16**, and the gates are not
self-consistency checks — each compares the numerical solve against a closed-form result:

| gate | analytic limit | error |
|---|---|---|
| G1 | Tier-1 Fick, neutral carrier with 10× support | **0.0%** |
| **G2** | **Newman binary electrolyte: anion in its own salt (×2 migration enhancement)** | **0.5%** |
| G3 | c_surf/c_bulk at i = ½ i_lim | 0.625% |
| G4 | Fick mesh drift, N = 40 → 160 | 1.0% → 0.0% |
| G5 | EC′ k→0 commuting bound F·D_red·C_med/δ | −0.129% |
| G6 | EC′ Savéant regime, depletion-corrected | 1.147% |
| **G8a** | **EC′ k→0 Newman binary, mesh-matched (×2)** | **0.261%** |
| G10 | Cl⁻/propylene: hits the analytic migration ceiling | 0.7% |
| G11 | EC′ current conservation, max face deviation at 0.9 i_lim | **0.0%** (3×10⁻¹²) |
| G12 | production-mesh convergence, two mediated rows | 0.127%, 0.067% |

**The ×2 migration enhancement for an anion in its own salt is Newman's own binary-electrolyte
result, and the solver reproduces it to 0.26–0.5%.** Discrete charge conservation — F·Σz_jN_j
equal at every interior face — holds at machine precision. A reviewer from that lineage will
check exactly these, and they are in place and negative-controlled.

That is the correct framing of the whole model: **the numerics are verified against the analytic
theory it implements; the exposure is that the theory is dilute-solution theory.**

---

## 4. What a Newman/Weber referee will ask, and whether there is an answer today

| question | answer |
|---|---|
| "Why dilute-solution theory at 3 M?" | Declared in the solver header. Exposure now quantified (§3a, §3b). **No concentrated-solution solve exists.** |
| "Where is the thermodynamic factor?" | Absent. Not bounded. |
| "δ from a correlation is not a boundary layer." | Declared; δ is a lumped parameter, swept, and the stirred value is the one load-bearing assumption (T3). |
| "You report a limiting current with no kinetics." | Correct and intentional — the claim is a *ceiling*, not an operating point. Stated in §S5. |
| "Is D concentration-dependent?" | No. Wilke–Chang at infinite dilution. §3a bounds the analogous mobility effect; D(c) itself is unbounded. |
| "Solution vs solvent viscosity?" | **Now answered:** G-MUSOLN, breaking point μ ×1.5 for counts, ordering safe to ×3. |
| "Do your integers survive your own assumptions?" | Partly. G-SOLV: ±3 of 50. G-MUSOLN: a count moves at ×1.5. G-ZSENS: one row (Ni aryl–aryl homocoupling) moves a count at a plausible z = +2. |

---

## 5. What would actually close the gap

In order of what a referee would weight:

1. **Solution viscosities for the 14 concentrated rows.** One measurement each, or a cited
   correlation, converts G-MUSOLN from a breaking-point sweep into a correction. Highest value
   per unit effort of anything on this list.
2. **The eight SI-ONLY rows** (§1) — open the SIs, page-anchor the concentrations.
3. **Settle z for Cathodic Ni aryl–aryl homocoupling** — the one carrier charge whose plausible
   alternative (z = +2, i.e. [Ni(bpy)₃]²⁺ as written by the source) moves a published count.
4. **A concentrated-solution comparison on one row.** Not a rewrite of the model — a single
   Stefan–Maxwell solve on the worst case (ADN at 6.85 M) would either bound the dilute-theory
   error or show it is tolerable. Without it, §3a is a proxy argument.
5. **D(c) for one carrier.** Same logic as 4.

Items 1–3 are data collection. Items 4–5 are modelling work and are the difference between
"honest about its scope" and "defensible to a concentrated-solution theorist."

---

## 6. Bottom line

The model is **not** fully provenanced with directly verifiable numbers, and cannot be — 15 rows
are declared modelling choices by construction. It **is** uniformly one physics across all 50
reactions, but that physics is **dilute-solution theory**, applied at concentrations where this
repository's own measured isotherms show the underlying assumption failing by a factor of two.

What the model can defend to a hostile reviewer today:

- every number is in a declared state, with a locator or a sensitivity;
- the architecture **ordering** and the order-of-magnitude contrasts survive every sweep run;
- the exposures are named, bounded, and gated rather than hidden.

What it cannot defend today:

- the individual threshold integers, which move under a viscosity ratio of 1.5;
- any quantitative claim resting on dilute-solution theory above ~1 M;
- eight concentrations that a referee cannot follow to a page.

---

## 7. Two overclaims found in the shipped documents

Swept both `.docx` files for language that promises more physics than the model delivers.

### 7a. §S7 described the PRE-MERGE architecture — fixed

The Results-summary paragraph still read *"combines the two physics levels at their appropriate
scope: direct and catalyst-carried entries carry the Tier-0 carrier-transport ceiling … while the
eight mediated entries carry the full EC′ solver result … (falling back to the Tier-0 floor for
the single unconverged moving-front solve)"*. Every clause of that was stale after the
2026-08-24 one-physics merge: there is one physics, not two; the direct rows carry Nernst–Planck
with migration, not Tier-0 Fick; and there is no unconverged solve to fall back for. Its
comparison numbers were the retired ones too (RCE ≥50 as 34, now 33).

Rewritten, and the comparison is now **computed** from `tier0_matrix.csv` against
`tier0_ec_matrix.csv`, so it states what the migration term actually buys and cannot go stale:

> …one physics across all fifty rows: a one-dimensional steady Nernst–Planck balance with
> migration and local electroneutrality across the diffusion film, on dilute-solution theory
> (Newman, Ch. 11), galvanostatic… The scope this fixes is worth stating plainly: the model
> computes a transport ceiling, so it carries no electrode kinetics, and its film thickness is a
> lumped parameter from a mass-transfer correlation rather than a solved momentum boundary layer.
> …≥25 count from 10 to 12 (unstirred), 15 to 18 (stirred), 17 to 20 (flow), 30 to 31 (thin-gap),
> 35 to 36 (RDE), 35 to 36 (RCE)… migration changes the ceiling by less than 5% on 40 of the 50
> rows, by more than twofold on five.

The SI now names its theory level in the results summary, which it did not before.

### 7b. The MANUSCRIPT says "from first principles" — twice, and it is an author decision

> "…the rate ceiling (by modeling limiting current densities for ~50 organic reactions **from
> first principles**)" — abstract
> "…which we quantify by modeling limiting current densities for roughly 50 representative
> reactions **from first principles** (Sections 3 and 4)" — introduction

This is the one phrase in the manuscript a reviewer of that lineage will stop on. What the model
actually is: dilute-solution Nernst–Planck across a film whose thickness comes from an *empirical*
mass-transfer correlation, with concentrations *page-verified from the literature* and
diffusivities from *Wilke–Chang*. Every input is sourced and every step is defensible — but none
of it is *ab initio*, and "first principles" invites exactly the attack the rest of the work is
built to survive.

**Not changed on agent authority — it is the framing of the abstract.** Suggested replacement,
which claims what the model can prove and nothing more:

> "…by solving the coupled transport problem for ~50 page-verified organic electrosyntheses"

The manuscript also **never states its theory level**: "dilute-solution" appears 0 times in the
MS and twice in the SI. One clause in Section 4 naming it would remove the objection entirely.
Both are v41 items.

---

## 8. Resolution (2026-08-30) — disclose, don't chase

Author ruling: **dilute-solution theory and pure-solvent viscosity stay. Both are disclosed.**
The Onsager coefficients concentrated-solution theory needs do not exist for fifty organic
compositions, and the solution viscosities cannot all be measured — chasing either would be a
measurement programme, not a modelling fix. The requirement is that **every modelling choice
reads as clear, understandable and deliberate, never as a number someone thought was reasonable.**

Delivered:

**Registry.** Two rows added to category 3, each with the reason for the choice and a measured
bound, both landing in ledger tier **T2** (quantified, conclusion survives):

- `Transport theory level = dilute-solution` — cites Newman Ch. 11–12; bound is this project's
  own Dorn isotherms (Λ → 0.44 at 0.80 mol kg⁻¹, 0.05 at 4.50 for Bu₄NBF₄/MeCN).
- `Viscosity used in D and in ν = pure solvent` — bound is G-MUSOLN's breaking point.

**SI §S1.1, "The four modelling choices, stated before any result"** — placed *before* any
number, so a reader meets the scope first rather than inferring it from the source:

1. dilute-solution theory — why chosen, and the isotherm bound;
2. pure-solvent viscosity — why chosen, and the ×1.5 / ×3.0 breaking points;
3. a *ceiling*, not an operating point — no Butler–Volmer, i₀ only in the thermal balance;
4. δ is a lumped parameter, not a solved boundary layer.

Closing paragraph states what actually protects the results: the numerics are verified against the
analytic limits of the theory that *is* implemented (Newman's binary ×2 to 0.5% and 0.26%, charge
conservation to 3×10⁻¹²), and every conclusion rests on the ordering and on order-of-magnitude
contrasts, which no sweep inverts.

**Manuscript v41** (3 tracked edits, no artwork):

- abstract and introduction: **"from first principles" removed.** It was never accurate — δ from
  an empirical correlation, D from Wilke–Chang, concentrations page-verified from primary sources.
  Now "by solving a one-dimensional transport model … at page-verified conditions".
- Section 4: "a one-dimensional **dilute-solution** Nernst–Planck transport model (migration and
  local electroneutrality across the diffusion film; modelling choices and their bounds in
  SI §S1.1)". The MS previously named its theory level **zero** times.

**Also fixed:** `runsFromText` now honours `**bold**`. Ten literal `**` markers were shipping in
the SI as visible asterisks — markdown nothing rendered. Now 227 bold runs, 0 stray markers.

State: `run_gates.sh` 26 passed / 1 REVIEW NEEDED (G-COND) / 3 skipped; `verify_v41.py` 31 checks
0 FAIL with its control firing exactly 9; `run_audit.jl` 16/16.

---

## 9. 2026-08-30, second pass — the disclosures given measured backing

**i₀ does not affect cooling, and the SI now says which side of the balance each input acts on.**
Author challenge, and it was right to make. `i₀` appears only in `q(i) = [2b·asinh(i/2i₀) + iL/κ]·i`
— the heat *generated*. The cooling coefficient `U′ = [(1/h_int + 1/h_ext)⁻¹]·σ` contains no
kinetic or electrolyte term at all. The SI listed κ, σ and i₀ together as "three assumptions that
straddle the pass/fail line" without saying that κ and i₀ move the heat while σ moves the
rejection. Now stated explicitly.

**δ = 100 µm for the stirred beaker — now backed by a computed lower bound (G-DSTIR).**
Evaluating Levich `δ = 1.61 D^⅓ν^⅙ω^−½` on each reaction's own D and ν at 200–1200 rpm:

    rpm    delta over the 50 (um): min / median / max
    200      23.9 /  35.7 /  44.6
    500      15.1 /  22.6 /  28.2
    1200      9.8 /  14.6 /  18.2

Median 15–36 µm, so **the declared 100 µm is 2.8–6.9× thicker than an idealised uniformly
accessible electrode would give** — conservative in the right direction for a plate mounted
off-axis in a beaker. Schmidt numbers are 176 / 445 / 19006 (min/median/max): these aprotic
organics are mostly *lower*-Sc than the aqueous ferricyanide the RCE correlation was fitted to.

**This settles the withdrawn sub-25 claim the opposite way from intuition, and it is reported as
found.** 68.3 µm lies *between* the idealised Levich value and the declared 100 µm, so a stirred
cell with genuinely good convection could reach it. The claim is not excluded by geometry — it is
simply not established by anything measured here. That is why it stays withdrawn, and the SI now
says so in those terms.

**Ea = 15 kJ mol⁻¹ for κ(T) — now compared against measurement (G-EAVISC).** It had been declared
outright ("no page-anchored source for Ea itself"), backed only by *water's* viscous activation
energy. The same CRC table that page-anchors μ(25 °C) also prints η at 25/50/75 °C:

| solvent | registry μ(25) | CRC η(25) | accepted | Ea(η), kJ mol⁻¹ |
|---|---|---|---|---|
| MeCN | 0.369 | 0.369 | yes | 8.4 (25–50), 7.2 (50–75) |
| DMF | 0.794 | 0.794 | yes | 7.7 |
| THF | 0.456 | 0.456 | yes | 7.7 |
| H₂O | 0.890 | 13.4 | **no** | — |

Every row is accepted **only if its η(25 °C) reproduces the registry viscosity**; water's row
mis-aligns in the extraction and is dropped rather than repaired — the check working. By Walden
(Λη ≈ const) this is the right quantity to judge an Ea(κ) bound against, and the declared 15 is
**1.8–2.1× the measured range** — an upper bound by about a factor of two.

**Six SIs mined; every carried number confirmed, none wrong.** The eight SI-ONLY rows are down to
four, and those four are accounted for: rows 20 and 47 have **no SI in existence** (a 1994 ChemComm
and a 2010 Electrochim. Acta), row 31 draws its substrate from IUPAC SDS vol. 57 (a different
cited source), row 45's volume is a sum (10:10:10:3).

| row | SI | result |
|---|---|---|
| 4 | `aan6206_fu_sm.pdf` | 0.2 mmol alkene / 0.01 mmol Mn / 3.9 mL → 0.0513, 0.00256, 0.1 M — as carried |
| 7 | `ol8b00981_si_001.pdf` | 0.3 mmol in 7.5 mL → 0.040 M substrate and NaBr — as carried |
| 11 | `science.adf4762_sm.pdf` | the quoted recipe is verbatim from the SI |
| 12 | `op6c00110_si_001.pdf` | 0.3 M substrate, 1.6 equiv LiBr → 0.48 M, 5 mol% Ni → 0.015 M — as carried |
| 14 | `ja211005g_si_001.pdf` | 5/15/3 mmol in 33 mL → 0.152, 0.455, 0.091 M — as carried |
| 37 | `c6sc02117d1_suppl.pdf` | 1.60/3.20 mmol, 2.13 g LiClO₄, 20 mL → 0.080, 0.160, 1.00 M — as carried |

**The charge sweep was testing species that do not exist.** `ALTS = [-1, 1, 2]` was written for the
five metal complexes carried neutral, then applied unchanged to the two anionic carriers — so it
tested a *cationic carboxylate* and a *cationic phthalimide* while **never testing z = 0**, the
only plausible alternative for either. For the decarboxylative row z = 0 is arguably the dominant
form: its own registry note says Et₃N at 7.5 mM against 0.1 M acid, so at most ~7% is deprotonated.
`ALTS = [-1, 0, 1, 2]` now; re-run in progress.
