## Mesh-convergence and monotonicity check for the limit-tracking solver on the one cell that
## needed it: Br- oxidation / electrophilic bromination x unstirred batch (delta = 300 um).
## Run with the PRODUCTION rate constant: run_mediated converts k_M = 1e3 M^-1 s^-1 to
## km = k_M/1000 = 1.0 m^3 mol^-1 s^-1, which reproduces the tabulated x_k of 3.149 um.
D=@__DIR__
include(joinpath(D,"params.jl")); include(joinpath(D,"correlations.jl")); include(joinpath(D,"npp_ecprime.jl"))
tr(x)=1e-6*x
sp = [ECSpecies("Br-", -1.0, 2.08e-9, 152.001, -1.0, +1.0),
      ECSpecies("Br2",  0.0, 1.2e-9,  tr(152.),+0.5, -1.0),
      ECSpecies("Sub",  0.0, 6.25e-10, 121.,    0.0, -1.0),
      ECSpecies("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),
      ECSpecies("Na+", +1.0, 1.33e-9, 152.,     0.0,  0.0)]
d  = 300e-6
km = 1e3/1000.0
xk = sqrt(sp[2].D/(km*sp[3].c_bulk))
i_t0 = F_const*sp[1].D*152.0/(abs(sp[1].s)*d)
@printf("x_k = %.3f um (table prints 3.149)   i_t0 = %.3f mA/cm2   i_subcap = %.3f mA/cm2\n",
        xk*1e6, i_t0*0.1, 2*F_const*sp[3].D*sp[3].c_bulk/d*0.1)

for N in (90, 180, 360, 720)
    mk  = kk -> ECProblem(sp, 2, 3, kk, geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/N), N))
    p0  = mk(0.0)
    i0, lim0, u0s, i0s = solve_ilim_ec(p0; i_start=0.02*i_t0, growth=1.15)
    i_k0 = i0; u_k0 = copy(u0s)
    if i0s > 0
        ic, limc, uc, _, _ = solve_ilim_ec_ccontrol(p0; u0=u0s, i0=i0s)
        if ic > i_k0; i_k0 = ic; u_k0 = copy(uc); end
    end
    rt = solve_ilim_ec_ktrack(mk, km, i_k0, u_k0)
    if rt === nothing
        @printf("N=%-4d  i_k0=%8.3f   k-tracking RETURNED NOTHING\n", N, i_k0*0.1); continue
    end
    pk = mk(km)
    @printf("N=%-4d  i_k0=%8.3f   i_ec=%8.3f mA/cm2  (x%.4f vs tier0, x%.4f vs floor)  c_red/cb=%.2e  c_sub/cb=%.2e  [%s]\n",
            N, i_k0*0.1, rt[1]*0.1, rt[1]/i_t0, rt[1]/i_k0,
            exp(rt[3][lidx(pk,1,1)])/152.001, exp(rt[3][lidx(pk,1,3)])/121.0, rt[2])
    flush(stdout)
end
