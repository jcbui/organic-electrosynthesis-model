# Strict provenance audit of the CODE, 2026-08-24

The existing gates check the registry against the published prose. **Nothing was checking that the
SOLVERS compute with the values the registry publishes.** This audit enumerates every numeric
literal in the hand-written production chain and forces each into a defensible category.

## Scope and scale

| | |
|---|---|
| literals in the whole data-producing chain | 7,930 |
| of those, in hand-written solver/method code (the rest are the registry generator, which IS the provenance record, and generated files) | 1,489 |
| non-structural (after removing indices, exponents, 0/1/2, unit conversions) | **554** |

## Findings

### 1. `npp.jl` never received two fixes its twin got — and it is what the audit gate runs on

`npp_ecprime.jl` had two defects found and fixed on 2026-08-23. `julia/npp.jl` is its twin and was
missed:

| | `npp_ecprime.jl` (fixed 08-23) | `npp.jl` (was still wrong) |
|---|---|---|
| Newton acceptance | `< tol` (1e-9, as declared) | **`< 1e-6`** — 1000x looser than its own signature |
| concentration clamp | `clamp(u, -300.0, 50.0)` | **`clamp(u, -50.0, 50.0)`** — the floor found to bind and zero Jacobian columns |

This matters more than it looks: `npp.jl` is what **audit gates G1–G4** run on — the gates that
validate the migration physics (Fick limit, Newman binary doubling, `c_surf/c_bulk = 0.500`, mesh
drift). The registry separately publishes "Newton tolerance ||F||_inf = 1e-9", so this was a
registry-versus-code violation, not merely an internal inconsistency.

**Fixed. `run_audit.jl` re-run: 16/16 gates still pass**, and G3 now reports `(converged)`.

### 2. The Levich coefficient in the code and in the registry disagreed

`julia/correlations.jl` computes with **1.61**; the registry published **1.613**.

The registry had DERIVED 1.613 as `1/0.62` from the RDE mass-transfer constant. That is
arithmetically fine but propagates a rounding: 0.62 is itself 2 significant figures, and
`1/0.62 = 1.6129` where `1/0.62048 = 1.6117`. So 1.613 asserted precision its own input never had.

Resolved by **retrieval, not argument**: the source PDF is in `papers for model/`. OCR strips the
constants from eqs. 9.3.24/9.3.25, but the Sect. 12.4 zone-diagram passage survives and prints
`delta^2/D = (1.61)^2 nu^(1/3)/(omega D^(1/3))` — algebraically exactly
`delta = 1.61 D^(1/3) nu^(1/6) omega^(-1/2)`. **The source prints 1.61.**

Registry and SI corrected to 1.61, matching the code. **No computed number changed.** Bounded by
direct recomputation at all three candidate values:

| coefficient | RDE median | >=25 | >=50 |
|---|---|---|---|
| 1.61 (published, code) | 108.489 | 36/50 | 32/50 |
| 1.6117 (exact) | 108.374 | 36/50 | 32/50 |
| 1.613 (retired) | 108.287 | 36/50 | 32/50 |

0.186% end to end and **the counts are identical in every case**.

### 3. `K+` — the registry published a value the solver does not use

`run_mediated.jl` uses **1.96e-9**; the registry published **1.9e-9**, and its own method note said
so outright: *"lambda0 = 73.5, z = 1 (K+ rounded 1.957e-9 -> 1.9e-9)"*. A 2-significant-figure
rounding 2.9% below both its own derivation and the code.

Corrected to 1.96e-9. Immaterial to results — K+ is a spectator (`s = 0, nu = 0`) in the only spec
that uses it, and a non-reacting species' D cancels from its own Nernst-Planck equation (verified
by perturbation earlier: x10 and /10 leave `i_lim` identical to 6 decimals) — **but a published
value must be the value used.**

### 4. Two solver species had no registry row at all

`H+` at 2.0e-9 (AcOH/HCOOH, aryl thiocyanation) and `B(OH)3` at 9.6e-10. Both added.

`H+` is instructive: a value-only audit bound it by coincidence to the unrelated
`NH4+ (MeCN, used aq-like)` row, which also reads 2e-9 — **exactly the wrong-row binding of trap
11**, and the coincidence was concealing a genuinely missing row. Both species are spectators, so
nothing reported moves.

