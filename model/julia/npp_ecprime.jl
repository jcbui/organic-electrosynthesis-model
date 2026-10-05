## npp_ecprime.jl — Tier 2: mediated electrolysis as an EC' reaction–diffusion
## problem across the film. The electrode exchanges electrons ONLY with the
## mediator couple (Med_red/Med_ox); the substrate reacts homogeneously with
## Med_ox throughout the electrolyte:
##
##      electrode:    Med_red  ->  Med_ox + e-        (anodic, n_c = 1)
##      film/bulk:    Med_ox + S  -k->  Med_red + P   (bimolecular, rate k c_ox c_S)
##
## FV residual per cell: J_left - J_right + nu_j * R * dx = 0  (co2r_bulk form,
## cf. buffer_sources!). Geometric mesh refined at the electrode resolves the
## Saveant reaction layer x_k = sqrt(D_ox / (k c_S)) down to ~0.03 um.
## Source for the EC' limits: J.-M. Saveant, "Elements of Molecular and Biomolecular
## Electrochemistry", Wiley, Hoboken NJ, 2006, Ch. 2 -- redox catalysis, and the pure-kinetic
## and total-catalysis limits that gates G6 and G7 of run_audit.jl check this code against.
## Numerics: log-concentration DOFs, damped Newton, dense FD Jacobian,
## geometric galvanostatic continuation with bisection refinement.
##
## Analytic gates:
##   k -> 0 :  i_lim -> F D_red C_med / delta                (shuttle bound)
##   mid-k  :  i_lim ≈ F C_med sqrt(D_ox k c_S)              (Saveant, slope 1/2)
##   k -> inf: i_lim -> F D_S C_S / delta                    (substrate cap;
##             total catalysis — the SUBSTRATE profile collapses, not the mediator)

using LinearAlgebra
using Printf

struct ECSpecies
    name::String
    z::Float64
    D::Float64
    c_bulk::Float64
    s::Float64         # electrode flux N_j(0) = s_j * i/F
    nu::Float64        # stoichiometry in the homogeneous step (+ produced)
end

struct ECProblem
    sp::Vector{ECSpecies}
    iox::Int           # index of Med_ox
    isub::Int          # index of S
    k::Float64         # homogeneous rate constant, m^3 mol^-1 s^-1
    xf::Vector{Float64}    # face positions, length N+1, xf[1]=0, xf[end]=delta
    xc::Vector{Float64}    # cell centers (precomputed)
    dxc::Vector{Float64}   # cell widths
    dxl::Vector{Float64}   # center-to-center spacing to the LEFT face pair
    dxr::Vector{Float64}   # spacing used on the right face of each cell
end

function ECProblem(sp, iox, isub, k, xf)
    N = length(xf) - 1
    xc  = [0.5 * (xf[i] + xf[i+1]) for i in 1:N]
    dxc = [xf[i+1] - xf[i] for i in 1:N]
    dxl = [i == 1 ? 0.0 : xc[i] - xc[i-1] for i in 1:N]
    dxr = [i == N ? (xf[end] - xc[i]) : xc[i+1] - xc[i] for i in 1:N]
    ECProblem(sp, iox, isub, k, xf, xc, dxc, dxl, dxr)
end

nnode(p::ECProblem) = length(p.xf) - 1
nvars(p::ECProblem) = (length(p.sp) + 1) * nnode(p)
lidx(p, ix, j) = (ix - 1) * (length(p.sp) + 1) + j
pidx(p, ix)   = (ix - 1) * (length(p.sp) + 1) + length(p.sp) + 1

"""Graded mesh refined at ARBITRARY interior locations, not only at the electrode.

`geometric_faces` puts its resolution at the wall, which is right when the reaction layer hugs
the electrode and wrong when the front DETACHES. Measured on Br- oxidation x unstirred: the front
sits at x_f/delta = 0.85, i.e. ~256 um out, where the geometric mesh has ~10 um cells against an
x_k of 3.16 um -- NOT ONE CELL CENTRE within +-x_k of the front. That cell will not solve on any
continuation path, and the reason is that the mesh does not resolve the physics where it happens.

Target size h(x) = min over refinement sites of dx_i * (1 + grade*|x - x_i|/dx_i), integrated to
place N cells. Pass every location that needs resolving: the electrode AND each front."""
function graded_faces(delta::Float64, N::Int, sites::Vector{Tuple{Float64,Float64}}; grade = 0.35)
    h(x) = minimum(dx * (1 + grade * abs(x - x0) / dx) for (x0, dx) in sites)
    ## integrate dx/h to get the arclength, then place N equal-arclength faces
    M = 20000; xs = range(0.0, delta; length = M)
    cum = zeros(M)
    for k in 2:M
        cum[k] = cum[k-1] + (xs[k] - xs[k-1]) / h(0.5 * (xs[k] + xs[k-1]))
    end
    total = cum[end]
    xf = zeros(N + 1)
    for f in 2:N+1
        t = total * (f - 1) / N
        k = searchsortedfirst(cum, t)
        k = clamp(k, 2, M)
        w = (t - cum[k-1]) / max(cum[k] - cum[k-1], 1e-300)
        xf[f] = xs[k-1] + w * (xs[k] - xs[k-1])
    end
    xf[end] = delta
    xf
end

"""Locate the reaction front: where the substrate profile rises through half its bulk value."""
function front_position(p::ECProblem, u::Vector{Float64})
    cs = [exp(u[lidx(p, ix, p.isub)]) for ix in 1:nnode(p)] ./ p.sp[p.isub].c_bulk
    idx = findfirst(>=(0.5), cs)
    idx === nothing && return p.xf[end]          # never recovers: front at the outer edge
    idx == 1 && return 0.0
    p.xc[idx]
end

"""geometric mesh: first cell dx1 at the electrode, stretching to fill delta."""
function geometric_faces(delta::Float64, dx1::Float64, N::Int)
    # solve (r^N - 1)/(r - 1) = delta/dx1 for r by bisection
    target = delta / dx1
    lo, hi = 1.0 + 1e-12, 2.0
    for _ in 1:200
        r = 0.5 * (lo + hi)
        s = (r^N - 1) / (r - 1)
        s < target ? (lo = r) : (hi = r)
    end
    r = 0.5 * (lo + hi)
    xf = zeros(N + 1); dx = dx1
    for f in 2:N+1
        xf[f] = xf[f-1] + dx; dx *= r
    end
    xf .*= delta / xf[end]
    return xf
end

