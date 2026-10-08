# Archive manifest

Nothing in this repository is deleted or overwritten in place. Files that are retired or
superseded are MOVED (or, for files that must keep their production path, COPIED before
edit) into `_archive/<subdir>/` preserving their relative path. Every entry below records
what was archived, when, and why. Reversibility is mandatory: restoring any line here is a
straight `cp` back over the production path.

| Date | Archived path | Original path | Reason |
|---|---|---|---|
| 2026-08-22 | `_archive/figure1_old_pipeline_20260822/Figure1_reproducibility_package/` | `Figure1_reproducibility_package/` | The ENTIRE retired Figure 1 pipeline and its 26,790-record corpus. Superseded by the KHL (Kasie) revision in `Figure_1b_Kasie/`, which Justin made authoritative on 2026-08-22. The KHL corpus is a strict subset (25,941 of 26,790; 849 dropped, none added, evenly spread across classes and years), its classifier keys on bond changes of the MAPPED reactant atoms rather than global bond-count deltas, and its polarity is site-local so RXNMapper's greedy atom-swap artifacts no longer register as redox change. Nothing in the current build reads this directory. **Still bound by the CAS grant terms** — see the NOTICE inside it. |
| 2026-08-22 | `_archive/figure1_old_pipeline_20260822/Polarity_Classifier/` | `Polarity_Classifier/` | The retired 26,790-reaction corpus and its classifier. Its only remaining consumer was `figs/make_fig_trle.py`, whose panel-(a) corpus assertion now re-counts `Figure_1b_Kasie/filtered_echem.parquet` instead. `data/build_reactions50.py` mentions it in a provenance comment only (no read). |
| 2026-08-22 | `_archive/figure1_old_pipeline_20260822/Figure1_preKHL/` | `Figure1/` | The pre-KHL composite script and its renders (md5 `8d05ec3b…`, the artwork embedded in v18/v19), plus `Figure1_caption.md`, whose class list describes the retired taxonomy. `Figure1/` now builds the composite from the KHL pipeline; the caption of record is the manuscript's. |
| 2026-08-22 | `_archive/figs/pre_khl_20260822/make_fig_trle.py`, `sec4_fig_trle.{png,svg}` | `figs/` | Pre-edit snapshot and render carrying the declared corpus count 26,790 and the "94% undivided" sub-label. Re-rendered against the KHL corpus: 25,941 and 95%. Panel (b) is untouched — the transport model did not move. |
| 2026-08-03 | `_archive/figure1_stale_20260803/fig_composite.py` | `Figure1/fig_composite.py` | The 2026-07-13 copy, one edit behind `Figure1_reproducibility_package/fig_composite.py`: its funnel label read `"Commercialized\n(0 of 17 cos.)"` where the authoritative script reads `"Commercialized in pharma\n(0 of 17 cos.)"`. **This single string is the whole of the "Figure 1's artwork is a newer render than its script produces" open item.** The package's script reproduces the manuscript artwork pixel-for-pixel (all 7,372,800 RGBA pixels; verified 2026-08-03); only this stale copy disagreed. `Figure1/` now holds the package's versions plus a `README.md` explaining that the CAS-restricted data inputs stay in the package. |
| 2026-08-03 | `_archive/figure1_stale_20260803/figure1_composite.{png,svg}` | `Figure1/figure1_composite.{png,svg}` | The renders that stale script produced (md5 `7d38748a…`). Superseded by the package render, md5 `8d05ec3b…`, which is byte-identical to the Figure 1 embedded in the manuscript. |
| 2026-08-02 | `_archive/pre_runnability_20260802/figs/make_figFG.py` | `figs/make_figFG.py` | Pre-edit snapshot before the runnability fix. Old lines 6 and 8 hardcoded `sys.path.insert(0,"/home/claude/rce")`, `os.chdir("/home/claude/rce")` and `os.chdir("/home/claude/rce/sec4")`, making the SOLE generator of SI Fig. F and Fig. G unrunnable in this repo and freezing both renders at 2026-07-12. Paths now resolve relative to the file. **Re-run output is geometry-identical to the frozen renders** (all 174 Fig-F and 43 Fig-G SVG path elements match exactly); no plotted value moved. |
| 2026-08-02 | `_archive/pre_runnability_20260802/figs/sec4_figF_gap.{png,svg}`, `.../sec4_figG_waterfall.{png,svg}` | `figs/` | The 2026-07-12 frozen renders, kept as the comparison baseline that establishes the re-run is numerically equivalent. |
| 2026-08-02 | `_archive/pre_runnability_20260802/figs/make_fig4A.py` | `figs/make_fig4A.py` | Pre-edit snapshot before the same `/home/claude/rce` runnability fix (old lines 11 and 13). Re-run output is geometry-identical to the frozen 2026-07-12 render (all 71 SVG path elements match); the only text-layer differences are font-substitution glyph encodings for δ and μ. |
| 2026-08-02 | `_archive/pre_runnability_20260802/figs/sec4_Fig4A.{png,svg}` | `figs/` | Frozen 2026-07-12 renders, kept as the comparison baseline. |
| 2026-08-02 | `_archive/pre_runnability_20260802/data/audit_numeric.py` | `data/audit_numeric.py` | Pre-edit snapshot. The checker could not run from ANY cwd: its reads were split across three roots (`data/` for `reactions_50.csv` + `solvents.csv`, repo root for `julia/*` and `make_si.js`, `figs/` for the three `make_fig*.py` reads in checks 7 and 8). All paths now resolve relative to the file; no check, tolerance or expected value was altered. |
| 2026-08-02 | `_archive/pre_runnability_20260802/make_figs.py` | `figs/make_figs.py` | Pre-edit snapshot. Old lines 168-174 and the `else` branch asserted that Fig. E's inputs `julia/npp_support_sweep.csv` and `npp_profiles.csv` "are NOT present in this repository" and that Fig. E "cannot be regenerated here". False: both are present and are written by `julia/run_section4.jl:57,69`. Claim removed; Fig. E verified to regenerate geometry-identically. |
| 2026-08-02 | `_archive/pre_runnability_20260802/figs/sec4_figE_npp.{png,svg}` | `figs/` | Pre-re-run renders, kept as the baseline proving Fig. E regenerates identically. |
| 2026-08-02 | `_archive/pre_runnability_20260802/AUDIT_REPORT.md` | `AUDIT_REPORT.md` | Pre-edit snapshot before correcting the stale `mu = 0.041` assertion at line 119 (correct value 0.0205; see the SUPERSEDED note now inline there). |
| 2026-08-02 | `_archive/figs/make_fig_main.py` | `figs/make_fig_main.py` | Pre-edit snapshot before remediating figure-audit finding 11 (panel e: analytic total-catalysis substitutions carried no on-figure flag; solver points were selected by a hardcoded `k_M <= 1e3` filter). Also had unrunnable hardcoded `/home/claude/rce` paths. |
| 2026-08-02 | `_archive/figs/sec4_MAIN_composite.png` | `figs/sec4_MAIN_composite.png` | Render of 2026-07-12 superseded by the finding-11 re-render. Panels a–d and f are pixel-identical; only panel e changed. |
| 2026-08-02 | `_archive/figs/sec4_MAIN_composite.svg` | `figs/sec4_MAIN_composite.svg` | As above. |
| 2026-08-02 | `_archive/figs/make_figL.py` | `figs/make_figL.py` | Pre-edit snapshot before remediating figure-audit finding 13 (unsourced `k_L a = 0.05 s^-1` driving the caption claim "bulk G–L capacity ≈ 4.8 A ≫ 1.3 A cell current"). |
| 2026-08-02 | `_archive/figs/sec4_figL_excell.png` | `figs/sec4_figL_excell.png` | Render carrying the retired `k_L a = 0.05 s^-1` caption line. |
| 2026-08-02 | `_archive/figs/sec4_figL_excell.svg` | `figs/sec4_figL_excell.svg` | As above. |
| 2026-08-02 | `_archive/figs/sec4_figH_ecprime.png` | `figs/sec4_figH_ecprime.png` | ORPHAN render of 2026-07-11: existed with no generator anywhere in the tree while being cited by SI §S5.4. Preserved as the historical artifact; the production path is now written by the reconstructed generator `figs/make_figH_ecprime.py`. See that file's header for the reconstruct-vs-delete decision and its evidence. |
| 2026-08-02 | `_archive/figs/sec4_figH_ecprime.svg` | `figs/sec4_figH_ecprime.svg` | As above. |
| 2026-08-02 | `_archive/figs/pre_findings_2to6_20260802/make_figs_sec34.py` | `figs/make_figs_sec34.py` | Pre-edit snapshot before remediating figure-audit findings 2, 3 and 4 (starvation-panel exemplar presented as representative; hardcoded ladder constant `C = 1740`; single "RDE / RCE" anchor at delta = 14 um, which is neither archetype). Also had unrunnable hardcoded `/home/claude/rce` paths. |
| 2026-08-02 | `_archive/figs/pre_findings_2to6_20260802/make_fig_carrier.py` | `figs/make_fig_carrier.py` | Pre-edit snapshot before remediating figure-audit findings 3, 4, 5 and 6 (unsourced catalyst constants D = 6e-6 cm2/s, n_c = 2, C_cat = 10 mM; all-50 median 1740 mislabelled "median substrate"; delta = 14 um "RDE/RCE" tick; mediated plateau band 13-30 with line at 22 drawn from 2 of 8 mediated systems). Also had unrunnable hardcoded `/home/claude/rce` paths. |
| 2026-08-02 | `_archive/figs/pre_findings_2to6_20260802/sec4_Fig_sec3.{png,svg}` | `figs/sec4_Fig_sec3.{png,svg}` | Renders of 2026-07-30 20:52 (which already predated their own generator). Superseded by the findings 2-4 re-render. |
| 2026-08-02 | `_archive/figs/pre_findings_2to6_20260802/sec4_Fig_ceiling.{png,svg}` | `figs/sec4_Fig_ceiling.{png,svg}` | Renders carrying the un-scoped 0.5 M / 1 e- exemplar framing. Superseded by the finding-2 re-render. |
| 2026-08-02 | `_archive/figs/pre_findings_2to6_20260802/sec4_Fig_carrier.{png,svg}` | `figs/sec4_Fig_carrier.{png,svg}` | Renders carrying the retired catalyst ceiling and the 2-of-8 mediated plateau band. Superseded by the findings 3-6 re-render. |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/make_fig_nd.py` | `figs/make_fig_nd.py` | Pre-edit snapshot before remediating figure-audit findings 8 and 9 (panel a: archetype bands hardcoded at x̂ = (2.5,3.5)/(5,15)/(30,100), two of three contradicted by the model, and a legend title still reading μ=0.041 after the constant was corrected to 0.0205; panel b: undisclosed `sw.k_M <= 1e3` filter dropping 3 of 10 solver points, and up to 31% deviation from the drawn asymptote with no disclosure). Also had unrunnable hardcoded `/home/claude/rce` paths. |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/make_fig4B.py` | `figs/make_fig4B.py` | Pre-edit snapshot before remediating findings 8 and 10 (panel c: same contradicted bands and same stale μ=0.041 legend title; panels d/e/f: a second thermal and ohmic model — unregistered electrolytes κ = 0.06/0.35/0.90/20.0 S m⁻¹, 5 mm beaker gap, assumed cooling U′ = 0.020/0.18/0.30 W cm⁻² K⁻¹ — contradicting Fig. K). Also had unrunnable hardcoded `/home/claude/rce` paths. |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/make_figs.py` | `figs/make_figs.py` | Pre-edit snapshot before remediating finding 10 (FIG D: a third thermal model on the same unregistered electrolytes, with panel b comparing Joule heat FLUX in W cm⁻² against three bands whose numbers are heat-transfer COEFFICIENTS in W cm⁻² K⁻¹ — dimensionally incomparable without a ΔT). Also had unrunnable hardcoded `/home/claude/rce` paths and read `reactions_50.csv` from the wrong directory. |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/make_figK.py` | `figs/make_figK.py` | Pre-edit snapshot before extracting its thermal model into `figs/thermal_model.py`. The extraction is numerically a no-op: `results/figK_thermal.json` and the full console dump are byte-identical before and after (verified). |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/sec4_figI_nondim.{png,svg}` | `figs/sec4_figI_nondim.{png,svg}` | Renders carrying the contradicted x̂ bands, the μ=0.041 legend title and the 7-of-10 filtered solver points. RECONSTRUCTED from the archived pre-edit generator rather than copied: the live renders had already been overwritten when the need to archive them was noticed. The reconstruction is deterministic (same generator, same input CSVs, same matplotlib) and is confirmed pre-edit by the literal string `0.041` in the SVG. |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/sec4_Fig4B_ac.{png,svg}` | `figs/sec4_Fig4B_ac.{png,svg}` | As above (panel c). |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/sec4_Fig4B_def.{png,svg}` | `figs/sec4_Fig4B_def.{png,svg}` | As above (panels d/e/f, superseded thermal model). |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/sec4_figD_voltage_joule.{png,svg}` | `figs/sec4_figD_voltage_joule.{png,svg}` | As above (flux-vs-coefficient cooling bands). |
| 2026-08-02 | `_archive/figs/pre_findings_8to10_20260802/sec4_figK_boiloff.{png,svg}` | `figs/sec4_figK_boiloff.{png,svg}` | Copy of the Fig. K render as it stood before the thermal-model extraction. Kept for completeness only — the re-render after extraction is numerically identical. |

