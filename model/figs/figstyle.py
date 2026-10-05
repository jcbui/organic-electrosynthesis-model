"""Shared visual language for the Section 4 figures (redesign of 2026-09-07).

Schematics follow the group's reference drawing: slate electrodes, pale-cyan electrolyte, a beige
separator, glossy spheres, thin cool-grey outlines, and NO text inside the drawing -- every label
lives in the caption. Plot axes keep the customplot house style (ticks in, top/right ticks, 1.25 pt
spines); what changes is that titles, annotation paragraphs and footnotes are gone.

Nothing here reads data. Every quantitative mark on a figure is still computed by the generator
that calls these primitives.
"""
import numpy as np
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch, Ellipse
from matplotlib.path import Path

# ── palette sampled from the reference schematic ─────────────────────────────────────────
SLATE = "#3E4B66"          # working electrode, dark hardware
SLATE_LT = "#5F6E8C"
ELECTRODE = "#D9B44A"      # working electrode: gold, black outline
ELECTRODE_CE = "#CBCFD4"   # counter electrode: silver, black outline
EDGE = "#000000"
STEEL = "#CBD2DE"          # light hardware (flow plates, cylinder body)
STEEL_EDGE = "#8E99AC"
ELECTROLYTE = "#D6EAF6"
FILM = "#8FBDDC"           # diffusion film next to the electrode
MEMBRANE = "#E8E1C8"
MEMBRANE_EDGE = "#CDC4A0"
OUTLINE = "#6B7688"        # thin outlines
RED_SPHERE, RED_HI = "#C8655F", "#EFB3AE"
GRAY_SPHERE, GRAY_HI = "#4B5566", "#98A1B1"
BLUE_SPHERE, BLUE_HI = "#4A86BB", "#B7D3EA"
ORANGE_SPHERE, ORANGE_HI = "#D08A45", "#F1CFA6"
# the ACTIVE form of a carrier is a lighter shade of the same hue (author, 2026-09-09), so the
# half of the cycle it travels reads as one thing and the resting half as another
RED_ACT, RED_ACT_HI = "#E4A19B", "#FBE0DD"
ORANGE_ACT, ORANGE_ACT_HI = "#EAB682", "#FBEBD8"
ARROW = "#5F6E8C"

FILM_CMAP = LinearSegmentedColormap.from_list("film", [FILM, ELECTROLYTE])


# ── schematic primitives (data coordinates; call ax.set_aspect("equal")) ────────────────
def blank(ax, xlim, ylim):
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.axis("off")


