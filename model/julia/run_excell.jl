## run_excell.jl — ex-cell vs in-film accounting for chloride-mediated alkene
## epoxidation, an illustrative system modelled on Leow et al., Science 2020, 368,
## 1228 (their headline runs are ethylene in 1.0 M KCl at 300 mA/cm2; they fix the
## chloride OPTIMUM at 2.0 M on plant-gate cost, Fig. 3B, and demonstrate propylene
## as well, Fig. 2E). Modelled here: 2 M chloride (the declared optimum), Cl- oxidized
## at the anode (Cl2/HOCl lumped as one neutral oxidant), propylene at its aqueous
## saturation supplied from the sparged bulk. Same EC' machinery, roles swapped:
## concentrated mediator, dilute substrate. Questions: (1) i_lim (carrier-limited?
## migration factor?) (2) at operating current, where is the reaction front and what
## fraction of the oxidant reacts IN-FILM vs exporting to the bulk?
##
## EVERY INPUT BELOW IS A REGISTRY VALUE, and results/excell.json now records them so
## G-EXCELL can bind them to the registry. Until 2026-09-05 this file carried C_P = 5.0
## (the Henry's-law value the registry row "Propylene C_sat (aq, 1 atm)" WITHDREW on
## 2026-08-22 in favour of 5.67 from Sander's compilation) and D_P = 1.2e-9 (a value
## that matches the registry's Br2 (aq) row and no propene row; the registry's
## propene/H2O Wilke-Chang value is 1.3663e-9, data/mediated_substrates.csv). Both
## moved x_k, the in-film share and the propylene-free zone by 6-30 pct; the
## conclusion (bulk-reaction-limited, >97 pct exported) did not move.

using Printf
include("params.jl"); include("npp_ecprime.jl")

const delta = 200e-6                # stirred batch (measured, 200 +/- 7 um)
const C_Cl  = 2000.0                # mol/m^3: 2 M chloride, Leow's declared optimum (registry: 2 M NaCl aq)
const C_P   = 5.67                  # mol/m^3: registry "Propylene C_sat (aq, 1 atm)", Sander 2023 H_cp = 5.6e-5 mol m-3 Pa-1 x 101325 Pa
const D_Cl  = 2.03e-9               # registry "Cl- (aq)", CRC 97th ed. p. 5-76
const D_OX  = 1.4e-9                # registry "Cl2/HOCl lumped OX (aq)" (declared lump between Cl2(aq) 1.38e-9 and HOCl 1.4e-9)
const D_P   = 1.3663e-9             # registry propene/H2O, Wilke-Chang (data/mediated_substrates.csv, G-DSUB)
const D_H   = 9.3e-9                # registry "H+ (aq)", CRC 97th ed. p. 5-76
const D_Na  = 1.33e-9               # registry "Na+ (aq)", CRC 97th ed. p. 5-76

## Cl- -> "Cl2/HOCl" + e-   (s_red=-1 on Cl-, s_ox=+1; sum z*s = (-1)(-1)=+1 anodic)
## homogeneous: OX + P -> Cl- + products (chlorohydrin path): nu_ox=-1, nu_red=+1, nu_P=-1
function make_problem(k_M; N = 90, dx1 = 0.03e-6, d = delta)
    ## nu_P = -1/(n_S*s_ox) = -0.5: epoxidation is 2 e-/propylene and OX is the
    ## per-electron chlorine equivalent, so each propylene consumes TWO OX events.
    ## H+ product (nu=+1) balances the Cl- (nu=+1, z=-1) so sum z*nu = 0.
    sp = [ECSpecies("Cl-", -1.0, D_Cl, C_Cl + 1e-3, -1.0, +1.0),
          ECSpecies("OX",   0.0, D_OX, C_Cl*1e-5,   +1.0, -1.0),
          ECSpecies("P",    0.0, D_P,  C_P,          0.0, -0.5),
          ECSpecies("H+",  +1.0, D_H, 1e-3,       0.0, +1.0),
          ECSpecies("Na+", +1.0, D_Na, C_Cl,      0.0,  0.0)]
    ECProblem(sp, 2, 3, k_M / 1000.0, geometric_faces(d, dx1, N))
end

