## dma_viscosity_ecprime.jl -- G-DMAMU's solver half: every DMA cell of the published matrix RE-SOLVED at each
## swept viscosity, so the sweep never has to guess how a cell scales with mu.
##
## WHY A RE-SOLVE. data/sensitivity_dma_viscosity.py used to scale every DMA cell as mu^p with p the archetype's
## transport exponent (-1 wherever the film is fixed). That is exact for a cell solved at k = 0 (the whole NP problem
## scales with D), and wrong for a cell solved as an EC' problem at a finite rate constant: on the kinetic plateau the
## current is n F C_cat (D_cat k C_S)^(1/2) (Saveant), i.e. mu^(-1/2), and between the plateau and the substrate cap it
## is neither. The Ni-XEC row is carried at its sourced k = 1e2 M-1 s-1, so its cells are re-solved here with the
## species construction, mesh rule and accept sequence of julia/run_catalyst_sourced.jl, copied verbatim.
##
## WHAT CHANGES WITH mu. Only the quantities the model DERIVES from the solvent viscosity: the carrier (and its
## product) diffusivity and the substrate diffusivity, both Wilke-Chang and so proportional to 1/mu, and the kinematic
## viscosity nu = mu/rho, which moves the RDE and rotating-cylinder films. The supporting-ion diffusivities in DMA are
## Krumgalz's limiting conductances (data/electrolyte_ions.csv), which do not depend on the handbook viscosity, so they
## are held. The rate constant is held.
##
## CONTROL. At the printed viscosity every re-solved cell must reproduce the published matrix (julia/tier0_ec_matrix.csv);
## data/sensitivity_dma_viscosity.py refuses the artifact otherwise.
##
## Run ONLY in a scratch copy of the tree (it writes ../results/dma_viscosity_ecprime.csv relative to itself):
##   cp -R Section4_Model/{julia,data} /tmp/x/ && mkdir /tmp/x/results && cd /tmp/x/data && julia dma_viscosity_ecprime.jl
## then copy /tmp/x/results/dma_viscosity_ecprime.csv into Section4_Model/results/.
using Printf
const JL = joinpath(@__DIR__, "..", "julia")
include(joinpath(JL, "params.jl")); include(joinpath(JL, "correlations.jl"))
include(joinpath(JL, "npp_ecprime.jl"))
include(joinpath(JL, "reactions_table.jl"))

const DATA = @__DIR__
const MU_SWEEP = [1.927, 1.427, 0.927, 0.919]   # printed (CRC 97th p. 6-244), midpoint, homolog reading,
                                                 # Krumgalz 1983 Table 3 p. 578 (0.00919 P)
const SOLVENT = "DMA"

function csvrows(path)
    out = Vector{Vector{String}}()
    for l in eachline(path)
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
rx  = csvrows(joinpath(DATA, "reactions_50.csv"));  rxh = rx[1];  rxd = rx[2:end]
cc  = csvrows(joinpath(DATA, "carrier_charge.csv")); cch = cc[1]; ccd = cc[2:end]
ei  = csvrows(joinpath(DATA, "electrolyte_ions.csv")); eih = ei[1]; eid = ei[2:end]
di_ = csvrows(joinpath(DATA, "electrode_direction.csv")); dih = di_[1]; did = di_[2:end]
src = csvrows(joinpath(JL, "catalyst_ec_sourced.csv")); srh = src[1]; srd = src[2:end]
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

const D_SUB = let t = csvrows(joinpath(DATA, "catalyst_substrates.csv")), h = t[1]
    Dict(getf(r, h, "reaction") => num(getf(r, h, "D_sub_m2s")) for r in t[2:end])
end
## the sourced rate constant each row is published at: the k > 0 member of julia/catalyst_ec_sourced.csv
function k_sourced(rxn)
    ks = unique([num(getf(r, srh, "k_M")) for r in srd if getf(r, srh, "reaction") == rxn && num(getf(r, srh, "k_M")) > 0])
    length(ks) <= 1 || error("more than one sourced k for $rxn: $ks")
    isempty(ks) ? 0.0 : ks[1]
end

## verbatim from julia/run_catalyst_sourced.jl, with g scaling the carrier D and the kinematic viscosity
function np_species(r, g)
    rxn = getf(r, rxh, "reaction")
    ti = findfirst(x -> x.name == rxn, RXNS); ti === nothing && error("not in reactions_table: $rxn")
    t = RXNS[ti]; Cc, nc, Dc, nu_s, Csub, nsub = t.C, t.n, t.D * g, t.nu / g, t.Csub, t.nsub
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

rows = [r for r in rxd if strip(getf(r, rxh, "solvent")) == SOLVENT]
length(rows) == 2 || error("expected 2 $SOLVENT rows, found $(length(rows))")
for r in rows
    occursin("catalyst", lowercase(getf(r, rxh, "carrier_type"))) ||
        error("$(getf(r, rxh, "reaction")) is not catalyst-carried; extend this script before using it")
end
mu0 = unique([num(getf(r, rxh, "mu_mPas")) for r in rows])
(length(mu0) == 1 && abs(mu0[1] - MU_SWEEP[1]) < 1e-9) || error("reactions_50.csv carries mu(DMA) = $mu0, not $(MU_SWEEP[1])")

outdir = joinpath(@__DIR__, "..", "results"); isdir(outdir) || mkpath(outdir)
open(joinpath(outdir, "dma_viscosity_ecprime.csv"), "w") do io
    println(io, "reaction,reactor_key,mu_mPas,k_M,delta_um,xk_um,i_k0_mAcm2,i_saveant_mAcm2,i_subcap_mAcm2,i_ec_mAcm2,limiter,path")
    for mu in MU_SWEEP, r in rows
        g = MU_SWEEP[1] / mu
        sp0, Cc, nc, Dc, nu_s, Csub, nsub, dirn, zc, zprod, Dan_like, Dcat_like, rxn = np_species(r, g)
        D_S = D_SUB[rxn] * g
        sp = ECSpecies[]
        for (j, s) in enumerate(sp0)
            nu = j == 1 ? +1.0 : (j == 2 ? -1.0 : 0.0)
            push!(sp, ECSpecies(s.name, s.z, s.D, s.c_bulk, s.s, nu))
        end
        push!(sp, ECSpecies("Sub", 0.0, D_S, Csub, 0.0, -nc/nsub))
        zx = dirn == "anodic" ? +1.0 : -1.0
        push!(sp, ECSpecies("Xion", zx, zx > 0 ? Dcat_like : Dan_like, 1e-5 * Cc, 0.0, nc))
        isb = findfirst(s -> s.name == "Sub", sp)
        ksrc = k_sourced(rxn)
        klist = ksrc > 0 ? [0.0, ksrc] : [0.0]
        @printf("=== %s  mu %.3f (g %.4f)  k_sourced %g\n", rxn, mu, g, ksrc); flush(stdout)
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
                @printf("  %-30s k=%-7g delta %7.2f um  i_k0 %8.4f  i_ec %8.4f  saveant %8.3f  cap %8.2f  [%s]\n",
                        rlab, k_M, d*1e6, i_k0*0.1, il*0.1, i_sav*0.1, i_cap*0.1, path); flush(stdout)
                (k_M == ksrc) && println(io, "\"$rxn\",$(rk),$mu,$k_M,$(d*1e6),$(xk*1e6),$(i_k0*0.1),$(i_sav*0.1),$(i_cap*0.1),$(il*0.1),\"$lim\",\"$path\"")
                flush(io)
            end
        end
    end
end
println("DMA VISCOSITY RE-SOLVE DONE")
