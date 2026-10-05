# The 48th mediated cell: Br- oxidation / electrophilic bromination x unstirred batch

`delta = 300 um`, `k = 1e3 M^-1 s^-1`, `x_k = 3.149 um`. This is the one cell of the 48 mediated
(reaction x reactor) cells that no solver path reached. This file records what it actually is,
what was wrong with every number previously produced for it, and how the answer was established.

## 1. What the cell physically is

Solved profiles at `N = 180` (mesh-resolved, see section 4) at a surface depletion of 0.5:

| quantity | value |
|---|---|
| Br2 at the wall | 113 mol/m3 (bulk Br- is 152 mol/m3) |
| substrate front | ~190 um from the electrode |
| substrate across the dead zone | falls 22 orders of magnitude over ~150 um |
| local decay length `lambda = sqrt(D_S/(k c_ox))` | 2.35 um at the wall, ~17 um at 196 um |

This is **detached-front total catalysis**. Br2 is generated far faster than substrate can arrive,
so it accumulates to a concentration comparable to the bulk mediator, consumes the substrate at a
front two thirds of the way across the film, and the excess escapes unreacted to the bulk.

The consequence that matters for reading the table: the **total** current legitimately exceeds the
substrate transport cap `i_subcap = 4.864 mA/cm2`, because most of the Br2 never reacts. All six
reactors of this reaction are reported the same way (the stirred cell reports 71.26 against its own
`i_subcap` of 14.59), so this cell follows the existing convention and introduces no new choice.
Whether the manuscript should report product-forming rather than total current is a separate,
already-flagged author decision that applies to all mediated rows alike, not to this cell.

## 2. Every number previously produced for this cell, and why each is wrong

| route | value (mA/cm2) | verdict |
|---|---|---|
| published in `mediated_ec_matrix.csv` | 18.161 | **below its own k = 0 floor** -- impossible |
| k-continuation | 17.259 / 19.290 / 19.899 / 20.110 | exactly 0.85 / 0.95 / 0.98 / 0.99 x the anchor it was handed |
| delta-continuation (`solve_ilim_ec_continued`) | 10.483 | half the floor |
| k-limit-tracking (added this session) | 22.785 | stalls at `c_red/cb = 4.9e-2`, ~4% short |
| direct ramp + c-control | 5.44 - 5.92 | dies on the substrate branch |

The floor these must clear is the **k = 0 solve of the identical species set, mesh and boundary
conditions**: 20.305 mA/cm2, and it is mesh-converged to five digits (identical at N = 90, 180 and
360). The source term only ever regenerates the carrier -- in all eight mediated systems the
electroactive reduced species (`s < 0`) carries `nu > 0` while its oxidised form carries `nu < 0` --
so `i_lim(k) >= i_lim(0)` exactly, and any route returning less than 20.305 has lost the branch
rather than found a limit.

Note on `18.161`: it is 0.85 x 21.366, i.e. the k-continuation anchor again, but 5.2% away from it
rather than 0.12%, so the 2% anchor-return guard added earlier does not catch it. The `flag = wall`
on that row is what correctly withheld it; it was never published as converged.

## 3. What the answer is, corroborated three ways

Both the no-source floor and the regeneration flux the source adds scale as `1/delta` -- the floor
because it is a diffusion-migration limit, the regeneration because it is capped by substrate
transport across the same film. Their ratio is therefore delta-INDEPENDENT, and it can be read off
the five reactors of this reaction that converge by plain ramp + c-control and never touch any
continuation:

| reactor | delta/um | i_k0 | i_ec | i_ec/i_k0 |
|---|---|---|---|---|
| Stirred batch | 100.0 | 60.936 | 71.260 | 1.1694 |
| Parallel-plate flow | 86.9 | 70.094 | 81.973 | 1.1695 |
| Thin-gap microflow | 34.5 | 176.988 | 206.656 | 1.1676 |
| RDE 1600 rpm | 15.8 | 387.411 | 452.629 | 1.1683 |
| Rotating cylinder | 14.8 | 411.370 | 480.608 | 1.1683 |

Constant to 0.16% across a 6.8x range in delta. Applied to this cell's floor:
**1.1686 x 20.305 = 23.73 mA/cm2**.

Independently: a purely additive flux estimate (bulk Br- flux plus substrate-limited regeneration,
with no migration enhancement on the regenerated ions) gives `20.305 x (1 + 24.32/203.05) = 22.74`.
The same estimate for the stirred cell gives 68.23 against its true 71.26, i.e. it undershoots by
4.4%; correcting this cell by the same factor gives **23.74**.

And the k-limit-tracking value of 22.785 is consistent with both: for a diffusion wave
`i/i_lim ~ 1 - c_red/c_bulk`, and it stalled at `c_red/cb = 4.9e-2`, which accounts for essentially
all of its 4% shortfall.

