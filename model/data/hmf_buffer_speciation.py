#!/usr/bin/env python3
"""The HMF -> FDCA row's buffer: 0.500 M total boron (boric acid) adjusted to pH 10.00 with NaOH, 25 C.

Source of the recipe: Cardiel, Taitt & Choi, ACS Sustainable Chem. Eng. 2019, 7, 11138 (Experimental: "0.5 M sodium
borate buffer solution (pH 8-12, adjusted with NaOH)", reagents boric acid and NaOH).

Speciation (the model carries monomers only): B(OH)3 + OH- = B(OH)4-, with the quotient of Mesmer, Baes & Sweeton,
Inorg. Chem. 1972, 11, 537-543 (abstract p. 537 and Table III, p. 541):
    log Q11 = 1573.21/T + 28.6059 + 0.012078 T - 13.2258 log T + (0.3250 - 0.00033 T) I - 0.0912 I^(3/2)
pH is read as -log a_H; a_OH = Kw / a_H with pKw = 13.995 (declared; the standard 25 C value, which enters only
through [OH-] ~ 0.1 mM and moves no concentration below the reported precision); gamma_OH from the Davies equation
iterated on the ionic strength; molar taken as molal. Na+ follows from charge balance.

Polyborates are NOT carried by the model. Mesmer's Table VI quotients (p. 542; fitted in 1 m KCl at 50-200 C, so 25 C
is an extrapolation) are evaluated here, schemes I and II, at the same pH, [OH-] and Q11(I) as the monomers, and each
scheme's composition is re-solved (results/hmf_buffer_runs/) with the polyborate charge lumped as an inert anion.

Writes results/hmf_buffer_speciation.json; asserts the adopted concentrations in julia/run_mediated.jl equal these.
"""
import csv, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
T, CB, PH, PKW = 298.15, 0.500, 10.00, 13.995


def logq11(I):
    return (1573.21 / T + 28.6059 + 0.012078 * T - 13.2258 * math.log10(T)
            + (0.3250 - 0.00033 * T) * I - 0.0912 * I ** 1.5)


def davies(I, z=1):
    A = 0.5091                     # Debye-Hueckel A at 25 C (kg^0.5 mol^-0.5), the Davies equation's own constant
    s = math.sqrt(I)
    return 10 ** (-A * z * z * (s / (1 + s) - 0.3 * I))


def speciate():
    I = 0.45
    for _ in range(200):
        a_oh = 10 ** (PH - PKW)
        oh = a_oh / davies(I)
        q = 10 ** logq11(I)
        f = q * oh / (1 + q * oh)          # fraction of boron as B(OH)4-
        b4, b3 = CB * f, CB * (1 - f)
        na = b4 + oh                        # charge balance (H+ negligible at pH 10)
        I_new = 0.5 * (na + b4 + oh)
        if abs(I_new - I) < 1e-12:
            break
        I = I_new
    return {"B(OH)4-": b4, "B(OH)3": b3, "Na+": na, "OH-": oh, "I": I, "log_Q11": logq11(I)}


# Mesmer, Baes & Sweeton Table VI, p. 542: log Q_x,y in 1 m KCl, analytical expressions fitted at 50-200 C (the 25 C column,
# from Ingri's 3 M NaClO4 data, is excluded from that fit), so 25 C is an extrapolation. Q_x,y = [B_x(OH)_(3x+y)^y-] /
# ([B(OH)3]^x [OH-]^y); Q_2,1, Q_3,1 and Q_5,3 belong to scheme II, Q_4,2 to scheme I (the table's own footnotes).
# Table VI prints analytical expressions for Q_2,1 and Q_3,1 on scheme II only, so 'scheme I' here is its Q_4,2 with those
# two scheme-II expressions; an exact scheme-I refit moves log Q_3,1 at 25 C by about 0.03 (audit pass 24).
def logq_tab(key, T=T):
    lt = math.log10(T)
    return {"11": 1573.21 / T + 28.8397 + 0.011748 * T - 13.2258 * lt,
            "21": 2756.1 / T - 18.966 + 5.835 * lt, "31": 3339.5 / T - 8.084 + 1.497 * lt,
            "42": 12820. / T - 134.56 + 42.105 * lt, "53": 14099. / T - 118.115 + 36.237 * lt}[key]


