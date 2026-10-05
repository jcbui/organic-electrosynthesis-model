# Rate constants for the eleven molecular-catalyst rows — retrieval dossier (2026-09-11)

**Status: ADOPTED 2026-09-11 (author decision). The retrieval record follows; what was changed in the tree
is in the closing section.**

## Why this exists

The published matrix solves the eleven catalyst-carried rows at k = 0: the activated catalyst is
credited with no turnover inside the diffusion film, so every published catalyst ceiling is the
carrier's own transport bound nF D C_cat/δ (a rigorous floor, since the EC′ source term only adds
current), and the class is "direct electrolysis of a dilute species" — its 24-fold
unstirred-to-rotating-cylinder gain is the 1/δ ratio and nothing else. The author's objection
(2026-09-11): "what's the point of intensification if nothing is happening [inside] the boundary
layer, there's no difference then with the direct." The finite-k sweep `julia/catalyst_ec_sweep.csv`
(G-CATK, k ∈ {0, 1, 10, 10², 10³, 10⁴} M⁻¹ s⁻¹, 77 cells each) already exists; what was missing was
a *sourced* k. The four-state standard forbids a plausible magnitude; it allows a measured value
with a declared transfer and a sensitivity. This file records what the literature actually prints.

Papers pulled by the author on 2026-09-11 into `papers for model/catalyst mediation/` (Box and the
local mirror, 19 files, md5-checked). Text extractions and rendered figure pages are in
`~/v87_session_scratch_20260910/kinetics_pull/` (scratch, not part of the tree).

## The model's k, and which elementary step it is per row

The EC′ solver's k multiplies c(activated carrier) × c(substrate). It is therefore the bimolecular
rate constant of the FIRST substrate-consuming step of the catalytic cycle, in the electrolysis
medium. Which step that is, row by row:

| row | carrier, substrate (model conc.) | substrate-consuming step |
|---|---|---|
| Ni-XEC C(sp²)–C(sp³) (Kelly/Stahl/Schreier OPRD 2026) | Ni(dtbbpy), 5-bromoindole-type ArBr 0.30 M, DMA | Ni(I)(bpy)Br + ArBr oxidative addition |
| Ni-catalyzed aryl amination (Kawamata/Baran JACS 2019) | Ni(Mebpy), ArBr 0.05 M, DMA | same |
| Electrochemical amination of ArX with NH₃ (Liu/Qiu Angew 2025) | Ni(bpy), 4-bromotoluene 0.104 M, DMSO/THF 85 °C | same |
| Cathodic Ni aryl–aryl homocoupling (Courtois/Périchon Tetrahedron 1997) | Ni(bpy), PhBr 0.30 M, EtOH/MeOH | same (Ni(0)(bpy) or Ni(I)) |
| Cathodic aryl-halide 5-exo cyclization (Ozaki/Ohmori 1994) | Ni(tet a) macrocycle, ArX 0.05 M, DMF | Ni(I) macrocycle + ArX — no source found |
| Co–H Markovnikov hydroamination (Gnaim/Baran Nature 2022, conditions A) | CoBr₂/4,4′-MeO-bpy, alkene 0.08 M, THF/HFIP | Co–H + alkene (MHAT) |
| Co–H alkene isomerization (Gnaim/Baran, conditions B) | Co(salen)-1, alkene 0.08 M, acetone | Co–H + alkene (MHAT) |
| Co(salen) aza-Wacker cyclization (Cai/H.-C. Xu Nat Commun 2021) | Co(salen), carbamate 0.033 M, MeCN/MeOH reflux | Co(III) + (deprotonated) substrate |
| Mn-catalyzed diazidation (Fu/Lin Science 2017) | Mn(N₃), alkene 0.051 M, MeCN/HOAc | azidyl radical + alkene, not a Mn + substrate step — no source |
| Cu-catalyzed benzylic cyanation (Cai/Xu Nat Catal 2022, PEC) | Cu(acac)₂/BOX, alkylarene 0.038 M | substrate consumed by photoexcited AQDS (HAT), not by Cu — no source |
| Rh-catalyzed C–H alkenylation (Qiu/Ackermann Angew 2018) | [Cp*RhCl₂]₂, acrylate 0.125 M, tAmOH/H₂O 100 °C | Rh(III) CMD C–H activation — no source |