---

# Prune of 2026-08-02 — reduce the tree to what the MS and SI require

**Archive root: `_archive/prune_20260802/`.** Paths are mirrored relative to `Section4_Model/`;
files pruned from the sibling `MS Drafts/` folder are mirrored under
`_archive/prune_20260802/MS Drafts/`. A dated root was used rather than `_archive/<rel path>`
directly because `_archive/figs/` already holds pre-edit snapshots under the *same* basenames
(`make_figL.py`, `sec4_figL_excell.png`, `sec4_figH_ecprime.svg`, …); writing into it would have
overwritten them, which the destructive-action rule forbids. Restoring any row below is
`mv "_archive/prune_20260802/<path>" "<path>"`.

**65 files, 18,971,916 B (18.1 MB) moved. Nothing was deleted or overwritten.**

## Basis for archiving a figure generator

Two independent tests, both applied before any move:

1. **Citation test.** The MS (`revised_outline_v17…docx`) embeds exactly six images: Fig 1
   (promise–practice gap), Fig 2 (`sec4_Fig_sec3`), Fig 3 (`sec4_Fig_ceiling`), Fig X/4
   (`combined_figure`), Fig 5 (pre-thermal-split figK) and the appended TRL-E Fig 2. The SI
   (`make_si.js`) names only: **Fig. C, Fig. E-a, Fig. F, Figs. F and G, Fig. H, Fig. K (×15),
   and main-text Fig. 4B-c (×2)**. Every other rendered figure in `figs/` is cited nowhere.
2. **Reference test.** `grep -rn --include=*.py --include=*.js --include=*.jl` across
   `Section4_Model/` and `MS Drafts/` for the generator's module name and for its output
   basenames. A generator was archived only when the sole hits were its own file and its own
   `savefig` call.

## Rows

