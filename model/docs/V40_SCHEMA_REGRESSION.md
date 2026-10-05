# v40 — the schema regression, and the fifteen numbers it hid

2026-08-25. Two findings, one cause and one consequence.

## 1. `build_merged_matrix.py` silently narrowed the published matrix, killing four generators

`data/build_merged_matrix.py` was added on 2026-08-24 to put ONE physics (Nernst–Planck with
migration) under all 50 rows. It rewrote `julia/tier0_ec_matrix.csv` **without its `class` and
`carrier` columns**:

```
was:  class,reaction,carrier,natural,stirred,flow,rde,rce,thingap
became: reaction,natural,stirred,flow,thingap,rde,rce
```

The passthrough was a no-op by construction:

```python
out = m.reset_index()
if "cls" in t0.columns:                                    # the column is spelled `class`
    out = out[["cls", "reaction"] + COLS] if "cls" in out.columns else out
```

The outer guard is never true, so the ternary inside it — itself guarded — falls through to
`out` unchanged. It reads like a deliberate conditional and does nothing.

`figs/model_medians.py` selects the published matrix on `carrier`
(`TIER0_EC[TIER0_EC.carrier == "catalyst"]`), so **four generators died outright**:

| generator | figure |
|---|---|
| `make_figs_sec34.py` | Fig 2, Fig 3 — both author-priority |
| `combined_figure.py` | Fig 4 |
| `make_fig_carrier.py` | `sec4_Fig_carrier.png` — author-priority |

**Why no gate caught it.** The artwork gates compare embedded bytes against on-disk bytes. A
crashed generator leaves the previous PNG in place, so both sides were frozen and agreed
perfectly, while neither could be reproduced. `verify_v39.py` G1 reported PASS on figures whose
generators could not run.

**The same shape bit me while diagnosing it.** I re-ran four generators, compared hashes, and
reported "all four re-render byte-identical" — but three had crashed, so I was comparing
untouched files to themselves. *A hash comparison is meaningless unless the producing command
is confirmed to have exited clean.* That is now written into `verify_v40.py`'s header.

Fixed: the two columns are carried through and their presence is asserted, so a missing
metadata column is a hard stop rather than a silent narrowing.

## 2. Three more checkers were asserting invariants the model had left behind

All three predate this session's work and all three are fixed:

- **`audit_numeric.py` merge check** compared the published matrix against `tier0_matrix.csv`
  (Fick, migration-free). Since the one-physics merge the published matrix is NP, so every one
  of the 300 cells was reported as a failure. Now compares against `all50_np_matrix.csv`.
- **`archetype_bands.verify_against_tier0`** did the same thing inside a figure generator,
  failing by 65% on the charged carriers and blocking Fig 4B. Now compares Fick to Fick.
- **`make_figs.py` / `make_fig_main.py`** still asked for `"Kolbe homocoupling of hexanoate"`;
  the row was relabelled to `10-undecenoate` when its substrate was page-verified.

## 3. Tables S5 and S6 were hand-typed, and both had drifted

Same defect class as Tables S3/S4, one table along. Both are computed from the matrices now.
Table S6 was wrong by a **clean factor of two** on the chloride/ethylene row — it printed
`392 → 789` against a model giving `196 → 394`, left over from an earlier migration convention.

The checkers for both read `make_si.js` — the **generator source**, not the shipped document —
so once a table became computed they could never pass. Both now assert against the built
`.docx`, bound to the row label beside the numbers, and both are negative-controlled.

## 4. Fifteen manuscript numbers, five of them uncovered by any gate

`data/check_ms_derived.py` asserted the unstirred and RCE counts but not the stirred one; it
asserted the Fig. 4 *caption's* catalyst pair (correct) but not the *body* sentence quoting the
same class; and it never looked at the TRL-E count range or at the Section 8 δ-ladder sentence,
which prints all four upper medians. Trap 9 — a gate covering part of a claim reports PASS for
the whole thing. All five are asserted now.

    architecture medians   6.1  17.1  19.4  48.6  108  122 mA cm-2
    clearing 25 mA cm-2     12    18    20    31    36   36  of 50
    clearing 50 mA cm-2      9    15    15    24    32   33  of 50