## What the retrieved papers print

### A. Ni(I)-bipyridine + aryl bromide (rows 1–4)

**Ting, S. I.; Williams, W. L.; Doyle, A. G. J. Am. Chem. Soc. 2022, 144, 5575–5582
(DOI 10.1021/jacs.2c00462; `ja2c00462.pdf`, SI `ja2c00462_si_001.pdf`).** Well-defined
[(CO₂Et-bpy)NiCl]₄ (1; CO₂Et-bpy = diethyl 2,2′-bipyridine-4,4′-dicarboxylate), THF, 26 °C,
pseudo-first-order UV-vis at 800 nm, first order in 1 and in ArBr. p. 5578: "The slope revealed a
second-order rate constant of 7.1 ± 0.3 M⁻¹ s⁻¹" (PhBr). p. 5579, Figure 6 table, k (M⁻¹ s⁻¹):
4-COMe 56 ± 3; 4-CF₃ 40 ± 2; 4-Cl 16.3 ± 0.5; 4-Ph 13.1 ± 0.5; 4-H 7.1 ± 0.3; 4-Me 5.0 ± 0.3;
4-OMe 3.4 ± 0.3; 2-Me 1.51 ± 0.09; 2,6-Me₂ 0.070 ± 0.007. Hammett slope 1.07 (ρ = +1.1, R² 0.95).
SI pp. S37–S39, Figures S36–S43: the k_obs-vs-[ArBr] fits (slopes 56, 40, 16.3, 13.1, 5.0, 3.4,
1.51, 0.070) — read from the rendered pages, values printed on the panels. Caveats the paper
itself states: 1 is 30 % monomer and ~40 % Ni(0) in solution, so "our measured rate constant with
1 similarly includes contributions from speciation equilibria" (ref. 55); the ligand is
electron-poor relative to bpy/Mebpy/dtbbpy.

**Till, N. A.; Oh, S.; MacMillan, D. W. C.; Bird, M. J. J. Am. Chem. Soc. 2021, 143, 9332–9337
(DOI 10.1021/jacs.1c04652; `ja1c04652.pdf`, SI `ja1c04652_si_001.pdf`).** Pulse radiolysis of
[(dtbbpy)NiBr] in DMF. p. 9334: "Examining the reactivity of 4-bromobenzotrifluoride with
[(dtbbpy)NiBr] revealed no significant lifetime change in the Ni(I) signal by pulse radiolysis,
providing an upper limit on the oxidative addition rate (kOA < 10⁴ M⁻¹ s⁻¹, Figures S7 and S8)";
SI: quenching attempted with 0–1000 mM ArBr. Aryl iodides: k_OA = 1.3 × 10⁴ – 2.4 × 10⁵ M⁻¹ s⁻¹
(abstract, p. 9332). SI p. S3–S5: CV of 20 mM [(dtbbpy)NiBr₂] in DMF with 0–128 mM
4-bromobenzotrifluoride shows the cathodic wave growing with [ArBr] — "rapid oxidative addition
between 4-bromobenzotrifluoride and electrolytically-generated low-valent Ni", Ni(0)/Ni(I)
ambiguous.

