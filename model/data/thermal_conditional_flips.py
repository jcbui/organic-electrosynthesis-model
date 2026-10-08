#!/usr/bin/env python3
"""G-COOLFLIP -- which cooling-class verdict of SI S6.2 survives the conductivity band, and the THF supporting-electrolyte
example of S6.1, both computed from figs/thermal_model.py.

    python data/thermal_conditional_flips.py            # writes results/thermal_conditional_flips.json

S6.2 names, for each architecture and solvent, the cheapest cooling class that holds the cell below boiling at its own
transport ceiling: passive (what the cell rejects unaided) or liquid cooling by the cell's own cooler (thermal_model.U_liquid; COOLING_BANDS).
The required coefficient U'_req = q(i)/(T_b - T_amb) falls as kappa rises, so each verdict has a conductivity at which it
moves one class. This script finds that conductivity as a multiple of the carried value and says whether it lies inside
the band SI Table S4 gives for that electrolyte (si_sensitivity_bounds.KAPPA_BAND), so the SI can call a verdict
conditional exactly when it is. It also evaluates the 0.1 M Bu4NPF6/THF example of S6.1 (measured kappa, electrolytes.csv)
in the unstirred 2 cm cell: its boil-off current and the cell voltage and ohmic drop at that current.

Control: at the carried conductivity the class found here must reproduce U'_req computed directly, and the bisection must
bracket its root (a verdict that does not change anywhere in 1e-3..1e3 x carried is reported as such, never as an endpoint).
"""
import csv, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "figs")); sys.path.insert(0, HERE)
import thermal_model as TM                                              # noqa: E402
import si_sensitivity_bounds as SB                                      # noqa: E402

OUT = os.path.join(ROOT, "results", "thermal_conditional_flips.json")
# 2026-10-06: liquid cooling is each architecture's own cooler (TM.U_liquid: a jacket on a vessel, a cooled plate
# behind a thin cell), classed at the favourable end of its declared construction; whether a verdict also holds at the
# unfavourable end is recorded as "liquid_holds_across_construction".
CLASSES = ["passive", "liquid cooling", "beyond liquid cooling"]          # forced air retired 2026-10-06


def label(r):
    return r[0].replace("\n", " ")


def klass(u_req, u_pass, u_liq):
    if u_req <= u_pass:
        return 0
    if u_req <= u_liq:
        return 1
    return 2


def cls_at(mult, kappa, gap, tb, i, u_pass, u_liq):
    return klass(TM.U_required(i, kappa * mult, gap, tb), u_pass, u_liq)


def flip(kappa, gap, tb, i, u_pass, u_liq, c0, direction):
    """Multiple of kappa at which the class first differs from c0, moving up (direction=+1) or down (-1) in kappa."""
    lo, hi = (1.0, 1e3) if direction > 0 else (1e-3, 1.0)
    end = hi if direction > 0 else lo
    if cls_at(end, kappa, gap, tb, i, u_pass, u_liq) == c0:
        return None
    a, b = (lo, hi)
    for _ in range(200):
        m = (a * b) ** 0.5
        same = cls_at(m, kappa, gap, tb, i, u_pass, u_liq) == c0
        if direction > 0:
            a, b = (m, b) if same else (a, m)
        else:
            a, b = (a, m) if same else (m, b)
    return (a * b) ** 0.5


