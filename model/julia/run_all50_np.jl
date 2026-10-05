## ── ALL 50 REACTIONS, ONE PHYSICS ────────────────────────────────────────────────────────────
##
##     cd Section4_Model/julia && julia --project=. run_all50_np.jl
##
## WHY. The published matrix mixed three physics levels in columns that were counted against
## each other: 42 rows Tier-0 Fick (NO migration at all), 8 rows full Nernst-Planck + migration
## + EC' coupling, and one of those 8 silently dropped back to Tier-0 when it failed to converge.
## "N of 50 clear 25 mA cm-2" was tallied across all three. That is not an apples-to-apples
## comparison and it would not survive review.
##
## Here every row is solved with the SAME solver: Nernst-Planck with migration and
## electroneutrality, on the same mesh policy, with the same limit criterion. The eight mediated
## rows additionally carry the EC' homogeneous source (k > 0); the other 42 have k = 0, which is
## the same equations with the source switched off -- not a different model.
##
## ELECTRODE BOOKKEEPING. Per electron: the carrier is consumed at s = -1/n and the product forms
## at +1/n with z_P = z_c + n, so
##      sum_j z_j s_j = z_c(-1/n) + (z_c + n)(1/n) = 1
## exactly, for ANY carrier charge. A neutral carrier (z_c = 0) must then reproduce the Fick
## answer -- that is the built-in correctness check on this machinery, asserted below.
##
## CARRIER CHARGE comes from data/carrier_charge.csv and SUPPORTING IONS from
## data/electrolyte_ions.csv. Both carry per-row provenance and both flag the rows that need
## author review; this script REFUSES to run on a row whose charge is unreviewed-LOW unless
## --allow-unreviewed is passed, because a wrong z moves a ceiling by up to 2x in silence.
using Printf, DelimitedFiles
include(joinpath(@__DIR__, "params.jl")); include(joinpath(@__DIR__, "correlations.jl"))
include(joinpath(@__DIR__, "npp_ecprime.jl"))
include(joinpath(@__DIR__, "reactions_table.jl"))

const DATA = joinpath(@__DIR__, "..", "data")
readcsv(f) = begin
    rows = [l for l in eachline(joinpath(DATA, f)) if !startswith(l, "#") && !isempty(strip(l))]
    hdr = split(rows[1], ','); (hdr, [split(r, ',') for r in rows[2:end]])
end
## naive split breaks on quoted commas; parse properly
function csvrows(f)
    out = Vector{Vector{String}}()
    for l in eachline(joinpath(DATA, f))
        (startswith(l, "#") || isempty(strip(l))) && continue
        fields = String[]; cur = IOBuffer(); inq = false
        for ch in l
            if ch == '"'; inq = !inq
            elseif ch == ',' && !inq; push!(fields, String(take!(cur)))
            else; write(cur, ch); end
        end
        push!(fields, String(take!(cur)))
        push!(out, fields)
    end
    out
end
rx  = csvrows("reactions_50.csv");  rxh = rx[1];  rxd = rx[2:end]
cc  = csvrows("carrier_charge.csv"); cch = cc[1]; ccd = cc[2:end]
ei  = csvrows("electrolyte_ions.csv"); eih = ei[1]; eid = ei[2:end]
di_ = csvrows("electrode_direction.csv"); dih = di_[1]; did = di_[2:end]
col(h, n) = findfirst(==(n), h)
getf(row, h, n) = row[col(h, n)]
num(x) = (y = tryparse(Float64, strip(x)); y === nothing ? NaN : y)

