#!/usr/bin/env python3
"""G-THERMAXIS: the cooling CLASS of every thermal verdict along every declared input, over that input's tested range.

Each cell's verdict is classed at its own operating current (thermal_model.REACTORS) as
  passive                U'_req <= U'_passive
  liquid cooling         U'_req <= U_liquid hi   (some cooler within the cell's declared construction range suffices)
  beyond liquid cooling  otherwise
Almost every declared input moves one of these verdicts inside its tested range (audit passes 30-33), so this sweep
finds every class change along every input and writes them as one table (SI Table S12), which the registry rows and
SI S6.2 point to. Each axis lists the registry rows it backs.

Writes results/thermal_axis_sweeps.json:
  axes[]        key, label, unit, range, declared, registry rows, and per cell the class changes across the range
  table[]       the rows of SI Table S12 (every cell-input pair whose class changes inside the range)
  <legacy keys> stack_gap, stack_current, inherited_sigma, volume, beaker_gap, cylinder_gap, vessel_diameter, kappa_T,
                each {rows: [{arch, solvent, declared, crossings: {passive|liquid_any|liquid_best: x}, moves}]}
G-THERMAXIS asserts the sigma axis reproduces G-THERMGEO's passive breaking points (a second code path); its control drops
one of them and must fail.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "figs"))
import thermal_model as TM                                    # noqa: E402

SOLV = [(s[0], s[2], s[3]) for s in TM.SOLVENTS]              # name, kappa (S/m), T_boil (C)
# 2026-10-07 (author): "best construction is super arbitrary". The liquid class is ONE class -- some cooler within the
# declared construction range of the cell's own cooler suffices (U'_req <= U_liquid hi) -- and beyond it no cooler in that
# range does. The split by construction that this sweep used to report rested only on declared cooler dimensions.
CLS = ["passive", "liquid cooling", "beyond liquid cooling"]
SHORT = ["passive", "liquid cooling", "beyond liquid cooling"]
R = {TM.REACTORS[k][0].replace("\n", " ").replace("$\\mu$m", "um"): TM.REACTORS[k] for k in range(len(TM.REACTORS))}
NICE = {"unstirred batch": "unstirred batch", "stirred batch": "stirred batch", "recirculating flow": "recirculating flow",
        "microfluidic 25 um": "microfluidic", "RDE 1600 rpm": "rotating disc", "rotating cyl. 3000 rpm": "rotating cylinder",
        "zero-gap PEM stack": "zero-gap stack"}


def _u(p, kappa, tb):
    """(U'_req, U'_passive, U_liquid lo, U_liquid hi) for a parameter set p (reactor, kmul, tamb, i0, btafel)."""
    reactor = p["reactor"]
    lab, gap, sigma, h_int, i = reactor
    i0, b0 = TM.I0, TM.B_TAFEL
    TM.I0, TM.B_TAFEL = p.get("i0", i0), p.get("btafel", b0)
    try:
        q = TM.q_Wcm2(i, kappa * p.get("kmul", 1.0), gap)
    finally:
        TM.I0, TM.B_TAFEL = i0, b0
    lo, hi = TM.U_liquid(reactor)
    return q / (tb - p.get("tamb", TM.TAMB)), TM.U_passive(sigma, h_int), lo, hi


def klass(p, kappa, tb):
    req, pas, lo, hi = _u(p, kappa, tb)
    return 0 if req <= pas else 1 if req <= hi else 2


def _with(reactor, gap=None, sigma=None, h_int=None, i=None):
    lab, g, sg, h, ii = reactor
    return (lab, g if gap is None else gap, sg if sigma is None else sigma, h if h_int is None else h_int,
            ii if i is None else i)


def intervals(build, x0, x1, kappa, tb, log=True, n=400):
    """Class change points along [x0, x1], refined by bisection: [(x, class_below, class_above)]."""
    xs = [x0 * (x1 / x0) ** (k / n) if log else x0 + (x1 - x0) * k / n for k in range(n + 1)]
    cl = [klass(build(x), kappa, tb) for x in xs]
    out = []
    for a, b, ca, cb in zip(xs, xs[1:], cl, cl[1:]):
        if ca != cb:
            lo, hi = a, b
            for _ in range(80):
                m = math.sqrt(lo * hi) if log else 0.5 * (lo + hi)
                lo, hi = (m, hi) if klass(build(m), kappa, tb) == ca else (lo, m)
            out.append((math.sqrt(lo * hi) if log else 0.5 * (lo + hi), ca, cb))
    return out


AXES = []
# the registry row a cell's change belongs to, where an axis spans rows by cell (h_int is declared per cell class; the
# beaker sigma row defers its liquid-cooling move to the vessel-area row)
HINT_ROW = {100.0: "h_int (stagnant electrolyte)", 800.0: "h_int (stirred electrolyte)",
            2000.0: "h_int (forced flow, centimetre gap)", 5000.0: "h_int (forced flow, thin gap)"}
ELEC_ROW = {s[0]: s[1] for s in TM.SOLVENTS}
ROWS_FOR = lambda ax, arch, solv: ([HINT_ROW[float(R[arch][3])]] if ax["key"] == "h_int" else
                                   ["Vessel external area"] if ax["key"] == "vessel_diameter" else
                                   [ELEC_ROW[solv]] if ax["key"] == "kappa_band" else ax["rows"])


def axis(key, label, fmt, x0, x1, decl, cells, build, rows, log=True, per_solvent_range=None):
    AXES.append(dict(key=key, label=label, fmt=fmt, x0=x0, x1=x1, decl=decl, cells=cells, build=build,
                     rows=rows, log=log, per_solvent_range=per_solvent_range))


def main():
    CENT = [a for a in R if abs(R[a][1] - TM.GAP_BEAKER) < 1e-12]
    VESSEL = ["unstirred batch", "stirred batch", "recirculating flow", "RDE 1600 rpm", "rotating cyl. 3000 rpm"]
    INH = ["recirculating flow", "RDE 1600 rpm", "rotating cyl. 3000 rpm"]
    ALL = list(R)
    cf = json.load(open(os.path.join(ROOT, "results", "thermal_conditional_flips.json")))
    band = {v["solvent"]: v["band_multiple"] for v in cf["verdicts"]}
    kt = json.load(open(os.path.join(ROOT, "results", "figK_kappaT_sensitivity.json")))
    ktf = {s: kt["solvents"][s]["kappa_factor_at_Tboil"] for s, _k, _t in SOLV}
    bnd = json.load(open(os.path.join(ROOT, "results", "si_sensitivity_bounds.json")))["transport"]
    P = lambda a, **kw: dict(reactor=_with(R[a], **{k: v for k, v in kw.items() if k in ("gap", "sigma", "h_int", "i")}),
                             **{k: v for k, v in kw.items() if k in ("kmul", "tamb", "i0", "btafel")})
    sig_d = lambda d: (math.pi * d * TM.CELL_VOLUME_M3 / (math.pi * (d / 2) ** 2) + math.pi * (d / 2) ** 2) / TM.A_ELEC_M2
    sig_v = lambda v: TM.SIGMA_BEAKER * (v / TM.CELL_VOLUME_M3) ** (2.0 / 3.0)
    assert abs(sig_d(TM.VESSEL_ID_M) - TM.SIGMA_BEAKER) < 1e-9
    rt_f = TM.B_TAFEL / 2.0

    axis("kappa_band", "conductivity, across its own band", "%.2fx carried", None, None, 1.0, ALL,
         lambda a, x: P(a, kmul=x), ["3.0 M LiBr/THF", "0.25 M Bu4NBF4/MeCN", "0.2 M NaI/DMF", "1 M NaOH aq"],
         per_solvent_range={s: tuple(band[s]) for s, _k, _t in SOLV})
    axis("kappa_T", "conductivity raised to its value at T_b (S6.3 bracket)", "%.2fx its 25 C value", None, None, 1.0, ALL,
         lambda a, x: P(a, kmul=x), ["Ea (kappa(T) Arrhenius upper bound, S6.3)"],
         per_solvent_range={s: (1.0, ktf[s]) for s, _k, _t in SOLV})
    axis("inherited_sigma", "inherited sigma (factor of 2.5 either way)", "%.2fx declared", 0.4, 2.5, 1.0, INH,
         lambda a, x: P(a, sigma=R[a][2] * x), ["sigma (recirculating flow, RDE, rotating cylinder)"])
    axis("vessel_diameter", "vessel inside diameter at 100 mL", "%.2f cm", 4.0, 6.0, 5.0, VESSEL,
         lambda a, x: P(a, sigma=sig_d(x / 100.0)), ["Vessel external area", "sigma (unstirred 100 mL beaker)"])
    axis("volume", "charge (sigma ~ V^2/3)", "%.0f mL", 50.0, 1000.0, 100.0, VESSEL,
         lambda a, x: P(a, sigma=sig_v(x * 1e-6)), ["Cell volume / electrode area"])
    axis("beaker_gap", "beaker gap (1 cm, where a plate replaces the jacket, to 2.5x)", "%.2f cm", 1.0, 5.0, 2.0, CENT,
         lambda a, x: P(a, gap=x / 100.0), ["Inter-electrode gap (beaker)"])
    axis("cylinder_gap", "rotating-cylinder gap (Eisenberg annuli)", "%.2f cm", TM.GAP_RCE * 100, 6.25,
         TM.GAP_RCE * 100, ["rotating cyl. 3000 rpm"], lambda a, x: P(a, gap=x / 100.0),
         ["Inter-electrode gap (rotating cylinder)"])
    axis("stack_gap", "stack gap", "%.0f um", 50.0, 200.0, 100.0, ["zero-gap PEM stack"],
         lambda a, x: P(a, gap=x * 1e-6), ["Inter-electrode gap (zero-gap PEM stack)"])
    axis("stack_sigma", "stack sigma (pitch 4-12 mm)", "%.2f", 0.51, 1.52, 0.8, ["zero-gap PEM stack"],
         lambda a, x: P(a, sigma=x), ["sigma (zero-gap PEM stack)"])
    axis("micro_sigma", "microfluidic sigma", "%.1f", 3.5, 21.0, 7.0, ["microfluidic 25 um"],
         lambda a, x: P(a, sigma=x), ["sigma (microfluidic 25 um)"])
    axis("stack_current", "stack current density", "%.0f mA cm-2", 500.0, 2000.0, 1000.0, ["zero-gap PEM stack"],
         lambda a, x: P(a, i=x), ["i_design (zero-gap PEM stack)"])
    axis("rde_rate", "rotation rate 400-3600 rpm, as its median current", "%.1f mA cm-2",
         bnd["median, rde"]["lower"], bnd["median, rde"]["upper"], R["RDE 1600 rpm"][4], ["RDE 1600 rpm"],
         lambda a, x: P(a, i=x), ["RDE operating point"])
    axis("rce_rate", "rotation rate 1000-5000 rpm, as its median current", "%.1f mA cm-2",
         bnd["median, rce"]["lower"], bnd["median, rce"]["upper"], R["rotating cyl. 3000 rpm"][4], ["rotating cyl. 3000 rpm"],
         lambda a, x: P(a, i=x), ["RCE operating point"])
    axis("h_int", "electrolyte-side film h_int (50 to 1e6)", "%.0f W m-2 K-1", 50.0, 1.0e6, None, ALL,
         lambda a, x: P(a, h_int=x), ["h_int (stagnant electrolyte)", "h_int (stirred electrolyte)",
                                       "h_int (forced flow, centimetre gap)", "h_int (forced flow, thin gap)"])
    axis("t_amb", "ambient and coolant temperature", "%.1f C", 20.0, 30.0, TM.TAMB, ALL,
         lambda a, x: P(a, tamb=x), ["T_amb (§S6)", "Coolant inlet temperature (liquid cooling)"], log=False)
    axis("i0", "exchange current density i0", "%.3g mA cm-2", 0.01, 10.0, TM.I0, ALL,
         lambda a, x: P(a, i0=x), ["i0 (exchange current density)"])
    axis("alpha", "transfer coefficient alpha", "%.2f", 0.3, 0.7, 0.5, ALL,
         lambda a, x: P(a, btafel=rt_f / x), ["Tafel slope b = 2RT/F per electrode"], log=False)

    res = {"classes": CLS, "axes": [], "table": []}
    # Share of the dissipated heat (Eq. S18-S19) carried by the two activation terms, at each cell's own operating
    # current and the declared i0 and alpha. SI S6 says where activation heat matters, and that sentence reads this.
    res["activation_share"] = {}
    for arch, (lab, gap, sigma, h_int, i) in R.items():
        act = 2 * TM.B_TAFEL * math.asinh(i / (2 * TM.I0))
        res["activation_share"][arch] = {s: float(act / (act + i * 10.0 * gap / k)) for s, k, tb in SOLV}
    for ax in AXES:
        rec = {k: ax[k] for k in ("key", "label", "fmt", "x0", "x1", "rows", "log")}
        rec["declared"] = ax["decl"]
        rec["cells"] = []
        for arch in ax["cells"]:
            for s, k, tb in SOLV:
                x0, x1 = ax["per_solvent_range"][s] if ax["per_solvent_range"] else (ax["x0"], ax["x1"])
                decl = ax["decl"] if ax["decl"] is not None else R[arch][3]
                build = lambda x, arch=arch: ax["build"](arch, x)
                pts = intervals(build, x0, x1, k, tb, log=ax["log"])
                c_decl = klass(build(decl), k, tb)
                rec["cells"].append({"arch": arch, "solvent": s, "range": [x0, x1], "declared": decl,
                                     "declared_class": CLS[c_decl], "changes": [[x, CLS[a], CLS[b]] for x, a, b in pts]})
                if pts:
                    seg, prev = [], x0
                    for x, a, b in pts:
                        seg.append((prev, x, a))
                        prev = x
                    seg.append((prev, x1, pts[-1][2]))
                    f = ax["fmt"]
                    desc = []
                    for i, (lo, hi, c) in enumerate(seg):
                        nm = SHORT[c]
                        desc.append(nm + (" below " + f % hi if i == 0 else " above " + f % lo if i == len(seg) - 1
                                          else " from " + f % lo + " to " + f % hi))
                    res["table"].append({"cell": NICE[arch], "arch": arch, "solvent": s, "input": ax["label"],
                                         "key": ax["key"], "range": (f % x0) + " to " + (f % x1),
                                         "declared": f % decl, "declared_class": SHORT[c_decl],
                                         "classes": "; ".join(desc), "rows": ROWS_FOR(ax, arch, s)})
        res["axes"].append(rec)

    def legacy(key):
        ax = [a for a in res["axes"] if a["key"] == key][0]
        rows = []
        for c in ax["cells"]:
            cr = {}
            for x, a, b in c["changes"]:
                lo_c, hi_c = sorted((CLS.index(a), CLS.index(b)))
                name = {0: "passive", 1: "liquid_best"}.get(lo_c) if hi_c == lo_c + 1 else None   # liquid_best: the liquid/beyond edge
                if name:
                    cr[name] = x
            rows.append({"arch": c["arch"], "solvent": c["solvent"], "declared": c["declared_class"], "crossings": cr,
                         "moves": bool(c["changes"])})
        return {"axis": ax["label"], "range": [ax["x0"], ax["x1"]], "declared": ax["declared"], "rows": rows}
    for key in ("stack_gap", "stack_current", "inherited_sigma", "beaker_gap", "cylinder_gap", "vessel_diameter", "kappa_T",
                "volume"):
        res[key] = legacy(key)
    res["volume"]["sigma"] = {str(v): sig_v(v * 1e-6) for v in (50, 100, 500, 1000)}

    tg = json.load(open(os.path.join(ROOT, "results", "thermal_geometry_sensitivity.json")))
    passive_flips = sorted((r["arch"], r["solvent"]) for r in res["inherited_sigma"]["rows"] if "passive" in r["crossings"])
    ref = sorted((c["arch"], c["solvent"]) for c in tg["conditional_on_sigma"])
    if "--negative-control" in sys.argv:
        bad = passive_flips == ref[1:]
        print("G-THERMAXIS control: %s" % ("GOOD" if not bad else "BAD -- test is inert"))
        sys.exit(0 if not bad else 1)
    ok = passive_flips == ref
    txt = json.dumps(res, indent=1)                      # serialise first: a failed dump must not truncate the artifact
    open(os.path.join(ROOT, "results", "thermal_axis_sweeps.json"), "w").write(txt)
    for t in res["table"]:
        print("%-18s %-8s %-52s %s" % (t["cell"], t["solvent"], t["input"][:52], t["classes"]))
    print("%d cell-input pairs change class inside their tested ranges" % len(res["table"]))
    print("G-THERMAXIS: %s" % ("PASS -- the sigma axis's passive breaking points reproduce G-THERMGEO's"
                                if ok else "FAIL -- passive sigma flips %r differ from G-THERMGEO" % passive_flips))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
