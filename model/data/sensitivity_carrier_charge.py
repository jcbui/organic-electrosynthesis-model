#!/usr/bin/env python3
"""G-ZSENS -- bound the exposure of the model to the carrier charges that are not yet certain.

    cd Section4_Model && python data/sensitivity_carrier_charge.py

WHY
---
Migration acts only on a CHARGED carrier, so `z_carrier` decides which rows move and by how much.
A wrong z does not fail loudly: it shifts a ceiling by up to a factor of two in silence.
`data/carrier_charge.csv` now carries 43 rows at high confidence and 7 at medium; five of those
seven are metal complexes carried NEUTRAL because that is how the precursor is written, while the
electroactive species could be cationic or anionic.

Rather than argue about them one at a time, this measures what the uncertainty is worth. Each
medium-confidence row is re-solved at plausible alternative charges and the ceilings and the
headline >=25 / >=50 counts are compared with the base case.

A row whose ceiling is unmoved by its charge does not need its charge settled before publication,
and that can be said with a number attached. A row that moves has to be resolved.
"""
import csv, glob, io, os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JULIA = os.path.join(ROOT, "julia")
CC = os.path.join(HERE, "carrier_charge.csv")
MATRIX = os.path.join(JULIA, "all50_np_matrix.csv")
# z = 0 WAS MISSING, and it is the only chemically plausible alternative for the two rows whose
# base is -1. The list was written for the five metal complexes carried NEUTRAL, where +1/+2 are
# the live question; applied unchanged to an anionic carrier it tested a CATIONIC carboxylate and
# a CATIONIC phthalimide -- species that do not exist -- while never testing the neutral acid,
# which for the decarboxylative row is the DOMINANT form (its own registry note: Et3N 7.5 mM
# against 0.1 M acid, so at most ~7.5% is deprotonated).
ALTS = [-1, 0, 1, 2]

DATA_INPUTS = ["reactions_50.csv", "electrolyte_ions.csv", "electrode_direction.csv"]


def read_raw(path):
    txt = io.open(path, encoding="utf8").read()
    head = [l for l in txt.split("\n") if l.startswith("#")]
    body = "\n".join(l for l in txt.split("\n") if not l.startswith("#"))
    rows = list(csv.DictReader(io.StringIO(body)))
    return head, rows


def write_raw(path, head, rows):
    fields = [k for k in rows[0].keys() if k is not None]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
    w.writeheader(); w.writerows(rows)
    txt = "\n".join(head) + ("\n" if head else "") + buf.getvalue()
    back = list(csv.DictReader(io.StringIO("\n".join(
        l for l in txt.split("\n") if not l.startswith("#")))))
    if len(back) != len(rows) or any(None in r for r in back):
        raise SystemExit("refusing to write a carrier_charge table that does not round-trip")
    io.open(path, "w", encoding="utf8", newline="").write(txt)


def solve_row(tag, rxn, head, rows):
    """Solve ONE row of the Nernst-Planck layer, with the carrier-charge table given, in an isolated
    copy of julia/ and data/. Until 2026-10-05 every alternative rewrote data/carrier_charge.csv in
    place and re-solved all 350 cells over the published matrix -- twenty-one full solves, during
    which the tree held a perturbed charge. A charge changes its own row only."""
    d = tempfile.mkdtemp(prefix="zsens_")
    try:
        os.makedirs(os.path.join(d, "julia")); os.makedirs(os.path.join(d, "data"))
        for f in glob.glob(os.path.join(JULIA, "*.jl")):
            shutil.copy(f, os.path.join(d, "julia"))
        for f in DATA_INPUTS:
            shutil.copy(os.path.join(HERE, f), os.path.join(d, "data"))
        write_raw(os.path.join(d, "data", "carrier_charge.csv"), head, rows)
        log = os.path.join(tempfile.gettempdir(), "zsens_%s.log" % tag)
        with open(log, "w") as fh:
            rc = subprocess.call(["julia", "run_all50_np.jl"], cwd=os.path.join(d, "julia"), stdout=fh, stderr=fh,
                                 env=dict(os.environ, NP_ONLY=rxn))
        if rc != 0:
            return None, log
        out = {(r["reaction"], r["reactor"]): float(r["i_np_mAcm2"])
               for r in csv.DictReader(open(os.path.join(d, "julia", "all50_np_matrix.csv")))}
        return (out if len(out) == 7 and all(k[0] == rxn for k in out) else None), log
    finally:
        shutil.rmtree(d, ignore_errors=True)


