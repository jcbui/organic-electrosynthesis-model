## run_section4.jl — orchestrates the Section 4 transport model.
##   julia run_section4.jl
## Outputs: tier0_matrix.csv, npp_validation.txt, npp_support_sweep.csv,
##          npp_profiles.csv, cellvoltage.csv

using Printf, DelimitedFiles
include("params.jl"); include("correlations.jl"); include("npp.jl")
include("cellvoltage.jl"); include("reactions_table.jl")

## ═══ Tier 0: 50 reactions × 6 reactor archetypes ═══════════════════════════════
println("═══ Tier 0: i_lim matrix (50 × $(length(REACTORS))) ═══")
hdr = vcat(["class","reaction","carrier"], [String(r.key) for r in REACTORS])
rows = Vector{Vector{Any}}()
for rx in RXNS
    row = Any[rx.cls, rx.name, rx.carrier]
    for r in REACTORS
        d = delta_eff(r.key, rx.D, rx.nu)
        push!(row, i_lim_tier0(rx.n, rx.D, rx.C, d))
    end
    push!(rows, row)
end
open(joinpath(@__DIR__, "tier0_matrix.csv"), "w") do io
    println(io, join(hdr, ","))
    for row in rows
        println(io, join([x isa Float64 ? @sprintf("%.4g", x) : "\"$x\"" for x in row], ","))
    end
end
for (k, r) in enumerate(REACTORS)
    vals = [row[3 + k] for row in rows]
    below = count(v -> v < I_THRESH, vals)
    @printf("  %-28s median %7.1f mA/cm2   below %2.0f mA/cm2: %d/50\n",
            r.label, sort(vals)[25], I_THRESH, below)
end

## ═══ Tier 1 validation gate A: neutral substrate, excess support ══════════════
println("\n═══ Tier 1 (NPP) validation ═══")
del = 100e-6
spA = [Species("S",   0.0, 1.0e-9, 200.0, -0.5),     # neutral, n=2
       Species("H+",  1.0, 9.3e-9,   1.0,  1.0),     # proton release
       Species("K+",  1.0, 1.9e-9, 500.0,  0.0),
       Species("A-", -1.0, 2.0e-9, 701.0,  0.0)]
pA = FilmProblem(spA, del, 60)
ilimA, curveA = solve_ilim(pA; jr = 1)
fickA = i_fick(pA, 1)
@printf("  gate A (excess support): i_lim/i_fick = %.3f  (target 1.00 ± 0.03)\n", ilimA / fickA)

## ═══ Tier 1 validation gate B: Kolbe binary electrolyte (migration ×2) ════════
spB(SR) = [Species("RCO2-", -1.0, 8.0e-10, 500.0, -1.0),
           Species("K+",     1.0, 1.9e-9,  500.0 * (1 + SR), 0.0),
           Species("X-",    -1.0, 1.5e-9,  500.0 * SR,       0.0)]
pB0 = FilmProblem(spB(0.0), del, 60)
ilimB0, _ = solve_ilim(pB0; jr = 1, imax_over_fick = 3.0)
@printf("  gate B (binary Kolbe):   i_lim/i_fick = %.3f  (analytic: 2.00)\n", ilimB0 / i_fick(pB0, 1))

## ═══ Tier 1: migration enhancement vs supporting-electrolyte ratio ════════════
println("\n═══ Kolbe migration enhancement vs support ratio ═══")
open(joinpath(@__DIR__, "npp_support_sweep.csv"), "w") do io
    println(io, "support_ratio,ilim_over_fick")
    for SR in [0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0]
        pS = FilmProblem(spB(SR), del, 60)
        il, _ = solve_ilim(pS; jr = 1, imax_over_fick = 3.0)
        enh = il / i_fick(pS, 1)
        @printf("  SR = %6.2f   i_lim/i_Fick = %.3f\n", SR, enh)
        println(io, "$SR,$enh")
    end
end

## concentration/potential profiles near the plateau, low vs high support
open(joinpath(@__DIR__, "npp_profiles.csv"), "w") do io
    println(io, "case,x_um,c_S_norm,phi_mV")
    for (tag, SR) in [("SR0", 0.0), ("SR10", 10.0)]
        pP = FilmProblem(spB(SR), del, 60)
        ilP, _ = solve_ilim(pP; jr = 1, imax_over_fick = 3.0)
        u = zeros(nvars(pP))
        for ix in 1:pP.N, j in 1:length(pP.sp)
            u[lidx(pP, ix, j)] = log(max(pP.sp[j].c_bulk, 1e-8))
        end
        for frac in 0.1:0.1:0.9                     # warm-start ramp to 0.9 i_lim
            newton_solve!(u, pP, frac * ilP)
        end
        dx = pP.delta / pP.N
        for ix in 1:pP.N
            x = (ix - 0.5) * dx * 1e6
            cS = exp(u[lidx(pP, ix, 1)]) / pP.sp[1].c_bulk
            ph = u[pidx(pP, ix)] * 1e3
            println(io, "$tag,$x,$cS,$ph")
        end
    end
end

