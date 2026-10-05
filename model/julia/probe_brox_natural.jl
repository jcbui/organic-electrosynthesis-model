## The one cell that will not solve: Br- oxidation x unstirred (delta 300 um, x_k 3.2 um).
## Try harder continuations from the stirred anchor. No fallbacks -- either it solves with the
## full EC' physics or it does not, and we say which.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end
spec = SPECS[findfirst(x -> x.label == "Br- oxidation / electrophilic bromination", SPECS)]
km = spec.k_M/1000.0; xk = sqrt(spec.species[2].D/(km*spec.C_S))
isb = findfirst(s -> s.name == "Sub", spec.species)
mk(dd) = ECProblem(spec.species, 2, isb, km, geometric_faces(dd, clamp(xk/50,0.02e-6,0.9*dd/90), 90))
d_st = delta_eff(:stirred, spec.D_red, spec.nu_solv)
d_na = delta_eff(:natural, spec.D_red, spec.nu_solv)
i_t0_na = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d_na)
@printf("target delta %.0f um; commuting bound %.2f mA/cm2; x_k %.2f um; delta/x_k %.0f\n\n",
        d_na*1e6, 0.9*i_t0_na*0.1, xk*1e6, d_na/xk)

## anchor: solve the stirred cell properly (ramp then c-control)
p_st = mk(d_st)
i_t0_st = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d_st)
il, lm, us, isf = solve_ilim_ec(p_st; i_start=0.02*i_t0_st, growth=1.15)
ic, limc, uc, fr = solve_ilim_ec_ccontrol(p_st; u0=us, i0=isf)
@printf("anchor (stirred): i = %.2f mA/cm2  [%s]\n\n", ic*0.1, first(limc,40))

@printf("%-34s %12s  %s\n", "continuation", "i mA/cm2", "outcome")
for (tag, ns, bo) in [("nsteps=24 (production)", 24, (1.0,0.85,0.70,0.55,0.40)),
                      ("nsteps=48",             48, (1.0,0.85,0.70,0.55,0.40)),
                      ("nsteps=96",             96, (1.0,0.85,0.70,0.55,0.40)),
                      ("nsteps=96, deep backoff",96,(0.9,0.7,0.5,0.35,0.25,0.15,0.10))]
    res = solve_ilim_ec_continued(mk, d_st, d_na, p_st, uc, ic; nsteps=ns, backoff=bo)
    if res === nothing
        @printf("%-34s %12s  continuation did not survive\n", tag, "-")
    else
        ## then c-control from the recovered state, which is the whole point
        ic2, lc2, _, _ = solve_ilim_ec_ccontrol(res.p; u0=res.u, i0=res.i)
        ok = ic2 >= 0.9*i_t0_na
        @printf("%-34s %12.2f  %s [%s]\n", tag, ic2*0.1,
                ok ? "SOLVED (clears bound)" : "below commuting bound", first(lc2,44))
    end
    flush(stdout)
end
