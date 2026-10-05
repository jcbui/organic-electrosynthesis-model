## cellvoltage.jl — cell-voltage stack and Joule-heating ceiling (Section 4).
##   E_cell(i) = E_thermo + eta_a(i) + eta_c(i) + i * L_gap / kappa
##   Q_joule   = i^2 * L_gap / kappa            [W/m^2 of electrode area]
## Kinetic terms use a symmetric Butler–Volmer inversion eta = b*asinh(i/2i0).
##   b = 2RT/F is the Tafel slope at alpha = 1/2, n = 1 -- Bard & Faulkner, "Electrochemical
##     Methods", 2nd edn, Wiley, 2001, ch. 3 (Butler-Volmer and Tafel forms). alpha = 1/2 is the
##     only free choice; alpha in [0.3, 0.7] moves the activation term by under 60 mV against
##     ohmic terms of 1-50 V in these cells.
##   i0 = 1 mA/cm^2 per electrode is a DECLARED MODELLING CHOICE with no source claimed
##     (registry row 'i0 (exchange current density)', state C, swept 0.01-10 mA/cm^2). It matters
##     only where activation heat is comparable to ohmic heat, which is not the regime any
##     published verdict sits in. See SI §S6.
##   E0 = 2.0 V is likewise declared -- a representative full-cell thermodynamic window, not a
##     measured potential for any one of the 50 reactions.
## The THERMAL ceiling compares Q_joule with achievable heat rejection.

struct Electrolyte
    label::String       # display label, written to cellvoltage.csv
    csvkey::String      # exact `electrolyte` field of data/electrolytes.csv
    kappa::Float64      # S/m, LOADED from that file -- never typed in this file
end

## ELECTROLYTE SET — READ FROM THE REGISTRY AT RUN TIME (2026-08-02 purge; made genuinely
## registry-driven, then re-stated against the revised registry, both 2026-08-02).
##
## HISTORY OF THIS BLOCK, because the correction matters more than the values, and because
## this header has now been wrong TWICE in two different ways.
##
## (1) It once asserted that each kappa "is read from [data/electrolytes.csv], NOT retyped"
## while `const ELECS` in fact held five hardcoded Float64 literals. False as written: a
## registry edit could have desynced this file's output from the CSV silently. `read_kappa`
## below now performs that read, so the assertion is enforced by execution, not by intent.
##
## (2) The rewrite that fixed (1) then claimed the five kappa were "unchanged by the change
## (0.30, 1.80, 0.80, 18.00, 0.30)" and that "cellvoltage.csv regenerates byte-identically".
## BOTH WERE FALSE, and falsified by this file's own output. The same-day kappa sourcing pass
## (docs/KAPPA_SOURCING_DOSSIER.md) had already moved two registry rows, so switching to the
## CSV moved the emitted values with them:
##     0.25 M Bu4NBF4/MeCN   18.0 -> 18.9  mS/cm   (1.80  -> 1.89  S/m, +5.0 %)
##     1 M NaOH aq          180.0 -> 178.0 mS/cm   (18.00 -> 17.80 S/m, -1.1 %)
## 40 of the 100 data rows of cellvoltage.csv therefore changed — the 20 MeCN rows and the
## 20 aq. NaOH rows — and the other 60 are byte-identical. THREE columns moved in those 40
## rows, not two: kappa_Sm, E_cell_V and Q_W_cm2. An earlier version of this note said "BOTH
## E_cell_V and Q_W_cm2", which omitted kappa_Sm — the column that is the CAUSE of the other
## two, and the only one in which the registry change is directly visible. electrolyte,
## gap_label, gap_m and i_mAcm2 are unchanged in all 100 rows. Verified by diffing
## julia/cellvoltage.csv against julia/cellvoltage.csv.bak_preFinalPass field by field:
## 40 rows differ, and within them kappa_Sm differs 40/40, E_cell_V 40/40, Q_W_cm2 40/40.
## The pre-pass output is preserved verbatim as julia/cellvoltage.csv.bak_preFinalPass; the
## current file is what the registry now produces. Two of the five kappa did move, so any
## downstream number quoted from a cellvoltage.csv older than 2026-08-02 must be re-checked
## against those two electrolytes before it is trusted.
##
## THE FIVE ROWS AS THE REGISTRY NOW STANDS. Each must carry status `registered` in
## data/electrolytes.csv; `read_kappa` throws if it does not, or if the name is absent.
## The right-hand column is the `state` field, i.e. the three-state provenance class of
## docs/PROVENANCE_STANDARD.md. THEY ARE NOT ALL ASSUMPTIONS — this header said they were,
## and two of them are now state B:
##     3.0 M LiBr/THF               3.0 mS/cm -> 0.30  S/m   assumption
##     0.25 M Bu4NBF4/MeCN         18.9 mS/cm -> 1.89  S/m   DERIVED  (Casteel-Amis fit)
##     0.2 M NaI/DMF                8.0 mS/cm -> 0.80  S/m   assumption
##     1 M NaOH aq                178.0 mS/cm -> 17.80 S/m   DERIVED  (CRC Sect. 5, p. 5-71)
##     0.3 wt% H2SO4/MeOH (BASF)    3.0 mS/cm -> 0.30  S/m   assumption (scale row; no §S6 claim)
## Three assumptions, two derived. The citation, the sensitivity band and the margin at which
## each supported statement flips belong to the registry row and to SI Table S4/S7f, not to
## this file; this file states no bound of its own. `read_kappa` divides the CSV's mS/cm by
## 10, and for these five that division is exact in Float64 (18.9/10 === 1.89 and
## 178.0/10 === 17.8 both hold), so nothing is lost in the unit conversion.
## The first four are the same four electrolytes as figs/thermal_model.py SOLVENTS, which
## remains the narrative single source of truth for §S6 and Fig. K.
##
## RESIDUAL COUPLING, stated rather than left implicit — and narrower than it was.
## data/electrolytes.csv is itself generated by data/build_reactions50.py from the
## ELECTROLYTES dict there, which is the true upstream of every value below.
## figs/thermal_model.py still holds a hand-maintained copy of the first four that Julia
## cannot import, but that copy is no longer unchecked: its `_check_registry()` asserts at
## import that both the VALUE and the provenance STATE of each of its four rows equal
## data/electrolytes.csv, and raises otherwise (it is silent only if the CSV is missing).
## The earlier warning here — that a revision of thermal_model.py alone would leave this
## file "emitting the old value without complaint" — no longer describes the code: that
## particular drift now fails loudly on the Python side. What is STILL unguarded is the
## direction neither file can see: nothing checks build_reactions50.py against the CSV at
## read time, so regenerating electrolytes.csv from a stale dict would propagate here
## unopposed.
##
## FOUR ENTRIES WERE REMOVED HERE AND MUST NOT BE REINTRODUCED. §S6.1 and the Table S4
## caption retract them by name, so shipping them let a reviewer regenerate the retracted
## claim from the shipped code. All four DO appear as rows of data/electrolytes.csv; three
## carry the status string `unused-legacy (no registry row)`, which `read_kappa` rejects,
## and one is `registered`, which it does not — so for that one the guard below is not a
## substitute for this note. Values are the S/m this file used to ship:
##     "0.1 M Bu4NPF6 / THF"        0.06  -- status `unused-legacy (no registry row)`.
##         The registry now carries 0.51 mS/cm (= 0.051 S/m) as MEASURED for this salt,
##         which is not the 0.6 mS/cm implied by the retracted 0.06 S/m.
##     "0.1 M Bu4NBF4 / DMF"        0.35  -- status `unused-legacy (no registry row)` (3.5 mS/cm)
##     "1 M KOH (aq)"              20.0   -- status `unused-legacy (no registry row)` (200 mS/cm)
##     "0.1 M Bu4NBF4 / MeCN"       0.90  -- THE ONE `read_kappa` WOULD ACCEPT: its row is
##         `registered` (now 9.9 mS/cm = 0.99 S/m, derived — no longer the 0.90 S/m shipped
##         here). It is excluded on editorial grounds: figs/thermal_model.py names 0.90
##         explicitly as part of the UNREGISTERED set that the 2026-08 thermal reconciliation
##         replaced, and shipping it beside the figK MeCN row (now 1.89 S/m) would put two
##         near-identically-labelled MeCN conductivities in one file. Removed for that
##         reason, not because the row is unregistered.
## Prior file: _archive/retracted_electrolytes_20260802/julia/cellvoltage.jl