| Date | Archived path (under `_archive/prune_20260802/`) | Original path | Reason |
|---|---|---|---|
| 2026-08-02 | `figs/make_fig_mediator_k.py` | `figs/make_fig_mediator_k.py` | Figure cited in neither MS nor SI. Closed-form toy: reads zero data files — D, DB, DT, the C_S band and all 16 numbers of the `MED` table live only in the script. Grep: no code reference anywhere; the only mentions are prose in `docs/` and one provenance-note *string literal* in `data/build_param_tables.py:653`, which is documentation, not a dependency. |
| 2026-08-02 | `figs/sec4_Fig_mediator_k.{png,svg}` | `figs/sec4_Fig_mediator_k.{png,svg}` | Sole writer was the generator archived above. |
| 2026-08-02 | `figs/make_fig3_ladder.py` | `figs/make_fig3_ladder.py` | Figure cited in neither MS nor SI. Grep: zero references of any kind in any `.py`/`.js`/`.jl`. Superseded by the ladder panel of `make_figs_sec34.py` (MS Fig 2). |
| 2026-08-02 | `figs/sec4_Fig3_ladder.{png,svg}` | `figs/sec4_Fig3_ladder.{png,svg}` | Sole writer was the generator archived above. |
| 2026-08-02 | `figs/make_figM.py` | `figs/make_figM.py` | Fig. M cited in neither MS nor SI (corroborated by `docs/FIGURE_PROVENANCE_AUDIT.md:274`). Grep: zero code references. |
| 2026-08-02 | `figs/sec4_figM_mediated_ec.{png,svg}` | `figs/sec4_figM_mediated_ec.{png,svg}` | Sole writer was the generator archived above. |
| 2026-08-02 | `figs/make_fig_profiles.py` | `figs/make_fig_profiles.py` | Fig. J cited in neither MS nor SI (same audit line). Grep: referenced only by `figs/mockups/make_mockups.py`, itself archived in this pass. |
| 2026-08-02 | `figs/sec4_figJ_profiles.{png,svg}` | `figs/sec4_figJ_profiles.{png,svg}` | Sole writer was the generator archived above. |
| 2026-08-02 | `figs/make_figL.py` | `figs/make_figL.py` | Fig. L is named in no SI sentence — `grep -niE "Fig\. L\|excell\|figL" make_si.js` returns nothing. Its *numbers* are quoted as prose in §S5.5/§S6.5, and those remain checkable: `julia/run_excell.jl` and `julia/excell_profiles.csv` are RETAINED and are named in the SI's own file manifest at `make_si.js:439`. NOTE: this file received the finding-13 k_L·a remediation earlier today; that edit is preserved intact in the archived copy. |
| 2026-08-02 | `figs/sec4_figL_excell.{png,svg}` | `figs/sec4_figL_excell.{png,svg}` | Sole writer was the generator archived above. |
| 2026-08-02 | `figs/make_fig_nd.py` | `figs/make_fig_nd.py` | Fig. I cited in neither MS nor SI. Its panel (a) is duplicated as main-text Fig. 4B-c, which the SI *does* cite twice — but that panel is drawn by `figs/make_fig4B.py`, which is RETAINED, as is the `figs/archetype_bands.py` module both shared. NOTE: carries today's findings-8/9 remediation, preserved in the archived copy. |
| 2026-08-02 | `figs/sec4_figI_nondim.{png,svg}` | `figs/sec4_figI_nondim.{png,svg}` | Sole writer was the generator archived above. |
| 2026-08-02 | `figs/make_fig_carrier.py` | `figs/make_fig_carrier.py` | `sec4_Fig_carrier` cited in neither MS nor SI. Grep: zero code references. Its `figs/model_medians.py` dependency is RETAINED — `make_figs_sec34.py` (MS Figs 2 and 3) also imports it. NOTE: carries today's findings-3/4/5/6 remediation, preserved in the archived copy. |
| 2026-08-02 | `figs/sec4_Fig_carrier.{png,svg}` | `figs/sec4_Fig_carrier.{png,svg}` | Sole writer was the generator archived above. |
| 2026-08-02 | `figs/_superseded/make_fig4B.py` | `figs/_superseded/make_fig4B.py` | Pre-`_ac`/`_def`-split version of Fig. 4B, superseded by `figs/make_fig4B.py`. `figs/_superseded/make_figK_preThermalSplit.py` was deliberately NOT moved — it is the sole generator of the image printed as MS Fig 5 (inventory flag F1). |
| 2026-08-02 | `figs/_superseded/sec4_Fig4B.{png,svg}` | `figs/_superseded/sec4_Fig4B.{png,svg}` | Renders of the superseded combined 4B figure. |
| 2026-08-02 | `figs/mockups/` (11 files) | `figs/mockups/` | Self-declared internal design documents, not manuscript figures. Grep: `make_mockups.py` is referenced by nothing. 9.1 MB of layout trials. |
| 2026-08-02 | `data/make_fig4B.py` | `data/make_fig4B.py` | Stale duplicate of `figs/make_fig4B.py` carrying `mu=0.041` — the 2×-overstated mediated plateau that was corrected to `mu=0.0205` in the `figs/` copy and in the SI. Dangerous to leave on disk next to the corrected version. |
| 2026-08-02 | `julia/run_scn.jl` | `julia/run_scn.jl` | Emits `mediated_scn.csv`, which does not exist on disk and is read by nothing. Grep: `mediated_scn` appears only inside `run_scn.jl` itself. Not named in the SI file manifest (`make_si.js:439`). |
| 2026-08-02 | `julia/test_g8.jl` | `julia/test_g8.jl` | Developer scratch test for gate G8. The gate itself is exercised by `julia/run_audit.jl`, which is RETAINED and passes 14/14. |
| 2026-08-02 | `make_si.js.bak_preKappaT_20260802`, `make_si.js.bak_preThermalRevision`, `make_si.js.bak_preThreeState` | same | Superseded SI-generator backups; `make_si.js` is the live version. |
| 2026-08-02 | `SI_Section4_Transport_Model_v3.docx.bak_preFigKFix`, `…bak_preThreeState` | same | Superseded SI build backups. |
| 2026-08-02 | `SI_Section4_Transport_Model.docx`, `SI_Section4_Transport_Model_v2.docx`, `SI_Section4_Transport_Model_v4.docx` | same | Older SI builds. Version *names* do not track recency here: `_v4` was built 00:59, `_v3` 01:15. The newest build is kept. |
| 2026-08-02 | `SI_Section4_Transport_Model_v3.docx.pre_mu_formula_rebuild` | `SI_Section4_Transport_Model_v3.docx` | The shipped `.docx` was **stale relative to its own generator**: it still printed μ = C_med D_med/(C_S D_S), whereas `make_si.js:394` had been corrected to μ = n_c C_med D_med/(n_S C_S D_S). Rebuilding `make_si.js` changed exactly this one sentence (3763 text runs, 1 differing). The stale copy is archived here and `SI_Section4_Transport_Model_v3.docx` now holds the fresh build, byte-identical to `data/SI_Section4_Transport_Model.docx`. |
| 2026-08-02 | `~$_Section4_Transport_Model.docx` | same | Word lock file. |
| 2026-08-02 | `__pycache__/`, `figs/__pycache__/`, `.DS_Store`, `figs/.DS_Store` | same | Build and OS detritus. |
| 2026-08-02 | `MS Drafts/SI_Reaction_Engineering_Electrified_Organic_Synthesis{,_v2,_v3}.docx` | same | Superseded by `_v4`, the hand-merged full SI (sole container of §S1 and §S11), which is RETAINED. |
| 2026-08-02 | `MS Drafts/revised_outline_v12…docx`, `…v13…_1.docx`, `…v15…docx` | same | Superseded MS drafts. `v17` (current) and `v14` are RETAINED — v14 per inventory §3d as a container of the TRL-E raster, for which no generator exists. |
| 2026-08-02 | `MS Drafts/EC_prime_mediator_profiles.{py,png,svg}` | same | Content absorbed verbatim into panels d–f of `MS Drafts/combined_figure.py` (MS Fig X/4). The raster appears in no MS version, and the script's own output names (`ecprime_figure.*`) do not even match the on-disk files. Grep: no code references `EC_prime_mediator_profiles`. |

## Deliberately NOT archived, against expectation

- **`figs/_superseded/make_figK_preThermalSplit.py`** — the prune brief allowed `figs/_superseded/`
  to move wholesale, but the inventory's REQUIRED SET and flag F1 make this file the sole
  generator of the 2-panel thermal figure printed as MS Fig 5. Retained.
- **`figs/make_fig4A.py` and `figs/make_fig_main.py`** — both draw figures cited in neither the MS
  nor the SI, and both would otherwise have been archived. **`data/audit_numeric.py:181-182` and
  `:200-201` open them by name** (`for fname in ["make_fig4A.py","make_figs.py","make_fig_main.py"]:
  s = open(FIG(fname)).read()`) with no guard, to cross-check `BARRIER = 50` and nine on-figure
  concentration labels against `reactions_50.csv`. Archiving them would break a provenance
  checker, which the brief forbids. Their renders are kept alongside so the pair stays coherent.

  > **Corrected 2026-08-02.** As originally written this entry read "would have broken a
  > provenance checker" and cited lines `:163` / `:179–180`. Both parts were stale. The line
  > numbers moved when the file was made runnable, and — the substantive point — **the checker
  > was already broken at the time this justification was written**: `audit_numeric.py` could not
  > execute from any working directory, because its reads were split across three different roots
  > (`data/`, the repo root, and `figs/`). So the retention was correct in outcome but rested on a
  > checker that could not have run. That is no longer hypothetical: the paths were fixed on
  > 2026-08-02, the checker now runs cwd-independently, and it does in fact open both files. The
  > retention is now load-bearing for a checker that actually executes.
- **`figs/make_figs.py` outputs Fig. A, Fig. B, Fig. D** — uncited, but written by a generator that
  also writes the SI's Fig. C and Fig. E. Archiving the renders would only have them reappear on
  the next required run.
- **`docs/*` (all five), `data/parameters_provenance.csv`, `AUDIT_REPORT.md`,
  `VERIFIED_CONDITIONS.md`, `EXEMPLAR_PULL_LIST.md`, `Section4_composite_versions.md`,
  `julia/audit_gates.csv`** — provenance material a reviewer needs.
- **`MS Drafts/Figure.pdf`, `TRL-E_figure.png`, `TRL-E_Framework_draft.docx`** — hand-authored or
  unmapped artwork with no generator; irreproducible if lost.

---

# Restores of 2026-08-02 (final verification)

Reversals, performed with the `mv` recipe above. Nothing was deleted or overwritten.

