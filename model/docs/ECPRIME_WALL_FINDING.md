# What the EC′ "Newton wall" actually is — and why it should never have existed

> **RESOLVED 2026-08-23.** Everything below the next section is the investigation that led here,
> kept because the reasoning errors in it are instructive. The conclusion changed: the wall was
> never a property of the physics or the mesh, it was a property of the **parameterisation**, and
> switching parameters removes it. All 48 EC′ cells now reach the physical collapse criterion.

## What the limiting current actually is, and why the solver kept missing it

The solver was asking the wrong question. It prescribed the **current** and looked for one
signature of the limit — the mediator starving, `c_red(0)/c_bulk < 1e-3`. Both halves of that
are wrong for part of the corpus.

**Prescribing current cannot reach the limit.** `dc_surf/di → −∞` there, so the Jacobian is
singular exactly at the answer and a current ramp cannot cross it. No mesh refinement helps; this
is a property of the parameterisation, not the discretisation. Eleven mesh variants of one cell
all died in the same place before this was identified.

**Mediator starvation is not the only limiting mechanism.** Prescribe `c_red(0)` instead, solve
for the current, and walk it down: `i` rises and **plateaus** at its limiting value. The walk ends
in one of three ways, and all three are the same physics:

| termination | meaning |
|---|---|
| `c_red(0)` reaches 1e-3 | the mediator is starved — the original criterion, correct where the mediator *can* be starved |
| **`i` plateaus** (`\|d ln i / d ln frac\| → 0`) | the limit is reached while the mediator is still present, because substrate supply behind a **detached front** is limiting |
| **Newton stops converging as `c_red → 0`** | the solution ceases to exist beyond `i_lim`; the last converged point *is* the answer, not a failure to work around |

**Why a mediator sometimes cannot be starved at all.** In Br⁻ oxidation the mediator *is* the
supporting anion (0.25 M Br⁻). Br⁻ is negative and the electrode is an anode, so migration drives
it **toward** the surface faster than reaction consumes it. `c_red(0)/c_bulk` sticks at 2.3e−2
while the **substrate** sits at 1e−20 of bulk. Hofmann × unstirred shows the same thing from the
other side, with `c_red(0)` *above* bulk. Terminating only on collapse therefore reports a **lower
bound for any migration-fed mediator** — and it was **22% low** on Br⁻-ox × stirred (84.8 against
108.3).

That is a physical result, not a numerical one: **mediated systems in which the mediator doubles
as the supporting electrolyte have a qualitatively different limiting mechanism** from those where
it does not. It belongs in §S5.4.

**`i` decreasing with further depletion is reported as SUSPECT, never harvested.** A genuine
turning point in a polarisation curve of this kind would be unphysical here, and treating one as
the answer would be indistinguishable from a solver landing on a different solution family.

**The curve is checked for smoothness.** `branch_roughness` measures the worst jump in
`d ln i / d ln frac` between consecutive points. A polarisation curve should be smooth; jumps mean
the continuation is hopping between roots. Measured on Hofmann × stirred: 0.018 over 20 points.
The previous solver reported only the endpoint of a curve nobody had looked at.

**No reduced-physics fallback anywhere.** `build_merged_matrix.py` used to substitute the Tier-0
(pure Fick, no coupling, no migration) value when an EC′ solve failed, so the published counts
were tallied across a column mixing two models. That is now a hard error: a cell that does not
solve stops the build.

## Two solver constants were deciding a published integer

Found 2026-08-23 by two independent Round-2 audits, by different mechanisms, landing on the same
cell (Br⁻ oxidation × unstirred) and the same answer. Both are now fixed.

**1. Newton accepted at a tolerance 1000× looser than it declared.** `npp_ecprime.jl:107` declares
`tol = 1e-9`; line 141 returned `norm(Fv, Inf) < 1e-6` on iteration exhaustion. Enforcing the
declared tolerance leaves **42 of 48 cells bit-identical** and moves six:

