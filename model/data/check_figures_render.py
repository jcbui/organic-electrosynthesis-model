#!/usr/bin/env python3
"""G-FIGRUN -- do the figure generators still RUN, and still draw what is shipped?

    cd Section4_Model && python data/check_figures_render.py
    cd Section4_Model && python data/check_figures_render.py --negative-control

WHY -- THE HOLE THIS CLOSES
---------------------------
Every artwork check in this repo compares the bytes embedded in the .docx against the PNG on
disk. That answers "embedded == on-disk". It cannot answer "on-disk == what the model draws
today", and the difference is not academic:

  * A CRASHED generator writes nothing and leaves the previous PNG in place, so both sides freeze
    and agree. figs/make_fig_trle.py raised AssertionError for days -- its pinned stirred >=25
    count still said 18 after the acetonitrile viscosity correction moved it to 17 -- and every
    artwork gate reported PASS the whole time. Re-rendering changed the PNG immediately and the
    manuscript gate then failed on image6, which is the proof the staleness had shipped.
  * A generator simply NOT RUN after the model moved does the same thing without an error at all
    (that is what forced v43).

So this gate does the one thing those gates cannot: it RUNS each generator with the pinned
interpreter and requires (a) a clean exit and (b) byte-identical output. A generator that crashes
FAILS here even though its artwork is unchanged -- which is the entire point.

IT RENDERS INTO THE REAL TREE, DELIBERATELY
-------------------------------------------
These generators chdir to the repo root and read the swatch workbook, the matrices and the
registry from there, so a scratch-tree copy (the G-REGEN approach) does not reproduce them. They
are therefore run in place, WITH THE PINNED INTERPRETER, because a figure rendered under the wrong
Python differs over ~14% of the canvas with no error (CLAUDE.md trap 8) and would silently
overwrite good artwork. The gate refuses to run if that interpreter is missing rather than falling
back to another one.

If a render legitimately changes, this gate FAILS and says so: that is the signal to re-embed,
not a defect in the gate.
"""
import hashlib
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PINNED = "/opt/anaconda3/bin/python3.12"
# Figure 1 renders ONLY in its own pinned env (CLAUDE.md trap 19). Built 2026-09-07; proved by
# rendering at the historical 400 dpi and reproducing the shipped raster byte for byte, where the
# 3.12 interpreter differs over 7.27 % of the canvas. Recreate with Figure_1b_Kasie/requirements.txt
# (rdkit is NOT needed: fig_composite.py reads finished parquets and imports no rdkit).
PINNED_FIG1 = "/opt/anaconda3/envs/fig1_pin/bin/python"
PROJECT = os.path.dirname(ROOT)

# generator -> the artifacts it is responsible for
GENERATORS = [
    ("figs/make_figs_sec34.py", ["figs/sec4_Fig_sec3.png", "figs/sec4_Fig_ceiling.png"]),
    ("figs/combined_figure.py", ["figs/combined_figure_grounded.png"]),
    ("figs/make_fig_trle.py", ["figs/sec4_fig_trle.png"]),
    ("figs/make_fig_carrier.py", ["figs/sec4_Fig_carrier.png"]),
    # Section 6 (2026-09-07): the SPECS reproducibility plate, drawn from the paper's own table
    ("figs/make_fig_specs.py", ["figs/sec6_fig_specs.png"]),
    # Figure 8 (2026-09-09): the author's failure-modes artwork, rasterised live from its .ai at
    # 600 dpi the way the SPECS plate is; the manuscript embeds this file, so an edit to the .ai
    # shows up here as a stale render. The marker proves the producer wrote, not merely exited.
    ("figs/make_fig_failure_modes.py", ["../Figures/Organic ESynth Failure Modes Figure_v3_600dpi.png"],
     PINNED, ROOT, "wrote "),
    # Figure 6 (2026-10-02): the author placed the six reaction schemes by hand in Illustrator, so
    # the figure is now his artwork and combined_figure.py's render is its INPUT. Both paths have to
    # be watched -- the entry above keeps the model-to-render path, this one the artwork-to-document
    # path -- and the generator additionally refuses to run once the render it was laid out over has
    # moved, because an Illustrator file cannot follow a model change.
    ("figs/make_fig6_final.py", ["../Figures/Figure6_with_schemes_20261002_600dpi.png"],
     PINNED, ROOT, "wrote "),
    # The SI embeds five figures of its own, and they were exposed to exactly the same trap: on
    # 2026-08-31 Figures C and F were both found to re-render differently, i.e. the SI had been
    # shipping pre-correction artwork. make_si.js reads these PNGs at build time, so a stale
    # render reaches the document silently.
    ("figs/make_figs.py", ["figs/sec4_figC_heatmap.png", "figs/sec4_figE_npp.png"]),
    ("figs/make_figFG.py", ["figs/sec4_figF_gap.png"]),
    ("figs/make_figH_ecprime.py", ["figs/sec4_figH_ecprime.png"]),
    ("figs/make_figK.py", ["figs/sec4_figK_boiloff.png"]),
    # Figure 1 (added 2026-09-07, once its pinned env existed). Three things make it unlike the
    # rest, and the third is the one that matters:
    #   (i)  it lives outside Section4_Model, so it runs with cwd = Figure1/ (customplot reads the
    #        Berkeley swatch workbook from cwd);
    #   (ii) it needs PINNED_FIG1, not PINNED;
    #   (iii) IT EXITS 0 WITHOUT WRITING when the environment is off-pin -- by design, so that
    #        reading its printed numbers cannot clobber a correct raster. So "clean exit and the
    #        file did not change" is exactly what a WRONG environment also produces, and the
    #        byte-comparison alone would pass vacuously. MUST_PRINT closes that: the run has to
    #        say it wrote the figure, or the gate fails.
    ("../Figure1/fig_composite.py", ["../Figure1/figure1_composite.png"],
     PINNED_FIG1, os.path.join(PROJECT, "Figure1"), "wrote figure1_composite"),
]


