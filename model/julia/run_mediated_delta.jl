## run_mediated_delta.jl (2026-09-11) -- three of the eight mediated rows, one per EC' regime, solved at their
## cited rate constants across the same seventeen films the Fig. 6 sweeps use (the seven archetype medians and
## log-spaced fill), for Fig. 6g (author: "I LOVE how h corresponds to 3 different chemistries, can we do that for
## the mediated g?"). The MedSpec struct and the three row specifications are COPIED VERBATIM from run_mediated.jl
## (the same page-verified conditions, the same species lists, the same k); the accept sequence -- direct ramp,
## then concentration control, accepted when a plateau or collapse is reached above the row's own k = 0 floor --
## is the one run_mediated.jl applies to every published cell. Writes mediated_ec_delta.csv beside itself.
##   cd julia && nohup julia run_mediated_delta.jl > /abs/path/log 2>&1 &
using Printf
include("params.jl"); include("correlations.jl"); include("npp_ecprime.jl"); include("reactions_table.jl")

struct MedSpec
    label::String
    k_M::Float64            # M^-1 s^-1 (estimate; SI Table S6)
    nu_solv::Float64        # kinematic viscosity m^2/s
    D_red::Float64          # for delta correlations (carrier)
    n_c::Float64            # electrons per mediator molecule
    n_S::Float64            # electrons per substrate molecule
    C_med::Float64          # mol/m^3
    C_S::Float64
    D_S::Float64
    species::Vector{ECSpecies}
end

S(args...) = ECSpecies(args...)
tr(C) = C * 1e-5     # trace bulk value for the electrogenerated form

SPECS = MedSpec[
 MedSpec("ACT-mediated alcohol oxidation (flow, hectogram)", 20., 8.93e-7, 5.93e-10, 1, 2, 25., 500., 7.2207e-10,
   ## Zhong/Stahl OPRD 2021 200-g campaign: 0.5 M alcohol, ACT 25 mM (5 mol%),
   ## purely aqueous 1 M NaHCO3 / 1 M Na2CO3 pH 8.5 -- released H+ is buffered
   [S("ACT",  0.0, 5.93e-10, 25.,    -1.0, +1.0),
    S("ACT+",+1.0, 5.93e-10, tr(25.),+1.0, -1.0),
    S("Sub",  0.0, 7.2207e-10, 500.,    0.0, -0.5),      # 2 ox per alcohol
    S("Na+", +1.0, 1.33e-9, 3000.,    0.0,  0.0),
    S("CO3--",-2.0, 0.92e-9, 1000.,   0.0, -1.0),      # buffer absorbs the proton:
    S("HCO3-",-1.0, 1.18e-9, 1000. + tr(25.), 0.0, +1.0)]),
 MedSpec("NHPI-mediated allylic C-H -> enone", 0.5, 3.90e-7, 2.09e-9, 1, 4, 33., 167., 1.9448e-09,
   ## Horn/Baran Nature 2016: Cl4NHPI 33 mM (20 mol%), substrate 167 mM,
   ## ACETONE, LiClO4 0.1 M, pyridine base takes the anodic proton
   [S("NHPI", 0.0, 2.09e-9, 33.,    -1.0, +1.0),
    S("PINO", 0.0, 2.09e-9, tr(33.),+1.0, -1.0),
    S("H+",  +1.0, 3.0e-9, 1e-3,    +1.0,  0.0),       # deprotonation carries charge
    S("Sub",  0.0, 1.9448e-09, 167.,    0.0, -0.25),      # 4 e- per allylic/benzylic C=O
    S("Li+", +1.0, 1.0e-9, 100.,     0.0,  0.0),
    S("ClO4-",-1.0, 1.7e-9, 100. + 1e-3, 0.0, 0.0)]),
 MedSpec("Br-mediated Hofmann rearrangement", 1e3, 4.755e-7, 2.7e-9, 1, 2, 80., 400., 1.8611e-09,
   ## Malviya/Cantillo OPRD 2023 scale-up: 0.4 M amide, NaBr 0.08 M in MeCN
   ## (MeOH 10 equiv = reagent, no alkoxide base). RC(O)NH2 + Br2 + MeOH ->
   ## carbamate + 2 H+ + 2 Br-: sum z_j*nu_j = 0 (charge-conserving)
   [S("Br-",  -1.0, 2.7e-9, 80.001,  -1.0, +2.0),      # 2 Br- returned per Br2
    S("Br2",   0.0, 2.2e-9, tr(80.), +0.5, -1.0),
    S("Sub",   0.0, 1.8611e-09, 400.,    0.0, -1.0),      # phenylacetamide, 2 e-, 1 Br2/S
    S("H+",   +1.0, 3.0e-9, 1e-3,     0.0, +2.0),      # HBr released; sum z*nu = 0
    S("Na+",  +1.0, 1.33e-9, 80.,     0.0,  0.0)]),
]
const DELTAS_UM = [260, 228, 200, 176.598, 119.95, 106.9, 81.473, 55.338, 37.587, 36.2, 25.53, 17.341, 12.624, 12.5, 11.778, 10.992, 8]