**Kawamata, Y. et al. J. Am. Chem. Soc. 2019, 141, 6392–6402 (DOI 10.1021/jacs.9b01886;
`jacs.9b01886.pdf`, SI `ja9b01886_si_001.pdf`)** — the aryl-amination exemplar's OWN voltammetry,
in its own medium. p. 6394, Figure 2B [C][D]: CV of 1 mM NiBr₂·3H₂O + 1 mM Mebpy in DMF (0.1 M
NBu₄Br), 100 mV s⁻¹; with 4-bromoanisole the anodic return peak of the Ni(II/I) couple disappears
("b: Disappearance of the peak with 4-bromoanisole. Rapid oxidative addition at Ni(I)") and the
reduction current rises. p. 6395: "A loss of electrochemical reversibility of the Ni(II/I) redox
couple upon addition of 4-bromoanisole suggests oxidative addition is [rapid] relative to the time
scale of the CV (100 mV/s), indicating this step is unlikely to be the rate-determining step."
**The ArBr concentration is stated two ways:** the figure legend reads "1:1:2 Ni/L/4-bromoanisole"
(2 mM) while SI p. S21 says "in the presence of 30 mM p-bromoanisole". SI pp. S18–S20 kinetics
(LC-MS, synthetic conditions): rate independent of amine, DBU and Ni loading, proportional to
current — the electrolysis is current-limited, so it bounds nothing about k.

**Reading of the voltammetric bound.** For an E step followed by an irreversible chemical step
the return wave is lost once k_obs ≳ Fν/RT (Nicholson & Shain 1964; Bard & Faulkner ch. 12, in
`papers for model/`). At 0.1 V s⁻¹, Fν/RT = 3.9 s⁻¹. With [ArBr] = 30 mM this is
k ≳ 1.3 × 10² M⁻¹ s⁻¹; with 2 mM, k ≳ 2 × 10³. Order-of-magnitude only; the switching potential
sets the exact threshold.

**Bracket for the Ni/ArBr step:** measured 3.4–56 M⁻¹ s⁻¹ (Ting; deactivated ligand, THF, para
series), in-medium voltammetry ≳ 10² (Kawamata; Mebpy, DMF), upper limit < 10⁴ (Till; dtbbpy,
DMF, activated ArBr). All three are consistent with one another.

**Not useful, checked:** Amatore & Jutand, Organometallics 1988, 7, 2203 is the dppe (phosphine)
system, not bpy. Budnikova et al., Russ. Chem. Bull. 2007, 56, 935 (`s11172-007-0142-9.pdf`) is
aryldichlorophosphine reduction, not aryl bromides. Doyle 2023 (`jacs.3c01726.pdf`) reports
RELATIVE rate constants for aryl IODIDES only.

### B. Co–H + alkene (rows 6–7)

**Boucher, D. G.; Pendergast, A. D.; Wu, X.; Nguyen, Z. A.; Jadhav, R. G.; Lin, S.; White, H. S.;
Minteer, S. D. J. Am. Chem. Soc. 2023, 145, 17665–17677 (DOI 10.1021/jacs.3c03815;
`ja3c03815.pdf`, SI `ja3c03815_si_001.pdf`).** Co(salen), 0.1 M TBAPF₆ in DMF, glassy carbon,
room temperature; oxidative MHAT (hydride from phenylsilane). p. 17668: hydride formation
k₁ = 11 M⁻¹ s⁻¹ from the EC′ plateau-current equation and 14 M⁻¹ s⁻¹ from the finite-element fit
(SI Table S2: k₁ = 36 (OMe), 13.8 (tBu), 1.0 (CF₃), 0.1 (CN), 0.96 (NO₂) M⁻¹ s⁻¹ by ligand
substituent). p. 17674: with 4-tert-butylstyrene added, "kMHAT equal to 7 × 10² M⁻¹ s⁻¹ was
found to give the observed current decrease and E1/2 shift" — the Co(III)–H + alkene step,
treated as irreversible. The catalytic-current decrease vs styrene is first order in styrene and
"independent of the identity of the styrene" (NMe₂, OMe, CF₃), hydride formation being
rate-determining.

**Wilson, C. V.; Holland, P. L. J. Am. Chem. Soc. 2024, 146, 2685–2700 (DOI
10.1021/jacs.3c12329).** Same conclusion by stoichiometric/kinetic work: the Co(III)–H forms in
the turnover-limiting step; rate law k_obs[Co]¹[silane]¹ with k_obs = 6.0 × 10⁻¹ M⁻¹ s⁻¹ at
−50 °C in acetone (p. 2693). Hydride formation, not the model's step.

