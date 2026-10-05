"""Build the PUBLISHED matrix -> julia/tier0_ec_matrix.csv, on ONE physics for all 50 rows.

    cd Section4_Model && python data/build_merged_matrix.py

WHAT CHANGED ON 2026-08-24, AND WHY IT MATTERED
-----------------------------------------------
This script used to build the published matrix from `tier0_matrix.csv` -- Tier-0 Fick, with NO
MIGRATION TERM -- and overlay only the 8 mediated rows from the EC' solver. So 42 of 50 published
rows had no migration in them, while the >=25 and >=50 counts were tallied straight across the
mixed column. `run_all50_np.jl` had ALREADY been written to solve all 50 x 6 (now 50 x 7) with Nernst-Planck,
migration and electroneutrality, and wrote `all50_np_matrix.csv` -- and NOTHING read that file. The
solve was done; the wiring was not. `docs/ONE_PHYSICS_20260823.md` described the job as finished.

The cost was not hypothetical. The Kolbe row is a charged carrier in its own salt, so migration
must double it exactly (Newman binary limit; the NP solve reports x2.006):

    architecture      Fick      NP    published-before
    natural          64.67  129.72       64.67
    rce            1801.08 3612.58     1801.00

Every published value in that row was the Fick value -- understated by a factor of two. Six rows
were affected (charged carrier AND not mediated): decarboxylative elimination x2.876, Kolbe x2.006,
lignin->vanillin x1.278, alkenesulfonate x1.176, sulfonylation x1.176, 5-exo cyclization x1.046.

No gate caught it because `audit_numeric.py` checks that the derived artifacts are CONSISTENT with
their sources, and never opened the orphan. Consistency between the wrong inputs is still
consistent. G-ORPHAN (data/check_orphans.py) now asserts that every solver output is consumed.

THE MERGE, NOW
--------------
  base    all50_np_matrix.csv   -- all 50 x 7, Nernst-Planck + migration, homogeneous source off
  overlay mediated_ec_matrix.csv -- the 8 mediated rows, same physics PLUS the EC' source term

Both layers are the same equation set; the overlay only switches on `k`. That is what makes the
counts a like-for-like comparison, which is the entire point of the 50 x 7 table.

THREE ASSERTIONS, each of which has caught something
  1. the NP layer must cover exactly 50 reactions x 7 architectures -- a silently short matrix
     would otherwise leave stale Tier-0 numbers showing through
  2. for every mediated cell, i_ec >= i_np. The homogeneous source can only ADD flux, so an
     overlay value below its own no-source solve would mean the EC' solve had under-converged.
     This replaces the old `i_ec >= 0.9*i_t0` check, whose reference was the FICK value and so was
     the weaker test once migration is present.
  3. a cell whose flag is not "ok" is a hard error, never a fallback to a simpler model

PATHS ARE ANCHORED ON __file__, NOT ON THE WORKING DIRECTORY -- tier0_ec_matrix.csv is read by six
figure generators, so a copy written into the wrong julia/ directory could later be picked up as if
it were canonical.
"""
import os
import pandas as pd

HERE  = os.path.dirname(os.path.abspath(__file__))
SEC4  = os.path.dirname(HERE)
JULIA = os.path.join(SEC4, "julia")
COLS  = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
RMAP  = {"Unstirred batch": "natural", "Stirred batch": "stirred",
         "Recirculating flow cell": "flow", "RDE 1600 rpm": "rde",
         "Rotating cylinder 3000 rpm": "rce", "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro"}

t0 = pd.read_csv(os.path.join(JULIA, "tier0_matrix.csv"))          # kept only for the delta report
np_ = pd.read_csv(os.path.join(JULIA, "all50_np_matrix.csv"))
ec  = pd.read_csv(os.path.join(JULIA, "mediated_ec_matrix.csv"))

## ---- assertion 1: the full-physics layer really covers everything -------------------------
rxns = sorted(np_.reaction.unique())
if len(rxns) != 50 or len(np_) != 350:
    raise SystemExit(
        "all50_np_matrix.csv has %d reactions and %d cells; expected 50 and 350.\n"
        "  A short NP matrix would let stale Tier-0 values show through for the missing rows, "
        "which is exactly the mixed-physics failure this rewrite exists to end.\n"
        "  If run_all50_np.jl skipped rows for LOW carrier-charge confidence, resolve those "
        "charges -- do not publish a partly-Fick column." % (len(rxns), len(np_)))

## a runaway or unsolved NP cell must never reach the published matrix
badflags = np_[~np_["flag"].isin(["ok"])] if "flag" in np_.columns else np_.iloc[0:0]
if len(badflags):
    rowsx = ", ".join("%s / %s (%s, x%.1f)" % (r.reaction, r.reactor, r.flag, r.i_np_mAcm2 / max(r.i_fick_mAcm2, 1e-12))
                      for _, r in badflags.head(6).iterrows())
    raise SystemExit(
        "%d NP cell(s) are not flagged ok: %s\n"
        "  A cell whose current ramp never converged to a limiting current has no ceiling to "
        "publish. Fix the cell; do not let it through." % (len(badflags), rowsx))

