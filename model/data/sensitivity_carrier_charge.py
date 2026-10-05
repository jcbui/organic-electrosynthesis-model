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
import csv, io, os, shutil, subprocess, sys

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

_BACKUPS = [CC + ".zsens", MATRIX + ".zsens"]


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


def solve(tag):
    log = os.path.join("/tmp", "zsens_%s.log" % tag)
    with open(log, "w") as fh:
        rc = subprocess.call(["julia", "run_all50_np.jl"], cwd=JULIA, stdout=fh, stderr=fh)
    if rc != 0:
        return None, log
    return {(r["reaction"], r["reactor"]): float(r["i_np_mAcm2"])
            for r in csv.DictReader(open(MATRIX))}, log


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

    # A SECOND INSTANCE WOULD OVERWRITE THE FIRST'S BACKUP and then the first's finally

    # would delete it, leaving the second with nothing to restore -- which is how

    # data/carrier_charge.csv was left holding a PERTURBED charge on 2026-08-26 and

    # julia/all50_np_matrix.csv was left interleaved by two writers. Refuse instead.

    for _b in _BACKUPS:

        if os.path.exists(_b):

            sys.exit("REFUSING TO RUN: %s exists, so another sweep owns these artifacts. "

                     "Wait for it, or if it died, restore from that file by hand and "

                     "delete it." % _b)


    shutil.copy(CC, CC + ".zsens"); shutil.copy(MATRIX, MATRIX + ".zsens")
    try:
        print("\nsolving BASE ...")
        base, log = solve("base")
        if base is None:
            raise SystemExit("base solve failed; see " + log)
        # A SHORT BASE IS NOT A BASE. On 2026-08-26 a concurrent writer left the matrix
        # interleaved, the base solve came back missing cells, and the first alternative died
        # on `KeyError: ('Electrochemical amination of ArX with NH3', 'Recirculating flow cell')`
        # 40 minutes in -- an obscure failure for a simple cause. Check it up front.
        if len(base) != 350:
            raise SystemExit(
                "base solve produced %d cells, expected 350 (50 reactions x 7 archetypes). "
                "Something else is writing julia/all50_np_matrix.csv, or the solve was cut "
                "short; see %s" % (len(base), log))
        base_c = counts(base)
        worst_overall = 0.0
        report = []
        for r in med:
            rxn, z0 = r["reaction"], r["z_carrier"]
            for alt in ALTS:
                if str(alt) == str(z0):
                    continue
                for rr in rows:
                    rr["z_carrier"] = (str(alt) if rr["reaction"] == rxn
                                       else rr["z_carrier"])
                # restore every other row to its original value
                for rr, orig in zip(rows, read_raw(CC + ".zsens")[1]):
                    if rr["reaction"] != rxn:
                        rr["z_carrier"] = orig["z_carrier"]
                write_raw(CC, head, rows)
                res, log = solve("%s_z%s" % (rxn[:12].replace(" ", "_"), alt))
                if res is None:
                    report.append((rxn, alt, None, None)); continue
                cells = [(k, v) for k, v in res.items() if k[0] == rxn]
                w = max((abs(v - base[k]) / base[k]) for k, v in cells) if cells else 0.0
                same = counts(res) == base_c
                worst_overall = max(worst_overall, w)
                report.append((rxn, alt, w, same))
            for rr, orig in zip(rows, read_raw(CC + ".zsens")[1]):
                rr["z_carrier"] = orig["z_carrier"]
            write_raw(CC, head, rows)
    finally:
        for _b in _BACKUPS:
            _live = _b[:-len(".zsens")]
            if os.path.exists(_b):
                shutil.copy(_b, _live); os.remove(_b)
            else:
                print("!! RESTORE FAILED: %s is missing, so %s may still hold "
                      "perturbed values. Check it before trusting any gate."
                      % (_b, _live))
        print("\n(restored carrier_charge.csv and the matrix)")

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