| cell | at 1e-6 | at tol = 1e-9 |
|---|---|---|
| Br⁻ ox × unstirred | 36.84 | **11.19** → below its commuting bound 15.05 → floored to Tier-0 **16.72** |
| Br⁻ ox × stirred | 110.52 | 79.09 |
| Br⁻ ox × flow | 127.13 | 121.41 |
| Hofmann × unstirred | 111.66 | 97.41 |
| Cl⁻/propylene × thin-gap | 2305.41 | 2300.72 |
| NHPI × flow | 8.44 | 8.42 |

36.84 clears 25; 16.72 does not. **The unstirred ≥25 count was 12/50 at `1e-6` and 11/50 at the
declared tolerance** — set by an undocumented constant rather than by the model.

**2. A concentration FLOOR, not the log-step clamp the SI discloses.** `npp_ecprime.jl:83` had
`exp(clamp(u, −50, 50))`, i.e. a hard floor at 1.9e−22 mol m⁻³. Where it binds the residual is
*exactly* independent of that degree of freedom, so its finite-difference Jacobian column is
exactly zero, the LU throws, and control diverts silently to the regularised least-squares
branch. Measured: it fires in **3 of 48 cells** (min log c reaching −52, 4045 singular-LU events
in one cell); in the other 45 the minimum is −5.5 to −41, nowhere near it. The SI's §S5.5
sentence invoking "no exponential tail to underflow the log-concentration clamp" is therefore
right for 3 cells and wrong for 45. Lowered to −300: below any physically meaningful
concentration (exp(−50) is already ~10 molecules m⁻³) and far above float64 underflow at
exp(−745), so it cannot bind and cannot silently zero a column.

**Three independent refinements agree.** Hofmann × unstirred gives 97.41 under strict tolerance,
97.41 at clamp −120 and −300, and 97.21 when the resume ramp is refined 1.05 → 1.01 — against a
shipped 111.66. **The shipped value was the maximum of six routes**, produced by the coarsest
mesh, the coarsest resume ramp and the loosest acceptance simultaneously. The honest range for
that cell is **≈97–112**, not the "≈100–112" quoted below, and it should not be printed to 16
significant figures: every EC′ value lies on the ramp × bisection grid, quantised to 0.234%.

## The actual cause: a fold in the current parameterisation

`solve_ilim_ec` prescribes the **applied current** and solves for the concentration field. That
map has a **turning point** at the limiting current: `dc_surf/di → −∞` as `i → i_lim`, so the
Jacobian degenerates exactly where the answer is. A ramp in current cannot cross a fold in
current. Newton fails, the ramp stops, and the value gets reported as a lower bound.

**No mesh can fix this**, which is why eleven mesh variants of the Hofmann cell (uniform and
stretched, N = 90…720, growth 1.15 and 1.02) all died in the same place. Chasing mesh resolution
was the wrong diagnosis, pursued for a long time before the fold was identified.

## The fix: continue in concentration, solve for current

Through the fold, `c_surf` is monotone where `i` is not. So prescribe the reduced-mediator
surface concentration and make the current an **unknown**. The system is bordered: the n
transport residuals keep `i_app` as a parameter, plus one added equation pinning `c_red(0)`.
Walking the target down to the `1e-3` collapse criterion reaches that criterion **directly**, and
the limiting current is read off rather than bounded.

`newton_ec_ccontrol!` and `solve_ilim_ec_ccontrol` in `npp_ecprime.jl`. The limiter string is
`"collapse (c-control)"` only when the criterion is genuinely reached — a stalled continuation
reports the fraction it stalled at, so a solved value stays distinguishable from a bounded one.

### Result, stirred archetype, N = 90