| Date | Restored to | Restored from | Reason |
|---|---|---|---|
| 2026-08-02 | `figs/make_fig_carrier.py` | `_archive/prune_20260802/figs/make_fig_carrier.py` | **The prune's citation test was the wrong test for this file.** The author's final-verification brief names `sec4_Fig_carrier` one of three author-priority figures. It is not cited by the current MS or SI, which is why the prune archived it — but author priority overrides the citation test. Restored and re-run; renders clean and its numbers reconcile to `julia/tier0_ec_matrix.csv`, `julia/mediated_ec_matrix.csv` and `data/reactions_50.csv` (findings 3/4/5/6 remediation intact: substrate-only median 2299 not 1740, six archetype ticks at computed δ not a single δ = 14, all 8 EC′ systems not a 2-of-8 band). |
| 2026-08-02 | `figs/sec4_Fig_carrier.png` | `_archive/prune_20260802/figs/sec4_Fig_carrier.png` | Sole writer is the generator restored above; re-rendered on restore. |
| 2026-08-02 | `figs/sec4_Fig_carrier.svg` | `_archive/prune_20260802/figs/sec4_Fig_carrier.svg` | As above. |

The prune's headline "65 files, 18,971,916 B" describes the state at the moment of the prune and
is left as the historical record; after these three restores `_archive/prune_20260802/` holds 62.

## Archived files that had no manifest row until now

Found by set-differencing `find _archive -type f` against the tables above during the final
verification, and recorded here so the manifest matches what is on disk.

| Date | Archived path | Original path | Reason |
|---|---|---|---|
| 2026-08-02 | `_archive/make_si_pre_F10.js` | `make_si.js` | Pre-edit snapshot of the SI generator taken before the F10 remediation. Was on disk with no row. |
| 2026-08-02 | `_archive/prune_20260802/data/build_param_tables.py.bak_preThreeState` | `data/build_param_tables.py.bak_preThreeState` | Superseded three-state-migration backup, moved in the prune but covered by no row (rows 86–87 name only the `make_si.js` and SI `.docx` backups). |
| 2026-08-02 | `_archive/prune_20260802/data/electrolytes.csv.bak_preThreeState` | `data/electrolytes.csv.bak_preThreeState` | As above. |
| 2026-08-02 | `_archive/prune_20260802/data/parameters_provenance.csv.bak_preThreeState` | `data/parameters_provenance.csv.bak_preThreeState` | As above. |

`_archive/docs/` is an empty directory left by an earlier pass; it holds no files.

---

# Retracted-electrolyte purge of 2026-08-02

`julia/cellvoltage.jl` still hardcoded the electrolytes that SI §S6.1 and the Table S4 caption
retract by name, so anyone running the shipped pipeline regenerated the retracted claim. All six
files below were COPIED before edit (production paths keep their names); nothing was deleted.

| Date | Archived path | Original path | Reason |
|---|---|---|---|
| 2026-08-02 | `_archive/retracted_electrolytes_20260802/julia/cellvoltage.jl` | `julia/cellvoltage.jl` | Pre-edit snapshot. `ELECS` carried 0.1 M Bu4NPF6/THF (0.06 S m⁻¹), 0.1 M Bu4NBF4/DMF (0.35) and 1 M KOH aq (20.0), none of which has a registry row, plus 0.1 M Bu4NBF4/MeCN (0.90), which `figs/thermal_model.py` names as part of the unregistered set the 2026-08 thermal reconciliation replaced. Replaced by the four registry electrolytes of `thermal_model.py` SOLVENTS. |
| 2026-08-02 | `_archive/retracted_electrolytes_20260802/julia/run_section4.jl` | `julia/run_section4.jl` | Pre-edit snapshot. Lines 100–109 printed the worked boil-off example on `ELECS[2]` = 0.1 M Bu4NBF4/DMF at a 5 mm gap (E_cell = 16.8 V, 4.54 K min⁻¹, ~13 min to +60 K) — the exact example §S6.1 retracts and inverts. |
| 2026-08-02 | `_archive/retracted_electrolytes_20260802/julia/cellvoltage.csv` | `julia/cellvoltage.csv` | Superseded output: 60 of its 120 rows were the three unregistered electrolytes, 80 of 120 once the 0.90 S m⁻¹ MeCN rows are counted. |
| 2026-08-02 | `_archive/retracted_electrolytes_20260802/results/cellvoltage.csv` | `results/cellvoltage.csv` | Superseded output, and staler still than the `julia/` copy: it predated the Birch/BASF rows and carried 0.5 M NaOMe/MeOH and 1 M LiBF4/THF as well, i.e. 100 of its 120 rows had no registry entry. Re-synced to the regenerated `julia/cellvoltage.csv`. |
| 2026-08-02 | `_archive/retracted_electrolytes_20260802/julia/{tier0_matrix,npp_support_sweep,npp_profiles}.csv` | `julia/` | Not defective — archived only because `run_section4.jl` rewrites them and the pre-run state had to be recoverable. All three regenerated byte-identical (MD5 unchanged), confirming the edit touched nothing but `cellvoltage.csv` and the worked example. |

---

# Main-text Figure X grounding, 2026-08-02 (`ms-figX-ungrounded`)

`MS Drafts/combined_figure.py` generated the main-text carriers + EC′ figure (embedded in
`revised_outline_v17_RCE_Perspective_JCB_tracked.docx` as `word/media/image4.png`) and **read no
data file**: every curve was a closed form and every printed number a literal. It was rewritten to
read the solver artifacts. Nothing was deleted; the pre-edit generator and its render were COPIED
aside before the rewrite, and the currently embedded artwork is deliberately left in place — the new
render goes to a staging folder so the swap into the .docx is an explicit act by the author.

| Date | Archived path | Original path | Reason |
|---|---|---|---|
| 2026-08-02 | `MS Drafts/combined_figure.py.bak_preGrounding` | `MS Drafts/combined_figure.py` | Pre-rewrite snapshot of the ungrounded generator. Hardcoded, among others: catalyst `i_lim` = 1.2 / 12 mA cm⁻² at δ = 100 / 10 µm (from `n_c` = 2, `D` = 6e-6 cm² s⁻¹, `C_cat` = 10 mM, none with a registry row); direct band 600–15000 and catalyst band 30–300 mA cm⁻² µm; a mediated plateau at exactly 25.0; a "RDE/RCE" δ guide at 13 µm matching neither archetype; and freehand EC′ profiles `clip(1-x/7)`, `exp(-x/6)`, `1-x/2`. Its printed claim "the dilute carrier (3–30 mM) caps it below 25 mA cm⁻²" is contradicted by `julia/tier0_ec_matrix.csv`, which reaches 52.6. |
| 2026-08-02 | `MS Drafts/_archive/figX_preGrounding/combined_figure.{png,svg}` | `MS Drafts/combined_figure.{png,svg}` | Pre-rewrite render. NOT byte-identical to the embedded `image4.png` (MD5 `6901f48b…` vs `6b1f5308…`, 2398×1589 vs 2397×1588): the embedded artwork is an earlier run whose panel c also carried an orange dashed "kinetic plateau" band spanning ≈ 4–180 mA cm⁻² that the on-disk script had since stopped drawing. The v17 caption's "≈ 3.5–177 mA cm⁻²" describes that dropped band, so the shipped generator could not reproduce the shipped figure. |
| 2026-08-02 | `docs/ARCHIVE_MANIFEST.md.bak_preFigX` | `docs/ARCHIVE_MANIFEST.md` | Pre-append snapshot of this manifest. |

**New files created by this pass (additive; nothing overwritten):**

| Path | What |
|---|---|
| `julia/run_ecprime_regimes.jl` | EC′ profile driver covering all three reaction–diffusion regimes. Same base case and same `make_problem` as `run_ecprime.jl`. Written because `npp_ecprime_profiles.csv` holds only k = 1, 1e2, 1e3, which against δ = 100 µm and γ = 41.67 occupy only TWO regimes — the thin-film/shuttle case (δ < x_k) had never been solved, which is why the old panel f was freehand. |
| `julia/npp_ecprime_regimes.csv` | Its output: k = 1e-2 (shuttle), 1e2 (kinetic), 1e3 (thick film), 90 nodes each, carrying x_k, γ·x_k, δ, `i_lim` and the solver's own limiter string on every row. The k = 1e2 and 1e3 blocks reproduce `npp_ecprime_profiles.csv` **bit-for-bit**, which is the regression check that the base case did not drift. |
| `MS Drafts/_replacement_artwork/combined_figure_grounded.{png,svg}` | The grounded render, 2417×1697 px @ 300 dpi. |
| `MS Drafts/_replacement_artwork/REPLACEMENT_NOTE_FigX.md` | Per-panel provenance table, revised caption, swap instructions, and the two body-text issues left for the author (the "Figure 4d" cross-reference points at a panel that never held the 1.7×–20× intensification numbers; they are in panel c). |

---

# Main-text Figure 5 refresh, 2026-08-02 (`ms-fig5-stale`)

