#!/usr/bin/env python3
"""Export the registry's method_note field to an INTERNAL audit document.

    cd Section4_Model && python data/export_method_notes.py

WHY THIS EXISTS
---------------
`method_note` is the working record of how each parameter was established: what was retrieved,
what was rejected and why, which value a row previously carried and what replaced it. That record
is the reason several real errors were caught, and it must not be lost.

It is NOT publication text. It is written in the first person of an audit -- datestamps, revision
clauses, prior values, the reasoning behind a rejection -- and printing it verbatim into the
Supporting Information made the SI read as an internal log rather than as a scientific document.
So `method_note` is no longer a column of SI Table S7; it lives here and in
data/parameters_provenance.csv, both of which stay internal.

The canonical store remains parameters_provenance.csv. This file is a readable rendering of the
same field, grouped by category, for use during audits.
"""
import csv, io, os, collections

HERE = os.path.dirname(os.path.abspath(__file__)); SEC4 = os.path.dirname(HERE)
OUT = os.path.join(SEC4, "docs", "METHOD_NOTES_INTERNAL.md")

def main():
    rows = list(csv.DictReader(io.open(os.path.join(HERE, "parameters_provenance.csv"),
                                       encoding="utf-8")))
    bycat = collections.OrderedDict()
    for r in rows:
        bycat.setdefault(r["category"], []).append(r)
    n_notes = sum(1 for r in rows if (r["method_note"] or "").strip())
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("# Method notes — INTERNAL, NOT FOR PUBLICATION\n\n")
        f.write("The `method_note` field of `data/parameters_provenance.csv`, rendered for reading.\n\n")
        f.write("**This is an audit record, not publication text.** It carries datestamps, revision\n"
                "clauses, superseded values and the reasoning behind rejected sources. It is\n"
                "deliberately NOT a column of SI Table S7: printing it made the Supporting\n"
                "Information read as an internal log. The SI publishes parameter, value, units,\n"
                "state, equation, citation with locator, and sensitivity.\n\n")
        f.write("Canonical store: `data/parameters_provenance.csv`. Regenerate this file with\n"
                "`python data/export_method_notes.py`.\n\n")
        f.write("| | |\n|---|---|\n| registry rows | %d |\n| rows carrying a method note | %d |\n\n"
                % (len(rows), n_notes))
        for cat, rs in bycat.items():
            f.write("\n---\n\n## %s\n\n" % cat)
            for r in rs:
                note = (r["method_note"] or "").strip()
                if not note:
                    continue
                f.write("### %s\n\n" % r["parameter"])
                f.write("`%s %s` — **%s**\n\n" % (r["value"], r["units"], r["provenance_class"]))
                f.write("%s\n\n" % note)
    print("wrote docs/METHOD_NOTES_INTERNAL.md — %d rows, %d method notes" % (len(rows), n_notes))

if __name__ == "__main__":
    main()
