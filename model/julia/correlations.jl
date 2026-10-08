## correlations.jl — mass-transfer correlations per reactor archetype.
## k_m in m/s; delta_eff = D / k_m.
##
## FULL REFERENCES, at the point of use. Each correlation is an EMPIRICAL fit from a named
## paper, and the registry carries the same locator for each (data/parameters_provenance.csv,
## category 7); they are repeated here so a reader of the solver does not have to leave it.
##
##   Levich, delta = 1.61 D^(1/3) nu^(1/6) omega^(-1/2)
##     A. J. Bard & L. R. Faulkner, "Electrochemical Methods: Fundamentals and Applications",
##     2nd edn, Wiley, 2001, p. 30 footnote 11 (cross-referring Sect. 9.3.2); the coefficient
##     1.61 is confirmed in Sect. 12.4, which prints delta^2/D = (1.61)^2 nu^(1/3)/(omega D^(1/3)).
##     NOTE the source prints 1.61, not 1.613: 1/0.62 carries precision the 2-s.f. 0.62 never had.
##
##   Leveque entrance solution, Sh = 1.85 (Re Sc d_h/L)^(1/3)
##     D. J. Pickett & K. L. Ong, "The influence of hydrodynamic and mass transfer entrance
##     effects on the operation of a parallel plate electrolytic cell", Electrochim. Acta 1974,
##     19, 875-882 -- experimental validation in this exact geometry. The same paper finds that
##     an entrance-length correction should be added to L, which this model does NOT apply.
##     Since 2026-09-07 no archetype film is computed from it: the three flow films are measured
##     (see delta_eff). km_leveque is retained for the S8.1 intensification illustration and
##     because its fully-developed floor D/(h/2) is the rule that sets the microfluidic film.
##
##   Eisenberg-Tobias-Wilke rotating cylinder, Sh = 0.0791 Re^0.70 Sc^0.356
##     M. Eisenberg, C. W. Tobias & C. R. Wilke, J. Electrochem. Soc. 1954, 101, 306-320,
##     DOI 10.1149/1.2781252. Fitted to the ferri/ferrocyanide couple at nickel cylinders in
##     alkaline aqueous solution. The paper states its own calibration on p. 313: "a Schmidt
##     number variation of 2230 to 3650 and a Reynolds number range of 112.0-162,000". The fifty
##     rows here run Sc 176-19,006, so 44 of 50 sit BELOW the fitted floor and only 5 above the
##     ceiling -- the extrapolation is predominantly to LOW Sc, because aprotic organics have low
##     viscosity, which raises D and lowers nu together. An earlier version of this comment said
##     the column was therefore "an upper estimate"; that was inferred from an exponent
##     substitution made WITHOUT re-anchoring the prefactor, which changes the correlation inside
##     the calibration range where the fit is known to hold. Re-anchored at the fit centre, the
##     Sc^(1/3) asymptote moves per-row values by 0.958-1.065x and RAISES the RCE median, so on
##     this axis the column is if anything an under-estimate. See data/schmidt_extrapolation.py
##     (G-SCRANGE), and Newman & Thomas-Alyea, "Electrochemical Systems", 3rd edn, Wiley, 2004,
##     Ch. 17 for the general mass-transfer treatment.

## Levich RDE: delta = 1.61 D^(1/3) nu^(1/6) omega^(-1/2)
function delta_rde(D::Float64, nu::Float64; rpm::Float64 = 1600.0)
    omega = 2pi * rpm / 60.0
    return 1.61 * D^(1/3) * nu^(1/6) / sqrt(omega)
end

## Leveque (entrance-dominated laminar channel): Sh = 1.85 (Re Sc d_h / L)^(1/3)
## Wide parallel-plate channel of gap h: d_h = 2h.
function km_leveque(D::Float64, nu::Float64; h::Float64, L::Float64, u::Float64)
    dh = 2h
    Re = u * dh / nu
    Sc = nu / D
    @assert Re < 2300 "Leveque used outside laminar regime (Re=$(round(Re)))"
    Sh = 1.85 * (Re * Sc * dh / L)^(1/3)
    # entrance solution cannot exceed the fully-developed film bounded by half-gap
    km = Sh * D / dh
    return max(km, D / (h/2))
end

## Eisenberg–Tobias–Wilke rotating cylinder (turbulent): Sh = 0.079 Re^0.70 Sc^0.356
function km_rce(D::Float64, nu::Float64; d::Float64 = 0.012, rpm::Float64 = 3000.0)
    U = pi * d * rpm / 60.0
    Re = U * d / nu
    Sc = nu / D
    Sh = 0.0791 * Re^0.70 * Sc^0.356
    return Sh * D / d
end