The manuscript carried the **pre-remediation** Fig. K as Figure 5. `word/media/image5.png` in
`revised_outline_v17_RCE_Perspective_JCB_tracked.docx` (2880×1320, MD5
`6d9ed9c1350547221937134eb76b552b`) is the output of `figs/_superseded/make_figK_preThermalSplit.py`
— retracted electrolytes (0.1 M Bu4NPF6/THF 0.06 S/m, 0.1 M Bu4NBF4 in DMF 0.35 / MeCN 0.90, aq. KOH
20.0), 5 mm beaker gap, ASSUMED still-air UA = 0.2 W/K, and a panel (b) that crossed solvent,
geometry and cooling on one axis. Everything the remediation fixed (registry electrolytes, 2 cm
canonical gap, sigma from vessel geometry, absolute-ceiling panel b, added active-cooling panel c)
existed only on disk. Confirmed by running the retired generator: it prints 31 / 132 / 139 / 555 /
1153 mA cm^-2, which are the numbers annotated on the printed figure.

Nothing was deleted or overwritten. The retired generator was edited in place for **safety and
runnability only** — its physics is untouched — after a copy was taken.

| Date | Archived path | Original path | Reason |
|---|---|---|---|
| 2026-08-02 | `_archive/pre_runnability_20260802/figs/_superseded/make_figK_preThermalSplit.py` | `figs/_superseded/make_figK_preThermalSplit.py` | Pre-edit snapshot of the retired Fig. K generator, taken before the two hazard fixes below. |
| 2026-08-02 | `docs/ARCHIVE_MANIFEST.md.bak_preFig5` | `docs/ARCHIVE_MANIFEST.md` | Pre-append snapshot of this manifest. |

**Two hazards closed in `figs/_superseded/make_figK_preThermalSplit.py`:**

1. It `savefig()`d to `figs/sec4_figK_boiloff.{png,svg}` — the SAME paths the live `figs/make_figK.py`
   writes — so running it would have silently replaced the current Fig. K with the retracted one. It
   now writes `figs/_superseded/sec4_figK_boiloff_preThermalSplit.{png,svg}`. Verified after running:
   `figs/sec4_figK_boiloff.png` MD5 unchanged at `919513f074d32d929b351a1045198ddc`.
2. It died on a hardcoded `/home/claude/rce` `sys.path`/`chdir`, so the provenance of the printed
   figure could not be reproduced at all. Paths now resolve from `__file__`; it runs and reproduces
   the printed numbers. It stays retired, with a header block saying so.

**New files created by this pass (additive; nothing overwritten):**

| Path | What |
|---|---|
| `figs/make_figK_MSlayout.py` | MS-layout render of the CURRENT remediated Fig. K: same three panels as `make_figK.py`, re-laid onto two rows and drawn at the printed size (6.5 in). Imports `figs/thermal_model.py`; does NOT write `results/figK_thermal.json`, it READS that file and asserts every plotted value against it before saving, so the artwork cannot drift from the published table. |
| `figs/_superseded/sec4_figK_boiloff_preThermalSplit.{png,svg}` | Reproduction of the retracted figure at its own, now-decoupled output path. Kept as the provenance record of what the manuscript currently prints. |
| `MS Drafts/_replacement_artwork/MS_Fig5_figK_boiloff_remediated.{png,svg}` | Drop-in replacement artwork, 3900×3198 px @ 600 dpi = 6.50 × 5.33 in at 100 %. |
| `MS Drafts/_replacement_artwork/REPLACEMENT_NOTE.md` | Swap instructions and dimensions, the layout decision and its justification, a revised caption whose every number is verified against `results/figK_thermal.json`, and the six body-text statements left for the author (notably "one to three orders of magnitude", which the remediated panel b contradicts: passive gap-thinning buys at most 6.2×, and the zero-gap stack ceiling falls). |

**Deliberately NOT changed:** `figs/make_figK.py`, `figs/thermal_model.py`,
`results/figK_thermal.json`, `figs/sec4_figK_boiloff.{png,svg}` and every `.docx`. The pending
constant revisions listed in the `make_figK.py` docstring (vessel area 0.0125 -> 0.00996 m^2, MeCN
T_boil 82.0 -> 81.6 C, natural-convection band edges) remain unapplied, so the replacement artwork
carries exactly the published numbers.

# SI build: two-document staleness trap closed, 2026-08-02 (`si-final-pass`)

`make_si.js` read its two CSVs by bare relative name and wrote `SI_Section4_Transport_Model.docx`
into the **working directory**, so `cd data && node ../make_si.js` was the only invocation that
worked and it deposited the document in `data/`. Meanwhile the repo root held
`SI_Section4_Transport_Model_v3.docx`, which the build never touched. Two SI documents existed,
one stale, neither obviously canonical, and nothing in the tree said which the manuscript shipped.

Every path in `make_si.js` now resolves from `__dirname`, so the build is cwd-independent and has
exactly one output: `Section4_Model/SI_Section4_Transport_Model.docx`. Both former documents are
retired below. **Neither was hand-authored** — both are prior outputs of this same generator,
verified by extracting `word/document.xml` from each: identical 236,903 characters of body text,
same title, and both carrying the pre-pass sentences "Every one of the 49 registered conductivities
is an assumption" and "the CRC concentrative-properties tables carry no conductivity", which this
pass replaced. No author manuscript `.docx` was touched.

| Date | Archived path | Original path | Reason |
|---|---|---|---|
| 2026-08-02 | `_archive/si_docx_20260802/SI_Section4_Transport_Model_v3.docx` | `SI_Section4_Transport_Model_v3.docx` | Stale build output at the repo root that `make_si.js` never updated (build of 2026-08-02 01:44). Superseded by the canonical output at the same directory under the un-suffixed name. Restore with a straight `cp` if the `_v3` naming is wanted back. |
| 2026-08-02 | `_archive/si_docx_20260802/data/SI_Section4_Transport_Model.docx` | `data/SI_Section4_Transport_Model.docx` | The cwd-dependent output location (build of 2026-08-02 02:30), byte-content-equivalent to the `_v3` file above. Removed so that `data/` holds only build inputs and the SI document has one home. |

**Build command, now the only one needed:** `node "<repo>/Section4_Model/make_si.js"` — from any
directory. It prints the citation audit, the absolute output path, and the registry census.

**Related change in the same pass:** every parameter count quoted in the SI prose (§S4 Table S4
caption, §S9 preamble, §S8 census) is now computed from `data/parameters_provenance.csv` at build
time instead of typed in. The hardcoded census `268 / 64 / 79 / 125` had already been falsified by
the κ-registry pass, which moved nine conductivities from assumption to derived without touching
`make_si.js`; the correct figures are `268 / 64 / 88 / 116`. The document can no longer state a
census its own Table S7 contradicts.

# Orphaned `results/*.csv` duplicates retired, 2026-08-02 (`shipped-code-truth`)

`results/` held five CSVs that were stale duplicates of `julia/*.csv` with **no producer**: no
script in the tree writes any CSV to `results/` (all ten `julia/run_*.jl` write beside themselves
and the only `results/` writers are `figs/make_figK.py` and `figs/analysis_kappaT_sensitivity.py`,
which write the two `figK_*.json` files), and no script reads one — a repo-wide grep over `figs/*.py`,
`data/*.py`, `julia/*.jl` and `make_si.js` returns **zero** reads of any `results/*.csv`. Every
consumer reads `julia/`. `make_si.js` L478 nevertheless names these files as shipped **without a
directory**, so a reader given both copies could not tell which was meant — and the copies disagreed:
`results/cellvoltage.csv` still carried κ = 1.80 / 18.00 S m⁻¹ (40 of its 100 rows differ from
`julia/`, the 20 MeCN and 20 aq. NaOH rows) after the κ-sourcing pass moved the registry to
1.89 / 17.80, and `results/npp_ecprime_sweep.csv` disagrees with `julia/` in **all 10** rows.
**Decision: `julia/` is the single source; the `results/` duplicates are retired**, leaving exactly
one copy of each file and making the undirectoried SI reference unambiguous. Nothing was edited to
achieve this and no consumer changed.