i_fick_Cl = F_const * D_Cl * C_Cl / delta
i_cap_P   = 2 * F_const * D_P * C_P / delta       # if propylene (2e-) had to cross the film
@printf("Cl- Fick bound (no migration): %7.1f mA/cm2\n", i_fick_Cl * 0.1)
@printf("in-film propylene cap (n=2)  : %7.2f mA/cm2\n", i_cap_P * 0.1)

k_M = 10.0                                        # HOCl + alkene, representative
p = make_problem(k_M)
xk = sqrt(D_OX / ((k_M/1000) * C_P)) * 1e6
@printf("reaction layer x_k = %.0f um  (vs delta = %.0f um)\n", xk, delta*1e6)

## (1) THE CARRIER LIMIT. This block replaced a hand-rolled current ramp on 2026-09-01.
##
## What the ramp did wrong. It grew i_app until newton_ec! failed, then printed whatever it had
## reached as "solver i_lim". Ramping the CURRENT has a fold at the limiting current -- dc/di
## -> -inf there -- so Newton fails AT the answer and the ramp stops short of it; this is the
## same defect npp_ecprime.jl was fixed for on 2026-08-23, and run_excell.jl was the one solver
## path that never got the fix. It stopped with the carrier at 22-48% of bulk, where its own
## success criterion is <1e-3, and the number it printed moved with the mesh (608.4 mA/cm2 at
## N=90, 426.2 at N=180, same delta). A mesh-dependent value is not a converged one. The SI
## published it as "converges to 785 mA cm-2, exactly 2.00x the Fick bound".
##
## What is used instead: solve_ilim_ec_ccontrol, the production path (46 of the 48 mediated
## cells reach their limit through it). It prescribes the CARRIER surface concentration and
## solves for i_app as an unknown, which is monotone through the fold. Its collapse detector
## watches the reduced species -- here Cl-, the electroactive one -- and merely REPORTS the
## substrate, so the objection that forced the hand-rolled ramp (propylene collapse at the
## front is expected and non-terminal) does not apply to it.
##
## What the answer is, and why this cell still cannot report one at its own delta. On a film
## the branch can be walked to, the solver reaches the collapse criterion cleanly and returns
## EXACTLY the analytic binary-electrolyte result: i_lim = 2 F D_Cl C_Cl / delta, the factor of
## 2 for an anion oxidized in its own salt. Verified below at delta = 25 um and carried outward
## by continuation at fixed surface depletion; it holds at 2.001x from 25 to 60 um and is
## independent of mesh (N = 90/180/360) and of NEGLIGIBLE_C over four decades.
##
## Above ~60 um the branch dies, and the reason is PHYSICAL, not numerical: reaching the
## carrier limit requires the film to hold c_OX(0) = 5.79 M of lumped Cl2/HOCl, against a Cl2
## solubility of ~0.09 M in water at 25 C. The model carries no solubility ceiling and no
## Cl3- speciation -- the same gap already declared for Br2 in S5.5 -- so the state that
## realises the limit at delta = 200 um is one the model has no business asserting. The limit
## is therefore reported from the analytic identity, which needs no such state, and the solver
## value at the production film is reported as the lower bound it is.
u0 = zeros(nvars(p))
for ix in 1:nnode(p), j in 1:length(p.sp)
    u0[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-6))
end
i_seed = 0.30 * i_fick_Cl
seeded = newton_ec!(u0, p, i_seed; max_iter = 200, max_log_step = 3.0)
i_cc, lim_cc, u_cc, frac_cc, branch_cc = seeded ?
    solve_ilim_ec_ccontrol(p; u0 = u0, i0 = i_seed) : (0.0, "seed failed", u0, 1.0, [(1.0, 0.0)])
converged_cc = startswith(lim_cc, "plateau") || startswith(lim_cc, "collapse")
@printf("c-control at delta = %.0f um: i = %7.1f mA/cm2 (%.3fx Fick), c_Cl(0)/bulk = %.2e\n",
        delta*1e6, i_cc*0.1, i_cc/i_fick_Cl, frac_cc)
@printf("   verdict: %s\n", converged_cc ?
        "CONVERGED to the collapse criterion -- this is i_lim" :
        "LOWER BOUND -- the branch ceases before the carrier is depleted; nothing here rests on it")
@printf("   limiter: %s\n", lim_cc)

