"""Section 6 figure: wireless parallel electrolysis (SPECS) and its device-to-device reproducibility.

  (a) the platform: the author's own Illustrator drawing (Figures/SPECS.ai, rendered here at build time,
      never redrawn) -- a 96-well plate, one well holding a SPECS chip under a red LED, the chip enlarged
      (25 Si photodiodes between a Pt(+) and a Pt(-) pad, 2 mm)
  (b) the assay reaction: bromination of 1,3,5-trimethoxybenzene, with the conditions the paper's Fig. 1d prints
  (c) the reproducibility plate: the UPLC yield of that assay in every one of 384 wells (rows A-P x
      columns 1-24), each value printed in its well
  (d) the yield distribution of those 384 wells, the summary written on the panel, and the equivalent
      device current on the top axis

PROVENANCE (docs/PROVENANCE_STANDARD.md). Every number drawn in (b), (c) and (d) is state A:
  B. Górski, ..., J. Rein, ..., S. Lin, "Light-harvesting microelectronic devices for wireless
  electrosynthesis", Nature 2025, 637, 354-361, DOI 10.1038/s41586-024-08373-1.
  * the 384 yields: SI Section 5.4 "Reproducibility studies", printed p. 29 (PDF p. 30), the same table
    that main-text Fig. 1d prints on the plate image (p. 355); extracted once by data/extract_specs_fig1d.py
    into data/specs_fig1d_yields.csv, which this script reads;
  * the summary the paper prints and this script ASSERTS against that table before saving: SI p. 29
    "average of 56.6% ... standard deviation of 2.6% (one device provided a yield more than 3σ smaller
    than the average yield on this plate) ... average current of 7.6 µA with a standard deviation of
    0.3 µA"; main text p. 356 "57(3)%", "7.6 µA ... 0.3 µA", "only one device ... outside the 3σ range", and
    Fig. 1d itself (p. 355) "Yield = 57 ± 3%  Current = 7.6 ± 0.3 μA". The numbers WRITTEN on panel (d) are
    the table's own mean and sd, rounded the way the paper rounds them, after that assertion has passed --
    nothing on the panel is typed;
  * the yield-to-current conversion: SI Section 5.1 (p. 25), the assay "shows a 100% faradaic efficiency"
    and 1.0 F gives 50% yield, i.e. two electrons per bromination; 0.5 µmol TMB per well, 2 h (SI 5.2,
    p. 26; Fig. 1d). So i = yield x 0.5 µmol x 2 F / 7200 s, and the printed 7.6 +/- 0.3 µA must follow;
  * the reaction conditions on panel (b), verbatim from Fig. 1d (p. 355): "TBABr (0.1 M), NMP/H2O (4:1)
    SPECS [Pt(+)|Pt(–)], 630-nm LED, 2 h"; the product drawn is the 2-bromo compound (SI 5.8, p. 33: the
    scale-up gives an 8:1 mixture of the 2-bromo and 2,4-dibromo products).
Panel (a) is a schematic (state S; the one-word tag the standard requires is on it). Its labels are the
author's; the magnitudes it shows (2 mm, 25 photodiodes) are Fig. 1b's (p. 355). Numbers for the caption:
<= 50 µL per well (p. 355), 0.5 µmol per well, 200x to 0.1 mmol with about 100 chips in a 20-mL vial,
6.5 h, 76% isolated yield (Fig. 1d p. 355; p. 356; SI Section 5.8 printed p. 33).

Author instruction of 2026-09-07 for THIS figure: the averages are written on the data panel, every well
carries its value, and the screened reaction is drawn -- as in the paper's own Fig. 1d.

Run:  cd Section4_Model && MPLBACKEND=Agg /opt/anaconda3/bin/python3.12 figs/make_fig_specs.py
Out:  figs/sec6_fig_specs.{png,svg}
"""
import matplotlib; matplotlib.use("Agg")
import csv, os, sys, statistics as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PROJECT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
os.chdir(ROOT)                      # customplot reads the Berkeley swatch workbook from cwd at import
from customplot import rainbow_2    # noqa: E402  (loads the house fonts)
import figstyle as FS               # noqa: E402

RED = rainbow_2[5]
TICK, AX, TAG = 7.0, 8.5, 6.5       # printed at 6.5 in: nothing under 6.5 pt
SCHEMATIC = os.path.join(PROJECT, "Figures", "SPECS.ai")   # the author's drawing; read live, never copied