| system | current ramp | c-control | ratio | ended on |
|---|---|---|---|---|
| Br-mediated Hofmann | 334.58 (wall) | **335.03** | 1.00 | collapse (c-control) |
| ACT alcohol oxidation | 16.57 (wall) | **16.57** | 1.00 | collapse (c-control) |
| Cl-propylene epoxidation | 788.94 (**collapse**) | **788.23** | 1.00 | collapse (c-control) |
| NHPI allylic C–H → enone | 7.55 (wall) | **7.55** | 1.00 | collapse (c-control) |
| HMF → FDCA | 17.74 (wall) | **17.75** | 1.00 | collapse (c-control) |
| BQ Wacker–Tsuji | 27.87 (wall) | **27.89** | 1.00 | collapse (c-control) |

**The Cl-propylene row is the validation.** It is the one system whose current ramp already
reached collapse unaided, and concentration control reproduces it to **0.09%**. The new
parameterisation agrees with the old where the old worked, and succeeds where it did not.

That the c-control values land within ~0.1% of the wall values also confirms, independently, the
measurement in the section below: the walls really were sitting essentially at the limiting
current. But "a tight lower bound" was the wrong thing to be measuring. The right question was
why the solver was not finishing, and the answer was the fold.

---

# The investigation (superseded, kept for the reasoning)


*2026-08-23. Diagnostic: `julia/probe_ecprime_wall.jl`. Gate: `julia/run_audit.jl` G12.*

## The question

44 of the 48 production EC′ cells end their galvanostatic current ramp on a **Newton failure**
rather than on the physical collapse criterion (`c_red/c_bulk < 1e-3`). Everything downstream —
SI Table S6, Figure 4c, the three EC′ uplift counts in §S5.5 — reported those values as *strict
lower bounds*, and said so honestly. What was never measured is whether those bounds are **tight
or loose**. "A lower bound of unknown tightness" is not a result; it is a placeholder.

Two things made this worth chasing rather than accepting:

1. Until 2026-08-23 `npp_ecprime.jl` **overwrote the wall marker with a physical limiter**
   whenever the stalled state happened to satisfy the collapse test. 14 rows that had in fact
   ended on a Newton failure were labelled `mediator` or `substrate (total catalysis)`, so
   Table S6 marked far fewer rows as bounds than actually were, and `combined_figure.py`'s
   envelope gate was validating against those 14 while reporting it had validated against
   converged solves. Prefixing the marker (`"newton-wall; " * which`) exposed all 44.
2. With all 44 visible, **every genuinely converged row belongs to Cl-mediated propylene
   epoxidation**, which is the γ = 0.003 inverted system and out of scope for the envelope
   claim. So the two-sided check that gate was performing had, in truth, nothing left to stand
   on.

## The measurement

The decisive test is not the current — it is the **surface state at the wall**. If the reduced
mediator is already near the `1e-3` collapse threshold when Newton fails, the ramp stalled
essentially *at* the limiting current and the bound is tight. If it is O(1), the ramp died far
from any physical limit and the number understates the ceiling.

Stirred batch (δ = 100 µm), production mesh N = 90, ramp growth 1.15:

| system | i_ec (mA cm⁻²) | c_red/c_bulk | c_sub/c_bulk | ended on | growth 1.02 | N = 180 |
|---|---|---|---|---|---|---|
| Br-mediated Hofmann rearrangement | 334.58 | 1.19e-02 | 4.46e-09 | newton-fail | 334.92 (+0.10%) | 334.58 (0.00%) |
| ACT-mediated alcohol oxidation | 16.57 | 1.35e-03 | 7.83e-01 | newton-fail | 16.58 (+0.06%) | 16.57 (0.00%) |
| Cl-mediated propylene epoxidation | 788.94 | 9.25e-05 | 6.23e-05 | **COLLAPSE** | 788.97 (+0.00%) | 785.73 (−0.41%) |
| NHPI-mediated allylic C–H → enone | 7.55 | 2.16e-04 | 9.92e-01 | newton-fail | 7.55 (0.00%) | 7.52 (−0.40%) |
| HMF → FDCA (biomass) | 17.74 | 1.75e-03 | 7.20e-01 | newton-fail | 17.75 (+0.06%) | 17.74 (0.00%) |
| BQ-mediated Wacker–Tsuji oxidation | 27.87 | 2.83e-03 | 1.83e-01 | newton-fail | 27.90 (+0.11%) | 27.87 (0.00%) |
| Br⁻ oxidation / electrophilic bromination | 110.52 | 1.06e-03 | 4.29e-17 | newton-fail | 110.61 (+0.08%) | 110.52 (0.00%) |
| Aryl thiocyanation (NH₄SCN) | 17.63 | 1.36e-04 | 5.06e-01 | newton-fail | 17.63 (0.00%) | 17.63 (0.00%) |

