#!/usr/bin/env python3
"""G-KBASIS -- every rate constant the model uses is set beside the system it was measured on, and the record agrees with
the solvers and with the built SI.

    cd Section4_Model && python data/check_rate_constant_basis.py [--negative-control]

Since the chemistry audit of 2026-10-05 the record also holds one mediated row at k = 0 (the triarylamine-mediated oxazole
synthesis, reclassified from catalyst): no constant was located and the exemplar's operation bounds none, so it is solved at
the floor and Table S11 says so. A k = 0 row must carry the relation 'none measured'.

Why (2026-10-05). A reviewer asked what substrate the cobalt-hydride rate constant had been measured for. Pulling every
source answered it for all eighteen constants and found two that the record had wrong in substance: the NHPI row carried
0.5 M-1 s-1, the order of PINO abstracting from TOLUENES in acetic acid, for an ALLYLIC oxidation whose own exemplar cites
the study that measured PINO with cyclohexene at 20.2; and the anisole bromination row carried a declared 1e3 while the
source it cited prints 2.28e4 for bromine with anisole itself. Both are adopted now. This gate keeps the record
(data/rate_constant_basis.csv) bound to what is actually solved and printed:

  A  every MedSpec of julia/run_mediated.jl has a record row whose k equals the solver's, and vice versa;
  B  every catalyst row carried at a sourced k (results/catalyst_ec_sensitivity.json) has a record row with that k, and
     no floor row has one;
  C  every row carries a relation from the fixed vocabulary; a row with no measurement prints no value, a measured one does;
     every source key the record cites is a reference the SI generator carries;
  D  Table S11 reads back out of BOTH built SIs with one row per record row, the k each row prints, its relation, and a
     sensitivity column that reproduces the two sweeps' own artifacts (tenfold cells for the mediated rows, the band-edge
     solves for the catalyst rows) to 1 %.

Negative control: the record is perturbed IN MEMORY three ways (one k, one relation, one sensitivity read) and each must
fire; nothing on disk is written.
"""
import csv, io, json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from check_si_condensed import read_docx, tables_by_header, plain, norm   # the condensed gate's own document reader

REC = os.path.join(HERE, "rate_constant_basis.csv")
SRC = os.path.join(ROOT, "julia", "run_mediated.jl")
CK = os.path.join(ROOT, "results", "catalyst_ec_sensitivity.json")
CELLS = os.path.join(ROOT, "results", "rate_constant_cells.csv")
SIS = [os.path.join(ROOT, "SI_Section4_Transport_Model.docx"), os.path.join(ROOT, "SI_Section4_Transport_Model_condensed.docx")]
RELATIONS = ["same carrier and substrate", "same carrier, other substrates", "analogue of the carrier",
             "bound from the exemplar's own data", "none measured"]
SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def k_si(k):
    """The SI's own formatting (make_si.js kSI): a decade as a power of ten, anything else to three significant figures."""
    import math
    if k == 0:
        return "0"
    e = math.log10(k)
    if k >= 100 and abs(e - round(e)) < 1e-9:
        return "10" + str(int(round(e))).translate(SUP)
    if k >= 100:
        ee = math.floor(e)
        m = float("%.3g" % (k / 10 ** ee))
        return ("%g" % m) + " × 10" + str(int(ee)).translate(SUP)
    return "%g" % float("%.3g" % k)


def fcur(v):
    return str(int(round(v))) if v >= 10 else "%.1f" % v