## the analytic limit, which needs no solved state: for an anion oxidized in its own binary
## salt, i_lim = F D_salt C / (delta (1 - t_-)) = 2 F D_anion C / delta exactly, since
## D_salt/(1 - t_-) = 2 D_- identically. Validated to +0.50% by gate G2 of run_audit.jl.
i_analytic = 2 * i_fick_Cl
@printf("analytic carrier limit (binary NaCl, anion oxidized): %.1f mA/cm2 = 2.00x Fick\n",
        i_analytic * 0.1)

## the same system on a film the branch CAN be walked to, as a check of that factor through
## this code path rather than through the closed-form gate
d_ok = 25e-6
p_ok = ECProblem(p.sp, 2, 3, k_M / 1000.0, geometric_faces(d_ok, 0.03e-6, 90))
u_ok = zeros(nvars(p_ok))
for ix in 1:nnode(p_ok), j in 1:length(p_ok.sp)
    u_ok[lidx(p_ok, ix, j)] = log(max(p_ok.sp[j].c_bulk, 1e-6))
end
i_fick_ok = F_const * D_Cl * C_Cl / d_ok
## This check is LOAD-BEARING -- it is what validates the factor of 2 through the EC-prime path,
## and results/excell.json publishes its result -- so a failure here must stop the script rather
## than fall through. Falling through would leave the variables below undefined and crash at the
## JSON write, which happens AFTER excell_profiles.csv has been rewritten: a hiccup in a seed
## solve would then leave a fresh CSV beside no JSON, and a gate reading the pair would compare
## artifacts from two different runs.
newton_ec!(u_ok, p_ok, 0.30 * i_fick_ok; max_iter = 200, max_log_step = 3.0) ||
    error("reachable-film seed solve failed at delta = $(d_ok*1e6) um; refusing to continue, " *
          "because the factor-of-2 verification below is published and must not be skipped")
i_ok, lim_ok, u_okc, frac_ok, _ = solve_ilim_ec_ccontrol(p_ok; u0 = u_ok, i0 = 0.30 * i_fick_ok)
ratio_ok = i_ok / i_fick_ok
@printf("reachable-film check, delta = %.0f um: i = %8.1f mA/cm2 = %.4fx Fick, c_Cl(0)/bulk = %.2e\n",
        d_ok*1e6, i_ok*0.1, ratio_ok, frac_ok)
@printf("   c_OX(0) at that limit = %.2f M -- the state the carrier limit requires\n",
        exp(u_okc[lidx(p_ok, 1, 2)]) / 1000)
@printf("   %s: the EC-prime path reproduces the analytic factor of 2 to %.2f%%\n",
        abs(ratio_ok - 2) < 0.02 ? "PASS" : "FAIL", 100*abs(ratio_ok - 2)/2)
abs(ratio_ok - 2) < 0.02 ||
    error("the EC-prime path no longer reproduces the analytic factor of 2 " *
          "(got $(ratio_ok)x); results/excell.json would publish a false verification")

## (2) operating point: 130 mA/cm2 (the tier-0 unstirred number) = 1306 A/m2
## (1b) CONTINUATION IN DELTA FROM THE CONVERGED 25 um LIMIT. The SI used to say the 200 um walk
## fails "for a physical reason -- the state that carries the limit holds 5.8 M oxidant". That
## cannot be the distinguishing reason: c_OX at the carrier limit is 2 D_Cl C_Cl / D_OX = 5.8 M on
## EVERY film, and the 25 um solve reaches it. So walk delta outward from that converged state --
## the route that reached the Hofmann detached-front branch -- and record how far the branch
## survives on each film. Measured 2026-09-05: it reaches the limit at 50 um, and ceases at 86 %
## of it on 100 um and 52 % on 200 um, by every route tried. The reason is NOT established here;
## what IS established is where the branch ends, and that is what the SI now states.
p_a = make_problem(k_M; d = d_ok)
DCONT = Vector{Tuple{Float64,Float64,Float64,Float64,Float64,Bool}}()   # (d, i_cc, ratio_fick, c_Cl frac, c_OX, converged)
for d1 in (50e-6, 100e-6, delta)
    res = solve_ilim_ec_continued(dd -> make_problem(k_M; d = dd), d_ok, d1, p_ok, u_okc, i_ok)
    i1 = res[1]
    u1 = res[findfirst(x -> x isa Vector{Float64}, res)]
    p1 = make_problem(k_M; d = d1)
    ic1, lim1, uc1, frc1, _ = solve_ilim_ec_ccontrol(p1; u0 = u1, i0 = 0.9 * i1)
    ## take the further of the two walks -- both are lower bounds where neither converges
    conv1 = startswith(lim1, "plateau") || startswith(lim1, "collapse")
    ibest = max(i1, ic1); fick1 = F_const * D_Cl * C_Cl / d1
    push!(DCONT, (d1, ibest, ibest / fick1, frc1, exp(uc1[lidx(p1, 1, 2)]) / 1000, conv1))
    @printf("delta-continuation to %3.0f um: i = %7.1f mA/cm2 = %.3fx Fick (%.0f%% of the analytic limit), c_Cl(0)/cb = %.2e, c_OX(0) = %.2f M  [%s]\n",
            d1*1e6, ibest*0.1, ibest/fick1, 50*ibest/fick1, frc1, exp(uc1[lidx(p1, 1, 2)])/1000, conv1 ? "converged" : "branch ends")