Also fixed: `check_ms_derived`'s negative control perturbed `"11/50 to 36/50"`, a phrase the
manuscript stopped containing at v39, so its wrong-number branch was perturbing nothing. It now
asserts the phrase is present before perturbing it.

## 5. State after v40

    v40: 14 tracked text edits, 5 figures re-embedded (Fig 1 unchanged, as the control)
    verify_v40.py                 31 checks, 0 FAIL
      --negative-control          fires exactly its 9
    G-MSKAPPA G-MSDERIVED G-SIDERIVED G-ECBAND G-MSCITE  PASS
    G-CODECONST G-SPECIES G-DSUB G-SIBOUNDS G-LIVE G-ASSUME G-CITE  PASS
    audit_numeric  0 FAIL (4 known checker-side WARNs)
    khl_stratification --check-si  5/5

The three MS-reading gates now resolve the highest-numbered draft automatically and print which
one they gated, so they cannot go on checking a superseded document.

## 6. One mistake worth recording

Renaming the Kolbe row, I ran the replacement across `figs/*` and `data/*` and hit **27
historical `.bak_*` files and a rendered SVG** as well as the two live generators. Backups are
the only history this repository has. All 27 were reversed exactly (each had zero occurrences of
the new name beforehand, so the reverse was unambiguous) and the SVG was restored.
**Scope a bulk rename to the files you named, never to a glob.**

---

## 7. Systematic sweep for the same three defect shapes (2026-08-25, after v40)

Today's defects were all found one at a time by accident, so I swept for the rest of each shape.

### Shape 1 — a checker reading the GENERATOR instead of the shipped artifact

Three more found and fixed:

| file | was | now |
|---|---|---|
| `data/check_ecprime_band.py` | grepped `make_si.js` for the EC′ bracket sentence | reads the built `.docx` |
| `figs/analysis_solvent_property_sensitivity.py` | parsed Table S5 rows out of `make_si.js` — which stopped containing them the moment the table became computed | builds the expected row from the model and tests membership in the `.docx` |
| `data/audit_numeric.py` | kept a now-dead `si = open(make_si.js)` | removed |

`data/docx_text.py`'s self-test was pinned to v39; it resolves the highest-numbered draft now.

**A parsing note worth keeping:** do not *parse* numbers back out of a rendered table. The cells
concatenate — `6.1` then `12/50` renders as `6.112/50`, which a regex happily splits as
`6.11` + `2/50`, and it reported per-architecture counts of `2/8/0/1/6/6`. Build the expected
string from the model and test membership instead.

### Shape 2 — pinned expectations that should be derived

Three left, all now derived from the shipped SI: `audit_numeric`'s `(28,31)` and `(10,11)`
partition counts, and the same `(28,31)` in the solvent sweep.

### Shape 3 — consumers assuming an old schema or a pre-relabel name

Swept every consumer of `tier0_ec_matrix.csv` and every reaction-like string literal in
`data/`, `figs/` and `make_si.js`. Clean: `make_figs.py`'s `.cls` is on `reactions_50.csv`
(which has that column), `make_figFG.py` matches by substring, and the `propylene` reference in
`check_reaction_names.py` is in a docstring recording the rename. G-NAMES passes.

## 8. FIVE GATES EXISTED AND NOTHING RAN THEM

`run_gates.sh` was missing **G-MSKAPPA, G-LIVE, G-ASSUME, G-SOLV and G-STRAT**. That is not
bookkeeping: **G-SOLV was carrying a real finding the whole time.**

It sweeps viscosity ±25–50% on the rows whose solvent properties are not page-anchored, and the
SI's §S5.5 sentence quoting its result was wrong three ways at once:

| the SI said | the model says |
|---|---|
| eleven of the fifty rows | **thirteen** (2 HFIP + 11 mixed-solvent) |
| shifts each count "by at most **two** entries of fifty" | **three** |
| baseline `11–17–21–31–36–36` | `12–18–20–31–36–36` |

The sentence is now emitted from `results/solvent_property_sensitivity.json`, and the gate's own
tolerance — a hardcoded `if worst > 2`, i.e. the gate carrying its own opinion instead of checking
the document — is bound to the bound the SI publishes. **What does not move is the conclusion:**
the architecture ordering unstirred < stirred < flow < thin-gap holds at every point of the sweep.