def _norm(entry):
    """(script, artifacts) or (script, artifacts, interpreter, cwd, required stdout marker)."""
    script, arts = entry[0], entry[1]
    interp = entry[2] if len(entry) > 2 else PINNED
    cwd = entry[3] if len(entry) > 3 else ROOT
    marker = entry[4] if len(entry) > 4 else None
    return script, arts, interp, cwd, marker


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def main(neg=False):
    if not os.path.exists(PINNED):
        print("G-FIGRUN: FAIL -- the pinned interpreter %s is missing; refusing to render with "
              "another one (trap 8)" % PINNED)
        return 1
    env = dict(os.environ, MPLBACKEND="Agg")
    rows, fails = [], []
    for entry in GENERATORS:
        script, arts, interp, cwd, marker = _norm(entry)
        if not os.path.exists(interp):
            fails.append("%s needs the interpreter %s, which is missing -- build it from "
                         "Figure_1b_Kasie/requirements.txt (see trap 19); refusing to render with "
                         "another one (trap 8)" % (script, interp))
            continue
        sp = os.path.join(ROOT, script)
        if not os.path.exists(sp):
            fails.append("%s does not exist" % script)
            continue
        before = {a: (md5(os.path.join(ROOT, a)) if os.path.exists(os.path.join(ROOT, a)) else None)
                  for a in arts}
        cmd = [interp, sp]
        if neg:
            # Perturb the RUN, not the repo: import a module that does not exist, so the
            # generator exits non-zero without writing anything. A control that edited a figure
            # input would leave real artwork perturbed on disk.
            cmd = [PINNED, "-c", "import __definitely_not_a_module__"]
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
        crashed = r.returncode != 0 or "Traceback" in r.stderr
        # A generator that guards its own environment can exit 0 having written nothing; that is
        # indistinguishable from success by exit status and by byte-comparison alike.
        silent = marker is not None and marker not in (r.stdout + r.stderr)
        after = {a: (md5(os.path.join(ROOT, a)) if os.path.exists(os.path.join(ROOT, a)) else None)
                 for a in arts}
        moved = [a for a in arts if before[a] != after[a]]
        rows.append({"script": script, "exit": r.returncode, "crashed": crashed,
                     "changed": moved, "wrote": (not silent) if marker else None})
        print("  %-32s exit %-3d %s%s"
              % (script, r.returncode, "CRASHED" if crashed else "clean",
                 ("  CHANGED: " + ", ".join(os.path.basename(m) for m in moved)) if moved else ""))
        if crashed:
            tail = [ln for ln in r.stderr.strip().split("\n") if ln.strip()][-1:] or [""]
            fails.append("%s does not run: %s" % (script, tail[0][:150]))
        elif silent:
            fails.append("%s exited 0 but never reported writing its figure (%r absent) -- it "
                         "refused to render, most likely an off-pin environment, and the "
                         "unchanged bytes on disk prove nothing" % (script, marker))
        if moved:
            fails.append("%s re-renders differently, so the shipped copy is stale: %s"
                         % (script, ", ".join(moved)))

    json.dump({"pinned_interpreter": PINNED, "generators": rows, "failures": fails},
              io.open(os.path.join(ROOT, "results", "figures_render%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)
    for f in fails:
        print("    FAIL  %s" % f)
    if neg:
        ok = len(fails) >= len(GENERATORS)
        print("\nNEGATIVE CONTROL: every generator replaced by a command that exits non-zero, so "
              "each must be reported as not running.")
        print("G-FIGRUN control: %s (%d finding(s))"
              % ("GOOD" if ok else "BAD -- test is inert", len(fails)))
        return 0 if ok else 1
    if fails:
        print("\nG-FIGRUN: FAIL")
        return 1
    print("\nG-FIGRUN: PASS -- all %d figure generators run clean under their pinned interpreter "
          "and reproduce their shipped renders byte-identically" % len(GENERATORS))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
