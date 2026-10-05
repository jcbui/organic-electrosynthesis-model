## Walk the c-control branch and print i(frac). The collapse criterion c_red/cb < 1e-3 assumes
## the mediator CAN be depleted that far. Where migration pumps the mediator in faster than it
## is consumed (the reacting ion is also the supporting anion, as in Br- oxidation) that may
## never happen -- and the limiting current is then set by a FOLD in i along the branch, not by
## the concentration threshold. i_lim = max(i) over the branch covers both cases without
## assuming either.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end
for (nm, rk) in [("Br- oxidation / electrophilic bromination", :stirred),
                 ("Br- oxidation / electrophilic bromination", :natural)]
    spec = SPECS[findfirst(x -> x.label == nm, SPECS)]
    km = spec.k_M/1000.0; xk = sqrt(spec.species[2].D/(km*spec.C_S))
    isb = findfirst(s -> s.name == "Sub", spec.species)
    ired = findfirst(s -> s.s < 0, spec.species)
    r = REACTORS[findfirst(x -> x.key == rk, REACTORS)]
    d = delta_eff(r.key, spec.D_red, spec.nu_solv)
    i_t0 = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d)
    p = ECProblem(spec.species, 2, isb, km, geometric_faces(d, clamp(xk/50,0.02e-6,0.9*d/90), 90))
    u = zeros(nvars(p)); for ix in 1:nnode(p), j in 1:length(p.sp)
        u[lidx(p,ix,j)] = log(max(p.sp[j].c_bulk,1e-6)) end
    ia = 0.02*i_t0
    for _ in 1:40
        newton_ec!(u, p, ia; max_iter=120, max_log_step=3.0) || break
        ia *= 1.15
    end
    ia /= 1.15
    @printf("\n=== %s / %s   (i_t0 %.2f, ramp reached %.2f mA/cm2) ===\n",
            first(nm,34), string(rk), i_t0*0.1, ia*0.1)
    @printf("%10s %12s %12s %10s\n", "c_red/cb", "i mA/cm2", "c_sub/cb", "note")
    iref = [ia]; frac = exp(u[lidx(p,1,ired)])/p.sp[ired].c_bulk
    best = ia; step = 0.12
    while frac > 1e-3 && step > 1e-5
        f = max(frac*exp(-step), 1e-3)
        ut = copy(u); it = [iref[1]]
        if newton_ec_ccontrol!(ut, it, p, f)
            u .= ut; iref[1] = it[1]; frac = f
            note = it[1] < best*0.999 ? "<-- PAST THE FOLD" : ""
            best = max(best, it[1])
            @printf("%10.3e %12.3f %12.3e %10s\n", frac, it[1]*0.1,
                    exp(u[lidx(p,1,isb)])/p.sp[isb].c_bulk, note)
            flush(stdout)
            step = min(step*1.3, 0.24)
        else
            step /= 2
        end
    end
    @printf("  -> max i along branch = %.3f mA/cm2 ; final c_red/cb = %.3e\n", best*0.1, frac)
end