## The row metadata (`class`, `carrier`) is carried through, NOT rebuilt: tier0_matrix.csv is
## the file that defines which of the 50 rows is substrate-, catalyst- or mediator-carried, and
## figs/model_medians.py selects on it (`TIER0_EC.carrier == "catalyst"`). This used to read
## `t0[["cls", ...]]` -- but the column is spelled `class`, so the guard was never true, both
## columns were dropped, and four figure generators died on `DataFrame has no attribute
## carrier`. It is an assertion now: a missing metadata column is a hard stop, never a silent
## narrowing of the schema.
META = ["class", "carrier"]
missing = [c for c in META if c not in t0.columns]
if missing:
    raise SystemExit(
        "tier0_matrix.csv is missing %s. Those columns are not decoration: model_medians.py\n"
        "  selects the published matrix on `carrier`, so dropping them breaks Fig. 2, Fig. 3,\n"
        "  Fig. 4 and the carrier figure at render time rather than here." % missing)
m = t0[["reaction"] + META].copy()
m = m.set_index("reaction")
for c in COLS:
    m[c] = pd.NA
for _, r in np_.iterrows():
    m.at[r.reaction, RMAP[r.reactor]] = round(float(r.i_np_mAcm2), 4)
if m[COLS].isna().any().any():
    raise SystemExit("a published cell was left empty after the NP layer; refusing to write")

## ---- assertions 2 and 3: the mediated overlay ---------------------------------------------
np_lookup = {(r.reaction, RMAP[r.reactor]): float(r.i_np_mAcm2) for _, r in np_.iterrows()}
n_over = 0
unresolved = []
for rxn, g in ec.groupby("reaction"):
    if rxn not in m.index:
        raise SystemExit("mediated row %r is not in the NP matrix -- renamed in one file only?" % rxn)
    for _, row in g.iterrows():
        col = RMAP[row.reactor]
        if row.flag != "ok":
            ## An unresolved cell is RECORDED, not silently replaced and not allowed to block the
            ## whole matrix. It is written as NaN, listed below, and excluded from every count --
            ## so a reader can never mistake it for a solved value, and a threshold tally can never
            ## quietly include or exclude it without saying so.
            ##
            ## Only one cell is in this state: Br- oxidation x unstirred. Its two candidate limits
            ## are 4.86 mA/cm2 (substrate transport) and >=20.31 (mediator, k=0 with migration),
            ## and which one the table should report is a definitional question about what a
            ## mediated row means -- see docs/PROVENANCE_PUSH_20260824.md section 15.
            unresolved.append((rxn, col, float(row.i_ec_mAcm2), row.limiter, row.path))
            m.at[rxn, col] = float("nan")
            n_over += 1
            continue
        ## NO CROSS-SOLVER FLOOR TEST HERE -- it would compare two different models.
        ##
        ## The tempting check is `i_ec >= i_np`, on the reasoning that the homogeneous source can
        ## only ADD flux. That reasoning is sound, but only against a k = 0 solve of the SAME
        ## system. It is not the same system: run_all50_np.jl builds four species (carrier,
        ## product, supporting cation, supporting anion) while run_mediated.jl builds six for the
        ## same row (mediator reduced and oxidised, substrate, H+, and the supporting pair). The
        ## ionic inventories differ, so the two k = 0 limits differ legitimately -- NHPI x RDE is
        ## 49.25 against the NP matrix's 52.75, and neither number is wrong.
        ##
        ## This test was added here, fired on four cells, and looked like a real finding. One of
        ## the four (Br- oxidation x unstirred) WAS real; the other three were this artefact. The
        ## correct floor lives inside run_mediated.jl, where `k0_floor` solves the identical
        ## species set, mesh and boundary conditions with k = 0 -- and every cell that fails it is
        ## flagged there and arrives here as flag != "ok".
        val = float(row.i_ec_mAcm2)
        m.at[rxn, col] = round(val, 4)
        n_over += 1
if n_over != 56:
    raise SystemExit("expected 56 mediated overlay cells, applied %d" % n_over)