| Date | Archived path | Original path | Reason |
|---|---|---|---|
| 2026-08-02 | `_archive/orphaned_results_csv_20260802/results/cellvoltage.csv` | `results/cellvoltage.csv` | Pre-κ-sourcing-pass output (κ = 1.80 / 18.00 S m⁻¹); **40 of 100 rows differ** from `julia/cellvoltage.csv`, which the registry now produces (1.89 / 17.80). Byte-identical to `julia/cellvoltage.csv.bak_preFinalPass`, so this is the same snapshot kept twice. No producer, no consumer. |
| 2026-08-02 | `_archive/orphaned_results_csv_20260802/results/tier0_matrix.csv` | `results/tier0_matrix.csv` | 2026-07-10 copy; 49 of 50 rows differ from the current `julia/tier0_matrix.csv` (verified reproducible byte-identically by `julia/run_tier0.jl` and `julia/run_section4.jl`). No producer, no consumer. |
| 2026-08-02 | `_archive/orphaned_results_csv_20260802/results/npp_profiles.csv` | `results/npp_profiles.csv` | 2026-07-10 copy; 27 of 120 rows differ from `julia/npp_profiles.csv`. `figs/make_figs.py` reads the `julia/` path only. No producer, no consumer. |
| 2026-08-02 | `_archive/orphaned_results_csv_20260802/results/npp_ecprime_sweep.csv` | `results/npp_ecprime_sweep.csv` | 2026-07-10 copy; **all 10 rows differ** from `julia/npp_ecprime_sweep.csv` — the pair the figure audit flagged as diverging by up to 87× at high *k*. Retiring it removes the ambiguity rather than resolving it in prose. No producer, no consumer. |
| 2026-08-02 | `_archive/orphaned_results_csv_20260802/results/npp_ecprime_profiles.csv` | `results/npp_ecprime_profiles.csv` | 2026-07-10 copy; **all 270 rows differ** from `julia/npp_ecprime_profiles.csv`, which `make_fig4B.py`, `make_fig_carrier.py` and `make_figH_ecprime.py` all read. No producer, no consumer. |
| 2026-08-02 | `_archive/orphaned_results_csv_20260802/results/npp_support_sweep.csv` | `results/npp_support_sweep.csv` | The last surviving double copy in `results/`, and the only one that was **byte-identical** to its `julia/` twin (SHA-256 `8666fb87…70d893`, 9 lines, unchanged by the move). Retired for ambiguity, not contradiction: `make_si.js:478` lists `npp_support_sweep.csv` among the SI's shipped outputs **without a directory**, which two copies made unresolvable. Grep evidence that nothing read this one: the sole reader is `figs/make_figs.py:188`, `_E_IN=[P("julia","npp_support_sweep.csv"), …]`, and the sole producer is `julia/run_section4.jl:57`, `open(joinpath(@__DIR__, "npp_support_sweep.csv"), "w")` — both bound to `julia/`. No `.py`, `.jl`, `.js`, `.sh` or `.json` file outside `_archive/` names the `results/` path; the only mentions of it anywhere are prose in `docs/SI_PROVENANCE_AUDIT.md` (lines 219, 477, 697), a closed audit record describing the pre-fix tree, and the retired paragraph below. No producer, no consumer. |

**Nothing is now left in place deliberately.** An earlier version of this note recorded
`results/npp_support_sweep.csv` as the one remaining CSV duplicate and an open item; that item is
closed by the row above, and `results/` now holds no duplicate of any `julia/` artifact. The two
`results/figK_*.json` files stay — they are live outputs with named producers, not duplicates.

---

## Relocation of 2026-08-02 — the Fig. 4 generator joins the other generators

Not an archival. `combined_figure.py` was the only figure generator for this manuscript living
outside `Section4_Model/figs/`; it sat in `MS Drafts/` while reading all of its data from the model
repo. Moved at the author's request so that every generator is in one place. **Nothing was deleted,
and the render is byte-identical after the move** (`combined_figure_grounded.png`, MD5
`c1f5122323ca03aaf7cdedd9af8d74dc`, before and after).

| moved from | moved to | note |
|---|---|---|
| `MS Drafts/combined_figure.py` | `figs/combined_figure.py` | `HERE`/`SEC4` re-anchored: `SEC4` was `dirname(HERE) + "Section4_Model"`, correct only from outside the repo; it is now `dirname(HERE)`. `OUT` was `HERE/_replacement_artwork`, now `HERE`, so renders sit beside the script like every other figure. |
| `MS Drafts/combined_figure.py.bak_preGrounding` | `figs/` | unchanged |
| `MS Drafts/combined_figure.py.bak_preFinalPass` | `figs/` | unchanged |
| `MS Drafts/combined_figure.{png,svg}` | `figs/combined_figure_preGrounding.{png,svg}` | renamed on the move: these are the *pre-grounding* render (MD5 `6901f48b…`), and a bare `combined_figure.png` beside `combined_figure_grounded.png` invited exactly the mix-up that put a stale figure in the manuscript in the first place. An identical copy remains at `MS Drafts/_archive/figX_preGrounding/`. |
| `MS Drafts/_replacement_artwork/combined_figure_grounded.{png,svg}` | `figs/` | the render embedded in v18 |

Verified after the move: runs under `env -i` from a foreign cwd, deposits nothing there, and the
v18 rebuild still embeds MD5 `c1f5122323…` as `word/media/image4.png`.

References updated: `REPLACEMENT_NOTE_FigX.md`, and the docx build script's `FIGX_PNG`.
`MS Drafts/_replacement_artwork/` now holds only the Fig. 5 artwork and the two notes.

## 2026-08-23 — `_archive/ecprime_continuation_20260823/`

| file | why |
|---|---|
| `_dbg_continuation.jl` | Minimal reproduction used to find why `solve_ilim_ec_continued` returned `nothing` inside `run_mediated.jl` while the standalone probe succeeded. The answer was the anchor's starting current — the branch survives continuation from 85% of the anchor limit and dies from 88.8% — which is now handled by the back-off ladder in `npp_ecprime.jl`. Kept because it is the smallest case that exhibits the sensitivity; superseded by `julia/probe_hofmann_homotopy.jl`, which is the maintained diagnostic. |

## 2026-08-24 — `_archive/cell48_superseded_probes_20260824/`

Five one-off probes written while diagnosing the one mediated cell that would not converge,
`Br- oxidation / electrophilic bromination x unstirred batch`. All five are superseded: the cell
turned out to be blocked by a defect in the Newton trust region (`limit_step!`, see
`docs/CELL48_BROMINATION_UNSTIRRED.md` §4), after which the ordinary ramp + c-control path solves
it and no bespoke continuation is needed. They are kept because each one *excludes* a hypothesis,
and that exclusion is what narrowed the search to the trust region.

| file | why archived |
|---|---|
| `dtrack_test.jl` | Fold-tracking in delta from the converged 100 um cell. Died at 141 um. Established that `_push_to_fold` stops where NEWTON stops rather than at the fold — at 120 um it read 56.21 where 1/delta scaling gives 59.38, already 5% short one step in. |
| `dtrack2_test.jl` | Same walk with c-control at every delta instead. Died at 114.7 um: a 5% back-off leaves the state on the fold, which is the worst initial guess for the next delta. |
| `dtrack3_test.jl` | Same again with a 15% back-off, plus a direct test of the existing `solve_ilim_ec_continued` on this cell — which returns **10.483 mA/cm2**, half the cell's own k = 0 floor. That is why delta-continuation never rescued it. |
| `fixedfrac_test.jl` | Continuation at fixed surface depletion, in k and in delta. Route 1 died at k = 0.36 (N=90), 0.218 (N=180), 0.0069 (N=360) — failing EARLIER on finer meshes, which is what first ruled out "the continuation is at fault" and sent the search to the discretisation and then to the step control. |
| `staged_test.jl` | Three-stage fixed-mesh path (k=0 c-control -> walk k at fixed depletion -> walk depletion down). Stages A and B succeed; stage C could not take a single step, at any depletion, from any starting point — the observation that the walk stalls *wherever it starts* and so is not a turning point. |

Maintained diagnostics for this cell, NOT archived: `julia/newton_trace.jl` (the residual/step trace
that identified the cause), `julia/clamp_test.jl` (excludes plain componentwise clamping),
`julia/profile_dump.jl` (front vs mesh spacing), `julia/stageC_test.jl` (iteration-budget control),
`julia/trustregion_verify.jl` (the six-reactor regression), `julia/ktrack_crosscheck.jl` (the
delta-independent ratio used to predict the answer before it was computed).

## 2026-08-31 — orphaned sweep sentinels

`_archive/orphaned_sentinels_20260831/mediated_ec_matrix.csv.ksens`

Left by a k-sensitivity sweep that was SIGKILLed days earlier; no sweep was running when it was
found (`ps` clear). Its content is byte-identical to `mediated_ec_matrix.csv.bak_nuderive`, i.e.
the matrix as it stood before the 2026-08-31 re-solve that made the EC-prime kinematic viscosities
derived — so it was a faithful copy of the then-live file and never held perturbed values.

It had to be retired because `run_gates.sh`'s concurrency guard compares each sentinel against its
live file and refuses to run when they differ. After the legitimate re-solve they differ, so the
orphan would have blocked every future gate run. Moved rather than deleted.

