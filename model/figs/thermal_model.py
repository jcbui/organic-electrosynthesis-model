"""THE lumped thermal model for Section 4. Single source of truth.

Extracted verbatim from make_figK.py (2026-08 remediated version) so that every
figure that makes a thermal statement makes the SAME thermal statement. Before
this module three generators carried three mutually contradictory versions:

  make_figK.py           registry electrolytes (3.0 M LiBr/THF 0.30 S/m,
                         0.25 M Bu4NBF4/MeCN 1.80, 0.2 M NaI/DMF 0.80,
                         1 M NaOH aq 18.0 -- these are the values AS OF THE
                         EXTRACTION; MeCN and NaOH have since moved to 1.89 and
                         17.80 S/m, see the SOLVENTS block below); beaker gap
                         2 cm; U' DERIVED from
                         vessel geometry, U'_passive(beaker) = 0.01438 W/cm2 K
  make_fig4B.py e/f      UNREGISTERED electrolytes (0.1 M Bu4NPF6/THF 0.06 S/m,
                         0.1 M Bu4NBF4/DMF 0.35, MeCN 0.90, 1 M KOH aq 20.0);
                         beaker gap 5 mm; U' ASSUMED = 0.020 "still air",
                         0.18 "stirred bath", 0.30 "PEM-class plates"
  make_figs.py  FIG D    same unregistered electrolytes; cooling shown as three
                         HEAT-FLUX bands (0.005-0.02, 0.05-0.2, 1-10 W/cm2),
                         which are not comparable with a heat-transfer
                         COEFFICIENT (W/cm2 K) without a stated temperature
                         difference -- the two axes were being read as if they
                         were the same quantity

All three are now reconciled onto the figK model: registry electrolytes, gaps
from the REACTORS table, sigma from vessel geometry, cooling classes expressed
as U' bands in W/cm2 K.

MODEL
    q(i)   = [ 2 b asinh(i / 2 i0) + i L / kappa ] * i          [W/cm2]
    T_ss   = T_amb + q(i) / U'
    i_boil : q(i_boil) = U' (T_boil - T_amb)
    U'_req = q(i_design) / (T_boil - T_amb)
    U'_passive = [ (1/h_int + 1/h_ext)^-1 ] * sigma,  sigma = A_ext / A_elec

Conservative by construction: reaction entropy is excluded from q, and
evaporative loss is omitted on BOTH sides because evaporation IS the failure
mode under test.

PROVENANCE. Every constant below is registered in data/parameters_provenance.csv
(category 9) under the three-state standard, exactly as documented in the
make_figK.py docstring -- that file remains the narrative authority for how each
value was classed. Nothing here was introduced, retuned or reclassified by the
extraction: the module is a copy of what make_figK.py already contained, and
make_figK.py now imports it back, so a single edit updates Fig. K, Fig. 4B-def
and FIG D together.

IF YOU CHANGE A CONSTANT, CHANGE IT HERE. Of the two revisions the make_figK.py
docstring listed as pending, the VESSEL AREA ONE WAS APPLIED on 2026-09-13:
sigma is derived from the declared archetype below (0.00996 m2, sigma 9.96) rather
than carried as the external area of a 5 x 8 cm cylinder, which encloses 157 mL and
is not this archetype. The natural-convection band edges (8e-4-2e-2 ->
1.0e-3-1.6e-2) remain deliberately unapplied, matching make_figK.py. The boiling points ARE applied
(CRC 97th ed. Sect. 15, registered as `T_boil: <solvent>`): MeCN 82.0 -> 81.6 C,
THF 66.0, DMF 152.8, water 99.974 -- see the solvent table below. When the other
two are applied, applying them in this file propagates them to all three figures
at once, which is the point of the extraction.
"""
import os as _os
import numpy as np

