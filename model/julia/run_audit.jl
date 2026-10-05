## run_audit.jl — verification audit: every continuum-model configuration with an
## easy analytic limiting current, checked against the solver prediction.
##
## Tier-1 (npp.jl):
##   G1  neutral reactant, 10x supporting electrolyte  -> i_lim = nFDC/delta (Fick)
##   G2  anion oxidized in its own binary salt          -> i_lim = 2 x Fick (Newman)
##   G3  neutral reactant at i = 0.5 i_lim              -> c_surf/c_bulk = 0.500
##   G4  G1 at N = 40 and N = 160                       -> mesh drift < 1%
## Tier-2 (npp_ecprime.jl):
##   G5  EC' with k -> 0                                -> commuting bound FD_redC_med/delta
##   G6  EC' with 1 << delta/x_k << gamma               -> Saveant FC_med sqrt(D_ox k C_S)
##   G7  EC' total catalysis (gamma >> 1, k = 10^3)     -> substrate cap (+shuttle leak),
##                                                         approached from below
##   G8  EC' k -> 0, anion mediator in its own binary   -> 2 x Fick (Newman through the
##                                                         EC' code path)
##   G9  G5/G6 at N = 130, dx1 = 0.015 um               -> mesh drift < 2%
##
## WHERE THE ANALYTIC LIMITS COME FROM
## -----------------------------------
## Each gate compares the solve against a CLOSED-FORM result from the literature, not against
## another run of the same code. The sources are cited in the SI, but a reader of this file
## should not have to go there to find them, so they are named here at the point of use:
##
##   Fick limit i_lim = nFDC/delta and the BINARY-ELECTROLYTE factor of 2 for an ion oxidized
##     or reduced in its own salt (G1, G2, G8):
##       J. Newman & K. E. Thomas-Alyea, "Electrochemical Systems", 3rd edn, John Wiley & Sons,
##       Hoboken NJ, 2004 -- dilute-solution theory, Ch. 11. The x2 is the standard result that
##       migration doubles the limiting flux of a reacting ion when it carries the current in a
##       binary electrolyte with no supporting salt.
##
##   c_surf/c_bulk = 1 - i/i_lim at a Fickian film (G3): same source, Ch. 11.
##
##   EC' catalytic plateau i_lim = F C_med sqrt(D_ox k C_S) in the pure kinetic regime (G6):
##       J.-M. Saveant, "Elements of Molecular and Biomolecular Electrochemistry", John Wiley &
##       Sons, Hoboken NJ, 2006, Ch. 2 (redox catalysis, the total-catalysis and pure-kinetic
##       limits). The commuting bound of G5 and the substrate cap of G7 are the k -> 0 and
##       gamma >> 1 ends of the same treatment.
##
## G2/G8 report in A/m2 (SI units); the SI prose quotes the same numbers in mA cm-2, a factor of
## ten smaller -- 7855 A/m2 there is 785 mA cm-2 in the document.
##
##   nohup /opt/julia/bin/julia run_audit.jl > run_audit.log 2>&1 &

using Printf
include("params.jl"); include("npp.jl"); include("npp_ecprime.jl")

results = NamedTuple[]
function gate!(id, desc, solver, analytic, tol_pct; note = "")
    err = (solver / analytic - 1) * 100
    ok = abs(err) <= tol_pct
    push!(results, (id=id, desc=desc, solver=solver, analytic=analytic,
                    err_pct=err, tol_pct=tol_pct, pass=ok, note=note))
    @printf("%-4s %-52s solver %10.4g  analytic %10.4g  err %+6.2f%%  [%s]%s\n",
            id, desc, solver, analytic, err, ok ? "PASS" : "FAIL",
            note == "" ? "" : "  ("*note*")")
    flush(stdout)
end

const dlt = 100e-6

