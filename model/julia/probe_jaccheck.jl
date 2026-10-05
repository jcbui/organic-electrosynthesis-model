## Verify the analytic Jacobian against central differences on REAL production states,
## across every mediated system and several currents -- not on a toy problem.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end

@printf("%-40s %-9s %6s %11s %11s  %s\n",
        "system", "reactor", "i/i_t0", "max|dJ|", "max rel", "verdict")
worst = 0.0
for spec in SPECS
    km = spec.k_M/1000.0; xk = sqrt(spec.species[2].D/(km*spec.C_S))
    isb = findfirst(s -> s.name == "Sub", spec.species)
    for rk in (:stirred, :natural)
        r = REACTORS[findfirst(x -> x.key == rk, REACTORS)]
        d = delta_eff(r.key, spec.D_red, spec.nu_solv)
        i_t0 = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d)
        p = ECProblem(spec.species, 2, isb, km,
                      geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/90), 90))
        u = zeros(nvars(p))
        for ix in 1:nnode(p), j in 1:length(p.sp)
            u[lidx(p,ix,j)] = log(max(p.sp[j].c_bulk, 1e-6))
        end
        ## check at a low current (near-bulk) and after ramping into depletion
        for (tag, target) in (("0.02", 0.02*i_t0), ("ramped", 0.0))
            if target == 0.0
                ia = 0.02*i_t0
                for _ in 1:25
                    newton_ec!(u, p, ia; max_iter=120, max_log_step=3.0) || break
                    ia *= 1.15
                end
                target = ia/1.15
            else
                newton_ec!(u, p, target; max_iter=120, max_log_step=3.0)
            end
            ma, mr, wr, wc, sc = jacobian_check(p, u, target)
            global worst = max(worst, mr)
            @printf("%-40s %-9s %6s %11.2e %11.2e  %s\n", first(spec.label,40), string(rk),
                    tag, ma, mr, mr < 1e-6 ? "OK" : "*** MISMATCH ***")
            flush(stdout)
        end
    end
end
@printf("\nworst relative disagreement anywhere: %.3e  ->  %s\n", worst,
        worst < 1e-6 ? "ANALYTIC JACOBIAN VERIFIED" : "ANALYTIC JACOBIAN IS WRONG")
