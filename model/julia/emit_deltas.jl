## Emit delta_eff for all 50 reactions x 7 architectures at the REFERENCE operating point and at
## both edges of the registry's declared bands. Used by data/si_sensitivity_bounds.py to bound the
## 42 Nernst-Planck rows analytically (i_lim ~ 1/delta is exact for them: i*delta is invariant).
## The correlations come from correlations.jl itself -- no second implementation to drift.
include("params.jl"); include("correlations.jl"); include("reactions_table.jl")
using Printf
d_lo(key, D, nu) = key === :natural ? 103e-6 :
                   ## stirred is MEASURED (200 +/- 7 um, Williams/Manthiram p. 1227), not swept:
                   ## the bound is the measurement's own uncertainty, not the 50-200 um range
                   ## that had to be swept while the value was a declared 100 um.
                   key === :stirred ? 193e-6 :
                   ## the three flow films (2026-09-07): bands defined once, in correlations.jl
                   key === :flow    ? DELTA_FLOW_BAND[1] :
                   key === :anec    ? DELTA_ANEC_BAND[1] :
                   key === :micro   ? D / km_micro(D; tau = TAU_MICRO_BAND[1]) :
                   key === :rde     ? delta_rde(D, nu; rpm = 3600.0) :
                                      D / km_rce(D, nu; d = 0.012, rpm = 5000.0)
d_hi(key, D, nu) = key === :natural ? 528e-6 :
                   key === :stirred ? 207e-6 :
                   key === :flow    ? DELTA_FLOW_BAND[2] :
                   key === :anec    ? DELTA_ANEC_BAND[2] :
                   key === :micro   ? D / km_micro(D; tau = TAU_MICRO_BAND[2]) :
                   key === :rde     ? delta_rde(D, nu; rpm = 400.0) :
                                      D / km_rce(D, nu; d = 0.012, rpm = 1000.0)
open(joinpath(@__DIR__, "delta_bounds.csv"), "w") do io
    println(io, "reaction,reactor,delta_ref_um,delta_lo_um,delta_hi_um")
    for rx in RXNS, r in REACTORS
        dr = delta_eff(r.key, rx.D, rx.nu)
        @printf(io, "\"%s\",\"%s\",%.6f,%.6f,%.6f\n", rx.name, r.label,
                dr*1e6, d_lo(r.key, rx.D, rx.nu)*1e6, d_hi(r.key, rx.D, rx.nu)*1e6)
    end
end
println("wrote julia/delta_bounds.csv")