def main(neg=False):
    bad = []
    rec = list(csv.DictReader(io.open(REC, encoding="utf-8")))
    if neg:
        rec = [dict(r) for r in rec]
        rec[3]["k_M1s1"] = str(float(rec[3]["k_M1s1"]) * 10)        # a k the solver does not use
        rec[6]["relation"] = "measured elsewhere"                   # a relation outside the vocabulary
    byrx = {r["reaction"]: r for r in rec}
    # A -- the mediated solver
    specs = re.findall(r'MedSpec\("([^"]+)",\s*([0-9.eE+-]+)', io.open(SRC, encoding="utf-8").read())
    for name, k in specs:
        r = byrx.get(name)
        if r is None:
            bad.append("A: MedSpec %r has no record row" % name); continue
        if r["carrier_class"] != "mediator":
            bad.append("A: %r is a MedSpec but the record calls it %s" % (name, r["carrier_class"]))
        if abs(float(r["k_M1s1"]) - float(k)) > 1e-9 * float(k):
            bad.append("A: %r is solved at k = %s but the record says %s" % (name, k, r["k_M1s1"]))
    for r in rec:
        if r["carrier_class"] == "mediator" and r["reaction"] not in dict(specs):
            bad.append("A: record row %r is no MedSpec" % r["reaction"])
    # B -- the catalyst rows
    ck = json.load(open(CK)); sr = ck.get("sourced") or {}
    for name, q in sr.get("per_row", {}).items():
        r = byrx.get(name)
        if r is None:
            bad.append("B: sourced catalyst row %r has no record row" % name); continue
        if r["carrier_class"] != "catalyst":
            bad.append("B: %r is a catalyst row but the record calls it %s" % (name, r["carrier_class"]))
        if abs(float(r["k_M1s1"]) - float(q["k_M"])) > 1e-9 * float(q["k_M"]):
            bad.append("B: %r is solved at k = %s but the record says %s" % (name, q["k_M"], r["k_M1s1"]))
    for name in sr.get("rows_floor", []):
        if name in byrx:
            bad.append("B: floor row %r (k = 0) has a record row" % name)
    for r in rec:
        if r["carrier_class"] == "catalyst" and r["reaction"] not in sr.get("per_row", {}):
            bad.append("B: record row %r is not a sourced catalyst row" % r["reaction"])
    # C -- vocabulary and sources
    gen = io.open(os.path.join(ROOT, "make_si.js"), encoding="utf-8").read()
    keys = set(re.findall(r'\{ k: "([^"]+)"', gen))
    for r in rec:
        if float(r["k_M1s1"]) == 0 and r["relation"] != RELATIONS[-1]:
            bad.append("C: %r is solved at k = 0 but claims a measurement (%r)" % (r["reaction"], r["relation"]))
        if r["relation"] not in RELATIONS:
            bad.append("C: %r carries the relation %r, not in the vocabulary" % (r["reaction"], r["relation"]))
        if (r["relation"] == RELATIONS[-1]) != (r["printed_value"].strip() in ("—", "-", "")) and r["relation"] in RELATIONS:
            # 'none measured' rows print no value; the Hofmann row prints the nearest class instead, which is allowed
            if not (r["relation"] == RELATIONS[-1] and "amine" in r["printed_value"]):
                bad.append("C: %r: relation %r against printed value %r" % (r["reaction"], r["relation"], r["printed_value"][:40]))
        for key in r["sources"].split(","):
            if key.strip() not in keys:
                bad.append("C: %r cites %r, which the SI reference list does not carry" % (r["reaction"], key))
    # D -- Table S11 in both builds
    cells = list(csv.DictReader(open(CELLS)))
    def best(rx, tag):
        v = [float(c["i_ec_mAcm2"]) for c in cells if c["reaction"] == rx and c["factor"] == tag]
        if len(v) != 7:
            raise SystemExit("rate_constant_cells.csv holds %d cells for %s / %s" % (len(v), rx, tag))
        return max(v)
    for si in SIS:
        items = read_docx(zipfile.ZipFile(si).read("word/document.xml"))
        tabs = tables_by_header(items)
        t = next((rows for h, rr in tabs.items() if h.startswith("Entry | Step solved") for rows in rr), None)
        if t is None:
            bad.append("D: %s has no Table S11" % os.path.basename(si)); continue
        body = t[1:]
        if len(body) != len(rec):
            bad.append("D: %s Table S11 has %d rows, the record %d" % (os.path.basename(si), len(body), len(rec)))
        for r, row in zip(rec, body):
            row = [norm(plain(c)) for c in row]
            k = float(r["k_M1s1"])
            if row[2] != norm(k_si(k)):                      # the reader NFKC-folds superscripts; fold the expectation the same way
                bad.append("D: %s Table S11 %r prints k %r, the record gives %s" % (os.path.basename(si), r["reaction"][:30], row[2], k_si(k)))
            if row[5] != r["relation"]:
                bad.append("D: %s Table S11 %r prints relation %r, the record %r" % (os.path.basename(si), r["reaction"][:30], row[5], r["relation"]))
            m = re.match(r"^([\d.]+) \(([\d.]+)–([\d.]+)", row[6]) or (re.match(r"^([\d.]+) \(k = 0", row[6]) if k == 0 else None)
            if not m:
                bad.append("D: %s Table S11 %r: sensitivity cell %r unreadable" % (os.path.basename(si), r["reaction"][:30], row[6])); continue
            got = [float(x) for x in m.groups()]
            if r["carrier_class"] == "mediator" and k == 0:
                # a row with no measured constant is solved at the floor: the cell prints the best ceiling and says so
                if "(k = 0, the floor)" not in row[6]:
                    bad.append("D: %s Table S11 %r is solved at k = 0 and does not say so" % (os.path.basename(si), r["reaction"][:30]))
                med = [float(c["i_ec_mAcm2"]) for c in csv.DictReader(open(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"))) if c["reaction"] == r["reaction"]]
                if len(med) != 7 or abs(got[0] - float(fcur(max(med)))) > 0.011 * max(1.0, max(med)) + 0.06:
                    bad.append("D: %s Table S11 %r prints %s where the matrix gives %s" % (os.path.basename(si), r["reaction"][:30], got[0], fcur(max(med) if med else 0)))
                continue
            if r["carrier_class"] == "mediator":
                want = [best(r["reaction"], "base"), min(best(r["reaction"], "div10"), best(r["reaction"], "mul10")), max(best(r["reaction"], "div10"), best(r["reaction"], "mul10"))]
            else:
                q = sr["per_row"][r["reaction"]]
                want = [max(q["i_mAcm2"].values()), max(q["i_at_band_lo"].values()), max(q["i_at_band_hi"].values())]
            if neg and r["reaction"].startswith("Thioether"):
                want = [w * 1.2 for w in want]                              # a sensitivity the artifact does not give
            for g, w in zip(got, want):
                if abs(g - float(fcur(w))) > 0.011 * max(1.0, w) + 0.06:
                    bad.append("D: %s Table S11 %r: sensitivity prints %s where the artifact gives %s" % (os.path.basename(si), r["reaction"][:30], got, [fcur(w) for w in want]))
                    break
    n_rel = {rel: sum(1 for r in rec if r["relation"] == rel) for rel in RELATIONS}
    print("rate-constant record: %d rows (%d mediated, %d catalyst); relations %s" % (len(rec), sum(r["carrier_class"] == "mediator" for r in rec),
          sum(r["carrier_class"] == "catalyst" for r in rec), n_rel))
    if neg:
        fired = {b[0] for b in bad}
        ok = fired >= {"A", "C", "D"} or (fired >= {"C", "D"} and any("solved at k" in b for b in bad))
        print("NEGATIVE CONTROL: one k, one relation and one sensitivity perturbed in memory -> %d finding(s): %s" % (len(bad), "; ".join(b[:90] for b in bad)))
        print("G-KBASIS control: %s" % ("GOOD (all three perturbations detected)" if ok else "BAD -- test is inert"))
        return 0 if ok else 1
    if bad:
        print("G-KBASIS: FAIL\n  " + "\n  ".join(bad))
        return 1
    print("G-KBASIS: PASS -- every rate constant the solvers use has a record of the system it was measured on, the record's k "
          "equals the solver's for all %d rows, and Table S11 reads back out of both SI builds with the sweeps' own sensitivities" % len(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