end
i_op = 1306.0
u = zeros(nvars(p)); N = nnode(p)
for ix in 1:N, j in 1:length(p.sp)
    u[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-6))
end
ok = true
for frac in 0.05:0.05:1.0
    global ok
    ok &= newton_ec!(u, p, frac * i_op; max_iter = 120)
end
println("operating-point converged: $ok")

## in-film reaction integral: F * sum(k*c_ox*c_P*dx) vs i_op
Rint = 0.0
open(joinpath(@__DIR__, "excell_profiles.csv"), "w") do io
    println(io, "x_um,c_Cl_M,c_OX_M,c_P_mM")
    for ix in 1:N
        cox = exp(u[lidx(p, ix, 2)]); cp = exp(u[lidx(p, ix, 3)])
        global Rint += p.k * cox * cp * p.dxc[ix]
        println(io, "$(p.xc[ix]*1e6),$(exp(u[lidx(p,ix,1)])/1000),$(cox/1000),$(cp)")
    end
end
i_infilm = F_const * Rint                          # A/m^2 (1 e- per OX regenerated)
@printf("at %.0f mA/cm2: in-film oxidant consumption = %.2f mA/cm2 (%.1f%%); exported to bulk = %.1f%%\n",
        i_op*0.1, i_infilm*0.1, 100*i_infilm/i_op, 100*(1 - i_infilm/i_op))

## bulk G-L absorption capacity vs cell current (100 mL, kLa = 0.05 1/s)
## The SI states the split is insensitive to the film. That sentence used to carry two typed
## numbers measured at delta = 100 um under the retired inputs; measure it here instead, at the
## same operating point on a halved film, and emit it so the SI interpolates it.
p_h = make_problem(k_M; d = delta / 2)
u_h = zeros(nvars(p_h)); N_h = nnode(p_h)
for ix in 1:N_h, j in 1:length(p_h.sp)
    u_h[lidx(p_h, ix, j)] = log(max(p_h.sp[j].c_bulk, 1e-6))
end
ok_h = true
for frac in 0.05:0.05:1.0
    global ok_h
    ok_h &= newton_ec!(u_h, p_h, frac * i_op; max_iter = 120)
end
ok_h || error("halved-film operating point did not converge; refusing to publish an unsolved split")
Rint_h = 0.0
for ix in 1:N_h
    global Rint_h += p_h.k * exp(u_h[lidx(p_h, ix, 2)]) * exp(u_h[lidx(p_h, ix, 3)]) * p_h.dxc[ix]
end
i_infilm_h = F_const * Rint_h
@printf("at %.0f mA/cm2 on a %.0f um film: in-film = %.2f mA/cm2 (%.1f%%); exported = %.1f%%\n",
        i_op*0.1, delta*5e5, i_infilm_h*0.1, 100*i_infilm_h/i_op, 100*(1 - i_infilm_h/i_op))
kLa = 0.05; V = 1e-4
I_GL = 2 * F_const * kLa * C_P * V                 # A (2 e- per propylene)
@printf("bulk G-L capacity (kLa=%.2f /s, 100 mL): %.1f A  vs cell current at 10 cm2: %.2f A\n",
        kLa, I_GL, i_op * 1e-3)
## Emit the verdict numbers so the SI can be gated against them rather than against a
## transcript. Written by hand (no JSON dependency; this tree is Julia-stdlib only).
## The propylene-free zone is measured the same way the SI states it: the last cell whose
## propylene sits below 5% of bulk.
zone_um = 0.0
for ix in 1:N
    if exp(u[lidx(p, ix, 3)]) < 0.05 * C_P
        global zone_um = p.xc[ix] * 1e6
    end
