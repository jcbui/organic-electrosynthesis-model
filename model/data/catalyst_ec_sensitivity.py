#!/usr/bin/env python3
"""G-CATK -- the eleven molecular-catalyst rows under a DECLARED rate-constant band.

The published matrix runs every catalyst row at k = 0 (no in-film regeneration), which is the
FLOOR of the EC' current, so "10 of 11 catalyst rows clear 25 mA cm-2 in no architecture" is a
k = 0 statement. julia/run_catalyst_ecprime.jl solves the same rows as EC' problems over
k in {0, 1, 10, 100, 1e3, 1e4} M^-1 s^-1 (declared; the band the mediated rows carry plus one
decade) with the substrate at its page-verified concentration and a declared D_S. This gate:

  1. CONTROL: the k = 0 member of every sweep must reproduce the published all50_np_matrix.csv
     cell (same solver, same species plus two spectators) to 1 %. A sweep whose k = 0 does not
     match the matrix is not a sensitivity of the matrix.
  2. Reports, per k, how many of the eleven clear 25 and 50 mA cm-2 in at least one architecture,
     and per row the smallest k at which it does, in which architecture, and whether that cell
     sits at its substrate cap (where the declared D_S is what sets the number).
  3. FAILS on any unresolved cell (a solve that fell below its own k = 0 floor), on a control
     miss, or -- once the documents carry the result -- on a document/artifact mismatch
     (--check-si is the fast tier, added when the SI text lands).

Writes results/catalyst_ec_sensitivity.json. Never touches the matrices.
--negative-control perturbs the published matrix in memory by 5 % and requires the control to FAIL.
"""
import json, sys, os, argparse
import pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SWEEP = os.path.join(ROOT, "julia", "catalyst_ec_sweep.csv")
PUB   = os.path.join(ROOT, "julia", "all50_np_matrix.csv")
OUT   = os.path.join(ROOT, "results", "catalyst_ec_sensitivity.json")
THR = (25.0, 50.0); CTRL_TOL = 0.01
SOURCED = os.path.join(ROOT, "julia", "catalyst_ec_sourced.csv")   # 2026-09-11: the seven sourced-k rows
# The measured bracket each adopted value sits in (M^-1 s^-1), keyed by the basis tag the solver writes
# (docs/CATALYST_RATE_CONSTANTS_20260911.md). Both edges are grid points of the declared-band sweep, so
# the sensitivity of the published counts to the adoption is read off the sweep, never re-solved here.
BANDS = {"Ni(I)bpy+ArBr": (10.0, 1e4),      # Ting 2022 (3.4-56, deactivated ligand, THF) .. Till 2021 (< 1e4, dtbbpy, DMF)
         "Co-H+alkene": (100.0, 1e4),       # Boucher 2023 fit 7e2 for styrenes; alkene class and hydride source undeclared
         "own CV": (1.0, 100.0)}            # Cai/Xu 2021 SI Fig. S2: <= 4e1 at room temperature with the reaction's base
RMAP = {"Unstirred batch": "natural", "Stirred batch": "stirred", "Recirculating flow cell": "flow",
        "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro", "RDE 1600 rpm": "rde",
        "Rotating cylinder 3000 rpm": "rce"}