All five are in `run_gates.sh` now, with a `PYFIG` interpreter for the figure-side gates.

## 9. Suite state

    ./run_gates.sh                24 passed, 1 REVIEW NEEDED, 3 skipped (slow sweeps)
    verify_v40.py                 31 checks, 0 FAIL; control fires exactly its 9
    julia/run_audit.jl            16/16, exit 0
    process-language sweep        SI 2 hits, MS 0 -- both SI hits legitimate

The one non-PASS is **G-COND: REVIEW NEEDED**, a deliberate third state and a standing author
review item, not a regression: it classifies each of the 50 rows by how well its conditions
anchor in its own exemplar PDF (15 ANCHORED, 4 HAND-VERIFIED, 17 SI-ONLY, 13 MIXED-EXPERIMENT,
1 unusable). It reads the PDFs, not `conc_provenance`, so the Table S2 rewrites could not have
moved it.

---

## 10. G-COND: 13 MIXED-EXPERIMENT rows were 12 matcher artifacts and 1 OCR failure

`anchor()` returned the position of the **numerically closest** occurrence of each target
concentration, independently per target. That is the wrong question. A paper states its
conditions once in a footnote and then repeats the same molarities in the optimisation
discussion, the scheme and the SI; picking each target's closest match on its own scatters the
three across the document, and the co-location test then reports MIXED-EXPERIMENT for a row
whose numbers all sit in one sentence.

Four were checked by hand first and every one was this artifact — the Ni amination's carrier,
substrate and electrolyte are all inside `10 mol % Ni(bpy)Br2, nBu4N·Br (0.2 M), DBU (2.0 equiv),
DMA (0.025–0.05 M)`.

The right question is whether a passage exists containing all of them, so `pick_colocated()` takes
the **minimum-span window holding one occurrence of each** (smallest range covering k lists).

    before   15 ANCHORED   4 HAND-VERIFIED   17 SI-ONLY   13 MIXED-EXPERIMENT   1 NO-TEXT
    after    27 ANCHORED   5 HAND-VERIFIED   17 SI-ONLY    0 MIXED-EXPERIMENT   1 NO-TEXT

The one survivor was row 19 (Courtois Ni aryl–aryl homocoupling), and it is an extraction
failure, not a mixed experiment: its footnote carries all three numbers, but the extractor
renders `4.10⁻² mol·L⁻¹` as `4.10 -2 mol.Ll`, so the electrolyte molarity is unreadable *at that
position* and its only parseable match is the general procedure 5 kB away. Recorded in
HAND_VERIFIED with the quote. `HAND_VERIFIED` now covers both failure modes — a number that
cannot be read at all, and numbers that can be read but not co-located — which it did not before.

**The control was reporting BAD on a working gate.** It required `nA <= 3` after the ×1.7
substrate perturbation, a pinned magic number; once the matcher could see every occurrence, a
perturbed value found a coincidental match slightly more often and the count went 3 → 5. It now
measures the collapse against the baseline the gate itself recorded: **ANCHORED 27 → 5, 19% of
baseline, GOOD**.

### What still needs an author: 10 rows

`G-COND: REVIEW NEEDED` is the correct verdict and should not be softened — the gate's own
docstring says an SI-ONLY row "is NOT state A on the evidence in this repo". Of the 17,
**7 name an SI or Supporting-Information source in their provenance and 10 do not**:

    row  4  Mn-catalyzed alkene diazidation          carrier, substrate
    row  7  Amidyl-radical C-H amination             carrier, substrate, electrolyte
    row 11  Kolbe homocoupling of 10-undecenoate     carrier, substrate, electrolyte
    row 12  Ni-XEC C(sp2)-C(sp3)                     carrier, electrolyte
    row 14  BDD phenol-arene cross-coupling          carrier, substrate, electrolyte
    row 20  Anodic dehydrogenative 2-naphthol        electrolyte
    row 31  Cl-mediated ethylene epoxidation         substrate
    row 37  Radical-cation Diels-Alder               carrier, substrate, electrolyte
    row 45  Br- oxidation / electrophilic bromination substrate
    row 47  Aryl thiocyanation (NH4SCN)              carrier, substrate, electrolyte

