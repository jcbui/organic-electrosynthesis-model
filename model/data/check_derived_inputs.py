#!/usr/bin/env python3
"""G-DERIVE -- does every derived row meet the standard's own definition of state B?

    cd Section4_Model && python data/check_derived_inputs.py
    cd Section4_Model && python data/check_derived_inputs.py --negative-control

WHY
---
PROVENANCE_STANDARD.md Sect. B: a derived row is "computed by an explicitly named, citable method
from inputs that are THEMSELVES state A or B". The builder asserts two of the standard's rules at
build time -- every measured row carries a locator, every assumption row carries a sensitivity --
and never asserted this one. On 2026-09-13 that let two rows through: both beaker sigma rows were
classed `derived` while resting on `Vessel external area`, which is `assumption`, and on the
declared electrode area. Neither cited a method; each cited a ROW.

The distinction the standard draws is not "no declared inputs". delta (unstirred batch) is derived
and its operating point is declared -- but it cites the Wilke/Eisenberg/Tobias EQUATION, and the
declared operating point carries its own assumption row with its own sensitivity. That is the
shape a derived row must have: a citable method, plus separately registered inputs.

WHAT IT ASSERTS
---------------
  1. every intra-registry reference of the form "row '<name>'" resolves to a row that exists;
  2. a derived row whose citation names ONLY other registry rows -- i.e. cites no method -- must
     have every one of those rows in state A or B;
  3. a derived row that cites a method (anything other than a bare row reference) is accepted,
     because the method is the citation the standard asks for.

A row may be exempted only verbatim, with its reason.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(HERE, "parameters_provenance.csv")
ROW_REF = re.compile(r"row '([^']+)'")

EXEMPT = {}


def load(path=REG):
    return list(csv.DictReader(open(path, encoding="utf8")))


def cites_only_rows(cit):
    """True when the citation is nothing but references to other registry rows."""
    stripped = ROW_REF.sub("", cit or "")
    stripped = re.sub(r"(of|in|the|this|registry|and|,|\.|;|:|declared basis|value of)", "",
                      stripped, flags=re.I)
    return not stripped.strip()


def cls_of(rows, name):
    return next((r["provenance_class"] for r in rows if r["parameter"] == name), None)


def audit(rows):
    cls = {r["parameter"]: r["provenance_class"] for r in rows}
    dangling, weak = [], []
    for r in rows:
        cit = r.get("citation") or ""
        for ref in ROW_REF.findall(cit):
            if ref not in cls:
                dangling.append((r["parameter"], ref))
        if r["provenance_class"] != "derived" or r["parameter"] in EXEMPT:
            continue
        refs = ROW_REF.findall(cit)
        if refs and cites_only_rows(cit):
            bad = [x for x in refs if cls.get(x) not in ("measured", "derived")]
            if bad:
                weak.append((r["parameter"], bad))
    return dangling, weak


def main(neg=False):
    rows = load()
    print("G-DERIVE -- the state-B input rule, asserted against the registry")
    print("  %d rows; %d derived" % (len(rows), sum(r["provenance_class"] == "derived" for r in rows)))
    for k, v in EXEMPT.items():
        print("  exempt: %s -- %s" % (k, v))

    if neg:
        # INJECT the two defects rather than perturb an existing row. The first version of this
        # control re-classed `Vessel external area` to assumption, which worked only while the
        # sigma rows cited a ROW; once they cited a method the gate stopped looking at them and
        # the control went inert (CLAUDE.md trap 10, aimed at a control). Injected probes cannot
        # go stale that way. Perturbs a COPY; the registry on disk is never written by a control.
        base = dict(rows[0])
        probe_c = dict(base, parameter="__CONTROL derived-on-assumption", provenance_class="derived",
                       citation="row 'Cell volume / electrode area' of this registry")
        probe_d = dict(base, parameter="__CONTROL dangling", provenance_class="derived",
                       citation="row 'A Row That Does Not Exist' of this registry")
        assert cls_of(rows, "Cell volume / electrode area") == "assumption", (
            "the control's state-C probe row is no longer assumption-class; re-point it")
        rows = rows + [probe_c, probe_d]

    dangling, weak = audit(rows)
    for p, ref in dangling:
        print("  DANGLING  %-46s cites row '%s', which does not exist" % (p[:46], ref))
    for p, bad in weak:
        print("  STATE-B   %-46s is derived but rests only on %s"
              % (p[:46], ", ".join("'%s'" % b for b in bad)))

    if neg:
        got_weak = any(p == "__CONTROL derived-on-assumption" for p, _ in weak)
        got_dang = any(p == "__CONTROL dangling" for p, _ in dangling)
        print("\nNEGATIVE CONTROL: one derived-on-assumption row and one dangling reference "
              "injected into a copy of the registry.")
        print("G-DERIVE control: %s (state-B probe caught: %s; dangling probe caught: %s)"
              % ("GOOD" if (got_weak and got_dang) else "BAD -- test is inert",
                 got_weak, got_dang))
        return 0 if (got_weak and got_dang) else 1

    if dangling or weak:
        print("\nG-DERIVE: FAIL -- %d dangling reference(s), %d derived row(s) that do not meet "
              "the standard's definition of state B." % (len(dangling), len(weak)))
        return 1
    print("\nG-DERIVE: PASS -- every intra-registry reference resolves, and every derived row "
          "either cites a method or rests on inputs that are themselves measured or derived.")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
