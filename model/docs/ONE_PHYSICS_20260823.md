# One physics for all 50 — migration everywhere, no reduced-model fallbacks

*2026-08-23. `julia/run_all50_np.jl`, `julia/run_mediated.jl`, `data/carrier_charge.csv`,
`data/electrolyte_ions.csv`.*

## The problem this fixes

The published matrix mixed **three physics levels in columns that were counted against each
other**:

| rows | physics |
|---|---|
| 42 | Tier-0 Fick — **no migration term at all** |
| 8 | full Nernst–Planck + migration + EC′ coupling |
| 1 of those 8 | Tier-0 again, silently substituted when the EC′ solve failed |

"N of 50 clear 25 mA cm⁻²" was tallied across all three. That is not an apples-to-apples
comparison, and the SI compounded it by *measuring* the migration enhancement (§S5.3, gate G2:
exactly 2.00 for an anion in its own binary salt; 1.38 / 1.18 / 1.04 at support ratios 0.25 / 1 /
5) and then licensing Tier-0 anyway on the grounds that it is "accurate to within a few percent
for **neutral** substrates" — while several of the 50 carriers are anions in low-support media.

## What is done now

**Every row, same solver.** `run_all50_np.jl` solves all 50 reactions × 6 architectures with
Nernst–Planck, migration and electroneutrality, on the same mesh policy with the same limit
criterion. The 42 non-mediated rows run at `k = 0` — the identical equation set with the
homogeneous source switched off, **not a different model**. The eight mediated rows additionally
carry the EC′ source.

**Electrode bookkeeping closes exactly for any carrier charge.** Per electron the carrier is
consumed at `s = −1/n` and the product forms at `+1/n` with `z_P = z_c + n`, so

```
Σ_j z_j s_j = z_c(−1/n) + (z_c + n)(1/n) = 1
```

identically. A neutral carrier must therefore reproduce the Fick answer — which is the built-in
correctness check, not a wasted solve.

**Same inputs as Tier-0.** Carrier `D`, `C`, `n` and the solvent kinematic viscosity are read
from `reactions_table.jl`, the same generated table `run_tier0.jl` uses, so any difference
between the two matrices is *physics*, not different numbers going in.

## Validation — three independent checks, all passing

| carrier | migration factor | checked against |
|---|---|---|
| neutral | **×1.004** | the Fick limit: migration must do nothing |
| anion at support ratio 1 | **×1.176** | SI Fig. E-a, measured independently: **1.18** |
| anion in its own salt (binary) | **×2.006** | the **exact** Newman binary result: **2** |

The last is the strongest: an anion oxidised in its own salt with no supporting electrolyte has an
analytically exact limiting current of twice the Fick value, reproduced here to 0.3% through a
completely different code path from gate G2.

**What it means for the old numbers:** every charged-carrier row in Tier-0 was understated — by
~18% at support ratio 1, and by a **factor of two** for the binary ones (carbonate in 1 M Na₂CO₃,
chloride in 2 M NaCl).

## No reduced-physics fallback anywhere

`build_merged_matrix.py` used to substitute the Tier-0 value when an EC′ solve failed. That is now
a **hard error that stops the build**, and it has fired in anger. A cell that does not solve is
not quietly replaced by a simpler model.

To make that survivable, the EC′ solver gained a **continuation cascade** — each path is tried in
turn and the first result that clears the commuting bound (`i ≥ 0.9 i_t0`) is taken:

| path | starts from | reaches |
|---|---|---|
| current ramp | bulk | most cells |
| c-control | the ramp's last state | the plateau, where the current ramp folds |
| **k-continuation** | the **analytic k = 0 solution** (`i_t0`; gate G5 verifies it to 0.13%) | the inverted γ < 1 deep-total-catalysis cells |
| δ-continuation | a solved smaller-δ neighbour | Hofmann × unstirred |

