# SIs to pull — 2026-08-23

Every one of these is a row whose modelled concentrations are **consistent and plausible but not
present in the article body**. They are state C, not state A, and must not be counted as measured
until the SI confirms them. For each row: the DOI, and the *specific number* to look for.

Where the body text already anchors part of a row, that part is marked ANCHORED — you only need
the missing piece.

## A. The eleven SIs

| # | DOI | row | what to find in the SI |
|---|---|---|---|
| 1 | **10.1021/ja402083e** | 6 — arene C–H pyridination | Body gives *"carried out on a 0.20 mmol scale"* and ANCHORS the electrolyte (*"0.3 M solution of Bu4NBF4 in CH3CN/pyridine (100/5)"*). **Need: the electrolysis volume.** Model's 0.02 M implies 10 mL. |
| 2 | **10.1126/science.adf4762** | 11 — Kolbe homocoupling | Nothing on concentrations in the body. **Need: hexanoic acid / hexanoate molarity, and the Me4NOH (15 mol%) + Me4NBF4 (5 mol%) basis** — mol% of what, and the acetone volume. Model carries 1.0 M carrier. |
| 3 | **10.1038/s41586-022-04691-4** | 13 — doubly decarboxylative | Body ANCHORS `NaI (0.2 M)` and gives *"about 2.5 h (0.1 mmol scale)"*. **Need: the DMF volume.** Model's 0.029 M implies ~3.5 mL. |
| 4 | **10.1021/ja211005g** | 14 — BDD phenol–arene | Body ANCHORS the electrolyte (0.68 g Et3NMe·OSO3Me / 27 mL HFIP + 6 mL MeOH = 0.0907 M) and gives only *"2 F/mol of phenol, ratio phenol/arene = 1:3"*. **Need: the phenol charge in mmol.** Model's 0.15 M implies 5 mmol/33 mL. |
| 5 | **10.1039/d0sc01694b** | 16 — cathodic Giese | **Need: 2-iodopropane and alkene concentrations**, and the basis of `NaCl 7 mol% + pH 2 HCl`. Model: 0.095 M / 0.079 M. |
| 6 | **10.1126/science.aav5606** | 22 — Birch reduction | Body names LiBr as replacing LiClO4 but gives no molarity. **Need: LiBr concentration and naphthalene concentration.** Model: 3.0 M / 0.18 M. |
| 7 | **10.1021/jacs.2c02102** | 24 — rAP imide reduction | Body gives *"performed on 0.1 mmol scale"*; footnotes name 1 equiv and 5 equiv of Me4N·BF4 only as **deviations**. **Need: the MeOH volume and the standard electrolyte equiv.** Model: 0.04 M / 0.08 M (implies 2.5 mL and 2 equiv). |
| 8 | **10.1039/c6sc02117d** | 37 — radical-cation Diels–Alder | Body ANCHORS the electrolyte (Table entry 1, `1.0 M LiClO4 / MeNO2`, 98%). **Need: trans-anethole concentration.** Model: 0.08 M. (Spelled *anethol* in this paper.) |
| 9 | **10.1139/v92-314** | 38 — BQ-mediated Wacker–Tsuji | **Need: the olefin concentration.** Model: 0.11 M with BQ 0.022 M (20 mol%). |
| 10 | **10.1002/anie.201603899** | 49 — N–N azo/pyrazole | Body ANCHORS only the solvent (HFIP). **Need: dianilide, and Bu4NPF6 concentrations.** Model: 0.04 M / 0.01 M — note 0.01 M is unusually dilute support, so this one is worth checking carefully. |
| 11 | **10.1021/acs.oprd.1c00036** | 28 — ACT alcohol oxidation | *Not strictly needed* — the 200 g run is fully ANCHORED in the body (`1272 mmol LEV-CH2OH and 5 mol % ACT in 2540 mL … NaHCO3 (1.0M)/Na2CO3 (1.0M), pH 8.5`). Listed only if you want the small-scale comparison. |

## B. Not an SI — a different paper is needed

**Ethylene solubility in KCl.** Row 31 now models ethylene at **4.67 mM**, the pure-water value
(131 mg L⁻¹ at 25 °C, 1 atm / MW 28.05). The anolyte is **1 M KCl** and ethylene is salted *out* of
it, so the true saturation is lower — roughly 20–30% on usual Setschenow magnitudes — and the row's
substrate-limited ceiling is currently an **upper bound**.

The salting-out reference already on hand (`je60038a033.pdf`, Clever & Holland, *J. Chem. Eng.
Data* **1968**, *13*, 411) does **not** contain this: it measures **argon** in KCl, and ethylene
only in **NaCl**, and only as a figure curve. Chaining ethylene-NaCl × (Ar-KCl/Ar-NaCl) would be two
derivations resting on salt effects transferring across gases, so it has not been done.

**What would settle it:** any source tabulating a Setschenow constant *k_s* for **ethylene in KCl**
(or ethylene solubility in KCl solutions) at 25 °C. Candidates worth trying —
- the IUPAC Solubility Data Series volume on ethene (Hayduk, ed.), which tabulates aqueous-salt data
- Battino/Clever's gas-solubility reviews
- any paper reporting C₂H₄ Henry constants in brines

## C. Not a paper — an OCR job

**`5507922.pdf`** (BASF, US 5,507,922, Lysmeral methoxylation, row 29) has **no text layer** —
5 characters extracted from the whole document. Nothing in that row has been verified. It needs
OCR, or a page image of the worked example so the substrate loading and the 0.3 wt% H2SO4/MeOH can
be read directly.

## D. Optional — κ dossier sources

Five conductivities are labelled ESTIMATES and print as a banner on every build. The only one with a
readily citable primary source is **1 M KCl aq = 111.3 mS/cm**, which wants the Jones & Bradshaw
demal standard (noting 1 demal is defined at 0 °C and so sits ~0.3% off 1 M at 25 °C). The other
four are derived from anchors already in the table and are documented in `KAPPA_ESTIMATED`.
