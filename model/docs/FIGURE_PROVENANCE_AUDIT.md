": "Trace every plotted number in all 14 Perspective figure generators to a source",
  "agentCount": 6,
  "logs": [
    "[stall] agent "trace:main-and-sec34" stalled (no progress) after 187s â retrying (1/5)"
  ],
  "result": {
    "traced": [
      "# Provenance trace: `make_fig3_ladder.py`, `make_fig_nd.py`, `make_figL.py`

Files read: the three generators; `data/parameters_provenance.csv`; `data/reactions_50.csv`; `julia/{params,correlations,reactions_table,run_tier0,run_ecprime,run_excell,run_mediated,npp_ecprime}.jl`; `julia/{tier0_matrix,tier0_ec_matrix,npp_ecprime_sweep,excell_profiles}.csv`; `make_si.js`; `AUDIT_REPORT.md`.

**Styling numbers excluded once, globally**: figure sizes, `dpi`, font sizes, `lw`, `alpha`, `zorder`, colour indices, rotations, `logspace` sample counts, text x/y placement offsets, axis limits and tick lists. One exception noted inline: the Fig-3 x-limit `0.3` doubles as the Tier-4 lower boundary.

---

## 1. `figs/make_fig3_ladder.py` â `sec4_Fig3_ladder.{svg,png}`

**Reads zero data files.** Every number below is a literal in the script.

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `C = 1740` | the entire master `i_lim = nFDC/Î´` curve (solid + dashed) | **UNSOURCED** â no registry row. Reverse-engineers as 17.4 mA cmâ»Â² Ã 100 Âµm | Reproduces the stirred median exactly, but is **not** `nFDC` for any reaction in the set; the on-figure label `i_lim=nFDC/Î´` misdescribes it |
| `300` | unstirred anchor Î´ | registry `delta (unstirred batch)`, class **lit-representative** (abolished), Bard & Faulkner ch. 1 / Amatore *JEAC* 2001 **500**, 62 â no page | â matches `correlations.jl :natural` |
| `6.1` | unstirred anchor i_lim | `julia/tier0_ec_matrix.csv`, col `natural`, median | â recomputed **6.0622** |
| `100` | stirred anchor Î´; Tier-1/2 boundary | registry `delta (stirred batch)`, **lit-representative**, Pletcher & Walsh â no page | â matches `:stirred` |
| `17.4` | stirred anchor i_lim | `tier0_ec_matrix.csv`, col `stirred`, median | â recomputed **17.3974** |
| `14` | RDE/RCE anchor Î´ | **UNSOURCED** | â **FAILS.** Model's own median Î´_rce = **10.94 Âµm**, Î´_rde = **12.65 Âµm**. 14 â 1740/124, i.e. back-solved onto the drawn line |
| `127` | RDE/RCE anchor i_lim | `tier0_ec_matrix.csv`, col `rce`, median | â recomputed **127.4** â but this is RCE alone; the RDE median is **111.7**, so the "RDE / RCE" label overstates RDE by 14% |
| `100, 500` | Tier-1 band | **UNSOURCED** | brackets Î´_natural=300, Î´_stirred=100 |
| `10, 100` | Tier-2 band | **UNSOURCED** | model's flow (38.0â95.8), thingap (15.1â38.0), rde (8.5â15.8), rce (8.8â14.9) *all* land here |
| `1, 10` | Tier-3 band, labelled "Thin-gap / 3D-printed" | **UNSOURCED** | â **CONTRADICTED** â the model's `:thingap` archetype gives Î´ = 15.1â38.0 Âµm (median 29.5), i.e. Tier 2 |
| `0.3, 1` | Tier-4 band ("GDE / MEA, zero-gap"); `0.3` also sets the x-limit | **UNSOURCED** | â no archetype in the model goes below **8.46 Âµm**; zero model support |
| `10` (solid/dashed split), `500`, `0.3` | "model-anchored" vs "frontier" segments | **UNSOURCED** | â mislabels: RDE/RCE Î´'s straddle 10 Âµm, so the true model-anchored range is â8.5â300 Âµm |
| `25` | threshold line | registry `Thresholds 25 / 50 mA cm-2`, **measured-lit**, Ferretti *OPRD* 2025, **29**, 322â332, **Fig. 11, page-verified**; also `params.jl I_THRESH` | â best-sourced number on the figure |
| `50` | threshold line, "(the barrier)" | same registry row | value â; the word "barrier" is unattributed |
| `"g â 100 g"`, `"100 g â kg"`, `"mg â g"`, `"frontier"` | production-scale annotations | **UNSOURCED** â no registry row, no SI sentence | â unauditable |
| `"Griffin, AbbVie (OPRD 2024)"`, `"Bottecchia, MSD 2022; Kappe 2023"`, `"Mo & Jensen (Science 2020)"`, `"Manthiram 2024; Berlinguette"` | on-figure citations | not in the registry; only `bottecchia2022` and `sherbo2018` (Berlinguette) resolve in `make_si.js` | â see finding 6 |

`grep` of `make_si.js` for `ladder`, `Tier 1`, `100â500`, `Griffin`, `AbbVie`, `Manthiram`: **no hits**. This figure has no SI paragraph behind it.

---

## 2. `figs/make_fig_nd.py` â `sec4_figI_nondim.{svg,png}` (panel a is duplicated verbatim as main-text **Fig. 4B-c** in `make_fig4B.py` L85âL95)

### Panel a â architecture payoff map

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `300` (Î´_batch, implicit in xÌ) | x-axis normalization | registry `delta (unstirred batch)`, lit-representative | â consistent with `correlations.jl` |
| `mu = 0.041` | all three mediated curves + legend title | **derived** from `julia/run_mediated.jl` MedSpec ACT row: C_med 25, C_S 500 mol mâ»Â³, D_med 5.93e-10, D_S 7.22e-10 (conditions page-verified to Zhong/Stahl *OPRD* 2021) | arithmetic â (25/500)Ã(5.93/7.22) = **0.04107**; **physics â** â omits n_S = 2 (finding 2) |
| `eps = 0.060` | catalyst line | C's â `data/reactions_50.csv` Ni-amination row (0.005 / 0.05 M, exemplar-verified Kawamata *JACS* 2019 Table 4 fn a p. 6399). **"D ratio 0.6" UNSOURCED** â no substrate D for this reaction exists in `reactions_50.csv`, `reactions_table.jl`, or the registry | 0.1 Ã 0.6 = 0.060 â; the 0.6 is unverifiable |
| `sl = 1, 10, 100` | the three mediated curves' Î´_batch/x_k | illustrative decades, **UNSOURCED** as system values | not wrong, but note the ACT system supplying Î¼ has x_k = **7.70 Âµm** â Î´_batch/x_k = **38.9**, none of the three |
| band `(2.5, 3.5)` "stirred" | archetype annotation | derived: xÌ = 300/100 | â exact (3.00) |
| band `(5, 15)` "flow" | archetype annotation | **UNSOURCED** | â **CONTRADICTED** â model flow xÌ = **3.13â7.90**, median **4.03**. Band excludes the median; its top is 1.9Ã the model max |
| band `(30, 100)` "thin gap / RDE / RCE" | archetype annotation | **UNSOURCED** | â **CONTRADICTED** â thingap xÌ = **7.9â19.9** (median 10.2, entirely outside); rde **19.0â35.5** (median 23.7); rce **20.2â34.3** (median 27.4). Nothing anywhere near 100 |
| `1.06` "unstirred batch" | label | xÌ = 1 by definition | â |
| "direct: every Î´ gain converts 1:1" | annotation | y = x | â |
| "dilute catalyst: parallel â only C_cat moves it" | annotation | y = Îµx on logâlog | â |
| "mediated plateau â¦ convection buys nothing here" | annotation | plateau branch y = Î¼Â·sl for xÌ < sl | â correct, and it is the Î´ > x_k regime as claimed |

### Panel b â ECâ² collapse

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `delta=100e-6, C_med=20, C_S=500, D_med=6e-10, D_S=1e-9` | Î³, i_sh, x-axis | **exact match to `julia/run_ecprime.jl` consts** | â fully reproducible |
| `96485.33` | i_sh | registry `Faraday constant F` 96485.332, CODATA 2018 | â (truncation immaterial) |
| `gamma` â **41.7** (cap line + label) | substrate cap | derived | â 41.667; equals `i_subcap` 48.24 mA cmâ»Â² / i_sh |
| `i_sh` â 1.1578 mA cmâ»Â² | y normalization | derived; = `run_ecprime` i_shuttle | â |
| marker data | `julia/npp_ecprime_sweep.csv`, cols `xk_um`, `ilim_mAcm2` | â real file read | see table below |
| `sw.k_M <= 1e3` | drops 3 of 10 solver points | **UNSOURCED exclusion** | â finding 8 |
| "k = 10â»Â²â10Â³ Mâ»Â¹sâ»Â¹" | annotation | matches the filter | â |
| theory `min(max(1,x), gamma)` | grey curve | SI Eq. S13âS15 | data deviate up to â31% |

Recomputed point-by-point (A = i_lim/i_sh, x = 100/x_k):

| k (Mâ»Â¹sâ»Â¹) | x = Î´/x_k | A (plotted) | theory | A/theory | `limiter` column |
|---|---|---|---|---|---|
| 0.01 | 0.289 | 1.026 | 1.000 | **1.026** | newton-wall (no collapse) |
| 0.1 | 0.913 | 1.252 | 1.000 | **1.252** | newton-wall (no collapse) |
| 1 | 2.887 | 2.799 | 2.887 | 0.970 | mediator |
| 10 | 9.129 | 8.188 | 9.129 | 0.897 | mediator |
| 100 | 28.87 | 20.72 | 28.87 | **0.718** | newton-wall (no collapse) |
| 300 | 50.0 | 28.72 | 41.67 | **0.689** | newton-wall (no collapse) |
| 1000 | 91.29 | 36.16 | 41.67 | 0.868 | mediator |
| *3000* | *158* | *40.05* | *41.67* | â | *dropped by filter* |
| *10â´* | *289* | *25.27* | *41.67* | â | *dropped* |
| *10âµ* | *913* | *16.66* | *41.67* | â | *dropped* |

Also unstated: panel a uses the **ACT** base case (25 mM, D ratio 0.82) while panel b uses the **generic** `run_ecprime` base case (20 mM, D ratio 0.60). Two different mediator systems in one figure.

---

## 3. `figs/make_figL.py` â `sec4_figL_excell.{svg,png}`

**Reads `julia/excell_profiles.csv`** (all three curves are real data). Backed by SI Â§S5.5 (`make_si.js` L252), which states 167 Âµm, 131 mA cmâ»Â², 2.2%, 2.9 mA cmâ»Â², 97.8%, â30 Âµm, 785 mA cmâ»Â², 2.00Ã.

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `2.0` (Ã2, Clâ» and OX normalizers) | blue/orange curve scale; "/ 2 M" labels | `run_excell.jl C_Cl = 2000` mol mâ»Â³; `reactions_50.csv` Cl-epoxidation C_carrier (Leow *et al.* exemplar). Registry has a `2 M NaCl aq` **conductivity** row (measured-lit, CRC 97th) but no concentration row | â data reach 1.99 M in bulk |
| `5.0` (mM) | green curve scale; "C_P,sat = 5 mM" | registry `Propylene C_sat (aq, 1 atm)` 5e-3 M, **measured-lit**, Sander *ACP* 2015, **15**, 4399â4981 (no page/table) | â = `run_excell C_P`; data reach 4.64 mM |
| `0.25` (mM) | defines the shaded "propylene-free zone" (5% of bulk) | **UNSOURCED** arbitrary cut, but the resulting extent is **computed from data** | â recomputed x_dark = **29.45 Âµm**; SI's "â30 Âµm" â |
| `131` mA cmâ»Â² (Ã2) | annotation + caption | `run_excell.jl i_op = 1306` A mâ»Â²; SI states 131 | â arithmetic (130.6). **â provenance**: the source comment calls it "the tier-0 unstirred number" â that is 130.6 in the *superseded* `tier0_matrix.csv`; the production `tier0_ec_matrix.csv` now gives **263.0** for this reaction |
| `97.8%` exported | orange annotation | `run_excell` stdout; SI | â **independently recomputed** from `excell_profiles.csv`: Fâ«kÂ·c_oxÂ·c_P dx = **2.880 mA cmâ»Â²** â 2.21% in-film â **97.79% exported** |
| `2.9` mA cmâ»Â² `(2.2%)` | green annotation | same | â recomputed **2.880 mA cmâ»Â² / 2.21%** |
| `167` Âµm (x_k) | orange annotation | derived â(D_OX/(kÂ·C_P)); D_OX 1.4e-9 registry `Cl2/HOCl lumped OX (aq)`, **lit-representative**, "CRC / water-treatment transport data" (no locator); k = 10 registry Table S6, **lit-representative** | â recomputed **167.3 Âµm** |
| `100` Âµm (Î´) | caption | registry `delta (stirred batch)`, lit-representative | â = `run_excell delta` |
| `k = 10` Mâ»Â¹sâ»Â¹ | caption | registry `8 mediated rate constants k (Table S6)`, **lit-representative** | value unlocated, but SI supplies a genuine sensitivity bound (conclusions k-independent from 10 to 10â·) |
| `785` mA cmâ»Â² | caption | **`run_excell.jl` stdout only â in no CSV**; SI repeats it | â not reproducible from archived files. Its ratio does check: Fick bound recomputed = **391.7**, 785/391.7 = **2.0039** |
| `2.00Ã` Fick | caption | derived; matches the audited analytic binary-electrolyte migration factor of 2 | â |
| `0.05` sâ»Â¹ (k_L a) | caption | **UNSOURCED** â no registry row, no SI sentence | â |
| `100` mL | caption | registry `Cell volume / electrode area` = 100 mL / 10 cmÂ², class **assumption**, citation `--`, filed under "9. Thermal model" | declared assumption, reused out of category, no sensitivity bound for this use |
| `4.8` A | caption | derived 2Â·FÂ·k_LaÂ·C_PÂ·V | â recomputed **4.824 A**, but inherits the unsourced k_La |
| `1.3` A | caption | derived i_op Ã 10 cmÂ² | â 1.306 A; area from the same assumption row |
| "surface barely perturbed at 131 mA cmâ»Â²" | blue annotation | data: c_Cl(0)/c_bulk = **0.835** | â soft â a 16.5% surface depletion |
| "generated at the electrode" | orange annotation | data: c_OX 0.958 M at xâ0 â 0.027 M at 97 Âµm | â |
| "x_k = 167 Âµm > Î´" | orange annotation | 167 > 100 | â |

---

## Most serious problems, ranked

**Affects a main-text figure**

1. **Fig. 4B-c archetype bands contradict the model's own correlations** (`make_fig_nd.py` L37, duplicated at `make_fig4B.py` L92). "flow" is drawn at xÌ 5â15 but the model gives 3.13â7.90 (median 4.03); "thin gap / RDE / RCE" is drawn at xÌ 30â100 but thin-gap is 7.9â19.9 (median 10.2, wholly outside the band), RDE 19.0â35.5, RCE 20.2â34.3, and *nothing* reaches 100. This is the Ã30/Ã9.0 mediator failure mode exactly: the bands are what a reader uses to read "what a flow cell buys," and they are 2â3Ã too far right, which also moves where the mediated plateau appears to bite. **Fix**: compute the bands from `delta_eff()` over the 50 rows (I did: flow 3.1â7.9, thingap 7.9â19.9, RDE 19.0â35.5, RCE 20.2â34.3) and split thin-gap from RDE/RCE, which are not the same band.

2. **Î¼ = 0.041 is a factor of 2 too high; SI Eq. S17 is internally inconsistent.** The y-axis is i_lim/i_lim^direct(batch) with i_direct = n_SÂ·FÂ·D_SÂ·C_S/Î´_batch, and the ACT substrate is a 2-electron oxidation (`run_mediated.jl` MedSpec n_S = 2). Îµ is defined *with* n_c/n; Î¼ is defined *without* n â in the same equation, in both the SI and the code. Correct Î¼ = 0.0205. Every mediated curve and the legend title are affected. `AUDIT_REPORT.md` L118â119 records Î¼ = 0.041 as "verified", but that check confirmed only C's and the D ratio (0.82 = 5.93e-10/7.22e-10 â which I confirm), never the electron count.

**Affects Fig. 3, which has no SI text at all**

3. **`make_fig3_ladder.py` is unauditable by construction.** Zero data reads. The three anchor i_lim values happen to reproduce `tier0_ec_matrix.csv` medians exactly today (6.0622 / 17.3974 / 127.4), so the figure is currently right â but nothing enforces it, and this exact drift has already happened elsewhere: `run_excell.jl` still pins its operating point to 130.6 mA cmâ»Â², a number the production matrix replaced with 263.0. Everything else on the figure â `C = 1740`, four tier boundaries, four reactor-class labels, four literature citations, four production-scale ranges â lives only in the script. `grep make_si.js` finds no "ladder", no tier-Î´ bands, no tier exemplars. **Fix**: read the medians from the CSV; register the tier boundaries; give the figure an SI paragraph or drop the unsupported annotations.

4. **The RDE/RCE anchor's Î´ = 14 Âµm is fabricated.** The model's median Î´_rce is **10.94 Âµm** and Î´_rde **12.65 Âµm**; 14 Âµm is 1740/124, back-solved so the marker lands on the drawn `C/Î´` line. At its true Î´ the point sits ~20% *below* the line, because one 1/Î´ curve cannot thread medians taken over 50 reactions with different nFDC (at the true medians the line over-predicts by 16%, 18%, 23%, 25% for flow, thingap, rde, rce). The visual claim "the medians lie on i_lim = nFDC/Î´" is manufactured by moving an x-coordinate. **Fix**: plot the anchors at their computed Î´ and either fit the line to them or relabel it as a guide, not `nFDC/Î´`.

5. **Tiers 3 and 4 have no model support and Tier 3 is mislabelled.** Tier 3 (Î´ 1â10 Âµm) is captioned "Thin-gap / 3D-printed", but the model's own thin-gap archetype (250 Âµm gap, LÃ©vÃªque) yields Î´ = 15.1â38.0 Âµm, median 29.5 â Tier 2. No archetype in the model produces Î´ < 8.46 Âµm, so the whole dashed "frontier" segment (0.3â10 Âµm) and both bottom tiers are extrapolation drawn at the same visual weight as the anchored region.

6. **Three of the four on-figure citations do not resolve.** "Griffin, AbbVie (OPRD 2024)" and "Manthiram 2024" match no key in `make_si.js`'s bibliography ("Griffin" appears only as a co-author of `hioki2023`, *Science* 2023, Baran group; "AbbVie" and "Manthiram" appear nowhere). "Kappe 2023" is presumably `malviya2023` (*OPRD* 2023), whose first author is Malviya. "Berlinguette" carries no year. None has a locator. Per the standard these are unusable as printed â either resolve them to registry rows with volume/page or remove them.

**Affects an SI claim**

7. **Four of the seven validation points in Fig. I(b) are not converged limiting currents.** `npp_ecprime_sweep.csv` labels k = 10â»Â², 10â»Â¹, 10Â², 3Ã10Â² as `newton-wall (no collapse)`, which by SI Â§S5.6's own wording means "strict lower bounds" from a stalled ramp. They are drawn as ordinary markers with no flag. The two worst (k = 100, 300) sit **28% and 31% below** the theory curve â the direction a stalled ramp produces â so the visible scatter in the "universal collapse" claim may be numerical, not physical. **Fix**: mark them (open symbols / down-arrows) or exclude them with the reason stated.

8. **Silent exclusion of the three highest-k points.** `sw[sw.k_M<=1e3]` drops k = 3Ã10Â³, 10â´, 10âµ, whose A values are 40.1, **25.3, 16.7** â the amplification *turns over and falls 2.4Ã* as k rises, contradicting the plotted "capped at Î³" plateau. Only the k range is disclosed; the reason is not. Either they are solver artefacts (say so, cite the `newton-wall` label) or the cap is wrong.

9. **The figure-L GâL closing argument rests on an unregistered number.** k_LÂ·a = 0.05 sâ»Â¹ appears in no registry row and in no SI sentence, yet it produces "bulk GâL capacity â 4.8 A â« 1.3 A cell current" â the claim that gasâliquid delivery is *not* binding. The 100 mL / 10 cmÂ² it multiplies is registered, but as class **assumption**, citation `--`, under "9. Thermal model". Note the SI says the *opposite* emphasis ("k_LÂ·a must be sized to match the chlorine-generation current") and quotes none of these numbers. **Fix**: either register a k_LÂ·a with a source and a sensitivity bound, or delete the third caption line and let the SI's qualitative statement stand.

10. **i_lim = 785 mA cmâ»Â² is archived nowhere.** It exists only in `run_excell.jl` stdout; `excell_profiles.csv` carries profiles only. Reproducing it requires re-running Julia. Its consistency does check (785 / 391.7 = 2.0039 against the Fick bound I recomputed, matching the audited migration factor of 2), so this is an archiving gap, not a wrong number â but the standard as written is not met. **Fix**: have `run_excell.jl` emit a one-row `excell_summary.csv`.

**Lower severity**

11. Two different propylene diffusivities for the same system: `run_excell.jl D_P = 1.2e-9` vs `run_mediated.jl` MedSpec `D_S = 1.37e-9`. Neither is in the registry (there is no propylene D row). D_P scales the in-film flux, so it moves the headline 2.2% / 97.8% split by roughly 15% relative.
12. The Fig-3 anchor labelled "RDE / RCE" plots the **RCE** median (127.4); the RDE median is 111.7 â 14% lower.
13. `make_figL.py` docstring says "98.6% of the oxidant exported"; the rendered annotation and the SI both say 97.8% (which is the correct one â I recomputed 97.79%). Stale docstring, not rendered.
14. "surface barely perturbed at 131 mA cmâ»Â²" describes a **16.5%** surface depletion (c_Cl(0)/c_bulk = 0.835).
15. Îµ's "D ratio 0.6" is unsourced: no substrate diffusivity for the Ni-amination exemplar exists in `reactions_50.csv`, `reactions_table.jl`, or the registry. The concentrations it multiplies (5 mM / 50 mM) *are* exemplar-verified to Kawamata *JACS* 2019, Table 4 fn a, p. 6399.

**Best-sourced numbers found across the three files**, for contrast: the 25 / 50 mA cmâ»Â² thresholds (Ferretti *OPRD* 2025, **29**, 322â332, Fig. 11, page-verified), the Faraday constant (CODATA 2018), and propylene C_sat (Sander *ACP* 2015). Everything Fig. 3 draws *besides* the two threshold lines and the three CSV-derived medians is script-internal.",
      "## Scope note

Pure styling literals â font sizes, `lw`, `ms`, `alpha`, RGB indices into `rainbow_2`, `figsize`, `dpi`, `w_pad`, text x/y placement coordinates, axis limits and tick counts â are ignored throughout and not listed. Everything below is a number that reaches plotted data, an annotation string, a reference line, a band edge, or a quoted value.

All three scripts hardcode `os.chdir("/home/claude/rce/sec4")` and read `reactions_50.csv` from the CWD root, not `data/`. I verified the repo copies reproduce the rendered figures exactly, so alignment holds, but none of the three can be re-run in place.

---

## 1. `figs/make_fig_profiles.py` â `sec4_figJ_profiles.png`

| value | what it controls | source | verified? |
|---|---|---|---|
| 9.649, 24.121, 38.594, 48.001 mA cmâ»Â² | the four fanned curves in (a), labels "10 / 24 / 39 / 48" | `julia/profiles_direct.csv`, `case=fan`, col `i_mAcm2` | **YES** â labels match data; ratios are exactly 0.2/0.5/0.8/0.995 Ã i_lim |
| 48.243 mA cmâ»Â² (rendered "48") | "at i_lim = 48 mA cmâ»Â² â¦" annotation, (a) | `profiles_direct.csv` col `ilim_mAcm2` | **YES** â recomputed nFDC/Î´ = 1Â·96485.332Â·1e-9Â·500/100e-6 = 482.43 A mâ»Â² = 48.243 |
| 0.5 M substrate | in-panel text (a); sets the entire panel | **UNSOURCED** â `const C_S = 500.0` in `run_profiles.jl`; no registry row (cat. 5 has no generic-substrate entry) | value is real in the code, but has no external source |
| 1 eâ» | in-panel text (a) | **UNSOURCED** â `s = -1.0` in `run_profiles.jl` | â |
| D = 10â»â¹ mÂ² sâ»Â¹ | in-panel text (a) | **UNSOURCED** â `const D_S = 1.0e-9`; registry's only 1e-9 rows are "Liâº (generic organic)" and "BuâNâº/Qâº", different species | â |
| Î´ = 100 Î¼m (stirred) | (a) text, (b) label, (c) text | registry `delta (stirred batch)` = 100 Î¼m, class *lit-representative*, Pletcher & Walsh 2nd ed., **chapter-level, no page** | value used correctly; provenance is the abolished class |
| Î´ = 300 Î¼m (unstirred) | (b) label | registry `delta (unstirred batch)` = 300 Î¼m, *lit-representative*, Bard & Faulkner ch. 1 / Amatore, **no page** | same |
| **Î´ = 30 Î¼m "flow cell"** | (b) grey/blue curve + label | **UNSOURCED** â `("flow", 30e-6)` hardcoded in `run_profiles.jl`. The paper's own flow archetype (LÃ©vÃªque, 1 mm gap, L 5 cm, u 5 cm/s) gives **68.1 Î¼m** at D = 1e-9 | **NO â inconsistent with the flow archetype used in figs F/G/M by 2.3Ã** |
| **Î´ = 10 Î¼m "thin gap / RCE"** | (b) green curve + label | **UNSOURCED** â `("thingap", 10e-6)` hardcoded. Thin-gap archetype (250 Î¼m gap) gives **27.0 Î¼m**; RCE gives 8.8â11.2 Î¼m | half-true: 10 Î¼m is the RCE number, **not** the thin-gap number |
| 50 mA cmâ»Â² barrier current | (b) run current, `i_bar = 500.0` A mâ»Â²; "50 mA cmâ»Â² barrier" text in (a) and (b) | registry `Thresholds 25 / 50 mA cm-2`, *measured-lit*, Ferretti OPRD 2025 29, 322-332, Fig. 11, page-verified | **YES** |
| c_surf = 0.90 (thin gap) | (b) annotation | hardcoded string | **YES** â data gives 0.8964; 1 â 50/482.427 = 0.8964 |
| **c_surf = 0.69 (flow cell)** | (b) annotation | hardcoded string; consistent with Î´ = 30 Î¼m | arithmetic **YES** (1 â 50/160.809 = 0.6891); but at the paper's real flow archetype (68.1 Î¼m, i_lim = 70.8) it is **0.29** |
| i_lim = 48 / i_lim = 16 (starved cases) | (b) annotations | `profiles_direct.csv` `ilim_mAcm2` = 48.243 / 16.081 | **YES** (16.081 = 482.427/3) |
| 300.0, 1.0 | (b) bulk padding appended after Î´ | plotting construct | benign; forces c = 1 beyond Î´, ~0.6% jump at the last solver node |
| k = 1, k = 10Â³ Mâ»Â¹ sâ»Â¹ | (c) two curve families | `julia/npp_ecprime_profiles.csv` col `k_M` | **YES** (file also holds k = 100, not plotted) |
| **x_k â 1 Î¼m** | (c) headline annotation "activated form consumed within x_k â 1 Î¼m" | formula â(D_med/kC_S) with **bulk** C_S = 500 â 1.095 Î¼m | **NO â see problem #2.** Actual plotted 1/e decay = **2.29 Î¼m**; c_ox at x = 1 Î¼m is still 0.46 (65% of its surface value); <5% of surface only at 6.6 Î¼m |
| Î´ = 100 Î¼m, 0.9 i_lim | (c) caption text | `run_ecprime.jl` (`frac 0.1:0.1:0.9`) | **YES** |
| C_med = 20 mM, D_med = 6e-10 mÂ² sâ»Â¹, C_sup = 0.1 M | set the (c) curves | **UNSOURCED** â `run_ecprime.jl` constants; no registry row for the generic "ACT-like base case" | â |
| "substrate dips too (total catalysis)" | (c) annotation | â | **partially NO**: c_S(0) = 0.237, and `npp_ecprime_sweep.csv` labels the k = 10Â³ limiter as **"mediator"**, not substrate. The SI reserves "total catalysis" for larger k |

**Numbers that exist only inside the plotting script:** none of the plotted data, but the strings `0.90`, `0.69`, `48`, `16`, `x_k â 1 Î¼m` are hand-typed and not read from the CSVs.
**Figure is not referenced in the SI** (`Fig. J` appears nowhere in `make_si.js` or `SI_Section4_Transport_Model_v3.docx`).

---

## 2. `figs/make_figFG.py` â `sec4_figF_gap.png`, `sec4_figG_waterfall.png`

| value | what it controls | source | verified? |
|---|---|---|---|
| `BARRIER = 50.0` | vertical rule (F), horizontal rule (G), all colour bins | registry `Thresholds 25 / 50 mA cm-2`, Ferretti 2025 Fig. 11, page-verified | **YES** |
| `OPER = 25.0` | grey band edge (F), dotted rule (G), "industry ceiling" | same registry row | **YES** |
| "10/14 scale-ups < 25 (Ferretti 2025)" | (F) band annotation | registry method_note: "n = 14 reporting: 10 < 25; 3 in 25-50" | **YES** |
| "the 50 mA cmâ»Â² barrier: 1/14 exceed" | (F) annotation | same row, by subtraction 14 â 10 â 3 = 1 | **YES** |
| 50 open-circle values (`natural`) | (F) left endpoints | `julia/tier0_ec_matrix.csv` col `natural` | **YES** â recomputed 0.1Â·nFDC/Î´ with Î´ = 300 Î¼m for both spot-checked rows to 4 s.f. |
| 50 arrowhead values (`best` = max of thingap/rde/rce) | (F) right endpoints | `tier0_ec_matrix.csv` | **YES** â `rce` wins 47/50, `rde` 3/50 |
| "crosses 50 mA cmâ»Â² (**34/50**)" | (F) legend, computed | recomputed from data | **YES** â also equals the SI's "34/50 at a rotating-cylinder electrode" (line 382) |
| "transport-capped by dilute carrier (**14/50**)" | (F) legend, computed | recomputed | **YES** (10 catalyst-, 3 substrate-, 1 mediator-carried) |
| (implicit) 2/50 in 25â50 band | (F) orange legend entry carries **no count** | â | 34 + 14 = 48; a reader cannot recover 50 |
| 6.535, 19.61, 24.48, 61.69, 188.1 mA cmâ»Â² | (G-a) bars 1â5 | `tier0_ec_matrix.csv` row "Dehydrogenative lactonization" | **YES** â independently recomputed from LÃ©vÃªque/Eisenberg/Levich + n = 2, D = 1.6256e-9, C = 62.5 mol mâ»Â³: 6.5353 / 19.6058 / 24.4836 / 61.6948 / 188.0912 |
| 0.1652, 0.4955, 0.9085, 2.289, 5.394 | (G-b) bars 1â5 | same file, row "Ni-catalyzed aryl amination" | **YES** â recomputed exactly |
| Ã3.0, Ã1.2, Ã2.5, Ã3.0, Ã2.0 (G-a) | inter-bar multipliers | computed in-script | **YES** â 3.000, 1.248, 2.520, 3.049, 2.000 |
| Ã3.0, Ã1.8, Ã2.5, Ã2.4, Ã5.0 (G-b) | inter-bar multipliers | computed in-script | **YES** â 3.000, 1.834, 2.520, 2.356, 5.000 |
| 0.0625 M "(verified)" | (G-a) header text | `data/reactions_50.csv` `conc_provenance`: "biaryl acid 0.0625 M (0.5 mmol/8 mL), Zhang/K. Xu/Zeng OL 2018, **Scheme 1 fn a p 253, Fig 3 p 254**" | **YES â class A with page locator** |
| 5 mM catalyst "(verified)" | (G-b) header text | `reactions_50.csv`: "Ni(bpy)âBrâ 10 mol% (2.5â5 mM), Kawamata JACS 2019, **Table 4 fn a p 6399**" | **YES â class A with page locator** |
| "K. Xu/Zeng 2018" | (G-a) header | `reactions_50.csv` `exemplar` = "Zhang/K. Xu/Zeng OL 2018" | **YES** |
| **Ã2 â "2Ã conc. (0.125 M)"** (bar 6, G-a) | green bar, 376.2 mA cmâ»Â² | **UNSOURCED** â `r.rce*2` invented in the script | arithmetic YES; the factor 2 has no source or feasibility bound |
| **Ã5 â "5Ã cat. (25 mM)"** (bar 6, G-b) | green bar, 26.97 mA cmâ»Â² | **UNSOURCED** â `r2.rce*5` invented in the script | arithmetic YES; **but see problem #3** â 25 mM Ni against 50 mM substrate is 50 mol%, i.e. stoichiometric, not catalytic |
| "flow 1 mm", "thin gap 250 Î¼m", "RCE 3000 rpm" | (G) x-tick labels | registry cat. 7: flow *correlation-est* (Pickett; Walsh & Ponce de LeÃ³n); RCE *measured-lit* (Eisenberg 1954, **101, 306-320**); **thin-gap is *lit-representative* with citation "Atobe/Noel flow-electrochemistry literature" â no author/year/page** | geometry reproduces the numbers, but the thin-gap geometry itself has no locator |
| "reactor levers alone never cross the barrier" | (G-b) claim | max of bars 1â5 = 5.394 < 50 | **YES** |

**Row alignment check:** `pd.concat(..., axis=1)` joins `reactions_50.csv` and `tier0_ec_matrix.csv` **positionally with no key**. I verified `rx.reaction == t0.reaction` for all 50 rows, so the current figure is correct â but the join is silent-failure-prone if either file is ever re-sorted.

**Merge provenance:** `tier0_ec_matrix.csv` = `tier0_matrix.csv` with the 8 mediated rows replaced by `mediated_ec_matrix.csv` ECâ² values via `data/build_merged_matrix.py`; I confirmed all 48 substitutions and the single `wall` fallback (Hofmann/unstirred â Tier-0 6.947).

**Fig. F is referenced in the SI (twice); Fig. G once ("Figs. F and G", Â§S8).**

---

## 3. `figs/make_figM.py` â `sec4_figM_mediated_ec.png`

| value | what it controls | source | verified? |
|---|---|---|---|
| `i_tier0_mAcm2` (14 open circles) | arrow tails | `julia/mediated_ec_matrix.csv` | **YES** â recomputed Hofmann/stirred: FÂ·D_redÂ·C_med/(\|s\|Â·Î´)Â·0.1 = 96485.332Â·2.7e-9Â·80/1e-4Â·0.1 = 20.84 â |
| `i_ec_mAcm2` (14 filled circles) | arrow heads | same file | read directly from solver output |
| `i_subcap_mAcm2` (14 grey ticks) | "substrate cap n_S F D_S C_S/Î´" | same file | **YES** â Hofmann/stirred: 2Â·96485.332Â·2e-9Â·400/1e-4Â·0.1 = 154.38 â |
| Î´ = 100 Î¼m (stirred) | legend | `params.jl` / registry, *lit-representative* | **YES** |
| "thin-gap flow" arrows | green series | `delta_eff(:thingap)` per system: **22.7â37.6 Î¼m**, not a single value | correct but the legend implies one Î´ |
| 25 (dotted), 50 (solid), "50 (the barrier)" | reference lines | registry Ferretti row, page-verified | **YES** |
| 80 mM / 25 mM / 2 M / 33 mM / 40 mM / 22 mM / 0.25 M / 0.1 M in the y-labels | mediator concentrations quoted on the figure | `run_mediated.jl` `SPECS` C_med = 80, 25, 2000, 33, 40, 22, 250, 100 mol mâ»Â³, each page-anchored in `reactions_50.csv` / SI Table S6 | **YES â all eight correct** |
| "(250 um)" inside the reactor key | row selection string | `params.jl` reactor label | **YES** |
| **`"NHPI-mediated benzylic C-H -> ketone"`** | selects the 4th row's data | data file says **`"NHPI-mediated allylic C-H -> enone"`** | **NO â zero matches; row is drawn empty** |

**Numbers existing only in the script:** none â every plotted coordinate is read from `mediated_ec_matrix.csv`. Rate constants k are *lit-representative* per registry cat. 10 (Table S6) but are not drawn on this figure.

**Fig. M is not referenced in the SI** (`Fig. M` appears nowhere). Its underlying matrix *is* Table S6, which is load-bearing.

---

## Most serious problems, ranked

**1. `make_figM.py` silently drops one of the eight systems â and it is the one carrying an SI structural result.**
The lookup key `"NHPI-mediated benzylic C-H -> ketone"` does not exist; the data says `"NHPI-mediated allylic C-H -> enone"`. `g.empty â continue` skips it without error, so the row "ClâNHPI / allylic CâH (33 mM med)" is rendered as a **y-label with no data** (visible in the PNG). The docstring claims "all 8 mediated reactions"; 7 are shown. SI Â§S5.7 states as its *third* structural result "the ClâNHPI system barely moves (Ã1.0â1.1 outside the unstirred cell) â¦ x_k â 158 Î¼m" â I confirmed those numbers (1.135 stirred, 1.020 thin-gap, x_k = 158.2 Î¼m), and the figure meant to display them omits exactly that row. One-line fix.

**2. `make_fig_profiles.py` panel (c): the "x_k â 1 Î¼m" annotation is off by ~2.3Ã, in the same way the mediator figure's "Ã30" was really Ã9.0.**
x_k = â(D_med/kC_S) = 1.095 Î¼m uses **bulk** C_S = 500 mol mâ»Â³, but the profile is drawn at 0.9 i_lim where the surface substrate is depleted to 0.237 Ã bulk. Recomputing with the actual surface concentration gives 2.25 Î¼m, which matches the measured 1/e decay of the plotted c_ox curve, **2.29 Î¼m**. At x = 1 Î¼m the activated mediator is still at 0.46 (65% of its surface value); it falls below 5% only at 6.6 Î¼m. The qualitative conclusion (x_k âª Î´ = 100 Î¼m) survives, but the quoted number does not describe the curve it points at.

**3. `make_figFG.py` panel (G-b): the concentration lever is illustrated with a loading that is not catalytic, unsourced and unbounded.**
`r2.rce*5` labelled "5Ã cat. (25 mM)". The verified exemplar is 5 mM Ni against 0.05 M ArBr (10 mol%); 25 mM against the same substrate is **50 mol%**, i.e. a stoichiometric metal reagent. The figure's punchline â "the missing lever is carrier concentration" â is carried by a bar whose x-value has no source, no solubility/cost check, and no sensitivity bound. The Ã2 lever in (G-a) (0.0625 â 0.125 M) is far more defensible but is equally undeclared.

**4. `make_fig_profiles.py` panel (b): "Î´ = 30 Î¼m flow cell" contradicts the flow archetype used in every other figure.**
`run_profiles.jl` hardcodes 30 Î¼m and 10 Î¼m with no registry backing. At D = 1e-9 mÂ² sâ»Â¹ the paper's own `delta_eff` gives **68.1 Î¼m** for the flow archetype (1 mm gap, L 5 cm, u 5 cm sâ»Â¹) and **27.0 Î¼m** for the thin-gap archetype (250 Î¼m gap). So the curve labelled "flow cell" is really the thin-gap archetype, and the curve labelled "thin gap / RCE" is really the RDE/RCE. The annotated **c_surf = 0.69** for the flow cell becomes **0.29** at the archetype's real Î´. The panel's conclusion ("flow survives") holds; the quoted surface concentration does not.

**5. `make_fig_profiles.py` panel (a): the headline claim rests entirely on an unsourced, apparently tuned concentration.**
"the '50 mA cmâ»Â² barrier' IS the stirred-beaker boundary layer" works only because 0.5 M Ã 1 eâ» Ã 1e-9 mÂ² sâ»Â¹ / 100 Î¼m = 48.2 mA cmâ»Â². None of those three inputs has a registry row. Against the paper's own page-verified set, the median substrate-carried row is **0.1 M, n = 2, D = 1.39e-9**, which at Î´ = 100 Î¼m gives **26.9 mA cmâ»Â²** â consistent with the model's published stirred-batch median of 17.4. The barrier therefore sits at ~3Ã the typical stirred-beaker ceiling, not on top of it. This needs either a declared assumption with a sensitivity bound (which values of C_S/n/D make the coincidence hold?) or a rewording.

**6. `make_figM.py`: the ECâ² point lies far to the right of the grey tick the legend calls the substrate cap, with no on-figure flag.**
Clâ»/propylene epoxidation, stirred: ECâ² = 788.9 mA cmâ»Â² against a substrate cap of **1.32 mA cmâ»Â²** â 600Ã. Hofmann stirred: 334.6 vs 154.4. The SI (Â§S5.1) does justify this for the chloride case as ex-cell mediation (97.8% oxidant export, propylene C_sat â 5 mM), but the figure asserts a cap and then plots points 2â3 decades past it. Any reader who has not read Â§S5.1 reads the panel as internally inconsistent.

**7. `make_figFG.py` Fig. F: seven endpoints are clipped off the axes.**
`set_xlim(0.05, 3000)` clips the open circles of *Rh-catalyzed CâH alkenylation* (0.0346) and *CoâH alkene isomerization* (0.0441) at the left edge â their unstirred baselines read as 0.05, ~40% high â and clips the arrowheads of the five rows whose `best` exceeds 3000 (ADN 7056, Cl/propylene 5479, Shono Î±-methoxylation 3645, and two more), so those rows have no visible right endpoint at all. Visible in the rendered PNG.

**8. Provenance-class gaps under otherwise-correct numbers (registry, not script, fixes).**
`delta (stirred batch)` = 100 Î¼m and `delta (unstirred batch)` = 300 Î¼m are both *lit-representative* with chapter-level citations only (Pletcher & Walsh 2nd ed.; Bard & Faulkner ch. 1) â and they set essentially every value in all three figures. `Thin-gap Leveque geometry` (250 Î¼m / 2.5 cm / 10 cm sâ»Â¹) is *lit-representative* citing "Atobe/Noel flow-electrochemistry literature" with **no author, year, or page**, and it sets the green series in Fig. M, the 4th bar in Fig. G, and part of `best` in Fig. F. The generic ECâ² base case (C_med = 20 mM, D_med = 6e-10) driving Fig. J(c) has no registry row at all.

**9. Two of the three figures are unauditable by construction.**
Fig. J and Fig. M are cited nowhere in `make_si.js` or in `SI_Section4_Transport_Model_v3.docx` (referenced figures are C, E, F, G, H, K only) â the same status as `make_fig_mediator_k.py`. Their annotations (problems 2, 4, 5, 6) are therefore invisible to the SI's own consistency checks. Either cite them with the numbers restated in text, or drop them.

**10. Minor:** Fig. F's legend gives counts for green (34/50) and red (14/50) but not orange (2/50), so the bins sum to 48; the stale comment on `make_figFG.py:81` says "10 mM" where the data and the rendered label both say 5 mM; Fig. J panel (a)'s third curve is 38.594 â labelled **"39"**, not "36" as listed in the audit brief.",
      "Both files read in full, all referenced data files loaded, and every computable quantity recomputed. Styling numbers (font sizes, `lw`, `ms`, `alpha`, colours, `set_xlim`/`ylim`, `size_inches`, `dpi`, text x/y placement coordinates, arrow `mutation_scale`, schematic patch geometry in panel a) are excluded throughout and not listed individually â stated once here.

Two structural facts up front:
- **`make_fig_mediator_k.py` reads zero data files.** Every plotted quantity is a closed form plus an 8-row literal table inside the script.
- **`make_fig_carrier.py` reads exactly one data file** (`julia/npp_ecprime_profiles.csv`), consumed only by panel b. Panels a, c and d read nothing.
- Neither `sec4_Fig_carrier` nor `sec4_Fig_mediator_k` is referenced anywhere in `make_si.js` (grep returns nothing). Both scripts also hardcode `sys.path.insert(0,"/home/claude/rce")` / `os.chdir("/home/claude/rce/sec4")`, which does not exist on this machine, so neither is re-runnable as checked out.

---

# 1. `figs/make_fig_carrier.py`

Absolute path: `/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model/figs/make_fig_carrier.py`

Panel a is a pure schematic: symbolic formulas, an `$x_k$` label, the word "dilute", 5 decorative circles. No quantitative content; nothing to trace.

| value | what it controls | source or UNSOURCED | verified? |
|---|---|---|---|
| `F=96485.33` (L17) | all i_lim arithmetic | registry `1. Physical constants / Faraday constant F` = 96485.332, measured-lit CODATA 2018 | YES |
| `julia/npp_ecprime_profiles.csv` cols `x_um, c_ox_norm, c_S_norm` (L18, 58â60) | panel b curves | DERIVED â `julia/run_ecprime.jl` NPP+ECâ² solver | YES, file present, 270 rows, 3 k values |
| `k_M â {1.0, 1000.0}` filter (L58) | which two profiles plot | `k_M` column of that CSV (available: 1, 100, 1000) | YES |
| `"k = 1 M$^{-1}$s$^{-1}$ (slow: commutes)"` (L61) | panel b label | matches `k_M=1.0` | YES |
| `"k = 10^3 M$^{-1}$s$^{-1}$ (fast)"` (L62) | panel b label | matches `k_M=1000.0` | YES |
| `"$x_k\approx$1 Âµm"` (L63) | panel b headline annotation | DERIVED: â(D_med/(kÂ·C_S)) = â(6e-10/(1Â·500)) = **1.095 Âµm**; also SI-stated (`make_si.js` Â§S5.4). But D_med=6e-10 mÂ²/s, C_med=20 mM and C_S=500 mol/mÂ³ are `run_ecprime.jl` constants with **no registry row** | arithmetic YES; **inputs UNSOURCED**; annotation **misdescribes the plotted curve** â see P4 |
| `"$\delta$ = 100 Âµm"` (L65) | panel b condition | registry `7. Reactors / delta (stirred batch)` = 100 Âµm, class *lit-representative* (abolished); matches `run_ecprime.jl const delta = 100e-6` | YES (class problem) |
| `"at 0.9 $i_{lim}$"` (L65) | panel b condition | `run_ecprime.jl` `for frac in 0.1:0.1:0.9` | YES, but the script computes `okall` and **never checks it** â convergence at 0.9Â·i_lim is asserted, not verified |
| `D=6e-6` cmÂ²/s (L71, `icat_mA` default) | panels c **and** d catalyst curves | **UNSOURCED** â no registry row. SI prose cites "3â7Ã10â»â¶ cmÂ² sâ»Â¹ â¦ amide solvents" with no locator. `reactions_50.csv` catalyst rows span 1.73e-6â1.59e-5, **median 8.92e-6** | arithmetic YES; value is below the set's own median â understates the catalyst band |
| `nc=2` (L71) | panels c and d catalyst curves | **UNSOURCED**. `reactions_50.csv` `n_carrier` for the 11 catalyst rows â {0.2, 1.0, 2.0}; only **4 of 11** are 2 | NO â unrepresentative |
| `Ccat=0.010` "10 mM representative" (L73) | panel c both lines | **UNSOURCED**. Catalyst set median C = **5.0 mM**, min 2.6, max 30 | NO â not the median or any registered value |
| `dl=100` (L74) | panel c stirred line | registry stirred Î´ | YES |
| `dl=10` "thin gap" (L74) | panel c thin-gap line | **UNSOURCED**. No archetype in the repo has Î´=10 Âµm. Leveque thin-gap Î´_eff = 24.9â37.6 Âµm, RDE 11.7â15.8, RCE 11.1â12.5 (`mediated_ec_matrix.csv`) | NO |
| printed `i_lim = 1.2` / `12` mA cmâ»Â² (L75â80) | panel c quoted values | computed | YES â recomputed 1.1578 and 11.5782 |
| `"10Ã thinner Î´ â 10Ã i_lim"` (L81) | panel c claim | 1/Î´ scaling | YES |
| `"(3â30 mM)"` (L81, L109) | quoted carrier range | `reactions_50.csv` catalyst C = **2.6â30 mM**; `make_si.js` says "2.6â30 mM" in one paragraph and "2.6â15 mM" in another | partial â lower bound rounded off the true 2.6 |
| `"caps it below 25 mA cm$^{-2}$"` (L81) | panel c conclusion | none | **NO â FALSE.** See P1 |
| `D=1e-5` cmÂ²/s (L88, `isub_mA`) | panel d blue band | **UNSOURCED**. Substrate rows in `reactions_50.csv`: 4.7e-6â2.78e-5, median **1.39e-5** | arithmetic YES; value UNSOURCED |
| `nc=2` (L88) | panel d blue band | **UNSOURCED**. Substrate `n_carrier` â {0.1, 1, 2, 4, 6} | NO |
| `0.02` / `0.5` M (L92) | blue band edges | SI-stated: "modern academic scope rows cluster at 0.02â0.5 M". `reactions_50.csv` substrate C min = 0.02 â, max = **6.85 M** (industrial rows silently excluded) | partial |
| **`1740.0`** (L93), commented "median substrate (~0.1 M-equiv)" | panel d median line | traced: = `tier0_ec_matrix.csv` **all-50** stirred median 17.397 mA cmâ»Â² Ã 100 Âµm = 1739.7 | **NO â MISLABELLED.** See P2 |
| `0.003` / `0.030` M (L95â96) | red catalyst band | as above (2.6â30 mM) | partial |
| `13` / `30` mA cmâ»Â² (L98) | orange mediator plateau band | `mediated_ec_matrix.csv`: ACT-alcohol i_ec 12.80â22.34; HMFâFDCA 12.50â30.42. SI states "13â22 and 13â30" | YES for those two rows â but only 2 of 8 mediated entries. See P3 |
| `22` mA cmâ»Â² (L99) | orange plateau centre line | SI: "the 25 mM ACT mediator plateaus at 22 mA cmâ»Â²"; = ACT-alcohol **maximum** (22.34 at RCE), not a median | arithmetic YES; presented as a plateau centre when it is a band top |
| `25`, `50` mA cmâ»Â² (L100) | threshold lines | registry `7. Reactors / Thresholds 25 / 50 mA cm-2`, measured-lit, Ferretti *OPRD* 2025, 29, 322â332 | YES â the best-sourced numbers in either figure |
| `300` "unstirred" (L104) | reference tick | registry `delta (unstirred batch)` = 300 Âµm, lit-representative | YES (class problem) |
| `100` "stirred" (L104) | reference tick | registry `delta (stirred batch)` | YES (class problem) |
| **`14`** "RDE/RCE" (L104) | reference tick | **UNSOURCED** â no such value exists. RDE Î´ = 11.7â15.8 Âµm, RCE Î´ = 11.1â12.5 Âµm across the 8 mediated solves; 14 is an unstated split-the-difference | NO |
| `"reactor converts 1:1"` (L107) | panel d blue annotation | 1/Î´ scaling; matches `tier0_ec_matrix` substrate rows | YES |
| `"capped low"` (L109) | panel d red annotation | none | **NO â contradicted by the script's own band** (30 mM crosses 25 at Î´=13.9 Âµm and 50 at Î´=6.95 Âµm, both inside the plotted range) |
| `"flat plateau â reactor can't move it"` (L110) | panel d orange annotation | none | **NO â contradicted by `mediated_ec_matrix.csv` for 6 of 8 mediated entries.** See P3 |

---

# 2. `figs/make_fig_mediator_k.py`

Absolute path: `â¦/Section4_Model/figs/make_fig_mediator_k.py`

| value | what it controls | source or UNSOURCED | verified? |
|---|---|---|---|
| `D=1e-5` cmÂ²/s (L15) | x_k of the model curve and band | **UNSOURCED**. Also **internally inconsistent**: back-solving x_kÂ² Â· k Â· C_S for each of the 8 plotted points gives D_ox = 5.5e-6 (SCN), 6e-6 (ACT), 1.4e-5 (Cl), 2.1e-5 (NHPI), 2.2e-5 (Br) cmÂ²/s. The curve and the markers are not the same model | NO |
| `DB = 300.0` (L16) | model, and the Ã30 reference | registry `delta (unstirred batch)` | YES (class problem) |
| `DT = 10.0` (L16) | model denominator, and the Ã30 reference | **UNSOURCED**; no repo archetype is 10 Âµm | NO |
| `I = min(300,x_k)/min(10,x_k)` (L18) | the entire y-axis | closed form, no data file | arithmetic self-consistent; **structurally incomplete** â see P5 |
| `0.5` / `0.02` M band, `0.1` M line (L24â25) | orange band + model line | SI-stated academic cluster; 0.1 M = `reactions_50.csv` substrate median â | YES |
| `DB/DT` â **"full reactor benefit (Ã30)"** (L28â29) | headline blue reference line | none | arithmetic YES; **empirically wrong** â see P6 |
| `1.0` hline "reactor useless" (L30â31) | lower reference | definitional | YES |
| 8 `MED` tuples, k values `0.5, 10, 20, 50, 100, 100, 1000, 1000` (L40â43) | marker x-positions | `make_si.js` Table S6 `k (Mâ»Â¹sâ»Â¹)` column, each with primary-source citations | YES â all 8 match exactly |
| 8 `MED` x_k values `158, 167, 7.7, 10.9, 12.7, 4.7, 2.3, 3.2` Âµm | marker y-positions | `julia/mediated_ec_matrix.csv` `xk_um` (158.209, 167.332, 7.7006, 10.890, 12.721, 4.6904, 2.3452, 3.1623) and Table S6 | YES â all 8 match to the printed precision |
| plotted marker y-values (L45) | the 8 points | recomputed: 15.82, 16.73, 1.00, 1.089, 1.272, 1.00, 1.00, 1.00 | arithmetic YES; **all 8 disagree with the solver.** See P5 |
| `(0.5, 15.8)` + `"reactor helps ~16Ã"` (L47) | NHPI annotation | = 158.2/10 | arithmetic YES; **solver gives Ã4.5 at the thin-gap archetype**, Ã14.1 at RCE |
| `(10, 16.7)` + `"C_S â 5 mM"` (L50) | Clâ»/propylene annotation | 5 mM traces to registry `5. Concentrations / Propylene C_sat (aq, 1 atm)` = 5e-3 M, measured-lit, Sander *ACP* 2015 â the single best-sourced number in this figure | value YES; **but the marker sits above the plotted 0.02â0.5 M band**, because its real C_S is 4Ã below the band floor |
| `"(kâ³20): â¦ plateau, reactor Ã1"` (L54) | grouped label over 6 markers | none | **NO â contradicted for 4 of 6.** See P5 |
| y-ticks `[1,2,5,10,20,30]` | axis | presentational | n/a |

---

# Most serious problems, ranked

**P1 â Panel c of the carrier figure states a false cap, and it is the panel's whole point.**
`"the dilute carrier (3â30 mM) caps it below 25 mA cmâ»Â²"` is refuted by the script's own function three lines later: `icat_mA(10, 0.030) = 34.7 mA cmâ»Â²`, and the panel-d band drawn from the same call crosses 25 at Î´ = 13.9 Âµm and 50 at Î´ = 6.95 Âµm. It is also refuted by the project's own solver: `tier0_ec_matrix.csv` catalyst rows reach **52.58 mA cmâ»Â² at RCE** (the 30 mM Ni homocoupling), clearing both thresholds. The SI is more careful than the figure â it says 10 of 11 catalyst entries clear 25 in no architecture "the single exception runs at 30 mM". The figure deletes the exception and hardens it into a physical cap. This is the one finding that would let a reviewer say a stated conclusion is contradicted by the authors' own table.

**P2 â The `1740.0` "median substrate" line in panel d is the all-carrier median, not the substrate median.**
Traced exactly: 17.397 mA cmâ»Â² (median of all 50 rows of `tier0_ec_matrix.csv` at stirred) Ã 100 Âµm = 1739.7. The substrate-only median is 22.99 Ã 100 = **2299**. The figure draws this line inside the blue *direct/substrate* band and labels it "median substrate (~0.1 M-equiv)", so it is 24% low. The all-50 median is depressed precisely by the 11 dilute-catalyst rows that panel d exists to contrast against â the figure has borrowed the contaminated statistic to represent the clean population. Fix is a one-character change (2299.0) plus a corrected comment; the magic constant should be read from `tier0_ec_matrix.csv` rather than hardcoded.

**P3 â The orange "fast mediator: flat plateau, reactor can't move it" band generalises 2 of 8 entries and is contradicted by the other 6.**
The 13â30 mA cmâ»Â² band and the 22 mA cmâ»Â² line come only from the two ACT/nitroxyl rows (the SI is explicit that these are the two ACT campaigns). The remaining six mediated entries in `mediated_ec_matrix.csv` run from 0.85 to 5479 mA cmâ»Â² and are strongly Î´-dependent. Cleanest counterexample, using two **fully converged** mediator-limited solves so no Newton-wall caveat applies: aryl thiocyanation (k = 100, x_k = 4.7 Âµm â squarely inside the claimed plateau regime) gives i = 17.63 mA cmâ»Â² at Î´ = 100 Âµm and 27.18 at Î´ = 62.7 Âµm, i.e. **i â Î´^â0.93** â essentially 1:1 reactor conversion, the exact opposite of "reactor can't move it".

**P4 â Panel b's "consumed within x_k â 1 Âµm â no reactor makes Î´ that thin" is undercut by the curve it annotates.**
The analytic x_k = 1.095 Âµm is right. But in the plotted `k_M=1000` profile, c_ox at 1 Âµm is still 0.466 (66% of its wall value); 1/e decay is at **2.33 Âµm** and 1% of wall at **10.5 Âµm**. The physically relevant depletion scale is therefore ~10 Âµm â which the repo's own RDE (11.7â15.8 Âµm) and RCE (11.1â12.5 Âµm) archetypes essentially reach. The clause "no reactor makes Î´ that thin" is true against 1 Âµm and false against the scale the curve actually shows, and it carries the panel title "mediated: reactor CANNOT help".

**P5 â Every one of the 8 markers in the mediator figure disagrees with the solver result for the same 8 reactions.** This is the same class of defect as the previously-found "Ã30 is really Ã9.0", but now on the data points rather than the reference line. Toy model vs. `mediated_ec_matrix.csv` (i_ec ratios; thin-gap archetype and RCE shown):

| system | k | figure I | solver, thin-gap/unstirred | solver, RCE/unstirred |
|---|---|---|---|---|
| ACT / alcohol | 20 | 1.00 | 1.44 | 1.75 |
| ACT / HMF | 50 | 1.09 | 1.70 | 2.43 |
| BQ / Wacker | 100 | 1.27 | 4.73 | 7.53 |
| SCNâ» | 100 | 1.00 | **9.91** | **18.47** |
| Brâ» / bromination | 1000 | 1.00 | **8.70** | **20.25** |
| Brâ» / Hofmann | 1000 | 1.00 | (unstirred is a Newton wall; stirredâRCE = 7.66) | â |
| ClâNHPI | 0.5 | 15.82 | 4.52 | 14.10 |
| Clâ» / propylene | 10 | 16.73 | 8.77 | 20.84 |

The grouped label "(k â³ 20): plateau, reactor Ã1" is wrong for 4 of the 6 points it covers, two of them by roughly an order of magnitude. The cause is structural, not calibration: `I_of` models only the commuting/SavÃ©ant mediator bound, but the solver's i_lim for SCNâ», Brâ» and BQ is set by the **substrate total-catalysis cap** FÂ·D_SÂ·C_S/Î´, which is 1/Î´-dependent. The toy model cannot represent the mechanism that actually binds these entries, so no re-tuning of D or DT will fix it â it needs to read `mediated_ec_matrix.csv`.

**P6 â "direct substrate: full reactor benefit (Ã30)" is 300/10 with an unsourced denominator.**
Against `tier0_ec_matrix.csv` substrate rows, the median per-row unstirredâX ratio is **Ã9.94** (thin-gap), Ã23.5 (RDE), Ã26.8 (RCE). So Ã30 exceeds every real archetype, and the figure's named comparator ("thin gap") gives Ã9.9. This corroborates the earlier audit's Ã9.0 from an independent route. Both `DB=300` and the 25/50 thresholds are registry-backed; `DT=10` is the sole unsourced input, and it sets the entire y-axis scale.

**P7 â Unauditable-by-construction (flagging as requested).**
`make_fig_mediator_k.py` reads no file: D, DB, DT, the C_S band, and all 16 numbers of the `MED` table live only in the plotting script. The x_k and k values happen to be correct (I verified all 16 against Table S6 and `mediated_ec_matrix.csv`), but nothing in the pipeline would catch it if they drifted. `make_fig_carrier.py` panels c and d are in the same position: 11 of their ~14 load-bearing numbers exist only in the script.

**P8 â Registry gaps needed to close these two figures.** No row exists for any of: D_cat (generic molecular catalyst, cmÂ² sâ»Â¹); D_sub (generic organic substrate); n_c for either class; C_cat representative; Î´ = 10 Âµm "thin gap"; Î´ = 14 Âµm "RDE/RCE"; and the entire ECâ² base case in `run_ecprime.jl` (D_med = 6e-10 mÂ² sâ»Â¹, C_med = 20 mM, C_S = 0.5 M, C_sup = 100 mM) on which panel b's x_k â 1 Âµm rests. Under the stated standard, D_cat and D_sub are class **C** (assumption + sensitivity bound) since only an unlocated range exists in SI prose; the two Î´ values are class C or should be replaced by the computed archetype Î´ values already in `mediated_ec_matrix.csv`, which are class **B**. Separately, the three registry rows these figures *do* rely on for Î´ (`delta (unstirred batch)` 300 Âµm, `delta (stirred batch)` 100 Âµm) are class *lit-representative* and need reclassifying under the abolition.",
      "## Preliminary notes on method

Neither script is runnable as shipped (`sys.path.insert(0,"/home/claude/rce"); os.chdir("/home/claude/rce/sec4")`, and `make_fig_main.py` reads `reactions_50.csv` from cwd while the repo copy is at `data/reactions_50.csv`). All verification below was done by re-implementing each computation in Python against the actual data files and comparing to the rendered PNG/SVG, not by re-running the generators.

**Styling numbers ignored throughout** (stated once, as instructed): font sizes, `color`/`alpha`/`lw`/`ms`/`mew`, figure `size_inches`/`dpi`/`gridspec` ratios, axis limits and tick lists, text x/y placement coordinates inside schematic axes, arrow `mutation_scale`, jitter array `np.linspace(-0.2,0.2,50)` and index permutation `(i*17)%50`, log-space sampling densities (`np.logspace(...,80)`, `np.linspace(1,300,200)`).

One caveat on `sec4_Fig_sec3`: the rendered SVG/PNG (2026-07-30 20:52) **predate** `make_figs_sec34.py` (21:02). I confirmed the visible surface-current labels still match current code, so the drift appears cosmetic â but the artifact is not guaranteed to correspond to the script.

Also: the author's brief lists the starvation panel currents as "10 / 24 / 36 / 48". The rendered figure and the code both give **10 / 24 / 39 / 48**. The brief is wrong, not the figure.

---

## Generator 1 â `figs/make_fig_main.py` (`sec4_MAIN_composite`)

| value | what it controls | source | verified? |
|---|---|---|---|
| `F=96485.33` | all i_lim / voltage arithmetic | registry `1. Physical constants / Faraday constant F` = 96485.332 | â (7th-digit truncation, irrelevant) |
| `BARRIER=50.0`, `OPER=25.0` | ref lines, colour bins, counts in c/d/f | registry `7. Reactors / Thresholds 25 / 50 mA cm-2`, Ferretti *OPRD* 2025 Fig. 11, page-verified | â |
| a: `"300 Âµm"` unstirred | schematic Î´ label | registry `7. Reactors / delta (unstirred batch)`, class **lit-representative** (abolished); Bard & Faulkner ch. 1 + Amatore 2001, no page | class-invalid |
| a: `"100 Âµm"` stirred | schematic Î´ label | registry `delta (stirred batch)`, class **lit-representative**; Pletcher & Walsh, no page/table | class-invalid |
| a: `"30â60 Âµm"` flow cell | schematic Î´ label | **UNSOURCED** â no registry row, no data file | â **contradicted**: LÃ©veque (h=1 mm, L=5 cm, u=5 cm/s) over the 50 D/Î½ pairs gives Î´ = **38.0â95.8 Âµm, median 74.4**; only 10/50 fall inside 30â60 |
| a: `"<10 Âµm"` thin gap / RCE | schematic Î´ label | **UNSOURCED** | â **contradicted**: thingap Î´ = **15.1â38.0 Âµm (median 29.5), 0/50 below 10**; RCE Î´ = 8.75â14.85 (median 10.9), 13/50 below 10 |
| a: film widths `1.66, 1.4, 0.7, 0.25` | drawn film thickness | schematic proportions only | not to scale (30:1 Î´ range drawn as 6.6:1); file carries the "schematic placeholder" disclaimer |
| b: `"$C_{cat}$ = 3â30 mM"` | carrier-taxonomy annotation | derived from `data/reactions_50.csv` (11 catalyst rows) | â  true range is **2.6â30 mM**; SI Â§S3 itself says "2.6â30 mM". Lower bound silently rounded up and disagrees with the SI |
| c: 9 exemplar names | which rows are plotted | `data/reactions_50.csv` `reaction` column | â all 9 resolve exactly |
| c: label concentrations 0.8 / 6.9 / 1 / 0.47 / 1.56 / 0.18 / 0.03 M; 25 mM; 15 mM | y-tick labels | `reactions_50.csv` `C_carrier_M` (0.81, 6.85, 1.0, 0.47, 1.56, 0.18, 0.029, 0.025, 0.015) | â all round correctly |
| c: plotted `r.natural`, `r.best` | gap-chart segments | `julia/tier0_ec_matrix.csv`; `best = max(thingap, rde, rce)` | â recomputed (e.g. ADN 289.4 â 7056; ACT 12.8 â 22.3, matching SI's "plateau at 22 mA cmâ»Â²") |
| c: `5200` cap + `"â«"` at 6300 | display truncation | presentational | â only ADN (7056) exceeds |
| c: `"50: 1/14 exceed"` | annotation | registry Ferretti row ("n = 14 reporting: 10 < 25; 3 in 25â50; 1 > 50") | â |
| c: `"< 25: 10/14 pharma scale-ups operate here"` | annotation | same row | â (note: describes a 14-process industry survey, drawn over 9 modelled reactions) |
| d: counts `8, 14, 15, 25, 32, 34` | `â¥50` strip labels | computed from `tier0_ec_matrix.csv` | â reproduce exactly; match SI Â§S7 ("13â14, 14â15, 23â25, RDE/RCE 32/50 and 34/50") |
| d: `annotate("50", xy=(1.005, 0.585), xycoords="axes fraction")` | label for the barrier line | hardcoded axes fraction | â **misplaced**: on ylim (0.008, 4000) log, frac 0.585 â **y â 17.3**. y=50 is at 0.666, y=25 at 0.613. Rendered PNG confirms the "50" sits *below* the dotted 25-line |
| e: `delta=100e-6`, `C_med=20.`, `C_S=500.`, `D_med=6e-10`, `D_S=1e-9` | both analytic bounds and the âk curve | `julia/run_ecprime.jl` consts (declared in its header) | â identical. â  but *no registry row*; and the base case is called "ACT-like" while ACT in `reactions_50.csv` / SI is **25 mM**, not 20 mM (panel c of the same figure prints "25 mM") |
| e: `i_sh = 0.1Â·FÂ·D_medÂ·C_med/Î´` = **1.158** | "mediator commuting bound" dashed line | computed; matches `run_ecprime.jl` `i_shuttle` | â recomputed 1.158 mA cmâ»Â² |
| e: `i_cap = 0.1Â·FÂ·D_SÂ·C_S/Î´` = **48.24** | "substrate cap" solid line | computed | â recomputed 48.243, identical to `profiles_direct.csv` `ilim_mAcm2` for Î´=100 Âµm |
| e: `0.1Â·FÂ·C_medÂ·â(D_medÂ·(k/1000)Â·C_S)` | dotted SavÃ©ant ââk curve | closed form | â matches `npp_ecprime_sweep.csv` `saveant_mAcm2` exactly (k=1 â 3.3423) |
| e: `val = sw[sw.k_M <= 1e3]` | which solver points are drawn | `julia/npp_ecprime_sweep.csv` | â **silently drops k = 3e3, 1e4, 1e5** â including k=3e3 (41.86â**46.38**, the sweep maximum) |
| e: `e.plot([3e3,1e4,1e5], [i_cap]*3, "s")` | three white squares | **hardcoded, not read** | â **contradicts the data file**: the solver gives **46.38, 29.26, 19.28**; the figure draws them at **48.24**. Errors of +4%, **+65%**, **+150%**, and the sign of the trend is reversed (data is non-monotone and falls; figure shows clean saturation) |
| f: `Îº = 0.06, 0.35, 0.90, 20.0` S/m | five voltage curves | `julia/cellvoltage.jl` `ELECS`; `data/electrolytes.csv` (0.6/3.5/9.0/200 mS cmâ»Â¹); registry cat. 6, class **lit-representative** ("Izutsu â¦ class data", no page/table) | values â, provenance class invalid |
| f: gaps `5e-3, 2.5e-4, 1e-3` m | ohmic term | `cellvoltage.jl` `GAPS` | â present; the gapâelectrolyte *pairings* (e.g. "DMF, 250 Âµm") are the script's choice |
| f: `E0 = 2.0` V | curve intercept | registry `8. Voltage stack / E0`, class **assumption**, no external source | declared, no sensitivity bound in registry |
| f: `2*(2Â·RT/F)Â·asinh(i/2)` | kinetic overpotential | registry `Tafel b = 2RT/F` (0.0514 V) and `i0 = 1.0 mA cm-2`, both **assumption**; `asinh(i/2)` = `asinh(i/2i0)` with i0=1 | â formula matches `cellvoltage.jl`; script uses R=8.314 vs registry 8.314463 (â0.006%, negligible) |
| f: whole curve family | plotted voltages | recomputed against `julia/cellvoltage.csv` at i = 10/25/50/100/300 for all five combos | â **agreement to 1e-4 V on all 25 points** (but the script re-implements the physics rather than reading the CSV) |
| f: `axhspan(10, 20)` "academic non-aqueous cells" | shaded band | **UNSOURCED**. SI Â§S6 makes the same claim ("reproducing the 10â20 V cells common in academic non-aqueous reports") but *derives it from this same model* (DMF/5 mm at 100 mA cmâ»Â² â 16.8 V). No external survey cited | circular |

---

## Generator 2 â `figs/make_figs_sec34.py` (`sec4_Fig_sec3`, `sec4_Fig_ceiling`)

| value | what it controls | source | verified? |
|---|---|---|---|
| `BARRIER=50.0`, `OPER=25.0` | ref lines in b, d | registry Ferretti row | â |
| schematic `300 / 100 / 30â60 / <10 Âµm` | panel-a Î´ labels | same as above | â same two failures as `make_fig_main` panel a â **and this file drops the "schematic placeholder" disclaimer**, so the non-proportional drawing and the wrong Î´ ranges read as model output |
| ladder `C = 1740.0` | the entire `i_lim = C/Î´` curve | **UNREGISTERED**, but reproducible: it is the 50-reaction median of `0.1Â·nÂ·FÂ·DÂ·C` in mA cmâ»Â²Â·Âµm (= stirred median 17.40 Ã 100 Âµm) | arithmetic â; provenance = derived-but-hardcoded |
| ladder TIERS `(100,500) (10,100) (1,10) (0.3,1)` | four shaded bands + "Tier 1â¦4, Î´ â¦Âµm" labels | **UNSOURCED** â no registry row, no data file, no SI text | â and the names **collide with the SI's own Tier 0 / Tier 1 model-tier nomenclature**, which means something completely different (Tier 0 = Nernst-film analytic, Tier 1 = NPP solver) |
| ladder anchor `(300, 6.1)` | "unstirred" dot | median of `tier0_ec_matrix.csv` `natural` = **6.062**; quoted in SI Â§S3 as 6.1 | value â; but it does **not** lie on the plotted curve (1740/300 = 5.80, â5.2%) |
| ladder anchor `(100, 17.4)` | "stirred" dot | median `stirred` = **17.40** | â (on-curve by construction) |
| ladder anchor `(14, 127)` | "RDE / RCE" dot | 127 = median `rce` = **127.4** â | **Î´ = 14 Âµm is UNSOURCED** and contradicts the model's own correlations: RDE median Î´ = 12.65 Âµm, RCE median Î´ = 10.94 Âµm. Also off-curve (1740/14 = 124.3) |
| ladder dashed extrapolation to Î´ = 0.3 Âµm | implies i_lim â 5800 mA cmâ»Â² | extrapolation of the fitted C | â **no archetype in the model reaches Tier 3 or Tier 4**; global minimum Î´ across all 6 archetypes Ã 50 reactions is **8.46 Âµm** |
| ladder `25 (ETC median)` / `50 (barrier)` | red dotted lines | registry Ferretti row | â |
| starvation `0.5 M substrate, 1 eâ», D = 10â»â¹ mÂ² sâ»Â¹` | quoted conditions box | `julia/run_profiles.jl` header consts (`C_S=500.0`, `D_S=1.0e-9`) | declared in code; **no registry row** for either the generic 0.5 M substrate or the generic D |
| starvation `Î´ = 100 Âµm` | quoted condition | registry `delta (stirred batch)` (lit-representative) | class-invalid |
| starvation `i_lim = 48 mA cmâ»Â²` | annotation + last curve label | `profiles_direct.csv` `ilim_mAcm2` = 48.243 | â recomputed nFDC/Î´ = 48.243 |
| starvation curve labels `10, 24, 39, 48` | four line labels | `profiles_direct.csv` fan currents 9.649 / 24.121 / 38.594 / 48.001 (fractions 0.2/0.5/0.8/0.995 of i_lim) | â exact. Minor: the "48 = i_lim" curve is at 48.001, i.e. 99.5% of i_lim, and 45.831 (frac 0.95) is skipped |
| starvation surface concentrations (implied 0.80/0.50/0.20/0.005) | curve intercepts via `with_surface` | linear extrapolation of the NPP grid | â extrapolated values reproduce `1 â i/i_lim` to 4 decimals |
| barrier `50 mA cmâ»Â²` for all four cases | panel-a(ceiling) currents | `profiles_direct.csv` `i_mAcm2` | â flow/thingap at 50.0; stirred/unstirred at 48.001/16.000 (their own 0.995Â·i_lim) â the caption's "dashed: at their own i_lim" is honest |
| barrier `Î´ = 10 Âµm thin gap/RCE`, `Î´ = 30 Âµm flow` | quoted Î´ in the four legend lines | `profiles_direct.csv` `delta_um`, hardcoded in `run_profiles.jl` line 65 | â **inconsistent with `correlations.jl`**, used for the scatter panel immediately below: flow Î´ = 38â96 Âµm, thingap Î´ = 15â38 Âµm. The same figure asserts two different Î´ for the same architecture |
| barrier `c_surf = 0.90` (thin gap) | quoted value | derived | â recomputed 0.8964 = 1 â 50/482.427 |
| barrier `c_surf = 0.69` (flow) | quoted value | derived | â recomputed 0.6891 = 1 â 50/160.809 |
| barrier `i_lim = 48` (stirred), `i_lim = 16` (unstirred) | quoted values | `profiles_direct.csv` | â 48.243 and 16.081 |
| barrier `300.0` bulk-extension point | draws the flat bulk to the axis edge | plotting device | â harmless |
| scatter counts `8/50 â¦ 34/50` | `nab` labels | computed from `tier0_ec_matrix.csv` | â 8, 14, 15, 25, 32, 34 â reproduce exactly and match SI Â§S7 |
| scatter `annotate("50 (barrier)")`, `annotate("25")` at `xy=(5.62, BARRIER)` / `(5.62, OPER)` | ref-line labels | data coordinates | â **correctly placed here** â this is the fixed version of the `make_fig_main` panel-d bug |
| scatter `axhspan(0.011, 0.030)`, text at 0.0182 | summary strip background | cosmetic | â |

---

## Most serious problems, ranked

**1. `make_fig_main.py` panel e plots three fabricated points on top of the substrate cap.** `e.plot([3e3,1e4,1e5],[i_cap]*3,"s")` draws markers at 48.24 mA cmâ»Â² for k = 3Ã10Â³, 10â´, 10âµ, while `julia/npp_ecprime_sweep.csv` reports **46.38, 29.26, 19.28** for exactly those k. Simultaneously `val=sw[sw.k_M<=1e3]` deletes the solver's own maximum (k=3000, 46.38) from the plotted line. The figure therefore shows monotone saturation at the direct-electrolysis ceiling; the model shows a peak followed by a 60% collapse. This is the same failure mode as the "Ã30 that is really Ã9.0" in `make_fig_mediator_k.py`, and it is worse because it directly supports the panel's stated conclusion ("fast mediator kinetics substitute for convection"). *Affects the mediator/ECâ² argument in both main text and SI Â§S5.*

**2. The Î´ ladder for flow and thin-gap contradicts the model's own mass-transfer correlations, in both generators.** "flow cell 1 mm gap: Î´ â 30â60 Âµm" vs. LÃ©veque's **38â96 Âµm (median 74)**, and "thin gap / RCE: Î´ < 10 Âµm" vs. thingap **15â38 Âµm with 0/50 below 10 Âµm**. The same 30 Âµm / 10 Âµm assumption is hardcoded in `run_profiles.jl`, so the `Fig_ceiling` panel-a legend inherits it â and sits directly above a scatter panel built from the correct correlations. No registry row supports either range. *Affects the SI Â§S2 architecture ladder and the main-text "engineering convection thins Î´" claim.*

**3. `make_fig_main.py` panel d labels the wrong line.** `annotate("50", xy=(1.005, 0.585), xycoords="axes fraction")` renders at y â 17.3 on the log axis (y=50 is at 0.666). Confirmed in the rendered PNG: the "50" caption sits below the dotted 25 line. A reader reads the 25-line as the 50 mA cmâ»Â² barrier â inverting the panel's headline result. Purely a coordinate bug; `make_figs_sec34.py` already has the corrected version.

**4. The Tier 1â4 Î´ bands are invented and collide with existing nomenclature.** `(100,500) (10,100) (1,10) (0.3,1) Âµm` appear in no registry row, no data file and no SI text, yet they are drawn as bold labelled bands and the i_lim line is extrapolated into Tiers 3â4 up to ~5800 mA cmâ»Â², a regime **no archetype in the model reaches** (global min Î´ = 8.46 Âµm). The SI already uses "Tier 0 / Tier 1" for *model* tiers, so the figure's taxonomy is both unsourced and ambiguous.

**5. `C = 1740` and the RDE/RCE anchor at Î´ = 14 Âµm exist only in the plotting script.** 1740 is recoverable (median nFDC = stirred median Ã 100 Âµm) but is nowhere in the registry; Î´ = 14 Âµm is not recoverable from anything and disagrees with the model's RDE (12.65) and RCE (10.94) medians. Consequence: the anchors do not lie on their own curve (unstirred off by +5.2%), and because Î´ correlates with D across the corpus, the single power law overstates the RCE median by ~25% (1740/10.94 = 159 vs. the actual 127). *Affects the SI Â§S3 median-ladder narrative.*

**6. Class-invalid provenance on every reactor and conductivity input.** `delta (unstirred batch)` 300 Âµm, `delta (stirred batch)` 100 Âµm and all five panel-f conductivities are registry rows of class **lit-representative** â the abolished class â with citations that carry no page or table locator (Bard & Faulkner "ch. 1", Pletcher & Walsh, "Izutsu â¦ class data"). Under the stated standard these must become A (with locator) or C (declared assumption + sensitivity bound).

**7. The 10â20 V "academic non-aqueous cells" band is circular.** SI Â§S6 asserts it, but derives it from this very voltage stack (DMF/5 mm at 100 mA cmâ»Â² â 16.8 V). No external survey is cited. It should either carry a literature survey or be redrawn as a model output, not a validation target.

**8. Two internal inconsistencies of the same quantity within one figure.** (a) Panel e's ECâ² base case is 20 mM mediator while panel c of the same composite prints "ACT-mediated alcohol ox. [med. 25 mM]", and `reactions_50.csv`/SI both say 25 mM. (b) Panel b's "C_cat = 3â30 mM" against the data's and the SI's 2.6â30 mM.

**9. Unauditable-by-construction inventory.** Numbers that exist *only* inside these plotting scripts, with no registry row and no data file: the four schematic Î´ labels, `C_cat = 3â30 mM`, `C = 1740`, the four Tier boundaries, the Î´ = 14 Âµm anchor, the three panel-e cap squares, the 10â20 V band, and the five ÎºÃgap pairings in panel f. Panel f additionally *re-implements* `cellvoltage.jl` rather than reading `cellvoltage.csv` â it agrees to 1e-4 V today, but nothing enforces that.

**10. Housekeeping that undermines reproducibility.** Neither generator runs outside `/home/claude/rce`; `make_fig_main.py` reads `reactions_50.csv` from a path that does not exist in the repo layout; `data/build_reactions50.py` (2026-07-13) is newer than the `reactions_50.csv` / `reactions_table.jl` it produces (2026-07-12); and `sec4_Fig_sec3.svg/png` predate `make_figs_sec34.py`.

**Verified clean** (worth stating, since it is most of the load-bearing content): every value read from `tier0_ec_matrix.csv`, `profiles_direct.csv`, `npp_ecprime_sweep.csv` and `cellvoltage.csv` reproduces to the printed precision â the six `â¥50` counts (8/14/15/25/32/34), the six medians, all nine exemplar concentrations and gap segments, the four starvation currents and their surface concentrations, `c_surf` = 0.90 and 0.69, i_lim = 48 and 16, the SavÃ©ant âk curve, the shuttle bound and the substrate cap, and all 25 cell-voltage points.",
      "## Preamble

Pure styling numbers â font sizes, colours, linewidths, marker sizes, alphas, zorders, axis limits/ticks, figure dimensions, schematic rectangle coordinates, jitter offsets â are excluded throughout and not listed again.

Two notes on state: **`figs/make_figK.py` was edited by the concurrent remediation workflow during this audit** (mtime moved 2026-08-01 23:21 â 2026-08-02 00:10). Both versions were read; the tables below audit the **current** version, and where the remediation fixed something I had independently found, I say so. `make_si.js` (00:12) is already in sync with the new figK.

Absolute paths: generators in `â¦/Section4_Model/figs/`, registry at `â¦/Section4_Model/data/parameters_provenance.csv`, model outputs in `â¦/Section4_Model/julia/` and `â¦/Section4_Model/results/`.

---

## 1. `figs/make_fig4A.py`

Reads `reactions_50.csv`, `julia/tier0_ec_matrix.csv`, `julia/profiles_direct.csv`.

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `BARRIER=50.0` | panel c/d reference line, panel d counts, panel c annotation text | registry `Thresholds 25 / 50 mA cm-2`, measured-lit, Ferretti *OPRD* 2025 Fig. 11, page-verified | **YES** |
| `OPER=25.0` | panel d dotted line | same registry row | **YES** |
| `300 Âµm` (unstirred) | panel a ladder label | registry `delta (unstirred batch)` = 300 Âµm (lit-representative; method_note says plateau is 250â500) | **YES** to registry |
| `100 Âµm` (stirred) | panel a ladder label | registry `delta (stirred batch)` = 100 Âµm (lit-representative) | **YES** |
| `"30â60 Âµm"` for "flow cell 1 mm gap" | panel a ladder label | **UNSOURCED, and contradicted by the model.** Back-solving `tier0_ec_matrix.csv` over the 31 substrate rows gives flow Î´ = **52.9â95.8 Âµm, median 76.1** | **NO â off by ~2.5Ã** |
| `"<10 Âµm"` for "thin gap / RCE" | panel a ladder label | **UNSOURCED, and contradicted.** Model Î´: thingap 21.0â38.0 (median 30.2), RDE 10.2â15.0, RCE 9.4â12.3. No architecture in the model is <10 Âµm | **NO** |
| `ivals[0],[1],[2],[4]` â labels `10 / 24 / 39 / 48` | panel b curve set | `julia/profiles_direct.csv`, `case=="fan"`, col `i_mAcm2` = 9.649 / 24.121 / 38.594 / 48.001 (`ivals[3]`=45.831 deliberately skipped) | **YES** (note: the brief lists "36"; the rendered SVG says **39**) |
| `"= $i_{lim}$"` tag on top curve | panel b | curve is i = 48.001; file `ilim_mAcm2` = 48.243 | **MARGINAL** â labelled as *i*_lim but is 0.995 *i*_lim |
| `"i_lim = 48 mA cm-2"` | panel b annotation | `profiles_direct.csv` `ilim_mAcm2` = 48.243 | **YES** |
| `0.5 M substrate, 1 eâ», D = 1e-9 mÂ² sâ»Â¹, Î´ = 100 Âµm` | panel b inset text | Worked-example inputs. **No registry row** for D = 1e-9 or C = 0.5 M as a named parameter. But arithmetic closes exactly: 1 Ã 96485 Ã 1e-9 Ã 500 / 1e-4 = 482.4 A mâ»Â² = **48.24 mA cmâ»Â²** = the file's `ilim` | **derivation YES / inputs UNSOURCED** |
| `c_surf = 0.90` (thin gap/RCE) | panel c annotation | computed `1 â i/i_lim` = 1 â 50/482.427 = **0.8964** | **YES** (arithmetic) |
| `c_surf = 0.69` (flow cell) | panel c annotation | computed = 1 â 50/160.809 = **0.6891** | **YES arithmetically, WRONG physically** â at the model's own flow Î´ = 76.1 Âµm, *i*_lim = 63.4 and **c_surf = 0.21** |
| `i_lim = 48` (stirred, starved) | panel c annotation | `profiles_direct` stirred `ilim` = 48.243 | **YES** |
| `i_lim = 16` (unstirred, starved) | panel c annotation | `profiles_direct` unstirred `ilim` = 16.081 | **YES** |
| `Î´ = 10 / 30 / 100 / 300 Âµm` | panel c legend lines | `profiles_direct.csv` `delta_um` | **YES to file**; the file's "flow"/"thingap" Î´ are not the model's flow/thingap Î´ (see above) |
| `8, 14, 15, 25, 32, 34` | panel d "â¥50:" counts | computed live from `julia/tier0_ec_matrix.csv` | **YES â reproduced exactly** |
| `xy=(1.005, 0.585)` for the text `"50"` | panel d axis label for the barrier line | the 50 line sits at axes-fraction **0.6661**, the 25 line at 0.6132; 0.585 corresponds to *y* â **17.3** | **NO â the "50" label floats below both reference lines** |
| Panel (a) schematic geometry | rectangles, arrows, film widths | in-script only; explicitly captioned *"schematic placeholder â final art in Illustrator"* | declared, acceptable |

---

## 2. `figs/make_fig4B.py`

Reads **only** `julia/npp_ecprime_profiles.csv`. **Five of its six panels read no data at all.**

### Fig 4B-ac

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `i_lim â n C_sub D/Î´`, `â C_med â(kC_sub D)`, `â n C_cat D_cat/Î´` | panel a formula text | analytic (SavÃ©ant ECâ² scaling); consistent with `run_ecprime.jl` line 69 | **YES** |
| `"C_cat = 3â30 mM"` | panel a schematic text | `data/reactions_50.csv`, 11 catalyst rows: actual range **2.6 â 30.0 mM** | **YES** (low edge rounded 2.6â3) |
| `k = 1.0` and `k = 1000.0` Mâ»Â¹sâ»Â¹ curves | panel b plotted profiles | `julia/npp_ecprime_profiles.csv`, cols `c_ox_norm`, `c_S_norm` | **YES** |
| `"x_k â 1 Âµm"` | panel b annotation | `julia/npp_ecprime_sweep.csv`, col `xk_um` at k=1000 = **1.0954**. Cross-checked: â(6e-10 / (1 Ã 500)) = 1.095 Âµm | **YES** |
| `"Î´ = 100 Âµm, at 0.9 i_lim"` | panel b inset text | `julia/run_ecprime.jl` L9 `delta = 100e-6`, L84 comment "profiles at 0.9 i_lim" | **YES** |
| `"substrate dips too (total catalysis)"` | panel b annotation | data: `c_S_norm` min = **0.237** at k=1000 vs 0.961 at k=1 | **YES** |
| `mu = 0.041` | panel c mediated plateau level + legend title | in-script. Comment cites "ACT 25 mM/0.5 M (D ratio 0.82)". C-ratio 0.025/0.5 = 0.05 â from `reactions_50.csv`; 0.05 Ã 0.82 = 0.041 â. **But the D ratio 0.82 is nowhere**: `reactions_50.csv` stores only the *carrier* diffusivity, no substrate D column | **arithmetic YES / input UNSOURCED** |
| `eps = 0.060` | panel c dilute-catalyst line | same: 0.005/0.05 = 0.10 â; Ã 0.6 = 0.060 â; **D ratio 0.6 unsourced** | **arithmetic YES / input UNSOURCED** |
| `sl = 1, 10, 100` (Î´_batch/x_k) | panel c three mediated curves | in-script illustrative ladder | **UNSOURCED** |
| bands `(2.5,3.5)` stirred, `(5,15)` flow, `(30,100)` thin gap | panel c architecture bands | xÌ = 300/Î´: stirred 100â3.0 â; flow 30â60â5â10 (band runs to 15 = 20 Âµm); thin gap <10â>30 â | **partly** â flow upper edge exceeds the ladder |
| `x = logspace(0, log10(300))` | panel c x-range | Î´_batch/Î´_min = 300/1 | in-script |

### Fig 4B-def â **entirely hardcoded, zero data reads**

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `F = 96485.33` | RT/F | registry `Faraday constant F`, CODATA 2018 | **YES** |
| `RT_F = 8.314Â·298.15/F` = 0.025691 | Tafel slope | registry `Gas constant R`, `Temperature T = 298.15 K` | **YES** (2b = 0.10276 â registry `Tafel b` 0.0514 Ã2) |
| `2.0` V (Eâ) | panel d intercept | registry `E0 (thermodynamic + kinetic floor)` = 2.0 V, **class: assumption**, no citation | declared assumption, **no sensitivity bound** |
| `i0 = 1.0` mA cmâ»Â² | asinh(i/2) in panels d, e, f | registry `i0 (exchange current density)` = 1.0, **assumption**, "illustrative" | declared assumption |
| `Îº = 0.06` S mâ»Â¹ ("0.1 M BuâNPFâ / THF") | panels d, e, f | **NO REGISTRY ROW.** figK's own header names this as unregistered | **UNSOURCED** |
| `Îº = 0.35` S mâ»Â¹ ("0.1 M BuâNBFâ / DMF") Ã2 | panels d, e, f | **NO REGISTRY ROW** (figK header names it) | **UNSOURCED** |
| `Îº = 0.90` S mâ»Â¹ ("0.1 M BuâNBFâ / MeCN") | panels d, e, f | registry `0.1 M Bu4NBF4/MeCN` = 9.0 mS cmâ»Â¹ = 0.90 S mâ»Â¹, lit-representative | **YES** (class abolished) |
| `Îº = 20.0` S mâ»Â¹ ("1 M KOH aq") | panels d, e, f | **NO REGISTRY ROW.** Nearest is `1 M NaOH aq` = 180 mS cmâ»Â¹ = 18.0 S mâ»Â¹ | **UNSOURCED** |
| gaps `5e-3, 5e-3, 5e-3, 2.5e-4, 1e-3` m | panels d, e, f | matches `julia/cellvoltage.csv` archetypes "batch, 5 mm" / "thin gap, 250 um" / "flow, 1 mm"; **but the 5 mm rows are labelled "5 mm" cells, and figK's header argues 5 mm is wrong for a beaker (2 cm is)** | **partly** |
| `T_b = 66, 153, 82, 153, 100` Â°C | panels e, f dotted lines and boil points | registry `THF: Tb` 66, `DMF: Tb` 153, `MeCN: Tb` 82, `aq. KOH: Tb` 100 â all measured-lit, CRC 97th ed. | **YES** |
| `axhspan(10,20)` "academic non-aqueous cells" | panel d grey band | **NO REGISTRY ROW.** Only registry hit for "10-20" is the PEM cold-plate *temperature* gradient, unrelated | **UNSOURCED** |
| `COOL = 0.020 / 0.18 / 0.30` W cmâ»Â² Kâ»Â¹ | panel f three markers per row | registry `UA still air` 0.20 W Kâ»Â¹ / 10 cmÂ² = 0.020 â; `U' stirred bath` 0.18 â; `U' PEM-class` 0.30 â | **YES to registry** â but see #2 below |
| `TAMB = 25.0` Â°C | panels e, f | registry `Temperature T = 298.15 K`, assumption | **YES** |
| `"UA = 0.2 W K-1, incl. radiation"` | panel e inset text | registry `UA still air (incl. radiation)` = 0.20, derived | **YES to registry, superseded by figK** (figK now computes 0.0144 W cmâ»Â² Kâ»Â¹, i.e. UA = 0.144 W Kâ»Â¹, and states in its docstring that 0.02 "does NOT recover" the geometry) |
| `"boils at {ib:.0f}"` Ã3 | panel e annotations | recomputed: THF **31**, DMF **132**, MeCN **139** (250 Âµm 555 and KOH 1153 fall off-panel) | **YES to this script's own model**; contradicts figK (29 / 85 / 84) |
| panel f markers | boil-off vs cooling | recomputed: THF 31/94/121; DMF 132/399/516; MeCN 139/424/549; DMF-250Âµm 555/1743/2264; KOH 1153/4405/5875 | reproduces |
| `axvline(25)` label `"25"`, `axvline(50)` label `"50 (the barrier)"` | panel f reference lines | registry `Thresholds 25 / 50`, Ferretti *OPRD* 2025 | **YES** |

---

## 3. `figs/make_figs.py`

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `THRESH = 25.0` | FIG A line, FIG B count, FIG C Ã-marks and column counts, FIG D vline | registry `Thresholds 25 / 50` | **YES** |
| `F = 96485.33` | FIG A/B *i*_lim, FIG D | registry `Faraday constant F` | **YES** |
| `il = 0.1Â·nÂ·FÂ·DÂ·C/Î´` (FIG A curves) | 7 plotted curves | `data/reactions_50.csv` cols `n_carrier`, `D_cm2s`, `C_carrier_M`. Unit chain verified (A mâ»Â² â mA cmâ»Â²). Cross-check: Kolbe at Î´=300 Âµm gives **89.48**, exactly `tier0_ec_matrix.natural` = 89.48 | **YES for substrate rows** |
| â same formula for mediator/catalyst rows | FIG A dashed curves | **model mismatch:** ACT-mediated at Î´=300 Âµm gives **0.48** here vs `tier0` `natural` = **12.80** (26Ã); Ni-XEC 0.50 vs 0.50 â at natural but 1.96 vs 2.73 at flow. FIG A's dashed curves and FIG B/C's points for the same reactions are two different models on identically-labelled axes | **NO â internally inconsistent** |
| `Î´ = logspace(5e-6, 500e-6)` | FIG A x-range | spans the registry reactor set | fine |
| labels `0.8 M / 1 M / 6.9 M / 0.47 M / 0.18 M / 15 mM / 25 mM` | FIG A legend | `reactions_50.csv` `C_carrier_M` = 0.81, 1.0, 6.85, 0.47, 0.18, 0.015, 0.025 | **YES â all seven check out** |
| bands `(200,400)` unstirred, `(70,140)` stirred, `(20,60)` flow, `(6,15)` RDE/RCE/thin gap | FIG A shaded bands | registry gives point values 300 and 100 (plateau note 250â500). **Band edges match neither**; flow/thin-gap edges match the ladder in Fig4A-a, which is itself wrong vs the model (flow 53â96, thingap 21â38) | **NO** |
| `nb` = 28 â `"28/50 below threshold"` | FIG B annotation | computed from `tier0_ec_matrix.flow` | **YES â reproduced** |
| guide line `n=2, D=8e-10 mÂ² sâ»Â¹, Î´=5.0e-5 m` | FIG B grey slope guide | **UNSOURCED.** Also contains dead code: the first term is multiplied by `0` | **UNSOURCED** |
| `vmin=-1, vmax=3.2` | FIG C colour scale | styling | n/a |
| `11/50, 17/50, 22/50, 31/50, 36/50, 36/50` (as `50ânbel`) | FIG C column headers "â¥25" | computed from `tier0_ec_matrix.csv` | **YES â reproduced exactly** |
| labels `"flow 1 mm"`, `"thin gap 250 Âµm"`, `"RDE 1600 rpm"`, `"RCE 3000 rpm"` | FIG C x-tick labels | registry `Leveque â¦ gap 1 mm`, `Thin-gap Leveque geometry gap 250 um`, `Levich â¦ 1600 rpm`, `Eisenberg RCE â¦ 3000 rpm` | **YES** |
| `cv = pd.read_csv("julia/cellvoltage.csv")` | â | **dead read: `cv` is never referenced again.** FIG D re-implements the voltage stack in Python | Python reimplementation **does** match `cellvoltage.csv` to <1e-3 V (THF/5 mm @25 mA: 23.164 both) |
| `scen` Îº = `0.06, 0.35, 0.90, 0.35, 20.0` S mâ»Â¹ | FIG D both panels | same as Fig4B: **three of five have no registry row** | **UNSOURCED** |
| `2.0` V, `2Â·(2RT/F)`, `arcsinh(ii/2)` | FIG D left panel | registry `E0` (assumption), `Tafel b` (assumption), `i0` (assumption) | declared assumptions |
| `axhspan(10,20)` "reported academic non-aqueous cells" | FIG D left band | **NO REGISTRY ROW** | **UNSOURCED** |
| `axhspan(0.005, 0.02)` "passive air" | FIG D right band | **UNIT ERROR.** These are the registry's *Uâ²* values (W cmâ»Â² Kâ»Â¹) drawn on a **heat-flux** (W cmâ»Â²) axis | **NO** |
| `axhspan(0.05, 0.2)` "stirred liquid" | FIG D right band | same: registry `U' stirred bath` = 0.18 **W cmâ»Â² Kâ»Â¹** | **NO** |
| `axhspan(1, 10)` "engineered cooling (PEM-class plates)" | FIG D right band | registry `U' PEM-class` method_note "2â6 W cmâ»Â² rejected" â this one *is* a genuine flux | **YES** (so the panel mixes two quantities on one axis) |
| `Q = (iÂ·10)Â²Â·g/ÎºÂ·1e-4` | FIG D right curves | ohmic-only Joule flux; matches `cellvoltage.csv` col `Q_W_cm2` (THF beaker @10 mA: 0.3333 both) | **YES** |
| `axhline(2.0)` "binary-electrolyte limit (2.00)" | FIG E left | `npp_support_sweep.csv` at support_ratio 0 = **2.0000000000000013**; theory (Bard & Faulkner) | **YES** |
| `phi_mV/50` | FIG E right dashed scaling | in-script display scaling, stated in the axis label | acceptable |
| `julia/npp_support_sweep.csv`, `julia/npp_profiles.csv` | FIG E inputs | **FILES DO NOT EXIST** at that path â they are in `results/` | **script crashes at L128** |

---

## 4. `figs/make_figK.py` (current, post-remediation)

**No data reads at all** â every input is a literal. The script now self-declares this in a `PROVENANCE GAPS` block.

| Value | What it controls | Source | Verified? |
|---|---|---|---|
| `RT_F = 0.025693`, `b = 2RT/F` | Tafel term in q(i), all three panels | registry `Tafel b` = 0.0514 V (assumption). Note this is hardcoded here but computed as `8.314Â·298.15/F` = 0.025691 in 4B/figs â a 7e-5 relative drift | declared assumption |
| `i0 = 1.0` mA cmâ»Â² | q(i) | registry `i0`, assumption | declared assumption |
| `TAMB = 25.0` Â°C | all panels | registry `Temperature T` | **YES** |
| `H_EXT = 13.0` W mâ»Â² Kâ»Â¹ | U_passive, all panels | registry has `h natural convection (air)` = 7 (lit-representative) and `h radiation (linearized)` = 6â8 (derived) **separately, never their sum**. Script flags this | **derivable (7+6), no registry row** â self-flagged |
| `SIGMA_BEAKER = 0.0125/1.0e-3 = 12.5` | panels a, b beaker columns | registry `Vessel external area` = 0.0125 mÂ² (derived, ~5 cm Ã 8 cm cylinder) / 10 cmÂ² | **YES â now genuinely registry-derived** (was 15.0 reverse-fitted 40 min earlier; **remediated during this audit**) |
| `Ï = 10 / 7 / 0.8` (flow / microfluidic / PEM stack) | panels b, c passive availability | **UNSOURCED** â script flags | **UNSOURCED, self-flagged** |
| `h_int = 100 / 800 / 2000 / 5000 / 5000` | U_passive | **UNSOURCED** â script flags | **UNSOURCED, self-flagged** |
| gaps `2 cm / 2 cm / 5 mm / 250 Âµm / 100 Âµm` | q(i) ohmic term | 2 cm, 5 mm, 250 Âµm match `cellvoltage.csv` archetypes; 100 Âµm has no archetype. Script flags all | **partly, self-flagged** |
| `i_design = 50 / 50 / 100 / 500 / 1000` | panel a vline, panel c operating point, panel b margins | **UNSOURCED** except 50 (registry threshold row) | **UNSOURCED, self-flagged** |
| Îº `0.30 / 1.80 / 0.80 / 18.00` S mâ»Â¹ | all panels | registry: `3.0 M LiBr/THF` 3.0 mS cmâ»Â¹ **measured-lit** (Peters *Science* 2019 SM pp. S15, S21) â; `0.25 M Bu4NBF4/MeCN` 18.0 lit-rep â; `0.2 M NaI/DMF` 8.0 lit-rep â; `1 M NaOH aq` 180.0 **measured-lit** CRC â | **YES â all four have rows** (two still class-abolished) |
| T_b `66 / 82 / 153 / 100` Â°C | panels a, b | registry `THF: Tb`, `MeCN: Tb`, `DMF: Tb`, `aq. KOH: Tb`, all measured-lit CRC 97th | **YES** (the 100 Â°C row is registered under *KOH*, script uses *NaOH*) |
| `U' = 0.014` in panel a inset | rendered text | recomputed `U_passive(12.5,100)` = **0.014381** | **YES** |
| `"THF boils at 29"`, `"MeCN â¦ 84"`, `"DMF â¦ 85"` | panel a annotations | independently recomputed: **29.48 / 83.87 / 84.90**. SVG on disk shows 29/84/85 | **YES â reproduced exactly** |
| panel b ceilings (20 points) | all four solvent traces | recomputed all 20; e.g. DMF: 84.9 / 89.6 / 158.5 / 515.6 / 176.5. Matches `results/figK_thermal.json` | **YES â reproduced exactly** |
| reference lines `50 / 500 / 1000` | panel b | 50 = registry threshold; 500 and 1000 are the (unsourced) design currents | 50 **YES**, others unsourced |
| `U_required` values | panel c | recomputed: THF 0.0418/0.0586/0.0986; MeCN 0.0057/0.0117/0.0222; DMF 0.0053/0.0086/0.0153; NaOH 0.0010/0.0047/0.0102; passive 0.0129/0.0091/0.0010 | **YES â reproduced exactly** |
| band edges `8e-4, 2e-2, 8e-2, 2e-1, 1.0` W cmâ»Â² Kâ»Â¹ | panel c three shaded bands | **UNSOURCED** â script flags. The PEM band (0.2â1.0) does contain registry `U' PEM-class` 0.30; but registry `U' stirred bath` 0.18 falls in the **unlabelled white gap** between "forced air" and "liquid cold plate" | **UNSOURCED, self-flagged** |
| volume sweep `50/100/500/1000 mL`, Ï â V^(2/3) | JSON `volume_sweep`, quoted in SI | recomputed DMF: **67.2 / 84.9 / 145.7 / 183.8**; SI text says "67, 85, 146 and 184" | **YES** |
| ratio "2.16Ã" (1 L vs 100 mL) | docstring / SI | 183.8/84.9 = **2.164**; V^(1/3) = 2.154 | **YES** |
| stirring claim "Uâ² rises only 0.0144 â 0.0160" | SI prose | recomputed `U_passive(12.5,800)` = **0.015990** | **YES** |

**Independently found and already remediated mid-audit:** the previous docstring quoted a vessel-size series "49 / 62 / 106 / 134 mA cmâ»Â²". I could not reproduce it (I got 74/93/160/201) and traced the exact 1.50Ã discrepancy to a **stale Îº = 0.35 S mâ»Â¹** (the unregistered DMF value) â reproducing 49.00 / 61.80 / 105.90 / 133.51 to the digit. The current version deletes the prose series and computes it into the JSON. Also fixed: a console header reading "UNSTIRRED BEAKER, 5 mm" against a 2 cm model.

---

## Most serious problems, ranked

**1. `make_fig4A.py` panels (a) and (c) label the Î´ ladder one rung off the model that panel (d) plots â main-text figure.** Panel (a) says the 1 mm flow cell has Î´ â 30â60 Âµm and thin gap/RCE Î´ < 10 Âµm. Back-solving the same figure's own `tier0_ec_matrix.csv` gives flow Î´ = 53â96 Âµm (median 76) and thingap Î´ = 21â38 Âµm (median 30); nothing in the model is below 9.4 Âµm. Panel (c) then plots the "flow cell" curve at Î´ = 30 Âµm and annotates **c_surf = 0.69**; at the model's real flow Î´ the answer is **c_surf = 0.21**. This is exactly the mediator-figure failure mode (Ã30 annotated, Ã9 real) â an annotation that is arithmetically self-consistent with a private input and contradicted by the adjacent panel by 3.3Ã. The "flow cell keeps its surface concentration at 69% of bulk at the barrier current" reading is not supported. Fix: either relabel panels (a)/(c) as a generic Fickian Î´ ladder (300/100/30/10 Âµm) with no reactor names, or re-run `run_profiles.jl` at the architecture medians (300/100/76/30/12.8/11.2).

**2. `make_fig4B.py` panels dâf are a superseded duplicate of Fig K built on conductivities that Fig K's own header names as unregistered.** Three of five Îº values (0.1 M BuâNPFâ/THF 0.6 mS cmâ»Â¹, 0.1 M BuâNBFâ/DMF 3.5, 1 M KOH aq 200) have **no row in the registry**. The two figures therefore publish different answers to the same question: THF boils at 31 (4B) vs 29 (K); DMF at 132 vs 85; MeCN at 139 vs 84 â and 4B's panel-e inset asserts Uâ² = 0.02 W cmâ»Â² Kâ»Â¹ while Fig K's docstring now states in terms that this value "does NOT recover" the vessel geometry (0.0144). The SI cites `Fig. 4B-c)` once and Fig K four times, so Fig K appears to be the intended survivor. If 4B-def still ships, the paper contradicts itself on its own thermal ceiling.

**3. `make_figs.py` FIG D right-panel cooling bands plot W cmâ»Â² Kâ»Â¹ numbers on a W cmâ»Â² axis.** "passive air" 0.005â0.02 and "stirred liquid" 0.05â0.2 are the registry's *Uâ²* values, not heat fluxes; only the PEM band (1â10) is a genuine flux. The two bad bands are low by roughly ÎT (60â130 K), i.e. ~2 orders of magnitude. Consequence: the panel shows a 5 mm DMF cell at 50 mA cmâ»Â² (0.357 W cmâ»Â²) as requiring engineered cooling, whereas Fig K's balance says the same chemistry in a beaker is passively fine to 85 mA cmâ»Â². Either fix the units or delete the bands.

**4. Fig 4B panel (c) â the entire nondimensional design map â reads no data and its two governing constants cannot be reconstructed.** `mu = 0.041` and `eps = 0.060` are hand-entered; the concentration ratios (0.05, 0.10) check out against `reactions_50.csv`, but the diffusivity ratios (0.82, 0.6) that produce them are stored nowhere â `reactions_50.csv` has a `D_cm2s` column for the *carrier only*, with no substrate diffusivity. The slope ladder (Î´_batch/x_k = 1, 10, 100) is likewise illustrative. This panel is unauditable by construction, same class as `make_fig_mediator_k.py`. Minimum fix: add a `D_substrate_cm2s` column to `reactions_50.csv` (the Wilke-Chang/Stokes-Einstein machinery in `D_provenance` already exists) and compute mu/eps in the script.

**5. `julia/` and `results/` hold non-identical copies of the same solver outputs, and the figures read `julia/`.** All four checked pairs differ. For the values Fig 4B actually plots the divergence is small (c_ox(0) at k=1000: 0.7081 vs 0.7059), but `npp_ecprime_sweep.csv` diverges catastrophically at high k (k=3000: 46.4 vs 27.6; k=10000: 29.3 vs **0.34**, an 87Ã gap). Nothing in the tree records which run is canonical. Any SI number quoted from `results/` while the figure was drawn from `julia/` is silently inconsistent.

**6. Two of the four generators cannot be executed against this repository.** `make_fig4A.py` L18 and `make_figs.py` L12 read `reactions_50.csv` from the working directory; the file is at `data/reactions_50.csv`. `make_figs.py` L128 reads `julia/npp_support_sweep.csv` and `julia/npp_profiles.csv`; both live in `results/`. The script therefore crashes before FIG E, so `sec4_figE_npp.svg` (dated 2026-07-12) is frozen and unregenerable â its numbers cannot be re-verified by running the code that made it. All four scripts also still carry the hardcoded sandbox paths `/home/claude/rce`; only `make_figK.py` has been given a portable path search.

**7. Lower-severity, does not flip a conclusion.**
- `make_figs.py` FIG A plots mediator/catalyst rows with a Fickian shuttle bound while FIG B/C plot the same reactions with the ECâ²-coupled `tier0` values, both on axes labelled "limiting current density"; ACT-mediated at Î´ = 300 Âµm reads 0.48 here and 12.80 there (26Ã). Distinguished only by linestyle, never stated.
- `make_figs.py` L99 loads `julia/cellvoltage.csv` into `cv` and never uses it; FIG D re-derives the stack in Python. The reimplementation is faithful (agrees with the Julia output to <1e-3 V), so this is a provenance smell rather than an error â but the figure does not plot the model file it appears to.
- `make_figs.py` FIG A band edges (200â400, 70â140, 20â60, 6â15 Âµm) match neither the registry point values (300, 100) nor its stated 250â500 Âµm plateau nor the model's back-solved Î´.
- `make_figs.py` FIG B guide line: `n=2`, `D=8e-10`, `Î´=50 Âµm` all unsourced, plus a dead `*0` term.
- Fig 4A panel d: the text `"50"` is placed at axes-fraction 0.585, which is *y* â 17 â below both the 50 line (0.666) and the 25 line (0.613).
- Fig 4A panel b: the top curve is tagged `= i_lim` but is i = 48.001 against `ilim` = 48.243.
- Fig 4B panel a: "C_cat = 3â30 mM" vs an actual `reactions_50.csv` minimum of 2.6 mM.
- Fig K registers its 100 Â°C boiling point under `aq. KOH: Tb` while the script's solvent is `1 M NaOH aq`.
- `E0 = 2.0 V`, `i0 = 1.0 mA cmâ»Â²` and `T = 298.15 K` are honestly declared registry assumptions but carry **no sensitivity bound**, which the standard requires for class C. `E0` is asserted to be dominated by the ohmic term; that claim is testable and untested in the registry.

**Verified clean (worth recording so it is not re-audited).** Every count and median that reaches these figures reproduces exactly from `julia/tier0_ec_matrix.csv`: the 50-reaction swarm â¥50 counts **8 / 14 / 15 / 25 / 32 / 34**, the â¥25 counts **11 / 17 / 22 / 31 / 36 / 36**, the architecture medians **6.06 / 17.40 / 20.18 / 50.16 / 111.69 / 127.40** mA cmâ»Â², and FIG B's "28/50 below threshold". The Fig 4A worked example closes analytically (1 eâ» Ã 96485 Ã 1e-9 mÂ² sâ»Â¹ Ã 500 mol mâ»Â³ / 100 Âµm = 48.24 mA cmâ»Â², matching the solver's `ilim` to four figures), and its 300/100/30/10 Âµm ladder scales as 1/Î´ exactly. The Fig 4B panel-b reaction layer (x_k = 1.095 Âµm at k = 10Â³, Î´ = 100 Âµm, 0.9 i_lim) traces cleanly to `julia/npp_ecprime_sweep.csv` and `julia/run_ecprime.jl`. Fig K's entire chain â Uâ², all four panel-a boil points, all 20 panel-b ceilings, all 12 panel-c duties, and the volume sweep â reproduces exactly from an independent reimplementation and agrees with both the rendered SVG and the SI prose. The rendered `sec4_Fig4A.svg` matches the current script text with no drift."
    ],
    "synthesis": "# CONSOLIDATED PROVENANCE DELIVERABLE â Section4_Model figure generators

Repo: `/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model`
14 generators in `figs/` â **20 rendered figure files**. Registry: `data/parameters_provenance.csv` (236 rows: 101 measured-lit, **86 lit-representative (abolished)**, 23 derived, 10 assumption, 8 correlation-est, 8 numerical).

Three findings from this pass that were **not** in the per-generator traces and change conclusions:

- **`figs/sec4_figH_ecprime.{png,svg}` has no generator anywhere in the repo** (grep `figH` â zero hits in any `.py`/`.jl`/`.js`). It is cited in the SI (`make_si.js` L331, Â§S5.6, "Fig. H, open squares"). This is the single most unauditable artifact in the set: an SI-cited figure with no source code at all.
- **The three "fabricated" open squares in `make_fig_main.py:150` are in fact SI-declared.** Â§S5.6 states: "in that regime the exact total-catalysis limit is reported instead (**Fig. H, open squares**)". So they are an analytic substitution (i_cap = Î³Â·i_sh = 48.24), not invented data â state **B**, not a fabrication. The defect is narrower: the substitution is disclosed only in the SI, only for Fig. H, and carries **no on-figure flag** in `sec4_MAIN_composite`; and the solver's own k = 3Ã10Â³ point (46.38, the sweep maximum) is silently deleted rather than replaced. Downgrade this from "worst finding" to "undeclared-on-figure substitution + one real deletion".
- **`make_figK.py` (remediated) and `make_fig4B.py` panels e/f + `make_figs.py` FIG D now contain two mutually contradictory thermal models of the same cells**, using two different electrolyte sets and two different passive-Uâ² values. Quantified in Â§3 (A29, A28, A30).

---

## 1. UNSOURCED-NUMBER REGISTER

Ranked by exposure. **E1** = sets a headline reference line or the annotated conclusion of a panel. **E2** = sets a plotted curve, marker, or on-figure quoted value. **E3** = sets a shaded band, tier boundary, axis annotation, or label.

### TIER E1 â headline reference lines and annotated conclusions

| # | file:line | value | controls | reader sees it in |
|---|---|---|---|---|
| R1 | `make_fig_carrier.py:71,73` | `D=6e-6` cmÂ²/s, `nc=2`, `Ccat=0.010` M | the entire catalyst ceiling in panels c **and** d, and the L81 conclusion "the dilute carrier (3â30 mM) caps it below 25 mA cmâ»Â²" | `sec4_Fig_carrier` c, d |
| R2 | `make_fig_mediator_k.py:16` | `DT = 10.0` Âµm | denominator of `I_of`; sets the **entire y-axis** and the Ã30 headline line (L28â29) | `sec4_Fig_mediator_k` |
| R3 | `make_fig_mediator_k.py:15` | `D = 1e-5` cmÂ²/s | the model curve + the 0.02â0.5 M band. Back-solving the 8 markers gives D_ox = 5.5e-6 â¦ 2.2e-5 â curve and markers are not the same model | `sec4_Fig_mediator_k` |
| R4 | `make_fig3_ladder.py:20`, `make_figs_sec34.py:61`, `make_fig_carrier.py:93` | `C = 1740.0` | the master `i_lim = C/Î´` line on three figures, plus the "median substrate" line in the carrier panel. Recoverable (all-50 stirred median 17.397 Ã 100 Âµm) but hardcoded, and it is the **wrong population** for the carrier panel (substrate-only median = 22.99 Ã 100 = **2299**) | `sec4_Fig3_ladder`, `sec4_Fig_sec3`, `sec4_Fig_carrier` d |
| R5 | `make_fig3_ladder.py:24`, `make_figs_sec34.py:64`, `make_fig_carrier.py:104` | `Î´ = 14` Âµm | x-coordinate of the RDE/RCE anchor and reference tick. Model medians: RDE **12.65**, RCE **10.94** Âµm. 14 = 1740/124, back-solved onto the drawn line | `sec4_Fig3_ladder`, `sec4_Fig_sec3`, `sec4_Fig_carrier` d |
| R6 | `make_fig4B.py:85,107`, `make_fig_nd.py:27` | `mu = 0.041` | all three mediated curves + the legend title. **Physics error**: n_S = 2 omitted; correct Î¼ = **0.0205** | `sec4_Fig4B_ac` c (main text), `sec4_figI_nondim` a |
| R7 | `make_fig4B.py:85`, `make_fig_nd.py:28` | `eps = 0.060` (the "D ratio 0.6" factor) | the catalyst line. Concentrations are page-verified (Kawamata *JACS* 2019 Table 4 fn a p. 6399); the 0.6 exists in no file â no substrate D for that exemplar is in `reactions_50.csv`, `reactions_table.jl`, or the registry | same |
| R8 | `run_profiles.jl` consts, quoted at `make_fig4A.py:65`, `make_fig_profiles.py`, `make_figs_sec34.py` | `C_S = 0.5` M, `s = 1` eâ», `D_S = 1e-9` mÂ²/s | produce i_lim = 48.243, on which "the '50 mA cmâ»Â² barrier' IS the stirred-beaker boundary layer" rests. Substrate-median equivalent (0.1 M, n = 2, D = 1.394e-9) gives **26.9** | `sec4_Fig4A` b, `sec4_figJ_profiles` a, `sec4_Fig_ceiling` |
| R9 | `make_figFG.py:83` | `r2.rce*5` â "5Ã cat. (25 mM)", 26.97 mA cmâ»Â² | the green punchline bar. 25 mM Ni against 50 mM ArBr = **50 mol%**, stoichiometric metal, not catalytic. No solubility, cost, or feasibility bound | `sec4_figG_waterfall` b |
| R10 | `make_figFG.py:71` | `r.rce*2` â "2Ã conc. (0.125 M)", 376.2 mA cmâ»Â² | companion lever bar | `sec4_figG_waterfall` a |
| R11 | `make_figL.py:36` | `k_LÂ·a = 0.05` sâ»Â¹ | the closing caption claim "bulk GâL capacity â 4.8 A â« 1.3 A cell current". No registry row; SI states the *opposite* emphasis and quotes no number | `sec4_figL_excell` caption |
| R12 | `make_fig_carrier.py:98,99` | band `13â30`, line `22` mA cmâ»Â² | the orange plateau + L110 "flat plateau â reactor can't move it". Derived from **2 of 8** mediated rows; the other 6 span 0.85â5479 mA cmâ»Â² and are Î´-dependent | `sec4_Fig_carrier` d |
| R13 | `make_figK.py:78` | `H_EXT = 13.0` W mâ»Â²Kâ»Â¹ | **every** Uâ², ceiling, and required-Uâ² in all three figK panels. *Partially recoverable*: registry has `h natural convection (air) = 7` (Incropera Table 1.1) and `h radiation = 6â8` (derived) â 13 is their sum at the **bottom** of the h_rad band; the registry's own combined row gives **0.20 W Kâ»Â¹ â 16 W mâ»Â²Kâ»Â¹** | `sec4_figK_boiloff` a, b, c |
| R14 | `make_figK.py:103â107` | `Ï = 12.5 / 12.5 / 10 / 7 / 0.8`; `h_int = 100 / 800 / 2000 / 5000` | panel b's entire architecture trend. Only Ï = 12.5 is registry-derived (`Vessel external area 0.0125 mÂ²`). Ï = 0.8 alone produces the counter-intuitive result that the PEM stack's aq-NaOH ceiling **falls from 841 â 149 mA cmâ»Â²** vs the microfluidic â the panel's most striking claim rests on one unsourced number | `sec4_figK_boiloff` b |
| R15 | `make_figK.py:103â107` | `i_design = 50 / 50 / 100 / 500 / 1000` mA cmâ»Â² | panel c's entire x-basis and its conclusion ("required Uâ² exceeds passively available"). 50 traces to the Ferretti row; 100/500/1000 do not | `sec4_figK_boiloff` c |

### TIER E2 â plotted curves, markers, and quoted values

| # | file:line | value | controls | figure |
|---|---|---|---|---|
| R16 | `make_fig4B.py:120â122,134â138`, `make_figs.py:103â107`, `make_fig_main.py` panel f | Îº = **0.06** (THF), **0.35** (DMF), **20.0** (KOH) S/m | all five voltage curves and all boil-off points. **No registry row for any of the three** (they exist in `data/electrolytes.csv` only; 18 of its 67 rows have no registry entry). Îº = 0.90 (0.1 M BuâNBFâ/MeCN, 9.0 mS cmâ»Â¹) *is* registered | `sec4_Fig4B_def` d,e,f; `sec4_figD_voltage_joule`; `sec4_MAIN_composite` f |
| R17 | `make_fig4B.py:134â138` | gap â electrolyte pairings (THF/5 mm, DMF/250 Âµm, KOH/1 mm) | which curve is which; not a physical measurement, a scripting choice | same |
| R18 | `make_fig4B.py:139` | `COOL = 0.020 / 0.18 / 0.30` W cmâ»Â²Kâ»Â¹ | all 15 markers in panel f. **These three *are* registry rows** (cat. 9: UA still air 0.20 W Kâ»Â¹ derived; Uâ² stirred bath 0.18 lit-representative; Uâ² PEM plates 0.30 measured-lit, Wallnoefer-Ogris *Front. Chem. Eng.* 2024, 6, 1384772) â but they contradict figK (see A28âA30) | `sec4_Fig4B_def` f |
| R19 | `make_fig_carrier.py:88` | `D = 1e-5` cmÂ²/s, `nc = 2` | panel d blue substrate band. Set median D = **1.394e-5**; n_carrier â {0.1,1,2,4,6} | `sec4_Fig_carrier` d |
| R20 | `make_fig_carrier.py:74` | `dl = 10` Âµm "thin gap" | panel c's second line and the "10Ã thinner Î´" claim. No archetype in the repo is 10 Âµm (LÃ©vÃªque thin-gap Î´_eff = 24.9â37.6) | `sec4_Fig_carrier` c |
| R21 | `run_profiles.jl` L65 | `("flow", 30e-6)`, `("thingap", 10e-6)` | the labelled curves in three figures. Paper's own archetypes at D = 1e-9: flow **68.1** Âµm, thin gap **27.0** Âµm | `sec4_figJ_profiles` b, `sec4_Fig_ceiling` a, `sec4_Fig4A` c |
| R22 | `make_figs.py:58` | guide slope `0.1*2*F*8e-10*(C*1000)/5.0e-5` â n = 2, D = 8e-10 mÂ²/s, Î´ = 50 Âµm | the grey `i â C` guide across all 50 points. **All three inputs are individually wrong** (D is 1.74Ã below the substrate median 1.394e-9; Î´ is 1.5Ã below the flow median 74.4 Âµm) and they cancel: at C = 0.1 M the guide gives 30.88 vs the substrate-row flow median **29.56**. Right answer, no defensible derivation | `sec4_figB_ilim_vs_C` |
| R23 | `run_ecprime.jl` consts | `C_med = 20` mM, `D_med = 6e-10`, `C_S = 500`, `C_sup = 0.1` M | the "ACT-like" ECâ² base case. **No registry row.** Drives five panels across four figures, and disagrees with the ACT system it names (25 mM in `reactions_50.csv` and in `sec4_MAIN_composite` panel c's own label) | `sec4_figJ_profiles` c, `sec4_Fig4B_ac` b, `sec4_figI_nondim` b, `sec4_MAIN_composite` e, `sec4_Fig_carrier` b |
| R24 | `make_figL.py` via `run_excell.jl` | `D_OX = 1.4e-9` mÂ²/s, `k = 10` Mâ»Â¹sâ»Â¹ | x_k = 167 Âµm, the whole ex-cell argument. Both lit-representative; D_OX cited as "CRC / water-treatment transport data" with no locator | `sec4_figL_excell` |
| R25 | `run_excell.jl` vs `run_mediated.jl` | `D_P = 1.2e-9` vs `D_S = 1.37e-9` mÂ²/s (propylene) | two diffusivities for one species; neither registered. Moves the headline 2.2% / 97.8% split by ~15% relative | `sec4_figL_excell` |
| R26 | `run_excell.jl` | `i_op = 1306` A mâ»Â² ("131 mA cmâ»Â²") | the operating point of every curve. Comment says "the tier-0 unstirred number" â that is 130.6 in the **superseded** `tier0_matrix.csv`; production `tier0_ec_matrix.csv` gives **263.0** | `sec4_figL_excell` |
| R27 | `make_figL.py:23` | `0.25` mM (5% of bulk) | defines the shaded "propylene-free zone". The *extent* (29.45 Âµm) is computed from data; the cut is arbitrary | `sec4_figL_excell` |
| R28 | `make_fig_main.py:150` | three open squares at `i_cap` = 48.24 for k = 3e3/1e4/1e5 | SI-declared as the analytic total-catalysis limit, **unflagged on the figure**; solver values 46.38 / 29.26 / 19.28 | `sec4_MAIN_composite` e |
| R29 | `make_fig_main.py` L~148, `make_fig_nd.py` | `sw.k_M <= 1e3` filter | drops the sweep maximum (k = 3e3, 46.38); reason undisclosed | `sec4_MAIN_composite` e, `sec4_figI_nondim` b |
| R30 | `make_fig_nd.py:32` | `sl = 1, 10, 100` | the three mediated curves. Illustrative decades; the ACT system supplying Î¼ has Î´_batch/x_k = **38.9**, none of the three | `sec4_figI_nondim` a, `sec4_Fig4B_ac` c |

### TIER E3 â bands, tier boundaries, schematic labels

| # | file:line | value | controls |
|---|---|---|---|
| R31 | `make_fig3_ladder.py:27â31`, `make_figs_sec34.py:62â63` | TIERS `(100,500)(10,100)(1,10)(0.3,1)` Âµm | four labelled bands + the tier taxonomy. No registry row, no data file, no SI text. Collides with the SI's *model*-tier nomenclature (Tier 0 = Nernst film, Tier 1 = NPP) |
| R32 | `make_fig3_ladder.py:28â31` | "g â 100 g", "100 g â kg", "mg â g", "frontier" | production-scale annotations; unauditable |
| R33 | `make_fig3_ladder.py:28â31` | 4 on-figure citations | "Griffin, AbbVie (OPRD 2024)", "Manthiram 2024", "Kappe 2023", "Berlinguette" â **three do not resolve** to any key in `make_si.js` |
| R34 | `make_figs.py:38` | FIG A bands `(200,400)(70,140)(20,60)(6,15)` Âµm | four reactor bands. Flow 20â60 vs LÃ©vÃªque **38.0â95.8** (median 74.4, outside); "RDE/RCE/thin gap" 6â15 vs thin gap **15.1â38.0** (entirely outside) |
| R35 | `make_fig_main.py:30`, `make_figs_sec34.py:41`, `make_fig4A.py:33` | schematic "30â60 Âµm", "<10 Âµm" | the architecture-ladder schematic in three figures. `make_figs_sec34.py` and `make_fig4A.py` both drop `make_fig_main.py`'s "schematic placeholder" disclaimer |
| R36 | `make_fig_main.py:162`, `make_figs.py:112`, `make_fig4B.py:124` | `axhspan(10,20)` V "academic non-aqueous cells" | validation band derived from this same voltage stack â **circular**, no external survey |
| R37 | `make_figs.py:119â121` | Joule bands `0.005â0.02`, `0.05â0.2`, `1â10` W cmâ»Â² | three cooling regimes. **Unit-inconsistent** (see A28) |
| R38 | `make_figK.py:186â188` | band edges `8e-4, 2e-2, 8e-2, 2e-1, 1.0` W cmâ»Â²Kâ»Â¹ | three cooling-regime bands in panel c. Registry Uâ² stirred bath = **0.18** falls in the gap between the "forced air" top (0.08) and "liquid cold plate" bottom (0.2) |
| R39 | `make_fig_main.py:56`, `make_fig4B.py:38` | "C_cat = 3â30 mM" | taxonomy annotation; data and the SI both say **2.6â30 mM** |
| R40 | `make_fig_carrier.py:92` | `0.02â0.5` M substrate band | silently excludes the industrial rows (max C = **6.85 M**) |
| R41 | `make_fig_nd.py:37`, `make_fig4B.py:92` | xÌ bands `(2.5,3.5)(5,15)(30,100)` | archetype annotation on a main-text panel; two of three contradicted (A24) |
| R42 | `make_fig4B.py:164` | caption "UA = 0.2 W Kâ»Â¹" | registry-derived, but figK's geometric value is **0.1438 W Kâ»Â¹** (â28%) |
| R43 | `make_figK.py:245` | `VOLUMES = 50/100/500/1000` mL, `V_REF = 100` | the V^(1/3) sweep. Derived and JSON-archived; inherits the registry row `Cell volume / electrode area`, class **assumption**, citation `--` |

### Registry-level gaps behind all of the above
- **`delta (unstirred batch) = 300 Âµm`** and **`delta (stirred batch) = 100 Âµm`**: class *lit-representative*, chapter-level citations only (Bard & Faulkner ch. 1 / Amatore *JEAC* 2001 **500**, 62; Pletcher & Walsh 2nd ed.). These two set essentially every number in the whole figure set.
- **`Thin-gap Leveque geometry` (250 Âµm / 2.5 cm / 10 cm sâ»Â¹)**: *lit-representative*, citation "Atobe/Noel flow-electrochemistry literature" â **no author, year, or page**. Sets the green series in Fig. M, bar 4 in Fig. G, and part of `best` in Fig. F.
- **49 of 49 registry conductivity rows** are class *lit-representative* except 8 measured-lit CRC/Peters entries; **18 rows of `data/electrolytes.csv` have no registry row at all**, including the three used by every voltage/thermal panel.
- **No registry row exists** for: generic D_cat, generic D_sub, n_c for either class, C_cat representative, Î´ = 10 Âµm, Î´ = 14 Âµm, the entire `run_ecprime.jl` base case, propylene D, k_LÂ·a, h_ext, h_int, Ï (except 12.5), i_design.

---

## 2. VERDICT PER FIGURE

**Definitions.** *Fully traceable* = every plotted coordinate **and** every on-figure annotation resolves to an archived data file or a registry row (the registry row's own class is judged separately). *Partial* = plotted data resolve but annotations/bands/labels are script-internal. *Unauditable* = the load-bearing numbers exist only in the plotting script (or no script exists).

| Rendered figure | Generator | Data reads | Verdict |
|---|---|---|---|
| `sec4_figC_heatmap` | `make_figs.py` | `tier0_ec_matrix.csv` | **FULLY TRACEABLE** â all 300 cells + all six column counts (11/17/22/31/36/36) recomputed exactly; only literal is THRESH = 25 (page-verified Ferretti) |
| `sec4_figE_npp` | `make_figs.py` | `npp_support_sweep.csv`, `npp_profiles.csv` | **FULLY TRACEABLE** in content; the 2.00 line is analytic. *But the script reads `julia/â¦` and the files now live in `results/â¦` â Fig E cannot be regenerated* |
| `sec4_figF_gap` | `make_figFG.py` | `tier0_ec_matrix.csv`, `reactions_50.csv` | **PARTIAL** â every endpoint and count verified; 7 endpoints clipped off-axis; one bin count missing |
| `sec4_figM_mediated_ec` | `make_figM.py` | `mediated_ec_matrix.csv` | **PARTIAL** â all coordinates from data, all 8 mediator concentrations correct; one row key mismatched â silently drops the system SI Â§S5.7 calls its third structural result |
| `sec4_figG_waterfall` | `make_figFG.py` | `tier0_ec_matrix.csv` | **PARTIAL** â bars 1â5 recomputed exactly; bar 6 (Ã2 / Ã5) invented |
| `sec4_figL_excell` | `make_figL.py` | `excell_profiles.csv` | **PARTIAL** â curves and the 97.8%/2.2% split independently recomputed; 785 mA cmâ»Â², k_LÂ·a, i_op = 131, and the 0.25 mM cut are script/stdout-only |
| `sec4_figA_ilim_vs_delta` | `make_figs.py` | `reactions_50.csv` + `tier0_ec_matrix.csv` | **PARTIAL** â 7 curves data-driven, all 7 concentration labels verified; four reactor bands unsourced, two contradicted |
| `sec4_figB_ilim_vs_C` | `make_figs.py` | same | **PARTIAL** â 50 points + the "28/50 below threshold" count verified; guide line has three unsourced inputs |
| `sec4_figJ_profiles` | `make_fig_profiles.py` | `profiles_direct.csv`, `npp_ecprime_profiles.csv` | **PARTIAL** â curves from data; every annotated number (0.90, 0.69, 48, 16, x_k â 1 Âµm) hand-typed; Î´ labels contradict the archetypes |
| `sec4_figI_nondim` | `make_fig_nd.py` | `npp_ecprime_sweep.csv` (panel b only) | **PARTIAL** â panel b markers real; panel a is entirely closed-form on two unsourced/incorrect constants |
| `sec4_MAIN_composite` | `make_fig_main.py` | `reactions_50.csv`, `tier0_ec_matrix.csv`, `npp_ecprime_sweep.csv` | **PARTIAL** â panels c, d, f verified to printing precision (all 25 voltage points to 1e-4 V); panels a, b, e carry script-only numbers |
| `sec4_Fig4A` | `make_fig4A.py` | `reactions_50.csv`, `tier0_ec_matrix.csv`, `profiles_direct.csv` | **PARTIAL** â panel d counts (8/14/15/25/32/34) exact; panel a schematic and panel c Î´ labels script-only; carries the axes-fraction label bug |
| `sec4_Fig4B_ac` | `make_fig4B.py` | `npp_ecprime_profiles.csv` (panel b only) | **PARTIAL** â panel b from data; panel c is closed-form on Î¼ (wrong by 2Ã) and Îµ, with two contradicted bands |
| `sec4_Fig_ceiling` | `make_figs_sec34.py` | `profiles_direct.csv`, `tier0_ec_matrix.csv` | **PARTIAL** â scatter counts and c_surf values exact; Î´ = 30/10 Âµm legend contradicts the scatter panel directly beneath it |
| `sec4_Fig_sec3` | `make_figs_sec34.py` | `profiles_direct.csv` | **PARTIAL** â starvation panel data-driven; the ladder half is script-only (C = 1740, four tiers, Î´ = 14). *SVG/PNG (20:52) predate the script (21:02)* |
| `sec4_figK_boiloff` | `make_figK.py` | **none** (self-contained model) | **PARTIAL / SELF-DECLARED** â output fully archived to `results/figK_thermal.json`, all values reproduced exactly here; but ~20 inputs are hardcoded and the docstring L53â64 enumerates them itself. Honest, not yet compliant |
| `sec4_Fig4B_def` | `make_fig4B.py` | none | **UNAUDITABLE** â every Îº, gap, Uâ², and boiling point is a script literal; superseded by figK with different answers |
| `sec4_figD_voltage_joule` | `make_figs.py` | reads `cellvoltage.csv` then **re-implements the physics instead of plotting it** | **UNAUDITABLE** â same unregistered Îº set; panel b's three cooling bands are dimensionally inconsistent |
| `sec4_Fig_carrier` | `make_fig_carrier.py` | `npp_ecprime_profiles.csv` (panel b only) | **UNAUDITABLE** â 11 of ~14 load-bearing numbers in panels c/d exist only in the script; three of its four written conclusions are contradicted by the project's own solver |
| `sec4_Fig3_ladder` | `make_fig3_ladder.py` | **zero** | **UNAUDITABLE** â C = 1740, three anchors, four tier boundaries, four reactor labels, four citations, four scale ranges all script-internal; no SI paragraph exists for it |
| `sec4_Fig_mediator_k` | `make_fig_mediator_k.py` | **zero** | **UNAUDITABLE** â closed-form toy; all 8 markers disagree with the solver; not in the SI |
| `sec4_figH_ecprime` | **none exists** | â | **UNAUDITABLE â NO GENERATOR.** Cited in SI Â§S5.6 |

**Counts (22 rendered artifacts incl. figH):**
- **Fully traceable: 2** (`figC`, `figE` â and `figE` is not re-runnable).
- **Partial: 14.**
- **Unauditable: 6** (`Fig4B_def`, `figD`, `Fig_carrier`, `Fig3_ladder`, `Fig_mediator_k`, `figH`).

**At generator level (the "14 figures"): 0 fully traceable, 9 partial, 5 unauditable** (`make_fig3_ladder.py`, `make_fig_mediator_k.py`, `make_fig_carrier.py`, `make_fig4B.py` def-half, `make_figs.py` D-half) â plus one SI-cited figure with no generator.

**Under the stated standard, zero of the 14 are compliant today**, because all of them inherit at least one abolished-class input (Î´_stirred / Î´_unstirred / thin-gap geometry / Îº).

**SI coverage** (`make_si.js`): referenced by name â Fig. C (Ã2), Fig. E, Fig. F (Ã2), "Figs. F and G", Fig. H, Fig. K (Ã3), Fig. 4B-c. **Not referenced anywhere** â Fig. A, Fig. B, Fig. D, Fig. I, Fig. J, Fig. L (its numbers appear in Â§S5.5 but the figure is never named), Fig. M, Fig. 3 ladder, Fig. 4A, `Fig_carrier`, `Fig_mediator_k`, `Fig_sec3`, `Fig_ceiling`. Nine unreferenced figures = nine figures the SI's own consistency checks cannot see.

---

## 3. ANNOTATION ERRORS (drawn value vs. underlying data)

**Structural / data-dropping**

| # | where | drawn | actual |
|---|---|---|---|
| A1 | `make_figM.py:17` | key `"NHPI-mediated benzylic C-H -> ketone"` â row rendered as an empty y-label | data says `"NHPI-mediated allylic C-H -> enone"`. `g.empty â continue` skips silently. Docstring claims 8 systems; **7** are drawn. The omitted row is SI Â§S5.7's third structural result (Ã1.135 stirred, Ã1.020 thin-gap, x_k = 158.2 Âµm) |
| A2 | `make_fig_main.py:131` **and** `make_fig4A.py:103` | `annotate("50", xy=(1.005, 0.585), axes fraction)` | on ylim (0.008, 4000) log, frac 0.585 â **y = 17.26**. y = 50 is at 0.666, y = 25 at 0.613. The "50" caption renders **below the dotted 25 line** in both figures. `make_figs_sec34.py` already has the fixed version (data coords) |
| A3 | `make_figs.py:128` | `pd.read_csv("julia/npp_support_sweep.csv")` | files are in `results/` â FIG E is unreproducible |
| A4 | repo | `sec4_figH_ecprime.{png,svg}` cited in SI Â§S5.6 | no generator exists |

**Stated conclusions contradicted by the authors' own data**

| # | where | drawn | actual |
|---|---|---|---|
| A5 | `make_fig_carrier.py:81` | "the dilute carrier (3â30 mM) **caps it below 25 mA cmâ»Â²**" | the script's own `icat_mA(10, 0.030)` = **34.7**; `tier0_ec_matrix.csv` catalyst rows reach **52.58** at RCE. The SI is careful ("10 of 11 â¦ the single exception runs at 30 mM"); the figure deletes the exception and hardens it into a physical cap |
| A6 | `make_fig_carrier.py:109` | "capped low" | the script's own band crosses 25 at Î´ = **13.9 Âµm** and 50 at **6.95 Âµm**, both inside the plotted range |
| A7 | `make_fig_carrier.py:110` | "fast mediator: flat plateau â reactor can't move it" | contradicted for **6 of 8** mediated entries. Cleanest converged counterexample: aryl thiocyanation (k = 100, x_k = 4.7 Âµm â inside the claimed plateau regime) gives 17.63 mA cmâ»Â² at Î´ = 100 Âµm and 27.18 at Î´ = 62.7 Âµm, i.e. **i â Î´^â0.93** |
| A8 | `make_fig_carrier.py:93` | 1740 labelled "median substrate (~0.1 M-equiv)" inside the blue substrate band | it is the **all-50** median (contaminated by the 11 dilute-catalyst rows the panel exists to contrast). Substrate-only = **2299**; the line is **24% low** |
| A9 | `make_fig_mediator_k.py:29` | "direct substrate: full reactor benefit (**Ã30**)" | per-row unstirredâX median ratios: thin gap **Ã9.94**, RDE Ã23.5, RCE Ã26.8. Ã30 exceeds every real archetype; the figure's own named comparator (thin gap) gives Ã9.9 |
| A10 | `make_fig_mediator_k.py:54` | "(k â³ 20): plateau, **reactor Ã1**" over 6 markers | wrong for **4 of 6**. Solver thin-gap/unstirred ratios: BQ/Wacker **Ã4.73**, SCNâ» **Ã9.91**, Brâ»/bromination **Ã8.70**, ACT/HMF Ã1.70 |
| A11 | `make_fig_mediator_k.py:45` | all 8 markers | **all 8 disagree with `mediated_ec_matrix.csv`.** Cause is structural: `I_of` models only the SavÃ©ant bound, but the solver's limiter for SCNâ»/Brâ»/BQ is the substrate total-catalysis cap â 1/Î´, which the toy cannot represent |
| A12 | `make_fig_carrier.py:64`, `make_fig_profiles.py:83`, `make_fig4B.py:74` | "x_k â 1 Âµm â no stirrer / no reactor reaches this layer" | analytic x_k = 1.095 Âµm uses **bulk** C_S, but the curve is drawn at 0.9 i_lim where c_S(0) = 0.237. Plotted 1/e decay = **2.29â2.33 Âµm**; c_ox(1 Âµm) = **0.466**; 1% of wall at **10.5 Âµm** â a depth the repo's own RDE (11.7â15.8) and RCE (11.1â12.5) archetypes reach |
| A13 | `make_fig4B.py:77`, `make_fig_profiles.py` | "substrate dips too (**total catalysis**)" | `npp_ecprime_sweep.csv` labels the k = 10Â³ limiter **"mediator"**, not substrate |

**Î´ / architecture mislabelling**

| # | where | drawn | actual |
|---|---|---|---|
| A14 | `make_fig_profiles.py:66`, `make_figs_sec34.py:109`, `make_fig4A.py:82` | "Î´ = 30 Âµm flow cell: c_surf = **0.69**" | arithmetic correct for 30 Âµm, but the paper's flow archetype gives Î´ = **68.1 Âµm** â c_surf = **0.29** |
| A15 | same files | "Î´ = 10 Âµm thin gap / RCE" | thin-gap archetype = **27.0 Âµm**; 10 Âµm is the RCE number only |
| A16 | `make_fig_nd.py:37`, `make_fig4B.py:92` (main text) | xÌ bands: "flow" 5â15, "thin gap / RDE / RCE" 30â100 | flow = **3.13â7.90** (median 4.03, band excludes it); thin gap = **7.9â19.9** (median 10.2, wholly outside); RDE 19.0â35.5; RCE 20.2â34.3. **Nothing reaches 100** |
| A17 | `make_figs.py:38` | FIG A bands "flow 20â60 Âµm", "RDE/RCE/thin gap 6â15 Âµm" | flow = **38.0â95.8** (median 74.4, above the band top); thin gap = **15.1â38.0**, entirely outside 6â15 |
| A18 | `make_fig_main.py:30`, `make_figs_sec34.py:41`, `make_fig4A.py:33` | schematic "flow 30â60 Âµm", "thin gap/RCE <10 Âµm" | flow 38.0â95.8 (10/50 inside 30â60); thin gap **0/50 below 10 Âµm** |
| A19 | `make_fig3_ladder.py:24` | anchor at (14, 127) sitting on the `nFDC/Î´` line | at its true Î´ (RCE 10.94) the point sits ~20% **below** the line. One 1/Î´ curve cannot thread medians over 50 reactions: the line over-predicts flow/thingap/RDE/RCE medians by **16 / 18 / 23 / 25%** |
| A20 | `make_fig3_ladder.py:22` | anchor (300, 6.1) on the curve | 1740/300 = **5.80**, â5.2% off |
| A21 | `make_fig3_ladder.py:24` | label "RDE / RCE", value 127 | that is the **RCE** median (127.4); RDE median = **111.7**, â14% |
| A22 | `make_fig3_ladder.py:30` | Tier 3 (Î´ 1â10 Âµm) labelled "Thin-gap / 3D-printed" | model thin gap = 15.1â38.0 Âµm, median 29.5 â **Tier 2**. Global minimum Î´ over all 6 archetypes Ã 50 reactions is **8.46 Âµm**, so Tiers 3 and 4 have zero model support and the dashed 0.3â10 Âµm extrapolation (to ~5800 mA cmâ»Â²) is drawn at the same visual weight as the anchored region |
| A23 | `make_figM.py` legend | "thin-gap flow" as one Î´ | actual `delta_eff(:thingap)` = **22.7â37.6 Âµm**, per system |

**Thermal â two models, two answers (new this pass)**

| # | where | drawn | actual |
|---|---|---|---|
| A24 | `make_figs.py:119â121` vs `make_figK.py` | FIG D-b bands "passive air 0.005â0.02 W cmâ»Â²", "stirred liquid 0.05â0.2", "engineered cooling 1â10" | **Units are mixed.** The first two are numerically the registry's Uâ² values (0.020 still air, 0.18 stirred bath) in W cmâ»Â²**Kâ»Â¹**, i.e. they implicitly assume ÎT = 1 K; only the PEM band (1â10 W cmâ»Â²) is a genuine flux matching the registry note "2â6 W cmâ»Â² across 10â20 K". Consequence: figK computes that the same passive 100 mL beaker rejects **0.590 W cmâ»Â²** (THF at boiling), **0.820** (MeCN), **1.841** (DMF) â **30â90Ã above FIG D-b's "passive air" band top**, and DMF's passive capacity lands inside FIG D-b's "engineered cooling (PEM-class plates)" band |
| A25 | `make_fig4B.py:134â139` vs `make_figK.py:88â107` | same five/four cells, two boil-off answers | Fig 4B-e/f (Îº = 0.06/0.35/0.90/20.0 S/m, Uâ² = 0.020) vs figK (Îº = 0.30/1.80/0.80/18.0, Uâ² = **0.01438**): DMF still air **132.1** vs **84.9** mA cmâ»Â²; MeCN **138.8** vs **83.9**; aqueous **1152.9** vs **286.5**; THF 31.2 vs 29.5. figK's Îº set is registry-backed (3.0 M LiBr/THF, Peters *Science* 2019 SM pp. S15/S21 â page-verified; 1 M NaOH aq, CRC); fig4B's is not |
| A26 | `make_figK.py:186â188` vs registry cat. 9 | band edges 2e-2â8e-2 ("forced air"), 2e-1â1.0 ("liquid cold plate") | the registry's own `U' stirred bath = 0.18 W cmâ»Â²Kâ»Â¹` falls in the **gap** between the two bands |
| A27 | `make_fig4B.py:164` | "UA = 0.2 W Kâ»Â¹, incl. radiation" | registry-derived, but figK's geometric route gives **0.1438 W Kâ»Â¹** (â28%), and figK's docstring explicitly states that 0.02 W cmâ»Â²Kâ»Â¹ "does NOT recover" the geometric value |

**Rendering / clipping / staleness**

| # | where | issue |
|---|---|---|
| A28 | `make_figFG.py:40` | `set_xlim(0.05, 3000)` clips 7 endpoints: Rh CâH alkenylation (0.0346) and CoâH isomerization (0.0441) read as 0.05 (~40% high); ADN (7056), Clâ»/propylene (5479), Shono Î±-methoxylation (3645) and two more have **no visible right endpoint** |
| A29 | `make_figFG.py` legend | 34/50 (green) + 14/50 (red) = 48; the orange 2/50 bin carries no count |
| A30 | `make_figL.py` docstring | "98.6% of the oxidant exported"; rendered and recomputed value is **97.79%** |
| A31 | `make_figL.py:28` | "surface barely perturbed at 131 mA cmâ»Â²" â c_Cl(0)/c_bulk = **0.835**, a 16.5% depletion |
| A32 | `make_figM.py` | ECâ² markers plotted 2â3 decades right of the grey ticks the legend calls the substrate cap (Clâ»/propylene stirred: **788.9 vs 1.32**, 600Ã). Justified in SI Â§S5.1 as ex-cell mediation; no on-figure flag |
| A33 | `make_fig_main.py` / `make_fig_nd.py` panel b | 4 of 7 plotted validation points are labelled `newton-wall (no collapse)` in `npp_ecprime_sweep.csv` (strict lower bounds from a stalled ramp) and are drawn as ordinary markers. The two worst (k = 100, 300) sit **28% and 31% below** theory â the direction a stalled ramp produces |
| A34 | `make_fig_main.py` panel c vs panel e | same ACT system labelled "med. 25 mM" in c and modelled at 20 mM in e |
| A35 | `make_fig_main.py:56` / `make_fig4B.py:38` | "C_cat = 3â30 mM"; data and SI both say **2.6â30 mM** |
| A36 | `make_figFG.py:81` comment | says "10 mM"; data and the rendered label both say 5 mM |
| A37 | `figs/sec4_Fig_sec3.{svg,png}` (20:52) | predate `make_figs_sec34.py` (21:02) |
| A38 | `data/build_reactions50.py` (2026-07-13) | newer than the `reactions_50.csv` / `reactions_table.jl` it produces (2026-07-12) |
| A39 | author's brief | lists the starvation currents as "10 / 24 / **36** / 48"; code and figures give **10 / 24 / 39 / 48** (data 9.649 / 24.121 / 38.594 / 48.001). The brief is wrong, not the figure |
| A40 | out of scope | the "26,790 / 60 / 6 / 3, 94% undivided" readiness distribution is produced by **no generator in this repo** (main-text Fig. 1); 26,790 appears only as `make_si.js` prose |

---

## 4. REMEDIATION PLAN, PRIORITISED

### P0 â CUT rather than fix (construction cannot be made honest)

**C1. `make_fig_mediator_k.py` â `sec4_Fig_mediator_k`. CUT.**
Reads zero data. The y-axis is `min(300,x_k)/min(10,x_k)`, a pure SavÃ©ant-bound model; the solver's actual limiter for SCNâ», Brâ» and BQ is the substrate total-catalysis cap â 1/Î´. **No re-tuning of D or DT can fix this** â the toy cannot represent the mechanism that binds 4 of its 6 "plateau" points, and all 8 markers disagree with `mediated_ec_matrix.csv` by up to an order of magnitude. Its headline Ã30 is Ã9.9 at its own named comparator. Not referenced in the SI.
*If the message is worth keeping*, rebuild it as a direct scatter of `mediated_ec_matrix.csv` i_ec ratios (unstirredâthin-gap and unstirredâRCE) against Table S6 k, with `xk_um` as the marker size. That plot is state B end-to-end and tells the honest version of the same story (the payoff is not Ã1, it ranges Ã1.4âÃ20 and does not order by k).

**C2. `make_figs.py` FIG D panel b (Joule/cooling bands). CUT.**
Dimensionally inconsistent (A24), and superseded by figK, which computes the same physics from registry geometry and archives its output. Delete panel b; keep panel a only if its Îº set is fixed (see A-2 below).

**C3. `make_fig4B.py` panels e and f. CUT, cross-reference figK.**
Two thermal models of the same cells in one paper, differing by up to **4Ã** in boil-off current (A25). figK is the better-sourced of the two (registry Îº, geometry-derived Uâ², JSON-archived). Replace 4B-e/f with a pointer to Fig. K, or regenerate them from `results/figK_thermal.json`.

**C4. `make_fig3_ladder.py` Tiers 3 and 4, the four production-scale ranges, and the four on-figure citations. CUT.**
No archetype in the model reaches Î´ < 8.46 Âµm, so Tiers 3â4 and the dashed 0.3â10 Âµm segment are pure extrapolation drawn at anchored weight; Tier 3's "Thin-gap / 3D-printed" label is contradicted by the model's own thin gap (29.5 Âµm, Tier 2). Three of four citations do not resolve. Keeping the figure requires deleting these elements, not sourcing them.

**C5. `sec4_figH_ecprime`. Either recover the generator or cut the SI reference.**
An SI-cited figure with no source code cannot be defended at any level.

### P1 â state B (derive from what is already in the repo; no literature hunt needed)

These are one-session fixes and remove ~15 of the register's entries outright.

| target | derivation | inputs |
|---|---|---|
| R4 `C = 1740` | read the median from `tier0_ec_matrix.csv` at runtime, don't hardcode | `tier0_ec_matrix.csv` |
| R4 carrier-panel median line | use the **substrate-only** median: **2299**, not 1740 | same, filtered by `carrier_type` |
| R5 `Î´ = 14 Âµm` | split into two anchors at the computed medians: RDE **12.65**, RCE **10.94** | `correlations.jl` over the 50 rows |
| R20/R21 `Î´ = 10 / 30 Âµm` in `run_profiles.jl` | replace with `delta_eff()` archetype medians: flow **68.1**, thin gap **27.0** (and restate c_surf: flow becomes **0.29**) | `correlations.jl` |
| R34/R41/R35 all Î´ and xÌ bands | compute from `delta_eff()` over the 50 rows: flow **38.0â95.8**, thingap **15.1â38.0**, RDE **8.5â15.8**, RCE **8.75â14.85**; xÌ flow **3.1â7.9**, thingap **7.9â19.9**, RDE **19.0â35.5**, RCE **20.2â34.3**. Split thin gap from RDE/RCE â they are not one band | same |
| R6 `mu = 0.041` | recompute with n_S = 2 â **0.0205**, and fix SI Eq. S17 (Îµ carries n_c/n; Î¼ does not â same equation) | `run_mediated.jl` MedSpec |
| R19/R1 generic D_cat, D_sub, n_c, C_cat | take the medians of the relevant `reactions_50.csv` populations: D_cat **8.92e-6** cmÂ²/s (11 rows), D_sub **1.394e-5** (31 rows), C_cat **5.0 mM**, and use the modal n_carrier per class. These are already registered derivations (WilkeâChang / StokesâEinstein, registry cat. 3) | `reactions_50.csv` |
| R22 FIG B guide line | rebuild from the same medians rather than n = 2 / 8e-10 / 50 Âµm | same |
| R13 `H_EXT = 13` | declare as `h_conv (7, Incropera Table 1.1) + h_rad (6, low end of the registry's 6â8 derived band)` and register the sum; state why 13 rather than the registry's own combined 16 | registry cat. 9 rows |
| R16 Îº for THF/DMF/KOH | **swap to figK's already-registry-backed set**: 3.0 M LiBr/THF = 3.0 mS cmâ»Â¹ (Peters *Science* 2019, SM pp. S15, S21 â page-verified, class A); 0.25 M BuâNBFâ/MeCN = 18.0; 0.2 M NaI/DMF = 8.0; 1 M NaOH aq = 180 (CRC 97th). This makes the voltage stack and the thermal model use one electrolyte set | registry cat. 6 |
| R23 ECâ² base case | retune to the ACT system it names (C_med = **25 mM**, not 20) so `sec4_MAIN_composite` panels c and e stop disagreeing; register the four constants as derived from the ACT row | `reactions_50.csv`, `run_mediated.jl` |
| R26 `i_op = 130.6` in `run_excell.jl` | repoint to the production `tier0_ec_matrix.csv` value **263.0** and re-render figL (all downstream percentages change) | `tier0_ec_matrix.csv` |
| R28/R29 fig_main panel e | plot the solver values 46.38 / 29.26 / 19.28 as flagged points **and** the analytic cap, with the SI Â§S5.6 substitution stated on the figure | `npp_ecprime_sweep.csv` |
| R43 volume sweep | already B and JSON-archived â just cite the JSON in the SI instead of restating | `results/figK_thermal.json` |
| A33 newton-wall points | read the `limiter` column and render those 4 points as open symbols with down-arrows | `npp_ecprime_sweep.csv` |
| 785 mA cmâ»Â² (figL) | have `run_excell.jl` emit a one-row `excell_summary.csv` â the number is *correct* (785/391.7 = 2.0039 against the recomputed Fick bound), it is only unarchived | â |

### P2 â state A (name the source to hunt; each needs a page/table locator)

| target | likely source to hunt | note |
|---|---|---|
| `delta (unstirred batch) = 300 Âµm` | Amatore *et al.*, *J. Electroanal. Chem.* **2001**, 500, 62â70 â pull the specific page/figure giving measured natural-convection layer thickness; or Bard & Faulkner 2nd ed. Â§1.4 with page | currently ch.-level only; **it sets nearly every number in the whole set** â highest-value A-hunt in the project |
| `delta (stirred batch) = 100 Âµm` | Pletcher & Walsh, *Industrial Electrochemistry* 2nd ed. â locate the table of Î´ vs stirring rate, cite page + table | same |
| `Thin-gap Leveque geometry` (250 Âµm / 2.5 cm / 10 cm sâ»Â¹) | a **named** microflow cell paper with stated gap, channel length and linear velocity (Atobe's or NoÃ«l's cell-description papers; the Ammonite/Vapourtec flow-cell specs are citable with numbers) | "Atobe/Noel flow-electrochemistry literature" is unusable as printed |
| `h_int = 100 / 800 / 2000 / 5000` W mâ»Â²Kâ»Â¹ | **Incropera & DeWitt 6th ed., Table 1.1** already in the registry for h_conv â it also gives free-convection-liquid (50â1000) and forced-convection-liquid (100â15,000) ranges. Cite table + page and state which end each archetype takes | cheap A-conversion |
| `k_LÂ·a = 0.05 sâ»Â¹` | Van 't Riet, *Ind. Eng. Chem. Process Des. Dev.* **1979**, 18, 357 (k_La correlation for stirred tanks), or a chlorohydrin-process reference | if no locator, drop to C with a sensitivity across 0.01â0.5 sâ»Â¹ |
| `D_OX = 1.4e-9` mÂ²/s (Clâ/HOCl) | CRC or a named water-treatment transport table with page | currently "CRC / water-treatment transport data", no locator |
| propylene D (1.2e-9 vs 1.37e-9) | WilkeâChang from a registered molar volume (which makes it B), or a named measurement | pick one value repo-wide |
| the 10â20 V "academic non-aqueous cells" band | an actual survey of reported cell voltages, or **redraw as model output** | currently circular (derived from this same stack) |
| on-figure citations | "Kappe 2023" â resolve to `malviya2023` (*OPRD* 2023, first author Malviya) with volume/page; "Berlinguette" â `sherbo2018` with year; **"Griffin, AbbVie (OPRD 2024)" and "Manthiram 2024" resolve to nothing â delete** | never invent a replacement |

### P3 â state C (declare + sensitivity bound; name the test)

| target | required sensitivity test |
|---|---|
| R8 profile base case (0.5 M, 1 eâ», D = 1e-9) | **The headline claim is at risk.** Declare the base case, then show over which (C_S, n, D) region the "i_lim â 50 mA cmâ»Â²" coincidence holds. Against the paper's own page-verified set the median substrate-carried row (0.1 M, n = 2, D = 1.394e-9) gives **26.9 mA cmâ»Â²** â the barrier sits at ~2Ã the typical stirred-beaker ceiling, not on top of it. If the sensitivity does not support the claim, **reword the annotation**, do not tune the inputs |
| R14 Ï = 10 / 7 / 0.8 | sweep Ï Ã0.5âÃ2 for each compact archetype and show whether the panel-b PEM-stack dip (841 â 149 mA cmâ»Â² for aq. NaOH) survives. This is the panel's most striking claim and it rests entirely on Ï = 0.8 |
| R14 h_int | sweep the Incropera range endpoints; show that h_ext is limiting for the beakers (the docstring already asserts this â quantify it: Uâ² moves only 0.01438 â 0.01599 from stagnant to stirred, **+11%**, which *is* the demonstration) |
| R15 i_design 100 / 500 / 1000 | re-plot panel c at Â±2Ã design current and state whether "required Uâ² > passively available" survives. Currently: 5 mm flow requires 0.0053â0.0418 vs 0.0129 available; 250 Âµm requires 0.0086â0.0586 vs 0.0091; PEM requires 0.0102â0.0986 vs 0.0010. Only THF fails at the flow cell â the conclusion is design-current-sensitive and must be bounded |
| R9/R10 the Ã2 and Ã5 concentration levers | declare as hypothetical, bound by solubility and by catalyst loading. **Ã5 must be replaced** â 25 mM Ni vs 50 mM ArBr is 50 mol%. Use the corpus maximum (30 mM, the Ni homocoupling, which is real and page-verified) as the lever endpoint instead of an invented multiple |
| R31 tier boundaries (if retained after C4) | declare as a taxonomy, not a measurement; rename to avoid collision with the SI's Tier 0/Tier 1 model tiers; show the model-supported Î´ span (8.46â300 Âµm) as an overlay so the extrapolated region is visually distinguished |
| R27 the 0.25 mM (5%) propylene cut | show x_dark for cuts of 1/5/10% (currently 29.45 Âµm at 5%; SI says â30) |
| R40 the 0.02â0.5 M substrate band | either widen to the true range (0.02â6.85 M) or declare the industrial-row exclusion and show the band with them included |
| registry `E0 = 2.0 V`, `i0 = 1.0 mA cmâ»Â²`, `Cell volume / electrode area` | all three are already class *assumption* with citation `--` but carry **no sensitivity bound**. Add one each; for i0 the claim "E_cell insensitive above ~10 mA cmâ»Â²" needs a number (quantify ÎE at i0 = 0.1 and 10) |

### P4 â housekeeping that blocks everything above

1. Six generators hardcode `sys.path.insert(0,"/home/claude/rce")` / `os.chdir("/home/claude/rce/sec4")` and read `reactions_50.csv` from cwd rather than `data/`. **None of them runs on this machine.** `make_figK.py` already has the portable pattern (`HERE`/`SEC4` probing) â apply it to the other 13.
2. `make_figs.py` FIG E reads `julia/npp_support_sweep.csv` and `julia/npp_profiles.csv`; both live in `results/`.
3. `make_figs.py` FIG D and `make_fig_main.py` panel f **re-implement** `cellvoltage.jl` instead of reading `cellvoltage.csv`. They agree to 1e-4 V today; nothing enforces it. Read the CSV.
4. `make_figFG.py` joins `reactions_50.csv` and `tier0_ec_matrix.csv` with `pd.concat(axis=1)` â positional, no key. Verified aligned today (all 50 rows match); make it a keyed merge on `reaction`.
5. Add the 18 `electrolytes.csv` rows that have no registry entry, or delete the unused ones.
6. Re-render `sec4_Fig_sec3` (artifact predates its script) and regenerate `reactions_50.csv` (older than its builder).

---

## 5. VERIFIED CLEAN â the next pass can skip these

Independently recomputed this pass or in the per-generator traces, and reproducing to printed precision:

**Data-file-backed quantities**
- All six architecture medians from `tier0_ec_matrix.csv`: **6.062 / 17.397 / 20.175 / 50.162 / 111.693 / 127.400** mA cmâ»Â². (The brief's "6.1, 17.4, 20.2, 50.2, 112, 127" is correct.)
- All six `â¥ 50 mA cmâ»Â²` counts: **8 / 14 / 15 / 25 / 32 / 34** â appear in `sec4_MAIN_composite` d, `sec4_Fig4A` d, `sec4_Fig_ceiling`, and match SI Â§S7.
- All six `â¥ 25 mA cmâ»Â²` counts (Fig. C header): **11 / 17 / 22 / 31 / 36 / 36**.
- Fig. B's "**28/50** below threshold" in the flow cell; and the 14 reactions stuck below 25 in the best reactor (11 catalyst-, 3 substrate-carried).
- Fig. F: all 50 open circles (`natural`) and all 50 arrowheads (`best`); `rce` wins 47/50, `rde` 3/50; "crosses 50 (34/50)" and "transport-capped by dilute carrier (14/50)".
- Fig. G: all ten bars (6.535 / 19.61 / 24.48 / 61.69 / 188.1 and 0.1652 / 0.4955 / 0.9085 / 2.289 / 5.394) recomputed from LÃ©vÃªque/Eisenberg/Levich; all ten inter-bar multipliers.
- Fig. M: all 14 tier-0 tails, all 14 substrate caps, and **all eight** mediator concentrations (80 / 25 / 2000 / 33 / 40 / 22 / 250 / 100 mol mâ»Â³) against `run_mediated.jl` and Table S6.
- Fig. J / Fig_ceiling: the four fan currents 9.649 / 24.121 / 38.594 / 48.001 (labels 10/24/39/48), i_lim = 48.243 and 16.081, c_surf = 0.8964 and 0.6891, and the surface-concentration extrapolation to 4 decimals.
- Fig. I(b): Î³ = 41.667, i_sh = 1.1578 mA cmâ»Â², the SavÃ©ant âk curve against `saveant_mAcm2`, and all seven plotted markers against `npp_ecprime_sweep.csv`.
- Fig. L: x_k = **167.3 Âµm**, x_dark = **29.45 Âµm**, the in-film flux **2.880 mA cmâ»Â² = 2.21%** â **97.79% exported**, the Fick bound 391.7 and the 785/391.7 = **2.0039** migration factor.
- Fig. A: all seven exemplar curves and all seven concentration labels (0.81 / 1.00 / 6.85 / 0.47 / 0.18 / 0.015 / 0.025 M).
- Voltage stack: all 25 points (5 scenarios Ã i = 10/25/50/100/300) agree with `cellvoltage.csv` to **1e-4 V**.
- Fig. K: **every** number reproduced exactly â Uâ² = 0.01438 / 0.01599 / 0.01292 / 0.00908 / 0.00104 W cmâ»Â²Kâ»Â¹; panel a ceilings 29.5 / 83.9 / 84.9 / 286.5 mA cmâ»Â²; all 20 panel-b ceilings; all 12 panel-c required-Uâ² values; the V^(1/3) sweep. Output is archived to `results/figK_thermal.json`, and the docstring self-declares its own provenance gaps.
- `tier0_ec_matrix.csv` merge provenance: all 48 substitutions from `mediated_ec_matrix.csv` plus the single `wall` fallback (6.947) confirmed.
- Row alignment: `reactions_50.csv` and `tier0_ec_matrix.csv` match on `reaction` for all 50 rows (the positional joins are currently correct).

**Best-sourced numbers in the set (class A with locator â do not re-audit)**
- **25 / 50 mA cmâ»Â² thresholds** â Ferretti *et al.*, *OPRD* **2025**, 29, 322â332, Fig. 11, page-verified; including the derived bins "10/14 < 25", "3 in 25â50", "1/14 > 50".
- **Faraday constant** 96485.332 C molâ»Â¹ â CODATA 2018 (scripts truncate to 96485.33; immaterial).
- **Propylene C_sat = 5 mM** â Sander, *Atmos. Chem. Phys.* **2015**, 15, 4399â4981, via Henry's law.
- **3.0 M LiBr/THF Îº = 3.0 mS cmâ»Â¹** â Peters *et al.*, *Science* **2019**, SM pp. S15, S21 (page-verified).
- **Four boiling points** (THF 66, MeCN 82, DMF 153, water 100 Â°C) and the aqueous conductivities â CRC 97th ed.
- **Uâ² PEM-class plates = 0.30 W cmâ»Â²Kâ»Â¹** â Wallnoefer-Ogris *et al.*, *Front. Chem. Eng.* **2024**, 6, 1384772.
- **Eisenberg RCE correlation** â *J. Electrochem. Soc.* **1954**, 101, 306â320. **Levich RDE** â 1962.
- **0.0625 M biaryl acid** (Zhang/K. Xu/Zeng *OL* 2018, Scheme 1 fn a p. 253) and **5 mM Ni(bpy)âBrâ** (Kawamata *JACS* 2019, Table 4 fn a p. 6399) â both page-verified and both used correctly on Fig. G."
  },
  "workflowProgress": [
    {
      "type": "workflow_phase",
      "index": 1,
      "title": "Trace"
    },
    {
      "type": "workflow_phase",
      "index": 2,
      "title": "Synthesis"
    },
    {
      "type": "workflow_agent",
      "index": 1,
      "label": "trace:ladder-and-tiers",
      "phaseIndex": 1,
      "phaseTitle": "Trace",
      "agentId": "aaad7dd07d4ca9d03",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785600267152,
      "queuedAt": 1785600267151,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "Repo: /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model
Figure generators: figs/make_*.py (14 files). Registry: data/parameters_provenance.csv
(category, parameter, value, units, provenance_class, method_note, citation). Data: data/*.csv.
Physics: julia/*.jl, which emit CSVs consumed by someâ¦",
      "lastProgressAt": 1785601050261,
      "tokens": 97717,
      "toolCalls": 26,
      "durationMs": 783109,
      "resultPreview": "# Provenance trace: `make_fig3_ladder.py`, `make_fig_nd.py`, `make_figL.py`

Files read: the three generators; `data/parameters_provenance.csv`; `data/reactions_50.csv`; `julia/{params,correlations,reactions_table,run_tier0,run_ecprime,run_excell,run_mediated,npp_ecprime}.jl`; `julia/{tier0_matrix,tier0_ec_matrix,npp_ecprime_sweep,excell_profiles}.csv`; `make_si.js`; `AUDIT_REPORT.md`.

**Styling â¦"
    },
    {
      "type": "workflow_agent",
      "index": 2,
      "label": "trace:profiles-and-swarm",
      "phaseIndex": 1,
      "phaseTitle": "Trace",
      "agentId": "aecbe84461a6d211d",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785600267152,
      "queuedAt": 1785600267151,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "Repo: /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model
Figure generators: figs/make_*.py (14 files). Registry: data/parameters_provenance.csv
(category, parameter, value, units, provenance_class, method_note, citation). Data: data/*.csv.
Physics: julia/*.jl, which emit CSVs consumed by someâ¦",
      "lastProgressAt": 1785601006566,
      "tokens": 120549,
      "toolCalls": 33,
      "durationMs": 739414,
      "resultPreview": "## Scope note

Pure styling literals â font sizes, `lw`, `ms`, `alpha`, RGB indices into `rainbow_2`, `figsize`, `dpi`, `w_pad`, text x/y placement coordinates, axis limits and tick counts â are ignored throughout and not listed. Everything below is a number that reaches plotted data, an annotation string, a reference line, a band edge, or a quoted value.

All three scripts hardcode `os.chdir("/hoâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 3,
      "label": "trace:carrier-and-mediator",
      "phaseIndex": 1,
      "phaseTitle": "Trace",
      "agentId": "a0025c8373d0f594d",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785600267152,
      "queuedAt": 1785600267151,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "Repo: /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model
Figure generators: figs/make_*.py (14 files). Registry: data/parameters_provenance.csv
(category, parameter, value, units, provenance_class, method_note, citation). Data: data/*.csv.
Physics: julia/*.jl, which emit CSVs consumed by someâ¦",
      "lastProgressAt": 1785600875558,
      "tokens": 85658,
      "toolCalls": 25,
      "durationMs": 608406,
      "resultPreview": "Both files read in full, all referenced data files loaded, and every computable quantity recomputed. Styling numbers (font sizes, `lw`, `ms`, `alpha`, colours, `set_xlim`/`ylim`, `size_inches`, `dpi`, text x/y placement coordinates, arrow `mutation_scale`, schematic patch geometry in panel a) are excluded throughout and not listed individually â stated once here.

Two structural facts up front:
- â¦"
    },
    {
      "type": "workflow_agent",
      "index": 4,
      "label": "trace:main-and-sec34 (retry 1)",
      "phaseIndex": 1,
      "phaseTitle": "Trace",
      "agentId": "a35953c1fe31ff4e5",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785600267152,
      "queuedAt": 1785600267151,
      "attempt": 2,
      "lastAttemptReason": "stalled",
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "Repo: /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model
Figure generators: figs/make_*.py (14 files). Registry: data/parameters_provenance.csv
(category, parameter, value, units, provenance_class, method_note, citation). Data: data/*.csv.
Physics: julia/*.jl, which emit CSVs consumed by someâ¦",
      "lastProgressAt": 1785601063309,
      "tokens": 121147,
      "toolCalls": 40,
      "durationMs": 796156,
      "resultPreview": "## Preliminary notes on method

Neither script is runnable as shipped (`sys.path.insert(0,"/home/claude/rce"); os.chdir("/home/claude/rce/sec4")`, and `make_fig_main.py` reads `reactions_50.csv` from cwd while the repo copy is at `data/reactions_50.csv`). All verification below was done by re-implementing each computation in Python against the actual data files and comparing to the rendered PNG/SVâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 5,
      "label": "trace:voltage-thermal-4AB",
      "phaseIndex": 1,
      "phaseTitle": "Trace",
      "agentId": "a5d6750d891cf8013",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785600267152,
      "queuedAt": 1785600267151,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "Repo: /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model
Figure generators: figs/make_*.py (14 files). Registry: data/parameters_provenance.csv
(category, parameter, value, units, provenance_class, method_note, citation). Data: data/*.csv.
Physics: julia/*.jl, which emit CSVs consumed by someâ¦",
      "lastProgressAt": 1785601267376,
      "tokens": 128420,
      "toolCalls": 38,
      "durationMs": 1000224,
      "resultPreview": "## Preamble

Pure styling numbers â font sizes, colours, linewidths, marker sizes, alphas, zorders, axis limits/ticks, figure dimensions, schematic rectangle coordinates, jitter offsets â are excluded throughout and not listed again.

Two notes on state: **`figs/make_figK.py` was edited by the concurrent remediation workflow during this audit** (mtime moved 2026-08-01 23:21 â 2026-08-02 00:10). Boâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 6,
      "label": "synthesis",
      "phaseIndex": 2,
      "phaseTitle": "Synthesis",
      "agentId": "a5146767f19d28972",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1785601267380,
      "queuedAt": 1785601267379,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd "/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_â¦",
      "promptPreview": "Repo: /Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model
Figure generators: figs/make_*.py (14 files). Registry: data/parameters_provenance.csv
(category, parameter, value, units, provenance_class, method_note, citation). Data: data/*.csv.
Physics: julia/*.jl, which emit CSVs consumed by someâ¦",
      "lastProgressAt": 1785601972549,
      "tokens": 139009,
      "toolCalls": 26,
      "durationMs": 705169,
      "resultPreview": "# CONSOLIDATED PROVENANCE DELIVERABLE â Section4_Model figure generators

Repo: `/Users/justinbui/Library/CloudStorage/Box-Box/Berkeley_Drive_BackUp/FINAL UNZIP/Takeout/Drive/MIT Postdoc/Organic Electrosynthesis Perspective/Section4_Model`
14 generators in `figs/` â **20 rendered figure files**. Registry: `data/parameters_provenance.csv` (236 rows: 101 measured-lit, **86 lit-representative (abolisâ¦"
    }
  ],
  "totalTokens": 692500,
  "totalToolCalls": 188
}