| 2026-09-06 | `MS Drafts/revised_outline_v71_RCE_Perspective_JCB_tracked.docx` -> `_archive/ms_drafts_retired/` | Retired: its single ZOTERO_PREF_1 property (307 chars) exceeded Word's 255-char custom-property limit, so Zotero could not read the document on Refresh. Superseded by v72 (same content, preference split into chunks). |
| 2026-09-06 | `MS Drafts/revised_outline_v72_...docx`, `..._v73_...docx` -> `_archive/ms_drafts_retired/` | Retired: v70 plus a hand-written Zotero preference property that Zotero could not read (v72: 255/52-char chunks; v73: 200/107). Superseded by v70 refreshed by Zotero itself after the preference was set in its Document Preferences dialog (Advanced Options). |
| 2026-09-08 | `MS Drafts/revised_outline_v80_...docx.bak_147fe1e7`, `.bak_88e58e64`, `.bak_946b921b`, `.bak_a98b8142` -> `_archive/v80_intermediate_builds_20260908/` | Retired: four intermediate v80 builds, each kept automatically by `apply_v80_fixes.py` as the script grew from the stability-figure insertion alone to that plus the three cross-reference fields and the seven de-duplicated citation groups. Superseded by the final v80 from the same script. Moved rather than deleted. |

| 2026-09-11 | `julia/run_regimes_delta.jl`, `julia/npp_ecprime_regimes_delta.csv` -> `_archive/fig6_basecase_delta_sweep_20260911/` | The base-case mediator (20 mM / 0.5 M) solved at k = 1e5, 1e2, 1e-2 across seventeen films, drawn as Fig. 6g in v88 for one morning. Replaced by `julia/run_mediated_delta.jl` -> `mediated_ec_delta.csv` (three real mediated rows at their cited k, one per regime; author: "can we do that for the mediated g?"). Kept because it is the only film sweep of the d-f base case. |
| 2026-09-11 | `julia/run_ecprime_regimes.jl`, `julia/npp_ecprime_regimes.csv` -> `_archive/fig6_basecase_regimes_20260911/` | The declared EC' base case (20 mM mediator / 0.5 M substrate / 100 um) solved at k = 1e5, 1e2, 1e-2 with its profiles at the c-control plateau: main-text Fig. 6d-f from v66 to v89 (as Fig. 4d-f before v77). Replaced by `julia/run_mediated_profiles.jl` -> `mediated_ec_profiles.csv`, the three mediated rows of Fig. 6g at their cited k on the measured ANEC film (author, 2026-09-11: "maybe we should show these profiles then for d-f bc they're really applicable?"). The SI's own base case (S5.4, Fig. H, `run_ecprime.jl`) is untouched. Kept because it is the only plateau-resolved solve of the base case at the three panel k. |

| 2026-09-12 | `figs/thermal_model.py`, `figs/make_figK.py`, `figs/make_figK_MSlayout.py` -> `.bak_v94_sevenarch_20260911` beside each; `data/si_sensitivity_bounds.py`, `data/build_param_tables.py`, `run_gates.sh`, `figs/make_fig4B.py`, `figs/make_fig_main.py` -> `.bak_v94_sevenarch_20260912` | The FIVE-reactor thermal table (unstirred beaker, stirred beaker, 5 mm flow cell, 250 um microfluidic, zero-gap PEM stack) and the four DECLARED design currents it was judged against (50, 50, 100, 500 mA cm-2). Two of those reactors were never architectures the transport model carries, and three of the four design currents were ledger-conditional rows. Replaced by Figure 5's own seven transport archetypes plus the zero-gap stack as a marked industrial reference, each run at the median limiting current the published 50-reaction matrix computes for it. Registry rows retired with them: `sigma (5 mm flow cell)`, `Inter-electrode gap (5 mm flow cell)`, `i_design (unstirred beaker)`, `i_design (stirred beaker)`, `i_design (5 mm flow cell)`, `i_design (250 um microfluidic)`; `sigma (250 um microfluidic)` and `h_int (forced flow, 5 mm gap)` renamed to their surviving architectures. The conditional census fell 6 -> 3. Kept as `.bak_` backups in place rather than moved, the convention for a rewritten source. |

| 2026-09-14 | `MS Drafts/SI_Reaction_Engineering_Electrified_Organic_Synthesis_v4.docx` -> `_archive/si_superseded_20260914/` | A STALE SI sitting in the manuscript folder, dated 2026-07-31 (118 kB, 136,776 characters, **zero embedded figures**). It predates the seven-archetype re-anchoring of 2026-09-07 (no ANEC cell, no microfluidic archetype), the catalyst rate-constant work (no S5.7) and the reactor-engineering section (no S8.1 or S3.3). Nothing builds it and nothing reads it; it is the "two SI documents existed" hazard `make_si.js` records in its own header, and anyone assembling a submission package out of `MS Drafts/` would have picked it up instead of the current build. Moved rather than deleted. Replaced beside the manuscript by `MS Drafts/SI_Section4_Transport_Model_v98_20260914.docx`, a DATED EXPORT of the canonical build. |

