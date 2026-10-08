"""TRL-E readiness figure (Section 8 outlook): (a) readiness distribution of the corpus,
(b) transport ceiling by reactor architecture.

WHY THIS FILE EXISTS. The figure printed in the manuscript (word/media/image6.png,
2229x1062, embedded from the v14 draft onward) had NO generator anywhere in the repo --
an exhaustive grep for "TRL", "Readiness" and "Bench PoC" across every .py/.jl/.js
returned nothing, and no prior Claude Code or Cowork session contains one either. It was
the one manuscript figure that could not be regenerated. This script reconstructs it.

PROVENANCE (docs/PROVENANCE_STANDARD.md: A measured w/ locator, B derived by a named
method from A/B inputs, C declared assumption w/ sensitivity).

Panel (b) -- state B, fully computed. Every bar height and every N/50 count is read at
run time from julia/tier0_ec_matrix.csv (the Tier-0 limiting-current matrix, 50 reactions
x 7 architectures) and asserted against the values the manuscript prints before saving.

Panel (a) -- four counts, NOT computed here. Each is a literal with a named source, and
each is declared in TIERS below:
  * 25,941  state A/B: the row count of Figure_1b_Kasie/filtered_echem.parquet, the
            KHL-revision corpus, re-counted at run time when that file is reachable (it
            lives outside this repo, one level up in the Perspective folder) and
            asserted.
  * ~60     state A: Lehnherr et al., >=20 g demonstrations 2000-2023, as cited on the
            Figure 1d scale-up funnel (Figure1/fig_composite.py).
  * 6       state A: Kelly 2026, kilogram-scale pharmaceutical processes, same funnel.
  * 3       state A: the three commodity processes named in the manuscript body and in
            Table 1 -- adiponitrile electrohydrodimerization (Baizer, J. Electrochem.
            Soc. 1964, 111, 215), Lysmeral methoxylation at BASF (Wiebe & Waldvogel,
            Angew. Chem. Int. Ed. 2018, 57, 5594), and chlor-alkali.
  The panel (a) counts therefore inherit Figure 1's provenance. If its funnel counts move,
  THIS FIGURE MUST BE RE-RENDERED.

Redesign, 2026-09-07 (author instruction: the captions carry the text). Titles, the bar
value labels, the italic sub-labels, the counts row and the separator captions are gone from
the drawing; every number is still computed, printed to stdout, and gated against the
manuscript below. The two dashed separators in (a) and the 25 mA cm-2 rule in (b) remain.

Run:  cd Section4_Model && MPLBACKEND=Agg python figs/make_fig_trle.py
Out:  figs/sec4_fig_trle.{png,svg}
"""
import matplotlib; matplotlib.use("Agg")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, sys, os

# ── portable paths: resolve everything from this file, never the cwd ──
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.chdir(ROOT)          # customplot reads the Berkeley swatch workbook from cwd at import
from customplot import gengrid, rainbow_2
import figstyle as FS

BLUE = rainbow_2[1]; LBLUE = rainbow_2[2]; RED = rainbow_2[5]; ORANGE = rainbow_2[6]

# ═════════════════════ panel (a): declared counts, each with its source ═════════════════
TIERS = [
    ("TRL-E 1–3\nbench",       25941, "corpus row count (Figure 1)"),
    ("TRL-E 4–5\ngram–hectogram", 60, "Lehnherr, ≥20 g demonstrations 2000–23 (Fig. 1d)"),
    ("TRL-E 6–7\nkilogram pilot",  6, "Kelly 2026, kilogram-scale pharma (Fig. 1d)"),
    ("TRL-E 8–9\ncommercial",      3, "three named commodity processes, Table 1"),
]
CORPUS_CSV = os.path.join(os.path.dirname(ROOT), "Figure_1b_Kasie",
                          "filtered_echem.parquet")
SEPARATORS = [(0, "rate / transport ceiling"), (2, "stability + energy ceiling")]

# ═════════════════════ panel (b): computed, nothing hardcoded ══════════════════════════
ARCH = [("natural", "unstirred\nbatch"), ("stirred", "stirred\nbatch"),
        ("flow", "recirc.\nflow cell"),      ("anec", "ANEC\nflow cell"),
        ("micro", "microfluidic\n25 µm"),
        ("rde", "RDE\n1600 rpm"),        ("rce", "rotating\ncylinder")]
THRESHOLD = 25.0        # mA cm-2, the industrial gate used throughout the Perspective

M = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))
if len(M) != 50:
    raise RuntimeError(f"expected 50 reactions in tier0_ec_matrix.csv, got {len(M)}")
med = [M[c].median() for c, _ in ARCH]
cnt = [int((M[c] >= THRESHOLD).sum()) for c, _ in ARCH]

# ═════════════════════ draw ════════════════════════════════════════════════════════════
from matplotlib.colors import LinearSegmentedColormap
CRIMSON = LinearSegmentedColormap.from_list("trle", ["#d3aab1", "#c0392f", "#a20000", "#4a0d18"])

fig, axes, _ = gengrid(2, 1, size_inches=(7.2, 3.3), ticklabel_size=7, genlabels=False)
a, b = np.ravel(np.asarray(axes, dtype=object))

