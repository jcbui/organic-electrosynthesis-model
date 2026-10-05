# Provenance and physics push — 2026-08-24 (overnight)

Brief: *"every number comes from a REAL source and the model and its physics are totally airtight
for even the harshest of reviewers"*, no shortcuts, full physics for all 50.

This file records what was found, what was fixed, what was rejected, and what is still open. Five
defects were found in the physics or the wiring, three of them capable of moving a published
number by a factor of two or more.

---

## 1. Ion diffusivities — from 13/100 sourced to 76/100

`electrolyte_ions.csv` used `1e-09` for **32 different cations** and `1.5e-09` for 24 anions.
Those are defaults, not data, and they feed the migration term.

### Sources, each read from page images and cross-checked against the others

| source | what it gave |
|---|---|
| **Krumgalz**, *J. Chem. Soc. Faraday Trans. 1* **1983**, *79*, 571–587, Tables 2 (p. 577), 3 (p. 578), 4 (pp. 580–581) | λ° per ion per non-aqueous solvent; the λ°η product for tetraalkylammonium ions; the viscosities used to recover λ° |
| **CRC Handbook 97th ed.**, "Ionic Conductivity and Diffusion at Infinite Dilution" (Vanýsek), **pp. 5-75 / 5-76** | aqueous λ° **and D directly**, for 23 ions incl. Bu₄N⁺, Et₄N⁺, Me₄N⁺, Et₃NH⁺, PF₆⁻ |
| **Energy Environ. Sci.** **2015**, *8*, 3515–3530, **Table 2 p. 3518** | non-aqueous λ° for BF₄⁻, ClO₄⁻, PF₆⁻, Li⁺ in MeCN/THF/PC/GBL — the ions neither of the others carries |

**They agree.** EES vs Krumgalz in MeCN, by wholly independent routes: Me₄N⁺ +0.02%, Et₄N⁺ +0.22%,
Bu₄N⁺ −0.09%. EES vs CRC in water: Li⁺ +0.05%, Me₄N⁺ 0.00%, Et₄N⁺ +0.31%, Bu₄N⁺ 0.00%,
ClO₄⁻ +0.09%.

**One conflict, recorded not smoothed:** aqueous PF₆⁻ is 65.5 in EES against CRC's 56.9 — 15%. It
does not propagate (every PF₆⁻ row here is non-aqueous), and CRC is preferred for water.

### Two shortcuts were TESTED AND REJECTED

| shortcut | measured accuracy | verdict |
|---|---|---|
| Walden transfer from water (λ°η const, water → organic) | 83 checkable pairs: median error **1.81×**, only **7%** within 30%, worst **11×** (H⁺) | **unusable** |
| Stokes–Einstein from the EES printed radii | 85 pairs: median 0.89 but worst **6.7×**, 59% within 30% | **too loose** |

### One transfer WAS used, only where it earns it

λ°η constancy was measured per ion on this file's own assembled data (non-aqueous only):

    Bu4N+ 4.6% (n=13)   Et4N+ 6.1% (n=9)   Me4N+ 6.8% (n=9)   BPh4- 3.8% (n=3)
    ... and it FAILS: BF4- 18.4%, Li+ 19.8%, Br- 19.7%, SCN- 20.1%, Cl- 23.2%, H+ 47.8%

Only the four <12% ions were transferred, closing Et₄N⁺/THF and Me₄N⁺/acetone. The Bu₄N⁺ mean
here, **0.2154 ± 0.0100 over 13 solvents**, reproduces Krumgalz's published 0.2131 ± 0.0024 to
within 1% from a partly different solvent set.

**24 slots remain unsourced and are marked as such in the file.** No number was invented for them.

---

## 2. HFIP density — resolved, and the CRC is wrong

The code carried 1.596 g cm⁻³ marked "rho STILL UNSOURCED".

