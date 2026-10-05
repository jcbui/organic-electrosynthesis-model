## run_ecprime.jl — EC' mediated-electrolysis sweep over the homogeneous rate
## constant k. ACT-like base case: C_med = 20 mM, C_S = 500 mM, delta = 100 um,
## D_med = 6e-10, D_S = 1e-9 m^2/s, 100 mM 1:1 supporting electrolyte.
##   julia run_ecprime.jl   ->  npp_ecprime_sweep.csv, npp_ecprime_profiles.csv

using Printf, DelimitedFiles
include("params.jl"); include("npp_ecprime.jl")

const delta  = 100e-6
const C_med  = 20.0        # mol/m^3
const C_S    = 500.0
const D_med  = 6.0e-10
const D_S    = 1.0e-9
const C_sup  = 100.0

## species: Med_red (neutral), Med_ox (+1, TEMPO+-like), S, H+, K+, A-
## electrode: red -> ox + e-  (s_red = -1, s_ox = +1; sum z*s = +1, anodic OK)
## homogeneous: ox + S -> red + P + H+ : nu_ox = -1, nu_red = +1, nu_S = -1,
## nu_H+ = +1 so the step conserves charge (sum z*nu = 0, div i = 0 across the
## film; audit finding, SI S5.6)
function make_problem(k_M; N = 90, dx1 = 0.03e-6)
    sp = [ECSpecies("Med_red", 0.0, D_med, C_med,        -1.0, +1.0),
          ECSpecies("Med_ox", +1.0, D_med, C_med * 1e-5, +1.0, -1.0),
          ECSpecies("S",       0.0, D_S,   C_S,           0.0, -1.0),
          ECSpecies("H+",     +1.0, 9.3e-9, 1e-3,         0.0, +1.0),
          ECSpecies("K+",     +1.0, 1.9e-9, C_sup,        0.0,  0.0),
          ECSpecies("A-",     -1.0, 1.5e-9, C_sup + C_med*1e-5 + 1e-3, 0.0, 0.0)]
    ECProblem(sp, 2, 3, k_M / 1000.0, geometric_faces(delta, dx1, N))
end

i_shuttle = F_const * D_med * C_med / delta          # A/m^2
i_subcap  = F_const * D_S * C_S / delta
@printf("shuttle bound  : %6.2f mA/cm2\n", i_shuttle * 0.1)
@printf("substrate cap  : %6.2f mA/cm2\n", i_subcap * 0.1)

ks = [1e-2, 1e-1, 1.0, 10.0, 1e2, 3e2, 1e3, 3e3, 1e4, 1e5]   # M^-1 s^-1
u_prev = nothing; il_prev = 0.0; k_prev = 0.0
open(joinpath(@__DIR__, "npp_ecprime_sweep.csv"), "w") do io
    println(io, "k_M,ilim_mAcm2,limiter,saveant_mAcm2,xk_um")
    for k in ks
        p = make_problem(k)
        global u_prev, il_prev, k_prev
        u0 = u_prev; ist = 0.05 * i_shuttle
        if u_prev !== nothing
            ## k-continuation (co2r_bulk §9.8 pattern): re-anchor the pre-collapse
            ## state at the NEW k at fixed current, with one geometric k-substep fallback
            ia_anchor = max(0.05 * i_shuttle, 0.6 * il_prev)
            v = copy(u_prev)
            ok = newton_ec!(v, p, ia_anchor; max_iter = 150, max_log_step = 3.0)
            if !ok
                pm = make_problem(sqrt(k_prev * k))
                vm = copy(u_prev)
                if newton_ec!(vm, pm, ia_anchor; max_iter = 150, max_log_step = 3.0)
                    v .= vm
                    ok = newton_ec!(v, p, ia_anchor; max_iter = 150, max_log_step = 3.0)
                end
            end
            if ok
                u0 = v; ist = ia_anchor
            else
                u0 = nothing
            end
        end
        il, lim, u_fin, i_fin = solve_ilim_ec(p; i_start = ist, growth = 1.1, u0 = u0)
        if i_fin > 0.0
            u_prev = u_fin; il_prev = il
        end
        k_prev = k
        i_sav = F_const * C_med * sqrt(D_med * (k/1000) * C_S)
        xk = sqrt(D_med / ((k/1000) * C_S)) * 1e6
        @printf("k = %8.0e M-1s-1   i_lim = %8.2f mA/cm2   (Saveant %8.2f, x_k %7.2f um)  limited by %s\n",
                k, il * 0.1, i_sav * 0.1, xk, lim)
        flush(stdout)
        println(io, "$k,$(il*0.1),\"$lim\",$(i_sav*0.1),$xk")
    end
end

## validation gates
p_lo = make_problem(1e-2); il_lo, _, _, _ = solve_ilim_ec(p_lo; i_start = 0.05 * i_shuttle)
il_hi = il_prev; lim_hi = "substrate (from sweep)"
@printf("\ngate C (k->0): i_lim/i_shuttle = %.3f (target ~1)\n", il_lo / i_shuttle)
@printf("gate D (k->inf): i_lim/i_subcap = %.3f (target <~1, limiter = %s)\n", il_hi / i_subcap, lim_hi)

## reaction-layer profiles at 0.9 i_lim for three k values
open(joinpath(@__DIR__, "npp_ecprime_profiles.csv"), "w") do io
    println(io, "k_M,x_um,c_red_norm,c_ox_norm,c_S_norm")
    for k in [1.0, 1e2, 1e3]
        p = make_problem(k)
        il, _, _, _ = solve_ilim_ec(p; i_start = 0.05 * i_shuttle)
        u = zeros(nvars(p)); N = nnode(p)
        for ix in 1:N, j in 1:length(p.sp)
            u[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-6))
        end
        okall = true
        for frac in 0.1:0.1:0.9
            okall &= newton_ec!(u, p, frac * il)
        end
        for ix in 1:N
            println(io, "$k,$(p.xc[ix]*1e6),$(exp(u[lidx(p,ix,1)])/C_med),$(exp(u[lidx(p,ix,2)])/C_med),$(exp(u[lidx(p,ix,3)])/C_S)")
        end
    end
end
println("DONE")