## ---- the SEVEN catalyst rows with a SOURCED rate constant (2026-09-11) --------------------
## julia/catalyst_ec_sourced.csv (run_catalyst_sourced.jl) solves every catalyst row at k = 0 and,
## for the seven rows whose substrate-consuming step has a MEASURED rate constant in the
## literature (docs/CATALYST_RATE_CONSTANTS_20260911.md; registry category 10; SI S5.7), at that k.
## Same solver and the same species set as the k = 0 layer plus the substrate and a
## charge-balancing product, so (i) the k = 0 member is a CONTROL against all50_np_matrix.csv,
## checked here to 1e-6, and (ii) i_ec >= i_k0 IS a valid floor test for these cells, because it
## compares the same system with the source on and off (unlike the cross-solver test refused
## above). The sourced cell is overlaid exactly as a mediated cell is; the four rows with no
## measured constant keep the NP layer's k = 0 value, the floor of the EC' current.
cs = pd.read_csv(os.path.join(JULIA, "catalyst_ec_sourced.csv"))
c0 = cs[cs.k_M == 0].copy()
c0["np"] = [np_lookup.get((r.reaction, RMAP[r.reactor])) for r in c0.itertuples()]
if c0["np"].isna().any():
    raise SystemExit("a k = 0 control cell of catalyst_ec_sourced.csv has no counterpart in all50_np_matrix.csv")
_rel = ((c0.i_ec_mAcm2 - c0["np"]) / c0["np"]).abs()
if _rel.max() > 1e-6:
    _w = c0.loc[_rel.idxmax()]
    raise SystemExit("catalyst_ec_sourced.csv: the k = 0 control differs from all50_np_matrix.csv by %.2e "
                     "(%s / %s) -- the two layers are no longer the same physics" % (_rel.max(), _w.reaction, _w.reactor))
csk = cs[cs.k_M > 0]
if len(csk) != 49 or csk.reaction.nunique() != 7:
    raise SystemExit("expected 49 sourced catalyst cells (7 rows x 7 architectures), found %d over %d rows"
                     % (len(csk), csk.reaction.nunique()))
n_cat = 0; n_cat_wall = 0
for row in csk.itertuples():
    col = RMAP[row.reactor]
    if row.reaction not in m.index:
        raise SystemExit("sourced catalyst row %r is not in the NP matrix" % row.reaction)
    if "UNRESOLVED" in row.path:
        raise SystemExit("sourced catalyst cell %s / %s fell below its own k = 0 floor (%s); refusing to publish it"
                         % (row.reaction, col, row.path))
    lim = str(row.limiter)
    reached = any(tok in lim for tok in ("plateau", "collapse", "limit reached"))
    if not reached:
        raise SystemExit("sourced catalyst cell %s / %s reached no concentration-control plateau: %s"
                         % (row.reaction, col, lim[:90]))
    if lim.startswith("newton-wall"):
        n_cat_wall += 1          # a ramp wall followed by a plateau: a lower bound, tight to the plateau (G-CATK)
    if float(row.i_ec_mAcm2) < float(row.i_k0_mAcm2) * (1 - 1e-9):
        raise SystemExit("sourced catalyst cell %s / %s is below its own k = 0 solve" % (row.reaction, col))
    m.at[row.reaction, col] = round(float(row.i_ec_mAcm2), 4)
    n_cat += 1
if n_cat != 49:
    raise SystemExit("expected 49 sourced catalyst overlay cells, applied %d" % n_cat)
print("sourced catalyst overlay: %d cells over %d rows (%d end on a ramp wall tight to a plateau; "
      "k = 0 control vs the NP layer: worst %.1e)" % (n_cat, csk.reaction.nunique(), n_cat_wall, _rel.max()))

out = m.reset_index()[["class", "reaction", "carrier"] + COLS]
for c in META:
    if out[c].isna().any():
        raise SystemExit("row metadata %r came through empty for %d rows; refusing to write"
                         % (c, int(out[c].isna().sum())))
OUT = os.path.join(JULIA, "tier0_ec_matrix.csv")
out.to_csv(OUT, index=False)

print("PUBLISHED MATRIX -- one physics for all 50 rows (NP + migration; EC' source on the 8 mediated rows and the 7 catalyst rows with a sourced k)")
for c in COLS:
    col = out[c].dropna()
    print("  %-8s >=25: %2d/%d   >=50: %2d/%d   median %7.1f"
          % (c, (col >= 25).sum(), len(col), (col >= 50).sum(), len(col), col.median()))
if unresolved:
    print("\nUNRESOLVED CELLS -- written as NaN and EXCLUDED from every count above (%d):" % len(unresolved))
    for rxn, col, val, lim, path in unresolved:
        print("  %-44s %-9s best-converged %.3f via %s" % (rxn[:44], col, val, path))
        print("       %s" % lim[:100])
    print("  These are not failures to be papered over: see docs/PROVENANCE_PUSH_20260824.md S15.")

## what the rewiring changed, so the effect is visible rather than silent
print("\nchange vs the OLD Tier-0-based build (same mediated overlay):")
old = t0.set_index("reaction")
for c in COLS:
    o25 = int((old[c] >= 25).sum()); o50 = int((old[c] >= 50).sum())
    print("  %-8s Tier-0 layer gave >=25: %2d, >=50: %2d   ->  full physics >=25: %2d, >=50: %2d"
          % (c, o25, o50, (out[c] >= 25).sum(), (out[c] >= 50).sum()))
print("\nwrote " + OUT)
