#!/usr/bin/env python3
"""G-RXNTABLE: audit SI Table S10 (the balanced reaction behind each of the fifty rows) AS BUILT.

`build_reaction_stoichiometry.py` asserts balance while it writes the table's source. This gate does not
trust that: it reads the table back out of the built SI and checks it by routes the builder does not use.

  A  SECOND CODE PATH FOR THE CHEMISTRY. Every species' composition is recomputed from its SMILES by the small
     parser in this file (no RDKit), compared with RDKit's, and each reaction is re-balanced, atoms and
     charge, on the recomputed compositions.
  B  THE PRINTED TABLE. For every row of the built document: the overall equation printed is the one whose
     balance A checked; the charge each species PRINTS (its trailing superscript) is its real charge, so the
     equation balances in charge as read; the electrons printed, per limiting substrate, are the number in
     the table's own electron column; the electrons sit on the side the Electrode column names; and name,
     order and carrier type agree with Table S2 of the same document.
  C  The condensed SI carries the identical table.

    python data/check_reaction_table.py                      (needs RDKit: run with the echem_analysis interpreter)
    python data/check_reaction_table.py --negative-control   four perturbations, each must fire
"""
import csv, io, os, re, sys, zipfile
import xml.etree.ElementTree as ET
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SI = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")
SIC = os.path.join(ROOT, "SI_Section4_Transport_Model_condensed.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# ───────────────────────── a SMILES composition counter that shares nothing with RDKit ─────────────────────────
ORGANIC = {"B": (3,), "C": (4,), "N": (3, 5), "O": (2,), "P": (3, 5), "S": (2, 4, 6), "F": (1,), "Cl": (1,), "Br": (1,), "I": (1,)}
BOND = {"-": 1, "=": 2, "#": 3, "$": 4, ":": 1.5, "/": 1, "\\": 1}


def smiles_composition(smi):
    """Element counts and net charge ('q') of a SMILES string; implicit hydrogens by the OpenSMILES valence rule."""
    atoms = []                      # dict(sym, arom, h (None = implicit), q, bonds=[orders])
    stack, prev, pend, rings = [], None, None, {}
    i, n = 0, len(smi)

    def link(a, b, order):
        if order is None:
            order = 1.5 if (atoms[a]["arom"] and atoms[b]["arom"]) else 1
        atoms[a]["bonds"].append(order); atoms[b]["bonds"].append(order)

    while i < n:
        ch = smi[i]
        if ch == "[":
            j = smi.index("]", i)
            m = re.match(r"^(\d+)?([A-Z][a-z]?|[a-z]|\*)(@{0,2})(H\d*)?([+-]+\d*|[+-]\d+)?(?::\d+)?$", smi[i + 1:j])
            if not m:
                raise ValueError("unparsed bracket atom %r in %s" % (smi[i:j + 1], smi))
            sym = m.group(2); arom = sym.islower()
            h = 0 if not m.group(4) else (int(m.group(4)[1:]) if len(m.group(4)) > 1 else 1)
            q = 0
            if m.group(5):
                c = m.group(5)
                q = (c.count("+") - c.count("-")) if not re.search(r"\d", c) else int(c[1:]) * (1 if c[0] == "+" else -1)
            atoms.append(dict(sym=sym.capitalize() if arom else sym, arom=arom, h=h, q=q, bonds=[]))
            i = j + 1
        elif ch in "()":
            if ch == "(":
                stack.append(prev)
            else:
                prev = stack.pop()
            i += 1; continue
        elif ch in BOND:
            pend = BOND[ch]; i += 1; continue
        elif ch == ".":
            prev = None; pend = None; i += 1; continue
        elif ch.isdigit() or ch == "%":
            if ch == "%":
                lab = smi[i + 1:i + 3]; i += 3
            else:
                lab = ch; i += 1
            if lab in rings:
                a, o = rings.pop(lab)
                link(a, prev, pend if pend is not None else o)
            else:
                rings[lab] = (prev, pend)
            pend = None; continue
        else:
            two = smi[i:i + 2]
            if two in ("Cl", "Br"):
                sym, arom, i = two, False, i + 2
            elif ch in "BCNOPSFI":
                sym, arom, i = ch, False, i + 1
            elif ch in "bcnops":
                sym, arom, i = ch.upper(), True, i + 1
            elif ch == "*":
                sym, arom, i = "*", False, i + 1
            else:
                raise ValueError("unparsed character %r in %s" % (ch, smi))
            atoms.append(dict(sym=sym, arom=arom, h=None, q=0, bonds=[]))
        cur = len(atoms) - 1
        if prev is not None:
            link(prev, cur, pend)
        prev, pend = cur, None
    if rings:
        raise ValueError("unclosed ring in %s" % smi)
    comp = Counter()
    for a in atoms:
        comp[a["sym"]] += 1
        comp["q"] += a["q"]
        if a["h"] is not None:
            comp["H"] += a["h"]
        elif a["sym"] in ORGANIC:
            if a["arom"]:
                comp["H"] += max(0, ORGANIC[a["sym"]][0] - len(a["bonds"]) - 1)
            else:
                v = sum(a["bonds"])
                tgt = next((x for x in ORGANIC[a["sym"]] if x >= v), v)
                comp["H"] += int(round(tgt - v))
    return +comp + Counter() if False else Counter({k: v for k, v in comp.items() if v})


# ───────────────────────── reading the built documents ─────────────────────────
def tables(path):
    root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    out = []
    for tbl in root.iter(W + "tbl"):
        rows = []
        for tr in tbl.iter(W + "tr"):
            rows.append(["".join(t.text or "" for t in tc.iter(W + "t")) for tc in tr.findall(W + "tc")])
        out.append(rows)
    return out


def find(tabs, first, must):
    hit = [t for t in tabs if t and t[0] and t[0][0].strip() == first and any(must in c for c in t[0])]
    if len(hit) != 1:
        raise SystemExit("G-RXNTABLE: FAIL -- %d tables with header %r / %r in the document" % (len(hit), first, must))
    return hit[0]


SUP = {"⁺": 1, "⁻": -1}


def printed_charge(label):
    """The charge a species label PRINTS: a trailing run of superscript digits and signs (²⁻, ⁺, •⁺)."""
    m = re.search(r"([²³]?)([⁺⁻])$", label)
    if not m:
        return 0
    mag = {"": 1, "²": 2, "³": 3}[m.group(1)]
    return mag * SUP[m.group(2)]


def split_terms(side_text):
    """'2 CO₃²⁻ + e⁻' -> [(2, 'CO₃²⁻'), (1, 'e⁻')].  Labels may contain ' + ' only as a separator."""
    out = []
    for term in side_text.split(" + "):
        m = re.match(r"^(\d+(?:\.\d+)?) (.+)$", term.strip())
        out.append((float(m.group(1)), m.group(2)) if m else (1.0, term.strip()))
    return out


def main():
    neg = "--negative-control" in sys.argv
    import importlib.util
    spec = importlib.util.spec_from_file_location("brs", os.path.join(HERE, "build_reaction_stoichiometry.py"))
    B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
    fails = []

    # ---- A: the chemistry, by a second code path
    rows = [dict(r, lhs=list(r["lhs"]), rhs=list(r["rhs"])) for r in B.ROWS]
    if neg:                                   # (iv) one hydrogen's worth of structure dropped from a product
        r = rows[43]
        lab, smi = r["rhs"][0][1]
        if not isinstance(smi, str):
            raise SystemExit("G-RXNTABLE control: BAD -- the product chosen for the structure perturbation is not a SMILES")
        r["rhs"][0] = (r["rhs"][0][0], (lab, smi + ".C"))         # one carbon (and four hydrogens) too many
    nspec = 0
    for r in rows:
        tot = {"lhs": Counter(), "rhs": Counter()}
        for sd in ("lhs", "rhs"):
            for nn, (lab, c) in r[sd]:
                if isinstance(c, dict):
                    mine = Counter({k: v for k, v in c.items() if v})
                else:
                    try:
                        mine = smiles_composition(c)
                    except ValueError as exc:
                        fails.append("row %d: %s" % (r["row"], exc)); continue
                    theirs = Counter({k: v for k, v in B.comp(c).items() if v})
                    nspec += 1
                    if mine != theirs and not neg:
                        fails.append("row %d %s: the two parsers disagree on %s -- %s vs RDKit %s"
                                     % (r["row"], lab, c, dict(mine), dict(theirs)))
                if printed_charge(lab) != mine.get("q", 0):
                    fails.append("row %d: %r prints charge %+d but is %+d" % (r["row"], lab, printed_charge(lab), mine.get("q", 0)))
                for k, v in mine.items():
                    tot[sd][k] += nn * v
        d = {k: tot["lhs"][k] - tot["rhs"][k] for k in set(tot["lhs"]) | set(tot["rhs"]) if tot["lhs"][k] != tot["rhs"][k]}
        if d:
            fails.append("row %d does not balance on the recomputed compositions: lhs - rhs = %s" % (r["row"], d))

    # ---- B: the printed table
    tabs = tables(SI)
    s10 = [list(x) for x in find(tabs, "#", "Overall reaction")]
    s2 = find(tabs, "#", "carrier")  if False else None
    s2c = [t for t in tabs if t and t[0] and t[0][0].strip() == "#" and len(t) == 51 and not any("Overall reaction" in c for c in t[0])]
    if len(s2c) != 1:
        fails.append("could not identify Table S2 uniquely in the SI (%d candidates)" % len(s2c)); s2 = None
    else:
        s2 = s2c[0]
    if len(s10) != 51:
        fails.append("Table S10 has %d rows, not 50" % (len(s10) - 1))
    ed = {r["reaction"]: r["direction"] for r in csv.DictReader(io.open(os.path.join(HERE, "electrode_direction.csv"), encoding="utf-8"))}
    if neg:
        for _i, _old, _new in ((24, "6 e⁻", "4 e⁻"), (7, "pyridinium⁺", "pyridinium")):
            if _old not in s10[_i][5]:
                raise SystemExit("G-RXNTABLE control: BAD -- row %d no longer prints %r, so the perturbation is inert" % (_i, _old))
        s10[24][5] = s10[24][5].replace("6 e⁻", "4 e⁻")            # (i) row 24 loses two electrons
        s10[12 + 1][2] = "anode"                                     # (iii) row 13 put at the wrong electrode
        s10[7][5] = s10[7][5].replace("pyridinium⁺", "pyridinium")   # (ii) row 7's cation printed without its charge
    hdr = s10[0]
    cI = {h: i for i, h in enumerate(hdr)}
    for k, row in enumerate(s10[1:], 1):
        num, name, electrode, active, step, overall, nel, ceil = row
        src = rows[k - 1]
        want_eq = B.fmt(B.ROWS[k - 1]["lhs"]) + " → " + B.fmt(B.ROWS[k - 1]["rhs"])
        eq = overall.split(" [")[0]
        if eq != want_eq:
            fails.append("row %d: the equation printed is not the one the balance was checked on: %r" % (k, eq[:80]))
        if " → " not in eq:
            fails.append("row %d: no arrow in %r" % (k, eq)); continue
        L, Rr = [split_terms(s) for s in eq.split(" → ")]
        qL = sum(nn * printed_charge(lab) for nn, lab in L); qR = sum(nn * printed_charge(lab) for nn, lab in Rr)
        if abs(qL - qR) > 1e-9:
            fails.append("row %d: as printed, the charges do not balance (%+g on the left, %+g on the right)" % (k, qL, qR))
        eL = sum(nn for nn, lab in L if lab == "e⁻"); eR = sum(nn for nn, lab in Rr if lab == "e⁻")
        kind = B.ROWS[k - 1]["kind"]
        m = re.match(r"^([\d.]+)", nel)
        nprint = float(m.group(1)) if m else None
        if kind in ("stoichiometric", "ex-cell"):
            if eL and eR:
                fails.append("row %d: electrons on both sides" % k)
            per = (eL or eR) / L[0][0]
            if nprint is None or abs(per - nprint) > 1e-9:
                fails.append("row %d: the equation carries %g e- per limiting substrate, the electron column says %s" % (k, per, nel))
            side_says = "cathode" if eL else "anode"
            if electrode != side_says:
                fails.append("row %d: electrons are written on the %s side but the Electrode column says %s"
                             % (k, "left" if eL else "right", electrode))
        elif eL or eR:
            fails.append("row %d: a %s row is printed with net electrons" % (k, kind))
        if {"anodic": "anode", "cathodic": "cathode"}[ed[name]] != electrode:
            fails.append("row %d: Electrode column %s, electrode_direction.csv %s" % (k, electrode, ed[name]))
        if s2 is not None:
            r2 = s2[k]
            if r2[2] != name:
                fails.append("row %d: Table S10 names %r, Table S2 names %r" % (k, name, r2[2]))
            if r2[3] != ceil:
                fails.append("row %d: 'Ceiling set by' is %s, Table S2's carrier type is %s" % (k, ceil, r2[3]))
            if not active.startswith({"substrate": ("substrate", "reagent"), "mediator": ("mediator",), "catalyst": ("catalyst",)}[r2[3]]):
                fails.append("row %d: electroactive species %r against carrier type %s" % (k, active, r2[3]))
    # ---- C: the condensed SI carries the same table
    try:
        c10 = find(tables(SIC), "#", "Overall reaction")
        if [list(x) for x in c10] != [list(x) for x in find(tabs, "#", "Overall reaction")]:
            fails.append("the condensed SI's Table S10 is not the detailed SI's")
    except SystemExit as exc:
        fails.append(str(exc))

    if neg:
        need = ["row 24", "row 13", "row 7", "row 44"]
        hit = {n: any(n + ":" in f or n + " " in f for f in fails) for n in need}
        ok = all(hit.values())
        print("G-RXNTABLE control: %s (lost electrons %s; wrong electrode %s; unprinted charge %s; broken structure %s)"
              % ("GOOD" if ok else "BAD", *["caught" if hit[n] else "MISSED" for n in need]))
        sys.exit(0 if ok else 1)
    for f in fails:
        print("   FAIL: " + f)
    kinds = Counter(r["kind"] for r in B.ROWS)
    print("G-RXNTABLE: %s -- 50 rows read from the built SI; %d species recomputed by a second parser and agreeing with RDKit; "
          "every reaction balances in atoms and charge and prints its charges; electrons, electrode and carrier type agree with "
          "the table's own columns and Table S2 (%d stoichiometric, %d paired or cycle-charge, %d chain, %d ex-cell); condensed SI identical"
          % ("FAIL" if fails else "PASS", nspec, kinds["stoichiometric"], kinds["paired"] + kinds["charge-consuming"], kinds["chain"], kinds["ex-cell"]))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