### 5. The registry cited a stale gate count

Category-11 rows cited *"audited: run_audit.jl, 14/14 gates"* and *"all 14 audit gates pass"*.
The audit is **16/16**. Corrected.

### 6. `NEGLIGIBLE_C` had no registry row

The trust-region threshold introduced on 2026-08-24 was a live solver constant with no provenance
row. Added to category 11 with its ten-decade sweep as the stated sensitivity.

### 7. FIXED — the 8 mediated substrate diffusivities were published as `derived` but were not reproducible, and three were wrong

The registry publishes *"8 mediated-spec substrate D values"* as class **derived**, method
*"Wilke-Chang on named surrogate structures in the VERIFIED exemplar solvents"*.

But `OERxn` has **no substrate-D field** (it carries the CARRIER D and the substrate
CONCENTRATION), `build_reactions50.py` computes none, and the eight values are **hand-typed into
`run_mediated.jl`**. Nothing reproduces or checks them.

The standard's own test for state B is *"the arithmetic reproducible from the registry alone"*.
This fails it — the same defect Casteel-Amis had before it was implemented.

And unlike the spectator diffusivities above, **these are material**: `D_S` sets `i_subcap` and
enters the EC' source term.

Values affected: 6.25e-10, 6.91e-10, 7.22e-10, 9.52e-10, 1.17e-9, 1.37e-9, 1.78e-9, 2.00e-9.

**Two ways to close it**, and the choice is the author's:
1. add the 8 surrogate SMILES to `build_reactions50.py` so `wilke_chang()` regenerates them — but
   3 of the 8 names are ambiguous (`levetiracetam-alcohol`, `sesquiterpene-core`, `naproxen-arene`)
   and writing SMILES for those would be inventing a modelling input; or
2. reclassify the row to `assumption` with a stated sensitivity.

`data/sensitivity_substrate_D.py` (**G-DSUBSENS**) was written to supply that sensitivity either
way: it perturbs all eight together and reports whether any published count moves. It never touches
the production solver — it patches a copy and redirects the output.

**RESOLVED 2026-08-24.** `data/build_mediated_substrates.py` now generates all eight by
Wilke-Chang from a NAMED structure in a NAMED solvent into `data/mediated_substrates.csv`, and
**G-DSUB** asserts the solver carries them in BOTH places it uses them (the MedSpec `D_S` field and
the `S("Sub")` species entry -- independent literals that can drift apart). **G-SPECIES now passes.**

Inverting Wilke-Chang gives the Le Bas volume each typed value implies; the inversion was
round-tripped against `lebas_volume()` on five structures and agrees to 2 dp. **Five of the eight
reproduced the carried value exactly** (ratios 1.000, 0.997, 1.000, 1.002, 0.999), which confirms
both the structure and that the method really was Wilke-Chang for those rows.

**Three did not, and were read out of the exemplar PDFs** -- necessarily, because a
3-significant-figure D does not identify a structure uniquely (4-fluorobenzamide V = 137.40 and
cyclopentanecarboxamide V = 135.90 both reproduce 2.00e-9 to 3 s.f.):

| reaction | substrate, from the paper | was | now | error |
|---|---|---|---|---|
| Hofmann | **2-phenylacetamide 1a**, 0.4 M (op3c00332.pdf) | 2.00e-9 | 1.861e-9 | 7.5% high |
| NHPI allylic | **valencene (4)** -> nootkatone (nature17431.pdf) | 1.78e-9 | 1.945e-9 | 8.5% low |
| bromination | **anisole** (s41467-025-57329-0.pdf) | 6.25e-10 | 9.148e-10 | **46% low** |

The bromination row's surrogate had been MISNAMED "naproxen-arene"; the exemplar brominates
anisole. The reading is confirmed arithmetically from the paper's own scale-up: "Substrate
(4 mmol), solvent (0.5 M NaBr in deionized water (10 mL): CH3CN: CH3OH: CH2Cl2 = 10:10:10:3)"
gives 4 mmol / 33 mL = 0.1212 M = `C_sub` exactly, and 0.5 M x 10/33 = 152 mol/m3 = the carrier
exactly.

A second naming point fell out: `propene` reproduces its value at 0.997 while ethylene gives 1.272,
so the registry's substrate name is right and the REACTION LABEL "Cl-mediated ethylene epoxidation"
is the loose one.