## ═══ Cell voltage & Joule heating ═════════════════════════════════════════════
println("\n═══ Cell voltage / Joule heating ═══")
open(joinpath(@__DIR__, "cellvoltage.csv"), "w") do io
    println(io, "electrolyte,kappa_Sm,gap_label,gap_m,i_mAcm2,E_cell_V,Q_W_cm2")
    for e in ELECS, (glab, g) in GAPS, i in [10.0, 25.0, 50.0, 100.0, 300.0]
        E = E_cell(i, e.kappa, g); Q = Q_joule_Wcm2(i, e.kappa, g)
        println(io, "\"$(e.label)\",$(e.kappa),\"$glab\",$g,$i,$E,$Q")
    end
end
## ═══ Worked boil-off example (SI §S6.1) ══════════════════════════════════════
## CANONICAL GEOMETRY: 0.2 M NaI/DMF across the 2 cm gap. kappa is READ FROM
## data/electrolytes.csv via read_kappa(), never typed here: this block used to carry the
## literal 0.80 S/m while read_kappa() returned 0.877 in the SAME RUN, so the script printed
## T_ss = 202 C where SI S6.1 prints 187 C. That is the failure the governing standard names
## -- a worked example retracted in the prose and still computed by the code.
## beaker gap, 100 mA/cm2, 10 cm2 electrodes, 100 mL batch.
##
## THE PREVIOUS VERSION OF THIS BLOCK IS RETRACTED and must not be restored: it ran
## ELECS[2] = 0.1 M Bu4NBF4/DMF (unregistered, 3.5 mS/cm) at a 5 mm gap and concluded
## the cell settled just below boiling. §S6.1 retracts that electrolyte and that gap by
## name; on the registered electrolyte at the canonical gap the conclusion INVERTS —
## the steady state sits above DMF's boiling point, so the cell boils rather than runs
## hot. Prior block: _archive/retracted_electrolytes_20260802/julia/run_section4.jl
##
## The heat balance is the lumped model of figs/thermal_model.py (the single source of
## truth for the thermal analysis). The three geometry/film constants below are mirrored
## from it; IF YOU CHANGE THEM, CHANGE THEM THERE FIRST. All are registry rows of
## data/parameters_provenance.csv, category 9:
##   h_ext = 13.0 W/m2 K (derived: 6.36 convection + 6.60 radiation at Ts = 65 C)
##   h_int = 100 W/m2 K  (assumption: stagnant electrolyte)
##   sigma = 12.5        (derived: 0.0125 m2 registered vessel external area / 1e-3 m2)
## Solvent properties are registry rows too: DMF rho 0.944 g/mL (cat 2, measured),
## DMF cp 2.05 J/g K and Tb 153 C (cat 9), THF rho 0.883, cp 1.72, Tb 66 C.
## NOTE the heat load q includes the ACTIVATION term as well as i^2 L/kappa; it is
## therefore larger than Q_joule_Wcm2, which is ohmic-only.
println("\n═══ Worked boil-off example (SI §S6.1) ═══")
let T_AMB = 25.0, H_EXT = 13.0, H_INT = 100.0, SIGMA = 12.5,
    gap = 2.0e-2, i = 100.0, A = 10.0, V_mL = 100.0

    U = (1.0 / (1.0/H_INT + 1.0/H_EXT)) * SIGMA * 1e-4     # W/cm2 K, referred to A_elec
    q_Wcm2(i, kap) = (2 * (2*RT_F) * asinh(i/2.0) + i*10.0*gap/kap) * i * 10.0 * 1e-4
    @printf("  unstirred 100 mL beaker, 2 cm gap, 10 cm2: U' = %.5f W/cm2 K\n", U)

    for (lab, ekey, rho, cp, Tb) in [("0.2 M NaI / DMF",  "0.2 M NaI/DMF",  0.944, 2.05, 153.0),
                                     ("3.0 M LiBr / THF", "3.0 M LiBr/THF", 0.883, 1.72,  66.0)]
        kap = read_kappa(ekey)                           # S/m; read_kappa already converts from mS/cm
        q    = q_Wcm2(i, kap)                              # W/cm2 (activation + ohmic)
        ohm  = i * 10.0 * gap / kap                        # V
        mcp  = V_mL * rho * cp                             # J/K
        dTdt = q * A / mcp                                 # K/s
        Tss  = T_AMB + q / U
        @printf("  %-17s E_cell(%3.0f) = %5.1f V (ohmic %5.1f V) | E_cell(50) = %5.1f V\n",
                lab, i, E_cell(i, kap, gap), ohm, E_cell(50.0, kap, gap))
        @printf("  %-17s q = %.2f W/cm2 -> %.1f W over %.0f cm2; m.cp = %.0f J/K\n",
                "", q, q*A, A, mcp)
        @printf("  %-17s self-heats at %.1f K/min; reaches Tb = %.0f C in %.1f min\n",
                "", dTdt*60, Tb, (Tb - T_AMB)/(dTdt*60))
        @printf("  %-17s passive steady state T_ss = %.0f C  -> %s (Tb = %.0f C)\n\n",
                "", Tss, Tss > Tb ? "BOILS" : "does not boil", Tb)
    end
end
println("\nDONE — CSVs written.")
