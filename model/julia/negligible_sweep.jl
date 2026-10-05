## SENSITIVITY OF THE ANSWER TO THE NEGLIGIBILITY THRESHOLD.
##
## limit_step! excludes from the Newton trust-region norm any component whose species sits below
## NEGLIGIBLE_C of its bulk value. That threshold is a numerical choice, so by this project's own
## standard it has to carry a stated sensitivity rather than a plausible-sounding justification.
##
## Sweep it over six decades and re-solve, by the ordinary ramp + c-control path, the two cells the
## change actually moved plus two it must NOT move. The requirement is strict:
##   * the two moved cells must return the same limit at every threshold;
##   * RDE and RCE, which never drive a species below even 1e-3 of bulk, must be invariant AND
##     equal to their pre-change values, because for them no threshold produces any exclusion.
D=@__DIR__
include(joinpath(D,"params.jl")); include(joinpath(D,"correlations.jl")); include(joinpath(D,"npp_ecprime.jl"))
tr(x)=1e-6*x
brom = [ECSpecies("Br-", -1.0, 2.08e-9, 152.001, -1.0, +1.0),
        ECSpecies("Br2",  0.0, 1.2e-9,  tr(152.),+0.5, -1.0),
        ECSpecies("Sub",  0.0, 6.25e-10, 121.,    0.0, -1.0),
        ECSpecies("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),
        ECSpecies("Na+", +1.0, 1.33e-9, 152.,     0.0,  0.0)]
hof  = [ECSpecies("Br-",  -1.0, 2.7e-9, 80.001,  -1.0, +2.0),
        ECSpecies("Br2",   0.0, 2.2e-9, tr(80.), +0.5, -1.0),
        ECSpecies("Sub",   0.0, 2.00e-9, 400.,    0.0, -1.0),
        ECSpecies("H+",   +1.0, 3.0e-9, 1e-3,     0.0, +2.0),
        ECSpecies("Na+",  +1.0, 1.33e-9, 80.,     0.0,  0.0)]

function solve_cell(sp, km, d, isb)
    xk = sqrt(sp[2].D/(km*sp[isb].c_bulk))
    p  = ECProblem(sp, 2, isb, km, geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/90), 90))
    i_t0 = F_const*sp[1].D*(sp[1].c_bulk-0.001)/(abs(sp[1].s)*d)
    il, lim, us, is_ = solve_ilim_ec(p; i_start=0.02*i_t0, growth=1.15)
    if is_ > 0
        rc = solve_ilim_ec_ccontrol(p; u0=us, i0=is_)
        rc[1] > il && (il = rc[1])
    end
    il*0.1
end

cells = [("brom  x unstirred", brom, 1e3/1000.0, 300.0e-6,             3),
         ("hofmann x unstirred", hof, 1e3/1000.0, 300.0e-6,            3),
         ("brom  x RDE",       brom, 1e3/1000.0, 15.761274893671272e-6, 3),
         ("brom  x RCE",       brom, 1e3/1000.0, 14.84333051680979e-6,  3)]

@printf("%-20s", "NEGLIGIBLE_C")
for (nm,_,_,_,_) in cells; @printf(" %18s", nm); end
println()
base = Dict{String,Float64}()
for thr in (1e-6, 1e-8, 1e-10, 1e-12, 1e-14, 1e-16)
    NEGLIGIBLE_C[] = thr
    @printf("%-20.0e", thr)
    for (nm, sp, km, d, isb) in cells
        v = solve_cell(sp, km, d, isb)
        haskey(base, nm) || (base[nm] = v)
        @printf(" %18.6f", v)
    end
    println(); flush(stdout)
end
println()
NEGLIGIBLE_C[] = 1e-10
println("Every row above must be identical: what is being tested is INVARIANCE to the threshold.")
println("These are BARE-RAMP figures -- solve_cell takes whichever of the ramp and the c-control")
println("walk reaches higher. They are NOT the published values, which are the c-control plateaus")
println("in mediated_ec_matrix.csv (Br- x unstirred publishes 23.7491, not 23.7715; the 0.09% is")
println("the plateau tolerance |dln i/dln frac| < 2e-3, not a difference in physics). The estimator")
println("only has to be the SAME at every threshold for the invariance test to mean something.")
for (nm, sp, km, d, isb) in cells
    @printf("  %-20s at the production threshold 1e-10, bare ramp: %.6f\n",
            nm, solve_cell(sp, km, d, isb))
end
