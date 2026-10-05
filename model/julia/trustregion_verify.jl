## Does the selective trust region (a) unblock the unstirred cell and (b) leave the five reactors
## that already converged exactly where they were? Both must hold. The stored values are read
## straight out of mediated_ec_matrix.csv as written before this change.
D=@__DIR__
include(joinpath(D,"params.jl")); include(joinpath(D,"correlations.jl")); include(joinpath(D,"npp_ecprime.jl"))
tr(x)=1e-6*x
sp = [ECSpecies("Br-", -1.0, 2.08e-9, 152.001, -1.0, +1.0),
      ECSpecies("Br2",  0.0, 1.2e-9,  tr(152.),+0.5, -1.0),
      ECSpecies("Sub",  0.0, 6.25e-10, 121.,    0.0, -1.0),
      ECSpecies("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),
      ECSpecies("Na+", +1.0, 1.33e-9, 152.,     0.0,  0.0)]
km = 1e3/1000.0
xk = sqrt(sp[2].D/(km*sp[3].c_bulk))
cells = [("Unstirred batch",     300.0e-6,               NaN),
         ("Stirred batch",       100.0e-6,               71.26002072290322),
         ("Parallel-plate flow",  86.93461099652019e-6,  81.97299417471426),
         ("Thin-gap microflow",   34.50002323708058e-6, 206.65618939957585),
         ("RDE 1600 rpm",         15.761274893671272e-6, 452.62864406258905),
         ("Rotating cylinder",    14.84333051680979e-6,  480.6081816622069)]
@printf("%-22s %7s %9s %10s %10s %9s  %s\n","reactor","d/um","i_k0","i_ec new","stored","delta%","limiter")
for (nm, d, stored) in cells
    N = 90
    mkp = kk -> ECProblem(sp, 2, 3, kk, geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/N), N))
    i_t0 = F_const*sp[1].D*152.0/(abs(sp[1].s)*d)
    ## no-source floor, same mesh and species
    p0 = mkp(0.0)
    a, l0, us0, is0 = solve_ilim_ec(p0; i_start=0.02*i_t0, growth=1.15)
    i_k0 = a
    if is0 > 0
        r0 = solve_ilim_ec_ccontrol(p0; u0=us0, i0=is0); r0[1] > i_k0 && (i_k0 = r0[1])
    end
    ## the ordinary production path: ramp then c-control. Nothing else.
    p = mkp(km)
    il, lim, us, is_ = solve_ilim_ec(p; i_start=0.02*i_t0, growth=1.15)
    if is_ > 0
        rc = solve_ilim_ec_ccontrol(p; u0=us, i0=is_)
        rc[1] > il && ((il, lim) = (rc[1], rc[2]))
    end
    dpc = isnan(stored) ? NaN : 100*(il*0.1 - stored)/stored
    @printf("%-22s %7.1f %9.3f %10.3f %10s %9s  %s\n", nm, d*1e6, i_k0*0.1, il*0.1,
            isnan(stored) ? "-" : @sprintf("%.3f", stored),
            isnan(dpc) ? "-" : @sprintf("%+.4f", dpc), lim)
    flush(stdout)
end