def speciate_poly(scheme):
    """Monomers plus polyborates at the same pH, [OH-] treatment and Q11(I) as speciate(). The Table VI quotients are
    carried as OH--free condensation constants (x-y) B(OH)3 + y B(OH)4- = B_x, log C = log Q_x,y - y log Q_1,1 (1 m),
    so that the monomer ratio still comes from Q11 at this solution's own ionic strength."""
    keys = ("21", "31", "42") if scheme == "I" else ("21", "31", "53")
    cond = {(int(k[0]), int(k[1])): logq_tab(k) - int(k[1]) * logq_tab("11") for k in keys}
    I = 0.45
    for _ in range(400):
        oh = 10 ** (PH - PKW) / davies(I)
        r = 10 ** logq11(I) * oh
        def total(b3):
            b4 = r * b3
            return b3 + b4 + sum(x * 10 ** lc * b3 ** (x - y) * b4 ** y for (x, y), lc in cond.items())
        lo, hi = 1e-15, CB
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if total(mid) < CB else (lo, mid)
        b3 = 0.5 * (lo + hi); b4 = r * b3
        poly = {(x, y): 10 ** lc * b3 ** (x - y) * b4 ** y for (x, y), lc in cond.items()}
        na = b4 + sum(y * v for (x, y), v in poly.items()) + oh
        I_new = 0.5 * (na + b4 + sum(y * y * v for (x, y), v in poly.items()) + oh)
        if abs(I_new - I) < 1e-12:
            break
        I = 0.5 * I + 0.5 * I_new
    frac = sum(x * v for (x, y), v in poly.items()) / CB
    return {"B(OH)4-": 1000 * b4, "B(OH)3": 1000 * b3, "Na+": 1000 * na,
            "polyborate_charge": 1000 * sum(y * v for (x, y), v in poly.items()),
            "polyborate_fraction_of_boron_pct": 100 * frac, "OH-": 1000 * oh, "I": I}


# The polyborate re-solves (results/hmf_buffer_runs/): the HMF row with each scheme's composition rounded to whole mM and
# the polyborate charge lumped as one inert (zero-flux) monovalent anion; Na+ is set to the carried anion charge so the
# bulk stays neutral, as the solver asserts. Lumping removes the base capacity the polyborates carry, so a run bounds the
# omission from the pessimistic side.
RUNS = {"I": "hmf_polyborate.csv", "II": "hmf_polyborate_II.csv"}
CARRIED_POLY = {"I": {"B(OH)4-": 260, "B(OH)3": 28, "Na+": 357, "polyborate_charge": 97},
                "II": {"B(OH)4-": 199, "B(OH)3": 21, "Na+": 360, "polyborate_charge": 161}}
RXN = "HMF -> FDCA (biomass)"
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]
REACTOR = {"Unstirred batch": "natural", "Stirred batch": "stirred", "Recirculating flow cell": "flow",
           "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro", "RDE 1600 rpm": "rde",
           "Rotating cylinder 3000 rpm": "rce"}