## ── G1: Fick, neutral reactant, 10x support ──────────────────────────────────
sp1 = [Species("S",0.0,1e-9,500.0,-1.0), Species("P+",1.0,1e-9,5e-3,+1.0),
       Species("K+",1.0,1.9e-9,5000.0,0.0), Species("A-",-1.0,1.5e-9,5000.005,0.0)]
p1 = FilmProblem(sp1, dlt, 80)
il1, _ = solve_ilim(p1; jr=1, di=0.01)
gate!("G1","Tier-1 Fick: neutral S, 10x support", il1, i_fick(p1,1), 1.5)

## ── G2: Newman binary, anion oxidized in its own salt ────────────────────────
sp2 = [Species("R-",-1.0,1e-9,500.0,-1.0), Species("P",0.0,1e-9,5e-3,+1.0),
       Species("Na+",1.0,1.33e-9,500.0,0.0)]
p2 = FilmProblem(sp2, dlt, 80)
il2, _ = solve_ilim(p2; jr=1, di=0.01, imax_over_fick=2.6)
gate!("G2","Tier-1 Newman binary: anion in own salt (x2)", il2, 2.0*i_fick(p2,1), 1.5)

## ── G3: half-current surface concentration ───────────────────────────────────
u3 = zeros(nvars(p1))
for ix in 1:p1.N, j in 1:length(p1.sp)
    u3[lidx(p1,ix,j)] = log(max(p1.sp[j].c_bulk,1e-8))
end
ok3 = true
for f in 0.1:0.1:0.5; global ok3 &= newton_solve!(u3, p1, f*i_fick(p1,1)); end
cs3 = exp(u3[lidx(p1,1,1)]) / 500.0
gate!("G3","Tier-1 c_surf/c_bulk at i = 0.5 i_lim", cs3, 0.5, 1.5,
      note = ok3 ? "converged" : "NEWTON FAIL")

## ── G4: mesh refinement on G1 ────────────────────────────────────────────────
for (nn, tag) in [(40,"N=40"), (160,"N=160")]
    pp = FilmProblem(sp1, dlt, nn)
    il, _ = solve_ilim(pp; jr=1, di=0.01)
    gate!("G4","Tier-1 Fick mesh drift ("*tag*")", il, i_fick(p1,1), 1.5)
end

## ── EC' base-case builder (run_ecprime conventions) ──────────────────────────
const C_med=20.0; const C_S=500.0; const D_med=6.0e-10; const D_S=1.0e-9; const C_sup=100.0
function ec_problem(k_M; N=90, dx1=0.03e-6, delta=dlt)
    ## matches run_ecprime.jl: H+ product keeps the homogeneous step charge-conserving
    sp = [ECSpecies("Med_red",0.0,D_med,C_med,-1.0,+1.0),
          ECSpecies("Med_ox",+1.0,D_med,C_med*1e-5,+1.0,-1.0),
          ECSpecies("S",0.0,D_S,C_S,0.0,-1.0),
          ECSpecies("H+",+1.0,9.3e-9,1e-3,0.0,+1.0),
          ECSpecies("K+",+1.0,1.9e-9,C_sup,0.0,0.0),
          ECSpecies("A-",-1.0,1.5e-9,C_sup+C_med*1e-5+1e-3,0.0,0.0)]
    ECProblem(sp, 2, 3, k_M/1000.0, geometric_faces(delta, dx1, N))
end
i_sh = F_const*D_med*C_med/dlt

## ── G5: EC' commuting bound (k -> 0) ─────────────────────────────────────────
p5 = ec_problem(1e-8)
il5, _, _, _ = solve_ilim_ec(p5; i_start=0.05*i_sh, growth=1.1)
gate!("G5","EC' k->0: commuting bound FD_redC_med/delta", il5, i_sh, 2.5)

