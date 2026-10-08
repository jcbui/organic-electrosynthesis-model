#!/usr/bin/env python3
"""G-REGEN -- every GENERATED data artifact must equal what its generator produces today.

    cd Section4_Model && python data/check_regenerates.py
    cd Section4_Model && python data/check_regenerates.py --negative-control

WHY THIS EXISTS
---------------
On 2026-08-31 `data/reactions_50.csv` and `julia/reactions_table.jl` were found to disagree with
`data/build_reactions50.py`, which writes both. The generator carried the corrected thiocyanation
conditions -- 5 mmol substrate and 2 mmol NH4SCN in 30 mL, i.e. 0.1667 M and 0.0667 M, read from
the article body -- while the two shipped artifacts still carried the superseded 0.25 M and 0.1 M.
The fix had been made in the generator and the artifacts were never regenerated.

That is not a cosmetic drift. `reactions_table.jl` is what the Julia solvers read, so every
ceiling for that row had been computed at 1.5x its own page-verified concentration, and two
published threshold counts turn on it.

NOTHING WAS CHECKING THIS, and the shape generalises: the repository has gates comparing code to
the registry (G-CODECONST), prose to the model (G-MSDERIVED, G-SIDERIVED), and figures to their
renders (verify_*.py G1) -- but nothing compared a GENERATED FILE to its GENERATOR. A fix applied
to the producer and never propagated is invisible to all of them.

HOW IT WORKS
------------
Copy the generator and its inputs into a scratch tree, run it there, and require the artifacts it
writes to be byte-identical to the ones in the repository. The generator is never run against the
real tree, so this gate cannot itself overwrite production data -- which matters, because the
thing being tested is a file the solvers depend on.
"""
import filecmp
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# generator -> (inputs it reads, artifacts it writes as (repo_path, path_within_scratch))
GENERATORS = [
    {
        "script": os.path.join(HERE, "build_reactions50.py"),
        # solvents.csv and electrolytes.csv are OUTPUTS of this generator, not inputs. The first
        # version of this gate listed them as inputs and copied them in, which hid the very defect
        # the gate exists for: an edit made to solvents.csv BY HAND (a corrected CRC cross-check
        # note, 2026-08-31) was not in the generator and would have been silently reverted on the
        # next regeneration. Classify by who WRITES the file, never by who reads it.
        "inputs": [],
        "outputs": [(os.path.join(HERE, "reactions_50.csv"), "data/reactions_50.csv"),
                    (os.path.join(HERE, "solvents.csv"), "data/solvents.csv"),
                    (os.path.join(HERE, "electrolytes.csv"), "data/electrolytes.csv"),
                    (os.path.join(ROOT, "julia", "reactions_table.jl"), "julia/reactions_table.jl")],
        "needs": "rdkit",
    },
    {
        # Writes the registry that Tables S2 and S7 are built from, so a drift here reaches the
        # published document directly. Its inputs are the three data CSVs, the kappa(T) bracket
        # and the Schmidt-extrapolation JSON -- the Eisenberg row interpolates its numbers from
        # the latter so that row cannot go stale, and omitting it here made this gate fail with
        # "a shipped artifact is not what its generator produces" the moment that was wired up.
        "script": os.path.join(HERE, "build_param_tables.py"),
        "inputs": [(os.path.join(HERE, "solvents.csv"), "data/solvents.csv"),
                   # chemistry audit pass 5: registry sentences computed from these
                   (os.path.join(HERE, "electrolyte_ions.csv"), "data/electrolyte_ions.csv"),
                   (os.path.join(HERE, "sensitivity_solution_viscosity.py"), "data/sensitivity_solution_viscosity.py"),
                   (os.path.join(ROOT, "results", "kappa_derivation.json"), "results/kappa_derivation.json"),
                   (os.path.join(ROOT, "results", "lebas_increment_sensitivity.json"), "results/lebas_increment_sensitivity.json"),
                   (os.path.join(ROOT, "julia", "audit_gates.csv"), "julia/audit_gates.csv"),
                   (os.path.join(ROOT, "julia", "run_mediated.jl"), "julia/run_mediated.jl"),
                   (os.path.join(ROOT, "julia", "emit_deltas.jl"), "julia/emit_deltas.jl"),
                   (os.path.join(HERE, "electrolytes.csv"), "data/electrolytes.csv"),
                   (os.path.join(HERE, "reactions_50.csv"), "data/reactions_50.csv"),
                   (os.path.join(ROOT, "results", "figK_kappaT_sensitivity.json"),
                    "results/figK_kappaT_sensitivity.json"),
                   (os.path.join(ROOT, "results", "schmidt_extrapolation.json"),
                    "results/schmidt_extrapolation.json"),
                   # audit pass 30: the cooling class along the stack gap/current, inherited sigma and charge
                   (os.path.join(ROOT, "results", "thermal_axis_sweeps.json"), "results/thermal_axis_sweeps.json"),
                   # 2026-09-12: the seven-archetype thermal table. The registry's inherited-gap
                   # sensitivity reads the sweep, and the MeCN row recomputes its own margins from
                   # the same module the figure draws from, so both are inputs now.
                   (os.path.join(ROOT, "results", "thermal_geometry_sensitivity.json"),
                    "results/thermal_geometry_sensitivity.json"),
                   (os.path.join(ROOT, "figs", "thermal_model.py"), "figs/thermal_model.py"),
                   (os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"),
                    "julia/tier0_ec_matrix.csv"),
                   # chemistry audit pass 3: the stirred-film row reads the unstirred archetype's film from here
                   (os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"),
                    "julia/mediated_ec_matrix.csv"),
                   # chemistry audit pass 4: the free-convection row reads the concentrated-row count from here
                   (os.path.join(ROOT, "results", "dilute_theory_stratify.json"),
                    "results/dilute_theory_stratify.json"),
                   (os.path.join(ROOT, "results", "excell.json"), "results/excell.json"),
                   # pass 16: the NEGLIGIBLE_C row reads the threshold sweep on the production path
                   (os.path.join(ROOT, "results", "negligible_c_sweep.json"), "results/negligible_c_sweep.json"),
                   (os.path.join(ROOT, "results", "cref_scale_sweep.json"), "results/cref_scale_sweep.json"),
                   # pass 17: the c_ref row reads the ex-cell mesh's first cell from run_excell.jl's own signature
                   (os.path.join(ROOT, "julia", "run_excell.jl"), "julia/run_excell.jl"),
                   # 2026-10-07: the borate speciation and the pyridinium bracket
                   (os.path.join(ROOT, "results", "hmf_buffer_speciation.json"), "results/hmf_buffer_speciation.json"),
                   (os.path.join(ROOT, "results", "pyridinium_bracket.json"), "results/pyridinium_bracket.json"),
                   (os.path.join(ROOT, "results", "free_convection_delta.json"),
                    "results/free_convection_delta.json"),
                   (os.path.join(ROOT, "results", "unsourced_D_sensitivity.json"),
                    "results/unsourced_D_sensitivity.json"),
                   (os.path.join(ROOT, "results", "carrier_charge_sensitivity.json"),
                    "results/carrier_charge_sensitivity.json"),
                   (os.path.join(ROOT, "results", "rate_constant_sensitivity.json"),
                    "results/rate_constant_sensitivity.json"),
                   (os.path.join(ROOT, "results", "substrate_D_sensitivity.json"),
                    "results/substrate_D_sensitivity.json"),
                   (os.path.join(ROOT, "results", "catalyst_ec_sensitivity.json"),
                    "results/catalyst_ec_sensitivity.json"),
                   # chemistry audit pass 6: the Casteel-Amis rows are computed by casteel_amis.py on Dorn's isotherms,
                   # the channel-pair row reads reactor_engineering.json, the Ea row both viscosity-Ea artifacts
                   (os.path.join(HERE, "casteel_amis.py"), "data/casteel_amis.py"),
                   (os.path.join(HERE, "dorn_isotherms.csv"), "data/dorn_isotherms.csv"),
                   (os.path.join(ROOT, "figs", "archetype_bands.py"), "figs/archetype_bands.py"),
                   (os.path.join(ROOT, "results", "reactor_engineering.json"), "results/reactor_engineering.json"),
                   (os.path.join(ROOT, "results", "ea_viscosity_crc.json"), "results/ea_viscosity_crc.json"),
                   (os.path.join(ROOT, "results", "ea_viscosity_water.json"), "results/ea_viscosity_water.json"),
                   # 2026-09-11: the DMA-viscosity and catalyst-radius sensitivities feed two registry rows
                   (os.path.join(ROOT, "results", "dma_viscosity_sensitivity.json"),
                    "results/dma_viscosity_sensitivity.json"),
                   (os.path.join(ROOT, "results", "catalyst_D_sensitivity.json"),
                    "results/catalyst_D_sensitivity.json"),
                   (os.path.join(ROOT, "results", "si_sensitivity_bounds.json"),
                    "results/si_sensitivity_bounds.json"),
                   # 2026-10-06: the viscosity row interpolates the maximum dissolved concentration and the flagged count
                   (os.path.join(ROOT, "results", "solution_viscosity_sensitivity.json"),
                    "results/solution_viscosity_sensitivity.json"),
                   (os.path.join(ROOT, "results", "homocoupling_charge_sensitivity.json"),
                    "results/homocoupling_charge_sensitivity.json"),
                   # 2026-10-06 (chemistry audit, pass 4): the solver-species rows read the doubled-D sweep, the
                   # medium-transfer brackets and the trace-seed sweep
                   (os.path.join(ROOT, "results", "solver_species_2xD.json"), "results/solver_species_2xD.json"),
                   (os.path.join(ROOT, "results", "medium_transfer_brackets.json"), "results/medium_transfer_brackets.json"),
                   (os.path.join(ROOT, "results", "trace_init_sensitivity.json"), "results/trace_init_sensitivity.json"),
                   (os.path.join(ROOT, "results", "xec_charge_sensitivity.json"), "results/xec_charge_sensitivity.json"),
                   (os.path.join(HERE, "carrier_charge.csv"), "data/carrier_charge.csv"),
                   # 2026-10-05: the class counts, the substrate rows and the electron-count row are
                   # computed from the reaction table and its three companions, never typed.
                   (os.path.join(HERE, "catalyst_substrates.csv"), "data/catalyst_substrates.csv"),
                   (os.path.join(HERE, "mediated_substrates.csv"), "data/mediated_substrates.csv"),
                   (os.path.join(HERE, "reaction_stoichiometry.csv"), "data/reaction_stoichiometry.csv"),
                   (os.path.join(ROOT, "julia", "catalyst_ec_sourced.csv"), "julia/catalyst_ec_sourced.csv"),
                   # added 2026-09-07: the builder reads the published matrix to COUNT the reactor
                   # archetypes, after three sensitivity rows shipped "the six architectures" into
                   # Table S7 with seven in the model. This gate caught the undeclared input on the
                   # first run after that change, which is what it is for.
                   (os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"),
                    "julia/tier0_ec_matrix.csv")],
        "outputs": [(os.path.join(HERE, "parameters_provenance.csv"),
                     "data/parameters_provenance.csv")],
        "needs": None,
        "perturb": ("data/solvents.csv", "MeCN,41.05,0.369", "MeCN,41.05,0.500"),
    },
    # 2026-09-05: the supporting-ion table the NP solver reads was NOT reproduced by its own
    # generator -- the Cathodic Giese row carried Na+'s diffusivity (1.334e-9) under an H+ label with
    # a CRC state-A basis string, and regenerating it gave H+'s 9.311e-9. A spectator, so no number
    # moved, but a solver input carried a wrong value under a page-anchored claim for weeks with no
    # gate able to see it. The script rewrites the file it reads; in the scratch tree the shipped
    # copy is the input and the output must come back byte-identical.
    {
        "script": os.path.join(HERE, "apply_ion_diffusivities.py"),
        "inputs": [(os.path.join(HERE, "electrolyte_ions.csv"), "data/electrolyte_ions.csv"),
                   (os.path.join(HERE, "ion_diffusivities.csv"), "data/ion_diffusivities.csv")],
        "outputs": [(os.path.join(HERE, "electrolyte_ions.csv"), "data/electrolyte_ions.csv")],
        "needs": None,
        "perturb": ("data/ion_diffusivities.csv", "9.311e-09", "9.000e-09"),
    },
    {
        # 2026-09-14: the short "Source, page, table" locators the condensed SI prints in Tables S2,
        # S4 and S7, derived from the registry and the 50-reaction table.
        "script": os.path.join(HERE, "build_short_locators.py"),
        "inputs": [(os.path.join(HERE, "parameters_provenance.csv"), "data/parameters_provenance.csv"),
                   (os.path.join(HERE, "reactions_50.csv"), "data/reactions_50.csv"),
                   (os.path.join(ROOT, "results", "registry_liveness.json"), "results/registry_liveness.json")],
        "outputs": [(os.path.join(ROOT, "results", "si_short_locators.json"), "results/si_short_locators.json")],
        "needs": None,
        "perturb": ("data/parameters_provenance.csv", "pp. 6-243 to 6-247", "pp. 6-243 to 6-249"),
    },
    # 2026-10-05: four generators written or wired in by the reaction audit. The two substrate tables
    # import build_reactions50.py for its Le Bas and Wilke-Chang functions, so it is an input to both.
    {
        "script": os.path.join(HERE, "build_mediated_substrates.py"),
        "inputs": [(os.path.join(HERE, "build_reactions50.py"), "data/build_reactions50.py"),
                   (os.path.join(HERE, "solvents.csv"), "data/solvents.csv"),
                   (os.path.join(HERE, "reactions_50.csv"), "data/reactions_50.csv")],
        "outputs": [(os.path.join(HERE, "mediated_substrates.csv"), "data/mediated_substrates.csv")],
        "needs": "rdkit",
        "perturb": ("data/build_mediated_substrates.py", "NC(=O)Cc1ccccc1", "NC(=O)CCc1ccccc1"),
    },
    {
        "script": os.path.join(HERE, "build_catalyst_substrates.py"),
        "inputs": [(os.path.join(HERE, "build_reactions50.py"), "data/build_reactions50.py"),
                   (os.path.join(HERE, "solvents.csv"), "data/solvents.csv"),
                   (os.path.join(HERE, "reactions_50.csv"), "data/reactions_50.csv")],
        "outputs": [(os.path.join(HERE, "catalyst_substrates.csv"), "data/catalyst_substrates.csv")],
        "needs": "rdkit",
        "perturb": ("data/build_catalyst_substrates.py", "Cc1ccc(Br)cc1", "CCc1ccc(Br)cc1"),
    },
    {
        # the balanced reaction behind every row (SI Table S10); it asserts atom and charge balance itself
        "script": os.path.join(HERE, "build_reaction_stoichiometry.py"),
        "inputs": [(os.path.join(HERE, "reactions_50.csv"), "data/reactions_50.csv"),
                   (os.path.join(HERE, "electrode_direction.csv"), "data/electrode_direction.csv")],
        "outputs": [(os.path.join(HERE, "reaction_stoichiometry.csv"), "data/reaction_stoichiometry.csv")],
        "needs": "rdkit",
        "perturb": ("data/electrode_direction.csv", "Benzaldehyde -> benzyl alcohol,cathodic", "Benzaldehyde -> benzyl alcohol,anodic"),
    },
    {
        # Lambda(c) by the Onsager limiting law at the registry viscosities (Table S4 caption, the display-only rows)
        "script": os.path.join(HERE, "derive_kappa.py"),
        "inputs": [(os.path.join(HERE, "solvents.csv"), "data/solvents.csv"),
                   (os.path.join(HERE, "electrolytes.csv"), "data/electrolytes.csv")],
        "outputs": [(os.path.join(ROOT, "results", "kappa_derivation.json"), "results/kappa_derivation.json")],
        "needs": None,
        "perturb": ("data/solvents.csv", "MeCN,41.05,0.369", "MeCN,41.05,0.343"),
    },
    {
        # Reid's specific Le Bas increments against the general ones the model carries, and the ferrocene benchmark
        "script": os.path.join(HERE, "lebas_increment_sensitivity.py"),
        "inputs": [(os.path.join(HERE, "build_reactions50.py"), "data/build_reactions50.py"),
                   (os.path.join(HERE, "reactions_50.csv"), "data/reactions_50.csv"),
                   (os.path.join(HERE, "solvents.csv"), "data/solvents.csv"),
                   (os.path.join(HERE, "mediated_substrates.csv"), "data/mediated_substrates.csv"),
                   (os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"), "julia/tier0_ec_matrix.csv")],
        "outputs": [(os.path.join(ROOT, "results", "lebas_increment_sensitivity.json"), "results/lebas_increment_sensitivity.json")],
        "needs": "rdkit",
        # it reads mu from build_reactions50.SOLVENTS, not from solvents.csv, so the generator source is what to perturb
        "perturb": ("data/build_reactions50.py", '"MeCN":      (41.05, 0.369,', '"MeCN":      (41.05, 0.500,'),
    },
    {
        # the cooling-class verdicts of SI S6.2 against the Table S4 conductivity bands, and the Bu4NPF6/THF example of S6.1
        "script": os.path.join(HERE, "thermal_conditional_flips.py"),
        "inputs": [(os.path.join(ROOT, "figs", "thermal_model.py"), "figs/thermal_model.py"),
                   (os.path.join(HERE, "si_sensitivity_bounds.py"), "data/si_sensitivity_bounds.py"),
                   (os.path.join(HERE, "parameters_provenance.csv"), "data/parameters_provenance.csv"),   # the bands, read at import
                   (os.path.join(HERE, "electrolytes.csv"), "data/electrolytes.csv"),
                   (os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"), "julia/tier0_ec_matrix.csv")],
        "outputs": [(os.path.join(ROOT, "results", "thermal_conditional_flips.json"), "results/thermal_conditional_flips.json")],
        "needs": None,
        "perturb": ("data/electrolytes.csv", "0.1 M Bu4NPF6/THF,0.51", "0.1 M Bu4NPF6/THF,0.60"),
    },
    {
        # the two band-edge mediated solvers are run_mediated.jl with one inserted block and a renamed output
        "script": os.path.join(HERE, "build_bounds_solvers.py"),
        "inputs": [(os.path.join(ROOT, "julia", "run_mediated.jl"), "julia/run_mediated.jl"),
                   (os.path.join(ROOT, "julia", "emit_deltas.jl"), "julia/emit_deltas.jl"),
                   (os.path.join(ROOT, "results", "free_convection_delta.json"), "results/free_convection_delta.json")],
        "outputs": [(os.path.join(ROOT, "julia", "_bounds_lo.jl"), "julia/_bounds_lo.jl"),
                    (os.path.join(ROOT, "julia", "_bounds_hi.jl"), "julia/_bounds_hi.jl")],
        "needs": None,
        "perturb": ("julia/run_mediated.jl", "MATRIX DONE", "MATRIX COMPLETE"),
    },
]
RDKIT_PY = "/opt/anaconda3/envs/echem_analysis/bin/python"

# GENERATORS NOT YET COVERED, declared rather than left silent -- a gate's coverage gap is exactly
# what let the defect above survive, so it should not be discoverable only by reading the list:
#   data/build_param_tables.py      -> data/parameters_provenance.csv
#       Reads solvents/electrolytes/reactions_50 AND several results/*.json, so a scratch run
#       needs that whole input set plumbed in. It is regenerated by hand often enough that it has
#       not drifted, which is luck, not a guarantee.
#   data/build_mediated_substrates.py -> data/mediated_substrates.csv
#   data/build_ion_diffusivities.py   -> data/ion_diffusivities.csv
#   data/build_merged_matrix.py       -> julia/tier0_ec_matrix.csv
#       The last two read julia/all50_np_matrix.csv, which a sensitivity sweep perturbs in place,
#       so they can only be checked when no .zsens sentinel exists.
#   julia/run_excell.jl -> results/excell.json, julia/excell_profiles.csv
#       A Julia solver, not a Python generator: this gate runs only the Python chain. Its output
#       is verified deterministic by running it twice, and every number it publishes is bound to
#       the SI by G-EXCELL, so the artifact cannot drift from the document unnoticed -- but
#       nothing re-derives it here.
UNCOVERED = ["build_ion_diffusivities.py",
             "build_merged_matrix.py", "run_excell.jl (Julia)"]   # apply_ion_diffusivities.py covered 2026-09-05


def interpreter(needs):
    if needs == "rdkit":
        if os.path.exists(RDKIT_PY):
            return RDKIT_PY
        return None
    return sys.executable


def run_one(g, neg=False):
    py = interpreter(g.get("needs"))
    name = os.path.basename(g["script"])
    if py is None:
        # A SKIP MUST BE LOUD. A gate that quietly passes because its interpreter is missing is
        # indistinguishable from a gate that passed.
        print("  %-26s SKIPPED -- %s interpreter not found at %s"
              % (name, g["needs"], RDKIT_PY))
        return None
    tmp = tempfile.mkdtemp(prefix="regen_")
    try:
        os.makedirs(os.path.join(tmp, "data"), exist_ok=True)
        os.makedirs(os.path.join(tmp, "julia"), exist_ok=True)
        os.makedirs(os.path.join(tmp, "results"), exist_ok=True)
        shutil.copy(g["script"], os.path.join(tmp, "data", name))
        for item in g["inputs"]:
            src, rel = item if isinstance(item, (tuple, list)) else (item, "data/" + os.path.basename(item))
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
        if neg:
            # Perturb whatever this generator actually reads: an INPUT file where it has one, and
            # otherwise the generator's own literal (build_reactions50.py carries its data inline).
            rel, old, new = g.get("perturb", ("data/" + name, '"MeCN":      (41.05, 0.369',
                                              '"MeCN":      (41.05, 0.500'))
            gp = os.path.join(tmp, rel)
            t = io.open(gp, encoding="utf-8").read()
            t2 = t.replace(old, new, 1)
            if t2 == t:
                print("  %-26s CONTROL COULD NOT PERTURB (anchor not found in %s)" % (name, rel))
                return False
            io.open(gp, "w", encoding="utf-8").write(t2)
        r = subprocess.run([py, name], cwd=os.path.join(tmp, "data"),
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("  %-26s FAILED TO RUN (exit %d)" % (name, r.returncode))
            print("    " + (r.stderr or r.stdout).strip().splitlines()[-1][:150])
            return False
        bad = []
        for repo_path, rel in g["outputs"]:
            made = os.path.join(tmp, rel)
            if not os.path.exists(made):
                bad.append("%s was not produced" % rel); continue
            if not filecmp.cmp(repo_path, made, shallow=False):
                a = io.open(repo_path, encoding="utf-8", errors="replace").read().split("\n")
                b = io.open(made, encoding="utf-8", errors="replace").read().split("\n")
                n = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
                bad.append("%s differs from what %s produces (%d line(s))"
                           % (os.path.relpath(repo_path, ROOT), name, n))
        if bad:
            print("  %-26s STALE" % name)
            for b in bad:
                print("      " + b)
            return False
        print("  %-26s reproduces byte-identically (%d artifact(s))" % (name, len(g["outputs"])))
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(neg=False):
    print("  regenerating each producer in a scratch tree and comparing to the shipped artifact")
    print("  covered: %d generator(s); NOT yet covered: %s\n"
          % (len(GENERATORS), ", ".join(UNCOVERED)))
    res = [run_one(g, neg) for g in GENERATORS]
    ran = [r for r in res if r is not None]
    if neg:
        # A CONTROL RUN FROM A DIRTY BASELINE PROVES NOTHING (CLAUDE.md trap 23): if a generator
        # already fails unperturbed, "it also failed when perturbed" is not evidence. Judge each
        # generator SEPARATELY, so one stale artifact does not make the whole control unusable --
        # a generator with a clean baseline still gets a real verdict.
        print("\n  (control: re-running unperturbed first, to establish each baseline)")
        base = [run_one(g, neg=False) for g in GENERATORS]
        good, inconclusive, bad = [], [], []
        for g, b, pert in zip(GENERATORS, base, res):
            nm = os.path.basename(g["script"])
            if b is None:
                continue                       # skipped for a missing interpreter; already said so
            if not b:
                inconclusive.append(nm)
            elif pert is False:
                good.append(nm)
            else:
                bad.append(nm)
        print("")
        for nm in good:
            print("  %-26s GOOD -- perturbing its input changes the artifact, against a clean "
                  "baseline" % nm)
        for nm in inconclusive:
            print("  %-26s INCONCLUSIVE -- already stale unperturbed, so this proves nothing; "
                  "regenerate, then re-run" % nm)
        for nm in bad:
            print("  %-26s BAD -- a changed input produced an identical artifact" % nm)
        ok = bool(good) and not bad
        print("\nG-REGEN control: %s"
              % ("GOOD -- %d of %d generator(s) demonstrated detection%s"
                 % (len(good), len(good) + len(inconclusive) + len(bad),
                    "; %d inconclusive until their artifacts are regenerated" % len(inconclusive)
                    if inconclusive else "")
                 if ok else
                 "BAD -- no generator demonstrated detection from a clean baseline"))
        return 0 if ok else 1

    if not ran:
        print("\nG-REGEN: FAIL -- no generator could be run, so nothing was checked")
        return 1
    if not all(ran):
        print("\nG-REGEN: FAIL -- a shipped artifact is not what its generator produces. The fix "
              "was applied to the producer and never propagated; regenerate, then RE-SOLVE, "
              "because the solvers read these files.")
        return 1
    print("\nG-REGEN: PASS -- every generated artifact equals what its generator produces today")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
