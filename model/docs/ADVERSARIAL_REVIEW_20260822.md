# Adversarial review — can a hostile expert actually reproduce this?

**Posture:** a reviewer who models multiphysics transport for a living, knows organic
electrosynthesis, intends to re-run the pipeline, and will not use a number whose provenance
is thin. Written against the state of the repository on 2026-08-22, **after** the provenance
passes of that day — i.e. this is an audit of the audit.

**Verdict up front: the Section 4 transport model would survive this review. The provenance
apparatus built on 2026-08-22 would not survive it unamended, and three things in it were
wrong.** They are corrected below and in the code.

---

## R1 — CRITICAL. The new provenance scripts introduced ~40 unregistered, recalled constants

The 2026-08-22 pass added four analysis scripts whose stated purpose was to remove typed-in
numbers. They introduced their own. None of the following appears in
`data/parameters_provenance.csv`; all were written from recall:

| constant set | count | where used | consequence |
|---|---|---|---|
| solvent permittivities ε | 9 | `derive_kappa.py` Onsager coefficients | see below |
| aqueous λ⁰ per ion | 15 | `derive_kappa.py` aqueous ceilings | see below |
| Onsager coefficients 8.204×10⁵, 82.5 | 2 | Eq. S29 | see below |
| KCl validation target Λ(0.01 M) = 141.3 | 1 | the self-validation | see below |
| Le Bas reference volumes | 10 | G-LEBAS | see R2 |
| complex molecular weights 186 / 325 / 487 | 3 | G-CATD mass scaling | see R3 |

**The ε block carried a comment reading `CRC Handbook 97th ed., Sect. 6, "Permittivity of
Liquids", 25 C column`. No such table was opened.** That is a citation asserted from
recognition, which is the precise failure mode that put the Wallnöfer-Ogris chimera into two
drafts of this manuscript. It has been rewritten to say so.

**What survives, and why.** The finding is serious but its blast radius is bounded, and the
bound is checkable:

- **ε enters only B₁ and B₂ of the Onsager law (Eq. S29), and this work adopts nothing from
  Onsager.** The script's own conclusion is that the limiting law is outside its validity range
  at every working concentration here — the √c term exceeds 20% of Λ⁰ in 8 of 8 cases, and
  returns a negative Λ twice. No number that reaches the model depends on any ε.
- **The λ⁰ values split cleanly, and the load-bearing half is traceable.** The MeCN set
  (Li⁺ 69.97, ClO₄⁻ 103.6, Et₄N⁺ 85.1, PF₆⁻ 102.8) and the DMF set (Na⁺ 29.81, I⁻ 52.11) are
  documented as retrieved in `KAPPA_SOURCING_DOSSIER.md` rows 14/20/38/55, citing Gong et al.
  Table 2 p. 3518 and Gopal & Jha Table 2 p. 81. **Those six are the ones that matter**, because
  the four rows whose Kohlrausch ceiling is load-bearing are the MeCN and DMF assumptions. The
  fifteen aqueous λ⁰ are recalled — but they compute a ceiling on four aqueous rows that are
  already `derived` by an independent CRC route (p. 5-71 + concentrative properties) and carry
  10–42× margins. Nothing rests on them.
- **The KCl validation is weaker than it reads.** Λ⁰(K⁺), Λ⁰(Cl⁻), the 141.3 target and both
  Onsager coefficients are four independent recollections. Their agreeing to 0.7% is evidence
  the *equation is implemented correctly*; it is not a page-anchored validation and must not be
  quoted as one. The script now says this at the point of use.

**Status:** comments corrected in `derive_kappa.py`; every recalled block is labelled
`RECALLED, NOT RETRIEVED` with the reason it is nonetheless usable. **Not closed** — a
retrieval pass on CRC Sect. 5 and Sect. 6 would close it and is the top pull item.

## R2 — SERIOUS. The Le Bas "closure" gate is partly circular

G-LEBAS compares computed molar volumes against reference values. For benzene the computed
value is 6(14.8) + 6(3.7) − 15 = 96.0 and the reference is a **recalled** 96.0 — but the
published Le Bas benzene volume *is* that same additive sum. For most of the ten compounds this
test compares the code's arithmetic against a remembered result of the same arithmetic.

It is not worthless: it catches ring detection, implicit-H counting, the acid-hydroxyl special
case and increment lookup, all of which can fail silently. Break ring detection and benzene
returns 111. But it is an **implementation regression test, not independent verification of the
increment set** — the increments are separately cited row-by-row to Table 11-1.

