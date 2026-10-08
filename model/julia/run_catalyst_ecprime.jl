## run_catalyst_ecprime.jl -- the eleven molecular-catalyst rows solved as EC' problems over a
## DECLARED rate-constant band (author instruction, 2026-09-09: "run the eleven catalyst rows
## through the EC' solver over a declared k band as a state-C sensitivity ... and report whether
## 10-of-11 survives").
##
## WHY THIS EXISTS. The published matrix runs every catalyst row at k = 0 (run_all50_np.jl): the
## catalyst is turned over at the electrode, leaves, and is credited with NO regeneration inside
## the film, so its ceiling is nF D C_cat/delta -- the carrier's own transport bound. That is the
## FLOOR of the EC' current (the homogeneous source only adds flux; i_ec >= i_t0 is the one
## rigorous inequality in this model), so "10 of 11 catalyst rows clear 25 mA cm-2 in no
## architecture" is a statement about k = 0, not about transport. This script measures what a
## finite k does to it.
##
## HOW. For each catalyst row the species set is built EXACTLY as run_all50_np.jl builds it
## (carrier, electrogenerated product, supporting ions, electroneutrality top-up -- that code is
## copied, not re-derived), then two species are appended:
##   Sub   the substrate, neutral, at the page-verified C_sub; nu = -n_c/n_S per homogeneous event
##   Xion  the charge-balancing product of the homogeneous step (halide for a cathodic row, H+ for
##         an anodic one), z = -/+1, nu = n_c, trace in the bulk. Its D is the supporting ion's of
##         the same sign -- a DECLARED simplification; it is a spectator that carries charge.
## and the homogeneous step Active + (n_c/n_S) Sub -> Resting + products is switched on with k.
## sum z*nu = 0 and sum z*s = +/-1 hold by construction and are asserted.
##
## DECLARED (state C) inputs, each with its band:
##   k    in {0, 1, 10, 100, 1e3, 1e4} M^-1 s^-1 -- the band the eight mediated rows carry
##        (0.5 to 1e3) plus one decade above. No literature k is claimed for any catalyst.
##   D_S  = 1.0e-9 m^2/s x (0.369 mPa s / mu_solvent): a typical small-organic diffusivity in
##        acetonitrile, scaled 1/mu to the row's solvent (Stokes-Einstein / Wilke-Chang scaling).
##        It enters only through the substrate cap n_S F D_S C_S/delta and the reaction layer;
##        the output records whether each cell sits at that cap, which is where D_S matters.
## The k = 0 member of every sweep is the CONTROL: it must reproduce the published
## all50_np_matrix.csv cell (same solver, same species plus two spectators).
##
##   cd julia && nohup julia run_catalyst_ecprime.jl > /abs/path/log 2>&1 &
## Writes catalyst_ec_sweep.csv beside itself. Touches no other artifact.
using Printf
include(joinpath(@__DIR__, "params.jl")); include(joinpath(@__DIR__, "correlations.jl"))
include(joinpath(@__DIR__, "npp_ecprime.jl"))
include(joinpath(@__DIR__, "reactions_table.jl"))

const DATA = joinpath(@__DIR__, "..", "data")
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

const CARRIER_IS_SUPPORTING_ANION = Set([
    "Br- oxidation / electrophilic bromination", "Br-mediated Hofmann rearrangement",
    "Amidyl-radical C-H amination (phenanthridinone)",
    "Cl-mediated ethylene epoxidation", "Alkaline lignin -> vanillin (pilot)"])
carrier_is_electrolyte_anion(rxn) = rxn in CARRIER_IS_SUPPORTING_ANION
const REACTORS_L = [(:natural,"Unstirred batch"), (:stirred,"Stirred batch"),
                    (:flow,"Recirculating flow cell"), (:anec,"ANEC flow cell"),
                    (:micro,"Microfluidic cell (25 um gap)"),
                    (:rde,"RDE 1600 rpm"), (:rce,"Rotating cylinder 3000 rpm")]

const K_BAND_M = [0.0, 1.0, 10.0, 100.0, 1e3, 1e4]        # M^-1 s^-1, DECLARED
## SUBSTRATE DIFFUSIVITIES: each row's own molecule, read from its exemplar and computed by
## Wilke-Chang in the row's solvent (data/build_catalyst_substrates.py -> catalyst_substrates.csv).
## Until 2026-10-05 every row used one declared value, 1.0e-9 m^2/s x (0.369 mPa s / mu).
const D_SUB = let t = csvrows("catalyst_substrates.csv"), h = t[1]
    Dict(getf(r, h, "reaction") => num(getf(r, h, "D_sub_m2s")) for r in t[2:end])
