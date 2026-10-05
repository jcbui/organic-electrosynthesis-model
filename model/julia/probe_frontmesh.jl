## Does resolving the FRONT let the one stubborn cell solve with full EC' physics?
## Two-pass: solve on the standard mesh to locate the front, re-mesh with resolution there,
## re-solve. No fallback -- it either solves or it does not.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end
spec = SPECS[findfirst(x -> x.label == "Br- oxidation / electrophilic bromination", SPECS)]
km = spec.k_M/1000.0; xk = sqrt(spec.species[2].D/(km*spec.C_S))
isb = findfirst(s -> s.name == "Sub", spec.species)
d  = delta_eff(:natural, spec.D_red, spec.nu_solv)
d_st = delta_eff(:stirred, spec.D_red, spec.nu_solv)
i_t0 = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d)
bound = 0.9*i_t0
@printf("Br- ox x unstirred: delta %.0f um, x_k %.2f um, commuting bound %.2f mA/cm2\n\n", d*1e6, xk*1e6, bound*0.1)

geo(dd)  = ECProblem(spec.species, 2, isb, km, geometric_faces(dd, clamp(xk/50,0.02e-6,0.9*dd/90), 90))
grd(dd,xf_front,N) = ECProblem(spec.species, 2, isb, km,
        graded_faces(dd, N, [(0.0, clamp(xk/50,0.02e-6,0.9*dd/N)), (xf_front, xk/4)]))

## anchor at stirred, properly solved
p_st = geo(d_st); i0st = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d_st)
il,_,us,isf = solve_ilim_ec(p_st; i_start=0.02*i0st, growth=1.15)
ic,_,uc,_ = solve_ilim_ec_ccontrol(p_st; u0=us, i0=isf)
@printf("anchor (stirred, geometric): %.2f mA/cm2\n\n", ic*0.1)

@printf("%-42s %10s  %s\n","mesh at delta=300","i mA/cm2","outcome")
for (tag, N, xfr) in [("graded, front 0.85d, N=270", 270, 0.85d),
                      ("graded, front 0.85d, N=360", 360, 0.85d),
                      ("graded, front 0.85d, N=540", 540, 0.85d)]
    p = xfr === nothing ? geo(d) : grd(d, xfr, N)
    res = solve_ilim_ec_continued(dd -> (xfr === nothing ? geo(dd) : grd(dd, xfr*dd/d, N)),
                                  d_st, d, p_st, uc, ic; nsteps=48,
                                  backoff=(0.9,0.7,0.5,0.35,0.25,0.15))
    if res === nothing
        @printf("%-42s %10s  continuation did not survive\n", tag, "-")
    else
        i2, l2, _, _ = solve_ilim_ec_ccontrol(res.p; u0=res.u, i0=res.i)
        @printf("%-42s %10.2f  %s [%s]\n", tag, i2*0.1,
                i2 >= bound ? "SOLVED" : "below bound", first(l2,40))
    end
    flush(stdout)
end