| 2026-09-14 | `MS Drafts/SI_Section4_Transport_Model_v101_20260914.docx` -> `_archive/si_superseded_20260914/` | Dated export of the SI that accompanied v101. Superseded by the v103 exports (`SI_Section4_Transport_Model_v103_detailed_20260914.docx` and `..._v103_condensed_20260914.docx`): since v101 the SI lost its supporting figures (author ruling), gained S11 (figure construction) and two references, had its headings rewritten, and its S6/S3.2/Table S4/S10 thermal and substrate-D numbers recomputed on the derived sigma. Kept so the v101 package stays reconstructable. |
| 2026-09-14 | `MS Drafts/SI_Section4_Transport_Model_v99_voice_tracked_20260914.docx` -> `_archive/si_superseded_20260914/` | Codex's voice pass applied by hand to a built SI (66 paired tracked edits). All 66 are now in `make_si.js`, whose rebuild reproduced Codex's accepted text character for character, so this hand-edited build output is superseded and must not be edited further. Kept as the record of that pass. |
| 2026-09-14 | `MS Drafts/SI_Section4_Transport_Model_v103_detailed_20260914.docx` -> `_archive/si_superseded_20260914/` | Dated export of the detailed SI that accompanied v103. Superseded by `..._v104_detailed_20260914.docx`: v104 removes the internal label "exemplar-verified" (the S4.2 sentence, and Table S2's concentration-provenance cells reworded at render time) and two uses of "corpus" in S4.1. No number changed. Kept so the v103 package stays reconstructable. |
| 2026-09-14 | `MS Drafts/SI_Section4_Transport_Model_v103_condensed_20260914.docx` -> `_archive/si_superseded_20260914/` | Dated export of the condensed SI that accompanied v103, superseded by `..._v104_condensed_20260914.docx` for the same wording changes (the condensed build carries the S4.2 sentence). Kept for the same reason. |
| 2026-09-14 | `MS Drafts/Cover_letter_scope_note_v104.md` -> `_archive/ms_drafts_retired/` | Draft scope paragraph and pre-submission query for the journal-format question. Superseded by `MS Drafts/Bui_RCE_Perspective_Cover_Letter.docx`, the full cover letter to Prof. Vlachos on the author's NYU letterhead, which carries the scope paragraph. |
| 2026-09-14 | `MS Drafts/revised_outline_v104_RCE_Perspective_JCB_clean.docx` (as built 13:06) -> `_archive/ms_drafts_retired/revised_outline_v104_RCE_Perspective_JCB_clean_prerefresh_20260914.docx` | The accept-all copy made by `apply_v104_fixes.py`. Superseded the same day: the author refreshed Zotero on the tracked v104, accepted every change, edited the abstract and re-embedded Figure 3 from the corrected Illustrator export, so the built clean copy no longer matched. The current clean file is the author's refreshed v104 with Track Changes switched off and nothing else changed. |
| 2026-09-16 | `MS Drafts/For Submission/revised_outline_v105_RCE_Perspective_JCB_tracked.docx` (and the same copy in the Box submission folder and the Box backup's For Submission folder) -> `_archive/ms_drafts_retired/revised_outline_v105_RCE_Perspective_JCB_tracked.docx` | Superseded within the hour by v106 (every cited work moved into the author's own Zotero library, five duplicated references merged, 128 works -> 123) and v107 (Hofmann x_k 2.4 -> 2.3 um). Retired from the submission folders so each holds exactly one tracked manuscript; v105 itself stays in `MS Drafts/` as the build step v104 (author) -> v105 -> v106 -> v107. |
| 2026-09-16 | `MS Drafts/SI_Section4_Transport_Model_v104_{detailed,condensed}_20260914.docx` -> `_archive/si_superseded_20260914/` | Superseded by the v107 exports: SI Table S9 gained eight rows (the RDE and rotating-cylinder cooling shortfalls per solvent) when Section 5's cooling margins were pinned in G-MSDERIVED and G-SIBOUNDS required a published band for them. |
| 2026-09-16 | `revised_outline_v107_RCE_Perspective_JCB_tracked.docx` in the three For Submission folders -> `_archive/ms_drafts_retired/revised_outline_v107_RCE_Perspective_JCB_accepted_20260916.docx` | Superseded by v108 (the Section 7 parallel-screening paragraph rewritten from Rein 2021 and Chen & Mo 2023). The archived copy is the AUTHOR ACCEPTED state he left at 22:51, which is the base v108 is built on; the v107 the build produced stays in `MS Drafts/`. |
| 2026-09-17 | `revised_outline_v108_RCE_Perspective_JCB_tracked.docx` in the three For Submission folders -> `_archive/ms_drafts_retired/` | Superseded by v109 (seven percentages made explicit; citation numbering made canonical after the author moved a block of Section 7). v108 stays in `MS Drafts/` as the build step. |
| 2026-09-17 | `revised_outline_v109_RCE_Perspective_JCB_tracked.docx` (the author 23:32 save) in the three For Submission folders -> `_archive/ms_drafts_retired/revised_outline_v109_RCE_Perspective_JCB_author_2332.docx` | Superseded by v110 (the Wi-eChem platform described; the "wireless" ambiguity with SPECS resolved). The archived copy is the base v110 is built on and is kept in `MS Drafts/` under the same name. |
| 2026-09-17 | `revised_outline_v110_RCE_Perspective_JCB_tracked.docx` (the author 00:13 revision) in the three For Submission folders -> `_archive/ms_drafts_retired/revised_outline_v110_RCE_Perspective_JCB_author_0013.docx` | Superseded by v111 (Section 7.2 rewritten from the author ML-for-stability proposals; one new citation; the orphaned Mo 2020 entry dropped and 28 stale field numbers repaired). The archived copy is the base v111 is built on and is kept in `MS Drafts/` under the same name. |

## 2026-09-17 — `_archive/si_superseded_20260917/`
`SI_Section4_Transport_Model_v107_{detailed,condensed}_20260916.docx` — the dated SI exports that
accompanied v107. Superseded by the v112 exports, which add the §S4.1 "Scale and readiness" note and
carry the reference list reordered after that note moved first appearance of the two scale-up
surveys into §S4. Retired rather than deleted; the canonical build is always
`Section4_Model/SI_Section4_Transport_Model{,_condensed}.docx`.

## si_superseded_20260921/ (2026-09-21)

`SI_Section4_Transport_Model_v112_{detailed,condensed}_20260917.docx` — the dated exports that
accompanied v112–v115. Superseded by the v116 exports, whose condensed Table S6 caption carries the
log–log slope sentence the main text cites it for (the v112 condensed caption had dropped it). Retired
rather than deleted; the canonical build is always `Section4_Model/SI_Section4_Transport_Model{,_condensed}.docx`.

## `_archive/fig6_abundance_variant_20260921/`
`combined_figure_grounded_abundance.{png,svg}` — the FIG6_ABUNDANCE=1 preview rendered for the author on
2026-09-21 while Figure 6 was still locked. Adopted as the shipped render in v118 (identical bytes), so the
switch and the separate filename are gone from `combined_figure.py`; kept only as the record of what was shown
before the author ruled.

## `_archive/si_superseded_20260921/`
`SI_Section4_Transport_Model_v116_{detailed,condensed}_20260921.docx` — the SI exports that accompanied v116/v117.
Superseded by the v118 builds, which correct the §S5.4 sentence that still said the published matrix credits the
molecular-catalyst rows with no rate constant (stale since v88; seven of the eleven carry a measured k).
- `_archive/si_superseded_20260921/SI_Section4_Transport_Model_v118_{detailed,condensed}_20260921.docx` — superseded by the v120
  builds, whose CAS data-access sentence reads "limited data use agreement" to match the manuscript (Connor's #81, accepted).
- `_archive/si_superseded_20260921/SI_Section4_Transport_Model_v120_{detailed,condensed}_20260921.docx` — the dated
  SI exports that sat beside the manuscript while it was v120. Their CONTENT is still current (v121-v126 changed no SI
  text), but the name no longer matches the manuscript they accompany; replaced by the v126-named exports of
  2026-09-21. The canonical builds in `Section4_Model/` are unchanged and remain the ones to trust.
| SI_v46_condensed_20260921.docx | 2026-09-28 | Superseded by SI_condensed_20260928.docx (SI cross-reference fixes: Section 5->6, Section 8->9, Fig. 5->7). Moved out of the send folder so only one condensed SI is staged. |
| codex_lineage_retired_20260928/ | 2026-09-28 | The whole OpenAI/Codex-derived chain, retired at the author's instruction ("Codex sucks never again"). Its prose cuts had also dropped 38 citations (128 works -> 104). Superseded by the JR lineage, built on Jonas Rein's own returned copy. |
| si_superseded_20260928/ | 2026-09-28 | The v126-named dated SI exports (detailed 18cb5ad8, condensed db0f9613), superseded by the JR15-named pair. Two separate changes had left them behind. (i) The detailed build gained the S4.1 "Operating current density" paragraph -- Jonas Rein's `(<XX mA cm-2)`, answered with its denominator and gated by G-DSETJ-SI -- and REFS moved `ferretti2025` to 17 because citing it in S4.1 moves its first appearance. (ii) BOTH builds carry the SI-to-MS cross-reference fixes made earlier the same day, which the v126-named exports were never refreshed for: measured against the archived copy, the condensed text differs by exactly three digits -- Fig. 5 -> Fig. 7 in the Table S9 caption, Section 5 -> Section 6 in the Figure 8 note, Section 8 -> Section 9 in the Figure 10 note -- and nothing else. The canonical builds in `Section4_Model/` remain the ones to trust. |
| resend_superseded_20261004/ | 2026-10-04 | The pre-Leech package manuscripts and two redundant copies, retired when the resend folder was consolidated. (i) `01_Manuscript_preLeech.docx`, `01_Manuscript_Clean_preLeech.docx`, `01_Manuscript_Comments_preLeech.docx` — the three package files before the Leech, Garcia, Petti, Dobbs & Lam citation (React. Chem. Eng. 2020, 5, 977–990) was added at Klavs's request; superseded by the Zotero-refreshed build in which that work is reference 5 and the bibliography runs 1–125. (ii) `01_Manuscript_Comments_leech_20261004_duplicate.docx` — byte-for-byte the same document as `01_Manuscript_with_comments.docx` (identical live text, identical comments.xml, identical comment ranges; only Word's settings.xml and docProps differ), so the package carried the commented manuscript twice under two names. (iii) three `*_leech_refreshed_20261004_snapshot.docx` — snapshots taken during verification, each md5-identical to the live package file it was taken from. Nothing here is unique; every byte survives in the package or in these copies. |
| resend_superseded_20261004/latex_build_files/ | 2026-10-04 | `emit.py`, `extract.py`, `audit_exact.py`, `doc.json` and `template_preamble.tex`, removed from the package's `latex/` folder after Klavs asked whether they were needed. They are not: the preamble is INLINED into `rsc_perspective.tex`, and the folder's remaining five items (`.tex`, `refs.bib`, `rsc.bst`, `figures/`, `head_foot/`) were verified to compile from scratch — no `.aux`, no `.bbl` — to a 24-page PDF whose text is identical to the shipped proof, with 125 entries and no unresolved citations. Each file here is byte-identical to the working copy in `MS Drafts/latex/`, which remains the live build tree; the package's `latex/README.md` was moved there rather than archived. `rsc_perspective.bbl` was ADDED to the package so the reference list is right even if BibTeX is never run, and `latex.zip` was rebuilt from the clean folder (24 entries, no `__MACOSX` forks). |
| fig6_aza_scheme_20261005/ | 2026-10-05 | `aza.png` and `aza.pdf`, the ChemDraw crops of Jonas Rein's Co(salen) aza-Wacker / allylic C-H amination drawing for Figure 6h. Retired when that row left panel (h): the chemistry audit found it has no measured rate constant (it turns over by a heat-driven homolysis, Cai/Xu Nat. Commun. 2021), and a search of the Ni(tet a) literature (Ozaki, Matsushita & Ohmori, Perkin Trans. 1 1993, 649; Olivero, Rolland & Dunach, Organometallics 1998, 17, 3747) found no constant for the obvious substitute either, so the third row became the Ni aryl-aryl homocoupling at k = 10^2. `make_fig6_schemes_cdxml.py` now writes `homo.{png,pdf}` in their place; his source drawing stays in `Figures/Fig6_schemes_JR_20261005.cdxml` and is still matched by signature. The author's 20261005c Illustrator artwork places this crop and is unaffected. |
