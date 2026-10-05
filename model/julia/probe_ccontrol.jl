## Does concentration-controlled continuation reach the collapse criterion where the
## current ramp stalls?  cd Section4_Model/julia && julia --project=. probe_ccontrol.jl
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end

function run_one(spec, r; N = 90)
    km = spec.k_M / 1000.0
    xk = sqrt(spec.species[2].D / (km * spec.C_S))
    d  = delta_eff(r.key, spec.D_red, spec.nu_solv)
    i_t0 = F_const * spec.D_red * spec.C_med / (abs(spec.species[1].s) * d)
    isb = findfirst(s -> s.name == "Sub", spec.species)
    p = ECProblem(spec.species, 2, isb, km,
                  geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/N), N))
    ## (a) the current ramp, as production does it
    il, lim, u_safe, i_safe = solve_ilim_ec(p; i_start = 0.02*i_t0, growth = 1.15)
    ## (b) concentration control, started from the ramp's last SAFE state
    ic, limc, _, frac = i_safe > 0 ?
        solve_ilim_ec_ccontrol(p; u0 = u_safe, i0 = i_safe) : (0.0, "no anchor", u_safe, 1.0)
    (ramp = il*0.1, ramp_lim = lim, cc = ic*0.1, cc_lim = limc, frac = frac, t0 = i_t0*0.1)
end

R = REACTORS[findfirst(x -> x.key == :stirred, REACTORS)]
println("stirred archetype, N = 90\n")
@printf("%-40s %10s %10s %8s  %s\n", "system", "ramp", "c-control", "ratio", "c-control ended on")
for spec in SPECS
    a = run_one(spec, R)
    @printf("%-40s %10.2f %10.2f %8.2f  %s\n", first(spec.label, 40), a.ramp, a.cc,
            a.ramp > 0 ? a.cc/a.ramp : 0.0, a.cc_lim)
    flush(stdout)
end
