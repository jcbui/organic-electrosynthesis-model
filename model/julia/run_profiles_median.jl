## run_profiles_median.jl — ADDITIVE companion to run_profiles.jl.
##
## Why this exists (figure-provenance audit, finding 2): run_profiles.jl's base
## chemistry (C_S = 0.5 M, n_S = 1 e-, D_S = 1e-9 m^2/s) gives i_lim = 48.24
## mA/cm^2 in a stirred beaker, a near-coincidence with the 50 mA/cm^2 barrier
## that is a property of THAT exemplar, not of the corpus. This script re-runs
## the identical NPP film model at the 50-reaction corpus's own SUBSTRATE-row
## medians so the two can be plotted side by side and the exemplar's special
## status is visible on the figure.
##
## Medians over the 31 substrate rows of reactions_table.jl / reactions_50.csv:
##   C_S = 100 mol/m^3 (0.1 M)   n_S = 2 e-   D_S = 1.3944e-9 m^2/s
## Electron bookkeeping identical in form to run_profiles.jl (S -> P^z+ + n e-,
## s_j per electron, sum z_j s_j = +1 anodic): for n = 2, s_S = -1/2, and the
## product carries z = +2 with s = +1/2. Supporting electrolyte unchanged
## (0.1 M 1:1), so the only differences from the base case are C_S, n_S, D_S.
##
## Writes a NEW file, profiles_direct_median.csv. run_profiles.jl and
## profiles_direct.csv are untouched.
##   julia run_profiles_median.jl

using Printf
include("params.jl"); include("npp.jl")

const C_S   = 100.0        # mol/m^3  — substrate-row median C_carrier
const D_S   = 1.3944e-9    # m^2/s    — substrate-row median D
const N_S   = 2.0          # e-/molecule — substrate-row modal/median n_carrier
const C_sup = 100.0        # unchanged from run_profiles.jl

function make_problem(delta; N = 80)
    sS = -1.0 / N_S                       # substrate consumed per electron
    sP = +1.0 / N_S                       # product formed per electron, z = +N_S
    sp = [Species("S",   0.0,  D_S,   C_S,             sS),
          Species("P+",  N_S,  1.0e-9, C_S * 1e-5,     sP),
          Species("K+",  1.0,  1.9e-9, C_sup,          0.0),
          Species("A-", -1.0,  1.5e-9, C_sup + N_S * C_S * 1e-5, 0.0)]
    @assert isapprox(sum(s.z * s.s for s in sp), 1.0; atol = 1e-12)
    @assert abs(sum(s.z * s.c_bulk for s in sp)) < 1e-6 * maximum(s.c_bulk for s in sp)
    FilmProblem(sp, delta, N)
end

bulk_init(p) = begin
    u = zeros(nvars(p))
    for ix in 1:p.N, j in 1:length(p.sp)
        u[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-8))
    end
    u
end

function ramp_to(p, i_target; nstep = 25)
    u = bulk_init(p)
    for f in range(1/nstep, 1.0; length = nstep)
        newton_solve!(u, p, f * i_target) || return nothing
    end
    u
end

open(joinpath(@__DIR__, "profiles_direct_median.csv"), "w") do io
    println(io, "case,delta_um,i_mAcm2,ilim_mAcm2,x_um,c_norm")
    delta = 200e-6
    p  = make_problem(delta)
    iF = i_fick(p, 1)
    @printf("stirred beaker, MEDIAN substrate: i_lim (Fick) = %.3f mA/cm2\n", iF * 0.1)
    for frac in (0.2, 0.5, 0.8, 0.95, 0.995)
        u = ramp_to(p, frac * iF)
        u === nothing && (println("  FAIL at frac $frac"); continue)
        dx = delta / p.N
        for ix in 1:p.N
            @printf(io, "fan_median,%.1f,%.3f,%.3f,%.4f,%.6f\n",
                    delta*1e6, frac*iF*0.1, iF*0.1, (ix-0.5)*dx*1e6,
                    exp(u[lidx(p, ix, 1)]) / C_S)
        end
        @printf("  i/ilim = %.3f  c_surf = %.4f\n", frac, exp(u[lidx(p, 1, 1)]) / C_S)
        flush(stdout)
    end
end
println("DONE")
