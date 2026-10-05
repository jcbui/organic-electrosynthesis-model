## npp.jl — Tier-1: 1D steady Nernst–Planck + electroneutrality across the
## diffusion film, galvanostatic, DILUTE-SOLUTION THEORY -- J. Newman & K. E. Thomas-Alyea,
## "Electrochemical Systems", 3rd edn, Wiley, Hoboken NJ, 2004, Ch. 11. Concentrated-solution
## theory (Stefan-Maxwell, Ch. 12 of the same book) is NOT used: the Onsager coefficients it
## needs do not exist in the literature for these fifty organic electrolyte compositions.
## What that costs is bounded in SI S1.1 from this project's own measured isotherms.
##
## Numerics transplanted from co2r_bulk: finite-volume flux balances,
## LOG-CONCENTRATION DOFs (positivity by construction), damped Newton with a
## dense forward-difference Jacobian and log-step clamp, and natural
## continuation (warm starts) in the applied current density.
##
## Unknowns per node ix (N nodes):  u[(ix-1)*(ns+1) + j] = ln c_j,  j = 1..ns
##                                  u[(ix-1)*(ns+1) + ns+1] = phi [V]
## Residuals per node: ns species FV balances (source-free film) + electroneutrality.
##
## Boundary conditions:
##   x = 0 (electrode):  N_j(0) = s_j * i_app / F        (s_j: e-normalized stoich)
##                        charge consistency requires  sum_j z_j s_j = 1 (anodic)
##   x = delta (bulk):    c_j = c_bulk_j (Dirichlet ghost),  phi = 0

using LinearAlgebra
using Printf

struct Species
    name::String
    z::Float64
    D::Float64        # m^2/s
    c_bulk::Float64   # mol/m^3
    s::Float64        # N_j(0) = s_j * i/F  (0 for inert)
end

struct FilmProblem
    sp::Vector{Species}
    delta::Float64
    N::Int
end

nvars(p::FilmProblem) = (length(p.sp) + 1) * p.N
lidx(p, ix, j) = (ix - 1) * (length(p.sp) + 1) + j          # ln c_j at node ix
pidx(p, ix)   = (ix - 1) * (length(p.sp) + 1) + length(p.sp) + 1   # phi at node ix

## NP flux on the face between (cL,phiL) and (cR,phiR), spacing dx:
##   N = -D (cR-cL)/dx - z (F/RT) D cbar (phiR-phiL)/dx
np_flux(D, z, cL, cR, phiL, phiR, dx) =
    -D * (cR - cL) / dx - z * D / RT_F * 0.5 * (cL + cR) * (phiR - phiL) / dx

function residual!(Fv::Vector{Float64}, u::Vector{Float64}, p::FilmProblem, i_app::Float64)
    ns = length(p.sp); N = p.N; dx = p.delta / N
    # unpack (clamped exp, co2r_bulk convention)
    ## FLOOR AT -300, NOT -50. exp(-50) is 2e-22 of unit concentration and a depleted species
    ## reaches it easily; where the clamp binds, dc/du is zeroed and the Jacobian column with it,
    ## which is how a Newton step silently stops seeing that species. Same fix as npp_ecprime.jl
    ## (2026-08-23); -300 is still far above the 1e-308 underflow and no longer binds.
    c   = [exp(clamp(u[lidx(p, ix, j)], -300.0, 50.0)) for j in 1:ns, ix in 1:N]
    phi = [u[pidx(p, ix)] for ix in 1:N]
    # residual scales for O(1) rows
    ## RESIDUAL SCALE (2026-09-06): per species, D * max(c_bulk, 0.01 c_max_bulk, max_x c) / delta --
    ## the rule npp_ecprime.jl adopted on 2026-09-05 and the registry row "Residual scale c_ref
    ## (per species)" publishes, so both stages of the film model use ONE rule and SI S5.2 describes
    ## both. The retired form scaled each species by its BULK value with an absolute 1 mol/m3 floor,
    ## so a species that is a trace in the bulk and large at the electrode had its residual measured
    ## against a flux far smaller than its own. Benign here (uniform mesh; all 300 cells and the
    ## closed-form audits converged either way) but the same defect class, and the last-digit effect
    ## on the published layer is measured by re-solving it, not assumed.
    cscale = maximum(s.c_bulk for s in p.sp)
    rscale = [p.sp[j].D * max(p.sp[j].c_bulk, 0.01 * cscale, maximum(@view c[j, :])) / p.delta for j in 1:ns]
    for ix in 1:N
        for j in 1:ns
            spj = p.sp[j]
            # left face
            Jl = ix == 1 ? spj.s * i_app / F_const :
                 np_flux(spj.D, spj.z, c[j, ix-1], c[j, ix], phi[ix-1], phi[ix], dx)
            # right face (bulk ghost at half-spacing)
            Jr = ix == N ? np_flux(spj.D, spj.z, c[j, ix], spj.c_bulk, phi[ix], 0.0, dx/2) :
                 np_flux(spj.D, spj.z, c[j, ix], c[j, ix+1], phi[ix], phi[ix+1], dx)
            Fv[lidx(p, ix, j)] = (Jl - Jr) / rscale[j]
        end
        Fv[pidx(p, ix)] = sum(p.sp[j].z * c[j, ix] for j in 1:ns) / cscale
    end
    return Fv