end
open(joinpath(@__DIR__, "..", "results", "excell.json"), "w") do io
    println(io, "{")
    println(io, "  \"note\": \"ex-cell chloride-mediated propylene epoxidation; written by julia/run_excell.jl\",")
    ## INPUTS, so the gate can bind them to the registry (they were unbound until 2026-09-05)
    ## c_OX_bulk_molm3 is the oxidant's trace bulk seed, read back from the problem object (species 2,
    ## the same slot line 244 reads its surface value from) so the JSON reports what was solved, not a
    ## retyped expression; the registry row "Trace initializations (Med_ox, H+ in aprotic)" declares
    ## the 1e-5 x C_med rule it is an instance of, and G-EXCELL binds the two (2026-09-06).
    @printf(io, "  \"inputs\": {\"C_Cl_M\": %.6g, \"C_P_mM\": %.6g, \"D_Cl_m2s\": %.6g, \"D_OX_m2s\": %.6g, \"D_P_m2s\": %.6g, \"D_H_m2s\": %.6g, \"D_Na_m2s\": %.6g, \"c_OX_bulk_molm3\": %.6g},\n",
            C_Cl/1000, C_P, D_Cl, D_OX, D_P, D_H, D_Na, p.sp[2].c_bulk)
    @printf(io, "  \"delta_um\": %.6g,\n", delta*1e6)
    @printf(io, "  \"i_fick_Cl_mAcm2\": %.6g,\n", i_fick_Cl*0.1)
    @printf(io, "  \"i_cap_P_mAcm2\": %.6g,\n", i_cap_P*0.1)
    @printf(io, "  \"x_k_um\": %.6g,\n", xk)
    @printf(io, "  \"i_ccontrol_mAcm2\": %.6g,\n", i_cc*0.1)
    @printf(io, "  \"ccontrol_frac_carrier\": %.6g,\n", frac_cc)
    println(io, "  \"ccontrol_converged\": ", converged_cc ? "true," : "false,")
    @printf(io, "  \"i_analytic_mAcm2\": %.6g,\n", i_analytic*0.1)
    @printf(io, "  \"reachable_film_um\": %.6g,\n", d_ok*1e6)
    @printf(io, "  \"reachable_ratio_to_fick\": %.6g,\n", ratio_ok)
    @printf(io, "  \"c_OX_at_limit_M\": %.6g,\n", exp(u_okc[lidx(p_ok, 1, 2)])/1000)
    println(io, "  \"dcont\": [")
    for (n, (d1, ib, rf, fr, cox, cv)) in enumerate(DCONT)
        @printf(io, "    {\"delta_um\": %.6g, \"i_mAcm2\": %.6g, \"ratio_fick\": %.6g, \"pct_of_analytic\": %.6g, \"c_Cl_frac\": %.6g, \"c_OX_M\": %.6g, \"converged\": %s}%s\n",
                d1*1e6, ib*0.1, rf, 50*rf, fr, cox, cv ? "true" : "false", n < length(DCONT) ? "," : "")
    end
    println(io, "  ],")
    @printf(io, "  \"i_op_mAcm2\": %.6g,\n", i_op*0.1)
    @printf(io, "  \"k_M\": %.6g,\n", k_M)
    @printf(io, "  \"i_infilm_mAcm2\": %.6g,\n", i_infilm*0.1)
    @printf(io, "  \"infilm_pct\": %.6g,\n", 100*i_infilm/i_op)
    @printf(io, "  \"exported_pct\": %.6g,\n", 100*(1 - i_infilm/i_op))
    @printf(io, "  \"half_delta_um\": %.6g,\n", delta*5e5)
    @printf(io, "  \"infilm_pct_half_delta\": %.6g,\n", 100*i_infilm_h/i_op)
    @printf(io, "  \"exported_pct_half_delta\": %.6g,\n", 100*(1 - i_infilm_h/i_op))
    @printf(io, "  \"c_OX_at_op_M\": %.6g,\n", exp(u[lidx(p, 1, 2)])/1000)
    @printf(io, "  \"propylene_free_zone_um\": %.6g\n", zone_um)
    println(io, "}")
end
println("wrote results/excell.json")
println("DONE")