## 4. The actual cause: a trust region throttled by a variable that cannot matter

Both Newton routines limited the step by rescaling the WHOLE vector so its largest component moves
at most `max_step` in log space:

```julia
mx = maximum(abs.(du)); mx > max_log_step && (du .*= max_log_step / mx)
```

That rule assumes every component is meaningful. Behind the reaction front it is not. Tracing a
single depletion step (0.500 -> 0.490) printed the same thing on every iteration:

```
16   |R|inf = 2.0203e-02   argmax at: constraint row
     Newton step: max|dv| = 2.802e+09 at Sub @ node 8 (x=0.59 um) ; global scale factor = 7.138e-10
...
34   |R|inf = 2.0203e-02   argmax at: constraint row
     Newton step: max|dv| = 3.891e+12 at Sub @ node 2 (x=0.10 um) ; global scale factor = 5.140e-13
```

`2.0203e-02` is exactly `|log(0.49/0.50)|`: the constraint was never satisfied to any degree at
all. The largest Newton component was, every single time, the **substrate in the dead zone** --
a variable sitting at ~1e-22 of bulk in a region where it reacts with nothing, whose equation
there is nearly singular, so the linear solve returns components of 1e9 to 1e12 for it. Rescaling
on that multiplied the entire step by ~1e-12, and the surface Br- that had to move by 0.0202 was
throttled to ~1e-14.

**The fix** (`limit_step!`, `npp_ecprime.jl`): exclude from the rescaling norm any component that
is a species concentration below `NEGLIGIBLE_C = 1e-10` of that species' bulk value, and clamp
those components individually instead. Applied at all three sites -- `newton_ec!` and both copies
of `newton_ec_ccontrol!`.

Two properties make this a correction rather than a fudge:

* **Where nothing is negligible it is the identical rule.** No species below the threshold means
  no exclusions and the same rescaling as before.
* **It is falsifiable, and was falsified against.** Re-solving all six reactors of this reaction by
  the ordinary ramp + c-control path, the shift tracks exactly how deep each cell's dead zone goes,
  and vanishes where there is none:

  | reactor | `c_sub/cb` at the wall | change vs stored |
  |---|---|---|
  | Stirred batch | 8.5e-16 | +0.076% |
  | Parallel-plate flow | 5.7e-14 | +0.072% |
  | Thin-gap microflow | 3.0e-6 | +0.025% |
  | RDE 1600 rpm | 2.6e-3 | **-0.0000%** |
  | Rotating cylinder | 3.6e-3 | **-0.0000%** |

  The two cells that never drive any species below 1e-10 of bulk are bit-identical. The others move
  by less than a tenth of a percent, upward -- the solver is no longer stopped short of the fold.

**With this corrected the cell needs no continuation at all.** The ordinary production path -- the
same current ramp followed by c-control that solves the other 47 -- reaches it. The full
`run_mediated.jl` gives **23.7491 mA/cm2**, against **23.73** predicted by the delta-independent
ratio and **23.74** by the corrected additive estimate -- both computed BEFORE the cell was solved.

The published figure is the **c-control plateau**: the walk stops when the current has effectively
ceased responding to further depletion, `|d ln i / d ln frac| < plateau_tol = 2e-3`, at
`c_red/cb = 1.68e-03`. A bare current ramp pushes 0.09% further, to **23.7715**, before Newton
stops. Both points sit on the same plateau and that 0.09% IS the plateau tolerance -- the walk
declining to chase the residual creep -- not a disagreement about the physics. Bare-ramp values
appear in the threshold sweep below, which is why that table reads 23.771472 rather than 23.7491.
`i_ec/i_k0 = 1.1696`, which sits inside the 1.1676-1.1695 band of the five reactors that were never
in doubt. So `solve_ilim_ec_ktrack` is retained but is not what solves this cell.

### The threshold carries a sensitivity, not a justification

`NEGLIGIBLE_C = 1e-10` is a numerical choice, so by this project's own standard it has to state the
range tested and what depends on it, rather than sound reasonable. `julia/negligible_sweep.jl`
sweeps it over **ten decades** and re-solves four cells by the ordinary ramp + c-control path: the
two the change actually moved, and two it must not move. It reports whichever of the ramp and the
c-control walk reaches higher, so its bromination figure is the bare-ramp 23.771472 rather than the
published c-control plateau of 23.7491 -- see the note above. What the sweep tests is INVARIANCE,
so the choice of estimator does not matter provided it is the same one at every threshold.

