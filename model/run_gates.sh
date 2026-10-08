#!/bin/bash
# Run every Section 4 gate and report one line each.
#
#   cd Section4_Model && ./run_gates.sh            # fast gates only (seconds)
#   cd Section4_Model && ./run_gates.sh --all      # + the sensitivity sweeps (tens of minutes;
#                                                  #   each re-solves the 50x6 matrix repeatedly)
#
# A gate is a FALSIFIABLE check with a negative control wherever one is meaningful. The three
# sensitivity sweeps are separated because they are expensive, not because they are optional --
# they are what converts "this number is unsourced" into "and here is what not knowing it costs".
set -u
cd "$(dirname "$0")"
PY=python3

# THE SENSITIVITY SWEEPS MUTATE SHARED SOLVER ARTIFACTS IN PLACE.
# sensitivity_carrier_charge.py and its siblings perturb data/carrier_charge.csv and
# julia/all50_np_matrix.csv, re-solve, and restore the originals from a .zsens copy in a
# `finally`. While one is in flight the matrix on disk is a PARTIAL, PERTURBED file -- for a
# while it holds 8 rows of 300 -- and any gate reading it reports failures that mean nothing.
# That happened on 2026-08-25: a --all run in the background made G-NUMERIC report 20 merge
# failures against a matrix that was mid-write. Refuse to start rather than produce a verdict
# nobody can trust.
# THE LIST USED TO BE TYPED, AND THAT IS TRAP 10 IN CLAUDE.md.
# It named four paths. On 2026-08-30 the two sentinels actually on disk were
# julia/run_mediated.jl.ksens and julia/mediated_ec_matrix.csv.ksens -- left by a k-sweep that
# was SIGKILLed on 2026-08-26, so its `finally` never ran -- and NEITHER was in the list.
# Both happened to be byte-identical to their live files, so the all-clear was CORRECT that day;
# the hole was latent, not realized. It is still a hole: had that sweep been killed one step
# earlier the matrix would have been perturbed, invisibly. DISCOVER the sentinels, never
# enumerate them, and decide by COMPARING rather than by the filename being on a list.
#
# A sentinel that is byte-identical to its live file is a provable ORPHAN: the restore completed
# (or never perturbed that file) and only the unlink was lost. Say so and continue. Any sentinel
# that DIFFERS means the live file is perturbed or partial -- refuse, and name the restore.
_dirty=0; _orphan=0
while IFS= read -r _z; do
  [ -n "$_z" ] || continue
  _live="${_z%.*}"
  if [ -e "$_live" ] && cmp -s "$_live" "$_z"; then
    _orphan=$((_orphan+1))
    echo "note: orphaned sentinel $_z (identical to $_live -- a killed sweep, already restored)"
  else
    _dirty=$((_dirty+1))
    echo "REFUSING TO RUN: $_z exists and $_live DIFFERS from it, so a sensitivity sweep is in"
    echo "  flight or died mid-perturbation and the solver artifacts on disk are perturbed or"
    echo "  partial. Wait for it to finish (it restores in a finally block); if it is dead,"
    echo "  restore with:  cp \"$_z\" \"$_live\" && rm \"$_z\""
  fi
done <<EOF
$(find julia data figs -maxdepth 1 \( -name '*.zsens' -o -name '*.dsens' -o -name '*.ksens' \) 2>/dev/null)
EOF
if [ "$_dirty" -gt 0 ]; then exit 2; fi
[ "$_orphan" -gt 0 ] && echo "  ($_orphan orphaned sentinel(s); harmless, delete at leisure)"
# The figure-side gates import matplotlib/mpl_fontkit, which only the anaconda 3.12
# interpreter has (CLAUDE.md trap 8). Fall back to PY if it is absent.
PYFIG=/opt/anaconda3/bin/python3.12
[ -x "$PYFIG" ] || PYFIG=$PY
export MPLBACKEND=Agg
pass=0; fail=0; skip=0

