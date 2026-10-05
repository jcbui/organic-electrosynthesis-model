## Can the ONE unconverged production cell be resolved by continuation in delta?
##
##     cd Section4_Model/julia && julia --project=. probe_hofmann_homotopy.jl
##
## Br-mediated Hofmann x UNSTIRRED (delta = 300 um, x_k = 2.35 um, delta/x_k = 128) is the only
## cell of 48 whose current ramp dies below its own commuting bound -- 0.74 mA cm-2 against a
## Tier-0 floor of 6.95, i.e. not a physical answer at all. Eleven mesh/continuation variants
## (probe_hofmann_unstirred.jl) all die in 0.52-3.01, so the failure is not a mesh-resolution
## problem: ramping the current from a bulk initial guess simply cannot reach the solution
## branch at this delta/x_k.
##
## This tries a different continuation path. The SAME system at delta = 100 um solves fine
## (334.58 mA cm-2). So: start there, walk delta outward in small steps, and at each step
## interpolate the previous converged state onto the new mesh and use it as the Newton guess,
## holding the current at a fixed fraction of the local Tier-0 scale so the target tracks the
## physics rather than sitting still. If the branch survives to delta = 300, ramp the current
## there from the continued state and read off the limit.
include(joinpath(@__DIR__, "npp_ecprime.jl"))
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end

spec  = SPECS[findfirst(x -> x.label == "Br-mediated Hofmann rearrangement", SPECS)]
km    = spec.k_M / 1000.0
xk    = sqrt(spec.species[2].D / (km * spec.C_S))
isub  = findfirst(s -> s.name == "Sub", spec.species)
ired  = findfirst(s -> s.s < 0, spec.species)
d_end = delta_eff(:natural, spec.D_red, spec.nu_solv)
d_beg = delta_eff(:stirred, spec.D_red, spec.nu_solv)

mkp(d, N) = ECProblem(spec.species, 2, isub, km,
                      geometric_faces(d, clamp(xk / 50, 0.02e-6, 0.9 * d / N), N))
tier0(d) = F_const * spec.D_red * spec.C_med / (abs(spec.species[1].s) * d)

"""Interpolate a state from p_old's mesh onto p_new's, in ABSOLUTE x.

The reaction layer sits at a fixed absolute distance from the electrode (x_k = 2.35 um), so
mapping by x/delta would smear it as delta grows. Cells beyond the old domain are filled with
bulk, which is what they physically are."""
function regrid(u_old, p_old, p_new)
    ns = length(p_old.sp)
    u = zeros(nvars(p_new))
    for (jx, x) in enumerate(p_new.xc)
        k = searchsortedfirst(p_old.xc, x)
        for j in 1:ns
            u[lidx(p_new, jx, j)] =
                k == 1                    ? u_old[lidx(p_old, 1, j)] :
                k > length(p_old.xc)      ? log(max(p_old.sp[j].c_bulk, 1e-6)) :
                begin
                    x0, x1 = p_old.xc[k-1], p_old.xc[k]
                    t = (x - x0) / (x1 - x0)
                    (1 - t) * u_old[lidx(p_old, k-1, j)] + t * u_old[lidx(p_old, k, j)]
                end
        end
        u[pidx(p_new, jx)] =
            k == 1               ? u_old[pidx(p_old, 1)] :
            k > length(p_old.xc) ? 0.0 :
            begin
                x0, x1 = p_old.xc[k-1], p_old.xc[k]
                t = (x - x0) / (x1 - x0)
                (1 - t) * u_old[pidx(p_old, k-1)] + t * u_old[pidx(p_old, k)]
            end
    end
    u
end

const N = 90
@printf("delta %.0f -> %.0f um, x_k %.2f um, tier0 at 300 um = %.2f mA/cm2\n\n",
        d_beg*1e6, d_end*1e6, xk*1e6, tier0(d_end)*0.1)

## ── step 1: establish the branch at delta = 100 um by the ordinary ramp ────────
p = mkp(d_beg, N)
il0, lim0, _, _ = solve_ilim_ec(p; i_start = 0.02 * tier0(d_beg), growth = 1.15)
@printf("anchor at delta = %.0f um: i_lim %.2f mA/cm2  (%s)\n", d_beg*1e6, il0*0.1, lim0)

## Re-solve at a safe fraction of that limit and KEEP the state to continue from.
frac = 0.85
u = zeros(nvars(p))
for ix in 1:nnode(p), j in 1:length(p.sp)
    u[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-6))
end
i_here = 0.02 * tier0(d_beg)
while i_here < frac * il0
    newton_ec!(u, p, i_here; max_iter = 120, max_log_step = 3.0) || error("anchor ramp died")
    global i_here = min(i_here * 1.15, frac * il0)
end
newton_ec!(u, p, i_here; max_iter = 120, max_log_step = 3.0) || error("anchor solve died")
@printf("continuing from i = %.2f mA/cm2 (%.0f%% of the anchor limit)\n\n", i_here*0.1, 100frac)

