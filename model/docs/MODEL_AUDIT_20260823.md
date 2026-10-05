# Sections 3–4 model audit — autonomous rounds to three consecutive clean passes

Scope: the transport / EC′ / thermal model behind main-text Sections 3 and 4 and the SI sections
that support them (S1–S10). Four dimensions per round: physics setup, numerics and mesh
convergence, parameter provenance, reproducibility.

Rule: a finding counts only after I reproduce it myself. Agent claims are leads, not results —
this session has already seen several confident false positives (a "lost tracked change" that was
Word re-chunking markup, an "857% trace sensitivity" that was a partially-written CSV, a
"misattributed" citation that was a Unicode surname the regex truncated).

A round is CLEAN when no CRITICAL or SERIOUS finding survives verification.

| round | physics | numerics | parameters | reproducibility | verdict |
|---|---|---|---|---|---|

## Round 2 — four auditors: physics, numerics, provenance, gates

A round is CLEAN when no CRITICAL or SERIOUS finding survives verification. **Round 2 was not
clean.** Every CRITICAL below was reproduced independently before being acted on.

### The finding that mattered most, found twice by different routes

Two auditors, given different briefs, landed on the same cell (Br⁻ oxidation × unstirred) and the
same conclusion: **the published unstirred ≥25 mA cm⁻² count was set by undocumented solver
constants, not by the model.**

| root cause | mechanism | that cell |
|---|---|---|
| `npp_ecprime.jl:141` returned success at `norm(F,Inf) < 1e-6` while `:107` declared `tol = 1e-9` | Newton accepted on exhaustion at 1000× its stated tolerance | 36.84 → 11.19 |
| `npp_ecprime.jl:83` floored concentrations at `exp(−50)` | where it binds, the Jacobian column is *exactly* zero → singular LU → silent diversion to a regularised least-squares branch; fires in 3 of 48 cells | 36.84 → 10.45 |

Both results sit below that cell's own commuting bound, so it floors to Tier-0 16.72 and stops
clearing 25 → **12/50 becomes 11/50**. Both causes are now fixed. Note the irony: the whole
δ-continuation effort earlier that day existed to move that integer 11 → 12; under a correct
solver it returns to 11 through a *different* cell.

### Verified and fixed

| sev | finding |
|---|---|
| CRIT | **G-SOLV was failing** — a hard `AssertionError` — and appeared in no runner, so nobody saw it. Its expectation was a typed literal never re-pointed, and its message libelled the SI ("Table S5 says 11/…" when Table S5 said 12). Now reads Table S5 out of `make_si.js` at run time; negative-controlled. |
| CRIT | The SI asserted **8/50** clearing 50 unstirred where its own Table S5, the manuscript and the model all said 9/50. |
| CRIT | The SI's **"20 of the 48 solves sit above min(Savéant, substrate supply)"** — recomputed: 34 by the sentence's own definition, 21 above the substrate term. The 20 predated the Hofmann fix. |
| CRIT | **Six sensitivity strings published verbatim into Table S7 were stale** — δ(stirred) medians and counts, δ(unstirred), Léveque, Eisenberg, the 68.4 µm breakpoint. Each recomputed from the model and corrected. |
| SER | **`check_ms_derived.py`'s per-architecture median checks never used their expected values.** Six `want()` calls against one phrase each matched *any* number in it, so a caption with every median attributed to the wrong architecture passed all six. This was written the same day, in the file whose own comment cites trap 11. Fixed with a positional matcher and demonstrated failing on the reversed caption. |
| SER | Newton-wall marker erasure — 14 of 48 rows read as converged when they were not, including by Fig. 4's envelope gate. |

### Verified, still open — see `HANDOFF_20260823.md` §5