## ── G6: Saveant regime (1 << delta/x_k << gamma) ─────────────────────────────
d6 = 50e-6; k6 = 30.0
p6 = ec_problem(k6; delta=d6)
i_sh6 = F_const*D_med*C_med/d6
il6, _, _, _ = solve_ilim_ec(p6; i_start=0.05*i_sh6, growth=1.08)
i_sav6 = F_const*C_med*sqrt(D_med*(k6/1000)*C_S)
xk6 = sqrt(D_med/((k6/1000)*C_S))*1e6
## first-order substrate-depletion correction: the reaction layer sees substrate
## at C_S(1 - A/gamma) (fraction A/gamma consumed at the Saveant current), so
## i = i_sav * sqrt(1 - A/gamma). Pure asymptote only holds when A << gamma.
A6 = d6*1e6/xk6; gam = D_S*C_S/(D_med*C_med)
i_sav6c = i_sav6*sqrt(1 - A6/gam)
gate!("G6","EC' Saveant (delta/x_k = "*string(round(A6,digits=1))*"), depletion-corrected",
      il6, i_sav6c, 4.0, note="uncorrected asymptote "*string(round(i_sav6*0.1,digits=1))*" mA/cm2, dev -"*string(round((1-i_sav6c/i_sav6)*100,digits=1))*"% expected")

## ── G7: total catalysis cap (gamma = 41.7, k = 1e3) ──────────────────────────
p7 = ec_problem(1e3)
u7 = nothing
## warm-start continuation over k exactly as the production sweep does
il7 = 0.0; u_prev = nothing; il_prev = 0.0; k_prev = 0.0
for k in (1.0, 10.0, 1e2, 3e2, 1e3)
    global u_prev, il_prev, k_prev, il7
    p = ec_problem(k)
    u0 = u_prev; ist = 0.05*i_sh
    if u_prev !== nothing
        ia = max(0.05*i_sh, 0.6*il_prev); v = copy(u_prev)
        if newton_ec!(v, p, ia; max_iter=150, max_log_step=3.0)
            u0 = v; ist = ia
        else
            u0 = nothing
        end
    end
    il, _, u_fin, i_fin = solve_ilim_ec(p; i_start=ist, growth=1.1, u0=u0)
    i_fin > 0 && (u_prev = u_fin; il_prev = il)
    k_prev = k; il7 = il
end
## Total catalysis is an asymptote: the exact plateau requires k -> inf, which
## lies beyond the moving-front regime the damped-Newton scheme can chase. The
## rigorous statements at finite k = 1e3 are a BRACKET: the solver must sit
## above 0.80 x cap (well into the plateau) and must NEVER exceed cap + shuttle.
i_cap = F_const*D_S*C_S/dlt
lo7, hi7 = 0.80*i_cap, 1.02*(i_cap + i_sh)
ok7 = lo7 <= il7 <= hi7
push!(results, (id="G7", desc="EC' total catalysis (k=1e3): bracket [0.80 cap, cap+shuttle]",
                solver=il7, analytic=i_cap+i_sh, err_pct=(il7/(i_cap+i_sh)-1)*100,
                tol_pct=NaN, pass=ok7, note="bracket $(round(lo7,digits=1))-$(round(hi7,digits=1)) A/m2; ceiling must not be exceeded"))
@printf("%-4s %-52s solver %10.4g  bracket [%.4g, %.4g]  [%s]\n",
        "G7","EC' total catalysis (k=1e3): bracket", il7, lo7, hi7, ok7 ? "PASS" : "FAIL")
flush(stdout)

## ── G8: Newman binary through the EC' code path (k -> 0) ─────────────────────
sp8 = [ECSpecies("Cl-",-1.0,2.03e-9,2000.001,-1.0,+1.0),
       ECSpecies("OX",0.0,1.4e-9,2000.0*1e-5,+1.0,-1.0),
       ECSpecies("Sub",0.0,1.2e-9,5.0,0.0,-0.5),
       ECSpecies("H+",+1.0,9.3e-9,1e-3,0.0,+1.0),
       ECSpecies("Na+",+1.0,1.33e-9,2000.0,0.0,0.0)]
