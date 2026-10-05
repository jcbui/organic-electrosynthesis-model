## WHY DOES THE DEPLETION WALK STALL?
## At N=180 the mesh resolves the front (h/lambda <= 0.87 everywhere) and the fixed-depletion
## k-walk reaches the production k without trouble. What fails is walking the depletion DOWN from
## 0.5 to 1e-3 at that k. Two candidate causes, tested separately:
##   (a) not enough Newton iterations. newton_ec_ccontrol! clamps each log-step at 2.0 and allows
##       120 iterations. The substrate spans 22 orders of magnitude across a 150 um dead zone, so
##       a step in depletion moves a great many cells by far more than 2 in log -- which with a
##       clamp of 2.0 needs a lot of iterations, not a smaller step.
##   (b) a genuine turning point / branch loss.
## Distinguishing them: rerun the identical walk with a much larger iteration budget. If (a), it
## proceeds; if (b), it stalls at the same depletion regardless.
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

function fracwalk(N, maxit, maxstep; ratio = 0.97, frac_end = 1.5e-3)
    r = state_at(N, 0.5); r === nothing && return
    u, i, p = r
    @printf("\nN=%d  max_iter=%d  max_step=%.1f   start frac=0.500 i=%.4f\n", N, maxit, maxstep, i*0.1)
    frac = 0.5; nfail = 0
    while frac > frac_end
        f_try = max(frac*ratio, frac_end)
        u_t = copy(u); i_t = [i]
        if newton_ec_ccontrol!(u_t, i_t, p, f_try; max_iter=maxit, max_step=maxstep)
            u, i, frac = u_t, i_t[1], f_try; nfail = 0
            if frac < 0.02 || abs(log(frac)/log(10) - round(log(frac)/log(10))) < 0.02
                cox = exp(u[lidx(p,1,2)]); csub = exp(u[lidx(p,1,3)])/121.0
                @printf("   frac=%.4e  i=%8.4f mA/cm2   c_ox(wall)=%7.2f  c_sub/cb(wall)=%.2e\n",
                        frac, i*0.1, cox, csub)
                flush(stdout)
            end
        else
            nfail += 1; ratio = 1 - (1-ratio)/2
            if nfail > 25 || ratio > 0.9999
                @printf("   STALLED at frac=%.4e  i=%8.4f mA/cm2\n", frac, i*0.1); return
            end
        end
    end
    cox = exp(u[lidx(p,1,2)]); csub = exp(u[lidx(p,1,3)])/121.0
    @printf("   REACHED frac=%.4e  i=%8.4f mA/cm2  x%.4f vs floor 20.305  c_ox(wall)=%.2f c_sub/cb=%.2e\n",
            frac, i*0.1, i*0.1/20.305, cox, csub)
end

fracwalk(180, 120,  2.0)     # the current defaults -- reproduce the stall
fracwalk(180, 4000, 2.0)     # (a) same clamp, far more iterations
fracwalk(180, 4000, 0.5)     # (a') smaller clamp, more iterations: gentler but slower
