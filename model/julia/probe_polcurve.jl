## The polarisation curve itself. It should be SMOOTH and rise to a plateau. Discontinuities
## mean the continuation is jumping between solution families -- numerics, not physics.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end
@printf("%-40s %-9s %10s %6s %9s  %s\n","system","reactor","i_lim","pts","roughness","ended on")
for spec in SPECS, rk in (:stirred, :natural)
    km = spec.k_M/1000.0; xk = sqrt(spec.species[2].D/(km*spec.C_S))
    isb = findfirst(s -> s.name == "Sub", spec.species)
    r = REACTORS[findfirst(x -> x.key == rk, REACTORS)]
    d = delta_eff(r.key, spec.D_red, spec.nu_solv)
    i_t0 = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d)
    p = ECProblem(spec.species, 2, isb, km, geometric_faces(d, clamp(xk/50,0.02e-6,0.9*d/90), 90))
    il, lm, us, isf = solve_ilim_ec(p; i_start=0.02*i_t0, growth=1.15)
    if isf <= 0
        @printf("%-40s %-9s %10s %6s %9s  ramp gave no anchor\n", first(spec.label,40), string(rk),"-","-","-"); continue
    end
    ic, limc, _, _, br = solve_ilim_ec_ccontrol(p; u0=us, i0=isf)
    @printf("%-40s %-9s %10.2f %6d %9.3f  %s\n", first(spec.label,40), string(rk),
            ic*0.1, length(br), branch_roughness(br), first(limc,52))
    flush(stdout)
end