All eight mediated systems, no exclusions.

## What it shows

**The wall is the limiting current, not a solver deficiency.** Every wall sits with the reduced
mediator between `9.25e-5` and `1.19e-2` of bulk — that is, depleted to between 0.009% and 1.2%.
The collapse criterion is `1e-3`; **seven of the eight are at or below `2.83e-3`**, and the
loosest (Hofmann, `1.19e-2`) stops roughly one 1.15× ramp step short of it. The Newton failure is the expected numerical
signature of a turning point when the state variable is `log c` and `c → 0`: the Jacobian
degenerates exactly where the physics says the current saturates.

**The values are converged.** Refining the continuation 7.5× (growth 1.15 → 1.02) moves the
answer by **≤ 0.11%** (largest: BQ, +0.11%). Doubling the mesh (N = 90 → 180) moves it by
**≤ 0.41%** (largest: Cl-propylene, −0.41%; five of the eight move by 0.00%). Both together
are well inside the ±2-of-50 count band that `G-SOLV` already declares for these rows. The
production mesh is adequate; this is now asserted by G12 rather than argued.

**A wall row is therefore a tight lower bound, not a loose one.** The SI's statement that these
values "cannot decrease under further solver refinement" remains true and is the safe direction;
what this adds is that they also cannot increase by more than about half a percent.

## What was tried and rejected

**"i_ec may not exceed i_subcap, so a row above it refutes the envelope."** Written, fired on 17
in-scope rows, and **wrong** — recorded here rather than shipped. `i_subcap = n_S F D_S C_S/δ`
assumes the reaction front sits *at* the electrode. The probe shows the substrate surface
concentration at the Hofmann wall is `4.46e-9` of bulk: the substrate is exhausted and the front
has **detached**. The rigorous bound is then `n_S F D_S C_S/(δ − x_f)`, which grows without limit
as `x_f → δ`. Exceeding `i_subcap` is evidence the front has moved, not evidence of a bad solve.

A related near-miss: two of the eight systems show an amplification `i_ec/i_t0` that is
*constant across all six δ* (Cl-propylene 2.01, Br⁻ oxidation 2.20). That looks like the
signature of a ramp dying after a fixed number of steps — and it is not. Both are binary systems
in which the reacting anion migrates toward the anode, and a δ-independent factor of ≈2 is the
Newman binary result that gate **G2** already validates to 0.50%.

## What is now checked

- `combined_figure.py` no longer claims a two-sided envelope agreement it cannot support. It
  states plainly that no converged in-scope row exists, checks the one relation that *is*
  rigorous (`i_ec ≥ 0.9 i_t0`, the commuting bound — the homogeneous source only adds), and
  asserts that this test and `run_mediated.jl`'s own `flag` column agree on which rows are usable.
- `run_audit.jl` **G12** re-solves two production rows at N = 90/180 and growth 1.15/1.02 and
  requires agreement within 1%, and reports the surface state so a future drift toward a *loose*
  wall is visible rather than silent. Negative-controlled by asserting the check fires when the
  tolerance is tightened past the measured spread.

## The one cell that was not a wall at all — Hofmann x unstirred, RESOLVED

Br-mediated Hofmann in an unstirred beaker (δ = 300 µm, x_k = 2.35 µm, δ/x_k = 128) is the only
cell of 48 whose ramp died **below its own commuting bound** — 0.74 mA cm⁻² against a Tier-0
floor of 6.95. That is not a tight bound or a loose one; it is not a physical answer at all, and
the pipeline floored it to 6.95. Because 6.95 < 25, that floor decided a headline integer.