**Gnaim, S. et al. Nature 2022, 605, 687–695 (DOI 10.1038/s41586-022-04595-3; SI
`41586_2022_4595_MOESM1_ESM.pdf`)** — the two Co–H exemplars' own kinetics. SI p. 112, Figure S19
table (Ph substrate, CoBr₂/4,4′-MeO-bpy, Et₃NHBF₄, MeCN): at 2.5 mA order 0 in Co, 0 in substrate,
1 in current; at 7.5–10 mA order 1 in Co, 0 in substrate, 0 in current. Main text p. 693:
"For conditions B, the reaction exhibits first-order kinetics in the [substrate] ... whereas, for
conditions A, the reaction is zero order in the [substrate]." Zero order in substrate = the
Co–H + alkene step is saturated, i.e. fast relative to hydride formation, consistent with Boucher.
No rate constant is printed.

**Transfer caveats:** Boucher's value is for STYRENES in DMF with an oxidatively generated hydride;
the Gnaim rows use unactivated alkenes in THF/acetone with a cathodically generated hydride
(protonation by HFIP/Et₃NHBF₄). The hydride-formation step differs entirely; the MHAT step is the
same elementary reaction with a different alkene class. No measured value for unactivated alkenes
was found.

### C. Co(salen) aza-Wacker (row 8) — its own voltammetry brackets it from ABOVE

**Cai, C.-Y.; Wu, Z.-J.; Liu, J.-Y. et al. Nat. Commun. 2021, 12, 3745 (DOI
10.1038/s41467-021-24125-5; `s41467-021-24125-5.pdf`, SI `41467_2021_24125_MOESM1_ESM.pdf`).**
SI p. 5, Supplementary Figure 2 (Et₄NPF₆ 0.1 M, MeCN/MeOH 5:1, glassy carbon, 100 mV s⁻¹):
[Co]-1 1.5 mM alone is a reversible Co(II)/Co(III) couple at ≈ +0.3 V vs SCE; with substrate 1
(10 mM) and NaOMe (1.5 mM) the return wave is largely lost but the forward current does not grow
(main text p. 6: "no catalytic current was observed"); with Na₂CO₃, the base the reaction actually
uses, the voltammogram "remained largely unchanged". Read with the same criterion as above: with
Na₂CO₃ at room temperature k·[1] ≲ 0.1 × Fν/RT, i.e. k ≲ 4 × 10¹ M⁻¹ s⁻¹; with NaOMe
4 × 10² ≲ k ≲ 4 × 10³ (return wave lost, no catalytic enhancement). The synthesis runs at reflux
(≈ 70 °C) — no temperature correction is available, and none is assumed. **This is the median row
of the class, and it is slow.**

### D. No source found (rows 5, 9, 10, 11)

Ozaki's Ni(tet a) macrocycle, the Mn/azidyl radical step, the Cu/AQDS photochemical step and the
Rh(III) CMD step: nothing retrieved prints a bimolecular constant for the step the model needs.
Fu/Lin's SI voltammetry (`aan6206_fu_sm.pdf`) concerns azide oxidation potentials only.

### E. Routes tried and closed

* **Operating-current lower bound** (i_campaign > i(k) at the campaign's film ⇒ k above that
  value): every one of the eleven campaigns runs on a THREE-DIMENSIONAL electrode — RVC (Kawamata,
  Fu/Lin, Cai/Xu ×2, Ackermann), carbon felt (Kelly flow), Ni foam (Liu/Qiu, Courtois), and Kelly's
  own batch screen is RVC too (SI p. S16). A nominal current density on a 3D electrode cannot be
  compared with a planar-film ceiling. Closed for the class.
* **Turnover-rate lower bound** from yield/time: the batch electrolyses are current-limited
  (Kawamata SI p. S18: rate ∝ current; Gnaim SI: first order in current at 2.5 mA), so the
  observed rate is the electron supply, not the chemistry. Closed.

