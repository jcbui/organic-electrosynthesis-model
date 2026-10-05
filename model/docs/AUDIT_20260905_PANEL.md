# Three-reviewer audit of the modelling sections, 2026-09-05

Read as three referees at once -- a Newman-school multiphysics modeller, a Baran-school synthetic
chemist and a Jensen-school reaction engineer -- over the code that computes Sections 3-4, the
manuscript text (v65) and the built SI. Scope: every number, every citation, every physical
statement. Everything below was found by reading; nothing was found by a gate, which is the
point of recording it. Fixes shipped in **v66** and the rebuilt SI; the gate suite is the record
of what is now checked.

## What was wrong (in order of severity)

### 1. The ex-cell solver computed with a value the registry had withdrawn
`julia/run_excell.jl` carried `C_P = 5.0` mM. The registry row *Propylene C_sat (aq, 1 atm)*
withdrew that value on 2026-08-22 ("Where 4.9e-5 came from could not be established, so it is
withdrawn") and publishes 5.67 mM from Sander's H_cp = 5.6e-5 mol m-3 Pa-1. The solver also
carried `D_P = 1.2e-9`, a number that matches the registry's **Br2 (aq)** row and no propene row
(the registry's propene/H2O Wilke-Chang value, gated by G-DSUB, is 1.3663e-9). Every ex-cell
number the SI printed -- x_k = 167 um, the 0.58 mA cm-2 cap, 2.2 % in-film / 97.8 % exported,
2.9 mA cm-2, the ~130 um zone -- came from those inputs, and G-EXCELL, binding outputs only,
passed. Re-solved at the registry values: x_k 157 um, cap 0.75, 2.7 % / 97.3 %, 3.6 mA cm-2,
zone ~120 um; the halved-film split is 2.7 % / 97.3 % (measured now, not carried over). The
conclusion the passage exists for -- bulk-reaction-limited, substrate delivery is the binding
unit operation -- does not move.
**Fixed:** solver inputs are the registry's, emitted into `results/excell.json`; G-EXCELL binds
each input to its registry row (D_P to `data/mediated_substrates.csv`); the SI passage
interpolates every number from the JSON; the C_sat row's sensitivity interpolates the split.

### 2. Four manuscript numbers were stale or unpinned, one of them two corrections old
Fig. 4b: "the single exception (30 mM) reaches only **52.6**" -- the matrix gives **40.1** (the
Ni-homocoupling row moved with the z = 0 ruling; the caption did not). Fig. 4c: flat slopes
"-0.14 and **-0.24**" -- the model gives -0.22 (the slope fit spans the unstirred film, which
moved to 228 um). Body: "~1.7x ... ~20x" mediated intensification -- the matrix gives 1.6x and
17x (ratios at the retired 300 um film). None was pinned by any gate: they are neither counts
nor medians, the two shapes G-MSDERIVED was built around. **Fixed in v66; 15 pins added.**

### 3. The manuscript asserted the opposite of the SI section it cited
Section 4: the rotating-cylinder column is "an extrapolation that **does not inflate** it (SI
S3.3)". S3.3 has said since the Jang comparison that the second correlation gives 0.667-0.755x,
the RCE median falls 30 %, and one adjacent pair inverts. Same class as the v48 finding (SI
candid, MS confident), recurring on the newest SI material. **Fixed in v66**, and the phrase is
bound to `results/schmidt_extrapolation.json` (30.1 %).

### 4. A dangling cross-reference
"(Figure 4c; **Figure S1**; Table S6)": the SI figures are lettered C, E, F, H, K. Table S6
carries the matrix; the pointer is dropped. G-GHOST resolves SI section/table refs from the
MS, not "Figure S<n>"; that is a gap it still has.

### 5. Fig. 4 (d-f) published ">=" lower bounds from a solver path the SI had retired
The base-case panels were solved by the galvanostatic ramp (`run_ecprime_regimes.jl`), ended
on a Newton wall, and the caption called them "strict lower bounds (SI S5.5)" -- while S5.5 no
longer contains that method or that phrase. Re-solved by the production concentration-control
path: 41.80 / 23.98 / 1.19 mA cm-2 against the ramp's 41.83 / 24.01 / 1.19, all three reaching
the collapse criterion with the resting mediator at 0.14-0.57 % of bulk. Printed values are
identical to three figures; the ">=" marks become "=", one ratio moves 1.02 -> 1.03 in its
second decimal, Figure 4 re-rendered and re-embedded. Its footer now reads the same fact from
the artifact.

### 6. The SI described its own batch films wrongly, twice
S1.1 (iv): "for the two batch archetypes, [delta] is declared outright" -- the stirred film has
been *measured* since v58 and the unstirred *derived* since v64 -- and "the stirred-batch value
is one of the five entries whose band a stated conclusion depends on" -- the five are
3.0 M LiBr/THF, three design currents and Ea; the stirred film is not among them. Table S1's
caption called the unstirred value "an assumption" in the sentence that derives it. **Fixed.**

### 7. Edit history shipped in Table S7 behind a green G-VOICE
The unstirred row's sensitivity read "Adopting 228 um in place of the retired 300 um raises
the unstirred median from 6.11 to 8.01 ...". Same class as the sentence G-VOICE was written
for, in different words. **Rewritten as a sensitivity; G-VOICE gained the pattern and a second
control sentence (the one that shipped).**

### 8. The Newman objection: drho/rho is not an operator setting
The free-convection film was "derived" at one declared drho/rho = 3.16e-3 for all fifty rows.
Wilke, Eisenberg & Tobias define the driving force through a specific densification
coefficient, rho_0 - rho_i = alpha rho_i (C_0 - C_i), so at the limiting current it is fixed by
the bulk concentration of the species the surface depletes -- which spans 3.5 mM to 13.7 M
across the set. The RDE and RCE each have an *operating point* row (assumption) beside their
correlation row (measured); the unstirred archetype had none, so its declared inputs were
invisible in the registry. **Added:** *Free-convection operating point (unstirred batch)*,
assumption-class, with the one page-anchorable case computed in `free_convection_delta.py`
from CRC 97th ed. p. 5-129 (NaCl block, 20 C: rho 1.0707 at 10.0 %, 1.0781 at 11.0 %, so 2 M
interpolates to 1.0770 against 0.9989 on the 0.1 % row): drho/rho = 0.078, 25x the declared
centre, film 102 um at the central height. Direction stated (thinner for the concentrated
aqueous rows that carry the unstirred counts, thicker for millimolar organics); magnitude per
row deliberately NOT computed, because the coefficients are unavailable. Table S1's caption and
the derived row point at it. Ledger tier T1 (declared choice), as for the RDE/RCE rows.

### 9. Section 3's Tier 2 sentence contradicted its own paragraph and the figure
"Tier 2 ... recovers an order of magnitude" followed "each tier recovers a factor of two to
three" and precedes a model in which stirred -> flow is 2.1x. Rotating-cylinder electrodes were
listed under Tier 2 while Fig. 2 and the v57 tier bands put the rotating cylinder (at the
model's 3000 rpm) in Tier 3. **v66:** "roughly doubles the median ceiling (9 -> 19 mA cm-2)",
pinned; Tier 3 now names the fast-rotation route and the Figure 2 cylinder. The Tier 2 list is
left as it was -- a rotating cylinder at low speed does sit in Tier 2 (delta ~ omega^-0.7).

### 10. Rounding consistency
Fig. 2c printed D = 1.39e-9 with a 13.5 mA cm-2 ceiling; the printed inputs give 13.4. The
solve used 1.3944e-9; four figures are printed now and the value is pinned to the solver's
constant.

### 11. Attribution wording (Leow)
The ex-cell passage read "the chloride-mediated propylene epoxidation of Leow et al., where
2 M Cl- is oxidized". Read from the paper: the headline runs are ethylene in 1.0 M KCl at
300 mA cm-2 (p. 1229); the chloride optimum of 2.0 M is set on plant-gate cost (Fig. 3B); the
propylene runs are Fig. 2E. The passage now states those three facts and calls the solved
system what it is -- Leow's optimum chloride with propylene at its registry solubility.

## What was checked and found sound
- Every reference in MS Sections 3-4 (22-34) and all 84 SI references resolve to real records
  (G-MSCITE, G-SIBIB); Eichner is ref 31, Suryanto ref 30, Li (Chorkendorff) in text.
- `correlations.jl`: Leveque 1.85 is the exact one-active-wall Graetz-Leveque coefficient
  (derived from wall shear 6u/h); Levich 1.61 as printed; Eisenberg definitions and window as
  printed on p. 313; the free-convection form is the source's own Eq. XVII.
- `npp.jl` / `npp_ecprime.jl`: textbook dilute-solution Nernst-Planck with electroneutrality;
  the EC' source and the Saveant limits; charge bookkeeping (G11) and the binary-electrolyte
  factor of 2 (G2, G8a, and now the ex-cell path to 0.10 %).
- The eight mediated SPECS: stoichiometry and charge balance per system checked by hand (BQ
  two-electron couple; NHPI anion; HMF borate buffer; ACT carbonate buffer). Spectator D values
  are aqueous transfers where the row says so; the binary-electrolyte factor is D+-independent,
  so they cannot move a ceiling.
- `thermal_model.py`: the irreversible heat is two Butler-Volmer overpotentials at alpha = 0.5
  plus ohmic; entropic heat and evaporation excluded and declared; boiling points CRC.
- `reactions_50.csv` row by row for n_carrier plausibility: the two fractional rows (n = 0.1 and
  0.2) are declared mechanistic choices with a sensitivity that keeps both below 25 mA cm-2 at
  n = 1 in every architecture.

## Closed on author instruction, same day (v67)
- **Ethylene's diffusivity is measured and cited.** The Cl-/ethylene row now carries
  D = 1.87e-9 m2 s-1 from Cussler, *Diffusion* 3rd ed., Table 5.2-1 p. 127 ("Diffusion
  coefficients at infinite dilution in water at 25 C", Ethylene 1.87e-5 cm2 s-1), read from the
  page raster with Bromine 1.18 on the same page as the control; a registry row *Ethylene (aq)*
  (measured) carries the locator, and `build_mediated_substrates.py` records the Wilke-Chang
  estimate for ethene (1.74e-9, 7 % low) beside it. Re-solved: 44 of 48 mediated cells
  bit-identical, the four ethylene c-control cells +0.10 to +0.15 %, no median or count moved;
  Figure 4 re-embedded for its panel (c) trace. Table S6 and S5.5 no longer call the row
  "chloride/propylene".
- **Figure 3a is drawn at the model's own films.** `run_profiles.jl` now solves the convective
  profiles at the archetype MEDIANS (rotating cylinder 11 um, 250 um-gap cell 30 um, parallel-plate
  flow cell 76 um), computed from the same correlations and table Fig. 2b uses, so the two figures
  name the same reactor for the same film; five curves, every label read from the solve, and
  G-MSDERIVED cross-checks the Julia medians against `model_medians.delta_median`. The flow cell
  at 50 mA cm-2 is nearly exhausted (c_surf = 0.21), which the old round-film panel never showed.
- **"Leow's 300"** is Leow et al.'s operating current density: 300 mA cm-2, the condition of their
  headline 70 % faradaic efficiency (and of the 0.5/1.0/2.0 M chloride series). The ex-cell
  partition is evaluated at 131 mA cm-2, one third of the analytic carrier limit at the 200 um
  film, because the concentration-controlled branch at that film ceases at 207 mA cm-2 (the
  lumped oxidant reaches molar concentrations the model has no solubility ceiling for), so
  300 mA cm-2 is not reachable on the modelled film; the SI states the choice. Left as is.

- **Two consequences of the swap, caught by the first v67 suite run and fixed structurally.** The
  ex-cell solver's propylene D lost its backing row when the substrate table's propene row became
  ethylene; a derived *Propylene (aq)* registry row (Wilke-Chang, arithmetic stated) now carries it
  and G-EXCELL binds to it. The S5.2 termination census was typed and drifted with the re-solve;
  it is computed from the matrix now, and the census counts cells that reach the 10^-3 criterion
  exactly (no plateau value recorded) AT the criterion -- both the SI and G-ECBAND had been
  skipping them, undercounting the "at or below 0.28 %" share (35 -> 39 of 48).

- **The SI's stated reason for the 200 µm branch failure was wrong, and the failure was a solver
  defect** (author's question: "is it because their cell operates supersaturated?"). The 5.8 M
  oxidant state it blamed is δ-independent and is reached at 25 µm. Bisection (reaction, substrate,
  k, mesh at either edge, proton mobility) moved nothing; δ alone did. Cause: the per-species
  residual scale used the BULK concentration, so the trace-in-bulk, molar-at-electrode oxidant's
  equations sat at the floating-point floor against the absolute 10⁻⁹ tolerance on thick films.
  Fixed in `npp_ecprime.jl` (scale includes the in-film maximum): 200 µm reaches 392.0 mA cm⁻² =
  2.001× Fick, δ-continuation converges on every film, 48 production cells unchanged to < 10⁻⁴ %,
  all manuscript figures byte-identical. SI S4 and S5.2 rewritten; numerics row added. Leow's
  cell is a flooded Pt-foil/IrO₂-mesh anode in a sparged, AEM-divided flow cell — thin chloride
  film, chlorine leaving as gas — not a GDE and not supersaturated.
- `npp_ecprime.jl` carried byte-identical duplicate definitions of `regrid` and
  `solve_ilim_ec_continued`; removed.

- **G-DSENS could not fail.** It printed "read the count lines" and exited 0; the runner trusts a
  gate's own PASS/FAIL line and falls back to the exit code only when there is none. It now asserts
  identical counts and < 10⁻⁶ relative change under ×⅓/×3 and writes `unsourced_D_sensitivity.json`.
  The 24 "unsourced" slots are supporting-ion diffusivities in solvents without tabulated λ°
  (~20 ion/solvent pairs); their basis now reads "declared class default (supporting ion: carries
  no flux, so its D does not enter i_lim)", and a registry row plus an S3.1 paragraph state the
  count, the defaults, the reason and the sweep's result, all interpolated.
- **The carrier charge z was not printed anywhere in the SI**, though it is the switch on the
  migration term and `carrier_charge.csv` records z, source, basis and confidence for all 50 rows.
  Table S2 now carries a z column (medium-confidence rows starred), its caption names the four
  medium rows and interpolates the G-ZSENS result (≤ 3.0 %, no count moves; the build throws if
  that stops being true), and a category-4 registry row carries the census and the four bases.

- **`--all` sweep (14:54–22:15): 98 passed, 3 verdict-class failures.** G-KSENS: a tenfold change in
  k moves a 25 mA cm⁻² threshold on four mediated rows (ACT ×10 in all six architectures; HMF;
  BQ; SCN⁻) — a real ±1-per-architecture exposure of the headline integers that the SI had
  argued around rather than measured; now measured on the published 300-cell matrix (four rows cross
  25: ACT ×10 in all six architectures, HMF ÷10/×10, BQ ÷10, SCN⁻ ÷10; five cross 50; the ≥25 and ≥50
  counts of any architecture move by at most ±1 from any one rate constant; ordering preserved),
  written to an artifact, interpolated in S5.5 and the registry, and gated (G-KSENS-SI, fast tier). G-DSUBSENS: no count moves at ×0.7–1.3, but
  the registry sentence quoting it was typed against the retired 300 µm film (bromination ×
  unstirred "25.34" is 33.34 now); artifact + interpolation added. G-EXEMPLAR/-2: REVIEW is their
  standing census (38/9/2/1), Crossref ranking artefacts, conditions verified from PDFs by G-COND.
- **The supporting-ion table was not reproducible from its generator**: Cathodic Giese's H⁺
  cation carried Na⁺'s diffusivity under a CRC state-A basis. Spectator, no number moves; corrected,
  NP layer re-solved, generator now covered by G-REGEN.

## Left open, deliberately
- `thermal_model.py`'s docstring lists "MeCN T_boil 82.0 -> 81.6" among revisions "deliberately
  NOT applied"; 81.6 IS applied. Internal docstring only.

## Gates added or changed
G-EXCELL (inputs bound to the registry; phrases to the interpolated SI; control perturbs an
input), G-VOICE (+3 patterns, +1 control sentence), G-MSDERIVED (+15 pins, wall-wording
direction check), G-SIBOUNDS (+14 declared exemptions), G-FREECONV (page-anchored drho/rho
illustration in its JSON), G-REGEN (two new registry inputs). `run_ecprime_regimes.jl` writes
`path` and `c_red_surf_norm`; `run_excell.jl` writes `inputs`, `half_delta_um`,
`infilm_pct_half_delta`, `exported_pct_half_delta`.

## Closure, 2026-09-06
- Post-sweep chain 2 (relaunched 22:23, EXIT 0 at 02:14): NP layer re-solved after the Giese
  correction, 300 of 300 cells bit-identical, counts unchanged; G-DSENS PASS (24 slots, 21 pairs,
  max relative change 0.0); G-KSENS artifact written (4 rows cross 25, 5 cross 50, max count delta
  ±1 / ±1, ordering preserved); G-DSUBSENS PASS (closest cell 8.6 % from 25); registry, liveness,
  ledger and SI rebuilt; eight figures rendered; fast suite 96 passed / 0 failed / 6 skipped.
- The four manuscript renders (Figs 2, 3, 4, 6) are md5-identical to the artwork embedded in v67:
  no re-embed; v67 stands as the current manuscript.
- Proof-read of the rebuilt SI from the built .docx found six prose defects (a measured zero printed
  as "0.0e+0%", "the row below" for a same-row sensitivity, "Two ... The third", a sentence-initial
  numeral, an unbound 0.02 mol m-3 seed typed twice, an unreproduced "order 10^6"). All fixed at
  source; the seed is now emitted by run_excell.jl and bound by G-EXCELL; ledger 0 tier moves;
  suite 96 / 0 / 6; verify_v67 31 / 0 with its control firing exactly its 9; run_audit.jl 16/16
  (run_audit_20260905_rscale.log, post-dating the residual-scale edit).
- Closed 2026-09-06 on the author's "Fix all": the thermal_model.py and make_figK.py docstrings
  (81.6 C IS applied; the other two listed revisions are not); the duplicate `newton_ec_ccontrol!`
  (second byte-identical copy removed; audit 16/16 with every gate line identical; the 300-cell
  layer re-solved through the deduped file 300/300 bit-identical); and npp.jl's residual scale,
  now the same per-species rule as npp_ecprime.jl. npp.jl does not solve the 300-cell layer
  (run_all50_np.jl includes npp_ecprime.jl at k = 0); its real consumers were each re-run: audit
  gate lines identical, tier0_matrix / npp_support_sweep / cellvoltage / Fig. 3a profiles
  byte-identical, Fig. 2c median profiles <= 3.9e-6 relative, Fig. E profiles 8e-15 (Fig. E
  re-rendered, 332 px differing by one unit; every other PNG byte-identical). The published
  layer's exposure to the EC-prime scale rule was measured in an isolated copy with the old rule
  restored: 300/300 bit-identical. Suite 96 / 0 / 6, verify_v67 31 / 0 (control 9 of 9),
  manuscript artwork identical to v67. G-EXEMPLAR / G-EXEMPLAR2 REVIEW stays as the standing
  census (author ruling). Nothing is left open by choice.