open(joinpath(@__DIR__, "mediated_ec_delta.csv"), "w") do io
    println(io, "reaction,k_M,delta_um,xk_um,i_tier0_mAcm2,i_k0_mAcm2,i_subcap_mAcm2,i_ec_mAcm2,limiter,path,flag")
    for spec in SPECS
        km = spec.k_M / 1000.0
        xk = sqrt(spec.species[2].D / (km * spec.C_S))
        isb = findfirst(s -> s.name == "Sub", spec.species)
        @printf("=== %s  (k = %g M-1s-1, x_k = %.1f um)\n", spec.label, spec.k_M, xk*1e6); flush(stdout)
        mkprob = (dd, kk) -> ECProblem(spec.species, 2, isb, kk, geometric_faces(dd, clamp(xk / 50, 0.02e-6, 0.9 * dd / 90), 90))
        for dum in DELTAS_UM
            d = dum * 1e-6
            i_t0  = F_const * spec.D_red * spec.C_med / (abs(spec.species[1].s) * d)
            i_cap = spec.n_S * F_const * spec.D_S * spec.C_S / d
            ## the k = 0 floor of the identical species set (as run_mediated.jl computes it)
            p0 = mkprob(d, 0.0)
            i0, lim0, u0s, i0s = solve_ilim_ec(p0; i_start = 0.02 * i_t0, growth = 1.15)
            if i0s > 0.0
                ic0, limc0, uc0, _, _ = solve_ilim_ec_ccontrol(p0; u0 = u0s, i0 = i0s)
                if (startswith(limc0, "collapse") || startswith(limc0, "plateau") || startswith(limc0, "limit reached")) && ic0 > i0
                    i0 = ic0
                end
            end
            floor_i = max(0.9 * i_t0, i0)
            p = mkprob(d, km)
            il, lim, u_safe, i_safe = solve_ilim_ec(p; i_start = 0.02 * i_t0, growth = 1.15)
            path = "direct-ramp"
            if i_safe > 0.0
                ic, limc, uc, _, _ = solve_ilim_ec_ccontrol(p; u0 = u_safe, i0 = i_safe)
                if (startswith(limc, "collapse") || startswith(limc, "plateau") || startswith(limc, "limit reached")) && ic > il
                    il, lim, path = ic, limc, "c-control"
                else
                    lim = lim * "; " * limc
                end
            end
            reached = occursin("plateau", lim) || occursin("collapse", lim) || occursin("limit reached", lim)
            flag = (il < floor_i) ? "below-floor" : (reached ? "ok" : "no-plateau")
            @printf("  delta %8.3f um  i_t0 %8.2f  i_k0 %8.2f  cap %9.2f  i_ec %9.2f  x%.2f  [%s | %s | %s]\n",
                    dum, i_t0*0.1, i0*0.1, i_cap*0.1, il*0.1, il/i0, flag, path, lim); flush(stdout)
            println(io, string("\"", spec.label, "\",", spec.k_M, ",", dum, ",", xk*1e6, ",", i_t0*0.1, ",", i0*0.1, ",", i_cap*0.1, ",", il*0.1, ",\"", lim, "\",\"", path, "\",\"", flag, "\""))
            flush(io)
        end
    end
end
println("MEDIATED DELTA DONE")