RT_F = 0.025693     # RT/F at 298.15 K = 8.3145*298.15/96485 (CODATA); not a fitted number
# b = 2RT/F per electrode is the Tafel slope at alpha = 1/2, n = 1 -- Bard & Faulkner,
# "Electrochemical Methods", 2nd edn, Wiley, 2001, ch. 3 (Butler-Volmer and Tafel forms).
# alpha = 1/2 is the only free choice; alpha in [0.3, 0.7] moves the activation term by under
# 60 mV against ohmic terms of 1-50 V in these cells, so nothing here turns on it.
B_TAFEL = 2*RT_F
# i0 IS A DECLARED MODELLING CHOICE, not a measurement -- no source is claimed for it. It is
# registered state C with a sweep: 0.01-10 mA/cm2 across all four Fig. K solvents. It matters
# only where activation heat is comparable to ohmic heat, which is not the regime any published
# verdict sits in; see the registry row 'i0 (exchange current density)' for the sweep result.
I0 = 1.0            # mA/cm2, per electrode
TAMB = 25.0         # C
# H_EXT = h_natural + h_radiation, both registered rows of parameters_provenance.csv:
#   h natural convection (air) = 7 W m-2 K-1 -- Churchill & Chu, Int. J. Heat Mass Transfer
#     1975, 18, 1323-1329; restated as Incropera, DeWitt, Bergman & Lavine, 'Fundamentals of
#     Heat and Mass Transfer', 6th edn, Wiley, Eq. 9.26-9.27 and Table A.4.
#   h radiation (linearized) = 6 W m-2 K-1 -- same registry, linearized about T_amb.
H_EXT = 13.0        # W/m2 K, natural convection + radiation off the outer surface

# (short label, electrolyte as registered, kappa S/m, T_boil C, provenance STATE)
# Three-state standard, docs/PROVENANCE_STANDARD.md: measured / derived / assumption.
#
# 2026-08-02 KAPPA SOURCING PASS (docs/KAPPA_SOURCING_DOSSIER.md). TWO of these four kappa values
# moved, and both moved to DERIVED (state B). None reaches measured (state A).
#   MeCN     1.80 -> 1.89 S/m  (18.0 -> 18.9 mS cm-1, +5.0 pct). Casteel-Amis from the measured fit
#            of Dorn et al., J. Chem. Eng. Data 2024, 69, 1493-1502, Table 3, p. 1499. Band 15-23.
#   aq NaOH 18.00 -> 17.80 S/m (180 -> 178 mS cm-1, -1.1 pct). CRC Handbook Sect. 5, 'Electrical
#            Conductivity of Aqueous Solutions', p. 5-71 + 'Concentrative Properties'. Band 174-182;
#            178 is the band centre, the old 180 sat at its upper edge.
#   THF  0.30 S/m and DMF 0.80 S/m are UNCHANGED and remain ASSUMPTIONS. THF's band tightens from
#            0.5-8.8 to 0.2-6.6 mS cm-1 (state-B floor 0.206 from Lee et al., OPRD 2022); DMF gains
#            a state-B ceiling of 16.38 mS cm-1 but no value.
# NO CONCLUSION FLIPS. The only verdict-adjacent number is the 250 um microfluidic MeCN ceiling,
# 426.1 -> 432.6 mA cm-2 against a 500 mA cm-2 design current; the flip still needs 31.56 mS cm-1,
# which is 94.6 pct of the MEASURED global maximum for that salt in that solvent (33.40 mS cm-1) and
# would require 2.6-4.4x the concentration. The aqueous ceilings move by at most 0.5 pct.
#
# Per-row Fig. K margins (the factor by which kappa must move before the statement each supports
# would flip), recomputed at the adopted values:
#   THF 2.6x for the Fig. K(b) verdicts ONLY. The margin is the SMALLEST of the five, i.e. the
#       verdict that flips first, and that is the STIRRED beaker at 2.62x -- NOT the unstirred
#       beaker at 2.93x, which is where the withdrawn "2.9x" came from. Stirring raises U' from
#       0.01438 to 0.01599 W cm-2 K-1, so its ceiling climbs faster with kappa and it is the
#       first verdict to turn over even though it starts higher (31.1 vs 29.5 mA cm-2). Full
#       set, all five FAIL at kappa = 0.30 S/m: unstirred beaker 2.93x, stirred beaker 2.62x,
#       5 mm flow 3.46x, 250 um microfluidic 39.5x, zero-gap stack UNREACHABLE on kappa at all
#       (at 1000 mA cm-2 the activation term alone puts out 0.71 W cm-2 against 0.043 W cm-2
#       of passive rejection, so no conductivity saves it). Quote 2.6x, not 2.9x.
#       Separately -- 1.30x for the zero-gap 'beyond forced-air' claim and 1.40x for the
#       25 mA cm-2 concession, both of which must be quoted conditionally
#   MeCN 2.6-3.0x beaker & flow (was 2.5-2.9x at 18.0; unstirred beaker 3.02, stirred 3.37,
#        5 mm flow 2.60), 0.60x microfluidic (was 0.57x)
#   DMF 1.08x -- and 1.39x for T_ss ~ 202 C, 1.41x/1.64x for the 10-20 V statement
#   aq. NaOH 10-42x
# The inherited blanket claim 'robust to 2x' is FALSE for DMF and has been withdrawn.
# Every kappa is a row of data/parameters_provenance.csv (category 6) and is
# reproduced with its class and citation in SI Table S4/S7f.
# IF YOU CHANGE A VALUE HERE, CHANGE data/electrolytes.csv IN THE SAME EDIT -- the two are checked
# against each other by the assertion immediately below.
# MeCN and the aqueous reference became MEASURED on 2026-08-22, read off the raw isotherms in the
# Dorn Supporting Information (Tables SI 85 p. 171 and SI 16 p. 61) rather than derived from the
# article body's Casteel-Amis fit. _check_registry below asserts these against electrolytes.csv,
# and it is what caught the change: it failed the moment the registry moved and would not let the
# figure render on stale conductivities.
## BOILING POINTS ARE THE PRINTED CRC VALUES AS OF 2026-08-24, not roundings of them.
## They were previously 66. / 82. / 153. / 100. -- hardcoded here with no registry row, no
## citation and no sensitivity, while every other constant in this file had all three. Retrieved
## from CRC Handbook 97th ed. (Haynes), Sect. 15 "Laboratory Solvents and Other Liquid Reagents",
## pp. 15-13 ff., normal boiling point column -- the same table solvents.csv already cites for mu
## and rho -- with a layout-preserving extraction so the columns stay aligned. The molecular
## weights on those same rows (41.052 / 73.094 / 72.106) match solvents.csv exactly, which pins
## the read. Now registered as `T_boil: <solvent>` in parameters_provenance.csv.
##   THF 66.0, MeCN 81.6, DMF 152.8, water 99.974.
## The aqueous row is 1 M NaOH, for which CRC prints no boiling point; the PURE WATER value is
## used and is CONSERVATIVE for a boil-off ceiling, because 1 M NaOH boils about 0.5 K HIGHER
## (boiling-point elevation), so the real ceiling is slightly above the one reported here.
SOLVENTS = [("THF",      "3.0 M LiBr/THF",      0.30,  66.0,   "assumption"),
            ("MeCN",     "0.25 M Bu4NBF4/MeCN", 1.995, 81.6,   "measured"),
            ("DMF",      "0.2 M NaI/DMF",       0.877, 152.8,  "derived"),
            ("aq. NaOH", "1 M NaOH aq",        17.45,  99.974, "measured")]