# A GATE'S EXIT CODE IS NOT ITS VERDICT.
#
# The first run of this suite reported 10 passed / 2 failed. Two of the "passes" were wrong:
#   G-COND    exited 0 while printing "G-COND: REVIEW NEEDED"
#   G-NUMERIC exited 0 while printing "[FAIL] SI-claims: EC' flow >=50 (12, 15) vs SI 13->14"
# Both scripts simply never call sys.exit with a status. Believing the exit code over the gate's
# own stated conclusion is the same failure this whole audit has been about: a check that cannot
# fail for the reason you care about. The verdict text now wins, and the exit code is only the
# fallback when a gate says nothing explicit.
run () {  # run <label> <command...>
  local label="$1"; shift
  local out rc
  out=$("$@" 2>&1); rc=$?
  # KEEP THE WHOLE OUTPUT. Only the last line is printed here, and for a 90-minute sweep that
  # means its findings are unrecoverable without running it again: G-ZSENS reported "6
  # alternative(s) change a published count" and WHICH SIX was thrown away.
  mkdir -p results/gate_logs
  printf '%s\n' "$out" > "results/gate_logs/${label}.log"
  # Read the gate's OWN verdict line -- "G-SOMETHING: PASS" / ": FAIL" / ": REVIEW NEEDED" --
  # and believe that over the exit status. Matching loose keywords anywhere in the output does not
  # work: the first attempt at this flagged G-ORPHAN as failing because its PASS line contains the
  # word "ORPHAN", and G-MSCITE because a citation it listed contained a matching token. A gate's
  # name is not a verdict. Only when a gate prints no verdict line at all does the exit code decide.
  local verdict
  # A CONTROL RUN'S VERDICT IS THE CONTROL'S LINE, NOT THE GATE'S. When a control fires, the gate
  # it perturbs correctly prints its own FAIL -- that IS the control succeeding. Taking the last
  # standard verdict line therefore read G-NAMES-NEG and G-ORPHAN-NEG as failures while their own
  # lines said "G-NAMES control: GOOD". Prefer a "<gate> control: GOOD|BAD" line whenever one is
  # present; fall back to the plain verdict otherwise.
  verdict=$(echo "$out" | grep -oE "^[[:space:]]*G-[A-Z0-9-]+[[:space:]]*control:[[:space:]]*(GOOD|BAD)" | tail -1)
  [ -n "$verdict" ] || verdict=$(echo "$out" | grep -oE "^[[:space:]]*G-[A-Z0-9-]+:[[:space:]]*control[[:space:]]+(GOOD|BAD)" | tail -1)
  [ -n "$verdict" ] || verdict=$(echo "$out" | grep -oE "^[[:space:]]*G-[A-Z0-9-]+:[[:space:]]*(PASS|FAIL|REVIEW NEEDED|GOOD|BAD)" | tail -1)
  if [ -n "$verdict" ]; then
    case "$verdict" in
      *PASS*|*GOOD*) rc=0 ;;
      *)             rc=1 ;;
    esac
  elif echo "$out" | grep -qE "^\[FAIL\]|AssertionError"; then
    rc=1
  fi
  if [ $rc -eq 0 ]; then
    printf '  \033[32mPASS\033[0m  %-22s %s\n' "$label" "$(echo "$out" | tail -1 | cut -c1-92)"
    pass=$((pass+1))
  else
    printf '  \033[31mFAIL\033[0m  %-22s %s\n' "$label" "$(echo "$out" | tail -1 | cut -c1-92)"
    fail=$((fail+1))
  fi
}

