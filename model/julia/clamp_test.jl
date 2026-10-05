## COMPONENTWISE vs GLOBAL STEP CLAMPING.
## newton_ec_ccontrol! rescales the WHOLE Newton step so its largest component is <= max_step:
##     mx = maximum(abs.(dv)); mx > max_step && (dv .*= max_step / mx)
## In the dead zone behind the reaction front the substrate log-variable has an enormous Newton
## step -- it is a variable whose value is 1e-22 of bulk and which reacts with nothing -- so one
## irrelevant component throttles every other variable by the same factor. That is why a 0.5%
## change in surface depletion cannot be taken within 120 iterations.
## Componentwise clamping limits each variable's movement without throttling the others. This is
## a local copy of the production routine with ONLY that line changed, so the comparison isolates it.
D=@__DIR__
include(joinpath(D,"params.jl")); include(joinpath(D,"correlations.jl")); include(joinpath(D,"npp_ecprime.jl"))
using LinearAlgebra
tr(x)=1e-6*x

function newton_cc_clamped!(u::Vector{Float64}, iapp_ref::Vector{Float64}, p::ECProblem,
                            frac::Float64; tol = 1e-9, max_iter = 120, max_step = 2.0)
    n = nvars(p)
    ired = findfirst(s -> s.s < 0, p.sp)
    ktgt = lidx(p, 1, ired); tgt = log(frac * p.sp[ired].c_bulk)
    v = vcat(u, log(iapp_ref[1]))
    R = zeros(n+1); Rp = zeros(n+1); J = zeros(n+1, n+1); Jb = zeros(n, n)
    Fw = zeros(n); uw = zeros(n)
    function resid!(Rv, vv)
        @inbounds for k in 1:n; uw[k] = vv[k]; end
        residual_ec!(Fw, uw, p, exp(vv[n+1]))
        @inbounds for k in 1:n; Rv[k] = Fw[k]; end
        Rv[n+1] = vv[ktgt] - tgt; Rv
    end
    resid!(R, v)
    for _ in 1:max_iter
        nrm = norm(R, Inf)
        if nrm < tol
            @inbounds for k in 1:n; u[k] = v[k]; end
            iapp_ref[1] = exp(v[n+1]); return true
        end
        fill!(J, 0.0)
        @inbounds for k in 1:n; uw[k] = v[k]; end
        jacobian_ec!(Jb, uw, p, exp(v[n+1]))
        @inbounds for r in 1:n, cc in 1:n; J[r, cc] = Jb[r, cc]; end
        let h = 1e-7 * max(abs(v[n+1]), 1.0)
            vp = copy(v); vp[n+1] = v[n+1] + h
            resid!(Rp, vp)
            @inbounds for r in 1:(n+1); J[r, n+1] = (Rp[r] - R[r]) / h; end
        end
        J[n+1, ktgt] = 1.0
        dv = try -(J \ R) catch; -((J'*J + 1e-10I) \ (J'*R)) end
        any(!isfinite, dv) && return false
        @inbounds for kk in eachindex(dv)                 ## <-- THE ONLY CHANGE
            dv[kk] = clamp(dv[kk], -max_step, max_step)
        end
        lam = 1.0; vnew = similar(v)
        for _ in 1:12
            vnew .= v .+ lam .* dv
            resid!(Rp, vnew)
            (norm(Rp, Inf) < nrm || lam < 1e-3) && break
            lam /= 2
        end
        v .= vnew; resid!(R, v)
    end
    ok = norm(R, Inf) < tol
    ok && (@inbounds for k in 1:n; u[k] = v[k]; end; iapp_ref[1] = exp(v[n+1]))
    ok
end

sp = [ECSpecies("Br-", -1.0, 2.08e-9, 152.001, -1.0, +1.0),
      ECSpecies("Br2",  0.0, 1.2e-9,  tr(152.),+0.5, -1.0),
      ECSpecies("Sub",  0.0, 6.25e-10, 121.,    0.0, -1.0),
      ECSpecies("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),
      ECSpecies("Na+", +1.0, 1.33e-9, 152.,     0.0,  0.0)]
km = 1e3/1000.0; d = 300e-6
xk = sqrt(sp[2].D/(km*sp[3].c_bulk))
i_t0 = F_const*sp[1].D*152.0/(abs(sp[1].s)*d)

function run(N, newton!; frac_end=1.5e-3, nk=40)
    mk = kk -> ECProblem(sp, 2, 3, kk, geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/N), N))
    p0 = mk(0.0)
    i0, l0, us, is_ = solve_ilim_ec(p0; i_start=0.02*i_t0, growth=1.15)
    rc0 = solve_ilim_ec_ccontrol(p0; u0=us, i0=is_)
    u = copy(rc0[3]); iv = [rc0[1]]
    newton!(u, iv, p0, 0.5) || return println("   stage A failed")
    t = 0.0; dt = 1.0/nk                                  # stage B: fixed depletion, walk k
    while t < 1.0
        t_try = min(t+dt, 1.0); k_try = km*t_try^2
        p_s = mk(k_try); u_s = copy(u); i_s = [iv[1]]
        if newton!(u_s, i_s, p_s, 0.5); u, iv, t = u_s, i_s, t_try; dt = min(dt*1.3, 2/nk)
        else; dt /= 2; dt < 1e-6 && return println("   stage B stalled"); end
    end
    pk = mk(km); frac = 0.5; ratio = 0.93; nfail = 0; i = iv[1]
    while frac > frac_end                                  # stage C: walk depletion down
        f_try = max(frac*ratio, frac_end)
        u_t = copy(u); i_t = [i]
        if newton!(u_t, i_t, pk, f_try)
            u, i, frac = u_t, i_t[1], f_try; nfail = 0; ratio = max(0.93, 1-(1-ratio)*1.3)
        else
            nfail += 1; ratio = 1 - (1-ratio)/2
            (nfail > 30 || ratio > 0.99999) && return @printf("   STALLED at frac=%.3e  i=%.4f\n", frac, i*0.1)
        end
    end
    @printf("   REACHED frac=%.3e  i=%9.4f mA/cm2   x%.4f vs floor 20.305\n", frac, i*0.1, i*0.1/20.305)
end
for N in (90, 180, 360)
    @printf("N=%d  global clamp (production)\n", N);      run(N, newton_ec_ccontrol!)
    @printf("N=%d  componentwise clamp\n", N);            run(N, newton_cc_clamped!)
    flush(stdout)
end