# ── the data, from the paper's own table ─────────────────────────────────────────────────
rows = [r for r in csv.reader(open(os.path.join(ROOT, "data", "specs_fig1d_yields.csv"))) if not r[0].startswith("#")][1:]
GRID = np.array([[int(v) for v in r[1:]] for r in rows], dtype=float)
assert GRID.shape == (16, 24), GRID.shape
Y = GRID.ravel()
N = Y.size
MEAN, SD = float(Y.mean()), float(st.stdev(Y))
F = 96485.332
N_TMB, N_E, T_S = 0.5e-6, 2, 7200.0                               # 0.5 umol per well, 2 e- per bromination, 2 h
to_uA = lambda y: y / 100.0 * N_TMB * N_E * F / T_S * 1e6
from_uA = lambda i: i * 1e-6 * T_S / (N_TMB * N_E * F) * 100.0
I = to_uA(Y)
I_MEAN, I_SD = float(I.mean()), float(st.stdev(I))
LOW = np.argwhere(GRID < MEAN - 3 * SD)                              # wells more than 3 sigma below the mean
HIGH = np.argwhere(GRID > MEAN + 3 * SD)

# ── the printed summary, asserted against the table (not a self-check: the table is the SI's, the
#    summary is the SI's sentence, and they are compared here) ─────────────────────────────
PRINTED = dict(n=384, mean_pct=56.6, sd_pct=2.6, mean_uA=7.6, sd_uA=0.3, n_low_3sigma=1, main_text_mean=57, main_text_sd=3)
bad = []
if N != PRINTED["n"]: bad.append("n = %d, SI says 384" % N)
if round(MEAN, 1) != PRINTED["mean_pct"]: bad.append("mean %.2f%%, SI says 56.6%%" % MEAN)
if round(SD, 1) != PRINTED["sd_pct"]: bad.append("sd %.2f%%, SI says 2.6%%" % SD)
if round(I_MEAN, 1) != PRINTED["mean_uA"]: bad.append("mean current %.2f uA, SI says 7.6" % I_MEAN)
if round(I_SD, 1) != PRINTED["sd_uA"]: bad.append("current sd %.2f uA, SI says 0.3" % I_SD)
if len(LOW) != PRINTED["n_low_3sigma"] or len(HIGH) != 0: bad.append("%d wells below and %d above 3 sigma; SI says one device below" % (len(LOW), len(HIGH)))
if round(MEAN) != PRINTED["main_text_mean"] or round(SD) != PRINTED["main_text_sd"]: bad.append("main text prints 57(3)%%; table gives %.0f(%.0f)" % (MEAN, SD))
if bad:
    raise AssertionError("the plate table does not reproduce the paper's printed summary:\n  " + "\n  ".join(bad))
print("provenance gate PASSED: n = %d, %.1f +/- %.1f %% (main text 57(3)%%), %.2f +/- %.2f uA, %d well(s) below mean - 3 sigma: %s"
      % (N, MEAN, SD, I_MEAN, I_SD, len(LOW), ["%s%d = %.0f%%" % (chr(65 + r), c + 1, GRID[r, c]) for r, c in LOW]))


# ── (a) the author's drawing, rendered from the Illustrator file ─────────────────────────
LED_RED = (0.847, 0.137, 0.212)                      # the drawing's own LED fill (#D82336), used to find the LED
GLOW_RGB, GLOW_ALPHA, GLOW_SIGMA_PT = (239, 73, 62), 0.45, 28.0   # the drawing's red (#EF493E); peak opacity; spread