Tier-0 has no migration term (two integers move if the model's own measured factor is applied);
Cl-epoxidation `C_S` duplicated with the copies disagreeing (solver uses 5.0, derived columns use
5.67, and the SI prints both 167 µm and 157 µm for the same x_k); the Br₂/Br₃⁻ caveat attached to
1 cell when it applies to ≥9 and binds hardest on a *different* cell than the one flagged; the
runtime invariants blind to the mediator element balance; G8b one-sided; G3/G11 putting the
convergence flag in the note string rather than the pass criterion.

### What the auditors tried and could not break

Worth recording, because it is evidence *for* the model: central-difference Jacobians reproduce
4 of 4 attached-front wall values bit-identically (refuting the auditor's own leading hypothesis);
residual scaling does **not** hide non-convergence when measured against the flux that actually
flows (worst case 1.4e-12); migration is well resolved everywhere (max cell Péclet 0.24 ≪ 2);
results are bit-identical across BLAS thread counts; G11's current conservation is 2.6e-10%; and
the commuting bound holds on all 48 rows.

## Round 1 — findings, and what survived verification

### PARTLY WRONG, AND CORRECTED — my Round 1 rejection of "11/50 and 8/50 are mesh artifacts"

**I rejected this finding on a bad test, and the agent's direction was right.** The record of what
I said and why is kept below, because the reasoning error is the useful part.

The numerics audit reported that coarsening the mesh moves the unstirred counts to 12/50 and 9/50,
driven by Br-/Hofmann × unstirred swinging over a factor of 205, and concluded "the shipped mesh is
the outlier at the bottom". I re-solved that cell independently, reproducing the production spec
exactly (tier0 6.947, Savéant 724.1, subcap 51.459 — matching the shipped CSV to 3 decimals):

    N=60   dx1 x0.5/x1/x2 -> 106.19 / 111.53 / 102.48   mA cm-2   ABOVE both thresholds
    N=90   (production)   ->   0.825 /   0.742 /  1.057
    N=135                 ->   0.885 /   0.981 /  1.018
    N=180                 ->   1.128 /   1.110 /  1.170

and concluded: *"Only N = 60 — COARSER than production — blows up, and it blows up to 102–112 mA
cm-2, which EXCEEDS the cell's own substrate cap of 51.46. That is an unphysical excursion, not a
converged answer. So the production mesh sits in the converged regime and the published integers
are NOT mesh artifacts."*

**Two things are wrong with that.**

1. **The substrate cap is not a physical ceiling, so "exceeds 51.46, therefore unphysical" proves
   nothing.** `i_subcap = n_S F D_S C_S/δ` assumes the reaction front sits AT the electrode. Once
   the substrate is exhausted the front DETACHES and the rigorous bound becomes
   `n_S F D_S C_S/(δ − x_f)`, which grows without limit as `x_f → δ`. Direct measurement settles
   it: at the Hofmann stirred wall the substrate surface concentration is `4.46e-9` of bulk, and
   20 of the 48 production solves sit above their own `i_subcap`. See
   `docs/ECPRIME_WALL_FINDING.md`.
2. **Agreement among three stalled solves is not convergence.** N = 90, 135 and 180 agree at
   0.7–1.2 mA cm-2 — and that value lies BELOW the cell's own commuting bound of 6.95, which the
   homogeneous source term can only raise. A number below a rigorous lower bound is not a
   converged answer; it is a dead solve, and three meshes agreeing on a dead solve says only that
   they die the same way. `run_mediated.jl`'s own `flag` column already knew this and marks the
   cell `wall`; the pipeline floors it to Tier-0. I read the agreement as convergence without
   checking it against the bound the model itself carries.

**What is true — and it has since been RESOLVED.** Exactly one production cell was genuinely
unresolved: Br-mediated Hofmann × unstirred (δ = 300 µm, δ/x_k = 128). It was shipped at its
Tier-0 floor of 6.95 mA cm-2, below the 25 mA cm-2 threshold, so that floor was setting a headline
integer.

The failure was **connectivity, not resolution**. Eleven mesh and continuation variants (uniform
and stretched, N = 90…720, growth 1.15 and 1.02) all die between 0.52 and 3.01 — every one below
the commuting bound. At this δ/x_k the substrate is exhausted at the wall and the reaction front
**detaches** into the interior, and that branch is not reachable by ramping current up from a bulk
initial state at any mesh. **Continuation in δ reaches it**: ~100–112 mA cm-2 (104.3 at N = 90,
100.4 at N = 180, 111.7 on the production path), with the front at x_f/δ = 0.506 and a clean
turning point above.

**So the unstirred counts ARE 12/50 and 9/50 — the numbers the agent named.** The agent's
*mechanism* was still wrong: N = 60's 102–112 was a coincidence of magnitude, not evidence, and
had no more claim on being converged than 0.74 did. But its conclusion was right and my rejection
was wrong. `npp_ecprime.jl` now carries the continuation, `run_mediated.jl` uses it on exactly the
cells that need it (1 of 48; the other 47 bit-identical), and v39 carries the corrected counts.

**The general lesson, which is the reason this section is kept rather than deleted:** *check a
solver value against the bounds the model itself carries before deciding whether it converged.*
The commuting bound was available the whole time and would have flagged this cell in one line.

### UPHELD: the EC' values are wall-terminated lower bounds, and the counts carry a band

What does survive is the concern underneath it. That cell's solver value (0.74-1.17) sits ~50x below
its physical cap (51.46), and 44 of the 48 mediated cells end on a Newton failure rather than the
collapse criterion — 14 of them silently relabelled with a physical limiter by npp_ecprime.jl:186,
which re-evaluates collapsed() at the stalled current. SI S5.5 says "one of 48".

Bounding the EC' layer between its two physically meaningful limits — every mediated cell suppressed
to the Tier-0 floor, and every one raised to min(Saveant, substrate cap) — brackets the counts:

    >=25   suppressed 10/15/18/30/35/35   published 11/17/21/31/36/36   at cap 11/17/21/31/35/35
    >=50   suppressed  8/13/13/23/32/34   published  8/14/14/25/32/34   at cap  9/14/15/25/32/34

The architecture ordering (unstirred < stirred < flow < thin-gap) holds at BOTH ends. The integers
carry a +/-1 to 3 band from the EC' layer; the ranking, which is what Sections 3-4 conclude, does not.

### Round 1 — fixes applied

Data and code
  n_carrier registered            the only linear factor of i_lim with no registry row (0.1-6.0,
                                  two fractional rows); sensitivity shows n=1 flips no verdict
  MeCN mu 0.343 -> 0.369          CRC 97th p. 6-243, eta(25 C) column. 0.343 is on no printed CRC
                                  page: Sect. 15 carries no printed viscosity column at all
  DMA mu 0.945 -> 1.927           CRC 97th p. 6-244, eta(25 C) column
  Le Bas ring correction          cyclomatic number, not RingInfo.AtomRings(); adamantane was
                                  getting 4 rings for 3 and D was 4.4% high
  run_section4.jl kappa           was a hard-coded 0.80 while read_kappa() returned 0.877 in the
                                  same run; now prints 25.3 V / 187 C, matching SI S6.1 exactly
  Eisenberg validity note         restated: Sc median 455, 46 of 50 BELOW the fitted floor of
                                  2230; the old note had range, direction and worst case wrong
  EC' wall label                  no longer erased by the collapsed() re-evaluation; 44 of 48,
                                  was displaying 30. Values bit-identical, labels only
  Hofmann nu_solv                 4.42e-7 -> 4.755e-7, stale against the corrected MeCN mu
  solvent-table cross-check       build_param_tables vs solvents.csv, negative-controlled; it
                                  fired on a real drift the moment it was added
  NaOH kappa                      chord vs Dorn's own Casteel-Amis fit (174.5 vs 179.23) fully
                                  documented; no verdict moves either way

Prose
  Fig. 5 caption                  "upper bound" -> "lower bound". Both omitted terms are heat
                                  SINKS. The registry recorded this correction on 2026-08-22 and
                                  it never reached the manuscript
  MS 92                           "and electrolyte" removed: kappa enters no transport quantity
  Architecture medians            6.2/17.4/20.2/50.2/111.7/127.4 -> 6.0/17.1/19.4/48.4/108.3/121.4
  Fig. 2b guide constant          1740 -> 1710 mA cm-2 um
  SI delta ranges                 flow 54-68 -> 38-96 um; thin-gap 21-27 -> 15-38 um
  SI S5.5                         "one of 48 solves" -> the 44/48 census, with the count band
  SI S7 XEC validation            WITHDRAWN: at the printed DMA viscosity the ceiling is 8.2 mA
                                  cm-2, BELOW the 10 the campaign ran at
  SI RDE/RCE                      thermal gap disclosed: never assessed, and both would fail

WHAT MOVED IN THE PUBLISHED NUMBERS
  >=25 counts  11/17/21/31/36/36   UNCHANGED
  >=50 counts  8/14/14/25/32/34 -> 8/14/14/24/32/34   (thin-gap, from the MeCN viscosity)
  medians      all six moved 1-5%; the thin-gap median crosses below 50
  architecture ordering            UNCHANGED at every point

Manuscript v33 -> v37 (v34 bound direction + transport inputs; v35 medians; v36 artwork; v37 guide
constant). 31/31 gates on v37.
