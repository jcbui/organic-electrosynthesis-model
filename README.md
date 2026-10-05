# Reaction engineering for electrified organic synthesis — model, data and figure generators

This repository holds the transport and thermal model, the page-verified reaction set it runs on,
and the figure generators behind the Perspective *Reaction engineering for electrified organic
synthesis* (J. C. Bui, A. X. Lam, J. Rein, K. Lam, C. W. Coley, K. F. Jensen), submitted to
*Reaction Chemistry & Engineering*.

Everything here is computed. Nothing in the published figures is a typed literal: each median,
threshold count and ceiling in the paper is produced by the code in `model/`, and the repository
carries the gates that assert the documents and the model agree.

## What the model computes

Fifty literature electrosyntheses, each with its concentrations read off the page of its own
exemplar, are solved for the **mass-transport ceiling** `i_lim` in seven reactor archetypes. Three
layers, run in order:

| stage | what it solves | entry point |
|---|---|---|
| 0 | Fick film, migration-free | `model/julia/run_tier0.jl` |
| 1 | Nernst–Planck with migration, 50 × 7 cells | `model/julia/run_all50_np.jl` |
| 2 | EC′ (mediator or catalyst regenerated in the film) | `model/julia/run_mediated.jl`, `run_catalyst_sourced.jl` |

The three layers are merged by `model/data/build_merged_matrix.py` into
`model/julia/tier0_ec_matrix.csv`, the published matrix:

| architecture | film δ | median `i_lim` (mA cm⁻²) | ≥ 25 | ≥ 50 |
|---|---|---|---|---|
| unstirred batch | 228 µm (derived, free convection) | 8.2 | 12/50 | 9/50 |
| stirred batch | 200 µm (measured) | 9.3 | 14/50 | 11/50 |
| recirculating flow | 106.9 µm (measured) | 16.8 | 18/50 | 13/50 |
| ANEC, angled inlet | 36.2 µm (measured) | 44.2 | 31/50 | 24/50 |
| microfluidic, 25 µm gap | 12.5 µm (half-gap, derived) | 110.7 | 36/50 | 34/50 |
| rotating disc, 1600 rpm | Levich | 108.5 | 36/50 | 33/50 |
| rotating cylinder, 3000 rpm | Eisenberg | 121.7 | 36/50 | 34/50 |

A separate lumped energy balance (`model/figs/thermal_model.py`) gives each architecture's
**boil-off ceiling** — the current at which ohmic and kinetic heat raises the electrolyte to its
boiling point — judged against the transport ceiling above.

## Layout

```
model/
  julia/      the solvers (Julia, standard library only) and their CSV outputs
  data/       the reaction set, the parameter provenance registry, and ~110 gates
  figs/       every figure generator and every render
  docs/       the provenance standard and the internal audit record
  results/    JSON artifacts the gates and the documents read
  run_gates.sh    the gate runner
figure1/      the Figure 1 composite (needs the restricted dataset — see below)
```

`model/` is the directory called `Section4_Model/` in the authors' working tree. Docstrings and usage
lines inside the scripts still name it that way, and the dated audit notes in `model/docs/` are left
as they were written; read `cd Section4_Model` as `cd model` throughout.

Two files are worth reading before anything else:

* **`model/docs/PROVENANCE_STANDARD.md`** — the four-state rule every number in the paper obeys:
  **measured** (an external source with a page-level locator), **derived** (a named method from
  inputs that are themselves measured or derived, reproducible from the registry alone),
  **assumption** (no page-anchorable source; must carry a sensitivity and the conclusion that
  depends on it), **schematic** (asserts no magnitude).
* **`model/data/parameters_provenance.csv`** — every parameter the model uses, in one of those four
  states, with its locator or its sensitivity. The Supporting Information's tables are generated
  from this file, so the prose cannot contradict its own tables.

## Requirements

**Julia** — tested on 1.12.5. The solvers import only `LinearAlgebra`, `Printf`, `Statistics`
and `DelimitedFiles`, so there is nothing to install and no `Project.toml`.

