#!/usr/bin/env python3
"""Write the two band-edge copies of run_mediated.jl used by the SI sensitivity table.

The 42 Nernst-Planck rows scale EXACTLY as i ~ 1/delta (i*delta is invariant), so their bounds are
computed analytically. The 8 EC' rows do NOT: their amplification i_ec/i_t0 depends on delta/x_k,
and measured across the delta range it varies by up to 1757% (ACT-mediated), 1232% (HMF), 233%
(BQ), 95% (NHPI), 46% (thiocyanation). Only bromination (0.12%), Cl-epoxidation (0.15%) and
Hofmann (4.0%) are near-invariant. So the mediated rows have to be RE-SOLVED at each band edge.

Each copy overrides delta_eff AFTER the includes and redirects its output. Production is untouched.
"""
import io, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); JL = os.path.join(os.path.dirname(HERE), "julia")

## registry bands. LO = the delta-minimising (current-maximising) edge, HI = the other.
OVERRIDE = {
 "lo": """
## band-edge delta_eff: every architecture at its CURRENT-MAXIMISING edge (smallest delta).
## Bands are the registry sensitivities, defined ONCE in correlations.jl for the flow films:
## unstirred 103-528 um (free-convection envelope), stirred 193-207 um (the measurement's own
## +/-7 um), the recirculating and ANEC films +/-12.1 % (Watkins Table S1's replicate scatter),
## the microfluidic film over Mo's printed residence times 4-12 min (the half-gap at both ends),
## RDE 400-3600 rpm, RCE 1000-5000 rpm.
function delta_eff(key::Symbol, D::Float64, nu::Float64)
    key === :natural  && return 103e-6
    key === :stirred  && return 193e-6
    key === :flow     && return DELTA_FLOW_BAND[1]
    key === :anec     && return DELTA_ANEC_BAND[1]
    key === :micro    && return D / km_micro(D; tau = TAU_MICRO_BAND[1])
    key === :rde      && return delta_rde(D, nu; rpm = 3600.0)
    key === :rce      && return D / km_rce(D, nu; d = 0.012, rpm = 5000.0)
    error("unknown reactor $key")
end
""",
 "hi": """
## band-edge delta_eff: every architecture at its CURRENT-MINIMISING edge (largest delta).
function delta_eff(key::Symbol, D::Float64, nu::Float64)
    key === :natural  && return 528e-6
    key === :stirred  && return 207e-6
    key === :flow     && return DELTA_FLOW_BAND[2]
    key === :anec     && return DELTA_ANEC_BAND[2]
    key === :micro    && return D / km_micro(D; tau = TAU_MICRO_BAND[2])
    key === :rde      && return delta_rde(D, nu; rpm = 400.0)
    key === :rce      && return D / km_rce(D, nu; d = 0.012, rpm = 1000.0)
    error("unknown reactor $key")
end
"""}

def main():
    src = io.open(os.path.join(JL, "run_mediated.jl"), encoding="utf-8").read()
    made = []
    for tag, override in OVERRIDE.items():
        s = src
        m = list(re.finditer(r'include\("[^"]+"\)', s))
        assert m, "could not find the include block"
        at = m[-1].end()          # after include("reactions_table.jl") -- last include in the file
        s = s[:at] + "\n" + override + s[at:]
        s = s.replace('open(joinpath(@__DIR__, "mediated_ec_matrix.csv"), "w")',
                      'open(joinpath(@__DIR__, "mediated_ec_matrix_band_%s.csv"), "w")' % tag)
        p = os.path.join(JL, "_bounds_%s.jl" % tag)
        io.open(p, "w", encoding="utf-8").write(s)
        made.append(p)
        print("wrote", os.path.basename(p))
    return made

if __name__ == "__main__":
    main()
