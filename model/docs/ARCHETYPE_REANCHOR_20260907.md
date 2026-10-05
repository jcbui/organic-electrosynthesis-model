# Re-anchoring the flow archetypes to measured films (2026-09-07)

Author instruction (Justin, 2026-09-07): "sweet yeah let's do it, then we also need a cool
schematic for the ANEC cell too for panel a but let's go and re-run everything ... fully
autonomously", after establishing that both flow-archetype operating points were declared
conventions with no source, that Mo 2020's SI had been on disk since 2026-08-31, and that
Watkins 2023 (SI Table S1) measures four cells' boundary layers by the ferricyanide method.

## What was wrong

The model's two flow archetypes were Leveque evaluations at DECLARED operating points:

| retired archetype | key | declared point | film it computed (per row) |
|---|---|---|---|
| Parallel-plate flow (1 mm) | `:flow` | gap 1 mm, L 5 cm, u 5 cm/s | 38-95 um, median 76 |
| Thin-gap microflow (250 um) | `:thingap` | gap 250 um, L 2.5 cm, u 10 cm/s | 21-38 um, median 30 |

The gap of the second came from a real paper (Watts, Gattrell & Wirth 2011, a 254 um FEP-spacer
microreactor), but its length and velocity were declared, and the 1 mm cell's velocity had once
been attributed to a source (Perry, Ponce de Leon & Walsh 2020) that states no velocity at all
(attribution withdrawn 2026-08-22, row kept as an assumption). Both were state C with
sensitivities and were disclosed in SI Table S1 and S7, so nothing was hidden -- but "measured
displaces declared" had been applied to the two batch films (v58, v64/v65) and never sought for
the flow films, although Mo's SI (`papers for model/aba3823_mo_sm.pdf`) had been in the tree
since 2026-08-31. That is the miss the author asked about ("How come you didn't catch before
these were made up?"); the declared-values audit (`docs/DECLARED_VALUES_AUDIT_20260907.md`)
is the remedy.

## The seven archetypes now

| key | label | film | state | source (locator) |
|---|---|---|---|---|
| natural | Unstirred batch | 228 um | derived | Wilke, Eisenberg & Tobias 1953, Eq. XVII (unchanged) |
| stirred | Stirred batch | 200 +/- 7 um | measured | Williams ... Manthiram 2019, p. 1227 (unchanged) |
| flow | Recirculating flow cell | 106.9 um | measured | Watkins et al. 2023, SI p. 6, Table S1, "Parallel H-cell (280 uL/s)" |
| anec | ANEC flow cell | 36.2 um | measured | same table, "ANEC (140 uL/s)" |
| micro | Microfluidic cell (25 um gap) | 12.5 um | derived | Mo et al. 2020, SI p. 13: 0.001 in FEP spacer; Table S1 tau = 4 min |
| rde | RDE 1600 rpm | Levich | unchanged | |
| rce | Rotating cylinder 3000 rpm | Eisenberg | unchanged | |

Watkins, Schiffer, Lai, Musgrave III, Atwater, Goddard III, Agapie, Peters & Gregoire,
"Hydrodynamics Change Tafel Slopes in Electrochemical CO2 Reduction on Copper", ACS Energy Lett.
2023, 8, 2185-2192, DOI 10.1021/acsenergylett.3c00442. SI Table S1 (p. 6), read from the PDF at
`papers for model/concentrations/SIs/final upload/zotero uploads/Final final/other cells/`:

| cell (flow rate) | experimental (um) | COMSOL (um) |
|---|---|---|
| Ager et al. H-cell (20 sccm) | 177.9 +/- 21.6 (n = 6) | -- |
| Parallel H-cell (280 uL/s) | 106.9 | 242 |
| Angled H-cell (280 uL/s) | 33.4 | 128 |
| ANEC (140 uL/s) | 36.2 | 57 |

Method (Figure S2, same page): constant-potential ferricyanide reduction in the mass-transport
limited regime, delta = n F D C* / i_ss with D = 0.720e-5 cm2/s and C* = 10 mM. Only the Ager
cell carries replicate error, 12.1 % of its mean; that scatter is the band applied to the other
two adopted values, declared as a transfer in their registry rows.

**A trap met while writing the citation.** The first comment written into `correlations.jl`
listed the authors from memory ("Watkins, Wu, Lee, Ross, Toste & Gregoire") and a title that
belongs to no paper. The SI's first page, read minutes later, gave the real author line and
title; the comment was corrected before anything was built on it. Every author line in this
pass was then read from a PDF page, not recalled.

### The microfluidic film, derived from two printed numbers

Mo's SI p. 13: the optimisation experiments "were conducted in a small-scale electrochemical
flow cell with the thinnest FEP spacer (0.001", 25 um)", and Table S1 on the same page prints
tau = 4 min for entries 9-12 (entry 12 is the published optimum). With u = Q/(w h) and
Q tau = w h L, the Leveque group Re Sc d_h/L = 4 u h^2/(D L) reduces to **4 h^2/(D tau)**, so no
channel width or length is needed. At h = 25 um and tau = 240 s that group is 1.0e-11/D, i.e.
0.003-0.06 across the fifty rows, and the entrance Sherwood number 1.85 (4h^2/(D tau))^(1/3) is
far below the fully-developed value of 4 (delta = h/2) for every row. The half-gap floor the
model has always applied therefore binds for all fifty: **delta = 12.5 um, independent of D and
nu**. (An early hand calculation put the Leveque group three decades too high, at ~10, and
concluded the film would be D-dependent; the Julia evaluation over the fifty rows corrected it
before any code shipped.) Over Table S1's printed tau range 4-12 min the film does not move, so
its band collapses onto the value.

## Retired registry rows, verbatim

From `data/build_param_tables.py.bak_pre7arch_20260907`:

```
add("7. Reactors", "Parallel-plate flow-cell geometry", "gap 1 mm, L 5 cm, u 5 cm/s", "-",
    "assumption",
    "a declared laboratory operating point. Corrected 2026-08-22 on retrieval of the source: this row claimed the 5 cm s-1 was 'anchored to real hardware -- a C-Flow cell is documented at a typical electrolyte linear flow velocity of 1-10 cm s-1'. Perry, Ponce de Leon & Walsh does show the C-Flow cell in Fig. 1, but the paper contains no linear flow velocity at all: the strings 'flow velocity', 'linear flow' and '1-10' do not occur in it. The velocity range was therefore attributed to a source that does not state it, and the attribution is withdrawn. Gap, length and velocity are all declared conventions; the Perry citation supports only that this cell architecture is real and in current laboratory use",
    "Perry, Ponce de Leon & Walsh, J. Electrochem. Soc. 2020, 167, 155525", "Fig. 1 caption",
    "delta ~ h^(2/3) L^(1/3) u^(-1/3). Tested gap 0.5-2 mm and u 1-10 cm s-1: delta spans about "
    "2.5x, so the flow-cell median moves roughly 8-50 mA cm-2 about the reported 20. The flow cell "
    "stays between the stirred beaker and the thin-gap cell throughout, so the ladder ordering "
    "holds; the >=25 and >=50 counts move with it and are reported only at the declared point.")
add("7. Reactors", "Thin-gap microflow gap", "250", "um", "measured",
    "the canonical thin-gap organic-electrosynthesis geometry, independently documented twice: a "
    "254 um FEP spacer in a 3 x 30 mm channel (23 uL) electrosynthesis microreactor, and '250 um in "
    "flow' against 1 cm in batch, with an 80 um gap demonstrated for an ortho-quinone synthesis",
    "Watts, Gattrell & Wirth, Beilstein J. Org. Chem. 2011, 7, 1108-1114, DOI 10.3762/bjoc.7.127; "
    "Noel, Cao & Laudadio, Acc. Chem. Res. 2019, 52, 2858-2869",
    "Beilstein J. Org. Chem. 2011, 7, 1108-1114 (FEP spacer, 254 um); Acc. Chem. Res. 2019, 52, "
    "2858-2869, section 'Bringing the Chemicals to the Electrodes'",
    "Best-anchored geometry in the model: both locators name a specific gap in a specific reactor.")
add("7. Reactors", "Thin-gap microflow operating point", "L 2.5 cm, u 10 cm/s", "-", "assumption",
    "a declared laboratory operating point for the 250 um cell", "declared operating point", "",
    "delta ~ L^(1/3) u^(-1/3). Tested L 1-5 cm and u 5-20 cm s-1: delta spans about 2x around the "
    "computed 21-27 um. The payoff-map archetype "
    "bands are not hardcoded at x_hat = delta_batch/delta = (2.5,3.5) stirred, (5,15) flow and "
    "(30,100) 'thin gap / RDE / RCE', which overstated thin-gap intensification by roughly 2.5-3x -- "
    "the model's own Leveque evaluation of this archetype gives 21-27 um, i.e. x_hat ~ 11-14, inside "
    "those figures' 'flow' band, and nothing in the 50-reaction set reaches x_hat = 100. The bands "
    "are computed at runtime from the reaction table and the mass-transfer correlations, and the "
    "Stage-0 matrix is re-derived from that same transcription and asserted to agree with the "
    "published matrix, so the bands cannot drift from the model. Live values: stirred 3.0, flow "
    "3.13-7.90, thin gap 7.89-19.91, RDE/RCE 19.03-35.46, none of them hardcoded.")
```

The Leveque coefficient row (state C, not page-anchored) is kept: no archetype film is computed
from it any more, it is evaluated only to confirm that the microfluidic floor binds, and it
still drives the S8.1 illustration. The retired 1 mm / 250 um pair survives ONLY as that
illustration, registered as "Illustrative channel pair (S8.1)" (assumption, with the ratio
argument as its sensitivity) so that its literals stay accounted for.

## A pre-existing inconsistency found on the way

`data/make_bounds_runs.py` (the mediated band-edge re-solves behind SI Table S8) still swept the
stirred film over **50-200 um**, the band of the RETIRED declared 100 um, while `emit_deltas.jl`
(the analytic bounds of the 42 Nernst-Planck rows in the same table) used the measurement's own
193-207 um. The two halves of one published bounds table were on different stirred bands since
2026-09-01. Both now read 193-207, and the three flow-film bands are defined ONCE, in
`correlations.jl` (`DELTA_FLOW_BAND`, `DELTA_ANEC_BAND`, `TAU_MICRO_BAND`), with both consumers
reading them.

## Files changed (all backed up as `.bak_pre7arch_20260907`)

Julia: `correlations.jl` (delta_eff, the film and band constants, `km_micro`), `params.jl`
(REACTORS), `run_all50_np.jl` (REACTORS_L), `run_profiles.jl` (six cases), `emit_deltas.jl`,
`carboxylate_decision.jl`. Data/gates: `build_merged_matrix.py` (50 x 7, 350 cells, 56 overlay),
`build_param_tables.py` (rows above; reads `results/si_sensitivity_bounds.json`),
`check_code_constants.py` (four new constants), `check_regenerates.py`, `audit_numeric.py`
(independent recompute), `check_cross_document.py`, `make_bounds_runs.py`, `reactor_engineering.py`
(illustration relabelled), the archetype lists in `check_ms_derived.py`, `check_ecprime_band.py`,
`check_si_bounds.py`, `check_transcription.py`, `dilute_theory_stratify.py`,
`schmidt_extrapolation.py`, `sensitivity_*.py`, `si_sensitivity_bounds.py`. Figures:
`model_medians.py`, `archetype_bands.py` (transcriptions and BAND_SPEC), `make_figs_sec34.py`
(six-cell schematic with the ANEC and microfluidic cells; tiers; ladder; Fig 3a/3b),
`make_figs.py` (computed Fig A bands; seven-column heatmap), `make_figFG.py`, `make_fig_trle.py`,
`analysis_*.py`, `anchored_diffusivity.py`; the legacy `make_fig4A.py`, `make_fig4B.py`,
`make_fig_main.py` had their column lists updated but are not run. `make_si.js`: Table S1, Table
S5/S6, the S1/S5.5/S7/S8.1/S10 passages, the reference list (Watkins added; Mo moved to its new
first appearance).

Old artifacts: `julia/*.csv.bak_pre7arch_20260907`, `results/*.json.bak_pre7arch_20260907`.

## Re-solve chain

`results/reanchor_chain_20260907.log` (absolute log paths, exit codes per step): run_tier0 ->
run_all50_np (350 cells) -> run_mediated (56 cells) -> run_profiles -> run_profiles_median ->
run_section4 -> emit_deltas; then make_bounds_runs + the two band-edge mediated solves ->
build_merged_matrix -> si_sensitivity_bounds -> registry / liveness / ledger -> make_si.js ->
figures -> gates. Results are recorded in CLAUDE.md under the v76 entry.

## Found on the way (2026-09-07, while re-running everything)

- **Four unchanged columns are bit-identical.** The unstirred, stirred, RDE and rotating-cylinder
  cells of the Nernst-Planck layer (200 of 350) and of the mediated layer (32 of 56) reproduce
  the previous matrices to the last digit -- the control that the re-solve changed only what it
  was meant to change.
- **SI S5.2 and S5.5 carried typed mediated-matrix numbers from the RETIRED films.** "delta/x_k
  ~ 43 stirred" (100 um era; the matrix gives 85 at 200 um), "the largest delta/x_k in the set at
  128 ... commuting bound of 6.95 ... resolves it at 104.7, an amplification of 15.1" (300 um era;
  228 um gives 97 / 9.14 / 137.8 / 15.1), "amplifications run x1.0 to x27" (the matrix has given
  x1.0-x22 since the stirred film moved), "rises from 2/8 to 3/8 (>=25: 2/8 to 4/8)" (the matrix:
  1/8 -> 2/8 and 1/8 -> 3/8), "amplify strongly in batch (x8-27)" (x13-22). Every one sat behind
  a green suite because G-ECBAND pinned the census sentence and nothing pinned these. All are
  computed in `make_si.js` now, with a build-time assertion that the Hofmann/unstirred cell is
  still the largest delta/x_k in the set. The wall sentence ("Two cells -- the rotating-disk and
  rotating-cylinder ...") is computed too, and the matrix now has three such cells (the
  microfluidic cell joins the two rotating ones); G-ECBAND builds the same sentence from the
  matrix instead of asserting "exactly two".
- **SI Fig. A drew typed archetype bands** (70-140 um "stirred", 20-60 um "flow") that had drifted
  from the archetypes they named; they are computed from `model_medians.delta_range` now.
- **`si_sensitivity_bounds.py` typed the band-file cell count (48)**, so the first bounds build
  after the re-solve refused two complete 56-cell files as "incomplete"; derived from the
  archetype count now.
- **The Watkins author line was first typed from memory and was wrong**; corrected from the SI's
  own first page before anything was built on it (see above).

## The carrier-charge sweep deadlocked, and the recovery had a misstep (2026-09-07, 12:40)

Inside `run_gates.sh --all`, the G-ZSENS re-solve for "Electrochemical amination z = -1" stopped
writing at 07:29 and sat for five hours at 0 % CPU with every thread in `__psynch_cvwait`: the main
thread in the libuv event loop, the OpenMP (`libgomp`) BLAS workers parked at a team barrier. The
machine had not slept (power log), the disk was not full, and a Newton loop that was merely slow
would have been on-CPU. An OpenMP barrier deadlock in the BLAS thread pool, not physics.

Recovery, in order, including the mistake: (i) `kill` on the Julia child made the sweep's
`subprocess.call` return non-zero, and the sweep simply moved to its NEXT alternative and spawned
a fresh Julia -- so one alternative would have been silently missing from the JSON; (ii) the child
was frozen with SIGSTOP (so it could write nothing more) and the sweep sent SIGTERM -- **which
Python does not turn into an exception, so the `finally` that restores the sentinels never ran**
and both perturbed files were left on disk (a partial `all50_np_matrix.csv`, `carrier_charge.csv`
with a perturbed row); SIGINT would have run it. (iii) Both were restored FROM their `.zsens`
sentinels, which were first proved byte-identical to copies taken before any kill, and the
sentinels removed; the restored matrix is 351 lines and the amination row is back at z = 0.
(iv) The runner recorded G-ZSENS as FAIL (a killed sweep, not a physics verdict) and went on to
G-KSENS and G-DSUBSENS, which touch only `run_mediated.jl` / `mediated_ec_matrix.csv` and a
patched copy respectively -- disjoint from the carrier-charge sweep's two files -- so the
carrier-charge sweep was relaunched on its own, concurrently, with `OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1` (`results/zsens_manual_20260907.log`). Single-threaded BLAS removes the
barrier that deadlocked; its verdict supersedes the runner's FAIL line and is recorded in
CLAUDE.md. *To abort a sweep cleanly: SIGSTOP the Julia child, SIGINT (not SIGTERM) the Python,
then SIGKILL the child; and verify the sentinels are gone and the live files match them.*
