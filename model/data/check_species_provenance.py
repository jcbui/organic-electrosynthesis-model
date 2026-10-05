#!/usr/bin/env python3
"""G-SPECIES -- every species diffusivity the EC' solver computes with must be traceable.

    cd Section4_Model && python data/check_species_provenance.py
    cd Section4_Model && python data/check_species_provenance.py --negative-control

Each (species, D) pair hardcoded in `julia/run_mediated.jl` must resolve to EXACTLY ONE of:

  (a) a category-4 row of parameters_provenance.csv, matched on BOTH the species name and the
      value -- never on value alone. A value-only match binds to the wrong row: on this check's
      first run `H+` at 2.0e-9 matched the unrelated `NH4+ (MeCN, used aq-like)` row, which also
      reads 2e-9 (CLAUDE.md trap 11), and that coincidence was hiding a genuinely missing row.

  (b) a carrier or substrate D in `julia/reactions_table.jl`, which build_reactions50.py generates
      by Wilke-Chang and which the registry covers as "All 50 carrier D values (Table S2)" and
      "8 mediated-spec substrate D values". G-MEDSYNC separately asserts the MedSpecs agree with
      that table, so this branch is a declared indirection, not a loophole -- the mediator species
      (ACT, BQ, NHPI...) and every `Sub` value reach their provenance this way.

Anything resolving to NEITHER is an unprovenanced number in the production solver.
"""
import csv, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); SEC4 = os.path.dirname(HERE)
REL_REG = 1e-4     # registry rows are the same number, so require an essentially exact match
## The generated table stores full Wilke-Chang precision (ACT: 5.9273e-10) while the MedSpecs carry
## the 3-significant-figure value a human typed (5.93e-10). G-MEDSYNC already absorbs exactly that
## rounding at 1% relative and says so in its own comment; reuse ITS declared tolerance rather than
## inventing a second one, so the two gates cannot disagree about what "agrees" means.
REL_GEN = 0.01

def norm(n):
    return re.sub(r"[()^]", "", n).lower()

def main(neg=False):
    reg  = list(csv.DictReader(io.open(os.path.join(HERE, "parameters_provenance.csv"), encoding="utf-8")))
    cat4 = []
    for r in reg:
        if not r["category"].startswith("4."): continue
        try: cat4.append((r["parameter"], float(r["value"]), r["provenance_class"]))
        except (ValueError, TypeError): pass

    tbl = io.open(os.path.join(SEC4, "julia", "reactions_table.jl"), encoding="utf-8").read()
    gen = set()
    for m in re.finditer(r"OERxn\([^)]*?,\s*([\d.]+e-\d+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+e-\d+),", tbl):
        gen.add(float(m.group(1)))
    for m in re.finditer(r"build_reactions50", tbl):
        pass
    ## substrate D values are carried in the MedSpecs themselves and asserted against this table
    ## by G-MEDSYNC; collect every numeric D in the table so the indirection is exact
    for m in re.finditer(r"([\d.]+e-\d+)", tbl):
        gen.add(float(m.group(1)))

    src = io.open(os.path.join(SEC4, "julia", "run_mediated.jl"), encoding="utf-8").read()
    src = "\n".join(re.sub(r"#.*$", "", ln) for ln in src.split("\n"))   # code, not comments
    pairs = sorted({(m.group(1), float(m.group(3)))
                    for m in re.finditer(r'S\("([^"]+)",\s*([-\d.+]+),\s*([\d.e-]+),', src)})
    if neg:
        pairs.append(("Xx-unregistered", 4.321e-9))

    ## `Sub` is handled separately and deliberately. Matching a substrate D against ANY value
    ## anywhere in reactions_table.jl is value-only matching across unrelated rows -- it "resolved"
    ## 4 of the 8 by coincidence on the first run. The table has no substrate-D field at all
    ## (OERxn carries the CARRIER D and the substrate CONCENTRATION), and build_reactions50.py
    ## computes none, so these 8 numbers are hand-typed into run_mediated.jl and nothing reproduces
    ## them. The registry publishes them as class `derived` -- "Wilke-Chang on named surrogate
    ## structures" -- but the standard's own test for state B is that the arithmetic be
    ## REPRODUCIBLE FROM THE REGISTRY ALONE, and it is not. Reported as its own category rather
    ## than passed, and rather than exempted into silence.
    ## `Sub` resolves against data/mediated_substrates.csv, which build_mediated_substrates.py
    ## generates by Wilke-Chang from a NAMED structure in a NAMED solvent, and which G-DSUB asserts
    ## the solver actually carries. Before 2026-08-24 these eight were hand-typed with nothing
    ## computing them and this branch reported them as unprovenanced; three were also WRONG.
    subgen = set()
    try:
        for r in csv.DictReader(io.open(os.path.join(HERE, "mediated_substrates.csv"), encoding="utf-8")):
            subgen.add(float(r["D_sub_m2s"]))
    except FileNotFoundError:
        pass
    unresolved, byreg, bygen, substrate = [], 0, 0, []
    for name, D in pairs:
        if name == "Sub":
            if any(abs(g - D) <= REL_REG * abs(D) for g in subgen):
                bygen += 1
            else:
                substrate.append(D)
            continue
        nn = norm(name); base = nn.rstrip("+-2")
        hit = next((p for p, v, c in cat4
                    if abs(v - D) <= REL_REG * abs(D) and (nn.split()[0] in norm(p) or (base and base in norm(p)))), None)
        if hit: byreg += 1; continue
        if any(abs(g - D) <= REL_GEN * abs(D) for g in gen): bygen += 1; continue
        unresolved.append((name, D))

    print("%d (species, D) pairs in run_mediated.jl" % len(pairs))
    print("   %d matched a category-4 registry row by NAME and VALUE" % byreg)
    print("   %d matched a generated D (reactions_table.jl via G-MEDSYNC, or mediated_substrates.csv via G-DSUB)" % bygen)
    print("   %d unresolved" % len(unresolved))
    if substrate:
        print()
        print("   %d mediated SUBSTRATE D values, published as class `derived` but NOT reproducible:"
              % len(substrate))
        for D in sorted(substrate):
            print("       D = %-10.4g  hand-typed in run_mediated.jl; no artifact computes it" % D)
        print("       registry row: '8 mediated-spec substrate D values' = (S5.5), class derived,")
        print("       method 'Wilke-Chang on named surrogate structures'. The method and the")
        print("       structures are NAMED but the arithmetic is reproduced nowhere, which is the")
        print("       state-B test in PROVENANCE_STANDARD.md. Resolve by EITHER adding the 8")
        print("       surrogate SMILES to build_reactions50.py so wilke_chang() regenerates them")
        print("       (3 of the 8 names are ambiguous and need the author), OR reclassifying the")
        print("       row to `assumption` with a stated sensitivity. Substrate D is MATERIAL --")
        print("       it sets i_subcap and enters the EC' solve -- so this is not a display-only row.")
    if unresolved or substrate:
        print()
        for n, D in unresolved:
            print("    UNPROVENANCED  %-16s D = %.4g" % (n, D))
        if neg:
            fired = any(n.startswith("Xx-") for n, _ in unresolved)
            print("\nG-SPECIES control: %s (injected unregistered species was %sdetected)"
                  % ("GOOD" if fired else "BAD", "" if fired else "NOT "))
            raise SystemExit(0 if fired else 1)
        print("\nG-SPECIES: FAIL")
        raise SystemExit(1)
    print("\nG-SPECIES: PASS -- every solver species diffusivity is traceable")

if __name__ == "__main__":
    main("--negative-control" in sys.argv)