Tellingly, the only two compounds whose recalled value differs from naive addition —
chlorobenzene (115.0 vs 116.9) and diethyl ether (104.8 vs 103.6) — are exactly the two that
disagree, at 1.7% and 1.1%. The 3% tolerance accommodates that; it is not a measured agreement.

**Status:** relabelled in code and in its printed output. The claim "10/10 within 3%" now ships
with what it does and does not test.

## R3 — The G-CATD mass-scaling step is an assumption stacked on a recalled anchor

r ∝ M^(1/3) presumes comparable density between a neutral metallocene and a charged tris-chelate.
Ferrocene ≈ 1.49 g cm⁻³ and bipyridyl complexes ≈ 1.4–1.5, so it is defensible — but it is an
assumption, the three molecular weights are recalled, and the ferrocene D = 2.4×10⁻⁵ cm² s⁻¹
anchor traces to a textbook *range* (1.7–2.4×10⁻⁵), not a page-anchored point value.

**What holds regardless:** the conclusion under test is one-sided. The typed radii (4–5 Å) are
*larger* than any scaling predicts (3.2–3.7 Å), so the model understates catalyst D and states
"10 of 11 clear 25 mA cm⁻² in none" conservatively. Charge and solvation push the same way. A
reviewer can reject the scaling entirely and the direction of the conclusion is unchanged.

## R4 — Figure 1 is not externally reproducible, and the SI does not say so

`Figure_1b_Kasie/` holds the four parquet files Figure 1 is built from, under CAS grant terms
that forbid placing per-record data in the paper, the SI, a public repository or a data archive.
**A reviewer therefore cannot reproduce Figure 1 at all**, and the SI contains no statement to
that effect — a search for any disclosure of the restriction returns nothing.

That is a real defect. A reviewer will attempt it, fail, and be entitled to ask why they were
not told. The honest position — aggregate statistics and the rendered figure are publishable,
per-record data is not — is defensible, but it has to be *stated*, alongside what a reviewer
can check instead: the corpus size, the class counts, the polarity shares, and the fact that the
pipeline reproduces bit-exactly on a pinned environment.

**Status: CLOSED, same day.** §S11 now states the limit explicitly: everything in S1-S10 runs
from the shipped files with no restricted dependency, main-text Figure 1 cannot be re-run
outside the author group, the aggregate layer a reader CAN check is enumerated (corpus size,
class counts, polarity shares, condition fractions, funnel counts), and the pinned environment
that reproduces it bit-exactly is named -- including that the rdkit pin is load-bearing.

## R5 — Table S2 places a ~50-source verification burden with no bundle

Each of the fifty rows is page-anchored to a primary article, patent or SI. The repository holds
58 PDFs, of which at least 11 are publisher copies (Science, Nature, Angew., JACS) that cannot
be redistributed with the SI. A reviewer checking Table S2 must therefore obtain ~50 sources
independently.

This is normal for a Perspective and is not a defect in the work — but the quoted anchors must
be exact, because each wrong one costs a reviewer a document retrieval before they discover it.
The two known imprecise rows (Shono transfer-by-analogy; the epoxidation Henry's-law
concentration) are now named explicitly in §S1.2 rather than folded into the verified count.

## R6 — Ansari & Singh is a weak journal, and it now carries a derived row

`H2O/MeCN 2:1 v/v` moved from assumption to derived on *Res. J. Chem. Sci.* 2022, 12(1), 67–69 —
a low-impact, non-indexed journal. A hostile reviewer would object on venue alone.

The mitigation is real and was applied before adoption: the paper's pure-component values
(ρ = 0.7767 g cm⁻³, η = 0.346 cP) reproduce the CRC 97th ed. MeCN entries carried here (0.776,
0.343) to 0.3% and 0.9%. A source that reproduces two independent reference values to under 1%
is measuring something. The row also sits inside the ±25% band over which G-SOLV shows no
published count moves.

**Acceptable, but the venue must stay visible in the citation** — it is, in both the registry and
the Table S3 caption.

---

## What would survive this review unamended

- **The Section 4 transport model.** Julia, standard library only, no restricted data, every
  input in-repo. `run_audit.jl` 14/14. A reviewer can clone and re-run it.
- **The 48 page-verified concentrations.** Explicit mmol/mL arithmetic, anchor quoted per row.
- **The Wilke-Chang chain.** Correlation cited to pp. 264–270 with its own φ set; every Le Bas
  increment cited to Table 11-1; assembly regression-tested.
