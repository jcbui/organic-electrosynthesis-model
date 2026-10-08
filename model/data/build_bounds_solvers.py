#!/usr/bin/env python3
"""Regenerate julia/_bounds_lo.jl and julia/_bounds_hi.jl from julia/run_mediated.jl.

    cd Section4_Model && python data/build_bounds_solvers.py

The two band-edge solvers are run_mediated.jl with exactly two changes: a delta_eff override
inserted after `include("reactions_table.jl")`, which puts every architecture at one edge of its
declared film band, and the output file name. They were hand-made copies until 2026-10-05, so a
MedSpec added to or corrected in run_mediated.jl did not reach them. This writes both from the
live solver, so the three files cannot carry different chemistry.
"""
import io, os
HERE = os.path.dirname(os.path.abspath(__file__)); JL = os.path.join(os.path.dirname(HERE), "julia")
ANCHOR = 'include("reactions_table.jl")\n'
OUT_OLD = 'open(joinpath(@__DIR__, "mediated_ec_matrix.csv"), "w") do io'
OVERRIDE = {
"lo": '## band-edge delta_eff: every architecture at its CURRENT-MAXIMISING edge (smallest delta).\n## Bands are the registry sensitivities, defined ONCE in correlations.jl for the flow films:\n## unstirred 103-528 um (free-convection envelope), stirred 193-207 um (the measurement\'s own\n## +/-7 um), the recirculating and ANEC films +/-12.1 % (Watkins Table S1\'s replicate scatter),\n## the microfluidic film over Mo\'s printed residence times 4-12 min (the half-gap at both ends),\n## RDE 400-3600 rpm, RCE 1000-5000 rpm.\nfunction delta_eff(key::Symbol, D::Float64, nu::Float64)\n    key === :natural  && return 103e-6\n    key === :stirred  && return 193e-6\n    key === :flow     && return DELTA_FLOW_BAND[1]\n    key === :anec     && return DELTA_ANEC_BAND[1]\n    key === :micro    && return D / km_micro(D; tau = TAU_MICRO_BAND[1])\n    key === :rde      && return delta_rde(D, nu; rpm = 3600.0)\n    key === :rce      && return D / km_rce(D, nu; d = 0.012, rpm = 5000.0)\n    error("unknown reactor $key")\nend',
"hi": '## band-edge delta_eff: every architecture at its CURRENT-MINIMISING edge (largest delta).\nfunction delta_eff(key::Symbol, D::Float64, nu::Float64)\n    key === :natural  && return 528e-6\n    key === :stirred  && return 207e-6\n    key === :flow     && return DELTA_FLOW_BAND[2]\n    key === :anec     && return DELTA_ANEC_BAND[2]\n    key === :micro    && return D / km_micro(D; tau = TAU_MICRO_BAND[2])\n    key === :rde      && return delta_rde(D, nu; rpm = 400.0)\n    key === :rce      && return D / km_rce(D, nu; d = 0.012, rpm = 1000.0)\n    error("unknown reactor $key")\nend',
}

def main():
    ## the unstirred edges are the free-convection envelope DERIVED in results/free_convection_delta.json (2026-10-07: they
    ## were typed as 103 / 528 um while the derivation gives 102.9 / 529.6); emit_deltas.jl must carry the same two numbers
    import json
    fc = json.load(io.open(os.path.join(os.path.dirname(HERE), "results", "free_convection_delta.json"), encoding="utf-8"))
    lo, hi = "%.1fe-6" % fc["delta_band_lo_um"], "%.1fe-6" % fc["delta_band_hi_um"]
    em = io.open(os.path.join(JL, "emit_deltas.jl"), encoding="utf-8").read()
    if ("key === :natural ? %s :" % lo) not in em or ("key === :natural ? %s :" % hi) not in em:
        raise SystemExit("julia/emit_deltas.jl does not carry the derived unstirred edges %s / %s" % (lo, hi))
    src = io.open(os.path.join(JL, "run_mediated.jl"), encoding="utf-8").read()
    assert src.count(ANCHOR) == 1 and src.count(OUT_OLD) == 1, "run_mediated.jl anchors moved"
    for edge, block in OVERRIDE.items():
        old = {"lo": "key === :natural  && return 103e-6", "hi": "key === :natural  && return 528e-6"}[edge]
        assert block.count(old) == 1, "the %s override's unstirred edge moved" % edge
        block = block.replace(old, "key === :natural  && return %s" % {"lo": lo, "hi": hi}[edge])
        block = block.replace("unstirred 103-528 um", "unstirred %.0f-%.0f um" % (fc["delta_band_lo_um"], fc["delta_band_hi_um"]))
        out = src.replace(ANCHOR, ANCHOR + "\n" + block + "\n\n\n")
        out = out.replace(OUT_OLD, OUT_OLD.replace("mediated_ec_matrix.csv", "mediated_ec_matrix_band_%s.csv" % edge))
        io.open(os.path.join(JL, "_bounds_%s.jl" % edge), "w", encoding="utf-8").write(out)
        print("wrote julia/_bounds_%s.jl" % edge)

if __name__ == "__main__":
    main()