echo "=== structural gates ==="
run G-ORPHAN   $PY data/check_orphans.py
run G-NAMES    $PY data/check_reaction_names.py
# G-STOICH (2026-10-05): the balanced reaction behind every row (SI Table S10). The builder asserts atom
# and charge balance, that each row's electrons are the reaction table's n, and that the electrode is
# the one electrode_direction.csv carries; it needs RDKit, and a missing interpreter is a FAIL, not a skip.
RDPY=/opt/anaconda3/envs/echem_analysis/bin/python
run G-STOICH   $RDPY data/build_reaction_stoichiometry.py --check
# G-RXNTABLE (2026-10-05): SI Table S10 audited AS BUILT -- compositions recomputed by a second parser that
# shares nothing with RDKit, and the printed equations, charges, electron counts and electrodes read back
# out of both SI documents.
run G-RXNTABLE $RDPY data/check_reaction_table.py
# G-KBASIS (2026-10-05): every rate constant the solvers use has a record of the system it was MEASURED on
# (data/rate_constant_basis.csv); the record's k equals the solver's and SI Table S11 reads back from both builds.
run G-KBASIS $PYFIG data/check_rate_constant_basis.py

echo "=== provenance gates ==="
run G-COND     $PY data/check_conditions.py
run G-CODECONST $PY data/check_code_constants.py
run G-SPECIES  $PY data/check_species_provenance.py
run G-DSUB     $PY data/check_substrate_D.py
run G-SIBOUNDS $PY data/check_si_bounds.py
run G-KAPPA-CA $PY data/check_kappa_casteel.py
run G-CA       $PY data/casteel_amis.py
run G-ANACONST $PY data/check_analysis_constants.py
run G-REGEN    $PYFIG data/check_regenerates.py
run G-PDFTEXT  $PYFIG data/build_pdftext.py --check
run G-CITE     $PY data/verify_citations.py
run G-MSCITE   $PY data/verify_ms_citations.py

echo "=== derived-value gates ==="
run G-MSDERIVED $PY data/check_ms_derived.py
run G-SIDERIVED $PY data/check_si_derived.py
run G-ECBAND    $PY data/check_ecprime_band.py
run G-NUMERIC   $PY data/audit_numeric.py
run G-MSKAPPA   $PY data/check_ms_numbers.py