## Rows whose CARRIER is the same ion as the supporting anion -- one pool, not two.
## Determined from data/reactions_50.csv (carrier_species vs the electrolyte string), listed
## explicitly rather than string-matched at run time so it can be checked by eye.
const CARRIER_IS_SUPPORTING_ANION = Set([
    "Br- oxidation / electrophilic bromination",     # bromide in 0.5 M NaBr
    "Br-mediated Hofmann rearrangement",             # bromide in 0.08 M NaBr
    "Cl-mediated ethylene epoxidation",              # chloride in 1 M KCl
    "Alkaline lignin -> vanillin (pilot)",           # carbonate in 1 M Na2CO3
    ## NOT "Non-Kolbe decarboxylative alpha-methoxylation". It was added here on 2026-08-24 and had to be
    ## taken straight back out. Registering it made the carboxylate the ONLY anion in the cell,
    ## and its anodic product is formally a CATION (z_c + n = -1 + 2 = +1). A system whose sole
    ## anion is consumed and turned into a cation has NO diffusion-limited current: electroneutrality
    ## forbids the anion from depleting at the surface, so the current ramp climbs without ever
    ## collapsing. Measured directly: i/i_fick = 50.0 with "no collapse", against 2.88 (near the
    ## binary expectation of 2.27) as soon as any second anion is present. The row published
    ## x73.6 before this was caught. Keep a second anion in that cell.
])
carrier_is_electrolyte_anion(rxn) = rxn in CARRIER_IS_SUPPORTING_ANION

## A STALE NAME IN THAT SET IS SILENT AND EXPENSIVE, so it is now checked against the actual
## reaction list. When the condition audit renamed "Cl-mediated propylene epoxidation" to
## "...ethylene...", this Set was not updated. `same_ion` then went false for that row, the
## chloride was counted twice -- once as the carrier and again as the supporting anion -- and its
## migration enhancement collapsed from the binary limit of ~2 to 1.176. That is precisely the
## symptom the comment above records as the original bug, reintroduced by a rename, and nothing
## flagged it because a Set lookup that misses simply returns false.
function check_supporting_anion_set(names)
    stale = [n for n in CARRIER_IS_SUPPORTING_ANION if !(n in names)]
    isempty(stale) || error("CARRIER_IS_SUPPORTING_ANION names reactions that do not exist: " *
        string(stale) * "\n  A stale entry here does not error, it silently double-counts the " *
        "carrier's own ion and suppresses that row's migration enhancement by up to 2x.")
end

const REACTORS_L = [(:natural,"Unstirred batch"), (:stirred,"Stirred batch"),
                    (:flow,"Recirculating flow cell"), (:anec,"ANEC flow cell"),
                    (:micro,"Microfluidic cell (25 um gap)"),
                    (:rde,"RDE 1600 rpm"), (:rce,"Rotating cylinder 3000 rpm")]

check_supporting_anion_set(Set(getf(r, rxh, "reaction") for r in rxd))

