# Reviewer-readiness pass — 2026-08-22

What a referee can now check, what they will find soft, and what was fixed to get here.

---

## 1. The census a reviewer reads

The SI publishes the parameters that can support a stated claim, and carries the rest in the
machine-readable registry with the omission disclosed.

| | rows | measured | derived | assumption |
|---|---|---|---|---|
| Internal registry (complete) | 273 | 65 | 92 | 116 |
| **Published in the SI** | **201** | **56** | **73** | **72** |
| Omitted, disclosed | 72 | 9 | 19 | 44 |

**The conductivity line is the one that changed character.** Counting every row it reads
*0 measured / 8 derived / 41 assumption* — which invites "the thermal analysis rests on 41
unsourced numbers". It rests on **four**, and those four are in Table S4 with the margin by which
each would have to be wrong to overturn the verdict it carries. Five conductivity rows survive the
filter: those four, plus `0.1 M Bu4NBF4/DMF`, which no entry of the fifty uses but the manuscript
quotes (§2 below). The inert rows were making the
weakest-looking category also the most inert one.

Every state-C row that reaches the SI: **0 inert, 14 declared choices, 41 quantified with the
conclusion surviving, 17 quantified but flagged conditional, 0 signed-only, 0 inadequate.**
The 17 are the rows to read before answering a referee (`ASSUMPTION_LEDGER.md`).

## 2. Two holes found by asserting against the manuscript

Both are the same failure: *used* meant *named by one of the 50 reactions*, and the manuscript is
a consumer that definition cannot see.

- **`1 M NaOH aq`** — one of the four conductivities carrying a Fig. 5 verdict — had **no registry
  row at all**. The provenance shown for it in Table S4 came from a hand-typed literal in
  `make_si.js`. The emission loop now iterates every *registered* electrolyte and asserts coverage.
- **`0.1 M Bu4NBF4/DMF`** is quoted in the manuscript body as *κ = 3.5 mS cm⁻¹*, with a worked
  example built on it (16.8 V cell, 14.3 V ohmic, 1.4 W cm⁻²), and was carried as
  `unused-legacy (no registry row)`. Now registered as state C with a manuscript-anchored
  sensitivity: the model reproduces the passage (16.76 V, 1.476 W cm⁻²) and the claim survives for
  **κ ∈ [2.85, 6.64] mS cm⁻¹ (0.82–1.90×)**. It is now pull-list item 7b.

**`data/check_ms_numbers.py` (G-MSKAPPA)** reads `document.xml` out of the shipped `.docx` and
requires every κ the manuscript asserts to have a registry row the SI prints. It found both. It
deliberately does *not* fire on a merely named electrolyte — `1 M LiBF4/THF` appears as a cited
literature precedent with no κ of ours attached. Negative-controlled by injecting a κ that matches
no registered electrolyte.

## 3. A claim in the registry that was false

The solver-species diffusivities carried the sensitivity *"they do not set any reported i_lim"*.
That was never tested. Doubling ClO₄⁻, SCN⁻, Br⁻ and Br₂ together and re-running
`julia/run_mediated.jl`:

- 3 of the 300 cells of the merged matrix move by more than 1 %;
- **the unstirred ≥25 mA cm⁻² count moves from 11 to 12 of 50.**

The other five architecture counts (17, 21, 31, 36, 36) are unchanged and the ordering is
preserved, so no conclusion changes — the movement sits inside the ±2 of 50 precision G-SOLV
already establishes. But the counts are *not* invariant to these values, and the row no longer
claims they are. G11 and the migration gate test charge bookkeeping, not the reported counts,
which is why neither ever caught it.

## 4. Tables that could contradict their own registry

Tables S3 and S4 were hand-typed. Their numeric and state columns are now read from
`solvents.csv` / `electrolytes.csv` at build time, with any drift printed. Drift had already
happened: **Table S3 still showed HFIP μ = 1.650** after the registry moved to the page-anchored
1.619 (Krumgalz Table 3, p. 578).

Display precision is preserved when the values agree numerically, so `0.890` against a registry
`0.89` is not reported as drift while `1.650` against `1.619` is.

## 5. A cross-reference to a figure that does not exist

The SI twice called the nondimensional payoff map *"main-text Fig. 4B-c"*. There is no such figure
in the manuscript, and the SI embeds no figures at all, so it could not be promoted. Both pointers
are removed; **no content is lost**, because Eq. S17 states the three carrier laws in full. If the
map is wanted as a numbered SI figure, the SI would need figure-embedding machinery it does not
currently have — that remains open.

## 6. What a referee will still find soft, and where it is stated