np_flux_ec(D, z, cL, cR, phiL, phiR, dx) =
    -D * (cR - cL) / dx - z * D / RT_F * 0.5 * (cL + cR) * (phiR - phiL) / dx

function residual_ec!(Fv::Vector{Float64}, u::Vector{Float64}, p::ECProblem, i_app::Float64)
    ns = length(p.sp); N = nnode(p)
    ## LOWERED -50 -> -300 on 2026-08-23. exp(-50) = 1.9e-22 mol m^-3 is a hard concentration
    ## FLOOR, not the log-STEP clamp the SI discloses. Where it binds the residual becomes
    ## exactly independent of that DOF, its finite-difference Jacobian column is exactly zero,
    ## the LU throws, and control diverts silently to the regularised least-squares branch. Two
    ## independent audits found it firing in 3 of 48 production cells (min log c reaching -52)
    ## and moving a PUBLISHED integer: the unstirred >=25 count reads 12/50 at -50 and 11/50 at
    ## -120 or -300. exp(-300) = 5e-131 is far below any physically meaningful concentration
    ## (exp(-50) is already ~10 molecules per m^3) and far above the float64 underflow at
    ## exp(-745), so at -300 the floor cannot bind and cannot silently zero a column.
    c   = [exp(clamp(u[lidx(p, ix, j)], -300.0, 50.0)) for j in 1:ns, ix in 1:N]
    phi = [u[pidx(p, ix)] for ix in 1:N]
    delta = p.xf[end]
    cscale = maximum(s.c_bulk for s in p.sp)
    ## trace-species floor at 1% of the dominant concentration: a floor tied to the
    ## trace bulk itself (e.g. 1e-3 mol/m^3 H+) makes that residual row O(1e4-1e5)
    ## and needlessly stiffens the line search (audit finding, SI S5.6)
    ## RESIDUAL SCALE (2026-09-05): each species' conservation residual is divided by a reference
    ## flux D_j c_ref / delta. c_ref used to be the species' BULK concentration (floored at 1 % of
    ## the largest bulk). For an electrogenerated species that is a trace in the bulk and molar at
    ## the electrode -- the oxidant of the chloride ex-cell system, 0.02 mol/m3 in the bulk and
    ## 5.8 M at its carrier limit -- that scale is ~150x too small: the first-cell terms D c/dx1
    ## scale to O(1e6) and the absolute Newton tolerance of 1e-9 sits below the double-precision
    ## floor, so Newton "fails" on a branch that exists. The scale carries 1/delta, which is why
    ## the failure appeared only on thick films (52 % of the limit reached at 200 um, 86 % at
    ## 100 um, the limit itself at <= 50 um) and moved with nothing else -- not the reaction, the
    ## substrate, the mesh at either edge, or the proton mobility (all bisected). Including the
    ## species' largest in-film concentration in c_ref changes only the SCALING of each equation,
    ## never its root, and the 200 um walk then reaches 2.0015x Fick. The scale is recomputed from
    ## the current iterate; its derivative is omitted from the Jacobian (an inexact-Newton term of
    ## relative size ~ one part in the residual, harmless).
    rscale = [p.sp[j].D * max(p.sp[j].c_bulk, 0.01 * cscale, maximum(@view c[j, :])) / delta for j in 1:ns]
    for ix in 1:N
        R = p.k * c[p.iox, ix] * c[p.isub, ix]               # homogeneous EC' rate
        for j in 1:ns
            spj = p.sp[j]
            Jl = ix == 1 ? spj.s * i_app / F_const :
                 np_flux_ec(spj.D, spj.z, c[j, ix-1], c[j, ix], phi[ix-1], phi[ix], p.dxl[ix])
            Jr = ix == N ? np_flux_ec(spj.D, spj.z, c[j, ix], spj.c_bulk, phi[ix], 0.0, p.dxr[ix]) :
                 np_flux_ec(spj.D, spj.z, c[j, ix], c[j, ix+1], phi[ix], phi[ix+1], p.dxr[ix])
            Fv[lidx(p, ix, j)] = (Jl - Jr + spj.nu * R * p.dxc[ix]) / rscale[j]
        end
        Fv[pidx(p, ix)] = sum(p.sp[j].z * c[j, ix] for j in 1:ns) / cscale
    end
    return Fv
end

