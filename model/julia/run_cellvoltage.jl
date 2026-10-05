## run_cellvoltage.jl — regenerate cellvoltage.csv only (extracted from run_section4.jl)
using Printf
include("params.jl"); include("cellvoltage.jl")
open(joinpath(@__DIR__, "cellvoltage.csv"), "w") do io
    println(io, "electrolyte,kappa_Sm,gap_label,gap_m,i_mAcm2,E_cell_V,Q_W_cm2")
    for e in ELECS, (glab, g) in GAPS, i in [10.0, 25.0, 50.0, 100.0, 300.0]
        E = E_cell(i, e.kappa, g); Q = Q_joule_Wcm2(i, e.kappa, g)
        println(io, "\"$(e.label)\",$(e.kappa),\"$glab\",$g,$i,$E,$Q")
    end
end
println("cellvoltage.csv written")
