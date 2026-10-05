## params.jl — constants and reactor archetypes for the Section 4 transport model.
## Conventions follow co2r_bulk: SI units throughout, concentrations mol/m^3.

## F and R are DERIVED from the exactly defined SI constants (e, N_A, k_B) of
## BIPM, The International System of Units (SI Brochure), 9th ed., 2019, Sect. 2.3.1 Table 1:
## F = e*N_A and R = k_B*N_A. T is a declared modelling convention, not a measurement --
## the model is isothermal at 25 C and says so (registry row 'Temperature T', state C).
const F_const = 96485.332          # C/mol
const R_gas   = 8.314462618        # J/(mol K)
const T_K     = 298.15             # K
const RT_F    = R_gas * T_K / F_const   # 0.02569 V

## Industrial viability threshold used throughout Section 4.
## Ferretti, Cohen, Deng, Diwan, Frederick & Lehnherr, Org. Process Res. Dev. 2025, 29, 322-332,
## Fig. 11 (page-verified) -- the 25 and 50 mA cm-2 rungs every threshold count in Table S5 and
## Fig. 3 is scored against.
const I_THRESH = 25.0              # mA/cm^2

## ── Reactor archetypes ────────────────────────────────────────────────────────
## Each archetype either fixes delta directly or supplies a k_m correlation
## (evaluated per species, since delta depends on D and nu). Geometry choices are
## representative laboratory/pilot values, documented in SI §S2.
##   :natural   unstirred batch, natural-convection-limited delta = 228 um (derived)
##   :stirred   magnetically stirred batch, delta ≈ 100 um
##   :rde       rotating disk, 1600 rpm (Levich)
##   :flow      recirculating flow cell, MEASURED 106.9 um (Watkins 2023, SI Table S1)
##   :anec      ANEC flow cell (angled inlet), MEASURED 36.2 um (Watkins 2023, SI Table S1)
##   :micro     microfluidic cell, 25 um gap (Mo 2020), film = half-gap 12.5 um
##   :rce       rotating cylinder electrode, d 1.2 cm, 3000 rpm (Eisenberg)
struct Reactor
    key::Symbol
    label::String
end

const REACTORS = Reactor[
    Reactor(:natural, "Unstirred batch"),
    Reactor(:stirred, "Stirred batch"),
    Reactor(:flow,    "Recirculating flow cell"),
    Reactor(:anec,    "ANEC flow cell"),
    Reactor(:micro,   "Microfluidic cell (25 um gap)"),
    Reactor(:rde,     "RDE 1600 rpm"),
    Reactor(:rce,     "Rotating cylinder 3000 rpm"),
]