# ---- (a) readiness distribution, log-x horizontal bars ----
ypos = np.arange(len(TIERS))[::-1]
XMAX = 10 ** 5.3
for i, ((lab, n, _src), y) in enumerate(zip(TIERS, ypos)):
    a.barh(y, n - 1, left=1.0, height=0.55, color=CRIMSON(i / (len(TIERS) - 1)), zorder=3)
for idx, txt in SEPARATORS:
    a.axhline(ypos[idx] - 0.5, color="0.45", lw=0.9, ls=(0, (5, 3)), zorder=2)
a.set_xscale("log"); a.set_xlim(1, XMAX); a.set_ylim(-0.6, len(TIERS) - 0.4)
a.set_yticks(ypos); a.set_yticklabels([t[0] for t in TIERS], fontsize=7)
a.tick_params(axis="y", length=0, which="both")
a.set_xlabel("reactions or processes", fontsize=7.5)

# ---- (b) transport ceiling by architecture ----
x = np.arange(len(ARCH)); ytop = max(med) * 1.12
b.bar(x, med, width=0.66, zorder=3, color=[CRIMSON(i / (len(ARCH) - 1)) for i in range(len(ARCH))])
b.axhline(THRESHOLD, color="0.15", lw=1.1, ls=(0, (6, 3)), zorder=2)
b.text(0.015, THRESHOLD + 0.012 * ytop, "25", transform=b.get_yaxis_transform(), fontsize=6,
       color="0.15", ha="left", va="bottom")   # 2026-09-21: at the left, where the two batch bars sit below the line
b.set_xticks(x); b.set_xticklabels([l.replace("\n", " ") for _, l in ARCH], fontsize=6.5, rotation=38, ha="right", rotation_mode="anchor")
# 2026-09-21 (Connor Coley, review comment 59): the two-line labels of adjacent architectures ran together
# ("ANEC flow cell" into "microfluidic 25 um", "1600 rpm" into "cylinder"); rotated so each label has its own footprint
b.set_ylim(0, ytop); b.set_xlim(-0.62, len(ARCH) - 0.38)
b.set_ylabel("median $i_{lim}$ (mA cm$^{-2}$)", fontsize=7.5)
b.tick_params(axis="x", which="minor", bottom=False, top=False)
FS.panel_letter(a, "a)", x=-0.30, y=1.02); FS.panel_letter(b, "b)", x=-0.16, y=1.02)

# ═════════════════════ provenance gate ═════════════════════════════════════════════════
# NOT a self-check: the reference is the DOCUMENT -- the values the manuscript caption, the
# Section 8 body text and SI Table 1 print. If the model moves, this fails at render time.
PUBLISHED = {           # architecture -> (median printed, N/50 printed) in the 2026-10-06 build (the chemistry review:
    # the rAP reduction row in its own THF/EtOH medium drops below 25 in the ANEC cell, 29 -> 28; SI Table S5 prints it)
    "natural": (8.6, 12), "stirred": (9.7, 14), "flow": (17.4, 19), "anec": (44.5, 28),   # chemistry audit pass 1 (2026-10-06):
    "micro": (109, 34), "rde": (104, 34), "rce": (122, 34),                                # rows 7, 14, 23, 34, 35, 39, 41, 46, 48, 50 re-solved
}
stale = []
for (col, lab), m, c in zip(ARCH, med, cnt):
    pm, pc = PUBLISHED[col]
    shown = round(m) if pm >= 100 else round(m, 1)
    if shown != pm:
        stale.append(f"{lab}: model {shown} vs printed {pm} mA/cm2")
    if c != pc:
        stale.append(f"{lab}: model {c}/50 clears {THRESHOLD:.0f} vs printed {pc}/50")
if stale:
    raise AssertionError(
        "the transport model no longer matches what the manuscript prints:\n  "
        + "\n  ".join(stale)
        + "\nUpdate the Fig. 2 caption, the Section 8 paragraph and SI Table 1, "
          "then update PUBLISHED here.")
print(f"provenance gate PASSED: all {len(ARCH)} medians and counts match the printed text")

if os.path.exists(CORPUS_CSV):
    n_corpus = len(pd.read_parquet(CORPUS_CSV, columns=["rxn_id"]))
    if n_corpus != TIERS[0][1]:
        raise AssertionError(
            f"corpus count moved: {n_corpus:,} rows in filtered_echem.parquet vs "
            f"{TIERS[0][1]:,} declared here. Re-check Figure 1 too -- both use it.")
    print(f"corpus re-counted from {os.path.relpath(CORPUS_CSV, ROOT)}: {n_corpus:,} rows")
else:
    print(f"NOTE corpus not reachable at {CORPUS_CSV}; 25,941 carried as declared")

fig.tight_layout(w_pad=2.4)
for ext in ("png", "svg"):
    fig.savefig(os.path.join(HERE, f"sec4_fig_trle.{ext}"), dpi=600, facecolor="white")
print("panel a counts :", " ".join(f"{t[1]:,}" for t in TIERS))
print("panel b medians:", " ".join(f"{m:.2f}" for m in med))
print("panel b >=25   :", " ".join(f"{c}/50" for c in cnt))
print("wrote figs/sec4_fig_trle.{png,svg}")
