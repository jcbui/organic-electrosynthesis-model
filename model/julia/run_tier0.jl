## run_tier0.jl — regenerate ONLY the Tier-0 matrix (extracted from run_section4.jl)
## after property-pipeline changes; avoids re-running the NPP validation sweeps.
using Printf
include("params.jl"); include("correlations.jl"); include("reactions_table.jl")

hdr = vcat(["class","reaction","carrier"], [String(r.key) for r in REACTORS])
rows = Vector{Vector{Any}}()
for rx in RXNS
    row = Any[rx.cls, rx.name, rx.carrier]
    for r in REACTORS
        d = delta_eff(r.key, rx.D, rx.nu)
        push!(row, i_lim_tier0(rx.n, rx.D, rx.C, d))
    end
    push!(rows, row)
end
open(joinpath(@__DIR__, "tier0_matrix.csv"), "w") do io
    println(io, join(hdr, ","))
    for row in rows
        println(io, join([x isa Float64 ? @sprintf("%.4g", x) : "\"$x\"" for x in row], ","))
    end
end
for (k, r) in enumerate(REACTORS)
    vals = [row[3 + k] for row in rows]
    @printf("  %-28s median %7.1f   >=25: %2d/50   >=50: %2d/50\n",
            r.label, sort(vals)[25], count(v -> v >= 25, vals), count(v -> v >= 50, vals))
end
println("tier0 DONE")