**It is not a mesh problem.** Eleven mesh and continuation variants (`probe_hofmann_unstirred.jl`)
all die between 0.52 and 3.01 mA cm⁻², every one of them below the bound:

| mesh | N | i (mA cm⁻²) | | mesh | N | i (mA cm⁻²) |
|---|---|---|---|---|---|---|
| production (x_k/50, stretched) | 90 | 0.74 | | uniform | 90 | 1.35 |
| production, slow ramp (g=1.02) | 90 | 0.52 | | uniform | 180 | 1.11 |
| production mesh | 180 | 1.11 | | uniform | 360 | 1.72 |
| production mesh | 360 | 3.01 | | uniform | 720 | 2.49 |
| mild stretch (δ/300) | 180 | 1.28 | | mild stretch (δ/300) | 360 | 1.72 |

**It is a connectivity problem.** The solution at this δ/x_k has a **detached reaction front**:
the substrate is exhausted at the electrode and the reaction zone sits out in the interior. That
branch is not connected to the bulk initial state by a current ramp, so no amount of mesh
refinement lets a ramp from bulk find it. Continuation in **δ** does: the same system at
δ = 100 µm solves normally (334.58), and walking δ outward in 24 steps — regridding the converged
state onto each new mesh in absolute x — follows the branch the whole way
(`probe_hofmann_homotopy.jl`).

At the resolved point the front sits at **x_f/δ = 0.506**, the substrate surface concentration is
`1.2e-20` of bulk, and the mediator is at 53% of bulk. Raising the current further fails cleanly,
so this is a genuine turning point, not an unbounded excursion.

| route | mesh | ramp | i_lim (mA cm⁻²) |
|---|---|---|---|
| δ-continuation probe | N = 90 | growth 1.10 | 104.27 |
| δ-continuation probe | N = 180 | growth 1.10 | 100.38 |
| production path (`solve_ilim_ec_continued`) | N = 90 | growth 1.05, back-off | 111.66 |

**≈ 100–112 mA cm⁻², i.e. ±6%.** That is much looser than the ≤0.5% the other 47 cells hold, and
it is reported as a range for that reason — but every route clears 25 and 50, against a shipped
floor of 6.95. **The unstirred counts are therefore 12/50 and 9/50, not 11/50 and 8/50.**

**Production fix.** `regrid` and `solve_ilim_ec_continued` live in `npp_ecprime.jl` (one
implementation, not two — "the same quantity in two places" has already drifted three times in
this project). `run_mediated.jl` now solves reactors in order of **increasing δ**, tries the
direct ramp first for every cell, and falls back to δ-continuation **only** when a cell fails its
own commuting bound. The 47 cells that already worked take the identical code path and are
bit-identical; a new `path` column records which route produced each value. The continuation
backs off the anchor current (1.0 → 0.85 → 0.70 → 0.55 → 0.40 of its limit) because the branch
survives from 85% of the anchor limit but dies from 88.8%.

**Model-scope caveat, stated rather than buried.** Sustaining a front at x_f ≈ 150 µm requires the
model to generate a few tenths of a molar Br₂ from an 0.08 M bromide bulk, supplied by migration
of Br⁻ into the anode. The Nernst–Planck system is satisfied exactly — G11 puts the current
conservation residual at 2.6e-10% — but the model carries **no Br₂ solubility ceiling and no
Br₃⁻ speciation**, so whether the chemistry supports a front that far out at 300 µm is outside
what this model can answer. The value is reported with that caveat in SI §S5.5.

## Open

The probe covers the stirred archetype. The δ-dependence of the wall's tightness — whether a
thin-gap cell at δ = 15 µm stalls as close to collapse as a beaker at 100 µm — is measured for
the two G12 rows only. Extending the probe across all six archetypes is cheap but slow (~40 s per
solve at N = 180) and has not been run in full.
