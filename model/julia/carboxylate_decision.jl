## Decision brief for the two rows whose anionic carrier is created by a LIMITED BASE.
##   julia carboxylate_decision.jl
##
## Both rows declare more carrier charge than their electrolyte can balance (Kolbe 5.0x,
## decarboxylative elimination 13.3x). Three readings are defensible and they differ by up to
## an order of magnitude. This solves each one exactly, at every architecture, so the choice is
## made on numbers rather than on argument.
##
##   (1) carrier = the carboxylate actually present, set by the base charged. Electroneutral.
##   (2) carrier = the neutral acid, z = 0. No migration; the full inventory is transported.
##   (3) as published: the full acid inventory carrying z = -1. NOT electroneutral -- the solver
##       manufactures the missing counter-ion -- and shown only for comparison.
D=@__DIR__
include(joinpath(D,"params.jl")); include(joinpath(D,"correlations.jl")); include(joinpath(D,"npp_ecprime.jl"))
include(joinpath(D,"reactions_table.jl"))

const CASES = [
 (name="Kolbe homocoupling of 10-undecenoate", n=1.0,
  C_full=1000.0, C_base=150.0, Csupp=50.0, Dcat=2.935e-9, Dan=1.5e-9, zan=-1.0),
 (name="Non-Kolbe decarboxylative alpha-methoxylation", n=2.0,
  C_full=100.0, C_base=7.5, Csupp=7.5, Dcat=1.0e-9, Dan=1.269e-9, zan=-1.0),
]
const REACT = [(:natural,"Unstirred"),(:stirred,"Stirred"),(:flow,"Flow 1mm"),
               (:anec,"ANEC"),(:micro,"Micro"),(:rde,"RDE"),(:rce,"RCE")]

function solve_case(t, C, z, n, Csupp, Dcat, Dan, zan, d)
    sp = ECSpecies[]
    push!(sp, ECSpecies("Carrier", z, t.D, C, -1/n, 0.0))
    push!(sp, ECSpecies("Product", z+n, t.D, max(1e-6*C,1e-9), +1/n, 0.0))
    q = z*C
    push!(sp, ECSpecies("Cat+", 1.0, Dcat, Csupp + max(0.0,-q), 0.0, 0.0))
    push!(sp, ECSpecies("An-", zan, Dan, Csupp + max(0.0,q), 0.0, 0.0))
    en = sum(s.z*s.c_bulk for s in sp)
    if abs(en) > 1e-9
        j = en > 0 ? findfirst(s->s.z<0, sp) : findfirst(s->s.z>0, sp)
        sp[j] = ECSpecies(sp[j].name, sp[j].z, sp[j].D, sp[j].c_bulk + abs(en)/abs(sp[j].z), sp[j].s, sp[j].nu)
    end
    i_f = n*F_const*t.D*C/d
    p = ECProblem(sp, 1, 1, 0.0, geometric_faces(d, 0.9*d/90, 90))
    il, lim, _, _ = solve_ilim_ec(p; i_start=0.02*i_f, growth=1.15)
    (il*0.1, il/i_f, lim)
end

for c in CASES
    ti = findfirst(x -> x.name == c.name, RXNS)
    ti === nothing && (println("skip: ", c.name); continue)
    t = RXNS[ti]
    println("="^104); println(c.name)
    @printf("%-11s | %-24s | %-24s | %-24s\n","arch",
            "(1) carboxylate only", "(2) neutral acid, z=0", "(3) as published")
    for (k,lab) in REACT
        d = delta_eff(k, t.D, t.nu)
        a = solve_case(t, c.C_base, -1.0, c.n, c.Csupp, c.Dcat, c.Dan, c.zan, d)
        b = solve_case(t, c.C_full,  0.0, c.n, c.Csupp, c.Dcat, c.Dan, c.zan, d)
        e = solve_case(t, c.C_full, -1.0, c.n, c.Csupp, c.Dcat, c.Dan, c.zan, d)
        @printf("%-11s | %9.1f (x%.2f) %s | %9.1f (x%.2f) %s | %9.1f (x%.2f) %s\n", lab,
                a[1],a[2], a[1]>=25 ? ">=25" : " <25",
                b[1],b[2], b[1]>=25 ? ">=25" : " <25",
                e[1],e[2], e[1]>=25 ? ">=25" : " <25")
    end
    println()
end