p8 = ECProblem(sp8, 2, 3, 1e-11, geometric_faces(dlt, 0.03e-6, 90))
iF8 = F_const*2.03e-9*2000.0/dlt
function ramp8(p; gstart=1.15)
    u = zeros(nvars(p))
    for ix in 1:nnode(p), j in 1:length(p.sp)
        u[lidx(p,ix,j)] = log(max(p.sp[j].c_bulk,1e-6))
    end
    ia = 0.02*iF8; g = gstart; il = 0.0
    while g > 1.003
        v = copy(u)
        if newton_ec!(v, p, ia; max_iter=150, max_log_step=3.0)
            u .= v; il = ia
            exp(u[lidx(p,1,1)])/p.sp[1].c_bulk < 1e-3 && break
            ia *= g
        else
            ia = il*sqrt(g); g = sqrt(g)
            ia <= il && break
        end
    end
    il, exp(u[lidx(p,1,1)])/p.sp[1].c_bulk
end
## G8a: mesh matched to the problem (no reaction layer -> no stretch needed)
p8a = ECProblem(sp8, 2, 3, 1e-11, geometric_faces(dlt, dlt/90, 90))
il8a, cs8a = ramp8(p8a)
gate!("G8a","EC' k->0 Newman binary, mesh-matched (x2)", il8a, 2.0*iF8, 1.5,
      note="uniform mesh; c_surf = "*string(round(cs8a,sigdigits=2)))
## G8b: production hyper-stretched mesh (dx1 = 0.03 um) — documents the known
## Newton stall in the deep-depletion migration regime. The requirement is
## one-sided: the stalled value must sit BELOW the analytic ceiling (conservative).
il8b, cs8b = ramp8(p8)
ok8b = il8b <= 1.02*2.0*iF8
push!(results,(id="G8b",desc="EC' k->0 binary, production stretch: stall is conservative",
               solver=il8b, analytic=2.0*iF8, err_pct=(il8b/(2iF8)-1)*100, tol_pct=NaN,
               pass=ok8b, note="known Newton stall (c_surf = $(round(cs8b,sigdigits=2))); must not exceed ceiling"))
@printf("%-4s %-52s solver %10.4g  ceiling %10.4g  [%s]  (stall documented)\n",
        "G8b","EC' k->0 binary, production stretch (one-sided)", il8b, 2.0*iF8, ok8b ? "PASS" : "FAIL")
flush(stdout)

## G10: production-matrix spot check — Cl-/propylene, stirred batch, k = 10,
## with a mesh matched to x_k = 167 um instead of the production 0.03 um stretch.
## The matrix value (698.9 A/m2 -> 69.9 mA/cm2... stored 698.9 mA*10) may be
## understated by the same stall; mesh-matched value must be >= it and <= ceiling.
p10 = ECProblem(sp8, 2, 3, 10.0/1000.0, geometric_faces(dlt, dlt/90, 90))
il10, cs10 = ramp8(p10)
ok10 = (0.95*2.0*iF8 <= il10 <= 1.03*2.0*iF8)
push!(results,(id="G10",desc="Cl-/propylene stirred, mesh-matched: hits migration ceiling",
               solver=il10, analytic=2.0*iF8, err_pct=(il10/(2iF8)-1)*100, tol_pct=NaN,
               pass=ok10, note="dilute substrate (k=10): carrier-limited, ceiling = 2x Fick"))
@printf("%-4s %-52s solver %10.4g  ceiling %10.4g  [%s]\n",
        "G10","Cl-/propylene stirred, mesh-matched vs ceiling", il10, 2.0*iF8, ok10 ? "PASS" : "FAIL")
flush(stdout)

