# What has to change in v40, and why

Generated 2026-08-24 from the three gates that currently fail: **G-MSDERIVED**, **G-ECBAND**,
**G-NUMERIC**. They fail because the model moved to full physics for all 50 rows (see
`PROVENANCE_PUSH_20260824.md` §17) and the text still prints the pre-change numbers. **Nothing here
has been edited in the manuscript or the SI** — changing published scientific claims is the
author's call, especially where a count moves.

Every "model gives" figure below comes from `julia/tier0_ec_matrix.csv` as rebuilt tonight.

---

## 1. The structural change to state first

The published matrix is now built on **one physics for all 50 rows** — Nernst–Planck with
migration everywhere, the EC′ source added on the 8 mediated rows. It was previously assembled from
the Tier-0 **Fick** table with the mediated overlay on top, so 42 of 50 rows had no migration term
while the counts were tallied across the mixed column.

Every count rises, by one to three rows per architecture. That direction is expected — migration
can only help a charged carrier reach the electrode.

**SUPERSEDED 2026-08-24 — every column is out of 50.** This section previously said
`Br⁻ oxidation × unstirred` does not converge, is written as NaN, and that the unstirred column is
"out of 49, not 50". That cell now converges: **23.749 mA cm⁻², `flag=ok`**, by the ordinary
ramp + c-control path. **There are zero unresolved cells in the 50 × 6 matrix**, so no column
carries a reduced denominator and nothing needs a "out of 49" caveat anywhere.

What had blocked it was a defect in the Newton trust region, not the physics and not a missing
continuation — see `CELL48_BROMINATION_UNSTIRRED.md`. Two consequences for the numbers below:

* the unstirred counts are now **out of 50** (11/50 clearing 25, 9/50 clearing 50);
* `Br⁻-mediated Hofmann × unstirred` moved 111.229 → 111.506 mA cm⁻² (+0.25%), which crosses no
  threshold.

Nothing else in the matrix moved: 43 of 48 mediated cells are bit-identical, 3 differ in the last
1–2 ulp, and the 50-reaction NP layer is **300 of 300 bit-identical**.

---

## 2. Manuscript body

| where | prints | model now gives |
|---|---|---|
| count clearing 25, unstirred | *(the phrase `11/50` is no longer present — the check needs re-pointing at the new wording)* | **11 of 49 resolved** |
| count clearing 50, RCE | `34/50` | **33** |
| median, unstirred — §4 body | "median limiting current density is only **6.0** mA cm⁻²…" | **6.1** |
| median, unstirred — Fig 1b body | "rises from **6.0** mA cm⁻² in an unstirred batch cell" | **6.1** |
| median, RCE — Fig 1b body | "to **121** mA cm⁻² at a rotating-cylinder electrode" | **121.7** |
| median, unstirred — TRL-E table | "**6.0** median (unstirred)" | **6.1** |
| Fig 2b caption medians | "**6, 17, 19, 48, 108 and 121** mA cm⁻² from unstirred batch to rotating cylinder" | **6.1, 17.1, 19.4, 48.6, 108.5, 121.7** |

The median shifts are cosmetic (6.0 → 6.1). **The RCE ≥50 count is not**: 34 → 33.

---

## 3. SI — the Tier-0 → EC′ bands (§S5.4)

These were printed as ranges spanning the Tier-0 and EC′ layers. With full physics as the base
layer the bands narrow and shift up:

| architecture | SI prints | model now gives |
|---|---|---|
| natural | 10–12 | **10–11** |
| stirred | 15–17 | **17–18** |
| flow | 18–21 | **19–20** |
| thingap | 30–31 | **31–31** |
| rde | 33–36 | **36–36** |
| rce | 33–36 | **36–36** |

Three of these (thingap, rde, rce) are now degenerate — the two layers agree — because those
architectures were already close to their ceilings.

Also flagged by G-NUMERIC: **EC′ flow ≥50** — SI says `13→14`, the model gives **(12, 15)**.

---

## 3b. SI Table S5 — the main results table

Every row changes. This is the table a reader looks at first.