## ── analytic Jacobian ─────────────────────────────────────────────────────────────────────
## Added 2026-08-23. The finite-difference Jacobian costs nvars residual evaluations per Newton
## iteration (630 for a 6-species/90-cell problem) and, more importantly, its conditioning is
## poor enough on the deep-total-catalysis cells that Newton does not converge there at all --
## Br- oxidation x unstirred stalls at residual 14 with BOTH forward and central differences, so
## it is not a precision problem. The residual is analytic, so the exact Jacobian is available.
##
## u = log c throughout, so dc/du = c (and 0 wherever the clamp binds -- which it should not,
## at -300, but the derivative is written to respect it rather than assume it).
##
## np_flux_ec(D, z, cL, cR, phiL, phiR, dx) = -D (cR - cL)/dx - (z D / RT_F) (cL + cR)/2 dphi/dx
##   d/dcL   =  D/dx - g/2 dphi        d/dphiL = +g (cL + cR)/2
##   d/dcR   = -D/dx - g/2 dphi        d/dphiR = -g (cL + cR)/2      with g = z D / (RT_F dx)
##
## VERIFY IT, DO NOT TRUST IT: `jacobian_check(p, u, i_app)` compares every entry against a
## central difference and is exercised by run_audit.jl G13 on production states. An analytic
## Jacobian that is subtly wrong is worse than a slow one, because Newton still limps toward a
## solution and only the convergence RATE betrays it.
function jacobian_ec!(J::Matrix{Float64}, u::Vector{Float64}, p::ECProblem, i_app::Float64)
    ns = length(p.sp); N = nnode(p)
    fill!(J, 0.0)
    uc  = [clamp(u[lidx(p, ix, j)], -300.0, 50.0) for j in 1:ns, ix in 1:N]
    c   = exp.(uc)
    ## dc/du is c where the clamp is inactive and 0 where it binds
    dcdu = [(-300.0 < u[lidx(p, ix, j)] < 50.0) ? c[j, ix] : 0.0 for j in 1:ns, ix in 1:N]
    phi = [u[pidx(p, ix)] for ix in 1:N]
    delta = p.xf[end]
    cscale = maximum(s.c_bulk for s in p.sp)
    ## RESIDUAL SCALE (2026-09-05): each species' conservation residual is divided by a reference
    ## flux D_j c_ref / delta. c_ref used to be the species' BULK concentration (floored at 1 % of
    ## the largest bulk). For an electrogenerated species that is a trace in the bulk and molar at
    ## the electrode -- the oxidant of the chloride ex-cell system, 0.02 mol/m3 in the bulk and
    ## 5.8 M at its carrier limit -- that scale is ~150x too small: the first-cell terms D c/dx1
    ## scale to O(1e6) and the absolute Newton tolerance of 1e-9 sits below the double-precision
    ## floor, so Newton "fails" on a branch that exists. The scale carries 1/delta, which is why
    ## the failure appeared only on thick films (52 % of the limit reached at 200 um, 86 % at
    ## 100 um, the limit itself at <= 50 um) and moved with nothing else -- not the reaction, the
    ## substrate, the mesh at either edge, or the proton mobility (all bisected). Including the
    ## species' largest in-film concentration in c_ref changes only the SCALING of each equation,
    ## never its root, and the 200 um walk then reaches 2.0015x Fick. The scale is recomputed from
    ## the current iterate; its derivative is omitted from the Jacobian (an inexact-Newton term of
    ## relative size ~ one part in the residual, harmless).
    rscale = [p.sp[j].D * max(p.sp[j].c_bulk, 0.01 * cscale, maximum(@view c[j, :])) / delta for j in 1:ns]

    for ix in 1:N
        R = p.k * c[p.iox, ix] * c[p.isub, ix]
        for j in 1:ns
            spj = p.sp[j]; row = lidx(p, ix, j); rs = rscale[j]

            ## ---- left face: Jl enters with +1 -------------------------------------------
            if ix > 1
                dx = p.dxl[ix]; g = spj.z * spj.D / RT_F / dx
                dphi = phi[ix] - phi[ix-1]; csum = c[j, ix-1] + c[j, ix]
                J[row, lidx(p, ix-1, j)] += ( spj.D/dx - 0.5g*dphi) * dcdu[j, ix-1] / rs
                J[row, lidx(p, ix,   j)] += (-spj.D/dx - 0.5g*dphi) * dcdu[j, ix]   / rs
                J[row, pidx(p, ix-1)]    += ( 0.5g*csum) / rs
                J[row, pidx(p, ix)]      += (-0.5g*csum) / rs
            end                                    # ix == 1: Jl = s_j i/F, constant

            ## ---- right face: Jr enters with -1 ------------------------------------------
            dx = p.dxr[ix]; g = spj.z * spj.D / RT_F / dx
            if ix < N
                dphi = phi[ix+1] - phi[ix]; csum = c[j, ix] + c[j, ix+1]
                J[row, lidx(p, ix,   j)] -= ( spj.D/dx - 0.5g*dphi) * dcdu[j, ix]   / rs
                J[row, lidx(p, ix+1, j)] -= (-spj.D/dx - 0.5g*dphi) * dcdu[j, ix+1] / rs
                J[row, pidx(p, ix)]      -= ( 0.5g*csum) / rs
                J[row, pidx(p, ix+1)]    -= (-0.5g*csum) / rs
            else                                   # bulk Dirichlet: cR = c_bulk, phiR = 0
                dphi = 0.0 - phi[ix]; csum = c[j, ix] + spj.c_bulk
                J[row, lidx(p, ix, j)] -= ( spj.D/dx - 0.5g*dphi) * dcdu[j, ix] / rs
                J[row, pidx(p, ix)]    -= ( 0.5g*csum) / rs
            end

            ## ---- homogeneous source: + nu_j R dxc ----------------------------------------
            if p.k != 0.0 && spj.nu != 0.0
                f = spj.nu * p.dxc[ix] * p.k / rs
                if p.iox == p.isub
                    J[row, lidx(p, ix, p.iox)] += f * 2 * c[p.iox, ix] * dcdu[p.iox, ix]
                else
                    J[row, lidx(p, ix, p.iox)]  += f * c[p.isub, ix] * dcdu[p.iox, ix]
                    J[row, lidx(p, ix, p.isub)] += f * c[p.iox, ix]  * dcdu[p.isub, ix]
                end
            end
        end
        ## ---- electroneutrality row ------------------------------------------------------
        prow = pidx(p, ix)
        for j in 1:ns
            J[prow, lidx(p, ix, j)] = p.sp[j].z * dcdu[j, ix] / cscale
        end
    end
    J
end

"""Compare `jacobian_ec!` against a central-difference Jacobian at (u, i_app).

Returns (max_abs_err, max_rel_err, worst_row, worst_col). Central differences are ~1e-11
accurate, so a correct analytic Jacobian should agree to roughly that, scaled by entry size."""
function jacobian_check(p::ECProblem, u::Vector{Float64}, i_app::Float64)
    n = nvars(p)
    Ja = zeros(n, n); jacobian_ec!(Ja, u, p, i_app)
    Jn = zeros(n, n)
    Fp = zeros(n); Fm = zeros(n); up = copy(u)
    for kk in 1:n
        h = cbrt(eps()) * max(abs(u[kk]), 1.0)
        up[kk] = u[kk] + h; residual_ec!(Fp, up, p, i_app)
        up[kk] = u[kk] - h; residual_ec!(Fm, up, p, i_app)
        @inbounds for r in 1:n
            Jn[r, kk] = (Fp[r] - Fm[r]) / (2h)
        end
        up[kk] = u[kk]
    end
    scale = maximum(abs, Jn)
    maxabs = 0.0; maxrel = 0.0; wr = 0; wc = 0
    for r in 1:n, cc in 1:n
        d = abs(Ja[r, cc] - Jn[r, cc])
        rel = d / max(abs(Jn[r, cc]), 1e-8 * scale)
        d > maxabs && (maxabs = d)
        if rel > maxrel; maxrel = rel; wr = r; wc = cc; end
    end
    (maxabs, maxrel, wr, wc, scale)
end


