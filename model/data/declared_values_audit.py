#!/usr/bin/env python3
"""Declared-values audit -> docs/DECLARED_VALUES_AUDIT_20260907.md

    cd Section4_Model && python data/declared_values_audit.py

WHY (author instruction, 2026-09-07: "can you also do another audit for made up #s while you're at
it"). The two flow archetypes were state-C declared operating points with no source, disclosed
and bounded but never displaced by the measured films that were on disk. This audit walks EVERY
assumption-class registry row and answers three questions per row, from the registry text and
the assumption ledger, never from memory:

  1. what backs it (the `citation` column: a declared basis, a bound, or a named source that
     supports the class but not the value);
  2. which ledger tier it lands in (results/assumption_ledger.json: inert, declared choice,
     quantified-and-survives, quantified-but-conditional, signed-only, inadequate);
  3. whether a page-anchored replacement exists in the repository tree (a static list below,
     maintained by hand from what the tree holds; each entry names the file).

The action column is the audit's judgement, and it is deliberately conservative: a row is marked
REPLACE only when a measured value with a locator is on disk for THIS quantity; DECLARED-KEEP when
the quantity is an operator choice (a rotation speed, a design current, a vessel geometry) that no
measurement could replace; BOUNDED when the row carries a citable bound rather than a value.
"""
import csv, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REG = os.path.join(HERE, "parameters_provenance.csv")
LEDGER = os.path.join(ROOT, "results", "assumption_ledger.json")
OUT = os.path.join(ROOT, "docs", "DECLARED_VALUES_AUDIT_20260907.md")

# Rows for which the tree DOES hold a measured replacement, or for which one was found and
# adopted in this pass. Everything else is judged by its category rule below.
REPLACED_THIS_PASS = {
    "Parallel-plate flow-cell geometry": "RETIRED: replaced by 'delta (recirculating flow cell)', measured "
        "(Watkins 2023 SI Table S1, papers for model/concentrations/SIs/final upload/zotero uploads/"
        "Final final/other cells/nz3c00442_si_001.pdf)",
    "Thin-gap microflow operating point": "RETIRED: replaced by 'delta (microfluidic cell)', derived from "
        "Mo 2020 SI p. 13 (papers for model/aba3823_mo_sm.pdf)",
}
# Category rules: what each block of state-C rows is, and whether a measurement could replace it.
CATEGORY_RULE = {
    "1.": "declared modelling convention (temperature): no measurement replaces a chosen operating temperature.",
    "2.": "mixed-solvent mu/rho with no tabulated 25 C value; each carries a citable bound (G-MIXBOUND) or says no bound exists.",
    "3.": "declared modelling choices (theory level, viscosity used, hydrodynamic radius, an unused Le Bas increment).",
    "4.": "solver-species diffusivities that are declared transfers or class defaults for spectator ions; G-DSENS "
          "proves the spectator set moves nothing (exactly zero), and the mediator/substrate base-case constants "
          "are bounded by G-ECPANEL.",
    "5.": "electron counts from the balanced half-reactions and a trace-initialisation rule; not measurable quantities.",
    "6.": "electrolyte conductivities with no measured value for that exact composition; the sourcing dossier "
          "(docs/KAPPA_SOURCING_DOSSIER.md) records what was retrieved, and every row carries a band.",
    "7.": "reactor operating points (rotation speeds, cylinder diameter, free-convection height and driving force) "
          "and the Leveque coefficient; operator choices that no measurement replaces, each with a swept band.",
    "8.": "voltage-stack floor and exchange current for the thermal balance; declared, and E0 cancels out of the "
          "dissipation entirely.",
    "9.": "thermal-model geometries, design currents and film coefficients for the five Fig. 5 reactors; DECLARED "
          "archetypes (no measured cell geometry is on disk for any of them), each swept in Table S7i.",
    "10.": "order-of-magnitude homogeneous rate constants with literature anchors per row (Table S6); G-KSENS "
           "states what a tenfold revision costs.",
    "11.": "numerical settings, verified against analytic limits (S5.6); not physical quantities.",
}