def sourced_block(sw, pub, fails):
    """The seven rows the published matrix now carries at a SOURCED k (2026-09-11). Three checks and one
    measurement: (i) the k = 0 member reproduces the published NP cell; (ii) a sourced k that lies on the
    declared-band grid reproduces the sweep's cell exactly (same solver, same mesh -- any drift means the
    two producers have diverged); (iii) no cell is unresolved or without a plateau; (iv) how far every
    published count moves when each adopted value is pushed to either edge of its measured bracket."""
    if not os.path.exists(SOURCED):
        fails.append("julia/catalyst_ec_sourced.csv is absent: the seven sourced rows have not been solved"); return None
    cs = pd.read_csv(SOURCED)
    k0 = cs[cs.k_M == 0].merge(pub, on=["reaction", "reactor"], suffixes=("", "_pub"))
    k0["rel"] = (k0.i_ec_mAcm2 - k0.i_np_mAcm2) / k0.i_np_mAcm2
    if len(k0) != cs[cs.k_M == 0].shape[0]:
        fails.append("sourced: %d of %d k=0 control cells matched the published matrix" % (len(k0), cs[cs.k_M == 0].shape[0]))
    for _, b in k0[k0.rel.abs() > CTRL_TOL].iterrows():
        fails.append("sourced control: %s / %s: k=0 solve %.4f vs published %.4f (%+.2f %%)" % (b.reaction, b.reactor, b.i_ec_mAcm2, b.i_np_mAcm2, 100 * b.rel))
    csk = cs[cs.k_M > 0].copy()
    if len(csk) != 49 or csk.reaction.nunique() != 7:
        fails.append("sourced: expected 49 cells over 7 rows, found %d over %d" % (len(csk), csk.reaction.nunique()))
    g = csk.merge(sw[["reaction", "reactor", "k_M", "i_ec_mAcm2"]], on=["reaction", "reactor", "k_M"], how="left", suffixes=("", "_sw"))
    on_grid = g[g.i_ec_mAcm2_sw.notna()]
    drift = ((on_grid.i_ec_mAcm2 - on_grid.i_ec_mAcm2_sw) / on_grid.i_ec_mAcm2_sw).abs()
    if len(on_grid) and drift.max() > 1e-9:
        w = on_grid.loc[drift.idxmax()]
        fails.append("sourced: %s / %s at k=%g differs from the sweep's grid cell by %.2e -- the two producers have diverged" % (w.reaction, w.reactor, w.k_M, drift.max()))
    for _, u in csk[csk.path.str.contains("UNRESOLVED")].iterrows():
        fails.append("sourced unresolved: %s / %s at k=%g" % (u.reaction, u.reactor, u.k_M))
    csk["reached"] = csk.limiter.str.contains("plateau|collapse|limit reached", regex=True)
    for _, u in csk[~csk.reached].iterrows():
        fails.append("sourced: %s / %s reached no plateau: %s" % (u.reaction, u.reactor, str(u.limiter)[:80]))
    ks = sorted(sw.k_M.unique())
    per_row = {}; adopted = {}; lo_edge = {}; hi_edge = {}; floor = {}
    for r, s_ in csk.groupby("reaction"):
        k = float(s_.k_M.iloc[0]); basis = str(s_.k_basis.iloc[0])
        tag = next((t for t in BANDS if basis.startswith(t)), None)
        if tag is None:
            fails.append("sourced: no declared band for basis %r (%s)" % (basis, r)); continue
        lo, hi = BANDS[tag]
        if lo not in ks or hi not in ks:
            fails.append("sourced: band edge %g or %g of %s is not a sweep grid point" % (lo, hi, r)); continue
        swr = sw[sw.reaction == r]
        at = lambda kk: {RMAP[x.reactor]: float(x.i_ec_mAcm2) for x in swr[swr.k_M == kk].itertuples()}
        i_ad = {RMAP[x.reactor]: float(x.i_ec_mAcm2) for x in s_.itertuples()}
        i_0 = {RMAP[x.reactor]: float(x.i_k0_mAcm2) for x in s_.itertuples()}
        adopted[r] = i_ad; lo_edge[r] = at(lo); hi_edge[r] = at(hi); floor[r] = i_0
        per_row[r] = {"k_M": k, "basis": basis, "band_M": [lo, hi], "xk_um": float(s_.xk_um.iloc[0]),
                      "i_mAcm2": i_ad, "i_k0_mAcm2": i_0, "i_at_band_lo": lo_edge[r], "i_at_band_hi": hi_edge[r],
                      "gain_unstirred_to_rce": i_ad["rce"] / i_ad["natural"], "gain_at_k0": i_0["rce"] / i_0["natural"],
                      "best_mAcm2": max(i_ad.values()), "best_k0_mAcm2": max(i_0.values()),
                      "clear25_anywhere": bool(max(i_ad.values()) >= THR[0]),
                      "clear25_anywhere_at_band": [bool(max(lo_edge[r].values()) >= THR[0]), bool(max(hi_edge[r].values()) >= THR[0])],
                      "wall_cells": int(s_.limiter.str.startswith("newton-wall").sum()),
                      "cells_at_substrate_cap": int((s_.i_ec_mAcm2 >= 0.95 * s_.i_subcap_mAcm2).sum())}
    # the four rows with no measured constant stay at the floor
    rows_all = list(dict.fromkeys(sw.reaction)); rows_floor = [r for r in rows_all if r not in per_row]
    pub_cat = pub[pub.reaction.isin(rows_all)]
    i_floor_pub = {r: {RMAP[x.reactor]: float(x.i_np_mAcm2) for x in pub_cat[pub_cat.reaction == r].itertuples()} for r in rows_floor}
    def counts(sel):        # rows >= thr per architecture, over the eleven rows, with the sourced rows at `sel`
        out = {}
        for arch in RMAP.values():
            vals = [sel[r][arch] for r in per_row] + [i_floor_pub[r][arch] for r in rows_floor]
            out[arch] = {"25": int(sum(v >= THR[0] for v in vals)), "50": int(sum(v >= THR[1] for v in vals))}
        return out
    c_ad, c_lo, c_hi, c_0 = counts(adopted), counts(lo_edge), counts(hi_edge), counts(floor)
    delta = {arch: {t: [c_lo[arch][t] - c_ad[arch][t], c_hi[arch][t] - c_ad[arch][t]] for t in ("25", "50")} for arch in RMAP.values()}
    best_ad = {r: max(v.values()) for r, v in adopted.items()}
    n25_any = sum(1 for v in best_ad.values() if v >= THR[0]) + sum(1 for r in rows_floor if max(i_floor_pub[r].values()) >= THR[0])
    n25_lo = sum(1 for v in lo_edge.values() if max(v.values()) >= THR[0]) + sum(1 for r in rows_floor if max(i_floor_pub[r].values()) >= THR[0])
    n25_hi = sum(1 for v in hi_edge.values() if max(v.values()) >= THR[0]) + sum(1 for r in rows_floor if max(i_floor_pub[r].values()) >= THR[0])
    gains = sorted(v["gain_unstirred_to_rce"] for v in per_row.values())
    return {"file": "julia/catalyst_ec_sourced.csv", "n_sourced": len(per_row), "n_floor": len(rows_floor), "rows_floor": rows_floor,
            "control": {"cells": int(len(k0)), "worst_rel": float(k0.rel.abs().max()) if len(k0) else None, "tolerance": CTRL_TOL},
            "grid_check": {"cells_on_grid": int(len(on_grid)), "max_rel_drift": float(drift.max()) if len(on_grid) else 0.0},
            "per_row": per_row,
            "counts_over_eleven": {"adopted": c_ad, "band_lo": c_lo, "band_hi": c_hi, "k0": c_0},
            "count_delta_at_band_edges": delta,
            "max_abs_count_delta": max(abs(d) for a in delta.values() for t in a.values() for d in t),
            "rows_clearing25_anywhere": n25_any, "rows_clearing25_anywhere_at_band": [n25_lo, n25_hi],
            "ten_of_eleven_holds": n25_any <= 1, "ten_of_eleven_holds_at_band": [n25_lo <= 1, n25_hi <= 1],
            "gain_sourced_min": gains[0], "gain_sourced_max": gains[-1], "gain_sourced_median": float(np.median(gains)),
            "gain_floor_median": float(np.median([v["gain_at_k0"] for v in per_row.values()] + [max(i_floor_pub[r].values()) / i_floor_pub[r]["natural"] for r in rows_floor])),
            "wall_cells": int(sum(v["wall_cells"] for v in per_row.values()))}