## ---------------------------------------------------------------------------------------------
## TRUST REGION THAT IGNORES VARIABLES WHICH CANNOT MATTER
## ---------------------------------------------------------------------------------------------
## Both Newton routines limit the step by rescaling the WHOLE vector so its largest component
## moves at most max_step in log space:
##       mx = maximum(abs.(du)); mx > max_step && (du .*= max_step / mx)
## That rule assumes every component is meaningful. Behind a reaction front it is not. In
## Br- oxidation x unstirred the substrate sits at ~1e-22 of bulk across a 150 um dead zone where
## it reacts with nothing; its equation there is nearly singular and the linear solve returns
## components of 1e9 to 1e12 for it. Rescaling on THAT multiplies the entire step by ~1e-12, so
## the variable that actually has to move cannot. Traced directly: asking for a 2% change in
## surface depletion, |R|inf stayed pinned at 2.0203e-02 -- exactly |log(0.49/0.5)|, i.e. no
## progress whatsoever on the constraint -- for every iteration, while the scale factor ran from
## 7.1e-10 down to 5.1e-13, the largest component being "Sub" at x = 0.03-2.8 um each time.
##
## So exclude from the rescaling norm any component that is a species concentration below
## NEGLIGIBLE_C of that species' bulk value, and clamp those components individually instead.
## They contribute a homogeneous source more than ten orders of magnitude below the front, so no
## reported quantity can depend on them.
##
## Two properties make this safe rather than a fudge:
##   * where no species is below the threshold the rule is IDENTICAL to the old one, so the k = 0
##     solves (substrate uniform at bulk) and every cell without a detached front are untouched;
##   * it is falsifiable -- sweep NEGLIGIBLE_C over decades and the answer must not move, and
##     every cell that converged before must still return the same limit.
## A Ref, not a bare const, so the sweep in `julia/negligible_sweep.jl` can vary it at run time
## and demonstrate that no reported number depends on where it sits. Production value 1e-10.
const NEGLIGIBLE_C = Ref(1e-10)

function limit_step!(dv::Vector{Float64}, v::Vector{Float64}, p::ECProblem, max_step::Float64)
    ns = length(p.sp); nv = nvars(p); mx = 0.0
    @inbounds for k in eachindex(dv)
        counts = true
        if k <= nv
            j = k - div(k - 1, ns + 1) * (ns + 1)          # 1..ns species, ns+1 potential
            if j <= ns && exp(v[k]) < NEGLIGIBLE_C[] * p.sp[j].c_bulk
                counts = false
            end
        end
        counts && (mx = max(mx, abs(dv[k])))
    end
    mx > max_step && (dv .*= max_step / mx)
    @inbounds for k in eachindex(dv)
        dv[k] = clamp(dv[k], -max_step, max_step)
    end
    dv
end

function newton_ec!(u::Vector{Float64}, p::ECProblem, i_app::Float64;
                    tol = 1e-9, max_iter = 80, max_log_step = 2.0)
    n = nvars(p)
    Fv = zeros(n); Fp = zeros(n); J = zeros(n, n)
    residual_ec!(Fv, u, p, i_app)
    for _ in 1:max_iter
        nrm = norm(Fv, Inf)
        nrm < tol && return true
        ## ANALYTIC Jacobian (jacobian_ec!), verified against central differences to 4.5e-8
        ## worst-case over all 8 systems x 2 archetypes x 2 currents, and gated by G13.
        ## This replaced an n-evaluation FORWARD difference whose conditioning left the
        ## deep-total-catalysis cells unconvergeable at any tolerance.
        jacobian_ec!(J, u, p, i_app)
        du = try
            -(J \ Fv)
        catch
            -((J' * J + 1e-10I) \ (J' * Fv))
        end
        any(!isfinite, du) && return false
        limit_step!(du, u, p, max_log_step)
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
    ## ENFORCE THE DECLARED TOLERANCE. This read `norm(Fv, Inf) < 1e-6` -- 1000x looser than the
    ## `tol = 1e-9` in this function's own signature -- so a Newton solve that exhausted its
    ## iterations was accepted as converged at a residual it never claimed to reach. It was not
    ## documented anywhere, and it decided a published integer: enforcing tol moves six of the 48
    ## production cells, one of them (Br- oxidation x unstirred, 36.84 -> 11.19) below its own
    ## commuting bound, taking the unstirred >=25 count from 12/50 to 11/50.
    return norm(Fv, Inf) < tol
end

"""Geometric galvanostatic ramp with bisection refinement.
Returns (i_lim [A/m^2], limiter::String, u_at_0.9ilim)."""
function solve_ilim_ec(p::ECProblem; i_start::Float64, growth = 1.15, u0 = nothing)
    N = nnode(p); ns = length(p.sp)
    u = zeros(nvars(p))
    if u0 === nothing
        for ix in 1:N, j in 1:ns
            u[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-6))
        end
    else
        u .= u0
    end
    ired = findfirst(s -> s.s < 0, p.sp)
    ## Collapse = starvation of the ELECTROACTIVE reduced species only. Substrate
    ## surface collapse is NOT terminal: in total catalysis (and in dilute-substrate
    ## ex-cell systems) the substrate profile collapses at a reaction front while the
    ## mediator keeps carrying current. The substrate state only labels the limiter.
    collapsed(u) = begin
        cred = exp(u[lidx(p, 1, ired)]) / p.sp[ired].c_bulk
        csub = exp(u[lidx(p, 1, p.isub)]) / p.sp[p.isub].c_bulk
        (cred < 1e-3, csub < 1e-2 ? "substrate (total catalysis)" : "mediator")
    end
    ia = i_start; i_ok = 0.0; lim = "none"; u_ok = copy(u); u_safe = copy(u); i_safe = 0.0
    while ia < i_start * 1e5
        ok = newton_ec!(u, p, ia; max_iter = 120, max_log_step = 3.0)
        ok || break
        i_ok = ia; u_ok .= u
        col, which = collapsed(u)
        col && (lim = which; break)
        u_safe .= u; i_safe = ia
        ia *= growth
    end
    if lim == "none"
        ## ramp ended on a Newton failure, not on collapse: bisect toward the wall,
        ## and label honestly — nothing has collapsed (audit finding, SI S5.6)
        lo, hi = i_ok, ia
        for _ in 1:6
            mid = 0.5 * (lo + hi)
            v = copy(u_ok)
            newton_ec!(v, p, mid) ? (lo = mid; u_ok .= v) : (hi = mid)
        end
        i_ok = lo
        col, which = collapsed(u_ok)
        ## The ramp ended on a NEWTON FAILURE, not on the collapse criterion, so i_ok is a lower
        ## bound whatever the state looks like at that current. This used to read
        ##     lim = col ? which : "newton-wall (no collapse)"
        ## which re-evaluated collapsed() at the stalled current and, when it happened to be true,
        ## overwrote the label with a PHYSICAL limiter -- erasing the fact that the value is a
        ## wall. A census of the 48 production cells found 44 ended on a Newton failure and 14 of
        ## them were being relabelled this way, so SI Table S6 marked far fewer rows as bounds
        ## than actually are. The marker is PREFIXED so that every existing consumer's
        ## startswith("newton-wall") test -- combined_figure.py's ">=" prefix and its _conv
        ## filter, make_figH_ecprime.py's open markers -- now sees all 44.
        lim = col ? ("newton-wall; " * which) : "newton-wall (no collapse)"
    else
        ## ramp ended on collapse: refine the crossing of the c_red = 1e-3 criterion
        ## between the last pre-collapse current and the first collapsed one, so the
        ## reported i_lim is not quantized by the ramp growth factor
        if i_safe > 0.0
            lo, hi = i_safe, i_ok
            v_lo = copy(u_safe)
            for _ in 1:6
                mid = 0.5 * (lo + hi)
                v = copy(v_lo)
                if newton_ec!(v, p, mid; max_iter = 120, max_log_step = 3.0)
                    col, which = collapsed(v)
                    col ? (hi = mid; lim = which) : (lo = mid; v_lo .= v; u_safe .= v; i_safe = mid)
                else
                    hi = mid
                end
            end
            i_ok = hi
        end
    end
    return i_ok, lim, u_safe, i_safe
