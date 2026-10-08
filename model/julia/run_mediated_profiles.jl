## run_mediated_profiles.jl (2026-09-11) -- Fig. 6d-f: the three mediated rows of Fig. 6g (ACT alcohol oxidation, NHPI allylic
## C-H oxidation, bromide-mediated bromination of anisole; the Hofmann row it replaced on 2026-10-06 rests on a declared
## k whose substrate-limited label flips inside its own band) solved at their cited rate constants on ONE measured film, the ANEC
## cell's 36.2 um (Watkins et al. 2023, the archetype film every row's ANEC cell of Table S5 uses), with the concentration
## profiles AT the limiting current (the c-control plateau). Author, 2026-09-11: "maybe we should show these profiles then for
## d-f bc they're really applicable?" -- the panels had drawn a declared base case (20 mM / 0.5 M, k = 1e5 / 1e2 / 1e-2).
##
## The MedSpec struct and the three row specifications are COPIED VERBATIM from run_mediated.jl (the same page-verified
## conditions, species lists and k), and the accept sequence -- direct ramp, then concentration control, accepted when a
## plateau or collapse is reached at or above the row's own floor -- is the one run_mediated.jl applies to every published
## cell. The drawn profile and the printed i_lim are the PRODUCTION solve (N = 90, dx1 = x_k/50 clamped, exactly
## run_mediated.jl's mesh), so what the panel shows IS the published ANEC cell of Table S5 (the control, asserted by
## data/check_ms_derived.py); a FINE mesh (N = 150, dx1 = 0.01 um, the mesh the retired base-case panels were drawn on) is
## solved beside it as a mesh check and its i_lim written in the ilim_fine_mAcm2 column (0.05-0.85 % apart on the three rows).
##
## The regime of each row is NAMED FROM THE SOLVE, not from the analytic inequalities: substrate-limited when the substrate
## is exhausted at the wall (c_S(0)/c_S,bulk < 0.05); otherwise by the share of the activated mediator consumed inside the
## film (the area of k c_ox c_S x/(i/F) against ln x): mediator-limited below one third, kinetic above two thirds, mixed
## control between (x_k from the ACTIVATED form's D, gamma = i_cap/i_shuttle from the RESTING form's, as Eqs. S12-S15 define
## them; the Hofmann row's Br2 and Br- differ); the share is normalised by the electrode's flux of the ACTIVATED form, s_ox i/F, so one Br2 counts for the two
## electrons that make it. The analytic assignment (x_k against delta and gamma x_k, gamma = i_subcap / i_t0) is written beside it so
## data/ecprime_panel_sensitivity.py (G-ECPANEL) can compare the two. The same gate needs the labels' sensitivity to the two
## diffusivities, so every row is ALSO solved with D_med and D_S each scaled by 0.75 and 1.25 (the +/-25 % working property
## error of S3.1), on the production mesh, and the solved label is written for each perturbation.
##
##   cd julia && nohup julia run_mediated_profiles.jl > /abs/path/log 2>&1 &
##   -> mediated_ec_profiles.csv (one row per node) and mediated_ec_profiles_dsens.csv (one row per perturbation)
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
 MedSpec("ACT-mediated alcohol oxidation (flow, hectogram)", 20., 8.93e-7, 5.93e-10, 1, 4, 25., 500., 7.2207e-10,
   ## Zhong/Stahl OPRD 2021 200-g campaign: 0.5 M alcohol, ACT 25 mM (5 mol%),
   ## purely aqueous 1 M NaHCO3 / 1 M Na2CO3 pH 8.5 -- released H+ is buffered
   [S("ACT",  0.0, 5.93e-10, 25.,    -1.0, +1.0),
    S("ACT+",+1.0, 5.93e-10, tr(25.),+1.0, -1.0),
    S("Sub",  0.0, 7.2207e-10, 500.,    0.0, -0.25),     # 4 ox per alcohol (to the carboxylic acid)
    S("Na+", +1.0, 1.33e-9, 3000.,    0.0,  0.0),
    S("CO3--",-2.0, 0.92e-9, 1000.,   0.0, -1.0),      # buffer absorbs the proton:
    S("HCO3-",-1.0, 1.18e-9, 1000. + tr(25.), 0.0, +1.0)]),
 MedSpec("NHPI-mediated allylic C-H -> enone", 20.2, 3.90e-7, 2.09e-9, 1, 2, 33., 167., 1.8660e-09,
   ## Horn/Baran Nature 2016: Cl4NHPI 33 mM (20 mol%), substrate 167 mM,
   ## k = 20.2 M-1 s-1 (2026-10-05): electrogenerated PINO + cyclohexene in MeCN with pyridine, Ueda, Noyama,
   ## Ohmori & Masui, Chem. Pharm. Bull. 1987, 35, 1372, Table II p. 1375 (allylic substrates 12.8-77.6). It was
   ## 0.5, the order of PINO + substituted TOLUENES in acetic acid (Koshino 2003) -- a benzylic value in another
   ## solvent, carried for an ALLYLIC oxidation whose own exemplar cites the Masui study as its kinetic reference.
   ## ACETONE, LiClO4 0.1 M, pyridine base takes the anodic proton
   ## the N-oxide ANION at the anode (Horn p. 81; carrier_charge.csv z = -1), pyridinium as its counter-cation
   [S("NHPI", -1.0, 2.09e-9, 33.,    -1.0, +1.0),
    S("PINO", 0.0, 2.09e-9, tr(33.),+1.0, -1.0),
    S("H+",  +1.0, 3.0e-9, 33.,      0.0, +1.0),       # pyridinium; sum z*nu = -1 + 1 = 0
    S("Sub",  0.0, 1.8660e-09, 167.,    0.0, -0.5),       # 2 anodic e- per enone (tBuOOH supplies the rest)
    S("Li+", +1.0, 1.0e-9, 100.,     0.0,  0.0),
    S("ClO4-",-1.0, 1.7e-9, 100.,    0.0,  0.0)]),
 MedSpec("Br- oxidation / electrophilic bromination", 2.28e4, 9.227e-7, 2.08e-9, 1, 2, 250., 33.3, 9.7945e-10,
   ## k = 2.28e4 M-1 s-1 (2026-10-05): Br2 + ANISOLE, this row's own carrier and substrate, measured in water at
   ## 20 C: (2.23 +/- 0.14)e4 para + (5.4 +/- 0.6)e2 ortho, Sivey, Bickley & Victor, Environ. Sci. Technol. 2015,
   ## 49, 4937, Table 1 p. 4941. It was a declared 1e3 ("conservative low end") while the measurement sat in a
   ## source the row already cited. The row is transport-limited: no cell moves by more than 0.4 %.
   ## Zhang/Su Nat Commun 2025, the campaign run on ANISOLE (2026-10-06): the divided H-cell of Methods and Fig 4,
   ## "each cell was filled with 7.5 mL acetonitrile and 7.5 mL 0.5 mol/L NaBr aqueous solution. 0.5 mmol
   ## substrate was dissolved in the anodic cell": anisole 0.5/15 = 33.3 mM, Br- 0.5 x 7.5/15 = 250 mM, water/MeCN
   ## 1:1. The flow runs of Fig 5b/c (10:10:10:3 medium, 518 g) are on drug and natural-product derivatives.
   [S("Br-", -1.0, 2.08e-9, 250.001, -1.0, +1.0),      # 1 Br- returned (1 Br into product)
    S("Br2",  0.0, 1.2e-9,  tr(250.),+0.5, -1.0),
    S("Sub",  0.0, 9.7945e-10, 33.3,    0.0, -1.0),
    S("H+",  +1.0, 5.0e-9,  1e-3,     0.0, +1.0),      # ArH + Br2 -> ArBr + Br- + H+; sum z*nu = 0
    S("Na+", +1.0, 1.33e-9, 250.,     0.0,  0.0)]),
]
const DELTA_UM = 36.2                      # the ANEC archetype film, measured (Watkins 2023, SI Table S1); Table S5's ANEC column
const SHORT = Dict("ACT-mediated alcohol oxidation (flow, hectogram)" => "ACT",
                   "NHPI-mediated allylic C-H -> enone" => "NHPI",
                   "Br- oxidation / electrophilic bromination" => "Bromination")