end

catrows = [r for r in rxd if occursin("catalyst", lowercase(getf(r, rxh, "carrier_type")))]
sort([getf(r, rxh, "reaction") for r in catrows]) == sort(collect(keys(D_SUB))) ||
    error("catalyst rows of reactions_50.csv and data/catalyst_substrates.csv disagree; found $(length(catrows)) rows and $(length(D_SUB)) substrates")

## SEGMENT MODE (2026-10-05). CAT_ROWS="a:b" restricts this run to catalyst rows a..b in table order, so the
## sweep can be solved as independent segments in scratch copies of julia/ and the segments concatenated in
## order. The rows are independent -- no state passes from one to the next -- so the concatenation is the
## file a single run writes; data/catalyst_ec_sensitivity.py --sweep is the single-run check of that.
if !isempty(get(ENV, "CAT_ROWS", ""))
    let ab = parse.(Int, split(ENV["CAT_ROWS"], ":"))
        global catrows = catrows[ab[1]:ab[2]]
        println("SEGMENT MODE: catalyst rows $(ab[1]) to $(ab[2]) of the table")
    end
end

## the species set, copied from run_all50_np.jl (k = 0 layer); returns (sp, Cc, nc, Dc, nu_s,
## Csub, nsub, dirn, zc, zprod, D_an_like, D_cat_like)
function np_species(r)
    rxn = getf(r, rxh, "reaction")
    ti = findfirst(x -> x.name == rxn, RXNS); ti === nothing && error("not in reactions_table: $rxn")
    t = RXNS[ti]; Cc, nc, Dc, nu_s, Csub, nsub = t.C, t.n, t.D, t.nu, t.Csub, t.nsub
    ci = findfirst(x -> getf(x, cch, "reaction") == rxn, ccd); ci === nothing && error("no carrier charge: $rxn")
    zc = num(getf(ccd[ci], cch, "z_carrier"))
    e = findfirst(x -> getf(x, eih, "reaction") == rxn, eid); e === nothing && error("no ions: $rxn")
    erow = eid[e]
    Cs = num(getf(erow, eih, "conc_M")) * 1000.0
    zcat = num(getf(erow, eih, "z_cat")); Dcat = num(getf(erow, eih, "D_cat"))
    zan  = num(getf(erow, eih, "z_an"));  Dan  = num(getf(erow, eih, "D_an"))
    d_ = findfirst(x -> getf(x, dih, "reaction") == rxn, did); d_ === nothing && error("no direction: $rxn")
    dirn = getf(did[d_], dih, "direction")
    (isnan(Cs) || isnan(zcat) || isnan(zan)) && (Cs = 0.0)
    zprod = (dirn == "anodic") ? (zc + nc) : (zc - nc)
    sp = ECSpecies[]
    push!(sp, ECSpecies("Carrier", zc, Dc, Cc, -1/nc, 0.0))
    push!(sp, ECSpecies("Product", zprod, Dc, max(1e-6*Cc, 1e-9), +1/nc, 0.0))
    Dan_like, Dcat_like = 1.5e-9, 1e-9
    if Cs > 0
        q_c = zc * Cc
        same_ion = (zc == zan) && carrier_is_electrolyte_anion(rxn)
        c_an  = same_ion ? max(0.0, Cs - Cc) : Cs + max(0.0, q_c) / max(-zan, 1.0)
        c_cat = same_ion ? (abs(q_c) + abs(zan) * c_an) / max(zcat, 1.0) : Cs + max(0.0, -q_c) / max(zcat, 1.0)
        push!(sp, ECSpecies("Cat+", zcat, Dcat, c_cat, 0.0, 0.0))
        c_an > 0 && push!(sp, ECSpecies("An-", zan, Dan, c_an, 0.0, 0.0))
        Dan_like, Dcat_like = Dan, Dcat
    else
        push!(sp, ECSpecies("Cat+", 1.0, 1e-9, max(-zc,0)*Cc + 1e-3, 0.0, 0.0))
        push!(sp, ECSpecies("An-", -1.0, 1.5e-9, max(zc,0)*Cc + 1e-3, 0.0, 0.0))
    end
    en = sum(s.z * s.c_bulk for s in sp)
    if abs(en) > 1e-9
        j = en > 0 ? findfirst(s -> s.z < 0, sp) : findfirst(s -> s.z > 0, sp)
        added = abs(en)/abs(sp[j].z)
        sp[j] = ECSpecies(sp[j].name, sp[j].z, sp[j].D, sp[j].c_bulk + added, sp[j].s, sp[j].nu)
    end
    (sp, Cc, nc, Dc, nu_s, Csub, nsub, dirn, zc, zprod, Dan_like, Dcat_like, rxn)