# THESE FIVE EXISTED AND NOTHING RAN THEM until 2026-08-25. That is not a bookkeeping detail:
# G-SOLV was carrying a real finding the whole time -- the SI said eleven rows had unsourced
# viscosity where the model flags thirteen, and "at most two entries of fifty" where the sweep
# measures three. A gate outside the runner is a gate nobody reads.
run G-LIVE      $PY data/registry_liveness.py
run G-ASSUME    $PYFIG figs/analysis_assumption_ledger.py
run G-SOLV      $PYFIG figs/analysis_solvent_property_sensitivity.py
run G-STRAT     $PYFIG data/khl_stratification.py --check-si
run G-DSETJ-SI  $PYFIG data/dataset_current_density.py --check-si
run G-MUSOLN    $PYFIG data/sensitivity_solution_viscosity.py
run G-DSTIR     $PYFIG data/delta_stirred_estimate.py
run G-EAVISC    $PYFIG data/ea_viscosity_crc.py
run G-SPECIATE  $PYFIG data/acid_base_speciation.py
run G-DMAMU     $PYFIG data/sensitivity_dma_viscosity.py
run G-MIXBOUND  $PYFIG data/mixture_property_bounds.py
run G-EVERYVAL  $PYFIG data/check_every_value.py
run G-RXNENG    $PYFIG data/reactor_engineering.py
run G-RXNENG-SI $PYFIG data/reactor_engineering.py --check-si
run G-DILUTE    $PYFIG data/dilute_theory_stratify.py
run G-DILUTE-SI $PYFIG data/dilute_theory_stratify.py --check-si
run G-ECPANEL   $PYFIG data/ecprime_panel_sensitivity.py
run G-HINT      $PYFIG data/hint_series_bound.py
run G-THERMGEO  $PYFIG data/thermal_geometry_sensitivity.py
run G-THERMAXIS $PYFIG data/thermal_axis_sweeps.py
run G-THERMROWS $PYFIG data/check_thermal_rows.py
run G-DERIVE    $PYFIG data/check_derived_inputs.py
run G-SCRANGE   $PYFIG data/schmidt_extrapolation.py
run G-GHOST     $PYFIG data/check_ghost_refs.py
run G-FIGRUN    $PYFIG data/check_figures_render.py
run G-NUMCLOSE  $PYFIG data/check_number_closure.py
run G-XDOC      $PYFIG data/check_cross_document.py
run G-PROVPRINT $PYFIG data/check_printed_provenance.py
run G-SIFRESH   $PYFIG data/check_si_fresh.py
# G-SICOND: the condensed pre-review SI (SI_MODE=condensed) against the detailed SI: headings,
# every equation, verbatim prose with the same cited works, every Table S7 row with a derivable
# short locator, Table S2 sources, manuscript targets, reference list, freshness.
run G-SICOND    $PYFIG data/check_si_condensed.py
run G-SIPROSE   $PYFIG data/check_si_prose_numbers.py
run G-VOICE     $PYFIG data/check_deprocessed.py
run G-EXCELL    $PYFIG data/check_excell.py
run G-KSENS-SI  $PYFIG data/sensitivity_rate_constants.py --check-si
# G-DSUBSENS-REG: the fast half of G-DSUBSENS. The sweep itself re-solves the mediated matrix
# once per scale (~15 min, --all only); this re-checks its STORED result against the registry
# row that publishes it, so an undeclared or oversized count movement fails in the fast tier.
run G-DSUBSENS-REG $PYFIG data/sensitivity_substrate_D.py --check-registry
# G-CATK: the eleven catalyst rows under a declared k band (results/catalyst_ec_sensitivity.json).
# Fast tier re-checks the STORED result (control vs the published matrix, no unresolved cell);
# the 45-minute Julia sweep that produces it runs under --all as G-CATK-SWEEP.
run G-CATK $PYFIG data/catalyst_ec_sensitivity.py
# G-PLATEAU (2026-10-05): mediated cells whose concentration-control plateau stops short of full depletion,
# each walked on to the 1e-3 criterion in an isolated solve. Fast tier re-checks the STORED result against
# the matrix; the solve itself (a few minutes) runs under --all as G-PLATEAU-SOLVE.
run G-PLATEAU $PYFIG data/plateau_continuation.py --check
run G-FREECONV  $PYFIG data/free_convection_delta.py
run G-SIBIB     $PYFIG data/verify_si_bibliography.py
run G-TRANSCRIBE $PYFIG data/check_transcription.py
run G-CATD      $PYFIG figs/analysis_catalyst_D_sensitivity.py
# chemistry audit pass 5: the surrogate-anchored catalyst diffusivities (S9.0), the cooling-class verdicts of S6.2 against
# the Table S4 bands, and Reid's specific Le Bas increments with the ferrocene benchmark (S3.1); each writes the artifact
# the SI reads
run G-ANCHOR    $PYFIG figs/anchored_diffusivity.py
run G-COOLFLIP  $PYFIG data/thermal_conditional_flips.py
run G-BORATE   $PYFIG data/hmf_buffer_speciation.py
run G-PYH      $PYFIG data/pyridinium_bracket.py
run G-LEBASINC  $RDPY data/lebas_increment_sensitivity.py
run G-KAPPAT    $PYFIG figs/analysis_kappaT_sensitivity.py
run G-KAPPA     $PYFIG figs/analysis_kappa_value_sensitivity.py
run G-COVER     $PYFIG data/audit_number_coverage.py