def render_schematic(path, dpi=300, pad=4.0):
    """Rasterise the drawn content of the .ai artboard (its content box, not the whole artboard).

    The one thing not taken as drawn is the LED glow. Illustrator flattened that effect into a 111 x 133 px
    raster whose alpha never falls below 7/255 at its edges, so it prints as a translucent rectangle rather
    than a glow (author, 2026-09-07: "should have a diffuse glow coming off the LED but it's a weird
    translucent rectangle"). That image is dropped here and a radial glow is multiplied onto the render,
    centred on the LED dome located by its fill colour; black line work stays black under a multiply."""
    import pymupdf
    pymupdf.TOOLS.mupdf_display_errors(False)          # the file's ICC profile provokes a harmless MuPDF warning
    pg = pymupdf.open(path)[0]
    bb = None
    for it in pg.get_drawings():
        bb = it["rect"] if bb is None else bb | it["rect"]
    for it in pg.get_image_info():
        r = pymupdf.Rect(it["bbox"]); bb = r if bb is None else bb | r
    for b in pg.get_text("blocks"):
        r = pymupdf.Rect(b[:4]); bb = r if bb is None else bb | r
    clip = pymupdf.Rect(bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad) & pg.rect
    # the LED: the union of the shapes filled with the drawing's LED red; the glow raster is the image sitting on it
    led = None
    for it in pg.get_drawings():
        f = it.get("fill")
        if f and max(abs(f[i] - LED_RED[i]) for i in range(3)) < 0.04:
            led = it["rect"] if led is None else led | it["rect"]
    glow_xref = None
    if led is not None:
        for it in pg.get_image_info(xrefs=True):
            if it["xref"] and pymupdf.Rect(it["bbox"]).contains(pymupdf.Point((led.x0 + led.x1) / 2, (led.y0 + led.y1) / 2)):
                glow_xref = it["xref"]
    if glow_xref is not None:
        pg.delete_image(glow_xref)                     # in memory only; the file on disk is never written
    pix = pg.get_pixmap(dpi=dpi, clip=clip, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(float)
    if glow_xref is not None:
        k = dpi / 72.0
        cx, cy = ((led.x0 + led.x1) / 2 - clip.x0) * k, (led.y0 + 0.42 * (led.y1 - led.y0) - clip.y0) * k   # on the dome, not the leads
        yy, xx = np.mgrid[0:pix.height, 0:pix.width]
        a = GLOW_ALPHA * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (GLOW_SIGMA_PT * k) ** 2))
        for ch in range(3):
            arr[:, :, ch] *= 1.0 - a * (1.0 - GLOW_RGB[ch] / 255.0)   # multiply blend: white takes the tint, black stays black
    arr = np.clip(np.rint(arr), 0, 255).astype(np.uint8)
    print("schematic: LED at %s; glow raster %s" % (led and tuple(round(v) for v in led), "replaced by a radial glow" if glow_xref else "not found, drawing taken as is"))
    return arr, clip.width / clip.height, clip


SCHEM, SCHEM_ASPECT, SCHEM_CLIP = render_schematic(SCHEMATIC)
print("schematic: %s, content box %.0f x %.0f pt, rendered %d x %d px" % (os.path.relpath(SCHEMATIC, PROJECT), SCHEM_CLIP.width, SCHEM_CLIP.height, SCHEM.shape[1], SCHEM.shape[0]))

# ── layout, in inches ────────────────────────────────────────────────────────────────────
W = 6.5
CELL = 10.0 / 72.0                                   # one well of the plate: 10 pt square, so a 6.5 pt value fits inside it
PW, PH = 24 * CELL, 16 * CELL                        # the plate
plate_x1 = W - 0.46                                  # colour bar, its tick labels and its axis label to the right
plate_x0 = plate_x1 - PW
plate_y0 = 0.36                                      # column numbers + axis label below
plate_y1 = plate_y0 + PH
left_x0, left_x1 = 0.12, plate_x0 - 0.30             # the reaction scheme and the histogram; row letters sit in the 0.30 gap
rxn_h = 0.85
rxn_y0 = plate_y1 - rxn_h
hist_y1 = rxn_y0 - 0.40                              # room for the µA axis on top of the histogram
hist_x0 = 0.44
schem_w = W - 0.24
schem_h = schem_w / SCHEM_ASPECT
schem_y0 = plate_y1 + 0.32
H = schem_y0 + schem_h + 0.14

fig = plt.figure(figsize=(W, H), dpi=200)
inax = lambda x0, y0, w, h: fig.add_axes([x0 / W, y0 / H, w / W, h / H])
ax_a = inax(0.12, schem_y0, schem_w, schem_h)
ax_b = inax(left_x0, rxn_y0, left_x1 - left_x0, rxn_h)
ax_c = inax(plate_x0, plate_y0, PW, PH)
ax_d = inax(hist_x0, plate_y0, left_x1 - hist_x0, hist_y1 - plate_y0)


def style(ax):
    ax.tick_params(axis="both", which="both", direction="in", top=True, right=True, labelsize=TICK)
    [s.set_linewidth(1.0) for s in ax.spines.values()]


