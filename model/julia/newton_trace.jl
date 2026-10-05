## TRACE ONE FAILING DEPLETION STEP.
## The depletion walk stalls wherever it starts (frac 0.5 from 0.5; frac 0.049 from 0.049), so it
## is not a turning point -- newton_ec_ccontrol! cannot take ANY step in depletion for this cell,
## while the current-controlled newton_ec! works on the same states. Print the residual history of
## a single step to see whether it diverges, oscillates, or plateaus, and print WHICH equation
## carries the infinity norm, since that names the culprit.
D=@__DIR__
include(joinpath(D,"params.jl")); include(joinpath(D,"correlations.jl")); include(joinpath(D,"npp_ecprime.jl"))
using LinearAlgebra
tr(x)=1e-6*x
sp = [ECSpecies("Br-", -1.0, 2.08e-9, 152.001, -1.0, +1.0),
      ECSpecies("Br2",  0.0, 1.2e-9,  tr(152.),+0.5, -1.0),
      ECSpecies("Sub",  0.0, 6.25e-10, 121.,    0.0, -1.0),
      ECSpecies("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),
      ECSpecies("Na+", +1.0, 1.33e-9, 152.,     0.0,  0.0)]
km = 1e3/1000.0; d = 300e-6; N = 90
xk = sqrt(sp[2].D/(km*sp[3].c_bulk))
i_t0 = F_const*sp[1].D*152.0/(abs(sp[1].s)*d)
mk = kk -> ECProblem(sp, 2, 3, kk, geometric_faces(d, clamp(xk/50, 0.02e-6, 0.9*d/N), N))

## reach the frac = 0.5 state at the production k
p0 = mk(0.0)
i0, l0, us, is_ = solve_ilim_ec(p0; i_start=0.02*i_t0, growth=1.15)
rc0 = solve_ilim_ec_ccontrol(p0; u0=us, i0=is_)
u = copy(rc0[3]); iv = [rc0[1]]
newton_ec_ccontrol!(u, iv, p0, 0.5) || error("stage A failed")
t = 0.0; dt = 1/40
while t < 1.0
    global t, dt, u, iv
    tt = min(t+dt, 1.0); ks = km*tt^2
    ps = mk(ks); ut = copy(u); it = [iv[1]]
    if newton_ec_ccontrol!(ut, it, ps, 0.5); u, iv, t = ut, it, tt; dt = min(dt*1.3, 2/40)
    else; dt /= 2; dt < 1e-6 && error("stage B stalled"); end
end
p = mk(km)
@printf("at k=%.3g, frac=0.5, i=%.4f mA/cm2\n\n", km, iv[1]*0.1)

## now trace ONE step to frac = 0.49
n = nvars(p); ired = 1; ktgt = lidx(p,1,ired); tgt = log(0.49*p.sp[ired].c_bulk)
v = vcat(u, log(iv[1]))
R = zeros(n+1); Rp = zeros(n+1); J = zeros(n+1,n+1); Jb = zeros(n,n); Fw = zeros(n); uw = zeros(n)
function resid!(Rv, vv)
    for k in 1:n; uw[k] = vv[k]; end
    residual_ec!(Fw, uw, p, exp(vv[n+1]))
    for k in 1:n; Rv[k] = Fw[k]; end
    Rv[n+1] = vv[ktgt] - tgt; Rv
end
names = [s.name for s in p.sp]
function where_max(Rv)
    k = argmax(abs.(Rv))
    k == n+1 && return "constraint row"
    ix = div(k-1, length(p.sp)+1) + 1; j = k - (ix-1)*(length(p.sp)+1)
    j == length(p.sp)+1 ? @sprintf("potential @ node %d (x=%.2f um)", ix, 0.5*(p.xf[ix]+p.xf[ix+1])*1e6) :
                          @sprintf("%s @ node %d (x=%.2f um)", names[j], ix, 0.5*(p.xf[ix]+p.xf[ix+1])*1e6)
end
resid!(R, v)
@printf("%4s %14s %14s  %s\n", "it", "|R|inf", "lambda", "argmax |R| is")
for it in 1:40
    global v, R
    nrm = norm(R, Inf)
    @printf("%4d %14.4e %14s  %s\n", it, nrm, "", where_max(R))
    nrm < 1e-9 && (println("converged"); break)
    fill!(J, 0.0)
    for k in 1:n; uw[k] = v[k]; end
    jacobian_ec!(Jb, uw, p, exp(v[n+1]))
    for r in 1:n, cc in 1:n; J[r,cc] = Jb[r,cc]; end
    let h = 1e-7*max(abs(v[n+1]),1.0)
        vp = copy(v); vp[n+1] = v[n+1]+h; resid!(Rp, vp)
        for r in 1:(n+1); J[r,n+1] = (Rp[r]-R[r])/h; end
    end
    J[n+1, ktgt] = 1.0
    dv = try -(J \ R) catch; -((J'*J + 1e-10I) \ (J'*R)) end
    any(!isfinite, dv) && (println("non-finite step"); break)
    mx = maximum(abs.(dv))
    @printf("        Newton step: max|dv| = %.3e at %s ; global scale factor = %.3e\n",
            mx, where_max(dv), mx > 2.0 ? 2.0/mx : 1.0)
    mx > 2.0 && (dv .*= 2.0/mx)
    lam = 1.0; vnew = similar(v)
    for _ in 1:12
        vnew .= v .+ lam.*dv; resid!(Rp, vnew)
        (norm(Rp, Inf) < nrm || lam < 1e-3) && break
        lam /= 2
    end
    v .= vnew; resid!(R, v)
end