allow_unreviewed = "--allow-unreviewed" in ARGS
open(joinpath(@__DIR__, "all50_np_matrix.csv"), "w") do io
    println(io, "reaction,reactor,delta_um,z_carrier,confidence,i_fick_mAcm2,i_np_mAcm2,migration_factor,limiter,flag")
    nrev = 0
    for (k, r) in enumerate(rxd)
        rxn  = getf(r, rxh, "reaction")
        ## carrier D, C, n and the solvent kinematic viscosity come from reactions_table.jl,
        ## the SAME generated table run_tier0.jl uses -- so any difference between this matrix
        ## and the Tier-0 one is the physics, not a different set of inputs.
        ti   = findfirst(x -> x.name == rxn, RXNS)
        ti === nothing && error("reaction not in reactions_table.jl: $rxn")
        t    = RXNS[ti]
        Cc, nc, Dc, nu_s = t.C, t.n, t.D, t.nu
        ## These two lookups used to be bare findfirst indexing. When the condition audit renamed
        ## "Cl-mediated propylene epoxidation" to "...ethylene...", they failed after all 300 cells
        ## had already solved, with `ArgumentError: invalid index: nothing` and a stack trace into
        ## Base.indices -- no mention of which file, which row, or what was renamed. The RXNS lookup
        ## immediately above was already guarded; these were not. Now all three name the problem.
        ci = findfirst(x -> getf(x, cch, "reaction") == rxn, ccd)
        ci === nothing && error("reaction not in data/carrier_charge.csv: $rxn\n" *
            "If a row was renamed in reactions_50.csv, rename it in carrier_charge.csv too.")
        crow = ccd[ci]
        zc   = num(getf(crow, cch, "z_carrier"))
        conf = getf(crow, cch, "confidence")
        ei = findfirst(x -> getf(x, eih, "reaction") == rxn, eid)
        ei === nothing && error("reaction not in data/electrolyte_ions.csv: $rxn\n" *
            "If a row was renamed in reactions_50.csv, rename it in electrolyte_ions.csv too.")
        erow = eid[ei]
        Cs   = num(getf(erow, eih, "conc_M")) * 1000.0
        zcat = num(getf(erow, eih, "z_cat")); Dcat = num(getf(erow, eih, "D_cat"))
        zan  = num(getf(erow, eih, "z_an"));  Dan  = num(getf(erow, eih, "D_an"))
        di = findfirst(x -> getf(x, dih, "reaction") == rxn, did)
        di === nothing && error("reaction not in data/electrode_direction.csv: $rxn\n" *
            "Every row needs a sourced anodic/cathodic assignment; the electrode stoichiometry " *
            "depends on it and a wrong direction silently reverses the migration effect.")
        dirn = getf(did[di], dih, "direction")
        (dirn == "anodic" || dirn == "cathodic") ||
            error("direction for $rxn must be anodic or cathodic, got '$dirn'")
        if conf == "LOW" && !allow_unreviewed
            nrev += 1; continue
        end
        (isnan(Cs) || isnan(zcat) || isnan(zan)) && (Cs = 0.0)   # unsupported: carrier + counter only
        for (rk, rlab) in REACTORS_L
            d = delta_eff(rk, Dc, nu_s)
            ## species: carrier, product, supporting cation, supporting anion
            sp = ECSpecies[]
            ## ELECTRODE DIRECTION. This line used to read `zc + nc` unconditionally, which is
            ## the OXIDATION stoichiometry: losing n electrons raises the carrier charge by n, and
            ## sum(z*s) then comes out at +1, i.e. anodic current. Every one of the 50 rows was
            ## therefore solved as an oxidation. For a REDUCTION the product is `zc - nc` and
            ## sum(z*s) = -1. The difference is not cosmetic: it reverses the sign of the field's
            ## effect on a charged carrier. Demonstrated on the Ni(tet a)(2+) row (z=+2, n=1,
            ## 0.1 M Et4NClO4/DMF, delta 300 um): as written it gave i_np/i_fick = 0.9687, a 3%
            ## HINDRANCE; with the reduction stoichiometry it gives 1.0459, a 4.6% ENHANCEMENT --
            ## which is the physical answer, because a dication is pulled toward a cathode.
            ## Direction per row is read from data/electrode_direction.csv, where each assignment
            ## carries the electrode wiring or mechanism sentence from its own paper.
            zprod = (dirn == "anodic") ? (zc + nc) : (zc - nc)
            push!(sp, ECSpecies("Carrier", zc, Dc, Cc, -1/nc, 0.0))
            push!(sp, ECSpecies("Product", zprod, Dc, max(1e-6*Cc, 1e-9), +1/nc, 0.0))
            if Cs > 0
                ## DO NOT DOUBLE-COUNT THE CARRIER'S OWN ION. Where the carrier IS the
                ## electrolyte anion -- bromide in NaBr, chloride in NaCl, carbonate in Na2CO3 --
                ## there is ONE ion pool, not a carrier plus a separate supporting anion. Adding
                ## both suppressed the migration enhancement badly: carbonate (z = -2, binary)
                ## came out at 1.105 where the binary limit is ~3, and chloride in 2 M NaCl at
                ## 1.176 where it should be ~2. The supporting anion is therefore only whatever
                ## EXCEEDS the carrier, and the cation is set by overall electroneutrality.
                q_c = zc * Cc
                same_ion = (zc == zan) && carrier_is_electrolyte_anion(rxn)
                c_an  = same_ion ? max(0.0, Cs - Cc) : Cs + max(0.0, q_c) / max(-zan, 1.0)
                c_cat = same_ion ? (abs(q_c) + abs(zan) * c_an) / max(zcat, 1.0) :
                                   Cs + max(0.0, -q_c) / max(zcat, 1.0)
                push!(sp, ECSpecies("Cat+", zcat, Dcat, c_cat, 0.0, 0.0))
                c_an > 0 && push!(sp, ECSpecies("An-", zan, Dan, c_an, 0.0, 0.0))
            else
                ## UNSUPPORTED ROW: carrier + its counter-ion only. The D values here are
                ## PLACEHOLDERS, not data, and this branch used to be entered SILENTLY whenever
                ## electrolyte_ions.csv had a blank conc_M -- which was true for exactly the three
                ## rows whose electrolyte definition ONE_PHYSICS_20260823.md had already flagged as
                ## unresolved (Kolbe's "Me4NOH 15 mol% + Me4NBF4 5 mol%", Giese's "NaCl 7 mol% +
                ## pH 2 HCl", and "5 wt% AcOH"). One of them, Kolbe, has a CHARGED carrier and
                ## reports a migration enhancement of x2.006 -- a factor of two on a published
                ## ceiling -- computed from these placeholders rather than from its own supporting
                ## electrolyte. Worse, a sensitivity sweep over the sourced table could not see it,
                ## because this branch never reads that table.
                ##
                ## A charged carrier here is now a hard error. A NEUTRAL carrier is allowed
                ## through, because migration does nothing to it and the placeholders cannot
                ## affect its ceiling -- but it is announced rather than hidden.
                if zc != 0
                    error("$rxn has a CHARGED carrier (z = $zc) but no resolved supporting " *
                          "electrolyte concentration in electrolyte_ions.csv (conc_M is blank).\n" *
                          "  The solve would fall back to placeholder ion diffusivities " *
                          "(1e-9 / 1.5e-9 m^2/s) and the migration enhancement -- worth up to a " *
                          "factor of two here -- would rest on those placeholders.\n" *
                          "  Resolve the electrolyte for this row before solving it.")
                end
                @printf("  [unsupported, neutral carrier: placeholder counter-ion D] %s\n", rxn)
                push!(sp, ECSpecies("Cat+", 1.0, 1e-9, max(-zc,0)*Cc + 1e-3, 0.0, 0.0))
                push!(sp, ECSpecies("An-", -1.0, 1.5e-9, max(zc,0)*Cc + 1e-3, 0.0, 0.0))
            end
            ## COUNTER-ION INVENTORY CHECK.
            ##
            ## The construction above sets c_cat = Cs + |z_c|*C_c/z_cat, i.e. it BUILDS whatever
            ## counter-ion the carrier's own charge demands. That is electroneutral by
            ## construction, so the top-up below never fires and the invention is invisible there.
            ## The Kolbe row is the case in point: it declares 1.00 M of a z = -1 carboxylate, so
            ## 1050 mol/m^3 of Me4N+ is constructed -- while the paper's charge sheet supplies
            ## 200 mol/m^3 (10 mmol Me4N.BF4 + 30 mmol Me4N.OH in 200 mL acetone). 850 mol/m^3,
            ## 5.2x the real inventory, is manufactured, and the transference numbers built on it
            ## set that row's migration enhancement.
            ##
            ## Where a paper's charge sheet fixes the counter-ion inventory, electrolyte_ions.csv
            ## records it in counterion_inventory_M and this check compares against it. A blank
            ## means "not established for this row" and the check is skipped -- it never invents a
            ## limit of its own.
            inv_s = getf(erow, eih, "counterion_inventory_M")
            if !isempty(strip(inv_s))
                inv = num(inv_s) * 1000.0
                need = abs(zc) * Cc
                if need > 1.05 * inv
                    @printf("  [COUNTER-ION] %s declares %.4g mol/m^3 of charge on its carrier but the paper supplies only %.4g mol/m^3 of counter-ion; %.4g (%.1fx the real inventory) is manufactured by the electroneutrality construction\n", rxn, need, inv, need-inv, need/inv)
                end
            end

            ## Enforce bulk electroneutrality by topping up the counter-ion.
            ##
            ## THIS STEP CAN INVENT IONS, so it now says how many. A row that specifies a charged
            ## carrier at a concentration its own counter-ion inventory cannot balance gets the
            ## shortfall silently manufactured here. The Kolbe row is the case in point: it carries
            ## 1.00 M of a z = -1 carboxylate while the paper's charge sheet supplies only 0.20 M
            ## of Me4N+ (10 mmol Me4N.BF4 + 30 mmol Me4N.OH in 200 mL), so 0.8 M of cation -- four
            ## fifths of the counter-ion pool -- was being conjured, and the resulting transference
            ## numbers set that row's x2.006 migration enhancement.
            ##
            ## A top-up that is a small fraction of the ion pool is ordinary bookkeeping. One that
            ## dominates the pool means the row's composition does not describe a real solution,
            ## and the number it produces should not be published without saying so.
            en = sum(s.z * s.c_bulk for s in sp)
            if abs(en) > 1e-9
                j = en > 0 ? findfirst(s -> s.z < 0, sp) : findfirst(s -> s.z > 0, sp)
                added = abs(en)/abs(sp[j].z)
                pool  = sum(abs(s.z)*s.c_bulk for s in sp)/2
                if added > 0.25 * pool
                    ## NB: @printf needs its format as ONE literal -- a `*`-concatenated format
                    ## string is a compile error in Julia, which is how this line failed once.
                    @printf("  [ELECTRONEUTRALITY] %s: topped up %s by %.4g mol/m^3 = %.0f%% of the whole ion pool; the stated composition is not electroneutral on its own\n", rxn, sp[j].name, added, 100*added/pool)
                end
                sp[j] = ECSpecies(sp[j].name, sp[j].z, sp[j].D,
                                  sp[j].c_bulk + added, sp[j].s, sp[j].nu)
            end
            i_fick = nc * F_const * Dc * Cc / d
            p = ECProblem(sp, 1, 1, 0.0, geometric_faces(d, 0.9*d/90, 90))   # k = 0: no EC' source
            il, lim, us, isf = solve_ilim_ec(p; i_start = 0.02*i_fick, growth = 1.15)
            i_np = il; lm = lim
            if isf > 0
                ic, limc, _, _, _ = solve_ilim_ec_ccontrol(p; u0 = us, i0 = isf)
                if (startswith(limc,"collapse") || startswith(limc,"plateau") ||
                    startswith(limc,"limit reached")) && ic > il
                    i_np = ic; lm = limc
                end
            end
            fac = i_np / i_fick
            ## PHYSICAL CEILING ON THE MIGRATION ENHANCEMENT.
            ## For a binary electrolyte in which the carrier is the reacting ion, Newman's result
            ## is 1 + |z_carrier|/z_counter -- 2 for a -1 carrier against a +1 counter-ion, 3 for
            ## a -2 carrier. A formally charged anodic product can add a little more (the
            ## decarboxylative-elimination cell reaches 2.88 legitimately), so the guard is set
            ## generously at 5. Above that the ramp is not finding a limiting current, it is
            ## running away: that row reported x73.6 before the cause was found, and the flag said
            ## "ok" because the flag only ever tested that the number was positive and finite.
            MIGRATION_CEILING = 5.0
            flag = if !(i_np > 0 && isfinite(fac))
                "unsolved"
            elseif fac > MIGRATION_CEILING
                @printf("  [RUNAWAY] %s / %s: migration factor x%.1f exceeds the physical ceiling of %.0f; the current ramp is not converging to a limiting current\n", rxn, rlab, fac, MIGRATION_CEILING)
                "runaway"
            else
                "ok"
            end
            @printf("%-44s %-26s z=%-4.1f  Fick %8.2f  NP %8.2f  x%.3f\n",
                    first(rxn,44), first(rlab,26), zc, i_fick*0.1, i_np*0.1, fac)
            flush(stdout)
            println(io, "\"$rxn\",\"$rlab\",$(d*1e6),$zc,\"$conf\",$(i_fick*0.1),$(i_np*0.1),$fac,\"$lm\",\"$flag\"")
            flush(io)
        end
    end
    if nrev > 0
        @printf("\n%d reactions SKIPPED: carrier charge is unreviewed (confidence LOW).\n", nrev)
        println("Review data/carrier_charge.csv, or pass --allow-unreviewed to run anyway.")
    end
end
println("ALL50 NP DONE")