- **Every conclusion's sensitivity.** κ 2.9× both directions; catalyst radius 1.26×; solvent
  viscosity ±2 of 50 counts with the ordering invariant. All computed, all gated,
  all negative-controlled.
- **The equation cross-reference.** Eqs. S23–S31 in §S9.0, `Eq.` column in Table S7, 81 rows
  tagged, and the tagger restricted to the leading method statement after a first version
  mislabelled 24 rows as Casteel-Amis.

## The three things a reviewer should still be told plainly

1. **No diffusion coefficient in this work is measured.** All are correlation estimates; the one
   measured anchor sits −24% from its prediction. Absolute i_lim is good to about ±25%; ratios
   and orderings are not affected.
2. **No conductivity in this work is measured.** κ enters no transport quantity. The two that
   reach a Fig. 5 conclusion are bounded and need a 2.9× error to break.
3. **Figure 1 cannot be re-run outside the author group.** R4.

## Pull list, re-ranked after this review

1. **CRC Sect. 5 (ionic conductivity) and Sect. 6 (permittivity)** — closes R1 outright and
   converts ~24 recalled constants into page-anchored ones.
2. **Reid/Poling Table 3-11 or Perry's Table 2-400** — closes R2 by making G-LEBAS an
   independent check rather than a regression test.
3. **A page-anchored ferrocene D** — strengthens R3.
5. Everything on the previous pull list, unchanged.


---

# Round 2 — after the fixes

Re-run against the same surfaces, plus the ones the fixes could have broken.

## R1 — was CRITICAL, now largely closed by an actual retrieval

Vanýsek, *"Equivalent Conductivity of Electrolytes in Aqueous Solution"* (CRC Handbook) was
**retrieved in full** and archived at
`papers for model/vanysek_CRC_equivalent_conductivity_of_electrolytes.pdf`. It supplied four
things this work had been taking from memory:

| | recalled | retrieved | |
|---|---|---|---|
| Debye–Hückel–Onsager equation | written from memory | printed in the table header | ✓ |
| Onsager constants for water, 1:1 | B₂ = 60.65, B₁ = 0.2297 computed | **A = 60.20, B = 0.229** | +0.7%, +0.3% |
| KCl Λ° | 149.8 | **149.79** | ✓ |
| KCl Λ(0.01 M) validation target | 141.3 | **141.20** | computed 140.28, −0.65% |

The aqueous ceilings now read **retrieved electrolyte Λ°** (NaOH 247.70, NaCl 126.39,
KHCO₃ 117.94) instead of recalled per-ion sums.

**And the recalled per-ion set is now independently validated.** Kohlrausch's law of
independent migration says ion contributions are additive across salts, so differences of
*retrieved* electrolyte Λ° must equal differences of *recalled* per-ion values — retrieved on
one side, recalled on the other, no circularity:

```
K+ - Na+   (chlorides)  retrieved +23.40   recalled +23.40
K+ - Na+   (iodides)    retrieved +23.43   recalled +23.40
I- - Cl-   (sodium)     retrieved  +0.49   recalled  +0.49
I- - Cl-   (potassium)  retrieved  +0.52   recalled  +0.49
```

Agreement better than **0.1%**. That is a real check, unlike the Le Bas regression test.

**A bonus the retrieval delivered:** the table states its own validity limit verbatim —
*"reliable for c < 0.001 mol/L; with higher concentration the error increases"* — which is
100–3000× below every working concentration here. The conclusion that a limiting-conductivity
route cannot supply κ at preparative concentration is now the source's own statement, not an
inference.

**Residual:** the nine ε values remain recalled. **This is now verified harmless rather than
argued harmless:** a repository-wide search returns **zero** consumers of `kappa_onsager`
outside its own script, so no adopted number depends on any ε.

## R2, R3 — closed as far as they can be

R2 stands as relabelled: G-LEBAS is an implementation regression test and says so. The genuinely
independent test that R2 wanted now exists elsewhere — the Kohlrausch check above.

R3: the three molecular weights are **computed from molecular formula** with IUPAC atomic
weights (C₁₀H₁₀Fe, C₁₈H₂₄Br₂N₂Ni, C₁₆H₁₄CoN₂O₂), not typed. The recalled values were right to
<0.1%, which is not the point.

## R7 (new) — the retrieval nearly created a contradiction, and did not