def _check_registry():
    """Assert SOLVENTS agrees with data/electrolytes.csv in value AND provenance state.

    The four Fig. K conductivities used to be retyped here with no link back to the registry
    that classes them, which is how make_fig_main.py and julia/cellvoltage.jl drifted onto
    unregistered values. This gate makes the same drift impossible for this module: it fails
    loudly at import if either the number or the state separates from the CSV.
    Silent if the CSV cannot be found (the module must stay importable from a bare checkout).
    """
    import csv as _csv
    import os as _os
    path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                         "data", "electrolytes.csv")
    if not _os.path.exists(path):
        return
    reg = {r["electrolyte"]: r for r in _csv.DictReader(open(path))}
    for lab, elyte, kap, Tb, prov in SOLVENTS:
        row = reg.get(elyte)
        assert row is not None, "Fig. K electrolyte absent from electrolytes.csv: " + elyte
        assert abs(float(row["kappa_mScm"]) - kap*10.0) < 1e-9, (
            "kappa drift for %s: thermal_model %.4f S/m = %.2f mS/cm vs electrolytes.csv %s"
            % (elyte, kap, kap*10.0, row["kappa_mScm"]))
        assert row["state"] == prov, (
            "provenance-state drift for %s: thermal_model '%s' vs electrolytes.csv '%s'"
            % (elyte, prov, row["state"]))


_check_registry()