def frame(ax, x, y, w, h, fc="white", ec=OUTLINE, lw=0.9, r=0.06, z=1):
    """Rounded cell body."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=%g" % (r * min(w, h)),
                                fc=fc, ec=ec, lw=lw, zorder=z))


def electrolyte(ax, x, y, w, h, z=2):
    ax.add_patch(Rectangle((x, y), w, h, fc=ELECTROLYTE, ec="none", zorder=z))


def film(ax, x, y, w, h, z=3, n=64, flip=False, down=False):
    """Diffusion film: a linear gradient from FILM at the electrode to the bulk colour at x + w
    (flip=True: the electrode is at x + w, so the gradient runs the other way).

    down=True turns the band through 90 degrees for a horizontal electrode -- the rotating disk, whose film lies
    BELOW its face -- so the gradient runs from FILM at y + h down to the bulk colour at y."""
    if w <= 0 or h <= 0:
        return
    if down:
        g = np.linspace(1, 0, n)[:, None]
        ax.imshow(g, extent=(x, x + w, y, y + h), cmap=FILM_CMAP, vmin=0, vmax=1, aspect="equal",
                  interpolation="bilinear", zorder=z)
        return
    g = np.linspace(0, 1, n)[None, :]
    if flip:
        g = g[:, ::-1]
    ax.imshow(g, extent=(x, x + w, y, y + h), cmap=FILM_CMAP, vmin=0, vmax=1, aspect="equal",
              interpolation="bilinear", zorder=z)      # "equal": imshow would otherwise reset the aspect


def electrode(ax, x, y, w, h, color=ELECTRODE, z=4):
    ax.add_patch(Rectangle((x, y), w, h, fc=color, ec=EDGE, lw=0.6, zorder=z))


def membrane(ax, x, y, w, h, z=4):
    ax.add_patch(Rectangle((x, y), w, h, fc=MEMBRANE, ec=MEMBRANE_EDGE, lw=0.6, zorder=z))


def sphere(ax, cx, cy, r, color, hi, z=6):
    """A glossy ball: dark outline so it pops off the pale electrolyte, and a CIRCULAR specular
    highlight up and to the left (author, 2026-09-08 -- the elliptical smear it had before read
    as a reflection of nothing in particular). The highlight is inset so it never touches the
    outline: its far edge sits at 0.75 r."""
    ax.add_patch(Circle((cx, cy), r, fc=color, ec=EDGE, lw=0.5, zorder=z))
    ax.add_patch(Circle((cx - 0.33 * r, cy + 0.33 * r), 0.28 * r, fc=hi, ec="none",
                        alpha=0.9, zorder=z + 1))


def stir_bar(ax, cx, cy, L, r, angle=0.0, z=6, spin=True):
    """A PTFE stir bar: white capsule, black outline, the raised pivot ring at its middle, and an elliptical
    rotation arrow around it."""
    tr = mpl.transforms.Affine2D().rotate_deg_around(cx, cy, angle) + ax.transData
    ax.add_patch(FancyBboxPatch((cx - L / 2, cy - r), L, 2 * r, boxstyle="round,pad=0,rounding_size=%g" % r,
                                fc="white", ec=EDGE, lw=0.6, zorder=z, transform=tr))
    ax.add_patch(Rectangle((cx - 0.09 * L, cy - 1.25 * r), 0.18 * L, 2.5 * r, fc="white", ec=EDGE, lw=0.6,
                           zorder=z + 1, transform=tr))
    if spin:
        spin_arrow(ax, cx, cy, 0.68 * L, 2.6 * r, z=z + 2)


def arrow(ax, p0, p1, color=ARROW, lw=1.1, ms=7, rad=0.0, z=7, style="-|>", shrinkA=0, shrinkB=0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, color=color, lw=lw,
                                 connectionstyle="arc3,rad=%g" % rad, zorder=z, shrinkA=shrinkA, shrinkB=shrinkB))


CLEAR = 0.8                                     # clearance between a sphere's surface and an arrow end, in sphere radii
def _clr(ax, r):
    """CLEAR sphere radii, converted from data units to the points FancyArrowPatch shrinks in."""
    p0 = ax.transData.transform((0.0, 0.0)); p1 = ax.transData.transform((CLEAR * r, 0.0))
    return float(p1[0] - p0[0]) * 72.0 / ax.figure.dpi


def flow_arrows(ax, x0, x1, ys, **kw):
    for y in ys:
        arrow(ax, (x0, y), (x1, y), **kw)


def cylinder(ax, cx, y, w, h, z=5):
    """Side view of a rotating cylinder electrode: a slate body with a lighter axis cap."""
    ax.add_patch(FancyBboxPatch((cx - w / 2, y), w, h, boxstyle="round,pad=0,rounding_size=%g" % (0.45 * w),
                                fc=SLATE, ec="none", zorder=z))
    ax.add_patch(Ellipse((cx, y + h), 0.85 * w, 0.28 * w, fc=SLATE_LT, ec="none", zorder=z + 1))


def spin_arrow(ax, cx, cy, rx, ry, z=7, ms=6, lw=1.0, span=(0.62, 2.35)):
    """A near-closed elliptical arc around (cx, cy) with a tangent arrowhead, suggesting rotation.

    The arc and its head are ONE FancyArrowPatch over a path, so the head sits tangent to the curve and carries no
    tail of its own. Drawing the head as a separate short arrow laid over the arc -- the shape this helper had until
    2026-09-22 -- leaves the arc's own round cap sticking out behind the head, which at Figure 4's cell size reads as
    a blob rather than an arrowhead (author: "arrows look weird"). `ms` is the head size in points and does not scale
    with the arc; `span` is the arc's extent in units of pi."""
    t = np.linspace(span[0] * np.pi, span[1] * np.pi, 120)
    v = np.column_stack([cx + rx * np.cos(t), cy + ry * np.sin(t)])
    ax.add_patch(FancyArrowPatch(path=Path(v, [Path.MOVETO] + [Path.LINETO] * (len(v) - 1)),
                                 arrowstyle="-|>,head_length=0.62,head_width=0.26", mutation_scale=ms,
                                 color=ARROW, lw=lw, zorder=z))


