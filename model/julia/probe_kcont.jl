include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end
@printf("%-40s %-9s %9s %9s  %s\n","system","reactor","bound","i_lim","outcome")
for (nm, rk) in [("Br- oxidation / electrophilic bromination", :natural),
                 ("Br- oxidation / electrophilic bromination", :stirred),
                 ("Br-mediated Hofmann rearrangement", :natural)]
    spec = SPECS[findfirst(x -> x.label == nm, SPECS)]
    km = spec.k_M/1000.0; xk = sqrt(spec.species[2].D/(km*spec.C_S))
    isb = findfirst(s -> s.name == "Sub", spec.species)
    d = delta_eff(rk, spec.D_red, spec.nu_solv)
    i_t0 = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d)
    mk(kk) = ECProblem(spec.species, 2, isb, kk,
                       geometric_faces(d, clamp(xk/50,0.02e-6,0.9*d/90), 90))
    r = solve_ilim_ec_kcont(mk, km, i_t0)
    if r === nothing
        @printf("%-40s %-9s %9.2f %9s  k-continuation did not survive\n", first(nm,40), string(rk), 0.9*i_t0*0.1, "-")
    else
        @printf("%-40s %-9s %9.2f %9.2f  %s\n", first(nm,40), string(rk), 0.9*i_t0*0.1, r[1]*0.1,
                r[1] >= 0.9*i_t0 ? "SOLVED" : "below bound")
    end
    flush(stdout)
end
