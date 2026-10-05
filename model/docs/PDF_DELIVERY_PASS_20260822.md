# What the "Model Papers for Params" delivery closed — 2026-08-22

Five PDFs were delivered. This records what each one actually settled, what it did **not**, and
two findings that had nothing to do with the PDFs but surfaced while working through them.

---

## 1. Krumgalz 1983 — the one that paid

> *J. Chem. Soc. Faraday Trans. 1* **1983**, 79, 571–587. `papers for model/f19837900571.pdf`

Pulled for limiting ionic conductances. It supplied those, and also the thing that had defeated
every search for weeks:

| what | where | value | effect |
|---|---|---|---|
| **η(HFIP)** | Table 3, p. 578 | 0.01619 P = **1.619 mPa s** | state C → **A**; −1.9 % on the carried 1.650, which had *no source at all* |
| λ°(SCN⁻, MeCN) | Table 4, p. 579 | 113.3 | → D = 3.017e-9, reproduces carried 2.9e-9 to **+4.0 %**; row → derived |
| λ°(Br⁻, MeOH) | Table 4, p. 579 | 56.53 | → D = 1.505e-9, reproduces carried 1.5e-9 to **+0.4 %**; row → derived |
| λ°(Et₄N⁺/Bu₄N⁺, MeCN) | Table 2 p. 577 ÷ Table 3 p. 578 | 84.9 / 61.6 | independent corroboration of the Et₄NBF₄ transfer |

HFIP's viscosity had never been found because every search returned hexafluoro**propane**
(R236fa), a different compound. It was item **7** on the pull list; the paper was pulled for item **2**.

**What it could not close.** λ°(ClO₄⁻, MeCN) is a dash in Table 4. The acetonitrile *cation* row
carries seven tokens across nine columns with no right-hand anchor, so H⁺ and Li⁺ cannot be
separated by position — and resolving that by recognising which value "looks right" is
recognition, not retrieval. `Li+ (generic organic)` and `ClO4- (MeCN, aq-like)` stay assumptions.

## 2. Dorn 2024 (article body) — retrieved, and the fit was *rejected*

Table 3, p. 1499 does carry the ACN/(C₂H₅)₄NBF₄ Casteel–Amis fit the pull list wanted
(m_max 4.00409, κ_max 60.97, a 0.84952, b −0.02650). Evaluated at 0.077 M it returns
**4.03 mS cm⁻¹**, i.e. Λ/Λ° = **0.269**, against **0.615** for Bu₄NBF₄ at the same molality in the
same solvent.

Two homologous R₄N⁺BF₄⁻ salts cannot differ that way. The fit is anchored at m_max = 4.0 mol kg⁻¹
and does not reach this concentration, so **it is not used**, and the row does not claim it.

This is worth stating plainly: the pull succeeded and the number was still not usable. Retrieving
a source is necessary, not sufficient — the value has to be applicable at the right concentration.

## 3. The correction this pass owes

`0.077 M Et4NBF4/MeCN` is now **derived at 9.26 mS cm⁻¹** by same-family transfer at equal Λ/Λ°
(same solvent, same anion, same concentration, homologous cation), replacing an 8.1 lower bound.

The limiting conductances came from **Kalugin, Lukinova & Novikov, *Kharkiv Univ. Bull. Chem. Ser.*
2019, 33(56), 23–33, Table 3, p. 28** — Et₄N⁺ 86.34, BF₄⁻ 109.20, Bu₄N⁺ 61.90.

**That source was already cited in `build_param_tables.py`, on the `Br- (MeCN)` row, the entire
time.** Pull-list items 1 *and* 2 both described λ°(Bu₄N⁺, MeCN) as "the single missing number".
It was never missing. The check that should have caught it is one line:

> 61.90 + 109.20 = **171.10**, reproducing to **0.00 %** the Λ°(Bu₄NBF₄/MeCN) = 171.1 that the
> registry independently carries as *measured*.

Krumgalz gives 9.20 by a fully independent tabulation — a 0.6 % spread. **Neither pull was needed.**
Rule added to `CLAUDE.md`: grep the registry for a quantity before putting it on the pull list.

## 4. The HFIP citation was wrong on two counts

The row named *Colomer, Chinchilla, **Waldvogel** et al.* The paper (*Nat. Rev. Chem.* 2017, 1,
0088) is by **Colomer, Chamberlain, Haughey & Donohoe**. It was also claimed to carry μ and ρ; its
Table 1 p. 2 carries boiling point and permittivity only. Both withdrawn. That table did correct
HFIP's ε from a recalled **16.7 → 15.7**; ε is verified to have zero consumers.

ρ(HFIP) = 1.596 g cm⁻³ **remains unsourced** and is now the whole of pull-list item 7.

---

## 5. A finding that had nothing to do with the PDFs: the headline matrix was stale

Re-solving after the HFIP change exposed a trap the repo had not recorded.

- `run_tier0.jl` writes **`tier0_matrix.csv`**.
- Every figure generator, both sensitivity gates and the SI read **`tier0_ec_matrix.csv`** — a
  *different* file, the EC′-coupled headline matrix, written by **`data/build_merged_matrix.py`**
  from `tier0_matrix.csv` + `mediated_ec_matrix.csv`.

Running `run_tier0.jl` therefore looks like it regenerated the matrix and does not. The two files
differed by 55–96 % on the ten mediated rows, and a diff of the headline matrix against its own
backup showed *zero* change — because it had never been rewritten.

**The correct chain after any property change:**

```
data/build_reactions50.py          # -> reactions_50.csv, reactions_table.jl
julia/run_tier0.jl                 # -> tier0_matrix.csv          (substrate/catalyst rows)
julia/run_mediated.jl              # -> mediated_ec_matrix.csv    (~12 min, 8 mediated rows)
data/build_merged_matrix.py        # -> tier0_ec_matrix.csv       <- THE ONE EVERYTHING READS
```

Once merged properly, the HFIP change moved the largest single cell of 300 by **1.95 %** and
**no published count moved**: per-architecture ≥25 stayed 11/17/21/31/36/36 of 50, substrate-carried
clearing stayed 28/31, catalyst never-clearing stayed 10/11.

But two **manuscript** figures did change, and `verify_v21.py` G1 failed on exactly those two —
which is that gate working as designed, since it compares embedded bytes against a *fresh render*
rather than against the generator. Fixed by **v22** (artwork only, `document.xml` byte-identical).

## 6. Registry effect

| | before | after |
|---|---|---|
| measured | 64 | **65** |
| derived | 88 | **91** |
| assumption | 119 | **115** |

Rows carrying an explicit "PULL NEEDED" clause: 60 → **57**.

And the bare assumption count is no longer the number to read: see `ASSUMPTION_LEDGER.md`, gated
by **G-ASSUME**, which sorts all 115 by what backs each one and finds **0** rows failing the
standard's own test of stating a perturbation and its effect.