def counts(res):
    RM = {"Unstirred batch": "natural", "Stirred batch": "stirred",
          "Recirculating flow cell": "flow", "RDE 1600 rpm": "rde",
          "Rotating cylinder 3000 rpm": "rce", "ANEC flow cell": "anec", "Microfluidic cell (25 um gap)": "micro"}
    per = {}
    for (rxn, rct), v in res.items():
        per.setdefault(RM.get(rct, rct), []).append(v)
    return {c: (sum(1 for v in vals if v >= 25), sum(1 for v in vals if v >= 50))
            for c, vals in per.items()}


def main():
    head, rows = read_raw(CC)
    med = [r for r in rows if r.get("confidence", "").lower() == "medium"]
    print("medium-confidence carrier charges: %d" % len(med))
    for r in med:
        print("   %-46s %-24s z=%s" % (r["reaction"][:46], r["carrier_species"][:24], r["z_carrier"]))
    if not med:
        print("\nG-ZSENS: nothing at medium confidence -- trivially PASSES"); return 0

    ## BASE = the published Nernst-Planck matrix; a short base is not a base.
    base = {(r["reaction"], r["reactor"]): float(r["i_np_mAcm2"]) for r in csv.DictReader(open(MATRIX))}
    if len(base) != 350:
        raise SystemExit("julia/all50_np_matrix.csv holds %d cells, expected 350 (50 reactions x 7 "
                         "archetypes); re-solve it before sweeping" % len(base))
    base_c = counts(base)
    ## CONTROL: an unperturbed one-row solve must reproduce the published cells.
    ctl, log = solve_row("control", med[0]["reaction"], head, rows)
    if ctl is None or any(abs(v - base[k]) > 1e-9 * max(1.0, abs(base[k])) for k, v in ctl.items()):
        raise SystemExit("control failed: an unperturbed one-row solve of %r does not reproduce the "
                         "published cells; see %s" % (med[0]["reaction"], log))
    print("control: unperturbed one-row solve of %r reproduces its 7 published cells" % med[0]["reaction"][:40])
    jobs = [(r["reaction"], alt) for r in med for alt in ALTS if str(alt) != str(r["z_carrier"])]
    def run(job):
        rxn, alt = job
        rows2 = [dict(rr, z_carrier=(str(alt) if rr["reaction"] == rxn else rr["z_carrier"])) for rr in rows]
        res, lg = solve_row("%s_z%s" % (rxn[:12].replace(" ", "_"), alt), rxn, head, rows2)
        return job, res
    print("\nsolving %d alternatives, %d at a time ..." % (len(jobs), int(os.environ.get("ZSENS_JOBS", "4"))))
    with ThreadPoolExecutor(max_workers=int(os.environ.get("ZSENS_JOBS", "4"))) as ex:
        results = dict(ex.map(run, jobs))
    worst_overall = 0.0
    report = []
    for rxn, alt in jobs:
        res = results[(rxn, alt)]
        if res is None:
            report.append((rxn, alt, None, None)); continue
        w = max(abs(v - base[k]) / base[k] for k, v in res.items())
        same = counts({**base, **res}) == base_c
        worst_overall = max(worst_overall, w)
        report.append((rxn, alt, w, same))
    if any(r[2] is None for r in report):
        raise SystemExit("an alternative-charge solve failed: %s" % [(r[0], r[1]) for r in report if r[2] is None])

    print("\n%-46s %-5s %-14s %s" % ("reaction", "z", "max change", "counts unchanged?"))
    for rxn, alt, w, same in report:
        if w is None:
            print("  %-46s %-5s %-14s %s" % (rxn[:46], alt, "SOLVE FAILED", "-")); continue
        print("  %-46s %-5s %-14s %s" % (rxn[:46], alt, "%.1f%%" % (100 * w),
                                         "yes" if same else "NO -- counts move"))
    # PERSIST THE REPORT. This printed its table and kept nothing, so the runner's one-line
    # summary was the only surviving trace of a 90-minute solve.
    import json as _json
    _out = os.path.join(ROOT, "results", "carrier_charge_sensitivity.json")
    _json.dump({"alternatives": ALTS,
                "worst_ceiling_change_pct": round(100 * worst_overall, 3),
                "rows": [{"reaction": r[0], "z_alt": r[1],
                          "max_ceiling_change_pct": None if r[2] is None else round(100 * r[2], 3),
                          "counts_unchanged": r[3]} for r in report]},
               io.open(_out, "w", encoding="utf8"), indent=1)
    print("-> %s" % _out)
    moved = [r for r in report if r[3] is False]
    print("\nworst ceiling change across every alternative charge: %.1f%%" % (100 * worst_overall))
    if moved:
        print("G-ZSENS: REVIEW NEEDED -- %d alternative(s) change a published count" % len(moved))
        return 1
    print("G-ZSENS: PASS -- no alternative charge on any medium-confidence row moves a count")
    return 0


if __name__ == "__main__":
    sys.exit(main())