def main(negative_control=False):
    sw = pd.read_csv(SWEEP); pub = pd.read_csv(PUB)
    if negative_control:
        pub = pub.copy(); pub["i_np_mAcm2"] *= 1.05
    rows = list(dict.fromkeys(sw.reaction)); ks = sorted(sw.k_M.unique())
    fails = []
    # 1. control
    k0 = sw[sw.k_M == 0].merge(pub, on=["reaction", "reactor"], suffixes=("", "_pub"))
    if len(k0) != len(rows) * sw.reactor.nunique():
        fails.append(f"control join: {len(k0)} of {len(rows) * sw.reactor.nunique()} k=0 cells matched the published matrix")
    k0["rel"] = (k0.i_ec_mAcm2 - k0.i_np_mAcm2) / k0.i_np_mAcm2
    worst = k0.loc[k0.rel.abs().idxmax()] if len(k0) else None
    bad = k0[k0.rel.abs() > CTRL_TOL]
    for _, b in bad.iterrows():
        fails.append(f"control: {b.reaction} / {b.reactor}: k=0 solve {b.i_ec_mAcm2:.4f} vs published {b.i_np_mAcm2:.4f} ({100*b.rel:+.2f} %)")
    # TIGHTNESS, cell by cell. A cell whose ramp ends on a Newton wall is a lower bound, and so,
    # more weakly, is any plateau. Each is TIGHT to the fraction of the EXHAUSTED species left at
    # the electrode when the concentration-control walk stops -- the resting carrier normally,
    # the substrate where the front detaches and the current runs above the carrier's own cap --
    # because that species is what sets the limit and what is left of it bounds the headroom.
    # (The same test S5.2 applies to the mediated matrix, G12: 0.009-1.2 % of bulk.) The census is
    # decidable only if no cell reported below a threshold could reach it within its own tightness.
    sw["wall"] = sw.limiter.str.startswith("newton-wall")
    sw["c_rest"] = sw.limiter.str.extract(r"c_red/cb ([0-9.e+-]+)")[0].astype(float)
    sw["c_sub"] = sw.limiter.str.extract(r"c_sub/cb ([0-9.e+-]+)")[0].astype(float)
    sw["tight"] = sw[["c_rest", "c_sub"]].min(axis=1)
    # a walk that CROSSED the collapse criterion records no plateau value -- it is the best-converged
    # case, not a missing one (the mediated census enters such cells AT the criterion, S5.2)
    sw.loc[sw.tight.isna() & sw.limiter.str.contains("collapse"), "tight"] = 1e-3
    fk = sw[sw.k_M > 0]; wk = fk[fk.wall]
    n_noplat = int(fk.tight.isna().sum())
    if n_noplat:
        fails.append(f"{n_noplat} finite-k cells reached no c-control plateau: unbounded lower bounds")
    undec = []
    for thr in THR:
        u = fk[(fk.i_ec_mAcm2 < thr) & (fk.i_ec_mAcm2 * (1 + fk.tight.fillna(1.0)) >= thr)]
        for c in u.itertuples(): undec.append((c.reaction, c.reactor, float(c.k_M), thr, float(c.i_ec_mAcm2), float(c.tight)))
    for u in undec:
        fails.append("undecidable: %s / %s at k=%g reports %.2f below %g with tightness %.2f %% -- the census cannot be read there" % (u[0], u[1], u[2], u[4], u[3], 100 * u[5]))
    walls = {"finite_k_cells": int(len(fk)), "wall_cells": int(len(wk)), "without_plateau": n_noplat,
             "exhausted_fraction_max_walls": float(wk.tight.max()) if len(wk) else 0.0,
             "exhausted_fraction_median_walls": float(wk.tight.median()) if len(wk) else 0.0,
             "exhausted_fraction_max_all": float(fk.tight.max()) if len(fk) else 0.0,
             "undecidable_cells": len(undec),
             "published_k0_cells_that_are_walls": int(sw[sw.k_M == 0].wall.sum())}
    # unresolved cells
    unres = sw[sw.path.str.contains("UNRESOLVED")]
    for _, u in unres.iterrows():
        fails.append(f"unresolved: {u.reaction} / {u.reactor} at k={u.k_M:g}: {u.i_ec_mAcm2:.3f} below its k=0 floor {u.i_k0_mAcm2:.3f}")
    # 2. the census
    per_k = {}
    for k in ks:
        s = sw[sw.k_M == k]
        best = s.groupby("reaction").i_ec_mAcm2.max()
        per_k[f"{k:g}"] = {"clear25": int((best >= THR[0]).sum()), "clear50": int((best >= THR[1]).sum()),
                           "rows_clearing25": sorted(best[best >= THR[0]].index.tolist()),
                           "max_amplification": float(s.amplification.max()),
                           # cells whose ceiling is at the substrate cap: where the declared D_S sets the number
                           "cells_at_substrate_cap": int((s.i_ec_mAcm2 >= 0.95 * s.i_subcap_mAcm2).sum()),
                           "cells": int(len(s))}
    rx = pd.read_csv(os.path.join(ROOT, "data", "reactions_50.csv")).set_index("reaction")
    per_row = {}
    for r in rows:
        s = sw[sw.reaction == r]
        d = {"i_k0_best_mAcm2": float(s[s.k_M == 0].i_ec_mAcm2.max()),
             "i_ec_best_mAcm2_at_kmax": float(s[s.k_M == max(ks)].i_ec_mAcm2.max()) if (s.k_M == max(ks)).any() else None,
             "max_amplification": float(s.amplification.max())}
        for thr, key in zip(THR, ("k_min_clearing25", "k_min_clearing50")):
            hit = s[s.i_ec_mAcm2 >= thr].sort_values(["k_M", "i_ec_mAcm2"], ascending=[True, False])
            if len(hit):
                h = hit.iloc[0]
                d[key] = {"k_M": float(h.k_M), "reactor": h.reactor, "i_ec_mAcm2": float(h.i_ec_mAcm2),
                          "at_substrate_cap": bool(h.i_ec_mAcm2 >= 0.95 * h.i_subcap_mAcm2)}
            else:
                d[key] = None
        # is the row substrate-capped at k_max (the number then rests on the declared D_S)?
        expect = len(ks) * sw.reactor.nunique()
        if len(s) != expect or (s.k_M == max(ks)).sum() != sw.reactor.nunique():
            fails.append(f"incomplete: {r} has {len(s)} of {expect} cells (sweep unfinished or a cell missing)")
            per_row[r] = dict(d, substrate_capped_at_kmax=None, C_cat_M=None, C_S_M=None, wall_cells=None); continue
        top = s[s.k_M == max(ks)].sort_values("i_ec_mAcm2").iloc[-1]
        d["substrate_capped_at_kmax"] = bool(top.i_ec_mAcm2 >= 0.95 * top.i_subcap_mAcm2)
        d["C_cat_M"] = float(rx.loc[r, "C_carrier_M"]) if r in rx.index else None
        d["C_S_M"] = float(rx.loc[r, "C_substrate_M"]) if r in rx.index else None
        # a wall cell is a lower bound; count them so the census cannot pass them off as plateaus
        d["wall_cells"] = int(s.limiter.str.startswith("newton-wall").sum())
        per_row[r] = d
    survives = {k: (v["clear25"] <= 1) for k, v in per_k.items()}
    srcd = sourced_block(sw, pub, fails)
    # every cell, so a document can quote a specific (row, reactor, k) without re-reading the CSV
    cells = [{"reaction": r.reaction, "reactor": r.reactor, "k_M": float(r.k_M), "delta_um": float(r.delta_um),
              "i_ec_mAcm2": float(r.i_ec_mAcm2), "i_subcap_mAcm2": float(r.i_subcap_mAcm2), "path": r.path}
             for r in sw.itertuples()]
    res = {"k_band_M": ks, "D_S_rule": "1.0e-9 m2/s x (0.369 mPa s / mu_solvent), declared", "cells": cells,
           "control": {"cells": int(len(k0)), "worst_rel": float(worst.rel) if worst is not None else None,
                       "worst_cell": (f"{worst.reaction} / {worst.reactor}" if worst is not None else None),
                       "tolerance": CTRL_TOL, "pass": len(bad) == 0},
           "unresolved_cells": int(len(unres)),
           "walls": walls,
           "per_k": per_k, "per_row": per_row,
           "ten_of_eleven_survives_at_k": survives,
           "sourced": srcd,
           "verdict": "PASS" if not fails else "FAIL", "fails": fails}
    if not negative_control:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(res, open(OUT, "w"), indent=1)
    print(f"G-CATK: control {len(k0)} cells, worst {100*res['control']['worst_rel']:+.3f} % ({res['control']['worst_cell']}); "
          f"unresolved {len(unres)}; walls {walls['wall_cells']}/{walls['finite_k_cells']} finite-k cells, exhausted species at plateau <= {100*walls['exhausted_fraction_max_walls']:.2f} % (all cells <= {100*walls['exhausted_fraction_max_all']:.2f} %), undecidable {walls['undecidable_cells']}")
    for k, v in per_k.items():
        print(f"  k = {k:>6} M-1 s-1: {v['clear25']:2d} of 11 clear 25 in some architecture, {v['clear50']:2d} clear 50; "
              f"max amplification x{v['max_amplification']:.1f}; 10-of-11 {'HOLDS' if survives[k] else 'FAILS'}"
              + (f"  [{', '.join(v['rows_clearing25'])}]" if v['rows_clearing25'] else ""))
    if srcd:
        print(f"  sourced k (7 rows, 4 at the floor): control worst {100*srcd['control']['worst_rel']:+.3f} %, grid drift {srcd['grid_check']['max_rel_drift']:.1e} over {srcd['grid_check']['cells_on_grid']} cells; "
              f"{srcd['rows_clearing25_anywhere']} of 11 clear 25 somewhere (band edges: {srcd['rows_clearing25_anywhere_at_band']}); gains x{srcd['gain_sourced_min']:.1f}-{srcd['gain_sourced_max']:.1f} (floor median x{srcd['gain_floor_median']:.1f}); "
              f"largest count movement at a band edge: {srcd['max_abs_count_delta']}")
        for arch, d in srcd["count_delta_at_band_edges"].items():
            if any(x != 0 for t in d.values() for x in t): print(f"    {arch}: >=25 {d['25']}  >=50 {d['50']}  (lo, hi edge minus adopted)")
    for f in fails: print("  FAIL:", f)
    print("G-CATK:", res["verdict"])
    return res["verdict"] == "PASS"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--negative-control", action="store_true")
    ap.add_argument("--sweep", action="store_true", help="re-run julia/run_catalyst_ecprime.jl first (~45 min)")
    ap.add_argument("--sweep-sourced", action="store_true", help="re-run julia/run_catalyst_sourced.jl and run_catalyst_delta.jl first (~30 min)")
    a = ap.parse_args()
    if a.sweep_sourced:
        import subprocess
        for script, marker in (("run_catalyst_sourced.jl", "CATALYST SOURCED DONE"), ("run_catalyst_delta.jl", "CATALYST DELTA DONE"),
                               ("run_catalyst_band.jl", "CATALYST BAND DONE")):
            log = os.path.join(ROOT, "results", "gate_logs", "G-CATK-SOURCED.%s.log" % script.replace(".jl", ""))
            os.makedirs(os.path.dirname(log), exist_ok=True)
            with open(log, "w") as fh:
                rc = subprocess.call(["julia", script], cwd=os.path.join(ROOT, "julia"), stdout=fh, stderr=subprocess.STDOUT)
            if rc != 0 or marker not in open(log).read():
                print(f"G-CATK: FAIL -- {script} exited {rc} without its DONE marker (see {log})"); sys.exit(1)
    if a.sweep:
        import subprocess
        log = os.path.join(ROOT, "results", "gate_logs", "G-CATK-SWEEP.julia.log")
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "w") as fh:
            rc = subprocess.call(["julia", "run_catalyst_ecprime.jl"], cwd=os.path.join(ROOT, "julia"), stdout=fh, stderr=subprocess.STDOUT)
        done = "CATALYST SWEEP DONE" in open(log).read()
        if rc != 0 or not done:
            print(f"G-CATK: FAIL -- the sweep exited {rc} without its DONE marker (see {log})"); sys.exit(1)
    if a.negative_control:
        ok = main(negative_control=True)
        # run_gates.sh scores a control by a "<gate> control: GOOD|BAD" line and otherwise falls back
        # to the gate's own verdict -- which in control mode is the FAIL the control exists to
        # provoke (CLAUDE.md: "a negative control that fires must not print the gate's own FAIL
        # verdict"). The first suite run scored this control FAIL for exactly that reason.
        print("G-CATK control:", "GOOD -- the control fires on a 5 % perturbation of the published matrix" if not ok else "BAD -- test is inert")
        sys.exit(0 if not ok else 1)
    sys.exit(0 if main() else 1)