end

## ── k-continuation ────────────────────────────────────────────────────────────────────────
## The most robust continuation available, because it starts from a solution that is known
## ANALYTICALLY rather than guessed. At k = 0 the EC' problem collapses to pure mediator
## oxidation with the oxidised form diffusing away, whose limiting current is exactly the
## commuting bound i_t0 = F D_red C_med / (|s| delta) -- gate G5 verifies the solver reproduces
## it to 0.13%. Walking k up from there to the production value follows the branch continuously,
## with the current held at a fixed fraction of the local limit so the state stays well inside
## the solvable region. Raising k at fixed current makes the problem EASIER (more mediator is
## regenerated near the wall), so the walk is climbing a gradient rather than fighting one.
##
## This is what finally reaches the inverted (gamma < 1) deep-total-catalysis cells, where the
## substrate is scarcer than the mediator and both the current ramp and delta-continuation fail:
## they start from a bulk state that is not connected to the working branch at that delta/x_k.

"""Solve for i_lim by continuing in the homogeneous rate constant from the analytic k = 0 limit.

`mkproblem(k)` must return the ECProblem for rate constant `k` (same species, same mesh).
Returns the same 5-tuple as `solve_ilim_ec_ccontrol`, or `nothing` if the walk does not survive."""
function solve_ilim_ec_kcont(mkproblem, k_target::Float64, i_t0::Float64;
                             nk::Int = 30, frac_i = 0.85, k_start = 1e-6)
    p0 = mkproblem(0.0)
    ## start from the analytic k = 0 state: ramp to frac_i of the known limit i_t0
    u = zeros(nvars(p0))
    for ix in 1:nnode(p0), j in 1:length(p0.sp)
        u[lidx(p0, ix, j)] = log(max(p0.sp[j].c_bulk, 1e-6))
    end
    ia = 0.05 * i_t0
    while ia < frac_i * i_t0
        newton_ec!(u, p0, ia; max_iter = 200, max_log_step = 3.0) || return nothing
        ia = min(ia * 1.15, frac_i * i_t0)
    end
    newton_ec!(u, p0, ia; max_iter = 200, max_log_step = 3.0) || return nothing
    ## walk k up geometrically at fixed current, halving the step on any failure
    p = p0; k_now = k_start <= 0 ? k_target / 10^6 : k_start
    lk0, lk1 = log(k_now), log(k_target)
    t = 0.0; dt = 1.0 / nk
    while t < 1.0
        t_try = min(t + dt, 1.0)
        k_try = exp(lk0 + (lk1 - lk0) * t_try)
        p_try = mkproblem(k_try)
        u_try = copy(u)
        if newton_ec!(u_try, p_try, ia; max_iter = 200, max_log_step = 2.0)
            u = u_try; p = p_try; t = t_try
            dt = min(dt * 1.4, 2.0 / nk)
        else
            dt /= 2
            dt < 1e-4 && return nothing
        end
    end
    ## at the production k, read the limit off the polarisation curve
    res = solve_ilim_ec_ccontrol(p; u0 = u, i0 = ia)
    ## A CONTINUATION THAT RETURNS ITS OWN ANCHOR HAS NOT COMPUTED ANYTHING.
    ## If the c-control walk at the production k fails on its first step it hands back the current
    ## it started from, `ia` = frac_i * (the limit passed in). That looks like an answer and is not.
    ## It was caught by sweeping frac_i: 0.85/0.95/0.98/0.99 returned 17.259/19.290/19.899/20.110
    ## on a k = 0 floor of 20.305 -- exactly 0.850/0.950/0.980/0.990 of it, every time. Three
    ## successive audits had recorded that cell's value as "solved by k-continuation" on the
    ## strength of numbers produced this way.
    ## Tolerance is 2%, not machine epsilon. The walk does not always return the anchor EXACTLY:
    ## for Br- oxidation x unstirred it took one step and stopped, giving 17.2795 against an anchor
    ## of 17.2593 -- 0.12% of movement, which a 1e-6 test lets through as if it were an answer.
    ## Anything within a couple of percent of where the continuation started has not walked a
    ## polarisation curve and must not be reported as a limit.
    if abs(res[1] - ia) <= 0.02 * max(ia, 1.0)
        return nothing
    end
    res
end

## ── delta-continuation ────────────────────────────────────────────────────────────────────
## Added 2026-08-23. One production cell of 48 -- Br-mediated Hofmann in an unstirred beaker,
## delta/x_k = 128 -- cannot be reached by ramping the current from a bulk initial guess. The
## ramp dies at 0.74 mA cm-2, BELOW that cell's own commuting bound of 6.95, so it is not a
## physical answer; the pipeline floored it to Tier-0 and the manuscript's unstirred counts
## were built on that floor. Eleven mesh and continuation variants all die the same way
## (probe_hofmann_unstirred.jl), so it is not a resolution problem: at this delta/x_k the
## solution branch simply is not connected to the bulk state by a current ramp.
##
## It IS reachable by continuation in delta. The same system at delta = 100 um solves normally;
## walking delta outward in small steps, regridding the converged state onto each new mesh,
## follows the branch all the way out (probe_hofmann_homotopy.jl).

