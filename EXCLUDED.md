# What is withheld from this repository, and why

This repository is assembled from a larger working tree. Four categories are left out. Each entry
says what is missing, why, and what remains in its place, so that a reader can tell a deliberate
omission from an oversight.

## 1. The CAS-derived dataset behind Figure 1

**Withheld:** `filtered_echem.parquet` (25,941 reaction-level records), `polarity_redox.parquet`
(21,459 scored records), the raw SciFinder exports they are built from, and the classifier and
polarity scorer that produce them.

**Why:** these records are derived from CAS content accessed through SciFinder under a limited data
use agreement. It permits publication of **aggregate statistics and the rendered figure**, and not
the underlying per-record data — reaction identifiers, structures, reaction SMILES or per-reaction
condition fields.

**What remains:** the rendered figure (`figure1/figure1_composite.png`), the composite generator and
the mediated/direct split script, and every aggregate the paper quotes (the 25,941 and 21,459 counts,
the class shares, the 94.6 % undivided / 98.4 % galvanostatic / 75.4 % direct shares, the share of
records reporting a current density). The five scripts that read the parquets are shipped and will
raise on the missing files; each expects them in a `Figure_1b_Kasie/` directory at the root of this
repository:

| script | what it needs them for |
|---|---|
| `figure1/fig_composite.py` | all four Figure 1 panels |
| `figure1/mediated_split.py` | the mediated/direct split of panel (c) |
| `model/figs/make_fig_trle.py` | re-counts the corpus for Figure 10 panel (a) and asserts 25,941 |
| `model/data/khl_stratification.py` | the SI §S4.2 class stratification of the fifty-reaction set |
| `model/data/dataset_current_density.py` | the SI's current-density census |

## 2. The exemplar papers

**Withheld:** the ~70 published PDFs the fifty reactions' conditions are read from, and the extracted
text caches (`results/pdftext/`) used to locate the passages.

**Why:** they are copyrighted third-party publications.

**What remains:** every value, with a locator precise enough to check against the paper. The
`conc_provenance` column of `model/data/reactions_50.csv` names the journal, year, page and table or
figure behind each concentration and states the arithmetic where a molarity is computed from a charge
and a volume. `model/data/exemplar_pdf_map.csv` names each row's paper.
`model/docs/LITERATURE_DOI_LIST.md` carries the DOI inventory.

Gates that read the PDFs — the condition anchoring (`check_conditions.py`) and the two exemplar
resolvers — cannot run without them.

## 3. The manuscript and the Supporting Information

**Withheld:** the article and SI `.docx` files, their build and verification scripts, and the LaTeX
typesetting of the proof.

**Why:** unpublished manuscript text, and the SI is a build output whose generator is tied to the
working tree.

**What remains:** everything the documents are generated *from* — the registry, the matrices, the
JSON artifacts in `results/`, and `model/data/ms_phrases.py`, the module that computes every number
and phrase the manuscript prints about the model.

The gates that assert document-and-model agreement read those `.docx` files and so cannot run here:
G-MSDERIVED, G-MSKAPPA, G-MSCITE, G-SIDERIVED, G-SIBOUNDS, G-SIFRESH, G-SICOND, G-SIBIB, G-GHOST,
G-XDOC, G-VOICE, G-STRAT (`--check-si`), G-KSENS-SI, G-DSUBSENS-REG and G-DSETJ-SI. Everything that
checks the model against itself, against the registry or against a second code path runs as shipped,
including the analytic audit `model/julia/run_audit.jl` (16/16) and the regeneration gate
`model/data/check_regenerates.py`.

## 4. Author-drawn artwork

**Withheld:** the Illustrator and ChemDraw sources behind Figures 2, 3 and 8, and the hand-placed
Figure 6 overlay (`Figure6_with_schemes_20261002.pdf`).

**Why:** they are the authors' drawings, not model output.

**What remains:** the generators that build the schemes and rasterise the artwork
(`make_fig2_lato_cdxml.py`, `make_fig_case_studies_cdxml.py`, `make_fig_failure_modes.py`,
`make_fig6_schemes_cdxml.py`, `make_fig6_final.py`) and the six Figure 6 ChemDraw scheme crops in
`model/figs/fig6_schemes/`. Those generators will raise on the missing source files.

---

Nothing in the model layer is withheld. The solvers, the fifty-reaction set, the parameter
provenance registry, the thermal model, every sensitivity sweep and every figure generator are all
here.