## The three flow archetypes are MEASURED films, adopted 2026-09-07 (author decision), in place
## of the two Leveque operating points (1 mm gap / 250 um gap) that had been declared with no
## source. Under the four-state rule a measured value with a locator displaces a declared one.
##
##   :flow   106.9 um  Watkins, Schiffer, Lai, Musgrave III, Atwater, Goddard III, Agapie, Peters
##                     & Gregoire, "Hydrodynamics Change Tafel Slopes in Electrochemical CO2
##                     Reduction on Copper", ACS Energy Lett. 2023, 8, 2185-2192, Supporting
##                     Information Table S1, p. 6 ("Parallel H-cell (280 uL/s)": 106.9 um
##                     experimental, 242 um COMSOL). Ferricyanide limiting current, method of
##                     Clark et al. (D = 0.720e-5 cm2/s, 10 mM), read against the page raster.
##   :anec    36.2 um  same table, "ANEC (140 uL/s)": 36.2 um experimental, 57 um COMSOL; the
##                     footnote gives 140 uL/s as the typical ANEC flow rate. The angled H-cell
##                     in the same table reads 33.4 um (128 COMSOL) at 280 uL/s. Only the Ager
##                     H-cell entry (177.9 +/- 21.6 um) carries replicate error (n = 6).
##   :micro   8-12.5 um  Mo, Rughoobur, Lu, ... Buchwald & Jensen, Science 2020, 368, 1352
##                     (aba3823), Supporting Information p. 13: the optimisation experiments
##                     "were conducted in a small-scale electrochemical flow cell with the
##                     thinnest FEP spacer (0.001", 25 um)", and Table S1 on the same page prints
##                     the residence time tau = 4 min for entries 9-12, entry 12 being the
##                     published optimum. The film is DERIVED from those two printed numbers by
##                     the rule every flow cell in this model has always used, the Leveque
##                     entrance solution bounded by the fully-developed half-gap film. It needs
##                     no channel width or length: with u = Q/(w h) and Q tau = w h L, the
##                     Leveque number Re Sc d_h/L = 4 u h^2/(D L) reduces to 4 h^2/(D tau)
##                     exactly: 1.0e-11 m2/s divided by D, i.e. 0.003-0.06 for the fifty rows.
##                     The entrance solution exceeds the fully-developed film only for
##                     D < 4 h^2/((4/1.85)^3 tau) = 1.0e-12 m2/s, three decades below any row,
##                     so the floor binds for all fifty and the film is the half-gap, 12.5 um,
##                     independent of D and nu. (Whether the entrance solution is applicable at
##                     all here is moot for the same reason: the flow is fully developed.)
##
## The two Watkins films are AQUEOUS ferricyanide measurements applied unscaled to every row,
## exactly as the stirred film is; the registry rows state that and its direction.
const DELTA_FLOW   = 106.9e-6
const DELTA_ANEC   =  36.2e-6
const H_MICRO      =  25.0e-6           # Mo 2020 SI p. 13: 0.001 in FEP spacer
const TAU_MICRO    = 4.0 * 60.0         # Mo 2020 SI Table S1 (p. 13), entries 9-12: tau = 4 min, in s
delta_halfgap(h::Float64) = h / 2
function km_micro(D::Float64; h::Float64 = H_MICRO, tau::Float64 = TAU_MICRO)
    Sh = 1.85 * (4h^2 / (D * tau))^(1/3)       # Leveque with Re Sc d_h/L = 4 h^2/(D tau)
    return max(Sh * D / (2h), D / (h / 2))     # bounded by the fully-developed half-gap film
end

## Sensitivity bands for the three measured/derived flow films (Table S7, the SI bounds table).
## Table S1 prints replicate error for ONE cell only, the Ager H-cell: 21.6/177.9 = 12.1 %
## (six experiments). The parallel H-cell and ANEC values are single printed numbers, so the
## band applied to them is that same-method, same-study scatter -- a DECLARED transfer, stated
## as such in the registry.
## The microfluidic band is the printed residence-time range of Mo's Table S1, 4-12 min. The
## entrance solution lies below the fully-developed film at both ends for every row, so the band
## collapses onto the half-gap itself: no printed condition in that cell moves the film. The
## exposure is the half-gap rule, which is shared with every flow cell this model has described.
const FILM_SCATTER     = 21.6 / 177.9
const DELTA_FLOW_BAND  = (DELTA_FLOW * (1 - FILM_SCATTER), DELTA_FLOW * (1 + FILM_SCATTER))
const DELTA_ANEC_BAND  = (DELTA_ANEC * (1 - FILM_SCATTER), DELTA_ANEC * (1 + FILM_SCATTER))
const TAU_MICRO_BAND   = (4.0 * 60.0, 12.0 * 60.0)   # Table S1's printed residence times, 4 and 12 min

"""delta_eff(key, D, nu) -> effective Nernst diffusion-layer thickness [m]"""
function delta_eff(key::Symbol, D::Float64, nu::Float64)
    if key === :natural
        return 228e-6
    elseif key === :stirred
        ## the stirred film. ADOPTED 200 um on 2026-09-01 (author decision). The retired 100 um was an assumption whose inherited citation had been WITHDRAWN -- no passage in Pletcher & Walsh giving ~100 um for a magnetically stirred cell could be located. 200 +/- 7 um is MEASURED: Williams, Corbin, Zeng, Lazouski, Yang & Manthiram, Sustain. Energy Fuels 2019, 3, 1225-1232, p. 1227, a planar electrode in a gas-bubbled cell, back-calculated from the ferricyanide limiting current. It is a proxy, not this system: O2 diffuses about 1.5 times as fast as the median carrier here, and a convective film thickens with D, so the organics' own layer should be THINNER (about 12-18 pct; SI S7), and the adopted value stays conservative (it lowers the ceilings).
        return 200e-6
    elseif key === :flow
        return DELTA_FLOW
    elseif key === :anec
        return DELTA_ANEC
    elseif key === :micro
        return D / km_micro(D)
    elseif key === :rde
        return delta_rde(D, nu)
    elseif key === :rce
        return D / km_rce(D, nu)
    else
        error("unknown reactor $key")
    end
end

## Tier-0 limiting current density [mA/cm^2]: i_lim = n F D C / delta × 0.1
i_lim_tier0(n::Float64, D::Float64, C::Float64, delta::Float64) =
    0.1 * n * F_const * D * C / delta