"""Interpolate a state from `p_old`'s mesh onto `p_new`'s, in ABSOLUTE x.

The reaction layer sits a fixed absolute distance from the electrode (x_k), so mapping by the
fractional coordinate x/delta would smear it as delta grows. Cells beyond the old domain are
filled with bulk values, which is what they physically are."""
function regrid(u_old::Vector{Float64}, p_old::ECProblem, p_new::ECProblem)
    ns = length(p_old.sp)
    u = zeros(nvars(p_new))
    lerp(a, b, t) = (1 - t) * a + t * b
    for (jx, x) in enumerate(p_new.xc)
        k = searchsortedfirst(p_old.xc, x)
        t = (1 < k <= length(p_old.xc)) ?
            (x - p_old.xc[k-1]) / (p_old.xc[k] - p_old.xc[k-1]) : 0.0
        for j in 1:ns
            u[lidx(p_new, jx, j)] =
                k == 1               ? u_old[lidx(p_old, 1, j)] :
                k > length(p_old.xc) ? log(max(p_old.sp[j].c_bulk, 1e-6)) :
                                       lerp(u_old[lidx(p_old, k-1, j)], u_old[lidx(p_old, k, j)], t)
        end
        u[pidx(p_new, jx)] =
            k == 1               ? u_old[pidx(p_old, 1)] :
            k > length(p_old.xc) ? 0.0 :
                                   lerp(u_old[pidx(p_old, k-1)], u_old[pidx(p_old, k)], t)
    end
    u
end

"""Reach `p_new`'s limiting current by continuation in delta from a solved smaller-delta cell.

`p_old`/`u_old`/`i_old` are a CONVERGED state at a smaller delta. The current is carried along
at the local 1/delta scale so the target tracks the physics instead of sitting still, then the
ramp is resumed at the destination. Returns `nothing` if the branch does not survive, so the
caller can fall back rather than silently accept a broken continuation."""
function solve_ilim_ec_continued(mkproblem, d_old::Float64, d_new::Float64,
                                 p_old::ECProblem, u_old::Vector{Float64}, i_old::Float64;
                                 nsteps::Int = 24, grow = 1.05, nbis::Int = 10,
                                 backoff = (1.0, 0.85, 0.70, 0.55, 0.40))
    ## The continuation is sensitive to how close the anchor sits to its OWN limit: starting
    ## from 88.8% of it the branch dies, from 85% it survives all the way. Rather than fail on
    ## that, walk the anchor current down and retry. The destination is unaffected -- the last
    ## step re-ramps and bisects at d_new -- so a lower start costs time, not accuracy.
    for f in backoff
        u_a = copy(u_old); i_a = i_old * f
        if f < 1.0
            newton_ec!(u_a, p_old, i_a; max_iter = 200, max_log_step = 2.0) || continue
        end
        p_c, u_c, i_c = p_old, u_a, i_a
        died = false
        for s in 1:nsteps
            d_s = d_old * (d_new / d_old)^(s / nsteps)
            p_s = mkproblem(d_s)
            u_s = regrid(u_c, p_c, p_s)
            i_s = i_c * (d_old * (d_new / d_old)^((s - 1) / nsteps)) / d_s
            if !newton_ec!(u_s, p_s, i_s; max_iter = 200, max_log_step = 2.0)
                died = true; break
            end
            p_c, u_c, i_c = p_s, u_s, i_s
        end
        died && continue
        ## resume the ramp at the destination delta, then bisect onto the turning point
        i_ok = i_c; u_ok = copy(u_c); ia = i_c * grow
        while ia < i_c * 50
            v = copy(u_ok)
            newton_ec!(v, p_c, ia; max_iter = 200, max_log_step = 2.0) || break
            i_ok = ia; u_ok .= v
            ia *= grow
        end
        lo, hi = i_ok, ia
        for _ in 1:nbis
            mid = 0.5 * (lo + hi); v = copy(u_ok)
            newton_ec!(v, p_c, mid; max_iter = 200, max_log_step = 2.0) ? (lo = mid; u_ok .= v) : (hi = mid)
        end
        return (i = lo, u = u_ok, p = p_c, start_frac = f)
    end
    nothing
end

## ── concentration-controlled continuation ─────────────────────────────────────────────────
## Added 2026-08-23. THE REASON 44 OF 48 CELLS NEVER REACHED THE COLLAPSE CRITERION.
##
## solve_ilim_ec ramps the APPLIED CURRENT and solves for the concentration field. That
## parameterisation has a FOLD at the limiting current: dc_surf/di -> -infinity as i -> i_lim,
## so the Jacobian degenerates exactly where the answer is. Newton then fails, the ramp stops,
## and the value is reported as a lower bound. No mesh refinement can fix that -- it is a
## property of the parameterisation, not of the discretisation, which is why eleven mesh
## variants of the Hofmann cell all died in the same place.
##
## Through the fold, c_surf is monotone where i is not. So prescribe the reduced-mediator
## surface concentration and solve for i_app as an UNKNOWN. The system is bordered: the n
## transport residuals keep i_app as a parameter, and one added equation pins c_red(0).
## Walking c_target down to the 1e-3 collapse criterion then reaches that criterion directly,
## and the limiting current is read off rather than bounded.

"""Bordered Newton: solve F(u; i_app) = 0 together with c_red(0)/c_bulk = `frac`.

`u` is updated in place; the current is carried in/out through `iapp_ref` (a 1-element vector)
in log space so it cannot go negative. Returns true on convergence."""
function newton_ec_ccontrol!(u::Vector{Float64}, iapp_ref::Vector{Float64}, p::ECProblem,
                             frac::Float64; tol = 1e-9, max_iter = 120, max_step = 2.0)
    n = nvars(p)
    ired = findfirst(s -> s.s < 0, p.sp)
    ktgt = lidx(p, 1, ired)
    tgt = log(frac * p.sp[ired].c_bulk)
    v = vcat(u, log(iapp_ref[1]))                 # unknowns: [u; log i_app]
    R = zeros(n + 1); Rp = zeros(n + 1); J = zeros(n + 1, n + 1)
    Jb = zeros(n, n)
    Fw = zeros(n); uw = zeros(n)                  # residual_ec! is typed on Vector, not a view

    function resid!(Rv, vv)
        @inbounds for k in 1:n; uw[k] = vv[k]; end
        residual_ec!(Fw, uw, p, exp(vv[n+1]))
        @inbounds for k in 1:n; Rv[k] = Fw[k]; end
        Rv[n+1] = vv[ktgt] - tgt                  # the constraint that replaces the ramp
        Rv
    end

    resid!(R, v)
    for _ in 1:max_iter
        nrm = norm(R, Inf)
        if nrm < tol
            @inbounds for k in 1:n; u[k] = v[k]; end
            iapp_ref[1] = exp(v[n+1]); return true
        end
        ## Bordered Jacobian: the n x n transport block is analytic; the final column
        ## (d/d log i_app) and the constraint row are cheap enough to take numerically --
        ## one extra residual evaluation, not n+1.
        fill!(J, 0.0)
        @inbounds for k in 1:n; uw[k] = v[k]; end
        jacobian_ec!(Jb, uw, p, exp(v[n+1]))
        @inbounds for r in 1:n, cc in 1:n
            J[r, cc] = Jb[r, cc]
        end
        let h = 1e-7 * max(abs(v[n+1]), 1.0)
            vp = copy(v); vp[n+1] = v[n+1] + h
            resid!(Rp, vp)
            @inbounds for r in 1:(n+1)
                J[r, n+1] = (Rp[r] - R[r]) / h
            end
        end
        J[n+1, ktgt] = 1.0                     # d/du of (u[ktgt] - tgt)
        dv = try
            -(J \ R)
        catch
            -((J' * J + 1e-10I) \ (J' * R))
        end
        any(!isfinite, dv) && return false
        limit_step!(dv, v, p, max_step)
        lam = 1.0; vnew = similar(v)
        for _ in 1:12
            vnew .= v .+ lam .* dv
            resid!(Rp, vnew)
            (norm(Rp, Inf) < nrm || lam < 1e-3) && break
            lam /= 2
        end
        v .= vnew
        resid!(R, v)
    end
    ok = norm(R, Inf) < tol            # same rule as newton_ec! -- see the note there
    if ok
        @inbounds for k in 1:n; u[k] = v[k]; end
        iapp_ref[1] = exp(v[n+1])
    end
    ok