**Consequence, and it runs the other way from the usual:** with the correct substrate the
bromination x unstirred cell reads 25.341 rather than 23.749 mA cm-2 and CLEARS the 25 threshold,
so the unstirred count returns to **12/50 -- which is what the manuscript already prints**. One
planned v40 edit is therefore WITHDRAWN, and `check_ms_derived.py`'s pinned expectation of
`"11/50"` was itself the stale thing. 46 of 48 mediated cells moved (bromination +6.7%, Hofmann
-6.1%, the rest under 0.2%); no other threshold was crossed and no median changed.

### 8. FIXED — four solvent boiling points set published Fig. 5 numbers and had no provenance at all

`figs/thermal_model.py` hardcoded THF 66, MeCN 82, DMF 153 and aq. NaOH 100 deg C. `solvents.csv`
carries M, mu, rho and phi but **no boiling point**, and the registry had **no T_boil row**. Every
other constant in that file — H_EXT, all five sigma, all four h_int, all five i_design, all three
cooling bands, the vessel area — has a registry row and matches it. These four did not, and they
are not decorative: they enter as `(T_boil - T_amb)` and set the boil-off ceilings that
G-MSDERIVED checks (THF 29, MeCN 88, DMF 89, aq. NaOH 283 mA cm-2).

Retrieved 2026-08-24 from the CRC 97th ed. PDF in `Model Papers for Params/` — the same Sect. 15
table `solvents.csv` already cites for mu and rho — with a layout-preserving extraction so the
columns stay aligned. Molecular weights on the same rows (41.052 / 73.094 / 72.106) match
`solvents.csv` exactly, which pins the read:

| solvent | CRC printed | code uses | ceiling shift if the printed value were adopted |
|---|---|---|---|
| Tetrahydrofuran | **66.0** | 66 | +0.000% |
| Acetonitrile | **81.6** | 82 | -0.702% |
| N,N-Dimethylformamide | **152.8** | 153 | -0.156% |
| Water | **99.974** | 100 | -0.035% |

All four now registered as `measured` with that locator, recording both the printed value and the
rounding the code uses, with the per-solvent bound above as the sensitivity.

**Not changed in the code.** Adopting the printed values would alter a published figure input and
require re-rendering Fig. 5; that is an author decision, and no manuscript number turns on it — the
caption's 88 and 89 mA cm-2 round identically either way. For 1 M NaOH the pure-water boiling point
is used; the real solution boils ~0.5 K higher, so 100 deg C is the CONSERVATIVE choice for a
boil-off ceiling.

## New gates

| gate | what it asserts |
|---|---|
| **G-CODECONST** | every physical constant hardcoded in the solvers equals its registry value. Both sides are READ FROM FILES — neither is typed into the gate, so it cannot go stale when a number moves (trap 14). 16 constants checked. It also asserts the Newton convergence test compares against the declared `tol`, never a literal — because the value check alone reads the signature default, which said 1e-9 the whole time npp.jl accepted at 1e-6, and would have passed the very defect it exists to catch. |
| **G-SPECIES** | every `(species, D)` pair in `run_mediated.jl` resolves to a category-4 registry row matched on **name AND value**, or to a generated carrier D in `reactions_table.jl` (a declared indirection that G-MEDSYNC separately gates). The 8 substrate values are reported as their own category rather than passed or exempted into silence. |

Both are negative-controlled: perturbing the code side makes each fire on exactly its own check.

**G-CODECONST caught the repository's recurring trap on its first run** — it reported both solvers
as violations because the comments documenting the fix quote the retired code verbatim
(``This read `norm(Fv, Inf) < 1e-6```). Prose quoting what it withdraws, read as the thing itself:
the fifth time this has bitten a gate here. It now strips comments before scanning.

## What was checked and found sound

* All correlation coefficients — Levich, Leveque 1.85, Eisenberg 0.0791/0.70/0.356 — carry
  registry rows with citations, and after finding 2 the code now matches all of them.
* All reactor geometry and operating points (delta archetypes, rpm, gaps, lengths, velocities).
* Physical constants F, R, T and the reporting thresholds.
* Voltage-stack parameters E0, Tafel b, i0.
* All 7 pre-existing numerics rows, plus the new one.
* 28 of 36 solver species diffusivities trace cleanly; the remaining 8 are finding 7.
