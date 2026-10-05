# Figure 1 — the composite that ships in the manuscript

`figure1_composite.png` is the artwork embedded in
`MS Drafts/revised_outline_v20_RCE_Perspective_JCB_tracked.docx`. All four panels come
from the **KHL (Kasie) pipeline** in `../Figure_1b_Kasie/`.

```
../Figure_1b_Kasie/filtered_echem.parquet    25,941 records  -> panels (a), (c), (d)
../Figure_1b_Kasie/polarity_redox.parquet    21,459 scored   -> panel (b)
./electron_transfer_split.csv                                -> panel (c), written by
                                                                mediated_split.py here
```

## Rebuild

```bash
cd Figure1
python mediated_split.py     # -> electron_transfer_split.csv   (KHL corpus)
python fig_composite.py      # -> figure1_composite.{png,svg}
```

`customplot.py` and `Color Swatches from UC Berkeley.xlsx` are kept here so the directory
is self-sufficient; `fig_composite.py` reads the swatch workbook from the working
directory, so run it from inside `Figure1/`.

## The environment is not optional

**The pinned environment exists on this machine: `/opt/anaconda3/envs/fig1_pin`** (built 2026-09-07).
Render with `MPLBACKEND=Agg /opt/anaconda3/envs/fig1_pin/bin/python fig_composite.py`. It carries
python 3.13.15 + the four pins below + mpl_fontkit, seaborn, scipy, sympy, openpyxl. **rdkit is not
in it and is not needed**: `fig_composite.py` imports no rdkit -- it reads the finished parquets, so
the rdkit pin binds `classify.py` / `polarity.py`, which write them.
**Prove the environment by output, not by version strings.** Rendered at the historical 400 dpi this
env reproduces the shipped raster byte for byte (md5 `ec5ecc9f349a17472f3eb719c9939db5`, 0 of
7,372,800 pixels differing); the base 3.12 interpreter differs over 7.27 % of the canvas. Since
2026-09-07 the script writes **600 dpi** (4320 x 3840 px, unchanged 7.20 x 6.40 in), so re-run that
control against `figure1_composite.png.bak_dpi600_20260907` if you ever doubt an environment.


**Pin rdkit, or the figure does not reproduce.** Verified 2026-08-22:

| | |
|---|---|
| python | 3.13 |
| rdkit | **2026.3.5** |
| pandas | 3.0.5 |
| numpy | 2.5.1 |
| pyarrow | 25.0.0 |

On that environment `classify.py` and `polarity.py` reproduce Kasie's shipped parquets
**bit-exactly** — 22,805/22,805 rows for classify (bin and label), 21,459 rows for
polarity (every scored column, `d_ox_site` included).

On **rdkit 2025.03.6** instead, 20 of 21,459 polarity labels drift and 144 `d_ox_site`
values change. The gray band moves 33.56% → 33.53%, which is immaterial to the caption,
but the pipeline is no longer bit-reproducible. The drift is deterministic within an
environment (two runs agreed exactly), and sits in Cyclization / C–C / C–N /
Multicomponent — the ring and multi-bond seeds, where aromaticity perception changed
between rdkit releases. `../Figure_1b_Kasie/requirements.txt` carries the full pin set.

## What the panels say

Printed by `fig_composite.py` on every run, so the caption is checked rather than
transcribed:

```
corpus N=25941, panel-b n=21459
panel b: gray band 7201 / 21459 = 33.56%
         C-N formation  1809  (55.9% of that class, n=3234)
         C-C formation  1647  (40.9% of that class, n=4023)
         Functional group intraconversion 948 (49.7%, n=1906)
panel c: undivided 94.6% (n=10392); galvanostatic 98.4% (n=11124); direct 75.4% (n=24221)
```

`MS Drafts/scripts/verify_v20.py` G6/G7 recompute all of these straight from the KHL
parquets and assert them against the manuscript caption.

## Two things the taxonomy changed

**Cyclization is now a class**, and it takes priority over the bond-forming classes. So
"C–N formation" in panel (b) means **acyclic** C–N formation. The caption says so; without
that sentence the class shares get read against the old taxonomy and misinterpreted.

**The fall-through subclassification is gone.** The retired pipeline re-derived three
classes from the polarity axis and then dropped 485 `EX-*` records. KHL treats redox state
as orthogonal to the transformation — which is the correct relationship — so nothing is
re-derived and there is nothing to exclude.

## CAS grant terms

`../Figure_1b_Kasie/` holds reaction-level CAS data under a limited SciFinder grant. See
its `NOTICE_INTERNAL_DO_NOT_PUBLISH.txt`: aggregate statistics and the rendered figure are
publishable, per-record data is not — not in the paper, the SI, a public repo, or a data
archive. `electron_transfer_split.csv` in this directory is per-record and falls under the
same restriction. Do not publish it.

## The retired pipeline

Everything from the previous Figure 1 — `Figure1_reproducibility_package/`,
`Polarity_Classifier/`, and this directory's pre-KHL script and renders — is in
`Section4_Model/_archive/figure1_old_pipeline_20260822/`. Nothing in the current build
reads any of it. `MS Drafts/scripts/verify_v19.py` still points at the old package and
will no longer run; it is superseded by `verify_v20.py`.