| `NEGLIGIBLE_C` | brom x unstirred | Hofmann x unstirred | brom x RDE | brom x RCE |
|---|---|---|---|---|
| 1e-06 | 23.771472 | 111.526372 | 452.628639 | 480.608174 |
| 1e-08 | 23.771472 | 111.526372 | 452.628639 | 480.608174 |
| 1e-10 | 23.771472 | 111.526372 | 452.628639 | 480.608174 |
| 1e-12 | 23.771472 | 111.526372 | 452.628639 | 480.608174 |
| 1e-14 | 23.771472 | 111.526372 | 452.628639 | 480.608174 |
| 1e-16 | 23.771472 | 111.526372 | 452.628639 | 480.608174 |

Identical to six decimal places at every threshold, for every cell. **No conclusion depends on
where the threshold sits.** RDE and RCE additionally return their pre-change values exactly, which
they must: they never drive a species below even 1e-3 of bulk, so no threshold in this range
produces any exclusion for them and the rule is literally the old one.

The sweep needs the threshold settable at run time, so it is a `Ref` rather than a bare `const`.
The production value is unchanged at 1e-10.

### Where else the same rule appears, and why it is left alone

`julia/npp.jl` carries the identical global rescaling in its own `newton_solve!`, and it is not a
dead file -- `run_audit.jl` (the 16/16 gate), `run_section4.jl`, `run_profiles.jl` and
`run_profiles_median.jl` all include it. It is deliberately NOT changed, for a structural reason
rather than an assumption: `FilmProblem` is a **source-free** film (its own header says so, and
the file contains no homogeneous rate term at all). With no homogeneous source there is no
reaction front, hence no dead zone, hence no species driven to 1e-22 of bulk across many cells --
so `limit_step!` there would be the identical rule with no exclusions. The pathology requires a
source term to create it.

`julia/probe_jacobian.jl` also carries the pattern; it is a diagnostic probe, not production.

### The whole mediated matrix, re-solved

| | |
|---|---|
| bit-identical | **43 of 48** |
| differing only in the last 1-2 ulp | 3 |
| genuinely moved | 2 |
| **cells not flagged `ok`** | **1 before -> 0 now** |

The two that moved are precisely the two with a deep substrate dead zone, and both had their
limiter reclassified from `"limit reached, solution ceases"` -- a Newton wall -- to `"plateau"`,
which is the real limiting current:

| cell | old | new | |
|---|---|---|---|
| Br- oxidation x unstirred | 18.1608 | **23.7491** | +30.77% |
| Hofmann rearrangement x unstirred | 111.2290 | 111.5058 | +0.25% |

Nothing moved down. That is the direction the diagnosis requires: the old step control stopped the
solver short of the fold, so correcting it can only find MORE current, never less.

## 5. A separate finding: the mesh, and why it does not change the answer

Continuation failing EARLIER on finer meshes was what ruled out "the continuation is at fault"
before the trust region was found. Measuring the front against the mesh:

* at **N = 90** (the production mesh) `h/lambda` reaches **2.03** through the front region --
  under-resolved, and coarse cells over-decay the exponential, which is why the coarse mesh reports
  a *smaller* wall substrate concentration (5.9e-22) than the fine one (2.5e-18);
* at **N = 180**, `h/lambda <= 0.87` everywhere -- resolved.

The substrate profile in the dead zone is therefore NOT mesh-converged. The reported quantity is:
at a fixed surface depletion of 0.5 the current is **13.6138 mA/cm2 at both N = 90 and N = 180**,
and the k = 0 floor is 20.305 at N = 90, 180 and 360 alike. This is what should be expected -- the
current is set by the Br- flux, and cannot depend on whether a substrate that reacts with nothing
sits at 1e-22 or 1e-18 of bulk. The under-resolved region is exactly the region the trust-region
fix declares irrelevant, which is the same statement arrived at from two directions.

## 6. Files

| file | role |
|---|---|
| `julia/ktrack_crosscheck.jl` | the delta-independent ratio of section 3, from the five converged reactors |
| `julia/profile_dump.jl` | front profile vs mesh spacing, section 4 |
| `julia/stageC_test.jl` | isolates the failure to the depletion walk |
| `julia/newton_trace.jl` | the residual/step trace of section 4 that identified the cause |
| `julia/clamp_test.jl` | rules out plain componentwise clamping (it breaks the Newton direction) |
| `julia/trustregion_verify.jl` | the six-reactor regression table of section 4 |
| `julia/npp_ecprime.jl` | `solve_ilim_ec_ktrack` + `_push_to_fold`, with the monotonicity guard |
| `julia/run_mediated.jl` | `k0_floor` now returns its state; k-limit-tracking added as the last cascade step |

Backups: `npp_ecprime.jl.bak_ktrack`, `npp_ecprime.jl.bak_trustregion`,
`run_mediated.jl.bak_ktrack`, `mediated_ec_matrix.csv.bak_preTrustRegion`,
`all50_np_matrix.csv.bak_preTrustRegion`.