def main():
    rows = list(csv.DictReader(io.open(REG, encoding="utf-8")))
    led = json.load(io.open(LEDGER, encoding="utf-8"))
    tier_of = {}
    for tier, names in led.get("tiers", {}).items():
        for n in names:
            tier_of[n] = tier
    if not tier_of:                       # older ledger layouts keep a per-row list
        for r in led.get("rows", []):
            tier_of[r.get("parameter", r.get("name"))] = r.get("tier")
    A = [r for r in rows if r["provenance_class"] == "assumption"]
    lines = []
    L = lines.append
    L("# Declared-values audit, 2026-09-07")
    L("")
    L("Author instruction: *\"can you also do another audit for made up #s while you're at it\"*, after the")
    L("two flow-archetype operating points turned out to be declared conventions that measured films on")
    L("disk could have replaced (see `ARCHETYPE_REANCHOR_20260907.md`).")
    L("")
    L("Generated by `data/declared_values_audit.py` from `data/parameters_provenance.csv` and")
    L("`results/assumption_ledger.json`. The registry holds **%d rows, %d of them assumption-class**." % (len(rows), len(A)))
    L("Every assumption row is listed; the *action* column is the audit's judgement.")
    L("")
    L("## The rule applied")
    L("")
    L("A state-C row is acceptable when (i) it is an operator choice or modelling convention that no")
    L("measurement could replace, or (ii) no page-anchored measurement of that quantity exists in the tree,")
    L("and in either case it carries a sensitivity. It is a **defect** when a page-anchored measurement")
    L("of the same quantity is on disk and was not adopted, which is what the flow films were. The search")
    L("for replacements was made against the PDFs in `papers for model/`, `Model Papers for Params/` and")
    L("`papers for model/concentrations/SIs/` (including the `final upload/zotero uploads` subtree).")
    L("")
    L("## Findings")
    L("")
    L("- **Two rows were defects and are retired** (the flow-archetype operating points). Both were")
    L("  disclosed as assumptions with swept bands; the defect was that measured films existed on disk.")
    L("- **No other assumption row has a page-anchored measurement of its own quantity in the tree.** The")
    L("  thermal-model reactors of Fig. 5 (category 9) are the largest declared block: five archetype")
    L("  geometries, four design currents, four internal film coefficients and three housing factors, all")
    L("  declared and all swept in Table S7i. They are flagged below as DECLARED-KEEP because no cell")
    L("  geometry or design current is measured anywhere in the tree; they should be read as the model's")
    L("  own definitions of its reactors, which the SI states.")
    L("- **The 34 electrolyte conductivities with no source** are the block the kappa dossier already")
    L("  audited; nothing new was found, and G-KAPPA/G-MSKAPPA bind every one the documents quote.")
    L("- **The stirred mediated band edges were stale** (50-200 um, the retired declared band, while the")
    L("  NP rows used 193-207 um); corrected in this pass (`make_bounds_runs.py`).")
    L("")
    L("## Category rules")
    L("")
    for k in sorted(CATEGORY_RULE, key=lambda x: int(x.rstrip("."))):
        L("- **%s** %s" % (k, CATEGORY_RULE[k]))
    L("")
    L("## Every assumption row")
    L("")
    L("| # | category | parameter | value | what backs it (citation column, abridged) | ledger tier | action |")
    L("|---|---|---|---|---|---|---|")
    counts = {}
    for i, r in enumerate(A, 1):
        cat = r["category"]
        key = cat.split(" ")[0]
        cite = re.sub(r"\s+", " ", r["citation"]).strip()
        cite = (cite[:110] + "...") if len(cite) > 113 else cite
        tier = tier_of.get(r["parameter"], "?")
        if r["parameter"] in REPLACED_THIS_PASS:
            action = REPLACED_THIS_PASS[r["parameter"]]
        elif key.startswith("2."):
            action = "BOUNDED" if ("bracket" in cite.lower() or "CRC" in cite) else "DECLARED-KEEP (no bound exists; stated)"
        elif key.startswith("6."):
            action = "DECLARED-KEEP (no measured kappa for this composition; banded)"
        elif key.startswith("9.") or key.startswith("7.") or key.startswith("8.") or key.startswith("1."):
            action = "DECLARED-KEEP (operator choice / archetype definition; swept)"
        elif key.startswith("11."):
            action = "DECLARED-KEEP (numerical setting; verified against analytic limits)"
        elif key.startswith("4."):
            action = "DECLARED-KEEP (spectator or base-case constant; sensitivity exactly zero or bounded)"
        elif key.startswith("10."):
            action = "DECLARED-KEEP (order-of-magnitude k with per-row anchors; G-KSENS states the exposure)"
        else:
            action = "DECLARED-KEEP (modelling choice)"
        counts[action.split(" (")[0].split(":")[0]] = counts.get(action.split(" (")[0].split(":")[0], 0) + 1
        L("| %d | %s | %s | %s | %s | %s | %s |" % (i, cat, r["parameter"].replace("|", "/"), r["value"].replace("|", "/")[:40],
                                                     cite.replace("|", "/"), tier, action.replace("|", "/")))
    L("")
    L("## Tally")
    L("")
    for k, v in sorted(counts.items()):
        L("- %s: %d" % (k, v))
    L("")
    L("## What this audit cannot do")
    L("")
    L("It reads the registry and the ledger; it does not read the manuscript's typed prose numbers, which")
    L("G-MSDERIVED, G-XDOC, G-PROVPRINT and G-COVER cover, and it cannot know about a measurement that is")
    L("not in the tree. A row marked DECLARED-KEEP is a row for which nothing on disk displaces the")
    L("declaration, not a row whose declaration is beyond question.")
    io.open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote %s: %d assumption rows audited" % (os.path.relpath(OUT, ROOT), len(A)))
    for k, v in sorted(counts.items()):
        print("  %-14s %d" % (k, v))


if __name__ == "__main__":
    main()