const ELYTE_CSV = joinpath(@__DIR__, "..", "data", "electrolytes.csv")

"""
    read_kappa(name) -> Float64

kappa in S/m for `name`, read from data/electrolytes.csv (columns
electrolyte,kappa_mScm,state,status). Errors if the row is absent or its status is not
`registered`, so a retracted or unregistered electrolyte cannot reach cellvoltage.csv
by a typo. Stdlib only, matching the rest of the Julia model; no field of that file
contains a comma, so a plain split is sufficient and is checked below.
"""
function read_kappa(name::AbstractString)
    for (n, line) in enumerate(eachline(ELYTE_CSV))
        n == 1 && continue                       # header
        isempty(strip(line)) && continue
        fields = split(line, ',')
        length(fields) == 4 || error("electrolytes.csv line $n has $(length(fields)) " *
                                     "fields, expected 4 (an embedded comma?): $line")
        if fields[1] == name
            fields[4] == "registered" ||
                error("electrolytes.csv: '$name' has status '$(fields[4])', not " *
                      "'registered'; it must not be used in the cell-voltage stack.")
            return parse(Float64, fields[2]) / 10.0     # mS/cm -> S/m
        end
    end
    error("electrolytes.csv: no row named '$name'")
end

const ELECS = [Electrolyte(lab, key, read_kappa(key)) for (lab, key) in
    [("3.0 M LiBr / THF",            "3.0 M LiBr/THF"),
     ("0.25 M Bu4NBF4 / MeCN",       "0.25 M Bu4NBF4/MeCN"),
     ("0.2 M NaI / DMF",             "0.2 M NaI/DMF"),
     ("1 M NaOH (aq)",               "1 M NaOH aq"),
     ("0.3 wt% H2SO4 / MeOH (BASF)", "0.3 wt% H2SO4/MeOH (BASF)")]]

const GAPS = [("beaker, 2 cm", 2.0e-2), ("batch, 5 mm", 5.0e-3),
              ("flow, 1 mm", 1.0e-3), ("thin gap, 250 um", 2.5e-4)]

function E_cell(i_mAcm2::Float64, kappa::Float64, gap::Float64;
                E0 = 2.0, b = 2 * RT_F, i0 = 1.0)
    i_SI = i_mAcm2 * 10.0                       # A/m^2
    eta_kin = 2 * b * asinh(i_mAcm2 / (2 * i0)) # both electrodes
    return E0 + eta_kin + i_SI * gap / kappa
end

Q_joule_Wcm2(i_mAcm2, kappa, gap) = (i_mAcm2 * 10.0)^2 * gap / kappa * 1e-4

## time to heat a batch by dT: m cp dT / (Q * A). Worked example in runner.
