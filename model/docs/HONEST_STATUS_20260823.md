# Honest status: full physics, and provenance — 2026-08-23

Two direct questions were asked. Both answers are **no**. This file records what is actually true,
with the evidence, so neither claim gets made by accident.

---

# 1. "Is everything solved with full physics?" — NO

## The full-physics matrix is computed and then thrown away

`julia/run_all50_np.jl` solves all 50 reactions × 6 architectures with Nernst–Planck, migration and
electroneutrality, and writes `julia/all50_np_matrix.csv`. That file is read by **nothing**:

```
$ grep -l all50_np_matrix *.js data/*.py julia/*.jl
julia/run_all50_np.jl        <- only its own writer
```

The published artifact, `julia/tier0_ec_matrix.csv` — which feeds `make_si.js`, the figures,
`build_param_tables.py`, `check_ecprime_band.py` and `check_ms_derived.py` — is built by
`data/build_merged_matrix.py` from:

```
t0 = pd.read_csv(.../"tier0_matrix.csv")        # Tier-0 FICK, no migration, all 50 rows
ec = pd.read_csv(.../"mediated_ec_matrix.csv")  # full NP + EC', the 8 mediated rows
```

**So 42 of 50 published rows are still Fick with no migration term.** `ONE_PHYSICS_20260823.md`
describes the one-physics work as done. The *solve* was done. The *wiring* was not.

## Proof, not inference

The Kolbe row has a charged carrier in its own salt, so migration must double it exactly
(Newman binary limit). `all50_np_matrix.csv` reports migration ×2.006. Compare:

| architecture | Fick | NP (full physics) | **published** |
|---|---|---|---|
| natural | 64.67 | 129.72 | **64.67** |
| stirred | 194.02 | 389.17 | **194.00** |
| flow | 225.71 | 452.73 | **225.70** |
| thingap | 568.75 | 1140.80 | **568.80** |
| rde | 1445.67 | 2899.70 | **1446.00** |
| rce | 1801.08 | 3612.58 | **1801.00** |

The published column is the Fick column. Every value is understated by a factor of two.

## Who is affected

11 rows have a charged carrier. 5 of those are mediated and do get the full EC′ treatment.
**6 rows are charged AND non-mediated, so they are published as Fick:**

| row | migration factor |
|---|---|
| Non-Kolbe decarboxylative alpha-methoxylation | **×2.876** |
| Kolbe homocoupling of 10-undecenoate | **×2.006** |
| Alkaline lignin → vanillin (pilot) | ×1.278 |
| Alkenesulfonate from cinnamic acid | ×1.176 |
| Sulfonylation of alkenes with sulfinates | ×1.176 |
| Cathodic aryl-halide radical 5-exo cyclization | ×0.969 |

Two of these need a second look on their own merits:

- **×2.876 exceeds the binary limit of 2.** For a singly-charged carrier that is its own supporting
  anion the enhancement is exactly 2. A value above it implies a different `z`, a different
  counter-ion charge, or an unsupported-medium effect. That row is `Et3N 7.5 mM (no salt)/MeOH`,
  i.e. essentially unsupported — plausible, but it must be explained, not just reported.
- **×0.969 is below 1** — migration *hindering* transport. Physically that means the carrier is
  driven away from the electrode that consumes it. Sensible for the wrong-sign pairing, but it
  should be confirmed against that row's `z` rather than assumed.

## What fixing it does to the headline counts

| architecture | published (mixed) | if full physics |
|---|---|---|
| natural | ≥25: 11, ≥50: 9 | ≥25: 11, ≥50: 9 |
| **stirred** | ≥25: 17, ≥50: 14 | **≥25: 18, ≥50: 15** |
| **flow** | ≥25: 20, ≥50: 14 | ≥25: 20, **≥50: 15** |
| thingap | ≥25: 31, ≥50: 24 | ≥25: 31, ≥50: 24 |
| rde | ≥25: 36, ≥50: 32 | ≥25: 36, ≥50: 32 |
| rce | ≥25: 36, ≥50: 33 | ≥25: 36, ≥50: 33 |

Small, but it moves in the direction that *helps* the claims, which is exactly why it must be done
before the numbers are quoted — not after.

## Why no gate caught this

`data/audit_numeric.py` is a **consistency** checker: it verifies that the derived artifacts agree
with their sources. It never opens `all50_np_matrix.csv`, so an orphaned source is invisible to it.
Consistency between the wrong inputs is still consistent.

---

# 2. "Does every number have strict PDF provenance?" — NO

Concentrations now do (Parts 1 and 2 of `CONDITION_AUDIT_20260823.md`). **Transport and kinetic
parameters largely do not.**

## Ion diffusivities — `data/electrolyte_ions.csv`

50 rows. **13 carry a basis string; 8 carry a note.** The D values are reused round numbers:

| value (m² s⁻¹) | times used |
|---|---|
| `1e-09` | **32** |
| `1.5e-09` | **24** |
| `1.33e-09` | 9 |
| `1.7e-09` | 8 |

A cation diffusivity of exactly 1×10⁻⁹ shared by 32 different cations is a **default**, not a
measurement. These feed the migration term directly — the same term that is worth up to 2× above.

## Per-species D in `julia/run_mediated.jl`

Same pattern: `3.0e-9`, `1.7e-9`, `1.0e-9`, `2.0e-9` recur across unrelated species. Each MedSpec
carries a conditions comment, but the individual ion D values do not carry sources.

## Rate constants k

All eight are order-of-magnitude literature passes (1e3, 20, 10, 0.5, 50, 100, 1e3, 100). Table S6
does document a provenance sentence per row, which is better than nothing — but the SI itself
concedes for SCN⁻: *"NO direct rate measurement located — estimate by analogy to halogenation."*
These are defensible as declared order-of-magnitude inputs. They are **not** measured values for
these systems, and the text must not imply otherwise.

## Conductivities

7 κ values are labelled ESTIMATES and print as a banner on every build (`KAPPA_ESTIMATED`). That is
honest labelling, not provenance. `1 M KCl aq = 111.3` is textbook but still not page-anchored here.

## Other known gaps

- HFIP density is marked **"rho STILL UNSOURCED"** in `SOLVENTS`.
- `THF/MeOH` and `EtOH/MeOH` viscosities are mole-fraction log-mix **estimates**.
- 16 carrier charges were flagged for author review in `ONE_PHYSICS_20260823.md`; migration acts
  only on a charged carrier, so a wrong `z` moves a ceiling by up to 2× silently.

---

# What "done" would require

1. Point `build_merged_matrix.py` at `all50_np_matrix.csv` for the 42 non-mediated rows, re-run,
   and re-derive every count and figure. Explain the ×2.876 and ×0.969 rows first.
2. Add a gate asserting that every solver output file is consumed by something — an orphan is a
   silent failure.
3. Source or explicitly declare every ion D, starting with the 32 rows sharing `1e-09`.
4. Resolve the 16 carrier charges.
5. Source the 7 estimated κ values and the HFIP density.

Until 1 is done, the phrase "all 50 solved with one physics" is **not true of the published
matrix** and should not appear in the manuscript.
