# Temperature dependence of κ — omitted systematic, now bounded

**Status:** analysis complete, artifact written, **SI text inserted — §S6.3 landed this pass**
(`make_si.js`, "S6.3 Temperature dependence of the conductivity: why the ceilings are lower bounds",
four paragraphs; §S6.1 and §S6.2 both now close on a cross-reference to it).
Artifact: `results/figK_kappaT_sensitivity.json`. Script: `figs/analysis_kappaT_sensitivity.py`.

**2026-08-02 desync repair.** The script used to retype its own `SOLVENTS` and `REACTORS` tables
instead of importing `figs/thermal_model.py`. When the κ sourcing pass promoted MeCN 1.80 → 1.89 S/m
and aq. NaOH 18.00 → 17.80 S/m in the registry and in `thermal_model.py`, this script kept the old
numbers and regenerated the JSON *self-consistently but wrong*, while §S6.3 pointed the reader at
that JSON by name. Both tables are now imported, exactly as `make_figK.py` does, so the two cannot
separate again. The κ(T) overlay itself is unchanged and stays local to this script; the bracket is
evaluated by feeding κ(T) into the **shared** `i_boil()`, which was verified to reproduce the old
artifact bit-for-bit (max relative difference 0.000e+00 over all 20 pairs) when driven with the old
κ values — so every number below moved for exactly one reason, the κ promotion, and none moved
because the solver changed. All numbers here and in the SI are the post-promotion values.

## The omission

The thermal model evaluates κ at 25 °C while predicting cells that run at 60–153 °C. Re-verified by
direct search 2026-08-02: **no temperature dependence of κ or μ exists anywhere** in `julia/*.jl`,
`figs/make_figK.py` or `figs/thermal_model.py` — the single "Walden" hit in the whole Julia tree is
`run_mediated.jl:99`, diffusivity scaling *between solvents* (D(SCN⁻) from λ°(MeCN)), not
temperature. (An earlier version of this note also named `run_scn.jl`; no such file exists in the
repo, and the substance of the claim is unaffected.) Conductivity rises with temperature, so fixing
κ at 25 °C **overstates ohmic heat and understates every boil-off ceiling**. The 25 °C result is a
conservative lower bound, not an estimate — and that was never disclosed.

## Why a bracket, not a correction

Two effects compete as temperature rises:

1. **viscosity falls** → ions move faster → κ rises (Walden: κ ∝ 1/η)
2. **dielectric constant falls** → ion pairing *increases* → κ rises *less* than (1) predicts

Arrhenius/Walden captures only (1), so it is an **upper** bound. The literature is explicit that a
single Arrhenius law describes organic liquid electrolytes poorly for exactly this reason — the
temperature dependence of the dielectric constant sitting in the prefactor — and that VFT-type
forms are needed. Absent measured κ(T) for these specific electrolytes, the defensible claim is a
bracket:

| bound | basis |
|---|---|
| lower | κ fixed at 25 °C (current model, conservative) |
| upper | Arrhenius, Ea = 15 kJ/mol (neglects the pairing penalty) |

**Coefficient anchor.** Water's viscosity is well tabulated: η(25 °C)/η(100 °C) = 0.890/0.282 =
**3.16**, so Walden predicts κ ×3.16 at 100 °C. Arrhenius with Ea = 15 kJ/mol gives **×3.37** at the
same point — **6.9 % apart**. That agreement is what licenses Ea = 15 kJ/mol as the upper-bound
coefficient; it is not a fitted value. The anchor depends only on temperature, so the κ promotion
did not touch it.

## Magnitude

κ(T_boil)/κ(25 °C) is a function of T_boil alone and is therefore **unchanged** by the κ promotion:
THF ×2.08, MeCN ×2.64, aq. NaOH ×3.37, **DMF ×6.16** (its 153 °C boiling point is the furthest
extrapolation, and therefore the least trustworthy).

Ceilings, unstirred 100 mL beaker at 2 cm, 25 °C → κ(T_b) upper bound (mA cm⁻²):

| solvent | κ₂₅ (S/m) | state | 25 °C | κ(T) | factor | was (pre-promotion) |
|---|---|---|---|---|---|---|
| THF (3.0 M LiBr) | 0.30 | assumption | 29.5 → **29** | 42.3 → **42** | 1.43× | unchanged |
| MeCN (0.25 M Bu₄NBF₄) | 1.89 | derived | 85.9 → **86** | 136.9 → **137** | 1.59× | 84 → 134 |
| DMF (0.2 M NaI) | 0.80 | assumption | 84.9 → **85** | 206.3 → **206** | 2.43× | unchanged |
| aq. NaOH (1 M) | 17.80 | derived | 285.0 → **285** | 481.7 → **482** | 1.69× | 286 → 484 |