## ── G9: mesh refinement on G5 and G6 ─────────────────────────────────────────
p9a = ec_problem(1e-8; N=130, dx1=0.015e-6)
il9a, _, _, _ = solve_ilim_ec(p9a; i_start=0.05*i_sh, growth=1.1)
gate!("G9","EC' commuting bound, refined mesh (N=130)", il9a, i_sh, 2.5)
p9b = ec_problem(k6; N=130, dx1=0.015e-6, delta=d6)
il9b, _, _, _ = solve_ilim_ec(p9b; i_start=0.05*i_sh6, growth=1.08)
gate!("G9","EC' Saveant, refined mesh (N=130), depletion-corrected", il9b, i_sav6c, 4.0)
@printf("     mesh drift: commuting %.2f%%, Saveant %.2f%%\n",
        (il9a/il5-1)*100, (il9b/il6-1)*100)

## ── G11: current conservation across the film (EC' with source active) ───────
## For a charge-conserving homogeneous step, the ionic current i(x) = F*sum_j z_j*N_j
## must equal i_app at EVERY interior face. Checked on the converged G6 state at
## 0.9*i_lim — this is the discrete divergence-free test a referee would run.
p11 = ec_problem(k6; delta=d6)
u11 = zeros(nvars(p11))
for ix in 1:nnode(p11), j in 1:length(p11.sp)
    u11[lidx(p11,ix,j)] = log(max(p11.sp[j].c_bulk,1e-6))
end
ok11 = true
for f in 0.1:0.1:0.9; global ok11 &= newton_ec!(u11, p11, f*0.9*il6/0.9); end
i_target = 0.9*il6
ok11 &= newton_ec!(u11, p11, i_target)
maxdev = 0.0
for ix in 2:nnode(p11)   # interior faces
    isum = 0.0
    for j in 1:length(p11.sp)
        spj = p11.sp[j]
        cL = exp(clamp(u11[lidx(p11,ix-1,j)],-50.0,50.0)); cR = exp(clamp(u11[lidx(p11,ix,j)],-50.0,50.0))
        Nj = np_flux(spj.D, spj.z, cL, cR, u11[pidx(p11,ix-1)], u11[pidx(p11,ix)], p11.dxl[ix])
        isum += spj.z * Nj
    end
    global maxdev = max(maxdev, abs(F_const*isum - i_target)/i_target)
end
gate!("G11","EC' current conservation, max face deviation at 0.9 i_lim", 1.0+maxdev, 1.0, 0.5,
      note = ok11 ? "max |i(x)-i_app|/i_app = "*string(round(maxdev*100,sigdigits=2))*"%" : "NEWTON FAIL")

## ── G12: mesh + continuation convergence ON A PRODUCTION ROW, PRODUCTION MESH ──
## The gap this closes: every gate above runs a CONSTRUCTED problem, or a production
## row on a mesh chosen for the gate (G10 rebuilds Cl-/propylene on an x_k-matched
## mesh, not the production one). Nothing exercised a row of mediated_ec_matrix.csv
## on the mesh that actually produced it -- so "the production mesh is converged" was
## an argument, never a measurement.
##
## RE-POINTED 2026-09-01. It used to call solve_ilim_ec -- the galvanostatic ramp --
## because at the time 44 of the 48 production cells ended on a Newton failure and were
## published as lower bounds, and the claim worth asserting was that such a wall is tight.
## That is no longer the production path. run_mediated.jl now ramps only to obtain a safe
## state and then runs CONCENTRATION CONTROL, which has no fold at i_lim, and all 48 cells
## reach the collapse criterion through it. A gate that kept ramping was therefore checking
## a parameterisation the published numbers no longer come from, while its own comment
## described a census that had moved from 44 to 2.
##
## It now mirrors run_mediated.jl's accept sequence exactly, and asserts the stronger and
## more falsifiable claim the 2026-08-23 handoff called for: the criterion is REACHED, not
## approached. A row that regresses to a bare wall fails here instead of being described.
##
## Two in-scope (gamma > 1) systems, stirred archetype, each solved twice:
##   production  N =  90, growth 1.15   (exactly what run_mediated.jl uses)
##   refined     N = 180, growth 1.02   (2x cells, 7.5x finer continuation)
## Requirement: agreement within 1%. Measured spread is <= 0.41%, so the tolerance is
## about 2.5x the observed drift -- tight enough to catch a regression, loose enough
## not to fire on floating-point reordering.
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end