## ── step 2: walk delta outward, holding i at the same fraction of local Tier-0 ─
nsteps = 24
@printf("%8s %10s %10s %10s  %s\n", "delta um", "i mA/cm2", "c_red/cb", "c_sub/cb", "status")
ok = true
for s in 1:nsteps
    d_new = d_beg * (d_end / d_beg)^(s / nsteps)
    p_new = mkp(d_new, N)
    u_new = regrid(u, p, p_new)
    i_new = i_here * (tier0(d_new) / tier0(d_beg * (d_end / d_beg)^((s-1) / nsteps)))
    i_new = i_here * (d_beg * (d_end/d_beg)^((s-1)/nsteps)) / d_new     # 1/delta scaling
    if !newton_ec!(u_new, p_new, i_new; max_iter = 200, max_log_step = 2.0)
        @printf("%8.1f %10.2f %10s %10s  CONTINUATION DIED\n", d_new*1e6, i_new*0.1, "-", "-")
        global ok = false
        break
    end
    global p, u, i_here = p_new, u_new, i_new
    if s % 4 == 0 || s == nsteps
        @printf("%8.1f %10.2f %10.2e %10.2e  ok\n", d_new*1e6, i_new*0.1,
                exp(u[lidx(p,1,ired)])/p.sp[ired].c_bulk,
                exp(u[lidx(p,1,isub)])/p.sp[isub].c_bulk)
    end
    flush(stdout)
end

## ── step 3: at delta = 300, push the current up from the continued state ───────
## Step 3: bisect onto the turning point, then repeat the ENTIRE continuation on a doubled
## mesh and bisect again. A value reached by continuation is only worth putting into production
## if it is mesh-independent, and this is the check that decides it.
function ramp_to_wall(p, u_start, i_start; grow = 1.10, nbis = 10)
    u_ok = copy(u_start); i_ok = i_start; ia = i_start * grow
    while ia < i_start * 50
        v = copy(u_ok)
        newton_ec!(v, p, ia; max_iter = 200, max_log_step = 2.0) || break
        i_ok = ia; u_ok .= v
        ia *= grow
    end
    lo, hi = i_ok, ia
    for _ in 1:nbis
        mid = 0.5 * (lo + hi); v = copy(u_ok)
        newton_ec!(v, p, mid; max_iter = 200, max_log_step = 2.0) ? (lo = mid; u_ok .= v) : (hi = mid)
    end
    (i = lo, u = u_ok)
end

"""Full delta-continuation from the stirred anchor out to `d_end`, at mesh size N."""
function continue_to_end(N)
    p0 = mkp(d_beg, N)
    u0 = zeros(nvars(p0))
    for ix in 1:nnode(p0), j in 1:length(p0.sp)
        u0[lidx(p0, ix, j)] = log(max(p0.sp[j].c_bulk, 1e-6))
    end
    il, _, _, _ = solve_ilim_ec(p0; i_start = 0.02 * tier0(d_beg), growth = 1.15)
    ih = 0.02 * tier0(d_beg)
    while ih < frac * il
        newton_ec!(u0, p0, ih; max_iter = 120, max_log_step = 3.0) || return nothing
        ih = min(ih * 1.15, frac * il)
    end
    newton_ec!(u0, p0, ih; max_iter = 120, max_log_step = 3.0) || return nothing
    pc, uc, ic = p0, u0, ih
    for s in 1:nsteps
        dn = d_beg * (d_end / d_beg)^(s / nsteps)
        pn = mkp(dn, N); un = regrid(uc, pc, pn)
        inew = ic * (d_beg * (d_end / d_beg)^((s - 1) / nsteps)) / dn
        newton_ec!(un, pn, inew; max_iter = 200, max_log_step = 2.0) || return nothing
        pc, uc, ic = pn, un, inew
    end
    (p = pc, u = uc, i = ic, anchor = il)
end

if ok
    println("\nbisecting onto the turning point at delta = 300 um\n")
    ired2 = findfirst(x -> x.s < 0, p.sp)
    csub_sc = spec.n_S * F_const * spec.D_S * spec.C_S
    a = ramp_to_wall(p, u, i_here)
    @printf("  N=90   i_lim = %.2f mA/cm2   c_red/cb %.3f  c_sub/cb %.2e  x_f/delta %.3f\n",
            a.i*0.1, exp(a.u[lidx(p,1,ired2)])/p.sp[ired2].c_bulk,
            exp(a.u[lidx(p,1,isub)])/p.sp[isub].c_bulk, 1.0 - csub_sc/(a.i*d_end))
    flush(stdout)
    r2 = continue_to_end(180)
    if r2 === nothing
        println("  N=180 continuation did not survive -- the value is NOT mesh-independent")
    else
        b = ramp_to_wall(r2.p, r2.u, r2.i)
        @printf("  N=180  i_lim = %.2f mA/cm2   (drift vs N=90: %+.2f%%)\n",
                b.i*0.1, (b.i/a.i - 1)*100)
    end
    @printf("\n  for comparison: tier0 floor %.2f (what the pipeline currently SHIPS for this cell),\n",
            tier0(d_end)*0.1)
    @printf("                  substrate-supply scale %.2f, Saveant plateau %.1f mA/cm2\n",
            csub_sc/d_end*0.1,
            spec.n_c*F_const*spec.C_med*sqrt(spec.species[2].D*km*spec.C_S)*0.1)
    @printf("  clears 25? %s    clears 50? %s\n", a.i*0.1 >= 25, a.i*0.1 >= 50)
end