end

open(joinpath(@__DIR__, "catalyst_ec_sweep.csv"), "w") do io
    println(io, "reaction,reactor,k_M,delta_um,xk_um,D_S_m2s,i_fick_mAcm2,i_k0_mAcm2,i_saveant_mAcm2,i_subcap_mAcm2,i_ec_mAcm2,amplification,limiter,path")
    for r in catrows
        sp0, Cc, nc, Dc, nu_s, Csub, nsub, dirn, zc, zprod, Dan_like, Dcat_like, rxn = np_species(r)
        mu = num(getf(r, rxh, "mu_mPas"))
        D_S = D_SUB[getf(r, rxh, "reaction")]
        ## the two appended species, and the homogeneous stoichiometry on the carrier pair
        sp = ECSpecies[]
        for (j, s) in enumerate(sp0)
            nu = j == 1 ? +1.0 : (j == 2 ? -1.0 : 0.0)      # resting regenerated, active spent
            push!(sp, ECSpecies(s.name, s.z, s.D, s.c_bulk, s.s, nu))
        end
        push!(sp, ECSpecies("Sub", 0.0, D_S, Csub, 0.0, -nc/nsub))
        zx = dirn == "anodic" ? +1.0 : -1.0
        push!(sp, ECSpecies("Xion", zx, zx > 0 ? Dcat_like : Dan_like, 1e-5 * Cc, 0.0, nc))
        isb = findfirst(s -> s.name == "Sub", sp)
        ## invariants
        zs  = sum(s.z * s.s  for s in sp); znu = sum(s.z * s.nu for s in sp)
        en  = sum(s.z * s.c_bulk for s in sp)
        abs(abs(zs) - 1.0) < 1e-9 || error("sum z*s != +/-1 for $rxn: $zs")
        abs(znu) < 1e-9 || error("homogeneous step injects charge for $rxn: $znu")
        abs(en) < 1e-6 * maximum(s.c_bulk for s in sp) + 1e-3 * Cc || error("bulk not electroneutral for $rxn: $en")
        @printf("=== %s  [%s, z_c=%g, n_c=%g, n_S=%g, C_cat=%g, C_S=%g mol/m3, D_S=%.3g]\n",
                rxn, dirn, zc, nc, nsub, Cc, Csub, D_S); flush(stdout)
        for (rk, rlab) in REACTORS_L
            d = delta_eff(rk, Dc, nu_s)
            i_fick = nc * F_const * Dc * Cc / d
            i_k0 = NaN
            for k_M in K_BAND_M
                km = k_M / 1000.0
                xk = km > 0 ? sqrt(Dc / (km * Csub)) : Inf
                dx1 = clamp(xk / 50, 0.02e-6, 0.9 * d / 90)
                p = ECProblem(sp, 2, isb, km, geometric_faces(d, dx1, 90))
                il, lim, us, isf = solve_ilim_ec(p; i_start = 0.02 * i_fick, growth = 1.15)
                path = "direct-ramp"
                if isf > 0
                    ic, limc, uc, _, _ = solve_ilim_ec_ccontrol(p; u0 = us, i0 = isf)
                    if (startswith(limc, "collapse") || startswith(limc, "plateau") ||
                        startswith(limc, "limit reached")) && ic > il
                        il, lim, path = ic, limc, "c-control"
                    else
                        lim = lim * "; " * limc
                    end
                end
                if k_M == 0.0
                    i_k0 = il
                elseif il < 0.98 * i_k0                 # below its own no-source floor: not a solution
                    path = path * ";UNRESOLVED<floor"
                end
                i_sav = km > 0 ? nc * F_const * Cc * sqrt(Dc * km * Csub) : NaN
                i_cap = nsub * F_const * D_S * Csub / d
                amp = il / i_k0
                @printf("  %-30s k=%-7g  delta %7.1f um  xk %9.3g um  i_k0 %8.3f  i_ec %8.3f  x%.3f  cap %8.2f  [%s | %s]\n",
                        rlab, k_M, d*1e6, xk*1e6, i_k0*0.1, il*0.1, amp, i_cap*0.1, path, lim); flush(stdout)
                println(io, "\"$rxn\",\"$rlab\",$k_M,$(d*1e6),$(xk*1e6),$D_S,$(i_fick*0.1),$(i_k0*0.1),$(i_sav*0.1),$(i_cap*0.1),$(il*0.1),$amp,\"$lim\",\"$path\"")
                flush(io)
            end
        end
    end
end
println("CATALYST SWEEP DONE")