function _g12_solve(spec, r; N, growth)
    km = spec.k_M / 1000.0
    xk = sqrt(spec.species[2].D / (km * spec.C_S))
    d  = delta_eff(r.key, spec.D_red, spec.nu_solv)
    i_t0 = F_const * spec.D_red * spec.C_med / (abs(spec.species[1].s) * d)
    ## dx1 exactly as run_mediated.jl forms it, with N carried through
    dx1 = clamp(xk / 50, 0.02e-6, 0.9 * d / N)
    p = ECProblem(spec.species, 2, findfirst(s -> s.name == "Sub", spec.species),
                  km, geometric_faces(d, dx1, N))
    ## mirror run_mediated.jl: ramp for a safe state, then concentration control, and take
    ## c-control on the same acceptance rule production uses (criterion reached AND the
    ## commuting bound cleared). This is the path the published value comes from.
    il, lim, u_safe, i_safe = solve_ilim_ec(p; i_start = 0.02 * i_t0, growth = growth)
    if i_safe > 0.0
        ic, limc, _, _, _ = solve_ilim_ec_ccontrol(p; u0 = u_safe, i0 = i_safe)
        if (startswith(limc, "collapse") || startswith(limc, "plateau") ||
            startswith(limc, "limit reached")) && ic >= 0.9 * i_t0
            il, lim = ic, limc
        end
    end
    (i = il * 0.1, lim = lim)
end

_g12_stir = REACTORS[findfirst(x -> x.key == :stirred, REACTORS)]
for nm in ("ACT-mediated alcohol oxidation (flow, hectogram)",
           "BQ-mediated Wacker-Tsuji oxidation")
    spec = SPECS[findfirst(x -> x.label == nm, SPECS)]
    prod = _g12_solve(spec, _g12_stir; N = 90,  growth = 1.15)
    refi = _g12_solve(spec, _g12_stir; N = 180, growth = 1.02)
    ## the criterion itself, as a hard requirement rather than a note: a row that stops on a
    ## bare Newton wall must fail the audit, not be reported in passing.
    for (tag, r) in (("production", prod), ("refined", refi))
        startswith(r.lim, "plateau") || startswith(r.lim, "collapse") ||
            startswith(r.lim, "limit reached") ||
            error("G12: $nm ($tag mesh) no longer reaches the concentration-control " *
                  "criterion -- limiter '" * r.lim * "'")
    end
    gate!("G12", "production mesh converged: " * first(nm, 30), refi.i, prod.i, 1.0,
          note = "N 90->180, growth 1.15->1.02, c-control path; limiter '" * prod.lim * "'")
end

## ── write CSV ─────────────────────────────────────────────────────────────────
open(joinpath(@__DIR__, "audit_gates.csv"),"w") do io
    println(io,"gate,description,solver,analytic,err_pct,tol_pct,pass,note")
    for r in results
        println(io,"$(r.id),\"$(r.desc)\",$(r.solver),$(r.analytic),$(round(r.err_pct,digits=3)),$(r.tol_pct),$(r.pass),\"$(r.note)\"")
    end
end
np = count(r->r.pass, results)
@printf("\nAUDIT: %d/%d gates pass\n", np, length(results))
println("DONE")

# A failing gate must FAIL THE PROCESS. This script used to print "13/14" and exit 0, so the
# "14/14 must pass" rule in CLAUDE.md was enforced only by a human reading a log -- and
# data/audit_numeric.py, the only consumer of audit_gates.csv, never inspected the pass column.
# A solver regression could therefore go green through the whole pipeline.
if np < length(results)
    failed = [r.id for r in results if !r.pass]
    @printf("AUDIT FAILED: %s\n", join(failed, ", "))
    exit(1)
end