end

"""Limiting current by continuation in c_red(0)/c_bulk, reading it off the POLARISATION CURVE.

The current is not "found" at a threshold; it is read off a curve that must look like a
polarisation curve. Walking c_red(0) down from bulk, i rises and then **plateaus** at its
limiting value. Three things can end the walk and all three are the same physics:

  * `c_red(0)` reaches the collapse criterion -- the mediator is starved;
  * i PLATEAUS, |d ln i / d ln frac| falling below `plateau_tol` -- the limit is reached while
    the mediator is still present, because something else (substrate supply behind a detached
    front) is limiting. Measured on Br- oxidation: i flat at 108.32 with c_red/c_bulk stuck at
    2.3e-2 and the substrate at 1e-20 of bulk. The mediator there is ALSO the supporting anion,
    so migration into the anode resupplies it and it can never be starved -- terminating only on
    collapse reports a LOWER BOUND, and did, by 22% on that cell;
  * Newton stops converging as c_red(0) -> 0. That is not a solver failure to be worked around:
    the solution ceases to exist beyond the limiting current, so the last converged point IS the
    answer.

`i` DECREASING with further depletion would be a genuine turning point, which is not what a
polarisation curve of this kind should do; it is reported as SUSPECT rather than harvested.

The whole branch is returned so the curve can be inspected. **A polarisation curve should be
smooth** -- `branch_roughness` measures the worst jump in d ln i / d ln frac between consecutive
points, and a large value means numerical trouble, not physics.

Returns (i_lim, limiter, u, frac_reached, branch) with branch::Vector{Tuple{frac, i}}."""
function solve_ilim_ec_ccontrol(p::ECProblem; u0, i0::Float64, frac_end = 1e-3,
                                step0 = 0.12, step_min = 5e-4, plateau_tol = 2e-3)
    ired = findfirst(s -> s.s < 0, p.sp)
    u = copy(u0); iref = [i0]
    frac = min(exp(u0[lidx(p, 1, ired)]) / p.sp[ired].c_bulk, 0.98)
    i_best = i0; u_best = copy(u0); frac_best = frac
    branch = [(frac, i0)]
    step = step0; why = :ran_out; n_reject = 0
    while frac > frac_end
        f_try = max(frac * exp(-step), frac_end)
        u_try = copy(u); i_try = [iref[1]]
        if newton_ec_ccontrol!(u_try, i_try, p, f_try)
            dlni = log(i_try[1] / iref[1]); dlnf = log(f_try / frac)
            u .= u_try; iref[1] = i_try[1]; frac = f_try
            push!(branch, (frac, i_try[1]))
            if i_try[1] > i_best
                i_best = i_try[1]; u_best .= u; frac_best = frac
            elseif i_try[1] < i_best * (1 - 1e-4)
                ## i DECREASING WITH FURTHER DEPLETION IS NOT PHYSICAL. A polarisation curve of
                ## this kind rises and plateaus; it does not turn over. So this is the solver
                ## losing the branch -- landing on a different root, or taking a step the line
                ## search could not correct -- NOT a feature of the model. Do not record it and
                ## do not stop on it: back the step right down and try to stay on the branch.
                ## Only if that fails repeatedly is the cell genuinely unresolved, and then it
                ## is reported as such rather than having a turnover passed off as a limit.
                n_reject += 1
                step /= 4
                if step < step_min || n_reject > 12
                    why = :lost_branch; break
                end
                continue                       # retry the same frac with a smaller step
            end
            ## plateau: the current has stopped responding to further depletion
            if abs(dlnf) > 1e-12 && abs(dlni / dlnf) < plateau_tol && length(branch) > 4
                why = :plateau; break
            end
            step = min(step * 1.3, 2 * step0)
        else
            step /= 2
            if step < step_min
                why = :newton_limit      # the solution ceases to exist -- this IS i_lim
                break
            end
        end
    end
    frac <= frac_end * 1.0000001 && (why = :collapse)
    csub = exp(u_best[lidx(p, p.isub == 0 ? 1 : 1, p.isub)]) / p.sp[p.isub].c_bulk
    lim = why === :collapse    ? "collapse (c-control)" :
          why === :plateau     ? @sprintf("plateau (c-control; c_red/cb %.2e, c_sub/cb %.1e)",
                                          frac_best, csub) :
          why === :newton_limit ? @sprintf("limit reached, solution ceases (c-control; c_red/cb %.2e, c_sub/cb %.1e)",
                                           frac_best, csub) :
          why === :lost_branch ? @sprintf("UNRESOLVED: lost the solution branch at c_red/cb %.2e (i turned over, which is not physical -- the solver left the branch)", frac_best) :
                                 @sprintf("c-control ran out at c_red/cb = %.2e", frac_best)
    (i_best, lim, u_best, frac_best, branch)
end

