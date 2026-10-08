#!/usr/bin/env python3
"""The NHPI row's pyridinium (pyH+, the "H+" species of its MedSpec, 33 mM) in acetone: a declared D, set against the two
single-ion assignments of acetone conductances, and its effect on the row re-solved.

No limiting conductance of pyridinium in acetone or acetonitrile was located (Yasukouchi 1979 reports voltammetry only;
Coetzee & Padmanabhan, JACS 1965, 87, 5005 gives pKa and homoconjugation, no conductance). Two assignments of single-ion
conductances in anhydrous acetone at 25 C disagree:
  - Brookes, Hotz & Spong, J. Chem. Soc. A 1971, 2415-2420, Table 2, p. 2418, split by measured KSCN transference numbers:
    NH4+ 116.0 (smaller than pyH+, an upper bound) and Me4N+ 93 (of similar size);
  - Krumgalz, J. Chem. Soc. Faraday Trans. 1 1983, 79, 571-587, Table 4, p. 580, the assignment the model's acetone ion
    table carries (data/ion_diffusivities.csv): NH4+ 89.5, so pyH+ would sit at or below 2.38e-9.
Nernst-Einstein D = R T lambda0 / F^2. Homoconjugation to (py)2H+ (K_f = 4 in MeCN, Coetzee Table I, p. 5007) lowers
the effective D further.

The runs in results/pyridinium_runs/ are run_mediated.jl with MED_ONLY = the NHPI row, in isolated copies of julia/,
with only the pyH+ D replaced. results/pyridinium_runs_spectators/krumgalz_spectators.csv is the same row with the
spectator Li+ and ClO4- at Krumgalz's acetone values (1.843e-9, 3.084e-9) and pyH+ at the carried value: zero-flux ions,
so it must reproduce the published cells exactly. Writes results/pyridinium_bracket.json; the registry rows read it.
"""
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RXN = "NHPI-mediated allylic C-H -> enone"
NE = 8.314462618 * 298.15 / 96485.33212 ** 2          # m2 s-1 per S m2 mol-1
LAM_B = {"NH4+": 116.0, "Me4N+": 93.0}                 # Brookes 1971 Part II, Table 2, p. 2418 (S cm2 mol-1)
LAM_K = {"NH4+": 89.5}                                 # Krumgalz 1983, Table 4, p. 580
CARRIED = 3.0e-9


def read(p):
    return {r["reactor"]: float(r["i_ec_mAcm2"]) for r in csv.DictReader(open(p))}


def main():
    pub = {r["reactor"]: float(r["i_ec_mAcm2"]) for r in csv.DictReader(open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv")))
           if r["reaction"] == RXN}
    runs = {}
    for f in sorted(os.listdir(os.path.join(ROOT, "results", "pyridinium_runs"))):
        rows = read(os.path.join(ROOT, "results", "pyridinium_runs", f))
        assert set(rows) == set(pub), f
        runs[float(f[2:-4])] = rows
    spect = read(os.path.join(ROOT, "results", "pyridinium_runs_spectators", "krumgalz_spectators.csv"))
    spect_identical = spect == pub
    DB = {k: NE * v * 1e-4 for k, v in LAM_B.items()}; DK = {k: NE * v * 1e-4 for k, v in LAM_K.items()}
    lo, hi = DB["Me4N+"], DB["NH4+"]
    inside = [d for d in runs if lo * 0.999 <= d <= hi * 1.001]
    ch = [100 * (runs[d][a] / pub[a] - 1) for d in inside for a in pub]
    def counts(vals):
        return {t: sum(v >= t for v in vals.values()) for t in (25, 50)}
    moves_b = [d for d in inside if counts(runs[d]) != counts(pub)]
    k_edge = [d for d in runs if abs(d / DK["NH4+"] - 1) < 2e-3]
    assert len(k_edge) == 1, "no run at Krumgalz's NH4+ edge"
    k_runs = runs[k_edge[0]]
    us = sorted((d, runs[d]["Unstirred batch"]) for d in runs)
    cross = None
    for (d1, v1), (d2, v2) in zip(us, us[1:]):
        if (v1 - 25) * (v2 - 25) < 0:
            cross = d1 + (25 - v1) * (d2 - d1) / (v2 - v1)
    res = {"brookes_bracket_m2s": [lo, hi], "lambda0_brookes": LAM_B, "krumgalz_nh4_D_m2s": DK["NH4+"],
           "lambda0_krumgalz": LAM_K, "carried": CARRIED, "carried_inside_brookes": lo <= CARRIED <= hi,
           "carried_above_krumgalz_edge": CARRIED > DK["NH4+"],
           "runs_D": sorted(runs), "change_inside_brookes_pct": [min(ch), max(ch)],
           "counts_move_inside_brookes": bool(moves_b), "unstirred_crosses_25_at_D": cross,
           "unstirred_at_krumgalz_edge_mAcm2": k_runs["Unstirred batch"],
           "unstirred_clears_25_at_krumgalz_edge": k_runs["Unstirred batch"] >= 25 > pub["Unstirred batch"],
           "other_cells_at_krumgalz_edge_cross": [a for a in pub if a != "Unstirred batch" and
                                                   any((pub[a] - t) * (k_runs[a] - t) < 0 for t in (25, 50))],
           "change_at_krumgalz_edge_pct": [min(100 * (k_runs[a] / pub[a] - 1) for a in pub),
                                           max(100 * (k_runs[a] / pub[a] - 1) for a in pub)],
           "spectators_krumgalz_bitidentical": spect_identical}
    open(os.path.join(ROOT, "results", "pyridinium_bracket.json"), "w").write(json.dumps(res, indent=1))
    print("Brookes bracket %.2e-%.2e (carried %.1e inside: %s, cells %+.1f to %+.1f pct, counts move: %s); Krumgalz NH4+ "
          "edge %.2e: unstirred %.2f mA cm-2 (clears 25: %s; other crossings %s); unstirred crosses 25 at D = %.3e; "
          "Krumgalz spectators bit-identical: %s"
          % (lo, hi, CARRIED, res["carried_inside_brookes"], min(ch), max(ch), bool(moves_b), DK["NH4+"],
             k_runs["Unstirred batch"], res["unstirred_clears_25_at_krumgalz_edge"], res["other_cells_at_krumgalz_edge_cross"],
             cross, spect_identical))
    ok = (res["carried_inside_brookes"] and not moves_b and len(inside) == 2 and spect_identical
          and res["unstirred_clears_25_at_krumgalz_edge"] and not res["other_cells_at_krumgalz_edge_cross"]
          and DK["NH4+"] < cross < lo)
    print("G-PYH: %s" % ("PASS -- inside Brookes's bracket no count moves; at Krumgalz's NH4+ edge the unstirred cell clears "
                          "25 (the row states the count as conditional); the spectators' D does not enter" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