# (a) --------------------------------------------------------------------------------------
ax_a.imshow(SCHEM, interpolation="lanczos", aspect="equal")
ax_a.set_axis_off()
ax_a.text(1.0, 0.0, "schematic", transform=ax_a.transAxes, ha="right", va="top", fontsize=TAG, color="0.55", style="italic")


# (b) the assay reaction --------------------------------------------------------------------
def benzene(ax, cx, cy, r, subs, lw=0.9, color=FS.EDGE, fs=7.0):
    """A Kekulé benzene ring of radius r (data units) with substituent labels at the given vertex angles."""
    ang = np.deg2rad(90 + 60 * np.arange(6))                        # vertices at 90, 150, 210, 270, 330, 30 degrees
    vx, vy = cx + r * np.cos(ang), cy + r * np.sin(ang)
    for k in range(6):
        k2 = (k + 1) % 6
        ax.plot([vx[k], vx[k2]], [vy[k], vy[k2]], color=color, lw=lw, solid_capstyle="round", zorder=3)
        if k % 2 == 0:                                                # the second line of every other bond, drawn inside the ring
            mx, my = (vx[k] + vx[k2]) / 2, (vy[k] + vy[k2]) / 2
            ex, ey = (vx[k2] - vx[k]) * 0.62 / 2, (vy[k2] - vy[k]) * 0.62 / 2
            ux, uy = cx - mx, cy - my; n = np.hypot(ux, uy); ux, uy = ux / n * 0.17 * r, uy / n * 0.17 * r
            ax.plot([mx - ex + ux, mx + ex + ux], [my - ey + uy, my + ey + uy], color=color, lw=lw, solid_capstyle="round", zorder=3)
    for deg, label in subs.items():
        a = np.deg2rad(deg)
        xe, ye = cx + 1.75 * r * np.cos(a), cy + 1.75 * r * np.sin(a)          # where the substituent bond ends
        ax.plot([cx + r * np.cos(a), xe], [cy + r * np.sin(a), ye], color=color, lw=lw, solid_capstyle="round", zorder=3)
        gap, half_O = 0.015, 0.036                                             # inches: clearance to the bond, half the width of an "O" at 7 pt
        if abs(np.cos(a)) < 0.3:                                               # vertical bond: the attached atom (first letter) sits over the bond
            ax.text(xe - half_O, ye + gap * np.sign(np.sin(a)), label, ha="left", va="bottom" if np.sin(a) > 0 else "top", fontsize=fs, color=color, zorder=4)
        elif np.cos(a) > 0:                                                    # bond to the right: label reads outward from the bond end
            ax.text(xe + gap, ye, label, ha="left", va="center", fontsize=fs, color=color, zorder=4)
        else:                                                                  # bond to the left: label written so its last letter (the O) meets the bond
            ax.text(xe - gap, ye, label, ha="right", va="center", fontsize=fs, color=color, zorder=4)


def draw_reaction(ax):
    FS.blank(ax, (0, left_x1 - left_x0), (0, rxn_h))
    r, cy = 0.115, 0.30
    cx_s, cx_p = 0.42, 1.82
    benzene(ax, cx_s, cy, r, {90: "OMe", 210: "MeO", 330: "OMe"})
    benzene(ax, cx_p, cy, r, {90: "OMe", 210: "MeO", 330: "OMe", 30: "Br"})
    FS.arrow(ax, (cx_s + 0.43, cy), (cx_p - 0.43, cy), color=FS.EDGE, lw=0.9, ms=6)
    xm = (cx_s + cx_p) / 2
    for i, line in enumerate(["TBABr (0.1 M)", "NMP/H$_2$O (4:1)", "SPECS [Pt(+)|Pt(−)]", "630-nm LED, 2 h"][::-1]):
        ax.text(xm, cy + 0.075 + i * 0.105, line, ha="center", va="bottom", fontsize=TAG, color="0.25")


draw_reaction(ax_b)

# (c) the plate, every value in its well --------------------------------------------------
YIELD_CMAP = LinearSegmentedColormap.from_list("specs", [FS.ELECTROLYTE, FS.FILM, FS.SLATE])
VMIN, VMAX = 45, 63
im = ax_c.imshow(GRID, cmap=YIELD_CMAP, vmin=VMIN, vmax=VMAX, aspect="equal", interpolation="nearest")
for r in range(16):
    for c in range(24):
        rgb = YIELD_CMAP((GRID[r, c] - VMIN) / (VMAX - VMIN))[:3]
        lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        ax_c.text(c, r, "%d" % GRID[r, c], ha="center", va="center", fontsize=TAG, color="white" if lum < 0.52 else FS.SLATE, zorder=4)