These are the four numbers §S6.3 prints as "29 to 42, 86 to 137, 85 to 206 and 285 to 482", and they
now agree with the artifact. Across all 20 (reactor, solvent) pairs the bracket factor spans
**1.01×–2.43×** (min: aq. NaOH in the zero-gap stack, 1.0095; max: DMF in the stirred beaker,
2.4319), which §S6.3 quotes as "a factor of 1.0 to 2.4".

## What survives

**Re-verified against the regenerated artifact, not carried over: exactly 1 flip of 20.**
19 of 20 pass/fail verdicts are unchanged between the bounds. The single flip is still MeCN in the
250 µm microfluidic, now **433 → 557 mA cm⁻²** against a 500 mA cm⁻² design current (margin 0.87× →
1.11×; pre-promotion it was 426 → 551, margin 0.85× → 1.10×). The flip count, the identity of the
flipping pair and the direction of the flip are all unchanged by the promotion — **no conclusion
moved.**

So the qualitative conclusions — THF fails passively everywhere, the stack collapses on σ, thin
gaps require active cooling — are robust to the omission. Absolute ceilings are not.

The rows nearest a *second* flip, ranked by how close either bound sits to a margin of 1.00:

| pair | margin at 25 °C | margin at κ(T) | why it does not flip |
|---|---|---|---|
| DMF, 250 µm microfluidic | 1.03× | 1.94× | passes at **both** ends — but the 1.03× is inside the uncertainty of its own κ assumption, which is why §S6.1 refuses to draw a conclusion from it |
| THF, stirred beaker | 0.62× | 0.89× | fails at **both** ends; 12 % from flipping at the upper bound |
| THF, unstirred beaker | 0.59× | 0.85× | fails at both ends |

Every one of the remaining 16 pairs sits at least **1.27×** away from a margin of 1.00 at *both*
bounds (the closest of them, THF in the 5 mm flow cell, misses at 0.55× and 0.79×), so no other
verdict is near the line.

## SI changes — status

1. ~~Add a §S6 sensitivity paragraph stating the omission, the bracket, the water anchor, and the
   robustness result.~~ **DONE.** §S6.3, four paragraphs.
2. ~~Re-word any absolute ceiling as a lower bound, or quote the bracket.~~ **DONE.** §S6.1 carries
   "Every ceiling quoted in this section is a lower bound … §S6.3 brackets the effect"; §S6.2 closes
   with the reciprocal statement for the cooling duties (upper bounds).
3. ~~Flag the MeCN/microfluidic verdict explicitly as bound-dependent.~~ **DONE.** Flagged in §S6.1
   ("reported here as bound-dependent on κ(T) alone, not as a finding"), in §S6.2 ("MeCN on the
   wrong side of a bound-dependent verdict (§S6.3)") and in §S6.3 itself.
4. ~~Register `Ea = 15 kJ/mol` as an **assumption** with the water anchor as its justification and
   this bracket as its sensitivity, in `data/parameters_provenance.csv`.~~ **DONE** (2026-08-02,
   later the same day). Category 9, `Ea (kappa(T) Arrhenius upper bound, S6.3) = 15 kJ mol-1`,
   class `assumption`. The `citation` field explicitly disclaims a page-anchored source for Ea
   itself and names the CRC water viscosities as the *anchor*; the `locator` carries those two
   viscosities. The `sensitivity` states that the bracket's lower bound is κ fixed at 25 °C (so the
   row can only raise a ceiling, never shrink one), that 19 of 20 pass/fail verdicts are unchanged
   between the bounds, that the single flip is MeCN in the 250 µm microfluidic, and that DMF's
   ×6.16 is the weakest point of the upper bound. Registry census went 270 → 271.
5. ~~DMF's ×6.16 extrapolation to 153 °C should carry its own caveat.~~ **DONE.** §S6.3 paragraph 4
   treats it separately: 128 K extrapolation against a 75 K anchor, largest single change in the
   table (85 → 206 beaker, 516 → 969 microfluidic), and an explicit statement that no conclusion
   rests on it.
