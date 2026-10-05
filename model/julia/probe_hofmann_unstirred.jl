## The ONE production cell that does not converge: Br-mediated Hofmann rearrangement in an
## UNSTIRRED beaker (delta = 300 um, x_k = 2.35 um, delta/x_k = 128 -- deep total catalysis).
##
##     cd Section4_Model/julia && julia --project=. probe_hofmann_unstirred.jl
##
## Why it matters out of all proportion to one cell: the pipeline floors it to the Tier-0
## commuting bound, 6.95 mA cm-2, which is below the 25 mA cm-2 threshold. Its substrate-supply
## scale is 51.46. So whether this single cell clears 25 decides whether the manuscript's
## headline unstirred counts read 11/50 and 8/50 (as shipped) or 12/50 and 9/50.
##
## The production ramp stalls at 0.74 mA cm-2 -- BELOW the commuting bound, so it is not a
## physical answer, it is a dead solve. The production mesh stretches toward the ELECTRODE
## (dx1 ~ x_k/50), which is right when the reaction layer hugs the wall. Here the substrate is
## exhausted and the front DETACHES into the interior, where that mesh is coarsest. This probe
## varies the two things that should matter -- where the mesh puts its resolution, and how the
## solution is continued -- and asks whether any of them reaches a stable answer.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end

spec = SPECS[findfirst(x -> x.label == "Br-mediated Hofmann rearrangement", SPECS)]
km   = spec.k_M / 1000.0
xk   = sqrt(spec.species[2].D / (km * spec.C_S))
R300 = REACTORS[findfirst(x -> x.key == :natural, REACTORS)]
d    = delta_eff(R300.key, spec.D_red, spec.nu_solv)
i_t0 = F_const * spec.D_red * spec.C_med / (abs(spec.species[1].s) * d)
i_cap = spec.n_S * F_const * spec.D_S * spec.C_S / d
i_sav = spec.n_c * F_const * spec.C_med * sqrt(spec.species[2].D * km * spec.C_S)
@printf("delta %.1f um   x_k %.2f um   delta/x_k %.0f\n", d*1e6, xk*1e6, d/xk)
@printf("tier0 %.2f   subcap %.2f   saveant %.1f   mA/cm2   (production ramp gives 0.74)\n\n",
        i_t0*0.1, i_cap*0.1, i_sav*0.1)

function run(dx1, N, growth; u0 = nothing)
    p = ECProblem(spec.species, 2, findfirst(s -> s.name == "Sub", spec.species),
                  km, geometric_faces(d, dx1, N))
    il, lim, _, _ = solve_ilim_ec(p; i_start = 0.02 * i_t0, growth = growth, u0 = u0)
    (i = il * 0.1, lim = lim)
end

@printf("%-34s %6s %8s %10s   %s\n", "mesh", "N", "dx1 um", "i mA/cm2", "limiter")
for (tag, dx1, N, g) in [
        ("production (x_k/50, stretched)", clamp(xk/50, 0.02e-6, 0.9*d/90),  90, 1.15),
        ("production, slow ramp",          clamp(xk/50, 0.02e-6, 0.9*d/90),  90, 1.02),
        ("production mesh, N=180",         clamp(xk/50, 0.02e-6, 0.9*d/180),180, 1.15),
        ("production mesh, N=360",         clamp(xk/50, 0.02e-6, 0.9*d/360),360, 1.15),
        ("UNIFORM, N=90",                  d/90,                             90, 1.15),
        ("UNIFORM, N=180",                 d/180,                           180, 1.15),
        ("UNIFORM, N=360",                 d/360,                           360, 1.15),
        ("UNIFORM, N=720",                 d/720,                           720, 1.15),
        ("mild stretch (d/300), N=180",    d/300,                           180, 1.15),
        ("mild stretch (d/300), N=360",    d/300,                           360, 1.15),
        ("mild stretch, N=360, slow ramp", d/300,                           360, 1.02)]
    a = run(dx1, N, g)
    @printf("%-34s %6d %8.3f %10.2f   %s\n", tag, N, dx1*1e6, a.i, a.lim)
    flush(stdout)
end