- **ρ(HFIP) = 1.596 g cm⁻³** is the only unsourced HFIP property left (μ is now page-anchored).
  It enters only through ν = μ/ρ in Sc, and Sh ∼ Sc^0.356, so a 5 % error moves k_m by 1.8 %.
- **Category 6 remains 0 measured** even after the trim: the four conductivities that carry
  verdicts are 2 derived and 2 assumption. The Dorn Supporting Information (pull item 1) is the
  only realistic route to a measured one.
- **The 17 conditional rows** each name a claim that depends on where a value sits in its band.
- **Figure 1 cannot be re-run outside the author group** (CAS grant terms), disclosed in §S11.

## 7. Hallucinated-citation sweep

The failure mode: an author list bolted onto somebody else's locator. This repo has had one —
"Wallnöfer-Ogris, *Front. Chem. Eng.* 2024, 6, 1384772" is really **Eichner, Amiri, Burheim &
Lamb**, reporting a value an order of magnitude below what was claimed of it, and it lived in both
the SI and the manuscript body across several drafts.

`data/verify_citations.py` (**G-CITE**) resolves every journal citation against Crossref and
asserts the leading surname appears in the resolved record.

| | |
|---|---|
| journal citations checked | 27 |
| resolve, first author matches | **24** |
| **chimera suspects** | **0** |
| Crossref carries no author list | 3 (Kalugin; two cleared by hand) |
| books Crossref cannot adjudicate | 34 |

Negative-controlled with a **real DOI wearing fabricated authors** — the first attempt injected
the genuine Wallnöfer-Ogris locator, whose Crossref match is a junk record with no authors, so it
exercised the "unresolved" path and the control passed vacuously. That is fixed.

Three sources Crossref cannot index were **retrieved and read** rather than trusted, and are now
in `papers for model/`:

- **Ansari & Singh**, *Res. J. Chem. Sci.* 2022, 12(1), 67–69 — all four values the registry
  attributes to Table-1 p. 68 are in the text; its neat-MeCN values match `solvents.csv`.
- **Gopal & Jha**, *Indian J. Chem.* 1977, 15A, 80–83 — Table 2, DMF 25 °C column: Et₄N⁺ 35.39,
  Na⁺ 29.81, I⁻ 52.11, ClO₄⁻ 52.67. Every value the registry claims. This backs `0.2 M NaI/DMF`,
  the most exposed number in the model.
- **Bhat, Mohan & Susha**, *Indian J. Chem.* 1996, 35A, 825–831 — Table I DMF column gives
  80/76/80/78 at 293 K and 89/86/89/88 at 303 K; interpolating to 298 K gives 83.25, reproducing
  the 83.3 cited. *Locator corrected: the table prints on p. 827, not 826.*

### What that leaves

Not fabrication, but the weaker risk: a **real** paper cited for a number nobody read off the
page. Two of the three largest such sources are now closed from PDFs already in the repo:

- **R1 closed.** CRC 97th ed. **pp. 5-75/5-76** — every recalled aqueous λ° and D matches to the
  digits carried. NH₄⁺ corrected 73.6 → **73.5**.
- **R2 closed.** Le Bas increments are **Table 3-8, p. 53** of the *4th* edition — not Table 11-1,
  and the held copy is the 4th ed., not the 5th the registry named. All sixteen match. The
  **phosphorus** increment is absent from that table and unused by all 50 reactions, so it was
  demoted from `measured` to a display-only assumption rather than left on a borrowed locator.
- Wilke–Chang's φ (2.6 / 1.9 / 1.5 / 1.0) confirmed verbatim at Reid 4th ed. p. 599.

Full inventory with DOIs: `docs/LITERATURE_DOI_LIST.md`.

## 8. State of the gates

| gate | what it asserts | negative-controlled |
|---|---|---|
| `run_audit.jl` | 14 analytic limits vs the solver | n/a (analytic) |
| `audit_numeric.py` | 10 checks, 0 FAIL (4 known checker-side WARNs) | — |
| G-ASSUME | every state-C row falls in exactly one tier | ✔ 4 degenerate forms |
| G-LIVE | the dead set holds nothing load-bearing | ✔ |
| **G-MSKAPPA** | every κ the *manuscript* asserts is traceable in the SI | ✔ |
| **G-CITE** | every journal citation resolves to the paper it names | ✔ |
| G-KAPPA / G-CATD / G-SOLV / G-ANCHOR | sweep gates on κ, catalyst D, solvent properties, anchoring | ✔ |
| `verify_v22.py` | 30 checks, 0 FAIL — incl. embedded artwork vs fresh renders | ✔ fires exactly 9 |

Manuscript **v22** is current; all six embedded images md5-match their on-disk renders.