const BAND = 0.25

reached(l) = startswith(l, "collapse") || startswith(l, "plateau") || startswith(l, "limit reached")

"""Scale D_med (species 1 and 2, the resting and activated mediator) and D_S (the substrate) of a spec's species list."""
function scaled_species(spec, fmed, fsub)
    isb = findfirst(s -> s.name == "Sub", spec.species)
    [ECSpecies(s.name, s.z, s.D * (j <= 2 ? fmed : (j == isb ? fsub : 1.0)), s.c_bulk, s.s, s.nu)
     for (j, s) in enumerate(spec.species)]
end

"""Solve one row on one film with run_mediated.jl's accept sequence. Returns the problem, i_lim (A/m^2), limiter, path and the
state AT the accepted current (the c-control plateau), or nothing when only the ramp converged."""
function solve_row(sp, isb, km, d, xk_mesh, floor_i; fine::Bool)
    faces = fine ? geometric_faces(d, 0.01e-6, 150) : geometric_faces(d, clamp(xk_mesh / 50, 0.02e-6, 0.9 * d / 90), 90)
    p = ECProblem(sp, 2, isb, km, faces)
    i_t0 = F_const * sp[1].D * sp[1].c_bulk / (abs(sp[1].s) * d)
    il, lim, u_safe, i_safe = solve_ilim_ec(p; i_start = 0.02 * i_t0, growth = 1.15)
    path = "direct-ramp"; u_at = nothing
    if i_safe > 0.0
        ic, limc, uc, _, _ = solve_ilim_ec_ccontrol(p; u0 = u_safe, i0 = i_safe)
        if reached(limc) && ic >= floor_i
            il, lim, path, u_at = ic, limc, "c-control", copy(uc)
        else
            lim = lim * "; " * limc
        end
    end
    return p, il, lim, path, u_at
