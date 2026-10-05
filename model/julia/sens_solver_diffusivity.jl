## SENSITIVITY: double the four assumption-class solver-species diffusivities and re-solve.
##
##     cd Section4_Model/julia && julia --project=. sens_solver_diffusivity.jl
##
## Fifteen category-4 registry rows carry the sensitivity "doubling ClO4-, SCN-, Br- and Br2
## together and re-solving moves ONE published count: the unstirred >=25 count 11 -> 12 of 50".
## That result was measured, but against a baseline that has since moved: the unstirred count is
## now 12 (the Br-mediated Hofmann x unstirred cell was resolved by delta-continuation instead of
## being floored to Tier-0). A sensitivity whose baseline has moved is not evidence of anything,
## and those 15 rows' tier-2 classification rests on it, so it is re-measured here rather than
## re-typed. Writes mediated_ec_matrix_2xD.csv; the merged counts are computed by
## data/build_merged_matrix.py --mediated <that file>.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end

const DOUBLED = ("ClO4-", "SCN-", "Br-", "Br2")
bump(sp) = ECSpecies(sp.name, sp.z, sp.name in DOUBLED ? 2sp.D : sp.D, sp.c_bulk, sp.s, sp.nu)

open(joinpath(@__DIR__, "mediated_ec_matrix_2xD.csv"), "w") do io
    println(io, "reaction,reactor,delta_um,xk_um,i_tier0_mAcm2,i_saveant_mAcm2,i_subcap_mAcm2,i_ec_mAcm2,amplification,limiter,flag,path")
    for spec0 in SPECS
        species = [bump(s) for s in spec0.species]
        spec = MedSpec(spec0.label, spec0.k_M, spec0.nu_solv, spec0.D_red, spec0.n_c,
                       spec0.n_S, spec0.C_med, spec0.C_S, spec0.D_S, species)
        km = spec.k_M / 1000.0
        xk = sqrt(spec.species[2].D / (km * spec.C_S))
        isb = findfirst(s -> s.name == "Sub", spec.species)
        @printf("=== %s  (x_k = %.1f um)\n", spec.label, xk*1e6); flush(stdout)
        mkprob = dd -> ECProblem(spec.species, 2, isb, km,
                                 geometric_faces(dd, clamp(xk/50, 0.02e-6, 0.9*dd/90), 90))
        order = sort(collect(REACTORS), by = r -> delta_eff(r.key, spec.D_red, spec.nu_solv))
        rows = Dict{String,String}(); anchor = nothing
        for r in order
            d = delta_eff(r.key, spec.D_red, spec.nu_solv)
            i_t0  = F_const * spec.D_red * spec.C_med / (abs(spec.species[1].s) * d)
            i_sav = spec.n_c * F_const * spec.C_med * sqrt(spec.species[2].D * km * spec.C_S)
            i_cap = spec.n_S * F_const * spec.D_S * spec.C_S / d
            p = mkprob(d)
            il, lim, u_safe, i_safe = solve_ilim_ec(p; i_start = 0.02*i_t0, growth = 1.15)
            path = "direct"
            if il < 0.9*i_t0 && anchor !== nothing
                res = solve_ilim_ec_continued(mkprob, anchor[1], d, anchor[2], anchor[3], anchor[4])
                if res !== nothing && res.i > il
                    il, path = res.i, "delta-continued"; lim = "delta-continued; " * lim
                    p, u_safe, i_safe = res.p, res.u, res.i
                end
            end
            flag = il >= 0.9*i_t0 ? "ok" : "wall"
            (flag == "ok" && i_safe > 0.0) && (anchor = (d, p, copy(u_safe), i_safe))
            @printf("  %-28s d %7.1f um  EC' %8.1f mA/cm2  (%s)\n", r.label, d*1e6, il*0.1, path)
            flush(stdout)
            rows[r.label] = "\"$(spec.label)\",\"$(r.label)\",$(d*1e6),$(xk*1e6),$(i_t0*0.1),$(i_sav*0.1),$(i_cap*0.1),$(il*0.1),$(il/i_t0),\"$lim\",\"$flag\",\"$path\""
        end
        for r in REACTORS; println(io, rows[r.label]); flush(io); end
    end
end
println("2xD MATRIX DONE")