# -- sigma for the 100 mL beaker: DERIVED from the declared archetype, 2026-09-13 ---------------
# It used to be 0.0125 m2 / 1e-3 m2 = 12.5, described as "a ~5 cm dia x 8 cm cylinder holding
# 100 mL". That cylinder holds 157 mL. The 0.0125 m2 is the external area of a vessel that is not
# this archetype, and it credits about 3 cm of DRY HEADSPACE WALL as rejecting surface.
#
# The archetype declares three things -- a 100 mL charge, a 5 cm inside diameter and a 10 cm2
# electrode -- and the rejecting area is a CONSEQUENCE of them, not a fourth free parameter:
#
#     fill height  h = V / (pi r^2)                = 5.09 cm
#     A_ext          = pi D h + pi r^2             = 0.00800 + 0.00196 = 0.00996 m2
#     sigma          = A_ext / A_elec              = 9.96
#
# Computed here rather than typed, so the construction cannot drift from the declared archetype.
# Same shape as delta (unstirred batch): the METHOD is citable (elementary geometry of the declared
# vessel) and the declared inputs carry their own registry rows and their own sensitivities.
#
# WHAT IT COSTS, measured before adoption and reported in whichever direction it fell: every
# ceiling computed on this sigma drops 10.8-11.4 pct (THF 29.5 -> 26.3, MeCN 87.8 -> 78.2,
# DMF 88.8 -> 79.2, aq. NaOH 282.4 -> 250.2 mA cm-2) and NOT ONE of the 20 architecture-solvent
# verdicts that rest on it changes. The move is conservative: less rejecting surface, lower
# ceilings, the boiling problem stated as slightly worse rather than better.
import math as _math

CELL_VOLUME_M3 = 100e-6        # declared archetype: 100 mL charge
VESSEL_ID_M = 0.05             # declared archetype: 5 cm inside diameter
A_ELEC_M2 = 10e-4              # declared archetype: 10 cm2 electrode
_R_VESSEL = VESSEL_ID_M/2
_FILL_M = CELL_VOLUME_M3/(_math.pi*_R_VESSEL**2)
A_EXT_BEAKER = _math.pi*VESSEL_ID_M*_FILL_M + _math.pi*_R_VESSEL**2   # wetted wall + base, m2
SIGMA_BEAKER = A_EXT_BEAKER/A_ELEC_M2                                  # = 9.963