end

"""The share of the activated mediator consumed inside the film: the area of rho = k c_ox c_S x/(s_ox i/F) against ln x, where
s_ox i/F is the electrode's flux of the activated form (s_ox = 1 for ACT+ and PINO, 0.5 for Br2), as Fig. 6d-f and ms_phrases.py
compute it, plus the wall values that name the regime."""
function profile_stats(p, u, il, km)
    N = nnode(p); ired = 1; iox = p.iox; isb = p.isub
    x = p.xc; cox = [exp(u[lidx(p, ix, iox)]) for ix in 1:N]; cs = [exp(u[lidx(p, ix, isb)]) for ix in 1:N]
    rho = km .* cox .* cs .* x ./ (abs(p.sp[iox].s) * il / F_const)
    share = 0.0
    for ix in 2:N
        share += 0.5 * (rho[ix] + rho[ix-1]) * (log(x[ix]) - log(x[ix-1]))
    end
    c_red_surf = exp(u[lidx(p, 1, ired)]) / p.sp[ired].c_bulk
    c_S_surf = cs[1] / p.sp[isb].c_bulk
    return share, c_red_surf, c_S_surf
end

## THREE labels along the kinetic axis since 2026-10-05, not two. With the NHPI row at the rate constant measured for PINO and
## an allylic C-H (20.2 M-1 s-1) its reaction layer is about the film (x_k 25 um on 36 um) and 54 % of the activated mediator
## reacts inside it: a two-way split at one half named it "kinetic", and a +25 % change in D_med (47 %) renamed it. A row
## that sits at the boundary is named for where it sits. For a first-order step with the substrate in excess the share is
## 1 - 1/cosh(delta/x_k), so one third and two thirds are delta/x_k = acosh(3/2) and acosh(3).
const SHARE_LO, SHARE_HI = 1/3, 2/3
const DXK_LO, DXK_HI = acosh(1 / (1 - SHARE_LO)), acosh(1 / (1 - SHARE_HI))
regime_solved(c_S_surf, share) = c_S_surf < 0.05 ? "substrate-limited" :
    (share < SHARE_LO ? "mediator-limited" : (share > SHARE_HI ? "kinetic" : "mixed"))
regime_analytic(d, xk, gamma) = d < DXK_LO * xk ? "mediator-limited" :
    (d > gamma * xk ? "substrate-limited" : (d > DXK_HI * xk ? "kinetic" : "mixed"))