def sign(ax, x, y, s, z=9, size=8):
    """A + or - beside an electrode (anode / cathode). `size` drops for a sign that sits ON a narrow electrode."""
    ax.text(x, y, s, ha="center", va="center", fontsize=size, fontweight="bold", color="black", zorder=z)


# ── plot helpers ─────────────────────────────────────────────────────────────────────────
def panel_letter(ax, s, x=-0.16, y=1.08, size=9.5):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=size, fontweight="bold", va="bottom", ha="right")


def rule_label(ax, y, text, x=None, color="0.35", size=5.5, side="right"):
    """A one-word label sitting on a horizontal reference line at the axes edge."""
    xa = 0.985 if side == "right" else 0.015
    ax.text(xa, y, text, transform=ax.get_yaxis_transform(), fontsize=size, color=color,
            ha="right" if side == "right" else "left", va="bottom")


def legend(ax, handles=None, labels=None, **kw):
    opts = dict(frameon=False, fontsize=5.8, handlelength=1.6, handletextpad=0.5, labelspacing=0.35,
                borderaxespad=0.4)
    opts.update(kw)
    if handles is None:
        return ax.legend(**opts)
    return ax.legend(handles=handles, labels=labels, **opts) if labels else ax.legend(handles=handles, **opts)


# ── the three-carrier schematic (Figure 4a and the carrier figure) ───────────────────────
def carrier_schematic(ax, blue=BLUE_SPHERE, orange=ORANGE_SPHERE, red=RED_SPHERE, tag=True):
    """Three cells, left to right: direct (substrate carried to the electrode, product away),
    mediated EC' (the mediator cycles inside a reaction layer next to the electrode; substrate
    is consumed there), dilute molecular catalyst (sparse carrier, cycled at the electrode).
    No text except the one-word 'schematic' tag the provenance standard requires on a state-S
    panel; the caption names everything else. Cells are tall (0.9 x 1.5) so the panel fills a
    plot-sized slot at equal aspect."""
    W, H, G, Y0 = 0.80, 1.78, 0.12, 0.10
    blank(ax, (0, 3 * W + 2 * G + 0.06), (0, H + 0.20))
    hi = {blue: BLUE_HI, orange: ORANGE_HI, red: RED_HI}
    r = 0.055
    for i in range(3):
        x = 0.03 + i * (W + G)
        frame(ax, x, Y0, W, H)
        ex, ey, ew, eh = x + 0.05, Y0 + 0.05, 0.09, H - 0.10
        electrolyte(ax, ex, ey, W - 0.10, eh)
        if i == 1:
            film(ax, ex + ew, ey, 0.24, eh)
        electrode(ax, ex, ey, ew, eh)
        P = lambda fx, fy: (x + fx * W, Y0 + fy * H)          # cell-relative coordinates
        if i == 0:
            sphere(ax, *P(0.62, 0.72), r, blue, hi[blue]); arrow(ax, P(0.55, 0.72), P(0.20, 0.72), color=blue, lw=1.2)
            sphere(ax, *P(0.80, 0.50), r, blue, hi[blue])
            sphere(ax, *P(0.25, 0.28), r, GRAY_SPHERE, GRAY_HI); arrow(ax, P(0.32, 0.28), P(0.68, 0.28), color=GRAY_HI, lw=1.2)
        elif i == 1:
            sphere(ax, *P(0.22, 0.70), r, orange, hi[orange]); sphere(ax, *P(0.36, 0.38), r, orange, hi[orange])
            arrow(ax, P(0.29, 0.65), P(0.40, 0.44), color=orange, lw=1.1, rad=-0.6, ms=6)
            arrow(ax, P(0.30, 0.37), P(0.17, 0.64), color=orange, lw=1.1, rad=-0.6, ms=6)
            sphere(ax, *P(0.74, 0.54), r, blue, hi[blue]); arrow(ax, P(0.67, 0.54), P(0.45, 0.54), color=blue, lw=1.2)
            sphere(ax, *P(0.84, 0.80), r, blue, hi[blue])
        else:
            for (fx, fy) in ((0.58, 0.82), (0.78, 0.62), (0.62, 0.30), (0.86, 0.86), (0.88, 0.32), (0.72, 0.12)):
                sphere(ax, *P(fx, fy), 0.045, red, hi[red])
            sphere(ax, *P(0.24, 0.62), 0.045, red, hi[red]); sphere(ax, *P(0.31, 0.38), 0.045, red, hi[red])
            arrow(ax, P(0.30, 0.58), P(0.35, 0.43), color=red, lw=1.0, rad=-0.7, ms=5)
            arrow(ax, P(0.26, 0.38), P(0.19, 0.57), color=red, lw=1.0, rad=-0.7, ms=5)
    if tag:
        ax.text(3 * W + 2 * G + 0.06, 0.0, "schematic", ha="right", va="bottom", fontsize=4.8, color="0.55", style="italic")


