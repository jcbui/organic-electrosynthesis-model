## Is the FORWARD-difference Jacobian what stops the hard cells reaching tol = 1e-9?
##
## A forward difference has O(h) truncation + O(eps/h) round-off, minimised near h ~ sqrt(eps),
## giving ~1e-8 relative accuracy. Newton's achievable residual is bounded by the Jacobian's
## accuracy, so tol = 1e-9 may simply be UNREACHABLE with forward differences -- in which case
## the three non-converging cells are a solver-construction problem, not physics.
## A central difference is O(h^2) + O(eps/h), ~1e-11 near h ~ eps^(1/3): 1000x better.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end

"""newton_ec! with a CENTRAL-difference Jacobian; otherwise identical."""
function newton_ec_cd!(u::Vector{Float64}, p::ECProblem, i_app::Float64;
                       tol = 1e-9, max_iter = 120, max_log_step = 3.0)
    n = nvars(p)
    Fv = zeros(n); Fp = zeros(n); Fm = zeros(n); J = zeros(n, n)
    residual_ec!(Fv, u, p, i_app)
    for _ in 1:max_iter
        nrm = norm(Fv, Inf)
        nrm < tol && return (true, nrm)
        up = copy(u)
        for kk in 1:n
            h = cbrt(eps()) * max(abs(u[kk]), 1.0)
            up[kk] = u[kk] + h; residual_ec!(Fp, up, p, i_app)
            up[kk] = u[kk] - h; residual_ec!(Fm, up, p, i_app)
            @inbounds for r in 1:n
                J[r, kk] = (Fp[r] - Fm[r]) / (2h)
            end
            up[kk] = u[kk]
        end
        du = try -(J \ Fv) catch; -((J' * J + 1e-10I) \ (J' * Fv)) end
        any(!isfinite, du) && return (false, nrm)
        mx = maximum(abs.(du)); mx > max_log_step && (du .*= max_log_step / mx)
        lam = 1.0; unew = similar(u)
        for _ in 1:12
            unew .= u .+ lam .* du
            residual_ec!(Fp, unew, p, i_app)
            (norm(Fp, Inf) < nrm || lam < 1e-3) && break
            lam /= 2
        end
        u .= unew
        residual_ec!(Fv, u, p, i_app)
    end
    (norm(Fv, Inf) < tol, norm(Fv, Inf))
end

## The three cells that will not converge, at a current just under their reported value.
CASES = [("Br- oxidation / electrophilic bromination", :natural,  0.95),
         ("Br- oxidation / electrophilic bromination", :stirred,  0.95),
         ("Br-mediated Hofmann rearrangement",         :natural,  0.95)]

@printf("%-42s %-9s %12s %12s  %s\n", "cell", "reactor", "fwd-diff", "central", "verdict")
for (nm, rk, frac) in CASES
    spec = SPECS[findfirst(x -> x.label == nm, SPECS)]
    km = spec.k_M/1000.0; xk = sqrt(spec.species[2].D/(km*spec.C_S))
    isb = findfirst(s -> s.name == "Sub", spec.species)
    r = REACTORS[findfirst(x -> x.key == rk, REACTORS)]
    d = delta_eff(r.key, spec.D_red, spec.nu_solv)
    i_t0 = F_const*spec.D_red*spec.C_med/(abs(spec.species[1].s)*d)
    p = ECProblem(spec.species, 2, isb, km, geometric_faces(d, clamp(xk/50,0.02e-6,0.9*d/90), 90))
    ## ramp both to the same place, then compare the residual each can reach
    ia = 0.02*i_t0
    u = zeros(nvars(p)); for ix in 1:nnode(p), j in 1:length(p.sp)
        u[lidx(p,ix,j)] = log(max(p.sp[j].c_bulk,1e-6)) end
    ok = true
    while ok && ia < 0.9*i_t0*frac
        ok = newton_ec!(u, p, ia; max_iter=120, max_log_step=3.0); ia *= 1.15
    end
    uf = copy(u); uc = copy(u)
    okf = newton_ec!(uf, p, ia; max_iter=200, max_log_step=3.0)
    Ff = zeros(nvars(p)); residual_ec!(Ff, uf, p, ia); rf = norm(Ff, Inf)
    okc, rc = newton_ec_cd!(uc, p, ia; max_iter=200, max_log_step=3.0)
    @printf("%-42s %-9s %12.2e %12.2e  %s\n", first(nm,42), string(rk), rf, rc,
            rc < 1e-9 ? "CENTRAL REACHES tol" : (rc < rf/10 ? "central much better" : "both limited"))
    flush(stdout)
end