# ── design currents: the architecture's OWN median transport ceiling ────────────────────────────
# 2026-09-11, author's ruling. Until v93 each reactor carried a DECLARED design current (50, 50,
# 100, 500, 1000 mA cm-2), and three of those were among the five ledger rows the provenance
# standard flags to read before answering a referee. They are replaced by the median limiting
# current the published 50-reaction matrix computes for that architecture -- a number this model
# already publishes in Fig. 5b, not a new assumption -- so the thermal question becomes the one the
# paper actually asks: at the current TRANSPORT allows, can the cell reject the heat? The median is
# a property of the ARCHITECTURE over the fifty reactions; the heat is a property of the SOLVENT
# named beside it, which is why the two can be crossed.
def _design_currents():
    import csv as _csv
    _p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "julia", "tier0_ec_matrix.csv")
    with open(_p, newline="", encoding="utf8") as fh:
        rows = list(_csv.DictReader(fh))
    if len(rows) != 50:
        raise AssertionError("tier0_ec_matrix.csv has %d rows, expected the 50-reaction set" % len(rows))
    out = {}
    for key in ("natural", "stirred", "flow", "anec", "micro", "rde", "rce"):
        vals = sorted(float(r[key]) for r in rows)
        n = len(vals)
        out[key] = 0.5 * (vals[n // 2 - 1] + vals[n // 2]) if n % 2 == 0 else vals[n // 2]
    return out


_IDES = _design_currents()

# The h_int column is an ASSUMPTION in every row (registry: 'h_int (stagnant electrolyte)',
# '(stirred electrolyte)', '(forced flow, 5 mm gap)', '(forced flow, thin gap)'). The source --
# Incropera, DeWitt, Bergman & Lavine, "Fundamentals of Heat and Mass Transfer", 6th edn, Wiley,
# Table 1.1 -- gives RANGES for free and forced convection in liquids and licenses no single
# value, which is why these are state C and not state B. They are not load-bearing: swept
# 50 -> infinity (past the top of that table's liquid band) every boil-off ceiling moves by less
# by -5/+6% about the declared value, because H_EXT is the smaller series conductance throughout
# and no S6.1/S6.2 verdict turns over anywhere in that range. An earlier version of this comment
# said the ceilings move "less than the reporting precision", which is not true -- the registry
# row for these four values has always carried the correct -5/+6% and the DMF beaker ceiling runs
# 84.1 -> 94.5 mA cm-2 across the sweep. The claim that survives is that nothing FLIPS, not that
# nothing moves; see data/hint_series_bound.py (G-HINT).
#
# ── the reactor set: the SEVEN transport archetypes of Fig. 5, plus the zero-gap stack ──────────
# 2026-09-11 (author: "revise it to now have all the same reactor architectures as Figure 5").
# Until v93 this table carried a five-reactor ladder of its own -- unstirred beaker, stirred beaker,
# "5 mm flow cell", "250 um microfluidic", zero-gap stack. The middle two are the ILLUSTRATIVE
# CHANNEL PAIR the transport model RETIRED in v76, when the flow archetypes were re-anchored onto
# cells whose boundary layers are measured (Watkins 2023; Mo 2020). Nothing was wrong with either
# value on its own terms -- the 250 um gap is Watts, Gattrell & Wirth 2011's FEP spacer, measured --
# but from v76 to v93 the two figures put different architectures on the same axis, and no gate saw
# it: every thermal gate compares this table against the registry, and the registry carried the pair.
#
# WHAT A THERMAL ARCHETYPE NEEDS, AND WHERE IT COMES FROM. The transport archetype is fixed by its
# diffusion layer delta; the thermal archetype needs three quite different things -- the ohmic path
# (the inter-electrode GAP), the heat-rejection area ratio (sigma), and the internal film (h_int).
# An exemplar that measures delta does not necessarily state any of them, so each is carried at its
# own provenance state and the ones that are declared are swept (see data/hint_series_bound.py for
# h_int, data/thermal_geometry_sensitivity.py for the gap and sigma).
#
#   archetype     gap                                              sigma            h_int
#   unstirred     2.0 cm  declared archetype (registry row)        12.5  derived    100   declared
#   stirred       2.0 cm  the same vessel                          12.5  derived    800   declared
#   flow          2.0 cm  INHERITED: Watkins' recirculating        12.5  inherited  2000  declared
#                         H-cell is a membrane-divided cell of
#                         beaker scale and its SI states no
#                         electrode separation and no areas
#   micro         25 um   MEASURED: Mo et al. 2020, SI p. 13 --    7.0   declared   5000  declared
#                         "the inter-electrode distance is
#                         controlled by the thickness of FEP
#                         spacer", thinnest 0.001 in = 25 um.
#                         The SAME number the transport model
#                         derives its 12.5 um half-gap film from
#   rde           2.0 cm  INHERITED: a rotating disc turns in a    12.5  derived    2000  declared
#                         beaker; rotation thins delta and moves
#                         no electrode
#   rce           2.44 cm DERIVED: Eisenberg, Tobias & Wilke       12.5  inherited  2000  declared
#                         1954 p. 308 build the correlation in a
#                         concentric cell with rotors of 1.273,
#                         2.48 and 5.024 cm diameter inside outer
#                         cylinders of 6.07, 9.87 and 13.69 cm ID
#                         (gap/d_inner 0.104-4.88, which those
#                         dimensions reproduce). At the 1.2 cm
#                         rotor this model turns, the TIGHTEST
#                         annulus his cell offers is
#                         (6.07 - 1.2)/2 = 2.44 cm; his widest is
#                         6.25 cm, and that is the row's band
#   zero-gap      100 um  declared (industrial reference, not a    0.8   declared   5000  declared
#                         modelled archetype: Fig. 5 reaches no
#                         Tier-4 cell)
#
# THE RESULT THIS TABLE MAKES VISIBLE, and the reason the two ladders are worth putting on one axis:
# FOUR of the six preparative archetypes share the 2 cm ohmic path. Rotating an electrode thins the diffusion
# layer twentyfold and moves no electrode, so it buys nothing thermally; only the microfluidic cell,
# which thins the GAP, moves the boil-off ceiling. Transport intensification and thermal
# intensification are different axes, and this is where that shows.
GAP_BEAKER = 2.0e-2          # m, the declared 100 mL beaker archetype (registry row)
GAP_MICRO = 2.5e-5           # m, Mo 2020 SI p. 13: 0.001 in FEP spacer
GAP_RCE = 2.435e-2           # m, (6.07 - 1.2)/2 cm, Eisenberg's tightest annulus at this rotor
REACTOR_KEYS = ["natural", "stirred", "flow", "micro", "rde", "rce", None]

# (label, gap m, sigma = A_ext/A_elec, h_int W/m2 K, design current mA/cm2)
REACTORS = [("unstirred\nbatch",        GAP_BEAKER, SIGMA_BEAKER,  100., _IDES["natural"]),
            ("stirred\nbatch",          GAP_BEAKER, SIGMA_BEAKER,  800., _IDES["stirred"]),
            ("recirculating\nflow",     GAP_BEAKER, SIGMA_BEAKER, 2000., _IDES["flow"]),
            ("microfluidic\n25 $\\mu$m", GAP_MICRO,  7.0,         5000., _IDES["micro"]),
            ("RDE\n1600 rpm",           GAP_BEAKER, SIGMA_BEAKER, 2000., _IDES["rde"]),
            ("rotating cyl.\n3000 rpm", GAP_RCE,    SIGMA_BEAKER, 2000., _IDES["rce"]),
            ("zero-gap\nPEM stack",     1.0e-4,     0.8,          5000., 1000.)]

# Cooling classes as heat-rejection COEFFICIENTS (W/cm2 K), not heat fluxes.
# All three are state C. Incropera 6th edn is the source for the two forced classes:
#   forced air         -- Table 1.1, forced convection in gases, 25-250 W m-2 K-1
#   liquid cold plate  -- Table 8.1 and Eq. 8.53 (laminar internal flow); Eq. 8.60
#                         (Dittus-Boelter) for the turbulent end
# natural convection carries NO external locator: its edges are derived from this file's own
# H_EXT and sigma rows, then ROUNDED OUTWARD by about 25%, which visually credits the passive
# class with more rejection than the model actually has. That rounding is declared in the
# registry rather than quietly tightened, because the Fig. 5 verdicts are read off the band
# edges and narrowing them here would move published conclusions.
COOLING_BANDS = [("natural convection\n(passive)", 8e-4, 2e-2, "0.88"),
                 ("forced air",                    2e-2, 8e-2, "0.80"),
                 ("liquid cold plate\n(PEM-class)", 2e-1, 1.0, "0.70")]


def U_passive(sigma, h_int):
    """Series internal + external film, referred to electrode area (W/cm2 K)."""
    return (1.0/(1.0/h_int + 1.0/H_EXT))*sigma*1e-4


def q_Wcm2(i, kappa, gap):
    """Dissipated heat per electrode area. i in mA/cm2, kappa S/m, gap m."""
    i_SI = i*10.0
    return (2*B_TAFEL*np.arcsinh(i/(2*I0)) + i_SI*gap/kappa)*i_SI*1e-4


def E_cell(i, kappa, gap, E0=2.0):
    """Full cell voltage: thermodynamic+kinetic floor, 2 asinh electrodes, ohmic."""
    return E0 + 2*(2*RT_F)*np.arcsinh(i/(2*I0)) + i*10.0*gap/kappa


def i_boil(kappa, gap, Tb, U):
    """Current density at which T_ss reaches Tb, by bisection in log i."""
    target = U*(Tb - TAMB)
    lo, hi = 1e-3, 1e6
    for _ in range(90):
        mid = np.sqrt(lo*hi)
        if q_Wcm2(mid, kappa, gap) > target:
            hi = mid
        else:
            lo = mid
    return np.sqrt(lo*hi)


def U_required(i_op, kappa, gap, Tb):
    """Heat-rejection coefficient needed to hold i_op with T_ss = T_boil."""
    return q_Wcm2(i_op, kappa, gap)/(Tb - TAMB)


def T_ss(i, kappa, gap, U):
    return TAMB + q_Wcm2(i, kappa, gap)/U


BEAKER = REACTORS[0]                       # unstirred 100 mL beaker
U_BEAKER = U_passive(BEAKER[2], BEAKER[3])  # 0.014381 W/cm2 K


if __name__ == "__main__":
    print("U'_passive by architecture (W/cm2 K)")
    for lab, L, sig, hi, iop in REACTORS:
        print("  %-26s L=%7.3f mm sigma=%5.1f h_int=%6.0f  U'=%.5f  i_design=%6.0f"
              % (lab.replace("\n", " "), L*1e3, sig, hi, U_passive(sig, hi), iop))
    print("\nunstirred beaker ceilings (mA/cm2), passive U' = %.5f" % U_BEAKER)
    for lab, el, kap, Tb, prov in SOLVENTS:
        print("  %-9s %-22s kappa=%6.2f  i_boil=%8.1f" %
              (lab, el, kap, i_boil(kap, BEAKER[1], Tb, U_BEAKER)))
