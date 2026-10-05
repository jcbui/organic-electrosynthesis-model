## run_catalyst_sourced.jl -- the eleven catalyst rows solved at k = 0 (the published control) and, for the
## seven rows with a SOURCED rate constant, at that k (docs/CATALYST_RATE_CONSTANTS_20260911.md; author
## decision 2026-09-11). Species construction, mesh rule and accept sequence are those of
## run_catalyst_ecprime.jl; only the k list is per row. The sourced cells are what the published matrix
## carries for those seven rows (data/build_merged_matrix.py overlays them exactly as it overlays the
## mediated rows). Writes catalyst_ec_sourced.csv beside itself. Touches no other artifact.
##   cd julia && nohup julia run_catalyst_sourced.jl > /abs/path/log 2>&1 &
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
    "Cl-mediated ethylene epoxidation", "Alkaline lignin -> vanillin (pilot)"])
carrier_is_electrolyte_anion(rxn) = rxn in CARRIER_IS_SUPPORTING_ANION
const REACTORS_L = [(:natural,"Unstirred batch"), (:stirred,"Stirred batch"),
                    (:flow,"Recirculating flow cell"), (:anec,"ANEC flow cell"),
                    (:micro,"Microfluidic cell (25 um gap)"),
                    (:rde,"RDE 1600 rpm"), (:rce,"Rotating cylinder 3000 rpm")]

## SOURCED rate constants (M^-1 s^-1) and their basis tag -- see the dossier for locators.
##   Ni(I)-bpy + ArBr: Ting/Williams/Doyle JACS 2022, 144, 5579 (3.4-56, PhBr 7.1; deactivated
##   ligand, THF) <= Kawamata JACS 2019, 141, 6394 in-medium CV (>= 1e2) < Till JACS 2021, 143,
##   9334 (< 1e4, dtbbpy): declared 1e2, band 1e1-1e4.
##   Co-H + alkene: Boucher et al. JACS 2023, 145, 17674, kMHAT = 7e2 (Co(salen) + styrene, DMF).
##   Co(salen) aza-Wacker: own CV, Cai/Xu Nat Commun 2021 SI p. 5, <= 4e1 at rt with Na2CO3: 1e1.
const K_SOURCED = Dict(
    "Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)"          => (100.0, "Ni(I)bpy+ArBr: Ting22/Kawamata19/Till21"),
    "Ni-catalyzed aryl amination (ArBr + amine)" => (100.0, "Ni(I)bpy+ArBr: Ting22/Kawamata19/Till21"),
    "Electrochemical amination of ArX with NH3"  => (100.0, "Ni(I)bpy+ArBr: Ting22/Kawamata19/Till21"),
    "Cathodic Ni aryl-aryl homocoupling"         => (100.0, "Ni(I)bpy+ArBr: Ting22/Kawamata19/Till21"),
    "Co-H alkene reduction (e-HAT)"    => (700.0, "Co-H+alkene: Boucher23 kMHAT"),
    "Co-H alkene isomerization (catalytic)"      => (700.0, "Co-H+alkene: Boucher23 kMHAT"),
    "Co-catalyzed aza-Wacker cyclization"        => (10.0,  "own CV: Cai/Xu21 SI Fig S2, <=4e1 at rt"),
)
const D_S_REF, MU_REF = 1.0e-9, 0.369                      # m^2/s at the MeCN viscosity, DECLARED

catrows = [r for r in rxd if occursin("catalyst", lowercase(getf(r, rxh, "carrier_type")))]
length(catrows) == 11 || error("expected 11 catalyst rows, found $(length(catrows))")
for k in keys(K_SOURCED)
    any(r -> getf(r, rxh, "reaction") == k, catrows) || error("K_SOURCED names a row not in reactions_50: $k")
end

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

open(joinpath(@__DIR__, "catalyst_ec_sourced.csv"), "w") do io
    println(io, "reaction,reactor,k_M,delta_um,xk_um,D_S_m2s,i_fick_mAcm2,i_k0_mAcm2,i_saveant_mAcm2,i_subcap_mAcm2,i_ec_mAcm2,amplification,limiter,path,k_basis")
    for r in catrows
        sp0, Cc, nc, Dc, nu_s, Csub, nsub, dirn, zc, zprod, Dan_like, Dcat_like, rxn = np_species(r)
        mu = num(getf(r, rxh, "mu_mPas"))
        D_S = D_S_REF * MU_REF / mu
        sp = ECSpecies[]
        for (j, s) in enumerate(sp0)
            nu = j == 1 ? +1.0 : (j == 2 ? -1.0 : 0.0)
            push!(sp, ECSpecies(s.name, s.z, s.D, s.c_bulk, s.s, nu))
        end
        push!(sp, ECSpecies("Sub", 0.0, D_S, Csub, 0.0, -nc/nsub))
        zx = dirn == "anodic" ? +1.0 : -1.0
        push!(sp, ECSpecies("Xion", zx, zx > 0 ? Dcat_like : Dan_like, 1e-5 * Cc, 0.0, nc))
        isb = findfirst(s -> s.name == "Sub", sp)
        zs  = sum(s.z * s.s  for s in sp); znu = sum(s.z * s.nu for s in sp)
        en  = sum(s.z * s.c_bulk for s in sp)
        abs(abs(zs) - 1.0) < 1e-9 || error("sum z*s != +/-1 for $rxn: $zs")
        abs(znu) < 1e-9 || error("homogeneous step injects charge for $rxn: $znu")
        abs(en) < 1e-6 * maximum(s.c_bulk for s in sp) + 1e-3 * Cc || error("bulk not electroneutral for $rxn: $en")
        ksrc, kbasis = get(K_SOURCED, rxn, (0.0, "no source: floor k = 0"))
        klist = ksrc > 0 ? [0.0, ksrc] : [0.0]
        @printf("=== %s  [%s, z_c=%g, n_c=%g, n_S=%g, C_cat=%g, C_S=%g mol/m3, D_S=%.3g]  k_sourced=%g (%s)\n",
                rxn, dirn, zc, nc, nsub, Cc, Csub, D_S, ksrc, kbasis); flush(stdout)
        for (rk, rlab) in REACTORS_L
            d = delta_eff(rk, Dc, nu_s)
            i_fick = nc * F_const * Dc * Cc / d
            i_k0 = NaN
            for k_M in klist
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
                i_sav = km > 0 ? nc * F_const * Cc * sqrt(Dc * km * Csub) : NaN
                i_cap = nsub * F_const * D_S * Csub / d
                amp = il / i_k0
                @printf("  %-30s k=%-7g  delta %7.1f um  xk %9.3g um  i_k0 %8.3f  i_ec %8.3f  x%.3f  cap %8.2f  [%s | %s]\n",
                        rlab, k_M, d*1e6, xk*1e6, i_k0*0.1, il*0.1, amp, i_cap*0.1, path, lim); flush(stdout)
                println(io, "\"$rxn\",\"$rlab\",$k_M,$(d*1e6),$(xk*1e6),$D_S,$(i_fick*0.1),$(i_k0*0.1),$(i_sav*0.1),$(i_cap*0.1),$(il*0.1),$amp,\"$lim\",\"$path\",\"$(k_M == 0.0 ? "control k = 0" : kbasis)\"")
                flush(io)
            end
        end
    end
end
println("CATALYST SOURCED DONE")
