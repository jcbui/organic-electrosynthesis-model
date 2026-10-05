#!/usr/bin/env python3
"""G-ORPHAN -- every artefact a solver writes must be read by something.

    cd Section4_Model && python data/check_orphans.py

WHY THIS EXISTS
---------------
`julia/run_all50_np.jl` solved all 50 reactions x 6 architectures with Nernst-Planck and migration
and wrote `all50_np_matrix.csv`. For an unknown period NOTHING read that file: the published matrix
was still assembled from the Tier-0 Fick table, so 42 of 50 published rows had no migration term
while the headline counts were tallied across the mixed column. The Kolbe row was understated by
exactly a factor of two.

Every existing gate missed it. `audit_numeric.py` verifies that derived artefacts are CONSISTENT
with their sources -- and it never opened the orphan, because an orphan is by definition not a
source of anything. Consistency between the wrong inputs is still consistent. A clean run of every
check in the repo therefore reported success while the published numbers came from a model the
project had already replaced.

WHAT THIS CHECKS
----------------
For each artefact a solver writes, is its basename mentioned in at least one CONSUMER source file
(the Python builders, the SI generator, the figure scripts, or another Julia script)? A file
mentioned only by its own writer is an orphan and fails.

This is deliberately a crude textual check. It cannot tell whether a consumer uses the file
correctly -- only whether the wiring exists at all. That is precisely the failure it is aimed at,
and it is the kind of check that is cheap to keep honest.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEC4 = os.path.dirname(HERE)
JULIA = os.path.join(SEC4, "julia")

## artefact -> the script that WRITES it (its own mention does not count as consumption)
WRITERS = {
    "all50_np_matrix.csv":    "run_all50_np.jl",
    "mediated_ec_matrix.csv": "run_mediated.jl",
    "tier0_matrix.csv":       "run_tier0.jl",
    "tier0_ec_matrix.csv":    "build_merged_matrix.py",
    "catalyst_ec_sweep.csv":  "run_catalyst_ecprime.jl",
    "catalyst_ec_sourced.csv": "run_catalyst_sourced.jl",     # 2026-09-11: the seven sourced-k rows (merge + G-CATK)
    "catalyst_ec_delta.csv":  "run_catalyst_delta.jl",       # 2026-09-11: Fig. 6h
    "catalyst_ec_band_lo.csv": "run_catalyst_band.jl",       # 2026-09-11: the SI bounds table (si_sensitivity_bounds.py)
    "catalyst_ec_band_hi.csv": "run_catalyst_band.jl",
    "mediated_ec_profiles.csv": "run_mediated_profiles.jl",       # 2026-09-11 (v90): Fig. 6d-f, the three rows of (g) at the ANEC film
    "mediated_ec_profiles_dsens.csv": "run_mediated_profiles.jl",  # the same solver's +/-25 % diffusivity re-solves (G-ECPANEL)
    "mediated_ec_delta.csv":  "run_mediated_delta.jl",      # 2026-09-11: Fig. 6g (three mediated rows at their cited k)
    "reactions_table.jl":     "build_reactions50.py",
    "ion_diffusivities.csv":  "build_ion_diffusivities.py",
    "electrode_direction.csv": None,       # hand-authored, not solver output
}

def sources():
    out = []
    # 2026-09-11: the figure generators are consumers too (the Fig. 6g/6h film sweeps are read by
    # figs/combined_figure.py and by nothing else); a consumer directory the scan omits makes a real
    # consumer look like an orphan.
    for d in (HERE, JULIA, SEC4, os.path.join(SEC4, "figs")):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith((".py", ".jl", ".js")) and ".bak" not in f:
                out.append(os.path.join(d, f))
    return out

def main(neg=False):
    files = sources()
    if neg:
        # Register an artefact nothing writes or reads. G-ORPHAN exists to catch a solver output
        # that no downstream script consumes, so an unconsumed entry MUST be reported.
        # It must EXIST on disk: the gate deliberately does not flag a registered artefact that
        # was never produced, so a control that only adds a dict entry tests nothing. (The first
        # version of this control did exactly that and reported the gate inert when it was fine.)
        WRITERS["__control_orphan.csv"] = "__control_writer.py"
        _ctl = os.path.join(JULIA, "__control_orphan.csv")
        with open(_ctl, "w", encoding="utf8") as _fh:
            _fh.write("control\n")
        import atexit
        atexit.register(lambda: os.path.exists(_ctl) and os.remove(_ctl))
    text = {f: open(f, encoding="utf8", errors="replace").read() for f in files}
    bad = []
    print("%-26s %-26s %s" % ("artefact", "written by", "consumers"))
    for art, writer in sorted(WRITERS.items()):
        cons = []
        for f, t in text.items():
            base = os.path.basename(f)
            if base == writer or base == os.path.basename(__file__):
                continue
            if art in t:
                cons.append(base)
        exists = os.path.exists(os.path.join(JULIA, art)) or os.path.exists(os.path.join(HERE, art))
        mark = "" if cons else "   <<< ORPHAN"
        if not cons and exists:
            bad.append(art)
        print("%-26s %-26s %s%s" % (art, writer or "(hand-authored)",
                                    ", ".join(cons[:4]) or "NONE", mark))
    print()
    if bad:
        print("G-ORPHAN: FAIL -- %d artefact(s) are written and never read: %s" % (len(bad), bad))
        print("  An orphan means a solve is being paid for and thrown away, and whatever consumes")
        print("  the same role instead is doing so with different physics or stale numbers.")
        if neg:
            print("G-ORPHAN control: GOOD (the unconsumed artefact was reported)")
            return 0
        return 1
    if neg:
        print("G-ORPHAN control: BAD -- test is inert (an unconsumed artefact was not reported)")
        return 1
    print("G-ORPHAN: PASS -- every solver artefact is consumed by at least one other script")
    return 0

if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