end

## ── damped Newton, dense FD Jacobian, log-step clamp (co2r_bulk §9.3/§9.5) ────
function newton_solve!(u::Vector{Float64}, p::FilmProblem, i_app::Float64;
                       tol = 1e-9, max_iter = 60, max_log_step = 2.0, verbose = false)
    n = nvars(p)
    Fv = zeros(n); Fp = zeros(n); J = zeros(n, n)
    residual!(Fv, u, p, i_app)
    for it in 1:max_iter
        nrm = norm(Fv, Inf)
        verbose && @printf("      it %2d  ||F||=%.3e\n", it, nrm)
        nrm < tol && return true
        # dense forward-difference Jacobian
        up = copy(u)
        for k in 1:n
            h = 1e-7 * max(abs(u[k]), 1.0)
            up[k] = u[k] + h
            residual!(Fp, up, p, i_app)
            @inbounds for r in 1:n
                J[r, k] = (Fp[r] - Fv[r]) / h
            end
            up[k] = u[k]
        end
        du = try
            -(J \ Fv)
        catch
            -((J' * J + 1e-10I) \ (J' * Fv))     # LM fallback on singular J
        end
        any(!isfinite, du) && return false
        # clamp log-concentration steps (nullspace-amplification guard)
        mx = maximum(abs.(du))
        mx > max_log_step && (du .*= max_log_step / mx)
        # backtracking line search on ||F||
        lam = 1.0; unew = similar(u)
        for _ in 1:12
            unew .= u .+ lam .* du
            residual!(Fp, unew, p, i_app)
            if norm(Fp, Inf) < nrm || lam < 1e-3
                break
            end
            lam /= 2
        end
        u .= unew
        residual!(Fv, u, p, i_app)
    end
    ## ENFORCE THE DECLARED TOLERANCE. This read `norm(Fv, Inf) < 1e-6` -- 1000x looser than the
    ## `tol = 1e-9` in this function's own signature -- so a solve that exhausted max_iter without
    ## reaching the declared tolerance was still reported as converged. The identical defect was
    ## found and fixed in npp_ecprime.jl on 2026-08-23; npp.jl is its twin and was missed, and it
    ## is what audit gates G1-G4 (the migration-physics validations) actually run on.
    return norm(Fv, Inf) < tol
end

## Fickian reference for the reacting species (index jr): |s_jr| i/F = D C/delta
i_fick(p::FilmProblem, jr::Int) =
    p.sp[jr].D * p.sp[jr].c_bulk / p.delta * F_const / abs(p.sp[jr].s)

"""
solve_ilim(p; jr) — galvanostatic continuation with warm starts. Ramps i_app
until the surface concentration of the reacting species jr collapses
(c_surf/c_bulk < 1e-3) or Newton fails; returns (i_lim, curve) with curve
rows (i_app, c_surf/c_bulk, dphi_film).
"""
function solve_ilim(p::FilmProblem; jr::Int = 1, imax_over_fick = 2.6, di = 0.02)
    iF = i_fick(p, jr)
    u = zeros(nvars(p))
    for ix in 1:p.N, j in 1:length(p.sp)
        u[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-8))
    end
    curve = Vector{NTuple{3,Float64}}()
    i_last_ok = 0.0
    frac = di
    while frac <= imax_over_fick
        ia = frac * iF
        ok = newton_solve!(u, p, ia)
        if !ok
            break
        end
        csurf = exp(u[lidx(p, 1, jr)]) / p.sp[jr].c_bulk
        dphi  = u[pidx(p, 1)]
        push!(curve, (ia, csurf, dphi))
        i_last_ok = ia
        csurf < 1e-3 && break
        frac += di
    end
    return i_last_ok, curve
end
