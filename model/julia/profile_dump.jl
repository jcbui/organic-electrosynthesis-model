## WHERE IS THE FRONT, AND DOES THE MESH RESOLVE IT?
## Continuation failing EARLIER on finer meshes (k = 0.36 at N=90, 0.218 at N=180, 0.0069 at
## N=360) and a wall substrate value that moves four orders of magnitude between meshes are both
## signs that the reaction front is under-resolved rather than that the continuation is at fault.
## Behind the front the substrate decays with local length lambda = sqrt(D_S / (k*c_ox)). Print it
## against the actual cell width h(x) so the requirement is measured, not guessed.
D=@__DIR__
include(joinpath(D,"params.jl")); include(joinpath(D,"correlations.jl")); include(joinpath(D,"npp_ecprime.jl"))
tr(x)=1e-6*x
sp = [ECSpecies("Br-", -1.0, 2.08e-9, 152.001, -1.0, +1.0),
      ECSpecies("Br2",  0.0, 1.2e-9,  tr(152.),+0.5, -1.0),
      ECSpecies("Sub",  0.0, 6.25e-10, 121.,    0.0, -1.0),
      ECSpecies("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),
      ECSpecies("Na+", +1.0, 1.33e-9, 152.,     0.0,  0.0)]
km = 1e3/1000.0; d = 300e-6
xk = sqrt(sp[2].D/(km*sp[3].c_bulk))
i_t0 = F_const*sp[1].D*152.0/(abs(sp[1].s)*d)

function state_at(N, frac_hold; nk=40)
    mk = kk -> ECProblem(sp, 2, 3, kk, geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/N), N))
    p0 = mk(0.0)
    i0, l0, us, is_ = solve_ilim_ec(p0; i_start=0.02*i_t0, growth=1.15)
    rc0 = solve_ilim_ec_ccontrol(p0; u0=us, i0=is_)
    u = copy(rc0[3]); iv = [rc0[1]]
    newton_ec_ccontrol!(u, iv, p0, frac_hold) || return nothing
    t = 0.0; dt = 1.0/nk
    while t < 1.0
        t_try = min(t+dt, 1.0); k_try = km*t_try^2
        p_s = mk(k_try); u_s = copy(u); i_s = [iv[1]]
        if newton_ec_ccontrol!(u_s, i_s, p_s, frac_hold)
            u, iv, t = u_s, i_s, t_try; dt = min(dt*1.3, 2.0/nk)
        else
            dt /= 2; dt < 1e-6 && return nothing
        end
    end
    (u, iv[1], mk(km))
end

for N in (90, 180)
    r = state_at(N, 0.5)
    if r === nothing; @printf("N=%d: could not reach k_target\n", N); continue; end
    u, i, p = r
    xf = p.xf; xc = 0.5*(xf[1:end-1] + xf[2:end])
    @printf("\n=== N=%d, delta=300 um, k=%.3g, frac=0.5, i=%.3f mA/cm2 ===\n", N, km, i*0.1)
    @printf("%8s %10s %12s %12s %10s %10s %8s\n","x/um","h/um","c_sub/cb","c_ox mol/m3","lambda/um","h/lambda","")
    for ix in 1:nnode(p)
        csub = exp(u[lidx(p,ix,3)])/121.0
        cox  = exp(u[lidx(p,ix,2)])
        lam  = sqrt(sp[3].D/(km*max(cox,1e-30)))
        h    = xf[ix+1]-xf[ix]
        if ix <= 3 || ix % 10 == 0 || (csub > 1e-12 && csub < 1e-1)
            @printf("%8.2f %10.3f %12.2e %12.4g %10.3f %10.2f %s\n",
                    xc[ix]*1e6, h*1e6, csub, cox, lam*1e6, h/lam, h/lam > 1 ? "<-- UNDER-RESOLVED" : "")
        end
    end
    flush(stdout)
end
