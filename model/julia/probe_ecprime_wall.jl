## Diagnostic: is the EC' "Newton wall" a physical turning point or a solver artifact?
##
##     cd Section4_Model/julia && julia --project=. probe_ecprime_wall.jl
##
## HISTORICAL DIAGNOSTIC, kept for the record. When it was written, 44 of the 48 production EC'
## cells ended their current ramp on a Newton failure rather than on the c_red/c_bulk < 1e-3
## collapse criterion, and were reported as strict LOWER BOUNDS; whether that bound was tight
## was unmeasured. That is no longer the production path -- run_mediated.jl ramps only to a safe
## state and then uses concentration control, and all 48 cells now REACH the criterion (gate G12
## in run_audit.jl asserts it). This probe measures the wall the retired ramp hit; nothing
## published depends on it. The decisive test is the SURFACE STATE at
## the wall: if c_red/c_bulk is already near 1e-3 the ramp stalled essentially at the limiting
## current and the bound is tight; if it is O(1) the ramp died far from any physical limit and
## the reported i_ec is a loose bound that understates the ceiling.
##
## Reports, per system, the wall current, the surface state there, and how both move under a
## finer continuation (growth 1.15 -> 1.02) and a finer mesh (N 90 -> 180). A wall that is
## physical does not move; one that is numerical does.
include(joinpath(@__DIR__, "npp_ecprime.jl"))

## Reuse the production spec definitions verbatim rather than restating them -- a probe that
## retypes its inputs measures the retyping, not the model.
let src = read(joinpath(@__DIR__, "run_mediated.jl"), String)
    cut = findfirst("## ── invariant checks", src)
    @eval Main $(Meta.parse("begin\n" * src[1:cut[1]-1] * "\nend"))
end

function probe(spec, r; N = 90, growth = 1.15, nbis = 6)
    km = spec.k_M / 1000.0
    xk = sqrt(spec.species[2].D / (km * spec.C_S))
    d  = delta_eff(r.key, spec.D_red, spec.nu_solv)
    i_t0 = F_const * spec.D_red * spec.C_med / (abs(spec.species[1].s) * d)
    dx1 = clamp(xk / 50, 0.02e-6, 0.9 * d / N)
    p = ECProblem(spec.species, 2, findfirst(s -> s.name == "Sub", spec.species),
                  km, geometric_faces(d, dx1, N))
    ired = findfirst(s -> s.s < 0, p.sp)
    ns = length(p.sp); Nn = nnode(p)
    u = zeros(nvars(p))
    for ix in 1:Nn, j in 1:ns
        u[lidx(p, ix, j)] = log(max(p.sp[j].c_bulk, 1e-6))
    end
    ia = 0.02 * i_t0; i_ok = 0.0; u_ok = copy(u); why = "ramp-exhausted"
    while ia < 0.02 * i_t0 * 1e5
        newton_ec!(u, p, ia; max_iter = 120, max_log_step = 3.0) || (why = "newton-fail"; break)
        i_ok = ia; u_ok .= u
        (exp(u[lidx(p, 1, ired)]) / p.sp[ired].c_bulk < 1e-3) && (why = "COLLAPSE"; break)
        ia *= growth
    end
    lo, hi = i_ok, ia
    for _ in 1:nbis
        mid = 0.5 * (lo + hi); v = copy(u_ok)
        newton_ec!(v, p, mid; max_iter = 120, max_log_step = 3.0) ? (lo = mid; u_ok .= v) : (hi = mid)
    end
    (i = lo * 0.1,
     cred = exp(u_ok[lidx(p, 1, ired)]) / p.sp[ired].c_bulk,
     csub = exp(u_ok[lidx(p, 1, p.isub)]) / p.sp[p.isub].c_bulk,
     why = why, t0 = i_t0 * 0.1)
end

for rk in (:stirred,)
    R = REACTORS[findfirst(x -> x.key == rk, REACTORS)]
    println("\n=== reactor: $(R.label) ===")
    @printf("%-42s %9s %10s %9s %8s  %-14s %9s %9s\n",
            "system", "i_ec", "c_red/cb", "c_sub/cb", "i/i_t0", "ended on",
            "g=1.02", "N=180")
    for spec in SPECS
        a = probe(spec, R)
        b = probe(spec, R; growth = 1.02)
        c = probe(spec, R; N = 180)
        @printf("%-42s %9.2f %10.2e %9.2e %8.2f  %-14s %9.2f %9.2f\n",
                first(spec.label, 42), a.i, a.cred, a.csub, a.i / a.t0, a.why, b.i, c.i)
        flush(stdout)
    end
end