# ═══════════════════════════════════════════════════════════════════════════════════
# LBL-style carrier schematic (2026-09-08, AUTHOR INSTRUCTION).
#
# The three-cell `carrier_schematic` above draws the same taxonomy at 0.80 x 1.78 per cell
# with NO text, and in a near-square grid slot at equal aspect it letterboxes into about a
# third of its space. The author's direction is the boundary-layer idiom of his earlier
# papers: the panel runs the FULL WIDTH of the figure, every region and every species is
# named on the drawing, and the diffusion layer carries a dimension bar.
#
# THIS IS AN AUTHOR-INSTRUCTED EXCEPTION to the 2026-09-07 "no text in the figures" rule,
# scoped to this panel, the same standing the SPECS plate has.
#
# IT REMAINS STATE S AND THE "schematic" TAG STAYS. Every label is an IDENTIFIER -- which
# species, which region, which length -- and NOT ONE OF THEM IS A MAGNITUDE. delta and x_k
# are named, never numbered: the numbers live in panels (c)-(f), which are solved. A cartoon
# that printed a film thickness would be asserting a measurement it has not made.
#
# The aspect is the whole reason the old panel failed, so it is stated: with equal aspect the
# data-span ratio MUST equal the axes-box ratio or matplotlib pillarboxes the drawing. At the
# printed 6.5 in the full-width box is about 6.05 x 1.95 in, so the spans are 3.10 x 1.00.
# Change the row height and this ratio must change with it.
# ═══════════════════════════════════════════════════════════════════════════════════

CELL_W, CELL_GAP = 1.10, 0.095
LBL_XSPAN, LBL_YSPAN = 3 * CELL_W + 2 * CELL_GAP, 1.00


def _dimbar(ax, x0, x1, y, text, color=SLATE, size=6.8, cap=0.022, lw=0.8, dy=-0.055):
    """A dimension bar with end caps, labelled below its own midpoint."""
    ax.plot([x0, x1], [y, y], color=color, lw=lw, solid_capstyle="butt", zorder=8)
    for xe in (x0, x1):
        ax.plot([xe, xe], [y - cap, y + cap], color=color, lw=lw, solid_capstyle="butt", zorder=8)
    ax.text(0.5 * (x0 + x1), y + dy, text, ha="center", va="top", fontsize=size,
            color=color, zorder=8)


def _leader(ax, xy_text, xy_point, color=OUTLINE, lw=0.6):
    ax.plot([xy_text[0], xy_point[0]], [xy_text[1], xy_point[1]], color=color, lw=lw,
            solid_capstyle="butt", zorder=7)


