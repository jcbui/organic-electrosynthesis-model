"""Composite Figure 1 for the RCE Perspective intro (§1.1): promise -> practice gap.
a) growth  b) reaction-class  c) undivided/galvanostatic default  d) scale-up funnel.

ALL FOUR PANELS come from the KHL (Kasie) pipeline in ../Figure_1b_Kasie/:

    filtered_echem.parquet   25,941 records   -> panels (a), (c), (d)
    polarity_redox.parquet   21,459 scored    -> panel (b)
    electron_transfer_split.csv                -> panel (c), written by mediated_split.py
                                                  in this directory, on the same corpus

The previous version of this script read the retired pipeline
(classified.parquet + polarity/corpus_polarity_full.parquet + fallthrough_subclass.csv,
26,790 records); it is archived beside its render. See ARCHIVE_MANIFEST for what moved.

Two structural changes follow from the KHL revision, both deliberate:

  * Panel (b)'s classes are the KHL taxonomy, keyed on bond changes of the MAPPED
    reactant atoms rather than global bond-count deltas. Cyclization is a class in its
    own right and takes priority over the bond-formation classes, so "C-N formation"
    here means ACYCLIC C-N formation. The caption says so.
  * The fall-through subclassification is gone. The old script re-derived three classes
    ("Oxidation (FGI)", "Reduction", "Other / redox-neutral") from the polarity axis and
    then dropped 485 EX-* records; KHL treats redox state as orthogonal to the
    transformation, which is the correct relationship, so no re-derivation happens and
    there is nothing to exclude.

Run from this directory:  python fig_composite.py
Needs 'Color Swatches from UC Berkeley.xlsx' in the working directory (customplot).
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

from customplot import gengrid, rainbow_2

HERE = os.path.dirname(os.path.abspath(__file__))
KHL = os.path.join(os.path.dirname(HERE), "Figure_1b_Kasie")

CORPUS = os.path.join(KHL, "filtered_echem.parquet")
POLARITY = os.path.join(KHL, "polarity_redox.parquet")
ETSPLIT = os.path.join(HERE, "electron_transfer_split.csv")

df = pd.read_parquet(CORPUS)
N = len(df)

BLUE = rainbow_2[1]; LBLUE = rainbow_2[2]; RED = rainbow_2[5]; GREEN = rainbow_2[0]
ORANGE = rainbow_2[6]; TEAL = rainbow_2[2]; GREY = (0.72, 0.72, 0.72)

fig, axes, sec = gengrid(2, 2, size_inches=(7.2, 6.4), ticklabel_size=8, label_pos=-0.13,
                         secondary_yaxis=[(0, 0)])
a, b = axes[0]; c, d = axes[1]; seca = sec[0][0]

# ---- a) growth (bars 1998-2026; cumulative includes pre-1998 so it spans all year-resolved) ----
dda = df[df["min_year"].notna()]; pre98 = int((dda.min_year < 1998).sum())
dda = dda[(dda.min_year >= 1998) & (dda.min_year <= 2026)]
yrs = np.arange(1998, 2027)
vals = dda["min_year"].astype(int).value_counts().reindex(yrs, fill_value=0).values
cum = np.cumsum(vals) + pre98
bars = a.bar(yrs, vals, color=BLUE, width=0.85, zorder=3)
bars[-1].set_color(LBLUE); bars[-1].set_hatch("///")
a.set_ylabel("New reactions / year", fontsize=8.5, color=BLUE); a.tick_params(axis="y", colors=BLUE)
a.set_xlabel("Year", fontsize=8.5); a.set_xlim(1999, 2026.7)
seca.plot(yrs, cum, color=RED, lw=1.8, zorder=4); seca.set_ylabel("Cumulative", fontsize=8.5, color=RED)
seca.tick_params(axis="y", colors=RED); seca.set_ylim(0, cum.max() * 1.05)

# ---- b) reaction class, stacked by atom-mapped substrate polarity ----
# One row per reaction that received a site-local polarity call. No re-derivation and no
# exclusions: `label` is the KHL class, `site_label` the KHL polarity.
pol = pd.read_parquet(POLARITY, columns=["rxn_id", "label", "site_label"])
Nb = len(pol)
# Long KHL class names wrapped to keep the quarter-panel legible. Keys must match the
# labels in polarity_redox.parquet exactly; asserted below so a rename cannot pass silently.
WRAP = {
    # Jonas Rein, Figure 1 comment: "use endash for bonds". The four bond-forming
    # classes arrive from polarity_redox.parquet with ASCII hyphens; relabel for display
    # only. "Functional-group" keeps its hyphen -- compound adjective, not a bond.
    "C-C formation": "C–C formation",
    "C-N formation": "C–N formation",
    "C-O formation": "C–O formation",
    "C-S formation": "C–S formation",
    "Functional group intraconversion": "Functional-group\nintraconversion",
    "Multicomponent coupling": "Multicomponent\ncoupling",
    "Other bond formation": "Other bond\nformation",
}
unknown = set(WRAP) - set(pol.label.unique())
if unknown:
    raise AssertionError("WRAP keys not present in polarity_redox.parquet: %s" % sorted(unknown))

orderb = pol.label.value_counts()
labs_raw = orderb.index.tolist()[::-1]
tabb = pd.crosstab(pol.label, pol.site_label).reindex(labs_raw)[["Oxidative", "Redox-neutral", "Reductive"]]
labs = [WRAP.get(x, x) for x in labs_raw]

OXC = RED; NEUC = (0.56, 0.56, 0.54); REDC = BLUE
yb = np.arange(len(labs)); leftb = np.zeros(len(labs))
for col, cc, nm in [("Oxidative", OXC, "net oxidative"), ("Redox-neutral", NEUC, "no net substrate redox"),
                    ("Reductive", REDC, "net reductive")]:
    vv = tabb[col].values.astype(float)
    b.barh(yb, vv, left=leftb, color=cc, height=0.74, zorder=3, edgecolor="white", linewidth=0.7, label=nm)
    tt = tabb.sum(axis=1).values.astype(float)
    for i, (sv, sl, st) in enumerate(zip(vv, leftb, tt)):
        if sv > 0.14 * orderb.max():
            b.text(sl + sv / 2, yb[i], f"{100*sv/st:.0f}%", va="center", ha="center",
                   fontsize=5.0, color="white", zorder=4)
    leftb += vv
totb = tabb.sum(axis=1).values
for i, val in enumerate(totb):
    pct = 100 * val / Nb
    b.text(val + Nb * 0.006, i, (f"{pct:.0f}%" if pct >= 1 else f"{pct:.1f}%"),
           va="center", fontsize=6, color="0.3")
b.set_yticks(yb); b.set_yticklabels(labs, fontsize=6.4); b.tick_params(axis="y", length=0)
b.set_xlabel(f"Reactions (atom-mapped, high-confidence; n = {Nb:,})", fontsize=7.5)
b.set_xlim(0, orderb.max() * 1.18)
b.legend(loc="lower right", fontsize=5.4, frameon=False, borderaxespad=0.15, handlelength=1.0)

# ---- c) engineering default + electron-transfer split ----
n = df["notes"].fillna("").str.lower()
und = n.str.contains(r"undivided").sum(); div = n.str.contains(r"(?<!un)divided cell").sum()
gc = n.str.contains(r"constant current|galvanostat|current in ma").sum()
cp = n.str.contains(r"constant potential|potentiostat").sum()
et = pd.read_csv(ETSPLIT); etd = et[et.et_bin != "no_data"]; net = len(etd)
ndir = int((etd.et_bin == "direct").sum()); nmed = net - ndir
rows = [(und, div, "undivided", "divided"), (gc, cp, "galvanostatic", "potentiostatic"),
        (ndir, nmed, "direct", "mediated")]
for y, (maj, mino, lmaj, lmin) in zip([2, 1, 0], rows):
    tot = maj + mino; pmaj = 100 * maj / tot; pmin = 100 * mino / tot
    c.barh(y, pmaj, color=BLUE, height=0.5, zorder=3, edgecolor="white")
    c.barh(y, pmin, left=pmaj, color=ORANGE, height=0.5, zorder=3, edgecolor="white")
    c.text(pmaj / 2, y, f"{lmaj}  {pmaj:.0f}%", ha="center", va="center", fontsize=7.5, color="white")
    c.text(101, y, f"{lmin} ({pmin:.0f}%)  n={tot:,}", ha="left", va="center", fontsize=6.3, color=ORANGE)
c.set_yticks([2, 1, 0]); c.set_yticklabels(["Cell\narchitecture", "Electrolysis\ncontrol", "Electron\ntransfer"], fontsize=7.5)
c.tick_params(axis="y", length=0); c.set_xlim(0, 100); c.set_ylim(-0.7, 2.7)
c.set_xlabel(f"% of reactions with the relevant\nrecord field (of {N:,} total)", fontsize=7.5)

# ---- d) scale-up funnel tapering to a point ----
ftiers = [dict(label="Distinct reactions\nin the literature", count=f"≈{int(round(N,-3)):,}", color=BLUE),
          dict(label="Demonstrated at ≥20 g scale", count="≈60", color=TEAL),
          dict(label="Kilogram scale in pharma", count="6", color=ORANGE),
          dict(label="Commercialized in pharma\n(0 of 17 companies surveyed)", count="0", color=RED)]
Bd = np.array([math.log10(N), math.log10(60), math.log10(6), 0.30, 0.0]); Bd = Bd / Bd[0] * 1.35
ntt = len(ftiers); ytt = ntt * 1.0; lblx = Bd.max() + 0.32
for i, t in enumerate(ftiers):
    yt = ytt - i; yb_ = ytt - (i + 1); wt, wb = Bd[i], Bd[i + 1]; yc = (yt + yb_) / 2
    d.add_patch(Polygon([(-wt, yt), (wt, yt), (wb, yb_), (-wb, yb_)], closed=True,
                        facecolor=t["color"], edgecolor="white", linewidth=1.1, zorder=3))
    if i < ntt - 1:
        d.text(0, yc, t["count"], ha="center", va="center", fontsize=8, color="white",
               fontweight="bold", zorder=6)
    d.plot([max(wt, wb), lblx - 0.06], [yc, yc], color="0.75", lw=0.5, zorder=2)
    d.text(lblx, yc, t["label"], ha="left", va="center", fontsize=6.6, color="0.15")
tipy = ytt - ntt
d.annotate("", xy=(0, tipy - 0.02), xytext=(0, ytt - (ntt - 1) - 0.12),
           arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.4), zorder=4)
d.text(0.2, tipy + 0.05, "0", ha="left", va="center", fontsize=9, color=RED, fontweight="bold", zorder=6)
d.set_xlim(-Bd.max() - 0.4, lblx + 1.75); d.set_ylim(tipy - 0.35, ytt + 0.2); d.axis("off")
for txt in d.texts:
    if txt.get_text() == "d)":
        txt.set_position((0.0, 1.02))

fig.tight_layout(w_pad=2.2, h_pad=1.8)
pa = a.get_position(); pb = b.get_position(); pc = c.get_position(); pd_ = d.get_position()
cw = 0.35; gap = 0.045
c.set_position([pa.x0, pc.y0, cw, pc.height])
dx0 = pa.x0 + cw + gap
d.set_position([dx0, pd_.y0, (pb.x0 + pb.width) - dx0, pd_.height])
# ---------------------------------------------------------------------------------------
# ENVIRONMENT GUARD -- Figure 1 renders DIFFERENTLY under a different matplotlib/font stack,
# and nothing else notices until verify_v*.py G1 compares the embedded bytes. On 2026-08-26
# this script was run under /opt/anaconda3/bin/python3.12 merely to READ its printed panel-c
# numbers, and it silently overwrote the correct render with one whose md5 differs; the
# authoritative bytes had to be recovered out of the v40 .docx. CLAUDE.md trap 8.
#
# The pins are Figure_1b_Kasie/requirements.txt. Refuse to WRITE off-pin -- the numbers this
# script prints are safe to read anywhere (verify_v40 G6 recomputes them from the parquets),
# it is only the raster that is environment-dependent.
def _env_off_pin():
    import sys as _s
    want = {"matplotlib": "3.11.1", "numpy": "2.5.1", "pandas": "3.0.5", "pyarrow": "25.0.0"}
    bad = []
    if _s.version_info[:2] != (3, 13):
        bad.append("python %d.%d (pinned 3.13)" % _s.version_info[:2])
    for mod, ver in want.items():
        try:
            got = __import__(mod).__version__
        except Exception:
            bad.append("%s missing (pinned %s)" % (mod, ver)); continue
        if got != ver:
            bad.append("%s %s (pinned %s)" % (mod, got, ver))
    return bad

_off = _env_off_pin()
if _off and os.environ.get("FIG1_ALLOW_OFF_PIN") != "1":
    print("\n!! NOT WRITING figure1_composite.png/.svg -- this environment is off-pin:")
    for _b in _off:
        print("     " + _b)
    print("   The raster is environment-dependent; writing here would silently replace a")
    print("   correct render with a different one. Build the pinned env")
    print("   (Figure_1b_Kasie/requirements.txt), or set FIG1_ALLOW_OFF_PIN=1 if you really")
    print("   mean to overwrite. Every NUMBER printed above is unaffected and safe to use.")
    raise SystemExit(0)

fig.savefig(os.path.join(HERE, "figure1_composite.svg"))
fig.savefig(os.path.join(HERE, "figure1_composite.png"), dpi=600)   # 600 dpi for print (author, 2026-09-07); the pinned env is /opt/anaconda3/envs/fig1_pin

# ---- printed so the caption can be checked against the render, never transcribed ----
neu = (pol.site_label == "Redox-neutral").sum()
print("wrote figure1_composite  (corpus N=%d, panel-b n=%d)" % (N, Nb))
print("panel b: gray band %d / %d = %.2f%%" % (neu, Nb, 100 * neu / Nb))
top = pol[pol.site_label == "Redox-neutral"].label.value_counts().head(3)
for k, v in top.items():
    print("         top neutral: %-34s %5d  (%.1f%% of that class, n=%d)"
          % (k, v, 100 * v / (pol.label == k).sum(), (pol.label == k).sum()))
print("panel c: undivided %.1f%% (n=%d); galvanostatic %.1f%% (n=%d); direct %.1f%% (n=%d)"
      % (100 * und / (und + div), und + div, 100 * gc / (gc + cp), gc + cp, 100 * ndir / net, net))