**Python** 3.12 with `numpy`, `pandas`, `matplotlib`, `scipy`, `seaborn`, `sympy`, `pillow`,
`openpyxl`, `mpl_fontkit` (Lato and Fira Math), and `pymupdf` for the generators that rasterise
vector artwork. `rdkit` is needed only by `model/data/build_reactions50.py`, and `pyarrow` only by
the scripts that read the restricted dataset.

Figures are rendered deterministically but **not across matplotlib versions**: a different
matplotlib redraws the same data to different pixels, so a render that differs only in pixels from
the committed one is an environment difference, not a result. The renders committed here were made
with Python 3.12.2, matplotlib 3.10.8, numpy 1.26.4 and pandas 2.2.2. Figure 1 is pinned separately
(Python 3.13, matplotlib 3.11.1, numpy 2.5.1, pandas 3.0.5, pyarrow 25.0.0) — see
`figure1/README.md`.

## Quickstart

```bash
# Stage 0, the Fick layer — seconds, and reproduces its committed CSV byte-for-byte
cd model/julia && julia run_tier0.jl

# Figures 4 and 5 (reactor architectures by film; the transport ceiling over 50 reactions)
cd model && MPLBACKEND=Agg python figs/make_figs_sec34.py
```

Both are byte-reproducing: run them in a clean clone and `git status` stays empty apart from
`__pycache__`. (The `.pdf` sidecar of a vector figure carries a creation timestamp and will
differ; the `.png` is the embedded artwork and is the one to compare.) That is the intended check — a generator here is expected to reproduce its committed
output exactly, and `model/data/check_regenerates.py` asserts it for the generated data files.

The full Nernst–Planck and EC′ re-solve takes longer (the catalyst rate-constant sweep is ~37 min)
and the analytic audit `model/julia/run_audit.jl` takes ~15 min; it validates the solvers against
closed-form limits and must report **16/16**.

```bash
cd model && ./run_gates.sh          # the fast tier
cd model && ./run_gates.sh --all    # adds the long sensitivity sweeps
```

**Not every gate can run from this repository.** Roughly a dozen of them read the manuscript or the
Supporting Information `.docx` and assert that the prose matches the model (G-MSDERIVED, G-SIDERIVED,
G-SICOND, G-GHOST, G-XDOC, G-MSKAPPA and others). Those documents are not redistributable here, so
those gates will report a missing input. Everything that checks the model against itself, against
the registry, or against a second code path runs as shipped.

## What is deliberately not here

**The Figure 1 dataset.** Figure 1 is built from 25,941 reaction-level records derived from CAS
content accessed through SciFinder under a limited data use agreement that permits publication of
aggregate statistics and the rendered figure but **not the underlying per-record data**. So
`filtered_echem.parquet` and `polarity_redox.parquet` are withheld, together with the classifier and
polarity scorer that produce them. Five scripts read them and will not run without them:

```
figure1/fig_composite.py          figure1/mediated_split.py
model/figs/make_fig_trle.py       model/data/khl_stratification.py
model/data/dataset_current_density.py
```

Each expects the two parquets in a `Figure_1b_Kasie/` directory at the root of this repository.
`figure1/figure1_composite.png` — the rendered figure — **is** here, as is every aggregate statistic
the paper quotes from that dataset. `.gitignore` excludes `Figure_1b_Kasie/` so that dropping the
restricted data in cannot commit it by accident.

**The exemplar PDFs.** The fifty reactions' concentrations are read from the published papers, and
the text caches used to locate those passages are copyrighted. `model/data/reactions_50.csv` carries
each value with its own locator (journal, year, page, table or figure) in its `conc_provenance`
column, so every read is checkable against the paper itself.

**The manuscript and Supporting Information**, and the author-drawn artwork behind Figures 2, 3, 8
and the Figure 6 overlay.

## Citation

Bui, J. C.; Lam, A. X.; Rein, J.; Lam, K.; Coley, C. W.; Jensen, K. F. *Reaction engineering for
electrified organic synthesis.* Submitted to *Reaction Chemistry & Engineering*, 2026. Please cite
the published article once it appears; cite this repository for the code and model.

## License

MIT, for the code and the generated data in this repository — see `LICENSE`. It does not extend to
the withheld CAS-derived dataset, to the published papers the reaction set is read from, or to the
author-drawn artwork.