def _carrier_cycle(ax, P, x_el, x_out, yMO, yMR, r, rest, rest_hi, act, act_hi, w):
    """The complete catalytic cycle (author, 2026-09-09: show "how reacting with the substrate
    regenerates the unactivated form"). Four spheres, one per corner. Resting form (bottom-left)
    is turned over AT THE ELECTRODE into the active form (top-left): the left semicircle, sized
    so its apex meets the metal, with e- on the metal there. Active form out along the top to
    the reaction site (top-right). There it reacts with S and is SPENT back to the resting form
    (bottom-right): the right arc, which the grey S -> P curl bows in to touch -- that contact is
    the reaction, and it is where x_k ends. Resting form back along the bottom. The active half
    of the loop is drawn in the lighter shade, the resting half in the full one."""
    sphere(ax, *P(x_el, yMR), r, rest, rest_hi)
    sphere(ax, *P(x_el, yMO), r, act, act_hi)
    sphere(ax, *P(x_out, yMO), r, act, act_hi)
    sphere(ax, *P(x_out, yMR), r, rest, rest_hi)
    c = _clr(ax, r)                                      # 2026-09-10: clear water between every arrow end and its sphere (author: "good clearance and space")
    xa = P(x_el, 0)[0] - 0.022 * w                       # electrode side: resting -> active (anchors on the surfaces)
    arrow(ax, (xa, P(0, yMR)[1] + 0.022 * w), (xa, P(0, yMO)[1] - 0.022 * w),
          color=act, lw=1.35, rad=-1.0, ms=7.5, shrinkA=c, shrinkB=c)
    arrow(ax, P(x_el + r, yMO), P(x_out - r, yMO), color=act, lw=1.25, ms=7, shrinkA=c, shrinkB=c)
    xb = P(x_out, 0)[0] + 0.022 * w                      # reaction side: active -> resting
    arrow(ax, (xb, P(0, yMO)[1] - 0.022 * w), (xb, P(0, yMR)[1] + 0.022 * w),
          color=rest, lw=1.35, rad=-0.45, ms=7.5, shrinkA=c, shrinkB=c)
    arrow(ax, P(x_out - r, yMR), P(x_el + r, yMR), color=rest, lw=1.25, ms=7, shrinkA=c, shrinkB=c)


CARRIER_AMP = 0.28          # catalyst-cell carrier level under abundance=True, as a fraction of the mediator's