## What the sweep already says at the sourced values (no new solves)

From `julia/catalyst_ec_sweep.csv`, seven archetypes (unstirred 228, stirred 200, recirculating
flow 107, ANEC 36, microfluidic 12.5, RDE ≈ 9, rotating cylinder ≈ 9 µm), mA cm⁻²:

| row | k grid point nearest the sourced value | unstirred | recirc. flow | rotating cyl. | gain vs k = 0 gain |
|---|---|---|---|---|---|
| Ni-XEC | 10² | 5.01 | 9.60 | 23.6 | ×4.7 (×25) |
| Ni aryl amination | 10² | 0.87 | 1.60 | 3.93 | ×4.5 (×24) |
| amination with NH₃ | 10² | 1.99 | 3.30 | 6.12 | ×3.1 (×26) |
| Ni homocoupling | 10² | 14.4 | 28.1 | 69.6 | ×4.8 (×23) |
| Co–H hydroamination | 10³ | 5.48 | 9.93 | 20.8 | ×3.8 (×25) |
| Co–H isomerization | 10³ | 0.82 | 1.49 | 3.11 | ×3.8 (×23) |
| Co(salen) aza-Wacker | 10¹ | 0.58 | 0.65 | 4.00 | ×6.9 (×24) |

The count "10 of 11 remain below 25 mA cm⁻² in every architecture" holds at every one of these
(only the homocoupling row clears 25 anywhere, as it already did at k = 0). Reaction-layer
thickness at 10² for the Ni rows is 0.3–0.7 µm (Ting's 7.1 gives the same order): the reaction
sits inside every film, kinetic regime, not shuttle.

## Adoption proposal (NOT adopted; author's decision)

State-C values with a measured basis and a declared band, per the standard:

| rows | proposed k (M⁻¹ s⁻¹) | basis | band (sensitivity) |
|---|---|---|---|
| 4 Ni/ArBr rows | 10² | inside the measured bracket: Ting 3.4–56 (deactivated ligand, THF) ≤ k ≲ 10² (Kawamata, in medium) < 10⁴ (Till, dtbbpy) | 10¹ – 10⁴ |
| 2 Co–H rows | 7 × 10² | Boucher fit, Co(salen) + styrene, DMF | 10² – 10⁴ (alkene class, hydride source) |
| Co(salen) aza-Wacker | 10¹ | own CV with Na₂CO₃ at rt: ≲ 4 × 10¹ | 10⁰ – 10² (reflux) |
| Ni(tet a), Mn, Cu, Rh | 0 (floor) | no source | 0 – 10⁴ (existing G-CATK band) |

If adopted: re-solve the seven sourced rows at their declared values (49 cells; the solver and
control exist in `julia/run_catalyst_ecprime.jl`), then propagate — merged matrix (Fig. 5b),
Fig. 6b class line/band, Tables S5/S7, registry rows (one per adopted value, citing the pages
above), S5.7, the "24-fold" sentence (class gain becomes ≈ 3–7-fold for the sourced rows), Fig. 6c
(catalyst cell drawn with the reaction inside the film), the G-MSDERIVED pins. Whether the class is
shown as one mixed-basis line or split into "sourced k" and "floor" groups is a figure decision.

---

## ADOPTED 2026-09-11 (author: "yeah we gotta use the sourced k ... get everything solved by the morning")

What went into the tree, in order:

* `julia/run_catalyst_sourced.jl` -> `julia/catalyst_ec_sourced.csv` (126 cells: every catalyst row at
  k = 0 and, for the seven sourced rows, at the adopted k). The k = 0 member reproduces every published
  NP cell to 0.0 (exactly); the five sourced values that lie on the declared-band grid (nickel 10², aza-Wacker
  10¹) reproduce the sweep's cells with zero drift, so the two producers are one solver.
* `data/build_merged_matrix.py` overlays the 49 sourced cells exactly as it overlays the 56 mediated cells
  (i_ec >= its own k = 0 solve, plateau reached, none unresolved; 22 of the 49 end on a ramp wall tight to a
  plateau, the G-CATK tightness census covers them). Published matrix after the overlay:
  medians 8.2 / 9.3 / 16.8 / 44.2 / 111 / 108 / 122 mA cm⁻²; >=25: 12-14-18-31-36-36-36; >=50: 9-11-13-24-34-33-34.
  Moved by the adoption: flow >=25 17 -> 18, ANEC >=25 30 -> 31 and >=50 23 -> 24, microfluidic >=50 33 -> 34,
  rotating cylinder >=50 33 -> 34, and the four thick-film medians in the first decimal (all the homocoupling
  row, PhBr 0.3 M, whose sourced cells cross the thresholds). Unstirred 12/50 and 9/50 unchanged.
* `data/catalyst_ec_sensitivity.py` (G-CATK) gained the `sourced` block: control, grid consistency, band
  sensitivity. With every sourced row pushed to the edges of its measured bracket at once, the fifty-row
  counts move by at most 3 entries (at the top of the nickel bracket, 10⁴: microfluidic/RDE/RCE >=25 +3);
  the ten-of-eleven result holds at the low edges and FAILS at the high edge (4 of 11 clear 25 there),
  which the manuscript now states. Gains unstirred -> rotating cylinder: x3.1-6.9 at the adopted values
  against a floor median of x24.8.
* Registry (category 10, Table S7j): four rows -- the three adopted values with their locators and bands
  and the four floor rows -- replacing the single "0 (matrix); band swept" row; the Stokes-Einstein radius
  and D_S rows scoped to the layers they now govern. 223 published rows (66/71/86); ledger 0 tier moves.
* SI: S5.7 rewritten around the sourced values (ting2022, till2021, boucher2023, wilson2024 added to the
  bibliography; kawamata2019, cai2021, gnaim2022 already cited); the shared catalyst sentence, the Table S5
  caption (the Ni-XEC reading: 9.6 mA cm⁻² in the recirculating cell at the sourced k against the campaign's
  nominal 10), the S8 sentence and the two Stokes-Einstein scopings.
* Figure 6 redesigned (a-c cells / d-f regime profiles at the limiting current, k = 1e5, 1e2, 1e-2 / g-h
  intensification); Figures 4, 5, 10 re-rendered from the new matrix; Figure 7 byte-identical.
* Manuscript v88: `MS Drafts/scripts/apply_v88_fixes.py` (four artwork swaps, ten tracked edits computed by
  `data/ms_phrases.py`), `verify_v88.py`.

**Open, for the author.** The manuscript's catalyst sentences quote the three adopted values and point to
S5.7; the five kinetics papers are cited in the SI bibliography only, because adding Zotero items needs
Zotero open. If they should be cited in the main text, add them to the library and a v89 can field them.

**Two declared inputs became load-bearing (found by the first suite run, 03:00).** With the Ni-XEC row at
k = 10² its thin-film ceilings sit within 5 % of 25 mA cm⁻² (RDE 23.7, rotating cylinder 23.6, microfluidic
22.7), so (i) the DMA viscosity's homolog reading (0.927 against the printed 1.927 mPa s) lifts the
ANEC/microfluidic/RDE/rotating-cylinder ≥25 counts by one each -- disclosed in the DMA viscosity registry
row (Table S7b), which G-DMAMU now generates from its own artifact and checks; and (ii) the ten-of-eleven
count is conditional on the 4-5 Å hydrodynamic radius: it breaks at 4.27 Å on that row (1/r bound; 4.05 Å
under the √D law of the kinetic regime) against the 3.40 Å the ferrocene anchor predicts -- disclosed in the
SI's S3 passage and the radius registry row (Table S7c, ledger tier T2 → T3), which G-CATD now checks for.
Neither moves the unstirred counts, the carrier-class conclusion or the architecture ordering.