def main():
    sp = speciate()
    mm = {k: 1000 * v for k, v in sp.items() if k in ("B(OH)4-", "B(OH)3", "Na+", "OH-")}
    print("monomers only, activity-corrected: B(OH)4- %.1f, B(OH)3 %.1f, Na+ %.1f, OH- %.2f mM (I = %.3f, log Q11 = %.3f)"
          % (mm["B(OH)4-"], mm["B(OH)3"], mm["Na+"], mm["OH-"], sp["I"], sp["log_Q11"]))
    src = open(os.path.join(ROOT, "julia", "run_mediated.jl"), encoding="utf-8").read()
    blk = src[src.index('MedSpec("HMF -> FDCA (biomass)"'):]
    blk = blk[:blk.index("]),") + 3]
    carried = {k: float(re.search(r'S\("%s",\s*[-+0-9.]+,\s*[0-9.e-]+,\s*([0-9.]+)' % re.escape(k), blk).group(1))
               for k in ("Na+", "B(OH)4-", "B(OH)3")}
    adopted_ok = all(abs(carried[k] - round(mm[k])) < 0.5 for k in carried)
    pub = {r["reactor"]: float(r["i_ec_mAcm2"]) for r in csv.DictReader(open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv")))
           if r["reaction"] == RXN}
    mat = list(csv.DictReader(open(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv"))))
    def med(vals):
        v = sorted(vals); n = len(v); return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])
    def shown(x):                       # the convention the SI and manuscript print medians to
        return round(x) if x >= 100 else round(x, 1)
    cnt = lambda vals: {t: sum(v >= t for v in vals) for t in (25, 50)}
    res = {"recipe": "Cardiel, Taitt & Choi 2019: 0.5 M boric acid adjusted to pH 10 with NaOH",
           "constant": "Mesmer, Baes & Sweeton 1972, log Q11 (abstract p. 537; Table III p. 541); polyborates Table VI p. 542",
           "pKw_declared": PKW, "monomers_mM": mm, "ionic_strength": sp["I"], "log_Q11_at_I": sp["log_Q11"],
           "carried_in_run_mediated_mM": carried, "carried_matches": adopted_ok, "schemes": {}}
    ok = adopted_ok
    for sc, fn in RUNS.items():
        comp = speciate_poly(sc)
        carr = CARRIED_POLY[sc]
        rounded_ok = (all(abs(carr[k] - comp[k]) < 0.5 for k in ("B(OH)4-", "B(OH)3", "polyborate_charge"))
                      and carr["Na+"] == carr["B(OH)4-"] + carr["polyborate_charge"])
        runs = {r["reactor"]: float(r["i_ec_mAcm2"]) for r in csv.DictReader(open(os.path.join(ROOT, "results", "hmf_buffer_runs", fn)))}
        assert set(runs) == set(pub), fn
        ch = {a: 100 * (runs[a] / pub[a] - 1) for a in pub}
        moved_counts, moved_medians = [], []
        for reactor, key in REACTOR.items():
            base = [float(r[key]) for r in mat]
            alt = [runs[reactor] if r["reaction"] == RXN else float(r[key]) for r in mat]
            if cnt(base) != cnt(alt):
                moved_counts.append(key)
            if shown(med(base)) != shown(med(alt)):
                moved_medians.append(key)
        res["schemes"][sc] = {"computed_mM": {k: comp[k] for k in ("B(OH)4-", "B(OH)3", "Na+", "polyborate_charge")},
                              "fraction_of_boron_pct": comp["polyborate_fraction_of_boron_pct"], "carried_mM": carr,
                              "carried_is_rounded_computed": rounded_ok, "resolve_pct": [min(ch.values()), max(ch.values())],
                              "resolve_by_reactor_pct": ch, "counts_move": moved_counts, "printed_medians_move": moved_medians,
                              "Na_over_carrier": carr["Na+"] / 40.0}
        ok = ok and rounded_ok and not moved_counts and not moved_medians
        print("scheme %s: %.0f pct of the boron in polyborates; re-solve %+.2f to %+.2f pct; counts move %s; printed medians "
              "move %s" % (sc, comp["polyborate_fraction_of_boron_pct"], min(ch.values()), max(ch.values()),
                           moved_counts, moved_medians))
    res["Na_over_carrier_monomer"] = mm["Na+"] / 40.0
    open(os.path.join(ROOT, "results", "hmf_buffer_speciation.json"), "w").write(json.dumps(res, indent=1))
    print("G-BORATE: %s" % ("PASS -- run_mediated.jl carries the computed buffer; both polyborate schemes are re-solved at "
                             "their computed compositions and move no count and no printed median"
                             if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