def carrier_schematic_lbl(ax, blue=BLUE_SPHERE, orange=ORANGE_SPHERE, red=RED_SPHERE,
                          tag=True, fs_title=7.6, fs_lab=6.8, fs_reg=6.6, xspan=None,
                          abundance=False):
    """Three carrier classes, full width and fully labelled. This panel is the legend for panel
    (c), which counts and plots exactly these three.

    ONE GRAMMAR IN ALL THREE CELLS, so the only thing that moves is the thing that matters
    (author, 2026-09-08): the substrate comes in along the top, a CURVED ARROW marks the
    S -> P step, the product leaves along the bottom. WHERE that curl sits is the taxonomy --
    on the electrode for the direct case, out in solution at the carrier for the other two.

    EACH CELL CARRIES ITS CONCENTRATION PROFILE: varying across delta, flat against a dashed
    c_bulk line beyond it, because delta is exactly the region that holds the gradient.

    EVERY INTERNAL LENGTH IS A FRACTION OF THE CELL WIDTH. They were absolute data units once,
    while the cell width is derived from the span -- so raising the figure row silently scaled
    the electrode and the film by 19 % against a cell whose physical width had not moved, and
    cramped the two right-hand cells. Geometry that must hold its proportions cannot be written
    in units that the layout is free to rescale.

    Still state S. No axis and no number: delta and x_k are named, never measured. The direct and
    catalyst profiles are the straight line steady 1-D Fick gives at i_lim (the line panel (b)
    plots); the mediated one is depleted-but-not-exhausted at the wall, the shape panel (d) solves."""
    hi = {blue: BLUE_HI, orange: ORANGE_HI, red: RED_HI}
    span = LBL_XSPAN if xspan is None else float(xspan)
    w = (span - 2 * CELL_GAP) / 3.0                       # cell width; everything below scales with it

    Y0, H = 0.118, 0.760
    EX, EW = 0.041 * w, 0.064 * w                         # electrode inset, electrode width
    FX = EX + EW                                          # electrolyte / film start
    # THE CELL IS MOSTLY delta (author, 2026-09-08: "these panels should really just be of the
    # L_BL where the interesting phenomena is occuring"). The bulk keeps only the strip it needs
    # to show the profile going flat -- which is the one thing the bulk has to say here.
    FW = 0.600 * w                                        # the film, drawn == delta
    IW = w - 2 * EX
    r = 0.031 * w
    PY0, PY1 = 0.68, 0.90                                 # profile band: 22 % of H (was 30 %)
    u = np.linspace(0, 1, 80)
    # The profile drawn is the RESTING form of whatever the cell transports, in the form the
    # model uses for that class (author question, 2026-09-09: "aren't they mathematically the
    # same?" -- they are). Direct: substrate, steady Fick at i_lim, linear to zero. Mediated AND
    # catalyst: both solved as EC' with a finite, cited k since v88 (2026-09-11: seven of the
    # eleven catalyst rows carry a measured rate constant and the merge overlays their 49 cells
    # the way it overlays the mediated ones), so in both the resting form is regenerated INSIDE
    # the film -- curved, non-zero at the wall, the shape panels (d-f) solve. The k = 0 floor the
    # four unsourced rows still sit at is the same equation with the source term off.
    # the reaction site: on the metal / at the edge of the reaction layer / out in solution.
    # For the mediated cell x_k IS the reaction site, so the marker and the curl are one number.
    # BOTH homogeneous cells draw the same reaction layer, because x_k = sqrt(D_carrier / k C_S)
    # is the same quantity for both and the two classes overlap in it: the mediated rows of (g)
    # run x_k = 2.3 / 7.7 / 158 um at their cited k, the catalyst rows of (h) 2.9 / 4.1 / 60 um.
    # The distinction the model does keep is CARRIER LOADING -- mediators 0.024-1.0 M (median
    # 0.060), molecular catalysts 2.6-30 mM (median 5.0), a 12x gap at the median that sets a
    # 17-23x gap in the class median ceiling at every architecture.
    # Reaction sites. A molecular catalyst is an EC' carrier like a mediator -- the electrode
    # generates the active oxidation state, the substrate consumes it in solution -- so the two
    # homogeneous cells draw the SAME reaction layer; what separates them is abundance (mediators
    # 0.1-0.5 M, catalysts 3-30 mM). The published matrix runs the catalyst rows at k = 0, the
    # floor of the EC' current; SI S5.7 (G-CATK) measures the finite-k case. This panel draws the
    # mechanism, panel (b) the k = 0 floor, panel (c) both. 2026-09-09.
    RXN = (0.010 * w, 0.360 * w, 0.360 * w)               # = 2 %, 60 %, 60 % of delta
    # two rows carry everything: active form / S in on the top, resting form / P out on the
    # bottom; the carrier's bulk supply takes the lane between them
    yA, yR, yL = 0.440, 0.160, 0.300
    # (the profile shapes are built here, AFTER RXN, so x_k and the mediated recovery are one number)
    uk = RXN[1] / FW                                      # x_k of the mediated cell, in units of delta
    ell = 0.5 * uk                                        # decay length: recovered by ~x_k, exactly c_bulk at delta
    rec = (np.exp(-u / ell) - np.exp(-1 / ell)) / (1 - np.exp(-1 / ell))
    SHAPES = (u, 1.0 - 0.72 * rec, 1.0 - 0.72 * rec)     # both homogeneous classes: recovered within x_k
    blank(ax, (0, span), (0, LBL_YSPAN))

    titles = ("direct", "mediated (EC$^\\prime$)", "molecular catalyst")
    cols = (blue, orange, red)
    for i, title in enumerate(titles):
        x = i * (w + CELL_GAP)
        frame(ax, x, Y0, w, H)
        ey, eh = Y0 + 0.026, H - 0.052
        electrolyte(ax, x + EX, ey, IW, eh)
        film(ax, x + FX, ey, FW, eh)
        electrode(ax, x + EX, ey, EW, eh)
        P = lambda fx, fy: (x + fx, Y0 + fy * H)
        py = lambda v: Y0 + (PY0 + (PY1 - PY0) * v) * H

        ax.text(x + 0.5 * w, Y0 + H + 0.052, title, ha="center", va="bottom",
                fontsize=fs_title, fontweight="bold", color=SLATE)
        _dimbar(ax, x + FX, x + FX + FW, Y0 - 0.026, "$\\delta$", size=fs_lab)
        # e- ON the electrode, at the height of the transfer: the grey curl's apex in the direct
        # cell, the carrier turnover's apex in the other two
        y_e = 0.5 * (yA + yR)
        ax.text(x + EX + 0.5 * EW, Y0 + y_e * H, "e$^-$", ha="center", va="center",
                fontsize=fs_lab, color="#4A3B12", fontweight="bold", zorder=6)
        if i == 0:
            ax.text(x + EX + 0.5 * EW, Y0 + 0.5 * H, "electrode", rotation=90, ha="center",
                    va="center", fontsize=fs_reg, color="#4A3B12", style="italic", zorder=6)

        # ── concentration profile: varying across delta, flat outside it ──────────────
        ax.plot([x + EX, x + EX + IW], [py(1.0), py(1.0)], color="#8A93A3", lw=0.65,
                ls=(0, (2.5, 2.0)), zorder=6)
        # 2026-09-10 (author: "neither of the profiles in b or c look like d-f"): every cell draws
        # the same species in the same styles as the solved panels -- substrate dotted; active form
        # (made at the electrode, light shade) solid; resting form (full shade) dashed.
        X = x + FX + FW * u; xe = [x + FX + FW, x + EX + IW]
        if i == 0:
            ax.plot(X, py(u), color=cols[i], lw=1.6, ls=(0, (1, 1.2)), zorder=8)                       # substrate, Fick at i_lim
            ax.plot(xe, [py(1.0), py(1.0)], color=cols[i], lw=1.6, ls=(0, (1, 1.2)), zorder=8)
        else:
            uk_i = RXN[i] / FW; ell_i = 0.5 * uk_i
            rec_i = (np.exp(-u / ell_i) - np.exp(-1 / ell_i)) / (1 - np.exp(-1 / ell_i))          # 1 at the wall, 0 at delta
            act, rest = (ORANGE_ACT, orange) if i == 1 else (RED_ACT, red)
            dip = 0.45 if i == 1 else 0.12                                  # substrate: drawn down inside x_k, Fick beyond it
            sub = np.where(u < uk_i, 1 - dip, 1 - dip + dip * (u - uk_i) / max(1 - uk_i, 1e-6))
            # ABUNDANCE, the one thing the model does keep apart (Connor Coley, 2026-09-21: "the distinction
            # between EC mediated and molecular catalyst is (almost) only the substrate concentration at the
            # surface. I'm not sure that this is what was implied"). He is reading the drawing correctly: the two
            # homogeneous cells solve the SAME EC' problem and were drawn alike, so the only visible difference
            # was the substrate's dip. What separates them in the 50-reaction set is how much carrier is present
            # -- mediators 0.024-1.0 M, molecular catalysts 2.6-30 mM -- and with the switch on the catalyst's
            # carrier curves are drawn against the same c_bulk rule at that lower level. Schematic: the ratio is
            # legible, not to scale.
            amp = CARRIER_AMP if (abundance and i == 2) else 1.0
            ax.plot(X, py(amp * 0.85 * rec_i), color=act, lw=1.6, zorder=8)                        # active form
            ax.plot(X, py(amp * (1.0 - 0.72 * rec_i)), color=rest, lw=1.6, ls=(0, (5, 2)), zorder=8)  # resting form
            ax.plot(X, py(sub), color=blue, lw=1.4, ls=(0, (1, 1.2)), zorder=9)                     # substrate
            ax.plot(xe, [py(0.0), py(0.0)], color=act, lw=1.6, zorder=8)
            ax.plot(xe, [py(amp), py(amp)], color=rest, lw=1.6, ls=(0, (5, 2)), zorder=8)
            ax.plot(xe, [py(1.0), py(1.0)], color=blue, lw=1.4, ls=(0, (1, 1.2)), zorder=9)
        if i == 0:
            ax.text(x + EX + IW - 0.012, py(1.0) + 0.020, "$c_{bulk}$", ha="right",
                    va="bottom", fontsize=fs_reg, color="#6F7889")

        # ── S in, the reaction, P out: attached to the cycle's own corners ──────────────
        # S enters the top-right (active) corner; P leaves the bottom-right (resting) corner; the
        # reaction is the carrier's own arc between them, so there is no separate curl to clash
        # with it (author, 2026-09-09: "arrows are clashing and unprofessional"). The direct cell
        # has no carrier, so there its arc is the grey curl on the metal.
        x_r = FX + RXN[i]                                 # apex of the reaction arc == end of x_k
        chord = (yA - yR) * H - 0.044 * w
        arc_bulge = 0.5 * 0.45 * chord
        x_out = x_r - 0.022 * w - arc_bulge               # the cycle's outer spheres
        xS = EX + 0.92 * IW                               # S and P at the far right, labels above/below
        if i == 0:
            x_in = FX + 0.012 * w + 0.5 * 0.38 * chord    # the grey curl hugs the metal
            arrow(ax, (x + x_in, Y0 + yA * H - 0.022 * w), (x + x_in, Y0 + yR * H + 0.022 * w),
                  color=GRAY_SPHERE, lw=1.35, rad=0.38, ms=7.5)
            x_join = x_in + 0.022 * w
        else:
            x_join = x_out + r                            # the corner sphere's surface; the trim below makes the gap
        c = _clr(ax, r); cj = c if i >= 1 else 0
        arrow(ax, P(xS - r, yA), P(x_join, yA), color=blue, lw=1.2, ms=7, shrinkA=c, shrinkB=cj)
        sphere(ax, *P(xS, yA), r, blue, hi[blue])
        ax.text(x + xS, Y0 + yA * H + 0.048, "S", ha="center", va="bottom",
                fontsize=fs_lab, color=blue, fontweight="bold")
        arrow(ax, P(x_join, yR), P(xS - r, yR), color=GRAY_HI, lw=1.2, ms=7, shrinkA=cj, shrinkB=c)
        sphere(ax, *P(xS, yR), r, GRAY_SPHERE, GRAY_HI)
        ax.text(x + xS, Y0 + yR * H - 0.044, "P", ha="center", va="top",
                fontsize=fs_lab, color=GRAY_SPHERE, fontweight="bold")

        if i >= 1:
            xk_y = Y0 + 0.615 * H
            ax.plot([x + FX, x + x_r], [xk_y, xk_y], color=SLATE, lw=0.8,
                    solid_capstyle="butt", zorder=8)
            for xe in (x + FX, x + x_r):
                ax.plot([xe, xe], [xk_y - 0.013, xk_y + 0.013], color=SLATE, lw=0.8, zorder=8)
            ax.text(x + x_r + 0.016 * w, xk_y, "$x_k$", ha="left", va="center",
                    fontsize=fs_lab, color=SLATE, zorder=8)
            col, hc = (orange, hi[orange]) if i == 1 else (red, hi[red])
            act, hact = (ORANGE_ACT, ORANGE_ACT_HI) if i == 1 else (RED_ACT, RED_ACT_HI)
            xel = FX + 0.022 * w + 0.5 * chord            # left semicircle's apex on the face
            _carrier_cycle(ax, P, xel, x_out, yA, yR, r, col, hc, act, hact, w)
            xm = x + 0.5 * (xel + x_out)
            top, bot = ("Med$_{ox}$", "Med$_{red}$") if i == 1 else ("Cat$^*$", "Cat")
            ax.text(xm, Y0 + yA * H + 0.034, top, ha="center", va="bottom",
                    fontsize=fs_lab, color=col, fontweight="bold")
            ax.text(xm, Y0 + yR * H - 0.030, bot, ha="center", va="top",
                    fontsize=fs_lab, color=col, fontweight="bold")
            # the carrier is transported too: its resting form arrives from the bulk on the
            # middle lane and joins the cycle at the reaction arc (author, 2026-09-09). Two
            # spheres for the abundant mediator, one for the dilute catalyst.
            lane = (0.90,) if abundance else ((0.80, 0.90) if i == 1 else (0.90,))
            for ff in lane:
                sphere(ax, x + EX + ff * IW, Y0 + yL * H, 0.9 * r, col, hc)
            arrow(ax, P(EX + lane[0] * IW - 0.9 * r, yL), P(x_r + 0.028 * w, yL),
                  color=col, lw=1.2, ms=7, shrinkA=_clr(ax, 0.9 * r))

    # region labels, once, on the first cell -- they name the same regions in all three
    ax.text(FX + 0.5 * FW, Y0 + 0.615 * H, "diffusion layer", ha="center", va="center",
            fontsize=fs_reg, color=SLATE, style="italic")
    ax.text(FX + FW + 0.5 * (IW - FW - EW) + 0.02, Y0 + 0.615 * H, "bulk", ha="center",
            va="center", fontsize=fs_reg, color=SLATE, style="italic")

    if tag:
        ax.text(span, 0.0, "schematic", ha="right", va="bottom", fontsize=6.5,
                color="0.55", style="italic")