Two of these are known NOT to be gaps, which is why the category needs a human rather than a
rule: row 31's substrate is ethene solubility from IUPAC SDS vol. 57 — a *different cited
source*, so its absence from the exemplar PDF is expected and correct; row 45's substrate is
4 mmol / 33 mL where 33 mL is a **sum** (10:10:10:3), so no stated volume exists for the
quotient matcher to find. The remaining eight are the ones worth opening the SIs for.

---

## 11. 2026-08-26 — I corrupted artifacts by editing a running shell script

**Cause.** `run_gates.sh --all` was executing when I edited it (twice: the concurrency guard, then
per-gate logging). **Bash reads a script incrementally from a byte offset**, so inserting lines
moved everything under the running interpreter and it resumed at the wrong position and
re-invoked itself: PID 20231 (7 h) spawned PID 79218 (4 min). Two `--all` sweeps then interleaved
writes to the same solver artifacts.

**Damage, and how each was established.**

| artifact | state | evidence |
|---|---|---|
| `data/carrier_charge.csv` | **perturbed** — Ni aryl amination `z = 1`, should be `0` | three independent backups all read 0 |
| `julia/all50_np_matrix.csv` | partial, 46 of 300 rows | pandas tokenizer error, then short read |
| `julia/mediated_ec_matrix.csv` | partial, 30 of 48 rows | short read |
| `julia/run_mediated.jl` | **clean** — the k-sweep rewrites this file in place | all 8 MedSpec k values identical to two backups |
| `julia/tier0_ec_matrix.csv` | **clean** — sweeps never write it | 50 rows, parsed |

The perturbed charge is the dangerous one: migration acts only on a charged carrier, so a wrong
`z` shifts a ceiling by up to 2× and fails nothing.

**Recovery, and the proof it worked.** `carrier_charge.csv` restored (exactly one cell changed,
header comments intact), then `run_all50_np.jl` → `run_mediated.jl` → `build_merged_matrix.py`
re-run with nothing else active. The regenerated published matrix is **bit-identical** to the
intact pre-corruption one — `max |published − regenerated| = 0.000e+00` across all 300 cells,
which simultaneously proves the charge restore was right and that nothing else was left perturbed.

**Three real defects in the sweeps that this exposed, all fixed:**

1. **No lock.** A second instance overwrote the first's backup; the first's `finally` then deleted
   it, leaving the second nothing to restore. Each sweep now refuses to start if a backup marker
   exists.
2. **The restore was not crash-safe.** `shutil.copy(backup, live)` with no existence check raised
   `FileNotFoundError` *inside the `finally`*, burying the original error. It now names the file
   that may still be perturbed instead of throwing.
3. **A short base solve failed obscurely** — `KeyError` on a random (reaction, reactor) 40 minutes
   in. The base is now required to hold all 300 cells up front.

**Rule: never edit a shell script while it is executing.**

## 12. Trap 8 again, on Figure 1 — and it cannot be re-rendered on this machine

Running `Figure1/fig_composite.py` under `/opt/anaconda3/bin/python3.12` **purely to read its
printed panel-c numbers** silently overwrote `figure1_composite.png` with a different raster.
`verify_v40` G1 caught it (Figure 1 had been the byte-identical control). The correct bytes were
recovered from the v40 `.docx` itself.

Neither interpreter on this machine is the pinned one:

    pinned    python 3.13, matplotlib 3.11.1, numpy 2.5.1, pandas 3.0.5, pyarrow 25.0.0, rdkit 2026.3.5
    available python 3.12 (no rdkit, matplotlib 3.10.8, numpy 1.26.4, pandas 2.2.2, pyarrow 19.0.0)
              python 3.11 (rdkit 2025.03.6)

So **the authoritative Figure 1 raster is the one embedded in v40**, now also on disk.
`fig_composite.py` now checks the pins and **refuses to write** off-pin (override with
`FIG1_ALLOW_OFF_PIN=1`), while still printing every number — the numbers are environment-
independent and `verify_v40` G6 recomputes them from the parquets.