| archetype | Table S5 prints | model now gives |
|---|---|---|
| Unstirred batch | 6.0, 11/50, 9/50 | **6.1, 11/49, 9/49** |
| Stirred batch | 17.1, 17/50, 14/50 | **17.1, 18/50, 15/50** |
| Parallel-plate flow (1 mm) | 19.4, 21/50, 14/50 | **19.4, 20/50, 15/50** |
| Thin-gap microflow (250 μm) | 48.4, 31/50, 24/50 | **48.6, 31/50, 24/50** |
| RDE 1600 rpm | 108, 36/50, 32/50 | **108.5, 36/50, 32/50** |
| Rotating cylinder 3000 rpm | 121, 36/50, 34/50 | **121.7, 36/50, 33/50** |

Substantive: stirred ≥25 **17 → 18** and ≥50 **14 → 15**; flow ≥25 **21 → 20** and ≥50 **14 → 15**;
RCE ≥50 **34 → 33**. Unstirred is now out of **49**.

## 3c. A dangling cross-reference

The correlation table justifies the stirred film as
*"δ ≈ 100 μm (fixed) — assumption; no source. Tested band 50–200 μm (**Table S7g**)"*.

**There is no Table S7g in the SI.** The only S7 caption is `Table S7.`, and it is not a δ
sensitivity table. So the one quantitative support offered for an explicitly unsourced assumption
points at nothing.

The band is worth tabulating for real, because it is large — across 50–200 μm the stirred ≥25 count
runs **29 / 18 / 15** (see PROVENANCE_PUSH §20). Either add the table the text promises, or drop the
reference.

## 4. Two things that need a decision before the text is final

1. **The carboxylate carrier concentration** (Kolbe, decarboxylative elimination). Both rows
   declare more carrier charge than their electrolyte can balance — 5.0× and 13.3×. Three readings,
   up to 10× apart. `julia/carboxylate_decision.jl` solves all three at all six architectures.
   Until this is settled, neither row's ceiling should be quoted.
2. **What a mediated row reports** — product-forming current or total current. Every other cell
   answers the same either way; `Br⁻ × unstirred` is where they diverge by 4.18×, and it is the
   cell now excluded from the counts. Under the product-forming reading its whole bracket sits a
   factor of four below 25 mA cm⁻², so the unstirred count is robust either way — but the table
   needs to say which quantity it reports.

---

## 4b. A limitation that should be stated, not just recorded

`G-KSENS` (run overnight) shows that an order of magnitude in the homogeneous rate constant — the
uncertainty the SI itself declares for these values — moves a threshold on **four of the eight
mediated rows**: ACT-mediated alcohol oxidation (5 cells), HMF → FDCA (3), BQ-mediated Wacker–Tsuji
(2), aryl thiocyanation (1). See PROVENANCE_PUSH §21.

The worst is **ACT-mediated alcohol oxidation**, the Stahl hectogram exemplar: five of its six cells
cross 25 mA cm⁻² if k is ten times larger. Its ceiling is currently reporting the kinetics estimate
as much as the transport.

By contrast Cl⁻ ethylene epoxidation moves 0.1% — it is genuinely transport-limited. That contrast
is worth making in the text: **sensitivity to k is a read-out of whether a mediated ceiling is a
transport statement or a kinetic one**, and only some of these are transport statements.

## 5. How to check the text once it is restated

    cd Section4_Model && ./run_gates.sh

G-MSDERIVED, G-ECBAND and G-NUMERIC should go green. If they do not, the remaining message names
the exact string and the exact value. **G-COND will still say REVIEW NEEDED** — that is the 11 rows
whose conditions live in Supporting Information we do not hold, and it is a standing state, not a
regression.


---

## Appendix (2026-08-24) — final numbers after the trust-region fix

`julia/tier0_ec_matrix.csv`, rebuilt with **zero unresolved cells**:

| architecture | median (mA cm⁻²) | ≥25 | ≥50 |
|---|---|---|---|
| unstirred batch | 6.109 | 11/50 | 9/50 |
| stirred batch | 17.085 | 18/50 | 15/50 |
| parallel-plate flow | 19.443 | 20/50 | 15/50 |
| thin-gap microflow | 48.597 | 31/50 | 24/50 |
| RDE 1600 rpm | 108.489 | 36/50 | 32/50 |
| rotating cylinder | 121.705 | 36/50 | 33/50 |

**G-MSDERIVED — seven manuscript numbers still to change:**

| claim | manuscript prints | model gives |
|---|---|---|
| count clearing 25, unstirred | 12/50 (v39) | **11/50** |
| count clearing 50, RCE | 34/50 | **33/50** |
| median, unstirred (Sec 4 body) | 6.0 | **6.1** |
| median, unstirred (Fig 1b body) | 6.0 | **6.1** |
| median, RCE (Fig 1b body) | 121 | **121.7** |
| median, unstirred (TRL-E table) | 6.0 | **6.1** |
| Fig 2b caption medians | 6, 17, 19, 48, 108, 121 | **6.1**, 17, 19, 48, 108, 121 |

**G-ECBAND — three SI brackets still to change** (three already agree):

| architecture | SI prints | model band |
|---|---|---|
| unstirred | 10–12 | **10–11** |
| stirred | 15–17 | **16–18** |
| flow | 18–21 | **17–20** |
| thin-gap | 30–31 | 30–31 ✓ |
| RDE | 33–36 | 33–36 ✓ |
| RCE | 33–36 | 33–36 ✓ |

**A statement the SI can now make that it could not before:** every one of the 48 mediated cells
reaches its limit by the ordinary current ramp followed by c-control. **No cell requires any
continuation** — 46 `c-control`, 2 `direct-ramp`, 0 continued. Before the trust-region fix exactly
one cell took a continuation path, and it was the defective one.

*(A gate bug was found while producing this: `check_ecprime_band.py` filtered continuations with
`m.path != "direct"`, and `"direct"` is not a value that column ever takes, so it reported "48 of
48 reached by delta-continuation" unconditionally. Fixed, and it now asserts the column holds only
recognised path names so a new path cannot be silently miscounted.)*

---

## Appendix B (2026-08-24) — solvent boiling points pulled from CRC

`figs/thermal_model.py` hardcoded THF 66, MeCN 82, DMF 153, aq. NaOH 100 °C with **no registry
row, no citation and no sensitivity**, while every other constant in that file had all three. They
are not decorative: they enter as `(T_boil − T_amb)` and set the Fig. 5 boil-off ceilings.

Retrieved from CRC 97th ed. §15 "Laboratory Solvents and Other Liquid Reagents", pp. 15-13 ff. —
the same table `solvents.csv` already cites for μ and ρ — layout-preserving extraction, molecular
weights on the same rows (41.052 / 73.094 / 72.106) matching `solvents.csv` exactly.

**Adopted at the author's direction, 2026-08-24:** THF 66 → **66.0**, MeCN 82 → **81.6**,
DMF 153 → **152.8**, aq. NaOH 100 → **99.974** (pure water; 1 M NaOH boils ~0.5 K higher, so this
is the conservative choice for a ceiling). All four now registered as `measured` with that locator.

### Ceilings that moved

| quantity | before | after |
|---|---|---|
| unstirred THF ceiling | 29.5 | 29.5 (unchanged) |
| unstirred MeCN ceiling | 88.2 | **87.8** |
| unstirred DMF ceiling | 88.8 | 88.8 (unchanged) |
| unstirred aq. NaOH ceiling | 282.5 | **282.4** |

### Published numbers that must change

**Manuscript — Fig. 5c:**

| claim | manuscript prints | model now gives |
|---|---|---|
| zero-gap DMF shortfall | 13.9× | **14.0×** |
| zero-gap MeCN shortfall | 20.5× | **20.6×** |

**SI:**

| claim | SI prints | model now gives |
|---|---|---|
| S6.1 microfluidic MeCN | 440, 0.88× | **437.7** (margin still 0.88×) |
| S9 MeCN flip | reverses only at κ ≥ 31.6 mS cm⁻¹ | **32.15** |