echo "=== negative controls (a gate that cannot fail is not a gate) ==="
run G-CODECONST-NEG $PY data/check_code_constants.py --negative-control
run G-DSUB-NEG $PY data/check_substrate_D.py --negative-control
run G-SIBOUNDS-NEG $PY data/check_si_bounds.py --negative-control
run G-SPECIES-NEG $PY data/check_species_provenance.py --negative-control
run G-COND-NEG  $PY data/check_conditions.py --negative-control
run G-NAMES-NEG $PY data/check_reaction_names.py --negative-control
run G-DSETJ-NEG $PYFIG data/dataset_current_density.py --check-si --negative-control
run G-KAPPA-CA-NEG $PY data/check_kappa_casteel.py --negative-control
run G-ORPHAN-NEG $PY data/check_orphans.py --negative-control
run G-MUSOLN-NEG $PYFIG data/sensitivity_solution_viscosity.py --negative-control
run G-DSTIR-NEG $PYFIG data/delta_stirred_estimate.py --negative-control
run G-EAVISC-NEG $PYFIG data/ea_viscosity_crc.py --negative-control
run G-SPECIATE-NEG $PYFIG data/acid_base_speciation.py --negative-control
run G-DMAMU-NEG $PYFIG data/sensitivity_dma_viscosity.py --negative-control
run G-MIXBOUND-NEG $PYFIG data/mixture_property_bounds.py --negative-control
run G-EVERYVAL-NEG $PYFIG data/check_every_value.py --negative-control
run G-RXNENG-NEG $PYFIG data/reactor_engineering.py --negative-control
run G-RXNENG-SI-NEG $PYFIG data/reactor_engineering.py --check-si --negative-control
run G-DILUTE-NEG $PYFIG data/dilute_theory_stratify.py --negative-control
run G-DILUTE-SI-NEG $PYFIG data/dilute_theory_stratify.py --check-si --negative-control
run G-ECPANEL-NEG $PYFIG data/ecprime_panel_sensitivity.py --negative-control
run G-HINT-NEG  $PYFIG data/hint_series_bound.py --negative-control
run G-THERMGEO-NEG $PYFIG data/thermal_geometry_sensitivity.py --negative-control
run G-THERMAXIS-NEG $PYFIG data/thermal_axis_sweeps.py --negative-control
run G-THERMROWS-NEG $PYFIG data/check_thermal_rows.py --negative-control
run G-DERIVE-NEG $PYFIG data/check_derived_inputs.py --negative-control
run G-SCRANGE-NEG $PYFIG data/schmidt_extrapolation.py --negative-control
run G-GHOST-NEG $PYFIG data/check_ghost_refs.py --negative-control
run G-FIGRUN-NEG $PYFIG data/check_figures_render.py --negative-control
run G-NUMCLOSE-NEG $PYFIG data/check_number_closure.py --negative-control
run G-XDOC-NEG  $PYFIG data/check_cross_document.py --negative-control
run G-COOLFLIP-NEG $PYFIG data/thermal_conditional_flips.py --negative-control
run G-LEBASINC-NEG $RDPY data/lebas_increment_sensitivity.py --negative-control
run G-PROVPRINT-NEG $PYFIG data/check_printed_provenance.py --negative-control
run G-SIFRESH-NEG $PYFIG data/check_si_fresh.py --negative-control
run G-SICOND-NEG $PYFIG data/check_si_condensed.py --negative-control
run G-SIPROSE-NEG $PYFIG data/check_si_prose_numbers.py --negative-control
run G-VOICE-NEG $PYFIG data/check_deprocessed.py --negative-control
run G-EXCELL-NEG $PYFIG data/check_excell.py --negative-control
run G-FREECONV-NEG $PYFIG data/free_convection_delta.py --negative-control
run G-SIBIB-NEG $PYFIG data/verify_si_bibliography.py --negative-control
run G-TRANSCRIBE-NEG $PYFIG data/check_transcription.py --negative-control
run G-CATD-NEG  $PYFIG figs/analysis_catalyst_D_sensitivity.py --negative-control
run G-KAPPAT-NEG $PYFIG figs/analysis_kappaT_sensitivity.py --negative-control
run G-KAPPA-NEG $PYFIG figs/analysis_kappa_value_sensitivity.py --negative-control
run G-EXEMPLAR-NEG $PY data/verify_exemplars.py --negative-control
run G-EXEMPLAR2-NEG $PY data/verify_exemplars_full.py --negative-control
run G-ANACONST-NEG $PY data/check_analysis_constants.py --negative-control
run G-REGEN-NEG $PYFIG data/check_regenerates.py --negative-control
run G-DSUBSENS-REG-NEG $PYFIG data/sensitivity_substrate_D.py --check-registry --negative-control
run G-CATK-NEG $PYFIG data/catalyst_ec_sensitivity.py --negative-control
run G-STOICH-NEG $RDPY data/build_reaction_stoichiometry.py --negative-control
run G-RXNTABLE-NEG $RDPY data/check_reaction_table.py --negative-control
run G-KBASIS-NEG $PYFIG data/check_rate_constant_basis.py --negative-control
run G-PLATEAU-NEG $PYFIG data/plateau_continuation.py --negative-control
run G-DIFF-VAL  $PY data/build_ion_diffusivities.py --validate