§S6.1 already argued that the Vanýsek table is **not applicable** to the concentrated aqueous
rows, "whose NaOH row in fact stops at 0.01 M". The retrieval **confirms that exactly** — the
0.02, 0.05 and 0.1 M columns of the NaOH row are dashes.

Citing the same table under Eq. S28 could therefore have read as contradicting §S6.1. It does
not, because only the **infinite-dilution column** is used, which is the only quantity a ceiling
needs. A clause now says so at the point of use: the table *bounds* these rows from above, it
does not *supply* their κ.

## R8 (new) — the archived source is not distributable, and is not distributed

The CRC table was archived into `papers for model/`, which sits **outside** `Section4_Model/`
and is referenced by the SI zero times, so it does not ship. Correct for copyright; the cost is
that a reviewer must obtain it themselves. The citation is precise enough that they can.

## Round-2 verdict

The three findings that were mine are closed or bounded, and one of them closed by retrieving
the source rather than by relabelling. What remains open is unchanged and stated plainly: no
measured D, no measured κ, Figure 1 not externally re-runnable. Each is now accompanied by an
equation, a bound, or a disclosure — which is the most that can honestly be claimed.


---

# Round 3 — the fix-everything pass

Two more CRC tables were **retrieved in full and archived**, which converted two things that had
been described in prose into things that are now recomputed on every run.

## What closed

**CRC p. 5-71, "Electrical Conductivity of Aqueous Solutions"** — archived at
`papers for model/CRC_electrical_conductivity_of_aqueous_solutions_p5-71.pdf`. This is the table
the registry's three derived aqueous conductivities come from. Until now the registry *described*
that derivation and quoted three numbers from the NaCl row; nothing recomputed it. **New gate
G-CRC** re-derives all three from the archived table:

| row | mass % | κ(20 °C) from table | 20→25 °C band | registry | |
|---|---|---|---|---|---|
| 1 M NaOH aq | 3.840 | 162.3 | 175–180 | 178.0 | PASS |
| 2 M NaCl aq | 10.846 | 133.6 | 144–148 | 148.0 | PASS |
| 1 M Na₂CO₃ aq | 9.600 | 72.2 | 78–80 | 80.0 | PASS |

The registry's quoted source values (NaCl 5% = 70.1, 10% = 126, 15% = 171) match the retrieved
table exactly. **The CRC route is now verified rather than asserted.**

**Le Bas ring correction resolved.** A search return suggested 15.6 for the six-ring correction
against the −15.0 used here. 15.6 is the *nitrogen* increment, garbled in the snippet: 6(14.8) +
6(3.7) − 15.0 = 96.0, which is the universally cited Le Bas benzene volume. The increment set and
the ring correction are mutually consistent with a known anchor.

## What could not be closed, and why

Each of these was attempted in this pass and failed for a stated reason, not for lack of trying:

- **HFIP μ and ρ.** Searched repeatedly; every hit is hexafluoro*propane* (R236fa), a different
  compound. No primary measurement for hexafluoroiso*propanol* was located. Exposure: 2 rows,
  both substrate-carried, both clearing 25 mA cm⁻² comfortably (220 and 44 mA cm⁻²), and both
  inside the ±25% band over which G-SOLV shows no published count moves.
- **CRC permittivity table.** Not present in the mirror that supplied the other two. The nine ε
  values stay recalled — and stay verified-unused: zero consumers of the Onsager estimate exist
  outside its own script.
- **A published Le Bas table.** Not retrievable. G-LEBAS remains an implementation regression
  test and says so; the independent check that R2 wanted is now the Kohlrausch one.
- **Measured D for the actual carriers.** Does not exist for these coordination complexes in
  these solvents. Bounded instead, one-sided, 1.26× margin.
- **Measured κ for the organic electrolytes at working concentration.** Does not exist; the
  retrieved Vanýsek table states its own limit as c < 0.001 mol/L.
- **Figure 1 external reproducibility.** CAS grant terms. Disclosed in §S11.
- **Four named mixed-solvent pull targets** (Cunningham 1967, Wode & Seidel 1994, Aminabhavi
  1995, González 2007). Paywalled; the rows say "PULL NEEDED" and name them.

## Final state of the provenance apparatus

Six gates now run on every build, all negative-controlled where a control is meaningful:

| gate | what it checks |
|---|---|
| G-LEBAS | Le Bas assembly, 10 reference compounds, ≤1.7% (regression test) |
| G-CRC | three aqueous κ re-derived from the archived CRC p. 5-71 table |
| G-KAPPA | six registry κ sensitivity claims recomputed from `thermal_model.py`, <0.1% |
| G-CATD | catalyst-radius conclusion, 1.26× margin against a mass-scaled ferrocene anchor |
| G-SOLV | threshold counts ±2 of 50, architecture ordering invariant |
| Kohlrausch | recalled per-ion λ⁰ vs retrieved electrolyte Λ°, <0.1% |

plus `run_audit.jl` 14/14, `audit_numeric.py` 0 FAIL, the SI citation-order audit, the
stratification gate and `verify_v21.py` 30/30.

**Three sources retrieved and archived this pass** so a reviewer can check them without a
subscription: Vanýsek equivalent conductivity, CRC p. 5-71, and Ansari & Singh MeCN–water.


---

# Round 4 — surrogate anchoring (Eqs. S32, S33)

Justin's proposal: rather than predicting D absolutely, take a MEASURED D for a chemically or
structurally similar species and correct it onto the target. This is the stronger of the two
options he raised, and it is now implemented.

## Why the ratio form is better than a surrogate substitution

"Use the D of a similar compound and call it close enough" leaves the error unquantified. The
ratio form makes the correction explicit and, more importantly, **cancels the term that is
actually wrong**. Writing Eq. S2 for two solutes in the same solvent, every solvent-dependent
factor and the correlation constant itself divide out:

    D_A = D_ref (V_ref / V_A)^0.6                                    (Eq. S32)

On the one system where a measurement exists, Eq. S2 is 24% low on ferrocene in MeCN. That error
lives in the prefactor. A ratio removes it exactly and leaves only the assumption that the size
dependence has the right SHAPE between two similar solutes — a much weaker claim than trusting
the absolute constant. Eq. S33 is the Stokes-Einstein analogue and permits a solvent change,
because mu is the only solvent property in it; where no molar volume exists the radius ratio is
taken structurally as M^(1/3).

## Applied to the eleven metal-complex rows

These are the rows with a typed hydrodynamic radius, and Le Bas cannot reach them. Anchoring on
ferrocene gives D values **1.14-1.56x higher** than the assumed radius does.

**The two estimates bracket rather than agree, and neither is adopted over the other.** The
assumed radius is unsourced; the anchored value inherits ferrocene's neutrality, and the charge
and stronger solvation of these complexes raise their effective radius and push the true D back
down toward it. Adopting either alone would be a choice without evidence.

What matters is that **the conclusion does not depend on the choice**. New gate **G-ANCHOR**:

| | typed radius | ferrocene-anchored |
|---|---|---|
| catalyst rows clearing 25 mA cm⁻² | 1 / 11 | **1 / 11** |
| second-best row | 16.2 mA cm⁻² | **19.9 mA cm⁻²** |

5.1 mA cm⁻² of headroom at the top of the bracket. The "ten of eleven clear in none" result is
bracket-proof, which is a strictly stronger statement than it could make before.

## Where the same trick cannot yet reach kappa

The analogous same-family transfer for conductivity —
kappa(Et₄NBF₄/MeCN) = kappa(Bu₄NBF₄/MeCN) x Λ°(Et₄NBF₄)/Λ°(Bu₄NBF₄) at matched concentration,
same solvent, same anion, homologous cation — is far more defensible than the cross-family
transfers the dossier rejects, because the attenuation Λ/Λ° should be nearly identical for two
tetraalkylammonium tetrafluoroborates at the same c. It is blocked by one number:

  * Λ°(Bu₄NBF₄/MeCN) = 171.1  — the SI states this as measured                    HAVE
  * λ°(Et₄N⁺, MeCN)  =  85.1  — Gong Table 2 p. 3518, dossier-retrieved            HAVE
  * λ°(Bu₄N⁺, MeCN)           — needed to split 171.1 into cation and anion       MISSING

It is deliberately NOT filled from recall. Dorn Table 3 carries a measured Casteel-Amis fit for
ACN/(C₂H₅)₄NBF₄ that would settle it outright; the ACS article is paywalled and was not
retrieved. That single pull converts `0.077 M Et4NBF4/MeCN` from a bound into a derived value,
and it is now the top item on the list.

## Standing caveat this inherits

Every anchored number scales linearly with the ferrocene D, which is a textbook RANGE
(1.7-2.4e-5) read at its upper end rather than a page-anchored point measurement (R3). Reading
it at the bottom of that range would lower every anchored D by 29% and move the bracket down
toward the typed-radius estimate — which strengthens the conclusion rather than threatening it,
since the claim is that these rows do NOT clear.