ax_c.set_xticks(range(24)); ax_c.set_xticklabels([str(i + 1) for i in range(24)], fontsize=TAG)
ax_c.set_yticks(range(16)); ax_c.set_yticklabels([chr(65 + i) for i in range(16)], fontsize=TAG)
ax_c.tick_params(length=1.5, pad=1.5, labelsize=TAG)
ax_c.set_xlabel("column", fontsize=AX, labelpad=1); ax_c.set_ylabel("row", fontsize=AX, labelpad=1)
[s.set_linewidth(0.8) for s in ax_c.spines.values()]
cax = inax(plate_x1 + 0.05, plate_y0, 0.07, PH)
cb = fig.colorbar(im, cax=cax, ticks=[46, 50, 54, 58, 62])
cb.ax.tick_params(labelsize=TICK, length=2, pad=1.5); cb.set_label("yield (%)", fontsize=AX, labelpad=2)
cb.outline.set_linewidth(0.6)

# (d) the distribution, with the summary written on it -------------------------------------
bins = np.arange(45.5, 63.6, 1.0)
ax_d.hist(Y, bins=bins, color=FS.FILM, ec="white", lw=0.5, zorder=3)
ax_d.axvline(MEAN, color=FS.SLATE, lw=1.0, ls=(0, (4, 2)), zorder=4)
ax_d.axvspan(MEAN - 3 * SD, MEAN + 3 * SD, color=FS.ELECTROLYTE, alpha=0.5, lw=0, zorder=1)
ax_d.set_xlim(45, 64); ax_d.set_ylim(0, 105); ax_d.set_xticks([46, 50, 54, 58, 62])
ax_d.set_xlabel("yield (%)", fontsize=AX, labelpad=1); ax_d.set_ylabel("devices", fontsize=AX, labelpad=1)
style(ax_d)
ax_d.tick_params(top=False)
sec = ax_d.secondary_xaxis("top", functions=(to_uA, from_uA))
sec.set_xlabel("device current (µA)", fontsize=AX, labelpad=2); sec.tick_params(direction="in", labelsize=TICK)
sec.set_xticks([6.5, 7.0, 7.5, 8.0])
# the summary: the table's own statistics, printed the way the paper rounds them (asserted above)
summary = ["n = %d" % N,
           "%.0f ± %.0f %% yield" % (MEAN, SD),
           "%.1f ± %.1f µA" % (I_MEAN, I_SD),
           r"%d device < mean − 3$\sigma$" % len(LOW)]
ax_d.text(0.04, 0.95, "\n".join(summary), transform=ax_d.transAxes, ha="left", va="top", fontsize=TAG, color=FS.SLATE, linespacing=1.35, zorder=7)

for l, x, y in (("a)", 0.02, H - 0.04), ("b)", 0.02, plate_y1 + 0.06), ("c)", plate_x0 - 0.36, plate_y1 + 0.06), ("d)", 0.02, hist_y1 + 0.30)):
    fig.text(x / W, y / H, l, ha="left", va="top", fontsize=10, fontweight="bold")

for ext in ("png", "svg"):
    fig.savefig(os.path.join(HERE, "sec6_fig_specs." + ext), dpi=600, facecolor="white")
print("caption numbers: %d wells, %.1f +/- %.1f %% yield (57(3)%% as printed), %.1f +/- %.1f uA, one well (%s) %.0f%% = %.1f uA, more than 3 sigma below the mean; "
      "scale-up 0.5 umol per well -> 0.1 mmol (200x) with about 100 chips, 6.5 h, 76%% isolated (main text p. 355-356; SI 5.8 p. 33)"
      % (N, MEAN, SD, I_MEAN, I_SD, ", ".join("%s%d" % (chr(65 + r), c + 1) for r, c in LOW), GRID[LOW[0][0], LOW[0][1]], to_uA(GRID[LOW[0][0], LOW[0][1]])))
print("figure %.2f x %.2f in; wrote figs/sec6_fig_specs.{png,svg}" % (W, H))