Everything else holds: the Fig. 5a caption values 88 and 89 still round the same way, the Fig. 5b
zero-gap values still round to 66 / 110 / 180 / 149, and THF's 29 and aq. NaOH's 283 are unmoved.

### Artwork

**Fig. 5 has been re-rendered** (`_replacement_artwork/MS_Fig5_figK_boiloff_remediated.png`) with
`/opt/anaconda3/bin/python3.12` per trap 8, and its own provenance gate passed — "every plotted
value equals results/figK_thermal.json". `results/figK_thermal.json` was regenerated first.

**Consequence: the Fig. 5 embedded in v39 is now stale**, so `verify_v39.py` G1 will fail until a
v40 re-embed. That is expected, and it is the gate that exists to catch exactly this.

---

## Appendix C (2026-08-24) — mediated substrate diffusivities corrected, and one V40 edit WITHDRAWN

The 8 mediated substrate D values were hand-typed with nothing computing them. They are now
generated by `data/build_mediated_substrates.py` (Wilke–Chang on named structures) into
`data/mediated_substrates.csv` and gated by **G-DSUB**. Running the arithmetic showed three were
never Wilke–Chang values:

| reaction | substrate (from the exemplar PDF) | was | now | |
|---|---|---|---|---|
| Hofmann | **2-phenylacetamide 1a**, 0.4 M | 2.00e−9 | 1.861e−9 | 7.5% high |
| NHPI allylic | **valencene (4)** → nootkatone | 1.78e−9 | 1.945e−9 | 8.5% low |
| bromination | **anisole** — registry had misnamed it "naproxen-arene" | 6.25e−10 | 9.148e−10 | **46% low** |

The other five were confirmed by exact reproduction of the carried value (ratios 1.000, 0.997,
1.000, 1.002, 0.999), so both their structures and the method are verified.

### Consequence for the published counts

**The unstirred ≥25 count returns to 12/50, which is what the manuscript already prints.**
`Br⁻ oxidation × unstirred` moves 23.749 → **25.341 mA cm⁻²** and clears the threshold.

> **WITHDRAWN from Appendix A:** the edit "count clearing 25, unstirred: 12/50 → 11/50" is
> **no longer required**. The manuscript was right; the model had been wrong, because that cell was
> carrying a diffusivity for the wrong molecule. `check_ms_derived.py` had a stale pinned
> expectation of `"11/50"`, now corrected to the manuscript's `"12/50"`.

Every other count and median is unchanged: unstirred ≥50 still 9/50, medians 6.1 / 17.1 / 19.4 /
48.6 / 108.5 / 121.7. Six mediated rows moved by ±6–7% (bromination up, Hofmann down) and none of
those crossed a threshold.

### Still required from Appendix A

RCE ≥50 **34/50 → 33/50**; the four medians 6.0 → 6.1 and RCE 121 → 121.7; the three SI EC′
brackets; plus Appendix B's Fig. 5c and SI MeCN items.

### Appendix C, addendum — the restored 12/50 is correct but NOT robust

`data/sensitivity_substrate_D.py` (**G-DSUBSENS**) sweeps all eight substrate diffusivities ±15%
together — Wilke–Chang's own accuracy band — re-solving the 48-cell mediated matrix at each point.

Five of the six architecture counts do not move. **The unstirred count does.**

`Br⁻ oxidation × unstirred` reads **25.34 mA cm⁻²**, clearing the 25 threshold by only **1.36%**.
The measured elasticity is `d(ln i)/d(ln D_S) = 0.170` (taken directly from the 46% correction to
that row), so:

> **the unstirred count falls 12/50 → 11/50 as soon as D_S is 7.6% below its Wilke–Chang value —
> inside the ±10–20% usually quoted for the method.**

So the manuscript's **12/50 is right as computed, but it rests on a Wilke–Chang estimate holding to
better than 8%.** That should be stated in the SI. It is not a reason to change the number; it is a
reason not to lean on it. Every other count and every median is insensitive across the band.