if [ "${1:-}" = "--all" ]; then
  echo "=== sensitivity sweeps (slow: each re-solves the matrix many times) ==="
  # pass 16: NEGLIGIBLE_C and the residual reference re-measured on the production path, isolated copies (~30 min)
  run G-SOLVSET  $PYFIG data/solver_setting_sweeps.py
  run G-DSENS  $PY data/sensitivity_unsourced_D.py
  run G-ZSENS  $PY data/sensitivity_carrier_charge.py
  # 2026-10-06: the Ni homocoupling's carrier charge at its adopted k (z = +1, +2; ~15 min), read by Table S2 and the registry
  run G-HOMOZ  $PY data/homocoupling_charge_sensitivity.py
  # 2026-10-06 (chemistry audit, pass 4): four sweeps whose results the registry and the SI now read rather than type --
  # the cross-coupling's charge at its sourced k, the doubled solver-species diffusivities, the medium-transfer brackets
  # of three declared diffusivities, and the trace seed of the electrogenerated form (each a few minutes in scratch copies)
  run G-XECZ    $PY data/xec_charge_sensitivity.py
  run G-SPEC2X  $PY data/sensitivity_solver_species_2xD.py
  run G-MEDXFER $PY data/sensitivity_medium_transfer.py
  run G-TRACE   $PY data/sensitivity_trace_init.py
  run G-KSENS  $PY data/sensitivity_rate_constants.py
  run G-DSUBSENS $PY data/sensitivity_substrate_D.py 0.7 1.3
  run G-CATK-SWEEP $PYFIG data/catalyst_ec_sensitivity.py --sweep
  run G-PLATEAU-SOLVE $PYFIG data/plateau_continuation.py
  # 2026-09-11: the seven sourced-k catalyst rows and the Fig. 6h film sweep (julia/run_catalyst_sourced.jl,
  # run_catalyst_delta.jl, ~30 min); the fast-tier G-CATK reads their artifacts and checks them against the sweep grid
  run G-CATK-SOURCED $PYFIG data/catalyst_ec_sensitivity.py --sweep-sourced
  # Crossref sweeps over all 50 rows: minutes each, and they need the network. Their negative
  # controls resolve only three invented citations, so THOSE stay in the fast tier above.
  run G-EXEMPLAR  $PY data/verify_exemplars.py
  run G-EXEMPLAR2 $PY data/verify_exemplars_full.py
else
  echo "=== sensitivity sweeps SKIPPED (pass --all to run them) ==="
  skip=$(sed -n '/^if \[ "\${1:-}" = "--all" \]; then/,/^else/p' "$(basename "$0")" | grep -c '^  run ')   # counted, never typed
  [ "$skip" -gt 0 ] || { echo "run_gates.sh: the slow-tier skip count read 0 -- the --all block header changed"; exit 1; }
fi

echo
echo "$pass passed, $fail failed, $skip skipped"
[ $fail -eq 0 ]
