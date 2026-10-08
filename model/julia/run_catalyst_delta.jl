## run_catalyst_delta.jl -- the seven SOURCED catalyst rows solved at k = 0 and at their sourced k across the
## same 17-film grid the base-case mediator sweep uses (run_regimes_delta.jl), so Fig. 6h can draw each row's
## intensification curve rather than seven archetype points. Species, mesh rule and accept sequence identical to
## run_catalyst_sourced.jl; only delta is imposed. Writes catalyst_ec_delta.csv beside itself. Touches no other artifact.
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

## CHEMISTRY AUDIT, 2026-10-05: the two Ni aminations and the Co(salen) allylic C-H amination left this table. In the
## aminations the oxidative addition happens at the cathode and the cycle closes only at the ANODE (Kawamata JACS 2019
## p. 6396, steps B-F; Liu/Qiu Angew 2025 Fig. 4f), so it cannot regenerate the carrier inside one electrode's film; in the
## allylic amination the catalyst does not regenerate at room temperature at all (Cai/Xu Nat Commun 2021 p. 6) and turns
## over by heat-induced homolysis at reflux (p. 7), whose rate is not reported. All three are solved at the floor, k = 0.
const K_SOURCED = Dict(
    "Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)"          => 100.0,
    "Cathodic Ni aryl-aryl homocoupling"         => 100.0,
    "Co-H alkene reduction (e-HAT)"    => 700.0,
    "Co-H alkene isomerization (catalytic)"      => 700.0,
    "Co-catalyzed allylic C-H amination"        => 0.0)   # drawn in Fig. 6h at the floor; no measured constant
const DELTAS_UM = [260, 228, 200, 176.598, 119.95, 106.9, 81.473, 55.338, 37.587, 36.2, 25.53, 17.341, 12.624, 12.5, 11.778, 10.992, 8]
## SUBSTRATE DIFFUSIVITIES: each row's own molecule, read from its exemplar and computed by
## Wilke-Chang in the row's solvent (data/build_catalyst_substrates.py -> catalyst_substrates.csv).
## Until 2026-10-05 every row used one declared value, 1.0e-9 m^2/s x (0.369 mPa s / mu).
const D_SUB = let t = csvrows("catalyst_substrates.csv"), h = t[1]
    Dict(getf(r, h, "reaction") => num(getf(r, h, "D_sub_m2s")) for r in t[2:end])
end

catrows = [r for r in rxd if haskey(K_SOURCED, getf(r, rxh, "reaction"))]
length(catrows) == length(K_SOURCED) || error("expected $(length(K_SOURCED)) sourced rows, found $(length(catrows))")

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

open(joinpath(@__DIR__, "catalyst_ec_delta.csv"), "w") do io
    println(io, "reaction,k_M,delta_um,xk_um,D_S_m2s,i_fick_mAcm2,i_k0_mAcm2,i_subcap_mAcm2,i_ec_mAcm2,amplification,limiter,path")
    for r in catrows
        sp0, Cc, nc, Dc, nu_s, Csub, nsub, dirn, zc, zprod, Dan_like, Dcat_like, rxn = np_species(r)
        mu = num(getf(r, rxh, "mu_mPas")); D_S = D_SUB[getf(r, rxh, "reaction")]
        sp = ECSpecies[]
        for (j, s) in enumerate(sp0)
            nu = j == 1 ? +1.0 : (j == 2 ? -1.0 : 0.0)
            push!(sp, ECSpecies(s.name, s.z, s.D, s.c_bulk, s.s, nu))
        end
        push!(sp, ECSpecies("Sub", 0.0, D_S, Csub, 0.0, -nc/nsub))
        zx = dirn == "anodic" ? +1.0 : -1.0
        push!(sp, ECSpecies("Xion", zx, zx > 0 ? Dcat_like : Dan_like, 1e-5 * Cc, 0.0, nc))
        isb = findfirst(s -> s.name == "Sub", sp)
        ksrc = K_SOURCED[rxn]
        @printf("=== %s  k_sourced=%g\n", rxn, ksrc); flush(stdout)
        for dum in DELTAS_UM
            d = dum * 1e-6
            i_fick = nc * F_const * Dc * Cc / d
            i_k0 = NaN
            for k_M in unique([0.0, ksrc])            # a row with no measured constant is solved once, at k = 0
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
                elseif il < 0.98 * i_k0
                    path = path * ";UNRESOLVED<floor"
                end
                i_cap = nsub * F_const * D_S * Csub / d
                amp = il / i_k0
                @printf("  delta %7.3f um  k=%-6g  xk %9.3g um  i_k0 %8.3f  i_ec %8.3f  x%.3f  cap %8.2f  [%s | %s]\n",
                        dum, k_M, xk*1e6, i_k0*0.1, il*0.1, amp, i_cap*0.1, path, lim); flush(stdout)
                println(io, "\"$rxn\",$k_M,$dum,$(xk*1e6),$D_S,$(i_fick*0.1),$(i_k0*0.1),$(i_cap*0.1),$(il*0.1),$amp,\"$lim\",\"$path\"")
                flush(io)
            end
        end
    end
end
println("CATALYST DELTA DONE")