That different cells need different paths is a fact about the branch structure, not a fudge.
**Br⁻ oxidation × unstirred** defeated the ramp, c-control, δ-continuation and four mesh
refinements — including a front-graded mesh that went *non-monotonic* with N (14.44 at N = 180,
12.55 at N = 270), which is what showed the mesh was not the problem. k-continuation solved it at
**16.37 mA cm⁻²**, clearing its bound of 15.05. k-continuation is the strongest path because it
starts from a solution known in closed form, and raising `k` at fixed current *eases* the problem —
it climbs a gradient rather than fighting one.

> **UPDATE 2026-08-23, after the condition audit.** This cell's inputs were wrong when the above
> was written. The row paired Br⁻ 0.25 M (the Fig 4 H-cell) with arene 0.121 M (the Fig 5b flow
> run) — two different experiments. On the corrected same-experiment values (**Br⁻ 0.152 M, arene
> 0.121 M**, both from Fig 5b) the cell **no longer needs k-continuation at all**: it now solves on
> the ordinary c-control path at **14.3 mA cm⁻²**. The whole row drops 13–36%, and the ×2.34
> amplification is uniform across the five faster architectures.
>
> The cascade is still the right design and the k-continuation path stays in the solver — but the
> specific claim that *this* cell requires it was an artifact of a mixed-experiment parameterisation,
> not a fact about the physics. The honest statement is that k-continuation was what made the cell
> solvable **at the concentrations then in the table**.

## BLOCKED ON AUTHOR REVIEW — 16 carrier charges

Migration acts only on a charged carrier, so `z` decides which rows move. `data/carrier_charge.csv`
carries every assignment with its basis. **9 of 50 carriers are charged.** Needing review:

- **11 LOW** — all the metal complexes (Ni(bpy), Ni(dtbbpy), Ni(tet a), Mn(azide), Co(salen)×2,
  CoBr₂(glyme), [Cp*RhCl₂]₂, Cu(acac)₂/BOX). Written neutral because that is how the precursor is
  written, but the **electroactive** species may be anionic Ni(I)/Ni(0), cationic Co(III), or
  dicationic Ni(tet a). If any is charged, that row gains a factor between 1.2 and 2.
- **5 medium** — speciation-dependent: thiophenol/thiolate, NHPI/NHPI⁻, biphenyl-2-carboxylic
  acid, the amino acid at only 7.5 mM Et₃N, the RAE-activated proline.

**A wrong `z` does not fail loudly — it moves a ceiling by up to 2× in silence.** All 11 LOW rows
are catalyst-carried, the same class whose Fig. 4 claim ("ten of the eleven clear 25 mA cm⁻² in no
architecture") already rests on the untested electrode-confined assumption.

`run_all50_np.jl` **refuses to run on a LOW row** unless `--allow-unreviewed` is passed.

## Three supporting-electrolyte rows also need a decision

`data/electrolyte_ions.csv` resolves 47 of 50. The other three:

- **5 wt% AcOH/MeOH-H₂O** — ~0.7 M *total* acid, but AcOH is weak (pKa 4.76) so the ionic strength
  is ~10⁻³ M. That row is effectively **unsupported**, and the migration enhancement would be
  large. Needs the intended supporting-ion concentration stated.
- **Me₄NOH 15 mol% + Me₄NBF₄ 5 mol% (Kolbe)** — mol% is relative to the 1.0 M substrate, so
  0.15 M base against a carrier that `reactions_50.csv` carries at 1.0 M. Only ~0.15 M can be
  carboxylate. Carrier concentration *and* support both need resolving.
- **NaCl 7 mol% + pH 2 HCl (Giese)** — ~0.017 M supporting against a 0.095 M carrier, i.e. support
  ratio ≈ 0.2, weakly supported. Confirm the mol% basis.

## A caution about the first version of the charge table

It was keyed on hand-written reaction names and was **misaligned by rows in three places** — it
would have given a neutral biaryl amide the charge of bromide. The species-agreement assertion
caught it before it reached a solve. It is now keyed by carrier species so it cannot drift, and
that assertion runs every time. This is the exact failure mode the file is meant to guard against:
silent, plausible, and worth up to 2× on a published ceiling.