"""Worst jump in d ln i / d ln frac between consecutive branch points.

A polarisation curve should be smooth. A large value here means the continuation is jumping
between solution families or the Newton solve is landing on different roots -- numerics, not
physics -- and the reported i_lim should not be trusted."""
function branch_roughness(branch)
    length(branch) < 4 && return 0.0
    sl = Float64[]
    for k in 2:length(branch)
        f0, i0 = branch[k-1]; f1, i1 = branch[k]
        df = log(f1 / f0)
        abs(df) > 1e-12 && push!(sl, log(i1 / i0) / df)
    end
    length(sl) < 3 && return 0.0
    maximum(abs(sl[k] - sl[k-1]) for k in 2:length(sl))
end

## ── delta-continuation ────────────────────────────────────────────────────────────────────
## Added 2026-08-23. One production cell of 48 -- Br-mediated Hofmann in an unstirred beaker,
## delta/x_k = 128 -- cannot be reached by ramping the current from a bulk initial guess. The
## ramp dies at 0.74 mA cm-2, BELOW that cell's own commuting bound of 6.95, so it is not a
## physical answer; the pipeline floored it to Tier-0 and the manuscript's unstirred counts
## were built on that floor. Eleven mesh and continuation variants all die the same way
## (probe_hofmann_unstirred.jl), so it is not a resolution problem: at this delta/x_k the
## solution branch simply is not connected to the bulk state by a current ramp.
##
## It IS reachable by continuation in delta. The same system at delta = 100 um solves normally;
## walking delta outward in small steps, regridding the converged state onto each new mesh,
## follows the branch all the way out (probe_hofmann_homotopy.jl).

## (2026-09-05: a byte-identical second copy of `regrid` and `solve_ilim_ec_continued` -- a paste
##  artefact; Julia silently took the later definition -- was removed here. One definition each, above.)


## (2026-09-06: a byte-identical second copy of the concentration-control section header and
##  `newton_ec_ccontrol!` -- the same paste artefact as the `regrid` pair above; Julia silently
##  took the later definition -- was removed here. One definition, above.)


## ---------------------------------------------------------------------------------------------
## LIMIT-TRACKING CONTINUATION IN k
## ---------------------------------------------------------------------------------------------
## solve_ilim_ec_kcont walks k up at a FIXED current -- the anchor, frac_i of the k = 0 limit --
## and reads the limit only once, at the very end. That is adequate while the EC-prime limit sits
## close to the k = 0 limit, because the anchor stays just below the fold the whole way. It fails
## whenever the source lifts the limit appreciably: the anchor is fixed while the fold moves up,
## so the state drifts further and further below it, and the single c-control at the end must
## climb the entire accumulated gap in one go. For Br- oxidation x unstirred the fold rises from
## 20.3 to 23.8 mA/cm2 while the anchor stays at 17.26, so that last walk has to cover 27% and
## dies on its first step -- handing back the anchor it started from, which is not an answer.
##
## This routine keeps the state ON the limit instead of below it. After each increase in k the
## current is pushed up until Newton stops converging, then stepped back to `back` of that value
## before k moves again: close enough to follow the fold, far enough off it that the next k-step
## has somewhere to converge to. The branch is therefore never abandoned and there is no gap to
## jump at the end. The k-step halves on failure and the final limit is read with a fine push
## followed by c-control.
##
## It needs the k = 0 STATE, not just the k = 0 current, which is why k0_floor returns both.
function _push_to_fold(p::ECProblem, u_in::Vector{Float64}, i_in::Float64; tol = 1.005)
    u = copy(u_in); i = i_in; step = 1.05
    while step > tol
        u_try = copy(u)
        if newton_ec!(u_try, p, i * step; max_iter = 200, max_log_step = 2.0)
            u = u_try; i *= step
        else
            step = 1.0 + (step - 1.0) / 2
        end
    end
    (i, u)
end

function solve_ilim_ec_ktrack(mkproblem, k_target::Float64, i_k0::Float64,
                              u_k0::Vector{Float64}; nk = 40, back = 0.90)
    k_target <= 0.0 && return nothing
    k_start = k_target / 1e7
    p0 = mkproblem(0.0)
    u = copy(u_k0); i_safe = back * i_k0
    ## step off the k = 0 fold before switching the source on
    newton_ec!(u, p0, i_safe; max_iter = 300, max_log_step = 2.0) || return nothing

    lk0, lk1 = log(k_start), log(k_target)
    t = 0.0; dt = 1.0 / nk; klast = 0.0
    while t < 1.0
        t_try = min(t + dt, 1.0)
        k_try = exp(lk0 + (lk1 - lk0) * t_try)
        p = mkproblem(k_try)
        u_try = copy(u)
        if newton_ec!(u_try, p, i_safe; max_iter = 300, max_log_step = 2.0)
            ilim_k, u_lim = _push_to_fold(p, u_try, i_safe)
            u_back = copy(u_lim); i_back = back * ilim_k
            if newton_ec!(u_back, p, i_back; max_iter = 300, max_log_step = 2.0)
                u = u_back; i_safe = i_back
            else
                u = u_try
            end
            t = t_try; klast = k_try
            dt = min(dt * 1.4, 2.0 / nk)
        else
            dt /= 2
            dt < 1e-5 && return nothing      # never reached k_target: not an answer
        end
    end
    ## the walk reached k_target; read the limit off the polarisation curve there
    pk = mkproblem(k_target)
    ifin, ufin = _push_to_fold(pk, u, i_safe; tol = 1.0002)
    rc = solve_ilim_ec_ccontrol(pk; u0 = ufin, i0 = ifin)
    ibest, lbest, ubest = (rc[1] > ifin) ?
        (rc[1], "k-tracked; " * rc[2], rc[3]) :
        (ifin, "k-tracked; fold located by current push", ufin)
    ## MONOTONICITY GUARD. In every one of the eight mediated systems the homogeneous source
    ## REGENERATES the electroactive reduced species (s < 0 always pairs with nu > 0) and consumes
    ## only its oxidised form and a non-electroactive substrate, so i_lim(k) >= i_lim(0) exactly.
    ## A tracked value below the k = 0 floor therefore reports a lost fold, not a limit:
    ## _push_to_fold stops where NEWTON stops, which is the fold only while the reaction layer
    ## stays resolved. Sweeping k far past the production value showed exactly that failure --
    ## the tracked limit climbed to 23.78 and then fell away monotonically, 21.39, 19.73, 18.66,
    ## 17.76, as x_k shrank below the mesh. Returning nothing lets the caller flag the cell rather
    ## than publish a number that its own no-source solve contradicts.
    ibest < i_k0 && return nothing
    (ibest, lbest, ubest)
end