d = DELTA_UM * 1e-6
open(joinpath(@__DIR__, "mediated_ec_profiles_dsens.csv"), "w") do ios
println(ios, "reaction,short,var,factor,k_M,delta_um,xk_um,gamma,ilim_mAcm2,limiter,path,c_red_surf_norm,c_S_surf_norm,share_in_film,regime_solved,regime_analytic")
open(joinpath(@__DIR__, "mediated_ec_profiles.csv"), "w") do io
    println(io, "reaction,short,k_M,delta_um,xk_um,gamma,gamma_xk_um,C_med_molm3,C_S_molm3,D_red,D_ox,D_S,n_S,s_red,s_ox,i_tier0_mAcm2,i_k0_mAcm2,i_subcap_mAcm2,ilim_mAcm2,ilim_fine_mAcm2,limiter,path,i_profile_mAcm2,c_red_surf_norm,c_S_surf_norm,share_in_film,regime_solved,regime_analytic,x_um,c_red_norm,c_ox_norm,c_S_norm")
    for spec in SPECS
        km = spec.k_M / 1000.0
        isb = findfirst(s -> s.name == "Sub", spec.species)
        xk = sqrt(spec.species[2].D / (km * spec.C_S))
        s_red = abs(spec.species[1].s); s_ox = abs(spec.species[2].s)
        i_t0 = F_const * spec.D_red * spec.C_med / (s_red * d)
        i_cap = spec.n_S * F_const * spec.D_S * spec.C_S / d
        gamma = i_cap / i_t0
        @printf("=== %s  (k = %g M-1s-1, x_k = %.2f um, gamma = %.2f, gamma x_k = %.1f um, delta = %.1f um)\n",
                spec.label, spec.k_M, xk*1e6, gamma, gamma*xk*1e6, DELTA_UM); flush(stdout)
        ## the k = 0 floor of the identical species set, production mesh (as run_mediated.jl computes it)
        p0, i0, lim0, path0, _ = solve_row(spec.species, isb, 0.0, d, xk, 0.0; fine = false)
        floor_i = max(0.9 * i_t0, i0)
        ## production mesh: the drawn profile AND the control against the published ANEC cell
        p, il, lim, path, u_at = solve_row(spec.species, isb, km, d, xk, floor_i; fine = false)
        if u_at === nothing
            error("$(spec.label): the production solve did not reach a c-control plateau ($lim); a profile at i_lim needs one")
        end
        ## fine mesh: the mesh check
        pf, ilf, limf, pathf, _ = solve_row(spec.species, isb, km, d, xk, floor_i; fine = true)
        share, c_red_s, c_S_s = profile_stats(p, u_at, il, km)
        rs, ra = regime_solved(c_S_s, share), regime_analytic(d, xk, gamma)
        @printf("  floor %8.3f  production %9.3f [%s | %s]  fine-mesh check %9.3f [%s | %s]  (%.3f %% apart)  share %.3f  c_red(0) %.2e  c_S(0) %.2e  -> %s (analytic: %s)\n",
                i0*0.1, il*0.1, path, lim, ilf*0.1, pathf, limf, 100*abs(ilf/il - 1), share, c_red_s, c_S_s, rs, ra); flush(stdout)
        N = nnode(p)
        for ix in 1:N
            println(io, string("\"", spec.label, "\",", SHORT[spec.label], ",", spec.k_M, ",", DELTA_UM, ",", xk*1e6, ",", gamma, ",", gamma*xk*1e6, ",",
                    spec.C_med, ",", spec.C_S, ",", spec.species[1].D, ",", spec.species[2].D, ",", spec.D_S, ",", spec.n_S, ",", s_red, ",", s_ox, ",",
                    i_t0*0.1, ",", i0*0.1, ",", i_cap*0.1, ",", il*0.1, ",", ilf*0.1, ",\"", lim, "\",", path, ",", il*0.1, ",",
                    c_red_s, ",", c_S_s, ",", share, ",", rs, ",", ra, ",",
                    p.xc[ix]*1e6, ",", exp(u_at[lidx(p, ix, 1)])/spec.C_med, ",", exp(u_at[lidx(p, ix, 2)])/spec.C_med, ",",
                    exp(u_at[lidx(p, ix, isb)])/spec.C_S))
        end
        flush(io)
        ## the labels' sensitivity to the two diffusivities: +/-25 % on D_med and on D_S, each alone, production mesh
        for (var, fm, fs) in (("D_med", 1 - BAND, 1.0), ("D_med", 1 + BAND, 1.0), ("D_S", 1.0, 1 - BAND), ("D_S", 1.0, 1 + BAND))
            spx = scaled_species(spec, fm, fs)
            xkx = sqrt(spx[2].D / (km * spec.C_S))
            gx = (spec.n_S * F_const * spx[isb].D * spec.C_S / d) / (F_const * spx[1].D * spec.C_med / (s_red * d))
            p0x, i0x, _, _, _ = solve_row(spx, isb, 0.0, d, xkx, 0.0; fine = false)
            px, ilx, limx, pathx, ux = solve_row(spx, isb, km, d, xkx, max(0.9 * F_const * spx[1].D * spec.C_med / (s_red * d), i0x); fine = false)
            if ux === nothing
                sharex, crx, csx, rsx = NaN, NaN, NaN, "no-plateau"
            else
                sharex, crx, csx = profile_stats(px, ux, ilx, km); rsx = regime_solved(csx, sharex)
            end
            fac = var == "D_med" ? fm : fs
            @printf("    %s x %.2f: i_lim %9.3f [%s | %s]  share %.3f  c_S(0) %.2e  -> %s (analytic: %s)\n",
                    var, fac, ilx*0.1, pathx, limx, sharex, csx, rsx, regime_analytic(d, xkx, gx)); flush(stdout)
            println(ios, string("\"", spec.label, "\",", SHORT[spec.label], ",", var, ",", fac, ",", spec.k_M, ",", DELTA_UM, ",", xkx*1e6, ",", gx, ",",
                    ilx*0.1, ",\"", limx, "\",", pathx, ",", crx, ",", csx, ",", sharex, ",", rsx, ",", regime_analytic(d, xkx, gx)))
            flush(ios)
        end
    end
end
end
println("MEDIATED PROFILES DONE")