def main():
    res = {"verdicts": [], "band_source": "si_sensitivity_bounds.KAPPA_BAND",
           "liquid_cooling": {label(r): {"cooler": TM.cooler_type(r), "U_lo": TM.U_liquid(r)[0], "U_hi": TM.U_liquid(r)[1]}
                              for r in TM.REACTORS}}
    for sol, elec, kappa, tb, _state in TM.SOLVENTS:
        lo_k, hi_k = SB.KAPPA_BAND[sol][0], SB.KAPPA_BAND[sol][1]
        for r in TM.REACTORS:
            gap, sigma, h_int, i = r[1], r[2], r[3], r[4]
            u_pass = TM.U_passive(sigma, h_int)
            u_req = TM.U_required(i, kappa, gap, tb)
            u_lo, u_liq = TM.U_liquid(r)
            c0 = klass(u_req, u_pass, u_liq)
            if cls_at(1.0, kappa, gap, tb, i, u_pass, u_liq) != c0:
                raise SystemExit("control: class at the carried kappa disagrees with the direct evaluation")
            up, dn = flip(kappa, gap, tb, i, u_pass, u_liq, c0, +1), flip(kappa, gap, tb, i, u_pass, u_liq, c0, -1)
            band = (lo_k / kappa, hi_k / kappa)
            inside = [m for m in (up, dn) if m is not None and band[0] <= m <= band[1]]
            res["verdicts"].append({"solvent": sol, "electrolyte": elec, "architecture": label(r), "i_mAcm2": round(i, 3),
                                    "U_req": u_req, "U_passive": u_pass, "class": CLASSES[c0], "U_liquid": [u_lo, u_liq],
                                    "liquid_holds_across_construction": bool(u_req <= u_lo) if c0 == 1 else None,
                                    "flip_up_multiple": up, "flip_down_multiple": dn,
                                    "band_multiple": [band[0], band[1]], "conditional": bool(inside),
                                    "class_up": CLASSES[c0 - 1] if up is not None and c0 > 0 else None,
                                    "class_down": CLASSES[c0 + 1] if dn is not None else None})
    # S6.1: 0.1 M Bu4NPF6/THF, measured, in the unstirred 2 cm cell
    el = {r["electrolyte"]: r for r in csv.DictReader(io.open(os.path.join(HERE, "electrolytes.csv"), encoding="utf-8"))}
    k_pf6 = float(el["0.1 M Bu4NPF6/THF"]["kappa_mScm"]) / 10.0           # S/m
    beaker = TM.REACTORS[0]
    tb_thf = [s[3] for s in TM.SOLVENTS if s[0] == "THF"][0]
    ib = TM.i_boil(k_pf6, beaker[1], tb_thf, TM.U_passive(beaker[2], beaker[3]))
    res["thf_pf6_example"] = {"kappa_mScm": k_pf6 * 10, "gap_m": beaker[1], "i_boil_mAcm2": ib,
                              "E_cell_V": float(TM.E_cell(ib, k_pf6, beaker[1])), "ohmic_V": ib * 10.0 * beaker[1] / k_pf6}
    # S6.1: share of the heat that is ohmic at each centimetre-gap cell's boil-off ceiling, and the total-heat ratio
    # between the 2 cm beaker gap and the 25 um microfluidic gap for 0.2 M NaI/DMF at equal current
    shares = []
    for sol, elec, kappa, tb, _state in TM.SOLVENTS:
        for r in TM.REACTORS:
            if r[1] < 1e-2:
                continue
            ib = TM.i_boil(kappa, r[1], tb, TM.U_passive(r[2], r[3]))
            ohm = ib * 10.0 * r[1] / kappa
            act = 2 * TM.B_TAFEL * float(TM.np.arcsinh(ib / (2 * TM.I0)))
            shares.append(ohm / (ohm + act))
    res["ohmic_share_cm_gap"] = [min(shares), max(shares)]
    k_dmf = [s[2] for s in TM.SOLVENTS if s[0] == "DMF"][0]
    res["dmf_heat_ratio_2cm_over_25um"] = {str(i): float(TM.q_Wcm2(i, k_dmf, TM.GAP_BEAKER) / TM.q_Wcm2(i, k_dmf, TM.GAP_MICRO)) for i in (50, 100)}
    res["dmf_ohmic_ratio_2cm_over_25um"] = TM.GAP_BEAKER / TM.GAP_MICRO
    # S6.4 closing paragraph: the vessel-wall conduction the balance omits, through the declared 2-3 mm borosilicate wall
    # of the glass-bodied cells (those on the beaker's sigma), put in series and the boil-off ceiling re-solved
    wl = []
    for sol, elec, kappa, tb, _state in TM.SOLVENTS:
        for r in TM.REACTORS:
            if abs(r[2] - TM.SIGMA_BEAKER) > 1e-9:
                continue
            u0 = TM.U_passive(r[2], r[3])
            i0 = TM.i_boil(kappa, r[1], tb, u0)
            for L in TM.T_VESSEL_WALL:
                uw = r[2] * 1e-4 / (1.0 / r[3] + 1.0 / TM.H_EXT + L / TM.K_PYREX)
                iw = TM.i_boil(kappa, r[1], tb, uw)
                wl.append((100 * (1 - uw / u0), 100 * (1 - iw / i0), (i0 >= r[4]) != (iw >= r[4])))
    res["wall_conduction"] = {"L_m": list(TM.T_VESSEL_WALL), "k_W_mK": TM.K_PYREX, "n_cells": len(wl) // 2,
                              "U_drop_pct": [float(min(w[0] for w in wl)), float(max(w[0] for w in wl))],
                              "ceiling_drop_pct": [float(min(w[1] for w in wl)), float(max(w[1] for w in wl))],
                              "verdicts_changed": int(sum(bool(w[2]) for w in wl))}
    _txt = json.dumps(res, indent=1)               # serialise first: a failed dump must not leave a truncated artifact
    io.open(OUT, "w", encoding="utf-8").write(_txt)
    print("ohmic share at centimetre-gap ceilings %.1f-%.1f %%; DMF total heat 2 cm / 25 um: %s"
          % (100 * min(shares), 100 * max(shares), {k: round(v, 1) for k, v in res["dmf_heat_ratio_2cm_over_25um"].items()}))
    for v in res["verdicts"]:
        print("%-9s %-24s %-20s %s%s" % (v["solvent"], v["architecture"], v["class"],
              "x%.2f up" % v["flip_up_multiple"] if v["flip_up_multiple"] else "", "  conditional" if v["conditional"] else ""))
    e = res["thf_pf6_example"]
    print("Bu4NPF6/THF: i_boil %.1f mA cm-2, E_cell %.1f V, ohmic %.1f V" % (e["i_boil_mAcm2"], e["E_cell_V"], e["ohmic_V"]))
    # (1) the conditional flag the SI prints must be exactly "a reversal multiple lies inside the electrolyte's band";
    # (2) a SECOND code path: the registry's THF row bisects its own liquid-cooling breakpoints (build_param_tables.py)
    #     and must print the same multiples this script computes. --negative-control perturbs one breakpoint by 10 pct.
    neg = "--negative-control" in sys.argv

    def check(perturb):
        """(1) the conditional flag the JSON carries (and make_si.js prints), re-derived WITHOUT the bisection: the class
        evaluated directly on a 401-point log grid across the band must differ from the class at the carried kappa exactly
        when the flag says conditional. Both paths share cls_at, so this tests the bisection and the flag logic, not the
        thermal model itself; (2) the registry's THF row, which bisects its own breakpoints in build_param_tables.py, must
        name each liquid-cooled architecture with ITS multiple, in the order it prints them. perturb: architecture
        whose breakpoint is scaled by 1.1 (control)."""
        out = []
        sol_k = {s[0]: (s[2], s[3]) for s in TM.SOLVENTS}
        rx = {label(r): r for r in TM.REACTORS}
        for v in res["verdicts"]:
            kappa, tb = sol_k[v["solvent"]]
            r = rx[v["architecture"]]
            u_pass, u_liq = TM.U_passive(r[2], r[3]), TM.U_liquid(r)[1]
            c0 = cls_at(1.0, kappa, r[1], tb, r[4], u_pass, u_liq)
            lo, hi = v["band_multiple"]
            grid = [lo * (hi / lo) ** (j / 400.0) for j in range(401)]
            moves = any(cls_at(m, kappa, r[1], tb, r[4], u_pass, u_liq) != c0 for m in grid)
            if bool(v["conditional"]) != moves:
                out.append("%s/%s: conditional=%s, but the class %s inside the band on a direct grid"
                           % (v["solvent"], v["architecture"], v["conditional"], "changes" if moves else "never changes"))
        reg = [r["sensitivity"] for r in csv.DictReader(io.open(os.path.join(ROOT, "data", "parameters_provenance.csv"),
                                                                encoding="utf-8")) if r["parameter"].startswith("3.0 M LiBr/THF")]
        liq = [v for v in res["verdicts"] if v["solvent"] == "THF" and v["class"] == "liquid cooling"]
        if len(reg) != 1:
            return out + ["the registry's 3.0 M LiBr/THF row is missing or duplicated"], liq
        m = re.search(r"tighter than any boil-off verdict: the ([^:.]+?) each hold their THF duty with liquid cooling.*?below (.+?) the carried conductivity", reg[0])
        if not m:
            return out + ["the registry's liquid-cooling breakpoint sentence is gone; re-point this check"], liq
        names = re.split(r", | and ", m.group(1))
        mults = re.findall(r"(\d+\.\d+)x", m.group(2))
        short = {"rotating disc": "RDE 1600 rpm", "rotating cylinder": "rotating cyl. 3000 rpm",
                 "zero-gap stack": "zero-gap PEM stack"}
        printed = {short.get(n, n): x for n, x in zip(names, mults)}
        if len(names) != len(mults) or len(printed) != len(liq):
            out.append("registry names %d architectures with %d multiples; the model has %d liquid-cooled THF verdicts"
                       % (len(names), len(mults), len(liq)))
        for v in liq:
            want = "%.2f" % (v["flip_down_multiple"] * (1.1 if v["architecture"] == perturb else 1.0))
            if printed.get(v["architecture"]) != want:
                out.append("registry THF row gives %s for the %s; this script computes %sx"
                           % (printed.get(v["architecture"]), v["architecture"], want))
        return out, liq

    fails, liq = check(None)
    for f in fails:
        print("  FAIL  " + f)
    if neg:
        if fails:
            print("G-COOLFLIP control: INCONCLUSIVE -- the unperturbed check already fails")
            sys.exit(1)
        bad, _ = check("RDE 1600 rpm")
        v0 = res["verdicts"][0]                       # the JSON is already written; this flip is in memory only
        v0["conditional"] = not v0["conditional"]
        bad2, _ = check(None)
        v0["conditional"] = not v0["conditional"]
        bad += bad2
        ok = any("RDE 1600 rpm" in f for f in bad) and any(f.startswith(v0["solvent"] + "/" + v0["architecture"] + ": conditional")
                                                         for f in bad2)
        for f in bad:
            print("  (control) " + f)
        print("G-COOLFLIP control: %s" % ("GOOD" if ok else "BAD -- test is inert"))
        sys.exit(0 if ok else 1)
    if fails:
        print("G-COOLFLIP: FAIL -- %d disagreement(s)" % len(fails))
        sys.exit(1)
    print("G-COOLFLIP: PASS -- every conditional flag agrees with a direct grid over its band, and the registry's THF "
          "row gives each of the %d liquid-cooled architectures the breakpoint this script computes; wrote %s"
          % (len(liq), os.path.relpath(OUT, ROOT)))

if __name__ == "__main__":
    main()