**CRC 97th ed. p. 3-296 entry 5801 prints 1.4600 at 21 °C** in the density column — verified by
x-coordinate (the value sits at x = 463.3, identical to a known density one row below, 28 pt left
of that row's nD). That is 9.4% from the value in use.

Three independent lines say the CRC cell is wrong:
1. **Sigma-Aldrich specification**: ρ = **1.596 g/mL at 25 °C**, and nD = **1.275** — so 1.4600 is
   neither the density nor the refractive index of this compound.
2. **TFE-calibrated molar volume**: the F-for-H increment from ethanol → 2,2,2-trifluoroethanol is
   (72.27 − 58.37)/3 = +4.63 cm³ mol⁻¹. Six of those on isopropanol predicts ρ = **1.611**.
   1.596 is −0.9% from that; 1.4600 is −9.4%.
3. CRC's own **bp 59 °C and mp −2.0 °C** for the same entry match everything else.

CRC's neighbouring entry 5802 carries nD = 1.4631²⁰, numerically adjacent to HFIP's printed
"density" 1.4600²¹ one row up — consistent with a typesetting slip in that cell.

**Decision: 1.596, cited as the Sigma-Aldrich specification (secondary, marked "lit."), never as
CRC, with the CRC disagreement stated so a referee who checks CRC knows why it was not used.**

---

## 3. A physics bug: every row was solved as an oxidation

`run_all50_np.jl` built the electrode product as `z_prod = z_c + n` **unconditionally**. That is
the oxidation stoichiometry; Σz·s comes out at +1, i.e. anodic current, for all 50 rows.

For a reduction the product is `z_c − n` and Σz·s = −1. The difference **reverses the sign of the
field's effect on a charged carrier**. Demonstrated on the Ni(tet a)²⁺ row in a controlled test:

| stoichiometry | Σz·s | i_NP/i_Fick |
|---|---|---|
| `z_c + n` (what the code did) | +1 | **0.9687** — a 3% hindrance |
| `z_c − n` (what the row is) | −1 | **1.0459** — a 4.6% enhancement |

0.9687 is exactly the 0.969 the published matrix carried, confirming the diagnosis.

**Fixed** with `data/electrode_direction.csv`: all 50 rows, **35 anodic / 15 cathodic**, each with
the electrode wiring or mechanism sentence from its own paper (e.g. Baran's Co-H rows: *"Mg(+)/C(–)"*,
*"Reduction of Co(salen)-1 at −2.03 V"*; Mo/Jensen's Minisci: *"the cathodic radical precursor"*).
A row missing from that table is now a hard error. Ten of the eleven charged carriers are anodic,
so exactly one row's number changes today — but the hardcoded sign was a latent trap for any future
charged cathodic row.

---

## 4. The orphan: 42 of 50 published rows had no migration

`run_all50_np.jl` solved all 50 × 6 with Nernst–Planck and migration, wrote `all50_np_matrix.csv`,
and **nothing read it**. The published matrix was assembled from the Tier-0 **Fick** table.

The Kolbe row is a charged carrier in its own salt, so migration must double it exactly:

| | Fick | NP | published |
|---|---|---|---|
| stirred | 194.02 | 389.17 | **194.00** |
| rce | 1801.08 | 3612.58 | **1801.00** |

Six rows were affected. `build_merged_matrix.py` is rewritten onto the NP layer, and
**G-ORPHAN** (`data/check_orphans.py`) now asserts every solver artefact is consumed —
`audit_numeric.py` could not catch this, because an orphan is by definition not a source of
anything, and consistency between the wrong inputs is still consistent.

---

## 5. A silent fallback to placeholder diffusivities

When `conc_M` was blank in `electrolyte_ions.csv`, the solver took an else-branch using **hardcoded
1e-9 / 1.5e-9** and never read the sourced table. That was true for exactly the **three rows whose
electrolyte definitions `ONE_PHYSICS_20260823.md` had already flagged as unresolved** — so the
flagged ambiguity had a concrete consequence nobody had named.

One of them, **Kolbe, has a charged carrier and reports ×2.006** — a factor of two on a published
ceiling, computed from placeholders. Worse, the sensitivity sweep over the sourced table *could not
see it*, because that branch never reads that table.

**Now a hard error for a charged carrier**; a neutral carrier is allowed through but announced.

**The fallback was not cosmetic.** Once Kolbe was moved onto the sourced diffusivities (Me₄N⁺ in
acetone from the per-ion λ°η transfer, BF₄⁻ from EES), its migration factor moved
**×2.006 → ×1.648** — an 18% change on a published row, caused purely by replacing the hardcoded
`1e-9` / `1.5e-9` placeholders with the real values. The ×2.006 that had been reported was the
binary-salt limit computed from two numbers that were in the Julia source because nobody had
supplied better ones.
All three electrolytes are resolved from their papers:

| row | resolved to |
|---|---|
| Kolbe | Me₄N⁺ 0.20 M = BF₄⁻ 0.05 M + carboxylate 0.15 M (10 mmol Me₄NBF₄ + 30 mmol Me₄NOH in 200 mL) |
| Giese | 0.0156 M: pH 2 gives H⁺ = Cl⁻ = 0.010 M, plus NaCl at 7 mol% of the 1.19 mmol alkene = 0.0056 M |
| benzaldehyde | 5 wt% AcOH is 0.83 M **total** but pKa 4.76 gives ionic strength √(Ka·C) = **0.0038 M** — effectively unsupported |

---

## 6. OPEN, AND THE MOST IMPORTANT ONE: the Kolbe row is not electroneutral

The row carries **1.00 M of a z = −1 carboxylate**. The paper's charge sheet supplies **0.20 M of
Me₄N⁺** (10 mmol Me₄NBF₄ + 30 mmol Me₄NOH·5H₂O in 200 mL acetone). You cannot have 1.00 M of anion
with 0.20 M of cation, and the solver was **manufacturing the missing 0.8 M** in its
electroneutrality step — four fifths of the counter-ion pool. That top-up now prints a warning when
it dominates the pool.

The base charged sets a ceiling on the carboxylate: 30 mmol of Me₄NOH can deprotonate at most
30 mmol of acid, i.e. **0.15 M carboxylate**, with ~1.05 M left as neutral acid (undecenoic +
pivalic).

**Three readings, and this needs an author, not a script:**

1. **carrier = carboxylate, 0.15 M, z = −1.** Electroneutral and self-consistent. Ceiling drops
   ~6.7×; the unstirred cell would fall below 25 mA cm⁻².
2. **carrier = acid, 1.00 M, z = 0.** No migration (the ×2.006 disappears), ceiling unchanged.
3. **a CE system** — fast acid ⇌ carboxylate pre-equilibrium with the acid as a mobile reservoir,
   so the transported quantity is the total 1.0 M even though the discharged species is at 0.15 M.
   This is the same structure as the mediated EC′ rows and is arguably the physically right
   description, but the model does not currently express it.

The present state — z = −1 **at** 1.00 M — is none of the three, and is the only one that is
definitely wrong. **I have not changed the number**, because picking between (1), (2) and (3) is a
chemical judgement with a 6.7× consequence, not a data lookup.

---

## 7. Conductivity κ — bounded, and six values externally validated

**κ never enters the transport solvers.** `grep -c kappa` over `npp_ecprime.jl`,
`run_all50_np.jl`, `run_mediated.jl` and `run_tier0.jl` returns **0** for all four. It feeds
`cellvoltage.jl` and the SI tables only. So no κ estimate can move an i_lim ceiling or a
threshold count — that bounds the exposure precisely.

**G-KAPPA-CA** (`data/check_kappa_casteel.py`) checks the six Bu₄NBF₄/Et₄NBF₄-in-MeCN entries
against a **measured** correlation: Dorn, Kareth, Weidner & Petermann, *J. Chem. Eng. Data* **2024**,
*69*, 1493–1502, Table 3 p. 1499 (Casteel–Amis, 298.15 K, MAPE 0.80% and 1.65%). All six agree
within **±6%**, over 0.043–0.3 M, with the molality conversion inside the fits' stated validity.

---

## 8. Sensitivity of the remaining unsourced diffusivities — MUST BE RE-RUN

`data/sensitivity_unsourced_D.py` perturbs all 24 unsourced slots by ×3 and ÷3 and re-solves the
full matrix. First run: **no change at all**, counts identical.

**That result is not yet trustworthy and is being re-run.** Fifteen of the nineteen affected rows
have a neutral carrier, where insensitivity is physical — migration does nothing to a neutral
species. But **Kolbe was on the placeholder branch at the time**, so the sweep structurally could
not see the one charged row that mattered. The branch is now a hard error and the electrolyte is
resolved, so the sweep will actually exercise it.

A sensitivity analysis that reports "no effect" because the perturbation never reached the
code path is worse than no analysis, and this one nearly did.

---

## Still open

1. **Kolbe carrier concentration** (§6) — author decision, 6.7×.
2. 24 unsourced diffusivity slots; sweep to be re-run and re-read.
3. Full-physics merge to be run and the counts re-derived.
4. **16 carrier charges** still unreviewed — migration acts only on a charged carrier, so a wrong
   z moves a ceiling by up to 2× in silence.
5. The eight rate constants remain order-of-magnitude literature passes; the SI concedes for SCN⁻
   *"NO direct rate measurement located"*.

---

## 9. The isothermal assumption, finally quantified

Every row is solved at 25 °C. That is declared per row in the provenance, but its **magnitude was
never stated**, which is the kind of gap a referee closes for you. Using the CRC's own note on the
ionic-conductivity table — λ and D "increase by 2 to 3% per degree" near 25 °C — at 2.5%/K:

| row | reaction | paper's T | ΔT | D factor | ceiling factor |
|---|---|---|---|---|---|
| 3 | benzimidazole annulation | reflux THF/MeOH ≈65 °C | +40 | 2.69 | **2.69** |
| 29 | anodic methoxylation (Lysmeral) | 55 °C | +30 | 2.10 | **2.10** |
| 14 | BDD phenol–arene | 50 °C | +25 | 1.85 | **1.85** |
| 25 | diazo difunctionalization | 50 °C | +25 | 1.85 | **1.85** |
| 19 | Ni aryl–aryl homocoupling | 45 °C | +20 | 1.64 | **1.64** |
| 33 | thioether → sulfone (kilo) | <20 °C | −7 | 0.84 | 0.84 |

`i_lim` is first order in D at fixed δ and D^(2/3) where δ comes from a Sherwood correlation, so
these are upper bounds on the effect.

**Five of the fifty rows run 20–40 K above the modelled temperature, so their true ceilings are
roughly 1.6–2.7× the tabulated ones.** The direction matters: the assumption is systematically
CONSERVATIVE — every affected row is understated, none overstated. That is a defensible modelling
choice, but it should be stated with this table rather than left as a per-row footnote, because a
referee who notices "reflux" against a 25 °C model will otherwise assume the worst.

---

## 10. Five more defects, found by the gates written earlier tonight

### 10a. A rename silently halved a migration enhancement

`julia/run_all50_np.jl` holds `CARRIER_IS_SUPPORTING_ANION`, the set of rows where the carrier IS
the electrolyte anion (bromide in NaBr, chloride in NaCl, carbonate in Na₂CO₃) and so must not be
counted twice. When the condition audit renamed *Cl-mediated **propylene** epoxidation* to
*…**ethylene**…*, that Set was not updated.

**A Set lookup that misses simply returns false.** `same_ion` went false, the chloride was counted
both as the carrier and as a separate supporting anion, and its migration enhancement collapsed
from the binary limit of ~2 to **×1.176** — which is, verbatim, the symptom the code's own comment
records as the original bug: *"chloride in 2 M NaCl at 1.176 where it should be ~2"*. Reintroduced
by a rename, silently, with no gate able to see it.

Fixed, and `check_supporting_anion_set()` now asserts every name in that Set is a real reaction.

### 10b. A phantom hydroxide, with its aqueous diffusivity, in methanol

*Non-Kolbe decarboxylative alpha-methoxylation* runs in `Et3N 7.5 mM (no salt)/MeOH`. Et₃N deprotonates the
amino acid, so the only ions present are **Et₃NH⁺ and the carboxylate — which is the carrier**.
The row instead named **OH⁻** as its supporting anion and gave it **5.27e-9 m² s⁻¹**, the *aqueous*
value from CRC p. 5-76, in methanol.

That phantom, unusually mobile ion carried current in the solve and pushed the row to **×2.876** —
above the binary limit of 2, which is what drew attention to it. Corrected: `D_an` is the carrier's
own diffusivity and the row is registered in `CARRIER_IS_SUPPORTING_ANION`.

### 10c. Four EC′ cells were accepted below their own no-source floor

The mediated solver accepted a cell when `i_ec ≥ 0.9·i_t0`, where `i_t0` is the **Fick** expression
`F·D·C/(|s|·δ)` — no migration. Once migration is in the model that bound is far too weak.

For Br⁻ oxidation × unstirred the Fick figure is **10.17** mA cm⁻² while the k = 0 solve *with
migration* is **20.44**. A c-control walk that died at **14.26** cleared 0.9 × 10.17 comfortably and
was published — while sitting **30% below the no-source floor of its own physics**. The homogeneous
source can only ADD flux, so that is not a possible answer.

Four of the 48 cells were being accepted this way:

| cell | published | its own k=0 floor | shortfall |
|---|---|---|---|
| Br⁻ oxidation × unstirred | 14.26 | 20.44 | **−30%** |
| NHPI × RCE | 61.25 | 65.66 | −6.7% |
| NHPI × RDE | 49.25 | 52.75 | −6.6% |
| NHPI × thin-gap | 19.63 | 20.75 | −5.4% |

The other five bromination cells pass with a consistent **×1.163** amplification over their k = 0
floors, which is what shows the two solvers are comparable and the floor is the right test.

`run_mediated.jl` now computes `k0_floor(δ)` — the identical species set, mesh and boundary
conditions with `k = 0`, solved with the same ramp-then-c-control treatment so the floor is not
itself fold-limited — and every acceptance test uses `max(0.9·i_t0, i_k0)`.
`build_merged_matrix.py` asserts the same relation independently at merge time; it is what caught
this.

### 10d and 10e. Stale keys in two more places

**G-NAMES** (`data/check_reaction_names.py`) was written to stop 10a recurring, and immediately
found two more:

- `data/reactions_50_khl_class.csv` was keyed on a **superseded 50-reaction set** — carrying
  *Electrocatalytic alkyne semihydrogenation* and *Alcohol → carboxylic acid (Ni(OH)₂ anode)*,
  and missing the two rows that replaced them. No published number depended on it
  (`khl_stratification.py` has read the class from `reactions_50.csv` directly since 2026-08-22),
  but it purported to be the audit trail for the current set and was not. The retired rows are
  marked `status=retired` rather than deleted; the two current rows are added.
- `make_si.js` carried a whole sentence describing the row by its **old name, old electrolyte
  (2 M Cl⁻) and old substrate basis (Henry's law)**. Rewritten to the verified 1.0 M KCl and the
  measured 3.52 mmol L⁻¹.
- `data/exemplar_pdf_map.csv` used `|` as a stand-in for commas in two reaction names — my own
  hack from building the file — so those two rows keyed on nothing. Restored to real commas with
  proper CSV quoting.

---

## 11. A configuration with no limiting current at all — and a flag that could not see it

Fixing the phantom hydroxide (§10b) meant registering *Non-Kolbe decarboxylative alpha-methoxylation* in
`CARRIER_IS_SUPPORTING_ANION`, so its carboxylate would not be counted twice. That made the row
**worse**: it came back at **×73.6**, flagged `ok`.

### Why

Registering it left the carboxylate as the **only** anion in the cell. Its anodic product is
formally a **cation** (`z_prod = z_c + n = −1 + 2 = +1`). A system whose sole anion is consumed and
converted into a cation **has no diffusion-limited current**: electroneutrality forbids that anion
from depleting at the surface, so the current ramp climbs without ever collapsing.

Measured directly, same cell, same mesh:

| configuration | i/i_Fick | limiter |
|---|---|---|
| carrier is the ONLY anion | **50.03** | `newton-wall (no collapse)` |
| any second anion present (7.5 mM) | **2.88** | `newton-wall; substrate (total catalysis)` |

against a binary expectation of 1/(1−t) = **2.27**. The second row terminates on a real physical
criterion; the first never terminates at all.

Reverted, with the reason recorded in the source so nobody re-adds it.

### The flag was the deeper problem

`flag = (i_np > 0 && isfinite(fac)) ? "ok" : "unsolved"` — the only tests were *positive* and
*finite*. A ramp that runs away to 73× satisfies both. Every one of the 300 cells reports limiter
`newton-wall`, because that is simply how `solve_ilim_ec` records termination, so the limiter string
could not distinguish a converged cell from a runaway either.

Two guards added:

- **`run_all50_np.jl`** now applies a physical ceiling. For a binary electrolyte in which the
  carrier is the reacting ion, Newman gives `1 + |z_c|/z_counter` — 2 for a −1 carrier, 3 for −2.
  A formally charged anodic product can add a little (2.88 above is legitimate), so the guard sits
  generously at **5**; beyond that the cell is flagged `runaway` and named.
- **`build_merged_matrix.py`** refuses to publish any NP cell not flagged `ok`.

**This is worth keeping as a result, not just a fix.** It says something real about mediator design:
a mediator that is the only anion in its own electrolyte, and whose oxidised form is cationic,
cannot be driven to a transport limit — the field holds it at the electrode. That is the opposite
of the failure mode the rest of §S5.4 is about.

---

## 12. The counter-ion deficit is bounded to exactly two rows

Having found it on Kolbe, the obvious question is how many other rows declare more carrier charge
than their electrolyte can balance. Checked across all eleven charged-carrier rows:

| row | z | C_carrier | supporting | carrier charge / support |
|---|---|---|---|---|
| **Kolbe homocoupling of 10-undecenoate** | −1 | 1.00 | 0.05 M Me₄NBF₄ | **5.0× vs the 0.20 M Me₄N⁺ inventory** |
| **Non-Kolbe decarboxylative alpha-methoxylation** | −1 | 0.10 | 7.5 mM Et₃N | **13.3×** |
| Alkaline lignin → vanillin | −2 | 1.00 | 1 M Na₂CO₃ | balanced — Na₂CO₃ gives **2** Na⁺ per carbonate, so the equivalents match; the apparent 2.00× is molarity-vs-equivalents, not a deficit |
| Br⁻ Hofmann, Cl⁻ ethylene, Br⁻ bromination, alkenesulfonate, sulfonylation, thiocyanation | −1 | — | — | 1.00× — the carrier IS its own salt |
| NHPI, 5-exo cyclization | −1, +2 | — | — | 0.33×, 0.20× — genuinely supported |

**The two affected rows are precisely the two in which a LIMITED BASE creates the anionic carrier**
— 30 mmol Me₄NOH against 200 mmol of undecenoic acid, and 7.5 mM Et₃N against 0.1 M of amino acid.
Everywhere else the carrier arrives as a fully dissociated salt and the books balance.

That is a satisfying place for the problem to land: it is not scattered through the set, it is one
identifiable chemical situation, and both instances need the same decision (§6). Neither row's
number should be quoted until it is made.

---

## 13. The 24 unsourced diffusivities provably cannot affect any published number

The sensitivity sweep reported *exactly* 0.0% change from perturbing all 24 unsourced diffusivities
by ×3 and ÷3. An exactly-zero result usually means the perturbation never reached the code, so it
was treated as void rather than as evidence. It turns out to be right, and for a reason worth
stating properly.

### The mechanism

A species that does not react — `s = 0` at the electrode and `ν = 0` in the homogeneous step —
carries **zero net flux at steady state**. Its Nernst–Planck equation reduces to

    0 = −D(dc/dx) − (zDF/RT)·c·(dφ/dx)

and **D cancels**. Its concentration profile is a Boltzmann distribution set by the potential
alone. A non-reacting ion's diffusivity therefore does not enter the limiting current at all.

### Measured, not argued

Same cell, same mesh, one ion's D moved by a factor of ten each way:

| case | i_lim (mA cm⁻²) | migration factor |
|---|---|---|
| baseline | 20.437 | 2.009892 |
| counter-ion D **×10** | **20.437** | **2.009892** — identical |
| counter-ion D **÷10** | **20.437** | **2.009892** — identical |
| CARRIER D ×2 | 40.874 | 2.009892 — i_lim scales through i_Fick; the *enhancement* is unchanged |
| CARRIER D ÷2 | 10.219 | 2.009892 |

Identical to six decimal places. The migration enhancement depends on the **charges and
concentrations** of the ion inventory, not on anybody's diffusivity; the carrier's D sets the Fick
scale and nothing else.

### Why this closes the question

- **All 24 unsourced slots are supporting-ion columns** (`D_cat` / `D_an`) in
  `electrolyte_ions.csv` — every one is a non-reacting species.
- The **carrier** diffusivity, which is the one that matters, comes from `reactions_50.csv`
  (Wilke–Chang on Le Bas volumes) and **all 50 rows carry a `D_provenance` string**.
- `run_mediated.jl` does not read `electrolyte_ions.csv` at all — it carries its own species
  lists — so the mediated rows are untouched by these values either way.

So the honest statement is no longer "24 numbers are unsourced and a sweep suggests they don't
matter". It is: **every unsourced diffusivity in this model belongs to a non-reacting species,
and non-reacting diffusivities provably do not enter the limiting current.** They still matter for
conductivity — and κ, as §7 shows, never enters the transport solvers either.

Sourcing them remains worth doing for the κ path and for the record. It is no longer a gap in the
provenance of any published ceiling.

**This also explains, retrospectively, why §5's placeholder-fallback bug moved Kolbe from ×2.006 to
×1.648.** It was never about the placeholder D values — those cannot matter. It was that the blank
`conc_M` sent the row down a branch with a different ion *inventory*: no supporting salt at all,
versus 0.05 M Me₄NBF₄. Concentrations and charges are exactly what the enhancement does depend on.

---

## 14. The cell that resisted everything: the continuation was anchored on the wrong limit

`Br⁻ oxidation × unstirred` has defeated the current ramp, c-control, δ-continuation and four mesh
refinements across two audits, and has been carried on a k-continuation result each time. With the
correct floor in place (§10c) the merge finally refused it: **15.53 mA cm⁻² against its own k = 0
floor of 20.44** — which cannot happen, because the homogeneous source only regenerates mediator.

### The diagnosis

Two things pointed at the answer rather than at the mesh:

1. The cell terminated with the **mediator still at 41% of bulk** (`c_red/cb = 4.06e-01`), whereas
   every cell that converges terminates with it near-exhausted (~1.7e-3). It was stopping early,
   not finding a limit.
2. **k-continuation starts at k = 0 and raises k, so its answer can only go UP.** Ending below the
   k = 0 value meant it had started from the wrong place.

`solve_ilim_ec_kcont(mkproblem, k_target, i_t0)` ramps the k = 0 problem to `frac_i` (0.85) of the
limit it is handed, walks `k` up at that fixed current, then reads the limit off the polarisation
curve. It was being handed **`i_t0` — the Fick expression `F·D·C/(|s|·δ)`, no migration**.

For this cell that is 10.17 mA cm⁻², so the continuation anchored at 0.85 × 10.17 = **8.65**, while
the true k = 0 limit with migration is **20.44**. Starting less than half way up, the subsequent
c-control walk settled on a lower branch and returned 15.53.

The bug was invisible for as long as the acceptance test was *also* Fick-based: 15.53 comfortably
cleared 0.9 × 10.17, so the cell looked solved. Two Fick-based quantities agreeing with each other
is not a check.

### The fix, and what it did NOT do

The continuation is now anchored on `max(i_t0, i_k0)`, where `i_k0` is the same cell's k = 0 solve
**with migration**, already computed for the floor test. Anchoring on the Fick value was wrong and
this is right.

**But it does not rescue the cell, and I reported otherwise before checking.** The value moved
15.53 → 18.16 and I called that an improvement. Sweeping the anchor shows it is not:

| anchor `frac_i` | result | ratio to the k = 0 floor |
|---|---|---|
| 0.85 | 17.259 | **0.850×** |
| 0.95 | 19.290 | **0.950×** |
| 0.98 | 19.899 | **0.980×** |
| 0.99 | 20.110 | **0.990×** |

The answer tracks `frac_i` × the floor at every setting. **The k-continuation is handing back
essentially its own anchor**: the c-control walk at the production `k` takes at most one step and
stops. Raising the anchor raised the artefact.

Replicating the exact call `run_mediated.jl` makes pins it down:

    k = 0 ramp            19.7693 mA/cm2   newton-wall (no collapse)
    k = 0 + c-control     20.3051 mA/cm2   plateau (c_red/cb 1.66e-03)   <- the floor
    anchor passed         20.3051
    0.85 x anchor         17.2593                                        <- ia inside kcont
    k-continuation ->     17.2795          movement from the anchor: 0.12%

Twelve hundredths of a percent. Not a literal return of the anchor -- which is why a 1e-6 guard let
it through -- but it has not walked a polarisation curve, and whatever the anchor it lands BELOW
the floor, so the cell is correctly flagged `wall` either way. The guard is now 2%: anything within
a couple of percent of where the continuation started is not a limit.

So the honest position is that this cell does not converge by ANY implemented path -- and the
apparent progress across this audit (14.26 → 15.53 → 18.16) was three different artefacts, not
three better solves. The direct ramp's 5.4-5.9 is the only value that comes from actually walking
the polarisation curve, and even that terminates on `newton-wall (no collapse)` rather than a clean
physical criterion.

**The lesson generalises.** Every one of the five silent defects tonight had the same shape: a
quantity was compared against a *weaker* version of itself — Fick against Nernst–Planck, a lookup
that misses against a lookup that legitimately finds nothing, positive-and-finite against
converged. A check is only worth having if it can fail for the reason you care about.

---

## 15. The last unresolved cell may be a definitional question, not a numerical one

`Br⁻ oxidation × unstirred` is the only cell in the set that does not converge. It has moved
14.26 → 15.53 → **18.16** as each defect above was fixed, against a k = 0 floor of **20.31**.

### It is not a mesh problem

| | N = 90 | N = 180 | N = 360 |
|---|---|---|---|
| k = 0 floor | 20.305 | 20.312 | 20.305 |
| EC′, direct ramp + c-control | 5.442 | 5.821 | 5.917 |

The floor is mesh-converged to **0.03%**. The EC′ direct path moves 8% over a 4× refinement and
lands nowhere near the floor. Deepening the c-control walk (`frac_end` 1e-3 → 1e-5) changes
nothing. This matches the eleven mesh and continuation variants tried in earlier audits.

### The cell has two limits, 4.18× apart

At δ = 300 μm:

| quantity | value |
|---|---|
| substrate transport limit, `i_subcap = n_S F D_S C_S/δ` | **4.86** mA cm⁻² |
| mediator Fick limit | 10.17 |
| mediator k = 0 **with migration** | **20.31** |

and the two solver paths land on different ones: the **direct ramp settles at 5.4–5.9**, just above
the substrate limit, while **k-continuation climbs toward 18.16**, heading for the mediator limit.

### Why that might be physics rather than failure

Both numbers describe something real:

* **Product-forming current** is capped by how fast arene reaches the reaction front. Past ~5 mA
  cm⁻² the substrate cannot be supplied and the extra current makes Br₂ that does not react.
* **Total current** keeps rising to the Br⁻ transport limit (≥20.3) whether or not the substrate is
  there, because the electrode reaction is simply Br⁻ → Br₂.

Unstirred is the **only** cell where this bites: at δ = 15–100 μm the substrate limit is 3–20× larger
and never binds, which is exactly why the other five bromination cells converge cleanly at ×2.34
over their floors.

### What this means for the assertion added in §10c

`i_ec ≥ i_k0` was justified as "the homogeneous source can only ADD flux". That is true when the
substrate is in excess. **When the substrate is the bottleneck it is not** — the source cannot add
what cannot arrive. So the assertion is too strong for this one cell, and the right guard is
conditional rather than absolute.

Note this does not rescue `i_subcap` as a bound either: the earlier audit established that the
reaction front DETACHES from the electrode, which is why the direct ramp reaches 5.4–5.9 rather
than stopping at 4.86, and why the five converging cells exceed their own `i_subcap` comfortably.

### The decision

**Which current does the 50 × 6 matrix report for a mediated row — the product-forming one or the
total?** Every other cell in the set answers the same either way, because the substrate never binds.
This cell is where the two diverge, and the manuscript's question ("can this be driven at
25 mA cm⁻²?") is really about the product-forming current.

That is an author decision about what the table means, not a solver bug. Until it is made, this
cell should carry both numbers and neither should be counted toward a threshold.

### Does the ambiguity threaten a claim? Under the reading the manuscript needs, no.

| interpretation | value for this cell | clears 25 mA cm⁻²? |
|---|---|---|
| **product-forming current** (substrate-limited) | 4.86 (transport limit) to ~5.9 (front detached) | **no, by 4×** |
| total current (mediator-limited) | ≥ 20.31, not bounded above | undetermined |

The manuscript's question is whether a transformation can be *driven* at 25 mA cm⁻² — i.e. whether
product forms at that rate. That is the product-forming current, and under that reading this cell
fails the threshold by a factor of four, with the bracket [4.86, ~5.9] entirely below it.

So the count is robust to the unresolved value **provided the table is understood to report
product-forming current**. If it is understood as total current the cell is undetermined and must
be excluded from the tally rather than assumed either way.

That is why §15 is a definitional decision and not merely a numerical loose end: it is the
difference between a cell that safely fails a threshold and a cell that cannot be counted at all.

---

## 16. A cross-solver assertion that was itself the artefact

The floor test added at merge time (§10c) — `i_ec >= i_np`, on the reasoning that the homogeneous
source can only ADD flux — fired on **four** cells. One of them was real. The other three were the
assertion's own fault, and it is worth recording why, because it is the same mistake in a new
costume.

The reasoning is sound *against a k = 0 solve of the same system*. **It is not the same system.**
`run_all50_np.jl` builds four species for a row — carrier, product, supporting cation, supporting
anion. `run_mediated.jl` builds six for the same row — mediator reduced and oxidised, substrate,
H⁺, and the supporting pair. Different ionic inventories give different k = 0 limits, legitimately:
NHPI × RDE is 49.25 in one and 52.75 in the other, and neither is wrong.

I had spotted the risk and checked it on the bromination row, where the five converging cells
agreed at a consistent ×1.163 — and concluded the two solvers were comparable. They are, for that
row. They are not for NHPI. **One row agreeing is not the same as the models agreeing.**

The correct floor already exists and lives in the right place: `k0_floor` inside
`run_mediated.jl`, which solves the identical species set, mesh and boundary conditions with
`k = 0`. Every cell that fails it is flagged there. The merge-time version is removed.

That leaves exactly one genuinely unresolved cell rather than four — and the three false alarms
would have sent someone chasing solver bugs that do not exist.

---

## 17. The published matrix, on one physics for all 50 rows

    architecture   >=25      >=50      median
    natural        11/49      9/49       6.1
    stirred        18/50     15/50      17.1
    flow           20/50     15/50      19.4
    thingap        31/50     24/50      48.6
    rde            36/50     32/50     108.5
    rce            36/50     33/50     121.7

`natural` is out of 49 because Br⁻ oxidation × unstirred is written as NaN and excluded from every
count (§15). No other cell is excluded.

**What switching from the Tier-0 layer to full physics did**, holding the mediated overlay fixed:

| architecture | ≥25 Tier-0 → full | ≥50 Tier-0 → full |
|---|---|---|
| natural | 10 → **11** | 8 → **9** |
| stirred | 15 → **18** | 12 → **15** |
| flow | 17 → **20** | 12 → **15** |
| thingap | 30 → **31** | 22 → **24** |
| rde | 35 → **36** | 32 → 32 |
| rce | 35 → **36** | 33 → 33 |

Every count rises. That is the expected direction — migration can only help a charged carrier
reach the electrode — and it is why the orphaned matrix mattered: the published table had been
systematically understating the six charged non-mediated rows, and the effect on the tallies is
between one and three rows per architecture.

**The manuscript's v39 figures were 12/50 and 9/50 for natural convection.** The ≥50 figure of 9
survives; the ≥25 figure is now **11 of the 49 resolved cells**, with one cell excluded rather than
counted. Both numbers need restating in v40 with the exclusion stated explicitly.

---

## 18. The gate suite made the same mistake it was built to catch

`run_gates.sh` ran the twelve fast gates and reported **10 passed, 2 failed**. Two of the passes
were wrong:

| gate | reported | its own output said |
|---|---|---|
| G-COND | PASS | `G-COND: REVIEW NEEDED` |
| G-NUMERIC | PASS | `[FAIL] SI-claims: EC' flow >=50 (12, 15) vs SI 13->14` |

Neither script calls `sys.exit` with a status, so both return 0 whatever they conclude, and the
runner believed the exit code over the gate's own stated verdict.

This is precisely the failure the six new gates exist to prevent, committed by the thing that runs
them, at the last step of the night. It belongs in the same list as the others:

| what was checked | against what |
|---|---|
| EC′ acceptance | Fick, not Nernst–Planck |
| k-continuation anchor | its own Fick starting point |
| a stale Set name | a lookup that misses vs one that legitimately finds nothing |
| a runaway solve | "positive and finite" vs "converged" |
| an orphaned matrix | consistency between the wrong inputs |
| a cross-solver floor | one model's k = 0 against another model's |
| **the gate suite** | **exit status vs the gate's own verdict** |

### The first fix was wrong too

The obvious repair -- grep the output for `FAIL`, `REVIEW NEEDED`, `MISMATCH`, `ORPHAN`,
`UNRESOLVED:` -- turned 10/2 into **6 passed, 6 failed**, and four of the six new failures were
nonsense:

* **G-ORPHAN** was marked FAIL because its own success line reads
  `G-ORPHAN: PASS -- every solver artefact is consumed...` and contains the word *ORPHAN*.
* **G-MSCITE** was marked FAIL because a citation it listed happened to contain a matching token.

**A gate's name is not a verdict.** The rule now extracts the gate's own verdict LINE --
`^G-SOMETHING: (PASS|FAIL|REVIEW NEEDED|GOOD|BAD)` -- and believes that; only if a gate prints no
verdict line at all does the exit code, or a bare `[FAIL]` / `AssertionError`, decide.

That makes three versions of this check in one night: too permissive (exit code only), too
aggressive (keyword anywhere), then targeted at the thing that actually carries the meaning. It is
a small illustration of the same point as everything above -- a check has to be aimed at the
specific signal, not at something correlated with it.

**The two genuine failures are expected and are the v40 work:** `G-MSDERIVED` and `G-ECBAND` compare
the manuscript's and SI's printed counts against the model, and the model has just moved to full
physics (§17). They are supposed to fail until the text is restated. That is the gates working.

---

## 19. The built-in physics checks still hold after everything

Two cases in the 50-row set have answers that are known independently of the solver, and both
survived the night's changes to the electrode stoichiometry, the ion inventories, the diffusivities
and the merge:

| case | expected | rebuilt matrix gives |
|---|---|---|
| **neutral carrier** — migration must do *nothing* to an uncharged species | 1.000 | **1.00366** on all 43 such rows |
| **Cl⁻ in its own 1 M KCl** — Newman's binary limit for an anion in its own salt is exactly 2 | 2.000 | **2.0099** (0.5%) |

The neutral case is the sharper of the two as a regression test, because it is the same code path
that produces every migration factor in the table: if the electrode-direction rewrite (§3) or the
ion-inventory corrections (§5, §10b) had broken the charge bookkeeping, a neutral carrier would not
still come back at unity. The residual 0.37% is the trace product species, unchanged from earlier
audits.

The binary case is the one that caught §10a: it read **1.176** while the stale Set name was double
counting the chloride, against a limit that is analytically exactly 2. A check whose right answer
is known to three figures is worth more than a dozen that only compare the code to itself.

### And the analytic Jacobian still matches finite differences

`julia/probe_jaccheck.jl` compares every entry of the hand-derived Jacobian against central
differences across the production states — each mediated row at two architectures, both at a fixed
current and at a ramped one:

    worst relative disagreement anywhere: 2.686e-08  ->  ANALYTIC JACOBIAN VERIFIED

Nothing tonight touched the Jacobian itself, but a great deal changed around it — electrode
stoichiometry, species lists, ion inventories, the continuation anchors. This confirms the
Newton solve at the centre of all 348 cells is still differentiating the equations it is actually
solving.

---

## 20. The biggest uncertainty in the model is not a defect — and it is bigger than every defect

Two of the six architectures do not get δ from a correlation. They get a **fixed declared number**,
and the SI says so:

| archetype | δ used | SI's own justification |
|---|---|---|
| Unstirred batch | 300 μm | *"assumption; free-convection band 150–380 μm (Wilke, Eisenberg & Tobias, JES 1953)"* |
| Stirred batch | 100 μm | *"assumption; **no source**. Tested band 50–200 μm (Table S7g)"* |

`i_lim ∝ 1/δ`, so those bands propagate straight into the counts:

| archetype | δ | ≥25 | ≥50 | median |
|---|---|---|---|---|
| unstirred | 150 μm | **17**/49 | 11 | 12.2 |
| unstirred | **300 μm (used)** | **11**/49 | 9 | 6.1 |
| unstirred | 380 μm | **11**/49 | 8 | 4.8 |
| stirred | 50 μm | **29**/50 | 18 | 34.2 |
| stirred | **100 μm (used)** | **18**/50 | 15 | 17.1 |
| stirred | 200 μm | **15**/50 | 11 | 8.5 |

**The unstirred ≥25 count spans 11–17 and the stirred spans 15–29 across the bands the SI itself
states.** Every defect fixed tonight moved a count by one to three rows. This moves it by six and by
fourteen.

That is not an argument against the work — the defects were real and several were wrong by factors
of two — but it is the honest frame for reading the result:

* For **RDE, RCE, thin-gap and parallel-plate flow**, δ comes from a sourced correlation
  (Levich; Eisenberg–Tobias–Wilke, whose 0.0791 / 0.70 / 0.356 are verified against equation IX of
  the 1954 paper; Lévêque). There the precision of the transport model is what limits the answer,
  and tonight's corrections are the difference between right and wrong.
* For **unstirred and stirred**, the answer is dominated by a declared δ. Getting migration exactly
  right there is refining a number whose leading uncertainty is a factor of two elsewhere.

Both δ choices sit at the **conservative** end of their bands — 300 μm gives 11 rather than 17,
100 μm gives 18 rather than 29 — so the published counts understate rather than overstate. That is
the right direction, and it should be said out loud next to the numbers rather than left in a
correlation table.

**Recommendation for v40:** quote the two fixed-δ counts with their bands
(*"11 of 49, and 11–17 across the 150–380 μm free-convection band"*), or drop the fixed-δ
architectures from the headline tallies and keep them as illustrative. A referee who divides
`i_lim` by δ will find this in about a minute.

### The complete uncertainty budget — and why the counts are robust exactly where it matters

The four correlation-based archetypes also rest on a **declared operating point** (rotation speed,
channel gap, length, velocity). Scaling each over a 4× range, using the correlations' own exponents
(`δ ∝ ω^-1/2` for Levich, `∝ rpm^-0.70` for Eisenberg, `∝ u^-1/3` for Lévêque):

| archetype | parameter varied | ≥25 range | ≥50 range |
|---|---|---|---|
| RDE | 800–3200 rpm | 35 → **36** → 39 | 30 → 32 → 35 |
| RCE | 1500–6000 rpm | 34 → **36** → 39 | 30 → 33 → 35 |
| thin-gap | 5–20 cm s⁻¹ | 30 → **31** → 33 | 18 → 24 → 27 |
| parallel-plate | 2.5–10 cm s⁻¹ | 19 → **20** → 24 | 15 → 15 → 16 |
| **stirred** | 50–200 μm | 29 → **18** → 15 | 18 → 15 → 11 |
| **unstirred** | 150–380 μm | 17 → **11** → 11 | 11 → 9 → 8 |

**A 4× swing in RDE rotation moves its count by four rows. A 4× swing in the stirred film moves its
count by fourteen.** The pattern is not an accident:

* Where a column sits **well above** the threshold — RDE, RCE, thin-gap — most rows clear 25 with
  room to spare, so moving them further barely changes the tally. The count is robust *because* the
  claim is strong.
* Where a column straddles the threshold — unstirred, stirred — the count is exactly the number of
  rows within a factor of the line, so any shift in δ walks rows across it.

So the two architectures whose δ is a bare assumption are also the two whose counts are most
sensitive to it, and the four whose δ comes from a sourced correlation are the four whose counts
barely move. That is the reverse of what one would want, and it is the single most useful thing to
say about the model's uncertainty:

> **The transport ceilings are quantitatively trustworthy where they are high, and the
> forced-convection conclusions (RDE, RCE, thin-gap clearing 25 mA cm⁻² for ~2/3 of the set) are
> robust to a factor of four in the operating point. The unstirred and stirred counts are not
> ceilings so much as statements about where a declared film thickness puts the threshold.**

Nothing in this section is a defect and nothing here was hidden — every assumption is labelled in
the SI's correlation table. What was missing is the magnitude, and a referee will compute it.

---

## 21. G-KSENS: four mediated rows have ceilings that are not robust to their own rate constants

The eight mediated rows carry an order-of-magnitude rate constant each, and the SI says so —
for SCN⁻ it states outright *"NO direct rate measurement located — estimate by analogy to
halogenation"*. `data/sensitivity_rate_constants.py` perturbs each `k` by exactly the order of
magnitude that is claimed, one row at a time, and re-solves the mediated matrix.

| row | case | max change in that row | cells crossing 25 mA cm⁻² |
|---|---|---|---|
| **ACT-mediated alcohol oxidation** (flow, hectogram) | ×10 | **194.3%** | **5** |
| **HMF → FDCA** | ×10 | 178.1% | **3** |
| **HMF → FDCA** | ÷10 | 63.7% | **1** |
| **BQ-mediated Wacker–Tsuji** | ÷10 | 45.5% | **2** |
| **Aryl thiocyanation** | ÷10 | 24.3% | **1** |
| NHPI allylic C–H | ×10 | 169.1% | 0 |
| Br⁻ Hofmann | ÷10 / ×10 | 54.3% / 41.5% | 0 |
| Br⁻ bromination | ÷10 / ×10 | 30.8% / 57.3% | 0 |
| Cl⁻ ethylene epoxidation | ÷10 / ×10 | **0.1% / 0.3%** | 0 |

**Verdict: REVIEW NEEDED.** Four rows move a threshold under the uncertainty their own provenance
declares, and **ACT-mediated alcohol oxidation is the worst of them** — five of its six cells cross
25 mA cm⁻² if `k` is ten times larger. That row is the Stahl hectogram levetiracetam exemplar, one
of the set's flagship scale-up cases.

Two structural observations worth keeping:

* **Cl⁻ ethylene epoxidation is immune** (0.1%), because that row is transport-limited, not
  kinetically limited — its ceiling is set by chloride supply and the homogeneous step is never
  rate-controlling. A row's sensitivity to `k` is a direct read-out of whether its ceiling is a
  transport statement or a kinetic one.
* A large *change* does not imply a moved *threshold*: NHPI shifts 169% and crosses nothing, while
  thiocyanation shifts 24% and crosses one cell. What matters is where a row sits relative to the
  line, the same pattern as the δ budget in §20.

**These four rows' ceilings should not be quoted as transport limits without a real rate constant**,
because for them the number is reporting the kinetics estimate as much as the transport.
