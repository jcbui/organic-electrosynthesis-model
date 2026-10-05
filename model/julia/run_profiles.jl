## run_profiles.jl — concentration profiles that make the transport argument
## visible: (A) substrate depletion vs current in a stirred beaker, and
## (B) the same barrier current (50 mA/cm2) across reactor architectures.
## Base chemistry: 0.5 M neutral substrate, 1 e- oxidation to a cationic
## product, D_S = 1e-9 m^2/s, 0.1 M 1:1 supporting electrolyte.
##   julia run_profiles.jl -> profiles_direct.csv

using Printf, DelimitedFiles
include("params.jl"); include("npp.jl")
## 2026-09-05: the two convective profiles were solved at ROUND films (30 and 10 um) and labelled
## "flow cell" and "thin gap / RCE" -- while the model's flow archetype computed to a different
## film, so the panel disagreed with Fig. 2 on which reactor a film belongs to. Every film below
## is now the archetype value (fixed films) or the archetype MEDIAN over the fifty rows (rotating
## cylinder), the same statistic Fig. 2b plots (model_medians.delta_median), computed here from
## the same correlations and the same table, so the two figures cannot disagree again.
include("correlations.jl"); include("reactions_table.jl")
using Statistics
dmed(key) = median([delta_eff(key, r.D, r.nu) for r in RXNS])

const C_S  = 500.0        # mol/m^3
const D_S  = 1.0e-9
const C_sup = 100.0

## S -> P+ + e-  (s_S = -1, s_P = +1; sum z*s = +1, anodic)
function make_problem(delta; N = 80)
    sp = [Species("S",  0.0, D_S,    C_S,          -1.0),
          Species("P+", 1.0, 1.0e-9, C_S * 1e-5,   +1.0),
          Species("K+", 1.0, 1.9e-9, C_sup,         0.0),
          Species("A-",-1.0, 1.5e-9, C_sup + C_S*1e-5, 0.0)]
    FilmProblem(sp, delta, N)
end

function bulk_init(p)
    u = zeros(nvars(p))
    for ix in 1:p.N, j in 1:length(p.sp)
        u[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-8))
    end
    u
end

## ramp to target current with warm starts; return u (or nothing)
function ramp_to(p, i_target; nstep = 25)
    u = bulk_init(p)
    for f in range(1/nstep, 1.0; length = nstep)
        newton_solve!(u, p, f * i_target) || return nothing
    end
    u
end

open(joinpath(@__DIR__, "profiles_direct.csv"), "w") do io
    println(io, "case,delta_um,i_mAcm2,ilim_mAcm2,x_um,c_norm")

    ## ── A: stirred beaker (delta = 100 um), fan of currents ──────────────────
    delta = 200e-6
    p  = make_problem(delta)
    iF = i_fick(p, 1)
    @printf("stirred beaker: i_lim (Fick) = %.1f mA/cm2\n", iF * 0.1)
    for frac in (0.2, 0.5, 0.8, 0.95, 0.995)
        u = ramp_to(p, frac * iF)
        u === nothing && (println("  FAIL at frac $frac"); continue)
        dx = delta / p.N
        for ix in 1:p.N
            @printf(io, "fan,%.1f,%.3f,%.3f,%.4f,%.6f\n",
                    delta*1e6, frac*iF*0.1, iF*0.1, (ix-0.5)*dx*1e6,
                    exp(u[lidx(p, ix, 1)]) / C_S)
        end
        @printf("  i/ilim = %.3f  c_surf = %.4f\n", frac,
                exp(u[lidx(p, 1, 1)]) / C_S)
        flush(stdout)
    end

    ## ── B: the barrier current (50 mA/cm2) across reactors ───────────────────
    i_bar = 500.0          # A/m^2 = 50 mA/cm2
    ## the two batch films and the three flow films are the archetype constants (delta_eff
    ## ignores D, nu for them); the rotating-cylinder film is the archetype median of Fig. 2b
    for (case, delta) in [("unstirred", delta_eff(:natural, D_S, 1e-6)),
                          ("stirred",   delta_eff(:stirred, D_S, 1e-6)),
                          ("flow",      dmed(:flow)),
                          ("anec",      dmed(:anec)),
                          ("micro",     dmed(:micro)),
                          ("rce",       dmed(:rce))]
        p  = make_problem(delta)
        iF = i_fick(p, 1)
        i_run = min(i_bar, 0.995 * iF)      # infeasible reactors shown at their own i_lim
        u = ramp_to(p, i_run)
        u === nothing && (println("  FAIL $case"); continue)
        dx = delta / p.N
        for ix in 1:p.N
            @printf(io, "%s,%.1f,%.3f,%.3f,%.4f,%.6f\n",
                    case, delta*1e6, i_run*0.1, iF*0.1, (ix-0.5)*dx*1e6,
                    exp(u[lidx(p, ix, 1)]) / C_S)
        end
        @printf("%-10s delta = %5.0f um   i_lim = %6.1f mA/cm2   runs at %6.1f  c_surf = %.3f\n",
                case, delta*1e6, iF*0.1, i_run*0.1, exp(u[lidx(p, 1, 1)]) / C_S)
        flush(stdout)
    end
end
println("DONE")
